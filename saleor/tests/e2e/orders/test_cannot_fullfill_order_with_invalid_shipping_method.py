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

first_address = DEFAULT_ADDRESS


def prepare_shops(
    e2e_staff_api_client,
):
    first_warehouse_data = create_warehouse(
        e2e_staff_api_client,
        name="Warehouse 1",
        slug="warehouse-1",
        address=first_address,
    )
    first_warehouse_id = first_warehouse_data["id"]

    first_channel_data = create_channel(
        e2e_staff_api_client, slug="channel-1", warehouse_ids=[first_warehouse_id]
    )
    first_channel_id = first_channel_data["id"]

    first_shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=[first_warehouse_id],
        channel_ids=[first_channel_id],
    )
    first_shipping_zone_id = first_shipping_zone_data["id"]

    first_shipping_method_data = create_shipping_method(
        e2e_staff_api_client, first_shipping_zone_id
    )
    first_shipping_method_id = first_shipping_method_data["id"]

    create_shipping_method_channel_listing(
        e2e_staff_api_client, first_shipping_method_id, first_channel_id
    )

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
    second_warehouse_data = create_warehouse(
        e2e_staff_api_client,
        name="Warehouse 2",
        slug="warehouse-2",
        address=second_address,
    )
    second_warehouse_id = second_warehouse_data["id"]

    second_channel_data = create_channel(
        e2e_staff_api_client, slug="channel-2", warehouse_ids=[second_warehouse_id]
    )
    second_channel_id = second_channel_data["id"]

    second_shipping_zone_data = create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=[second_warehouse_id],
        channel_ids=[second_channel_id],
    )
    second_shipping_zone_id = second_shipping_zone_data["id"]

    second_shipping_method_data = create_shipping_method(
        e2e_staff_api_client, second_shipping_zone_id
    )
    second_shipping_method_id = second_shipping_method_data["id"]

    create_shipping_method_channel_listing(
        e2e_staff_api_client, second_shipping_method_id, second_channel_id
    )

    return (
        first_warehouse_id,
        first_channel_id,
        first_shipping_method_id,
        second_address,
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
        first_warehouse_id,
        first_channel_id,
        first_shipping_method_id,
        second_address,
    ) = prepare_shops(e2e_staff_api_client)

    price = 2
    (
        _,
        result_product_variant_id,
        _,
    ) = prepare_product(
        e2e_staff_api_client, first_warehouse_id, first_channel_id, price
    )

    # Step 1 - Create draft order and add lines
    draft_order_input = {
        "channelId": first_channel_id,
    }
    data = draft_order_create(
        e2e_staff_api_client,
        draft_order_input,
    )
    order_id = data["order"]["id"]
    assert order_id is not None

    lines = [{"variantId": result_product_variant_id, "quantity": 1}]
    order_lines = order_lines_create(e2e_staff_api_client, order_id, lines)
    order_product_variant_id = order_lines["order"]["lines"][0]["variant"]["id"]
    assert order_product_variant_id == result_product_variant_id

    # # Step 2 - Update order's shipping method
    input = {
        "shippingMethod": first_shipping_method_id,
        "shippingAddress": first_address,
        "billingAddress": first_address,
    }
    draft_order = draft_order_update(e2e_staff_api_client, order_id, input)
    order_shipping_id = draft_order["order"]["deliveryMethod"]["id"]
    assert order_shipping_id is not None

    # # Step 3 - Update order's shipping address for country PL
    update_input = {"shippingAddress": second_address}
    draft_update = draft_order_update(e2e_staff_api_client, order_id, update_input)
    draft_order_shipping_id = draft_update["order"]["deliveryMethod"]["id"]
    assert draft_order_shipping_id == order_shipping_id
    # assert draft_update["order"]["shippingAddress"] == second_address

    # Step 4 - Complete the order
    order = raw_draft_order_complete(e2e_staff_api_client, order_id)
    assert (
        order["errors"][0]["message"]
        == "Shipping method is not valid for chosen shipping address"
    )
