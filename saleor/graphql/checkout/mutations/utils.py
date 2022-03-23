import datetime
import uuid
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Union

import graphene
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q

from ....checkout import models
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import CheckoutInfo, CheckoutLineInfo
from ....checkout.utils import (
    calculate_checkout_quantity,
    clear_delivery_method,
    is_shipping_required,
)
from ....core.exceptions import InsufficientStock
from ....product import models as product_models
from ....product.models import ProductChannelListing
from ....shipping import interface as shipping_interface
from ....warehouse import models as warehouse_models
from ....warehouse.availability import check_stock_and_preorder_quantity_bulk

ERROR_DOES_NOT_SHIP = "This checkout doesn't need shipping"


def clean_delivery_method(
    checkout_info: "CheckoutInfo",
    lines: Iterable[CheckoutLineInfo],
    method: Optional[
        Union[
            shipping_interface.ShippingMethodData,
            warehouse_models.Warehouse,
        ]
    ],
) -> bool:
    """Check if current shipping method is valid."""

    if not method:
        # no shipping method was provided, it is valid
        return True

    if not is_shipping_required(lines):
        raise ValidationError(
            ERROR_DOES_NOT_SHIP, code=CheckoutErrorCode.SHIPPING_NOT_REQUIRED.value
        )

    if not checkout_info.shipping_address and isinstance(
        method, shipping_interface.ShippingMethodData
    ):
        raise ValidationError(
            "Cannot choose a shipping method for a checkout without the "
            "shipping address.",
            code=CheckoutErrorCode.SHIPPING_ADDRESS_NOT_SET.value,
        )

    valid_methods = checkout_info.valid_delivery_methods
    return method in valid_methods


def update_checkout_shipping_method_if_invalid(
    checkout_info: "CheckoutInfo", lines: Iterable[CheckoutLineInfo]
):
    quantity = calculate_checkout_quantity(lines)

    # remove shipping method when empty checkout
    if quantity == 0 or not is_shipping_required(lines):
        clear_delivery_method(checkout_info)

    is_valid = clean_delivery_method(
        checkout_info=checkout_info,
        lines=lines,
        method=checkout_info.delivery_method_info.delivery_method,
    )

    if not is_valid:
        clear_delivery_method(checkout_info)


def check_lines_quantity(
    variants,
    quantities,
    country,
    channel_slug,
    global_quantity_limit,
    allow_zero_quantity=False,
    existing_lines=None,
    replace=False,
    check_reservations=False,
):
    """Clean quantities and check if stock is sufficient for each checkout line.

    By default, zero quantity is not allowed,
    but if this validation is used for updating existing checkout lines,
    allow_zero_quantities can be set to True
    and checkout lines with this quantity can be later removed.
    """

    for quantity in quantities:
        if not allow_zero_quantity and quantity <= 0:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "The quantity should be higher than zero.",
                        code=CheckoutErrorCode.ZERO_QUANTITY,
                    )
                }
            )

        elif allow_zero_quantity and quantity < 0:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "The quantity should be higher or equal zero.",
                        code=CheckoutErrorCode.ZERO_QUANTITY,
                    )
                }
            )
    try:
        check_stock_and_preorder_quantity_bulk(
            variants,
            country,
            quantities,
            channel_slug,
            global_quantity_limit,
            existing_lines=existing_lines,
            replace=replace,
            check_reservations=check_reservations,
        )
    except InsufficientStock as e:
        errors = [
            ValidationError(
                f"Could not add items {item.variant}. "
                f"Only {max(item.available_quantity, 0)} remaining in stock.",
                code=e.code,
            )
            for item in e.items
        ]
        raise ValidationError({"quantity": errors})


def validate_variants_available_for_purchase(variants_id: set, channel_id: int):
    today = datetime.date.today()
    is_available_for_purchase = Q(
        available_for_purchase__lte=today,
        product__variants__id__in=variants_id,
        channel_id=channel_id,
    )
    available_variants = ProductChannelListing.objects.filter(
        is_available_for_purchase
    ).values_list("product__variants__id", flat=True)
    not_available_variants = variants_id.difference(set(available_variants))
    if not_available_variants:
        variant_ids = [
            graphene.Node.to_global_id("ProductVariant", pk)
            for pk in not_available_variants
        ]
        error_code = CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.value
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines for unavailable for purchase variants.",
                    code=error_code,
                    params={"variants": variant_ids},
                )
            }
        )


def validate_variants_are_published(variants_id: set, channel_id: int):
    published_variants = product_models.ProductChannelListing.objects.filter(
        channel_id=channel_id, product__variants__id__in=variants_id, is_published=True
    ).values_list("product__variants__id", flat=True)
    not_published_variants = variants_id.difference(set(published_variants))
    if not_published_variants:
        variant_ids = [
            graphene.Node.to_global_id("ProductVariant", pk)
            for pk in not_published_variants
        ]
        error_code = CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.value
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines for unpublished variants.",
                    code=error_code,
                    params={"variants": variant_ids},
                )
            }
        )


def get_checkout_by_token(token: uuid.UUID, qs=None):
    if qs is None:
        qs = models.Checkout.objects.select_related(
            "channel",
            "shipping_method",
            "collection_point",
            "billing_address",
            "shipping_address",
        )
    try:
        checkout = qs.get(token=token)
    except ObjectDoesNotExist:
        raise ValidationError(
            {
                "token": ValidationError(
                    f"Couldn't resolve to a node: {token}.",
                    code=CheckoutErrorCode.NOT_FOUND.value,
                )
            }
        )
    return checkout


def group_quantity_by_variants(lines: List[Dict[str, Any]]) -> List[int]:
    variant_quantity_map: Dict[str, int] = defaultdict(int)

    for quantity, variant_id in (line.values() for line in lines):
        variant_quantity_map[variant_id] += quantity

    return list(variant_quantity_map.values())


def validate_checkout_email(checkout: models.Checkout):
    if not checkout.email:
        raise ValidationError(
            "Checkout email must be set.",
            code=CheckoutErrorCode.EMAIL_NOT_SET.value,
        )
