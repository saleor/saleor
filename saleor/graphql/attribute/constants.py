from ...permission.enums import (
    PagePermissions,
    ProductPermissions,
    ProductTypePermissions,
)
from .enums import AttributeTypeEnum

PERMISSIONS_MAP: dict = {
    AttributeTypeEnum.PRODUCT_TYPE.value: {
        "default": (
            ProductPermissions.MANAGE_PRODUCTS,
            ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
        )
    },
    AttributeTypeEnum.PAGE_TYPE.value: {
        "default": (
            PagePermissions.MANAGE_PAGES,
            ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
        ),
        "create": (
            ProductPermissions.MANAGE_PRODUCTS,
            PagePermissions.MANAGE_PAGES,
            ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
        ),
    },
}
