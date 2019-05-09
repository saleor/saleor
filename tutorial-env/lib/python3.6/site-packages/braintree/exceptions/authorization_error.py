from braintree.exceptions.braintree_error import BraintreeError

class AuthorizationError(BraintreeError):
    """
    Raised when the user does not have permission to complete the requested operation.

    See https://developers.braintreepayments.com/reference/general/exceptions/python#authorization-error
    """
    pass
