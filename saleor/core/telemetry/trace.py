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

from .utils import Scope, enrich_with_global_attributes

logger = logging.getLogger(__name__)


class Tracer:
    """Interface for instrumenting code with distributed tracing.

    The class provides an interface for creating and managing trace spans.
    This default implementation uses OpenTelemetry to provide that but can be easily
    subclassed to alter or change the telemetry implementation.

    The Tracer operates with two distinct scopes:
        - CORE: For internal system operations and core functionality
        - SERVICE: For business logic and service-level operations

    Note:
        The Tracer internally uses the global OpenTelemetry TracerProvider, which should
        be initialized following OpenTelemetry's standard process, for example using
        the `opentelemetry-instrument` tool.

    """

    def __init__(self, instrumentation_version: str):
        self._core_tracer = get_tracer(Scope.CORE.value, instrumentation_version)
        self._service_tracer = get_tracer(Scope.SERVICE.value, instrumentation_version)

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        *,
        scope: Scope = Scope.CORE,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
        end_on_exit: bool = True,
    ) -> Iterator[Span]:
        """Start a new span and set it as the current span in the context.

        Args:
            name: The name of the span
            scope: The scope of the span, defaults to Scope.CORE
            kind: The SpanKind of the span
            attributes: Initial attributes for the span
            links: Links to other spans
            start_time: Optional start time for the span in nanoseconds
            record_exception: Whether to record exceptions as span events
            set_status_on_exception: Whether to set span status on exception
            end_on_exit: Whether to end the span when exiting the context

        Yields:
            The newly created span

        """
        attributes = enrich_with_global_attributes(attributes)
        tracer = self._service_tracer if scope.is_service else self._core_tracer
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
        scope: Scope = Scope.CORE,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Attributes = None,
        links: Sequence[Link] | None = None,
        start_time: int | None = None,
        record_exception: bool = True,
        set_status_on_exception: bool = True,
    ) -> Span:
        """Create a new span without setting it as current in the context.

        Args:
            name: The name of the span
            scope: The scope of the span, defaults to Scope.CORE
            kind: The SpanKind of the span
            attributes: Initial attributes for the span
            links: Links to other spans
            start_time: Optional start time for the span in nanoseconds
            record_exception: Whether to record exceptions as span events
            set_status_on_exception: Whether to set span status on exception

        Returns:
            The newly created span

        """
        attributes = enrich_with_global_attributes(attributes)
        tracer = self._service_tracer if scope.is_service else self._core_tracer
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
        """Return the current span from the context."""
        return get_current_span()


class TracerProxy(Tracer):
    """A proxy that enables delayed initialization of Tracer.

    This class is designed to ensure fork safety in multi-process environments by
    allowing Tracer initialization to be deferred until after process forking.
    """

    def __init__(self):
        self._tracer: Tracer | None = None

    def initialize(self, tracer_cls: type[Tracer], instrumentation_version: str):
        if self._tracer is not None:
            logger.warning("Tracer already initialized")
        self._tracer = tracer_cls(instrumentation_version)

    @contextmanager
    def start_as_current_span(
        self,
        name: str,
        *,
        scope: Scope = Scope.CORE,
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
                scope=scope,
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
        scope: Scope = Scope.CORE,
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
            scope=scope,
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
