import json
from unittest import mock

import graphene
import pytest

from ....core.models import EventDelivery
from ....payment.interface import (
    ListStoredPaymentMethodsRequestData,
    StoredPaymentMethodRequestDeleteData,
    StoredPaymentMethodRequestDeleteResponseData,
    StoredPaymentMethodRequestDeleteResult,
)
from ....settings import WEBHOOK_SYNC_TIMEOUT
from ....webhook.const import WEBHOOK_CACHE_DEFAULT_TIMEOUT
from ....webhook.event_types import WebhookEventSyncType
from ....webhook.models import Webhook
from ....webhook.transport.utils import (
    generate_cache_key_for_webhook,
    to_payment_app_id,
)

STORED_PAYMENT_METHOD_DELETE_REQUESTED = """
subscription {
  event {
    ... on StoredPaymentMethodDeleteRequested{
      user{
        id
      }
      paymentMethodId
      channel{
        id
      }
    }
  }
}
"""


@pytest.fixture
def webhook_stored_payment_method_request_delete_response():
    return {
        "result": StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED.name,
    }


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_stored_payment_method_request_delete_with_static_payload(
    mock_request,
    customer_user,
    webhook_plugin,
    stored_payment_method_request_delete_app,
    webhook_stored_payment_method_request_delete_response,
    channel_USD,
):
    # given
    mock_request.return_value = webhook_stored_payment_method_request_delete_response

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = StoredPaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            stored_payment_method_request_delete_app, payment_method_id
        ),
        channel=channel_USD,
    )

    previous_value = StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER,
        error="Payment method request delete failed to deliver.",
    )

    # when
    response = plugin.stored_payment_method_request_delete(
        request_delete_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.payload.payload == json.dumps(
        {
            "payment_method_id": payment_method_id,
            "user_id": graphene.Node.to_global_id("User", customer_user.pk),
            "channel_slug": channel_USD.slug,
        }
    )
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED, error=None
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_stored_payment_method_request_delete_with_subscription_payload(
    mock_request,
    customer_user,
    webhook_plugin,
    stored_payment_method_request_delete_app,
    webhook_stored_payment_method_request_delete_response,
    channel_USD,
):
    # given
    mock_request.return_value = webhook_stored_payment_method_request_delete_response

    webhook = stored_payment_method_request_delete_app.webhooks.first()
    webhook.subscription_query = STORED_PAYMENT_METHOD_DELETE_REQUESTED
    webhook.save()

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = StoredPaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            stored_payment_method_request_delete_app, payment_method_id
        ),
        channel=channel_USD,
    )

    previous_value = StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER,
        error="Payment method request delete failed to deliver.",
    )

    # when
    response = plugin.stored_payment_method_request_delete(
        request_delete_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.payload.payload == json.dumps(
        {
            "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
            "paymentMethodId": payment_method_id,
            "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
        }
    )
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED, error=None
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_stored_payment_method_request_delete_failure_from_app(
    mock_request,
    customer_user,
    webhook_plugin,
    stored_payment_method_request_delete_app,
    webhook_stored_payment_method_request_delete_response,
    channel_USD,
):
    # given
    expected_error_msg = "Payment method request delete failed1."
    mock_request.return_value = {
        "result": StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE.name,
        "error": expected_error_msg,
    }

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = StoredPaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            stored_payment_method_request_delete_app, payment_method_id
        ),
        channel=channel_USD,
    )

    previous_value = StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER,
        error="Payment method request delete failed to deliver.",
    )

    # when
    response = plugin.stored_payment_method_request_delete(
        request_delete_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.payload.payload == json.dumps(
        {
            "payment_method_id": payment_method_id,
            "user_id": graphene.Node.to_global_id("User", customer_user.pk),
            "channel_slug": channel_USD.slug,
        }
    )
    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE,
        error=expected_error_msg,
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_stored_payment_method_request_delete_missing_response_from_webhook(
    mock_request,
    customer_user,
    webhook_plugin,
    stored_payment_method_request_delete_app,
    webhook_stored_payment_method_request_delete_response,
    channel_USD,
):
    # given
    mock_request.return_value = None

    webhook = stored_payment_method_request_delete_app.webhooks.first()
    webhook.subscription_query = STORED_PAYMENT_METHOD_DELETE_REQUESTED
    webhook.save()

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = StoredPaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            stored_payment_method_request_delete_app, payment_method_id
        ),
        channel=channel_USD,
    )

    previous_value = StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER,
        error="Payment method request delete failed to deliver.",
    )

    # when
    response = plugin.stored_payment_method_request_delete(
        request_delete_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()

    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER,
        error="Failed to delivery request.",
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_stored_payment_method_request_delete_incorrect_result_response_from_webhook(
    mock_request,
    customer_user,
    webhook_plugin,
    stored_payment_method_request_delete_app,
    webhook_stored_payment_method_request_delete_response,
    channel_USD,
):
    # given
    mock_request.return_value = {"result": "incorrect_result"}

    webhook = stored_payment_method_request_delete_app.webhooks.first()
    webhook.subscription_query = STORED_PAYMENT_METHOD_DELETE_REQUESTED
    webhook.save()

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = StoredPaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            stored_payment_method_request_delete_app, payment_method_id
        ),
        channel=channel_USD,
    )

    previous_value = StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER,
        error="Payment method request delete failed to deliver.",
    )

    # when
    response = plugin.stored_payment_method_request_delete(
        request_delete_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()

    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE,
        error="Missing or incorrect `result` in response.",
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_stored_payment_method_request_delete_missing_result_in_response_from_webhook(
    mock_request,
    customer_user,
    webhook_plugin,
    stored_payment_method_request_delete_app,
    webhook_stored_payment_method_request_delete_response,
    channel_USD,
):
    # given
    mock_request.return_value = {}

    webhook = stored_payment_method_request_delete_app.webhooks.first()
    webhook.subscription_query = STORED_PAYMENT_METHOD_DELETE_REQUESTED
    webhook.save()

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = StoredPaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            stored_payment_method_request_delete_app, payment_method_id
        ),
        channel=channel_USD,
    )

    previous_value = StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER,
        error="Payment method request delete failed to deliver.",
    )

    # when
    response = plugin.stored_payment_method_request_delete(
        request_delete_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.get()

    mock_request.assert_called_once_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELETE,
        error="Missing or incorrect `result` in response.",
    )


@mock.patch("saleor.webhook.transport.synchronous.transport.cache.delete")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.set")
@mock.patch("saleor.webhook.transport.synchronous.transport.cache.get")
@mock.patch("saleor.webhook.transport.synchronous.transport.send_webhook_request_sync")
def test_stored_payment_method_request_delete_invalidates_cache_for_app(
    mocked_request,
    mocked_cache_get,
    mocked_cache_set,
    mocked_cache_delete,
    customer_user,
    webhook_plugin,
    stored_payment_method_request_delete_app,
    webhook_stored_payment_method_request_delete_response,
    channel_USD,
):
    # given
    mocked_cache_get.return_value = None

    webhook = Webhook.objects.create(
        name="list_stored_payment_methods",
        app=stored_payment_method_request_delete_app,
        target_url="http://localhost:8000/endpoint/",
    )
    webhook.events.create(
        event_type=WebhookEventSyncType.LIST_STORED_PAYMENT_METHODS,
    )
    list_stored_payment_methods_response = {"paymentMethods": []}
    mocked_request.side_effect = [
        list_stored_payment_methods_response,
        webhook_stored_payment_method_request_delete_response,
    ]

    webhook = stored_payment_method_request_delete_app.webhooks.first()
    webhook.subscription_query = STORED_PAYMENT_METHOD_DELETE_REQUESTED
    webhook.save()

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = StoredPaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            stored_payment_method_request_delete_app, payment_method_id
        ),
        channel=channel_USD,
    )

    previous_value = StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.FAILED_TO_DELIVER,
        error="Payment method request delete failed to deliver.",
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
        stored_payment_method_request_delete_app.id,
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
    response = plugin.stored_payment_method_request_delete(
        request_delete_data, previous_value
    )

    # then
    delivery = EventDelivery.objects.filter(
        event_type=WebhookEventSyncType.STORED_PAYMENT_METHOD_DELETE_REQUESTED
    ).first()
    assert delivery.payload.payload == json.dumps(
        {
            "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
            "paymentMethodId": payment_method_id,
            "channel": {"id": graphene.Node.to_global_id("Channel", channel_USD.pk)},
        }
    )
    # delete the same cache key as created when fetching stored payment methods
    mocked_cache_delete.assert_called_once_with(expected_cache_key)

    mocked_request.assert_called_with(delivery, timeout=WEBHOOK_SYNC_TIMEOUT)

    assert response == StoredPaymentMethodRequestDeleteResponseData(
        result=StoredPaymentMethodRequestDeleteResult.SUCCESSFULLY_DELETED, error=None
    )
