from enum import Enum

import graphene

from .. import models


class VendorErrorCode(Enum):
    VENDOR_NOT_FOUND = "vendor_not_found"
    VENDOR_ERROR = "vendor_error"
    VENDOR_SLUG = "vendor_error_generate_slug"


class BillingErrorCode(Enum):
    BILLING_NOT_FOUND = "Billing_not_found"
    BILLING_ERROR = "Billing_error"


TargetGenderEnum = graphene.Enum.from_enum(models.Vendor.TargetGender)
RegistrationTypeEnum = graphene.Enum.from_enum(models.Vendor.RegistrationType)
