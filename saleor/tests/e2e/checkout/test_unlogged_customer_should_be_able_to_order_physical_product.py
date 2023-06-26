from ..channel.utils import create_channel
from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse


def test_process_checkout_with_physical_product(
    e2e_staff_api_client,
    permission_manage_products,
    permission_manage_channels,
):
    # given
    permissions = [
        permission_manage_products,
        permission_manage_channels,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]

    warehouse_ids = [warehouse_id]
    channel_data = create_channel(e2e_staff_api_client, warehouse_ids=warehouse_ids)
    channel_id = channel_data["id"]
    channel_slug = channel_data["slug"]
    assert channel_id is not None
    assert channel_slug is not None
