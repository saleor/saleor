from __future__ import print_function, division

from sympy import Basic
from sympy.core.expr import Expr
from sympy.core.numbers import Integer
from sympy.core.sympify import sympify
from sympy.core.compatibility import SYMPY_INTS, Iterable

import itertools

class NDimArray(object):
    """

    Examples
    ========

    Create an N-dim array of zeros:

    >>> from sympy import MutableDenseNDimArray
    >>> a = MutableDenseNDimArray.zeros(2, 3, 4)
    >>> a
    [[[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]], [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]]

    Create an N-dim array from a list;

    >>> a = MutableDenseNDimArray([[2, 3], [4, 5]])
    >>> a
    [[2, 3], [4, 5]]

    >>> b = MutableDenseNDimArray([[[1, 2], [3, 4], [5, 6]], [[7, 8], [9, 10], [11, 12]]])
    >>> b
    [[[1, 2], [3, 4], [5, 6]], [[7, 8], [9, 10], [11, 12]]]

    Create an N-dim array from a flat list with dimension shape:

    >>> a = MutableDenseNDimArray([1, 2, 3, 4, 5, 6], (2, 3))
    >>> a
    [[1, 2, 3], [4, 5, 6]]

    Create an N-dim array from a matrix:

    >>> from sympy import Matrix
    >>> a = Matrix([[1,2],[3,4]])
    >>> a
    Matrix([
    [1, 2],
    [3, 4]])
    >>> b = MutableDenseNDimArray(a)
    >>> b
    [[1, 2], [3, 4]]

    Arithmetic operations on N-dim arrays

    >>> a = MutableDenseNDimArray([1, 1, 1, 1], (2, 2))
    >>> b = MutableDenseNDimArray([4, 4, 4, 4], (2, 2))
    >>> c = a + b
    >>> c
    [[5, 5], [5, 5]]
    >>> a - b
    [[-3, -3], [-3, -3]]

    """

    _diff_wrt = True

    def __new__(cls, iterable, shape=None, **kwargs):
        from sympy.tensor.array import ImmutableDenseNDimArray
        return ImmutableDenseNDimArray(iterable, shape, **kwargs)

    def _parse_index(self, index):

        if isinstance(index, (SYMPY_INTS, Integer)):
            if index >= self._loop_size:
                raise ValueError("index out of range")
            return index

        if len(index) != self._rank:
            raise ValueError('Wrong number of array axes')

        real_index = 0
        # check if input index can exist in current indexing
        for i in range(self._rank):
            if index[i] >= self.shape[i]:
                raise ValueError('Index ' + str(index) + ' out of border')
            real_index = real_index*self.shape[i] + index[i]

        return real_index

    def _get_tuple_index(self, integer_index):
        index = []
        for i, sh in enumerate(reversed(self.shape)):
            index.append(integer_index % sh)
            integer_index //= sh
        index.reverse()
        return tuple(index)

    def _check_symbolic_index(self, index):
        # Check if any index is symbolic:
        tuple_index = (index if isinstance(index, tuple) else (index,))
        if any([(isinstance(i, Expr) and (not i.is_number)) for i in tuple_index]):
            for i, nth_dim in zip(tuple_index, self.shape):
                if ((i < 0) == True) or ((i >= nth_dim) == True):
                    raise ValueError("index out of range")
            from sympy.tensor import Indexed
            return Indexed(self, *tuple_index)
        return None

    def _setter_iterable_check(self, value):
        from sympy.matrices.matrices import MatrixBase
        if isinstance(value, (Iterable, MatrixBase, NDimArray)):
            raise NotImplementedError

    @classmethod
    def _scan_iterable_shape(cls, iterable):
        def f(pointer):
            if not isinstance(pointer, Iterable):
                return [pointer], ()

            result = []
            elems, shapes = zip(*[f(i) for i in pointer])
            if len(set(shapes)) != 1:
                raise ValueError("could not determine shape unambiguously")
            for i in elems:
                result.extend(i)
            return result, (len(shapes),)+shapes[0]

        return f(iterable)

    @classmethod
    def _handle_ndarray_creation_inputs(cls, iterable=None, shape=None, **kwargs):
        from sympy.matrices.matrices import MatrixBase

        if shape is None and iterable is None:
            shape = ()
            iterable = ()
        # Construction from another `NDimArray`:
        elif shape is None and isinstance(iterable, NDimArray):
            shape = iterable.shape
            iterable = list(iterable)
        # Construct N-dim array from an iterable (numpy arrays included):
        elif shape is None and isinstance(iterable, Iterable):
            iterable, shape = cls._scan_iterable_shape(iterable)

        # Construct N-dim array from a Matrix:
        elif shape is None and isinstance(iterable, MatrixBase):
            shape = iterable.shape

        # Construct N-dim array from another N-dim array:
        elif shape is None and isinstance(iterable, NDimArray):
            shape = iterable.shape

        # Construct NDimArray(iterable, shape)
        elif shape is not None:
            pass

        else:
            shape = ()
            iterable = (iterable,)

        if isinstance(shape, (SYMPY_INTS, Integer)):
            shape = (shape,)

        if any([not isinstance(dim, (SYMPY_INTS, Integer)) for dim in shape]):
            raise TypeError("Shape should contain integers only.")

        return tuple(shape), iterable

    def __len__(self):
        """Overload common function len(). Returns number of elements in array.

        Examples
        ========

        >>> from sympy import MutableDenseNDimArray
        >>> a = MutableDenseNDimArray.zeros(3, 3)
        >>> a
        [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        >>> len(a)
        9

        """
        return self._loop_size

    @property
    def shape(self):
        """
        Returns array shape (dimension).

        Examples
        ========

        >>> from sympy import MutableDenseNDimArray
        >>> a = MutableDenseNDimArray.zeros(3, 3)
        >>> a.shape
        (3, 3)

        """
        return self._shape

    def rank(self):
        """
        Returns rank of array.

        Examples
        ========

        >>> from sympy import MutableDenseNDimArray
        >>> a = MutableDenseNDimArray.zeros(3,4,5,6,3)
        >>> a.rank()
        5

        """
        return self._rank

    def diff(self, *args, **kwargs):
        """
        Calculate the derivative of each element in the array.

        Examples
        ========

        >>> from sympy import ImmutableDenseNDimArray
        >>> from sympy.abc import x, y
        >>> M = ImmutableDenseNDimArray([[x, y], [1, x*y]])
        >>> M.diff(x)
        [[1, 0], [0, y]]

        """
        from sympy import Derivative
        kwargs.setdefault('evaluate', True)
        return Derivative(self.as_immutable(), *args, **kwargs)

    def _accept_eval_derivative(self, s):
        return s._visit_eval_derivative_array(self)

    def _visit_eval_derivative_scalar(self, base):
        # Types are (base: scalar, self: array)
        return self.applyfunc(lambda x: base.diff(x))

    def _visit_eval_derivative_array(self, base):
        # Types are (base: array/matrix, self: array)
        from sympy import derive_by_array
        return derive_by_array(base, self)

    def _eval_derivative_n_times(self, s, n):
        return Basic._eval_derivative_n_times(self, s, n)

    def _eval_derivative(self, arg):
        from sympy import derive_by_array
        from sympy import Tuple
        from sympy.matrices.common import MatrixCommon
        if isinstance(arg, (Iterable, Tuple, MatrixCommon, NDimArray)):
            return derive_by_array(self, arg)
        else:
            return self.applyfunc(lambda x: x.diff(arg))

    def applyfunc(self, f):
        """Apply a function to each element of the N-dim array.

        Examples
        ========

        >>> from sympy import ImmutableDenseNDimArray
        >>> m = ImmutableDenseNDimArray([i*2+j for i in range(2) for j in range(2)], (2, 2))
        >>> m
        [[0, 1], [2, 3]]
        >>> m.applyfunc(lambda i: 2*i)
        [[0, 2], [4, 6]]
        """
        return type(self)(map(f, self), self.shape)

    def __str__(self):
        """Returns string, allows to use standard functions print() and str().

        Examples
        ========

        >>> from sympy import MutableDenseNDimArray
        >>> a = MutableDenseNDimArray.zeros(2, 2)
        >>> a
        [[0, 0], [0, 0]]

        """
        def f(sh, shape_left, i, j):
            if len(shape_left) == 1:
                return "["+", ".join([str(self[e]) for e in range(i, j)])+"]"

            sh //= shape_left[0]
            return "[" + ", ".join([f(sh, shape_left[1:], i+e*sh, i+(e+1)*sh) for e in range(shape_left[0])]) + "]" # + "\n"*len(shape_left)

        if self.rank() == 0:
            return self[()].__str__()

        return f(self._loop_size, self.shape, 0, self._loop_size)

    def __repr__(self):
        return self.__str__()

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

    def tolist(self):
        """
        Converting MutableDenseNDimArray to one-dim list

        Examples
        ========

        >>> from sympy import MutableDenseNDimArray
        >>> a = MutableDenseNDimArray([1, 2, 3, 4], (2, 2))
        >>> a
        [[1, 2], [3, 4]]
        >>> b = a.tolist()
        >>> b
        [[1, 2], [3, 4]]
        """

        def f(sh, shape_left, i, j):
            if len(shape_left) == 1:
                return [self[e] for e in range(i, j)]
            result = []
            sh //= shape_left[0]
            for e in range(shape_left[0]):
                result.append(f(sh, shape_left[1:], i+e*sh, i+(e+1)*sh))
            return result

        return f(self._loop_size, self.shape, 0, self._loop_size)

    def __add__(self, other):
        if not isinstance(other, NDimArray):
            raise TypeError(str(other))

        if self.shape != other.shape:
            raise ValueError("array shape mismatch")
        result_list = [i+j for i,j in zip(self, other)]

        return type(self)(result_list, self.shape)

    def __sub__(self, other):
        if not isinstance(other, NDimArray):
            raise TypeError(str(other))

        if self.shape != other.shape:
            raise ValueError("array shape mismatch")
        result_list = [i-j for i,j in zip(self, other)]

        return type(self)(result_list, self.shape)

    def __mul__(self, other):
        from sympy.matrices.matrices import MatrixBase

        if isinstance(other, (Iterable, NDimArray, MatrixBase)):
            raise ValueError("scalar expected, use tensorproduct(...) for tensorial product")
        other = sympify(other)
        result_list = [i*other for i in self]
        return type(self)(result_list, self.shape)

    def __rmul__(self, other):
        from sympy.matrices.matrices import MatrixBase

        if isinstance(other, (Iterable, NDimArray, MatrixBase)):
            raise ValueError("scalar expected, use tensorproduct(...) for tensorial product")
        other = sympify(other)
        result_list = [other*i for i in self]
        return type(self)(result_list, self.shape)

    def __div__(self, other):
        from sympy.matrices.matrices import MatrixBase

        if isinstance(other, (Iterable, NDimArray, MatrixBase)):
            raise ValueError("scalar expected")
        other = sympify(other)
        result_list = [i/other for i in self]
        return type(self)(result_list, self.shape)

    def __rdiv__(self, other):
        raise NotImplementedError('unsupported operation on NDimArray')

    def __neg__(self):
        result_list = [-i for i in self]
        return type(self)(result_list, self.shape)

    def __eq__(self, other):
        """
        NDimArray instances can be compared to each other.
        Instances equal if they have same shape and data.

        Examples
        ========

        >>> from sympy import MutableDenseNDimArray
        >>> a = MutableDenseNDimArray.zeros(2, 3)
        >>> b = MutableDenseNDimArray.zeros(2, 3)
        >>> a == b
        True
        >>> c = a.reshape(3, 2)
        >>> c == b
        False
        >>> a[0,0] = 1
        >>> b[0,0] = 2
        >>> a == b
        False
        """
        if not isinstance(other, NDimArray):
            return False
        return (self.shape == other.shape) and (list(self) == list(other))

    def __ne__(self, other):
        return not self == other

    __truediv__ = __div__
    __rtruediv__ = __rdiv__

    def _eval_transpose(self):
        if self.rank() != 2:
            raise ValueError("array rank not 2")
        from .arrayop import permutedims
        return permutedims(self, (1, 0))

    def transpose(self):
        return self._eval_transpose()

    def _eval_conjugate(self):
        return self.func([i.conjugate() for i in self], self.shape)

    def conjugate(self):
        return self._eval_conjugate()

    def _eval_adjoint(self):
        return self.transpose().conjugate()

    def adjoint(self):
        return self._eval_adjoint()

    def _slice_expand(self, s, dim):
        if not isinstance(s, slice):
                return (s,)
        start, stop, step = s.indices(dim)
        return [start + i*step for i in range((stop-start)//step)]

    def _get_slice_data_for_array_access(self, index):
        sl_factors = [self._slice_expand(i, dim) for (i, dim) in zip(index, self.shape)]
        eindices = itertools.product(*sl_factors)
        return sl_factors, eindices

    def _get_slice_data_for_array_assignment(self, index, value):
        if not isinstance(value, NDimArray):
            value = type(self)(value)
        sl_factors, eindices = self._get_slice_data_for_array_access(index)
        slice_offsets = [min(i) if isinstance(i, list) else None for i in sl_factors]
        # TODO: add checks for dimensions for `value`?
        return value, eindices, slice_offsets

    @classmethod
    def _check_special_bounds(cls, flat_list, shape):
        if shape == () and len(flat_list) != 1:
            raise ValueError("arrays without shape need one scalar value")
        if shape == (0,) and len(flat_list) > 0:
            raise ValueError("if array shape is (0,) there cannot be elements")


class ImmutableNDimArray(NDimArray, Basic):
    _op_priority = 11.0

    def __hash__(self):
        return Basic.__hash__(self)

    def as_immutable(self):
        return self

    def as_mutable(self):
        raise NotImplementedError("abstract method")
