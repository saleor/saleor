from decimal import Decimal

import graphene
import pytest

from ....order import OrderStatus
from ....order.fetch import fetch_draft_order_lines_info
from ....product.models import Product
from ....product.utils.variant_prices import update_discounted_prices_for_promotion
from ....product.utils.variants import fetch_variants_for_promotion_rules
from ... import RewardValueType
from ...models import Promotion, PromotionRule
from ...utils.order import refresh_order_base_prices_and_discounts


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.DRAFT
    return order_with_lines


def test_refresh_order_base_prices(order_with_lines):
    # given
    order = order_with_lines
    line_1, line_2 = order.lines.all()
    variant_1 = line_1.variant

    initial_variant_1_price = line_1.undiscounted_base_unit_price_amount
    initial_variant_2_price = line_2.undiscounted_base_unit_price_amount
    channel_listing = variant_1.channel_listings.get()
    assert initial_variant_1_price == channel_listing.price_amount
    assert initial_variant_1_price == channel_listing.discounted_price_amount

    new_variant_1_price = initial_variant_1_price + Decimal(1)
    channel_listing.price_amount = new_variant_1_price
    channel_listing.discounted_price_amount = new_variant_1_price
    channel_listing.save(update_fields=["price_amount", "discounted_price_amount"])

    lines_info = fetch_draft_order_lines_info(order, lines=None, extend=True)

    # when
    refresh_order_base_prices_and_discounts(order, lines_info)

    # then
    line_1, line_2 = (line_info.line for line_info in lines_info)
    assert line_1.undiscounted_base_unit_price_amount == new_variant_1_price
    assert line_1.base_unit_price_amount == new_variant_1_price
    assert line_2.undiscounted_base_unit_price_amount == initial_variant_2_price
    assert line_2.base_unit_price_amount == initial_variant_2_price


def test_refresh_order_base_prices_catalogue_discount_update(
    order_with_lines_and_catalogue_promotion,
):
    # given
    order = order_with_lines_and_catalogue_promotion
    promotion = Promotion.objects.get()
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rule = promotion.rules.get()
    initial_reward_value = rule.reward_value
    initial_reward_value_type = rule.reward_value_type

    line_1, line_2 = order.lines.all()
    discount = line_1.discounts.first()
    assert initial_reward_value == discount.value
    assert initial_reward_value_type == discount.value_type == RewardValueType.FIXED

    # update catalogue promotion
    new_reward_value = Decimal(50)
    new_reward_value_type = RewardValueType.PERCENTAGE
    rule.reward_value = new_reward_value
    rule.reward_value_type = new_reward_value_type
    rule.save(update_fields=["reward_value", "reward_value_type"])
    fetch_variants_for_promotion_rules(PromotionRule.objects.all())
    update_discounted_prices_for_promotion(Product.objects.all())

    undiscounted_line_1_price = line_1.undiscounted_base_unit_price_amount
    undiscounted_line_2_price = line_2.undiscounted_base_unit_price_amount
    expected_line_1_price = undiscounted_line_1_price * new_reward_value / 100
    expected_unit_discount = undiscounted_line_1_price - expected_line_1_price
    expected_discount_amount = expected_unit_discount * line_1.quantity

    lines_info = fetch_draft_order_lines_info(order, lines=None, extend=True)

    # when
    refresh_order_base_prices_and_discounts(order, lines_info)

    # then
    line_1, line_2 = (line_info.line for line_info in lines_info)
    assert line_1.undiscounted_base_unit_price_amount == undiscounted_line_1_price
    assert line_1.base_unit_price_amount == expected_line_1_price
    assert line_2.undiscounted_base_unit_price_amount == undiscounted_line_2_price
    assert line_2.base_unit_price_amount == undiscounted_line_2_price
    assert line_1.unit_discount_amount == expected_unit_discount
    assert line_1.unit_discount_reason == f"Promotion: {promotion_id}"
    assert line_2.unit_discount_amount == Decimal(0)

    discount.refresh_from_db()
    assert discount.value == new_reward_value
    assert discount.value_type == new_reward_value_type
    assert discount.amount.amount == expected_discount_amount
