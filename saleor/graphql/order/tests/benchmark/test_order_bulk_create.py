import pytest

from ....tests.utils import get_graphql_content
from ..mutations.test_order_bulk_create import (  # noqa F401
    ORDER_BULK_CREATE,
    order_bulk_input,
)


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_order_bulk_create(
    staff_api_client,
    permission_manage_orders,
    permission_manage_orders_import,
    permission_manage_users,
    order_bulk_input,  # noqa F881
):
    order = order_bulk_input

    staff_api_client.user.user_permissions.add(
        permission_manage_orders_import,
        permission_manage_orders,
        permission_manage_users,
    )
    variables = {"orders": [order]}

    get_graphql_content(staff_api_client.post_graphql(ORDER_BULK_CREATE, variables))
