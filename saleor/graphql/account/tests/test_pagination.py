import pytest
from django.contrib.auth import models as auth_models

from ....account.models import User
from ....order.models import Order
from ...tests.utils import get_graphql_content


@pytest.fixture()
def customers_for_search(db, address):
    accounts = User.objects.bulk_create(
        [
            User(
                first_name="John",
                last_name="Miller",
                email="jmiller12@example.com",
                is_staff=False,
                is_active=True,
                default_shipping_address=address,
            ),
            User(
                first_name="Leslie",
                last_name="Miller",
                email="lmiller33@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Harry",
                last_name="Smith",
                email="hsmith91@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Alan",
                last_name="Smith",
                email="alansmith1@example.com",
                is_staff=False,
                is_active=False,
                default_shipping_address=address,
            ),
            User(
                first_name="Robert",
                last_name="Davis",
                email="rdavis11@example.com",
                is_staff=False,
                is_active=False,
            ),
            User(
                first_name="Xavier",
                last_name="Davis",
                email="xdavis93@example.com",
                is_staff=False,
                is_active=True,
            ),
        ]
    )
    return accounts


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


QUERY_STAFF_WITH_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: UserSortingInput, $filter: StaffUserInput
    ){
        staffUsers(
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


@pytest.mark.parametrize(
    "customer_filter, users_order",
    [
        ({"search": "example.com"}, ["Alan", "Harry"]),  # email
        (
            {"search": "Miller"},
            ["John", "Leslie"],
        ),  # default_shipping_address__last_name
        ({"search": "wroc"}, ["Alan", "John"]),  # default_shipping_address__city
        ({"search": "pl"}, ["Alan", "John"]),  # default_shipping_address__country
    ],
)
def test_query_customer_members_pagination_with_filter_search(
    customer_filter,
    users_order,
    staff_api_client,
    permission_manage_users,
    customers_for_search,
):
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": customer_filter}
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(
        QUERY_CUSTOMERS_WITH_PAGINATION,
        variables,
    )
    content = get_graphql_content(response)

    users = content["data"]["customers"]["edges"]
    assert users_order[0] == users[0]["node"]["firstName"]
    assert users_order[1] == users[1]["node"]["firstName"]
    assert len(users) == page_size


@pytest.mark.parametrize(
    "staff_member_filter, users_order",
    [
        ({"search": "example.com"}, ["Alan", "Harry"]),  # email
        (
            {"search": "davis"},
            ["Robert", "Xavier"],
        ),  # default_shipping_address__last_name
        ({"search": "wroc"}, ["Alan", "John"]),  # default_shipping_address__city
        ({"search": "pl"}, ["Alan", "John"]),  # default_shipping_address__country
        ({"status": "DEACTIVATED"}, ["Alan", "Robert"]),  # status
        ({"status": "ACTIVE"}, ["Harry", "John"]),  # status
    ],
)
def test_query_staff_members_pagination_with_filter_search(
    staff_member_filter,
    users_order,
    staff_api_client,
    permission_manage_staff,
    customers_for_search,
):
    page_size = 2

    for customer in customers_for_search:
        customer.is_staff = True
    User.objects.filter(
        id__in=[customer.pk for customer in customers_for_search]
    ).update(is_staff=True)

    variables = {"first": page_size, "after": None, "filter": staff_member_filter}
    staff_api_client.user.user_permissions.add(permission_manage_staff)
    response = staff_api_client.post_graphql(QUERY_STAFF_WITH_PAGINATION, variables)
    content = get_graphql_content(response)
    users = content["data"]["staffUsers"]["edges"]
    assert users_order[0] == users[0]["node"]["firstName"]
    assert users_order[1] == users[1]["node"]["firstName"]
    assert len(users) == page_size


@pytest.fixture
def permission_groups_for_pagination(db):
    return auth_models.Group.objects.bulk_create(
        [
            auth_models.Group(name="admin"),
            auth_models.Group(name="customer_manager"),
            auth_models.Group(name="discount_manager"),
            auth_models.Group(name="staff"),
            auth_models.Group(name="accountant"),
        ]
    )


QUERY_PERMISSION_GROUPS_PAGINATION = """
    query (
        $first: Int, $last: Int, $after: String, $before: String,
        $sortBy: PermissionGroupSortingInput, $filter: PermissionGroupFilterInput
    ){
        permissionGroups (
            first: $first, last: $last, after: $after, before: $before,
            sortBy: $sortBy, filter: $filter
        ) {
            edges {
                node {
                    name
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


@pytest.mark.parametrize(
    "sort_by, permission_groups_order",
    [
        (
            {"field": "NAME", "direction": "ASC"},
            ["accountant", "admin", "customer_manager"],
        ),
        (
            {"field": "NAME", "direction": "DESC"},
            ["staff", "discount_manager", "customer_manager"],
        ),
    ],
)
def test_permission_groups_pagination_with_sorting(
    sort_by,
    permission_groups_order,
    staff_api_client,
    permission_manage_staff,
    permission_groups_for_pagination,
):
    page_size = 3

    variables = {"first": page_size, "after": None, "sortBy": sort_by}
    response = staff_api_client.post_graphql(
        QUERY_PERMISSION_GROUPS_PAGINATION,
        variables,
        permissions=[permission_manage_staff],
    )
    content = get_graphql_content(response)
    permission_groups_nodes = content["data"]["permissionGroups"]["edges"]
    assert permission_groups_order[0] == permission_groups_nodes[0]["node"]["name"]
    assert permission_groups_order[1] == permission_groups_nodes[1]["node"]["name"]
    assert permission_groups_order[2] == permission_groups_nodes[2]["node"]["name"]
    assert len(permission_groups_nodes) == page_size


def test_permission_groups_pagination_with_filtering(
    staff_api_client,
    permission_manage_staff,
    permission_groups_for_pagination,
):
    page_size = 2

    variables = {"first": page_size, "after": None, "filter": {"search": "manager"}}
    response = staff_api_client.post_graphql(
        QUERY_PERMISSION_GROUPS_PAGINATION,
        variables,
        permissions=[permission_manage_staff],
    )
    content = get_graphql_content(response)
    permission_groups_nodes = content["data"]["permissionGroups"]["edges"]
    assert permission_groups_nodes[0]["node"]["name"] == "customer_manager"
    assert permission_groups_nodes[1]["node"]["name"] == "discount_manager"
    assert len(permission_groups_nodes) == page_size
