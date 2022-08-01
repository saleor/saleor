import graphene
from django.core.exceptions import ValidationError

from ....checkout.checkout_cleaner import validate_checkout_email
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    update_delivery_method_lists_for_checkout_info,
)
from ....checkout.utils import add_promo_code_to_checkout, invalidate_checkout_prices
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ..types import Checkout
from .utils import get_checkout, update_checkout_shipping_method_if_invalid


class CheckoutAddPromoCode(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the added gift card or voucher."
    )

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_34,
            required=False,
        )
        checkout_id = graphene.ID(
            description=(
                f"The ID of the checkout.{DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
            required=False,
        )
        token = UUID(
            description=f"Checkout token.{DEPRECATED_IN_3X_INPUT} Use `id` instead.",
            required=False,
        )
        promo_code = graphene.String(
            description="Gift card code or voucher code.", required=True
        )

    class Meta:
        description = "Adds a gift card or a voucher to a checkout."
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(
        cls, _root, info, promo_code, checkout_id=None, token=None, id=None
    ):
        checkout = get_checkout(
            cls,
            info,
            checkout_id=checkout_id,
            token=token,
            id=id,
            error_class=CheckoutErrorCode,
        )

        validate_checkout_email(checkout)

        manager = info.context.plugins
        discounts = info.context.discounts

        lines, unavailable_variant_pks = fetch_checkout_lines(checkout)
        if unavailable_variant_pks:
            not_available_variants_ids = {
                graphene.Node.to_global_id("ProductVariant", pk)
                for pk in unavailable_variant_pks
            }
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Some of the checkout lines variants are unavailable.",
                        code=CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL.value,
                        params={"variants": not_available_variants_ids},
                    )
                }
            )

        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
        checkout_info = fetch_checkout_info(
            checkout, lines, discounts, manager, shipping_channel_listings
        )

        add_promo_code_to_checkout(
            manager,
            checkout_info,
            lines,
            promo_code,
            discounts,
        )

        update_delivery_method_lists_for_checkout_info(
            checkout_info,
            checkout_info.checkout.shipping_method,
            checkout_info.checkout.collection_point,
            checkout_info.shipping_address,
            lines,
            discounts,
            manager,
            shipping_channel_listings,
        )

        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        invalidate_checkout_prices(
            checkout_info,
            lines,
            manager,
            discounts,
            recalculate_discount=False,
            save=True,
        )
        manager.checkout_updated(checkout)

        return CheckoutAddPromoCode(checkout=checkout)
