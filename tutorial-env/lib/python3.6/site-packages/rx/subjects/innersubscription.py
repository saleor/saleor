from rx import config


class InnerSubscription(object):
    def __init__(self, subject, observer):
        self.subject = subject
        self.observer = observer

        self.lock = config["concurrency"].RLock()

    def dispose(self):
        with self.lock:
            if not self.subject.is_disposed and self.observer:
                if self.observer in self.subject.observers:
                    self.subject.observers.remove(self.observer)
                self.observer = None
