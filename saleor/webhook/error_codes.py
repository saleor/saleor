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
    NOT_FOUND = "not_found"
    INVALID_ID = "invalid_id"
    MISSING_APP_PERMISSION = "missing_app_permission"
