from enum import Enum


class PluginsErrorCode(Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    PLUGIN_MISCONFIGURED = "plugin-misconfigured"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
