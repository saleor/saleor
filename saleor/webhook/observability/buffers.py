import zlib
from typing import Dict, List, Optional

from asgiref.local import Local
from django.conf import settings
from redis import ConnectionPool, Redis

from .exceptions import ConnectionDoesNotExist

_local = Local()


class BaseBuffer:
    _compressor_preset = 6

    def __init__(self, broker_url: str, max_size: int, batch_size: int):
        self._broker_url = broker_url
        self._max_size = max_size
        self._batch_size = batch_size

    def decode(self, value: bytes) -> str:
        return zlib.decompress(value).decode()

    def encode(self, value: str) -> bytes:
        return zlib.compress(value.encode(), self._compressor_preset)

    def put_event(self, key: str, event: str, retry=False):
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a put_event() method"
        )

    def put_events(self, key: str, events: List[str], retry=False) -> int:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a put_events() method"
        )

    def put_events_multi_buffer(
        self, events_dict: Dict[str, List[str]], retry=False
    ) -> Dict[str, int]:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a put_events_multi_buffer() method"
        )

    def pop_event(self, key) -> Optional[str]:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a pop_events() method"
        )

    def pop_events(self, key, batch_size=100) -> List[str]:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a pop_events() method"
        )

    def size(self, key: str) -> int:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a size() method"
        )


class RedisBuffer(BaseBuffer):
    _pools: Dict[str, ConnectionPool] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client: Optional[Redis] = None

    def get_connection_pool(self):
        return ConnectionPool.from_url(self._broker_url)

    def get_or_create_connection_pool(self):
        if self._broker_url not in self._pools:
            self._pools[self._broker_url] = self.get_connection_pool()
        return self._pools[self._broker_url]

    def connect(self) -> Redis:
        pool = self.get_or_create_connection_pool()
        return Redis(connection_pool=pool)

    @property
    def client(self) -> Redis:
        if not self._client:
            self._client = self.connect()
        return self._client

    def _put_events(
        self, key: str, events: List[bytes], client: Optional[Redis] = None
    ):
        if client is None:
            client = self.client
        client.lpush(key, *events)
        client.ltrim(key, 0, max(0, self._max_size - 1))

    def put_events(self, key: str, events: List[str], retry=False) -> int:
        events_data = [self.encode(event) for event in events]
        with self.client.pipeline(transaction=False) as pipe:
            self._put_events(key, events_data, client=pipe)
            result = pipe.execute()
        return max(0, result[0] - self._max_size)

    def put_event(self, key: str, event: str, retry=False):
        return self.put_events(key, [event])

    def put_events_multi_buffer(
        self, events_dict: Dict[str, List[str]], retry=False
    ) -> Dict[str, int]:
        keys = list(events_dict.keys())
        trimmed: Dict[str, int] = {}
        if not keys:
            return trimmed
        with self.client.pipeline(transaction=False) as pipe:
            for key in keys:
                events_data = [self.encode(event) for event in events_dict[key]]
                self._put_events(key, events_data, client=pipe)
            result = pipe.execute()
        for key in keys:
            buffer_len, _ = result.pop(0), result.pop(0)
            trimmed[key] = max(0, buffer_len - self._max_size)
        return trimmed

    def pop_events(self, key, batch_size=100) -> List[str]:
        events = []
        with self.client.pipeline(transaction=False) as pipe:
            for i in range(max(1, batch_size)):
                pipe.rpop(key)
            result = pipe.execute()
        for elem in result:
            if elem is None:
                break
            events.append(self.decode(elem))
        return events

    def pop_event(self, key) -> Optional[str]:
        events = self.pop_events(key, batch_size=1)
        return events[0] if events else None

    def size(self, key: str) -> int:
        return self.client.llen(key)


def buffer_factory(broker_url: str, max_size: int, batch_size: int) -> BaseBuffer:
    return RedisBuffer(broker_url, max_size, batch_size)


def get_buffer() -> BaseBuffer:
    attr_name = "observability_buffer"
    if hasattr(_local, attr_name):
        return _local.observability_buffer
    try:
        return getattr(_local, "observability_buffer")
    except AttributeError:
        pass
    if not settings.OBSERVABILITY_BROKER_URL:
        raise ConnectionDoesNotExist("The observability broker url not set")
    broker_url = settings.OBSERVABILITY_BROKER_URL
    max_size = settings.OBSERVABILITY_BUFFER_SIZE_LIMIT
    batch_size = settings.OBSERVABILITY_BUFFER_BATCH_SIZE
    buffer = buffer_factory(broker_url, max_size, batch_size)
    setattr(_local, attr_name, buffer)
    return buffer
