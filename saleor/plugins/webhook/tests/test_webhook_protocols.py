from unittest.mock import MagicMock, patch

import pytest
import requests
from django.core.serializers import serialize

from ....webhook.event_types import WebhookEventType
from ...webhook.tasks import trigger_webhooks_for_event


def test_trigger_webhooks_with_google_pub_sub(
    webhook,
    order_with_lines,
    permission_manage_orders,
    permission_manage_users,
    permission_manage_products,
    monkeypatch,
):
    mocked_publisher = MagicMock()
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
