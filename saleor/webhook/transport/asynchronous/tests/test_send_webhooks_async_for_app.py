from threading import Event
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings
from freezegun import freeze_time

from .....app.models import AppWebhookMutex
from .....core.models import EventDelivery, EventDeliveryAttempt, EventDeliveryStatus
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook
from ...utils import get_pending_delivery_requests
from ..transport import (
    MAX_WEBHOOK_RETRIES,
    WebhookResponse,
    execute_webhook_requests,
    send_webhooks_async_for_app,
)


@pytest.fixture
def app_webhook_mutex(app):
    return AppWebhookMutex.objects.create(app=app)


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
@patch("saleor.webhook.transport.asynchronous.transport.record_external_request")
@patch(
    "saleor.webhook.transport.asynchronous.transport.record_first_delivery_attempt_delay"
)
@patch("saleor.webhook.transport.asynchronous.transport.webhooks_otel_trace")
def test_send_webhooks_async_for_app(
    mock_webhooks_otel_trace,
    mock_record_first_delivery_attempt_delay,
    mock_record_external_request,
    mock_send_prepared_webhook_request_using_http,
    app,
    app_webhook_mutex,
    event_delivery,
):
    # given
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()
    mock_send_prepared_webhook_request_using_http.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.SUCCESS
    )

    # when
    send_webhooks_async_for_app(
        app_id=app.id, telemetry_context=MagicMock(), concurrency=1
    )
    app_webhook_mutex.refresh_from_db()

    # then
    mock_send_prepared_webhook_request_using_http.assert_called_once()
    mock_record_external_request.assert_called_once()
    mock_record_first_delivery_attempt_delay.assert_called_once()
    mock_webhooks_otel_trace.assert_called_once()

    # deliveries should be cleared
    assert not EventDelivery.objects.exists()


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_send_webhooks_async_for_app_no_deliveries(
    mock_send_prepared_webhook_request_using_http, settings, app
):
    # given
    assert not EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()

    # when
    send_webhooks_async_for_app(
        app_id=app.id, telemetry_context=MagicMock(), concurrency=1
    )

    # then
    assert mock_send_prepared_webhook_request_using_http.called == 0


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_send_webhooks_async_for_app_skips_failed_deliveries(
    mock_send_prepared_webhook_request_using_http,
    app,
    app_webhook_mutex,
    event_delivery,
):
    # given
    event_delivery.status = EventDeliveryStatus.FAILED
    event_delivery.save()
    assert not EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()

    # when
    send_webhooks_async_for_app(app_id=app.id, concurrency=1)

    # then
    assert mock_send_prepared_webhook_request_using_http.called == 0


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_send_webhooks_async_for_app_skips_deliveries_without_payload(
    mock_send_prepared_webhook_request_using_http,
    app,
    event_delivery,
):
    # given
    event_delivery.payload = None
    event_delivery.save()

    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()

    # when
    send_webhooks_async_for_app(
        app_id=app.id, telemetry_context=MagicMock(), concurrency=1
    )

    # then
    mock_send_prepared_webhook_request_using_http.assert_not_called()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.PENDING
    assert not EventDeliveryAttempt.objects.exists()


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_send_webhooks_async_for_app_skips_inactive_webhooks(
    mock_send_prepared_webhook_request_using_http,
    app,
    event_delivery,
):
    # given
    webhook = event_delivery.webhook
    webhook.is_active = False
    webhook.save()

    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()

    # when
    send_webhooks_async_for_app(
        app_id=app.id, telemetry_context=MagicMock(), concurrency=1
    )

    # then
    mock_send_prepared_webhook_request_using_http.assert_not_called()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.PENDING
    assert not EventDeliveryAttempt.objects.exists()


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_send_webhooks_async_for_app_failed_status(
    mock_send_prepared_webhook_request_using_http,
    app,
    event_delivery,
):
    # given
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()
    mock_send_prepared_webhook_request_using_http.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.FAILED
    )

    # when
    send_webhooks_async_for_app(
        app_id=app.id, telemetry_context=MagicMock(), concurrency=1
    )

    # then
    mock_send_prepared_webhook_request_using_http.assert_called_once()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.PENDING
    assert EventDeliveryAttempt.objects.filter(
        status=EventDeliveryStatus.FAILED
    ).exists()


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
@patch("saleor.webhook.transport.asynchronous.transport.record_external_request")
@patch(
    "saleor.webhook.transport.asynchronous.transport.record_first_delivery_attempt_delay"
)
@patch("saleor.webhook.transport.asynchronous.transport.webhooks_otel_trace")
def test_send_multiple_webhooks_async_for_app(
    mock_webhooks_otel_trace,
    mock_record_first_delivery_attempt_delay,
    mock_record_external_request,
    mock_send_prepared_webhook_request_using_http,
    app,
    event_deliveries,
):
    # given
    assert len(EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING)) == 3
    mock_send_prepared_webhook_request_using_http.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.SUCCESS
    )

    # when
    send_webhooks_async_for_app(
        app_id=app.id, telemetry_context=MagicMock(), concurrency=1
    )

    # then
    assert mock_send_prepared_webhook_request_using_http.call_count == 3
    assert mock_record_external_request.call_count == 3
    assert mock_record_first_delivery_attempt_delay.call_count == 3
    assert mock_webhooks_otel_trace.call_count == 3

    # deliveries should be cleared
    assert not EventDelivery.objects.exists()


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
@patch("saleor.webhook.transport.asynchronous.transport.record_external_request")
@patch(
    "saleor.webhook.transport.asynchronous.transport.record_first_delivery_attempt_delay"
)
@patch("saleor.webhook.transport.asynchronous.transport.webhooks_otel_trace")
def test_send_multiple_webhooks_async_for_app_retry_on_failure(
    mock_webhooks_otel_trace,
    mock_record_first_delivery_attempt_delay,
    mock_record_external_request,
    mock_send_prepared_webhook_request_using_http,
    app,
    event_deliveries,
):
    # given
    deliveries = EventDelivery.objects.order_by("created_at").all()
    assert len(deliveries) == 3
    assert all(d.status == EventDeliveryStatus.PENDING for d in deliveries)

    mock_send_prepared_webhook_request_using_http.side_effect = [
        WebhookResponse(content="", status=EventDeliveryStatus.SUCCESS),
        WebhookResponse(content="", status=EventDeliveryStatus.FAILED),
        WebhookResponse(content="", status=EventDeliveryStatus.SUCCESS),
        WebhookResponse(content="", status=EventDeliveryStatus.SUCCESS),
    ]

    # when
    send_webhooks_async_for_app(
        app_id=app.id, telemetry_context=MagicMock(), concurrency=1
    )

    # then
    # execute only first two attempts (stop on failure during second attempt)
    assert mock_send_prepared_webhook_request_using_http.call_count == 2
    assert mock_record_external_request.call_count == 2
    assert mock_record_first_delivery_attempt_delay.call_count == 2
    assert mock_webhooks_otel_trace.call_count == 2

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
    send_webhooks_async_for_app(
        app_id=app.id, telemetry_context=MagicMock(), concurrency=1
    )

    # then
    # record all four webhooks calls
    assert mock_send_prepared_webhook_request_using_http.call_count == 4
    assert mock_record_external_request.call_count == 4
    assert mock_webhooks_otel_trace.call_count == 4

    # measure only first attempt delay
    assert mock_record_first_delivery_attempt_delay.call_count == 3


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_send_webhooks_async_for_app_last_retry_failed(
    mock_send_prepared_webhook_request_using_http,
    app,
    event_delivery,
):
    # given
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()
    EventDeliveryAttempt.objects.bulk_create(
        [
            EventDeliveryAttempt(
                delivery=event_delivery, status=EventDeliveryStatus.FAILED
            )
            for _ in range(MAX_WEBHOOK_RETRIES)
        ]
    )
    mock_send_prepared_webhook_request_using_http.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.FAILED
    )

    # when
    send_webhooks_async_for_app(app_id=app.id, concurrency=1)

    # then
    mock_send_prepared_webhook_request_using_http.assert_called_once()
    deliveries = EventDelivery.objects.all()
    assert len(deliveries) == 1
    assert deliveries[0].status == EventDeliveryStatus.FAILED
    assert (
        len(EventDeliveryAttempt.objects.filter(status=EventDeliveryStatus.FAILED))
        == MAX_WEBHOOK_RETRIES + 1
    )


@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_send_webhooks_async_for_app_last_retry_succeeds(
    mock_send_prepared_webhook_request_using_http,
    app,
    event_delivery,
):
    # given
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).exists()
    EventDeliveryAttempt.objects.bulk_create(
        [
            EventDeliveryAttempt(
                delivery=event_delivery, status=EventDeliveryStatus.FAILED
            )
            for _ in range(MAX_WEBHOOK_RETRIES)
        ]
    )
    mock_send_prepared_webhook_request_using_http.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.SUCCESS
    )

    # when
    send_webhooks_async_for_app(app_id=app.id, concurrency=1)

    # then
    mock_send_prepared_webhook_request_using_http.assert_called_once()

    assert not EventDelivery.objects.exists()
    assert not EventDeliveryAttempt.objects.exists()


@override_settings(WEBHOOK_ASYNC_BATCH_TIMEOUT=10)
@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_execute_webhook_requests_stops_mid_batch_on_soft_timeout(
    mock_send_prepared_webhook_request_using_http,
    app,
    event_deliveries,
):
    # given
    with freeze_time("2024-01-01 12:00:00", tick=False) as frozen_time:

        def succeed_then_advance_past_timeout(*args, **kwargs):
            # advance past WEBHOOK_ASYNC_BATCH_TIMEOUT after the first request,
            # so the next loop guard breaks the loop
            frozen_time.tick(delta=11)
            return WebhookResponse(content="", status=EventDeliveryStatus.SUCCESS)

        mock_send_prepared_webhook_request_using_http.side_effect = (
            succeed_then_advance_past_timeout
        )

        http_requests, _ = get_pending_delivery_requests(
            domain="example.com",
            app_id=app.id,
            session=MagicMock(),
            batch_size=10,
        )
        assert http_requests.qsize() == 3
        results: list = []

        # when
        execute_webhook_requests(
            thread_id=0,
            queue=http_requests,
            results=results,
            deadline_exceeded_event=Event(),
            telemetry_context=MagicMock(),
        )

    # then
    # exactly one delivery was processed before the timeout broke the loop
    assert mock_send_prepared_webhook_request_using_http.call_count == 1
    assert len(results) == 1
    # the remaining deliveries stay queued for a later batch
    assert http_requests.qsize() == 2


@override_settings(WEBHOOK_ASYNC_MAX_CONCURRENCY=1)
@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_execute_webhook_requests_stops_on_failure_when_concurrency_is_one(
    mock_send_prepared_webhook_request_using_http,
    app,
    event_deliveries,
):
    # given
    mock_send_prepared_webhook_request_using_http.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.FAILED
    )
    http_requests, _ = get_pending_delivery_requests(
        domain="example.com",
        app_id=app.id,
        session=MagicMock(),
        batch_size=10,
    )
    assert http_requests.qsize() == 3
    results: list = []

    # when
    execute_webhook_requests(
        thread_id=0,
        queue=http_requests,
        results=results,
        deadline_exceeded_event=Event(),
        telemetry_context=MagicMock(),
    )

    # then
    # with concurrency 1 deliveries are processed in chronological order, so a
    # failure must stop the thread to preserve ordering on the next batch
    assert mock_send_prepared_webhook_request_using_http.call_count == 1
    assert len(results) == 1
    assert http_requests.qsize() == 2


@override_settings(WEBHOOK_ASYNC_MAX_CONCURRENCY=2)
@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_execute_webhook_requests_continues_on_failure_when_concurrency_above_one(
    mock_send_prepared_webhook_request_using_http,
    app,
    event_deliveries,
):
    # given
    mock_send_prepared_webhook_request_using_http.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.FAILED
    )
    http_requests, _ = get_pending_delivery_requests(
        domain="example.com",
        app_id=app.id,
        session=MagicMock(),
        batch_size=10,
    )
    assert http_requests.qsize() == 3
    results: list = []

    # when
    execute_webhook_requests(
        thread_id=0,
        queue=http_requests,
        results=results,
        deadline_exceeded_event=Event(),
        telemetry_context=MagicMock(),
    )

    # then
    # with concurrency greater than 1 ordering is not guaranteed, so a failed delivery must
    # not stop the thread - it keeps draining the queue
    assert mock_send_prepared_webhook_request_using_http.call_count == 3
    assert len(results) == 3
    assert http_requests.empty()


@pytest.fixture
def sqs_webhook(app):
    return Webhook.objects.create(
        name="SQS webhook",
        app=app,
        target_url=(
            "awssqs://access_key:secret@sqs.us-east-1.amazonaws.com/account_id/queue"
        ),
    )


@pytest.fixture
def sqs_event_delivery(event_payload, sqs_webhook):
    return EventDelivery.objects.create(
        event_type=WebhookEventAsyncType.ANY,
        payload=event_payload,
        webhook=sqs_webhook,
    )


@override_settings(WEBHOOK_ASYNC_MAX_CONCURRENCY=2)
@patch("saleor.webhook.transport.utils.boto3.client")
@patch("saleor.webhook.transport.utils.send_prepared_webhook_request_using_http")
def test_send_webhooks_async_for_app_processes_http_and_non_http(
    mock_send_prepared_webhook_request_using_http,
    mock_boto3_client,
    app,
    app_webhook_mutex,
    event_delivery,
    sqs_event_delivery,
):
    # given
    assert EventDelivery.objects.filter(status=EventDeliveryStatus.PENDING).count() == 2

    mock_send_prepared_webhook_request_using_http.return_value = WebhookResponse(
        content="", status=EventDeliveryStatus.SUCCESS
    )
    mock_sqs = MagicMock()
    mock_sqs.send_message.return_value = {"MessageId": "1"}
    mock_boto3_client.return_value = mock_sqs

    # when
    send_webhooks_async_for_app(
        app_id=app.id, telemetry_context=MagicMock(), concurrency=1
    )

    # then
    mock_send_prepared_webhook_request_using_http.assert_called_once()
    mock_sqs.send_message.assert_called_once()
    assert not EventDelivery.objects.exists()
