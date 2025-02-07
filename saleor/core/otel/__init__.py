from django.conf import settings
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Create an internal tracer instance. With `DD_TRACE_OTEL_ENABLED` env variable set,
# this will be Datadog's OpenTelemetry tracer.
tracer = trace.get_tracer(__name__)


# Create a public tracer instance for manually instrumenting signals for public.
public_tracer_provider = TracerProvider(
    resource=Resource.create({"service.name": "saleor"})
)
public_tracer_provider.add_span_processor(
    BatchSpanProcessor(OTLPSpanExporter(settings.OTEL_PUBLIC_ENDPOINT))
)
public_tracer = trace.get_tracer(
    "saleor.public", tracer_provider=public_tracer_provider
)


def get_span_link_data(span: trace.Span) -> dict | None:
    """Get the data to create a link from the given span.

    Args:
        span (trace.Span): The span to get the link data from.

    Return:
        dict: The span link data.

    """

    span_ctx = span.get_span_context()
    return {
        "trace_id": span_ctx.trace_id,
        "span_id": span_ctx.span_id,
        "is_remote": False,
    }


def create_span_link(link_span_data: dict | None) -> list[trace.Link]:
    """Create a span link from the given data.

    Args:
        link_span_data (dict): The data to create a span link from.

    Return:
        list: A list of span links.

    """

    if not link_span_data:
        return []

    links = []
    link_span_ctx = trace.SpanContext(**link_span_data)
    links = [trace.Link(link_span_ctx)]
    return links
