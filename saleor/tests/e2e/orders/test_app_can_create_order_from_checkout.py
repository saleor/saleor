import pytest

from ..checkout.utils import checkout_create, checkout_delivery_method_update
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from .utils import order_create_from_checkout


@pytest.mark.e2e
def test_app_can_create_order_from_checkout_CORE_0215(
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
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
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
    order_data = order_create_from_checkout(e2e_app_api_client, checkout_id)
    order_id = order_data["order"]["id"]
    assert order_id is not None
    assert order_data["order"]["status"] == "UNCONFIRMED"
    assert order_data["order"]["paymentStatus"] == "NOT_CHARGED"
