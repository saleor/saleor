from decimal import Decimal
from typing import Optional

from django.utils import timezone

from ...core.exceptions import ProductNotPublished
from ...product import models as product_models
from ...warehouse.availability import check_stock_and_preorder_quantity
from ..fetch import CheckoutInfo
from ..models import Checkout, CheckoutLine


def add_variant_to_checkout(
    checkout_info: "CheckoutInfo",
    variant: product_models.ProductVariant,
    quantity: int = 1,
    price_override: Optional["Decimal"] = None,
    replace: bool = False,
    check_quantity: bool = True,
    force_new_line: bool = False,
    calculate_stocks_with_shipping_zones: bool = True,
):
    """Add a product variant to checkout.

    If `replace` is truthy then any previous quantity is discarded instead
    of added to.

    This function is not used outside of test suite.
    """
    checkout = checkout_info.checkout
    channel_slug = checkout_info.channel.slug

    product_channel_listing = product_models.ProductChannelListing.objects.filter(
        channel_id=checkout.channel_id, product_id=variant.product_id
    ).first()
    if not product_channel_listing or not product_channel_listing.is_published:
        raise ProductNotPublished()

    variant_channel_listing = product_models.ProductVariantChannelListing.objects.get(
        channel_id=checkout.channel_id, variant_id=variant.id
    )
    variant_price_amount = variant.get_base_price(
        variant_channel_listing, price_override
    ).amount
    variant_prior_price_amount = variant.get_prior_price_amount(variant_channel_listing)

    new_quantity, line = check_variant_in_stock(
        checkout,
        variant,
        channel_slug,
        quantity=quantity,
        replace=replace,
        check_quantity=check_quantity,
        calculate_stocks_with_shipping_zones=calculate_stocks_with_shipping_zones,
    )

    if force_new_line:
        checkout.lines.create(
            variant=variant,
            quantity=quantity,
            price_override=price_override,
            undiscounted_unit_price_amount=variant_price_amount,
            prior_unit_price_amount=variant_prior_price_amount,
        )
        return checkout

    if line is None:
        line = checkout.lines.filter(variant=variant).first()

    if new_quantity == 0:
        if line is not None:
            line.delete()
    elif line is None:
        checkout.lines.create(
            variant=variant,
            quantity=new_quantity,
            currency=checkout.currency,
            price_override=price_override,
            undiscounted_unit_price_amount=variant_price_amount,
            prior_unit_price_amount=variant_prior_price_amount,
        )
    elif new_quantity > 0:
        line.quantity = new_quantity
        line.save(update_fields=["quantity"])

    # invalidate calculated prices
    price_expiration = timezone.now()
    checkout.price_expiration = price_expiration
    checkout.discount_expiration = price_expiration

    return checkout


def check_variant_in_stock(
    checkout: Checkout,
    variant: product_models.ProductVariant,
    channel_slug: str,
    quantity: int = 1,
    *,
    calculate_stocks_with_shipping_zones: bool,
    replace: bool = False,
    check_quantity: bool = True,
    checkout_lines: list["CheckoutLine"] | None = None,
    check_reservations: bool = False,
) -> tuple[int, CheckoutLine | None]:
    """Check if a given variant is in stock and return the new quantity + line."""
    line = checkout.lines.filter(variant=variant).first()
    line_quantity = 0 if line is None else line.quantity

    new_quantity = quantity if replace else (quantity + line_quantity)

    if new_quantity < 0:
        raise ValueError(
            f"{quantity!r} is not a valid quantity (results in {new_quantity!r})"
        )

    if new_quantity > 0 and check_quantity:
        check_stock_and_preorder_quantity(
            variant,
            checkout.get_country(),
            channel_slug,
            new_quantity,
            include_shipping_zones=calculate_stocks_with_shipping_zones,
            checkout_lines=checkout_lines,
            check_reservations=check_reservations,
        )

    return new_quantity, line
