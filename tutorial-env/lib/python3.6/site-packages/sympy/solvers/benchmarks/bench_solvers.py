from __future__ import print_function, division

from sympy import zeros, eye, Symbol, solve_linear_system
from sympy.core.compatibility import range

N = 8
M = zeros(N, N + 1)
M[:, :N] = eye(N)
S = [Symbol('A%i' % i) for i in range(N)]


def timeit_linsolve_trivial():
    solve_linear_system(M, *S)
