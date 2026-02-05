import graphene
import pytest

from .....order.models import Order
from ....tests.utils import assert_no_permission, get_graphql_content


@pytest.fixture
def transactions_in_different_channels(
    order_list,
    checkout,
    channel_USD,
    channel_JPY,
    channel_PLN,
    transaction_item_generator,
):
    order_list[0].channel = channel_PLN
    order_list[1].channel = channel_JPY
    order_list[2].channel = channel_USD
    Order.objects.bulk_update(order_list, ["channel"])

    checkout.channel = channel_USD
    checkout.save(update_fields=["channel"])

    transaction_1 = transaction_item_generator(
        order_id=order_list[0].pk,
        psp_reference="PSP-PLN",
        currency="PLN",
    )
    transaction_2 = transaction_item_generator(
        order_id=order_list[1].pk,
        psp_reference="PSP-JPY",
        currency="JPY",
    )
    transaction_3 = transaction_item_generator(
        order_id=order_list[2].pk,
        psp_reference="PSP-USD",
        currency="USD",
    )
    transaction_4 = transaction_item_generator(
        checkout_id=checkout.pk,
        psp_reference="PSP-CHECKOUT-USD",
        currency="USD",
    )

    return [transaction_1, transaction_2, transaction_3, transaction_4]


TRANSACTIONS_QUERY = """
    query Transactions($where: TransactionWhereInput){
        transactions(first: 10, where: $where) {
            edges {
                node {
                    id
                    pspReference
                }
            }
        }
    }
"""


def test_transactions_query_no_permission(
    staff_api_client, transactions_in_different_channels
):
    # given
    variables = {}

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    assert_no_permission(response)


def test_transactions_query_by_app(
    transactions_in_different_channels,
    app_api_client,
    permission_manage_payments,
):
    # given
    app_api_client.app.permissions.add(permission_manage_payments)
    variables = {}

    # when
    response = app_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == len(transactions_in_different_channels)


def test_transactions_query_with_manage_orders_permission(
    transactions_in_different_channels,
    staff_api_client,
    permission_group_manage_orders,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)
    variables = {}

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == len(transactions_in_different_channels)


def test_transactions_query_filtered_by_accessible_channels_for_user(
    transactions_in_different_channels,
    staff_api_client,
    permission_group_manage_orders,
    channel_USD,
):
    # given
    permission_group_manage_orders.restricted_access_to_channels = True
    permission_group_manage_orders.save(update_fields=["restricted_access_to_channels"])
    permission_group_manage_orders.channels.add(channel_USD)

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {}

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]

    # Should only see transactions from channel_USD
    assert len(transactions) == 2
    assert {node["node"]["pspReference"] for node in transactions} == {
        "PSP-USD",
        "PSP-CHECKOUT-USD",
    }


def test_transactions_query_by_user_with_no_channel_access(
    transactions_in_different_channels,
    staff_api_client,
    permission_group_manage_orders,
    other_channel_USD,
):
    # given
    permission_group_manage_orders.channels.set([other_channel_USD])
    permission_group_manage_orders.restricted_access_to_channels = True
    permission_group_manage_orders.save(update_fields=["restricted_access_to_channels"])

    permission_group_manage_orders.user_set.add(staff_api_client.user)

    variables = {}

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 0


def test_transactions_query_filter_by_ids(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    transaction_1 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="PSP ref1",
        currency="USD",
    )
    transaction_2 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="PSP ref2",
        currency="USD",
    )
    _transaction_3 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="PSP ref3",
        currency="USD",
    )

    ids = [
        graphene.Node.to_global_id("TransactionItem", transaction_1.token),
        graphene.Node.to_global_id("TransactionItem", transaction_2.token),
    ]
    variables = {"where": {"ids": ids}}

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 2
    returned_ids = {node["node"]["id"] for node in transactions}
    assert returned_ids == set(ids)


@pytest.mark.parametrize("value", [None, []])
def test_transactions_query_filter_by_ids_empty_values(
    value, staff_api_client, permission_manage_payments, transaction_item_created_by_app
):
    # given
    variables = {"where": {"ids": value}}

    # when
    response = staff_api_client.post_graphql(
        TRANSACTIONS_QUERY, variables, permissions=(permission_manage_payments,)
    )

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 0


@pytest.mark.parametrize(
    ("where", "expected_psp_refs"),
    [
        ({"eq": "PSP ref1"}, ["PSP ref1"]),
        ({"eq": "Non-existing"}, []),
        ({"eq": None}, []),
        ({"eq": ""}, []),
        ({"oneOf": ["PSP ref1", "PSP ref2"]}, ["PSP ref1", "PSP ref2"]),
        ({"oneOf": ["PSP ref1"]}, ["PSP ref1"]),
        ({"oneOf": ["Non-existing 1", "Non-existing 2"]}, []),
        ({"oneOf": []}, []),
        (None, []),
    ],
)
def test_transactions_query_filter_by_psp_reference(
    where,
    expected_psp_refs,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)
    permission_group_manage_orders.channels.add(order_with_lines.channel)

    transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="PSP ref1",
        currency="USD",
    )
    transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="PSP ref2",
        currency="USD",
    )
    transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="PSP ref3",
        currency="USD",
    )

    variables = {"where": {"pspReference": where}}

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == len(expected_psp_refs)
    returned_psp_refs = {node["node"]["pspReference"] for node in transactions}
    assert returned_psp_refs == set(expected_psp_refs)


def test_transactions_query_combined_filters(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    transaction_1 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="PSP-TARGET",
        currency="USD",
    )
    transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="PSP-OTHER",
        currency="USD",
    )

    ids = [graphene.Node.to_global_id("TransactionItem", transaction_1.token)]
    variables = {
        "where": {
            "AND": [
                {"ids": ids},
                {"pspReference": {"eq": transaction_1.psp_reference}},
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 1
    assert transactions[0]["node"]["pspReference"] == transaction_1.psp_reference
