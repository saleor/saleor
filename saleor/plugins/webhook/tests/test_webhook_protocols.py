from unittest.mock import MagicMock, patch

import boto3
import pytest
import requests
from django.core.serializers import serialize
from google.cloud.pubsub_v1 import PublisherClient
from kombu.asynchronous.aws.sqs.connection import AsyncSQSConnection

from ....webhook.event_types import WebhookEventType
from ...webhook import signature_for_payload
from ...webhook.tasks import trigger_webhooks_for_event


def test_trigger_webhooks_with_aws_sqs(
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
    monkeypatch,
):
    mocked_client = MagicMock(spec=AsyncSQSConnection)
    mocked_client_constructor = MagicMock(spec=boto3.client, return_value=mocked_client)

    monkeypatch.setattr(
        "saleor.plugins.webhook.tasks.boto3.client",
        mocked_client_constructor,
    )

    webhook.app.permissions.add(permission_manage_orders)
    access_key = "access_key_id"
    secret_key = "secret_access"
    region = "us-east-1"

    webhook.target_url = (
        f"awssqs://{access_key}:{secret_key}@sqs.{region}.amazonaws.com/account_id/"
        f"queue_name"
    )
    webhook.save()

    expected_data = serialize("json", [order_with_lines])

    trigger_webhooks_for_event(WebhookEventType.ORDER_CREATED, expected_data)

    mocked_client_constructor.assert_called_once_with(
        "sqs",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    mocked_client.send_message.assert_called_once_with(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/account_id/queue_name",
        MessageAttributes={
            "SaleorDomain": {"DataType": "String", "StringValue": "mirumee.com"},
            "EventType": {"DataType": "String", "StringValue": "order_created"},
        },
        MessageBody=expected_data,
    )


def test_trigger_webhooks_with_aws_sqs_and_secret_key(
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
    monkeypatch,
):
    mocked_client = MagicMock(spec=AsyncSQSConnection)
    mocked_client_constructor = MagicMock(spec=boto3.client, return_value=mocked_client)

    monkeypatch.setattr(
        "saleor.plugins.webhook.tasks.boto3.client",
        mocked_client_constructor,
    )

    webhook.app.permissions.add(permission_manage_orders)
    access_key = "access_key_id"
    secret_key = "secret_access"
    region = "us-east-1"

    webhook.target_url = (
        f"awssqs://{access_key}:{secret_key}@sqs.{region}.amazonaws.com/account_id/"
        f"queue_name"
    )
    webhook.secret_key = "secret_key"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    expected_signature = signature_for_payload(
        expected_data.encode("utf-8"), webhook.secret_key
    )

    trigger_webhooks_for_event(WebhookEventType.ORDER_CREATED, expected_data)

    mocked_client_constructor.assert_called_once_with(
        "sqs",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    mocked_client.send_message.assert_called_once_with(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/account_id/queue_name",
        MessageAttributes={
            "SaleorDomain": {"DataType": "String", "StringValue": "mirumee.com"},
            "EventType": {"DataType": "String", "StringValue": "order_created"},
            "Signature": {"DataType": "String", "StringValue": expected_signature},
        },
        MessageBody=expected_data,
    )


def test_trigger_webhooks_with_google_pub_sub(
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
    monkeypatch,
):
    mocked_publisher = MagicMock(spec=PublisherClient)
    monkeypatch.setattr(
        "saleor.plugins.webhook.tasks.pubsub_v1.PublisherClient",
        lambda: mocked_publisher,
    )
    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = "gcpubsub://cloud.google.com/projects/saleor/topics/test"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])

    trigger_webhooks_for_event(WebhookEventType.ORDER_CREATED, expected_data)
    mocked_publisher.publish.assert_called_once_with(
        "projects/saleor/topics/test",
        expected_data.encode("utf-8"),
        saleorDomain="mirumee.com",
        eventType=WebhookEventType.ORDER_CREATED,
        signature="",
    )


def test_trigger_webhooks_with_google_pub_sub_and_secret_key(
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
    monkeypatch,
):
    mocked_publisher = MagicMock(spec=PublisherClient)
    monkeypatch.setattr(
        "saleor.plugins.webhook.tasks.pubsub_v1.PublisherClient",
        lambda: mocked_publisher,
    )
    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = "gcpubsub://cloud.google.com/projects/saleor/topics/test"
    webhook.secret_key = "secret_key"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    expected_signature = signature_for_payload(
        expected_data.encode("utf-8"), webhook.secret_key
    )
    trigger_webhooks_for_event(WebhookEventType.ORDER_CREATED, expected_data)
    mocked_publisher.publish.assert_called_once_with(
        "projects/saleor/topics/test",
        expected_data.encode("utf-8"),
        saleorDomain="mirumee.com",
        eventType=WebhookEventType.ORDER_CREATED,
        signature=expected_signature,
    )


@pytest.mark.vcr
@patch("saleor.plugins.webhook.tasks.requests.post", wraps=requests.post)
def test_trigger_webhooks_with_http(
    mock_request,
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
):
    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = "https://webhook.site/48978b64-4efb-43d5-a334-451a1d164009"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])

    trigger_webhooks_for_event(WebhookEventType.ORDER_CREATED, expected_data)

    expected_headers = {
        "Content-Type": "application/json",
        "X-Saleor-Event": "order_created",
        "X-Saleor-Domain": "mirumee.com",
        "X-Saleor-Signature": "",
    }

    mock_request.assert_called_once_with(
        webhook.target_url,
        data=bytes(expected_data, "utf-8"),
        headers=expected_headers,
        timeout=10,
    )


@pytest.mark.vcr
@patch("saleor.plugins.webhook.tasks.requests.post", wraps=requests.post)
def test_trigger_webhooks_with_http_and_secret_key(
    mock_request, webhook, order_with_lines, permission_manage_orders
):
    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = "https://webhook.site/48978b64-4efb-43d5-a334-451a1d164009"
    webhook.secret_key = "secret_key"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    trigger_webhooks_for_event(WebhookEventType.ORDER_CREATED, expected_data)

    expected_signature = signature_for_payload(
        expected_data.encode("utf-8"), webhook.secret_key
    )
    expected_headers = {
        "Content-Type": "application/json",
        "X-Saleor-Event": "order_created",
        "X-Saleor-Domain": "mirumee.com",
        "X-Saleor-Signature": expected_signature,
        "X-Saleor-HMAC-SHA256": f"sha1={expected_signature}",
    }

    mock_request.assert_called_once_with(
        webhook.target_url,
        data=bytes(expected_data, "utf-8"),
        headers=expected_headers,
        timeout=10,
    )
