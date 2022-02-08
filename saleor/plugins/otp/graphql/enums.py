from enum import Enum

import graphene


class OTPErrorCode(Enum):
    INVALID = "invalid_otp_supplied"
    USER_NOT_FOUND = "user_not_found"
    INVALID_URL = "invalid_redirect_url"
    MISSING_CHANNEL_SLUG = "missing_channel_slug"


OTPErrorCodeType = graphene.Enum.from_enum(OTPErrorCode)
