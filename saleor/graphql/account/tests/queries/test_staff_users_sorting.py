import pytest

from .....account.models import User
from .....order.models import Order
from ....tests.utils import get_graphql_content

QUERY_STAFF_USERS_WITH_SORT = """
    query ($sort_by: UserSortingInput!) {
        staffUsers(first:5, sortBy: $sort_by) {
                edges{
                    node{
                        firstName
                    }
                }
            }
        }
"""


@pytest.mark.parametrize(
    "customer_sort, result_order",
    [
        # Empty string in result is first_name for staff_api_client.
        ({"field": "FIRST_NAME", "direction": "ASC"}, ["", "Joe", "John", "Leslie"]),
        ({"field": "FIRST_NAME", "direction": "DESC"}, ["Leslie", "John", "Joe", ""]),
        ({"field": "LAST_NAME", "direction": "ASC"}, ["", "John", "Joe", "Leslie"]),
        ({"field": "LAST_NAME", "direction": "DESC"}, ["Leslie", "Joe", "John", ""]),
        ({"field": "EMAIL", "direction": "ASC"}, ["John", "Leslie", "", "Joe"]),
        ({"field": "EMAIL", "direction": "DESC"}, ["Joe", "", "Leslie", "John"]),
        ({"field": "ORDER_COUNT", "direction": "ASC"}, ["John", "Leslie", "", "Joe"]),
        ({"field": "ORDER_COUNT", "direction": "DESC"}, ["Joe", "", "Leslie", "John"]),
    ],
)
def test_query_staff_members_with_sort(
    customer_sort, result_order, staff_api_client, permission_manage_staff, channel_USD
):
    User.objects.bulk_create(
        [
            User(
                first_name="John",
                last_name="Allen",
                email="allen@example.com",
                is_staff=True,
                is_active=True,
            ),
            User(
                first_name="Joe",
                last_name="Doe",
                email="zordon01@example.com",
                is_staff=True,
                is_active=True,
            ),
            User(
                first_name="Leslie",
                last_name="Wade",
                email="leslie@example.com",
                is_staff=True,
                is_active=True,
            ),
        ]
    )
    Order.objects.create(
        user=User.objects.get(email="zordon01@example.com"), channel=channel_USD
    )
    variables = {"sort_by": customer_sort}
    staff_api_client.user.user_permissions.add(permission_manage_staff)
    response = staff_api_client.post_graphql(QUERY_STAFF_USERS_WITH_SORT, variables)
    content = get_graphql_content(response)
    users = content["data"]["staffUsers"]["edges"]

    for order, user_first_name in enumerate(result_order):
        assert users[order]["node"]["firstName"] == user_first_name
