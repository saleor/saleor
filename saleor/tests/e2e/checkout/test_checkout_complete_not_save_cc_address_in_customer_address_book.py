import pytest

from .. import ADDRESS_DE
from ..account.utils import get_own_data
from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assert_address_data, assign_permissions
from ..warehouse.utils import update_warehouse
from .utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    raw_checkout_shipping_address_update,
)


@pytest.mark.e2e
def test_checkout_complete_not_save_cc_address_in_customer_address_book_CORE_0130(
    e2e_staff_api_client,
    e2e_logged_api_client,
    permission_manage_product_types_and_attributes,
    shop_permissions,
):
    # Before
    permissions = [
        permission_manage_product_types_and_attributes,
        *shop_permissions,
    ]

    assign_permissions(e2e_staff_api_client, permissions)

    shop_data = prepare_default_shop(e2e_staff_api_client)
    channel_id = shop_data["channel"]["id"]
    channel_slug = shop_data["channel"]["slug"]
    warehouse_id = shop_data["warehouse"]["id"]
    update_warehouse(
        e2e_staff_api_client,
        warehouse_id,
        is_private=False,
        click_and_collect_option="LOCAL",
    )
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

    # Step 1 - Create checkout.
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    billing_address = ADDRESS_DE
    shipping_address = {
        "firstName": "John",
        "lastName": "Muller",
        "companyName": "Saleor Commerce CZ",
        "streetAddress1": "Sluneční 1396",
        "streetAddress2": "",
        "postalCode": "74784",
        "country": "CZ",
        "city": "Melc",
        "phone": "+420722274643",
        "countryArea": "",
    }
    checkout_data = checkout_create(
        e2e_logged_api_client,
        lines,
        channel_slug,
        email=None,
        billing_address=billing_address,
        shipping_address=shipping_address,
        save_billing_address=True,
        save_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    expected_email = e2e_logged_api_client.user.email
    assert checkout_data["email"] == expected_email
    assert checkout_data["user"]["email"] == expected_email
    assert checkout_data["isShippingRequired"] is True
    checkout_shipping_address = checkout_data["shippingAddress"]

    collection_point = checkout_data["availableCollectionPoints"][0]
    assert collection_point["id"] == warehouse_id
    assert collection_point["isPrivate"] is False
    assert collection_point["clickAndCollectOption"] == "LOCAL"

    # Step 2 - Assign delivery method
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        collection_point["id"],
    )
    assert checkout_data["deliveryMethod"]["id"] == warehouse_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]
    # Ensure the address has been changed
    assert (
        checkout_data["shippingAddress"]["streetAddress1"]
        != checkout_shipping_address["streetAddress1"]
    )

    # Step 3 - Try to change the shipping address and set the save_shipping_address value
    checkout_data = raw_checkout_shipping_address_update(
        e2e_logged_api_client, checkout_id, save_address=True
    )

    assert len(checkout_data["errors"]) == 1
    assert checkout_data["errors"][0]["field"] == "shippingAddress"
    assert checkout_data["errors"][0]["code"] == "SHIPPING_CHANGE_FORBIDDEN"

    # Step 3 - Create dummy payment
    checkout_dummy_payment_create(
        e2e_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 4 - Complete the checkout
    order_data = checkout_complete(
        e2e_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["deliveryMethod"]["id"] == warehouse_id
    assert order_data["shippingAddress"]
    assert order_data["billingAddress"]
    assert_address_data(order_data["billingAddress"], billing_address)

    # Step 5 - Verify the user address book
    me = get_own_data(e2e_logged_api_client)

    assert len(me["addresses"]) == 1
    address = me["addresses"][0]
    assert_address_data(address, billing_address)
    assert address["id"] != order_data["billingAddress"]["id"]
    assert address["id"] != order_data["shippingAddress"]["id"]
