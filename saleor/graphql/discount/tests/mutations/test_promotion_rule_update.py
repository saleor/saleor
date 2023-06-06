from decimal import Decimal
from unittest.mock import ANY

import graphene

from .....discount.error_codes import PromotionRuleUpdateErrorCode
from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import RewardValueTypeEnum

PROMOTION_RULE_UPDATE_MUTATION = """
    mutation promotionRuleUpdate($id: ID!, $input: PromotionRuleUpdateInput!) {
        promotionRuleUpdate(id: $id, input: $input) {
            promotionRule {
                name
                description
                promotion {
                    id
                }
                channels {
                    slug
                }
                rewardValueType
                rewardValue
                cataloguePredicate
            }
            errors {
                field
                code
                message
                channels
            }
        }
    }
"""


def test_promotion_rule_update_by_staff_user(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
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
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == rule.name
    assert rule_data["description"] == rule.description
    assert len(rule_data["channels"]) == 1
    assert rule_data["channels"][0]["slug"] == channel_PLN.slug
    assert rule_data["cataloguePredicate"] == catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count


def test_promotion_rule_update_by_app(
    app_api_client,
    permission_manage_discounts,
    channel_USD,
    channel_PLN,
    promotion,
):
    # given
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name
    promotion_id = graphene.Node.to_global_id("Promotion", promotion.id)
    rules_count = promotion.rules.count()

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
        },
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_RULE_UPDATE_MUTATION,
        variables,
        permissions=(permission_manage_discounts,),
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    rule_data = data["promotionRule"]

    assert not data["errors"]
    assert rule_data["name"] == rule.name
    assert rule_data["description"] == rule.description
    assert len(rule_data["channels"]) == 1
    assert rule_data["channels"][0]["slug"] == channel_PLN.slug
    assert rule_data["cataloguePredicate"] == rule.catalogue_predicate
    assert rule_data["rewardValueType"] == reward_value_type
    assert rule_data["rewardValue"] == reward_value
    assert rule_data["promotion"]["id"] == promotion_id
    assert promotion.rules.count() == rules_count


def test_promotion_rule_update_by_customer(
    api_client,
    channel_USD,
    channel_PLN,
    promotion,
):
    # given
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
        },
    }

    # when
    response = api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    assert_no_permission(response)


def test_promotion_rule_update_duplicates_channels_in_add_and_remove_field(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_PLN, channel_USD]
    ]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
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
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name

    variables = {
        "id": rule_id,
        "input": {
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 2
    expected_errors = [
        {
            "code": PromotionRuleUpdateErrorCode.DUPLICATED_INPUT_ITEM.name,
            "field": "addChannels",
            "message": ANY,
            "channels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
        },
        {
            "code": PromotionRuleUpdateErrorCode.DUPLICATED_INPUT_ITEM.name,
            "field": "removeChannels",
            "message": ANY,
            "channels": [graphene.Node.to_global_id("Channel", channel_PLN.pk)],
        },
    ]
    for error in expected_errors:
        assert error in errors


def test_promotion_rule_update_invalid_catalogue_predicate(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    collection,
    category,
    promotion,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    catalogue_predicate = {
        "OR": [
            {
                "categoryPredicate": {
                    "ids": [graphene.Node.to_global_id("Category", category.id)]
                }
            },
        ],
        "AND": [
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ],
    }
    reward_value = Decimal("10")

    variables = {
        "id": rule_id,
        "input": {
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        },
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_RULE_UPDATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionRuleUpdate"]
    errors = data["errors"]

    assert not data["promotionRule"]
    assert len(errors) == 1
    assert errors[0]["code"] == PromotionRuleUpdateErrorCode.INVALID.name
    assert errors[0]["field"] == "cataloguePredicate"
