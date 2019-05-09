from decimal import Decimal
from braintree.attribute_getter import AttributeGetter

class DisbursementDetail(AttributeGetter):
    def __init__(self, attributes):
        AttributeGetter.__init__(self, attributes)

        if self.settlement_amount is not None:
            self.settlement_amount = Decimal(self.settlement_amount)
        if self.settlement_currency_exchange_rate is not None:
            self.settlement_currency_exchange_rate = Decimal(self.settlement_currency_exchange_rate)

    @property
    def is_valid(self):
        return self.disbursement_date is not None
