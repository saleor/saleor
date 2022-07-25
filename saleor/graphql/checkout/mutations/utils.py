import datetime
import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Type, Union, cast

import graphene
import pytz
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q, QuerySet
from graphql import ResolveInfo

from ....checkout import models
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import CheckoutInfo, CheckoutLineInfo
from ....checkout.utils import (
    calculate_checkout_quantity,
    clear_delivery_method,
    is_shipping_required,
)
from ....core.exceptions import InsufficientStock, PermissionDenied
from ....core.permissions import CheckoutPermissions
from ....product import models as product_models
from ....product.models import ProductChannelListing
from ....shipping import interface as shipping_interface
from ....warehouse import models as warehouse_models
from ....warehouse.availability import check_stock_and_preorder_quantity_bulk
from ...core.validators import validate_one_of_args_is_in_mutation
from ..types import Checkout

if TYPE_CHECKING:
    from ...core.mutations import BaseMutation


ERROR_DOES_NOT_SHIP = "This checkout doesn't need shipping"


@dataclass
class CheckoutLineData:
    quantity: int = 0
    quantity_to_update: bool = False
    custom_price: Optional[Decimal] = None
    custom_price_to_update: bool = False


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
    today = datetime.datetime.now(pytz.UTC)
    is_available_for_purchase = Q(
        available_for_purchase_at__lte=today,
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


def get_checkout(
    mutation_class: Type["BaseMutation"],
    info: ResolveInfo,
    checkout_id: str = None,
    token: uuid.UUID = None,
    id: str = None,
    error_class=CheckoutErrorCode,
    qs: QuerySet = None,
):
    """Return checkout by using the current id field or the deprecated one.

    It is helper logic to return a checkout for mutations that takes into account the
    current `id` field and the deprecated one (`checkout_id`, `token`). If checkout is
    not found, it will raise an exception.
    """

    validate_one_of_args_is_in_mutation(
        error_class, "checkout_id", checkout_id, "token", token, "id", id
    )
    if qs is None:
        qs = models.Checkout.objects.select_related(
            "channel",
            "shipping_method",
            "collection_point",
            "billing_address",
            "shipping_address",
        )

    if id:
        checkout = mutation_class.get_node_or_error(
            info, id, only_type=Checkout, field="id", qs=qs
        )
    else:  # DEPRECATED
        if token:
            checkout = get_checkout_by_token(token, qs=qs)
        else:
            checkout = mutation_class.get_node_or_error(
                info, checkout_id, only_type=Checkout, field="checkout_id", qs=qs
            )
    return checkout


def group_quantity_and_custom_prices_by_variants(
    lines: List[Dict[str, Any]]
) -> List[CheckoutLineData]:
    variant_checkout_line_data_map: Dict[str, CheckoutLineData] = defaultdict(
        CheckoutLineData
    )

    for line in lines:
        variant_id = cast(str, line.get("variant_id"))
        line_data = variant_checkout_line_data_map[variant_id]
        if (quantity := line.get("quantity")) is not None:
            line_data.quantity += quantity
            line_data.quantity_to_update = True
        if "price" in line:
            line_data.custom_price = line["price"]
            line_data.custom_price_to_update = True

    return list(variant_checkout_line_data_map.values())


def check_permissions_for_custom_prices(app, lines):
    """Raise PermissionDenied when custom price is changed by user or app without perm.

    Checkout line custom price can be changed only by app with
    handle checkout permission.
    """
    if any(["price" in line for line in lines]) and (
        not app or not app.has_perm(CheckoutPermissions.HANDLE_CHECKOUTS)
    ):
        raise PermissionDenied(permissions=[CheckoutPermissions.HANDLE_CHECKOUTS])
