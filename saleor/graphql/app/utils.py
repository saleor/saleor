from django.core.exceptions import ValidationError

from ...app.models import App
from ...permission.enums import AppPermission
from ..account.utils import get_out_of_scope_permissions
from ..core.enums import AppErrorCode
from ..utils import requestor_is_superuser


def ensure_can_manage_permissions(requestor, permission_items):
    """Check if requestor can manage permissions from input.

    Requestor cannot manage permissions witch he doesn't have. It raises
    ValidationError when requestor doesn't have required permissions.
    """
    if requestor_is_superuser(requestor):
        return
    missing_permissions = get_out_of_scope_permissions(requestor, permission_items)
    if missing_permissions:
        error_msg = "You can't add permission that you don't have."
        code = AppErrorCode.OUT_OF_SCOPE_PERMISSION.value
        params = {"permissions": missing_permissions}
        raise ValidationError(
            {"permissions": ValidationError(error_msg, code=code, params=params)}
        )


def ensure_app_permissions_allowed(permission_items: list[str]):
    """Reject permissions that an App must never hold.

    Apps must not hold MANAGE_APPS regardless of requestor scope - even
    superusers cannot grant it. This prevents privilege laundering through a
    non-human principal.

    permission_items contains dotted codenames as produced by graphene's
    PermissionEnum deserialization (e.g. "app.manage_apps").
    """
    manage_apps = AppPermission.MANAGE_APPS.value
    if manage_apps not in permission_items:
        return

    error_msg = "MANAGE_APPS permission cannot be granted to an app."
    code = AppErrorCode.OUT_OF_SCOPE_PERMISSION.value
    params = {"permissions": [manage_apps]}
    raise ValidationError(
        {"permissions": ValidationError(error_msg, code=code, params=params)}
    )


def validate_app_is_not_removed(
    app: App | None,
    app_global_id: str,
    field_name: str,
    code: str = AppErrorCode.NOT_FOUND.value,
):
    if app and app.removed_at is not None:
        raise ValidationError(
            {
                field_name: ValidationError(
                    f"Couldn't resolve to a node: {app_global_id}", code=code
                )
            }
        )
