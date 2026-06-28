import graphene

from .....permission.enums import AccountPermissions
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_324
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.types import CustomerTagError
from ...types import CustomerTag
from .customer_tag_create import CustomerTagInput, CustomerTagMutationBase


class CustomerTagUpdate(CustomerTagMutationBase):
    class Arguments:
        id = graphene.ID(required=True, description="ID of the customer tag to update.")
        input = CustomerTagInput(
            required=True, description="Fields required to update a customer tag."
        )

    class Meta:
        description = "Update an existing customer tag." + ADDED_IN_324
        doc_category = DOC_CATEGORY_USERS
        permissions = (AccountPermissions.MANAGE_CUSTOMER_TAGS,)
        error_type_class = CustomerTagError
        support_meta_field = True
        support_private_meta_field = True

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id, input
    ):
        instance = cls.get_node_or_error(info, id, only_type=CustomerTag)
        cleaned_input = cls.clean_input(instance, input)
        instance = cls.save_instance(info, instance, cleaned_input)
        return cls(customer_tag=instance)
