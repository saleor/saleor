from decimal import Decimal
from braintree.attribute_getter import AttributeGetter

class TransactionDetails(AttributeGetter):
    def __init__(self, attributes):
        AttributeGetter.__init__(self, attributes)

        if self.amount is not None:
            self.amount = Decimal(self.amount)
