import graphene
from django.core.exceptions import ValidationError

from .....account.error_codes import CustomerTagErrorCode
from .....permission.enums import AccountPermissions
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_324, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import CustomerTagError
from ...types import CustomerTag


class CustomerTagDelete(BaseMutation):
    customer_tag = graphene.Field(CustomerTag, description="The deleted customer tag.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the customer tag to delete.")
        force = graphene.Boolean(
            required=False,
            default_value=False,
            description=(
                "Delete the tag even if it is still assigned to users. The "
                "assignments are removed together with the tag. Defaults to false."
            ),
        )

    class Meta:
        description = "Delete a customer tag." + ADDED_IN_324 + PREVIEW_FEATURE
        doc_category = DOC_CATEGORY_USERS
        permissions = (AccountPermissions.MANAGE_CUSTOMER_TAGS,)
        error_type_class = CustomerTagError

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, force=False
    ):
        instance = cls.get_node_or_error(info, id, only_type=CustomerTag)
        if not force and instance.users.exists():
            raise ValidationError(
                {
                    "id": ValidationError(
                        "Cannot delete a customer tag that is still assigned to "
                        "users. Pass `force: true` to delete it anyway.",
                        code=CustomerTagErrorCode.CANNOT_DELETE.value,
                    )
                }
            )
        db_id = instance.id
        instance.delete()
        instance.id = db_id
        return cls(customer_tag=instance)
