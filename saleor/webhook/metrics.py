from datetime import UTC, datetime

from ..core.models import EventDelivery
from ..core.telemetry import MetricType, Scope, Unit, meter

# Initialize metrics
METRIC_FIRST_EVENT_DELIVERY_ATTEMPT_DELAY = meter.create_metric(
    "saleor.webhooks.async.first_event_delivery_attempt_delay",
    scope=Scope.CORE,
    type=MetricType.HISTOGRAM,
    unit=Unit.MILLISECOND,
    description="Delay for the first attempt of delivering async webhook event after creation of EventDelivery.",
)

METRIC_ASYNC_WEBHOOK_CALLS = meter.create_metric(
    "saleor.webhooks.async.calls",
    scope=Scope.CORE,
    type=MetricType.COUNTER,
    unit=Unit.REQUEST,
    description="Number of async webhook calls.",
)


def record_first_delivery_attempt_delay(event_delivery: EventDelivery) -> None:
    delay = (datetime.now(UTC) - event_delivery.created_at).total_seconds()
    attributes = {
        "app.name": event_delivery.webhook.app.name,
        "event_type": event_delivery.event_type,
    }
    meter.record(
        METRIC_FIRST_EVENT_DELIVERY_ATTEMPT_DELAY,
        delay,
        unit=Unit.SECOND,
        attributes=attributes,
    )


def record_async_webhooks_count(
    event_delivery: EventDelivery, response_status: str, amount: int = 1
) -> None:
    attributes = {
        "app.name": event_delivery.webhook.app.name,
        "response_status": response_status,
    }
    meter.record(
        METRIC_ASYNC_WEBHOOK_CALLS, amount, unit=Unit.REQUEST, attributes=attributes
    )
