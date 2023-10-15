import functools
from typing import Any, Callable, Optional

from django.utils.functional import LazyObject, SimpleLazyObject, empty


def lazy_no_retry(func: Callable) -> SimpleLazyObject:
    """Wrap SimpleLazyObject while ensuring it is never re-evaluated on failure.

    Wraps a given function into a ``SimpleLazyObject`` class while ensuring
    if ``func`` fails, then ``func`` is never invoked again.

    This mitigates an issue where an expensive ``func`` can be rerun for
    each GraphQL resolver instead of flagging it as rejected/failed.
    """
    error: Optional[Exception] = None

    @functools.wraps(func)
    def _wrapper():
        nonlocal error

        # If it was already evaluated, and it crashed, then do not re-attempt.
        if error:
            raise error

        try:
            return func()
        except Exception as exc:
            error = exc
            raise

    return SimpleLazyObject(_wrapper)


def unwrap_lazy(obj: LazyObject) -> Any:
    """Return the value of a given ``LazyObject``."""
    if obj._wrapped is empty:  # type: ignore[attr-defined] # valid attribute
        obj._setup()  # type: ignore[attr-defined] # valid attribute
    return obj._wrapped  # type: ignore[attr-defined] # valid attribute
