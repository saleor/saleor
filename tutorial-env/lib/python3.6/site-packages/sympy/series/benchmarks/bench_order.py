from __future__ import print_function, division

from sympy import Symbol, O, Add

x = Symbol('x')
l = list(x**i for i in range(1000))
l.append(O(x**1001))

def timeit_order_1x():
    _ = Add(*l)
