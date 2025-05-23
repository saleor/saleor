import pytest

from ......product.tasks import recalculate_discounted_price_for_products_task
from ....product.utils.preparing_product import prepare_product
from ....promotions.utils import create_promotion, create_promotion_rule
from ....shop.utils import prepare_default_shop
from ....utils import assign_permissions
from ...utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)


@pytest.mark.e2e
def test_checkout_products_on_fixed_promotion_core_2102(
    e2e_not_logged_api_client,
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

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client, warehouse_id, channel_id, variant_price=20
    )

    promotion_name = "Promotion Fixed"
    discount_value = 5
    discount_type = "FIXED"
    promotion_rule_name = "rule for product"
    promotion_type = "CATALOGUE"

    promotion_data = create_promotion(
        e2e_staff_api_client, promotion_name, promotion_type
    )
    promotion_id = promotion_data["id"]

    catalogue_predicate = {"productPredicate": {"ids": [product_id]}}

    input = {
        "promotion": promotion_id,
        "channels": [channel_id],
        "name": promotion_rule_name,
        "cataloguePredicate": catalogue_predicate,
        "rewardValue": discount_value,
        "rewardValueType": "FIXED",
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

    # Step 1 - checkoutCreate for product on promotion
    lines = [
        {"variantId": product_variant_id, "quantity": 2},
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
    )
    checkout_id = checkout_data["id"]
    checkout_lines = checkout_data["lines"][0]
    unit_price = float(product_variant_price) - discount_value

    assert checkout_data["isShippingRequired"] is True
    assert checkout_lines["unitPrice"]["gross"]["amount"] == unit_price
    assert checkout_lines["undiscountedUnitPrice"]["amount"] == float(
        product_variant_price
    )

    # Step 2 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    subtotal_gross_amount = checkout_data["subtotalPrice"]["gross"]["amount"]

    # Step 3 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_not_logged_api_client, checkout_id, total_gross_amount
    )

    # Step 5 - Complete checkout.
    order_data = checkout_complete(e2e_not_logged_api_client, checkout_id)

    order_line = order_data["lines"][0]
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["subtotal"]["gross"]["amount"] == subtotal_gross_amount
    assert order_line["undiscountedUnitPrice"]["gross"]["amount"] == float(
        product_variant_price
    )
    assert order_line["unitDiscountType"] == discount_type
    assert order_line["unitPrice"]["gross"]["amount"] == unit_price
    assert order_line["unitDiscount"]["amount"] == float(discount_value)
    assert order_line["unitDiscountReason"] == f"Promotion: {promotion_id}"
