import pytest

from .... import TransactionKind
from .. import process_payment, authenticate_test


INVALID_TOKEN = "Y29kZTo1MF8yXzA2MDAwIHRva2VuOjEgdjoxLjE="
SUCCESS_TRANSACTION_ID = 60156217587


@pytest.mark.integration
@pytest.mark.vcr()
def test_authenticate_test():
    success, _ = authenticate_test("test", "test", True)
    assert success


@pytest.mark.integration
@pytest.mark.vcr()
def test_authenticate_test_failure():
    success, message = authenticate_test("test", "test", True)
    assert not success
    assert message == "User authentication failed due to invalid authentication values."


@pytest.mark.integration
@pytest.mark.vcr()
def test_process_payment(dummy_payment_data, authorize_net_gateway_config):
    dummy_payment_data.token = INVALID_TOKEN
    response = process_payment(dummy_payment_data, authorize_net_gateway_config)
    assert not response.error
    assert response.transaction_id == SUCCESS_TRANSACTION_ID
    assert response.kind == TransactionKind.CAPTURE
    assert response.is_success
    assert response.amount == dummy_payment_data.amount
    assert response.currency == dummy_payment_data.currency
    assert not response.action_required


@pytest.mark.integration
@pytest.mark.vcr()
def test_process_payment_error_response(
    dummy_payment_data, authorize_net_gateway_config
):
    dummy_payment_data.token = INVALID_TOKEN
    response = process_payment(dummy_payment_data, authorize_net_gateway_config)
    assert (
        response.error
        == "User authentication failed due to invalid authentication values."
    )
    assert response.transaction_id == INVALID_TOKEN
    assert response.kind == TransactionKind.CAPTURE
    assert not response.is_success
    assert response.amount == dummy_payment_data.amount
    assert response.currency == dummy_payment_data.currency
    assert not response.action_required
