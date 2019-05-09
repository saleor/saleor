import braintree
from braintree.add_on import AddOn
from braintree.resource_collection import ResourceCollection

class AddOnGateway(object):
    def __init__(self, gateway):
        self.gateway = gateway
        self.config = gateway.config

    def all(self):
        response = self.config.http().get(self.config.base_merchant_path() + "/add_ons/")
        add_ons = {"add_on": response["add_ons"]}
        return [AddOn(self.gateway, item) for item in ResourceCollection._extract_as_array(add_ons, "add_on")]
