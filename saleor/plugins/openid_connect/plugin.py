import logging
from typing import cast

from authlib.common.errors import AuthlibBaseError
from django.core import signing
from django.core.exceptions import ValidationError
from jwt import DecodeError, ExpiredSignatureError, InvalidTokenError
from requests import HTTPError, PreparedRequest

from ...account.models import User
from ...account.utils import get_user_groups_permissions
from ...core.auth import get_token_from_request
from ...core.jwt import (
    JWT_REFRESH_TOKEN_COOKIE_NAME,
    PERMISSIONS_FIELD,
    get_user_from_access_payload,
    get_user_from_payload,
    jwt_decode,
)
from ...graphql.core import SaleorContext
from ...permission.enums import get_permissions_codename, get_permissions_from_names
from ..base_plugin import BasePlugin, ConfigurationTypeField, ExternalAccessTokens
from ..error_codes import PluginErrorCode
from ..models import PluginConfiguration
from . import PLUGIN_ID
from .client import OAuth2Client
from .const import SALEOR_STAFF_PERMISSION
from .dataclasses import OpenIDConnectConfig
from .exceptions import AuthenticationError
from .utils import (
    OAUTH_TOKEN_REFRESH_FIELD,
    assign_staff_to_default_group_and_update_permissions,
    create_tokens_from_oauth_payload,
    get_domain_from_email,
    get_incorrect_fields,
    get_or_create_user_from_payload,
    get_parsed_id_token,
    get_saleor_permission_names,
    get_saleor_permissions_qs_from_scope,
    get_staff_user_domains,
    get_user_from_oauth_access_token,
    get_user_from_token,
    is_owner_of_token_valid,
    send_user_event,
    validate_refresh_token,
)

logger = logging.getLogger(__name__)


class OpenIDConnectPlugin(BasePlugin):
    PLUGIN_ID = PLUGIN_ID
    DEFAULT_CONFIGURATION = [
        {"name": "client_id", "value": None},
        {"name": "client_secret", "value": None},
        {"name": "enable_refresh_token", "value": True},
        {"name": "oauth_authorization_url", "value": None},
        {"name": "oauth_token_url", "value": None},
        {"name": "json_web_key_set_url", "value": None},
        {"name": "oauth_logout_url", "value": None},
        {"name": "user_info_url", "value": None},
        {"name": "audience", "value": None},
        {"name": "use_oauth_scope_permissions", "value": False},
        {"name": "staff_user_domains", "value": None},
        {"name": "default_group_name_for_new_staff_users", "value": None},
    ]
    PLUGIN_NAME = "OpenID Connect"
    CONFIGURATION_PER_CHANNEL = False

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
                "`offline_access`."
            ),
            "label": "Enable refreshing token",
        },
        "oauth_authorization_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": "The endpoint used to redirect user to authorization page.",
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
        "user_info_url": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "The URL which can be used to fetch user details by using an access "
                "token."
            ),
            "label": "User info URL",
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
        "staff_user_domains": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Provide the domains of the user emails, separated by commas, "
                "that should be treated as staff users (e.g. example.com)."
            ),
            "label": "Staff user domains",
        },
        "default_group_name_for_new_staff_users": {
            "type": ConfigurationTypeField.STRING,
            "help_text": (
                "Provide the name of the default permission group to which the new "
                "staff user should be assigned to. When the provided group doesn't "
                "exist, the new group without any permissions and any channels "
                "will be created."
            ),
            "label": "Default permission group name for new staff users",
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
            user_info_url=configuration["user_info_url"],
            staff_user_domains=configuration["staff_user_domains"],
            default_group_name=configuration["default_group_name_for_new_staff_users"],
        )

        # Determine, if we have defined all fields required to use OAuth access token
        # as Saleor's authorization token.
        self.use_oauth_access_token = bool(
            self.config.user_info_url and self.config.json_web_key_set_url
        )

        # Determine, if we have defined all fields required to process the
        # authorization flow.
        self.use_authorization_flow = bool(
            self.config.json_web_key_set_url
            and self.config.authorization_url
            and self.config.token_url
        )
        self.oauth = self._get_oauth_session()

    @classmethod
    def validate_plugin_configuration(
        cls, plugin_configuration: "PluginConfiguration", **kwargs
    ):
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
            permissions.append(SALEOR_STAFF_PERMISSION)
            scope_permissions = " ".join(permissions)
            scope += f" {scope_permissions}"
        if self.config.enable_refresh_token:
            scope += " offline_access"
        return OAuth2Client(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            scope=scope,
        )

    def _use_scope_permissions(self, user, scope):
        user_permissions = []
        if scope:
            permissions = get_saleor_permissions_qs_from_scope(scope)
            user_permissions = get_saleor_permission_names(permissions)
            user.effective_permissions = permissions
        return user_permissions

    def external_obtain_access_tokens(
        self, data: dict, request: SaleorContext, previous_value
    ) -> ExternalAccessTokens:
        if not self.active:
            return previous_value

        if not self.use_authorization_flow:
            return previous_value

        code = data.get("code")
        if not code:
            msg = "Missing required field - code"
            raise ValidationError(
                {"code": ValidationError(msg, code=PluginErrorCode.NOT_FOUND.value)}
            )

        state = data.get("state")
        if not state:
            msg = "Missing required field - state"
            raise ValidationError(
                {"state": ValidationError(msg, code=PluginErrorCode.NOT_FOUND.value)}
            )

        try:
            state_data = signing.loads(state)
        except signing.BadSignature as e:
            msg = "Bad signature"
            raise ValidationError(
                {"state": ValidationError(msg, code=PluginErrorCode.INVALID.value)}
            ) from e

        redirect_uri = state_data.get("redirectUri")
        if not redirect_uri:
            msg = "The state value is incorrect"
            raise ValidationError(
                {"code": ValidationError(msg, code=PluginErrorCode.INVALID.value)}
            )

        try:
            token_data = self.oauth.fetch_token(
                self.config.token_url, code=code, redirect_uri=redirect_uri
            )
        except AuthlibBaseError as e:
            raise ValidationError(
                {
                    "code": ValidationError(
                        e.description, code=PluginErrorCode.INVALID.value
                    )
                }
            ) from e

        try:
            parsed_id_token = get_parsed_id_token(
                token_data, self.config.json_web_key_set_url
            )
            user, user_created, user_updated = get_or_create_user_from_payload(
                parsed_id_token,
                self.config.authorization_url,
            )
        except AuthenticationError as e:
            raise ValidationError(
                {"code": ValidationError(str(e), code=PluginErrorCode.INVALID.value)}
            ) from e

        user_permissions = []
        is_staff_user_email = self.is_staff_user_email(user)
        if self.config.use_scope_permissions or is_staff_user_email:
            scope = token_data.get("scope")
            user_permissions = self._use_scope_permissions(user, scope)

            is_staff_in_scope = SALEOR_STAFF_PERMISSION in scope
            is_staff_user = is_staff_in_scope or user_permissions or is_staff_user_email
            if is_staff_user:
                assign_staff_to_default_group_and_update_permissions(
                    user, self.config.default_group_name
                )
                if not user.is_staff:
                    user.is_staff = True
                    user_updated = True
                    user.save(update_fields=["is_staff"])
            elif user.is_staff and not is_staff_user:
                user.is_staff = False
                user_updated = True
                user.save(update_fields=["is_staff"])

        if user_created or user_updated:
            send_user_event(user, user_created, user_updated)

        tokens = create_tokens_from_oauth_payload(
            token_data, user, parsed_id_token, user_permissions, owner=self.PLUGIN_ID
        )
        return ExternalAccessTokens(user=user, **tokens)

    def is_staff_user_email(self, user: "User"):
        """Return True if the user email is from staff user domains."""
        staff_user_domains = get_staff_user_domains(self.config)
        email_domain = get_domain_from_email(user.email)
        return email_domain in staff_user_domains

    def external_authentication_url(
        self, data: dict, request: SaleorContext, previous_value
    ) -> dict:
        if not self.active:
            return previous_value

        if not self.use_authorization_flow:
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
        self, data: dict, request: SaleorContext, previous_value
    ) -> ExternalAccessTokens:
        if not self.active:
            return previous_value

        if not self.use_authorization_flow:
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
        refresh_token = cast(str, refresh_token)
        saleor_refresh_token = jwt_decode(refresh_token)
        token_endpoint = self.config.token_url
        try:
            token_data = self.oauth.refresh_token(
                token_endpoint,
                refresh_token=saleor_refresh_token[OAUTH_TOKEN_REFRESH_FIELD],
            )
        except (AuthlibBaseError, HTTPError) as e:
            logger.warning("Unable to refresh the token.", exc_info=True)
            raise ValidationError(
                {
                    "refresh_token": ValidationError(
                        "Unable to refresh the token.",
                        code=error_code,
                    )
                }
            ) from e
        try:
            parsed_id_token = get_parsed_id_token(
                token_data, self.config.json_web_key_set_url
            )
            user = get_user_from_token(parsed_id_token)

            user_permissions = self.get_and_update_user_permissions(
                user, self.config.use_scope_permissions, token_data.get("scope")
            )

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
            ) from e

    def get_and_update_user_permissions(
        self, user: User, use_scope_permissions: bool, scope: str
    ):
        """Update user permissions based on scope and user groups' permissions."""
        permissions = get_user_groups_permissions(user)
        if use_scope_permissions and scope:
            permissions |= get_saleor_permissions_qs_from_scope(scope)
        user.effective_permissions = permissions
        user_permissions = (
            get_saleor_permission_names(permissions) if permissions else []
        )
        return user_permissions

    def external_logout(self, data: dict, request: SaleorContext, previous_value):
        if not self.active:
            return previous_value

        if not self.use_authorization_flow:
            return previous_value

        if not self.config.logout_url:
            # Logout url doesn't exist
            return {}
        req = PreparedRequest()
        req.prepare_url(self.config.logout_url, data)

        return {"logoutUrl": req.url}

    def external_verify(
        self, data: dict, request: SaleorContext, previous_value
    ) -> tuple[User | None, dict]:
        if not self.active:
            return previous_value

        if not self.use_authorization_flow:
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
            if not user:
                return previous_value
            user.is_staff = False
        except (ExpiredSignatureError, InvalidTokenError) as e:
            raise ValidationError({"token": e}) from e
        permissions = payload.get(PERMISSIONS_FIELD)
        if permissions:
            user.is_staff = True
            user.effective_permissions = get_permissions_from_names(permissions)
            assign_staff_to_default_group_and_update_permissions(
                user, self.config.default_group_name
            )
        return user, payload

    def authenticate_user(self, request: SaleorContext, previous_value) -> User | None:
        if not self.active:
            return previous_value
        token = get_token_from_request(request)
        if not token:
            return previous_value
        user = previous_value
        if self.use_authorization_flow and is_owner_of_token_valid(
            token, owner=self.PLUGIN_ID
        ):
            # Check if the token is created by this plugin
            try:
                payload = jwt_decode(token)
                user = get_user_from_access_payload(payload, request)
            except (InvalidTokenError, DecodeError):
                return previous_value
            if user.is_staff:
                assign_staff_to_default_group_and_update_permissions(
                    user, self.config.default_group_name
                )
            return user

        staff_user_domains = get_staff_user_domains(self.config)

        if self.use_oauth_access_token:
            try:
                user = get_user_from_oauth_access_token(
                    token,
                    self.config.json_web_key_set_url,
                    self.config.user_info_url,
                    self.config.use_scope_permissions,
                    self.config.audience,
                    staff_user_domains,
                    self.config.default_group_name,
                )
            except AuthenticationError:
                return previous_value
        return user or previous_value
