import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

x, y = me.dynamicsymbols('x y')
a11, a12, a21, a22, b1, b2 = sm.symbols('a11 a12 a21 a22 b1 b2', real=True)
eqn = sm.Matrix([[0]])
eqn[0] = a11*x+a12*y-b1
eqn = eqn.row_insert(eqn.shape[0], sm.Matrix([[0]]))
eqn[eqn.shape[0]-1] = a21*x+a22*y-b2
eqn_list = []
for i in eqn:  eqn_list.append(i.subs({a11:2, a12:5, a21:3, a22:4, b1:7, b2:6}))
print(sm.linsolve(eqn_list, x,y))
