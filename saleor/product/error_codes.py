from enum import Enum


class ProductErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    ATTRIBUTE_ALREADY_ASSIGNED = "attribute_already_assigned"
    ATTRIBUTE_BAD_VALUE = "attribute_bad_value"
    ATTRIBUTE_CANNOT_BE_ASSIGNED = "attribute_cannot_be_assigned"
    ATTRIBUTE_DISABLED_VARIANTS = "attribute_disabled_variants"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_PRODUCTS_IMAGE = "not_products_image"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    VARIANT_NO_DIGITAL_CONTENT = "variant_no_digital_content"
