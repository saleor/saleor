from enum import Enum


class ProductErrorCode(Enum):
    ALREADY_EXISTS = "already_exists"
    ATTRIBUTE_ALREADY_ASSIGNED = "attribute_already_assigned"
    ATTRIBUTE_CANNOT_BE_ASSIGNED = "attribute_cannot_be_assigned"
    ATTRIBUTE_VARIANTS_DISABLED = "attribute_variants_disabled"
    MEDIA_ALREADY_ASSIGNED = "media_already_assigned"
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    PRODUCT_WITHOUT_CATEGORY = "product_without_category"
    NOT_PRODUCTS_IMAGE = "not_products_image"
    NOT_PRODUCTS_VARIANT = "not_products_variant"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    VARIANT_NO_DIGITAL_CONTENT = "variant_no_digital_content"
    CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT = "cannot_manage_product_without_variant"
    PRODUCT_NOT_ASSIGNED_TO_CHANNEL = "product_not_assigned_to_channel"
    UNSUPPORTED_MEDIA_PROVIDER = "unsupported_media_provider"
    PREORDER_VARIANT_CANNOT_BE_DEACTIVATED = "preorder_variant_cannot_be_deactivated"


class CollectionErrorCode(Enum):
    DUPLICATED_INPUT_ITEM = "duplicated_input_item"
    GRAPHQL_ERROR = "graphql_error"
    INVALID = "invalid"
    NOT_FOUND = "not_found"
    REQUIRED = "required"
    UNIQUE = "unique"
    CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT = "cannot_manage_product_without_variant"
