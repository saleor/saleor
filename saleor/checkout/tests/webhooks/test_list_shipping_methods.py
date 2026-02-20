import datetime
from decimal import Decimal
from unittest import mock

from django.utils import timezone

from ....webhook import const
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.payloads import generate_checkout_payload
from ....webhook.response_schemas.utils.annotations import logger as annotations_logger
from ....webhook.transport.utils import generate_cache_key_for_webhook
from ...utils import get_or_create_checkout_metadata
from ...webhooks.list_shipping_methods import (
    CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    _get_cache_data_for_shipping_list_methods_for_checkout,
    _parse_list_shipping_methods_response,
    list_shipping_methods_for_checkout,
)


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_shipping_methods_for_checkout_webhook_response_none(
    mocked_webhook,
    checkout_ready_to_complete,
    shipping_app,
):
    # given
    checkout = checkout_ready_to_complete
    mocked_webhook.return_value = None

    # when
    response = list_shipping_methods_for_checkout(
        checkout,
        [],
        allow_replica=False,
        requestor=None,
    )

    # then
    assert not response


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_shipping_methods_for_checkout_set_cache(
    mocked_webhook,
    mocked_cache_set,
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

    # when
    list_shipping_methods_for_checkout(
        checkout_with_item, [], allow_replica=False, requestor=None
    )

    # then
    assert mocked_webhook.called
    assert mocked_cache_set.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_shipping_methods_no_webhook_response_sets_short_term_cache(
    mocked_webhook,
    mocked_cache_set,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_webhook.return_value = None

    payload = generate_checkout_payload(checkout_with_item)
    key_data = _get_cache_data_for_shipping_list_methods_for_checkout(payload)
    target_url = shipping_app.webhooks.first().target_url
    cache_key = generate_cache_key_for_webhook(
        key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )

    # when
    list_shipping_methods_for_checkout(
        checkout_with_item, [], allow_replica=False, requestor=None
    )

    # then
    assert mocked_webhook.called
    mocked_cache_set.assert_called_once_with(
        cache_key,
        const.SYNC_WEBHOOK_FAILURE_SENTINEL,
        timeout=const.SYNC_WEBHOOK_FAILURE_CACHE_TTL,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_shipping_methods_for_checkout_use_cache(
    mocked_webhook,
    mocked_cache_get,
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

    # when
    list_shipping_methods_for_checkout(
        checkout_with_item, [], allow_replica=False, requestor=None
    )

    # then
    assert not mocked_webhook.called
    assert mocked_cache_get.called


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_list_shipping_methods_for_checkout_use_cache_for_empty_list(
    mocked_webhook,
    mocked_cache_get,
    checkout_with_item,
    shipping_app,
):
    # given
    mocked_cache_get.return_value = []

    # when
    list_shipping_methods_for_checkout(
        checkout_with_item, [], allow_replica=False, requestor=None
    )

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
    key_data = _get_cache_data_for_shipping_list_methods_for_checkout(payload)
    target_url = shipping_app.webhooks.first().target_url
    cache_key = generate_cache_key_for_webhook(
        key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )

    # when
    checkout_with_item.email = "newemail@example.com"
    checkout_with_item.save(update_fields=["email"])
    new_payload = generate_checkout_payload(checkout_with_item)
    new_key_data = _get_cache_data_for_shipping_list_methods_for_checkout(new_payload)
    new_cache_key = generate_cache_key_for_webhook(
        new_key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )
    list_shipping_methods_for_checkout(
        checkout_with_item, [], allow_replica=False, requestor=None
    )

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
    key_data = _get_cache_data_for_shipping_list_methods_for_checkout(payload)
    target_url = shipping_app.webhooks.first().target_url
    cache_key = generate_cache_key_for_webhook(
        key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )

    # when
    checkout_with_item.last_change = timezone.now() + datetime.timedelta(seconds=30)
    checkout_with_item.save(update_fields=["last_change"])
    new_payload = generate_checkout_payload(checkout_with_item)
    new_key_data = _get_cache_data_for_shipping_list_methods_for_checkout(new_payload)
    new_cache_key = generate_cache_key_for_webhook(
        new_key_data,
        target_url,
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT,
        shipping_app.id,
    )
    list_shipping_methods_for_checkout(
        checkout_with_item, [], allow_replica=False, requestor=None
    )

    # then
    assert cache_key == new_cache_key
    mocked_cache_get.assert_called_once_with(new_cache_key)
    mocked_cache_set.assert_called_once_with(
        new_cache_key,
        mocked_webhook_response,
        timeout=CACHE_TIME_SHIPPING_LIST_METHODS_FOR_CHECKOUT,
    )


@mock.patch.object(annotations_logger, "warning")
def test_parse_list_shipping_methods_response_response_incorrect_format(
    mocked_logger, app
):
    # given
    response_data_with_incorrect_format = [[1], 2, "3"]

    # when
    result = _parse_list_shipping_methods_response(
        response_data_with_incorrect_format, app, "USD"
    )

    # then
    assert result == []
    assert mocked_logger.call_count == len(response_data_with_incorrect_format)
    error_msg = mocked_logger.call_args[0][1]
    assert error_msg == "Skipping invalid shipping method (ListShippingMethodsSchema)"


def test_parse_list_shipping_methods_with_metadata(app):
    # given
    response_data_with_meta = [
        {
            "id": 123,
            "amount": 10,
            "currency": "USD",
            "name": "shipping",
            "description": "Description",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
            "metadata": {"field": "value"},
        }
    ]

    # when
    response = _parse_list_shipping_methods_response(
        response_data_with_meta, app, "USD"
    )

    # then
    assert response[0].metadata == response_data_with_meta[0]["metadata"]
    assert response[0].description == response_data_with_meta[0]["description"]


def test_parse_list_shipping_methods_with_metadata_in_incorrect_format(app):
    # given
    response_data_with_meta = [
        {
            "id": 123,
            "amount": 10,
            "currency": "USD",
            "name": "shipping",
            "description": "Description",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
            "metadata": {"field": None},
        }
    ]

    # when
    response = _parse_list_shipping_methods_response(
        response_data_with_meta, app, "USD"
    )

    # then
    assert response[0].metadata == {}


def test_parse_list_shipping_methods_metadata_absent_in_response(app):
    # given
    response_data_with_meta = [
        {
            "id": 123,
            "amount": 10,
            "currency": "USD",
            "name": "shipping",
            "description": "Description",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
        }
    ]

    # when
    response = _parse_list_shipping_methods_response(
        response_data_with_meta, app, "USD"
    )

    # then
    assert response[0].metadata == {}


def test_parse_list_shipping_methods_metadata_is_none(app):
    # given
    response_data_with_meta = [
        {
            "id": "123",
            "amount": 10,
            "currency": "USD",
            "name": "shipping",
            "description": "Description",
            "maximum_delivery_days": 10,
            "minimum_delivery_days": 2,
            "metadata": None,
        }
    ]

    # when
    response = _parse_list_shipping_methods_response(
        response_data_with_meta, app, "USD"
    )

    # then
    assert response[0].metadata == {}


def test_get_cache_data_for_shipping_list_methods_for_checkout(checkout_with_items):
    # given
    metadata = get_or_create_checkout_metadata(checkout_with_items)
    metadata.store_value_in_private_metadata({"external_app_shipping_id": "something"})
    metadata.save()
    payload_str = generate_checkout_payload(checkout_with_items)
    assert "last_change" in payload_str
    assert "meta" in payload_str
    assert "external_app_shipping_id" in payload_str

    # when
    cache_data = _get_cache_data_for_shipping_list_methods_for_checkout(payload_str)

    # then
    assert "last_change" not in cache_data[0]
    assert "meta" not in cache_data[0]
    assert "external_app_shipping_id" not in cache_data[0]["private_metadata"]
