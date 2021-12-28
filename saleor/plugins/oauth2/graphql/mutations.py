import graphene
from django.contrib.auth import get_user_model

from ....graphql.account.mutations.authentication import CreateToken
from ....graphql.core.mutations import BaseMutation
from ..providers import Provider
from ..utils import get_oauth_provider
from .types import OAuth2Error, OAuth2Input, ProviderEnum

User = get_user_model()


class SocialLogin(BaseMutation):
    class Arguments:
        provider = ProviderEnum(required=True)

    class Meta:
        description = "Initiate OAuth2 and get back the authorization URL"
        error_type_class = OAuth2Error

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
        provider: Provider = get_oauth_provider(provider, info)

        auth_endpoint = provider.get_url_for("auth")
        url, state = provider.get_authorization_url()
        scope = provider.scope

        return SocialLogin(
            client_id=provider.client_id,
            baseUrl=auth_endpoint,
            fullUrl=url,
            state=state,
            scope=scope,
        )


class SocialLoginConfirm(CreateToken):
    class Arguments:
        oauth2 = OAuth2Input(description="OAuth2 data.", required=True)

    class Meta:
        description = "Perform an OAuth2 callback"
        error_type_class = OAuth2Error

    @classmethod
    def get_user(cls, _info, auth_response):
        provider: Provider = auth_response["provider"]
        return provider.fetch_user_oauth2(auth_response)

    @classmethod
    def perform_mutation(cls, root, info, oauth2, **kwargs):
        provider = get_oauth_provider(oauth2.provider, info)
        auth_response = provider.fetch_tokens(info, oauth2.code, oauth2.state)
        return super().perform_mutation(root, info, provider=provider, **auth_response)


# class AccountRegisterSocial(ModelMutation):
#     class Arguments:
#         oauth2 = OAuth2Input(description="OAuth2 data.", required=True)

#     class Meta:
#         model = User
#         description = "Register a new user with oauth2 code"
#         error_type_class = OAuth2Error
#         exclude = ["password"]

#     @classmethod
#     def clean_input(cls, info, instance, oauth2, input_cls=None):
#         session = get_oauth2_session(
#             oauth2.provider,
#             info,
#             "Invalid state provided",
#             state=oauth2.state,
#         )

#         auth_response = fetch_tokens(session, info, oauth2_input=oauth2)
#         user_info = fetch_profile_info(auth_response)

#         email = user_info.get("email", None)
#         first_name = get_possible_keys(user_info, ["first_name", "firstName"])
#         last_name = get_possible_keys(user_info, ["last_name", "lastName"])

#         data["channel"] = clean_channel(
#             data.get("channel"), error_class=OAuth2ErrorCode
#         ).slug

#         password = data["password"]
#         try:
#             password_validation.validate_password(password, instance)
#         except ValidationError as error:
#             raise ValidationError({"password": error})

#         return super().clean_input(info, instance, data, input_cls=None)

#     @classmethod
#     @traced_atomic_transaction()
#     def save(cls, info, user, cleaned_input):
#         password = cleaned_input["password"]
#         user.set_password(password)
#         user.search_document = search.prepare_user_search_document_value(
#             user, attach_addresses_data=False
#         )
#         user.save()
#         account_events.customer_account_created_event(user=user)
#         info.context.plugins.customer_created(customer=user)
