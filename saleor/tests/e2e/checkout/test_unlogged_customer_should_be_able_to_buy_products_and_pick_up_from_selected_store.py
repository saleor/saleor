import pytest

from ..channel.utils import create_channel
from ..product.utils import create_product_type
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
    _channel_data = create_channel(e2e_staff_api_client, warehouse_data["id"])

    product_type_data = create_product_type(
        e2e_staff_api_client,
    )

    assert product_type_data is not None
