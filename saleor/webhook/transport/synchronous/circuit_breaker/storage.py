import time
from collections import defaultdict


class Storage:
    def last_open(self, app_id: int) -> int:
        pass

    def update_open(self, app_id: int, open_time_seconds: int):
        pass

    def register_event_returning_count(self, key: str, ttl_seconds: int) -> int:
        pass


class InMemoryStorage(Storage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._events = defaultdict(list)
        self._last_open = {}

    def last_open(self, app_id: int) -> int:
        if app_id not in self._last_open:
            return 0

        return self._last_open[app_id]

    def update_open(self, app_id: int, open_time_seconds: int):
        self._last_open[app_id] = open_time_seconds

    def register_event_returning_count(self, key: str, ttl_seconds: int) -> int:
        events = self._events[key]

        now = int(time.time())
        events.append(now)

        filtered_entries = [event for event in events if event >= now - ttl_seconds]
        self._events[key] = filtered_entries
        return len(filtered_entries)
