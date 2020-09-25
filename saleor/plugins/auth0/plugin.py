import json
import logging
from typing import Callable, Optional
from urllib.parse import urlencode

from authlib.common.errors import AuthlibBaseError
from authlib.integrations.requests_client import OAuth2Session
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound
from django.shortcuts import redirect

from ...account.models import User
from ...core.jwt import (
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    get_token_from_request,
    get_user_from_access_token,
    jwt_decode,
)
from ...core.utils.url import prepare_url
from ..base_plugin import BasePlugin, ConfigurationTypeField
from ..error_codes import PluginErrorCode
from .dataclasses import Auth0Config
from .exceptions import AuthenticationError
from .utils import (
    get_auth_service_url,
    get_valid_auth_tokens_from_auth0_payload,
    prepare_redirect_url,
    validate_refresh_token,
    validate_storefront_redirect_url,
)

logger = logging.getLogger(__name__)

AUTHORIZE_PATH = "/authorize"
OAUTH_TOKEN_PATH = "/oauth/token"


def convert_error_to_http_response(fn: Callable) -> Callable:
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AuthenticationError as e:
            return HttpResponseBadRequest(str(e))

    return wrapped


class Auth0Plugin(BasePlugin):
    PLUGIN_ID = "mirumee.authentication.auth0"
    PLUGIN_NAME = "Auth0"
    DEFAULT_CONFIGURATION = [
        {"name": "client_id", "value": None},
        {"name": "client_secret", "value": None},
        {"name": "enable_refresh_token", "value": True},
        {"name": "domain", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "client_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Your client id required to authenticate on Auth0 side. The client id "
                "for your app can be found on https://manage.auth0.com/dashboard in "
                "Applications section."
            ),
            "label": "Client ID",
        },
        "client_secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": (
                "Your client secret required to authenticate on Auth0 side. The client "
                "secret for your app can be found on https://manage.auth0.com/dashboard"
                " in Applications section."
            ),
            "label": "Client Secret",
        },
        "enable_refresh_token": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "Determine if the refresh token should be also fetched from Auth0. "
                "By disabling it, users will need to re-login after the access token "
                "expired. By enabling it, frontend apps will be able to refresh the "
                "access token. More details: "
                "https://auth0.com/docs/tokens/refresh-tokens"
            ),
            "label": "Enable refreshing token",
        },
        "domain": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The domain which is assigned to your app by Auth0. All requests will "
                "be sent to the provided domain. The domain can be found on "
                "https://manage.auth0.com/dashboard in the Applications section."
            ),
            "label": "Domain",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = Auth0Config(
            client_id=configuration["client_id"],
            client_secret=configuration["client_secret"],
            enable_refresh_token=configuration["enable_refresh_token"],
            domain=configuration["domain"],
        )
        self.auth0 = self._get_oauth_session()

    def _get_oauth_session(self):
        scope = "openid profile email"
        if self.config.enable_refresh_token:
            scope += " offline_access"
        return OAuth2Session(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            scope=scope,
        )

    def _get_auth0_service_url(self, service):
        return get_auth_service_url(self.config.domain, service)

    def external_authentication(self, data: dict, previous_value) -> dict:
        storefront_redirect_url = data.get("redirectUrl")
        validate_storefront_redirect_url(storefront_redirect_url)
        uri, state = self.auth0.create_authorization_url(
            self._get_auth0_service_url(AUTHORIZE_PATH),
            redirect_uri=prepare_redirect_url(self.PLUGIN_ID, storefront_redirect_url),
        )
        return {"authorizationUrl": uri}

    def external_refresh(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> dict:
        # Todo validate if plugin is active
        refresh_token = request.COOKIES.get(JWT_REFRESH_TOKEN_COOKIE_NAME, None)
        refresh_token = data.get("refreshToken") or refresh_token

        validate_refresh_token(refresh_token, data)
        saleor_refresh_token = jwt_decode(refresh_token)  # type: ignore
        token_endpoint = self._get_auth0_service_url(OAUTH_TOKEN_PATH)
        try:
            token_data = self.auth0.refresh_token(
                token_endpoint,
                refresh_token=saleor_refresh_token["oauth_refresh_token"],
            )
        except AuthlibBaseError:
            logger.warning("Unable to refresh the token.", exc_info=True)
            raise ValidationError(
                {
                    "refresh_token": ValidationError(
                        "Unable to refresh the token.",
                        code=PluginErrorCode.INVALID.value,
                    )
                }
            )
        try:
            return get_valid_auth_tokens_from_auth0_payload(
                token_data, self.config.domain, get_or_create=False
            )
        except AuthenticationError as e:
            raise ValidationError(
                {
                    "refreshToken": ValidationError(
                        str(e), code=PluginErrorCode.INVALID.value
                    )
                }
            )

    def authenticate_user(self, request: WSGIRequest, previous_value) -> Optional[User]:
        # TODO this will be covered by tests and modified after we add Auth backend for
        #  plugins
        token = get_token_from_request(request)
        if not token:
            return None
        return get_user_from_access_token(token)

    @convert_error_to_http_response
    def handle_auth0_callback(self, request: WSGIRequest) -> HttpResponse:
        token_endpoint = self._get_auth0_service_url(OAUTH_TOKEN_PATH)
        storefront_redirect_url = request.GET.get("redirectUrl")
        if not storefront_redirect_url:
            raise AuthenticationError("Missing get param - redirectUrl")
        token_data = self.auth0.fetch_token(
            token_endpoint,
            authorization_response=request.build_absolute_uri(),
            redirect_uri=prepare_redirect_url(self.PLUGIN_ID),
        )
        params = get_valid_auth_tokens_from_auth0_payload(
            token_data, self.config.domain,
        )

        redirect_url = prepare_url(urlencode(params), storefront_redirect_url)
        return redirect(redirect_url)

    def webhook(self, request: WSGIRequest, path: str, previous_value) -> HttpResponse:
        if path.startswith("/refresh"):
            # TODO this call will be moved to external refresh mutation
            return HttpResponse(self.external_refresh({}, request, None))
        if path.startswith("/login"):
            # TODO this will be moved to external auth mutation
            return HttpResponse(
                json.dumps(
                    self.external_authentication(request.GET, None)  # type: ignore
                )
            )
        if path.startswith("/callback"):
            return self.handle_auth0_callback(request)
        return HttpResponseNotFound()
