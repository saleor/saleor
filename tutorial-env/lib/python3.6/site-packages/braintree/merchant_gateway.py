from braintree.error_result import ErrorResult
from braintree.resource import Resource
from braintree.resource_collection import ResourceCollection
from braintree.successful_result import SuccessfulResult
from braintree.exceptions.not_found_error import NotFoundError
from braintree.merchant import Merchant
from braintree.oauth_credentials import OAuthCredentials

class MerchantGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def create(self, params):
        return self.__create_merchant(params)

    def __create_merchant(self, params={}):
        response = self.config.http().post("/merchants/create_via_api", {
            "merchant": params
        })

        if "response" in response and "merchant" in response["response"]:
            return SuccessfulResult({
                "merchant": Merchant(self.gateway, response["response"]["merchant"]),
                "credentials": OAuthCredentials(self.gateway, response["response"]["credentials"])
            })
        else:
            return ErrorResult(self.gateway, response["api_error_response"])

