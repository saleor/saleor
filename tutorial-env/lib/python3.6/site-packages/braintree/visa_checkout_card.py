import braintree
from braintree.address import Address
from braintree.resource import Resource
from braintree.credit_card_verification import CreditCardVerification

class VisaCheckoutCard(Resource):
    """
    A class representing Visa Checkout card
    """
    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)

        if "billing_address" in attributes:
            self.billing_address = Address(gateway, self.billing_address)
        else:
            self.billing_address = None

        if "subscriptions" in attributes:
            self.subscriptions = [braintree.subscription.Subscription(gateway, subscription) for subscription in self.subscriptions]

        if "verifications" in attributes:
            sorted_verifications = sorted(attributes["verifications"], key=lambda verification: verification["created_at"], reverse=True)
            if len(sorted_verifications) > 0:
                self.verification = CreditCardVerification(gateway, sorted_verifications[0])

    @property
    def expiration_date(self):
        return self.expiration_month + "/" + self.expiration_year

    @property
    def masked_number(self):
        return self.bin + "******" + self.last_4

