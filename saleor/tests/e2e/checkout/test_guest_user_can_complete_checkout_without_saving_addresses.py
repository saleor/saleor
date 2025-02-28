import pytest

from .. import ADDRESS_DE
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assert_address_data, assign_permissions
from .utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)


@pytest.mark.e2e
def test_guest_user_can_complete_checkout_without_saving_addresses_CORE_0129(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
    permission_manage_orders,
    permission_manage_checkouts,
    permission_manage_users,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
        permission_manage_users,
        *shop_permissions,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

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

    # Step 1 - Create checkout
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    # use different address for shipping and billing
    billing_address = ADDRESS_DE
    email = "test0129@example.com"
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email=email,
        billing_address=billing_address,
        save_billing_address=True,
        save_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["email"] == email
    assert checkout_data["user"] is None
    assert checkout_data["isShippingRequired"] is True
    checkout_billing_address = checkout_data["billingAddress"]
    checkout_shipping_address = checkout_data["shippingAddress"]

    # Step 2 - Set DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 3 - Create payment for checkout
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 4 - Complete checkout.
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["isShippingRequired"] is True
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["deliveryMethod"]["id"] == shipping_method_id
    assert order_data["shippingAddress"]
    assert order_data["billingAddress"]
    checkout_billing_address["country"] = checkout_billing_address["country"]["code"]
    checkout_shipping_address["country"] = checkout_shipping_address["country"]["code"]
    assert_address_data(order_data["shippingAddress"], checkout_shipping_address)
    assert_address_data(order_data["billingAddress"], checkout_billing_address)
