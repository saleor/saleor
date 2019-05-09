import warnings
from braintree.util.http import Http
from braintree.successful_result import SuccessfulResult
from braintree.error_result import ErrorResult
from braintree.resource import Resource
from braintree.apple_pay_card import ApplePayCard
from braintree.android_pay_card import AndroidPayCard
from braintree.amex_express_checkout_card import AmexExpressCheckoutCard
from braintree.credit_card import CreditCard
from braintree.paypal_account import PayPalAccount
from braintree.europe_bank_account import EuropeBankAccount
from braintree.us_bank_account import UsBankAccount
from braintree.coinbase_account import CoinbaseAccount
from braintree.venmo_account import VenmoAccount
from braintree.visa_checkout_card import VisaCheckoutCard
from braintree.masterpass_card import MasterpassCard
from braintree.address import Address
from braintree.configuration import Configuration
from braintree.ids_search import IdsSearch
from braintree.exceptions.not_found_error import NotFoundError
from braintree.resource_collection import ResourceCollection
from braintree.transparent_redirect import TransparentRedirect
from braintree.samsung_pay_card import SamsungPayCard

class Customer(Resource):
    """
    A class representing a customer.

    An example of creating an customer with all available fields::

        result = braintree.Customer.create({
            "id": "my_customer_id",
            "company": "Some company",
            "email": "john.doe@example.com",
            "fax": "123-555-1212",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "123-555-1221",
            "website": "http://www.example.com",
            "credit_card": {
                "cardholder_name": "John Doe",
                "cvv": "123",
                "expiration_date": "12/2012",
                "number": "4111111111111111",
                "token": "my_token",
                "billing_address": {
                    "first_name": "John",
                    "last_name": "Doe",
                    "company": "Braintree",
                    "street_address": "111 First Street",
                    "extended_address": "Unit 1",
                    "locality": "Chicago",
                    "postal_code": "60606",
                    "region": "IL",
                    "country_name": "United States of America"
                },
                "options": {
                    "verify_card": True,
                    "verification_amount": "2.00"
                }
            },
            "custom_fields": {
                "my_key": "some value"
            }
        })

        print(result.customer.id)
        print(result.customer.first_name)

    For more information on Customers, see https://developers.braintreepayments.com/reference/request/customer/create/python

    """

    def __repr__(self):
        detail_list = [
            "id",
            "company",
            "created_at",
            "email",
            "fax",
            "first_name",
            "last_name",
            "merchant_id",
            "phone",
            "updated_at",
            "website",
        ]

        return super(Customer, self).__repr__(detail_list)

    @staticmethod
    def all():
        """ Return a collection of all customers. """
        return Configuration.gateway().customer.all()

    @staticmethod
    def confirm_transparent_redirect(query_string):
        """
        Confirms a transparent redirect request.  It expects the query string from the
        redirect request.  The query string should _not_ include the leading "?" character. ::

            result = braintree.Customer.confirm_transparent_redirect_request("foo=bar&id=12345")
        """

        warnings.warn("Please use TransparentRedirect.confirm instead", DeprecationWarning)
        return Configuration.gateway().customer.confirm_transparent_redirect(query_string)

    @staticmethod
    def create(params={}):
        """
        Create a Customer

        No field is required::

            result = braintree.Customer.create({
                "company": "Some company",
                "first_name": "John"
            })

        """

        return Configuration.gateway().customer.create(params)

    @staticmethod
    def delete(customer_id):
        """
        Delete a customer

        Given a customer_id::

            result = braintree.Customer.delete("my_customer_id")

        """

        return Configuration.gateway().customer.delete(customer_id)

    @staticmethod
    def find(customer_id, association_filter_id=None):
        """
        Find an customer, given a customer_id.  This does not return a result
        object.  This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided customer_id
        is not found. ::

            customer = braintree.Customer.find("my_customer_id")
        """

        return Configuration.gateway().customer.find(customer_id, association_filter_id)

    @staticmethod
    def search(*query):
        return Configuration.gateway().customer.search(*query)

    @staticmethod
    def tr_data_for_create(tr_data, redirect_url):
        """ Builds tr_data for creating a Customer. """

        return Configuration.gateway().customer.tr_data_for_create(tr_data, redirect_url)

    @staticmethod
    def tr_data_for_update(tr_data, redirect_url):
        """ Builds tr_data for updating a Customer. """

        return Configuration.gateway().customer.tr_data_for_update(tr_data, redirect_url)

    @staticmethod
    def transparent_redirect_create_url():
        """ Returns the url to use for creating Customers through transparent redirect. """

        warnings.warn("Please use TransparentRedirect.url instead", DeprecationWarning)
        return Configuration.gateway().customer.transparent_redirect_create_url()

    @staticmethod
    def transparent_redirect_update_url():
        """ Returns the url to use for updating Customers through transparent redirect. """

        warnings.warn("Please use TransparentRedirect.url instead", DeprecationWarning)
        return Configuration.gateway().customer.transparent_redirect_update_url()

    @staticmethod
    def update(customer_id, params={}):
        """
        Update an existing Customer

        By customer_id. The params are similar to create::

            result = braintree.Customer.update("my_customer_id", {
                "last_name": "Smith"
            })

        """

        return Configuration.gateway().customer.update(customer_id, params)

    @staticmethod
    def create_signature():
        return [
            "company", "email", "fax", "first_name", "id", "last_name", "phone", "website", "device_data", "device_session_id", "fraud_merchant_id", "payment_method_nonce",
            {"risk_data": ["customer_browser", "customer_ip"]},
            {"credit_card": CreditCard.create_signature()},
            {"custom_fields": ["__any_key__"]},
            {"options": [{"paypal": [
                "payee_email",
                "order_id",
                "custom_field",
                "description",
                "amount",
                { "shipping": Address.create_signature() }
            ]}]},
        ]

    @staticmethod
    def update_signature():
        return [
            "company", "email", "fax", "first_name", "id", "last_name", "phone", "website", "device_data", "device_session_id", "fraud_merchant_id", "payment_method_nonce", "default_payment_method_token",
            {"credit_card": CreditCard.signature("update_via_customer")},
            {"custom_fields": ["__any_key__"]},
            {"options": [{"paypal": [
                "payee_email",
                "order_id",
                "custom_field",
                "description",
                "amount",
                { "shipping": Address.create_signature() }
            ]}]},
        ]

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        self.payment_methods = []

        if "credit_cards" in attributes:
            self.credit_cards = [CreditCard(gateway, credit_card) for credit_card in self.credit_cards]
            self.payment_methods += self.credit_cards
        if "addresses" in attributes:
            self.addresses = [Address(gateway, address) for address in self.addresses]

        if "paypal_accounts" in attributes:
            self.paypal_accounts  = [PayPalAccount(gateway, paypal_account) for paypal_account in self.paypal_accounts]
            self.payment_methods += self.paypal_accounts

        if "apple_pay_cards" in attributes:
            self.apple_pay_cards  = [ApplePayCard(gateway, apple_pay_card) for apple_pay_card in self.apple_pay_cards]
            self.payment_methods += self.apple_pay_cards

        if "android_pay_cards" in attributes:
            self.android_pay_cards  = [AndroidPayCard(gateway, android_pay_card) for android_pay_card in self.android_pay_cards]
            self.payment_methods += self.android_pay_cards

        if "amex_express_checkout_cards" in attributes:
            self.amex_express_checkout_cards  = [AmexExpressCheckoutCard(gateway, amex_express_checkout_card) for amex_express_checkout_card in self.amex_express_checkout_cards]
            self.payment_methods += self.amex_express_checkout_cards

        if "europe_bank_accounts" in attributes:
            self.europe_bank_accounts = [EuropeBankAccount(gateway, europe_bank_account) for europe_bank_account in self.europe_bank_accounts]
            self.payment_methods += self.europe_bank_accounts

        if "coinbase_accounts" in attributes:
            self.coinbase_accounts = [CoinbaseAccount(gateway, coinbase_account) for coinbase_account in self.coinbase_accounts]
            self.payment_methods += self.coinbase_accounts

        if "venmo_accounts" in attributes:
            self.venmo_accounts = [VenmoAccount(gateway, venmo_account) for venmo_account in self.venmo_accounts]
            self.payment_methods += self.venmo_accounts

        if "us_bank_accounts" in attributes:
            self.us_bank_accounts = [UsBankAccount(gateway, us_bank_account) for us_bank_account in self.us_bank_accounts]
            self.payment_methods += self.us_bank_accounts

        if "visa_checkout_cards" in attributes:
            self.visa_checkout_cards = [VisaCheckoutCard(gateway, visa_checkout_card) for visa_checkout_card in self.visa_checkout_cards]
            self.payment_methods += self.visa_checkout_cards

        if "masterpass_cards" in attributes:
            self.masterpass_cards = [MasterpassCard(gateway, masterpass_card) for masterpass_card in self.masterpass_cards]
            self.payment_methods += self.masterpass_cards

        if "samsung_pay_cards" in attributes:
            self.samsung_pay_cards = [SamsungPayCard(gateway, samsung_pay_card) for samsung_pay_card in self.samsung_pay_cards]
            self.payment_methods += self.samsung_pay_cards
