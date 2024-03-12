import pytest

from ......product.tasks import recalculate_discounted_price_for_products_task
from ....product.utils import get_product
from ....product.utils.preparing_product import prepare_product
from ....promotions.utils import create_promotion, create_promotion_rule
from ....shop.utils import prepare_default_shop
from ....utils import assign_permissions
from ...utils import checkout_create


@pytest.mark.e2e
def test_checkout_with_fixed_promotion_should_not_result_in_negative_price_CORE_2111(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]

    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(e2e_staff_api_client, warehouse_id, channel_id, variant_price=5)

    promotion_name = "Promotion Fixed"
    promotion_type = "CATALOGUE"

    promotion_data = create_promotion(
        e2e_staff_api_client,
        promotion_name,
        promotion_type,
    )
    promotion_id = promotion_data["id"]

    assert promotion_id is not None

    # Step 1 - Create promotion rule with fixed promotion for the product
    discount_value = 10
    discount_type = "FIXED"
    promotion_rule_name = "rule for product"

    catalogue_predicate = {"productPredicate": {"ids": [product_id]}}

    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": promotion_rule_name,
        "cataloguePredicate": catalogue_predicate,
        "rewardValue": discount_value,
        "rewardValueType": discount_type,
    }
    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        input,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == channel_id
    assert product_predicate[0] == product_id

    # prices are updated in the background, we need to force it to retrieve the correct
    # ones
    recalculate_discounted_price_for_products_task()

    # Step 2 - Get product and check if it is on promotion
    product_data = get_product(e2e_staff_api_client, product_id, channel_slug)
    assert product_data["id"] == product_id
    assert product_data["pricing"]["onSale"] is True
    variant_data = product_data["variants"][0]
    variant_id = product_data["variants"][0]["id"]
    assert variant_id == product_variant_id
    assert variant_data["pricing"]["onSale"] is True

    # Step 3 - Create checkout and verify the total is not below 0
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]
    assert checkout_id is not None
    checkout_lines = checkout_data["lines"][0]
    unit_price = float(product_variant_price) - discount_value
    assert unit_price < 0
    assert checkout_lines["unitPrice"]["gross"]["amount"] == 0
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == float(
        product_variant_price
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    assert total_gross_amount == 0
