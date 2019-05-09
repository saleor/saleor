from decimal import Decimal
from braintree.resource import Resource

class StatusEvent(Resource):
    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

        self.amount = Decimal(self.amount)
