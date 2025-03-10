from contextlib import AbstractContextManager

from ..core.telemetry import AttributeValue, MetricType, Scope, Unit, meter

# Initialize metrics
METRIC_GRAPHQL_QUERIES = meter.create_metric(
    "saleor.graphql_queries",
    scope=Scope.SERVICE,
    type=MetricType.COUNTER,
    unit=Unit.REQUEST,
    description="Number of GraphQL queries.",
)
METRIC_GRAPHQL_QUERY_DURATION = meter.create_metric(
    "saleor.graphql_query_duration",
    scope=Scope.SERVICE,
    type=MetricType.HISTOGRAM,
    unit=Unit.MILLISECOND,
    description="Duration of GraphQL queries.",
)


# Helper functions
def record_graphql_queries_count(amount: int = 1) -> None:
    meter.record(METRIC_GRAPHQL_QUERIES, amount)


def record_graphql_query_duration() -> AbstractContextManager[
    dict[str, AttributeValue]
]:
    return meter.record_duration(METRIC_GRAPHQL_QUERY_DURATION)
