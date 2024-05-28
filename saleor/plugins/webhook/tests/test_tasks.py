import json
from decimal import Decimal
from unittest import mock

import pytest
from django.utils import timezone
from freezegun import freeze_time
from graphene import Node
from requests_hardened import HTTPSession

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....payment import TransactionEventType
from ....payment.interface import TransactionActionData
from ....payment.models import TransactionEvent
from ....payment.transaction_item_calculations import recalculate_transaction_amounts
from ....tests.utils import flush_post_commit_hooks
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.payloads import generate_transaction_action_request_payload
from ....webhook.transport.synchronous.transport import handle_transaction_request_task
from ....webhook.transport.utils import trigger_transaction_request


@pytest.fixture
def mocked_webhook_response():
    mocked_post_response = mock.Mock()
    mocked_post_response.text = json.dumps({"pspReference": "123"})
    mocked_post_response.headers = []
    mocked_post_response.status_code = 200
    mocked_post_response.ok = True
    mocked_post_response.content = json.dumps({"pspReference": "123"})
    mocked_post_response.elapsed.total_seconds = lambda: 1  # noqa: E731
    return mocked_post_response


@freeze_time("2022-06-11 12:50")
@mock.patch(
    "saleor.webhook.transport.synchronous."
    "transport.handle_transaction_request_task.delay"
)
def test_trigger_transaction_request(
    mocked_task,
    transaction_item_created_by_app,
    staff_user,
    permission_manage_payments,
    app,
):
    # given
    event = transaction_item_created_by_app.events.create(
        type=TransactionEventType.REFUND_REQUEST
    )
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook", is_active=True, target_url="http://localhost:3000/"
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=app,
    )

    # when
    trigger_transaction_request(
        transaction_data, WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED, staff_user
    )

    # then
    flush_post_commit_hooks()
    generated_payload = EventPayload.objects.first()
    generated_delivery = EventDelivery.objects.first()

    assert generated_payload.payload == generate_transaction_action_request_payload(
        transaction_data, staff_user
    )
    assert generated_delivery.status == EventDeliveryStatus.PENDING
    assert (
        generated_delivery.event_type
        == WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    assert generated_delivery.webhook == webhook
    assert generated_delivery.payload == generated_payload

    mocked_task.assert_called_once_with(generated_delivery.id, event.id)


@freeze_time("2022-06-11 12:50")
@mock.patch(
    "saleor.webhook.transport.synchronous."
    "transport.handle_transaction_request_task.delay"
)
def test_trigger_transaction_request_with_webhook_subscription(
    mocked_task,
    transaction_item_created_by_app,
    staff_user,
    permission_manage_payments,
    app,
):
    # given
    subscription = """
    subscription{
        event{
            ...on TransactionRefundRequested{
                transaction{
                    id
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
        type=TransactionEventType.REFUND_REQUEST
    )
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url="http://localhost:3000/",
        subscription_query=subscription,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=app,
    )

    # when
    trigger_transaction_request(
        transaction_data, WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED, staff_user
    )

    # then
    flush_post_commit_hooks()
    generated_payload = EventPayload.objects.first()
    generated_delivery = EventDelivery.objects.first()

    assert generated_payload
    assert generated_delivery
    assert json.loads(generated_payload.payload) == {
        "transaction": {
            "id": Node.to_global_id(
                "TransactionItem", transaction_data.transaction.token
            ),
        },
        "action": {"amount": 10.0, "actionType": "REFUND"},
    }
    assert generated_delivery.status == EventDeliveryStatus.PENDING
    assert (
        generated_delivery.event_type
        == WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED
    )
    assert generated_delivery.webhook == webhook

    assert generated_delivery.payload == generated_payload

    mocked_task.assert_called_once_with(generated_delivery.id, event.id)


@freeze_time("2022-06-11 12:50")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.handle_transaction_request_task.delay"
)
def test_trigger_transaction_request_missing_app_owner_updates_refundable_checkout(
    mocked_task,
    transaction_item_created_by_app,
    staff_user,
    permission_manage_payments,
    app,
    checkout,
):
    # given
    subscription = """
    subscription{
        event{
            ...on TransactionRefundRequested{
                transaction{
                    id
                }
                action{
                    amount
                    actionType
                }
            }
        }
    }
    """
    checkout.automatically_refundable = True
    checkout.save()

    transaction_item_created_by_app.order = None
    transaction_item_created_by_app.checkout = checkout
    transaction_item_created_by_app.save()
    event = transaction_item_created_by_app.events.create(
        type=TransactionEventType.REFUND_REQUEST
    )

    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url="http://localhost:3000/",
        subscription_query=subscription,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=None,
    )

    # when
    trigger_transaction_request(
        transaction_data, WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED, staff_user
    )

    # then
    checkout.refresh_from_db()
    transaction_item_created_by_app.refresh_from_db()
    assert checkout.automatically_refundable is False
    assert transaction_item_created_by_app.last_refund_success is False
    assert not mocked_task.called


@freeze_time("2022-06-11 12:50")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.handle_transaction_request_task.delay"
)
def test_trigger_transaction_request_missing_webhook_updates_refundable_checkout(
    mocked_task,
    transaction_item_created_by_app,
    staff_user,
    permission_manage_payments,
    app,
    checkout,
):
    # given
    checkout.automatically_refundable = True
    checkout.save()

    transaction_item_created_by_app.order = None
    transaction_item_created_by_app.checkout = checkout
    transaction_item_created_by_app.save()
    event = transaction_item_created_by_app.events.create(
        type=TransactionEventType.REFUND_REQUEST
    )

    app.permissions.set([permission_manage_payments])

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=app,
    )

    # when
    trigger_transaction_request(
        transaction_data, WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED, staff_user
    )

    # then
    checkout.refresh_from_db()
    transaction_item_created_by_app.refresh_from_db()
    assert checkout.automatically_refundable is False
    assert transaction_item_created_by_app.last_refund_success is False
    assert not mocked_task.called


@freeze_time("2022-06-11 12:50")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.handle_transaction_request_task.delay"
)
def test_trigger_transaction_request_incorrect_subscription_updates_refundable_checkout(
    mocked_task,
    transaction_item_created_by_app,
    staff_user,
    permission_manage_payments,
    app,
    checkout,
):
    # given
    subscription = """
        subscription{
            event{
                ...on TransactionRefundRequested{
                    transaction{
                        id
                        incorrectField
                    }
                    action{
                        amount
                        actionType
                    }
                }
            }
        }
        """
    checkout.automatically_refundable = True
    checkout.save()

    transaction_item_created_by_app.order = None
    transaction_item_created_by_app.checkout = checkout
    transaction_item_created_by_app.save()
    event = transaction_item_created_by_app.events.create(
        type=TransactionEventType.REFUND_REQUEST
    )

    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url="http://localhost:3000/",
        subscription_query=subscription,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=app,
    )

    # when
    trigger_transaction_request(
        transaction_data, WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED, staff_user
    )

    # then
    checkout.refresh_from_db()
    transaction_item_created_by_app.refresh_from_db()
    assert checkout.automatically_refundable is False
    assert transaction_item_created_by_app.last_refund_success is False
    assert not mocked_task.called


@freeze_time("2022-06-11 12:50")
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_missing_delivery_updates_refundable_checkout(
    mocked_post_request,
    transaction_item_generator,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
    checkout,
):
    # given
    checkout.automatically_refundable = True
    checkout.save()

    transaction = transaction_item_generator(checkout_id=checkout.pk)
    expected_psp_reference = "psp:ref:123"
    mocked_webhook_response.text = json.dumps({"pspReference": expected_psp_reference})
    mocked_webhook_response.content = json.dumps(
        {"pspReference": expected_psp_reference}
    )
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    event = transaction.events.create(type=TransactionEventType.REFUND_REQUEST)
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )
    delivery_id = delivery.id

    delivery.delete()

    # when
    handle_transaction_request_task(delivery_id, transaction_data.event.id)

    # then
    checkout.refresh_from_db()
    transaction.refresh_from_db()

    assert checkout.automatically_refundable is False
    assert transaction.last_refund_success is False
    assert not mocked_post_request.called


@freeze_time("2022-06-11 12:50")
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_with_only_psp_reference(
    mocked_post_request,
    transaction_item_generator,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
):
    # given
    transaction = transaction_item_generator()
    expected_psp_reference = "psp:ref:123"
    mocked_webhook_response.text = json.dumps({"pspReference": expected_psp_reference})
    mocked_webhook_response.content = json.dumps(
        {"pspReference": expected_psp_reference}
    )
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    event = transaction.events.create(type=TransactionEventType.REFUND_REQUEST)
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, transaction_data.event.id)

    # then
    assert TransactionEvent.objects.count() == 1
    event.refresh_from_db()
    assert event.psp_reference == expected_psp_reference
    mocked_post_request.assert_called_once_with(
        "POST",
        target_url,
        data=payload.encode("utf-8"),
        headers=mock.ANY,
        timeout=mock.ANY,
        allow_redirects=False,
    )


@pytest.mark.parametrize("status_code", [500, 501, 510])
@freeze_time("2022-06-11 12:50")
@mock.patch("saleor.webhook.transport.synchronous.transport.handle_webhook_retry")
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_with_server_error(
    mocked_post_request,
    mocked_webhook_retry,
    status_code,
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
):
    # given
    mocked_webhook_response.status_code = status_code
    mocked_webhook_response.text = ""
    mocked_webhook_response.content = ""
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    event = transaction_item_created_by_app.events.create(
        type=TransactionEventType.CHARGE_REQUEST
    )
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, transaction_data.event.id)

    # then
    assert mocked_webhook_retry.called


@freeze_time("2022-06-11 12:50")
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_with_missing_psp_reference(
    mocked_post_request,
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
):
    # given
    mocked_webhook_response.text = "{}"
    mocked_webhook_response.content = "{}"
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    event = transaction_item_created_by_app.events.create(
        type=TransactionEventType.REFUND_REQUEST
    )
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, transaction_data.event.id)

    # then
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.REFUND_FAILURE
        ).count()
        == 1
    )
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.REFUND_REQUEST
        ).count()
        == 1
    )
    failure_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_FAILURE
    ).first()
    event.refresh_from_db()
    assert event.psp_reference is None
    assert failure_event.amount_value == event.amount_value
    assert failure_event.transaction_id == event.transaction_id
    mocked_post_request.assert_called_once_with(
        "POST",
        target_url,
        data=payload.encode("utf-8"),
        headers=mock.ANY,
        timeout=mock.ANY,
        allow_redirects=False,
    )


@freeze_time("2022-06-11 12:50")
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_with_missing_required_event_field(
    mocked_post_request,
    transaction_item_created_by_app,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
):
    # given
    expected_psp_reference = "psp:123:111"
    mocked_webhook_response.text = json.dumps(
        {"pspReference": expected_psp_reference, "amount": 12.00}
    )
    mocked_webhook_response.content = json.dumps(
        {"pspReference": expected_psp_reference, "amount": 12.00}
    )
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    event = transaction_item_created_by_app.events.create(
        type=TransactionEventType.REFUND_REQUEST
    )
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction_item_created_by_app,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, transaction_data.event.id)

    # then
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.REFUND_FAILURE
        ).count()
        == 1
    )
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.REFUND_REQUEST
        ).count()
        == 1
    )
    failure_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_FAILURE
    ).first()
    event.refresh_from_db()
    assert event.psp_reference is None
    assert failure_event.amount_value == event.amount_value
    assert failure_event.transaction_id == event.transaction_id
    mocked_post_request.assert_called_once_with(
        "POST",
        target_url,
        data=payload.encode("utf-8"),
        headers=mock.ANY,
        timeout=mock.ANY,
        allow_redirects=False,
    )


@freeze_time("2022-06-11 12:50")
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_with_result_event(
    mocked_post_request,
    transaction_item_generator,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
):
    # given
    transaction = transaction_item_generator()
    request_psp_reference = "psp:123:111"
    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_SUCCESS
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    response_payload = {
        "pspReference": request_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
    }
    mocked_webhook_response.text = json.dumps(response_payload)
    mocked_webhook_response.content = json.dumps(response_payload)
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    request_event = transaction.events.create(type=TransactionEventType.CHARGE_REQUEST)
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=request_event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, transaction_data.event.id)

    # then
    assert TransactionEvent.objects.all().count() == 2
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.CHARGE_REQUEST
        ).count()
        == 1
    )
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.CHARGE_SUCCESS
        ).count()
        == 1
    )
    success_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert success_event
    request_event.refresh_from_db()
    assert request_event.psp_reference == request_psp_reference
    assert success_event.psp_reference == request_psp_reference
    assert success_event.amount_value == event_amount
    assert success_event.created_at.isoformat() == event_time
    assert success_event.external_url == event_url
    assert success_event.message == event_cause

    mocked_post_request.assert_called_once_with(
        "POST",
        target_url,
        data=payload.encode("utf-8"),
        headers=mock.ANY,
        timeout=mock.ANY,
        allow_redirects=False,
    )


@freeze_time("2022-06-11T17:50:00+00:00")
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_with_only_required_fields_for_result_event(
    mocked_post_request,
    transaction_item_generator,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
):
    # given
    transaction = transaction_item_generator()
    request_psp_reference = "psp:123:111"

    request_event = transaction.events.create(type=TransactionEventType.REFUND_REQUEST)

    response_payload = {
        "pspReference": request_psp_reference,
        "result": TransactionEventType.REFUND_SUCCESS.upper(),
        "amount": str(request_event.amount_value),
    }
    mocked_webhook_response.text = json.dumps(response_payload)
    mocked_webhook_response.content = json.dumps(response_payload)
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=request_event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, transaction_data.event.id)

    # then
    assert TransactionEvent.objects.all().count() == 2
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.REFUND_REQUEST
        ).count()
        == 1
    )
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.REFUND_SUCCESS
        ).count()
        == 1
    )
    success_event = TransactionEvent.objects.filter(
        type=TransactionEventType.REFUND_SUCCESS
    ).first()
    request_event.refresh_from_db()
    assert success_event
    assert request_event.psp_reference == request_psp_reference
    assert success_event.type == TransactionEventType.REFUND_SUCCESS
    assert success_event.psp_reference == request_psp_reference
    assert success_event.amount_value == request_event.amount_value
    assert success_event.created_at == timezone.now()
    assert success_event.external_url == ""
    assert success_event.message == ""

    mocked_post_request.assert_called_once_with(
        "POST",
        target_url,
        data=payload.encode("utf-8"),
        headers=mock.ANY,
        timeout=mock.ANY,
        allow_redirects=False,
    )


@freeze_time("2022-06-11 12:50")
@mock.patch(
    "saleor.payment.utils.recalculate_transaction_amounts",
    wraps=recalculate_transaction_amounts,
)
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_calls_recalculation_of_amounts(
    mocked_post_request,
    mocked_recalculation,
    transaction_item_generator,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
):
    # given
    transaction = transaction_item_generator()
    request_psp_reference = "psp:123:111"
    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_SUCCESS
    event_time = "2022-11-18T13:25:58.169685+00:00"
    event_url = "http://localhost:3000/event/ref123"
    event_cause = "No cause"

    response_payload = {
        "pspReference": request_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "time": event_time,
        "externalUrl": event_url,
        "message": event_cause,
    }
    mocked_webhook_response.text = json.dumps(response_payload)
    mocked_webhook_response.content = json.dumps(response_payload)
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    request_event = transaction.events.create(type=TransactionEventType.CHARGE_REQUEST)
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type="charge",
        action_value=Decimal("12.00"),
        event=request_event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, transaction_data.event.id)

    # then
    mocked_recalculation.assert_called_once_with(transaction, save=False)
    transaction.refresh_from_db()
    assert transaction.charged_value == event_amount


@freeze_time("2022-06-11 12:50")
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_with_available_actions(
    mocked_post_request,
    transaction_item_generator,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
):
    # given
    transaction = transaction_item_generator()
    request_psp_reference = "psp:123:111"
    event_amount = 12.00
    event_type = TransactionEventType.CHARGE_SUCCESS

    response_payload = {
        "pspReference": request_psp_reference,
        "amount": event_amount,
        "result": event_type.upper(),
        "actions": ["CHARGE", "REFUND", "CANCEL", "VOID", "INCORRECT_EVENT"],
    }
    mocked_webhook_response.text = json.dumps(response_payload)
    mocked_webhook_response.content = json.dumps(response_payload)
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"

    request_event = transaction.events.create(type=TransactionEventType.CHARGE_REQUEST)
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type="refund",
        action_value=Decimal("10.00"),
        event=request_event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_CHARGE_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, transaction_data.event.id)

    # then
    assert TransactionEvent.objects.all().count() == 2
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.CHARGE_REQUEST
        ).count()
        == 1
    )
    assert (
        TransactionEvent.objects.filter(
            type=TransactionEventType.CHARGE_SUCCESS
        ).count()
        == 1
    )
    success_event = TransactionEvent.objects.filter(
        type=TransactionEventType.CHARGE_SUCCESS
    ).first()
    assert success_event
    request_event.refresh_from_db()
    assert request_event.psp_reference == request_psp_reference
    assert success_event.psp_reference == request_psp_reference
    assert success_event.amount_value == event_amount

    transaction.refresh_from_db()
    assert set(transaction.available_actions) == set(
        [
            "charge",
            "refund",
            "cancel",
        ]
    )

    mocked_post_request.assert_called_once_with(
        "POST",
        target_url,
        allow_redirects=False,
        data=payload.encode("utf-8"),
        headers=mock.ANY,
        timeout=mock.ANY,
    )


@freeze_time("2022-06-11 12:50")
@mock.patch.object(HTTPSession, "request")
def test_handle_transaction_request_task_request_event_included_in_calculations(
    mocked_post_request,
    transaction_item_generator,
    permission_manage_payments,
    staff_user,
    mocked_webhook_response,
    app,
):
    # given
    transaction = transaction_item_generator(charged_value=Decimal("100"))
    expected_psp_reference = "psp:ref:123"
    mocked_webhook_response.text = json.dumps({"pspReference": expected_psp_reference})
    mocked_webhook_response.content = json.dumps(
        {"pspReference": expected_psp_reference}
    )
    mocked_post_request.return_value = mocked_webhook_response

    target_url = "http://localhost:3000/"
    action_value = Decimal("10.00")

    event = transaction.events.create(
        type=TransactionEventType.REFUND_REQUEST, amount_value=action_value
    )
    app.permissions.set([permission_manage_payments])

    webhook = app.webhooks.create(
        name="webhook",
        is_active=True,
        target_url=target_url,
    )
    webhook.events.create(event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED)

    transaction_data = TransactionActionData(
        transaction=transaction,
        action_type="refund",
        action_value=action_value,
        event=event,
        transaction_app_owner=app,
    )

    payload = generate_transaction_action_request_payload(transaction_data, staff_user)
    event_payload = EventPayload.objects.create(payload=payload)
    delivery = EventDelivery.objects.create(
        status=EventDeliveryStatus.PENDING,
        event_type=WebhookEventSyncType.TRANSACTION_REFUND_REQUESTED,
        payload=event_payload,
        webhook=webhook,
    )

    # when
    handle_transaction_request_task(delivery.id, transaction_data.event.id)

    # then
    assert TransactionEvent.objects.count() == 2
    event.refresh_from_db()
    transaction.refresh_from_db()
    assert event.psp_reference == expected_psp_reference
    assert event.include_in_calculations is True

    assert transaction.amount_refund_pending.amount == action_value
    mocked_post_request.assert_called_once_with(
        "POST",
        target_url,
        data=payload.encode("utf-8"),
        headers=mock.ANY,
        timeout=mock.ANY,
        allow_redirects=False,
    )
