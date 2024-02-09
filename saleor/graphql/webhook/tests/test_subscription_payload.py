from django.test import override_settings
from django.utils import timezone

from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.models import Webhook
from ..subscription_payload import (
    generate_pre_save_payloads,
    get_pre_save_payload_key,
    initialize_request,
)


def test_initialize_request():
    # when
    request = initialize_request()

    # then
    assert request.dataloaders == {}
    assert request.request_time is not None


def test_initialize_request_pass_params():
    # given
    dataloaders = {"test": "test"}
    request_time = timezone.now()

    # when
    request = initialize_request(dataloaders=dataloaders, request_time=request_time)

    # then
    assert request.dataloaders is dataloaders
    assert request.request_time is request_time


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


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=False)
def test_generate_pre_save_payloads_disabled_with_env(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    # when
    pre_save_payloads = generate_pre_save_payloads(
        [webhook],
        [variant],
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
        None,
        timezone.now(),
    )

    # then
    assert pre_save_payloads == {}


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=True)
def test_generate_pre_save_payloads_no_subscription_query(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=None,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    # when
    pre_save_payloads = generate_pre_save_payloads(
        [webhook],
        [variant],
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
        None,
        timezone.now(),
    )

    # then
    assert pre_save_payloads == {}


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=True)
def test_generate_pre_save_payloads(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=SUBSCRIPTION_QUERY,
    )
    event_type = WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED
    webhook.events.create(event_type=event_type)

    # when
    pre_save_payloads = generate_pre_save_payloads(
        [webhook],
        [variant],
        WebhookEventAsyncType.PRODUCT_VARIANT_UPDATED,
        None,
        timezone.now(),
    )

    # then
    key = get_pre_save_payload_key(webhook, variant)
    assert key in pre_save_payloads
    assert pre_save_payloads[key]
