from decimal import Decimal

import pytest

from saleor.core.payments import Gateway, PaymentInterface
from saleor.payment import TransactionKind
from saleor.payment.gateway import PaymentGateway
from saleor.payment.interface import GatewayResponse
from saleor.payment.utils import create_payment_information

RAW_RESPONSE = {"test": "abcdefgheijklmn"}
PROCESS_PAYMENT_RESPONSE = GatewayResponse(
    is_success=True,
    customer_id="test_customer",
    action_required=False,
    kind=TransactionKind.AUTH,
    amount=Decimal(10.0),
    currency="usd",
    transaction_id="1234",
    error=None,
    raw_response=RAW_RESPONSE,
)
TOKEN = "token"
USED_GATEWAY = Gateway.DUMMY


@pytest.fixture
def fake_manager(mocker):
    return mocker.Mock(spec=PaymentInterface)


@pytest.fixture(autouse=True, scope="function")
def mock_get_manager(mocker, fake_manager):
    mgr = mocker.patch(
        "saleor.payment.gateway.get_extensions_manager",
        auto_spec=True,
        return_value=fake_manager,
    )
    yield mgr
    mgr.assert_called_once()


@pytest.fixture
def gateway():
    return PaymentGateway()


def test_process_payment(gateway, payment_txn_preauth):
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=TOKEN
    )
    gateway.plugin_manager.process_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.process_payment(payment=payment_txn_preauth, token=TOKEN)

    gateway.plugin_manager.process_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )
    assert transaction.amount == PROCESS_PAYMENT_RESPONSE.amount
    assert transaction.kind == TransactionKind.AUTH
    assert transaction.currency == "usd"
    assert transaction.gateway_response == RAW_RESPONSE


def test_store_source_when_processing_payment(gateway, payment_txn_preauth):
    PAYMENT_DATA = create_payment_information(
        payment=payment_txn_preauth, payment_token=TOKEN, store_source=True
    )
    gateway.plugin_manager.process_payment.return_value = PROCESS_PAYMENT_RESPONSE

    transaction = gateway.process_payment(
        payment=payment_txn_preauth, token=TOKEN, store_source=True
    )

    gateway.plugin_manager.process_payment.assert_called_once_with(
        USED_GATEWAY, PAYMENT_DATA
    )
    assert transaction.customer_id == PROCESS_PAYMENT_RESPONSE.customer_id
