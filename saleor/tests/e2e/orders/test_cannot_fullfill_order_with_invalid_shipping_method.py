import base64

import pytest

from .. import DEFAULT_ADDRESS
from ..channel.utils import create_channel
from ..product.utils.preparing_product import prepare_product
from ..shipping_zone.utils import (
    create_shipping_method,
    create_shipping_method_channel_listing,
    create_shipping_zone,
)
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse
from .utils.draft_order_complete import raw_draft_order_complete
from .utils.draft_order_create import draft_order_create
from .utils.draft_order_update import draft_order_update
from .utils.order_lines_create import order_lines_create
from .utils.order_query import order_query

#  Please note: decoding won't be necessary once
# https://github.com/saleor/saleor/issues/13675 is fixed


def decode_base64_and_get_last_2_chars(encoded_string):
    base64_bytes = encoded_string.encode("ascii")
    decoded_bytes = base64.b64decode(base64_bytes)
    decoded_string = decoded_bytes.decode("ascii")
    return decoded_string[-2:]


first_address = DEFAULT_ADDRESS


def prepare_shipping_methods(
    e2e_staff_api_client,
):
    warehouse_data = create_warehouse(
        e2e_staff_api_client,
        name="Warehouse 1",
        slug="warehouse-1",
        address=first_address,
    )
    warehouse_id = warehouse_data["id"]

    channel_data = create_channel(
        e2e_staff_api_client,
        warehouse_ids=[warehouse_id],
    )
    channel_id = channel_data["id"]

    first_shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=[warehouse_id],
        channel_ids=[channel_id],
    )
    first_shipping_zone_id = first_shipping_zone_data["id"]

    first_shipping_method_data = create_shipping_method(
        e2e_staff_api_client,
        first_shipping_zone_id,
        name="First shipping method",
        type="PRICE",
    )
    first_shipping_method_id = first_shipping_method_data["id"]

    create_shipping_method_channel_listing(
        e2e_staff_api_client,
        first_shipping_method_id,
        channel_id,
    )

    second_shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        name="second shipping zone",
        countries="PL",
        warehouse_ids=[warehouse_id],
        channel_ids=[channel_id],
    )
    second_shipping_zone_id = second_shipping_zone_data["id"]

    second_shipping_method_data = create_shipping_method(
        e2e_staff_api_client,
        second_shipping_zone_id,
        name="Second shipping method",
        type="PRICE",
    )
    second_shipping_method_id = second_shipping_method_data["id"]

    create_shipping_method_channel_listing(
        e2e_staff_api_client,
        second_shipping_method_id,
        channel_id,
    )

    return (
        warehouse_id,
        channel_id,
        first_shipping_method_id,
        second_shipping_method_id,
    )


@pytest.mark.e2e
def test_cannot_fullfill_order_with_invalid_shipping_method_core_0203(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_orders,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    (
        warehouse_id,
        channel_id,
        first_shipping_method_id,
        second_shipping_method_id,
    ) = prepare_shipping_methods(e2e_staff_api_client)

    price = 2
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

    # Step 1 - Create draft order and add lines
    draft_order_input = {
        "channelId": channel_id,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        draft_order_input,
    )
    order_id = data["order"]["id"]
    assert order_id is not None

    lines = [{"variantId": product_variant_id, "quantity": 1}]
    order_lines = order_lines_create(
        e2e_staff_api_client,
        order_id,
        lines,
    )
    order_product_variant_id = order_lines["order"]["lines"][0]["variant"]["id"]
    assert order_product_variant_id == product_variant_id

    # Step 2 - Update order's shipping method
    input = {
        "shippingMethod": first_shipping_method_id,
        "shippingAddress": first_address,
        "billingAddress": first_address,
    }
    draft_order = draft_order_update(
        e2e_staff_api_client,
        order_id,
        input,
    )
    order_shipping_id = draft_order["order"]["deliveryMethod"]["id"]
    first_shipping_id_number = decode_base64_and_get_last_2_chars(
        first_shipping_method_id
    )
    shipping_id_number = decode_base64_and_get_last_2_chars(order_shipping_id)

    assert shipping_id_number == first_shipping_id_number

    # Step 3 - Update order's shipping address for country PL
    second_address = {
        "firstName": "Jan",
        "lastName": "Kowalski",
        "phone": "+48123456787",
        "companyName": "Saleor PL",
        "country": "PL",
        "countryArea": "",
        "city": "WROCLAW",
        "postalCode": "53-346",
        "streetAddress1": "Smolna",
        "streetAddress2": "13/1",
    }
    update_input = {"shippingAddress": second_address}
    draft_update = draft_order_update(
        e2e_staff_api_client,
        order_id,
        update_input,
    )
    draft_order_shipping_id = draft_update["order"]["deliveryMethod"]["id"]
    assert draft_order_shipping_id == order_shipping_id

    # Step 4 - Complete the order and check that 2nd shipping method is now available
    order_complete = raw_draft_order_complete(
        e2e_staff_api_client,
        order_id,
    )
    assert (
        order_complete["errors"][0]["message"]
        == "Shipping method is not valid for chosen shipping address"
    )
    order_details = order_query(
        e2e_staff_api_client,
        order_id,
    )
    order_shipping_method = order_details["availableShippingMethods"][0]["id"]
    second_shipping_id_number = decode_base64_and_get_last_2_chars(
        second_shipping_method_id
    )
    order_shipping_method_number = decode_base64_and_get_last_2_chars(
        order_shipping_method
    )
    assert order_shipping_method_number == second_shipping_id_number
