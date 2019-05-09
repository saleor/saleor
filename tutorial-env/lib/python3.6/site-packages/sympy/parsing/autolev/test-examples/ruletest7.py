import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

x, y = me.dynamicsymbols('x y')
xd, yd = me.dynamicsymbols('x y', 1)
e = sm.cos(x)+sm.sin(x)+sm.tan(x)+sm.cosh(x)+sm.sinh(x)+sm.tanh(x)+sm.acos(x)+sm.asin(x)+sm.atan(x)+sm.log(x)+sm.exp(x)+sm.sqrt(x)+sm.factorial(x)+sm.ceiling(x)+sm.floor(x)+sm.sign(x)
e = (x)**2+sm.log(x, 10)
a = sm.Abs(-1*1)+int(1.5)+round(1.9)
e1 = 2*x+3*y
e2 = x+y
am = sm.Matrix([e1.expand().coeff(x), e1.expand().coeff(y), e2.expand().coeff(x), e2.expand().coeff(y)]).reshape(2, 2)
b = (e1).expand().coeff(x)
c = (e2).expand().coeff(y)
d1 = (e1).collect(x).coeff(x,0)
d2 = (e1).collect(x).coeff(x,1)
fm = sm.Matrix([i.collect(x)for i in sm.Matrix([e1,e2]).reshape(1, 2)]).reshape((sm.Matrix([e1,e2]).reshape(1, 2)).shape[0], (sm.Matrix([e1,e2]).reshape(1, 2)).shape[1])
f = (e1).collect(y)
g = (e1).subs({x:2*x})
gm = sm.Matrix([i.subs({x:3}) for i in sm.Matrix([e1,e2]).reshape(2, 1)]).reshape((sm.Matrix([e1,e2]).reshape(2, 1)).shape[0], (sm.Matrix([e1,e2]).reshape(2, 1)).shape[1])
frame_a = me.ReferenceFrame('a')
frame_b = me.ReferenceFrame('b')
theta = me.dynamicsymbols('theta')
frame_b.orient(frame_a, 'Axis', [theta, frame_a.z])
v1=2*frame_a.x-3*frame_a.y+frame_a.z
v2=frame_b.x+frame_b.y+frame_b.z
a = me.dot(v1, v2)
bm = sm.Matrix([me.dot(v1, v2),me.dot(v1, 2*v2)]).reshape(2, 1)
c=me.cross(v1, v2)
d = 2*v1.magnitude()+3*v1.magnitude()
dyadic=me.outer(3*frame_a.x, frame_a.x)+me.outer(frame_a.y, frame_a.y)+me.outer(2*frame_a.z, frame_a.z)
am = (dyadic).to_matrix(frame_b)
m = sm.Matrix([1,2,3]).reshape(3, 1)
v=m[0]*frame_a.x +m[1]*frame_a.y +m[2]*frame_a.z
