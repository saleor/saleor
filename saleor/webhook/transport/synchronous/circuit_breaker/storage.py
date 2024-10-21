import logging
import time
import uuid
from collections import defaultdict
from typing import Optional

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ImproperlyConfigured
from redis import Redis, RedisError

logger = logging.getLogger(__name__)


class Storage:
    def last_open(self, app_id: int) -> int:  # type: ignore[empty-body]
        pass

    def update_open(self, app_id: int, open_time_seconds: int):
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

    def last_open(self, app_id: int) -> int:
        if app_id not in self._last_open:
            return 0

        return self._last_open[app_id]

    def update_open(self, app_id: int, open_time_seconds: int):
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

    def __init__(self, client: Optional[Redis] = None):
        super().__init__()

        if client:
            self._client = client
        else:
            if settings.CACHE_URL is None or not settings.CACHE_URL.startswith("redis"):
                raise ImproperlyConfigured(
                    "Redis storage cannot be used when Redis cache is not configured"
                )

            self._client = cache._cache.get_client()  # type: ignore[attr-defined]

    def last_open(self, app_id: int) -> int:
        try:
            result = self._client.get(f"{self.KEY_PREFIX}-{app_id}")
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)
            return 0

        if result is None:
            return 0
        return int(str(result, "utf-8"))

    def update_open(self, app_id: int, open_time_seconds: int):
        try:
            self._client.set(f"{self.KEY_PREFIX}-{app_id}", open_time_seconds)
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)

    def register_event_returning_count(
        self, app_id: int, name: str, ttl_seconds: int
    ) -> int:
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
            keys = self._client.keys(f"{self.KEY_PREFIX}-{app_id}*")
            if keys:
                self._client.delete(*keys)
        except RedisError:
            logger.warning(self.WARNING_MESSAGE, exc_info=True)
