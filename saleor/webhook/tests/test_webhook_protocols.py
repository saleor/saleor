import datetime
from unittest import mock
from unittest.mock import MagicMock, patch

import boto3
import jwt
import pytest
from django.core.serializers import serialize
from google.cloud.pubsub_v1 import PublisherClient
from requests_hardened import HTTPSession

from ...core.models import EventDelivery
from ..event_types import WebhookEventAsyncType
from ..transport import signature_for_payload
from ..transport.asynchronous import trigger_webhooks_async


@pytest.mark.parametrize(
    ("queue_name", "additional_call_args"),
    [("queue_name", {}), ("queue_name.fifo", {"MessageGroupId": "mirumee.com"})],
)
def test_trigger_webhooks_with_aws_sqs(
    queue_name,
    additional_call_args,
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
    monkeypatch,
):
    mocked_client = MagicMock()
    mocked_client.send_message.return_value = {"example": "response"}
    mocked_client_constructor = MagicMock(spec=boto3.client, return_value=mocked_client)

    monkeypatch.setattr(
        "saleor.webhook.transport.utils.boto3.client",
        mocked_client_constructor,
    )

    webhook.app.permissions.add(permission_manage_orders)
    access_key = "access_key_id"
    secret_key = "secret_access"
    region = "us-east-1"

    webhook.target_url = (
        f"awssqs://{access_key}:{secret_key}@sqs.{region}.amazonaws.com/account_id/"
        f"{queue_name}"
    )
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    expected_signature = signature_for_payload(expected_data.encode("utf-8"), None)
    trigger_webhooks_async(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [webhook],
        allow_replica=False,
    )

    mocked_client_constructor.assert_called_once_with(
        "sqs",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
    )
    expected_call_args = {
        "QueueUrl": f"https://sqs.us-east-1.amazonaws.com/account_id/{queue_name}",
        "MessageAttributes": {
            "SaleorDomain": {"DataType": "String", "StringValue": "mirumee.com"},
            "SaleorApiUrl": {
                "DataType": "String",
                "StringValue": "http://mirumee.com/graphql/",
            },
            "EventType": {"DataType": "String", "StringValue": "order_created"},
            "Signature": {"DataType": "String", "StringValue": expected_signature},
        },
        "MessageBody": expected_data,
    }
    expected_call_args.update(additional_call_args)
    mocked_client.send_message.assert_called_once_with(**expected_call_args)


@pytest.mark.parametrize(
    ("secret_key", "unquoted_secret"),
    [
        ("secret_access", "secret_access"),
        ("secret%2B%2Faccess", "secret+/access"),
    ],
)
def test_trigger_webhooks_with_aws_sqs_and_secret_key(
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
    monkeypatch,
    secret_key,
    unquoted_secret,
):
    mocked_client = MagicMock()
    mocked_client.send_message.return_value = {"example": "response"}
    mocked_client_constructor = MagicMock(spec=boto3.client, return_value=mocked_client)

    monkeypatch.setattr(
        "saleor.webhook.transport.utils.boto3.client",
        mocked_client_constructor,
    )

    webhook.app.permissions.add(permission_manage_orders)
    access_key = "access_key_id"
    region = "us-east-1"

    webhook.target_url = (
        f"awssqs://{access_key}:{secret_key}@sqs.{region}.amazonaws.com/account_id/"
        f"queue_name"
    )
    webhook.secret_key = "secret+/access"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    message = expected_data
    expected_signature = signature_for_payload(
        message.encode("utf-8"), webhook.secret_key
    )
    trigger_webhooks_async(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [webhook],
        allow_replica=False,
    )

    mocked_client_constructor.assert_called_once_with(
        "sqs",
        region_name=region,
        aws_access_key_id=access_key,
        aws_secret_access_key=unquoted_secret,
    )
    mocked_client.send_message.assert_called_once_with(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/account_id/queue_name",
        MessageAttributes={
            "SaleorDomain": {"DataType": "String", "StringValue": "mirumee.com"},
            "SaleorApiUrl": {
                "DataType": "String",
                "StringValue": "http://mirumee.com/graphql/",
            },
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
    mocked_publisher.publish.return_value.result.return_value = "message_id"
    monkeypatch.setattr(
        "saleor.webhook.transport.utils.pubsub_v1.PublisherClient",
        lambda: mocked_publisher,
    )
    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = "gcpubsub://cloud.google.com/projects/saleor/topics/test"
    webhook.save()
    expected_data = serialize("json", [order_with_lines])
    expected_signature = signature_for_payload(expected_data.encode("utf-8"), None)

    trigger_webhooks_async(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [webhook],
        allow_replica=False,
    )
    mocked_publisher.publish.assert_called_once_with(
        "projects/saleor/topics/test",
        expected_data.encode("utf-8"),
        saleorDomain="mirumee.com",
        saleorApiUrl="http://mirumee.com/graphql/",
        eventType=WebhookEventAsyncType.ORDER_CREATED,
        signature=expected_signature,
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
    mocked_publisher.publish.return_value.result.return_value = "message_id"
    monkeypatch.setattr(
        "saleor.webhook.transport.utils.pubsub_v1.PublisherClient",
        lambda: mocked_publisher,
    )
    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = "gcpubsub://cloud.google.com/projects/saleor/topics/test"
    webhook.secret_key = "secret_key"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    message = expected_data
    expected_signature = signature_for_payload(
        message.encode("utf-8"), webhook.secret_key
    )
    trigger_webhooks_async(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [webhook],
        allow_replica=False,
    )
    mocked_publisher.publish.assert_called_once_with(
        "projects/saleor/topics/test",
        message.encode("utf-8"),
        saleorDomain="mirumee.com",
        saleorApiUrl="http://mirumee.com/graphql/",
        eventType=WebhookEventAsyncType.ORDER_CREATED,
        signature=expected_signature,
    )


@patch.object(HTTPSession, "request")
def test_trigger_webhooks_with_http(
    mock_request,
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
    settings,
):
    mock_request.return_value = MagicMock(
        text="{response: body}",
        headers={"response": "header"},
        elapsed=datetime.timedelta(seconds=2),
        status_code=200,
        ok=True,
    )
    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = "https://webhook.site/48978b64-4efb-43d5-a334-451a1d164009"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    expected_signature = signature_for_payload(
        expected_data.encode("utf-8"), webhook.secret_key
    )

    trigger_webhooks_async(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [webhook],
        allow_replica=False,
    )

    expected_headers = {
        "Content-Type": "application/json",
        # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
        "X-Saleor-Event": "order_created",
        "X-Saleor-Domain": "mirumee.com",
        "X-Saleor-Signature": expected_signature,
        "Saleor-Event": "order_created",
        "Saleor-Domain": "mirumee.com",
        "Saleor-Signature": expected_signature,
        "Saleor-Api-Url": "http://mirumee.com/graphql/",
    }

    mock_request.assert_called_once_with(
        "POST",
        webhook.target_url,
        data=bytes(expected_data, "utf-8"),
        headers=expected_headers,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        allow_redirects=False,
    )


@patch.object(HTTPSession, "request")
def test_trigger_webhooks_with_http_and_secret_key(
    mock_request, webhook, order_with_lines, permission_manage_orders, settings
):
    mock_request.return_value = MagicMock(
        text="{response: body}",
        headers={"response": "header"},
        elapsed=datetime.timedelta(seconds=2),
        status_code=200,
        ok=True,
    )
    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = "https://webhook.site/48978b64-4efb-43d5-a334-451a1d164009"
    webhook.secret_key = "secret_key"
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    trigger_webhooks_async(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [webhook],
        allow_replica=False,
    )

    expected_signature = signature_for_payload(
        expected_data.encode("utf-8"), webhook.secret_key
    )
    expected_headers = {
        "Content-Type": "application/json",
        # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
        "X-Saleor-Event": "order_created",
        "X-Saleor-Domain": "mirumee.com",
        "X-Saleor-Signature": expected_signature,
        "Saleor-Event": "order_created",
        "Saleor-Domain": "mirumee.com",
        "Saleor-Signature": expected_signature,
        "Saleor-Api-Url": "http://mirumee.com/graphql/",
    }

    mock_request.assert_called_once_with(
        "POST",
        webhook.target_url,
        data=bytes(expected_data, "utf-8"),
        headers=expected_headers,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        allow_redirects=False,
    )


@patch.object(HTTPSession, "request")
def test_trigger_webhooks_with_http_and_secret_key_as_empty_string(
    mock_request, webhook, order_with_lines, permission_manage_orders, settings
):
    mock_request.return_value = MagicMock(
        text="{response: body}",
        headers={"response": "header"},
        elapsed=datetime.timedelta(seconds=2),
        status_code=200,
        ok=True,
    )
    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = "https://webhook.site/48978b64-4efb-43d5-a334-451a1d164009"
    webhook.secret_key = ""
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    trigger_webhooks_async(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [webhook],
        allow_replica=False,
    )

    expected_signature = signature_for_payload(expected_data.encode("utf-8"), "")
    expected_headers = {
        "Content-Type": "application/json",
        # X- headers will be deprecated in Saleor 4.0, proper headers are without X-
        "X-Saleor-Event": "order_created",
        "X-Saleor-Domain": "mirumee.com",
        "X-Saleor-Signature": expected_signature,
        "Saleor-Event": "order_created",
        "Saleor-Domain": "mirumee.com",
        "Saleor-Signature": expected_signature,
        "Saleor-Api-Url": "http://mirumee.com/graphql/",
    }

    signature_headers = jwt.get_unverified_header(expected_signature)

    # make sure that the signature has been build as a jwt token
    assert signature_headers["typ"] == "JWT"
    assert signature_headers["alg"] == "RS256"

    mock_request.assert_called_once_with(
        "POST",
        webhook.target_url,
        data=bytes(expected_data, "utf-8"),
        headers=expected_headers,
        timeout=settings.WEBHOOK_SYNC_TIMEOUT,
        allow_redirects=False,
    )


@patch.object(HTTPSession, "request")
def test_trigger_webhooks_with_http_and_custom_headers(
    mock_request, webhook, order_with_lines, permission_manage_orders
):
    # given
    webhook.app.permissions.add(permission_manage_orders)
    webhook.custom_headers = {"X-Key": "Value", "Authorization-Key": "Value"}
    webhook.secret_key = ""
    webhook.save()

    expected_data = serialize("json", [order_with_lines])
    expected_signature = signature_for_payload(expected_data.encode("utf-8"), "")
    expected_headers = {
        "Content-Type": "application/json",
        "X-Saleor-Event": "order_created",
        "X-Saleor-Domain": "mirumee.com",
        "X-Saleor-Signature": expected_signature,
        "Saleor-Event": "order_created",
        "Saleor-Domain": "mirumee.com",
        "Saleor-Signature": expected_signature,
        "Saleor-Api-Url": "http://mirumee.com/graphql/",
        "X-Key": "Value",
        "Authorization-Key": "Value",
    }

    # when
    trigger_webhooks_async(
        expected_data,
        WebhookEventAsyncType.ORDER_CREATED,
        [webhook],
        allow_replica=False,
    )

    # then
    mock_request.assert_called_once()
    assert mock_request.call_args[1]["headers"] == expected_headers


@pytest.mark.parametrize(
    ("expected_queue_name", "target_url"),
    [
        ("PUBSUB_QUEUE", "gcpubsub://cloud.google.com/projects/saleor/topics/test"),
        (
            "SQS_QUEUE",
            "awssqs://key:secret@sqs.us-east-2.amazonaws.com/xxxx/myqueue.fifo",
        ),
        (None, "https://localhost:8888/webhook-endpoint/"),
    ],
)
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.send_webhook_request_async.apply_async"
)
def test_trigger_webhooks_async_pick_up_queue_based_on_protocol(
    mock_async_apply,
    expected_queue_name,
    target_url,
    app,
    order_with_lines,
    permission_manage_orders,
    settings,
    webhook,
    django_assert_num_queries,
):
    # given
    settings.WEBHOOK_CELERY_QUEUE_NAME = None
    settings.WEBHOOK_SQS_CELERY_QUEUE_NAME = "SQS_QUEUE"
    settings.WEBHOOK_PUBSUB_CELERY_QUEUE_NAME = "PUBSUB_QUEUE"

    webhook.app.permissions.add(permission_manage_orders)
    webhook.target_url = target_url
    webhook.save()

    expected_data = serialize("json", [order_with_lines])

    # when
    with django_assert_num_queries(7):
        trigger_webhooks_async(
            expected_data,
            WebhookEventAsyncType.ORDER_CREATED,
            [webhook],
            allow_replica=False,
        )

    # then
    delivery = EventDelivery.objects.get()
    mock_async_apply.assert_called_once_with(
        kwargs={"event_delivery_id": delivery.id},
        queue=expected_queue_name,
        bind=True,
        retry_backoff=10,
        retry_kwargs={"max_retries": 5},
    )
