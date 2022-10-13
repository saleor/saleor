import json
import uuid
from decimal import Decimal
from unittest import mock
from urllib.parse import quote_plus

import graphene
import pytest

from ......order import OrderEvents
from ..... import PaymentError, TransactionKind
from ...webhooks import handle_additional_actions

ERROR_MSG_MISSING_PAYMENT = "Cannot perform payment. There is no active Adyen payment."
ERROR_MSG_MISSING_CHECKOUT = (
    "Cannot perform payment. There is no checkout with this payment."
)


@mock.patch("saleor.payment.gateways.adyen.webhooks.payment_refund_or_void")
@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_post(
    api_call_mock, _, payment_adyen_for_checkout, adyen_plugin
):
    # given
    plugin = adyen_plugin()
    channel_slug = plugin.channel.slug
    payment_adyen_for_checkout.to_confirm = True
    payment_adyen_for_checkout.extra_data = json.dumps(
        [{"payment_data": "test_data", "parameters": ["payload"]}]
    )
    payment_adyen_for_checkout.save(update_fields=["to_confirm", "extra_data"])

    transaction_count = payment_adyen_for_checkout.transactions.all().count()

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": str(checkout.pk)}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "pspReference": "11111",
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, channel_slug
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url
    transactions = payment_adyen_for_checkout.transactions.all()
    assert transactions.count() == transaction_count + 2  # TO_CONFIRM, AUTH

    assert transactions.first().kind == TransactionKind.ACTION_TO_CONFIRM
    assert transactions.last().kind == TransactionKind.AUTH
    assert payment_adyen_for_checkout.order
    assert payment_adyen_for_checkout.checkout is None


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_order_already_created(
    api_call_mock, payment_adyen_for_order, adyen_plugin, order
):
    # given
    plugin = adyen_plugin()
    channel_slug = plugin.channel.slug
    payment_adyen_for_order.to_confirm = True
    payment_adyen_for_order.extra_data = json.dumps(
        [{"payment_data": "test_data", "parameters": ["payload"]}]
    )
    payment_adyen_for_order.save(update_fields=["to_confirm", "extra_data"])

    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_order.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", "1")

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": "1"}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "pspReference": "11111",
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, channel_slug
    )

    # then
    payment_adyen_for_order.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url

    assert payment_adyen_for_order.order
    assert payment_adyen_for_order.checkout is None


@pytest.mark.parametrize(
    "custom_url",
    [
        "adyencheckout://your.package.name",
        "myiOSapp://path",
        "https://checkout.saleor.com/",
    ],
)
@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_handles_return_urls(
    api_call_mock, custom_url, payment_adyen_for_checkout, adyen_plugin
):
    # given
    plugin = adyen_plugin()
    channel_slug = plugin.channel.slug
    payment_adyen_for_checkout.return_url = custom_url
    payment_adyen_for_checkout.to_confirm = True
    payment_adyen_for_checkout.extra_data = json.dumps(
        [{"payment_data": "test_data", "parameters": ["payload"]}]
    )
    payment_adyen_for_checkout.save(
        update_fields=["to_confirm", "extra_data", "return_url"]
    )

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": str(checkout.pk)}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "pspReference": "11111",
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, channel_slug
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 302


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_get(
    api_call_mock, payment_adyen_for_checkout, adyen_plugin
):
    # given
    plugin = adyen_plugin()
    channel_slug = plugin.channel.slug
    payment_adyen_for_checkout.to_confirm = True
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save(update_fields=["to_confirm", "extra_data"])

    transaction_count = payment_adyen_for_checkout.transactions.all().count()

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {
        "payment": payment_id,
        "checkout": str(checkout.pk),
        "payload": "test",
    }

    payment_details_mock = mock.Mock()
    message = {
        "pspReference": "11111",
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, channel_slug
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url
    transactions = payment_adyen_for_checkout.transactions.all()
    assert transactions.count() == transaction_count + 2  # TO_CONFIRM, AUTH
    assert transactions.first().kind == TransactionKind.ACTION_TO_CONFIRM
    assert transactions.last().kind == TransactionKind.AUTH
    assert payment_adyen_for_checkout.order
    assert payment_adyen_for_checkout.checkout is None


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_with_adyen_partial_data(
    api_call_mock, payment_adyen_for_checkout, adyen_plugin
):
    # given
    plugin = adyen_plugin()
    payment = payment_adyen_for_checkout
    channel_slug = plugin.channel.slug
    payment.to_confirm = True
    payment.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment.save(update_fields=["to_confirm", "extra_data"])

    transaction_count = payment.transactions.all().count()

    checkout = payment.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {
        "payment": payment_id,
        "checkout": str(checkout.pk),
        "payload": "test",
    }

    payment_details_mock = mock.Mock()
    message = {
        "additionalData": {
            "order-2-paymentMethod": "visa",
            "threeds2.cardEnrolled": "false",
            "order-2-pspReference": "861643021198177D",
            "order-2-paymentAmount": "GBP 16.29",
            "recurringProcessingModel": "Subscription",
            "paymentMethod": "visa",
            "order-1-pspReference": "861643021155073F",
            "order-1-paymentAmount": "GBP 14.71",
            "order-1-paymentMethod": "givex",
        },
        "pspReference": "861643021198177D",
        "resultCode": "Authorised",
        "merchantReference": "UGF5bWVudDoyNw==",
        "paymentMethod": "visa",
        "shopperLocale": "en_GB",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, channel_slug
    )

    # then
    payment.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url
    transactions = payment.transactions.all()
    assert transactions.count() == transaction_count + 2  # TO_CONFIRM, AUTH
    assert transactions.first().kind == TransactionKind.ACTION_TO_CONFIRM
    assert transactions.last().kind == TransactionKind.AUTH
    assert payment.order
    assert payment.checkout is None

    external_events = payment.order.events.filter(
        type=OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    )
    assert external_events.count() == 1

    external_event = external_events.first()
    event_message = external_event.parameters["message"]
    assert "Partial payment" in event_message
    assert "GBP 16.29" in event_message
    assert "GBP 14.71" in event_message
    assert "861643021198177D" in event_message
    assert "861643021155073F" in event_message
    assert "givex" in event_message
    assert "visa" in event_message

    partial_payments = list(payment.order.payments.exclude(id=payment.id))
    assert len(partial_payments) == 2
    assert all([payment.is_active is False for payment in partial_payments])
    assert all([payment.partial is True for payment in partial_payments])
    assert all([payment.is_active is False for payment in partial_payments])
    assert any(payment.total == Decimal("16.29") for payment in partial_payments)
    assert any(payment.total == Decimal("14.71") for payment in partial_payments)
    assert any(
        payment.psp_reference == "861643021198177D" for payment in partial_payments
    )
    assert any(
        payment.psp_reference == "861643021155073F" for payment in partial_payments
    )


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_with_adyen_partial_data_without_amount(
    api_call_mock, payment_adyen_for_checkout, adyen_plugin
):
    # given
    plugin = adyen_plugin()
    payment = payment_adyen_for_checkout
    channel_slug = plugin.channel.slug
    payment.to_confirm = True
    payment.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment.save(update_fields=["to_confirm", "extra_data"])

    transaction_count = payment.transactions.all().count()

    checkout = payment.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {
        "payment": payment_id,
        "checkout": str(checkout.pk),
        "payload": "test",
    }

    payment_details_mock = mock.Mock()
    message = {
        "additionalData": {
            "order-2-paymentMethod": "visa",
            "threeds2.cardEnrolled": "false",
            "order-2-pspReference": "861643021198177D",
            "recurringProcessingModel": "Subscription",
            "paymentMethod": "visa",
            "order-1-pspReference": "861643021155073F",
            "order-1-paymentAmount": "GBP 14.71",
            "order-1-paymentMethod": "givex",
        },
        "pspReference": "861643021198177D",
        "resultCode": "Authorised",
        "merchantReference": "UGF5bWVudDoyNw==",
        "paymentMethod": "visa",
        "shopperLocale": "en_GB",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, channel_slug
    )

    # then
    payment.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url
    transactions = payment.transactions.all()
    assert transactions.count() == transaction_count + 2  # TO_CONFIRM, AUTH
    assert transactions.first().kind == TransactionKind.ACTION_TO_CONFIRM
    assert transactions.last().kind == TransactionKind.AUTH
    assert payment.order
    assert payment.checkout is None

    external_events = payment.order.events.filter(
        type=OrderEvents.EXTERNAL_SERVICE_NOTIFICATION
    )
    assert external_events.count() == 1

    external_event = external_events.first()
    event_message = external_event.parameters["message"]
    assert "Partial payment" in event_message
    assert "GBP 65.29" in event_message
    assert "GBP 14.71" in event_message
    assert "861643021198177D" in event_message
    assert "861643021155073F" in event_message
    assert "givex" in event_message
    assert "visa" in event_message

    partial_payments = list(payment.order.payments.exclude(id=payment.id))
    assert len(partial_payments) == 2
    assert all([payment.is_active is False for payment in partial_payments])
    assert all([payment.partial is True for payment in partial_payments])
    assert all([payment.is_active is False for payment in partial_payments])
    assert any(payment.total == Decimal("65.29") for payment in partial_payments)
    assert any(payment.total == Decimal("14.71") for payment in partial_payments)
    assert any(
        payment.psp_reference == "861643021198177D" for payment in partial_payments
    )
    assert any(
        payment.psp_reference == "861643021155073F" for payment in partial_payments
    )


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_for_ideal(
    api_call_mock, payment_adyen_for_checkout, adyen_plugin
):
    # given
    plugin = adyen_plugin()
    channel_slug = plugin.channel.slug
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "extra_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    transaction_count = payment_adyen_for_checkout.transactions.all().count()

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {
        "payment": payment_id,
        "checkout": str(checkout.pk),
        "payload": "test",
    }

    payment_details_mock = mock.Mock()
    message = {
        "additionalData": {
            "bankAccount.ownerName": "A. Klaassen",
            "bankAccount.iban": "NL13TEST0123456789",
        },
        "pspReference": "861638465362046G",
        "resultCode": "Authorised",
        "merchantReference": payment_id,
        "paymentMethod": "ideal",
        "shopperLocale": "en_GB",
    }

    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, channel_slug
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url
    transactions = payment_adyen_for_checkout.transactions.all()
    assert transactions.count() == transaction_count + 2  # TO_CONFIRM, CAPTURE
    assert transactions.first().kind == TransactionKind.ACTION_TO_CONFIRM
    assert transactions.last().kind == TransactionKind.CAPTURE
    assert payment_adyen_for_checkout.order
    assert payment_adyen_for_checkout.checkout is None


def test_handle_additional_actions_more_action_required(payment_adyen_for_checkout):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": str(checkout.pk)}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Pending",
        "action": {
            "method": "GET",
            "paymentData": "123",
            "paymentMethodType": "ideal",
            "type": "redirect",
            "url": "https://test.adyen.com/hpp/redirectIdeal.shtml?brandCode=ideal",
        },
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    assert response.status_code == 302
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"method={message['action']['method']}" in response.url
    assert f"paymentData={message['action']['paymentData']}" in response.url
    assert f"paymentMethodType={message['action']['paymentMethodType']}" in response.url
    assert f"type={message['action']['type']}" in response.url
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url

    transaction = payment_adyen_for_checkout.transactions.last()
    assert transaction.kind == TransactionKind.ACTION_TO_CONFIRM
    assert transaction.action_required is True
    assert payment_adyen_for_checkout.order is None
    assert payment_adyen_for_checkout.checkout


def test_handle_additional_actions_payment_does_not_exist(payment_adyen_for_checkout):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    request_mock = mock.Mock()
    request_mock.GET = {
        "payment": payment_id,
        "checkout": payment_adyen_for_checkout.checkout.pk,
    }
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    payment_details_mock.return_value.message = {
        "resultCode": "Test",
    }

    payment_adyen_for_checkout.delete()

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    assert response.status_code == 404
    assert response.content.decode() == ERROR_MSG_MISSING_PAYMENT


def test_handle_additional_actions_payment_lack_of_return_url(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.return_url = None
    payment_adyen_for_checkout.save(update_fields=["extra_data", "return_url"])

    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    request_mock = mock.Mock()
    request_mock.GET = {
        "payment": payment_id,
        "checkout": str(payment_adyen_for_checkout.checkout.pk),
    }
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    payment_details_mock.return_value.message = {
        "resultCode": "Test",
    }

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    assert response.status_code == 404
    assert (
        response.content.decode()
        == "Cannot perform payment. Lack of data about returnUrl."
    )


def test_handle_additional_actions_no_payment_id_in_get(payment_adyen_for_checkout):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    request_mock = mock.Mock()
    request_mock.GET = {}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    assert response.status_code == 404


def test_handle_additional_actions_checkout_not_related_to_payment(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": uuid.uuid4()}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    assert response.status_code == 404
    assert response.content.decode() == ERROR_MSG_MISSING_CHECKOUT


def test_handle_additional_actions_payment_does_not_have_checkout(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.checkout = None
    payment_adyen_for_checkout.save()

    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": uuid.uuid4()}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    assert response.status_code == 404
    assert response.content.decode() == ERROR_MSG_MISSING_CHECKOUT


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_api_call_error(
    api_call_mock,
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save()

    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)

    error_message = "Test error"
    api_call_mock.side_effect = PaymentError(error_message)

    request_mock = mock.Mock()
    request_mock.GET = {
        "payment": payment_id,
        "checkout": str(payment_adyen_for_checkout.checkout.pk),
    }
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    assert response.status_code == 400
    assert response.content.decode() == error_message


def test_handle_additional_actions_payment_not_active(payment_adyen_for_checkout):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.is_active = False
    payment_adyen_for_checkout.save(update_fields=["extra_data", "is_active"])

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": checkout.pk}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    assert response.status_code == 404
    assert response.content.decode() == ERROR_MSG_MISSING_PAYMENT


def test_handle_additional_actions_payment_with_no_adyen_gateway(
    payment_adyen_for_checkout,
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.gateway = "test"
    payment_adyen_for_checkout.save(update_fields=["extra_data", "gateway"])

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": checkout.pk}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    assert response.status_code == 404
    assert response.content.decode() == ERROR_MSG_MISSING_PAYMENT


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_lack_of_parameter_in_request(
    api_call_mock, payment_adyen_for_checkout
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload", "second_param"]}
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": str(checkout.pk)}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(request_mock, payment_details_mock, "channel")

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 400
    assert (
        response.content.decode()
        == "Cannot perform payment. Lack of required parameters in request."
    )
