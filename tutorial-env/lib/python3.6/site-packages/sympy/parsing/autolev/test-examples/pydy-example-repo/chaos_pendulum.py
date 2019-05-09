import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

g, lb, w, h = sm.symbols('g lb w h', real=True)
theta, phi, omega, alpha = me.dynamicsymbols('theta phi omega alpha')
thetad, phid, omegad, alphad = me.dynamicsymbols('theta phi omega alpha', 1)
thetad2, phid2 = me.dynamicsymbols('theta phi', 2)
frame_n = me.ReferenceFrame('n')
body_a_cm = me.Point('a_cm')
body_a_cm.set_vel(frame_n, 0)
body_a_f = me.ReferenceFrame('a_f')
body_a = me.RigidBody('a', body_a_cm, body_a_f, sm.symbols('m'), (me.outer(body_a_f.x,body_a_f.x),body_a_cm))
body_b_cm = me.Point('b_cm')
body_b_cm.set_vel(frame_n, 0)
body_b_f = me.ReferenceFrame('b_f')
body_b = me.RigidBody('b', body_b_cm, body_b_f, sm.symbols('m'), (me.outer(body_b_f.x,body_b_f.x),body_b_cm))
body_a_f.orient(frame_n, 'Axis', [theta, frame_n.y])
body_b_f.orient(body_a_f, 'Axis', [phi, body_a_f.z])
point_o = me.Point('o')
la = (lb-h/2)/2
body_a_cm.set_pos(point_o, la*body_a_f.z)
body_b_cm.set_pos(point_o, lb*body_a_f.z)
body_a_f.set_ang_vel(frame_n, omega*frame_n.y)
body_b_f.set_ang_vel(body_a_f, alpha*body_a_f.z)
point_o.set_vel(frame_n, 0)
body_a_cm.v2pt_theory(point_o,frame_n,body_a_f)
body_b_cm.v2pt_theory(point_o,frame_n,body_a_f)
ma = sm.symbols('ma')
body_a.mass = ma
mb = sm.symbols('mb')
body_b.mass = mb
iaxx = 1/12*ma*(2*la)**2
iayy = iaxx
iazz = 0
ibxx = 1/12*mb*h**2
ibyy = 1/12*mb*(w**2+h**2)
ibzz = 1/12*mb*w**2
body_a.inertia = (me.inertia(body_a_f, iaxx, iayy, iazz, 0, 0, 0), body_a_cm)
body_b.inertia = (me.inertia(body_b_f, ibxx, ibyy, ibzz, 0, 0, 0), body_b_cm)
force_a = body_a.mass*(g*frame_n.z)
force_b = body_b.mass*(g*frame_n.z)
kd_eqs = [thetad - omega, phid - alpha]
forceList = [(body_a.masscenter,body_a.mass*(g*frame_n.z)), (body_b.masscenter,body_b.mass*(g*frame_n.z))]
kane = me.KanesMethod(frame_n, q_ind=[theta,phi], u_ind=[omega, alpha], kd_eqs = kd_eqs)
fr, frstar = kane.kanes_equations([body_a, body_b], forceList)
zero = fr+frstar
from pydy.system import System
sys = System(kane, constants = {g:9.81, lb:0.2, w:0.2, h:0.1, ma:0.01, mb:0.1},
specifieds={},
initial_conditions={theta:np.deg2rad(90), phi:np.deg2rad(0.5), omega:0, alpha:0},
times = np.linspace(0.0, 10, 10/0.02))

y=sys.integrate()
