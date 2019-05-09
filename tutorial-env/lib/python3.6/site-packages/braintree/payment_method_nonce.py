import braintree
from braintree.resource import Resource
from braintree.configuration import Configuration
from braintree.three_d_secure_info import ThreeDSecureInfo
from braintree.bin_data import BinData

class PaymentMethodNonce(Resource):
    @staticmethod
    def create(payment_method_token):
        return Configuration.gateway().payment_method_nonce.create(payment_method_token)

    @staticmethod
    def find(payment_method_nonce):
        return Configuration.gateway().payment_method_nonce.find(payment_method_nonce)

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

        if "three_d_secure_info" in attributes and not attributes["three_d_secure_info"] is None:
            self.three_d_secure_info = ThreeDSecureInfo(attributes["three_d_secure_info"])
        else:
            self.three_d_secure_info = None

        if "bin_data" in attributes and not attributes["bin_data"] is None:
            self.bin_data = BinData(attributes["bin_data"])
        else:
            self.bin_data = None
