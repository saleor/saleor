import json
from unittest.mock import MagicMock, patch

import pytest

from ....core import EventDeliveryStatus
from ...event_types import WebhookEventAsyncType
from ..utils import (
    WebhookResponse,
    attempt_update,
    create_attempt,
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


@pytest.mark.parametrize(
    ("content", "expected_attempt_response"),
    [
        ("", ""),
        ("error", "error"),
        ("errorerrorerrore", "errorerrorerrore"),
        (100 * "error", "errorerrorerrore..."),
    ],
)
def test_truncate_attempt_response(
    content, expected_attempt_response, event_delivery, settings
):
    settings.EVENT_DELIVERY_ATTEMPT_RESPONSE_SIZE_LIMIT = 16

    # given
    attempt = create_attempt(event_delivery)
    response = WebhookResponse(
        content=content,
        response_status_code=500,
        status=EventDeliveryStatus.FAILED,
    )

    # when
    attempt_update(attempt, response)

    # then
    attempt.refresh_from_db(fields=["response"])
    assert attempt.response == expected_attempt_response
