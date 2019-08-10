from typing import Dict
from django_countries import countries

from ...interface import GatewayConfig, GatewayResponse, PaymentData

from ..stripe.utils import get_amount_for_stripe

import urllib.request
from urllib.parse import urlencode
from urllib.request import urlopen
import hmac
import hashlib
import base64
import json
from django.utils.translation import pgettext_lazy

PAYREXX_API_URL = "https://api.payrexx.com/v1.0"

ZERO_DECIMAL_CURRENCIES = [
    "BIF",
    "CLP",
    "DJF",
    "GNF",
    "JPY",
    "KMF",
    "KRW",
    "MGA",
    "PYG",
    "RWF",
    "UGX",
    "VND",
    "VUV",
    "XAF",
    "XOF",
    "XPF",
    ]

CHECKOUT_DESCRIPTION = pgettext_lazy(
    "Payrexx payment gateway description", "Total payment"
)


def create_payrexx_link(payment_information: PaymentData, gateway_params: Dict):
    post_data = {
        "title": gateway_params.get('store_name'),
        "description": CHECKOUT_DESCRIPTION,
        "referenceId": payment_information.order_id,
        "purpose": pgettext_lazy(
            "Purpose for payrexx payment", "Payment for Order #{}")
        .format(payment_information.order_id),
        "amount": get_amount_for_stripe(
            payment_information.amount,
            payment_information.currency
            ),
        "currency": payment_information.currency,
        "preAuthorization": gateway_params.get('preAuth', 0),
        "reservation": 0,
        "name": gateway_params.get('name'),
        }
    instance = gateway_params['instance']

    data = urllib.parse.urlencode(post_data).encode('UTF-8')

    key = bytes(gateway_params['api_secret'], 'utf-8')

    dig = hmac.new(key=key,
                   msg=data, digestmod=hashlib.sha256).digest()
    post_data['ApiSignature'] = base64.b64encode(dig).decode()
    data = urlencode(post_data, quote_via=urllib.parse.quote).encode('UTF-8')

    result = urlopen(PAYREXX_API_URL + '/Invoice/?instance=' + instance, data)
    content = result.read().decode('UTF-8')
    response = json.loads(content)
    print(response)

    return response['data'][0]


def get_payrexx_link(payrexx_id, gateway_params: Dict):
    post_data = {}

    data = urllib.parse.urlencode(post_data).encode('UTF-8')

    key = bytes(gateway_params['api_secret'], 'utf-8')

    dig = hmac.new(key=key,
                   msg=data, digestmod=hashlib.sha256).digest()
    post_data['ApiSignature'] = base64.b64encode(dig).decode()
    post_data['instance'] = gateway_params['instance']

    data = urlencode(post_data, quote_via=urllib.parse.quote)

    print(PAYREXX_API_URL + '/Invoice/' + payrexx_id + '/')
    result = urlopen(PAYREXX_API_URL + '/Invoice/' + payrexx_id + '/?' + data)
    content = result.read().decode('UTF-8')
    response = json.loads(content)

    return response['data'][0]
