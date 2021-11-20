from enum import Enum


class ExternalNotificationErrorCodes(Enum):
    REQUIRED = "required"
    INVALID_MODEL_TYPE = "invalid_model_type"
    NOT_FOUND = "not_found"
    CHANNEL_INACTIVE = "channel_inactive"
