import json
from unittest import mock

import graphene
from freezegun import freeze_time

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....payment.interface import PaymentGatewayData
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ....webhook.payloads import generate_checkout_payload, generate_order_payload

PAYMENT_GATEWAY_INITIALIZE_SESSION = """
subscription {
  event{
    ...on PaymentGatewayInitializeSession{
      data
      sourceObject{
        __typename
        ... on Checkout{
          id
        }
        ... on Order{
          id
        }
      }
    }
  }
}
"""


def _assert_for_checkout_with_subscription(
    checkout, request_data, webhook, expected_data, response, mock_request
):
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    payload = {
        "data": request_data,
        "sourceObject": {"__typename": "Checkout", "id": checkout_id},
    }
    _assert_fields(payload, webhook, expected_data, response, mock_request)


def _assert_for_order_with_subscription(
    order, request_data, webhook, expected_data, response, mock_request
):
    order_id = graphene.Node.to_global_id("Order", order.pk)
    payload = {
        "data": request_data,
        "sourceObject": {"__typename": "Order", "id": order_id},
    }
    _assert_fields(payload, webhook, expected_data, response, mock_request)


def _assert_for_checkout_with_static_payload(
    checkout, request_data, webhook, expected_data, response, mock_request
):
    payload = json.loads(generate_checkout_payload(checkout, None))
    payload[0]["data"] = request_data
    _assert_fields(payload, webhook, expected_data, response, mock_request)


def _assert_for_order_with_static_payload(
    order, request_data, webhook, expected_data, response, mock_request
):
    payload = json.loads(generate_order_payload(order, None))
    payload[0]["data"] = request_data
    _assert_fields(payload, webhook, expected_data, response, mock_request)


def _assert_fields(payload, webhook, expected_data, response, mock_request):
    webhook_app = webhook.app
    event_payload = EventPayload.objects.get()
    assert json.loads(event_payload.payload) == payload
    delivery = EventDelivery.objects.get()
    assert delivery.status == EventDeliveryStatus.PENDING
    assert (
        delivery.event_type == WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    )
    assert delivery.payload == event_payload
    assert delivery.webhook == webhook
    mock_request.assert_called_once_with(webhook.app.name, delivery)
    assert response == [
        PaymentGatewayData(app_identifier=webhook_app.identifier, data=expected_data)
    ]


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_gateway_initialize_checkout_without_request_data_and_static_payload(
    mock_request, webhook_plugin, webhook_app, checkout, permission_manage_payments
):
    # given
    expected_data = {"some": "json data"}
    mock_request.return_value = expected_data
    plugin = webhook_plugin()

    webhook_app.identifier = "app.identifier"
    webhook_app.save()
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)

    # when
    response = plugin.payment_gateway_initialize_session(
        payment_gateways=None, transaction_object=checkout, previous_value=None
    )

    # then
    _assert_for_checkout_with_static_payload(
        checkout, None, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_gateway_initialize_checkout_with_request_data_and_static_payload(
    mock_request, webhook_plugin, webhook_app, checkout, permission_manage_payments
):
    # given
    data = {"some": "request-data"}
    expected_data = {"some": "json data"}
    mock_request.return_value = expected_data
    plugin = webhook_plugin()

    webhook_app.identifier = "app.identifier"
    webhook_app.save()
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)

    # when
    response = plugin.payment_gateway_initialize_session(
        payment_gateways=[
            PaymentGatewayData(app_identifier=webhook_app.identifier, data=data)
        ],
        transaction_object=checkout,
        previous_value=None,
    )

    # then
    _assert_for_checkout_with_static_payload(
        checkout, data, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_gateway_initialize_checkout_without_request_data(
    mock_request, webhook_plugin, webhook_app, checkout, permission_manage_payments
):
    # given
    expected_data = {"some": "json data"}
    mock_request.return_value = expected_data
    plugin = webhook_plugin()

    webhook_app.identifier = "app.identifier"
    webhook_app.save()
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=PAYMENT_GATEWAY_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)

    # when
    response = plugin.payment_gateway_initialize_session(
        payment_gateways=None, transaction_object=checkout, previous_value=None
    )

    # then
    _assert_for_checkout_with_subscription(
        checkout, None, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_gateway_initialize_checkout_with_request_data(
    mock_request, webhook_plugin, webhook_app, checkout, permission_manage_payments
):
    # given
    data = {"some": "request-data"}
    expected_data = {"some": "json data"}
    mock_request.return_value = expected_data
    plugin = webhook_plugin()

    webhook_app.identifier = "app.identifier"
    webhook_app.save()
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=PAYMENT_GATEWAY_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)

    # when
    response = plugin.payment_gateway_initialize_session(
        payment_gateways=[
            PaymentGatewayData(app_identifier=webhook_app.identifier, data=data)
        ],
        transaction_object=checkout,
        previous_value=None,
    )

    # then
    _assert_for_checkout_with_subscription(
        checkout, data, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_gateway_initialize_session_skips_app_without_identifier(
    mock_request, webhook_plugin, webhook_app, checkout, permission_manage_payments
):
    # given
    plugin = webhook_plugin()

    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)

    # when
    response = plugin.payment_gateway_initialize_session(
        payment_gateways=None, transaction_object=checkout, previous_value=None
    )

    # then
    assert not EventPayload.objects.first()
    assert not EventDelivery.objects.first()
    assert not mock_request.called
    assert response == []


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_gateway_initialize_order_without_request_data_static_payload(
    mock_request, webhook_plugin, webhook_app, order, permission_manage_payments
):
    # given
    expected_data = {"some": "json data"}
    mock_request.return_value = expected_data
    plugin = webhook_plugin()

    webhook_app.identifier = "app.identifier"
    webhook_app.save()
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)

    # when
    response = plugin.payment_gateway_initialize_session(
        payment_gateways=None, transaction_object=order, previous_value=None
    )

    # then
    _assert_for_order_with_static_payload(
        order, None, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_gateway_initialize_order_with_request_data_static_payload(
    mock_request, webhook_plugin, webhook_app, order, permission_manage_payments
):
    # given
    data = {"some": "request-data"}
    expected_data = {"some": "json data"}
    mock_request.return_value = expected_data
    plugin = webhook_plugin()

    webhook_app.identifier = "app.identifier"
    webhook_app.save()
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)

    # when
    response = plugin.payment_gateway_initialize_session(
        payment_gateways=[
            PaymentGatewayData(app_identifier=webhook_app.identifier, data=data)
        ],
        transaction_object=order,
        previous_value=None,
    )

    # then
    _assert_for_order_with_static_payload(
        order, data, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_gateway_initialize_session_for_order_without_request_data(
    mock_request, webhook_plugin, webhook_app, order, permission_manage_payments
):
    # given
    expected_data = {"some": "json data"}
    mock_request.return_value = expected_data
    plugin = webhook_plugin()

    webhook_app.identifier = "app.identifier"
    webhook_app.save()
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=PAYMENT_GATEWAY_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)

    # when
    response = plugin.payment_gateway_initialize_session(
        payment_gateways=None, transaction_object=order, previous_value=None
    )

    # then
    _assert_for_order_with_subscription(
        order, None, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_gateway_initialize_session_for_order_with_request_data(
    mock_request, webhook_plugin, webhook_app, order, permission_manage_payments
):
    # given
    data = {"some": "request-data"}
    expected_data = {"some": "json data"}
    mock_request.return_value = expected_data
    plugin = webhook_plugin()

    webhook_app.identifier = "app.identifier"
    webhook_app.save()
    webhook_app.permissions.add(permission_manage_payments)
    webhook = Webhook.objects.create(
        name="Webhook",
        app=webhook_app,
        subscription_query=PAYMENT_GATEWAY_INITIALIZE_SESSION,
    )
    event_type = WebhookEventSyncType.PAYMENT_GATEWAY_INITIALIZE_SESSION
    webhook.events.create(event_type=event_type)

    # when
    response = plugin.payment_gateway_initialize_session(
        payment_gateways=[
            PaymentGatewayData(app_identifier=webhook_app.identifier, data=data)
        ],
        transaction_object=order,
        previous_value=None,
    )

    # then
    _assert_for_order_with_subscription(
        order, data, webhook, expected_data, response, mock_request
    )
