import pytest

from .. import ADDRESS_DE, DEFAULT_ADDRESS
from ..account.utils import get_own_data, get_user
from ..checkout.utils import (
    checkout_create,
    checkout_delivery_method_update,
    raw_checkout_complete,
)
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_shop
from ..utils import assert_address_data, assign_permissions
from .utils import (
    order_update,
)


@pytest.mark.e2e
def test_changing_order_address_do_not_influence_customer_address_CORE_0257(
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

    product_price = 10
    shipping_price = 10
    tax_settings = {
        "charge_taxes": True,
        "tax_calculation_strategy": "FLAT_RATES",
        "display_gross_prices": False,
        "prices_entered_with_tax": True,
    }

    shop_data, _tax_config = prepare_shop(
        e2e_staff_api_client,
        channels=[
            {
                "shipping_zones": [
                    {
                        "countries": ["US"],
                        "shipping_methods": [
                            {
                                "name": "us shipping zone",
                                "add_channels": {
                                    "price": shipping_price,
                                },
                            }
                        ],
                    }
                ],
                "order_settings": {
                    "automaticallyConfirmAllNewOrders": False,
                    "allowUnpaidOrders": True,
                },
            }
        ],
        tax_settings=tax_settings,
    )
    channel_id = shop_data[0]["id"]
    channel_slug = shop_data[0]["slug"]
    warehouse_id = shop_data[0]["warehouse_id"]
    shipping_method_id = shop_data[0]["shipping_zones"][0]["shipping_methods"][0]["id"]

    _product_id, product_variant_id, _product_variant_price = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        product_price,
    )

    # Step 1 - Create checkout.
    # use different address for shipping and billing
    billing_address = ADDRESS_DE
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    user = e2e_logged_api_client.user
    checkout_data = checkout_create(
        e2e_logged_api_client,
        lines,
        channel_slug,
        billing_address=billing_address,
        save_billing_address=True,
        save_shipping_address=False,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["deliveryMethod"] is None
    assert checkout_data["shippingMethod"] is None
    assert checkout_data["shippingAddress"]
    assert checkout_data["billingAddress"]
    assert_address_data(checkout_data["shippingAddress"], DEFAULT_ADDRESS)
    assert_address_data(checkout_data["billingAddress"], billing_address)

    # Step 2 - Set shipping address and DeliveryMethod for checkout
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id

    # Step 3 - Checkout complete results in the order creation
    data = raw_checkout_complete(
        e2e_logged_api_client,
        checkout_id,
    )
    order_data = data["order"]
    order_id = order_data["id"]
    assert order_data is not None
    assert order_data["id"] is not None
    assert order_data["isShippingRequired"] is True
    assert order_data["paymentStatus"] == "NOT_CHARGED"
    assert order_data["status"] == "UNCONFIRMED"
    assert order_data["isPaid"] is False
    order_billing_address = order_data["billingAddress"]
    assert order_billing_address
    order_shipping_address = order_data["shippingAddress"]
    assert order_shipping_address
    assert order_data["userEmail"] == user.email

    # Step 5 - Verify the user address book
    user = get_own_data(e2e_logged_api_client)

    assert len(user["addresses"]) == 1
    address = user["addresses"][0]
    order_billing_address["country"] = order_billing_address["country"]["code"]
    assert_address_data(address, order_billing_address)
    assert address["id"] != order_billing_address["id"]
    user_id = user["id"]

    # Step 6 - Update order's shipping address
    billing_address["streetAddress1"] = "New street 12"
    updated_order_data = order_update(
        e2e_staff_api_client,
        order_id,
        {"billingAddress": billing_address},
    )

    assert (
        updated_order_data["order"]["billingAddress"]["streetAddress1"]
        == billing_address["streetAddress1"]
    )

    # Step 7 - Verify if the user address stay unchanged
    user = get_user(e2e_staff_api_client, user_id)
    assert len(user["addresses"]) == 1
    address = user["addresses"][0]
    assert_address_data(address, order_billing_address)
