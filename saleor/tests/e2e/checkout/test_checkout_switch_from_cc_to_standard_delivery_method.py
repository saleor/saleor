import pytest

from ..product.utils.preparing_product import prepare_product
from ..shop.utils.preparing_shop import prepare_default_shop
from ..utils import assign_permissions
from ..warehouse.utils import update_warehouse
from .utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
    checkout_shipping_address_update,
)


@pytest.mark.e2e
def test_checkout_switch_from_cc_to_standard_delivery_method_CORE_0133(
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
    shipping_method_id = shop_data["shipping_method"]["id"]
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
    checkout_data = checkout_create(
        e2e_logged_api_client,
        lines,
        channel_slug,
        email=None,
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

    # Step 2 - Assign CC as a delivery method
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        collection_point["id"],
    )
    assert checkout_data["deliveryMethod"]["id"] == warehouse_id
    # Ensure the address has been changed
    assert (
        checkout_data["shippingAddress"]["streetAddress1"]
        != checkout_shipping_address["streetAddress1"]
    )

    # Step 3 - Change the delivery method to standard shipping method
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    assert checkout_data["shippingAddress"] is None
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 4 - Update shipping address
    checkout_data = checkout_shipping_address_update(e2e_logged_api_client, checkout_id)
    assert checkout_data["shippingAddress"]

    # Step 5 - Create payment
    checkout_dummy_payment_create(
        e2e_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 6 - Complete the checkout
    order_data = checkout_complete(
        e2e_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["deliveryMethod"]["id"] == shipping_method_id
