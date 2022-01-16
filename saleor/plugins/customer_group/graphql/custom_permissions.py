from saleor.core.permissions import BasePermissionEnum


class CustomerGroupPermissions(BasePermissionEnum):
    MANAGE_GROUPS = "groups.manage"
