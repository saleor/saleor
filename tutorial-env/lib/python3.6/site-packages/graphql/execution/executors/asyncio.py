from __future__ import absolute_import

from asyncio import Future, get_event_loop, iscoroutine, wait

from promise import Promise

# Necessary for static type checking
if False:  # flake8: noqa
    from asyncio.unix_events import _UnixSelectorEventLoop
    from typing import Optional, Any, Callable, List

try:
    from asyncio import ensure_future
except ImportError:
    # ensure_future is only implemented in Python 3.4.4+
    def ensure_future(coro_or_future, loop=None):  # type: ignore
        """Wrap a coroutine or an awaitable in a future.

        If the argument is a Future, it is returned directly.
        """
        if isinstance(coro_or_future, Future):
            if loop is not None and loop is not coro_or_future._loop:
                raise ValueError("loop argument must agree with Future")
            return coro_or_future
        elif iscoroutine(coro_or_future):
            if loop is None:
                loop = get_event_loop()
            task = loop.create_task(coro_or_future)
            if task._source_traceback:
                del task._source_traceback[-1]
            return task
        else:
            raise TypeError("A Future, a coroutine or an awaitable is required")


try:
    from .asyncio_utils import asyncgen_to_observable, isasyncgen
except Exception:

    def isasyncgen(object):  # type: ignore
        False

    def asyncgen_to_observable(asyncgen, loop=None):
        pass


class AsyncioExecutor(object):
    def __init__(self, loop=None):
        # type: (Optional[_UnixSelectorEventLoop]) -> None
        if loop is None:
            loop = get_event_loop()
        self.loop = loop
        self.futures = []  # type: List[Future]

    def wait_until_finished(self):
        # type: () -> None
        # if there are futures to wait for
        while self.futures:
            # wait for the futures to finish
            futures = self.futures
            self.futures = []
            self.loop.run_until_complete(wait(futures))

    def clean(self):
        self.futures = []

    def execute(self, fn, *args, **kwargs):
        # type: (Callable, *Any, **Any) -> Any
        result = fn(*args, **kwargs)
        if isinstance(result, Future) or iscoroutine(result):
            future = ensure_future(result, loop=self.loop)
            self.futures.append(future)
            return Promise.resolve(future)
        elif isasyncgen(result):
            return asyncgen_to_observable(result, loop=self.loop)
        return result
