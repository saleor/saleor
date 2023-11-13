import pytest

from ..product.utils.preparing_product import prepare_product
from ..shop.utils import prepare_shop
from ..utils import assign_permissions
from .utils import (
    checkout_create,
    checkout_delivery_method_update,
    raw_checkout_complete,
)


@pytest.mark.e2e
def test_should_be_able_to_create_order_with_no_payment_CORE_0111(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_taxes,
    permission_manage_settings,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
        permission_manage_taxes,
        permission_manage_settings,
    ]
    assign_permissions(e2e_staff_api_client, permissions)
    shop_data = prepare_shop(
        e2e_staff_api_client,
        allow_unpaid_orders=True,
    )
    warehouse_id = shop_data["warehouse_id"]
    channel_id = shop_data["channel_id"]
    channel_slug = shop_data["channel_slug"]
    shipping_method_id = shop_data["shipping_method_id"]

    variant_price = 10

    (
        _product_id,
        product_variant_id,
        _product_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        variant_price,
    )

    assert shipping_method_id is not None

    # Step 1 - Create checkout.
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
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

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["deliveryMethod"] is None
    assert checkout_data["shippingMethod"] is None
    shipping_method_id = checkout_data["shippingMethods"][0]["id"]

    # Step 2 - Set shipping address and DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_staff_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 3 - Checkout complete results in the order creation
    data = raw_checkout_complete(
        e2e_staff_api_client,
        checkout_id,
    )
    order_data = data["order"]
    assert order_data is not None
    assert order_data["id"] is not None
    assert order_data["isShippingRequired"] is True
    assert order_data["paymentStatus"] == "NOT_CHARGED"
    assert order_data["status"] == "UNCONFIRMED"
    assert order_data["isPaid"] is False

    errors = data["errors"]
    assert errors == []
