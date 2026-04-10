from typing import Any


def maybe_to_int(o: Any) -> int:
    """Cast a given object to an integer if it's possible, otherwise it raises.

    It's a lenient parsing for backward compatibility.
    """

    if isinstance(o, str):
        if o.isnumeric() is False:
            raise ValueError("Value must be an integer")
        return int(o)

    if isinstance(o, int) is False:
        raise ValueError("Value must be an integer")

    return o
