import logging
from typing import Optional, Tuple

from authlib.common.errors import AuthlibBaseError
from authlib.integrations.requests_client import OAuth2Session
from django.core import signing
from django.core.exceptions import ValidationError
from django.core.handlers.wsgi import WSGIRequest
from jwt import ExpiredSignatureError, InvalidTokenError
from requests import PreparedRequest

from ...account.models import User
from ...core.jwt import (
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    PERMISSIONS_FIELD,
    get_token_from_request,
    get_user_from_access_payload,
    get_user_from_payload,
    jwt_decode,
)
from ...core.permissions import get_permissions_codename, get_permissions_from_names
from ..base_plugin import BasePlugin, ConfigurationTypeField, ExternalAccessTokens
from ..error_codes import PluginErrorCode
from ..models import PluginConfiguration
from .dataclasses import OpenIDConnectConfig
from .exceptions import AuthenticationError
from .utils import (
    OAUTH_TOKEN_REFRESH_FIELD,
    create_tokens_from_oauth_payload,
    get_incorrect_fields,
    get_or_create_user_from_token,
    get_parsed_id_token,
    get_saleor_permissions_from_scope,
    get_user_from_token,
    is_owner_of_token_valid,
    validate_refresh_token,
)

logger = logging.getLogger(__name__)


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
        {"name": "audience", "value": None},
        {"name": "use_oauth_scope_permissions", "value": False},
    ]

    CONFIG_STRUCTURE = {
        "client_id": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Your Client ID required to authenticate on the provider side."
            ),
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
                "access token. OAuth provider needs to have included scope "
                "`offline_access`"
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
        "audience": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The OAuth resource identifier. If provided, Saleor will define "
                "audience for each authorization request."
            ),
            "label": "Audience",
        },
        "use_oauth_scope_permissions": {
            "type": ConfigurationTypeField.BOOLEAN,
            "help_text": (
                "Use OAuth scope permissions to grant a logged-in user access to "
                "protected resources. Your OAuth provider needs to have defined "
                "Saleor's permission scopes in format saleor:<saleor-perm>. Check"
                " Saleor docs for more details."
            ),
            "label": "Use OAuth scope permissions",
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
            audience=configuration["audience"],
            use_scope_permissions=configuration["use_oauth_scope_permissions"],
        )
        self.oauth = self._get_oauth_session()

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        incorrect_fields = get_incorrect_fields(plugin_configuration)
        if incorrect_fields:
            error_msg = "To enable a plugin, you need to provide values for this field."
            raise ValidationError(
                {
                    field: ValidationError(
                        error_msg, code=PluginErrorCode.PLUGIN_MISCONFIGURED.value
                    )
                    for field in incorrect_fields
                }
            )

    def _get_oauth_session(self):
        scope = "openid profile email"
        if self.config.use_scope_permissions:
            permissions = [f"saleor:{perm}" for perm in get_permissions_codename()]
            scope_permissions = " ".join(permissions)
            scope += f" {scope_permissions}"
        if self.config.enable_refresh_token:
            scope += " offline_access"
        return OAuth2Session(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            scope=scope,
        )

    def external_obtain_access_tokens(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        if not self.active:
            return previous_value

        state = data.get("state")
        if not state:
            msg = "Missing required field - state"
            raise ValidationError(
                {"state": ValidationError(msg, code=PluginErrorCode.NOT_FOUND.value)}
            )

        code = data.get("code")
        if not code:
            msg = "Missing required field - code"
            raise ValidationError(
                {"code": ValidationError(msg, code=PluginErrorCode.NOT_FOUND.value)}
            )

        state_data = signing.loads(state)
        redirect_uri = state_data.get("redirectUri")
        if not redirect_uri:
            msg = "The state value is incorrect"
            raise ValidationError(
                {"code": ValidationError(msg, code=PluginErrorCode.INVALID.value)}
            )

        token_data = self.oauth.fetch_token(
            self.config.token_url, code=code, redirect_uri=redirect_uri
        )
        user_permissions = None
        if self.config.use_scope_permissions:
            user_permissions = get_saleor_permissions_from_scope(
                token_data.get("scope")
            )

        parsed_id_token = get_parsed_id_token(
            token_data, self.config.json_web_key_set_url
        )
        user = get_or_create_user_from_token(parsed_id_token)
        tokens = create_tokens_from_oauth_payload(
            token_data, user, parsed_id_token, user_permissions, owner=self.PLUGIN_ID
        )
        return ExternalAccessTokens(user=user, **tokens)

    def external_authentication_url(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> dict:
        if not self.active:
            return previous_value
        redirect_uri = data.get("redirectUri")
        if not redirect_uri:
            msg = "Missing required field - redirectUri"
            raise ValidationError(
                {
                    "redirectUri": ValidationError(
                        msg, code=PluginErrorCode.NOT_FOUND.value
                    )
                }
            )
        kwargs = {
            "redirect_uri": redirect_uri,
            "state": signing.dumps({"redirectUri": redirect_uri}),
        }
        if self.config.audience:
            kwargs["audience"] = self.config.audience
        uri, state = self.oauth.create_authorization_url(
            self.config.authorization_url, **kwargs
        )
        return {"authorizationUrl": uri}

    def external_refresh(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> ExternalAccessTokens:
        if not self.active:
            return previous_value

        error_code = PluginErrorCode.INVALID.value
        if not self.config.enable_refresh_token:
            msg = (
                "Unable to refresh the token. Support for refreshing tokens is disabled"
            )
            raise ValidationError(
                {"refresh_token": ValidationError(msg, code=error_code)}
            )
        refresh_token = request.COOKIES.get(JWT_REFRESH_TOKEN_COOKIE_NAME, None)
        refresh_token = data.get("refreshToken") or refresh_token

        validate_refresh_token(refresh_token, data)
        saleor_refresh_token = jwt_decode(refresh_token)  # type: ignore
        token_endpoint = self.config.token_url
        try:
            token_data = self.oauth.refresh_token(
                token_endpoint,
                refresh_token=saleor_refresh_token[OAUTH_TOKEN_REFRESH_FIELD],
            )
        except AuthlibBaseError:
            logger.warning("Unable to refresh the token.", exc_info=True)
            raise ValidationError(
                {
                    "refresh_token": ValidationError(
                        "Unable to refresh the token.",
                        code=error_code,
                    )
                }
            )
        try:
            user_permissions = None
            if self.config.use_scope_permissions:
                user_permissions = get_saleor_permissions_from_scope(
                    token_data.get("scope")
                )
            parsed_id_token = get_parsed_id_token(
                token_data, self.config.json_web_key_set_url
            )
            user = get_user_from_token(parsed_id_token)
            tokens = create_tokens_from_oauth_payload(
                token_data,
                user,
                parsed_id_token,
                user_permissions,
                owner=self.PLUGIN_ID,
            )
            return ExternalAccessTokens(user=user, **tokens)
        except AuthenticationError as e:
            raise ValidationError(
                {"refreshToken": ValidationError(str(e), code=error_code)}
            )

    def external_logout(self, data: dict, request: WSGIRequest, previous_value):
        if not self.active:
            return previous_value

        if not self.config.logout_url:
            # Logout url doesn't exist
            return {}
        req = PreparedRequest()
        req.prepare_url(self.config.logout_url, data)

        return {"logoutUrl": req.url}

    def external_verify(
        self, data: dict, request: WSGIRequest, previous_value
    ) -> Tuple[Optional[User], dict]:
        if not self.active:
            return previous_value
        token = data.get("token")
        if not token:
            return previous_value
        valid = is_owner_of_token_valid(token, owner=self.PLUGIN_ID)
        if not valid:
            return previous_value
        try:
            payload = jwt_decode(token)
            user = get_user_from_payload(payload)
        except (ExpiredSignatureError, InvalidTokenError) as e:
            raise ValidationError({"token": e})
        permissions = payload.get(PERMISSIONS_FIELD)
        if permissions is not None:
            user.effective_permissions = get_permissions_from_names(  # type: ignore
                permissions
            )
        return user, payload

    def authenticate_user(self, request: WSGIRequest, previous_value) -> Optional[User]:
        if not self.active:
            return previous_value
        token = get_token_from_request(request)
        if not token:
            return previous_value
        valid = is_owner_of_token_valid(token, owner=self.PLUGIN_ID)
        if not valid:
            return previous_value
        payload = jwt_decode(token)
        user = get_user_from_access_payload(payload)
        return user
