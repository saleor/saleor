from decimal import Decimal

import graphene
import pytest

from ....tests.utils import get_graphql_content
from ...enums import RewardTypeEnum, RewardValueTypeEnum

PROMOTION_RULE_CREATE_MUTATION = """
    mutation promotionRuleCreate($input: PromotionRuleCreateInput!) {
        promotionRuleCreate(input: $input) {
            promotionRule {
                id
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
def test_promotion_rule_create(
    staff_api_client,
    description_json,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    catalogue_promotion,
    variant,
    product,
    category,
    collection,
    count_queries,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_discounts)

    rule_channel_ids = [
        graphene.Node.to_global_id("Channel", channel.pk)
        for channel in [channel_USD, channel_PLN]
    ]
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

    promotion_id = graphene.Node.to_global_id("Promotion", catalogue_promotion.id)
    variables = {
        "input": {
            "promotion": promotion_id,
            "name": "Rule 1",
            "description": description_json,
            "channels": rule_channel_ids,
            "rewardValueType": RewardValueTypeEnum.PERCENTAGE.name,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        }
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            PROMOTION_RULE_CREATE_MUTATION,
            variables,
        )
    )

    # then
    data = content["data"]["promotionRuleCreate"]
    assert data["promotionRule"]


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_promotion_rule_create_gift(
    staff_api_client,
    permission_group_manage_discounts,
    channel_USD,
    count_queries,
    product_variant_list,
    gift_promotion_rule,
    django_assert_num_queries,
):
    # given
    permission_group_manage_discounts.user_set.add(staff_api_client.user)
    order_predicate = {
        "discountedObjectPredicate": {"baseSubtotalPrice": {"range": {"gte": "100"}}}
    }
    channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    gift_ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list
    ]

    variables = {
        "input": {
            "promotion": graphene.Node.to_global_id(
                "Promotion", gift_promotion_rule.promotion_id
            ),
            "name": "test gift promotion rule",
            "channels": channel_ids,
            "rewardType": RewardTypeEnum.GIFT.name,
            "orderPredicate": order_predicate,
            "gifts": gift_ids,
        }
    }

    # when
    with django_assert_num_queries(16):
        content = get_graphql_content(
            staff_api_client.post_graphql(PROMOTION_RULE_CREATE_MUTATION, variables)
        )

    # then
    data = content["data"]["promotionRuleCreate"]
    assert data["promotionRule"]
    assert not data["errors"]
