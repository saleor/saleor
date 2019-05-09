import braintree
from braintree.resource import Resource

class AmexExpressCheckoutCard(Resource):
    """
    A class representing Braintree Amex Express Checkout card objects.
    """
    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

        if "subscriptions" in attributes:
            self.subscriptions = [braintree.subscription.Subscription(gateway, subscription) for subscription in self.subscriptions]

    @property
    def expiration_date(self):
        return self.expiration_month + "/" + self.expiration_year

