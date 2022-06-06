from enum import Enum


class TaxConfigurationUpdateErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
