from decimal import Decimal

import graphene

from saleor.order.fetch import fetch_draft_order_lines_info
from saleor.product.models import (
    ProductVariantChannelListing,
)

from ... import DiscountType, RewardValueType
from ...models import OrderDiscount, OrderLineDiscount
from ...utils import create_or_update_discount_objects_from_promotion_for_order


def test_subtotal_and_catalogue_discounts_applied(draft_order_and_promotions):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    lines_info = fetch_draft_order_lines_info(order)
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


def test_gift_and_catalogue_discount_applied(draft_order_and_promotions):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    lines_info = fetch_draft_order_lines_info(order)
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


def test_fetch_draft_order_lines_info(draft_order_and_promotions):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    channel = order.channel
    lines = order.lines.all()
    line_1 = [line for line in lines if line.quantity == 3][0]
    line_2 = [line for line in lines if line.quantity == 2][0]

    manual_discount = line_1.discounts.create(
        value=Decimal(1),
        amount_value=Decimal(1),
        currency=channel.currency_code,
        name="Manual line discount",
    )

    # when
    lines_info = fetch_draft_order_lines_info(order)

    # then
    line_info_1 = [
        line_info for line_info in lines_info if line_info.line.quantity == 3
    ][0]
    line_info_2 = [
        line_info for line_info in lines_info if line_info.line.quantity == 2
    ][0]

    assert line_info_1.line == line_1
    variant_1 = line_1.variant
    product_1 = variant_1.product
    assert line_info_1.variant == variant_1
    assert (
        line_info_1.channel_listing
        == ProductVariantChannelListing.objects.filter(
            channel=channel, variant=variant_1
        ).first()
    )
    assert line_info_1.product == product_1
    assert line_info_1.product_type == product_1.product_type
    assert line_info_1.collections == []
    assert line_info_1.discounts == [manual_discount]
    assert line_info_1.channel == channel
    assert line_info_1.tax_class == product_1.tax_class
    assert line_info_1.voucher is None
    assert line_info_1.rules_info == []

    assert line_info_2.line == line_2
    variant_2 = line_2.variant
    product_2 = variant_2.product
    assert line_info_2.variant == variant_2
    assert (
        line_info_2.channel_listing
        == ProductVariantChannelListing.objects.filter(
            channel=channel, variant=variant_2
        ).first()
    )
    assert line_info_2.product == product_2
    assert line_info_2.product_type == product_2.product_type
    assert line_info_2.collections == []
    assert line_info_2.discounts == []
    assert line_info_2.channel == channel
    assert line_info_2.tax_class == product_2.tax_class
    assert line_info_2.voucher is None
    rule_info_2 = line_info_2.rules_info[0]
    assert rule_info_2.rule == rule_catalogue
    assert rule_info_2.variant_listing_promotion_rule
    assert rule_info_2.promotion == rule_catalogue.promotion


def test_no_discount_applied(draft_order_and_promotions, product_variant_list):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    rule_total.order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100000}}}
    }
    rule_total.save(update_fields=["order_predicate"])
    rule_gift.order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100000}}}
    }
    rule_total.save(update_fields=["order_predicate"])
    rule_catalogue.catalogue_predicate = {
        "variantPredicate": {
            "ids": [
                graphene.Node.to_global_id("ProductVariant", product_variant_list[0].id)
            ]
        }
    }
    rule_catalogue.save(update_fields=["catalogue_predicate"])
    lines_info = fetch_draft_order_lines_info(order)

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    assert not OrderLineDiscount.objects.exists()
    assert not OrderDiscount.objects.exists()
