from datetime import timedelta

import graphene
import pytest
from django.utils import timezone

from .....payment import TransactionEventType
from .....payment.models import TransactionEvent, TransactionItem
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


def test_transactions_query_filter_respects_app_permissions(
    app_api_client,
    permission_manage_payments,
    order_with_lines,
    transaction_item_generator,
    external_app,
):
    # given
    app = app_api_client.app
    app.permissions.add(permission_manage_payments)
    external_app.permissions.add(permission_manage_payments)

    app_1_identifier = app.identifier
    app_2_identifier = external_app.identifier

    # Create transactions for App1
    transaction_app1_1 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="APP1-PSP-REF-1",
        currency="USD",
    )
    transaction_app1_2 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="APP1-PSP-REF-2",
        currency="USD",
    )

    # Create transactions for App2
    transaction_app2_1 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="APP2-PSP-REF-1",
        currency="USD",
    )
    transaction_app2_2 = transaction_item_generator(
        order_id=order_with_lines.pk,
        psp_reference="APP2-PSP-REF-2",
        currency="USD",
    )

    transaction_app1_1.app_identifier = app_1_identifier
    transaction_app1_2.app_identifier = app_1_identifier
    transaction_app2_1.app_identifier = app_2_identifier
    transaction_app2_2.app_identifier = app_2_identifier

    TransactionItem.objects.bulk_update(
        [
            transaction_app1_1,
            transaction_app1_2,
            transaction_app2_1,
            transaction_app2_2,
        ],
        ["app_identifier"],
    )

    # Filter by App2 pspReference using App1 credentials
    variables = {"where": {"pspReference": {"eq": transaction_app2_1.psp_reference}}}

    # when
    response = app_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 0


@pytest.mark.parametrize(
    ("field", "date_filter", "expected"),
    [
        ("createdAt", "gte_and_lte", "RECENT"),
        ("createdAt", "gte_only", "RECENT"),
        ("createdAt", "lte_only", "OLD"),
        ("modifiedAt", "gte_and_lte", "RECENT"),
        ("modifiedAt", "gte_only", "RECENT"),
        ("modifiedAt", "lte_only", "OLD"),
    ],
)
def test_filter_by_date_range(
    field,
    date_filter,
    expected,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    now = timezone.now()
    old_date = now - timedelta(days=30)
    recent_date = now - timedelta(days=5)

    db_field = "created_at" if field == "createdAt" else "modified_at"

    transaction_old = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="OLD", currency="USD"
    )
    transaction_recent = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="RECENT", currency="USD"
    )

    TransactionItem.objects.filter(pk=transaction_old.pk).update(**{db_field: old_date})
    TransactionItem.objects.filter(pk=transaction_recent.pk).update(
        **{db_field: recent_date}
    )

    if date_filter == "gte_and_lte":
        range_input = {
            "gte": (now - timedelta(days=10)).isoformat(),
            "lte": now.isoformat(),
        }
    elif date_filter == "gte_only":
        range_input = {"gte": (now - timedelta(days=10)).isoformat()}
    else:
        range_input = {"lte": (now - timedelta(days=20)).isoformat()}

    variables = {"where": {field: range_input}}

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 1
    assert transactions[0]["node"]["pspReference"] == expected


def test_filter_by_created_at_combined_with_psp_reference(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    now = timezone.now()
    recent_date = now - timedelta(days=5)
    old_date = now - timedelta(days=30)

    transaction_target = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="TARGET", currency="USD"
    )
    transaction_wrong_date = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="TARGET", currency="USD"
    )
    transaction_wrong_psp = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="OTHER", currency="USD"
    )

    TransactionItem.objects.filter(pk=transaction_target.pk).update(
        created_at=recent_date
    )
    TransactionItem.objects.filter(pk=transaction_wrong_date.pk).update(
        created_at=old_date
    )
    TransactionItem.objects.filter(pk=transaction_wrong_psp.pk).update(
        created_at=recent_date
    )

    variables = {
        "where": {
            "AND": [
                {"pspReference": {"eq": transaction_target.psp_reference}},
                {"createdAt": {"gte": (now - timedelta(days=10)).isoformat()}},
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 1
    assert transactions[0]["node"]["pspReference"] == transaction_target.psp_reference


def test_filter_by_event_type_eq(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    transaction_with_refund = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="REFUNDED", currency="USD"
    )
    transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="NO-EVENTS", currency="USD"
    )

    TransactionEvent.objects.create(
        transaction=transaction_with_refund,
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=10,
        currency="USD",
    )

    variables = {
        "where": {
            "events": [{"type": {"eq": TransactionEventType.REFUND_SUCCESS.upper()}}]
        }
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 1
    assert (
        transactions[0]["node"]["pspReference"] == transaction_with_refund.psp_reference
    )


def test_filter_by_event_type_one_of(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    transaction_refund = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="REFUNDED", currency="USD"
    )
    transaction_charge = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="CHARGED", currency="USD"
    )
    transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="NO-EVENTS", currency="USD"
    )

    TransactionEvent.objects.create(
        transaction=transaction_refund,
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=10,
        currency="USD",
    )
    TransactionEvent.objects.create(
        transaction=transaction_charge,
        type=TransactionEventType.CHARGE_SUCCESS,
        amount_value=20,
        currency="USD",
    )

    variables = {
        "where": {
            "events": [
                {
                    "type": {
                        "oneOf": [
                            TransactionEventType.REFUND_SUCCESS.upper(),
                            TransactionEventType.CHARGE_SUCCESS.upper(),
                        ]
                    }
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 2
    psp_refs = {t["node"]["pspReference"] for t in transactions}
    assert psp_refs == {
        transaction_refund.psp_reference,
        transaction_charge.psp_reference,
    }


def test_filter_by_event_created_at(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    now = timezone.now()

    transaction_recent = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="RECENT-EVENT", currency="USD"
    )
    transaction_old = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="OLD-EVENT", currency="USD"
    )

    TransactionEvent.objects.create(
        transaction=transaction_recent,
        type=TransactionEventType.CHARGE_SUCCESS,
        amount_value=10,
        currency="USD",
        created_at=now - timedelta(days=5),
    )
    TransactionEvent.objects.create(
        transaction=transaction_old,
        type=TransactionEventType.CHARGE_SUCCESS,
        amount_value=10,
        currency="USD",
        created_at=now - timedelta(days=30),
    )

    variables = {
        "where": {
            "events": [{"createdAt": {"gte": (now - timedelta(days=10)).isoformat()}}]
        }
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 1
    assert transactions[0]["node"]["pspReference"] == transaction_recent.psp_reference


def test_filter_by_event_type_and_created_at(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    now = timezone.now()
    recent_date = now - timedelta(days=5)
    old_date = now - timedelta(days=30)

    transaction_target = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="TARGET", currency="USD"
    )
    transaction_wrong_type = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="WRONG-TYPE", currency="USD"
    )
    transaction_wrong_date = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="WRONG-DATE", currency="USD"
    )

    TransactionEvent.objects.create(
        transaction=transaction_target,
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=10,
        currency="USD",
        created_at=recent_date,
    )
    TransactionEvent.objects.create(
        transaction=transaction_wrong_type,
        type=TransactionEventType.CHARGE_SUCCESS,
        amount_value=10,
        currency="USD",
        created_at=recent_date,
    )
    TransactionEvent.objects.create(
        transaction=transaction_wrong_date,
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=10,
        currency="USD",
        created_at=old_date,
    )

    variables = {
        "where": {
            "events": [
                {
                    "type": {"eq": TransactionEventType.REFUND_SUCCESS.upper()},
                    "createdAt": {"gte": (now - timedelta(days=10)).isoformat()},
                }
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 1
    assert transactions[0]["node"]["pspReference"] == transaction_target.psp_reference


@pytest.mark.parametrize("events_value", [[], None])
def test_filter_by_events_empty_returns_none(
    events_value,
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="PSP-1", currency="USD"
    )

    variables = {"where": {"events": events_value}}

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 0


def test_filter_by_events_combined_with_psp_reference(
    staff_api_client,
    permission_group_manage_orders,
    order_with_lines,
    transaction_item_generator,
):
    # given
    staff_api_client.user.groups.add(permission_group_manage_orders)

    target_psp = "PSP-TARGET"

    transaction_target = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference=target_psp, currency="USD"
    )
    transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference=target_psp, currency="USD"
    )
    transaction_same_event = transaction_item_generator(
        order_id=order_with_lines.pk, psp_reference="PSP-OTHER", currency="USD"
    )

    TransactionEvent.objects.create(
        transaction=transaction_target,
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=10,
        currency="USD",
    )
    TransactionEvent.objects.create(
        transaction=transaction_same_event,
        type=TransactionEventType.REFUND_SUCCESS,
        amount_value=10,
        currency="USD",
    )

    variables = {
        "where": {
            "AND": [
                {"pspReference": {"eq": target_psp}},
                {
                    "events": [
                        {"type": {"eq": TransactionEventType.REFUND_SUCCESS.upper()}}
                    ]
                },
            ]
        }
    }

    # when
    response = staff_api_client.post_graphql(TRANSACTIONS_QUERY, variables)

    # then
    content = get_graphql_content(response)
    transactions = content["data"]["transactions"]["edges"]
    assert len(transactions) == 1
    assert transactions[0]["node"]["pspReference"] == transaction_target.psp_reference
