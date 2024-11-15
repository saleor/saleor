import datetime
import json
from unittest.mock import MagicMock, patch

import pytest
from celery import Task
from celery.exceptions import Retry
from celery.utils.threads import LocalStack

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventDeliveryAttempt
from ...event_types import WebhookEventAsyncType
from ..utils import (
    WebhookResponse,
    get_delivery_for_webhook,
    get_multiple_deliveries_for_webhooks,
    handle_webhook_retry,
    send_webhook_using_aws_sqs,
)


@pytest.fixture
def mocked_boto3_client_constructor():
    with patch("saleor.webhook.transport.utils.boto3.client") as mocked_constructor:
        yield mocked_constructor


@pytest.fixture
def sqs_response():
    return {
        "MD5OfMessageBody": "message-body-hash",
        "MD5OfMessageAttributes": "message-attributes-hash",
        "MD5OfMessageSystemAttributes": "message-system-attributes-hash",
        "MessageId": "message-id",
        "SequenceNumber": "sequence-number",
    }


@pytest.fixture
def mocked_boto3_client(mocked_boto3_client_constructor, sqs_response):
    mocked_client = MagicMock()
    mocked_client.send_message.return_value = sqs_response
    mocked_boto3_client_constructor.return_value = mocked_client
    return mocked_client


class DummyTask(Task):
    retry_backoff = 10
    retry_kwargs = {"max_retries": 2}
    request_stack = LocalStack()


def test_webhook_retry(webhook, event_delivery):
    # given
    attempt = EventDeliveryAttempt(
        id=1,
        created_at=datetime.datetime.now(tz=datetime.UTC),
        delivery=event_delivery,
        request_headers="",
        task_id="123",
    )
    task = DummyTask()
    # when
    task.push_request(retries=1)
    response = WebhookResponse(
        content="Error!", response_status_code=500, status=EventDeliveryStatus.FAILED
    )
    # then
    with pytest.raises(Retry):
        handle_webhook_retry(task, webhook, response, event_delivery, attempt)


def test_webhook_retry_404(webhook, event_delivery):
    # given
    attempt = EventDeliveryAttempt(
        id=1,
        created_at=datetime.datetime.now(tz=datetime.UTC),
        delivery=event_delivery,
        request_headers="",
        task_id="123",
    )
    task = DummyTask()
    # when
    task.push_request(retries=1)
    response = WebhookResponse(
        content="Error!", response_status_code=404, status=EventDeliveryStatus.FAILED
    )
    # then
    retry = handle_webhook_retry(task, webhook, response, event_delivery, attempt)
    assert retry is False


def test_webhook_retry_redirect(webhook, event_delivery):
    # given
    attempt = EventDeliveryAttempt(
        id=1,
        created_at=datetime.datetime.now(tz=datetime.UTC),
        delivery=event_delivery,
        request_headers="",
        task_id="123",
    )
    task = DummyTask()
    # when
    task.push_request(retries=1)
    response = WebhookResponse(
        content="Error!", response_status_code=302, status=EventDeliveryStatus.FAILED
    )
    # then
    retry = handle_webhook_retry(task, webhook, response, event_delivery, attempt)
    assert retry is False


@pytest.mark.parametrize(
    (
        "target_url",
        "expected_access_key_id",
        "expected_secret_access_key",
        "expected_region",
        "expected_queue_url",
    ),
    [
        (
            "awssqs://key_id:secret%2B%2Faccess@sqs.eu-west-1.amazonaws.com/account_id/queue_name",
            "key_id",
            "secret+/access",
            "eu-west-1",
            "https://sqs.eu-west-1.amazonaws.com/account_id/queue_name",
        ),
        (
            "awssqs://key_id:secret@sqs.example.com/account_id/queue_name",
            "key_id",
            "secret",
            "us-east-1",
            "https://sqs.example.com/account_id/queue_name",
        ),
    ],
)
def test_send_webhook_using_aws_sqs(
    mocked_boto3_client_constructor,
    mocked_boto3_client,
    sqs_response,
    target_url,
    expected_access_key_id,
    expected_secret_access_key,
    expected_region,
    expected_queue_url,
):
    # given
    message, signature, domain = "payload", "signature", "example.com"
    event_type = WebhookEventAsyncType.ORDER_CREATED

    # when
    webhook_response = send_webhook_using_aws_sqs(
        target_url, message.encode("utf-8"), domain, signature, event_type
    )

    # then
    mocked_boto3_client_constructor.assert_called_once_with(
        "sqs",
        region_name=expected_region,
        aws_access_key_id=expected_access_key_id,
        aws_secret_access_key=expected_secret_access_key,
    )
    expected_call_args = {
        "QueueUrl": expected_queue_url,
        "MessageAttributes": {
            "SaleorDomain": {"DataType": "String", "StringValue": domain},
            "SaleorApiUrl": {
                "DataType": "String",
                "StringValue": f"http://{domain}/graphql/",
            },
            "EventType": {"DataType": "String", "StringValue": event_type},
            "Signature": {"DataType": "String", "StringValue": signature},
        },
        "MessageBody": message,
    }
    mocked_boto3_client.send_message.assert_called_once_with(**expected_call_args)
    assert webhook_response.status == EventDeliveryStatus.SUCCESS
    assert webhook_response.content == json.dumps(sqs_response)


def test_send_webhook_using_aws_sqs_with_fifo_queue(mocked_boto3_client):
    # given
    domain = "example.com"
    event_type = WebhookEventAsyncType.ORDER_CREATED
    target_url = (
        "awssqs://key_id:secret@sqs.us-east-1.amazonaws.com/account_id/queue_name.fifo"
    )

    # when
    send_webhook_using_aws_sqs(target_url, b"payload", domain, "signature", event_type)

    # then
    _, send_message_kwargs = mocked_boto3_client.send_message.call_args
    assert send_message_kwargs["MessageGroupId"] == domain


def test_get_delivery_for_webhook(event_delivery):
    # when
    delivery = get_delivery_for_webhook(event_delivery.pk)

    # then
    assert delivery == event_delivery


def test_get_delivery_for_webhook_invalid_id(caplog):
    # when
    invalid_pk = 99999
    delivery = get_delivery_for_webhook(invalid_pk)

    # then
    assert delivery is None
    assert caplog.records[0].message == (f"Event delivery id: {invalid_pk} not found")


def test_get_delivery_for_webhook_inactive_webhook(event_delivery, caplog):
    # given
    event_delivery.webhook.is_active = False
    event_delivery.webhook.save(update_fields=["is_active"])

    # when
    delivery = get_delivery_for_webhook(event_delivery.pk)

    # then
    assert delivery is None
    event_delivery.refresh_from_db()
    assert event_delivery.status == EventDeliveryStatus.FAILED
    assert caplog.records[0].message == (
        f"Event delivery id: {event_delivery.pk} webhook is disabled."
    )


def test_get_multiple_deliveries_for_webhooks(event_deliveries):
    # given
    all_deliveries = EventDelivery.objects.all()
    ids = [event_delivery.pk for event_delivery in all_deliveries]

    # when
    deliveries = get_multiple_deliveries_for_webhooks(ids)

    # then
    assert len(all_deliveries) == len(deliveries)
    assert set(deliveries.keys()) == set(ids)


def test_get_multiple_deliveries_for_webhooks_with_inactive(
    any_webhook, event_deliveries
):
    # given
    all_deliveries = EventDelivery.objects.all()
    ids = [event_delivery.pk for event_delivery in all_deliveries]
    inactive_delivery = all_deliveries[0]

    any_webhook.is_active = False
    any_webhook.save(update_fields=["is_active"])
    inactive_delivery.webhook = any_webhook
    inactive_delivery.save(update_fields=["webhook"])

    # when
    deliveries = get_multiple_deliveries_for_webhooks(ids)

    # then
    assert len(deliveries) == len(all_deliveries) - 1
    assert set(deliveries.keys()) == set(ids) - {inactive_delivery.pk}

    inactive_delivery.refresh_from_db()
    assert inactive_delivery.status == EventDeliveryStatus.FAILED
