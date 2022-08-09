from typing import Optional

from .payload_schema import ObservabilityEventTypes


class ObservabilityError(Exception):
    pass


class ConnectionNotConfigured(ObservabilityError):
    pass


class TruncationError(ObservabilityError):
    _event_type: Optional[ObservabilityEventTypes] = None

    def __init__(self, operation: str, bytes_limit: int, payload_size: int, **kwargs):
        self.extra = {
            "observability_event_type": self._event_type,
            "operation": operation,
            "bytes_limit": bytes_limit,
            "payload_size": payload_size,
            **kwargs,
        }
        super().__init__(self.__str__())

    def __str__(self):
        return (
            f"Event {self.extra['observability_event_type']}"
            f" truncation error at {self.extra['operation']!r}."
        )


class ApiCallTruncationError(TruncationError):
    _event_type = ObservabilityEventTypes.API_CALL


class EventDeliveryAttemptTruncationError(TruncationError):
    _event_type = ObservabilityEventTypes.EVENT_DELIVERY_ATTEMPT
