from unittest.mock import ANY, MagicMock, patch

from saleor.core.models import EventDelivery, EventDeliveryAttempt, EventDeliveryStatus
from saleor.webhook.transport.asynchronous.transport import (
    WebhookResponse,
    send_webhooks_async_for_app,
)


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@patch("saleor.webhook.transport.asynchronous.transport.record_async_webhooks_count")
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
    mock_record_async_webhooks_count,
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

    # when
    send_webhooks_async_for_app(app_id=app.id, telemetry_context=MagicMock())

    # then
    mock_send_webhook_using_scheme_method.assert_called_once()
    mock_record_async_webhooks_count.assert_called_once()
    mock_record_first_delivery_attempt_delay.assert_called_once()
    mock_webhooks_otel_trace.assert_called_once()
    # get current lock uuid
    app_webhook_mutex.refresh_from_db()
    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={
            "app_id": app.id,
            "telemetry_context": ANY,
        },
        queue=settings.WEBHOOK_FIFO_QUEUE_NAME,
        MessageGroupId="core",
        MessageDeduplicationId=f"{app.id}-{app_webhook_mutex.uuid}",
        bind=True,
    )

    # deliveries should be cleared
    assert not EventDelivery.objects.exists()


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
def test_send_webhooks_async_for_app_no_deliveries(
    mock_send_webhook_using_scheme_method, settings, app, app_webhook_mutex
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
    event_delivery,
    app_webhook_mutex,
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

    # then
    mock_send_webhook_using_scheme_method.assert_not_called()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.PENDING
    assert EventDeliveryAttempt.objects.filter(
        status=EventDeliveryStatus.FAILED
    ).exists()

    # get current lock uuid
    app_webhook_mutex.refresh_from_db()
    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={
            "app_id": app.id,
            "telemetry_context": ANY,
        },
        queue=settings.WEBHOOK_FIFO_QUEUE_NAME,
        MessageGroupId="core",
        MessageDeduplicationId=f"{app.id}-{app_webhook_mutex.uuid}",
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

    # then
    mock_send_webhook_using_scheme_method.assert_called_once()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.PENDING
    assert EventDeliveryAttempt.objects.filter(
        status=EventDeliveryStatus.FAILED
    ).exists()

    # get current lock uuid
    app_webhook_mutex.refresh_from_db()
    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={
            "app_id": app.id,
            "telemetry_context": ANY,
        },
        queue=settings.WEBHOOK_FIFO_QUEUE_NAME,
        MessageGroupId="core",
        MessageDeduplicationId=f"{app.id}-{app_webhook_mutex.uuid}",
        bind=True,
    )


@patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_using_scheme_method"
)
@patch("saleor.webhook.transport.asynchronous.transport.record_async_webhooks_count")
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
    mock_record_async_webhooks_count,
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

    # then
    assert mock_send_webhook_using_scheme_method.call_count == 3
    assert mock_record_async_webhooks_count.call_count == 3
    assert mock_record_first_delivery_attempt_delay.call_count == 3
    assert mock_webhooks_otel_trace.call_count == 3
    # get current lock uuid
    app_webhook_mutex.refresh_from_db()
    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={
            "app_id": app.id,
            "telemetry_context": ANY,
        },
        queue=settings.WEBHOOK_FIFO_QUEUE_NAME,
        MessageGroupId="core",
        MessageDeduplicationId=f"{app.id}-{app_webhook_mutex.uuid}",
        bind=True,
    )

    # deliveries should be cleared
    assert not EventDelivery.objects.exists()


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

    # then
    mock_send_webhook_using_scheme_method.assert_called_once()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.FAILED
    assert (
        len(EventDeliveryAttempt.objects.filter(status=EventDeliveryStatus.FAILED)) == 6
    )

    # get current lock uuid
    app_webhook_mutex.refresh_from_db()
    mock_send_webhooks_async_for_app_apply_async.assert_called_once_with(
        kwargs={"app_id": app.id, "telemetry_context": ANY},
        queue=settings.WEBHOOK_FIFO_QUEUE_NAME,
        MessageGroupId="core",
        MessageDeduplicationId=f"{app.id}-{app_webhook_mutex.uuid}",
        bind=True,
    )
