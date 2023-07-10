from typing import TYPE_CHECKING, Iterable, Union

from .auth_filters import AuthorizationFilters, resolve_authorization_filter_fn
from .enums import AccountPermissions, BasePermissionEnum

if TYPE_CHECKING:
    from ..account.models import User
    from ..app.models import App


def one_of_permissions_or_auth_filter_required(
    context, permissions: Iterable[BasePermissionEnum]
) -> bool:
    """Determine whether user or app has rights to perform an action.

    The `context` parameter is the Context instance associated with the request.
    """
    if not permissions:
        return True

    authorization_filters = [
        p for p in permissions if isinstance(p, AuthorizationFilters)
    ]
    permissions = [p for p in permissions if not isinstance(p, AuthorizationFilters)]

    granted_by_permissions = False
    granted_by_authorization_filters = False

    # TODO: move this function from graphql to core
    from saleor.graphql.utils import get_user_or_app_from_context

    requestor = get_user_or_app_from_context(context)

    if requestor and permissions:
        perm_checks_results = [requestor.has_perm(perm) for perm in permissions]
        granted_by_permissions = any(perm_checks_results)

    if authorization_filters:
        auth_filters_results = []
        for p in authorization_filters:
            perm_fn = resolve_authorization_filter_fn(p)
            if perm_fn:
                res = perm_fn(context)
                auth_filters_results.append(bool(res))
        granted_by_authorization_filters = any(auth_filters_results)

    return granted_by_permissions or granted_by_authorization_filters


def permission_required(
    requestor: Union["User", "App", None], perms: Iterable[BasePermissionEnum]
) -> bool:
    from ..account.models import User

    if isinstance(requestor, User):
        return requestor.has_perms(perms)
    elif requestor:
        # for now MANAGE_STAFF permission for app is not supported
        if AccountPermissions.MANAGE_STAFF in perms:
            return False
        return requestor.has_perms(perms)
    return False


def has_one_of_permissions(
    requestor: Union["User", "App", None], permissions: Iterable[BasePermissionEnum]
) -> bool:
    if not permissions:
        return True
    if not requestor:
        return False
    for perm in permissions:
        if permission_required(requestor, (perm,)):
            return True
    return False


def message_one_of_permissions_required(
    permissions: Iterable[BasePermissionEnum],
) -> str:
    permission_msg = ", ".join([p.name for p in permissions])
    return f"\n\nRequires one of the following permissions: {permission_msg}."
