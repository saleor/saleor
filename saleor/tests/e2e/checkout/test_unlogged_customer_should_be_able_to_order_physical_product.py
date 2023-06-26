from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse


def test_process_checkout_with_physical_product(
    e2e_staff_api_client,
    permission_manage_products,
):
    # given
    permissions = [
        permission_manage_products,
    ]
    assign_permissions(e2e_staff_api_client, permissions)

    warehouse_data = create_warehouse(e2e_staff_api_client)
    warehouse_id = warehouse_data["id"]
    assert warehouse_id is not None
