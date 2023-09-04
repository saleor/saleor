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
    CHANNEL_INACTIVE = "channel_inactive"
    BALANCE_CHECK_ERROR = "balance_check_error"
    CHECKOUT_EMAIL_NOT_SET = "checkout_email_not_set"
    UNAVAILABLE_VARIANT_IN_CHANNEL = "unavailable_variant_in_channel"
    NO_CHECKOUT_LINES = "no_checkout_lines"


class TransactionCreateErrorCode(Enum):
    INVALID = "invalid"
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    INCORRECT_CURRENCY = "incorrect_currency"
    METADATA_KEY_REQUIRED = "metadata_key_required"
    UNIQUE = "unique"


class TransactionUpdateErrorCode(Enum):
    INVALID = "invalid"
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    INCORRECT_CURRENCY = "incorrect_currency"
    METADATA_KEY_REQUIRED = "metadata_key_required"
    UNIQUE = "unique"


class TransactionRequestActionErrorCode(Enum):
    INVALID = "invalid"
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK = (
        "missing_transaction_action_request_webhook"
    )


class TransactionRequestRefundForGrantedRefundErrorCode(Enum):
    INVALID = "invalid"
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    MISSING_TRANSACTION_ACTION_REQUEST_WEBHOOK = (
        "missing_transaction_action_request_webhook"
    )


class TransactionEventReportErrorCode(Enum):
    INVALID = "invalid"
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    INCORRECT_DETAILS = "incorrect_details"
    ALREADY_EXISTS = "already_exists"


class PaymentGatewayConfigErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class PaymentGatewayInitializeErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class TransactionInitializeErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class TransactionProcessErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    TRANSACTION_ALREADY_PROCESSED = "transaction_already_processed"
    MISSING_PAYMENT_APP_RELATION = "missing_payment_app_relation"
    MISSING_PAYMENT_APP = "missing_payment_app"


class StoredPaymentMethodRequestDeleteErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    CHANNEL_INACTIVE = "channel_inactive"
    GATEWAY_ERROR = "gateway_error"


class PaymentGatewayInitializeTokenizationErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    CHANNEL_INACTIVE = "channel_inactive"
    GATEWAY_ERROR = "gateway_error"


class PaymentMethodInitializeTokenizationErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    CHANNEL_INACTIVE = "channel_inactive"
    GATEWAY_ERROR = "gateway_error"


class PaymentMethodProcessTokenizationErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    CHANNEL_INACTIVE = "channel_inactive"
    GATEWAY_ERROR = "gateway_error"
