from enum import Enum

import graphene

from .. import models


class VendorErrorCode(Enum):
    UNKNOWN_ERROR = "unknown_error"
    EXISTING_VENDOR = "existing_vendor"
    INVALID_BRAND_NAME = "invalid_brand_name"
    INVALID_FIRST_NAME = "invalid_first_name"
    INVALID_LAST_NAME = "invalid_last_name"
    INVALID_VENDOR = "invalid_vendor"
    INVALID_SLUG = "invalid_slug"
    INVALID_PHONE_NUMBER = "invalid_phone_number"
    INVALID_EMAIL = "invalid_email"
    INVALID_REGISTRATION_NUMBER = "invalid_registration_number"
    INVALID_VAT = "invalid_vat"
    INVALID_RESIDENCE_ID = "invalid_residence_id"
    INVALID_NATIONAL_ID = "invalid_national_id"
    MISSING_VAT = "missing_vat"
    INVALID_FIELD_VALUE = "invalid_field_value"
    ONLY_ONE_ALLOWED = "only_one_allowed"


TargetGenderEnum = graphene.Enum.from_enum(models.Vendor.TargetGender)
RegistrationTypeEnum = graphene.Enum.from_enum(models.Vendor.RegistrationType)
