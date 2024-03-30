import json
from unittest import mock

from django.test import override_settings

from .....graphql.webhook.subscription_payload import generate_payload_from_subscription
from .....webhook.event_types import WebhookEventAsyncType
from .....webhook.models import Webhook
from ..transport import create_deliveries_for_subscriptions, get_pre_save_payload_key

SUBSCRIPTION_QUERY = """
    subscription {
        event {
            ... on ProductVariantUpdated {
                productVariant {
                    name
                }
            }
        }
    }
"""


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=True)
def test_create_deliveries_different_pre_save_payloads(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    key = get_pre_save_payload_key(webhook, variant)
    pre_save_payloads = {key: {"productVariant": {"name": "Different name"}}}

    # when
    event_deliveries = create_deliveries_for_subscriptions(
        event_type=event_type,
        subscribable_object=variant,
        webhooks=[webhook],
        pre_save_payloads=pre_save_payloads,
    )

    # then
    assert event_deliveries
    event_delivery = event_deliveries[0]
    assert event_delivery
    payload = event_delivery.payload
    assert payload.payload


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=True)
def test_skip_delivery_creation_no_payload_changes(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    key = get_pre_save_payload_key(webhook, variant)
    pre_save_payloads = {key: {"productVariant": {"name": variant.name}}}  # no change

    # when
    event_deliveries = create_deliveries_for_subscriptions(
        event_type=event_type,
        subscribable_object=variant,
        webhooks=[webhook],
        pre_save_payloads=pre_save_payloads,
    )

    # then
    assert event_deliveries == []


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=False)
def test_create_deliveries_no_payload_changes_limiting_disabled(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    key = get_pre_save_payload_key(webhook, variant)
    pre_payload = {"productVariant": {"name": variant.name}}
    pre_save_payloads = {key: pre_payload}  # no change

    # when
    event_deliveries = create_deliveries_for_subscriptions(
        event_type=event_type,
        subscribable_object=variant,
        webhooks=[webhook],
        pre_save_payloads=pre_save_payloads,
    )

    # then
    assert event_deliveries
    event_delivery = event_deliveries[0]
    assert event_delivery
    payload = event_delivery.payload
    assert json.loads(payload.payload) == pre_payload


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=True)
@mock.patch(
    "saleor.webhook.transport.asynchronous.transport.generate_payload_from_subscription",
    wraps=generate_payload_from_subscription,
)
def test_create_deliveries_reuse_request_for_webhooks(
    mock_generate_payload_from_subscription, webhook_app, variant
):
    # given
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook_1 = Webhook.objects.create(
        name="Webhook 1",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    webhook_1.events.create(event_type=event_type)

    webhook_2 = Webhook.objects.create(
        name="Webhook 2",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    webhook_2.events.create(event_type=event_type)

    key_1 = get_pre_save_payload_key(webhook_1, variant)
    key_2 = get_pre_save_payload_key(webhook_2, variant)

    pre_payload = {"productVariant": {"name": "Different name"}}
    pre_save_payloads = {key_1: pre_payload, key_2: pre_payload}

    # when
    event_deliveries = create_deliveries_for_subscriptions(
        event_type=event_type,
        subscribable_object=variant,
        webhooks=[webhook_1, webhook_2],
        pre_save_payloads=pre_save_payloads,
    )

    # then
    assert len(event_deliveries) == 2
    assert mock_generate_payload_from_subscription.call_count == 2

    request_1 = mock_generate_payload_from_subscription.call_args_list[0][1]["request"]
    request_2 = mock_generate_payload_from_subscription.call_args_list[1][1]["request"]
    assert request_1 is request_2
    assert request_1.dataloaders is request_2.dataloaders
