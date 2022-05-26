import atexit
import logging
import os
from queue import Empty, Full, Queue
from threading import Lock, Thread
from time import monotonic
from typing import Any, Callable, Optional

from django.conf import settings

from .buffers import get_buffer

_worker: Optional["BackgroundWorker"] = None
_TERMINATOR = object()
FLUSH_TIMEOUT = 2.0

logger = logging.getLogger(__name__)


def _shutdown_worker():
    logger.debug("[Observability] Atexit shutdown signal")
    if _worker:
        _worker.close()


def init():
    global _worker
    if _worker is None:
        _worker = BackgroundWorker(
            batch_size=settings.OBSERVABILITY_BUFFER_BATCH_SIZE,
            timeout=settings.OBSERVABILITY_REPORT_PERIOD.total_seconds(),
        )
        atexit.register(_shutdown_worker)


def put_event(buffer_name: str, generate_payload: Callable[[], Any]):
    if _worker:
        return _worker.submit_event(buffer_name, generate_payload)
    logger.warning("[Observability] Worker not initialized, event dropped")


class BackgroundWorker:
    def __init__(self, batch_size: int, timeout: float):
        self._batch_size = batch_size
        self._queue: "Queue[Any]" = Queue(maxsize=batch_size)
        self._lock = Lock()
        self._thread: Optional[Thread] = None
        self._thread_for_pid: Optional[int] = None
        self._timeout = timeout

    def _target(self):
        logger.info("[Observability] Background worker started")
        working = True
        while working:
            events, events_count, deadline = {}, 0, monotonic() + self._timeout
            while (
                events_count < self._batch_size
                and (timeout := deadline - monotonic()) > 0.0
            ):
                try:
                    event_data = self._queue.get(timeout=timeout)
                except Empty:
                    break
                try:
                    if event_data is _TERMINATOR:
                        working = False
                        break
                    buffer_name, generate_payload = event_data
                    events.setdefault(buffer_name, []).append(generate_payload())
                    events_count += 1
                except Exception:
                    logger.error(
                        "[Observability] Failed generating payload", exc_info=True
                    )
                finally:
                    self._queue.task_done()
            if events_count:
                try:
                    get_buffer("").put_multi_key_events(events)
                except Exception:
                    logger.error(
                        "[Observability] Buffer error, dropped %s events",
                        events_count,
                        exc_info=True,
                    )

    def start(self):
        with self._lock:
            if not self.is_alive:
                self._thread = Thread(
                    target=self._target,
                    name="observability_worker",
                    daemon=True,
                )
                self._thread.start()
                self._thread_for_pid = os.getpid()

    @property
    def is_alive(self) -> bool:
        if self._thread_for_pid != os.getpid():
            return False
        if not self._thread:
            return False
        return self._thread.is_alive()

    def _ensure_thread(self):
        if not self.is_alive:
            self.start()

    def submit_event(self, buffer_name: str, generate_payload: Callable[[], Any]):
        self._ensure_thread()
        try:
            self._queue.put_nowait((buffer_name, generate_payload))
            return True
        except Full:
            logger.warning("[Observability] Queue full, event dropped")
            return False

    def _timed_queue_join(self, timeout: float) -> bool:
        deadline = monotonic() + timeout
        queue = self._queue
        self._timeout = timeout
        with queue.all_tasks_done:
            while queue.unfinished_tasks:
                delay = deadline - monotonic()
                if delay <= 0:
                    return False
                queue.all_tasks_done.wait(timeout=delay)
            return True

    def _wait_flush(self, timeout: float):
        initial_timeout = min(0.1, timeout)
        if not self._timed_queue_join(initial_timeout):
            pending = self._queue.qsize() + 1
            logger.debug("[Observability] %d events pending on flush", pending)
            if not self._timed_queue_join(timeout - initial_timeout):
                pending = self._queue.qsize() + 1
                logger.error(
                    "[Observability] Flush timed out, dropped %s events", pending
                )

    def flush(self, timeout: float):
        with self._lock:
            if self.is_alive and timeout > 0.0:
                self._wait_flush(timeout)

    def kill(self):
        logger.debug("[Observability] Worker got kill request")
        with self._lock:
            if self._thread:
                try:
                    self._queue.put_nowait(_TERMINATOR)
                except Full:
                    logger.debug("[Observability] Worker queue full, kill failed")
                self._thread = None
                self._thread_for_pid = None

    def close(self):
        self.flush(FLUSH_TIMEOUT)
        self.kill()
