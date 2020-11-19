from enum import Enum


class DiscountErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT = "cannot_manage_product_without_variant"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
