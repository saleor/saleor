import json
import pytest

import graphene
from django.shortcuts import reverse
from tests.utils import get_graphql_content
from saleor.payment.models import Transaction, PaymentMethodChargeStatus, TransactionType

CHARGE_QUERY = """
        mutation PaymentMethodCharge($paymentMethodId: ID!, $amount: Decimal!) {
            paymentMethodCharge(paymentMethodId: $paymentMethodId, amount: $amount) {
                paymentMethod {
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

REFUND_QUERY = """
        mutation PaymentMethodRefund($paymentMethodId: ID!, $amount: Decimal!) {
            paymentMethodRefund(paymentMethodId: $paymentMethodId, amount: $amount) {
                paymentMethod {
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

VOID_QUERY = """
        mutation PaymentMethodRefund($paymentMethodId: ID!, $amount: Decimal!) {
            paymentMethodRefund(paymentMethodId: $paymentMethodId, amount: $amount) {
                paymentMethod {
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

CREATE_QUERY = """
        mutation CheckoutPaymentMethodCreate($input: PaymentMethodInput!) {
            checkoutPaymentMethodCreate(input: $input) {
                paymentMethod {
                    transactions(first: 1) {
                        edges {
                            node {
                                transactionType,
                                token
                            }
                        }
                    }
                    chargeStatus
                }
                errors {
                    field
                    message
                }
            }
        }
    """

def test_checkout_add_payment_method(
        user_api_client, cart_with_item, graphql_address_data):
    cart = cart_with_item
    assert cart.user is None

    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    variables = json.dumps({
        'input': {
            'checkoutId': checkout_id,
            'gateway': 'DUMMY',
            'transactionToken': 'sample-token',
            'amount': str(cart.get_total().gross.amount),
            'billingAddress': graphql_address_data,
            'storePaymentMethod': False}
    })
    response = user_api_client.post(
        reverse('api'), {'query': CREATE_QUERY, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['checkoutPaymentMethodCreate']
    assert not data['errors']
    transaction_id = data['paymentMethod']['transactions']['edges'][0]['node']['token']
    txn = Transaction.objects.filter(token=transaction_id).first()
    assert txn.transaction_type == TransactionType.AUTH
    assert txn is not None
    payment_method = txn.payment_method
    assert payment_method.checkout == cart
    assert payment_method.is_active
    assert payment_method.total == cart.get_total().gross.amount
    assert payment_method.charge_status == PaymentMethodChargeStatus.NOT_CHARGED


def test_payment_method_charge_success(admin_api_client, payment_method_dummy):

    payment_method = payment_method_dummy
    assert payment_method.charge_status == PaymentMethodChargeStatus.NOT_CHARGED
    payment_method_id = graphene.Node.to_global_id(
        'PaymentMethod', payment_method_dummy.pk)

    variables = json.dumps({
        'paymentMethodId': payment_method_id,
        'amount': payment_method_dummy.total
    })
    response = admin_api_client.post(
        reverse('api'), {'query': CHARGE_QUERY, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['paymentMethodCharge']
    assert not data['errors']
    payment_method_dummy.refresh_from_db()
    assert payment_method.charge_status == PaymentMethodChargeStatus.CHARGED
    assert payment_method.transactions.count() == 1
    txn = payment_method.transactions.first()
    assert txn.transaction_type == TransactionType.CHARGE


def test_payment_method_charge_gateway_error(
        admin_api_client, payment_method_dummy, monkeypatch):

    payment_method = payment_method_dummy
    assert payment_method.charge_status == PaymentMethodChargeStatus.NOT_CHARGED
    payment_method_id = graphene.Node.to_global_id(
        'PaymentMethod', payment_method_dummy.pk)

    variables = json.dumps({
        'paymentMethodId': payment_method_id,
        'amount': payment_method_dummy.total
    })
    monkeypatch.setattr(
        'saleor.payment.providers.dummy.dummy_success', lambda: False)
    response = admin_api_client.post(
        reverse('api'), {'query': CHARGE_QUERY, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['paymentMethodCharge']
    assert 'errors' in data
    errors = data['errors']
    assert errors[0]['field'] == None
    assert errors[0]['message'] is not None
    payment_method_dummy.refresh_from_db()
    assert payment_method.charge_status == PaymentMethodChargeStatus.NOT_CHARGED
    assert payment_method.transactions.count() == 1
    txn = payment_method.transactions.first()
    assert txn.transaction_type == TransactionType.CHARGE
    assert not txn.is_success


def test_payment_method_refund_success(admin_api_client, payment_method_dummy):

    payment_method = payment_method_dummy
    payment_method.charge_status = PaymentMethodChargeStatus.CHARGED
    payment_method.captured_amount = payment_method.total
    payment_method.save()
    payment_method_id = graphene.Node.to_global_id(
        'PaymentMethod', payment_method.pk)

    variables = json.dumps({
        'paymentMethodId': payment_method_id,
        'amount': payment_method_dummy.total
    })
    response = admin_api_client.post(
        reverse('api'), {'query': REFUND_QUERY, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['paymentMethodRefund']
    assert not data['errors']
    payment_method_dummy.refresh_from_db()
    assert payment_method.charge_status == PaymentMethodChargeStatus.FULLY_REFUNDED
    assert payment_method.transactions.count() == 1
    txn = payment_method.transactions.first()
    assert txn.transaction_type == TransactionType.REFUND


def test_payment_method_refund_error(
    admin_api_client, payment_method_dummy, monkeypatch):

    payment_method = payment_method_dummy
    payment_method.charge_status = PaymentMethodChargeStatus.CHARGED
    payment_method.captured_amount = payment_method.total
    payment_method.save()
    payment_method_id = graphene.Node.to_global_id(
        'PaymentMethod', payment_method_dummy.pk)
    variables = json.dumps({
        'paymentMethodId': payment_method_id,
        'amount': payment_method.total
    })
    monkeypatch.setattr(
        'saleor.payment.providers.dummy.dummy_success', lambda: False)
    response = admin_api_client.post(
        reverse('api'), {'query': REFUND_QUERY, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['paymentMethodRefund']
    assert 'errors' in data
    errors = data['errors']
    assert errors[0]['field'] == None
    assert errors[0]['message'] is not None
    payment_method_dummy.refresh_from_db()
    assert payment_method.charge_status == PaymentMethodChargeStatus.CHARGED
    assert payment_method.transactions.count() == 1
    txn = payment_method.transactions.first()
    assert txn.transaction_type == TransactionType.REFUND
    assert not txn.is_success
