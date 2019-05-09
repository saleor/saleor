from braintree.attribute_getter import AttributeGetter
from braintree.configuration import Configuration
import braintree.us_bank_account

class UsBankAccountVerification(AttributeGetter):

    class Status(object):
        """
        Constants representing transaction statuses. Available statuses are:

        * braintree.UsBankAccountVerification.Status.Failed
        * braintree.UsBankAccountVerification.Status.GatewayRejected
        * braintree.UsBankAccountVerification.Status.ProcessorDeclined
        * braintree.UsBankAccountVerification.Status.Unrecognized
        * braintree.UsBankAccountVerification.Status.Verified
        * braintree.UsBankAccountVerification.Status.Pending
        """

        Failed                 = "failed"
        GatewayRejected        = "gateway_rejected"
        ProcessorDeclined      = "processor_declined"
        Unrecognized           = "unrecognized"
        Verified               = "verified"
        Pending                = "pending"

    class VerificationMethod(object):
        """
        Constants representing transaction statuses. Available statuses are:

        * braintree.UsBankAccountVerification.VerificationMethod.NetworkCheck
        * braintree.UsBankAccountVerification.VerificationMethod.IndependentCheck
        * braintree.UsBankAccountVerification.VerificationMethod.TokenizedCheck
        * braintree.UsBankAccountVerification.VerificationMethod.MicroTransfers
        """

        NetworkCheck = "network_check"
        IndependentCheck = "independent_check"
        TokenizedCheck = "tokenized_check"
        MicroTransfers = "micro_transfers"

    def __init__(self, gateway, attributes):
        AttributeGetter.__init__(self, attributes)

        if attributes.get("us_bank_account") is not None:
            self.us_bank_account = braintree.us_bank_account.UsBankAccount(gateway, self.us_bank_account)
        else:
            self.us_bank_account = None

    @staticmethod
    def confirm_micro_transfer_amounts(verification_id, amounts):
        return Configuration.gateway().us_bank_account_verification.confirm_micro_transfer_amounts(verification_id, amounts)

    @staticmethod
    def find(verification_id):
        return Configuration.gateway().us_bank_account_verification.find(verification_id)

    @staticmethod
    def search(*query):
        return Configuration.gateway().us_bank_account_verification.search(*query)

    def __eq__(self, other):
        if not isinstance(other, UsBankAccountVerification):
            return False
        return self.id == other.id
