from braintree.resource import Resource
from braintree.merchant_account import MerchantAccount

class Merchant(Resource):
    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

        if "merchant_accounts" in attributes:
            self.merchant_accounts = [MerchantAccount(gateway, ma) for ma in attributes.get("merchant_accounts")]
