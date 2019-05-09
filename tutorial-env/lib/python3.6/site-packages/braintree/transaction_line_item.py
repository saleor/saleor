import braintree
import warnings

from braintree.attribute_getter import AttributeGetter
from braintree.resource import Resource
from braintree.configuration import Configuration

class TransactionLineItem(AttributeGetter):
    pass

    class Kind(object):
        """
        Constants representing transaction line item kinds. Available kinds are:

        * braintree.TransactionLineItem.Kind.Credit
        * braintree.TransactionLineItem.Kind.Debit
        """

        Credit = "credit"
        Debit = "debit"

    def __init__(self, attributes):
        AttributeGetter.__init__(self, attributes)

    @staticmethod
    def find_all(transaction_id):
        """
        Find all line items on a transaction, given a transaction_id. This returns an array of TransactionLineItems.
        This will raise a :class:`NotFoundError <braintree.exceptions.not_found_error.NotFoundError>` if the provided
        transaction_id is not found. ::

            transaction_line_items = braintree.TransactionLineItem.find_all("my_transaction_id")
        """
        return Configuration.gateway().transaction_line_item.find_all(transaction_id)
