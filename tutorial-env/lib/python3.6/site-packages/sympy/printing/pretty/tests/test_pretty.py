# -*- coding: utf-8 -*-
from sympy import (
    Add, And, Basic, Derivative, Dict, Eq, Equivalent, FF,
    FiniteSet, Function, Ge, Gt, I, Implies, Integral, SingularityFunction,
    Lambda, Le, Limit, Lt, Matrix, Mul, Nand, Ne, Nor, Not, O, Or,
    Pow, Product, QQ, RR, Rational, Ray, rootof, RootSum, S,
    Segment, Subs, Sum, Symbol, Tuple, Trace, Xor, ZZ, conjugate,
    groebner, oo, pi, symbols, ilex, grlex, Range, Contains,
    SeqPer, SeqFormula, SeqAdd, SeqMul, fourier_series, fps, ITE,
    Complement, Interval, Intersection, Union, EulerGamma, GoldenRatio)

from sympy.codegen.ast import (Assignment, AddAugmentedAssignment,
    SubAugmentedAssignment, MulAugmentedAssignment, DivAugmentedAssignment, ModAugmentedAssignment)
from sympy.core.compatibility import range, u_decode as u, PY3
from sympy.core.expr import UnevaluatedExpr
from sympy.core.trace import Tr

from sympy.functions import (Abs, Chi, Ci, Ei, KroneckerDelta,
    Piecewise, Shi, Si, atan2, beta, binomial, catalan, ceiling, cos,
    euler, exp, expint, factorial, factorial2, floor, gamma, hyper, log,
    meijerg, sin, sqrt, subfactorial, tan, uppergamma, lerchphi,
    elliptic_k, elliptic_f, elliptic_e, elliptic_pi, DiracDelta, bell,
    bernoulli, fibonacci, tribonacci, lucas)

from sympy.matrices import Adjoint, Inverse, MatrixSymbol, Transpose, KroneckerProduct

from sympy.physics import mechanics
from sympy.physics.units import joule, degree
from sympy.printing.pretty import pprint, pretty as xpretty
from sympy.printing.pretty.pretty_symbology import center_accent

from sympy.sets import ImageSet
from sympy.sets.setexpr import SetExpr
from sympy.tensor.array import (ImmutableDenseNDimArray, ImmutableSparseNDimArray,
                                MutableDenseNDimArray, MutableSparseNDimArray, tensorproduct)
from sympy.tensor.functions import TensorProduct
from sympy.tensor.tensor import (TensorIndexType, tensor_indices, tensorhead,
        TensorElement)

from sympy.utilities.pytest import raises, XFAIL

from sympy.vector import CoordSys3D, Gradient, Curl, Divergence, Dot, Cross, Laplacian



import sympy as sym
class lowergamma(sym.lowergamma):
    pass   # testing notation inheritance by a subclass with same name

a, b, c, d, x, y, z, k, n = symbols('a,b,c,d,x,y,z,k,n')
f = Function("f")
th = Symbol('theta')
ph = Symbol('phi')

"""
Expressions whose pretty-printing is tested here:
(A '#' to the right of an expression indicates that its various acceptable
orderings are accounted for by the tests.)


BASIC EXPRESSIONS:

oo
(x**2)
1/x
y*x**-2
x**Rational(-5,2)
(-2)**x
Pow(3, 1, evaluate=False)
(x**2 + x + 1)  #
1-x  #
1-2*x  #
x/y
-x/y
(x+2)/y  #
(1+x)*y  #3
-5*x/(x+10)  # correct placement of negative sign
1 - Rational(3,2)*(x+1)
-(-x + 5)*(-x - 2*sqrt(2) + 5) - (-y + 5)*(-y + 5) # issue 5524


ORDERING:

x**2 + x + 1
1 - x
1 - 2*x
2*x**4 + y**2 - x**2 + y**3


RELATIONAL:

Eq(x, y)
Lt(x, y)
Gt(x, y)
Le(x, y)
Ge(x, y)
Ne(x/(y+1), y**2)  #


RATIONAL NUMBERS:

y*x**-2
y**Rational(3,2) * x**Rational(-5,2)
sin(x)**3/tan(x)**2


FUNCTIONS (ABS, CONJ, EXP, FUNCTION BRACES, FACTORIAL, FLOOR, CEILING):

(2*x + exp(x))  #
Abs(x)
Abs(x/(x**2+1)) #
Abs(1 / (y - Abs(x)))
factorial(n)
factorial(2*n)
subfactorial(n)
subfactorial(2*n)
factorial(factorial(factorial(n)))
factorial(n+1) #
conjugate(x)
conjugate(f(x+1)) #
f(x)
f(x, y)
f(x/(y+1), y) #
f(x**x**x**x**x**x)
sin(x)**2
conjugate(a+b*I)
conjugate(exp(a+b*I))
conjugate( f(1 + conjugate(f(x))) ) #
f(x/(y+1), y)  # denom of first arg
floor(1 / (y - floor(x)))
ceiling(1 / (y - ceiling(x)))


SQRT:

sqrt(2)
2**Rational(1,3)
2**Rational(1,1000)
sqrt(x**2 + 1)
(1 + sqrt(5))**Rational(1,3)
2**(1/x)
sqrt(2+pi)
(2+(1+x**2)/(2+x))**Rational(1,4)+(1+x**Rational(1,1000))/sqrt(3+x**2)


DERIVATIVES:

Derivative(log(x), x, evaluate=False)
Derivative(log(x), x, evaluate=False) + x  #
Derivative(log(x) + x**2, x, y, evaluate=False)
Derivative(2*x*y, y, x, evaluate=False) + x**2  #
beta(alpha).diff(alpha)


INTEGRALS:

Integral(log(x), x)
Integral(x**2, x)
Integral((sin(x))**2 / (tan(x))**2)
Integral(x**(2**x), x)
Integral(x**2, (x,1,2))
Integral(x**2, (x,Rational(1,2),10))
Integral(x**2*y**2, x,y)
Integral(x**2, (x, None, 1))
Integral(x**2, (x, 1, None))
Integral(sin(th)/cos(ph), (th,0,pi), (ph, 0, 2*pi))


MATRICES:

Matrix([[x**2+1, 1], [y, x+y]])  #
Matrix([[x/y, y, th], [0, exp(I*k*ph), 1]])


PIECEWISE:

Piecewise((x,x<1),(x**2,True))

ITE:

ITE(x, y, z)

SEQUENCES (TUPLES, LISTS, DICTIONARIES):

()
[]
{}
(1/x,)
[x**2, 1/x, x, y, sin(th)**2/cos(ph)**2]
(x**2, 1/x, x, y, sin(th)**2/cos(ph)**2)
{x: sin(x)}
{1/x: 1/y, x: sin(x)**2}  #
[x**2]
(x**2,)
{x**2: 1}


LIMITS:

Limit(x, x, oo)
Limit(x**2, x, 0)
Limit(1/x, x, 0)
Limit(sin(x)/x, x, 0)


UNITS:

joule => kg*m**2/s


SUBS:

Subs(f(x), x, ph**2)
Subs(f(x).diff(x), x, 0)
Subs(f(x).diff(x)/y, (x, y), (0, Rational(1, 2)))


ORDER:

O(1)
O(1/x)
O(x**2 + y**2)

"""


def pretty(expr, order=None):
    """ASCII pretty-printing"""
    return xpretty(expr, order=order, use_unicode=False, wrap_line=False)


def upretty(expr, order=None):
    """Unicode pretty-printing"""
    return xpretty(expr, order=order, use_unicode=True, wrap_line=False)


def test_pretty_ascii_str():
    assert pretty( 'xxx' ) == 'xxx'
    assert pretty( "xxx" ) == 'xxx'
    assert pretty( 'xxx\'xxx' ) == 'xxx\'xxx'
    assert pretty( 'xxx"xxx' ) == 'xxx\"xxx'
    assert pretty( 'xxx\"xxx' ) == 'xxx\"xxx'
    assert pretty( "xxx'xxx" ) == 'xxx\'xxx'
    assert pretty( "xxx\'xxx" ) == 'xxx\'xxx'
    assert pretty( "xxx\"xxx" ) == 'xxx\"xxx'
    assert pretty( "xxx\"xxx\'xxx" ) == 'xxx"xxx\'xxx'
    assert pretty( "xxx\nxxx" ) == 'xxx\nxxx'


def test_pretty_unicode_str():
    assert pretty( u'xxx' ) == u'xxx'
    assert pretty( u'xxx' ) == u'xxx'
    assert pretty( u'xxx\'xxx' ) == u'xxx\'xxx'
    assert pretty( u'xxx"xxx' ) == u'xxx\"xxx'
    assert pretty( u'xxx\"xxx' ) == u'xxx\"xxx'
    assert pretty( u"xxx'xxx" ) == u'xxx\'xxx'
    assert pretty( u"xxx\'xxx" ) == u'xxx\'xxx'
    assert pretty( u"xxx\"xxx" ) == u'xxx\"xxx'
    assert pretty( u"xxx\"xxx\'xxx" ) == u'xxx"xxx\'xxx'
    assert pretty( u"xxx\nxxx" ) == u'xxx\nxxx'


def test_upretty_greek():
    assert upretty( oo ) == u'∞'
    assert upretty( Symbol('alpha^+_1') ) == u'α⁺₁'
    assert upretty( Symbol('beta') ) == u'β'
    assert upretty(Symbol('lambda')) == u'λ'


def test_upretty_multiindex():
    assert upretty( Symbol('beta12') ) == u'β₁₂'
    assert upretty( Symbol('Y00') ) == u'Y₀₀'
    assert upretty( Symbol('Y_00') ) == u'Y₀₀'
    assert upretty( Symbol('F^+-') ) == u'F⁺⁻'


def test_upretty_sub_super():
    assert upretty( Symbol('beta_1_2') ) == u'β₁ ₂'
    assert upretty( Symbol('beta^1^2') ) == u'β¹ ²'
    assert upretty( Symbol('beta_1^2') ) == u'β²₁'
    assert upretty( Symbol('beta_10_20') ) == u'β₁₀ ₂₀'
    assert upretty( Symbol('beta_ax_gamma^i') ) == u'βⁱₐₓ ᵧ'
    assert upretty( Symbol("F^1^2_3_4") ) == u'F¹ ²₃ ₄'
    assert upretty( Symbol("F_1_2^3^4") ) == u'F³ ⁴₁ ₂'
    assert upretty( Symbol("F_1_2_3_4") ) == u'F₁ ₂ ₃ ₄'
    assert upretty( Symbol("F^1^2^3^4") ) == u'F¹ ² ³ ⁴'


def test_upretty_subs_missing_in_24():
    assert upretty( Symbol('F_beta') ) == u'Fᵦ'
    assert upretty( Symbol('F_gamma') ) == u'Fᵧ'
    assert upretty( Symbol('F_rho') ) == u'Fᵨ'
    assert upretty( Symbol('F_phi') ) == u'Fᵩ'
    assert upretty( Symbol('F_chi') ) == u'Fᵪ'

    assert upretty( Symbol('F_a') ) == u'Fₐ'
    assert upretty( Symbol('F_e') ) == u'Fₑ'
    assert upretty( Symbol('F_i') ) == u'Fᵢ'
    assert upretty( Symbol('F_o') ) == u'Fₒ'
    assert upretty( Symbol('F_u') ) == u'Fᵤ'
    assert upretty( Symbol('F_r') ) == u'Fᵣ'
    assert upretty( Symbol('F_v') ) == u'Fᵥ'
    assert upretty( Symbol('F_x') ) == u'Fₓ'


def test_missing_in_2X_issue_9047():
    if PY3:
        assert upretty( Symbol('F_h') ) == u'Fₕ'
        assert upretty( Symbol('F_k') ) == u'Fₖ'
        assert upretty( Symbol('F_l') ) == u'Fₗ'
        assert upretty( Symbol('F_m') ) == u'Fₘ'
        assert upretty( Symbol('F_n') ) == u'Fₙ'
        assert upretty( Symbol('F_p') ) == u'Fₚ'
        assert upretty( Symbol('F_s') ) == u'Fₛ'
        assert upretty( Symbol('F_t') ) == u'Fₜ'


def test_upretty_modifiers():
    # Accents
    assert upretty( Symbol('Fmathring') ) == u'F̊'
    assert upretty( Symbol('Fddddot') ) == u'F⃜'
    assert upretty( Symbol('Fdddot') ) == u'F⃛'
    assert upretty( Symbol('Fddot') ) == u'F̈'
    assert upretty( Symbol('Fdot') ) == u'Ḟ'
    assert upretty( Symbol('Fcheck') ) == u'F̌'
    assert upretty( Symbol('Fbreve') ) == u'F̆'
    assert upretty( Symbol('Facute') ) == u'F́'
    assert upretty( Symbol('Fgrave') ) == u'F̀'
    assert upretty( Symbol('Ftilde') ) == u'F̃'
    assert upretty( Symbol('Fhat') ) == u'F̂'
    assert upretty( Symbol('Fbar') ) == u'F̅'
    assert upretty( Symbol('Fvec') ) == u'F⃗'
    assert upretty( Symbol('Fprime') ) == u'F′'
    assert upretty( Symbol('Fprm') ) == u'F′'
    # No faces are actually implemented, but test to make sure the modifiers are stripped
    assert upretty( Symbol('Fbold') ) == u'Fbold'
    assert upretty( Symbol('Fbm') ) == u'Fbm'
    assert upretty( Symbol('Fcal') ) == u'Fcal'
    assert upretty( Symbol('Fscr') ) == u'Fscr'
    assert upretty( Symbol('Ffrak') ) == u'Ffrak'
    # Brackets
    assert upretty( Symbol('Fnorm') ) == u'‖F‖'
    assert upretty( Symbol('Favg') ) == u'⟨F⟩'
    assert upretty( Symbol('Fabs') ) == u'|F|'
    assert upretty( Symbol('Fmag') ) == u'|F|'
    # Combinations
    assert upretty( Symbol('xvecdot') ) == u'x⃗̇'
    assert upretty( Symbol('xDotVec') ) == u'ẋ⃗'
    assert upretty( Symbol('xHATNorm') ) == u'‖x̂‖'
    assert upretty( Symbol('xMathring_yCheckPRM__zbreveAbs') ) == u'x̊_y̌′__|z̆|'
    assert upretty( Symbol('alphadothat_nVECDOT__tTildePrime') ) == u'α̇̂_n⃗̇__t̃′'
    assert upretty( Symbol('x_dot') ) == u'x_dot'
    assert upretty( Symbol('x__dot') ) == u'x__dot'


def test_pretty_Cycle():
    from sympy.combinatorics.permutations import Cycle
    assert pretty(Cycle(1, 2)) == '(1 2)'
    assert pretty(Cycle(2)) == '(2)'
    assert pretty(Cycle(1, 3)(4, 5)) == '(1 3)(4 5)'
    assert pretty(Cycle()) == '()'


def test_pretty_basic():
    assert pretty( -Rational(1)/2 ) == '-1/2'
    assert pretty( -Rational(13)/22 ) == \
"""\
-13 \n\
----\n\
 22 \
"""
    expr = oo
    ascii_str = \
"""\
oo\
"""
    ucode_str = \
u("""\
∞\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (x**2)
    ascii_str = \
"""\
 2\n\
x \
"""
    ucode_str = \
u("""\
 2\n\
x \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = 1/x
    ascii_str = \
"""\
1\n\
-\n\
x\
"""
    ucode_str = \
u("""\
1\n\
─\n\
x\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    # not the same as 1/x
    expr = x**-1.0
    ascii_str = \
"""\
 -1.0\n\
x    \
"""
    ucode_str = \
("""\
 -1.0\n\
x    \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    # see issue #2860
    expr = Pow(S(2), -1.0, evaluate=False)
    ascii_str = \
"""\
 -1.0\n\
2    \
"""
    ucode_str = \
("""\
 -1.0\n\
2    \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = y*x**-2
    ascii_str = \
"""\
y \n\
--\n\
 2\n\
x \
"""
    ucode_str = \
u("""\
y \n\
──\n\
 2\n\
x \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    #see issue #14033
    expr = x**Rational(1, 3)
    ascii_str = \
"""\
 1/3\n\
x   \
"""
    ucode_str = \
u("""\
 1/3\n\
x   \
""")
    assert xpretty(expr, use_unicode=False, wrap_line=False,\
    root_notation = False) == ascii_str
    assert xpretty(expr, use_unicode=True, wrap_line=False,\
    root_notation = False) == ucode_str

    expr = x**Rational(-5, 2)
    ascii_str = \
"""\
 1  \n\
----\n\
 5/2\n\
x   \
"""
    ucode_str = \
u("""\
 1  \n\
────\n\
 5/2\n\
x   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (-2)**x
    ascii_str = \
"""\
    x\n\
(-2) \
"""
    ucode_str = \
u("""\
    x\n\
(-2) \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    # See issue 4923
    expr = Pow(3, 1, evaluate=False)
    ascii_str = \
"""\
 1\n\
3 \
"""
    ucode_str = \
u("""\
 1\n\
3 \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (x**2 + x + 1)
    ascii_str_1 = \
"""\
         2\n\
1 + x + x \
"""
    ascii_str_2 = \
"""\
 2        \n\
x  + x + 1\
"""
    ascii_str_3 = \
"""\
 2        \n\
x  + 1 + x\
"""
    ucode_str_1 = \
u("""\
         2\n\
1 + x + x \
""")
    ucode_str_2 = \
u("""\
 2        \n\
x  + x + 1\
""")
    ucode_str_3 = \
u("""\
 2        \n\
x  + 1 + x\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2, ascii_str_3]
    assert upretty(expr) in [ucode_str_1, ucode_str_2, ucode_str_3]

    expr = 1 - x
    ascii_str_1 = \
"""\
1 - x\
"""
    ascii_str_2 = \
"""\
-x + 1\
"""
    ucode_str_1 = \
u("""\
1 - x\
""")
    ucode_str_2 = \
u("""\
-x + 1\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = 1 - 2*x
    ascii_str_1 = \
"""\
1 - 2*x\
"""
    ascii_str_2 = \
"""\
-2*x + 1\
"""
    ucode_str_1 = \
u("""\
1 - 2⋅x\
""")
    ucode_str_2 = \
u("""\
-2⋅x + 1\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = x/y
    ascii_str = \
"""\
x\n\
-\n\
y\
"""
    ucode_str = \
u("""\
x\n\
─\n\
y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = -x/y
    ascii_str = \
"""\
-x \n\
---\n\
 y \
"""
    ucode_str = \
u("""\
-x \n\
───\n\
 y \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (x + 2)/y
    ascii_str_1 = \
"""\
2 + x\n\
-----\n\
  y  \
"""
    ascii_str_2 = \
"""\
x + 2\n\
-----\n\
  y  \
"""
    ucode_str_1 = \
u("""\
2 + x\n\
─────\n\
  y  \
""")
    ucode_str_2 = \
u("""\
x + 2\n\
─────\n\
  y  \
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = (1 + x)*y
    ascii_str_1 = \
"""\
y*(1 + x)\
"""
    ascii_str_2 = \
"""\
(1 + x)*y\
"""
    ascii_str_3 = \
"""\
y*(x + 1)\
"""
    ucode_str_1 = \
u("""\
y⋅(1 + x)\
""")
    ucode_str_2 = \
u("""\
(1 + x)⋅y\
""")
    ucode_str_3 = \
u("""\
y⋅(x + 1)\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2, ascii_str_3]
    assert upretty(expr) in [ucode_str_1, ucode_str_2, ucode_str_3]

    # Test for correct placement of the negative sign
    expr = -5*x/(x + 10)
    ascii_str_1 = \
"""\
-5*x  \n\
------\n\
10 + x\
"""
    ascii_str_2 = \
"""\
-5*x  \n\
------\n\
x + 10\
"""
    ucode_str_1 = \
u("""\
-5⋅x  \n\
──────\n\
10 + x\
""")
    ucode_str_2 = \
u("""\
-5⋅x  \n\
──────\n\
x + 10\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = -S(1)/2 - 3*x
    ascii_str = \
"""\
-3*x - 1/2\
"""
    ucode_str = \
u("""\
-3⋅x - 1/2\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = S(1)/2 - 3*x
    ascii_str = \
"""\
1/2 - 3*x\
"""
    ucode_str = \
u("""\
1/2 - 3⋅x\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = -S(1)/2 - 3*x/2
    ascii_str = \
"""\
  3*x   1\n\
- --- - -\n\
   2    2\
"""
    ucode_str = \
u("""\
  3⋅x   1\n\
- ─── - ─\n\
   2    2\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = S(1)/2 - 3*x/2
    ascii_str = \
"""\
1   3*x\n\
- - ---\n\
2    2 \
"""
    ucode_str = \
u("""\
1   3⋅x\n\
─ - ───\n\
2    2 \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_negative_fractions():
    expr = -x/y
    ascii_str =\
"""\
-x \n\
---\n\
 y \
"""
    ucode_str =\
u("""\
-x \n\
───\n\
 y \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str
    expr = -x*z/y
    ascii_str =\
"""\
-x*z \n\
-----\n\
  y  \
"""
    ucode_str =\
u("""\
-x⋅z \n\
─────\n\
  y  \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str
    expr = x**2/y
    ascii_str =\
"""\
 2\n\
x \n\
--\n\
y \
"""
    ucode_str =\
u("""\
 2\n\
x \n\
──\n\
y \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str
    expr = -x**2/y
    ascii_str =\
"""\
  2 \n\
-x  \n\
----\n\
 y  \
"""
    ucode_str =\
u("""\
  2 \n\
-x  \n\
────\n\
 y  \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str
    expr = -x/(y*z)
    ascii_str =\
"""\
-x \n\
---\n\
y*z\
"""
    ucode_str =\
u("""\
-x \n\
───\n\
y⋅z\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str
    expr = -a/y**2
    ascii_str =\
"""\
-a \n\
---\n\
  2\n\
 y \
"""
    ucode_str =\
u("""\
-a \n\
───\n\
  2\n\
 y \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str
    expr = y**(-a/b)
    ascii_str =\
"""\
 -a \n\
 ---\n\
  b \n\
y   \
"""
    ucode_str =\
u("""\
 -a \n\
 ───\n\
  b \n\
y   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str
    expr = -1/y**2
    ascii_str =\
"""\
-1 \n\
---\n\
  2\n\
 y \
"""
    ucode_str =\
u("""\
-1 \n\
───\n\
  2\n\
 y \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str
    expr = -10/b**2
    ascii_str =\
"""\
-10 \n\
----\n\
  2 \n\
 b  \
"""
    ucode_str =\
u("""\
-10 \n\
────\n\
  2 \n\
 b  \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str
    expr = Rational(-200, 37)
    ascii_str =\
"""\
-200 \n\
-----\n\
  37 \
"""
    ucode_str =\
u("""\
-200 \n\
─────\n\
  37 \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

def test_issue_5524():
    assert pretty(-(-x + 5)*(-x - 2*sqrt(2) + 5) - (-y + 5)*(-y + 5)) == \
"""\
         2           /         ___    \\\n\
- (5 - y)  + (x - 5)*\\-x - 2*\\/ 2  + 5/\
"""

    assert upretty(-(-x + 5)*(-x - 2*sqrt(2) + 5) - (-y + 5)*(-y + 5)) == \
u("""\
         2                          \n\
- (5 - y)  + (x - 5)⋅(-x - 2⋅√2 + 5)\
""")

def test_pretty_ordering():
    assert pretty(x**2 + x + 1, order='lex') == \
"""\
 2        \n\
x  + x + 1\
"""
    assert pretty(x**2 + x + 1, order='rev-lex') == \
"""\
         2\n\
1 + x + x \
"""
    assert pretty(1 - x, order='lex') == '-x + 1'
    assert pretty(1 - x, order='rev-lex') == '1 - x'

    assert pretty(1 - 2*x, order='lex') == '-2*x + 1'
    assert pretty(1 - 2*x, order='rev-lex') == '1 - 2*x'

    f = 2*x**4 + y**2 - x**2 + y**3
    assert pretty(f, order=None) == \
"""\
   4    2    3    2\n\
2*x  - x  + y  + y \
"""
    assert pretty(f, order='lex') == \
"""\
   4    2    3    2\n\
2*x  - x  + y  + y \
"""
    assert pretty(f, order='rev-lex') == \
"""\
 2    3    2      4\n\
y  + y  - x  + 2*x \
"""

    expr = x - x**3/6 + x**5/120 + O(x**6)
    ascii_str = \
"""\
     3     5        \n\
    x     x     / 6\\\n\
x - -- + --- + O\\x /\n\
    6    120        \
"""
    ucode_str = \
u("""\
     3     5        \n\
    x     x     ⎛ 6⎞\n\
x - ── + ─── + O⎝x ⎠\n\
    6    120        \
""")
    assert pretty(expr, order=None) == ascii_str
    assert upretty(expr, order=None) == ucode_str

    assert pretty(expr, order='lex') == ascii_str
    assert upretty(expr, order='lex') == ucode_str

    assert pretty(expr, order='rev-lex') == ascii_str
    assert upretty(expr, order='rev-lex') == ucode_str

def test_EulerGamma():
    assert pretty(EulerGamma) == str(EulerGamma) == "EulerGamma"
    assert upretty(EulerGamma) == u"γ"

def test_GoldenRatio():
    assert pretty(GoldenRatio) == str(GoldenRatio) == "GoldenRatio"
    assert upretty(GoldenRatio) == u"φ"

def test_pretty_relational():
    expr = Eq(x, y)
    ascii_str = \
"""\
x = y\
"""
    ucode_str = \
u("""\
x = y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Lt(x, y)
    ascii_str = \
"""\
x < y\
"""
    ucode_str = \
u("""\
x < y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Gt(x, y)
    ascii_str = \
"""\
x > y\
"""
    ucode_str = \
u("""\
x > y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Le(x, y)
    ascii_str = \
"""\
x <= y\
"""
    ucode_str = \
u("""\
x ≤ y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Ge(x, y)
    ascii_str = \
"""\
x >= y\
"""
    ucode_str = \
u("""\
x ≥ y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Ne(x/(y + 1), y**2)
    ascii_str_1 = \
"""\
  x       2\n\
----- != y \n\
1 + y      \
"""
    ascii_str_2 = \
"""\
  x       2\n\
----- != y \n\
y + 1      \
"""
    ucode_str_1 = \
u("""\
  x      2\n\
───── ≠ y \n\
1 + y     \
""")
    ucode_str_2 = \
u("""\
  x      2\n\
───── ≠ y \n\
y + 1     \
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

def test_Assignment():
    expr = Assignment(x, y)
    ascii_str = \
"""\
x := y\
"""
    ucode_str = \
u("""\
x := y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

def test_AugmentedAssignment():
    expr = AddAugmentedAssignment(x, y)
    ascii_str = \
"""\
x += y\
"""
    ucode_str = \
u("""\
x += y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = SubAugmentedAssignment(x, y)
    ascii_str = \
"""\
x -= y\
"""
    ucode_str = \
u("""\
x -= y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = MulAugmentedAssignment(x, y)
    ascii_str = \
"""\
x *= y\
"""
    ucode_str = \
u("""\
x *= y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = DivAugmentedAssignment(x, y)
    ascii_str = \
"""\
x /= y\
"""
    ucode_str = \
u("""\
x /= y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = ModAugmentedAssignment(x, y)
    ascii_str = \
"""\
x %= y\
"""
    ucode_str = \
u("""\
x %= y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

def test_issue_7117():
    # See also issue #5031 (hence the evaluate=False in these).
    e = Eq(x + 1, x/2)
    q = Mul(2, e, evaluate=False)
    assert upretty(q) == u("""\
  ⎛        x⎞\n\
2⋅⎜x + 1 = ─⎟\n\
  ⎝        2⎠\
""")
    q = Add(e, 6, evaluate=False)
    assert upretty(q) == u("""\
    ⎛        x⎞\n\
6 + ⎜x + 1 = ─⎟\n\
    ⎝        2⎠\
""")
    q = Pow(e, 2, evaluate=False)
    assert upretty(q) == u("""\
           2\n\
⎛        x⎞ \n\
⎜x + 1 = ─⎟ \n\
⎝        2⎠ \
""")
    e2 = Eq(x, 2)
    q = Mul(e, e2, evaluate=False)
    assert upretty(q) == u("""\
⎛        x⎞        \n\
⎜x + 1 = ─⎟⋅(x = 2)\n\
⎝        2⎠        \
""")


def test_pretty_rational():
    expr = y*x**-2
    ascii_str = \
"""\
y \n\
--\n\
 2\n\
x \
"""
    ucode_str = \
u("""\
y \n\
──\n\
 2\n\
x \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = y**Rational(3, 2) * x**Rational(-5, 2)
    ascii_str = \
"""\
 3/2\n\
y   \n\
----\n\
 5/2\n\
x   \
"""
    ucode_str = \
u("""\
 3/2\n\
y   \n\
────\n\
 5/2\n\
x   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = sin(x)**3/tan(x)**2
    ascii_str = \
"""\
   3   \n\
sin (x)\n\
-------\n\
   2   \n\
tan (x)\
"""
    ucode_str = \
u("""\
   3   \n\
sin (x)\n\
───────\n\
   2   \n\
tan (x)\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_functions():
    """Tests for Abs, conjugate, exp, function braces, and factorial."""
    expr = (2*x + exp(x))
    ascii_str_1 = \
"""\
       x\n\
2*x + e \
"""
    ascii_str_2 = \
"""\
 x      \n\
e  + 2*x\
"""
    ucode_str_1 = \
u("""\
       x\n\
2⋅x + ℯ \
""")
    ucode_str_2 = \
u("""\
 x     \n\
ℯ + 2⋅x\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = Abs(x)
    ascii_str = \
"""\
|x|\
"""
    ucode_str = \
u("""\
│x│\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Abs(x/(x**2 + 1))
    ascii_str_1 = \
"""\
|  x   |\n\
|------|\n\
|     2|\n\
|1 + x |\
"""
    ascii_str_2 = \
"""\
|  x   |\n\
|------|\n\
| 2    |\n\
|x  + 1|\
"""
    ucode_str_1 = \
u("""\
│  x   │\n\
│──────│\n\
│     2│\n\
│1 + x │\
""")
    ucode_str_2 = \
u("""\
│  x   │\n\
│──────│\n\
│ 2    │\n\
│x  + 1│\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = Abs(1 / (y - Abs(x)))
    ascii_str = \
"""\
|   1   |\n\
|-------|\n\
|y - |x||\
"""
    ucode_str = \
u("""\
│   1   │\n\
│───────│\n\
│y - │x││\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    n = Symbol('n', integer=True)
    expr = factorial(n)
    ascii_str = \
"""\
n!\
"""
    ucode_str = \
u("""\
n!\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = factorial(2*n)
    ascii_str = \
"""\
(2*n)!\
"""
    ucode_str = \
u("""\
(2⋅n)!\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = factorial(factorial(factorial(n)))
    ascii_str = \
"""\
((n!)!)!\
"""
    ucode_str = \
u("""\
((n!)!)!\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = factorial(n + 1)
    ascii_str_1 = \
"""\
(1 + n)!\
"""
    ascii_str_2 = \
"""\
(n + 1)!\
"""
    ucode_str_1 = \
u("""\
(1 + n)!\
""")
    ucode_str_2 = \
u("""\
(n + 1)!\
""")

    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = subfactorial(n)
    ascii_str = \
"""\
!n\
"""
    ucode_str = \
u("""\
!n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = subfactorial(2*n)
    ascii_str = \
"""\
!(2*n)\
"""
    ucode_str = \
u("""\
!(2⋅n)\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    n = Symbol('n', integer=True)
    expr = factorial2(n)
    ascii_str = \
"""\
n!!\
"""
    ucode_str = \
u("""\
n!!\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = factorial2(2*n)
    ascii_str = \
"""\
(2*n)!!\
"""
    ucode_str = \
u("""\
(2⋅n)!!\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = factorial2(factorial2(factorial2(n)))
    ascii_str = \
"""\
((n!!)!!)!!\
"""
    ucode_str = \
u("""\
((n!!)!!)!!\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = factorial2(n + 1)
    ascii_str_1 = \
"""\
(1 + n)!!\
"""
    ascii_str_2 = \
"""\
(n + 1)!!\
"""
    ucode_str_1 = \
u("""\
(1 + n)!!\
""")
    ucode_str_2 = \
u("""\
(n + 1)!!\
""")

    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = 2*binomial(n, k)
    ascii_str = \
"""\
  /n\\\n\
2*| |\n\
  \\k/\
"""
    ucode_str = \
u("""\
  ⎛n⎞\n\
2⋅⎜ ⎟\n\
  ⎝k⎠\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = 2*binomial(2*n, k)
    ascii_str = \
"""\
  /2*n\\\n\
2*|   |\n\
  \\ k /\
"""
    ucode_str = \
u("""\
  ⎛2⋅n⎞\n\
2⋅⎜   ⎟\n\
  ⎝ k ⎠\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = 2*binomial(n**2, k)
    ascii_str = \
"""\
  / 2\\\n\
  |n |\n\
2*|  |\n\
  \\k /\
"""
    ucode_str = \
u("""\
  ⎛ 2⎞\n\
  ⎜n ⎟\n\
2⋅⎜  ⎟\n\
  ⎝k ⎠\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = catalan(n)
    ascii_str = \
"""\
C \n\
 n\
"""
    ucode_str = \
u("""\
C \n\
 n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = catalan(n)
    ascii_str = \
"""\
C \n\
 n\
"""
    ucode_str = \
u("""\
C \n\
 n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = bell(n)
    ascii_str = \
"""\
B \n\
 n\
"""
    ucode_str = \
u("""\
B \n\
 n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = bernoulli(n)
    ascii_str = \
"""\
B \n\
 n\
"""
    ucode_str = \
u("""\
B \n\
 n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = fibonacci(n)
    ascii_str = \
"""\
F \n\
 n\
"""
    ucode_str = \
u("""\
F \n\
 n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = lucas(n)
    ascii_str = \
"""\
L \n\
 n\
"""
    ucode_str = \
u("""\
L \n\
 n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = tribonacci(n)
    ascii_str = \
"""\
T \n\
 n\
"""
    ucode_str = \
u("""\
T \n\
 n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = conjugate(x)
    ascii_str = \
"""\
_\n\
x\
"""
    ucode_str = \
u("""\
_\n\
x\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    f = Function('f')
    expr = conjugate(f(x + 1))
    ascii_str_1 = \
"""\
________\n\
f(1 + x)\
"""
    ascii_str_2 = \
"""\
________\n\
f(x + 1)\
"""
    ucode_str_1 = \
u("""\
________\n\
f(1 + x)\
""")
    ucode_str_2 = \
u("""\
________\n\
f(x + 1)\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = f(x)
    ascii_str = \
"""\
f(x)\
"""
    ucode_str = \
u("""\
f(x)\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = f(x, y)
    ascii_str = \
"""\
f(x, y)\
"""
    ucode_str = \
u("""\
f(x, y)\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = f(x/(y + 1), y)
    ascii_str_1 = \
"""\
 /  x     \\\n\
f|-----, y|\n\
 \\1 + y   /\
"""
    ascii_str_2 = \
"""\
 /  x     \\\n\
f|-----, y|\n\
 \\y + 1   /\
"""
    ucode_str_1 = \
u("""\
 ⎛  x     ⎞\n\
f⎜─────, y⎟\n\
 ⎝1 + y   ⎠\
""")
    ucode_str_2 = \
u("""\
 ⎛  x     ⎞\n\
f⎜─────, y⎟\n\
 ⎝y + 1   ⎠\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = f(x**x**x**x**x**x)
    ascii_str = \
"""\
 / / / / / x\\\\\\\\\\
 | | | | \\x /||||
 | | | \\x    /|||
 | | \\x       /||
 | \\x          /|
f\\x             /\
"""
    ucode_str = \
u("""\
 ⎛ ⎛ ⎛ ⎛ ⎛ x⎞⎞⎞⎞⎞
 ⎜ ⎜ ⎜ ⎜ ⎝x ⎠⎟⎟⎟⎟
 ⎜ ⎜ ⎜ ⎝x    ⎠⎟⎟⎟
 ⎜ ⎜ ⎝x       ⎠⎟⎟
 ⎜ ⎝x          ⎠⎟
f⎝x             ⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = sin(x)**2
    ascii_str = \
"""\
   2   \n\
sin (x)\
"""
    ucode_str = \
u("""\
   2   \n\
sin (x)\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = conjugate(a + b*I)
    ascii_str = \
"""\
_     _\n\
a - I*b\
"""
    ucode_str = \
u("""\
_     _\n\
a - ⅈ⋅b\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = conjugate(exp(a + b*I))
    ascii_str = \
"""\
 _     _\n\
 a - I*b\n\
e       \
"""
    ucode_str = \
u("""\
 _     _\n\
 a - ⅈ⋅b\n\
ℯ       \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = conjugate( f(1 + conjugate(f(x))) )
    ascii_str_1 = \
"""\
___________\n\
 /    ____\\\n\
f\\1 + f(x)/\
"""
    ascii_str_2 = \
"""\
___________\n\
 /____    \\\n\
f\\f(x) + 1/\
"""
    ucode_str_1 = \
u("""\
___________\n\
 ⎛    ____⎞\n\
f⎝1 + f(x)⎠\
""")
    ucode_str_2 = \
u("""\
___________\n\
 ⎛____    ⎞\n\
f⎝f(x) + 1⎠\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = f(x/(y + 1), y)
    ascii_str_1 = \
"""\
 /  x     \\\n\
f|-----, y|\n\
 \\1 + y   /\
"""
    ascii_str_2 = \
"""\
 /  x     \\\n\
f|-----, y|\n\
 \\y + 1   /\
"""
    ucode_str_1 = \
u("""\
 ⎛  x     ⎞\n\
f⎜─────, y⎟\n\
 ⎝1 + y   ⎠\
""")
    ucode_str_2 = \
u("""\
 ⎛  x     ⎞\n\
f⎜─────, y⎟\n\
 ⎝y + 1   ⎠\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = floor(1 / (y - floor(x)))
    ascii_str = \
"""\
     /     1      \\\n\
floor|------------|\n\
     \\y - floor(x)/\
"""
    ucode_str = \
u("""\
⎢   1   ⎥\n\
⎢───────⎥\n\
⎣y - ⌊x⌋⎦\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = ceiling(1 / (y - ceiling(x)))
    ascii_str = \
"""\
       /      1       \\\n\
ceiling|--------------|\n\
       \\y - ceiling(x)/\
"""
    ucode_str = \
u("""\
⎡   1   ⎤\n\
⎢───────⎥\n\
⎢y - ⌈x⌉⎥\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = euler(n)
    ascii_str = \
"""\
E \n\
 n\
"""
    ucode_str = \
u("""\
E \n\
 n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = euler(1/(1 + 1/(1 + 1/n)))
    ascii_str = \
"""\
E         \n\
     1    \n\
 ---------\n\
       1  \n\
 1 + -----\n\
         1\n\
     1 + -\n\
         n\
"""

    ucode_str = \
u("""\
E         \n\
     1    \n\
 ─────────\n\
       1  \n\
 1 + ─────\n\
         1\n\
     1 + ─\n\
         n\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = euler(n, x)
    ascii_str = \
"""\
E (x)\n\
 n   \
"""
    ucode_str = \
u("""\
E (x)\n\
 n   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = euler(n, x/2)
    ascii_str = \
"""\
  /x\\\n\
E |-|\n\
 n\\2/\
"""
    ucode_str = \
u("""\
  ⎛x⎞\n\
E ⎜─⎟\n\
 n⎝2⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_sqrt():
    expr = sqrt(2)
    ascii_str = \
"""\
  ___\n\
\\/ 2 \
"""
    ucode_str = \
u"√2"
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = 2**Rational(1, 3)
    ascii_str = \
"""\
3 ___\n\
\\/ 2 \
"""
    ucode_str = \
u("""\
3 ___\n\
╲╱ 2 \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = 2**Rational(1, 1000)
    ascii_str = \
"""\
1000___\n\
  \\/ 2 \
"""
    ucode_str = \
u("""\
1000___\n\
  ╲╱ 2 \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = sqrt(x**2 + 1)
    ascii_str = \
"""\
   ________\n\
  /  2     \n\
\\/  x  + 1 \
"""
    ucode_str = \
u("""\
   ________\n\
  ╱  2     \n\
╲╱  x  + 1 \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (1 + sqrt(5))**Rational(1, 3)
    ascii_str = \
"""\
   ___________\n\
3 /       ___ \n\
\\/  1 + \\/ 5  \
"""
    ucode_str = \
u("""\
3 ________\n\
╲╱ 1 + √5 \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = 2**(1/x)
    ascii_str = \
"""\
x ___\n\
\\/ 2 \
"""
    ucode_str = \
u("""\
x ___\n\
╲╱ 2 \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = sqrt(2 + pi)
    ascii_str = \
"""\
  ________\n\
\\/ 2 + pi \
"""
    ucode_str = \
u("""\
  _______\n\
╲╱ 2 + π \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (2 + (
        1 + x**2)/(2 + x))**Rational(1, 4) + (1 + x**Rational(1, 1000))/sqrt(3 + x**2)
    ascii_str = \
"""\
     ____________              \n\
    /      2        1000___    \n\
   /      x  + 1      \\/ x  + 1\n\
4 /   2 + ------  + -----------\n\
\\/        x + 2        ________\n\
                      /  2     \n\
                    \\/  x  + 3 \
"""
    ucode_str = \
u("""\
     ____________              \n\
    ╱      2        1000___    \n\
   ╱      x  + 1      ╲╱ x  + 1\n\
4 ╱   2 + ──────  + ───────────\n\
╲╱        x + 2        ________\n\
                      ╱  2     \n\
                    ╲╱  x  + 3 \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_sqrt_char_knob():
    # See PR #9234.
    expr = sqrt(2)
    ucode_str1 = \
u("""\
  ___\n\
╲╱ 2 \
""")
    ucode_str2 = \
u"√2"
    assert xpretty(expr, use_unicode=True,
                   use_unicode_sqrt_char=False) == ucode_str1
    assert xpretty(expr, use_unicode=True,
                   use_unicode_sqrt_char=True) == ucode_str2


def test_pretty_sqrt_longsymbol_no_sqrt_char():
    # Do not use unicode sqrt char for long symbols (see PR #9234).
    expr = sqrt(Symbol('C1'))
    ucode_str = \
u("""\
  ____\n\
╲╱ C₁ \
""")
    assert upretty(expr) == ucode_str


def test_pretty_KroneckerDelta():
    x, y = symbols("x, y")
    expr = KroneckerDelta(x, y)
    ascii_str = \
"""\
d   \n\
 x,y\
"""
    ucode_str = \
u("""\
δ   \n\
 x,y\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_product():
    n, m, k, l = symbols('n m k l')
    f = symbols('f', cls=Function)
    expr = Product(f((n/3)**2), (n, k**2, l))

    unicode_str = \
u("""\
    l           \n\
─┬──────┬─      \n\
 │      │   ⎛ 2⎞\n\
 │      │   ⎜n ⎟\n\
 │      │  f⎜──⎟\n\
 │      │   ⎝9 ⎠\n\
 │      │       \n\
       2        \n\
  n = k         """)
    ascii_str = \
"""\
    l           \n\
__________      \n\
 |      |   / 2\\\n\
 |      |   |n |\n\
 |      |  f|--|\n\
 |      |   \\9 /\n\
 |      |       \n\
       2        \n\
  n = k         """

    expr = Product(f((n/3)**2), (n, k**2, l), (l, 1, m))

    unicode_str = \
u("""\
    m          l           \n\
─┬──────┬─ ─┬──────┬─      \n\
 │      │   │      │   ⎛ 2⎞\n\
 │      │   │      │   ⎜n ⎟\n\
 │      │   │      │  f⎜──⎟\n\
 │      │   │      │   ⎝9 ⎠\n\
 │      │   │      │       \n\
  l = 1           2        \n\
             n = k         """)
    ascii_str = \
"""\
    m          l           \n\
__________ __________      \n\
 |      |   |      |   / 2\\\n\
 |      |   |      |   |n |\n\
 |      |   |      |  f|--|\n\
 |      |   |      |   \\9 /\n\
 |      |   |      |       \n\
  l = 1           2        \n\
             n = k         """

    assert pretty(expr) == ascii_str
    assert upretty(expr) == unicode_str


def test_pretty_lambda():
    # S.IdentityFunction is a special case
    expr = Lambda(y, y)
    assert pretty(expr) == "x -> x"
    assert upretty(expr) == u"x ↦ x"

    expr = Lambda(x, x+1)
    assert pretty(expr) == "x -> x + 1"
    assert upretty(expr) == u"x ↦ x + 1"

    expr = Lambda(x, x**2)
    ascii_str = \
"""\
      2\n\
x -> x \
"""
    ucode_str = \
u("""\
     2\n\
x ↦ x \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Lambda(x, x**2)**2
    ascii_str = \
"""\
         2
/      2\\ \n\
\\x -> x / \
"""
    ucode_str = \
u("""\
        2
⎛     2⎞ \n\
⎝x ↦ x ⎠ \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Lambda((x, y), x)
    ascii_str = "(x, y) -> x"
    ucode_str = u"(x, y) ↦ x"
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Lambda((x, y), x**2)
    ascii_str = \
"""\
           2\n\
(x, y) -> x \
"""
    ucode_str = \
u("""\
          2\n\
(x, y) ↦ x \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_order():
    expr = O(1)
    ascii_str = \
"""\
O(1)\
"""
    ucode_str = \
u("""\
O(1)\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = O(1/x)
    ascii_str = \
"""\
 /1\\\n\
O|-|\n\
 \\x/\
"""
    ucode_str = \
u("""\
 ⎛1⎞\n\
O⎜─⎟\n\
 ⎝x⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = O(x**2 + y**2)
    ascii_str = \
"""\
 / 2    2                  \\\n\
O\\x  + y ; (x, y) -> (0, 0)/\
"""
    ucode_str = \
u("""\
 ⎛ 2    2                 ⎞\n\
O⎝x  + y ; (x, y) → (0, 0)⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = O(1, (x, oo))
    ascii_str = \
"""\
O(1; x -> oo)\
"""
    ucode_str = \
u("""\
O(1; x → ∞)\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = O(1/x, (x, oo))
    ascii_str = \
"""\
 /1         \\\n\
O|-; x -> oo|\n\
 \\x         /\
"""
    ucode_str = \
u("""\
 ⎛1       ⎞\n\
O⎜─; x → ∞⎟\n\
 ⎝x       ⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = O(x**2 + y**2, (x, oo), (y, oo))
    ascii_str = \
"""\
 / 2    2                    \\\n\
O\\x  + y ; (x, y) -> (oo, oo)/\
"""
    ucode_str = \
u("""\
 ⎛ 2    2                 ⎞\n\
O⎝x  + y ; (x, y) → (∞, ∞)⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_derivatives():
    # Simple
    expr = Derivative(log(x), x, evaluate=False)
    ascii_str = \
"""\
d         \n\
--(log(x))\n\
dx        \
"""
    ucode_str = \
u("""\
d         \n\
──(log(x))\n\
dx        \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Derivative(log(x), x, evaluate=False) + x
    ascii_str_1 = \
"""\
    d         \n\
x + --(log(x))\n\
    dx        \
"""
    ascii_str_2 = \
"""\
d             \n\
--(log(x)) + x\n\
dx            \
"""
    ucode_str_1 = \
u("""\
    d         \n\
x + ──(log(x))\n\
    dx        \
""")
    ucode_str_2 = \
u("""\
d             \n\
──(log(x)) + x\n\
dx            \
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    # basic partial derivatives
    expr = Derivative(log(x + y) + x, x)
    ascii_str_1 = \
"""\
d                 \n\
--(log(x + y) + x)\n\
dx                \
"""
    ascii_str_2 = \
"""\
d                 \n\
--(x + log(x + y))\n\
dx                \
"""
    ucode_str_1 = \
u("""\
∂                 \n\
──(log(x + y) + x)\n\
∂x                \
""")
    ucode_str_2 = \
u("""\
∂                 \n\
──(x + log(x + y))\n\
∂x                \
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2], upretty(expr)

    # Multiple symbols
    expr = Derivative(log(x) + x**2, x, y)
    ascii_str_1 = \
"""\
   2              \n\
  d  /          2\\\n\
-----\\log(x) + x /\n\
dy dx             \
"""
    ascii_str_2 = \
"""\
   2              \n\
  d  / 2         \\\n\
-----\\x  + log(x)/\n\
dy dx             \
"""
    ucode_str_1 = \
u("""\
   2              \n\
  d  ⎛          2⎞\n\
─────⎝log(x) + x ⎠\n\
dy dx             \
""")
    ucode_str_2 = \
u("""\
   2              \n\
  d  ⎛ 2         ⎞\n\
─────⎝x  + log(x)⎠\n\
dy dx             \
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = Derivative(2*x*y, y, x) + x**2
    ascii_str_1 = \
"""\
   2             \n\
  d             2\n\
-----(2*x*y) + x \n\
dx dy            \
"""
    ascii_str_2 = \
"""\
        2        \n\
 2     d         \n\
x  + -----(2*x*y)\n\
     dx dy       \
"""
    ucode_str_1 = \
u("""\
   2             \n\
  ∂             2\n\
─────(2⋅x⋅y) + x \n\
∂x ∂y            \
""")
    ucode_str_2 = \
u("""\
        2        \n\
 2     ∂         \n\
x  + ─────(2⋅x⋅y)\n\
     ∂x ∂y       \
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = Derivative(2*x*y, x, x)
    ascii_str = \
"""\
  2       \n\
 d        \n\
---(2*x*y)\n\
  2       \n\
dx        \
"""
    ucode_str = \
u("""\
  2       \n\
 ∂        \n\
───(2⋅x⋅y)\n\
  2       \n\
∂x        \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Derivative(2*x*y, x, 17)
    ascii_str = \
"""\
 17        \n\
d          \n\
----(2*x*y)\n\
  17       \n\
dx         \
"""
    ucode_str = \
u("""\
 17        \n\
∂          \n\
────(2⋅x⋅y)\n\
  17       \n\
∂x         \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Derivative(2*x*y, x, x, y)
    ascii_str = \
"""\
   3         \n\
  d          \n\
------(2*x*y)\n\
     2       \n\
dy dx        \
"""
    ucode_str = \
u("""\
   3         \n\
  ∂          \n\
──────(2⋅x⋅y)\n\
     2       \n\
∂y ∂x        \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    # Greek letters
    alpha = Symbol('alpha')
    beta = Function('beta')
    expr = beta(alpha).diff(alpha)
    ascii_str = \
"""\
  d                \n\
------(beta(alpha))\n\
dalpha             \
"""
    ucode_str = \
u("""\
d       \n\
──(β(α))\n\
dα      \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Derivative(f(x), (x, n))

    ascii_str = \
"""\
  n      \n\
 d       \n\
---(f(x))\n\
  n      \n\
dx       \
"""
    ucode_str = \
u("""\
  n      \n\
 d       \n\
───(f(x))\n\
  n      \n\
dx       \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_integrals():
    expr = Integral(log(x), x)
    ascii_str = \
"""\
  /         \n\
 |          \n\
 | log(x) dx\n\
 |          \n\
/           \
"""
    ucode_str = \
u("""\
⌠          \n\
⎮ log(x) dx\n\
⌡          \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Integral(x**2, x)
    ascii_str = \
"""\
  /     \n\
 |      \n\
 |  2   \n\
 | x  dx\n\
 |      \n\
/       \
"""
    ucode_str = \
u("""\
⌠      \n\
⎮  2   \n\
⎮ x  dx\n\
⌡      \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Integral((sin(x))**2 / (tan(x))**2)
    ascii_str = \
"""\
  /          \n\
 |           \n\
 |    2      \n\
 | sin (x)   \n\
 | ------- dx\n\
 |    2      \n\
 | tan (x)   \n\
 |           \n\
/            \
"""
    ucode_str = \
u("""\
⌠           \n\
⎮    2      \n\
⎮ sin (x)   \n\
⎮ ─────── dx\n\
⎮    2      \n\
⎮ tan (x)   \n\
⌡           \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Integral(x**(2**x), x)
    ascii_str = \
"""\
  /        \n\
 |         \n\
 |  / x\\   \n\
 |  \\2 /   \n\
 | x     dx\n\
 |         \n\
/          \
"""
    ucode_str = \
u("""\
⌠         \n\
⎮  ⎛ x⎞   \n\
⎮  ⎝2 ⎠   \n\
⎮ x     dx\n\
⌡         \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Integral(x**2, (x, 1, 2))
    ascii_str = \
"""\
  2      \n\
  /      \n\
 |       \n\
 |   2   \n\
 |  x  dx\n\
 |       \n\
/        \n\
1        \
"""
    ucode_str = \
u("""\
2      \n\
⌠      \n\
⎮  2   \n\
⎮ x  dx\n\
⌡      \n\
1      \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Integral(x**2, (x, Rational(1, 2), 10))
    ascii_str = \
"""\
 10      \n\
  /      \n\
 |       \n\
 |   2   \n\
 |  x  dx\n\
 |       \n\
/        \n\
1/2      \
"""
    ucode_str = \
u("""\
 10      \n\
 ⌠       \n\
 ⎮   2   \n\
 ⎮  x  dx\n\
 ⌡       \n\
1/2      \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Integral(x**2*y**2, x, y)
    ascii_str = \
"""\
  /  /           \n\
 |  |            \n\
 |  |  2  2      \n\
 |  | x *y  dx dy\n\
 |  |            \n\
/  /             \
"""
    ucode_str = \
u("""\
⌠ ⌠            \n\
⎮ ⎮  2  2      \n\
⎮ ⎮ x ⋅y  dx dy\n\
⌡ ⌡            \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Integral(sin(th)/cos(ph), (th, 0, pi), (ph, 0, 2*pi))
    ascii_str = \
"""\
 2*pi pi                           \n\
   /   /                           \n\
  |   |                            \n\
  |   |  sin(theta)                \n\
  |   |  ---------- d(theta) d(phi)\n\
  |   |   cos(phi)                 \n\
  |   |                            \n\
 /   /                             \n\
 0   0                             \
"""
    ucode_str = \
u("""\
2⋅π π             \n\
 ⌠  ⌠             \n\
 ⎮  ⎮ sin(θ)      \n\
 ⎮  ⎮ ────── dθ dφ\n\
 ⎮  ⎮ cos(φ)      \n\
 ⌡  ⌡             \n\
 0  0             \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_matrix():
    # Empty Matrix
    expr = Matrix()
    ascii_str = "[]"
    unicode_str = "[]"
    assert pretty(expr) == ascii_str
    assert upretty(expr) == unicode_str
    expr = Matrix(2, 0, lambda i, j: 0)
    ascii_str = "[]"
    unicode_str = "[]"
    assert pretty(expr) == ascii_str
    assert upretty(expr) == unicode_str
    expr = Matrix(0, 2, lambda i, j: 0)
    ascii_str = "[]"
    unicode_str = "[]"
    assert pretty(expr) == ascii_str
    assert upretty(expr) == unicode_str
    expr = Matrix([[x**2 + 1, 1], [y, x + y]])
    ascii_str_1 = \
"""\
[     2       ]
[1 + x     1  ]
[             ]
[  y     x + y]\
"""
    ascii_str_2 = \
"""\
[ 2           ]
[x  + 1    1  ]
[             ]
[  y     x + y]\
"""
    ucode_str_1 = \
u("""\
⎡     2       ⎤
⎢1 + x     1  ⎥
⎢             ⎥
⎣  y     x + y⎦\
""")
    ucode_str_2 = \
u("""\
⎡ 2           ⎤
⎢x  + 1    1  ⎥
⎢             ⎥
⎣  y     x + y⎦\
""")
    assert pretty(expr) in [ascii_str_1, ascii_str_2]
    assert upretty(expr) in [ucode_str_1, ucode_str_2]

    expr = Matrix([[x/y, y, th], [0, exp(I*k*ph), 1]])
    ascii_str = \
"""\
[x                 ]
[-     y      theta]
[y                 ]
[                  ]
[    I*k*phi       ]
[0  e           1  ]\
"""
    ucode_str = \
u("""\
⎡x           ⎤
⎢─    y     θ⎥
⎢y           ⎥
⎢            ⎥
⎢    ⅈ⋅k⋅φ   ⎥
⎣0  ℯ       1⎦\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_ndim_arrays():
    x, y, z, w = symbols("x y z w")

    for ArrayType in (ImmutableDenseNDimArray, ImmutableSparseNDimArray, MutableDenseNDimArray, MutableSparseNDimArray):
        # Basic: scalar array
        M = ArrayType(x)

        assert pretty(M) == "x"
        assert upretty(M) == "x"

        M = ArrayType([[1/x, y], [z, w]])
        M1 = ArrayType([1/x, y, z])

        M2 = tensorproduct(M1, M)
        M3 = tensorproduct(M, M)

        ascii_str = \
"""\
[1   ]\n\
[-  y]\n\
[x   ]\n\
[    ]\n\
[z  w]\
"""
        ucode_str = \
u("""\
⎡1   ⎤\n\
⎢─  y⎥\n\
⎢x   ⎥\n\
⎢    ⎥\n\
⎣z  w⎦\
""")
        assert pretty(M) == ascii_str
        assert upretty(M) == ucode_str

        ascii_str = \
"""\
[1      ]\n\
[-  y  z]\n\
[x      ]\
"""
        ucode_str = \
u("""\
⎡1      ⎤\n\
⎢─  y  z⎥\n\
⎣x      ⎦\
""")
        assert pretty(M1) == ascii_str
        assert upretty(M1) == ucode_str

        ascii_str = \
"""\
[[1   y]                       ]\n\
[[--  -]              [z      ]]\n\
[[ 2  x]  [ y    2 ]  [-   y*z]]\n\
[[x    ]  [ -   y  ]  [x      ]]\n\
[[     ]  [ x      ]  [       ]]\n\
[[z   w]  [        ]  [ 2     ]]\n\
[[-   -]  [y*z  w*y]  [z   w*z]]\n\
[[x   x]                       ]\
"""
        ucode_str = \
u("""\
⎡⎡1   y⎤                       ⎤\n\
⎢⎢──  ─⎥              ⎡z      ⎤⎥\n\
⎢⎢ 2  x⎥  ⎡ y    2 ⎤  ⎢─   y⋅z⎥⎥\n\
⎢⎢x    ⎥  ⎢ ─   y  ⎥  ⎢x      ⎥⎥\n\
⎢⎢     ⎥  ⎢ x      ⎥  ⎢       ⎥⎥\n\
⎢⎢z   w⎥  ⎢        ⎥  ⎢ 2     ⎥⎥\n\
⎢⎢─   ─⎥  ⎣y⋅z  w⋅y⎦  ⎣z   w⋅z⎦⎥\n\
⎣⎣x   x⎦                       ⎦\
""")
        assert pretty(M2) == ascii_str
        assert upretty(M2) == ucode_str

        ascii_str = \
"""\
[ [1   y]             ]\n\
[ [--  -]             ]\n\
[ [ 2  x]   [ y    2 ]]\n\
[ [x    ]   [ -   y  ]]\n\
[ [     ]   [ x      ]]\n\
[ [z   w]   [        ]]\n\
[ [-   -]   [y*z  w*y]]\n\
[ [x   x]             ]\n\
[                     ]\n\
[[z      ]  [ w      ]]\n\
[[-   y*z]  [ -   w*y]]\n\
[[x      ]  [ x      ]]\n\
[[       ]  [        ]]\n\
[[ 2     ]  [      2 ]]\n\
[[z   w*z]  [w*z  w  ]]\
"""
        ucode_str = \
u("""\
⎡ ⎡1   y⎤             ⎤\n\
⎢ ⎢──  ─⎥             ⎥\n\
⎢ ⎢ 2  x⎥   ⎡ y    2 ⎤⎥\n\
⎢ ⎢x    ⎥   ⎢ ─   y  ⎥⎥\n\
⎢ ⎢     ⎥   ⎢ x      ⎥⎥\n\
⎢ ⎢z   w⎥   ⎢        ⎥⎥\n\
⎢ ⎢─   ─⎥   ⎣y⋅z  w⋅y⎦⎥\n\
⎢ ⎣x   x⎦             ⎥\n\
⎢                     ⎥\n\
⎢⎡z      ⎤  ⎡ w      ⎤⎥\n\
⎢⎢─   y⋅z⎥  ⎢ ─   w⋅y⎥⎥\n\
⎢⎢x      ⎥  ⎢ x      ⎥⎥\n\
⎢⎢       ⎥  ⎢        ⎥⎥\n\
⎢⎢ 2     ⎥  ⎢      2 ⎥⎥\n\
⎣⎣z   w⋅z⎦  ⎣w⋅z  w  ⎦⎦\
""")
        assert pretty(M3) == ascii_str
        assert upretty(M3) == ucode_str

        Mrow = ArrayType([[x, y, 1 / z]])
        Mcolumn = ArrayType([[x], [y], [1 / z]])
        Mcol2 = ArrayType([Mcolumn.tolist()])

        ascii_str = \
"""\
[[      1]]\n\
[[x  y  -]]\n\
[[      z]]\
"""
        ucode_str = \
    u("""\
⎡⎡      1⎤⎤\n\
⎢⎢x  y  ─⎥⎥\n\
⎣⎣      z⎦⎦\
""")
        assert pretty(Mrow) == ascii_str
        assert upretty(Mrow) == ucode_str

        ascii_str = \
"""\
[x]\n\
[ ]\n\
[y]\n\
[ ]\n\
[1]\n\
[-]\n\
[z]\
"""
        ucode_str = \
u("""\
⎡x⎤\n\
⎢ ⎥\n\
⎢y⎥\n\
⎢ ⎥\n\
⎢1⎥\n\
⎢─⎥\n\
⎣z⎦\
""")
        assert pretty(Mcolumn) == ascii_str
        assert upretty(Mcolumn) == ucode_str

        ascii_str = \
"""\
[[x]]\n\
[[ ]]\n\
[[y]]\n\
[[ ]]\n\
[[1]]\n\
[[-]]\n\
[[z]]\
"""
        ucode_str = \
u("""\
⎡⎡x⎤⎤\n\
⎢⎢ ⎥⎥\n\
⎢⎢y⎥⎥\n\
⎢⎢ ⎥⎥\n\
⎢⎢1⎥⎥\n\
⎢⎢─⎥⎥\n\
⎣⎣z⎦⎦\
""")
        assert pretty(Mcol2) == ascii_str
        assert upretty(Mcol2) == ucode_str


def test_tensor_TensorProduct():
    A = MatrixSymbol("A", 3, 3)
    B = MatrixSymbol("B", 3, 3)
    assert upretty(TensorProduct(A, B)) == "A\u2297B"
    assert upretty(TensorProduct(A, B, A)) == "A\u2297B\u2297A"


def test_diffgeom_print_WedgeProduct():
    from sympy.diffgeom.rn import R2
    from sympy.diffgeom import WedgeProduct
    wp = WedgeProduct(R2.dx, R2.dy)
    assert upretty(wp) == u("ⅆ x∧ⅆ y")


def test_Adjoint():
    X = MatrixSymbol('X', 2, 2)
    Y = MatrixSymbol('Y', 2, 2)
    assert pretty(Adjoint(X)) == " +\nX "
    assert pretty(Adjoint(X + Y)) == "       +\n(X + Y) "
    assert pretty(Adjoint(X) + Adjoint(Y)) == " +    +\nX  + Y "
    assert pretty(Adjoint(X*Y)) == "     +\n(X*Y) "
    assert pretty(Adjoint(Y)*Adjoint(X)) == " +  +\nY *X "
    assert pretty(Adjoint(X**2)) == "    +\n/ 2\\ \n\\X / "
    assert pretty(Adjoint(X)**2) == "    2\n/ +\\ \n\\X / "
    assert pretty(Adjoint(Inverse(X))) == "     +\n/ -1\\ \n\\X  / "
    assert pretty(Inverse(Adjoint(X))) == "    -1\n/ +\\  \n\\X /  "
    assert pretty(Adjoint(Transpose(X))) == "    +\n/ T\\ \n\\X / "
    assert pretty(Transpose(Adjoint(X))) == "    T\n/ +\\ \n\\X / "
    assert upretty(Adjoint(X)) == u" †\nX "
    assert upretty(Adjoint(X + Y)) == u"       †\n(X + Y) "
    assert upretty(Adjoint(X) + Adjoint(Y)) == u" †    †\nX  + Y "
    assert upretty(Adjoint(X*Y)) == u"     †\n(X⋅Y) "
    assert upretty(Adjoint(Y)*Adjoint(X)) == u" †  †\nY ⋅X "
    assert upretty(Adjoint(X**2)) == \
        u"    †\n⎛ 2⎞ \n⎝X ⎠ "
    assert upretty(Adjoint(X)**2) == \
        u"    2\n⎛ †⎞ \n⎝X ⎠ "
    assert upretty(Adjoint(Inverse(X))) == \
        u"     †\n⎛ -1⎞ \n⎝X  ⎠ "
    assert upretty(Inverse(Adjoint(X))) == \
        u"    -1\n⎛ †⎞  \n⎝X ⎠  "
    assert upretty(Adjoint(Transpose(X))) == \
        u"    †\n⎛ T⎞ \n⎝X ⎠ "
    assert upretty(Transpose(Adjoint(X))) == \
        u"    T\n⎛ †⎞ \n⎝X ⎠ "

def test_pretty_Trace_issue_9044():
    X = Matrix([[1, 2], [3, 4]])
    Y = Matrix([[2, 4], [6, 8]])
    ascii_str_1 = \
"""\
  /[1  2]\\
tr|[    ]|
  \\[3  4]/\
"""
    ucode_str_1 = \
u("""\
  ⎛⎡1  2⎤⎞
tr⎜⎢    ⎥⎟
  ⎝⎣3  4⎦⎠\
""")
    ascii_str_2 = \
"""\
  /[1  2]\\     /[2  4]\\
tr|[    ]| + tr|[    ]|
  \\[3  4]/     \\[6  8]/\
"""
    ucode_str_2 = \
u("""\
  ⎛⎡1  2⎤⎞     ⎛⎡2  4⎤⎞
tr⎜⎢    ⎥⎟ + tr⎜⎢    ⎥⎟
  ⎝⎣3  4⎦⎠     ⎝⎣6  8⎦⎠\
""")
    assert pretty(Trace(X)) == ascii_str_1
    assert upretty(Trace(X)) == ucode_str_1

    assert pretty(Trace(X) + Trace(Y)) == ascii_str_2
    assert upretty(Trace(X) + Trace(Y)) == ucode_str_2


def test_MatrixExpressions():
    n = Symbol('n', integer=True)
    X = MatrixSymbol('X', n, n)

    assert pretty(X) == upretty(X) == "X"

    Y = X[1:2:3, 4:5:6]

    ascii_str = ucode_str = "X[1:3, 4:6]"

    assert pretty(Y) == ascii_str
    assert upretty(Y) == ucode_str

    Z = X[1:10:2]

    ascii_str = ucode_str = "X[1:10:2, :n]"

    assert pretty(Z) == ascii_str
    assert upretty(Z) == ucode_str

def test_pretty_dotproduct():
    from sympy.matrices import Matrix, MatrixSymbol
    from sympy.matrices.expressions.dotproduct import DotProduct
    n = symbols("n", integer=True)
    A = MatrixSymbol('A', n, 1)
    B = MatrixSymbol('B', n, 1)
    C = Matrix(1, 3, [1, 2, 3])
    D = Matrix(1, 3, [1, 3, 4])

    assert pretty(DotProduct(A, B)) == u"A*B"
    assert pretty(DotProduct(C, D)) == u"[1  2  3]*[1  3  4]"
    assert upretty(DotProduct(A, B)) == u"A⋅B"
    assert upretty(DotProduct(C, D)) == u"[1  2  3]⋅[1  3  4]"


def test_pretty_piecewise():
    expr = Piecewise((x, x < 1), (x**2, True))
    ascii_str = \
"""\
/x   for x < 1\n\
|             \n\
< 2           \n\
|x   otherwise\n\
\\             \
"""
    ucode_str = \
u("""\
⎧x   for x < 1\n\
⎪             \n\
⎨ 2           \n\
⎪x   otherwise\n\
⎩             \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = -Piecewise((x, x < 1), (x**2, True))
    ascii_str = \
"""\
 //x   for x < 1\\\n\
 ||             |\n\
-|< 2           |\n\
 ||x   otherwise|\n\
 \\\\             /\
"""
    ucode_str = \
u("""\
 ⎛⎧x   for x < 1⎞\n\
 ⎜⎪             ⎟\n\
-⎜⎨ 2           ⎟\n\
 ⎜⎪x   otherwise⎟\n\
 ⎝⎩             ⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = x + Piecewise((x, x > 0), (y, True)) + Piecewise((x/y, x < 2),
    (y**2, x > 2), (1, True)) + 1
    ascii_str = \
"""\
                      //x            \\    \n\
                      ||-   for x < 2|    \n\
                      ||y            |    \n\
    //x  for x > 0\\   ||             |    \n\
x + |<            | + |< 2           | + 1\n\
    \\\\y  otherwise/   ||y   for x > 2|    \n\
                      ||             |    \n\
                      ||1   otherwise|    \n\
                      \\\\             /    \
"""
    ucode_str = \
u("""\
                      ⎛⎧x            ⎞    \n\
                      ⎜⎪─   for x < 2⎟    \n\
                      ⎜⎪y            ⎟    \n\
    ⎛⎧x  for x > 0⎞   ⎜⎪             ⎟    \n\
x + ⎜⎨            ⎟ + ⎜⎨ 2           ⎟ + 1\n\
    ⎝⎩y  otherwise⎠   ⎜⎪y   for x > 2⎟    \n\
                      ⎜⎪             ⎟    \n\
                      ⎜⎪1   otherwise⎟    \n\
                      ⎝⎩             ⎠    \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = x - Piecewise((x, x > 0), (y, True)) + Piecewise((x/y, x < 2),
    (y**2, x > 2), (1, True)) + 1
    ascii_str = \
"""\
                      //x            \\    \n\
                      ||-   for x < 2|    \n\
                      ||y            |    \n\
    //x  for x > 0\\   ||             |    \n\
x - |<            | + |< 2           | + 1\n\
    \\\\y  otherwise/   ||y   for x > 2|    \n\
                      ||             |    \n\
                      ||1   otherwise|    \n\
                      \\\\             /    \
"""
    ucode_str = \
u("""\
                      ⎛⎧x            ⎞    \n\
                      ⎜⎪─   for x < 2⎟    \n\
                      ⎜⎪y            ⎟    \n\
    ⎛⎧x  for x > 0⎞   ⎜⎪             ⎟    \n\
x - ⎜⎨            ⎟ + ⎜⎨ 2           ⎟ + 1\n\
    ⎝⎩y  otherwise⎠   ⎜⎪y   for x > 2⎟    \n\
                      ⎜⎪             ⎟    \n\
                      ⎜⎪1   otherwise⎟    \n\
                      ⎝⎩             ⎠    \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = x*Piecewise((x, x > 0), (y, True))
    ascii_str = \
"""\
  //x  for x > 0\\\n\
x*|<            |\n\
  \\\\y  otherwise/\
"""
    ucode_str = \
u("""\
  ⎛⎧x  for x > 0⎞\n\
x⋅⎜⎨            ⎟\n\
  ⎝⎩y  otherwise⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Piecewise((x, x > 0), (y, True))*Piecewise((x/y, x < 2), (y**2, x >
    2), (1, True))
    ascii_str = \
"""\
                //x            \\\n\
                ||-   for x < 2|\n\
                ||y            |\n\
//x  for x > 0\\ ||             |\n\
|<            |*|< 2           |\n\
\\\\y  otherwise/ ||y   for x > 2|\n\
                ||             |\n\
                ||1   otherwise|\n\
                \\\\             /\
"""
    ucode_str = \
u("""\
                ⎛⎧x            ⎞\n\
                ⎜⎪─   for x < 2⎟\n\
                ⎜⎪y            ⎟\n\
⎛⎧x  for x > 0⎞ ⎜⎪             ⎟\n\
⎜⎨            ⎟⋅⎜⎨ 2           ⎟\n\
⎝⎩y  otherwise⎠ ⎜⎪y   for x > 2⎟\n\
                ⎜⎪             ⎟\n\
                ⎜⎪1   otherwise⎟\n\
                ⎝⎩             ⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = -Piecewise((x, x > 0), (y, True))*Piecewise((x/y, x < 2), (y**2, x
        > 2), (1, True))
    ascii_str = \
"""\
                 //x            \\\n\
                 ||-   for x < 2|\n\
                 ||y            |\n\
 //x  for x > 0\\ ||             |\n\
-|<            |*|< 2           |\n\
 \\\\y  otherwise/ ||y   for x > 2|\n\
                 ||             |\n\
                 ||1   otherwise|\n\
                 \\\\             /\
"""
    ucode_str = \
u("""\
                 ⎛⎧x            ⎞\n\
                 ⎜⎪─   for x < 2⎟\n\
                 ⎜⎪y            ⎟\n\
 ⎛⎧x  for x > 0⎞ ⎜⎪             ⎟\n\
-⎜⎨            ⎟⋅⎜⎨ 2           ⎟\n\
 ⎝⎩y  otherwise⎠ ⎜⎪y   for x > 2⎟\n\
                 ⎜⎪             ⎟\n\
                 ⎜⎪1   otherwise⎟\n\
                 ⎝⎩             ⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Piecewise((0, Abs(1/y) < 1), (1, Abs(y) < 1), (y*meijerg(((2, 1),
        ()), ((), (1, 0)), 1/y), True))
    ascii_str = \
"""\
/                                |1|    \n\
|            0               for |-| < 1\n\
|                                |y|    \n\
|                                       \n\
<            1               for |y| < 1\n\
|                                       \n\
|   __0, 2 /2, 1       | 1\\             \n\
|y*/__     |           | -|   otherwise \n\
\\  \\_|2, 2 \\      1, 0 | y/             \
"""
    ucode_str = \
u("""\
⎧                                │1│    \n\
⎪            0               for │─│ < 1\n\
⎪                                │y│    \n\
⎪                                       \n\
⎨            1               for │y│ < 1\n\
⎪                                       \n\
⎪  ╭─╮0, 2 ⎛2, 1       │ 1⎞             \n\
⎪y⋅│╶┐     ⎜           │ ─⎟   otherwise \n\
⎩  ╰─╯2, 2 ⎝      1, 0 │ y⎠             \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    # XXX: We have to use evaluate=False here because Piecewise._eval_power
    # denests the power.
    expr = Pow(Piecewise((x, x > 0), (y, True)), 2, evaluate=False)
    ascii_str = \
"""\
               2\n\
//x  for x > 0\\ \n\
|<            | \n\
\\\\y  otherwise/ \
"""
    ucode_str = \
u("""\
               2\n\
⎛⎧x  for x > 0⎞ \n\
⎜⎨            ⎟ \n\
⎝⎩y  otherwise⎠ \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_ITE():
    expr = ITE(x, y, z)
    assert pretty(expr) == (
        '/y    for x  \n'
        '<            \n'
        '\\z  otherwise'
        )
    assert upretty(expr) == u("""\
⎧y    for x  \n\
⎨            \n\
⎩z  otherwise\
""")


def test_pretty_seq():
    expr = ()
    ascii_str = \
"""\
()\
"""
    ucode_str = \
u("""\
()\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = []
    ascii_str = \
"""\
[]\
"""
    ucode_str = \
u("""\
[]\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = {}
    expr_2 = {}
    ascii_str = \
"""\
{}\
"""
    ucode_str = \
u("""\
{}\
""")
    assert pretty(expr) == ascii_str
    assert pretty(expr_2) == ascii_str
    assert upretty(expr) == ucode_str
    assert upretty(expr_2) == ucode_str

    expr = (1/x,)
    ascii_str = \
"""\
 1  \n\
(-,)\n\
 x  \
"""
    ucode_str = \
u("""\
⎛1 ⎞\n\
⎜─,⎟\n\
⎝x ⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = [x**2, 1/x, x, y, sin(th)**2/cos(ph)**2]
    ascii_str = \
"""\
                 2        \n\
  2  1        sin (theta) \n\
[x , -, x, y, -----------]\n\
     x            2       \n\
               cos (phi)  \
"""
    ucode_str = \
u("""\
⎡                2   ⎤\n\
⎢ 2  1        sin (θ)⎥\n\
⎢x , ─, x, y, ───────⎥\n\
⎢    x           2   ⎥\n\
⎣             cos (φ)⎦\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (x**2, 1/x, x, y, sin(th)**2/cos(ph)**2)
    ascii_str = \
"""\
                 2        \n\
  2  1        sin (theta) \n\
(x , -, x, y, -----------)\n\
     x            2       \n\
               cos (phi)  \
"""
    ucode_str = \
u("""\
⎛                2   ⎞\n\
⎜ 2  1        sin (θ)⎟\n\
⎜x , ─, x, y, ───────⎟\n\
⎜    x           2   ⎟\n\
⎝             cos (φ)⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Tuple(x**2, 1/x, x, y, sin(th)**2/cos(ph)**2)
    ascii_str = \
"""\
                 2        \n\
  2  1        sin (theta) \n\
(x , -, x, y, -----------)\n\
     x            2       \n\
               cos (phi)  \
"""
    ucode_str = \
u("""\
⎛                2   ⎞\n\
⎜ 2  1        sin (θ)⎟\n\
⎜x , ─, x, y, ───────⎟\n\
⎜    x           2   ⎟\n\
⎝             cos (φ)⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = {x: sin(x)}
    expr_2 = Dict({x: sin(x)})
    ascii_str = \
"""\
{x: sin(x)}\
"""
    ucode_str = \
u("""\
{x: sin(x)}\
""")
    assert pretty(expr) == ascii_str
    assert pretty(expr_2) == ascii_str
    assert upretty(expr) == ucode_str
    assert upretty(expr_2) == ucode_str

    expr = {1/x: 1/y, x: sin(x)**2}
    expr_2 = Dict({1/x: 1/y, x: sin(x)**2})
    ascii_str = \
"""\
 1  1        2    \n\
{-: -, x: sin (x)}\n\
 x  y             \
"""
    ucode_str = \
u("""\
⎧1  1        2   ⎫\n\
⎨─: ─, x: sin (x)⎬\n\
⎩x  y            ⎭\
""")
    assert pretty(expr) == ascii_str
    assert pretty(expr_2) == ascii_str
    assert upretty(expr) == ucode_str
    assert upretty(expr_2) == ucode_str

    # There used to be a bug with pretty-printing sequences of even height.
    expr = [x**2]
    ascii_str = \
"""\
  2 \n\
[x ]\
"""
    ucode_str = \
u("""\
⎡ 2⎤\n\
⎣x ⎦\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (x**2,)
    ascii_str = \
"""\
  2  \n\
(x ,)\
"""
    ucode_str = \
u("""\
⎛ 2 ⎞\n\
⎝x ,⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Tuple(x**2)
    ascii_str = \
"""\
  2  \n\
(x ,)\
"""
    ucode_str = \
u("""\
⎛ 2 ⎞\n\
⎝x ,⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = {x**2: 1}
    expr_2 = Dict({x**2: 1})
    ascii_str = \
"""\
  2    \n\
{x : 1}\
"""
    ucode_str = \
u("""\
⎧ 2   ⎫\n\
⎨x : 1⎬\n\
⎩     ⎭\
""")
    assert pretty(expr) == ascii_str
    assert pretty(expr_2) == ascii_str
    assert upretty(expr) == ucode_str
    assert upretty(expr_2) == ucode_str


def test_any_object_in_sequence():
    # Cf. issue 5306
    b1 = Basic()
    b2 = Basic(Basic())

    expr = [b2, b1]
    assert pretty(expr) == "[Basic(Basic()), Basic()]"
    assert upretty(expr) == u"[Basic(Basic()), Basic()]"

    expr = {b2, b1}
    assert pretty(expr) == "{Basic(), Basic(Basic())}"
    assert upretty(expr) == u"{Basic(), Basic(Basic())}"

    expr = {b2: b1, b1: b2}
    expr2 = Dict({b2: b1, b1: b2})
    assert pretty(expr) == "{Basic(): Basic(Basic()), Basic(Basic()): Basic()}"
    assert pretty(
        expr2) == "{Basic(): Basic(Basic()), Basic(Basic()): Basic()}"
    assert upretty(
        expr) == u"{Basic(): Basic(Basic()), Basic(Basic()): Basic()}"
    assert upretty(
        expr2) == u"{Basic(): Basic(Basic()), Basic(Basic()): Basic()}"

def test_print_builtin_set():
    assert pretty(set()) == 'set()'
    assert upretty(set()) == u'set()'

    assert pretty(frozenset()) == 'frozenset()'
    assert upretty(frozenset()) == u'frozenset()'

    s1 = {1/x, x}
    s2 = frozenset(s1)

    assert pretty(s1) == \
"""\
 1    \n\
{-, x}
 x    \
"""
    assert upretty(s1) == \
u"""\
⎧1   ⎫
⎨─, x⎬
⎩x   ⎭\
"""

    assert pretty(s2) == \
"""\
           1     \n\
frozenset({-, x})
           x     \
"""
    assert upretty(s2) == \
u"""\
         ⎛⎧1   ⎫⎞
frozenset⎜⎨─, x⎬⎟
         ⎝⎩x   ⎭⎠\
"""

def test_pretty_sets():
    s = FiniteSet
    assert pretty(s(*[x*y, x**2])) == \
"""\
  2      \n\
{x , x*y}\
"""
    assert pretty(s(*range(1, 6))) == "{1, 2, 3, 4, 5}"
    assert pretty(s(*range(1, 13))) == "{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}"

    assert pretty(set([x*y, x**2])) == \
"""\
  2      \n\
{x , x*y}\
"""
    assert pretty(set(range(1, 6))) == "{1, 2, 3, 4, 5}"
    assert pretty(set(range(1, 13))) == \
        "{1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}"

    assert pretty(frozenset([x*y, x**2])) == \
"""\
            2       \n\
frozenset({x , x*y})\
"""
    assert pretty(frozenset(range(1, 6))) == "frozenset({1, 2, 3, 4, 5})"
    assert pretty(frozenset(range(1, 13))) == \
        "frozenset({1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12})"

    assert pretty(Range(0, 3, 1)) == '{0, 1, 2}'

    ascii_str = '{0, 1, ..., 29}'
    ucode_str = u'{0, 1, …, 29}'
    assert pretty(Range(0, 30, 1)) == ascii_str
    assert upretty(Range(0, 30, 1)) == ucode_str

    ascii_str = '{30, 29, ..., 2}'
    ucode_str = u('{30, 29, …, 2}')
    assert pretty(Range(30, 1, -1)) == ascii_str
    assert upretty(Range(30, 1, -1)) == ucode_str

    ascii_str = '{0, 2, ...}'
    ucode_str = u'{0, 2, …}'
    assert pretty(Range(0, oo, 2)) == ascii_str
    assert upretty(Range(0, oo, 2)) == ucode_str

    ascii_str = '{..., 2, 0}'
    ucode_str = u('{…, 2, 0}')
    assert pretty(Range(oo, -2, -2)) == ascii_str
    assert upretty(Range(oo, -2, -2)) == ucode_str

    ascii_str = '{-2, -3, ...}'
    ucode_str = u('{-2, -3, …}')
    assert pretty(Range(-2, -oo, -1)) == ascii_str
    assert upretty(Range(-2, -oo, -1)) == ucode_str


def test_pretty_SetExpr():
    iv = Interval(1, 3)
    se = SetExpr(iv)
    ascii_str = "SetExpr([1, 3])"
    ucode_str = u("SetExpr([1, 3])")
    assert pretty(se) == ascii_str
    assert upretty(se) == ucode_str


def test_pretty_ImageSet():
    imgset = ImageSet(Lambda((x, y), x + y), {1, 2, 3}, {3, 4})
    ascii_str = '{x + y | x in {1, 2, 3} , y in {3, 4}}'
    ucode_str = u('{x + y | x ∊ {1, 2, 3} , y ∊ {3, 4}}')
    assert pretty(imgset) == ascii_str
    assert upretty(imgset) == ucode_str

    imgset = ImageSet(Lambda(x, x**2), S.Naturals)
    ascii_str = \
    '  2                 \n'\
    '{x  | x in Naturals}'
    ucode_str = u('''\
⎧ 2        ⎫\n\
⎨x  | x ∊ ℕ⎬\n\
⎩          ⎭''')
    assert pretty(imgset) == ascii_str
    assert upretty(imgset) == ucode_str


def test_pretty_ConditionSet():
    from sympy import ConditionSet
    ascii_str = '{x | x in (-oo, oo) and sin(x) = 0}'
    ucode_str = u'{x | x ∊ ℝ ∧ sin(x) = 0}'
    assert pretty(ConditionSet(x, Eq(sin(x), 0), S.Reals)) == ascii_str
    assert upretty(ConditionSet(x, Eq(sin(x), 0), S.Reals)) == ucode_str

    assert pretty(ConditionSet(x, Contains(x, S.Reals, evaluate=False), FiniteSet(1))) == '{1}'
    assert upretty(ConditionSet(x, Contains(x, S.Reals, evaluate=False), FiniteSet(1))) == u'{1}'

    assert pretty(ConditionSet(x, And(x > 1, x < -1), FiniteSet(1, 2, 3))) == "EmptySet()"
    assert upretty(ConditionSet(x, And(x > 1, x < -1), FiniteSet(1, 2, 3))) == u"∅"

    assert pretty(ConditionSet(x, Or(x > 1, x < -1), FiniteSet(1, 2))) == '{2}'
    assert upretty(ConditionSet(x, Or(x > 1, x < -1), FiniteSet(1, 2))) == u'{2}'


def test_pretty_ComplexRegion():
    from sympy import ComplexRegion
    ucode_str = u'{x + y⋅ⅈ | x, y ∊ [3, 5] × [4, 6]}'
    assert upretty(ComplexRegion(Interval(3, 5)*Interval(4, 6))) == ucode_str

    ucode_str = u'{r⋅(ⅈ⋅sin(θ) + cos(θ)) | r, θ ∊ [0, 1] × [0, 2⋅π)}'
    assert upretty(ComplexRegion(Interval(0, 1)*Interval(0, 2*pi), polar=True)) == ucode_str

def test_pretty_Union_issue_10414():
    a, b = Interval(2, 3), Interval(4, 7)
    ucode_str = u'[2, 3] ∪ [4, 7]'
    ascii_str = '[2, 3] U [4, 7]'
    assert upretty(Union(a, b)) == ucode_str
    assert pretty(Union(a, b)) == ascii_str

def test_pretty_Intersection_issue_10414():
    x, y, z, w = symbols('x, y, z, w')
    a, b = Interval(x, y), Interval(z, w)
    ucode_str = u'[x, y] ∩ [z, w]'
    ascii_str = '[x, y] n [z, w]'
    assert upretty(Intersection(a, b)) == ucode_str
    assert pretty(Intersection(a, b)) == ascii_str

def test_ProductSet_paranthesis():
    ucode_str = u'([4, 7] × {1, 2}) ∪ ([2, 3] × [4, 7])'

    a, b, c = Interval(2, 3), Interval(4, 7), Interval(1, 9)
    assert upretty(Union(a*b, b*FiniteSet(1, 2))) == ucode_str

def test_ProductSet_prod_char_issue_10413():
    ascii_str = '[2, 3] x [4, 7]'
    ucode_str = u'[2, 3] × [4, 7]'

    a, b = Interval(2, 3), Interval(4, 7)
    assert pretty(a*b) == ascii_str
    assert upretty(a*b) == ucode_str

def test_pretty_sequences():
    s1 = SeqFormula(a**2, (0, oo))
    s2 = SeqPer((1, 2))

    ascii_str = '[0, 1, 4, 9, ...]'
    ucode_str = u'[0, 1, 4, 9, …]'

    assert pretty(s1) == ascii_str
    assert upretty(s1) == ucode_str

    ascii_str = '[1, 2, 1, 2, ...]'
    ucode_str = u'[1, 2, 1, 2, …]'
    assert pretty(s2) == ascii_str
    assert upretty(s2) == ucode_str

    s3 = SeqFormula(a**2, (0, 2))
    s4 = SeqPer((1, 2), (0, 2))

    ascii_str = '[0, 1, 4]'
    ucode_str = u'[0, 1, 4]'

    assert pretty(s3) == ascii_str
    assert upretty(s3) == ucode_str

    ascii_str = '[1, 2, 1]'
    ucode_str = u'[1, 2, 1]'
    assert pretty(s4) == ascii_str
    assert upretty(s4) == ucode_str

    s5 = SeqFormula(a**2, (-oo, 0))
    s6 = SeqPer((1, 2), (-oo, 0))

    ascii_str = '[..., 9, 4, 1, 0]'
    ucode_str = u'[…, 9, 4, 1, 0]'

    assert pretty(s5) == ascii_str
    assert upretty(s5) == ucode_str

    ascii_str = '[..., 2, 1, 2, 1]'
    ucode_str = u'[…, 2, 1, 2, 1]'
    assert pretty(s6) == ascii_str
    assert upretty(s6) == ucode_str

    ascii_str = '[1, 3, 5, 11, ...]'
    ucode_str = u'[1, 3, 5, 11, …]'

    assert pretty(SeqAdd(s1, s2)) == ascii_str
    assert upretty(SeqAdd(s1, s2)) == ucode_str

    ascii_str = '[1, 3, 5]'
    ucode_str = u'[1, 3, 5]'

    assert pretty(SeqAdd(s3, s4)) == ascii_str
    assert upretty(SeqAdd(s3, s4)) == ucode_str

    ascii_str = '[..., 11, 5, 3, 1]'
    ucode_str = u'[…, 11, 5, 3, 1]'

    assert pretty(SeqAdd(s5, s6)) == ascii_str
    assert upretty(SeqAdd(s5, s6)) == ucode_str

    ascii_str = '[0, 2, 4, 18, ...]'
    ucode_str = u'[0, 2, 4, 18, …]'

    assert pretty(SeqMul(s1, s2)) == ascii_str
    assert upretty(SeqMul(s1, s2)) == ucode_str

    ascii_str = '[0, 2, 4]'
    ucode_str = u'[0, 2, 4]'

    assert pretty(SeqMul(s3, s4)) == ascii_str
    assert upretty(SeqMul(s3, s4)) == ucode_str

    ascii_str = '[..., 18, 4, 2, 0]'
    ucode_str = u'[…, 18, 4, 2, 0]'

    assert pretty(SeqMul(s5, s6)) == ascii_str
    assert upretty(SeqMul(s5, s6)) == ucode_str

    # Sequences with symbolic limits, issue 12629
    s7 = SeqFormula(a**2, (a, 0, x))
    raises(NotImplementedError, lambda: pretty(s7))
    raises(NotImplementedError, lambda: upretty(s7))

    b = Symbol('b')
    s8 = SeqFormula(b*a**2, (a, 0, 2))
    ascii_str = u'[0, b, 4*b]'
    ucode_str = u'[0, b, 4⋅b]'
    assert pretty(s8) == ascii_str
    assert upretty(s8) == ucode_str


def test_pretty_FourierSeries():
    f = fourier_series(x, (x, -pi, pi))

    ascii_str = \
"""\
                      2*sin(3*x)      \n\
2*sin(x) - sin(2*x) + ---------- + ...\n\
                          3           \
"""

    ucode_str = \
u("""\
                      2⋅sin(3⋅x)    \n\
2⋅sin(x) - sin(2⋅x) + ────────── + …\n\
                          3         \
""")

    assert pretty(f) == ascii_str
    assert upretty(f) == ucode_str


def test_pretty_FormalPowerSeries():
    f = fps(log(1 + x))


    ascii_str = \
"""\
  oo             \n\
____             \n\
\\   `            \n\
 \\         -k  k \n\
  \\   -(-1)  *x  \n\
  /   -----------\n\
 /         k     \n\
/___,            \n\
k = 1            \
"""

    ucode_str = \
u("""\
  ∞              \n\
 ____            \n\
 ╲               \n\
  ╲        -k  k \n\
   ╲  -(-1)  ⋅x  \n\
   ╱  ───────────\n\
  ╱        k     \n\
 ╱               \n\
 ‾‾‾‾            \n\
k = 1            \
""")

    assert pretty(f) == ascii_str
    assert upretty(f) == ucode_str


def test_pretty_limits():
    expr = Limit(x, x, oo)
    ascii_str = \
"""\
 lim x\n\
x->oo \
"""
    ucode_str = \
u("""\
lim x\n\
x─→∞ \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Limit(x**2, x, 0)
    ascii_str = \
"""\
      2\n\
 lim x \n\
x->0+  \
"""
    ucode_str = \
u("""\
      2\n\
 lim x \n\
x─→0⁺  \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Limit(1/x, x, 0)
    ascii_str = \
"""\
     1\n\
 lim -\n\
x->0+x\
"""
    ucode_str = \
u("""\
     1\n\
 lim ─\n\
x─→0⁺x\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Limit(sin(x)/x, x, 0)
    ascii_str = \
"""\
     /sin(x)\\\n\
 lim |------|\n\
x->0+\\  x   /\
"""
    ucode_str = \
u("""\
     ⎛sin(x)⎞\n\
 lim ⎜──────⎟\n\
x─→0⁺⎝  x   ⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Limit(sin(x)/x, x, 0, "-")
    ascii_str = \
"""\
     /sin(x)\\\n\
 lim |------|\n\
x->0-\\  x   /\
"""
    ucode_str = \
u("""\
     ⎛sin(x)⎞\n\
 lim ⎜──────⎟\n\
x─→0⁻⎝  x   ⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Limit(x + sin(x), x, 0)
    ascii_str = \
"""\
 lim (x + sin(x))\n\
x->0+            \
"""
    ucode_str = \
u("""\
 lim (x + sin(x))\n\
x─→0⁺            \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Limit(x, x, 0)**2
    ascii_str = \
"""\
        2\n\
/ lim x\\ \n\
\\x->0+ / \
"""
    ucode_str = \
u("""\
        2\n\
⎛ lim x⎞ \n\
⎝x─→0⁺ ⎠ \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Limit(x*Limit(y/2,y,0), x, 0)
    ascii_str = \
"""\
     /       /y\\\\\n\
 lim |x* lim |-||\n\
x->0+\\  y->0+\\2//\
"""
    ucode_str = \
u("""\
     ⎛       ⎛y⎞⎞\n\
 lim ⎜x⋅ lim ⎜─⎟⎟\n\
x─→0⁺⎝  y─→0⁺⎝2⎠⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = 2*Limit(x*Limit(y/2,y,0), x, 0)
    ascii_str = \
"""\
       /       /y\\\\\n\
2* lim |x* lim |-||\n\
  x->0+\\  y->0+\\2//\
"""
    ucode_str = \
u("""\
       ⎛       ⎛y⎞⎞\n\
2⋅ lim ⎜x⋅ lim ⎜─⎟⎟\n\
  x─→0⁺⎝  y─→0⁺⎝2⎠⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Limit(sin(x), x, 0, dir='+-')
    ascii_str = \
"""\
lim sin(x)\n\
x->0      \
"""
    ucode_str = \
u("""\
lim sin(x)\n\
x─→0      \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_ComplexRootOf():
    expr = rootof(x**5 + 11*x - 2, 0)
    ascii_str = \
"""\
       / 5              \\\n\
CRootOf\\x  + 11*x - 2, 0/\
"""
    ucode_str = \
u("""\
       ⎛ 5              ⎞\n\
CRootOf⎝x  + 11⋅x - 2, 0⎠\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_RootSum():
    expr = RootSum(x**5 + 11*x - 2, auto=False)
    ascii_str = \
"""\
       / 5           \\\n\
RootSum\\x  + 11*x - 2/\
"""
    ucode_str = \
u("""\
       ⎛ 5           ⎞\n\
RootSum⎝x  + 11⋅x - 2⎠\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = RootSum(x**5 + 11*x - 2, Lambda(z, exp(z)))
    ascii_str = \
"""\
       / 5                   z\\\n\
RootSum\\x  + 11*x - 2, z -> e /\
"""
    ucode_str = \
u("""\
       ⎛ 5                  z⎞\n\
RootSum⎝x  + 11⋅x - 2, z ↦ ℯ ⎠\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_GroebnerBasis():
    expr = groebner([], x, y)

    ascii_str = \
"""\
GroebnerBasis([], x, y, domain=ZZ, order=lex)\
"""
    ucode_str = \
u("""\
GroebnerBasis([], x, y, domain=ℤ, order=lex)\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    F = [x**2 - 3*y - x + 1, y**2 - 2*x + y - 1]
    expr = groebner(F, x, y, order='grlex')

    ascii_str = \
"""\
             /[ 2                 2              ]                              \\\n\
GroebnerBasis\\[x  - x - 3*y + 1, y  - 2*x + y - 1], x, y, domain=ZZ, order=grlex/\
"""
    ucode_str = \
u("""\
             ⎛⎡ 2                 2              ⎤                             ⎞\n\
GroebnerBasis⎝⎣x  - x - 3⋅y + 1, y  - 2⋅x + y - 1⎦, x, y, domain=ℤ, order=grlex⎠\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = expr.fglm('lex')

    ascii_str = \
"""\
             /[       2           4      3      2           ]                            \\\n\
GroebnerBasis\\[2*x - y  - y + 1, y  + 2*y  - 3*y  - 16*y + 7], x, y, domain=ZZ, order=lex/\
"""
    ucode_str = \
u("""\
             ⎛⎡       2           4      3      2           ⎤                           ⎞\n\
GroebnerBasis⎝⎣2⋅x - y  - y + 1, y  + 2⋅y  - 3⋅y  - 16⋅y + 7⎦, x, y, domain=ℤ, order=lex⎠\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_Boolean():
    expr = Not(x, evaluate=False)

    assert pretty(expr) == "Not(x)"
    assert upretty(expr) == u"¬x"

    expr = And(x, y)

    assert pretty(expr) == "And(x, y)"
    assert upretty(expr) == u"x ∧ y"

    expr = Or(x, y)

    assert pretty(expr) == "Or(x, y)"
    assert upretty(expr) == u"x ∨ y"

    syms = symbols('a:f')
    expr = And(*syms)

    assert pretty(expr) == "And(a, b, c, d, e, f)"
    assert upretty(expr) == u"a ∧ b ∧ c ∧ d ∧ e ∧ f"

    expr = Or(*syms)

    assert pretty(expr) == "Or(a, b, c, d, e, f)"
    assert upretty(expr) == u"a ∨ b ∨ c ∨ d ∨ e ∨ f"

    expr = Xor(x, y, evaluate=False)

    assert pretty(expr) == "Xor(x, y)"
    assert upretty(expr) == u"x ⊻ y"

    expr = Nand(x, y, evaluate=False)

    assert pretty(expr) == "Nand(x, y)"
    assert upretty(expr) == u"x ⊼ y"

    expr = Nor(x, y, evaluate=False)

    assert pretty(expr) == "Nor(x, y)"
    assert upretty(expr) == u"x ⊽ y"

    expr = Implies(x, y, evaluate=False)

    assert pretty(expr) == "Implies(x, y)"
    assert upretty(expr) == u"x → y"

    # don't sort args
    expr = Implies(y, x, evaluate=False)

    assert pretty(expr) == "Implies(y, x)"
    assert upretty(expr) == u"y → x"

    expr = Equivalent(x, y, evaluate=False)

    assert pretty(expr) == "Equivalent(x, y)"
    assert upretty(expr) == u"x ⇔ y"

    expr = Equivalent(y, x, evaluate=False)

    assert pretty(expr) == "Equivalent(x, y)"
    assert upretty(expr) == u"x ⇔ y"


def test_pretty_Domain():
    expr = FF(23)

    assert pretty(expr) == "GF(23)"
    assert upretty(expr) == u"ℤ₂₃"

    expr = ZZ

    assert pretty(expr) == "ZZ"
    assert upretty(expr) == u"ℤ"

    expr = QQ

    assert pretty(expr) == "QQ"
    assert upretty(expr) == u"ℚ"

    expr = RR

    assert pretty(expr) == "RR"
    assert upretty(expr) == u"ℝ"

    expr = QQ[x]

    assert pretty(expr) == "QQ[x]"
    assert upretty(expr) == u"ℚ[x]"

    expr = QQ[x, y]

    assert pretty(expr) == "QQ[x, y]"
    assert upretty(expr) == u"ℚ[x, y]"

    expr = ZZ.frac_field(x)

    assert pretty(expr) == "ZZ(x)"
    assert upretty(expr) == u"ℤ(x)"

    expr = ZZ.frac_field(x, y)

    assert pretty(expr) == "ZZ(x, y)"
    assert upretty(expr) == u"ℤ(x, y)"

    expr = QQ.poly_ring(x, y, order=grlex)

    assert pretty(expr) == "QQ[x, y, order=grlex]"
    assert upretty(expr) == u"ℚ[x, y, order=grlex]"

    expr = QQ.poly_ring(x, y, order=ilex)

    assert pretty(expr) == "QQ[x, y, order=ilex]"
    assert upretty(expr) == u"ℚ[x, y, order=ilex]"


def test_pretty_prec():
    assert xpretty(S("0.3"), full_prec=True, wrap_line=False) == "0.300000000000000"
    assert xpretty(S("0.3"), full_prec="auto", wrap_line=False) == "0.300000000000000"
    assert xpretty(S("0.3"), full_prec=False, wrap_line=False) == "0.3"
    assert xpretty(S("0.3")*x, full_prec=True, use_unicode=False, wrap_line=False) in [
        "0.300000000000000*x",
        "x*0.300000000000000"
    ]
    assert xpretty(S("0.3")*x, full_prec="auto", use_unicode=False, wrap_line=False) in [
        "0.3*x",
        "x*0.3"
    ]
    assert xpretty(S("0.3")*x, full_prec=False, use_unicode=False, wrap_line=False) in [
        "0.3*x",
        "x*0.3"
    ]


def test_pprint():
    import sys
    from sympy.core.compatibility import StringIO
    fd = StringIO()
    sso = sys.stdout
    sys.stdout = fd
    try:
        pprint(pi, use_unicode=False, wrap_line=False)
    finally:
        sys.stdout = sso
    assert fd.getvalue() == 'pi\n'


def test_pretty_class():
    """Test that the printer dispatcher correctly handles classes."""
    class C:
        pass   # C has no .__class__ and this was causing problems

    class D(object):
        pass

    assert pretty( C ) == str( C )
    assert pretty( D ) == str( D )


def test_pretty_no_wrap_line():
    huge_expr = 0
    for i in range(20):
        huge_expr += i*sin(i + x)
    assert xpretty(huge_expr            ).find('\n') != -1
    assert xpretty(huge_expr, wrap_line=False).find('\n') == -1


def test_settings():
    raises(TypeError, lambda: pretty(S(4), method="garbage"))


def test_pretty_sum():
    from sympy.abc import x, a, b, k, m, n

    expr = Sum(k**k, (k, 0, n))
    ascii_str = \
"""\
  n     \n\
 ___    \n\
 \\  `   \n\
  \\    k\n\
  /   k \n\
 /__,   \n\
k = 0   \
"""
    ucode_str = \
u("""\
  n     \n\
 ___    \n\
 ╲      \n\
  ╲    k\n\
  ╱   k \n\
 ╱      \n\
 ‾‾‾    \n\
k = 0   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(k**k, (k, oo, n))
    ascii_str = \
"""\
  n      \n\
 ___     \n\
 \\  `    \n\
  \\     k\n\
  /    k \n\
 /__,    \n\
k = oo   \
"""
    ucode_str = \
u("""\
  n     \n\
 ___    \n\
 ╲      \n\
  ╲    k\n\
  ╱   k \n\
 ╱      \n\
 ‾‾‾    \n\
k = ∞   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(k**(Integral(x**n, (x, -oo, oo))), (k, 0, n**n))
    ascii_str = \
"""\
    n             \n\
   n              \n\
______            \n\
\\     `           \n\
 \\        oo      \n\
  \\        /      \n\
   \\      |       \n\
    \\     |   n   \n\
     )    |  x  dx\n\
    /     |       \n\
   /     /        \n\
  /      -oo      \n\
 /      k         \n\
/_____,           \n\
 k = 0            \
"""
    ucode_str = \
u("""\
   n            \n\
  n             \n\
______          \n\
╲               \n\
 ╲      ∞       \n\
  ╲     ⌠       \n\
   ╲    ⎮   n   \n\
    ╲   ⎮  x  dx\n\
    ╱   ⌡       \n\
   ╱    -∞      \n\
  ╱    k        \n\
 ╱              \n\
╱               \n\
‾‾‾‾‾‾          \n\
k = 0           \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(k**(
        Integral(x**n, (x, -oo, oo))), (k, 0, Integral(x**x, (x, -oo, oo))))
    ascii_str = \
"""\
 oo                 \n\
  /                 \n\
 |                  \n\
 |   x              \n\
 |  x  dx           \n\
 |                  \n\
/                   \n\
-oo                 \n\
 ______             \n\
 \\     `            \n\
  \\         oo      \n\
   \\         /      \n\
    \\       |       \n\
     \\      |   n   \n\
      )     |  x  dx\n\
     /      |       \n\
    /      /        \n\
   /       -oo      \n\
  /       k         \n\
 /_____,            \n\
  k = 0             \
"""
    ucode_str = \
u("""\
∞                 \n\
⌠                 \n\
⎮   x             \n\
⎮  x  dx          \n\
⌡                 \n\
-∞                \n\
 ______           \n\
 ╲                \n\
  ╲       ∞       \n\
   ╲      ⌠       \n\
    ╲     ⎮   n   \n\
     ╲    ⎮  x  dx\n\
     ╱    ⌡       \n\
    ╱     -∞      \n\
   ╱     k        \n\
  ╱               \n\
 ╱                \n\
 ‾‾‾‾‾‾           \n\
 k = 0            \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(k**(Integral(x**n, (x, -oo, oo))), (
        k, x + n + x**2 + n**2 + (x/n) + (1/x), Integral(x**x, (x, -oo, oo))))
    ascii_str = \
"""\
          oo                          \n\
           /                          \n\
          |                           \n\
          |   x                       \n\
          |  x  dx                    \n\
          |                           \n\
         /                            \n\
         -oo                          \n\
          ______                      \n\
          \\     `                     \n\
           \\                  oo      \n\
            \\                  /      \n\
             \\                |       \n\
              \\               |   n   \n\
               )              |  x  dx\n\
              /               |       \n\
             /               /        \n\
            /                -oo      \n\
           /                k         \n\
          /_____,                     \n\
     2        2       1   x           \n\
k = n  + n + x  + x + - + -           \n\
                      x   n           \
"""
    ucode_str = \
u("""\
          ∞                          \n\
          ⌠                          \n\
          ⎮   x                      \n\
          ⎮  x  dx                   \n\
          ⌡                          \n\
          -∞                         \n\
           ______                    \n\
           ╲                         \n\
            ╲                ∞       \n\
             ╲               ⌠       \n\
              ╲              ⎮   n   \n\
               ╲             ⎮  x  dx\n\
               ╱             ⌡       \n\
              ╱              -∞      \n\
             ╱              k        \n\
            ╱                        \n\
           ╱                         \n\
           ‾‾‾‾‾‾                    \n\
     2        2       1   x          \n\
k = n  + n + x  + x + ─ + ─          \n\
                      x   n          \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(k**(
        Integral(x**n, (x, -oo, oo))), (k, 0, x + n + x**2 + n**2 + (x/n) + (1/x)))
    ascii_str = \
"""\
 2        2       1   x           \n\
n  + n + x  + x + - + -           \n\
                  x   n           \n\
        ______                    \n\
        \\     `                   \n\
         \\                oo      \n\
          \\                /      \n\
           \\              |       \n\
            \\             |   n   \n\
             )            |  x  dx\n\
            /             |       \n\
           /             /        \n\
          /              -oo      \n\
         /              k         \n\
        /_____,                   \n\
         k = 0                    \
"""
    ucode_str = \
u("""\
 2        2       1   x          \n\
n  + n + x  + x + ─ + ─          \n\
                  x   n          \n\
         ______                  \n\
         ╲                       \n\
          ╲              ∞       \n\
           ╲             ⌠       \n\
            ╲            ⎮   n   \n\
             ╲           ⎮  x  dx\n\
             ╱           ⌡       \n\
            ╱            -∞      \n\
           ╱            k        \n\
          ╱                      \n\
         ╱                       \n\
         ‾‾‾‾‾‾                  \n\
         k = 0                   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(x, (x, 0, oo))
    ascii_str = \
"""\
  oo   \n\
 __    \n\
 \\ `   \n\
  )   x\n\
 /_,   \n\
x = 0  \
"""
    ucode_str = \
u("""\
  ∞    \n\
 ___   \n\
 ╲     \n\
  ╲   x\n\
  ╱    \n\
 ╱     \n\
 ‾‾‾   \n\
x = 0  \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(x**2, (x, 0, oo))
    ascii_str = \
u("""\
  oo    \n\
 ___    \n\
 \\  `   \n\
  \\    2\n\
  /   x \n\
 /__,   \n\
x = 0   \
""")
    ucode_str = \
u("""\
  ∞     \n\
 ___    \n\
 ╲      \n\
  ╲    2\n\
  ╱   x \n\
 ╱      \n\
 ‾‾‾    \n\
x = 0   \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(x/2, (x, 0, oo))
    ascii_str = \
"""\
  oo   \n\
 ___   \n\
 \\  `  \n\
  \\   x\n\
   )  -\n\
  /   2\n\
 /__,  \n\
x = 0  \
"""
    ucode_str = \
u("""\
  ∞    \n\
 ____  \n\
 ╲     \n\
  ╲   x\n\
   ╲  ─\n\
   ╱  2\n\
  ╱    \n\
 ╱     \n\
 ‾‾‾‾  \n\
x = 0  \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(x**3/2, (x, 0, oo))
    ascii_str = \
"""\
  oo    \n\
____    \n\
\\   `   \n\
 \\     3\n\
  \\   x \n\
  /   --\n\
 /    2 \n\
/___,   \n\
x = 0   \
"""
    ucode_str = \
u("""\
  ∞     \n\
 ____   \n\
 ╲      \n\
  ╲    3\n\
   ╲  x \n\
   ╱  ──\n\
  ╱   2 \n\
 ╱      \n\
 ‾‾‾‾   \n\
x = 0   \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum((x**3*y**(x/2))**n, (x, 0, oo))
    ascii_str = \
"""\
  oo          \n\
____          \n\
\\   `         \n\
 \\           n\n\
  \\   /    x\\ \n\
   )  |    -| \n\
  /   | 3  2| \n\
 /    \\x *y / \n\
/___,         \n\
x = 0         \
"""
    ucode_str = \
u("""\
  ∞           \n\
_____         \n\
╲             \n\
 ╲           n\n\
  ╲   ⎛    x⎞ \n\
   ╲  ⎜    ─⎟ \n\
   ╱  ⎜ 3  2⎟ \n\
  ╱   ⎝x ⋅y ⎠ \n\
 ╱            \n\
╱             \n\
‾‾‾‾‾         \n\
x = 0         \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(1/x**2, (x, 0, oo))
    ascii_str = \
"""\
  oo    \n\
____    \n\
\\   `   \n\
 \\    1 \n\
  \\   --\n\
  /    2\n\
 /    x \n\
/___,   \n\
x = 0   \
"""
    ucode_str = \
u("""\
  ∞     \n\
 ____   \n\
 ╲      \n\
  ╲   1 \n\
   ╲  ──\n\
   ╱   2\n\
  ╱   x \n\
 ╱      \n\
 ‾‾‾‾   \n\
x = 0   \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(1/y**(a/b), (x, 0, oo))
    ascii_str = \
"""\
  oo      \n\
____      \n\
\\   `     \n\
 \\     -a \n\
  \\    ---\n\
  /     b \n\
 /    y   \n\
/___,     \n\
x = 0     \
"""
    ucode_str = \
u("""\
  ∞       \n\
 ____     \n\
 ╲        \n\
  ╲    -a \n\
   ╲   ───\n\
   ╱    b \n\
  ╱   y   \n\
 ╱        \n\
 ‾‾‾‾     \n\
x = 0     \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Sum(1/y**(a/b), (x, 0, oo), (y, 1, 2))
    ascii_str = \
"""\
  2     oo     \n\
____  ____     \n\
\\   ` \\   `    \n\
 \\     \\     -a\n\
  \\     \\    --\n\
  /     /    b \n\
 /     /    y  \n\
/___, /___,    \n\
y = 1 x = 0    \
"""
    ucode_str = \
u("""\
  2     ∞      \n\
____  ____     \n\
╲     ╲        \n\
 ╲     ╲     -a\n\
  ╲     ╲    ──\n\
  ╱     ╱    b \n\
 ╱     ╱    y  \n\
╱     ╱        \n\
‾‾‾‾  ‾‾‾‾     \n\
y = 1 x = 0    \
""")
    expr = Sum(1/(1 + 1/(
        1 + 1/k)) + 1, (k, 111, 1 + 1/n), (k, 1/(1 + m), oo)) + 1/(1 + 1/k)
    ascii_str = \
"""\
               1                         \n\
           1 + -                         \n\
    oo         n                         \n\
  _____    _____                         \n\
  \\    `   \\    `                        \n\
   \\        \\     /        1    \\        \n\
    \\        \\    |1 + ---------|        \n\
     \\        \\   |          1  |     1  \n\
      )        )  |    1 + -----| + -----\n\
     /        /   |            1|       1\n\
    /        /    |        1 + -|   1 + -\n\
   /        /     \\            k/       k\n\
  /____,   /____,                        \n\
      1   k = 111                        \n\
k = -----                                \n\
    m + 1                                \
"""
    ucode_str = \
u("""\
               1                         \n\
           1 + ─                         \n\
    ∞          n                         \n\
  ______   ______                        \n\
  ╲        ╲                             \n\
   ╲        ╲     ⎛        1    ⎞        \n\
    ╲        ╲    ⎜1 + ─────────⎟        \n\
     ╲        ╲   ⎜          1  ⎟        \n\
      ╲        ╲  ⎜    1 + ─────⎟     1  \n\
      ╱        ╱  ⎜            1⎟ + ─────\n\
     ╱        ╱   ⎜        1 + ─⎟       1\n\
    ╱        ╱    ⎝            k⎠   1 + ─\n\
   ╱        ╱                           k\n\
  ╱        ╱                             \n\
  ‾‾‾‾‾‾   ‾‾‾‾‾‾                        \n\
      1   k = 111                        \n\
k = ─────                                \n\
    m + 1                                \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_units():
    expr = joule
    ascii_str1 = \
"""\
              2\n\
kilogram*meter \n\
---------------\n\
          2    \n\
    second     \
"""
    unicode_str1 = \
u("""\
              2\n\
kilogram⋅meter \n\
───────────────\n\
          2    \n\
    second     \
""")

    ascii_str2 = \
"""\
                    2\n\
3*x*y*kilogram*meter \n\
---------------------\n\
             2       \n\
       second        \
"""
    unicode_str2 = \
u("""\
                    2\n\
3⋅x⋅y⋅kilogram⋅meter \n\
─────────────────────\n\
             2       \n\
       second        \
""")

    from sympy.physics.units import kg, m, s
    assert upretty(expr) == u("joule")
    assert pretty(expr) == "joule"
    assert upretty(expr.convert_to(kg*m**2/s**2)) == unicode_str1
    assert pretty(expr.convert_to(kg*m**2/s**2)) == ascii_str1
    assert upretty(3*kg*x*m**2*y/s**2) == unicode_str2
    assert pretty(3*kg*x*m**2*y/s**2) == ascii_str2

def test_pretty_Subs():
    f = Function('f')
    expr = Subs(f(x), x, ph**2)
    ascii_str = \
"""\
(f(x))|     2\n\
      |x=phi \
"""
    unicode_str = \
u("""\
(f(x))│   2\n\
      │x=φ \
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == unicode_str

    expr = Subs(f(x).diff(x), x, 0)
    ascii_str = \
"""\
/d       \\|   \n\
|--(f(x))||   \n\
\\dx      /|x=0\
"""
    unicode_str = \
u("""\
⎛d       ⎞│   \n\
⎜──(f(x))⎟│   \n\
⎝dx      ⎠│x=0\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == unicode_str

    expr = Subs(f(x).diff(x)/y, (x, y), (0, Rational(1, 2)))
    ascii_str = \
"""\
/d       \\|          \n\
|--(f(x))||          \n\
|dx      ||          \n\
|--------||          \n\
\\   y    /|x=0, y=1/2\
"""
    unicode_str = \
u("""\
⎛d       ⎞│          \n\
⎜──(f(x))⎟│          \n\
⎜dx      ⎟│          \n\
⎜────────⎟│          \n\
⎝   y    ⎠│x=0, y=1/2\
""")

    assert pretty(expr) == ascii_str
    assert upretty(expr) == unicode_str


def test_gammas():
    assert upretty(lowergamma(x, y)) == u"γ(x, y)"
    assert upretty(uppergamma(x, y)) == u"Γ(x, y)"
    assert xpretty(gamma(x), use_unicode=True) == u'Γ(x)'
    assert xpretty(gamma, use_unicode=True) == u'Γ'
    assert xpretty(symbols('gamma', cls=Function)(x), use_unicode=True) == u'γ(x)'
    assert xpretty(symbols('gamma', cls=Function), use_unicode=True) == u'γ'


def test_beta():
    assert xpretty(beta(x,y), use_unicode=True) == u'Β(x, y)'
    assert xpretty(beta(x,y), use_unicode=False) == u'B(x, y)'
    assert xpretty(beta, use_unicode=True) == u'Β'
    assert xpretty(beta, use_unicode=False) == u'B'
    mybeta = Function('beta')
    assert xpretty(mybeta(x), use_unicode=True) == u'β(x)'
    assert xpretty(mybeta(x, y, z), use_unicode=False) == u'beta(x, y, z)'
    assert xpretty(mybeta, use_unicode=True) == u'β'


# test that notation passes to subclasses of the same name only
def test_function_subclass_different_name():
    class mygamma(gamma):
        pass
    assert xpretty(mygamma, use_unicode=True) == r"mygamma"
    assert xpretty(mygamma(x), use_unicode=True) == r"mygamma(x)"


def test_SingularityFunction():
    assert xpretty(SingularityFunction(x, 0, n), use_unicode=True) == (
"""\
   n\n\
<x> \
""")
    assert xpretty(SingularityFunction(x, 1, n), use_unicode=True) == (
"""\
       n\n\
<x - 1> \
""")
    assert xpretty(SingularityFunction(x, -1, n), use_unicode=True) == (
"""\
       n\n\
<x + 1> \
""")
    assert xpretty(SingularityFunction(x, a, n), use_unicode=True) == (
"""\
        n\n\
<-a + x> \
""")
    assert xpretty(SingularityFunction(x, y, n), use_unicode=True) == (
"""\
       n\n\
<x - y> \
""")
    assert xpretty(SingularityFunction(x, 0, n), use_unicode=False) == (
"""\
   n\n\
<x> \
""")
    assert xpretty(SingularityFunction(x, 1, n), use_unicode=False) == (
"""\
       n\n\
<x - 1> \
""")
    assert xpretty(SingularityFunction(x, -1, n), use_unicode=False) == (
"""\
       n\n\
<x + 1> \
""")
    assert xpretty(SingularityFunction(x, a, n), use_unicode=False) == (
"""\
        n\n\
<-a + x> \
""")
    assert xpretty(SingularityFunction(x, y, n), use_unicode=False) == (
"""\
       n\n\
<x - y> \
""")


def test_deltas():
    assert xpretty(DiracDelta(x), use_unicode=True) == u'δ(x)'
    assert xpretty(DiracDelta(x, 1), use_unicode=True) == \
u("""\
 (1)    \n\
δ    (x)\
""")
    assert xpretty(x*DiracDelta(x, 1), use_unicode=True) == \
u("""\
   (1)    \n\
x⋅δ    (x)\
""")


def test_hyper():
    expr = hyper((), (), z)
    ucode_str = \
u("""\
 ┌─  ⎛  │  ⎞\n\
 ├─  ⎜  │ z⎟\n\
0╵ 0 ⎝  │  ⎠\
""")
    ascii_str = \
"""\
  _         \n\
 |_  /  |  \\\n\
 |   |  | z|\n\
0  0 \\  |  /\
"""
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = hyper((), (1,), x)
    ucode_str = \
u("""\
 ┌─  ⎛  │  ⎞\n\
 ├─  ⎜  │ x⎟\n\
0╵ 1 ⎝1 │  ⎠\
""")
    ascii_str = \
"""\
  _         \n\
 |_  /  |  \\\n\
 |   |  | x|\n\
0  1 \\1 |  /\
"""
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = hyper([2], [1], x)
    ucode_str = \
u("""\
 ┌─  ⎛2 │  ⎞\n\
 ├─  ⎜  │ x⎟\n\
1╵ 1 ⎝1 │  ⎠\
""")
    ascii_str = \
"""\
  _         \n\
 |_  /2 |  \\\n\
 |   |  | x|\n\
1  1 \\1 |  /\
"""
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = hyper((pi/3, -2*k), (3, 4, 5, -3), x)
    ucode_str = \
u("""\
     ⎛  π         │  ⎞\n\
 ┌─  ⎜  ─, -2⋅k   │  ⎟\n\
 ├─  ⎜  3         │ x⎟\n\
2╵ 4 ⎜            │  ⎟\n\
     ⎝3, 4, 5, -3 │  ⎠\
""")
    ascii_str = \
"""\
                      \n\
  _  /  pi        |  \\\n\
 |_  |  --, -2*k  |  |\n\
 |   |  3         | x|\n\
2  4 |            |  |\n\
     \\3, 4, 5, -3 |  /\
"""
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = hyper((pi, S('2/3'), -2*k), (3, 4, 5, -3), x**2)
    ucode_str = \
u("""\
 ┌─  ⎛π, 2/3, -2⋅k │  2⎞\n\
 ├─  ⎜             │ x ⎟\n\
3╵ 4 ⎝3, 4, 5, -3  │   ⎠\
""")
    ascii_str = \
"""\
  _                      \n\
 |_  /pi, 2/3, -2*k |  2\\\n\
 |   |              | x |\n\
3  4 \\ 3, 4, 5, -3  |   /\
"""
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = hyper([1, 2], [3, 4], 1/(1/(1/(1/x + 1) + 1) + 1))
    ucode_str = \
u("""\
     ⎛     │       1      ⎞\n\
     ⎜     │ ─────────────⎟\n\
     ⎜     │         1    ⎟\n\
 ┌─  ⎜1, 2 │ 1 + ─────────⎟\n\
 ├─  ⎜     │           1  ⎟\n\
2╵ 2 ⎜3, 4 │     1 + ─────⎟\n\
     ⎜     │             1⎟\n\
     ⎜     │         1 + ─⎟\n\
     ⎝     │             x⎠\
""")

    ascii_str = \
"""\
                           \n\
     /     |       1      \\\n\
     |     | -------------|\n\
  _  |     |         1    |\n\
 |_  |1, 2 | 1 + ---------|\n\
 |   |     |           1  |\n\
2  2 |3, 4 |     1 + -----|\n\
     |     |             1|\n\
     |     |         1 + -|\n\
     \\     |             x/\
"""
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_meijerg():
    expr = meijerg([pi, pi, x], [1], [0, 1], [1, 2, 3], z)
    ucode_str = \
u("""\
╭─╮2, 3 ⎛π, π, x     1    │  ⎞\n\
│╶┐     ⎜                 │ z⎟\n\
╰─╯4, 5 ⎝ 0, 1    1, 2, 3 │  ⎠\
""")
    ascii_str = \
"""\
 __2, 3 /pi, pi, x     1    |  \\\n\
/__     |                   | z|\n\
\\_|4, 5 \\  0, 1     1, 2, 3 |  /\
"""
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = meijerg([1, pi/7], [2, pi, 5], [], [], z**2)
    ucode_str = \
u("""\
        ⎛   π          │   ⎞\n\
╭─╮0, 2 ⎜1, ─  2, π, 5 │  2⎟\n\
│╶┐     ⎜   7          │ z ⎟\n\
╰─╯5, 0 ⎜              │   ⎟\n\
        ⎝              │   ⎠\
""")
    ascii_str = \
"""\
        /   pi           |   \\\n\
 __0, 2 |1, --  2, pi, 5 |  2|\n\
/__     |   7            | z |\n\
\\_|5, 0 |                |   |\n\
        \\                |   /\
"""
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    ucode_str = \
u("""\
╭─╮ 1, 10 ⎛1, 1, 1, 1, 1, 1, 1, 1, 1, 1  1 │  ⎞\n\
│╶┐       ⎜                                │ z⎟\n\
╰─╯11,  2 ⎝             1                1 │  ⎠\
""")
    ascii_str = \
"""\
 __ 1, 10 /1, 1, 1, 1, 1, 1, 1, 1, 1, 1  1 |  \\\n\
/__       |                                | z|\n\
\\_|11,  2 \\             1                1 |  /\
"""

    expr = meijerg([1]*10, [1], [1], [1], z)
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = meijerg([1, 2, ], [4, 3], [3], [4, 5], 1/(1/(1/(1/x + 1) + 1) + 1))

    ucode_str = \
u("""\
        ⎛           │       1      ⎞\n\
        ⎜           │ ─────────────⎟\n\
        ⎜           │         1    ⎟\n\
╭─╮1, 2 ⎜1, 2  4, 3 │ 1 + ─────────⎟\n\
│╶┐     ⎜           │           1  ⎟\n\
╰─╯4, 3 ⎜ 3    4, 5 │     1 + ─────⎟\n\
        ⎜           │             1⎟\n\
        ⎜           │         1 + ─⎟\n\
        ⎝           │             x⎠\
""")

    ascii_str = \
"""\
        /           |       1      \\\n\
        |           | -------------|\n\
        |           |         1    |\n\
 __1, 2 |1, 2  4, 3 | 1 + ---------|\n\
/__     |           |           1  |\n\
\\_|4, 3 | 3    4, 5 |     1 + -----|\n\
        |           |             1|\n\
        |           |         1 + -|\n\
        \\           |             x/\
"""

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = Integral(expr, x)

    ucode_str = \
u("""\
⌠                                        \n\
⎮         ⎛           │       1      ⎞   \n\
⎮         ⎜           │ ─────────────⎟   \n\
⎮         ⎜           │         1    ⎟   \n\
⎮ ╭─╮1, 2 ⎜1, 2  4, 3 │ 1 + ─────────⎟   \n\
⎮ │╶┐     ⎜           │           1  ⎟ dx\n\
⎮ ╰─╯4, 3 ⎜ 3    4, 5 │     1 + ─────⎟   \n\
⎮         ⎜           │             1⎟   \n\
⎮         ⎜           │         1 + ─⎟   \n\
⎮         ⎝           │             x⎠   \n\
⌡                                        \
""")

    ascii_str = \
"""\
  /                                       \n\
 |                                        \n\
 |         /           |       1      \\   \n\
 |         |           | -------------|   \n\
 |         |           |         1    |   \n\
 |  __1, 2 |1, 2  4, 3 | 1 + ---------|   \n\
 | /__     |           |           1  | dx\n\
 | \\_|4, 3 | 3    4, 5 |     1 + -----|   \n\
 |         |           |             1|   \n\
 |         |           |         1 + -|   \n\
 |         \\           |             x/   \n\
 |                                        \n\
/                                         \
"""

    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_noncommutative():
    A, B, C = symbols('A,B,C', commutative=False)

    expr = A*B*C**-1
    ascii_str = \
"""\
     -1\n\
A*B*C  \
"""
    ucode_str = \
u("""\
     -1\n\
A⋅B⋅C  \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = C**-1*A*B
    ascii_str = \
"""\
 -1    \n\
C  *A*B\
"""
    ucode_str = \
u("""\
 -1    \n\
C  ⋅A⋅B\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = A*C**-1*B
    ascii_str = \
"""\
   -1  \n\
A*C  *B\
"""
    ucode_str = \
u("""\
   -1  \n\
A⋅C  ⋅B\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = A*C**-1*B/x
    ascii_str = \
"""\
   -1  \n\
A*C  *B\n\
-------\n\
   x   \
"""
    ucode_str = \
u("""\
   -1  \n\
A⋅C  ⋅B\n\
───────\n\
   x   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_special_functions():
    x, y = symbols("x y")

    # atan2
    expr = atan2(y/sqrt(200), sqrt(x))
    ascii_str = \
"""\
     /  ___         \\\n\
     |\\/ 2 *y    ___|\n\
atan2|-------, \\/ x |\n\
     \\   20         /\
"""
    ucode_str = \
u("""\
     ⎛√2⋅y    ⎞\n\
atan2⎜────, √x⎟\n\
     ⎝ 20     ⎠\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_geometry():
    e = Segment((0, 1), (0, 2))
    assert pretty(e) == 'Segment2D(Point2D(0, 1), Point2D(0, 2))'
    e = Ray((1, 1), angle=4.02*pi)
    assert pretty(e) == 'Ray2D(Point2D(1, 1), Point2D(2, tan(pi/50) + 1))'


def test_expint():
    expr = Ei(x)
    string = 'Ei(x)'
    assert pretty(expr) == string
    assert upretty(expr) == string

    expr = expint(1, z)
    ucode_str = u"E₁(z)"
    ascii_str = "expint(1, z)"
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    assert pretty(Shi(x)) == 'Shi(x)'
    assert pretty(Si(x)) == 'Si(x)'
    assert pretty(Ci(x)) == 'Ci(x)'
    assert pretty(Chi(x)) == 'Chi(x)'
    assert upretty(Shi(x)) == 'Shi(x)'
    assert upretty(Si(x)) == 'Si(x)'
    assert upretty(Ci(x)) == 'Ci(x)'
    assert upretty(Chi(x)) == 'Chi(x)'


def test_elliptic_functions():
    ascii_str = \
"""\
 /  1  \\\n\
K|-----|\n\
 \\z + 1/\
"""
    ucode_str = \
u("""\
 ⎛  1  ⎞\n\
K⎜─────⎟\n\
 ⎝z + 1⎠\
""")
    expr = elliptic_k(1/(z + 1))
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    ascii_str = \
"""\
 / |  1  \\\n\
F|1|-----|\n\
 \\ |z + 1/\
"""
    ucode_str = \
u("""\
 ⎛ │  1  ⎞\n\
F⎜1│─────⎟\n\
 ⎝ │z + 1⎠\
""")
    expr = elliptic_f(1, 1/(1 + z))
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    ascii_str = \
"""\
 /  1  \\\n\
E|-----|\n\
 \\z + 1/\
"""
    ucode_str = \
u("""\
 ⎛  1  ⎞\n\
E⎜─────⎟\n\
 ⎝z + 1⎠\
""")
    expr = elliptic_e(1/(z + 1))
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    ascii_str = \
"""\
 / |  1  \\\n\
E|1|-----|\n\
 \\ |z + 1/\
"""
    ucode_str = \
u("""\
 ⎛ │  1  ⎞\n\
E⎜1│─────⎟\n\
 ⎝ │z + 1⎠\
""")
    expr = elliptic_e(1, 1/(1 + z))
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    ascii_str = \
"""\
  / |4\\\n\
Pi|3|-|\n\
  \\ |x/\
"""
    ucode_str = \
u("""\
 ⎛ │4⎞\n\
Π⎜3│─⎟\n\
 ⎝ │x⎠\
""")
    expr = elliptic_pi(3, 4/x)
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    ascii_str = \
"""\
  /   4| \\\n\
Pi|3; -|6|\n\
  \\   x| /\
"""
    ucode_str = \
u("""\
 ⎛   4│ ⎞\n\
Π⎜3; ─│6⎟\n\
 ⎝   x│ ⎠\
""")
    expr = elliptic_pi(3, 4/x, 6)
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_RandomDomain():
    from sympy.stats import Normal, Die, Exponential, pspace, where
    X = Normal('x1', 0, 1)
    assert upretty(where(X > 0)) == u"Domain: 0 < x₁ ∧ x₁ < ∞"

    D = Die('d1', 6)
    assert upretty(where(D > 4)) == u'Domain: d₁ = 5 ∨ d₁ = 6'

    A = Exponential('a', 1)
    B = Exponential('b', 1)
    assert upretty(pspace(Tuple(A, B)).domain) == \
        u'Domain: 0 ≤ a ∧ 0 ≤ b ∧ a < ∞ ∧ b < ∞'


def test_PrettyPoly():
    F = QQ.frac_field(x, y)
    R = QQ.poly_ring(x, y)

    expr = F.convert(x/(x + y))
    assert pretty(expr) == "x/(x + y)"
    assert upretty(expr) == u"x/(x + y)"

    expr = R.convert(x + y)
    assert pretty(expr) == "x + y"
    assert upretty(expr) == u"x + y"


def test_issue_6285():
    assert pretty(Pow(2, -5, evaluate=False)) == '1 \n--\n 5\n2 '
    assert pretty(Pow(x, (1/pi))) == 'pi___\n\\/ x '


def test_issue_6359():
    assert pretty(Integral(x**2, x)**2) == \
"""\
          2
/  /     \\ \n\
| |      | \n\
| |  2   | \n\
| | x  dx| \n\
| |      | \n\
\\/       / \
"""
    assert upretty(Integral(x**2, x)**2) == \
u("""\
         2
⎛⌠      ⎞ \n\
⎜⎮  2   ⎟ \n\
⎜⎮ x  dx⎟ \n\
⎝⌡      ⎠ \
""")

    assert pretty(Sum(x**2, (x, 0, 1))**2) == \
"""\
          2
/  1     \\ \n\
| ___    | \n\
| \\  `   | \n\
|  \\    2| \n\
|  /   x | \n\
| /__,   | \n\
\\x = 0   / \
"""
    assert upretty(Sum(x**2, (x, 0, 1))**2) == \
u("""\
          2
⎛  1     ⎞ \n\
⎜ ___    ⎟ \n\
⎜ ╲      ⎟ \n\
⎜  ╲    2⎟ \n\
⎜  ╱   x ⎟ \n\
⎜ ╱      ⎟ \n\
⎜ ‾‾‾    ⎟ \n\
⎝x = 0   ⎠ \
""")

    assert pretty(Product(x**2, (x, 1, 2))**2) == \
"""\
           2
/  2      \\ \n\
|______   | \n\
| |  |   2| \n\
| |  |  x | \n\
| |  |    | \n\
\\x = 1    / \
"""
    assert upretty(Product(x**2, (x, 1, 2))**2) == \
u("""\
           2
⎛  2      ⎞ \n\
⎜─┬──┬─   ⎟ \n\
⎜ │  │   2⎟ \n\
⎜ │  │  x ⎟ \n\
⎜ │  │    ⎟ \n\
⎝x = 1    ⎠ \
""")

    f = Function('f')
    assert pretty(Derivative(f(x), x)**2) == \
"""\
          2
/d       \\ \n\
|--(f(x))| \n\
\\dx      / \
"""
    assert upretty(Derivative(f(x), x)**2) == \
u("""\
          2
⎛d       ⎞ \n\
⎜──(f(x))⎟ \n\
⎝dx      ⎠ \
""")

def test_issue_6739():
    ascii_str = \
"""\
  1  \n\
-----\n\
  ___\n\
\\/ x \
"""
    ucode_str = \
u("""\
1 \n\
──\n\
√x\
""")
    assert pretty(1/sqrt(x)) == ascii_str
    assert upretty(1/sqrt(x)) == ucode_str


def test_complicated_symbol_unchanged():
    for symb_name in ["dexpr2_d1tau", "dexpr2^d1tau"]:
        assert pretty(Symbol(symb_name)) == symb_name


def test_categories():
    from sympy.categories import (Object, IdentityMorphism,
        NamedMorphism, Category, Diagram, DiagramGrid)

    A1 = Object("A1")
    A2 = Object("A2")
    A3 = Object("A3")

    f1 = NamedMorphism(A1, A2, "f1")
    f2 = NamedMorphism(A2, A3, "f2")
    id_A1 = IdentityMorphism(A1)

    K1 = Category("K1")

    assert pretty(A1) == "A1"
    assert upretty(A1) == u"A₁"

    assert pretty(f1) == "f1:A1-->A2"
    assert upretty(f1) == u"f₁:A₁——▶A₂"
    assert pretty(id_A1) == "id:A1-->A1"
    assert upretty(id_A1) == u"id:A₁——▶A₁"

    assert pretty(f2*f1) == "f2*f1:A1-->A3"
    assert upretty(f2*f1) == u"f₂∘f₁:A₁——▶A₃"

    assert pretty(K1) == "K1"
    assert upretty(K1) == u"K₁"

    # Test how diagrams are printed.
    d = Diagram()
    assert pretty(d) == "EmptySet()"
    assert upretty(d) == u"∅"

    d = Diagram({f1: "unique", f2: S.EmptySet})
    assert pretty(d) == "{f2*f1:A1-->A3: EmptySet(), id:A1-->A1: " \
        "EmptySet(), id:A2-->A2: EmptySet(), id:A3-->A3: " \
        "EmptySet(), f1:A1-->A2: {unique}, f2:A2-->A3: EmptySet()}"

    assert upretty(d) == u("{f₂∘f₁:A₁——▶A₃: ∅, id:A₁——▶A₁: ∅, " \
        "id:A₂——▶A₂: ∅, id:A₃——▶A₃: ∅, f₁:A₁——▶A₂: {unique}, f₂:A₂——▶A₃: ∅}")

    d = Diagram({f1: "unique", f2: S.EmptySet}, {f2 * f1: "unique"})
    assert pretty(d) == "{f2*f1:A1-->A3: EmptySet(), id:A1-->A1: " \
        "EmptySet(), id:A2-->A2: EmptySet(), id:A3-->A3: " \
        "EmptySet(), f1:A1-->A2: {unique}, f2:A2-->A3: EmptySet()}" \
        " ==> {f2*f1:A1-->A3: {unique}}"
    assert upretty(d) == u("{f₂∘f₁:A₁——▶A₃: ∅, id:A₁——▶A₁: ∅, id:A₂——▶A₂: " \
        "∅, id:A₃——▶A₃: ∅, f₁:A₁——▶A₂: {unique}, f₂:A₂——▶A₃: ∅}" \
        " ══▶ {f₂∘f₁:A₁——▶A₃: {unique}}")

    grid = DiagramGrid(d)
    assert pretty(grid) == "A1  A2\n      \nA3    "
    assert upretty(grid) == u"A₁  A₂\n      \nA₃    "


def test_PrettyModules():
    R = QQ.old_poly_ring(x, y)
    F = R.free_module(2)
    M = F.submodule([x, y], [1, x**2])

    ucode_str = \
u("""\
       2\n\
ℚ[x, y] \
""")
    ascii_str = \
"""\
        2\n\
QQ[x, y] \
"""

    assert upretty(F) == ucode_str
    assert pretty(F) == ascii_str

    ucode_str = \
u("""\
╱        ⎡    2⎤╲\n\
╲[x, y], ⎣1, x ⎦╱\
""")
    ascii_str = \
"""\
              2  \n\
<[x, y], [1, x ]>\
"""

    assert upretty(M) == ucode_str
    assert pretty(M) == ascii_str

    I = R.ideal(x**2, y)

    ucode_str = \
u("""\
╱ 2   ╲\n\
╲x , y╱\
""")

    ascii_str = \
"""\
  2    \n\
<x , y>\
"""

    assert upretty(I) == ucode_str
    assert pretty(I) == ascii_str

    Q = F / M

    ucode_str = \
u("""\
            2    \n\
     ℚ[x, y]     \n\
─────────────────\n\
╱        ⎡    2⎤╲\n\
╲[x, y], ⎣1, x ⎦╱\
""")

    ascii_str = \
"""\
            2    \n\
    QQ[x, y]     \n\
-----------------\n\
              2  \n\
<[x, y], [1, x ]>\
"""

    assert upretty(Q) == ucode_str
    assert pretty(Q) == ascii_str

    ucode_str = \
u("""\
╱⎡    3⎤                                                ╲\n\
│⎢   x ⎥   ╱        ⎡    2⎤╲           ╱        ⎡    2⎤╲│\n\
│⎢1, ──⎥ + ╲[x, y], ⎣1, x ⎦╱, [2, y] + ╲[x, y], ⎣1, x ⎦╱│\n\
╲⎣   2 ⎦                                                ╱\
""")

    ascii_str = \
"""\
      3                                                  \n\
     x                   2                           2   \n\
<[1, --] + <[x, y], [1, x ]>, [2, y] + <[x, y], [1, x ]>>\n\
     2                                                   \
"""


def test_QuotientRing():
    R = QQ.old_poly_ring(x)/[x**2 + 1]

    ucode_str = \
u("""\
  ℚ[x]  \n\
────────\n\
╱ 2    ╲\n\
╲x  + 1╱\
""")

    ascii_str = \
"""\
 QQ[x]  \n\
--------\n\
  2     \n\
<x  + 1>\
"""

    assert upretty(R) == ucode_str
    assert pretty(R) == ascii_str

    ucode_str = \
u("""\
    ╱ 2    ╲\n\
1 + ╲x  + 1╱\
""")

    ascii_str = \
"""\
      2     \n\
1 + <x  + 1>\
"""

    assert upretty(R.one) == ucode_str
    assert pretty(R.one) == ascii_str


def test_Homomorphism():
    from sympy.polys.agca import homomorphism

    R = QQ.old_poly_ring(x)

    expr = homomorphism(R.free_module(1), R.free_module(1), [0])

    ucode_str = \
u("""\
          1         1\n\
[0] : ℚ[x]  ──> ℚ[x] \
""")

    ascii_str = \
"""\
           1          1\n\
[0] : QQ[x]  --> QQ[x] \
"""

    assert upretty(expr) == ucode_str
    assert pretty(expr) == ascii_str

    expr = homomorphism(R.free_module(2), R.free_module(2), [0, 0])

    ucode_str = \
u("""\
⎡0  0⎤       2         2\n\
⎢    ⎥ : ℚ[x]  ──> ℚ[x] \n\
⎣0  0⎦                  \
""")

    ascii_str = \
"""\
[0  0]        2          2\n\
[    ] : QQ[x]  --> QQ[x] \n\
[0  0]                    \
"""

    assert upretty(expr) == ucode_str
    assert pretty(expr) == ascii_str

    expr = homomorphism(R.free_module(1), R.free_module(1) / [[x]], [0])

    ucode_str = \
u("""\
                    1\n\
          1     ℚ[x] \n\
[0] : ℚ[x]  ──> ─────\n\
                <[x]>\
""")

    ascii_str = \
"""\
                      1\n\
           1     QQ[x] \n\
[0] : QQ[x]  --> ------\n\
                 <[x]> \
"""

    assert upretty(expr) == ucode_str
    assert pretty(expr) == ascii_str


def test_Tr():
    A, B = symbols('A B', commutative=False)
    t = Tr(A*B)
    assert pretty(t) == r'Tr(A*B)'
    assert upretty(t) == u'Tr(A⋅B)'


def test_pretty_Add():
    eq = Mul(-2, x - 2, evaluate=False) + 5
    assert pretty(eq) == '5 - 2*(x - 2)'


def test_issue_7179():
    assert upretty(Not(Equivalent(x, y))) == u'x ⇎ y'
    assert upretty(Not(Implies(x, y))) == u'x ↛ y'


def test_issue_7180():
    assert upretty(Equivalent(x, y)) == u'x ⇔ y'


def test_pretty_Complement():
    assert pretty(S.Reals - S.Naturals) == '(-oo, oo) \\ Naturals'
    assert upretty(S.Reals - S.Naturals) == u'ℝ \\ ℕ'
    assert pretty(S.Reals - S.Naturals0) == '(-oo, oo) \\ Naturals0'
    assert upretty(S.Reals - S.Naturals0) == u'ℝ \\ ℕ₀'


def test_pretty_SymmetricDifference():
    from sympy import SymmetricDifference, Interval
    from sympy.utilities.pytest import raises
    assert upretty(SymmetricDifference(Interval(2,3), Interval(3,5), \
           evaluate = False)) == u'[2, 3] ∆ [3, 5]'
    with raises(NotImplementedError):
        pretty(SymmetricDifference(Interval(2,3), Interval(3,5), evaluate = False))


def test_pretty_Contains():
    assert pretty(Contains(x, S.Integers)) == 'Contains(x, Integers)'
    assert upretty(Contains(x, S.Integers)) == u'x ∈ ℤ'


def test_issue_8292():
    from sympy.core import sympify
    e = sympify('((x+x**4)/(x-1))-(2*(x-1)**4/(x-1)**4)', evaluate=False)
    ucode_str = \
u("""\
           4    4    \n\
  2⋅(x - 1)    x  + x\n\
- ────────── + ──────\n\
          4    x - 1 \n\
   (x - 1)           \
""")
    ascii_str = \
"""\
           4    4    \n\
  2*(x - 1)    x  + x\n\
- ---------- + ------\n\
          4    x - 1 \n\
   (x - 1)           \
"""
    assert pretty(e) == ascii_str
    assert upretty(e) == ucode_str


def test_issue_4335():
    y = Function('y')
    expr = -y(x).diff(x)
    ucode_str = \
u("""\
 d       \n\
-──(y(x))\n\
 dx      \
""")
    ascii_str = \
"""\
  d       \n\
- --(y(x))\n\
  dx      \
"""
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_issue_8344():
    from sympy.core import sympify
    e = sympify('2*x*y**2/1**2 + 1', evaluate=False)
    ucode_str = \
u("""\
     2    \n\
2⋅x⋅y     \n\
────── + 1\n\
   2      \n\
  1       \
""")
    assert upretty(e) == ucode_str


def test_issue_6324():
    x = Pow(2, 3, evaluate=False)
    y = Pow(10, -2, evaluate=False)
    e = Mul(x, y, evaluate=False)
    ucode_str = \
u("""\
  3\n\
 2 \n\
───\n\
  2\n\
10 \
""")
    assert upretty(e) == ucode_str


def test_issue_7927():
    e = sin(x/2)**cos(x/2)
    ucode_str = \
u("""\
           ⎛x⎞\n\
        cos⎜─⎟\n\
           ⎝2⎠\n\
⎛   ⎛x⎞⎞      \n\
⎜sin⎜─⎟⎟      \n\
⎝   ⎝2⎠⎠      \
""")
    assert upretty(e) == ucode_str
    e = sin(x)**(S(11)/13)
    ucode_str = \
u("""\
        11\n\
        ──\n\
        13\n\
(sin(x))  \
""")
    assert upretty(e) == ucode_str


def test_issue_6134():
    from sympy.abc import lamda, t
    phi = Function('phi')

    e = lamda*x*Integral(phi(t)*pi*sin(pi*t), (t, 0, 1)) + lamda*x**2*Integral(phi(t)*2*pi*sin(2*pi*t), (t, 0, 1))
    ucode_str = \
u("""\
     1                              1                   \n\
   2 ⌠                              ⌠                   \n\
λ⋅x ⋅⎮ 2⋅π⋅φ(t)⋅sin(2⋅π⋅t) dt + λ⋅x⋅⎮ π⋅φ(t)⋅sin(π⋅t) dt\n\
     ⌡                              ⌡                   \n\
     0                              0                   \
""")
    assert upretty(e) == ucode_str


def test_issue_9877():
    ucode_str1 = u'(2, 3) ∪ ([1, 2] \\ {x})'
    a, b, c = Interval(2, 3, True, True), Interval(1, 2), FiniteSet(x)
    assert upretty(Union(a, Complement(b, c))) == ucode_str1

    ucode_str2 = u'{x} ∩ {y} ∩ ({z} \\ [1, 2])'
    d, e, f, g = FiniteSet(x), FiniteSet(y), FiniteSet(z), Interval(1, 2)
    assert upretty(Intersection(d, e, Complement(f, g))) == ucode_str2


def test_issue_13651():
    expr1 = c + Mul(-1, a + b, evaluate=False)
    assert pretty(expr1) == 'c - (a + b)'
    expr2 = c + Mul(-1, a - b + d, evaluate=False)
    assert pretty(expr2) == 'c - (a - b + d)'


def test_pretty_primenu():
    from sympy.ntheory.factor_ import primenu

    ascii_str1 = "nu(n)"
    ucode_str1 = u("ν(n)")

    n = symbols('n', integer=True)
    assert pretty(primenu(n)) == ascii_str1
    assert upretty(primenu(n)) == ucode_str1


def test_pretty_primeomega():
    from sympy.ntheory.factor_ import primeomega

    ascii_str1 = "Omega(n)"
    ucode_str1 = u("Ω(n)")

    n = symbols('n', integer=True)
    assert pretty(primeomega(n)) == ascii_str1
    assert upretty(primeomega(n)) == ucode_str1


def test_pretty_Mod():
    from sympy.core import Mod

    ascii_str1 = "x mod 7"
    ucode_str1 = u("x mod 7")

    ascii_str2 = "(x + 1) mod 7"
    ucode_str2 = u("(x + 1) mod 7")

    ascii_str3 = "2*x mod 7"
    ucode_str3 = u("2⋅x mod 7")

    ascii_str4 = "(x mod 7) + 1"
    ucode_str4 = u("(x mod 7) + 1")

    ascii_str5 = "2*(x mod 7)"
    ucode_str5 = u("2⋅(x mod 7)")

    x = symbols('x', integer=True)
    assert pretty(Mod(x, 7)) == ascii_str1
    assert upretty(Mod(x, 7)) == ucode_str1
    assert pretty(Mod(x + 1, 7)) == ascii_str2
    assert upretty(Mod(x + 1, 7)) == ucode_str2
    assert pretty(Mod(2 * x, 7)) == ascii_str3
    assert upretty(Mod(2 * x, 7)) == ucode_str3
    assert pretty(Mod(x, 7) + 1) == ascii_str4
    assert upretty(Mod(x, 7) + 1) == ucode_str4
    assert pretty(2 * Mod(x, 7)) == ascii_str5
    assert upretty(2 * Mod(x, 7)) == ucode_str5


def test_issue_11801():
    assert pretty(Symbol("")) == ""
    assert upretty(Symbol("")) == ""


def test_pretty_UnevaluatedExpr():
    x = symbols('x')
    he = UnevaluatedExpr(1/x)

    ucode_str = \
u("""\
1\n\
─\n\
x\
""")

    assert upretty(he) == ucode_str

    ucode_str = \
u("""\
   2\n\
⎛1⎞ \n\
⎜─⎟ \n\
⎝x⎠ \
""")

    assert upretty(he**2) == ucode_str

    ucode_str = \
u("""\
    1\n\
1 + ─\n\
    x\
""")

    assert upretty(he + 1) == ucode_str

    ucode_str = \
u('''\
  1\n\
x⋅─\n\
  x\
''')
    assert upretty(x*he) == ucode_str


def test_issue_10472():
    M = (Matrix([[0, 0], [0, 0]]), Matrix([0, 0]))

    ucode_str = \
u("""\
⎛⎡0  0⎤  ⎡0⎤⎞
⎜⎢    ⎥, ⎢ ⎥⎟
⎝⎣0  0⎦  ⎣0⎦⎠\
""")
    assert upretty(M) == ucode_str


def test_MatrixElement_printing():
    # test cases for issue #11821
    A = MatrixSymbol("A", 1, 3)
    B = MatrixSymbol("B", 1, 3)
    C = MatrixSymbol("C", 1, 3)

    ascii_str1 = "A_00"
    ucode_str1 = u("A₀₀")
    assert pretty(A[0, 0])  == ascii_str1
    assert upretty(A[0, 0]) == ucode_str1

    ascii_str1 = "3*A_00"
    ucode_str1 = u("3⋅A₀₀")
    assert pretty(3*A[0, 0])  == ascii_str1
    assert upretty(3*A[0, 0]) == ucode_str1

    ascii_str1 = "(-B + A)[0, 0]"
    ucode_str1 = u("(-B + A)[0, 0]")
    F = C[0, 0].subs(C, A - B)
    assert pretty(F)  == ascii_str1
    assert upretty(F) == ucode_str1


def test_issue_12675():
    from sympy.vector import CoordSys3D
    x, y, t, j = symbols('x y t j')
    e = CoordSys3D('e')

    ucode_str = \
u("""\
⎛   t⎞    \n\
⎜⎛x⎞ ⎟ e_j\n\
⎜⎜─⎟ ⎟    \n\
⎝⎝y⎠ ⎠    \
""")
    assert upretty((x/y)**t*e.j) == ucode_str
    ucode_str = \
u("""\
⎛1⎞    \n\
⎜─⎟ e_j\n\
⎝y⎠    \
""")
    assert upretty((1/y)*e.j) == ucode_str


def test_MatrixSymbol_printing():
    # test cases for issue #14237
    A = MatrixSymbol("A", 3, 3)
    B = MatrixSymbol("B", 3, 3)
    C = MatrixSymbol("C", 3, 3)
    assert pretty(-A*B*C) == "-A*B*C"
    assert pretty(A - B) == "-B + A"
    assert pretty(A*B*C - A*B - B*C) == "-A*B -B*C + A*B*C"

    # issue #14814
    x = MatrixSymbol('x', n, n)
    y = MatrixSymbol('y*', n, n)
    assert pretty(x + y) == "x + y*"
    ascii_str = \
"""\
     2     \n\
-2*y*  -a*x\
"""
    assert pretty(-a*x + -2*y*y) == ascii_str


def test_degree_printing():
    expr1 = 90*degree
    assert pretty(expr1) == u'90°'
    expr2 = x*degree
    assert pretty(expr2) == u'x°'
    expr3 = cos(x*degree + 90*degree)
    assert pretty(expr3) == u'cos(x° + 90°)'


def test_vector_expr_pretty_printing():
    A = CoordSys3D('A')

    assert upretty(Cross(A.i, A.x*A.i+3*A.y*A.j)) == u("(A_i)×((A_x) A_i + (3⋅A_y) A_j)")
    assert upretty(x*Cross(A.i, A.j)) == u('x⋅(A_i)×(A_j)')

    assert upretty(Curl(A.x*A.i + 3*A.y*A.j)) == u("∇×((A_x) A_i + (3⋅A_y) A_j)")

    assert upretty(Divergence(A.x*A.i + 3*A.y*A.j)) == u("∇⋅((A_x) A_i + (3⋅A_y) A_j)")

    assert upretty(Dot(A.i, A.x*A.i+3*A.y*A.j)) == u("(A_i)⋅((A_x) A_i + (3⋅A_y) A_j)")

    assert upretty(Gradient(A.x+3*A.y)) == u("∇(A_x + 3⋅A_y)")
    assert upretty(Laplacian(A.x+3*A.y)) == u("∆(A_x + 3⋅A_y)")
    # TODO: add support for ASCII pretty.


def test_pretty_print_tensor_expr():
    L = TensorIndexType("L")
    i, j, k = tensor_indices("i j k", L)
    i0 = tensor_indices("i_0", L)
    A, B, C, D = tensorhead("A B C D", [L], [[1]])
    H = tensorhead("H", [L, L], [[1], [1]])

    expr = -i
    ascii_str = \
"""\
-i\
"""
    ucode_str = \
u("""\
-i\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = A(i)
    ascii_str = \
"""\
 i\n\
A \n\
  \
"""
    ucode_str = \
u("""\
 i\n\
A \n\
  \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = A(i0)
    ascii_str = \
"""\
 i_0\n\
A   \n\
    \
"""
    ucode_str = \
u("""\
 i₀\n\
A  \n\
   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = A(-i)
    ascii_str = \
"""\
  \n\
A \n\
 i\
"""
    ucode_str = \
u("""\
  \n\
A \n\
 i\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = -3*A(-i)
    ascii_str = \
"""\
     \n\
-3*A \n\
    i\
"""
    ucode_str = \
u("""\
     \n\
-3⋅A \n\
    i\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = H(i, -j)
    ascii_str = \
"""\
 i \n\
H  \n\
  j\
"""
    ucode_str = \
u("""\
 i \n\
H  \n\
  j\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = H(i, -i)
    ascii_str = \
"""\
 L_0   \n\
H      \n\
    L_0\
"""
    ucode_str = \
u("""\
 L₀  \n\
H    \n\
   L₀\
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = H(i, -j)*A(j)*B(k)
    ascii_str = \
"""\
 i     L_0  k\n\
H    *A   *B \n\
  L_0        \
"""
    ucode_str = \
u("""\
 i    L₀  k\n\
H   ⋅A  ⋅B \n\
  L₀       \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (1+x)*A(i)
    ascii_str = \
"""\
         i\n\
(x + 1)*A \n\
          \
"""
    ucode_str = \
u("""\
         i\n\
(x + 1)⋅A \n\
          \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = A(i) + 3*B(i)
    ascii_str = \
"""\
 i      i\n\
A  + 3*B \n\
         \
"""
    ucode_str = \
u("""\
 i      i\n\
A  + 3⋅B \n\
         \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_pretty_print_tensor_partial_deriv():
    from sympy.tensor.toperators import PartialDerivative
    from sympy.tensor.tensor import TensorIndexType, tensor_indices, tensorhead

    L = TensorIndexType("L")
    i, j, k = tensor_indices("i j k", L)
    i0 = tensor_indices("i0", L)

    A, B, C, D = tensorhead("A B C D", [L], [[1]])

    H = tensorhead("H", [L, L], [[1], [1]])

    expr = PartialDerivative(A(i), A(j))
    ascii_str = \
"""\
 d / i\\\n\
---|A |\n\
  j\\  /\n\
dA     \n\
       \
"""
    ucode_str = \
u("""\
 ∂ ⎛ i⎞\n\
───⎜A ⎟\n\
  j⎝  ⎠\n\
∂A     \n\
       \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = A(i)*PartialDerivative(H(k, -i), A(j))
    ascii_str = \
"""\
 L_0  d / k   \\\n\
A   *---|H    |\n\
       j\\  L_0/\n\
     dA        \n\
               \
"""
    ucode_str = \
u("""\
 L₀  ∂ ⎛ k  ⎞\n\
A  ⋅───⎜H   ⎟\n\
      j⎝  L₀⎠\n\
    ∂A       \n\
             \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = A(i)*PartialDerivative(B(k)*C(-i) + 3*H(k, -i), A(j))
    ascii_str = \
"""\
 L_0  d / k           k   \\\n\
A   *---|B *C    + 3*H    |\n\
       j\\    L_0       L_0/\n\
     dA                    \n\
                           \
"""
    ucode_str = \
u("""\
 L₀  ∂ ⎛ k          k  ⎞\n\
A  ⋅───⎜B ⋅C   + 3⋅H   ⎟\n\
      j⎝    L₀       L₀⎠\n\
    ∂A                  \n\
                        \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (A(i) + B(i))*PartialDerivative(C(-j), D(j))
    ascii_str = \
"""\
/ i    i\\   d  /    \\\n\
|A  + B |*-----|C   |\n\
\\       /   L_0\\ L_0/\n\
          dD         \n\
                     \
"""
    ucode_str = \
u("""\
⎛ i    i⎞  ∂  ⎛   ⎞\n\
⎜A  + B ⎟⋅────⎜C  ⎟\n\
⎝       ⎠   L₀⎝ L₀⎠\n\
          ∂D       \n\
                   \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = (A(i) + B(i))*PartialDerivative(C(-i), D(j))
    ascii_str = \
"""\
/ L_0    L_0\\  d /    \\\n\
|A    + B   |*---|C   |\n\
\\           /   j\\ L_0/\n\
              dD       \n\
                       \
"""
    ucode_str = \
u("""\
⎛ L₀    L₀⎞  ∂ ⎛   ⎞\n\
⎜A   + B  ⎟⋅───⎜C  ⎟\n\
⎝         ⎠   j⎝ L₀⎠\n\
            ∂D      \n\
                    \
""")
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = TensorElement(H(i, j), {i:1})
    ascii_str = \
"""\
 i=1,j\n\
H     \n\
      \
"""
    ucode_str = ascii_str
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = TensorElement(H(i, j), {i:1, j:1})
    ascii_str = \
"""\
 i=1,j=1\n\
H       \n\
        \
"""
    ucode_str = ascii_str
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str

    expr = TensorElement(H(i, j), {j:1})
    ascii_str = \
"""\
 i,j=1\n\
H     \n\
      \
"""
    ucode_str = ascii_str

    expr = TensorElement(H(-i, j), {-i:1})
    ascii_str = \
"""\
    j\n\
H    \n\
 i=1 \
"""
    ucode_str = ascii_str
    assert pretty(expr) == ascii_str
    assert upretty(expr) == ucode_str


def test_issue_15560():
    a = MatrixSymbol('a', 1, 1)
    e = pretty(a*(KroneckerProduct(a, a)))
    result = 'a*(a x a)'
    assert e == result


def test_print_lerchphi():
    # Part of issue 6013
    a = Symbol('a')
    pretty(lerchphi(a, 1, 2))
    uresult = u'Φ(a, 1, 2)'
    aresult = 'lerchphi(a, 1, 2)'
    assert pretty(lerchphi(a, 1, 2)) == aresult
    assert upretty(lerchphi(a, 1, 2)) == uresult

def test_issue_15583():

    N = mechanics.ReferenceFrame('N')
    result = '(n_x, n_y, n_z)'
    e = pretty((N.x, N.y, N.z))
    assert e == result


def test_matrixSymbolBold():
    # Issue 15871
    def boldpretty(expr):
        return xpretty(expr, use_unicode=True, wrap_line=False, mat_symbol_style="bold")

    from sympy import trace
    A = MatrixSymbol("A", 2, 2)
    assert boldpretty(trace(A)) == u'tr(𝐀)'

    A = MatrixSymbol("A", 3, 3)
    B = MatrixSymbol("B", 3, 3)
    C = MatrixSymbol("C", 3, 3)

    assert boldpretty(-A) == u'-𝐀'
    assert boldpretty(A - A*B - B) == u'-𝐁 -𝐀⋅𝐁 + 𝐀'
    assert boldpretty(-A*B - A*B*C - B) == u'-𝐁 -𝐀⋅𝐁 -𝐀⋅𝐁⋅𝐂'

    A = MatrixSymbol("Addot", 3, 3)
    assert boldpretty(A) == u'𝐀̈'
    omega = MatrixSymbol("omega", 3, 3)
    assert boldpretty(omega) == u'ω'
    omega = MatrixSymbol("omeganorm", 3, 3)
    assert boldpretty(omega) == u'‖ω‖'

    a = Symbol('alpha')
    b = Symbol('b')
    c = MatrixSymbol("c", 3, 1)
    d = MatrixSymbol("d", 3, 1)

    assert boldpretty(a*B*c+b*d) == u'b⋅𝐝 + α⋅𝐁⋅𝐜'

    d = MatrixSymbol("delta", 3, 1)
    B = MatrixSymbol("Beta", 3, 3)

    assert boldpretty(a*B*c+b*d) == u'b⋅δ + α⋅Β⋅𝐜'

    A = MatrixSymbol("A_2", 3, 3)
    assert boldpretty(A) == u'𝐀₂'


def test_center_accent():
    assert center_accent('a', u'\N{COMBINING TILDE}') == u'ã'
    assert center_accent('aa', u'\N{COMBINING TILDE}') == u'aã'
    assert center_accent('aaa', u'\N{COMBINING TILDE}') == u'aãa'
    assert center_accent('aaaa', u'\N{COMBINING TILDE}') == u'aaãa'
    assert center_accent('aaaaa', u'\N{COMBINING TILDE}') == u'aaãaa'
    assert center_accent('abcdefg', u'\N{COMBINING FOUR DOTS ABOVE}') == u'abcd⃜efg'


def test_imaginary_unit():
    from sympy import pretty # As it is redefined above
    assert pretty(1 + I, use_unicode=False) == '1 + I'
    assert pretty(1 + I, use_unicode=True) == u'1 + ⅈ'
    assert pretty(1 + I, use_unicode=False, imaginary_unit='j') == '1 + I'
    assert pretty(1 + I, use_unicode=True, imaginary_unit='j') == u'1 + ⅉ'

    raises(TypeError, lambda: pretty(I, imaginary_unit=I))
    raises(ValueError, lambda: pretty(I, imaginary_unit="kkk"))
