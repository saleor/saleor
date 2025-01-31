from .metrics import get_meter
from .trace import get_tracer

INTERNAL_SCOPE = "saleor.internal"
PUBLIC_SCOPE = "saleor.tracer.public"
# Create a global tracer instances
tracer = get_tracer(INTERNAL_SCOPE)
public_tracer = get_tracer(PUBLIC_SCOPE)

internal_meter = get_meter(INTERNAL_SCOPE)
public_meter = get_meter(PUBLIC_SCOPE)
