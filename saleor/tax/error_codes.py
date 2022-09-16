from enum import Enum


class TaxConfigurationUpdateErrorCode(Enum):
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class TaxClassCreateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class TaxClassUpdateErrorCode(Enum):
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class TaxClassDeleteErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class TaxCountryConfigurationUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    ONLY_ONE_DEFAULT_COUNTRY_RATE_ALLOWED = "only_one_default_country_rate_allowed"
    CANNOT_CREATE_WITH_NULL_RATE = "cannot_create_with_null_rate"


class TaxCountryConfigurationDeleteErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
