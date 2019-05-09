from sympy import (Rational, Float, S, Symbol, cos, oo, pi, simplify,
    sin, sqrt, symbols, acos)
from sympy.core.compatibility import range
from sympy.functions.elementary.trigonometric import tan
from sympy.geometry import (Circle, GeometryError, Line, Point, Ray,
    Segment, Triangle, intersection, Point3D, Line3D, Ray3D, Segment3D,
    Point2D, Line2D)
from sympy.geometry.line import Undecidable
from sympy.geometry.polygon import _asa as asa
from sympy.utilities.iterables import cartes
from sympy.utilities.pytest import raises, slow, warns

import traceback
import sys

x = Symbol('x', real=True)
y = Symbol('y', real=True)
z = Symbol('z', real=True)
k = Symbol('k', real=True)
x1 = Symbol('x1', real=True)
y1 = Symbol('y1', real=True)
t = Symbol('t', real=True)
a, b = symbols('a,b', real=True)
m = symbols('m', real=True)


def test_object_from_equation():
    from sympy.abc import x, y, a, b
    assert Line(3*x + y + 18) == Line2D(Point2D(0, -18), Point2D(1, -21))
    assert Line(3*x + 5 * y + 1) == Line2D(Point2D(0, -S(1)/5), Point2D(1, -S(4)/5))
    assert Line(3*a + b + 18, x='a', y='b') == Line2D(Point2D(0, -18), Point2D(1, -21))
    assert Line(3*x + y) == Line2D(Point2D(0, 0), Point2D(1, -3))
    assert Line(x + y) == Line2D(Point2D(0, 0), Point2D(1, -1))
    raises(ValueError, lambda: Line(x))
    raises(ValueError, lambda: Line(y))
    raises(ValueError, lambda: Line(x/y))
    raises(ValueError, lambda: Line(a/b, x='a', y='b'))
    raises(ValueError, lambda: Line(y/x))
    raises(ValueError, lambda: Line(b/a, x='a', y='b'))
    raises(ValueError, lambda: Line((x + 1)**2 + y))


def feq(a, b):
    """Test if two floating point values are 'equal'."""
    t_float = Float("1.0E-10")
    return -t_float < a - b < t_float


def test_angle_between():
    a = Point(1, 2, 3, 4)
    b = a.orthogonal_direction
    o = a.origin
    assert feq(Line.angle_between(Line(Point(0, 0), Point(1, 1)),
                                  Line(Point(0, 0), Point(5, 0))).evalf(), pi.evalf() / 4)
    assert Line(a, o).angle_between(Line(b, o)) == pi / 2
    assert Line3D.angle_between(Line3D(Point3D(0, 0, 0), Point3D(1, 1, 1)),
                                Line3D(Point3D(0, 0, 0), Point3D(5, 0, 0))) == acos(sqrt(3) / 3)


def test_closing_angle():
    a = Ray((0, 0), angle=0)
    b = Ray((1, 2), angle=pi/2)
    assert a.closing_angle(b) == -pi/2
    assert b.closing_angle(a) == pi/2
    assert a.closing_angle(a) == 0


def test_arbitrary_point():
    l1 = Line3D(Point3D(0, 0, 0), Point3D(1, 1, 1))
    l2 = Line(Point(x1, x1), Point(y1, y1))
    assert l2.arbitrary_point() in l2
    assert Ray((1, 1), angle=pi / 4).arbitrary_point() == \
           Point(t + 1, t + 1)
    assert Segment((1, 1), (2, 3)).arbitrary_point() == Point(1 + t, 1 + 2 * t)
    assert l1.perpendicular_segment(l1.arbitrary_point()) == l1.arbitrary_point()
    assert Ray3D((1, 1, 1), direction_ratio=[1, 2, 3]).arbitrary_point() == \
           Point3D(t + 1, 2 * t + 1, 3 * t + 1)
    assert Segment3D(Point3D(0, 0, 0), Point3D(1, 1, 1)).midpoint == \
           Point3D(Rational(1, 2), Rational(1, 2), Rational(1, 2))
    assert Segment3D(Point3D(x1, x1, x1), Point3D(y1, y1, y1)).length == sqrt(3) * sqrt((x1 - y1) ** 2)
    assert Segment3D((1, 1, 1), (2, 3, 4)).arbitrary_point() == \
           Point3D(t + 1, 2 * t + 1, 3 * t + 1)
    raises(ValueError, (lambda: Line((x, 1), (2, 3)).arbitrary_point(x)))


def test_are_concurrent_2d():
    l1 = Line(Point(0, 0), Point(1, 1))
    l2 = Line(Point(x1, x1), Point(x1, 1 + x1))
    assert Line.are_concurrent(l1) is False
    assert Line.are_concurrent(l1, l2)
    assert Line.are_concurrent(l1, l1, l1, l2)
    assert Line.are_concurrent(l1, l2, Line(Point(5, x1), Point(-Rational(3, 5), x1)))
    assert Line.are_concurrent(l1, Line(Point(0, 0), Point(-x1, x1)), l2) is False


def test_are_concurrent_3d():
    p1 = Point3D(0, 0, 0)
    l1 = Line(p1, Point3D(1, 1, 1))
    parallel_1 = Line3D(Point3D(0, 0, 0), Point3D(1, 0, 0))
    parallel_2 = Line3D(Point3D(0, 1, 0), Point3D(1, 1, 0))
    assert Line3D.are_concurrent(l1) is False
    assert Line3D.are_concurrent(l1, Line(Point3D(x1, x1, x1), Point3D(y1, y1, y1))) is False
    assert Line3D.are_concurrent(l1, Line3D(p1, Point3D(x1, x1, x1)),
                                 Line(Point3D(x1, x1, x1), Point3D(x1, 1 + x1, 1))) is True
    assert Line3D.are_concurrent(parallel_1, parallel_2) is False


def test_arguments():
    """Functions accepting `Point` objects in `geometry`
    should also accept tuples, lists, and generators and
    automatically convert them to points."""
    from sympy import subsets

    singles2d = ((1, 2), [1, 3], Point(1, 5))
    doubles2d = subsets(singles2d, 2)
    l2d = Line(Point2D(1, 2), Point2D(2, 3))
    singles3d = ((1, 2, 3), [1, 2, 4], Point(1, 2, 6))
    doubles3d = subsets(singles3d, 2)
    l3d = Line(Point3D(1, 2, 3), Point3D(1, 1, 2))
    singles4d = ((1, 2, 3, 4), [1, 2, 3, 5], Point(1, 2, 3, 7))
    doubles4d = subsets(singles4d, 2)
    l4d = Line(Point(1, 2, 3, 4), Point(2, 2, 2, 2))
    # test 2D
    test_single = ['contains', 'distance', 'equals', 'parallel_line', 'perpendicular_line', 'perpendicular_segment',
                   'projection', 'intersection']
    for p in doubles2d:
        Line2D(*p)
    for func in test_single:
        for p in singles2d:
            getattr(l2d, func)(p)
    # test 3D
    for p in doubles3d:
        Line3D(*p)
    for func in test_single:
        for p in singles3d:
            getattr(l3d, func)(p)
    # test 4D
    for p in doubles4d:
        Line(*p)
    for func in test_single:
        for p in singles4d:
            getattr(l4d, func)(p)


def test_basic_properties_2d():
    p1 = Point(0, 0)
    p2 = Point(1, 1)
    p10 = Point(2000, 2000)
    p_r3 = Ray(p1, p2).random_point()
    p_r4 = Ray(p2, p1).random_point()

    l1 = Line(p1, p2)
    l3 = Line(Point(x1, x1), Point(x1, 1 + x1))
    l4 = Line(p1, Point(1, 0))

    r1 = Ray(p1, Point(0, 1))
    r2 = Ray(Point(0, 1), p1)

    s1 = Segment(p1, p10)
    p_s1 = s1.random_point()

    assert Line((1, 1), slope=1) == Line((1, 1), (2, 2))
    assert Line((1, 1), slope=oo) == Line((1, 1), (1, 2))
    assert Line((1, 1), slope=-oo) == Line((1, 1), (1, 2))
    assert Line(p1, p2).scale(2, 1) == Line(p1, Point(2, 1))
    assert Line(p1, p2) == Line(p1, p2)
    assert Line(p1, p2) != Line(p2, p1)
    assert l1 != Line(Point(x1, x1), Point(y1, y1))
    assert l1 != l3
    assert Line(p1, p10) != Line(p10, p1)
    assert Line(p1, p10) != p1
    assert p1 in l1  # is p1 on the line l1?
    assert p1 not in l3
    assert s1 in Line(p1, p10)
    assert Ray(Point(0, 0), Point(0, 1)) in Ray(Point(0, 0), Point(0, 2))
    assert Ray(Point(0, 0), Point(0, 2)) in Ray(Point(0, 0), Point(0, 1))
    assert (r1 in s1) is False
    assert Segment(p1, p2) in s1
    assert Ray(Point(x1, x1), Point(x1, 1 + x1)) != Ray(p1, Point(-1, 5))
    assert Segment(p1, p2).midpoint == Point(Rational(1, 2), Rational(1, 2))
    assert Segment(p1, Point(-x1, x1)).length == sqrt(2 * (x1 ** 2))

    assert l1.slope == 1
    assert l3.slope == oo
    assert l4.slope == 0
    assert Line(p1, Point(0, 1)).slope == oo
    assert Line(r1.source, r1.random_point()).slope == r1.slope
    assert Line(r2.source, r2.random_point()).slope == r2.slope
    assert Segment(Point(0, -1), Segment(p1, Point(0, 1)).random_point()).slope == Segment(p1, Point(0, 1)).slope

    assert l4.coefficients == (0, 1, 0)
    assert Line((-x, x), (-x + 1, x - 1)).coefficients == (1, 1, 0)
    assert Line(p1, Point(0, 1)).coefficients == (1, 0, 0)
    # issue 7963
    r = Ray((0, 0), angle=x)
    assert r.subs(x, 3 * pi / 4) == Ray((0, 0), (-1, 1))
    assert r.subs(x, 5 * pi / 4) == Ray((0, 0), (-1, -1))
    assert r.subs(x, -pi / 4) == Ray((0, 0), (1, -1))
    assert r.subs(x, pi / 2) == Ray((0, 0), (0, 1))
    assert r.subs(x, -pi / 2) == Ray((0, 0), (0, -1))

    for ind in range(0, 5):
        assert l3.random_point() in l3

    assert p_r3.x >= p1.x and p_r3.y >= p1.y
    assert p_r4.x <= p2.x and p_r4.y <= p2.y
    assert p1.x <= p_s1.x <= p10.x and p1.y <= p_s1.y <= p10.y
    assert hash(s1) != hash(Segment(p10, p1))

    assert s1.plot_interval() == [t, 0, 1]
    assert Line(p1, p10).plot_interval() == [t, -5, 5]
    assert Ray((0, 0), angle=pi / 4).plot_interval() == [t, 0, 10]


def test_basic_properties_3d():
    p1 = Point3D(0, 0, 0)
    p2 = Point3D(1, 1, 1)
    p3 = Point3D(x1, x1, x1)
    p5 = Point3D(x1, 1 + x1, 1)

    l1 = Line3D(p1, p2)
    l3 = Line3D(p3, p5)

    r1 = Ray3D(p1, Point3D(-1, 5, 0))
    r3 = Ray3D(p1, p2)

    s1 = Segment3D(p1, p2)

    assert Line3D((1, 1, 1), direction_ratio=[2, 3, 4]) == Line3D(Point3D(1, 1, 1), Point3D(3, 4, 5))
    assert Line3D((1, 1, 1), direction_ratio=[1, 5, 7]) == Line3D(Point3D(1, 1, 1), Point3D(2, 6, 8))
    assert Line3D((1, 1, 1), direction_ratio=[1, 2, 3]) == Line3D(Point3D(1, 1, 1), Point3D(2, 3, 4))
    assert Line3D(Line3D(p1, Point3D(0, 1, 0))) == Line3D(p1, Point3D(0, 1, 0))
    assert Ray3D(Line3D(Point3D(0, 0, 0), Point3D(1, 0, 0))) == Ray3D(p1, Point3D(1, 0, 0))
    assert Line3D(p1, p2) != Line3D(p2, p1)
    assert l1 != l3
    assert l1 != Line3D(p3, Point3D(y1, y1, y1))
    assert r3 != r1
    assert Ray3D(Point3D(0, 0, 0), Point3D(1, 1, 1)) in Ray3D(Point3D(0, 0, 0), Point3D(2, 2, 2))
    assert Ray3D(Point3D(0, 0, 0), Point3D(2, 2, 2)) in Ray3D(Point3D(0, 0, 0), Point3D(1, 1, 1))
    assert p1 in l1
    assert p1 not in l3

    assert l1.direction_ratio == [1, 1, 1]

    assert s1.midpoint == Point3D(Rational(1, 2), Rational(1, 2), Rational(1, 2))
    # Test zdirection
    assert Ray3D(p1, Point3D(0, 0, -1)).zdirection == S.NegativeInfinity


def test_contains():
    p1 = Point(0, 0)

    r = Ray(p1, Point(4, 4))
    r1 = Ray3D(p1, Point3D(0, 0, -1))
    r2 = Ray3D(p1, Point3D(0, 1, 0))
    r3 = Ray3D(p1, Point3D(0, 0, 1))

    l = Line(Point(0, 1), Point(3, 4))
    # Segment contains
    assert Point(0, (a + b) / 2) in Segment((0, a), (0, b))
    assert Point((a + b) / 2, 0) in Segment((a, 0), (b, 0))
    assert Point3D(0, 1, 0) in Segment3D((0, 1, 0), (0, 1, 0))
    assert Point3D(1, 0, 0) in Segment3D((1, 0, 0), (1, 0, 0))
    assert Segment3D(Point3D(0, 0, 0), Point3D(1, 0, 0)).contains([]) is True
    assert Segment3D(Point3D(0, 0, 0), Point3D(1, 0, 0)).contains(
        Segment3D(Point3D(2, 2, 2), Point3D(3, 2, 2))) is False
    # Line contains
    assert l.contains(Point(0, 1)) is True
    assert l.contains((0, 1)) is True
    assert l.contains((0, 0)) is False
    # Ray contains
    assert r.contains(p1) is True
    assert r.contains((1, 1)) is True
    assert r.contains((1, 3)) is False
    assert r.contains(Segment((1, 1), (2, 2))) is True
    assert r.contains(Segment((1, 2), (2, 5))) is False
    assert r.contains(Ray((2, 2), (3, 3))) is True
    assert r.contains(Ray((2, 2), (3, 5))) is False
    assert r1.contains(Segment3D(p1, Point3D(0, 0, -10))) is True
    assert r1.contains(Segment3D(Point3D(1, 1, 1), Point3D(2, 2, 2))) is False
    assert r2.contains(Point3D(0, 0, 0)) is True
    assert r3.contains(Point3D(0, 0, 0)) is True
    assert Ray3D(Point3D(1, 1, 1), Point3D(1, 0, 0)).contains([]) is False
    assert Line3D((0, 0, 0), (x, y, z)).contains((2 * x, 2 * y, 2 * z))
    with warns(UserWarning):
        assert Line3D(p1, Point3D(0, 1, 0)).contains(Point(1.0, 1.0)) is False

    with warns(UserWarning):
        assert r3.contains(Point(1.0, 1.0)) is False


def test_contains_nonreal_symbols():
    u, v, w, z = symbols('u, v, w, z')
    l = Segment(Point(u, w), Point(v, z))
    p = Point(2*u/3 + v/3, 2*w/3 + z/3)
    assert l.contains(p)


def test_distance_2d():
    p1 = Point(0, 0)
    p2 = Point(1, 1)
    half = Rational(1, 2)

    s1 = Segment(Point(0, 0), Point(1, 1))
    s2 = Segment(Point(half, half), Point(1, 0))

    r = Ray(p1, p2)

    assert s1.distance(Point(0, 0)) == 0
    assert s1.distance((0, 0)) == 0
    assert s2.distance(Point(0, 0)) == 2 ** half / 2
    assert s2.distance(Point(Rational(3) / 2, Rational(3) / 2)) == 2 ** half
    assert Line(p1, p2).distance(Point(-1, 1)) == sqrt(2)
    assert Line(p1, p2).distance(Point(1, -1)) == sqrt(2)
    assert Line(p1, p2).distance(Point(2, 2)) == 0
    assert Line(p1, p2).distance((-1, 1)) == sqrt(2)
    assert Line((0, 0), (0, 1)).distance(p1) == 0
    assert Line((0, 0), (0, 1)).distance(p2) == 1
    assert Line((0, 0), (1, 0)).distance(p1) == 0
    assert Line((0, 0), (1, 0)).distance(p2) == 1
    assert r.distance(Point(-1, -1)) == sqrt(2)
    assert r.distance(Point(1, 1)) == 0
    assert r.distance(Point(-1, 1)) == sqrt(2)
    assert Ray((1, 1), (2, 2)).distance(Point(1.5, 3)) == 3 * sqrt(2) / 4
    assert r.distance((1, 1)) == 0


def test_dimension_normalization():
    with warns(UserWarning):
        assert Ray((1, 1), (2, 1, 2)) == Ray((1, 1, 0), (2, 1, 2))


def test_distance_3d():
    p1, p2 = Point3D(0, 0, 0), Point3D(1, 1, 1)
    p3 = Point3D(Rational(3) / 2, Rational(3) / 2, Rational(3) / 2)

    s1 = Segment3D(Point3D(0, 0, 0), Point3D(1, 1, 1))
    s2 = Segment3D(Point3D(S(1) / 2, S(1) / 2, S(1) / 2), Point3D(1, 0, 1))

    r = Ray3D(p1, p2)

    assert s1.distance(p1) == 0
    assert s2.distance(p1) == sqrt(3) / 2
    assert s2.distance(p3) == 2 * sqrt(6) / 3
    assert s1.distance((0, 0, 0)) == 0
    assert s2.distance((0, 0, 0)) == sqrt(3) / 2
    assert s1.distance(p1) == 0
    assert s2.distance(p1) == sqrt(3) / 2
    assert s2.distance(p3) == 2 * sqrt(6) / 3
    assert s1.distance((0, 0, 0)) == 0
    assert s2.distance((0, 0, 0)) == sqrt(3) / 2
    # Line to point
    assert Line3D(p1, p2).distance(Point3D(-1, 1, 1)) == 2 * sqrt(6) / 3
    assert Line3D(p1, p2).distance(Point3D(1, -1, 1)) == 2 * sqrt(6) / 3
    assert Line3D(p1, p2).distance(Point3D(2, 2, 2)) == 0
    assert Line3D(p1, p2).distance((2, 2, 2)) == 0
    assert Line3D(p1, p2).distance((1, -1, 1)) == 2 * sqrt(6) / 3
    assert Line3D((0, 0, 0), (0, 1, 0)).distance(p1) == 0
    assert Line3D((0, 0, 0), (0, 1, 0)).distance(p2) == sqrt(2)
    assert Line3D((0, 0, 0), (1, 0, 0)).distance(p1) == 0
    assert Line3D((0, 0, 0), (1, 0, 0)).distance(p2) == sqrt(2)
    # Ray to point
    assert r.distance(Point3D(-1, -1, -1)) == sqrt(3)
    assert r.distance(Point3D(1, 1, 1)) == 0
    assert r.distance((-1, -1, -1)) == sqrt(3)
    assert r.distance((1, 1, 1)) == 0
    assert Ray3D((0, 0, 0), (1, 1, 2)).distance((-1, -1, 2)) == 4 * sqrt(3) / 3
    assert Ray3D((1, 1, 1), (2, 2, 2)).distance(Point3D(1.5, -3, -1)) == Rational(9) / 2
    assert Ray3D((1, 1, 1), (2, 2, 2)).distance(Point3D(1.5, 3, 1)) == sqrt(78) / 6


def test_equals():
    p1 = Point(0, 0)
    p2 = Point(1, 1)

    l1 = Line(p1, p2)
    l2 = Line((0, 5), slope=m)
    l3 = Line(Point(x1, x1), Point(x1, 1 + x1))

    assert l1.perpendicular_line(p1.args).equals(Line(Point(0, 0), Point(1, -1)))
    assert l1.perpendicular_line(p1).equals(Line(Point(0, 0), Point(1, -1)))
    assert Line(Point(x1, x1), Point(y1, y1)).parallel_line(Point(-x1, x1)). \
        equals(Line(Point(-x1, x1), Point(-y1, 2 * x1 - y1)))
    assert l3.parallel_line(p1.args).equals(Line(Point(0, 0), Point(0, -1)))
    assert l3.parallel_line(p1).equals(Line(Point(0, 0), Point(0, -1)))
    assert (l2.distance(Point(2, 3)) - 2 * abs(m + 1) / sqrt(m ** 2 + 1)).equals(0)
    assert Line3D(p1, Point3D(0, 1, 0)).equals(Point(1.0, 1.0)) is False
    assert Line3D(Point3D(0, 0, 0), Point3D(1, 0, 0)).equals(Line3D(Point3D(-5, 0, 0), Point3D(-1, 0, 0))) is True
    assert Line3D(Point3D(0, 0, 0), Point3D(1, 0, 0)).equals(Line3D(p1, Point3D(0, 1, 0))) is False
    assert Ray3D(p1, Point3D(0, 0, -1)).equals(Point(1.0, 1.0)) is False
    assert Ray3D(p1, Point3D(0, 0, -1)).equals(Ray3D(p1, Point3D(0, 0, -1))) is True
    assert Line3D((0, 0), (t, t)).perpendicular_line(Point(0, 1, 0)).equals(
        Line3D(Point3D(0, 1, 0), Point3D(S(1) / 2, S(1) / 2, 0)))
    assert Line3D((0, 0), (t, t)).perpendicular_segment(Point(0, 1, 0)).equals(Segment3D((0, 1), (S(1) / 2, S(1) / 2)))
    assert Line3D(p1, Point3D(0, 1, 0)).equals(Point(1.0, 1.0)) is False


def test_equation():
    p1 = Point(0, 0)
    p2 = Point(1, 1)
    l1 = Line(p1, p2)
    l3 = Line(Point(x1, x1), Point(x1, 1 + x1))

    assert simplify(l1.equation()) in (x - y, y - x)
    assert simplify(l3.equation()) in (x - x1, x1 - x)
    assert simplify(l1.equation()) in (x - y, y - x)
    assert simplify(l3.equation()) in (x - x1, x1 - x)

    assert Line(p1, Point(1, 0)).equation(x=x, y=y) == y
    assert Line(p1, Point(0, 1)).equation() == x
    assert Line(Point(2, 0), Point(2, 1)).equation() == x - 2
    assert Line(p2, Point(2, 1)).equation() == y - 1

    assert Line3D(Point(x1, x1, x1), Point(y1, y1, y1)
        ).equation() == (-x + y, -x + z)
    assert Line3D(Point(1, 2, 3), Point(2, 3, 4)
        ).equation() == (-x + y - 1, -x + z - 2)
    assert Line3D(Point(1, 2, 3), Point(1, 3, 4)
        ).equation() == (x - 1, -y + z - 1)
    assert Line3D(Point(1, 2, 3), Point(2, 2, 4)
        ).equation() == (y - 2, -x + z - 2)
    assert Line3D(Point(1, 2, 3), Point(2, 3, 3)
        ).equation() == (-x + y - 1, z - 3)
    assert Line3D(Point(1, 2, 3), Point(1, 2, 4)
        ).equation() == (x - 1, y - 2)
    assert Line3D(Point(1, 2, 3), Point(1, 3, 3)
        ).equation() == (x - 1, z - 3)
    assert Line3D(Point(1, 2, 3), Point(2, 2, 3)
        ).equation() == (y - 2, z - 3)


def test_intersection_2d():
    p1 = Point(0, 0)
    p2 = Point(1, 1)
    p3 = Point(x1, x1)
    p4 = Point(y1, y1)

    l1 = Line(p1, p2)
    l3 = Line(Point(0, 0), Point(3, 4))

    r1 = Ray(Point(1, 1), Point(2, 2))
    r2 = Ray(Point(0, 0), Point(3, 4))
    r4 = Ray(p1, p2)
    r6 = Ray(Point(0, 1), Point(1, 2))
    r7 = Ray(Point(0.5, 0.5), Point(1, 1))

    s1 = Segment(p1, p2)
    s2 = Segment(Point(0.25, 0.25), Point(0.5, 0.5))
    s3 = Segment(Point(0, 0), Point(3, 4))

    assert intersection(l1, p1) == [p1]
    assert intersection(l1, Point(x1, 1 + x1)) == []
    assert intersection(l1, Line(p3, p4)) in [[l1], [Line(p3, p4)]]
    assert intersection(l1, l1.parallel_line(Point(x1, 1 + x1))) == []
    assert intersection(l3, l3) == [l3]
    assert intersection(l3, r2) == [r2]
    assert intersection(l3, s3) == [s3]
    assert intersection(s3, l3) == [s3]
    assert intersection(Segment(Point(-10, 10), Point(10, 10)), Segment(Point(-5, -5), Point(-5, 5))) == []
    assert intersection(r2, l3) == [r2]
    assert intersection(r1, Ray(Point(2, 2), Point(0, 0))) == [Segment(Point(1, 1), Point(2, 2))]
    assert intersection(r1, Ray(Point(1, 1), Point(-1, -1))) == [Point(1, 1)]
    assert intersection(r1, Segment(Point(0, 0), Point(2, 2))) == [Segment(Point(1, 1), Point(2, 2))]

    assert r4.intersection(s2) == [s2]
    assert r4.intersection(Segment(Point(2, 3), Point(3, 4))) == []
    assert r4.intersection(Segment(Point(-1, -1), Point(0.5, 0.5))) == [Segment(p1, Point(0.5, 0.5))]
    assert r4.intersection(Ray(p2, p1)) == [s1]
    assert Ray(p2, p1).intersection(r6) == []
    assert r4.intersection(r7) == r7.intersection(r4) == [r7]
    assert Ray3D((0, 0), (3, 0)).intersection(Ray3D((1, 0), (3, 0))) == [Ray3D((1, 0), (3, 0))]
    assert Ray3D((1, 0), (3, 0)).intersection(Ray3D((0, 0), (3, 0))) == [Ray3D((1, 0), (3, 0))]
    assert Ray(Point(0, 0), Point(0, 4)).intersection(Ray(Point(0, 1), Point(0, -1))) == \
           [Segment(Point(0, 0), Point(0, 1))]

    assert Segment3D((0, 0), (3, 0)).intersection(
        Segment3D((1, 0), (2, 0))) == [Segment3D((1, 0), (2, 0))]
    assert Segment3D((1, 0), (2, 0)).intersection(
        Segment3D((0, 0), (3, 0))) == [Segment3D((1, 0), (2, 0))]
    assert Segment3D((0, 0), (3, 0)).intersection(
        Segment3D((3, 0), (4, 0))) == [Point3D((3, 0))]
    assert Segment3D((0, 0), (3, 0)).intersection(
        Segment3D((2, 0), (5, 0))) == [Segment3D((2, 0), (3, 0))]
    assert Segment3D((0, 0), (3, 0)).intersection(
        Segment3D((-2, 0), (1, 0))) == [Segment3D((0, 0), (1, 0))]
    assert Segment3D((0, 0), (3, 0)).intersection(
        Segment3D((-2, 0), (0, 0))) == [Point3D(0, 0)]
    assert s1.intersection(Segment(Point(1, 1), Point(2, 2))) == [Point(1, 1)]
    assert s1.intersection(Segment(Point(0.5, 0.5), Point(1.5, 1.5))) == [Segment(Point(0.5, 0.5), p2)]
    assert s1.intersection(Segment(Point(4, 4), Point(5, 5))) == []
    assert s1.intersection(Segment(Point(-1, -1), p1)) == [p1]
    assert s1.intersection(Segment(Point(-1, -1), Point(0.5, 0.5))) == [Segment(p1, Point(0.5, 0.5))]
    assert s1.intersection(Line(Point(1, 0), Point(2, 1))) == []
    assert s1.intersection(s2) == [s2]
    assert s2.intersection(s1) == [s2]


def test_intersection_3d():
    p1 = Point3D(0, 0, 0)
    p2 = Point3D(1, 1, 1)

    l1 = Line3D(p1, p2)
    l2 = Line3D(Point3D(0, 0, 0), Point3D(3, 4, 0))

    r1 = Ray3D(Point3D(1, 1, 1), Point3D(2, 2, 2))
    r2 = Ray3D(Point3D(0, 0, 0), Point3D(3, 4, 0))

    s1 = Segment3D(Point3D(0, 0, 0), Point3D(3, 4, 0))

    assert intersection(l1, p1) == [p1]
    assert intersection(l1, Point3D(x1, 1 + x1, 1)) == []
    assert intersection(l1, l1.parallel_line(p1)) == [Line3D(Point3D(0, 0, 0), Point3D(1, 1, 1))]
    assert intersection(l2, r2) == [r2]
    assert intersection(l2, s1) == [s1]
    assert intersection(r2, l2) == [r2]
    assert intersection(r1, Ray3D(Point3D(1, 1, 1), Point3D(-1, -1, -1))) == [Point3D(1, 1, 1)]
    assert intersection(r1, Segment3D(Point3D(0, 0, 0), Point3D(2, 2, 2))) == [
        Segment3D(Point3D(1, 1, 1), Point3D(2, 2, 2))]
    assert intersection(Ray3D(Point3D(1, 0, 0), Point3D(-1, 0, 0)), Ray3D(Point3D(0, 1, 0), Point3D(0, -1, 0))) \
           == [Point3D(0, 0, 0)]
    assert intersection(r1, Ray3D(Point3D(2, 2, 2), Point3D(0, 0, 0))) == \
           [Segment3D(Point3D(1, 1, 1), Point3D(2, 2, 2))]
    assert intersection(s1, r2) == [s1]

    assert Line3D(Point3D(4, 0, 1), Point3D(0, 4, 1)).intersection(Line3D(Point3D(0, 0, 1), Point3D(4, 4, 1))) == \
           [Point3D(2, 2, 1)]
    assert Line3D((0, 1, 2), (0, 2, 3)).intersection(Line3D((0, 1, 2), (0, 1, 1))) == [Point3D(0, 1, 2)]
    assert Line3D((0, 0), (t, t)).intersection(Line3D((0, 1), (t, t))) == \
           [Point3D(t, t)]

    assert Ray3D(Point3D(0, 0, 0), Point3D(0, 4, 0)).intersection(Ray3D(Point3D(0, 1, 1), Point3D(0, -1, 1))) == []


def test_is_parallel():
    p1 = Point3D(0, 0, 0)
    p2 = Point3D(1, 1, 1)
    p3 = Point3D(x1, x1, x1)

    l2 = Line(Point(x1, x1), Point(y1, y1))
    l2_1 = Line(Point(x1, x1), Point(x1, 1 + x1))

    assert Line.is_parallel(Line(Point(0, 0), Point(1, 1)), l2)
    assert Line.is_parallel(l2, Line(Point(x1, x1), Point(x1, 1 + x1))) is False
    assert Line.is_parallel(l2, l2.parallel_line(Point(-x1, x1)))
    assert Line.is_parallel(l2_1, l2_1.parallel_line(Point(0, 0)))
    assert Line3D(p1, p2).is_parallel(Line3D(p1, p2))  # same as in 2D
    assert Line3D(Point3D(4, 0, 1), Point3D(0, 4, 1)).is_parallel(Line3D(Point3D(0, 0, 1), Point3D(4, 4, 1))) is False
    assert Line3D(p1, p2).parallel_line(p3) == Line3D(Point3D(x1, x1, x1),
                                                      Point3D(x1 + 1, x1 + 1, x1 + 1))
    assert Line3D(p1, p2).parallel_line(p3.args) == \
           Line3D(Point3D(x1, x1, x1), Point3D(x1 + 1, x1 + 1, x1 + 1))
    assert Line3D(Point3D(4, 0, 1), Point3D(0, 4, 1)).is_parallel(Line3D(Point3D(0, 0, 1), Point3D(4, 4, 1))) is False


def test_is_perpendicular():
    p1 = Point(0, 0)
    p2 = Point(1, 1)

    l1 = Line(p1, p2)
    l2 = Line(Point(x1, x1), Point(y1, y1))
    l1_1 = Line(p1, Point(-x1, x1))
    # 2D
    assert Line.is_perpendicular(l1, l1_1)
    assert Line.is_perpendicular(l1, l2) is False
    p = l1.random_point()
    assert l1.perpendicular_segment(p) == p
    # 3D
    assert Line3D.is_perpendicular(Line3D(Point3D(0, 0, 0), Point3D(1, 0, 0)),
                                   Line3D(Point3D(0, 0, 0), Point3D(0, 1, 0))) is True
    assert Line3D.is_perpendicular(Line3D(Point3D(0, 0, 0), Point3D(1, 0, 0)),
                                   Line3D(Point3D(0, 1, 0), Point3D(1, 1, 0))) is False
    assert Line3D.is_perpendicular(Line3D(Point3D(0, 0, 0), Point3D(1, 1, 1)),
                                   Line3D(Point3D(x1, x1, x1), Point3D(y1, y1, y1))) is False


def test_is_similar():
    p1 = Point(2000, 2000)
    p2 = p1.scale(2, 2)

    r1 = Ray3D(Point3D(1, 1, 1), Point3D(1, 0, 0))
    r2 = Ray(Point(0, 0), Point(0, 1))

    s1 = Segment(Point(0, 0), p1)

    assert s1.is_similar(Segment(p1, p2))
    assert s1.is_similar(r2) is False
    assert r1.is_similar(Line3D(Point3D(1, 1, 1), Point3D(1, 0, 0))) is True
    assert r1.is_similar(Line3D(Point3D(0, 0, 0), Point3D(0, 1, 0))) is False


@slow
def test_line_intersection():
    assert asa(120, 8, 52) == \
           Triangle(
               Point(0, 0),
               Point(8, 0),
               Point(-4 * cos(19 * pi / 90) / sin(2 * pi / 45),
                     4 * sqrt(3) * cos(19 * pi / 90) / sin(2 * pi / 45)))
    assert Line((0, 0), (1, 1)).intersection(Ray((1, 0), (1, 2))) == [Point(1, 1)]
    assert Line((0, 0), (1, 1)).intersection(Segment((1, 0), (1, 2))) == [Point(1, 1)]
    assert Ray((0, 0), (1, 1)).intersection(Ray((1, 0), (1, 2))) == [Point(1, 1)]
    assert Ray((0, 0), (1, 1)).intersection(Segment((1, 0), (1, 2))) == [Point(1, 1)]
    assert Ray((0, 0), (10, 10)).contains(Segment((1, 1), (2, 2))) is True
    assert Segment((1, 1), (2, 2)) in Line((0, 0), (10, 10))
    x = 8 * tan(13 * pi / 45) / (tan(13 * pi / 45) + sqrt(3))
    y = (-8 * sqrt(3) * tan(13 * pi / 45) ** 2 + 24 * tan(13 * pi / 45)) / (-3 + tan(13 * pi / 45) ** 2)
    assert Line(Point(0, 0), Point(1, -sqrt(3))).contains(Point(x, y)) is True


def test_length():
    s2 = Segment3D(Point3D(x1, x1, x1), Point3D(y1, y1, y1))
    assert Line(Point(0, 0), Point(1, 1)).length == oo
    assert s2.length == sqrt(3) * sqrt((x1 - y1) ** 2)
    assert Line3D(Point3D(0, 0, 0), Point3D(1, 1, 1)).length == oo


def test_projection():
    p1 = Point(0, 0)
    p2 = Point3D(0, 0, 0)
    p3 = Point(-x1, x1)

    l1 = Line(p1, Point(1, 1))
    l2 = Line3D(Point3D(0, 0, 0), Point3D(1, 0, 0))
    l3 = Line3D(p2, Point3D(1, 1, 1))

    r1 = Ray(Point(1, 1), Point(2, 2))

    assert Line(Point(x1, x1), Point(y1, y1)).projection(Point(y1, y1)) == Point(y1, y1)
    assert Line(Point(x1, x1), Point(x1, 1 + x1)).projection(Point(1, 1)) == Point(x1, 1)
    assert Segment(Point(-2, 2), Point(0, 4)).projection(r1) == Segment(Point(-1, 3), Point(0, 4))
    assert Segment(Point(0, 4), Point(-2, 2)).projection(r1) == Segment(Point(0, 4), Point(-1, 3))
    assert l1.projection(p3) == p1
    assert l1.projection(Ray(p1, Point(-1, 5))) == Ray(Point(0, 0), Point(2, 2))
    assert l1.projection(Ray(p1, Point(-1, 1))) == p1
    assert r1.projection(Ray(Point(1, 1), Point(-1, -1))) == Point(1, 1)
    assert r1.projection(Ray(Point(0, 4), Point(-1, -5))) == Segment(Point(1, 1), Point(2, 2))
    assert r1.projection(Segment(Point(-1, 5), Point(-5, -10))) == Segment(Point(1, 1), Point(2, 2))
    assert r1.projection(Ray(Point(1, 1), Point(-1, -1))) == Point(1, 1)
    assert r1.projection(Ray(Point(0, 4), Point(-1, -5))) == Segment(Point(1, 1), Point(2, 2))
    assert r1.projection(Segment(Point(-1, 5), Point(-5, -10))) == Segment(Point(1, 1), Point(2, 2))

    assert l3.projection(Ray3D(p2, Point3D(-1, 5, 0))) == Ray3D(Point3D(0, 0, 0), Point3D(S(4)/3, S(4)/3, S(4)/3))
    assert l3.projection(Ray3D(p2, Point3D(-1, 1, 1))) == Ray3D(Point3D(0, 0, 0), Point3D(S(1)/3, S(1)/3, S(1)/3))
    assert l2.projection(Point3D(5, 5, 0)) == Point3D(5, 0)
    assert l2.projection(Line3D(Point3D(0, 1, 0), Point3D(1, 1, 0))).equals(l2)


def test_perpendicular_bisector():
    s1 = Segment(Point(0, 0), Point(1, 1))
    aline = Line(Point(S(1)/2, S(1)/2), Point(S(3)/2, -S(1)/2))
    on_line = Segment(Point(S(1)/2, S(1)/2), Point(S(3)/2, -S(1)/2)).midpoint

    assert s1.perpendicular_bisector().equals(aline)
    assert s1.perpendicular_bisector(on_line).equals(Segment(s1.midpoint, on_line))
    assert s1.perpendicular_bisector(on_line + (1, 0)).equals(aline)


def test_raises():
    d, e = symbols('a,b', real=True)
    s = Segment((d, 0), (e, 0))

    raises(TypeError, lambda: Line((1, 1), 1))
    raises(ValueError, lambda: Line(Point(0, 0), Point(0, 0)))
    raises(Undecidable, lambda: Point(2 * d, 0) in s)
    raises(ValueError, lambda: Ray3D(Point(1.0, 1.0)))
    raises(ValueError, lambda: Line3D(Point3D(0, 0, 0), Point3D(0, 0, 0)))
    raises(TypeError, lambda: Line3D((1, 1), 1))
    raises(ValueError, lambda: Line3D(Point3D(0, 0, 0)))
    raises(TypeError, lambda: Ray((1, 1), 1))
    raises(GeometryError, lambda: Line(Point(0, 0), Point(1, 0))
           .projection(Circle(Point(0, 0), 1)))


def test_ray_generation():
    assert Ray((1, 1), angle=pi / 4) == Ray((1, 1), (2, 2))
    assert Ray((1, 1), angle=pi / 2) == Ray((1, 1), (1, 2))
    assert Ray((1, 1), angle=-pi / 2) == Ray((1, 1), (1, 0))
    assert Ray((1, 1), angle=-3 * pi / 2) == Ray((1, 1), (1, 2))
    assert Ray((1, 1), angle=5 * pi / 2) == Ray((1, 1), (1, 2))
    assert Ray((1, 1), angle=5.0 * pi / 2) == Ray((1, 1), (1, 2))
    assert Ray((1, 1), angle=pi) == Ray((1, 1), (0, 1))
    assert Ray((1, 1), angle=3.0 * pi) == Ray((1, 1), (0, 1))
    assert Ray((1, 1), angle=4.0 * pi) == Ray((1, 1), (2, 1))
    assert Ray((1, 1), angle=0) == Ray((1, 1), (2, 1))
    assert Ray((1, 1), angle=4.05 * pi) == Ray(Point(1, 1),
                                               Point(2, -sqrt(5) * sqrt(2 * sqrt(5) + 10) / 4 - sqrt(
                                                   2 * sqrt(5) + 10) / 4 + 2 + sqrt(5)))
    assert Ray((1, 1), angle=4.02 * pi) == Ray(Point(1, 1),
                                               Point(2, 1 + tan(4.02 * pi)))
    assert Ray((1, 1), angle=5) == Ray((1, 1), (2, 1 + tan(5)))

    assert Ray3D((1, 1, 1), direction_ratio=[4, 4, 4]) == Ray3D(Point3D(1, 1, 1), Point3D(5, 5, 5))
    assert Ray3D((1, 1, 1), direction_ratio=[1, 2, 3]) == Ray3D(Point3D(1, 1, 1), Point3D(2, 3, 4))
    assert Ray3D((1, 1, 1), direction_ratio=[1, 1, 1]) == Ray3D(Point3D(1, 1, 1), Point3D(2, 2, 2))


def test_symbolic_intersect():
    # Issue 7814.
    circle = Circle(Point(x, 0), y)
    line = Line(Point(k, z), slope=0)
    assert line.intersection(circle) == [Point(x + sqrt((y - z) * (y + z)), z), Point(x - sqrt((y - z) * (y + z)), z)]


def test_issue_2941():
    def _check():
        for f, g in cartes(*[(Line, Ray, Segment)] * 2):
            l1 = f(a, b)
            l2 = g(c, d)
            assert l1.intersection(l2) == l2.intersection(l1)
    # intersect at end point
    c, d = (-2, -2), (-2, 0)
    a, b = (0, 0), (1, 1)
    _check()
    # midline intersection
    c, d = (-2, -3), (-2, 0)
    _check()


def test_parameter_value():
    t = Symbol('t')
    p1, p2 = Point(0, 1), Point(5, 6)
    l = Line(p1, p2)
    assert l.parameter_value((5, 6), t) == {t: 1}
    raises(ValueError, lambda: l.parameter_value((0, 0), t))
