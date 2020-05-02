import os
from decimal import Decimal
from math import isclose

import pytest

from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.gateways.paypal import authorize, get_paypal_order_id, refund
from saleor.payment.interface import GatewayConfig
from saleor.payment.utils import create_payment_information

TRANSACTION_AMOUNT = Decimal(42.42)
TRANSACTION_REFUND_AMOUNT = Decimal(24.24)
TRANSACTION_CURRENCY = "EUR"


# Set to True if recording new cassette with sandbox using credentials in env
RECORD = False

"""
To generate a new order:
- remove cassette test_get_client_token.yaml
- run .cassettes/test_get_client_token
- open the new test_get_client_token.yaml and copy id (ORDER_ID) from body
- open in browser https://www.sandbox.paypal.com/checkoutnow?token=<ORDER_ID>) and
approve payment with your sandbox buyer account
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
def test_authorize_success(sandbox_gateway_config, paypal_payment):
    """
    To run this you need first to:
    - run the test_create_paypal_order with RECORD = True and copy paypal_order_id
    from the cassette and paste below
    - open in browser https://www.sandbox.paypal.com/checkoutnow?token=<paypal_order_id>
    and approve payment with your sandbox buyer account
    """
    paypal_order_id = "39R61016NN2825118"  # from cassette
    payment_info = create_payment_information(paypal_payment, paypal_order_id)
    response = authorize(payment_info, sandbox_gateway_config)
    assert not response.error
    assert response.kind == TransactionKind.CAPTURE
    assert isclose(response.amount, TRANSACTION_AMOUNT)
    assert response.currency == TRANSACTION_CURRENCY
    assert response.is_success is True
    # assert response.card_info == CARD_SIMPLE_DETAILS
    assert not response.action_required


@pytest.mark.integration
@pytest.mark.vcr
def test_authorize_error(sandbox_gateway_config, paypal_payment):
    invalid_paypal_order_id = "INVALID-PAYPAL-ORDER-ID"  # from cassette
    payment_info = create_payment_information(paypal_payment, invalid_paypal_order_id)
    response = authorize(payment_info, sandbox_gateway_config)
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
    # Get id from sandbox for succeeded payment
    paypal_capture_id = "81466026X71727922"  # from cassettes/test_authorize
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
    # Get id from sandbox for succeeded payment
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
