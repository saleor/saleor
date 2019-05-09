import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

x, y = me.dynamicsymbols('x y')
a, b = sm.symbols('a b', real=True)
e = a*(b*x+y)**2
m = sm.Matrix([e,e]).reshape(2, 1)
e = e.expand()
m = sm.Matrix([i.expand() for i in m]).reshape((m).shape[0], (m).shape[1])
e = sm.factor(e, x)
m = sm.Matrix([sm.factor(i,x) for i in m]).reshape((m).shape[0], (m).shape[1])
eqn = sm.Matrix([[0]])
eqn[0] = a*x+b*y
eqn = eqn.row_insert(eqn.shape[0], sm.Matrix([[0]]))
eqn[eqn.shape[0]-1] = 2*a*x-3*b*y
print(sm.solve(eqn,x,y))
rhs_y = sm.solve(eqn,x,y)[y]
e = (x+y)**2+2*x**2
e.collect(x)
a, b, c = sm.symbols('a b c', real=True)
m = sm.Matrix([a,b,c,0]).reshape(2, 2)
m2 = sm.Matrix([i.subs({a:1,b:2,c:3}) for i in m]).reshape((m).shape[0], (m).shape[1])
eigvalue = sm.Matrix([i.evalf() for i in (m2).eigenvals().keys()])
eigvec = sm.Matrix([i[2][0].evalf() for i in (m2).eigenvects()]).reshape(m2.shape[0], m2.shape[1])
frame_n = me.ReferenceFrame('n')
frame_a = me.ReferenceFrame('a')
frame_a.orient(frame_n, 'Axis', [x, frame_n.x])
frame_a.orient(frame_n, 'Axis', [sm.pi/2, frame_n.x])
c1, c2, c3 = sm.symbols('c1 c2 c3', real=True)
v=c1*frame_a.x+c2*frame_a.y+c3*frame_a.z
point_o = me.Point('o')
point_p = me.Point('p')
point_o.set_pos(point_p, c1*frame_a.x)
v = (v).express(frame_n)
point_o.set_pos(point_p, (point_o.pos_from(point_p)).express(frame_n))
frame_a.set_ang_vel(frame_n, c3*frame_a.z)
print(frame_n.ang_vel_in(frame_a))
point_p.v2pt_theory(point_o,frame_n,frame_a)
particle_p1 = me.Particle('p1', me.Point('p1_pt'), sm.Symbol('m'))
particle_p2 = me.Particle('p2', me.Point('p2_pt'), sm.Symbol('m'))
particle_p2.point.v2pt_theory(particle_p1.point,frame_n,frame_a)
point_p.a2pt_theory(particle_p1.point,frame_n,frame_a)
body_b1_cm = me.Point('b1_cm')
body_b1_cm.set_vel(frame_n, 0)
body_b1_f = me.ReferenceFrame('b1_f')
body_b1 = me.RigidBody('b1', body_b1_cm, body_b1_f, sm.symbols('m'), (me.outer(body_b1_f.x,body_b1_f.x),body_b1_cm))
body_b2_cm = me.Point('b2_cm')
body_b2_cm.set_vel(frame_n, 0)
body_b2_f = me.ReferenceFrame('b2_f')
body_b2 = me.RigidBody('b2', body_b2_cm, body_b2_f, sm.symbols('m'), (me.outer(body_b2_f.x,body_b2_f.x),body_b2_cm))
g = sm.symbols('g', real=True)
force_p1 = particle_p1.mass*(g*frame_n.x)
force_p2 = particle_p2.mass*(g*frame_n.x)
force_b1 = body_b1.mass*(g*frame_n.x)
force_b2 = body_b2.mass*(g*frame_n.x)
z = me.dynamicsymbols('z')
v=x*frame_a.x+y*frame_a.z
point_o.set_pos(point_p, x*frame_a.x+y*frame_a.y)
v = (v).subs({x:2*z, y:z})
point_o.set_pos(point_p, (point_o.pos_from(point_p)).subs({x:2*z, y:z}))
force_o = -1*(x*y*frame_a.x)
force_p1 = particle_p1.mass*(g*frame_n.x)+ x*y*frame_a.x
