from unittest import mock

from ....core.models import EventDelivery
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.response_schemas.utils.annotations import logger as annotations_logger
from ....webhook.transport.shipping import (
    parse_list_shipping_methods_response,
)
from ....webhook.transport.synchronous.transport import trigger_webhook_sync


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_trigger_webhook_sync(mock_request, shipping_app):
    data = '{"key": "value"}'
    webhook = shipping_app.webhooks.first()
    trigger_webhook_sync(
        WebhookEventSyncType.SHIPPING_LIST_METHODS_FOR_CHECKOUT, data, webhook, False
    )
    mock_request.assert_called_once()
    assert not EventDelivery.objects.exists()


@mock.patch.object(annotations_logger, "warning")
def test_parse_list_shipping_methods_response_response_incorrect_format(
    mocked_logger, app
):
    # given
    response_data_with_incorrect_format = [[1], 2, "3"]
    # when
    result = parse_list_shipping_methods_response(
        response_data_with_incorrect_format, app, "USD"
    )
    # then
    assert result == []
    # Ensure the warning about invalit method data wa logged
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
    response = parse_list_shipping_methods_response(response_data_with_meta, app, "USD")
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
    response = parse_list_shipping_methods_response(response_data_with_meta, app, "USD")
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
    response = parse_list_shipping_methods_response(response_data_with_meta, app, "USD")

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
    response = parse_list_shipping_methods_response(response_data_with_meta, app, "USD")
    # then
    assert response[0].metadata == {}
