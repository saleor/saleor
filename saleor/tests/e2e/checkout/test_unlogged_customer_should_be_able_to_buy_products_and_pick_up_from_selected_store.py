import pytest

from ..channel.utils import create_channel
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse, update_warehouse


@pytest.mark.e2e
def test_unlogged_customer_buy_by_click_and_collect(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
):
    assign_permissions(
        e2e_staff_api_client,
        [
            permission_manage_products,
            permission_manage_channels,
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

    assert channel_data is not None
