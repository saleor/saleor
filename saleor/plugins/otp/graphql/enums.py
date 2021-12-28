from enum import Enum

import graphene


class OTPErrorCode(Enum):
    INVALID = "invalid_otp_supplied"
    MISSING_CHANNEL_SLUG = "missing_channel_slug"
    INVALID_URL = "invalid_redirect_url"


OTPErrorCodeType = graphene.Enum.from_enum(OTPErrorCode)
