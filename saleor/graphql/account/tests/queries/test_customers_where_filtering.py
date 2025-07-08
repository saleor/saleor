import datetime

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....account.models import Address, User
from .....order import OrderOrigin
from ....tests.utils import get_graphql_content

QUERY_CUSTOMERS_WITH_WHERE = """
    query ($where: CustomerWhereInput!, ) {
        customers(first: 5, where: $where) {
            totalCount
            edges {
                node {
                    id
                    email
                    lastName
                    firstName
                }
            }
        }
    }
"""


def test_customers_filter_by_ids(
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    permission_group_manage_users.user_set.add(staff_api_client.user)
    ids = [graphene.Node.to_global_id("User", user.pk) for user in customer_users[:2]]
    variables = {"where": {"ids": ids}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    data = get_graphql_content(response)
    customers = data["data"]["customers"]["edges"]
    assert len(customers) == 2
    returned_ids = {node["node"]["id"] for node in customers}
    returned_emails = {node["node"]["email"] for node in customers}
    expected_emails = {user.email for user in customer_users[:2]}
    assert returned_ids == set(ids)
    assert returned_emails == expected_emails


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            {
                "gte": (timezone.now() - datetime.timedelta(days=7)).isoformat(),
                "lte": (timezone.now() - datetime.timedelta(days=1)).isoformat(),
            },
            [1, 2],
        ),
        (
            {
                "gte": (timezone.now() - datetime.timedelta(days=4)).isoformat(),
            },
            [0, 2],
        ),
        (
            {
                "lte": (timezone.now() + datetime.timedelta(days=1)).isoformat(),
            },
            [0, 1, 2],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(days=25)).isoformat(),
            },
            [],
        ),
        (None, []),
        ({"gte": None}, []),
        ({"lte": None}, []),
        ({"lte": None, "gte": None}, []),
        ({}, []),
    ],
)
def test_customers_filter_by_date_joined(
    where,
    indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_user,
):
    # given
    with freeze_time((timezone.now() - datetime.timedelta(days=5)).isoformat()):
        customer_2 = User.objects.create_user(
            "test2@example.com",
            "password",
            first_name="Leslie",
            last_name="Wade",
        )

    with freeze_time((timezone.now() - datetime.timedelta(days=2)).isoformat()):
        customer_3 = User.objects.create_user(
            "test3@example.com",
            "password",
            first_name="John",
            last_name="Lee",
        )

    customer_list = [customer_user, customer_2, customer_3]

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"dateJoined": where}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_list[index].email for index in indexes}


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            {
                "gte": (timezone.now() - datetime.timedelta(days=6)).isoformat(),
                "lte": (timezone.now() - datetime.timedelta(days=4)).isoformat(),
            },
            [0],
        ),
        (
            {
                "gte": (timezone.now() - datetime.timedelta(days=3)).isoformat(),
            },
            [1, 2],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(days=2)).isoformat(),
            },
            [0, 1],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(days=7)).isoformat(),
            },
            [],
        ),
        (None, []),
        ({"gte": None}, []),
        ({"lte": None}, []),
        ({"lte": None, "gte": None}, []),
        ({}, []),
    ],
)
def test_customers_filter_by_updated_at(
    where,
    indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    now = timezone.now()
    updated_at_dates = [
        now - datetime.timedelta(days=5),
        now - datetime.timedelta(days=3),
        now - datetime.timedelta(days=2),
    ]

    for user, updated_at in zip(customer_users, updated_at_dates, strict=True):
        user.updated_at = updated_at

    User.objects.bulk_update(customer_users, ["updated_at"])

    customer_list = customer_users

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"updatedAt": where}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_list[index].email for index in indexes}


@pytest.mark.parametrize(
    ("metadata", "expected_indexes"),
    [
        ({"key": "foo"}, [0, 1]),
        ({"key": "foo", "value": {"eq": "bar"}}, [0]),
        ({"key": "foo", "value": {"eq": "baz"}}, []),
        ({"key": "foo", "value": {"oneOf": ["bar", "zaz"]}}, [0, 1]),
        ({"key": "notfound"}, []),
        ({"key": "foo", "value": {"eq": None}}, []),
        ({"key": "foo", "value": {"oneOf": []}}, []),
        (None, []),
    ],
)
def test_customers_filter_by_metadata(
    metadata,
    expected_indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    metadata_values = [
        {"foo": "bar"},
        {"foo": "zaz"},
        {},
    ]
    for user, metadata_value in zip(customer_users, metadata_values, strict=True):
        user.metadata = metadata_value

    User.objects.bulk_update(customer_users, ["metadata"])

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"metadata": metadata}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(expected_indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_users[i].email for i in expected_indexes}


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            {
                "gte": (timezone.now() - datetime.timedelta(days=10)).isoformat(),
                "lte": (timezone.now() - datetime.timedelta(days=5)).isoformat(),
            },
            [0],
        ),
        (
            {
                "gte": (timezone.now() - datetime.timedelta(days=4)).isoformat(),
            },
            [1, 2],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(days=6)).isoformat(),
            },
            [0],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(days=15)).isoformat(),
            },
            [],
        ),
        (None, []),
        ({"gte": None}, []),
        ({"lte": None}, []),
        ({"lte": None, "gte": None}, []),
        ({}, []),
    ],
)
def test_customers_filter_by_placed_orders_at(
    where,
    indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
    address,
    channel_USD,
):
    # given
    now = timezone.now()
    placed_orders_dates = [
        now - datetime.timedelta(days=7),
        now - datetime.timedelta(days=3),
        now - datetime.timedelta(days=2),
    ]

    for user, placed_at in zip(customer_users, placed_orders_dates, strict=True):
        with freeze_time(placed_at.isoformat()):
            user.orders.create(
                billing_address=address,
                user_email=user.email,
                channel=channel_USD,
                origin=OrderOrigin.CHECKOUT,
                lines_count=0,
            )

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"placedOrdersAt": where}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_users[index].email for index in indexes}


@pytest.mark.parametrize(
    ("email_filter", "expected_indexes"),
    [
        ({"eq": "test1@example.com"}, [0]),
        ({"eq": "test2@example.com"}, [1]),
        ({"eq": "notfound@example.com"}, []),
        ({"oneOf": ["test1@example.com", "test3@example.com"]}, [0, 2]),
        ({"oneOf": ["notfound@example.com"]}, []),
        (None, []),
        ({"eq": None}, []),
        ({"oneOf": []}, []),
    ],
)
def test_customers_filter_by_email(
    email_filter,
    expected_indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    customer_emails = [
        "test1@example.com",
        "test2@example.com",
        "test3@example.com",
    ]
    for user, email in zip(customer_users, customer_emails, strict=True):
        user.email = email

    User.objects.bulk_update(customer_users, ["email"])

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"email": email_filter}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(expected_indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_users[i].email for i in expected_indexes}


@pytest.mark.parametrize(
    ("is_active_filter", "expected_indexes"),
    [
        (True, [0, 1]),
        (False, [2]),
        (None, []),
    ],
)
def test_customers_filter_by_is_active(
    is_active_filter,
    expected_indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    is_active_values = [True, True, False]
    for user, is_active in zip(customer_users, is_active_values, strict=True):
        user.is_active = is_active

    User.objects.bulk_update(customer_users, ["is_active"])

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"isActive": is_active_filter}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(expected_indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_users[i].email for i in expected_indexes}


@pytest.mark.parametrize(
    ("address_filter", "expected_indexes"),
    [
        ({"phoneNumber": {"eq": "+48123456789"}}, [0]),
        ({"phoneNumber": {"eq": "+1987654321"}}, [1]),
        ({"phoneNumber": {"eq": "notfound"}}, []),
        ({"phoneNumber": {"oneOf": ["+48123456789", "+86555555555"]}}, [0, 2]),
        ({"phoneNumber": {"oneOf": ["notfound"]}}, []),
        ({"country": {"eq": "GE"}}, [0]),
        ({"country": {"eq": "US"}}, [1]),
        ({"country": {"eq": "CN"}}, [2]),
        ({"country": {"eq": "JP"}}, []),
        ({"country": {"oneOf": ["GE", "CN"]}}, [0, 2]),
        ({"country": {"oneOf": ["JP"]}}, []),
        ({"country": {"notOneOf": ["GE", "CN", "PL"]}}, [1]),
        ({"phoneNumber": {"eq": "+48123456789"}, "country": {"eq": "GE"}}, [0]),
        ({"phoneNumber": {"eq": "+48123456789"}, "country": {"eq": "US"}}, []),
        (
            {
                "phoneNumber": {"oneOf": ["+48123456789", "+86555555555"]},
                "country": {"notOneOf": ["GE"]},
            },
            [2],
        ),
        (None, []),
        ({"phoneNumber": {"eq": None}}, []),
        ({"phoneNumber": {"oneOf": []}}, []),
        ({"country": {"eq": None}}, []),
        ({"country": {"oneOf": []}}, []),
    ],
)
def test_customers_filter_by_addresses(
    address_filter,
    expected_indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    phones = [
        "+48123456789",
        "+1987654321",
        "+86555555555",
    ]
    countries = ["GE", "US", "CN"]
    addresses = [
        Address.objects.create(
            first_name="John",
            last_name="Doe",
            company_name="Mirumee Software",
            street_address_1="Tęczowa 7",
            city="WROCŁAW",
            postal_code="53-601",
            country=country,
            phone=phone,
        )
        for phone, country in zip(phones, countries, strict=True)
    ]
    for user, address in zip(customer_users, addresses, strict=True):
        user.addresses.add(address)

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"addresses": address_filter}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(expected_indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_users[i].email for i in expected_indexes}


@pytest.mark.parametrize(
    ("orders_filter", "expected_indexes"),
    [
        ({"range": {"gte": 2}}, [0, 1]),
        ({"range": {"lte": 1}}, [2]),
        ({"range": {"gte": 2, "lte": 3}}, [0, 1]),
        ({"eq": 3}, [0]),
        ({"eq": 0}, []),
        ({"range": {"gte": 4}}, []),
        ({"oneOf": [3, 1]}, [0, 2]),
        ({"oneOf": [2]}, [1]),
        ({"oneOf": [4, 5]}, []),
        ({"oneOf": []}, []),
        (None, []),
        ({"range": {"gte": None}}, []),
        ({"range": {"lte": None}}, []),
        ({"eq": None}, []),
    ],
)
def test_customers_filter_by_number_of_orders(
    orders_filter,
    expected_indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    orders_counts = [3, 2, 1]
    for user, orders_count in zip(customer_users, orders_counts, strict=True):
        user.number_of_orders = orders_count

    User.objects.bulk_update(customer_users, ["number_of_orders"])

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"numberOfOrders": orders_filter}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(expected_indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_users[i].email for i in expected_indexes}


@pytest.mark.parametrize(
    ("first_name_filter", "expected_indexes"),
    [
        ({"eq": "John"}, [0]),
        ({"eq": "Leslie"}, [1]),
        ({"eq": "NotFound"}, []),
        ({"oneOf": ["John", "Jane"]}, [0, 2]),
        ({"oneOf": ["NotFound"]}, []),
        (None, []),
        ({"eq": None}, []),
        ({"oneOf": []}, []),
    ],
)
def test_customers_filter_by_first_name(
    first_name_filter,
    expected_indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    first_names = [
        "John",
        "Leslie",
        "Jane",
    ]
    for user, first_name in zip(customer_users, first_names, strict=True):
        user.first_name = first_name

    User.objects.bulk_update(customer_users, ["first_name"])

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"firstName": first_name_filter}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(expected_indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_users[i].email for i in expected_indexes}


@pytest.mark.parametrize(
    ("last_name_filter", "expected_indexes"),
    [
        ({"eq": "Doe"}, [0]),
        ({"eq": "Wade"}, [1]),
        ({"eq": "NotFound"}, []),
        ({"oneOf": ["Doe", "Smith"]}, [0, 2]),
        ({"oneOf": ["NotFound"]}, []),
        (None, []),
        ({"eq": None}, []),
        ({"oneOf": []}, []),
    ],
)
def test_customers_filter_by_last_name(
    last_name_filter,
    expected_indexes,
    staff_api_client,
    permission_group_manage_users,
    customer_users,
):
    # given
    last_names = [
        "Doe",
        "Wade",
        "Smith",
    ]
    for user, last_name in zip(customer_users, last_names, strict=True):
        user.last_name = last_name

    User.objects.bulk_update(customer_users, ["last_name"])

    permission_group_manage_users.user_set.add(staff_api_client.user)
    variables = {"where": {"lastName": last_name_filter}}

    # when
    response = staff_api_client.post_graphql(QUERY_CUSTOMERS_WITH_WHERE, variables)

    # then
    content = get_graphql_content(response)
    customers = content["data"]["customers"]["edges"]
    assert len(customers) == len(expected_indexes)
    emails = {node["node"]["email"] for node in customers}
    assert emails == {customer_users[i].email for i in expected_indexes}
