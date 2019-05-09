from sympy.tensor.tensor import (TensExpr, TensMul)


class PartialDerivative(TensExpr):
    """
    Partial derivative for tensor expressions.

    Examples
    ========

    >>> from sympy.tensor.tensor import TensorIndexType, tensorhead
    >>> from sympy.tensor.toperators import PartialDerivative
    >>> from sympy import symbols
    >>> L = TensorIndexType("L")
    >>> A = tensorhead("A", [L], [[1]])
    >>> i, j = symbols("i j")

    >>> expr = PartialDerivative(A(i), A(j))
    >>> expr
    PartialDerivative(A(i), A(j))

    The ``PartialDerivative`` object behaves like a tensorial expression:

    >>> expr.get_indices()
    [i, j]

    Indices can be contracted:

    >>> PartialDerivative(A(i), A(-i))
    PartialDerivative(A(L_0), A(-L_0))
    """

    def __new__(cls, expr, *variables):

        # Flatten:
        if isinstance(expr, PartialDerivative):
            variables = expr.variables + variables
            expr = expr.expr

        # TODO: check that all variables have rank 1.

        args, indices, free, dum = TensMul._tensMul_contract_indices([expr] +
            list(variables), replace_indices=True)

        obj = TensExpr.__new__(cls, *args)

        obj._indices = indices
        obj._free = free
        obj._dum = dum
        return obj

    def doit(self):
        args, indices, free, dum = TensMul._tensMul_contract_indices(self.args)

        obj = self.func(*args)
        obj._indices = indices
        obj._free = free
        obj._dum = dum
        return obj

    def get_indices(self):
        return self._indices

    @property
    def expr(self):
        return self.args[0]

    @property
    def variables(self):
        return self.args[1:]

    def _extract_data(self, replacement_dict):
        from .array import derive_by_array, tensorcontraction
        indices, array = self.expr._extract_data(replacement_dict)
        for variable in self.variables:
            var_indices, var_array = variable._extract_data(replacement_dict)
            coeff_array, var_array = zip(*[i.as_coeff_Mul() for i in var_array])
            array = derive_by_array(array, var_array)
            array = array.as_mutable()
            varindex = var_indices[0]
            # Remove coefficients of base vector:
            coeff_index = [0] + [slice(None) for i in range(len(indices))]
            for i, coeff in enumerate(coeff_array):
                coeff_index[0] = i
                array[tuple(coeff_index)] /= coeff
            if -varindex in indices:
                pos = indices.index(-varindex)
                array = tensorcontraction(array, (0, pos+1))
                indices.pop(pos)
            else:
                indices.append(varindex)
        return indices, array
