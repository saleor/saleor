from rx import config
from rx.core import Disposable


class RefCountDisposable(Disposable):
    """Represents a disposable resource that only disposes its underlying
    disposable resource when all dependent disposable objects have been
    disposed."""

    class InnerDisposable(Disposable):

        def __init__(self, parent):
            self.parent = parent
            self.is_disposed = False
            self.lock = config["concurrency"].RLock()

        def dispose(self):
            with self.lock:
                parent = self.parent
                self.parent = None
            parent.release()

    def __init__(self, disposable):
        """Initializes a new instance of the RefCountDisposable class with the
        specified disposable."""

        self.underlying_disposable = disposable
        self.is_primary_disposed = False
        self.is_disposed = False
        self.lock = config["concurrency"].RLock()
        self.count = 0

        super(RefCountDisposable, self).__init__()

    def dispose(self):
        """Disposes the underlying disposable only when all dependent
        disposables have been disposed."""

        if self.is_disposed:
            return

        disposable = None
        with self.lock:
            if not self.is_primary_disposed:
                self.is_primary_disposed = True
                if not self.count:
                    self.is_disposed = True
                    disposable = self.underlying_disposable

        if disposable:
            disposable.dispose()

    def release(self):
        if self.is_disposed:
            return

        should_dispose = False
        with self.lock:
            self.count -= 1
            if not self.count and self.is_primary_disposed:
                self.is_disposed = True
                should_dispose = True

        if should_dispose:
            self.underlying_disposable.dispose()

    @property
    def disposable(self):
        """Returns a dependent disposable that when disposed decreases the
        refcount on the underlying disposable."""

        with self.lock:
            if self.is_disposed:
                return Disposable.empty()
            else:
                self.count += 1
                return self.InnerDisposable(self)
