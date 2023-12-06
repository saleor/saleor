import pytest

from ..checkout.utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    raw_checkout_dummy_payment_create,
)
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import order_query, order_void, raw_order_void


def prepare_checkout_with_voided_payment(e2e_staff_api_client):
    price = 10

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
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

    lines = [
        {
            "variantId": product_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_create(
        e2e_staff_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    checkout_data = checkout_delivery_method_update(
        e2e_staff_api_client,
        checkout_id,
        shipping_method_id,
    )
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    raw_checkout_dummy_payment_create(
        e2e_staff_api_client,
        checkout_id,
        total_gross_amount,
        token="not-charged",
    )

    order_data = checkout_complete(
        e2e_staff_api_client,
        checkout_id,
    )
    order_id = order_data["id"]

    order_void(
        e2e_staff_api_client,
        order_id,
    )

    return order_id


@pytest.mark.e2e
def test_checkout_void_once_voided_payment_CORE_0218(
    e2e_staff_api_client,
    e2e_app_api_client,
    shop_permissions,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_payments,
    permission_handle_checkouts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)
    app_permissions = [
        permission_manage_payments,
        permission_handle_checkouts,
        permission_manage_orders,
        permission_manage_channels,
    ]
    assign_permissions(e2e_app_api_client, app_permissions)

    order_id = prepare_checkout_with_voided_payment(
        e2e_staff_api_client,
    )

    # Step 1 - Check the order's payment is voided
    order_data = order_query(
        e2e_staff_api_client,
        order_id,
    )
    events = order_data["events"]
    assert events != []
    assert any(event["type"] == "PAYMENT_VOIDED" for event in events)
    assert order_data["status"] == "UNFULFILLED"

    # Step 2 - Void the payment
    order = raw_order_void(
        e2e_staff_api_client,
        order_id,
    )
    error = order["errors"][0]
    assert error["message"] == "Only pre-authorized payments can be voided"
    assert error["code"] == "VOID_INACTIVE_PAYMENT"
    assert error["field"] == "payment"
