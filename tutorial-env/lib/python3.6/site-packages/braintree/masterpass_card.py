import braintree
from braintree.address import Address
from braintree.resource import Resource

class MasterpassCard(Resource):
    """
    A class representing Masterpass card
    """
    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

        if "billing_address" in attributes:
            self.billing_address = Address(gateway, self.billing_address)
        else:
            self.billing_address = None

        if "subscriptions" in attributes:
            self.subscriptions = [braintree.subscription.Subscription(gateway, subscription) for subscription in self.subscriptions]

    @property
    def expiration_date(self):
        return self.expiration_month + "/" + self.expiration_year

    @property
    def masked_number(self):
        return self.bin + "******" + self.last_4

