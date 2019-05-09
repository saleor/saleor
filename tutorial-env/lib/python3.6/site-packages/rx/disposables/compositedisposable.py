from rx import config
from rx.core import Disposable


class CompositeDisposable(Disposable):
    """Represents a group of disposable resources that are disposed together"""

    def __init__(self, *args):
        if args and isinstance(args[0], list):
            self.disposables = args[0]
        else:
            self.disposables = list(args)

        self.is_disposed = False
        self.lock = config["concurrency"].RLock()
        super(CompositeDisposable, self).__init__()

    def add(self, item):
        """Adds a disposable to the CompositeDisposable or disposes the
        disposable if the CompositeDisposable is disposed

        Keyword arguments:
        item -- Disposable to add."""

        should_dispose = False
        with self.lock:
            if self.is_disposed:
                should_dispose = True
            else:
                self.disposables.append(item)

        if should_dispose:
            item.dispose()

    def remove(self, item):
        """Removes and disposes the first occurrence of a disposable from the
        CompositeDisposable."""

        if self.is_disposed:
            return

        should_dispose = False
        with self.lock:
            if item in self.disposables:
                self.disposables.remove(item)
                should_dispose = True

        if should_dispose:
            item.dispose()

        return should_dispose

    def dispose(self):
        """Disposes all disposables in the group and removes them from the
        group."""

        if self.is_disposed:
            return

        with self.lock:
            self.is_disposed = True
            current_disposables = self.disposables[:]
            self.disposables = []

        for disposable in current_disposables:
            disposable.dispose()

    def clear(self):
        """Removes and disposes all disposables from the CompositeDisposable,
        but does not dispose the CompositeDisposable."""

        with self.lock:
            current_disposables = self.disposables[:]
            self.disposables = []

        for disposable in current_disposables:
            disposable.dispose()

    def contains(self, item):
        """Determines whether the CompositeDisposable contains a specific
        disposable.

        Keyword arguments:
        item -- Disposable to search for

        Returns True if the disposable was found; otherwise, False"""

        return item in self.disposables

    def to_list(self):
        return self.disposables[:]

    def __len__(self):
        return len(self.disposables)

    @property
    def length(self):
        return len(self.disposables)

