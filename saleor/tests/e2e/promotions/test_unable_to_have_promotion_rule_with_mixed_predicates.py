import pytest

from ..product.utils import (
    create_collection,
    create_collection_channel_listing,
)
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import create_promotion, raw_create_promotion, raw_update_promotion_rule


def prepare_collection(
    e2e_staff_api_client,
):
    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]

    collection_data = create_collection(e2e_staff_api_client)
    collection_id = collection_data["id"]

    create_collection_channel_listing(e2e_staff_api_client, collection_id, channel_id)

    return channel_id, collection_id


@pytest.mark.e2e
def test_unable_to_have_promotion_rule_with_mixed_predicates_CORE_2125(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        channel_id,
        collection_id,
    ) = prepare_collection(
        e2e_staff_api_client,
    )

    # Step 1- Create promotion with rule with mixed predicates
    invalid_promotion_name = "Promotion with mixed predicates"
    invalid_promotion_type = "CATALOGUE"
    invalid_promotion_reward_value = "20"
    invalid_promotion_rules = [
        {
            "name": "rule for promotion with mixed predicates",
            "channels": [channel_id],
            "cataloguePredicate": {"collectionPredicate": {"ids": [collection_id]}},
            "orderPredicate": {
                "discountedObjectPredicate": {"baseTotalPrice": {"eq": "10"}}
            },
            "rewardType": "SUBTOTAL_DISCOUNT",
            "rewardValue": invalid_promotion_reward_value,
            "rewardValueType": "PERCENTAGE",
        }
    ]
    data = raw_create_promotion(
        e2e_staff_api_client,
        invalid_promotion_name,
        invalid_promotion_type,
        invalid_promotion_rules,
    )
    errors = data["errors"]
    assert errors[0]["message"] == (
        "`Order` predicate cannot be provided for promotion rule with "
        "`catalogue` predicate type."
    )
    assert errors[0]["code"] == "INVALID"
    assert errors[0]["field"] == "orderPredicate"

    # Step 2- Create promotion with rule with order predicate
    promotion_name = "Promotion"
    promotion_type = "ORDER"
    reward_value = "20"
    rules = [
        {
            "name": "rule for promotion with order predicate",
            "channels": [channel_id],
            "orderPredicate": {
                "discountedObjectPredicate": {"baseTotalPrice": {"eq": "10"}}
            },
            "rewardType": "SUBTOTAL_DISCOUNT",
            "rewardValue": reward_value,
            "rewardValueType": "PERCENTAGE",
        }
    ]
    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, promotion_type, rules
    )
    promotion_rule_id = promotion_data["rules"][0]["id"]

    # Step 3 - Check the promotion rule cannot be updated with catalogue predicate
    update_input = {
        "cataloguePredicate": {"collectionPredicate": {"ids": [collection_id]}}
    }
    data = raw_update_promotion_rule(
        e2e_staff_api_client, promotion_rule_id, update_input
    )
    error = data["errors"][0]
    assert (
        error["message"]
        == "`Catalogue` predicate cannot be provided for promotion rule with `order` predicate type."
    )
    assert error["code"] == "INVALID"
    assert error["field"] == "cataloguePredicate"
