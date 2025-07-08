from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.db.models import prefetch_related_objects
from prices import TaxedMoney

from ...channel.models import Channel
from ...core.db.connection import allow_writer
from ...core.prices import quantize_price
from ...core.taxes import zero_money
from ...order.base_calculations import base_order_subtotal
from ...order.lock_objects import order_qs_select_for_update
from ...order.models import Order, OrderLine
from .. import DiscountType
from ..interface import VariantPromotionRuleInfo
from ..models import DiscountValueType, OrderLineDiscount
from .manual_discount import apply_discount_to_value
from .promotion import (
    _get_rule_discount_amount,
    create_discount_objects_for_order_promotions,
    delete_gift_line,
    get_discount_name,
    get_discount_translated_name,
    is_discounted_line_by_catalogue_promotion,
    prepare_promotion_discount_reason,
    update_promotion_discount,
)
from .shared import update_line_info_cached_discounts

if TYPE_CHECKING:
    from ...order.fetch import EditableOrderLineInfo


def create_order_line_discount_objects(
    lines_info: list["EditableOrderLineInfo"],
    discount_data: tuple[
        list[OrderLineDiscount],
        list[OrderLineDiscount],
        list[OrderLineDiscount],
        list[str],
    ],
) -> None | list["EditableOrderLineInfo"]:
    if not discount_data or not lines_info:
        return None

    (
        discounts_to_create,
        discounts_to_update,
        discount_to_remove,
        updated_fields,
    ) = discount_data

    affected_line_ids: list[UUID] = []
    with allow_writer():
        with transaction.atomic():
            # Protect against potential thread race. OrderLine object can have only
            # single catalogue discount applied.
            order_id = lines_info[0].line.order_id
            _order_lock = list(order_qs_select_for_update().filter(id=order_id))

            if discount_ids_to_remove := [
                discount.id for discount in discount_to_remove
            ]:
                affected_line_ids.extend(
                    discount.line_id
                    for discount in discount_to_remove
                    if discount.line_id is not None
                )
                OrderLineDiscount.objects.filter(id__in=discount_ids_to_remove).delete()

            if discounts_to_create:
                OrderLineDiscount.objects.bulk_create(
                    discounts_to_create, ignore_conflicts=True
                )

            if discounts_to_update and updated_fields:
                OrderLineDiscount.objects.bulk_update(
                    discounts_to_update, updated_fields
                )

    update_line_info_cached_discounts(
        lines_info, discounts_to_create, discounts_to_update, discount_ids_to_remove
    )
    affected_line_ids.extend(
        discount_line.line_id
        for discount_line in (discounts_to_create + discounts_to_update)
        if discount_line.line_id is not None
    )

    modified_lines_info = [
        line_info for line_info in lines_info if line_info.line.id in affected_line_ids
    ]
    return modified_lines_info


def update_catalogue_promotion_discount_amount_for_order(
    discount_to_update: "OrderLineDiscount",
    line: OrderLine,
    quantity: int,
    currency: str,
):
    """Update catalogue promotion discount amount.

    The discount amount must be updated when:
    - line quantity has changed
    - line is updated with custom price
    """
    unit_price = apply_discount_to_value(
        discount_to_update.value,
        discount_to_update.value_type,
        currency,
        line.undiscounted_base_unit_price,
    )
    unit_discount = line.undiscounted_base_unit_price_amount - unit_price.amount
    discount_amount = quantize_price(unit_discount * quantity, currency)
    discount_to_update.amount_value = discount_amount
    discount_to_update.save(update_fields=["amount_value"])


def update_unit_discount_data_on_order_line(
    line: OrderLine, discounts: list[OrderLineDiscount]
):
    unit_discount_reason = (
        "; ".join([discount.reason for discount in discounts if discount.reason])
        or None
    )

    unit_discount_amount = Decimal("0.0")
    unit_discount_type = None
    unit_discount_value = Decimal("0.0")
    if discounts:
        discount_amount = sum(
            [discount.amount_value for discount in discounts], Decimal("0.0")
        )
        unit_discount_amount = quantize_price(
            discount_amount / line.quantity, line.currency
        )

        more_than_one_discount = len(discounts) > 1
        if more_than_one_discount:
            unit_discount_type = DiscountValueType.FIXED
            unit_discount_value = unit_discount_amount
        else:
            discount = discounts[0]
            unit_discount_type = discount.value_type
            unit_discount_value = discount.value

    line.unit_discount_amount = unit_discount_amount
    line.unit_discount_reason = unit_discount_reason
    line.unit_discount_type = unit_discount_type
    line.unit_discount_value = unit_discount_value


def update_unit_discount_data_on_order_lines_info(
    lines_info: list["EditableOrderLineInfo"],
):
    for line_info in lines_info:
        line = line_info.line
        update_unit_discount_data_on_order_line(line, line_info.discounts)


def handle_order_promotion(
    order: "Order",
    lines_info,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    create_order_discount_objects_for_order_promotions(
        order, lines_info, database_connection_name=database_connection_name
    )
    # order object
    _clear_prefetched_order_discounts(order)
    with allow_writer():
        # TODO: Load discounts with a dataloader and pass as argument
        prefetch_related_objects([order], "discounts")


def create_order_discount_objects_for_order_promotions(
    order: "Order",
    lines_info: list["EditableOrderLineInfo"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    from ...order.utils import get_order_country

    # If voucher is set or manual discount applied, then skip order promotions
    if order.voucher_code or order.discounts.filter(type=DiscountType.MANUAL):
        _clear_order_discount(order, lines_info)
        return

    # The base prices are required for order promotion discount qualification.
    _set_order_base_prices(order, lines_info)

    lines = [line_info.line for line_info in lines_info]
    subtotal = base_order_subtotal(order, lines)
    with allow_writer():
        country = get_order_country(order)

    (
        gift_promotion_applied,
        discount_object,
    ) = create_discount_objects_for_order_promotions(
        order,
        lines_info,
        subtotal,
        order.channel,
        country,
        database_connection_name=database_connection_name,
    )
    if not gift_promotion_applied and not discount_object:
        _clear_order_discount(order, lines_info)
        return


def _clear_prefetched_order_discounts(order):
    if hasattr(order, "_prefetched_objects_cache"):
        order._prefetched_objects_cache.pop("discounts", None)


def _set_order_base_prices(order: Order, lines_info: list["EditableOrderLineInfo"]):
    """Set base order prices that includes only catalogue discounts."""
    lines = [line_info.line for line_info in lines_info]
    subtotal = base_order_subtotal(order, lines)
    shipping_price = order.undiscounted_base_shipping_price
    total = subtotal + shipping_price

    update_fields = []
    if order.subtotal != TaxedMoney(net=subtotal, gross=subtotal):
        order.subtotal = TaxedMoney(net=subtotal, gross=subtotal)
        update_fields.extend(["subtotal_net_amount", "subtotal_gross_amount"])
    if order.total != TaxedMoney(net=total, gross=total):
        order.total = TaxedMoney(net=total, gross=total)
        update_fields.extend(["total_net_amount", "total_gross_amount"])

    if update_fields:
        with allow_writer():
            order.save(update_fields=update_fields)


@allow_writer()
def _clear_order_discount(
    order_or_checkout: Order,
    lines_info: list["EditableOrderLineInfo"],
):
    with transaction.atomic():
        delete_gift_line(order_or_checkout, lines_info)
        order_or_checkout.discounts.filter(type=DiscountType.ORDER_PROMOTION).delete()


def _create_order_line_discount_for_catalogue_promotion(
    line: OrderLine, rule_info: VariantPromotionRuleInfo, channel: Channel
):
    rule = rule_info.rule
    if rule.reward_value_type is None or rule.reward_value is None:
        raise ValueError(
            "Reward value type and reward value cannot be NULL for catalogue promotions."
        )
    rule_discount_amount = _get_rule_discount_amount(line, rule_info, channel)
    discount_name = get_discount_name(rule, rule_info.promotion)
    translated_name = get_discount_translated_name(rule_info)
    reason = prepare_promotion_discount_reason(rule_info.promotion)
    return OrderLineDiscount(
        line=line,
        type=DiscountType.PROMOTION,
        value_type=rule.reward_value_type,
        value=rule.reward_value,
        amount_value=rule_discount_amount,
        currency=line.currency,
        name=discount_name,
        translated_name=translated_name,
        reason=reason,
        promotion_rule=rule,
        unique_type=DiscountType.PROMOTION,
    )


def create_order_line_discount_objects_for_catalogue_promotions(
    line: "OrderLine",
    rules_info: Iterable[VariantPromotionRuleInfo],
    channel: Channel,
) -> list["OrderLineDiscount"]:
    line_discounts_to_create: list[OrderLineDiscount] = []
    for rule_info in rules_info:
        line_discount = _create_order_line_discount_for_catalogue_promotion(
            line, rule_info, channel
        )
        line_discounts_to_create.append(line_discount)

    if line_discounts_to_create:
        with allow_writer():
            with transaction.atomic():
                order_id = line.order_id
                _order_lock = list(order_qs_select_for_update().filter(id=order_id))
                return OrderLineDiscount.objects.bulk_create(
                    line_discounts_to_create, ignore_conflicts=True
                )
    return []


def refresh_order_line_discount_objects_for_catalogue_promotions(
    lines_info: list["EditableOrderLineInfo"],
):
    discount_data = prepare_order_line_discount_objects_for_catalogue_promotions(
        lines_info
    )
    create_order_line_discount_objects(lines_info, discount_data)
    _update_base_unit_price_amount_for_catalogue_promotion(lines_info)


def prepare_order_line_discount_objects_for_catalogue_promotions(lines_info):
    line_discounts_to_create: list[OrderLineDiscount] = []
    line_discounts_to_update: list[OrderLineDiscount] = []
    line_discounts_to_remove: list[OrderLineDiscount] = []
    updated_fields: list[str] = []

    if not lines_info:
        return None

    for line_info in lines_info:
        line = line_info.line

        # get the existing catalogue discount for the line
        discount_to_update = None
        if discounts_to_update := line_info.get_catalogue_discounts():
            discount_to_update = discounts_to_update[0]
            # Line should never have multiple catalogue discounts associated. Before
            # introducing unique_type on discount models, there was such a possibility.
            line_discounts_to_remove.extend(discounts_to_update[1:])

        # manual line discount do not stack with other line discounts
        if [
            discount
            for discount in line_info.discounts
            if discount.type == DiscountType.MANUAL
        ]:
            line_discounts_to_remove.extend(discounts_to_update)
            continue

        # check if the line price is discounted by catalogue promotion
        discounted_line = is_discounted_line_by_catalogue_promotion(
            line_info.channel_listing
        )

        # delete all existing discounts if the line is not discounted or it is a gift
        if not discounted_line or line.is_gift:
            line_discounts_to_remove.extend(discounts_to_update)
            continue

        if line_info.rules_info:
            rule_info = line_info.rules_info[0]
            rule = rule_info.rule
            if not discount_to_update:
                line_discount = _create_order_line_discount_for_catalogue_promotion(
                    line, rule_info, line_info.channel
                )
                line_discounts_to_create.append(line_discount)
            else:
                rule_discount_amount = _get_rule_discount_amount(
                    line, rule_info, line_info.channel
                )
                update_promotion_discount(
                    rule,
                    rule_info,
                    rule_discount_amount,
                    discount_to_update,
                    updated_fields,
                )
                line_discounts_to_update.append(discount_to_update)
        else:
            # Fallback for unlike mismatch between discount_amount and rules_info
            line_discounts_to_remove.extend(discounts_to_update)

    return (
        line_discounts_to_create,
        line_discounts_to_update,
        line_discounts_to_remove,
        updated_fields,
    )


def _update_base_unit_price_amount_for_catalogue_promotion(
    lines_info: list["EditableOrderLineInfo"],
):
    for line_info in lines_info:
        line = line_info.line
        base_unit_price = line.undiscounted_base_unit_price_amount
        for discount in line_info.get_catalogue_discounts():
            unit_discount = discount.amount_value / line.quantity
            base_unit_price -= unit_discount
        line.base_unit_price_amount = max(base_unit_price, Decimal(0))


def refresh_manual_line_discount_object(lines_info):
    discount_to_update: list[OrderLineDiscount] = []
    for line_info in lines_info:
        manual_discount = line_info.get_manual_line_discount()
        if not manual_discount:
            continue
        line = line_info.line
        # manual line discounts do not combine with other line-level discounts
        base_unit_price = line.undiscounted_base_unit_price
        reduced_unit_price = apply_discount_to_value(
            manual_discount.value,
            manual_discount.value_type,
            line.currency,
            base_unit_price,
        )
        reduced_unit_price = max(reduced_unit_price, zero_money(line.currency))
        line.base_unit_price_amount = reduced_unit_price.amount

        discount_unit_amount = (base_unit_price - reduced_unit_price).amount
        discount_amount = discount_unit_amount * line.quantity
        if manual_discount.amount_value != discount_amount:
            manual_discount.amount_value = discount_amount
            discount_to_update.append(manual_discount)

    if discount_to_update:
        OrderLineDiscount.objects.bulk_update(discount_to_update, ["amount_value"])
