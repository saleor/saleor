from decimal import Decimal
from unittest.mock import ANY

import pytest
from sympy.physics.units import amount

from saleor.core.payments import Gateway, PaymentInterface
from saleor.payment.gateway import PaymentGateway
from saleor.payment.interface import GatewayResponse, PaymentData
from saleor.payment.utils import create_payment_information

PROCESS_PAYMENT_RESPONSE = GatewayResponse(
    is_success=True,
    action_required=False,
    kind="process_payment",
    amount=Decimal(10.0),
    currency="usd",
    transaction_id="1234",
    error=None,
)


@pytest.fixture
def fake_manager(mocker):
    mgr = mocker.Mock(spec=PaymentInterface)
    return mgr


@pytest.fixture(autouse=True, scope="function")
def mock_get_manager(mocker, fake_manager):
    mgr = mocker.patch(
        "saleor.payment.gateway.get_extensions_manager",
        auto_spec=True,
        return_value=fake_manager,
    )
    yield mgr
    mgr.assert_called_once()


def test_process_payment(payment_txn_preauth):
    TOKEN = "token"
    gateway = PaymentGateway()
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=TOKEN
    )
    gateway.plugin_manager.process_payment.result_value = PROCESS_PAYMENT_RESPONSE

    gateway.process_payment(
        payment=payment_txn_preauth, gateway=Gateway.STRIPE, token=TOKEN
    )

    gateway.plugin_manager.process_payment.assert_called_once_with(
        Gateway.STRIPE, PAYMENT_DATA, TOKEN
    )
