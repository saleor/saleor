"""Time Utilities."""
# flake8: noqa

from __future__ import absolute_import, unicode_literals

__all__ = ('maybe_s_to_ms',)


def maybe_s_to_ms(v):
    # type: (Optional[Union[int, float]]) -> int
    """Convert seconds to milliseconds, but return None for None."""
    return int(float(v) * 1000.0) if v is not None else v
