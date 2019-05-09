"""Tests for Dixon's and Macaulay's classes. """

from sympy import Matrix
from sympy.core import symbols
from sympy.tensor.indexed import IndexedBase

from sympy.polys.multivariate_resultants import (DixonResultant,
                                                 MacaulayResultant)

c, d = symbols("a, b")
x, y = symbols("x, y")

p =  c * x + y
q =  x + d * y

dixon = DixonResultant(polynomials=[p, q], variables=[x, y])
macaulay = MacaulayResultant(polynomials=[p, q], variables=[x, y])

def test_dixon_resultant_init():
    """Test init method of DixonResultant."""
    a = IndexedBase("alpha")

    assert dixon.polynomials == [p, q]
    assert dixon.variables == [x, y]
    assert dixon.n == 2
    assert dixon.m == 2
    assert dixon.dummy_variables == [a[0], a[1]]
    assert dixon.max_degrees == [1, 1]

def test_get_dixon_polynomial_numerical():
    """Test Dixon's polynomial for a numerical example."""
    a = IndexedBase("alpha")

    p = x + y
    q = x ** 2 + y **3
    h = x ** 2 + y

    dixon = DixonResultant([p, q, h], [x, y])
    polynomial = -x * y ** 2 * a[0] - x * y ** 2 * a[1] - x * y * a[0] \
    * a[1] - x * y * a[1] ** 2 - x * a[0] * a[1] ** 2 + x * a[0] - \
    y ** 2 * a[0] * a[1] + y ** 2 * a[1] - y * a[0] * a[1] ** 2 + y * \
    a[1] ** 2

    assert dixon.get_dixon_polynomial().factor() == polynomial

def test_get_upper_degree():
    """Tests upper degree function."""
    h = c * x ** 2 + y
    dixon = DixonResultant(polynomials=[h, q], variables=[x, y])

    assert dixon.get_upper_degree() == 3

def test_get_dixon_matrix_example_two():
    """Test Dixon's matrix for example from [Palancz08]_."""
    x, y, z = symbols('x, y, z')

    f = x ** 2 + y ** 2 - 1 + z * 0
    g = x ** 2 + z ** 2 - 1 + y * 0
    h = y ** 2 + z ** 2 - 1

    example_two = DixonResultant([f, g, h], [y, z])
    poly = example_two.get_dixon_polynomial()
    matrix = example_two.get_dixon_matrix(poly)

    expr = 1 - 8 * x ** 2 + 24 * x ** 4 - 32 * x ** 6 + 16 * x ** 8
    assert (matrix.det() - expr).expand() == 0

def test_get_dixon_matrix():
    """Test Dixon's resultant for a numerical example."""

    x, y = symbols('x, y')

    p = x + y
    q = x ** 2 + y ** 3
    h = x ** 2 + y

    dixon = DixonResultant([p, q, h], [x, y])
    polynomial = dixon.get_dixon_polynomial()

    assert dixon.get_dixon_matrix(polynomial).det() == 0

def test_macaulay_resultant_init():
    """Test init method of MacaulayResultant."""
    a = IndexedBase("alpha")

    assert macaulay.polynomials == [p, q]
    assert macaulay.variables == [x, y]
    assert macaulay.n == 2
    assert macaulay.degrees == [1, 1]
    assert macaulay.degree_m == 1
    assert macaulay.monomials_size == 2

def test_get_degree_m():
    assert macaulay._get_degree_m() == 1

def test_get_size():
    assert macaulay.get_size() == 2

def test_macaulay_example_one():
    """Tests the Macaulay for example from [Bruce97]_"""

    x, y, z = symbols('x, y, z')
    a_1_1, a_1_2, a_1_3 = symbols('a_1_1, a_1_2, a_1_3')
    a_2_2, a_2_3, a_3_3 = symbols('a_2_2, a_2_3, a_3_3')
    b_1_1, b_1_2, b_1_3 = symbols('b_1_1, b_1_2, b_1_3')
    b_2_2, b_2_3, b_3_3 = symbols('b_2_2, b_2_3, b_3_3')
    c_1, c_2, c_3 = symbols('c_1, c_2, c_3')

    f_1 = a_1_1 * x ** 2 + a_1_2 * x * y + a_1_3 * x * z + \
          a_2_2 * y ** 2 + a_2_3 * y * z + a_3_3 * z ** 2
    f_2 = b_1_1 * x ** 2 + b_1_2 * x * y + b_1_3 * x * z + \
          b_2_2 * y ** 2 + b_2_3 * y * z + b_3_3 * z ** 2
    f_3 = c_1 * x + c_2 * y + c_3 * z

    mac = MacaulayResultant([f_1, f_2, f_3], [x, y, z])

    assert mac.degrees == [2, 2, 1]
    assert mac.degree_m == 3

    assert mac.monomial_set == [x ** 3, x ** 2 * y, x ** 2 * z,
                                x * y ** 2,
                                x * y * z, x * z ** 2, y ** 3,
                                y ** 2 *z, y * z ** 2, z ** 3]
    assert mac.monomials_size == 10
    assert mac.get_row_coefficients() == [[x, y, z], [x, y, z],
                                          [x * y, x * z, y * z, z ** 2]]

    matrix = mac.get_matrix()
    assert matrix.shape == (mac.monomials_size, mac.monomials_size)
    assert mac.get_submatrix(matrix) == Matrix([[a_1_1, a_2_2],
                                                [b_1_1, b_2_2]])

def test_macaulay_example_two():
    """Tests the Macaulay formulation for example from [Stiller96]_."""

    x, y, z = symbols('x, y, z')
    a_0, a_1, a_2 = symbols('a_0, a_1, a_2')
    b_0, b_1, b_2 = symbols('b_0, b_1, b_2')
    c_0, c_1, c_2, c_3, c_4 = symbols('c_0, c_1, c_2, c_3, c_4')

    f = a_0 * y -  a_1 * x + a_2 * z
    g = b_1 * x ** 2 + b_0 * y ** 2 - b_2 * z ** 2
    h = c_0 * y - c_1 * x ** 3 + c_2 * x ** 2 * z - c_3 * x * z ** 2 + \
        c_4 * z ** 3

    mac = MacaulayResultant([f, g, h], [x, y, z])

    assert mac.degrees == [1, 2, 3]
    assert mac.degree_m == 4
    assert mac.monomials_size == 15
    assert len(mac.get_row_coefficients()) == mac.n

    matrix = mac.get_matrix()
    assert matrix.shape == (mac.monomials_size, mac.monomials_size)
    assert mac.get_submatrix(matrix) == Matrix([[-a_1, a_0, a_2, 0],
                                                [0, -a_1, 0, 0],
                                                [0, 0, -a_1, 0],
                                                [0, 0, 0, -a_1]])
