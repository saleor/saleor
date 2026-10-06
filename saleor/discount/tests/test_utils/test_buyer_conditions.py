from decimal import Decimal

import pytest
from django.db import connection
from django.db.models import ProtectedError
from django.test.utils import CaptureQueriesContext

from ....attribute.models import AttributeValue
from ....product.scoped_prices import BuyerConditions
from ... import RewardValueType
from ...models import (
    PromotionRule,
    PromotionRuleCustomerAttributeValue,
    PromotionRuleCustomerType,
)
from ...utils.buyer_conditions import (
    count_promotion_rules_by_attribute_id,
    count_promotion_rules_by_attribute_value_id,
    count_promotion_rules_for_attribute_values,
    count_promotion_rules_for_customer_type,
    create_rule_buyer_conditions,
    get_rule_buyer_conditions,
    set_rule_buyer_conditions,
)


def _loyalty_values(loyalty_customer_attribute):
    gold = AttributeValue.objects.get(attribute=loyalty_customer_attribute, slug="gold")
    silver = AttributeValue.objects.get(
        attribute=loyalty_customer_attribute, slug="silver"
    )
    return gold, silver


def test_get_rule_buyer_conditions_groups_the_values_by_attribute(
    promotion_rule, customer_type, loyalty_customer_attribute
):
    # given
    gold, silver = _loyalty_values(loyalty_customer_attribute)
    PromotionRuleCustomerType.objects.create(
        rule=promotion_rule, customer_type=customer_type
    )
    PromotionRuleCustomerAttributeValue.objects.bulk_create(
        [
            PromotionRuleCustomerAttributeValue(rule=promotion_rule, value=gold),
            PromotionRuleCustomerAttributeValue(rule=promotion_rule, value=silver),
        ]
    )

    # when
    with CaptureQueriesContext(connection) as context:
        conditions = get_rule_buyer_conditions([promotion_rule.pk])

    # then
    assert len(context.captured_queries) == 2
    assert conditions == {
        promotion_rule.pk: BuyerConditions(
            customer_type_ids=frozenset({customer_type.pk}),
            value_ids_by_attribute_id={
                loyalty_customer_attribute.pk: frozenset({gold.pk, silver.pk})
            },
        )
    }


def test_get_rule_buyer_conditions_leaves_out_rules_without_conditions(
    promotion_rule,
):
    # when
    conditions = get_rule_buyer_conditions([promotion_rule.pk])

    # then
    assert conditions == {}


def test_get_rule_buyer_conditions_without_rules_runs_no_query():
    # when
    with CaptureQueriesContext(connection) as context:
        conditions = get_rule_buyer_conditions([])

    # then
    assert conditions == {}
    assert len(context.captured_queries) == 0


def test_create_rule_buyer_conditions_writes_every_rule_in_two_queries(
    catalogue_promotion, customer_type, loyalty_customer_attribute
):
    # given
    gold, silver = _loyalty_values(loyalty_customer_attribute)
    rules = PromotionRule.objects.bulk_create(
        [
            PromotionRule(
                promotion=catalogue_promotion,
                name=name,
                catalogue_predicate={},
                reward_value_type=RewardValueType.PERCENTAGE,
                reward_value=Decimal(5),
            )
            for name in ("first", "second")
        ]
    )
    first_rule, second_rule = rules

    # when
    with CaptureQueriesContext(connection) as context:
        create_rule_buyer_conditions(
            [
                (first_rule, {customer_type.pk}, {gold.pk, silver.pk}),
                (second_rule, set(), {gold.pk}),
            ]
        )

    # then
    assert len(context.captured_queries) == 2
    assert list(
        first_rule.customer_type_conditions.values_list("customer_type_id", flat=True)
    ) == [customer_type.pk]
    assert set(
        first_rule.customer_attribute_value_conditions.values_list(
            "value_id", flat=True
        )
    ) == {gold.pk, silver.pk}
    assert second_rule.customer_type_conditions.exists() is False
    assert list(
        second_rule.customer_attribute_value_conditions.values_list(
            "value_id", flat=True
        )
    ) == [gold.pk]


@pytest.mark.parametrize(
    ("_case", "customer_type_slugs", "attribute_value_slugs"),
    [
        ("replaces_both_dimensions", ["default"], ["silver"]),
        ("clears_both_dimensions", [], []),
        ("keeps_an_unset_dimension", None, ["silver"]),
    ],
)
def test_set_rule_buyer_conditions(
    _case,
    customer_type_slugs,
    attribute_value_slugs,
    promotion_rule,
    customer_type,
    default_customer_type,
    loyalty_customer_attribute,
):
    # given
    gold, _ = _loyalty_values(loyalty_customer_attribute)
    PromotionRuleCustomerType.objects.create(
        rule=promotion_rule, customer_type=customer_type
    )
    PromotionRuleCustomerAttributeValue.objects.create(rule=promotion_rule, value=gold)
    customer_types_by_slug = {"default": default_customer_type, "b2b": customer_type}
    kwargs = {}
    if customer_type_slugs is not None:
        kwargs["customer_type_ids"] = frozenset(
            customer_types_by_slug[slug].pk for slug in customer_type_slugs
        )
    if attribute_value_slugs is not None:
        kwargs["attribute_value_ids"] = frozenset(
            AttributeValue.objects.get(
                attribute=loyalty_customer_attribute, slug=slug
            ).pk
            for slug in attribute_value_slugs
        )

    # when
    set_rule_buyer_conditions(promotion_rule, **kwargs)

    # then
    expected_type_ids = (
        kwargs["customer_type_ids"]
        if customer_type_slugs is not None
        else {customer_type.pk}
    )
    assert (
        set(
            promotion_rule.customer_type_conditions.values_list(
                "customer_type_id", flat=True
            )
        )
        == expected_type_ids
    )
    assert (
        set(
            promotion_rule.customer_attribute_value_conditions.values_list(
                "value_id", flat=True
            )
        )
        == kwargs["attribute_value_ids"]
    )


def test_count_helpers_count_each_rule_once(
    promotion_rule,
    order_promotion_rule,
    customer_type,
    loyalty_customer_attribute,
    segment_customer_attribute,
):
    # given
    gold, silver = _loyalty_values(loyalty_customer_attribute)
    retail = AttributeValue.objects.get(attribute=segment_customer_attribute)
    PromotionRuleCustomerType.objects.create(
        rule=promotion_rule, customer_type=customer_type
    )
    PromotionRuleCustomerAttributeValue.objects.bulk_create(
        [
            PromotionRuleCustomerAttributeValue(rule=promotion_rule, value=gold),
            PromotionRuleCustomerAttributeValue(rule=promotion_rule, value=silver),
            PromotionRuleCustomerAttributeValue(rule=order_promotion_rule, value=gold),
        ]
    )

    # then
    assert count_promotion_rules_for_customer_type(customer_type.pk) == 1
    assert count_promotion_rules_for_attribute_values([gold.pk, silver.pk]) == 2
    assert count_promotion_rules_by_attribute_value_id(
        [gold.pk, silver.pk, retail.pk]
    ) == {gold.pk: 2, silver.pk: 1}
    assert count_promotion_rules_by_attribute_id(
        [loyalty_customer_attribute.pk, segment_customer_attribute.pk]
    ) == {loyalty_customer_attribute.pk: 2}


def test_deleting_a_referenced_customer_type_is_protected(
    promotion_rule_for_customer_type, customer_type
):
    # when / then
    with pytest.raises(ProtectedError):
        customer_type.delete()
    assert PromotionRuleCustomerType.objects.filter(
        rule=promotion_rule_for_customer_type
    ).exists()


def test_deleting_a_rule_removes_its_conditions(promotion_rule_for_customer_type):
    # given
    rule_id = promotion_rule_for_customer_type.pk

    # when
    promotion_rule_for_customer_type.delete()

    # then
    assert PromotionRuleCustomerType.objects.filter(rule_id=rule_id).exists() is False


def test_set_rule_buyer_conditions_locks_the_rule_before_writing(
    promotion_rule, customer_type
):
    # when
    with CaptureQueriesContext(connection) as context:
        set_rule_buyer_conditions(
            promotion_rule, customer_type_ids=frozenset({customer_type.pk})
        )

    # then
    queries = [query["sql"] for query in context.captured_queries]
    lock_queries = [
        query for query in queries if "FOR UPDATE" in query and "ORDER BY" in query
    ]
    assert len(lock_queries) == 1
    first_write = next(
        index for index, query in enumerate(queries) if query.startswith("INSERT")
    )
    assert queries.index(lock_queries[0]) < first_write
