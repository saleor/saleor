import braintree
from braintree.resource import Resource
from braintree.configuration import Configuration

class EuropeBankAccount(Resource):
    class MandateType(object):
        """
        Constants representing the type of the mandate.  Available type:
        * Braintree.EuropeBankAccount.MandateType.Business
        * Braintree.EuropeBankAccount.MandateType.Consumer
        """
        Business = "business"
        Consumer = "consumer"

    @staticmethod
    def signature():
        signature = [
            "billing_address",
            "customer_id",
            "token",
            "masked_iban",
            "bic",
            "mandate_reference_number",
            "mandate_accepted_at",
            "account_holder_name"
        ]
        return signature
