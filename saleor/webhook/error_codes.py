from enum import Enum


class WebhookErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    DELETE_FAILED = "delete_failed"


class WebhookDryRunErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    UNABLE_TO_PARSE = "unable_to_parse"
    NOT_FOUND = "not_found"
    INVALID_ID = "invalid_id"
    MISSING_PERMISSION = "missing_permission"
    TYPE_NOT_SUPPORTED = "type_not_supported"
