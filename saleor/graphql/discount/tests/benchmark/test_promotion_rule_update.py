from decimal import Decimal

import graphene
import pytest

from ....tests.utils import get_graphql_content
from ...enums import RewardValueTypeEnum
from ..mutations.test_promotion_rule_update import PROMOTION_RULE_UPDATE_MUTATION


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_promotion_rule_update(
    staff_api_client,
    description_json,
    permission_group_manage_discounts,
    channel_USD,
    channel_PLN,
    catalogue_promotion,
    product_list,
    collection,
    count_queries,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_discounts)

    promotion = catalogue_promotion
    rule = promotion.rules.first()
    rule_id = graphene.Node.to_global_id("PromotionRule", rule.id)

    add_channel_ids = [graphene.Node.to_global_id("Channel", channel_PLN.pk)]
    remove_channel_ids = [graphene.Node.to_global_id("Channel", channel_USD.pk)]
    catalogue_predicate = {
        "OR": [
            {
                "variantPredicate": {
                    "ids": [
                        graphene.Node.to_global_id(
                            "ProductVariant", product_list[1].variants.first().id
                        )
                    ]
                }
            },
            {
                "collectionPredicate": {
                    "ids": [graphene.Node.to_global_id("Collection", collection.id)]
                }
            },
        ]
    }
    collection.products.add(product_list[2])
    reward_value = Decimal("10")
    reward_value_type = RewardValueTypeEnum.FIXED.name

    variables = {
        "id": rule_id,
        "input": {
            "name": "New rule name",
            "description": description_json,
            "addChannels": add_channel_ids,
            "removeChannels": remove_channel_ids,
            "rewardValueType": reward_value_type,
            "rewardValue": reward_value,
            "cataloguePredicate": catalogue_predicate,
        },
    }

    # when
    content = get_graphql_content(
        staff_api_client.post_graphql(
            PROMOTION_RULE_UPDATE_MUTATION,
            variables,
        )
    )

    # then
    data = content["data"]["promotionRuleUpdate"]
    assert data["promotionRule"]
