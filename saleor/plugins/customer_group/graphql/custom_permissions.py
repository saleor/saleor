from saleor.core.permissions import BasePermissionEnum


class CustomerGroupPermissions(BasePermissionEnum):
    MANAGE_USERS = "account.manage_users"
    MANAGE_STAFF = "account.manage_staff"
    IMPERSONATE_USER = "account.impersonate_user"
