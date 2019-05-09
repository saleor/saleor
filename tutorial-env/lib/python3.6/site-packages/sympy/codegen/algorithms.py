from __future__ import (absolute_import, division, print_function)

from sympy import And, Gt, Lt, Abs, Dummy, oo, Tuple, Symbol
from sympy.codegen.ast import (
    Assignment, AddAugmentedAssignment, CodeBlock, Declaration, FunctionDefinition,
    Print, Return, Scope, While, Variable, Pointer, real
)

""" This module collects functions for constructing ASTs representing algorithms. """

def newtons_method(expr, wrt, atol=1e-12, delta=None, debug=False,
                   itermax=None, counter=None):
    """ Generates an AST for Newton-Raphson method (a root-finding algorithm).

    Returns an abstract syntax tree (AST) based on ``sympy.codegen.ast`` for Netwon's
    method of root-finding.

    Parameters
    ==========

    expr : expression
    wrt : Symbol
        With respect to, i.e. what is the variable.
    atol : number or expr
        Absolute tolerance (stopping criterion)
    delta : Symbol
        Will be a ``Dummy`` if ``None``.
    debug : bool
        Whether to print convergence information during iterations
    itermax : number or expr
        Maximum number of iterations.
    counter : Symbol
        Will be a ``Dummy`` if ``None``.

    Examples
    ========

    >>> from sympy import symbols, cos
    >>> from sympy.codegen.ast import Assignment
    >>> from sympy.codegen.algorithms import newtons_method
    >>> x, dx, atol = symbols('x dx atol')
    >>> expr = cos(x) - x**3
    >>> algo = newtons_method(expr, x, atol, dx)
    >>> algo.has(Assignment(dx, -expr/expr.diff(x)))
    True

    References
    ==========

    .. [1] https://en.wikipedia.org/wiki/Newton%27s_method

    """

    if delta is None:
        delta = Dummy()
        Wrapper = Scope
        name_d = 'delta'
    else:
        Wrapper = lambda x: x
        name_d = delta.name

    delta_expr = -expr/expr.diff(wrt)
    whl_bdy = [Assignment(delta, delta_expr), AddAugmentedAssignment(wrt, delta)]
    if debug:
        prnt = Print([wrt, delta], r"{0}=%12.5g {1}=%12.5g\n".format(wrt.name, name_d))
        whl_bdy = [whl_bdy[0], prnt] + whl_bdy[1:]
    req = Gt(Abs(delta), atol)
    declars = [Declaration(Variable(delta, type=real, value=oo))]
    if itermax is not None:
        counter = counter or Dummy(integer=True)
        v_counter = Variable.deduced(counter, 0)
        declars.append(Declaration(v_counter))
        whl_bdy.append(AddAugmentedAssignment(counter, 1))
        req = And(req, Lt(counter, itermax))
    whl = While(req, CodeBlock(*whl_bdy))
    blck = declars + [whl]
    return Wrapper(CodeBlock(*blck))


def _symbol_of(arg):
    if isinstance(arg, Declaration):
        arg = arg.variable.symbol
    elif isinstance(arg, Variable):
        arg = arg.symbol
    return arg


def newtons_method_function(expr, wrt, params=None, func_name="newton", attrs=Tuple(), **kwargs):
    """ Generates an AST for a function implementing the Newton-Raphson method.

    Parameters
    ==========

    expr : expression
    wrt : Symbol
        With respect to, i.e. what is the variable
    params : iterable of symbols
        Symbols appearing in expr that are taken as constants during the iterations
        (these will be accepted as parameters to the generated function).
    func_name : str
        Name of the generated function.
    attrs : Tuple
        Attribute instances passed as ``attrs`` to ``FunctionDefinition``.
    \\*\\*kwargs :
        Keyword arguments passed to :func:`sympy.codegen.algorithms.newtons_method`.

    Examples
    ========

    >>> from sympy import symbols, cos
    >>> from sympy.codegen.algorithms import newtons_method_function
    >>> from sympy.codegen.pyutils import render_as_module
    >>> from sympy.core.compatibility import exec_
    >>> x = symbols('x')
    >>> expr = cos(x) - x**3
    >>> func = newtons_method_function(expr, x)
    >>> py_mod = render_as_module(func)  # source code as string
    >>> namespace = {}
    >>> exec_(py_mod, namespace, namespace)
    >>> res = eval('newton(0.5)', namespace)
    >>> abs(res - 0.865474033102) < 1e-12
    True

    See Also
    ========

    sympy.codegen.ast.newtons_method

    """
    if params is None:
        params = (wrt,)
    pointer_subs = {p.symbol: Symbol('(*%s)' % p.symbol.name)
                    for p in params if isinstance(p, Pointer)}
    delta = kwargs.pop('delta', None)
    if delta is None:
        delta = Symbol('d_' + wrt.name)
        if expr.has(delta):
            delta = None  # will use Dummy
    algo = newtons_method(expr, wrt, delta=delta, **kwargs).xreplace(pointer_subs)
    if isinstance(algo, Scope):
        algo = algo.body
    not_in_params = expr.free_symbols.difference(set(_symbol_of(p) for p in params))
    if not_in_params:
        raise ValueError("Missing symbols in params: %s" % ', '.join(map(str, not_in_params)))
    declars = tuple(Variable(p, real) for p in params)
    body = CodeBlock(algo, Return(wrt))
    return FunctionDefinition(real, func_name, declars, body, attrs=attrs)
