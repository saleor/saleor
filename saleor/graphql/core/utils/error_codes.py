from enum import Enum

DJANGO_VALIDATORS_ERROR_CODES = [
    "invalid",
    "limit_value",
    "max_value",
    "min_value",
    "min_length",
    "max_length",
    "max_digits",
    "max_decimal_places",
    "max_whole_digits",
    "invalid_extension",
    "null_characters_not_allowed",
]

DJANGO_FORM_FIELDS_ERROR_CODES = [
    "required",
    "overflow",
    "missing",
    "empty",
    "contradiction",
    "invalid_image",
    "invalid_choice",
    "invalid_list",
    "incomplete",
    "invalid_date",
    "invalid_time",
]

DJANGO_PASSWORD_VALIDATION_ERROR_CODES = [
    "password_too_short",
    "password_too_similar",
    "password_too_common",
    "password_entirely_numeric",
]


class AccountErrorCode(Enum):
    INVALID_PHONE_NUMBER = "invalid_phone_number"
    ACTIVATE_OWN_ACCOUNT = "activate_own_account"
    ACTIVATE_SUPERUSER_ACCOUNT = "activate_superuser_account"
    DEACTIVATE_OWN_ACCOUNT = "deactivate_own_account"
    DEACTIVATE_SUPERUSER_ACCOUNT = "deactivate_superuser_account"
    INVALID_COUNTRY = "invalid_country"
    DELETE_STUFF_ACCOUNT = "delete_stuff_account"
    INVALID_USER_TOKEN = "invalid_user_token"
    NOT_USERS_ADDRESS = "not_users_address"
    USER_DOES_NOT_EXIST = "user_does_not_exist"
    DELETE_OWN_ACCOUNT = "delete_own_account"
    DELETE_SUPERUSER_ACCOUNT = "delete_superuser_account"
    DELETE_STAFF_ACCOUNT = "delete_staff_account"
    DELETE_NON_STAFF_USER = "delete_non_staff_user"


class CheckoutErrorCode(Enum):
    VOUCHER_NOT_APPLICABLE = "voucher_not_applicable"
    SHIPPING_METHOD_NOT_SET = "shipping_method_not_set"
    SHIPPING_ADDRESS_NOT_SET = "shipping_address_not_set"
    BILLING_ADDRESS_NOT_SET = "billing_address_not_set"
    INVALID_SHIPPING_METHOD = "invalid_shipping_method"
    CHECKOUT_NOT_FULLY_PAID = "checkout_not_fully_paid"
    SHIPPING_NOT_REQUIRED = "shipping_not_required"
    QUANTITY_GREATER_THAN_LIMIT = "quantity_greater_than_limit"
    INSUFFICIENT_STOCK = "insufficient_stock"
    SHIPPING_METHOD_NOT_APPLICABLE = "shipping_method_not_applicable"
    TAX_ERROR = "tax_error"


class MenuErrorCode(Enum):
    TOO_MANY_MENU_ITEMS = "too_many_items"
    NO_MENU_ITEM_PROVIDED = "no_item_provided"
    INVALID_MENU_ITEM = "invalid_menu_item"
    ASSIGN_MENU_ITEM_TO_ITSELF = "assign_menu_item_to_itself"
    CANNOT_ASSIGN_NOTE = "cannot_assign_node"


class OrderErrorCode(Enum):
    DELETE_NON_DRAFT_ORDER = "delete_non_draft_order"
    DELETE_LINE_NON_DRAFT_ORDER = "delete_line_non_draft_order"
    EDIT_NON_DRAFT_ORDER = "edit_non_draft_order"
    QUANTITY_LESS_THAN_ONE = "quantity_less_than_one"
    FULFILL_ORDER_LINE = "fulfill_order_line"
    CANNOT_CANCEL_FULFILLMENT = "cannot_cancel_fulfillment"
    CANNOT_CANCEL_ORDER = "cannot_cancel_order"
    ORDER_NO_PAYMENT = "order_no_payment"
    CAPTURE_INACTIVE_PAYMENT = "capture_inactive_payment"
    VOID_INACTIVE_PAYMENT = "void_inactive_payment"
    REFUND_MANUAL_PAYMENT = "refund_manual_payment"
    ORDER_NO_PRODUCTS = "order_without_products"
    VARIANT_DOES_NOT_EXIST = "variant_does_not_exist"
    ORDER_NO_SHIPPING_ADDRESS = "order_no_shipping_address"
    ORDER_INVALID_SHIPPING_METHOD = "order_invalid_shipping_method"


class CommonErrorCode(Enum):
    PAYMENT_ERROR = "payment_error"
    PARTIAL_PAYMENT_NOT_ALLOWED = "partial_payment_not_allowed"
    SHIPPING_METHOD_REQUIRED = "shipping_method_required"
    POSITIVE_NUMBER_REQUIRED = "positive_number_required"
    DOES_NOT_EXIST = "does_not_exist"
    VALUE_ERROR = "value_error"
    NON_BLANK_VALUE_REQUIRED = "non_blank_value_required"
    MISSING_VALUE = "missing_value"
    INCORRECT_VALUE = "incorrect_value"
    CANNOT_FETCH_TAX_RATES = "cannot_fetch_tax_rates"
    GRAPHQL_ERROR = "graphql_error"
    INVALID_FILE_TYPE = "invalid_file_type"
    INVALID_STOREFRONT_URL = "invalid_storefront_url"
    AUTHORIZATION_KEY_ALREADY_EXISTS = "authorization_key_already_exists"


class AttributeErrorCode(Enum):
    ATTRIBUTE_ALREADY_EXISTS = "attribute_already_exists"
    ATTRIBUTE_VALUES_NOT_UNIQUE = "attribute_values_not_unique"
    ATTRIBUTE_SLUG_BLANK = "attribute_slug_blank"
    ATTRIBUTE_SLUG_ALREADY_EXISTS = "attribute_slug_already_exists"
    ATTRIBUTE_BAD_VALUE = "attribute_bad_value"
    ATTRIBUTE_ALREADY_ASSIGNED = "attribute_already_assigned"
    ATTRIBUTE_NON_ASSIGNABLE = "attribute_non_assignable"
    ATTRIBUTE_CANNOT_BE_ASSIGNED = "attribute_cannot_be_assigned"
    ATTRIBUTE_DISABLED_VARIANTS = "attribute_disabled_variants"


class DigitalContentErrorCode(Enum):
    MISSING_CONFIGURATION_FIELDS = "missing_configuration_fields"
    VARIANT_NO_DIGITAL_CONTENT = "variant_no_digital_content"


class ProductErrorCode(Enum):
    PRODUCT_ALREADY_EXISTS = "product_already_exists"
    NOT_PRODUCTS_IMAGE = "not_products_image"


class ShippingErrorCode(Enum):
    DEFAULT_SHIPPING_ZONE_ALREADY_EXISTS = "default_shipping_zone_already_exists"
    MAX_LESS_THAN_MIN = "max_less_than_min"


ERROR_CODE_UNKNOWN = "unknown"

SALEOR_ERROR_CODE_ENUMS = [
    AccountErrorCode,
    CheckoutErrorCode,
    MenuErrorCode,
    OrderErrorCode,
    CommonErrorCode,
    AttributeErrorCode,
    DigitalContentErrorCode,
    ProductErrorCode,
    ShippingErrorCode,
]

saleor_error_codes = []
for enum in SALEOR_ERROR_CODE_ENUMS:
    saleor_error_codes.extend([code.value for code in enum])


ERROR_CODES = (
    [ERROR_CODE_UNKNOWN]
    + DJANGO_VALIDATORS_ERROR_CODES
    + DJANGO_FORM_FIELDS_ERROR_CODES
    + DJANGO_PASSWORD_VALIDATION_ERROR_CODES
    + saleor_error_codes
)


def get_error_code_from_error(error):
    """Return valid error code or UNKNOWN for unknown error code."""
    code = error.code
    if isinstance(code, Enum):
        code = code.value
    if code not in ERROR_CODES:
        return ERROR_CODE_UNKNOWN
    return code
