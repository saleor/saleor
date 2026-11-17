import datetime
import json
import re
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.sites.models import Site
from requests_hardened import HTTPSession

from ...app.headers import AppHeaders, DeprecatedAppHeaders
from ...core.models import EventDelivery
from ...webhook.event_types import WebhookEventAsyncType
from ...webhook.transport.asynchronous.transport import send_webhook_request_async
from ..saleor_api_url import notify_saleor_api_url_changed

PREVIOUS_DOMAIN = "old.example.com"
PREVIOUS_SALEOR_API_URL = "https://old.example.com/graphql/"
NEW_DOMAIN = "new.example.com"
NEW_PUBLIC_URL = "https://new.example.com"
NEW_SALEOR_API_URL = "https://new.example.com/graphql/"


def _http_ok_response():
    return MagicMock(
        text="{}",
        headers={},
        elapsed=datetime.timedelta(seconds=1),
        status_code=200,
        ok=True,
    )


@patch.object(HTTPSession, "request")
def test_notify_sends_previous_url_in_headers(
    mocked_request, subscription_saleor_api_url_changed_webhook, settings
):
    # given
    settings.PUBLIC_URL = None
    settings.ENABLE_SSL = True
    mocked_request.return_value = _http_ok_response()

    # when
    change = notify_saleor_api_url_changed(PREVIOUS_DOMAIN, NEW_DOMAIN)

    # then
    assert change.previous_saleor_api_url == PREVIOUS_SALEOR_API_URL
    assert change.saleor_api_url == NEW_SALEOR_API_URL
    mocked_request.assert_called_once()
    _, kwargs = mocked_request.call_args
    assert kwargs["headers"][AppHeaders.API_URL] == PREVIOUS_SALEOR_API_URL
    assert kwargs["headers"][AppHeaders.DOMAIN] == "old.example.com"
    assert kwargs["headers"][DeprecatedAppHeaders.DOMAIN] == "old.example.com"
    assert kwargs["headers"][AppHeaders.EVENT_TYPE] == (
        WebhookEventAsyncType.SALEOR_API_URL_CHANGED
    )
    assert json.loads(kwargs["data"]) == {
        "previousSaleorApiUrl": PREVIOUS_SALEOR_API_URL,
        "saleorApiUrl": NEW_SALEOR_API_URL,
    }


@pytest.mark.parametrize(
    ("_case", "public_url_after_change", "site_domain_after_change"),
    [
        ("cloud_site_domain_renamed", None, "new.example.com"),
        ("public_url_changed", NEW_PUBLIC_URL, "example.com"),
    ],
)
@patch.object(HTTPSession, "request")
def test_retry_after_change_sends_previous_url(
    mocked_request,
    _case,
    public_url_after_change,
    site_domain_after_change,
    event_delivery,
    settings,
):
    # given
    settings.PUBLIC_URL = public_url_after_change
    Site.objects.filter(pk=settings.SITE_ID).update(domain=site_domain_after_change)
    Site.objects.clear_cache()
    mocked_request.return_value = _http_ok_response()

    # when
    send_webhook_request_async(
        event_delivery_id=event_delivery.pk,
        telemetry_context={},
        saleor_api_url=PREVIOUS_SALEOR_API_URL,
    )

    # then
    Site.objects.clear_cache()
    mocked_request.assert_called_once()
    _, kwargs = mocked_request.call_args
    assert kwargs["headers"][AppHeaders.API_URL] == PREVIOUS_SALEOR_API_URL
    assert kwargs["headers"][AppHeaders.DOMAIN] == "old.example.com"


def test_retry_to_aws_sqs_sends_previous_url(event_delivery, monkeypatch):
    # given
    webhook = event_delivery.webhook
    webhook.target_url = (
        "awssqs://key_id:secret@sqs.us-east-1.amazonaws.com/account_id/queue_name"
    )
    webhook.save(update_fields=["target_url"])
    mocked_client = MagicMock()
    mocked_client.send_message.return_value = {}
    monkeypatch.setattr(
        "saleor.webhook.transport.utils.boto3.client",
        lambda *args, **kwargs: mocked_client,
    )

    # when
    send_webhook_request_async(
        event_delivery_id=event_delivery.pk,
        telemetry_context={},
        saleor_api_url=PREVIOUS_SALEOR_API_URL,
    )

    # then
    mocked_client.send_message.assert_called_once()
    attributes = mocked_client.send_message.call_args.kwargs["MessageAttributes"]
    assert attributes["SaleorApiUrl"]["StringValue"] == PREVIOUS_SALEOR_API_URL
    assert attributes["SaleorDomain"]["StringValue"] == "old.example.com"


def test_retry_to_google_cloud_pubsub_sends_previous_url(event_delivery, monkeypatch):
    # given
    webhook = event_delivery.webhook
    webhook.target_url = "gcpubsub://cloud.google.com/projects/saleor/topics/test"
    webhook.save(update_fields=["target_url"])
    mocked_publisher = MagicMock()
    mocked_publisher.publish.return_value.result.return_value = "message_id"
    monkeypatch.setattr(
        "saleor.webhook.transport.utils.pubsub_v1.PublisherClient",
        lambda: mocked_publisher,
    )

    # when
    send_webhook_request_async(
        event_delivery_id=event_delivery.pk,
        telemetry_context={},
        saleor_api_url=PREVIOUS_SALEOR_API_URL,
    )

    # then
    mocked_publisher.publish.assert_called_once()
    kwargs = mocked_publisher.publish.call_args.kwargs
    assert kwargs["saleorApiUrl"] == PREVIOUS_SALEOR_API_URL
    assert kwargs["saleorDomain"] == "old.example.com"


@pytest.mark.parametrize(
    ("_case", "public_url", "new_domain"),
    [
        ("same_domain", None, PREVIOUS_DOMAIN),
        ("public_url_overrides_domain", NEW_PUBLIC_URL, NEW_DOMAIN),
    ],
)
def test_notify_rejects_unchanged_url(
    _case,
    public_url,
    new_domain,
    subscription_saleor_api_url_changed_webhook,
    settings,
):
    # given
    settings.PUBLIC_URL = public_url
    settings.ENABLE_SSL = True
    unchanged_url = public_url + "/graphql/" if public_url else PREVIOUS_SALEOR_API_URL
    error_message = f"Saleor API URL is already {unchanged_url!r}; nothing changes."

    # when
    with pytest.raises(ValueError, match=f"^{re.escape(error_message)}$"):
        notify_saleor_api_url_changed(PREVIOUS_DOMAIN, new_domain)

    # then
    assert EventDelivery.objects.exists() is False
