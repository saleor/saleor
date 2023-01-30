import datetime
import uuid
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal
from typing import (
    TYPE_CHECKING,
    Any,
    DefaultDict,
    Dict,
    Iterable,
    List,
    Optional,
    Type,
    Union,
    cast,
)

import graphene
import pytz
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db.models import Q, QuerySet

from ....checkout import models
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import CheckoutInfo, CheckoutLineInfo
from ....checkout.utils import (
    calculate_checkout_quantity,
    clear_delivery_method,
    is_shipping_required,
)
from ....core.exceptions import InsufficientStock, PermissionDenied
from ....permission.enums import CheckoutPermissions
from ....product import models as product_models
from ....product.models import ProductChannelListing, ProductVariant
from ....shipping import interface as shipping_interface
from ....warehouse import models as warehouse_models
from ....warehouse.availability import check_stock_and_preorder_quantity_bulk
from ...core import ResolveInfo
from ...core.validators import validate_one_of_args_is_in_mutation
from ..types import Checkout

if TYPE_CHECKING:
    from ...core.mutations import BaseMutation


ERROR_DOES_NOT_SHIP = "This checkout doesn't need shipping"


@dataclass
class CheckoutLineData:
    variant_id: Optional[str] = None
    line_id: Optional[str] = None
    quantity: int = 0
    quantity_to_update: bool = False
    custom_price: Optional[Decimal] = None
    custom_price_to_update: bool = False
    metadata_list: Optional[list] = None


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


def get_variants_and_total_quantities(
    variants: List[ProductVariant],
    lines_data: Iterable[CheckoutLineData],
    quantity_to_update_check=False,
):
    variants_total_quantity_map: DefaultDict[ProductVariant, int] = defaultdict(int)
    mapped_data: DefaultDict[Optional[str], int] = defaultdict(int)

    if quantity_to_update_check:
        lines_data = filter(lambda d: d.quantity_to_update, lines_data)

    for data in lines_data:
        mapped_data[data.variant_id] += data.quantity

    for variant in variants:
        quantity = mapped_data.get(str(variant.id), None)
        if quantity is not None:
            variants_total_quantity_map[variant] += quantity

    return variants_total_quantity_map.keys(), variants_total_quantity_map.values()


def check_lines_quantity(
    variants,
    quantities,
    country,
    channel_slug,
    global_quantity_limit,
    delivery_method_info=None,
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
                        code=CheckoutErrorCode.ZERO_QUANTITY.value,
                    )
                }
            )

        elif allow_zero_quantity and quantity < 0:
            raise ValidationError(
                {
                    "quantity": ValidationError(
                        "The quantity should be higher or equal zero.",
                        code=CheckoutErrorCode.ZERO_QUANTITY.value,
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
            delivery_method_info=delivery_method_info,
            existing_lines=existing_lines,
            replace=replace,
            check_reservations=check_reservations,
        )
    except InsufficientStock as e:
        errors = [
            ValidationError(
                f"Could not add items {item.variant}. "
                f"Only {max(item.available_quantity, 0)} remaining in stock.",
                code=e.code.value,
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


def get_checkout_by_token(
    token: uuid.UUID, qs: Optional[QuerySet[models.Checkout]] = None
):
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
    checkout_id: Optional[str] = None,
    token: Optional[uuid.UUID] = None,
    id: Optional[str] = None,
    qs: Optional[QuerySet] = None,
):
    """Return checkout by using the current id field or the deprecated one.

    It is helper logic to return a checkout for mutations that takes into account the
    current `id` field and the deprecated one (`checkout_id`, `token`). If checkout is
    not found, it will raise an exception.
    """

    validate_one_of_args_is_in_mutation(
        "checkout_id", checkout_id, "token", token, "id", id
    )
    if qs is None:
        qs = models.Checkout.objects.select_related(
            "channel__tax_configuration",
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
            checkout_id = cast(str, checkout_id)
            checkout = mutation_class.get_node_or_error(
                info, checkout_id, only_type=Checkout, field="checkout_id", qs=qs
            )
    return checkout


def group_lines_input_on_add(
    lines: List[Dict[str, Any]], existing_lines_info=None
) -> List[CheckoutLineData]:
    """Return list od CheckoutLineData objects.

    Lines data provided in CheckoutLineInput will be grouped depending on
    provided parameters.
    """
    grouped_checkout_lines_data: List[CheckoutLineData] = []
    checkout_lines_data_map: Dict[str, CheckoutLineData] = defaultdict(CheckoutLineData)

    for line in lines:
        variant_id = cast(str, line.get("variant_id"))
        force_new_line = line.get("force_new_line")
        metadata_list = line.get("metadata")

        _, variant_db_id = graphene.Node.from_global_id(variant_id)

        if force_new_line:
            line_data = CheckoutLineData(
                variant_id=variant_db_id, metadata_list=metadata_list
            )
            grouped_checkout_lines_data.append(line_data)
        else:
            _, variant_db_id = graphene.Node.from_global_id(variant_id)

            try:
                line_db_id = find_line_id_when_variant_parameter_used(
                    variant_db_id, existing_lines_info
                )

                if not line_db_id:
                    line_data = checkout_lines_data_map[variant_db_id]
                    line_data.variant_id = variant_db_id
                    line_data.metadata_list = metadata_list
                else:
                    line_data = checkout_lines_data_map[line_db_id]
                    line_data.line_id = line_db_id
                    line_data.variant_id = find_variant_id_when_line_parameter_used(
                        line_db_id, existing_lines_info
                    )

                    if line_data.metadata_list and metadata_list:
                        line_data.metadata_list += metadata_list
                    else:
                        line_data.metadata_list = metadata_list

            # when variant already exist in multiple lines then create a new line
            except ValidationError:
                line_data = CheckoutLineData(
                    variant_id=variant_db_id, metadata_list=metadata_list
                )
                grouped_checkout_lines_data.append(line_data)

        if (quantity := line.get("quantity")) is not None:
            line_data.quantity += quantity
            line_data.quantity_to_update = True

        if "price" in line:
            line_data.custom_price = line["price"]
            line_data.custom_price_to_update = True

    grouped_checkout_lines_data += list(checkout_lines_data_map.values())
    return grouped_checkout_lines_data


def group_lines_input_data_on_update(
    lines: List[Dict[str, Any]], existing_lines_info=None
) -> List[CheckoutLineData]:
    """Return list od CheckoutLineData objects.

    This function is used in CheckoutLinesUpdate mutation.
    Lines data provided in CheckoutLineUpdateInput will be grouped depending on
    provided parameters.
    """
    grouped_checkout_lines_data: List[CheckoutLineData] = []
    checkout_lines_data_map: Dict[str, CheckoutLineData] = defaultdict(CheckoutLineData)

    for line in lines:
        variant_id = cast(str, line.get("variant_id"))
        line_id = cast(str, line.get("line_id"))

        if line_id:
            _, line_db_id = graphene.Node.from_global_id(line_id)

        if variant_id:
            _, variant_db_id = graphene.Node.from_global_id(variant_id)
            line_db_id = find_line_id_when_variant_parameter_used(
                variant_db_id, existing_lines_info
            )

        if not line_db_id:
            line_data = checkout_lines_data_map[variant_db_id]
            line_data.variant_id = variant_db_id
        else:
            line_data = checkout_lines_data_map[line_db_id]
            line_data.line_id = line_db_id
            line_data.variant_id = find_variant_id_when_line_parameter_used(
                line_db_id, existing_lines_info
            )

        if (quantity := line.get("quantity")) is not None:
            line_data.quantity += quantity
            line_data.quantity_to_update = True

        if "price" in line:
            line_data.custom_price = line["price"]
            line_data.custom_price_to_update = True

    grouped_checkout_lines_data += list(checkout_lines_data_map.values())
    return grouped_checkout_lines_data


def check_permissions_for_custom_prices(app, lines):
    """Raise PermissionDenied when custom price is changed by user or app without perm.

    Checkout line custom price can be changed only by app with
    handle checkout permission.
    """
    if any(["price" in line for line in lines]) and (
        not app or not app.has_perm(CheckoutPermissions.HANDLE_CHECKOUTS)
    ):
        raise PermissionDenied(permissions=[CheckoutPermissions.HANDLE_CHECKOUTS])


def find_line_id_when_variant_parameter_used(
    variant_db_id: str, lines_info: List[CheckoutLineInfo]
):
    """Return line id when variantId parameter was used.

    If variant exists in multiple lines error will be returned.
    """
    if not lines_info:
        return

    line_info = list(filter(lambda x: (x.variant.pk == int(variant_db_id)), lines_info))

    if not line_info:
        return

    # if same variant occur in multiple lines `lineId` parameter have to be used
    if len(line_info) > 1:
        message = (
            "Variant occurs in multiple lines. Use `lineId` instead " "of `variantId`."
        )
        variant_global_id = graphene.Node.to_global_id("ProductVariant", variant_db_id)

        raise ValidationError(
            {
                "variantId": ValidationError(
                    message=message,
                    code=CheckoutErrorCode.INVALID.value,
                    params={"variants": [variant_global_id]},
                )
            }
        )

    return str(line_info[0].line.id)


def find_variant_id_when_line_parameter_used(
    line_db_id: str, lines_info: List[CheckoutLineInfo]
):
    """Return variant id when lineId parameter was used."""
    if not lines_info:
        return

    line_info = list(filter(lambda x: (str(x.line.pk) == line_db_id), lines_info))
    return str(line_info[0].line.variant_id)
