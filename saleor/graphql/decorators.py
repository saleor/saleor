from enum import Enum
from functools import wraps
from typing import Iterable, Union

from graphql.execution.base import ResolveInfo

from ..attribute import AttributeType
from ..core.exceptions import PermissionDenied
from ..core.permissions import (
    PagePermissions,
    PageTypePermissions,
    ProductPermissions,
    ProductTypePermissions,
    has_one_of_permissions,
    is_app,
    is_staff_user,
    one_of_permissions_or_auth_filter_required,
)
from ..core.permissions import permission_required as core_permission_required
from .utils import get_user_or_app_from_context


def context(f):
    def decorator(func):
        def wrapper(*args, **kwargs):
            info = next(arg for arg in args if isinstance(arg, ResolveInfo))
            return func(info.context, *args, **kwargs)

        return wrapper

    return decorator


def account_passes_test(test_func):
    """Determine if user/app has permission to access to content."""

    def decorator(f):
        @wraps(f)
        @context(f)
        def wrapper(context, *args, **kwargs):
            test_func(context)
            return f(*args, **kwargs)

        return wrapper

    return decorator


def account_passes_test_for_attribute(test_func):
    """Determine if user/app has permission to access to content."""

    def decorator(f):
        @wraps(f)
        @context(f)
        def wrapper(context, *args, **kwargs):
            root = args[0]
            test_func(context, root)
            return f(*args, **kwargs)

        return wrapper

    return decorator


def permission_required(perm: Union[Enum, Iterable[Enum]]):
    def check_perms(context):
        if isinstance(perm, Enum):
            perms = (perm,)
        else:
            perms = perm

        requestor = get_user_or_app_from_context(context)
        if not core_permission_required(requestor, perms):
            raise PermissionDenied(permissions=perms)

    return account_passes_test(check_perms)


def one_of_permissions_required(perms: Iterable[Enum]):
    def check_perms(context):
        if not one_of_permissions_or_auth_filter_required(context, perms):
            raise PermissionDenied(permissions=perms)

    return account_passes_test(check_perms)


def _check_staff_member(context):
    if not is_staff_user(context):
        raise PermissionDenied(
            message=(
                "You need to be authenticated as a staff member to perform this action"
            )
        )


staff_member_required = account_passes_test(_check_staff_member)


def _check_staff_member_or_app(context):
    if not (is_app(context) or is_staff_user(context)):
        raise PermissionDenied(
            message=(
                "You need to be authenticated as a staff member or an app to perform "
                "this action"
            )
        )


staff_member_or_app_required = account_passes_test(_check_staff_member_or_app)


def check_attribute_required_permissions():
    """Check attribute permissions that depend on attribute type.

    As an attribute can belong to the product or to the page,
    different permissions need to be checked.
    """

    def check_perms(context, attribute):
        requestor = get_user_or_app_from_context(context)
        if attribute.type == AttributeType.PAGE_TYPE:
            permissions = (
                PagePermissions.MANAGE_PAGES,
                PageTypePermissions.MANAGE_PAGE_TYPES_AND_ATTRIBUTES,
            )
        else:
            permissions = (
                ProductPermissions.MANAGE_PRODUCTS,
                ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,
            )
        if not has_one_of_permissions(
            requestor,
            permissions,
        ):
            raise PermissionDenied(permissions=permissions)

    return account_passes_test_for_attribute(check_perms)
