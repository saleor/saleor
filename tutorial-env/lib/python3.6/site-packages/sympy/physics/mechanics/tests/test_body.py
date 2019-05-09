from sympy.core.backend import Symbol, symbols
from sympy.physics.vector import Point, ReferenceFrame
from sympy.physics.mechanics import inertia, Body
from sympy.utilities.pytest import raises

def test_default():
    body = Body('body')
    assert body.name == 'body'
    assert body.loads == []
    point = Point('body_masscenter')
    point.set_vel(body.frame, 0)
    com = body.masscenter
    frame = body.frame
    assert com.vel(frame) == point.vel(frame)
    assert body.mass == Symbol('body_mass')
    ixx, iyy, izz = symbols('body_ixx body_iyy body_izz')
    ixy, iyz, izx = symbols('body_ixy body_iyz body_izx')
    assert body.inertia == (inertia(body.frame, ixx, iyy, izz, ixy, iyz, izx),
                            body.masscenter)


def test_custom_rigid_body():
    # Body with RigidBody.
    rigidbody_masscenter = Point('rigidbody_masscenter')
    rigidbody_mass = Symbol('rigidbody_mass')
    rigidbody_frame = ReferenceFrame('rigidbody_frame')
    body_inertia = inertia(rigidbody_frame, 1, 0, 0)
    rigid_body = Body('rigidbody_body', rigidbody_masscenter, rigidbody_mass,
                      rigidbody_frame, body_inertia)
    com = rigid_body.masscenter
    frame = rigid_body.frame
    rigidbody_masscenter.set_vel(rigidbody_frame, 0)
    assert com.vel(frame) == rigidbody_masscenter.vel(frame)
    assert com.pos_from(com) == rigidbody_masscenter.pos_from(com)

    assert rigid_body.mass == rigidbody_mass
    assert rigid_body.inertia == (body_inertia, rigidbody_masscenter)

    assert hasattr(rigid_body, 'masscenter')
    assert hasattr(rigid_body, 'mass')
    assert hasattr(rigid_body, 'frame')
    assert hasattr(rigid_body, 'inertia')


def test_particle_body():
    #  Body with Particle
    particle_masscenter = Point('particle_masscenter')
    particle_mass = Symbol('particle_mass')
    particle_frame = ReferenceFrame('particle_frame')
    particle_body = Body('particle_body', particle_masscenter, particle_mass,
                         particle_frame)
    com = particle_body.masscenter
    frame = particle_body.frame
    particle_masscenter.set_vel(particle_frame, 0)
    assert com.vel(frame) == particle_masscenter.vel(frame)
    assert com.pos_from(com) == particle_masscenter.pos_from(com)

    assert particle_body.mass == particle_mass
    assert not hasattr(particle_body, "_inertia")
    assert hasattr(particle_body, 'frame')
    assert hasattr(particle_body, 'masscenter')
    assert hasattr(particle_body, 'mass')


def test_particle_body_add_force():
    #  Body with Particle
    particle_masscenter = Point('particle_masscenter')
    particle_mass = Symbol('particle_mass')
    particle_frame = ReferenceFrame('particle_frame')
    particle_body = Body('particle_body', particle_masscenter, particle_mass,
                         particle_frame)

    a = Symbol('a')
    force_vector = a * particle_body.frame.x
    particle_body.apply_force(force_vector, particle_body.masscenter)
    assert len(particle_body.loads) == 1
    point = particle_body.masscenter.locatenew(
        particle_body._name + '_point0', 0)
    point.set_vel(particle_body.frame, 0)
    force_point = particle_body.loads[0][0]

    frame = particle_body.frame
    assert force_point.vel(frame) == point.vel(frame)
    assert force_point.pos_from(force_point) == point.pos_from(force_point)

    assert particle_body.loads[0][1] == force_vector


def test_body_add_force():
    # Body with RigidBody.
    rigidbody_masscenter = Point('rigidbody_masscenter')
    rigidbody_mass = Symbol('rigidbody_mass')
    rigidbody_frame = ReferenceFrame('rigidbody_frame')
    body_inertia = inertia(rigidbody_frame, 1, 0, 0)
    rigid_body = Body('rigidbody_body', rigidbody_masscenter, rigidbody_mass,
                      rigidbody_frame, body_inertia)

    l = Symbol('l')
    Fa = Symbol('Fa')
    point = rigid_body.masscenter.locatenew(
        'rigidbody_body_point0',
        l * rigid_body.frame.x)
    point.set_vel(rigid_body.frame, 0)
    force_vector = Fa * rigid_body.frame.z
    # apply_force with point
    rigid_body.apply_force(force_vector, point)
    assert len(rigid_body.loads) == 1
    force_point = rigid_body.loads[0][0]
    frame = rigid_body.frame
    assert force_point.vel(frame) == point.vel(frame)
    assert force_point.pos_from(force_point) == point.pos_from(force_point)
    assert rigid_body.loads[0][1] == force_vector
    # apply_force without point
    rigid_body.apply_force(force_vector)
    assert len(rigid_body.loads) == 2
    assert rigid_body.loads[1][1] == force_vector
    # passing something else than point
    raises(TypeError, lambda: rigid_body.apply_force(force_vector,  0))
    raises(TypeError, lambda: rigid_body.apply_force(0))

def test_body_add_torque():
    body = Body('body')
    torque_vector = body.frame.x
    body.apply_torque(torque_vector)

    assert len(body.loads) == 1
    assert body.loads[0] == (body.frame, torque_vector)
    raises(TypeError, lambda: body.apply_torque(0))
