from enum import Enum


class DiscountErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT = "cannot_manage_product_without_variant"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    VOUCHER_ALREADY_USED = "voucher_already_used"


class PromotionCreateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    INVALID = "invalid"
    MULTIPLE_CURRENCIES_NOT_ALLOWED = "multiple_currencies_not_allowed"
    INVALID_PRECISION = "invalid_precision"
    MISSING_CHANNELS = "missing_channels"
    RULES_NUMBER_LIMIT = "rules_number_limit"
    GIFTS_NUMBER_LIMIT = "gifts_number_limit"
    INVALID_GIFT_TYPE = "invalid_gift_type"


class PromotionUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    INVALID = "invalid"


class PromotionDeleteErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"


class PromotionRuleCreateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    INVALID = "invalid"
    MULTIPLE_CURRENCIES_NOT_ALLOWED = "multiple_currencies_not_allowed"
    INVALID_PRECISION = "invalid_precision"
    MISSING_CHANNELS = "missing_channels"
    RULES_NUMBER_LIMIT = "rules_number_limit"
    GIFTS_NUMBER_LIMIT = "gifts_number_limit"
    INVALID_GIFT_TYPE = "invalid_gift_type"


class PromotionRuleUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    INVALID = "invalid"
    REQUIRED = "required"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    MISSING_CHANNELS = "missing_channels"
    MULTIPLE_CURRENCIES_NOT_ALLOWED = "multiple_currencies_not_allowed"
    INVALID_PRECISION = "invalid_precision"
    INVALID_GIFT_TYPE = "invalid_gift_type"
    GIFTS_NUMBER_LIMIT = "gifts_number_limit"


class PromotionRuleDeleteErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"


class VoucherCodeBulkDeleteErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    INVALID = "invalid"
