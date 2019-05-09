from braintree.exceptions.braintree_error import BraintreeError

class NotFoundError(BraintreeError):
    """
    Raised when an object is not found in the gateway, such as a Transaction.find("bad_id").

    See https://developers.braintreepayments.com/reference/general/exceptions/python#not-found-error
    """
    pass
