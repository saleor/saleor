import sys
from sympy.external import import_module
matchpy = import_module("matchpy")

if not matchpy:
    #bin/test will not execute any tests now
    disabled = True

if sys.version_info[:2] < (3, 6):
    disabled = True

from sympy.integrals.rubi.utility_function import (Int, Set, With, Module, Scan, MapAnd, FalseQ, ZeroQ, NegativeQ, NonzeroQ, FreeQ, NFreeQ, List, Log, PositiveQ, PositiveIntegerQ, NegativeIntegerQ, IntegerQ, IntegersQ, ComplexNumberQ, PureComplexNumberQ, RealNumericQ, PositiveOrZeroQ, NegativeOrZeroQ, FractionOrNegativeQ, NegQ, Equal, Unequal, IntPart, FracPart, RationalQ, ProductQ, SumQ, NonsumQ, Subst, First, Rest, SqrtNumberQ, SqrtNumberSumQ, LinearQ, Sqrt, ArcCosh, Coefficient, Denominator, Hypergeometric2F1, Not, Simplify, FractionalPart, IntegerPart, AppellF1, EllipticPi, PolynomialQuotient,
    EllipticE, EllipticF, ArcTan, ArcCot, ArcCoth, ArcTanh, ArcSin, ArcSinh, ArcCos, ArcCsc, ArcSec, ArcCsch, ArcSech, Sinh, Tanh, Cosh, Sech, Csch, Coth, LessEqual, Less, Greater, GreaterEqual, FractionQ, IntLinearcQ, Expand, IndependentQ, PowerQ, IntegerPowerQ, PositiveIntegerPowerQ, FractionalPowerQ, AtomQ, ExpQ, LogQ, Head, MemberQ, TrigQ, SinQ, CosQ, TanQ, CotQ, SecQ, CscQ, Sin, Cos, Tan, Cot, Sec, Csc, HyperbolicQ, SinhQ, CoshQ, TanhQ, CothQ, SechQ, CschQ, InverseTrigQ, SinCosQ, SinhCoshQ, LeafCount, Numerator, NumberQ, NumericQ, Length, ListQ, Im, Re, InverseHyperbolicQ,
    InverseFunctionQ, TrigHyperbolicFreeQ, InverseFunctionFreeQ, RealQ, EqQ, FractionalPowerFreeQ, ComplexFreeQ, PolynomialQ, FactorSquareFree, PowerOfLinearQ, Exponent, QuadraticQ, LinearPairQ, BinomialParts, TrinomialParts, PolyQ, EvenQ, OddQ, PerfectSquareQ, NiceSqrtAuxQ, NiceSqrtQ, Together, PosAux, PosQ, CoefficientList, ReplaceAll, ExpandLinearProduct, GCD, ContentFactor, NumericFactor, NonnumericFactors, MakeAssocList, GensymSubst, KernelSubst, ExpandExpression, Apart, SmartApart, MatchQ, PolynomialQuotientRemainder, FreeFactors, NonfreeFactors, RemoveContentAux, RemoveContent, FreeTerms, NonfreeTerms, ExpandAlgebraicFunction, CollectReciprocals, ExpandCleanup, AlgebraicFunctionQ, Coeff, LeadTerm, RemainingTerms, LeadFactor, RemainingFactors, LeadBase, LeadDegree, Numer, Denom, hypergeom, Expon, MergeMonomials, PolynomialDivide, BinomialQ, TrinomialQ, GeneralizedBinomialQ, GeneralizedTrinomialQ, FactorSquareFreeList, PerfectPowerTest, SquareFreeFactorTest, RationalFunctionQ, RationalFunctionFactors, NonrationalFunctionFactors, Reverse, RationalFunctionExponents, RationalFunctionExpand, ExpandIntegrand, SimplerQ, SimplerSqrtQ, SumSimplerQ, BinomialDegree, TrinomialDegree, CancelCommonFactors, SimplerIntegrandQ, GeneralizedBinomialDegree, GeneralizedBinomialParts, GeneralizedTrinomialDegree, GeneralizedTrinomialParts, MonomialQ, MonomialSumQ, MinimumMonomialExponent, MonomialExponent, LinearMatchQ, PowerOfLinearMatchQ, QuadraticMatchQ, CubicMatchQ, BinomialMatchQ, TrinomialMatchQ, GeneralizedBinomialMatchQ, GeneralizedTrinomialMatchQ, QuotientOfLinearsMatchQ, PolynomialTermQ, PolynomialTerms, NonpolynomialTerms, PseudoBinomialParts, NormalizePseudoBinomial, PseudoBinomialPairQ, PseudoBinomialQ, PolynomialGCD, PolyGCD, AlgebraicFunctionFactors, NonalgebraicFunctionFactors, QuotientOfLinearsP, QuotientOfLinearsParts, QuotientOfLinearsQ, Flatten, Sort, AbsurdNumberQ, AbsurdNumberFactors, NonabsurdNumberFactors, SumSimplerAuxQ, Prepend, Drop, CombineExponents, FactorInteger, FactorAbsurdNumber, SubstForInverseFunction, SubstForFractionalPower, SubstForFractionalPowerOfQuotientOfLinears, FractionalPowerOfQuotientOfLinears, SubstForFractionalPowerQ, SubstForFractionalPowerAuxQ, FractionalPowerOfSquareQ, FractionalPowerSubexpressionQ, Apply, FactorNumericGcd, MergeableFactorQ, MergeFactor, MergeFactors, TrigSimplifyQ, TrigSimplify, TrigSimplifyRecur, Order, FactorOrder, Smallest, OrderedQ, MinimumDegree, PositiveFactors, Sign, NonpositiveFactors, PolynomialInAuxQ, PolynomialInQ, ExponentInAux, ExponentIn, PolynomialInSubstAux, PolynomialInSubst, Distrib, DistributeDegree, FunctionOfPower, DivideDegreesOfFactors, MonomialFactor, FullSimplify, FunctionOfLinearSubst, FunctionOfLinear, NormalizeIntegrand, NormalizeIntegrandAux, NormalizeIntegrandFactor, NormalizeIntegrandFactorBase, NormalizeTogether, NormalizeLeadTermSigns, AbsorbMinusSign, NormalizeSumFactors, SignOfFactor, NormalizePowerOfLinear, SimplifyIntegrand, SimplifyTerm, TogetherSimplify, SmartSimplify, SubstForExpn, ExpandToSum, UnifySum, UnifyTerms, UnifyTerm, CalculusQ, FunctionOfInverseLinear, PureFunctionOfSinhQ, PureFunctionOfTanhQ, PureFunctionOfCoshQ, IntegerQuotientQ, OddQuotientQ, EvenQuotientQ, FindTrigFactor, FunctionOfSinhQ, FunctionOfCoshQ, OddHyperbolicPowerQ, FunctionOfTanhQ, FunctionOfTanhWeight, FunctionOfHyperbolicQ, SmartNumerator, SmartDenominator, SubstForAux, ActivateTrig, ExpandTrig, TrigExpand, SubstForTrig, SubstForHyperbolic, InertTrigFreeQ, LCM, SubstForFractionalPowerOfLinear, FractionalPowerOfLinear, InverseFunctionOfLinear, InertTrigQ, InertReciprocalQ, DeactivateTrig, FixInertTrigFunction, DeactivateTrigAux, PowerOfInertTrigSumQ, PiecewiseLinearQ, KnownTrigIntegrandQ, KnownSineIntegrandQ, KnownTangentIntegrandQ, KnownCotangentIntegrandQ, KnownSecantIntegrandQ, TryPureTanSubst, TryTanhSubst, TryPureTanhSubst, AbsurdNumberGCD, AbsurdNumberGCDList, ExpandTrigExpand, ExpandTrigReduce, ExpandTrigReduceAux, NormalizeTrig, TrigToExp, ExpandTrigToExp, TrigReduce, FunctionOfTrig, AlgebraicTrigFunctionQ, FunctionOfHyperbolic, FunctionOfQ, FunctionOfExpnQ, PureFunctionOfSinQ, PureFunctionOfCosQ, PureFunctionOfTanQ, PureFunctionOfCotQ, FunctionOfCosQ, FunctionOfSinQ, OddTrigPowerQ, FunctionOfTanQ, FunctionOfTanWeight, FunctionOfTrigQ, FunctionOfDensePolynomialsQ, FunctionOfLog, PowerVariableExpn, PowerVariableDegree, PowerVariableSubst, EulerIntegrandQ, FunctionOfSquareRootOfQuadratic, SquareRootOfQuadraticSubst, Divides, EasyDQ, ProductOfLinearPowersQ, Rt, NthRoot, AtomBaseQ, SumBaseQ, NegSumBaseQ, AllNegTermQ, SomeNegTermQ, TrigSquareQ, RtAux, TrigSquare, IntSum, IntTerm, Map2, ConstantFactor, SameQ, ReplacePart, CommonFactors, MostMainFactorPosition, FunctionOfExponentialQ, FunctionOfExponential, FunctionOfExponentialFunction, FunctionOfExponentialFunctionAux, FunctionOfExponentialTest, FunctionOfExponentialTestAux, stdev, rubi_test, If, IntQuadraticQ, IntBinomialQ, RectifyTangent, RectifyCotangent, Inequality, Condition, Simp, SimpHelp, SplitProduct, SplitSum, SubstFor, SubstForAux, FresnelS, FresnelC, Erfc, Erfi, Gamma, FunctionOfTrigOfLinearQ, ElementaryFunctionQ, Complex, UnsameQ, _SimpFixFactor,
    DerivativeDivides, SimpFixFactor, _FixSimplify, FixSimplify, _SimplifyAntiderivativeSum, SimplifyAntiderivativeSum, PureFunctionOfCothQ, _SimplifyAntiderivative, SimplifyAntiderivative, _TrigSimplifyAux, TrigSimplifyAux, Cancel, Part, PolyLog, D, Dist, IntegralFreeQ, Sum_doit, rubi_exp, rubi_log, rubi_log as log,
    PolynomialRemainder, CoprimeQ, Distribute, ProductLog, Floor, PolyGamma, process_trig, replace_pow_exp)
from sympy.core.symbol import symbols, S
from sympy.functions.elementary.trigonometric import atan, acsc, asin, acot, acos, asec, atan2
from sympy.functions.elementary.hyperbolic import acosh, asinh, atanh, acsch, cosh, sinh, tanh, coth, sech, csch, acoth
from sympy.functions import (sin, cos, tan, cot, sec, csc, sqrt, log as sym_log)
from sympy import (I, E, pi, hyper, Add, Wild, simplify, Symbol, exp, UnevaluatedExpr, Pow, li, Ei, expint,
    Si, Ci, Shi, Chi, loggamma, zeta, zoo, gamma, polylog, oo, polygamma)
from sympy import Integral, nsimplify, Min
A, B, a, b, c, d, e, f, g, h, y, z, m, n, p, q, u, v, w, F = symbols('A B a b c d e f g h y z m n p q u v w F', real=True, imaginary=False)
x = Symbol('x')

def test_ZeroQ():
    e = b*(n*p + n + 1)
    d = a
    assert ZeroQ(a*e - b*d*(n*(p + S(1)) + S(1)))
    assert ZeroQ(S(0))
    assert not ZeroQ(S(10))
    assert not ZeroQ(S(-2))
    assert ZeroQ(0, 2-2)
    assert ZeroQ([S(2), (4), S(0), S(8)]) == [False, False, True, False]
    assert ZeroQ([S(2), S(4), S(8)]) == [False, False, False]

def test_NonzeroQ():
    assert NonzeroQ(S(1)) == True

def test_FreeQ():
    l = [a*b, x, a + b]
    assert FreeQ(l, x) == False

    l = [a*b, a + b]
    assert FreeQ(l, x) == True

def test_List():
    assert List(a, b, c) == [a, b, c]

def test_Log():
    assert Log(a) == log(a)

def test_PositiveIntegerQ():
    assert PositiveIntegerQ(S(1))
    assert not PositiveIntegerQ(S(-3))
    assert not PositiveIntegerQ(S(0))

def test_NegativeIntegerQ():
    assert not NegativeIntegerQ(S(1))
    assert NegativeIntegerQ(S(-3))
    assert not NegativeIntegerQ(S(0))

def test_PositiveQ():
    assert PositiveQ(S(1))
    assert not PositiveQ(S(-3))
    assert not PositiveQ(S(0))
    assert not PositiveQ(zoo)
    assert not PositiveQ(I)
    assert PositiveQ(b/(b*(b*c/(-a*d + b*c)) - a*(b*d/(-a*d + b*c))))

def test_IntegerQ():
    assert IntegerQ(S(1))
    assert not IntegerQ(S(-1.9))
    assert not IntegerQ(S(0.0))
    assert IntegerQ(S(-1))

def test_FracPart():
    assert FracPart(S(10)) == 0
    assert FracPart(S(10)+0.5) == 10.5

def test_IntPart():
    assert IntPart(m*n) == 0
    assert IntPart(S(10)) == 10
    assert IntPart(1 + m) == 1

def test_NegQ():
    assert NegQ(-S(3))
    assert not NegQ(S(0))
    assert not NegQ(S(0))

def test_RationalQ():
    assert RationalQ(S(5)/6)
    assert RationalQ(S(5)/6, S(4)/5)
    assert not RationalQ(Sqrt(1.6))
    assert not RationalQ(Sqrt(1.6), S(5)/6)
    assert not RationalQ(log(2))

def test_ArcCosh():
    assert ArcCosh(x) == acosh(x)

def test_LinearQ():
    assert not LinearQ(a, x)
    assert LinearQ(3*x + y**2, x)
    assert not LinearQ(3*x + y**2, y)
    assert not LinearQ(S(3), x)

def test_Sqrt():
    assert Sqrt(x) == sqrt(x)
    assert Sqrt(25) == 5

def test_Util_Coefficient():
    from sympy.integrals.rubi.utility_function import Util_Coefficient
    assert Util_Coefficient(a + b*x + c*x**3, x, a) == Util_Coefficient(a + b*x + c*x**3, x, a)
    assert Util_Coefficient(a + b*x + c*x**3, x, 4).doit() == 0

def test_Coefficient():
    assert Coefficient(7 + 2*x + 4*x**3, x, 1) == 2
    assert Coefficient(a + b*x + c*x**3, x, 0) == a
    assert Coefficient(a + b*x + c*x**3, x, 4) == 0
    assert Coefficient(b*x + c*x**3, x, 3) == c
    assert Coefficient(x, x, -1) == 0

def test_Denominator():
    assert Denominator((-S(1)/S(2) + I/3)) == 6
    assert Denominator((-a/b)**3) == (b)**(3)
    assert Denominator(S(3)/2) == 2
    assert Denominator(x/y) == y
    assert Denominator(S(4)/5) == 5

def test_Hypergeometric2F1():
    assert Hypergeometric2F1(1, 2, 3, x) == hyper((1, 2), (3,), x)

def test_ArcTan():
    assert ArcTan(x) == atan(x)
    assert ArcTan(x, y) == atan2(x, y)

def test_Not():
    a = 10
    assert Not(a == 2)

def test_FractionalPart():
    assert FractionalPart(S(3.0)) == 0.0

def test_IntegerPart():
    assert IntegerPart(3.6) == 3
    assert IntegerPart(-3.6) == -4

def test_AppellF1():
    assert AppellF1(1,0,0.5,1,0.5,0.25).evalf() == 1.154700538379251529018298
    assert AppellF1(a, b, c, d, e, f) == AppellF1(a, b, c, d, e, f)

def test_Simplify():
    assert Simplify(sin(x)**2 + cos(x)**2) == 1
    assert Simplify((x**3 + x**2 - x - 1)/(x**2 + 2*x + 1)) == x - 1

def test_ArcTanh():
    assert ArcTanh(a) == atanh(a)

def test_ArcSin():
    assert ArcSin(a) == asin(a)

def test_ArcSinh():
    assert ArcSinh(a) == asinh(a)

def test_ArcCos():
    assert ArcCos(a) == acos(a)

def test_ArcCsc():
    assert ArcCsc(a) == acsc(a)

def test_ArcCsch():
    assert ArcCsch(a) == acsch(a)

def test_Equal():
    assert Equal(a, a)
    assert not Equal(a, b)

def test_LessEqual():
    assert LessEqual(1, 2, 3)
    assert LessEqual(1, 1)
    assert not LessEqual(3, 2, 1)

def test_With():
    assert With(Set(x, 3), x + y) == 3 + y
    assert With(List(Set(x, 3), Set(y, c)), x + y) == 3 + c

def test_Less():
    assert Less(1, 2, 3)
    assert not Less(1, 1, 3)

def test_Greater():
    assert Greater(3, 2, 1)
    assert not Greater(3, 2, 2)

def test_GreaterEqual():
    assert GreaterEqual(3, 2, 1)
    assert GreaterEqual(3, 2, 2)
    assert not GreaterEqual(2, 3)

def test_Unequal():
    assert Unequal(1, 2)
    assert not Unequal(1, 1)

def test_FractionQ():
    assert not FractionQ(S('3'))
    assert FractionQ(S('3')/S('2'))

def test_Expand():
    assert Expand((1 + x)**10) == x**10 + 10*x**9 + 45*x**8 + 120*x**7 + 210*x**6 + 252*x**5 + 210*x**4 + 120*x**3 + 45*x**2 + 10*x + 1

def test_Scan():
    assert list(Scan(sin, [a, b])) == [sin(a), sin(b)]

def test_MapAnd():
    assert MapAnd(PositiveQ, [S(1), S(2), S(3), S(0)]) == False
    assert MapAnd(PositiveQ, [S(1), S(2), S(3)]) == True

def test_FalseQ():
    assert FalseQ(True) == False
    assert FalseQ(False) == True

def test_ComplexNumberQ():
    assert ComplexNumberQ(1 + I*2, I) == True
    assert ComplexNumberQ(a + b, I) == False

def test_Re():
    assert Re(1 + I) == 1

def test_Im():
    assert Im(1 + 2*I) == 2
    assert Im(a*I) == a

def test_PositiveOrZeroQ():
    assert PositiveOrZeroQ(S(0)) == True
    assert PositiveOrZeroQ(S(1)) == True
    assert PositiveOrZeroQ(-S(1)) == False

def test_RealNumericQ():
    assert RealNumericQ(S(1)) == True
    assert RealNumericQ(-S(1)) == True

def test_NegativeOrZeroQ():
    assert NegativeOrZeroQ(S(0)) == True
    assert NegativeOrZeroQ(-S(1)) == True
    assert NegativeOrZeroQ(S(1)) == False

def test_FractionOrNegativeQ():
    assert FractionOrNegativeQ(S(1)/2) == True
    assert FractionOrNegativeQ(-S(1)) == True

def test_ProductQ():
    assert ProductQ(a*b) == True
    assert ProductQ(a + b) == False

def test_SumQ():
    assert SumQ(a*b) == False
    assert SumQ(a + b) == True

def test_NonsumQ():
    assert NonsumQ(a*b) == True
    assert NonsumQ(a + b) == False

def test_SqrtNumberQ():
    assert SqrtNumberQ(sqrt(2)) == True

def test_IntLinearcQ():
    assert IntLinearcQ(1, 2, 3, 4, 5, 6, x) == True
    assert IntLinearcQ(S(1)/100, S(2)/100, S(3)/100, S(4)/100, S(5)/100, S(6)/100, x) == False

def test_IndependentQ():
    assert IndependentQ(a + b*x, x) == False
    assert IndependentQ(a + b, x) == True

def test_PowerQ():
    assert PowerQ(a**b) == True
    assert PowerQ(a + b) == False

def test_IntegerPowerQ():
    assert IntegerPowerQ(a**2) == True
    assert IntegerPowerQ(a**0.5) == False

def test_PositiveIntegerPowerQ():
    assert PositiveIntegerPowerQ(a**3) == True
    assert PositiveIntegerPowerQ(a**(-2)) == False

def test_FractionalPowerQ():
    assert FractionalPowerQ(a**(S(2)/S(3)))
    assert FractionalPowerQ(a**sqrt(2)) == False

def test_AtomQ():
    assert AtomQ(x)
    assert not AtomQ(x+1)
    assert not AtomQ([a, b])

def test_ExpQ():
    assert ExpQ(E**2)
    assert not ExpQ(2**E)

def test_LogQ():
    assert LogQ(log(x))
    assert not LogQ(sin(x) + log(x))

def test_Head():
    assert Head(sin(x)) == sin
    assert Head(log(x**3 + 3)) in (sym_log, log)

def test_MemberQ():
    assert MemberQ([a, b, c], b)
    assert MemberQ([sin, cos, log, tan], Head(sin(x)))
    assert MemberQ([[sin, cos], [tan, cot]], [sin, cos])
    assert not MemberQ([[sin, cos], [tan, cot]], [sin, tan])

def test_TrigQ():
    assert TrigQ(sin(x))
    assert TrigQ(tan(x**2 + 2))
    assert not TrigQ(sin(x) + tan(x))

def test_SinQ():
    assert SinQ(sin(x))
    assert not SinQ(tan(x))

def test_CosQ():
    assert CosQ(cos(x))
    assert not CosQ(csc(x))

def test_TanQ():
    assert TanQ(tan(x))
    assert not TanQ(cot(x))

def test_CotQ():
    assert not CotQ(tan(x))
    assert CotQ(cot(x))

def test_SecQ():
    assert SecQ(sec(x))
    assert not SecQ(csc(x))

def test_CscQ():
    assert not CscQ(sec(x))
    assert CscQ(csc(x))

def test_HyperbolicQ():
    assert HyperbolicQ(sinh(x))
    assert HyperbolicQ(cosh(x))
    assert HyperbolicQ(tanh(x))
    assert not HyperbolicQ(sinh(x) + cosh(x) + tanh(x))

def test_SinhQ():
    assert SinhQ(sinh(x))
    assert not SinhQ(cosh(x))

def test_CoshQ():
    assert not CoshQ(sinh(x))
    assert CoshQ(cosh(x))

def test_TanhQ():
    assert TanhQ(tanh(x))
    assert not TanhQ(coth(x))

def test_CothQ():
    assert not CothQ(tanh(x))
    assert CothQ(coth(x))

def test_SechQ():
    assert SechQ(sech(x))
    assert not SechQ(csch(x))

def test_CschQ():
    assert not CschQ(sech(x))
    assert CschQ(csch(x))

def test_InverseTrigQ():
    assert InverseTrigQ(acot(x))
    assert InverseTrigQ(asec(x))
    assert not InverseTrigQ(acsc(x) + asec(x))

def test_SinCosQ():
    assert SinCosQ(sin(x))
    assert SinCosQ(cos(x))
    assert SinCosQ(sec(x))
    assert not SinCosQ(acsc(x))

def test_SinhCoshQ():
    assert not SinhCoshQ(sin(x))
    assert SinhCoshQ(cosh(x))
    assert SinhCoshQ(sech(x))
    assert SinhCoshQ(csch(x))

def test_LeafCount():
    assert LeafCount(1 + a + x**2) == 6

def test_Numerator():
    assert Numerator((-S(1)/S(2) + I/3)) == -3 + 2*I
    assert Numerator((-a/b)**3) == (-a)**(3)
    assert Numerator(S(3)/2) == 3
    assert Numerator(x/y) == x

def test_Length():
    assert Length(a + b) == 2
    assert Length(sin(a)*cos(a)) == 2

def test_ListQ():
    assert ListQ([1, 2])
    assert not ListQ(a)

def test_InverseHyperbolicQ():
    assert InverseHyperbolicQ(acosh(a))

def test_InverseFunctionQ():
    assert InverseFunctionQ(log(a))
    assert InverseFunctionQ(acos(a))
    assert not InverseFunctionQ(a)
    assert InverseFunctionQ(acosh(a))
    assert InverseFunctionQ(polylog(a, b))

def test_EqQ():
    assert EqQ(a, a)
    assert not EqQ(a, b)

def test_FactorSquareFree():
    assert FactorSquareFree(x**5 - x**3 - x**2 + 1) == (x**3 + 2*x**2 + 2*x + 1)*(x - 1)**2

def test_FactorSquareFreeList():
    assert FactorSquareFreeList(x**5-x**3-x**2 + 1) == [[1, 1], [x**3 + 2*x**2 + 2*x + 1, 1], [x - 1, 2]]
    assert FactorSquareFreeList(x**4 - 2*x**2 + 1) == [[1, 1], [x**2 - 1, 2]]

def test_PerfectPowerTest():
    assert not PerfectPowerTest(sqrt(x), x)
    assert not PerfectPowerTest(x**5-x**3-x**2 + 1, x)
    assert PerfectPowerTest(x**4 - 2*x**2 + 1, x) == (x**2 - 1)**2

def test_SquareFreeFactorTest():
    assert not SquareFreeFactorTest(sqrt(x), x)
    assert SquareFreeFactorTest(x**5 - x**3 - x**2 + 1, x) == (x**3 + 2*x**2 + 2*x + 1)*(x - 1)**2

def test_Rest():
    assert Rest([2, 3, 5, 7]) == [3, 5, 7]
    assert Rest(a + b + c) == b + c
    assert Rest(a*b*c) == b*c
    assert Rest(1/b) == -1

def test_First():
    assert First([2, 3, 5, 7]) == 2
    assert First(y**S(2)) == y
    assert First(a + b + c) == a
    assert First(a*b*c) == a

def test_ComplexFreeQ():
    assert ComplexFreeQ(a)
    assert not ComplexFreeQ(a + 2*I)

def test_FractionalPowerFreeQ():
    assert not FractionalPowerFreeQ(x**(S(2)/3))
    assert FractionalPowerFreeQ(x)

def test_Exponent():
    assert Exponent(x**2 + x + 1 + 5, x, Min) == 0
    assert Exponent(x**2 + x + 1 + 5, x, List) == [0, 1, 2]
    assert Exponent(x**2 + x + 1, x, List) == [0, 1, 2]
    assert Exponent(x**2 + 2*x + 1, x, List) == [0, 1, 2]
    assert Exponent(x**3 + x + 1, x) == 3
    assert Exponent(x**2 + 2*x + 1, x) == 2
    assert Exponent(x**3, x, List) == [3]
    assert Exponent(S(1), x) == 0
    assert Exponent(x**(-3), x) == 0

def test_Expon():
    assert Expon(x**2+2*x+1, x) == 2
    assert Expon(x**3, x, List) == [3]

def test_QuadraticQ():
    assert not QuadraticQ([x**2+x+1, 5*x**2], x)
    assert QuadraticQ([x**2+x+1, 5*x**2+3*x+6], x)
    assert not QuadraticQ(x**2+1+x**3, x)
    assert QuadraticQ(x**2+1+x, x)
    assert not QuadraticQ(x**2, x)

def test_BinomialQ():
    assert BinomialQ(x**9, x)
    assert not BinomialQ((1 + x)**3, x)

def test_BinomialParts():
    assert BinomialParts(2 + x*(9*x), x) == [2, 9, 2]
    assert BinomialParts(x**9, x) == [0, 1, 9]
    assert BinomialParts(2*x**3, x) == [0, 2, 3]
    assert BinomialParts(2 + x, x) == [2, 1, 1]

def test_BinomialDegree():
    assert BinomialDegree(b + 2*c*x**n, x) == n
    assert BinomialDegree(2 + x*(9*x), x) == 2
    assert BinomialDegree(x**9, x) == 9

def test_PolynomialQ():
    assert not PolynomialQ(x*(-1 + x**2), (1 + x)**(S(1)/2))
    assert not PolynomialQ((16*x + 1)/((x + 5)**2*(x**2 + x + 1)), 2*x)
    C = Symbol('C')
    assert not PolynomialQ(A + b*x + c*x**2, x**2)
    assert PolynomialQ(A + B*x + C*x**2)
    assert PolynomialQ(A + B*x**4 + C*x**2, x**2)
    assert PolynomialQ(x**3, x)
    assert not PolynomialQ(sqrt(x), x)

def test_PolyQ():
    assert PolyQ(-2*a*d**3*e**2 + x**6*(a*e**5 - b*d*e**4 + c*d**2*e**3)\
        + x**4*(-2*a*d*e**4 + 2*b*d**2*e**3 - 2*c*d**3*e**2) + x**2*(2*a*d**2*e**3 - 2*b*d**3*e**2), x)
    assert not PolyQ(1/sqrt(a + b*x**2 - c*x**4), x**2)
    assert PolyQ(x, x, 1)
    assert PolyQ(x**2, x, 2)
    assert not PolyQ(x**3, x, 2)

def test_EvenQ():
    assert EvenQ(S(2))
    assert not EvenQ(S(1))

def test_OddQ():
    assert OddQ(S(1))
    assert not OddQ(S(2))

def test_PerfectSquareQ():
    assert PerfectSquareQ(S(4))
    assert PerfectSquareQ(a**S(2)*b**S(4))
    assert not PerfectSquareQ(S(1)/3)

def test_NiceSqrtQ():
    assert NiceSqrtQ(S(1)/3)
    assert not NiceSqrtQ(-S(1))
    assert NiceSqrtQ(pi**2)
    assert NiceSqrtQ(pi**2*sin(4)**4)
    assert not NiceSqrtQ(pi**2*sin(4)**3)

def test_Together():
    assert Together(1/a + b/2) == (a*b + 2)/(2*a)

def test_PosQ():
    #assert not PosQ((b*e - c*d)/(c*e))
    assert not PosQ(S(0))
    assert PosQ(S(1))
    assert PosQ(pi)
    assert PosQ(pi**3)
    assert PosQ((-pi)**4)
    assert PosQ(sin(1)**2*pi**4)

def test_NumericQ():
    assert NumericQ(sin(cos(2)))

def test_NumberQ():
    assert NumberQ(pi)

def test_CoefficientList():
    assert CoefficientList(1 + a*x, x) == [1, a]
    assert CoefficientList(1 + a*x**3, x) == [1, 0, 0, a]
    assert CoefficientList(sqrt(x), x) == []

def test_ReplaceAll():
    assert ReplaceAll(x, {x: a}) == a
    assert ReplaceAll(a*x, {x: a + b}) == a*(a + b)
    assert ReplaceAll(a*x, {a: b, x: a + b}) == b*(a + b)

def test_ExpandLinearProduct():
    assert ExpandLinearProduct(log(x), x**2, a, b, x) == a**2*log(x)/b**2 - 2*a*(a + b*x)*log(x)/b**2 + (a + b*x)**2*log(x)/b**2
    assert ExpandLinearProduct((a + b*x)**n, x**3, a, b, x) == -a**3*(a + b*x)**n/b**3 + 3*a**2*(a + b*x)**(n + 1)/b**3 - 3*a*(a + b*x)**(n + 2)/b**3 + (a + b*x)**(n + 3)/b**3

def test_PolynomialDivide():
    assert PolynomialDivide((a*c - b*c*x)**2, (a + b*x)**2, x) == -4*a*b*c**2*x/(a + b*x)**2 + c**2
    assert PolynomialDivide(x + x**2, x, x) == x + 1
    assert PolynomialDivide((1 + x)**3, (1 + x)**2, x) == x + 1
    assert PolynomialDivide((a + b*x)**3, x**3, x) == a*(a**2 + 3*a*b*x + 3*b**2*x**2)/x**3 + b**3
    assert PolynomialDivide(x**3*(a + b*x), S(1), x) == b*x**4 + a*x**3
    assert PolynomialDivide(x**6, (a + b*x)**2, x) == -a**5*(5*a + 6*b*x)/(b**6*(a + b*x)**2) + 5*a**4/b**6 - 4*a**3*x/b**5 + 3*a**2*x**2/b**4 - 2*a*x**3/b**3 + x**4/b**2

def test_MatchQ():
    a_ = Wild('a', exclude=[x])
    b_ = Wild('b', exclude=[x])
    c_ = Wild('c', exclude=[x])
    assert MatchQ(a*b + c, a_*b_ + c_, a_, b_, c_) == (a, b, c)

def test_PolynomialQuotientRemainder():
    assert PolynomialQuotientRemainder(x**2, x+a, x) == [-a + x, a**2]

def test_FreeFactors():
    assert FreeFactors(a, x) == a
    assert FreeFactors(x + a, x) == 1
    assert FreeFactors(a*b*x, x) == a*b

def test_NonfreeFactors():
    assert NonfreeFactors(a, x) == 1
    assert NonfreeFactors(x + a, x) == x + a
    assert NonfreeFactors(a*b*x, x) == x

def test_FreeTerms():
    assert FreeTerms(a, x) == a
    assert FreeTerms(x*a, x) == 0
    assert FreeTerms(a*x + b, x) == b

def test_NonfreeTerms():
    assert NonfreeTerms(a, x) == 0
    assert NonfreeTerms(a*x, x) == a*x
    assert NonfreeTerms(a*x + b, x) == a*x

def test_RemoveContent():
    assert RemoveContent(a + b*x, x) == a + b*x

def test_ExpandAlgebraicFunction():
    assert ExpandAlgebraicFunction((a + b)*x, x) == a*x + b*x
    assert ExpandAlgebraicFunction((a + b)**2*x, x)== a**2*x + 2*a*b*x + b**2*x
    assert ExpandAlgebraicFunction((a + b)**2*x**2, x) == a**2*x**2 + 2*a*b*x**2 + b**2*x**2

def test_CollectReciprocals():
    assert CollectReciprocals(-1/(1 + 1*x) - 1/(1 - 1*x), x) == -2/(-x**2 + 1)
    assert CollectReciprocals(1/(1 + 1*x) - 1/(1 - 1*x), x) == -2*x/(-x**2 + 1)

def test_ExpandCleanup():
    assert ExpandCleanup(a + b, x) == a*(1 + b/a)
    assert ExpandCleanup(b**2/(a**2*(a + b*x)**2) + 1/(a**2*x**2) + 2*b**2/(a**3*(a + b*x)) - 2*b/(a**3*x), x) == b**2/(a**2*(a + b*x)**2) + 1/(a**2*x**2) + 2*b**2/(a**3*(a + b*x)) - 2*b/(a**3*x)

def test_AlgebraicFunctionQ():
    assert not AlgebraicFunctionQ(1/(a + c*x**(2*n)), x)
    assert AlgebraicFunctionQ(a, x) == True
    assert AlgebraicFunctionQ(a*b, x) == True
    assert AlgebraicFunctionQ(x**2, x) == True
    assert AlgebraicFunctionQ(x**2*a, x) == True
    assert AlgebraicFunctionQ(x**2 + a, x) == True
    assert AlgebraicFunctionQ(sin(x), x) == False
    assert AlgebraicFunctionQ([], x) == True
    assert AlgebraicFunctionQ([a, a*b], x) == True
    assert AlgebraicFunctionQ([sin(x)], x) == False

def test_MonomialQ():
    assert not MonomialQ(2*x**7 + 6, x)
    assert MonomialQ(2*x**7, x)
    assert not MonomialQ(2*x**7 + 5*x**3, x)
    assert not MonomialQ([2*x**7 + 6, 2*x**7], x)
    assert MonomialQ([2*x**7, 5*x**3], x)

def test_MonomialSumQ():
    assert MonomialSumQ(2*x**7 + 6, x) == True
    assert MonomialSumQ(x**2 + x**3 + 5*x, x) == True

def test_MinimumMonomialExponent():
    assert MinimumMonomialExponent(x**2 + 5*x**2 + 3*x**5, x) == 2
    assert MinimumMonomialExponent(x**2 + 5*x**2 + 1, x) == 0

def test_MonomialExponent():
    assert MonomialExponent(3*x**7, x) == 7
    assert not MonomialExponent(3+x**3, x)

def test_LinearMatchQ():
    assert LinearMatchQ(2 + 3*x, x)
    assert LinearMatchQ(3*x, x)
    assert not LinearMatchQ(3*x**2, x)

def test_SimplerQ():
    a1, b1 = symbols('a1 b1')
    assert SimplerQ(a1, b1)

    assert SimplerQ(2*a, a + 2)
    assert SimplerQ(2, x)
    assert not SimplerQ(x**2, x)
    assert SimplerQ(2*x, x + 2 + 6*x**3)

def test_GeneralizedTrinomialParts():
    assert not GeneralizedTrinomialParts((7 + 2*x**6 + 3*x**12), x)
    assert GeneralizedTrinomialParts(x**2 + x**3 + x**4, x) == [1, 1, 1, 3, 2]
    assert not GeneralizedTrinomialParts(2*x + 3*x + 4*x, x)

def test_TrinomialQ():
    assert TrinomialQ((7 + 2*x**6 + 3*x**12), x)
    assert not TrinomialQ(x**2, x)

def test_GeneralizedTrinomialDegree():
    assert not GeneralizedTrinomialDegree((7 + 2*x**6 + 3*x**12), x)
    assert GeneralizedTrinomialDegree(x**2 + x**3 + x**4, x) == 1

def test_GeneralizedBinomialParts():
    assert GeneralizedBinomialParts(3*x*(3 + x**6), x) == [9, 3, 7, 1]
    assert GeneralizedBinomialParts((3*x + x**7), x) == [3, 1, 7, 1]

def test_GeneralizedBinomialDegree():
    assert GeneralizedBinomialDegree(3*x*(3 + x**6), x) == 6
    assert GeneralizedBinomialDegree((3*x + x**7), x) == 6

def test_PowerOfLinearQ():
    assert PowerOfLinearQ((6*x), x)
    assert not PowerOfLinearQ((3 + 6*x**3), x)
    assert PowerOfLinearQ((3 + 6*x)**3, x)

def test_LinearPairQ():
    assert not LinearPairQ(6*x**2 + 4, 3*x**2 + 2, x)
    assert LinearPairQ(6*x + 4, 3*x + 2, x)
    assert not LinearPairQ(6*x, 3*x + 2, x)
    assert LinearPairQ(6*x, 3*x, x)

def test_LeadTerm():
    assert LeadTerm(a*b*c) == a*b*c
    assert LeadTerm(a + b + c) == a

def test_RemainingTerms():
    assert RemainingTerms(a*b*c) == a*b*c
    assert RemainingTerms(a + b + c) == b + c

def test_LeadFactor():
    assert LeadFactor(a*b*c) == a
    assert LeadFactor(a + b + c) == a + b + c
    assert LeadFactor(b*I) == I
    assert LeadFactor(c*a**b) == a**b
    assert LeadFactor(S(2)) == S(2)

def test_RemainingFactors():
    assert RemainingFactors(a*b*c) == b*c
    assert RemainingFactors(a + b + c) == 1
    assert RemainingFactors(a*I) == a

def test_LeadBase():
    assert LeadBase(a**b) == a
    assert LeadBase(a**b*c) == a

def test_LeadDegree():
    assert LeadDegree(a**b) == b
    assert LeadDegree(a**b*c) == b

def test_Numer():
    assert Numer(a/b) == a
    assert Numer(a**(-2)) == 1
    assert Numer(a**(-2)*a/b) == 1

def test_Denom():
    assert Denom(a/b) == b
    assert Denom(a**(-2)) == a**2
    assert Denom(a**(-2)*a/b) == a*b

def test_Coeff():
    assert Coeff(7 + 2*x + 4*x**3, x, 1) == 2
    assert Coeff(a + b*x + c*x**3, x, 0) == a
    assert Coeff(a + b*x + c*x**3, x, 4) == 0
    assert Coeff(b*x + c*x**3, x, 3) == c

def test_MergeMonomials():
    assert MergeMonomials(x**2*(1 + 1*x)**3*(1 + 1*x)**n, x) == x**2*(x + 1)**(n + 3)
    assert MergeMonomials(x**2*(1 + 1*x)**2*(1*(1 + 1*x)**1)**2, x) == x**2*(x + 1)**4
    assert MergeMonomials(b**2/a**3, x) == b**2/a**3

def test_RationalFunctionQ():
    assert RationalFunctionQ(a, x)
    assert RationalFunctionQ(x**2, x)
    assert RationalFunctionQ(x**3 + x**4, x)
    assert RationalFunctionQ(x**3*S(2), x)
    assert not RationalFunctionQ(x**3 + x**(0.5), x)
    assert not RationalFunctionQ(x**(S(2)/3)*(a + b*x)**2, x)

def test_Apart():
    assert Apart(1/(x**2*(a + b*x)**2), x) == b**2/(a**2*(a + b*x)**2) + 1/(a**2*x**2) + 2*b**2/(a**3*(a + b*x)) - 2*b/(a**3*x)
    assert Apart(x**(S(2)/3)*(a + b*x)**2, x) == x**(S(2)/3)*(a + b*x)**2

def test_RationalFunctionFactors():
    assert RationalFunctionFactors(a, x) == a
    assert RationalFunctionFactors(sqrt(x), x) == 1
    assert RationalFunctionFactors(x*x**3, x) == x*x**3
    assert RationalFunctionFactors(x*sqrt(x), x) == 1

def test_NonrationalFunctionFactors():
    assert NonrationalFunctionFactors(x, x) == 1
    assert NonrationalFunctionFactors(sqrt(x), x) == sqrt(x)
    assert NonrationalFunctionFactors(sqrt(x)*log(x), x) == sqrt(x)*log(x)

def test_Reverse():
    assert Reverse([1, 2, 3]) == [3, 2, 1]
    assert Reverse(a**b) == b**a

def test_RationalFunctionExponents():
    assert RationalFunctionExponents(sqrt(x), x) == [0, 0]
    assert RationalFunctionExponents(a, x) == [0, 0]
    assert RationalFunctionExponents(x, x) == [1, 0]
    assert RationalFunctionExponents(x**(-1), x)== [0, 1]
    assert RationalFunctionExponents(x**(-1)*a, x) == [0, 1]
    assert RationalFunctionExponents(x**(-1) + a, x) == [1, 1]

def test_PolynomialGCD():
    assert PolynomialGCD(x**2 - 1, x**2 - 3*x + 2) == x - 1

def test_PolyGCD():
    assert PolyGCD(x**2 - 1, x**2 - 3*x + 2, x) == x - 1

def test_AlgebraicFunctionFactors():
    assert AlgebraicFunctionFactors(sin(x)*x, x) == x
    assert AlgebraicFunctionFactors(sin(x), x) == 1
    assert AlgebraicFunctionFactors(x, x) == x

def test_NonalgebraicFunctionFactors():
    assert NonalgebraicFunctionFactors(sin(x)*x, x) == sin(x)
    assert NonalgebraicFunctionFactors(sin(x), x) == sin(x)
    assert NonalgebraicFunctionFactors(x, x) == 1

def test_QuotientOfLinearsP():
    assert QuotientOfLinearsP((a + b*x)/(x), x)
    assert QuotientOfLinearsP(x*a, x)
    assert not QuotientOfLinearsP(x**2*a, x)
    assert not QuotientOfLinearsP(x**2 + a, x)
    assert QuotientOfLinearsP(x + a, x)
    assert QuotientOfLinearsP(x, x)
    assert QuotientOfLinearsP(1 + x, x)

def test_QuotientOfLinearsParts():
    assert QuotientOfLinearsParts((b*x)/(c), x) == [0, b/c, 1, 0]
    assert QuotientOfLinearsParts((b*x)/(c + x), x) == [0, b, c, 1]
    assert QuotientOfLinearsParts((b*x)/(c + d*x), x) == [0, b, c, d]
    assert QuotientOfLinearsParts((a + b*x)/(c + d*x), x) == [a, b, c, d]
    assert QuotientOfLinearsParts(x**2 + a, x) == [a + x**2, 0, 1, 0]
    assert QuotientOfLinearsParts(a/x, x) == [a, 0, 0, 1]
    assert QuotientOfLinearsParts(1/x, x) == [1, 0, 0, 1]
    assert QuotientOfLinearsParts(a*x + 1, x) == [1, a, 1, 0]
    assert QuotientOfLinearsParts(x, x) == [0, 1, 1, 0]
    assert QuotientOfLinearsParts(a, x) == [a, 0, 1, 0]

def test_QuotientOfLinearsQ():
    assert not QuotientOfLinearsQ((a + x), x)
    assert QuotientOfLinearsQ((a + x)/(x), x)
    assert QuotientOfLinearsQ((a + b*x)/(x), x)

def test_Flatten():
    assert Flatten([a, b, [c, [d, e]]]) == [a, b, c, d, e]

def test_Sort():
    assert Sort([b, a, c]) == [a, b, c]
    assert Sort([b, a, c], True) == [c, b, a]

def test_AbsurdNumberQ():
    assert AbsurdNumberQ(S(1))
    assert not AbsurdNumberQ(a*x)
    assert not AbsurdNumberQ(a**(S(1)/2))
    assert AbsurdNumberQ((S(1)/3)**(S(1)/3))

def test_AbsurdNumberFactors():
    assert AbsurdNumberFactors(S(1)) == S(1)
    assert AbsurdNumberFactors((S(1)/3)**(S(1)/3)) == S(3)**(S(2)/3)/S(3)
    assert AbsurdNumberFactors(a) == S(1)

def test_NonabsurdNumberFactors():
    assert NonabsurdNumberFactors(a) == a
    assert NonabsurdNumberFactors(S(1)) == S(1)
    assert NonabsurdNumberFactors(a*S(2)) == a

def test_NumericFactor():
    assert NumericFactor(S(1)) == S(1)
    assert NumericFactor(1*I) == S(1)
    assert NumericFactor(S(1) + I) == S(1)
    assert NumericFactor(a**(S(1)/3)) == S(1)
    assert NumericFactor(a*S(3)) == S(3)
    assert NumericFactor(a + b) == S(1)

def test_NonnumericFactors():
    assert NonnumericFactors(S(3)) == S(1)
    assert NonnumericFactors(I) == I
    assert NonnumericFactors(S(3) + I) == S(3) + I
    assert NonnumericFactors((S(1)/3)**(S(1)/3)) == S(1)
    assert NonnumericFactors(log(a)) == log(a)

def test_Prepend():
    assert Prepend([1, 2, 3], [4, 5]) == [4, 5, 1, 2, 3]

def test_SumSimplerQ():
    assert not SumSimplerQ(S(4 + x),S(3 + x**3))
    assert SumSimplerQ(S(4 + x), S(3 - x))

def test_SumSimplerAuxQ():
    assert SumSimplerAuxQ(S(4 + x), S(3 - x))
    assert not SumSimplerAuxQ(S(4), S(3))

def test_SimplerSqrtQ():
    assert SimplerSqrtQ(S(2), S(16*x**3))
    assert not SimplerSqrtQ(S(x*2), S(16))
    assert not SimplerSqrtQ(S(-4), S(16))
    assert SimplerSqrtQ(S(4), S(16))
    assert not SimplerSqrtQ(S(4), S(0))

def test_TrinomialParts():
    assert TrinomialParts((1 + 5*x**3)**2, x) == [1, 10, 25, 3]
    assert TrinomialParts(1 + 5*x**3 + 2*x**6, x) == [1, 5, 2, 3]
    assert TrinomialParts(((1 + 5*x**3)**2) + 6, x) == [7, 10, 25, 3]
    assert not TrinomialParts(1 + 5*x**3 + 2*x**5, x)

def test_TrinomialDegree():
    assert TrinomialDegree((7 + 2*x**6)**2, x) == 6
    assert TrinomialDegree(1 + 5*x**3 + 2*x**6, x) == 3
    assert not TrinomialDegree(1 + 5*x**3 + 2*x**5, x)

def test_CubicMatchQ():
    assert not CubicMatchQ(S(3 + x**6), x)
    assert CubicMatchQ(S(x**3), x)
    assert not CubicMatchQ(S(3), x)
    assert CubicMatchQ(S(3 + x**3), x)
    assert CubicMatchQ(S(3 + x**3 + 2*x), x)

def test_BinomialMatchQ():
    assert BinomialMatchQ(x, x)
    assert BinomialMatchQ(2 + 3*x**5, x)
    assert BinomialMatchQ(3*x**5, x)
    assert BinomialMatchQ(3*x, x)
    assert not BinomialMatchQ(x + x**2 + x**3, x)

def test_TrinomialMatchQ():
    assert not TrinomialMatchQ((5 + 2*x**6)**2, x)
    assert not TrinomialMatchQ((7 + 8*x**6), x)
    assert TrinomialMatchQ((7 + 2*x**6 + 3*x**3), x)
    assert TrinomialMatchQ(b*x**2 + c*x**4, x)

def test_GeneralizedBinomialMatchQ():
    assert not GeneralizedBinomialMatchQ((1 + x**4), x)
    assert GeneralizedBinomialMatchQ((3*x + x**7), x)

def test_QuadraticMatchQ():
    assert not QuadraticMatchQ((a + b*x)*(c + d*x), x)
    assert QuadraticMatchQ(x**2 + x, x)
    assert QuadraticMatchQ(x**2+1+x, x)
    assert QuadraticMatchQ(x**2, x)

def test_PowerOfLinearMatchQ():
    assert PowerOfLinearMatchQ(x, x)
    assert not PowerOfLinearMatchQ(S(6)**3, x)
    assert not PowerOfLinearMatchQ(S(6 + 3*x**2)**3, x)
    assert PowerOfLinearMatchQ(S(6 + 3*x)**3, x)

def test_GeneralizedTrinomialMatchQ():
    assert not GeneralizedTrinomialMatchQ(7 + 2*x**6 + 3*x**12, x)
    assert not GeneralizedTrinomialMatchQ(7 + 2*x**6 + 3*x**3, x)
    assert not GeneralizedTrinomialMatchQ(7 + 2*x**6 + 3*x**5, x)
    assert GeneralizedTrinomialMatchQ(x**2 + x**3 + x**4, x)

def test_QuotientOfLinearsMatchQ():
    assert QuotientOfLinearsMatchQ((1 + x)*(3 + 4*x**2)/(2 + 4*x), x)
    assert not QuotientOfLinearsMatchQ(x*(3 + 4*x**2)/(2 + 4*x**3), x)
    assert QuotientOfLinearsMatchQ(x*(3 + 4*x)/(2 + 4*x), x)
    assert QuotientOfLinearsMatchQ(2*(3 + 4*x)/(2 + 4*x), x)

def test_PolynomialTermQ():
    assert not PolynomialTermQ(S(3), x)
    assert PolynomialTermQ(3*x**6, x)
    assert not PolynomialTermQ(3*x**6+5*x, x)

def test_PolynomialTerms():
    assert PolynomialTerms(x + 6*x**3 + log(x), x) == 6*x**3 + x
    assert PolynomialTerms(x + 6*x**3 + 6*x, x) == 6*x**3 + 7*x
    assert PolynomialTerms(x + 6*x**3 + 6, x) == 6*x**3 + x

def test_NonpolynomialTerms():
    assert NonpolynomialTerms(x + 6*x**3 + log(x), x) == log(x)
    assert NonpolynomialTerms(x + 6*x**3 + 6*x, x) == 0
    assert NonpolynomialTerms(x + 6*x**3 + 6, x) == 6

def test_PseudoBinomialQ():
    assert PseudoBinomialQ(3 + 5*(x)**6, x)
    assert PseudoBinomialQ(3 + 5*(2 + 5*x)**6, x)

def test_PseudoBinomialParts():
    assert PseudoBinomialParts(3 + 7*(1 + x)**6, x) == [3, 1, 7**(S(1)/S(6)), 7**(S(1)/S(6)), 6]
    assert PseudoBinomialParts(3 + 7*(1 + x)**3, x) == [3, 1, 7**(S(1)/S(3)), 7**(S(1)/S(3)), 3]
    assert not PseudoBinomialParts(3 + 7*(1 + x)**2, x)
    assert PseudoBinomialParts(3 + 7*(x)**5, x) == [3, 1, 0, 7**(S(1)/S(5)), 5]

def test_PseudoBinomialPairQ():
    assert not PseudoBinomialPairQ(3 + 5*(x)**6,3 + (x)**6, x)
    assert not PseudoBinomialPairQ(3 + 5*(1 + x)**6,3 + (1 + x)**6, x)

def test_NormalizePseudoBinomial():
    assert NormalizePseudoBinomial(3 + 5*(1 + x)**6, x) == 3+(5**(S(1)/S(6))+5**(S(1)/S(6))*x)**S(6)
    assert NormalizePseudoBinomial(3 + 5*(x)**6, x) == 3+5*x**6

def test_CancelCommonFactors():
    assert CancelCommonFactors(S(x*y*S(6))**S(6), S(x*y*S(6))) == [46656*x**6*y**6, 6*x*y]
    assert CancelCommonFactors(S(y*6)**S(6), S(x*y*S(6))) == [46656*y**6, 6*x*y]
    assert CancelCommonFactors(S(6), S(3)) == [6, 3]

def test_SimplerIntegrandQ():
    assert SimplerIntegrandQ(S(5), 4*x, x)
    assert not SimplerIntegrandQ(S(x + 5*x**3), S(x**2 + 3*x), x)
    assert SimplerIntegrandQ(S(x + 8), S(x**2 + 3*x), x)

def test_Drop():
    assert Drop([1, 2, 3, 4, 5, 6], [2, 4]) == [1, 5, 6]
    assert Drop([1, 2, 3, 4, 5, 6], -3) == [1, 2, 3]
    assert Drop([1, 2, 3, 4, 5, 6], 2) == [3, 4, 5, 6]
    assert Drop(a*b*c, 1) == b*c

def test_SubstForInverseFunction():
    assert SubstForInverseFunction(x, a, b, x) == b
    assert SubstForInverseFunction(a, a, b, x) == a
    assert SubstForInverseFunction(x**a, x**a, b, x) == x
    assert SubstForInverseFunction(a*x**a, a, b, x) == a*b**a

def test_SubstForFractionalPower():
    assert SubstForFractionalPower(a, b, n, c, x) == a
    assert SubstForFractionalPower(x, b, n, c, x) == c
    assert SubstForFractionalPower(a**(S(1)/2), a, n, b, x) == x**(n/2)

def test_CombineExponents():
    assert True

def test_FractionalPowerOfSquareQ():
    assert not FractionalPowerOfSquareQ(x)
    assert not FractionalPowerOfSquareQ((a + b)**(S(2)/S(3)))
    assert not FractionalPowerOfSquareQ((a + b)**(S(2)/S(3))*c)
    assert FractionalPowerOfSquareQ(((a + b*x)**(S(2)))**(S(1)/3)) == (a + b*x)**S(2)

def test_FractionalPowerSubexpressionQ():
    assert not FractionalPowerSubexpressionQ(x, a, x)
    assert FractionalPowerSubexpressionQ(x**(S(2)/S(3)), a, x)
    assert not FractionalPowerSubexpressionQ(b*a, a, x)

def test_FactorNumericGcd():
    assert FactorNumericGcd(5*a**2*e**4 + 2*a*b*d*e**3 + 2*a*c*d**2*e**2 + b**2*d**2*e**2 - 6*b*c*d**3*e + 21*c**2*d**4) ==\
        5*a**2*e**4 + 2*a*b*d*e**3 + 2*a*c*d**2*e**2 + b**2*d**2*e**2 - 6*b*c*d**3*e + 21*c**2*d**4
    assert FactorNumericGcd(x**(S(2))) == x**S(2)
    assert FactorNumericGcd(log(x)) == log(x)
    assert FactorNumericGcd(log(x)*x) == x*log(x)
    assert FactorNumericGcd(log(x) + x**S(2)) == log(x) + x**S(2)

def test_Apply():
    assert Apply(List, [a, b, c]) == [a, b, c]

def test_TrigSimplify():
    assert TrigSimplify(a*sin(x)**2 + a*cos(x)**2 + v) == a + v
    assert TrigSimplify(a*sec(x)**2 - a*tan(x)**2 + v) == a + v
    assert TrigSimplify(a*csc(x)**2 - a*cot(x)**2 + v) == a + v
    assert TrigSimplify(S(1) - sin(x)**2) == cos(x)**2
    assert TrigSimplify(1 + tan(x)**2) == sec(x)**2
    assert TrigSimplify(1 + cot(x)**2) == csc(x)**2
    assert TrigSimplify(-S(1) + sec(x)**2) == tan(x)**2
    assert TrigSimplify(-1 + csc(x)**2) == cot(x)**2

def test_MergeFactors():
    assert simplify(MergeFactors(b/(a - c)**3 , 8*c**3*(b*x + c)**(3/2)/(3*b**4) - 24*c**2*(b*x + c)**(5/2)/(5*b**4) + \
        24*c*(b*x + c)**(7/2)/(7*b**4) - 8*(b*x + c)**(9/2)/(9*b**4)) - (8*c**3*(b*x + c)**1.5/(3*b**3) - 24*c**2*(b*x + c)**2.5/(5*b**3) + \
        24*c*(b*x + c)**3.5/(7*b**3) - 8*(b*x + c)**4.5/(9*b**3))/(a - c)**3) == 0
    assert MergeFactors(x, x) == x**2
    assert MergeFactors(x*y, x) == x**2*y

def test_FactorInteger():
    assert FactorInteger(2434500) == [(2, 2), (3, 2), (5, 3), (541, 1)]

def test_ContentFactor():
    assert ContentFactor(a*b + a*c) == a*(b + c)

def test_Order():
    assert Order(a, b) == 1
    assert Order(b, a) == -1
    assert Order(a, a) == 0

def test_FactorOrder():
    assert FactorOrder(1, 1) == 0
    assert FactorOrder(1, 2) == -1
    assert FactorOrder(2, 1) == 1
    assert FactorOrder(a, b) == 1

def test_Smallest():
    assert Smallest([2, 1, 3, 4]) == 1
    assert Smallest(1, 2) == 1
    assert Smallest(-1, -2) == -2

def test_MostMainFactorPosition():
    assert MostMainFactorPosition([S(1), S(2), S(3)]) == 1
    assert MostMainFactorPosition([S(1), S(7), S(3), S(4), S(5)]) == 2

def test_OrderedQ():
    assert OrderedQ([a, b])
    assert not OrderedQ([b, a])

def test_MinimumDegree():
    assert MinimumDegree(S(1), S(2)) == 1
    assert MinimumDegree(S(1), sqrt(2)) == 1
    assert MinimumDegree(sqrt(2), S(1)) == 1
    assert MinimumDegree(sqrt(3), sqrt(2)) == sqrt(2)
    assert MinimumDegree(sqrt(2), sqrt(2)) == sqrt(2)

def test_PositiveFactors():
    assert PositiveFactors(S(0)) == 1
    assert PositiveFactors(-S(1)) == S(1)
    assert PositiveFactors(sqrt(2)) == sqrt(2)
    assert PositiveFactors(-log(2)) == log(2)
    assert PositiveFactors(sqrt(2)*S(-1)) == sqrt(2)

def test_NonpositiveFactors():
    assert NonpositiveFactors(S(0)) == 0
    assert NonpositiveFactors(-S(1)) == -1
    assert NonpositiveFactors(sqrt(2)) == 1
    assert NonpositiveFactors(-log(2)) == -1

def test_Sign():
    assert Sign(S(0)) == 0
    assert Sign(S(1)) == 1
    assert Sign(-S(1)) == -1

def test_PolynomialInQ():
    v = log(x)
    assert PolynomialInQ(S(1), v, x)
    assert PolynomialInQ(v, v, x)
    assert PolynomialInQ(1 + v**2, v, x)
    assert PolynomialInQ(1 + a*v**2, v, x)
    assert not PolynomialInQ(sqrt(v), v, x)


def test_ExponentIn():
    v = log(x)
    assert ExponentIn(S(1), log(x), x) == 0
    assert ExponentIn(S(1) + v, log(x), x) == 1
    assert ExponentIn(S(1) + v + v**3, log(x), x) == 3
    assert ExponentIn(S(2)*sqrt(v)*v**3, log(x), x) == 3.5

def test_PolynomialInSubst():
    v = log(x)
    assert PolynomialInSubst(S(1) + log(x)**3, log(x), x) == 1 + x**3
    assert PolynomialInSubst(S(1) + log(x), log(x), x) == x + 1

def test_Distrib():
    assert Distrib(x, a) == x*a
    assert Distrib(x, a + b) == a*x + b*x

def test_DistributeDegree():
    assert DistributeDegree(x, m) == x**m
    assert DistributeDegree(x**a, m) == x**(a*m)
    assert DistributeDegree(a*b, m) == a**m * b**m

def test_FunctionOfPower():
    assert FunctionOfPower(a, x) == None
    assert FunctionOfPower(x, x) == 1
    assert FunctionOfPower(x**3, x) == 3
    assert FunctionOfPower(x**3*cos(x**6), x) == 3

def test_DivideDegreesOfFactors():
    assert DivideDegreesOfFactors(a**b, S(3)) == a**(b/3)
    assert DivideDegreesOfFactors(a**b*c, S(3)) == a**(b/3)*c**(c/3)

def test_MonomialFactor():
    assert MonomialFactor(a, x) == [0, a]
    assert MonomialFactor(x, x) == [1, 1]
    assert MonomialFactor(x + y, x) == [0, x + y]
    assert MonomialFactor(log(x), x) == [0, log(x)]
    assert MonomialFactor(log(x)*x, x) == [1, log(x)]

def test_NormalizeIntegrand():
    assert NormalizeIntegrand((x**2 + 8), x) == x**2 + 8
    assert NormalizeIntegrand((x**2 + 3*x)**2, x) == x**2*(x + 3)**2
    assert NormalizeIntegrand(a**2*(a + b*x)**2, x) == a**2*(a + b*x)**2
    assert NormalizeIntegrand(b**2/(a**2*(a + b*x)**2), x) == b**2/(a**2*(a + b*x)**2)

def test_NormalizeIntegrandAux():
    v = (6*A*a*c - 2*A*b**2 + B*a*b)/(a*x**2) - (6*A*a**2*c**2 - 10*A*a*b**2*c - 8*A*a*b*c**2*x + 2*A*b**4 + 2*A*b**3*c*x + 5*B*a**2*b*c + 4*B*a**2*c**2*x - B*a*b**3 - B*a*b**2*c*x)/(a**2*(a + b*x + c*x**2)) + (-2*A*b + B*a)*(4*a*c - b**2)/(a**2*x)
    assert NormalizeIntegrandAux(v, x) == (6*A*a*c - 2*A*b**2 + B*a*b)/(a*x**2) - (6*A*a**2*c**2 - 10*A*a*b**2*c + 2*A*b**4 + 5*B*a**2*b*c - B*a*b**3 + x*(-8*A*a*b*c**2 + 2*A*b**3*c + 4*B*a**2*c**2 - B*a*b**2*c))/(a**2*(a + b*x + c*x**2)) + (-2*A*b + B*a)*(4*a*c - b**2)/(a**2*x)
    assert NormalizeIntegrandAux((x**2 + 3*x)**2, x) == x**2*(x + 3)**2
    assert NormalizeIntegrandAux((x**2 + 8), x) == x**2 + 8

def test_NormalizeIntegrandFactor():
    assert NormalizeIntegrandFactor((3*x + x**3)**2, x) == x**2*(x**2 + 3)**2
    assert NormalizeIntegrandFactor((x**2 + 8), x) == x**2 + 8

def test_NormalizeIntegrandFactorBase():
    assert NormalizeIntegrandFactorBase((x**2 + 8)**3, x) == (x**2 + 8)**3
    assert NormalizeIntegrandFactorBase((x**2 + 8), x) == x**2 + 8
    assert NormalizeIntegrandFactorBase(a**2*(a + b*x)**2, x) == a**2*(a + b*x)**2

def test_AbsorbMinusSign():
    assert AbsorbMinusSign((x + 2)**5*(x + 3)**5) == (-x - 3)**5*(x + 2)**5
    assert  AbsorbMinusSign((x + 2)**5*(x + 3)**2) == -(x + 2)**5*(x + 3)**2

def test_NormalizeLeadTermSigns():
    assert NormalizeLeadTermSigns((-x + 3)*(x**2 + 3)) == (-x + 3)*(x**2 + 3)
    assert NormalizeLeadTermSigns(x + 3) == x + 3

def test_SignOfFactor():
    assert SignOfFactor(S(-x + 3)) == [1, -x + 3]
    assert SignOfFactor(S(-x)) == [-1, x]

def test_NormalizePowerOfLinear():
    assert NormalizePowerOfLinear((x + 3)**5, x) == (x + 3)**5
    assert NormalizePowerOfLinear(((x + 3)**2) + 3, x) == x**2 + 6*x + 12

def test_SimplifyIntegrand():
    assert SimplifyIntegrand((x**2 + 3)**2, x) == (x**2 + 3)**2
    assert SimplifyIntegrand(x**2 + 3 + (x**6) + 6, x) == x**6 + x**2 + 9

def test_SimplifyTerm():
    assert SimplifyTerm(a**2/b**2, x) == a**2/b**2
    assert SimplifyTerm(-6*x/5 + (5*x + 3)**2/25 - 9/25, x) == x**2

def test_togetherSimplify():
    assert TogetherSimplify(-6*x/5 + (5*x + 3)**2/25 - 9/25) == x**2

def test_ExpandToSum():

    qq = 6
    Pqq = e**3
    Pq = (d+e*x**2)**3
    aa = 2
    nn = 2
    cc = 1
    pp = -1/2
    bb = 3
    assert nsimplify(ExpandToSum(Pq - Pqq*x**qq - Pqq*(aa*x**(-2*nn + qq)*(-2*nn + qq + 1) + bb*x**(-nn + qq)*(nn*(pp - 1) + qq + 1))/(cc*(2*nn*pp + qq + 1)), x) - \
        (d**3 + x**4*(3*d*e**2 - 2.4*e**3) + x**2*(3*d**2*e - 1.2*e**3))) == 0
    assert ExpandToSum(x**2 + 3*x + 3, x**3 + 3, x) == x**3*(x**2 + 3*x + 3) + 3*x**2 + 9*x + 9
    assert ExpandToSum(x**3 + 6, x) == x**3 + 6
    assert ExpandToSum(S(x**2 + 3*x + 3)*3, x) == 3*x**2 + 9*x + 9
    assert ExpandToSum((a + b*x), x) == a + b*x

def test_UnifySum():
    assert UnifySum((3 + x + 6*x**3 + sin(x)), x) == 6*x**3 + x + sin(x) + 3
    assert UnifySum((3 + x + 6*x**3)*3, x) == 18*x**3 + 3*x + 9

def test_FunctionOfInverseLinear():
    assert FunctionOfInverseLinear((x)/(a + b*x), x) == [a, b]
    assert FunctionOfInverseLinear((c + d*x)/(a + b*x), x) == [a, b]
    assert not FunctionOfInverseLinear(1/(a + b*x), x)

def test_PureFunctionOfSinhQ():
    v = log(x)
    f = sinh(v)
    assert PureFunctionOfSinhQ(f, v, x)
    assert not PureFunctionOfSinhQ(cosh(v), v, x)
    assert PureFunctionOfSinhQ(f**2, v, x)

def test_PureFunctionOfTanhQ():
    v = log(x)
    f = tanh(v)
    assert PureFunctionOfTanhQ(f, v, x)
    assert not PureFunctionOfTanhQ(cosh(v), v, x)
    assert PureFunctionOfTanhQ(f**2, v, x)

def test_PureFunctionOfCoshQ():
    v = log(x)
    f = cosh(v)
    assert PureFunctionOfCoshQ(f, v, x)
    assert not PureFunctionOfCoshQ(sinh(v), v, x)
    assert PureFunctionOfCoshQ(f**2, v, x)

def test_IntegerQuotientQ():
    u = S(2)*sin(x)
    v = sin(x)
    assert IntegerQuotientQ(u, v)
    assert IntegerQuotientQ(u, u)
    assert not IntegerQuotientQ(S(1), S(2))

def test_OddQuotientQ():
    u = S(3)*sin(x)
    v = sin(x)
    assert OddQuotientQ(u, v)
    assert OddQuotientQ(u, u)
    assert not OddQuotientQ(S(1), S(2))

def test_EvenQuotientQ():
    u = S(2)*sin(x)
    v = sin(x)
    assert EvenQuotientQ(u, v)
    assert not EvenQuotientQ(u, u)
    assert not EvenQuotientQ(S(1), S(2))

def test_FunctionOfSinhQ():
    v = log(x)
    assert FunctionOfSinhQ(cos(sinh(v)), v, x)
    assert FunctionOfSinhQ(sinh(v), v, x)
    assert FunctionOfSinhQ(sinh(v)*cos(sinh(v)), v, x)

def test_FunctionOfCoshQ():
    v = log(x)
    assert FunctionOfCoshQ(cos(cosh(v)), v, x)
    assert FunctionOfCoshQ(cosh(v), v, x)
    assert FunctionOfCoshQ(cosh(v)*cos(cosh(v)), v, x)

def test_FunctionOfTanhQ():
    v = log(x)
    t = Tanh(v)
    c = Coth(v)
    assert FunctionOfTanhQ(t, v, x)
    assert FunctionOfTanhQ(c, v, x)
    assert FunctionOfTanhQ(t + c, v, x)
    assert FunctionOfTanhQ(t*c, v, x)
    assert not FunctionOfTanhQ(sin(x), v, x)

def test_FunctionOfTanhWeight():
    v = log(x)
    t = Tanh(v)
    c = Coth(v)
    assert FunctionOfTanhWeight(x, v, x) == 0
    assert FunctionOfTanhWeight(sinh(v), v, x) == 0
    assert FunctionOfTanhWeight(tanh(v), v, x) == 1
    assert FunctionOfTanhWeight(coth(v), v, x) == -1
    assert FunctionOfTanhWeight(t**2, v, x) == 1
    assert FunctionOfTanhWeight(sinh(v)**2, v, x) == -1
    assert FunctionOfTanhWeight(coth(v)*sinh(v)**2, v, x) == -2

def test_FunctionOfHyperbolicQ():
    v = log(x)
    s = Sinh(v)
    t = Tanh(v)
    assert not FunctionOfHyperbolicQ(x, v, x)
    assert FunctionOfHyperbolicQ(s + t, v, x)
    assert FunctionOfHyperbolicQ(sinh(t), v, x)

def test_SmartNumerator():
    assert SmartNumerator(x**(-2)) == 1
    assert SmartNumerator(x**(2)*a) == x**2*a

def test_SmartDenominator():
    assert SmartDenominator(x**(-2)) == x**2
    assert SmartDenominator(x**(-2)*1/S(3)) == x**2*3

def test_SubstForAux():
    v = log(x)
    assert SubstForAux(v, v, x) == x
    assert SubstForAux(v**2, v, x) == x**2
    assert SubstForAux(x, v, x) == x
    assert SubstForAux(v**2, v**4, x) == sqrt(x)
    assert SubstForAux(v**2*v, v, x) == x**3

def test_SubstForTrig():
    v = log(x)
    s, c, t = sin(v), cos(v), tan(v)
    assert SubstForTrig(cos(a/2 + b*x/2), x/sqrt(x**2 + 1), 1/sqrt(x**2 + 1), a/2 + b*x/2, x) == 1/sqrt(x**2 + 1)
    assert SubstForTrig(s, sin, cos, v, x) == sin
    assert SubstForTrig(t, sin(v), cos(v), v, x) == sin(log(x))/cos(log(x))
    assert SubstForTrig(sin(2*v), sin(x), cos(x), v, x) == 2*sin(x)*cos(x)
    assert SubstForTrig(s*t, sin(x), cos(x), v, x) == sin(x)**2/cos(x)

def test_SubstForHyperbolic():
    v = log(x)
    s, c, t = sinh(v), cosh(v), tanh(v)
    assert SubstForHyperbolic(s, sinh(x), cosh(x), v, x) == sinh(x)
    assert SubstForHyperbolic(t, sinh(x), cosh(x), v, x) == sinh(x)/cosh(x)
    assert SubstForHyperbolic(sinh(2*v), sinh(x), cosh(x), v, x) == 2*sinh(x)*cosh(x)
    assert SubstForHyperbolic(s*t, sinh(x), cosh(x), v, x) == sinh(x)**2/cosh(x)

def test_SubstForFractionalPowerOfLinear():
    u = a + b*x
    assert not SubstForFractionalPowerOfLinear(u, x)
    assert not SubstForFractionalPowerOfLinear(u**(S(2)), x)
    assert SubstForFractionalPowerOfLinear(u**(S(1)/2), x) == [x**2, 2, a + b*x, 1/b]

def test_InverseFunctionOfLinear():
    u = a + b*x
    assert InverseFunctionOfLinear(log(u)*sin(x), x) == log(u)
    assert InverseFunctionOfLinear(log(u), x) == log(u)

def test_InertTrigQ():
    s = sin(x)
    c = cos(x)
    assert not InertTrigQ(sin(x), csc(x), cos(h))
    assert InertTrigQ(sin(x), csc(x))
    assert not InertTrigQ(s, c)
    assert InertTrigQ(c)

def test_PowerOfInertTrigSumQ():
    func = sin
    assert PowerOfInertTrigSumQ((1 + S(2)*(S(3)*func(x**2))**S(5))**3, func, x)
    assert PowerOfInertTrigSumQ((1 + 2*(S(3)*func(x**2))**3 + 4*(S(5)*func(x**2))**S(3))**2, func, x)

def test_PiecewiseLinearQ():
    assert PiecewiseLinearQ(a + b*x, x)
    assert not PiecewiseLinearQ(Log(c*sin(a)**S(3)), x)
    assert not PiecewiseLinearQ(x**3, x)
    assert PiecewiseLinearQ(atanh(tanh(a + b*x)), x)
    assert PiecewiseLinearQ(tanh(atanh(a + b*x)), x)
    assert not PiecewiseLinearQ(coth(atanh(a + b*x)), x)

def test_KnownTrigIntegrandQ():
    func = sin(a + b*x)
    assert KnownTrigIntegrandQ([sin], S(1), x)
    assert KnownTrigIntegrandQ([sin], (a + b*func)**m, x)
    assert KnownTrigIntegrandQ([sin], (a + b*func)**m*(1 + 2*func), x)
    assert KnownTrigIntegrandQ([sin], a + c*func**2, x)
    assert KnownTrigIntegrandQ([sin], a + b*func + c*func**2, x)
    assert KnownTrigIntegrandQ([sin], (a + b*func)**m*(c + d*func**2), x)
    assert KnownTrigIntegrandQ([sin], (a + b*func)**m*(c + d*func + e*func**2), x)
    assert not KnownTrigIntegrandQ([cos], (a + b*func)**m, x)

def test_KnownSineIntegrandQ():
    assert KnownSineIntegrandQ((a + b*sin(a + b*x))**m, x)

def test_KnownTangentIntegrandQ():
    assert KnownTangentIntegrandQ((a + b*tan(a + b*x))**m, x)

def test_KnownCotangentIntegrandQ():
    assert KnownCotangentIntegrandQ((a + b*cot(a + b*x))**m, x)

def test_KnownSecantIntegrandQ():
    assert KnownSecantIntegrandQ((a + b*sec(a + b*x))**m, x)

def test_TryPureTanSubst():
    assert TryPureTanSubst(atan(c*(a + b*tan(a + b*x))), x)
    assert TryPureTanSubst(atanh(c*(a + b*cot(a + b*x))), x)
    assert not TryPureTanSubst(tan(c*(a + b*cot(a + b*x))), x)

def test_TryPureTanhSubst():
    assert not TryPureTanhSubst(log(x), x)
    assert TryPureTanhSubst(sin(x), x)
    assert not TryPureTanhSubst(atanh(a*tanh(x)), x)
    assert not TryPureTanhSubst((a + b*x)**S(2), x)

def test_TryTanhSubst():
    assert not TryTanhSubst(log(x), x)
    assert not TryTanhSubst(a*(b + c)**3, x)
    assert not TryTanhSubst(1/(a + b*sinh(x)**S(3)), x)
    assert not TryTanhSubst(sinh(S(3)*x)*cosh(S(4)*x), x)
    assert not TryTanhSubst(a*(b*sech(x)**3)**c, x)

def test_GeneralizedBinomialQ():
    assert GeneralizedBinomialQ(a*x**q + b*x**n, x)
    assert not GeneralizedBinomialQ(a*x**q, x)

def test_GeneralizedTrinomialQ():
    assert not GeneralizedTrinomialQ(7 + 2*x**6 + 3*x**12, x)
    assert not GeneralizedTrinomialQ(a*x**q + c*x**(2*n-q), x)

def test_SubstForFractionalPowerOfQuotientOfLinears():
    assert SubstForFractionalPowerOfQuotientOfLinears(((a + b*x)/(c + d*x))**(S(3)/2), x) == [x**4/(b - d*x**2)**2, 2, (a + b*x)/(c + d*x), -a*d + b*c]

def test_SubstForFractionalPowerQ():
    assert SubstForFractionalPowerQ(x, sin(x), x)
    assert SubstForFractionalPowerQ(x**2, sin(x), x)
    assert not SubstForFractionalPowerQ(x**(S(3)/2), sin(x), x)
    assert SubstForFractionalPowerQ(sin(x)**(S(3)/2), sin(x), x)

def test_AbsurdNumberGCD():
    assert AbsurdNumberGCD(S(4)) == 4
    assert AbsurdNumberGCD(S(4), S(8), S(12)) == 4
    assert AbsurdNumberGCD(S(2), S(3), S(12)) == 1

def test_TrigReduce():
    assert TrigReduce(cos(x)**2) == cos(2*x)/2 + 1/2
    assert TrigReduce(cos(x)**2*sin(x)) == sin(x)/4 + sin(3*x)/4
    assert TrigReduce(cos(x)**2+sin(x)) == sin(x) + cos(2*x)/2 + 1/2
    assert TrigReduce(cos(x)**2*sin(x)**5) == 5*sin(x)/64 + sin(3*x)/64 - 3*sin(5*x)/64 + sin(7*x)/64
    assert TrigReduce(2*sin(x)*cos(x) + 2*cos(x)**2) == sin(2*x) + cos(2*x) + 1
    assert TrigReduce(sinh(a + b*x)**2) == cosh(2*a + 2*b*x)/2 - 1/2
    assert TrigReduce(sinh(a + b*x)*cosh(a + b*x)) == sinh(2*a + 2*b*x)/2

def test_FunctionOfDensePolynomialsQ():
    assert FunctionOfDensePolynomialsQ(x**2 + 3, x)
    assert not FunctionOfDensePolynomialsQ(x**2, x)
    assert not FunctionOfDensePolynomialsQ(x, x)
    assert FunctionOfDensePolynomialsQ(S(2), x)

def test_PureFunctionOfSinQ():
    v = log(x)
    f = sin(v)
    assert PureFunctionOfSinQ(f, v, x)
    assert not PureFunctionOfSinQ(cos(v), v, x)
    assert PureFunctionOfSinQ(f**2, v, x)

def test_PureFunctionOfTanQ():
    v = log(x)
    f = tan(v)
    assert PureFunctionOfTanQ(f, v, x)
    assert not PureFunctionOfTanQ(cos(v), v, x)
    assert PureFunctionOfTanQ(f**2, v, x)

def test_PowerVariableSubst():
    assert PowerVariableSubst((2*x)**3, 2, x) == 8*x**(3/2)
    assert PowerVariableSubst((2*x)**3, 2, x) == 8*x**(3/2)
    assert PowerVariableSubst((2*x), 2, x) == 2*x
    assert PowerVariableSubst((2*x)**3, 2, x) == 8*x**(3/2)
    assert PowerVariableSubst((2*x)**7, 2, x) == 128*x**(7/2)
    assert PowerVariableSubst((6+2*x)**7, 2, x) == (2*x + 6)**7
    assert PowerVariableSubst((2*x)**7+3, 2, x) == 128*x**(7/2) + 3

def test_PowerVariableDegree():
    assert PowerVariableDegree(S(2), 0, 2*x, x) == [0, 2*x]
    assert PowerVariableDegree((2*x)**2, 0, 2*x, x) == [2, 1]
    assert PowerVariableDegree(x**2, 0, 2*x, x) == [2, 1]
    assert PowerVariableDegree(S(4), 0, 2*x, x) == [0, 2*x]

def test_PowerVariableExpn():
    assert not PowerVariableExpn((x)**3, 2, x)
    assert not PowerVariableExpn((2*x)**3, 2, x)
    assert PowerVariableExpn((2*x)**2, 4, x) == [4*x**3, 2, 1]

def test_FunctionOfQ():
    assert FunctionOfQ(x**2, sqrt(-exp(2*x**2) + 1)*exp(x**2),x)
    assert not FunctionOfQ(S(x**3), x*2, x)
    assert FunctionOfQ(S(a), x*2, x)
    assert FunctionOfQ(S(3*x), x*2, x)

def test_ExpandTrigExpand():
    assert ExpandTrigExpand(1, cos(x), x**2, 2, 2, x) == 4*cos(x**2)**4 - 4*cos(x**2)**2 + 1
    assert ExpandTrigExpand(1, cos(x) + sin(x), x**2, 2, 2, x) == 4*sin(x**2)**2*cos(x**2)**2 + 8*sin(x**2)*cos(x**2)**3 - 4*sin(x**2)*cos(x**2) + 4*cos(x**2)**4 - 4*cos(x**2)**2 + 1

def test_TrigToExp():
    from sympy.integrals.rubi.utility_function import rubi_exp as exp
    assert TrigToExp(sin(x)) == -I*(exp(I*x) - exp(-I*x))/2
    assert TrigToExp(cos(x)) == exp(I*x)/2 + exp(-I*x)/2
    assert TrigToExp(cos(x)*tan(x**2)) == I*(exp(I*x)/2 + exp(-I*x)/2)*(-exp(I*x**2) + exp(-I*x**2))/(exp(I*x**2) + exp(-I*x**2))
    assert TrigToExp(cos(x) + sin(x)**2) == -(exp(I*x) - exp(-I*x))**2/4 + exp(I*x)/2 + exp(-I*x)/2
    assert Simplify(TrigToExp(cos(x)*tan(x**S(2))*sin(x)**S(2))-(-I*(exp(I*x)/S(2) + exp(-I*x)/S(2))*(exp(I*x) - exp(-I*x))**S(2)*(-exp(I*x**S(2)) + exp(-I*x**S(2)))/(S(4)*(exp(I*x**S(2)) + exp(-I*x**S(2)))))) == 0

def test_ExpandTrigReduce():
    assert ExpandTrigReduce(2*cos(3 + x)**3, x) == 3*cos(x + 3)/2 + cos(3*x + 9)/2
    assert ExpandTrigReduce(2*sin(x)**3+cos(2 + x), x) == 3*sin(x)/2 - sin(3*x)/2 + cos(x + 2)
    assert ExpandTrigReduce(cos(x + 3)**2, x) == cos(2*x + 6)/2 + 1/2

def test_NormalizeTrig():
    assert NormalizeTrig(S(2*sin(2 + x)), x) == 2*sin(x + 2)
    assert NormalizeTrig(S(2*sin(2 + x)**3), x) == 2*sin(x + 2)**3
    assert NormalizeTrig(S(2*sin((2 + x)**2)**3), x) == 2*sin(x**2 + 4*x + 4)**3

def test_FunctionOfTrigQ():
    v = log(x)
    s = sin(v)
    t = tan(v)
    assert not FunctionOfTrigQ(x, v, x)
    assert FunctionOfTrigQ(s + t, v, x)
    assert FunctionOfTrigQ(sin(t), v, x)

def test_RationalFunctionExpand():
    assert RationalFunctionExpand(x**S(5)*(e + f*x)**n/(a + b*x**S(3)), x) == -a*x**2*(e + f*x)**n/(b*(a + b*x**3)) +\
        e**2*(e + f*x)**n/(b*f**2) - 2*e*(e + f*x)**(n + 1)/(b*f**2) + (e + f*x)**(n + 2)/(b*f**2)
    assert RationalFunctionExpand(x**S(3)*(S(2)*x + 2)**S(2)/(2*x**2 + 1), x) == 2*x**3 + 4*x**2 + x + (- x + 2)/(2*x**2 + 1) - 2
    assert RationalFunctionExpand((a + b*x + c*x**4)*log(x)**3, x) == a*log(x)**3 + b*x*log(x)**3 + c*x**4*log(x)**3
    assert RationalFunctionExpand(a + b*x + c*x**4, x) == a + b*x + c*x**4

def test_SameQ():
    assert SameQ(1, 1, 1)
    assert not SameQ(1, 1, 2)

def test_Map2():
    assert Map2(Add, [a, b, c], [x, y, z]) == [a + x, b + y, c + z]

def test_ConstantFactor():
    assert ConstantFactor(a + a*x**3, x) == [a, x**3 + 1]
    assert ConstantFactor(a, x) == [a, 1]
    assert ConstantFactor(x, x) == [1, x]
    assert ConstantFactor(x**S(3), x) == [1, x**3]
    assert ConstantFactor(x**(S(3)/2), x) == [1, x**(3/2)]
    assert ConstantFactor(a*x**3, x) == [a, x**3]
    assert ConstantFactor(a + x**3, x) == [1, a + x**3]

def test_CommonFactors():
    assert CommonFactors([a, a, a]) == [a, 1, 1, 1]
    assert CommonFactors([x*S(2), x**S(3)*S(2), sin(x)*x*S(2)]) == [2, x, x**3, x*sin(x)]
    assert CommonFactors([x, x**S(3), sin(x)*x]) == [1, x, x**3, x*sin(x)]
    assert CommonFactors([S(2), S(4), S(6)]) == [2, 1, 2, 3]

def test_FunctionOfLinear():
    f = sin(a + b*x)
    assert FunctionOfLinear(f, x) == [sin(x), a, b]
    assert FunctionOfLinear(a + b*x, x) == [x, a, b]
    assert not FunctionOfLinear(a, x)

def test_FunctionOfExponentialQ():
    assert FunctionOfExponentialQ(exp(x + exp(x) + exp(exp(x))), x)
    assert FunctionOfExponentialQ(a**(a + b*x), x)
    assert FunctionOfExponentialQ(a**(b*x), x)
    assert not FunctionOfExponentialQ(a**sin(a + b*x), x)

def test_FunctionOfExponential():
    assert FunctionOfExponential(a**(a + b*x), x)

def test_FunctionOfExponentialFunction():
    assert FunctionOfExponentialFunction(a**(a + b*x), x) == x
    assert FunctionOfExponentialFunction(S(2)*a**(a + b*x), x) == 2*x

def test_FunctionOfTrig():
    assert FunctionOfTrig(sin(x + 1), x + 1, x) == x + 1
    assert FunctionOfTrig(sin(x), x) == x
    assert not FunctionOfTrig(cos(x**2 + 1), x)
    assert FunctionOfTrig(sin(a+b*x)**3, x) == a+b*x

def test_AlgebraicTrigFunctionQ():
    assert AlgebraicTrigFunctionQ(sin(x + 3), x)
    assert AlgebraicTrigFunctionQ(x, x)
    assert AlgebraicTrigFunctionQ(x + 1, x)
    assert AlgebraicTrigFunctionQ(sinh(x + 1), x)
    assert AlgebraicTrigFunctionQ(sinh(x + 1)**2, x)
    assert not AlgebraicTrigFunctionQ(sinh(x**2 + 1)**2, x)

def test_FunctionOfHyperbolic():
    assert FunctionOfTrig(sin(x + 1), x + 1, x) == x + 1
    assert FunctionOfTrig(sin(x), x) == x
    assert not FunctionOfTrig(cos(x**2 + 1), x)

def test_FunctionOfExpnQ():
    assert FunctionOfExpnQ(x, x, x) == 1
    assert FunctionOfExpnQ(x**2, x, x) == 2
    assert FunctionOfExpnQ(x**2.1, x, x) == 1
    assert not FunctionOfExpnQ(x, x**2, x)
    assert not FunctionOfExpnQ(x + 1, (x + 5)**2, x)
    assert not FunctionOfExpnQ(x + 1, (x + 1)**2, x)

def test_PureFunctionOfCosQ():
    v = log(x)
    f = cos(v)
    assert PureFunctionOfCosQ(f, v, x)
    assert not PureFunctionOfCosQ(sin(v), v, x)
    assert PureFunctionOfCosQ(f**2, v, x)

def test_PureFunctionOfCotQ():
    v = log(x)
    f = cot(v)
    assert PureFunctionOfCotQ(f, v, x)
    assert not PureFunctionOfCotQ(sin(v), v, x)
    assert PureFunctionOfCotQ(f**2, v, x)

def test_FunctionOfSinQ():
    v = log(x)
    assert FunctionOfSinQ(cos(sin(v)), v, x)
    assert FunctionOfSinQ(sin(v), v, x)
    assert FunctionOfSinQ(sin(v)*cos(sin(v)), v, x)

def test_FunctionOfCosQ():
    v = log(x)
    assert FunctionOfCosQ(cos(cos(v)), v, x)
    assert FunctionOfCosQ(cos(v), v, x)
    assert FunctionOfCosQ(cos(v)*cos(cos(v)), v, x)

def test_FunctionOfTanQ():
    v = log(x)
    t = tan(v)
    c = cot(v)
    assert FunctionOfTanQ(t, v, x)
    assert FunctionOfTanQ(c, v, x)
    assert FunctionOfTanQ(t + c, v, x)
    assert FunctionOfTanQ(t*c, v, x)
    assert not FunctionOfTanQ(sin(x), v, x)

def test_FunctionOfTanWeight():
    v = log(x)
    t = tan(v)
    c = cot(v)
    assert FunctionOfTanWeight(x, v, x) == 0
    assert FunctionOfTanWeight(sin(v), v, x) == 0
    assert FunctionOfTanWeight(tan(v), v, x) == 1
    assert FunctionOfTanWeight(cot(v), v, x) == -1
    assert FunctionOfTanWeight(t**2, v, x) == 1
    assert FunctionOfTanWeight(sin(v)**2, v, x) == -1
    assert FunctionOfTanWeight(cot(v)*sin(v)**2, v, x) == -2

def test_OddTrigPowerQ():
    assert not OddTrigPowerQ(sin(x)**3, 1, x)
    assert OddTrigPowerQ(sin(3),1,x)
    assert OddTrigPowerQ(sin(3*x),x,x)
    assert OddTrigPowerQ(sin(3*x)**3,x,x)

def test_FunctionOfLog():
    assert not FunctionOfLog(x**2*(a + b*x)**3*exp(-a - b*x) ,False, False, x)
    assert FunctionOfLog(log(2*x**8)*2 + log(2*x**8) + 1, x) == [3*x + 1, 2*x**8, 8]
    assert FunctionOfLog(log(2*x)**2,x) == [x**2, 2*x, 1]
    assert FunctionOfLog(log(3*x**3)**2 + 1,x) == [x**2 + 1, 3*x**3, 3]
    assert FunctionOfLog(log(2*x**8)*2,x) == [2*x, 2*x**8, 8]
    assert not FunctionOfLog(2*sin(x)*2,x)

def test_EulerIntegrandQ():
    assert EulerIntegrandQ((2*x + 3*((x + 1)**3)**1.5)**(-3), x)
    assert not EulerIntegrandQ((2*x + (2*x**2)**2)**3, x)
    assert not EulerIntegrandQ(3*x**2 + 5*x + 1, x)

def test_Divides():
    assert not Divides(x, a*x**2, x)
    assert Divides(x, a*x, x) == a

def test_EasyDQ():
    assert EasyDQ(3*x**2, x)
    assert EasyDQ(3*x**3 - 6, x)
    assert EasyDQ(x**3, x)
    assert EasyDQ(sin(x**log(3)), x)

def test_ProductOfLinearPowersQ():
    assert ProductOfLinearPowersQ(S(1), x)
    assert ProductOfLinearPowersQ((x + 1)**3, x)
    assert not ProductOfLinearPowersQ((x**2 + 1)**3, x)
    assert ProductOfLinearPowersQ(x + 1, x)

def test_Rt():
    b = symbols('b')
    assert Rt(-b**2, 4) == (-b**2)**(S(1)/S(4))
    assert Rt(x**2, 2) == x
    assert Rt(S(2 + 3*I), S(8)) == (2 + 3*I)**(1/8)
    assert Rt(x**2 + 4 + 4*x, 2) == x + 2
    assert Rt(S(8), S(3)) == 2
    assert Rt(S(16807), S(5)) == 7

def test_NthRoot():
    assert NthRoot(S(14580), S(3)) == 9*2**(S(2)/S(3))*5**(S(1)/S(3))
    assert NthRoot(9, 2) == 3.0
    assert NthRoot(81, 2) == 9.0
    assert NthRoot(81, 4) == 3.0

def test_AtomBaseQ():
    assert not AtomBaseQ(x**2)
    assert AtomBaseQ(x**3)
    assert AtomBaseQ(x)
    assert AtomBaseQ(S(2)**3)
    assert not AtomBaseQ(sin(x))

def test_SumBaseQ():
    assert not SumBaseQ((x + 1)**2)
    assert SumBaseQ((x + 1)**3)
    assert SumBaseQ((3*x+3))
    assert not SumBaseQ(x)

def test_NegSumBaseQ():
    assert not NegSumBaseQ(-x + 1)
    assert NegSumBaseQ(x - 1)
    assert not NegSumBaseQ((x - 1)**2)
    assert NegSumBaseQ((x - 1)**3)

def test_AllNegTermQ():
    x = Symbol('x', negative=True)
    assert AllNegTermQ(x)
    assert not AllNegTermQ(x + 2)
    assert AllNegTermQ(x - 2)
    assert AllNegTermQ((x - 2)**3)
    assert not AllNegTermQ((x - 2)**2)

def test_TrigSquareQ():
    assert TrigSquareQ(sin(x)**2)
    assert TrigSquareQ(cos(x)**2)
    assert not TrigSquareQ(tan(x)**2)

def test_Inequality():
    assert not Inequality(S('0'), Less, m, LessEqual, S('1'))
    assert Inequality(S('0'), Less, S('1'))
    assert Inequality(S('0'), Less, S('1'), LessEqual, S('5'))

def test_SplitProduct():
    assert SplitProduct(OddQ, S(3)*x) == [3, x]
    assert not SplitProduct(OddQ, S(2)*x)

def test_SplitSum():
    assert SplitSum(FracPart, sin(x)) == [sin(x), 0]
    assert SplitSum(FracPart, sin(x) + S(2)) == [sin(x), S(2)]

def test_Complex():
    assert Complex(a, b) == a + I*b

def test_SimpFixFactor():
    assert SimpFixFactor((a*c + b*c)**S(4), x) == (a*c + b*c)**4
    assert SimpFixFactor((a*Complex(0, c) + b*Complex(0, d))**S(3), x) == -I*(a*c + b*d)**3
    assert SimpFixFactor((a*Complex(0, d) + b*Complex(0, e) + c*Complex(0, f))**S(2), x) == -(a*d + b*e + c*f)**2
    assert SimpFixFactor((a + b*x**(-1/S(2))*x**S(3))**S(3), x) == (a + b*x**(5/2))**3
    assert SimpFixFactor((a*c + b*c**S(2)*x**S(2))**S(3), x) == c**3*(a + b*c*x**2)**3
    assert SimpFixFactor((a*c**S(2) + b*c**S(1)*x**S(2))**S(3), x) == c**3*(a*c + b*x**2)**3
    assert SimpFixFactor(a*cos(x)**2 + a*sin(x)**2 + v, x) == a*cos(x)**2 + a*sin(x)**2 + v

def test_SimplifyAntiderivative():
    assert SimplifyAntiderivative(acoth(coth(x)), x) == x
    assert SimplifyAntiderivative(a*x, x) == a*x
    assert SimplifyAntiderivative(atanh(cot(x)), x) == atanh(2*sin(x)*cos(x))/2
    assert SimplifyAntiderivative(a*cos(x)**2 + a*sin(x)**2 + v, x) == a*cos(x)**2 + a*sin(x)**2

def test_FixSimplify():
    assert FixSimplify(x*Complex(0, a)*(v*Complex(0, b) + w)**S(3)) == a*x*(b*v - I*w)**3

def test_TrigSimplifyAux():
    assert TrigSimplifyAux(a*cos(x)**2 + a*sin(x)**2 + v) == a + v
    assert TrigSimplifyAux(x**2) == x**2

def test_SubstFor():
    assert SubstFor(x**2 + 1, tanh(x), x) == tanh(x)
    assert SubstFor(x**2, sinh(x), x) == sinh(sqrt(x))

def test_FresnelS():
    assert  FresnelS(oo) == 1/2
    assert FresnelS(0) == 0

def test_FresnelC():
    assert FresnelC(0) == 0
    assert FresnelC(oo) == 1/2

def test_Erfc():
    assert Erfc(0) == 1
    assert Erfc(oo) == 0

def test_Erfi():
    assert Erfi(oo) == oo
    assert Erfi(0) == 0

def test_Gamma():
    assert Gamma(u) == gamma(u)

def test_ElementaryFunctionQ():
    assert  ElementaryFunctionQ(x + y)
    assert ElementaryFunctionQ(sin(x + y))
    assert ElementaryFunctionQ(E**(x*a))

def test_Util_Part():
    from sympy.integrals.rubi.utility_function import Util_Part
    assert Util_Part(1, a + b).doit() == a
    assert Util_Part(c, a + b).doit() == Util_Part(c, a + b)

def test_Part():
    assert Part([1, 2, 3], 1) == 1
    assert Part(a*b, 1) == a

def test_PolyLog():
    assert PolyLog(a, b) == polylog(a, b)

def test_PureFunctionOfCothQ():
    v = log(x)
    assert PureFunctionOfCothQ(coth(v), v, x)
    assert PureFunctionOfCothQ(a + coth(v), v, x)
    assert not PureFunctionOfCothQ(sin(v), v, x)

def test_ExpandIntegrand():
    assert ExpandIntegrand(sqrt(a + b*x**S(2) + c*x**S(4)), (f*x)**(S(3)/2)*(d + e*x**S(2)), x) == \
        d*(f*x)**(3/2)*sqrt(a + b*x**2 + c*x**4) + e*(f*x)**(7/2)*sqrt(a + b*x**2 + c*x**4)/f**2
    assert ExpandIntegrand((6*A*a*c - 2*A*b**2 + B*a*b - 2*c*x*(A*b - 2*B*a))/(x**2*(a + b*x + c*x**2)), x) == \
        (6*A*a*c - 2*A*b**2 + B*a*b)/(a*x**2) + (-6*A*a**2*c**2 + 10*A*a*b**2*c - 2*A*b**4 - 5*B*a**2*b*c + B*a*b**3 + x*(8*A*a*b*c**2 - 2*A*b**3*c - 4*B*a**2*c**2 + B*a*b**2*c))/(a**2*(a + b*x + c*x**2)) + (-2*A*b + B*a)*(4*a*c - b**2)/(a**2*x)
    assert ExpandIntegrand(x**2*(e + f*x)**3*F**(a + b*(c + d*x)**1), x) == F**(a + b*(c + d*x))*e**2*(e + f*x)**3/f**2 - 2*F**(a + b*(c + d*x))*e*(e + f*x)**4/f**2 + F**(a + b*(c + d*x))*(e + f*x)**5/f**2
    assert ExpandIntegrand((x)*(a + b*x)**2*f**(e*(c + d*x)**n), x) == a**2*f**(e*(c + d*x)**n)*x + 2*a*b*f**(e*(c + d*x)**n)*x**2 + b**2*f**(e*(c + d*x)**n)*x**3
    assert ExpandIntegrand(sin(x)**3*(a + b*(1/sin(x)))**2, x) == a**2*sin(x)**3 + 2*a*b*sin(x)**2 + b**2*sin(x)
    assert ExpandIntegrand(x*(a + b*ArcSin(c + d*x))**n, x) == -c*(a + b*asin(c + d*x))**n/d + (a + b*asin(c + d*x))**n*(c + d*x)/d
    assert ExpandIntegrand((a + b*x)**S(3)*(A + B*x)/(c + d*x), x) == B*(a + b*x)**3/d + b*(a + b*x)**2*(A*d - B*c)/d**2 + b*(a + b*x)*(A*d - B*c)*(a*d - b*c)/d**3 + b*(A*d - B*c)*(a*d - b*c)**2/d**4 + (A*d - B*c)*(a*d - b*c)**3/(d**4*(c + d*x))
    assert ExpandIntegrand((x**2)*(S(3)*x)**(S(1)/2), x) ==sqrt(3)*x**(5/2)
    assert ExpandIntegrand((x)*(sin(x))**(S(1)/2), x) == x*sqrt(sin(x))
    assert ExpandIntegrand(x*(e + f*x)**2*F**(b*(c + d*x)), x) == -F**(b*(c + d*x))*e*(e + f*x)**2/f + F**(b*(c + d*x))*(e + f*x)**3/f
    assert ExpandIntegrand(x**m*(e + f*x)**2*F**(b*(c + d*x)**n), x) == F**(b*(c + d*x)**n)*e**2*x**m + 2*F**(b*(c + d*x)**n)*e*f*x*x**m + F**(b*(c + d*x)**n)*f**2*x**2*x**m
    assert simplify(ExpandIntegrand((S(1) - S(1)*x**S(2))**(-S(3)), x) - (-S(3)/(8*(x**2 - 1)) + S(3)/(16*(x + 1)**2) + S(1)/(S(8)*(x + 1)**3) + S(3)/(S(16)*(x - 1)**2) - S(1)/(S(8)*(x - 1)**3))) == 0
    assert ExpandIntegrand(-S(1), 1/((-q - x)**3*(q - x)**3), x) == 1/(8*q**3*(q + x)**3) - 1/(8*q**3*(-q + x)**3) - 3/(8*q**4*(-q**2 + x**2)) + 3/(16*q**4*(q + x)**2) + 3/(16*q**4*(-q + x)**2)
    assert ExpandIntegrand((1 + 1*x)**(3)/(2 + 1*x), x) == x**2 + x + 1 - 1/(x + 2)
    assert ExpandIntegrand((c + d*x**1 + e*x**2)/(1 - x**3), x) == (c - (-1)**(S(1)/3)*d + (-1)**(S(2)/3)*e)/(-3*(-1)**(S(2)/3)*x + 3) + (c + (-1)**(S(2)/3)*d - (-1)**(S(1)/3)*e)/(3*(-1)**(S(1)/3)*x + 3) + (c + d + e)/(-3*x + 3)
    assert ExpandIntegrand((c + d*x**1 + e*x**2 + f*x**3)/(1 - x**4), x) == (c + I*d - e - I*f)/(4*I*x + 4) + (c - I*d - e + I*f)/(-4*I*x + 4) + (c - d + e - f)/(4*x + 4) + (c + d + e + f)/(-4*x + 4)
    assert ExpandIntegrand((d + e*(f + g*x))/(2 + 3*x + 1*x**2), x) == (-2*d - 2*e*f + 4*e*g)/(2*x + 4) + (2*d + 2*e*f - 2*e*g)/(2*x + 2)
    assert ExpandIntegrand(x/(a*x**3 + b*Sqrt(c + d*x**6)), x) == a*x**4/(-b**2*c + x**6*(a**2 - b**2*d)) + b*x*sqrt(c + d*x**6)/(b**2*c + x**6*(-a**2 + b**2*d))
    assert simplify(ExpandIntegrand(x**1*(1 - x**4)**(-2), x) - (x/(S(4)*(x**2 + 1)) + x/(S(4)*(x**2 + 1)**2) - x/(S(4)*(x**2 - 1)) + x/(S(4)*(x**2 - 1)**2))) == 0
    assert simplify(ExpandIntegrand((-1 + x**S(6))**(-3), x) - (S(3)/(S(8)*(x**6 - 1)) - S(3)/(S(16)*(x**S(3) + S(1))**S(2)) - S(1)/(S(8)*(x**S(3) + S(1))**S(3)) - S(3)/(S(16)*(x**S(3) - S(1))**S(2)) + S(1)/(S(8)*(x**S(3) - S(1))**S(3)))) == 0
    assert simplify(ExpandIntegrand(u**1*(a + b*u**2 + c*u**4)**(-1), x)) == simplify(1/(2*b*(u + sqrt(-(a + c*u**4)/b))) - 1/(2*b*(-u + sqrt(-(a + c*u**4)/b))))
    assert simplify(ExpandIntegrand((1 + 1*u + 1*u**2)**(-2), x) - (S(1)/(S(2)*(-u - 1)*(-u**2 - u - 1)) + S(1)/(S(4)*(-u - 1)*(u + sqrt(-u - 1))**2) + S(1)/(S(4)*(-u - 1)*(u - sqrt(-u - 1))**2))) == 0
    assert ExpandIntegrand(x*(a + b*Log(c*(d*(e + f*x)**p)**q))**n, x) == -e*(a + b*log(c*(d*(e + f*x)**p)**q))**n/f + (a + b*log(c*(d*(e + f*x)**p)**q))**n*(e + f*x)/f
    assert ExpandIntegrand(x*f**(e*(c + d*x)*S(1)), x) == f**(e*(c + d*x))*x
    assert simplify(ExpandIntegrand((x)*(a + b*x)**m*Log(c*(d + e*x**n)**p), x) - (-a*(a + b*x)**m*log(c*(d + e*x**n)**p)/b + (a + b*x)**(m + S(1))*log(c*(d + e*x**n)**p)/b)) == 0
    assert simplify(ExpandIntegrand(u*(a + b*F**v)**S(2)*(c + d*F**v)**S(-3), x) - (b**2*u/(d**2*(F**v*d + c)) + 2*b*u*(a*d - b*c)/(d**2*(F**v*d + c)**2) + u*(a*d - b*c)**2/(d**2*(F**v*d + c)**3))) == 0
    assert ExpandIntegrand((S(1) + 1*x)**S(2)*f**(e*(1 + S(1)*x)**n)/(g + h*x), x) == f**(e*(x + 1)**n)*(x + 1)/h + f**(e*(x + 1)**n)*(-g + h)/h**2 + f**(e*(x + 1)**n)*(g - h)**2/(h**2*(g + h*x))

    assert ExpandIntegrand((a*c - b*c*x)**2/(a + b*x)**2, x) == 4*a**2*c**2/(a + b*x)**2 - 4*a*c**2/(a + b*x) + c**2
    assert simplify(ExpandIntegrand(x**2*(1 - 1*x**2)**(-2), x) - (1/(S(2)*(x**2 - 1)) + 1/(S(4)*(x + 1)**2) + 1/(S(4)*(x - 1)**2))) == 0
    assert ExpandIntegrand((a + x)**2, x) == a**2 + 2*a*x + x**2
    assert ExpandIntegrand((a + b*x)**S(2)/x**3, x) == a**2/x**3 + 2*a*b/x**2 + b**2/x
    assert ExpandIntegrand(1/(x**2*(a + b*x)**2), x) == b**2/(a**2*(a + b*x)**2) + 1/(a**2*x**2) + 2*b**2/(a**3*(a + b*x)) - 2*b/(a**3*x)
    assert ExpandIntegrand((1 + x)**3/x, x) == x**2 + 3*x + 3 + 1/x
    assert ExpandIntegrand((1 + 2*(3 + 4*x**2))/(2 + 3*x**2 + 1*x**4), x) == 18/(2*x**2 + 4) - 2/(2*x**2 + 2)
    assert ExpandIntegrand((c + d*x**2 + e*x**3)/(1 - 1*x**4), x) == (c - d - I*e)/(4*I*x + 4) + (c - d + I*e)/(-4*I*x + 4) + (c + d - e)/(4*x + 4) + (c + d + e)/(-4*x + 4)
    assert ExpandIntegrand((a + b*x)**2/(c + d*x), x) == b*(a + b*x)/d + b*(a*d - b*c)/d**2 + (a*d - b*c)**2/(d**2*(c + d*x))
    assert ExpandIntegrand(x**2*(a + b*Log(c*(d*(e + f*x)**p)**q))**n, x) == e**2*(a + b*log(c*(d*(e + f*x)**p)**q))**n/f**2 - 2*e*(a + b*log(c*(d*(e + f*x)**p)**q))**n*(e + f*x)/f**2 + (a + b*log(c*(d*(e + f*x)**p)**q))**n*(e + f*x)**2/f**2
    assert ExpandIntegrand(x*(1 + 2*x)**3*log(2*(1 + 1*x**2)**1), x) == 8*x**4*log(2*x**2 + 2) + 12*x**3*log(2*x**2 + 2) + 6*x**2*log(2*x**2 + 2) + x*log(2*x**2 + 2)
    assert ExpandIntegrand((1 + 1*x)**S(3)*f**(e*(1 + 1*x)**n)/(g + h*x), x) == f**(e*(x + 1)**n)*(x + 1)**2/h + f**(e*(x + 1)**n)*(-g + h)*(x + 1)/h**2 + f**(e*(x + 1)**n)*(-g + h)**2/h**3 - f**(e*(x + 1)**n)*(g - h)**3/(h**3*(g + h*x))

def test_Dist():
    assert Dist(x, a + b, x) == a*x + b*x
    assert Dist(x, Integral(a + b , x), x) == x*Integral(a + b, x)
    assert Dist(3*x,(a+b), x) - Dist(2*x, (a+b), x) == a*x + b*x
    assert Dist(3*x,(a+b), x) + Dist(2*x, (a+b), x) == 5*a*x + 5*b*x
    assert Dist(x, c*Integral((a + b), x), x) == c*x*Integral(a + b, x)

def test_IntegralFreeQ():
    assert not IntegralFreeQ(Integral(a, x))
    assert IntegralFreeQ(a + b)

def test_OneQ():
    from sympy.integrals.rubi.utility_function import OneQ
    assert OneQ(S(1))
    assert not OneQ(S(2))

def test_DerivativeDivides():
    assert not DerivativeDivides(x, x, x)
    assert not DerivativeDivides(a, x + y, b)
    assert DerivativeDivides(a + x, a, x) == a
    assert DerivativeDivides(a + b, x + y, b) == x + y

def test_LogIntegral():
    from sympy.integrals.rubi.utility_function import LogIntegral
    assert LogIntegral(a) == li(a)

def test_SinIntegral():
    from sympy.integrals.rubi.utility_function import SinIntegral
    assert SinIntegral(a) == Si(a)

def test_CosIntegral():
    from sympy.integrals.rubi.utility_function import CosIntegral
    assert CosIntegral(a) == Ci(a)

def test_SinhIntegral():
    from sympy.integrals.rubi.utility_function import SinhIntegral
    assert SinhIntegral(a) == Shi(a)

def test_CoshIntegral():
    from sympy.integrals.rubi.utility_function import CoshIntegral
    assert CoshIntegral(a) == Chi(a)

def test_ExpIntegralEi():
    from sympy.integrals.rubi.utility_function import ExpIntegralEi
    assert ExpIntegralEi(a) == Ei(a)

def test_ExpIntegralE():
    from sympy.integrals.rubi.utility_function import ExpIntegralE
    assert ExpIntegralE(a, z) == expint(a, z)

def test_LogGamma():
    from sympy.integrals.rubi.utility_function import LogGamma
    assert LogGamma(a) == loggamma(a)

def test_Factorial():
    from sympy.integrals.rubi.utility_function import Factorial
    assert Factorial(S(5)) == 120

def test_Zeta():
    from sympy.integrals.rubi.utility_function import Zeta
    assert Zeta(a, z) == zeta(a, z)

def test_HypergeometricPFQ():
    from sympy.integrals.rubi.utility_function import HypergeometricPFQ
    assert HypergeometricPFQ([a, b], [c], z) == hyper([a, b], [c], z)

def test_PolyGamma():
    assert PolyGamma(S(2), S(3)) == polygamma(2, 3)

def test_ProductLog():
    from sympy import N
    assert N(ProductLog(S(5.0)), 5) == N(1.32672466524220, 5)
    assert N(ProductLog(S(2), S(3.5)), 5) == N(-1.14064876353898 + 10.8912237027092*I, 5)

def test_PolynomialQuotient():
    assert PolynomialQuotient(log((-a*d + b*c)/(b*(c + d*x)))/(c + d*x), a + b*x, e) == log((-a*d + b*c)/(b*(c + d*x)))/((a + b*x)*(c + d*x))
    assert PolynomialQuotient(x**2, x + a, x) == -a + x

def test_PolynomialRemainder():
    assert PolynomialRemainder(log((-a*d + b*c)/(b*(c + d*x)))/(c + d*x), a + b*x, e) == 0
    assert PolynomialRemainder(x**2, x + a, x) == a**2

def test_Floor():
    assert Floor(S(7.5)) == 7
    assert Floor(S(15.5), S(6)) == 12

def test_Factor():
    from sympy.integrals.rubi.utility_function import Factor
    assert Factor(a*b + a*c) == a*(b + c)

def test_Rule():
    from sympy.integrals.rubi.utility_function import Rule
    assert Rule(x, S(5)) == {x: 5}

def test_Distribute():
    assert Distribute((a + b)*c + (a + b)*d, Add) == c*(a + b) + d*(a + b)
    assert Distribute((a + b)*(c + e), Add) == a*c + a*e + b*c + b*e

def test_CoprimeQ():
    assert CoprimeQ(S(7), S(5))
    assert not CoprimeQ(S(6), S(3))

def test_Discriminant():
    from sympy.integrals.rubi.utility_function import Discriminant
    assert Discriminant(a*x**2 + b*x + c, x) == b**2 - 4*a*c
    assert Discriminant(1/x, x) == Discriminant(1/x, x)

def test_Sum_doit():
    assert Sum_doit(2*x + 2, [x, 0, 1.7]) == 6

def test_DeactivateTrig():
    assert DeactivateTrig(sec(a + b*x), x) == sec(a + b*x)

def test_Negative():
    from sympy.integrals.rubi.utility_function import Negative
    assert Negative(S(-2))
    assert not Negative(S(0))

def test_Quotient():
    from sympy.integrals.rubi.utility_function import Quotient
    assert Quotient(17, 5) == 3

def test_process_trig():
    assert process_trig(x*cot(x)) == x/tan(x)
    assert process_trig(coth(x)*csc(x)) == S(1)/(tanh(x)*sin(x))

def test_replace_pow_exp():
    assert replace_pow_exp(rubi_exp(S(5))) == exp(S(5))

def test_rubi_unevaluated_expr():
    from sympy.integrals.rubi.utility_function import rubi_unevaluated_expr
    assert rubi_unevaluated_expr(a)*rubi_unevaluated_expr(b) == rubi_unevaluated_expr(b)*rubi_unevaluated_expr(a)

def test_rubi_exp():
    # class name in utility_function is `exp`. To avoid confusion `rubi_exp` has been used here
    assert isinstance(rubi_exp(a), Pow)

def test_rubi_log():
    # class name in utility_function is `log`. To avoid confusion `rubi_log` has been used here
    assert rubi_log(rubi_exp(S(a))) == a
