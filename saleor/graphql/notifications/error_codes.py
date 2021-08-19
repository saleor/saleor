from enum import Enum


class ExternalNotificationErrorCodes(Enum):
    INPUT_MISSING = "lack_of_input"
    IDS_MISSING = "lack_of_ids"
    EXTERNAL_EVENT_TYPE_MISSING = "lack_of_external_event_type"
