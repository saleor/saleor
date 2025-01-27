import asyncio
import contextlib

from asgiref.local import Local, _CVar


@contextlib.contextmanager
def _Local_lock_storage(self):
    # Thread safe access to storage
    if self._thread_critical:
        is_async = True
        try:
            # this is a test for are we in a async or sync
            # thread - will raise RuntimeError if there is
            # no current loop
            asyncio.get_running_loop()
        except RuntimeError:
            is_async = False
        if not is_async:
            # We are in a sync thread, the storage is
            # just the plain thread local (i.e, "global within
            # this thread" - it doesn't matter where you are
            # in a call stack you see the same storage)
            yield self._storage
        else:
            # We are in an async thread - storage is still
            # local to this thread, but additionally should
            # behave like a context var (is only visible with
            # the same async call stack)

            # Ensure context exists in the current thread
            if not hasattr(self._storage, "cvar"):
                self._storage.cvar = _CVar()

            # self._storage is a thread local, so the members
            # can't be accessed in another thread (we don't
            # need any locks)
            yield self._storage.cvar
    else:
        # Lock for thread_critical=False as other threads
        # can access the exact same storage object
        with self._thread_lock:
            yield self._storage


def patch_local():
    """Patch `_lock_storage in `Local` to avoid memory leaks.

    Those changes will remove the circular references inside `Local` class,
    allowing memory to be freed immediately, without the need of a deep garbage collection cycle.
    Issue: https://github.com/django/asgiref/issues/487
    """
    Local._lock_storage = _Local_lock_storage  # type: ignore[method-assign]
