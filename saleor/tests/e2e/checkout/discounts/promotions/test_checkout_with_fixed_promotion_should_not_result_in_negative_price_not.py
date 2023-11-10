import pytest

from ....product.utils import get_product
from ....product.utils.preparing_product import prepare_product
from ....promotions.utils import create_promotion, create_promotion_rule
from ....shop.utils.preparing_shop import prepare_shop
from ....utils import assign_permissions
from ...utils import checkout_create


@pytest.mark.e2e
def test_checkout_with_fixed_promotion_should_not_result_in_negative_price_CORE_2111(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_discounts,
    permission_manage_orders,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_discounts,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        result_warehouse_id,
        result_channel_id,
        result_channel_slug,
        _,
    ) = prepare_shop(e2e_staff_api_client)

    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, result_warehouse_id, result_channel_id, variant_price=5
    )

    promotion_name = "Promotion Fixed"

    promotion_data = create_promotion(
        e2e_staff_api_client,
        promotion_name,
    )
    promotion_id = promotion_data["id"]

    assert promotion_id is not None

    # Step 1 - Create promotion rule with fixed promotion for the product
    discount_value = 10
    discount_type = "FIXED"
    promotion_rule_name = "rule for product"

    catalogue_predicate = {"productPredicate": {"ids": [product_id]}}

    promotion_rule = create_promotion_rule(
        e2e_staff_api_client,
        promotion_id,
        catalogue_predicate,
        discount_type,
        discount_value,
        promotion_rule_name,
        result_channel_id,
    )
    product_predicate = promotion_rule["cataloguePredicate"]["productPredicate"]["ids"]
    assert promotion_rule["channels"][0]["id"] == result_channel_id
    assert product_predicate[0] == product_id

    # Step 2 - Get product and check if it is on promotion
    product_data = get_product(e2e_staff_api_client, product_id, result_channel_slug)
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
        result_channel_slug,
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
