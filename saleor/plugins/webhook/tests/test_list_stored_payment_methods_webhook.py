import json
from unittest import mock

import graphene

from ....core.models import EventDelivery
from ....payment.interface import ListStoredPaymentMethodsRequestData
from ....settings import WEBHOOK_SYNC_TIMEOUT
from ....webhook.const import WEBHOOK_CACHE_DEFAULT_TIMEOUT
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.transport.list_stored_payment_methods import (
    get_list_stored_payment_methods_from_response,
)
from ....webhook.transport.utils import generate_cache_key_for_webhook
from .subscription_webhooks.subscription_queries import (
    LIST_STORED_PAYMENT_METHODS as LIST_STORED_PAYMENT_METHODS_SUBSCRIPTION,
)

LIST_STORED_PAYMENT_METHODS = """
subscription {
  event {
    ... on ListStoredPaymentMethods{
      user{
        id
      }
      channel{
        id
      }
    }
  }
}
"""


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_stored_payment_methods_with_static_payload(
    mock_request,
    mocked_cache_get,
    mocked_cache_set,
    channel_USD,
    customer_user,
    webhook_plugin,
    list_stored_payment_methods_app,
    webhook_list_stored_payment_methods_response,
):
    # given
    mock_request.return_value = webhook_list_stored_payment_methods_response
    mocked_cache_get.return_value = None
    webhook = list_stored_payment_methods_app.webhooks.first()

    plugin = webhook_plugin()

    data = ListStoredPaymentMethodsRequestData(
        channel=channel_USD,
        user=customer_user,
    )
    expected_payload = {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
    }
    expected_cache_key = generate_cache_key_for_webhook(
        expected_payload,
        webhook.target_url,
        WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
        list_stored_payment_methods_app.id,
    )

    # when
    response = plugin.list_stored_payment_methods(data, [])

    # then
    delivery = EventDelivery.objects.get()
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    mocked_cache_get.assert_called_once_with(expected_cache_key)
    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_list_stored_payment_methods_response,
        timeout=WEBHOOK_CACHE_DEFAULT_TIMEOUT,
    )

    assert response
    assert response == get_list_stored_payment_methods_from_response(
        list_stored_payment_methods_app,
        webhook_list_stored_payment_methods_response,
        channel_USD.currency_code,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_stored_payment_methods_subscription_issuing_principal(
    mock_request,
    mocked_cache_get,
    channel_USD,
    customer_user,
    webhook_plugin,
    list_stored_payment_methods_app,
    webhook_list_stored_payment_methods_response,
):
    # given
    mock_request.return_value = webhook_list_stored_payment_methods_response
    mocked_cache_get.return_value = None
    webhook = list_stored_payment_methods_app.webhooks.first()
    webhook.subscription_query = LIST_STORED_PAYMENT_METHODS_SUBSCRIPTION
    webhook.save(update_fields=["subscription_query"])

    plugin = webhook_plugin()
    plugin.requestor = customer_user

    data = ListStoredPaymentMethodsRequestData(
        channel=channel_USD,
        user=customer_user,
    )

    # when
    response = plugin.list_stored_payment_methods(data, [])

    # then
    delivery = EventDelivery.objects.get()
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    delivery_subscription_payload = json.loads(delivery.payload.payload)
    assert delivery_subscription_payload == {
        "issuingPrincipal": {"id": graphene.Node.to_global_id("User", customer_user.pk)}
    }

    assert response
    assert response == get_list_stored_payment_methods_from_response(
        list_stored_payment_methods_app,
        webhook_list_stored_payment_methods_response,
        channel_USD.currency_code,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_stored_payment_methods_subscription_issuing_principal_as_app(
    mock_request,
    mocked_cache_get,
    channel_USD,
    customer_user,
    webhook_plugin,
    list_stored_payment_methods_app,
    webhook_list_stored_payment_methods_response,
):
    # given
    mock_request.return_value = webhook_list_stored_payment_methods_response
    mocked_cache_get.return_value = None
    webhook = list_stored_payment_methods_app.webhooks.first()
    webhook.subscription_query = LIST_STORED_PAYMENT_METHODS_SUBSCRIPTION
    webhook.save(update_fields=["subscription_query"])

    plugin = webhook_plugin()
    plugin.requestor = list_stored_payment_methods_app

    data = ListStoredPaymentMethodsRequestData(
        channel=channel_USD,
        user=customer_user,
    )

    # when
    response = plugin.list_stored_payment_methods(data, [])

    # then
    delivery = EventDelivery.objects.get()
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    delivery_subscription_payload = json.loads(delivery.payload.payload)
    assert delivery_subscription_payload == {
        "issuingPrincipal": {
            "id": graphene.Node.to_global_id("App", list_stored_payment_methods_app.pk)
        }
    }

    assert response
    assert response == get_list_stored_payment_methods_from_response(
        list_stored_payment_methods_app,
        webhook_list_stored_payment_methods_response,
        channel_USD.currency_code,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_stored_payment_methods_with_subscription_payload(
    mock_request,
    mocked_cache_get,
    mocked_cache_set,
    channel_USD,
    customer_user,
    webhook_plugin,
    list_stored_payment_methods_app,
    webhook_list_stored_payment_methods_response,
):
    # given
    mock_request.return_value = webhook_list_stored_payment_methods_response
    mocked_cache_get.return_value = None

    webhook = list_stored_payment_methods_app.webhooks.first()
    webhook.subscription_query = LIST_STORED_PAYMENT_METHODS
    webhook.save()

    plugin = webhook_plugin()

    data = ListStoredPaymentMethodsRequestData(
        channel=channel_USD,
        user=customer_user,
    )
    expected_payload = {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
    }
    expected_cache_key = generate_cache_key_for_webhook(
        expected_payload,
        webhook.target_url,
        WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
        list_stored_payment_methods_app.id,
    )

    # when
    response = plugin.list_stored_payment_methods(data, [])

    # then
    delivery = EventDelivery.objects.get()
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    mocked_cache_get.assert_called_once_with(expected_cache_key)
    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        webhook_list_stored_payment_methods_response,
        timeout=WEBHOOK_CACHE_DEFAULT_TIMEOUT,
    )

    assert response
    assert response == get_list_stored_payment_methods_from_response(
        list_stored_payment_methods_app,
        webhook_list_stored_payment_methods_response,
        channel_USD.currency_code,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_stored_payment_methods_uses_cache_if_available(
    mock_request,
    mocked_cache_get,
    mocked_cache_set,
    channel_USD,
    customer_user,
    webhook_plugin,
    list_stored_payment_methods_app,
    webhook_list_stored_payment_methods_response,
):
    # given
    mock_request.return_value = webhook_list_stored_payment_methods_response
    mocked_cache_get.return_value = webhook_list_stored_payment_methods_response

    webhook = list_stored_payment_methods_app.webhooks.first()
    webhook.subscription_query = LIST_STORED_PAYMENT_METHODS
    webhook.save()

    plugin = webhook_plugin()

    data = ListStoredPaymentMethodsRequestData(
        channel=channel_USD,
        user=customer_user,
    )
    expected_payload = {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
    }
    expected_cache_key = generate_cache_key_for_webhook(
        expected_payload,
        webhook.target_url,
        WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
        list_stored_payment_methods_app.id,
    )

    # when
    response = plugin.list_stored_payment_methods(data, [])

    # then
    mocked_cache_get.assert_called_once_with(expected_cache_key)
    assert not mock_request.called
    assert not mocked_cache_set.called

    assert response
    assert response == get_list_stored_payment_methods_from_response(
        list_stored_payment_methods_app,
        webhook_list_stored_payment_methods_response,
        channel_USD.currency_code,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_stored_payment_methods_app_returns_incorrect_response(
    mock_request,
    mocked_cache_get,
    mocked_cache_set,
    channel_USD,
    customer_user,
    webhook_plugin,
    list_stored_payment_methods_app,
    webhook_list_stored_payment_methods_response,
):
    # given
    mock_request.return_value = None
    mocked_cache_get.return_value = None

    webhook = list_stored_payment_methods_app.webhooks.first()
    webhook.subscription_query = LIST_STORED_PAYMENT_METHODS
    webhook.save()

    plugin = webhook_plugin()
    data = ListStoredPaymentMethodsRequestData(
        channel=channel_USD,
        user=customer_user,
    )

    expected_payload = {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
    }
    expected_cache_key = generate_cache_key_for_webhook(
        expected_payload,
        webhook.target_url,
        WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
        list_stored_payment_methods_app.id,
    )

    # when
    response = plugin.list_stored_payment_methods(data, [])

    # then
    delivery = EventDelivery.objects.get()
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    mocked_cache_get.assert_called_once_with(expected_cache_key)
    assert not mocked_cache_set.called

    assert response == []
