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


@pytest.mark.e2e
def test_unlogged_customer_buy_by_click_and_collect(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
    permission_manage_product_types_and_attributes,
):
    assign_permissions(
        e2e_staff_api_client,
        [
            permission_manage_products,
            permission_manage_channels,
            permission_manage_product_types_and_attributes,
        ],
    )
    warehouse_data = create_warehouse(e2e_staff_api_client)
    update_warehouse(
        e2e_staff_api_client,
        warehouse_data["id"],
        is_private=False,
        click_and_collect_option="LOCAL",
    )
    channel_data = create_channel(e2e_staff_api_client, warehouse_data["id"])
    channel_id = channel_data["id"]

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

    variant_listing = create_product_variant_channel_listing(
        e2e_staff_api_client,
        variant_id,
        channel_id,
    )

    assert variant_listing is not None
