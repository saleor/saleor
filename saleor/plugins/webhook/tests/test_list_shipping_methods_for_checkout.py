import json
from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.utils import timezone

from ....webhook.payloads import generate_checkout_payload
from ..shipping import generate_cache_key_for_shipping_list_methods_for_checkout


@mock.patch("saleor.plugins.webhook.plugin.cache.set")
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
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


@mock.patch("saleor.plugins.webhook.plugin.cache.set")
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
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


@mock.patch("saleor.plugins.webhook.plugin.cache.get")
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
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


@mock.patch("saleor.plugins.webhook.plugin.cache.get")
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
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


def test_checkout_change_invalidates_cache_key(checkout_with_item, shipping_app):
    # given
    payload = generate_checkout_payload(checkout_with_item)
    target_url = shipping_app.webhooks.first().target_url
    cache_key = generate_cache_key_for_shipping_list_methods_for_checkout(
        payload, target_url
    )

    # when
    checkout_with_item.email = "newemail@example.com"
    checkout_with_item.save(update_fields=["email"])
    new_payload = generate_checkout_payload(checkout_with_item)
    new_cache_key = generate_cache_key_for_shipping_list_methods_for_checkout(
        new_payload, target_url
    )

    # then
    assert cache_key != new_cache_key


def test_ignore_selected_fields_on_generating_cache_key(
    checkout_with_item, shipping_app
):
    # given
    target_url = shipping_app.webhooks.first().target_url

    payload = generate_checkout_payload(checkout_with_item)
    cache_key = generate_cache_key_for_shipping_list_methods_for_checkout(
        payload, target_url
    )

    # when
    checkout_with_item.last_change = timezone.now() + timedelta(seconds=30)
    checkout_with_item.save(update_fields=["last_change"])

    new_payload = generate_checkout_payload(checkout_with_item)
    new_payload_data = json.loads(new_payload)
    new_payload_data[0]["meta"]["issued_at"] = timezone.now().isoformat()
    new_payload = json.dumps(new_payload_data)
    new_cache_key = generate_cache_key_for_shipping_list_methods_for_checkout(
        new_payload, target_url
    )

    # then
    assert cache_key == new_cache_key


def test_different_target_urls_produce_different_cache_key(checkout_with_item):
    # given
    target_url_1 = "http://example.com/1"
    target_url_2 = "http://example.com/2"

    payload = generate_checkout_payload(checkout_with_item)

    # when
    cache_key_1 = generate_cache_key_for_shipping_list_methods_for_checkout(
        payload, target_url_1
    )
    cache_key_2 = generate_cache_key_for_shipping_list_methods_for_checkout(
        payload, target_url_2
    )

    # then
    assert cache_key_1 != cache_key_2
