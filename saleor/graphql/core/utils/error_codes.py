from enum import Enum

DJANGO_VALIDATORS_ERROR_CODES = [
    "invalid",
    "invalid_extension",
    "limit_value",
    "max_decimal_places",
    "max_digits",
    "max_length",
    "max_value",
    "max_whole_digits",
    "min_length",
    "min_value",
    "null_characters_not_allowed",
]

DJANGO_FORM_FIELDS_ERROR_CODES = [
    "contradiction",
    "empty",
    "incomplete",
    "invalid_choice",
    "invalid_date",
    "invalid_image",
    "invalid_list",
    "invalid_time",
    "missing",
    "overflow",
]


class AccountErrorCode(Enum):
    ACTIVATE_OWN_ACCOUNT = "activate_own_account"
    ACTIVATE_SUPERUSER_ACCOUNT = "activate_superuser_account"
    DEACTIVATE_OWN_ACCOUNT = "deactivate_own_account"
    DEACTIVATE_SUPERUSER_ACCOUNT = "deactivate_superuser_account"
    DELETE_NON_STAFF_USER = "delete_non_staff_user"
    DELETE_OWN_ACCOUNT = "delete_own_account"
    DELETE_STAFF_ACCOUNT = "delete_staff_account"
    DELETE_SUPERUSER_ACCOUNT = "delete_superuser_account"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    INVALID_PASSWORD = "invalid_password"
    OBJECT_DOES_NOT_EXIST = "object_does_not_exist"
    PASSWORD_ENTIRELY_NUMERIC = "password_entirely_numeric"
    PASSWORD_TOO_COMMON = "password_too_common"
    PASSWORD_TOO_SHORT = "password_too_short"
    PASSWORD_TOO_SIMILAR = "password_too_similar"
    REQUIRED = "required"
    UNIQUE = "unique"


class CheckoutErrorCode(Enum):
    BILLING_ADDRESS_NOT_SET = "billing_address_not_set"
    CHECKOUT_NOT_FULLY_PAID = "checkout_not_fully_paid"
    GRAPHQL_ERROR = "graphql_error"
    INSUFFICIENT_STOCK = "insufficient_stock"
    INVALID = "invalid"
    INVALID_SHIPPING_METHOD = "invalid_shipping_method"
    OBJECT_ALREADY_EXISTS = "object_already_exists"
    OBJECT_DOES_NOT_EXIST = "object_does_not_exist"
    PAYMENT_ERROR = "payment_error"
    QUANTITY_GREATER_THAN_LIMIT = "quantity_greater_than_limit"
    REQUIRED = "required"
    SHIPPING_ADDRESS_NOT_SET = "shipping_address_not_set"
    SHIPPING_METHOD_NOT_APPLICABLE = "shipping_method_not_applicable"
    SHIPPING_METHOD_NOT_SET = "shipping_method_not_set"
    SHIPPING_NOT_REQUIRED = "shipping_not_required"
    TAX_ERROR = "tax_error"
    UNIQUE = "unique"
    VOUCHER_NOT_APPLICABLE = "voucher_not_applicable"
    ZERO_QUANTITY = "zero_quantity"


class MenuErrorCode(Enum):
    CANNOT_ASSIGN_NODE = "cannot_assign_node"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    INVALID_MENU_ITEM = "invalid_menu_item"
    NO_MENU_ITEM_PROVIDED = "no_item_provided"
    OBJECT_DOES_NOT_EXIST = "object_does_not_exist"
    REQUIRED = "required"
    TOO_MANY_MENU_ITEMS = "too_many_items"
    UNIQUE = "unique"


class OrderErrorCode(Enum):
    CANNOT_CANCEL_FULFILLMENT = "cannot_cancel_fulfillment"
    CANNOT_CANCEL_ORDER = "cannot_cancel_order"
    CANNOT_DELETE = "cannot_delete"
    CANNOT_REFUND = "cannot_refund"
    CAPTURE_INACTIVE_PAYMENT = "capture_inactive_payment"
    EDIT_NON_DRAFT_ORDER = "edit_non_draft_order"
    FULFILL_ORDER_LINE = "fulfill_order_line"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    OBJECT_DOES_NOT_EXIST = "object_does_not_exist"
    ORDER_INVALID_SHIPPING_METHOD = "order_invalid_shipping_method"
    ORDER_NO_SHIPPING_ADDRESS = "order_no_shipping_address"
    PAYMENT_ERROR = "payment_error"
    PAYMENT_MISSING = "payment_missing"
    REQUIRED = "required"
    SHIPPING_METHOD_REQUIRED = "shipping_method_required"
    UNIQUE = "unique"
    VOID_INACTIVE_PAYMENT = "void_inactive_payment"
    ZERO_QUANTITY = "zero_quantity"


class ProductErrorCode(Enum):
    ATTRIBUTE_ALREADY_ASSIGNED = "attribute_already_assigned"
    ATTRIBUTE_BAD_VALUE = "attribute_bad_value"
    ATTRIBUTE_CANNOT_BE_ASSIGNED = "attribute_cannot_be_assigned"
    ATTRIBUTE_DISABLED_VARIANTS = "attribute_disabled_variants"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_PRODUCTS_IMAGE = "not_products_image"
    OBJECT_ALREADY_EXISTS = "object_already_exists"
    OBJECT_DOES_NOT_EXIST = "object_does_not_exist"
    REQUIRED = "required"
    UNIQUE = "unique"
    VARIANT_NO_DIGITAL_CONTENT = "variant_no_digital_content"


class ShopErrorCode(Enum):
    CANNOT_FETCH_TAX_RATES = "cannot_fetch_tax_rates"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    OBJECT_ALREADY_EXISTS = "object_already_exists"
    OBJECT_DOES_NOT_EXIST = "object_does_not_exist"
    REQUIRED = "required"
    UNIQUE = "unique"


class ShippingErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    MAX_LESS_THAN_MIN = "max_less_than_min"
    OBJECT_ALREADY_EXISTS = "object_already_exists"
    OBJECT_DOES_NOT_EXIST = "object_does_not_exist"
    REQUIRED = "required"
    UNIQUE = "unique"


class PaymentErrorCode(Enum):
    BILLING_ADDRESS_NOT_SET = "billing_address_not_set"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    OBJECT_DOES_NOT_EXIST = "object_does_not_exist"
    PARTIAL_PAYMENT_NOT_ALLOWED = "partial_payment_not_allowed"
    PAYMENT_ERROR = "payment_error"
    REQUIRED = "required"
    UNIQUE = "unique"


class GiftcardErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    OBJECT_ALREADY_EXISTS = "object_already_exists"
    OBJECT_DOES_NOT_EXIST = "object_does_not_exist"
    REQUIRED = "required"
    UNIQUE = "unique"


class ExtensionsErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    PLUGIN_MISCONFIGURED = "plugin-misconfigured"
    REQUIRED = "required"
    UNIQUE = "unique"


SALEOR_ERROR_CODE_ENUMS = [
    AccountErrorCode,
    CheckoutErrorCode,
    ExtensionsErrorCode,
    GiftcardErrorCode,
    MenuErrorCode,
    OrderErrorCode,
    PaymentErrorCode,
    ProductErrorCode,
    ShippingErrorCode,
    ShopErrorCode,
]

saleor_error_codes = []
for enum in SALEOR_ERROR_CODE_ENUMS:
    saleor_error_codes.extend([code.value for code in enum])


def get_error_code_from_error(error):
    """Return valid error code."""
    code = error.code
    if code in ["required", "blank", "null"]:
        return "required"
    if code in ["unique", "unique_for_date"]:
        return "unique"
    if code in DJANGO_VALIDATORS_ERROR_CODES or code in DJANGO_FORM_FIELDS_ERROR_CODES:
        return "invalid"
    if isinstance(code, Enum):
        code = code.value
    if code not in saleor_error_codes:
        return "invalid"
    return code
