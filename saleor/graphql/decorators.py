from functools import wraps
from typing import Iterable, Union

import six
from graphql_jwt import exceptions
from graphql_jwt.decorators import context


def account_passes_test(test_func):
    """Determine if user/service_account has permission to access to content."""

    def decorator(f):
        @wraps(f)
        @context(f)
        def wrapper(context, *args, **kwargs):
            if test_func(context):
                return f(*args, **kwargs)
            raise exceptions.PermissionDenied()

        return wrapper

    return decorator


def _permission_required(perms: Iterable[str], context):
    if context.user.has_perms(perms):
        return True
    service_account = getattr(context, "service_account", None)
    if service_account and service_account.has_perms(perms):
        return True
    return False


def permission_required(perm: Union[str, Iterable[str]]):
    def check_perms(context):
        if isinstance(perm, six.string_types):
            perms = (perm,)
        else:
            perms = perm
        return _permission_required(perms, context)

    return account_passes_test(check_perms)


def one_of_permissions_required(perms: Iterable[str]):
    def check_perms(context):
        for perm in perms:
            has_perm = _permission_required((perm,), context)
            if has_perm:
                return True
        return False

    return account_passes_test(check_perms)
