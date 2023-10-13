import pytest

from ..channel.utils import create_channel
from ..product.utils.preparing_product import prepare_product
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse, update_warehouse
from .utils import (
    checkout_complete,
    checkout_create,
    checkout_delivery_method_update,
    checkout_dummy_payment_create,
)


def prepare_shop_click_and_collect(
    e2e_staff_api_client,
):
    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    update_warehouse(
        e2e_staff_api_client,
        warehouse_data["id"],
        is_private=False,
        click_and_collect_option="LOCAL",
    )
    channel_data = create_channel(
        e2e_staff_api_client,
        warehouse_data["id"],
    )
    channel_id = channel_data["id"]
    channel_slug = channel_data["slug"]

    return channel_id, channel_slug, warehouse_id


@pytest.mark.e2e
def test_unlogged_customer_buy_by_click_and_collect_CORE_0105(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
):
    # Before
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
    ]

    assign_permissions(e2e_staff_api_client, permissions)
    (
        channel_id,
        channel_slug,
        warehouse_id,
    ) = prepare_shop_click_and_collect(
        e2e_staff_api_client,
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

    # Step 1 - Create checkout and check collection point
    lines = [
        {
            "variantId": product_variant_id,
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

    collection_point = checkout_data["availableCollectionPoints"][0]
    assert collection_point["id"] == warehouse_id
    assert collection_point["isPrivate"] is False
    assert collection_point["clickAndCollectOption"] == "LOCAL"

    # Step 2 - Assign delivery method
    checkout_data = checkout_delivery_method_update(
        e2e_not_logged_api_client,
        checkout_id,
        collection_point["id"],
    )
    assert checkout_data["deliveryMethod"]["id"] == warehouse_id
    total_gross_amount = checkout_data["totalPrice"]["gross"]["amount"]

    # Step 3 - Create dummy payment
    checkout_dummy_payment_create(
        e2e_not_logged_api_client,
        checkout_id,
        total_gross_amount,
    )

    # Step 4 - Complete checkout and verify created order
    order_data = checkout_complete(
        e2e_not_logged_api_client,
        checkout_id,
    )
    assert order_data["status"] == "UNFULFILLED"
    assert order_data["total"]["gross"]["amount"] == total_gross_amount
    assert order_data["deliveryMethod"]["id"] == warehouse_id
