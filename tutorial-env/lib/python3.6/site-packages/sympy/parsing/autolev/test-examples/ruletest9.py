import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

frame_n = me.ReferenceFrame('n')
frame_a = me.ReferenceFrame('a')
a=0
d=me.inertia(frame_a, 1, 1, 1)
point_po1 = me.Point('po1')
point_po2 = me.Point('po2')
particle_p1 = me.Particle('p1', me.Point('p1_pt'), sm.Symbol('m'))
particle_p2 = me.Particle('p2', me.Point('p2_pt'), sm.Symbol('m'))
c1, c2, c3 = me.dynamicsymbols('c1 c2 c3')
c1d, c2d, c3d = me.dynamicsymbols('c1 c2 c3', 1)
body_r_cm = me.Point('r_cm')
body_r_cm.set_vel(frame_n, 0)
body_r_f = me.ReferenceFrame('r_f')
body_r = me.RigidBody('r', body_r_cm, body_r_f, sm.symbols('m'), (me.outer(body_r_f.x,body_r_f.x),body_r_cm))
point_po2.set_pos(particle_p1.point, c1*frame_a.x)
v=2*point_po2.pos_from(particle_p1.point)+c2*frame_a.y
frame_a.set_ang_vel(frame_n, c3*frame_a.z)
v=2*frame_a.ang_vel_in(frame_n)+c2*frame_a.y
body_r_f.set_ang_vel(frame_n, c3*frame_a.z)
v=2*body_r_f.ang_vel_in(frame_n)+c2*frame_a.y
frame_a.set_ang_acc(frame_n, (frame_a.ang_vel_in(frame_n)).dt(frame_a))
v=2*frame_a.ang_acc_in(frame_n)+c2*frame_a.y
particle_p1.point.set_vel(frame_a, c1*frame_a.x+c3*frame_a.y)
body_r_cm.set_acc(frame_n, c2*frame_a.y)
v_a = me.cross(body_r_cm.acc(frame_n), particle_p1.point.vel(frame_a))
x_b_c = v_a
x_b_d = 2*x_b_c
a_b_c_d_e=x_b_d*2
a_b_c = 2*c1*c2*c3
a_b_c += 2*c1
a_b_c  =  3*c1
q1, q2, u1, u2 = me.dynamicsymbols('q1 q2 u1 u2')
q1d, q2d, u1d, u2d = me.dynamicsymbols('q1 q2 u1 u2', 1)
x, y = me.dynamicsymbols('x y')
xd, yd = me.dynamicsymbols('x y', 1)
xd2, yd2 = me.dynamicsymbols('x y', 2)
yy = me.dynamicsymbols('yy')
yy = x*xd**2+1
m = sm.Matrix([[0]])
m[0] = 2*x
m = m.row_insert(m.shape[0], sm.Matrix([[0]]))
m[m.shape[0]-1] = 2*y
a = 2*m[0]
m = sm.Matrix([1,2,3,4,5,6,7,8,9]).reshape(3, 3)
m[0,1]=5
a = m[0, 1]*2
force_ro = q1*frame_n.x
torque_a = q2*frame_n.z
force_ro = q1*frame_n.x + q2*frame_n.y
f=force_ro*2
