from enum import Enum


class MenuErrorCode(Enum):
    CANNOT_ASSIGN_NODE = "cannot_assign_node"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    INVALID_MENU_ITEM = "invalid_menu_item"
    NO_MENU_ITEM_PROVIDED = "no_item_provided"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    TOO_MANY_MENU_ITEMS = "too_many_items"
    UNIQUE = "unique"
