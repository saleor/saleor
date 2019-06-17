'''
plans.py
'''
from forex_python.converter import CurrencyCodes
from .base import Base

class Plan(Base):
    '''
    Plan class for making payment plans
    '''

    interval = None
    name = None
    amount = None
    plan_code = None
    currency = None
    id = None
    send_sms = True
    send_invoices = True
    description = None
    __interval_values = ('hourly', 'daily', 'weekly', 'monthly', 'annually')

    def __init__(self, name, interval, amount, currency='NGN', plan_code=None,
                 id=None, send_sms=None, send_invoices=None, description=None):
        super().__init__()
        #Check if currency supplied is valid
        if not CurrencyCodes().get_symbol(currency.upper()):
            raise ValueError("Invalid currency supplied")

        if interval.lower() not in self.__interval_values:
            raise ValueError("Interval should be one of 'hourly',"
                             "'daily', 'weekly', 'monthly','annually'"
                            )

        try:
            amount = int(amount)
        except ValueError:
            raise ValueError("Invalid amount")
        else:
            self.interval = interval.lower()
            self.name = name
            self.interval = interval
            self.amount = amount
            self.currency = currency
            self.plan_code = plan_code
            self.id = id
            self.send_sms = send_sms
            self.send_invoices = send_invoices
            self.description = description

    def __str__(self):
        return "%s plan" % self.name
