from sympy import (Symbol, gamma, expand_func, beta, digamma, diff)


def test_beta():
    x, y = Symbol('x'), Symbol('y')

    assert isinstance(beta(x, y), beta)

    assert expand_func(beta(x, y)) == gamma(x)*gamma(y)/gamma(x + y)
    assert expand_func(beta(x, y) - beta(y, x)) == 0  # Symmetric
    assert expand_func(beta(x, y)) == expand_func(beta(x, y + 1) + beta(x + 1, y)).simplify()

    assert diff(beta(x, y), x) == beta(x, y)*(digamma(x) - digamma(x + y))
    assert diff(beta(x, y), y) == beta(x, y)*(digamma(y) - digamma(x + y))
