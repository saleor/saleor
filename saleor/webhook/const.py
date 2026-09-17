from enum import StrEnum

WEBHOOK_CACHE_DEFAULT_TTL: int = 5 * 60  # 5 minutes
SYNC_WEBHOOK_FAILURE_CACHE_TTL: int = 1  # 1 second
SYNC_WEBHOOK_FAILURE_SENTINEL = (
    "WEBHOOK_FAILURE"  # Arbitrary value to indicate webhook failure in cache
)
APP_ID_PREFIX = "app"

MAX_FILTERABLE_CHANNEL_SLUGS_LIMIT = 500

# How long a single dropped-payload report suppresses further reports for a webhook.
WEBHOOK_PAYLOAD_ERROR_PROBLEM_TTL: int = 60 * 60  # 1 hour
# Window, in minutes, within which consecutive reports bump the same problem instead of
# creating a new one. Must comfortably exceed the reporting TTL above so that a webhook
# broken for days keeps a single problem whose count tracks how long it has been broken.
WEBHOOK_PAYLOAD_ERROR_PROBLEM_AGGREGATION_PERIOD: int = 24 * 60  # 1 day


class WebhookPayloadErrorReason(StrEnum):
    """Reason why a webhook payload could not be generated and the event was dropped."""

    INVALID_SUBSCRIPTION_QUERY = "invalid_subscription_query"
    EMPTY_PAYLOAD = "empty_payload"
