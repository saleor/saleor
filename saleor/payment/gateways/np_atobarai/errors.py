from enum import Enum


class NPAtobaraiError(Exception):
    pass


class TransactionCancellationResultError(Enum):
    EPRO0101 = "Please confirm that at least one normal transaction is set."
    EPRO0102 = (
        "Please confirm that 1, 000 or fewer sets of normal transactions are set."
    )
    EPRO0105 = "Please check if the NP Transaction ID has been entered."
    EPRO0106 = "Please check if the same NP Transaction ID is duplicated."
    E0100002 = (
        "Please check if the NP Transaction ID is in "
        "half - width alphanumeric characters."
    )
    E0100003 = "Please check if the NP Transaction ID is 11 digits."

    # That the transaction in question exists.
    E0100113 = ...
    # Is not an NP card transaction.
    EPRO0107 = ...
    # Is not cancelled.
    E0100114 = ...
    # Is prior to customer payment.
    E0100118 = ...
    # Prior to returning to merchant.
    E0100131 = ...
    # The payment method is as expected.
    E0100132 = ...


UNKNOWN_ERROR = "Unknown error while processing the payment."
