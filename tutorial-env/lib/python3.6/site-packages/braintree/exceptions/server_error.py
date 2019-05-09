from braintree.exceptions.braintree_error import BraintreeError

class ServerError(BraintreeError):
    """
    Raised when the gateway raises an error.  Please contant support at support@getbraintree.com.

    See https://developers.braintreepayments.com/reference/general/exceptions/python#server-error
    """
    pass
