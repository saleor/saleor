from ... import __version__
from .metrics import Meter, MetricType
from .trace import Tracer

INTERNAL_SCOPE = "saleor.internal"
PUBLIC_SCOPE = "saleor.tracer.public"

tracer = Tracer(INTERNAL_SCOPE, PUBLIC_SCOPE, __version__)
meter = Meter(INTERNAL_SCOPE, PUBLIC_SCOPE, __version__)

meter.create_instrument(
    "saleor.graphql_queries", MetricType.Counter, internal=False, unit="{request}"
)
meter.create_instrument(
    "saleor.graphql_query_duration", MetricType.Histogram, internal=False, unit="ms"
)
