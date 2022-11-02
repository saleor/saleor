from decimal import Decimal

from .....payment import TransactionEventActionType, TransactionEventStatus
from .....payment.models import TransactionEvent
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

TEST_SERVER_DOMAIN = "testserver.com"

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
                createdAt
                status
                pspReference
                name
                externalUrl
                amount{
                    currency
                    amount
                }
                type
            }
            status
            type
            reference
            order {
                id
            }
            user {
                id
            }
            app {
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
    assert data["events"][0]["id"] == to_global_id_or_none(event)
    assert data["status"] == transaction_item.status
    assert data["type"] == transaction_item.type
    if transaction_item.order_id:
        assert data["order"]["id"] == to_global_id_or_none(transaction_item.order)
    else:
        assert data["order"] is None


def _assert_transaction_fields_created_by_app(content, transaction_item, event):
    _assert_transaction_fields(content, transaction_item, event)
    data = content["data"]["transaction"]
    assert data["app"]["id"] == to_global_id_or_none(transaction_item.app)
    assert not data["user"]


def _assert_transaction_fields_created_by_user(content, transaction_item, event):
    _assert_transaction_fields(content, transaction_item, event)
    data = content["data"]["transaction"]
    assert data["user"]["id"] == to_global_id_or_none(transaction_item.user)
    assert not data["app"]


def test_transaction_created_by_app_query_by_app(
    app_api_client, transaction_item_created_by_app, permission_manage_payments
):
    # given
    event = TransactionEvent.objects.create(transaction=transaction_item_created_by_app)

    variables = {"id": to_global_id_or_none(transaction_item_created_by_app)}

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_QUERY, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    _assert_transaction_fields_created_by_app(
        content, transaction_item_created_by_app, event
    )


def test_transaction_creted_by_app_query_no_order(
    app_api_client, transaction_item_created_by_app, permission_manage_payments
):
    # given
    transaction_item_created_by_app.order = None
    transaction_item_created_by_app.save(update_fields=["order"])

    event = TransactionEvent.objects.create(transaction=transaction_item_created_by_app)

    variables = {"id": to_global_id_or_none(transaction_item_created_by_app)}

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_QUERY, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    _assert_transaction_fields_created_by_app(
        content, transaction_item_created_by_app, event
    )


def test_transaction_created_by_app_query_by_staff(
    staff_api_client, transaction_item_created_by_app, permission_manage_payments
):
    # given
    event = TransactionEvent.objects.create(transaction=transaction_item_created_by_app)

    variables = {"id": to_global_id_or_none(transaction_item_created_by_app)}

    # when
    response = staff_api_client.post_graphql(
        TRANSACTION_QUERY, variables, permissions=[permission_manage_payments]
    )

    # then
    content = get_graphql_content(response)
    _assert_transaction_fields_created_by_app(
        content, transaction_item_created_by_app, event
    )


def test_transaction_create_by_app_query_no_permission(
    app_api_client, transaction_item_created_by_app
):
    # given
    variables = {"id": to_global_id_or_none(transaction_item_created_by_app)}

    # when
    response = app_api_client.post_graphql(TRANSACTION_QUERY, variables)

    # then
    assert_no_permission(response)


def test_transaction_created_by_user_query_by_app(
    app_api_client,
    transaction_item_created_by_user,
    permission_manage_payments,
    permission_manage_staff,
):
    # given
    event = TransactionEvent.objects.create(
        transaction=transaction_item_created_by_user
    )

    variables = {"id": to_global_id_or_none(transaction_item_created_by_user)}

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_QUERY,
        variables,
        permissions=[permission_manage_payments, permission_manage_staff],
    )

    # then
    content = get_graphql_content(response)
    _assert_transaction_fields_created_by_user(
        content, transaction_item_created_by_user, event
    )


def test_transaction_creted_by_user_query_no_order(
    app_api_client,
    transaction_item_created_by_user,
    permission_manage_payments,
    permission_manage_staff,
):
    # given
    transaction_item_created_by_user.order = None
    transaction_item_created_by_user.save(update_fields=["order"])

    event = TransactionEvent.objects.create(
        transaction=transaction_item_created_by_user
    )

    variables = {"id": to_global_id_or_none(transaction_item_created_by_user)}

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_QUERY,
        variables,
        permissions=[permission_manage_payments, permission_manage_staff],
    )

    # then
    content = get_graphql_content(response)
    _assert_transaction_fields_created_by_user(
        content, transaction_item_created_by_user, event
    )


def test_transaction_created_by_user_query_by_staff(
    staff_api_client,
    transaction_item_created_by_user,
    permission_manage_payments,
    permission_manage_staff,
):
    # given
    event = TransactionEvent.objects.create(
        transaction=transaction_item_created_by_user
    )

    variables = {"id": to_global_id_or_none(transaction_item_created_by_user)}

    # when
    response = staff_api_client.post_graphql(
        TRANSACTION_QUERY,
        variables,
        permissions=[permission_manage_payments, permission_manage_staff],
    )

    # then
    content = get_graphql_content(response)
    _assert_transaction_fields_created_by_user(
        content, transaction_item_created_by_user, event
    )


def test_transaction_create_by_user_query_no_permission(
    app_api_client, transaction_item_created_by_user
):
    # given
    variables = {"id": to_global_id_or_none(transaction_item_created_by_user)}

    # when
    response = app_api_client.post_graphql(TRANSACTION_QUERY, variables)

    # then
    assert_no_permission(response)


def test_transaction_event_by_user(
    transaction_item_created_by_user,
    permission_manage_payments,
    permission_manage_staff,
    staff_api_client,
):
    # given
    event = TransactionEvent.objects.create(
        transaction=transaction_item_created_by_user,
        status=TransactionEventStatus.SUCCESS,
        psp_reference="psp-ref-123",
        name="Sucesfull charge",
        currency="USD",
        type=TransactionEventActionType.CHARGE,
        amount_value=Decimal("10.00"),
        external_url=f"http://`{TEST_SERVER_DOMAIN}/test",
    )

    variables = {"id": to_global_id_or_none(transaction_item_created_by_user)}

    # when
    response = staff_api_client.post_graphql(
        TRANSACTION_QUERY,
        variables,
        permissions=[permission_manage_payments, permission_manage_staff],
    )

    # then
    content = get_graphql_content(response)
    events = content["data"]["transaction"]["events"]
    assert len(events) == 1
    event_data = events[0]
    assert event_data["id"] == to_global_id_or_none(event)
    assert event_data["createdAt"] == event.created_at.isoformat()
    assert event_data["status"] == event.status.upper()
    assert event_data["pspReference"] == event.psp_reference
    assert event_data["name"] == event.name
    assert event_data["externalUrl"] == event.external_url
    assert event_data["amount"]["amount"] == event.amount_value
    assert event_data["amount"]["currency"] == event.currency
    assert event_data["type"] == event.type.upper()


def test_transaction_event_by_app(
    transaction_item_created_by_app,
    permission_manage_payments,
    permission_manage_staff,
    app_api_client,
):
    # given
    event = TransactionEvent.objects.create(
        transaction=transaction_item_created_by_app,
        status=TransactionEventStatus.SUCCESS,
        psp_reference="psp-ref-123",
        name="Sucesfull charge",
        currency="USD",
        type=TransactionEventActionType.CHARGE,
        amount_value=Decimal("10.00"),
        external_url=f"http://`{TEST_SERVER_DOMAIN}/test",
    )

    variables = {"id": to_global_id_or_none(transaction_item_created_by_app)}

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_QUERY,
        variables,
        permissions=[permission_manage_payments, permission_manage_staff],
    )

    # then
    content = get_graphql_content(response)
    events = content["data"]["transaction"]["events"]
    assert len(events) == 1
    event_data = events[0]
    assert event_data["id"] == to_global_id_or_none(event)
    assert event_data["createdAt"] == event.created_at.isoformat()
    assert event_data["status"] == event.status.upper()
    assert event_data["pspReference"] == event.psp_reference
    assert event_data["name"] == event.name
    assert event_data["externalUrl"] == event.external_url
    assert event_data["amount"]["amount"] == event.amount_value
    assert event_data["amount"]["currency"] == event.currency
    assert event_data["type"] == event.type.upper()
