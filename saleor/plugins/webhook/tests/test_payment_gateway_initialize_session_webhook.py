import json
from decimal import Decimal
from unittest import mock

import graphene
from freezegun import freeze_time

from ....core import EventDeliveryStatus
from ....core.models import EventDelivery, EventPayload
from ....payment.interface import PaymentGatewayData
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook

PAYMENT_GATEWAY_INITIALIZE_SESSION = """
subscription {
  event{
    ...on PaymentGatewayInitializeSession{
      data
      amount
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


def _assert_with_subscription(
    transaction_object,
    request_data,
    amount,
    webhook,
    expected_data,
    response,
    mock_request,
):
    object_id = graphene.Node.to_global_id(
        transaction_object.__class__.__name__, transaction_object.pk
    )
    payload = {
        "data": request_data,
        "amount": amount,
        "sourceObject": {
            "__typename": transaction_object.__class__.__name__,
            "id": object_id,
        },
    }
    _assert_fields(payload, webhook, expected_data, response, mock_request)


def _assert_with_static_payload(
    transaction_object,
    request_data,
    amount,
    webhook,
    expected_data,
    response,
    mock_request,
):
    transaction_object_id = graphene.Node.to_global_id(
        transaction_object.__class__.__name__, transaction_object.pk
    )
    payload = {"id": transaction_object_id, "data": request_data, "amount": str(amount)}
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
    mock_request.assert_called_once_with(delivery)
    assert response == [
        PaymentGatewayData(app_identifier=webhook_app.identifier, data=expected_data)
    ]


@freeze_time()
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    amount = Decimal("10.00")
    # when
    response = plugin.payment_gateway_initialize_session(
        amount=amount,
        payment_gateways=None,
        source_object=checkout,
        previous_value=None,
    )

    # then
    _assert_with_static_payload(
        checkout, None, amount, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    amount = Decimal("10.00")

    # when
    response = plugin.payment_gateway_initialize_session(
        amount=amount,
        payment_gateways=[
            PaymentGatewayData(app_identifier=webhook_app.identifier, data=data)
        ],
        source_object=checkout,
        previous_value=None,
    )

    # then
    _assert_with_static_payload(
        checkout, data, amount, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    amount = Decimal("10.00")

    # when
    response = plugin.payment_gateway_initialize_session(
        amount=amount,
        payment_gateways=None,
        source_object=checkout,
        previous_value=None,
    )

    # then
    _assert_with_subscription(
        checkout, None, amount, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    amount = Decimal("10.00")

    # when
    response = plugin.payment_gateway_initialize_session(
        amount=amount,
        payment_gateways=[
            PaymentGatewayData(app_identifier=webhook_app.identifier, data=data)
        ],
        source_object=checkout,
        previous_value=None,
    )

    # then
    _assert_with_subscription(
        checkout, data, amount, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    amount = Decimal("10.00")

    # when
    response = plugin.payment_gateway_initialize_session(
        amount=amount,
        payment_gateways=None,
        source_object=checkout,
        previous_value=None,
    )

    # then
    assert not EventPayload.objects.first()
    assert not EventDelivery.objects.first()
    assert not mock_request.called
    assert response == []


@freeze_time()
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    amount = Decimal("10.00")
    # when
    response = plugin.payment_gateway_initialize_session(
        amount=amount,
        payment_gateways=None,
        source_object=order,
        previous_value=None,
    )

    # then
    _assert_with_static_payload(
        order, None, amount, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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
    amount = Decimal("10.00")

    # when
    response = plugin.payment_gateway_initialize_session(
        amount=amount,
        payment_gateways=[
            PaymentGatewayData(app_identifier=webhook_app.identifier, data=data)
        ],
        source_object=order,
        previous_value=None,
    )

    # then
    _assert_with_static_payload(
        order, data, amount, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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

    amount = Decimal("10.00")

    # when
    response = plugin.payment_gateway_initialize_session(
        amount=amount,
        payment_gateways=None,
        source_object=order,
        previous_value=None,
    )

    # then
    _assert_with_subscription(
        order, None, amount, webhook, expected_data, response, mock_request
    )


@freeze_time()
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
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

    amount = Decimal("10.00")

    # when
    response = plugin.payment_gateway_initialize_session(
        amount=amount,
        payment_gateways=[
            PaymentGatewayData(app_identifier=webhook_app.identifier, data=data)
        ],
        source_object=order,
        previous_value=None,
    )

    # then
    _assert_with_subscription(
        order, data, amount, webhook, expected_data, response, mock_request
    )
