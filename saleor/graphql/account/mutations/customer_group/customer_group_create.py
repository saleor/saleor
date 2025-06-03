import graphene
from django.core.exceptions import ValidationError

from .....account import models
from .....account.error_codes import CustomerGroupErrorCode
from .....permission.enums import AccountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_USERS
from ....core.mutations import BaseMutation
from ....core.types import CustomerGroupError
from ....core.utils import WebhookEventInfo
from ...types import CustomerGroup, CustomerGroupInput


class CustomerGroupCreate(BaseMutation):
    customer_group = graphene.Field(
        CustomerGroup, description="A customer group instance."
    )

    class Arguments:
        input = graphene.Argument(CustomerGroupInput, required=True)

    class Meta:
        auto_permission_message = False
        description = (
            "Create a new customer group.\n\nRequires MANAGE_USERS permission."
        )
        doc_category = DOC_CATEGORY_USERS
        model = models.CustomerGroup
        object_type = CustomerGroup
        error_type_class = CustomerGroupError
        error_type_field = "customer_group_errors"
        permissions = (AccountPermissions.MANAGE_USERS,)
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CUSTOMER_GROUP_CREATED,
            )
        ]

    @classmethod
    def perform_mutation(
        cls, _root, info: ResolveInfo, /, *, input: CustomerGroupInput
    ):
        cls.validate_unique_name(input)
        customer_group = models.CustomerGroup.objects.create(name=input["name"])

        return CustomerGroupCreate(customer_group=customer_group)

    @classmethod
    def validate_unique_name(cls, input: CustomerGroupInput):
        name = input["name"]
        if models.CustomerGroup.objects.filter(name=name).exists():
            raise ValidationError(
                {
                    "name": ValidationError(
                        "Customer group with this name already exists.",
                        code=CustomerGroupErrorCode.UNIQUE.value,
                    )
                }
            )
