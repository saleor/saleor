from decimal import Decimal
from unittest.mock import Mock, patch

import pytest
from braintree import Environment, ErrorResult, SuccessfulResult, Transaction
from braintree.errors import Errors
from braintree.validation_error import ValidationError
from django.core.exceptions import ImproperlyConfigured

from ....interface import CustomerSource, GatewayConfig, PaymentMethodInfo, TokenConfig
from ....utils import create_payment_information
from .. import (
    TransactionKind,
    authorize,
    capture,
    extract_gateway_response,
    get_braintree_gateway,
    get_client_token,
    get_customer_data,
    get_error_for_client,
    list_client_sources,
    refund,
    void,
)
from ..errors import DEFAULT_ERROR_MESSAGE, BraintreeException

DEFAULT_ERROR = "Unable to process transaction. Please try again in a moment"


@pytest.fixture
def braintree_success_response():
    return Mock(
        spec=SuccessfulResult,
        is_success=True,
        transaction=Mock(
            id="1x02131",
            spec=Transaction,
            amount=Decimal("80.00"),
            created_at="2018-10-20 18:34:22",
            credit_card="",  # FIXME we should provide a proper CreditCard mock
            customer_details=Mock(id=None),
            additional_processor_response="",
            gateway_rejection_reason="",
            processor_response_code="1000",
            processor_response_text="Approved",
            processor_settlement_response_code="",
            processor_settlement_response_text="",
            risk_data="",
            currency_iso_code="EUR",
            status="authorized",
        ),
    )


@pytest.fixture
def braintree_error():
    return Mock(
        spec=ValidationError,
        code="91507",
        attribute="base",
        message="Cannot submit for settlement unless status is authorized.",
    )


@pytest.fixture
def braintree_error_response(braintree_error):
    return Mock(
        spec=ErrorResult,
        is_success=False,
        transaction=None,
        errors=Mock(spec=Errors, deep_errors=[braintree_error]),
    )


@pytest.fixture
def gateway_config():
    return GatewayConfig(
        gateway_name="braintree",
        auto_capture=False,
        store_customer=False,
        connection_params={
            "sandbox_mode": False,
            "merchant_id": "123",
            "public_key": "456",
            "private_key": "789",
        },
        supported_currencies="USD",
    )


def test_get_customer_data(payment_dummy):
    payment = payment_dummy
    payment_info = create_payment_information(payment)
    result = get_customer_data(payment_info)
    expected_result = {
        "order_id": payment.order_id,
        "billing": {
            "first_name": payment.billing_first_name,
            "last_name": payment.billing_last_name,
            "company": payment.billing_company_name,
            "postal_code": payment.billing_postal_code,
            "street_address": payment.billing_address_1[:255],
            "extended_address": payment.billing_address_2[:255],
            "locality": payment.billing_city,
            "region": payment.billing_country_area,
            "country_code_alpha2": payment.billing_country_code,
        },
        "risk_data": {"customer_ip": payment.customer_ip_address or ""},
        "customer": {"email": payment.billing_email},
    }
    assert result == expected_result


def test_get_error_for_client(braintree_error, monkeypatch):
    # no error
    assert get_error_for_client([]) == ""

    error = {"code": braintree_error.code, "message": braintree_error.message}

    # error not whitelisted
    monkeypatch.setattr("saleor.payment.gateways.braintree.ERROR_CODES_WHITELIST", {})
    assert get_error_for_client([error]) == DEFAULT_ERROR

    monkeypatch.setattr(
        "saleor.payment.gateways.braintree.ERROR_CODES_WHITELIST",
        {braintree_error.code: ""},
    )
    assert get_error_for_client([error]) == braintree_error.message

    monkeypatch.setattr(
        "saleor.payment.gateways.braintree.ERROR_CODES_WHITELIST",
        {braintree_error.code: "Error msg override"},
    )
    assert get_error_for_client([error]) == "Error msg override"


def test_extract_gateway_response(braintree_success_response):
    result = extract_gateway_response(braintree_success_response)
    t = braintree_success_response.transaction
    expected_result = {
        "currency": t.currency_iso_code,
        "amount": t.amount,
        "credit_card": t.credit_card,
        "errors": [],
        "transaction_id": t.id,
        "customer_id": None,
    }
    assert result == expected_result


def test_extract_gateway_response_no_transaction(
    braintree_error_response, braintree_error
):
    result = extract_gateway_response(braintree_error_response)
    assert result == {
        "errors": [{"code": braintree_error.code, "message": braintree_error.message}]
    }


def test_get_braintree_gateway(gateway_config):
    connection_params = gateway_config.connection_params
    result = get_braintree_gateway(**gateway_config.connection_params)
    assert connection_params["sandbox_mode"] is False
    assert result.config.environment == Environment.Production
    assert result.config.merchant_id == connection_params["merchant_id"]
    assert result.config.public_key == connection_params["public_key"]
    assert result.config.private_key == connection_params["private_key"]


@pytest.mark.integration
def test_get_braintree_gateway_sandbox(gateway_config):
    gateway_config.connection_params["sandbox_mode"] = True
    result = get_braintree_gateway(**gateway_config.connection_params)
    assert result.config.environment == Environment.Sandbox


def test_get_braintree_gateway_inproperly_configured(gateway_config):
    with pytest.raises(ImproperlyConfigured):
        gateway_config.connection_params["private_key"] = None
        get_braintree_gateway(**gateway_config.connection_params)


@patch("saleor.payment.gateways.braintree.get_braintree_gateway")
def test_get_client_token(mock_gateway, gateway_config):
    expected_token = "client-token"
    mock_generate = Mock(return_value=expected_token)
    mock_gateway.return_value = Mock(client_token=Mock(generate=mock_generate))
    token = get_client_token(gateway_config)
    mock_gateway.assert_called_once_with(**gateway_config.connection_params)
    mock_generate.assert_called_once_with()
    assert token == expected_token


@pytest.fixture
def gateway_config_with_store_enabled(gateway_config):
    gateway_config.store_customer = True
    return gateway_config


@patch("saleor.payment.gateways.braintree.get_braintree_gateway")
def test_get_client_token_with_customer_id(
    mock_gateway, gateway_config_with_store_enabled
):
    expected_token = "client-token"
    mock_generate = Mock(return_value=expected_token)
    mock_gateway.return_value = Mock(client_token=Mock(generate=mock_generate))
    token = get_client_token(
        gateway_config_with_store_enabled, TokenConfig(customer_id="1234")
    )
    mock_gateway.assert_called_once_with(
        **gateway_config_with_store_enabled.connection_params
    )
    mock_generate.assert_called_once_with({"customer_id": "1234"})
    assert token == expected_token


@patch("saleor.payment.gateways.braintree.get_braintree_gateway")
def test_get_client_token_with_no_customer_id_when_disabled(
    mock_gateway, gateway_config
):
    expected_token = "client-token"
    mock_generate = Mock(return_value=expected_token)
    mock_gateway.return_value = Mock(client_token=Mock(generate=mock_generate))
    token = get_client_token(gateway_config, TokenConfig(customer_id="1234"))
    mock_gateway.assert_called_once_with(**gateway_config.connection_params)
    mock_generate.assert_called_once_with({})
    assert token == expected_token


@pytest.mark.integration
@patch("saleor.payment.gateways.braintree.get_braintree_gateway")
def test_authorize_error_response(
    mock_gateway, payment_dummy, braintree_error_response, gateway_config
):
    payment = payment_dummy
    payment_token = "payment-token"
    mock_response = Mock(return_value=braintree_error_response)
    mock_gateway.return_value = Mock(transaction=Mock(sale=mock_response))

    payment_info = create_payment_information(payment, payment_token)
    response = authorize(payment_info, gateway_config)

    assert response.raw_response == extract_gateway_response(braintree_error_response)
    assert not response.is_success
    assert response.error == DEFAULT_ERROR


@pytest.fixture
def sandbox_braintree_gateway_config(gateway_config):
    """Set up your environment variables to record sandbox."""
    gateway_config.connection_params = {
        "merchant_id": "9m6qhfxsqzm3cgzw",  # CHANGE WHEN RECORDING, DO NOT COMMIT
        "public_key": "fake_public_key",  # CHANGE WHEN RECORDING
        "private_key": "fake_private_key",  # CHANGE WHEN RECORDING
        "sandbox_mode": True,
    }
    gateway_config.auto_capture = True
    return gateway_config


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_authorize_one_time(
    payment_dummy, sandbox_braintree_gateway_config, braintree_success_response
):
    payment = payment_dummy

    payment_info = create_payment_information(payment, "fake-valid-nonce")
    sandbox_braintree_gateway_config.auto_capture = False

    response = authorize(payment_info, sandbox_braintree_gateway_config)
    assert not response.error
    assert response.kind == TransactionKind.AUTH
    assert response.amount == braintree_success_response.transaction.amount
    assert response.currency == braintree_success_response.transaction.currency_iso_code
    assert response.is_success is True
    assert response.payment_method_info.last_4 == "1881"
    assert response.payment_method_info.brand == "visa"
    assert response.payment_method_info.type == "card"
    assert response.payment_method_info.exp_month == "12"
    assert response.payment_method_info.exp_year == "2020"


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_authorize_and_save_customer_id(
    payment_dummy, sandbox_braintree_gateway_config
):
    CUSTOMER_ID = "595109854"  # retrieved from sandbox
    payment = payment_dummy

    payment_info = create_payment_information(payment, "fake-valid-nonce")
    payment_info.amount = 100.00
    payment_info.reuse_source = True

    sandbox_braintree_gateway_config.store_customer = True
    response = authorize(payment_info, sandbox_braintree_gateway_config)
    assert not response.error
    assert response.customer_id == CUSTOMER_ID


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_authorize_with_customer_id(payment_dummy, sandbox_braintree_gateway_config):
    CUSTOMER_ID = "810066863"  # retrieved from sandbox
    payment = payment_dummy

    payment_info = create_payment_information(payment, None)
    payment_info.amount = 100.00
    payment_info.customer_id = CUSTOMER_ID

    response = authorize(payment_info, sandbox_braintree_gateway_config)
    assert not response.error
    assert response.customer_id == CUSTOMER_ID
    assert response.is_success


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_refund(payment_txn_captured, sandbox_braintree_gateway_config):
    amount = Decimal("10.00")
    TRANSACTION_ID = "rjfqmf3r"
    payment_info = create_payment_information(
        payment_txn_captured, TRANSACTION_ID, amount
    )
    response = refund(payment_info, sandbox_braintree_gateway_config)
    assert not response.error

    assert response.kind == TransactionKind.REFUND
    assert response.amount == amount
    assert response.currency == "EUR"
    assert response.is_success is True


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_refund_incorrect_token(payment_txn_captured, sandbox_braintree_gateway_config):
    payment = payment_txn_captured
    amount = Decimal("10.00")

    payment_info = create_payment_information(payment, "token", amount)
    with pytest.raises(BraintreeException) as e:
        refund(payment_info, sandbox_braintree_gateway_config)
    assert str(e.value) == DEFAULT_ERROR_MESSAGE


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_capture(payment_txn_preauth, sandbox_braintree_gateway_config):
    payment = payment_txn_preauth
    amount = Decimal("80.00")

    payment_info = create_payment_information(payment, "m30bcfym", amount)
    response = capture(payment_info, sandbox_braintree_gateway_config)
    assert not response.error

    assert response.kind == TransactionKind.CAPTURE
    assert response.amount == amount
    assert response.currency == "EUR"
    assert response.is_success is True


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_capture_incorrect_token(payment_txn_preauth, sandbox_braintree_gateway_config):
    payment_info = create_payment_information(payment_txn_preauth, "12345")
    with pytest.raises(BraintreeException) as e:
        response = capture(payment_info, sandbox_braintree_gateway_config)
        assert str(e.value) == DEFAULT_ERROR_MESSAGE
        assert response.raw_response == extract_gateway_response(
            braintree_error_response
        )
        assert not response.is_success
        assert response.error == DEFAULT_ERROR


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_void(payment_txn_preauth, sandbox_braintree_gateway_config):
    payment = payment_txn_preauth
    payment_info = create_payment_information(payment, "narvpy2m")
    response = void(payment_info, sandbox_braintree_gateway_config)
    assert not response.error

    assert response.kind == TransactionKind.VOID
    assert response.is_success is True


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_void_incorrect_token(payment_txn_preauth, sandbox_braintree_gateway_config):
    payment = payment_txn_preauth

    payment_info = create_payment_information(payment, "incorrect_token")
    with pytest.raises(BraintreeException) as e:
        void(payment_info, sandbox_braintree_gateway_config)
    assert str(e.value) == DEFAULT_ERROR_MESSAGE


@pytest.mark.integration
@pytest.mark.vcr(filter_headers=["authorization"])
def test_list_customer_sources(sandbox_braintree_gateway_config):
    CUSTOMER_ID = "595109854"  # retrieved from sandbox
    expected_credit_card = PaymentMethodInfo(
        last_4="1881", exp_year=2020, exp_month=12, name=None
    )
    expected_customer_source = CustomerSource(
        id="d0b52c80b648ae8e5a14eddcaf24d254",
        gateway="braintree",
        credit_card_info=expected_credit_card,
    )
    sources = list_client_sources(sandbox_braintree_gateway_config, CUSTOMER_ID)
    assert sources == [expected_customer_source]
