from ....core.http_client import HTTPClient
from ....core.models import EventDeliveryAttempt
from ....webhook.transport.asynchronous.transport import trigger_webhooks_async


def test_rejects_private_ips(webhook, monkeypatch):
    """Ensure private IP addresses are rejected by webhooks."""

    # Enable IP filter
    monkeypatch.setattr(HTTPClient.config, "ip_filter_enable", True)

    # Configure webhook
    webhook.target_url = "https://10.0.0.0/test"
    webhook.save(update_fields=["target_url"])

    assert (
        not EventDeliveryAttempt.objects.exists()
    ), "should not have any pre-existing attempts"

    # Trigger the webhook
    trigger_webhooks_async(
        data="", event_type="test", webhooks=[webhook], allow_replica=False
    )

    # Should have rejected the ip address used in all attempts.
    statuses = list(EventDeliveryAttempt.objects.values_list("status", "response"))
    assert len(statuses) > 0
    assert statuses == [("failed", "Invalid IP address")] * len(statuses)
