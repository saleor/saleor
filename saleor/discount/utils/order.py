from collections.abc import Iterable
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction
from prices import TaxedMoney

from ...channel.models import Channel
from ...core.db.connection import allow_writer
from ...core.prices import quantize_price
from ...core.taxes import zero_money
from ...order.base_calculations import base_order_subtotal
from ...order.models import Order, OrderLine
from .. import DiscountType
from ..interface import VariantPromotionRuleInfo
from ..models import (
    DiscountValueType,
    OrderLineDiscount,
)
from .manual_discount import apply_discount_to_value
from .promotion import (
    _get_rule_discount_amount,
    create_discount_objects_for_order_promotions,
    delete_gift_line,
    get_discount_name,
    get_discount_translated_name,
    prepare_promotion_discount_reason,
)
from .shared import update_line_info_cached_discounts
from .voucher import (
    create_or_update_discount_object_from_order_level_voucher,
    create_or_update_line_discount_objects_from_voucher,
)

if TYPE_CHECKING:
    from ...order.fetch import EditableOrderLineInfo


def create_or_update_discount_objects_for_order(
    order: "Order",
    lines_info: list["EditableOrderLineInfo"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    _update_base_unit_price_amount_for_catalogue_promotion(lines_info)
    create_or_update_line_discount_objects_from_voucher(lines_info)
    create_or_update_line_discount_objects_for_manual_discounts(lines_info)
    create_or_update_discount_object_from_order_level_voucher(
        order, database_connection_name
    )
    create_order_discount_objects_for_order_promotions(
        order, lines_info, database_connection_name=database_connection_name
    )
    _copy_unit_discount_data_to_order_line(lines_info)


def create_order_line_discount_objects(
    lines_info: list["EditableOrderLineInfo"],
    discount_data: tuple[
        list[dict],
        list[OrderLineDiscount],
        list[OrderLineDiscount],
        list[str],
    ],
) -> None | list["EditableOrderLineInfo"]:
    from ...order.utils import order_qs_select_for_update

    if not discount_data or not lines_info:
        return None

    (
        discounts_to_create_inputs,
        discounts_to_update,
        discount_to_remove,
        updated_fields,
    ) = discount_data

    new_line_discounts: list[OrderLineDiscount] = []
    with allow_writer():
        with transaction.atomic():
            # Protect against potential thread race. OrderLine object can have only
            # single catalogue discount applied.
            order_id = lines_info[0].line.order_id
            _order_lock = list(order_qs_select_for_update().filter(id=order_id))

            if discount_ids_to_remove := [
                discount.id for discount in discount_to_remove
            ]:
                OrderLineDiscount.objects.filter(id__in=discount_ids_to_remove).delete()

            if discounts_to_create_inputs:
                new_line_discounts = [
                    OrderLineDiscount(**input) for input in discounts_to_create_inputs
                ]
                OrderLineDiscount.objects.bulk_create(
                    new_line_discounts, ignore_conflicts=True
                )

            if discounts_to_update and updated_fields:
                OrderLineDiscount.objects.bulk_update(
                    discounts_to_update, updated_fields
                )

    update_line_info_cached_discounts(
        lines_info, new_line_discounts, discounts_to_update, discount_ids_to_remove
    )
    affected_line_ids = [
        discount_line.line_id
        for discount_line in (new_line_discounts + discounts_to_update)
    ]
    affected_line_ids.extend(discount_ids_to_remove)
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


def _copy_unit_discount_data_to_order_line(
    lines_info: list["EditableOrderLineInfo"],
):
    for line_info in lines_info:
        if discounts := line_info.discounts:
            line = line_info.line
            discount_amount = sum([discount.amount_value for discount in discounts])
            unit_discount_amount = discount_amount / line.quantity
            discount_reason = "; ".join(
                [discount.reason for discount in discounts if discount.reason]
            )
            discount_type = (
                discounts[0].value_type
                if len(discounts) == 1
                else DiscountValueType.FIXED
            )
            discount_value = (
                discounts[0].value if len(discounts) == 1 else unit_discount_amount
            )

            line.unit_discount_amount = unit_discount_amount
            line.unit_discount_reason = discount_reason
            line.unit_discount_type = discount_type
            line.unit_discount_value = discount_value


def _update_base_unit_price_amount_for_catalogue_promotion(
    lines_info: list["EditableOrderLineInfo"],
):
    for line_info in lines_info:
        line_info.line.base_unit_price = line_info.variant_discounted_price


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


def create_or_update_line_discount_objects_for_manual_discounts(lines_info):
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


def create_order_line_discount_objects_for_catalogue_promotions(
    line: "OrderLine",
    rules_info: Iterable[VariantPromotionRuleInfo],
    channel: Channel,
) -> Iterable["OrderLineDiscount"]:
    from ...order.utils import order_qs_select_for_update

    line_discounts_to_create_inputs: list[dict] = []
    for rule_info in rules_info:
        rule = rule_info.rule
        rule_discount_amount = _get_rule_discount_amount(line, rule_info, channel)
        discount_name = get_discount_name(rule, rule_info.promotion)
        translated_name = get_discount_translated_name(rule_info)
        reason = prepare_promotion_discount_reason(rule_info.promotion)

        line_discount_input = {
            "line": line,
            "type": DiscountType.PROMOTION,
            "value_type": rule.reward_value_type,
            "value": rule.reward_value,
            "amount_value": rule_discount_amount,
            "currency": line.currency,
            "name": discount_name,
            "translated_name": translated_name,
            "reason": reason,
            "promotion_rule": rule,
            "unique_type": DiscountType.PROMOTION,
        }
        line_discounts_to_create_inputs.append(line_discount_input)

    if line_discounts_to_create_inputs:
        with allow_writer():
            with transaction.atomic():
                order_id = line.order_id
                _order_lock = list(order_qs_select_for_update().filter(id=order_id))
                new_line_discounts = [
                    OrderLineDiscount(**input)
                    for input in line_discounts_to_create_inputs
                ]

                return OrderLineDiscount.objects.bulk_create(
                    new_line_discounts, ignore_conflicts=True
                )
    return []
