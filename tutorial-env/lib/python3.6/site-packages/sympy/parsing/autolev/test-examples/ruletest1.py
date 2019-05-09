import sympy.physics.mechanics as me
import sympy as sm
import math as m
import numpy as np

f = sm.S(3)
g = sm.S(9.81)
a, b = sm.symbols('a b', real=True)
s, s1 = sm.symbols('s s1', real=True)
s2, s3 = sm.symbols('s2 s3', real=True, nonnegative=True)
s4 = sm.symbols('s4', real=True, nonpositive=True)
k1, k2, k3, k4, l1, l2, l3, p11, p12, p13, p21, p22, p23 = sm.symbols('k1 k2 k3 k4 l1 l2 l3 p11 p12 p13 p21 p22 p23', real=True)
c11, c12, c13, c21, c22, c23 = sm.symbols('c11 c12 c13 c21 c22 c23', real=True)
e1 = a*f+s2-g
e2 = f**2+k3*k2*g
