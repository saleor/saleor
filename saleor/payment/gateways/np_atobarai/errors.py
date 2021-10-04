from enum import Enum
from typing import Iterable, List, Type


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

    E0100113 = "Please confirm that the transaction in question exists."

    EPRO0107 = "Please confirm that the transaction s an NP card transaction."

    E0100114 = "Please confirm that the transaction is prior to customer payment."

    E0100118 = "Please confirm that the transaction is not cancelled."

    E0100131 = "Please confirm that the transaction is prior to returning to merchant."

    E0100132 = "Please confirm that the payment method is as expected."


UNKNOWN_ERROR = "Unknown error while processing the payment."


def get_error_messages_from_codes(
    error_codes: Iterable[str], error_enum_cls: Type[Enum]
) -> List[str]:
    error_messages = []
    for code in error_codes:
        try:
            message = error_enum_cls[code].value
        except KeyError:
            message = f"#{code}: {UNKNOWN_ERROR}"

        error_messages.append(message)

    return error_messages
