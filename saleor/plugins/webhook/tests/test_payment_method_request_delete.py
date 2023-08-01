import json

import graphene
import mock
import pytest

from ....core.models import EventDelivery
from ....payment.interface import (
    PaymentMethodRequestDeleteData,
    PaymentMethodRequestDeleteResponseData,
)
from ....settings import WEBHOOK_SYNC_TIMEOUT
from ..utils import to_payment_app_id

PAYMENT_METHOD_REQUEST_DELETE = """
subscription {
  event {
    ... on PaymentMethodRequestDelete{
      user{
        id
      }
      paymentMethodId
    }
  }
}
"""


@pytest.fixture
def webhook_payment_method_request_delete_response():
    return {"success": True, "message": "Payment method deleted successfully"}


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_payment_method_request_delete_with_static_payload(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_method_request_delete_app,
    webhook_payment_method_request_delete_response,
):
    # given
    mock_request.return_value = webhook_payment_method_request_delete_response

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = PaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            payment_method_request_delete_app, payment_method_id
        ),
    )

    previous_value = PaymentMethodRequestDeleteResponseData(
        success=False, message="Payment method request delete failed to deliver."
    )

    # when
    response = plugin.payment_method_request_delete(request_delete_data, previous_value)

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.payload.payload == json.dumps(
        {
            "payment_method_id": payment_method_id,
            "user_id": graphene.Node.to_global_id("User", customer_user.pk),
        }
    )
    mock_request.assert_called_once_with(
        payment_method_request_delete_app, delivery, timeout=WEBHOOK_SYNC_TIMEOUT
    )

    assert response == PaymentMethodRequestDeleteResponseData(
        success=True, message=webhook_payment_method_request_delete_response["message"]
    )


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_payment_method_request_delete_with_subscription_payload(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_method_request_delete_app,
    webhook_payment_method_request_delete_response,
):
    # given
    mock_request.return_value = webhook_payment_method_request_delete_response

    webhook = payment_method_request_delete_app.webhooks.first()
    webhook.subscription_query = PAYMENT_METHOD_REQUEST_DELETE
    webhook.save()

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = PaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            payment_method_request_delete_app, payment_method_id
        ),
    )

    previous_value = PaymentMethodRequestDeleteResponseData(
        success=False, message="Payment method request delete failed to deliver."
    )

    # when
    response = plugin.payment_method_request_delete(request_delete_data, previous_value)

    # then
    delivery = EventDelivery.objects.get()
    assert delivery.payload.payload == json.dumps(
        {
            "user": {"id": graphene.Node.to_global_id("User", customer_user.pk)},
            "paymentMethodId": payment_method_id,
        }
    )
    mock_request.assert_called_once_with(
        payment_method_request_delete_app, delivery, timeout=WEBHOOK_SYNC_TIMEOUT
    )

    assert response == PaymentMethodRequestDeleteResponseData(
        success=True, message=webhook_payment_method_request_delete_response["message"]
    )


@mock.patch("saleor.plugins.webhook.tasks.send_webhook_request_sync")
def test_payment_method_request_delete_missing_correct_response_from_webhook(
    mock_request,
    customer_user,
    webhook_plugin,
    payment_method_request_delete_app,
    webhook_payment_method_request_delete_response,
):
    # given
    mock_request.return_value = None

    webhook = payment_method_request_delete_app.webhooks.first()
    webhook.subscription_query = PAYMENT_METHOD_REQUEST_DELETE
    webhook.save()

    plugin = webhook_plugin()

    payment_method_id = "123"

    request_delete_data = PaymentMethodRequestDeleteData(
        user=customer_user,
        payment_method_id=to_payment_app_id(
            payment_method_request_delete_app, payment_method_id
        ),
    )

    previous_value = PaymentMethodRequestDeleteResponseData(
        success=False, message="Payment method request delete failed to deliver."
    )

    # when
    response = plugin.payment_method_request_delete(request_delete_data, previous_value)

    # then
    delivery = EventDelivery.objects.get()

    mock_request.assert_called_once_with(
        payment_method_request_delete_app, delivery, timeout=WEBHOOK_SYNC_TIMEOUT
    )

    assert response == PaymentMethodRequestDeleteResponseData(
        success=False, message="Failed to delivery request."
    )
