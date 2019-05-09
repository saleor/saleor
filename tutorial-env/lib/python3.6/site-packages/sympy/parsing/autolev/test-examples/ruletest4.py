import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

frame_a = me.ReferenceFrame('a')
frame_b = me.ReferenceFrame('b')
q1, q2, q3 = me.dynamicsymbols('q1 q2 q3')
frame_b.orient(frame_a, 'Axis', [q3, frame_a.x])
dcm = frame_a.dcm(frame_b)
m = dcm*3-frame_a.dcm(frame_b)
r = me.dynamicsymbols('r')
circle_area = sm.pi*r**2
u, a = me.dynamicsymbols('u a')
x, y = me.dynamicsymbols('x y')
s = u*me.dynamicsymbols._t-1/2*a*me.dynamicsymbols._t**2
expr1 = 2*a*0.5-1.25+0.25
expr2 = -1*x**2+y**2+0.25*(x+y)**2
expr3 = 0.5*10**(-10)
dyadic=me.outer(frame_a.x, frame_a.x)+me.outer(frame_a.y, frame_a.y)+me.outer(frame_a.z, frame_a.z)
