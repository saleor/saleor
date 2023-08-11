from ...permission.enums import (
    PagePermissions,
    ProductPermissions,
    ProductTypePermissions,
)
from .enums import AttributeTypeEnum
from .utils import prepare_permission_text_for_description

CREATE_PERMISSIONS_MAP = {
    AttributeTypeEnum.PRODUCT_TYPE.value: (
        ProductPermissions.MANAGE_PRODUCTS,
        ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
    ),
    AttributeTypeEnum.PAGE_TYPE.value: (
        ProductPermissions.MANAGE_PRODUCTS,
        PagePermissions.MANAGE_PAGES,
        ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
    ),
}
CREATE_PRODUCT_TYPE_PERMISSIONS_TEXT = prepare_permission_text_for_description(
    CREATE_PERMISSIONS_MAP[AttributeTypeEnum.PRODUCT_TYPE.value]
)
CREATE_PAGE_TYPE_PERMISSIONS_TEXT = prepare_permission_text_for_description(
    CREATE_PERMISSIONS_MAP[AttributeTypeEnum.PAGE_TYPE.value]
)

UPDATE_DELETE_PERMISSIONS_MAP = {
    AttributeTypeEnum.PRODUCT_TYPE.value: (
        ProductPermissions.MANAGE_PRODUCTS,
        ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
    ),
    AttributeTypeEnum.PAGE_TYPE.value: (
        PagePermissions.MANAGE_PAGES,
        ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
    ),
}
UPDATE_DELETE_PRODUCT_TYPE_PERMISSIONS_TEXT = prepare_permission_text_for_description(
    UPDATE_DELETE_PERMISSIONS_MAP[AttributeTypeEnum.PRODUCT_TYPE.value]
)
UPDATE_DELETE_PAGE_TYPE_PERMISSIONS_TEXT = prepare_permission_text_for_description(
    UPDATE_DELETE_PERMISSIONS_MAP[AttributeTypeEnum.PAGE_TYPE.value]
)
