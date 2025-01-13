import pytest

from ... import DEFAULT_ADDRESS
from ...orders.utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_line_discount_update,
    order_lines_create,
)
from ...product.utils.preparing_product import prepare_digital_product
from ...shop.utils.preparing_shop import prepare_default_shop
from ...utils import assign_permissions


@pytest.mark.e2e
def test_complete_draft_order_with_0_total_manual_discount_for_digital_products_CORE_0239(
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

    _product_id, product_variant_id, product_variant_price = prepare_digital_product(
        e2e_staff_api_client, channel_id, warehouse_id, 200
    )
    variant_quantity = 1

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
            "variantId": product_variant_id,
            "quantity": variant_quantity,
        }
    ]
    order_data = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_product_variant_id = order_data["order"]["lines"][0]["variant"]["id"]
    assert order_product_variant_id == product_variant_id
    assert order_data["order"]["total"]["gross"]["amount"] == product_variant_price

    order_line = order_data["order"]["lines"][0]
    line_total = round(product_variant_price * variant_quantity, 2)
    assert order_line["totalPrice"]["gross"]["amount"] == product_variant_price
    assert order_line["undiscountedTotalPrice"]["gross"]["amount"] == line_total
    assert order_line["unitPrice"]["gross"]["amount"] == product_variant_price
    assert order_line["undiscountedTotalPrice"]["gross"]["amount"] == line_total

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
    assert draft_order["order"]["isShippingRequired"] is False

    # Step 4 - Add manual discount to the order line
    manual_discount_value = product_variant_price
    manual_discount_reason = "Manual discount reason"
    manual_line_discount_input = {
        "valueType": "FIXED",
        "value": manual_discount_value,
        "reason": manual_discount_reason,
    }
    order_data = order_line_discount_update(
        e2e_staff_api_client, order_line["id"], manual_line_discount_input
    )
    assert order_data["order"]["total"]["gross"]["amount"] == 0
    assert order_data["order"]["subtotal"]["gross"]["amount"] == 0
    order_line = order_data["order"]["lines"][0]
    assert order_line["totalPrice"]["gross"]["amount"] == 0
    assert order_line["undiscountedTotalPrice"]["gross"]["amount"] == line_total
    assert order_line["unitPrice"]["gross"]["amount"] == 0
    assert (
        order_line["undiscountedUnitPrice"]["gross"]["amount"] == product_variant_price
    )

    # Step 5 - Complete the order and check it's status
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert order["order"]["status"] == "UNFULFILLED"
    assert order["order"]["total"]["gross"]["amount"] == 0
    order_line = order["order"]["lines"][0]
    assert order_line["totalPrice"]["gross"]["amount"] == 0
    assert order_line["undiscountedTotalPrice"]["gross"]["amount"] == line_total
    assert order_line["unitPrice"]["gross"]["amount"] == 0
    assert (
        order_line["undiscountedUnitPrice"]["gross"]["amount"] == product_variant_price
    )
