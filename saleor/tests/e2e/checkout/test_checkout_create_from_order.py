import pytest

from ..orders.utils import draft_order_create, order_lines_create
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions
from .utils import checkout_create_from_order


@pytest.mark.e2e
def test_checkout_create_from_order_core_0104(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_orders,
    permission_manage_checkouts,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    price = 10

    (
        warehouse_id,
        channel_id,
        _channel_slug,
        _shipping_method_id,
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

    # Step 1 - Create checkout from order
    channel_id = {"channelId": channel_id}
    data = draft_order_create(
        e2e_staff_api_client,
        channel_id,
    )

    order_id = data["order"]["id"]
    assert order_id is not None
    order_lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
            "price": 100,
        }
    ]
    order_data = order_lines_create(
        e2e_staff_api_client,
        order_id,
        order_lines,
    )
    order_product_variant_id = order_data["order"]["lines"][0]["variant"]
    order_product_quantity = order_data["order"]["lines"][0]["quantity"]

    checkout_data = checkout_create_from_order(
        e2e_staff_api_client,
        order_id,
    )
    checkout_id = checkout_data["checkout"]["id"]
    assert checkout_id is not None
    errors = checkout_data["errors"]
    assert errors == []
    checkout_lines = checkout_data["checkout"]["lines"]
    assert checkout_lines != []

    checkout_product_variant_id = checkout_lines[0]["variant"]["id"]
    checkout_product_quantity = checkout_lines[0]["quantity"]
    order_product_variant_id_value = order_product_variant_id["id"]

    assert checkout_product_variant_id == order_product_variant_id_value
    assert checkout_product_quantity == order_product_quantity
