import time
from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager

from django.conf import settings
from opentelemetry.semconv._incubating.attributes import graphql_attributes
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.util.types import AttributeValue

from ..core.telemetry import (
    DEFAULT_DURATION_BUCKETS,
    MetricType,
    Scope,
    Unit,
    meter,
    saleor_attributes,
)

# Initialize metrics
METRIC_GRAPHQL_QUERY_COUNT = meter.create_metric(
    "saleor.graphql.operation.count",
    scope=Scope.SERVICE,
    type=MetricType.COUNTER,
    unit=Unit.REQUEST,
    description="Number of GraphQL queries.",
)

METRIC_GRAPHQL_QUERY_DURATION = meter.create_metric(
    "saleor.graphql.operation.duration",
    scope=Scope.SERVICE,
    type=MetricType.HISTOGRAM,
    unit=Unit.SECOND,
    description="Duration of GraphQL queries.",
    bucket_boundaries=DEFAULT_DURATION_BUCKETS,
)

METRIC_GRAPHQL_SLOW_OPERATION_DURATION = meter.create_metric(
    "saleor.graphql.slow_operation.duration",
    scope=Scope.CORE,
    type=MetricType.HISTOGRAM,
    unit=Unit.SECOND,
    description="Duration of slow GraphQL operations.",
    bucket_boundaries=DEFAULT_DURATION_BUCKETS,
)

QUERY_COST_BUCKETS = [
    0,
    5,
    10,
    25,
    50,
    100,
    250,
    500,
    1000,
    2000,
    5000,
    10000,
    15000,
    20000,
    30000,
    50000,
]
METRIC_GRAPHQL_QUERY_COST = meter.create_metric(
    "saleor.graphql.operation.cost",
    scope=Scope.SERVICE,
    type=MetricType.HISTOGRAM,
    unit=Unit.COST,
    description="Cost of GraphQL queries.",
    bucket_boundaries=QUERY_COST_BUCKETS,
)

METRIC_REQUEST_COUNT = meter.create_metric(
    "saleor.request.count",
    scope=Scope.SERVICE,
    type=MetricType.COUNTER,
    unit=Unit.REQUEST,
    description="Number of API requests.",
)

METRIC_REQUEST_DURATION = meter.create_metric(
    "saleor.request.duration",
    scope=Scope.SERVICE,
    type=MetricType.HISTOGRAM,
    unit=Unit.SECOND,
    description="Duration of API requests.",
    bucket_boundaries=DEFAULT_DURATION_BUCKETS,
)


# Helper functions
def record_graphql_query_count(
    amount: int = 1,
    *,
    operation_type: str | None = "",
    error_type: str | None = None,
) -> None:
    attributes = {graphql_attributes.GRAPHQL_OPERATION_TYPE: operation_type or ""}
    if error_type:
        attributes[error_attributes.ERROR_TYPE] = error_type
    meter.record(
        METRIC_GRAPHQL_QUERY_COUNT, amount, Unit.REQUEST, attributes=attributes
    )


@contextmanager
def record_graphql_query_duration() -> Iterator[dict[str, AttributeValue]]:
    start = time.monotonic()
    attributes: dict[str, AttributeValue] = {
        graphql_attributes.GRAPHQL_OPERATION_TYPE: ""
    }
    try:
        yield attributes
    finally:
        duration = time.monotonic() - start
        if duration >= settings.TELEMETRY_SLOW_GRAPHQL_OPERATION_THRESHOLD:
            meter.record(
                METRIC_GRAPHQL_SLOW_OPERATION_DURATION,
                duration,
                unit=Unit.SECOND,
                attributes=attributes,
            )
        # Set graphql.document_fingerprint attribute only for slow operations metric
        attributes.pop(saleor_attributes.GRAPHQL_DOCUMENT_FINGERPRINT, None)
        meter.record(
            METRIC_GRAPHQL_QUERY_DURATION,
            duration,
            unit=Unit.SECOND,
            attributes=attributes,
        )


def record_graphql_query_cost(
    cost: int,
    *,
    operation_type: str | None = "",
    error_type: str | None = None,
) -> None:
    attributes = {graphql_attributes.GRAPHQL_OPERATION_TYPE: operation_type or ""}
    if error_type:
        attributes[error_attributes.ERROR_TYPE] = error_type
    meter.record(METRIC_GRAPHQL_QUERY_COST, cost, Unit.COST, attributes=attributes)


def record_request_count(
    amount: int = 1,
    error_type: str | None = None,
) -> None:
    attributes = {}
    if error_type:
        attributes[error_attributes.ERROR_TYPE] = error_type
    meter.record(METRIC_REQUEST_COUNT, amount, Unit.REQUEST, attributes=attributes)


def record_request_duration() -> AbstractContextManager[dict[str, AttributeValue]]:
    attributes: dict[str, AttributeValue] = {}
    return meter.record_duration(METRIC_REQUEST_DURATION, attributes=attributes)
