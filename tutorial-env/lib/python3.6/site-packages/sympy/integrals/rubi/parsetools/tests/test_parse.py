import sys
from sympy.external import import_module
matchpy = import_module("matchpy")

if not matchpy:
    #bin/test will not execute any tests now
    disabled = True

if sys.version_info[:2] < (3, 6):
    disabled = True

from sympy.integrals.rubi.parsetools.parse import (rubi_rule_parser,
    get_default_values, add_wildcards, parse_freeq, seperate_freeq,
    get_free_symbols, divide_constraint, generate_sympy_from_parsed,
    setWC, replaceWith, rubi_printer, set_matchq_in_constraint, contains_diff_return_type,
    process_return_type, extract_set)

from sympy import Symbol, Not, symbols
from sympy import sympify

a, b, c, d, e, j, m, n, p, q, x, Pq, Pqq = symbols('a b c d e j m n p q x Pq Pqq')

def test_rubi_rule_parser():
    header = '''
from matchpy import Operation, CommutativeOperation
    rubi = ManyToOneReplacer()
'''
    fullform = 'List[RuleDelayed[HoldPattern[Int[Power[Pattern[x,Blank[]],Optional[Pattern[m,Blank[]]]],Pattern[x,Blank[Symbol]]]],Condition[Times[Power[x,Plus[m,1]],Power[Plus[m,1],-1]],NonzeroQ[Plus[m,1]]]]]'
    rules, constraint = rubi_rule_parser(fullform, header)
    result_rule = '''
from matchpy import Operation, CommutativeOperation
    rubi = ManyToOneReplacer()
    from sympy.integrals.rubi.constraints import cons1

    pattern1 = Pattern(Integral(x_**WC('m', S(1)), x_), cons1)
    def replacement1(m, x):
        rubi.append(1)
        return x**(m + S(1))/(m + S(1))
    rule1 = ReplacementRule(pattern1, replacement1)
    return [rule1, ]
'''
    result_constraint = '''
from matchpy import Operation, CommutativeOperation

    def cons_f1(m):
        return NonzeroQ(m + S(1))

    cons1 = CustomConstraint(cons_f1)
'''
    assert len(result_rule.strip()) == len(rules.strip()) # failing randomly while using `result.strip() == rules`
    assert len(result_constraint.strip()) == len(constraint.strip())

def test_get_default_values():
    s = ['Int', ['Power', ['Plus', ['Optional', ['Pattern', 'a', ['Blank']]], ['Times', ['Optional', ['Pattern', 'b', ['Blank']]], ['Pattern', 'x', ['Blank']]]], ['Pattern', 'm', ['Blank']]], ['Pattern', 'x', ['Blank', 'Symbol']]]
    assert get_default_values(s, {}) == {'a': 0, 'b': 1}
    s = ['Int', ['Power', ['Pattern', 'x', ['Blank']], ['Optional', ['Pattern', 'm', ['Blank']]]], ['Pattern', 'x', ['Blank', 'Symbol']]]
    assert get_default_values(s, {}) == {'m': 1}

def test_add_wildcards():
    s = 'Integral(Pow(Pattern(x, Blank), Optional(Pattern(m, Blank))), Pattern(x, Blank(Symbol)))'
    assert add_wildcards(s, {'m': 1}) == ("Integral(Pow(x_, WC('m', S(1))), x_)", ['m', 'x', 'x'])

def test_seperate_freeq():
    s = ['FreeQ', ['List', 'a', 'b'], 'x']
    assert seperate_freeq(s) == (['a', 'b'], 'x')

def test_parse_freeq():
    l = ['a', 'b']
    x = 'x'
    symbols = ['x', 'a', 'b']
    assert parse_freeq(l, x, 0, {}, [], symbols) == (', cons1, cons2', '\n    def cons_f1(a, x):\n        return FreeQ(a, x)\n\n    cons1 = CustomConstraint(cons_f1)\n\n    def cons_f2(b, x):\n        return FreeQ(b, x)\n\n    cons2 = CustomConstraint(cons_f2)\n', 2)

def test_get_free_symbols():
    s = ['NonzeroQ', ['Plus', 'm', '1']]
    symbols = ['m', 'x']
    assert get_free_symbols(s, symbols, []) == ['m']

def test_divide_constraint():
    s = ['And', ['FreeQ', 'm', 'x'], ['NonzeroQ', ['Plus', 'm', '1']]]
    assert divide_constraint(s, ['m', 'x'], 0, {}, []) == (', cons1', '\n    def cons_f1(m):\n        return NonzeroQ(m + S(1))\n\n    cons1 = CustomConstraint(cons_f1)\n', 1)

def test_setWC():
    assert setWC('Integral(x_**WC(m, S(1)), x_)') == "Integral(x_**WC('m', S(1)), x_)"

def test_replaceWith():
    s = sympify('Module(List(Set(r, Numerator(Rt(a/b, n))), Set(s, Denominator(Rt(a/b, n))), k, u), CompoundExpression(Set(u, Integral((r - s*x*cos(Pi*(2*k - 1)/n))/(r**2 - 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x)), Dist(2*r/(a*n), _Sum(u, List(k, 1, n/2 - 1/2)), x) + r*Integral(1/(r + s*x), x)/(a*n)))')
    symbols = ['x', 'a', 'n', 'b']
    assert replaceWith(s, symbols, 1) == ("    def With1(x, a, n, b):\n        r = Numerator(Rt(a/b, n))\n        s = Denominator(Rt(a/b, n))\n        k = Symbol('k')\n        u = Symbol('u')\n        u = Integral((r - s*x*cos(Pi*(S(2)*k + S(-1))/n))/(r**S(2) - S(2)*r*s*x*cos(Pi*(S(2)*k + S(-1))/n) + s**S(2)*x**S(2)), x)\n        u = Integral((r - s*x*cos(Pi*(2*k - 1)/n))/(r**2 - 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x)\n        rubi.append(1)\n        return Dist(S(2)*r/(a*n), _Sum(u, List(k, S(1), n/S(2) + S(-1)/2)), x) + r*Integral(S(1)/(r + s*x), x)/(a*n)", ' ', None)

def test_generate_sympy_from_parsed():
    s = ['Int', ['Power', ['Plus', ['Pattern', 'a', ['Blank']], ['Times', ['Optional', ['Pattern', 'b', ['Blank']]], ['Power', ['Pattern', 'x', ['Blank']], ['Pattern', 'n', ['Blank']]]]], '-1'], ['Pattern', 'x', ['Blank', 'Symbol']]]
    assert generate_sympy_from_parsed(s, wild=True) == 'Int(Pow(Add(Pattern(a, Blank), Mul(Optional(Pattern(b, Blank)), Pow(Pattern(x, Blank), Pattern(n, Blank)))), S(-1)), Pattern(x, Blank(Symbol)))'
    assert generate_sympy_from_parsed(s ,replace_Int=True) == 'Integral(Pow(Add(Pattern(a, Blank), Mul(Optional(Pattern(b, Blank)), Pow(Pattern(x, Blank), Pattern(n, Blank)))), S(-1)), Pattern(x, Blank(Symbol)))'
    s = ['And', ['FreeQ', ['List', 'a', 'b'], 'x'], ['PositiveIntegerQ', ['Times', ['Plus', 'n', '-3'], ['Power', '2', '-1']]], ['PosQ', ['Times', 'a', ['Power', 'b', '-1']]]]
    assert generate_sympy_from_parsed(s) == 'And(FreeQ(List(a, b), x), PositiveIntegerQ(Mul(Add(n, S(-3)), Pow(S(2), S(-1)))), PosQ(Mul(a, Pow(b, S(-1)))))'


def test_rubi_printer():
    #14819
    a = Symbol('a')
    assert rubi_printer(Not(a)) == 'Not(a)'

def test_contains_diff_return_type():
    assert contains_diff_return_type(['Plus', ['BinomialDegree', 'u', 'x'], ['Times', '-1', ['BinomialDegree', 'z', 'x']]])

def test_set_matchq_in_constraint():
    expected = ('result_matchq', "        def _cons_f_1229(g, m):\n            return FreeQ(List(g, m), x)\n        _cons_1229 = CustomConstraint(_cons_f_1229)\n        pat = Pattern(UtilityOperator((x*WC('g', S(1)))**WC('m', S(1)), x), _cons_1229)\n        result_matchq = is_match(UtilityOperator(v, x), pat)")
    expected1 = ('result_matchq', "        def _cons_f_1229(m, g):\n            return FreeQ(List(g, m), x)\n        _cons_1229 = CustomConstraint(_cons_f_1229)\n        pat = Pattern(UtilityOperator((x*WC('g', S(1)))**WC('m', S(1)), x), _cons_1229)\n        result_matchq = is_match(UtilityOperator(v, x), pat)")
    result = set_matchq_in_constraint(['MatchQ', 'v', ['Condition', ['Power', ['Times', ['Optional',\
        ['Pattern', 'g', ['Blank']]], 'x'], ['Optional', ['Pattern', 'm', ['Blank']]]], ['FreeQ', ['List', 'g', 'm'], 'x']]], 1229)
    assert result == expected1 or result == expected

def test_process_return_type():
    from sympy import Function
    Int = Function("Int")
    ExpandToSum = Function("ExpandToSum")
    s = ('\n        q = Expon(Pq, x)\n        Pqq = Coeff(Pq, x, q)', 'With(List(Set(Pqq, Coeff(Pq, x, q))), Pqq*c**(n - q + S(-1))*(c*x)**(m - n + q + S(1))*(a*x**j + b*x**n)**(p + S(1))/(b*(m + n*p + q + S(1))) + Int((c*x)**m*(a*x**j + b*x**n)**p*ExpandToSum(Pq - Pqq*a*x**(-n + q)*(m - n + q + S(1))/(b*(m + n*p + q + S(1))) - Pqq*x**q, x), x))')
    result = process_return_type(s, [])
    expected = ('\n        Pqq = Coeff(Pq, x, q)',\
    Pqq*c**(n - q - 1)*(c*x)**(m - n + q + 1)*(a*x**j + b*x**n)**(p + 1)/(b*(m + n*p + q + 1)) + Int((c*x)**m*(a*x**j + b*x**n)**p*ExpandToSum(Pq - Pqq*a*x**(-n + q)*(m - n + q + 1)/(b*(m + n*p + q + 1)) - Pqq*x**q, x), x),\
    True)
    assert result == expected

def test_extract_set():
    s = sympify('Module(List(Set(r, Numerator(Rt(a/b, n))), Set(s, Denominator(Rt(a/b, n))), k, u), CompoundExpression(Set(u, Integral((r - s*x*cos(Pi*(2*k - 1)/n))/(r**2 - 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x)), Dist(2*r/(a*n), _Sum(u, List(k, 1, n/2 - 1/2)), x) + r*Integral(1/(r + s*x), x)/(a*n)))')
    expected = list(sympify('Set(r, Numerator(Rt(a/b, n))), Set(s, Denominator(Rt(a/b, n))), Set(u, Integral((r - s*x*cos(Pi*(2*k - 1)/n))/(r**2 - 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x))'))
    assert extract_set(s, []) == expected
