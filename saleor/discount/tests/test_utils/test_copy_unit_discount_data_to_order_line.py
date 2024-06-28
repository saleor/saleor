from decimal import Decimal

import graphene

from ....order.fetch import fetch_draft_order_lines_info
from ... import DiscountType, DiscountValueType
from ...models import PromotionRule
from ...utils.order import _copy_unit_discount_data_to_order_line


def test_copy_unit_discount_data_to_order_line_multiple_discounts(
    order_with_lines_and_catalogue_promotion,
):
    # given
    order = order_with_lines_and_catalogue_promotion
    rule = PromotionRule.objects.get()
    rule_reward_value = rule.reward_value
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    rule_discount_reason = f"Promotion: {promotion_id}"

    line = order.lines.first()
    rule_discount = line.discounts.get()
    rule_discount.reason = rule_discount_reason
    rule_discount.save(update_fields=["reason"])

    manual_reward_value = Decimal("2")
    manual_discount_reason = "Manual discount"
    line.discounts.create(
        type=DiscountType.MANUAL,
        value_type=DiscountValueType.FIXED,
        value=manual_reward_value,
        amount_value=manual_reward_value * line.quantity,
        currency=order.currency,
        reason=manual_discount_reason,
    )

    assert line.discounts.count() == 2
    lines_info = fetch_draft_order_lines_info(order)

    # when
    _copy_unit_discount_data_to_order_line(lines_info)

    # then
    line = lines_info[0].line
    assert line.unit_discount_amount == rule_reward_value + manual_reward_value
    assert rule_discount_reason in line.unit_discount_reason
    assert manual_discount_reason in line.unit_discount_reason
    assert line.unit_discount_type == DiscountValueType.FIXED
    assert line.unit_discount_value == line.unit_discount_amount


def test_copy_unit_discount_data_to_order_line_single_discount(
    order_with_lines_and_catalogue_promotion,
):
    # given
    order = order_with_lines_and_catalogue_promotion
    rule = PromotionRule.objects.get()
    rule_reward_value = rule.reward_value
    promotion_id = graphene.Node.to_global_id("Promotion", rule.promotion_id)
    rule_discount_reason = f"Promotion: {promotion_id}"

    line = order.lines.first()
    rule_discount = line.discounts.get()
    rule_discount.reason = rule_discount_reason
    rule_discount.save(update_fields=["reason"])

    assert line.discounts.count() == 1
    lines_info = fetch_draft_order_lines_info(order)

    # when
    _copy_unit_discount_data_to_order_line(lines_info)

    # then
    line = lines_info[0].line
    assert line.unit_discount_amount == rule_reward_value
    assert line.unit_discount_reason == rule_discount_reason
    assert line.unit_discount_type == rule.reward_value_type
    assert line.unit_discount_value == rule_reward_value


def test_copy_unit_discount_data_to_order_line_no_discount(order_with_lines):
    # given
    order = order_with_lines
    line = order.lines.first()
    assert not line.discounts.exists()
    lines_info = fetch_draft_order_lines_info(order)

    # when
    _copy_unit_discount_data_to_order_line(lines_info)

    # then
    line = lines_info[0].line
    assert line.unit_discount_amount == Decimal(0)
    assert not line.unit_discount_reason
    assert line.unit_discount_type is None
    assert line.unit_discount_value == Decimal(0)
