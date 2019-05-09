'''
Rule Based Integration(RUBI) module in sympy uses set of transformation
rules to integrate an expression. All the transformation rules are compiled as a
discrimination-net which helps in matching expression with the rule efficiently.

Due to large number of rules, the module would normally take lot of time to load.
Hence, it is better to use Rubi while doing multiple integrations.

Rules are taken from Rubi version 4.10.8.

Note: This module has dependency on MatchPy library.

Basic Structure
===============
All rules in matchpy format are in rules folder. They are in separate files.
While matching a pattern, there are constraints that need to be checked.
These constraints are placed in a single file `constraints.py`.

A complete rule look like this:

```
def cons_f1(m, x):
    return FreeQ(m, x)
cons1 = CustomConstraint(cons_f1)

def cons_f2(m):
    return NonzeroQ(m + S(1))
cons2 = CustomConstraint(cons_f2)

pattern1 = Pattern(Integral(x_**WC('m', S(1)), x_), cons1, cons2)
def replacement1(m, x):
    rubi.append(1)
    return Simp(x**(m + S(1))/(m + S(1)), x)
rule1 = ReplacementRule(pattern1, replacement1)
```

As seen in the above example, a rule has 3 parts
1. Pattern with constraints. Expression is matched against this pattern.
2. Replacement function, which gives the resulting expression with which the original expression has to be replaced with.
   There is also `rubi.append(1)`. This (rubi) is a list which keeps track of rules applied to an expression.
   This can be accesed by `rules_applied` in `rubi.py`
3. Rule, which combines pattern and replacement function.
(For more details refer to matchpy documents)

Note:
The name of arguments of function for constraints and replacement should be taken care of.
They need to be exactly same as wildcard in the `Pattern`. Like, in the above example,
if `cons_f1` is written something like this:

```
def cons_f1(a, x):
    return FreeQ(a, x)
```
This is not going to work because in the Pattern, `m` has been used as a wildcard. So only thing is
naming of arguments matters.


TODO
====
* Use code generation to implement all rules.
* Testing of all the tests from rubi test suit. See: http://www.apmaths.uwo.ca/~arich/IntegrationProblems/MathematicaSyntaxFiles/MathematicaSyntaxFiles.html
* Add support for `Piecewise` functions.

Debugging
=========
When an integration is not successful. We can see which rule is matching the
expression by using `get_matching_rule_definition()` function. We can cross-check
if correct rule is being applied by evaluating the same expression in Mathematica.
If the applied rule is same, then we need to check the `ReplacementRule` and
the utility functions used in the `ReplacementRule`.

Parsing Rules and Tests
=======================
Code for parsing rule and tests are included in sympy.
They have been properly explained with steps in `sympy/integrals/rubi/parsetools/rubi_parsing_guide.md`.

Running Tests
=============
The tests for rubi in `rubi_tests` have been blacklisted as it takes a very long time to run all the tests.
To run a test run the following in a python terminal:
```
>>> import sympy
>>> sympy.test("rubi_tests", blacklist = []) # doctest: +SKIP
```
For specific tests like `test_sine.py` use this `sympy.test("rubi_tests/tests/test_sine.py", blacklist = [])`.

References
==========
[1] http://www.apmaths.uwo.ca/~arich/
[2] https://github.com/sympy/sympy/issues/7749
[3] https://github.com/sympy/sympy/pull/12978
'''
