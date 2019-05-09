import braintree
from braintree.discount import Discount
from braintree.resource_collection import ResourceCollection

class DiscountGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def all(self):
        response = self.config.http().get(self.config.base_merchant_path() + "/discounts/")
        discounts = {"discount": response["discounts"]}
        return [Discount(self.gateway, item) for item in ResourceCollection._extract_as_array(discounts, "discount")]
