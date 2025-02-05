import time
from collections.abc import Generator
from contextlib import contextmanager

from opentelemetry.metrics import Histogram
from opentelemetry.util.types import AttributeValue

from .metrics import get_meter
from .trace import get_tracer

INTERNAL_SCOPE = "saleor.internal"
PUBLIC_SCOPE = "saleor.tracer.public"
# Create a global tracer instances
tracer = get_tracer(INTERNAL_SCOPE)
public_tracer = get_tracer(PUBLIC_SCOPE)

internal_meter = get_meter(INTERNAL_SCOPE)
public_meter = get_meter(PUBLIC_SCOPE)


@contextmanager
def report_duration_ms(
    instrument: Histogram,
) -> Generator[dict[str, AttributeValue], None, None]:
    start = time.monotonic_ns()
    attributes: dict[str, AttributeValue] = {}
    try:
        yield attributes
    finally:
        duration_ms = (time.monotonic_ns() - start) / 1_000_000
        instrument.record(duration_ms, attributes=attributes)
