import pytest

from .... import TransactionKind
from ....interface import PaymentData
from .. import (
    authenticate_test,
    capture,
    list_client_sources,
    process_payment,
    refund,
    void,
)

INVALID_TOKEN = "Y29kZTo1MF8yXzA2MDAwIHRva2VuOjEgdjoxLjE="
SUCCESS_TRANSACTION_ID = "60156217587"
REFUND_AMOUNT = 10.0
REFUND_TOKEN = "test"


@pytest.mark.integration
@pytest.mark.vcr
def test_authenticate_test():
    success, _ = authenticate_test("test", "test", True)
    assert success


@pytest.mark.integration
@pytest.mark.vcr
def test_authenticate_test_failure():
    success, message = authenticate_test("test", "test", True)
    assert not success
    assert message == "User authentication failed due to invalid authentication values."


@pytest.mark.integration
@pytest.mark.vcr
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
@pytest.mark.vcr
def test_process_payment_with_user(
    dummy_payment_data, authorize_net_gateway_config, address
):
    dummy_payment_data.token = INVALID_TOKEN
    dummy_payment_data.billing = address
    user_id = 123
    response = process_payment(
        dummy_payment_data, authorize_net_gateway_config, user_id
    )
    assert not response.error
    assert response.kind == TransactionKind.CAPTURE
    assert response.is_success
    assert response.amount == dummy_payment_data.amount
    assert response.currency == dummy_payment_data.currency


@pytest.mark.integration
@pytest.mark.vcr
def test_process_payment_reuse_source(dummy_payment_data, authorize_net_gateway_config):
    dummy_payment_data.token = INVALID_TOKEN
    dummy_payment_data.reuse_source = True
    user_id = 124
    response = process_payment(
        dummy_payment_data, authorize_net_gateway_config, user_id
    )
    assert not response.error
    assert response.kind == TransactionKind.CAPTURE
    assert response.is_success
    assert response.customer_id == 1929153842


@pytest.mark.integration
@pytest.mark.vcr
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


@pytest.mark.integration
@pytest.mark.vcr
def test_process_payment_error_response_null(
    dummy_payment_data, authorize_net_gateway_config
):
    dummy_payment_data.token = INVALID_TOKEN
    response = process_payment(dummy_payment_data, authorize_net_gateway_config)
    assert response.error == "Null Response"
    assert not response.is_success


@pytest.mark.integration
@pytest.mark.vcr
def test_refund(authorize_net_payment, authorize_net_gateway_config):
    payment_data = PaymentData(
        authorize_net_payment.gateway,
        REFUND_AMOUNT,
        "USD",
        None,
        None,
        payment_id=authorize_net_payment.pk,
        graphql_payment_id=None,
        order_id=authorize_net_payment.order_id,
        customer_ip_address=authorize_net_payment.customer_ip_address,
        customer_email=authorize_net_payment.billing_email,
        token=REFUND_TOKEN,
    )
    response = refund(
        payment_data,
        authorize_net_payment.cc_last_digits,
        authorize_net_gateway_config,
    )
    assert not response.error
    assert response.kind == TransactionKind.REFUND
    assert response.is_success


@pytest.mark.integration
@pytest.mark.vcr
def test_refund_error(authorize_net_payment, authorize_net_gateway_config):
    payment_data = PaymentData(
        authorize_net_payment.gateway,
        REFUND_AMOUNT,
        "USD",
        None,
        None,
        payment_id=authorize_net_payment.pk,
        graphql_payment_id=None,
        order_id=authorize_net_payment.order_id,
        customer_ip_address=authorize_net_payment.customer_ip_address,
        customer_email=authorize_net_payment.billing_email,
        token=REFUND_TOKEN,
    )
    response = refund(
        payment_data,
        authorize_net_payment.cc_last_digits,
        authorize_net_gateway_config,
    )
    assert response.error
    assert response.kind == TransactionKind.REFUND
    assert not response.is_success


@pytest.mark.integration
@pytest.mark.vcr
def test_authorize_and_capture(dummy_payment_data, authorize_net_gateway_config):
    dummy_payment_data.token = INVALID_TOKEN
    authorize_net_gateway_config.auto_capture = False

    response = process_payment(dummy_payment_data, authorize_net_gateway_config)
    transaction_id = response.transaction_id
    assert not response.error
    assert response.kind == TransactionKind.AUTH
    assert response.is_success
    assert response.amount == dummy_payment_data.amount
    assert response.currency == dummy_payment_data.currency
    assert not response.action_required

    dummy_payment_data.token = str(transaction_id)
    response = capture(dummy_payment_data, authorize_net_gateway_config)
    assert not response.error
    assert response.kind == TransactionKind.CAPTURE
    assert response.is_success
    assert response.amount == dummy_payment_data.amount
    assert response.currency == dummy_payment_data.currency
    assert not response.action_required


@pytest.mark.integration
@pytest.mark.vcr
def test_void(authorize_net_payment, authorize_net_gateway_config):
    payment_data = PaymentData(
        authorize_net_payment.gateway,
        None,
        None,
        None,
        None,
        payment_id=authorize_net_payment.pk,
        graphql_payment_id=None,
        order_id=authorize_net_payment.order_id,
        customer_ip_address=authorize_net_payment.customer_ip_address,
        customer_email=authorize_net_payment.billing_email,
        token="1",
    )
    response = void(
        payment_data,
        authorize_net_gateway_config,
    )
    assert not response.error
    assert response.kind == TransactionKind.VOID
    assert response.is_success


@pytest.mark.integration
@pytest.mark.vcr
def test_void_duplicate(authorize_net_payment, authorize_net_gateway_config):
    """Test that duplicate voids are considered successful."""
    payment_data = PaymentData(
        authorize_net_payment.gateway,
        None,
        None,
        None,
        None,
        payment_id=authorize_net_payment.pk,
        graphql_payment_id=None,
        order_id=authorize_net_payment.order_id,
        customer_ip_address=authorize_net_payment.customer_ip_address,
        customer_email=authorize_net_payment.billing_email,
        token="1",
    )
    response = void(
        payment_data,
        authorize_net_gateway_config,
    )
    assert not response.error
    assert response.kind == TransactionKind.VOID
    assert response.is_success


@pytest.mark.integration
@pytest.mark.vcr
def test_void_failure(authorize_net_payment, authorize_net_gateway_config):
    """Test void with invalid transaction ID."""
    payment_data = PaymentData(
        authorize_net_payment.gateway,
        None,
        None,
        None,
        None,
        payment_id=authorize_net_payment.pk,
        graphql_payment_id=None,
        order_id=authorize_net_payment.order_id,
        customer_ip_address=authorize_net_payment.customer_ip_address,
        customer_email=authorize_net_payment.billing_email,
        token="1",
    )
    response = void(
        payment_data,
        authorize_net_gateway_config,
    )
    assert response.error
    assert response.kind == TransactionKind.VOID
    assert not response.is_success


@pytest.mark.integration
@pytest.mark.vcr
def test_list_client_sources(authorize_net_gateway_config):
    customer_id = "1929079648"
    response = list_client_sources(authorize_net_gateway_config, customer_id)
    assert len(response) == 1
    assert response[0].id == 1841309241
    assert response[0].credit_card_info.last_4 == "1111"
    assert response[0].credit_card_info.exp_year == 2021
    assert response[0].credit_card_info.exp_month == 2
    assert response[0].credit_card_info.brand == "Visa"
    assert response[0].credit_card_info.name == "John Doe"


@pytest.mark.integration
@pytest.mark.vcr
def test_list_client_sources_other_name(authorize_net_gateway_config):
    customer_id = "1929079648"
    response = list_client_sources(authorize_net_gateway_config, customer_id)
    assert len(response) == 1
    assert response[0].credit_card_info.name == "Doe"
