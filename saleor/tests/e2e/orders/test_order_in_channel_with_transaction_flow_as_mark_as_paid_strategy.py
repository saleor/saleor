import pytest

from .. import DEFAULT_ADDRESS
from ..channel.utils import create_channel
from ..product.utils.preparing_product import prepare_product
from ..shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse
from .utils import (
    draft_order_complete,
    draft_order_create,
    draft_order_update,
    mark_order_paid,
    order_lines_create,
    order_query,
)


def prepare_shop_in_channel_with_transaction_flow_as_mark_as_paid_strategy(
    e2e_staff_api_client,
):
    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    warehouse_ids = [warehouse_id]

    channel_data = create_channel(
        e2e_staff_api_client,
        warehouse_ids=[warehouse_ids],
        mark_as_paid_strategy="TRANSACTION_FLOW",
    )
    channel_id = channel_data["id"]

    shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=[warehouse_id],
        channel_ids=[channel_id],
    )
    shipping_zone_id = shipping_zone_data["id"]

    shipping_method_data = create_shipping_method(
        e2e_staff_api_client,
        shipping_zone_id,
        type="PRICE",
    )
    shipping_method_id = shipping_method_data["id"]

    create_shipping_method_channel_listing(
        e2e_staff_api_client,
        shipping_method_id,
        channel_id,
    )

    return (
        warehouse_id,
        channel_id,
        shipping_method_id,
    )


@pytest.mark.e2e
def test_order_in_channel_with_transaction_flow_as_mark_as_paid_strategy_CORE_0209(
    e2e_staff_api_client,
    e2e_app_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_orders,
    permission_manage_payments,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_payments,
    ]
    assign_permissions(e2e_staff_api_client, permissions)
    app_permissions = [permission_manage_payments]
    assign_permissions(e2e_app_api_client, app_permissions)

    (
        warehouse_id,
        channel_id,
        shipping_method_id,
    ) = prepare_shop_in_channel_with_transaction_flow_as_mark_as_paid_strategy(
        e2e_staff_api_client
    )

    price = 2
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
    lines = [{"variantId": product_variant_id, "quantity": 1}]
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

    # Step 4 - Complete the order and check it's status
    order = draft_order_complete(e2e_staff_api_client, order_id)
    order_complete_id = order["order"]["id"]
    assert order_complete_id == order_id
    order_line = order["order"]["lines"][0]
    assert order_line["productVariantId"] == product_variant_id
    assert order["order"]["status"] == "UNFULFILLED"
    assert (
        order["order"]["channel"]["orderSettings"]["markAsPaidStrategy"]
        == "TRANSACTION_FLOW"
    )
    order_total = order["order"]["total"]["gross"]["amount"]
    assert order_total != 0

    # Step 5 - Mark order as paid in transaction flow and check order's payment status
    order_paid_data = mark_order_paid(
        e2e_staff_api_client,
        order_id,
        transactionReference="test-pspreference",
    )
    assert order_paid_data["order"]["isPaid"] is True
    assert order_paid_data["order"]["paymentStatus"] == "FULLY_CHARGED"
    assert order_paid_data["order"]["status"] == "UNFULFILLED"
    order_data = order_query(
        e2e_staff_api_client,
        order_id,
    )
    assert order_data["isPaid"] is True
    assert order_data["paymentStatus"] == "FULLY_CHARGED"
    assert order_data["transactions"] is not None
