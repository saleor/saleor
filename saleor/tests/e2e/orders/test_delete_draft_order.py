import pytest

from .. import DEFAULT_ADDRESS
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions
from .utils import (
    draft_order_create,
    draft_order_delete,
    draft_order_update,
    order_lines_create,
    order_query,
)


@pytest.mark.e2e
def test_delete_draft_order_CORE_0205(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_orders,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    price = 10

    (
        warehouse_id,
        channel_id,
        _channel_slug,
        shipping_method_id,
    ) = prepare_shop(e2e_staff_api_client)

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

    # Step 4 - Delete the order
    cancelled_order = draft_order_delete(
        e2e_staff_api_client,
        order_id,
    )
    assert cancelled_order["order"]["status"] is not None
    order = order_query(e2e_staff_api_client, order_id)
    assert order is None
