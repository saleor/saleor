import pytest

from ..channel.utils import create_channel
from ..product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
)
from ..shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse
from .utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)


def prepare_product(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    channel_slug,
):
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]

    warehouse_ids = [warehouse_id]
    channel_data = create_channel(
        e2e_staff_api_client, slug=channel_slug, warehouse_ids=warehouse_ids
    )
    channel_id = channel_data["id"]

    channel_ids = [channel_id]
    shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=warehouse_ids,
        channel_ids=channel_ids,
    )
    shipping_zone_id = shipping_zone_data["id"]

    shipping_method_data = create_shipping_method(
        e2e_staff_api_client, shipping_zone_id
    )
    shipping_method_id = shipping_method_data["id"]

    create_shipping_method_channel_listing(
        e2e_staff_api_client, shipping_method_id, channel_id
    )

    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    product_data = create_product(e2e_staff_api_client, product_type_id, category_id)
    product_id = product_data["id"]

    create_product_channel_listing(e2e_staff_api_client, product_id, channel_id)

    stocks = [
        {
            "warehouse": warehouse_id,
            "quantity": 5,
        }
    ]
    product_variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=stocks,
    )
    product_variant_id = product_variant_data["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        product_variant_id,
        channel_id,
    )
    return product_variant_id


@pytest.mark.e2e
def test_process_checkout_with_physical_product(
    e2e_staff_api_client,
    e2e_logged_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
):
    # Before
    channel_slug = "test-channel"
    product_variant_id = prepare_product(
        e2e_staff_api_client,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        channel_slug,
    )

    # Step 1 - Login as existing customer.

    # This step is implemented automatically by using a proper
    # API client(eg. e2e_staff_api_client, e2e_not_logged_api_client,
    # e2e_logged_api_client).

    # Step 2 - Create checkout.
    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = checkout_create(
        e2e_logged_api_client,
        lines,
        channel_slug,
        email=None,
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    expected_email = e2e_logged_api_client.user.email
    assert checkout_data["email"] == expected_email
    assert checkout_data["user"]["email"] == expected_email
    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["shippingMethods"] != []
    shipping_method_id = checkout_data["shippingMethods"][0]["id"]

    # Step 3 - Set DeliveryMethod for checkout.
    checkout_data = checkout_delivery_method_update(
        e2e_logged_api_client,
        checkout_id,
        shipping_method_id,
    )
    assert checkout_data["deliveryMethod"]["id"] == shipping_method_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 4 - Create payment for checkout.
    checkout_dummy_payment_create(
        e2e_logged_api_client, checkout_id, total_gross_amount
    )

    # Step 5 - Complete checkout.
    order_data = checkout_complete(e2e_logged_api_client, checkout_id)
    assert order_data["isShippingRequired"] is True
    assert order_data["user"]["email"] == expected_email
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["deliveryMethod"]["id"] == shipping_method_id
