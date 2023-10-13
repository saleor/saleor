import json

import graphene
import mock
import pytest

from ....core.models import EventDelivery
from ....payment.interface import (
    PaymentGatewayInitializeTokenizationRequestData,
    PaymentGatewayInitializeTokenizationResponseData,
    PaymentGatewayInitializeTokenizationResult,
)
from ....settings import WEBHOOK_SYNC_TIMEOUT

PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION = """
subscription {
  event {
    ... on PaymentGatewayInitializeTokenizationSession{
      user{
        id
      }
      channel{
        id
      }
      data
    }
  }
}
"""


@pytest.fixture
def webhook_payment_gateway_initialize_tokenization_response():
    return {
        "result": (
            PaymentGatewayInitializeTokenizationResult.SUCCESSFULLY_INITIALIZED.name
        ),
        "data": {"foo": "bar"},
    }


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_gateway_initialize_tokenization_with_static_payload(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_gateway_initialize_tokenization_app,
    webhook_payment_gateway_initialize_tokenization_response,
    channel_USD,
):
    # given
    mock_request.return_value = webhook_payment_gateway_initialize_tokenization_response

    plugin = webhook_plugin()

    expected_data = {"foo": "bar"}
    request_data = PaymentGatewayInitializeTokenizationRequestData(
        user=customer_user,
        app_identifier=payment_gateway_initialize_tokenization_app.identifier,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentGatewayInitializeTokenizationResponseData(
        result=PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER,
        error="Payment gateway initialize tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_gateway_initialize_tokenization(
        request_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()
    assert json.loads(delivery.payload.payload) == {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
        "data": expected_data,
    }
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentGatewayInitializeTokenizationResponseData(
        result=PaymentGatewayInitializeTokenizationResult.SUCCESSFULLY_INITIALIZED,
        error=None,
        data=webhook_payment_gateway_initialize_tokenization_response["data"],
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_gateway_initialize_tokenization_with_subscription_payload(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_gateway_initialize_tokenization_app,
    webhook_payment_gateway_initialize_tokenization_response,
    channel_USD,
):
    # given
    mock_request.return_value = webhook_payment_gateway_initialize_tokenization_response

    webhook = payment_gateway_initialize_tokenization_app.webhooks.first()
    webhook.subscription_query = PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION
    webhook.save()

    plugin = webhook_plugin()

    expected_data = {"foo": "bar"}

    request_data = PaymentGatewayInitializeTokenizationRequestData(
        user=customer_user,
        app_identifier=payment_gateway_initialize_tokenization_app.identifier,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentGatewayInitializeTokenizationResponseData(
        result=PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER,
        error="Payment gateway initialize tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_gateway_initialize_tokenization(
        request_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()
    assert json.loads(delivery.payload.payload) == {
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
        "data": expected_data,
        "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
    }
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentGatewayInitializeTokenizationResponseData(
        result=PaymentGatewayInitializeTokenizationResult.SUCCESSFULLY_INITIALIZED,
        error=None,
        data=webhook_payment_gateway_initialize_tokenization_response["data"],
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_gateway_initialize_tokenization_missing_correct_response_from_webhook(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_gateway_initialize_tokenization_app,
    channel_USD,
):
    # given
    mock_request.return_value = None

    webhook = payment_gateway_initialize_tokenization_app.webhooks.first()
    webhook.subscription_query = PAYMENT_GATEWAY_INITIALIZE_TOKENIZATION
    webhook.save()

    plugin = webhook_plugin()

    expected_data = {"foo": "bar"}

    request_data = PaymentGatewayInitializeTokenizationRequestData(
        user=customer_user,
        app_identifier=payment_gateway_initialize_tokenization_app.identifier,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentGatewayInitializeTokenizationResponseData(
        result=PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER,
        error="Payment gateway initialize tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_gateway_initialize_tokenization(
        request_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()

    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentGatewayInitializeTokenizationResponseData(
        result=PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER,
        error="Failed to delivery request.",
        data=None,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_gateway_initialize_tokenization_failure_from_app(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_gateway_initialize_tokenization_app,
    channel_USD,
):
    # given
    expected_error_msg = "Expected error msg."
    mock_request.return_value = {
        "result": PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE.name,
        "error": expected_error_msg,
        "data": None,
    }

    plugin = webhook_plugin()

    expected_data = {"foo": "bar"}
    request_data = PaymentGatewayInitializeTokenizationRequestData(
        user=customer_user,
        app_identifier=payment_gateway_initialize_tokenization_app.identifier,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentGatewayInitializeTokenizationResponseData(
        result=PaymentGatewayInitializeTokenizationResult.FAILED_TO_DELIVER,
        error="Payment gateway initialize tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_gateway_initialize_tokenization(
        request_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()
    assert json.loads(delivery.payload.payload) == {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
        "data": expected_data,
    }
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentGatewayInitializeTokenizationResponseData(
        result=PaymentGatewayInitializeTokenizationResult.FAILED_TO_INITIALIZE,
        error=expected_error_msg,
        data=None,
    )
