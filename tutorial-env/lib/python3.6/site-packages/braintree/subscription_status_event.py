from decimal import Decimal
from braintree.resource import Resource

class SubscriptionStatusEvent(Resource):
    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

        self.balance = Decimal(self.balance)
        self.price = Decimal(self.price)
