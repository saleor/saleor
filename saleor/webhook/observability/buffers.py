import pickle
import zlib
from typing import Any, Dict, List, Optional

from asgiref.local import Local
from django.conf import settings
from redis import ConnectionPool, Redis

from .exceptions import ConnectionNotConfigured

KEY_TYPE = str
_local = Local()


class BaseBuffer:
    _compressor_preset = 6
    _pickle_version = 5

    def __init__(self, broker_url: str, max_size: int, batch_size: int):
        self.broker_url = broker_url
        self.max_size = max_size
        self.batch_size = batch_size

    def decode(self, value: bytes) -> Any:
        return pickle.loads(zlib.decompress(value))

    def encode(self, value: Any) -> bytes:
        return zlib.compress(
            pickle.dumps(value, self._pickle_version), self._compressor_preset
        )

    def put_event(self, key: KEY_TYPE, event: Any):
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a put_event() method"
        )

    def put_events(self, key: KEY_TYPE, events: List[Any]) -> int:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a put_events() method"
        )

    def put_multi_key_events(
        self, events_dict: Dict[KEY_TYPE, List[Any]]
    ) -> Dict[KEY_TYPE, int]:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a put_events_multi_buffer() method"
        )

    def pop_event(self, key: KEY_TYPE) -> Any:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a pop_events() method"
        )

    def pop_events(self, key: KEY_TYPE) -> List[Any]:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a pop_events() method"
        )

    def clear(self, key: KEY_TYPE):
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a clear() method"
        )

    def size(self, key: KEY_TYPE) -> int:
        raise NotImplementedError(
            "subclasses of BaseBuffer must provide a size() method"
        )


class RedisBuffer(BaseBuffer):
    _pools: Dict[str, ConnectionPool] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._client: Optional[Redis] = None

    def get_connection_pool(self):
        return ConnectionPool.from_url(self.broker_url)

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
        self, key: KEY_TYPE, events: List[bytes], client: Optional[Redis] = None
    ):
        if client is None:
            client = self.client
        client.lpush(key, *events)
        client.ltrim(key, 0, max(0, self.max_size - 1))

    def put_events(self, key: KEY_TYPE, events: List[Any]) -> int:
        events_data = [self.encode(event) for event in events]
        with self.client.pipeline(transaction=False) as pipe:
            self._put_events(key, events_data, client=pipe)
            result = pipe.execute()
        return max(0, result[0] - self.max_size)

    def put_event(self, key: KEY_TYPE, event: Any):
        self.put_events(key, [event])

    def put_multi_key_events(
        self, events_dict: Dict[KEY_TYPE, List[Any]]
    ) -> Dict[KEY_TYPE, int]:
        keys = list(events_dict.keys())
        trimmed: Dict[KEY_TYPE, int] = {}
        if not keys:
            return trimmed
        with self.client.pipeline(transaction=False) as pipe:
            for key in keys:
                events_data = [self.encode(event) for event in events_dict[key]]
                self._put_events(key, events_data, client=pipe)
            result = pipe.execute()
        for key in keys:
            buffer_len, _ = result.pop(0), result.pop(0)
            trimmed[key] = max(0, buffer_len - self.max_size)
        return trimmed

    def _pop_events(self, key: KEY_TYPE, batch_size: int) -> List[Any]:
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

    def pop_event(self, key: KEY_TYPE) -> Any:
        events = self._pop_events(key, batch_size=1)
        return events[0] if events else None

    def pop_events(self, key: KEY_TYPE) -> List[Any]:
        return self._pop_events(key, self.batch_size)

    def clear(self, key: KEY_TYPE) -> int:
        with self.client.pipeline(transaction=False) as pipe:
            pipe.llen(key)
            pipe.delete(key)
            result = pipe.execute()
        return result[0]

    def size(self, key: KEY_TYPE) -> int:
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
        raise ConnectionNotConfigured("The observability broker url not set")
    broker_url = settings.OBSERVABILITY_BROKER_URL
    max_size = settings.OBSERVABILITY_BUFFER_SIZE_LIMIT
    batch_size = settings.OBSERVABILITY_BUFFER_BATCH_SIZE
    buffer = buffer_factory(broker_url, max_size, batch_size)
    setattr(_local, attr_name, buffer)
    return buffer
