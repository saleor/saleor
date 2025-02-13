import logging
import time
import uuid
from collections import defaultdict

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from redis import Redis, RedisError

from ...graphql.app.types import CircuitBreakerState

logger = logging.getLogger(__name__)


class Storage:
    def last_open(self, app_id: int) -> tuple[int, str]:  # type: ignore[empty-body]
        pass

    def update_open(
        self, app_id: int, open_time_seconds: int, state: CircuitBreakerState
    ):
        pass

    def register_event_returning_count(  # type: ignore[empty-body]
        self, app_id: int, name: str, ttl_seconds: int
    ) -> int:
        pass

    def clear_state_for_app(self, app_id: int):
        pass


class InMemoryStorage(Storage):
    def __init__(self):
        super().__init__()
        self._events = defaultdict(list)
        self._last_open = {}

    def last_open(self, app_id: int) -> tuple[int, str]:
        if app_id not in self._last_open:
            return 0, CircuitBreakerState.CLOSED

        return self._last_open[app_id]

    def update_open(
        self, app_id: int, open_time_seconds: int, state: CircuitBreakerState
    ):
        self._last_open[app_id] = open_time_seconds

    def register_event_returning_count(
        self, app_id: int, name: str, ttl_seconds: int
    ) -> int:
        key = f"{app_id}-{name}"
        events = self._events[key]

        now = int(time.time())
        events.append(now)

        filtered_entries = [event for event in events if event > now - ttl_seconds]
        self._events[key] = filtered_entries
        return len(filtered_entries)

    def clear_state_for_app(self, app_id: int):
        self._last_open.pop(app_id, None)
        self._events = defaultdict(
            list,
            {
                key: value
                for key, value in self._events.items()
                if not key.startswith(str(app_id))
            },
        )


class RedisStorage(Storage):
    WARNING_MESSAGE = "An error occurred when interacting with Redis"
    KEY_PREFIX = "bbrs"  # as in "breaker board redis storage"
    EVENT_KEYS = ["error", "total"]
    STATE_KEY = "state"

    def __init__(self, client: Redis | None = None):
        super().__init__()

        if client:
            self._client = client
        else:
            if settings.CACHE_URL is None or not settings.CACHE_URL.startswith("redis"):
                raise ImproperlyConfigured(
                    "Redis storage cannot be used when Redis cache is not configured"
                )

            self._client = cache._cache.get_client()  # type: ignore[attr-defined]

    def last_open(self, app_id: int) -> tuple[int, str]:
        try:
            state_key = f"{self.KEY_PREFIX}-{app_id}-{self.STATE_KEY}"
            half_open_key = f"{state_key}-{CircuitBreakerState.HALF_OPEN}"
            open_key = f"{state_key}-{CircuitBreakerState.OPEN}"
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
        try:
            self._client.set(
                f"{self.KEY_PREFIX}-{app_id}-{self.STATE_KEY}-{state}",
                open_time_seconds,
            )
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)

    def get_event_count(self, app_id: int, name: str) -> int:
        key = f"{self.KEY_PREFIX}-{app_id}-{name}"
        return self._client.zcard(key)

    def register_event(self, app_id: int, name: str, ttl_seconds: int) -> int:
        key = f"{self.KEY_PREFIX}-{app_id}-{name}"
        now = int(time.time())

        try:
            # Use Redis pipeline for network optimization.
            p = self._client.pipeline()

            # Remove all no longer relevant events.
            # The command removes all events from `key` set where score (event's registration
            # time) already reached end of life (TTL).
            p.zremrangebyscore(key, "-inf", now - ttl_seconds)

            # Add event to `key` set where event is random identifier and event's score is
            # event's registration time).
            # Event is random identifier because underlying structure to contain items
            # within Redis is a set.
            p.zadd(key, {uuid.uuid4().bytes: now})

            # Return number of events in `key` set.
            p.zcard(key)

            result = p.execute()
            return result.pop()
        except (RedisError, IndexError):
            logger.warning(self.WARNING_MESSAGE, exc_info=True)
            return 0

    def clear_state_for_app(self, app_id: int):
        try:
            keys = [f"{self.KEY_PREFIX}-{app_id}-{name}" for name in self.EVENT_KEYS]
            keys.append(f"{self.KEY_PREFIX}-{app_id}")
            keys.extend(
                [
                    f"{self.KEY_PREFIX}-{app_id}-{self.STATE_KEY}-{state}"
                    for state in [
                        CircuitBreakerState.CLOSED,
                        CircuitBreakerState.OPEN,
                        CircuitBreakerState.HALF_OPEN,
                    ]
                ]
            )
            self._client.delete(*keys)
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)
            error = 1
            return error
