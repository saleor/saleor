from saleor.core.permissions import BasePermissionEnum


class VendorPermissions(BasePermissionEnum):
    MANAGE_VENDOR = "vendors.manage"
