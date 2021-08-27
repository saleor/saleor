from enum import Enum


class ExternalNotificationErrorCodes(Enum):
    REQUIRED = "required"
    INVALID_MODEL_TYPE = "invalid_model_type"
    INVALID_CHANNEL_NAME = "invalid_channel_name"
    CHANNEL_INACTIVE = "channel_inactive"
