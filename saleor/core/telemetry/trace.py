from abc import ABC, abstractmethod
from collections.abc import Iterator, Sequence
from contextlib import AbstractContextManager, contextmanager
from typing import TypedDict

from django.conf import settings
from opentelemetry.trace import INVALID_SPAN, Link, Span, SpanKind
from opentelemetry.util.types import Attributes

from .utils import enrich_with_global_attributes, load_object


class SpanConfig(TypedDict):
    kind: SpanKind
    attributes: Attributes
    links: Sequence[Link] | None
    start_time: int | None
    record_exception: bool
    set_status_on_exception: bool


class Tracer(ABC):
    def start_as_current_span(
        self,
        name: str,
        *,
        service: bool = False,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
        end_on_exit: bool = True,
    ) -> AbstractContextManager[Span]:
        attributes = enrich_with_global_attributes(attributes)
        span_config = SpanConfig(
            kind=kind,
            attributes=attributes,
            links=links,
            start_time=start_time,
            record_exception=record_exception,
            set_status_on_exception=set_status_on_exception,
        )
        return self._start_as_current_span(name, service, span_config, end_on_exit)

    @abstractmethod
    def _start_as_current_span(
        self, name: str, service: bool, span_config: SpanConfig, end_on_exit: bool
    ) -> AbstractContextManager[Span]:
        pass

    def start_span(
        self,
        name: str,
        *,
        service: bool = False,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
    ) -> Span:
        attributes = enrich_with_global_attributes(attributes)
        span_config = SpanConfig(
            kind=kind,
            attributes=attributes,
            links=links,
            start_time=start_time,
            record_exception=record_exception,
            set_status_on_exception=set_status_on_exception,
        )
        return self._start_span(name, service, span_config)

    @abstractmethod
    def _start_span(self, name: str, service: bool, span_config: SpanConfig) -> Span:
        pass

    @abstractmethod
    def get_current_span(self) -> Span:
        pass


def load_tracer() -> type[Tracer]:
    tracer_cls = load_object(settings.TELEMETRY_TRACER_CLASS)
    if not issubclass(tracer_cls, Tracer):
        raise ValueError(
            "settings.TELEMETRY_TRACER_CLASS must point to a subclass of Tracer"
        )
    return tracer_cls


class TracerProxy(Tracer):
    def __init__(self):
        self._tracer: Tracer | None = None

    def initialize(self, tracer_cls: type[Tracer]):
        if self._tracer is not None:
            raise RuntimeError("Tracer already initialized")
        self._tracer = tracer_cls()

    @contextmanager
    def _start_as_current_span(self, *args, **kwargs) -> Iterator[Span]:
        if self._tracer is None:
            yield INVALID_SPAN
        else:
            with self._tracer._start_as_current_span(*args, **kwargs) as span:
                yield span

    def _start_span(self, *args, **kwargs) -> Span:
        if self._tracer is None:
            return INVALID_SPAN
        return self._tracer._start_span(*args, **kwargs)

    def get_current_span(self) -> Span:
        if self._tracer is None:
            return INVALID_SPAN
        return self._tracer.get_current_span()
