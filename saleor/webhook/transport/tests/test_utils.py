import datetime
import json
from unittest.mock import MagicMock

import boto3
import pytest
from celery import Task
from celery.exceptions import Retry
from celery.utils.threads import LocalStack

from ....core import EventDeliveryStatus
from ....core.models import EventDeliveryAttempt
from ...event_types import WebhookEventAsyncType
from ..utils import WebhookResponse, handle_webhook_retry, send_webhook_using_aws_sqs


class DummyTask(Task):
    retry_backoff = 10
    retry_kwargs = {"max_retries": 2}
    request_stack = LocalStack()


def test_webhook_retry(webhook, event_delivery):
    # given
    attempt = EventDeliveryAttempt(
        id=1,
        created_at=datetime.datetime.utcnow(),
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
        created_at=datetime.datetime.utcnow(),
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
        created_at=datetime.datetime.utcnow(),
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
        "is_fifo",
        "expected_queue_url",
    ),
    [
        (
            "awssqs://key_id:secret%2B%2Faccess@sqs.eu-west-1.amazonaws.com/account_id/queue_name",
            "key_id",
            "secret+/access",
            "eu-west-1",
            False,
            "https://sqs.eu-west-1.amazonaws.com/account_id/queue_name",
        ),
        (
            "awssqs://key_id:secret@sqs.example.com/account_id/queue_name.fifo",
            "key_id",
            "secret",
            "us-east-1",
            True,
            "https://sqs.example.com/account_id/queue_name.fifo",
        ),
    ],
)
def test_send_webhook_using_aws_sqs(
    target_url,
    expected_access_key_id,
    expected_secret_access_key,
    expected_region,
    is_fifo,
    expected_queue_url,
    monkeypatch,
):
    # given
    message, signature, domain = "payload", "signature", "example.com"
    event_type = WebhookEventAsyncType.ORDER_CREATED
    sqs_response = {
        "MD5OfMessageBody": "message-body-hash",
        "MD5OfMessageAttributes": "message-attributes-hash",
        "MD5OfMessageSystemAttributes": "message-system-attributes-hash",
        "MessageId": "message-id",
        "SequenceNumber": "sequence-number",
    }
    mocked_client = MagicMock()
    mocked_client.send_message.return_value = sqs_response
    mocked_client_constructor = MagicMock(spec=boto3.client, return_value=mocked_client)
    monkeypatch.setattr(
        "saleor.webhook.transport.utils.boto3.client",
        mocked_client_constructor,
    )

    # when
    webhook_response = send_webhook_using_aws_sqs(
        target_url, message.encode("utf-8"), domain, signature, event_type
    )

    # then
    mocked_client_constructor.assert_called_once_with(
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
    if is_fifo:
        expected_call_args.update({"MessageGroupId": domain})
    mocked_client.send_message.assert_called_once_with(**expected_call_args)
    assert webhook_response.status == EventDeliveryStatus.SUCCESS
    assert webhook_response.content == json.dumps(sqs_response)
