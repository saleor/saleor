from enum import Enum


class AppErrorCode(Enum):
    FORBIDDEN = "forbidden"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    OUT_OF_SCOPE_APP = "out_of_scope_app"
    OUT_OF_SCOPE_PERMISSION = "out_of_scope_permission"
