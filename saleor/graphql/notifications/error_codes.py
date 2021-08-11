from enum import Enum


class ExternalNotificationErrorCodes(Enum):
    CANNOT_ASSIGN_NODE = "cannot_assign_node"
    GRAPHQL_ERROR = "graphql_error"
    WRONG_PLUGIN_ID = "wrong_plugin_id"
