from collections import defaultdict
from decimal import Decimal
from typing import TYPE_CHECKING, Optional, Union

import graphene

from ...graphql.core.utils import to_global_id_or_none
from .. import DiscountType
from ..models import (
    CheckoutDiscount,
    CheckoutLineDiscount,
    OrderDiscount,
    OrderLineDiscount,
    PromotionRule,
)

if TYPE_CHECKING:
    from ..models import Voucher


def update_discount(
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
    voucher_code: Optional[str],
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
    if voucher_code and discount_to_update.voucher_code != voucher_code:
        discount_to_update.voucher_code = voucher_code
        updated_fields.append("voucher_code")


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


def is_order_level_discount(discount: OrderDiscount) -> bool:
    from .voucher import is_order_level_voucher

    return discount.type in [
        DiscountType.MANUAL,
        DiscountType.ORDER_PROMOTION,
    ] or is_order_level_voucher(discount.voucher)


def discount_info_for_logs(discounts):
    return [
        {
            "id": to_global_id_or_none(discount),
            "type": discount.type,
            "value_type": discount.value_type,
            "value": discount.value,
            "amount_value": discount.amount_value,
            "reason": discount.reason,
            "promotion_rule": {
                "id": to_global_id_or_none(discount.promotion_rule),
                "promotion_id": graphene.Node.to_global_id(
                    "Promotion", discount.promotion_rule.promotion_id
                ),
                "catalogue_predicate": discount.promotion_rule.catalogue_predicate,
                "order_predicate": discount.promotion_rule.order_predicate,
                "reward_value_type": discount.promotion_rule.reward_value_type,
                "reward_value": discount.promotion_rule.reward_value,
                "reward_type": discount.promotion_rule.reward_type,
                "variants_dirty": discount.promotion_rule.variants_dirty,
            }
            if discount.promotion_rule
            else None,
            "voucher": {
                "id": to_global_id_or_none(discount.voucher),
                "type": discount.voucher.type,
                "discount_value_type": discount.voucher.discount_value_type,
                "apply_once_per_order": discount.voucher.apply_once_per_order,
            }
            if discount.voucher
            else None,
        }
        for discount in discounts
    ]
