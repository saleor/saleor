import graphene

from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.fields import JSONString
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import User


class ExternalRefresh(BaseMutation):
    """Refresh user's access by a custom plugin."""

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
            description="The data required by plugin to proceed the refresh process.",
        )

    class Meta:
        description = "Refresh user's access by custom plugin."
        doc_category = DOC_CATEGORY_AUTH
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, plugin_id
    ):
        request = info.context
        manager = get_plugin_manager_promise(info.context).get()
        access_tokens_response = manager.external_refresh(plugin_id, input, request)
        setattr(info.context, "refresh_token", access_tokens_response.refresh_token)

        if access_tokens_response.user and access_tokens_response.user.id:
            info.context._cached_user = access_tokens_response.user

        return cls(
            token=access_tokens_response.token,
            refresh_token=access_tokens_response.refresh_token,
            csrf_token=access_tokens_response.csrf_token,
            user=access_tokens_response.user,
        )
