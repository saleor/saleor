from urllib.parse import urlparse

from opentelemetry.semconv.attributes import error_attributes, server_attributes

from ...core.models import EventDeliveryStatus
from ...core.telemetry import MetricType, Scope, Unit, meter
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
)
METRIC_EXTERNAL_REQUEST_BODY_SIZE = meter.create_metric(
    "saleor.external_request.body.size",
    scope=Scope.SERVICE,
    type=MetricType.HISTOGRAM,
    unit=Unit.BYTE,
    description="Size of webhook event payloads.",
)


def record_external_request(
    target_url: str, webhook_response: WebhookResponse, payload_size: int
) -> None:
    attributes = {server_attributes.SERVER_ADDRESS: urlparse(target_url).hostname or ""}
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
