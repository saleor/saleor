"""Integration method that emulates by-hand techniques.

This module also provides functionality to get the steps used to evaluate a
particular integral, in the ``integral_steps`` function. This will return
nested namedtuples representing the integration rules used. The
``manualintegrate`` function computes the integral using those steps given
an integrand; given the steps, ``_manualintegrate`` will evaluate them.

The integrator can be extended with new heuristics and evaluation
techniques. To do so, write a function that accepts an ``IntegralInfo``
object and returns either a namedtuple representing a rule or
``None``. Then, write another function that accepts the namedtuple's fields
and returns the antiderivative, and decorate it with
``@evaluates(namedtuple_type)``.  If the new technique requires a new
match, add the key and call to the antiderivative function to integral_steps.
To enable simple substitutions, add the match to find_substitutions.

"""
from __future__ import print_function, division

from collections import namedtuple, defaultdict

import sympy

from sympy.core.compatibility import reduce, Mapping
from sympy.core.containers import Dict
from sympy.core.logic import fuzzy_not
from sympy.functions.elementary.trigonometric import TrigonometricFunction
from sympy.functions.special.polynomials import OrthogonalPolynomial
from sympy.functions.elementary.piecewise import Piecewise
from sympy.strategies.core import switch, do_one, null_safe, condition
from sympy.core.relational import Eq, Ne
from sympy.polys.polytools import degree
from sympy.ntheory.factor_ import divisors

ZERO = sympy.S.Zero

def Rule(name, props=""):
    # GOTCHA: namedtuple class name not considered!
    def __eq__(self, other):
        return self.__class__ == other.__class__ and tuple.__eq__(self, other)
    __neq__ = lambda self, other: not __eq__(self, other)
    cls = namedtuple(name, props + " context symbol")
    cls.__eq__ = __eq__
    cls.__ne__ = __neq__
    return cls

ConstantRule = Rule("ConstantRule", "constant")
ConstantTimesRule = Rule("ConstantTimesRule", "constant other substep")
PowerRule = Rule("PowerRule", "base exp")
AddRule = Rule("AddRule", "substeps")
URule = Rule("URule", "u_var u_func constant substep")
PartsRule = Rule("PartsRule", "u dv v_step second_step")
CyclicPartsRule = Rule("CyclicPartsRule", "parts_rules coefficient")
TrigRule = Rule("TrigRule", "func arg")
ExpRule = Rule("ExpRule", "base exp")
ReciprocalRule = Rule("ReciprocalRule", "func")
ArcsinRule = Rule("ArcsinRule")
InverseHyperbolicRule = Rule("InverseHyperbolicRule", "func")
AlternativeRule = Rule("AlternativeRule", "alternatives")
DontKnowRule = Rule("DontKnowRule")
DerivativeRule = Rule("DerivativeRule")
RewriteRule = Rule("RewriteRule", "rewritten substep")
PiecewiseRule = Rule("PiecewiseRule", "subfunctions")
HeavisideRule = Rule("HeavisideRule", "harg ibnd substep")
TrigSubstitutionRule = Rule("TrigSubstitutionRule",
                            "theta func rewritten substep restriction")
ArctanRule = Rule("ArctanRule", "a b c")
ArccothRule = Rule("ArccothRule", "a b c")
ArctanhRule = Rule("ArctanhRule", "a b c")
JacobiRule = Rule("JacobiRule", "n a b")
GegenbauerRule = Rule("GegenbauerRule", "n a")
ChebyshevTRule = Rule("ChebyshevTRule", "n")
ChebyshevURule = Rule("ChebyshevURule", "n")
LegendreRule = Rule("LegendreRule", "n")
HermiteRule = Rule("HermiteRule", "n")
LaguerreRule = Rule("LaguerreRule", "n")
AssocLaguerreRule = Rule("AssocLaguerreRule", "n a")
CiRule = Rule("CiRule", "a b")
ChiRule = Rule("ChiRule", "a b")
EiRule = Rule("EiRule", "a b")
SiRule = Rule("SiRule", "a b")
ShiRule = Rule("ShiRule", "a b")
ErfRule = Rule("ErfRule", "a b c")
FresnelCRule = Rule("FresnelCRule", "a b c")
FresnelSRule = Rule("FresnelSRule", "a b c")
LiRule = Rule("LiRule", "a b")
PolylogRule = Rule("PolylogRule", "a b")
UpperGammaRule = Rule("UpperGammaRule", "a e")
EllipticFRule = Rule("EllipticFRule", "a d")
EllipticERule = Rule("EllipticERule", "a d")

IntegralInfo = namedtuple('IntegralInfo', 'integrand symbol')

evaluators = {}
def evaluates(rule):
    def _evaluates(func):
        func.rule = rule
        evaluators[rule] = func
        return func
    return _evaluates

def contains_dont_know(rule):
    if isinstance(rule, DontKnowRule):
        return True
    else:
        for val in rule:
            if isinstance(val, tuple):
                if contains_dont_know(val):
                    return True
            elif isinstance(val, list):
                if any(contains_dont_know(i) for i in val):
                    return True
    return False

def manual_diff(f, symbol):
    """Derivative of f in form expected by find_substitutions

    SymPy's derivatives for some trig functions (like cot) aren't in a form
    that works well with finding substitutions; this replaces the
    derivatives for those particular forms with something that works better.

    """
    if f.args:
        arg = f.args[0]
        if isinstance(f, sympy.tan):
            return arg.diff(symbol) * sympy.sec(arg)**2
        elif isinstance(f, sympy.cot):
            return -arg.diff(symbol) * sympy.csc(arg)**2
        elif isinstance(f, sympy.sec):
            return arg.diff(symbol) * sympy.sec(arg) * sympy.tan(arg)
        elif isinstance(f, sympy.csc):
            return -arg.diff(symbol) * sympy.csc(arg) * sympy.cot(arg)
        elif isinstance(f, sympy.Add):
            return sum([manual_diff(arg, symbol) for arg in f.args])
        elif isinstance(f, sympy.Mul):
            if len(f.args) == 2 and isinstance(f.args[0], sympy.Number):
                return f.args[0] * manual_diff(f.args[1], symbol)
    return f.diff(symbol)

def manual_subs(expr, *args):
    """
    A wrapper for `expr.subs(*args)` with additional logic for substitution
    of invertible functions.
    """
    if len(args) == 1:
        sequence = args[0]
        if isinstance(sequence, (Dict, Mapping)):
            sequence = sequence.items()
        elif not iterable(sequence):
            raise ValueError("Expected an iterable of (old, new) pairs")
    elif len(args) == 2:
        sequence = [args]
    else:
        raise ValueError("subs accepts either 1 or 2 arguments")

    new_subs = []
    for old, new in sequence:
        if isinstance(old, sympy.log):
            # If log(x) = y, then exp(a*log(x)) = exp(a*y)
            # that is, x**a = exp(a*y). Replace nontrivial powers of x
            # before subs turns them into `exp(y)**a`, but
            # do not replace x itself yet, to avoid `log(exp(y))`.
            a = sympy.Wild('a')
            expr = expr.replace(old.args[0]**(1 + a),
                sympy.exp((1 + a)*new), exact=True)
            new_subs.append((old.args[0], sympy.exp(new)))

    return expr.subs(list(sequence) + new_subs)

# Method based on that on SIN, described in "Symbolic Integration: The
# Stormy Decade"

def find_substitutions(integrand, symbol, u_var):
    results = []

    def test_subterm(u, u_diff):
        substituted = integrand / u_diff
        if symbol not in substituted.free_symbols:
            # replaced everything already
            return False

        substituted = manual_subs(substituted, u, u_var).cancel()

        if symbol not in substituted.free_symbols:
            # avoid increasing the degree of a rational function
            if integrand.is_rational_function(symbol) and substituted.is_rational_function(u_var):
                deg_before = max([degree(t, symbol) for t in integrand.as_numer_denom()])
                deg_after = max([degree(t, u_var) for t in substituted.as_numer_denom()])
                if deg_after > deg_before:
                    return False
            return substituted.as_independent(u_var, as_Add=False)

        # special treatment for substitutions u = (a*x+b)**(1/n)
        if (isinstance(u, sympy.Pow) and (1/u.exp).is_Integer and
            sympy.Abs(u.exp) < 1):
                a = sympy.Wild('a', exclude=[symbol])
                b = sympy.Wild('b', exclude=[symbol])
                match = u.base.match(a*symbol + b)
                if match:
                    a, b = [match.get(i, ZERO) for i in (a, b)]
                    if a != 0 and b != 0:
                        substituted = substituted.subs(symbol,
                            (u_var**(1/u.exp) - b)/a)
                        return substituted.as_independent(u_var, as_Add=False)

        return False

    def possible_subterms(term):
        if isinstance(term, (TrigonometricFunction,
                             sympy.asin, sympy.acos, sympy.atan,
                             sympy.exp, sympy.log, sympy.Heaviside)):
            return [term.args[0]]
        elif isinstance(term, (sympy.chebyshevt, sympy.chebyshevu,
                        sympy.legendre, sympy.hermite, sympy.laguerre)):
            return [term.args[1]]
        elif isinstance(term, (sympy.gegenbauer, sympy.assoc_laguerre)):
            return [term.args[2]]
        elif isinstance(term, sympy.jacobi):
            return [term.args[3]]
        elif isinstance(term, sympy.Mul):
            r = []
            for u in term.args:
                r.append(u)
                r.extend(possible_subterms(u))
            return r
        elif isinstance(term, sympy.Pow):
            r = []
            if term.args[1].is_constant(symbol):
                r.append(term.args[0])
            elif term.args[0].is_constant(symbol):
                r.append(term.args[1])
            if term.args[1].is_Integer:
                r.extend([term.args[0]**d for d in divisors(term.args[1])
                    if 1 < d < abs(term.args[1])])
                if term.args[0].is_Add:
                    r.extend([t for t in possible_subterms(term.args[0])
                        if t.is_Pow])
            return r
        elif isinstance(term, sympy.Add):
            r = []
            for arg in term.args:
                r.append(arg)
                r.extend(possible_subterms(arg))
            return r
        return []

    for u in possible_subterms(integrand):
        if u == symbol:
            continue
        u_diff = manual_diff(u, symbol)
        new_integrand = test_subterm(u, u_diff)
        if new_integrand is not False:
            constant, new_integrand = new_integrand
            if new_integrand == integrand.subs(symbol, u_var):
                continue
            substitution = (u, constant, new_integrand)
            if substitution not in results:
                results.append(substitution)

    return results

def rewriter(condition, rewrite):
    """Strategy that rewrites an integrand."""
    def _rewriter(integral):
        integrand, symbol = integral
        if condition(*integral):
            rewritten = rewrite(*integral)
            if rewritten != integrand:
                substep = integral_steps(rewritten, symbol)
                if not isinstance(substep, DontKnowRule) and substep:
                    return RewriteRule(
                        rewritten,
                        substep,
                        integrand, symbol)
    return _rewriter

def proxy_rewriter(condition, rewrite):
    """Strategy that rewrites an integrand based on some other criteria."""
    def _proxy_rewriter(criteria):
        criteria, integral = criteria
        integrand, symbol = integral
        args = criteria + list(integral)
        if condition(*args):
            rewritten = rewrite(*args)
            if rewritten != integrand:
                return RewriteRule(
                    rewritten,
                    integral_steps(rewritten, symbol),
                    integrand, symbol)
    return _proxy_rewriter

def multiplexer(conditions):
    """Apply the rule that matches the condition, else None"""
    def multiplexer_rl(expr):
        for key, rule in conditions.items():
            if key(expr):
                return rule(expr)
    return multiplexer_rl

def alternatives(*rules):
    """Strategy that makes an AlternativeRule out of multiple possible results."""
    def _alternatives(integral):
        alts = []
        for rule in rules:
            result = rule(integral)
            if (result and not isinstance(result, DontKnowRule) and
                result != integral and result not in alts):
                alts.append(result)
        if len(alts) == 1:
            return alts[0]
        elif alts:
            doable = [rule for rule in alts if not contains_dont_know(rule)]
            if doable:
                return AlternativeRule(doable, *integral)
            else:
                return AlternativeRule(alts, *integral)
    return _alternatives

def constant_rule(integral):
    integrand, symbol = integral
    return ConstantRule(integral.integrand, *integral)

def power_rule(integral):
    integrand, symbol = integral
    base, exp = integrand.as_base_exp()

    if symbol not in exp.free_symbols and isinstance(base, sympy.Symbol):
        if sympy.simplify(exp + 1) == 0:
            return ReciprocalRule(base, integrand, symbol)
        return PowerRule(base, exp, integrand, symbol)
    elif symbol not in base.free_symbols and isinstance(exp, sympy.Symbol):
        rule = ExpRule(base, exp, integrand, symbol)

        if fuzzy_not(sympy.log(base).is_zero):
            return rule
        elif sympy.log(base).is_zero:
            return ConstantRule(1, 1, symbol)

        return PiecewiseRule([
            (rule, sympy.Ne(sympy.log(base), 0)),
            (ConstantRule(1, 1, symbol), True)
        ], integrand, symbol)

def exp_rule(integral):
    integrand, symbol = integral
    if isinstance(integrand.args[0], sympy.Symbol):
        return ExpRule(sympy.E, integrand.args[0], integrand, symbol)


def orthogonal_poly_rule(integral):
    orthogonal_poly_classes = {
        sympy.jacobi: JacobiRule,
        sympy.gegenbauer: GegenbauerRule,
        sympy.chebyshevt: ChebyshevTRule,
        sympy.chebyshevu: ChebyshevURule,
        sympy.legendre: LegendreRule,
        sympy.hermite: HermiteRule,
        sympy.laguerre: LaguerreRule,
        sympy.assoc_laguerre: AssocLaguerreRule
        }
    orthogonal_poly_var_index = {
        sympy.jacobi: 3,
        sympy.gegenbauer: 2,
        sympy.assoc_laguerre: 2
        }
    integrand, symbol = integral
    for klass in orthogonal_poly_classes:
        if isinstance(integrand, klass):
            var_index = orthogonal_poly_var_index.get(klass, 1)
            if (integrand.args[var_index] is symbol and not
                any(v.has(symbol) for v in integrand.args[:var_index])):
                    args = integrand.args[:var_index] + (integrand, symbol)
                    return orthogonal_poly_classes[klass](*args)


def special_function_rule(integral):
    integrand, symbol = integral
    a = sympy.Wild('a', exclude=[symbol], properties=[lambda x: not x.is_zero])
    b = sympy.Wild('b', exclude=[symbol])
    c = sympy.Wild('c', exclude=[symbol])
    d = sympy.Wild('d', exclude=[symbol], properties=[lambda x: not x.is_zero])
    e = sympy.Wild('e', exclude=[symbol], properties=[
        lambda x: not (x.is_nonnegative and x.is_integer)])
    wilds = (a, b, c, d, e)
    # patterns consist of a SymPy class, a wildcard expr, an optional
    # condition coded as a lambda (when Wild properties are not enough),
    # followed by an applicable rule
    patterns = (
        (sympy.Mul, sympy.exp(a*symbol + b)/symbol, None, EiRule),
        (sympy.Mul, sympy.cos(a*symbol + b)/symbol, None, CiRule),
        (sympy.Mul, sympy.cosh(a*symbol + b)/symbol, None, ChiRule),
        (sympy.Mul, sympy.sin(a*symbol + b)/symbol, None, SiRule),
        (sympy.Mul, sympy.sinh(a*symbol + b)/symbol, None, ShiRule),
        (sympy.Pow, 1/sympy.log(a*symbol + b), None, LiRule),
        (sympy.exp, sympy.exp(a*symbol**2 + b*symbol + c), None, ErfRule),
        (sympy.sin, sympy.sin(a*symbol**2 + b*symbol + c), None, FresnelSRule),
        (sympy.cos, sympy.cos(a*symbol**2 + b*symbol + c), None, FresnelCRule),
        (sympy.Mul, symbol**e*sympy.exp(a*symbol), None, UpperGammaRule),
        (sympy.Mul, sympy.polylog(b, a*symbol)/symbol, None, PolylogRule),
        (sympy.Pow, 1/sympy.sqrt(a - d*sympy.sin(symbol)**2),
            lambda a, d: a != d, EllipticFRule),
        (sympy.Pow, sympy.sqrt(a - d*sympy.sin(symbol)**2),
            lambda a, d: a != d, EllipticERule),
    )
    for p in patterns:
        if isinstance(integrand, p[0]):
            match = integrand.match(p[1])
            if match:
                wild_vals = tuple(match.get(w) for w in wilds
                                  if match.get(w) is not None)
                if p[2] is None or p[2](*wild_vals):
                    args = wild_vals + (integrand, symbol)
                    return p[3](*args)


def inverse_trig_rule(integral):
    integrand, symbol = integral
    base, exp = integrand.as_base_exp()
    a = sympy.Wild('a', exclude=[symbol])
    b = sympy.Wild('b', exclude=[symbol])
    match = base.match(a + b*symbol**2)

    if not match:
        return

    def negative(x):
        return x.is_negative or x.could_extract_minus_sign()

    def ArcsinhRule(integrand, symbol):
        return InverseHyperbolicRule(sympy.asinh, integrand, symbol)

    def ArccoshRule(integrand, symbol):
        return InverseHyperbolicRule(sympy.acosh, integrand, symbol)

    def make_inverse_trig(RuleClass, base_exp, a, sign_a, b, sign_b):
        u_var = sympy.Dummy("u")
        current_base = base
        current_symbol = symbol
        constant = u_func = u_constant = substep = None
        factored = integrand
        if a != 1:
            constant = a**base_exp
            current_base = sign_a + sign_b * (b/a) * current_symbol**2
            factored = current_base ** base_exp
        if (b/a) != 1:
            u_func = sympy.sqrt(b/a) * symbol
            u_constant = sympy.sqrt(a/b)
            current_symbol = u_var
            current_base = sign_a + sign_b * current_symbol**2

        substep = RuleClass(current_base ** base_exp, current_symbol)
        if u_func is not None:
            if u_constant != 1 and substep is not None:
                substep = ConstantTimesRule(
                    u_constant, current_base ** base_exp, substep,
                    u_constant * current_base ** base_exp, symbol)
            substep = URule(u_var, u_func, u_constant, substep, factored, symbol)
        if constant is not None and substep is not None:
            substep = ConstantTimesRule(constant, factored, substep, integrand, symbol)
        return substep

    a, b = [match.get(i, ZERO) for i in (a, b)]
    # list of (rule, base_exp, a, sign_a, b, sign_b, condition)
    possibilities = []

    if sympy.simplify(2*exp + 1) == 0:
        possibilities.append((ArcsinRule, exp, a, 1, -b, -1, sympy.And(a > 0, b < 0)))
        possibilities.append((ArcsinhRule, exp, a, 1, b, 1, sympy.And(a > 0, b > 0)))
        possibilities.append((ArccoshRule, exp, -a, -1, b, 1, sympy.And(a < 0, b > 0)))

    possibilities = [p for p in possibilities if p[-1] is not sympy.false]
    if a.is_number and b.is_number:
        possibility = [p for p in possibilities if p[-1] is sympy.true]
        if len(possibility) == 1:
            return make_inverse_trig(*possibility[0][:-1])
    elif possibilities:
        return PiecewiseRule(
            [(make_inverse_trig(*p[:-1]), p[-1]) for p in possibilities],
            integrand, symbol)

def add_rule(integral):
    integrand, symbol = integral
    results = [integral_steps(g, symbol)
              for g in integrand.as_ordered_terms()]
    return None if None in results else AddRule(results, integrand, symbol)

def mul_rule(integral):
    integrand, symbol = integral
    args = integrand.args

    # Constant times function case
    coeff, f = integrand.as_independent(symbol)
    next_step = integral_steps(f, symbol)

    if coeff != 1 and next_step is not None:
        return ConstantTimesRule(
            coeff, f,
            next_step,
            integrand, symbol)

def _parts_rule(integrand, symbol):
    # LIATE rule:
    # log, inverse trig, algebraic, trigonometric, exponential
    def pull_out_algebraic(integrand):
        integrand = integrand.cancel().together()
        # iterating over Piecewise args would not work here
        algebraic = ([] if isinstance(integrand, sympy.Piecewise)
            else [arg for arg in integrand.args if arg.is_algebraic_expr(symbol)])
        if algebraic:
            u = sympy.Mul(*algebraic)
            dv = (integrand / u).cancel()
            return u, dv

    def pull_out_u(*functions):
        def pull_out_u_rl(integrand):
            if any([integrand.has(f) for f in functions]):
                args = [arg for arg in integrand.args
                        if any(isinstance(arg, cls) for cls in functions)]
                if args:
                    u = reduce(lambda a,b: a*b, args)
                    dv = integrand / u
                    return u, dv

        return pull_out_u_rl

    liate_rules = [pull_out_u(sympy.log), pull_out_u(sympy.atan, sympy.asin, sympy.acos),
                   pull_out_algebraic, pull_out_u(sympy.sin, sympy.cos),
                   pull_out_u(sympy.exp)]


    dummy = sympy.Dummy("temporary")
    # we can integrate log(x) and atan(x) by setting dv = 1
    if isinstance(integrand, (sympy.log, sympy.atan, sympy.asin, sympy.acos)):
        integrand = dummy * integrand

    for index, rule in enumerate(liate_rules):
        result = rule(integrand)

        if result:
            u, dv = result

            # Don't pick u to be a constant if possible
            if symbol not in u.free_symbols and not u.has(dummy):
                return

            u = u.subs(dummy, 1)
            dv = dv.subs(dummy, 1)

            # Don't pick a non-polynomial algebraic to be differentiated
            if rule == pull_out_algebraic and not u.is_polynomial(symbol):
                return
            # Don't trade one logarithm for another
            if isinstance(u, sympy.log):
                rec_dv = 1/dv
                if (rec_dv.is_polynomial(symbol) and
                    degree(rec_dv, symbol) == 1):
                        return

            # Can integrate a polynomial times OrthogonalPolynomial
            if rule == pull_out_algebraic and isinstance(dv, OrthogonalPolynomial):
                    v_step = integral_steps(dv, symbol)
                    if contains_dont_know(v_step):
                        return
                    else:
                        du = u.diff(symbol)
                        v = _manualintegrate(v_step)
                        return u, dv, v, du, v_step

            # make sure dv is amenable to integration
            accept = False
            if index < 2:  # log and inverse trig are usually worth trying
                accept = True
            elif (rule == pull_out_algebraic and dv.args and
                all(isinstance(a, (sympy.sin, sympy.cos, sympy.exp))
                for a in dv.args)):
                    accept = True
            else:
                for rule in liate_rules[index + 1:]:
                    r = rule(integrand)
                    if r and r[0].subs(dummy, 1).equals(dv):
                        accept = True
                        break

            if accept:
                du = u.diff(symbol)
                v_step = integral_steps(sympy.simplify(dv), symbol)
                if not contains_dont_know(v_step):
                    v = _manualintegrate(v_step)
                    return u, dv, v, du, v_step


def parts_rule(integral):
    integrand, symbol = integral
    constant, integrand = integrand.as_coeff_Mul()

    result = _parts_rule(integrand, symbol)

    steps = []
    if result:
        u, dv, v, du, v_step = result
        steps.append(result)

        if isinstance(v, sympy.Integral):
            return

        # Set a limit on the number of times u can be used
        if isinstance(u, (sympy.sin, sympy.cos, sympy.exp, sympy.sinh, sympy.cosh)):
            cachekey = u.xreplace({symbol: _cache_dummy})
            if _parts_u_cache[cachekey] > 2:
                return
            _parts_u_cache[cachekey] += 1

        # Try cyclic integration by parts a few times
        for _ in range(4):
            coefficient = ((v * du) / integrand).cancel()
            if coefficient == 1:
                break
            if symbol not in coefficient.free_symbols:
                rule = CyclicPartsRule(
                    [PartsRule(u, dv, v_step, None, None, None)
                     for (u, dv, v, du, v_step) in steps],
                    (-1) ** len(steps) * coefficient,
                    integrand, symbol
                )
                if (constant != 1) and rule:
                    rule = ConstantTimesRule(constant, integrand, rule,
                                             constant * integrand, symbol)
                return rule

            # _parts_rule is sensitive to constants, factor it out
            next_constant, next_integrand = (v * du).as_coeff_Mul()
            result = _parts_rule(next_integrand, symbol)

            if result:
                u, dv, v, du, v_step = result
                u *= next_constant
                du *= next_constant
                steps.append((u, dv, v, du, v_step))
            else:
                break

    def make_second_step(steps, integrand):
        if steps:
            u, dv, v, du, v_step = steps[0]
            return PartsRule(u, dv, v_step,
                             make_second_step(steps[1:], v * du),
                             integrand, symbol)
        else:
            steps = integral_steps(integrand, symbol)
            if steps:
                return steps
            else:
                return DontKnowRule(integrand, symbol)

    if steps:
        u, dv, v, du, v_step = steps[0]
        rule = PartsRule(u, dv, v_step,
                         make_second_step(steps[1:], v * du),
                         integrand, symbol)
        if (constant != 1) and rule:
            rule = ConstantTimesRule(constant, integrand, rule,
                                     constant * integrand, symbol)
        return rule


def trig_rule(integral):
    integrand, symbol = integral
    if isinstance(integrand, sympy.sin) or isinstance(integrand, sympy.cos):
        arg = integrand.args[0]

        if not isinstance(arg, sympy.Symbol):
            return  # perhaps a substitution can deal with it

        if isinstance(integrand, sympy.sin):
            func = 'sin'
        else:
            func = 'cos'

        return TrigRule(func, arg, integrand, symbol)

    if integrand == sympy.sec(symbol)**2:
        return TrigRule('sec**2', symbol, integrand, symbol)
    elif integrand == sympy.csc(symbol)**2:
        return TrigRule('csc**2', symbol, integrand, symbol)

    if isinstance(integrand, sympy.tan):
        rewritten = sympy.sin(*integrand.args) / sympy.cos(*integrand.args)
    elif isinstance(integrand, sympy.cot):
        rewritten = sympy.cos(*integrand.args) / sympy.sin(*integrand.args)
    elif isinstance(integrand, sympy.sec):
        arg = integrand.args[0]
        rewritten = ((sympy.sec(arg)**2 + sympy.tan(arg) * sympy.sec(arg)) /
                     (sympy.sec(arg) + sympy.tan(arg)))
    elif isinstance(integrand, sympy.csc):
        arg = integrand.args[0]
        rewritten = ((sympy.csc(arg)**2 + sympy.cot(arg) * sympy.csc(arg)) /
                     (sympy.csc(arg) + sympy.cot(arg)))
    else:
        return

    return RewriteRule(
        rewritten,
        integral_steps(rewritten, symbol),
        integrand, symbol
    )

def trig_product_rule(integral):
    integrand, symbol = integral

    sectan = sympy.sec(symbol) * sympy.tan(symbol)
    q = integrand / sectan

    if symbol not in q.free_symbols:
        rule = TrigRule('sec*tan', symbol, sectan, symbol)
        if q != 1 and rule:
            rule = ConstantTimesRule(q, sectan, rule, integrand, symbol)

        return rule

    csccot = -sympy.csc(symbol) * sympy.cot(symbol)
    q = integrand / csccot

    if symbol not in q.free_symbols:
        rule = TrigRule('csc*cot', symbol, csccot, symbol)
        if q != 1 and rule:
            rule = ConstantTimesRule(q, csccot, rule, integrand, symbol)

        return rule

def quadratic_denom_rule(integral):
    integrand, symbol = integral
    a = sympy.Wild('a', exclude=[symbol])
    b = sympy.Wild('b', exclude=[symbol])
    c = sympy.Wild('c', exclude=[symbol])
    match = integrand.match(a / (b * symbol ** 2 + c))

    if not match:
        return

    a, b, c = match[a], match[b], match[c]
    return PiecewiseRule([(ArctanRule(a, b, c, integrand, symbol), sympy.Gt(c / b, 0)),
                          (ArccothRule(a, b, c, integrand, symbol), sympy.And(sympy.Gt(symbol ** 2, -c / b), sympy.Lt(c / b, 0))),
                          (ArctanhRule(a, b, c, integrand, symbol), sympy.And(sympy.Lt(symbol ** 2, -c / b), sympy.Lt(c / b, 0))),
    ], integrand, symbol)

def root_mul_rule(integral):
    integrand, symbol = integral
    a = sympy.Wild('a', exclude=[symbol])
    b = sympy.Wild('b', exclude=[symbol])
    c = sympy.Wild('c')
    match = integrand.match(sympy.sqrt(a * symbol + b) * c)

    if not match:
        return

    a, b, c = match[a], match[b], match[c]
    d = sympy.Wild('d', exclude=[symbol])
    e = sympy.Wild('e', exclude=[symbol])
    f = sympy.Wild('f')
    recursion_test = c.match(sympy.sqrt(d * symbol + e) * f)
    if recursion_test:
        return

    u = sympy.Dummy('u')
    u_func = sympy.sqrt(a * symbol + b)
    integrand = integrand.subs(u_func, u)
    integrand = integrand.subs(symbol, (u**2 - b) / a)
    integrand = integrand * 2 * u / a
    next_step = integral_steps(integrand, u)
    if next_step:
        return URule(u, u_func, None, next_step, integrand, symbol)

@sympy.cacheit
def make_wilds(symbol):
    a = sympy.Wild('a', exclude=[symbol])
    b = sympy.Wild('b', exclude=[symbol])
    m = sympy.Wild('m', exclude=[symbol], properties=[lambda n: isinstance(n, sympy.Integer)])
    n = sympy.Wild('n', exclude=[symbol], properties=[lambda n: isinstance(n, sympy.Integer)])

    return a, b, m, n

@sympy.cacheit
def sincos_pattern(symbol):
    a, b, m, n = make_wilds(symbol)
    pattern = sympy.sin(a*symbol)**m * sympy.cos(b*symbol)**n

    return pattern, a, b, m, n

@sympy.cacheit
def tansec_pattern(symbol):
    a, b, m, n = make_wilds(symbol)
    pattern = sympy.tan(a*symbol)**m * sympy.sec(b*symbol)**n

    return pattern, a, b, m, n

@sympy.cacheit
def cotcsc_pattern(symbol):
    a, b, m, n = make_wilds(symbol)
    pattern = sympy.cot(a*symbol)**m * sympy.csc(b*symbol)**n

    return pattern, a, b, m, n

@sympy.cacheit
def heaviside_pattern(symbol):
    m = sympy.Wild('m', exclude=[symbol])
    b = sympy.Wild('b', exclude=[symbol])
    g = sympy.Wild('g')
    pattern = sympy.Heaviside(m*symbol + b) * g

    return pattern, m, b, g

def uncurry(func):
    def uncurry_rl(args):
        return func(*args)
    return uncurry_rl

def trig_rewriter(rewrite):
    def trig_rewriter_rl(args):
        a, b, m, n, integrand, symbol = args
        rewritten = rewrite(a, b, m, n, integrand, symbol)
        if rewritten != integrand:
            return RewriteRule(
                rewritten,
                integral_steps(rewritten, symbol),
                integrand, symbol)
    return trig_rewriter_rl

sincos_botheven_condition = uncurry(
    lambda a, b, m, n, i, s: m.is_even and n.is_even and
    m.is_nonnegative and n.is_nonnegative)

sincos_botheven = trig_rewriter(
    lambda a, b, m, n, i, symbol: ( (((1 - sympy.cos(2*a*symbol)) / 2) ** (m / 2)) *
                                    (((1 + sympy.cos(2*b*symbol)) / 2) ** (n / 2)) ))

sincos_sinodd_condition = uncurry(lambda a, b, m, n, i, s: m.is_odd and m >= 3)

sincos_sinodd = trig_rewriter(
    lambda a, b, m, n, i, symbol: ( (1 - sympy.cos(a*symbol)**2)**((m - 1) / 2) *
                                    sympy.sin(a*symbol) *
                                    sympy.cos(b*symbol) ** n))

sincos_cosodd_condition = uncurry(lambda a, b, m, n, i, s: n.is_odd and n >= 3)

sincos_cosodd = trig_rewriter(
    lambda a, b, m, n, i, symbol: ( (1 - sympy.sin(b*symbol)**2)**((n - 1) / 2) *
                                    sympy.cos(b*symbol) *
                                    sympy.sin(a*symbol) ** m))

tansec_seceven_condition = uncurry(lambda a, b, m, n, i, s: n.is_even and n >= 4)
tansec_seceven = trig_rewriter(
    lambda a, b, m, n, i, symbol: ( (1 + sympy.tan(b*symbol)**2) ** (n/2 - 1) *
                                    sympy.sec(b*symbol)**2 *
                                    sympy.tan(a*symbol) ** m ))

tansec_tanodd_condition = uncurry(lambda a, b, m, n, i, s: m.is_odd)
tansec_tanodd = trig_rewriter(
    lambda a, b, m, n, i, symbol: ( (sympy.sec(a*symbol)**2 - 1) ** ((m - 1) / 2) *
                                     sympy.tan(a*symbol) *
                                     sympy.sec(b*symbol) ** n ))

tan_tansquared_condition = uncurry(lambda a, b, m, n, i, s: m == 2 and n == 0)
tan_tansquared = trig_rewriter(
    lambda a, b, m, n, i, symbol: ( sympy.sec(a*symbol)**2 - 1))

cotcsc_csceven_condition = uncurry(lambda a, b, m, n, i, s: n.is_even and n >= 4)
cotcsc_csceven = trig_rewriter(
    lambda a, b, m, n, i, symbol: ( (1 + sympy.cot(b*symbol)**2) ** (n/2 - 1) *
                                    sympy.csc(b*symbol)**2 *
                                    sympy.cot(a*symbol) ** m ))

cotcsc_cotodd_condition = uncurry(lambda a, b, m, n, i, s: m.is_odd)
cotcsc_cotodd = trig_rewriter(
    lambda a, b, m, n, i, symbol: ( (sympy.csc(a*symbol)**2 - 1) ** ((m - 1) / 2) *
                                    sympy.cot(a*symbol) *
                                    sympy.csc(b*symbol) ** n ))

def trig_sincos_rule(integral):
    integrand, symbol = integral

    if any(integrand.has(f) for f in (sympy.sin, sympy.cos)):
        pattern, a, b, m, n = sincos_pattern(symbol)
        match = integrand.match(pattern)
        if not match:
            return

        return multiplexer({
            sincos_botheven_condition: sincos_botheven,
            sincos_sinodd_condition: sincos_sinodd,
            sincos_cosodd_condition: sincos_cosodd
        })(tuple(
            [match.get(i, ZERO) for i in (a, b, m, n)] +
            [integrand, symbol]))

def trig_tansec_rule(integral):
    integrand, symbol = integral

    integrand = integrand.subs({
        1 / sympy.cos(symbol): sympy.sec(symbol)
    })

    if any(integrand.has(f) for f in (sympy.tan, sympy.sec)):
        pattern, a, b, m, n = tansec_pattern(symbol)
        match = integrand.match(pattern)
        if not match:
            return

        return multiplexer({
            tansec_tanodd_condition: tansec_tanodd,
            tansec_seceven_condition: tansec_seceven,
            tan_tansquared_condition: tan_tansquared
        })(tuple(
            [match.get(i, ZERO) for i in (a, b, m, n)] +
            [integrand, symbol]))

def trig_cotcsc_rule(integral):
    integrand, symbol = integral
    integrand = integrand.subs({
        1 / sympy.sin(symbol): sympy.csc(symbol),
        1 / sympy.tan(symbol): sympy.cot(symbol),
        sympy.cos(symbol) / sympy.tan(symbol): sympy.cot(symbol)
    })

    if any(integrand.has(f) for f in (sympy.cot, sympy.csc)):
        pattern, a, b, m, n = cotcsc_pattern(symbol)
        match = integrand.match(pattern)
        if not match:
            return

        return multiplexer({
            cotcsc_cotodd_condition: cotcsc_cotodd,
            cotcsc_csceven_condition: cotcsc_csceven
        })(tuple(
            [match.get(i, ZERO) for i in (a, b, m, n)] +
            [integrand, symbol]))

def trig_sindouble_rule(integral):
    integrand, symbol = integral
    a = sympy.Wild('a', exclude=[sympy.sin(2*symbol)])
    match = integrand.match(sympy.sin(2*symbol)*a)
    if match:
        sin_double = 2*sympy.sin(symbol)*sympy.cos(symbol)/sympy.sin(2*symbol)
        return integral_steps(integrand * sin_double, symbol)

def trig_powers_products_rule(integral):
    return do_one(null_safe(trig_sincos_rule),
                  null_safe(trig_tansec_rule),
                  null_safe(trig_cotcsc_rule),
                  null_safe(trig_sindouble_rule))(integral)

def trig_substitution_rule(integral):
    integrand, symbol = integral
    A = sympy.Wild('a', exclude=[0, symbol])
    B = sympy.Wild('b', exclude=[0, symbol])
    theta = sympy.Dummy("theta")
    target_pattern = A + B*symbol**2

    matches = integrand.find(target_pattern)
    for expr in matches:
        match = expr.match(target_pattern)
        a = match.get(A, ZERO)
        b = match.get(B, ZERO)

        a_positive = ((a.is_number and a > 0) or a.is_positive)
        b_positive = ((b.is_number and b > 0) or b.is_positive)
        a_negative = ((a.is_number and a < 0) or a.is_negative)
        b_negative = ((b.is_number and b < 0) or b.is_negative)
        x_func = None
        if a_positive and b_positive:
            # a**2 + b*x**2. Assume sec(theta) > 0, -pi/2 < theta < pi/2
            x_func = (sympy.sqrt(a)/sympy.sqrt(b)) * sympy.tan(theta)
            # Do not restrict the domain: tan(theta) takes on any real
            # value on the interval -pi/2 < theta < pi/2 so x takes on
            # any value
            restriction = True
        elif a_positive and b_negative:
            # a**2 - b*x**2. Assume cos(theta) > 0, -pi/2 < theta < pi/2
            constant = sympy.sqrt(a)/sympy.sqrt(-b)
            x_func = constant * sympy.sin(theta)
            restriction = sympy.And(symbol > -constant, symbol < constant)
        elif a_negative and b_positive:
            # b*x**2 - a**2. Assume sin(theta) > 0, 0 < theta < pi
            constant = sympy.sqrt(-a)/sympy.sqrt(b)
            x_func = constant * sympy.sec(theta)
            restriction = sympy.And(symbol > -constant, symbol < constant)
        if x_func:
            # Manually simplify sqrt(trig(theta)**2) to trig(theta)
            # Valid due to assumed domain restriction
            substitutions = {}
            for f in [sympy.sin, sympy.cos, sympy.tan,
                      sympy.sec, sympy.csc, sympy.cot]:
                substitutions[sympy.sqrt(f(theta)**2)] = f(theta)
                substitutions[sympy.sqrt(f(theta)**(-2))] = 1/f(theta)

            replaced = integrand.subs(symbol, x_func).trigsimp()
            replaced = manual_subs(replaced, substitutions)
            if not replaced.has(symbol):
                replaced *= manual_diff(x_func, theta)
                replaced = replaced.trigsimp()
                secants = replaced.find(1/sympy.cos(theta))
                if secants:
                    replaced = replaced.xreplace({
                        1/sympy.cos(theta): sympy.sec(theta)
                    })

                substep = integral_steps(replaced, theta)
                if not contains_dont_know(substep):
                    return TrigSubstitutionRule(
                        theta, x_func, replaced, substep, restriction,
                        integrand, symbol)

def heaviside_rule(integral):
    integrand, symbol = integral
    pattern, m, b, g = heaviside_pattern(symbol)
    match = integrand.match(pattern)
    if match and 0 != match[g]:
        # f = Heaviside(m*x + b)*g
        v_step = integral_steps(match[g], symbol)
        result = _manualintegrate(v_step)
        m, b = match[m], match[b]
        return HeavisideRule(m*symbol + b, -b/m, result, integrand, symbol)

def substitution_rule(integral):
    integrand, symbol = integral

    u_var = sympy.Dummy("u")
    substitutions = find_substitutions(integrand, symbol, u_var)
    if substitutions:
        ways = []
        for u_func, c, substituted in substitutions:
            subrule = integral_steps(substituted, u_var)
            if contains_dont_know(subrule):
                continue

            if sympy.simplify(c - 1) != 0:
                _, denom = c.as_numer_denom()
                if subrule:
                    subrule = ConstantTimesRule(c, substituted, subrule, substituted, u_var)

                if denom.free_symbols:
                    piecewise = []
                    could_be_zero = []

                    if isinstance(denom, sympy.Mul):
                        could_be_zero = denom.args
                    else:
                        could_be_zero.append(denom)

                    for expr in could_be_zero:
                        if not fuzzy_not(expr.is_zero):
                            substep = integral_steps(manual_subs(integrand, expr, 0), symbol)

                            if substep:
                                piecewise.append((
                                    substep,
                                    sympy.Eq(expr, 0)
                                ))
                    piecewise.append((subrule, True))
                    subrule = PiecewiseRule(piecewise, substituted, symbol)

            ways.append(URule(u_var, u_func, c,
                              subrule,
                              integrand, symbol))

        if len(ways) > 1:
            return AlternativeRule(ways, integrand, symbol)
        elif ways:
            return ways[0]

    elif integrand.has(sympy.exp):
        u_func = sympy.exp(symbol)
        c = 1
        substituted = integrand / u_func.diff(symbol)
        substituted = substituted.subs(u_func, u_var)

        if symbol not in substituted.free_symbols:
            return URule(u_var, u_func, c,
                         integral_steps(substituted, u_var),
                         integrand, symbol)

partial_fractions_rule = rewriter(
    lambda integrand, symbol: integrand.is_rational_function(),
    lambda integrand, symbol: integrand.apart(symbol))

cancel_rule = rewriter(
    # lambda integrand, symbol: integrand.is_algebraic_expr(),
    # lambda integrand, symbol: isinstance(integrand, sympy.Mul),
    lambda integrand, symbol: True,
    lambda integrand, symbol: integrand.cancel())

distribute_expand_rule = rewriter(
    lambda integrand, symbol: (
        all(arg.is_Pow or arg.is_polynomial(symbol) for arg in integrand.args)
        or isinstance(integrand, sympy.Pow)
        or isinstance(integrand, sympy.Mul)),
    lambda integrand, symbol: integrand.expand())

trig_expand_rule = rewriter(
    # If there are trig functions with different arguments, expand them
    lambda integrand, symbol: (
        len(set(a.args[0] for a in integrand.atoms(TrigonometricFunction))) > 1),
    lambda integrand, symbol: integrand.expand(trig=True))

def derivative_rule(integral):
    integrand = integral[0]
    diff_variables = integrand.variables
    undifferentiated_function = integrand.expr
    integrand_variables = undifferentiated_function.free_symbols

    if integral.symbol in integrand_variables:
        if integral.symbol in diff_variables:
            return DerivativeRule(*integral)
        else:
            return DontKnowRule(integrand, integral.symbol)
    else:
        return ConstantRule(integral.integrand, *integral)

def rewrites_rule(integral):
    integrand, symbol = integral

    if integrand.match(1/sympy.cos(symbol)):
        rewritten = integrand.subs(1/sympy.cos(symbol), sympy.sec(symbol))
        return RewriteRule(rewritten, integral_steps(rewritten, symbol), integrand, symbol)

def fallback_rule(integral):
    return DontKnowRule(*integral)

# Cache is used to break cyclic integrals.
# Need to use the same dummy variable in cached expressions for them to match.
# Also record "u" of integration by parts, to avoid infinite repetition.
_integral_cache = {}
_parts_u_cache = defaultdict(int)
_cache_dummy = sympy.Dummy("z")

def integral_steps(integrand, symbol, **options):
    """Returns the steps needed to compute an integral.

    This function attempts to mirror what a student would do by hand as
    closely as possible.

    SymPy Gamma uses this to provide a step-by-step explanation of an
    integral. The code it uses to format the results of this function can be
    found at
    https://github.com/sympy/sympy_gamma/blob/master/app/logic/intsteps.py.

    Examples
    ========

    >>> from sympy import exp, sin, cos
    >>> from sympy.integrals.manualintegrate import integral_steps
    >>> from sympy.abc import x
    >>> print(repr(integral_steps(exp(x) / (1 + exp(2 * x)), x))) \
    # doctest: +NORMALIZE_WHITESPACE
    URule(u_var=_u, u_func=exp(x), constant=1,
    substep=PiecewiseRule(subfunctions=[(ArctanRule(a=1, b=1, c=1, context=1/(_u**2 + 1), symbol=_u), True),
        (ArccothRule(a=1, b=1, c=1, context=1/(_u**2 + 1), symbol=_u), False),
        (ArctanhRule(a=1, b=1, c=1, context=1/(_u**2 + 1), symbol=_u), False)],
    context=1/(_u**2 + 1), symbol=_u), context=exp(x)/(exp(2*x) + 1), symbol=x)
    >>> print(repr(integral_steps(sin(x), x))) \
    # doctest: +NORMALIZE_WHITESPACE
    TrigRule(func='sin', arg=x, context=sin(x), symbol=x)
    >>> print(repr(integral_steps((x**2 + 3)**2 , x))) \
    # doctest: +NORMALIZE_WHITESPACE
    RewriteRule(rewritten=x**4 + 6*x**2 + 9,
    substep=AddRule(substeps=[PowerRule(base=x, exp=4, context=x**4, symbol=x),
        ConstantTimesRule(constant=6, other=x**2,
            substep=PowerRule(base=x, exp=2, context=x**2, symbol=x),
                context=6*x**2, symbol=x),
        ConstantRule(constant=9, context=9, symbol=x)],
    context=x**4 + 6*x**2 + 9, symbol=x), context=(x**2 + 3)**2, symbol=x)


    Returns
    =======
    rule : namedtuple
        The first step; most rules have substeps that must also be
        considered. These substeps can be evaluated using ``manualintegrate``
        to obtain a result.

    """
    cachekey = integrand.xreplace({symbol: _cache_dummy})
    if cachekey in _integral_cache:
        if _integral_cache[cachekey] is None:
            # Stop this attempt, because it leads around in a loop
            return DontKnowRule(integrand, symbol)
        else:
            # TODO: This is for future development, as currently
            # _integral_cache gets no values other than None
            return (_integral_cache[cachekey].xreplace(_cache_dummy, symbol),
                symbol)
    else:
        _integral_cache[cachekey] = None

    integral = IntegralInfo(integrand, symbol)

    def key(integral):
        integrand = integral.integrand

        if isinstance(integrand, TrigonometricFunction):
            return TrigonometricFunction
        elif isinstance(integrand, sympy.Derivative):
            return sympy.Derivative
        elif symbol not in integrand.free_symbols:
            return sympy.Number
        else:
            for cls in (sympy.Pow, sympy.Symbol, sympy.exp, sympy.log,
                        sympy.Add, sympy.Mul, sympy.atan, sympy.asin,
                        sympy.acos, sympy.Heaviside, OrthogonalPolynomial):
                if isinstance(integrand, cls):
                    return cls


    def integral_is_subclass(*klasses):
        def _integral_is_subclass(integral):
            k = key(integral)
            return k and issubclass(k, klasses)
        return _integral_is_subclass

    result = do_one(
        null_safe(special_function_rule),
        null_safe(switch(key, {
            sympy.Pow: do_one(null_safe(power_rule), null_safe(inverse_trig_rule), \
                              null_safe(quadratic_denom_rule)),
            sympy.Symbol: power_rule,
            sympy.exp: exp_rule,
            sympy.Add: add_rule,
            sympy.Mul: do_one(null_safe(mul_rule), null_safe(trig_product_rule), \
                              null_safe(heaviside_rule), null_safe(quadratic_denom_rule), \
                              null_safe(root_mul_rule)),
            sympy.Derivative: derivative_rule,
            TrigonometricFunction: trig_rule,
            sympy.Heaviside: heaviside_rule,
            OrthogonalPolynomial: orthogonal_poly_rule,
            sympy.Number: constant_rule
        })),
        do_one(
            null_safe(trig_rule),
            null_safe(alternatives(
                rewrites_rule,
                substitution_rule,
                condition(
                    integral_is_subclass(sympy.Mul, sympy.Pow),
                    partial_fractions_rule),
                condition(
                    integral_is_subclass(sympy.Mul, sympy.Pow),
                    cancel_rule),
                condition(
                    integral_is_subclass(sympy.Mul, sympy.log, sympy.atan, sympy.asin, sympy.acos),
                    parts_rule),
                condition(
                    integral_is_subclass(sympy.Mul, sympy.Pow),
                    distribute_expand_rule),
                trig_powers_products_rule,
                trig_expand_rule
            )),
            null_safe(trig_substitution_rule)
        ),
        fallback_rule)(integral)
    del _integral_cache[cachekey]
    return result

@evaluates(ConstantRule)
def eval_constant(constant, integrand, symbol):
    return constant * symbol

@evaluates(ConstantTimesRule)
def eval_constanttimes(constant, other, substep, integrand, symbol):
    return constant * _manualintegrate(substep)

@evaluates(PowerRule)
def eval_power(base, exp, integrand, symbol):
    return sympy.Piecewise(
        ((base**(exp + 1))/(exp + 1), sympy.Ne(exp, -1)),
        (sympy.log(base), True),
        )

@evaluates(ExpRule)
def eval_exp(base, exp, integrand, symbol):
    return integrand / sympy.ln(base)

@evaluates(AddRule)
def eval_add(substeps, integrand, symbol):
    return sum(map(_manualintegrate, substeps))

@evaluates(URule)
def eval_u(u_var, u_func, constant, substep, integrand, symbol):
    result = _manualintegrate(substep)
    if u_func.is_Pow and u_func.exp == -1:
        # avoid needless -log(1/x) from substitution
        result = result.subs(sympy.log(u_var), -sympy.log(u_func.base))
    return result.subs(u_var, u_func)

@evaluates(PartsRule)
def eval_parts(u, dv, v_step, second_step, integrand, symbol):
    v = _manualintegrate(v_step)

    return u * v - _manualintegrate(second_step)

@evaluates(CyclicPartsRule)
def eval_cyclicparts(parts_rules, coefficient, integrand, symbol):
    coefficient = 1 - coefficient
    result = []

    sign = 1
    for rule in parts_rules:
        result.append(sign * rule.u * _manualintegrate(rule.v_step))
        sign *= -1

    return sympy.Add(*result) / coefficient

@evaluates(TrigRule)
def eval_trig(func, arg, integrand, symbol):
    if func == 'sin':
        return -sympy.cos(arg)
    elif func == 'cos':
        return sympy.sin(arg)
    elif func == 'sec*tan':
        return sympy.sec(arg)
    elif func == 'csc*cot':
        return sympy.csc(arg)
    elif func == 'sec**2':
        return sympy.tan(arg)
    elif func == 'csc**2':
        return -sympy.cot(arg)

@evaluates(ArctanRule)
def eval_arctan(a, b, c, integrand, symbol):
    return a / b * 1 / sympy.sqrt(c / b) * sympy.atan(symbol / sympy.sqrt(c / b))

@evaluates(ArccothRule)
def eval_arccoth(a, b, c, integrand, symbol):
    return - a / b * 1 / sympy.sqrt(-c / b) * sympy.acoth(symbol / sympy.sqrt(-c / b))

@evaluates(ArctanhRule)
def eval_arctanh(a, b, c, integrand, symbol):
    return - a / b * 1 / sympy.sqrt(-c / b) * sympy.atanh(symbol / sympy.sqrt(-c / b))

@evaluates(ReciprocalRule)
def eval_reciprocal(func, integrand, symbol):
    return sympy.ln(func)

@evaluates(ArcsinRule)
def eval_arcsin(integrand, symbol):
    return sympy.asin(symbol)

@evaluates(InverseHyperbolicRule)
def eval_inversehyperbolic(func, integrand, symbol):
    return func(symbol)

@evaluates(AlternativeRule)
def eval_alternative(alternatives, integrand, symbol):
    return _manualintegrate(alternatives[0])

@evaluates(RewriteRule)
def eval_rewrite(rewritten, substep, integrand, symbol):
    return _manualintegrate(substep)

@evaluates(PiecewiseRule)
def eval_piecewise(substeps, integrand, symbol):
    return sympy.Piecewise(*[(_manualintegrate(substep), cond)
                             for substep, cond in substeps])

@evaluates(TrigSubstitutionRule)
def eval_trigsubstitution(theta, func, rewritten, substep, restriction, integrand, symbol):
    func = func.subs(sympy.sec(theta), 1/sympy.cos(theta))

    trig_function = list(func.find(TrigonometricFunction))
    assert len(trig_function) == 1
    trig_function = trig_function[0]
    relation = sympy.solve(symbol - func, trig_function)
    assert len(relation) == 1
    numer, denom = sympy.fraction(relation[0])

    if isinstance(trig_function, sympy.sin):
        opposite = numer
        hypotenuse = denom
        adjacent = sympy.sqrt(denom**2 - numer**2)
        inverse = sympy.asin(relation[0])
    elif isinstance(trig_function, sympy.cos):
        adjacent = numer
        hypotenuse = denom
        opposite = sympy.sqrt(denom**2 - numer**2)
        inverse = sympy.acos(relation[0])
    elif isinstance(trig_function, sympy.tan):
        opposite = numer
        adjacent = denom
        hypotenuse = sympy.sqrt(denom**2 + numer**2)
        inverse = sympy.atan(relation[0])

    substitution = [
        (sympy.sin(theta), opposite/hypotenuse),
        (sympy.cos(theta), adjacent/hypotenuse),
        (sympy.tan(theta), opposite/adjacent),
        (theta, inverse)
    ]
    return sympy.Piecewise(
        (_manualintegrate(substep).subs(substitution).trigsimp(), restriction)
    )

@evaluates(DerivativeRule)
def eval_derivativerule(integrand, symbol):
    # isinstance(integrand, Derivative) should be True
    variable_count = list(integrand.variable_count)
    for i, (var, count) in enumerate(variable_count):
        if var == symbol:
            variable_count[i] = (var, count-1)
            break
    return sympy.Derivative(integrand.expr, *variable_count)

@evaluates(HeavisideRule)
def eval_heaviside(harg, ibnd, substep, integrand, symbol):
    # If we are integrating over x and the integrand has the form
    #       Heaviside(m*x+b)*g(x) == Heaviside(harg)*g(symbol)
    # then there needs to be continuity at -b/m == ibnd,
    # so we subtract the appropriate term.
    return sympy.Heaviside(harg)*(substep - substep.subs(symbol, ibnd))

@evaluates(JacobiRule)
def eval_jacobi(n, a, b, integrand, symbol):
    return Piecewise(
        (2*sympy.jacobi(n + 1, a - 1, b - 1, symbol)/(n + a + b), Ne(n + a + b, 0)),
        (symbol, Eq(n, 0)),
        ((a + b + 2)*symbol**2/4 + (a - b)*symbol/2, Eq(n, 1)))

@evaluates(GegenbauerRule)
def eval_gegenbauer(n, a, integrand, symbol):
    return Piecewise(
        (sympy.gegenbauer(n + 1, a - 1, symbol)/(2*(a - 1)), Ne(a, 1)),
        (sympy.chebyshevt(n + 1, symbol)/(n + 1), Ne(n, -1)),
        (sympy.S.Zero, True))

@evaluates(ChebyshevTRule)
def eval_chebyshevt(n, integrand, symbol):
    return Piecewise(((sympy.chebyshevt(n + 1, symbol)/(n + 1) -
        sympy.chebyshevt(n - 1, symbol)/(n - 1))/2, Ne(sympy.Abs(n), 1)),
        (symbol**2/2, True))

@evaluates(ChebyshevURule)
def eval_chebyshevu(n, integrand, symbol):
    return Piecewise(
        (sympy.chebyshevt(n + 1, symbol)/(n + 1), Ne(n, -1)),
        (sympy.S.Zero, True))

@evaluates(LegendreRule)
def eval_legendre(n, integrand, symbol):
    return (sympy.legendre(n + 1, symbol) - sympy.legendre(n - 1, symbol))/(2*n + 1)

@evaluates(HermiteRule)
def eval_hermite(n, integrand, symbol):
    return sympy.hermite(n + 1, symbol)/(2*(n + 1))

@evaluates(LaguerreRule)
def eval_laguerre(n, integrand, symbol):
    return sympy.laguerre(n, symbol) - sympy.laguerre(n + 1, symbol)

@evaluates(AssocLaguerreRule)
def eval_assoclaguerre(n, a, integrand, symbol):
    return -sympy.assoc_laguerre(n + 1, a - 1, symbol)

@evaluates(CiRule)
def eval_ci(a, b, integrand, symbol):
    return sympy.cos(b)*sympy.Ci(a*symbol) - sympy.sin(b)*sympy.Si(a*symbol)

@evaluates(ChiRule)
def eval_chi(a, b, integrand, symbol):
    return sympy.cosh(b)*sympy.Chi(a*symbol) + sympy.sinh(b)*sympy.Shi(a*symbol)

@evaluates(EiRule)
def eval_ei(a, b, integrand, symbol):
    return sympy.exp(b)*sympy.Ei(a*symbol)

@evaluates(SiRule)
def eval_si(a, b, integrand, symbol):
    return sympy.sin(b)*sympy.Ci(a*symbol) + sympy.cos(b)*sympy.Si(a*symbol)

@evaluates(ShiRule)
def eval_shi(a, b, integrand, symbol):
    return sympy.sinh(b)*sympy.Chi(a*symbol) + sympy.cosh(b)*sympy.Shi(a*symbol)

@evaluates(ErfRule)
def eval_erf(a, b, c, integrand, symbol):
    return Piecewise(
        (sympy.sqrt(sympy.pi/(-a))/2 * sympy.exp(c - b**2/(4*a)) *
            sympy.erf((-2*a*symbol - b)/(2*sympy.sqrt(-a))), a < 0),
        (sympy.sqrt(sympy.pi/a)/2 * sympy.exp(c - b**2/(4*a)) *
            sympy.erfi((2*a*symbol + b)/(2*sympy.sqrt(a))), True))

@evaluates(FresnelCRule)
def eval_fresnelc(a, b, c, integrand, symbol):
    return sympy.sqrt(sympy.pi/(2*a)) * (
        sympy.cos(b**2/(4*a) - c)*sympy.fresnelc((2*a*symbol + b)/sympy.sqrt(2*a*sympy.pi)) +
        sympy.sin(b**2/(4*a) - c)*sympy.fresnels((2*a*symbol + b)/sympy.sqrt(2*a*sympy.pi)))

@evaluates(FresnelSRule)
def eval_fresnels(a, b, c, integrand, symbol):
    return sympy.sqrt(sympy.pi/(2*a)) * (
        sympy.cos(b**2/(4*a) - c)*sympy.fresnels((2*a*symbol + b)/sympy.sqrt(2*a*sympy.pi)) -
        sympy.sin(b**2/(4*a) - c)*sympy.fresnelc((2*a*symbol + b)/sympy.sqrt(2*a*sympy.pi)))

@evaluates(LiRule)
def eval_li(a, b, integrand, symbol):
    return sympy.li(a*symbol + b)/a

@evaluates(PolylogRule)
def eval_polylog(a, b, integrand, symbol):
    return sympy.polylog(b + 1, a*symbol)

@evaluates(UpperGammaRule)
def eval_uppergamma(a, e, integrand, symbol):
    return symbol**e * (-a*symbol)**(-e) * sympy.uppergamma(e + 1, -a*symbol)/a

@evaluates(EllipticFRule)
def eval_elliptic_f(a, d, integrand, symbol):
    return sympy.elliptic_f(symbol, d/a)/sympy.sqrt(a)

@evaluates(EllipticERule)
def eval_elliptic_e(a, d, integrand, symbol):
    return sympy.elliptic_e(symbol, d/a)*sympy.sqrt(a)

@evaluates(DontKnowRule)
def eval_dontknowrule(integrand, symbol):
    return sympy.Integral(integrand, symbol)

def _manualintegrate(rule):
    evaluator = evaluators.get(rule.__class__)
    if not evaluator:

        raise ValueError("Cannot evaluate rule %s" % repr(rule))
    return evaluator(*rule)

def manualintegrate(f, var):
    """manualintegrate(f, var)

    Compute indefinite integral of a single variable using an algorithm that
    resembles what a student would do by hand.

    Unlike ``integrate``, var can only be a single symbol.

    Examples
    ========

    >>> from sympy import sin, cos, tan, exp, log, integrate
    >>> from sympy.integrals.manualintegrate import manualintegrate
    >>> from sympy.abc import x
    >>> manualintegrate(1 / x, x)
    log(x)
    >>> integrate(1/x)
    log(x)
    >>> manualintegrate(log(x), x)
    x*log(x) - x
    >>> integrate(log(x))
    x*log(x) - x
    >>> manualintegrate(exp(x) / (1 + exp(2 * x)), x)
    atan(exp(x))
    >>> integrate(exp(x) / (1 + exp(2 * x)))
    RootSum(4*_z**2 + 1, Lambda(_i, _i*log(2*_i + exp(x))))
    >>> manualintegrate(cos(x)**4 * sin(x), x)
    -cos(x)**5/5
    >>> integrate(cos(x)**4 * sin(x), x)
    -cos(x)**5/5
    >>> manualintegrate(cos(x)**4 * sin(x)**3, x)
    cos(x)**7/7 - cos(x)**5/5
    >>> integrate(cos(x)**4 * sin(x)**3, x)
    cos(x)**7/7 - cos(x)**5/5
    >>> manualintegrate(tan(x), x)
    -log(cos(x))
    >>> integrate(tan(x), x)
    -log(cos(x))

    See Also
    ========

    sympy.integrals.integrals.integrate
    sympy.integrals.integrals.Integral.doit
    sympy.integrals.integrals.Integral
    """
    result = _manualintegrate(integral_steps(f, var))
    # Clear the cache of u-parts
    _parts_u_cache.clear()
    # If we got Piecewise with two parts, put generic first
    if isinstance(result, Piecewise) and len(result.args) == 2:
        cond = result.args[0][1]
        if isinstance(cond, Eq) and result.args[1][1] == True:
            result = result.func(
                (result.args[1][0], sympy.Ne(*cond.args)),
                (result.args[0][0], True))
    return result
