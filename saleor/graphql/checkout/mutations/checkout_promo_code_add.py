import graphene

from ...core.mutations import BaseMutation
from ...core.types.common import CheckoutError
from ..types import Checkout


class CheckoutPromoCodeAdd(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the added gift card or voucher."
    )

    class Arguments:
        checkout_id = graphene.ID(description=("The ID of the checkout"), required=True)
        promo_codes = graphene.List(
            graphene.String,
            description="Gift card codes or voucher codes.",
        )

    class Meta:
        description = "Adds a gift card or a voucher to a checkout."
        error_type_class = CheckoutError
