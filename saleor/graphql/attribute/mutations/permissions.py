from collections.abc import Iterable

from ....attribute import AttributeType
from ....core.exceptions import PermissionDenied
from ....permission.enums import (
    BasePermissionEnum,
    CustomerTypePermissions,
    PageTypePermissions,
    ProductTypePermissions,
)
from ...core.mutations import BaseMutation

ATTRIBUTE_TYPE_PERMISSION_MAP: dict[str, BasePermissionEnum] = {
    AttributeType.PRODUCT_TYPE: (
        ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES
    ),
    AttributeType.PAGE_TYPE: PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
    AttributeType.CUSTOMER_TYPE: (
        CustomerTypePermissions.MANAGE_CUSTOMER_TYPES_AND_ATTRIBUTES
    ),
}


def check_any_attribute_type_permission(
    mutation_cls: type[BaseMutation], context
) -> None:
    """Require any of the attribute type permissions.

    Used as a pre-gate before the mutation input is resolved, so permission
    errors take precedence over validation errors. The concrete permission is
    checked with `check_attribute_type_permissions` once the target attribute
    types are known.
    """
    permissions = tuple(ATTRIBUTE_TYPE_PERMISSION_MAP.values())
    if not mutation_cls.check_permissions(context, permissions):
        raise PermissionDenied(permissions=permissions)


def check_attribute_type_permissions(
    mutation_cls: type[BaseMutation], context, attribute_types: Iterable[str]
) -> None:
    """Require the permission matching each of the given attribute types.

    An attribute type missing from `ATTRIBUTE_TYPE_PERMISSION_MAP` is denied
    rather than allowed, so adding a type without mapping it fails closed.
    """
    attribute_types_set = set(attribute_types)
    if unmapped_types := attribute_types_set - ATTRIBUTE_TYPE_PERMISSION_MAP.keys():
        raise PermissionDenied(
            message=(
                "No permission is defined for attribute type "
                f"{sorted(unmapped_types)[0]}."
            )
        )
    missing_permissions = [
        permission
        for attribute_type, permission in ATTRIBUTE_TYPE_PERMISSION_MAP.items()
        if attribute_type in attribute_types_set
        and not mutation_cls.check_permissions(context, (permission,))
    ]
    if missing_permissions:
        raise PermissionDenied(permissions=missing_permissions)
