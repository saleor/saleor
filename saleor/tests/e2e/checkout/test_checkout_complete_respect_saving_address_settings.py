import pytest

from .. import ADDRESS_DE
from ..account.utils import get_own_data
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
def test_respect_saving_address_setting_in_checkout_process_CORE_0132(
    e2e_staff_api_client,
    e2e_logged_api_client,
    shop_permissions,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_users,
):
    # Before
    permissions = [
        *shop_permissions,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_users,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    shipping_method_id = shop_data["shipping_method"]["id"]

    product_price = 10
    _product_id, product_variant_id, _product_variant_price = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        product_price,
    )

    # Step 1 - Create checkout.
    # use different address for shipping and billing
    billing_address = ADDRESS_DE
    shipping_address = {
        "firstName": "John",
        "lastName": "Muller",
        "companyName": "Saleor Commerce USA",
        "streetAddress1": "2595 Shinn Street",
        "streetAddress2": "",
        "postalCode": "10281",
        "country": "US",
        "city": "New York",
        "phone": "+19175563216",
        "countryArea": "NY",
    }
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    user = e2e_logged_api_client.user
    checkout_data = checkout_create(
        e2e_logged_api_client,
        lines,
        channel_slug,
        billing_address=billing_address,
        shipping_address=shipping_address,
        save_billing_address=False,
        save_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["deliveryMethod"] is None
    assert checkout_data["shippingMethod"] is None
    assert checkout_data["shippingAddress"]
    assert checkout_data["billingAddress"]
    assert (
        checkout_data["shippingAddress"]["streetAddress1"]
        == shipping_address["streetAddress1"]
    )
    assert (
        checkout_data["billingAddress"]["streetAddress1"]
        == billing_address["streetAddress1"]
    )

    # Step 2 - Set shipping address and DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 3 - Create dummy payment
    checkout_dummy_payment_create(
        e2e_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 4 - Checkout complete results in the order creation
    order_data = checkout_complete(
        e2e_logged_api_client,
        checkout_id,
    )
    assert order_data["isShippingRequired"] is True
    assert order_data["paymentStatus"] == "FULLY_CHARGED"
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["isPaid"] is True
    order_billing_address = order_data["billingAddress"]
    assert order_billing_address
    order_shipping_address = order_data["shippingAddress"]
    assert order_shipping_address
    assert_address_data(order_shipping_address, shipping_address)
    assert_address_data(order_billing_address, billing_address)
    assert order_data["userEmail"] == user.email

    # Step 5 - Verify the user address book
    user = get_own_data(e2e_logged_api_client)

    assert len(user["addresses"]) == 1
    address = user["addresses"][0]
    assert_address_data(address, shipping_address)
    assert address["id"] != order_billing_address["id"]
    assert address["id"] != order_shipping_address["id"]
