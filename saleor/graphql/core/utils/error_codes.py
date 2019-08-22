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
    "required",
]

DJANGO_PASSWORD_VALIDATION_ERROR_CODES = [
    "password_entirely_numeric",
    "password_too_common",
    "password_too_short",
    "password_too_similar",
]

DJANGO_MODEL_FIELDS_ERROR_CODES = ["blank", "null", "unique", "unique_for_date"]


class AccountErrorCode(Enum):
    ACTIVATE_OWN_ACCOUNT = "activate_own_account"
    ACTIVATE_SUPERUSER_ACCOUNT = "activate_superuser_account"
    DEACTIVATE_OWN_ACCOUNT = "deactivate_own_account"
    DEACTIVATE_SUPERUSER_ACCOUNT = "deactivate_superuser_account"
    DELETE_NON_STAFF_USER = "delete_non_staff_user"
    DELETE_OWN_ACCOUNT = "delete_own_account"
    DELETE_STAFF_ACCOUNT = "delete_staff_account"
    DELETE_STUFF_ACCOUNT = "delete_stuff_account"
    DELETE_SUPERUSER_ACCOUNT = "delete_superuser_account"
    INVALID_COUNTRY = "invalid_country"
    INVALID_PASSWORD = "invalid_password"
    INVALID_PHONE_NUMBER = "invalid_phone_number"
    INVALID_USER_TOKEN = "invalid_user_token"
    NOT_USERS_ADDRESS = "not_users_address"
    USER_DOES_NOT_EXIST = "user_does_not_exist"


class CheckoutErrorCode(Enum):
    BILLING_ADDRESS_NOT_SET = "billing_address_not_set"
    CHECKOUT_NOT_FULLY_PAID = "checkout_not_fully_paid"
    INSUFFICIENT_STOCK = "insufficient_stock"
    INVALID_PROMO_CODE = "invalid_promo_code"
    INVALID_SHIPPING_METHOD = "invalid_shipping_method"
    PROMO_CODE_ALREADY_EXISTS = "promo_code_already_exists"
    QUANTITY_GREATER_THAN_LIMIT = "quantity_greater_than_limit"
    SHIPPING_ADDRESS_NOT_SET = "shipping_address_not_set"
    SHIPPING_METHOD_NOT_APPLICABLE = "shipping_method_not_applicable"
    SHIPPING_METHOD_NOT_SET = "shipping_method_not_set"
    SHIPPING_NOT_REQUIRED = "shipping_not_required"
    TAX_ERROR = "tax_error"
    VOUCHER_NOT_APPLICABLE = "voucher_not_applicable"


class MenuErrorCode(Enum):
    ASSIGN_MENU_ITEM_TO_ITSELF = "assign_menu_item_to_itself"
    CANNOT_ASSIGN_NOTE = "cannot_assign_node"
    INVALID_MENU_ITEM = "invalid_menu_item"
    NO_MENU_ITEM_PROVIDED = "no_item_provided"
    TOO_MANY_MENU_ITEMS = "too_many_items"


class OrderErrorCode(Enum):
    CANNOT_CANCEL_FULFILLMENT = "cannot_cancel_fulfillment"
    CANNOT_CANCEL_ORDER = "cannot_cancel_order"
    CAPTURE_INACTIVE_PAYMENT = "capture_inactive_payment"
    DELETE_LINE_NON_DRAFT_ORDER = "delete_line_non_draft_order"
    DELETE_NON_DRAFT_ORDER = "delete_non_draft_order"
    EDIT_NON_DRAFT_ORDER = "edit_non_draft_order"
    FULFILL_ORDER_LINE = "fulfill_order_line"
    ORDER_INVALID_SHIPPING_METHOD = "order_invalid_shipping_method"
    ORDER_NO_PAYMENT = "order_no_payment"
    ORDER_NO_PRODUCTS = "order_without_products"
    ORDER_NO_SHIPPING_ADDRESS = "order_no_shipping_address"
    QUANTITY_LESS_THAN_ONE = "quantity_less_than_one"
    REFUND_MANUAL_PAYMENT = "refund_manual_payment"
    VARIANT_DOES_NOT_EXIST = "variant_does_not_exist"
    VOID_INACTIVE_PAYMENT = "void_inactive_payment"


class CommonErrorCode(Enum):
    AUTHORIZATION_KEY_ALREADY_EXISTS = "authorization_key_already_exists"
    CANNOT_FETCH_TAX_RATES = "cannot_fetch_tax_rates"
    DOES_NOT_EXIST = "does_not_exist"
    GRAPHQL_ERROR = "graphql_error"
    INCORRECT_VALUE = "incorrect_value"
    INVALID_FILE_TYPE = "invalid_file_type"
    INVALID_STOREFRONT_URL = "invalid_storefront_url"
    INVALID_WEIGHT_UNIT = "invalid_weight_unit"
    MISSING_VALUE = "missing_value"
    NON_BLANK_VALUE_REQUIRED = "non_blank_value_required"
    PARTIAL_PAYMENT_NOT_ALLOWED = "partial_payment_not_allowed"
    PAYMENT_ERROR = "payment_error"
    POSITIVE_NUMBER_REQUIRED = "positive_number_required"
    SHIPPING_METHOD_REQUIRED = "shipping_method_required"
    VALUE_ERROR = "value_error"


class AttributeErrorCode(Enum):
    ATTRIBUTE_ALREADY_ASSIGNED = "attribute_already_assigned"
    ATTRIBUTE_ALREADY_EXISTS = "attribute_already_exists"
    ATTRIBUTE_BAD_VALUE = "attribute_bad_value"
    ATTRIBUTE_CANNOT_BE_ASSIGNED = "attribute_cannot_be_assigned"
    ATTRIBUTE_DISABLED_VARIANTS = "attribute_disabled_variants"
    ATTRIBUTE_NON_ASSIGNABLE = "attribute_non_assignable"
    ATTRIBUTE_SLUG_ALREADY_EXISTS = "attribute_slug_already_exists"
    ATTRIBUTE_SLUG_BLANK = "attribute_slug_blank"
    ATTRIBUTE_VALUES_NOT_UNIQUE = "attribute_values_not_unique"


class DigitalContentErrorCode(Enum):
    MISSING_CONFIGURATION_FIELDS = "missing_configuration_fields"
    VARIANT_NO_DIGITAL_CONTENT = "variant_no_digital_content"


class ProductErrorCode(Enum):
    NOT_PRODUCTS_IMAGE = "not_products_image"
    PRODUCT_ALREADY_EXISTS = "product_already_exists"


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
    + DJANGO_MODEL_FIELDS_ERROR_CODES
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
