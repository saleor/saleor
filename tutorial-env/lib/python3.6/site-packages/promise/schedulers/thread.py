from threading import Thread, Event


class ThreadScheduler(object):
    def call(self, fn):
        thread = Thread(target=fn)
        thread.start()

    def wait(self, promise, timeout=None):
        e = Event()

        def on_resolve_or_reject(_):
            e.set()

        promise._then(on_resolve_or_reject, on_resolve_or_reject)
        waited = e.wait(timeout)
        if not waited:
            raise Exception("Timeout")
