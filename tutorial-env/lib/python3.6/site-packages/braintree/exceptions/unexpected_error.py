from braintree.exceptions.braintree_error import BraintreeError

class UnexpectedError(BraintreeError):
    """ Raised for unknown or unexpected errors. """
    pass
