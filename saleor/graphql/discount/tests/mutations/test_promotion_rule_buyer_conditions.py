from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest

from .....attribute.models import AttributeValue
from .....discount import PromotionType, RewardType, RewardValueType
from .....discount.error_codes import (
    PromotionCreateErrorCode,
    PromotionRuleCreateErrorCode,
    PromotionRuleUpdateErrorCode,
)
from .....discount.models import (
    Promotion,
    PromotionRule,
    PromotionRuleCustomerAttributeValue,
    PromotionRuleCustomerType,
)
from .....product.models import ProductChannelListing
from ....tests.utils import get_graphql_content
from ...enums import PromotionTypeEnum, RewardTypeEnum, RewardValueTypeEnum

PROMOTION_RULE_CREATE_MUTATION = """
    mutation promotionRuleCreate($input: PromotionRuleCreateInput!) {
        promotionRuleCreate(input: $input) {
            promotionRule {
                id
                orderPredicate
                customerTypes {
                    id
                }
                customerAttributeValues {
                    id
                }
            }
            errors {
                field
                code
                message
                customerAttributeValues
            }
        }
    }
"""

PROMOTION_RULE_UPDATE_MUTATION = """
    mutation promotionRuleUpdate($id: ID!, $input: PromotionRuleUpdateInput!) {
        promotionRuleUpdate(id: $id, input: $input) {
            promotionRule {
                id
                customerTypes {
                    id
                }
                customerAttributeValues {
                    id
                }
            }
            errors {
                field
                code
                message
                customerAttributeValues
            }
        }
    }
"""

PROMOTION_CREATE_MUTATION = """
    mutation promotionCreate($input: PromotionCreateInput!) {
        promotionCreate(input: $input) {
            promotion {
                id
                rules {
                    id
                    customerTypes {
                        id
                    }
                    customerAttributeValues {
                        id
                    }
                }
            }
            errors {
                field
                code
                message
                index
                customerAttributeValues
            }
        }
    }
"""


def _customer_type_id(customer_type):
    return graphene.Node.to_global_id("CustomerType", customer_type.pk)


def _value_id(value):
    return graphene.Node.to_global_id("AttributeValue", value.pk)


def _gold_value(loyalty_customer_attribute):
    return AttributeValue.objects.get(attribute=loyalty_customer_attribute, slug="gold")


def _catalogue_rule_input(product, channel):
    return {
        "name": "Buyer rule",
        "channels": [graphene.Node.to_global_id("Channel", channel.pk)],
        "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
        "rewardValue": Decimal(10),
        "cataloguePredicate": {
            "productPredicate": {
                "ids": [graphene.Node.to_global_id("Product", product.pk)]
            }
        },
    }


@patch("saleor.plugins.manager.PluginsManager.promotion_rule_created")
def test_rule_create_stores_the_buyer_conditions(
    promotion_rule_created_mock,
    staff_api_client,
    permission_group_manage_discounts,
    catalogue_promotion,
    product,
    channel_USD,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    gold_value = _gold_value(loyalty_customer_attribute)
    variables = {
        "input": {
            "promotion": graphene.Node.to_global_id(
                "Promotion", catalogue_promotion.pk
            ),
            **_catalogue_rule_input(product, channel_USD),
            "customerTypes": [_customer_type_id(customer_type)],
            "customerAttributeValues": [_value_id(gold_value)],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionRuleCreate"]
    assert data["errors"] == []
    rule_data = data["promotionRule"]
    assert rule_data["customerTypes"] == [{"id": _customer_type_id(customer_type)}]
    assert rule_data["customerAttributeValues"] == [{"id": _value_id(gold_value)}]
    _, rule_pk = graphene.Node.from_global_id(rule_data["id"])
    rule = PromotionRule.objects.get(pk=rule_pk)
    assert list(
        rule.customer_type_conditions.values_list("customer_type_id", flat=True)
    ) == [customer_type.pk]
    assert list(
        rule.customer_attribute_value_conditions.values_list("value_id", flat=True)
    ) == [gold_value.pk]
    promotion_rule_created_mock.assert_called_once_with(rule)


def test_rule_create_on_an_order_promotion_accepts_buyer_conditions_alone(
    staff_api_client,
    permission_group_manage_discounts,
    order_promotion_without_rules,
    channel_USD,
    customer_type,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    variables = {
        "input": {
            "promotion": graphene.Node.to_global_id(
                "Promotion", order_promotion_without_rules.pk
            ),
            "name": "Buyer rule",
            "channels": [graphene.Node.to_global_id("Channel", channel_USD.pk)],
            "rewardType": RewardTypeEnum.SUBTOTAL_DISCOUNT.name,
            "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
            "rewardValue": Decimal(5),
            "customerTypes": [_customer_type_id(customer_type)],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionRuleCreate"]
    assert data["errors"] == []
    assert data["promotionRule"]["orderPredicate"] == {}
    rule = order_promotion_without_rules.rules.get()
    assert rule.order_predicate == {}
    assert rule.reward_type == RewardType.SUBTOTAL_DISCOUNT
    assert list(
        rule.customer_type_conditions.values_list("customer_type_id", flat=True)
    ) == [customer_type.pk]


def test_rule_create_on_an_order_promotion_with_buyer_conditions_needs_a_reward_type(
    staff_api_client,
    permission_group_manage_discounts,
    order_promotion_without_rules,
    channel_USD,
    customer_type,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    variables = {
        "input": {
            "promotion": graphene.Node.to_global_id(
                "Promotion", order_promotion_without_rules.pk
            ),
            "name": "Buyer rule",
            "channels": [graphene.Node.to_global_id("Channel", channel_USD.pk)],
            "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
            "rewardValue": Decimal(5),
            "customerTypes": [_customer_type_id(customer_type)],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionRuleCreate"]
    assert data["promotionRule"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "rewardType"
    assert error["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert error["message"] == (
        "The rewardType is required when customerTypes or customerAttributeValues "
        "are provided for an order promotion."
    )
    assert order_promotion_without_rules.rules.exists() is False


@pytest.mark.parametrize(
    ("_case", "field", "build_ids", "expected_code", "expected_message"),
    [
        (
            "unknown_customer_type",
            "customerTypes",
            lambda customer_type, value: [
                graphene.Node.to_global_id("CustomerType", -1)
            ],
            PromotionRuleCreateErrorCode.GRAPHQL_ERROR.name,
            "Could not resolve to a node with the global id list of "
            f"'['{graphene.Node.to_global_id('CustomerType', -1)}']'.",
        ),
        (
            "value_of_a_product_attribute",
            "customerAttributeValues",
            lambda customer_type, value: [_value_id(value)],
            PromotionRuleCreateErrorCode.INVALID.name,
            "Only values of customer attributes with a fixed set of choices can "
            "scope a promotion rule.",
        ),
    ],
)
def test_rule_create_rejects_invalid_buyer_conditions(
    _case,
    field,
    build_ids,
    expected_code,
    expected_message,
    staff_api_client,
    permission_group_manage_discounts,
    catalogue_promotion,
    product,
    channel_USD,
    customer_type,
    color_attribute,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    color_value = color_attribute.values.first()
    ids = build_ids(customer_type, color_value)
    variables = {
        "input": {
            "promotion": graphene.Node.to_global_id(
                "Promotion", catalogue_promotion.pk
            ),
            **_catalogue_rule_input(product, channel_USD),
            field: ids,
        }
    }
    rules_count = catalogue_promotion.rules.count()

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionRuleCreate"]
    assert data["promotionRule"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == field
    assert error["code"] == expected_code
    assert error["message"] == expected_message
    if _case == "value_of_a_product_attribute":
        assert error["customerAttributeValues"] == ids
    assert catalogue_promotion.rules.count() == rules_count


@pytest.mark.parametrize(
    ("_case", "customer_types_input", "expected_type_slugs"),
    [
        ("given_list_replaces", ["default"], ["default"]),
        ("null_clears", None, []),
        ("empty_list_clears", [], []),
    ],
)
@patch("saleor.plugins.manager.PluginsManager.promotion_rule_updated")
def test_rule_update_replaces_a_dimension_and_keeps_the_other(
    promotion_rule_updated_mock,
    _case,
    customer_types_input,
    expected_type_slugs,
    staff_api_client,
    permission_group_manage_discounts,
    promotion_rule_for_customer_type,
    customer_type,
    default_customer_type,
    loyalty_customer_attribute,
    product,
    channel_USD,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion_rule_for_customer_type
    gold_value = _gold_value(loyalty_customer_attribute)
    PromotionRuleCustomerAttributeValue.objects.create(rule=rule, value=gold_value)
    types_by_slug = {"default": default_customer_type, "b2b": customer_type}
    product_listing = ProductChannelListing.objects.get(
        product=product, channel=channel_USD
    )
    product_listing.discounted_price_dirty = False
    product_listing.save(update_fields=["discounted_price_dirty"])
    variables = {
        "id": graphene.Node.to_global_id("PromotionRule", rule.pk),
        "input": {
            "customerTypes": (
                [
                    _customer_type_id(types_by_slug[slug])
                    for slug in customer_types_input
                ]
                if customer_types_input is not None
                else None
            )
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionRuleUpdate"]
    assert data["errors"] == []
    expected_type_ids = [
        _customer_type_id(types_by_slug[slug]) for slug in expected_type_slugs
    ]
    assert data["promotionRule"]["customerTypes"] == [
        {"id": type_id} for type_id in expected_type_ids
    ]
    assert data["promotionRule"]["customerAttributeValues"] == [
        {"id": _value_id(gold_value)}
    ]
    assert [
        _customer_type_id(condition.customer_type)
        for condition in rule.customer_type_conditions.all()
    ] == expected_type_ids
    assert list(
        rule.customer_attribute_value_conditions.values_list("value_id", flat=True)
    ) == [gold_value.pk]
    product_listing.refresh_from_db(fields=["discounted_price_dirty"])
    assert product_listing.discounted_price_dirty is True
    promotion_rule_updated_mock.assert_called_once_with(rule)


def test_rule_update_rejects_an_ineligible_value_and_keeps_the_conditions(
    staff_api_client,
    permission_group_manage_discounts,
    promotion_rule_for_customer_type,
    customer_type,
    color_attribute,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion_rule_for_customer_type
    color_value_id = _value_id(color_attribute.values.first())
    variables = {
        "id": graphene.Node.to_global_id("PromotionRule", rule.pk),
        "input": {"customerAttributeValues": [color_value_id]},
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionRuleUpdate"]
    assert data["promotionRule"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "customerAttributeValues"
    assert error["code"] == PromotionRuleUpdateErrorCode.INVALID.name
    assert error["message"] == (
        "Only values of customer attributes with a fixed set of choices can scope "
        "a promotion rule."
    )
    assert error["customerAttributeValues"] == [color_value_id]
    assert rule.customer_attribute_value_conditions.exists() is False
    assert list(
        rule.customer_type_conditions.values_list("customer_type_id", flat=True)
    ) == [customer_type.pk]


def test_promotion_create_stores_the_buyer_conditions_of_every_rule(
    staff_api_client,
    permission_group_manage_discounts,
    product,
    channel_USD,
    customer_type,
    loyalty_customer_attribute,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    gold_value = _gold_value(loyalty_customer_attribute)
    variables = {
        "input": {
            "name": "Buyer promotion",
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    **_catalogue_rule_input(product, channel_USD),
                    "name": "Type rule",
                    "customerTypes": [_customer_type_id(customer_type)],
                },
                {
                    **_catalogue_rule_input(product, channel_USD),
                    "name": "Value rule",
                    "customerAttributeValues": [_value_id(gold_value)],
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionCreate"]
    assert data["errors"] == []
    promotion = Promotion.objects.get(name="Buyer promotion")
    assert promotion.type == PromotionType.CATALOGUE
    type_rule = promotion.rules.get(name="Type rule")
    value_rule = promotion.rules.get(name="Value rule")
    assert list(
        PromotionRuleCustomerType.objects.filter(rule=type_rule).values_list(
            "customer_type_id", flat=True
        )
    ) == [customer_type.pk]
    assert type_rule.customer_attribute_value_conditions.exists() is False
    assert value_rule.customer_type_conditions.exists() is False
    assert list(
        value_rule.customer_attribute_value_conditions.values_list(
            "value_id", flat=True
        )
    ) == [gold_value.pk]
    rules_data = {rule["id"]: rule for rule in data["promotion"]["rules"]}
    type_rule_data = rules_data[
        graphene.Node.to_global_id("PromotionRule", type_rule.pk)
    ]
    assert type_rule_data["customerTypes"] == [{"id": _customer_type_id(customer_type)}]
    assert type_rule_data["customerAttributeValues"] == []


def test_promotion_create_rejects_more_than_100_customer_types(
    staff_api_client,
    permission_group_manage_discounts,
    product,
    channel_USD,
    customer_type,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    variables = {
        "input": {
            "name": "Buyer promotion",
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    **_catalogue_rule_input(product, channel_USD),
                    "customerTypes": [_customer_type_id(customer_type)] * 101,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionCreate"]
    assert data["promotion"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "customerTypes"
    assert error["code"] == PromotionCreateErrorCode.INVALID.name
    assert error["index"] == 0
    assert error["message"] == "Provide at most 100 items."
    assert Promotion.objects.filter(name="Buyer promotion").exists() is False


def test_promotion_create_reports_an_invalid_buyer_condition_with_its_index(
    staff_api_client,
    permission_group_manage_discounts,
    product,
    channel_USD,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    unknown_id = graphene.Node.to_global_id("CustomerType", -1)
    variables = {
        "input": {
            "name": "Buyer promotion",
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                _catalogue_rule_input(product, channel_USD),
                {
                    **_catalogue_rule_input(product, channel_USD),
                    "customerTypes": [unknown_id],
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionCreate"]
    assert data["promotion"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "customerTypes"
    assert error["code"] == PromotionCreateErrorCode.GRAPHQL_ERROR.name
    assert error["index"] == 1
    assert error["message"] == (
        f"Could not resolve to a node with the global id list of '['{unknown_id}']'."
    )
    assert Promotion.objects.filter(name="Buyer promotion").exists() is False


def test_order_rules_limit_counts_rules_with_buyer_conditions_only(
    staff_api_client,
    permission_group_manage_discounts,
    order_promotion_without_rules,
    channel_USD,
    customer_type,
    settings,
):
    # given
    settings.ORDER_RULES_LIMIT = 1
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    existing_rule = PromotionRule.objects.create(
        name="Existing buyer rule",
        promotion=order_promotion_without_rules,
        order_predicate={},
        reward_type=RewardType.SUBTOTAL_DISCOUNT,
        reward_value_type=RewardValueType.PERCENTAGE,
        reward_value=Decimal(5),
    )
    PromotionRuleCustomerType.objects.create(
        rule=existing_rule, customer_type=customer_type
    )
    variables = {
        "input": {
            "promotion": graphene.Node.to_global_id(
                "Promotion", order_promotion_without_rules.pk
            ),
            "name": "Second rule",
            "channels": [graphene.Node.to_global_id("Channel", channel_USD.pk)],
            "rewardType": RewardTypeEnum.SUBTOTAL_DISCOUNT.name,
            "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
            "rewardValue": Decimal(5),
            "orderPredicate": {
                "discountedObjectPredicate": {
                    "baseSubtotalPrice": {"range": {"gte": "10"}}
                }
            },
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionRuleCreate"]
    assert data["promotionRule"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "orderPredicate"
    assert error["code"] == PromotionRuleCreateErrorCode.RULES_NUMBER_LIMIT.name
    assert (
        error["message"] == "Number of rules with orderPredicate has reached the limit."
    )
    assert order_promotion_without_rules.rules.count() == 1


def test_rule_update_cannot_clear_the_only_condition_of_an_order_rule(
    staff_api_client,
    permission_group_manage_discounts,
    order_promotion_rule_for_customer_type,
    customer_type,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = order_promotion_rule_for_customer_type
    rule.order_predicate = {}
    rule.save(update_fields=["order_predicate"])
    variables = {
        "id": graphene.Node.to_global_id("PromotionRule", rule.pk),
        "input": {"customerTypes": []},
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    data = get_graphql_content(response)["data"]["promotionRuleUpdate"]
    assert data["promotionRule"] is None
    assert len(data["errors"]) == 1
    error = data["errors"][0]
    assert error["field"] == "orderPredicate"
    assert error["code"] == PromotionRuleUpdateErrorCode.REQUIRED.name
    assert error["message"] == (
        "For `order` predicate type, `orderPredicate` must be provided."
    )
    assert list(
        rule.customer_type_conditions.values_list("customer_type_id", flat=True)
    ) == [customer_type.pk]
