import pytest

from ..channel.utils import create_channel
from ..orders.utils.draft_order import draft_order_create
from ..orders.utils.order_lines import order_lines_create
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
from .utils import checkout_create_from_order


def prepare_product(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_shipping,
    permission_manage_product_types_and_attributes,
    permission_manage_orders,
    permission_manage_checkouts,
    channel_slug,
):
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_shipping,
        permission_manage_product_types_and_attributes,
        permission_manage_orders,
        permission_manage_checkouts,
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
    data = draft_order_create(
        e2e_staff_api_client,
        channel_id,
    )

    order_id = data["order"]["id"]
    order_lines = [{"variantId": product_variant_id, "quantity": 1, "price": 100}]
    order_data = order_lines_create(e2e_staff_api_client, order_id, order_lines)
    order_product_variant_id = order_data["order"]["lines"][0]["variant"]
    order_product_quantity = order_data["order"]["lines"][0]["quantity"]

    return (
        order_id,
        order_product_variant_id,
        order_product_quantity,
    )


@pytest.mark.e2e
def test_checkout_create_from_order_core_0104(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
    permission_manage_orders,
    permission_manage_checkouts,
):
    # Before
    (
        order_id,
        order_product_variant_id,
        order_product_quantity,
    ) = prepare_product(
        e2e_staff_api_client,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_shipping,
        permission_manage_orders,
        permission_manage_checkouts,
        channel_slug="test",
    )

    # Step 1 - Create checkout from order

    checkout_data = checkout_create_from_order(e2e_staff_api_client, order_id)
    checkout_id = checkout_data["checkout"]["id"]
    assert checkout_id is not None
    errors = checkout_data["errors"]
    assert errors == []
    checkout_lines = checkout_data["checkout"]["lines"]
    assert checkout_lines != []

    checkout_product_variant_id = checkout_lines[0]["variant"]["id"]
    checkout_product_quantity = checkout_lines[0]["quantity"]
    order_product_variant_id_value = order_product_variant_id["id"]

    assert checkout_product_variant_id == order_product_variant_id_value
    assert checkout_product_quantity == order_product_quantity
