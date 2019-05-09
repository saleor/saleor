from braintree.exceptions.braintree_error import BraintreeError

class TooManyRequestsError(BraintreeError):
    """
    Raised when the rate limit request threshold is exceeded.
    """
    pass
