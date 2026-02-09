import graphene
import pytest

from .....payment.models import TransactionItem
from ....tests.utils import get_graphql_content

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


@pytest.mark.parametrize(
    ("where", "expected_app_identifiers"),
    [
        ({"eq": "app.identifier.1"}, ["app.identifier.1"]),
        ({"eq": "Non-existing"}, []),
        ({"eq": None}, []),
        ({"eq": ""}, []),
        (
            {"oneOf": ["app.identifier.1", "app.identifier.2"]},
            ["app.identifier.1", "app.identifier.2"],
        ),
        ({"oneOf": ["app.identifier.1"]}, ["app.identifier.1"]),
        ({"oneOf": ["Non-existing 1", "Non-existing 2"]}, []),
        ({"oneOf": []}, []),
        (None, []),
    ],
)
def test_transactions_query_filter_by_app_identifier(
    where,
    expected_app_identifiers,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    app_identifier_1 = "app.identifier.1"
    app_identifier_2 = "app.identifier.2"
    app_identifier_3 = "app.identifier.3"

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
    transaction_3 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="PSP ref3",
        currency="USD",
    )

    transaction_1.app_identifier = app_identifier_1
    transaction_2.app_identifier = app_identifier_2
    transaction_3.app_identifier = app_identifier_3
    TransactionItem.objects.bulk_update(
        [transaction_1, transaction_2, transaction_3], ["app_identifier"]
    )

    variables = {"where": {"appIdentifier": where}}

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == len(expected_app_identifiers)


def test_transactions_query_filter_by_app_identifier_combined_with_psp_reference(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    target_app_identifier = "my.app.identifier"
    other_app_identifier = "other.app.identifier"
    target_psp_reference = "PSP-TARGET"
    other_psp_reference = "PSP-OTHER"

    target_transaction = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference=target_psp_reference,
        currency="USD",
    )
    transaction_2 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference=other_psp_reference,
        currency="USD",
    )
    transaction_3 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference=target_psp_reference,
        currency="USD",
    )

    target_transaction.app_identifier = target_app_identifier
    transaction_2.app_identifier = target_app_identifier
    transaction_3.app_identifier = other_app_identifier
    TransactionItem.objects.bulk_update(
        [target_transaction, transaction_2, transaction_3], ["app_identifier"]
    )

    variables = {
        "where": {
            "AND": [
                {"appIdentifier": {"eq": target_app_identifier}},
                {"pspReference": {"eq": target_psp_reference}},
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 1
    assert transactions[0]["node"]["pspReference"] == target_transaction.psp_reference
