import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

x, y = me.dynamicsymbols('x y')
xd, yd = me.dynamicsymbols('x y', 1)
e1 = (x+y)**2+(x-y)**3
e2 = (x-y)**2
e3 = x**2+y**2+2*x*y
m1 = sm.Matrix([e1,e2]).reshape(2, 1)
m2 = sm.Matrix([(x+y)**2,(x-y)**2]).reshape(1, 2)
m3 = m1+sm.Matrix([x,y]).reshape(2, 1)
am = sm.Matrix([i.expand() for i in m1]).reshape((m1).shape[0], (m1).shape[1])
cm = sm.Matrix([i.expand() for i in sm.Matrix([(x+y)**2,(x-y)**2]).reshape(1, 2)]).reshape((sm.Matrix([(x+y)**2,(x-y)**2]).reshape(1, 2)).shape[0], (sm.Matrix([(x+y)**2,(x-y)**2]).reshape(1, 2)).shape[1])
em = sm.Matrix([i.expand() for i in m1+sm.Matrix([x,y]).reshape(2, 1)]).reshape((m1+sm.Matrix([x,y]).reshape(2, 1)).shape[0], (m1+sm.Matrix([x,y]).reshape(2, 1)).shape[1])
f = (e1).expand()
g = (e2).expand()
a = sm.factor((e3), x)
bm = sm.Matrix([sm.factor(i, x) for i in m1]).reshape((m1).shape[0], (m1).shape[1])
cm = sm.Matrix([sm.factor(i, x) for i in m1+sm.Matrix([x,y]).reshape(2, 1)]).reshape((m1+sm.Matrix([x,y]).reshape(2, 1)).shape[0], (m1+sm.Matrix([x,y]).reshape(2, 1)).shape[1])
a = (e3).diff(x)
b = (e3).diff(y)
cm = sm.Matrix([i.diff(x) for i in m2]).reshape((m2).shape[0], (m2).shape[1])
dm = sm.Matrix([i.diff(x) for i in m1+sm.Matrix([x,y]).reshape(2, 1)]).reshape((m1+sm.Matrix([x,y]).reshape(2, 1)).shape[0], (m1+sm.Matrix([x,y]).reshape(2, 1)).shape[1])
frame_a = me.ReferenceFrame('a')
frame_b = me.ReferenceFrame('b')
frame_b.orient(frame_a, 'DCM', sm.Matrix([1,0,0,1,0,0,1,0,0]).reshape(3, 3))
v1=x*frame_a.x+y*frame_a.y+x*y*frame_a.z
e=(v1).diff(x, frame_b)
fm = sm.Matrix([i.diff(sm.Symbol('t')) for i in m1]).reshape((m1).shape[0], (m1).shape[1])
gm = sm.Matrix([i.diff(sm.Symbol('t')) for i in sm.Matrix([(x+y)**2,(x-y)**2]).reshape(1, 2)]).reshape((sm.Matrix([(x+y)**2,(x-y)**2]).reshape(1, 2)).shape[0], (sm.Matrix([(x+y)**2,(x-y)**2]).reshape(1, 2)).shape[1])
h=(v1).dt(frame_b)
