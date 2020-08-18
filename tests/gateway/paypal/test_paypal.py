import os
from decimal import Decimal
from math import isclose

import pytest

from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.gateways.paypal import capture, get_paypal_order_id, refund
from saleor.payment.interface import GatewayConfig
from saleor.payment.utils import create_payment_information

TRANSACTION_AMOUNT = Decimal(42.42)
TRANSACTION_REFUND_AMOUNT = Decimal(24.24)
TRANSACTION_CURRENCY = "EUR"


# Set to True if recording new cassette with sandbox using credentials in env
RECORD = False

"""
Instructions to recreate Paypal tests:
- Set your Paypal sandbox credentials in the env:
    `export PAYPAL_SANDBOX_PUBLIC_KEY=foo-public-key-LD0pMfrNBM-erCm8sCahoY1kfXxL6C2M9J1TblHPsV5jdP_E1eojLn0gFxui`
    `export PAYPAL_SANDBOX_SECRET_KEY=foo-secret-key--ZNJYmrc5fpTJWbGJjrG6P1DAZ2L5EtlEqIRc8LD6PyrOvjAGZpRQqs0CM3o`
- Set RECORD = True
- Remove all cassettes (./cassettes directory)
- Run `poetry run pytest --vcr-record-mode=once tests/gateway/paypal/test_paypal.py::test_create_paypal_order`
- copy ORDER_ID from ./cassettes/test_get_client_token.yaml response > body > string > id
- In test_capture_success, set paypal_order_id to ORDER_ID (ex: paypal_order_id = "2N779501TA0611714")
- Open in browser https://www.sandbox.paypal.com/checkoutnow?token=<ORDER_ID>) and
    approve payment manually with your sandbox buyer account
- Run `poetry run pytest --vcr-record-mode=once tests/gateway/paypal/test_paypal.py::test_capture_success`
- copy PAYMENT_ID from ./cassettes/test_capture_success.yaml response > body > payments > captures > id
- paste PAYMENT_ID in test_refund_success paypal_capture_id (ex: paypal_capture_id = "3VF366050L3453640")
- run `poetry run pytest --vcr-record-mode=once tests/gateway/paypal/test_paypal.py::test_refund_success`
- run again all tests: `poetry run pytest --vcr-record-mode=once tests/gateway/paypal/test_paypal.py`

IMPORTANT: once you finished:
- Set RECORD = False
"""


@pytest.fixture()
def gateway_config():
    return GatewayConfig(
        gateway_name="paypal",
        auto_capture=True,
        connection_params={
            "client_id": "public",
            "private_key": "secret",
            "sandbox_mode": True,
        },
    )


@pytest.fixture()
def sandbox_gateway_config(gateway_config):
    if RECORD:
        connection_params = {
            "client_id": os.environ.get("PAYPAL_SANDBOX_PUBLIC_KEY"),
            "private_key": os.environ.get("PAYPAL_SANDBOX_SECRET_KEY"),
        }
        gateway_config.connection_params.update(connection_params)
    return gateway_config


@pytest.fixture()
def paypal_payment(payment_dummy):
    payment_dummy.total = TRANSACTION_AMOUNT
    payment_dummy.currency = TRANSACTION_CURRENCY
    return payment_dummy


if RECORD:

    @pytest.mark.integration
    @pytest.mark.vcr
    def test_create_paypal_order(sandbox_gateway_config):
        """create order and record Paypal order id to be used as token in following
        tests"""
        assert get_paypal_order_id(
            sandbox_gateway_config, float(TRANSACTION_AMOUNT), TRANSACTION_CURRENCY
        )


@pytest.mark.integration
@pytest.mark.vcr
def test_capture_success(sandbox_gateway_config, paypal_payment):

    # copy from ./cassettes/test_get_client_token.yaml response > body > string > id
    paypal_order_id = "8UT45527HV521594P"

    payment_info = create_payment_information(paypal_payment, paypal_order_id)
    response = capture(payment_info, sandbox_gateway_config)
    assert not response.error
    assert response.kind == TransactionKind.CAPTURE
    assert isclose(response.amount, TRANSACTION_AMOUNT)
    assert response.currency == TRANSACTION_CURRENCY
    assert response.is_success is True
    assert not response.action_required


@pytest.mark.integration
@pytest.mark.vcr
def test_capture_error(sandbox_gateway_config, paypal_payment):
    invalid_paypal_order_id = "INVALID-PAYPAL-ORDER-ID"
    payment_info = create_payment_information(paypal_payment, invalid_paypal_order_id)
    response = capture(payment_info, sandbox_gateway_config)
    assert response.error is not None
    assert response.transaction_id == invalid_paypal_order_id
    assert response.kind == TransactionKind.CAPTURE
    assert not response.is_success
    assert isclose(response.amount, TRANSACTION_AMOUNT)
    assert response.currency == TRANSACTION_CURRENCY
    assert not response.action_required


@pytest.fixture()
def paypal_paid_payment(paypal_payment):
    paypal_payment.charge_status = ChargeStatus.FULLY_CHARGED
    paypal_payment.save(update_fields=["charge_status"])
    return paypal_payment


@pytest.mark.integration
@pytest.mark.vcr
def test_refund_success(paypal_paid_payment, sandbox_gateway_config):

    # Copy from cassettes/test_capture in response > body > payments > captures > id
    paypal_capture_id = "5DH34141WG814093W"

    payment_info = create_payment_information(
        paypal_paid_payment,
        amount=TRANSACTION_REFUND_AMOUNT,
        payment_token=paypal_capture_id,
    )
    response = refund(payment_info, sandbox_gateway_config)

    assert not response.error
    assert response.kind == TransactionKind.REFUND
    assert response.is_success
    assert isclose(response.amount, TRANSACTION_REFUND_AMOUNT)
    assert response.currency == TRANSACTION_CURRENCY


@pytest.mark.integration
@pytest.mark.vcr
def test_refund_error(paypal_paid_payment, sandbox_gateway_config):
    invalid_paypal_capture_id = "NON-EXISTENT-CAPTURE-ID"
    payment_info = create_payment_information(
        paypal_paid_payment,
        amount=TRANSACTION_REFUND_AMOUNT,
        payment_token=invalid_paypal_capture_id,
    )
    response = refund(payment_info, sandbox_gateway_config)

    assert response.error is not None
    assert response.transaction_id == invalid_paypal_capture_id
    assert response.kind == TransactionKind.REFUND
    assert not response.is_success
    assert isclose(response.amount, TRANSACTION_REFUND_AMOUNT)
    assert response.currency == TRANSACTION_CURRENCY
