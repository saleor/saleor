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
)


@pytest.mark.e2e
def test_order_with_the_same_variant_in_multiple_lines_and_overwrite_prices_core_0213(
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

    (
        _product_id,
        product_variant_id,
        product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price=10,
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

    # Step 2 - Add lines to the order and overwrite variants price
    new_price = 9.99
    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
            "price": new_price,
        },
        {
            "variantId": product_variant_id,
            "quantity": 1,
            "forceNewLine": True,
        },
    ]
    order_lines = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    assert order_lines["order"]["lines"] is not None
    first_line_product_variant = order_lines["order"]["lines"][0]
    assert first_line_product_variant["variant"]["id"] == product_variant_id
    second_line_product_variant = order_lines["order"]["lines"][1]
    assert second_line_product_variant["variant"]["id"] == product_variant_id
    assert order_lines["order"]["shippingMethods"] is not None

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
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    order_complete_id = order["order"]["id"]
    assert order_complete_id == order_id
    order_line = order["order"]["lines"]
    first_line_product_variant = order_line[0]
    second_line_product_variant = order_line[1]
    assert first_line_product_variant["productVariantId"] == product_variant_id
    assert second_line_product_variant["productVariantId"] == product_variant_id
    first_product_variant_price = first_line_product_variant["unitPrice"]["gross"][
        "amount"
    ]
    assert first_product_variant_price == product_variant_price
    second_product_variant_price = second_line_product_variant["unitPrice"]["gross"][
        "amount"
    ]
    assert second_product_variant_price != product_variant_price
    assert second_product_variant_price == new_price
    assert order["order"]["status"] == "UNFULFILLED"
