'''
transfers.py
'''
from forex_python.converter import CurrencyCodes
from .base import Base

class Transfer(Base):
    '''
    Transfer class
    '''
    source = None
    amount = None
    currency = None
    reason = None
    recipient = None
    status = None
    id = None
    transfer_code = None
    otp = None

    def __init__(self, amount, recipient, source = 'balance', reason='', currency='NGN'):
        super().__init__()
        try:
            amount = int(amount)
        except ValueError:
            raise ValueError("Invalid amount. Amount(in kobo) should be an integer")

        if not CurrencyCodes().get_symbol(currency.upper()):
            raise ValueError("Invalid currency supplied")

        self.source = source
        self.amount = amount
        self.recipient = recipient
        self.reason = reason
        self.currency = currency

    def __str__(self):
        value = "Transfer of %s %s from %s to %s %s" % (self.amount, self.currency,
                                                        self.source, self.recipient, self.reason)

        return value
