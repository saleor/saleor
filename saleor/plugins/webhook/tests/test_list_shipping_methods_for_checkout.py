from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.utils import timezone

from ....webhook.event_types import WebhookEventSyncType
from ....webhook.payloads import generate_checkout_payload
from ....webhook.transport.shipping import (
    get_cache_data_for_shipping_list_methods_for_checkout,
)
from ....webhook.transport.utils import generate_cache_key_for_webhook
from ..plugin import CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_for_checkout_webhook_response_none(
    mocked_webhook,
    webhook_plugin,
    checkout_ready_to_complete,
    shipping_app,
):
    # given
    checkout = checkout_ready_to_complete
    plugin = webhook_plugin()
    mocked_webhook.return_value = None

    # when
    response = plugin.get_shipping_methods_for_checkout(checkout, None)

    # then
    assert not response


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_for_checkout_set_cache(
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_webhook.return_value = [
        {
            "id": "method-1",
            "name": "Standard Shipping",
            "amount": Decimal("5.5"),
            "currency": "GBP",
        }
    ]
    plugin = webhook_plugin()

    # when
    plugin.get_shipping_methods_for_checkout(checkout_with_item, None)

    # then
    assert mocked_webhook.called
    assert mocked_cache_set.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_no_webhook_response_does_not_set_cache(
    mocked_webhook,
    mocked_cache_set,
    webhook_plugin,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_webhook.return_value = None
    plugin = webhook_plugin()

    # when
    plugin.get_shipping_methods_for_checkout(checkout_with_item, None)

    # then
    assert mocked_webhook.called
    assert not mocked_cache_set.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_for_checkout_use_cache(
    mocked_webhook,
    mocked_cache_get,
    webhook_plugin,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_cache_get.return_value = [
        {
            "id": "method-1",
            "name": "Standard Shipping",
            "amount": Decimal("5.5"),
            "currency": "GBP",
        }
    ]
    plugin = webhook_plugin()

    # when
    plugin.get_shipping_methods_for_checkout(checkout_with_item, None)

    # then
    assert not mocked_webhook.called
    assert mocked_cache_get.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_get_shipping_methods_for_checkout_use_cache_for_empty_list(
    mocked_webhook,
    mocked_cache_get,
    webhook_plugin,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_cache_get.return_value = []
    plugin = webhook_plugin()

    # when
    plugin.get_shipping_methods_for_checkout(checkout_with_item, None)

    # then
    assert not mocked_webhook.called
    assert mocked_cache_get.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_checkout_change_invalidates_cache_key(
    mocked_webhook,
    mocked_cache_get,
    mocked_cache_set,
    webhook_plugin,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_webhook_response = [
        {
            "id": "method-1",
            "name": "Standard Shipping",
            "amount": Decimal("5.5"),
            "currency": "GBP",
        }
    ]
    mocked_webhook.return_value = mocked_webhook_response
    mocked_cache_get.return_value = None

    payload = generate_checkout_payload(checkout_with_item)
    key_data = get_cache_data_for_shipping_list_methods_for_checkout(payload)
    target_url = shipping_app.webhooks.first().target_url
    cache_key = generate_cache_key_for_webhook(
        key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )
    plugin = webhook_plugin()

    # when
    checkout_with_item.email = "newemail@example.com"
    checkout_with_item.save(update_fields=["email"])
    new_payload = generate_checkout_payload(checkout_with_item)
    new_key_data = get_cache_data_for_shipping_list_methods_for_checkout(new_payload)
    new_cache_key = generate_cache_key_for_webhook(
        new_key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )
    plugin.get_shipping_methods_for_checkout(checkout_with_item, None)

    # then
    assert cache_key != new_cache_key
    mocked_cache_get.assert_called_once_with(new_cache_key)
    mocked_cache_set.assert_called_once_with(
        new_cache_key,
        mocked_webhook_response,
        timeout=CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_ignore_selected_fields_on_generating_cache_key(
    mocked_webhook,
    mocked_cache_get,
    mocked_cache_set,
    webhook_plugin,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_webhook_response = [
        {
            "id": "method-1",
            "name": "Standard Shipping",
            "amount": Decimal("5.5"),
            "currency": "GBP",
        }
    ]
    mocked_webhook.return_value = mocked_webhook_response
    mocked_cache_get.return_value = None

    payload = generate_checkout_payload(checkout_with_item)
    key_data = get_cache_data_for_shipping_list_methods_for_checkout(payload)
    target_url = shipping_app.webhooks.first().target_url
    cache_key = generate_cache_key_for_webhook(
        key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )
    plugin = webhook_plugin()

    # when
    checkout_with_item.last_change = timezone.now() + timedelta(seconds=30)
    checkout_with_item.save(update_fields=["last_change"])
    new_payload = generate_checkout_payload(checkout_with_item)
    new_key_data = get_cache_data_for_shipping_list_methods_for_checkout(new_payload)
    new_cache_key = generate_cache_key_for_webhook(
        new_key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )
    plugin.get_shipping_methods_for_checkout(checkout_with_item, None)

    # then
    assert cache_key == new_cache_key
    mocked_cache_get.assert_called_once_with(new_cache_key)
    mocked_cache_set.assert_called_once_with(
        new_cache_key,
        mocked_webhook_response,
        timeout=CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )
