from typing import Any, List

from ...account import models as account_models
from ...core.exceptions import PermissionDenied
from ...core.permissions import (
    AccountPermissions,
    AppPermission,
    BasePermissionEnum,
    CheckoutPermissions,
    OrderPermissions,
    PagePermissions,
    ProductPermissions,
    ProductTypePermissions,
)


def no_permissions(_info, _object_pk: Any) -> List[None]:
    return []


def public_user_permissions(info, user_pk: int) -> List[BasePermissionEnum]:
    """Resolve permission for access to public metadata for user.

    Customer have access to own public metadata.
    Staff user with `MANAGE_USERS` have access to customers public metadata.
    Staff user with `MANAGE_STAFF` have access to staff users public metadata.
    """
    user = account_models.User.objects.filter(pk=user_pk).first()
    if not user:
        raise PermissionDenied()
    if info.context.user.pk == user.pk:
        return []
    if user.is_staff:
        return [AccountPermissions.MANAGE_STAFF]
    return [AccountPermissions.MANAGE_USERS]


def private_user_permissions(_info, user_pk: int) -> List[BasePermissionEnum]:
    user = account_models.User.objects.filter(pk=user_pk).first()
    if not user:
        raise PermissionDenied()
    if user.is_staff:
        return [AccountPermissions.MANAGE_STAFF]
    return [AccountPermissions.MANAGE_USERS]


def product_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [ProductPermissions.MANAGE_PRODUCTS]


def product_type_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES]


def order_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [OrderPermissions.MANAGE_ORDERS]


def invoice_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [OrderPermissions.MANAGE_ORDERS]


def app_permissions(_info, _object_pk: int) -> List[BasePermissionEnum]:
    return [AppPermission.MANAGE_APPS]


def checkout_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [CheckoutPermissions.MANAGE_CHECKOUTS]


def page_permissions(_info, _object_pk: Any) -> List[BasePermissionEnum]:
    return [PagePermissions.MANAGE_PAGES]


PUBLIC_META_PERMISSION_MAP = {
    "Attribute": product_type_permissions,
    "Category": product_permissions,
    "Checkout": no_permissions,
    "Collection": product_permissions,
    "DigitalContent": product_permissions,
    "Fulfillment": order_permissions,
    "Order": no_permissions,
    "Invoice": invoice_permissions,
    "Page": page_permissions,
    "Product": product_permissions,
    "ProductType": product_type_permissions,
    "ProductVariant": product_permissions,
    "App": app_permissions,
    "User": public_user_permissions,
}


PRIVATE_META_PERMISSION_MAP = {
    "Attribute": product_type_permissions,
    "Category": product_permissions,
    "Checkout": checkout_permissions,
    "Collection": product_permissions,
    "DigitalContent": product_permissions,
    "Fulfillment": order_permissions,
    "Order": order_permissions,
    "Invoice": invoice_permissions,
    "Page": page_permissions,
    "Product": product_permissions,
    "ProductType": product_type_permissions,
    "ProductVariant": product_permissions,
    "App": app_permissions,
    "User": private_user_permissions,
}
