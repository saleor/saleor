import braintree
from braintree.resource import Resource

class ApplePayCard(Resource):
    """
    A class representing Braintree Apple Pay card objects.
    """
    class CardType(object):
        """
        Contants representing the type of the credit card.  Available types are:

        * Braintree.ApplePayCard.AmEx
        * Braintree.ApplePayCard.MasterCard
        * Braintree.ApplePayCard.Visa
        """

        AmEx = "Apple Pay - American Express"
        MasterCard = "Apple Pay - MasterCard"
        Visa = "Apple Pay - Visa"

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        if hasattr(self, 'expired'):
            self.is_expired = self.expired

        if "subscriptions" in attributes:
            self.subscriptions = [braintree.subscription.Subscription(gateway, subscription) for subscription in self.subscriptions]

    @property
    def expiration_date(self):
        return self.expiration_month + "/" + self.expiration_year

