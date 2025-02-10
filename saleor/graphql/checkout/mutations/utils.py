import datetime
import uuid
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

import graphene
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Exists, OuterRef, Q, QuerySet
from prices import Money

from ....checkout import models
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import CheckoutInfo, CheckoutLineInfo
from ....checkout.utils import (
    calculate_checkout_quantity,
    clear_delivery_method,
    delete_external_shipping_id_if_present,
    get_external_shipping_id,
    is_shipping_required,
)
from ....core.exceptions import InsufficientStock, PermissionDenied
from ....discount import DiscountType, DiscountValueType
from ....discount.models import CheckoutLineDiscount, PromotionRule
from ....discount.utils.promotion import (
    create_gift_line,
    fetch_promotion_rules_for_checkout_or_order,
    get_best_rule,
)
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
ERROR_CC_ADDRESS_CHANGE_FORBIDDEN = (
    "Can't change shipping address manually. "
    "For click and collect delivery, address is set to a warehouse address."
)


@dataclass
class CheckoutLineData:
    variant_id: str | None = None
    line_id: str | None = None
    quantity: int = 0
    quantity_to_update: bool = False
    custom_price: Decimal | None = None
    custom_price_to_update: bool = False
    metadata_list: list | None = None


def clean_delivery_method(
    checkout_info: "CheckoutInfo",
    method: shipping_interface.ShippingMethodData | warehouse_models.Warehouse | None,
) -> bool:
    """Check if current shipping method is valid."""
    if not method:
        # no shipping method was provided, it is valid
        return True

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


def _is_external_shipping_valid(checkout_info: "CheckoutInfo") -> bool:
    if external_shipping_id := get_external_shipping_id(checkout_info.checkout):
        return external_shipping_id in [
            method.id for method in checkout_info.valid_delivery_methods
        ]
    return True


def update_checkout_external_shipping_method_if_invalid(
    checkout_info: "CheckoutInfo", lines: list[CheckoutLineInfo]
):
    if not _is_external_shipping_valid(checkout_info):
        delete_external_shipping_id_if_present(checkout_info.checkout)


def update_checkout_shipping_method_if_invalid(
    checkout_info: "CheckoutInfo", lines: list[CheckoutLineInfo]
):
    quantity = calculate_checkout_quantity(lines)

    # remove shipping method when empty checkout
    if quantity == 0 or not is_shipping_required(lines):
        clear_delivery_method(checkout_info)

    is_valid = clean_delivery_method(
        checkout_info=checkout_info,
        method=checkout_info.delivery_method_info.delivery_method,
    )

    if not is_valid:
        clear_delivery_method(checkout_info)


def get_variants_and_total_quantities(
    variants: list[ProductVariant],
    lines_data: Iterable[CheckoutLineData],
    quantity_to_update_check=False,
):
    variants_total_quantity_map: defaultdict[ProductVariant, int] = defaultdict(int)
    mapped_data: defaultdict[str | None, int] = defaultdict(int)

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

        if allow_zero_quantity and quantity < 0:
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
        raise ValidationError({"quantity": errors}) from e


def get_not_available_variants_for_purchase(
    variants_id: set, channel_id: int
) -> tuple[set[int], set[str]]:
    today = datetime.datetime.now(tz=datetime.UTC)
    is_available_for_purchase = Q(
        available_for_purchase_at__lte=today,
        product__variants__id__in=variants_id,
        channel_id=channel_id,
    )
    available_variants = ProductChannelListing.objects.filter(
        is_available_for_purchase
    ).values_list("product__variants__id", flat=True)
    not_available_variants = variants_id.difference(set(available_variants))
    not_available_graphql_ids = {
        graphene.Node.to_global_id("ProductVariant", pk)
        for pk in not_available_variants
    }
    return not_available_variants, not_available_graphql_ids


def validate_variants_available_for_purchase(
    variants_id: set,
    channel_id: int,
    error_code: str = CheckoutErrorCode.PRODUCT_UNAVAILABLE_FOR_PURCHASE.value,
):
    (
        not_available_variants,
        not_available_graphql_ids,
    ) = get_not_available_variants_for_purchase(variants_id, channel_id)
    if not_available_variants:
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines for unavailable for purchase variants.",
                    code=error_code,
                    params={"variants": not_available_graphql_ids},
                )
            }
        )


def get_not_published_variants(
    variants_id: set, channel_id: int
) -> tuple[set[int], set[str]]:
    published_variants = product_models.ProductChannelListing.objects.filter(
        channel_id=channel_id, product__variants__id__in=variants_id, is_published=True
    ).values_list("product__variants__id", flat=True)
    not_published_ids = variants_id.difference(set(published_variants))
    not_published_graphql_ids = {
        graphene.Node.to_global_id("ProductVariant", pk) for pk in not_published_ids
    }
    return not_published_ids, not_published_graphql_ids


def validate_variants_are_published(
    variants_id: set,
    channel_id: int,
    error_code: str = CheckoutErrorCode.PRODUCT_NOT_PUBLISHED.value,
):
    not_published_ids, not_published_graphql_ids = get_not_published_variants(
        variants_id, channel_id
    )
    if not_published_ids:
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines for unpublished variants.",
                    code=error_code,
                    params={"variants": not_published_graphql_ids},
                )
            }
        )


def get_checkout_by_token(
    token: uuid.UUID, qs: QuerySet[models.Checkout] | None = None
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
    except ObjectDoesNotExist as e:
        raise ValidationError(
            {
                "token": ValidationError(
                    f"Couldn't resolve to a node: {token}.",
                    code=CheckoutErrorCode.NOT_FOUND.value,
                )
            }
        ) from e
    return checkout


def get_checkout(
    mutation_class: type["BaseMutation"],
    info: ResolveInfo,
    checkout_id: str | None = None,
    token: uuid.UUID | None = None,
    id: str | None = None,
    qs: QuerySet | None = None,
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
    lines: list[dict[str, Any]], existing_lines_info=None
) -> list[CheckoutLineData]:
    """Return list od CheckoutLineData objects.

    Lines data provided in CheckoutLineInput will be grouped depending on
    provided parameters.
    """
    grouped_checkout_lines_data: list[CheckoutLineData] = []
    checkout_lines_data_map: dict[str, CheckoutLineData] = defaultdict(CheckoutLineData)

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
    lines: list[dict[str, Any]], existing_lines_info=None
) -> list[CheckoutLineData]:
    """Return list od CheckoutLineData objects.

    This function is used in CheckoutLinesUpdate mutation.
    Lines data provided in CheckoutLineUpdateInput will be grouped depending on
    provided parameters.
    """
    grouped_checkout_lines_data: list[CheckoutLineData] = []
    checkout_lines_data_map: dict[str, CheckoutLineData] = defaultdict(CheckoutLineData)

    for line in lines:
        variant_id = cast(str, line.get("variant_id"))
        line_id = cast(str, line.get("line_id"))

        line_db_id, variant_db_id = None, None
        if line_id:
            _, line_db_id = graphene.Node.from_global_id(line_id)

        if variant_id:
            _, variant_db_id = graphene.Node.from_global_id(variant_id)
            line_db_id = find_line_id_when_variant_parameter_used(
                variant_db_id, existing_lines_info
            )

        if not line_db_id:
            line_data = checkout_lines_data_map[variant_db_id]  # type: ignore[index]
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
    if any("price" in line for line in lines) and (
        not app or not app.has_perm(CheckoutPermissions.HANDLE_CHECKOUTS)
    ):
        raise PermissionDenied(permissions=[CheckoutPermissions.HANDLE_CHECKOUTS])


def find_line_id_when_variant_parameter_used(
    variant_db_id: str, lines_info: list[CheckoutLineInfo]
) -> None | str:
    """Return line id when variantId parameter was used.

    If variant exists in multiple lines error will be returned.
    """
    if not lines_info:
        return None

    line_info = list(filter(lambda x: (x.variant.pk == int(variant_db_id)), lines_info))

    if not line_info:
        return None

    # if same variant occur in multiple lines `lineId` parameter have to be used
    if len(line_info) > 1:
        message = (
            "Variant occurs in multiple lines. Use `lineId` instead of `variantId`."
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
    line_db_id: str, lines_info: list[CheckoutLineInfo]
) -> None | str:
    """Return variant id when lineId parameter was used."""
    if not lines_info:
        return None

    line_info = list(filter(lambda x: (str(x.line.pk) == line_db_id), lines_info))
    return str(line_info[0].line.variant_id)


def apply_gift_reward_if_applicable_on_checkout_creation(
    checkout: "models.Checkout",
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> None:
    """Apply gift reward if applicable on newly created checkout.

    This method apply the gift reward if any gift promotion exists and
    when it's giving the best discount on the current checkout.
    """
    PromotionRuleChannel = PromotionRule.channels.through
    rule_channels = PromotionRuleChannel.objects.filter(channel_id=checkout.channel_id)
    if not PromotionRule.objects.filter(
        Exists(rule_channels.filter(promotionrule_id=OuterRef("pk"))),
        gifts__isnull=False,
    ).exists():
        return

    _set_checkout_base_subtotal_and_total_on_checkout_creation(checkout)
    rules = fetch_promotion_rules_for_checkout_or_order(checkout)
    best_rule_data = get_best_rule(
        rules,
        checkout.channel,
        checkout.get_country(),
        checkout.base_subtotal,
        database_connection_name,
    )
    if not best_rule_data:
        return

    best_rule, best_discount_amount, gift_listing = best_rule_data
    if not gift_listing:
        return

    with transaction.atomic():
        line, _line_created = create_gift_line(checkout, gift_listing)
        CheckoutLineDiscount.objects.create(
            type=DiscountType.ORDER_PROMOTION,
            line=line,
            amount_value=best_discount_amount,
            value_type=DiscountValueType.FIXED,
            value=best_discount_amount,
            promotion_rule=best_rule,
            currency=checkout.currency,
        )


def _set_checkout_base_subtotal_and_total_on_checkout_creation(
    checkout: "models.Checkout",
):
    """Calculate and set base subtotal and total for newly created checkout."""
    variants_id = [line.variant_id for line in checkout.lines.all()]
    variant_id_to_discounted_price = {
        variant_id: discounted_price or price
        for variant_id, discounted_price, price in product_models.ProductVariantChannelListing.objects.filter(
            variant_id__in=variants_id,
            channel_id=checkout.channel_id,
        ).values_list("variant_id", "discounted_price_amount", "price_amount")
    }
    subtotal = Decimal("0")
    for line in checkout.lines.all():
        if price_amount := line.price_override:
            price = price_amount
        else:
            price = variant_id_to_discounted_price.get(line.variant_id) or Decimal("0")
        subtotal += price * line.quantity
    checkout.base_subtotal = Money(subtotal, checkout.currency)
    # base total and subtotal is the same, as there is no option to set the
    # delivery method during checkout creation
    checkout.base_total = checkout.base_subtotal
    checkout.save(update_fields=["base_subtotal_amount", "base_total_amount"])
