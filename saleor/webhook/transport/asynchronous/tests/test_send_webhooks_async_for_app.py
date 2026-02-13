from unittest.mock import ANY, MagicMock, patch

import pytest

from saleor.app.models import AppWebhookMutex
from saleor.core.models import EventDelivery, EventDeliveryAttempt, EventDeliveryStatus
from saleor.webhook.transport.asynchronous.transport import (
    WebhookResponse,
    send_webhooks_async_for_app,
)


@pytest.fixture
def app_webhook_mutex(app):
    return AppWebhookMutex.objects.create(app=app)


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@patch("saleor.webhook.transport.asynchronous.transport.record_external_request")
@patch(
    "saleor.webhook.transport.asynchronous.transport.record_first_delivery_attempt_delay"
)
@patch("saleor.webhook.transport.asynchronous.transport.webhooks_otel_trace")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_send_webhooks_async_for_app(
    mock_send_webhooks_async_for_app_apply_async,
    mock_webhooks_otel_trace,
    mock_record_first_delivery_attempt_delay,
    mock_record_external_request,
    mock_send_webhook_using_scheme_method,
    settings,
    app,
    app_webhook_mutex,
    event_delivery,
):
    # given
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()
    mock_send_webhook_using_scheme_method.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.SUCCESS
    )
    lock_id = app_webhook_mutex.lock_id

    # when
    send_webhooks_async_for_app(app_id=app.id, telemetry_context=MagicMock())
    app_webhook_mutex.refresh_from_db()

    # then
    assert app_webhook_mutex.lock_id != lock_id
    mock_send_webhook_using_scheme_method.assert_called_once()
    mock_record_external_request.assert_called_once()
    mock_record_first_delivery_attempt_delay.assert_called_once()
    mock_webhooks_otel_trace.assert_called_once()
    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={
            "app_id": app.id,
            "telemetry_context": ANY,
        },
        queue=settings.WEBHOOK_BATCH_CELERY_QUEUE_NAME,
        MessageGroupId="example.com",
        MessageDeduplicationId=f"{app.id}:{app_webhook_mutex.lock_id}",
        bind=True,
    )

    # deliveries should be cleared
    assert not EventDelivery.objects.exists()


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhooks_async_for_app_no_deliveries(
    mock_send_webhook_using_scheme_method, settings, app
):
    # given
    assert not EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()

    # when
    send_webhooks_async_for_app(app_id=app.id, telemetry_context=MagicMock())

    # then
    assert mock_send_webhook_using_scheme_method.called == 0


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhooks_async_for_app_doesnt_pick_failed(
    mock_send_webhook_using_scheme_method,
    settings,
    app,
    app_webhook_mutex,
    event_delivery,
):
    # given
    event_delivery.status = EventDeliveryStatus.FAILED
    event_delivery.save()
    assert not EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()

    # when
    send_webhooks_async_for_app(app_id=app.id)

    # then
    assert mock_send_webhook_using_scheme_method.called == 0


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_send_webhooks_async_for_app_no_payload(
    mock_send_webhooks_async_for_app_apply_async,
    mock_send_webhook_using_scheme_method,
    settings,
    app,
    app_webhook_mutex,
    event_delivery,
):
    # given
    event_delivery.payload = None
    event_delivery.save()

    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()

    # when
    send_webhooks_async_for_app(app_id=app.id, telemetry_context=MagicMock())
    app_webhook_mutex.refresh_from_db()

    # then
    mock_send_webhook_using_scheme_method.assert_not_called()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.PENDING
    assert EventDeliveryAttempt.objects.filter(
        status=EventDeliveryStatus.FAILED
    ).exists()

    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={
            "app_id": app.id,
            "telemetry_context": ANY,
        },
        queue=settings.WEBHOOK_BATCH_CELERY_QUEUE_NAME,
        MessageGroupId="example.com",
        MessageDeduplicationId=f"{app.id}:{app_webhook_mutex.lock_id}",
        bind=True,
    )


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_send_webhooks_async_for_app_failed_status(
    mock_send_webhooks_async_for_app_apply_async,
    mock_send_webhook_using_scheme_method,
    settings,
    app,
    app_webhook_mutex,
    event_delivery,
):
    # given
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()
    mock_send_webhook_using_scheme_method.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.FAILED
    )

    # when
    send_webhooks_async_for_app(app_id=app.id, telemetry_context=MagicMock())
    app_webhook_mutex.refresh_from_db()

    # then
    mock_send_webhook_using_scheme_method.assert_called_once()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.PENDING
    assert EventDeliveryAttempt.objects.filter(
        status=EventDeliveryStatus.FAILED
    ).exists()

    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={
            "app_id": app.id,
            "telemetry_context": ANY,
        },
        queue=settings.WEBHOOK_BATCH_CELERY_QUEUE_NAME,
        MessageGroupId="example.com",
        MessageDeduplicationId=f"{app.id}:{app_webhook_mutex.lock_id}",
        bind=True,
    )


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@patch("saleor.webhook.transport.asynchronous.transport.record_external_request")
@patch(
    "saleor.webhook.transport.asynchronous.transport.record_first_delivery_attempt_delay"
)
@patch("saleor.webhook.transport.asynchronous.transport.webhooks_otel_trace")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_send_multiple_webhooks_async_for_app(
    mock_send_webhooks_async_for_app_apply_async,
    mock_webhooks_otel_trace,
    mock_record_first_delivery_attempt_delay,
    mock_record_external_request,
    mock_send_webhook_using_scheme_method,
    settings,
    app,
    app_webhook_mutex,
    event_deliveries,
):
    # given
    assert len(EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING)) == 3
    mock_send_webhook_using_scheme_method.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.SUCCESS
    )

    # when
    send_webhooks_async_for_app(app_id=app.id, telemetry_context=MagicMock())
    app_webhook_mutex.refresh_from_db()

    # then
    assert mock_send_webhook_using_scheme_method.call_count == 3
    assert mock_record_external_request.call_count == 3
    assert mock_record_first_delivery_attempt_delay.call_count == 3
    assert mock_webhooks_otel_trace.call_count == 3
    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={
            "app_id": app.id,
            "telemetry_context": ANY,
        },
        queue=settings.WEBHOOK_BATCH_CELERY_QUEUE_NAME,
        MessageGroupId="example.com",
        MessageDeduplicationId=f"{app.id}:{app_webhook_mutex.lock_id}",
        bind=True,
    )

    # deliveries should be cleared
    assert not EventDelivery.objects.exists()


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@patch("saleor.webhook.transport.asynchronous.transport.record_external_request")
@patch(
    "saleor.webhook.transport.asynchronous.transport.record_first_delivery_attempt_delay"
)
@patch("saleor.webhook.transport.asynchronous.transport.webhooks_otel_trace")
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async",
)
def test_send_multiple_webhooks_async_for_app_retry_on_failure(
    mock_send_webhooks_async_for_app_apply_async,
    mock_webhooks_otel_trace,
    mock_record_first_delivery_attempt_delay,
    mock_record_external_request,
    mock_send_webhook_using_scheme_method,
    settings,
    app,
    app_webhook_mutex,
    event_deliveries,
):
    # given
    deliveries = EventDelivery.objects.order_by("created_at").all()
    assert len(deliveries) == 3
    assert all(d.status == EventDeliveryStatus.PENDING for d in deliveries)

    mock_send_webhook_using_scheme_method.side_effect = [
        WebhookResponse(content="", status=EventDeliveryStatus.SUCCESS),
        WebhookResponse(content="", status=EventDeliveryStatus.FAILED),
        WebhookResponse(content="", status=EventDeliveryStatus.SUCCESS),
        WebhookResponse(content="", status=EventDeliveryStatus.SUCCESS),
    ]

    # when
    send_webhooks_async_for_app(app_id=app.id, telemetry_context=MagicMock())
    app_webhook_mutex.refresh_from_db()

    # then
    # execute only first two attempts (stop on failure during second attempt)
    assert mock_send_webhook_using_scheme_method.call_count == 2
    assert mock_record_external_request.call_count == 2
    assert mock_record_first_delivery_attempt_delay.call_count == 2
    assert mock_webhooks_otel_trace.call_count == 2

    # trigger retry
    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={
            "app_id": app.id,
            "telemetry_context": ANY,
        },
        queue=settings.WEBHOOK_BATCH_CELERY_QUEUE_NAME,
        MessageGroupId="example.com",
        MessageDeduplicationId=f"{app.id}:{app_webhook_mutex.lock_id}",
        bind=True,
    )

    # successful deliveries should be cleared
    # failed or unexecuted delivery should remain pending
    remaining_deliveries = EventDelivery.objects.order_by("created_at").all()
    assert len(remaining_deliveries) == 2
    assert all(d.status == EventDeliveryStatus.PENDING for d in remaining_deliveries)
    assert remaining_deliveries[0].id == deliveries[1].id
    assert remaining_deliveries[1].id == deliveries[2].id

    # failed attempt should be recorded
    attempts = EventDeliveryAttempt.objects.all()
    assert len(attempts) == 1
    assert attempts[0].status == EventDeliveryStatus.FAILED
    assert attempts[0].delivery.id == deliveries[1].id

    # when retriggered
    send_webhooks_async_for_app(app_id=app.id, telemetry_context=MagicMock())
    mock_send_webhooks_async_for_app_apply_async.reset_mock()

    # then
    # record all four webhooks calls
    assert mock_send_webhook_using_scheme_method.call_count == 4
    assert mock_record_external_request.call_count == 4
    assert mock_webhooks_otel_trace.call_count == 4

    # measure only first attempt delay
    assert mock_record_first_delivery_attempt_delay.call_count == 3

    # do not schedule another retry
    mock_send_webhooks_async_for_app_apply_async.assert_not_called()


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhooks_async_for_app.apply_async"
)
def test_send_webhooks_async_for_app_last_retry_failed(
    mock_send_webhooks_async_for_app_apply_async,
    mock_send_webhook_using_scheme_method,
    settings,
    app,
    app_webhook_mutex,
    event_delivery,
):
    # given
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()
    EventDeliveryAttempt.objects.bulk_create(
        [
            EventDeliveryAttempt(
                delivery=event_delivery, status=EventDeliveryStatus.FAILED
            )
            for _ in range(5)
        ]
    )
    mock_send_webhook_using_scheme_method.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.FAILED
    )

    # when
    send_webhooks_async_for_app(app_id=app.id)
    app_webhook_mutex.refresh_from_db()

    # then
    mock_send_webhook_using_scheme_method.assert_called_once()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.FAILED
    assert (
        len(EventDeliveryAttempt.objects.filter(status=EventDeliveryStatus.FAILED)) == 6
    )

    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={"app_id": app.id, "telemetry_context": ANY},
        queue=settings.WEBHOOK_BATCH_CELERY_QUEUE_NAME,
        MessageGroupId="example.com",
        MessageDeduplicationId=f"{app.id}:{app_webhook_mutex.lock_id}",
        bind=True,
    )
