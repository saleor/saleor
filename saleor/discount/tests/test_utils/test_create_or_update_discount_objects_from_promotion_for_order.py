from decimal import Decimal

import graphene

from ....order.fetch import fetch_draft_order_lines_info
from ....product.models import (
    ProductVariantChannelListing,
    VariantChannelListingPromotionRule,
)
from ....warehouse.models import Stock
from ... import DiscountType, RewardType, RewardValueType
from ...models import OrderDiscount, OrderLineDiscount
from ...utils.order import create_or_update_discount_objects_from_promotion_for_order


def test_create_catalogue_discount_fixed(
    order_with_lines,
    catalogue_promotion_without_rules,
):
    # given
    order = order_with_lines
    promotion = catalogue_promotion_without_rules
    channel = order.channel
    line_1 = order.lines.get(quantity=3)

    # prepare catalogue promotions
    variant_1 = line_1.variant
    reward_value = Decimal(3)
    rule = promotion.rules.create(
        name="Catalogue rule fixed",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant_1.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    listing = variant_1.channel_listings.get(channel=channel)
    undiscounted_price = listing.price_amount
    listing.discounted_price_amount = undiscounted_price - reward_value
    listing.save(update_fields=["discounted_price_amount"])

    currency = order.currency
    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=reward_value,
        currency=currency,
    )
    lines_info = fetch_draft_order_lines_info(order)

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    assert OrderLineDiscount.objects.count() == 1
    assert not OrderDiscount.objects.exists()
    discount = OrderLineDiscount.objects.get()
    assert discount.line == line_1
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.PROMOTION
    assert discount.value_type == RewardValueType.FIXED
    assert discount.value == reward_value == Decimal(3)
    assert discount.amount_value == reward_value * line_1.quantity == Decimal(9)
    assert discount.currency == channel.currency_code
    assert discount.name == f"{promotion.name}: {rule.name}"

    line = [line_info.line for line_info in lines_info if line_info.line == line_1][0]
    assert line.base_unit_price_amount == Decimal(7)


def test_create_catalogue_discount_percentage(
    order_with_lines,
    catalogue_promotion_without_rules,
):
    # given
    order = order_with_lines
    promotion = catalogue_promotion_without_rules
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    channel = order.channel
    line_1 = order.lines.get(quantity=3)

    variant_1 = line_1.variant
    reward_value = Decimal(50)
    rule = promotion.rules.create(
        name="Catalogue rule percentage",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant_1.id)]
            }
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    listing = variant_1.channel_listings.get(channel=channel)
    undiscounted_price = listing.price_amount
    discount_amount = undiscounted_price * reward_value / 100
    listing.discounted_price_amount = discount_amount
    listing.save(update_fields=["discounted_price_amount"])

    currency = order.currency
    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule,
        discount_amount=discount_amount,
        currency=currency,
    )
    lines_info = fetch_draft_order_lines_info(order)

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    assert OrderLineDiscount.objects.count() == 1
    assert not OrderDiscount.objects.exists()
    discount = OrderLineDiscount.objects.get()
    assert discount.line == line_1
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.PROMOTION
    assert discount.value_type == RewardValueType.PERCENTAGE
    assert discount.value == reward_value == Decimal(50)
    assert discount.amount_value == discount_amount * line_1.quantity == Decimal(15)
    assert discount.currency == channel.currency_code
    assert discount.name == f"{promotion.name}: {rule.name}"
    assert discount.reason == f"Promotion: {promotion_id}"

    line = [line_info.line for line_info in lines_info if line_info.line == line_1][0]
    assert line.base_unit_price_amount == Decimal(5)


def test_create_order_discount_subtotal_fixed(
    order_with_lines, order_promotion_without_rules
):
    # given
    order = order_with_lines
    channel = order.channel
    promotion = order_promotion_without_rules
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    reward_value = Decimal(25)
    rule = promotion.rules.create(
        name="Fixed subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseTotalPrice": {"range": {"gte": 10}}}
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(order.channel)

    lines_info = fetch_draft_order_lines_info(order)

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    assert OrderDiscount.objects.count() == 1
    assert not OrderLineDiscount.objects.exists()
    discount = OrderDiscount.objects.get()
    assert discount.order == order
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value_type == RewardValueType.FIXED
    assert discount.value == reward_value == Decimal(25)
    assert discount.amount_value == reward_value == Decimal(25)
    assert discount.currency == channel.currency_code
    assert discount.name == f"{promotion.name}: {rule.name}"
    assert discount.reason == f"Promotion: {promotion_id}"


def test_create_order_discount_subtotal_percentage(
    order_with_lines, order_promotion_without_rules
):
    # given
    order = order_with_lines
    channel = order.channel
    promotion = order_promotion_without_rules
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    reward_value = Decimal(50)
    rule = promotion.rules.create(
        name="Percentage subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"eq": 70}}
        },
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=reward_value,
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(order.channel)

    lines_info = fetch_draft_order_lines_info(order)

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    assert OrderDiscount.objects.count() == 1
    assert not OrderLineDiscount.objects.exists()
    discount = OrderDiscount.objects.get()
    assert discount.order == order
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value_type == RewardValueType.PERCENTAGE
    assert discount.value == reward_value == Decimal(50)
    assert discount.amount_value == Decimal(35)
    assert discount.currency == channel.currency_code
    assert discount.name == f"{promotion.name}: {rule.name}"
    assert discount.reason == f"Promotion: {promotion_id}"


def test_create_order_discount_gift(
    order_with_lines, order_promotion_without_rules, variant_with_many_stocks
):
    # given
    order = order_with_lines
    variant = variant_with_many_stocks
    product = variant.product
    channel = order.channel
    promotion = order_promotion_without_rules
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rule = promotion.rules.create(
        name="Gift subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
        },
        reward_type=RewardType.GIFT,
    )
    rule.channels.add(channel)
    rule.gifts.set([variant])

    lines_info = fetch_draft_order_lines_info(order)

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    assert OrderLineDiscount.objects.count() == 1
    assert not OrderDiscount.objects.exists()
    lines = order.lines.all()
    assert len(lines) == 3

    gift_line = [line for line in lines if line.is_gift][0]
    discount = OrderLineDiscount.objects.get()
    assert discount.line == gift_line
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.ORDER_PROMOTION
    listing = ProductVariantChannelListing.objects.filter(
        channel=channel, variant=variant
    ).first()
    assert discount.value == listing.price_amount == Decimal(10)
    assert discount.amount_value == Decimal(10)
    assert discount.currency == channel.currency_code
    assert discount.name == f"{promotion.name}: {rule.name}"
    assert discount.reason == f"Promotion: {promotion_id}"

    assert gift_line.quantity == 1
    assert gift_line.variant == variant
    assert gift_line.total_price_gross_amount == Decimal(0)
    assert gift_line.total_price_net_amount == Decimal(0)
    assert gift_line.undiscounted_total_price_gross_amount == Decimal(0)
    assert gift_line.undiscounted_total_price_net_amount == Decimal(0)
    assert gift_line.unit_price_gross_amount == Decimal(0)
    assert gift_line.unit_price_net_amount == Decimal(0)
    assert gift_line.base_unit_price_amount == Decimal(0)
    assert gift_line.unit_discount_amount == Decimal(0)
    assert gift_line.unit_discount_type is None
    assert gift_line.unit_discount_value == Decimal(0)
    assert gift_line.product_name == product.name
    assert gift_line.product_sku == variant.sku


def test_multiple_rules_subtotal_and_catalogue_discount_applied(
    draft_order_and_promotions,
):
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


def test_multiple_rules_gift_and_catalogue_discount_applied(draft_order_and_promotions):
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


def test_multiple_rules_no_discount_applied(
    draft_order_and_promotions, product_variant_list
):
    # given
    order, rule_catalogue, rule_total, rule_gift = draft_order_and_promotions
    rule_total.order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100000}}}
    }
    rule_total.save(update_fields=["order_predicate"])
    rule_gift.order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 100000}}}
    }
    rule_gift.save(update_fields=["order_predicate"])

    line_2 = [line for line in order.lines.all() if line.quantity == 2][0]
    discounted_variant = line_2.variant
    listing = discounted_variant.channel_listings.get(channel=order.channel)
    listing.discounted_price_amount = listing.price_amount
    listing.variantlistingpromotionrule.all().delete()
    listing.save(update_fields=["discounted_price_amount"])
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


def test_update_catalogue_discount(
    order_with_lines_and_catalogue_promotion, catalogue_promotion_without_rules
):
    # given
    order = order_with_lines_and_catalogue_promotion
    promotion = catalogue_promotion_without_rules

    channel = order.channel
    line = order.lines.get(quantity=3)
    variant = line.variant
    assert OrderLineDiscount.objects.count() == 1
    discount_to_update = line.discounts.get()

    reward_value = Decimal(6)
    assert reward_value > promotion.rules.first().reward_value
    rule = promotion.rules.create(
        name="New catalogue rule fixed",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
    )
    rule.channels.add(channel)

    variant_channel_listing = variant.channel_listings.get(channel=channel)
    undiscounted_price = variant_channel_listing.price_amount
    variant_channel_listing.discounted_price_amount = undiscounted_price - reward_value
    variant_channel_listing.save(update_fields=["discounted_price_amount"])

    variant_rule_listing = variant_channel_listing.variantlistingpromotionrule.get()
    variant_rule_listing.discount_amount = reward_value
    variant_rule_listing.promotion_rule = rule
    variant_rule_listing.save(update_fields=["discount_amount", "promotion_rule"])

    lines_info = fetch_draft_order_lines_info(order)

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    assert OrderLineDiscount.objects.count() == 1
    discount = OrderLineDiscount.objects.get()
    assert discount_to_update.id == discount.id
    assert discount.line == line
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.PROMOTION
    assert discount.value_type == RewardValueType.FIXED
    assert discount.value == reward_value == Decimal(6)
    assert discount.amount_value == reward_value * line.quantity == Decimal(18)
    assert discount.currency == channel.currency_code
    assert discount.name == f"{promotion.name}: {rule.name}"

    line = [line_info.line for line_info in lines_info if line_info.line == line][0]
    assert line.base_unit_price_amount == Decimal(4)


def test_update_order_discount_subtotal(
    order_with_lines_and_order_promotion, order_promotion_without_rules
):
    # given
    order = order_with_lines_and_order_promotion
    channel = order.channel
    promotion = order_promotion_without_rules

    reward_value = Decimal(30)
    assert reward_value > promotion.rules.first().reward_value
    rule = promotion.rules.create(
        name="Fixed subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseTotalPrice": {"range": {"gte": 10}}}
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=reward_value,
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule.channels.add(order.channel)

    lines_info = fetch_draft_order_lines_info(order)

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    assert OrderDiscount.objects.count() == 1
    discount = order.discounts.get()
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value_type == RewardValueType.FIXED
    assert discount.value == reward_value == Decimal(30)
    assert discount.amount_value == reward_value == Decimal(30)
    assert discount.currency == channel.currency_code
    assert discount.name == f"{promotion.name}: {rule.name}"


def test_update_gift_discount_new_gift_available(
    order_with_lines_and_gift_promotion, product_variant_list, warehouse
):
    # given
    order = order_with_lines_and_gift_promotion
    variant = product_variant_list[0]
    Stock.objects.create(product_variant=variant, warehouse=warehouse, quantity=100)
    channel = order.channel
    current_discount = OrderLineDiscount.objects.get()
    rule = current_discount.promotion_rule

    gift_price = Decimal(50)
    listing = variant.channel_listings.get(channel=channel)
    listing.discounted_price_amount = gift_price
    listing.price_amount = gift_price
    listing.save(update_fields=["discounted_price_amount", "price_amount"])
    rule.gifts.add(variant)

    lines_info = fetch_draft_order_lines_info(order)

    # when
    create_or_update_discount_objects_from_promotion_for_order(order, lines_info)

    # then
    assert OrderLineDiscount.objects.count() == 1
    lines = order.lines.all()
    assert len(lines) == 3

    gift_line = [line for line in lines if line.is_gift][0]
    discount = OrderLineDiscount.objects.get()
    assert discount.line == gift_line
    assert discount.promotion_rule == rule
    assert discount.type == DiscountType.ORDER_PROMOTION
    assert discount.value == gift_price == Decimal(50)
    assert discount.amount_value == gift_price
    assert discount.currency == channel.currency_code

    assert gift_line.quantity == 1
    assert gift_line.variant == variant
