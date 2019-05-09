from .cache import clear_cache
from contextlib import contextmanager


class _global_function(list):
    """ The cache must be cleared whenever _global_function is changed. """

    def __setitem__(self, key, value):
        if (self[key] != value):
            clear_cache()
        super(_global_function, self).__setitem__(key, value)


global_evaluate = _global_function([True])
global_distribute = _global_function([True])


@contextmanager
def evaluate(x):
    """ Control automatic evaluation

    This context manager controls whether or not all SymPy functions evaluate
    by default.

    Note that much of SymPy expects evaluated expressions.  This functionality
    is experimental and is unlikely to function as intended on large
    expressions.

    Examples
    ========

    >>> from sympy.abc import x
    >>> from sympy.core.evaluate import evaluate
    >>> print(x + x)
    2*x
    >>> with evaluate(False):
    ...     print(x + x)
    x + x
    """

    old = global_evaluate[0]

    global_evaluate[0] = x
    yield
    global_evaluate[0] = old


@contextmanager
def distribute(x):
    """ Control automatic distribution of Number over Add

    This context manager controls whether or not Mul distribute Number over
    Add. Plan is to avoid distributing Number over Add in all of sympy. Once
    that is done, this contextmanager will be removed.

    Examples
    ========

    >>> from sympy.abc import x
    >>> from sympy.core.evaluate import distribute
    >>> print(2*(x + 1))
    2*x + 2
    >>> with distribute(False):
    ...     print(2*(x + 1))
    2*(x + 1)
    """

    old = global_distribute[0]

    global_distribute[0] = x
    yield
    global_distribute[0] = old
