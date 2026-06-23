from enum import Enum


class SiteErrorCode(Enum):
    FORBIDDEN_CHARACTER = "forbidden_character"
    GRAPHQL_ERROR = "graphql_error"


class OrderSettingsErrorCode(Enum):
    INVALID = "invalid"


class GiftCardSettingsErrorCode(Enum):
    INVALID = "invalid"
    REQUIRED = "required"
    GRAPHQL_ERROR = "graphql_error"


class RefundSettingsErrorCode(Enum):
    INVALID = "invalid"
    REQUIRED = "required"
    GRAPHQL_ERROR = "graphql_error"


class ReturnSettingsErrorCode(Enum):
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    GRAPHQL_ERROR = "graphql_error"
