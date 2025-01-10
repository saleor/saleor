import pytest

from .. import DEFAULT_ADDRESS
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    draft_order_bulk_delete,
    draft_order_create,
    order_lines_create,
    order_query,
)


@pytest.mark.e2e
def test_delete_draft_orders_in_bulk_CORE_0248(
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

    orders_list = []
    for i in range(5):
        user_email = f"test_user_{i +1}@test.com"
        draft_order_input = {
            "channelId": channel_id,
            "userEmail": user_email,
            "shippingAddress": DEFAULT_ADDRESS,
            "billingAddress": DEFAULT_ADDRESS,
        }
        data = draft_order_create(
            e2e_staff_api_client,
            draft_order_input,
        )
        order_id = order_id = data["order"]["id"]
        lines = [
            {
                "variantId": product_variant_id,
                "quantity": 1,
            }
        ]
        order_lines_create(
            e2e_staff_api_client,
            order_id,
            lines,
        )
        orders_list.append(order_id)

    # Step 1 - Remove draft orders in bulk
    data = draft_order_bulk_delete(e2e_staff_api_client, orders_list)
    assert data["errors"] == []
    assert data["count"] == 5

    # Step 2 - Try to query the deleted draft orders
    for order_id in orders_list:
        data = order_query(e2e_staff_api_client, order_id)
        assert data is None
