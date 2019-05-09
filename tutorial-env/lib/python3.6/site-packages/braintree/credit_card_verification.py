from decimal import Decimal
from braintree.attribute_getter import AttributeGetter
from braintree.configuration import Configuration
from braintree.risk_data import RiskData
from braintree.resource import Resource

class CreditCardVerification(AttributeGetter):

    class Status(object):
        """
        Constants representing transaction statuses. Available statuses are:

        * braintree.CreditCardVerification.Status.Failed
        * braintree.CreditCardVerification.Status.GatewayRejected
        * braintree.CreditCardVerification.Status.ProcessorDeclined
        * braintree.CreditCardVerification.Status.Unrecognized
        * braintree.CreditCardVerification.Status.Verified
        """

        Failed                 = "failed"
        GatewayRejected        = "gateway_rejected"
        ProcessorDeclined      = "processor_declined"
        Unrecognized           = "unrecognized"
        Verified               = "verified"

    def __init__(self, gateway, attributes):
        AttributeGetter.__init__(self, attributes)

        if "amount" in attributes and self.amount:
            self.amount = Decimal(self.amount)
        else:
            self.amount = None

        if "currency_iso_code" not in attributes:
            self.currency_iso_code = None

        if "processor_response_code" not in attributes:
            self.processor_response_code = None
        if "processor_response_text" not in attributes:
            self.processor_response_text = None

        if "risk_data" in attributes:
            self.risk_data = RiskData(attributes["risk_data"])
        else:
            self.risk_data = None

    @staticmethod
    def find(verification_id):
        return Configuration.gateway().verification.find(verification_id)

    @staticmethod
    def search(*query):
        return Configuration.gateway().verification.search(*query)

    @staticmethod
    def create(params):
        Resource.verify_keys(params, CreditCardVerification.create_signature())
        return Configuration.gateway().verification.create(params)

    @staticmethod
    def create_signature():
        billing_address_params = [
                "company", "country_code_alpha2", "country_code_alpha3", "country_code_numeric",
                "country_name", "extended_address", "first_name", "last_name", "locality",
                "postal_code", "region", "street_address"
            ]
        credit_card_params = [
                "number", "cvv", "cardholder_name", "cvv", "expiration_date", "expiration_month",
                "expiration_year", {"billing_address": billing_address_params}
            ]
        return [{"credit_card": credit_card_params}, {"options": ["amount", "merchant_account_id"]}]

    def __eq__(self, other):
        if not isinstance(other, CreditCardVerification):
            return False
        return self.id == other.id
