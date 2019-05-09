from braintree.util.http import Http
import braintree
from braintree.add_on import AddOn
from braintree.configuration import Configuration
from braintree.discount import Discount
from braintree.resource_collection import ResourceCollection
from braintree.resource import Resource

class Plan(Resource):

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        if "add_ons" in attributes:
            self.add_ons = [AddOn(gateway, add_on) for add_on in self.add_ons]
        if "discounts" in attributes:
            self.discounts = [Discount(gateway, discount) for discount in self.discounts]

    @staticmethod
    def all():
        return Configuration.gateway().plan.all()

