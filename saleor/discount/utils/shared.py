from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Union

from ..models import (
    CheckoutDiscount,
    CheckoutLineDiscount,
    OrderDiscount,
    OrderLineDiscount,
    PromotionRule,
    Voucher,
)

if TYPE_CHECKING:
    from ..models import Voucher


def update_line_discount(
    rule: Optional["PromotionRule"],
    voucher: Optional["Voucher"],
    discount_name: str,
    translated_name: str,
    discount_reason: str,
    discount_amount: Decimal,
    value: Decimal,
    value_type: str,
    unique_type: str,
    discount_to_update: Union[
        "CheckoutLineDiscount", "CheckoutDiscount", "OrderLineDiscount", "OrderDiscount"
    ],
    updated_fields: list[str],
):
    if voucher and discount_to_update.voucher_id != voucher.id:
        discount_to_update.voucher_id = voucher.id
        updated_fields.append("voucher_id")
    if rule and discount_to_update.promotion_rule_id != rule.id:
        discount_to_update.promotion_rule_id = rule.id
        updated_fields.append("promotion_rule_id")
    if discount_to_update.value_type != value_type:
        discount_to_update.value_type = value_type
        updated_fields.append("value_type")
    if discount_to_update.value != value:
        discount_to_update.value = value
        updated_fields.append("value")
    if discount_to_update.amount_value != discount_amount:
        discount_to_update.amount_value = discount_amount
        updated_fields.append("amount_value")
    if discount_to_update.name != discount_name:
        discount_to_update.name = discount_name
        updated_fields.append("name")
    if discount_to_update.translated_name != translated_name:
        discount_to_update.translated_name = translated_name
        updated_fields.append("translated_name")

    if discount_to_update.reason != discount_reason:
        discount_to_update.reason = discount_reason
        updated_fields.append("reason")
    if hasattr(discount_to_update, "unique_type"):
        if discount_to_update.unique_type is None:
            discount_to_update.unique_type = unique_type
            updated_fields.append("unique_type")


def update_line_info_cached_discounts(
    lines_info, new_line_discounts, updated_discounts, line_discount_ids_to_remove
):
    if not any([new_line_discounts, updated_discounts, line_discount_ids_to_remove]):
        return

    line_id_line_discounts_map = defaultdict(list)
    for line_discount in new_line_discounts:
        line_id_line_discounts_map[line_discount.line_id].append(line_discount)

    for line_info in lines_info:
        line_info.discounts = [
            discount
            for discount in line_info.discounts
            if discount.id not in line_discount_ids_to_remove
        ]
        if discount := line_id_line_discounts_map.get(line_info.line.id):
            line_info.discounts.extend(discount)
