from ....product.utils.product import get_channel_to_products_map_from_rules
from ...models import PromotionRule


def test_get_channel_to_products_map_from_rules_empty_rules_qs():
    # when
    results = get_channel_to_products_map_from_rules(rules=PromotionRule.objects.none())

    # then
    assert results == {}


def test_get_channel_to_products_when_single_rule_related(
    promotion, channel_USD, product
):
    # given
    rule = promotion.rules.first()
    rule.variants.set([product.variants.first()])
    rule.channels.set([channel_USD])

    # when
    result = get_channel_to_products_map_from_rules(
        rules=PromotionRule.objects.filter(id=rule.id)
    )

    # then
    assert isinstance(result, dict)
    assert dict(result) == {channel_USD.id: {product.id}}


def test_get_channel_to_products_when_multiple_rules_related(
    promotion_list, channel_USD, product_list
):
    # given
    first_product = product_list[0]
    second_product = product_list[1]

    first_promotion = promotion_list[0]
    second_promotion = promotion_list[1]
    first_rule = first_promotion.rules.first()
    first_rule.variants.set([first_product.variants.first()])
    first_rule.channels.set([channel_USD])
    second_rule = second_promotion.rules.first()
    second_rule.variants.set([second_product.variants.first()])
    second_rule.channels.set([channel_USD])

    # when
    results = get_channel_to_products_map_from_rules(
        rules=PromotionRule.objects.filter(id__in=[first_rule.id, second_rule.id])
    )

    # then
    assert isinstance(results, dict)
    assert dict(results) == {channel_USD.id: {first_product.id, second_product.id}}


def test_get_channel_to_products_when_multiple_channels_and_rules_related(
    promotion_list, channel_USD, channel_PLN, channel_JPY, product_list
):
    # given
    first_product = product_list[0]
    second_product = product_list[1]

    first_promotion = promotion_list[0]
    second_promotion = promotion_list[1]
    first_rule = first_promotion.rules.first()
    first_rule.variants.set([first_product.variants.first()])
    first_rule.channels.set([channel_USD, channel_PLN])
    second_rule = second_promotion.rules.first()
    second_rule.variants.set([second_product.variants.first()])
    second_rule.channels.set([channel_PLN, channel_JPY])

    # when
    results = get_channel_to_products_map_from_rules(
        rules=PromotionRule.objects.filter(id__in=[first_rule.id, second_rule.id])
    )

    # then
    assert isinstance(results, dict)
    assert results[channel_USD.id] == {
        first_product.id,
    }
    assert results[channel_PLN.id] == {first_product.id, second_product.id}
    assert results[channel_JPY.id] == {second_product.id}
