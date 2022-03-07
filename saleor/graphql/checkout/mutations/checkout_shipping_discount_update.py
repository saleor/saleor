import graphene

from ....permission.enums import CheckoutPermissions
from ...core.mutations import BaseMutation
from ...core.types.common import CheckoutError

from ...order.mutations.order_discount_common import DiscountCommonInput
from ..types import Checkout


class CheckoutShippingDiscountUpdate(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="Checkout which has updated shipping discount."
    )

    class Arguments:
        discount_id = graphene.ID(
            description="ID of a discount to update.", required=True
        )
        input = DiscountCommonInput(
            required=True,
            description=(
                "Fields required to update a discount for the checkout shipping."
            ),
        )

    class Meta:
        description = "Update discount to the checkout shipping."
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = CheckoutError
