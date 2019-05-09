from sympy.external import import_module
from sympy.utilities.decorator import doctest_depends_on
from sympy.functions.elementary.integers import floor, frac
from sympy.functions import (log, sin, cos, tan, cot, csc, sec, sqrt, erf, gamma, uppergamma, polygamma, digamma,
    loggamma, factorial, zeta, LambertW)
from sympy.functions.elementary.hyperbolic import acosh, asinh, atanh, acoth, acsch, asech, cosh, sinh, tanh, coth, sech, csch
from sympy.functions.elementary.trigonometric import atan, acsc, asin, acot, acos, asec, atan2
from sympy.polys.polytools import Poly, quo, rem, total_degree, degree
from sympy.simplify.simplify import fraction, simplify, cancel, powsimp
from sympy.core.sympify import sympify
from sympy.utilities.iterables import postorder_traversal
from sympy.functions.special.error_functions import fresnelc, fresnels, erfc, erfi, Ei, expint, li, Si, Ci, Shi, Chi
from sympy.functions.elementary.complexes import im, re, Abs
from sympy.core.exprtools import factor_terms
from sympy import (Basic, E, polylog, N, Wild, WildFunction, factor, gcd, Sum, S, I, Mul, Integer, Float, Dict, Symbol, Rational,
    Add, hyper, symbols, sqf_list, sqf, Max, factorint, factorrat, Min, sign, E, Function, collect, FiniteSet, nsimplify,
    expand_trig, expand, poly, apart, lcm, And, Pow, pi, zoo, oo, Integral, UnevaluatedExpr, PolynomialError, Dummy, exp,
    powdenest, PolynomialDivisionFailed, discriminant, UnificationFailed, appellf1)
from sympy.functions.special.hyper import TupleArg
from sympy.functions.special.elliptic_integrals import elliptic_f, elliptic_e, elliptic_pi
from sympy.utilities.iterables import flatten
from random import randint
from sympy.logic.boolalg import Or

matchpy = import_module("matchpy")

if matchpy:
    from matchpy import Arity, Operation, CommutativeOperation, AssociativeOperation, OneIdentityOperation, CustomConstraint, Pattern, ReplacementRule, ManyToOneReplacer
    from matchpy.expressions.functions import op_iter, create_operation_expression, op_len
    from sympy.integrals.rubi.symbol import WC
    from matchpy import is_match, replace_all

    Operation.register(Integral)
    Operation.register(Pow)
    OneIdentityOperation.register(Pow)

    Operation.register(Add)
    OneIdentityOperation.register(Add)
    CommutativeOperation.register(Add)
    AssociativeOperation.register(Add)

    Operation.register(Mul)
    OneIdentityOperation.register(Mul)
    CommutativeOperation.register(Mul)
    AssociativeOperation.register(Mul)

    Operation.register(exp)
    Operation.register(log)
    Operation.register(gamma)
    Operation.register(uppergamma)
    Operation.register(fresnels)
    Operation.register(fresnelc)
    Operation.register(erf)
    Operation.register(Ei)
    Operation.register(erfc)
    Operation.register(erfi)
    Operation.register(sin)
    Operation.register(cos)
    Operation.register(tan)
    Operation.register(cot)
    Operation.register(csc)
    Operation.register(sec)
    Operation.register(sinh)
    Operation.register(cosh)
    Operation.register(tanh)
    Operation.register(coth)
    Operation.register(csch)
    Operation.register(sech)
    Operation.register(asin)
    Operation.register(acos)
    Operation.register(atan)
    Operation.register(acot)
    Operation.register(acsc)
    Operation.register(asec)
    Operation.register(asinh)
    Operation.register(acosh)
    Operation.register(atanh)
    Operation.register(acoth)
    Operation.register(acsch)
    Operation.register(asech)

    @op_iter.register(Integral)
    def _(operation):
        return iter((operation._args[0],) + operation._args[1])

    @op_iter.register(Basic)
    def _(operation):
        return iter(operation._args)

    @op_len.register(Integral)
    def _(operation):
        return 1 + len(operation._args[1])

    @op_len.register(Basic)
    def _(operation):
        return len(operation._args)

    @create_operation_expression.register(Basic)
    def sympy_op_factory(old_operation, new_operands, variable_name=True):
         return type(old_operation)(*new_operands)
