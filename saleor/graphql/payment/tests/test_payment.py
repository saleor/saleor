import json
from decimal import Decimal
from unittest.mock import patch

import graphene
import pytest

from ....checkout import calculations
from ....checkout.utils import fetch_checkout_lines
from ....payment import PaymentError
from ....payment.error_codes import PaymentErrorCode
from ....payment.gateways.dummy_credit_card import (
    TOKEN_EXPIRED,
    TOKEN_VALIDATION_MAPPING,
)
from ....payment.interface import (
    CustomerSource,
    InitializedPaymentResponse,
    PaymentMethodInfo,
    TokenConfig,
)
from ....payment.models import ChargeStatus, Payment, TransactionKind
from ....payment.utils import fetch_customer_id, store_customer_id
from ....plugins.manager import PluginsManager, get_plugins_manager
from ...tests.utils import assert_no_permission, get_graphql_content
from ..enums import OrderAction, PaymentChargeStatusEnum

DUMMY_GATEWAY = "mirumee.payments.dummy"

VOID_QUERY = """
    mutation PaymentVoid($paymentId: ID!) {
        paymentVoid(paymentId: $paymentId) {
            payment {
                id,
                chargeStatus
            }
            errors {
                field
                message
            }
        }
    }
"""


def test_payment_void_success(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.is_active is False
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID


def test_payment_void_gateway_error(
    staff_api_client, permission_manage_orders, payment_txn_preauth, monkeypatch
):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment_txn_preauth.pk)
    variables = {"paymentId": payment_id}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentVoid"]
    assert data["errors"]
    assert data["errors"][0]["field"] is None
    assert data["errors"][0]["message"] == "Unable to void the transaction."
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    assert payment_txn_preauth.is_active is True
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID
    assert not txn.is_success


CREATE_PAYMENT_MUTATION = """
    mutation CheckoutPaymentCreate($checkoutId: ID!, $input: PaymentInput!) {
        checkoutPaymentCreate(checkoutId: $checkoutId, input: $input) {
            payment {
                transactions {
                    kind,
                    token
                }
                chargeStatus
            }
            paymentErrors {
                code
                field
            }
        }
    }
    """


def test_checkout_add_payment_without_shipping_method_and_not_shipping_required(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    variables = {
        "checkoutId": checkout_id,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert not data["paymentErrors"]
    transactions = data["payment"]["transactions"]
    assert not transactions
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.billing_address_1 == checkout.billing_address.street_address_1
    assert payment.billing_first_name == checkout.billing_address.first_name
    assert payment.billing_last_name == checkout.billing_address.last_name


def test_checkout_add_payment_without_shipping_method_with_shipping_required(
    user_api_client, checkout_with_shipping_required, address
):
    checkout = checkout_with_shipping_required

    checkout.billing_address = address
    checkout.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    variables = {
        "checkoutId": checkout_id,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert data["paymentErrors"][0]["code"] == "SHIPPING_METHOD_NOT_SET"
    assert data["paymentErrors"][0]["field"] == "shippingMethod"


def test_checkout_add_payment_with_shipping_method_and_shipping_required(
    user_api_client, checkout_with_shipping_required, other_shipping_method, address
):
    checkout = checkout_with_shipping_required
    checkout.billing_address = address
    checkout.shipping_address = address
    checkout.shipping_method = other_shipping_method
    checkout.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    variables = {
        "checkoutId": checkout_id,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert not data["paymentErrors"]
    transactions = data["payment"]["transactions"]
    assert not transactions
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.billing_address_1 == checkout.billing_address.street_address_1
    assert payment.billing_first_name == checkout.billing_address.first_name
    assert payment.billing_last_name == checkout.billing_address.last_name


def test_checkout_add_payment(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    return_url = "https://www.example.com"
    variables = {
        "checkoutId": checkout_id,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
            "returnUrl": return_url,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    assert not data["paymentErrors"]
    transactions = data["payment"]["transactions"]
    assert not transactions
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.billing_address_1 == checkout.billing_address.street_address_1
    assert payment.billing_first_name == checkout.billing_address.first_name
    assert payment.billing_last_name == checkout.billing_address.last_name
    assert payment.return_url == return_url


def test_checkout_add_payment_default_amount(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()

    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )

    variables = {
        "checkoutId": checkout_id,
        "input": {"gateway": DUMMY_GATEWAY, "token": "sample-token"},
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert not data["paymentErrors"]
    transactions = data["payment"]["transactions"]
    assert not transactions
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == "sample-token"
    assert payment.total == total.gross.amount
    assert payment.currency == total.gross.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED


def test_checkout_add_payment_bad_amount(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.save()
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )

    variables = {
        "checkoutId": checkout_id,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": str(total.gross.amount + Decimal(1)),
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert (
        data["paymentErrors"][0]["code"]
        == PaymentErrorCode.PARTIAL_PAYMENT_NOT_ALLOWED.name
    )


def test_checkout_add_payment_not_supported_gateways(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout.billing_address = address
    checkout.currency = "EUR"
    checkout.save(update_fields=["billing_address", "currency"])
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)

    variables = {
        "checkoutId": checkout_id,
        "input": {"gateway": DUMMY_GATEWAY, "token": "sample-token", "amount": "10.0"},
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]
    assert (
        data["paymentErrors"][0]["code"] == PaymentErrorCode.NOT_SUPPORTED_GATEWAY.name
    )
    assert data["paymentErrors"][0]["field"] == "gateway"


def test_use_checkout_billing_address_as_payment_billing(
    user_api_client, checkout_without_shipping_required, address
):
    checkout = checkout_without_shipping_required
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    variables = {
        "checkoutId": checkout_id,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)
    data = content["data"]["checkoutPaymentCreate"]

    # check if proper error is returned if address is missing
    assert data["paymentErrors"][0]["field"] == "billingAddress"
    assert (
        data["paymentErrors"][0]["code"]
        == PaymentErrorCode.BILLING_ADDRESS_NOT_SET.name
    )

    # assign the address and try again
    address.street_address_1 = "spanish-inqusition"
    address.save()
    checkout.billing_address = address
    checkout.save()
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    get_graphql_content(response)

    checkout.refresh_from_db()
    assert checkout.payments.count() == 1
    payment = checkout.payments.first()
    assert payment.billing_address_1 == address.street_address_1


def test_create_payment_for_checkout_with_active_payments(
    checkout_with_payments, user_api_client, address
):
    # given
    checkout = checkout_with_payments
    address.street_address_1 = "spanish-inqusition"
    address.save()
    checkout.billing_address = address
    checkout.save()

    manager = get_plugins_manager()
    lines = fetch_checkout_lines(checkout)
    total = calculations.checkout_total(
        manager=manager, checkout=checkout, lines=lines, address=address
    )
    checkout_id = graphene.Node.to_global_id("Checkout", checkout.pk)
    variables = {
        "checkoutId": checkout_id,
        "input": {
            "gateway": DUMMY_GATEWAY,
            "token": "sample-token",
            "amount": total.gross.amount,
        },
    }

    payments_count = checkout.payments.count()
    previous_active_payments = checkout.payments.filter(is_active=True)
    previous_active_payments_ids = list(
        previous_active_payments.values_list("pk", flat=True)
    )
    assert len(previous_active_payments_ids) > 0

    # when
    response = user_api_client.post_graphql(CREATE_PAYMENT_MUTATION, variables)
    content = get_graphql_content(response)

    # then
    data = content["data"]["checkoutPaymentCreate"]

    assert not data["paymentErrors"]
    checkout.refresh_from_db()
    assert checkout.payments.all().count() == payments_count + 1
    active_payments = checkout.payments.all().filter(is_active=True)
    assert active_payments.count() == 1
    assert active_payments.first().pk not in previous_active_payments_ids


CAPTURE_QUERY = """
    mutation PaymentCapture($paymentId: ID!, $amount: PositiveDecimal!) {
        paymentCapture(paymentId: $paymentId, amount: $amount) {
            payment {
                id,
                chargeStatus
            }
            errors {
                field
                message
            }
        }
    }
"""


def test_payment_capture_success(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert not data["errors"]
    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE


def test_payment_capture_with_invalid_argument(
    staff_api_client, permission_manage_orders, payment_txn_preauth
):
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 0}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Amount should be a positive number."


def test_payment_capture_with_payment_non_authorized_yet(
    staff_api_client, permission_manage_orders, payment_dummy
):
    """Ensure capture a payment that is set as authorized is failing with
    the proper error message.
    """
    payment = payment_dummy
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 1}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert data["errors"] == [
        {"field": None, "message": "Cannot find successful auth transaction."}
    ]


def test_payment_capture_gateway_error(
    staff_api_client, permission_manage_orders, payment_txn_preauth, monkeypatch
):
    # given
    payment = payment_txn_preauth

    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert data["errors"] == [{"field": None, "message": "Unable to process capture"}]

    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE
    assert not txn.is_success


@patch(
    "saleor.payment.gateways.dummy_credit_card.plugin."
    "DummyCreditCardGatewayPlugin.DEFAULT_ACTIVE",
    True,
)
def test_payment_capture_gateway_dummy_credit_card_error(
    staff_api_client, permission_manage_orders, payment_txn_preauth, monkeypatch
):
    # given
    token = TOKEN_EXPIRED
    error = TOKEN_VALIDATION_MAPPING[token]

    payment = payment_txn_preauth
    payment.gateway = "mirumee.payments.dummy_credit_card"
    payment.save()

    transaction = payment.transactions.last()
    transaction.token = token
    transaction.save()

    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment_txn_preauth.total)}
    monkeypatch.setattr(
        "saleor.payment.gateways.dummy_credit_card.dummy_success", lambda: False
    )

    # when
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["paymentCapture"]
    assert data["errors"] == [{"field": None, "message": error}]

    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE
    assert not txn.is_success


REFUND_QUERY = """
    mutation PaymentRefund($paymentId: ID!, $amount: PositiveDecimal!) {
        paymentRefund(paymentId: $paymentId, amount: $amount) {
            payment {
                id,
                chargeStatus
            }
            errors {
                field
                message
            }
        }
    }
"""


def test_payment_refund_success(
    staff_api_client, permission_manage_orders, payment_txn_captured
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": str(payment.total)}
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert not data["errors"]
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND


def test_payment_refund_with_invalid_argument(
    staff_api_client, permission_manage_orders, payment_txn_captured
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)

    variables = {"paymentId": payment_id, "amount": 0}
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]
    assert len(data["errors"]) == 1
    assert data["errors"][0]["message"] == "Amount should be a positive number."


def test_payment_refund_error(
    staff_api_client, permission_manage_orders, payment_txn_captured, monkeypatch
):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"paymentId": payment_id, "amount": str(payment.total)}
    monkeypatch.setattr("saleor.payment.gateways.dummy.dummy_success", lambda: False)
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["paymentRefund"]

    assert data["errors"] == [{"field": None, "message": "Unable to process refund"}]
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success


def test_payments_query(
    payment_txn_captured, permission_manage_orders, staff_api_client
):
    query = """ {
        payments(first: 20) {
            edges {
                node {
                    id
                    gateway
                    capturedAmount {
                        amount
                        currency
                    }
                    total {
                        amount
                        currency
                    }
                    actions
                    chargeStatus
                    transactions {
                        amount {
                            currency
                            amount
                        }
                    }
                }
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    data = content["data"]["payments"]["edges"][0]["node"]
    pay = payment_txn_captured
    assert data["gateway"] == pay.gateway
    amount = str(data["capturedAmount"]["amount"])
    assert Decimal(amount) == pay.captured_amount
    assert data["capturedAmount"]["currency"] == pay.currency
    total = str(data["total"]["amount"])
    assert Decimal(total) == pay.total
    assert data["total"]["currency"] == pay.currency
    assert data["chargeStatus"] == PaymentChargeStatusEnum.FULLY_CHARGED.name
    assert data["actions"] == [OrderAction.REFUND.name]
    txn = pay.transactions.get()
    assert data["transactions"] == [
        {"amount": {"currency": pay.currency, "amount": float(str(txn.amount))}}
    ]


def test_query_payment(payment_dummy, user_api_client, permission_manage_orders):
    query = """
    query payment($id: ID!) {
        payment(id: $id) {
            id
        }
    }
    """
    payment = payment_dummy
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    variables = {"id": payment_id}
    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    received_id = content["data"]["payment"]["id"]
    assert received_id == payment_id


def test_query_payments(payment_dummy, permission_manage_orders, staff_api_client):
    query = """
    {
        payments(first: 20) {
            edges {
                node {
                    id
                }
            }
        }
    }
    """
    payment = payment_dummy
    payment_id = graphene.Node.to_global_id("Payment", payment.pk)
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_orders]
    )
    content = get_graphql_content(response)
    edges = content["data"]["payments"]["edges"]
    payment_ids = [edge["node"]["id"] for edge in edges]
    assert payment_ids == [payment_id]


@pytest.fixture
def braintree_customer_id():
    return "1234"


@pytest.fixture
def dummy_customer_id():
    return "4321"


def test_store_payment_gateway_meta(customer_user, braintree_customer_id):
    gateway_name = "braintree"
    meta_key = "BRAINTREE.customer_id"
    META = {meta_key: braintree_customer_id}
    store_customer_id(customer_user, gateway_name, braintree_customer_id)
    assert customer_user.private_metadata == META
    customer_user.refresh_from_db()
    assert fetch_customer_id(customer_user, gateway_name) == braintree_customer_id


@pytest.fixture
def token_config_with_customer(braintree_customer_id):
    return TokenConfig(customer_id=braintree_customer_id)


@pytest.fixture
def set_braintree_customer_id(customer_user, braintree_customer_id):
    gateway_name = "braintree"
    store_customer_id(customer_user, gateway_name, braintree_customer_id)
    return customer_user


@pytest.fixture
def set_dummy_customer_id(customer_user, dummy_customer_id):
    gateway_name = DUMMY_GATEWAY
    store_customer_id(customer_user, gateway_name, dummy_customer_id)
    return customer_user


def test_list_payment_sources(
    mocker, dummy_customer_id, set_dummy_customer_id, user_api_client
):
    gateway = DUMMY_GATEWAY
    query = """
    {
        me {
            storedPaymentSources {
                gateway
                creditCardInfo {
                    lastDigits
                }
            }
        }
    }
    """
    card = PaymentMethodInfo(last_4="5678", exp_year=2020, exp_month=12, name="JohnDoe")
    source = CustomerSource(id="test1", gateway=gateway, credit_card_info=card)
    mock_get_source_list = mocker.patch(
        "saleor.graphql.account.resolvers.gateway.list_payment_sources",
        return_value=[source],
        autospec=True,
    )
    response = user_api_client.post_graphql(query)

    mock_get_source_list.assert_called_once_with(gateway, dummy_customer_id)
    content = get_graphql_content(response)["data"]["me"]["storedPaymentSources"]
    assert content is not None and len(content) == 1
    assert content[0] == {"gateway": gateway, "creditCardInfo": {"lastDigits": "5678"}}


def test_stored_payment_sources_restriction(
    mocker, staff_api_client, customer_user, permission_manage_users
):
    # Only owner of storedPaymentSources can fetch it.
    card = PaymentMethodInfo(last_4="5678", exp_year=2020, exp_month=12, name="JohnDoe")
    source = CustomerSource(id="test1", gateway="dummy", credit_card_info=card)
    mocker.patch(
        "saleor.graphql.account.resolvers.gateway.list_payment_sources",
        return_value=[source],
        autospec=True,
    )

    customer_user_id = graphene.Node.to_global_id("User", customer_user.pk)
    query = """
        query PaymentSources($id: ID!) {
            user(id: $id) {
                storedPaymentSources {
                    creditCardInfo {
                        firstDigits
                    }
                }
            }
        }
    """
    variables = {"id": customer_user_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    assert_no_permission(response)


PAYMENT_INITIALIZE_MUTATION = """
mutation PaymentInitialize($gateway: String!, $paymentData: JSONString){
      paymentInitialize(gateway: $gateway, paymentData: $paymentData)
      {
        initializedPayment{
          gateway
          name
          data
        }
        paymentErrors{
          field
          message
        }
      }
}
"""


@patch.object(PluginsManager, "initialize_payment")
def test_payment_initialize(mocked_initialize_payment, api_client):
    exected_initialize_payment_response = InitializedPaymentResponse(
        gateway="gateway.id",
        name="PaymentPluginName",
        data={
            "epochTimestamp": 1604652056653,
            "expiresAt": 1604655656653,
            "merchantSessionIdentifier": "SSH5EFCB46BA25C4B14B3F37795A7F5B974_BB8E",
        },
    )
    mocked_initialize_payment.return_value = exected_initialize_payment_response

    query = PAYMENT_INITIALIZE_MUTATION
    variables = {
        "gateway": exected_initialize_payment_response.gateway,
        "paymentData": json.dumps(
            {"paymentMethod": "applepay", "validationUrl": "https://127.0.0.1/valid"}
        ),
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    init_payment_data = content["data"]["paymentInitialize"]["initializedPayment"]
    assert init_payment_data["gateway"] == exected_initialize_payment_response.gateway
    assert init_payment_data["name"] == exected_initialize_payment_response.name
    assert (
        json.loads(init_payment_data["data"])
        == exected_initialize_payment_response.data
    )


def test_payment_initialize_gateway_doesnt_exist(api_client):
    query = PAYMENT_INITIALIZE_MUTATION
    variables = {
        "gateway": "wrong.gateway",
        "paymentData": json.dumps(
            {"paymentMethod": "applepay", "validationUrl": "https://127.0.0.1/valid"}
        ),
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    assert content["data"]["paymentInitialize"]["initializedPayment"] is None


@patch.object(PluginsManager, "initialize_payment")
def test_payment_initialize_plugin_raises_error(mocked_initialize_payment, api_client):
    error_msg = "Missing paymentMethod field."
    mocked_initialize_payment.side_effect = PaymentError(error_msg)

    query = PAYMENT_INITIALIZE_MUTATION
    variables = {
        "gateway": "gateway.id",
        "paymentData": json.dumps({"validationUrl": "https://127.0.0.1/valid"}),
    }
    response = api_client.post_graphql(query, variables)
    content = get_graphql_content(response)
    initialized_payment_data = content["data"]["paymentInitialize"][
        "initializedPayment"
    ]
    errors = content["data"]["paymentInitialize"]["paymentErrors"]
    assert initialized_payment_data is None
    assert len(errors) == 1
    assert errors[0]["field"] == "paymentData"
    assert errors[0]["message"] == error_msg
