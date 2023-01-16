import pytest

from ....account.models import Group, User
from ....account.search import prepare_user_search_document_value
from ....order.models import Order
from ...tests.utils import get_graphql_content


@pytest.fixture()
def customers_for_search(db, address):
    accounts = User.objects.bulk_create(
        [
            User(
                first_name="Alan",
                last_name="Smith",
                email="asmith@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Harry",
                last_name="Smith",
                email="hsmith@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Robert",
                last_name="Davis",
                email="rdavis@test.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Xavier",
                last_name="Davis",
                email="xdavis@test.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Anthony",
                last_name="Matthews",
                email="amatthews@test.com",
                is_staff=False,
                is_active=True,
            ),
        ]
    )
    for i, user in enumerate(accounts):
        if i in (0, 3, 4):
            user.addresses.set([address])
        user.search_document = prepare_user_search_document_value(user)
    User.objects.bulk_update(accounts, ["search_document"])
    return accounts


@pytest.fixture()
def staff_for_search(db, address):
    accounts = User.objects.bulk_create(
        [
            User(
                first_name="Alan",
                last_name="Smith",
                email="asmith@example.com",
                is_staff=True,
                is_active=False,
            ),
            User(
                first_name="Harry",
                last_name="Smith",
                email="hsmith@example.com",
                is_staff=True,
                is_active=True,
            ),
            User(
                first_name="Robert",
                last_name="Davis",
                email="rdavis@example.com",
                is_staff=True,
                is_active=False,
            ),
            User(
                first_name="Xavier",
                last_name="Davis",
                email="xdavis@example.com",
                is_staff=True,
                is_active=True,
            ),
            User(
                first_name="Anthony",
                last_name="Matthews",
                email="amatthews@example.com",
                is_staff=True,
                is_active=True,
            ),
        ]
    )
    for i, user in enumerate(accounts):
        if i in (0, 3, 4):
            user.addresses.set([address])
        user.search_document = prepare_user_search_document_value(user)
    User.objects.bulk_update(accounts, ["search_document"])
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
        ({"search": "davis@test.com"}, ["Robert", "Xavier"]),  # email
        ({"search": "davis"}, ["Robert", "Xavier"]),  # last_name
        ({"search": "wroc"}, ["Anthony", "Alan"]),  # city
        ({"search": "pl"}, ["Anthony", "Alan"]),  # country
    ],
)
def test_query_customer_members_pagination_with_filter_search(
    customer_filter,
    users_order,
    staff_api_client,
    permission_manage_users,
    address,
    staff_user,
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
        ({"search": "davis@example.com"}, ["Robert", "Xavier"]),  # email
        ({"search": "davis"}, ["Robert", "Xavier"]),  # last_name
        ({"search": "wroc"}, ["Anthony", "Alan"]),  # city
        ({"search": "pl"}, ["Anthony", "Alan"]),  # country
        ({"status": "DEACTIVATED"}, ["Alan", "Robert"]),  # status
        ({"status": "ACTIVE"}, ["Anthony", "Harry"]),  # status
    ],
)
def test_query_staff_members_pagination_with_filter_search(
    staff_member_filter,
    users_order,
    staff_api_client,
    permission_manage_staff,
    address,
    staff_user,
    staff_for_search,
):
    page_size = 2
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
    return Group.objects.bulk_create(
        [
            Group(name="admin"),
            Group(name="customer_manager"),
            Group(name="discount_manager"),
            Group(name="staff"),
            Group(name="accountant"),
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
