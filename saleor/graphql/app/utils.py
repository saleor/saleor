from django.core.exceptions import ValidationError

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
