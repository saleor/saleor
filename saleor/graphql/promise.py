from promise import Promise


def __del_promise__(self: Promise) -> None:
    # Clean up references to break up any reference cycles
    self._handlers = None  # type: ignore[assignment]
    self._fulfillment_handler0 = None
    self._rejection_handler0 = None
    self._promise0 = None
    self._future = None  # type: ignore[assignment]
    self._event_instance = None  # type: ignore[attr-defined]
    self._traceback = None


def patch_promise():
    """Patch Promise.__del__ to avoid memory leaks.

    Promise.__del__ will remove all references that could result in reference cycles,
    allowing memory to be freed immediately, without the need of a deep garbage collection cycle.
    Issue: https://github.com/syrusakbary/promise/issues/106
    """
    Promise.__del__ = __del_promise__  # type: ignore[attr-defined]
