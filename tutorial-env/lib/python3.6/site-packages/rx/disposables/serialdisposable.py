from rx import config
from rx.core import Disposable


class SerialDisposable(Disposable):
    """Represents a disposable resource whose underlying disposable resource can
    be replaced by another disposable resource, causing automatic disposal of
    the previous underlying disposable resource."""

    def __init__(self):
        self.current = None
        self.is_disposed = False
        self.lock = config["concurrency"].RLock()

        super(SerialDisposable, self).__init__()

    def get_disposable(self):
        return self.current

    def set_disposable(self, value):
        """If the SerialDisposable has already been disposed, assignment to this
        property causes immediate disposal of the given disposable object.
        Assigning this property disposes the previous disposable object."""

        should_dispose = self.is_disposed
        old = None

        with self.lock:
            if not should_dispose:
                old = self.current
                self.current = value

        if old:
            old.dispose()

        if should_dispose and value:
            value.dispose()

    disposable = property(get_disposable, set_disposable)

    def dispose(self):
        """Disposes the underlying disposable as well as all future
        replacements."""

        old = None

        with self.lock:
            if not self.is_disposed:
                self.is_disposed = True
                old = self.current
                self.current = None

        if old:
            old.dispose()
