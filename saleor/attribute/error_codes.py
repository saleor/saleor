from enum import Enum


class AttributeErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"


class AttributeBulkCreateErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    BLANK = "blank"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    MAX_LENGTH = "max_length"


class AttributeBulkUpdateErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    BLANK = "blank"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    MAX_LENGTH = "max_length"
