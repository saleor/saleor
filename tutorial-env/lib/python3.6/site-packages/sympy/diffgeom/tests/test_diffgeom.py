from sympy.diffgeom.rn import R2, R2_p, R2_r, R3_r, R3_c, R3_s
from sympy.diffgeom import (Commutator, Differential, TensorProduct,
        WedgeProduct, BaseCovarDerivativeOp, CovarDerivativeOp, LieDerivative,
        covariant_order, contravariant_order, twoform_to_matrix, metric_to_Christoffel_1st,
        metric_to_Christoffel_2nd, metric_to_Riemann_components,
        metric_to_Ricci_components, intcurve_diffequ, intcurve_series)
from sympy.core import Symbol, symbols
from sympy.simplify import trigsimp, simplify
from sympy.functions import sqrt, atan2, sin
from sympy.matrices import Matrix
from sympy.utilities.pytest import raises

TP = TensorProduct


def test_R2():
    x0, y0, r0, theta0 = symbols('x0, y0, r0, theta0', real=True)
    point_r = R2_r.point([x0, y0])
    point_p = R2_p.point([r0, theta0])

    # r**2 = x**2 + y**2
    assert (R2.r**2 - R2.x**2 - R2.y**2).rcall(point_r) == 0
    assert trigsimp( (R2.r**2 - R2.x**2 - R2.y**2).rcall(point_p) ) == 0
    assert trigsimp(R2.e_r(R2.x**2 + R2.y**2).rcall(point_p).doit()) == 2*r0

    # polar->rect->polar == Id
    a, b = symbols('a b', positive=True)
    m = Matrix([[a], [b]])
    #TODO assert m == R2_r.coord_tuple_transform_to(R2_p, R2_p.coord_tuple_transform_to(R2_r, [a, b])).applyfunc(simplify)
    assert m == R2_p.coord_tuple_transform_to(
        R2_r, R2_r.coord_tuple_transform_to(R2_p, m)).applyfunc(simplify)


def test_R3():
    a, b, c = symbols('a b c', positive=True)
    m = Matrix([[a], [b], [c]])
    assert m == R3_c.coord_tuple_transform_to(
        R3_r, R3_r.coord_tuple_transform_to(R3_c, m)).applyfunc(simplify)
    #TODO assert m == R3_r.coord_tuple_transform_to(R3_c, R3_c.coord_tuple_transform_to(R3_r, m)).applyfunc(simplify)
    assert m == R3_s.coord_tuple_transform_to(
        R3_r, R3_r.coord_tuple_transform_to(R3_s, m)).applyfunc(simplify)
    #TODO assert m == R3_r.coord_tuple_transform_to(R3_s, R3_s.coord_tuple_transform_to(R3_r, m)).applyfunc(simplify)
    assert m == R3_s.coord_tuple_transform_to(
        R3_c, R3_c.coord_tuple_transform_to(R3_s, m)).applyfunc(simplify)
    #TODO assert m == R3_c.coord_tuple_transform_to(R3_s, R3_s.coord_tuple_transform_to(R3_c, m)).applyfunc(simplify)


def test_point():
    x, y = symbols('x, y')
    p = R2_r.point([x, y])
    #TODO assert p.free_symbols() == set([x, y])
    assert p.coords(R2_r) == p.coords() == Matrix([x, y])
    assert p.coords(R2_p) == Matrix([sqrt(x**2 + y**2), atan2(y, x)])


def test_commutator():
    assert Commutator(R2.e_x, R2.e_y) == 0
    assert Commutator(R2.x*R2.e_x, R2.x*R2.e_x) == 0
    assert Commutator(R2.x*R2.e_x, R2.x*R2.e_y) == R2.x*R2.e_y
    c = Commutator(R2.e_x, R2.e_r)
    assert c(R2.x) == R2.y*(R2.x**2 + R2.y**2)**(-1)*sin(R2.theta)


def test_differential():
    xdy = R2.x*R2.dy
    dxdy = Differential(xdy)
    assert xdy.rcall(None) == xdy
    assert dxdy(R2.e_x, R2.e_y) == 1
    assert dxdy(R2.e_x, R2.x*R2.e_y) == R2.x
    assert Differential(dxdy) == 0


def test_products():
    assert TensorProduct(
        R2.dx, R2.dy)(R2.e_x, R2.e_y) == R2.dx(R2.e_x)*R2.dy(R2.e_y) == 1
    assert TensorProduct(R2.dx, R2.dy)(None, R2.e_y) == R2.dx
    assert TensorProduct(R2.dx, R2.dy)(R2.e_x, None) == R2.dy
    assert TensorProduct(R2.dx, R2.dy)(R2.e_x) == R2.dy
    assert TensorProduct(R2.x, R2.dx) == R2.x*R2.dx
    assert TensorProduct(
        R2.e_x, R2.e_y)(R2.x, R2.y) == R2.e_x(R2.x) * R2.e_y(R2.y) == 1
    assert TensorProduct(R2.e_x, R2.e_y)(None, R2.y) == R2.e_x
    assert TensorProduct(R2.e_x, R2.e_y)(R2.x, None) == R2.e_y
    assert TensorProduct(R2.e_x, R2.e_y)(R2.x) == R2.e_y
    assert TensorProduct(R2.x, R2.e_x) == R2.x * R2.e_x
    assert TensorProduct(
        R2.dx, R2.e_y)(R2.e_x, R2.y) == R2.dx(R2.e_x) * R2.e_y(R2.y) == 1
    assert TensorProduct(R2.dx, R2.e_y)(None, R2.y) == R2.dx
    assert TensorProduct(R2.dx, R2.e_y)(R2.e_x, None) == R2.e_y
    assert TensorProduct(R2.dx, R2.e_y)(R2.e_x) == R2.e_y
    assert TensorProduct(R2.x, R2.e_x) == R2.x * R2.e_x
    assert TensorProduct(
        R2.e_x, R2.dy)(R2.x, R2.e_y) == R2.e_x(R2.x) * R2.dy(R2.e_y) == 1
    assert TensorProduct(R2.e_x, R2.dy)(None, R2.e_y) == R2.e_x
    assert TensorProduct(R2.e_x, R2.dy)(R2.x, None) == R2.dy
    assert TensorProduct(R2.e_x, R2.dy)(R2.x) == R2.dy
    assert TensorProduct(R2.e_y,R2.e_x)(R2.x**2 + R2.y**2,R2.x**2 + R2.y**2) == 4*R2.x*R2.y

    assert WedgeProduct(R2.dx, R2.dy)(R2.e_x, R2.e_y) == 1
    assert WedgeProduct(R2.e_x, R2.e_y)(R2.x, R2.y) == 1


def test_lie_derivative():
    assert LieDerivative(R2.e_x, R2.y) == R2.e_x(R2.y) == 0
    assert LieDerivative(R2.e_x, R2.x) == R2.e_x(R2.x) == 1
    assert LieDerivative(R2.e_x, R2.e_x) == Commutator(R2.e_x, R2.e_x) == 0
    assert LieDerivative(R2.e_x, R2.e_r) == Commutator(R2.e_x, R2.e_r)
    assert LieDerivative(R2.e_x + R2.e_y, R2.x) == 1
    assert LieDerivative(
        R2.e_x, TensorProduct(R2.dx, R2.dy))(R2.e_x, R2.e_y) == 0


def test_covar_deriv():
    ch = metric_to_Christoffel_2nd(TP(R2.dx, R2.dx) + TP(R2.dy, R2.dy))
    cvd = BaseCovarDerivativeOp(R2_r, 0, ch)
    assert cvd(R2.x) == 1
    assert cvd(R2.x*R2.e_x) == R2.e_x
    cvd = CovarDerivativeOp(R2.x*R2.e_x, ch)
    assert cvd(R2.x) == R2.x
    assert cvd(R2.x*R2.e_x) == R2.x*R2.e_x


def test_intcurve_diffequ():
    t = symbols('t')
    start_point = R2_r.point([1, 0])
    vector_field = -R2.y*R2.e_x + R2.x*R2.e_y
    equations, init_cond = intcurve_diffequ(vector_field, t, start_point)
    assert str(equations) == '[f_1(t) + Derivative(f_0(t), t), -f_0(t) + Derivative(f_1(t), t)]'
    assert str(init_cond) == '[f_0(0) - 1, f_1(0)]'
    equations, init_cond = intcurve_diffequ(vector_field, t, start_point, R2_p)
    assert str(
        equations) == '[Derivative(f_0(t), t), Derivative(f_1(t), t) - 1]'
    assert str(init_cond) == '[f_0(0) - 1, f_1(0)]'


def test_helpers_and_coordinate_dependent():
    one_form = R2.dr + R2.dx
    two_form = Differential(R2.x*R2.dr + R2.r*R2.dx)
    three_form = Differential(
        R2.y*two_form) + Differential(R2.x*Differential(R2.r*R2.dr))
    metric = TensorProduct(R2.dx, R2.dx) + TensorProduct(R2.dy, R2.dy)
    metric_ambig = TensorProduct(R2.dx, R2.dx) + TensorProduct(R2.dr, R2.dr)
    misform_a = TensorProduct(R2.dr, R2.dr) + R2.dr
    misform_b = R2.dr**4
    misform_c = R2.dx*R2.dy
    twoform_not_sym = TensorProduct(R2.dx, R2.dx) + TensorProduct(R2.dx, R2.dy)
    twoform_not_TP = WedgeProduct(R2.dx, R2.dy)

    one_vector = R2.e_x + R2.e_y
    two_vector = TensorProduct(R2.e_x, R2.e_y)
    three_vector = TensorProduct(R2.e_x, R2.e_y, R2.e_x)
    two_wp = WedgeProduct(R2.e_x,R2.e_y)

    assert covariant_order(one_form) == 1
    assert covariant_order(two_form) == 2
    assert covariant_order(three_form) == 3
    assert covariant_order(two_form + metric) == 2
    assert covariant_order(two_form + metric_ambig) == 2
    assert covariant_order(two_form + twoform_not_sym) == 2
    assert covariant_order(two_form + twoform_not_TP) == 2

    assert contravariant_order(one_vector) == 1
    assert contravariant_order(two_vector) == 2
    assert contravariant_order(three_vector) == 3
    assert contravariant_order(two_vector + two_wp) == 2

    raises(ValueError, lambda: covariant_order(misform_a))
    raises(ValueError, lambda: covariant_order(misform_b))
    raises(ValueError, lambda: covariant_order(misform_c))

    assert twoform_to_matrix(metric) == Matrix([[1, 0], [0, 1]])
    assert twoform_to_matrix(twoform_not_sym) == Matrix([[1, 0], [1, 0]])
    assert twoform_to_matrix(twoform_not_TP) == Matrix([[0, -1], [1, 0]])

    raises(ValueError, lambda: twoform_to_matrix(one_form))
    raises(ValueError, lambda: twoform_to_matrix(three_form))
    raises(ValueError, lambda: twoform_to_matrix(metric_ambig))

    raises(ValueError, lambda: metric_to_Christoffel_1st(twoform_not_sym))
    raises(ValueError, lambda: metric_to_Christoffel_2nd(twoform_not_sym))
    raises(ValueError, lambda: metric_to_Riemann_components(twoform_not_sym))
    raises(ValueError, lambda: metric_to_Ricci_components(twoform_not_sym))


def test_correct_arguments():
    raises(ValueError, lambda: R2.e_x(R2.e_x))
    raises(ValueError, lambda: R2.e_x(R2.dx))

    raises(ValueError, lambda: Commutator(R2.e_x, R2.x))
    raises(ValueError, lambda: Commutator(R2.dx, R2.e_x))

    raises(ValueError, lambda: Differential(Differential(R2.e_x)))

    raises(ValueError, lambda: R2.dx(R2.x))

    raises(ValueError, lambda: LieDerivative(R2.dx, R2.dx))
    raises(ValueError, lambda: LieDerivative(R2.x, R2.dx))

    raises(ValueError, lambda: CovarDerivativeOp(R2.dx, []))
    raises(ValueError, lambda: CovarDerivativeOp(R2.x, []))

    a = Symbol('a')
    raises(ValueError, lambda: intcurve_series(R2.dx, a, R2_r.point([1, 2])))
    raises(ValueError, lambda: intcurve_series(R2.x, a, R2_r.point([1, 2])))

    raises(ValueError, lambda: intcurve_diffequ(R2.dx, a, R2_r.point([1, 2])))
    raises(ValueError, lambda: intcurve_diffequ(R2.x, a, R2_r.point([1, 2])))

    raises(ValueError, lambda: contravariant_order(R2.e_x + R2.dx))
    raises(ValueError, lambda: covariant_order(R2.e_x + R2.dx))

    raises(ValueError, lambda: contravariant_order(R2.e_x*R2.e_y))
    raises(ValueError, lambda: covariant_order(R2.dx*R2.dy))

def test_simplify():
    x, y = R2_r.coord_functions()
    dx, dy = R2_r.base_oneforms()
    ex, ey = R2_r.base_vectors()
    assert simplify(x) == x
    assert simplify(x*y) == x*y
    assert simplify(dx*dy) == dx*dy
    assert simplify(ex*ey) == ex*ey
    assert ((1-x)*dx)/(1-x)**2 == dx/(1-x)
