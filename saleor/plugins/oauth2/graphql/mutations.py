import graphene
import requests
from authlib.integrations.base_client.errors import OAuthError
from authlib.integrations.requests_client import OAuth2Session
from django.core.exceptions import ValidationError

from ....account.models import User
from ....graphql.account.mutations.authentication import CreateToken
from ....graphql.core.mutations import BaseMutation
from ..utils import get_oauth_info, get_state_from_qs, get_uri_for
from .types import OAuth2Error

# from .enums import OAuth2ErrorCode


class ProviderEnum(graphene.Enum):
    Google = "google"
    FACEBOOK = "facebook"


class InitateOAuth2Mutation(BaseMutation):
    class Arguments:
        provider = ProviderEnum(required=True)

    baseUrl = graphene.String(description="Base service authorization URL")

    fullUrl = graphene.String(description="Full service authorization URL")

    client_id = graphene.String(
        description="The client ID of the authorization service"
    )

    response_type = graphene.String(
        default_value="code",
        description="Grant type used by the service",
    )

    scope = graphene.List(
        graphene.String, description="Scope to be used in the service"
    )

    state = graphene.String(description="State provided by OAuth2 provider")

    @classmethod
    def perform_mutation(cls, root, info, provider, **data):
        oauth_info = get_oauth_info(provider, info)
        client_id, client_secret, redirect_uri = oauth_info.values()

        session = OAuth2Session(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=["email"],
        )

        auth_endpoint = get_uri_for(provider, "auth")
        url, state = session.create_authorization_url(auth_endpoint)

        return InitateOAuth2Mutation(
            client_id=client_id,
            baseUrl=auth_endpoint,
            fullUrl=url,
            state=state,
            scope=["email"],
        )

    class Meta:
        description = "Initiate OAuth2 and get back the authorization URL"
        error_type_class = OAuth2Error


class OAuth2CallbackMutation(CreateToken):
    class Arguments:
        provider = ProviderEnum(required=True)
        code = graphene.String(required=True)
        state = graphene.String(required=True)

    @classmethod
    def get_user(cls, _info, auth_response):
        user_info_url = get_uri_for(auth_response["provider"], "userinfo")

        access_token = auth_response["access_token"]

        response = requests.get(
            user_info_url,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code == 200:
            response = response.json()

            email = response["email"]

            try:
                return User.objects.get(email=email)
            except User.DoesNotExist:
                raise ValidationError(
                    message="No user found with the specified email",
                    # code=OAuth2ErrorCode.USER_NOT_FOUND, # not working for some reason
                )

        raise ValidationError(
            message="An error occured while requesting the oauth2 service",
            # code=OAuth2ErrorCode.USER_NOT_FOUND
        )  # TODO change "oauth2 service to provider name"

    @classmethod
    def perform_mutation(cls, root, info, provider, code, state, **kwargs):
        oauth_info = get_oauth_info(provider, info)
        client_id, client_secret, redirect_uri = oauth_info.values()

        state = get_state_from_qs(info)
        token_uri = get_uri_for(provider, "token")

        try:
            session = OAuth2Session(
                client_id=client_id,
                client_secret=client_secret,
                state=state,
            )
        except OAuthError:
            raise ValidationError("Invalid state provided")

        try:
            auth_response = session.fetch_token(
                token_uri,
                code=code,
                state=state,
                grant_type="authorization_code",
                redirect_uri=redirect_uri,
            )
        except OAuthError:
            raise ValidationError(
                "Invalid authentication details",
                # code="oauth2_error",  # not working for some reason
            )

        auth_response["provider"] = provider
        return super().perform_mutation(root, info, **auth_response)

    class Meta:
        description = "Perform an OAuth2 callback"
        error_type_class = OAuth2Error
