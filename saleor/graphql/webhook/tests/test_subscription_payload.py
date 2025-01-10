import graphene
from django.test import override_settings
from django.utils import timezone

from ....webhook.event_types import WebhookEventAsyncType, WebhookEventSyncType
from ....webhook.models import Webhook
from ..subscription_payload import (
    generate_payload_from_subscription,
    generate_payload_promise_from_subscription,
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


def test_generate_payload_from_subscription(
    checkout,
    subscription_webhook,
):
    # given
    query = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ... on Checkout {
                id
              }
            }
          }
        }
      }
    }
    """
    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request()
    checkout_global_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
        app=app,
    )

    # then
    assert payload["taxBase"]["sourceObject"]["id"] == checkout_global_id


def test_generate_payload_from_subscription_missing_permissions(
    gift_card, subscription_gift_card_created_webhook, permission_manage_gift_card
):
    # given

    webhook = subscription_gift_card_created_webhook
    app = webhook.app
    app.permissions.remove(permission_manage_gift_card)
    request = initialize_request(requestor=app, sync_event=False)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventAsyncType.GIFT_CARD_CREATED,
        subscribable_object=gift_card,
        subscription_query=webhook.subscription_query,
        request=request,
        app=app,
    )

    # then
    error_code = "PermissionDenied"
    assert "errors" in payload.keys()
    assert not payload["giftCard"]
    error = payload["errors"][0]
    assert error["extensions"]["exception"]["code"] == error_code


def test_generate_payload_from_subscription_circular_call(
    checkout, subscription_webhook, permission_handle_taxes
):
    # given
    query = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ...on Checkout{
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(requestor=app, sync_event=True)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
        app=app,
    )
    # then
    error_code = "CircularSubscriptionSyncEvent"
    assert list(payload.keys()) == ["errors"]
    error = payload["errors"][0]
    assert (
        error["message"] == "Resolving this field is not allowed in synchronous events."
    )
    assert error["extensions"]["exception"]["code"] == error_code


def test_generate_payload_from_subscription_unable_to_build_payload(
    checkout, subscription_webhook
):
    # given
    query = """
    subscription {
      event {
        ... on OrderCalculateTaxes {
          taxBase {
            sourceObject {
              ...on Checkout{
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(requestor=app, sync_event=True)

    # when
    payload = generate_payload_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
        app=app,
    )
    # then
    assert payload is None


def test_generate_payload_promise_from_subscription(
    checkout,
    subscription_webhook,
):
    # given
    query = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ... on Checkout {
                id
              }
            }
          }
        }
      }
    }
    """
    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request()
    checkout_global_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    # when
    payload = generate_payload_promise_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
        app=app,
    )

    # then
    payload = payload.get()
    assert payload["taxBase"]["sourceObject"]["id"] == checkout_global_id


def test_generate_payload_promise_from_subscription_missing_permissions(
    gift_card, subscription_gift_card_created_webhook, permission_manage_gift_card
):
    # given

    webhook = subscription_gift_card_created_webhook
    app = webhook.app
    app.permissions.remove(permission_manage_gift_card)
    request = initialize_request(requestor=app, sync_event=False)

    # when
    payload = generate_payload_promise_from_subscription(
        event_type=WebhookEventAsyncType.GIFT_CARD_CREATED,
        subscribable_object=gift_card,
        subscription_query=webhook.subscription_query,
        request=request,
        app=app,
    )

    # then
    payload = payload.get()
    error_code = "PermissionDenied"
    assert "errors" in payload.keys()
    assert not payload["giftCard"]
    error = payload["errors"][0]
    assert error["extensions"]["exception"]["code"] == error_code


def test_generate_payload_promise_from_subscription_circular_call(
    checkout, subscription_webhook, permission_handle_taxes
):
    # given
    query = """
    subscription {
      event {
        ... on CalculateTaxes {
          taxBase {
            sourceObject {
              ...on Checkout{
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(requestor=app, sync_event=True)

    # when
    payload = generate_payload_promise_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
        app=app,
    )
    # then
    payload = payload.get()
    error_code = "CircularSubscriptionSyncEvent"
    assert list(payload.keys()) == ["errors"]
    error = payload["errors"][0]
    assert (
        error["message"] == "Resolving this field is not allowed in synchronous events."
    )
    assert error["extensions"]["exception"]["code"] == error_code


def test_generate_payload_promise_from_subscription_unable_to_build_payload(
    checkout, subscription_webhook
):
    # given
    query = """
    subscription {
      event {
        ... on OrderCalculateTaxes {
          taxBase {
            sourceObject {
              ...on Checkout{
                totalPrice {
                  gross {
                    amount
                  }
                }
              }
            }
          }
        }
      }
    }
    """

    webhook = subscription_webhook(
        query,
        WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
    )
    app = webhook.app
    request = initialize_request(requestor=app, sync_event=True)

    # when
    payload = generate_payload_promise_from_subscription(
        event_type=WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES,
        subscribable_object=checkout,
        subscription_query=webhook.subscription_query,
        request=request,
        app=app,
    )
    # then
    payload = payload.get()
    assert payload is None
