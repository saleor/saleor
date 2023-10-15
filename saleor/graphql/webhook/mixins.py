from django.core.exceptions import ValidationError

from ...webhook.error_codes import WebhookErrorCode
from ...webhook.event_types import WebhookEventAsyncType


class NotifyUserEventValidationMixin:
    @classmethod
    def validate_events(cls, events):
        # NOTIFY_USER needs to be the only one event registered per webhook.
        # This solves issue temporarily. NOTIFY_USER will be deprecated in the future.
        if WebhookEventAsyncType.NOTIFY_USER in events and len(events) > 1:
            raise ValidationError(
                {
                    "async_events": ValidationError(
                        "The NOTIFY_USER webhook cannot be combined with other events.",
                        code=WebhookErrorCode.INVALID_NOTIFY_WITH_SUBSCRIPTION.value,
                    )
                }
            )
        return events
