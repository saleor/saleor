from typing import Dict
import uuid
from django.db import transaction
import braintree

from ... import TransactionType, PaymentMethodChargeStatus
from ...models import Transaction

#FIXME: Move to SiteSettings

AUTO_CHARGE = False
THREE_D_SECURE_REQUIRED = False

def extract_gateway_response(braintree_result) -> Dict:
    """
    Extract data from Braintree response that will be stored locally
    """
    errors = {}
    if not braintree_result.is_success:
        errors = [
            {'code': error.code, 'message': error.message}
            for error in braintree_result.errors.deep_errors
        ]

    transaction = braintree_result.transaction
    gateway_response = {
        'credit_card': braintree_result.transaction.credit_card,
        'additional_processor_response': transaction.additional_processor_response,
        'gateway_rejection_reason': transaction.gateway_rejection_reason,
        'processor_response_code': transaction.processor_response_code,
        'processor_response_text': transaction.processor_response_text,
        'processor_settlement_response_code': transaction.processor_settlement_response_code,
        'processor_settlement_response_text': transaction.processor_settlement_response_text,
        'risk_data': transaction.risk_data,
        'status': transaction.status,
        'errors': errors}
    return gateway_response

def get_gateway(sandbox_mode, merchant_id, public_key, private_key):
    environment = braintree.Environment.Sandbox
    if not sandbox_mode:
        environment = braintree.Environment.Production

    gateway = braintree.BraintreeGateway(
        braintree.Configuration(
            environment=environment,
            merchant_id=merchant_id,
            public_key=public_key,
            private_key=private_key
        )
    )
    return gateway


def authorize(payment_method,  transaction_token, **client_kwargs):
    gateway = get_gateway(**client_kwargs)
    result = gateway.transaction.sale({
      'amount': payment_method.total,
      'payment_method_nonce': transaction_token,
      'options': {
          'submit_for_settlement': AUTO_CHARGE,
          'three_d_secure': {
              'required': THREE_D_SECURE_REQUIRED
          }}})
    gateway_response = extract_gateway_response(result)
    txn = Transaction.objects.get_or_create(
        payment_method=payment_method,
        transaction_type=TransactionType.AUTH,
        amount=payment_method.total,
        gateway_response=gateway_response,
        token=result.transaction.id,
        is_success=result.is_success)[0]
    return txn

def charge(payment_method, amount=None, **client_kwargs):
    gateway = get_gateway(**client_kwargs)
    auth_transaction = payment_method.transactions.filter(
        transaction_type=TransactionType.AUTH).first()
    if not amount:
        amount = payment_method.total
    result = gateway.transaction.submit_for_settlement(
        transaction_id=auth_transaction.token,
        amount=amount)
    gateway_response = extract_gateway_response(result)

    txn = Transaction.objects.get_or_create(
        payment_method=payment_method,
        transaction_type=TransactionType.CHARGE,
        amount=amount,
        token=result.transaction.id,
        is_success=result.is_success,
        gateway_response=gateway_response)
    return txn

def void(payment_method, **client_kwargs):
    gateway = get_gateway(**client_kwargs)

    txn = Transaction.objects.get_or_create(
        payment_method=payment_method,
        transaction_type=TransactionType.VOID,
        amount=payment_method.total,
        gateway_response={},
        defaults={
            'token': str(uuid.uuid4()),
            'is_success': dummy_success()})[0]
    return txn

def refund(payment_method, amount=None, **client_kwargs):
    gateway = get_gateway(**client_kwargs)

    txn = Transaction.objects.get_or_create(
        payment_method=payment_method,
        transaction_type=TransactionType.REFUND,
        amount=amount,
        defaults={
            'token': str(uuid.uuid4()),
            'gateway_response': {},
            'is_success': dummy_success()})[0]
    return txn
