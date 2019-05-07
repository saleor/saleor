from unittest.mock import patch

import graphene

from saleor.core.utils import get_country_name_by_code
from saleor.graphql.payment.enums import (
    OrderAction, PaymentChargeStatusEnum, PaymentGatewayEnum)
from saleor.payment.models import ChargeStatus, Payment, TransactionKind
from tests.api.utils import get_graphql_content

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
        staff_api_client, permission_manage_orders, payment_txn_preauth):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_txn_preauth.pk)
    variables = {'paymentId': payment_id}
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentVoid']
    assert not data['errors']
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.is_active is False
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID


def test_payment_void_gateway_error(
        staff_api_client, permission_manage_orders, payment_txn_preauth,
        monkeypatch):
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_txn_preauth.pk)
    variables = {'paymentId': payment_id}
    monkeypatch.setattr(
        'saleor.payment.gateways.dummy.dummy_success', lambda: False)
    response = staff_api_client.post_graphql(
        VOID_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentVoid']
    assert data['errors']
    assert data['errors'][0]['field'] is None
    assert data['errors'][0]['message'] == 'Unable to void the transaction.'
    payment_txn_preauth.refresh_from_db()
    assert payment_txn_preauth.charge_status == ChargeStatus.NOT_CHARGED
    assert payment_txn_preauth.is_active is True
    assert payment_txn_preauth.transactions.count() == 2
    txn = payment_txn_preauth.transactions.last()
    assert txn.kind == TransactionKind.VOID
    assert not txn.is_success


CREATE_QUERY = """
    mutation CheckoutPaymentCreate($checkoutId: ID!, $input: PaymentInput!) {
        checkoutPaymentCreate(checkoutId: $checkoutId, input: $input) {
            payment {
                transactions {
                    kind,
                    token
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
        user_api_client, checkout_with_item, graphql_address_data):
    checkout = checkout_with_item
    checkout_id = graphene.Node.to_global_id('Checkout', checkout.pk)
    variables = {
        'checkoutId': checkout_id,
        'input': {
            'gateway': 'DUMMY',
            'token': 'sample-token',
            'amount': str(checkout.get_total().gross.amount),
            'billingAddress': graphql_address_data}}
    response = user_api_client.post_graphql(CREATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutPaymentCreate']
    assert not data['errors']
    transactions = data['payment']['transactions']
    assert not transactions
    payment = Payment.objects.get()
    assert payment.checkout == checkout
    assert payment.is_active
    assert payment.token == 'sample-token'
    total = checkout.get_total().gross
    assert payment.total == total.amount
    assert payment.currency == total.currency
    assert payment.charge_status == ChargeStatus.NOT_CHARGED


def test_use_checkout_billing_address_as_payment_billing(
        user_api_client, checkout_with_item, address):
    checkout = checkout_with_item
    checkout_id = graphene.Node.to_global_id('Checkout', checkout.pk)
    variables = {
        'checkoutId': checkout_id,
        'input': {
            'gateway': 'DUMMY',
            'token': 'sample-token',
            'amount': str(checkout.get_total().gross.amount)}}
    response = user_api_client.post_graphql(CREATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutPaymentCreate']

    # check if proper error is returned if address is missing
    assert data['errors'][0]['field'] == 'billingAddress'

    # assign the address and try again
    address.street_address_1 = 'spanish-inqusition'
    address.save()
    checkout.billing_address = address
    checkout.save()
    response = user_api_client.post_graphql(CREATE_QUERY, variables)
    content = get_graphql_content(response)
    data = content['data']['checkoutPaymentCreate']

    checkout.refresh_from_db()
    assert checkout.payments.count() == 1
    payment = checkout.payments.first()
    assert payment.billing_address_1 == address.street_address_1


CAPTURE_QUERY = """
    mutation PaymentCapture($paymentId: ID!, $amount: Decimal!) {
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
        staff_api_client, permission_manage_orders, payment_txn_preauth):
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_txn_preauth.pk)

    variables = {
        'paymentId': payment_id,
        'amount': str(payment_txn_preauth.total)}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentCapture']
    assert not data['errors']
    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE


def test_payment_capture_with_invalid_argument(
        staff_api_client, permission_manage_orders, payment_txn_preauth):
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_txn_preauth.pk)

    variables = {
        'paymentId': payment_id,
        'amount': 0}
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentCapture']
    assert len(data['errors']) == 1
    assert data['errors'][0]['message'] == \
        'Amount should be a positive number.'


def test_payment_capture_gateway_error(
        staff_api_client, permission_manage_orders, payment_txn_preauth,
        monkeypatch):
    payment = payment_txn_preauth
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    payment_id = graphene.Node.to_global_id(
        'Payment', payment_txn_preauth.pk)
    variables = {
        'paymentId': payment_id,
        'amount': str(payment_txn_preauth.total)}
    monkeypatch.setattr(
        'saleor.payment.gateways.dummy.dummy_success', lambda: False)
    response = staff_api_client.post_graphql(
        CAPTURE_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentCapture']
    assert data['errors']
    assert data['errors'][0]['field'] is None
    assert data['errors'][0]['message']

    payment_txn_preauth.refresh_from_db()
    assert payment.charge_status == ChargeStatus.NOT_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.CAPTURE
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
        staff_api_client, permission_manage_orders, payment_txn_captured):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id(
        'Payment', payment.pk)

    variables = {
        'paymentId': payment_id,
        'amount': str(payment.total)}
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentRefund']
    assert not data['errors']
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_REFUNDED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND


def test_payment_refund_with_invalid_argument(
        staff_api_client, permission_manage_orders, payment_txn_captured):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id(
        'Payment', payment.pk)

    variables = {
        'paymentId': payment_id,
        'amount': 0}
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentRefund']
    assert len(data['errors']) == 1
    assert data['errors'][0]['message'] == \
        'Amount should be a positive number.'


def test_payment_refund_error(
        staff_api_client, permission_manage_orders, payment_txn_captured,
        monkeypatch):
    payment = payment_txn_captured
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()
    payment_id = graphene.Node.to_global_id(
        'Payment', payment.pk)
    variables = {
        'paymentId': payment_id,
        'amount': str(payment.total)}
    monkeypatch.setattr(
        'saleor.payment.gateways.dummy.dummy_success', lambda: False)
    response = staff_api_client.post_graphql(
        REFUND_QUERY, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['paymentRefund']

    assert data['errors']
    assert data['errors'][0]['field'] is None
    assert data['errors'][0]['message']
    payment.refresh_from_db()
    assert payment.charge_status == ChargeStatus.FULLY_CHARGED
    assert payment.transactions.count() == 2
    txn = payment.transactions.last()
    assert txn.kind == TransactionKind.REFUND
    assert not txn.is_success


def test_payments_query(
        payment_txn_captured, permission_manage_orders, staff_api_client):
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
                    billingAddress {
                        country {
                            code
                            country
                        }
                        firstName
                        lastName
                        cityArea
                        countryArea
                        city
                        companyName
                        streetAddress1
                        streetAddress2
                        postalCode
                    }
                    transactions {
                        amount {
                            currency
                            amount
                        }
                    }
                    creditCard {
                        expMonth
                        expYear
                        brand
                        firstDigits
                        lastDigits
                    }
                }
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    data = content['data']['payments']['edges'][0]['node']
    pay = payment_txn_captured
    assert data['gateway'] == pay.gateway
    assert data['capturedAmount'] == {
        'amount': pay.captured_amount, 'currency': pay.currency}
    assert data['total'] == {'amount': pay.total, 'currency': pay.currency}
    assert data['chargeStatus'] == PaymentChargeStatusEnum.FULLY_CHARGED.name
    assert data['billingAddress'] == {
        'firstName': pay.billing_first_name,
        'lastName': pay.billing_last_name,
        'city': pay.billing_city,
        'cityArea': pay.billing_city_area,
        'countryArea': pay.billing_country_area,
        'companyName': pay.billing_company_name,
        'streetAddress1': pay.billing_address_1,
        'streetAddress2': pay.billing_address_2,
        'postalCode': pay.billing_postal_code,
        'country': {
            'code': pay.billing_country_code,
            'country': get_country_name_by_code(pay.billing_country_code)
        }
    }
    assert data['actions'] == [OrderAction.REFUND.name]
    txn = pay.transactions.get()
    assert data['transactions'] == [{
        'amount': {
            'currency': pay.currency,
            'amount': float(str(txn.amount))}}]
    assert data['creditCard'] == {
        'expMonth': pay.cc_exp_month,
        'expYear': pay.cc_exp_year,
        'brand': pay.cc_brand,
        'firstDigits': pay.cc_first_digits,
        'lastDigits': pay.cc_last_digits}


def test_query_payment(
        payment_dummy, user_api_client, permission_manage_orders):
    query = """
    query payment($id: ID) {
        payment(id: $id) {
            id
        }
    }
    """
    payment = payment_dummy
    payment_id = graphene.Node.to_global_id('Payment', payment.pk)
    variables = {'id': payment_id}
    response = user_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    received_id = content['data']['payment']['id']
    assert received_id == payment_id


def test_query_payments(
        payment_dummy, permission_manage_orders, staff_api_client):
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
    payment_id = graphene.Node.to_global_id('Payment', payment.pk)
    response = staff_api_client.post_graphql(
        query, {}, permissions=[permission_manage_orders])
    content = get_graphql_content(response)
    edges = content['data']['payments']['edges']
    payment_ids = [edge['node']['id'] for edge in edges]
    assert payment_ids == [payment_id]


@patch('saleor.graphql.payment.resolvers.gateway_get_client_token')
def test_query_payment_client_token(mock_get_client_token, user_api_client):
    query = """
    query paymentClientToken($gateway: GatewaysEnum) {
        paymentClientToken(gateway: $gateway)
    }
    """
    example_token = 'example-token'
    mock_get_client_token.return_value = example_token
    variables = {'gateway': PaymentGatewayEnum.BRAINTREE.name}
    response = user_api_client.post_graphql(query, variables)

    content = get_graphql_content(response)
    assert mock_get_client_token.called_once_with(
        PaymentGatewayEnum.BRAINTREE.name)
    token = content['data']['paymentClientToken']
    assert token == example_token
