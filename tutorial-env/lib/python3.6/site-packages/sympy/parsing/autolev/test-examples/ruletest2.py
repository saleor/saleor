import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

x1, x2 = me.dynamicsymbols('x1 x2')
f1 = x1*x2+3*x1**2
f2 = x1*me.dynamicsymbols._t+x2*me.dynamicsymbols._t**2
x, y = me.dynamicsymbols('x y')
xd, yd = me.dynamicsymbols('x y', 1)
yd2 = me.dynamicsymbols('y', 2)
q1, q2, q3, u1, u2 = me.dynamicsymbols('q1 q2 q3 u1 u2')
p1, p2 = me.dynamicsymbols('p1 p2')
p1d, p2d = me.dynamicsymbols('p1 p2', 1)
w1, w2, w3, r1, r2 = me.dynamicsymbols('w1 w2 w3 r1 r2')
w1d, w2d, w3d, r1d, r2d = me.dynamicsymbols('w1 w2 w3 r1 r2', 1)
r1d2, r2d2 = me.dynamicsymbols('r1 r2', 2)
c11, c12, c21, c22 = me.dynamicsymbols('c11 c12 c21 c22')
d11, d12, d13 = me.dynamicsymbols('d11 d12 d13')
j1, j2 = me.dynamicsymbols('j1 j2')
n = sm.symbols('n')
n = sm.I
