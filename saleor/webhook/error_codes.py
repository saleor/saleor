from enum import Enum


class WebhookErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    DELETE_FAILED = "delete_failed"
    SYNTAX = "syntax"
    MISSING_SUBSCRIPTION = "missing_subscription"
    UNABLE_TO_PARSE = "unable_to_parse"
    MISSING_EVENT = "missing_event"
    INVALID_CUSTOM_HEADERS = "invalid_custom_headers"


class WebhookDryRunErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    INVALID_ID = "invalid_id"
    MISSING_PERMISSION = "missing_permission"
    TYPE_NOT_SUPPORTED = "type_not_supported"
    SYNTAX = "syntax"
    MISSING_SUBSCRIPTION = "missing_subscription"
    UNABLE_TO_PARSE = "unable_to_parse"
    MISSING_EVENT = "missing_event"


class WebhookTriggerErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    NOT_FOUND = "not_found"
    INVALID_ID = "invalid_id"
    MISSING_PERMISSION = "missing_permission"
    TYPE_NOT_SUPPORTED = "type_not_supported"
    SYNTAX = "syntax"
    MISSING_SUBSCRIPTION = "missing_subscription"
    UNABLE_TO_PARSE = "unable_to_parse"
    MISSING_QUERY = "missing_query"
    MISSING_EVENT = "missing_event"
