from datetime import timedelta
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone

from ....tests.utils import get_graphql_content
from ...enums import PromotionTypeEnum, RewardTypeEnum, RewardValueTypeEnum

PROMOTION_CREATE_MUTATION = """
    mutation promotionCreate($input: PromotionCreateInput!) {
        promotionCreate(input: $input) {
            promotion {
                id
                rules {
                    id
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


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_promotion_create(
    staff_api_client,
    description_json,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    variant,
    product,
    category,
    collection,
    count_queries,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_discounts)
    start_date = timezone.now() - timedelta(days=30)
    end_date = timezone.now() + timedelta(days=30)

    rule_1_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    rule_2_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]

    reward_value = Decimal("10")

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
            "name": "Promotion",
            "description": description_json,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "type": PromotionTypeEnum.CATALOGUE.name,
            "rules": [
                {
                    "name": "Rule 1",
                    "description": description_json,
                    "channels": rule_1_channel_ids,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": "Rule 2",
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
                {
                    "name": "Rule 3",
                    "description": description_json,
                    "channels": rule_2_channel_ids,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": reward_value,
                    "cataloguePredicate": catalogue_predicate,
                },
            ],
        }
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            PROMOTION_CREATE_MUTATION,
            variables,
        )
    )

    # then
    data = content["data"]["promotionCreate"]
    assert data["promotion"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_promotion_create_order_promotion(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    product_variant_list,
    count_queries,
    django_assert_num_queries,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    order_predicate_0 = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "10"}}}
    }
    order_predicate_1 = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "50"}}}
    }
    order_predicate_2 = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    gift_ids_1 = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list[:2]
    ]
    gift_ids_2 = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list[2:]
    ]

    variables = {
        "input": {
            "name": "test gift promotion",
            "type": PromotionTypeEnum.ORDER.name,
            "rules": [
                {
                    "name": "test order promotion rule 1",
                    "channels": channel_ids,
                    "rewardType": RewardTypeEnum.SUBTOTAL_DISCOUNT.name,
                    "rewardValueType": RewardValueTypeEnum.FIXED.name,
                    "rewardValue": Decimal("1"),
                    "orderPredicate": order_predicate_0,
                },
                {
                    "name": "test order promotion rule 2",
                    "channels": channel_ids,
                    "rewardType": RewardTypeEnum.SUBTOTAL_DISCOUNT.name,
                    "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
                    "rewardValue": Decimal("10"),
                    "orderPredicate": order_predicate_0,
                },
                {
                    "name": "test gift promotion rule 1",
                    "channels": channel_ids,
                    "rewardType": RewardTypeEnum.GIFT.name,
                    "orderPredicate": order_predicate_1,
                    "gifts": gift_ids_1,
                },
                {
                    "name": "test gift promotion rule 2",
                    "channels": channel_ids,
                    "rewardType": RewardTypeEnum.GIFT.name,
                    "orderPredicate": order_predicate_2,
                    "gifts": gift_ids_2,
                },
            ],
        }
    }

    # when
    with django_assert_num_queries(36):
        response = staff_api_client.post_graphql(PROMOTION_CREATE_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["promotionCreate"]
    assert not data["errors"]
