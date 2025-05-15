from collections.abc import Mapping

from ..metric import Meter
from ..trace import Tracer


class TestTracer(Tracer):
    _inject_context = False

    def inject_context(self, carrier: Mapping[str, str | list[str]]):
        if self._inject_context:
            super().inject_context(carrier)


class TestMeter(Meter):
    pass
