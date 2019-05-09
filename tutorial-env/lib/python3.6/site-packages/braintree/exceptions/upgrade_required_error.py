from braintree.exceptions.braintree_error import BraintreeError

class UpgradeRequiredError(BraintreeError):
    """
    Raised for unsupported client library versions.

    See https://developers.braintreepayments.com/reference/general/exceptions/python#upgrade-required-error
    """
    pass
