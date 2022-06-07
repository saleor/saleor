from enum import Enum


class TaxConfigurationUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"


class TaxClassCreateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"


class TaxClassUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"


class TaxClassDeleteErrorCode(Enum):
    CANNOT_DELETE_DEFAULT_CLASS = "cannot_delete_default_class"
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"


class TaxCountryConfigurationUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"


class TaxCountryConfigurationDeleteErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
