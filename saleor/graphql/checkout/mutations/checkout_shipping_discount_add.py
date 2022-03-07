import graphene

from ....permission.enums import CheckoutPermissions
from ...core.mutations import BaseMutation
from ...core.types.common import CheckoutError

from ...order.mutations.order_discount_common import DiscountCommonInput
from ..types import Checkout


class CheckoutShippingDiscountAdd(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="Checkout which has discounted shipping."
    )

    class Arguments:
        checkout_id = graphene.ID(required=True, description="The ID of the checkout.")
        input = DiscountCommonInput(
            required=True,
            description="Fields required to create a discount for the checkout.",
        )

    class Meta:
        description = "Adds discount to the checkout shipping."
        permissions = (CheckoutPermissions.MANAGE_CHECKOUTS,)
        error_type_class = CheckoutError
