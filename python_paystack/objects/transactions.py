'''
transactions.py
'''
import math, uuid
from datetime import datetime
import validators
from .base import Base
from .errors import InvalidEmailError

class Transaction(Base):
    '''
    Transactions class
    '''
    reference = None
    amount = None
    email = None
    plan = None
    transaction_charge = None
    metadata = None
    card_locale = 'LOCAL'
    authorization_url = None
    authorization_code = None

    def __init__(self, amount: int, email):
        super().__init__()
        try:
            amount = int(amount)
        except ValueError:
            raise ValueError("Invalid amount. Amount(in kobo) should be an integer")

        else:
            if validators.email(email):
                self.amount = amount
                self.email = email
            else:
                raise InvalidEmailError

    def generate_reference_code(self):
        '''
        Generates a unique transaction reference code
        '''
        return uuid.uuid4()

    def full_transaction_cost(self, locale, local_cost, intl_cost):
        '''
        Adds on paystack transaction charges and returns updated cost

        Arguments:
        locale : Card location (LOCAL or INTERNATIONAL)
        '''
        if self.amount:

            if locale not in ('LOCAL', 'INTERNATIONAL'):
                raise ValueError("Invalid locale, locale should be 'LOCAL' or 'INTERNATIONAL'")

            else:
                locale_cost = {'LOCAL' : local_cost, 'INTERNATIONAL' : intl_cost}

                cost = self.amount / (1 - locale_cost[locale])

                if cost > 250000:
                    cost = (self.amount + 100)/ (1 - locale_cost[locale])

                paystack_charge = locale_cost[locale] * cost
                #Paystack_charge is capped at N2000
                if paystack_charge > 200000:
                    cost = self.amount + 200000

                return math.ceil(cost)

        else:
            raise AttributeError("Amount not set")
