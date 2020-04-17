from enum import Enum


class ShopErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    CANNOT_FETCH_TAX_RATES = "cannot_fetch_tax_rates"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"


class MetadataErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class TranslationErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
