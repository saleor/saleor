from collections.abc import Iterable
from decimal import Decimal
from typing import TYPE_CHECKING

from django.conf import settings
from django.db import transaction

from ...core.db.connection import allow_writer
from ...core.taxes import zero_money
from ...order.models import Order
from ..models import (
    DiscountValueType,
    OrderLineDiscount,
)
from .manual_discount import apply_discount_to_value
from .promotion import (
    create_order_discount_objects_for_order_promotions,
    prepare_line_discount_objects_for_catalogue_promotions,
)
from .shared import update_line_info_cached_discounts
from .voucher import create_or_update_line_discount_objects_from_voucher

if TYPE_CHECKING:
    from ...order.fetch import EditableOrderLineInfo


def create_or_update_discount_objects_for_order(
    order: "Order",
    lines_info: Iterable["EditableOrderLineInfo"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    create_or_update_discount_objects_from_promotion_for_order(
        order, lines_info, database_connection_name
    )
    create_or_update_line_discount_objects_for_manual_discounts(lines_info)
    create_or_update_line_discount_objects_from_voucher(order, lines_info)
    _copy_unit_discount_data_to_order_line(lines_info)


def create_or_update_discount_objects_from_promotion_for_order(
    order: "Order",
    lines_info: Iterable["EditableOrderLineInfo"],
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    create_order_line_discount_objects_for_catalogue_promotions(lines_info)
    # base unit price must reflect all actual catalogue discounts
    _update_base_unit_price_amount_for_catalogue_promotion(lines_info)
    create_order_discount_objects_for_order_promotions(
        order, lines_info, database_connection_name=database_connection_name
    )


def create_order_line_discount_objects_for_catalogue_promotions(
    lines_info: Iterable["EditableOrderLineInfo"],
):
    discount_data = prepare_line_discount_objects_for_catalogue_promotions(lines_info)
    create_order_line_discount_objects(lines_info, discount_data)


def create_order_line_discount_objects(
    lines_info: Iterable["EditableOrderLineInfo"],
    discount_data: tuple[
        list[dict],
        list["OrderLineDiscount"],
        list["OrderLineDiscount"],
        list[str],
    ],
):
    if not discount_data or not lines_info:
        return

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
            order_id = lines_info[0].line.order_id  # type: ignore[index]
            _order_lock = list(
                Order.objects.filter(id=order_id).select_for_update(of=(["self"]))
            )

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


def _copy_unit_discount_data_to_order_line(
    lines_info: Iterable["EditableOrderLineInfo"],
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
    lines_info: Iterable["EditableOrderLineInfo"],
):
    for line_info in lines_info:
        line = line_info.line
        base_unit_price = line.undiscounted_base_unit_price_amount
        for discount in line_info.get_catalogue_discounts():
            unit_discount = discount.amount_value / line.quantity
            base_unit_price -= unit_discount
        line.base_unit_price_amount = max(base_unit_price, Decimal(0))


def create_or_update_line_discount_objects_for_manual_discounts(lines_info):
    discount_to_update: list[OrderLineDiscount] = []
    for line_info in lines_info:
        manual_discount = line_info.get_manual_line_discount()
        if not manual_discount:
            continue
        line = line_info.line
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
