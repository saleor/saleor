from decimal import Decimal

import pytest
from prices import Money, TaxedMoney

from ....discount import RewardValueType
from ....discount.models import OrderDiscount, OrderLineDiscount, PromotionRule
from ....product.models import Product
from ....product.utils.variant_prices import update_discounted_prices_for_promotion
from ....product.utils.variants import fetch_variants_for_promotion_rules
from ....tax import TaxCalculationStrategy
from ....warehouse.models import Stock
from ... import OrderStatus
from ...calculations import fetch_order_prices_if_expired
from ...models import OrderLine


@pytest.fixture
def order_with_lines(order_with_lines):
    order_with_lines.status = OrderStatus.UNCONFIRMED
    return order_with_lines


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_fetch_order_prices_catalogue_discount(
    order_with_lines_and_catalogue_promotion,
    plugins_manager,
    django_assert_num_queries,
    count_queries,
):
    # given
    OrderLineDiscount.objects.all().delete()
    order = order_with_lines_and_catalogue_promotion
    channel = order.channel

    tc = channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

    # when
    with django_assert_num_queries(44):
        fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderLineDiscount.objects.count() == 1
    assert not OrderDiscount.objects.exists()


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_fetch_order_prices_multiple_catalogue_discounts(
    order_with_lines,
    catalogue_promotion_without_rules,
    plugins_manager,
    product_variant_list,
    django_assert_num_queries,
    count_queries,
):
    # given
    Stock.objects.update(quantity=100)
    order = order_with_lines
    channel = order.channel

    variants = product_variant_list
    variants.extend(line.variant for line in order.lines.all())
    variant_global_ids = [variant.get_global_id() for variant in variants]

    # create many rules
    promotion = catalogue_promotion_without_rules
    rules = []
    catalogue_predicate = {"variantPredicate": {"ids": variant_global_ids}}
    for idx in range(5):
        reward_value = 2 + idx
        rules.append(
            PromotionRule(
                name=f"Catalogue rule fixed {reward_value}",
                promotion=promotion,
                catalogue_predicate=catalogue_predicate,
                reward_value_type=RewardValueType.FIXED,
                reward_value=Decimal(reward_value),
            )
        )
    for idx in range(5):
        reward_value = idx * 10 + 25
        rules.append(
            PromotionRule(
                name=f"Catalogue rule percentage {reward_value}",
                promotion=promotion,
                catalogue_predicate=catalogue_predicate,
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal(reward_value),
            )
        )
    rules = PromotionRule.objects.bulk_create(rules)
    for rule in rules:
        rule.channels.add(channel)

    fetch_variants_for_promotion_rules(PromotionRule.objects.all())

    # update prices
    update_discounted_prices_for_promotion(Product.objects.all())

    # create lines
    new_order_lines = []
    for idx, variant in enumerate(product_variant_list):
        base_price = variant.channel_listings.first().discounted_price
        currency = base_price.currency
        gross = Money(amount=base_price.amount * Decimal(1.23), currency=currency)
        quantity = 4 + idx
        unit_price = TaxedMoney(net=base_price, gross=gross)
        new_order_lines.append(
            OrderLine(
                order=order,
                product_name=str(variant.product),
                variant_name=str(variant),
                product_sku=variant.sku,
                product_variant_id=variant.get_global_id(),
                is_shipping_required=variant.is_shipping_required(),
                is_gift_card=variant.is_gift_card(),
                quantity=quantity,
                variant=variant,
                unit_price=unit_price,
                total_price=unit_price * quantity,
                tax_rate=Decimal("0.23"),
            )
        )
    OrderLine.objects.bulk_create(new_order_lines)

    tc = channel.tax_configuration
    tc.country_exceptions.all().delete()
    tc.prices_entered_with_tax = False
    tc.tax_calculation_strategy = TaxCalculationStrategy.FLAT_RATES
    tc.save()

    # when
    with django_assert_num_queries(44):
        fetch_order_prices_if_expired(order, plugins_manager, None, True)

    # then
    assert OrderLineDiscount.objects.count() == 7
    assert not OrderDiscount.objects.exists()
