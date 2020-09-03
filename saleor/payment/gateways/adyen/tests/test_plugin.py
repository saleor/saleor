import json
from decimal import Decimal
from unittest import mock

import pytest

from .... import PaymentError, TransactionKind
from ....interface import GatewayResponse, PaymentMethodInfo
from ....models import Payment
from ....utils import create_payment_information, create_transaction


@pytest.mark.vcr
def test_get_payment_gateway_for_checkout(
    adyen_plugin, checkout_with_single_item, address
):
    checkout_with_single_item.billing_address = address
    checkout_with_single_item.save()
    adyen_plugin = adyen_plugin()
    response = adyen_plugin.get_payment_gateway_for_checkout(
        checkout_with_single_item, None
    )
    assert response.id == adyen_plugin.PLUGIN_ID
    assert response.name == adyen_plugin.PLUGIN_NAME
    config = response.config
    assert len(config) == 2
    assert config[0] == {
        "field": "client_key",
        "value": adyen_plugin.config.connection_params["client_key"],
    }
    assert config[1]["field"] == "config"
    config = json.loads(config[1]["value"])
    assert isinstance(config, dict)


@pytest.mark.vcr
def test_process_payment(payment_adyen_for_checkout, checkout_with_items, adyen_plugin):
    payment_info = create_payment_information(
        payment_adyen_for_checkout,
        additional_data={"paymentMethod": {"paymentdata": "", "type": "test"}},
    )
    adyen_plugin = adyen_plugin()
    response = adyen_plugin.process_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.AUTH
    assert response.amount == Decimal("80.00")
    assert response.currency == checkout_with_items.currency
    assert response.transaction_id == "882595494831959A"  # ID returned by Adyen
    assert response.error is None
    assert response.action_required_data is None
    assert response.payment_method_info == PaymentMethodInfo(brand="visa", type="test")


@pytest.mark.vcr
def test_process_payment_with_adyen_auto_capture(
    payment_adyen_for_checkout, checkout_with_items, adyen_plugin
):
    payment_info = create_payment_information(
        payment_adyen_for_checkout,
        additional_data={"paymentMethod": {"paymentdata": ""}},
    )
    adyen_plugin = adyen_plugin(adyen_auto_capture=True)
    response = adyen_plugin.process_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.CAPTURE
    assert response.amount == Decimal("80.00")
    assert response.currency == checkout_with_items.currency
    assert response.transaction_id == "882595494831959A"  # ID returned by Adyen
    assert response.error is None


@pytest.mark.vcr
def test_process_payment_with_auto_capture(
    payment_adyen_for_checkout, checkout_with_items, adyen_plugin
):
    payment_info = create_payment_information(
        payment_adyen_for_checkout,
        additional_data={"paymentMethod": {"paymentdata": ""}},
    )
    adyen_plugin = adyen_plugin(auto_capture=True)
    response = adyen_plugin.process_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.CAPTURE
    assert response.amount == Decimal("80.00")
    assert response.currency == checkout_with_items.currency
    assert response.transaction_id == "853596624248395G"  # ID returned by Adyen
    assert response.error is None
    assert response.action_required_data is None


@pytest.mark.vcr
@mock.patch("saleor.payment.gateways.adyen.plugin.api_call")
def test_process_payment_additional_action(
    api_call_mock, payment_adyen_for_checkout, checkout_with_items, adyen_plugin
):
    payment_adyen_for_checkout.extra_data = ""
    payment_adyen_for_checkout.save(update_fields=["extra_data"])
    payment_data = "Ab02b4c0!B"
    action_data = {
        "method": "GET",
        "paymentData": payment_data,
        "paymentMethodType": "ideal",
        "type": "redirect",
        "url": "https://test.adyen.com/hpp/redirectIdeal.shtml?brandCode=ideal",
    }
    message = {
        "resultCode": "RedirectShopper",
        "action": action_data,
        "details": [{"key": "payload", "type": "text"}],
        "pspReference": "882595494831959A",
    }
    api_call_mock.return_value.message = message

    payment_info = create_payment_information(
        payment_adyen_for_checkout,
        additional_data={"paymentMethod": {"paymentdata": ""}},
    )
    adyen_plugin = adyen_plugin(auto_capture=True)
    response = adyen_plugin.process_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is True
    assert response.kind == TransactionKind.AUTH
    assert response.amount == Decimal("80.00")
    assert response.currency == checkout_with_items.currency
    assert response.transaction_id == "882595494831959A"
    assert response.error is None
    assert response.action_required_data == action_data

    payment_adyen_for_checkout.refresh_from_db()
    assert payment_adyen_for_checkout.extra_data == json.dumps(
        [{"payment_data": payment_data, "parameters": ["payload"]}]
    )


@pytest.mark.vcr
@mock.patch("saleor.payment.gateways.adyen.plugin.api_call")
def test_process_payment_additional_action_payment_does_not_exists(
    api_call_mock, payment_adyen_for_checkout, checkout_with_items, adyen_plugin
):
    action_data = {
        "method": "GET",
        "paymentData": "Ab02b4c0!B",
        "paymentMethodType": "ideal",
        "type": "redirect",
        "url": "https://test.adyen.com/hpp/redirectIdeal.shtml?brandCode=ideal",
    }
    message = {
        "resultCode": "RedirectShopper",
        "action": action_data,
        "details": [{"key": "payload", "type": "text"}],
        "pspReference": "882595494831959A",
    }
    api_call_mock.return_value.message = message

    payment_info = create_payment_information(
        payment_adyen_for_checkout,
        additional_data={"paymentMethod": {"paymentdata": ""}},
    )

    Payment.objects.all().delete()

    adyen_plugin = adyen_plugin(auto_capture=True)

    with pytest.raises(PaymentError) as e:
        adyen_plugin.process_payment(payment_info, None)

    assert str(e.value) == "Payment cannot be performed. Payment does not exists."


@pytest.mark.vcr
@mock.patch("saleor.payment.gateways.adyen.plugin.api_call")
def test_process_payment_additional_action_checkout_does_not_exists(
    api_call_mock, payment_adyen_for_checkout, checkout_with_items, adyen_plugin
):
    action_data = {
        "method": "GET",
        "paymentData": "Ab02b4c0!B",
        "paymentMethodType": "ideal",
        "type": "redirect",
        "url": "https://test.adyen.com/hpp/redirectIdeal.shtml?brandCode=ideal",
    }
    message = {
        "resultCode": "RedirectShopper",
        "action": action_data,
        "details": [{"key": "payload", "type": "text"}],
        "pspReference": "882595494831959A",
    }
    api_call_mock.return_value.message = message

    payment_info = create_payment_information(
        payment_adyen_for_checkout,
        additional_data={"paymentMethod": {"paymentdata": ""}},
    )

    payment_adyen_for_checkout.checkout = None
    payment_adyen_for_checkout.save()

    adyen_plugin = adyen_plugin(auto_capture=True)

    with pytest.raises(PaymentError) as e:
        adyen_plugin.process_payment(payment_info, None)

    assert (
        str(e.value)
        == "Payment cannot be performed. Checkout for this payment does not exist."
    )


def test_confirm_payment(payment_adyen_for_order, adyen_plugin):
    payment_info = create_payment_information(payment_adyen_for_order,)
    gateway_response = GatewayResponse(
        kind=TransactionKind.ACTION_TO_CONFIRM,
        action_required=False,
        transaction_id="882595494831959A",
        is_success=True,
        amount=payment_info.amount,
        currency=payment_info.currency,
        error="",
        raw_response={},
    )

    action_transaction = create_transaction(
        payment=payment_adyen_for_order,
        payment_information=payment_info,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        gateway_response=gateway_response,
    )
    adyen_plugin = adyen_plugin()
    response = adyen_plugin.confirm_payment(payment_info, None)

    assert response is not None
    assert response.is_success is True
    assert response.kind == TransactionKind.AUTH
    assert response.amount == action_transaction.amount
    assert response.currency == action_transaction.currency


def test_confirm_payment_pending_order(payment_adyen_for_checkout, adyen_plugin):
    payment_info = create_payment_information(payment_adyen_for_checkout,)
    gateway_response = GatewayResponse(
        kind=TransactionKind.ACTION_TO_CONFIRM,
        action_required=False,
        transaction_id="882595494831959A",
        is_success=True,
        amount=payment_info.amount,
        currency=payment_info.currency,
        error="",
        raw_response={"pspReference": "882595494831959A", "resultCode": "Pending"},
    )
    action_transaction = create_transaction(
        payment=payment_adyen_for_checkout,
        payment_information=payment_info,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        gateway_response=gateway_response,
    )
    adyen_plugin = adyen_plugin()
    response = adyen_plugin.confirm_payment(payment_info, None)

    assert response is not None
    assert response.is_success is True
    assert response.kind == TransactionKind.PENDING
    assert response.amount == action_transaction.amount
    assert response.currency == action_transaction.currency


def test_confirm_already_processed_payment(payment_adyen_for_order, adyen_plugin):
    payment_info = create_payment_information(payment_adyen_for_order,)
    gateway_response = GatewayResponse(
        kind=TransactionKind.ACTION_TO_CONFIRM,
        action_required=False,
        transaction_id="882595494831959A",
        is_success=True,
        amount=payment_info.amount,
        currency=payment_info.currency,
        error="",
        raw_response={},
    )
    create_transaction(
        payment=payment_adyen_for_order,
        payment_information=payment_info,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        gateway_response=gateway_response,
    )
    gateway_response.kind = TransactionKind.AUTH
    action_transaction = create_transaction(
        payment=payment_adyen_for_order,
        payment_information=payment_info,
        kind=TransactionKind.AUTH,
        gateway_response=gateway_response,
    )
    adyen_plugin = adyen_plugin()
    response = adyen_plugin.confirm_payment(payment_info, None)

    assert response is not None
    assert response.transaction_already_processed is True
    assert response.is_success is True
    assert response.kind == TransactionKind.AUTH
    assert response.amount == action_transaction.amount
    assert response.currency == action_transaction.currency
    assert payment_adyen_for_order.transactions.count() == 3


def test_confirm_payment_with_adyen_auto_capture(payment_adyen_for_order, adyen_plugin):
    payment_info = create_payment_information(payment_adyen_for_order,)
    gateway_response = GatewayResponse(
        kind=TransactionKind.ACTION_TO_CONFIRM,
        action_required=False,
        transaction_id="882595494831959A",
        is_success=True,
        amount=payment_info.amount,
        currency=payment_info.currency,
        error="",
        raw_response={},
    )

    auth_transaction = create_transaction(
        payment=payment_adyen_for_order,
        payment_information=payment_info,
        kind=TransactionKind.ACTION_TO_CONFIRM,
        gateway_response=gateway_response,
    )
    adyen_plugin = adyen_plugin(adyen_auto_capture=True)
    response = adyen_plugin.confirm_payment(payment_info, None)

    assert response is not None
    assert response.is_success is True
    assert response.kind == TransactionKind.CAPTURE
    assert response.amount == auth_transaction.amount
    assert response.currency == auth_transaction.currency


@pytest.mark.vcr
@pytest.mark.skip(reason="To finish when additional auth data schema will be known")
def test_confirm_payment_with_additional_details(payment_adyen_for_order, adyen_plugin):
    return  # test it when we will have additional auth data
    payment_info = create_payment_information(payment_adyen_for_order,)
    adyen_plugin = adyen_plugin()
    adyen_plugin.confirm_payment(payment_info, None)


@pytest.mark.vcr
def test_refund_payment(payment_adyen_for_order, order_with_lines, adyen_plugin):
    payment_info = create_payment_information(
        payment_adyen_for_order,
        # additional_data=...
    )
    gateway_response = GatewayResponse(
        kind=TransactionKind.AUTH,
        action_required=False,
        transaction_id="882595494831959A",
        is_success=True,
        amount=payment_info.amount,
        currency=payment_info.currency,
        error="",
        raw_response={},
    )

    create_transaction(
        payment=payment_adyen_for_order,
        payment_information=payment_info,
        kind=TransactionKind.AUTH,
        gateway_response=gateway_response,
    )
    response = adyen_plugin().refund_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.REFUND_ONGOING
    assert response.amount == Decimal("80.00")
    assert response.currency == order_with_lines.currency
    assert response.transaction_id == "882595499620961A"  # ID returned by Adyen


@pytest.mark.vcr
def test_void_payment(payment_adyen_for_order, order_with_lines, adyen_plugin):
    payment_info = create_payment_information(payment_adyen_for_order,)
    gateway_response = GatewayResponse(
        kind=TransactionKind.AUTH,
        action_required=False,
        transaction_id="883597146907178J",
        is_success=True,
        amount=payment_info.amount,
        currency=payment_info.currency,
        error="",
        raw_response={},
    )
    create_transaction(
        payment=payment_adyen_for_order,
        payment_information=payment_info,
        kind=TransactionKind.AUTH,
        gateway_response=gateway_response,
    )

    response = adyen_plugin().void_payment(payment_info, None)

    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.VOID
    assert response.amount == Decimal("80.00")
    assert response.currency == order_with_lines.currency
    assert response.transaction_id == "853597151490739D"  # ID returned by Adyen


@pytest.mark.vcr
def test_capture_payment(payment_adyen_for_order, order_with_lines, adyen_plugin):
    payment_info = create_payment_information(
        payment_adyen_for_order,
        payment_token="882595494831959A",
        additional_data={"paymentMethod": {"paymentdata": "", "type": "test"}},
    )
    gateway_response = GatewayResponse(
        kind=TransactionKind.AUTH,
        action_required=False,
        transaction_id="882595494831959A",
        is_success=True,
        amount=payment_info.amount,
        currency=payment_info.currency,
        error="",
        raw_response={},
    )

    create_transaction(
        payment=payment_adyen_for_order,
        payment_information=payment_info,
        kind=TransactionKind.AUTH,
        gateway_response=gateway_response,
    )
    response = adyen_plugin().capture_payment(payment_info, None)
    assert response.is_success is True
    assert response.action_required is False
    assert response.kind == TransactionKind.CAPTURE
    assert response.amount == Decimal("80.00")
    assert response.currency == order_with_lines.currency
    assert response.transaction_id == "852595499936560C"  # ID returned by Adyen
    assert response.payment_method_info == PaymentMethodInfo(brand="visa", type="test")
