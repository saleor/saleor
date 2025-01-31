from typing import cast

from opentelemetry import metrics
from opentelemetry.metrics import Meter, Synchronous
from opentelemetry.util.types import Attributes

from ... import __version__
from .context import enrich_with_trace_attributes


class _ContextAwareSyncInstrument:
    def __init__(self, instrument: Synchronous):
        self._instrument = instrument

    def add(self, amount, attributes: Attributes = None, **kwargs):
        attributes = enrich_with_trace_attributes(attributes)
        return getattr(self._instrument, "add")(amount, attributes, **kwargs)

    def record(self, amount, attributes: Attributes = None, **kwargs):
        attributes = enrich_with_trace_attributes(attributes)
        return getattr(self._instrument, "record")(amount, attributes, **kwargs)


class _ContextAwareMeter(Meter):
    _NOT_IMPLEMENTED_MSG = "Observable instruments are not supported"

    def __init__(self, meter: Meter):
        self._meter = meter

    def create_counter(self, *args, **kwargs):
        return _ContextAwareSyncInstrument(self._meter.create_counter(*args, **kwargs))

    def create_up_down_counter(self, *args, **kwargs):
        return _ContextAwareSyncInstrument(
            self._meter.create_up_down_counter(*args, **kwargs)
        )

    def create_histogram(self, *args, **kwargs):
        return _ContextAwareSyncInstrument(
            self._meter.create_histogram(*args, **kwargs)
        )

    def create_observable_counter(self, *args, **kwargs):
        raise NotImplementedError(self._NOT_IMPLEMENTED_MSG)

    def create_observable_up_down_counter(self, *args, **kwargs):
        raise NotImplementedError(self._NOT_IMPLEMENTED_MSG)

    def create_observable_gauge(self, *args, **kwargs):
        raise NotImplementedError(self._NOT_IMPLEMENTED_MSG)


def get_meter(scope_name: str) -> Meter:
    meter = metrics.get_meter(scope_name, __version__)
    return cast(Meter, _ContextAwareMeter(meter))
