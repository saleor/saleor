from enum import Enum


class PaymentErrorCode(Enum):
    BILLING_ADDRESS_NOT_SET = "billing_address_not_set"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    PARTIAL_PAYMENT_NOT_ALLOWED = "partial_payment_not_allowed"
    SHIPPING_ADDRESS_NOT_SET = "shipping_address_not_set"
    INVALID_SHIPPING_METHOD = "invalid_shipping_method"
    SHIPPING_METHOD_NOT_SET = "shipping_method_not_set"
    PAYMENT_ERROR = "payment_error"
    NOT_SUPPORTED_GATEWAY = "not_supported_gateway"
