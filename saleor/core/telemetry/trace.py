import logging
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

from opentelemetry.trace import (
    INVALID_SPAN,
    Link,
    Span,
    SpanKind,
    get_current_span,
    get_tracer,
)
from opentelemetry.util.types import Attributes

from ... import __version__ as saleor_version
from .utils import CORE_SCOPE, SERVICE_SCOPE, enrich_with_global_attributes

logger = logging.getLogger(__name__)


class Tracer:
    def __init__(self):
        self._core_tracer = get_tracer(CORE_SCOPE, saleor_version)
        self._service_tracer = get_tracer(SERVICE_SCOPE, saleor_version)

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        *,
        service_scope: bool = False,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
        end_on_exit: bool = True,
    ) -> Iterator[Span]:
        attributes = enrich_with_global_attributes(attributes)
        tracer = self._service_tracer if service_scope else self._core_tracer
        with tracer.start_as_current_span(
            name,
            kind=kind,
            attributes=attributes,
            links=links,
            start_time=start_time,
            record_exception=record_exception,
            set_status_on_exception=set_status_on_exception,
            end_on_exit=end_on_exit,
        ) as span:
            yield span

    def start_span(
        self,
        name: str,
        *,
        service_scope: bool = False,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
    ) -> Span:
        attributes = enrich_with_global_attributes(attributes)
        tracer = self._service_tracer if service_scope else self._core_tracer
        return tracer.start_span(
            name,
            kind=kind,
            attributes=attributes,
            links=links,
            start_time=start_time,
            record_exception=record_exception,
            set_status_on_exception=set_status_on_exception,
        )

    def get_current_span(self) -> Span:
        return get_current_span()


class TracerProxy(Tracer):
    def __init__(self):
        self._tracer: Tracer | None = None

    def initialize(self, tracer_cls: type[Tracer]):
        if self._tracer is not None:
            logger.warning("Tracer already initialized")
        self._tracer = tracer_cls()

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        *,
        service_scope: bool = False,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
        end_on_exit: bool = True,
    ) -> Iterator[Span]:
        if self._tracer is None:
            yield INVALID_SPAN
        else:
            with self._tracer.start_as_current_span(
                name,
                service_scope=service_scope,
                kind=kind,
                attributes=attributes,
                links=links,
                start_time=start_time,
                record_exception=record_exception,
                set_status_on_exception=set_status_on_exception,
                end_on_exit=end_on_exit,
            ) as span:
                yield span

    def start_span(
        self,
        name: str,
        *,
        service_scope: bool = False,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
    ) -> Span:
        if self._tracer is None:
            return INVALID_SPAN
        return self._tracer.start_span(
            name,
            service_scope=service_scope,
            kind=kind,
            attributes=attributes,
            links=links,
            start_time=start_time,
            record_exception=record_exception,
            set_status_on_exception=set_status_on_exception,
        )

    def get_current_span(self) -> Span:
        if self._tracer is None:
            return INVALID_SPAN
        return self._tracer.get_current_span()
