import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

frame_a = me.ReferenceFrame('a')
frame_b = me.ReferenceFrame('b')
frame_n = me.ReferenceFrame('n')
x1, x2, x3 = me.dynamicsymbols('x1 x2 x3')
l = sm.symbols('l', real=True)
v1=x1*frame_a.x+x2*frame_a.y+x3*frame_a.z
v2=x1*frame_b.x+x2*frame_b.y+x3*frame_b.z
v3=x1*frame_n.x+x2*frame_n.y+x3*frame_n.z
v=v1+v2+v3
point_c = me.Point('c')
point_d = me.Point('d')
point_po1 = me.Point('po1')
point_po2 = me.Point('po2')
point_po3 = me.Point('po3')
particle_l = me.Particle('l', me.Point('l_pt'), sm.Symbol('m'))
particle_p1 = me.Particle('p1', me.Point('p1_pt'), sm.Symbol('m'))
particle_p2 = me.Particle('p2', me.Point('p2_pt'), sm.Symbol('m'))
particle_p3 = me.Particle('p3', me.Point('p3_pt'), sm.Symbol('m'))
body_s_cm = me.Point('s_cm')
body_s_cm.set_vel(frame_n, 0)
body_s_f = me.ReferenceFrame('s_f')
body_s = me.RigidBody('s', body_s_cm, body_s_f, sm.symbols('m'), (me.outer(body_s_f.x,body_s_f.x),body_s_cm))
body_r1_cm = me.Point('r1_cm')
body_r1_cm.set_vel(frame_n, 0)
body_r1_f = me.ReferenceFrame('r1_f')
body_r1 = me.RigidBody('r1', body_r1_cm, body_r1_f, sm.symbols('m'), (me.outer(body_r1_f.x,body_r1_f.x),body_r1_cm))
body_r2_cm = me.Point('r2_cm')
body_r2_cm.set_vel(frame_n, 0)
body_r2_f = me.ReferenceFrame('r2_f')
body_r2 = me.RigidBody('r2', body_r2_cm, body_r2_f, sm.symbols('m'), (me.outer(body_r2_f.x,body_r2_f.x),body_r2_cm))
v4=x1*body_s_f.x+x2*body_s_f.y+x3*body_s_f.z
body_s_cm.set_pos(point_c, l*frame_n.x)
