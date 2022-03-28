from contextlib import contextmanager
from typing import Generator, List, Optional, cast

import opentracing
from django.conf import settings
from django.core.cache import cache
from kombu import Connection, Exchange, Queue, pools
from kombu.exceptions import ChannelError, KombuError
from kombu.simple import SimpleQueue

from .exceptions import (
    FullObservabilityBuffer,
    ObservabilityConnectionError,
    ObservabilityKombuError,
)

OBSERVABILITY_EXCHANGE_NAME = "observability_exchange"
CACHE_KEY = "observability_buffer"
EXCHANGE = Exchange(OBSERVABILITY_EXCHANGE_NAME, type="direct")
CONNECT_TIMEOUT = 0.2
DRAIN_EVENTS_TIMEOUT = 10.0


class ObservabilityBuffer(SimpleQueue):
    no_ack = True

    @staticmethod
    def _queue_name() -> str:
        return cache.make_key(CACHE_KEY)

    @staticmethod
    def _routing_key() -> str:
        return f"{OBSERVABILITY_EXCHANGE_NAME}.buffer.{cache.make_key('')}"

    def __init__(
        self,
        channel,
        batch_size: int = 10,
        max_size: int = 100,
    ):
        self.queue_name = self._queue_name()
        queue = Queue(self.queue_name, EXCHANGE, routing_key=self._routing_key())
        super().__init__(channel, queue)
        self.batch_size = max(0, batch_size)
        self.max_size = max(0, max_size)

    def get(self, block=True, timeout=DRAIN_EVENTS_TIMEOUT):
        return super().get(block=block, timeout=timeout)

    def qsize(self):
        try:
            return super().qsize()
        except ChannelError:
            # Let's suppose that queue size is 0 if it not exists
            return 0

    def __repr__(self):
        return f"ObservabilityBuffer('{self.queue_name}')"

    def put_event(self, json_str: str):
        if len(self) >= self.max_size:
            raise FullObservabilityBuffer(self)
        self.put(
            json_str,
            retry=False,
            timeout=CONNECT_TIMEOUT,
            content_type="application/json",
            compression="zlib",
        )

    def get_events(self, timeout=DRAIN_EVENTS_TIMEOUT) -> List[dict]:
        self.consumer.qos(prefetch_count=self.batch_size)
        events: List[dict] = []
        for _ in range(self.batch_size):
            try:
                message = self.get(timeout=timeout)
                events.append(cast(dict, message.decode()))
            except self.Empty:
                break
        return events


def broker_connection() -> Connection:
    return Connection(
        settings.OBSERVABILITY_BROKER_URL, connect_timeout=CONNECT_TIMEOUT
    )


@contextmanager
def observability_connection(
    connection: Optional[Connection] = None,
) -> Generator[Connection, None, None]:
    conn = connection if connection else broker_connection()
    conn_errors = conn.connection_errors + conn.channel_errors
    try:
        connection = pools.connections[conn].acquire(block=False)
        yield connection
    except conn_errors as err:
        raise ObservabilityConnectionError() from err
    except KombuError as err:
        raise ObservabilityKombuError() from err
    finally:
        if connection:
            connection.release()


@contextmanager
def observability_buffer() -> Generator[ObservabilityBuffer, None, None]:
    with observability_connection() as conn:
        with ObservabilityBuffer(
            conn,
            batch_size=settings.OBSERVABILITY_BUFFER_BATCH_SIZE,
            max_size=settings.OBSERVABILITY_BUFFER_SIZE_LIMIT,
        ) as buffer:
            yield buffer


def _opentracing(func):
    def wrapper(*args, **kwargs):
        operation = f"observability_{func.__name__}"
        tracer = opentracing.global_tracer()
        with tracer.start_active_span(operation) as scope:
            scope.span.set_tag(opentracing.tags.COMPONENT, "observability")
            return func(*args, **kwargs)

    return wrapper


@_opentracing
def put_event(json_payload: str):
    with observability_buffer() as buffer:
        buffer.put_event(json_payload)


@_opentracing
def get_events(timeout=DRAIN_EVENTS_TIMEOUT) -> List[dict]:
    with observability_buffer() as buffer:
        return buffer.get_events(timeout=timeout)


@_opentracing
def buffer_size() -> int:
    with observability_buffer() as buffer:
        return len(buffer)
