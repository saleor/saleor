from decimal import Decimal
from unittest.mock import ANY

import graphene

from .....discount.error_codes import PromotionRuleCreateErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import RewardValueTypeEnum

PROMOTION_RULE_CREATE_MUTATION = """
    mutation promotionRuleCreate($input: PromotionRuleCreateInput!) {
        promotionRuleCreate(input: $input) {
            promotionRule {
                name
                description
                promotion {
                    id
                }
                channels {
                    id
                }
                rewardValueType
                rewardValue
                cataloguePredicate
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


def test_promotion_rule_create_by_staff_user(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [graphene.Node.to_global_id("ProductVariant", variant.id)]
                }
            },
            {
                "productPredicate": {
                    "ids": [graphene.Node.to_global_id("Product", product.id)]
                }
            },
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert {channel["id"] for channel in rule_data["channels"]} == set(channel_ids)
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1


def test_promotion_rule_create_by_app(
    app_api_client,
    permission_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_CREATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == name
    assert rule_data["description"] == description_json
    assert {channel["id"] for channel in rule_data["channels"]} == set(channel_ids)
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count + 1


def test_promotion_rule_create_by_customer(
    api_client,
    permission_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)
    assert_no_permission(response)


def test_promotion_rule_create_missing_catalogue_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    name = "test promotion rule"
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "cataloguePredicate"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_missing_reward_value(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    name = "test promotion rule"
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValueType": reward_value_type,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardValue"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_missing_reward_value_type(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    name = "test promotion rule"
    reward_value = Decimal("10")
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleCreateErrorCode.REQUIRED.name
    assert errors[0]["field"] == "rewardValueType"
    assert promotion.rules.count() == rules_count


def test_promotion_rule_create_multiple_errors(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    product,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)

    channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
    catalogue_predicate = {
        "productPredicate": {"ids": [graphene.Node.to_global_id("Product", product.id)]}
    }
    name = "test promotion rule"
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "input": {
            "name": name,
            "promotion": promotion_id,
            "description": description_json,
            "channels": channel_ids,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleCreate"]
    errors = data["errors"]

    assert len(errors) == 2
    expected_errors = [
        {
            "code": PromotionRuleCreateErrorCode.REQUIRED.name,
            "field": "rewardValue",
            "message": ANY,
        },
        {
            "code": PromotionRuleCreateErrorCode.REQUIRED.name,
            "field": "rewardValueType",
            "message": ANY,
        },
    ]
    for error in expected_errors:
        assert error in errors

    assert promotion.rules.count() == rules_count
