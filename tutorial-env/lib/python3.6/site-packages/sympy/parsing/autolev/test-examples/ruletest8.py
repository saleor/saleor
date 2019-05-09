import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

frame_a = me.ReferenceFrame('a')
c1, c2, c3 = sm.symbols('c1 c2 c3', real=True)
a=me.inertia(frame_a, 1, 1, 1)
particle_p1 = me.Particle('p1', me.Point('p1_pt'), sm.Symbol('m'))
particle_p2 = me.Particle('p2', me.Point('p2_pt'), sm.Symbol('m'))
body_r_cm = me.Point('r_cm')
body_r_f = me.ReferenceFrame('r_f')
body_r = me.RigidBody('r', body_r_cm, body_r_f, sm.symbols('m'), (me.outer(body_r_f.x,body_r_f.x),body_r_cm))
frame_a.orient(body_r_f, 'DCM', sm.Matrix([1,1,1,1,1,0,0,0,1]).reshape(3, 3))
point_o = me.Point('o')
m1 = sm.symbols('m1')
particle_p1.mass = m1
m2 = sm.symbols('m2')
particle_p2.mass = m2
mr = sm.symbols('mr')
body_r.mass = mr
i1 = sm.symbols('i1')
i2 = sm.symbols('i2')
i3 = sm.symbols('i3')
body_r.inertia = (me.inertia(body_r_f, i1, i2, i3, 0, 0, 0), body_r_cm)
point_o.set_pos(particle_p1.point, c1*frame_a.x)
point_o.set_pos(particle_p2.point, c2*frame_a.y)
point_o.set_pos(body_r_cm, c3*frame_a.z)
a=me.inertia_of_point_mass(particle_p1.mass, particle_p1.point.pos_from(point_o), frame_a)
a=me.inertia_of_point_mass(particle_p2.mass, particle_p2.point.pos_from(point_o), frame_a)
a=body_r.inertia[0] + me.inertia_of_point_mass(body_r.mass, body_r.masscenter.pos_from(point_o), frame_a)
a=me.inertia_of_point_mass(particle_p1.mass, particle_p1.point.pos_from(point_o), frame_a) + me.inertia_of_point_mass(particle_p2.mass, particle_p2.point.pos_from(point_o), frame_a) + body_r.inertia[0] + me.inertia_of_point_mass(body_r.mass, body_r.masscenter.pos_from(point_o), frame_a)
a=me.inertia_of_point_mass(particle_p1.mass, particle_p1.point.pos_from(point_o), frame_a) + body_r.inertia[0] + me.inertia_of_point_mass(body_r.mass, body_r.masscenter.pos_from(point_o), frame_a)
a=body_r.inertia[0] + me.inertia_of_point_mass(body_r.mass, body_r.masscenter.pos_from(point_o), frame_a)
a=body_r.inertia[0]
particle_p2.point.set_pos(particle_p1.point, c1*frame_a.x+c2*frame_a.y)
body_r_cm.set_pos(particle_p1.point, c3*frame_a.x)
body_r_cm.set_pos(particle_p2.point, c3*frame_a.y)
b=me.functions.center_of_mass(point_o,particle_p1, particle_p2, body_r)
b=me.functions.center_of_mass(point_o,particle_p1, body_r)
b=me.functions.center_of_mass(particle_p1.point,particle_p1, particle_p2, body_r)
u1, u2, u3 = me.dynamicsymbols('u1 u2 u3')
v=u1*frame_a.x+u2*frame_a.y+u3*frame_a.z
u=(v+c1*frame_a.x).normalize()
particle_p1.point.set_vel(frame_a, u1*frame_a.x)
a=particle_p1.point.partial_velocity(frame_a, u1)
m = particle_p1.mass+body_r.mass
m = particle_p2.mass
m = particle_p1.mass+particle_p2.mass+body_r.mass
