from unittest import mock

import graphene
from promise import Promise

from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ....webhook.response_schemas.shipping import logger as schema_logger
from ....webhook.response_schemas.utils.annotations import logger as annotations_logger
from ....webhook.transport.shipping_helpers import to_shipping_app_id
from ...webhooks.shared import (
    _get_excluded_shipping_methods_from_response,
    _get_excluded_shipping_methods_or_fetch,
)


@mock.patch.object(annotations_logger, "warning")
@mock.patch.object(schema_logger, "warning")
def test_get_excluded_shipping_methods_from_response(
    mocked_schema_logger, mocked_annotations_logger, app
):
    # given
    external_id = to_shipping_app_id(app, "test-1234")
    response = {
        "excluded_methods": [
            {
                "id": "",
            },
            {
                "id": "not-an-id",
            },
            {
                "id": graphene.Node.to_global_id("Car", "1"),
            },
            {
                "id": graphene.Node.to_global_id("ShippingMethod", "2"),
            },
            {
                "id": external_id,
            },
        ]
    }
    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-gateway.com/apiv2/",
    )

    # when
    excluded_methods = _get_excluded_shipping_methods_from_response(response, webhook)

    # then
    assert len(excluded_methods) == 2
    assert excluded_methods[0].id == "2"
    assert excluded_methods[1].id == external_id
    assert mocked_schema_logger.call_count == 3
    assert mocked_annotations_logger.call_count == 3


@mock.patch.object(annotations_logger, "warning")
@mock.patch.object(schema_logger, "warning")
def test_get_excluded_shipping_methods_from_response_invalid(
    mocked_schema_logger, mocked_annotations_logger, app
):
    # given
    response = {
        "excluded_methods": [
            {
                "id": "not-an-id",
            },
        ]
    }
    webhook = Webhook.objects.create(
        name="shipping-webhook-1",
        app=app,
        target_url="https://shipping-gateway.com/apiv2/",
    )

    # when
    excluded_methods = _get_excluded_shipping_methods_from_response(response, webhook)

    # then
    assert not excluded_methods
    assert mocked_schema_logger.call_count == 1
    assert (
        "Malformed ShippingMethod id was provided:"
        in mocked_schema_logger.call_args[0][0]
    )
    assert mocked_annotations_logger.call_count == 1
    error_msg = mocked_annotations_logger.call_args[0][1]
    assert "Skipping invalid shipping method (FilterShippingMethodsSchema)" in error_msg


@mock.patch("saleor.shipping.webhooks.shared._parse_excluded_shipping_methods")
@mock.patch(
    "saleor.webhook.transport.synchronous.transport.trigger_webhook_sync_promise"
)
@mock.patch(
    "saleor.shipping.webhooks.shared._get_excluded_shipping_methods_from_response"
)
def test_get_excluded_shipping_methods_or_fetch_invalid_response_type(
    mocked_get_excluded,
    mocked_webhook_sync_trigger,
    mocked_parse,
    app,
    checkout,
):
    # given
    mocked_webhook_sync_trigger.return_value = Promise.resolve(["incorrect_type"])
    webhook = Webhook.objects.create(
        name="Simple webhook", app=app, target_url="http://www.example.com/test"
    )
    event_type = WebhookEventSyncType.CHECKOUT_FILTER_SHIPPING_METHODS
    webhook.events.create(event_type=event_type)
    webhooks = Webhook.objects.all()

    # when
    _get_excluded_shipping_methods_or_fetch(
        webhooks, event_type, '{"test":"payload"}', checkout, False, None, {}
    ).get()

    # then
    mocked_get_excluded.assert_not_called()
    mocked_parse.assert_called_once_with([])
