from decimal import Decimal
from braintree.attribute_getter import AttributeGetter

class AuthorizationAdjustment(AttributeGetter):
    def __init__(self, attributes):
        AttributeGetter.__init__(self, attributes)
        if hasattr(self, 'amount') and self.amount is not None:
            self.amount = Decimal(self.amount)
