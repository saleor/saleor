from enum import Enum


class OrderErrorCode(Enum):
    BILLING_ADDRESS_NOT_SET = "billing_address_not_set"
    CANNOT_CANCEL_FULFILLMENT = "cannot_cancel_fulfillment"
    CANNOT_CANCEL_ORDER = "cannot_cancel_order"
    CANNOT_DELETE = "cannot_delete"
    CANNOT_DISCOUNT = "cannot_discount"
    CANNOT_REFUND = "cannot_refund"
    CANNOT_FULFILL_UNPAID_ORDER = "cannot_fulfill_unpaid_order"
    CAPTURE_INACTIVE_PAYMENT = "capture_inactive_payment"
    GIFT_CARD_LINE = "gift_card_line"
    NOT_EDITABLE = "not_editable"
    FULFILL_ORDER_LINE = "fulfill_order_line"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    PRODUCT_NOT_PUBLISHED = "product_not_published"
    PRODUCT_UNAVAILABLE_FOR_PURCHASE = "product_unavailable_for_purchase"
    NOT_FOUND = "not_found"
    ORDER_NO_SHIPPING_ADDRESS = "order_no_shipping_address"
    PAYMENT_ERROR = "payment_error"
    PAYMENT_MISSING = "payment_missing"
    TRANSACTION_ERROR = "transaction_error"
    REQUIRED = "required"
    SHIPPING_METHOD_NOT_APPLICABLE = "shipping_method_not_applicable"
    SHIPPING_METHOD_REQUIRED = "shipping_method_required"
    TAX_ERROR = "tax_error"
    UNIQUE = "unique"
    VOID_INACTIVE_PAYMENT = "void_inactive_payment"
    ZERO_QUANTITY = "zero_quantity"
    INVALID_QUANTITY = "invalid_quantity"
    INSUFFICIENT_STOCK = "insufficient_stock"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    NOT_AVAILABLE_IN_CHANNEL = "not_available_in_channel"
    CHANNEL_INACTIVE = "channel_inactive"


class OrderGrantRefundCreateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    SHIPPING_COSTS_ALREADY_GRANTED = "shipping_costs_already_granted"
    REQUIRED = "required"
    INVALID = "invalid"


class OrderGrantRefundUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    INVALID = "invalid"
    SHIPPING_COSTS_ALREADY_GRANTED = "shipping_costs_already_granted"


class OrderGrantRefundCreateLineErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    QUANTITY_GREATER_THAN_AVAILABLE = "quantity_greater_than_available"


class OrderGrantRefundUpdateLineErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    QUANTITY_GREATER_THAN_AVAILABLE = "quantity_greater_than_available"


class OrderBulkCreateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    REQUIRED = "required"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    UNIQUE = "unique"
    BULK_LIMIT = "bulk_limit"
    TOO_MANY_IDENTIFIERS = "too_many_identifiers"
    FUTURE_DATE = "future_date"
    INVALID_QUANTITY = "invalid_quantity"
    PRICE_ERROR = "price_error"
    NOTE_LENGTH = "note_length"
    INSUFFICIENT_STOCK = "insufficient_stock"
    NON_EXISTING_STOCK = "non_existing_stock"
    NO_RELATED_ORDER_LINE = "no_related_order_line"
    NEGATIVE_INDEX = "negative_index"
    ORDER_LINE_FULFILLMENT_LINE_MISMATCH = "order_line_fulfillment_line_mismatch"
    METADATA_KEY_REQUIRED = "metadata_key_required"
    INCORRECT_CURRENCY = "incorrect_currency"


class OrderNoteAddErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    REQUIRED = "required"


class OrderNoteUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
