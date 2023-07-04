import pytest

from ..utils import assign_permissions
from ..warehouse.utils import create_warehouse


@pytest.mark.e2e
def test_unlogged_customer_buy_by_click_and_collect(
    e2e_staff_api_client, permission_manage_products
):
    assign_permissions(
        e2e_staff_api_client,
        [permission_manage_products],
    )
    warehouse_data = create_warehouse(e2e_staff_api_client)

    assert warehouse_data is not None
