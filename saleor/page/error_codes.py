from enum import Enum


class PageErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    ATTRIBUTE_ALREADY_ASSIGNED = "attribute_already_assigned"
