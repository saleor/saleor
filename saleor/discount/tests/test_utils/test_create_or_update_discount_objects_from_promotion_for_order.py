from decimal import Decimal

import graphene

from saleor.product.models import ProductVariantChannelListing

from ... import DiscountType, RewardValueType
from ...models import OrderDiscount, OrderLineDiscount
from ...utils import create_or_update_discount_objects_from_promotion_for_order


def test_subtotal_and_catalogue_discounts_applied(
    draft_order_and_promotions, draft_order_lines_info
):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    lines_info = draft_order_lines_info
    discounted_variant_global_id = rule_catalogue.catalogue_predicate[
        "variantPredicate"
    ]["ids"][0]
    _, discounted_variant_id = graphene.Node.from_global_id(
        discounted_variant_global_id
    )

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    order.refresh_from_db()
    assert OrderLineDiscount.objects.count() == 1
    line = order.lines.get(variant_id=discounted_variant_id)
    catalogue_discount = line.discounts.first()
    assert catalogue_discount.type == DiscountType.PROMOTION
    assert catalogue_discount.value == Decimal(3)
    assert catalogue_discount.value == rule_catalogue.reward_value
    assert catalogue_discount.amount_value == Decimal(6)
    assert (
        catalogue_discount.amount_value == line.quantity * rule_catalogue.reward_value
    )
    assert catalogue_discount.value_type == RewardValueType.FIXED

    assert OrderDiscount.objects.count() == 1
    order_discount = order.discounts.first()
    assert order_discount.type == DiscountType.ORDER_PROMOTION
    assert order_discount.amount_value == Decimal(25)
    assert order_discount.amount_value == rule_total.reward_value
    assert order_discount.value_type == RewardValueType.FIXED


def test_gift_discount_applied(draft_order_and_promotions, draft_order_lines_info):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    lines_info = draft_order_lines_info
    rule_total.reward_value = Decimal(0)
    rule_total.save(update_fields=["reward_value"])

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    order.refresh_from_db()
    # If gift reward applies and gift is discounted by catalogue promotion,
    # do not create discount object for catalogue promotion. Instead, create discount
    # object for gift promotion and set reward amount to undiscounted price
    assert OrderLineDiscount.objects.count() == 2
    lines = order.lines.all()
    assert len(lines) == 3
    gift_line = [line for line in lines if line.is_gift][0]
    gift_discount = gift_line.discounts.get()
    assert gift_discount.type == DiscountType.ORDER_PROMOTION
    listing = ProductVariantChannelListing.objects.filter(
        channel=order.channel, variant=gift_line.variant
    ).first()
    assert gift_discount.value == listing.price_amount
    assert not gift_discount.value == listing.discounted_price_amount
    assert gift_discount.value == Decimal(20)

    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]
    assert not line_1.discounts.exists()
    catalogue_discount = line_2.discounts.first()
    assert catalogue_discount.type == DiscountType.PROMOTION

    assert not OrderDiscount.objects.exists()
