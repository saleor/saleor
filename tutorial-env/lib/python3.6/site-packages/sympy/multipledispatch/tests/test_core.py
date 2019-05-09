from sympy.multipledispatch import dispatch
from sympy.multipledispatch.conflict import AmbiguityWarning
from sympy.utilities.pytest import raises, XFAIL, warns
from functools import partial

test_namespace = dict()

orig_dispatch = dispatch
dispatch = partial(dispatch, namespace=test_namespace)


@XFAIL
def test_singledispatch():
    @dispatch(int)
    def f(x):
        return x + 1

    @dispatch(int)
    def g(x):
        return x + 2

    @dispatch(float)
    def f(x):
        return x - 1

    assert f(1) == 2
    assert g(1) == 3
    assert f(1.0) == 0

    assert raises(NotImplementedError, lambda: f('hello'))


def test_multipledispatch():
    @dispatch(int, int)
    def f(x, y):
        return x + y

    @dispatch(float, float)
    def f(x, y):
        return x - y

    assert f(1, 2) == 3
    assert f(1.0, 2.0) == -1.0


class A(object): pass
class B(object): pass
class C(A): pass
class D(C): pass
class E(C): pass


def test_inheritance():
    @dispatch(A)
    def f(x):
        return 'a'

    @dispatch(B)
    def f(x):
        return 'b'

    assert f(A()) == 'a'
    assert f(B()) == 'b'
    assert f(C()) == 'a'


@XFAIL
def test_inheritance_and_multiple_dispatch():
    @dispatch(A, A)
    def f(x, y):
        return type(x), type(y)

    @dispatch(A, B)
    def f(x, y):
        return 0

    assert f(A(), A()) == (A, A)
    assert f(A(), C()) == (A, C)
    assert f(A(), B()) == 0
    assert f(C(), B()) == 0
    assert raises(NotImplementedError, lambda: f(B(), B()))


def test_competing_solutions():
    @dispatch(A)
    def h(x):
        return 1

    @dispatch(C)
    def h(x):
        return 2

    assert h(D()) == 2


def test_competing_multiple():
    @dispatch(A, B)
    def h(x, y):
        return 1

    @dispatch(C, B)
    def h(x, y):
        return 2

    assert h(D(), B()) == 2


def test_competing_ambiguous():
    test_namespace = dict()
    dispatch = partial(orig_dispatch, namespace=test_namespace)

    @dispatch(A, C)
    def f(x, y):
        return 2

    with warns(AmbiguityWarning):
        @dispatch(C, A)
        def f(x, y):
            return 2

    assert f(A(), C()) == f(C(), A()) == 2
    # assert raises(Warning, lambda : f(C(), C()))


def test_caching_correct_behavior():
    @dispatch(A)
    def f(x):
        return 1

    assert f(C()) == 1

    @dispatch(C)
    def f(x):
        return 2

    assert f(C()) == 2


def test_union_types():
    @dispatch((A, C))
    def f(x):
        return 1

    assert f(A()) == 1
    assert f(C()) == 1


def test_namespaces():
    ns1 = dict()
    ns2 = dict()

    def foo(x):
        return 1
    foo1 = orig_dispatch(int, namespace=ns1)(foo)

    def foo(x):
        return 2
    foo2 = orig_dispatch(int, namespace=ns2)(foo)

    assert foo1(0) == 1
    assert foo2(0) == 2


"""
Fails
def test_dispatch_on_dispatch():
    @dispatch(A)
    @dispatch(C)
    def q(x):
        return 1

    assert q(A()) == 1
    assert q(C()) == 1
"""


def test_methods():
    class Foo(object):
        @dispatch(float)
        def f(self, x):
            return x - 1

        @dispatch(int)
        def f(self, x):
            return x + 1

        @dispatch(int)
        def g(self, x):
            return x + 3


    foo = Foo()
    assert foo.f(1) == 2
    assert foo.f(1.0) == 0.0
    assert foo.g(1) == 4


def test_methods_multiple_dispatch():
    class Foo(object):
        @dispatch(A, A)
        def f(x, y):
            return 1

        @dispatch(A, C)
        def f(x, y):
            return 2


    foo = Foo()
    assert foo.f(A(), A()) == 1
    assert foo.f(A(), C()) == 2
    assert foo.f(C(), C()) == 2
