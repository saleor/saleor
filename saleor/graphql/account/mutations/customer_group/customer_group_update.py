import graphene

from .....account import models
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import CustomerGroupError
from ....core.utils import WebhookEventInfo
from ...types import CustomerGroup, CustomerGroupUpdateInput, User
from .customer_group_create import CustomerGroupCreate


class CustomerGroupUpdate(BaseMutation):
    customer_group = graphene.Field(
        CustomerGroup, description="A customer group instance."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of the customer group.")
        input = graphene.Argument(CustomerGroupUpdateInput, required=True)

    class Meta:
        auto_permission_message = False
        description = (
            "Update customer group assignments.\n\nRequires MANAGE_USERS permission."
        )
        doc_category = DOC_CATEGORY_USERS
        model = models.CustomerGroup
        object_type = CustomerGroup
        error_type_class = CustomerGroupError
        error_type_field = "customer_group_errors"
        permissions = (AccountPermissions.MANAGE_USERS,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_GROUP_UPDATED,
            )
        ]

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info: ResolveInfo,
        /,
        *,
        id: str,
        input: CustomerGroupUpdateInput,
    ):
        instance = cls.get_node_or_error(info, id, only_type=CustomerGroup)
        if input.get("name") and input["name"] != instance.name:
            CustomerGroupCreate.validate_unique_name(input)
            instance.name = input["name"]

        if add := input.get("add_customers"):
            instance.customers.add(*cls.get_nodes_or_error(add, "customers", User))

        if remove := input.get("remove_customers"):
            instance.customers.remove(
                *cls.get_nodes_or_error(remove, "customers", User)
            )

        instance.save()

        return CustomerGroupUpdate(customer_group=instance)
