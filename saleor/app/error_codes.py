from enum import Enum


class AppErrorCode(Enum):
    FORBIDDEN = "forbidden"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    INVALID_STATUS = "invalid_status"
    INVALID_PERMISSION = "invalid_permission"
    INVALID_URL_FORMAT = "invalid_url_format"
    INVALID_MANIFEST_FORMAT = "invalid_manifest_format"
    MANIFEST_URL_CANT_CONNECT = "manifest_url_cant_connect"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    OUT_OF_SCOPE_APP = "out_of_scope_app"
    OUT_OF_SCOPE_PERMISSION = "out_of_scope_permission"
