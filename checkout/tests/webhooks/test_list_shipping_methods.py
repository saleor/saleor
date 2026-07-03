from unittest import mock

from ....webhook.response_schemas.utils.annotations import logger as annotations_logger
from ...webhooks.list_shipping_methods import (
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
    ).get()

    # then
    assert not response


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
