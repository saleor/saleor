from enum import Enum


class ShippingErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    MAX_LESS_THAN_MIN = "max_less_than_min"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    CANNOT_ADD_AND_REMOVE = "cannot_add_and_remove"
