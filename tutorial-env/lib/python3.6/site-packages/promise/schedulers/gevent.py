from __future__ import absolute_import

from gevent.event import Event  # type: ignore
import gevent  # type: ignore


class GeventScheduler(object):
    def call(self, fn):
        # print fn
        gevent.spawn(fn)

    def wait(self, promise, timeout=None):
        e = Event()

        def on_resolve_or_reject(_):
            e.set()

        promise._then(on_resolve_or_reject, on_resolve_or_reject)
        waited = e.wait(timeout)
        if not waited:
            raise Exception("Timeout")
