import graphene
from django.core.exceptions import ValidationError

from ...core.exceptions import InsufficientStock
from ...order.error_codes import OrderErrorCode
from ...product.models import Product, ProductVariant, ProductVariantChannelListing
from ...warehouse.availability import check_stock_quantity


def validate_total_quantity(order):
    if order.get_total_quantity() == 0:
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Could not create order without any products.",
                    code=OrderErrorCode.REQUIRED,
                )
            }
        )


def validate_shipping_method(order):
    if not order.shipping_method:
        raise ValidationError(
            {
                "shipping": ValidationError(
                    "Shipping method is required.",
                    code=OrderErrorCode.SHIPPING_METHOD_REQUIRED,
                )
            }
        )
    if (
        order.shipping_address.country.code
        not in order.shipping_method.shipping_zone.countries
    ):
        raise ValidationError(
            {
                "shipping": ValidationError(
                    "Shipping method is not valid for chosen shipping address",
                    code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE,
                )
            }
        )


def validate_billing_address(order):
    if not order.billing_address:
        raise ValidationError(
            {
                "order": ValidationError(
                    "Can't finalize draft with no billing address.",
                    code=OrderErrorCode.BILLING_ADDRESS_NOT_SET,
                )
            }
        )


def validate_shipping_address(order):
    if not order.shipping_address:
        raise ValidationError(
            {
                "order": ValidationError(
                    "Can't finalize draft with no shipping address.",
                    code=OrderErrorCode.ORDER_NO_SHIPPING_ADDRESS,
                )
            }
        )


def validate_order_lines(order, country):
    for line in order:
        if line.variant is None:
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Could not create orders with non-existing products.",
                        code=OrderErrorCode.NOT_FOUND,
                    )
                }
            )
        if line.variant.track_inventory:
            try:
                check_stock_quantity(line.variant, country, line.quantity)
            except InsufficientStock as exc:
                raise ValidationError(
                    {
                        "lines": ValidationError(
                            f"Insufficient product stock: {exc.item}",
                            code=OrderErrorCode.INSUFFICIENT_STOCK,
                        )
                    }
                )


def validate_product_is_published(order):
    variant_ids = []
    for line in order:
        variant_ids.append(line.variant_id)
    unpublished_product = Product.objects.filter(
        variants__id__in=variant_ids
    ).not_published(order.channel.slug)
    if unpublished_product.exists():
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Can't finalize draft with unpublished product.",
                    code=OrderErrorCode.PRODUCT_NOT_PUBLISHED,
                )
            }
        )


def validate_product_is_published_in_channel(variants, channel):
    if not channel:
        raise ValidationError(
            "Can't add product variant for draft order without channel",
            code=OrderErrorCode.REQUIRED,
        )
    variant_ids = [variant.id for variant in variants]
    unpublished_product = list(
        Product.objects.filter(variants__id__in=variant_ids).not_published(channel.slug)
    )
    if unpublished_product:
        unpublished_variants = ProductVariant.objects.filter(
            product_id__in=unpublished_product, id__in=variant_ids
        ).values_list("pk", flat=True)
        unpublished_variants_global_ids = [
            graphene.Node.to_global_id("ProductVariant", unpublished_variant)
            for unpublished_variant in unpublished_variants
        ]
        raise ValidationError(
            "Can't add product variant that are not published in "
            "the channel associated with this draft order.",
            code=OrderErrorCode.PRODUCT_NOT_PUBLISHED,
            params={"variants": unpublished_variants_global_ids},
        )


def validate_variant_channel_listings(variants, channel):
    if not channel:
        raise ValidationError(
            "Can't add product variant for draft order without channel",
            code=OrderErrorCode.REQUIRED,
        )
    variant_ids = set([variant.id for variant in variants])
    variant_channel_listings = ProductVariantChannelListing.objects.filter(
        channel=channel, variant_id__in=variant_ids
    )
    variant_ids_in_channel = set(
        [
            variant_channel_listing.variant_id
            for variant_channel_listing in variant_channel_listings
        ]
    )
    missing_variant_ids_in_channel = variant_ids - variant_ids_in_channel
    if missing_variant_ids_in_channel:
        missing_variant_global_ids = [
            graphene.Node.to_global_id("ProductVariant", missing_variant_id_in_channel)
            for missing_variant_id_in_channel in missing_variant_ids_in_channel
        ]
        raise ValidationError(
            "Can't add product variant that are don't have price in"
            "the channel associated with this draft order.",
            code=OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL,
            params={"variants": missing_variant_global_ids},
        )


def validate_product_is_available_for_purchase(order):
    for line in order:
        product_channel_listing = line.variant.product.channel_listings.filter(
            channel_id=order.channel_id
        ).first()
        if not (
            product_channel_listing
            and product_channel_listing.is_available_for_purchase()
        ):
            raise ValidationError(
                {
                    "lines": ValidationError(
                        "Can't finalize draft with product unavailable for purchase.",
                        code=OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE,
                    )
                }
            )


def validate_channel_is_active(channel):
    if not channel.is_active:
        raise ValidationError(
            {
                "channel": ValidationError(
                    "Cannot complete draft order with inactive channel.",
                    code=OrderErrorCode.CHANNEL_INACTIVE.value,
                )
            }
        )


def validate_draft_order(order, country):
    """Check if the given order contains the proper data.

    - Has proper customer data,
    - Shipping address and method are set up,
    - Product variants for order lines still exists in database.
    - Product variants are available in requested quantity.
    - Product variants are published.

    Returns a list of errors if any were found.
    """
    validate_billing_address(order)
    if order.is_shipping_required():
        validate_shipping_address(order)
        validate_shipping_method(order)
    validate_total_quantity(order)
    validate_order_lines(order, country)
    validate_product_is_published(order)
    validate_product_is_available_for_purchase(order)
    validate_channel_is_active(order.channel)
