from enum import Enum


class WarehouseErrorCode(str, Enum):
    ALREADY_EXISTS = "already_exists"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"


class StockErrorCode(str, Enum):
    ALREADY_EXISTS = "already_exists"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"


class StockBulkUpdateErrorCode(str, Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
