'''

'''
from .base import Base

class SubAccount(Base):
    '''

    '''
    business_name = None
    settlement_bank = None
    account_number = None
    percentage_charge = None

    primary_contact_email = None
    primary_contact_name = None
    primary_contact_phone = None
    settlement_schedule = None
  
    def __init__(self, business_name, settlement_bank, account_number, percentage_charge):
        super().__init__()
        self.business_name = business_name
        self.settlement_bank = settlement_bank
        self.account_number = account_number
        self.percentage_charge = percentage_charge

    def __str__(self):
        return "Sub Account for %s - %s" % (self.business_name, self.account_number)