import graphene

from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.fields import JSONString
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....directives import doc
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import User
from .utils import update_user_last_login_if_required


@doc(category=DOC_CATEGORY_AUTH)
class ExternalObtainAccessTokens(BaseMutation):
    """Obtain session tokens from an external authentication mechanism."""

    token = graphene.String(description="The token, required to authenticate.")
    refresh_token = graphene.String(
        description="The refresh token, required to re-generate external access token."
    )
    csrf_token = graphene.String(
        description="CSRF token required to re-generate external access token."
    )
    user = graphene.Field(User, description="A user instance.")

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = JSONString(
            required=True,
            description="The data required by plugin to create authentication data.",
        )

    class Meta:
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, plugin_id
    ):
        request = info.context
        manager = get_plugin_manager_promise(info.context).get()
        access_tokens_response = manager.external_obtain_access_tokens(
            plugin_id, input, request
        )
        setattr(info.context, "refresh_token", access_tokens_response.refresh_token)

        if access_tokens_response.user and access_tokens_response.user.id:
            user = access_tokens_response.user
            info.context._cached_user = user
            update_user_last_login_if_required(user)

        return cls(
            token=access_tokens_response.token,
            refresh_token=access_tokens_response.refresh_token,
            csrf_token=access_tokens_response.csrf_token,
            user=access_tokens_response.user,
        )
