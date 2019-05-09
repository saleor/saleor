import itertools
from functools import reduce
from collections import defaultdict

from sympy import Indexed, IndexedBase, Tuple, Sum, Add, S, Integer
from sympy.combinatorics import Permutation
from sympy.core.basic import Basic
from sympy.core.compatibility import accumulate, default_sort_key
from sympy.core.mul import Mul
from sympy.core.sympify import _sympify
from sympy.functions.special.tensor_functions import KroneckerDelta
from sympy.matrices.expressions import (MatAdd, MatMul, Trace, Transpose,
        MatrixSymbol)
from sympy.matrices.expressions.matexpr import MatrixExpr, MatrixElement
from sympy.tensor.array import NDimArray


class _CodegenArrayAbstract(Basic):

    @property
    def subranks(self):
        """
        Returns the ranks of the objects in the uppermost tensor product inside
        the current object.  In case no tensor products are contained, return
        the atomic ranks.

        Examples
        ========

        >>> from sympy.codegen.array_utils import CodegenArrayTensorProduct, CodegenArrayContraction
        >>> from sympy import MatrixSymbol
        >>> M = MatrixSymbol("M", 3, 3)
        >>> N = MatrixSymbol("N", 3, 3)
        >>> P = MatrixSymbol("P", 3, 3)

        Important: do not confuse the rank of the matrix with the rank of an array.

        >>> tp = CodegenArrayTensorProduct(M, N, P)
        >>> tp.subranks
        [2, 2, 2]

        >>> co = CodegenArrayContraction(tp, (1, 2), (3, 4))
        >>> co.subranks
        [2, 2, 2]
        """
        return self._subranks[:]

    def subrank(self):
        """
        The sum of ``subranks``.
        """
        return sum(self.subranks)

    @property
    def shape(self):
        return self._shape


class CodegenArrayContraction(_CodegenArrayAbstract):
    r"""
    This class is meant to represent contractions of arrays in a form easily
    processable by the code printers.
    """
    def __new__(cls, expr, *contraction_indices, **kwargs):
        contraction_indices = _sort_contraction_indices(contraction_indices)
        expr = _sympify(expr)

        if len(contraction_indices) == 0:
            return expr

        if isinstance(expr, CodegenArrayContraction):
            return cls._flatten(expr, *contraction_indices)

        obj = Basic.__new__(cls, expr, *contraction_indices)
        obj._subranks = _get_subranks(expr)
        obj._mapping = _get_mapping_from_subranks(obj._subranks)

        free_indices_to_position = {i: i for i in range(sum(obj._subranks)) if all([i not in cind for cind in contraction_indices])}
        obj._free_indices_to_position = free_indices_to_position

        shape = expr.shape
        if shape:
            # Check that no contraction happens when the shape is mismatched:
            for i in contraction_indices:
                if len(set(shape[j] for j in i)) != 1:
                    raise ValueError("contracting indices of different dimensions")
            shape = tuple(shp for i, shp in enumerate(shape) if not any(i in j for j in contraction_indices))
        obj._shape = shape
        return obj

    @staticmethod
    def _get_free_indices_to_position_map(free_indices, contraction_indices):
        free_indices_to_position = {}
        flattened_contraction_indices = [j for i in contraction_indices for j in i]
        counter = 0
        for ind in free_indices:
            while counter in flattened_contraction_indices:
                counter += 1
            free_indices_to_position[ind] = counter
            counter += 1
        return free_indices_to_position

    @staticmethod
    def _get_index_shifts(expr):
        """
        Get the mapping of indices at the positions before the contraction
        occures.

        Examples
        ========

        >>> from sympy.codegen.array_utils import CodegenArrayContraction, CodegenArrayTensorProduct
        >>> from sympy import MatrixSymbol
        >>> M = MatrixSymbol("M", 3, 3)
        >>> N = MatrixSymbol("N", 3, 3)
        >>> cg = CodegenArrayContraction(CodegenArrayTensorProduct(M, N), [1, 2])
        >>> cg._get_index_shifts(cg)
        [0, 2]

        Indeed, ``cg`` after the contraction has two dimensions, 0 and 1. They
        need to be shifted by 0 and 2 to get the corresponding positions before
        the contraction (that is, 0 and 3).
        """
        inner_contraction_indices = expr.contraction_indices
        all_inner = [j for i in inner_contraction_indices for j in i]
        all_inner.sort()
        # TODO: add API for total rank and cumulative rank:
        total_rank = get_rank(expr)
        inner_rank = len(all_inner)
        outer_rank = total_rank - inner_rank
        shifts = [0 for i in range(outer_rank)]
        counter = 0
        pointer = 0
        for i in range(outer_rank):
            while pointer < inner_rank and counter >= all_inner[pointer]:
                counter += 1
                pointer += 1
            shifts[i] += pointer
            counter += 1
        return shifts

    @staticmethod
    def _convert_outer_indices_to_inner_indices(expr, *outer_contraction_indices):
        shifts = CodegenArrayContraction._get_index_shifts(expr)
        outer_contraction_indices = tuple(tuple(shifts[j] + j for j in i) for i in outer_contraction_indices)
        return outer_contraction_indices

    @staticmethod
    def _flatten(expr, *outer_contraction_indices):
        inner_contraction_indices = expr.contraction_indices
        outer_contraction_indices = CodegenArrayContraction._convert_outer_indices_to_inner_indices(expr, *outer_contraction_indices)
        contraction_indices = inner_contraction_indices + outer_contraction_indices
        return CodegenArrayContraction(expr.expr, *contraction_indices)

    def _get_contraction_tuples(self):
        r"""
        Return tuples containing the argument index and position within the
        argument of the index position.

        Examples
        ========

        >>> from sympy import MatrixSymbol, MatrixExpr, Sum, Symbol
        >>> from sympy.abc import i, j, k, l, N
        >>> from sympy.codegen.array_utils import CodegenArrayContraction, CodegenArrayTensorProduct
        >>> A = MatrixSymbol("A", N, N)
        >>> B = MatrixSymbol("B", N, N)

        >>> cg = CodegenArrayContraction(CodegenArrayTensorProduct(A, B), (1, 2))
        >>> cg._get_contraction_tuples()
        [[(0, 1), (1, 0)]]

        Here the contraction pair `(1, 2)` meaning that the 2nd and 3rd indices
        of the tensor product `A\otimes B` are contracted, has been transformed
        into `(0, 1)` and `(1, 0)`, identifying the same indices in a different
        notation. `(0, 1)` is the second index (1) of the first argument (i.e.
                0 or `A`). `(1, 0)` is the first index (i.e. 0) of the second
        argument (i.e. 1 or `B`).
        """
        mapping = self._mapping
        return [[mapping[j] for j in i] for i in self.contraction_indices]

    @staticmethod
    def _contraction_tuples_to_contraction_indices(expr, contraction_tuples):
        # TODO: check that `expr` has `.subranks`:
        ranks = expr.subranks
        cumulative_ranks = [0] + list(accumulate(ranks))
        return [tuple(cumulative_ranks[j]+k for j, k in i) for i in contraction_tuples]

    @property
    def free_indices(self):
        return self._free_indices[:]

    @property
    def free_indices_to_position(self):
        return dict(self._free_indices_to_position)

    @property
    def expr(self):
        return self.args[0]

    @property
    def contraction_indices(self):
        return self.args[1:]

    def _contraction_indices_to_components(self):
        expr = self.expr
        if not isinstance(expr, CodegenArrayTensorProduct):
            raise NotImplementedError("only for contractions of tensor products")
        ranks = expr.subranks
        mapping = {}
        counter = 0
        for i, rank in enumerate(ranks):
            for j in range(rank):
                mapping[counter] = (i, j)
                counter += 1
        return mapping

    def sort_args_by_name(self):
        """
        Sort arguments in the tensor product so that their order is lexicographical.

        Examples
        ========

        >>> from sympy import MatrixSymbol, MatrixExpr, Sum, Symbol
        >>> from sympy.abc import i, j, k, l, N
        >>> from sympy.codegen.array_utils import CodegenArrayContraction
        >>> A = MatrixSymbol("A", N, N)
        >>> B = MatrixSymbol("B", N, N)
        >>> C = MatrixSymbol("C", N, N)
        >>> D = MatrixSymbol("D", N, N)

        >>> cg = CodegenArrayContraction.from_MatMul(C*D*A*B)
        >>> cg
        CodegenArrayContraction(CodegenArrayTensorProduct(C, D, A, B), (1, 2), (3, 4), (5, 6))
        >>> cg.sort_args_by_name()
        CodegenArrayContraction(CodegenArrayTensorProduct(A, B, C, D), (0, 7), (1, 2), (5, 6))
        """
        expr = self.expr
        if not isinstance(expr, CodegenArrayTensorProduct):
            return self
        args = expr.args
        sorted_data = sorted(enumerate(args), key=lambda x: default_sort_key(x[1]))
        pos_sorted, args_sorted = zip(*sorted_data)
        reordering_map = {i: pos_sorted.index(i) for i, arg in enumerate(args)}
        contraction_tuples = self._get_contraction_tuples()
        contraction_tuples = [[(reordering_map[j], k) for j, k in i] for i in contraction_tuples]
        c_tp = CodegenArrayTensorProduct(*args_sorted)
        new_contr_indices = self._contraction_tuples_to_contraction_indices(
                c_tp,
                contraction_tuples
        )
        return CodegenArrayContraction(c_tp, *new_contr_indices)

    def _get_contraction_links(self):
        r"""
        Returns a dictionary of links between arguments in the tensor product
        being contracted.

        See the example for an explanation of the values.

        Examples
        ========

        >>> from sympy import MatrixSymbol, MatrixExpr, Sum, Symbol
        >>> from sympy.abc import i, j, k, l, N
        >>> from sympy.codegen.array_utils import CodegenArrayContraction
        >>> A = MatrixSymbol("A", N, N)
        >>> B = MatrixSymbol("B", N, N)
        >>> C = MatrixSymbol("C", N, N)
        >>> D = MatrixSymbol("D", N, N)

        Matrix multiplications are pairwise contractions between neighboring
        matrices:

        `A_{ij} B_{jk} C_{kl} D_{lm}`

        >>> cg = CodegenArrayContraction.from_MatMul(A*B*C*D)
        >>> cg
        CodegenArrayContraction(CodegenArrayTensorProduct(A, B, C, D), (1, 2), (3, 4), (5, 6))
        >>> cg._get_contraction_links()
        {0: {1: (1, 0)}, 1: {0: (0, 1), 1: (2, 0)}, 2: {0: (1, 1), 1: (3, 0)}, 3: {0: (2, 1)}}

        This dictionary is interpreted as follows: argument in position 0 (i.e.
        matrix `A`) has its second index (i.e. 1) contracted to `(1, 0)`, that
        is argument in position 1 (matrix `B`) on the first index slot of `B`,
        this is the contraction provided by the index `j` from `A`.

        The argument in position 1 (that is, matrix `B`) has two contractions,
        the ones provided by the indices `j` and `k`, respectively the first
        and second indices (0 and 1 in the sub-dict).  The link `(0, 1)` and
        `(2, 0)` respectively. `(0, 1)` is the index slot 1 (the 2nd) of
        argument in position 0 (that is, `A_{\ldot j}`), and so on.
        """
        return _get_contraction_links(self.subranks, *self.contraction_indices)

    @staticmethod
    def from_MatMul(expr):
        args_nonmat = []
        args = []
        contractions = []
        for arg in expr.args:
            if isinstance(arg, MatrixExpr):
                args.append(arg)
            else:
                args_nonmat.append(arg)
        contractions = [(2*i+1, 2*i+2) for i in range(len(args)-1)]
        return Mul.fromiter(args_nonmat)*CodegenArrayContraction(
                CodegenArrayTensorProduct(*args),
                *contractions
            )


def get_shape(expr):
    if hasattr(expr, "shape"):
        return expr.shape
    return ()


class CodegenArrayTensorProduct(_CodegenArrayAbstract):
    r"""
    Class to represent the tensor product of array-like objects.
    """
    def __new__(cls, *args):
        args = [_sympify(arg) for arg in args]
        args = cls._flatten(args)
        ranks = [get_rank(arg) for arg in args]

        if len(args) == 1:
            return args[0]

        # If there are contraction objects inside, transform the whole
        # expression into `CodegenArrayContraction`:
        contractions = {i: arg for i, arg in enumerate(args) if isinstance(arg, CodegenArrayContraction)}
        if contractions:
            cumulative_ranks = list(accumulate([0] + ranks))[:-1]
            tp = cls(*[arg.expr if isinstance(arg, CodegenArrayContraction) else arg for arg in args])
            contraction_indices = [tuple(cumulative_ranks[i] + k for k in j) for i, arg in contractions.items() for j in arg.contraction_indices]
            return CodegenArrayContraction(tp, *contraction_indices)

        #newargs = [i for i in args if hasattr(i, "shape")]
        #coeff = reduce(lambda x, y: x*y, [i for i in args if not hasattr(i, "shape")], S.One)
        #newargs[0] *= coeff

        obj = Basic.__new__(cls, *args)
        obj._subranks = ranks
        shapes = [get_shape(i) for i in args]

        if any(i is None for i in shapes):
            obj._shape = None
        else:
            obj._shape = tuple(j for i in shapes for j in i)
        return obj

    @classmethod
    def _flatten(cls, args):
        args = [i for arg in args for i in (arg.args if isinstance(arg, cls) else [arg])]
        return args


class CodegenArrayElementwiseAdd(_CodegenArrayAbstract):
    r"""
    Class for elementwise array additions.
    """
    def __new__(cls, *args):
        args = [_sympify(arg) for arg in args]
        obj = Basic.__new__(cls, *args)
        ranks = [get_rank(arg) for arg in args]
        ranks = list(set(ranks))
        if len(ranks) != 1:
            raise ValueError("summing arrays of different ranks")
        obj._subranks = ranks
        shapes = [arg.shape for arg in args]
        if len(set([i for i in shapes if i is not None])) > 1:
            raise ValueError("mismatching shapes in addition")
        if any(i is None for i in shapes):
            obj._shape = None
        else:
            obj._shape = shapes[0]
        return obj


class CodegenArrayPermuteDims(_CodegenArrayAbstract):
    r"""
    Class to represent permutation of axes of arrays.

    Examples
    ========

    >>> from sympy.codegen.array_utils import CodegenArrayPermuteDims
    >>> from sympy import MatrixSymbol
    >>> M = MatrixSymbol("M", 3, 3)
    >>> cg = CodegenArrayPermuteDims(M, [1, 0])

    The object ``cg`` represents the transposition of ``M``, as the permutation
    ``[1, 0]`` will act on its indices by switching them:

    `M_{ij} \Rightarrow M_{ji}`

    This is evident when transforming back to matrix form:

    >>> from sympy.codegen.array_utils import recognize_matrix_expression
    >>> recognize_matrix_expression(cg)
    M.T

    >>> N = MatrixSymbol("N", 3, 2)
    >>> cg = CodegenArrayPermuteDims(N, [1, 0])
    >>> cg.shape
    (2, 3)
    """
    def __new__(cls, expr, permutation):
        from sympy.combinatorics import Permutation
        expr = _sympify(expr)
        permutation = Permutation(permutation)
        plist = permutation.args[0]
        if plist == sorted(plist):
            return expr
        obj = Basic.__new__(cls, expr, permutation)
        obj._subranks = [get_rank(expr)]
        shape = expr.shape
        if shape is None:
            obj._shape = None
        else:
            obj._shape = tuple(shape[permutation(i)] for i in range(len(shape)))
        return obj

    @property
    def expr(self):
        return self.args[0]

    @property
    def permutation(self):
        return self.args[1]

    def nest_permutation(self):
        r"""
        Nest the permutation down the expression tree.

        Examples
        ========

        >>> from sympy.codegen.array_utils import (CodegenArrayPermuteDims, CodegenArrayTensorProduct, nest_permutation)
        >>> from sympy import MatrixSymbol
        >>> from sympy.combinatorics import Permutation
        >>> Permutation.print_cyclic = True

        >>> M = MatrixSymbol("M", 3, 3)
        >>> N = MatrixSymbol("N", 3, 3)
        >>> cg = CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), [1, 0, 3, 2])
        >>> cg
        CodegenArrayPermuteDims(CodegenArrayTensorProduct(M, N), (0 1)(2 3))
        >>> nest_permutation(cg)
        CodegenArrayTensorProduct(CodegenArrayPermuteDims(M, (0 1)), CodegenArrayPermuteDims(N, (0 1)))

        In ``cg`` both ``M`` and ``N`` are transposed. The cyclic
        representation of the permutation after the tensor product is
        `(0 1)(2 3)`. After nesting it down the expression tree, the usual
        transposition permutation `(0 1)` appears.
        """
        expr = self.expr
        if isinstance(expr, CodegenArrayTensorProduct):
            # Check if the permutation keeps the subranks separated:
            subranks = expr.subranks
            subrank = expr.subrank()
            l = list(range(subrank))
            p = [self.permutation(i) for i in l]
            dargs = {}
            counter = 0
            for i, arg in zip(subranks, expr.args):
                p0 = p[counter:counter+i]
                counter += i
                s0 = sorted(p0)
                if not all([s0[j+1]-s0[j] == 1 for j in range(len(s0)-1)]):
                    # Cross-argument permutations, impossible to nest the object:
                    return self
                subpermutation = [p0.index(j) for j in s0]
                dargs[s0[0]] = CodegenArrayPermuteDims(arg, subpermutation)
            # Read the arguments sorting the according to the keys of the dict:
            args = [dargs[i] for i in sorted(dargs)]
            return CodegenArrayTensorProduct(*args)
        elif isinstance(expr, CodegenArrayContraction):
            # Invert tree hierarchy: put the contraction above.
            cycles = self.permutation.cyclic_form
            newcycles = CodegenArrayContraction._convert_outer_indices_to_inner_indices(expr, *cycles)
            newpermutation = Permutation(newcycles)
            new_contr_indices = [tuple(newpermutation(j) for j in i) for i in expr.contraction_indices]
            return CodegenArrayContraction(CodegenArrayPermuteDims(expr.expr, newpermutation), *new_contr_indices)
        elif isinstance(expr, CodegenArrayElementwiseAdd):
            return CodegenArrayElementwiseAdd(*[CodegenArrayPermuteDims(arg, self.permutation) for arg in expr.args])

        return self


def nest_permutation(expr):
    if isinstance(expr, CodegenArrayPermuteDims):
        return expr.nest_permutation()
    else:
        return expr


class CodegenArrayDiagonal(_CodegenArrayAbstract):
    r"""
    Class to represent the diagonal operator.

    In a 2-dimensional array it returns the diagonal, this looks like the
    operation:

    `A_{ij} \rightarrow A_{ii}`

    The diagonal over axes 1 and 2 (the second and third) of the tensor product
    of two 2-dimensional arrays `A \otimes B` is

    `\Big[ A_{ab} B_{cd} \Big]_{abcd} \rightarrow \Big[ A_{ai} B_{id} \Big]_{adi}`

    In this last example the array expression has been reduced from
    4-dimensional to 3-dimensional. Notice that no contraction has occurred,
    rather there is a new index `i` for the diagonal, contraction would have
    reduced the array to 2 dimensions.

    Notice that the diagonalized out dimensions are added as new dimensions at
    the end of the indices.
    """
    def __new__(cls, expr, *diagonal_indices):
        expr = _sympify(expr)
        diagonal_indices = [Tuple(*sorted(i)) for i in diagonal_indices]
        if isinstance(expr, CodegenArrayDiagonal):
            return cls._flatten(expr, *diagonal_indices)
        obj = Basic.__new__(cls, expr, *diagonal_indices)
        obj._subranks = _get_subranks(expr)
        shape = expr.shape
        if shape is None:
            obj._shape = None
        else:
            # Check that no diagonalization happens on indices with mismatched
            # dimensions:
            for i in diagonal_indices:
                if len(set(shape[j] for j in i)) != 1:
                    raise ValueError("contracting indices of different dimensions")
            # Get new shape:
            shp1 = tuple(shp for i,shp in enumerate(shape) if not any(i in j for j in diagonal_indices))
            shp2 = tuple(shape[i[0]] for i in diagonal_indices)
            obj._shape = shp1 + shp2
        return obj

    @property
    def expr(self):
        return self.args[0]

    @property
    def diagonal_indices(self):
        return self.args[1:]

    @staticmethod
    def _flatten(expr, *outer_diagonal_indices):
        inner_diagonal_indices = expr.diagonal_indices
        all_inner = [j for i in inner_diagonal_indices for j in i]
        all_inner.sort()
        # TODO: add API for total rank and cumulative rank:
        total_rank = get_rank(expr)
        inner_rank = len(all_inner)
        outer_rank = total_rank - inner_rank
        shifts = [0 for i in range(outer_rank)]
        counter = 0
        pointer = 0
        for i in range(outer_rank):
            while pointer < inner_rank and counter >= all_inner[pointer]:
                counter += 1
                pointer += 1
            shifts[i] += pointer
            counter += 1
        outer_diagonal_indices = tuple(tuple(shifts[j] + j for j in i) for i in outer_diagonal_indices)
        diagonal_indices = inner_diagonal_indices + outer_diagonal_indices
        return CodegenArrayDiagonal(expr.expr, *diagonal_indices)


def get_rank(expr):
    if isinstance(expr, (MatrixExpr, MatrixElement)):
        return 2
    if isinstance(expr, _CodegenArrayAbstract):
        return expr.subrank()
    if isinstance(expr, NDimArray):
        return expr.rank()
    if isinstance(expr, Indexed):
        return expr.rank
    if isinstance(expr, IndexedBase):
        shape = expr.shape
        if shape is None:
            return -1
        else:
            return len(shape)
    if isinstance(expr, _RecognizeMatOp):
        return expr.rank()
    if isinstance(expr, _RecognizeMatMulLines):
        return expr.rank()
    return 0


def _get_subranks(expr):
    if isinstance(expr, _CodegenArrayAbstract):
        return expr.subranks
    else:
        return [get_rank(expr)]


def _get_mapping_from_subranks(subranks):
    mapping = {}
    counter = 0
    for i, rank in enumerate(subranks):
        for j in range(rank):
            mapping[counter] = (i, j)
            counter += 1
    return mapping

def _get_contraction_links(subranks, *contraction_indices):
    mapping = _get_mapping_from_subranks(subranks)
    contraction_tuples = [[mapping[j] for j in i] for i in contraction_indices]
    dlinks = defaultdict(dict)
    for links in contraction_tuples:
        if len(links) > 2:
            raise NotImplementedError("three or more axes contracted at the same time")
        (arg1, pos1), (arg2, pos2) = links
        dlinks[arg1][pos1] = (arg2, pos2)
        dlinks[arg2][pos2] = (arg1, pos1)
    return dict(dlinks)


def _sort_contraction_indices(pairing_indices):
    pairing_indices = [Tuple(*sorted(i)) for i in pairing_indices]
    pairing_indices.sort(key=lambda x: min(x))
    return pairing_indices


def _get_diagonal_indices(flattened_indices):
    axes_contraction = defaultdict(list)
    for i, ind in enumerate(flattened_indices):
        if isinstance(ind, (int, Integer)):
            # If the indices is a number, there can be no diagonal operation:
            continue
        axes_contraction[ind].append(i)
    axes_contraction = {k: v for k, v in axes_contraction.items() if len(v) > 1}
    # Put the diagonalized indices at the end:
    ret_indices = [i for i in flattened_indices if i not in axes_contraction]
    diag_indices = list(axes_contraction)
    diag_indices.sort(key=lambda x: flattened_indices.index(x))
    diagonal_indices = [tuple(axes_contraction[i]) for i in diag_indices]
    ret_indices += diag_indices
    ret_indices = tuple(ret_indices)
    return diagonal_indices, ret_indices


def _get_argindex(subindices, ind):
    for i, sind in enumerate(subindices):
        if ind == sind:
            return i
        if isinstance(sind, (set, frozenset)) and ind in sind:
            return i
    raise IndexError("%s not found in %s" % (ind, subindices))


def _codegen_array_parse(expr):
    if isinstance(expr, Sum):
        function = expr.function
        summation_indices = expr.variables
        subexpr, subindices = _codegen_array_parse(function)
        # Check dimensional consistency:
        shape = subexpr.shape
        if shape:
            for ind, istart, iend in expr.limits:
                i = _get_argindex(subindices, ind)
                if istart != 0 or iend+1 != shape[i]:
                    raise ValueError("summation index and array dimension mismatch: %s" % ind)
        contraction_indices = []
        subindices = list(subindices)
        if isinstance(subexpr, CodegenArrayDiagonal):
            diagonal_indices = list(subexpr.diagonal_indices)
            dindices = subindices[-len(diagonal_indices):]
            subindices = subindices[:-len(diagonal_indices)]
            for index in summation_indices:
                if index in dindices:
                    position = dindices.index(index)
                    contraction_indices.append(diagonal_indices[position])
                    diagonal_indices[position] = None
            diagonal_indices = [i for i in diagonal_indices if i is not None]
            for i, ind in enumerate(subindices):
                if ind in summation_indices:
                    pass
            if diagonal_indices:
                subexpr = CodegenArrayDiagonal(subexpr.expr, *diagonal_indices)
            else:
                subexpr = subexpr.expr

        axes_contraction = defaultdict(list)
        for i, ind in enumerate(subindices):
            if ind in summation_indices:
                axes_contraction[ind].append(i)
                subindices[i] = None
        for k, v in axes_contraction.items():
            contraction_indices.append(tuple(v))
        free_indices = [i for i in subindices if i is not None]
        indices_ret = list(free_indices)
        indices_ret.sort(key=lambda x: free_indices.index(x))
        return CodegenArrayContraction(
                subexpr,
                *contraction_indices,
                free_indices=free_indices
            ), tuple(indices_ret)
    if isinstance(expr, Mul):
        args, indices = zip(*[_codegen_array_parse(arg) for arg in expr.args])
        # Check if there are KroneckerDelta objects:
        kronecker_delta_repl = {}
        for arg in args:
            if not isinstance(arg, KroneckerDelta):
                continue
            # Diagonalize two indices:
            i, j = arg.indices
            kindices = set(arg.indices)
            if i in kronecker_delta_repl:
                kindices.update(kronecker_delta_repl[i])
            if j in kronecker_delta_repl:
                kindices.update(kronecker_delta_repl[j])
            kindices = frozenset(kindices)
            for index in kindices:
                kronecker_delta_repl[index] = kindices
        # Remove KroneckerDelta objects, their relations should be handled by
        # CodegenArrayDiagonal:
        newargs = []
        newindices = []
        for arg, loc_indices in zip(args, indices):
            if isinstance(arg, KroneckerDelta):
                continue
            newargs.append(arg)
            newindices.append(loc_indices)
        flattened_indices = [kronecker_delta_repl.get(j, j) for i in newindices for j in i]
        diagonal_indices, ret_indices = _get_diagonal_indices(flattened_indices)
        tp = CodegenArrayTensorProduct(*newargs)
        if diagonal_indices:
            return (CodegenArrayDiagonal(tp, *diagonal_indices), ret_indices)
        else:
            return tp, ret_indices
    if isinstance(expr, MatrixElement):
        indices = expr.args[1:]
        diagonal_indices, ret_indices = _get_diagonal_indices(indices)
        if diagonal_indices:
            return (CodegenArrayDiagonal(expr.args[0], *diagonal_indices), ret_indices)
        else:
            return expr.args[0], ret_indices
    if isinstance(expr, Indexed):
        indices = expr.indices
        diagonal_indices, ret_indices = _get_diagonal_indices(indices)
        if diagonal_indices:
            return (CodegenArrayDiagonal(expr.base, *diagonal_indices), ret_indices)
        else:
            return expr.args[0], ret_indices
    if isinstance(expr, IndexedBase):
        raise NotImplementedError
    if isinstance(expr, KroneckerDelta):
        return expr, expr.indices
    if isinstance(expr, Add):
        args, indices = zip(*[_codegen_array_parse(arg) for arg in expr.args])
        args = list(args)
        # Check if all indices are compatible. Otherwise expand the dimensions:
        index0set = set(indices[0])
        index0 = indices[0]
        for i in range(1, len(args)):
            if set(indices[i]) != index0set:
                raise NotImplementedError("indices must be the same")
            permutation = Permutation([index0.index(j) for j in indices[i]])
            # Perform index permutations:
            args[i] = CodegenArrayPermuteDims(args[i], permutation)
        return CodegenArrayElementwiseAdd(*args), index0
    return expr, ()
    raise NotImplementedError("could not recognize expression %s" % expr)


def _parse_matrix_expression(expr):
    if isinstance(expr, MatMul):
        args_nonmat = []
        args = []
        contractions = []
        for arg in expr.args:
            if isinstance(arg, MatrixExpr):
                args.append(arg)
            else:
                args_nonmat.append(arg)
        contractions = [(2*i+1, 2*i+2) for i in range(len(args)-1)]
        return Mul.fromiter(args_nonmat)*CodegenArrayContraction(
                CodegenArrayTensorProduct(*[_parse_matrix_expression(arg) for arg in args]),
                *contractions
        )
    elif isinstance(expr, MatAdd):
        return CodegenArrayElementwiseAdd(
                *[_parse_matrix_expression(arg) for arg in expr.args]
        )
    elif isinstance(expr, Transpose):
        return CodegenArrayPermuteDims(
                _parse_matrix_expression(expr.args[0]), [1, 0]
        )
    else:
        return expr


def parse_indexed_expression(expr, first_indices=[]):
    r"""
    Parse indexed expression into a form useful for code generation.

    Examples
    ========

    >>> from sympy.codegen.array_utils import parse_indexed_expression
    >>> from sympy import MatrixSymbol, Sum, symbols
    >>> from sympy.combinatorics import Permutation
    >>> Permutation.print_cyclic = True

    >>> i, j, k, d = symbols("i j k d")
    >>> M = MatrixSymbol("M", d, d)
    >>> N = MatrixSymbol("N", d, d)

    Recognize the trace in summation form:

    >>> expr = Sum(M[i, i], (i, 0, d-1))
    >>> parse_indexed_expression(expr)
    CodegenArrayContraction(M, (0, 1))

    Recognize the extraction of the diagonal by using the same index `i` on
    both axes of the matrix:

    >>> expr = M[i, i]
    >>> parse_indexed_expression(expr)
    CodegenArrayDiagonal(M, (0, 1))

    This function can help perform the transformation expressed in two
    different mathematical notations as:

    `\sum_{j=0}^{N-1} A_{i,j} B_{j,k} \Longrightarrow \mathbf{A}\cdot \mathbf{B}`

    Recognize the matrix multiplication in summation form:

    >>> expr = Sum(M[i, j]*N[j, k], (j, 0, d-1))
    >>> parse_indexed_expression(expr)
    CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (1, 2))

    Specify that ``k`` has to be the starting index:

    >>> parse_indexed_expression(expr, first_indices=[k])
    CodegenArrayPermuteDims(CodegenArrayContraction(CodegenArrayTensorProduct(M, N), (1, 2)), (0 1))
    """

    result, indices = _codegen_array_parse(expr)
    if not first_indices:
        return result
    for i in first_indices:
        if i not in indices:
            first_indices.remove(i)
            #raise ValueError("index %s not found or not a free index" % i)
    first_indices.extend([i for i in indices if i not in first_indices])
    permutation = [first_indices.index(i) for i in indices]
    return CodegenArrayPermuteDims(result, permutation)


def _has_multiple_lines(expr):
    if isinstance(expr, _RecognizeMatMulLines):
        return True
    if isinstance(expr, _RecognizeMatOp):
        return expr.multiple_lines
    return False


class _RecognizeMatOp(object):
    """
    Class to help parsing matrix multiplication lines.
    """
    def __init__(self, operator, args):
        self.operator = operator
        self.args = args
        if any(_has_multiple_lines(arg) for arg in args):
            multiple_lines = True
        else:
            multiple_lines = False
        self.multiple_lines = multiple_lines

    def rank(self):
        if self.operator == Trace:
            return 0
        # TODO: check
        return 2

    def __repr__(self):
        op = self.operator
        if op == MatMul:
            s = "*"
        elif op == MatAdd:
            s = "+"
        else:
            s = op.__name__
            return "_RecognizeMatOp(%s, %s)" % (s, repr(self.args))
        return "_RecognizeMatOp(%s)" % (s.join(repr(i) for i in self.args))

    def __eq__(self, other):
        if not isinstance(other, type(self)):
            return False
        if self.operator != other.operator:
            return False
        if self.args != other.args:
            return False
        return True

    def __iter__(self):
        return iter(self.args)


class _RecognizeMatMulLines(list):
    """
    This class handles multiple parsed multiplication lines.
    """
    def __new__(cls, args):
        if len(args) == 1:
            return args[0]
        return list.__new__(cls, args)

    def rank(self):
        return reduce(lambda x, y: x*y, [get_rank(i) for i in self], S.One)

    def __repr__(self):
        return "_RecognizeMatMulLines(%s)" % super(_RecognizeMatMulLines, self).__repr__()


def _support_function_tp1_recognize(contraction_indices, args):
    if not isinstance(args, list):
        args = [args]
    subranks = [get_rank(i) for i in args]
    coeff = reduce(lambda x, y: x*y, [arg for arg, srank in zip(args, subranks) if srank == 0], S.One)
    mapping = _get_mapping_from_subranks(subranks)
    dlinks = _get_contraction_links(subranks, *contraction_indices)
    flatten_contractions = [j for i in contraction_indices for j in i]
    total_rank = sum(subranks)
    # TODO: turn `free_indices` into a list?
    free_indices = {i: i for i in range(total_rank) if i not in flatten_contractions}
    return_list = []
    while dlinks:
        if free_indices:
            first_index, starting_argind = min(free_indices.items(), key=lambda x: x[1])
            free_indices.pop(first_index)
            starting_argind, starting_pos = mapping[starting_argind]
        else:
            # Maybe a Trace
            first_index = None
            starting_argind = min(dlinks)
            starting_pos = 0
        current_argind, current_pos = starting_argind, starting_pos
        matmul_args = []
        last_index = None
        while True:
            elem = args[current_argind]
            if current_pos == 1:
                elem = _RecognizeMatOp(Transpose, [elem])
            matmul_args.append(elem)
            if current_argind not in dlinks:
                break
            other_pos = 1 - current_pos
            link_dict = dlinks.pop(current_argind)
            if other_pos not in link_dict:
                if free_indices:
                    last_index = [i for i, j in free_indices.items() if mapping[j] == (current_argind, other_pos)][0]
                else:
                    last_index = None
                break
            if len(link_dict) > 2:
                raise NotImplementedError("not a matrix multiplication line")
            # Get the last element of `link_dict` as the next link. The last
            # element is the correct start for trace expressions:
            current_argind, current_pos = link_dict[other_pos]
            if current_argind == starting_argind:
                # This is a trace:
                if len(matmul_args) > 1:
                    matmul_args = [_RecognizeMatOp(Trace, [_RecognizeMatOp(MatMul, matmul_args)])]
                else:
                    matmul_args = [_RecognizeMatOp(Trace, matmul_args)]
                break
        dlinks.pop(starting_argind, None)
        free_indices.pop(last_index, None)
        return_list.append(_RecognizeMatOp(MatMul, matmul_args))
    if coeff != 1:
        # Let's inject the coefficient:
        return_list[0].args.insert(0, coeff)
    return _RecognizeMatMulLines(return_list)


def recognize_matrix_expression(expr):
    r"""
    Recognize matrix expressions in codegen objects.

    If more than one matrix multiplication line have been detected, return a
    list with the matrix expressions.

    Examples
    ========

    >>> from sympy import MatrixSymbol, MatrixExpr, Sum, Symbol
    >>> from sympy.abc import i, j, k, l, N
    >>> from sympy.codegen.array_utils import CodegenArrayContraction, CodegenArrayTensorProduct
    >>> from sympy.codegen.array_utils import recognize_matrix_expression, parse_indexed_expression
    >>> A = MatrixSymbol("A", N, N)
    >>> B = MatrixSymbol("B", N, N)
    >>> C = MatrixSymbol("C", N, N)
    >>> D = MatrixSymbol("D", N, N)

    >>> expr = Sum(A[i, j]*B[j, k], (j, 0, N-1))
    >>> cg = parse_indexed_expression(expr)
    >>> recognize_matrix_expression(cg)
    A*B
    >>> cg = parse_indexed_expression(expr, first_indices=[k])
    >>> recognize_matrix_expression(cg)
    (A*B).T

    Transposition is detected:

    >>> expr = Sum(A[j, i]*B[j, k], (j, 0, N-1))
    >>> cg = parse_indexed_expression(expr)
    >>> recognize_matrix_expression(cg)
    A.T*B
    >>> cg = parse_indexed_expression(expr, first_indices=[k])
    >>> recognize_matrix_expression(cg)
    (A.T*B).T

    Detect the trace:

    >>> expr = Sum(A[i, i], (i, 0, N-1))
    >>> cg = parse_indexed_expression(expr)
    >>> recognize_matrix_expression(cg)
    Trace(A)

    Recognize some more complex traces:
    >>> expr = Sum(A[i, j]*B[j, i], (i, 0, N-1), (j, 0, N-1))
    >>> cg = parse_indexed_expression(expr)
    >>> recognize_matrix_expression(cg)
    Trace(A*B)

    More complicated expressions:

    >>> expr = Sum(A[i, j]*B[k, j]*A[l, k], (j, 0, N-1), (k, 0, N-1))
    >>> cg = parse_indexed_expression(expr)
    >>> recognize_matrix_expression(cg)
    A*B.T*A.T

    Expressions constructed from matrix expressions do not contain literal
    indices, the positions of free indices are returned instead:

    >>> expr = A*B
    >>> cg = CodegenArrayContraction.from_MatMul(expr)
    >>> recognize_matrix_expression(cg)
    A*B

    If more than one line of matrix multiplications is detected, return
    separate matrix multiplication factors:

    >>> cg = CodegenArrayContraction(CodegenArrayTensorProduct(A, B, C, D), (1, 2), (5, 6))
    >>> recognize_matrix_expression(cg)
    [A*B, C*D]

    The two lines have free indices at axes 0, 3 and 4, 7, respectively.
    """
    # TODO: expr has to be a CodegenArray... type
    rec = _recognize_matrix_expression(expr)
    return _unfold_recognized_expr(rec)


def _recognize_matrix_expression(expr):
    if isinstance(expr, CodegenArrayContraction):
        args = _recognize_matrix_expression(expr.expr)
        contraction_indices = expr.contraction_indices
        if isinstance(args, _RecognizeMatOp) and args.operator == MatAdd:
            addends = []
            for arg in args.args:
                addends.append(_support_function_tp1_recognize(contraction_indices, arg))
            return _RecognizeMatOp(MatAdd, addends)
        elif isinstance(args, _RecognizeMatMulLines):
            return _support_function_tp1_recognize(contraction_indices, args)
        return _support_function_tp1_recognize(contraction_indices, [args])
    elif isinstance(expr, CodegenArrayElementwiseAdd):
        add_args = []
        for arg in expr.args:
            add_args.append(_recognize_matrix_expression(arg))
        return _RecognizeMatOp(MatAdd, add_args)
    elif isinstance(expr, (MatrixSymbol, IndexedBase)):
        return expr
    elif isinstance(expr, CodegenArrayPermuteDims):
        if expr.permutation.args[0] == [1, 0]:
            return _RecognizeMatOp(Transpose, [_recognize_matrix_expression(expr.expr)])
        elif isinstance(expr.expr, CodegenArrayTensorProduct):
            ranks = expr.expr.subranks
            newrange = [expr.permutation(i) for i in range(sum(ranks))]
            newpos = []
            counter = 0
            for rank in ranks:
                newpos.append(newrange[counter:counter+rank])
                counter += rank
            newargs = []
            for pos, arg in zip(newpos, expr.expr.args):
                if pos == sorted(pos):
                    newargs.append((_recognize_matrix_expression(arg), pos[0]))
                elif len(pos) == 2:
                    newargs.append((_RecognizeMatOp(Transpose, [_recognize_matrix_expression(arg)]), pos[0]))
                else:
                    raise NotImplementedError
            newargs.sort(key=lambda x: x[1])
            newargs = [i[0] for i in newargs]
            return _RecognizeMatMulLines(newargs)
        else:
            raise NotImplementedError
    elif isinstance(expr, CodegenArrayTensorProduct):
        args = [_recognize_matrix_expression(arg) for arg in expr.args]
        multiple_lines = [_has_multiple_lines(arg) for arg in args]
        if any(multiple_lines):
            if any(a.operator != MatAdd for i, a in enumerate(args) if multiple_lines[i]):
                raise NotImplementedError
            expand_args = [arg.args if multiple_lines[i] else [arg] for i, arg in enumerate(args)]
            it = itertools.product(*expand_args)
            ret = _RecognizeMatOp(MatAdd, [_RecognizeMatMulLines([k for j in i for k in (j if isinstance(j, _RecognizeMatMulLines) else [j])]) for i in it])
            return ret
        return _RecognizeMatMulLines(args)
    elif isinstance(expr, Transpose):
        return expr
    elif isinstance(expr, MatrixExpr):
        return expr
    return expr


def _unfold_recognized_expr(expr):
    if isinstance(expr, _RecognizeMatOp):
        return expr.operator(*[_unfold_recognized_expr(i) for i in expr.args])
    elif isinstance(expr, _RecognizeMatMulLines):
        return [_unfold_recognized_expr(i) for i in expr]
    else:
        return expr
