from decimal import Decimal

import graphene
from mock import patch

from .....payment import TransactionAction, TransactionEventType
from .....payment.interface import TransactionActionData
from .....payment.models import TransactionEvent
from .....webhook.event_types import WebhookEventSyncType
from ....core.enums import TransactionRequestRefundForGrantedRefundErrorCode
from ....core.utils import to_global_id_or_none
from ....tests.utils import assert_no_permission, get_graphql_content

TRANSACTION_REQUEST_REFUND_FOR_GRANTED_REFUND = """
mutation TransactionRequestRefundForGrantedRefund($id: ID!, $grantedRefundID: ID!) {
  transactionRequestRefundForGrantedRefund(id: $id, grantedRefundId: $grantedRefundID) {
    transaction {
      id
      events {
        type
        amount {
          amount
        }
      }
    }
    errors {
      field
      message
      code
    }
  }
}
"""


def test_missing_permission_for_app(
    app_api_client,
    order_with_lines,
    permission_manage_orders,
    transaction_item_generator,
):
    # given
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=Decimal("10.00")
    )
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, charged_value=order_with_lines.total_gross.amount
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "grantedRefundID": to_global_id_or_none(granted_refund),
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_REQUEST_REFUND_FOR_GRANTED_REFUND,
        variables,
        permissions=[permission_manage_orders],
    )

    # then
    assert_no_permission(response)


def test_missing_permission_for_user(
    staff_api_client,
    order_with_lines,
    transaction_item_generator,
    permission_group_no_perms_all_channels,
):
    # given
    permission_group_no_perms_all_channels.user_set.add(staff_api_client.user)
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=Decimal("10.00")
    )
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, charged_value=order_with_lines.total_gross.amount
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "grantedRefundID": to_global_id_or_none(granted_refund),
    }

    # when
    response = staff_api_client.post_graphql(
        TRANSACTION_REQUEST_REFUND_FOR_GRANTED_REFUND,
        variables,
    )

    # then
    assert_no_permission(response)


def test_transaction_doesnt_exist(
    app_api_client,
    order_with_lines,
    permission_manage_payments,
):
    # given
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=Decimal("10.00")
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", "1"),
        "grantedRefundID": to_global_id_or_none(granted_refund),
    }
    # when
    response = app_api_client.post_graphql(
        TRANSACTION_REQUEST_REFUND_FOR_GRANTED_REFUND,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    error_class = TransactionRequestRefundForGrantedRefundErrorCode
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestRefundForGrantedRefund"]
    assert data["errors"][0]["field"] == "id"
    assert data["errors"][0]["code"] == error_class.NOT_FOUND.name


def test_granted_refund_doesnt_exist(
    app_api_client,
    order_with_lines,
    permission_manage_payments,
    transaction_item_generator,
):
    # given
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, charged_value=order_with_lines.total_gross.amount
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "grantedRefundID": graphene.Node.to_global_id("OrderGrantedRefund", 1),
    }
    # when
    response = app_api_client.post_graphql(
        TRANSACTION_REQUEST_REFUND_FOR_GRANTED_REFUND,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    error_class = TransactionRequestRefundForGrantedRefundErrorCode
    content = get_graphql_content(response)

    data = content["data"]["transactionRequestRefundForGrantedRefund"]
    assert data["errors"][0]["field"] == "grantedRefundId"
    assert data["errors"][0]["code"] == error_class.NOT_FOUND.name


def test_transaction_belongs_to_different_order_than_granted_refund_order(
    app_api_client,
    order_with_lines,
    permission_manage_payments,
    transaction_item_generator,
    order_with_lines_for_cc,
):
    # given
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk, charged_value=order_with_lines.total_gross.amount
    )

    granted_refund = order_with_lines_for_cc.granted_refunds.create(
        amount_value=Decimal("10.00")
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "grantedRefundID": to_global_id_or_none(granted_refund),
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_REQUEST_REFUND_FOR_GRANTED_REFUND,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    content = get_graphql_content(response)

    error_class = TransactionRequestRefundForGrantedRefundErrorCode
    data = content["data"]["transactionRequestRefundForGrantedRefund"]
    assert len(data["errors"]) == 2
    assert any([err["field"] == "grantedRefundId" for err in data["errors"]])
    assert any([err["field"] == "id" for err in data["errors"]])
    assert all([err["code"] == error_class.INVALID.name for err in data["errors"]])


@patch("saleor.payment.gateway.get_webhooks_for_event")
@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
def test_missing_assigned_webhook_event(
    mocked_is_active,
    mocked_get_webhooks,
    app_api_client,
    order_with_lines,
    permission_manage_payments,
    transaction_item_generator,
    app,
):
    # given
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        charged_value=order_with_lines.total_gross.amount,
        app=app,
    )

    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=Decimal("10.00")
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "grantedRefundID": to_global_id_or_none(granted_refund),
    }

    mocked_get_webhooks.return_value = []
    mocked_is_active.return_value = False

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_REQUEST_REFUND_FOR_GRANTED_REFUND,
        variables,
        permissions=[permission_manage_payments],
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["transactionRequestRefundForGrantedRefund"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == (
        "No app or plugin is configured to handle payment action requests."
    )
    error_class = TransactionRequestRefundForGrantedRefundErrorCode
    assert data["errors"][0]["code"] == (
        error_class.MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK.name
    )

    assert mocked_is_active.called
    assert mocked_get_webhooks.called
    mocked_get_webhooks.assert_called_once_with(
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        apps_ids=[app.id],
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_triggers_refund_request_for_app(
    mocked_payment_action_request,
    mocked_is_active,
    app_api_client,
    order_with_lines,
    permission_manage_payments,
    transaction_item_generator,
    app,
):
    # given
    app.permissions.set([permission_manage_payments])
    webhook = app.webhooks.create(
        name="Request", is_active=True, target_url="http://localhost:8000/endpoint/"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        charged_value=order_with_lines.total_gross.amount,
        app=app,
    )
    expected_refund_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=expected_refund_amount
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "grantedRefundID": to_global_id_or_none(granted_refund),
    }

    # when
    response = app_api_client.post_graphql(
        TRANSACTION_REQUEST_REFUND_FOR_GRANTED_REFUND,
        variables,
    )

    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()
    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction_item,
            action_type=TransactionAction.REFUND,
            action_value=expected_refund_amount,
            event=request_event,
            transaction_app_owner=app,
            granted_refund=granted_refund,
        ),
        order_with_lines.channel.slug,
    )

    assert TransactionEvent.objects.get(
        transaction=transaction_item,
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=expected_refund_amount,
    )


@patch("saleor.plugins.manager.PluginsManager.is_event_active_for_any_plugin")
@patch("saleor.plugins.manager.PluginsManager.transaction_refund_requested")
def test_triggers_refund_request_for_staff_user(
    mocked_payment_action_request,
    mocked_is_active,
    staff_api_client,
    order_with_lines,
    permission_manage_payments,
    transaction_item_generator,
    app,
    permission_group_no_perms_all_channels,
):
    # given
    permission_group_no_perms_all_channels.user_set.add(staff_api_client.user)
    staff_api_client.user.user_permissions.add(permission_manage_payments)

    webhook = app.webhooks.create(
        name="Request", is_active=True, target_url="http://localhost:8000/endpoint/"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)
    transaction_item = transaction_item_generator(
        order_id=order_with_lines.pk,
        charged_value=order_with_lines.total_gross.amount,
        app=app,
    )
    expected_refund_amount = Decimal("10.00")
    granted_refund = order_with_lines.granted_refunds.create(
        amount_value=expected_refund_amount
    )

    variables = {
        "id": graphene.Node.to_global_id("TransactionItem", transaction_item.token),
        "grantedRefundID": to_global_id_or_none(granted_refund),
    }

    # when
    response = staff_api_client.post_graphql(
        TRANSACTION_REQUEST_REFUND_FOR_GRANTED_REFUND,
        variables,
    )

    get_graphql_content(response)

    request_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_REQUEST,
    ).first()
    assert request_event
    assert mocked_is_active.called
    mocked_payment_action_request.assert_called_once_with(
        TransactionActionData(
            transaction=transaction_item,
            action_type=TransactionAction.REFUND,
            action_value=expected_refund_amount,
            event=request_event,
            transaction_app_owner=app,
            granted_refund=granted_refund,
        ),
        order_with_lines.channel.slug,
    )

    assert TransactionEvent.objects.get(
        transaction=transaction_item,
        type=TransactionEventType.REFUND_REQUEST,
        amount_value=expected_refund_amount,
    )
