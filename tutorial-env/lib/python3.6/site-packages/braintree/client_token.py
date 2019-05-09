import datetime
import json
import urllib
from braintree.configuration import Configuration
from braintree.signature_service import SignatureService
from braintree.util.crypto import Crypto
from braintree import exceptions

class ClientToken(object):

    @staticmethod
    def generate(params={}, gateway=None):
        if gateway is None:
            gateway = Configuration.gateway().client_token

        return gateway.generate(params)

    @staticmethod
    def generate_signature():
        return [
            "customer_id",
            "proxy_merchant_id",
            "version",
            "merchant_account_id",
            {"options": ["make_default", "verify_card", "fail_on_duplicate_payment_method"]}
        ]
