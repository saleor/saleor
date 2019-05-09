# Based on https://github.com/petkaantonov/bluebird/blob/master/src/promise.js
from collections import deque

if False:
    from .promise import Promise
    from typing import Any, Callable, Optional, Union  # flake8: noqa


class Async(object):
    def __init__(self, trampoline_enabled=True):
        self.is_tick_used = False
        self.late_queue = deque()  # type: ignore
        self.normal_queue = deque()  # type: ignore
        self.have_drained_queues = False
        self.trampoline_enabled = trampoline_enabled

    def enable_trampoline(self):
        self.trampoline_enabled = True

    def disable_trampoline(self):
        self.trampoline_enabled = False

    def have_items_queued(self):
        return self.is_tick_used or self.have_drained_queues

    def _async_invoke_later(self, fn, scheduler):
        self.late_queue.append(fn)
        self.queue_tick(scheduler)

    def _async_invoke(self, fn, scheduler):
        # type: (Callable, Any) -> None
        self.normal_queue.append(fn)
        self.queue_tick(scheduler)

    def _async_settle_promise(self, promise):
        # type: (Promise) -> None
        self.normal_queue.append(promise)
        self.queue_tick(promise.scheduler)

    def invoke_later(self, fn):
        if self.trampoline_enabled:
            self._async_invoke_later(fn, scheduler)
        else:
            scheduler.call_later(0.1, fn)

    def invoke(self, fn, scheduler):
        # type: (Callable, Any) -> None
        if self.trampoline_enabled:
            self._async_invoke(fn, scheduler)
        else:
            scheduler.call(fn)

    def settle_promises(self, promise):
        # type: (Promise) -> None
        if self.trampoline_enabled:
            self._async_settle_promise(promise)
        else:
            promise.scheduler.call(promise._settle_promises)

    def throw_later(self, reason, scheduler):
        # type: (Exception, Any) -> None
        def fn():
            # type: () -> None
            raise reason

        scheduler.call(fn)

    fatal_error = throw_later

    def drain_queue(self, queue):
        # type: (deque) -> None
        from .promise import Promise

        while queue:
            fn = queue.popleft()
            if isinstance(fn, Promise):
                fn._settle_promises()
                continue
            fn()

    def drain_queue_until_resolved(self, promise):
        # type: (Promise) -> None
        from .promise import Promise

        queue = self.normal_queue
        while queue:
            if not promise.is_pending:
                return
            fn = queue.popleft()
            if isinstance(fn, Promise):
                fn._settle_promises()
                continue
            fn()

        self.reset()
        self.have_drained_queues = True
        self.drain_queue(self.late_queue)

    def wait(self, promise, timeout=None):
        # type: (Promise, Optional[float]) -> None
        if not promise.is_pending:
            # We return if the promise is already
            # fulfilled or rejected
            return

        target = promise._target()

        if self.trampoline_enabled:
            if self.is_tick_used:
                self.drain_queue_until_resolved(target)

            if not promise.is_pending:
                # We return if the promise is already
                # fulfilled or rejected
                return
        target.scheduler.wait(target, timeout)

    def drain_queues(self):
        # type: () -> None
        assert self.is_tick_used
        self.drain_queue(self.normal_queue)
        self.reset()
        self.have_drained_queues = True
        self.drain_queue(self.late_queue)

    def queue_tick(self, scheduler):
        # type: (Any) -> None
        if not self.is_tick_used:
            self.is_tick_used = True
            scheduler.call(self.drain_queues)

    def reset(self):
        # type: () -> None
        self.is_tick_used = False
