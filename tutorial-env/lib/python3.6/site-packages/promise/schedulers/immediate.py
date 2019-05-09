from threading import Event

if False:
    from ..promise import Promise
    from typing import Callable, Any, Optional  # flake8: noqa


class ImmediateScheduler(object):
    def call(self, fn):
        # type: (Callable) -> None
        try:
            fn()
        except:
            pass

    def wait(self, promise, timeout=None):
        # type: (Promise, Optional[float]) -> None
        e = Event()

        def on_resolve_or_reject(_):
            # type: (Any) -> None
            e.set()

        promise._then(on_resolve_or_reject, on_resolve_or_reject)
        waited = e.wait(timeout)
        if not waited:
            raise Exception("Timeout")
