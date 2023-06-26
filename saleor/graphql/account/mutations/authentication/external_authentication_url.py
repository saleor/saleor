import graphene

from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.fields import JSONString
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....plugins.dataloaders import get_plugin_manager_promise


class ExternalAuthenticationUrl(BaseMutation):
    """Prepare external authentication url for user by a custom plugin."""

    authentication_data = JSONString(
        description="The data returned by authentication plugin."
    )

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = JSONString(
            required=True,
            description=(
                "The data required by plugin to create external authentication url."
            ),
        )

    class Meta:
        description = "Prepare external authentication URL for user by custom plugin."
        doc_category = DOC_CATEGORY_AUTH
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, plugin_id
    ):
        request = info.context
        manager = get_plugin_manager_promise(info.context).get()
        return cls(
            authentication_data=manager.external_authentication_url(
                plugin_id, input, request
            )
        )
