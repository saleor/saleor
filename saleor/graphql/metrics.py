from contextlib import AbstractContextManager

from opentelemetry.util.types import AttributeValue

from ..core.telemetry import MetricType, Scope, Unit, meter
from ..core.telemetry.attributes import (
    SALEOR_GRAPHQL_IDENTIFIER,
    SALEOR_GRAPHQL_OPERATION_TYPE,
)

# Initialize metrics
METRIC_GRAPHQL_QUERY_COUNT = meter.create_metric(
    "saleor.graphql.query_count",
    scope=Scope.SERVICE,
    type=MetricType.COUNTER,
    unit=Unit.REQUEST,
    description="Number of GraphQL queries.",
)
METRIC_GRAPHQL_QUERY_DURATION = meter.create_metric(
    "saleor.graphql.query_duration",
    scope=Scope.SERVICE,
    type=MetricType.HISTOGRAM,
    unit=Unit.MILLISECOND,
    description="Duration of GraphQL queries.",
)
METRIC_GRAPHQL_QUERY_COST = meter.create_metric(
    "saleor.graphql.query_cost",
    scope=Scope.SERVICE,
    type=MetricType.HISTOGRAM,
    unit=Unit.REQUEST,
    description="Cost of GraphQL queries.",
)


# Helper functions
def record_graphql_query_count(
    identifier: str, operation_type: str, amount: int = 1
) -> None:
    attributes = {
        SALEOR_GRAPHQL_IDENTIFIER: identifier,
        SALEOR_GRAPHQL_OPERATION_TYPE: operation_type,
    }
    meter.record(
        METRIC_GRAPHQL_QUERY_COUNT, amount, Unit.REQUEST, attributes=attributes
    )


def record_graphql_query_duration() -> AbstractContextManager[
    dict[str, AttributeValue]
]:
    return meter.record_duration(METRIC_GRAPHQL_QUERY_DURATION)
