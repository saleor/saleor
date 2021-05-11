import pytest

from ....payment import TransactionKind
from ..utils import parse_payment_action_response


@pytest.fixture
def payment_action_response(dummy_payment_data):
    return {
        "action_required": False,
        "action_required_data": {},
        "amount": dummy_payment_data.amount,
        "currency": dummy_payment_data.currency,
        "customer_id": "1000",
        "kind": TransactionKind.AUTH,
        "payment_method": {
            "brand": "Visa",
            "exp_month": "05",
            "exp_year": "2025",
            "last_4": "4444",
            "name": "John Doe",
            "type": "card",
        },
        "searchable_key": "1000",
        "transaction_id": "1000",
        "transaction_already_processed": False,
    }


def test_parse_payment_action_response(dummy_payment_data, payment_action_response):
    gateway_response = parse_payment_action_response(
        dummy_payment_data, payment_action_response, TransactionKind.AUTH
    )
    assert gateway_response.error is None
    assert gateway_response.is_success
    assert gateway_response.raw_response == payment_action_response
    assert (
        gateway_response.action_required == payment_action_response["action_required"]
    )
    assert (
        gateway_response.action_required_data
        == payment_action_response["action_required_data"]
    )
    assert gateway_response.amount == payment_action_response["amount"]
    assert gateway_response.currency == payment_action_response["currency"]
    assert gateway_response.customer_id == payment_action_response["customer_id"]
    assert gateway_response.kind == payment_action_response["kind"]
    assert gateway_response.searchable_key == payment_action_response["searchable_key"]
    assert gateway_response.transaction_id == payment_action_response["transaction_id"]
    assert (
        gateway_response.transaction_already_processed
        == payment_action_response["transaction_already_processed"]
    )

    assert (
        gateway_response.payment_method_info.brand
        == payment_action_response["payment_method"]["brand"]
    )
    assert (
        gateway_response.payment_method_info.exp_month
        == payment_action_response["payment_method"]["exp_month"]
    )
    assert (
        gateway_response.payment_method_info.exp_year
        == payment_action_response["payment_method"]["exp_year"]
    )
    assert (
        gateway_response.payment_method_info.last_4
        == payment_action_response["payment_method"]["last_4"]
    )
    assert (
        gateway_response.payment_method_info.name
        == payment_action_response["payment_method"]["name"]
    )
    assert (
        gateway_response.payment_method_info.type
        == payment_action_response["payment_method"]["type"]
    )
