from datetime import timedelta
from decimal import Decimal

import graphene
import pytest
from django.utils import timezone

from ....tests.utils import get_graphql_content
from ...enums import RewardValueTypeEnum
from ..mutations.test_promotion_create import PROMOTION_CREATE_MUTATION


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
