import json
from decimal import Decimal
from unittest import mock
from urllib.parse import quote_plus

import graphene
import pytest
from django.contrib.auth.hashers import make_password

from .....order import OrderStatus
from .... import ChargeStatus, PaymentError, TransactionKind
from ....models import Transaction
from ..utils import get_price_amount
from ..webhooks import (
    create_new_transaction,
    handle_additional_actions,
    handle_authorization,
    handle_cancel_or_refund,
    handle_cancellation,
    handle_capture,
    handle_failed_capture,
    handle_failed_refund,
    handle_pending,
    handle_refund,
    handle_reversed_refund,
    prepare_api_request_data,
    validate_auth_user,
    validate_hmac_signature,
    webhook_not_implemented,
)


@pytest.fixture()
def notification():
    def fun(
        event_code=None,
        success=None,
        psp_reference=None,
        merchant_reference=None,
        value=None,
    ):
        event_code = event_code or "AUTHORISATION"
        success = success or "true"
        psp_reference = psp_reference or "852595499936560C"
        merchant_reference = merchant_reference or "UGF5bWVudDoxNw=="
        value = value or 1130

        return {
            "additionalData": {},
            "eventCode": event_code,
            "success": success,
            "eventDate": "2019-06-28T18:03:50+01:00",
            "merchantAccountCode": "SaleorECOM",
            "pspReference": psp_reference,
            "merchantReference": merchant_reference,
            "amount": {"value": value, "currency": "USD"},
        }

    return fun


def test_handle_authorization(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    handle_authorization(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.AUTH


def test_handle_authorization_with_adyen_auto_capture(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    config.connection_params["adyen_auto_capture"] = True
    handle_authorization(notification, config)

    assert payment.transactions.count() == 1
    assert payment.transactions.get().kind == TransactionKind.CAPTURE


@pytest.mark.vcr
def test_handle_authorization_with_auto_capture(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        psp_reference="853596537720508F",
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    config.auto_capture = True
    config.connection_params["adyen_auto_capture"] = False

    handle_authorization(notification, config)

    payment.refresh_from_db()
    assert payment.transactions.count() == 2
    assert payment.transactions.first().kind == TransactionKind.AUTH
    assert payment.transactions.last().kind == TransactionKind.CAPTURE
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED


def test_handle_authorization_with_adyen_auto_capture_and_payment_charged(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    config.connection_params["adyen_auto_capture"] = True
    handle_authorization(notification, config)

    # payment already has a charge status no need to handle auth action
    assert payment.transactions.count() == 0


def test_handle_cancel(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_cancellation(notification, config)

    payment.order.refresh_from_db()
    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.CANCEL

    assert payment.order.status == OrderStatus.CANCELED


def test_handle_cancel_already_canceleld(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.CANCEL)

    handle_cancellation(notification, config)

    assert payment.transactions.count() == 1


@mock.patch("saleor.payment.gateways.adyen.webhooks.order_captured")
def test_handle_capture(
    mocked_captured, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_capture(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.CAPTURE
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    mocked_captured.assert_called_once_with(
        payment.order, None, transaction.amount, payment
    )


def test_handle_capture_with_payment_already_charged(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_capture(notification, config)

    # Payment is already captured so no need to save capture transaction
    assert payment.transactions.count() == 0


@pytest.mark.parametrize(
    "charge_status", [ChargeStatus.NOT_CHARGED, ChargeStatus.FULLY_CHARGED]
)
def test_handle_failed_capture(
    charge_status, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = charge_status
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_failed_capture(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.CAPTURE_FAILED
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED


def test_handle_failed_capture_partial_charge(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount += payment.total * 2
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_failed_capture(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.CAPTURE_FAILED
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.PARTIALLY_CHARGED


def test_handle_pending(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_pending(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.PENDING
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.PENDING


def test_handle_pending_with_adyen_auto_capture(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    config.connection_params["adyen_auto_capture"] = True

    handle_pending(notification, config)

    # in case of autocapture we don't want to store the pending status as all payments
    # by default get capture status.
    assert payment.transactions.count() == 1
    assert payment.transactions.get().kind == TransactionKind.PENDING
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.PENDING


def test_handle_pending_already_pending(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.PENDING
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.PENDING)

    handle_pending(notification, config)

    assert payment.transactions.count() == 1


@mock.patch("saleor.payment.gateways.adyen.webhooks.order_refunded")
def test_handle_refund(
    mock_order_refunded, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_refund(notification, config)

    assert payment.transactions.count() == 1
    transaction = payment.transactions.get()
    assert transaction.is_success is True
    assert transaction.kind == TransactionKind.REFUND
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.captured_amount == Decimal("0.00")

    mock_order_refunded.assert_called_once_with(
        payment.order, None, transaction.amount, payment
    )


@mock.patch("saleor.payment.gateways.adyen.webhooks.order_refunded")
def test_handle_refund_already_refunded(
    mock_order_refunded, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.captured_amount = Decimal("0.00")
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    create_new_transaction(notification, payment, TransactionKind.REFUND)
    config = adyen_plugin().config

    handle_refund(notification, config)

    assert payment.transactions.count() == 1
    assert not mock_order_refunded.called


def test_handle_failed_refund_missing_transaction(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    handle_failed_refund(notification, config)

    assert payment.transactions.count() == 0


def test_handle_failed_refund_with_transaction_refund_ongoing(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.REFUND_ONGOING)
    handle_failed_refund(notification, config)

    assert (
        payment.transactions.count() == 3
    )  # REFUND_ONGOING, REFUND_FAILED, FULLY_CHARGED
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.total == payment.captured_amount


def test_handle_failed_refund_with_transaction_refund(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.captured_amount = Decimal("0.0")
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.REFUND)
    handle_failed_refund(notification, config)

    payment.refresh_from_db()
    assert payment.transactions.count() == 3  # REFUND, REFUND_FAILED, FULLY_CHARGED
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.total == payment.captured_amount


def test_handle_reversed_refund(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.captured_amount = Decimal("0.0")
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    handle_reversed_refund(notification, config)

    payment.refresh_from_db()
    assert payment.transactions.count() == 1  # REFUND_REVERSED
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.total == payment.captured_amount


def test_handle_reversed_refund_already_processed(
    notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config
    create_new_transaction(notification, payment, TransactionKind.REFUND_REVERSED)
    handle_reversed_refund(notification, config)

    payment.refresh_from_db()
    assert payment.transactions.count() == 1


def test_webhook_not_implemented(notification, adyen_plugin, payment_adyen_for_order):
    payment = payment_adyen_for_order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    config = adyen_plugin().config

    webhook_not_implemented(notification, config)

    assert payment.order.events.count() == 1


@mock.patch("saleor.payment.gateways.adyen.webhooks.handle_refund")
def test_handle_cancel_or_refund_action_refund(
    mock_handle_refund, notification, adyen_plugin, payment_adyen_for_order
):

    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    config = adyen_plugin().config
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    notification["additionalData"]["modification.action"] = "refund"

    handle_cancel_or_refund(notification, config)

    mock_handle_refund.assert_called_once_with(notification, config)


@mock.patch("saleor.payment.gateways.adyen.webhooks.handle_cancellation")
def test_handle_cancel_or_refund_action_cancel(
    mock_handle_cancellation, notification, adyen_plugin, payment_adyen_for_order
):
    payment = payment_adyen_for_order
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    config = adyen_plugin().config
    notification = notification(
        merchant_reference=payment_id,
        value=get_price_amount(payment.total, payment.currency),
    )
    notification["additionalData"]["modification.action"] = "cancel"

    handle_cancel_or_refund(notification, config)

    mock_handle_cancellation.assert_called_once_with(notification, config)


@pytest.fixture
def notification_with_hmac_signature():
    return {
        "additionalData": {
            "expiryDate": "12/2012",
            " NAME1 ": "VALUE1",
            "cardSummary": "7777",
            "totalFraudScore": "10",
            "hmacSignature": "D4bKVtjx5AlBL2eeQZIh1p7G1Lh6vWjzwkDlzC+PoMo=",
            "NAME2": "  VALUE2  ",
            "fraudCheck-6-ShopperIpUsage": "10",
        },
        "amount": {"currency": "GBP", "value": 20150},
        "eventCode": "AUTHORISATION",
        "eventDate": "2020-07-24T12:40:22+02:00",
        "merchantAccountCode": "SaleorPOS",
        "merchantReference": "8313842560770001",
        "paymentMethod": "visa",
        "pspReference": "test_AUTHORISATION_4",
        "reason": "REFUSED",
        "success": "false",
    }


def test_validate_hmac_signature(adyen_plugin, notification_with_hmac_signature):
    hmac_key = "8E60EDDCA27F96095AD5882EF0AA3B05844864710EC089B7967F796AC44AE76E"
    plugin = adyen_plugin()
    config = plugin.config
    config.connection_params["webhook_hmac"] = hmac_key
    assert validate_hmac_signature(notification_with_hmac_signature, config) is True


def test_validate_hmac_signature_missing_key_in_saleor(
    adyen_plugin, notification_with_hmac_signature
):
    plugin = adyen_plugin()
    config = plugin.config
    assert validate_hmac_signature(notification_with_hmac_signature, config) is False


def test_validate_hmac_signature_missing_key_in_notification(
    adyen_plugin, notification
):
    hmac_key = "8E60EDDCA27F96095AD5882EF0AA3B05844864710EC089B7967F796AC44AE76E"
    plugin = adyen_plugin()
    config = plugin.config
    config.connection_params["webhook_hmac"] = hmac_key
    assert validate_hmac_signature(notification(), config) is False


def test_validate_hmac_signature_without_keys(adyen_plugin, notification):
    plugin = adyen_plugin()
    config = plugin.config
    assert validate_hmac_signature(notification(), config) is True


def test_validate_auth_user(adyen_plugin):
    plugin = adyen_plugin()
    config = plugin.config
    config.connection_params["webhook_user"] = "admin@example.com"
    password = make_password("admin")
    config.connection_params["webhook_user_password"] = password
    is_valid = validate_auth_user(
        headers={"Authorization": "Basic YWRtaW5AZXhhbXBsZS5jb206YWRtaW4="},
        gateway_config=config,
    )
    assert is_valid is True


def validate_auth_user_when_header_is_missing(adyen_plugin):
    plugin = adyen_plugin()
    config = plugin.config
    config.connection_params["webhook_user"] = "admin@example.com"
    password = make_password("admin")
    config.connection_params["webhook_user_password"] = password
    is_valid = validate_auth_user(headers={}, gateway_config=config)
    assert is_valid is False


def test_validate_auth_user_when_user_is_missing(adyen_plugin):
    plugin = adyen_plugin()
    config = plugin.config
    is_valid = validate_auth_user(
        headers={"Authorization": "Basic YWRtaW5AZXhhbXBsZS5jb206YWRtaW4="},
        gateway_config=config,
    )
    assert is_valid is False


def test_validate_auth_user_when_auth_is_disabled(adyen_plugin):
    plugin = adyen_plugin()
    config = plugin.config
    is_valid = validate_auth_user(headers={}, gateway_config=config)
    assert is_valid is True


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_post(api_call_mock, payment_adyen_for_checkout):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        [{"payment_data": "test_data", "parameters": ["payload"]}]
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    transaction_count = payment_adyen_for_checkout.transactions.all().count()

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": checkout.pk}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url
    assert (
        payment_adyen_for_checkout.transactions.all().count() == transaction_count + 1
    )
    transaction = payment_adyen_for_checkout.transactions.last()
    assert transaction.kind == "auth"


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_get(api_call_mock, payment_adyen_for_checkout):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    transaction_count = payment_adyen_for_checkout.transactions.all().count()

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {
        "payment": payment_id,
        "checkout": checkout.pk,
        "payload": "test",
    }

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url
    assert (
        payment_adyen_for_checkout.transactions.all().count() == transaction_count + 1
    )
    transaction = payment_adyen_for_checkout.transactions.last()
    assert transaction.kind == "auth"


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_adyen_auto_capture(
    api_call_mock, payment_adyen_for_checkout
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    transaction_count = payment_adyen_for_checkout.transactions.all().count()

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": checkout.pk}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, True, False
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url
    assert (
        payment_adyen_for_checkout.transactions.all().count() == transaction_count + 1
    )
    transaction = payment_adyen_for_checkout.transactions.last()
    assert transaction.kind == "capture"


@mock.patch("saleor.payment.gateways.adyen.webhooks.capture")
@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_auto_capture(
    api_call_mock, capture_mock, payment_adyen_for_checkout
):
    # given
    payment_adyen_for_checkout.extra_data = json.dumps(
        {"payment_data": "test_data", "parameters": ["payload"]}
    )
    payment_adyen_for_checkout.save(update_fields=["extra_data"])

    payment_adyen_for_checkout.transactions.create(
        amount=payment_adyen_for_checkout.total,
        kind=TransactionKind.AUTH,
        gateway_response={},
        is_success=True,
    )

    transaction_count = payment_adyen_for_checkout.transactions.all().count()

    checkout = payment_adyen_for_checkout.checkout
    payment_id = graphene.Node.to_global_id("Payment", payment_adyen_for_checkout.pk)
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    request_mock = mock.Mock()
    request_mock.GET = {"payment": payment_id, "checkout": checkout.pk}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    capture_mock.return_value = Transaction.objects.create(
        payment=payment_adyen_for_checkout,
        action_required=False,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, True
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 302
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url
    assert (
        payment_adyen_for_checkout.transactions.all().count() == transaction_count + 2
    )


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
    request_mock.GET = {"payment": payment_id, "checkout": checkout.pk}
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
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

    # then
    assert response.status_code == 302
    assert f"resultCode={message['resultCode']}" in response.url
    assert f"method={message['action']['method']}" in response.url
    assert f"paymentData={message['action']['paymentData']}" in response.url
    assert f"paymentMethodType={message['action']['paymentMethodType']}" in response.url
    assert f"type={message['action']['type']}" in response.url
    assert f"checkout={quote_plus(checkout_id)}" in response.url
    assert f"payment={quote_plus(payment_id)}" in response.url


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
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

    # then
    assert response.status_code == 404
    assert (
        response.content.decode() == "Cannot perform payment. Payment does not exists."
    )


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
        "checkout": payment_adyen_for_checkout.checkout.pk,
    }
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    payment_details_mock.return_value.message = {
        "resultCode": "Test",
    }

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

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
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

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
    request_mock.GET = {"payment": payment_id, "checkout": "123"}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

    # then
    assert response.status_code == 400
    assert (
        response.content.decode()
        == "The given checkout is not related to the specified payment"
    )


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
    request_mock.GET = {"payment": payment_id, "checkout": "123"}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

    # then
    assert response.status_code == 400
    assert (
        response.content.decode()
        == "The given payment does not have the corresponding checkout."
    )


@mock.patch("saleor.payment.gateways.adyen.webhooks.api_call")
def test_handle_additional_actions_api_call_error(
    api_call_mock, payment_adyen_for_checkout,
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
        "checkout": payment_adyen_for_checkout.checkout.pk,
    }
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    payment_details_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

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
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

    # then
    assert response.status_code == 400
    assert response.content.decode() == "Payment is not active."


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
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

    # then
    assert response.status_code == 400
    assert response.content.decode() == "Cannot perform not adyen payment."


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
    request_mock.GET = {"payment": payment_id, "checkout": checkout.pk}
    request_mock.POST = {"payload": "test"}

    payment_details_mock = mock.Mock()
    message = {
        "resultCode": "Test",
    }
    api_call_mock.return_value.message = message

    # when
    response = handle_additional_actions(
        request_mock, payment_details_mock, False, False
    )

    # then
    payment_adyen_for_checkout.refresh_from_db()
    assert response.status_code == 400
    assert (
        response.content.decode()
        == "Cannot perform payment. Lack of required parameters in request."
    )


def test_prepare_api_request_data_get():
    # given
    data = {
        "parameters": ["payload", "second_param"],
        "payment_data": "test data",
    }

    request_mock = mock.Mock()
    request_mock.GET = {
        "payload": "payload data",
        "second_param": "second param data",
    }
    request_mock.POST = {}

    # when
    request_data = prepare_api_request_data(request_mock, data)

    # then
    assert request_data == {
        "paymentData": data["payment_data"],
        "details": {"payload": "payload data", "second_param": "second param data"},
    }


def test_prepare_api_request_data_post():
    # given
    data = {
        "parameters": ["payload", "second_param"],
        "payment_data": "test data",
    }

    request_mock = mock.Mock()
    request_mock.GET = {}
    request_mock.POST = {
        "payload": "payload data",
        "second_param": "second param data",
    }

    # when
    request_data = prepare_api_request_data(request_mock, data)

    # then
    assert request_data == {
        "paymentData": data["payment_data"],
        "details": {"payload": "payload data", "second_param": "second param data"},
    }


def test_prepare_api_request_data_lack_of_info_in_data():
    # given
    data = {
        "parameters": ["payload", "second_param"],
    }

    request_mock = mock.Mock()
    request_mock.GET = {}
    request_mock.POST = {
        "payload": "payload data",
        "second_param": "second param data",
    }

    # when
    with pytest.raises(KeyError) as e:
        prepare_api_request_data(request_mock, data)

    # then
    assert (
        e._excinfo[1].args[0]
        == "Cannot perform payment. Lack of payment data and parameters information."
    )


def test_prepare_api_request_data_lack_of_required_parameters_in_request():
    # given
    data = {
        "parameters": ["payload", "second_param"],
        "payment_data": "test data",
    }

    request_mock = mock.Mock()
    request_mock.GET = {}
    request_mock.POST = {
        "payload": "payload data",
    }

    # when
    with pytest.raises(KeyError) as e:
        prepare_api_request_data(request_mock, data)

    # then
    assert (
        e._excinfo[1].args[0]
        == "Cannot perform payment. Lack of required parameters in request."
    )
