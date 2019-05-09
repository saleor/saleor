from braintree.exceptions.braintree_error import BraintreeError

class ForgedQueryStringError(BraintreeError):
    """
    Raised when the query string has been forged or tampered with during a transparent redirect.

    See https://developers.braintreepayments.com/reference/general/exceptions/python#forged-query-string
    """
    pass
