from sympy.external import import_module
matchpy = import_module("matchpy")
from sympy.utilities.decorator import doctest_depends_on
from sympy.core import Integer, Float
import inspect, re
from sympy import powsimp

if matchpy:
    from matchpy import (Operation, CommutativeOperation, AssociativeOperation,
        ManyToOneReplacer, OneIdentityOperation, CustomConstraint)
    from sympy import Pow, Add, Integral, Basic, Mul, S, Function, E
    from sympy.functions import (log, sin, cos, tan, cot, csc, sec, sqrt, erf,
        exp as sym_exp, gamma, acosh, asinh, atanh, acoth, acsch, asech, cosh, sinh,
        tanh, coth, sech, csch, atan, acsc, asin, acot, acos, asec, fresnels,
        fresnelc, erfc, erfi, Ei, uppergamma, polylog, zeta, factorial, polygamma, digamma, li,
        expint, LambertW, loggamma)
    from sympy.integrals.rubi.utility_function import (Gamma, rubi_exp, rubi_log, ProductLog, PolyGamma,
        rubi_unevaluated_expr, process_trig)

    from sympy.utilities.matchpy_connector import op_iter, op_len

    @doctest_depends_on(modules=('matchpy',))
    def rubi_object():
        '''
        Returns rubi ManyToOneReplacer by adding all rules from different modules.

        Uncomment the lines to add integration capabilities of that module.

        Currently, there are parsing issues with special_function,
        derivative and miscellaneous_integration. Hence they are commented.
        '''
        from sympy.integrals.rubi.rules.integrand_simplification import integrand_simplification
        from sympy.integrals.rubi.rules.linear_products import linear_products
        from sympy.integrals.rubi.rules.quadratic_products import quadratic_products
        from sympy.integrals.rubi.rules.binomial_products import binomial_products
        from sympy.integrals.rubi.rules.trinomial_products import trinomial_products
        from sympy.integrals.rubi.rules.miscellaneous_algebraic import miscellaneous_algebraic
        from sympy.integrals.rubi.rules.exponential import exponential
        from sympy.integrals.rubi.rules.logarithms import logarithms
        from sympy.integrals.rubi.rules.sine import sine
        from sympy.integrals.rubi.rules.tangent import tangent
        from sympy.integrals.rubi.rules.secant import secant
        from sympy.integrals.rubi.rules.miscellaneous_trig import miscellaneous_trig
        from sympy.integrals.rubi.rules.inverse_trig import inverse_trig
        from sympy.integrals.rubi.rules.hyperbolic import hyperbolic
        from sympy.integrals.rubi.rules.inverse_hyperbolic import inverse_hyperbolic
        from sympy.integrals.rubi.rules.special_functions import special_functions
        #from sympy.integrals.rubi.rules.derivative import derivative
        #from sympy.integrals.rubi.rules.piecewise_linear import piecewise_linear
        from sympy.integrals.rubi.rules.miscellaneous_integration import miscellaneous_integration
        rules = []
        rules_applied = []
        rules += integrand_simplification(rules_applied)
        rules += linear_products(rules_applied)
        rules += quadratic_products(rules_applied)
        rules += binomial_products(rules_applied)
        rules += trinomial_products(rules_applied)
        rules += miscellaneous_algebraic(rules_applied)
        rules += exponential(rules_applied)
        rules += logarithms(rules_applied)
        rules += special_functions(rules_applied)
        rules += sine(rules_applied)
        rules += tangent(rules_applied)
        rules += secant(rules_applied)
        rules += miscellaneous_trig(rules_applied)
        rules += inverse_trig(rules_applied)
        rules += hyperbolic(rules_applied)
        rules += inverse_hyperbolic(rules_applied)
        #rubi = piecewise_linear(rubi)
        rules += miscellaneous_integration(rules_applied)
        rubi = ManyToOneReplacer(*rules)
        return rubi, rules_applied, rules
    _E = rubi_unevaluated_expr(E)
    Integrate = Function('Integrate')
    rubi, rules_applied, rules = rubi_object()

def _has_cycle():
    if rules_applied.count(rules_applied[-1]) == 1:
        return False
    if rules_applied[-1] == rules_applied[-2] == rules_applied[-3] == rules_applied[-4] == rules_applied[-5]:
        return True

def process_final_integral(expr):
    '''
    When there is recursion for more than 10 rules or in total 20 rules have been applied
    rubi returns `Integrate` in order to stop any further matching. After complete integration,
    Integrate needs to be replaced back to Integral. Also rubi's `exp` need to be replaced back
    to sympy's general `exp`.

    Examples
    ========
    >>> from sympy import Function, E
    >>> from sympy.integrals.rubi.rubi import process_final_integral
    >>> from sympy.integrals.rubi.utility_function import rubi_unevaluated_expr
    >>> Integrate = Function("Integrate")
    >>> from sympy.abc import a, x
    >>> _E = rubi_unevaluated_expr(E)
    >>> process_final_integral(Integrate(a, x))
    Integral(a, x)
    >>> process_final_integral(_E**5)
    exp(5)

    '''
    if expr.has(Integrate):
        expr = expr.replace(Integrate, Integral)
    if expr.has(_E):
        expr = expr.replace(_E, E)
    return expr

def rubi_powsimp(expr):
    '''
    This function is needed to preprocess an expression as done in matchpy
    `x^a*x^b` in matchpy auotmatically transforms to `x^(a+b)`

    Examples
    ========

    >>> from sympy.integrals.rubi.rubi import rubi_powsimp
    >>> from sympy.abc import a, b, x
    >>> rubi_powsimp(x**a*x**b)
    x**(a+b)

    '''
    lst_pow =[]
    lst_non_pow = []
    if isinstance(expr, Mul):
        for i in expr.args:
            if isinstance(i, (Pow, exp, sym_exp)):
                lst_pow.append(i)
            else:
                lst_non_pow.append(i)
        return powsimp(Mul(*lst_pow))*Mul(*lst_non_pow)
    return expr

@doctest_depends_on(modules=('matchpy',))
def rubi_integrate(expr, var, showsteps=False):
    '''
    Rule based algorithm for integration. Integrates the expression by applying
    transformation rules to the expression.

    Returns `Integrate` if an expression cannot be integrated.

    Parameters
    ==========
    expr : integrand expression
    var : variable of integration

    Returns Integral object if unable to integrate.
    '''
    expr = expr.replace(sym_exp, exp)
    rules_applied[:] = []
    expr = process_trig(expr)
    expr = rubi_powsimp(expr)
    if isinstance(expr, (int, Integer)) or isinstance(expr, (float, Float)):
        return S(expr)*var
    if isinstance(expr, Add):
        results = 0
        for ex in expr.args:
            rules_applied[:] = []
            results += rubi.replace(Integral(ex, var))
            rules_applied[:] = []
        return process_final_integral(results)

    results = rubi.replace(Integral(expr, var), max_count = 10)
    return process_final_integral(results)

@doctest_depends_on(modules=('matchpy',))
def util_rubi_integrate(expr, var, showsteps=False):
    expr = process_trig(expr)
    expr = expr.replace(sym_exp, exp)
    if isinstance(expr, (int, Integer)) or isinstance(expr, (float, Float)):
        return S(expr)*var
    if isinstance(expr, Add):
        return rubi_integrate(expr, var)
    if len(rules_applied) > 10:
        if _has_cycle() or len(rules_applied) > 20:
            return Integrate(expr, var)
    results = rubi.replace(Integral(expr, var), max_count = 10)
    rules_applied[:] = []
    return results

@doctest_depends_on(modules=('matchpy',))
def get_matching_rule_definition(expr, var):
    '''
    Prints the list or rules which match to `expr`.

    Parameters
    ==========
    expr : integrand expression
    var : variable of integration
    '''
    matcher = rubi.matcher
    miter = matcher.match(Integral(expr, var))
    for fun, e in miter:
        print("Rule matching: ")
        print(inspect.getsourcefile(fun))
        code, lineno = inspect.getsourcelines(fun)
        print("On line: ", lineno)
        print("\n".join(code))
        print("Pattern matching: ")
        pattno = int(re.match(r"^\s*rule(\d+)", code[0]).group(1))
        print(matcher.patterns[pattno-1])
        print(e)
        print()
