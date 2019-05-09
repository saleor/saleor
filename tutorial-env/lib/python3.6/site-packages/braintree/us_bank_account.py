import braintree
from braintree.resource import Resource
from braintree.configuration import Configuration
from braintree.ach_mandate import AchMandate
from braintree.us_bank_account_verification import UsBankAccountVerification

class UsBankAccount(Resource):

    @staticmethod
    def find(token):
        return Configuration.gateway().us_bank_account.find(token)

    @staticmethod
    def sale(token, transactionRequest):
        transactionRequest["payment_method_token"] = token
        if not "options" in transactionRequest:
            transactionRequest["options"] = {}
        transactionRequest["options"]["submit_for_settlement"] = True
        return Configuration.gateway().transaction.sale(transactionRequest)

    @staticmethod
    def signature():
        signature = [
            "routing_number",
            "last_4",
            "account_type",
            "account_holder_name",
            "token",
            "image_url",
            "bank_name",
            "ach_mandate"
        ]
        return signature

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        if attributes.get("ach_mandate") is not None:
            self.ach_mandate = AchMandate(gateway, self.ach_mandate)
        else:
            self.ach_mandate = None

        if attributes.get("verifications") is not None:
            self.verifications = [UsBankAccountVerification(gateway, v) for v in self.verifications]
        else:
            self.verifications = None
