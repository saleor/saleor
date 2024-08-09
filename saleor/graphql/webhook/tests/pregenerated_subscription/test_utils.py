from .....webhook.models import Webhook
from ...utils import get_pregenerated_subscription_payload, get_subscription_query_hash


def test_get_subscription_query_hash():
    # given
    subscription_query = "subscription { orderCreated { id } }"

    # when
    query_hash = get_subscription_query_hash(subscription_query)

    # then
    assert query_hash == "6553179c22234d0b8e07d8db49ac9bd2"


def test_get_pregenerated_subscription_payload(webhook_app):
    # given
    example_payload = {"payload": "example"}
    subscription_query = "subscription { orderCreated { id } }"
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=subscription_query,
    )

    pregenerated_subscription_payloads = {
        webhook_app.pk: {"6553179c22234d0b8e07d8db49ac9bd2": example_payload}
    }

    # when
    payload = get_pregenerated_subscription_payload(
        webhook, pregenerated_subscription_payloads
    )

    # then
    assert payload == example_payload


def test_get_pregenerated_subscription_payload_payload_for_other_app(webhook_app):
    # given
    example_payload = {"payload": "example"}
    subscription_query = "subscription { orderCreated { id } }"
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=subscription_query,
    )
    invalid_app_id = webhook_app.pk + 1

    pregenerated_subscription_payloads = {
        invalid_app_id: {"6553179c22234d0b8e07d8db49ac9bd2": example_payload}
    }

    # when
    payload = get_pregenerated_subscription_payload(
        webhook, pregenerated_subscription_payloads
    )

    # then
    assert payload is None


def test_get_pregenerated_subscription_payload_empty_pregenerated_dict(webhook_app):
    # given
    subscription_query = "subscription { orderCreated { id } }"
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
        subscription_query=subscription_query,
    )

    pregenerated_subscription_payloads = {}

    # when
    payload = get_pregenerated_subscription_payload(
        webhook, pregenerated_subscription_payloads
    )

    # then
    assert payload is None


def test_get_pregenerated_subscription_payload_webhook_without_subscription(
    webhook_app,
):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        target_url="http://www.example.com/any",
    )

    pregenerated_subscription_payloads = {}

    # when
    payload = get_pregenerated_subscription_payload(
        webhook, pregenerated_subscription_payloads
    )

    # then
    assert payload is None
