import braintree
from braintree.resource import Resource

class CoinbaseAccount(Resource):
    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        if "subscriptions" in attributes:
            self.subscriptions = [braintree.subscription.Subscription(gateway, subscription) for subscription in self.subscriptions]
