import pytest

from ..channel.utils import create_channel
from ..product.utils import (
    create_category,
    create_product,
    create_product_channel_listing,
    create_product_type,
    create_product_variant_channel_listing,
    raw_create_product_variant,
)
from ..shipping_zone.utils import create_shipping_zone
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse
from .utils import raw_checkout_create


def prepare_product(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
):
    permissions = [
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_shipping,
    ]

    assign_permissions(e2e_staff_api_client, permissions)
    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]

    channel_data = create_channel(e2e_staff_api_client, warehouse_data["id"])
    channel_id = channel_data["id"]
    channel_slug = channel_data["slug"]

    create_shipping_zone(
        e2e_staff_api_client,
        warehouse_ids=[warehouse_id],
        channel_ids=[channel_id],
    )

    product_type_data = create_product_type(
        e2e_staff_api_client,
        is_shipping_required=True,
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
    variant_data = raw_create_product_variant(
        e2e_staff_api_client, product_id, stocks=stocks
    )
    variant_id = variant_data["productVariant"]["id"]

    create_product_variant_channel_listing(
        e2e_staff_api_client,
        variant_id,
        channel_id,
    )

    return variant_id, channel_slug


@pytest.mark.e2e
def test_unlogged_customer_cannot_buy_product_in_quantity_grater_than_stock_core_0107(
    e2e_not_logged_api_client,
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    permission_manage_shipping,
):
    # Before
    variant_id, channel_slug = prepare_product(
        e2e_staff_api_client,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        permission_manage_shipping,
    )
    # Step 1 - Create checkout with product quantity greater than the available stock
    lines = [
        {"variantId": variant_id, "quantity": 10},
    ]
    checkout_data = raw_checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="jon.doe@saleor.io",
        set_default_billing_address=True,
        set_default_shipping_address=True,
    )

    errors = checkout_data["errors"]
    assert errors[0]["code"] == "INSUFFICIENT_STOCK"
    assert errors[0]["field"] == "quantity"
    assert (
        errors[0]["message"]
        == "Could not add items Test product variant. Only 5 remaining in stock."
    )
