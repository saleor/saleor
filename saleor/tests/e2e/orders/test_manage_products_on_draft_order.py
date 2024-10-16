import pytest

from .. import DEFAULT_ADDRESS
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    draft_order_complete,
    draft_order_create,
    order_line_delete,
    order_line_update,
    order_lines_create,
    order_update_shipping,
)


@pytest.mark.e2e
def test_should_change_lines_on_draft_orders_CORE_0246(
    e2e_staff_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
):
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
    product1_price = 9
    product2_price = 21

    (
        _product1_id,
        product1_variant_id,
        product1_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=product1_price,
        product_type_slug="test-product-type1",
    )

    (
        _product2_id,
        product2_variant_id,
        product2_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=product2_price,
        product_type_slug="test-product-type2",
    )

    # Step 1 - Create a draft order
    input = {
        "channelId": channel_id,
        "userEmail": "customer@example.com",
        "billingAddress": DEFAULT_ADDRESS,
        "shippingAddress": DEFAULT_ADDRESS,
    }
    data = draft_order_create(e2e_staff_api_client, input)
    order_id = data["order"]["id"]
    assert data["order"]["billingAddress"] is not None
    assert data["order"]["shippingAddress"] is not None
    assert order_id is not None

    # Step 2 - Add order lines to the order
    lines = [
        {"variantId": product1_variant_id, "quantity": 2},
        {"variantId": product2_variant_id, "quantity": 5},
    ]
    order = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_lines = order["order"]["lines"]
    assert len(order_lines) == 2
    line1_total = product1_variant_price * 2
    line2_total = product2_variant_price * 5
    assert order_lines[0]["totalPrice"]["gross"]["amount"] == line1_total
    assert order_lines[1]["totalPrice"]["gross"]["amount"] == line2_total
    first_order_line_id = order_lines[0]["id"]
    second_order_line_id = order_lines[1]["id"]
    assert order["order"]["subtotal"]["gross"]["amount"] == line1_total + line2_total

    # Step 3 - Update second order line quantity
    input = {"quantity": 2}

    order = order_line_update(e2e_staff_api_client, second_order_line_id, input)
    order_lines = order["order"]["lines"]
    assert len(order_lines) == 2
    line2_total = product2_variant_price * 2
    assert order["order"]["lines"][1]["quantity"] == 2
    assert order["order"]["lines"][1]["totalPrice"]["gross"]["amount"] == line2_total
    assert order["order"]["subtotal"]["gross"]["amount"] == line1_total + line2_total

    # Step 4 - Remove first order line
    order = order_line_delete(e2e_staff_api_client, first_order_line_id)
    assert len(order["order"]["lines"]) == 1
    assert order["order"]["lines"][0]["id"] == second_order_line_id
    assert order["order"]["subtotal"]["gross"]["amount"] == line2_total

    # Step 5 - Add a shipping method to the order
    input = {"shippingMethod": shipping_method_id}
    order = order_update_shipping(e2e_staff_api_client, order_id, input)
    assert order["order"]["deliveryMethod"]["id"] is not None
    assert order["order"]["shippingPrice"]["gross"]["amount"] == shipping_price
    assert order["order"]["total"]["gross"]["amount"] == line2_total + shipping_price

    # Step 6 - Complete the draft order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    assert len(order["order"]["lines"]) == 1
    assert order["order"]["lines"][0]["id"] == second_order_line_id
    assert order["order"]["total"]["gross"]["amount"] == line2_total + shipping_price
    assert order["order"]["shippingPrice"]["gross"]["amount"] == shipping_price
