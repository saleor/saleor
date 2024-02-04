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
    order_invoice_create,
    order_lines_create,
    order_query,
)


def prepare_fulfilled_order(e2e_staff_api_client):
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
    draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )

    mark_order_paid(
        e2e_staff_api_client,
        order_id,
    )

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
    order_fulfill(e2e_staff_api_client, order_id, input)

    return (order_id,)


@pytest.mark.e2e
def test_order_create_invoice_with_metadata_CORE_0212(
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

    (order_id,) = prepare_fulfilled_order(e2e_staff_api_client)

    # Step 1 - Create invoice for the order
    order = order_query(e2e_staff_api_client, order_id)
    assert order["status"] == "FULFILLED"
    invoice_number = "FV_123"
    invoice_url = "https://example.com"
    invoice_metadata = [{"key": "invoice_code", "value": "abc"}]
    invoice_private_metadata = [{"key": "invoice_code", "value": "priv-abc"}]
    input = {
        "number": invoice_number,
        "url": invoice_url,
        "metadata": invoice_metadata,
        "privateMetadata": invoice_private_metadata,
    }
    data = order_invoice_create(e2e_staff_api_client, order_id, input)
    assert data["invoice"]["number"] == invoice_number
    assert data["invoice"]["url"] == invoice_url
    assert data["invoice"]["metadata"] == invoice_metadata
    assert data["invoice"]["privateMetadata"] == invoice_private_metadata
