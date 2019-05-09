"""
This module contains functions for two multivariate resultants. These
are:

- Dixon's resultant.
- Macaulay's resultant.

Multivariate resultants are used to identify whether a multivariate
system has common roots. That is when the resultant is equal to zero.
"""

from sympy import IndexedBase, Matrix, Mul, Poly
from sympy import rem, prod, degree_list, diag
from sympy.core.compatibility import range
from sympy.polys.monomials import monomial_deg, itermonomials
from sympy.polys.orderings import monomial_key
from sympy.polys.polytools import poly_from_expr, total_degree
from sympy.functions.combinatorial.factorials import binomial

from itertools import combinations_with_replacement


class DixonResultant():
    """
    A class for retrieving the Dixon's resultant of a multivariate
    system.

    Examples
    ========

    >>> from sympy.core import symbols

    >>> from sympy.polys.multivariate_resultants import DixonResultant
    >>> x, y = symbols('x, y')

    >>> p = x + y
    >>> q = x ** 2 + y ** 3
    >>> h = x ** 2 + y

    >>> dixon = DixonResultant(variables=[x, y], polynomials=[p, q, h])
    >>> poly = dixon.get_dixon_polynomial()
    >>> matrix = dixon.get_dixon_matrix(polynomial=poly)
    >>> matrix
    Matrix([
    [ 0,  0, -1,  0, -1],
    [ 0, -1,  0, -1,  0],
    [-1,  0,  1,  0,  0],
    [ 0, -1,  0,  0,  1],
    [-1,  0,  0,  1,  0]])
    >>> matrix.det()
    0

    See Also
    ========

    Notebook in examples: sympy/example/notebooks.

    References
    ==========

    .. [1] [Kapur1994]_
    .. [2] [Palancz08]_

    """

    def __init__(self, polynomials, variables):
        """
        A class that takes two lists, a list of polynomials and list of
        variables. Returns the Dixon matrix of the multivariate system.

        Parameters
        ----------
        polynomials : list of polynomials
            A  list of m n-degree polynomials
        variables: list
            A list of all n variables
        """
        self.polynomials = polynomials
        self.variables = variables

        self.n = len(self.variables)
        self.m = len(self.polynomials)

        a = IndexedBase("alpha")
        # A list of n alpha variables (the replacing variables)
        self.dummy_variables = [a[i] for i in range(self.n)]

        # A list of the d_max of each variable.
        self.max_degrees = [
            max(degree_list(poly)[i] for poly in self.polynomials)
            for i in range(self.n)]

    def get_dixon_polynomial(self):
        r"""
        Returns
        =======

        dixon_polynomial: polynomial
            Dixon's polynomial is calculated as:

            delta = Delta(A) / ((x_1 - a_1) ... (x_n - a_n)) where,

            A =  |p_1(x_1,... x_n), ..., p_n(x_1,... x_n)|
                 |p_1(a_1,... x_n), ..., p_n(a_1,... x_n)|
                 |...             , ...,              ...|
                 |p_1(a_1,... a_n), ..., p_n(a_1,... a_n)|
        """
        if self.m != (self.n + 1):
            raise ValueError('Method invalid for given combination.')

        # First row
        rows = [self.polynomials]

        temp = list(self.variables)

        for idx in range(self.n):
            temp[idx] = self.dummy_variables[idx]
            substitution = {var: t for var, t in zip(self.variables, temp)}
            rows.append([f.subs(substitution) for f in self.polynomials])

        A = Matrix(rows)

        terms = zip(self.variables, self.dummy_variables)
        product_of_differences = Mul(*[a - b for a, b in terms])
        dixon_polynomial = (A.det() / product_of_differences).factor()

        return poly_from_expr(dixon_polynomial, self.dummy_variables)[0]

    def get_upper_degree(self):
        list_of_products = [self.variables[i] ** self.max_degrees[i]
                            for i in range(self.n)]
        product = prod(list_of_products)
        product = Poly(product).monoms()

        return monomial_deg(*product)

    def get_dixon_matrix(self, polynomial):
        r"""
        Construct the Dixon matrix from the coefficients of polynomial
        \alpha. Each coefficient is viewed as a polynomial of x_1, ...,
        x_n.
        """

        # A list of coefficients (in x_i, ..., x_n terms) of the power
        # products a_1, ..., a_n in Dixon's polynomial.
        coefficients = polynomial.coeffs()

        monomials = list(itermonomials(self.variables,
                                       self.get_upper_degree()))
        monomials = sorted(monomials, reverse=True,
                           key=monomial_key('lex', self.variables))

        dixon_matrix = Matrix([[Poly(c, *self.variables).coeff_monomial(m)
                                for m in monomials]
                                for c in coefficients])

        keep = [column for column in range(dixon_matrix.shape[-1])
                if any([element != 0 for element
                        in dixon_matrix[:, column]])]
        return dixon_matrix[:, keep]

class MacaulayResultant():
    """
    A class for calculating the Macaulay resultant. Note that the
    polynomials must be homogenized and their coefficients must be
    given as symbols.

    Examples
    ========

    >>> from sympy.core import symbols

    >>> from sympy.polys.multivariate_resultants import MacaulayResultant
    >>> x, y, z = symbols('x, y, z')

    >>> a_0, a_1, a_2 = symbols('a_0, a_1, a_2')
    >>> b_0, b_1, b_2 = symbols('b_0, b_1, b_2')
    >>> c_0, c_1, c_2,c_3, c_4 = symbols('c_0, c_1, c_2, c_3, c_4')

    >>> f = a_0 * y -  a_1 * x + a_2 * z
    >>> g = b_1 * x ** 2 + b_0 * y ** 2 - b_2 * z ** 2
    >>> h = c_0 * y * z ** 2 - c_1 * x ** 3 + c_2 * x ** 2 * z - c_3 * x * z ** 2 + c_4 * z ** 3

    >>> mac = MacaulayResultant(polynomials=[f, g, h], variables=[x, y, z])
    >>> mac.monomial_set
    [x**4, x**3*y, x**3*z, x**2*y**2, x**2*y*z, x**2*z**2, x*y**3,
    x*y**2*z, x*y*z**2, x*z**3, y**4, y**3*z, y**2*z**2, y*z**3, z**4]
    >>> matrix = mac.get_matrix()
    >>> submatrix = mac.get_submatrix(matrix)
    >>> submatrix
    Matrix([
    [-a_1,  a_0,  a_2,    0],
    [   0, -a_1,    0,    0],
    [   0,    0, -a_1,    0],
    [   0,    0,    0, -a_1]])

    See Also
    ========

    Notebook in examples: sympy/example/notebooks.

    References
    ==========

    .. [1] [Bruce97]_
    .. [2] [Stiller96]_

    """
    def __init__(self, polynomials, variables):
        """
        Parameters
        ==========

        variables: list
            A list of all n variables
        polynomials : list of sympy polynomials
            A  list of m n-degree polynomials
        """
        self.polynomials = polynomials
        self.variables = variables
        self.n = len(variables)

        # A list of the d_max of each polynomial.
        self.degrees = [total_degree(poly, *self.variables) for poly
                        in self.polynomials]

        self.degree_m = self._get_degree_m()
        self.monomials_size = self.get_size()

        # The set T of all possible monomials of degree degree_m
        self.monomial_set = self.get_monomials_of_certain_degree(self.degree_m)

    def _get_degree_m(self):
        r"""
        Returns
        =======

        degree_m: int
            The degree_m is calculated as  1 + \sum_1 ^ n (d_i - 1),
            where d_i is the degree of the i polynomial
        """
        return 1 + sum(d - 1 for d in self.degrees)

    def get_size(self):
        r"""
        Returns
        =======

        size: int
            The size of set T. Set T is the set of all possible
            monomials of the n variables for degree equal to the
            degree_m
        """
        return binomial(self.degree_m + self.n - 1, self.n - 1)

    def get_monomials_of_certain_degree(self, degree):
        """
        Returns
        =======

        monomials: list
            A list of monomials of a certain degree.
        """
        monomials = [Mul(*monomial) for monomial
                     in combinations_with_replacement(self.variables,
                                                      degree)]

        return sorted(monomials, reverse=True,
                      key=monomial_key('lex', self.variables))

    def get_row_coefficients(self):
        """
        Returns
        =======

        row_coefficients: list
            The row coefficients of Macaulay's matrix
        """
        row_coefficients = []
        divisible = []
        for i in range(self.n):
            if i == 0:
                degree = self.degree_m - self.degrees[i]
                monomial = self.get_monomials_of_certain_degree(degree)
                row_coefficients.append(monomial)
            else:
                divisible.append(self.variables[i - 1] **
                                 self.degrees[i - 1])
                degree = self.degree_m - self.degrees[i]
                poss_rows = self.get_monomials_of_certain_degree(degree)
                for div in divisible:
                    for p in poss_rows:
                        if rem(p, div) == 0:
                            poss_rows = [item for item in poss_rows
                                         if item != p]
                row_coefficients.append(poss_rows)
        return row_coefficients

    def get_matrix(self):
        """
        Returns
        =======

        macaulay_matrix: Matrix
            The Macaulay numerator matrix
        """
        rows = []
        row_coefficients = self.get_row_coefficients()
        for i in range(self.n):
            for multiplier in row_coefficients[i]:
                coefficients = []
                poly = Poly(self.polynomials[i] * multiplier,
                            *self.variables)

                for mono in self.monomial_set:
                    coefficients.append(poly.coeff_monomial(mono))
                rows.append(coefficients)

        macaulay_matrix = Matrix(rows)
        return macaulay_matrix

    def get_reduced_nonreduced(self):
        r"""
        Returns
        =======

        reduced: list
            A list of the reduced monomials
        non_reduced: list
            A list of the monomials that are not reduced

        Definition
        ==========

        A polynomial is said to be reduced in x_i, if its degree (the
        maximum degree of its monomials) in x_i is less than d_i. A
        polynomial that is reduced in all variables but one is said
        simply to be reduced.
        """
        divisible = []
        for m in self.monomial_set:
            temp = []
            for i, v in enumerate(self.variables):
                temp.append(bool(total_degree(m, v) >= self.degrees[i]))
            divisible.append(temp)
        reduced = [i for i, r in enumerate(divisible)
                   if sum(r) < self.n - 1]
        non_reduced = [i for i, r in enumerate(divisible)
                       if sum(r) >= self.n -1]

        return reduced, non_reduced

    def get_submatrix(self, matrix):
        r"""
        Returns
        =======

        macaulay_submatrix: Matrix
            The Macaulay denominator matrix. Columns that are non reduced are kept.
            The row which contains one of the a_{i}s is dropped. a_{i}s
            are the coefficients of x_i ^ {d_i}.
        """
        reduced, non_reduced = self.get_reduced_nonreduced()

        # if reduced == [], then det(matrix) should be 1
        if reduced == []:
            return diag([1])

        # reduced != []
        reduction_set = [v ** self.degrees[i] for i, v
                         in enumerate(self.variables)]

        ais = list([self.polynomials[i].coeff(reduction_set[i])
                    for i in range(self.n)])

        reduced_matrix = matrix[:, reduced]
        keep = []
        for row in range(reduced_matrix.rows):
            check = [ai in reduced_matrix[row, :] for ai in ais]
            if True not in check:
                keep.append(row)

        return matrix[keep, non_reduced]
