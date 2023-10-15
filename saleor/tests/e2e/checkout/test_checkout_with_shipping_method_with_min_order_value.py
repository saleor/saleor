import base64

import pytest

from ..channel.utils import create_channel
from ..product.utils import (
    create_product_variant,
    create_product_variant_channel_listing,
)
from ..product.utils.preparing_product import prepare_product
from ..shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse
from .utils import checkout_create, checkout_delivery_method_update


#  Please note: decoding won't be necessary once
# https://github.com/saleor/saleor/issues/13675 is fixed
def decode_base64_and_get_last_3_chars(encoded_string):
    base64_bytes = encoded_string.encode("ascii")
    decoded_bytes = base64.b64decode(base64_bytes)
    decoded_string = decoded_bytes.decode("ascii")
    return decoded_string[-2:]


def prepare_shop_with_shipping_method_with_min_order_value(
    e2e_staff_api_client,
):
    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    channel_slug = "test"
    warehouse_ids = [warehouse_id]
    channel_data = create_channel(
        e2e_staff_api_client,
        slug=channel_slug,
        warehouse_ids=warehouse_ids,
    )
    channel_id = channel_data["id"]
    channel_ids = [channel_id]
    shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=warehouse_ids,
        channel_ids=channel_ids,
    )
    shipping_zone_id = shipping_zone_data["id"]

    return (
        warehouse_id,
        channel_id,
        channel_slug,
        shipping_zone_id,
    )


@pytest.mark.e2e
def test_checkout_with_shipping_method_with_min_order_value_CORE_0501(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_checkouts,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_shipping,
        permission_manage_checkouts,
    ]

    assign_permissions(e2e_staff_api_client, permissions)
    (
        warehouse_id,
        channel_id,
        channel_slug,
        shipping_zone_id,
    ) = prepare_shop_with_shipping_method_with_min_order_value(
        e2e_staff_api_client,
    )

    first_variant_price = 25

    (
        product_id,
        first_product_variant_id,
        first_variant_price,
    ) = prepare_product(
        e2e_staff_api_client,
        warehouse_id,
        channel_id,
        first_variant_price,
    )

    variant_data = create_product_variant(
        e2e_staff_api_client,
        product_id,
        stocks=[
            {
                "warehouse": warehouse_id,
                "quantity": 20,
            }
        ],
    )
    second_product_variant_id = variant_data["id"]

    second_variant_price = 15
    create_product_variant_channel_listing(
        e2e_staff_api_client,
        second_product_variant_id,
        channel_id,
        second_variant_price,
    )

    # Step 1 - Create shipping method with minimal order value
    minimum_order_price = 20.0
    shipping_method_data = create_shipping_method(
        e2e_staff_api_client, shipping_zone_id
    )
    shipping_method_id = shipping_method_data["id"]
    data = create_shipping_method_channel_listing(
        e2e_staff_api_client,
        shipping_method_id,
        channel_id,
        price="5.00",
        minimumOrderPrice=minimum_order_price,
    )
    shipping_method_min_order_value = data["channelListings"][0]["minimumOrderPrice"][
        "amount"
    ]
    assert shipping_method_min_order_value == minimum_order_price

    # Step 2 - Create checkout with the first product variant
    lines = [
        {
            "variantId": first_product_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="jon.doe@saleor.io",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    checkout_shipping_method = checkout_data["shippingMethods"][0]["id"]
    decoded_checkout_shipping_method = decode_base64_and_get_last_3_chars(
        checkout_shipping_method
    )
    decoded_shipping_method = decode_base64_and_get_last_3_chars(shipping_method_id)
    assert decoded_checkout_shipping_method == decoded_shipping_method

    # Step 2 - Set DeliveryMethod for the checkout with the first product variant
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        checkout_shipping_method,
    )
    assert checkout_data["deliveryMethod"]["id"] == checkout_shipping_method

    # Step 3 - Create checkout with the second product variant
    lines = [
        {
            "variantId": second_product_variant_id,
            "quantity": 1,
        },
    ]
    checkout_data = checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="jon.doe@saleor.io",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )
    checkout_id = checkout_data["id"]

    assert checkout_data["isShippingRequired"] is True
    assert checkout_data["shippingMethods"] == []
