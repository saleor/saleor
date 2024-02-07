from django.test import override_settings
from django.utils import timezone

from ....webhook.event_types import WebhookEventAsyncType
from ....webhook.models import Webhook
from ..subscription_payload import generate_pre_save_payloads, initialize_request


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


@override_settings(ENABLE_LIMITING_WEBHOOKS_FOR_IDENTICAL_PAYLOADS=False)
def test_generate_pre_save_payloads_disabled_with_env(webhook_app, variant):
    # given
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
    )

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
