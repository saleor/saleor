import json
from decimal import Decimal
from unittest import mock

import pytest
from django.utils import timezone
from freezegun import freeze_time
from graphene import Node

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....payment import (
    TransactionEventActionType,
    TransactionEventReportResult,
    TransactionEventStatus,
)
from ....payment.interface import TransactionActionData
from ....payment.models import TransactionEvent
from ....tests.utils import flush_post_commit_hooks
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.payloads import generate_transaction_action_request_payload
from ..tasks import handle_transaction_request_task, trigger_transaction_request


@pytest.fixture
def mocked_webhook_response():
    mocked_post_response = mock.Mock()
    mocked_post_response.text = json.dumps({"pspReference": "123"})
    mocked_post_response.headers = []
    mocked_post_response.status_code = 200
    mocked_post_response.ok = True
    mocked_post_response.content = json.dumps({"pspReference": "123"})
    mocked_post_response.elapsed.total_seconds = lambda: 1
    return mocked_post_response


@freeze_time("2022-06-11 12:50")
@mock.patch("saleor.plugins.webhook.tasks.handle_transaction_request_task.delay")
def test_trigger_transaction_request(
    mocked_task, transaction_item_created_by_app, staff_user, permission_manage_payments
):
    # given
    event = transaction_item_created_by_app.events.create(
        status=TransactionEventStatus.REQUEST
    )
    app = transaction_item_created_by_app.app
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook", is_active=True, target_url="http://localhost:3000/"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REQUEST)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
    )

    # when
    trigger_transaction_request(transaction_data, staff_user)

    # then
    flush_post_commit_hooks()
    generated_payload = EventPayload.objects.first()
    generated_delivery = EventDelivery.objects.first()

    assert generated_payload.payload == generate_transaction_action_request_payload(
        transaction_data, staff_user
    )
    assert generated_delivery.status == EventDeliveryStatus.PENDING
    assert generated_delivery.event_type == WebhookEventSyncType.TRANSACTION_REQUEST
    assert generated_delivery.webhook == webhook
    assert generated_delivery.payload == generated_payload

    mocked_task.assert_called_once_with(generated_delivery.id, app.name, event.id)


@freeze_time("2022-06-11 12:50")
@mock.patch("saleor.plugins.webhook.tasks.handle_transaction_request_task.delay")
def test_trigger_transaction_request_with_webhook_subscription(
    mocked_task, transaction_item_created_by_app, staff_user, permission_manage_payments
):
    # given
    subscription = """
    subscription{
        event{
            ...on TransactionRequest{
                transaction{
                    id
                    status
                }
                action{
                    amount
                    actionType
                }
            }
        }
    }
    """
    event = transaction_item_created_by_app.events.create(
        status=TransactionEventStatus.REQUEST
    )
    app = transaction_item_created_by_app.app
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url="http://localhost:3000/",
        subscription_query=subscription,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REQUEST)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
    )

    # when
    trigger_transaction_request(transaction_data, staff_user)

    # then
    flush_post_commit_hooks()
    generated_payload = EventPayload.objects.first()
    generated_delivery = EventDelivery.objects.first()

    assert json.loads(generated_payload.payload) == {
        "transaction": {
            "id": Node.to_global_id("TransactionItem", transaction_data.transaction.id),
            "status": "Captured",
        },
        "action": {"amount": 10.0, "actionType": "REFUND"},
    }
    assert generated_delivery.status == EventDeliveryStatus.PENDING
    assert generated_delivery.event_type == WebhookEventSyncType.TRANSACTION_REQUEST
    assert generated_delivery.webhook == webhook

    assert generated_delivery.payload == generated_payload

    mocked_task.assert_called_once_with(generated_delivery.id, app.name, event.id)


@freeze_time("2022-06-11 12:50")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
def test_handle_transaction_request_task_with_only_psp_reference(
    mocked_post_request,
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
):
    # given
    expected_psp_reference = "psp:ref:123"
    mocked_webhook_response.text = json.dumps({"pspReference": expected_psp_reference})
    mocked_webhook_response.content = json.dumps(
        {"pspReference": expected_psp_reference}
    )
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    event = transaction_item_created_by_app.events.create(
        status=TransactionEventStatus.REQUEST
    )
    app = transaction_item_created_by_app.app
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REQUEST)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REQUEST,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, app.name, transaction_data.event.id)

    # then
    assert TransactionEvent.objects.count() == 1
    event.refresh_from_db()
    assert event.psp_reference == expected_psp_reference
    mocked_post_request.assert_called_once_with(
        target_url, data=payload.encode("utf-8"), headers=mock.ANY, timeout=mock.ANY
    )


@pytest.mark.parametrize("status_code", [500, 501, 510])
@freeze_time("2022-06-11 12:50")
@mock.patch("saleor.plugins.webhook.tasks.handle_webhook_retry")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
def test_handle_transaction_request_task_with_server_error(
    mocked_post_request,
    mocked_webhook_retry,
    status_code,
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
):
    # given
    mocked_webhook_response.status_code = status_code
    mocked_webhook_response.text = ""
    mocked_webhook_response.content = ""
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    event = transaction_item_created_by_app.events.create(
        status=TransactionEventStatus.REQUEST
    )
    app = transaction_item_created_by_app.app
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REQUEST)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REQUEST,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, app.name, transaction_data.event.id)

    # then
    assert mocked_webhook_retry.called


@freeze_time("2022-06-11 12:50")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
def test_handle_transaction_request_task_with_missing_psp_reference(
    mocked_post_request,
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
):
    # given
    mocked_webhook_response.text = "{}"
    mocked_webhook_response.content = "{}"
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    event = transaction_item_created_by_app.events.create(
        status=TransactionEventStatus.REQUEST
    )
    app = transaction_item_created_by_app.app
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REQUEST)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REQUEST,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, app.name, transaction_data.event.id)

    # then
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.FAILURE).count()
        == 1
    )
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.REQUEST).count()
        == 1
    )
    failure_event = TransactionEvent.objects.filter(
        status=TransactionEventStatus.FAILURE
    ).first()
    event.refresh_from_db()
    assert event.psp_reference is None
    assert failure_event.type == event.type
    assert failure_event.amount_value == event.amount_value
    assert failure_event.transaction_id == event.transaction_id
    mocked_post_request.assert_called_once_with(
        target_url, data=payload.encode("utf-8"), headers=mock.ANY, timeout=mock.ANY
    )


@freeze_time("2022-06-11 12:50")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
def test_handle_transaction_request_task_with_missing_required_event_field(
    mocked_post_request,
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
):
    # given
    expected_psp_reference = "psp:123:111"
    mocked_webhook_response.text = json.dumps(
        {"pspReference": expected_psp_reference, "event": {"amount": 12.00}}
    )
    mocked_webhook_response.content = json.dumps(
        {"pspReference": expected_psp_reference, "event": {"amount": 12.00}}
    )
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    event = transaction_item_created_by_app.events.create(
        status=TransactionEventStatus.REQUEST
    )
    app = transaction_item_created_by_app.app
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REQUEST)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REQUEST,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, app.name, transaction_data.event.id)

    # then
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.FAILURE).count()
        == 1
    )
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.REQUEST).count()
        == 1
    )
    failure_event = TransactionEvent.objects.filter(
        status=TransactionEventStatus.FAILURE
    ).first()
    event.refresh_from_db()
    assert event.psp_reference is None
    assert failure_event.type == event.type
    assert failure_event.amount_value == event.amount_value
    assert failure_event.transaction_id == event.transaction_id
    mocked_post_request.assert_called_once_with(
        target_url, data=payload.encode("utf-8"), headers=mock.ANY, timeout=mock.ANY
    )


@freeze_time("2022-06-11 12:50")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
def test_handle_transaction_request_task_with_result_event(
    mocked_post_request,
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
):
    # given
    request_psp_reference = "psp:123:111"
    event_amount = 12.00
    event_type = TransactionEventActionType.CHARGE
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_name = "Charge event"
    event_cause = "No cause"
    event_psp_reference = "psp:111:111"

    response_payload = {
        "pspReference": request_psp_reference,
        "event": {
            "pspReference": event_psp_reference,
            "result": TransactionEventReportResult.SUCCESS.upper(),
            "amount": event_amount,
            "type": event_type.upper(),
            "time": event_time,
            "externalUrl": event_url,
            "name": event_name,
            "cause": event_cause,
        },
    }
    mocked_webhook_response.text = json.dumps(response_payload)
    mocked_webhook_response.content = json.dumps(response_payload)
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    request_event = transaction_item_created_by_app.events.create(
        status=TransactionEventStatus.REQUEST
    )
    app = transaction_item_created_by_app.app
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REQUEST)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=request_event,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REQUEST,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, app.name, transaction_data.event.id)

    # then
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.FAILURE).count()
        == 0
    )
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.REQUEST).count()
        == 1
    )
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.SUCCESS).count()
        == 1
    )
    success_event = TransactionEvent.objects.filter(
        status=TransactionEventStatus.SUCCESS
    ).first()
    request_event.refresh_from_db()
    assert request_event.psp_reference == request_psp_reference
    assert success_event.type == event_type
    assert success_event.psp_reference == event_psp_reference
    assert success_event.amount_value == event_amount
    assert success_event.created_at.isoformat() == event_time
    assert success_event.external_url == event_url
    assert success_event.name == event_name
    assert success_event.cause == event_cause

    mocked_post_request.assert_called_once_with(
        target_url, data=payload.encode("utf-8"), headers=mock.ANY, timeout=mock.ANY
    )


@freeze_time("2022-06-11T17:50:00+00:00")
@mock.patch("saleor.plugins.webhook.tasks.requests.post")
def test_handle_transaction_request_task_with_only_required_fields_for_result_event(
    mocked_post_request,
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
):
    # given
    request_psp_reference = "psp:123:111"
    event_psp_reference = "psp:111:111"

    response_payload = {
        "pspReference": request_psp_reference,
        "event": {
            "pspReference": event_psp_reference,
            "result": TransactionEventReportResult.SUCCESS.upper(),
        },
    }
    mocked_webhook_response.text = json.dumps(response_payload)
    mocked_webhook_response.content = json.dumps(response_payload)
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    request_event = transaction_item_created_by_app.events.create(
        status=TransactionEventStatus.REQUEST
    )
    app = transaction_item_created_by_app.app
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REQUEST)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=request_event,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REQUEST,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, app.name, transaction_data.event.id)

    # then
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.FAILURE).count()
        == 0
    )
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.REQUEST).count()
        == 1
    )
    assert (
        TransactionEvent.objects.filter(status=TransactionEventStatus.SUCCESS).count()
        == 1
    )
    success_event = TransactionEvent.objects.filter(
        status=TransactionEventStatus.SUCCESS
    ).first()
    request_event.refresh_from_db()
    assert request_event.psp_reference == request_psp_reference
    assert success_event.type == request_event.type
    assert success_event.psp_reference == event_psp_reference
    assert success_event.amount_value == request_event.amount_value
    assert success_event.created_at == timezone.now()
    assert success_event.external_url == ""
    assert success_event.name == ""
    assert success_event.cause == ""

    mocked_post_request.assert_called_once_with(
        target_url, data=payload.encode("utf-8"), headers=mock.ANY, timeout=mock.ANY
    )
