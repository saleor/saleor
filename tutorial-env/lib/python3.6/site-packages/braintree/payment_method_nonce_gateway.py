import braintree
from braintree.payment_method_nonce import PaymentMethodNonce

from braintree.error_result import ErrorResult
from braintree.exceptions.not_found_error import NotFoundError
from braintree.resource import Resource
from braintree.resource_collection import ResourceCollection
from braintree.successful_result import SuccessfulResult

class PaymentMethodNonceGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def create(self, payment_method_token):
        try:
            response = self.config.http().post(self.config.base_merchant_path() + "/payment_methods/" + payment_method_token + "/nonces")
            if "api_error_response" in response:
                return ErrorResult(self.gateway, response["api_error_response"])
            else:
                payment_method_nonce = self._parse_payment_method_nonce(response)
                return SuccessfulResult({"payment_method_nonce": payment_method_nonce})
        except NotFoundError:
            raise NotFoundError("payment method with token " + payment_method_token + " not found")

    def find(self, payment_method_nonce):
        try:
            response = self.config.http().get(self.config.base_merchant_path() + "/payment_method_nonces/" + payment_method_nonce)
            return self._parse_payment_method_nonce(response)
        except NotFoundError:
            raise NotFoundError("payment method nonce with id " + payment_method_nonce + " not found")

    def _parse_payment_method_nonce(self, response):
        return PaymentMethodNonce(self.gateway, response["payment_method_nonce"])
