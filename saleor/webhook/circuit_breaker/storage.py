import logging
import time
import uuid

from django.core.cache import cache
from redis import RedisError

from ...graphql.app.enums import CircuitBreakerState

logger = logging.getLogger(__name__)


class Storage:
    def set_app_state(self, app_id: int, state: CircuitBreakerState, changed_at: int):
        pass

    def get_app_state(self, app_id: int) -> tuple[str, int]:  # type: ignore[empty-body]
        pass

    def get_event_count(self, app_id: int, name: str) -> int:  # type: ignore[empty-body]
        pass

    def register_event(self, app_id: int, name: str, ttl_seconds: int):
        pass

    def clear_state_for_app(self, app_id: int):
        pass

    class Meta:
        abstract = True


def serialize_breaker_state(state, changed_at) -> str:
    return f"{state}|{changed_at}"


def deserialize_breaker_state(data) -> tuple[str, int]:
    data = str(data, "utf-8")
    state, changed_at = data.split("|")
    return state, int(changed_at)


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

    def set_app_state(self, app_id: int, state: CircuitBreakerState, changed_at: int):
        base_key = self.get_base_storage_key()
        try:
            self._client.set(
                f"{base_key}-{app_id}-{self.STATE_KEY}",
                serialize_breaker_state(state, changed_at),
            )
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)

    def get_app_state(self, app_id: int) -> tuple[str, int]:
        base_key = self.get_base_storage_key()
        state_key = f"{base_key}-{app_id}-{self.STATE_KEY}"
        try:
            if data := self._client.get(state_key):
                return deserialize_breaker_state(data)
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)

        return CircuitBreakerState.CLOSED, 0

    def get_event_count(self, app_id: int, name: str) -> int:
        base_key = self.get_base_storage_key()
        key = f"{base_key}-{app_id}-{name}"
        try:
            return self._client.zcard(key)
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)
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
            logger.warning(self.WARNING_MESSAGE, exc_info=True)

    def clear_state_for_app(self, app_id: int):
        base_key = self.get_base_storage_key()
        keys = [f"{base_key}-{app_id}-{name}" for name in self.EVENT_KEYS]
        keys.append(f"{base_key}-{app_id}-{self.STATE_KEY}")
        try:
            self._client.delete(*keys)
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)
            error = 1
            return error
