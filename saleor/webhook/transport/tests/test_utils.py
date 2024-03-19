import datetime
import json
from unittest.mock import MagicMock, call, patch

import pytest
from celery import Task
from celery.exceptions import Retry
from celery.utils.threads import LocalStack

from ....core import EventDeliveryStatus
from ....core.models import EventDeliveryAttempt
from ...event_types import WebhookEventAsyncType
from ..shipping import get_cache_data_for_shipping_list_methods_for_checkout
from ..utils import WebhookResponse, handle_webhook_retry, send_webhook_using_aws_sqs


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


@patch("saleor.webhook.transport.shipping.json.loads")
def test_get_cache_data_for_shipping_list_methods_for_checkout(mock_loads):
    # when
    result = get_cache_data_for_shipping_list_methods_for_checkout("test payload")

    # then
    assert result is mock_loads.return_value
    assert mock_loads.mock_calls == [
        call("test payload"),
        call().__getitem__(0),
        call().__getitem__().pop("last_change"),
        call().__getitem__(0),
        call().__getitem__().pop("meta"),
    ]
