import pytest

from .. import DEFAULT_ADDRESS
from ..product.utils.preparing_product import prepare_product
from ..shop.utils import prepare_shop
from ..utils import assign_permissions
from .utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    mark_order_paid,
    order_fulfill,
    order_fulfillment_cancel,
    order_lines_create,
    order_query,
)


def prepare_order(e2e_staff_api_client):
    price = 10

    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "shipping_methods": [{}],
                    },
                ],
                "order_settings": {},
            }
        ],
        shop_settings={
            "fulfillmentAutoApprove": True,
            "fulfillmentAllowUnpaid": False,
        },
    )
    channel_id = shop_data[0]["id"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

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
    data = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_line_id = data["order"]["lines"][0]["id"]

    input = {"shippingMethod": shipping_method_id}
    draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )

    return (
        order_id,
        product_variant_id,
        warehouse_id,
        order_line_id,
    )


@pytest.mark.e2e
def test_order_cancel_fulfillment_CORE_0220(
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
    (
        order_id,
        product_variant_id,
        warehouse_id,
        order_line_id,
    ) = prepare_order(
        e2e_staff_api_client,
    )

    # Step 1 - Complete the order
    order = draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    order_complete_id = order["order"]["id"]
    assert order_complete_id == order_id
    order_line = order["order"]["lines"][0]
    assert order_line["productVariantId"] == product_variant_id
    assert order["order"]["status"] == "UNFULFILLED"

    # Step 2 - Mark order as paid
    order_paid_data = mark_order_paid(
        e2e_staff_api_client,
        order_id,
    )
    assert order_paid_data["order"]["isPaid"] is True
    assert order_paid_data["order"]["paymentStatus"] == "FULLY_CHARGED"
    assert order_paid_data["order"]["status"] == "UNFULFILLED"

    # Step 3 - Fulfill the order and check the status
    input = {
        "lines": [
            {
                "orderLineId": order_line_id,
                "stocks": [
                    {
                        "quantity": 1,
                        "warehouse": warehouse_id,
                    }
                ],
            }
        ],
        "notifyCustomer": True,
        "allowStockToBeExceeded": False,
    }
    order_data = order_fulfill(e2e_staff_api_client, order_id, input)
    fulfillment_id = order_data["order"]["fulfillments"][0]["id"]
    assert order_data["order"]["fulfillments"] != []
    assert order_data["order"]["fulfillments"][0]["status"] == "FULFILLED"

    order = order_query(e2e_staff_api_client, order_id)
    assert order["status"] == "FULFILLED"

    # Step 4 - Cancel the fulfillment
    order_data = order_fulfillment_cancel(
        e2e_staff_api_client,
        fulfillment_id,
        warehouse_id,
    )
    assert order_data["order"]["status"] == "UNFULFILLED"
    assert order_data["order"]["fulfillments"] != []
    assert order_data["order"]["fulfillments"][0]["status"] == "CANCELED"
