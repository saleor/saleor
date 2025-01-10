import pytest

from ... import DEFAULT_ADDRESS
from ...orders.utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_discount_add,
    order_lines_create,
)
from ...product.utils.preparing_product import prepare_products
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions


@pytest.mark.e2e
def test_complete_draft_order_with_0_total_100_percent_manual_total_discount_CORE_0252(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    shipping_price = 10

    products_data = prepare_products(
        e2e_staff_api_client, warehouse_id, channel_id, [103, 9.99]
    )
    product1_variant_id = products_data[0]["variant_id"]
    product1_variant_price = float(products_data[0]["price"])

    product2_variant_id = products_data[1]["variant_id"]
    product2_variant_price = float(products_data[1]["price"])

    variant1_quantity = 2
    variant2_quantity = 1

    # Step 1 - Create draft order
    draft_order_input = {
        "channelId": channel_id,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        draft_order_input,
    )
    order_id = data["order"]["id"]
    assert order_id is not None

    # Step 2 - Add lines to the order
    lines = [
        {
            "variantId": product1_variant_id,
            "quantity": variant1_quantity,
        },
        {
            "variantId": product2_variant_id,
            "quantity": variant2_quantity,
        },
    ]
    order_data = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    assert len(order_data["order"]["lines"]) == 2
    line1_total = round(product1_variant_price * variant1_quantity, 2)
    line2_total = round(product2_variant_price * variant2_quantity, 2)

    line1 = order_data["order"]["lines"][0]
    assert line1["totalPrice"]["gross"]["amount"] == line1_total
    assert line1["unitPrice"]["gross"]["amount"] == product1_variant_price
    assert line1["undiscountedTotalPrice"]["gross"]["amount"] == line1_total
    assert line1["undiscountedUnitPrice"]["gross"]["amount"] == product1_variant_price

    line2 = order_data["order"]["lines"][1]
    assert line2["totalPrice"]["gross"]["amount"] == line2_total
    assert line2["unitPrice"]["gross"]["amount"] == product2_variant_price
    assert line2["undiscountedTotalPrice"]["gross"]["amount"] == line2_total
    assert line2["undiscountedUnitPrice"]["gross"]["amount"] == product2_variant_price

    calculated_subtotal = line1_total + line2_total
    assert order_data["order"]["subtotal"]["gross"]["amount"] == calculated_subtotal
    assert order_data["order"]["total"]["gross"]["amount"] == calculated_subtotal

    # Step 3 - Update order's addresses and email
    input = {
        "userEmail": "test_user@test.com",
        "shippingAddress": DEFAULT_ADDRESS,
        "billingAddress": DEFAULT_ADDRESS,
    }
    draft_order = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )

    assert draft_order["order"]["userEmail"] == "test_user@test.com"
    assert draft_order["order"]["shippingAddress"] is not None
    assert draft_order["order"]["billingAddress"] is not None
    assert draft_order["order"]["isShippingRequired"] is True
    assert draft_order["order"]["total"]["gross"]["amount"] == calculated_subtotal
    assert draft_order["order"]["subtotal"]["gross"]["amount"] == calculated_subtotal

    # Step 4 - Update shipping method
    shipping_method_id = shop_data["shipping_method"]["id"]
    draft_order = draft_order_update(
        e2e_staff_api_client,
        order_id,
        {"shippingMethod": shipping_method_id},
    )
    assert draft_order["order"]["shippingPrice"]["gross"]["amount"] == shipping_price
    calculated_total = calculated_subtotal + shipping_price
    assert draft_order["order"]["total"]["gross"]["amount"] == calculated_total
    assert draft_order["order"]["subtotal"]["gross"]["amount"] == calculated_subtotal

    # Step 5 - Add manual discount to the order
    manual_discount_input = {
        "valueType": "PERCENTAGE",
        "value": 100,
    }
    order_data = order_discount_add(
        e2e_staff_api_client,
        order_id,
        manual_discount_input,
    )
    assert order_data["order"]["total"]["gross"]["amount"] == 0
    assert order_data["order"]["subtotal"]["gross"]["amount"] == 0
    assert order_data["order"]["shippingPrice"]["gross"]["amount"] == 0
    assert order_data["order"]["undiscountedShippingPrice"]["amount"] == shipping_price
    # Bug SHOPX-1390 - uncoment below line when fixed
    # assert (
    #     order_data["order"]["undiscountedTotal"]["gross"]["amount"] == calculated_total
    # )
    assert order_data["order"]["discounts"][0]["amount"]["amount"] == calculated_total

    line1 = order_data["order"]["lines"][0]
    assert line1["totalPrice"]["gross"]["amount"] == 0
    assert line1["unitPrice"]["gross"]["amount"] == 0
    assert line1["undiscountedTotalPrice"]["gross"]["amount"] == line1_total
    assert line1["undiscountedUnitPrice"]["gross"]["amount"] == product1_variant_price

    line2 = order_data["order"]["lines"][1]
    assert line2["totalPrice"]["gross"]["amount"] == 0
    assert line2["unitPrice"]["gross"]["amount"] == 0
    assert line2["undiscountedTotalPrice"]["gross"]["amount"] == line2_total
    assert line2["undiscountedUnitPrice"]["gross"]["amount"] == product2_variant_price

    # Step 6 - Complete the order and check it's status
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["order"]["status"] == "UNFULFILLED"
    assert order["order"]["total"]["gross"]["amount"] == 0
    assert order["order"]["subtotal"]["gross"]["amount"] == 0
    assert order["order"]["discounts"][0]["amount"]["amount"] == calculated_total
    assert order["order"]["shippingPrice"]["gross"]["amount"] == 0
    assert order["order"]["undiscountedShippingPrice"]["amount"] == shipping_price
    # Bug SHOPX-1390 - uncoment below line when fixed
    # assert order["order"]["undiscountedTotal"]["gross"]["amount"] == calculated_total

    assert len(order["order"]["lines"]) == 2
    line1 = order["order"]["lines"][0]
    assert line1["unitPrice"]["gross"]["amount"] == 0
    assert line1["totalPrice"]["gross"]["amount"] == 0
    assert line1["undiscountedTotalPrice"]["gross"]["amount"] == line1_total
    assert line1["undiscountedUnitPrice"]["gross"]["amount"] == product1_variant_price

    line2 = order["order"]["lines"][1]
    assert line2["unitPrice"]["gross"]["amount"] == 0
    assert line2["totalPrice"]["gross"]["amount"] == 0
    assert line2["undiscountedTotalPrice"]["gross"]["amount"] == line2_total
    assert line2["undiscountedUnitPrice"]["gross"]["amount"] == product2_variant_price
