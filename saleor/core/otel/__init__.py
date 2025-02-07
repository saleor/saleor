from ... import __version__
from .metrics import Meter, MetricType
from .trace import Tracer

INTERNAL_SCOPE = "saleor.internal"
PUBLIC_SCOPE = "saleor.tracer.public"

tracer = Tracer(INTERNAL_SCOPE, PUBLIC_SCOPE, __version__)
meter = Meter(INTERNAL_SCOPE, PUBLIC_SCOPE, __version__)

__all__ = [
    "tracer",
    "meter",
    "MetricType",
]
