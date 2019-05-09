from __future__ import absolute_import

from asyncio import get_event_loop, Event


class AsyncioScheduler(object):
    def __init__(self, loop=None):
        self.loop = loop or get_event_loop()

    def call(self, fn):
        self.loop.call_soon(fn)

    def wait(self, promise, timeout=None):
        e = Event()

        def on_resolve_or_reject(_):
            e.set()

        promise._then(on_resolve_or_reject, on_resolve_or_reject)

        # We can't use the timeout in Asyncio event
        e.wait()
