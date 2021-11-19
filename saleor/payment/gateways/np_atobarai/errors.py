from typing import Iterable, List

TRANSACTION_REGISTRATION = "TR"
TRANSACTION_CANCELLATION = "TC"
TRANSACTION_CHANGE = "CH"
FULFILLMENT_REPORT = "FR"


def get_error_messages_from_codes(
    error_codes: Iterable[str],
    action: str,
) -> List[str]:
    return [f"{action}#{code}" for code in error_codes]
