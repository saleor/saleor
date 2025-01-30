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
