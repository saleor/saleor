import enum
from typing import Final, Literal


class _Unset(enum.Enum):
    UNSET = "unset"


UNSET: Final = _Unset.UNSET
Unset = Literal[_Unset.UNSET]
"""A sentinel for an argument left out, distinct from `None` meaning cleared."""
