from enum import Enum

import graphene


class VendorErrorCode(Enum):
    VENDOR_NOT_FOUND = "vendor_not_found"
    VENDOR_ERROR = "vendor_error"
    VENDOR_SLUG = "vendor_error_generate_slug"


class BillingErrorCode(Enum):
    GROUP_NOT_FOUND = "Billing_not_found"
    GROUP_ERROR = "Billing_error"


class CommercialInfo(graphene.Enum):
    CR = "cr"
    MAROOF = "maroof"


class SellsGender(graphene.Enum):
    MEN = "men"
    WOMEN = "women"
    UNISEX = "unisex"
