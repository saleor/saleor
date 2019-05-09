from sympy import symbols
from sympy.physics.mechanics import Point, Particle, ReferenceFrame


def test_particle():
    m, m2, v1, v2, v3, r, g, h = symbols('m m2 v1 v2 v3 r g h')
    P = Point('P')
    P2 = Point('P2')
    p = Particle('pa', P, m)
    assert p.mass == m
    assert p.point == P
    # Test the mass setter
    p.mass = m2
    assert p.mass == m2
    # Test the point setter
    p.point = P2
    assert p.point == P2
    # Test the linear momentum function
    N = ReferenceFrame('N')
    O = Point('O')
    P2.set_pos(O, r * N.y)
    P2.set_vel(N, v1 * N.x)
    assert p.linear_momentum(N) == m2 * v1 * N.x
    assert p.angular_momentum(O, N) == -m2 * r *v1 * N.z
    P2.set_vel(N, v2 * N.y)
    assert p.linear_momentum(N) == m2 * v2 * N.y
    assert p.angular_momentum(O, N) == 0
    P2.set_vel(N, v3 * N.z)
    assert p.linear_momentum(N) == m2 * v3 * N.z
    assert p.angular_momentum(O, N) == m2 * r * v3 * N.x
    P2.set_vel(N, v1 * N.x + v2 * N.y + v3 * N.z)
    assert p.linear_momentum(N) == m2 * (v1 * N.x + v2 * N.y + v3 * N.z)
    assert p.angular_momentum(O, N) == m2 * r * (v3 * N.x - v1 * N.z)
    p.potential_energy = m * g * h
    assert p.potential_energy == m * g * h
    # TODO make the result not be system-dependent
    assert p.kinetic_energy(
        N) in [m2*(v1**2 + v2**2 + v3**2)/2,
        m2 * v1**2 / 2 + m2 * v2**2 / 2 + m2 * v3**2 / 2]
