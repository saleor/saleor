import braintree
import warnings
from braintree.resource import Resource
from braintree.address import Address
from braintree.configuration import Configuration
from braintree.transparent_redirect import TransparentRedirect
from braintree.credit_card_verification import CreditCardVerification

class CreditCard(Resource):
    """
    A class representing Braintree CreditCard objects.

    An example of creating an credit card with all available fields::

        result = braintree.CreditCard.create({
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
        })

        print(result.credit_card.token)
        print(result.credit_card.masked_number)

    For more information on CreditCards, see https://developers.braintreepayments.com/reference/request/credit-card/create/python

    """
    class CardType(object):
        """
        Contants representing the type of the credit card.  Available types are:

        * Braintree.CreditCard.AmEx
        * Braintree.CreditCard.CarteBlanche
        * Braintree.CreditCard.ChinaUnionPay
        * Braintree.CreditCard.DinersClubInternational
        * Braintree.CreditCard.Discover
        * Braintree.CreditCard.Electron
        * Braintree.CreditCard.Elo
        * Braintree.CreditCard.JCB
        * Braintree.CreditCard.Laser
        * Braintree.CreditCard.UK_Maestro
        * Braintree.CreditCard.Maestro
        * Braintree.CreditCard.MasterCard
        * Braintree.CreditCard.Solo
        * Braintree.CreditCard.Switch
        * Braintree.CreditCard.Visa
        * Braintree.CreditCard.Unknown
        """

        AmEx = "American Express"
        CarteBlanche = "Carte Blanche"
        ChinaUnionPay = "China UnionPay"
        DinersClubInternational = "Diners Club"
        Discover = "Discover"
        Electron = "Electron"
        Elo = "Elo"
        JCB = "JCB"
        Laser = "Laser"
        UK_Maestro = "UK Maestro"
        Maestro = "Maestro"
        MasterCard = "MasterCard"
        Solo = "Solo"
        Switch = "Switch"
        Visa = "Visa"
        Unknown = "Unknown"

    class CustomerLocation(object):
        """
        Contants representing the issuer location of the credit card.  Available locations are:

        * braintree.CreditCard.CustomerLocation.International
        * braintree.CreditCard.CustomerLocation.US
        """

        International = "international"
        US = "us"

    class CardTypeIndicator(object):
        """
        Constants representing the three states for the card type indicator attributes

        * braintree.CreditCard.CardTypeIndicator.Yes
        * braintree.CreditCard.CardTypeIndicator.No
        * braintree.CreditCard.CardTypeIndicator.Unknown
        """
        Yes = "Yes"
        No = "No"
        Unknown = "Unknown"

    Commercial = DurbinRegulated = Debit = Healthcare = \
            CountryOfIssuance = IssuingBank = Payroll = Prepaid = ProductId = CardTypeIndicator

    @staticmethod
    def confirm_transparent_redirect(query_string):
        """
        Confirms a transparent redirect request. It expects the query string from the
        redirect request. The query string should _not_ include the leading "?" character. ::

            result = braintree.CreditCard.confirm_transparent_redirect_request("foo=bar&id=12345")
        """

        warnings.warn("Please use TransparentRedirect.confirm instead", DeprecationWarning)
        return Configuration.gateway().credit_card.confirm_transparent_redirect(query_string)

    @staticmethod
    def create(params={}):
        """
        Create a CreditCard.

        A number and expiration_date are required. ::

            result = braintree.CreditCard.create({
                "number": "4111111111111111",
                "expiration_date": "12/2012"
            })

        """

        return Configuration.gateway().credit_card.create(params)

    @staticmethod
    def update(credit_card_token, params={}):
        """
        Update an existing CreditCard

        By credit_card_id.  The params are similar to create::

            result = braintree.CreditCard.update("my_credit_card_id", {
                "cardholder_name": "John Doe"
            })

        """

        return Configuration.gateway().credit_card.update(credit_card_token, params)

    @staticmethod
    def delete(credit_card_token):
        """
        Delete a credit card

        Given a credit_card_id::

            result = braintree.CreditCard.delete("my_credit_card_id")

        """

        return Configuration.gateway().credit_card.delete(credit_card_token)

    @staticmethod
    def expired():
        """ Return a collection of expired credit cards. """
        return Configuration.gateway().credit_card.expired()

    @staticmethod
    def expiring_between(start_date, end_date):
        """ Return a collection of credit cards expiring between the given dates. """
        return Configuration.gateway().credit_card.expiring_between(start_date, end_date)

    @staticmethod
    def find(credit_card_token):
        """
        Find a credit card, given a credit_card_id. This does not return
        a result object. This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided
        credit_card_id is not found. ::

            credit_card = braintree.CreditCard.find("my_credit_card_token")
        """
        return Configuration.gateway().credit_card.find(credit_card_token)

    @staticmethod
    def forward(credit_card_token, receiving_merchant_id):
        """
        This method has been deprecated. Please consider the Grant API instead.
        """

        return Configuration.gateway().credit_card.forward(credit_card_token, receiving_merchant_id)

    @staticmethod
    def from_nonce(nonce):
        """
        Convert a payment method nonce into a CreditCard. This does not return
        a result object. This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided
        credit_card_id is not found. ::

            credit_card = braintree.CreditCard.from_nonce("my_payment_method_nonce")
        """
        return Configuration.gateway().credit_card.from_nonce(nonce)

    @staticmethod
    def create_signature():
        return CreditCard.signature("create")

    @staticmethod
    def update_signature():
        return CreditCard.signature("update")

    @staticmethod
    def signature(type):
        billing_address_params = [
            "company",
            "country_code_alpha2",
            "country_code_alpha3",
            "country_code_numeric",
            "country_name",
            "extended_address",
            "first_name",
            "last_name",
            "locality",
            "postal_code",
            "region",
            "street_address"
        ]

        options = [
            "make_default",
            "verification_merchant_account_id",
            "verify_card",
            "verification_amount",
            "venmo_sdk_session",
            "fail_on_duplicate_payment_method",
            {
                "adyen":[
                    "overwrite_brand",
                    "selected_brand"
                ]
            }
        ]

        signature = [
            "billing_address_id",
            "cardholder_name",
            "cvv",
            "expiration_date",
            "expiration_month",
            "expiration_year",
            "device_session_id",
            "fraud_merchant_id",
            "number",
            "token",
            "venmo_sdk_payment_method_code",
            "device_data",
            "payment_method_nonce",
            {
                "billing_address": billing_address_params
            },
            {
                "options": options
            }
        ]

        if type == "create":
            signature.append("customer_id")
        elif type == "update":
            billing_address_params.append({"options": ["update_existing"]})
        elif type == "update_via_customer":
            options.append("update_existing_token")
            billing_address_params.append({"options": ["update_existing"]})
        else:
            raise AttributeError

        return signature

    @staticmethod
    def transparent_redirect_create_url():
        """
        Returns the url to use for creating CreditCards through transparent redirect.
        """
        warnings.warn("Please use TransparentRedirect.url instead", DeprecationWarning)
        return Configuration.gateway().credit_card.transparent_redirect_create_url()

    @staticmethod
    def tr_data_for_create(tr_data, redirect_url):
        """
        Builds tr_data for CreditCard creation.
        """

        return Configuration.gateway().credit_card.tr_data_for_create(tr_data, redirect_url)

    @staticmethod
    def tr_data_for_update(tr_data, redirect_url):
        """
        Builds tr_data for CreditCard updating.
        """

        return Configuration.gateway().credit_card.tr_data_for_update(tr_data, redirect_url)

    @staticmethod
    def transparent_redirect_update_url():
        """
        Returns the url to be used for updating CreditCards through transparent redirect.
        """
        warnings.warn("Please use TransparentRedirect.url instead", DeprecationWarning)
        return Configuration.gateway().credit_card.transparent_redirect_update_url()

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        self.is_expired = self.expired
        if "billing_address" in attributes:
            self.billing_address = Address(gateway, self.billing_address)
        else:
            self.billing_address = None

        if "subscriptions" in attributes:
            self.subscriptions = [braintree.subscription.Subscription(gateway, subscription) for subscription in self.subscriptions]

        if "verifications" in attributes:
            sorted_verifications = sorted(attributes["verifications"], key=lambda verification: verification["created_at"], reverse=True)
            if len(sorted_verifications) > 0:
                self.verification = CreditCardVerification(gateway, sorted_verifications[0])

    @property
    def expiration_date(self):
        return self.expiration_month + "/" + self.expiration_year

    @property
    def masked_number(self):
        """
        Returns the masked number of the CreditCard.
        """
        return self.bin + "******" + self.last_4

