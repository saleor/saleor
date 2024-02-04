import pytest

from .. import DEFAULT_ADDRESS
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    order_lines_create,
    raw_order_void,
)


@pytest.mark.e2e
def test_unable_to_void_order_without_payment_CORE_0210(
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

    price = 10

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        price,
    )

    # Step 1 - Create draft order
    draft_order_input = {
        "channelId": channel_id,
        "userEmail": "test_user@test.com",
        "shippingAddress": DEFAULT_ADDRESS,
        "billingAddress": DEFAULT_ADDRESS,
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
            "quantity": 1,
        }
    ]
    order_lines = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_product_variant_id = order_lines["order"]["lines"][0]["variant"]["id"]
    assert order_product_variant_id == product_variant_id

    # Step 3 - Update order's shipping method
    input = {"shippingMethod": shipping_method_id}
    draft_order = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    order_shipping_id = draft_order["order"]["deliveryMethod"]["id"]
    assert order_shipping_id is not None

    # Step 4 - Complete the order
    order = draft_order_complete(e2e_staff_api_client, order_id)
    order_complete_id = order["order"]["id"]
    order_line = order["order"]["lines"][0]
    assert order_complete_id == order_id
    assert order_line["productVariantId"] == product_variant_id
    assert order["order"]["status"] == "UNFULFILLED"

    # Step 5 - Void the order
    order = raw_order_void(
        e2e_staff_api_client,
        order_id,
    )
    error = order["errors"][0]
    assert error["message"] == "There's no payment associated with the order."
    assert error["code"] == "PAYMENT_MISSING"
    assert error["field"] == "payment"
