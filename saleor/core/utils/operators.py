from typing import Any, Optional


def xor_none(a: Optional[Any], b: Optional[Any]) -> bool:
    """Check whether a exclusive-or b is not None."""
    return (a is not None) ^ (b is not None)
