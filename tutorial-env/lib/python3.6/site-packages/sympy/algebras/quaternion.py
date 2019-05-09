# References :
# http://www.euclideanspace.com/maths/algebra/realNormedAlgebra/quaternions/
# https://en.wikipedia.org/wiki/Quaternion
from __future__ import print_function

from sympy import Rational
from sympy import re, im, conjugate
from sympy import sqrt, sin, cos, acos, exp, ln
from sympy import trigsimp
from sympy import integrate
from sympy import Matrix, Add, Mul
from sympy import sympify
from sympy.core.compatibility import SYMPY_INTS
from sympy.core.expr import Expr
from sympy.core.numbers import Integer


class Quaternion(Expr):
    """Provides basic quaternion operations.
    Quaternion objects can be instantiated as Quaternion(a, b, c, d)
    as in (a + b*i + c*j + d*k).

    Examples
    ========

    >>> from sympy.algebras.quaternion import Quaternion
    >>> q = Quaternion(1, 2, 3, 4)
    >>> q
    1 + 2*i + 3*j + 4*k

    Quaternions over complex fields can be defined as :

    >>> from sympy.algebras.quaternion import Quaternion
    >>> from sympy import symbols, I
    >>> x = symbols('x')
    >>> q1 = Quaternion(x, x**3, x, x**2, real_field = False)
    >>> q2 = Quaternion(3 + 4*I, 2 + 5*I, 0, 7 + 8*I, real_field = False)
    >>> q1
    x + x**3*i + x*j + x**2*k
    >>> q2
    (3 + 4*I) + (2 + 5*I)*i + 0*j + (7 + 8*I)*k
    """
    _op_priority = 11.0

    is_commutative = False

    def __new__(cls, a=0, b=0, c=0, d=0, real_field=True):
        a = sympify(a)
        b = sympify(b)
        c = sympify(c)
        d = sympify(d)

        if any(i.is_commutative is False for i in [a, b, c, d]):
            raise ValueError("arguments have to be commutative")
        else:
            obj = Expr.__new__(cls, a, b, c, d)
            obj._a = a
            obj._b = b
            obj._c = c
            obj._d = d
            obj._real_field = real_field
            return obj

    @property
    def a(self):
        return self._a

    @property
    def b(self):
        return self._b

    @property
    def c(self):
        return self._c

    @property
    def d(self):
        return self._d
    @property
    def real_field(self):
        return self._real_field

    @classmethod
    def from_axis_angle(cls, vector, angle):
        """Returns a rotation quaternion given the axis and the angle of rotation.

        Parameters
        ==========

        vector : tuple of three numbers
            The vector representation of the given axis.
        angle : number
            The angle by which axis is rotated (in radians).

        Returns
        =======

        Quaternion
            The normalized rotation quaternion calculated from the given axis and the angle of rotation.

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import pi, sqrt
        >>> q = Quaternion.from_axis_angle((sqrt(3)/3, sqrt(3)/3, sqrt(3)/3), 2*pi/3)
        >>> q
        1/2 + 1/2*i + 1/2*j + 1/2*k
        """
        (x, y, z) = vector
        norm = sqrt(x**2 + y**2 + z**2)
        (x, y, z) = (x / norm, y / norm, z / norm)
        s = sin(angle * Rational(1, 2))
        a = cos(angle * Rational(1, 2))
        b = x * s
        c = y * s
        d = z * s

        return cls(a, b, c, d).normalize()

    @classmethod
    def from_rotation_matrix(cls, M):
        """Returns the equivalent quaternion of a matrix. The quaternion will be normalized
        only if the matrix is special orthogonal (orthogonal and det(M) = 1).

        Parameters
        ==========

        M : Matrix
            Input matrix to be converted to equivalent quaternion. M must be special
            orthogonal (orthogonal and det(M) = 1) for the quaternion to be normalized.

        Returns
        =======

        Quaternion
            The quaternion equivalent to given matrix.

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import Matrix, symbols, cos, sin, trigsimp
        >>> x = symbols('x')
        >>> M = Matrix([[cos(x), -sin(x), 0], [sin(x), cos(x), 0], [0, 0, 1]])
        >>> q = trigsimp(Quaternion.from_rotation_matrix(M))
        >>> q
        sqrt(2)*sqrt(cos(x) + 1)/2 + 0*i + 0*j + sqrt(2 - 2*cos(x))/2*k
        """

        absQ = M.det()**Rational(1, 3)

        a = sqrt(absQ + M[0, 0] + M[1, 1] + M[2, 2]) / 2
        b = sqrt(absQ + M[0, 0] - M[1, 1] - M[2, 2]) / 2
        c = sqrt(absQ - M[0, 0] + M[1, 1] - M[2, 2]) / 2
        d = sqrt(absQ - M[0, 0] - M[1, 1] + M[2, 2]) / 2

        try:
            b = Quaternion.__copysign(b, M[2, 1] - M[1, 2])
            c = Quaternion.__copysign(c, M[0, 2] - M[2, 0])
            d = Quaternion.__copysign(d, M[1, 0] - M[0, 1])

        except Exception:
            pass

        return Quaternion(a, b, c, d)

    @staticmethod
    def __copysign(x, y):

        # Takes the sign from the second term and sets the sign of the first
        # without altering the magnitude.

        if y == 0:
            return 0
        return x if x*y > 0 else -x

    def __add__(self, other):
        return self.add(other)

    def __radd__(self, other):
        return self.add(other)

    def __sub__(self, other):
        return self.add(other*-1)

    def __mul__(self, other):
        return self._generic_mul(self, other)

    def __rmul__(self, other):
        return self._generic_mul(other, self)

    def __pow__(self, p):
        return self.pow(p)

    def __neg__(self):
        return Quaternion(-self._a, -self._b, -self._c, -self.d)

    def _eval_Integral(self, *args):
        return self.integrate(*args)

    def diff(self, *symbols, **kwargs):
        kwargs.setdefault('evaluate', True)
        return self.func(*[a.diff(*symbols, **kwargs) for a  in self.args])

    def add(self, other):
        """Adds quaternions.

        Parameters
        ==========

        other : Quaternion
            The quaternion to add to current (self) quaternion.

        Returns
        =======

        Quaternion
            The resultant quaternion after adding self to other

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import symbols
        >>> q1 = Quaternion(1, 2, 3, 4)
        >>> q2 = Quaternion(5, 6, 7, 8)
        >>> q1.add(q2)
        6 + 8*i + 10*j + 12*k
        >>> q1 + 5
        6 + 2*i + 3*j + 4*k
        >>> x = symbols('x', real = True)
        >>> q1.add(x)
        (x + 1) + 2*i + 3*j + 4*k

        Quaternions over complex fields :

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import I
        >>> q3 = Quaternion(3 + 4*I, 2 + 5*I, 0, 7 + 8*I, real_field = False)
        >>> q3.add(2 + 3*I)
        (5 + 7*I) + (2 + 5*I)*i + 0*j + (7 + 8*I)*k
        """
        q1 = self
        q2 = sympify(other)

        # If q2 is a number or a sympy expression instead of a quaternion
        if not isinstance(q2, Quaternion):
            if q1.real_field:
                if q2.is_complex:
                    return Quaternion(re(q2) + q1.a, im(q2) + q1.b, q1.c, q1.d)
                else:
                    # q2 is something strange, do not evaluate:
                    return Add(q1, q2)
            else:
                return Quaternion(q1.a + q2, q1.b, q1.c, q1.d)

        return Quaternion(q1.a + q2.a, q1.b + q2.b, q1.c + q2.c, q1.d
                          + q2.d)

    def mul(self, other):
        """Multiplies quaternions.

        Parameters
        ==========

        other : Quaternion or symbol
            The quaternion to multiply to current (self) quaternion.

        Returns
        =======

        Quaternion
            The resultant quaternion after multiplying self with other

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import symbols
        >>> q1 = Quaternion(1, 2, 3, 4)
        >>> q2 = Quaternion(5, 6, 7, 8)
        >>> q1.mul(q2)
        (-60) + 12*i + 30*j + 24*k
        >>> q1.mul(2)
        2 + 4*i + 6*j + 8*k
        >>> x = symbols('x', real = True)
        >>> q1.mul(x)
        x + 2*x*i + 3*x*j + 4*x*k

        Quaternions over complex fields :

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import I
        >>> q3 = Quaternion(3 + 4*I, 2 + 5*I, 0, 7 + 8*I, real_field = False)
        >>> q3.mul(2 + 3*I)
        (2 + 3*I)*(3 + 4*I) + (2 + 3*I)*(2 + 5*I)*i + 0*j + (2 + 3*I)*(7 + 8*I)*k
        """
        return self._generic_mul(self, other)

    @staticmethod
    def _generic_mul(q1, q2):
        """Generic multiplication.

        Parameters
        ==========

        q1 : Quaternion or symbol
        q2 : Quaternion or symbol

        It's important to note that if neither q1 nor q2 is a Quaternion,
        this function simply returns q1 * q2.

        Returns
        =======

        Quaternion
            The resultant quaternion after multiplying q1 and q2

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import symbols
        >>> q1 = Quaternion(1, 2, 3, 4)
        >>> q2 = Quaternion(5, 6, 7, 8)
        >>> Quaternion._generic_mul(q1, q2)
        (-60) + 12*i + 30*j + 24*k
        >>> Quaternion._generic_mul(q1, 2)
        2 + 4*i + 6*j + 8*k
        >>> x = symbols('x', real = True)
        >>> Quaternion._generic_mul(q1, x)
        x + 2*x*i + 3*x*j + 4*x*k

        Quaternions over complex fields :

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import I
        >>> q3 = Quaternion(3 + 4*I, 2 + 5*I, 0, 7 + 8*I, real_field = False)
        >>> Quaternion._generic_mul(q3, 2 + 3*I)
        (2 + 3*I)*(3 + 4*I) + (2 + 3*I)*(2 + 5*I)*i + 0*j + (2 + 3*I)*(7 + 8*I)*k
        """
        q1 = sympify(q1)
        q2 = sympify(q2)

        # None is a Quaternion:
        if not isinstance(q1, Quaternion) and not isinstance(q2, Quaternion):
            return q1 * q2

        # If q1 is a number or a sympy expression instead of a quaternion
        if not isinstance(q1, Quaternion):
            if q2.real_field:
                if q1.is_complex:
                    return q2 * Quaternion(re(q1), im(q1), 0, 0)
                else:
                    return Mul(q1, q2)
            else:
                return Quaternion(q1 * q2.a, q1 * q2.b, q1 * q2.c, q1 * q2.d)


        # If q2 is a number or a sympy expression instead of a quaternion
        if not isinstance(q2, Quaternion):
            if q1.real_field:
                if q2.is_complex:
                    return q1 * Quaternion(re(q2), im(q2), 0, 0)
                else:
                    return Mul(q1, q2)
            else:
                return Quaternion(q2 * q1.a, q2 * q1.b, q2 * q1.c, q2 * q1.d)

        return Quaternion(-q1.b*q2.b - q1.c*q2.c - q1.d*q2.d + q1.a*q2.a,
                          q1.b*q2.a + q1.c*q2.d - q1.d*q2.c + q1.a*q2.b,
                          -q1.b*q2.d + q1.c*q2.a + q1.d*q2.b + q1.a*q2.c,
                          q1.b*q2.c - q1.c*q2.b + q1.d*q2.a + q1.a * q2.d)

    def _eval_conjugate(self):
        """Returns the conjugate of the quaternion."""
        q = self
        return Quaternion(q.a, -q.b, -q.c, -q.d)

    def norm(self):
        """Returns the norm of the quaternion."""
        q = self
        # trigsimp is used to simplify sin(x)^2 + cos(x)^2 (these terms
        # arise when from_axis_angle is used).
        return sqrt(trigsimp(q.a**2 + q.b**2 + q.c**2 + q.d**2))

    def normalize(self):
        """Returns the normalized form of the quaternion."""
        q = self
        return q * (1/q.norm())

    def inverse(self):
        """Returns the inverse of the quaternion."""
        q = self
        if not q.norm():
            raise ValueError("Cannot compute inverse for a quaternion with zero norm")
        return conjugate(q) * (1/q.norm()**2)

    def pow(self, p):
        """Finds the pth power of the quaternion.

        Parameters
        ==========

        p : int
            Power to be applied on quaternion.

        Returns
        =======

        Quaternion
            Returns the p-th power of the current quaternion.
            Returns the inverse if p = -1.

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> q = Quaternion(1, 2, 3, 4)
        >>> q.pow(4)
        668 + (-224)*i + (-336)*j + (-448)*k
        """
        q = self
        if p == -1:
            return q.inverse()
        res = 1

        if p < 0:
            q, p = q.inverse(), -p

        if not (isinstance(p, (Integer, SYMPY_INTS))):
            return NotImplemented

        while p > 0:
            if p & 1:
                res = q * res

            p = p >> 1
            q = q * q

        return res

    def exp(self):
        """Returns the exponential of q (e^q).

        Returns
        =======

        Quaternion
            Exponential of q (e^q).

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> q = Quaternion(1, 2, 3, 4)
        >>> q.exp()
        E*cos(sqrt(29))
        + 2*sqrt(29)*E*sin(sqrt(29))/29*i
        + 3*sqrt(29)*E*sin(sqrt(29))/29*j
        + 4*sqrt(29)*E*sin(sqrt(29))/29*k
        """
        # exp(q) = e^a(cos||v|| + v/||v||*sin||v||)
        q = self
        vector_norm = sqrt(q.b**2 + q.c**2 + q.d**2)
        a = exp(q.a) * cos(vector_norm)
        b = exp(q.a) * sin(vector_norm) * q.b / vector_norm
        c = exp(q.a) * sin(vector_norm) * q.c / vector_norm
        d = exp(q.a) * sin(vector_norm) * q.d / vector_norm

        return Quaternion(a, b, c, d)

    def _ln(self):
        """Returns the natural logarithm of the quaternion (_ln(q)).

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> q = Quaternion(1, 2, 3, 4)
        >>> q._ln()
        log(sqrt(30))
        + 2*sqrt(29)*acos(sqrt(30)/30)/29*i
        + 3*sqrt(29)*acos(sqrt(30)/30)/29*j
        + 4*sqrt(29)*acos(sqrt(30)/30)/29*k
        """
        # _ln(q) = _ln||q|| + v/||v||*arccos(a/||q||)
        q = self
        vector_norm = sqrt(q.b**2 + q.c**2 + q.d**2)
        q_norm = q.norm()
        a = ln(q_norm)
        b = q.b * acos(q.a / q_norm) / vector_norm
        c = q.c * acos(q.a / q_norm) / vector_norm
        d = q.d * acos(q.a / q_norm) / vector_norm

        return Quaternion(a, b, c, d)

    def pow_cos_sin(self, p):
        """Computes the pth power in the cos-sin form.

        Parameters
        ==========

        p : int
            Power to be applied on quaternion.

        Returns
        =======

        Quaternion
            The p-th power in the cos-sin form.

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> q = Quaternion(1, 2, 3, 4)
        >>> q.pow_cos_sin(4)
        900*cos(4*acos(sqrt(30)/30))
        + 1800*sqrt(29)*sin(4*acos(sqrt(30)/30))/29*i
        + 2700*sqrt(29)*sin(4*acos(sqrt(30)/30))/29*j
        + 3600*sqrt(29)*sin(4*acos(sqrt(30)/30))/29*k
        """
        # q = ||q||*(cos(a) + u*sin(a))
        # q^p = ||q||^p * (cos(p*a) + u*sin(p*a))

        q = self
        (v, angle) = q.to_axis_angle()
        q2 = Quaternion.from_axis_angle(v, p * angle)
        return q2 * (q.norm()**p)

    def integrate(self, *args):
        # TODO: is this expression correct?
        return Quaternion(integrate(self.a, *args), integrate(self.b, *args),
                          integrate(self.c, *args), integrate(self.d, *args))

    @staticmethod
    def rotate_point(pin, r):
        """Returns the coordinates of the point pin(a 3 tuple) after rotation.

        Parameters
        ==========

        pin : tuple
            A 3-element tuple of coordinates of a point. This point will be
            the axis of rotation.
        r
            Angle to be rotated.

        Returns
        =======

        tuple
            The coordinates of the quaternion after rotation.

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import symbols, trigsimp, cos, sin
        >>> x = symbols('x')
        >>> q = Quaternion(cos(x/2), 0, 0, sin(x/2))
        >>> trigsimp(Quaternion.rotate_point((1, 1, 1), q))
        (sqrt(2)*cos(x + pi/4), sqrt(2)*sin(x + pi/4), 1)
        >>> (axis, angle) = q.to_axis_angle()
        >>> trigsimp(Quaternion.rotate_point((1, 1, 1), (axis, angle)))
        (sqrt(2)*cos(x + pi/4), sqrt(2)*sin(x + pi/4), 1)
        """
        if isinstance(r, tuple):
            # if r is of the form (vector, angle)
            q = Quaternion.from_axis_angle(r[0], r[1])
        else:
            # if r is a quaternion
            q = r.normalize()
        pout = q * Quaternion(0, pin[0], pin[1], pin[2]) * conjugate(q)
        return (pout.b, pout.c, pout.d)

    def to_axis_angle(self):
        """Returns the axis and angle of rotation of a quaternion

        Returns
        =======

        tuple
            Tuple of (axis, angle)

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> q = Quaternion(1, 1, 1, 1)
        >>> (axis, angle) = q.to_axis_angle()
        >>> axis
        (sqrt(3)/3, sqrt(3)/3, sqrt(3)/3)
        >>> angle
        2*pi/3
        """
        q = self
        try:
            # Skips it if it doesn't know whether q.a is negative
            if q.a < 0:
                # avoid error with acos
                # axis and angle of rotation of q and q*-1 will be the same
                q = q * -1
        except BaseException:
            pass

        q = q.normalize()
        angle = trigsimp(2 * acos(q.a))

        # Since quaternion is normalised, q.a is less than 1.
        s = sqrt(1 - q.a*q.a)

        x = trigsimp(q.b / s)
        y = trigsimp(q.c / s)
        z = trigsimp(q.d / s)

        v = (x, y, z)
        t = (v, angle)

        return t

    def to_rotation_matrix(self, v=None):
        """Returns the equivalent rotation transformation matrix of the quaternion
        which represents rotation about the origin if v is not passed.

        Parameters
        ==========

        v : tuple or None
            Default value: None

        Returns
        =======

        tuple
            Returns the equivalent rotation transformation matrix of the quaternion
            which represents rotation about the origin if v is not passed.

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import symbols, trigsimp, cos, sin
        >>> x = symbols('x')
        >>> q = Quaternion(cos(x/2), 0, 0, sin(x/2))
        >>> trigsimp(q.to_rotation_matrix())
        Matrix([
        [cos(x), -sin(x), 0],
        [sin(x),  cos(x), 0],
        [     0,       0, 1]])

        Generates a 4x4 transformation matrix (used for rotation about a point
        other than the origin) if the point(v) is passed as an argument.

        Examples
        ========

        >>> from sympy.algebras.quaternion import Quaternion
        >>> from sympy import symbols, trigsimp, cos, sin
        >>> x = symbols('x')
        >>> q = Quaternion(cos(x/2), 0, 0, sin(x/2))
        >>> trigsimp(q.to_rotation_matrix((1, 1, 1)))
         Matrix([
        [cos(x), -sin(x), 0,  sin(x) - cos(x) + 1],
        [sin(x),  cos(x), 0, -sin(x) - cos(x) + 1],
        [     0,       0, 1,                    0],
        [     0,       0, 0,                    1]])
        """

        q = self
        s = q.norm()**-2
        m00 = 1 - 2*s*(q.c**2 + q.d**2)
        m01 = 2*s*(q.b*q.c - q.d*q.a)
        m02 = 2*s*(q.b*q.d + q.c*q.a)

        m10 = 2*s*(q.b*q.c + q.d*q.a)
        m11 = 1 - 2*s*(q.b**2 + q.d**2)
        m12 = 2*s*(q.c*q.d - q.b*q.a)

        m20 = 2*s*(q.b*q.d - q.c*q.a)
        m21 = 2*s*(q.c*q.d + q.b*q.a)
        m22 = 1 - 2*s*(q.b**2 + q.c**2)

        if not v:
            return Matrix([[m00, m01, m02], [m10, m11, m12], [m20, m21, m22]])

        else:
            (x, y, z) = v

            m03 = x - x*m00 - y*m01 - z*m02
            m13 = y - x*m10 - y*m11 - z*m12
            m23 = z - x*m20 - y*m21 - z*m22
            m30 = m31 = m32 = 0
            m33 = 1

            return Matrix([[m00, m01, m02, m03], [m10, m11, m12, m13],
                          [m20, m21, m22, m23], [m30, m31, m32, m33]])
