import graphene

from ...core.mutations import BaseMutation
from ...core.types.common import CheckoutError
from ..types import Checkout


class CheckoutPromoCodeRemove(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the removed gift card or voucher."
    )

    class Arguments:
        checkout_id = graphene.ID(
            description=("The ID of the checkout."), required=True
        )
        promo_codes = graphene.List(
            graphene.String,
            description="Gift card codes or voucher codes.",
            required=False,
        )
        promo_code_ids = graphene.List(
            graphene.ID,
            description="Gift card or voucher ID's.",
            required=False,
        )

    class Meta:
        description = "Remove a gift card or a voucher from a checkout."
        error_type_class = CheckoutError
