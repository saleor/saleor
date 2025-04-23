from contextlib import AbstractContextManager

from opentelemetry.semconv._incubating.attributes import graphql_attributes
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.util.types import AttributeValue

from ..core.telemetry import MetricType, Scope, Unit, meter, saleor_attributes

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
    operation_name: str = "",
    operation_type: str = "",
    operation_identifier: str = "",
    amount: int = 1,
    error_type: str | None = None,
) -> None:
    attributes = {
        saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: operation_identifier,
        graphql_attributes.GRAPHQL_OPERATION_NAME: operation_name,
        graphql_attributes.GRAPHQL_OPERATION_TYPE: operation_type,
    }
    if error_type:
        attributes[error_attributes.ERROR_TYPE] = error_type
    meter.record(
        METRIC_GRAPHQL_QUERY_COUNT, amount, Unit.REQUEST, attributes=attributes
    )


def record_graphql_query_duration() -> AbstractContextManager[
    dict[str, AttributeValue]
]:
    attributes: dict[str, AttributeValue] = {
        graphql_attributes.GRAPHQL_OPERATION_NAME: "",
        graphql_attributes.GRAPHQL_OPERATION_TYPE: "",
        saleor_attributes.GRAPHQL_OPERATION_IDENTIFIER: "",
    }
    return meter.record_duration(METRIC_GRAPHQL_QUERY_DURATION, attributes=attributes)
