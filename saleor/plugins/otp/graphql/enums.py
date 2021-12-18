from enum import Enum

import graphene


class OTPErrorCode(Enum):
    INVALID = "invalid_otp_supplied"
    MISSING_CHANNEL_SLUG = "missing_channel_slug"


OTPErrorCodeType = graphene.Enum.from_enum(OTPErrorCode)
