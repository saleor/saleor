import pytest

from ..product.utils import get_product
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions
from .utils import create_promotion, create_promotion_rule, update_promotion_rule


def prepare_promotion(
    e2e_staff_api_client,
    discount_value,
    discount_type,
    promotion_rule_name="Test rule",
    variant_ids=None,
    channel_id=None,
):
    promotion_name = "Promotion Test"
    promotion_data = create_promotion(e2e_staff_api_client, promotion_name)
    promotion_id = promotion_data["id"]

    predicate_input = {"variantPredicate": {"ids": variant_ids}}
    promotion_rule_data = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        predicate_input,
        discount_type,
        discount_value,
        promotion_rule_name,
        channel_id,
    )
    promotion_rule_id = promotion_rule_data["id"]
    discount_value = promotion_rule_data["rewardValue"]

    return promotion_rule_id, discount_value


@pytest.mark.e2e
def test_staff_can_change_reward_value_type_in_promotion_rule_core_2117(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_shipping,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_shipping,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    warehouse_id, channel_id, channel_slug, _shipping_method_id = prepare_shop(
        e2e_staff_api_client
    )

    product_id, product_variant_id, product_variant_price = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, "14.99"
    )

    promotion_rule_id, discount_value = prepare_promotion(
        e2e_staff_api_client,
        30,
        "PERCENTAGE",
        variant_ids=[product_variant_id],
        channel_id=channel_id,
    )

    # Step 1 - Get product and check prices
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    variant = product_data["variants"][0]
    variant_discount = round(float(product_variant_price) * discount_value / 100, 2)
    assert variant["pricing"]["discount"]["gross"]["amount"] == variant_discount
    unit_price = variant["pricing"]["price"]["gross"]["amount"]
    assert unit_price == float(product_variant_price) - variant_discount

    # Step 2 - Update promotion rule by changing discount value type
    fixed_reward_value = 10
    input = {"rewardValueType": "FIXED", "rewardValue": fixed_reward_value}
    rule_data = update_promotion_rule(e2e_staff_api_client, promotion_rule_id, input)
    assert rule_data["rewardValueType"] == "FIXED"
    assert rule_data["rewardValue"] == fixed_reward_value

    # Step 3 - Get product and check prices
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    variant = product_data["variants"][0]
    variant_discount = fixed_reward_value
    assert variant["pricing"]["discount"]["gross"]["amount"] == variant_discount
    unit_price = variant["pricing"]["price"]["gross"]["amount"]
    assert unit_price == float(product_variant_price) - variant_discount
