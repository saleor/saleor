from decimal import Decimal

import graphene
import pytest
from prices import TaxedMoney

from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....core.taxes import zero_money
from ....discount import RewardType, RewardValueType
from ....order import OrderStatus
from ....plugins.manager import get_plugins_manager
from ....product.models import VariantChannelListingPromotionRule
from ....warehouse.models import Stock


@pytest.fixture
def checkout_lines_info(checkout_with_items, categories, published_collections):
    lines = checkout_with_items.lines.all()
    category1, category2 = categories

    product1 = lines[0].variant.product
    product1.category = category1
    product1.collections.add(*published_collections[:2])
    product1.save()

    product2 = lines[1].variant.product
    product2.category = category2
    product2.collections.add(published_collections[0])
    product2.save()

    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    return lines_info


@pytest.fixture
def checkout_info(checkout_lines_info):
    manager = get_plugins_manager(allow_replica=False)
    checkout = checkout_lines_info[0].line.checkout
    checkout_info = fetch_checkout_info(checkout, checkout_lines_info, manager)
    return checkout_info


@pytest.fixture
def checkout_lines_with_multiple_quantity_info(
    checkout_with_items, categories, published_collections
):
    checkout_with_items.lines.update(quantity=5)
    lines = checkout_with_items.lines.all()
    category1, category2 = categories

    product1 = lines[0].variant.product
    product1.category = category1
    product1.collections.add(*published_collections[:2])
    product1.save()

    product2 = lines[1].variant.product
    product2.category = category2
    product2.collections.add(published_collections[0])
    product2.save()

    lines_info, _ = fetch_checkout_lines(checkout_with_items)
    return lines_info


@pytest.fixture
def draft_order_and_promotions(
    order_with_lines,
    order_promotion_without_rules,
    catalogue_promotion_without_rules,
    channel_USD,
):
    # given
    order = order_with_lines
    line_1 = order.lines.get(quantity=3)
    line_2 = order.lines.get(quantity=2)

    # prepare catalogue promotions
    catalogue_promotion = catalogue_promotion_without_rules
    variant_1 = line_1.variant
    variant_2 = line_2.variant
    rule_catalogue = catalogue_promotion.rules.create(
        name="Catalogue rule fixed",
        catalogue_predicate={
            "variantPredicate": {
                "ids": [graphene.Node.to_global_id("ProductVariant", variant_2.id)]
            }
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(3),
    )
    rule_catalogue.channels.add(channel_USD)

    listing = variant_2.channel_listings.first()
    listing.discounted_price_amount = Decimal(17)
    listing.save(update_fields=["discounted_price_amount"])

    currency = order.currency
    VariantChannelListingPromotionRule.objects.create(
        variant_channel_listing=listing,
        promotion_rule=rule_catalogue,
        discount_amount=Decimal(3),
        currency=currency,
    )

    # prepare order promotion - subtotal
    order_promotion = order_promotion_without_rules
    rule_total = order_promotion.rules.create(
        name="Fixed subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
        },
        reward_value_type=RewardValueType.FIXED,
        reward_value=Decimal(25),
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
    )
    rule_total.channels.add(channel_USD)

    # prepare order promotion - gift
    rule_gift = order_promotion.rules.create(
        name="Gift subtotal rule",
        order_predicate={
            "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": 10}}}
        },
        reward_type=RewardType.GIFT,
    )
    rule_gift.channels.add(channel_USD)
    rule_gift.gifts.set([variant_1, variant_2])
    Stock.objects.update(quantity=100)

    # reset prices
    order.total = TaxedMoney(net=zero_money(currency), gross=zero_money(currency))
    order.subtotal = TaxedMoney(net=zero_money(currency), gross=zero_money(currency))
    order.undiscounted_total = TaxedMoney(
        net=zero_money(currency), gross=zero_money(currency)
    )
    order.status = OrderStatus.DRAFT
    order.save()

    return order, rule_catalogue, rule_total, rule_gift
