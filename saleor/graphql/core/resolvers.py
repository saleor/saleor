from .types import Shop
from ...core.permissions import get_permissions
from .types import PermissionDisplay

def resolve_shop(root, info):
    permissions = get_permissions()
    permissions = [PermissionDisplay(
            code='.'.join([permission.content_type.app_label, permission.codename]),
            name=permission.name) for permission in permissions]
    return Shop(permissions=permissions)
