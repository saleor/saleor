from typing import cast

from opentelemetry import metrics
from opentelemetry.metrics import Meter
from opentelemetry.util.types import Attributes

from ... import __version__
from .context import enrich_with_trace_attributes


class _ContextAwareMeter(Meter):
    _NOT_IMPLEMENTED_MSG = "Observable instruments are not supported"

    def __init__(self, meter: Meter):
        self._meter = meter

    @staticmethod
    def _wrapp(original_method):
        def wrapper(amount, attributes: Attributes = None, *args, **kwargs):
            attributes = enrich_with_trace_attributes(attributes)
            return original_method(amount, attributes, *args, **kwargs)

        return wrapper

    def create_counter(self, *args, **kwargs):
        counter = self._meter.create_counter(*args, **kwargs)
        setattr(counter, "add", self._wrapp(counter.add))
        return counter

    def create_up_down_counter(self, *args, **kwargs):
        counter = self._meter.create_up_down_counter(*args, **kwargs)
        setattr(counter, "add", self._wrapp(counter.add))
        return counter

    def create_histogram(self, *args, **kwargs):
        histogram = self._meter.create_histogram(*args, **kwargs)
        setattr(histogram, "record", self._wrapp(histogram.record))
        return histogram

    def create_observable_counter(self, *args, **kwargs):
        raise NotImplementedError(self._NOT_IMPLEMENTED_MSG)

    def create_observable_up_down_counter(self, *args, **kwargs):
        raise NotImplementedError(self._NOT_IMPLEMENTED_MSG)

    def create_observable_gauge(self, *args, **kwargs):
        raise NotImplementedError(self._NOT_IMPLEMENTED_MSG)


def get_meter(scope_name: str) -> Meter:
    meter = metrics.get_meter(scope_name, __version__)
    return cast(Meter, _ContextAwareMeter(meter))
