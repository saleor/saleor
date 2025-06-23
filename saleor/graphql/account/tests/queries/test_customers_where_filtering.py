import datetime

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....account.models import User
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
        user.save(update_fields=["metadata"])

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
