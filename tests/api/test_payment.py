import graphene
from tests.api.utils import get_graphql_content

from saleor.payment.models import (
    ChargeStatus, Payment, Transaction, TransactionType)

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
        staff_api_client, permission_manage_orders, payment_dummy):
    assert payment_dummy.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_dummy.pk)
    variables = {'paymentId': payment_id}
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentVoid']
    assert not data['errors']
    payment_dummy.refresh_from_db()
    assert payment_dummy.is_active == False
    assert payment_dummy.transactions.count() == 1
    txn = payment_dummy.transactions.first()
    assert txn.transaction_type == TransactionType.VOID


def test_payment_charge_gateway_error(
        staff_api_client, permission_manage_orders, payment_dummy,
        monkeypatch):
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_dummy.pk)
    variables = {'paymentId': payment_id}
    monkeypatch.setattr(
        'saleor.payment.providers.dummy.dummy_success', lambda: False)
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentCapture']
    assert data['errors']
    assert data['errors'][0]['field'] is None
    assert data['errors'][0]['message'] == (
        'Only pre-authorized transactions can be void.')
    payment_dummy.refresh_from_db()
    assert payment_dummy.charge_status == ChargeStatus.NOT_CHARGED
    assert payment_dummy.is_active == True
    assert payment_dummy.transactions.count() == 1
    txn = payment_dummy.transactions.first()
    assert txn.transaction_type == TransactionType.VOID
    assert not txn.is_success


CREATE_QUERY = """
    mutation CheckoutPaymentCreate($input: PaymentInput!) {
        checkoutPaymentCreate(input: $input) {
            payment {
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


def test_checkout_add_payment(
        user_api_client, cart_with_item, graphql_address_data):
    cart = cart_with_item
    assert cart.user is None

    checkout_id = graphene.Node.to_global_id('Checkout', cart.pk)

    variables = {
        'input': {
            'checkoutId': checkout_id,
            'gateway': 'DUMMY',
            'transactionToken': 'sample-token',
            'amount': str(cart.get_total().gross.amount),
            'billingAddress': graphql_address_data}}
    response = user_api_client.post_graphql(CREATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutPaymentCreate']
    assert not data['errors']
    transactions = data['payment']['transactions']['edges']
    assert not transactions
    payment = Payment.objects.get()
    assert payment.checkout == cart
    assert payment.is_active
    assert payment.token == 'sample-token'
    total = cart.get_total().gross
    assert payment.total == total.amount
    assert payment.currency == total.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED


CHARGE_QUERY = """
    mutation PaymentCharge($paymentId: ID!, $amount: Decimal!) {
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


def test_payment_charge_success(
        staff_api_client, permission_manage_orders, payment_dummy):
    payment = payment_dummy
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_dummy.pk)

    variables = {
        'paymentId': payment_id,
        'amount': str(payment_dummy.total)}
    response = staff_api_client.post_graphql(
        CHARGE_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentCapture']
    assert not data['errors']
    payment_dummy.refresh_from_db()
    assert payment.charge_status == ChargeStatus.CHARGED
    assert payment.transactions.count() == 1
    txn = payment.transactions.first()
    assert txn.transaction_type == TransactionType.CHARGE


def test_payment_charge_gateway_error(
        staff_api_client, permission_manage_orders, payment_dummy,
        monkeypatch):
    payment = payment_dummy
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_dummy.pk)
    variables = {
        'paymentId': payment_id,
        'amount': str(payment_dummy.total)}
    monkeypatch.setattr(
        'saleor.payment.providers.dummy.dummy_success', lambda: False)
    response = staff_api_client.post_graphql(
        CHARGE_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentCapture']
    assert data['errors']
    assert data['errors'][0]['field'] is None
    assert data['errors'][0]['message']

    payment_dummy.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.transactions.count() == 1
    txn = payment.transactions.first()
    assert txn.transaction_type == TransactionType.CHARGE
    assert not txn.is_success


REFUND_QUERY = """
    mutation PaymentRefund($paymentId: ID!, $amount: Decimal!) {
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
        staff_api_client, permission_manage_orders, payment_dummy):
    payment = payment_dummy
    payment.charge_status = ChargeStatus.CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id(
        'Payment', payment.pk)

    variables = {
        'paymentId': payment_id,
        'amount': str(payment_dummy.total)}
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentRefund']
    assert not data['errors']
    payment_dummy.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.transactions.count() == 1
    txn = payment.transactions.first()
    assert txn.transaction_type == TransactionType.REFUND


def test_payment_refund_error(
        staff_api_client, permission_manage_orders, payment_dummy,
        monkeypatch):
    payment = payment_dummy
    payment.charge_status = ChargeStatus.CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_dummy.pk)
    variables = {
        'paymentId': payment_id,
        'amount': str(payment.total)}
    monkeypatch.setattr(
        'saleor.payment.providers.dummy.dummy_success', lambda: False)
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentRefund']

    assert data['errors']
    assert data['errors'][0]['field'] is None
    assert data['errors'][0]['message']
    payment_dummy.refresh_from_db()
    assert payment.charge_status == ChargeStatus.CHARGED
    assert payment.transactions.count() == 1
    txn = payment.transactions.first()
    assert txn.transaction_type == TransactionType.REFUND
    assert not txn.is_success


def test_payments_query(
        payment_dummy, permission_manage_orders, staff_api_client):
    query = """ {
        payments {
            edges {
                node {
                    id
                    variant
                }
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['payments']
    assert data['edges'][0]['node']['variant'] == payment_dummy.variant
