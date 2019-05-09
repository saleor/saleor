from sympy.core.backend import sympify, Add, ImmutableMatrix as Matrix
from sympy.core.compatibility import unicode
from .printing import (VectorLatexPrinter, VectorPrettyPrinter,
                       VectorStrPrinter)

__all__ = ['Dyadic']


class Dyadic(object):
    """A Dyadic object.

    See:
    https://en.wikipedia.org/wiki/Dyadic_tensor
    Kane, T., Levinson, D. Dynamics Theory and Applications. 1985 McGraw-Hill

    A more powerful way to represent a rigid body's inertia. While it is more
    complex, by choosing Dyadic components to be in body fixed basis vectors,
    the resulting matrix is equivalent to the inertia tensor.

    """

    def __init__(self, inlist):
        """
        Just like Vector's init, you shouldn't call this unless creating a
        zero dyadic.

        zd = Dyadic(0)

        Stores a Dyadic as a list of lists; the inner list has the measure
        number and the two unit vectors; the outerlist holds each unique
        unit vector pair.

        """

        self.args = []
        if inlist == 0:
            inlist = []
        while len(inlist) != 0:
            added = 0
            for i, v in enumerate(self.args):
                if ((str(inlist[0][1]) == str(self.args[i][1])) and
                        (str(inlist[0][2]) == str(self.args[i][2]))):
                    self.args[i] = (self.args[i][0] + inlist[0][0],
                                    inlist[0][1], inlist[0][2])
                    inlist.remove(inlist[0])
                    added = 1
                    break
            if added != 1:
                self.args.append(inlist[0])
                inlist.remove(inlist[0])
        i = 0
        # This code is to remove empty parts from the list
        while i < len(self.args):
            if ((self.args[i][0] == 0) | (self.args[i][1] == 0) |
                    (self.args[i][2] == 0)):
                self.args.remove(self.args[i])
                i -= 1
            i += 1

    def __add__(self, other):
        """The add operator for Dyadic. """
        other = _check_dyadic(other)
        return Dyadic(self.args + other.args)

    def __and__(self, other):
        """The inner product operator for a Dyadic and a Dyadic or Vector.

        Parameters
        ==========

        other : Dyadic or Vector
            The other Dyadic or Vector to take the inner product with

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, outer
        >>> N = ReferenceFrame('N')
        >>> D1 = outer(N.x, N.y)
        >>> D2 = outer(N.y, N.y)
        >>> D1.dot(D2)
        (N.x|N.y)
        >>> D1.dot(N.y)
        N.x

        """
        from sympy.physics.vector.vector import Vector, _check_vector
        if isinstance(other, Dyadic):
            other = _check_dyadic(other)
            ol = Dyadic(0)
            for i, v in enumerate(self.args):
                for i2, v2 in enumerate(other.args):
                    ol += v[0] * v2[0] * (v[2] & v2[1]) * (v[1] | v2[2])
        else:
            other = _check_vector(other)
            ol = Vector(0)
            for i, v in enumerate(self.args):
                ol += v[0] * v[1] * (v[2] & other)
        return ol

    def __div__(self, other):
        """Divides the Dyadic by a sympifyable expression. """
        return self.__mul__(1 / other)

    __truediv__ = __div__

    def __eq__(self, other):
        """Tests for equality.

        Is currently weak; needs stronger comparison testing

        """

        if other == 0:
            other = Dyadic(0)
        other = _check_dyadic(other)
        if (self.args == []) and (other.args == []):
            return True
        elif (self.args == []) or (other.args == []):
            return False
        return set(self.args) == set(other.args)

    def __mul__(self, other):
        """Multiplies the Dyadic by a sympifyable expression.

        Parameters
        ==========

        other : Sympafiable
            The scalar to multiply this Dyadic with

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, outer
        >>> N = ReferenceFrame('N')
        >>> d = outer(N.x, N.x)
        >>> 5 * d
        5*(N.x|N.x)

        """

        newlist = [v for v in self.args]
        for i, v in enumerate(newlist):
            newlist[i] = (sympify(other) * newlist[i][0], newlist[i][1],
                          newlist[i][2])
        return Dyadic(newlist)

    def __ne__(self, other):
        return not self == other

    def __neg__(self):
        return self * -1

    def _latex(self, printer=None):
        ar = self.args  # just to shorten things
        if len(ar) == 0:
            return str(0)
        ol = []  # output list, to be concatenated to a string
        mlp = VectorLatexPrinter()
        for i, v in enumerate(ar):
            # if the coef of the dyadic is 1, we skip the 1
            if ar[i][0] == 1:
                ol.append(' + ' + mlp.doprint(ar[i][1]) + r"\otimes " +
                          mlp.doprint(ar[i][2]))
            # if the coef of the dyadic is -1, we skip the 1
            elif ar[i][0] == -1:
                ol.append(' - ' +
                          mlp.doprint(ar[i][1]) +
                          r"\otimes " +
                          mlp.doprint(ar[i][2]))
            # If the coefficient of the dyadic is not 1 or -1,
            # we might wrap it in parentheses, for readability.
            elif ar[i][0] != 0:
                arg_str = mlp.doprint(ar[i][0])
                if isinstance(ar[i][0], Add):
                    arg_str = '(%s)' % arg_str
                if arg_str.startswith('-'):
                    arg_str = arg_str[1:]
                    str_start = ' - '
                else:
                    str_start = ' + '
                ol.append(str_start + arg_str + mlp.doprint(ar[i][1]) +
                          r"\otimes " + mlp.doprint(ar[i][2]))
        outstr = ''.join(ol)
        if outstr.startswith(' + '):
            outstr = outstr[3:]
        elif outstr.startswith(' '):
            outstr = outstr[1:]
        return outstr

    def _pretty(self, printer=None):
        e = self

        class Fake(object):
            baseline = 0

            def render(self, *args, **kwargs):
                ar = e.args  # just to shorten things
                settings = printer._settings if printer else {}
                if printer:
                    use_unicode = printer._use_unicode
                else:
                    from sympy.printing.pretty.pretty_symbology import (
                        pretty_use_unicode)
                    use_unicode = pretty_use_unicode()
                mpp = printer if printer else VectorPrettyPrinter(settings)
                if len(ar) == 0:
                    return unicode(0)
                bar = u"\N{CIRCLED TIMES}" if use_unicode else "|"
                ol = []  # output list, to be concatenated to a string
                for i, v in enumerate(ar):
                    # if the coef of the dyadic is 1, we skip the 1
                    if ar[i][0] == 1:
                        ol.extend([u" + ",
                                  mpp.doprint(ar[i][1]),
                                  bar,
                                  mpp.doprint(ar[i][2])])

                    # if the coef of the dyadic is -1, we skip the 1
                    elif ar[i][0] == -1:
                        ol.extend([u" - ",
                                  mpp.doprint(ar[i][1]),
                                  bar,
                                  mpp.doprint(ar[i][2])])

                    # If the coefficient of the dyadic is not 1 or -1,
                    # we might wrap it in parentheses, for readability.
                    elif ar[i][0] != 0:
                        if isinstance(ar[i][0], Add):
                            arg_str = mpp._print(
                                ar[i][0]).parens()[0]
                        else:
                            arg_str = mpp.doprint(ar[i][0])
                        if arg_str.startswith(u"-"):
                            arg_str = arg_str[1:]
                            str_start = u" - "
                        else:
                            str_start = u" + "
                        ol.extend([str_start, arg_str, u" ",
                                  mpp.doprint(ar[i][1]),
                                  bar,
                                  mpp.doprint(ar[i][2])])

                outstr = u"".join(ol)
                if outstr.startswith(u" + "):
                    outstr = outstr[3:]
                elif outstr.startswith(" "):
                    outstr = outstr[1:]
                return outstr
        return Fake()

    def __rand__(self, other):
        """The inner product operator for a Vector or Dyadic, and a Dyadic

        This is for: Vector dot Dyadic

        Parameters
        ==========

        other : Vector
            The vector we are dotting with

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, dot, outer
        >>> N = ReferenceFrame('N')
        >>> d = outer(N.x, N.x)
        >>> dot(N.x, d)
        N.x

        """

        from sympy.physics.vector.vector import Vector, _check_vector
        other = _check_vector(other)
        ol = Vector(0)
        for i, v in enumerate(self.args):
            ol += v[0] * v[2] * (v[1] & other)
        return ol

    def __rsub__(self, other):
        return (-1 * self) + other

    def __rxor__(self, other):
        """For a cross product in the form: Vector x Dyadic

        Parameters
        ==========

        other : Vector
            The Vector that we are crossing this Dyadic with

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, outer, cross
        >>> N = ReferenceFrame('N')
        >>> d = outer(N.x, N.x)
        >>> cross(N.y, d)
        - (N.z|N.x)

        """

        from sympy.physics.vector.vector import _check_vector
        other = _check_vector(other)
        ol = Dyadic(0)
        for i, v in enumerate(self.args):
            ol += v[0] * ((other ^ v[1]) | v[2])
        return ol

    def __str__(self, printer=None):
        """Printing method. """
        ar = self.args  # just to shorten things
        if len(ar) == 0:
            return str(0)
        ol = []  # output list, to be concatenated to a string
        for i, v in enumerate(ar):
            # if the coef of the dyadic is 1, we skip the 1
            if ar[i][0] == 1:
                ol.append(' + (' + str(ar[i][1]) + '|' + str(ar[i][2]) + ')')
            # if the coef of the dyadic is -1, we skip the 1
            elif ar[i][0] == -1:
                ol.append(' - (' + str(ar[i][1]) + '|' + str(ar[i][2]) + ')')
            # If the coefficient of the dyadic is not 1 or -1,
            # we might wrap it in parentheses, for readability.
            elif ar[i][0] != 0:
                arg_str = VectorStrPrinter().doprint(ar[i][0])
                if isinstance(ar[i][0], Add):
                    arg_str = "(%s)" % arg_str
                if arg_str[0] == '-':
                    arg_str = arg_str[1:]
                    str_start = ' - '
                else:
                    str_start = ' + '
                ol.append(str_start + arg_str + '*(' + str(ar[i][1]) +
                          '|' + str(ar[i][2]) + ')')
        outstr = ''.join(ol)
        if outstr.startswith(' + '):
            outstr = outstr[3:]
        elif outstr.startswith(' '):
            outstr = outstr[1:]
        return outstr

    def __sub__(self, other):
        """The subtraction operator. """
        return self.__add__(other * -1)

    def __xor__(self, other):
        """For a cross product in the form: Dyadic x Vector.

        Parameters
        ==========

        other : Vector
            The Vector that we are crossing this Dyadic with

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, outer, cross
        >>> N = ReferenceFrame('N')
        >>> d = outer(N.x, N.x)
        >>> cross(d, N.y)
        (N.x|N.z)

        """

        from sympy.physics.vector.vector import _check_vector
        other = _check_vector(other)
        ol = Dyadic(0)
        for i, v in enumerate(self.args):
            ol += v[0] * (v[1] | (v[2] ^ other))
        return ol

    # We don't define _repr_png_ here because it would add a large amount of
    # data to any notebook containing SymPy expressions, without adding
    # anything useful to the notebook. It can still enabled manually, e.g.,
    # for the qtconsole, with init_printing().
    def _repr_latex_(self):
        """
        IPython/Jupyter LaTeX printing

        To change the behavior of this (e.g., pass in some settings to LaTeX),
        use init_printing(). init_printing() will also enable LaTeX printing
        for built in numeric types like ints and container types that contain
        SymPy objects, like lists and dictionaries of expressions.
        """
        from sympy.printing.latex import latex
        s = latex(self, mode='plain')
        return "$\\displaystyle %s$" % s

    _repr_latex_orig = _repr_latex_

    _sympystr = __str__
    _sympyrepr = _sympystr
    __repr__ = __str__
    __radd__ = __add__
    __rmul__ = __mul__

    def express(self, frame1, frame2=None):
        """Expresses this Dyadic in alternate frame(s)

        The first frame is the list side expression, the second frame is the
        right side; if Dyadic is in form A.x|B.y, you can express it in two
        different frames. If no second frame is given, the Dyadic is
        expressed in only one frame.

        Calls the global express function

        Parameters
        ==========

        frame1 : ReferenceFrame
            The frame to express the left side of the Dyadic in
        frame2 : ReferenceFrame
            If provided, the frame to express the right side of the Dyadic in

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, outer, dynamicsymbols
        >>> N = ReferenceFrame('N')
        >>> q = dynamicsymbols('q')
        >>> B = N.orientnew('B', 'Axis', [q, N.z])
        >>> d = outer(N.x, N.x)
        >>> d.express(B, N)
        cos(q)*(B.x|N.x) - sin(q)*(B.y|N.x)

        """
        from sympy.physics.vector.functions import express
        return express(self, frame1, frame2)

    def to_matrix(self, reference_frame, second_reference_frame=None):
        """Returns the matrix form of the dyadic with respect to one or two
        reference frames.

        Parameters
        ----------
        reference_frame : ReferenceFrame
            The reference frame that the rows and columns of the matrix
            correspond to. If a second reference frame is provided, this
            only corresponds to the rows of the matrix.
        second_reference_frame : ReferenceFrame, optional, default=None
            The reference frame that the columns of the matrix correspond
            to.

        Returns
        -------
        matrix : ImmutableMatrix, shape(3,3)
            The matrix that gives the 2D tensor form.

        Examples
        ========

        >>> from sympy import symbols
        >>> from sympy.physics.vector import ReferenceFrame, Vector
        >>> Vector.simp = True
        >>> from sympy.physics.mechanics import inertia
        >>> Ixx, Iyy, Izz, Ixy, Iyz, Ixz = symbols('Ixx, Iyy, Izz, Ixy, Iyz, Ixz')
        >>> N = ReferenceFrame('N')
        >>> inertia_dyadic = inertia(N, Ixx, Iyy, Izz, Ixy, Iyz, Ixz)
        >>> inertia_dyadic.to_matrix(N)
        Matrix([
        [Ixx, Ixy, Ixz],
        [Ixy, Iyy, Iyz],
        [Ixz, Iyz, Izz]])
        >>> beta = symbols('beta')
        >>> A = N.orientnew('A', 'Axis', (beta, N.x))
        >>> inertia_dyadic.to_matrix(A)
        Matrix([
        [                           Ixx,                                           Ixy*cos(beta) + Ixz*sin(beta),                                           -Ixy*sin(beta) + Ixz*cos(beta)],
        [ Ixy*cos(beta) + Ixz*sin(beta), Iyy*cos(2*beta)/2 + Iyy/2 + Iyz*sin(2*beta) - Izz*cos(2*beta)/2 + Izz/2,                 -Iyy*sin(2*beta)/2 + Iyz*cos(2*beta) + Izz*sin(2*beta)/2],
        [-Ixy*sin(beta) + Ixz*cos(beta),                -Iyy*sin(2*beta)/2 + Iyz*cos(2*beta) + Izz*sin(2*beta)/2, -Iyy*cos(2*beta)/2 + Iyy/2 - Iyz*sin(2*beta) + Izz*cos(2*beta)/2 + Izz/2]])

        """

        if second_reference_frame is None:
            second_reference_frame = reference_frame

        return Matrix([i.dot(self).dot(j) for i in reference_frame for j in
                      second_reference_frame]).reshape(3, 3)

    def doit(self, **hints):
        """Calls .doit() on each term in the Dyadic"""
        return sum([Dyadic([(v[0].doit(**hints), v[1], v[2])])
                    for v in self.args], Dyadic(0))

    def dt(self, frame):
        """Take the time derivative of this Dyadic in a frame.

        This function calls the global time_derivative method

        Parameters
        ==========

        frame : ReferenceFrame
            The frame to take the time derivative in

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame, outer, dynamicsymbols
        >>> N = ReferenceFrame('N')
        >>> q = dynamicsymbols('q')
        >>> B = N.orientnew('B', 'Axis', [q, N.z])
        >>> d = outer(N.x, N.x)
        >>> d.dt(B)
        - q'*(N.y|N.x) - q'*(N.x|N.y)

        """
        from sympy.physics.vector.functions import time_derivative
        return time_derivative(self, frame)

    def simplify(self):
        """Returns a simplified Dyadic."""
        out = Dyadic(0)
        for v in self.args:
            out += Dyadic([(v[0].simplify(), v[1], v[2])])
        return out

    def subs(self, *args, **kwargs):
        """Substitution on the Dyadic.

        Examples
        ========

        >>> from sympy.physics.vector import ReferenceFrame
        >>> from sympy import Symbol
        >>> N = ReferenceFrame('N')
        >>> s = Symbol('s')
        >>> a = s*(N.x|N.x)
        >>> a.subs({s: 2})
        2*(N.x|N.x)

        """

        return sum([Dyadic([(v[0].subs(*args, **kwargs), v[1], v[2])])
                    for v in self.args], Dyadic(0))

    def applyfunc(self, f):
        """Apply a function to each component of a Dyadic."""
        if not callable(f):
            raise TypeError("`f` must be callable.")

        out = Dyadic(0)
        for a, b, c in self.args:
            out += f(a) * (b|c)
        return out

    dot = __and__
    cross = __xor__


def _check_dyadic(other):
    if not isinstance(other, Dyadic):
        raise TypeError('A Dyadic must be supplied')
    return other
