from datetime import UTC, datetime
from urllib.parse import urlparse

from opentelemetry.semconv.attributes import error_attributes, server_attributes

from ...app.models import App
from ...core.models import EventDeliveryStatus
from ...core.telemetry import (
    DEFAULT_DURATION_BUCKETS,
    MetricType,
    Scope,
    Unit,
    meter,
    saleor_attributes,
)
from .utils import WebhookResponse

# Initialize metrics
METRIC_EXTERNAL_REQUEST_COUNT = meter.create_metric(
    "saleor.external_request.count",
    scope=Scope.SERVICE,
    type=MetricType.COUNTER,
    unit=Unit.REQUEST,
    description="Number of webhook events.",
)
METRIC_EXTERNAL_REQUEST_DURATION = meter.create_metric(
    "saleor.external_request.duration",
    scope=Scope.SERVICE,
    type=MetricType.HISTOGRAM,
    unit=Unit.SECOND,
    description="Duration of webhook event delivery.",
    bucket_boundaries=DEFAULT_DURATION_BUCKETS,
)

BODY_SIZE_BUCKETS = [
    0,  # 0B
    100,  # 100B
    500,  # 500B
    1000,  # 1KB
    2000,  # 2KB
    4000,  # 4KB
    8000,  # 8KB
    16000,  # 16KB
    32000,  # 32KB
    64000,  # 64KB
    128000,  # 128KB
    256000,  # 256KB
    512000,  # 512KB
    1048576,  # 1MB
    2097152,  # 2MB
    4194304,  # 4MB
]
METRIC_EXTERNAL_REQUEST_BODY_SIZE = meter.create_metric(
    "saleor.external_request.body.size",
    scope=Scope.SERVICE,
    type=MetricType.HISTOGRAM,
    unit=Unit.BYTE,
    description="Size of webhook event payloads.",
    bucket_boundaries=BODY_SIZE_BUCKETS,
)

METRIC_EXTERNAL_REQUEST_FIRST_ATTEMPT_DELAY = meter.create_metric(
    "saleor.external_request.async.first_attempt_delay",
    scope=Scope.CORE,
    type=MetricType.HISTOGRAM,
    unit=Unit.MILLISECOND,
    description="Delay of the first delivery attempt for async webhook.",
)


def record_external_request(
    event_type: str,
    target_url: str,
    webhook_response: WebhookResponse,
    payload_size: int,
    app: App,
    sync: bool,
) -> None:
    attributes = {
        server_attributes.SERVER_ADDRESS: urlparse(target_url).hostname or "",
        saleor_attributes.SALEOR_WEBHOOK_EVENT_TYPE: event_type,
        saleor_attributes.SALEOR_WEBHOOK_EXECUTION_MODE: "sync" if sync else "async",
        saleor_attributes.SALEOR_APP_IDENTIFIER: app.identifier,
    }
    if webhook_response.status == EventDeliveryStatus.FAILED:
        attributes[error_attributes.ERROR_TYPE] = "request_error"
    meter.record(METRIC_EXTERNAL_REQUEST_COUNT, 1, Unit.REQUEST, attributes=attributes)
    meter.record(
        METRIC_EXTERNAL_REQUEST_BODY_SIZE,
        payload_size,
        Unit.BYTE,
        attributes=attributes,
    )
    meter.record(
        METRIC_EXTERNAL_REQUEST_DURATION,
        webhook_response.duration,
        Unit.SECOND,
        attributes=attributes,
    )


def record_first_delivery_attempt_delay(
    created_at: datetime, event_type: str, app: App
) -> None:
    delay = (datetime.now(UTC) - created_at).total_seconds()
    attributes = {
        saleor_attributes.SALEOR_WEBHOOK_EVENT_TYPE: event_type,
        saleor_attributes.SALEOR_APP_IDENTIFIER: app.identifier,
    }
    meter.record(
        METRIC_EXTERNAL_REQUEST_FIRST_ATTEMPT_DELAY,
        delay,
        unit=Unit.SECOND,
        attributes=attributes,
    )
