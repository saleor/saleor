from unittest import mock
from unittest.mock import Mock, sentinel

import pytest
from freezegun import freeze_time

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....core.taxes import TaxType
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.taxed_payloads import generate_checkout_payload, generate_order_payload
from ..utils import (
    DEFAULT_TAX_CODE,
    DEFAULT_TAX_DESCRIPTION,
    WEBHOOK_TAX_CODES_CACHE_KEY,
    parse_tax_data,
)


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_taxes_for_checkout(
    mock_request,
    permission_handle_taxes,
    webhook_plugin,
    tax_checkout_webhook,
    tax_data_response,
    checkout,
    tax_app_with_webhooks,
):
    # given
    mock_request.return_value = tax_data_response
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout, None)

    # then
    payload = EventPayload.objects.get()
    assert payload.payload == generate_checkout_payload(checkout, taxed=False)
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.CHECKOUT_CALCULATE_TAXES
    assert delivery.payload == payload
    assert delivery.webhook == tax_checkout_webhook
    mock_request.assert_called_once_with(tax_checkout_webhook.app.name, delivery)
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_taxes_for_checkout_no_permission(
    mock_request,
    webhook_plugin,
    checkout,
):
    # given
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_checkout(checkout, None)

    # then
    assert mock_request.call_count == 0
    assert tax_data is None


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_taxes_for_order(
    mock_request,
    permission_handle_taxes,
    webhook_plugin,
    tax_order_webhook,
    tax_data_response,
    order,
    tax_app_with_webhooks,
):
    # given
    mock_request.return_value = tax_data_response
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_order(order, None)

    # then
    payload = EventPayload.objects.get()
    assert payload.payload == generate_order_payload(order, taxed=False)
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert delivery.event_type == WebhookEventSyncType.ORDER_CALCULATE_TAXES
    assert delivery.payload == payload
    assert delivery.webhook == tax_order_webhook
    mock_request.assert_called_once_with(tax_order_webhook.app.name, delivery)
    assert tax_data == parse_tax_data(tax_data_response)


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_get_taxes_for_order_no_permission(
    mock_request,
    webhook_plugin,
    order,
):
    # given
    plugin = webhook_plugin()

    # when
    tax_data = plugin.get_taxes_for_order(order, None)

    # then
    assert mock_request.call_count == 0
    assert tax_data is None


@pytest.fixture
def tax_type():
    return TaxType(
        code="code_2",
        description="description_2",
    )


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
@mock.patch("saleor.plugins.webhook.plugin.cache")
def test_fetch_taxes_data(
    mocked_cache,
    mock_request,
    webhook_plugin,
    tax_codes_response,
    tax_app_with_webhooks,
):
    # given
    plugin = webhook_plugin()
    mock_request.return_value = tax_codes_response
    mocked_cache.get.return_value = None

    # when
    plugin.fetch_taxes_data(None)

    # then
    mocked_cache.set.assert_called_once_with(
        WEBHOOK_TAX_CODES_CACHE_KEY,
        {tax_code["code"]: tax_code["description"] for tax_code in tax_codes_response},
    )


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
@mock.patch("saleor.plugins.webhook.plugin.cache")
def test_get_tax_rate_type_choices(
    mocked_cache,
    mock_request,
    webhook_plugin,
    tax_codes_response,
    tax_app_with_webhooks,
):
    # given
    plugin = webhook_plugin()
    mock_request.return_value = tax_codes_response
    mocked_cache.get.return_value = None

    # when
    tax_types = plugin.get_tax_rate_type_choices(None)

    # then
    assert tax_types == [
        TaxType(code=tax_code["code"], description=tax_code["description"])
        for tax_code in tax_codes_response
    ]


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
@mock.patch("saleor.plugins.webhook.plugin.cache")
def test_get_tax_rate_type_choices_from_cache(
    mocked_cache,
    mock_request,
    webhook_plugin,
    tax_codes_response,
    tax_app_with_webhooks,
    cache,
):
    # given
    plugin = webhook_plugin()
    mock_request.return_value = tax_codes_response
    mocked_cache.get = Mock(
        return_value={
            tax_code["code"]: tax_code["description"] for tax_code in tax_codes_response
        },
    )

    # when
    tax_types = plugin.get_tax_rate_type_choices(None)

    # then
    assert tax_types == [
        TaxType(code=tax_code["code"], description=tax_code["description"])
        for tax_code in tax_codes_response
    ]


@mock.patch("saleor.plugins.webhook.plugin.cache")
def test_assign_tax_code_to_object_meta(
    mocked_cache,
    webhook_plugin,
    tax_app_with_webhooks,
    tax_codes_response,
    tax_type,
    product,
):
    # given
    plugin = webhook_plugin()
    mocked_cache.get = Mock(
        return_value={
            tax_code["code"]: tax_code["description"] for tax_code in tax_codes_response
        }
    )

    # when
    plugin.assign_tax_code_to_object_meta(product, tax_type.code, None)

    # then
    assert product.metadata == {
        f"{tax_app_with_webhooks.identifier}.code": tax_type.code,
        f"{tax_app_with_webhooks.identifier}.description": tax_type.description,
    }


def test_assign_tax_code_to_object_meta_delete(
    webhook_plugin, tax_app_with_webhooks, tax_codes_response, tax_type, product
):
    # given
    product.metadata = {
        f"{tax_app_with_webhooks.identifier}.code": tax_type.code,
        f"{tax_app_with_webhooks.identifier}.description": tax_type.description,
    }

    # when
    plugin = webhook_plugin()
    plugin.assign_tax_code_to_object_meta(product, None, None)

    # then
    assert product.metadata == {}


@mock.patch("saleor.plugins.webhook.plugin.cache")
def test_assign_tax_code_to_object_meta_no_tax_types(
    mocked_cache,
    webhook_plugin,
    tax_app_with_webhooks,
    tax_codes_response,
    tax_type,
    product,
):
    # given
    plugin = webhook_plugin()
    mocked_cache.get = Mock(return_value={})

    # when
    plugin.assign_tax_code_to_object_meta(product, tax_type.code, None)

    # then
    assert product.metadata == {}


@mock.patch("saleor.plugins.webhook.plugin.cache")
def test_assign_tax_code_to_object_meta_wrong_code(
    mocked_cache,
    webhook_plugin,
    tax_app_with_webhooks,
    tax_codes_response,
    tax_type,
    product,
):
    # given
    plugin = webhook_plugin()
    mocked_cache.get = Mock(
        return_value={
            tax_code["code"]: tax_code["description"] for tax_code in tax_codes_response
        },
    )

    # when
    plugin.assign_tax_code_to_object_meta(product, "wrong_code", None)

    # then
    assert product.metadata == {}


def test_get_tax_code_from_object_meta_no_app(
    webhook_plugin,
    product,
):
    # given
    plugin = webhook_plugin()
    previous_value = sentinel.PREVIOUS_VALUE

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, previous_value)

    # then
    assert fetched_tax_type == previous_value


@mock.patch("saleor.plugins.webhook.plugin.cache")
def test_get_tax_code_from_object_meta(
    mocked_cache,
    webhook_plugin,
    tax_app_with_webhooks,
    tax_codes_response,
    tax_type,
    product,
):
    # given
    plugin = webhook_plugin()
    mocked_cache.get = Mock(
        return_value={
            tax_code["code"]: tax_code["description"] for tax_code in tax_codes_response
        },
    )
    product.metadata = {
        f"{tax_app_with_webhooks.identifier}.code": tax_type.code,
        f"{tax_app_with_webhooks.identifier}.description": tax_type.description,
    }

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, None)

    # then
    assert fetched_tax_type == tax_type


@mock.patch("saleor.plugins.webhook.plugin.cache")
def test_get_tax_code_from_object_meta_default_code(
    mocked_cache,
    webhook_plugin,
    tax_app_with_webhooks,
    tax_codes_response,
    product,
):
    # given
    plugin = webhook_plugin()
    mocked_cache.get = Mock(
        return_value={
            tax_code["code"]: tax_code["description"] for tax_code in tax_codes_response
        },
    )

    # when
    fetched_tax_type = plugin.get_tax_code_from_object_meta(product, None)

    # then
    assert fetched_tax_type == TaxType(
        code=DEFAULT_TAX_CODE,
        description=DEFAULT_TAX_DESCRIPTION,
    )
