'''
Managers.py
'''

import json
import requests
import validators

from .objects.base import Manager
from .objects.customers import Customer
from .objects.errors import APIConnectionFailedError, URLValidationError
from .objects.filters import Filter
from .objects.plans import Plan
from .objects.transfers import Transfer
from .objects.transactions import Transaction
from .objects.subaccounts import SubAccount

from .paystack_config import PaystackConfig
from .mixins import CreatableMixin, RetrieveableMixin, UpdateableMixin

class Utils(Manager):
    '''

    '''

    def __init__(self):
        super().__init__()


    def resolve_card_bin(self, card_bin, endpoint='/decision/bin/'):
        '''

        '''
        card_bin = card_bin[:6]
        url = self.PAYSTACK_URL + endpoint + card_bin
        headers, _ = self.build_request_args()

        response = requests.get(url, headers=headers)
        content = self.parse_response_content(response.content)

        status, message = self.get_content_status(content)
        if status:
            return content['data']
        
    def get_banks(self, endpoint='/bank'):
        '''

        '''
        url = self.PAYSTACK_URL + endpoint
        headers, _ = self.build_request_args()

        response = requests.get(url, headers=headers)
        content = self.parse_response_content(response.content)

        status, message = self.get_content_status(content)
        if status:
            return content['data']

    def resolve_bvn(self, bvn, endpoint='/bank/resolve_bvn/'):
        url = self.PAYSTACK_URL + endpoint + bvn
        headers, _ = self.build_request_args()

        response = requests.get(url, headers=headers)
        content = self.parse_response_content(response.content)

        status, message = self.get_content_status(content)
        if status:
            return content['data']
    
    def resolve_account_number(self, account_number, bank_code, endpoint='/bank/resolve'):
        '''
        '''        
        params = "?account_number=%s&bank_code=%s" % (account_number, bank_code)
        url = self.PAYSTACK_URL + endpoint + params

        headers, _ = self.build_request_args()

        response = requests.get(url, headers=headers)
        content = self.parse_response_content(response.content)

        status, message = self.get_content_status(content)
        if status:
            return content['data']
        


class TransactionsManager(RetrieveableMixin, Manager):
    '''
    TransactionsManager class that handles every part of a transaction

    Attributes:
    amount : Transaction cost
    email : Buyer's email
    reference
    authorization_url
    card_locale : Card location for application of paystack charges
    '''

    LOCAL_COST = PaystackConfig.LOCAL_COST
    INTL_COST = PaystackConfig.INTL_COST
    PASS_ON_TRANSACTION_COST = PaystackConfig.PASS_ON_TRANSACTION_COST

    _endpoint = '/transaction'
    _object_class = Transaction


    def __init__(self, endpoint='/transaction'):
        super().__init__()
        self._endpoint = endpoint


    def initialize_transaction(self, method, transaction: Transaction,
                               callback_url='', endpoint='/initialize'):
        '''
        Initializes a paystack transaction.
        Returns an authorization url which points to a paystack form if the method is standard.
        Returns a dict containing transaction information if the method is inline or inline embed

        Arguments:
        method : Specifies whether to use paystack inline, standard or inline embed
        callback_url : URL paystack redirects to after a user enters their card details
        plan_code : Payment plan code
        endpoint : Paystack API endpoint for intializing transactions
        '''

        method = method.upper()
        if method not in ('STANDARD', 'INLINE', 'INLINE EMBED'):
            raise ValueError("method argument should be STANDARD, INLINE or INLINE EMBED")

        if self.PASS_ON_TRANSACTION_COST:
            transaction.amount = transaction.full_transaction_cost(transaction.card_locale,
                                                                   self.LOCAL_COST, self.INTL_COST)

        data = json.JSONDecoder().decode(transaction.to_json())

        if callback_url:
            if validators.url(callback_url):
                data['callback_url'] = callback_url

            else:
                raise URLValidationError

        if method in ('INLINE', 'INLINE EMBED'):
            data['key'] = PaystackConfig.PUBLIC_KEY
            return data

        headers, data = self.build_request_args(data)

        url = self.PAYSTACK_URL + self._endpoint + endpoint
        response = requests.post(url, headers=headers, data=data)
        content = response.content
        content = self.parse_response_content(content)


        status, message = self.get_content_status(content)

        #status = True for a successful connection
        if status:
            data = json.dumps(content['data'])
            transaction = Transaction.from_json(data)
            return transaction
        else:
            #Connection failed
            raise APIConnectionFailedError(message)

    def verify_transaction(self, transaction_reference : str, endpoint='/verify/'):
        '''
        Verifies a payment using the transaction reference.

        Arguments:
        endpoint : Paystack API endpoint for verifying transactions
        '''

        endpoint += transaction_reference
        url = self.PAYSTACK_URL + self._endpoint + endpoint

        headers, _ = self.build_request_args()
        response = requests.get(url, headers=headers)
        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            data_dict = content['data']
            data = json.dumps(content['data'])
            transaction = Transaction.from_json(data)
            transaction.email = data_dict['customer']['email']
            transaction.authorization_code = data_dict['authorization']['authorization_code']
            return transaction
        else:
            raise APIConnectionFailedError(message)

    def charge_authorization(self, transaction: Transaction, endpoint='/charge_authorization'):
        data = transaction.to_json()
        headers, _ = self.build_request_args()

        response = requests.post(self.PAYSTACK_URL + self._endpoint + endpoint,
                                 headers=headers, data=data)
        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        #status = True for a successful connection
        if status:
            return content['data']
        else:
            #Connection failed
            raise APIConnectionFailedError(message)
    
    def get_transactions(self,filter=None):
        '''
        Returns all transactions with the option of filtering by the transation status
        Transaction statuses include : 'failed', 'success', 'abandoned'
        '''
        url = self.PAYSTACK_URL + self._endpoint
        if filter:
            url += '/?status={}'.format(filter)
        
        config = PaystackConfig()
        headers = {
            'Authorization':'Bearer '+config.SECRET_KEY
        }        
        r = requests.get(url,headers=headers)

        return r.json()

    def get_total_transactions(self):
        '''
        Get total amount recieved from transactions
        '''
        headers, _ = self.build_request_args()
        url = self.PAYSTACK_URL + self._endpoint
        url += '/totals'
        response = requests.get(url, headers=headers)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)
    

    def filter_transactions(self, amount_range: range, transactions):
        '''
        Returns all transactions with amounts in the given amount_range
        '''
        results = []
        for transaction in transactions:
            if Filter.filter_amount(amount_range, transaction):
                results.append(transaction)

        return results
    

class CustomersManager(CreatableMixin, RetrieveableMixin, UpdateableMixin, Manager):
    '''
    CustomersManager class which handels actions for Paystack Customers

    Attributes :
    _endpoint : Paystack API endpoint for 'customers' actions

    '''
    _endpoint = '/customer'
    _object_class = Customer

    def __init__(self):
        super().__init__()
 

    def set_risk_action(self, risk_action, customer: Customer):
        '''
        Method for either blacklisting or whitelisting a customer

        Arguments :
        risk_action : (allow or deny)
        customer_id : Customer id

        '''

        if not isinstance(customer, Customer):
            raise TypeError("customer argument should be of type 'Customer' ")

        endpoint = '/set_risk_action'

        if risk_action not in ('allow', 'deny'):
            raise ValueError("Invalid risk action")

        else:
            data = {'customer' : customer.id, 'risk_action' : risk_action}
            headers, data = self.build_request_args(data)
            url = "%s%s" % (self.PAYSTACK_URL + self._endpoint, endpoint)

            response = requests.post(url, headers=headers, data=data)

            content = response.content
            content = self.parse_response_content(content)

            status, message = self.get_content_status(content)

            if status:
                data = json.dumps(content['data'])
                return Customer.from_json(data)
            else:
                raise APIConnectionFailedError(message)

    def deactive_authorization(self, authorization_code):
        '''
        Method to deactivate an existing authorization

        Arguments :
        authorization_code : Code for the transaction to be deactivated

        '''
        data = {'authorization_code' : authorization_code}
        headers, data = self.build_request_args(data)

        url = "%s/deactivate_authorization" % (self.PAYSTACK_URL + self._endpoint)
        response = requests.post(url, headers=headers, data=data)

        content = response.content
        content = self.parse_response_content(content)

        status, message = self.get_content_status(content)

        if status:
            return content['data']
        else:
            raise APIConnectionFailedError(message)




class PlanManager(CreatableMixin, RetrieveableMixin, UpdateableMixin, Manager):
    '''
    Plan Manager class
    '''

    _endpoint = '/plan'
    _object_class = Plan

    def __init__(self, endpoint='/plan'):
        super().__init__()
        self._endpoint = endpoint

    


class TransfersManager(CreatableMixin, RetrieveableMixin, UpdateableMixin, Manager):
    '''
    TransfersManager class
    '''

    _endpoint = '/transfer'
    _object_class = Transfer

    def __init__(self, endpoint='/transfer'):
        super().__init__()
        self._endpoint = endpoint


    def finalize_transfer(self, transfer_id, otp):
        '''
        Method for finalizing transfers
        '''
        transfer_id = str(transfer_id)
        otp = str(otp)

        data = {'transfer_code' : transfer_id, 'otp' : otp}
        headers, data = self.build_request_args(data)

        url = self.PAYSTACK_URL + self._endpoint
        url += '/finalize_transfer'
        response = requests.post(url, headers=headers, data=data)
        content = response.content
        content = self.parse_response_content(content)


        status, message = self.get_content_status(content)

        if status:
            data = content['data']
            return data

        else:
            #Connection failed
            raise APIConnectionFailedError(message)




class SubAccountManager(CreatableMixin, RetrieveableMixin, UpdateableMixin, Manager):
    '''

    '''
    _endpoint = None
    _object_class = SubAccount

    def __init__(self, endpoint='/subaccount'):
        super().__init__()
        self._endpoint = endpoint

