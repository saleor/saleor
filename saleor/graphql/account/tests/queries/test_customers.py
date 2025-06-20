import pytest

from .....account.models import User
from .....account.search import prepare_user_search_document_value
from .....order.models import Order
from ....tests.utils import get_graphql_content

QUERY_CUSTOMERS_WITH_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: UserSortingInput, $filter: CustomerFilterInput, $search: String
    ){
        customers(
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter, search: $search
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
    ("customer_sort", "result_order"),
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
        user=User.objects.get(email="zordon01@example.com"),
        channel=channel_USD,
        lines_count=0,
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


@pytest.mark.parametrize(
    ("customer_filter", "count"),
    [
        ("example.com", 3),
        ("Joe", 1),
        ("Allen", 1),
        ("Leslie", 1),  # first_name
        ("Wade", 1),  # last_name
        ("new york", 0),  # city
        ("us", 0),  # country
        ("+123456789", 0),
        ("John Allen", 1),
        ("Allen John", 1),
        ("Leslie Wade", 1),
        ("Joe Doe", 1),
        ("Alice Doe", 0),
    ],
)
def test_query_customers_root_level_filter(
    customer_filter,
    count,
    staff_api_client,
    permission_manage_users,
    address,
    customers_for_pagination,
):
    # given
    customers_for_pagination[1].addresses.set([address])

    for user in customers_for_pagination:
        user.search_document = prepare_user_search_document_value(user)
    User.objects.bulk_update(customers_for_pagination, ["search_document"])

    variables = {"search": customer_filter, "first": 10}
    staff_api_client.user.user_permissions.add(permission_manage_users)

    # when
    response = staff_api_client.post_graphql(
        QUERY_CUSTOMERS_WITH_PAGINATION,
        variables,
    )

    # then
    content = get_graphql_content(response)
    nodes = content["data"]["customers"]["edges"]
    assert len(nodes) == count
