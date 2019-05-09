from decimal import Decimal
from braintree.resource import Resource
from braintree.transaction_search import TransactionSearch
from braintree.merchant_account import MerchantAccount

class Disbursement(Resource):
    class Type(object):
        """
        """

        Credit = "credit"
        Debit = "debit"

    def __init__(self, gateway, attributes):
        Resource.__init__(self, gateway, attributes)
        self.amount = Decimal(self.amount)
        self.merchant_account = MerchantAccount(gateway, attributes["merchant_account"])

    def __repr__(self):
        detail_list = ["amount", "disbursement_date", "exception_message", "follow_up_action", "id", "success", "retry"]
        return super(Disbursement, self).__repr__(detail_list)

    def transactions(self):
        return self.gateway.transaction.search([TransactionSearch.ids.in_list(self.transaction_ids)])

    def is_credit(self):
        return self.disbursement_type == Disbursement.Type.Credit

    def is_debit(self):
        return self.disbursement_type == Disbursement.Type.Debit
