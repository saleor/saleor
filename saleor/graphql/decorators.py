from enum import Enum
from functools import wraps
from typing import Iterable, Union

from graphql.execution.base import ResolveInfo

from ..attribute import AttributeType
from ..core.exceptions import PermissionDenied
from ..core.permissions import AccountPermissions, PagePermissions, ProductPermissions


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
            if test_func(context):
                return f(*args, **kwargs)
            raise PermissionDenied()

        return wrapper

    return decorator


def account_passes_test_for_attribute(test_func):
    """Determine if user/app has permission to access to content."""

    def decorator(f):
        @wraps(f)
        @context(f)
        def wrapper(context, *args, **kwargs):
            root = args[0]
            if test_func(context, root):
                return f(*args, **kwargs)
            raise PermissionDenied()

        return wrapper

    return decorator


def _permission_required(perms: Iterable[Enum], context):
    if context.user.has_perms(perms):
        return True
    app = getattr(context, "app", None)
    if app:
        # for now MANAGE_STAFF permission for app is not supported
        if AccountPermissions.MANAGE_STAFF in perms:
            return False
        return app.has_perms(perms)
    return False


def permission_required(perm: Union[Enum, Iterable[Enum]]):
    def check_perms(context):
        if isinstance(perm, Enum):
            perms = (perm,)
        else:
            perms = perm
        return _permission_required(perms, context)

    return account_passes_test(check_perms)


def one_of_permissions_required(perms: Iterable[Enum]):
    def check_perms(context):
        for perm in perms:
            has_perm = _permission_required((perm,), context)
            if has_perm:
                return True
        return False

    return account_passes_test(check_perms)


staff_member_required = account_passes_test(
    lambda context: context.user.is_active and context.user.is_staff
)


staff_member_or_app_required = account_passes_test(
    lambda context: context.app or (context.user.is_active and context.user.is_staff)
)


def check_attribute_required_permissions():
    """Check attribute permissions that depend on attribute type.

    As an attribute can belong to the product or to the page,
    different permissions need to be checked.
    """

    def check_perms(context, attribute):
        if attribute.type == AttributeType.PAGE_TYPE:
            return _permission_required((PagePermissions.MANAGE_PAGES,), context)
        return _permission_required((ProductPermissions.MANAGE_PRODUCTS,), context)

    return account_passes_test_for_attribute(check_perms)


def check_attribute_value_required_permissions():
    """Check attribute value permissions depending on the corresponding attribute type.

    As an value's attribute can belong to the product or to the page,
    different permissions need to be checked.
    """

    def check_perms(context, attribute_value):
        if attribute_value.attribute.type == AttributeType.PAGE_TYPE:
            return _permission_required((PagePermissions.MANAGE_PAGES,), context)
        return _permission_required((ProductPermissions.MANAGE_PRODUCTS,), context)

    return account_passes_test_for_attribute(check_perms)
