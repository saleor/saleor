# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Dict, Any


class PairSet(object):
    __slots__ = ("_data",)

    def __init__(self):
        # type: () -> None
        self._data = {}  # type: Dict[str, Any]

    def __contains__(self, item):
        return self.has(item[0], item[1], item[2])

    def __str__(self):
        return str(self._data)

    def __repr__(self):
        return str(self._data)

    def has(self, a, b, are_mutually_exclusive):
        first = self._data.get(a)
        result = first and first.get(b)
        if result is None:
            return False

        # are_mutually_exclusive being false is a superset of being true,
        # hence if we want to know if this PairSet "has" these two with no
        # exclusivity, we have to ensure it was added as such.
        if not are_mutually_exclusive:
            return not result

        return True

    def add(self, a, b, are_mutually_exclusive):
        _pair_set_add(self._data, a, b, are_mutually_exclusive)
        _pair_set_add(self._data, b, a, are_mutually_exclusive)
        return self


def _pair_set_add(data, a, b, are_mutually_exclusive):
    sub_dict = data.get(a)

    if not sub_dict:
        sub_dict = {}
        data[a] = sub_dict

    sub_dict[b] = are_mutually_exclusive
