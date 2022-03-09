from enum import Enum


class WishlistErrorCode(str, Enum):
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT = "CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT"
