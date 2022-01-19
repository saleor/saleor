import graphene
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....account import events as account_events
from ....account import search
from ....core.utils.url import validate_storefront_url
from ....graphql.core.mutations import BaseMutation
from ..providers import Provider
from ..utils import get_oauth_provider, get_user_tokens
from . import enums, types

User = get_user_model()


class SocialLogin(BaseMutation):
    class Arguments:
        provider = types.ProviderEnum(required=True, description="Provider name.")
        redirect_url = graphene.String(
            required=True,
            description="A url to redirect to after authorization is done.",
        )

    class Meta:
        description = "Initiate OAuth2 and get back the authorization URL"
        error_type_class = types.OAuth2Error

    base_url = graphene.String(description="Base service authorization URL")
    full_url = graphene.String(description="Full service authorization URL")
    redirect_url = graphene.String(
        description="A URL to redirect to after successful OAuth2"
    )

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
    def clean_input(cls, root, info, **data):
        redirect_url = data["redirect_url"]
        validate_storefront_url(redirect_url)

    @classmethod
    def perform_mutation(cls, root, info, **data):
        cls.clean_input(root, info, **data)

        provider, redirect_url = data["provider"], data["redirect_url"]
        provider: Provider = get_oauth_provider(provider, info)

        auth_endpoint = provider.get_url_for("auth")
        url, state = provider.get_authorization_url(redirect_url)
        scope = provider.scope

        return SocialLogin(
            client_id=provider.client_id,
            base_url=auth_endpoint,
            full_url=url,
            redirect_url=redirect_url,
            state=state,
            scope=scope,
        )


class SocialLoginByAccessToken(BaseMutation):
    created = graphene.Boolean(description="Describes if the account is created.")
    token = graphene.String(description="JWT token, required to authenticate.")
    refresh_token = graphene.String(
        description="JWT refresh token, required to re-generate access token."
    )
    csrf_token = graphene.String(
        description="CSRF token required to re-generate access token."
    )

    class Arguments:
        input = types.OAuth2TokenInput(description="The OAuth2 data.", required=True)

    class Meta:
        description = "Perform an OAuth2 callback"
        error_type_class = types.OAuth2Error

    @classmethod
    def get_user(cls, info, input, **data):
        provider = data["provider"]
        access_token = data["access_token"]

        profile_info = provider.fetch_profile_info(access_token=access_token)
        email = profile_info.get("email", None)

        if email is None:
            raise ValidationError(
                "Missing email in provider response, have you added the necessary scopes?",  # noqa: E501
                code=enums.OAuth2ErrorCode.OAUTH2_ERROR,
            )

        try:
            user = User.objects.get(email=email)
            created = False
        except User.DoesNotExist:
            password = User.objects.make_random_password()
            user = User(email=email, is_active=True)
            user.set_password(password)
            user.search_document = search.prepare_user_search_document_value(
                user, attach_addresses_data=False
            )
            user.save()
            account_events.customer_account_created_event(user=user)
            info.context.plugins.customer_created(customer=user)
            # TODO: send welcome email
            created = True

        return created, user

    @classmethod
    def get_access_token(cls, **data):
        return data["input"].token

    @classmethod
    def perform_mutation(cls, root, info, **kwargs):
        input = kwargs["input"]
        provider = get_oauth_provider(input.provider, info)
        created, user = cls.get_user(
            info, input, provider=provider, access_token=cls.get_access_token(**kwargs)
        )
        user_tokens = get_user_tokens(user)
        info.context.refresh_token = user_tokens["refresh_token"]
        info.context._cached_user = user
        user.last_login = timezone.now()
        user.save(update_fields=["last_login"])

        return cls(
            errors=[],
            created=created,
            **user_tokens,
        )


class SocialLoginConfirm(SocialLoginByAccessToken):
    class Arguments:
        input = types.OAuth2Input(description="The OAuth2 data.", required=True)

    class Meta:
        description = "Perform an OAuth2 callback with the provider access token."
        error_type_class = types.OAuth2Error

    @classmethod
    def get_access_token(cls, **data):
        return data["auth_response"]["access_token"]

    @classmethod
    def perform_mutation(cls, root, info, **kwargs):
        input = kwargs["input"]
        provider = get_oauth_provider(input.provider, info)
        auth_response = provider.fetch_tokens(
            info, input.code, input.state, input.redirect_url
        )

        kwargs["auth_response"] = auth_response
        return super().perform_mutation(root, info, **kwargs)
