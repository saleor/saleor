import graphene
import pytest

from .....account.models import User
from .....account.search import update_user_search_vector
from ....tests.utils import get_graphql_content


@pytest.fixture
def query_staff_users_with_filter():
    query = """
    query ($filter: StaffUserInput!, ) {
        staffUsers(first: 5, filter: $filter) {
            totalCount
            edges {
                node {
                    id
                    lastName
                    firstName
                }
            }
        }
    }
    """
    return query


@pytest.mark.parametrize(
    ("staff_member_filter", "count"),
    [({"status": "DEACTIVATED"}, 1), ({"status": "ACTIVE"}, 2)],
)
def test_query_staff_members_with_filter_status(
    staff_member_filter,
    count,
    query_staff_users_with_filter,
    staff_api_client,
    permission_manage_staff,
    staff_user,
):
    User.objects.bulk_create(
        [
            User(email="second@example.com", is_staff=True, is_active=False),
            User(email="third@example.com", is_staff=True, is_active=True),
        ]
    )

    variables = {"filter": staff_member_filter}
    response = staff_api_client.post_graphql(
        query_staff_users_with_filter, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    users = content["data"]["staffUsers"]["edges"]

    assert len(users) == count


def test_query_staff_members_with_filter_by_ids(
    query_staff_users_with_filter,
    staff_api_client,
    permission_manage_staff,
    staff_user,
):
    # given
    variables = {
        "filter": {
            "ids": [graphene.Node.to_global_id("User", staff_user.pk)],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query_staff_users_with_filter, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)

    # then
    users = content["data"]["staffUsers"]["edges"]
    assert len(users) == 1


@pytest.mark.parametrize(
    ("staff_member_filter", "count"),
    [
        ({"search": "second@mirumee.com"}, 1),
        ({"search": "Alice"}, 1),
        ({"search": "Kowalski"}, 1),
        ({"search": "John"}, 1),  # first_name
        ({"search": "Doe"}, 1),  # last_name
        ({"search": "Irvine"}, 1),  # city
        ({"search": "US"}, 1),  # country
        ({"search": "Alice Kowalski"}, 1),
        ({"search": "Kowalski Alice"}, 1),
        ({"search": "John Doe"}, 1),
        ({"search": "Alice Doe"}, 0),
    ],
)
def test_query_staff_members_with_filter_search(
    staff_member_filter,
    count,
    query_staff_users_with_filter,
    staff_api_client,
    permission_manage_staff,
    address_usa,
    staff_user,
):
    users = User.objects.bulk_create(
        [
            User(
                email="second@mirumee.com",
                first_name="Alice",
                last_name="Kowalski",
                is_staff=True,
                is_active=False,
            ),
            User(
                email="third@mirumee.com",
                is_staff=True,
                is_active=True,
            ),
            User(
                email="customer@mirumee.com",
                first_name="Alice",
                last_name="Kowalski",
                is_staff=False,
                is_active=True,
            ),
        ]
    )
    users[1].addresses.set([address_usa])
    for user in users:
        update_user_search_vector(user, save=False)
    User.objects.bulk_update(users, ["search_vector"])

    variables = {"filter": staff_member_filter}
    response = staff_api_client.post_graphql(
        query_staff_users_with_filter, variables, permissions=[permission_manage_staff]
    )
    content = get_graphql_content(response)
    users = content["data"]["staffUsers"]["edges"]

    assert len(users) == count


@pytest.fixture
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
        update_user_search_vector(user, save=False)
    User.objects.bulk_update(accounts, ["search_vector"])
    return accounts


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


@pytest.mark.parametrize(
    ("staff_member_filter", "expected_names"),
    [
        ({"search": "rdavis@example.com"}, ["Robert"]),  # email
        ({"search": "Davis"}, ["Robert", "Xavier"]),  # last_name
        ({"search": "WROCŁAW"}, ["Anthony", "Alan"]),  # city
        ({"search": "PL"}, ["Anthony", "Alan"]),  # country
        ({"status": "DEACTIVATED"}, ["Alan", "Robert"]),  # status
        ({"status": "ACTIVE"}, ["Anthony", "Harry"]),  # status
    ],
)
def test_query_staff_members_pagination_with_filter_search(
    staff_member_filter,
    expected_names,
    staff_api_client,
    permission_manage_staff,
    address,
    staff_user,
    staff_for_search,
):
    # given
    page_size = 2
    variables = {"first": page_size, "after": None, "filter": staff_member_filter}
    staff_api_client.user.user_permissions.add(permission_manage_staff)

    # when
    response = staff_api_client.post_graphql(QUERY_STAFF_WITH_PAGINATION, variables)

    # then
    content = get_graphql_content(response)

    users = content["data"]["staffUsers"]["edges"]
    assert len(users) == len(expected_names)
    names = {user["node"]["firstName"] for user in users}
    assert names == set(expected_names)
