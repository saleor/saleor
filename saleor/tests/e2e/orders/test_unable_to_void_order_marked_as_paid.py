import pytest

from .. import DEFAULT_ADDRESS
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    mark_order_paid,
    order_lines_create,
    order_query,
    raw_order_void,
)


def prepare_order_marked_as_paid(e2e_staff_api_client):
    price = 10

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    _product_id, product_variant_id, _product_variant_price = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        price,
    )

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

    input = {"shippingMethod": shipping_method_id}
    draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )

    draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )

    data = mark_order_paid(
        e2e_staff_api_client,
        order_id,
    )
    payment_id = data["order"]["payments"][0]["id"]

    return order_id, payment_id


@pytest.mark.e2e
def test_unable_to_void_order_marked_as_paid_CORE_0211(
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

    order_id, payment_id = prepare_order_marked_as_paid(e2e_staff_api_client)

    # Step 1 - Check the order is marked as paid
    order_data = order_query(
        e2e_staff_api_client,
        order_id,
    )
    assert order_data["isPaid"] is True
    assert order_data["payments"][0]["id"] == payment_id
    assert order_data["payments"][0]["gateway"] == "manual"
    assert order_data["paymentStatus"] == "FULLY_CHARGED"
    assert order_data["status"] == "UNFULFILLED"

    # Step 2 - Void the payment
    order = raw_order_void(
        e2e_staff_api_client,
        order_id,
    )
    error = order["errors"][0]
    assert error["message"] == "Cannot find successful auth transaction."
    assert error["code"] == "PAYMENT_ERROR"
    assert error["field"] == "payment"
