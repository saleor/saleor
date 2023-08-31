import pytest

from ..orders.utils.draft_order import draft_order_create
from ..orders.utils.order_lines import order_lines_create
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
        result_warehouse_id,
        result_channel_id,
        _,
        _,
    ) = prepare_shop(e2e_staff_api_client)

    _, result_product_variant_id, _ = prepare_product(
        e2e_staff_api_client, result_warehouse_id, result_channel_id, price
    )

    # Step 1 - Create checkout from order
    data = draft_order_create(
        e2e_staff_api_client,
        result_channel_id,
    )

    order_id = data["order"]["id"]
    assert order_id is not None
    order_lines = [
        {"variantId": result_product_variant_id, "quantity": 1, "price": 100}
    ]
    order_data = order_lines_create(e2e_staff_api_client, order_id, order_lines)
    order_product_variant_id = order_data["order"]["lines"][0]["variant"]
    order_product_quantity = order_data["order"]["lines"][0]["quantity"]

    checkout_data = checkout_create_from_order(e2e_staff_api_client, order_id)
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
