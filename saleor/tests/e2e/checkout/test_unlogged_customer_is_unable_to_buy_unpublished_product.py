import pytest

from ..channel.utils import create_channel
from ..product.utils import (
    create_category,
    create_product,
    create_product_type,
    create_product_variant,
    create_product_variant_channel_listing,
    raw_create_product_channel_listing,
)
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse
from .utils import raw_checkout_create


def prepare_product(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
    channel_slug,
):
    permissions = [
        permission_manage_products,
        permission_manage_channels,
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

    product_type_data = create_product_type(
        e2e_staff_api_client,
    )
    product_type_id = product_type_data["id"]

    category_data = create_category(e2e_staff_api_client)
    category_id = category_data["id"]

    product_data = create_product(e2e_staff_api_client, product_type_id, category_id)
    product_id = product_data["id"]

    raw_create_product_channel_listing(
        e2e_staff_api_client,
        product_id,
        channel_id,
        is_published=False,
        is_available_for_purchase=True,
    )

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

    return product_variant_id, channel_id, product_id, permissions


@pytest.mark.e2e
def test_unlogged_customer_is_unable_to_buy_unpublished_product_core_0109(
    e2e_staff_api_client,
    e2e_not_logged_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
):
    # Before
    channel_slug = "test-channel222"
    product_variant_id, channel_id, product_id, permissions = prepare_product(
        e2e_staff_api_client,
        permission_manage_products,
        permission_manage_channels,
        permission_manage_product_types_and_attributes,
        channel_slug,
    )

    # Step 1 - Create checkout with unpublished product variant

    lines = [
        {"variantId": product_variant_id, "quantity": 1},
    ]
    checkout_data = raw_checkout_create(
        e2e_not_logged_api_client,
        lines,
        channel_slug,
        email="testEmail@example.com",
        set_default_billing_address=True,
    )

    errors = checkout_data["errors"]

    assert errors[0]["code"] == "PRODUCT_NOT_PUBLISHED"
    assert errors[0]["field"] == "lines"
    assert errors[0]["message"] == "Cannot add lines for unpublished variants."
