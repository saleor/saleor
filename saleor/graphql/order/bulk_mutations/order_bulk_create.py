import graphene

from ....order.models import Order
from ....permission.enums import OrderPermissions
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_312, PREVIEW_FEATURE
from ...core.enums import ErrorPolicyEnum
from ...core.mutations import BaseMutation
from ...core.types import NonNullList
from ...core.types.common import OrderBulkCreateError
from ..mutations.draft_order_create import DraftOrderCreateInput


class OrderBulkCreateResult(graphene.ObjectType):
    order = graphene.Field(
        Order,
        required=False,
        description="Order data." + ADDED_IN_312 + PREVIEW_FEATURE,
    )
    errors = NonNullList(
        OrderBulkCreateError,
        required=False,
        description="List of errors occurred on create attempt."
        + ADDED_IN_312
        + PREVIEW_FEATURE,
    )


class OrderBulkCreate(BaseMutation):
    count = graphene.Int(
        required=True,
        default_value=0,
        description="Returns how many objects were created."
        + ADDED_IN_312
        + PREVIEW_FEATURE,
    )
    results = NonNullList(
        OrderBulkCreateResult,
        required=True,
        default_value=[],
        description="List of the created orders." + ADDED_IN_312 + PREVIEW_FEATURE,
    )

    class Arguments:
        orders = NonNullList(
            DraftOrderCreateInput,
            required=True,
            description="Input list of orders to create."
            + ADDED_IN_312
            + PREVIEW_FEATURE,
        )
        error_policy = ErrorPolicyEnum(
            required=False,
            default_value=ErrorPolicyEnum.REJECT_EVERYTHING.value,
            description=(
                "Policies of error handling. DEFAULT: "
                + ErrorPolicyEnum.REJECT_EVERYTHING.name
                + ADDED_IN_312
                + PREVIEW_FEATURE
            ),
        )

    class Meta:
        description = "Creates multiple orders."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = OrderBulkCreateError
        error_type_field = "bulk_order_errors"

    @classmethod
    def perform_mutation(cls, _root, _info: ResolveInfo, /):
        pass
