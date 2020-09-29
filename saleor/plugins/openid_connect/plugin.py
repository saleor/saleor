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
from requests import PreparedRequest

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
from ..models import PluginConfiguration
from .dataclasses import OpenIDConnectConfig
from .exceptions import AuthenticationError
from .utils import (
    get_incorrect_or_missing_urls,
    get_or_create_user_from_token,
    get_parsed_id_token,
    get_user_from_token,
    get_valid_auth_tokens_from_auth_payload,
    prepare_redirect_url,
    validate_refresh_token,
    validate_storefront_redirect_url,
)

logger = logging.getLogger(__name__)


def convert_error_to_http_response(fn: Callable) -> Callable:
    def wrapped(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AuthenticationError as e:
            return HttpResponseBadRequest(str(e))

    return wrapped


class OpenIDConnectPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.authentication.openidconnect"
    PLUGIN_NAME = "OpenID Connect"
    DEFAULT_CONFIGURATION = [
        {"name": "client_id", "value": None},
        {"name": "client_secret", "value": None},
        {"name": "enable_refresh_token", "value": True},
        {"name": "oauth_authorization_url", "value": None},
        {"name": "oauth_token_url", "value": None},
        {"name": "json_web_key_set_url", "value": None},
        {"name": "oauth_logout_url", "value": None},
    ]

    CONFIG_STRUCTURE = {
        "client_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": ("Your client id required to authenticate on provider side."),
            "label": "Client ID",
        },
        "client_secret": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": (
                "Your client secret required to authenticate on provider side."
            ),
            "label": "Client Secret",
        },
        "enable_refresh_token": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "Determine if the refresh token should be also fetched from provider. "
                "By disabling it, users will need to re-login after the access token "
                "expired. By enabling it, frontend apps will be able to refresh the "
                "access token."
            ),
            "label": "Enable refreshing token",
        },
        "oauth_authorization_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": ("The endpoint used to redirect user to authorization page"),
            "label": "OAuth Authorization URL",
        },
        "oauth_token_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The endpoint to exchange an Authorization Code for a Token."
            ),
            "label": "OAuth Token URL",
        },
        "json_web_key_set_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The JSON Web Key Set (JWKS) is a set of keys containing the public "
                "keys used to verify any JSON Web Token (JWT) issued by the "
                "authorization server and signed using the RS256 signing algorithm."
            ),
            "label": "JSON Web Key Set URL",
        },
        "oauth_logout_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The URL for logging out the user from the OAuth provider side."
            ),
            "label": "OAuth logout URL",
        },
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Convert to dict to easier take config elements
        configuration = {item["name"]: item["value"] for item in self.configuration}
        self.config = OpenIDConnectConfig(
            client_id=configuration["client_id"],
            client_secret=configuration["client_secret"],
            enable_refresh_token=configuration["enable_refresh_token"],
            json_web_key_set_url=configuration["json_web_key_set_url"],
            authorization_url=configuration["oauth_authorization_url"],
            token_url=configuration["oauth_token_url"],
            logout_url=configuration["oauth_logout_url"],
        )
        self.oauth = self._get_oauth_session()

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}
        if plugin_configuration.active:
            urls_to_validate = {
                "json_web_key_set_url": configuration["json_web_key_set_url"],
                "oauth_authorization_url": configuration["oauth_authorization_url"],
                "oauth_token_url": configuration["oauth_token_url"],
            }
            incorrect_fields = get_incorrect_or_missing_urls(urls_to_validate)
            if not configuration["client_id"]:
                incorrect_fields.append("client_id")
            if not configuration["client_secret"]:
                incorrect_fields.append("client_secret")
            if incorrect_fields:
                error_msg = (
                    "To enable a plugin, you need to provide values for the "
                    "following fields: "
                )
                raise ValidationError(
                    error_msg + ", ".join(incorrect_fields),
                    code=PluginErrorCode.PLUGIN_MISCONFIGURED.value,
                )

    def _get_oauth_session(self):
        scope = "openid profile email"
        if self.config.enable_refresh_token:
            scope += " offline_access"
        return OAuth2Session(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            scope=scope,
        )

    def external_authentication(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> dict:
        storefront_redirect_url = data.get("redirectUrl")
        validate_storefront_redirect_url(storefront_redirect_url)
        uri, state = self.oauth.create_authorization_url(
            self.config.authorization_url,
            redirect_uri=prepare_redirect_url(self.PLUGIN_ID, storefront_redirect_url),
        )
        return {"authorizationUrl": uri}

    def external_refresh(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> dict:
        refresh_token = request.COOKIES.get(JWT_REFRESH_TOKEN_COOKIE_NAME, None)
        refresh_token = data.get("refreshToken") or refresh_token

        validate_refresh_token(refresh_token, data)
        saleor_refresh_token = jwt_decode(refresh_token)  # type: ignore
        token_endpoint = self.config.token_url
        try:
            token_data = self.oauth.refresh_token(
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
            parsed_id_token = get_parsed_id_token(
                token_data, self.config.json_web_key_set_url
            )
            user = get_user_from_token(parsed_id_token)
            return get_valid_auth_tokens_from_auth_payload(
                token_data, user, parsed_id_token
            )
        except AuthenticationError as e:
            raise ValidationError(
                {
                    "refreshToken": ValidationError(
                        str(e), code=PluginErrorCode.INVALID.value
                    )
                }
            )

    def external_logout(self, data: dict, request: WSGIRequest, previous_value):
        if not self.config.logout_url:
            # Logout url doesn't exist
            return {}
        req = PreparedRequest()
        req.prepare_url(self.config.logout_url, data)

        return {"logoutUrl": req.url}

    def authenticate_user(self, request: WSGIRequest, previous_value) -> Optional[User]:
        # TODO this will be covered by tests and modified after we add Auth backend for
        #  plugins
        token = get_token_from_request(request)
        if not token:
            return None
        return get_user_from_access_token(token)

    @convert_error_to_http_response
    def handle_auth_callback(self, request: WSGIRequest) -> HttpResponse:
        storefront_redirect_url = request.GET.get("redirectUrl")
        if not storefront_redirect_url:
            raise AuthenticationError("Missing get param - redirectUrl")
        token_data = self.oauth.fetch_token(
            self.config.token_url,
            authorization_response=request.build_absolute_uri(),
            redirect_uri=prepare_redirect_url(self.PLUGIN_ID),
        )
        parsed_id_token = get_parsed_id_token(
            token_data, self.config.json_web_key_set_url
        )
        user = get_or_create_user_from_token(parsed_id_token)
        params = get_valid_auth_tokens_from_auth_payload(
            token_data, user, parsed_id_token
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
                    self.external_authentication(
                        request.GET, request, None  # type: ignore
                    )
                )
            )
        if path.startswith("/callback"):
            return self.handle_auth_callback(request)
        return HttpResponseNotFound()
