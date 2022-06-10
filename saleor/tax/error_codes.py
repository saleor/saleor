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
    CANNOT_DELETE_DEFAULT_CLASS = "cannot_delete_default_class"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class TaxCountryConfigurationUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


class TaxCountryConfigurationDeleteErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
