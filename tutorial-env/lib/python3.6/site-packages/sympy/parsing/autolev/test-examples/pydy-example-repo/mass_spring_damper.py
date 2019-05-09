import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

m, k, b, g = sm.symbols('m k b g', real=True)
position, speed = me.dynamicsymbols('position speed')
positiond, speedd = me.dynamicsymbols('position speed', 1)
o = me.dynamicsymbols('o')
force = o*sm.sin(me.dynamicsymbols._t)
frame_ceiling = me.ReferenceFrame('ceiling')
point_origin = me.Point('origin')
point_origin.set_vel(frame_ceiling, 0)
particle_block = me.Particle('block', me.Point('block_pt'), sm.Symbol('m'))
particle_block.point.set_pos(point_origin, position*frame_ceiling.x)
particle_block.mass = m
particle_block.point.set_vel(frame_ceiling, speed*frame_ceiling.x)
force_magnitude = m*g-k*position-b*speed+force
force_block = (force_magnitude*frame_ceiling.x).subs({positiond:speed})
kd_eqs = [positiond - speed]
forceList = [(particle_block.point,(force_magnitude*frame_ceiling.x).subs({positiond:speed}))]
kane = me.KanesMethod(frame_ceiling, q_ind=[position], u_ind=[speed], kd_eqs = kd_eqs)
fr, frstar = kane.kanes_equations([particle_block], forceList)
zero = fr+frstar
from pydy.system import System
sys = System(kane, constants = {m:1.0, k:1.0, b:0.2, g:9.8},
specifieds={me.dynamicsymbols('t'):lambda x, t: t, o:2},
initial_conditions={position:0.1, speed:-1*1.0},
times = np.linspace(0.0, 10.0, 10.0/0.01))

y=sys.integrate()
