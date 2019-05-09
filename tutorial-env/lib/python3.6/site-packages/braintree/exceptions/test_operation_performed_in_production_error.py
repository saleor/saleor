from braintree.exceptions.braintree_error import BraintreeError

class TestOperationPerformedInProductionError(BraintreeError):
    """
    Raised when an operation that should be used for testing is used in a production environment
    """
    pass
