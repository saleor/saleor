import json
from unittest import mock

import graphene
import pytest

from ....core.models import EventDelivery
from ....payment.interface import (
    ListStoredPaymentMethodsRequestData,
    PaymentMethodProcessTokenizationRequestData,
    PaymentMethodTokenizationResponseData,
    PaymentMethodTokenizationResult,
)
from ....settings import WEBHOOK_SYNC_TIMEOUT
from ....webhook.const import WEBHOOK_CACHE_DEFAULT_TIMEOUT
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ....webhook.transport.utils import (
    generate_cache_key_for_webhook,
    to_payment_app_id,
)

PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION = """
subscription{
  event{
    ...on PaymentMethodProcessTokenizationSession{
      id
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
def webhook_payment_method_process_tokenization_response():
    return {
        "result": PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name,
        "id": "payment-method-id",
        "data": {"foo": "bar"},
    }


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_method_process_tokenization_with_static_payload(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_method_process_tokenization_app,
    webhook_payment_method_process_tokenization_response,
    channel_USD,
    app,
):
    # given
    mock_request.return_value = webhook_payment_method_process_tokenization_response

    plugin = webhook_plugin()

    expected_payment_method_id = "payment-method-id"
    expected_saleor_id = to_payment_app_id(
        payment_method_process_tokenization_app, expected_payment_method_id
    )

    expected_data = {"foo": "bar"}
    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_saleor_id,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Payment method process tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_method_process_tokenization(request_data, previous_value)

    # then
    delivery = EventDelivery.objects.get()
    assert json.loads(delivery.payload.payload) == {
        "id": expected_payment_method_id,
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
        "data": expected_data,
    }
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED,
        id=to_payment_app_id(
            payment_method_process_tokenization_app,
            webhook_payment_method_process_tokenization_response["id"],
        ),
        error=None,
        data=webhook_payment_method_process_tokenization_response["data"],
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_method_process_tokenization_with_subscription_payload(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_method_process_tokenization_app,
    webhook_payment_method_process_tokenization_response,
    channel_USD,
    app,
):
    # given
    mock_request.return_value = webhook_payment_method_process_tokenization_response

    webhook = payment_method_process_tokenization_app.webhooks.first()
    webhook.subscription_query = PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION
    webhook.save()

    plugin = webhook_plugin()

    expected_payment_method_id = "payment-method-id"
    expected_saleor_id = to_payment_app_id(
        payment_method_process_tokenization_app, expected_payment_method_id
    )

    expected_data = {"foo": "bar"}

    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_saleor_id,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Payment method process tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_method_process_tokenization(request_data, previous_value)

    # then
    delivery = EventDelivery.objects.get()
    assert json.loads(delivery.payload.payload) == {
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
        "data": expected_data,
        "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
        "id": expected_payment_method_id,
    }
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED,
        id=to_payment_app_id(
            payment_method_process_tokenization_app,
            webhook_payment_method_process_tokenization_response["id"],
        ),
        error=None,
        data=webhook_payment_method_process_tokenization_response["data"],
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_method_process_tokenization_missing_correct_response_from_webhook(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_method_process_tokenization_app,
    channel_USD,
    app,
):
    # given
    mock_request.return_value = None

    webhook = payment_method_process_tokenization_app.webhooks.first()
    webhook.subscription_query = PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION
    webhook.save()

    plugin = webhook_plugin()

    expected_id = to_payment_app_id(
        payment_method_process_tokenization_app, "payment-method-id"
    )
    expected_data = {"foo": "bar"}

    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_id,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Payment method process tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_method_process_tokenization(request_data, previous_value)

    # then
    delivery = EventDelivery.objects.get()

    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Failed to delivery request.",
        id=None,
        data=None,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_method_process_tokenization_failure_from_app(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_method_process_tokenization_app,
    channel_USD,
    app,
):
    # given
    expected_error_msg = "Expected error msg."
    mock_request.return_value = {
        "result": PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE.name,
        "error": expected_error_msg,
        "data": None,
    }

    plugin = webhook_plugin()

    expected_payment_method_id = "payment-method-id"
    expected_saleor_id = to_payment_app_id(
        payment_method_process_tokenization_app, expected_payment_method_id
    )

    expected_data = {"foo": "bar"}
    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_saleor_id,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Payment method process tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_method_process_tokenization(request_data, previous_value)

    # then
    delivery = EventDelivery.objects.get()
    assert json.loads(delivery.payload.payload) == {
        "id": expected_payment_method_id,
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
        "data": expected_data,
    }
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE,
        error=expected_error_msg,
        id=None,
        data=None,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_method_process_tokenization_additional_action_required(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_method_process_tokenization_app,
    channel_USD,
    app,
):
    # given
    expected_payment_method_id = "payment-method-id"
    expected_saleor_id = to_payment_app_id(
        payment_method_process_tokenization_app, expected_payment_method_id
    )

    expected_additiona_data = {"foo": "bar1"}
    mock_request.return_value = {
        "result": PaymentMethodTokenizationResult.ADDITIONAL_ACTION_REQUIRED.name,
        "id": expected_payment_method_id,
        "data": expected_additiona_data,
    }

    plugin = webhook_plugin()

    expected_data = {"foo": "bar"}
    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_saleor_id,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Payment method process tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_method_process_tokenization(request_data, previous_value)

    # then
    delivery = EventDelivery.objects.get()
    assert json.loads(delivery.payload.payload) == {
        "id": expected_payment_method_id,
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
        "data": expected_data,
    }
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.ADDITIONAL_ACTION_REQUIRED,
        id=to_payment_app_id(
            payment_method_process_tokenization_app, expected_payment_method_id
        ),
        data=expected_additiona_data,
        error=None,
    )


@pytest.mark.parametrize(
    "result",
    [
        PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED.name,
        PaymentMethodTokenizationResult.ADDITIONAL_ACTION_REQUIRED.name,
    ],
)
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_payment_method_process_tokenization_missing_required_id(
    mock_request,
    result,
    customer_user,
    webhook_plugin,
    payment_method_process_tokenization_app,
    channel_USD,
    app,
):
    # given
    expected_error_msg = "Missing payment method `id` in response."
    mock_request.return_value = {
        "result": result,
        "data": None,
    }

    plugin = webhook_plugin()

    expected_payment_method_id = "payment-method-id"
    expected_saleor_id = to_payment_app_id(
        payment_method_process_tokenization_app, expected_payment_method_id
    )
    expected_data = {"foo": "bar"}
    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_saleor_id,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Payment method process tokenization failed to deliver.",
        data=None,
    )

    # when
    response = plugin.payment_method_process_tokenization(request_data, previous_value)

    # then
    delivery = EventDelivery.objects.get()
    assert json.loads(delivery.payload.payload) == {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
        "data": expected_data,
        "id": expected_payment_method_id,
    }
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_TOKENIZE,
        error=expected_error_msg,
        id=None,
        data=None,
    )


@pytest.mark.parametrize(
    "result",
    [
        PaymentMethodTokenizationResult.SUCCESSFULLY_TOKENIZED,
        PaymentMethodTokenizationResult.PENDING,
    ],
)
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.delete")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_expected_result_invalidates_cache_for_app(
    mocked_request,
    mocked_cache_get,
    mocked_cache_set,
    mocked_cache_delete,
    result,
    customer_user,
    webhook_plugin,
    payment_method_process_tokenization_app,
    webhook_payment_method_process_tokenization_response,
    channel_USD,
    app,
):
    # given
    mocked_cache_get.return_value = None

    webhook = Webhook.objects.create(
        name="list_stored_payment_methods",
        app=payment_method_process_tokenization_app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
    )
    list_stored_payment_methods_response = {"paymentMethods": []}
    response = webhook_payment_method_process_tokenization_response
    response["result"] = result.name
    mocked_request.side_effect = [
        list_stored_payment_methods_response,
        response,
    ]

    webhook = payment_method_process_tokenization_app.webhooks.first()
    webhook.subscription_query = PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION
    webhook.save()

    plugin = webhook_plugin()

    expected_payment_method_id = "payment-method-id"
    expected_saleor_id = to_payment_app_id(
        payment_method_process_tokenization_app, expected_payment_method_id
    )
    expected_data = {"foo": "bar"}

    request_data = PaymentMethodProcessTokenizationRequestData(
        user=customer_user,
        id=expected_saleor_id,
        channel=channel_USD,
        data=expected_data,
    )

    previous_value = PaymentMethodTokenizationResponseData(
        result=PaymentMethodTokenizationResult.FAILED_TO_DELIVER,
        error="Payment method process tokenization failed to deliver.",
        data=None,
    )

    data = ListStoredPaymentMethodsRequestData(
        channel=channel_USD,
        user=customer_user,
    )
    expected_payload = {
        "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        "channel_slug": channel_USD.slug,
    }
    expected_cache_key = generate_cache_key_for_webhook(
        expected_payload,
        webhook.target_url,
        WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
        payment_method_process_tokenization_app.id,
    )

    # call mocked list_stored_payment_methods to call mocked cache logic
    # this will make sure that we're deleting the same cache key as the one created
    # in list_stored_payment_methods
    plugin.list_stored_payment_methods(data, [])

    mocked_cache_get.assert_called_once_with(expected_cache_key)
    mocked_cache_set.assert_called_once_with(
        expected_cache_key,
        list_stored_payment_methods_response,
        timeout=WEBHOOK_CACHE_DEFAULT_TIMEOUT,
    )

    # when
    response = plugin.payment_method_process_tokenization(request_data, previous_value)

    # then
    delivery = EventDelivery.objects.filter(
        event_type=WebhookEventSyncType.PAYMENT_METHOD_PROCESS_TOKENIZATION_SESSION
    ).first()
    assert json.loads(delivery.payload.payload) == {
        "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
        "data": expected_data,
        "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
        "id": expected_payment_method_id,
    }

    # delete the same cache key as created when fetching stored payment methods
    mocked_cache_delete.assert_called_once_with(expected_cache_key)

    mocked_request.assert_called_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == PaymentMethodTokenizationResponseData(
        result=result,
        id=to_payment_app_id(
            payment_method_process_tokenization_app,
            webhook_payment_method_process_tokenization_response["id"],
        ),
        error=None,
        data=webhook_payment_method_process_tokenization_response["data"],
    )
