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
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse, update_warehouse
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
    permission_manage_product_types_and_attributes,
):
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
    ]

    assign_permissions(e2e_staff_api_client, permissions)
    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    update_warehouse(
        e2e_staff_api_client,
        warehouse_data["id"],
        is_private=False,
        click_and_collect_option="LOCAL",
    )
    channel_data = create_channel(e2e_staff_api_client, warehouse_data["id"])
    channel_id = channel_data["id"]
    channel_slug = channel_data["slug"]

    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(
        e2e_staff_api_client,
    )
    category_id = category_data["id"]

    product_data = create_product(
        e2e_staff_api_client,
        product_type_id,
        category_id,
    )
    product_id = product_data["id"]

    create_product_channel_listing(e2e_staff_api_client, product_id, channel_id)

    stocks = [
        {
            "warehouse": warehouse_data["id"],
            "quantity": 5,
        }
    ]
    variant_data = create_product_variant(
        e2e_staff_api_client, product_id, stocks=stocks
    )
    variant_id = variant_data["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        variant_id,
        channel_id,
    )

    return variant_id, channel_slug, warehouse_id


@pytest.mark.e2e
def test_unlogged_customer_buy_by_click_and_collect(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
):
    # Before
    variant_id, channel_slug, warehouse_id = prepare_product(
        e2e_staff_api_client,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
    )

    # Step 1 - Create checkout and check collection point
    lines = [
        {"variantId": variant_id, "quantity": 1},
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

    collection_point = checkout_data["availableCollectionPoints"][0]
    assert collection_point["id"] == warehouse_id
    assert collection_point["isPrivate"] is False
    assert collection_point["clickAndCollectOption"] == "LOCAL"

    # Step 2 - Assign delivery method
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client, checkout_id, collection_point["id"]
    )
    assert checkout_data["deliveryMethod"]["id"] == warehouse_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 3 - Create dummy payment
    checkout_dummy_payment_create(
        e2e_not_logged_api_client, checkout_id, total_gross_amount
    )

    # Step 4 - Complete checkout and verify created order
    order_data = checkout_complete(e2e_not_logged_api_client, checkout_id)
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["deliveryMethod"]["id"] == warehouse_id
