import braintree
from braintree.resource import Resource

class AndroidPayCard(Resource):
    """
    A class representing Braintree Android Pay card objects.
    """
    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        if hasattr(self, 'expired'):
            self.is_expired = self.expired

        if "subscriptions" in attributes:
            self.subscriptions = [braintree.subscription.Subscription(gateway, subscription) for subscription in self.subscriptions]

    @property
    def expiration_date(self):
        return self.expiration_month + "/" + self.expiration_year

    @property
    def last_4(self):
        return self.virtual_card_last_4

    @property
    def card_type(self):
        return self.virtual_card_type

