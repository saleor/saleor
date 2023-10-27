from collections.abc import Iterable

TRANSACTION_REGISTRATION = "TR"
TRANSACTION_CANCELLATION = "TC"
TRANSACTION_CHANGE = "CH"
FULFILLMENT_REPORT = "FR"


def add_action_to_code(action: str, error_code: str) -> str:
    return f"{action}#{error_code}"


def get_error_messages_from_codes(action: str, error_codes: Iterable[str]) -> list[str]:
    return [add_action_to_code(action, code) for code in error_codes]


# connection error codes
NP_CONNECTION_ERROR = "SALEORNP000"

# address error codes
NO_BILLING_ADDRESS = "SALEORNP001"
NO_SHIPPING_ADDRESS = "SALEORNP002"
BILLING_ADDRESS_INVALID = "SALEORNP003"
SHIPPING_ADDRESS_INVALID = "SALEORNP004"

# payment error codes
NO_PSP_REFERENCE = "SALEORNP005"
PAYMENT_DOES_NOT_EXIST = "SALEORNP006"

# fulfillment error codes
NO_TRACKING_NUMBER = "SALEORNP007"
SHIPPING_COMPANY_CODE_INVALID = "SALEORNP008"
