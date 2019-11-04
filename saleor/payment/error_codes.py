from enum import Enum


class PaymentErrorCode(Enum):
    BILLING_ADDRESS_NOT_SET = "billing_address_not_set"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    PARTIAL_PAYMENT_NOT_ALLOWED = "partial_payment_not_allowed"
    PAYMENT_ERROR = "payment_error"
    REQUIRED = "required"
    UNIQUE = "unique"
