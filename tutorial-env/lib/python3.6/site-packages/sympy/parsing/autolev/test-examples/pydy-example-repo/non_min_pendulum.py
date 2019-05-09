import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

q1, q2 = me.dynamicsymbols('q1 q2')
q1d, q2d = me.dynamicsymbols('q1 q2', 1)
q1d2, q2d2 = me.dynamicsymbols('q1 q2', 2)
l, m, g = sm.symbols('l m g', real=True)
frame_n = me.ReferenceFrame('n')
point_pn = me.Point('pn')
point_pn.set_vel(frame_n, 0)
theta1 = sm.atan(q2/q1)
frame_a = me.ReferenceFrame('a')
frame_a.orient(frame_n, 'Axis', [theta1, frame_n.z])
particle_p = me.Particle('p', me.Point('p_pt'), sm.Symbol('m'))
particle_p.point.set_pos(point_pn, q1*frame_n.x+q2*frame_n.y)
particle_p.mass = m
particle_p.point.set_vel(frame_n, (point_pn.pos_from(particle_p.point)).dt(frame_n))
f_v = me.dot((particle_p.point.vel(frame_n)).express(frame_a), frame_a.x)
force_p = particle_p.mass*(g*frame_n.x)
dependent = sm.Matrix([[0]])
dependent[0] = f_v
velocity_constraints = [i for i in dependent]
u_q1d = me.dynamicsymbols('u_q1d')
u_q2d = me.dynamicsymbols('u_q2d')
kd_eqs = [q1d-u_q1d, q2d-u_q2d]
forceList = [(particle_p.point,particle_p.mass*(g*frame_n.x))]
kane = me.KanesMethod(frame_n, q_ind=[q1,q2], u_ind=[u_q2d], u_dependent=[u_q1d], kd_eqs = kd_eqs, velocity_constraints = velocity_constraints)
fr, frstar = kane.kanes_equations([particle_p], forceList)
zero = fr+frstar
f_c = point_pn.pos_from(particle_p.point).magnitude()-l
config = sm.Matrix([[0]])
config[0] = f_c
zero = zero.row_insert(zero.shape[0], sm.Matrix([[0]]))
zero[zero.shape[0]-1] = config[0]
