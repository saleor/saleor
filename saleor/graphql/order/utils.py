from collections import defaultdict
from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

import graphene
from django.conf import settings
from django.core.exceptions import ValidationError

from ...core.exceptions import InsufficientStock
from ...discount.interface import VariantPromotionRuleInfo
from ...discount.models import NotApplicable
from ...discount.utils.voucher import validate_voucher_in_order
from ...order.error_codes import OrderErrorCode
from ...order.utils import (
    get_total_quantity,
    get_valid_shipping_methods_for_order,
    is_shipping_required,
)
from ...plugins.manager import PluginsManager
from ...product.models import Product, ProductChannelListing, ProductVariant
from ...shipping.interface import ShippingMethodData
from ...shipping.utils import convert_to_shipping_method_data
from ...warehouse.availability import check_stock_and_preorder_quantity
from ..core.validators import validate_variants_available_in_channel

if TYPE_CHECKING:
    from ...channel.models import Channel
    from ...order.models import Order, OrderLine

from dataclasses import dataclass

T_ERRORS = dict[str, list[ValidationError]]


@dataclass
class OrderLineData:
    variant_id: Optional[str] = None
    variant: Optional[ProductVariant] = None
    line_id: Optional[str] = None
    price_override: Optional[Decimal] = None
    quantity: int = 0
    rules_info: Optional[Iterable[VariantPromotionRuleInfo]] = None


def validate_total_quantity(lines: Iterable["OrderLine"], errors: T_ERRORS):
    total_quantity = get_total_quantity(lines)
    if total_quantity == 0:
        errors["lines"].append(
            ValidationError(
                "Could not create order without any products.",
                code=OrderErrorCode.REQUIRED.value,
            )
        )


def get_shipping_method_availability_error(
    order: "Order",
    method: Optional["ShippingMethodData"],
    manager: "PluginsManager",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Validate whether shipping method is still available for the order."""
    is_valid = False
    if method:
        valid_methods_ids = {
            m.id
            for m in get_valid_shipping_methods_for_order(
                order,
                order.channel.shipping_method_listings.all(),
                manager,
                database_connection_name=database_connection_name,
            )
            if m.active
        }
        is_valid = method.id in valid_methods_ids

    if not is_valid:
        return ValidationError(
            "Shipping method cannot be used with this order.",
            code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
        )


def validate_shipping_method(
    order: "Order",
    channel: "Channel",
    errors: T_ERRORS,
    manager: "PluginsManager",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    if not order.shipping_method:
        error = ValidationError(
            "Shipping method is required.",
            code=OrderErrorCode.SHIPPING_METHOD_REQUIRED.value,
        )
    elif (
        order.shipping_address
        and order.shipping_address.country.code
        not in order.shipping_method.shipping_zone.countries
    ):
        error = ValidationError(
            "Shipping method is not valid for chosen shipping address",
            code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
        )
    elif not order.shipping_method.shipping_zone.channels.filter(id=order.channel_id):
        error = ValidationError(
            "Shipping method not available in given channel.",
            code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
        )
    else:
        listing = channel.shipping_method_listings.filter(
            shipping_method=order.shipping_method
        ).last()
        if not listing:
            error = ValidationError(
                "Shipping method not available in given channel.",
                code=OrderErrorCode.SHIPPING_METHOD_NOT_APPLICABLE.value,
            )
        else:
            error = get_shipping_method_availability_error(
                order,
                convert_to_shipping_method_data(order.shipping_method, listing),
                manager,
                database_connection_name=database_connection_name,
            )

    if error:
        errors["shipping"].append(error)


def validate_billing_address(order: "Order", errors: T_ERRORS):
    if not order.billing_address:
        errors["order"].append(
            ValidationError(
                "Can't finalize draft with no billing address.",
                code=OrderErrorCode.BILLING_ADDRESS_NOT_SET.value,
            )
        )


def validate_shipping_address(order: "Order", errors: T_ERRORS):
    if not order.shipping_address:
        errors["order"].append(
            ValidationError(
                "Can't finalize draft with no shipping address.",
                code=OrderErrorCode.ORDER_NO_SHIPPING_ADDRESS.value,
            )
        )


def validate_order_lines(
    order: "Order",
    lines: Iterable["OrderLine"],
    channel: "Channel",
    country: str,
    errors: T_ERRORS,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    for line in lines:
        if line.variant is None:
            errors["lines"].append(
                ValidationError(
                    "Could not create orders with non-existing products.",
                    code=OrderErrorCode.NOT_FOUND.value,
                )
            )
        elif line.variant.track_inventory:
            try:
                check_stock_and_preorder_quantity(
                    line.variant,
                    country,
                    channel.slug,
                    line.quantity,
                    order_line=line,
                    database_connection_name=database_connection_name,
                )
            except InsufficientStock as exc:
                errors["lines"].extend(
                    prepare_insufficient_stock_order_validation_errors(exc)
                )


def validate_variants_is_available(
    channel: "Channel",
    lines: Iterable["OrderLine"],
    errors: T_ERRORS,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    variants_ids = {line.variant_id for line in lines}
    try:
        validate_variants_available_in_channel(
            variants_ids,
            channel.id,
            OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.value,
            database_connection_name=database_connection_name,
        )
    except ValidationError as e:
        errors["lines"].extend(e.error_dict["lines"])


def validate_product_is_published(
    channel: "Channel",
    lines: Iterable["OrderLine"],
    errors: T_ERRORS,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    variant_ids = [line.variant_id for line in lines]
    unpublished_product = (
        Product.objects.using(database_connection_name)
        .filter(variants__id__in=variant_ids)
        .not_published(channel)
    )
    if unpublished_product.exists():
        errors["lines"].append(
            ValidationError(
                "Can't finalize draft with unpublished product.",
                code=OrderErrorCode.PRODUCT_NOT_PUBLISHED.value,
            )
        )


def validate_product_is_published_in_channel(
    variants: Iterable[ProductVariant],
    channel: "Channel",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    if not channel:
        raise ValidationError(
            {
                "channel": ValidationError(
                    "Can't add product variant for draft order without channel",
                    code=OrderErrorCode.REQUIRED.value,
                )
            }
        )
    variant_ids = [variant.id for variant in variants]
    unpublished_product = list(
        Product.objects.using(database_connection_name)
        .filter(variants__id__in=variant_ids)
        .not_published(channel)
    )
    if unpublished_product:
        unpublished_variants = (
            ProductVariant.objects.using(database_connection_name)
            .filter(product_id__in=unpublished_product, id__in=variant_ids)
            .values_list("pk", flat=True)
        )
        unpublished_variants_global_ids = [
            graphene.Node.to_global_id("ProductVariant", unpublished_variant)
            for unpublished_variant in unpublished_variants
        ]
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Can't add product variant that are not published in "
                    "the channel associated with this draft order.",
                    code=OrderErrorCode.PRODUCT_NOT_PUBLISHED.value,
                    params={"variants": unpublished_variants_global_ids},
                )
            }
        )


def validate_variant_channel_listings(
    variants: Iterable[ProductVariant], channel: "Channel"
):
    if not channel:
        raise ValidationError(
            {
                "channel": ValidationError(
                    "Can't add product variant for draft order without channel",
                    code=OrderErrorCode.REQUIRED.value,
                )
            }
        )

    variant_ids = {variant.id for variant in variants}
    validate_variants_available_in_channel(
        variant_ids, channel.id, OrderErrorCode.NOT_AVAILABLE_IN_CHANNEL.value
    )


def validate_product_is_available_for_purchase(
    channel: "Channel",
    lines: Iterable["OrderLine"],
    errors: T_ERRORS,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    invalid_lines = []
    for line in lines:
        variant = line.variant
        if not variant:
            continue
        product_channel_listing = (
            ProductChannelListing.objects.using(database_connection_name)
            .filter(channel_id=channel.id, product_id=variant.product_id)
            .first()
        )
        if not (
            product_channel_listing
            and product_channel_listing.is_available_for_purchase()
        ):
            invalid_lines.append(graphene.Node.to_global_id("OrderLine", line.pk))
    if invalid_lines:
        errors["lines"].append(
            ValidationError(
                "Can't finalize draft with product unavailable for purchase.",
                code=OrderErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.value,
                params={"order_lines": invalid_lines},
            )
        )


def validate_channel_is_active(channel: "Channel", errors: T_ERRORS):
    if not channel.is_active:
        errors["channel"].append(
            ValidationError(
                "Cannot complete draft order with inactive channel.",
                code=OrderErrorCode.CHANNEL_INACTIVE.value,
            )
        )


def _validate_voucher(
    order: "Order", lines: Iterable["OrderLine"], channel: "Channel", errors: T_ERRORS
):
    if channel.include_draft_order_in_voucher_usage:
        try:
            validate_voucher_in_order(order, lines, channel)
        except NotApplicable as e:
            errors["voucher"].append(
                ValidationError(
                    message=e.args[0],
                    code=OrderErrorCode.INVALID_VOUCHER.value,
                )
            )


def validate_draft_order(
    order: "Order",
    lines: Iterable["OrderLine"],
    country: str,
    manager: "PluginsManager",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Check if the given order contains the proper data.

    - Has proper customer data,
    - Shipping address and method are set up,
    - Product variants for order lines still exists in database.
    - Product variants are available in requested quantity.
    - Product variants are published.
    - Voucher is properly applied.

    Returns a list of errors if any were found.
    """
    channel = order.channel

    errors: T_ERRORS = defaultdict(list)
    validate_billing_address(order, errors)
    if is_shipping_required(lines):
        validate_shipping_address(order, errors)
        validate_shipping_method(
            order, channel, errors, manager, database_connection_name
        )
    validate_total_quantity(lines, errors)
    validate_order_lines(
        order, lines, channel, country, errors, database_connection_name
    )
    validate_channel_is_active(channel, errors)
    validate_product_is_published(channel, lines, errors, database_connection_name)
    validate_product_is_available_for_purchase(
        channel, lines, errors, database_connection_name
    )
    validate_variants_is_available(channel, lines, errors, database_connection_name)
    _validate_voucher(order, lines, channel, errors)

    if errors:
        raise ValidationError(errors)


def prepare_insufficient_stock_order_validation_errors(exc):
    errors = []
    for item in exc.items:
        order_line_global_id = (
            graphene.Node.to_global_id("OrderLine", item.order_line.pk)
            if item.order_line
            else None
        )
        warehouse_global_id = (
            graphene.Node.to_global_id("Warehouse", item.warehouse_pk)
            if item.warehouse_pk
            else None
        )
        errors.append(
            ValidationError(
                "Insufficient product stock.",
                code=OrderErrorCode.INSUFFICIENT_STOCK.value,
                params={
                    "order_lines": (
                        [order_line_global_id] if order_line_global_id else []
                    ),
                    "warehouse": warehouse_global_id,
                },
            )
        )
    return errors
