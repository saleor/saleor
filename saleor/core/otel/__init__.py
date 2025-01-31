from opentelemetry import trace

from ... import __version__
from .context import ContextAwareTracer

SCOPE = "saleor.tracer"
PUBLIC_SCOPE = "saleor.tracer.public"
# Create a global tracer instances
tracer = ContextAwareTracer.wrap(trace.get_tracer(SCOPE, __version__))
public_tracer = ContextAwareTracer.wrap(trace.get_tracer(PUBLIC_SCOPE, __version__))
