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


def get_attribute_type_permissions(
    attribute_type: str,
) -> tuple[BasePermissionEnum, ...] | None:
    """Return the permissions accepted for the given attribute type.

    Returns `None` when the attribute type has no mapped permission, so callers
    can report it as an error instead of allowing the operation.
    """
    permission = ATTRIBUTE_TYPE_PERMISSION_MAP.get(attribute_type)
    if permission is None:
        return None
    return (permission,)


def check_any_attribute_type_permission(
    mutation_cls: type[BaseMutation],
    context,
    legacy_permissions: Iterable[BasePermissionEnum] = (),
) -> None:
    """Require any of the attribute type permissions.

    Used as a pre-gate before the mutation input is resolved, so permission
    errors take precedence over validation errors. The concrete permission is
    checked with `check_attribute_type_permissions` once the target attribute
    types are known.

    `legacy_permissions` are the permissions the mutation accepted before the
    checks became type-aware; they are still accepted here.
    """
    permissions = (*ATTRIBUTE_TYPE_PERMISSION_MAP.values(), *legacy_permissions)
    if not mutation_cls.check_permissions(context, permissions):
        raise PermissionDenied(permissions=permissions)


def check_attribute_type_permissions(
    mutation_cls: type[BaseMutation],
    context,
    attribute_types: Iterable[str],
    legacy_permissions: Iterable[BasePermissionEnum] = (),
) -> None:
    """Require the permission matching each of the given attribute types.

    An attribute type missing from `ATTRIBUTE_TYPE_PERMISSION_MAP` is denied
    rather than allowed, so adding a type without mapping it fails closed.

    `legacy_permissions` are the permissions the mutation accepted before the
    checks became type-aware. Holding one of them satisfies the check for every
    attribute type, so requestors authorized under the previous rules keep
    working.
    """
    attribute_types_set = set(attribute_types)
    if unmapped_types := attribute_types_set - ATTRIBUTE_TYPE_PERMISSION_MAP.keys():
        raise PermissionDenied(
            message=(
                "No permission is defined for attribute type "
                f"{sorted(unmapped_types)[0]}."
            )
        )
    legacy_permissions = tuple(legacy_permissions)
    if legacy_permissions and mutation_cls.check_permissions(
        context, legacy_permissions
    ):
        return
    missing_permissions = [
        permission
        for attribute_type, permission in ATTRIBUTE_TYPE_PERMISSION_MAP.items()
        if attribute_type in attribute_types_set
        and not mutation_cls.check_permissions(context, (permission,))
    ]
    if missing_permissions:
        raise PermissionDenied(permissions=[*missing_permissions, *legacy_permissions])
