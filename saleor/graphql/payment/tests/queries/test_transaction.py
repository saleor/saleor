import graphene

from .....payment.models import TransactionEvent
from ....tests.utils import assert_no_permission, get_graphql_content

TRANSACTION_QUERY = """
    query transaction($id: ID!){
        transaction(id: $id) {
            id
            createdAt
            actions
            authorizedAmount{
                currency
                amount
            }
            refundedAmount{
                currency
                amount
            }
            voidedAmount{
                currency
                amount
            }
            chargedAmount{
                currency
                amount
            }
            events{
                id
            }
            status
            type
            reference
            order {
                id
            }
        }
    }
"""


def _assert_transaction_fields(content, transaction_item, event):
    data = content["data"]["transaction"]
    assert data["createdAt"] == transaction_item.created_at.isoformat()
    assert data["actions"] == [
        action.upper() for action in transaction_item.available_actions
    ]
    assert (
        data["authorizedAmount"]["amount"] == transaction_item.amount_authorized.amount
    )
    assert data["refundedAmount"]["amount"] == transaction_item.amount_refunded.amount
    assert data["voidedAmount"]["amount"] == transaction_item.amount_voided.amount
    assert data["chargedAmount"]["amount"] == transaction_item.amount_charged.amount
    assert len(data["events"]) == 1
    assert data["events"][0]["id"] == graphene.Node.to_global_id(
        "TransactionEvent", event.id
    )
    assert data["status"] == transaction_item.status
    assert data["type"] == transaction_item.type
    if transaction_item.order_id:
        assert data["order"]["id"] == graphene.Node.to_global_id(
            "Order", transaction_item.order.id
        )
    else:
        assert data["order"] is None


def test_transaction_query_by_app(
    app_api_client, transaction_item, permission_manage_payments
):
    # given
    event = TransactionEvent.objects.create(transaction=transaction_item)

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.id)
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_QUERY, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    _assert_transaction_fields(content, transaction_item, event)


def test_transaction_query_no_order(
    app_api_client, transaction_item, permission_manage_payments
):
    # given
    transaction_item.order = None
    transaction_item.save(update_fields=["order"])

    event = TransactionEvent.objects.create(transaction=transaction_item)

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.id)
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_QUERY, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    _assert_transaction_fields(content, transaction_item, event)


def test_transaction_query_by_staff(
    staff_api_client, transaction_item, permission_manage_payments
):
    # given
    event = TransactionEvent.objects.create(transaction=transaction_item)

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.id)
    }

    # when
    response = staff_api_client.post_graphql(
        TRANSACTION_QUERY, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    _assert_transaction_fields(content, transaction_item, event)


def test_transaction_query_no_permission(app_api_client, transaction_item):
    # given
    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.id)
    }

    # when
    response = app_api_client.post_graphql(TRANSACTION_QUERY, variables)

    # then
    assert_no_permission(response)
