from enum import Enum


class VendorErrorCode(Enum):
    GROUP_NOT_FOUND = "vendor_not_found"
    GROUP_ERROR = "vendor_error"


class BillingErrorCode(Enum):
    GROUP_NOT_FOUND = "Billing_not_found"
    GROUP_ERROR = "Billing_error"
