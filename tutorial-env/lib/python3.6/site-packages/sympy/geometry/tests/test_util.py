from sympy import Symbol, sqrt, Derivative, S, Function, exp
from sympy.geometry import Point, Point2D, Line, Circle, Polygon, Segment, convex_hull, intersection, centroid
from sympy.geometry.util import idiff, closest_points, farthest_points, _ordered_points
from sympy.solvers.solvers import solve
from sympy.utilities.pytest import raises


def test_idiff():
    x = Symbol('x', real=True)
    y = Symbol('y', real=True)
    t = Symbol('t', real=True)
    f = Function('f')
    g = Function('g')
    # the use of idiff in ellipse also provides coverage
    circ = x**2 + y**2 - 4
    ans = -3*x*(x**2 + y**2)/y**5
    assert ans == idiff(circ, y, x, 3).simplify()
    assert ans == idiff(circ, [y], x, 3).simplify()
    assert idiff(circ, y, x, 3).simplify() == ans
    explicit  = 12*x/sqrt(-x**2 + 4)**5
    assert ans.subs(y, solve(circ, y)[0]).equals(explicit)
    assert True in [sol.diff(x, 3).equals(explicit) for sol in solve(circ, y)]
    assert idiff(x + t + y, [y, t], x) == -Derivative(t, x) - 1
    assert idiff(f(x) * exp(f(x)) - x * exp(x), f(x), x) == (x + 1) * exp(x - f(x))/(f(x) + 1)
    assert idiff(f(x) - y * exp(x), [f(x), y], x) == (y + Derivative(y, x)) * exp(x)
    assert idiff(f(x) - y * exp(x), [y, f(x)], x) == -y + exp(-x) * Derivative(f(x), x)
    assert idiff(f(x) - g(x), [f(x), g(x)], x) == Derivative(g(x), x)


def test_intersection():
    assert intersection(Point(0, 0)) == []
    raises(TypeError, lambda: intersection(Point(0, 0), 3))
    assert intersection(
            Segment((0, 0), (2, 0)),
            Segment((-1, 0), (1, 0)),
            Line((0, 0), (0, 1)), pairwise=True) == [
        Point(0, 0), Segment((0, 0), (1, 0))]
    assert intersection(
            Line((0, 0), (0, 1)),
            Segment((0, 0), (2, 0)),
            Segment((-1, 0), (1, 0)), pairwise=True) == [
        Point(0, 0), Segment((0, 0), (1, 0))]
    assert intersection(
            Line((0, 0), (0, 1)),
            Segment((0, 0), (2, 0)),
            Segment((-1, 0), (1, 0)),
            Line((0, 0), slope=1), pairwise=True) == [
        Point(0, 0), Segment((0, 0), (1, 0))]


def test_convex_hull():
    raises(TypeError, lambda: convex_hull(Point(0, 0), 3))
    points = [(1, -1), (1, -2), (3, -1), (-5, -2), (15, -4)]
    assert convex_hull(*points, **dict(polygon=False)) == (
        [Point2D(-5, -2), Point2D(1, -1), Point2D(3, -1), Point2D(15, -4)],
        [Point2D(-5, -2), Point2D(15, -4)])


def test_centroid():
    p = Polygon((0, 0), (10, 0), (10, 10))
    q = p.translate(0, 20)
    assert centroid(p, q) == Point(20, 40)/3
    p = Segment((0, 0), (2, 0))
    q = Segment((0, 0), (2, 2))
    assert centroid(p, q) == Point(1, -sqrt(2) + 2)
    assert centroid(Point(0, 0), Point(2, 0)) == Point(2, 0)/2
    assert centroid(Point(0, 0), Point(0, 0), Point(2, 0)) == Point(2, 0)/3


def test_farthest_points_closest_points():
    from random import randint
    from sympy.utilities.iterables import subsets

    for how in (min, max):
        if how is min:
            func = closest_points
        else:
            func = farthest_points

        raises(ValueError, lambda: func(Point2D(0, 0), Point2D(0, 0)))

        # 3rd pt dx is close and pt is closer to 1st pt
        p1 = [Point2D(0, 0), Point2D(3, 0), Point2D(1, 1)]
        # 3rd pt dx is close and pt is closer to 2nd pt
        p2 = [Point2D(0, 0), Point2D(3, 0), Point2D(2, 1)]
        # 3rd pt dx is close and but pt is not closer
        p3 = [Point2D(0, 0), Point2D(3, 0), Point2D(1, 10)]
        # 3rd pt dx is not closer and it's closer to 2nd pt
        p4 = [Point2D(0, 0), Point2D(3, 0), Point2D(4, 0)]
        # 3rd pt dx is not closer and it's closer to 1st pt
        p5 = [Point2D(0, 0), Point2D(3, 0), Point2D(-1, 0)]
        # duplicate point doesn't affect outcome
        dup = [Point2D(0, 0), Point2D(3, 0), Point2D(3, 0), Point2D(-1, 0)]
        # symbolic
        x = Symbol('x', positive=True)
        s = [Point2D(a) for a in ((x, 1), (x + 3, 2), (x + 2, 2))]

        for points in (p1, p2, p3, p4, p5, s, dup):
            d = how(i.distance(j) for i, j in subsets(points, 2))
            ans = a, b = list(func(*points))[0]
            a.distance(b) == d
            assert ans == _ordered_points(ans)

        # if the following ever fails, the above tests were not sufficient
        # and the logical error in the routine should be fixed
        points = set()
        while len(points) != 7:
            points.add(Point2D(randint(1, 100), randint(1, 100)))
        points = list(points)
        d = how(i.distance(j) for i, j in subsets(points, 2))
        ans = a, b = list(func(*points))[0]
        a.distance(b) == d
        assert ans == _ordered_points(ans)

    # equidistant points
    a, b, c = (
        Point2D(0, 0), Point2D(1, 0), Point2D(S(1)/2, sqrt(3)/2))
    ans = set([_ordered_points((i, j))
        for i, j in subsets((a, b, c), 2)])
    assert closest_points(b, c, a) == ans
    assert farthest_points(b, c, a) == ans

    # unique to farthest
    points = [(1, 1), (1, 2), (3, 1), (-5, 2), (15, 4)]
    assert farthest_points(*points) == set(
        [(Point2D(-5, 2), Point2D(15, 4))])
    points = [(1, -1), (1, -2), (3, -1), (-5, -2), (15, -4)]
    assert farthest_points(*points) == set(
        [(Point2D(-5, -2), Point2D(15, -4))])
    assert farthest_points((1, 1), (0, 0)) == set(
        [(Point2D(0, 0), Point2D(1, 1))])
    raises(ValueError, lambda: farthest_points((1, 1)))
