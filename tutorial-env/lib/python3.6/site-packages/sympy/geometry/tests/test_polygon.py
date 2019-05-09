from sympy import Abs, Rational, Float, S, Symbol, symbols, cos, pi, sqrt, oo
from sympy.functions.elementary.trigonometric import tan
from sympy.geometry import (Circle, Ellipse, GeometryError, Point, Point2D, \
                            Polygon, Ray, RegularPolygon, Segment, Triangle, \
                            are_similar,convex_hull, intersection, Line)
from sympy.utilities.pytest import raises, slow, warns
from sympy.utilities.randtest import verify_numerically
from sympy.geometry.polygon import rad, deg
from sympy import integrate


def feq(a, b):
    """Test if two floating point values are 'equal'."""
    t_float = Float("1.0E-10")
    return -t_float < a - b < t_float

@slow
def test_polygon():
    x = Symbol('x', real=True)
    y = Symbol('y', real=True)
    q = Symbol('q', real=True)
    u = Symbol('u', real=True)
    v = Symbol('v', real=True)
    w = Symbol('w', real=True)
    x1 = Symbol('x1', real=True)
    half = Rational(1, 2)
    a, b, c = Point(0, 0), Point(2, 0), Point(3, 3)
    t = Triangle(a, b, c)
    assert Polygon(a, Point(1, 0), b, c) == t
    assert Polygon(Point(1, 0), b, c, a) == t
    assert Polygon(b, c, a, Point(1, 0)) == t
    # 2 "remove folded" tests
    assert Polygon(a, Point(3, 0), b, c) == t
    assert Polygon(a, b, Point(3, -1), b, c) == t
    # remove multiple collinear points
    assert Polygon(Point(-4, 15), Point(-11, 15), Point(-15, 15),
        Point(-15, 33/5), Point(-15, -87/10), Point(-15, -15),
        Point(-42/5, -15), Point(-2, -15), Point(7, -15), Point(15, -15),
        Point(15, -3), Point(15, 10), Point(15, 15)) == \
        Polygon(Point(-15,-15), Point(15,-15), Point(15,15), Point(-15,15))

    p1 = Polygon(
        Point(0, 0), Point(3, -1),
        Point(6, 0), Point(4, 5),
        Point(2, 3), Point(0, 3))
    p2 = Polygon(
        Point(6, 0), Point(3, -1),
        Point(0, 0), Point(0, 3),
        Point(2, 3), Point(4, 5))
    p3 = Polygon(
        Point(0, 0), Point(3, 0),
        Point(5, 2), Point(4, 4))
    p4 = Polygon(
        Point(0, 0), Point(4, 4),
        Point(5, 2), Point(3, 0))
    p5 = Polygon(
        Point(0, 0), Point(4, 4),
        Point(0, 4))
    p6 = Polygon(
        Point(-11, 1), Point(-9, 6.6),
        Point(-4, -3), Point(-8.4, -8.7))
    p7 = Polygon(
        Point(x, y), Point(q, u),
        Point(v, w))
    p8 = Polygon(
        Point(x, y), Point(v, w),
        Point(q, u))
    p9 = Polygon(
        Point(0, 0), Point(4, 4),
        Point(3, 0), Point(5, 2))
    p10 = Polygon(
        Point(0, 2), Point(2, 2),
        Point(0, 0), Point(2, 0))
    p11 = Polygon(Point(0, 0), 1, n=3)

    r = Ray(Point(-9,6.6), Point(-9,5.5))
    #
    # General polygon
    #
    assert p1 == p2
    assert len(p1.args) == 6
    assert len(p1.sides) == 6
    assert p1.perimeter == 5 + 2*sqrt(10) + sqrt(29) + sqrt(8)
    assert p1.area == 22
    assert not p1.is_convex()
    assert Polygon((-1, 1), (2, -1), (2, 1), (-1, -1), (3, 0)
        ).is_convex() is False
    # ensure convex for both CW and CCW point specification
    assert p3.is_convex()
    assert p4.is_convex()
    dict5 = p5.angles
    assert dict5[Point(0, 0)] == pi / 4
    assert dict5[Point(0, 4)] == pi / 2
    assert p5.encloses_point(Point(x, y)) is None
    assert p5.encloses_point(Point(1, 3))
    assert p5.encloses_point(Point(0, 0)) is False
    assert p5.encloses_point(Point(4, 0)) is False
    assert p1.encloses(Circle(Point(2.5,2.5),5)) is False
    assert p1.encloses(Ellipse(Point(2.5,2),5,6)) is False
    p5.plot_interval('x') == [x, 0, 1]
    assert p5.distance(
        Polygon(Point(10, 10), Point(14, 14), Point(10, 14))) == 6 * sqrt(2)
    assert p5.distance(
        Polygon(Point(1, 8), Point(5, 8), Point(8, 12), Point(1, 12))) == 4
    with warns(UserWarning, \
               match="Polygons may intersect producing erroneous output"):
        Polygon(Point(0, 0), Point(1, 0), Point(1, 1)).distance(
                Polygon(Point(0, 0), Point(0, 1), Point(1, 1)))
    assert hash(p5) == hash(Polygon(Point(0, 0), Point(4, 4), Point(0, 4)))
    assert hash(p1) == hash(p2)
    assert hash(p7) == hash(p8)
    assert hash(p3) != hash(p9)
    assert p5 == Polygon(Point(4, 4), Point(0, 4), Point(0, 0))
    assert Polygon(Point(4, 4), Point(0, 4), Point(0, 0)) in p5
    assert p5 != Point(0, 4)
    assert Point(0, 1) in p5
    assert p5.arbitrary_point('t').subs(Symbol('t', real=True), 0) == \
        Point(0, 0)
    raises(ValueError, lambda: Polygon(
        Point(x, 0), Point(0, y), Point(x, y)).arbitrary_point('x'))
    assert p6.intersection(r) == [Point(-9, -S(84)/13), Point(-9, S(33)/5)]
    assert p10.area == 0
    assert p11 == RegularPolygon(Point(0, 0), 1, 3, 0)
    assert p11.vertices[0] == Point(1, 0)
    assert p11.args[0] == Point(0, 0)
    p11.spin(pi/2)
    assert p11.vertices[0] == Point(0, 1)
    #
    # Regular polygon
    #
    p1 = RegularPolygon(Point(0, 0), 10, 5)
    p2 = RegularPolygon(Point(0, 0), 5, 5)
    raises(GeometryError, lambda: RegularPolygon(Point(0, 0), Point(0,
           1), Point(1, 1)))
    raises(GeometryError, lambda: RegularPolygon(Point(0, 0), 1, 2))
    raises(ValueError, lambda: RegularPolygon(Point(0, 0), 1, 2.5))

    assert p1 != p2
    assert p1.interior_angle == 3*pi/5
    assert p1.exterior_angle == 2*pi/5
    assert p2.apothem == 5*cos(pi/5)
    assert p2.circumcenter == p1.circumcenter == Point(0, 0)
    assert p1.circumradius == p1.radius == 10
    assert p2.circumcircle == Circle(Point(0, 0), 5)
    assert p2.incircle == Circle(Point(0, 0), p2.apothem)
    assert p2.inradius == p2.apothem == (5 * (1 + sqrt(5)) / 4)
    p2.spin(pi / 10)
    dict1 = p2.angles
    assert dict1[Point(0, 5)] == 3 * pi / 5
    assert p1.is_convex()
    assert p1.rotation == 0
    assert p1.encloses_point(Point(0, 0))
    assert p1.encloses_point(Point(11, 0)) is False
    assert p2.encloses_point(Point(0, 4.9))
    p1.spin(pi/3)
    assert p1.rotation == pi/3
    assert p1.vertices[0] == Point(5, 5*sqrt(3))
    for var in p1.args:
        if isinstance(var, Point):
            assert var == Point(0, 0)
        else:
            assert var == 5 or var == 10 or var == pi / 3
    assert p1 != Point(0, 0)
    assert p1 != p5

    # while spin works in place (notice that rotation is 2pi/3 below)
    # rotate returns a new object
    p1_old = p1
    assert p1.rotate(pi/3) == RegularPolygon(Point(0, 0), 10, 5, 2*pi/3)
    assert p1 == p1_old

    assert p1.area == (-250*sqrt(5) + 1250)/(4*tan(pi/5))
    assert p1.length == 20*sqrt(-sqrt(5)/8 + S(5)/8)
    assert p1.scale(2, 2) == \
        RegularPolygon(p1.center, p1.radius*2, p1._n, p1.rotation)
    assert RegularPolygon((0, 0), 1, 4).scale(2, 3) == \
        Polygon(Point(2, 0), Point(0, 3), Point(-2, 0), Point(0, -3))

    assert repr(p1) == str(p1)

    #
    # Angles
    #
    angles = p4.angles
    assert feq(angles[Point(0, 0)].evalf(), Float("0.7853981633974483"))
    assert feq(angles[Point(4, 4)].evalf(), Float("1.2490457723982544"))
    assert feq(angles[Point(5, 2)].evalf(), Float("1.8925468811915388"))
    assert feq(angles[Point(3, 0)].evalf(), Float("2.3561944901923449"))

    angles = p3.angles
    assert feq(angles[Point(0, 0)].evalf(), Float("0.7853981633974483"))
    assert feq(angles[Point(4, 4)].evalf(), Float("1.2490457723982544"))
    assert feq(angles[Point(5, 2)].evalf(), Float("1.8925468811915388"))
    assert feq(angles[Point(3, 0)].evalf(), Float("2.3561944901923449"))

    #
    # Triangle
    #
    p1 = Point(0, 0)
    p2 = Point(5, 0)
    p3 = Point(0, 5)
    t1 = Triangle(p1, p2, p3)
    t2 = Triangle(p1, p2, Point(Rational(5, 2), sqrt(Rational(75, 4))))
    t3 = Triangle(p1, Point(x1, 0), Point(0, x1))
    s1 = t1.sides
    assert Triangle(p1, p2, p1) == Polygon(p1, p2, p1) == Segment(p1, p2)
    raises(GeometryError, lambda: Triangle(Point(0, 0)))

    # Basic stuff
    assert Triangle(p1, p1, p1) == p1
    assert Triangle(p2, p2*2, p2*3) == Segment(p2, p2*3)
    assert t1.area == Rational(25, 2)
    assert t1.is_right()
    assert t2.is_right() is False
    assert t3.is_right()
    assert p1 in t1
    assert t1.sides[0] in t1
    assert Segment((0, 0), (1, 0)) in t1
    assert Point(5, 5) not in t2
    assert t1.is_convex()
    assert feq(t1.angles[p1].evalf(), pi.evalf()/2)

    assert t1.is_equilateral() is False
    assert t2.is_equilateral()
    assert t3.is_equilateral() is False
    assert are_similar(t1, t2) is False
    assert are_similar(t1, t3)
    assert are_similar(t2, t3) is False
    assert t1.is_similar(Point(0, 0)) is False
    assert t1.is_similar(t2) is False

    # Bisectors
    bisectors = t1.bisectors()
    assert bisectors[p1] == Segment(p1, Point(Rational(5, 2), Rational(5, 2)))
    ic = (250 - 125*sqrt(2)) / 50
    assert t1.incenter == Point(ic, ic)

    # Inradius
    assert t1.inradius == t1.incircle.radius == 5 - 5*sqrt(2)/2
    assert t2.inradius == t2.incircle.radius == 5*sqrt(3)/6
    assert t3.inradius == t3.incircle.radius == x1**2/((2 + sqrt(2))*Abs(x1))

    # Exradius
    assert t1.exradii[t1.sides[2]] == 5*sqrt(2)/2

    # Circumcircle
    assert t1.circumcircle.center == Point(2.5, 2.5)

    # Medians + Centroid
    m = t1.medians
    assert t1.centroid == Point(Rational(5, 3), Rational(5, 3))
    assert m[p1] == Segment(p1, Point(Rational(5, 2), Rational(5, 2)))
    assert t3.medians[p1] == Segment(p1, Point(x1/2, x1/2))
    assert intersection(m[p1], m[p2], m[p3]) == [t1.centroid]
    assert t1.medial == Triangle(Point(2.5, 0), Point(0, 2.5), Point(2.5, 2.5))

    # Nine-point circle
    assert t1.nine_point_circle == Circle(Point(2.5, 0),
                                          Point(0, 2.5), Point(2.5, 2.5))
    assert t1.nine_point_circle == Circle(Point(0, 0),
                                          Point(0, 2.5), Point(2.5, 2.5))

    # Perpendicular
    altitudes = t1.altitudes
    assert altitudes[p1] == Segment(p1, Point(Rational(5, 2), Rational(5, 2)))
    assert altitudes[p2].equals(s1[0])
    assert altitudes[p3] == s1[2]
    assert t1.orthocenter == p1
    t = S('''Triangle(
    Point(100080156402737/5000000000000, 79782624633431/500000000000),
    Point(39223884078253/2000000000000, 156345163124289/1000000000000),
    Point(31241359188437/1250000000000, 338338270939941/1000000000000000))''')
    assert t.orthocenter == S('''Point(-780660869050599840216997'''
    '''79471538701955848721853/80368430960602242240789074233100000000000000,'''
    '''20151573611150265741278060334545897615974257/16073686192120448448157'''
    '''8148466200000000000)''')

    # Ensure
    assert len(intersection(*bisectors.values())) == 1
    assert len(intersection(*altitudes.values())) == 1
    assert len(intersection(*m.values())) == 1

    # Distance
    p1 = Polygon(
        Point(0, 0), Point(1, 0),
        Point(1, 1), Point(0, 1))
    p2 = Polygon(
        Point(0, Rational(5)/4), Point(1, Rational(5)/4),
        Point(1, Rational(9)/4), Point(0, Rational(9)/4))
    p3 = Polygon(
        Point(1, 2), Point(2, 2),
        Point(2, 1))
    p4 = Polygon(
        Point(1, 1), Point(Rational(6)/5, 1),
        Point(1, Rational(6)/5))
    pt1 = Point(half, half)
    pt2 = Point(1, 1)

    '''Polygon to Point'''
    assert p1.distance(pt1) == half
    assert p1.distance(pt2) == 0
    assert p2.distance(pt1) == Rational(3)/4
    assert p3.distance(pt2) == sqrt(2)/2

    '''Polygon to Polygon'''
    # p1.distance(p2) emits a warning
    with warns(UserWarning, \
               match="Polygons may intersect producing erroneous output"):
        assert p1.distance(p2) == half/2

    assert p1.distance(p3) == sqrt(2)/2

    # p3.distance(p4) emits a warning
    with warns(UserWarning, \
               match="Polygons may intersect producing erroneous output"):
        assert p3.distance(p4) == (sqrt(2)/2 - sqrt(Rational(2)/25)/2)


def test_convex_hull():
    p = [Point(-5, -1), Point(-2, 1), Point(-2, -1), Point(-1, -3), \
         Point(0, 0), Point(1, 1), Point(2, 2), Point(2, -1), Point(3, 1), \
         Point(4, -1), Point(6, 2)]
    ch = Polygon(p[0], p[3], p[9], p[10], p[6], p[1])
    #test handling of duplicate points
    p.append(p[3])

    #more than 3 collinear points
    another_p = [Point(-45, -85), Point(-45, 85), Point(-45, 26), \
                 Point(-45, -24)]
    ch2 = Segment(another_p[0], another_p[1])

    assert convex_hull(*another_p) == ch2
    assert convex_hull(*p) == ch
    assert convex_hull(p[0]) == p[0]
    assert convex_hull(p[0], p[1]) == Segment(p[0], p[1])

    # no unique points
    assert convex_hull(*[p[-1]]*3) == p[-1]

    # collection of items
    assert convex_hull(*[Point(0, 0), \
                        Segment(Point(1, 0), Point(1, 1)), \
                        RegularPolygon(Point(2, 0), 2, 4)]) == \
        Polygon(Point(0, 0), Point(2, -2), Point(4, 0), Point(2, 2))


def test_encloses():
    # square with a dimpled left side
    s = Polygon(Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 1), \
        Point(S.Half, S.Half))
    # the following is True if the polygon isn't treated as closing on itself
    assert s.encloses(Point(0, S.Half)) is False
    assert s.encloses(Point(S.Half, S.Half)) is False  # it's a vertex
    assert s.encloses(Point(Rational(3, 4), S.Half)) is True


def test_triangle_kwargs():
    assert Triangle(sss=(3, 4, 5)) == \
        Triangle(Point(0, 0), Point(3, 0), Point(3, 4))
    assert Triangle(asa=(30, 2, 30)) == \
        Triangle(Point(0, 0), Point(2, 0), Point(1, sqrt(3)/3))
    assert Triangle(sas=(1, 45, 2)) == \
        Triangle(Point(0, 0), Point(2, 0), Point(sqrt(2)/2, sqrt(2)/2))
    assert Triangle(sss=(1, 2, 5)) is None
    assert deg(rad(180)) == 180


def test_transform():
    pts = [Point(0, 0), Point(S(1)/2, S(1)/4), Point(1, 1)]
    pts_out = [Point(-4, -10), Point(-3, -S(37)/4), Point(-2, -7)]
    assert Triangle(*pts).scale(2, 3, (4, 5)) == Triangle(*pts_out)
    assert RegularPolygon((0, 0), 1, 4).scale(2, 3, (4, 5)) == \
        Polygon(Point(-2, -10), Point(-4, -7), Point(-6, -10), Point(-4, -13))


def test_reflect():
    x = Symbol('x', real=True)
    y = Symbol('y', real=True)
    b = Symbol('b')
    m = Symbol('m')
    l = Line((0, b), slope=m)
    p = Point(x, y)
    r = p.reflect(l)
    dp = l.perpendicular_segment(p).length
    dr = l.perpendicular_segment(r).length

    assert verify_numerically(dp, dr)
    t = Triangle((0, 0), (1, 0), (2, 3))
    assert Polygon((1, 0), (2, 0), (2, 2)).reflect(Line((3, 0), slope=oo)) \
        == Triangle(Point(5, 0), Point(4, 0), Point(4, 2))
    assert Polygon((1, 0), (2, 0), (2, 2)).reflect(Line((0, 3), slope=oo)) \
        == Triangle(Point(-1, 0), Point(-2, 0), Point(-2, 2))
    assert Polygon((1, 0), (2, 0), (2, 2)).reflect(Line((0, 3), slope=0)) \
        == Triangle(Point(1, 6), Point(2, 6), Point(2, 4))
    assert Polygon((1, 0), (2, 0), (2, 2)).reflect(Line((3, 0), slope=0)) \
        == Triangle(Point(1, 0), Point(2, 0), Point(2, -2))

def test_bisectors():
    p1, p2, p3 = Point(0, 0), Point(1, 0), Point(0, 1)
    t = Triangle(p1, p2, p3)
    assert t.bisectors()[p2] == Segment(Point(1, 0), Point(0, sqrt(2) - 1))

def test_incenter():
    assert Triangle(Point(0, 0), Point(1, 0), Point(0, 1)).incenter \
        == Point(1 - sqrt(2)/2, 1 - sqrt(2)/2)

def test_inradius():
    assert Triangle(Point(0, 0), Point(4, 0), Point(0, 3)).inradius == 1

def test_incircle():
    assert Triangle(Point(0, 0), Point(2, 0), Point(0, 2)).incircle \
        == Circle(Point(2 - sqrt(2), 2 - sqrt(2)), 2 - sqrt(2))

def test_exradii():
    t = Triangle(Point(0, 0), Point(6, 0), Point(0, 2))
    assert t.exradii[t.sides[2]] == (-2 + sqrt(10))

def test_medians():
    t = Triangle(Point(0, 0), Point(1, 0), Point(0, 1))
    assert t.medians[Point(0, 0)] == Segment(Point(0, 0), Point(S(1)/2, S(1)/2))

def test_medial():
    assert Triangle(Point(0, 0), Point(1, 0), Point(0, 1)).medial \
        == Triangle(Point(S(1)/2, 0), Point(S(1)/2, S(1)/2), Point(0, S(1)/2))

def test_nine_point_circle():
    assert Triangle(Point(0, 0), Point(1, 0), Point(0, 1)).nine_point_circle \
        == Circle(Point2D(S(1)/4, S(1)/4), sqrt(2)/4)

def test_eulerline():
    assert Triangle(Point(0, 0), Point(1, 0), Point(0, 1)).eulerline \
        == Line(Point2D(0, 0), Point2D(S(1)/2, S(1)/2))
    assert Triangle(Point(0, 0), Point(10, 0), Point(5, 5*sqrt(3))).eulerline \
        == Point2D(5, 5*sqrt(3)/3)
    assert Triangle(Point(4, -6), Point(4, -1), Point(-3, 3)).eulerline \
        == Line(Point2D(S(64)/7, 3), Point2D(-S(29)/14, -S(7)/2))

def test_intersection():
    poly1 = Triangle(Point(0, 0), Point(1, 0), Point(0, 1))
    poly2 = Polygon(Point(0, 1), Point(-5, 0),
                    Point(0, -4), Point(0, S(1)/5),
                    Point(S(1)/2, -0.1), Point(1,0), Point(0, 1))

    assert poly1.intersection(poly2) == [Point2D(S(1)/3, 0),
        Segment(Point(0, S(1)/5), Point(0, 0)),
        Segment(Point(1, 0), Point(0, 1))]
    assert poly2.intersection(poly1) == [Point(S(1)/3, 0),
        Segment(Point(0, 0), Point(0, S(1)/5)),
        Segment(Point(1, 0), Point(0, 1))]
    assert poly1.intersection(Point(0, 0)) == [Point(0, 0)]
    assert poly1.intersection(Point(-12,  -43)) == []
    assert poly2.intersection(Line((-12, 0), (12, 0))) == [Point(-5, 0),
        Point(0, 0),Point(S(1)/3, 0), Point(1, 0)]
    assert poly2.intersection(Line((-12, 12), (12, 12))) == []
    assert poly2.intersection(Ray((-3,4), (1,0))) == [Segment(Point(1, 0),
        Point(0, 1))]
    assert poly2.intersection(Circle((0, -1), 1)) == [Point(0, -2),
        Point(0, 0)]
    assert poly1.intersection(poly1) == [Segment(Point(0, 0), Point(1, 0)),
        Segment(Point(0, 1), Point(0, 0)), Segment(Point(1, 0), Point(0, 1))]
    assert poly2.intersection(poly2) == [Segment(Point(-5, 0), Point(0, -4)),
        Segment(Point(0, -4), Point(0, S(1)/5)),
        Segment(Point(0, S(1)/5), Point(S(1)/2, -S(1)/10)),
        Segment(Point(0, 1), Point(-5, 0)),
        Segment(Point(S(1)/2, -S(1)/10), Point(1, 0)),
        Segment(Point(1, 0), Point(0, 1))]
    assert poly2.intersection(Triangle(Point(0, 1), Point(1, 0), Point(-1, 1))) \
        == [Point(-S(5)/7, S(6)/7), Segment(Point2D(0, 1), Point(1, 0))]
    assert poly1.intersection(RegularPolygon((-12, -15), 3, 3)) == []


def test_parameter_value():
    t = Symbol('t')
    sq = Polygon((0, 0), (0, 1), (1, 1), (1, 0))
    assert sq.parameter_value((0.5, 1), t) == {t: S(3)/8}
    q = Polygon((0, 0), (2, 1), (2, 4), (4, 0))
    assert q.parameter_value((4, 0), t) == {t: -6 + 3*sqrt(5)}  # ~= 0.708
    raises(ValueError, lambda: sq.parameter_value((5, 6), t))


def test_issue_12966():
    poly = Polygon(Point(0, 0), Point(0, 10), Point(5, 10), Point(5, 5),
        Point(10, 5), Point(10, 0))
    t = Symbol('t')
    pt = poly.arbitrary_point(t)
    DELTA = 5/poly.perimeter
    assert [pt.subs(t, DELTA*i) for i in range(int(1/DELTA))] == [
        Point(0, 0), Point(0, 5), Point(0, 10), Point(5, 10),
        Point(5, 5), Point(10, 5), Point(10, 0), Point(5, 0)]


def test_second_moment_of_area():
    x, y = symbols('x, y')
    # triangle
    p1, p2, p3 = [(0, 0), (4, 0), (0, 2)]
    p = (0, 0)
    # equation of hypotenuse
    eq_y = (1-x/4)*2
    I_yy = integrate((x**2) * (integrate(1, (y, 0, eq_y))), (x, 0, 4))
    I_xx = integrate(1 * (integrate(y**2, (y, 0, eq_y))), (x, 0, 4))
    I_xy = integrate(x * (integrate(y, (y, 0, eq_y))), (x, 0, 4))

    triangle = Polygon(p1, p2, p3)

    assert (I_xx - triangle.second_moment_of_area(p)[0]) == 0
    assert (I_yy - triangle.second_moment_of_area(p)[1]) == 0
    assert (I_xy - triangle.second_moment_of_area(p)[2]) == 0

    # rectangle
    p1, p2, p3, p4=[(0, 0), (4, 0), (4, 2), (0, 2)]
    I_yy = integrate((x**2) * integrate(1, (y, 0, 2)), (x, 0, 4))
    I_xx = integrate(1 * integrate(y**2, (y, 0, 2)), (x, 0, 4))
    I_xy = integrate(x * integrate(y, (y, 0, 2)), (x, 0, 4))

    rectangle = Polygon(p1, p2, p3, p4)

    assert (I_xx - rectangle.second_moment_of_area(p)[0]) == 0
    assert (I_yy - rectangle.second_moment_of_area(p)[1]) == 0
    assert (I_xy - rectangle.second_moment_of_area(p)[2]) == 0
