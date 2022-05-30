import math
import pickle
import zlib
from typing import Any, Dict, List, Optional, Tuple

from asgiref.local import Local
from django.conf import settings
from redis import ConnectionPool, Redis

from .exceptions import ConnectionNotConfigured

KEY_TYPE = str
_local = Local()


class BaseBuffer:
    _compressor_preset = 6
    _pickle_version = 5

    def __init__(
        self,
        broker_url: str,
        key: KEY_TYPE,
        max_size: int,
        batch_size: int,
        connection_timeout=10.0,
    ):
        self.broker_url = broker_url
        self.key = key
        self.max_size = max_size
        self.batch_size = batch_size
        self.connection_timeout = connection_timeout

    def decode(self, value: bytes) -> Any:
        return pickle.loads(zlib.decompress(value))

    def encode(self, value: Any) -> bytes:
        return zlib.compress(
            pickle.dumps(value, self._pickle_version), self._compressor_preset
        )

    def put_event(self, event: Any) -> int:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a put_event() method"
        )

    def put_events(self, events: List[Any]) -> int:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a put_events() method"
        )

    def put_multi_key_events(
        self, events_dict: Dict[KEY_TYPE, List[Any]]
    ) -> Dict[KEY_TYPE, int]:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a put_events_multi_buffer() method"
        )

    def pop_event(self) -> Any:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a pop_events() method"
        )

    def pop_events(self) -> List[Any]:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a pop_events() method"
        )

    def pop_events_get_size(self) -> Tuple[List[Any], int]:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a pop_events_get_size() method"
        )

    def clear(self):
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a clear() method"
        )

    def size(self) -> int:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a size() method"
        )

    def in_batches(self, size: int) -> int:
        return math.ceil(size / self.batch_size)


class RedisBuffer(BaseBuffer):
    _pools: Dict[str, ConnectionPool] = {}
    _socket_connect_timeout = 0.25
    _client_name = "observability_buffer"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client: Optional[Redis] = None

    def get_connection_pool(self):
        return ConnectionPool.from_url(
            self.broker_url,
            socket_connect_timeout=self._socket_connect_timeout,
            socket_timeout=self.connection_timeout,
            client_name=self._client_name,
        )

    def get_or_create_connection_pool(self):
        if self.broker_url not in self._pools:
            self._pools[self.broker_url] = self.get_connection_pool()
        return self._pools[self.broker_url]

    def connect(self) -> Redis:
        pool = self.get_or_create_connection_pool()
        return Redis(connection_pool=pool)

    @property
    def client(self) -> Redis:
        if not self._client:
            self._client = self.connect()
        return self._client

    def _put_events(
        self, key: KEY_TYPE, events: List[Any], client: Optional[Redis] = None
    ) -> int:
        start_index = -self.max_size
        events_data = [self.encode(event) for event in events[start_index:]]
        if client is None:
            client = self.client
        client.lpush(key, *events_data)
        client.ltrim(key, 0, max(0, self.max_size - 1))
        return max(0, len(events) - self.max_size)

    def put_events(self, events: List[Any]) -> int:
        with self.client.pipeline(transaction=False) as pipe:
            dropped = self._put_events(self.key, events, client=pipe)
            result = pipe.execute()
        return dropped + max(0, result[0] - self.max_size)

    def put_event(self, event: Any) -> int:
        return self.put_events([event])

    def put_multi_key_events(
        self, events_dict: Dict[KEY_TYPE, List[Any]]
    ) -> Dict[KEY_TYPE, int]:
        keys = list(events_dict.keys())
        trimmed: Dict[KEY_TYPE, int] = {}
        if not keys:
            return trimmed
        with self.client.pipeline(transaction=False) as pipe:
            for key in keys:
                trimmed[key] = self._put_events(key, events_dict[key], client=pipe)
            result = pipe.execute()
        for key in keys:
            buffer_len, _ = result.pop(0), result.pop(0)
            trimmed[key] += max(0, buffer_len - self.max_size)
        return trimmed

    def _pop_events(self, key: KEY_TYPE, batch_size: int) -> Tuple[List[Any], int]:
        events = []
        with self.client.pipeline(transaction=False) as pipe:
            pipe.llen(key)
            for i in range(max(1, batch_size)):
                pipe.rpop(key)
            result = pipe.execute()
        size = result.pop(0)
        for elem in result:
            if elem is None:
                break
            events.append(self.decode(elem))
        return events, size - len(events)

    def pop_event(self) -> Any:
        events, _ = self._pop_events(self.key, batch_size=1)
        return events[0] if events else None

    def pop_events(self) -> List[Any]:
        events, _ = self._pop_events(self.key, self.batch_size)
        return events

    def pop_events_get_size(self) -> Tuple[List[Any], int]:
        return self._pop_events(self.key, self.batch_size)

    def clear(self) -> int:
        with self.client.pipeline(transaction=False) as pipe:
            pipe.llen(self.key)
            pipe.delete(self.key)
            result = pipe.execute()
        return result[0]

    def size(self) -> int:
        return self.client.llen(self.key)


def get_buffer(key: KEY_TYPE) -> BaseBuffer:
    if not settings.OBSERVABILITY_BROKER_URL:
        raise ConnectionNotConfigured("The observability broker url not set")
    broker_url = settings.OBSERVABILITY_BROKER_URL
    max_size = settings.OBSERVABILITY_BUFFER_SIZE_LIMIT
    batch_size = settings.OBSERVABILITY_BUFFER_BATCH_SIZE
    connection_timeout = settings.OBSERVABILITY_REPORT_PERIOD.total_seconds()
    return RedisBuffer(
        broker_url, key, max_size, batch_size, connection_timeout=connection_timeout
    )
