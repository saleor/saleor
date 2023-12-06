import datetime

import pytest
from django.utils import timezone
from freezegun import freeze_time

from ....order.tasks import delete_expired_orders_task, expire_orders_task
from ..checkout.utils import checkout_create, checkout_delivery_method_update
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assign_permissions
from .utils import order_create_from_checkout, order_query


@pytest.mark.e2e
def test_expired_order_is_deleted_after_specified_time_CORE_0216(
    e2e_staff_api_client,
    e2e_app_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_payments,
    permission_handle_checkouts,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_orders,
        permission_manage_product_types_and_attributes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)
    app_permissions = [
        permission_manage_payments,
        permission_handle_checkouts,
        permission_manage_orders,
        *shop_permissions,
    ]
    assign_permissions(e2e_app_api_client, app_permissions)

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
                "order_settings": {
                    "expireOrdersAfter": 1,
                    "deleteExpiredOrdersAfter": "1",
                },
            }
        ],
        shop_settings={},
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]
    expire_order_after_in_minutes = shop_data[0]["order_settings"]["expireOrdersAfter"]
    delete_expired_order_after_in_days = shop_data[0]["order_settings"][
        "deleteExpiredOrdersAfter"
    ]
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

    # Step 1 - Create checkout
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
    assert checkout_id is not None
    assert checkout_data["isShippingRequired"] is True
    assert len(checkout_data["shippingMethods"]) == 1

    # Step 2 - Assign shipping method
    checkout_data = checkout_delivery_method_update(
        e2e_staff_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] is not None

    # Step 3 - Create order from the checkout
    now = timezone.now()
    order_data = order_create_from_checkout(e2e_app_api_client, checkout_id)
    order_id = order_data["order"]["id"]
    assert order_id is not None
    assert order_data["order"]["status"] == "UNCONFIRMED"
    assert order_data["order"]["paymentStatus"] == "NOT_CHARGED"
    (order_data["order"]["created"]) = now
    assert order_data["order"]["created"] == now
    expired_orders_settings = order_data["order"]["channel"]["orderSettings"][
        "expireOrdersAfter"
    ]
    delete_expired_orders_settings = order_data["order"]["channel"]["orderSettings"][
        "deleteExpiredOrdersAfter"
    ]
    assert expired_orders_settings == expire_order_after_in_minutes
    assert delete_expired_orders_settings == int(delete_expired_order_after_in_days)

    # Step 4 - Check the order is expired
    time_of_expiration = now + datetime.timedelta(minutes=2)
    with freeze_time(time_of_expiration):
        expire_orders_task()
        data = order_query(e2e_staff_api_client, order_id)
        assert data["status"] == "EXPIRED"
        assert data["paymentStatus"] == "NOT_CHARGED"

    # Step 5 - Check the order has been deleted
    valid_deletion_time = time_of_expiration + datetime.timedelta(days=1)
    with freeze_time(valid_deletion_time):
        delete_expired_orders_task()
        data = order_query(e2e_staff_api_client, order_id)

    assert data is None
