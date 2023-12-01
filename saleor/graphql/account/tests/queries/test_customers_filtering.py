import graphene
import pytest
from freezegun import freeze_time

from .....account.models import User
from .....account.search import prepare_user_search_document_value
from .....order.models import Order
from ....tests.utils import get_graphql_content


@pytest.fixture
def query_customer_with_filter():
    query = """
    query ($filter: CustomerFilterInput!, ) {
        customers(first: 5, filter: $filter) {
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
    ("customer_filter", "count"),
    [
        ({"search": "mirumee.com"}, 2),
        ({"search": "Alice"}, 1),
        ({"search": "Kowalski"}, 1),
        ({"search": "John"}, 1),  # first_name
        ({"search": "Doe"}, 1),  # last_name
        ({"search": "wroc"}, 1),  # city
        ({"search": "pl"}, 1),  # country
        ({"search": "+48713988102"}, 1),
        ({"search": "alice Kowalski"}, 1),
        ({"search": "kowalski alice"}, 1),
        ({"search": "John doe"}, 1),
        ({"search": "Alice Doe"}, 0),
    ],
)
def test_query_customer_members_with_filter_search(
    customer_filter,
    count,
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    address,
    staff_user,
):
    users = User.objects.bulk_create(
        [
            User(
                email="second@mirumee.com",
                first_name="Alice",
                last_name="Kowalski",
                is_active=False,
            ),
            User(
                email="third@mirumee.com",
                is_active=True,
            ),
        ]
    )
    users[1].addresses.set([address])

    for user in users:
        user.search_document = prepare_user_search_document_value(user)
    User.objects.bulk_update(users, ["search_document"])

    variables = {"filter": customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]

    assert len(users) == count


def test_query_customers_with_filter_by_one_id(
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_users,
):
    # given
    search_user = customer_users[0]

    variables = {
        "filter": {
            "ids": [graphene.Node.to_global_id("User", search_user.pk)],
        }
    }

    # when
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    result_user = content["data"]["customers"]["edges"][0]
    _, id = graphene.Node.from_global_id(result_user["node"]["id"])
    assert id == str(search_user.pk)


def test_query_customers_with_filter_by_multiple_ids(
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_users,
):
    # given
    search_users = [customer_users[0], customer_users[1]]
    search_users_ids = [
        graphene.Node.to_global_id("User", user.pk) for user in search_users
    ]

    variables = {"filter": {"ids": search_users_ids}}

    # when
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    result_users = content["data"]["customers"]["edges"]
    expected_ids = [str(user.pk) for user in customer_users]

    assert len(result_users) == len(search_users)
    for result_user in result_users:
        _, id = graphene.Node.from_global_id(result_user["node"]["id"])
        assert id in expected_ids


def test_query_customers_with_filter_by_empty_list(
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_users,
):
    # given
    variables = {"filter": {"ids": []}}

    # when
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    result_users = content["data"]["customers"]["edges"]
    expected_ids = [str(user.pk) for user in customer_users]

    assert len(result_users) == len(customer_users)
    for result_user in result_users:
        _, id = graphene.Node.from_global_id(result_user["node"]["id"])
        assert id in expected_ids


def test_query_customers_with_filter_by_not_existing_id(
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_users,
):
    # given
    search_pk = max([user.pk for user in customer_users]) + 1
    search_id = graphene.Node.to_global_id("User", search_pk)
    variables = {"filter": {"ids": [search_id]}}

    # when
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)

    # then
    result_users = content["data"]["customers"]["edges"]

    assert len(result_users) == 0


@pytest.mark.parametrize(
    ("customer_filter", "count"),
    [
        ({"placedOrders": {"gte": "2019-04-18"}}, 1),
        ({"placedOrders": {"lte": "2012-01-14"}}, 1),
        ({"placedOrders": {"lte": "2012-01-14", "gte": "2012-01-13"}}, 1),
        ({"placedOrders": {"gte": "2012-01-14"}}, 2),
    ],
)
def test_query_customers_with_filter_placed_orders(
    customer_filter,
    count,
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_user,
    channel_USD,
):
    Order.objects.create(user=customer_user, channel=channel_USD)
    second_customer = User.objects.create(email="second_example@example.com")
    with freeze_time("2012-01-14 11:00:00"):
        Order.objects.create(user=second_customer, channel=channel_USD)
    variables = {"filter": customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]

    assert len(users) == count


@pytest.mark.parametrize(
    ("customer_filter", "count"),
    [
        ({"dateJoined": {"gte": "2019-04-18"}}, 1),
        ({"dateJoined": {"lte": "2012-01-14"}}, 1),
        ({"dateJoined": {"lte": "2012-01-14", "gte": "2012-01-13"}}, 1),
        ({"dateJoined": {"gte": "2012-01-14"}}, 2),
        ({"updatedAt": {"gte": "2012-01-14T10:59:00+00:00"}}, 2),
        ({"updatedAt": {"gte": "2012-01-14T11:01:00+00:00"}}, 1),
        ({"updatedAt": {"lte": "2012-01-14T12:00:00+00:00"}}, 1),
        ({"updatedAt": {"lte": "2011-01-14T10:59:00+00:00"}}, 0),
        (
            {
                "updatedAt": {
                    "lte": "2012-01-14T12:00:00+00:00",
                    "gte": "2012-01-14T10:00:00+00:00",
                }
            },
            1,
        ),
        ({"updatedAt": {"gte": "2012-01-14T10:00:00+00:00"}}, 2),
    ],
)
def test_query_customers_with_filter_date_joined_and_updated_at(
    customer_filter,
    count,
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_user,
):
    with freeze_time("2012-01-14 11:00:00"):
        User.objects.create(email="second_example@example.com")
    variables = {"filter": customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]
    assert len(users) == count


@pytest.mark.parametrize(
    ("customer_filter", "count"),
    [
        ({"numberOfOrders": {"gte": 0, "lte": 1}}, 1),
        ({"numberOfOrders": {"gte": 1, "lte": 3}}, 2),
        ({"numberOfOrders": {"gte": 0}}, 2),
        ({"numberOfOrders": {"lte": 3}}, 2),
    ],
)
def test_query_customers_with_filter_placed_orders_(
    customer_filter,
    count,
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_user,
    channel_USD,
):
    Order.objects.bulk_create(
        [
            Order(user=customer_user, channel=channel_USD),
            Order(user=customer_user, channel=channel_USD),
            Order(user=customer_user, channel=channel_USD),
        ]
    )
    second_customer = User.objects.create(email="second_example@example.com")
    with freeze_time("2012-01-14 11:00:00"):
        Order.objects.create(user=second_customer, channel=channel_USD)
    variables = {"filter": customer_filter}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]

    assert len(users) == count


def test_query_customers_with_filter_metadata(
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    customer_user,
    channel_USD,
):
    second_customer = User.objects.create(email="second_example@example.com")
    second_customer.store_value_in_metadata({"metakey": "metavalue"})
    second_customer.save()

    variables = {"filter": {"metadata": [{"key": "metakey", "value": "metavalue"}]}}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]
    assert len(users) == 1
    user = users[0]
    _, user_id = graphene.Node.from_global_id(user["node"]["id"])
    assert second_customer.id == int(user_id)


def test_query_customers_search_without_duplications(
    query_customer_with_filter,
    staff_api_client,
    permission_manage_users,
    permission_manage_orders,
):
    customer = User.objects.create(email="david@example.com")
    customer.addresses.create(first_name="David")
    customer.addresses.create(first_name="David")
    customer.search_document = prepare_user_search_document_value(customer)
    customer.save(update_fields=["search_document"])

    variables = {"filter": {"search": "David"}}
    response = staff_api_client.post_graphql(
        query_customer_with_filter, variables, permissions=[permission_manage_users]
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]
    assert len(users) == 1

    response = staff_api_client.post_graphql(
        query_customer_with_filter,
        variables,
        permissions=[permission_manage_orders],
        check_no_permissions=False,
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["edges"]
    assert len(users) == 1


def test_query_customers_with_permission_manage_orders(
    query_customer_with_filter,
    customer_user,
    staff_api_client,
    permission_manage_orders,
):
    variables = {"filter": {}}

    response = staff_api_client.post_graphql(
        query_customer_with_filter,
        variables,
        permissions=[permission_manage_orders],
    )
    content = get_graphql_content(response)
    users = content["data"]["customers"]["totalCount"]
    assert users == 1


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


@pytest.mark.parametrize(
    ("customer_filter", "users_order"),
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
