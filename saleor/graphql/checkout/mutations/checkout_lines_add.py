import graphene

from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import (
    fetch_checkout_info,
    fetch_checkout_lines,
    update_delivery_method_lists_for_checkout_info,
)
from ....checkout.utils import add_variants_to_checkout, invalidate_checkout_prices
from ....warehouse.reservations import get_reservation_length, is_reservation_enabled
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError, NonNullList
from ...core.validators import validate_variants_available_in_channel
from ...product.types import ProductVariant
from ..types import Checkout
from .checkout_create import CheckoutLineInput
from .utils import (
    check_lines_quantity,
    check_permissions_for_custom_prices,
    get_checkout,
    group_quantity_and_custom_prices_by_variants,
    update_checkout_shipping_method_if_invalid,
    validate_variants_are_published,
    validate_variants_available_for_purchase,
)


class CheckoutLinesAdd(BaseMutation):
    checkout = graphene.Field(Checkout, description="An updated checkout.")

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_34,
            required=False,
        )
        token = UUID(
            description=f"Checkout token.{DEPRECATED_IN_3X_INPUT} Use `id` instead.",
            required=False,
        )
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
        )
        lines = NonNullList(
            CheckoutLineInput,
            required=True,
            description=(
                "A list of checkout lines, each containing information about "
                "an item in the checkout."
            ),
        )

    class Meta:
        description = (
            "Adds a checkout line to the existing checkout."
            "If line was already in checkout, its quantity will be increased."
        )
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def validate_checkout_lines(
        cls,
        info,
        variants,
        checkout_lines_data,
        country,
        channel_slug,
        lines=None,
    ):
        quantities = [line_data.quantity for line_data in checkout_lines_data]
        check_lines_quantity(
            variants,
            quantities,
            country,
            channel_slug,
            info.context.site.settings.limit_quantity_per_checkout,
            existing_lines=lines,
            check_reservations=is_reservation_enabled(info.context.site.settings),
        )

    @classmethod
    def clean_input(
        cls,
        info,
        checkout,
        variants,
        checkout_lines_data,
        checkout_info,
        lines,
        manager,
        discounts,
        replace,
    ):
        channel_slug = checkout_info.channel.slug

        cls.validate_checkout_lines(
            info,
            variants,
            checkout_lines_data,
            checkout.get_country(),
            channel_slug,
            lines=lines,
        )

        variants_ids_to_validate = {
            variant.id
            for variant, line_data in zip(variants, checkout_lines_data)
            if line_data.quantity_to_update and line_data.quantity != 0
        }

        # validate variant only when line quantity is bigger than 0
        if variants_ids_to_validate:
            validate_variants_available_for_purchase(
                variants_ids_to_validate, checkout.channel_id
            )
            validate_variants_available_in_channel(
                variants_ids_to_validate,
                checkout.channel_id,
                CheckoutErrorCode.UNAVAILABLE_VARIANT_IN_CHANNEL,
            )
            validate_variants_are_published(
                variants_ids_to_validate, checkout.channel_id
            )

        if variants and checkout_lines_data:
            checkout = add_variants_to_checkout(
                checkout,
                variants,
                checkout_lines_data,
                channel_slug,
                replace=replace,
                replace_reservations=True,
                reservation_length=get_reservation_length(info.context),
            )

        lines, _ = fetch_checkout_lines(checkout)
        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
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
        return lines

    @classmethod
    def perform_mutation(
        cls, _root, info, lines, checkout_id=None, token=None, id=None, replace=False
    ):
        check_permissions_for_custom_prices(info.context.app, lines)

        checkout = get_checkout(
            cls,
            info,
            checkout_id=checkout_id,
            token=token,
            id=id,
            error_class=CheckoutErrorCode,
        )

        discounts = info.context.discounts
        manager = info.context.plugins

        variant_ids = [line.get("variant_id") for line in lines]
        variants = cls.get_nodes_or_error(variant_ids, "variant_id", ProductVariant)
        checkout_lines_data = group_quantity_and_custom_prices_by_variants(lines)

        shipping_channel_listings = checkout.channel.shipping_method_listings.all()
        checkout_info = fetch_checkout_info(
            checkout, [], discounts, manager, shipping_channel_listings
        )

        lines, _ = fetch_checkout_lines(checkout)
        lines = cls.clean_input(
            info,
            checkout,
            variants,
            checkout_lines_data,
            checkout_info,
            lines,
            manager,
            discounts,
            replace,
        )
        update_checkout_shipping_method_if_invalid(checkout_info, lines)
        invalidate_checkout_prices(checkout_info, lines, manager, discounts, save=True)
        manager.checkout_updated(checkout)

        return CheckoutLinesAdd(checkout=checkout)
