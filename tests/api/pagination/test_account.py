import pytest
from django.contrib.auth import models as auth_models

from saleor.account.models import User
from saleor.order.models import Order

from ..utils import get_graphql_content


@pytest.fixture()
def customers_for_search(db, address):
    accounts = User.objects.bulk_create(
        [
            User(
                first_name="Jack1",
                last_name="Allen1",
                email="allen1@example.com",
                is_staff=False,
                is_active=True,
                default_shipping_address=address,
            ),
            User(
                first_name="JackJack1",
                last_name="AllenAllen2",
                email="allenallen2@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="JackJack2",
                last_name="AllenAllen2",
                email="jackjack2allenallen2@example.com",
                is_staff=False,
                is_active=True,
            ),
            User(
                first_name="Jack2",
                last_name="Allen2",
                email="allen2@example.com",
                is_staff=False,
                is_active=True,
                default_shipping_address=address,
            ),
            User(
                first_name="Jack3",
                last_name="Allen3",
                email="allen3@example.com",
                is_staff=False,
                is_active=True,
                default_shipping_address=address,
            ),
        ]
    )
    return accounts


@pytest.fixture()
def staff_for_search(db, address):
    accounts = User.objects.bulk_create(
        [
            User(
                first_name="Jack1",
                last_name="Allen1",
                email="allen1@example.com",
                is_staff=True,
                is_active=True,
                default_shipping_address=address,
            ),
            User(
                first_name="JackJack1",
                last_name="AllenAllen2",
                email="allenallen2@example.com",
                is_staff=True,
                is_active=True,
            ),
            User(
                first_name="JackJack2",
                last_name="AllenAllen2",
                email="jackjack2allenallen2@example.com",
                is_staff=True,
                is_active=True,
            ),
            User(
                first_name="Jack2",
                last_name="Allen2",
                email="allen2@example.com",
                is_staff=True,
                is_active=True,
                default_shipping_address=address,
            ),
            User(
                first_name="Jack3",
                last_name="Allen3",
                email="allen3@example.com",
                is_staff=True,
                is_active=True,
                default_shipping_address=address,
            ),
            User(
                first_name="Jack4",
                last_name="Allen4",
                email="allen4@example.com",
                is_staff=True,
                is_active=False,
                default_shipping_address=address,
            ),
            User(
                first_name="Jack5",
                last_name="Allen5",
                email="allen5@example.com",
                is_staff=True,
                is_active=False,
                default_shipping_address=address,
            ),
            User(
                first_name="Jack6",
                last_name="Allen6",
                email="allen6@example.com",
                is_staff=True,
                is_active=False,
                default_shipping_address=address,
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
):
    Order.objects.create(user=User.objects.get(email="zordon01@example.com"))
    page_size = 2
    variables = {"first": page_size, "after": None, "sortBy": customer_sort}
    staff_api_client.user.user_permissions.add(permission_manage_users)
    response = staff_api_client.post_graphql(
        QUERY_CUSTOMERS_WITH_PAGINATION, variables,
    )
    content = get_graphql_content(response)
    nodes = content["data"]["customers"]["edges"]
    assert result_order[0] == nodes[0]["node"]["firstName"]
    assert result_order[1] == nodes[1]["node"]["firstName"]
    assert len(nodes) == page_size


@pytest.mark.parametrize(
    "customer_filter, users_order",
    [
        ({"search": "example.com"}, ["Jack1", "Jack2"]),
        ({"search": "Jack"}, ["Jack1", "Jack2"]),
        ({"search": "Allen"}, ["Jack1", "Jack2"]),
        ({"search": "JackJack"}, ["JackJack1", "JackJack2"]),
        ({"search": "jackjack"}, ["JackJack1", "JackJack2"]),
        ({"search": "Jack1"}, ["Jack1", "JackJack1"]),
        (
            {"search": "John"},
            ["Jack1", "Jack2"],
        ),  # default_shipping_address__first_name
        ({"search": "Doe"}, ["Jack1", "Jack2"]),  # default_shipping_address__last_name
        ({"search": "wroc"}, ["Jack1", "Jack2"]),  # default_shipping_address__city
        (
            {"search": "pl"},
            ["Jack1", "Jack2"],
        ),  # default_shipping_address__country, email
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
        QUERY_CUSTOMERS_WITH_PAGINATION, variables,
    )
    content = get_graphql_content(response)

    users = content["data"]["customers"]["edges"]
    assert users_order[0] == users[0]["node"]["firstName"]
    assert users_order[1] == users[1]["node"]["firstName"]
    assert len(users) == page_size


@pytest.mark.parametrize(
    "staff_member_filter, users_order",
    [
        ({"search": "example.com"}, ["Jack1", "Jack2"]),
        ({"search": "Jack"}, ["Jack1", "Jack2"]),
        ({"search": "Allen"}, ["Jack1", "Jack2"]),
        ({"search": "JackJack"}, ["JackJack1", "JackJack2"]),
        ({"search": "jackjack"}, ["JackJack1", "JackJack2"]),
        ({"search": "Jack1"}, ["Jack1", "JackJack1"]),
        (
            {"search": "John"},
            ["Jack1", "Jack2"],
        ),  # default_shipping_address__first_name
        ({"search": "Doe"}, ["Jack1", "Jack2"]),  # default_shipping_address__last_name
        ({"search": "wroc"}, ["Jack1", "Jack2"]),  # default_shipping_address__city
        (
            {"search": "pl"},
            ["Jack1", "Jack2"],
        ),  # default_shipping_address__country, email
        ({"status": "DEACTIVATED"}, ["Jack4", "Jack5"]),
        ({"status": "ACTIVE"}, ["Jack1", "Jack2"]),
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
    return auth_models.Group.objects.bulk_create(
        [
            auth_models.Group(name="Group1"),
            auth_models.Group(name="GroupGroup1"),
            auth_models.Group(name="GroupGroup2"),
            auth_models.Group(name="Group2"),
            auth_models.Group(name="Group3"),
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
        ({"field": "NAME", "direction": "ASC"}, ["Group1", "Group2", "Group3"]),
        (
            {"field": "NAME", "direction": "DESC"},
            ["GroupGroup2", "GroupGroup1", "Group3"],
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


@pytest.mark.parametrize(
    "filter_by, permission_groups_order",
    [
        ({"search": "GroupGroup"}, ["GroupGroup1", "GroupGroup2"]),
        ({"search": "Group1"}, ["Group1", "GroupGroup1"]),
    ],
)
def test_permission_groups_pagination_with_filtering(
    filter_by,
    permission_groups_order,
    staff_api_client,
    permission_manage_staff,
    permission_groups_for_pagination,
):
    page_size = 2

    variables = {"first": page_size, "after": None, "filter": filter_by}
    response = staff_api_client.post_graphql(
        QUERY_PERMISSION_GROUPS_PAGINATION,
        variables,
        permissions=[permission_manage_staff],
    )
    content = get_graphql_content(response)
    permission_groups_nodes = content["data"]["permissionGroups"]["edges"]
    assert permission_groups_order[0] == permission_groups_nodes[0]["node"]["name"]
    assert permission_groups_order[1] == permission_groups_nodes[1]["node"]["name"]
    assert len(permission_groups_nodes) == page_size
