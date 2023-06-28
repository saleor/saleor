import pytest

from .....account.models import User
from .....order.models import Order
from ....tests.utils import get_graphql_content

QUERY_CUSTOMERS_WITH_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: UserSortingInput, $filter: CustomerFilterInput
    ){
        customers(
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter
        ) {
            edges {
                node {
                    firstName
                }
            }
            pageInfo{
                startCursor
                endCursor
                hasNextPage
                hasPreviousPage
            }
        }
    }
"""


@pytest.fixture
def customers_for_pagination(db):
    return User.objects.bulk_create(
        [
            User(
                first_name="John",
                last_name="Allen",
                email="allen@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Joe",
                last_name="Doe",
                email="zordon01@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Leslie",
                last_name="Wade",
                email="leslie@example.com",
                is_staff=False,
                is_active=True,
            ),
        ]
    )


@pytest.mark.parametrize(
    "customer_sort, result_order",
    [
        ({"field": "FIRST_NAME", "direction": "ASC"}, ["Joe", "John", "Leslie"]),
        ({"field": "FIRST_NAME", "direction": "DESC"}, ["Leslie", "John", "Joe"]),
        ({"field": "LAST_NAME", "direction": "ASC"}, ["John", "Joe", "Leslie"]),
        ({"field": "LAST_NAME", "direction": "DESC"}, ["Leslie", "Joe", "John"]),
        ({"field": "EMAIL", "direction": "ASC"}, ["John", "Leslie", "Joe"]),
        ({"field": "EMAIL", "direction": "DESC"}, ["Joe", "Leslie", "John"]),
        ({"field": "ORDER_COUNT", "direction": "ASC"}, ["John", "Leslie", "Joe"]),
        ({"field": "ORDER_COUNT", "direction": "DESC"}, ["Joe", "Leslie", "John"]),
    ],
)
def test_query_customers_pagination_with_sort(
    customer_sort,
    result_order,
    staff_api_client,
    permission_manage_users,
    customers_for_pagination,
    channel_USD,
):
    Order.objects.create(
        user=User.objects.get(email="zordon01@example.com"), channel=channel_USD
    )
    page_size = 2
    variables = {"first": page_size, "after": None, "sortBy": customer_sort}
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(
        QUERY_CUSTOMERS_WITH_PAGINATION,
        variables,
    )
    content = get_graphql_content(response)
    nodes = content["data"]["customers"]["edges"]
    assert result_order[0] == nodes[0]["node"]["firstName"]
    assert result_order[1] == nodes[1]["node"]["firstName"]
    assert len(nodes) == page_size
