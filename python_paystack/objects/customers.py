'''
customers.py
'''

import validators
from .errors import InvalidEmailError
from .base import Base

class Customer(Base):
    '''
    Customer class that holds customer properties
    '''

    phone = None
    email = None
    customer_code = None
    risk_action = None
    first_name = None
    last_name = None
    id = None
    metadata = None

    def __init__(self, email, first_name=None, last_name=None,
                 phone=None, risk_action=None, id=None, metadata=None):
        super().__init__()
        if validators.email(email):
            self.email = email
            self.first_name = first_name
            self.last_name = last_name
            self.phone = phone
            self.risk_action = risk_action
            # self.id = id
        else:
            raise InvalidEmailError

        if metadata and not isinstance(metadata, dict):
            raise TypeError("meta argument should be a dict")
        else:
            self.metadata = metadata

    def __str__(self):
        value = self.email
        if self.first_name:
            value += ' %s' % (self.first_name)
        return value
