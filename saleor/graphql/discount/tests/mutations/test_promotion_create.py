from datetime import timedelta
from decimal import Decimal

import graphene
from django.utils import timezone
from freezegun import freeze_time

from ....tests.utils import assert_no_permission, get_graphql_content
from ...enums import RewardValueTypeEnum

PROMOTION_CREATE_MUTATION = """
    mutation promotionCreate($input: PromotionCreateInput!) {
        promotionCreate(input: $input) {
            promotion {
                id
                name
                description
                startDate
                endDate
                createdAt
                updatedAt
                rules {
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
            }
            errors {
                field
                code
                message
            }
        }
    }
"""


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_by_staff_user(
    staff_api_client,
    permission_group_manage_discounts,
    description_json,
    channel_USD,
    channel_PLN,
    variant,
    product,
    collection,
    category,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    promotion_name = "test promotion"
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
    rule_1_name = "test promotion rule 1"
    rule_2_name = "test promotion rule 2"
    reward_value = Decimal("10")
    reward_value_type_1 = RewardValueTypeEnum.FIXED.name
    reward_value_type_2 = RewardValueTypeEnum.PERCENTAGE.name

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "rules": [
                {
                    "name": rule_1_name,
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": reward_value_type_1,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": rule_2_name,
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": reward_value_type_2,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
            ],
        }
    }

    # when
    response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == promotion_name
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()

    assert len(promotion_data["rules"]) == 2
    for rule_data in variables["input"]["rules"]:
        rule_data["promotion"] = {"id": promotion_data["id"]}
        rule_data["channels"] = [
            {"id": channel_id} for channel_id in rule_data["channels"]
        ]
        assert rule_data in promotion_data["rules"]


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_by_app(
    app_api_client,
    permission_manage_discounts,
    description_json,
    channel_USD,
    variant,
    product,
    collection,
    category,
):
    # given
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    promotion_name = "test promotion"
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

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "rules": [
                {
                    "name": "test promotion rule",
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("10"),
                    "cataloguePredicate": catalogue_predicate,
                }
            ],
        }
    }

    # when
    response = app_api_client.post_graphql(
        PROMOTION_CREATE_MUTATION, variables, permissions=(permission_manage_discounts,)
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    promotion_data = data["promotion"]

    assert not data["errors"]
    assert promotion_data["name"] == promotion_name
    assert promotion_data["startDate"] == start_date.isoformat()
    assert promotion_data["endDate"] == end_date.isoformat()


@freeze_time("2020-03-18 12:00:00")
def test_promotion_create_by_customer(
    api_client, description_json, channel_USD, variant, product, collection, category
):
    # given
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    promotion_name = "test promotion"
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

    variables = {
        "input": {
            "name": promotion_name,
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "rules": [
                {
                    "name": "test promotion rule",
                    "description": description_json,
                    "channels": channel_ids,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("10"),
                    "cataloguePredicate": catalogue_predicate,
                }
            ],
        }
    }

    # when
    response = api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    assert_no_permission(response)
