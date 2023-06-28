import graphene

from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_AUTH
from ....core.fields import JSONString
from ....core.mutations import BaseMutation
from ....core.types import AccountError
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import User


class ExternalVerify(BaseMutation):
    user = graphene.Field(User, description="User assigned to data.")
    is_valid = graphene.Boolean(
        required=True,
        default_value=False,
        description="Determine if authentication data is valid or not.",
    )
    verify_data = JSONString(description="External data.")

    class Arguments:
        plugin_id = graphene.String(
            description="The ID of the authentication plugin.", required=True
        )
        input = JSONString(
            required=True,
            description="The data required by plugin to proceed the verification.",
        )

    class Meta:
        description = "Verify external authentication data by plugin."
        doc_category = DOC_CATEGORY_AUTH
        error_type_class = AccountError
        error_type_field = "account_errors"

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, input, plugin_id
    ):
        request = info.context
        manager = get_plugin_manager_promise(info.context).get()
        user, data = manager.external_verify(plugin_id, input, request)
        return cls(user=user, is_valid=bool(user), verify_data=data)
