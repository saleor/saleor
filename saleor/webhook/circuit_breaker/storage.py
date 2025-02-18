import logging
import time
import uuid

from django.core.cache import cache
from redis import RedisError

from ...graphql.app.types import CircuitBreakerState

logger = logging.getLogger(__name__)


class Storage:
    def last_open(self, app_id: int) -> tuple[int, str]:  # type: ignore[empty-body]
        pass

    def update_open(
        self, app_id: int, open_time_seconds: int, state: CircuitBreakerState
    ):
        pass

    def get_event_count(self, app_id: int, name: str) -> int:  # type: ignore[empty-body]
        pass

    def register_event(self, app_id: int, name: str, ttl_seconds: int):
        pass

    def clear_state_for_app(self, app_id: int):
        pass

    class Meta:
        abstract = True


class RedisStorage(Storage):
    WARNING_MESSAGE = "An error occurred when interacting with Redis"
    KEY_PREFIX = "bbrs"  # as in "breaker board redis storage"
    EVENT_KEYS = ["error", "total"]
    STATE_KEY = "state"

    def __init__(self, client=None):
        super().__init__()
        if client:
            self._client = client
        else:
            self._client = cache._cache.get_client()  # type: ignore[attr-defined]

    def get_base_storage_key(self) -> str:
        return self.KEY_PREFIX

    def last_open(self, app_id: int) -> tuple[int, str]:
        base_key = self.get_base_storage_key()
        state_key = f"{base_key}-{app_id}-{self.STATE_KEY}"
        half_open_key = f"{state_key}-{CircuitBreakerState.HALF_OPEN}"
        open_key = f"{state_key}-{CircuitBreakerState.OPEN}"
        try:
            half_open_val, open_val = self._client.mget([half_open_key, open_key])
            if half_open_val:
                value = int(str(half_open_val, "utf-8"))
                return value, CircuitBreakerState.HALF_OPEN
            if open_val:
                value = int(str(open_val, "utf-8"))
                return value, CircuitBreakerState.OPEN
        except RedisError:
            pass

        return 0, CircuitBreakerState.CLOSED

    def update_open(
        self, app_id: int, open_time_seconds: int, state: CircuitBreakerState
    ):
        base_key = self.get_base_storage_key()
        try:
            self._client.set(
                f"{base_key}-{app_id}-{self.STATE_KEY}-{state}",
                open_time_seconds,
            )
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)

    def get_event_count(self, app_id: int, name: str) -> int:
        base_key = self.get_base_storage_key()
        key = f"{base_key}-{app_id}-{name}"
        try:
            return self._client.zcard(key)
        except RedisError:
            return 0

    def register_event(self, app_id: int, name: str, ttl_seconds: int):
        base_key = self.get_base_storage_key()
        key = f"{base_key}-{app_id}-{name}"
        now = int(time.time())

        try:
            # Use Redis pipeline for network optimization.
            p = self._client.pipeline()

            # Remove all no longer relevant events.
            # The command removes all events from `key` set where score (event's registration
            # time) already reached end of life (TTL).
            p.zremrangebyscore(key, "-inf", now - ttl_seconds)

            # Add event to `key` set where event is random identifier and event's score is
            # event's registration time.
            # Event is random identifier because underlying structure to contain items
            # within Redis is a set.
            p.zadd(key, {uuid.uuid4().bytes: now})

            p.execute()
        except RedisError:
            pass

    def clear_state_for_app(self, app_id: int):
        base_key = self.get_base_storage_key()
        keys = [f"{base_key}-{app_id}-{name}" for name in self.EVENT_KEYS]
        keys.append(f"{base_key}-{app_id}")
        keys.extend(
            [
                f"{base_key}-{app_id}-{self.STATE_KEY}-{state}"
                for state in [
                    CircuitBreakerState.CLOSED,
                    CircuitBreakerState.OPEN,
                    CircuitBreakerState.HALF_OPEN,
                ]
            ]
        )
        try:
            self._client.delete(*keys)
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)
            error = 1
            return error
