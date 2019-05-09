import copy
from collections import OrderedDict

# Necessary for static type checking
if False:  # flake8: noqa
    from typing import Any, List


class DefaultOrderedDict(OrderedDict):
    __slots__ = ("default_factory",)

    # Source: http://stackoverflow.com/a/6190500/562769
    def __init__(self, default_factory=None, *a, **kw):
        # type: (type, *Any, **Any) -> None
        if default_factory is not None and not callable(default_factory):
            raise TypeError("first argument must be callable")

        OrderedDict.__init__(self, *a, **kw)
        self.default_factory = default_factory

    def __missing__(self, key):
        # type: (str) -> Any
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

    def __reduce__(self):
        if self.default_factory is None:
            args = tuple()
        else:
            args = (self.default_factory,)
        return type(self), args, None, None, iter(self.items())

    def copy(self):
        return self.__copy__()

    def __copy__(self):
        return type(self)(self.default_factory, self)

    def __deepcopy__(self, memo):
        return self.__class__(self.default_factory, copy.deepcopy(list(self.items())))

    def __repr__(self):
        return "DefaultOrderedDict({}, {})".format(
            self.default_factory, OrderedDict.__repr__(self)[19:-1]
        )
