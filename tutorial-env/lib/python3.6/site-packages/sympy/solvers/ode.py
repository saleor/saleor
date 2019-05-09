r"""
This module contains :py:meth:`~sympy.solvers.ode.dsolve` and different helper
functions that it uses.

:py:meth:`~sympy.solvers.ode.dsolve` solves ordinary differential equations.
See the docstring on the various functions for their uses.  Note that partial
differential equations support is in ``pde.py``.  Note that hint functions
have docstrings describing their various methods, but they are intended for
internal use.  Use ``dsolve(ode, func, hint=hint)`` to solve an ODE using a
specific hint.  See also the docstring on
:py:meth:`~sympy.solvers.ode.dsolve`.

**Functions in this module**

    These are the user functions in this module:

    - :py:meth:`~sympy.solvers.ode.dsolve` - Solves ODEs.
    - :py:meth:`~sympy.solvers.ode.classify_ode` - Classifies ODEs into
      possible hints for :py:meth:`~sympy.solvers.ode.dsolve`.
    - :py:meth:`~sympy.solvers.ode.checkodesol` - Checks if an equation is the
      solution to an ODE.
    - :py:meth:`~sympy.solvers.ode.homogeneous_order` - Returns the
      homogeneous order of an expression.
    - :py:meth:`~sympy.solvers.ode.infinitesimals` - Returns the infinitesimals
      of the Lie group of point transformations of an ODE, such that it is
      invariant.
    - :py:meth:`~sympy.solvers.ode_checkinfsol` - Checks if the given infinitesimals
      are the actual infinitesimals of a first order ODE.

    These are the non-solver helper functions that are for internal use.  The
    user should use the various options to
    :py:meth:`~sympy.solvers.ode.dsolve` to obtain the functionality provided
    by these functions:

    - :py:meth:`~sympy.solvers.ode.odesimp` - Does all forms of ODE
      simplification.
    - :py:meth:`~sympy.solvers.ode.ode_sol_simplicity` - A key function for
      comparing solutions by simplicity.
    - :py:meth:`~sympy.solvers.ode.constantsimp` - Simplifies arbitrary
      constants.
    - :py:meth:`~sympy.solvers.ode.constant_renumber` - Renumber arbitrary
      constants.
    - :py:meth:`~sympy.solvers.ode._handle_Integral` - Evaluate unevaluated
      Integrals.

    See also the docstrings of these functions.

**Currently implemented solver methods**

The following methods are implemented for solving ordinary differential
equations.  See the docstrings of the various hint functions for more
information on each (run ``help(ode)``):

  - 1st order separable differential equations.
  - 1st order differential equations whose coefficients or `dx` and `dy` are
    functions homogeneous of the same order.
  - 1st order exact differential equations.
  - 1st order linear differential equations.
  - 1st order Bernoulli differential equations.
  - Power series solutions for first order differential equations.
  - Lie Group method of solving first order differential equations.
  - 2nd order Liouville differential equations.
  - Power series solutions for second order differential equations
    at ordinary and regular singular points.
  - `n`\th order differential equation that can be solved with algebraic
    rearrangement and integration.
  - `n`\th order linear homogeneous differential equation with constant
    coefficients.
  - `n`\th order linear inhomogeneous differential equation with constant
    coefficients using the method of undetermined coefficients.
  - `n`\th order linear inhomogeneous differential equation with constant
    coefficients using the method of variation of parameters.

**Philosophy behind this module**

This module is designed to make it easy to add new ODE solving methods without
having to mess with the solving code for other methods.  The idea is that
there is a :py:meth:`~sympy.solvers.ode.classify_ode` function, which takes in
an ODE and tells you what hints, if any, will solve the ODE.  It does this
without attempting to solve the ODE, so it is fast.  Each solving method is a
hint, and it has its own function, named ``ode_<hint>``.  That function takes
in the ODE and any match expression gathered by
:py:meth:`~sympy.solvers.ode.classify_ode` and returns a solved result.  If
this result has any integrals in it, the hint function will return an
unevaluated :py:class:`~sympy.integrals.Integral` class.
:py:meth:`~sympy.solvers.ode.dsolve`, which is the user wrapper function
around all of this, will then call :py:meth:`~sympy.solvers.ode.odesimp` on
the result, which, among other things, will attempt to solve the equation for
the dependent variable (the function we are solving for), simplify the
arbitrary constants in the expression, and evaluate any integrals, if the hint
allows it.

**How to add new solution methods**

If you have an ODE that you want :py:meth:`~sympy.solvers.ode.dsolve` to be
able to solve, try to avoid adding special case code here.  Instead, try
finding a general method that will solve your ODE, as well as others.  This
way, the :py:mod:`~sympy.solvers.ode` module will become more robust, and
unhindered by special case hacks.  WolphramAlpha and Maple's
DETools[odeadvisor] function are two resources you can use to classify a
specific ODE.  It is also better for a method to work with an `n`\th order ODE
instead of only with specific orders, if possible.

To add a new method, there are a few things that you need to do.  First, you
need a hint name for your method.  Try to name your hint so that it is
unambiguous with all other methods, including ones that may not be implemented
yet.  If your method uses integrals, also include a ``hint_Integral`` hint.
If there is more than one way to solve ODEs with your method, include a hint
for each one, as well as a ``<hint>_best`` hint.  Your ``ode_<hint>_best()``
function should choose the best using min with ``ode_sol_simplicity`` as the
key argument.  See
:py:meth:`~sympy.solvers.ode.ode_1st_homogeneous_coeff_best`, for example.
The function that uses your method will be called ``ode_<hint>()``, so the
hint must only use characters that are allowed in a Python function name
(alphanumeric characters and the underscore '``_``' character).  Include a
function for every hint, except for ``_Integral`` hints
(:py:meth:`~sympy.solvers.ode.dsolve` takes care of those automatically).
Hint names should be all lowercase, unless a word is commonly capitalized
(such as Integral or Bernoulli).  If you have a hint that you do not want to
run with ``all_Integral`` that doesn't have an ``_Integral`` counterpart (such
as a best hint that would defeat the purpose of ``all_Integral``), you will
need to remove it manually in the :py:meth:`~sympy.solvers.ode.dsolve` code.
See also the :py:meth:`~sympy.solvers.ode.classify_ode` docstring for
guidelines on writing a hint name.

Determine *in general* how the solutions returned by your method compare with
other methods that can potentially solve the same ODEs.  Then, put your hints
in the :py:data:`~sympy.solvers.ode.allhints` tuple in the order that they
should be called.  The ordering of this tuple determines which hints are
default.  Note that exceptions are ok, because it is easy for the user to
choose individual hints with :py:meth:`~sympy.solvers.ode.dsolve`.  In
general, ``_Integral`` variants should go at the end of the list, and
``_best`` variants should go before the various hints they apply to.  For
example, the ``undetermined_coefficients`` hint comes before the
``variation_of_parameters`` hint because, even though variation of parameters
is more general than undetermined coefficients, undetermined coefficients
generally returns cleaner results for the ODEs that it can solve than
variation of parameters does, and it does not require integration, so it is
much faster.

Next, you need to have a match expression or a function that matches the type
of the ODE, which you should put in :py:meth:`~sympy.solvers.ode.classify_ode`
(if the match function is more than just a few lines, like
:py:meth:`~sympy.solvers.ode._undetermined_coefficients_match`, it should go
outside of :py:meth:`~sympy.solvers.ode.classify_ode`).  It should match the
ODE without solving for it as much as possible, so that
:py:meth:`~sympy.solvers.ode.classify_ode` remains fast and is not hindered by
bugs in solving code.  Be sure to consider corner cases.  For example, if your
solution method involves dividing by something, make sure you exclude the case
where that division will be 0.

In most cases, the matching of the ODE will also give you the various parts
that you need to solve it.  You should put that in a dictionary (``.match()``
will do this for you), and add that as ``matching_hints['hint'] = matchdict``
in the relevant part of :py:meth:`~sympy.solvers.ode.classify_ode`.
:py:meth:`~sympy.solvers.ode.classify_ode` will then send this to
:py:meth:`~sympy.solvers.ode.dsolve`, which will send it to your function as
the ``match`` argument.  Your function should be named ``ode_<hint>(eq, func,
order, match)`.  If you need to send more information, put it in the ``match``
dictionary.  For example, if you had to substitute in a dummy variable in
:py:meth:`~sympy.solvers.ode.classify_ode` to match the ODE, you will need to
pass it to your function using the `match` dict to access it.  You can access
the independent variable using ``func.args[0]``, and the dependent variable
(the function you are trying to solve for) as ``func.func``.  If, while trying
to solve the ODE, you find that you cannot, raise ``NotImplementedError``.
:py:meth:`~sympy.solvers.ode.dsolve` will catch this error with the ``all``
meta-hint, rather than causing the whole routine to fail.

Add a docstring to your function that describes the method employed.  Like
with anything else in SymPy, you will need to add a doctest to the docstring,
in addition to real tests in ``test_ode.py``.  Try to maintain consistency
with the other hint functions' docstrings.  Add your method to the list at the
top of this docstring.  Also, add your method to ``ode.rst`` in the
``docs/src`` directory, so that the Sphinx docs will pull its docstring into
the main SymPy documentation.  Be sure to make the Sphinx documentation by
running ``make html`` from within the doc directory to verify that the
docstring formats correctly.

If your solution method involves integrating, use :py:meth:`Integral()
<sympy.integrals.integrals.Integral>` instead of
:py:meth:`~sympy.core.expr.Expr.integrate`.  This allows the user to bypass
hard/slow integration by using the ``_Integral`` variant of your hint.  In
most cases, calling :py:meth:`sympy.core.basic.Basic.doit` will integrate your
solution.  If this is not the case, you will need to write special code in
:py:meth:`~sympy.solvers.ode._handle_Integral`.  Arbitrary constants should be
symbols named ``C1``, ``C2``, and so on.  All solution methods should return
an equality instance.  If you need an arbitrary number of arbitrary constants,
you can use ``constants = numbered_symbols(prefix='C', cls=Symbol, start=1)``.
If it is possible to solve for the dependent function in a general way, do so.
Otherwise, do as best as you can, but do not call solve in your
``ode_<hint>()`` function.  :py:meth:`~sympy.solvers.ode.odesimp` will attempt
to solve the solution for you, so you do not need to do that.  Lastly, if your
ODE has a common simplification that can be applied to your solutions, you can
add a special case in :py:meth:`~sympy.solvers.ode.odesimp` for it.  For
example, solutions returned from the ``1st_homogeneous_coeff`` hints often
have many :py:meth:`~sympy.functions.log` terms, so
:py:meth:`~sympy.solvers.ode.odesimp` calls
:py:meth:`~sympy.simplify.simplify.logcombine` on them (it also helps to write
the arbitrary constant as ``log(C1)`` instead of ``C1`` in this case).  Also
consider common ways that you can rearrange your solution to have
:py:meth:`~sympy.solvers.ode.constantsimp` take better advantage of it.  It is
better to put simplification in :py:meth:`~sympy.solvers.ode.odesimp` than in
your method, because it can then be turned off with the simplify flag in
:py:meth:`~sympy.solvers.ode.dsolve`.  If you have any extraneous
simplification in your function, be sure to only run it using ``if
match.get('simplify', True):``, especially if it can be slow or if it can
reduce the domain of the solution.

Finally, as with every contribution to SymPy, your method will need to be
tested.  Add a test for each method in ``test_ode.py``.  Follow the
conventions there, i.e., test the solver using ``dsolve(eq, f(x),
hint=your_hint)``, and also test the solution using
:py:meth:`~sympy.solvers.ode.checkodesol` (you can put these in a separate
tests and skip/XFAIL if it runs too slow/doesn't work).  Be sure to call your
hint specifically in :py:meth:`~sympy.solvers.ode.dsolve`, that way the test
won't be broken simply by the introduction of another matching hint.  If your
method works for higher order (>1) ODEs, you will need to run ``sol =
constant_renumber(sol, 'C', 1, order)`` for each solution, where ``order`` is
the order of the ODE.  This is because ``constant_renumber`` renumbers the
arbitrary constants by printing order, which is platform dependent.  Try to
test every corner case of your solver, including a range of orders if it is a
`n`\th order solver, but if your solver is slow, such as if it involves hard
integration, try to keep the test run time down.

Feel free to refactor existing hints to avoid duplicating code or creating
inconsistencies.  If you can show that your method exactly duplicates an
existing method, including in the simplicity and speed of obtaining the
solutions, then you can remove the old, less general method.  The existing
code is tested extensively in ``test_ode.py``, so if anything is broken, one
of those tests will surely fail.

"""
from __future__ import print_function, division

from collections import defaultdict
from itertools import islice
from functools import cmp_to_key

from sympy.core import Add, S, Mul, Pow, oo
from sympy.core.compatibility import ordered, iterable, is_sequence, range, string_types
from sympy.core.containers import Tuple
from sympy.core.exprtools import factor_terms
from sympy.core.expr import AtomicExpr, Expr
from sympy.core.function import (Function, Derivative, AppliedUndef, diff,
    expand, expand_mul, Subs, _mexpand)
from sympy.core.multidimensional import vectorize
from sympy.core.numbers import NaN, zoo, I, Number
from sympy.core.relational import Equality, Eq
from sympy.core.symbol import Symbol, Wild, Dummy, symbols
from sympy.core.sympify import sympify

from sympy.logic.boolalg import (BooleanAtom, And, Or, Not, BooleanTrue,
                                BooleanFalse)
from sympy.functions import cos, exp, im, log, re, sin, tan, sqrt, \
    atan2, conjugate, Piecewise
from sympy.functions.combinatorial.factorials import factorial
from sympy.integrals.integrals import Integral, integrate
from sympy.matrices import wronskian, Matrix, eye, zeros
from sympy.polys import (Poly, RootOf, rootof, terms_gcd,
                         PolynomialError, lcm, roots)
from sympy.polys.polyroots import roots_quartic
from sympy.polys.polytools import cancel, degree, div
from sympy.series import Order
from sympy.series.series import series
from sympy.simplify import collect, logcombine, powsimp, separatevars, \
    simplify, trigsimp, posify, cse
from sympy.simplify.powsimp import powdenest
from sympy.simplify.radsimp import collect_const
from sympy.solvers import solve
from sympy.solvers.pde import pdsolve

from sympy.utilities import numbered_symbols, default_sort_key, sift
from sympy.solvers.deutils import _preprocess, ode_order, _desolve

#: This is a list of hints in the order that they should be preferred by
#: :py:meth:`~sympy.solvers.ode.classify_ode`. In general, hints earlier in the
#: list should produce simpler solutions than those later in the list (for
#: ODEs that fit both).  For now, the order of this list is based on empirical
#: observations by the developers of SymPy.
#:
#: The hint used by :py:meth:`~sympy.solvers.ode.dsolve` for a specific ODE
#: can be overridden (see the docstring).
#:
#: In general, ``_Integral`` hints are grouped at the end of the list, unless
#: there is a method that returns an unevaluable integral most of the time
#: (which go near the end of the list anyway).  ``default``, ``all``,
#: ``best``, and ``all_Integral`` meta-hints should not be included in this
#: list, but ``_best`` and ``_Integral`` hints should be included.
allhints = (
    "nth_algebraic",
    "separable",
    "1st_exact",
    "1st_linear",
    "Bernoulli",
    "Riccati_special_minus2",
    "1st_homogeneous_coeff_best",
    "1st_homogeneous_coeff_subs_indep_div_dep",
    "1st_homogeneous_coeff_subs_dep_div_indep",
    "almost_linear",
    "linear_coefficients",
    "separable_reduced",
    "1st_power_series",
    "lie_group",
    "nth_linear_constant_coeff_homogeneous",
    "nth_linear_euler_eq_homogeneous",
    "nth_linear_constant_coeff_undetermined_coefficients",
    "nth_linear_euler_eq_nonhomogeneous_undetermined_coefficients",
    "nth_linear_constant_coeff_variation_of_parameters",
    "nth_linear_euler_eq_nonhomogeneous_variation_of_parameters",
    "Liouville",
    "nth_order_reducible",
    "2nd_power_series_ordinary",
    "2nd_power_series_regular",
    "nth_algebraic_Integral",
    "separable_Integral",
    "1st_exact_Integral",
    "1st_linear_Integral",
    "Bernoulli_Integral",
    "1st_homogeneous_coeff_subs_indep_div_dep_Integral",
    "1st_homogeneous_coeff_subs_dep_div_indep_Integral",
    "almost_linear_Integral",
    "linear_coefficients_Integral",
    "separable_reduced_Integral",
    "nth_linear_constant_coeff_variation_of_parameters_Integral",
    "nth_linear_euler_eq_nonhomogeneous_variation_of_parameters_Integral",
    "Liouville_Integral",
       )

lie_heuristics = (
    "abaco1_simple",
    "abaco1_product",
    "abaco2_similar",
    "abaco2_unique_unknown",
    "abaco2_unique_general",
    "linear",
    "function_sum",
    "bivariate",
    "chi"
    )


def sub_func_doit(eq, func, new):
    r"""
    When replacing the func with something else, we usually want the
    derivative evaluated, so this function helps in making that happen.

    Examples
    ========

    >>> from sympy import Derivative, symbols, Function
    >>> from sympy.solvers.ode import sub_func_doit
    >>> x, z = symbols('x, z')
    >>> y = Function('y')

    >>> sub_func_doit(3*Derivative(y(x), x) - 1, y(x), x)
    2

    >>> sub_func_doit(x*Derivative(y(x), x) - y(x)**2 + y(x), y(x),
    ... 1/(x*(z + 1/x)))
    x*(-1/(x**2*(z + 1/x)) + 1/(x**3*(z + 1/x)**2)) + 1/(x*(z + 1/x))
    ...- 1/(x**2*(z + 1/x)**2)
    """
    reps= {func: new}
    for d in eq.atoms(Derivative):
        if d.expr == func:
            reps[d] = new.diff(*d.variable_count)
        else:
            reps[d] = d.xreplace({func: new}).doit(deep=False)
    return eq.xreplace(reps)


def get_numbered_constants(eq, num=1, start=1, prefix='C'):
    """
    Returns a list of constants that do not occur
    in eq already.
    """

    ncs = iter_numbered_constants(eq, start, prefix)
    Cs = [next(ncs) for i in range(num)]
    return (Cs[0] if num == 1 else tuple(Cs))


def iter_numbered_constants(eq, start=1, prefix='C'):
    """
    Returns an iterator of constants that do not occur
    in eq already.
    """

    if isinstance(eq, Expr):
        eq = [eq]
    elif not iterable(eq):
        raise ValueError("Expected Expr or iterable but got %s" % eq)

    atom_set = set().union(*[i.free_symbols for i in eq])
    func_set = set().union(*[i.atoms(Function) for i in eq])
    if func_set:
        atom_set |= {Symbol(str(f.func)) for f in func_set}
    return numbered_symbols(start=start, prefix=prefix, exclude=atom_set)


def dsolve(eq, func=None, hint="default", simplify=True,
    ics= None, xi=None, eta=None, x0=0, n=6, **kwargs):
    r"""
    Solves any (supported) kind of ordinary differential equation and
    system of ordinary differential equations.

    For single ordinary differential equation
    =========================================

    It is classified under this when number of equation in ``eq`` is one.
    **Usage**

        ``dsolve(eq, f(x), hint)`` -> Solve ordinary differential equation
        ``eq`` for function ``f(x)``, using method ``hint``.

    **Details**

        ``eq`` can be any supported ordinary differential equation (see the
            :py:mod:`~sympy.solvers.ode` docstring for supported methods).
            This can either be an :py:class:`~sympy.core.relational.Equality`,
            or an expression, which is assumed to be equal to ``0``.

        ``f(x)`` is a function of one variable whose derivatives in that
            variable make up the ordinary differential equation ``eq``.  In
            many cases it is not necessary to provide this; it will be
            autodetected (and an error raised if it couldn't be detected).

        ``hint`` is the solving method that you want dsolve to use.  Use
            ``classify_ode(eq, f(x))`` to get all of the possible hints for an
            ODE.  The default hint, ``default``, will use whatever hint is
            returned first by :py:meth:`~sympy.solvers.ode.classify_ode`.  See
            Hints below for more options that you can use for hint.

        ``simplify`` enables simplification by
            :py:meth:`~sympy.solvers.ode.odesimp`.  See its docstring for more
            information.  Turn this off, for example, to disable solving of
            solutions for ``func`` or simplification of arbitrary constants.
            It will still integrate with this hint. Note that the solution may
            contain more arbitrary constants than the order of the ODE with
            this option enabled.

        ``xi`` and ``eta`` are the infinitesimal functions of an ordinary
            differential equation. They are the infinitesimals of the Lie group
            of point transformations for which the differential equation is
            invariant. The user can specify values for the infinitesimals. If
            nothing is specified, ``xi`` and ``eta`` are calculated using
            :py:meth:`~sympy.solvers.ode.infinitesimals` with the help of various
            heuristics.

        ``ics`` is the set of initial/boundary conditions for the differential equation.
          It should be given in the form of ``{f(x0): x1, f(x).diff(x).subs(x, x2):
          x3}`` and so on.  For power series solutions, if no initial
          conditions are specified ``f(0)`` is assumed to be ``C0`` and the power
          series solution is calculated about 0.

        ``x0`` is the point about which the power series solution of a differential
          equation is to be evaluated.

        ``n`` gives the exponent of the dependent variable up to which the power series
          solution of a differential equation is to be evaluated.

    **Hints**

        Aside from the various solving methods, there are also some meta-hints
        that you can pass to :py:meth:`~sympy.solvers.ode.dsolve`:

        ``default``:
                This uses whatever hint is returned first by
                :py:meth:`~sympy.solvers.ode.classify_ode`. This is the
                default argument to :py:meth:`~sympy.solvers.ode.dsolve`.

        ``all``:
                To make :py:meth:`~sympy.solvers.ode.dsolve` apply all
                relevant classification hints, use ``dsolve(ODE, func,
                hint="all")``.  This will return a dictionary of
                ``hint:solution`` terms.  If a hint causes dsolve to raise the
                ``NotImplementedError``, value of that hint's key will be the
                exception object raised.  The dictionary will also include
                some special keys:

                - ``order``: The order of the ODE.  See also
                  :py:meth:`~sympy.solvers.deutils.ode_order` in
                  ``deutils.py``.
                - ``best``: The simplest hint; what would be returned by
                  ``best`` below.
                - ``best_hint``: The hint that would produce the solution
                  given by ``best``.  If more than one hint produces the best
                  solution, the first one in the tuple returned by
                  :py:meth:`~sympy.solvers.ode.classify_ode` is chosen.
                - ``default``: The solution that would be returned by default.
                  This is the one produced by the hint that appears first in
                  the tuple returned by
                  :py:meth:`~sympy.solvers.ode.classify_ode`.

        ``all_Integral``:
                This is the same as ``all``, except if a hint also has a
                corresponding ``_Integral`` hint, it only returns the
                ``_Integral`` hint.  This is useful if ``all`` causes
                :py:meth:`~sympy.solvers.ode.dsolve` to hang because of a
                difficult or impossible integral.  This meta-hint will also be
                much faster than ``all``, because
                :py:meth:`~sympy.core.expr.Expr.integrate` is an expensive
                routine.

        ``best``:
                To have :py:meth:`~sympy.solvers.ode.dsolve` try all methods
                and return the simplest one.  This takes into account whether
                the solution is solvable in the function, whether it contains
                any Integral classes (i.e.  unevaluatable integrals), and
                which one is the shortest in size.

        See also the :py:meth:`~sympy.solvers.ode.classify_ode` docstring for
        more info on hints, and the :py:mod:`~sympy.solvers.ode` docstring for
        a list of all supported hints.

    **Tips**

        - You can declare the derivative of an unknown function this way:

            >>> from sympy import Function, Derivative
            >>> from sympy.abc import x # x is the independent variable
            >>> f = Function("f")(x) # f is a function of x
            >>> # f_ will be the derivative of f with respect to x
            >>> f_ = Derivative(f, x)

        - See ``test_ode.py`` for many tests, which serves also as a set of
          examples for how to use :py:meth:`~sympy.solvers.ode.dsolve`.
        - :py:meth:`~sympy.solvers.ode.dsolve` always returns an
          :py:class:`~sympy.core.relational.Equality` class (except for the
          case when the hint is ``all`` or ``all_Integral``).  If possible, it
          solves the solution explicitly for the function being solved for.
          Otherwise, it returns an implicit solution.
        - Arbitrary constants are symbols named ``C1``, ``C2``, and so on.
        - Because all solutions should be mathematically equivalent, some
          hints may return the exact same result for an ODE. Often, though,
          two different hints will return the same solution formatted
          differently.  The two should be equivalent. Also note that sometimes
          the values of the arbitrary constants in two different solutions may
          not be the same, because one constant may have "absorbed" other
          constants into it.
        - Do ``help(ode.ode_<hintname>)`` to get help more information on a
          specific hint, where ``<hintname>`` is the name of a hint without
          ``_Integral``.

    For system of ordinary differential equations
    =============================================

   **Usage**
        ``dsolve(eq, func)`` -> Solve a system of ordinary differential
        equations ``eq`` for ``func`` being list of functions including
        `x(t)`, `y(t)`, `z(t)` where number of functions in the list depends
        upon the number of equations provided in ``eq``.

    **Details**

        ``eq`` can be any supported system of ordinary differential equations
        This can either be an :py:class:`~sympy.core.relational.Equality`,
        or an expression, which is assumed to be equal to ``0``.

        ``func`` holds ``x(t)`` and ``y(t)`` being functions of one variable which
        together with some of their derivatives make up the system of ordinary
        differential equation ``eq``. It is not necessary to provide this; it
        will be autodetected (and an error raised if it couldn't be detected).

    **Hints**

        The hints are formed by parameters returned by classify_sysode, combining
        them give hints name used later for forming method name.

    Examples
    ========

    >>> from sympy import Function, dsolve, Eq, Derivative, sin, cos, symbols
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> dsolve(Derivative(f(x), x, x) + 9*f(x), f(x))
    Eq(f(x), C1*sin(3*x) + C2*cos(3*x))

    >>> eq = sin(x)*cos(f(x)) + cos(x)*sin(f(x))*f(x).diff(x)
    >>> dsolve(eq, hint='1st_exact')
    [Eq(f(x), -acos(C1/cos(x)) + 2*pi), Eq(f(x), acos(C1/cos(x)))]
    >>> dsolve(eq, hint='almost_linear')
    [Eq(f(x), -acos(C1/cos(x)) + 2*pi), Eq(f(x), acos(C1/cos(x)))]
    >>> t = symbols('t')
    >>> x, y = symbols('x, y', cls=Function)
    >>> eq = (Eq(Derivative(x(t),t), 12*t*x(t) + 8*y(t)), Eq(Derivative(y(t),t), 21*x(t) + 7*t*y(t)))
    >>> dsolve(eq)
    [Eq(x(t), C1*x0(t) + C2*x0(t)*Integral(8*exp(Integral(7*t, t))*exp(Integral(12*t, t))/x0(t)**2, t)),
    Eq(y(t), C1*y0(t) + C2*(y0(t)*Integral(8*exp(Integral(7*t, t))*exp(Integral(12*t, t))/x0(t)**2, t) +
    exp(Integral(7*t, t))*exp(Integral(12*t, t))/x0(t)))]
    >>> eq = (Eq(Derivative(x(t),t),x(t)*y(t)*sin(t)), Eq(Derivative(y(t),t),y(t)**2*sin(t)))
    >>> dsolve(eq)
    {Eq(x(t), -exp(C1)/(C2*exp(C1) - cos(t))), Eq(y(t), -1/(C1 - cos(t)))}
    """
    if iterable(eq):
        match = classify_sysode(eq, func)
        eq = match['eq']
        order = match['order']
        func = match['func']
        t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]

        # keep highest order term coefficient positive
        for i in range(len(eq)):
            for func_ in func:
                if isinstance(func_, list):
                    pass
                else:
                    if eq[i].coeff(diff(func[i],t,ode_order(eq[i], func[i]))).is_negative:
                        eq[i] = -eq[i]
        match['eq'] = eq
        if len(set(order.values()))!=1:
            raise ValueError("It solves only those systems of equations whose orders are equal")
        match['order'] = list(order.values())[0]
        def recur_len(l):
            return sum(recur_len(item) if isinstance(item,list) else 1 for item in l)
        if recur_len(func) != len(eq):
            raise ValueError("dsolve() and classify_sysode() work with "
            "number of functions being equal to number of equations")
        if match['type_of_equation'] is None:
            raise NotImplementedError
        else:
            if match['is_linear'] == True:
                if match['no_of_equation'] > 3:
                    solvefunc = globals()['sysode_linear_neq_order%(order)s' % match]
                else:
                    solvefunc = globals()['sysode_linear_%(no_of_equation)seq_order%(order)s' % match]
            else:
                solvefunc = globals()['sysode_nonlinear_%(no_of_equation)seq_order%(order)s' % match]
            sols = solvefunc(match)
            if ics:
                constants = Tuple(*sols).free_symbols - Tuple(*eq).free_symbols
                solved_constants = solve_ics(sols, func, constants, ics)
                return [sol.subs(solved_constants) for sol in sols]
            return sols
    else:
        given_hint = hint  # hint given by the user

        # See the docstring of _desolve for more details.
        hints = _desolve(eq, func=func,
            hint=hint, simplify=True, xi=xi, eta=eta, type='ode', ics=ics,
            x0=x0, n=n, **kwargs)

        eq = hints.pop('eq', eq)
        all_ = hints.pop('all', False)
        if all_:
            retdict = {}
            failed_hints = {}
            gethints = classify_ode(eq, dict=True)
            orderedhints = gethints['ordered_hints']
            for hint in hints:
                try:
                    rv = _helper_simplify(eq, hint, hints[hint], simplify)
                except NotImplementedError as detail:
                    failed_hints[hint] = detail
                else:
                    retdict[hint] = rv
            func = hints[hint]['func']

            retdict['best'] = min(list(retdict.values()), key=lambda x:
                ode_sol_simplicity(x, func, trysolving=not simplify))
            if given_hint == 'best':
                return retdict['best']
            for i in orderedhints:
                if retdict['best'] == retdict.get(i, None):
                    retdict['best_hint'] = i
                    break
            retdict['default'] = gethints['default']
            retdict['order'] = gethints['order']
            retdict.update(failed_hints)
            return retdict

        else:
            # The key 'hint' stores the hint needed to be solved for.
            hint = hints['hint']
            return _helper_simplify(eq, hint, hints, simplify, ics=ics)

def _helper_simplify(eq, hint, match, simplify=True, ics=None, **kwargs):
    r"""
    Helper function of dsolve that calls the respective
    :py:mod:`~sympy.solvers.ode` functions to solve for the ordinary
    differential equations. This minimizes the computation in calling
    :py:meth:`~sympy.solvers.deutils._desolve` multiple times.
    """
    r = match
    if hint.endswith('_Integral'):
        solvefunc = globals()['ode_' + hint[:-len('_Integral')]]
    else:
        solvefunc = globals()['ode_' + hint]
    func = r['func']
    order = r['order']
    match = r[hint]

    free = eq.free_symbols
    cons = lambda s: s.free_symbols.difference(free)

    if simplify:
        # odesimp() will attempt to integrate, if necessary, apply constantsimp(),
        # attempt to solve for func, and apply any other hint specific
        # simplifications
        sols = solvefunc(eq, func, order, match)
        if isinstance(sols, Expr):
            rv =  odesimp(eq, sols, func, hint)
        else:
            rv = [odesimp(eq, s, func, hint) for s in sols]
    else:
        # We still want to integrate (you can disable it separately with the hint)
        match['simplify'] = False  # Some hints can take advantage of this option
        rv = _handle_Integral(solvefunc(eq, func, order, match), func, hint)

    if ics and not 'power_series' in hint:
        if isinstance(rv, Expr):
            solved_constants = solve_ics([rv], [r['func']], cons(rv), ics)
            rv = rv.subs(solved_constants)
        else:
            rv1 = []
            for s in rv:
                try:
                    solved_constants = solve_ics([s], [r['func']], cons(s), ics)
                except ValueError:
                    continue
                rv1.append(s.subs(solved_constants))
            if len(rv1) == 1:
                return rv1[0]
            rv = rv1
    return rv

def solve_ics(sols, funcs, constants, ics):
    """
    Solve for the constants given initial conditions

    ``sols`` is a list of solutions.

    ``funcs`` is a list of functions.

    ``constants`` is a list of constants.

    ``ics`` is the set of initial/boundary conditions for the differential
    equation. It should be given in the form of ``{f(x0): x1,
    f(x).diff(x).subs(x, x2):  x3}`` and so on.

    Returns a dictionary mapping constants to values.
    ``solution.subs(constants)`` will replace the constants in ``solution``.

    Example
    =======
    >>> # From dsolve(f(x).diff(x) - f(x), f(x))
    >>> from sympy import symbols, Eq, exp, Function
    >>> from sympy.solvers.ode import solve_ics
    >>> f = Function('f')
    >>> x, C1 = symbols('x C1')
    >>> sols = [Eq(f(x), C1*exp(x))]
    >>> funcs = [f(x)]
    >>> constants = [C1]
    >>> ics = {f(0): 2}
    >>> solved_constants = solve_ics(sols, funcs, constants, ics)
    >>> solved_constants
    {C1: 2}
    >>> sols[0].subs(solved_constants)
    Eq(f(x), 2*exp(x))

    """
    # Assume ics are of the form f(x0): value or Subs(diff(f(x), x, n), (x,
    # x0)): value (currently checked by classify_ode). To solve, replace x
    # with x0, f(x0) with value, then solve for constants. For f^(n)(x0),
    # differentiate the solution n times, so that f^(n)(x) appears.
    x = funcs[0].args[0]
    diff_sols = []
    subs_sols = []
    diff_variables = set()
    for funcarg, value in ics.items():
        if isinstance(funcarg, AppliedUndef):
            x0 = funcarg.args[0]
            matching_func = [f for f in funcs if f.func == funcarg.func][0]
            S = sols
        elif isinstance(funcarg, (Subs, Derivative)):
            if isinstance(funcarg, Subs):
                # Make sure it stays a subs. Otherwise subs below will produce
                # a different looking term.
                funcarg = funcarg.doit()
            if isinstance(funcarg, Subs):
                deriv = funcarg.expr
                x0 = funcarg.point[0]
                variables = funcarg.expr.variables
                matching_func = deriv
            elif isinstance(funcarg, Derivative):
                deriv = funcarg
                x0 = funcarg.variables[0]
                variables = (x,)*len(funcarg.variables)
                matching_func = deriv.subs(x0, x)
            if variables not in diff_variables:
                for sol in sols:
                    if sol.has(deriv.expr.func):
                        diff_sols.append(Eq(sol.lhs.diff(*variables), sol.rhs.diff(*variables)))
            diff_variables.add(variables)
            S = diff_sols
        else:
            raise NotImplementedError("Unrecognized initial condition")

        for sol in S:
            if sol.has(matching_func):
                sol2 = sol
                sol2 = sol2.subs(x, x0)
                sol2 = sol2.subs(funcarg, value)
                # This check is necessary because of issue #15724
                if not isinstance(sol2, BooleanAtom) or not subs_sols:
                    subs_sols = [s for s in subs_sols if not isinstance(s, BooleanAtom)]
                    subs_sols.append(sol2)

    # TODO: Use solveset here
    try:
        solved_constants = solve(subs_sols, constants, dict=True)
    except NotImplementedError:
        solved_constants = []

    # XXX: We can't differentiate between the solution not existing because of
    # invalid initial conditions, and not existing because solve is not smart
    # enough. If we could use solveset, this might be improvable, but for now,
    # we use NotImplementedError in this case.
    if not solved_constants:
        raise ValueError("Couldn't solve for initial conditions")

    if solved_constants == True:
        raise ValueError("Initial conditions did not produce any solutions for constants. Perhaps they are degenerate.")

    if len(solved_constants) > 1:
        raise NotImplementedError("Initial conditions produced too many solutions for constants")

    return solved_constants[0]

def classify_ode(eq, func=None, dict=False, ics=None, **kwargs):
    r"""
    Returns a tuple of possible :py:meth:`~sympy.solvers.ode.dsolve`
    classifications for an ODE.

    The tuple is ordered so that first item is the classification that
    :py:meth:`~sympy.solvers.ode.dsolve` uses to solve the ODE by default.  In
    general, classifications at the near the beginning of the list will
    produce better solutions faster than those near the end, thought there are
    always exceptions.  To make :py:meth:`~sympy.solvers.ode.dsolve` use a
    different classification, use ``dsolve(ODE, func,
    hint=<classification>)``.  See also the
    :py:meth:`~sympy.solvers.ode.dsolve` docstring for different meta-hints
    you can use.

    If ``dict`` is true, :py:meth:`~sympy.solvers.ode.classify_ode` will
    return a dictionary of ``hint:match`` expression terms. This is intended
    for internal use by :py:meth:`~sympy.solvers.ode.dsolve`.  Note that
    because dictionaries are ordered arbitrarily, this will most likely not be
    in the same order as the tuple.

    You can get help on different hints by executing
    ``help(ode.ode_hintname)``, where ``hintname`` is the name of the hint
    without ``_Integral``.

    See :py:data:`~sympy.solvers.ode.allhints` or the
    :py:mod:`~sympy.solvers.ode` docstring for a list of all supported hints
    that can be returned from :py:meth:`~sympy.solvers.ode.classify_ode`.

    Notes
    =====

    These are remarks on hint names.

    ``_Integral``

        If a classification has ``_Integral`` at the end, it will return the
        expression with an unevaluated :py:class:`~sympy.integrals.Integral`
        class in it.  Note that a hint may do this anyway if
        :py:meth:`~sympy.core.expr.Expr.integrate` cannot do the integral,
        though just using an ``_Integral`` will do so much faster.  Indeed, an
        ``_Integral`` hint will always be faster than its corresponding hint
        without ``_Integral`` because
        :py:meth:`~sympy.core.expr.Expr.integrate` is an expensive routine.
        If :py:meth:`~sympy.solvers.ode.dsolve` hangs, it is probably because
        :py:meth:`~sympy.core.expr.Expr.integrate` is hanging on a tough or
        impossible integral.  Try using an ``_Integral`` hint or
        ``all_Integral`` to get it return something.

        Note that some hints do not have ``_Integral`` counterparts.  This is
        because :py:meth:`~sympy.solvers.ode.integrate` is not used in solving
        the ODE for those method. For example, `n`\th order linear homogeneous
        ODEs with constant coefficients do not require integration to solve,
        so there is no ``nth_linear_homogeneous_constant_coeff_Integrate``
        hint. You can easily evaluate any unevaluated
        :py:class:`~sympy.integrals.Integral`\s in an expression by doing
        ``expr.doit()``.

    Ordinals

        Some hints contain an ordinal such as ``1st_linear``.  This is to help
        differentiate them from other hints, as well as from other methods
        that may not be implemented yet. If a hint has ``nth`` in it, such as
        the ``nth_linear`` hints, this means that the method used to applies
        to ODEs of any order.

    ``indep`` and ``dep``

        Some hints contain the words ``indep`` or ``dep``.  These reference
        the independent variable and the dependent function, respectively. For
        example, if an ODE is in terms of `f(x)`, then ``indep`` will refer to
        `x` and ``dep`` will refer to `f`.

    ``subs``

        If a hints has the word ``subs`` in it, it means the the ODE is solved
        by substituting the expression given after the word ``subs`` for a
        single dummy variable.  This is usually in terms of ``indep`` and
        ``dep`` as above.  The substituted expression will be written only in
        characters allowed for names of Python objects, meaning operators will
        be spelled out.  For example, ``indep``/``dep`` will be written as
        ``indep_div_dep``.

    ``coeff``

        The word ``coeff`` in a hint refers to the coefficients of something
        in the ODE, usually of the derivative terms.  See the docstring for
        the individual methods for more info (``help(ode)``).  This is
        contrast to ``coefficients``, as in ``undetermined_coefficients``,
        which refers to the common name of a method.

    ``_best``

        Methods that have more than one fundamental way to solve will have a
        hint for each sub-method and a ``_best`` meta-classification. This
        will evaluate all hints and return the best, using the same
        considerations as the normal ``best`` meta-hint.


    Examples
    ========

    >>> from sympy import Function, classify_ode, Eq
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> classify_ode(Eq(f(x).diff(x), 0), f(x))
    ('nth_algebraic', 'separable', '1st_linear', '1st_homogeneous_coeff_best',
    '1st_homogeneous_coeff_subs_indep_div_dep',
    '1st_homogeneous_coeff_subs_dep_div_indep',
    '1st_power_series', 'lie_group',
    'nth_linear_constant_coeff_homogeneous',
    'nth_linear_euler_eq_homogeneous', 'nth_algebraic_Integral',
    'separable_Integral', '1st_linear_Integral',
    '1st_homogeneous_coeff_subs_indep_div_dep_Integral',
    '1st_homogeneous_coeff_subs_dep_div_indep_Integral')
    >>> classify_ode(f(x).diff(x, 2) + 3*f(x).diff(x) + 2*f(x) - 4)
    ('nth_linear_constant_coeff_undetermined_coefficients',
    'nth_linear_constant_coeff_variation_of_parameters',
    'nth_linear_constant_coeff_variation_of_parameters_Integral')

    """
    ics = sympify(ics)

    prep = kwargs.pop('prep', True)

    if func and len(func.args) != 1:
        raise ValueError("dsolve() and classify_ode() only "
        "work with functions of one variable, not %s" % func)
    if prep or func is None:
        eq, func_ = _preprocess(eq, func)
        if func is None:
            func = func_
    x = func.args[0]
    f = func.func
    y = Dummy('y')
    xi = kwargs.get('xi')
    eta = kwargs.get('eta')
    terms = kwargs.get('n')

    if isinstance(eq, Equality):
        if eq.rhs != 0:
            return classify_ode(eq.lhs - eq.rhs, func, dict=dict, ics=ics, xi=xi,
                n=terms, eta=eta, prep=False)
        eq = eq.lhs
    order = ode_order(eq, f(x))
    # hint:matchdict or hint:(tuple of matchdicts)
    # Also will contain "default":<default hint> and "order":order items.
    matching_hints = {"order": order}

    if not order:
        if dict:
            matching_hints["default"] = None
            return matching_hints
        else:
            return ()

    df = f(x).diff(x)
    a = Wild('a', exclude=[f(x)])
    b = Wild('b', exclude=[f(x)])
    c = Wild('c', exclude=[f(x)])
    d = Wild('d', exclude=[df, f(x).diff(x, 2)])
    e = Wild('e', exclude=[df])
    k = Wild('k', exclude=[df])
    n = Wild('n', exclude=[x, f(x), df])
    c1 = Wild('c1', exclude=[x])
    a2 = Wild('a2', exclude=[x, f(x), df])
    b2 = Wild('b2', exclude=[x, f(x), df])
    c2 = Wild('c2', exclude=[x, f(x), df])
    d2 = Wild('d2', exclude=[x, f(x), df])
    a3 = Wild('a3', exclude=[f(x), df, f(x).diff(x, 2)])
    b3 = Wild('b3', exclude=[f(x), df, f(x).diff(x, 2)])
    c3 = Wild('c3', exclude=[f(x), df, f(x).diff(x, 2)])
    r3 = {'xi': xi, 'eta': eta}  # Used for the lie_group hint
    boundary = {}  # Used to extract initial conditions
    C1 = Symbol("C1")
    eq = expand(eq)

    # Preprocessing to get the initial conditions out
    if ics is not None:
        for funcarg in ics:
            # Separating derivatives
            if isinstance(funcarg, (Subs, Derivative)):
                # f(x).diff(x).subs(x, 0) is a Subs, but f(x).diff(x).subs(x,
                # y) is a Derivative
                if isinstance(funcarg, Subs):
                    deriv = funcarg.expr
                    old = funcarg.variables[0]
                    new = funcarg.point[0]
                elif isinstance(funcarg, Derivative):
                    deriv = funcarg
                    # No information on this. Just assume it was x
                    old = x
                    new = funcarg.variables[0]

                if (isinstance(deriv, Derivative) and isinstance(deriv.args[0],
                    AppliedUndef) and deriv.args[0].func == f and
                    len(deriv.args[0].args) == 1 and old == x and not
                    new.has(x) and all(i == deriv.variables[0] for i in
                    deriv.variables) and not ics[funcarg].has(f)):

                    dorder = ode_order(deriv, x)
                    temp = 'f' + str(dorder)
                    boundary.update({temp: new, temp + 'val': ics[funcarg]})
                else:
                    raise ValueError("Enter valid boundary conditions for Derivatives")


            # Separating functions
            elif isinstance(funcarg, AppliedUndef):
                if (funcarg.func == f and len(funcarg.args) == 1 and
                    not funcarg.args[0].has(x) and not ics[funcarg].has(f)):
                    boundary.update({'f0': funcarg.args[0], 'f0val': ics[funcarg]})
                else:
                    raise ValueError("Enter valid boundary conditions for Function")

            else:
                raise ValueError("Enter boundary conditions of the form ics={f(point}: value, f(x).diff(x, order).subs(x, point): value}")

    # Precondition to try remove f(x) from highest order derivative
    reduced_eq = None
    if eq.is_Add:
        deriv_coef = eq.coeff(f(x).diff(x, order))
        if deriv_coef not in (1, 0):
            r = deriv_coef.match(a*f(x)**c1)
            if r and r[c1]:
                den = f(x)**r[c1]
                reduced_eq = Add(*[arg/den for arg in eq.args])
    if not reduced_eq:
        reduced_eq = eq

    if order == 1:

        ## Linear case: a(x)*y'+b(x)*y+c(x) == 0
        if eq.is_Add:
            ind, dep = reduced_eq.as_independent(f)
        else:
            u = Dummy('u')
            ind, dep = (reduced_eq + u).as_independent(f)
            ind, dep = [tmp.subs(u, 0) for tmp in [ind, dep]]
        r = {a: dep.coeff(df),
             b: dep.coeff(f(x)),
             c: ind}
        # double check f[a] since the preconditioning may have failed
        if not r[a].has(f) and not r[b].has(f) and (
                r[a]*df + r[b]*f(x) + r[c]).expand() - reduced_eq == 0:
            r['a'] = a
            r['b'] = b
            r['c'] = c
            matching_hints["1st_linear"] = r
            matching_hints["1st_linear_Integral"] = r

        ## Bernoulli case: a(x)*y'+b(x)*y+c(x)*y**n == 0
        r = collect(
            reduced_eq, f(x), exact=True).match(a*df + b*f(x) + c*f(x)**n)
        if r and r[c] != 0 and r[n] != 1:  # See issue 4676
            r['a'] = a
            r['b'] = b
            r['c'] = c
            r['n'] = n
            matching_hints["Bernoulli"] = r
            matching_hints["Bernoulli_Integral"] = r

        ## Riccati special n == -2 case: a2*y'+b2*y**2+c2*y/x+d2/x**2 == 0
        r = collect(reduced_eq,
            f(x), exact=True).match(a2*df + b2*f(x)**2 + c2*f(x)/x + d2/x**2)
        if r and r[b2] != 0 and (r[c2] != 0 or r[d2] != 0):
            r['a2'] = a2
            r['b2'] = b2
            r['c2'] = c2
            r['d2'] = d2
            matching_hints["Riccati_special_minus2"] = r

        # NON-REDUCED FORM OF EQUATION matches
        r = collect(eq, df, exact=True).match(d + e * df)
        if r:
            r['d'] = d
            r['e'] = e
            r['y'] = y
            r[d] = r[d].subs(f(x), y)
            r[e] = r[e].subs(f(x), y)

            # FIRST ORDER POWER SERIES WHICH NEEDS INITIAL CONDITIONS
            # TODO: Hint first order series should match only if d/e is analytic.
            # For now, only d/e and (d/e).diff(arg) is checked for existence at
            # at a given point.
            # This is currently done internally in ode_1st_power_series.
            point = boundary.get('f0', 0)
            value = boundary.get('f0val', C1)
            check = cancel(r[d]/r[e])
            check1 = check.subs({x: point, y: value})
            if not check1.has(oo) and not check1.has(zoo) and \
                not check1.has(NaN) and not check1.has(-oo):
                check2 = (check1.diff(x)).subs({x: point, y: value})
                if not check2.has(oo) and not check2.has(zoo) and \
                    not check2.has(NaN) and not check2.has(-oo):
                    rseries = r.copy()
                    rseries.update({'terms': terms, 'f0': point, 'f0val': value})
                    matching_hints["1st_power_series"] = rseries

            r3.update(r)
            ## Exact Differential Equation: P(x, y) + Q(x, y)*y' = 0 where
            # dP/dy == dQ/dx
            try:
                if r[d] != 0:
                    numerator = simplify(r[d].diff(y) - r[e].diff(x))
                    # The following few conditions try to convert a non-exact
                    # differential equation into an exact one.
                    # References : Differential equations with applications
                    # and historical notes - George E. Simmons

                    if numerator:
                        # If (dP/dy - dQ/dx) / Q = f(x)
                        # then exp(integral(f(x))*equation becomes exact
                        factor = simplify(numerator/r[e])
                        variables = factor.free_symbols
                        if len(variables) == 1 and x == variables.pop():
                            factor = exp(Integral(factor).doit())
                            r[d] *= factor
                            r[e] *= factor
                            matching_hints["1st_exact"] = r
                            matching_hints["1st_exact_Integral"] = r
                        else:
                            # If (dP/dy - dQ/dx) / -P = f(y)
                            # then exp(integral(f(y))*equation becomes exact
                            factor = simplify(-numerator/r[d])
                            variables = factor.free_symbols
                            if len(variables) == 1 and y == variables.pop():
                                factor = exp(Integral(factor).doit())
                                r[d] *= factor
                                r[e] *= factor
                                matching_hints["1st_exact"] = r
                                matching_hints["1st_exact_Integral"] = r
                    else:
                        matching_hints["1st_exact"] = r
                        matching_hints["1st_exact_Integral"] = r

            except NotImplementedError:
                # Differentiating the coefficients might fail because of things
                # like f(2*x).diff(x).  See issue 4624 and issue 4719.
                pass

        # Any first order ODE can be ideally solved by the Lie Group
        # method
        matching_hints["lie_group"] = r3

        # This match is used for several cases below; we now collect on
        # f(x) so the matching works.
        r = collect(reduced_eq, df, exact=True).match(d + e*df)
        if r:
            # Using r[d] and r[e] without any modification for hints
            # linear-coefficients and separable-reduced.
            num, den = r[d], r[e]  # ODE = d/e + df
            r['d'] = d
            r['e'] = e
            r['y'] = y
            r[d] = num.subs(f(x), y)
            r[e] = den.subs(f(x), y)

            ## Separable Case: y' == P(y)*Q(x)
            r[d] = separatevars(r[d])
            r[e] = separatevars(r[e])
            # m1[coeff]*m1[x]*m1[y] + m2[coeff]*m2[x]*m2[y]*y'
            m1 = separatevars(r[d], dict=True, symbols=(x, y))
            m2 = separatevars(r[e], dict=True, symbols=(x, y))
            if m1 and m2:
                r1 = {'m1': m1, 'm2': m2, 'y': y}
                matching_hints["separable"] = r1
                matching_hints["separable_Integral"] = r1

            ## First order equation with homogeneous coefficients:
            # dy/dx == F(y/x) or dy/dx == F(x/y)
            ordera = homogeneous_order(r[d], x, y)
            if ordera is not None:
                orderb = homogeneous_order(r[e], x, y)
                if ordera == orderb:
                    # u1=y/x and u2=x/y
                    u1 = Dummy('u1')
                    u2 = Dummy('u2')
                    s = "1st_homogeneous_coeff_subs"
                    s1 = s + "_dep_div_indep"
                    s2 = s + "_indep_div_dep"
                    if simplify((r[d] + u1*r[e]).subs({x: 1, y: u1})) != 0:
                        matching_hints[s1] = r
                        matching_hints[s1 + "_Integral"] = r
                    if simplify((r[e] + u2*r[d]).subs({x: u2, y: 1})) != 0:
                        matching_hints[s2] = r
                        matching_hints[s2 + "_Integral"] = r
                    if s1 in matching_hints and s2 in matching_hints:
                        matching_hints["1st_homogeneous_coeff_best"] = r

            ## Linear coefficients of the form
            # y'+ F((a*x + b*y + c)/(a'*x + b'y + c')) = 0
            # that can be reduced to homogeneous form.
            F = num/den
            params = _linear_coeff_match(F, func)
            if params:
                xarg, yarg = params
                u = Dummy('u')
                t = Dummy('t')
                # Dummy substitution for df and f(x).
                dummy_eq = reduced_eq.subs(((df, t), (f(x), u)))
                reps = ((x, x + xarg), (u, u + yarg), (t, df), (u, f(x)))
                dummy_eq = simplify(dummy_eq.subs(reps))
                # get the re-cast values for e and d
                r2 = collect(expand(dummy_eq), [df, f(x)]).match(e*df + d)
                if r2:
                    orderd = homogeneous_order(r2[d], x, f(x))
                    if orderd is not None:
                        ordere = homogeneous_order(r2[e], x, f(x))
                        if orderd == ordere:
                            # Match arguments are passed in such a way that it
                            # is coherent with the already existing homogeneous
                            # functions.
                            r2[d] = r2[d].subs(f(x), y)
                            r2[e] = r2[e].subs(f(x), y)
                            r2.update({'xarg': xarg, 'yarg': yarg,
                                'd': d, 'e': e, 'y': y})
                            matching_hints["linear_coefficients"] = r2
                            matching_hints["linear_coefficients_Integral"] = r2

            ## Equation of the form y' + (y/x)*H(x^n*y) = 0
            # that can be reduced to separable form

            factor = simplify(x/f(x)*num/den)

            # Try representing factor in terms of x^n*y
            # where n is lowest power of x in factor;
            # first remove terms like sqrt(2)*3 from factor.atoms(Mul)
            u = None
            for mul in ordered(factor.atoms(Mul)):
                if mul.has(x):
                    _, u = mul.as_independent(x, f(x))
                    break
            if u and u.has(f(x)):
                h = x**(degree(Poly(u.subs(f(x), y), gen=x)))*f(x)
                p = Wild('p')
                if (u/h == 1) or ((u/h).simplify().match(x**p)):
                    t = Dummy('t')
                    r2 = {'t': t}
                    xpart, ypart = u.as_independent(f(x))
                    test = factor.subs(((u, t), (1/u, 1/t)))
                    free = test.free_symbols
                    if len(free) == 1 and free.pop() == t:
                        r2.update({'power': xpart.as_base_exp()[1], 'u': test})
                        matching_hints["separable_reduced"] = r2
                        matching_hints["separable_reduced_Integral"] = r2

        ## Almost-linear equation of the form f(x)*g(y)*y' + k(x)*l(y) + m(x) = 0
        r = collect(eq, [df, f(x)]).match(e*df + d)
        if r:
            r2 = r.copy()
            r2[c] = S.Zero
            if r2[d].is_Add:
                # Separate the terms having f(x) to r[d] and
                # remaining to r[c]
                no_f, r2[d] = r2[d].as_independent(f(x))
                r2[c] += no_f
            factor = simplify(r2[d].diff(f(x))/r[e])
            if factor and not factor.has(f(x)):
                r2[d] = factor_terms(r2[d])
                u = r2[d].as_independent(f(x), as_Add=False)[1]
                r2.update({'a': e, 'b': d, 'c': c, 'u': u})
                r2[d] /= u
                r2[e] /= u.diff(f(x))
                matching_hints["almost_linear"] = r2
                matching_hints["almost_linear_Integral"] = r2


    elif order == 2:
        # Liouville ODE in the form
        # f(x).diff(x, 2) + g(f(x))*(f(x).diff(x))**2 + h(x)*f(x).diff(x)
        # See Goldstein and Braun, "Advanced Methods for the Solution of
        # Differential Equations", pg. 98

        s = d*f(x).diff(x, 2) + e*df**2 + k*df
        r = reduced_eq.match(s)
        if r and r[d] != 0:
            y = Dummy('y')
            g = simplify(r[e]/r[d]).subs(f(x), y)
            h = simplify(r[k]/r[d]).subs(f(x), y)
            if y in h.free_symbols or x in g.free_symbols:
                pass
            else:
                r = {'g': g, 'h': h, 'y': y}
                matching_hints["Liouville"] = r
                matching_hints["Liouville_Integral"] = r

        # Homogeneous second order differential equation of the form
        # a3*f(x).diff(x, 2) + b3*f(x).diff(x) + c3, where
        # for simplicity, a3, b3 and c3 are assumed to be polynomials.
        # It has a definite power series solution at point x0 if, b3/a3 and c3/a3
        # are analytic at x0.
        deq = a3*(f(x).diff(x, 2)) + b3*df + c3*f(x)
        r = collect(reduced_eq,
            [f(x).diff(x, 2), f(x).diff(x), f(x)]).match(deq)
        ordinary = False
        if r and r[a3] != 0:
            if all([r[key].is_polynomial() for key in r]):
                p = cancel(r[b3]/r[a3])  # Used below
                q = cancel(r[c3]/r[a3])  # Used below
                point = kwargs.get('x0', 0)
                check = p.subs(x, point)
                if not check.has(oo) and not check.has(NaN) and \
                    not check.has(zoo) and not check.has(-oo):
                    check = q.subs(x, point)
                    if not check.has(oo) and not check.has(NaN) and \
                        not check.has(zoo) and not check.has(-oo):
                        ordinary = True
                        r.update({'a3': a3, 'b3': b3, 'c3': c3, 'x0': point, 'terms': terms})
                        matching_hints["2nd_power_series_ordinary"] = r

                # Checking if the differential equation has a regular singular point
                # at x0. It has a regular singular point at x0, if (b3/a3)*(x - x0)
                # and (c3/a3)*((x - x0)**2) are analytic at x0.
                if not ordinary:
                    p = cancel((x - point)*p)
                    check = p.subs(x, point)
                    if not check.has(oo) and not check.has(NaN) and \
                        not check.has(zoo) and not check.has(-oo):
                        q = cancel(((x - point)**2)*q)
                        check = q.subs(x, point)
                        if not check.has(oo) and not check.has(NaN) and \
                            not check.has(zoo) and not check.has(-oo):
                            coeff_dict = {'p': p, 'q': q, 'x0': point, 'terms': terms}
                            matching_hints["2nd_power_series_regular"] = coeff_dict


    if order > 0:
        # Any ODE that can be solved with a substitution and
        # repeated integration e.g.:
        # `d^2/dx^2(y) + x*d/dx(y) = constant
        #f'(x) must be finite for this to work
        r = _nth_order_reducible_match(reduced_eq, func)
        if r:
            matching_hints['nth_order_reducible'] = r

        # Any ODE that can be solved with a combination of algebra and
        # integrals e.g.:
        # d^3/dx^3(x y) = F(x)
        r = _nth_algebraic_match(reduced_eq, func)
        if r['solutions']:
            matching_hints['nth_algebraic'] = r
            matching_hints['nth_algebraic_Integral'] = r

        # nth order linear ODE
        # a_n(x)y^(n) + ... + a_1(x)y' + a_0(x)y = F(x) = b

        r = _nth_linear_match(reduced_eq, func, order)

        # Constant coefficient case (a_i is constant for all i)
        if r and not any(r[i].has(x) for i in r if i >= 0):
            # Inhomogeneous case: F(x) is not identically 0
            if r[-1]:
                undetcoeff = _undetermined_coefficients_match(r[-1], x)
                s = "nth_linear_constant_coeff_variation_of_parameters"
                matching_hints[s] = r
                matching_hints[s + "_Integral"] = r
                if undetcoeff['test']:
                    r['trialset'] = undetcoeff['trialset']
                    matching_hints[
                        "nth_linear_constant_coeff_undetermined_coefficients"
                            ] = r

            # Homogeneous case: F(x) is identically 0
            else:
                matching_hints["nth_linear_constant_coeff_homogeneous"] = r

        # nth order Euler equation a_n*x**n*y^(n) + ... + a_1*x*y' + a_0*y = F(x)
        #In case of Homogeneous euler equation F(x) = 0
        def _test_term(coeff, order):
            r"""
            Linear Euler ODEs have the form  K*x**order*diff(y(x),x,order) = F(x),
            where K is independent of x and y(x), order>= 0.
            So we need to check that for each term, coeff == K*x**order from
            some K.  We have a few cases, since coeff may have several
            different types.
            """
            if order < 0:
                raise ValueError("order should be greater than 0")
            if coeff == 0:
                return True
            if order == 0:
                if x in coeff.free_symbols:
                    return False
                return True
            if coeff.is_Mul:
                if coeff.has(f(x)):
                    return False
                return x**order in coeff.args
            elif coeff.is_Pow:
                return coeff.as_base_exp() == (x, order)
            elif order == 1:
                return x == coeff
            return False

        # Find coefficient for higest derivative, multiply coefficients to
        # bring the equation into Euler form if possible
        r_rescaled = None
        if r is not None:
            coeff = r[order]
            factor = x**order / coeff
            r_rescaled = {i: factor*r[i] for i in r}

        if r_rescaled and not any(not _test_term(r_rescaled[i], i) for i in
                r_rescaled if i != 'trialset' and i >= 0):
            if not r_rescaled[-1]:
                matching_hints["nth_linear_euler_eq_homogeneous"] = r_rescaled
            else:
                matching_hints["nth_linear_euler_eq_nonhomogeneous_variation_of_parameters"] = r_rescaled
                matching_hints["nth_linear_euler_eq_nonhomogeneous_variation_of_parameters_Integral"] = r_rescaled
                e, re = posify(r_rescaled[-1].subs(x, exp(x)))
                undetcoeff = _undetermined_coefficients_match(e.subs(re), x)
                if undetcoeff['test']:
                    r_rescaled['trialset'] = undetcoeff['trialset']
                    matching_hints["nth_linear_euler_eq_nonhomogeneous_undetermined_coefficients"] = r_rescaled


    # Order keys based on allhints.
    retlist = [i for i in allhints if i in matching_hints]

    if dict:
        # Dictionaries are ordered arbitrarily, so make note of which
        # hint would come first for dsolve().  Use an ordered dict in Py 3.
        matching_hints["default"] = retlist[0] if retlist else None
        matching_hints["ordered_hints"] = tuple(retlist)
        return matching_hints
    else:
        return tuple(retlist)

def classify_sysode(eq, funcs=None, **kwargs):
    r"""
    Returns a dictionary of parameter names and values that define the system
    of ordinary differential equations in ``eq``.
    The parameters are further used in
    :py:meth:`~sympy.solvers.ode.dsolve` for solving that system.

    The parameter names and values are:

    'is_linear' (boolean), which tells whether the given system is linear.
    Note that "linear" here refers to the operator: terms such as ``x*diff(x,t)`` are
    nonlinear, whereas terms like ``sin(t)*diff(x,t)`` are still linear operators.

    'func' (list) contains the :py:class:`~sympy.core.function.Function`s that
    appear with a derivative in the ODE, i.e. those that we are trying to solve
    the ODE for.

    'order' (dict) with the maximum derivative for each element of the 'func'
    parameter.

    'func_coeff' (dict) with the coefficient for each triple ``(equation number,
    function, order)```. The coefficients are those subexpressions that do not
    appear in 'func', and hence can be considered constant for purposes of ODE
    solving.

    'eq' (list) with the equations from ``eq``, sympified and transformed into
    expressions (we are solving for these expressions to be zero).

    'no_of_equations' (int) is the number of equations (same as ``len(eq)``).

    'type_of_equation' (string) is an internal classification of the type of
    ODE.

    References
    ==========
    -http://eqworld.ipmnet.ru/en/solutions/sysode/sode-toc1.htm
    -A. D. Polyanin and A. V. Manzhirov, Handbook of Mathematics for Engineers and Scientists

    Examples
    ========

    >>> from sympy import Function, Eq, symbols, diff
    >>> from sympy.solvers.ode import classify_sysode
    >>> from sympy.abc import t
    >>> f, x, y = symbols('f, x, y', cls=Function)
    >>> k, l, m, n = symbols('k, l, m, n', Integer=True)
    >>> x1 = diff(x(t), t) ; y1 = diff(y(t), t)
    >>> x2 = diff(x(t), t, t) ; y2 = diff(y(t), t, t)
    >>> eq = (Eq(5*x1, 12*x(t) - 6*y(t)), Eq(2*y1, 11*x(t) + 3*y(t)))
    >>> classify_sysode(eq)
    {'eq': [-12*x(t) + 6*y(t) + 5*Derivative(x(t), t), -11*x(t) - 3*y(t) + 2*Derivative(y(t), t)],
    'func': [x(t), y(t)], 'func_coeff': {(0, x(t), 0): -12, (0, x(t), 1): 5, (0, y(t), 0): 6,
    (0, y(t), 1): 0, (1, x(t), 0): -11, (1, x(t), 1): 0, (1, y(t), 0): -3, (1, y(t), 1): 2},
    'is_linear': True, 'no_of_equation': 2, 'order': {x(t): 1, y(t): 1}, 'type_of_equation': 'type1'}
    >>> eq = (Eq(diff(x(t),t), 5*t*x(t) + t**2*y(t)), Eq(diff(y(t),t), -t**2*x(t) + 5*t*y(t)))
    >>> classify_sysode(eq)
    {'eq': [-t**2*y(t) - 5*t*x(t) + Derivative(x(t), t), t**2*x(t) - 5*t*y(t) + Derivative(y(t), t)],
    'func': [x(t), y(t)], 'func_coeff': {(0, x(t), 0): -5*t, (0, x(t), 1): 1, (0, y(t), 0): -t**2,
    (0, y(t), 1): 0, (1, x(t), 0): t**2, (1, x(t), 1): 0, (1, y(t), 0): -5*t, (1, y(t), 1): 1},
    'is_linear': True, 'no_of_equation': 2, 'order': {x(t): 1, y(t): 1}, 'type_of_equation': 'type4'}

    """

    # Sympify equations and convert iterables of equations into
    # a list of equations
    def _sympify(eq):
        return list(map(sympify, eq if iterable(eq) else [eq]))

    eq, funcs = (_sympify(w) for w in [eq, funcs])
    for i, fi in enumerate(eq):
        if isinstance(fi, Equality):
            eq[i] = fi.lhs - fi.rhs
    matching_hints = {"no_of_equation":i+1}
    matching_hints['eq'] = eq
    if i==0:
        raise ValueError("classify_sysode() works for systems of ODEs. "
        "For scalar ODEs, classify_ode should be used")
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]

    # find all the functions if not given
    order = dict()
    if funcs==[None]:
        funcs = []
        for eqs in eq:
            derivs = eqs.atoms(Derivative)
            func = set().union(*[d.atoms(AppliedUndef) for d in derivs])
            for func_ in  func:
                funcs.append(func_)
    funcs = list(set(funcs))
    if len(funcs) != len(eq):
        raise ValueError("Number of functions given is not equal to the number of equations %s" % funcs)
    func_dict = dict()
    for func in funcs:
        if not order.get(func, False):
            max_order = 0
            for i, eqs_ in enumerate(eq):
                order_ = ode_order(eqs_,func)
                if max_order < order_:
                    max_order = order_
                    eq_no = i
            if eq_no in func_dict:
                list_func = []
                list_func.append(func_dict[eq_no])
                list_func.append(func)
                func_dict[eq_no] = list_func
            else:
                func_dict[eq_no] = func
            order[func] = max_order
    funcs = [func_dict[i] for i in range(len(func_dict))]
    matching_hints['func'] = funcs
    for func in funcs:
        if isinstance(func, list):
            for func_elem in func:
                if len(func_elem.args) != 1:
                    raise ValueError("dsolve() and classify_sysode() work with "
                    "functions of one variable only, not %s" % func)
        else:
            if func and len(func.args) != 1:
                raise ValueError("dsolve() and classify_sysode() work with "
                "functions of one variable only, not %s" % func)

    # find the order of all equation in system of odes
    matching_hints["order"] = order

    # find coefficients of terms f(t), diff(f(t),t) and higher derivatives
    # and similarly for other functions g(t), diff(g(t),t) in all equations.
    # Here j denotes the equation number, funcs[l] denotes the function about
    # which we are talking about and k denotes the order of function funcs[l]
    # whose coefficient we are calculating.
    def linearity_check(eqs, j, func, is_linear_):
        for k in range(order[func] + 1):
            func_coef[j, func, k] = collect(eqs.expand(), [diff(func, t, k)]).coeff(diff(func, t, k))
            if is_linear_ == True:
                if func_coef[j, func, k] == 0:
                    if k == 0:
                        coef = eqs.as_independent(func, as_Add=True)[1]
                        for xr in range(1, ode_order(eqs,func) + 1):
                            coef -= eqs.as_independent(diff(func, t, xr), as_Add=True)[1]
                        if coef != 0:
                            is_linear_ = False
                    else:
                        if eqs.as_independent(diff(func, t, k), as_Add=True)[1]:
                            is_linear_ = False
                else:
                    for func_ in funcs:
                        if isinstance(func_, list):
                            for elem_func_ in func_:
                                dep = func_coef[j, func, k].as_independent(elem_func_, as_Add=True)[1]
                                if dep != 0:
                                    is_linear_ = False
                        else:
                            dep = func_coef[j, func, k].as_independent(func_, as_Add=True)[1]
                            if dep != 0:
                                is_linear_ = False
        return is_linear_

    func_coef = {}
    is_linear = True
    for j, eqs in enumerate(eq):
        for func in funcs:
            if isinstance(func, list):
                for func_elem in func:
                    is_linear = linearity_check(eqs, j, func_elem, is_linear)
            else:
                is_linear = linearity_check(eqs, j, func, is_linear)
    matching_hints['func_coeff'] = func_coef
    matching_hints['is_linear'] = is_linear

    if len(set(order.values()))==1:
        order_eq = list(matching_hints['order'].values())[0]
        if matching_hints['is_linear'] == True:
            if matching_hints['no_of_equation'] == 2:
                if order_eq == 1:
                    type_of_equation = check_linear_2eq_order1(eq, funcs, func_coef)
                elif order_eq == 2:
                    type_of_equation = check_linear_2eq_order2(eq, funcs, func_coef)
                else:
                    type_of_equation = None

            elif matching_hints['no_of_equation'] == 3:
                if order_eq == 1:
                    type_of_equation = check_linear_3eq_order1(eq, funcs, func_coef)
                    if type_of_equation==None:
                        type_of_equation = check_linear_neq_order1(eq, funcs, func_coef)
                else:
                    type_of_equation = None
            else:
                if order_eq == 1:
                    type_of_equation = check_linear_neq_order1(eq, funcs, func_coef)
                else:
                    type_of_equation = None
        else:
            if matching_hints['no_of_equation'] == 2:
                if order_eq == 1:
                    type_of_equation = check_nonlinear_2eq_order1(eq, funcs, func_coef)
                else:
                    type_of_equation = None
            elif matching_hints['no_of_equation'] == 3:
                if order_eq == 1:
                    type_of_equation = check_nonlinear_3eq_order1(eq, funcs, func_coef)
                else:
                    type_of_equation = None
            else:
                type_of_equation = None
    else:
        type_of_equation = None

    matching_hints['type_of_equation'] = type_of_equation

    return matching_hints


def check_linear_2eq_order1(eq, func, func_coef):
    x = func[0].func
    y = func[1].func
    fc = func_coef
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    r = dict()
    # for equations Eq(a1*diff(x(t),t), b1*x(t) + c1*y(t) + d1)
    # and Eq(a2*diff(y(t),t), b2*x(t) + c2*y(t) + d2)
    r['a1'] = fc[0,x(t),1] ; r['a2'] = fc[1,y(t),1]
    r['b1'] = -fc[0,x(t),0]/fc[0,x(t),1] ; r['b2'] = -fc[1,x(t),0]/fc[1,y(t),1]
    r['c1'] = -fc[0,y(t),0]/fc[0,x(t),1] ; r['c2'] = -fc[1,y(t),0]/fc[1,y(t),1]
    forcing = [S(0),S(0)]
    for i in range(2):
        for j in Add.make_args(eq[i]):
            if not j.has(x(t), y(t)):
                forcing[i] += j
    if not (forcing[0].has(t) or forcing[1].has(t)):
        # We can handle homogeneous case and simple constant forcings
        r['d1'] = forcing[0]
        r['d2'] = forcing[1]
    else:
        # Issue #9244: nonhomogeneous linear systems are not supported
        return None

    # Conditions to check for type 6 whose equations are Eq(diff(x(t),t), f(t)*x(t) + g(t)*y(t)) and
    # Eq(diff(y(t),t), a*[f(t) + a*h(t)]x(t) + a*[g(t) - h(t)]*y(t))
    p = 0
    q = 0
    p1 = cancel(r['b2']/(cancel(r['b2']/r['c2']).as_numer_denom()[0]))
    p2 = cancel(r['b1']/(cancel(r['b1']/r['c1']).as_numer_denom()[0]))
    for n, i in enumerate([p1, p2]):
        for j in Mul.make_args(collect_const(i)):
            if not j.has(t):
                q = j
            if q and n==0:
                if ((r['b2']/j - r['b1'])/(r['c1'] - r['c2']/j)) == j:
                    p = 1
            elif q and n==1:
                if ((r['b1']/j - r['b2'])/(r['c2'] - r['c1']/j)) == j:
                    p = 2
    # End of condition for type 6

    if r['d1']!=0 or r['d2']!=0:
        if not r['d1'].has(t) and not r['d2'].has(t):
            if all(not r[k].has(t) for k in 'a1 a2 b1 b2 c1 c2'.split()):
                # Equations for type 2 are Eq(a1*diff(x(t),t),b1*x(t)+c1*y(t)+d1) and Eq(a2*diff(y(t),t),b2*x(t)+c2*y(t)+d2)
                return "type2"
        else:
            return None
    else:
        if all(not r[k].has(t) for k in 'a1 a2 b1 b2 c1 c2'.split()):
             # Equations for type 1 are Eq(a1*diff(x(t),t),b1*x(t)+c1*y(t)) and Eq(a2*diff(y(t),t),b2*x(t)+c2*y(t))
            return "type1"
        else:
            r['b1'] = r['b1']/r['a1'] ; r['b2'] = r['b2']/r['a2']
            r['c1'] = r['c1']/r['a1'] ; r['c2'] = r['c2']/r['a2']
            if (r['b1'] == r['c2']) and (r['c1'] == r['b2']):
                # Equation for type 3 are Eq(diff(x(t),t), f(t)*x(t) + g(t)*y(t)) and Eq(diff(y(t),t), g(t)*x(t) + f(t)*y(t))
                return "type3"
            elif (r['b1'] == r['c2']) and (r['c1'] == -r['b2']) or (r['b1'] == -r['c2']) and (r['c1'] == r['b2']):
                # Equation for type 4 are Eq(diff(x(t),t), f(t)*x(t) + g(t)*y(t)) and Eq(diff(y(t),t), -g(t)*x(t) + f(t)*y(t))
                return "type4"
            elif (not cancel(r['b2']/r['c1']).has(t) and not cancel((r['c2']-r['b1'])/r['c1']).has(t)) \
            or (not cancel(r['b1']/r['c2']).has(t) and not cancel((r['c1']-r['b2'])/r['c2']).has(t)):
                # Equations for type 5 are Eq(diff(x(t),t), f(t)*x(t) + g(t)*y(t)) and Eq(diff(y(t),t), a*g(t)*x(t) + [f(t) + b*g(t)]*y(t)
                return "type5"
            elif p:
                return "type6"
            else:
                # Equations for type 7 are Eq(diff(x(t),t), f(t)*x(t) + g(t)*y(t)) and Eq(diff(y(t),t), h(t)*x(t) + p(t)*y(t))
                return "type7"

def check_linear_2eq_order2(eq, func, func_coef):
    x = func[0].func
    y = func[1].func
    fc = func_coef
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    r = dict()
    a = Wild('a', exclude=[1/t])
    b = Wild('b', exclude=[1/t**2])
    u = Wild('u', exclude=[t, t**2])
    v = Wild('v', exclude=[t, t**2])
    w = Wild('w', exclude=[t, t**2])
    p = Wild('p', exclude=[t, t**2])
    r['a1'] = fc[0,x(t),2] ; r['a2'] = fc[1,y(t),2]
    r['b1'] = fc[0,x(t),1] ; r['b2'] = fc[1,x(t),1]
    r['c1'] = fc[0,y(t),1] ; r['c2'] = fc[1,y(t),1]
    r['d1'] = fc[0,x(t),0] ; r['d2'] = fc[1,x(t),0]
    r['e1'] = fc[0,y(t),0] ; r['e2'] = fc[1,y(t),0]
    const = [S(0), S(0)]
    for i in range(2):
        for j in Add.make_args(eq[i]):
            if not (j.has(x(t)) or j.has(y(t))):
                const[i] += j
    r['f1'] = const[0]
    r['f2'] = const[1]
    if r['f1']!=0 or r['f2']!=0:
        if all(not r[k].has(t) for k in 'a1 a2 d1 d2 e1 e2 f1 f2'.split()) \
        and r['b1']==r['c1']==r['b2']==r['c2']==0:
            return "type2"

        elif all(not r[k].has(t) for k in 'a1 a2 b1 b2 c1 c2 d1 d2 e1 e1'.split()):
            p = [S(0), S(0)] ; q = [S(0), S(0)]
            for n, e in enumerate([r['f1'], r['f2']]):
                if e.has(t):
                    tpart = e.as_independent(t, Mul)[1]
                    for i in Mul.make_args(tpart):
                        if i.has(exp):
                            b, e = i.as_base_exp()
                            co = e.coeff(t)
                            if co and not co.has(t) and co.has(I):
                                p[n] = 1
                            else:
                                q[n] = 1
                        else:
                            q[n] = 1
                else:
                    q[n] = 1

            if p[0]==1 and p[1]==1 and q[0]==0 and q[1]==0:
                    return "type4"
            else:
                return None
        else:
            return None
    else:
        if r['b1']==r['b2']==r['c1']==r['c2']==0 and all(not r[k].has(t) \
        for k in 'a1 a2 d1 d2 e1 e2'.split()):
            return "type1"

        elif r['b1']==r['e1']==r['c2']==r['d2']==0 and all(not r[k].has(t) \
        for k in 'a1 a2 b2 c1 d1 e2'.split()) and r['c1'] == -r['b2'] and \
        r['d1'] == r['e2']:
            return "type3"

        elif cancel(-r['b2']/r['d2'])==t and cancel(-r['c1']/r['e1'])==t and not \
        (r['d2']/r['a2']).has(t) and not (r['e1']/r['a1']).has(t) and \
        r['b1']==r['d1']==r['c2']==r['e2']==0:
            return "type5"

        elif ((r['a1']/r['d1']).expand()).match((p*(u*t**2+v*t+w)**2).expand()) and not \
        (cancel(r['a1']*r['d2']/(r['a2']*r['d1']))).has(t) and not (r['d1']/r['e1']).has(t) and not \
        (r['d2']/r['e2']).has(t) and r['b1'] == r['b2'] == r['c1'] == r['c2'] == 0:
            return "type10"

        elif not cancel(r['d1']/r['e1']).has(t) and not cancel(r['d2']/r['e2']).has(t) and not \
        cancel(r['d1']*r['a2']/(r['d2']*r['a1'])).has(t) and r['b1']==r['b2']==r['c1']==r['c2']==0:
            return "type6"

        elif not cancel(r['b1']/r['c1']).has(t) and not cancel(r['b2']/r['c2']).has(t) and not \
        cancel(r['b1']*r['a2']/(r['b2']*r['a1'])).has(t) and r['d1']==r['d2']==r['e1']==r['e2']==0:
            return "type7"

        elif cancel(-r['b2']/r['d2'])==t and cancel(-r['c1']/r['e1'])==t and not \
        cancel(r['e1']*r['a2']/(r['d2']*r['a1'])).has(t) and r['e1'].has(t) \
        and r['b1']==r['d1']==r['c2']==r['e2']==0:
            return "type8"

        elif (r['b1']/r['a1']).match(a/t) and (r['b2']/r['a2']).match(a/t) and not \
        (r['b1']/r['c1']).has(t) and not (r['b2']/r['c2']).has(t) and \
        (r['d1']/r['a1']).match(b/t**2) and (r['d2']/r['a2']).match(b/t**2) \
        and not (r['d1']/r['e1']).has(t) and not (r['d2']/r['e2']).has(t):
            return "type9"

        elif -r['b1']/r['d1']==-r['c1']/r['e1']==-r['b2']/r['d2']==-r['c2']/r['e2']==t:
            return "type11"

        else:
            return None

def check_linear_3eq_order1(eq, func, func_coef):
    x = func[0].func
    y = func[1].func
    z = func[2].func
    fc = func_coef
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    r = dict()
    r['a1'] = fc[0,x(t),1]; r['a2'] = fc[1,y(t),1]; r['a3'] = fc[2,z(t),1]
    r['b1'] = fc[0,x(t),0]; r['b2'] = fc[1,x(t),0]; r['b3'] = fc[2,x(t),0]
    r['c1'] = fc[0,y(t),0]; r['c2'] = fc[1,y(t),0]; r['c3'] = fc[2,y(t),0]
    r['d1'] = fc[0,z(t),0]; r['d2'] = fc[1,z(t),0]; r['d3'] = fc[2,z(t),0]
    forcing = [S(0), S(0), S(0)]
    for i in range(3):
        for j in Add.make_args(eq[i]):
            if not j.has(x(t), y(t), z(t)):
                forcing[i] += j
    if forcing[0].has(t) or forcing[1].has(t) or forcing[2].has(t):
        # We can handle homogeneous case and simple constant forcings.
        # Issue #9244: nonhomogeneous linear systems are not supported
        return None

    if all(not r[k].has(t) for k in 'a1 a2 a3 b1 b2 b3 c1 c2 c3 d1 d2 d3'.split()):
        if r['c1']==r['d1']==r['d2']==0:
            return 'type1'
        elif r['c1'] == -r['b2'] and r['d1'] == -r['b3'] and r['d2'] == -r['c3'] \
        and r['b1'] == r['c2'] == r['d3'] == 0:
            return 'type2'
        elif r['b1'] == r['c2'] == r['d3'] == 0 and r['c1']/r['a1'] == -r['d1']/r['a1'] \
        and r['d2']/r['a2'] == -r['b2']/r['a2'] and r['b3']/r['a3'] == -r['c3']/r['a3']:
            return 'type3'
        else:
            return None
    else:
        for k1 in 'c1 d1 b2 d2 b3 c3'.split():
            if r[k1] == 0:
                continue
            else:
                if all(not cancel(r[k1]/r[k]).has(t) for k in 'd1 b2 d2 b3 c3'.split() if r[k]!=0) \
                and all(not cancel(r[k1]/(r['b1'] - r[k])).has(t) for k in 'b1 c2 d3'.split() if r['b1']!=r[k]):
                    return 'type4'
                else:
                    break
    return None

def check_linear_neq_order1(eq, func, func_coef):
    x = func[0].func
    y = func[1].func
    z = func[2].func
    fc = func_coef
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    r = dict()
    n = len(eq)
    for i in range(n):
        for j in range(n):
            if (fc[i,func[j],0]/fc[i,func[i],1]).has(t):
                return None
    if len(eq)==3:
        return 'type6'
    return 'type1'

def check_nonlinear_2eq_order1(eq, func, func_coef):
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    f = Wild('f')
    g = Wild('g')
    u, v = symbols('u, v', cls=Dummy)
    def check_type(x, y):
        r1 = eq[0].match(t*diff(x(t),t) - x(t) + f)
        r2 = eq[1].match(t*diff(y(t),t) - y(t) + g)
        if not (r1 and r2):
            r1 = eq[0].match(diff(x(t),t) - x(t)/t + f/t)
            r2 = eq[1].match(diff(y(t),t) - y(t)/t + g/t)
        if not (r1 and r2):
            r1 = (-eq[0]).match(t*diff(x(t),t) - x(t) + f)
            r2 = (-eq[1]).match(t*diff(y(t),t) - y(t) + g)
        if not (r1 and r2):
            r1 = (-eq[0]).match(diff(x(t),t) - x(t)/t + f/t)
            r2 = (-eq[1]).match(diff(y(t),t) - y(t)/t + g/t)
        if r1 and r2 and not (r1[f].subs(diff(x(t),t),u).subs(diff(y(t),t),v).has(t) \
        or r2[g].subs(diff(x(t),t),u).subs(diff(y(t),t),v).has(t)):
            return 'type5'
        else:
            return None
    for func_ in func:
        if isinstance(func_, list):
            x = func[0][0].func
            y = func[0][1].func
            eq_type = check_type(x, y)
            if not eq_type:
                eq_type = check_type(y, x)
            return eq_type
    x = func[0].func
    y = func[1].func
    fc = func_coef
    n = Wild('n', exclude=[x(t),y(t)])
    f1 = Wild('f1', exclude=[v,t])
    f2 = Wild('f2', exclude=[v,t])
    g1 = Wild('g1', exclude=[u,t])
    g2 = Wild('g2', exclude=[u,t])
    for i in range(2):
        eqs = 0
        for terms in Add.make_args(eq[i]):
            eqs += terms/fc[i,func[i],1]
        eq[i] = eqs
    r = eq[0].match(diff(x(t),t) - x(t)**n*f)
    if r:
        g = (diff(y(t),t) - eq[1])/r[f]
    if r and not (g.has(x(t)) or g.subs(y(t),v).has(t) or r[f].subs(x(t),u).subs(y(t),v).has(t)):
        return 'type1'
    r = eq[0].match(diff(x(t),t) - exp(n*x(t))*f)
    if r:
        g = (diff(y(t),t) - eq[1])/r[f]
    if r and not (g.has(x(t)) or g.subs(y(t),v).has(t) or r[f].subs(x(t),u).subs(y(t),v).has(t)):
        return 'type2'
    g = Wild('g')
    r1 = eq[0].match(diff(x(t),t) - f)
    r2 = eq[1].match(diff(y(t),t) - g)
    if r1 and r2 and not (r1[f].subs(x(t),u).subs(y(t),v).has(t) or \
    r2[g].subs(x(t),u).subs(y(t),v).has(t)):
        return 'type3'
    r1 = eq[0].match(diff(x(t),t) - f)
    r2 = eq[1].match(diff(y(t),t) - g)
    num, den = (
        (r1[f].subs(x(t),u).subs(y(t),v))/
        (r2[g].subs(x(t),u).subs(y(t),v))).as_numer_denom()
    R1 = num.match(f1*g1)
    R2 = den.match(f2*g2)
    phi = (r1[f].subs(x(t),u).subs(y(t),v))/num
    if R1 and R2:
        return 'type4'
    return None


def check_nonlinear_2eq_order2(eq, func, func_coef):
    return None

def check_nonlinear_3eq_order1(eq, func, func_coef):
    x = func[0].func
    y = func[1].func
    z = func[2].func
    fc = func_coef
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    u, v, w = symbols('u, v, w', cls=Dummy)
    a = Wild('a', exclude=[x(t), y(t), z(t), t])
    b = Wild('b', exclude=[x(t), y(t), z(t), t])
    c = Wild('c', exclude=[x(t), y(t), z(t), t])
    f = Wild('f')
    F1 = Wild('F1')
    F2 = Wild('F2')
    F3 = Wild('F3')
    for i in range(3):
        eqs = 0
        for terms in Add.make_args(eq[i]):
            eqs += terms/fc[i,func[i],1]
        eq[i] = eqs
    r1 = eq[0].match(diff(x(t),t) - a*y(t)*z(t))
    r2 = eq[1].match(diff(y(t),t) - b*z(t)*x(t))
    r3 = eq[2].match(diff(z(t),t) - c*x(t)*y(t))
    if r1 and r2 and r3:
        num1, den1 = r1[a].as_numer_denom()
        num2, den2 = r2[b].as_numer_denom()
        num3, den3 = r3[c].as_numer_denom()
        if solve([num1*u-den1*(v-w), num2*v-den2*(w-u), num3*w-den3*(u-v)],[u, v]):
            return 'type1'
    r = eq[0].match(diff(x(t),t) - y(t)*z(t)*f)
    if r:
        r1 = collect_const(r[f]).match(a*f)
        r2 = ((diff(y(t),t) - eq[1])/r1[f]).match(b*z(t)*x(t))
        r3 = ((diff(z(t),t) - eq[2])/r1[f]).match(c*x(t)*y(t))
    if r1 and r2 and r3:
        num1, den1 = r1[a].as_numer_denom()
        num2, den2 = r2[b].as_numer_denom()
        num3, den3 = r3[c].as_numer_denom()
        if solve([num1*u-den1*(v-w), num2*v-den2*(w-u), num3*w-den3*(u-v)],[u, v]):
            return 'type2'
    r = eq[0].match(diff(x(t),t) - (F2-F3))
    if r:
        r1 = collect_const(r[F2]).match(c*F2)
        r1.update(collect_const(r[F3]).match(b*F3))
        if r1:
            if eq[1].has(r1[F2]) and not eq[1].has(r1[F3]):
                r1[F2], r1[F3] = r1[F3], r1[F2]
                r1[c], r1[b] = -r1[b], -r1[c]
            r2 = eq[1].match(diff(y(t),t) - a*r1[F3] + r1[c]*F1)
        if r2:
            r3 = (eq[2] == diff(z(t),t) - r1[b]*r2[F1] + r2[a]*r1[F2])
        if r1 and r2 and r3:
            return 'type3'
    r = eq[0].match(diff(x(t),t) - z(t)*F2 + y(t)*F3)
    if r:
        r1 = collect_const(r[F2]).match(c*F2)
        r1.update(collect_const(r[F3]).match(b*F3))
        if r1:
            if eq[1].has(r1[F2]) and not eq[1].has(r1[F3]):
                r1[F2], r1[F3] = r1[F3], r1[F2]
                r1[c], r1[b] = -r1[b], -r1[c]
            r2 = (diff(y(t),t) - eq[1]).match(a*x(t)*r1[F3] - r1[c]*z(t)*F1)
        if r2:
            r3 = (diff(z(t),t) - eq[2] == r1[b]*y(t)*r2[F1] - r2[a]*x(t)*r1[F2])
        if r1 and r2 and r3:
            return 'type4'
    r = (diff(x(t),t) - eq[0]).match(x(t)*(F2 - F3))
    if r:
        r1 = collect_const(r[F2]).match(c*F2)
        r1.update(collect_const(r[F3]).match(b*F3))
        if r1:
            if eq[1].has(r1[F2]) and not eq[1].has(r1[F3]):
                r1[F2], r1[F3] = r1[F3], r1[F2]
                r1[c], r1[b] = -r1[b], -r1[c]
            r2 = (diff(y(t),t) - eq[1]).match(y(t)*(a*r1[F3] - r1[c]*F1))
        if r2:
            r3 = (diff(z(t),t) - eq[2] == z(t)*(r1[b]*r2[F1] - r2[a]*r1[F2]))
        if r1 and r2 and r3:
            return 'type5'
    return None

def check_nonlinear_3eq_order2(eq, func, func_coef):
    return None


def checksysodesol(eqs, sols, func=None):
    r"""
    Substitutes corresponding ``sols`` for each functions into each ``eqs`` and
    checks that the result of substitutions for each equation is ``0``. The
    equations and solutions passed can be any iterable.

    This only works when each ``sols`` have one function only, like `x(t)` or `y(t)`.
    For each function, ``sols`` can have a single solution or a list of solutions.
    In most cases it will not be necessary to explicitly identify the function,
    but if the function cannot be inferred from the original equation it
    can be supplied through the ``func`` argument.

    When a sequence of equations is passed, the same sequence is used to return
    the result for each equation with each function substituted with corresponding
    solutions.

    It tries the following method to find zero equivalence for each equation:

    Substitute the solutions for functions, like `x(t)` and `y(t)` into the
    original equations containing those functions.
    This function returns a tuple.  The first item in the tuple is ``True`` if
    the substitution results for each equation is ``0``, and ``False`` otherwise.
    The second item in the tuple is what the substitution results in.  Each element
    of the ``list`` should always be ``0`` corresponding to each equation if the
    first item is ``True``. Note that sometimes this function may return ``False``,
    but with an expression that is identically equal to ``0``, instead of returning
    ``True``.  This is because :py:meth:`~sympy.simplify.simplify.simplify` cannot
    reduce the expression to ``0``.  If an expression returned by each function
    vanishes identically, then ``sols`` really is a solution to ``eqs``.

    If this function seems to hang, it is probably because of a difficult simplification.

    Examples
    ========

    >>> from sympy import Eq, diff, symbols, sin, cos, exp, sqrt, S, Function
    >>> from sympy.solvers.ode import checksysodesol
    >>> C1, C2 = symbols('C1:3')
    >>> t = symbols('t')
    >>> x, y = symbols('x, y', cls=Function)
    >>> eq = (Eq(diff(x(t),t), x(t) + y(t) + 17), Eq(diff(y(t),t), -2*x(t) + y(t) + 12))
    >>> sol = [Eq(x(t), (C1*sin(sqrt(2)*t) + C2*cos(sqrt(2)*t))*exp(t) - S(5)/3),
    ... Eq(y(t), (sqrt(2)*C1*cos(sqrt(2)*t) - sqrt(2)*C2*sin(sqrt(2)*t))*exp(t) - S(46)/3)]
    >>> checksysodesol(eq, sol)
    (True, [0, 0])
    >>> eq = (Eq(diff(x(t),t),x(t)*y(t)**4), Eq(diff(y(t),t),y(t)**3))
    >>> sol = [Eq(x(t), C1*exp(-1/(4*(C2 + t)))), Eq(y(t), -sqrt(2)*sqrt(-1/(C2 + t))/2),
    ... Eq(x(t), C1*exp(-1/(4*(C2 + t)))), Eq(y(t), sqrt(2)*sqrt(-1/(C2 + t))/2)]
    >>> checksysodesol(eq, sol)
    (True, [0, 0])

    """
    def _sympify(eq):
        return list(map(sympify, eq if iterable(eq) else [eq]))
    eqs = _sympify(eqs)
    for i in range(len(eqs)):
        if isinstance(eqs[i], Equality):
            eqs[i] = eqs[i].lhs - eqs[i].rhs
    if func is None:
        funcs = []
        for eq in eqs:
            derivs = eq.atoms(Derivative)
            func = set().union(*[d.atoms(AppliedUndef) for d in derivs])
            for func_ in  func:
                funcs.append(func_)
        funcs = list(set(funcs))
    if not all(isinstance(func, AppliedUndef) and len(func.args) == 1 for func in funcs)\
    and len({func.args for func in funcs})!=1:
        raise ValueError("func must be a function of one variable, not %s" % func)
    for sol in sols:
        if len(sol.atoms(AppliedUndef)) != 1:
            raise ValueError("solutions should have one function only")
    if len(funcs) != len({sol.lhs for sol in sols}):
        raise ValueError("number of solutions provided does not match the number of equations")
    t = funcs[0].args[0]
    dictsol = dict()
    for sol in sols:
        func = list(sol.atoms(AppliedUndef))[0]
        if sol.rhs == func:
            sol = sol.reversed
        solved = sol.lhs == func and not sol.rhs.has(func)
        if not solved:
            rhs = solve(sol, func)
            if not rhs:
                raise NotImplementedError
        else:
            rhs = sol.rhs
        dictsol[func] = rhs
    checkeq = []
    for eq in eqs:
        for func in funcs:
            eq = sub_func_doit(eq, func, dictsol[func])
        ss = simplify(eq)
        if ss != 0:
            eq = ss.expand(force=True)
        else:
            eq = 0
        checkeq.append(eq)
    if len(set(checkeq)) == 1 and list(set(checkeq))[0] == 0:
        return (True, checkeq)
    else:
        return (False, checkeq)


@vectorize(0)
def odesimp(ode, eq, func, hint):
    r"""
    Simplifies solutions of ODEs, including trying to solve for ``func`` and
    running :py:meth:`~sympy.solvers.ode.constantsimp`.

    It may use knowledge of the type of solution that the hint returns to
    apply additional simplifications.

    It also attempts to integrate any :py:class:`~sympy.integrals.Integral`\s
    in the expression, if the hint is not an ``_Integral`` hint.

    This function should have no effect on expressions returned by
    :py:meth:`~sympy.solvers.ode.dsolve`, as
    :py:meth:`~sympy.solvers.ode.dsolve` already calls
    :py:meth:`~sympy.solvers.ode.odesimp`, but the individual hint functions
    do not call :py:meth:`~sympy.solvers.ode.odesimp` (because the
    :py:meth:`~sympy.solvers.ode.dsolve` wrapper does).  Therefore, this
    function is designed for mainly internal use.

    Examples
    ========

    >>> from sympy import sin, symbols, dsolve, pprint, Function
    >>> from sympy.solvers.ode import odesimp
    >>> x , u2, C1= symbols('x,u2,C1')
    >>> f = Function('f')

    >>> eq = dsolve(x*f(x).diff(x) - f(x) - x*sin(f(x)/x), f(x),
    ... hint='1st_homogeneous_coeff_subs_indep_div_dep_Integral',
    ... simplify=False)
    >>> pprint(eq, wrap_line=False)
                            x
                           ----
                           f(x)
                             /
                            |
                            |   /        1   \
                            |  -|u2 + -------|
                            |   |        /1 \|
                            |   |     sin|--||
                            |   \        \u2//
    log(f(x)) = log(C1) +   |  ---------------- d(u2)
                            |          2
                            |        u2
                            |
                           /

    >>> pprint(odesimp(eq, f(x), 1, {C1},
    ... hint='1st_homogeneous_coeff_subs_indep_div_dep'
    ... )) #doctest: +SKIP
        x
    --------- = C1
       /f(x)\
    tan|----|
       \2*x /

    """
    x = func.args[0]
    f = func.func
    C1 = get_numbered_constants(eq, num=1)
    constants = eq.free_symbols - ode.free_symbols

    # First, integrate if the hint allows it.
    eq = _handle_Integral(eq, func, hint)
    if hint.startswith("nth_linear_euler_eq_nonhomogeneous"):
        eq = simplify(eq)
    if not isinstance(eq, Equality):
        raise TypeError("eq should be an instance of Equality")

    # Second, clean up the arbitrary constants.
    # Right now, nth linear hints can put as many as 2*order constants in an
    # expression.  If that number grows with another hint, the third argument
    # here should be raised accordingly, or constantsimp() rewritten to handle
    # an arbitrary number of constants.
    eq = constantsimp(eq, constants)

    # Lastly, now that we have cleaned up the expression, try solving for func.
    # When CRootOf is implemented in solve(), we will want to return a CRootOf
    # every time instead of an Equality.

    # Get the f(x) on the left if possible.
    if eq.rhs == func and not eq.lhs.has(func):
        eq = [Eq(eq.rhs, eq.lhs)]

    # make sure we are working with lists of solutions in simplified form.
    if eq.lhs == func and not eq.rhs.has(func):
        # The solution is already solved
        eq = [eq]

        # special simplification of the rhs
        if hint.startswith("nth_linear_constant_coeff"):
            # Collect terms to make the solution look nice.
            # This is also necessary for constantsimp to remove unnecessary
            # terms from the particular solution from variation of parameters
            #
            # Collect is not behaving reliably here.  The results for
            # some linear constant-coefficient equations with repeated
            # roots do not properly simplify all constants sometimes.
            # 'collectterms' gives different orders sometimes, and results
            # differ in collect based on that order.  The
            # sort-reverse trick fixes things, but may fail in the
            # future. In addition, collect is splitting exponentials with
            # rational powers for no reason.  We have to do a match
            # to fix this using Wilds.
            global collectterms
            try:
                collectterms.sort(key=default_sort_key)
                collectterms.reverse()
            except Exception:
                pass
            assert len(eq) == 1 and eq[0].lhs == f(x)
            sol = eq[0].rhs
            sol = expand_mul(sol)
            for i, reroot, imroot in collectterms:
                sol = collect(sol, x**i*exp(reroot*x)*sin(abs(imroot)*x))
                sol = collect(sol, x**i*exp(reroot*x)*cos(imroot*x))
            for i, reroot, imroot in collectterms:
                sol = collect(sol, x**i*exp(reroot*x))
            del collectterms

            # Collect is splitting exponentials with rational powers for
            # no reason.  We call powsimp to fix.
            sol = powsimp(sol)

            eq[0] = Eq(f(x), sol)

    else:
        # The solution is not solved, so try to solve it
        try:
            floats = any(i.is_Float for i in eq.atoms(Number))
            eqsol = solve(eq, func, force=True, rational=False if floats else None)
            if not eqsol:
                raise NotImplementedError
        except (NotImplementedError, PolynomialError):
            eq = [eq]
        else:
            def _expand(expr):
                numer, denom = expr.as_numer_denom()

                if denom.is_Add:
                    return expr
                else:
                    return powsimp(expr.expand(), combine='exp', deep=True)

            # XXX: the rest of odesimp() expects each ``t`` to be in a
            # specific normal form: rational expression with numerator
            # expanded, but with combined exponential functions (at
            # least in this setup all tests pass).
            eq = [Eq(f(x), _expand(t)) for t in eqsol]

        # special simplification of the lhs.
        if hint.startswith("1st_homogeneous_coeff"):
            for j, eqi in enumerate(eq):
                newi = logcombine(eqi, force=True)
                if isinstance(newi.lhs, log) and newi.rhs == 0:
                    newi = Eq(newi.lhs.args[0]/C1, C1)
                eq[j] = newi

    # We cleaned up the constants before solving to help the solve engine with
    # a simpler expression, but the solved expression could have introduced
    # things like -C1, so rerun constantsimp() one last time before returning.
    for i, eqi in enumerate(eq):
        eq[i] = constantsimp(eqi, constants)
        eq[i] = constant_renumber(eq[i], ode.free_symbols)

    # If there is only 1 solution, return it;
    # otherwise return the list of solutions.
    if len(eq) == 1:
        eq = eq[0]
    return eq

def checkodesol(ode, sol, func=None, order='auto', solve_for_func=True):
    r"""
    Substitutes ``sol`` into ``ode`` and checks that the result is ``0``.

    This only works when ``func`` is one function, like `f(x)`.  ``sol`` can
    be a single solution or a list of solutions.  Each solution may be an
    :py:class:`~sympy.core.relational.Equality` that the solution satisfies,
    e.g. ``Eq(f(x), C1), Eq(f(x) + C1, 0)``; or simply an
    :py:class:`~sympy.core.expr.Expr`, e.g. ``f(x) - C1``. In most cases it
    will not be necessary to explicitly identify the function, but if the
    function cannot be inferred from the original equation it can be supplied
    through the ``func`` argument.

    If a sequence of solutions is passed, the same sort of container will be
    used to return the result for each solution.

    It tries the following methods, in order, until it finds zero equivalence:

    1. Substitute the solution for `f` in the original equation.  This only
       works if ``ode`` is solved for `f`.  It will attempt to solve it first
       unless ``solve_for_func == False``.
    2. Take `n` derivatives of the solution, where `n` is the order of
       ``ode``, and check to see if that is equal to the solution.  This only
       works on exact ODEs.
    3. Take the 1st, 2nd, ..., `n`\th derivatives of the solution, each time
       solving for the derivative of `f` of that order (this will always be
       possible because `f` is a linear operator). Then back substitute each
       derivative into ``ode`` in reverse order.

    This function returns a tuple.  The first item in the tuple is ``True`` if
    the substitution results in ``0``, and ``False`` otherwise. The second
    item in the tuple is what the substitution results in.  It should always
    be ``0`` if the first item is ``True``. Sometimes this function will
    return ``False`` even when an expression is identically equal to ``0``.
    This happens when :py:meth:`~sympy.simplify.simplify.simplify` does not
    reduce the expression to ``0``.  If an expression returned by this
    function vanishes identically, then ``sol`` really is a solution to
    the ``ode``.

    If this function seems to hang, it is probably because of a hard
    simplification.

    To use this function to test, test the first item of the tuple.

    Examples
    ========

    >>> from sympy import Eq, Function, checkodesol, symbols
    >>> x, C1 = symbols('x,C1')
    >>> f = Function('f')
    >>> checkodesol(f(x).diff(x), Eq(f(x), C1))
    (True, 0)
    >>> assert checkodesol(f(x).diff(x), C1)[0]
    >>> assert not checkodesol(f(x).diff(x), x)[0]
    >>> checkodesol(f(x).diff(x, 2), x**2)
    (False, 2)

    """
    if not isinstance(ode, Equality):
        ode = Eq(ode, 0)
    if func is None:
        try:
            _, func = _preprocess(ode.lhs)
        except ValueError:
            funcs = [s.atoms(AppliedUndef) for s in (
                sol if is_sequence(sol, set) else [sol])]
            funcs = set().union(*funcs)
            if len(funcs) != 1:
                raise ValueError(
                    'must pass func arg to checkodesol for this case.')
            func = funcs.pop()
    if not isinstance(func, AppliedUndef) or len(func.args) != 1:
        raise ValueError(
            "func must be a function of one variable, not %s" % func)
    if is_sequence(sol, set):
        return type(sol)([checkodesol(ode, i, order=order, solve_for_func=solve_for_func) for i in sol])

    if not isinstance(sol, Equality):
        sol = Eq(func, sol)
    elif sol.rhs == func:
        sol = sol.reversed

    if order == 'auto':
        order = ode_order(ode, func)
    solved = sol.lhs == func and not sol.rhs.has(func)
    if solve_for_func and not solved:
        rhs = solve(sol, func)
        if rhs:
            eqs = [Eq(func, t) for t in rhs]
            if len(rhs) == 1:
                eqs = eqs[0]
            return checkodesol(ode, eqs, order=order,
                solve_for_func=False)

    s = True
    testnum = 0
    x = func.args[0]
    while s:
        if testnum == 0:
            # First pass, try substituting a solved solution directly into the
            # ODE. This has the highest chance of succeeding.
            ode_diff = ode.lhs - ode.rhs

            if sol.lhs == func:
                s = sub_func_doit(ode_diff, func, sol.rhs)
            else:
                testnum += 1
                continue
            ss = simplify(s)
            if ss:
                # with the new numer_denom in power.py, if we do a simple
                # expansion then testnum == 0 verifies all solutions.
                s = ss.expand(force=True)
            else:
                s = 0
            testnum += 1
        elif testnum == 1:
            # Second pass. If we cannot substitute f, try seeing if the nth
            # derivative is equal, this will only work for odes that are exact,
            # by definition.
            s = simplify(
                trigsimp(diff(sol.lhs, x, order) - diff(sol.rhs, x, order)) -
                trigsimp(ode.lhs) + trigsimp(ode.rhs))
            # s2 = simplify(
            #     diff(sol.lhs, x, order) - diff(sol.rhs, x, order) - \
            #     ode.lhs + ode.rhs)
            testnum += 1
        elif testnum == 2:
            # Third pass. Try solving for df/dx and substituting that into the
            # ODE. Thanks to Chris Smith for suggesting this method.  Many of
            # the comments below are his, too.
            # The method:
            # - Take each of 1..n derivatives of the solution.
            # - Solve each nth derivative for d^(n)f/dx^(n)
            #   (the differential of that order)
            # - Back substitute into the ODE in decreasing order
            #   (i.e., n, n-1, ...)
            # - Check the result for zero equivalence
            if sol.lhs == func and not sol.rhs.has(func):
                diffsols = {0: sol.rhs}
            elif sol.rhs == func and not sol.lhs.has(func):
                diffsols = {0: sol.lhs}
            else:
                diffsols = {}
            sol = sol.lhs - sol.rhs
            for i in range(1, order + 1):
                # Differentiation is a linear operator, so there should always
                # be 1 solution. Nonetheless, we test just to make sure.
                # We only need to solve once.  After that, we automatically
                # have the solution to the differential in the order we want.
                if i == 1:
                    ds = sol.diff(x)
                    try:
                        sdf = solve(ds, func.diff(x, i))
                        if not sdf:
                            raise NotImplementedError
                    except NotImplementedError:
                        testnum += 1
                        break
                    else:
                        diffsols[i] = sdf[0]
                else:
                    # This is what the solution says df/dx should be.
                    diffsols[i] = diffsols[i - 1].diff(x)

            # Make sure the above didn't fail.
            if testnum > 2:
                continue
            else:
                # Substitute it into ODE to check for self consistency.
                lhs, rhs = ode.lhs, ode.rhs
                for i in range(order, -1, -1):
                    if i == 0 and 0 not in diffsols:
                        # We can only substitute f(x) if the solution was
                        # solved for f(x).
                        break
                    lhs = sub_func_doit(lhs, func.diff(x, i), diffsols[i])
                    rhs = sub_func_doit(rhs, func.diff(x, i), diffsols[i])
                    ode_or_bool = Eq(lhs, rhs)
                    ode_or_bool = simplify(ode_or_bool)

                    if isinstance(ode_or_bool, (bool, BooleanAtom)):
                        if ode_or_bool:
                            lhs = rhs = S.Zero
                    else:
                        lhs = ode_or_bool.lhs
                        rhs = ode_or_bool.rhs
                # No sense in overworking simplify -- just prove that the
                # numerator goes to zero
                num = trigsimp((lhs - rhs).as_numer_denom()[0])
                # since solutions are obtained using force=True we test
                # using the same level of assumptions
                ## replace function with dummy so assumptions will work
                _func = Dummy('func')
                num = num.subs(func, _func)
                ## posify the expression
                num, reps = posify(num)
                s = simplify(num).xreplace(reps).xreplace({_func: func})
                testnum += 1
        else:
            break

    if not s:
        return (True, s)
    elif s is True:  # The code above never was able to change s
        raise NotImplementedError("Unable to test if " + str(sol) +
            " is a solution to " + str(ode) + ".")
    else:
        return (False, s)


def ode_sol_simplicity(sol, func, trysolving=True):
    r"""
    Returns an extended integer representing how simple a solution to an ODE
    is.

    The following things are considered, in order from most simple to least:

    - ``sol`` is solved for ``func``.
    - ``sol`` is not solved for ``func``, but can be if passed to solve (e.g.,
      a solution returned by ``dsolve(ode, func, simplify=False``).
    - If ``sol`` is not solved for ``func``, then base the result on the
      length of ``sol``, as computed by ``len(str(sol))``.
    - If ``sol`` has any unevaluated :py:class:`~sympy.integrals.Integral`\s,
      this will automatically be considered less simple than any of the above.

    This function returns an integer such that if solution A is simpler than
    solution B by above metric, then ``ode_sol_simplicity(sola, func) <
    ode_sol_simplicity(solb, func)``.

    Currently, the following are the numbers returned, but if the heuristic is
    ever improved, this may change.  Only the ordering is guaranteed.

    +----------------------------------------------+-------------------+
    | Simplicity                                   | Return            |
    +==============================================+===================+
    | ``sol`` solved for ``func``                  | ``-2``            |
    +----------------------------------------------+-------------------+
    | ``sol`` not solved for ``func`` but can be   | ``-1``            |
    +----------------------------------------------+-------------------+
    | ``sol`` is not solved nor solvable for       | ``len(str(sol))`` |
    | ``func``                                     |                   |
    +----------------------------------------------+-------------------+
    | ``sol`` contains an                          | ``oo``            |
    | :py:class:`~sympy.integrals.Integral`        |                   |
    +----------------------------------------------+-------------------+

    ``oo`` here means the SymPy infinity, which should compare greater than
    any integer.

    If you already know :py:meth:`~sympy.solvers.solvers.solve` cannot solve
    ``sol``, you can use ``trysolving=False`` to skip that step, which is the
    only potentially slow step.  For example,
    :py:meth:`~sympy.solvers.ode.dsolve` with the ``simplify=False`` flag
    should do this.

    If ``sol`` is a list of solutions, if the worst solution in the list
    returns ``oo`` it returns that, otherwise it returns ``len(str(sol))``,
    that is, the length of the string representation of the whole list.

    Examples
    ========

    This function is designed to be passed to ``min`` as the key argument,
    such as ``min(listofsolutions, key=lambda i: ode_sol_simplicity(i,
    f(x)))``.

    >>> from sympy import symbols, Function, Eq, tan, cos, sqrt, Integral
    >>> from sympy.solvers.ode import ode_sol_simplicity
    >>> x, C1, C2 = symbols('x, C1, C2')
    >>> f = Function('f')

    >>> ode_sol_simplicity(Eq(f(x), C1*x**2), f(x))
    -2
    >>> ode_sol_simplicity(Eq(x**2 + f(x), C1), f(x))
    -1
    >>> ode_sol_simplicity(Eq(f(x), C1*Integral(2*x, x)), f(x))
    oo
    >>> eq1 = Eq(f(x)/tan(f(x)/(2*x)), C1)
    >>> eq2 = Eq(f(x)/tan(f(x)/(2*x) + f(x)), C2)
    >>> [ode_sol_simplicity(eq, f(x)) for eq in [eq1, eq2]]
    [28, 35]
    >>> min([eq1, eq2], key=lambda i: ode_sol_simplicity(i, f(x)))
    Eq(f(x)/tan(f(x)/(2*x)), C1)

    """
    # TODO: if two solutions are solved for f(x), we still want to be
    # able to get the simpler of the two

    # See the docstring for the coercion rules.  We check easier (faster)
    # things here first, to save time.

    if iterable(sol):
        # See if there are Integrals
        for i in sol:
            if ode_sol_simplicity(i, func, trysolving=trysolving) == oo:
                return oo

        return len(str(sol))

    if sol.has(Integral):
        return oo

    # Next, try to solve for func.  This code will change slightly when CRootOf
    # is implemented in solve().  Probably a CRootOf solution should fall
    # somewhere between a normal solution and an unsolvable expression.

    # First, see if they are already solved
    if sol.lhs == func and not sol.rhs.has(func) or \
            sol.rhs == func and not sol.lhs.has(func):
        return -2
    # We are not so lucky, try solving manually
    if trysolving:
        try:
            sols = solve(sol, func)
            if not sols:
                raise NotImplementedError
        except NotImplementedError:
            pass
        else:
            return -1

    # Finally, a naive computation based on the length of the string version
    # of the expression.  This may favor combined fractions because they
    # will not have duplicate denominators, and may slightly favor expressions
    # with fewer additions and subtractions, as those are separated by spaces
    # by the printer.

    # Additional ideas for simplicity heuristics are welcome, like maybe
    # checking if a equation has a larger domain, or if constantsimp has
    # introduced arbitrary constants numbered higher than the order of a
    # given ODE that sol is a solution of.
    return len(str(sol))


def _get_constant_subexpressions(expr, Cs):
    Cs = set(Cs)
    Ces = []
    def _recursive_walk(expr):
        expr_syms = expr.free_symbols
        if expr_syms and expr_syms.issubset(Cs):
            Ces.append(expr)
        else:
            if expr.func == exp:
                expr = expr.expand(mul=True)
            if expr.func in (Add, Mul):
                d = sift(expr.args, lambda i : i.free_symbols.issubset(Cs))
                if len(d[True]) > 1:
                    x = expr.func(*d[True])
                    if not x.is_number:
                        Ces.append(x)
            elif isinstance(expr, Integral):
                if expr.free_symbols.issubset(Cs) and \
                            all(len(x) == 3 for x in expr.limits):
                    Ces.append(expr)
            for i in expr.args:
                _recursive_walk(i)
        return
    _recursive_walk(expr)
    return Ces

def __remove_linear_redundancies(expr, Cs):
    cnts = {i: expr.count(i) for i in Cs}
    Cs = [i for i in Cs if cnts[i] > 0]

    def _linear(expr):
        if isinstance(expr, Add):
            xs = [i for i in Cs if expr.count(i)==cnts[i] \
                and 0 == expr.diff(i, 2)]
            d = {}
            for x in xs:
                y = expr.diff(x)
                if y not in d:
                    d[y]=[]
                d[y].append(x)
            for y in d:
                if len(d[y]) > 1:
                    d[y].sort(key=str)
                    for x in d[y][1:]:
                        expr = expr.subs(x, 0)
        return expr

    def _recursive_walk(expr):
        if len(expr.args) != 0:
            expr = expr.func(*[_recursive_walk(i) for i in expr.args])
        expr = _linear(expr)
        return expr

    if isinstance(expr, Equality):
        lhs, rhs = [_recursive_walk(i) for i in expr.args]
        f = lambda i: isinstance(i, Number) or i in Cs
        if isinstance(lhs, Symbol) and lhs in Cs:
            rhs, lhs = lhs, rhs
        if lhs.func in (Add, Symbol) and rhs.func in (Add, Symbol):
            dlhs = sift([lhs] if isinstance(lhs, AtomicExpr) else lhs.args, f)
            drhs = sift([rhs] if isinstance(rhs, AtomicExpr) else rhs.args, f)
            for i in [True, False]:
                for hs in [dlhs, drhs]:
                    if i not in hs:
                        hs[i] = [0]
            # this calculation can be simplified
            lhs = Add(*dlhs[False]) - Add(*drhs[False])
            rhs = Add(*drhs[True]) - Add(*dlhs[True])
        elif lhs.func in (Mul, Symbol) and rhs.func in (Mul, Symbol):
            dlhs = sift([lhs] if isinstance(lhs, AtomicExpr) else lhs.args, f)
            if True in dlhs:
                if False not in dlhs:
                    dlhs[False] = [1]
                lhs = Mul(*dlhs[False])
                rhs = rhs/Mul(*dlhs[True])
        return Eq(lhs, rhs)
    else:
        return _recursive_walk(expr)

@vectorize(0)
def constantsimp(expr, constants):
    r"""
    Simplifies an expression with arbitrary constants in it.

    This function is written specifically to work with
    :py:meth:`~sympy.solvers.ode.dsolve`, and is not intended for general use.

    Simplification is done by "absorbing" the arbitrary constants into other
    arbitrary constants, numbers, and symbols that they are not independent
    of.

    The symbols must all have the same name with numbers after it, for
    example, ``C1``, ``C2``, ``C3``.  The ``symbolname`` here would be
    '``C``', the ``startnumber`` would be 1, and the ``endnumber`` would be 3.
    If the arbitrary constants are independent of the variable ``x``, then the
    independent symbol would be ``x``.  There is no need to specify the
    dependent function, such as ``f(x)``, because it already has the
    independent symbol, ``x``, in it.

    Because terms are "absorbed" into arbitrary constants and because
    constants are renumbered after simplifying, the arbitrary constants in
    expr are not necessarily equal to the ones of the same name in the
    returned result.

    If two or more arbitrary constants are added, multiplied, or raised to the
    power of each other, they are first absorbed together into a single
    arbitrary constant.  Then the new constant is combined into other terms if
    necessary.

    Absorption of constants is done with limited assistance:

    1. terms of :py:class:`~sympy.core.add.Add`\s are collected to try join
       constants so `e^x (C_1 \cos(x) + C_2 \cos(x))` will simplify to `e^x
       C_1 \cos(x)`;

    2. powers with exponents that are :py:class:`~sympy.core.add.Add`\s are
       expanded so `e^{C_1 + x}` will be simplified to `C_1 e^x`.

    Use :py:meth:`~sympy.solvers.ode.constant_renumber` to renumber constants
    after simplification or else arbitrary numbers on constants may appear,
    e.g. `C_1 + C_3 x`.

    In rare cases, a single constant can be "simplified" into two constants.
    Every differential equation solution should have as many arbitrary
    constants as the order of the differential equation.  The result here will
    be technically correct, but it may, for example, have `C_1` and `C_2` in
    an expression, when `C_1` is actually equal to `C_2`.  Use your discretion
    in such situations, and also take advantage of the ability to use hints in
    :py:meth:`~sympy.solvers.ode.dsolve`.

    Examples
    ========

    >>> from sympy import symbols
    >>> from sympy.solvers.ode import constantsimp
    >>> C1, C2, C3, x, y = symbols('C1, C2, C3, x, y')
    >>> constantsimp(2*C1*x, {C1, C2, C3})
    C1*x
    >>> constantsimp(C1 + 2 + x, {C1, C2, C3})
    C1 + x
    >>> constantsimp(C1*C2 + 2 + C2 + C3*x, {C1, C2, C3})
    C1 + C3*x

    """
    # This function works recursively.  The idea is that, for Mul,
    # Add, Pow, and Function, if the class has a constant in it, then
    # we can simplify it, which we do by recursing down and
    # simplifying up.  Otherwise, we can skip that part of the
    # expression.

    Cs = constants

    orig_expr = expr

    constant_subexprs = _get_constant_subexpressions(expr, Cs)
    for xe in constant_subexprs:
        xes = list(xe.free_symbols)
        if not xes:
            continue
        if all([expr.count(c) == xe.count(c) for c in xes]):
            xes.sort(key=str)
            expr = expr.subs(xe, xes[0])

    # try to perform common sub-expression elimination of constant terms
    try:
        commons, rexpr = cse(expr)
        commons.reverse()
        rexpr = rexpr[0]
        for s in commons:
            cs = list(s[1].atoms(Symbol))
            if len(cs) == 1 and cs[0] in Cs and \
                cs[0] not in rexpr.atoms(Symbol) and \
                not any(cs[0] in ex for ex in commons if ex != s):
                rexpr = rexpr.subs(s[0], cs[0])
            else:
                rexpr = rexpr.subs(*s)
        expr = rexpr
    except Exception:
        pass
    expr = __remove_linear_redundancies(expr, Cs)

    def _conditional_term_factoring(expr):
        new_expr = terms_gcd(expr, clear=False, deep=True, expand=False)

        # we do not want to factor exponentials, so handle this separately
        if new_expr.is_Mul:
            infac = False
            asfac = False
            for m in new_expr.args:
                if isinstance(m, exp):
                    asfac = True
                elif m.is_Add:
                    infac = any(isinstance(fi, exp) for t in m.args
                        for fi in Mul.make_args(t))
                if asfac and infac:
                    new_expr = expr
                    break
        return new_expr

    expr = _conditional_term_factoring(expr)

    # call recursively if more simplification is possible
    if orig_expr != expr:
        return constantsimp(expr, Cs)
    return expr


def constant_renumber(expr, variables=None, newconstants=None):
    r"""
    Renumber arbitrary constants in ``expr`` to use the symbol names as given
    in ``newconstants``. In the process, this reorders expression terms in a
    standard way.

    If ``newconstants`` is not provided then the new constant names will be
    ``C1``, ``C2`` etc. Otherwise ``newconstants`` should be an iterable
    giving the new symbols to use for the constants in order.

    The ``variables`` argument is a list of non-constant symbols. All other
    free symbols found in ``expr`` are assumed to be constants and will be
    renumbered. If ``variables`` is not given then any numbered symbol
    beginning with ``C`` (e.g. ``C1``) is assumed to be a constant.

    Symbols are renumbered based on ``.sort_key()``, so they should be
    numbered roughly in the order that they appear in the final, printed
    expression.  Note that this ordering is based in part on hashes, so it can
    produce different results on different machines.

    The structure of this function is very similar to that of
    :py:meth:`~sympy.solvers.ode.constantsimp`.

    Examples
    ========

    >>> from sympy import symbols, Eq, pprint
    >>> from sympy.solvers.ode import constant_renumber
    >>> x, C1, C2, C3 = symbols('x,C1:4')
    >>> expr = C3 + C2*x + C1*x**2
    >>> expr
    C1*x**2  + C2*x + C3
    >>> constant_renumber(expr)
    C1 + C2*x + C3*x**2

    The ``variables`` argument specifies which are constants so that the
    other symbols will not be renumbered:

    >>> constant_renumber(expr, [C1, x])
    C1*x**2  + C2 + C3*x

    The ``newconstants`` argument is used to specify what symbols to use when
    replacing the constants:

    >>> constant_renumber(expr, [x], newconstants=symbols('E1:4'))
    E1 + E2*x + E3*x**2

    """
    if type(expr) in (set, list, tuple):
        renumbered = [constant_renumber(e, variables, newconstants) for e in expr]
        return type(expr)(renumbered)

    # Symbols in solution but not ODE are constants
    if variables is not None:
        variables = set(variables)
        constantsymbols = list(expr.free_symbols - variables)
    # Any Cn is a constant...
    else:
        variables = set()
        isconstant = lambda s: s.startswith('C') and s[1:].isdigit()
        constantsymbols = [sym for sym in expr.free_symbols if isconstant(sym.name)]

    # Find new constants checking that they aren't alread in the ODE
    if newconstants is None:
        iter_constants = numbered_symbols(start=1, prefix='C', exclude=variables)
    else:
        iter_constants = (sym for sym in newconstants if sym not in variables)

    global newstartnumber
    newstartnumber = 1
    endnumber = len(constantsymbols)
    constants_found = [None]*(endnumber + 2)

    # make a mapping to send all constantsymbols to S.One and use
    # that to make sure that term ordering is not dependent on
    # the indexed value of C
    C_1 = [(ci, S.One) for ci in constantsymbols]
    sort_key=lambda arg: default_sort_key(arg.subs(C_1))

    def _constant_renumber(expr):
        r"""
        We need to have an internal recursive function so that
        newstartnumber maintains its values throughout recursive calls.

        """
        # FIXME: Use nonlocal here when support for Py2 is dropped:
        global newstartnumber

        if isinstance(expr, Equality):
            return Eq(
                _constant_renumber(expr.lhs),
                _constant_renumber(expr.rhs))

        if type(expr) not in (Mul, Add, Pow) and not expr.is_Function and \
                not expr.has(*constantsymbols):
            # Base case, as above.  Hope there aren't constants inside
            # of some other class, because they won't be renumbered.
            return expr
        elif expr.is_Piecewise:
            return expr
        elif expr in constantsymbols:
            if expr not in constants_found:
                constants_found[newstartnumber] = expr
                newstartnumber += 1
            return expr
        elif expr.is_Function or expr.is_Pow or isinstance(expr, Tuple):
            return expr.func(
                *[_constant_renumber(x) for x in expr.args])
        else:
            sortedargs = list(expr.args)
            sortedargs.sort(key=sort_key)
            return expr.func(*[_constant_renumber(x) for x in sortedargs])
    expr = _constant_renumber(expr)

    # Don't renumber symbols present in the ODE.
    constants_found = [c for c in constants_found if c not in variables]

    # Renumbering happens here
    expr = expr.subs(zip(constants_found[1:], iter_constants), simultaneous=True)
    return expr


def _handle_Integral(expr, func, hint):
    r"""
    Converts a solution with Integrals in it into an actual solution.

    For most hints, this simply runs ``expr.doit()``.

    """
    global y
    x = func.args[0]
    f = func.func
    if hint == "1st_exact":
        sol = (expr.doit()).subs(y, f(x))
        del y
    elif hint == "1st_exact_Integral":
        sol = Eq(Subs(expr.lhs, y, f(x)), expr.rhs)
        del y
    elif hint == "nth_linear_constant_coeff_homogeneous":
        sol = expr
    elif not hint.endswith("_Integral"):
        sol = expr.doit()
    else:
        sol = expr
    return sol


# FIXME: replace the general solution in the docstring with
# dsolve(equation, hint='1st_exact_Integral').  You will need to be able
# to have assumptions on P and Q that dP/dy = dQ/dx.
def ode_1st_exact(eq, func, order, match):
    r"""
    Solves 1st order exact ordinary differential equations.

    A 1st order differential equation is called exact if it is the total
    differential of a function. That is, the differential equation

    .. math:: P(x, y) \,\partial{}x + Q(x, y) \,\partial{}y = 0

    is exact if there is some function `F(x, y)` such that `P(x, y) =
    \partial{}F/\partial{}x` and `Q(x, y) = \partial{}F/\partial{}y`.  It can
    be shown that a necessary and sufficient condition for a first order ODE
    to be exact is that `\partial{}P/\partial{}y = \partial{}Q/\partial{}x`.
    Then, the solution will be as given below::

        >>> from sympy import Function, Eq, Integral, symbols, pprint
        >>> x, y, t, x0, y0, C1= symbols('x,y,t,x0,y0,C1')
        >>> P, Q, F= map(Function, ['P', 'Q', 'F'])
        >>> pprint(Eq(Eq(F(x, y), Integral(P(t, y), (t, x0, x)) +
        ... Integral(Q(x0, t), (t, y0, y))), C1))
                    x                y
                    /                /
                   |                |
        F(x, y) =  |  P(t, y) dt +  |  Q(x0, t) dt = C1
                   |                |
                  /                /
                  x0               y0

    Where the first partials of `P` and `Q` exist and are continuous in a
    simply connected region.

    A note: SymPy currently has no way to represent inert substitution on an
    expression, so the hint ``1st_exact_Integral`` will return an integral
    with `dy`.  This is supposed to represent the function that you are
    solving for.

    Examples
    ========

    >>> from sympy import Function, dsolve, cos, sin
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> dsolve(cos(f(x)) - (x*sin(f(x)) - f(x)**2)*f(x).diff(x),
    ... f(x), hint='1st_exact')
    Eq(x*cos(f(x)) + f(x)**3/3, C1)

    References
    ==========

    - https://en.wikipedia.org/wiki/Exact_differential_equation
    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 73

    # indirect doctest

    """
    x = func.args[0]
    f = func.func
    r = match  # d+e*diff(f(x),x)
    e = r[r['e']]
    d = r[r['d']]
    global y  # This is the only way to pass dummy y to _handle_Integral
    y = r['y']
    C1 = get_numbered_constants(eq, num=1)
    # Refer Joel Moses, "Symbolic Integration - The Stormy Decade",
    # Communications of the ACM, Volume 14, Number 8, August 1971, pp. 558
    # which gives the method to solve an exact differential equation.
    sol = Integral(d, x) + Integral((e - (Integral(d, x).diff(y))), y)
    return Eq(sol, C1)


def ode_1st_homogeneous_coeff_best(eq, func, order, match):
    r"""
    Returns the best solution to an ODE from the two hints
    ``1st_homogeneous_coeff_subs_dep_div_indep`` and
    ``1st_homogeneous_coeff_subs_indep_div_dep``.

    This is as determined by :py:meth:`~sympy.solvers.ode.ode_sol_simplicity`.

    See the
    :py:meth:`~sympy.solvers.ode.ode_1st_homogeneous_coeff_subs_indep_div_dep`
    and
    :py:meth:`~sympy.solvers.ode.ode_1st_homogeneous_coeff_subs_dep_div_indep`
    docstrings for more information on these hints.  Note that there is no
    ``ode_1st_homogeneous_coeff_best_Integral`` hint.

    Examples
    ========

    >>> from sympy import Function, dsolve, pprint
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> pprint(dsolve(2*x*f(x) + (x**2 + f(x)**2)*f(x).diff(x), f(x),
    ... hint='1st_homogeneous_coeff_best', simplify=False))
                             /    2    \
                             | 3*x     |
                          log|----- + 1|
                             | 2       |
                             \f (x)    /
    log(f(x)) = log(C1) - --------------
                                3

    References
    ==========

    - https://en.wikipedia.org/wiki/Homogeneous_differential_equation
    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 59

    # indirect doctest

    """
    # There are two substitutions that solve the equation, u1=y/x and u2=x/y
    # They produce different integrals, so try them both and see which
    # one is easier.
    sol1 = ode_1st_homogeneous_coeff_subs_indep_div_dep(eq,
    func, order, match)
    sol2 = ode_1st_homogeneous_coeff_subs_dep_div_indep(eq,
    func, order, match)
    simplify = match.get('simplify', True)
    if simplify:
        # why is odesimp called here?  Should it be at the usual spot?
        sol1 = odesimp(eq, sol1, func, "1st_homogeneous_coeff_subs_indep_div_dep")
        sol2 = odesimp(eq, sol2, func, "1st_homogeneous_coeff_subs_dep_div_indep")
    return min([sol1, sol2], key=lambda x: ode_sol_simplicity(x, func,
        trysolving=not simplify))


def ode_1st_homogeneous_coeff_subs_dep_div_indep(eq, func, order, match):
    r"""
    Solves a 1st order differential equation with homogeneous coefficients
    using the substitution `u_1 = \frac{\text{<dependent
    variable>}}{\text{<independent variable>}}`.

    This is a differential equation

    .. math:: P(x, y) + Q(x, y) dy/dx = 0

    such that `P` and `Q` are homogeneous and of the same order.  A function
    `F(x, y)` is homogeneous of order `n` if `F(x t, y t) = t^n F(x, y)`.
    Equivalently, `F(x, y)` can be rewritten as `G(y/x)` or `H(x/y)`.  See
    also the docstring of :py:meth:`~sympy.solvers.ode.homogeneous_order`.

    If the coefficients `P` and `Q` in the differential equation above are
    homogeneous functions of the same order, then it can be shown that the
    substitution `y = u_1 x` (i.e. `u_1 = y/x`) will turn the differential
    equation into an equation separable in the variables `x` and `u`.  If
    `h(u_1)` is the function that results from making the substitution `u_1 =
    f(x)/x` on `P(x, f(x))` and `g(u_2)` is the function that results from the
    substitution on `Q(x, f(x))` in the differential equation `P(x, f(x)) +
    Q(x, f(x)) f'(x) = 0`, then the general solution is::

        >>> from sympy import Function, dsolve, pprint
        >>> from sympy.abc import x
        >>> f, g, h = map(Function, ['f', 'g', 'h'])
        >>> genform = g(f(x)/x) + h(f(x)/x)*f(x).diff(x)
        >>> pprint(genform)
         /f(x)\    /f(x)\ d
        g|----| + h|----|*--(f(x))
         \ x  /    \ x  / dx
        >>> pprint(dsolve(genform, f(x),
        ... hint='1st_homogeneous_coeff_subs_dep_div_indep_Integral'))
                       f(x)
                       ----
                        x
                         /
                        |
                        |       -h(u1)
        log(x) = C1 +   |  ---------------- d(u1)
                        |  u1*h(u1) + g(u1)
                        |
                       /

    Where `u_1 h(u_1) + g(u_1) \ne 0` and `x \ne 0`.

    See also the docstrings of
    :py:meth:`~sympy.solvers.ode.ode_1st_homogeneous_coeff_best` and
    :py:meth:`~sympy.solvers.ode.ode_1st_homogeneous_coeff_subs_indep_div_dep`.

    Examples
    ========

    >>> from sympy import Function, dsolve
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> pprint(dsolve(2*x*f(x) + (x**2 + f(x)**2)*f(x).diff(x), f(x),
    ... hint='1st_homogeneous_coeff_subs_dep_div_indep', simplify=False))
                          /          3   \
                          |3*f(x)   f (x)|
                       log|------ + -----|
                          |  x         3 |
                          \           x  /
    log(x) = log(C1) - -------------------
                                3

    References
    ==========

    - https://en.wikipedia.org/wiki/Homogeneous_differential_equation
    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 59

    # indirect doctest

    """
    x = func.args[0]
    f = func.func
    u = Dummy('u')
    u1 = Dummy('u1')  # u1 == f(x)/x
    r = match  # d+e*diff(f(x),x)
    C1 = get_numbered_constants(eq, num=1)
    xarg = match.get('xarg', 0)
    yarg = match.get('yarg', 0)
    int = Integral(
        (-r[r['e']]/(r[r['d']] + u1*r[r['e']])).subs({x: 1, r['y']: u1}),
        (u1, None, f(x)/x))
    sol = logcombine(Eq(log(x), int + log(C1)), force=True)
    sol = sol.subs(f(x), u).subs(((u, u - yarg), (x, x - xarg), (u, f(x))))
    return sol


def ode_1st_homogeneous_coeff_subs_indep_div_dep(eq, func, order, match):
    r"""
    Solves a 1st order differential equation with homogeneous coefficients
    using the substitution `u_2 = \frac{\text{<independent
    variable>}}{\text{<dependent variable>}}`.

    This is a differential equation

    .. math:: P(x, y) + Q(x, y) dy/dx = 0

    such that `P` and `Q` are homogeneous and of the same order.  A function
    `F(x, y)` is homogeneous of order `n` if `F(x t, y t) = t^n F(x, y)`.
    Equivalently, `F(x, y)` can be rewritten as `G(y/x)` or `H(x/y)`.  See
    also the docstring of :py:meth:`~sympy.solvers.ode.homogeneous_order`.

    If the coefficients `P` and `Q` in the differential equation above are
    homogeneous functions of the same order, then it can be shown that the
    substitution `x = u_2 y` (i.e. `u_2 = x/y`) will turn the differential
    equation into an equation separable in the variables `y` and `u_2`.  If
    `h(u_2)` is the function that results from making the substitution `u_2 =
    x/f(x)` on `P(x, f(x))` and `g(u_2)` is the function that results from the
    substitution on `Q(x, f(x))` in the differential equation `P(x, f(x)) +
    Q(x, f(x)) f'(x) = 0`, then the general solution is:

    >>> from sympy import Function, dsolve, pprint
    >>> from sympy.abc import x
    >>> f, g, h = map(Function, ['f', 'g', 'h'])
    >>> genform = g(x/f(x)) + h(x/f(x))*f(x).diff(x)
    >>> pprint(genform)
     / x  \    / x  \ d
    g|----| + h|----|*--(f(x))
     \f(x)/    \f(x)/ dx
    >>> pprint(dsolve(genform, f(x),
    ... hint='1st_homogeneous_coeff_subs_indep_div_dep_Integral'))
                 x
                ----
                f(x)
                  /
                 |
                 |       -g(u2)
                 |  ---------------- d(u2)
                 |  u2*g(u2) + h(u2)
                 |
                /
    <BLANKLINE>
    f(x) = C1*e

    Where `u_2 g(u_2) + h(u_2) \ne 0` and `f(x) \ne 0`.

    See also the docstrings of
    :py:meth:`~sympy.solvers.ode.ode_1st_homogeneous_coeff_best` and
    :py:meth:`~sympy.solvers.ode.ode_1st_homogeneous_coeff_subs_dep_div_indep`.

    Examples
    ========

    >>> from sympy import Function, pprint, dsolve
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> pprint(dsolve(2*x*f(x) + (x**2 + f(x)**2)*f(x).diff(x), f(x),
    ... hint='1st_homogeneous_coeff_subs_indep_div_dep',
    ... simplify=False))
                             /    2    \
                             | 3*x     |
                          log|----- + 1|
                             | 2       |
                             \f (x)    /
    log(f(x)) = log(C1) - --------------
                                3

    References
    ==========

    - https://en.wikipedia.org/wiki/Homogeneous_differential_equation
    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 59

    # indirect doctest

    """
    x = func.args[0]
    f = func.func
    u = Dummy('u')
    u2 = Dummy('u2')  # u2 == x/f(x)
    r = match  # d+e*diff(f(x),x)
    C1 = get_numbered_constants(eq, num=1)
    xarg = match.get('xarg', 0)  # If xarg present take xarg, else zero
    yarg = match.get('yarg', 0)  # If yarg present take yarg, else zero
    int = Integral(
        simplify(
            (-r[r['d']]/(r[r['e']] + u2*r[r['d']])).subs({x: u2, r['y']: 1})),
        (u2, None, x/f(x)))
    sol = logcombine(Eq(log(f(x)), int + log(C1)), force=True)
    sol = sol.subs(f(x), u).subs(((u, u - yarg), (x, x - xarg), (u, f(x))))
    return sol

# XXX: Should this function maybe go somewhere else?


def homogeneous_order(eq, *symbols):
    r"""
    Returns the order `n` if `g` is homogeneous and ``None`` if it is not
    homogeneous.

    Determines if a function is homogeneous and if so of what order.  A
    function `f(x, y, \cdots)` is homogeneous of order `n` if `f(t x, t y,
    \cdots) = t^n f(x, y, \cdots)`.

    If the function is of two variables, `F(x, y)`, then `f` being homogeneous
    of any order is equivalent to being able to rewrite `F(x, y)` as `G(x/y)`
    or `H(y/x)`.  This fact is used to solve 1st order ordinary differential
    equations whose coefficients are homogeneous of the same order (see the
    docstrings of
    :py:meth:`~solvers.ode.ode_1st_homogeneous_coeff_subs_dep_div_indep` and
    :py:meth:`~solvers.ode.ode_1st_homogeneous_coeff_subs_indep_div_dep`).

    Symbols can be functions, but every argument of the function must be a
    symbol, and the arguments of the function that appear in the expression
    must match those given in the list of symbols.  If a declared function
    appears with different arguments than given in the list of symbols,
    ``None`` is returned.

    Examples
    ========

    >>> from sympy import Function, homogeneous_order, sqrt
    >>> from sympy.abc import x, y
    >>> f = Function('f')
    >>> homogeneous_order(f(x), f(x)) is None
    True
    >>> homogeneous_order(f(x,y), f(y, x), x, y) is None
    True
    >>> homogeneous_order(f(x), f(x), x)
    1
    >>> homogeneous_order(x**2*f(x)/sqrt(x**2+f(x)**2), x, f(x))
    2
    >>> homogeneous_order(x**2+f(x), x, f(x)) is None
    True

    """

    if not symbols:
        raise ValueError("homogeneous_order: no symbols were given.")
    symset = set(symbols)
    eq = sympify(eq)

    # The following are not supported
    if eq.has(Order, Derivative):
        return None

    # These are all constants
    if (eq.is_Number or
        eq.is_NumberSymbol or
        eq.is_number
            ):
        return S.Zero

    # Replace all functions with dummy variables
    dum = numbered_symbols(prefix='d', cls=Dummy)
    newsyms = set()
    for i in [j for j in symset if getattr(j, 'is_Function')]:
        iargs = set(i.args)
        if iargs.difference(symset):
            return None
        else:
            dummyvar = next(dum)
            eq = eq.subs(i, dummyvar)
            symset.remove(i)
            newsyms.add(dummyvar)
    symset.update(newsyms)

    if not eq.free_symbols & symset:
        return None

    # assuming order of a nested function can only be equal to zero
    if isinstance(eq, Function):
        return None if homogeneous_order(
            eq.args[0], *tuple(symset)) != 0 else S.Zero

    # make the replacement of x with x*t and see if t can be factored out
    t = Dummy('t', positive=True)  # It is sufficient that t > 0
    eqs = separatevars(eq.subs([(i, t*i) for i in symset]), [t], dict=True)[t]
    if eqs is S.One:
        return S.Zero  # there was no term with only t
    i, d = eqs.as_independent(t, as_Add=False)
    b, e = d.as_base_exp()
    if b == t:
        return e


def ode_1st_linear(eq, func, order, match):
    r"""
    Solves 1st order linear differential equations.

    These are differential equations of the form

    .. math:: dy/dx + P(x) y = Q(x)\text{.}

    These kinds of differential equations can be solved in a general way.  The
    integrating factor `e^{\int P(x) \,dx}` will turn the equation into a
    separable equation.  The general solution is::

        >>> from sympy import Function, dsolve, Eq, pprint, diff, sin
        >>> from sympy.abc import x
        >>> f, P, Q = map(Function, ['f', 'P', 'Q'])
        >>> genform = Eq(f(x).diff(x) + P(x)*f(x), Q(x))
        >>> pprint(genform)
                    d
        P(x)*f(x) + --(f(x)) = Q(x)
                    dx
        >>> pprint(dsolve(genform, f(x), hint='1st_linear_Integral'))
               /       /                   \
               |      |                    |
               |      |         /          |     /
               |      |        |           |    |
               |      |        | P(x) dx   |  - | P(x) dx
               |      |        |           |    |
               |      |       /            |   /
        f(x) = |C1 +  | Q(x)*e           dx|*e
               |      |                    |
               \     /                     /


    Examples
    ========

    >>> f = Function('f')
    >>> pprint(dsolve(Eq(x*diff(f(x), x) - f(x), x**2*sin(x)),
    ... f(x), '1st_linear'))
    f(x) = x*(C1 - cos(x))

    References
    ==========

    - https://en.wikipedia.org/wiki/Linear_differential_equation#First_order_equation
    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 92

    # indirect doctest

    """
    x = func.args[0]
    f = func.func
    r = match  # a*diff(f(x),x) + b*f(x) + c
    C1 = get_numbered_constants(eq, num=1)
    t = exp(Integral(r[r['b']]/r[r['a']], x))
    tt = Integral(t*(-r[r['c']]/r[r['a']]), x)
    f = match.get('u', f(x))  # take almost-linear u if present, else f(x)
    return Eq(f, (tt + C1)/t)


def ode_Bernoulli(eq, func, order, match):
    r"""
    Solves Bernoulli differential equations.

    These are equations of the form

    .. math:: dy/dx + P(x) y = Q(x) y^n\text{, }n \ne 1`\text{.}

    The substitution `w = 1/y^{1-n}` will transform an equation of this form
    into one that is linear (see the docstring of
    :py:meth:`~sympy.solvers.ode.ode_1st_linear`).  The general solution is::

        >>> from sympy import Function, dsolve, Eq, pprint
        >>> from sympy.abc import x, n
        >>> f, P, Q = map(Function, ['f', 'P', 'Q'])
        >>> genform = Eq(f(x).diff(x) + P(x)*f(x), Q(x)*f(x)**n)
        >>> pprint(genform)
                    d                n
        P(x)*f(x) + --(f(x)) = Q(x)*f (x)
                    dx
        >>> pprint(dsolve(genform, f(x), hint='Bernoulli_Integral')) #doctest: +SKIP
                                                                                       1
                                                                                      ----
                                                                                     1 - n
               //                /                            \                     \
               ||               |                             |                     |
               ||               |                  /          |             /       |
               ||               |                 |           |            |        |
               ||               |        (1 - n)* | P(x) dx   |  (-1 + n)* | P(x) dx|
               ||               |                 |           |            |        |
               ||               |                /            |           /         |
        f(x) = ||C1 + (-1 + n)* | -Q(x)*e                   dx|*e                   |
               ||               |                             |                     |
               \\               /                            /                     /


    Note that the equation is separable when `n = 1` (see the docstring of
    :py:meth:`~sympy.solvers.ode.ode_separable`).

    >>> pprint(dsolve(Eq(f(x).diff(x) + P(x)*f(x), Q(x)*f(x)), f(x),
    ... hint='separable_Integral'))
     f(x)
       /
      |                /
      |  1            |
      |  - dy = C1 +  | (-P(x) + Q(x)) dx
      |  y            |
      |              /
     /


    Examples
    ========

    >>> from sympy import Function, dsolve, Eq, pprint, log
    >>> from sympy.abc import x
    >>> f = Function('f')

    >>> pprint(dsolve(Eq(x*f(x).diff(x) + f(x), log(x)*f(x)**2),
    ... f(x), hint='Bernoulli'))
                    1
    f(x) = -------------------
             /     log(x)   1\
           x*|C1 + ------ + -|
             \       x      x/

    References
    ==========

    - https://en.wikipedia.org/wiki/Bernoulli_differential_equation
    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 95

    # indirect doctest

    """
    x = func.args[0]
    f = func.func
    r = match  # a*diff(f(x),x) + b*f(x) + c*f(x)**n, n != 1
    C1 = get_numbered_constants(eq, num=1)
    t = exp((1 - r[r['n']])*Integral(r[r['b']]/r[r['a']], x))
    tt = (r[r['n']] - 1)*Integral(t*r[r['c']]/r[r['a']], x)
    return Eq(f(x), ((tt + C1)/t)**(1/(1 - r[r['n']])))


def ode_Riccati_special_minus2(eq, func, order, match):
    r"""
    The general Riccati equation has the form

    .. math:: dy/dx = f(x) y^2 + g(x) y + h(x)\text{.}

    While it does not have a general solution [1], the "special" form, `dy/dx
    = a y^2 - b x^c`, does have solutions in many cases [2].  This routine
    returns a solution for `a(dy/dx) = b y^2 + c y/x + d/x^2` that is obtained
    by using a suitable change of variables to reduce it to the special form
    and is valid when neither `a` nor `b` are zero and either `c` or `d` is
    zero.

    >>> from sympy.abc import x, y, a, b, c, d
    >>> from sympy.solvers.ode import dsolve, checkodesol
    >>> from sympy import pprint, Function
    >>> f = Function('f')
    >>> y = f(x)
    >>> genform = a*y.diff(x) - (b*y**2 + c*y/x + d/x**2)
    >>> sol = dsolve(genform, y)
    >>> pprint(sol, wrap_line=False)
            /                                 /        __________________       \\
            |           __________________    |       /                2        ||
            |          /                2     |     \/  4*b*d - (a + c)  *log(x)||
           -|a + c - \/  4*b*d - (a + c)  *tan|C1 + ----------------------------||
            \                                 \                 2*a             //
    f(x) = ------------------------------------------------------------------------
                                            2*b*x

    >>> checkodesol(genform, sol, order=1)[0]
    True

    References
    ==========

    1. http://www.maplesoft.com/support/help/Maple/view.aspx?path=odeadvisor/Riccati
    2. http://eqworld.ipmnet.ru/en/solutions/ode/ode0106.pdf -
       http://eqworld.ipmnet.ru/en/solutions/ode/ode0123.pdf
    """

    x = func.args[0]
    f = func.func
    r = match  # a2*diff(f(x),x) + b2*f(x) + c2*f(x)/x + d2/x**2
    a2, b2, c2, d2 = [r[r[s]] for s in 'a2 b2 c2 d2'.split()]
    C1 = get_numbered_constants(eq, num=1)
    mu = sqrt(4*d2*b2 - (a2 - c2)**2)
    return Eq(f(x), (a2 - c2 - mu*tan(mu/(2*a2)*log(x) + C1))/(2*b2*x))


def ode_Liouville(eq, func, order, match):
    r"""
    Solves 2nd order Liouville differential equations.

    The general form of a Liouville ODE is

    .. math:: \frac{d^2 y}{dx^2} + g(y) \left(\!
                \frac{dy}{dx}\!\right)^2 + h(x)
                \frac{dy}{dx}\text{.}

    The general solution is:

        >>> from sympy import Function, dsolve, Eq, pprint, diff
        >>> from sympy.abc import x
        >>> f, g, h = map(Function, ['f', 'g', 'h'])
        >>> genform = Eq(diff(f(x),x,x) + g(f(x))*diff(f(x),x)**2 +
        ... h(x)*diff(f(x),x), 0)
        >>> pprint(genform)
                          2                    2
                /d       \         d          d
        g(f(x))*|--(f(x))|  + h(x)*--(f(x)) + ---(f(x)) = 0
                \dx      /         dx           2
                                              dx
        >>> pprint(dsolve(genform, f(x), hint='Liouville_Integral'))
                                          f(x)
                  /                     /
                 |                     |
                 |     /               |     /
                 |    |                |    |
                 |  - | h(x) dx        |    | g(y) dy
                 |    |                |    |
                 |   /                 |   /
        C1 + C2* | e            dx +   |  e           dy = 0
                 |                     |
                /                     /

    Examples
    ========

    >>> from sympy import Function, dsolve, Eq, pprint
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> pprint(dsolve(diff(f(x), x, x) + diff(f(x), x)**2/f(x) +
    ... diff(f(x), x)/x, f(x), hint='Liouville'))
               ________________           ________________
    [f(x) = -\/ C1 + C2*log(x) , f(x) = \/ C1 + C2*log(x) ]

    References
    ==========

    - Goldstein and Braun, "Advanced Methods for the Solution of Differential
      Equations", pp. 98
    - http://www.maplesoft.com/support/help/Maple/view.aspx?path=odeadvisor/Liouville

    # indirect doctest

    """
    # Liouville ODE:
    #  f(x).diff(x, 2) + g(f(x))*(f(x).diff(x, 2))**2 + h(x)*f(x).diff(x)
    # See Goldstein and Braun, "Advanced Methods for the Solution of
    # Differential Equations", pg. 98, as well as
    # http://www.maplesoft.com/support/help/view.aspx?path=odeadvisor/Liouville
    x = func.args[0]
    f = func.func
    r = match  # f(x).diff(x, 2) + g*f(x).diff(x)**2 + h*f(x).diff(x)
    y = r['y']
    C1, C2 = get_numbered_constants(eq, num=2)
    int = Integral(exp(Integral(r['g'], y)), (y, None, f(x)))
    sol = Eq(int + C1*Integral(exp(-Integral(r['h'], x)), x) + C2, 0)
    return sol


def ode_2nd_power_series_ordinary(eq, func, order, match):
    r"""
    Gives a power series solution to a second order homogeneous differential
    equation with polynomial coefficients at an ordinary point. A homogenous
    differential equation is of the form

    .. math :: P(x)\frac{d^2y}{dx^2} + Q(x)\frac{dy}{dx} + R(x) = 0

    For simplicity it is assumed that `P(x)`, `Q(x)` and `R(x)` are polynomials,
    it is sufficient that `\frac{Q(x)}{P(x)}` and `\frac{R(x)}{P(x)}` exists at
    `x_{0}`. A recurrence relation is obtained by substituting `y` as `\sum_{n=0}^\infty a_{n}x^{n}`,
    in the differential equation, and equating the nth term. Using this relation
    various terms can be generated.


    Examples
    ========

    >>> from sympy import dsolve, Function, pprint
    >>> from sympy.abc import x, y
    >>> f = Function("f")
    >>> eq = f(x).diff(x, 2) + f(x)
    >>> pprint(dsolve(eq, hint='2nd_power_series_ordinary'))
              / 4    2    \        /     2\
              |x    x     |        |    x |    / 6\
    f(x) = C2*|-- - -- + 1| + C1*x*|1 - --| + O\x /
              \24   2     /        \    6 /


    References
    ==========
    - http://tutorial.math.lamar.edu/Classes/DE/SeriesSolutions.aspx
    - George E. Simmons, "Differential Equations with Applications and
      Historical Notes", p.p 176 - 184

    """
    x = func.args[0]
    f = func.func
    C0, C1 = get_numbered_constants(eq, num=2)
    n = Dummy("n", integer=True)
    s = Wild("s")
    k = Wild("k", exclude=[x])
    x0 = match.get('x0')
    terms = match.get('terms', 5)
    p = match[match['a3']]
    q = match[match['b3']]
    r = match[match['c3']]
    seriesdict = {}
    recurr = Function("r")

    # Generating the recurrence relation which works this way:
    # for the second order term the summation begins at n = 2. The coefficients
    # p is multiplied with an*(n - 1)*(n - 2)*x**n-2 and a substitution is made such that
    # the exponent of x becomes n.
    # For example, if p is x, then the second degree recurrence term is
    # an*(n - 1)*(n - 2)*x**n-1, substituting (n - 1) as n, it transforms to
    # an+1*n*(n - 1)*x**n.
    # A similar process is done with the first order and zeroth order term.

    coefflist = [(recurr(n), r), (n*recurr(n), q), (n*(n - 1)*recurr(n), p)]
    for index, coeff in enumerate(coefflist):
        if coeff[1]:
            f2 = powsimp(expand((coeff[1]*(x - x0)**(n - index)).subs(x, x + x0)))
            if f2.is_Add:
                addargs = f2.args
            else:
                addargs = [f2]
            for arg in addargs:
                powm = arg.match(s*x**k)
                term = coeff[0]*powm[s]
                if not powm[k].is_Symbol:
                    term = term.subs(n, n - powm[k].as_independent(n)[0])
                startind = powm[k].subs(n, index)
                # Seeing if the startterm can be reduced further.
                # If it vanishes for n lesser than startind, it is
                # equal to summation from n.
                if startind:
                    for i in reversed(range(startind)):
                        if not term.subs(n, i):
                            seriesdict[term] = i
                        else:
                            seriesdict[term] = i + 1
                            break
                else:
                    seriesdict[term] = S(0)

    # Stripping of terms so that the sum starts with the same number.
    teq = S(0)
    suminit = seriesdict.values()
    rkeys = seriesdict.keys()
    req = Add(*rkeys)
    if any(suminit):
        maxval = max(suminit)
        for term in seriesdict:
            val = seriesdict[term]
            if val != maxval:
                for i in range(val, maxval):
                    teq += term.subs(n, val)

    finaldict = {}
    if teq:
        fargs = teq.atoms(AppliedUndef)
        if len(fargs) == 1:
            finaldict[fargs.pop()] = 0
        else:
            maxf = max(fargs, key = lambda x: x.args[0])
            sol = solve(teq, maxf)
            if isinstance(sol, list):
                sol = sol[0]
            finaldict[maxf] = sol

    # Finding the recurrence relation in terms of the largest term.
    fargs = req.atoms(AppliedUndef)
    maxf = max(fargs, key = lambda x: x.args[0])
    minf = min(fargs, key = lambda x: x.args[0])
    if minf.args[0].is_Symbol:
        startiter = 0
    else:
        startiter = -minf.args[0].as_independent(n)[0]
    lhs = maxf
    rhs =  solve(req, maxf)
    if isinstance(rhs, list):
        rhs = rhs[0]

    # Checking how many values are already present
    tcounter = len([t for t in finaldict.values() if t])

    for _ in range(tcounter, terms - 3):  # Assuming c0 and c1 to be arbitrary
        check = rhs.subs(n, startiter)
        nlhs = lhs.subs(n, startiter)
        nrhs = check.subs(finaldict)
        finaldict[nlhs] = nrhs
        startiter += 1

    # Post processing
    series = C0 + C1*(x - x0)
    for term in finaldict:
        if finaldict[term]:
            fact = term.args[0]
            series += (finaldict[term].subs([(recurr(0), C0), (recurr(1), C1)])*(
                x - x0)**fact)
    series = collect(expand_mul(series), [C0, C1]) + Order(x**terms)
    return Eq(f(x), series)



def ode_2nd_power_series_regular(eq, func, order, match):
    r"""
    Gives a power series solution to a second order homogeneous differential
    equation with polynomial coefficients at a regular point. A second order
    homogenous differential equation is of the form

    .. math :: P(x)\frac{d^2y}{dx^2} + Q(x)\frac{dy}{dx} + R(x) = 0

    A point is said to regular singular at `x0` if `x - x0\frac{Q(x)}{P(x)}`
    and `(x - x0)^{2}\frac{R(x)}{P(x)}` are analytic at `x0`. For simplicity
    `P(x)`, `Q(x)` and `R(x)` are assumed to be polynomials. The algorithm for
    finding the power series solutions is:

    1.  Try expressing `(x - x0)P(x)` and `((x - x0)^{2})Q(x)` as power series
        solutions about x0. Find `p0` and `q0` which are the constants of the
        power series expansions.
    2.  Solve the indicial equation `f(m) = m(m - 1) + m*p0 + q0`, to obtain the
        roots `m1` and `m2` of the indicial equation.
    3.  If `m1 - m2` is a non integer there exists two series solutions. If
        `m1 = m2`, there exists only one solution. If `m1 - m2` is an integer,
        then the existence of one solution is confirmed. The other solution may
        or may not exist.

    The power series solution is of the form `x^{m}\sum_{n=0}^\infty a_{n}x^{n}`. The
    coefficients are determined by the following recurrence relation.
    `a_{n} = -\frac{\sum_{k=0}^{n-1} q_{n-k} + (m + k)p_{n-k}}{f(m + n)}`. For the case
    in which `m1 - m2` is an integer, it can be seen from the recurrence relation
    that for the lower root `m`, when `n` equals the difference of both the
    roots, the denominator becomes zero. So if the numerator is not equal to zero,
    a second series solution exists.


    Examples
    ========

    >>> from sympy import dsolve, Function, pprint
    >>> from sympy.abc import x, y
    >>> f = Function("f")
    >>> eq = x*(f(x).diff(x, 2)) + 2*(f(x).diff(x)) + x*f(x)
    >>> pprint(dsolve(eq))
                                  /    6    4    2    \
                                  |   x    x    x     |
              /  4    2    \   C1*|- --- + -- - -- + 1|
              | x    x     |      \  720   24   2     /    / 6\
    f(x) = C2*|--- - -- + 1| + ------------------------ + O\x /
              \120   6     /              x


    References
    ==========
    - George E. Simmons, "Differential Equations with Applications and
      Historical Notes", p.p 176 - 184

    """
    x = func.args[0]
    f = func.func
    C0, C1 = get_numbered_constants(eq, num=2)
    n = Dummy("n")
    m = Dummy("m")  # for solving the indicial equation
    s = Wild("s")
    k = Wild("k", exclude=[x])
    x0 = match.get('x0')
    terms = match.get('terms', 5)
    p = match['p']
    q = match['q']

    # Generating the indicial equation
    indicial = []
    for term in [p, q]:
        if not term.has(x):
            indicial.append(term)
        else:
            term = series(term, n=1, x0=x0)
            if isinstance(term, Order):
                indicial.append(S(0))
            else:
                for arg in term.args:
                    if not arg.has(x):
                        indicial.append(arg)
                        break

    p0, q0 = indicial
    sollist = solve(m*(m - 1) + m*p0 + q0, m)
    if sollist and isinstance(sollist, list) and all(
        [sol.is_real for sol in sollist]):
        serdict1 = {}
        serdict2 = {}
        if len(sollist) == 1:
            # Only one series solution exists in this case.
            m1 = m2 = sollist.pop()
            if terms-m1-1 <= 0:
              return Eq(f(x), Order(terms))
            serdict1 = _frobenius(terms-m1-1, m1, p0, q0, p, q, x0, x, C0)

        else:
            m1 = sollist[0]
            m2 = sollist[1]
            if m1 < m2:
                m1, m2 = m2, m1
            # Irrespective of whether m1 - m2 is an integer or not, one
            # Frobenius series solution exists.
            serdict1 = _frobenius(terms-m1-1, m1, p0, q0, p, q, x0, x, C0)
            if not (m1 - m2).is_integer:
                # Second frobenius series solution exists.
                serdict2 = _frobenius(terms-m2-1, m2, p0, q0, p, q, x0, x, C1)
            else:
                # Check if second frobenius series solution exists.
                serdict2 = _frobenius(terms-m2-1, m2, p0, q0, p, q, x0, x, C1, check=m1)

        if serdict1:
            finalseries1 = C0
            for key in serdict1:
                power = int(key.name[1:])
                finalseries1 += serdict1[key]*(x - x0)**power
            finalseries1 = (x - x0)**m1*finalseries1
            finalseries2 = S(0)
            if serdict2:
                for key in serdict2:
                    power = int(key.name[1:])
                    finalseries2 += serdict2[key]*(x - x0)**power
                finalseries2 += C1
                finalseries2 = (x - x0)**m2*finalseries2
            return Eq(f(x), collect(finalseries1 + finalseries2,
                [C0, C1]) + Order(x**terms))

def _frobenius(n, m, p0, q0, p, q, x0, x, c, check=None):
    r"""
    Returns a dict with keys as coefficients and values as their values in terms of C0
    """
    n = int(n)
    # In cases where m1 - m2 is not an integer
    m2 = check

    d = Dummy("d")
    numsyms = numbered_symbols("C", start=0)
    numsyms = [next(numsyms) for i in range(n + 1)]
    C0 = Symbol("C0")
    serlist = []
    for ser in [p, q]:
        # Order term not present
        if ser.is_polynomial(x) and Poly(ser, x).degree() <= n:
            if x0:
                ser = ser.subs(x, x + x0)
            dict_ = Poly(ser, x).as_dict()
        # Order term present
        else:
            tseries = series(ser, x=x0, n=n+1)
            # Removing order
            dict_ = Poly(list(ordered(tseries.args))[: -1], x).as_dict()
        # Fill in with zeros, if coefficients are zero.
        for i in range(n + 1):
            if (i,) not in dict_:
                dict_[(i,)] = S(0)
        serlist.append(dict_)

    pseries = serlist[0]
    qseries = serlist[1]
    indicial = d*(d - 1) + d*p0 + q0
    frobdict = {}
    for i in range(1, n + 1):
        num = c*(m*pseries[(i,)] + qseries[(i,)])
        for j in range(1, i):
            sym = Symbol("C" + str(j))
            num += frobdict[sym]*((m + j)*pseries[(i - j,)] + qseries[(i - j,)])

        # Checking for cases when m1 - m2 is an integer. If num equals zero
        # then a second Frobenius series solution cannot be found. If num is not zero
        # then set constant as zero and proceed.
        if m2 is not None and i == m2 - m:
            if num:
                return False
            else:
                frobdict[numsyms[i]] = S(0)
        else:
            frobdict[numsyms[i]] = -num/(indicial.subs(d, m+i))

    return frobdict

def _nth_order_reducible_match(eq, func):
    r"""
    Matches any differential equation that can be rewritten with a smaller
    order. Only derivatives of ``func`` alone, wrt a single variable,
    are considered, and only in them should ``func`` appear.
    """
    # ODE only handles functions of 1 variable so this affirms that state
    assert len(func.args) == 1
    x = func.args[0]
    vc= [d.variable_count[0] for d in eq.atoms(Derivative)
         if d.expr == func and len(d.variable_count) == 1]
    ords = [c for v, c in vc if v == x]
    if len(ords) < 2:
        return
    smallest = min(ords)
    # make sure func does not appear outside of derivatives
    D = Dummy()
    if eq.subs(func.diff(x, smallest), D).has(func):
        return
    return {'n': smallest}

def ode_nth_order_reducible(eq, func, order, match):
    r"""
    Solves ODEs that only involve derivatives of the dependent variable using
    a substitution of the form `f^n(x) = g(x)`.

    For example any second order ODE of the form `f''(x) = h(f'(x), x)` can be
    transformed into a pair of 1st order ODEs `g'(x) = h(g(x), x)` and
    `f'(x) = g(x)`. Usually the 1st order ODE for `g` is easier to solve. If
    that gives an explicit solution for `g` then `f` is found simply by
    integration.


    Examples
    ========

    >>> from sympy import Function, dsolve, Eq
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> eq = Eq(x*f(x).diff(x)**2 + f(x).diff(x, 2))
    >>> dsolve(eq, f(x), hint='nth_order_reducible')
    ... # doctest: +NORMALIZE_WHITESPACE
    Eq(f(x), C1 - sqrt(-1/C2)*log(-C2*sqrt(-1/C2) + x) + sqrt(-1/C2)*log(C2*sqrt(-1/C2) + x))

    """
    x = func.args[0]
    f = func.func
    n = match['n']
    # get a unique function name for g
    names = [a.name for a in eq.atoms(AppliedUndef)]
    while True:
        name = Dummy().name
        if name not in names:
            g = Function(name)
            break
    w = f(x).diff(x, n)
    geq = eq.subs(w, g(x))
    gsol = dsolve(geq, g(x))

    if not isinstance(gsol, list):
        gsol = [gsol]

    # Might be multiple solutions to the reduced ODE:
    fsol = []
    for gsoli in gsol:
        fsoli = dsolve(gsoli.subs(g(x), w), f(x))  # or do integration n times
        fsol.append(fsoli)

    if len(fsol) == 1:
        fsol = fsol[0]

    return fsol

def _nth_algebraic_match(eq, func):
    r"""
    Matches any differential equation that nth_algebraic can solve. Uses
    `sympy.solve` but teaches it how to integrate derivatives.

    This involves calling `sympy.solve` and does most of the work of finding a
    solution (apart from evaluating the integrals).
    """

    # Each integration should generate a different constant
    constants = iter_numbered_constants(eq)
    constant = lambda: next(constants, None)

    # Like Derivative but "invertible"
    class diffx(Function):
        def inverse(self):
            # We mustn't use integrate here because fx has been replaced by _t
            # in the equation so integrals will not be correct while solve is
            # still working.
            return lambda expr: Integral(expr, var) + constant()

    # Replace derivatives wrt the independent variable with diffx
    def replace(eq, var):
        def expand_diffx(*args):
            differand, diffs = args[0], args[1:]
            toreplace = differand
            for v, n in diffs:
                for _ in range(n):
                    if v == var:
                        toreplace = diffx(toreplace)
                    else:
                        toreplace = Derivative(toreplace, v)
            return toreplace
        return eq.replace(Derivative, expand_diffx)

    # Restore derivatives in solution afterwards
    def unreplace(eq, var):
        return eq.replace(diffx, lambda e: Derivative(e, var))

    # The independent variable
    var = func.args[0]
    subs_eqn = replace(eq, var)
    try:
        solns = solve(subs_eqn, func)
    except NotImplementedError:
        solns = []

    solns = [unreplace(soln, var) for soln in solns]
    solns = [Equality(func, soln) for soln in solns]
    return {'var':var, 'solutions':solns}

def ode_nth_algebraic(eq, func, order, match):
    r"""
    Solves an `n`\th order ordinary differential equation using algebra and
    integrals.

    There is no general form for the kind of equation that this can solve. The
    the equation is solved algebraically treating differentiation as an
    invertible algebraic function.

    Examples
    ========

    >>> from sympy import Function, dsolve, Eq
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> eq = Eq(f(x) * (f(x).diff(x)**2 - 1), 0)
    >>> dsolve(eq, f(x), hint='nth_algebraic')
    ... # doctest: +NORMALIZE_WHITESPACE
    [Eq(f(x), 0), Eq(f(x), C1 - x), Eq(f(x), C1 + x)]

    Note that this solver can return algebraic solutions that do not have any
    integration constants (f(x) = 0 in the above example).

    # indirect doctest

    """
    solns = match['solutions']
    var = match['var']
    solns = _nth_algebraic_remove_redundant_solutions(eq, solns, order, var)
    if len(solns) == 1:
        return solns[0]
    else:
        return solns

# FIXME: Maybe something like this function should be applied to the solutions
# returned by dsolve in general rather than just for nth_algebraic...

def _nth_algebraic_remove_redundant_solutions(eq, solns, order, var):
    r"""
    Remove redundant solutions from the set of solutions returned by
    nth_algebraic.

    This function is needed because otherwise nth_algebraic can return
    redundant solutions where both algebraic solutions and integral
    solutions are found to the ODE. As an example consider:

        eq = Eq(f(x) * f(x).diff(x), 0)

    There are two ways to find solutions to eq. The first is the algebraic
    solution f(x)=0. The second is to solve the equation f(x).diff(x) = 0
    leading to the solution f(x) = C1. In this particular case we then see
    that the first solution is a special case of the second and we don't
    want to return it.

    This does not always happen for algebraic solutions though since if we
    have

        eq = Eq(f(x)*(1 + f(x).diff(x)), 0)

    then we get the algebraic solution f(x) = 0 and the integral solution
    f(x) = -x + C1 and in this case the two solutions are not equivalent wrt
    initial conditions so both should be returned.
    """
    def is_special_case_of(soln1, soln2):
        return _nth_algebraic_is_special_case_of(soln1, soln2, eq, order, var)

    unique_solns = []
    for soln1 in solns:
        for soln2 in unique_solns[:]:
            if is_special_case_of(soln1, soln2):
                break
            elif is_special_case_of(soln2, soln1):
                unique_solns.remove(soln2)
        else:
            unique_solns.append(soln1)

    return unique_solns

def _nth_algebraic_is_special_case_of(soln1, soln2, eq, order, var):
    r"""
    True if soln1 is found to be a special case of soln2 wrt some value of the
    constants that appear in soln2. False otherwise.
    """
    # The solutions returned by nth_algebraic should be given explicitly as in
    # Eq(f(x), expr). We will equate the RHSs of the two solutions giving an
    # equation f1(x) = f2(x).
    #
    # Since this is supposed to hold for all x it also holds for derivatives
    # f1'(x) and f2'(x). For an order n ode we should be able to differentiate
    # each solution n times to get n+1 equations.
    #
    # We then try to solve those n+1 equations for the integrations constants
    # in f2(x). If we can find a solution that doesn't depend on x then it
    # means that some value of the constants in f1(x) is a special case of
    # f2(x) corresponding to a paritcular choice of the integration constants.

    constants1 = soln1.free_symbols.difference(eq.free_symbols)
    constants2 = soln2.free_symbols.difference(eq.free_symbols)

    constants1_new = get_numbered_constants(soln1.rhs - soln2.rhs, len(constants1))
    if len(constants1) == 1:
        constants1_new = {constants1_new}
    for c_old, c_new in zip(constants1, constants1_new):
        soln1 = soln1.subs(c_old, c_new)

    # n equations for f1(x)=f2(x), f1'(x)=f2'(x), ...
    lhs = soln1.rhs.doit()
    rhs = soln2.rhs.doit()
    eqns = [Eq(lhs, rhs)]
    for n in range(1, order):
        lhs = lhs.diff(var)
        rhs = rhs.diff(var)
        eq = Eq(lhs, rhs)
        eqns.append(eq)

    # BooleanTrue/False awkwardly show up for trivial equations
    if any(isinstance(eq, BooleanFalse) for eq in eqns):
        return False
    eqns = [eq for eq in eqns if not isinstance(eq, BooleanTrue)]

    constant_solns = solve(eqns, constants2)

    # Sometimes returns a dict and sometimes a list of dicts
    if isinstance(constant_solns, dict):
        constant_solns = [constant_solns]

    # If any solution gives all constants as expressions that don't depend on
    # x then there exists constants for soln2 that give soln1
    for constant_soln in constant_solns:
        if not any(c.has(var) for c in constant_soln.values()):
            return True
    else:
        return False


def _nth_linear_match(eq, func, order):
    r"""
    Matches a differential equation to the linear form:

    .. math:: a_n(x) y^{(n)} + \cdots + a_1(x)y' + a_0(x) y + B(x) = 0

    Returns a dict of order:coeff terms, where order is the order of the
    derivative on each term, and coeff is the coefficient of that derivative.
    The key ``-1`` holds the function `B(x)`. Returns ``None`` if the ODE is
    not linear.  This function assumes that ``func`` has already been checked
    to be good.

    Examples
    ========

    >>> from sympy import Function, cos, sin
    >>> from sympy.abc import x
    >>> from sympy.solvers.ode import _nth_linear_match
    >>> f = Function('f')
    >>> _nth_linear_match(f(x).diff(x, 3) + 2*f(x).diff(x) +
    ... x*f(x).diff(x, 2) + cos(x)*f(x).diff(x) + x - f(x) -
    ... sin(x), f(x), 3)
    {-1: x - sin(x), 0: -1, 1: cos(x) + 2, 2: x, 3: 1}
    >>> _nth_linear_match(f(x).diff(x, 3) + 2*f(x).diff(x) +
    ... x*f(x).diff(x, 2) + cos(x)*f(x).diff(x) + x - f(x) -
    ... sin(f(x)), f(x), 3) == None
    True

    """
    x = func.args[0]
    one_x = {x}
    terms = {i: S.Zero for i in range(-1, order + 1)}
    for i in Add.make_args(eq):
        if not i.has(func):
            terms[-1] += i
        else:
            c, f = i.as_independent(func)
            if (isinstance(f, Derivative)
                    and set(f.variables) == one_x
                    and f.args[0] == func):
                terms[f.derivative_count] += c
            elif f == func:
                terms[len(f.args[1:])] += c
            else:
                return None
    return terms


def ode_nth_linear_euler_eq_homogeneous(eq, func, order, match, returns='sol'):
    r"""
    Solves an `n`\th order linear homogeneous variable-coefficient
    Cauchy-Euler equidimensional ordinary differential equation.

    This is an equation with form `0 = a_0 f(x) + a_1 x f'(x) + a_2 x^2 f''(x)
    \cdots`.

    These equations can be solved in a general manner, by substituting
    solutions of the form `f(x) = x^r`, and deriving a characteristic equation
    for `r`.  When there are repeated roots, we include extra terms of the
    form `C_{r k} \ln^k(x) x^r`, where `C_{r k}` is an arbitrary integration
    constant, `r` is a root of the characteristic equation, and `k` ranges
    over the multiplicity of `r`.  In the cases where the roots are complex,
    solutions of the form `C_1 x^a \sin(b \log(x)) + C_2 x^a \cos(b \log(x))`
    are returned, based on expansions with Euler's formula.  The general
    solution is the sum of the terms found.  If SymPy cannot find exact roots
    to the characteristic equation, a
    :py:class:`~sympy.polys.rootoftools.CRootOf` instance will be returned
    instead.

    >>> from sympy import Function, dsolve, Eq
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> dsolve(4*x**2*f(x).diff(x, 2) + f(x), f(x),
    ... hint='nth_linear_euler_eq_homogeneous')
    ... # doctest: +NORMALIZE_WHITESPACE
    Eq(f(x), sqrt(x)*(C1 + C2*log(x)))

    Note that because this method does not involve integration, there is no
    ``nth_linear_euler_eq_homogeneous_Integral`` hint.

    The following is for internal use:

    - ``returns = 'sol'`` returns the solution to the ODE.
    - ``returns = 'list'`` returns a list of linearly independent solutions,
      corresponding to the fundamental solution set, for use with non
      homogeneous solution methods like variation of parameters and
      undetermined coefficients.  Note that, though the solutions should be
      linearly independent, this function does not explicitly check that.  You
      can do ``assert simplify(wronskian(sollist)) != 0`` to check for linear
      independence.  Also, ``assert len(sollist) == order`` will need to pass.
    - ``returns = 'both'``, return a dictionary ``{'sol': <solution to ODE>,
      'list': <list of linearly independent solutions>}``.

    Examples
    ========

    >>> from sympy import Function, dsolve, pprint
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> eq = f(x).diff(x, 2)*x**2 - 4*f(x).diff(x)*x + 6*f(x)
    >>> pprint(dsolve(eq, f(x),
    ... hint='nth_linear_euler_eq_homogeneous'))
            2
    f(x) = x *(C1 + C2*x)

    References
    ==========

    - https://en.wikipedia.org/wiki/Cauchy%E2%80%93Euler_equation
    - C. Bender & S. Orszag, "Advanced Mathematical Methods for Scientists and
      Engineers", Springer 1999, pp. 12

    # indirect doctest

    """
    global collectterms
    collectterms = []

    x = func.args[0]
    f = func.func
    r = match

    # First, set up characteristic equation.
    chareq, symbol = S.Zero, Dummy('x')

    for i in r.keys():
        if not isinstance(i, string_types) and i >= 0:
            chareq += (r[i]*diff(x**symbol, x, i)*x**-symbol).expand()

    chareq = Poly(chareq, symbol)
    chareqroots = [rootof(chareq, k) for k in range(chareq.degree())]

    # A generator of constants
    constants = list(get_numbered_constants(eq, num=chareq.degree()*2))
    constants.reverse()

    # Create a dict root: multiplicity or charroots
    charroots = defaultdict(int)
    for root in chareqroots:
        charroots[root] += 1
    gsol = S(0)
    # We need keep track of terms so we can run collect() at the end.
    # This is necessary for constantsimp to work properly.
    ln = log
    for root, multiplicity in charroots.items():
        for i in range(multiplicity):
            if isinstance(root, RootOf):
                gsol += (x**root) * constants.pop()
                if multiplicity != 1:
                    raise ValueError("Value should be 1")
                collectterms = [(0, root, 0)] + collectterms
            elif root.is_real:
                gsol += ln(x)**i*(x**root) * constants.pop()
                collectterms = [(i, root, 0)] + collectterms
            else:
                reroot = re(root)
                imroot = im(root)
                gsol += ln(x)**i * (x**reroot) * (
                    constants.pop() * sin(abs(imroot)*ln(x))
                    + constants.pop() * cos(imroot*ln(x)))
                # Preserve ordering (multiplicity, real part, imaginary part)
                # It will be assumed implicitly when constructing
                # fundamental solution sets.
                collectterms = [(i, reroot, imroot)] + collectterms
    if returns == 'sol':
        return Eq(f(x), gsol)
    elif returns in ('list' 'both'):
        # HOW TO TEST THIS CODE? (dsolve does not pass 'returns' through)
        # Create a list of (hopefully) linearly independent solutions
        gensols = []
        # Keep track of when to use sin or cos for nonzero imroot
        for i, reroot, imroot in collectterms:
            if imroot == 0:
                gensols.append(ln(x)**i*x**reroot)
            else:
                sin_form = ln(x)**i*x**reroot*sin(abs(imroot)*ln(x))
                if sin_form in gensols:
                    cos_form = ln(x)**i*x**reroot*cos(imroot*ln(x))
                    gensols.append(cos_form)
                else:
                    gensols.append(sin_form)
        if returns == 'list':
            return gensols
        else:
            return {'sol': Eq(f(x), gsol), 'list': gensols}
    else:
        raise ValueError('Unknown value for key "returns".')


def ode_nth_linear_euler_eq_nonhomogeneous_undetermined_coefficients(eq, func, order, match, returns='sol'):
    r"""
    Solves an `n`\th order linear non homogeneous Cauchy-Euler equidimensional
    ordinary differential equation using undetermined coefficients.

    This is an equation with form `g(x) = a_0 f(x) + a_1 x f'(x) + a_2 x^2 f''(x)
    \cdots`.

    These equations can be solved in a general manner, by substituting
    solutions of the form `x = exp(t)`, and deriving a characteristic equation
    of form `g(exp(t)) = b_0 f(t) + b_1 f'(t) + b_2 f''(t) \cdots` which can
    be then solved by nth_linear_constant_coeff_undetermined_coefficients if
    g(exp(t)) has finite number of linearly independent derivatives.

    Functions that fit this requirement are finite sums functions of the form
    `a x^i e^{b x} \sin(c x + d)` or `a x^i e^{b x} \cos(c x + d)`, where `i`
    is a non-negative integer and `a`, `b`, `c`, and `d` are constants.  For
    example any polynomial in `x`, functions like `x^2 e^{2 x}`, `x \sin(x)`,
    and `e^x \cos(x)` can all be used.  Products of `\sin`'s and `\cos`'s have
    a finite number of derivatives, because they can be expanded into `\sin(a
    x)` and `\cos(b x)` terms.  However, SymPy currently cannot do that
    expansion, so you will need to manually rewrite the expression in terms of
    the above to use this method.  So, for example, you will need to manually
    convert `\sin^2(x)` into `(1 + \cos(2 x))/2` to properly apply the method
    of undetermined coefficients on it.

    After replacement of x by exp(t), this method works by creating a trial function
    from the expression and all of its linear independent derivatives and
    substituting them into the original ODE.  The coefficients for each term
    will be a system of linear equations, which are be solved for and
    substituted, giving the solution. If any of the trial functions are linearly
    dependent on the solution to the homogeneous equation, they are multiplied
    by sufficient `x` to make them linearly independent.

    Examples
    ========

    >>> from sympy import dsolve, Function, Derivative, log
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> eq = x**2*Derivative(f(x), x, x) - 2*x*Derivative(f(x), x) + 2*f(x) - log(x)
    >>> dsolve(eq, f(x),
    ... hint='nth_linear_euler_eq_nonhomogeneous_undetermined_coefficients').expand()
    Eq(f(x), C1*x + C2*x**2 + log(x)/2 + 3/4)

    """
    x = func.args[0]
    f = func.func
    r = match

    chareq, eq, symbol = S.Zero, S.Zero, Dummy('x')

    for i in r.keys():
        if not isinstance(i, string_types) and i >= 0:
            chareq += (r[i]*diff(x**symbol, x, i)*x**-symbol).expand()

    for i in range(1,degree(Poly(chareq, symbol))+1):
        eq += chareq.coeff(symbol**i)*diff(f(x), x, i)

    if chareq.as_coeff_add(symbol)[0]:
        eq += chareq.as_coeff_add(symbol)[0]*f(x)
    e, re = posify(r[-1].subs(x, exp(x)))
    eq += e.subs(re)

    match = _nth_linear_match(eq, f(x), ode_order(eq, f(x)))
    match['trialset'] = r['trialset']
    return ode_nth_linear_constant_coeff_undetermined_coefficients(eq, func, order, match).subs(x, log(x)).subs(f(log(x)), f(x)).expand()


def ode_nth_linear_euler_eq_nonhomogeneous_variation_of_parameters(eq, func, order, match, returns='sol'):
    r"""
    Solves an `n`\th order linear non homogeneous Cauchy-Euler equidimensional
    ordinary differential equation using variation of parameters.

    This is an equation with form `g(x) = a_0 f(x) + a_1 x f'(x) + a_2 x^2 f''(x)
    \cdots`.

    This method works by assuming that the particular solution takes the form

    .. math:: \sum_{x=1}^{n} c_i(x) y_i(x) {a_n} {x^n} \text{,}

    where `y_i` is the `i`\th solution to the homogeneous equation.  The
    solution is then solved using Wronskian's and Cramer's Rule.  The
    particular solution is given by multiplying eq given below with `a_n x^{n}`

    .. math:: \sum_{x=1}^n \left( \int \frac{W_i(x)}{W(x)} \,dx
                \right) y_i(x) \text{,}

    where `W(x)` is the Wronskian of the fundamental system (the system of `n`
    linearly independent solutions to the homogeneous equation), and `W_i(x)`
    is the Wronskian of the fundamental system with the `i`\th column replaced
    with `[0, 0, \cdots, 0, \frac{x^{- n}}{a_n} g{\left(x \right)}]`.

    This method is general enough to solve any `n`\th order inhomogeneous
    linear differential equation, but sometimes SymPy cannot simplify the
    Wronskian well enough to integrate it.  If this method hangs, try using the
    ``nth_linear_constant_coeff_variation_of_parameters_Integral`` hint and
    simplifying the integrals manually.  Also, prefer using
    ``nth_linear_constant_coeff_undetermined_coefficients`` when it
    applies, because it doesn't use integration, making it faster and more
    reliable.

    Warning, using simplify=False with
    'nth_linear_constant_coeff_variation_of_parameters' in
    :py:meth:`~sympy.solvers.ode.dsolve` may cause it to hang, because it will
    not attempt to simplify the Wronskian before integrating.  It is
    recommended that you only use simplify=False with
    'nth_linear_constant_coeff_variation_of_parameters_Integral' for this
    method, especially if the solution to the homogeneous equation has
    trigonometric functions in it.

    Examples
    ========

    >>> from sympy import Function, dsolve, Derivative
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> eq = x**2*Derivative(f(x), x, x) - 2*x*Derivative(f(x), x) + 2*f(x) - x**4
    >>> dsolve(eq, f(x),
    ... hint='nth_linear_euler_eq_nonhomogeneous_variation_of_parameters').expand()
    Eq(f(x), C1*x + C2*x**2 + x**4/6)

    """
    x = func.args[0]
    f = func.func
    r = match

    gensol = ode_nth_linear_euler_eq_homogeneous(eq, func, order, match, returns='both')
    match.update(gensol)
    r[-1] = r[-1]/r[ode_order(eq, f(x))]
    sol = _solve_variation_of_parameters(eq, func, order, match)
    return Eq(f(x), r['sol'].rhs + (sol.rhs - r['sol'].rhs)*r[ode_order(eq, f(x))])


def ode_almost_linear(eq, func, order, match):
    r"""
    Solves an almost-linear differential equation.

    The general form of an almost linear differential equation is

    .. math:: f(x) g(y) y + k(x) l(y) + m(x) = 0
                \text{where} l'(y) = g(y)\text{.}

    This can be solved by substituting `l(y) = u(y)`.  Making the given
    substitution reduces it to a linear differential equation of the form `u'
    + P(x) u + Q(x) = 0`.

    The general solution is

        >>> from sympy import Function, dsolve, Eq, pprint
        >>> from sympy.abc import x, y, n
        >>> f, g, k, l = map(Function, ['f', 'g', 'k', 'l'])
        >>> genform = Eq(f(x)*(l(y).diff(y)) + k(x)*l(y) + g(x))
        >>> pprint(genform)
             d
        f(x)*--(l(y)) + g(x) + k(x)*l(y) = 0
             dy
        >>> pprint(dsolve(genform, hint = 'almost_linear'))
               /     //       y*k(x)                \\
               |     ||       ------                ||
               |     ||        f(x)                 ||  -y*k(x)
               |     ||-g(x)*e                      ||  --------
               |     ||--------------  for k(x) != 0||    f(x)
        l(y) = |C1 + |<     k(x)                    ||*e
               |     ||                             ||
               |     ||   -y*g(x)                   ||
               |     ||   --------       otherwise  ||
               |     ||     f(x)                    ||
               \     \\                             //


    See Also
    ========
    :meth:`sympy.solvers.ode.ode_1st_linear`

    Examples
    ========

    >>> from sympy import Function, Derivative, pprint
    >>> from sympy.solvers.ode import dsolve, classify_ode
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> d = f(x).diff(x)
    >>> eq = x*d + x*f(x) + 1
    >>> dsolve(eq, f(x), hint='almost_linear')
    Eq(f(x), (C1 - Ei(x))*exp(-x))
    >>> pprint(dsolve(eq, f(x), hint='almost_linear'))
                         -x
    f(x) = (C1 - Ei(x))*e

    References
    ==========

    - Joel Moses, "Symbolic Integration - The Stormy Decade", Communications
      of the ACM, Volume 14, Number 8, August 1971, pp. 558
    """

    # Since ode_1st_linear has already been implemented, and the
    # coefficients have been modified to the required form in
    # classify_ode, just passing eq, func, order and match to
    # ode_1st_linear will give the required output.
    return ode_1st_linear(eq, func, order, match)

def _linear_coeff_match(expr, func):
    r"""
    Helper function to match hint ``linear_coefficients``.

    Matches the expression to the form `(a_1 x + b_1 f(x) + c_1)/(a_2 x + b_2
    f(x) + c_2)` where the following conditions hold:

    1. `a_1`, `b_1`, `c_1`, `a_2`, `b_2`, `c_2` are Rationals;
    2. `c_1` or `c_2` are not equal to zero;
    3. `a_2 b_1 - a_1 b_2` is not equal to zero.

    Return ``xarg``, ``yarg`` where

    1. ``xarg`` = `(b_2 c_1 - b_1 c_2)/(a_2 b_1 - a_1 b_2)`
    2. ``yarg`` = `(a_1 c_2 - a_2 c_1)/(a_2 b_1 - a_1 b_2)`


    Examples
    ========

    >>> from sympy import Function
    >>> from sympy.abc import x
    >>> from sympy.solvers.ode import _linear_coeff_match
    >>> from sympy.functions.elementary.trigonometric import sin
    >>> f = Function('f')
    >>> _linear_coeff_match((
    ... (-25*f(x) - 8*x + 62)/(4*f(x) + 11*x - 11)), f(x))
    (1/9, 22/9)
    >>> _linear_coeff_match(
    ... sin((-5*f(x) - 8*x + 6)/(4*f(x) + x - 1)), f(x))
    (19/27, 2/27)
    >>> _linear_coeff_match(sin(f(x)/x), f(x))

    """
    f = func.func
    x = func.args[0]
    def abc(eq):
        r'''
        Internal function of _linear_coeff_match
        that returns Rationals a, b, c
        if eq is a*x + b*f(x) + c, else None.
        '''
        eq = _mexpand(eq)
        c = eq.as_independent(x, f(x), as_Add=True)[0]
        if not c.is_Rational:
            return
        a = eq.coeff(x)
        if not a.is_Rational:
            return
        b = eq.coeff(f(x))
        if not b.is_Rational:
            return
        if eq == a*x + b*f(x) + c:
            return a, b, c

    def match(arg):
        r'''
        Internal function of _linear_coeff_match that returns Rationals a1,
        b1, c1, a2, b2, c2 and a2*b1 - a1*b2 of the expression (a1*x + b1*f(x)
        + c1)/(a2*x + b2*f(x) + c2) if one of c1 or c2 and a2*b1 - a1*b2 is
        non-zero, else None.
        '''
        n, d = arg.together().as_numer_denom()
        m = abc(n)
        if m is not None:
            a1, b1, c1 = m
            m = abc(d)
            if m is not None:
                a2, b2, c2 = m
                d = a2*b1 - a1*b2
                if (c1 or c2) and d:
                    return a1, b1, c1, a2, b2, c2, d

    m = [fi.args[0] for fi in expr.atoms(Function) if fi.func != f and
         len(fi.args) == 1 and not fi.args[0].is_Function] or {expr}
    m1 = match(m.pop())
    if m1 and all(match(mi) == m1 for mi in m):
        a1, b1, c1, a2, b2, c2, denom = m1
        return (b2*c1 - b1*c2)/denom, (a1*c2 - a2*c1)/denom

def ode_linear_coefficients(eq, func, order, match):
    r"""
    Solves a differential equation with linear coefficients.

    The general form of a differential equation with linear coefficients is

    .. math:: y' + F\left(\!\frac{a_1 x + b_1 y + c_1}{a_2 x + b_2 y +
                c_2}\!\right) = 0\text{,}

    where `a_1`, `b_1`, `c_1`, `a_2`, `b_2`, `c_2` are constants and `a_1 b_2
    - a_2 b_1 \ne 0`.

    This can be solved by substituting:

    .. math:: x = x' + \frac{b_2 c_1 - b_1 c_2}{a_2 b_1 - a_1 b_2}

              y = y' + \frac{a_1 c_2 - a_2 c_1}{a_2 b_1 - a_1
                  b_2}\text{.}

    This substitution reduces the equation to a homogeneous differential
    equation.

    See Also
    ========
    :meth:`sympy.solvers.ode.ode_1st_homogeneous_coeff_best`
    :meth:`sympy.solvers.ode.ode_1st_homogeneous_coeff_subs_indep_div_dep`
    :meth:`sympy.solvers.ode.ode_1st_homogeneous_coeff_subs_dep_div_indep`

    Examples
    ========

    >>> from sympy import Function, Derivative, pprint
    >>> from sympy.solvers.ode import dsolve, classify_ode
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> df = f(x).diff(x)
    >>> eq = (x + f(x) + 1)*df + (f(x) - 6*x + 1)
    >>> dsolve(eq, hint='linear_coefficients')
    [Eq(f(x), -x - sqrt(C1 + 7*x**2) - 1), Eq(f(x), -x + sqrt(C1 + 7*x**2) - 1)]
    >>> pprint(dsolve(eq, hint='linear_coefficients'))
                      ___________                     ___________
                   /         2                     /         2
    [f(x) = -x - \/  C1 + 7*x   - 1, f(x) = -x + \/  C1 + 7*x   - 1]


    References
    ==========

    - Joel Moses, "Symbolic Integration - The Stormy Decade", Communications
      of the ACM, Volume 14, Number 8, August 1971, pp. 558
    """

    return ode_1st_homogeneous_coeff_best(eq, func, order, match)


def ode_separable_reduced(eq, func, order, match):
    r"""
    Solves a differential equation that can be reduced to the separable form.

    The general form of this equation is

    .. math:: y' + (y/x) H(x^n y) = 0\text{}.

    This can be solved by substituting `u(y) = x^n y`.  The equation then
    reduces to the separable form `\frac{u'}{u (\mathrm{power} - H(u))} -
    \frac{1}{x} = 0`.

    The general solution is:

        >>> from sympy import Function, dsolve, Eq, pprint
        >>> from sympy.abc import x, n
        >>> f, g = map(Function, ['f', 'g'])
        >>> genform = f(x).diff(x) + (f(x)/x)*g(x**n*f(x))
        >>> pprint(genform)
                         / n     \
        d          f(x)*g\x *f(x)/
        --(f(x)) + ---------------
        dx                x
        >>> pprint(dsolve(genform, hint='separable_reduced'))
         n
        x *f(x)
          /
         |
         |         1
         |    ------------ dy = C1 + log(x)
         |    y*(n - g(y))
         |
         /

    See Also
    ========
    :meth:`sympy.solvers.ode.ode_separable`

    Examples
    ========

    >>> from sympy import Function, Derivative, pprint
    >>> from sympy.solvers.ode import dsolve, classify_ode
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> d = f(x).diff(x)
    >>> eq = (x - x**2*f(x))*d - f(x)
    >>> dsolve(eq, hint='separable_reduced')
    [Eq(f(x), (1 - sqrt(C1*x**2 + 1))/x), Eq(f(x), (sqrt(C1*x**2 + 1) + 1)/x)]
    >>> pprint(dsolve(eq, hint='separable_reduced'))
                   ___________            ___________
                  /     2                /     2
            1 - \/  C1*x  + 1          \/  C1*x  + 1  + 1
    [f(x) = ------------------, f(x) = ------------------]
                    x                          x

    References
    ==========

    - Joel Moses, "Symbolic Integration - The Stormy Decade", Communications
      of the ACM, Volume 14, Number 8, August 1971, pp. 558
    """

    # Arguments are passed in a way so that they are coherent with the
    # ode_separable function
    x = func.args[0]
    f = func.func
    y = Dummy('y')
    u = match['u'].subs(match['t'], y)
    ycoeff = 1/(y*(match['power'] - u))
    m1 = {y: 1, x: -1/x, 'coeff': 1}
    m2 = {y: ycoeff, x: 1, 'coeff': 1}
    r = {'m1': m1, 'm2': m2, 'y': y, 'hint': x**match['power']*f(x)}
    return ode_separable(eq, func, order, r)


def ode_1st_power_series(eq, func, order, match):
    r"""
    The power series solution is a method which gives the Taylor series expansion
    to the solution of a differential equation.

    For a first order differential equation `\frac{dy}{dx} = h(x, y)`, a power
    series solution exists at a point `x = x_{0}` if `h(x, y)` is analytic at `x_{0}`.
    The solution is given by

    .. math:: y(x) = y(x_{0}) + \sum_{n = 1}^{\infty} \frac{F_{n}(x_{0},b)(x - x_{0})^n}{n!},

    where `y(x_{0}) = b` is the value of y at the initial value of `x_{0}`.
    To compute the values of the `F_{n}(x_{0},b)` the following algorithm is
    followed, until the required number of terms are generated.

    1. `F_1 = h(x_{0}, b)`
    2. `F_{n+1} = \frac{\partial F_{n}}{\partial x} + \frac{\partial F_{n}}{\partial y}F_{1}`

    Examples
    ========

    >>> from sympy import Function, Derivative, pprint, exp
    >>> from sympy.solvers.ode import dsolve
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> eq = exp(x)*(f(x).diff(x)) - f(x)
    >>> pprint(dsolve(eq, hint='1st_power_series'))
                           3       4       5
                       C1*x    C1*x    C1*x     / 6\
    f(x) = C1 + C1*x - ----- + ----- + ----- + O\x /
                         6       24      60


    References
    ==========

    - Travis W. Walker, Analytic power series technique for solving first-order
      differential equations, p.p 17, 18

    """
    x = func.args[0]
    y = match['y']
    f = func.func
    h = -match[match['d']]/match[match['e']]
    point = match.get('f0')
    value = match.get('f0val')
    terms = match.get('terms')

    # First term
    F = h
    if not h:
        return Eq(f(x), value)

    # Initialization
    series = value
    if terms > 1:
        hc = h.subs({x: point, y: value})
        if hc.has(oo) or hc.has(NaN) or hc.has(zoo):
            # Derivative does not exist, not analytic
            return Eq(f(x), oo)
        elif hc:
            series += hc*(x - point)

    for factcount in range(2, terms):
        Fnew = F.diff(x) + F.diff(y)*h
        Fnewc = Fnew.subs({x: point, y: value})
        # Same logic as above
        if Fnewc.has(oo) or Fnewc.has(NaN) or Fnewc.has(-oo) or Fnewc.has(zoo):
            return Eq(f(x), oo)
        series += Fnewc*((x - point)**factcount)/factorial(factcount)
        F = Fnew
    series += Order(x**terms)
    return Eq(f(x), series)


def ode_nth_linear_constant_coeff_homogeneous(eq, func, order, match,
        returns='sol'):
    r"""
    Solves an `n`\th order linear homogeneous differential equation with
    constant coefficients.

    This is an equation of the form

    .. math:: a_n f^{(n)}(x) + a_{n-1} f^{(n-1)}(x) + \cdots + a_1 f'(x)
                + a_0 f(x) = 0\text{.}

    These equations can be solved in a general manner, by taking the roots of
    the characteristic equation `a_n m^n + a_{n-1} m^{n-1} + \cdots + a_1 m +
    a_0 = 0`.  The solution will then be the sum of `C_n x^i e^{r x}` terms,
    for each where `C_n` is an arbitrary constant, `r` is a root of the
    characteristic equation and `i` is one of each from 0 to the multiplicity
    of the root - 1 (for example, a root 3 of multiplicity 2 would create the
    terms `C_1 e^{3 x} + C_2 x e^{3 x}`).  The exponential is usually expanded
    for complex roots using Euler's equation `e^{I x} = \cos(x) + I \sin(x)`.
    Complex roots always come in conjugate pairs in polynomials with real
    coefficients, so the two roots will be represented (after simplifying the
    constants) as `e^{a x} \left(C_1 \cos(b x) + C_2 \sin(b x)\right)`.

    If SymPy cannot find exact roots to the characteristic equation, a
    :py:class:`~sympy.polys.rootoftools.CRootOf` instance will be return
    instead.

    >>> from sympy import Function, dsolve, Eq
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> dsolve(f(x).diff(x, 5) + 10*f(x).diff(x) - 2*f(x), f(x),
    ... hint='nth_linear_constant_coeff_homogeneous')
    ... # doctest: +NORMALIZE_WHITESPACE
    Eq(f(x), C5*exp(x*CRootOf(_x**5 + 10*_x - 2, 0))
    + (C1*sin(x*im(CRootOf(_x**5 + 10*_x - 2, 1)))
    + C2*cos(x*im(CRootOf(_x**5 + 10*_x - 2, 1))))*exp(x*re(CRootOf(_x**5 + 10*_x - 2, 1)))
    + (C3*sin(x*im(CRootOf(_x**5 + 10*_x - 2, 3)))
    + C4*cos(x*im(CRootOf(_x**5 + 10*_x - 2, 3))))*exp(x*re(CRootOf(_x**5 + 10*_x - 2, 3))))

    Note that because this method does not involve integration, there is no
    ``nth_linear_constant_coeff_homogeneous_Integral`` hint.

    The following is for internal use:

    - ``returns = 'sol'`` returns the solution to the ODE.
    - ``returns = 'list'`` returns a list of linearly independent solutions,
      for use with non homogeneous solution methods like variation of
      parameters and undetermined coefficients.  Note that, though the
      solutions should be linearly independent, this function does not
      explicitly check that.  You can do ``assert simplify(wronskian(sollist))
      != 0`` to check for linear independence.  Also, ``assert len(sollist) ==
      order`` will need to pass.
    - ``returns = 'both'``, return a dictionary ``{'sol': <solution to ODE>,
      'list': <list of linearly independent solutions>}``.

    Examples
    ========

    >>> from sympy import Function, dsolve, pprint
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> pprint(dsolve(f(x).diff(x, 4) + 2*f(x).diff(x, 3) -
    ... 2*f(x).diff(x, 2) - 6*f(x).diff(x) + 5*f(x), f(x),
    ... hint='nth_linear_constant_coeff_homogeneous'))
                        x                            -2*x
    f(x) = (C1 + C2*x)*e  + (C3*sin(x) + C4*cos(x))*e

    References
    ==========

    - https://en.wikipedia.org/wiki/Linear_differential_equation section:
      Nonhomogeneous_equation_with_constant_coefficients
    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 211

    # indirect doctest

    """
    x = func.args[0]
    f = func.func
    r = match

    # First, set up characteristic equation.
    chareq, symbol = S.Zero, Dummy('x')

    for i in r.keys():
        if type(i) == str or i < 0:
            pass
        else:
            chareq += r[i]*symbol**i

    chareq = Poly(chareq, symbol)
    # Can't just call roots because it doesn't return rootof for unsolveable
    # polynomials.
    chareqroots = roots(chareq, multiple=True)
    if len(chareqroots) != order:
        chareqroots = [rootof(chareq, k) for k in range(chareq.degree())]

    chareq_is_complex = not all([i.is_real for i in chareq.all_coeffs()])

    # A generator of constants
    constants = list(get_numbered_constants(eq, num=chareq.degree()*2))

    # Create a dict root: multiplicity or charroots
    charroots = defaultdict(int)
    for root in chareqroots:
        charroots[root] += 1
    gsol = S(0)
    # We need to keep track of terms so we can run collect() at the end.
    # This is necessary for constantsimp to work properly.
    global collectterms
    collectterms = []
    gensols = []
    conjugate_roots = [] # used to prevent double-use of conjugate roots
    # Loop over roots in theorder provided by roots/rootof...
    for root in chareqroots:
        # but don't repoeat multiple roots.
        if root not in charroots:
            continue
        multiplicity = charroots.pop(root)
        for i in range(multiplicity):
            if chareq_is_complex:
                gensols.append(x**i*exp(root*x))
                collectterms = [(i, root, 0)] + collectterms
                continue
            reroot = re(root)
            imroot = im(root)
            if imroot.has(atan2) and reroot.has(atan2):
                # Remove this condition when re and im stop returning
                # circular atan2 usages.
                gensols.append(x**i*exp(root*x))
                collectterms = [(i, root, 0)] + collectterms
            else:
                if root in conjugate_roots:
                    collectterms = [(i, reroot, imroot)] + collectterms
                    continue
                if imroot == 0:
                    gensols.append(x**i*exp(reroot*x))
                    collectterms = [(i, reroot, 0)] + collectterms
                    continue
                conjugate_roots.append(conjugate(root))
                gensols.append(x**i*exp(reroot*x) * sin(abs(imroot) * x))
                gensols.append(x**i*exp(reroot*x) * cos(    imroot  * x))

                # This ordering is important
                collectterms = [(i, reroot, imroot)] + collectterms
    if returns == 'list':
        return gensols
    elif returns in ('sol' 'both'):
        gsol = Add(*[i*j for (i,j) in zip(constants, gensols)])
        if returns == 'sol':
            return Eq(f(x), gsol)
        else:
            return {'sol': Eq(f(x), gsol), 'list': gensols}
    else:
        raise ValueError('Unknown value for key "returns".')


def ode_nth_linear_constant_coeff_undetermined_coefficients(eq, func, order, match):
    r"""
    Solves an `n`\th order linear differential equation with constant
    coefficients using the method of undetermined coefficients.

    This method works on differential equations of the form

    .. math:: a_n f^{(n)}(x) + a_{n-1} f^{(n-1)}(x) + \cdots + a_1 f'(x)
                + a_0 f(x) = P(x)\text{,}

    where `P(x)` is a function that has a finite number of linearly
    independent derivatives.

    Functions that fit this requirement are finite sums functions of the form
    `a x^i e^{b x} \sin(c x + d)` or `a x^i e^{b x} \cos(c x + d)`, where `i`
    is a non-negative integer and `a`, `b`, `c`, and `d` are constants.  For
    example any polynomial in `x`, functions like `x^2 e^{2 x}`, `x \sin(x)`,
    and `e^x \cos(x)` can all be used.  Products of `\sin`'s and `\cos`'s have
    a finite number of derivatives, because they can be expanded into `\sin(a
    x)` and `\cos(b x)` terms.  However, SymPy currently cannot do that
    expansion, so you will need to manually rewrite the expression in terms of
    the above to use this method.  So, for example, you will need to manually
    convert `\sin^2(x)` into `(1 + \cos(2 x))/2` to properly apply the method
    of undetermined coefficients on it.

    This method works by creating a trial function from the expression and all
    of its linear independent derivatives and substituting them into the
    original ODE.  The coefficients for each term will be a system of linear
    equations, which are be solved for and substituted, giving the solution.
    If any of the trial functions are linearly dependent on the solution to
    the homogeneous equation, they are multiplied by sufficient `x` to make
    them linearly independent.

    Examples
    ========

    >>> from sympy import Function, dsolve, pprint, exp, cos
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> pprint(dsolve(f(x).diff(x, 2) + 2*f(x).diff(x) + f(x) -
    ... 4*exp(-x)*x**2 + cos(2*x), f(x),
    ... hint='nth_linear_constant_coeff_undetermined_coefficients'))
           /             4\
           |            x |  -x   4*sin(2*x)   3*cos(2*x)
    f(x) = |C1 + C2*x + --|*e   - ---------- + ----------
           \            3 /           25           25

    References
    ==========

    - https://en.wikipedia.org/wiki/Method_of_undetermined_coefficients
    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 221

    # indirect doctest

    """
    gensol = ode_nth_linear_constant_coeff_homogeneous(eq, func, order, match,
        returns='both')
    match.update(gensol)
    return _solve_undetermined_coefficients(eq, func, order, match)


def _solve_undetermined_coefficients(eq, func, order, match):
    r"""
    Helper function for the method of undetermined coefficients.

    See the
    :py:meth:`~sympy.solvers.ode.ode_nth_linear_constant_coeff_undetermined_coefficients`
    docstring for more information on this method.

    The parameter ``match`` should be a dictionary that has the following
    keys:

    ``list``
      A list of solutions to the homogeneous equation, such as the list
      returned by
      ``ode_nth_linear_constant_coeff_homogeneous(returns='list')``.

    ``sol``
      The general solution, such as the solution returned by
      ``ode_nth_linear_constant_coeff_homogeneous(returns='sol')``.

    ``trialset``
      The set of trial functions as returned by
      ``_undetermined_coefficients_match()['trialset']``.

    """
    x = func.args[0]
    f = func.func
    r = match
    coeffs = numbered_symbols('a', cls=Dummy)
    coefflist = []
    gensols = r['list']
    gsol = r['sol']
    trialset = r['trialset']
    notneedset = set([])
    newtrialset = set([])
    global collectterms
    if len(gensols) != order:
        raise NotImplementedError("Cannot find " + str(order) +
        " solutions to the homogeneous equation necessary to apply" +
        " undetermined coefficients to " + str(eq) +
        " (number of terms != order)")
    usedsin = set([])
    mult = 0  # The multiplicity of the root
    getmult = True
    for i, reroot, imroot in collectterms:
        if getmult:
            mult = i + 1
            getmult = False
        if i == 0:
            getmult = True
        if imroot:
            # Alternate between sin and cos
            if (i, reroot) in usedsin:
                check = x**i*exp(reroot*x)*cos(imroot*x)
            else:
                check = x**i*exp(reroot*x)*sin(abs(imroot)*x)
                usedsin.add((i, reroot))
        else:
            check = x**i*exp(reroot*x)

        if check in trialset:
            # If an element of the trial function is already part of the
            # homogeneous solution, we need to multiply by sufficient x to
            # make it linearly independent.  We also don't need to bother
            # checking for the coefficients on those elements, since we
            # already know it will be 0.
            while True:
                if check*x**mult in trialset:
                    mult += 1
                else:
                    break
            trialset.add(check*x**mult)
            notneedset.add(check)

    newtrialset = trialset - notneedset

    trialfunc = 0
    for i in newtrialset:
        c = next(coeffs)
        coefflist.append(c)
        trialfunc += c*i

    eqs = sub_func_doit(eq, f(x), trialfunc)

    coeffsdict = dict(list(zip(trialset, [0]*(len(trialset) + 1))))

    eqs = _mexpand(eqs)

    for i in Add.make_args(eqs):
        s = separatevars(i, dict=True, symbols=[x])
        coeffsdict[s[x]] += s['coeff']

    coeffvals = solve(list(coeffsdict.values()), coefflist)

    if not coeffvals:
        raise NotImplementedError(
            "Could not solve `%s` using the "
            "method of undetermined coefficients "
            "(unable to solve for coefficients)." % eq)

    psol = trialfunc.subs(coeffvals)

    return Eq(f(x), gsol.rhs + psol)


def _undetermined_coefficients_match(expr, x):
    r"""
    Returns a trial function match if undetermined coefficients can be applied
    to ``expr``, and ``None`` otherwise.

    A trial expression can be found for an expression for use with the method
    of undetermined coefficients if the expression is an
    additive/multiplicative combination of constants, polynomials in `x` (the
    independent variable of expr), `\sin(a x + b)`, `\cos(a x + b)`, and
    `e^{a x}` terms (in other words, it has a finite number of linearly
    independent derivatives).

    Note that you may still need to multiply each term returned here by
    sufficient `x` to make it linearly independent with the solutions to the
    homogeneous equation.

    This is intended for internal use by ``undetermined_coefficients`` hints.

    SymPy currently has no way to convert `\sin^n(x) \cos^m(y)` into a sum of
    only `\sin(a x)` and `\cos(b x)` terms, so these are not implemented.  So,
    for example, you will need to manually convert `\sin^2(x)` into `[1 +
    \cos(2 x)]/2` to properly apply the method of undetermined coefficients on
    it.

    Examples
    ========

    >>> from sympy import log, exp
    >>> from sympy.solvers.ode import _undetermined_coefficients_match
    >>> from sympy.abc import x
    >>> _undetermined_coefficients_match(9*x*exp(x) + exp(-x), x)
    {'test': True, 'trialset': {x*exp(x), exp(-x), exp(x)}}
    >>> _undetermined_coefficients_match(log(x), x)
    {'test': False}

    """
    a = Wild('a', exclude=[x])
    b = Wild('b', exclude=[x])
    expr = powsimp(expr, combine='exp')  # exp(x)*exp(2*x + 1) => exp(3*x + 1)
    retdict = {}

    def _test_term(expr, x):
        r"""
        Test if ``expr`` fits the proper form for undetermined coefficients.
        """
        if not expr.has(x):
            return True
        elif expr.is_Add:
            return all(_test_term(i, x) for i in expr.args)
        elif expr.is_Mul:
            if expr.has(sin, cos):
                foundtrig = False
                # Make sure that there is only one trig function in the args.
                # See the docstring.
                for i in expr.args:
                    if i.has(sin, cos):
                        if foundtrig:
                            return False
                        else:
                            foundtrig = True
            return all(_test_term(i, x) for i in expr.args)
        elif expr.is_Function:
            if expr.func in (sin, cos, exp):
                if expr.args[0].match(a*x + b):
                    return True
                else:
                    return False
            else:
                return False
        elif expr.is_Pow and expr.base.is_Symbol and expr.exp.is_Integer and \
                expr.exp >= 0:
            return True
        elif expr.is_Pow and expr.base.is_number:
            if expr.exp.match(a*x + b):
                return True
            else:
                return False
        elif expr.is_Symbol or expr.is_number:
            return True
        else:
            return False

    def _get_trial_set(expr, x, exprs=set([])):
        r"""
        Returns a set of trial terms for undetermined coefficients.

        The idea behind undetermined coefficients is that the terms expression
        repeat themselves after a finite number of derivatives, except for the
        coefficients (they are linearly dependent).  So if we collect these,
        we should have the terms of our trial function.
        """
        def _remove_coefficient(expr, x):
            r"""
            Returns the expression without a coefficient.

            Similar to expr.as_independent(x)[1], except it only works
            multiplicatively.
            """
            term = S.One
            if expr.is_Mul:
                for i in expr.args:
                    if i.has(x):
                        term *= i
            elif expr.has(x):
                term = expr
            return term

        expr = expand_mul(expr)
        if expr.is_Add:
            for term in expr.args:
                if _remove_coefficient(term, x) in exprs:
                    pass
                else:
                    exprs.add(_remove_coefficient(term, x))
                    exprs = exprs.union(_get_trial_set(term, x, exprs))
        else:
            term = _remove_coefficient(expr, x)
            tmpset = exprs.union({term})
            oldset = set([])
            while tmpset != oldset:
                # If you get stuck in this loop, then _test_term is probably
                # broken
                oldset = tmpset.copy()
                expr = expr.diff(x)
                term = _remove_coefficient(expr, x)
                if term.is_Add:
                    tmpset = tmpset.union(_get_trial_set(term, x, tmpset))
                else:
                    tmpset.add(term)
            exprs = tmpset
        return exprs

    retdict['test'] = _test_term(expr, x)
    if retdict['test']:
        # Try to generate a list of trial solutions that will have the
        # undetermined coefficients. Note that if any of these are not linearly
        # independent with any of the solutions to the homogeneous equation,
        # then they will need to be multiplied by sufficient x to make them so.
        # This function DOES NOT do that (it doesn't even look at the
        # homogeneous equation).
        retdict['trialset'] = _get_trial_set(expr, x)

    return retdict


def ode_nth_linear_constant_coeff_variation_of_parameters(eq, func, order, match):
    r"""
    Solves an `n`\th order linear differential equation with constant
    coefficients using the method of variation of parameters.

    This method works on any differential equations of the form

    .. math:: f^{(n)}(x) + a_{n-1} f^{(n-1)}(x) + \cdots + a_1 f'(x) + a_0
                f(x) = P(x)\text{.}

    This method works by assuming that the particular solution takes the form

    .. math:: \sum_{x=1}^{n} c_i(x) y_i(x)\text{,}

    where `y_i` is the `i`\th solution to the homogeneous equation.  The
    solution is then solved using Wronskian's and Cramer's Rule.  The
    particular solution is given by

    .. math:: \sum_{x=1}^n \left( \int \frac{W_i(x)}{W(x)} \,dx
                \right) y_i(x) \text{,}

    where `W(x)` is the Wronskian of the fundamental system (the system of `n`
    linearly independent solutions to the homogeneous equation), and `W_i(x)`
    is the Wronskian of the fundamental system with the `i`\th column replaced
    with `[0, 0, \cdots, 0, P(x)]`.

    This method is general enough to solve any `n`\th order inhomogeneous
    linear differential equation with constant coefficients, but sometimes
    SymPy cannot simplify the Wronskian well enough to integrate it.  If this
    method hangs, try using the
    ``nth_linear_constant_coeff_variation_of_parameters_Integral`` hint and
    simplifying the integrals manually.  Also, prefer using
    ``nth_linear_constant_coeff_undetermined_coefficients`` when it
    applies, because it doesn't use integration, making it faster and more
    reliable.

    Warning, using simplify=False with
    'nth_linear_constant_coeff_variation_of_parameters' in
    :py:meth:`~sympy.solvers.ode.dsolve` may cause it to hang, because it will
    not attempt to simplify the Wronskian before integrating.  It is
    recommended that you only use simplify=False with
    'nth_linear_constant_coeff_variation_of_parameters_Integral' for this
    method, especially if the solution to the homogeneous equation has
    trigonometric functions in it.

    Examples
    ========

    >>> from sympy import Function, dsolve, pprint, exp, log
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> pprint(dsolve(f(x).diff(x, 3) - 3*f(x).diff(x, 2) +
    ... 3*f(x).diff(x) - f(x) - exp(x)*log(x), f(x),
    ... hint='nth_linear_constant_coeff_variation_of_parameters'))
           /                     3                \
           |                2   x *(6*log(x) - 11)|  x
    f(x) = |C1 + C2*x + C3*x  + ------------------|*e
           \                            36        /

    References
    ==========

    - https://en.wikipedia.org/wiki/Variation_of_parameters
    - http://planetmath.org/VariationOfParameters
    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 233

    # indirect doctest

    """

    gensol = ode_nth_linear_constant_coeff_homogeneous(eq, func, order, match,
        returns='both')
    match.update(gensol)
    return _solve_variation_of_parameters(eq, func, order, match)


def _solve_variation_of_parameters(eq, func, order, match):
    r"""
    Helper function for the method of variation of parameters and nonhomogeneous euler eq.

    See the
    :py:meth:`~sympy.solvers.ode.ode_nth_linear_constant_coeff_variation_of_parameters`
    docstring for more information on this method.

    The parameter ``match`` should be a dictionary that has the following
    keys:

    ``list``
      A list of solutions to the homogeneous equation, such as the list
      returned by
      ``ode_nth_linear_constant_coeff_homogeneous(returns='list')``.

    ``sol``
      The general solution, such as the solution returned by
      ``ode_nth_linear_constant_coeff_homogeneous(returns='sol')``.

    """

    x = func.args[0]
    f = func.func
    r = match
    psol = 0
    gensols = r['list']
    gsol = r['sol']
    wr = wronskian(gensols, x)

    if r.get('simplify', True):
        wr = simplify(wr)  # We need much better simplification for
                           # some ODEs. See issue 4662, for example.

        # To reduce commonly occurring sin(x)**2 + cos(x)**2 to 1
        wr = trigsimp(wr, deep=True, recursive=True)
    if not wr:
        # The wronskian will be 0 iff the solutions are not linearly
        # independent.
        raise NotImplementedError("Cannot find " + str(order) +
        " solutions to the homogeneous equation necessary to apply " +
        "variation of parameters to " + str(eq) + " (Wronskian == 0)")
    if len(gensols) != order:
        raise NotImplementedError("Cannot find " + str(order) +
        " solutions to the homogeneous equation necessary to apply " +
        "variation of parameters to " +
        str(eq) + " (number of terms != order)")
    negoneterm = (-1)**(order)
    for i in gensols:
        psol += negoneterm*Integral(wronskian([sol for sol in gensols if sol != i], x)*r[-1]/wr, x)*i/r[order]
        negoneterm *= -1

    if r.get('simplify', True):
        psol = simplify(psol)
        psol = trigsimp(psol, deep=True)
    return Eq(f(x), gsol.rhs + psol)


def ode_separable(eq, func, order, match):
    r"""
    Solves separable 1st order differential equations.

    This is any differential equation that can be written as `P(y)
    \tfrac{dy}{dx} = Q(x)`.  The solution can then just be found by
    rearranging terms and integrating: `\int P(y) \,dy = \int Q(x) \,dx`.
    This hint uses :py:meth:`sympy.simplify.simplify.separatevars` as its back
    end, so if a separable equation is not caught by this solver, it is most
    likely the fault of that function.
    :py:meth:`~sympy.simplify.simplify.separatevars` is
    smart enough to do most expansion and factoring necessary to convert a
    separable equation `F(x, y)` into the proper form `P(x)\cdot{}Q(y)`.  The
    general solution is::

        >>> from sympy import Function, dsolve, Eq, pprint
        >>> from sympy.abc import x
        >>> a, b, c, d, f = map(Function, ['a', 'b', 'c', 'd', 'f'])
        >>> genform = Eq(a(x)*b(f(x))*f(x).diff(x), c(x)*d(f(x)))
        >>> pprint(genform)
                     d
        a(x)*b(f(x))*--(f(x)) = c(x)*d(f(x))
                     dx
        >>> pprint(dsolve(genform, f(x), hint='separable_Integral'))
             f(x)
           /                  /
          |                  |
          |  b(y)            | c(x)
          |  ---- dy = C1 +  | ---- dx
          |  d(y)            | a(x)
          |                  |
         /                  /

    Examples
    ========

    >>> from sympy import Function, dsolve, Eq
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> pprint(dsolve(Eq(f(x)*f(x).diff(x) + x, 3*x*f(x)**2), f(x),
    ... hint='separable', simplify=False))
       /   2       \         2
    log\3*f (x) - 1/        x
    ---------------- = C1 + --
           6                2

    References
    ==========

    - M. Tenenbaum & H. Pollard, "Ordinary Differential Equations",
      Dover 1963, pp. 52

    # indirect doctest

    """
    x = func.args[0]
    f = func.func
    C1 = get_numbered_constants(eq, num=1)
    r = match  # {'m1':m1, 'm2':m2, 'y':y}
    u = r.get('hint', f(x))  # get u from separable_reduced else get f(x)
    return Eq(Integral(r['m2']['coeff']*r['m2'][r['y']]/r['m1'][r['y']],
        (r['y'], None, u)), Integral(-r['m1']['coeff']*r['m1'][x]/
        r['m2'][x], x) + C1)


def checkinfsol(eq, infinitesimals, func=None, order=None):
    r"""
    This function is used to check if the given infinitesimals are the
    actual infinitesimals of the given first order differential equation.
    This method is specific to the Lie Group Solver of ODEs.

    As of now, it simply checks, by substituting the infinitesimals in the
    partial differential equation.


    .. math:: \frac{\partial \eta}{\partial x} + \left(\frac{\partial \eta}{\partial y}
                - \frac{\partial \xi}{\partial x}\right)*h
                - \frac{\partial \xi}{\partial y}*h^{2}
                - \xi\frac{\partial h}{\partial x} - \eta\frac{\partial h}{\partial y} = 0


    where `\eta`, and `\xi` are the infinitesimals and `h(x,y) = \frac{dy}{dx}`

    The infinitesimals should be given in the form of a list of dicts
    ``[{xi(x, y): inf, eta(x, y): inf}]``, corresponding to the
    output of the function infinitesimals. It returns a list
    of values of the form ``[(True/False, sol)]`` where ``sol`` is the value
    obtained after substituting the infinitesimals in the PDE. If it
    is ``True``, then ``sol`` would be 0.

    """
    if isinstance(eq, Equality):
        eq = eq.lhs - eq.rhs
    if not func:
        eq, func = _preprocess(eq)
    variables = func.args
    if len(variables) != 1:
        raise ValueError("ODE's have only one independent variable")
    else:
        x = variables[0]
        if not order:
            order = ode_order(eq, func)
        if order != 1:
            raise NotImplementedError("Lie groups solver has been implemented "
            "only for first order differential equations")
        else:
            df = func.diff(x)
            a = Wild('a', exclude = [df])
            b = Wild('b', exclude = [df])
            match = collect(expand(eq), df).match(a*df + b)

            if match:
                h = -simplify(match[b]/match[a])
            else:
                try:
                    sol = solve(eq, df)
                except NotImplementedError:
                    raise NotImplementedError("Infinitesimals for the "
                        "first order ODE could not be found")
                else:
                    h = sol[0]  # Find infinitesimals for one solution

            y = Dummy('y')
            h = h.subs(func, y)
            xi = Function('xi')(x, y)
            eta = Function('eta')(x, y)
            dxi = Function('xi')(x, func)
            deta = Function('eta')(x, func)
            pde = (eta.diff(x) + (eta.diff(y) - xi.diff(x))*h -
                (xi.diff(y))*h**2 - xi*(h.diff(x)) - eta*(h.diff(y)))
            soltup = []
            for sol in infinitesimals:
                tsol = {xi: S(sol[dxi]).subs(func, y),
                    eta: S(sol[deta]).subs(func, y)}
                sol = simplify(pde.subs(tsol).doit())
                if sol:
                    soltup.append((False, sol.subs(y, func)))
                else:
                    soltup.append((True, 0))
            return soltup

def ode_lie_group(eq, func, order, match):
    r"""
    This hint implements the Lie group method of solving first order differential
    equations. The aim is to convert the given differential equation from the
    given coordinate given system into another coordinate system where it becomes
    invariant under the one-parameter Lie group of translations. The converted ODE is
    quadrature and can be solved easily. It makes use of the
    :py:meth:`sympy.solvers.ode.infinitesimals` function which returns the
    infinitesimals of the transformation.

    The coordinates `r` and `s` can be found by solving the following Partial
    Differential Equations.

    .. math :: \xi\frac{\partial r}{\partial x} + \eta\frac{\partial r}{\partial y}
                  = 0

    .. math :: \xi\frac{\partial s}{\partial x} + \eta\frac{\partial s}{\partial y}
                  = 1

    The differential equation becomes separable in the new coordinate system

    .. math :: \frac{ds}{dr} = \frac{\frac{\partial s}{\partial x} +
                 h(x, y)\frac{\partial s}{\partial y}}{
                 \frac{\partial r}{\partial x} + h(x, y)\frac{\partial r}{\partial y}}

    After finding the solution by integration, it is then converted back to the original
    coordinate system by substituting `r` and `s` in terms of `x` and `y` again.

    Examples
    ========

    >>> from sympy import Function, dsolve, Eq, exp, pprint
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> pprint(dsolve(f(x).diff(x) + 2*x*f(x) - x*exp(-x**2), f(x),
    ... hint='lie_group'))
           /      2\    2
           |     x |  -x
    f(x) = |C1 + --|*e
           \     2 /


    References
    ==========

    - Solving differential equations by Symmetry Groups,
      John Starrett, pp. 1 - pp. 14

    """

    heuristics = lie_heuristics
    inf = {}
    f = func.func
    x = func.args[0]
    df = func.diff(x)
    xi = Function("xi")
    eta = Function("eta")
    a = Wild('a', exclude = [df])
    b = Wild('b', exclude = [df])
    xis = match.pop('xi')
    etas = match.pop('eta')

    if match:
        h = -simplify(match[match['d']]/match[match['e']])
        y = match['y']
    else:
        try:
            sol = solve(eq, df)
            if sol == []:
                raise NotImplementedError
        except NotImplementedError:
            raise NotImplementedError("Unable to solve the differential equation " +
                str(eq) + " by the lie group method")
        else:
            y = Dummy("y")
            h = sol[0].subs(func, y)

    if xis is not None and etas is not None:
        inf = [{xi(x, f(x)): S(xis), eta(x, f(x)): S(etas)}]

        if not checkinfsol(eq, inf, func=f(x), order=1)[0][0]:
            raise ValueError("The given infinitesimals xi and eta"
                " are not the infinitesimals to the given equation")
        else:
            heuristics = ["user_defined"]

    match = {'h': h, 'y': y}

    # This is done so that if:
    # a] solve raises a NotImplementedError.
    # b] any heuristic raises a ValueError
    # another heuristic can be used.
    tempsol = []  # Used by solve below
    for heuristic in heuristics:
        try:
            if not inf:
                inf = infinitesimals(eq, hint=heuristic, func=func, order=1, match=match)
        except ValueError:
            continue
        else:
            for infsim in inf:
                xiinf = (infsim[xi(x, func)]).subs(func, y)
                etainf = (infsim[eta(x, func)]).subs(func, y)
                # This condition creates recursion while using pdsolve.
                # Since the first step while solving a PDE of form
                # a*(f(x, y).diff(x)) + b*(f(x, y).diff(y)) + c = 0
                # is to solve the ODE dy/dx = b/a
                if simplify(etainf/xiinf) == h:
                    continue
                rpde = f(x, y).diff(x)*xiinf + f(x, y).diff(y)*etainf
                r = pdsolve(rpde, func=f(x, y)).rhs
                s = pdsolve(rpde - 1, func=f(x, y)).rhs
                newcoord = [_lie_group_remove(coord) for coord in [r, s]]
                r = Dummy("r")
                s = Dummy("s")
                C1 = Symbol("C1")
                rcoord = newcoord[0]
                scoord = newcoord[-1]
                try:
                    sol = solve([r - rcoord, s - scoord], x, y, dict=True)
                except NotImplementedError:
                    continue
                else:
                    sol = sol[0]
                    xsub = sol[x]
                    ysub = sol[y]
                    num = simplify(scoord.diff(x) + scoord.diff(y)*h)
                    denom = simplify(rcoord.diff(x) + rcoord.diff(y)*h)
                    if num and denom:
                        diffeq = simplify((num/denom).subs([(x, xsub), (y, ysub)]))
                        sep = separatevars(diffeq, symbols=[r, s], dict=True)
                        if sep:
                            # Trying to separate, r and s coordinates
                            deq = integrate((1/sep[s]), s) + C1 - integrate(sep['coeff']*sep[r], r)
                            # Substituting and reverting back to original coordinates
                            deq = deq.subs([(r, rcoord), (s, scoord)])
                            try:
                                sdeq = solve(deq, y)
                            except NotImplementedError:
                                tempsol.append(deq)
                            else:
                                if len(sdeq) == 1:
                                    return Eq(f(x), sdeq.pop())
                                else:
                                    return [Eq(f(x), sol) for sol in sdeq]


                    elif denom: # (ds/dr) is zero which means s is constant
                        return Eq(f(x), solve(scoord - C1, y)[0])

                    elif num: # (dr/ds) is zero which means r is constant
                        return Eq(f(x), solve(rcoord - C1, y)[0])

    # If nothing works, return solution as it is, without solving for y
    if tempsol:
        if len(tempsol) == 1:
            return Eq(tempsol.pop().subs(y, f(x)), 0)
        else:
            return [Eq(sol.subs(y, f(x)), 0) for sol in tempsol]

    raise NotImplementedError("The given ODE " + str(eq) + " cannot be solved by"
        + " the lie group method")


def _lie_group_remove(coords):
    r"""
    This function is strictly meant for internal use by the Lie group ODE solving
    method. It replaces arbitrary functions returned by pdsolve with either 0 or 1 or the
    args of the arbitrary function.

    The algorithm used is:
    1] If coords is an instance of an Undefined Function, then the args are returned
    2] If the arbitrary function is present in an Add object, it is replaced by zero.
    3] If the arbitrary function is present in an Mul object, it is replaced by one.
    4] If coords has no Undefined Function, it is returned as it is.

    Examples
    ========

    >>> from sympy.solvers.ode import _lie_group_remove
    >>> from sympy import Function
    >>> from sympy.abc import x, y
    >>> F = Function("F")
    >>> eq = x**2*y
    >>> _lie_group_remove(eq)
    x**2*y
    >>> eq = F(x**2*y)
    >>> _lie_group_remove(eq)
    x**2*y
    >>> eq = y**2*x + F(x**3)
    >>> _lie_group_remove(eq)
    x*y**2
    >>> eq = (F(x**3) + y)*x**4
    >>> _lie_group_remove(eq)
    x**4*y

    """
    if isinstance(coords, AppliedUndef):
        return coords.args[0]
    elif coords.is_Add:
        subfunc = coords.atoms(AppliedUndef)
        if subfunc:
            for func in subfunc:
                coords = coords.subs(func, 0)
        return coords
    elif coords.is_Pow:
        base, expr = coords.as_base_exp()
        base = _lie_group_remove(base)
        expr = _lie_group_remove(expr)
        return base**expr
    elif coords.is_Mul:
        mulargs = []
        coordargs = coords.args
        for arg in coordargs:
            if not isinstance(coords, AppliedUndef):
                mulargs.append(_lie_group_remove(arg))
        return Mul(*mulargs)
    return coords

def infinitesimals(eq, func=None, order=None, hint='default', match=None):
    r"""
    The infinitesimal functions of an ordinary differential equation, `\xi(x,y)`
    and `\eta(x,y)`, are the infinitesimals of the Lie group of point transformations
    for which the differential equation is invariant. So, the ODE `y'=f(x,y)`
    would admit a Lie group `x^*=X(x,y;\varepsilon)=x+\varepsilon\xi(x,y)`,
    `y^*=Y(x,y;\varepsilon)=y+\varepsilon\eta(x,y)` such that `(y^*)'=f(x^*, y^*)`.
    A change of coordinates, to `r(x,y)` and `s(x,y)`, can be performed so this Lie group
    becomes the translation group, `r^*=r` and `s^*=s+\varepsilon`.
    They are tangents to the coordinate curves of the new system.

    Consider the transformation `(x, y) \to (X, Y)` such that the
    differential equation remains invariant. `\xi` and `\eta` are the tangents to
    the transformed coordinates `X` and `Y`, at `\varepsilon=0`.

    .. math:: \left(\frac{\partial X(x,y;\varepsilon)}{\partial\varepsilon
                }\right)|_{\varepsilon=0} = \xi,
              \left(\frac{\partial Y(x,y;\varepsilon)}{\partial\varepsilon
                }\right)|_{\varepsilon=0} = \eta,

    The infinitesimals can be found by solving the following PDE:

        >>> from sympy import Function, diff, Eq, pprint
        >>> from sympy.abc import x, y
        >>> xi, eta, h = map(Function, ['xi', 'eta', 'h'])
        >>> h = h(x, y)  # dy/dx = h
        >>> eta = eta(x, y)
        >>> xi = xi(x, y)
        >>> genform = Eq(eta.diff(x) + (eta.diff(y) - xi.diff(x))*h
        ... - (xi.diff(y))*h**2 - xi*(h.diff(x)) - eta*(h.diff(y)), 0)
        >>> pprint(genform)
        /d               d           \                     d              2       d
        |--(eta(x, y)) - --(xi(x, y))|*h(x, y) - eta(x, y)*--(h(x, y)) - h (x, y)*--(x
        \dy              dx          /                     dy                     dy
        <BLANKLINE>
                            d             d
        i(x, y)) - xi(x, y)*--(h(x, y)) + --(eta(x, y)) = 0
                            dx            dx

    Solving the above mentioned PDE is not trivial, and can be solved only by
    making intelligent assumptions for `\xi` and `\eta` (heuristics). Once an
    infinitesimal is found, the attempt to find more heuristics stops. This is done to
    optimise the speed of solving the differential equation. If a list of all the
    infinitesimals is needed, ``hint`` should be flagged as ``all``, which gives
    the complete list of infinitesimals. If the infinitesimals for a particular
    heuristic needs to be found, it can be passed as a flag to ``hint``.

    Examples
    ========

    >>> from sympy import Function, diff
    >>> from sympy.solvers.ode import infinitesimals
    >>> from sympy.abc import x
    >>> f = Function('f')
    >>> eq = f(x).diff(x) - x**2*f(x)
    >>> infinitesimals(eq)
    [{eta(x, f(x)): exp(x**3/3), xi(x, f(x)): 0}]

    References
    ==========

    - Solving differential equations by Symmetry Groups,
      John Starrett, pp. 1 - pp. 14

    """

    if isinstance(eq, Equality):
        eq = eq.lhs - eq.rhs
    if not func:
        eq, func = _preprocess(eq)
    variables = func.args
    if len(variables) != 1:
        raise ValueError("ODE's have only one independent variable")
    else:
        x = variables[0]
        if not order:
            order = ode_order(eq, func)
        if order != 1:
            raise NotImplementedError("Infinitesimals for only "
                "first order ODE's have been implemented")
        else:
            df = func.diff(x)
            # Matching differential equation of the form a*df + b
            a = Wild('a', exclude = [df])
            b = Wild('b', exclude = [df])
            if match:  # Used by lie_group hint
                h = match['h']
                y = match['y']
            else:
                match = collect(expand(eq), df).match(a*df + b)
                if match:
                    h = -simplify(match[b]/match[a])
                else:
                    try:
                        sol = solve(eq, df)
                    except NotImplementedError:
                        raise NotImplementedError("Infinitesimals for the "
                            "first order ODE could not be found")
                    else:
                        h = sol[0]  # Find infinitesimals for one solution
                y = Dummy("y")
                h = h.subs(func, y)

            u = Dummy("u")
            hx = h.diff(x)
            hy = h.diff(y)
            hinv = ((1/h).subs([(x, u), (y, x)])).subs(u, y)  # Inverse ODE
            match = {'h': h, 'func': func, 'hx': hx, 'hy': hy, 'y': y, 'hinv': hinv}
            if hint == 'all':
                xieta = []
                for heuristic in lie_heuristics:
                    function = globals()['lie_heuristic_' + heuristic]
                    inflist = function(match, comp=True)
                    if inflist:
                        xieta.extend([inf for inf in inflist if inf not in xieta])
                if xieta:
                    return xieta
                else:
                    raise NotImplementedError("Infinitesimals could not be found for "
                        "the given ODE")

            elif hint == 'default':
                for heuristic in lie_heuristics:
                    function = globals()['lie_heuristic_' + heuristic]
                    xieta = function(match, comp=False)
                    if xieta:
                        return xieta

                raise NotImplementedError("Infinitesimals could not be found for"
                    " the given ODE")

            elif hint not in lie_heuristics:
                 raise ValueError("Heuristic not recognized: " + hint)

            else:
                 function = globals()['lie_heuristic_' + hint]
                 xieta = function(match, comp=True)
                 if xieta:
                     return xieta
                 else:
                     raise ValueError("Infinitesimals could not be found using the"
                         " given heuristic")


def lie_heuristic_abaco1_simple(match, comp=False):
    r"""
    The first heuristic uses the following four sets of
    assumptions on `\xi` and `\eta`

    .. math:: \xi = 0, \eta = f(x)

    .. math:: \xi = 0, \eta = f(y)

    .. math:: \xi = f(x), \eta = 0

    .. math:: \xi = f(y), \eta = 0

    The success of this heuristic is determined by algebraic factorisation.
    For the first assumption `\xi = 0` and `\eta` to be a function of `x`, the PDE

    .. math:: \frac{\partial \eta}{\partial x} + (\frac{\partial \eta}{\partial y}
                - \frac{\partial \xi}{\partial x})*h
                - \frac{\partial \xi}{\partial y}*h^{2}
                - \xi*\frac{\partial h}{\partial x} - \eta*\frac{\partial h}{\partial y} = 0

    reduces to `f'(x) - f\frac{\partial h}{\partial y} = 0`
    If `\frac{\partial h}{\partial y}` is a function of `x`, then this can usually
    be integrated easily. A similar idea is applied to the other 3 assumptions as well.


    References
    ==========

    - E.S Cheb-Terrab, L.G.S Duarte and L.A,C.P da Mota, Computer Algebra
      Solving of First Order ODEs Using Symmetry Methods, pp. 8


    """

    xieta = []
    y = match['y']
    h = match['h']
    func = match['func']
    x = func.args[0]
    hx = match['hx']
    hy = match['hy']
    xi = Function('xi')(x, func)
    eta = Function('eta')(x, func)

    hysym = hy.free_symbols
    if y not in hysym:
        try:
            fx = exp(integrate(hy, x))
        except NotImplementedError:
            pass
        else:
            inf = {xi: S(0), eta: fx}
            if not comp:
                return [inf]
            if comp and inf not in xieta:
                xieta.append(inf)

    factor = hy/h
    facsym = factor.free_symbols
    if x not in facsym:
        try:
            fy = exp(integrate(factor, y))
        except NotImplementedError:
            pass
        else:
            inf = {xi: S(0), eta: fy.subs(y, func)}
            if not comp:
                return [inf]
            if comp and inf not in xieta:
                xieta.append(inf)

    factor = -hx/h
    facsym = factor.free_symbols
    if y not in facsym:
        try:
            fx = exp(integrate(factor, x))
        except NotImplementedError:
            pass
        else:
            inf = {xi: fx, eta: S(0)}
            if not comp:
                return [inf]
            if comp and inf not in xieta:
                xieta.append(inf)

    factor = -hx/(h**2)
    facsym = factor.free_symbols
    if x not in facsym:
        try:
            fy = exp(integrate(factor, y))
        except NotImplementedError:
            pass
        else:
            inf = {xi: fy.subs(y, func), eta: S(0)}
            if not comp:
                return [inf]
            if comp and inf not in xieta:
                xieta.append(inf)

    if xieta:
        return xieta

def lie_heuristic_abaco1_product(match, comp=False):
    r"""
    The second heuristic uses the following two assumptions on `\xi` and `\eta`

    .. math:: \eta = 0, \xi = f(x)*g(y)

    .. math:: \eta = f(x)*g(y), \xi = 0

    The first assumption of this heuristic holds good if
    `\frac{1}{h^{2}}\frac{\partial^2}{\partial x \partial y}\log(h)` is
    separable in `x` and `y`, then the separated factors containing `x`
    is `f(x)`, and `g(y)` is obtained by

    .. math:: e^{\int f\frac{\partial}{\partial x}\left(\frac{1}{f*h}\right)\,dy}

    provided `f\frac{\partial}{\partial x}\left(\frac{1}{f*h}\right)` is a function
    of `y` only.

    The second assumption holds good if `\frac{dy}{dx} = h(x, y)` is rewritten as
    `\frac{dy}{dx} = \frac{1}{h(y, x)}` and the same properties of the first assumption
    satisfies. After obtaining `f(x)` and `g(y)`, the coordinates are again
    interchanged, to get `\eta` as `f(x)*g(y)`


    References
    ==========
    - E.S. Cheb-Terrab, A.D. Roche, Symmetries and First Order
      ODE Patterns, pp. 7 - pp. 8

    """

    xieta = []
    y = match['y']
    h = match['h']
    hinv = match['hinv']
    func = match['func']
    x = func.args[0]
    xi = Function('xi')(x, func)
    eta = Function('eta')(x, func)


    inf = separatevars(((log(h).diff(y)).diff(x))/h**2, dict=True, symbols=[x, y])
    if inf and inf['coeff']:
        fx = inf[x]
        gy = simplify(fx*((1/(fx*h)).diff(x)))
        gysyms = gy.free_symbols
        if x not in gysyms:
            gy = exp(integrate(gy, y))
            inf = {eta: S(0), xi: (fx*gy).subs(y, func)}
            if not comp:
                return [inf]
            if comp and inf not in xieta:
                xieta.append(inf)

    u1 = Dummy("u1")
    inf = separatevars(((log(hinv).diff(y)).diff(x))/hinv**2, dict=True, symbols=[x, y])
    if inf and inf['coeff']:
        fx = inf[x]
        gy = simplify(fx*((1/(fx*hinv)).diff(x)))
        gysyms = gy.free_symbols
        if x not in gysyms:
            gy = exp(integrate(gy, y))
            etaval = fx*gy
            etaval = (etaval.subs([(x, u1), (y, x)])).subs(u1, y)
            inf = {eta: etaval.subs(y, func), xi: S(0)}
            if not comp:
                return [inf]
            if comp and inf not in xieta:
                xieta.append(inf)

    if xieta:
        return xieta

def lie_heuristic_bivariate(match, comp=False):
    r"""
    The third heuristic assumes the infinitesimals `\xi` and `\eta`
    to be bi-variate polynomials in `x` and `y`. The assumption made here
    for the logic below is that `h` is a rational function in `x` and `y`
    though that may not be necessary for the infinitesimals to be
    bivariate polynomials. The coefficients of the infinitesimals
    are found out by substituting them in the PDE and grouping similar terms
    that are polynomials and since they form a linear system, solve and check
    for non trivial solutions. The degree of the assumed bivariates
    are increased till a certain maximum value.

    References
    ==========
    - Lie Groups and Differential Equations
      pp. 327 - pp. 329

    """

    h = match['h']
    hx = match['hx']
    hy = match['hy']
    func = match['func']
    x = func.args[0]
    y = match['y']
    xi = Function('xi')(x, func)
    eta = Function('eta')(x, func)

    if h.is_rational_function():
        # The maximum degree that the infinitesimals can take is
        # calculated by this technique.
        etax, etay, etad, xix, xiy, xid = symbols("etax etay etad xix xiy xid")
        ipde = etax + (etay - xix)*h - xiy*h**2 - xid*hx - etad*hy
        num, denom = cancel(ipde).as_numer_denom()
        deg = Poly(num, x, y).total_degree()
        deta = Function('deta')(x, y)
        dxi = Function('dxi')(x, y)
        ipde = (deta.diff(x) + (deta.diff(y) - dxi.diff(x))*h - (dxi.diff(y))*h**2
            - dxi*hx - deta*hy)
        xieq = Symbol("xi0")
        etaeq = Symbol("eta0")

        for i in range(deg + 1):
            if i:
                xieq += Add(*[
                    Symbol("xi_" + str(power) + "_" + str(i - power))*x**power*y**(i - power)
                    for power in range(i + 1)])
                etaeq += Add(*[
                    Symbol("eta_" + str(power) + "_" + str(i - power))*x**power*y**(i - power)
                    for power in range(i + 1)])
            pden, denom = (ipde.subs({dxi: xieq, deta: etaeq}).doit()).as_numer_denom()
            pden = expand(pden)

            # If the individual terms are monomials, the coefficients
            # are grouped
            if pden.is_polynomial(x, y) and pden.is_Add:
                polyy = Poly(pden, x, y).as_dict()
            if polyy:
                symset = xieq.free_symbols.union(etaeq.free_symbols) - {x, y}
                soldict = solve(polyy.values(), *symset)
                if isinstance(soldict, list):
                    soldict = soldict[0]
                if any(x for x in soldict.values()):
                    xired = xieq.subs(soldict)
                    etared = etaeq.subs(soldict)
                    # Scaling is done by substituting one for the parameters
                    # This can be any number except zero.
                    dict_ = dict((sym, 1) for sym in symset)
                    inf = {eta: etared.subs(dict_).subs(y, func),
                        xi: xired.subs(dict_).subs(y, func)}
                    return [inf]

def lie_heuristic_chi(match, comp=False):
    r"""
    The aim of the fourth heuristic is to find the function `\chi(x, y)`
    that satisfies the PDE `\frac{d\chi}{dx} + h\frac{d\chi}{dx}
    - \frac{\partial h}{\partial y}\chi = 0`.

    This assumes `\chi` to be a bivariate polynomial in `x` and `y`. By intuition,
    `h` should be a rational function in `x` and `y`. The method used here is
    to substitute a general binomial for `\chi` up to a certain maximum degree
    is reached. The coefficients of the polynomials, are calculated by by collecting
    terms of the same order in `x` and `y`.

    After finding `\chi`, the next step is to use `\eta = \xi*h + \chi`, to
    determine `\xi` and `\eta`. This can be done by dividing `\chi` by `h`
    which would give `-\xi` as the quotient and `\eta` as the remainder.


    References
    ==========
    - E.S Cheb-Terrab, L.G.S Duarte and L.A,C.P da Mota, Computer Algebra
      Solving of First Order ODEs Using Symmetry Methods, pp. 8

    """

    h = match['h']
    hx = match['hx']
    hy = match['hy']
    func = match['func']
    x = func.args[0]
    y = match['y']
    xi = Function('xi')(x, func)
    eta = Function('eta')(x, func)

    if h.is_rational_function():
        schi, schix, schiy = symbols("schi, schix, schiy")
        cpde = schix + h*schiy - hy*schi
        num, denom = cancel(cpde).as_numer_denom()
        deg = Poly(num, x, y).total_degree()

        chi = Function('chi')(x, y)
        chix = chi.diff(x)
        chiy = chi.diff(y)
        cpde = chix + h*chiy - hy*chi
        chieq = Symbol("chi")
        for i in range(1, deg + 1):
            chieq += Add(*[
                Symbol("chi_" + str(power) + "_" + str(i - power))*x**power*y**(i - power)
                for power in range(i + 1)])
            cnum, cden = cancel(cpde.subs({chi : chieq}).doit()).as_numer_denom()
            cnum = expand(cnum)
            if cnum.is_polynomial(x, y) and cnum.is_Add:
                cpoly = Poly(cnum, x, y).as_dict()
                if cpoly:
                    solsyms = chieq.free_symbols - {x, y}
                    soldict = solve(cpoly.values(), *solsyms)
                    if isinstance(soldict, list):
                        soldict = soldict[0]
                    if any(x for x in soldict.values()):
                        chieq = chieq.subs(soldict)
                        dict_ = dict((sym, 1) for sym in solsyms)
                        chieq = chieq.subs(dict_)
                        # After finding chi, the main aim is to find out
                        # eta, xi by the equation eta = xi*h + chi
                        # One method to set xi, would be rearranging it to
                        # (eta/h) - xi = (chi/h). This would mean dividing
                        # chi by h would give -xi as the quotient and eta
                        # as the remainder. Thanks to Sean Vig for suggesting
                        # this method.
                        xic, etac = div(chieq, h)
                        inf = {eta: etac.subs(y, func), xi: -xic.subs(y, func)}
                        return [inf]

def lie_heuristic_function_sum(match, comp=False):
    r"""
    This heuristic uses the following two assumptions on `\xi` and `\eta`

    .. math:: \eta = 0, \xi = f(x) + g(y)

    .. math:: \eta = f(x) + g(y), \xi = 0

    The first assumption of this heuristic holds good if

    .. math:: \frac{\partial}{\partial y}[(h\frac{\partial^{2}}{
                \partial x^{2}}(h^{-1}))^{-1}]

    is separable in `x` and `y`,

    1. The separated factors containing `y` is `\frac{\partial g}{\partial y}`.
       From this `g(y)` can be determined.
    2. The separated factors containing `x` is `f''(x)`.
    3. `h\frac{\partial^{2}}{\partial x^{2}}(h^{-1})` equals
       `\frac{f''(x)}{f(x) + g(y)}`. From this `f(x)` can be determined.

    The second assumption holds good if `\frac{dy}{dx} = h(x, y)` is rewritten as
    `\frac{dy}{dx} = \frac{1}{h(y, x)}` and the same properties of the first
    assumption satisfies. After obtaining `f(x)` and `g(y)`, the coordinates
    are again interchanged, to get `\eta` as `f(x) + g(y)`.

    For both assumptions, the constant factors are separated among `g(y)`
    and `f''(x)`, such that `f''(x)` obtained from 3] is the same as that
    obtained from 2]. If not possible, then this heuristic fails.


    References
    ==========
    - E.S. Cheb-Terrab, A.D. Roche, Symmetries and First Order
      ODE Patterns, pp. 7 - pp. 8

    """

    xieta = []
    h = match['h']
    hx = match['hx']
    hy = match['hy']
    func = match['func']
    hinv = match['hinv']
    x = func.args[0]
    y = match['y']
    xi = Function('xi')(x, func)
    eta = Function('eta')(x, func)

    for odefac in [h, hinv]:
        factor = odefac*((1/odefac).diff(x, 2))
        sep = separatevars((1/factor).diff(y), dict=True, symbols=[x, y])
        if sep and sep['coeff'] and sep[x].has(x) and sep[y].has(y):
            k = Dummy("k")
            try:
                gy = k*integrate(sep[y], y)
            except NotImplementedError:
                pass
            else:
                fdd = 1/(k*sep[x]*sep['coeff'])
                fx = simplify(fdd/factor - gy)
                check = simplify(fx.diff(x, 2) - fdd)
                if fx:
                    if not check:
                        fx = fx.subs(k, 1)
                        gy = (gy/k)
                    else:
                        sol = solve(check, k)
                        if sol:
                            sol = sol[0]
                            fx = fx.subs(k, sol)
                            gy = (gy/k)*sol
                        else:
                            continue
                    if odefac == hinv:  # Inverse ODE
                        fx = fx.subs(x, y)
                        gy = gy.subs(y, x)
                    etaval = factor_terms(fx + gy)
                    if etaval.is_Mul:
                        etaval = Mul(*[arg for arg in etaval.args if arg.has(x, y)])
                    if odefac == hinv:  # Inverse ODE
                        inf = {eta: etaval.subs(y, func), xi : S(0)}
                    else:
                        inf = {xi: etaval.subs(y, func), eta : S(0)}
                    if not comp:
                        return [inf]
                    else:
                        xieta.append(inf)

        if xieta:
            return xieta

def lie_heuristic_abaco2_similar(match, comp=False):
    r"""
    This heuristic uses the following two assumptions on `\xi` and `\eta`

    .. math:: \eta = g(x), \xi = f(x)

    .. math:: \eta = f(y), \xi = g(y)

    For the first assumption,

    1. First `\frac{\frac{\partial h}{\partial y}}{\frac{\partial^{2} h}{
       \partial yy}}` is calculated. Let us say this value is A

    2. If this is constant, then `h` is matched to the form `A(x) + B(x)e^{
       \frac{y}{C}}` then, `\frac{e^{\int \frac{A(x)}{C} \,dx}}{B(x)}` gives `f(x)`
       and `A(x)*f(x)` gives `g(x)`

    3. Otherwise `\frac{\frac{\partial A}{\partial X}}{\frac{\partial A}{
       \partial Y}} = \gamma` is calculated. If

       a] `\gamma` is a function of `x` alone

       b] `\frac{\gamma\frac{\partial h}{\partial y} - \gamma'(x) - \frac{
       \partial h}{\partial x}}{h + \gamma} = G` is a function of `x` alone.
       then, `e^{\int G \,dx}` gives `f(x)` and `-\gamma*f(x)` gives `g(x)`

    The second assumption holds good if `\frac{dy}{dx} = h(x, y)` is rewritten as
    `\frac{dy}{dx} = \frac{1}{h(y, x)}` and the same properties of the first assumption
    satisfies. After obtaining `f(x)` and `g(x)`, the coordinates are again
    interchanged, to get `\xi` as `f(x^*)` and `\eta` as `g(y^*)`

    References
    ==========
    - E.S. Cheb-Terrab, A.D. Roche, Symmetries and First Order
      ODE Patterns, pp. 10 - pp. 12

    """

    xieta = []
    h = match['h']
    hx = match['hx']
    hy = match['hy']
    func = match['func']
    hinv = match['hinv']
    x = func.args[0]
    y = match['y']
    xi = Function('xi')(x, func)
    eta = Function('eta')(x, func)

    factor = cancel(h.diff(y)/h.diff(y, 2))
    factorx = factor.diff(x)
    factory = factor.diff(y)
    if not factor.has(x) and not factor.has(y):
        A = Wild('A', exclude=[y])
        B = Wild('B', exclude=[y])
        C = Wild('C', exclude=[x, y])
        match = h.match(A + B*exp(y/C))
        try:
            tau = exp(-integrate(match[A]/match[C]), x)/match[B]
        except NotImplementedError:
            pass
        else:
            gx = match[A]*tau
            return [{xi: tau, eta: gx}]

    else:
        gamma = cancel(factorx/factory)
        if not gamma.has(y):
            tauint = cancel((gamma*hy - gamma.diff(x) - hx)/(h + gamma))
            if not tauint.has(y):
                try:
                    tau = exp(integrate(tauint, x))
                except NotImplementedError:
                    pass
                else:
                    gx = -tau*gamma
                    return [{xi: tau, eta: gx}]

    factor = cancel(hinv.diff(y)/hinv.diff(y, 2))
    factorx = factor.diff(x)
    factory = factor.diff(y)
    if not factor.has(x) and not factor.has(y):
        A = Wild('A', exclude=[y])
        B = Wild('B', exclude=[y])
        C = Wild('C', exclude=[x, y])
        match = h.match(A + B*exp(y/C))
        try:
            tau = exp(-integrate(match[A]/match[C]), x)/match[B]
        except NotImplementedError:
            pass
        else:
            gx = match[A]*tau
            return [{eta: tau.subs(x, func), xi: gx.subs(x, func)}]

    else:
        gamma = cancel(factorx/factory)
        if not gamma.has(y):
            tauint = cancel((gamma*hinv.diff(y) - gamma.diff(x) - hinv.diff(x))/(
                hinv + gamma))
            if not tauint.has(y):
                try:
                    tau = exp(integrate(tauint, x))
                except NotImplementedError:
                    pass
                else:
                    gx = -tau*gamma
                    return [{eta: tau.subs(x, func), xi: gx.subs(x, func)}]


def lie_heuristic_abaco2_unique_unknown(match, comp=False):
    r"""
    This heuristic assumes the presence of unknown functions or known functions
    with non-integer powers.

    1. A list of all functions and non-integer powers containing x and y
    2. Loop over each element `f` in the list, find `\frac{\frac{\partial f}{\partial x}}{
       \frac{\partial f}{\partial x}} = R`

       If it is separable in `x` and `y`, let `X` be the factors containing `x`. Then

       a] Check if `\xi = X` and `\eta = -\frac{X}{R}` satisfy the PDE. If yes, then return
          `\xi` and `\eta`
       b] Check if `\xi = \frac{-R}{X}` and `\eta = -\frac{1}{X}` satisfy the PDE.
           If yes, then return `\xi` and `\eta`

       If not, then check if

       a] :math:`\xi = -R,\eta = 1`

       b] :math:`\xi = 1, \eta = -\frac{1}{R}`

       are solutions.

    References
    ==========
    - E.S. Cheb-Terrab, A.D. Roche, Symmetries and First Order
      ODE Patterns, pp. 10 - pp. 12

    """

    xieta = []
    h = match['h']
    hx = match['hx']
    hy = match['hy']
    func = match['func']
    hinv = match['hinv']
    x = func.args[0]
    y = match['y']
    xi = Function('xi')(x, func)
    eta = Function('eta')(x, func)

    funclist = []
    for atom in h.atoms(Pow):
        base, exp = atom.as_base_exp()
        if base.has(x) and base.has(y):
            if not exp.is_Integer:
                funclist.append(atom)

    for function in h.atoms(AppliedUndef):
        syms = function.free_symbols
        if x in syms and y in syms:
            funclist.append(function)

    for f in funclist:
        frac = cancel(f.diff(y)/f.diff(x))
        sep = separatevars(frac, dict=True, symbols=[x, y])
        if sep and sep['coeff']:
            xitry1 = sep[x]
            etatry1 = -1/(sep[y]*sep['coeff'])
            pde1 = etatry1.diff(y)*h - xitry1.diff(x)*h - xitry1*hx - etatry1*hy
            if not simplify(pde1):
                return [{xi: xitry1, eta: etatry1.subs(y, func)}]
            xitry2 = 1/etatry1
            etatry2 = 1/xitry1
            pde2 = etatry2.diff(x) - (xitry2.diff(y))*h**2 - xitry2*hx - etatry2*hy
            if not simplify(expand(pde2)):
                return [{xi: xitry2.subs(y, func), eta: etatry2}]

        else:
            etatry = -1/frac
            pde = etatry.diff(x) + etatry.diff(y)*h - hx - etatry*hy
            if not simplify(pde):
                return [{xi: S(1), eta: etatry.subs(y, func)}]
            xitry = -frac
            pde = -xitry.diff(x)*h -xitry.diff(y)*h**2 - xitry*hx -hy
            if not simplify(expand(pde)):
                return [{xi: xitry.subs(y, func), eta: S(1)}]


def lie_heuristic_abaco2_unique_general(match, comp=False):
    r"""
    This heuristic finds if infinitesimals of the form `\eta = f(x)`, `\xi = g(y)`
    without making any assumptions on `h`.

    The complete sequence of steps is given in the paper mentioned below.

    References
    ==========
    - E.S. Cheb-Terrab, A.D. Roche, Symmetries and First Order
      ODE Patterns, pp. 10 - pp. 12

    """
    xieta = []
    h = match['h']
    hx = match['hx']
    hy = match['hy']
    func = match['func']
    hinv = match['hinv']
    x = func.args[0]
    y = match['y']
    xi = Function('xi')(x, func)
    eta = Function('eta')(x, func)

    C = S(0)
    A = hx.diff(y)
    B = hy.diff(y) + hy**2
    C = hx.diff(x) - hx**2

    if not (A and B and C):
        return

    Ax = A.diff(x)
    Ay = A.diff(y)
    Axy = Ax.diff(y)
    Axx = Ax.diff(x)
    Ayy = Ay.diff(y)
    D = simplify(2*Axy + hx*Ay - Ax*hy + (hx*hy + 2*A)*A)*A - 3*Ax*Ay
    if not D:
        E1 = simplify(3*Ax**2 + ((hx**2 + 2*C)*A - 2*Axx)*A)
        if E1:
            E2 = simplify((2*Ayy + (2*B - hy**2)*A)*A - 3*Ay**2)
            if not E2:
                E3 = simplify(
                    E1*((28*Ax + 4*hx*A)*A**3 - E1*(hy*A + Ay)) - E1.diff(x)*8*A**4)
                if not E3:
                    etaval = cancel((4*A**3*(Ax - hx*A) + E1*(hy*A - Ay))/(S(2)*A*E1))
                    if x not in etaval:
                        try:
                            etaval = exp(integrate(etaval, y))
                        except NotImplementedError:
                            pass
                        else:
                            xival = -4*A**3*etaval/E1
                            if y not in xival:
                                return [{xi: xival, eta: etaval.subs(y, func)}]

    else:
        E1 = simplify((2*Ayy + (2*B - hy**2)*A)*A - 3*Ay**2)
        if E1:
            E2 = simplify(
                4*A**3*D - D**2 + E1*((2*Axx - (hx**2 + 2*C)*A)*A - 3*Ax**2))
            if not E2:
                E3 = simplify(
                   -(A*D)*E1.diff(y) + ((E1.diff(x) - hy*D)*A + 3*Ay*D +
                    (A*hx - 3*Ax)*E1)*E1)
                if not E3:
                    etaval = cancel(((A*hx - Ax)*E1 - (Ay + A*hy)*D)/(S(2)*A*D))
                    if x not in etaval:
                        try:
                            etaval = exp(integrate(etaval, y))
                        except NotImplementedError:
                            pass
                        else:
                            xival = -E1*etaval/D
                            if y not in xival:
                                return [{xi: xival, eta: etaval.subs(y, func)}]


def lie_heuristic_linear(match, comp=False):
    r"""
    This heuristic assumes

    1. `\xi = ax + by + c` and
    2. `\eta = fx + gy + h`

    After substituting the following assumptions in the determining PDE, it
    reduces to

    .. math:: f + (g - a)h - bh^{2} - (ax + by + c)\frac{\partial h}{\partial x}
                 - (fx + gy + c)\frac{\partial h}{\partial y}

    Solving the reduced PDE obtained, using the method of characteristics, becomes
    impractical. The method followed is grouping similar terms and solving the system
    of linear equations obtained. The difference between the bivariate heuristic is that
    `h` need not be a rational function in this case.

    References
    ==========
    - E.S. Cheb-Terrab, A.D. Roche, Symmetries and First Order
      ODE Patterns, pp. 10 - pp. 12

    """
    xieta = []
    h = match['h']
    hx = match['hx']
    hy = match['hy']
    func = match['func']
    hinv = match['hinv']
    x = func.args[0]
    y = match['y']
    xi = Function('xi')(x, func)
    eta = Function('eta')(x, func)

    coeffdict = {}
    symbols = numbered_symbols("c", cls=Dummy)
    symlist = [next(symbols) for _ in islice(symbols, 6)]
    C0, C1, C2, C3, C4, C5 = symlist
    pde = C3 + (C4 - C0)*h -(C0*x + C1*y + C2)*hx - (C3*x + C4*y + C5)*hy - C1*h**2
    pde, denom = pde.as_numer_denom()
    pde = powsimp(expand(pde))
    if pde.is_Add:
        terms = pde.args
        for term in terms:
            if term.is_Mul:
                rem = Mul(*[m for m in term.args if not m.has(x, y)])
                xypart = term/rem
                if xypart not in coeffdict:
                    coeffdict[xypart] = rem
                else:
                    coeffdict[xypart] += rem
            else:
                if term not in coeffdict:
                    coeffdict[term] = S(1)
                else:
                    coeffdict[term] += S(1)

    sollist = coeffdict.values()
    soldict = solve(sollist, symlist)
    if soldict:
        if isinstance(soldict, list):
            soldict = soldict[0]
        subval = soldict.values()
        if any(t for t in subval):
            onedict = dict(zip(symlist, [1]*6))
            xival = C0*x + C1*func + C2
            etaval = C3*x + C4*func + C5
            xival = xival.subs(soldict)
            etaval = etaval.subs(soldict)
            xival = xival.subs(onedict)
            etaval = etaval.subs(onedict)
            return [{xi: xival, eta: etaval}]


def sysode_linear_2eq_order1(match_):
    x = match_['func'][0].func
    y = match_['func'][1].func
    func = match_['func']
    fc = match_['func_coeff']
    eq = match_['eq']
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    r = dict()
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    for i in range(2):
        eqs = 0
        for terms in Add.make_args(eq[i]):
            eqs += terms/fc[i,func[i],1]
        eq[i] = eqs

    # for equations Eq(a1*diff(x(t),t), a*x(t) + b*y(t) + k1)
    # and Eq(a2*diff(x(t),t), c*x(t) + d*y(t) + k2)
    r['a'] = -fc[0,x(t),0]/fc[0,x(t),1]
    r['c'] = -fc[1,x(t),0]/fc[1,y(t),1]
    r['b'] = -fc[0,y(t),0]/fc[0,x(t),1]
    r['d'] = -fc[1,y(t),0]/fc[1,y(t),1]
    forcing = [S(0),S(0)]
    for i in range(2):
        for j in Add.make_args(eq[i]):
            if not j.has(x(t), y(t)):
                forcing[i] += j
    if not (forcing[0].has(t) or forcing[1].has(t)):
        r['k1'] = forcing[0]
        r['k2'] = forcing[1]
    else:
        raise NotImplementedError("Only homogeneous problems are supported" +
                                  " (and constant inhomogeneity)")

    if match_['type_of_equation'] == 'type1':
        sol = _linear_2eq_order1_type1(x, y, t, r, eq)
    if match_['type_of_equation'] == 'type2':
        gsol = _linear_2eq_order1_type1(x, y, t, r, eq)
        psol = _linear_2eq_order1_type2(x, y, t, r, eq)
        sol = [Eq(x(t), gsol[0].rhs+psol[0]), Eq(y(t), gsol[1].rhs+psol[1])]
    if match_['type_of_equation'] == 'type3':
        sol = _linear_2eq_order1_type3(x, y, t, r, eq)
    if match_['type_of_equation'] == 'type4':
        sol = _linear_2eq_order1_type4(x, y, t, r, eq)
    if match_['type_of_equation'] == 'type5':
        sol = _linear_2eq_order1_type5(x, y, t, r, eq)
    if match_['type_of_equation'] == 'type6':
        sol = _linear_2eq_order1_type6(x, y, t, r, eq)
    if match_['type_of_equation'] == 'type7':
        sol = _linear_2eq_order1_type7(x, y, t, r, eq)
    return sol

def _linear_2eq_order1_type1(x, y, t, r, eq):
    r"""
    It is classified under system of two linear homogeneous first-order constant-coefficient
    ordinary differential equations.

    The equations which come under this type are

    .. math:: x' = ax + by,

    .. math:: y' = cx + dy

    The characteristics equation is written as

    .. math:: \lambda^{2} + (a+d) \lambda + ad - bc = 0

    and its discriminant is `D = (a-d)^{2} + 4bc`. There are several cases

    1. Case when `ad - bc \neq 0`. The origin of coordinates, `x = y = 0`,
    is the only stationary point; it is
    - a node if `D = 0`
    - a node if `D > 0` and `ad - bc > 0`
    - a saddle if `D > 0` and `ad - bc < 0`
    - a focus if `D < 0` and `a + d \neq 0`
    - a centre if `D < 0` and `a + d \neq 0`.

    1.1. If `D > 0`. The characteristic equation has two distinct real roots
    `\lambda_1` and `\lambda_ 2` . The general solution of the system in question is expressed as

    .. math:: x = C_1 b e^{\lambda_1 t} + C_2 b e^{\lambda_2 t}

    .. math:: y = C_1 (\lambda_1 - a) e^{\lambda_1 t} + C_2 (\lambda_2 - a) e^{\lambda_2 t}

    where `C_1` and `C_2` being arbitrary constants

    1.2. If `D < 0`. The characteristics equation has two conjugate
    roots, `\lambda_1 = \sigma + i \beta` and `\lambda_2 = \sigma - i \beta`.
    The general solution of the system is given by

    .. math:: x = b e^{\sigma t} (C_1 \sin(\beta t) + C_2 \cos(\beta t))

    .. math:: y = e^{\sigma t} ([(\sigma - a) C_1 - \beta C_2] \sin(\beta t) + [\beta C_1 + (\sigma - a) C_2 \cos(\beta t)])

    1.3. If `D = 0` and `a \neq d`. The characteristic equation has
    two equal roots, `\lambda_1 = \lambda_2`. The general solution of the system is written as

    .. math:: x = 2b (C_1 + \frac{C_2}{a-d} + C_2 t) e^{\frac{a+d}{2} t}

    .. math:: y = [(d - a) C_1 + C_2 + (d - a) C_2 t] e^{\frac{a+d}{2} t}

    1.4. If `D = 0` and `a = d \neq 0` and `b = 0`

    .. math:: x = C_1 e^{a t} , y = (c C_1 t + C_2) e^{a t}

    1.5. If `D = 0` and `a = d \neq 0` and `c = 0`

    .. math:: x = (b C_1 t + C_2) e^{a t} , y = C_1 e^{a t}

    2. Case when `ad - bc = 0` and `a^{2} + b^{2} > 0`. The whole straight
    line `ax + by = 0` consists of singular points. The original system of differential
    equations can be rewritten as

    .. math:: x' = ax + by , y' = k (ax + by)

    2.1 If `a + bk \neq 0`, solution will be

    .. math:: x = b C_1 + C_2 e^{(a + bk) t} , y = -a C_1 + k C_2 e^{(a + bk) t}

    2.2 If `a + bk = 0`, solution will be

    .. math:: x = C_1 (bk t - 1) + b C_2 t , y = k^{2} b C_1 t + (b k^{2} t + 1) C_2

    """

    l = Dummy('l')
    C1, C2 = get_numbered_constants(eq, num=2)
    a, b, c, d = r['a'], r['b'], r['c'], r['d']
    real_coeff = all(v.is_real for v in (a, b, c, d))
    D = (a - d)**2 + 4*b*c
    l1 = (a + d + sqrt(D))/2
    l2 = (a + d - sqrt(D))/2
    equal_roots = Eq(D, 0).expand()
    gsol1, gsol2 = [], []

    # Solutions have exponential form if either D > 0 with real coefficients
    # or D != 0 with complex coefficients. Eigenvalues are distinct.
    # For each eigenvalue lam, pick an eigenvector, making sure we don't get (0, 0)
    # The candidates are (b, lam-a) and (lam-d, c).
    exponential_form = D > 0 if real_coeff else Not(equal_roots)
    bad_ab_vector1 = And(Eq(b, 0), Eq(l1, a))
    bad_ab_vector2 = And(Eq(b, 0), Eq(l2, a))
    vector1 = Matrix((Piecewise((l1 - d, bad_ab_vector1), (b, True)),
                      Piecewise((c, bad_ab_vector1), (l1 - a, True))))
    vector2 = Matrix((Piecewise((l2 - d, bad_ab_vector2), (b, True)),
                      Piecewise((c, bad_ab_vector2), (l2 - a, True))))
    sol_vector = C1*exp(l1*t)*vector1 + C2*exp(l2*t)*vector2
    gsol1.append((sol_vector[0], exponential_form))
    gsol2.append((sol_vector[1], exponential_form))

    # Solutions have trigonometric form for real coefficients with D < 0
    # Both b and c are nonzero in this case, so (b, lam-a) is an eigenvector
    # It splits into real/imag parts as (b, sigma-a) and (0, beta). Then
    # multiply it by C1(cos(beta*t) + I*C2*sin(beta*t)) and separate real/imag
    trigonometric_form = D < 0 if real_coeff else False
    sigma = re(l1)
    if im(l1).is_positive:
        beta = im(l1)
    else:
        beta = im(l2)
    vector1 = Matrix((b, sigma - a))
    vector2 = Matrix((0, beta))
    sol_vector = exp(sigma*t) * (C1*(cos(beta*t)*vector1 - sin(beta*t)*vector2) + \
        C2*(sin(beta*t)*vector1 + cos(beta*t)*vector2))
    gsol1.append((sol_vector[0], trigonometric_form))
    gsol2.append((sol_vector[1], trigonometric_form))

    # Final case is D == 0, a single eigenvalue. If the eigenspace is 2-dimensional
    # then we have a scalar matrix, deal with this case first.
    scalar_matrix = And(Eq(a, d), Eq(b, 0), Eq(c, 0))

    vector1 = Matrix((S.One, S.Zero))
    vector2 = Matrix((S.Zero, S.One))
    sol_vector = exp(l1*t) * (C1*vector1 + C2*vector2)
    gsol1.append((sol_vector[0], scalar_matrix))
    gsol2.append((sol_vector[1], scalar_matrix))

    # Have one eigenvector. Get a generalized eigenvector from (A-lam)*vector2 = vector1
    vector1 = Matrix((Piecewise((l1 - d, bad_ab_vector1), (b, True)),
                      Piecewise((c, bad_ab_vector1), (l1 - a, True))))
    vector2 = Matrix((Piecewise((S.One, bad_ab_vector1), (S.Zero, Eq(a, l1)),
                                (b/(a - l1), True)),
                      Piecewise((S.Zero, bad_ab_vector1), (S.One, Eq(a, l1)),
                                (S.Zero, True))))
    sol_vector = exp(l1*t) * (C1*vector1  + C2*(vector2 + t*vector1))
    gsol1.append((sol_vector[0], equal_roots))
    gsol2.append((sol_vector[1], equal_roots))
    return [Eq(x(t), Piecewise(*gsol1)), Eq(y(t), Piecewise(*gsol2))]


def _linear_2eq_order1_type2(x, y, t, r, eq):
    r"""
    The equations of this type are

    .. math:: x' = ax + by + k1 , y' = cx + dy + k2

    The general solution of this system is given by sum of its particular solution and the
    general solution of the corresponding homogeneous system is obtained from type1.

    1. When `ad - bc \neq 0`. The particular solution will be
    `x = x_0` and `y = y_0` where `x_0` and `y_0` are determined by solving linear system of equations

    .. math:: a x_0 + b y_0 + k1 = 0 , c x_0 + d y_0 + k2 = 0

    2. When `ad - bc = 0` and `a^{2} + b^{2} > 0`. In this case, the system of equation becomes

    .. math:: x' = ax + by + k_1 , y' = k (ax + by) + k_2

    2.1 If `\sigma = a + bk \neq 0`, particular solution is given by

    .. math:: x = b \sigma^{-1} (c_1 k - c_2) t - \sigma^{-2} (a c_1 + b c_2)

    .. math:: y = kx + (c_2 - c_1 k) t

    2.2 If `\sigma = a + bk = 0`, particular solution is given by

    .. math:: x = \frac{1}{2} b (c_2 - c_1 k) t^{2} + c_1 t

    .. math:: y = kx + (c_2 - c_1 k) t

    """
    r['k1'] = -r['k1']; r['k2'] = -r['k2']
    if (r['a']*r['d'] - r['b']*r['c']) != 0:
        x0, y0 = symbols('x0, y0', cls=Dummy)
        sol = solve((r['a']*x0+r['b']*y0+r['k1'], r['c']*x0+r['d']*y0+r['k2']), x0, y0)
        psol = [sol[x0], sol[y0]]
    elif (r['a']*r['d'] - r['b']*r['c']) == 0 and (r['a']**2+r['b']**2) > 0:
        k = r['c']/r['a']
        sigma = r['a'] + r['b']*k
        if sigma != 0:
            sol1 = r['b']*sigma**-1*(r['k1']*k-r['k2'])*t - sigma**-2*(r['a']*r['k1']+r['b']*r['k2'])
            sol2 = k*sol1 + (r['k2']-r['k1']*k)*t
        else:
            # FIXME: a previous typo fix shows this is not covered by tests
            sol1 = r['b']*(r['k2']-r['k1']*k)*t**2 + r['k1']*t
            sol2 = k*sol1 + (r['k2']-r['k1']*k)*t
        psol = [sol1, sol2]
    return psol

def _linear_2eq_order1_type3(x, y, t, r, eq):
    r"""
    The equations of this type of ode are

    .. math:: x' = f(t) x + g(t) y

    .. math:: y' = g(t) x + f(t) y

    The solution of such equations is given by

    .. math:: x = e^{F} (C_1 e^{G} + C_2 e^{-G}) , y = e^{F} (C_1 e^{G} - C_2 e^{-G})

    where `C_1` and `C_2` are arbitrary constants, and

    .. math:: F = \int f(t) \,dt , G = \int g(t) \,dt

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    F = Integral(r['a'], t)
    G = Integral(r['b'], t)
    sol1 = exp(F)*(C1*exp(G) + C2*exp(-G))
    sol2 = exp(F)*(C1*exp(G) - C2*exp(-G))
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order1_type4(x, y, t, r, eq):
    r"""
    The equations of this type of ode are .

    .. math:: x' = f(t) x + g(t) y

    .. math:: y' = -g(t) x + f(t) y

    The solution is given by

    .. math:: x = F (C_1 \cos(G) + C_2 \sin(G)), y = F (-C_1 \sin(G) + C_2 \cos(G))

    where `C_1` and `C_2` are arbitrary constants, and

    .. math:: F = \int f(t) \,dt , G = \int g(t) \,dt

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    if r['b'] == -r['c']:
        F = exp(Integral(r['a'], t))
        G = Integral(r['b'], t)
        sol1 = F*(C1*cos(G) + C2*sin(G))
        sol2 = F*(-C1*sin(G) + C2*cos(G))
    elif r['d'] == -r['a']:
        F = exp(Integral(r['c'], t))
        G = Integral(r['d'], t)
        sol1 = F*(-C1*sin(G) + C2*cos(G))
        sol2 = F*(C1*cos(G) + C2*sin(G))
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order1_type5(x, y, t, r, eq):
    r"""
    The equations of this type of ode are .

    .. math:: x' = f(t) x + g(t) y

    .. math:: y' = a g(t) x + [f(t) + b g(t)] y

    The transformation of

    .. math:: x = e^{\int f(t) \,dt} u , y = e^{\int f(t) \,dt} v , T = \int g(t) \,dt

    leads to a system of constant coefficient linear differential equations

    .. math:: u'(T) = v , v'(T) = au + bv

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    u, v = symbols('u, v', cls=Function)
    T = Symbol('T')
    if not cancel(r['c']/r['b']).has(t):
        p = cancel(r['c']/r['b'])
        q = cancel((r['d']-r['a'])/r['b'])
        eq = (Eq(diff(u(T),T), v(T)), Eq(diff(v(T),T), p*u(T)+q*v(T)))
        sol = dsolve(eq)
        sol1 = exp(Integral(r['a'], t))*sol[0].rhs.subs(T, Integral(r['b'],t))
        sol2 = exp(Integral(r['a'], t))*sol[1].rhs.subs(T, Integral(r['b'],t))
    if not cancel(r['a']/r['d']).has(t):
        p = cancel(r['a']/r['d'])
        q = cancel((r['b']-r['c'])/r['d'])
        sol = dsolve(Eq(diff(u(T),T), v(T)), Eq(diff(v(T),T), p*u(T)+q*v(T)))
        sol1 = exp(Integral(r['c'], t))*sol[1].rhs.subs(T, Integral(r['d'],t))
        sol2 = exp(Integral(r['c'], t))*sol[0].rhs.subs(T, Integral(r['d'],t))
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order1_type6(x, y, t, r, eq):
    r"""
    The equations of this type of ode are .

    .. math:: x' = f(t) x + g(t) y

    .. math:: y' = a [f(t) + a h(t)] x + a [g(t) - h(t)] y

    This is solved by first multiplying the first equation by `-a` and adding
    it to the second equation to obtain

    .. math:: y' - a x' = -a h(t) (y - a x)

    Setting `U = y - ax` and integrating the equation we arrive at

    .. math:: y - ax = C_1 e^{-a \int h(t) \,dt}

    and on substituting the value of y in first equation give rise to first order ODEs. After solving for
    `x`, we can obtain `y` by substituting the value of `x` in second equation.

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    p = 0
    q = 0
    p1 = cancel(r['c']/cancel(r['c']/r['d']).as_numer_denom()[0])
    p2 = cancel(r['a']/cancel(r['a']/r['b']).as_numer_denom()[0])
    for n, i in enumerate([p1, p2]):
        for j in Mul.make_args(collect_const(i)):
            if not j.has(t):
                q = j
            if q!=0 and n==0:
                if ((r['c']/j - r['a'])/(r['b'] - r['d']/j)) == j:
                    p = 1
                    s = j
                    break
            if q!=0 and n==1:
                if ((r['a']/j - r['c'])/(r['d'] - r['b']/j)) == j:
                    p = 2
                    s = j
                    break
    if p == 1:
        equ = diff(x(t),t) - r['a']*x(t) - r['b']*(s*x(t) + C1*exp(-s*Integral(r['b'] - r['d']/s, t)))
        hint1 = classify_ode(equ)[1]
        sol1 = dsolve(equ, hint=hint1+'_Integral').rhs
        sol2 = s*sol1 + C1*exp(-s*Integral(r['b'] - r['d']/s, t))
    elif p ==2:
        equ = diff(y(t),t) - r['c']*y(t) - r['d']*s*y(t) + C1*exp(-s*Integral(r['d'] - r['b']/s, t))
        hint1 = classify_ode(equ)[1]
        sol2 = dsolve(equ, hint=hint1+'_Integral').rhs
        sol1 = s*sol2 + C1*exp(-s*Integral(r['d'] - r['b']/s, t))
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order1_type7(x, y, t, r, eq):
    r"""
    The equations of this type of ode are .

    .. math:: x' = f(t) x + g(t) y

    .. math:: y' = h(t) x + p(t) y

    Differentiating the first equation and substituting the value of `y`
    from second equation will give a second-order linear equation

    .. math:: g x'' - (fg + gp + g') x' + (fgp - g^{2} h + f g' - f' g) x = 0

    This above equation can be easily integrated if following conditions are satisfied.

    1. `fgp - g^{2} h + f g' - f' g = 0`

    2. `fgp - g^{2} h + f g' - f' g = ag, fg + gp + g' = bg`

    If first condition is satisfied then it is solved by current dsolve solver and in second case it becomes
    a constant coefficient differential equation which is also solved by current solver.

    Otherwise if the above condition fails then,
    a particular solution is assumed as `x = x_0(t)` and `y = y_0(t)`
    Then the general solution is expressed as

    .. math:: x = C_1 x_0(t) + C_2 x_0(t) \int \frac{g(t) F(t) P(t)}{x_0^{2}(t)} \,dt

    .. math:: y = C_1 y_0(t) + C_2 [\frac{F(t) P(t)}{x_0(t)} + y_0(t) \int \frac{g(t) F(t) P(t)}{x_0^{2}(t)} \,dt]

    where C1 and C2 are arbitrary constants and

    .. math:: F(t) = e^{\int f(t) \,dt} , P(t) = e^{\int p(t) \,dt}

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    e1 = r['a']*r['b']*r['c'] - r['b']**2*r['c'] + r['a']*diff(r['b'],t) - diff(r['a'],t)*r['b']
    e2 = r['a']*r['c']*r['d'] - r['b']*r['c']**2 + diff(r['c'],t)*r['d'] - r['c']*diff(r['d'],t)
    m1 = r['a']*r['b'] + r['b']*r['d'] + diff(r['b'],t)
    m2 = r['a']*r['c'] + r['c']*r['d'] + diff(r['c'],t)
    if e1 == 0:
        sol1 = dsolve(r['b']*diff(x(t),t,t) - m1*diff(x(t),t)).rhs
        sol2 = dsolve(diff(y(t),t) - r['c']*sol1 - r['d']*y(t)).rhs
    elif e2 == 0:
        sol2 = dsolve(r['c']*diff(y(t),t,t) - m2*diff(y(t),t)).rhs
        sol1 = dsolve(diff(x(t),t) - r['a']*x(t) - r['b']*sol2).rhs
    elif not (e1/r['b']).has(t) and not (m1/r['b']).has(t):
        sol1 = dsolve(diff(x(t),t,t) - (m1/r['b'])*diff(x(t),t) - (e1/r['b'])*x(t)).rhs
        sol2 = dsolve(diff(y(t),t) - r['c']*sol1 - r['d']*y(t)).rhs
    elif not (e2/r['c']).has(t) and not (m2/r['c']).has(t):
        sol2 = dsolve(diff(y(t),t,t) - (m2/r['c'])*diff(y(t),t) - (e2/r['c'])*y(t)).rhs
        sol1 = dsolve(diff(x(t),t) - r['a']*x(t) - r['b']*sol2).rhs
    else:
        x0 = Function('x0')(t)    # x0 and y0 being particular solutions
        y0 = Function('y0')(t)
        F = exp(Integral(r['a'],t))
        P = exp(Integral(r['d'],t))
        sol1 = C1*x0 + C2*x0*Integral(r['b']*F*P/x0**2, t)
        sol2 = C1*y0 + C2*(F*P/x0 + y0*Integral(r['b']*F*P/x0**2, t))
    return [Eq(x(t), sol1), Eq(y(t), sol2)]


def sysode_linear_2eq_order2(match_):
    x = match_['func'][0].func
    y = match_['func'][1].func
    func = match_['func']
    fc = match_['func_coeff']
    eq = match_['eq']
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    r = dict()
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    for i in range(2):
        eqs = []
        for terms in Add.make_args(eq[i]):
            eqs.append(terms/fc[i,func[i],2])
        eq[i] = Add(*eqs)
    # for equations Eq(diff(x(t),t,t), a1*diff(x(t),t)+b1*diff(y(t),t)+c1*x(t)+d1*y(t)+e1)
    # and Eq(a2*diff(y(t),t,t), a2*diff(x(t),t)+b2*diff(y(t),t)+c2*x(t)+d2*y(t)+e2)
    r['a1'] = -fc[0,x(t),1]/fc[0,x(t),2] ; r['a2'] = -fc[1,x(t),1]/fc[1,y(t),2]
    r['b1'] = -fc[0,y(t),1]/fc[0,x(t),2] ; r['b2'] = -fc[1,y(t),1]/fc[1,y(t),2]
    r['c1'] = -fc[0,x(t),0]/fc[0,x(t),2] ; r['c2'] = -fc[1,x(t),0]/fc[1,y(t),2]
    r['d1'] = -fc[0,y(t),0]/fc[0,x(t),2] ; r['d2'] = -fc[1,y(t),0]/fc[1,y(t),2]
    const = [S(0), S(0)]
    for i in range(2):
        for j in Add.make_args(eq[i]):
            if not (j.has(x(t)) or j.has(y(t))):
                const[i] += j
    r['e1'] = -const[0]
    r['e2'] = -const[1]
    if match_['type_of_equation'] == 'type1':
        sol = _linear_2eq_order2_type1(x, y, t, r, eq)
    elif match_['type_of_equation'] == 'type2':
        gsol = _linear_2eq_order2_type1(x, y, t, r, eq)
        psol = _linear_2eq_order2_type2(x, y, t, r, eq)
        sol = [Eq(x(t), gsol[0].rhs+psol[0]), Eq(y(t), gsol[1].rhs+psol[1])]
    elif match_['type_of_equation'] == 'type3':
        sol = _linear_2eq_order2_type3(x, y, t, r, eq)
    elif match_['type_of_equation'] == 'type4':
        sol = _linear_2eq_order2_type4(x, y, t, r, eq)
    elif match_['type_of_equation'] == 'type5':
        sol = _linear_2eq_order2_type5(x, y, t, r, eq)
    elif match_['type_of_equation'] == 'type6':
        sol = _linear_2eq_order2_type6(x, y, t, r, eq)
    elif match_['type_of_equation'] == 'type7':
        sol = _linear_2eq_order2_type7(x, y, t, r, eq)
    elif match_['type_of_equation'] == 'type8':
        sol = _linear_2eq_order2_type8(x, y, t, r, eq)
    elif match_['type_of_equation'] == 'type9':
        sol = _linear_2eq_order2_type9(x, y, t, r, eq)
    elif match_['type_of_equation'] == 'type10':
        sol = _linear_2eq_order2_type10(x, y, t, r, eq)
    elif match_['type_of_equation'] == 'type11':
        sol = _linear_2eq_order2_type11(x, y, t, r, eq)
    return sol

def _linear_2eq_order2_type1(x, y, t, r, eq):
    r"""
    System of two constant-coefficient second-order linear homogeneous differential equations

    .. math:: x'' = ax + by

    .. math:: y'' = cx + dy

    The characteristic equation for above equations

    .. math:: \lambda^4 - (a + d) \lambda^2 + ad - bc = 0

    whose discriminant is `D = (a - d)^2 + 4bc \neq 0`

    1. When `ad - bc \neq 0`

    1.1. If `D \neq 0`. The characteristic equation has four distinct roots, `\lambda_1, \lambda_2, \lambda_3, \lambda_4`.
    The general solution of the system is

    .. math:: x = C_1 b e^{\lambda_1 t} + C_2 b e^{\lambda_2 t} + C_3 b e^{\lambda_3 t} + C_4 b e^{\lambda_4 t}

    .. math:: y = C_1 (\lambda_1^{2} - a) e^{\lambda_1 t} + C_2 (\lambda_2^{2} - a) e^{\lambda_2 t} + C_3 (\lambda_3^{2} - a) e^{\lambda_3 t} + C_4 (\lambda_4^{2} - a) e^{\lambda_4 t}

    where `C_1,..., C_4` are arbitrary constants.

    1.2. If `D = 0` and `a \neq d`:

    .. math:: x = 2 C_1 (bt + \frac{2bk}{a - d}) e^{\frac{kt}{2}} + 2 C_2 (bt + \frac{2bk}{a - d}) e^{\frac{-kt}{2}} + 2b C_3 t e^{\frac{kt}{2}} + 2b C_4 t e^{\frac{-kt}{2}}

    .. math:: y = C_1 (d - a) t e^{\frac{kt}{2}} + C_2 (d - a) t e^{\frac{-kt}{2}} + C_3 [(d - a) t + 2k] e^{\frac{kt}{2}} + C_4 [(d - a) t - 2k] e^{\frac{-kt}{2}}

    where `C_1,..., C_4` are arbitrary constants and `k = \sqrt{2 (a + d)}`

    1.3. If `D = 0` and `a = d \neq 0` and `b = 0`:

    .. math:: x = 2 \sqrt{a} C_1 e^{\sqrt{a} t} + 2 \sqrt{a} C_2 e^{-\sqrt{a} t}

    .. math:: y = c C_1 t e^{\sqrt{a} t} - c C_2 t e^{-\sqrt{a} t} + C_3 e^{\sqrt{a} t} + C_4 e^{-\sqrt{a} t}

    1.4. If `D = 0` and `a = d \neq 0` and `c = 0`:

    .. math:: x = b C_1 t e^{\sqrt{a} t} - b C_2 t e^{-\sqrt{a} t} + C_3 e^{\sqrt{a} t} + C_4 e^{-\sqrt{a} t}

    .. math:: y = 2 \sqrt{a} C_1 e^{\sqrt{a} t} + 2 \sqrt{a} C_2 e^{-\sqrt{a} t}

    2. When `ad - bc = 0` and `a^2 + b^2 > 0`. Then the original system becomes

    .. math:: x'' = ax + by

    .. math:: y'' = k (ax + by)

    2.1. If `a + bk \neq 0`:

    .. math:: x = C_1 e^{t \sqrt{a + bk}} + C_2 e^{-t \sqrt{a + bk}} + C_3 bt + C_4 b

    .. math:: y = C_1 k e^{t \sqrt{a + bk}} + C_2 k e^{-t \sqrt{a + bk}} - C_3 at - C_4 a

    2.2. If `a + bk = 0`:

    .. math:: x = C_1 b t^3 + C_2 b t^2 + C_3 t + C_4

    .. math:: y = kx + 6 C_1 t + 2 C_2

    """
    r['a'] = r['c1']
    r['b'] = r['d1']
    r['c'] = r['c2']
    r['d'] = r['d2']
    l = Symbol('l')
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    chara_eq = l**4 - (r['a']+r['d'])*l**2 + r['a']*r['d'] - r['b']*r['c']
    l1 = rootof(chara_eq, 0)
    l2 = rootof(chara_eq, 1)
    l3 = rootof(chara_eq, 2)
    l4 = rootof(chara_eq, 3)
    D = (r['a'] - r['d'])**2 + 4*r['b']*r['c']
    if (r['a']*r['d'] - r['b']*r['c']) != 0:
        if D != 0:
            gsol1 = C1*r['b']*exp(l1*t) + C2*r['b']*exp(l2*t) + C3*r['b']*exp(l3*t) \
            + C4*r['b']*exp(l4*t)
            gsol2 = C1*(l1**2-r['a'])*exp(l1*t) + C2*(l2**2-r['a'])*exp(l2*t) + \
            C3*(l3**2-r['a'])*exp(l3*t) + C4*(l4**2-r['a'])*exp(l4*t)
        else:
            if r['a'] != r['d']:
                k = sqrt(2*(r['a']+r['d']))
                mid = r['b']*t+2*r['b']*k/(r['a']-r['d'])
                gsol1 = 2*C1*mid*exp(k*t/2) + 2*C2*mid*exp(-k*t/2) + \
                2*r['b']*C3*t*exp(k*t/2) + 2*r['b']*C4*t*exp(-k*t/2)
                gsol2 = C1*(r['d']-r['a'])*t*exp(k*t/2) + C2*(r['d']-r['a'])*t*exp(-k*t/2) + \
                C3*((r['d']-r['a'])*t+2*k)*exp(k*t/2) + C4*((r['d']-r['a'])*t-2*k)*exp(-k*t/2)
            elif r['a'] == r['d'] != 0 and r['b'] == 0:
                sa = sqrt(r['a'])
                gsol1 = 2*sa*C1*exp(sa*t) + 2*sa*C2*exp(-sa*t)
                gsol2 = r['c']*C1*t*exp(sa*t)-r['c']*C2*t*exp(-sa*t)+C3*exp(sa*t)+C4*exp(-sa*t)
            elif r['a'] == r['d'] != 0 and r['c'] == 0:
                sa = sqrt(r['a'])
                gsol1 = r['b']*C1*t*exp(sa*t)-r['b']*C2*t*exp(-sa*t)+C3*exp(sa*t)+C4*exp(-sa*t)
                gsol2 = 2*sa*C1*exp(sa*t) + 2*sa*C2*exp(-sa*t)
    elif (r['a']*r['d'] - r['b']*r['c']) == 0 and (r['a']**2 + r['b']**2) > 0:
        k = r['c']/r['a']
        if r['a'] + r['b']*k != 0:
            mid = sqrt(r['a'] + r['b']*k)
            gsol1 = C1*exp(mid*t) + C2*exp(-mid*t) + C3*r['b']*t + C4*r['b']
            gsol2 = C1*k*exp(mid*t) + C2*k*exp(-mid*t) - C3*r['a']*t - C4*r['a']
        else:
            gsol1 = C1*r['b']*t**3 + C2*r['b']*t**2 + C3*t + C4
            gsol2 = k*gsol1 + 6*C1*t + 2*C2
    return [Eq(x(t), gsol1), Eq(y(t), gsol2)]

def _linear_2eq_order2_type2(x, y, t, r, eq):
    r"""
    The equations in this type are

    .. math:: x'' = a_1 x + b_1 y + c_1

    .. math:: y'' = a_2 x + b_2 y + c_2

    The general solution of this system is given by the sum of its particular solution
    and the general solution of the homogeneous system. The general solution is given
    by the linear system of 2 equation of order 2 and type 1

    1. If `a_1 b_2 - a_2 b_1 \neq 0`. A particular solution will be `x = x_0` and `y = y_0`
    where the constants `x_0` and `y_0` are determined by solving the linear algebraic system

    .. math:: a_1 x_0 + b_1 y_0 + c_1 = 0, a_2 x_0 + b_2 y_0 + c_2 = 0

    2. If `a_1 b_2 - a_2 b_1 = 0` and `a_1^2 + b_1^2 > 0`. In this case, the system in question becomes

    .. math:: x'' = ax + by + c_1, y'' = k (ax + by) + c_2

    2.1. If `\sigma = a + bk \neq 0`, the particular solution will be

    .. math:: x = \frac{1}{2} b \sigma^{-1} (c_1 k - c_2) t^2 - \sigma^{-2} (a c_1 + b c_2)

    .. math:: y = kx + \frac{1}{2} (c_2 - c_1 k) t^2

    2.2. If `\sigma = a + bk = 0`, the particular solution will be

    .. math:: x = \frac{1}{24} b (c_2 - c_1 k) t^4 + \frac{1}{2} c_1 t^2

    .. math:: y = kx + \frac{1}{2} (c_2 - c_1 k) t^2

    """
    x0, y0 = symbols('x0, y0')
    if r['c1']*r['d2'] - r['c2']*r['d1'] != 0:
        sol = solve((r['c1']*x0+r['d1']*y0+r['e1'], r['c2']*x0+r['d2']*y0+r['e2']), x0, y0)
        psol = [sol[x0], sol[y0]]
    elif r['c1']*r['d2'] - r['c2']*r['d1'] == 0 and (r['c1']**2 + r['d1']**2) > 0:
        k = r['c2']/r['c1']
        sig = r['c1'] + r['d1']*k
        if sig != 0:
            psol1 = r['d1']*sig**-1*(r['e1']*k-r['e2'])*t**2/2 - \
            sig**-2*(r['c1']*r['e1']+r['d1']*r['e2'])
            psol2 = k*psol1  + (r['e2'] - r['e1']*k)*t**2/2
            psol = [psol1, psol2]
        else:
            psol1 = r['d1']*(r['e2']-r['e1']*k)*t**4/24 + r['e1']*t**2/2
            psol2 = k*psol1 + (r['e2']-r['e1']*k)*t**2/2
            psol = [psol1, psol2]
    return psol

def _linear_2eq_order2_type3(x, y, t, r, eq):
    r"""
    These type of equation is used for describing the horizontal motion of a pendulum
    taking into account the Earth rotation.
    The solution is given with `a^2 + 4b > 0`:

    .. math:: x = C_1 \cos(\alpha t) + C_2 \sin(\alpha t) + C_3 \cos(\beta t) + C_4 \sin(\beta t)

    .. math:: y = -C_1 \sin(\alpha t) + C_2 \cos(\alpha t) - C_3 \sin(\beta t) + C_4 \cos(\beta t)

    where `C_1,...,C_4` and

    .. math:: \alpha = \frac{1}{2} a + \frac{1}{2} \sqrt{a^2 + 4b}, \beta = \frac{1}{2} a - \frac{1}{2} \sqrt{a^2 + 4b}

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    if r['b1']**2 - 4*r['c1'] > 0:
        r['a'] = r['b1'] ; r['b'] = -r['c1']
        alpha = r['a']/2 + sqrt(r['a']**2 + 4*r['b'])/2
        beta = r['a']/2 - sqrt(r['a']**2 + 4*r['b'])/2
        sol1 = C1*cos(alpha*t) + C2*sin(alpha*t) + C3*cos(beta*t) + C4*sin(beta*t)
        sol2 = -C1*sin(alpha*t) + C2*cos(alpha*t) - C3*sin(beta*t) + C4*cos(beta*t)
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order2_type4(x, y, t, r, eq):
    r"""
    These equations are found in the theory of oscillations

    .. math:: x'' + a_1 x' + b_1 y' + c_1 x + d_1 y = k_1 e^{i \omega t}

    .. math:: y'' + a_2 x' + b_2 y' + c_2 x + d_2 y = k_2 e^{i \omega t}

    The general solution of this linear nonhomogeneous system of constant-coefficient
    differential equations is given by the sum of its particular solution and the
    general solution of the corresponding homogeneous system (with `k_1 = k_2 = 0`)

    1. A particular solution is obtained by the method of undetermined coefficients:

    .. math:: x = A_* e^{i \omega t}, y = B_* e^{i \omega t}

    On substituting these expressions into the original system of differential equations,
    one arrive at a linear nonhomogeneous system of algebraic equations for the
    coefficients `A` and `B`.

    2. The general solution of the homogeneous system of differential equations is determined
    by a linear combination of linearly independent particular solutions determined by
    the method of undetermined coefficients in the form of exponentials:

    .. math:: x = A e^{\lambda t}, y = B e^{\lambda t}

    On substituting these expressions into the original system and collecting the
    coefficients of the unknown `A` and `B`, one obtains

    .. math:: (\lambda^{2} + a_1 \lambda + c_1) A + (b_1 \lambda + d_1) B = 0

    .. math:: (a_2 \lambda + c_2) A + (\lambda^{2} + b_2 \lambda + d_2) B = 0

    The determinant of this system must vanish for nontrivial solutions A, B to exist.
    This requirement results in the following characteristic equation for `\lambda`

    .. math:: (\lambda^2 + a_1 \lambda + c_1) (\lambda^2 + b_2 \lambda + d_2) - (b_1 \lambda + d_1) (a_2 \lambda + c_2) = 0

    If all roots `k_1,...,k_4` of this equation are distinct, the general solution of the original
    system of the differential equations has the form

    .. math:: x = C_1 (b_1 \lambda_1 + d_1) e^{\lambda_1 t} - C_2 (b_1 \lambda_2 + d_1) e^{\lambda_2 t} - C_3 (b_1 \lambda_3 + d_1) e^{\lambda_3 t} - C_4 (b_1 \lambda_4 + d_1) e^{\lambda_4 t}

    .. math:: y = C_1 (\lambda_1^{2} + a_1 \lambda_1 + c_1) e^{\lambda_1 t} + C_2 (\lambda_2^{2} + a_1 \lambda_2 + c_1) e^{\lambda_2 t} + C_3 (\lambda_3^{2} + a_1 \lambda_3 + c_1) e^{\lambda_3 t} + C_4 (\lambda_4^{2} + a_1 \lambda_4 + c_1) e^{\lambda_4 t}

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    k = Symbol('k')
    Ra, Ca, Rb, Cb = symbols('Ra, Ca, Rb, Cb')
    a1 = r['a1'] ; a2 = r['a2']
    b1 = r['b1'] ; b2 = r['b2']
    c1 = r['c1'] ; c2 = r['c2']
    d1 = r['d1'] ; d2 = r['d2']
    k1 = r['e1'].expand().as_independent(t)[0]
    k2 = r['e2'].expand().as_independent(t)[0]
    ew1 = r['e1'].expand().as_independent(t)[1]
    ew2 = powdenest(ew1).as_base_exp()[1]
    ew3 = collect(ew2, t).coeff(t)
    w = cancel(ew3/I)
    # The particular solution is assumed to be (Ra+I*Ca)*exp(I*w*t) and
    # (Rb+I*Cb)*exp(I*w*t) for x(t) and y(t) respectively
    peq1 = (-w**2+c1)*Ra - a1*w*Ca + d1*Rb - b1*w*Cb - k1
    peq2 = a1*w*Ra + (-w**2+c1)*Ca + b1*w*Rb + d1*Cb
    peq3 = c2*Ra - a2*w*Ca + (-w**2+d2)*Rb - b2*w*Cb - k2
    peq4 = a2*w*Ra + c2*Ca + b2*w*Rb + (-w**2+d2)*Cb
    # FIXME: solve for what in what?  Ra, Rb, etc I guess
    # but then psol not used for anything?
    psol = solve([peq1, peq2, peq3, peq4])

    chareq = (k**2+a1*k+c1)*(k**2+b2*k+d2) - (b1*k+d1)*(a2*k+c2)
    [k1, k2, k3, k4] = roots_quartic(Poly(chareq))
    sol1 = -C1*(b1*k1+d1)*exp(k1*t) - C2*(b1*k2+d1)*exp(k2*t) - \
    C3*(b1*k3+d1)*exp(k3*t) - C4*(b1*k4+d1)*exp(k4*t) + (Ra+I*Ca)*exp(I*w*t)

    a1_ = (a1-1)
    sol2 = C1*(k1**2+a1_*k1+c1)*exp(k1*t) + C2*(k2**2+a1_*k2+c1)*exp(k2*t) + \
    C3*(k3**2+a1_*k3+c1)*exp(k3*t) + C4*(k4**2+a1_*k4+c1)*exp(k4*t) + (Rb+I*Cb)*exp(I*w*t)
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order2_type5(x, y, t, r, eq):
    r"""
    The equation which come under this category are

    .. math:: x'' = a (t y' - y)

    .. math:: y'' = b (t x' - x)

    The transformation

    .. math:: u = t x' - x, b = t y' - y

    leads to the first-order system

    .. math:: u' = atv, v' = btu

    The general solution of this system is given by

    If `ab > 0`:

    .. math:: u = C_1 a e^{\frac{1}{2} \sqrt{ab} t^2} + C_2 a e^{-\frac{1}{2} \sqrt{ab} t^2}

    .. math:: v = C_1 \sqrt{ab} e^{\frac{1}{2} \sqrt{ab} t^2} - C_2 \sqrt{ab} e^{-\frac{1}{2} \sqrt{ab} t^2}

    If `ab < 0`:

    .. math:: u = C_1 a \cos(\frac{1}{2} \sqrt{\left|ab\right|} t^2) + C_2 a \sin(-\frac{1}{2} \sqrt{\left|ab\right|} t^2)

    .. math:: v = C_1 \sqrt{\left|ab\right|} \sin(\frac{1}{2} \sqrt{\left|ab\right|} t^2) + C_2 \sqrt{\left|ab\right|} \cos(-\frac{1}{2} \sqrt{\left|ab\right|} t^2)

    where `C_1` and `C_2` are arbitrary constants. On substituting the value of `u` and `v`
    in above equations and integrating the resulting expressions, the general solution will become

    .. math:: x = C_3 t + t \int \frac{u}{t^2} \,dt, y = C_4 t + t \int \frac{u}{t^2} \,dt

    where `C_3` and `C_4` are arbitrary constants.

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    r['a'] = -r['d1'] ; r['b'] = -r['c2']
    mul = sqrt(abs(r['a']*r['b']))
    if r['a']*r['b'] > 0:
        u = C1*r['a']*exp(mul*t**2/2) + C2*r['a']*exp(-mul*t**2/2)
        v = C1*mul*exp(mul*t**2/2) - C2*mul*exp(-mul*t**2/2)
    else:
        u = C1*r['a']*cos(mul*t**2/2) + C2*r['a']*sin(mul*t**2/2)
        v = -C1*mul*sin(mul*t**2/2) + C2*mul*cos(mul*t**2/2)
    sol1 = C3*t + t*Integral(u/t**2, t)
    sol2 = C4*t + t*Integral(v/t**2, t)
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order2_type6(x, y, t, r, eq):
    r"""
    The equations are

    .. math:: x'' = f(t) (a_1 x + b_1 y)

    .. math:: y'' = f(t) (a_2 x + b_2 y)

    If `k_1` and `k_2` are roots of the quadratic equation

    .. math:: k^2 - (a_1 + b_2) k + a_1 b_2 - a_2 b_1 = 0

    Then by multiplying appropriate constants and adding together original equations
    we obtain two independent equations:

    .. math:: z_1'' = k_1 f(t) z_1, z_1 = a_2 x + (k_1 - a_1) y

    .. math:: z_2'' = k_2 f(t) z_2, z_2 = a_2 x + (k_2 - a_1) y

    Solving the equations will give the values of `x` and `y` after obtaining the value
    of `z_1` and `z_2` by solving the differential equation and substituting the result.

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    k = Symbol('k')
    z = Function('z')
    num, den = cancel(
        (r['c1']*x(t) + r['d1']*y(t))/
        (r['c2']*x(t) + r['d2']*y(t))).as_numer_denom()
    f = r['c1']/num.coeff(x(t))
    a1 = num.coeff(x(t))
    b1 = num.coeff(y(t))
    a2 = den.coeff(x(t))
    b2 = den.coeff(y(t))
    chareq = k**2 - (a1 + b2)*k + a1*b2 - a2*b1
    k1, k2 = [rootof(chareq, k) for k in range(Poly(chareq).degree())]
    z1 = dsolve(diff(z(t),t,t) - k1*f*z(t)).rhs
    z2 = dsolve(diff(z(t),t,t) - k2*f*z(t)).rhs
    sol1 = (k1*z2 - k2*z1 + a1*(z1 - z2))/(a2*(k1-k2))
    sol2 = (z1 - z2)/(k1 - k2)
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order2_type7(x, y, t, r, eq):
    r"""
    The equations are given as

    .. math:: x'' = f(t) (a_1 x' + b_1 y')

    .. math:: y'' = f(t) (a_2 x' + b_2 y')

    If `k_1` and 'k_2` are roots of the quadratic equation

    .. math:: k^2 - (a_1 + b_2) k + a_1 b_2 - a_2 b_1 = 0

    Then the system can be reduced by adding together the two equations multiplied
    by appropriate constants give following two independent equations:

    .. math:: z_1'' = k_1 f(t) z_1', z_1 = a_2 x + (k_1 - a_1) y

    .. math:: z_2'' = k_2 f(t) z_2', z_2 = a_2 x + (k_2 - a_1) y

    Integrating these and returning to the original variables, one arrives at a linear
    algebraic system for the unknowns `x` and `y`:

    .. math:: a_2 x + (k_1 - a_1) y = C_1 \int e^{k_1 F(t)} \,dt + C_2

    .. math:: a_2 x + (k_2 - a_1) y = C_3 \int e^{k_2 F(t)} \,dt + C_4

    where `C_1,...,C_4` are arbitrary constants and `F(t) = \int f(t) \,dt`

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    k = Symbol('k')
    num, den = cancel(
        (r['a1']*x(t) + r['b1']*y(t))/
        (r['a2']*x(t) + r['b2']*y(t))).as_numer_denom()
    f = r['a1']/num.coeff(x(t))
    a1 = num.coeff(x(t))
    b1 = num.coeff(y(t))
    a2 = den.coeff(x(t))
    b2 = den.coeff(y(t))
    chareq = k**2 - (a1 + b2)*k + a1*b2 - a2*b1
    [k1, k2] = [rootof(chareq, k) for k in range(Poly(chareq).degree())]
    F = Integral(f, t)
    z1 = C1*Integral(exp(k1*F), t) + C2
    z2 = C3*Integral(exp(k2*F), t) + C4
    sol1 = (k1*z2 - k2*z1 + a1*(z1 - z2))/(a2*(k1-k2))
    sol2 = (z1 - z2)/(k1 - k2)
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order2_type8(x, y, t, r, eq):
    r"""
    The equation of this category are

    .. math:: x'' = a f(t) (t y' - y)

    .. math:: y'' = b f(t) (t x' - x)

    The transformation

    .. math:: u = t x' - x, v = t y' - y

    leads to the system of first-order equations

    .. math:: u' = a t f(t) v, v' = b t f(t) u

    The general solution of this system has the form

    If `ab > 0`:

    .. math:: u = C_1 a e^{\sqrt{ab} \int t f(t) \,dt} + C_2 a e^{-\sqrt{ab} \int t f(t) \,dt}

    .. math:: v = C_1 \sqrt{ab} e^{\sqrt{ab} \int t f(t) \,dt} - C_2 \sqrt{ab} e^{-\sqrt{ab} \int t f(t) \,dt}

    If `ab < 0`:

    .. math:: u = C_1 a \cos(\sqrt{\left|ab\right|} \int t f(t) \,dt) + C_2 a \sin(-\sqrt{\left|ab\right|} \int t f(t) \,dt)

    .. math:: v = C_1 \sqrt{\left|ab\right|} \sin(\sqrt{\left|ab\right|} \int t f(t) \,dt) + C_2 \sqrt{\left|ab\right|} \cos(-\sqrt{\left|ab\right|} \int t f(t) \,dt)

    where `C_1` and `C_2` are arbitrary constants. On substituting the value of `u` and `v`
    in above equations and integrating the resulting expressions, the general solution will become

    .. math:: x = C_3 t + t \int \frac{u}{t^2} \,dt, y = C_4 t + t \int \frac{u}{t^2} \,dt

    where `C_3` and `C_4` are arbitrary constants.

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    num, den = cancel(r['d1']/r['c2']).as_numer_denom()
    f = -r['d1']/num
    a = num
    b = den
    mul = sqrt(abs(a*b))
    Igral = Integral(t*f, t)
    if a*b > 0:
        u = C1*a*exp(mul*Igral) + C2*a*exp(-mul*Igral)
        v = C1*mul*exp(mul*Igral) - C2*mul*exp(-mul*Igral)
    else:
        u = C1*a*cos(mul*Igral) + C2*a*sin(mul*Igral)
        v = -C1*mul*sin(mul*Igral) + C2*mul*cos(mul*Igral)
    sol1 = C3*t + t*Integral(u/t**2, t)
    sol2 = C4*t + t*Integral(v/t**2, t)
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order2_type9(x, y, t, r, eq):
    r"""
    .. math:: t^2 x'' + a_1 t x' + b_1 t y' + c_1 x + d_1 y = 0

    .. math:: t^2 y'' + a_2 t x' + b_2 t y' + c_2 x + d_2 y = 0

    These system of equations are euler type.

    The substitution of `t = \sigma e^{\tau} (\sigma \neq 0)` leads to the system of constant
    coefficient linear differential equations

    .. math:: x'' + (a_1 - 1) x' + b_1 y' + c_1 x + d_1 y = 0

    .. math:: y'' + a_2 x' + (b_2 - 1) y' + c_2 x + d_2 y = 0

    The general solution of the homogeneous system of differential equations is determined
    by a linear combination of linearly independent particular solutions determined by
    the method of undetermined coefficients in the form of exponentials

    .. math:: x = A e^{\lambda t}, y = B e^{\lambda t}

    On substituting these expressions into the original system and collecting the
    coefficients of the unknown `A` and `B`, one obtains

    .. math:: (\lambda^{2} + (a_1 - 1) \lambda + c_1) A + (b_1 \lambda + d_1) B = 0

    .. math:: (a_2 \lambda + c_2) A + (\lambda^{2} + (b_2 - 1) \lambda + d_2) B = 0

    The determinant of this system must vanish for nontrivial solutions A, B to exist.
    This requirement results in the following characteristic equation for `\lambda`

    .. math:: (\lambda^2 + (a_1 - 1) \lambda + c_1) (\lambda^2 + (b_2 - 1) \lambda + d_2) - (b_1 \lambda + d_1) (a_2 \lambda + c_2) = 0

    If all roots `k_1,...,k_4` of this equation are distinct, the general solution of the original
    system of the differential equations has the form

    .. math:: x = C_1 (b_1 \lambda_1 + d_1) e^{\lambda_1 t} - C_2 (b_1 \lambda_2 + d_1) e^{\lambda_2 t} - C_3 (b_1 \lambda_3 + d_1) e^{\lambda_3 t} - C_4 (b_1 \lambda_4 + d_1) e^{\lambda_4 t}

    .. math:: y = C_1 (\lambda_1^{2} + (a_1 - 1) \lambda_1 + c_1) e^{\lambda_1 t} + C_2 (\lambda_2^{2} + (a_1 - 1) \lambda_2 + c_1) e^{\lambda_2 t} + C_3 (\lambda_3^{2} + (a_1 - 1) \lambda_3 + c_1) e^{\lambda_3 t} + C_4 (\lambda_4^{2} + (a_1 - 1) \lambda_4 + c_1) e^{\lambda_4 t}

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    k = Symbol('k')
    a1 = -r['a1']*t; a2 = -r['a2']*t
    b1 = -r['b1']*t; b2 = -r['b2']*t
    c1 = -r['c1']*t**2; c2 = -r['c2']*t**2
    d1 = -r['d1']*t**2; d2 = -r['d2']*t**2
    eq = (k**2+(a1-1)*k+c1)*(k**2+(b2-1)*k+d2)-(b1*k+d1)*(a2*k+c2)
    [k1, k2, k3, k4] = roots_quartic(Poly(eq))
    sol1 = -C1*(b1*k1+d1)*exp(k1*log(t)) - C2*(b1*k2+d1)*exp(k2*log(t)) - \
    C3*(b1*k3+d1)*exp(k3*log(t)) - C4*(b1*k4+d1)*exp(k4*log(t))

    a1_ = (a1-1)
    sol2 = C1*(k1**2+a1_*k1+c1)*exp(k1*log(t)) + C2*(k2**2+a1_*k2+c1)*exp(k2*log(t)) \
    + C3*(k3**2+a1_*k3+c1)*exp(k3*log(t)) + C4*(k4**2+a1_*k4+c1)*exp(k4*log(t))

    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order2_type10(x, y, t, r, eq):
    r"""
    The equation of this category are

    .. math:: (\alpha t^2 + \beta t + \gamma)^{2} x'' = ax + by

    .. math:: (\alpha t^2 + \beta t + \gamma)^{2} y'' = cx + dy

    The transformation

    .. math:: \tau = \int \frac{1}{\alpha t^2 + \beta t + \gamma} \,dt , u = \frac{x}{\sqrt{\left|\alpha t^2 + \beta t + \gamma\right|}} , v = \frac{y}{\sqrt{\left|\alpha t^2 + \beta t + \gamma\right|}}

    leads to a constant coefficient linear system of equations

    .. math:: u'' = (a - \alpha \gamma + \frac{1}{4} \beta^{2}) u + b v

    .. math:: v'' = c u + (d - \alpha \gamma + \frac{1}{4} \beta^{2}) v

    These system of equations obtained can be solved by type1 of System of two
    constant-coefficient second-order linear homogeneous differential equations.

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    u, v = symbols('u, v', cls=Function)
    assert False
    T = Symbol('T')
    p = Wild('p', exclude=[t, t**2])
    q = Wild('q', exclude=[t, t**2])
    s = Wild('s', exclude=[t, t**2])
    n = Wild('n', exclude=[t, t**2])
    num, den = r['c1'].as_numer_denom()
    dic = den.match((n*(p*t**2+q*t+s)**2).expand())
    eqz = dic[p]*t**2 + dic[q]*t + dic[s]
    a = num/dic[n]
    b = cancel(r['d1']*eqz**2)
    c = cancel(r['c2']*eqz**2)
    d = cancel(r['d2']*eqz**2)
    [msol1, msol2] = dsolve([Eq(diff(u(t), t, t), (a - dic[p]*dic[s] + dic[q]**2/4)*u(t) \
    + b*v(t)), Eq(diff(v(t),t,t), c*u(t) + (d - dic[p]*dic[s] + dic[q]**2/4)*v(t))])
    sol1 = (msol1.rhs*sqrt(abs(eqz))).subs(t, Integral(1/eqz, t))
    sol2 = (msol2.rhs*sqrt(abs(eqz))).subs(t, Integral(1/eqz, t))
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def _linear_2eq_order2_type11(x, y, t, r, eq):
    r"""
    The equations which comes under this type are

    .. math:: x'' = f(t) (t x' - x) + g(t) (t y' - y)

    .. math:: y'' = h(t) (t x' - x) + p(t) (t y' - y)

    The transformation

    .. math:: u = t x' - x, v = t y' - y

    leads to the linear system of first-order equations

    .. math:: u' = t f(t) u + t g(t) v, v' = t h(t) u + t p(t) v

    On substituting the value of `u` and `v` in transformed equation gives value of `x` and `y` as

    .. math:: x = C_3 t + t \int \frac{u}{t^2} \,dt , y = C_4 t + t \int \frac{v}{t^2} \,dt.

    where `C_3` and `C_4` are arbitrary constants.

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    u, v = symbols('u, v', cls=Function)
    f = -r['c1'] ; g = -r['d1']
    h = -r['c2'] ; p = -r['d2']
    [msol1, msol2] = dsolve([Eq(diff(u(t),t), t*f*u(t) + t*g*v(t)), Eq(diff(v(t),t), t*h*u(t) + t*p*v(t))])
    sol1 = C3*t + t*Integral(msol1.rhs/t**2, t)
    sol2 = C4*t + t*Integral(msol2.rhs/t**2, t)
    return [Eq(x(t), sol1), Eq(y(t), sol2)]

def sysode_linear_3eq_order1(match_):
    x = match_['func'][0].func
    y = match_['func'][1].func
    z = match_['func'][2].func
    func = match_['func']
    fc = match_['func_coeff']
    eq = match_['eq']
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    r = dict()
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    for i in range(3):
        eqs = 0
        for terms in Add.make_args(eq[i]):
            eqs += terms/fc[i,func[i],1]
        eq[i] = eqs
    # for equations:
    #   Eq(g1*diff(x(t),t), a1*x(t)+b1*y(t)+c1*z(t)+d1),
    #   Eq(g2*diff(y(t),t), a2*x(t)+b2*y(t)+c2*z(t)+d2), and
    #   Eq(g3*diff(z(t),t), a3*x(t)+b3*y(t)+c3*z(t)+d3)
    r['a1'] = fc[0,x(t),0]/fc[0,x(t),1]; r['a2'] = fc[1,x(t),0]/fc[1,y(t),1];
    r['a3'] = fc[2,x(t),0]/fc[2,z(t),1]
    r['b1'] = fc[0,y(t),0]/fc[0,x(t),1]; r['b2'] = fc[1,y(t),0]/fc[1,y(t),1];
    r['b3'] = fc[2,y(t),0]/fc[2,z(t),1]
    r['c1'] = fc[0,z(t),0]/fc[0,x(t),1]; r['c2'] = fc[1,z(t),0]/fc[1,y(t),1];
    r['c3'] = fc[2,z(t),0]/fc[2,z(t),1]
    for i in range(3):
        for j in Add.make_args(eq[i]):
            if not j.has(x(t), y(t), z(t)):
                raise NotImplementedError("Only homogeneous problems are supported, non-homogenous are not supported currently.")
    if match_['type_of_equation'] == 'type1':
        sol = _linear_3eq_order1_type1(x, y, z, t, r, eq)
    if match_['type_of_equation'] == 'type2':
        sol = _linear_3eq_order1_type2(x, y, z, t, r, eq)
    if match_['type_of_equation'] == 'type3':
        sol = _linear_3eq_order1_type3(x, y, z, t, r, eq)
    if match_['type_of_equation'] == 'type4':
        sol = _linear_3eq_order1_type4(x, y, z, t, r, eq)
    if match_['type_of_equation'] == 'type6':
        sol = _linear_neq_order1_type1(match_)
    return sol

def _linear_3eq_order1_type1(x, y, z, t, r, eq):
    r"""
    .. math:: x' = ax

    .. math:: y' = bx + cy

    .. math:: z' = dx + ky + pz

    Solution of such equations are forward substitution. Solving first equations
    gives the value of `x`, substituting it in second and third equation and
    solving second equation gives `y` and similarly substituting `y` in third
    equation give `z`.

    .. math:: x = C_1 e^{at}

    .. math:: y = \frac{b C_1}{a - c} e^{at} + C_2 e^{ct}

    .. math:: z = \frac{C_1}{a - p} (d + \frac{bk}{a - c}) e^{at} + \frac{k C_2}{c - p} e^{ct} + C_3 e^{pt}

    where `C_1, C_2` and `C_3` are arbitrary constants.

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    a = -r['a1']; b = -r['a2']; c = -r['b2']
    d = -r['a3']; k = -r['b3']; p = -r['c3']
    sol1 = C1*exp(a*t)
    sol2 = b*C1*exp(a*t)/(a-c) + C2*exp(c*t)
    sol3 = C1*(d+b*k/(a-c))*exp(a*t)/(a-p) + k*C2*exp(c*t)/(c-p) + C3*exp(p*t)
    return [Eq(x(t), sol1), Eq(y(t), sol2), Eq(z(t), sol3)]

def _linear_3eq_order1_type2(x, y, z, t, r, eq):
    r"""
    The equations of this type are

    .. math:: x' = cy - bz

    .. math:: y' = az - cx

    .. math:: z' = bx - ay

    1. First integral:

    .. math:: ax + by + cz = A             \qquad - (1)

    .. math:: x^2 + y^2 + z^2 = B^2        \qquad - (2)

    where `A` and `B` are arbitrary constants. It follows from these integrals
    that the integral lines are circles formed by the intersection of the planes
    `(1)` and sphere `(2)`

    2. Solution:

    .. math:: x = a C_0 + k C_1 \cos(kt) + (c C_2 - b C_3) \sin(kt)

    .. math:: y = b C_0 + k C_2 \cos(kt) + (a C_2 - c C_3) \sin(kt)

    .. math:: z = c C_0 + k C_3 \cos(kt) + (b C_2 - a C_3) \sin(kt)

    where `k = \sqrt{a^2 + b^2 + c^2}` and the four constants of integration,
    `C_1,...,C_4` are constrained by a single relation,

    .. math:: a C_1 + b C_2 + c C_3 = 0

    """
    C0, C1, C2, C3 = get_numbered_constants(eq, num=4, start=0)
    a = -r['c2']; b = -r['a3']; c = -r['b1']
    k = sqrt(a**2 + b**2 + c**2)
    C3 = (-a*C1 - b*C2)/c
    sol1 = a*C0 + k*C1*cos(k*t) + (c*C2-b*C3)*sin(k*t)
    sol2 = b*C0 + k*C2*cos(k*t) + (a*C3-c*C1)*sin(k*t)
    sol3 = c*C0 + k*C3*cos(k*t) + (b*C1-a*C2)*sin(k*t)
    return [Eq(x(t), sol1), Eq(y(t), sol2), Eq(z(t), sol3)]

def _linear_3eq_order1_type3(x, y, z, t, r, eq):
    r"""
    Equations of this system of ODEs

    .. math:: a x' = bc (y - z)

    .. math:: b y' = ac (z - x)

    .. math:: c z' = ab (x - y)

    1. First integral:

    .. math:: a^2 x + b^2 y + c^2 z = A

    where A is an arbitrary constant. It follows that the integral lines are plane curves.

    2. Solution:

    .. math:: x = C_0 + k C_1 \cos(kt) + a^{-1} bc (C_2 - C_3) \sin(kt)

    .. math:: y = C_0 + k C_2 \cos(kt) + a b^{-1} c (C_3 - C_1) \sin(kt)

    .. math:: z = C_0 + k C_3 \cos(kt) + ab c^{-1} (C_1 - C_2) \sin(kt)

    where `k = \sqrt{a^2 + b^2 + c^2}` and the four constants of integration,
    `C_1,...,C_4` are constrained by a single relation

    .. math:: a^2 C_1 + b^2 C_2 + c^2 C_3 = 0

    """
    C0, C1, C2, C3 = get_numbered_constants(eq, num=4, start=0)
    c = sqrt(r['b1']*r['c2'])
    b = sqrt(r['b1']*r['a3'])
    a = sqrt(r['c2']*r['a3'])
    C3 = (-a**2*C1-b**2*C2)/c**2
    k = sqrt(a**2 + b**2 + c**2)
    sol1 = C0 + k*C1*cos(k*t) + a**-1*b*c*(C2-C3)*sin(k*t)
    sol2 = C0 + k*C2*cos(k*t) + a*b**-1*c*(C3-C1)*sin(k*t)
    sol3 = C0 + k*C3*cos(k*t) + a*b*c**-1*(C1-C2)*sin(k*t)
    return [Eq(x(t), sol1), Eq(y(t), sol2), Eq(z(t), sol3)]

def _linear_3eq_order1_type4(x, y, z, t, r, eq):
    r"""
    Equations:

    .. math:: x' = (a_1 f(t) + g(t)) x + a_2 f(t) y + a_3 f(t) z

    .. math:: y' = b_1 f(t) x + (b_2 f(t) + g(t)) y + b_3 f(t) z

    .. math:: z' = c_1 f(t) x + c_2 f(t) y + (c_3 f(t) + g(t)) z

    The transformation

    .. math:: x = e^{\int g(t) \,dt} u, y = e^{\int g(t) \,dt} v, z = e^{\int g(t) \,dt} w, \tau = \int f(t) \,dt

    leads to the system of constant coefficient linear differential equations

    .. math:: u' = a_1 u + a_2 v + a_3 w

    .. math:: v' = b_1 u + b_2 v + b_3 w

    .. math:: w' = c_1 u + c_2 v + c_3 w

    These system of equations are solved by homogeneous linear system of constant
    coefficients of `n` equations of first order. Then substituting the value of
    `u, v` and `w` in transformed equation gives value of `x, y` and `z`.

    """
    u, v, w = symbols('u, v, w', cls=Function)
    a2, a3 = cancel(r['b1']/r['c1']).as_numer_denom()
    f = cancel(r['b1']/a2)
    b1 = cancel(r['a2']/f); b3 = cancel(r['c2']/f)
    c1 = cancel(r['a3']/f); c2 = cancel(r['b3']/f)
    a1, g = div(r['a1'],f)
    b2 = div(r['b2'],f)[0]
    c3 = div(r['c3'],f)[0]
    trans_eq = (diff(u(t),t)-a1*u(t)-a2*v(t)-a3*w(t), diff(v(t),t)-b1*u(t)-\
    b2*v(t)-b3*w(t), diff(w(t),t)-c1*u(t)-c2*v(t)-c3*w(t))
    sol = dsolve(trans_eq)
    sol1 = exp(Integral(g,t))*((sol[0].rhs).subs(t, Integral(f,t)))
    sol2 = exp(Integral(g,t))*((sol[1].rhs).subs(t, Integral(f,t)))
    sol3 = exp(Integral(g,t))*((sol[2].rhs).subs(t, Integral(f,t)))
    return [Eq(x(t), sol1), Eq(y(t), sol2), Eq(z(t), sol3)]

def sysode_linear_neq_order1(match_):
    sol = _linear_neq_order1_type1(match_)
    return sol

def _linear_neq_order1_type1(match_):
    r"""
    System of n first-order constant-coefficient linear nonhomogeneous differential equation

    .. math:: y'_k = a_{k1} y_1 + a_{k2} y_2 +...+ a_{kn} y_n; k = 1,2,...,n

    or that can be written as `\vec{y'} = A . \vec{y}`
    where `\vec{y}` is matrix of `y_k` for `k = 1,2,...n` and `A` is a `n \times n` matrix.

    Since these equations are equivalent to a first order homogeneous linear
    differential equation. So the general solution will contain `n` linearly
    independent parts and solution will consist some type of exponential
    functions. Assuming `y = \vec{v} e^{rt}` is a solution of the system where
    `\vec{v}` is a vector of coefficients of `y_1,...,y_n`. Substituting `y` and
    `y' = r v e^{r t}` into the equation `\vec{y'} = A . \vec{y}`, we get

    .. math:: r \vec{v} e^{rt} = A \vec{v} e^{rt}

    .. math:: r \vec{v} = A \vec{v}

    where `r` comes out to be eigenvalue of `A` and vector `\vec{v}` is the eigenvector
    of `A` corresponding to `r`. There are three possibilities of eigenvalues of `A`

    - `n` distinct real eigenvalues
    - complex conjugate eigenvalues
    - eigenvalues with multiplicity `k`

    1. When all eigenvalues `r_1,..,r_n` are distinct with `n` different eigenvectors
    `v_1,...v_n` then the solution is given by

    .. math:: \vec{y} = C_1 e^{r_1 t} \vec{v_1} + C_2 e^{r_2 t} \vec{v_2} +...+ C_n e^{r_n t} \vec{v_n}

    where `C_1,C_2,...,C_n` are arbitrary constants.

    2. When some eigenvalues are complex then in order to make the solution real,
    we take a linear combination: if `r = a + bi` has an eigenvector
    `\vec{v} = \vec{w_1} + i \vec{w_2}` then to obtain real-valued solutions to
    the system, replace the complex-valued solutions `e^{rx} \vec{v}`
    with real-valued solution `e^{ax} (\vec{w_1} \cos(bx) - \vec{w_2} \sin(bx))`
    and for `r = a - bi` replace the solution `e^{-r x} \vec{v}` with
    `e^{ax} (\vec{w_1} \sin(bx) + \vec{w_2} \cos(bx))`

    3. If some eigenvalues are repeated. Then we get fewer than `n` linearly
    independent eigenvectors, we miss some of the solutions and need to
    construct the missing ones. We do this via generalized eigenvectors, vectors
    which are not eigenvectors but are close enough that we can use to write
    down the remaining solutions. For a eigenvalue `r` with eigenvector `\vec{w}`
    we obtain `\vec{w_2},...,\vec{w_k}` using

    .. math:: (A - r I) . \vec{w_2} = \vec{w}

    .. math:: (A - r I) . \vec{w_3} = \vec{w_2}

    .. math:: \vdots

    .. math:: (A - r I) . \vec{w_k} = \vec{w_{k-1}}

    Then the solutions to the system for the eigenspace are `e^{rt} [\vec{w}],
    e^{rt} [t \vec{w} + \vec{w_2}], e^{rt} [\frac{t^2}{2} \vec{w} + t \vec{w_2} + \vec{w_3}],
    ...,e^{rt} [\frac{t^{k-1}}{(k-1)!} \vec{w} + \frac{t^{k-2}}{(k-2)!} \vec{w_2} +...+ t \vec{w_{k-1}}
    + \vec{w_k}]`

    So, If `\vec{y_1},...,\vec{y_n}` are `n` solution of obtained from three
    categories of `A`, then general solution to the system `\vec{y'} = A . \vec{y}`

    .. math:: \vec{y} = C_1 \vec{y_1} + C_2 \vec{y_2} + \cdots + C_n \vec{y_n}

    """
    eq = match_['eq']
    func = match_['func']
    fc = match_['func_coeff']
    n = len(eq)
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    constants = numbered_symbols(prefix='C', cls=Symbol, start=1)
    M = Matrix(n,n,lambda i,j:-fc[i,func[j],0])
    evector = M.eigenvects(simplify=True)
    def is_complex(mat, root):
        return Matrix(n, 1, lambda i,j: re(mat[i])*cos(im(root)*t) - im(mat[i])*sin(im(root)*t))
    def is_complex_conjugate(mat, root):
        return Matrix(n, 1, lambda i,j: re(mat[i])*sin(abs(im(root))*t) + im(mat[i])*cos(im(root)*t)*abs(im(root))/im(root))
    conjugate_root = []
    e_vector = zeros(n,1)
    for evects in evector:
        if evects[0] not in conjugate_root:
            # If number of column of an eigenvector is not equal to the multiplicity
            # of its eigenvalue then the legt eigenvectors are calculated
            if len(evects[2])!=evects[1]:
                var_mat = Matrix(n, 1, lambda i,j: Symbol('x'+str(i)))
                Mnew = (M - evects[0]*eye(evects[2][-1].rows))*var_mat
                w = [0 for i in range(evects[1])]
                w[0] = evects[2][-1]
                for r in range(1, evects[1]):
                    w_ = Mnew - w[r-1]
                    sol_dict = solve(list(w_), var_mat[1:])
                    sol_dict[var_mat[0]] = var_mat[0]
                    for key, value in sol_dict.items():
                        sol_dict[key] = value.subs(var_mat[0],1)
                    w[r] = Matrix(n, 1, lambda i,j: sol_dict[var_mat[i]])
                    evects[2].append(w[r])
            for i in range(evects[1]):
                C = next(constants)
                for j in range(i+1):
                    if evects[0].has(I):
                        evects[2][j] = simplify(evects[2][j])
                        e_vector += C*is_complex(evects[2][j], evects[0])*t**(i-j)*exp(re(evects[0])*t)/factorial(i-j)
                        C = next(constants)
                        e_vector += C*is_complex_conjugate(evects[2][j], evects[0])*t**(i-j)*exp(re(evects[0])*t)/factorial(i-j)
                    else:
                        e_vector += C*evects[2][j]*t**(i-j)*exp(evects[0]*t)/factorial(i-j)
            if evects[0].has(I):
                conjugate_root.append(conjugate(evects[0]))
    sol = []
    for i in range(len(eq)):
        sol.append(Eq(func[i],e_vector[i]))
    return sol

def sysode_nonlinear_2eq_order1(match_):
    func = match_['func']
    eq = match_['eq']
    fc = match_['func_coeff']
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    if match_['type_of_equation'] == 'type5':
        sol = _nonlinear_2eq_order1_type5(func, t, eq)
        return sol
    x = func[0].func
    y = func[1].func
    for i in range(2):
        eqs = 0
        for terms in Add.make_args(eq[i]):
            eqs += terms/fc[i,func[i],1]
        eq[i] = eqs
    if match_['type_of_equation'] == 'type1':
        sol = _nonlinear_2eq_order1_type1(x, y, t, eq)
    elif match_['type_of_equation'] == 'type2':
        sol = _nonlinear_2eq_order1_type2(x, y, t, eq)
    elif match_['type_of_equation'] == 'type3':
        sol = _nonlinear_2eq_order1_type3(x, y, t, eq)
    elif match_['type_of_equation'] == 'type4':
        sol = _nonlinear_2eq_order1_type4(x, y, t, eq)
    return sol

def _nonlinear_2eq_order1_type1(x, y, t, eq):
    r"""
    Equations:

    .. math:: x' = x^n F(x,y)

    .. math:: y' = g(y) F(x,y)

    Solution:

    .. math:: x = \varphi(y), \int \frac{1}{g(y) F(\varphi(y),y)} \,dy = t + C_2

    where

    if `n \neq 1`

    .. math:: \varphi = [C_1 + (1-n) \int \frac{1}{g(y)} \,dy]^{\frac{1}{1-n}}

    if `n = 1`

    .. math:: \varphi = C_1 e^{\int \frac{1}{g(y)} \,dy}

    where `C_1` and `C_2` are arbitrary constants.

    """
    C1, C2 = get_numbered_constants(eq, num=2)
    n = Wild('n', exclude=[x(t),y(t)])
    f = Wild('f')
    u, v = symbols('u, v')
    r = eq[0].match(diff(x(t),t) - x(t)**n*f)
    g = ((diff(y(t),t) - eq[1])/r[f]).subs(y(t),v)
    F = r[f].subs(x(t),u).subs(y(t),v)
    n = r[n]
    if n!=1:
        phi = (C1 + (1-n)*Integral(1/g, v))**(1/(1-n))
    else:
        phi = C1*exp(Integral(1/g, v))
    phi = phi.doit()
    sol2 = solve(Integral(1/(g*F.subs(u,phi)), v).doit() - t - C2, v)
    sol = []
    for sols in sol2:
        sol.append(Eq(x(t),phi.subs(v, sols)))
        sol.append(Eq(y(t), sols))
    return sol

def _nonlinear_2eq_order1_type2(x, y, t, eq):
    r"""
    Equations:

    .. math:: x' = e^{\lambda x} F(x,y)

    .. math:: y' = g(y) F(x,y)

    Solution:

    .. math:: x = \varphi(y), \int \frac{1}{g(y) F(\varphi(y),y)} \,dy = t + C_2

    where

    if `\lambda \neq 0`

    .. math:: \varphi = -\frac{1}{\lambda} log(C_1 - \lambda \int \frac{1}{g(y)} \,dy)

    if `\lambda = 0`

    .. math:: \varphi = C_1 + \int \frac{1}{g(y)} \,dy

    where `C_1` and `C_2` are arbitrary constants.

    """
    C1, C2 = get_numbered_constants(eq, num=2)
    n = Wild('n', exclude=[x(t),y(t)])
    f = Wild('f')
    u, v = symbols('u, v')
    r = eq[0].match(diff(x(t),t) - exp(n*x(t))*f)
    g = ((diff(y(t),t) - eq[1])/r[f]).subs(y(t),v)
    F = r[f].subs(x(t),u).subs(y(t),v)
    n = r[n]
    if n:
        phi = -1/n*log(C1 - n*Integral(1/g, v))
    else:
        phi = C1 + Integral(1/g, v)
    phi = phi.doit()
    sol2 = solve(Integral(1/(g*F.subs(u,phi)), v).doit() - t - C2, v)
    sol = []
    for sols in sol2:
        sol.append(Eq(x(t),phi.subs(v, sols)))
        sol.append(Eq(y(t), sols))
    return sol

def _nonlinear_2eq_order1_type3(x, y, t, eq):
    r"""
    Autonomous system of general form

    .. math:: x' = F(x,y)

    .. math:: y' = G(x,y)

    Assuming `y = y(x, C_1)` where `C_1` is an arbitrary constant is the general
    solution of the first-order equation

    .. math:: F(x,y) y'_x = G(x,y)

    Then the general solution of the original system of equations has the form

    .. math:: \int \frac{1}{F(x,y(x,C_1))} \,dx = t + C_1

    """
    C1, C2, C3, C4 = get_numbered_constants(eq, num=4)
    v = Function('v')
    u = Symbol('u')
    f = Wild('f')
    g = Wild('g')
    r1 = eq[0].match(diff(x(t),t) - f)
    r2 = eq[1].match(diff(y(t),t) - g)
    F = r1[f].subs(x(t), u).subs(y(t), v(u))
    G = r2[g].subs(x(t), u).subs(y(t), v(u))
    sol2r = dsolve(Eq(diff(v(u), u), G/F))
    for sol2s in sol2r:
        sol1 = solve(Integral(1/F.subs(v(u), sol2s.rhs), u).doit() - t - C2, u)
    sol = []
    for sols in sol1:
        sol.append(Eq(x(t), sols))
        sol.append(Eq(y(t), (sol2s.rhs).subs(u, sols)))
    return sol

def _nonlinear_2eq_order1_type4(x, y, t, eq):
    r"""
    Equation:

    .. math:: x' = f_1(x) g_1(y) \phi(x,y,t)

    .. math:: y' = f_2(x) g_2(y) \phi(x,y,t)

    First integral:

    .. math:: \int \frac{f_2(x)}{f_1(x)} \,dx - \int \frac{g_1(y)}{g_2(y)} \,dy = C

    where `C` is an arbitrary constant.

    On solving the first integral for `x` (resp., `y` ) and on substituting the
    resulting expression into either equation of the original solution, one
    arrives at a first-order equation for determining `y` (resp., `x` ).

    """
    C1, C2 = get_numbered_constants(eq, num=2)
    u, v = symbols('u, v')
    U, V = symbols('U, V', cls=Function)
    f = Wild('f')
    g = Wild('g')
    f1 = Wild('f1', exclude=[v,t])
    f2 = Wild('f2', exclude=[v,t])
    g1 = Wild('g1', exclude=[u,t])
    g2 = Wild('g2', exclude=[u,t])
    r1 = eq[0].match(diff(x(t),t) - f)
    r2 = eq[1].match(diff(y(t),t) - g)
    num, den = (
        (r1[f].subs(x(t),u).subs(y(t),v))/
        (r2[g].subs(x(t),u).subs(y(t),v))).as_numer_denom()
    R1 = num.match(f1*g1)
    R2 = den.match(f2*g2)
    phi = (r1[f].subs(x(t),u).subs(y(t),v))/num
    F1 = R1[f1]; F2 = R2[f2]
    G1 = R1[g1]; G2 = R2[g2]
    sol1r = solve(Integral(F2/F1, u).doit() - Integral(G1/G2,v).doit() - C1, u)
    sol2r = solve(Integral(F2/F1, u).doit() - Integral(G1/G2,v).doit() - C1, v)
    sol = []
    for sols in sol1r:
        sol.append(Eq(y(t), dsolve(diff(V(t),t) - F2.subs(u,sols).subs(v,V(t))*G2.subs(v,V(t))*phi.subs(u,sols).subs(v,V(t))).rhs))
    for sols in sol2r:
        sol.append(Eq(x(t), dsolve(diff(U(t),t) - F1.subs(u,U(t))*G1.subs(v,sols).subs(u,U(t))*phi.subs(v,sols).subs(u,U(t))).rhs))
    return set(sol)

def _nonlinear_2eq_order1_type5(func, t, eq):
    r"""
    Clairaut system of ODEs

    .. math:: x = t x' + F(x',y')

    .. math:: y = t y' + G(x',y')

    The following are solutions of the system

    `(i)` straight lines:

    .. math:: x = C_1 t + F(C_1, C_2), y = C_2 t + G(C_1, C_2)

    where `C_1` and `C_2` are arbitrary constants;

    `(ii)` envelopes of the above lines;

    `(iii)` continuously differentiable lines made up from segments of the lines
    `(i)` and `(ii)`.

    """
    C1, C2 = get_numbered_constants(eq, num=2)
    f = Wild('f')
    g = Wild('g')
    def check_type(x, y):
        r1 = eq[0].match(t*diff(x(t),t) - x(t) + f)
        r2 = eq[1].match(t*diff(y(t),t) - y(t) + g)
        if not (r1 and r2):
            r1 = eq[0].match(diff(x(t),t) - x(t)/t + f/t)
            r2 = eq[1].match(diff(y(t),t) - y(t)/t + g/t)
        if not (r1 and r2):
            r1 = (-eq[0]).match(t*diff(x(t),t) - x(t) + f)
            r2 = (-eq[1]).match(t*diff(y(t),t) - y(t) + g)
        if not (r1 and r2):
            r1 = (-eq[0]).match(diff(x(t),t) - x(t)/t + f/t)
            r2 = (-eq[1]).match(diff(y(t),t) - y(t)/t + g/t)
        return [r1, r2]
    for func_ in func:
        if isinstance(func_, list):
            x = func[0][0].func
            y = func[0][1].func
            [r1, r2] = check_type(x, y)
            if not (r1 and r2):
                [r1, r2] = check_type(y, x)
                x, y = y, x
    x1 = diff(x(t),t); y1 = diff(y(t),t)
    return {Eq(x(t), C1*t + r1[f].subs(x1,C1).subs(y1,C2)), Eq(y(t), C2*t + r2[g].subs(x1,C1).subs(y1,C2))}

def sysode_nonlinear_3eq_order1(match_):
    x = match_['func'][0].func
    y = match_['func'][1].func
    z = match_['func'][2].func
    eq = match_['eq']
    fc = match_['func_coeff']
    func = match_['func']
    t = list(list(eq[0].atoms(Derivative))[0].atoms(Symbol))[0]
    if match_['type_of_equation'] == 'type1':
        sol = _nonlinear_3eq_order1_type1(x, y, z, t, eq)
    if match_['type_of_equation'] == 'type2':
        sol = _nonlinear_3eq_order1_type2(x, y, z, t, eq)
    if match_['type_of_equation'] == 'type3':
        sol = _nonlinear_3eq_order1_type3(x, y, z, t, eq)
    if match_['type_of_equation'] == 'type4':
        sol = _nonlinear_3eq_order1_type4(x, y, z, t, eq)
    if match_['type_of_equation'] == 'type5':
        sol = _nonlinear_3eq_order1_type5(x, y, z, t, eq)
    return sol

def _nonlinear_3eq_order1_type1(x, y, z, t, eq):
    r"""
    Equations:

    .. math:: a x' = (b - c) y z, \enspace b y' = (c - a) z x, \enspace c z' = (a - b) x y

    First Integrals:

    .. math:: a x^{2} + b y^{2} + c z^{2} = C_1

    .. math:: a^{2} x^{2} + b^{2} y^{2} + c^{2} z^{2} = C_2

    where `C_1` and `C_2` are arbitrary constants. On solving the integrals for `y` and
    `z` and on substituting the resulting expressions into the first equation of the
    system, we arrives at a separable first-order equation on `x`. Similarly doing that
    for other two equations, we will arrive at first order equation on `y` and `z` too.

    References
    ==========
    -http://eqworld.ipmnet.ru/en/solutions/sysode/sode0401.pdf

    """
    C1, C2 = get_numbered_constants(eq, num=2)
    u, v, w = symbols('u, v, w')
    p = Wild('p', exclude=[x(t), y(t), z(t), t])
    q = Wild('q', exclude=[x(t), y(t), z(t), t])
    s = Wild('s', exclude=[x(t), y(t), z(t), t])
    r = (diff(x(t),t) - eq[0]).match(p*y(t)*z(t))
    r.update((diff(y(t),t) - eq[1]).match(q*z(t)*x(t)))
    r.update((diff(z(t),t) - eq[2]).match(s*x(t)*y(t)))
    n1, d1 = r[p].as_numer_denom()
    n2, d2 = r[q].as_numer_denom()
    n3, d3 = r[s].as_numer_denom()
    val = solve([n1*u-d1*v+d1*w, d2*u+n2*v-d2*w, d3*u-d3*v-n3*w],[u,v])
    vals = [val[v], val[u]]
    c = lcm(vals[0].as_numer_denom()[1], vals[1].as_numer_denom()[1])
    b = vals[0].subs(w,c)
    a = vals[1].subs(w,c)
    y_x = sqrt(((c*C1-C2) - a*(c-a)*x(t)**2)/(b*(c-b)))
    z_x = sqrt(((b*C1-C2) - a*(b-a)*x(t)**2)/(c*(b-c)))
    z_y = sqrt(((a*C1-C2) - b*(a-b)*y(t)**2)/(c*(a-c)))
    x_y = sqrt(((c*C1-C2) - b*(c-b)*y(t)**2)/(a*(c-a)))
    x_z = sqrt(((b*C1-C2) - c*(b-c)*z(t)**2)/(a*(b-a)))
    y_z = sqrt(((a*C1-C2) - c*(a-c)*z(t)**2)/(b*(a-b)))
    sol1 = dsolve(a*diff(x(t),t) - (b-c)*y_x*z_x)
    sol2 = dsolve(b*diff(y(t),t) - (c-a)*z_y*x_y)
    sol3 = dsolve(c*diff(z(t),t) - (a-b)*x_z*y_z)
    return [sol1, sol2, sol3]


def _nonlinear_3eq_order1_type2(x, y, z, t, eq):
    r"""
    Equations:

    .. math:: a x' = (b - c) y z f(x, y, z, t)

    .. math:: b y' = (c - a) z x f(x, y, z, t)

    .. math:: c z' = (a - b) x y f(x, y, z, t)

    First Integrals:

    .. math:: a x^{2} + b y^{2} + c z^{2} = C_1

    .. math:: a^{2} x^{2} + b^{2} y^{2} + c^{2} z^{2} = C_2

    where `C_1` and `C_2` are arbitrary constants. On solving the integrals for `y` and
    `z` and on substituting the resulting expressions into the first equation of the
    system, we arrives at a first-order differential equations on `x`. Similarly doing
    that for other two equations we will arrive at first order equation on `y` and `z`.

    References
    ==========
    -http://eqworld.ipmnet.ru/en/solutions/sysode/sode0402.pdf

    """
    C1, C2 = get_numbered_constants(eq, num=2)
    u, v, w = symbols('u, v, w')
    p = Wild('p', exclude=[x(t), y(t), z(t), t])
    q = Wild('q', exclude=[x(t), y(t), z(t), t])
    s = Wild('s', exclude=[x(t), y(t), z(t), t])
    f = Wild('f')
    r1 = (diff(x(t),t) - eq[0]).match(y(t)*z(t)*f)
    r = collect_const(r1[f]).match(p*f)
    r.update(((diff(y(t),t) - eq[1])/r[f]).match(q*z(t)*x(t)))
    r.update(((diff(z(t),t) - eq[2])/r[f]).match(s*x(t)*y(t)))
    n1, d1 = r[p].as_numer_denom()
    n2, d2 = r[q].as_numer_denom()
    n3, d3 = r[s].as_numer_denom()
    val = solve([n1*u-d1*v+d1*w, d2*u+n2*v-d2*w, -d3*u+d3*v+n3*w],[u,v])
    vals = [val[v], val[u]]
    c = lcm(vals[0].as_numer_denom()[1], vals[1].as_numer_denom()[1])
    a = vals[0].subs(w,c)
    b = vals[1].subs(w,c)
    y_x = sqrt(((c*C1-C2) - a*(c-a)*x(t)**2)/(b*(c-b)))
    z_x = sqrt(((b*C1-C2) - a*(b-a)*x(t)**2)/(c*(b-c)))
    z_y = sqrt(((a*C1-C2) - b*(a-b)*y(t)**2)/(c*(a-c)))
    x_y = sqrt(((c*C1-C2) - b*(c-b)*y(t)**2)/(a*(c-a)))
    x_z = sqrt(((b*C1-C2) - c*(b-c)*z(t)**2)/(a*(b-a)))
    y_z = sqrt(((a*C1-C2) - c*(a-c)*z(t)**2)/(b*(a-b)))
    sol1 = dsolve(a*diff(x(t),t) - (b-c)*y_x*z_x*r[f])
    sol2 = dsolve(b*diff(y(t),t) - (c-a)*z_y*x_y*r[f])
    sol3 = dsolve(c*diff(z(t),t) - (a-b)*x_z*y_z*r[f])
    return [sol1, sol2, sol3]

def _nonlinear_3eq_order1_type3(x, y, z, t, eq):
    r"""
    Equations:

    .. math:: x' = c F_2 - b F_3, \enspace y' = a F_3 - c F_1, \enspace z' = b F_1 - a F_2

    where `F_n = F_n(x, y, z, t)`.

    1. First Integral:

    .. math:: a x + b y + c z = C_1,

    where C is an arbitrary constant.

    2. If we assume function `F_n` to be independent of `t`,i.e, `F_n` = `F_n (x, y, z)`
    Then, on eliminating `t` and `z` from the first two equation of the system, one
    arrives at the first-order equation

    .. math:: \frac{dy}{dx} = \frac{a F_3 (x, y, z) - c F_1 (x, y, z)}{c F_2 (x, y, z) -
                b F_3 (x, y, z)}

    where `z = \frac{1}{c} (C_1 - a x - b y)`

    References
    ==========
    -http://eqworld.ipmnet.ru/en/solutions/sysode/sode0404.pdf

    """
    C1 = get_numbered_constants(eq, num=1)
    u, v, w = symbols('u, v, w')
    p = Wild('p', exclude=[x(t), y(t), z(t), t])
    q = Wild('q', exclude=[x(t), y(t), z(t), t])
    s = Wild('s', exclude=[x(t), y(t), z(t), t])
    F1, F2, F3 = symbols('F1, F2, F3', cls=Wild)
    r1 = (diff(x(t),t) - eq[0]).match(F2-F3)
    r = collect_const(r1[F2]).match(s*F2)
    r.update(collect_const(r1[F3]).match(q*F3))
    if eq[1].has(r[F2]) and not eq[1].has(r[F3]):
        r[F2], r[F3] = r[F3], r[F2]
        r[s], r[q] = -r[q], -r[s]
    r.update((diff(y(t),t) - eq[1]).match(p*r[F3] - r[s]*F1))
    a = r[p]; b = r[q]; c = r[s]
    F1 = r[F1].subs(x(t),u).subs(y(t),v).subs(z(t),w)
    F2 = r[F2].subs(x(t),u).subs(y(t),v).subs(z(t),w)
    F3 = r[F3].subs(x(t),u).subs(y(t),v).subs(z(t),w)
    z_xy = (C1-a*u-b*v)/c
    y_zx = (C1-a*u-c*w)/b
    x_yz = (C1-b*v-c*w)/a
    y_x = dsolve(diff(v(u),u) - ((a*F3-c*F1)/(c*F2-b*F3)).subs(w,z_xy).subs(v,v(u))).rhs
    z_x = dsolve(diff(w(u),u) - ((b*F1-a*F2)/(c*F2-b*F3)).subs(v,y_zx).subs(w,w(u))).rhs
    z_y = dsolve(diff(w(v),v) - ((b*F1-a*F2)/(a*F3-c*F1)).subs(u,x_yz).subs(w,w(v))).rhs
    x_y = dsolve(diff(u(v),v) - ((c*F2-b*F3)/(a*F3-c*F1)).subs(w,z_xy).subs(u,u(v))).rhs
    y_z = dsolve(diff(v(w),w) - ((a*F3-c*F1)/(b*F1-a*F2)).subs(u,x_yz).subs(v,v(w))).rhs
    x_z = dsolve(diff(u(w),w) - ((c*F2-b*F3)/(b*F1-a*F2)).subs(v,y_zx).subs(u,u(w))).rhs
    sol1 = dsolve(diff(u(t),t) - (c*F2 - b*F3).subs(v,y_x).subs(w,z_x).subs(u,u(t))).rhs
    sol2 = dsolve(diff(v(t),t) - (a*F3 - c*F1).subs(u,x_y).subs(w,z_y).subs(v,v(t))).rhs
    sol3 = dsolve(diff(w(t),t) - (b*F1 - a*F2).subs(u,x_z).subs(v,y_z).subs(w,w(t))).rhs
    return [sol1, sol2, sol3]

def _nonlinear_3eq_order1_type4(x, y, z, t, eq):
    r"""
    Equations:

    .. math:: x' = c z F_2 - b y F_3, \enspace y' = a x F_3 - c z F_1, \enspace z' = b y F_1 - a x F_2

    where `F_n = F_n (x, y, z, t)`

    1. First integral:

    .. math:: a x^{2} + b y^{2} + c z^{2} = C_1

    where `C` is an arbitrary constant.

    2. Assuming the function `F_n` is independent of `t`: `F_n = F_n (x, y, z)`. Then on
    eliminating `t` and `z` from the first two equations of the system, one arrives at
    the first-order equation

    .. math:: \frac{dy}{dx} = \frac{a x F_3 (x, y, z) - c z F_1 (x, y, z)}
                {c z F_2 (x, y, z) - b y F_3 (x, y, z)}

    where `z = \pm \sqrt{\frac{1}{c} (C_1 - a x^{2} - b y^{2})}`

    References
    ==========
    -http://eqworld.ipmnet.ru/en/solutions/sysode/sode0405.pdf

    """
    C1 = get_numbered_constants(eq, num=1)
    u, v, w = symbols('u, v, w')
    p = Wild('p', exclude=[x(t), y(t), z(t), t])
    q = Wild('q', exclude=[x(t), y(t), z(t), t])
    s = Wild('s', exclude=[x(t), y(t), z(t), t])
    F1, F2, F3 = symbols('F1, F2, F3', cls=Wild)
    r1 = eq[0].match(diff(x(t),t) - z(t)*F2 + y(t)*F3)
    r = collect_const(r1[F2]).match(s*F2)
    r.update(collect_const(r1[F3]).match(q*F3))
    if eq[1].has(r[F2]) and not eq[1].has(r[F3]):
        r[F2], r[F3] = r[F3], r[F2]
        r[s], r[q] = -r[q], -r[s]
    r.update((diff(y(t),t) - eq[1]).match(p*x(t)*r[F3] - r[s]*z(t)*F1))
    a = r[p]; b = r[q]; c = r[s]
    F1 = r[F1].subs(x(t),u).subs(y(t),v).subs(z(t),w)
    F2 = r[F2].subs(x(t),u).subs(y(t),v).subs(z(t),w)
    F3 = r[F3].subs(x(t),u).subs(y(t),v).subs(z(t),w)
    x_yz = sqrt((C1 - b*v**2 - c*w**2)/a)
    y_zx = sqrt((C1 - c*w**2 - a*u**2)/b)
    z_xy = sqrt((C1 - a*u**2 - b*v**2)/c)
    y_x = dsolve(diff(v(u),u) - ((a*u*F3-c*w*F1)/(c*w*F2-b*v*F3)).subs(w,z_xy).subs(v,v(u))).rhs
    z_x = dsolve(diff(w(u),u) - ((b*v*F1-a*u*F2)/(c*w*F2-b*v*F3)).subs(v,y_zx).subs(w,w(u))).rhs
    z_y = dsolve(diff(w(v),v) - ((b*v*F1-a*u*F2)/(a*u*F3-c*w*F1)).subs(u,x_yz).subs(w,w(v))).rhs
    x_y = dsolve(diff(u(v),v) - ((c*w*F2-b*v*F3)/(a*u*F3-c*w*F1)).subs(w,z_xy).subs(u,u(v))).rhs
    y_z = dsolve(diff(v(w),w) - ((a*u*F3-c*w*F1)/(b*v*F1-a*u*F2)).subs(u,x_yz).subs(v,v(w))).rhs
    x_z = dsolve(diff(u(w),w) - ((c*w*F2-b*v*F3)/(b*v*F1-a*u*F2)).subs(v,y_zx).subs(u,u(w))).rhs
    sol1 = dsolve(diff(u(t),t) - (c*w*F2 - b*v*F3).subs(v,y_x).subs(w,z_x).subs(u,u(t))).rhs
    sol2 = dsolve(diff(v(t),t) - (a*u*F3 - c*w*F1).subs(u,x_y).subs(w,z_y).subs(v,v(t))).rhs
    sol3 = dsolve(diff(w(t),t) - (b*v*F1 - a*u*F2).subs(u,x_z).subs(v,y_z).subs(w,w(t))).rhs
    return [sol1, sol2, sol3]

def _nonlinear_3eq_order1_type5(x, y, t, eq):
    r"""
    .. math:: x' = x (c F_2 - b F_3), \enspace y' = y (a F_3 - c F_1), \enspace z' = z (b F_1 - a F_2)

    where `F_n = F_n (x, y, z, t)` and are arbitrary functions.

    First Integral:

    .. math:: \left|x\right|^{a} \left|y\right|^{b} \left|z\right|^{c} = C_1

    where `C` is an arbitrary constant. If the function `F_n` is independent of `t`,
    then, by eliminating `t` and `z` from the first two equations of the system, one
    arrives at a first-order equation.

    References
    ==========
    -http://eqworld.ipmnet.ru/en/solutions/sysode/sode0406.pdf

    """
    C1 = get_numbered_constants(eq, num=1)
    u, v, w = symbols('u, v, w')
    p = Wild('p', exclude=[x(t), y(t), z(t), t])
    q = Wild('q', exclude=[x(t), y(t), z(t), t])
    s = Wild('s', exclude=[x(t), y(t), z(t), t])
    F1, F2, F3 = symbols('F1, F2, F3', cls=Wild)
    r1 = eq[0].match(diff(x(t),t) - x(t)*(F2 - F3))
    r = collect_const(r1[F2]).match(s*F2)
    r.update(collect_const(r1[F3]).match(q*F3))
    if eq[1].has(r[F2]) and not eq[1].has(r[F3]):
        r[F2], r[F3] = r[F3], r[F2]
        r[s], r[q] = -r[q], -r[s]
    r.update((diff(y(t),t) - eq[1]).match(y(t)*(a*r[F3] - r[c]*F1)))
    a = r[p]; b = r[q]; c = r[s]
    F1 = r[F1].subs(x(t),u).subs(y(t),v).subs(z(t),w)
    F2 = r[F2].subs(x(t),u).subs(y(t),v).subs(z(t),w)
    F3 = r[F3].subs(x(t),u).subs(y(t),v).subs(z(t),w)
    x_yz = (C1*v**-b*w**-c)**-a
    y_zx = (C1*w**-c*u**-a)**-b
    z_xy = (C1*u**-a*v**-b)**-c
    y_x = dsolve(diff(v(u),u) - ((v*(a*F3-c*F1))/(u*(c*F2-b*F3))).subs(w,z_xy).subs(v,v(u))).rhs
    z_x = dsolve(diff(w(u),u) - ((w*(b*F1-a*F2))/(u*(c*F2-b*F3))).subs(v,y_zx).subs(w,w(u))).rhs
    z_y = dsolve(diff(w(v),v) - ((w*(b*F1-a*F2))/(v*(a*F3-c*F1))).subs(u,x_yz).subs(w,w(v))).rhs
    x_y = dsolve(diff(u(v),v) - ((u*(c*F2-b*F3))/(v*(a*F3-c*F1))).subs(w,z_xy).subs(u,u(v))).rhs
    y_z = dsolve(diff(v(w),w) - ((v*(a*F3-c*F1))/(w*(b*F1-a*F2))).subs(u,x_yz).subs(v,v(w))).rhs
    x_z = dsolve(diff(u(w),w) - ((u*(c*F2-b*F3))/(w*(b*F1-a*F2))).subs(v,y_zx).subs(u,u(w))).rhs
    sol1 = dsolve(diff(u(t),t) - (u*(c*F2-b*F3)).subs(v,y_x).subs(w,z_x).subs(u,u(t))).rhs
    sol2 = dsolve(diff(v(t),t) - (v*(a*F3-c*F1)).subs(u,x_y).subs(w,z_y).subs(v,v(t))).rhs
    sol3 = dsolve(diff(w(t),t) - (w*(b*F1-a*F2)).subs(u,x_z).subs(v,y_z).subs(w,w(t))).rhs
    return [sol1, sol2, sol3]
