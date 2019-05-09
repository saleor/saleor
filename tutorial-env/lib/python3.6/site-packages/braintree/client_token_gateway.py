import braintree
from braintree.resource import Resource
from braintree.client_token import ClientToken
from braintree import exceptions

class ClientTokenGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config


    def generate(self, params={}):
        if "options" in params and not "customer_id" in params:
            for option in ["verify_card", "make_default", "fail_on_duplicate_payment_method"]:
                if option in params["options"]:
                    raise exceptions.InvalidSignatureError("cannot specify %s without a customer_id" % option)

        if "version" not in params:
            params["version"] = 2

        Resource.verify_keys(params, ClientToken.generate_signature())
        params = {'client_token': params}

        response = self.config.http().post(self.config.base_merchant_path() + "/client_token", params)

        if "client_token" in response:
            return response["client_token"]["value"]
        else:
            raise ValueError(response["api_error_response"]["message"])
