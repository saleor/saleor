import sys
from sympy.external import import_module
matchpy = import_module("matchpy")
if not matchpy:
    disabled = True
if sys.version_info[:2] < (3, 6):
    disabled = True

if matchpy:
    from matchpy import Pattern, ReplacementRule, CustomConstraint, is_match
    from sympy.integrals.rubi.utility_function import (
        sympy_op_factory, Int, Sum, Set, With, Module, Scan, MapAnd, FalseQ,
        ZeroQ, NegativeQ, NonzeroQ, FreeQ, NFreeQ, List, Log, PositiveQ,
        PositiveIntegerQ, NegativeIntegerQ, IntegerQ, IntegersQ,
        ComplexNumberQ, PureComplexNumberQ, RealNumericQ, PositiveOrZeroQ,
        NegativeOrZeroQ, FractionOrNegativeQ, NegQ, Equal, Unequal, IntPart,
        FracPart, RationalQ, ProductQ, SumQ, NonsumQ, Subst, First, Rest,
        SqrtNumberQ, SqrtNumberSumQ, LinearQ, Sqrt, ArcCosh, Coefficient,
        Denominator, Hypergeometric2F1, Not, Simplify, FractionalPart,
        IntegerPart, AppellF1, EllipticPi, EllipticE, EllipticF, ArcTan,
        ArcCot, ArcCoth, ArcTanh, ArcSin, ArcSinh, ArcCos, ArcCsc, ArcSec,
        ArcCsch, ArcSech, Sinh, Tanh, Cosh, Sech, Csch, Coth, LessEqual, Less,
        Greater, GreaterEqual, FractionQ, IntLinearcQ, Expand, IndependentQ,
        PowerQ, IntegerPowerQ, PositiveIntegerPowerQ, FractionalPowerQ, AtomQ,
        ExpQ, LogQ, Head, MemberQ, TrigQ, SinQ, CosQ, TanQ, CotQ, SecQ, CscQ,
        Sin, Cos, Tan, Cot, Sec, Csc, HyperbolicQ, SinhQ, CoshQ, TanhQ, CothQ,
        SechQ, CschQ, InverseTrigQ, SinCosQ, SinhCoshQ, LeafCount, Numerator,
        NumberQ, NumericQ, Length, ListQ, Im, Re, InverseHyperbolicQ,
        InverseFunctionQ, TrigHyperbolicFreeQ, InverseFunctionFreeQ, RealQ,
        EqQ, FractionalPowerFreeQ, ComplexFreeQ, PolynomialQ, FactorSquareFree,
        PowerOfLinearQ, Exponent, QuadraticQ, LinearPairQ, BinomialParts,
        TrinomialParts, PolyQ, EvenQ, OddQ, PerfectSquareQ, NiceSqrtAuxQ,
        NiceSqrtQ, Together, PosAux, PosQ, CoefficientList, ReplaceAll,
        ExpandLinearProduct, GCD, ContentFactor, NumericFactor,
        NonnumericFactors, MakeAssocList, GensymSubst, KernelSubst,
        ExpandExpression, Apart, SmartApart, MatchQ,
        PolynomialQuotientRemainder, FreeFactors, NonfreeFactors,
        RemoveContentAux, RemoveContent, FreeTerms, NonfreeTerms,
        ExpandAlgebraicFunction, CollectReciprocals, ExpandCleanup,
        AlgebraicFunctionQ, Coeff, LeadTerm, RemainingTerms, LeadFactor,
        RemainingFactors, LeadBase, LeadDegree, Numer, Denom, hypergeom, Expon,
        MergeMonomials, PolynomialDivide, BinomialQ, TrinomialQ,
        GeneralizedBinomialQ, GeneralizedTrinomialQ, FactorSquareFreeList,
        PerfectPowerTest, SquareFreeFactorTest, RationalFunctionQ,
        RationalFunctionFactors, NonrationalFunctionFactors, Reverse,
        RationalFunctionExponents, RationalFunctionExpand, ExpandIntegrand,
        SimplerQ, SimplerSqrtQ, SumSimplerQ, BinomialDegree, TrinomialDegree,
        CancelCommonFactors, SimplerIntegrandQ, GeneralizedBinomialDegree,
        GeneralizedBinomialParts, GeneralizedTrinomialDegree,
        GeneralizedTrinomialParts, MonomialQ, MonomialSumQ,
        MinimumMonomialExponent, MonomialExponent, LinearMatchQ,
        PowerOfLinearMatchQ, QuadraticMatchQ, CubicMatchQ, BinomialMatchQ,
        TrinomialMatchQ, GeneralizedBinomialMatchQ, GeneralizedTrinomialMatchQ,
        QuotientOfLinearsMatchQ, PolynomialTermQ, PolynomialTerms,
        NonpolynomialTerms, PseudoBinomialParts, NormalizePseudoBinomial,
        PseudoBinomialPairQ, PseudoBinomialQ, PolynomialGCD, PolyGCD,
        AlgebraicFunctionFactors, NonalgebraicFunctionFactors,
        QuotientOfLinearsP, QuotientOfLinearsParts, QuotientOfLinearsQ,
        Flatten, Sort, AbsurdNumberQ, AbsurdNumberFactors,
        NonabsurdNumberFactors, SumSimplerAuxQ, Prepend, Drop,
        CombineExponents, FactorInteger, FactorAbsurdNumber,
        SubstForInverseFunction, SubstForFractionalPower,
        SubstForFractionalPowerOfQuotientOfLinears,
        FractionalPowerOfQuotientOfLinears, SubstForFractionalPowerQ,
        SubstForFractionalPowerAuxQ, FractionalPowerOfSquareQ,
        FractionalPowerSubexpressionQ, Apply, FactorNumericGcd,
        MergeableFactorQ, MergeFactor, MergeFactors, TrigSimplifyQ,
        TrigSimplify, TrigSimplifyRecur, Order, FactorOrder, Smallest,
        OrderedQ, MinimumDegree, PositiveFactors, Sign, NonpositiveFactors,
        PolynomialInAuxQ, PolynomialInQ, ExponentInAux, ExponentIn,
        PolynomialInSubstAux, PolynomialInSubst, Distrib, DistributeDegree,
        FunctionOfPower, DivideDegreesOfFactors, MonomialFactor, FullSimplify,
        FunctionOfLinearSubst, FunctionOfLinear, NormalizeIntegrand,
        NormalizeIntegrandAux, NormalizeIntegrandFactor,
        NormalizeIntegrandFactorBase, NormalizeTogether,
        NormalizeLeadTermSigns, AbsorbMinusSign, NormalizeSumFactors,
        SignOfFactor, NormalizePowerOfLinear, SimplifyIntegrand, SimplifyTerm,
        TogetherSimplify, SmartSimplify, SubstForExpn, ExpandToSum, UnifySum,
        UnifyTerms, UnifyTerm, CalculusQ, FunctionOfInverseLinear,
        PureFunctionOfSinhQ, PureFunctionOfTanhQ, PureFunctionOfCoshQ,
        IntegerQuotientQ, OddQuotientQ, EvenQuotientQ, FindTrigFactor,
        FunctionOfSinhQ, FunctionOfCoshQ, OddHyperbolicPowerQ, FunctionOfTanhQ,
        FunctionOfTanhWeight, FunctionOfHyperbolicQ, SmartNumerator,
        SmartDenominator, SubstForAux, ActivateTrig, ExpandTrig, TrigExpand,
        SubstForTrig, SubstForHyperbolic, InertTrigFreeQ, LCM,
        SubstForFractionalPowerOfLinear, FractionalPowerOfLinear,
        InverseFunctionOfLinear, InertTrigQ, InertReciprocalQ, DeactivateTrig,
        FixInertTrigFunction, DeactivateTrigAux, PowerOfInertTrigSumQ,
        PiecewiseLinearQ, KnownTrigIntegrandQ, KnownSineIntegrandQ,
        KnownTangentIntegrandQ, KnownCotangentIntegrandQ,
        KnownSecantIntegrandQ, TryPureTanSubst, TryTanhSubst, TryPureTanhSubst,
        AbsurdNumberGCD, AbsurdNumberGCDList, ExpandTrigExpand,
        ExpandTrigReduce, ExpandTrigReduceAux, NormalizeTrig, TrigToExp,
        ExpandTrigToExp, TrigReduce, FunctionOfTrig, AlgebraicTrigFunctionQ,
        FunctionOfHyperbolic, FunctionOfQ, FunctionOfExpnQ, PureFunctionOfSinQ,
        PureFunctionOfCosQ, PureFunctionOfTanQ, PureFunctionOfCotQ,
        FunctionOfCosQ, FunctionOfSinQ, OddTrigPowerQ, FunctionOfTanQ,
        FunctionOfTanWeight, FunctionOfTrigQ, FunctionOfDensePolynomialsQ,
        FunctionOfLog, PowerVariableExpn, PowerVariableDegree,
        PowerVariableSubst, EulerIntegrandQ, FunctionOfSquareRootOfQuadratic,
        SquareRootOfQuadraticSubst, Divides, EasyDQ, ProductOfLinearPowersQ,
        Rt, NthRoot, AtomBaseQ, SumBaseQ, NegSumBaseQ, AllNegTermQ,
        SomeNegTermQ, TrigSquareQ, RtAux, TrigSquare, IntSum, IntTerm, Map2,
        ConstantFactor, SameQ, ReplacePart, CommonFactors,
        MostMainFactorPosition, FunctionOfExponentialQ, FunctionOfExponential,
        FunctionOfExponentialFunction, FunctionOfExponentialFunctionAux,
        FunctionOfExponentialTest, FunctionOfExponentialTestAux, stdev,
        rubi_test, If, IntQuadraticQ, IntBinomialQ, RectifyTangent,
        RectifyCotangent, Inequality, Condition, Simp, SimpHelp, SplitProduct,
        SplitSum, SubstFor, SubstForAux, FresnelS, FresnelC, Erfc, Erfi, Gamma,
        FunctionOfTrigOfLinearQ, ElementaryFunctionQ, Complex, UnsameQ,
        _SimpFixFactor, SimpFixFactor, _FixSimplify, FixSimplify,
        _SimplifyAntiderivativeSum, SimplifyAntiderivativeSum,
        _SimplifyAntiderivative, SimplifyAntiderivative, _TrigSimplifyAux,
        TrigSimplifyAux, Cancel, Part, PolyLog, D, Dist, Sum_doit, PolynomialQuotient, Floor,
        PolynomialRemainder, Factor, PolyLog, CosIntegral, SinIntegral, LogIntegral, SinhIntegral,
        CoshIntegral, Rule, Erf, PolyGamma, ExpIntegralEi, ExpIntegralE, LogGamma , UtilityOperator, Factorial,
        Zeta, ProductLog, DerivativeDivides, HypergeometricPFQ, IntHide, OneQ, Null, exp, log, Discriminant
    )
    from sympy import (Integral, S, sqrt, And, Or, Integer, Float, Mod, I, Abs, simplify, Mul, Add, Pow)
    from sympy.integrals.rubi.symbol import WC
    from sympy.core.symbol import symbols, Symbol
    from sympy.functions import (sin, cos, tan, cot, csc, sec, sqrt, erf)
    from sympy.functions.elementary.hyperbolic import (acosh, asinh, atanh, acoth, acsch, asech, cosh, sinh, tanh, coth, sech, csch)
    from sympy.functions.elementary.trigonometric import (atan, acsc, asin, acot, acos, asec, atan2)
    from sympy import pi as Pi

from sympy.integrals.rubi.rubi import rubi_integrate
from sympy import Integral as Integrate, exp, log

a, b, c, d, e, f, g, h, i, j, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z = symbols('a b c d e f g h i j k l m n o p q r s t u v w x y z')
A, B, C, F, G, H, J, K, L, M, N, O, P, Q, R, T, U, V, W, X, Y, Z = symbols('A B C F G H J K L M N O P Q R T U V W X Y Z')

def test_error_functions():

    assert rubi_test(rubi_integrate(x**S(5)*Erf(b*x)**S(2), x), x, x**S(6)*Erf(b*x)**S(2)/S(6) - S(5)*Erf(b*x)**S(2)/(S(16)*b**S(6)) + x**S(4)*exp(-S(2)*b**S(2)*x**S(2))/(S(6)*Pi*b**S(2)) + S(7)*x**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(12)*Pi*b**S(4)) + S(11)*exp(-S(2)*b**S(2)*x**S(2))/(S(12)*Pi*b**S(6)) + x**S(5)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*b) + S(5)*x**S(3)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(6)*sqrt(Pi)*b**S(3)) + S(5)*x*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(4)*Erf(b*x)**S(2), x), x, x**S(5)*Erf(b*x)**S(2)/S(5) + x**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(5)*Pi*b**S(2)) + S(11)*x*exp(-S(2)*b**S(2)*x**S(2))/(S(20)*Pi*b**S(4)) + S(2)*x**S(4)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(5)*sqrt(Pi)*b) + S(4)*x**S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(5)*sqrt(Pi)*b**S(3)) + S(4)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(5)*sqrt(Pi)*b**S(5)) - S(43)*sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(80)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(3)*Erf(b*x)**S(2), x), x, x**S(4)*Erf(b*x)**S(2)/S(4) - S(3)*Erf(b*x)**S(2)/(S(16)*b**S(4)) + x**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*Pi*b**S(2)) + exp(-S(2)*b**S(2)*x**S(2))/(S(2)*Pi*b**S(4)) + x**S(3)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*sqrt(Pi)*b) + S(3)*x*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erf(b*x)**S(2), x), x, x**S(3)*Erf(b*x)**S(2)/S(3) + x*exp(-S(2)*b**S(2)*x**S(2))/(S(3)*Pi*b**S(2)) + S(2)*x**S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*b) + S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*b**S(3)) - S(5)*sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(12)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erf(b*x)**S(2), x), x, x**S(2)*Erf(b*x)**S(2)/S(2) - Erf(b*x)**S(2)/(S(4)*b**S(2)) + exp(-S(2)*b**S(2)*x**S(2))/(S(2)*Pi*b**S(2)) + x*Erf(b*x)*exp(-b**S(2)*x**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)**S(2), x), x, x*Erf(b*x)**S(2) - sqrt(S(2))*sqrt(S(1)/Pi)*Erf(sqrt(S(2))*b*x)/b + S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)**S(2)/x, x), x, Integrate(Erf(b*x)**S(2)/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)**S(2)/x**S(2), x), x, Integrate(Erf(b*x)**S(2)/x**S(2), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)**S(2)/x**S(3), x), x, -b**S(2)*Erf(b*x)**S(2) - Erf(b*x)**S(2)/(S(2)*x**S(2)) + S(2)*b**S(2)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/Pi - S(2)*b*Erf(b*x)*exp(-b**S(2)*x**S(2))/(sqrt(Pi)*x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)**S(2)/x**S(4), x), x, Integrate(Erf(b*x)**S(2)/x**S(4), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)**S(2)/x**S(5), x), x, b**S(4)*Erf(b*x)**S(2)/S(3) - Erf(b*x)**S(2)/(S(4)*x**S(4)) - S(4)*b**S(4)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/(S(3)*Pi) - b**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(3)*Pi*x**S(2)) + S(2)*b**S(3)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x) - b*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)**S(2)/x**S(6), x), x, Integrate(Erf(b*x)**S(2)/x**S(6), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)**S(2)/x**S(7), x), x, -S(4)*b**S(6)*Erf(b*x)**S(2)/S(45) - Erf(b*x)**S(2)/(S(6)*x**S(6)) + S(28)*b**S(6)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/(S(45)*Pi) + S(2)*b**S(4)*exp(-S(2)*b**S(2)*x**S(2))/(S(9)*Pi*x**S(2)) - b**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(15)*Pi*x**S(4)) - S(8)*b**S(5)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(45)*sqrt(Pi)*x) + S(4)*b**S(3)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(45)*sqrt(Pi)*x**S(3)) - S(2)*b*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(15)*sqrt(Pi)*x**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)**S(2)/x**S(8), x), x, Integrate(Erf(b*x)**S(2)/x**S(8), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(3)*Erf(a + b*x), x), x, -a**S(4)*Erf(a + b*x)/(S(4)*b**S(4)) - S(3)*a**S(2)*Erf(a + b*x)/(S(4)*b**S(4)) + x**S(4)*Erf(a + b*x)/S(4) - S(3)*Erf(a + b*x)/(S(16)*b**S(4)) - a**S(3)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(4)) + S(3)*a**S(2)*(a + b*x)*exp(-(a + b*x)**S(2))/(S(2)*sqrt(Pi)*b**S(4)) - a*(a + b*x)**S(2)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(4)) - a*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(4)) + (a + b*x)**S(3)*exp(-(a + b*x)**S(2))/(S(4)*sqrt(Pi)*b**S(4)) + (S(3)*a + S(3)*b*x)*exp(-(a + b*x)**S(2))/(S(8)*sqrt(Pi)*b**S(4)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erf(a + b*x), x), x, a**S(3)*Erf(a + b*x)/(S(3)*b**S(3)) + a*Erf(a + b*x)/(S(2)*b**S(3)) + x**S(3)*Erf(a + b*x)/S(3) + a**S(2)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) - a*(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) + (a + b*x)**S(2)*exp(-(a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)) + exp(-(a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erf(a + b*x), x), x, -a**S(2)*Erf(a + b*x)/(S(2)*b**S(2)) + x**S(2)*Erf(a + b*x)/S(2) - Erf(a + b*x)/(S(4)*b**S(2)) - a*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(2)) + (a + b*x)*exp(-(a + b*x)**S(2))/(S(2)*sqrt(Pi)*b**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(a + b*x), x), x, (a + b*x)*Erf(a + b*x)/b + exp(-(a + b*x)**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(a + b*x)/x, x), x, Integrate(Erf(a + b*x)/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(a + b*x)/x**S(2), x), x, -Erf(a + b*x)/x + S(2)*b*Integrate(exp(-(a + b*x)**S(2))/x, x)/sqrt(Pi), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erf(a + b*x)**S(2), x), x, a**S(2)*(a + b*x)*Erf(a + b*x)**S(2)/b**S(3) - sqrt(S(2))*a**S(2)*sqrt(S(1)/Pi)*Erf(sqrt(S(2))*(a + b*x))/b**S(3) - a*(a + b*x)**S(2)*Erf(a + b*x)**S(2)/b**S(3) + a*Erf(a + b*x)**S(2)/(S(2)*b**S(3)) + (a + b*x)**S(3)*Erf(a + b*x)**S(2)/(S(3)*b**S(3)) - a*exp(-S(2)*(a + b*x)**S(2))/(Pi*b**S(3)) + (a + b*x)*exp(-S(2)*(a + b*x)**S(2))/(S(3)*Pi*b**S(3)) + S(2)*a**S(2)*Erf(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) - S(2)*a*(a + b*x)*Erf(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) + S(2)*(a + b*x)**S(2)*Erf(a + b*x)*exp(-(a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)) - S(5)*sqrt(S(2))*Erf(sqrt(S(2))*(a + b*x))/(S(12)*sqrt(Pi)*b**S(3)) + S(2)*Erf(a + b*x)*exp(-(a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erf(a + b*x)**S(2), x), x, -a*(a + b*x)*Erf(a + b*x)**S(2)/b**S(2) + sqrt(S(2))*a*sqrt(S(1)/Pi)*Erf(sqrt(S(2))*(a + b*x))/b**S(2) + (a + b*x)**S(2)*Erf(a + b*x)**S(2)/(S(2)*b**S(2)) - Erf(a + b*x)**S(2)/(S(4)*b**S(2)) + exp(-S(2)*(a + b*x)**S(2))/(S(2)*Pi*b**S(2)) - S(2)*a*Erf(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(2)) + (a + b*x)*Erf(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(a + b*x)**S(2), x), x, (a + b*x)*Erf(a + b*x)**S(2)/b - sqrt(S(2))*sqrt(S(1)/Pi)*Erf(sqrt(S(2))*(a + b*x))/b + S(2)*Erf(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(a + b*x)**S(2)/x, x), x, Integrate(Erf(a + b*x)**S(2)/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(a + b*x)**S(2)/x**S(2), x), x, Integrate(Erf(a + b*x)**S(2)/x**S(2), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(6)*Erf(b*x)*exp(-b**S(2)*x**S(2)), x), x, S(15)*sqrt(Pi)*Erf(b*x)**S(2)/(S(32)*b**S(7)) - x**S(5)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) - S(5)*x**S(3)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*b**S(4)) - S(15)*x*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(8)*b**S(6)) - x**S(4)*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)) - S(7)*x**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(8)*sqrt(Pi)*b**S(5)) - S(11)*exp(-S(2)*b**S(2)*x**S(2))/(S(8)*sqrt(Pi)*b**S(7)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(5)*Erf(b*x)*exp(-b**S(2)*x**S(2)), x), x, -x**S(4)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) - x**S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/b**S(4) - Erf(b*x)*exp(-b**S(2)*x**S(2))/b**S(6) + S(43)*sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(64)*b**S(6)) - x**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)) - S(11)*x*exp(-S(2)*b**S(2)*x**S(2))/(S(16)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(4)*Erf(b*x)*exp(-b**S(2)*x**S(2)), x), x, S(3)*sqrt(Pi)*Erf(b*x)**S(2)/(S(16)*b**S(5)) - x**S(3)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) - S(3)*x*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*b**S(4)) - x**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)) - exp(-S(2)*b**S(2)*x**S(2))/(S(2)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(3)*Erf(b*x)*exp(-b**S(2)*x**S(2)), x), x, -x**S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) - Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(4)) + S(5)*sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(16)*b**S(4)) - x*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2)), x), x, sqrt(Pi)*Erf(b*x)**S(2)/(S(8)*b**S(3)) - x*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) - exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erf(b*x)*exp(-b**S(2)*x**S(2)), x), x, -Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) + sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(4)*b**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)*exp(-b**S(2)*x**S(2)), x), x, sqrt(Pi)*Erf(b*x)**S(2)/(S(4)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)*exp(-b**S(2)*x**S(2))/x, x), x, Integrate(Erf(b*x)*exp(-b**S(2)*x**S(2))/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)*exp(-b**S(2)*x**S(2))/x**S(2), x), x, -sqrt(Pi)*b*Erf(b*x)**S(2)/S(2) - Erf(b*x)*exp(-b**S(2)*x**S(2))/x + b*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/sqrt(Pi), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)*exp(-b**S(2)*x**S(2))/x**S(3), x), x, -sqrt(S(2))*b**S(2)*Erf(sqrt(S(2))*b*x) - b**S(2)*Integrate(Erf(b*x)*exp(-b**S(2)*x**S(2))/x, x) - Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*x**S(2)) - b*exp(-S(2)*b**S(2)*x**S(2))/(sqrt(Pi)*x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)*exp(-b**S(2)*x**S(2))/x**S(4), x), x, sqrt(Pi)*b**S(3)*Erf(b*x)**S(2)/S(3) + S(2)*b**S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*x) - Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*x**S(3)) - S(4)*b**S(3)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/(S(3)*sqrt(Pi)) - b*exp(-S(2)*b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)*exp(-b**S(2)*x**S(2))/x**S(5), x), x, S(7)*sqrt(S(2))*b**S(4)*Erf(sqrt(S(2))*b*x)/S(6) + b**S(4)*Integrate(Erf(b*x)*exp(-b**S(2)*x**S(2))/x, x)/S(2) + b**S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*x**S(2)) - Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*x**S(4)) + S(7)*b**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(6)*sqrt(Pi)*x) - b*exp(-S(2)*b**S(2)*x**S(2))/(S(6)*sqrt(Pi)*x**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erf(b*x)*exp(-b**S(2)*x**S(2))/x**S(6), x), x, -S(2)*sqrt(Pi)*b**S(5)*Erf(b*x)**S(2)/S(15) - S(4)*b**S(4)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(15)*x) + S(2)*b**S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(15)*x**S(3)) - Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(5)*x**S(5)) + S(14)*b**S(5)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/(S(15)*sqrt(Pi)) + b**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x**S(2)) - b*exp(-S(2)*b**S(2)*x**S(2))/(S(10)*sqrt(Pi)*x**S(4)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(b**S(2)*Erf(b*x)*exp(-b**S(2)*x**S(2))/x + Erf(b*x)*exp(-b**S(2)*x**S(2))/x**S(3), x), x, -sqrt(S(2))*b**S(2)*Erf(sqrt(S(2))*b*x) - Erf(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*x**S(2)) - b*exp(-S(2)*b**S(2)*x**S(2))/(sqrt(Pi)*x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)**S(2)/x**S(8), x), x, Integrate(Erfc(b*x)**S(2)/x**S(8), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)**S(2)/x**S(7), x), x, -S(4)*b**S(6)*Erfc(b*x)**S(2)/S(45) - Erfc(b*x)**S(2)/(S(6)*x**S(6)) + S(28)*b**S(6)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/(S(45)*Pi) + S(2)*b**S(4)*exp(-S(2)*b**S(2)*x**S(2))/(S(9)*Pi*x**S(2)) - b**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(15)*Pi*x**S(4)) + S(8)*b**S(5)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(45)*sqrt(Pi)*x) - S(4)*b**S(3)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(45)*sqrt(Pi)*x**S(3)) + S(2)*b*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(15)*sqrt(Pi)*x**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)**S(2)/x**S(6), x), x, Integrate(Erfc(b*x)**S(2)/x**S(6), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)**S(2)/x**S(5), x), x, b**S(4)*Erfc(b*x)**S(2)/S(3) - Erfc(b*x)**S(2)/(S(4)*x**S(4)) - S(4)*b**S(4)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/(S(3)*Pi) - b**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(3)*Pi*x**S(2)) - S(2)*b**S(3)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x) + b*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)**S(2)/x**S(4), x), x, Integrate(Erfc(b*x)**S(2)/x**S(4), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)**S(2)/x**S(3), x), x, -b**S(2)*Erfc(b*x)**S(2) - Erfc(b*x)**S(2)/(S(2)*x**S(2)) + S(2)*b**S(2)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/Pi + S(2)*b*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(sqrt(Pi)*x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)**S(2)/x**S(2), x), x, Integrate(Erfc(b*x)**S(2)/x**S(2), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)**S(2)/x, x), x, Integrate(Erfc(b*x)**S(2)/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)**S(2), x), x, x*Erfc(b*x)**S(2) - sqrt(S(2))*sqrt(S(1)/Pi)*Erf(sqrt(S(2))*b*x)/b - S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erfc(b*x)**S(2), x), x, x**S(2)*Erfc(b*x)**S(2)/S(2) - Erfc(b*x)**S(2)/(S(4)*b**S(2)) + exp(-S(2)*b**S(2)*x**S(2))/(S(2)*Pi*b**S(2)) - x*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erfc(b*x)**S(2), x), x, x**S(3)*Erfc(b*x)**S(2)/S(3) + x*exp(-S(2)*b**S(2)*x**S(2))/(S(3)*Pi*b**S(2)) - S(2)*x**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*b) - S(5)*sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(12)*sqrt(Pi)*b**S(3)) - S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(3)*Erfc(b*x)**S(2), x), x, x**S(4)*Erfc(b*x)**S(2)/S(4) - S(3)*Erfc(b*x)**S(2)/(S(16)*b**S(4)) + x**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*Pi*b**S(2)) + exp(-S(2)*b**S(2)*x**S(2))/(S(2)*Pi*b**S(4)) - x**S(3)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*sqrt(Pi)*b) - S(3)*x*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(4)*Erfc(b*x)**S(2), x), x, x**S(5)*Erfc(b*x)**S(2)/S(5) + x**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(5)*Pi*b**S(2)) + S(11)*x*exp(-S(2)*b**S(2)*x**S(2))/(S(20)*Pi*b**S(4)) - S(2)*x**S(4)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(5)*sqrt(Pi)*b) - S(4)*x**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(5)*sqrt(Pi)*b**S(3)) - S(43)*sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(80)*sqrt(Pi)*b**S(5)) - S(4)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(5)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(5)*Erfc(b*x)**S(2), x), x, x**S(6)*Erfc(b*x)**S(2)/S(6) - S(5)*Erfc(b*x)**S(2)/(S(16)*b**S(6)) + x**S(4)*exp(-S(2)*b**S(2)*x**S(2))/(S(6)*Pi*b**S(2)) + S(7)*x**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(12)*Pi*b**S(4)) + S(11)*exp(-S(2)*b**S(2)*x**S(2))/(S(12)*Pi*b**S(6)) - x**S(5)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*b) - S(5)*x**S(3)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(6)*sqrt(Pi)*b**S(3)) - S(5)*x*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(a + b*x)/x, x), x, Integrate(Erfc(a + b*x)/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(a + b*x), x), x, (a + b*x)*Erfc(a + b*x)/b - exp(-(a + b*x)**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erfc(a + b*x), x), x, a**S(2)*Erf(a + b*x)/(S(2)*b**S(2)) + x**S(2)*Erfc(a + b*x)/S(2) + Erf(a + b*x)/(S(4)*b**S(2)) + a*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(2)) - (a + b*x)*exp(-(a + b*x)**S(2))/(S(2)*sqrt(Pi)*b**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erfc(a + b*x), x), x, -a**S(3)*Erf(a + b*x)/(S(3)*b**S(3)) - a*Erf(a + b*x)/(S(2)*b**S(3)) + x**S(3)*Erfc(a + b*x)/S(3) - a**S(2)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) + a*(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) - (a + b*x)**S(2)*exp(-(a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)) - exp(-(a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(3)*Erfc(a + b*x), x), x, a**S(4)*Erf(a + b*x)/(S(4)*b**S(4)) + S(3)*a**S(2)*Erf(a + b*x)/(S(4)*b**S(4)) + x**S(4)*Erfc(a + b*x)/S(4) + S(3)*Erf(a + b*x)/(S(16)*b**S(4)) + a**S(3)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(4)) - S(3)*a**S(2)*(a + b*x)*exp(-(a + b*x)**S(2))/(S(2)*sqrt(Pi)*b**S(4)) + a*(a + b*x)**S(2)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(4)) + a*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(4)) - (a + b*x)**S(3)*exp(-(a + b*x)**S(2))/(S(4)*sqrt(Pi)*b**S(4)) - (S(3)*a + S(3)*b*x)*exp(-(a + b*x)**S(2))/(S(8)*sqrt(Pi)*b**S(4)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(a + b*x)**S(2)/x, x), x, Integrate(Erfc(a + b*x)**S(2)/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(a + b*x)**S(2), x), x, (a + b*x)*Erfc(a + b*x)**S(2)/b - sqrt(S(2))*sqrt(S(1)/Pi)*Erf(sqrt(S(2))*(a + b*x))/b - S(2)*Erfc(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erfc(a + b*x)**S(2), x), x, -a*(a + b*x)*Erfc(a + b*x)**S(2)/b**S(2) + sqrt(S(2))*a*sqrt(S(1)/Pi)*Erf(sqrt(S(2))*(a + b*x))/b**S(2) + (a + b*x)**S(2)*Erfc(a + b*x)**S(2)/(S(2)*b**S(2)) - Erfc(a + b*x)**S(2)/(S(4)*b**S(2)) + exp(-S(2)*(a + b*x)**S(2))/(S(2)*Pi*b**S(2)) + S(2)*a*Erfc(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(2)) - (a + b*x)*Erfc(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erfc(a + b*x)**S(2), x), x, a**S(2)*(a + b*x)*Erfc(a + b*x)**S(2)/b**S(3) - sqrt(S(2))*a**S(2)*sqrt(S(1)/Pi)*Erf(sqrt(S(2))*(a + b*x))/b**S(3) - a*(a + b*x)**S(2)*Erfc(a + b*x)**S(2)/b**S(3) + a*Erfc(a + b*x)**S(2)/(S(2)*b**S(3)) + (a + b*x)**S(3)*Erfc(a + b*x)**S(2)/(S(3)*b**S(3)) - a*exp(-S(2)*(a + b*x)**S(2))/(Pi*b**S(3)) + (a + b*x)*exp(-S(2)*(a + b*x)**S(2))/(S(3)*Pi*b**S(3)) - S(2)*a**S(2)*Erfc(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) + S(2)*a*(a + b*x)*Erfc(a + b*x)*exp(-(a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) - S(2)*(a + b*x)**S(2)*Erfc(a + b*x)*exp(-(a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)) - S(5)*sqrt(S(2))*Erf(sqrt(S(2))*(a + b*x))/(S(12)*sqrt(Pi)*b**S(3)) - S(2)*Erfc(a + b*x)*exp(-(a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x**S(8), x), x, -S(4)*sqrt(Pi)*b**S(7)*Erfc(b*x)**S(2)/S(105) + S(8)*b**S(6)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(105)*x) - S(4)*b**S(4)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(105)*x**S(3)) + S(2)*b**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(35)*x**S(5)) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(7)*x**S(7)) + S(16)*b**S(7)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/(S(35)*sqrt(Pi)) + S(4)*b**S(5)*exp(-S(2)*b**S(2)*x**S(2))/(S(21)*sqrt(Pi)*x**S(2)) - S(8)*b**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(105)*sqrt(Pi)*x**S(4)) + b*exp(-S(2)*b**S(2)*x**S(2))/(S(21)*sqrt(Pi)*x**S(6)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x**S(7), x), x, S(67)*sqrt(S(2))*b**S(6)*Erf(sqrt(S(2))*b*x)/S(90) - b**S(6)*Integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x, x)/S(6) - b**S(4)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(12)*x**S(2)) + b**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(12)*x**S(4)) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(6)*x**S(6)) + S(67)*b**S(5)*exp(-S(2)*b**S(2)*x**S(2))/(S(90)*sqrt(Pi)*x) - S(13)*b**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(90)*sqrt(Pi)*x**S(3)) + b*exp(-S(2)*b**S(2)*x**S(2))/(S(15)*sqrt(Pi)*x**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x**S(6), x), x, S(2)*sqrt(Pi)*b**S(5)*Erfc(b*x)**S(2)/S(15) - S(4)*b**S(4)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(15)*x) + S(2)*b**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(15)*x**S(3)) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(5)*x**S(5)) - S(14)*b**S(5)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/(S(15)*sqrt(Pi)) - b**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x**S(2)) + b*exp(-S(2)*b**S(2)*x**S(2))/(S(10)*sqrt(Pi)*x**S(4)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x**S(5), x), x, -S(7)*sqrt(S(2))*b**S(4)*Erf(sqrt(S(2))*b*x)/S(6) + b**S(4)*Integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x, x)/S(2) + b**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*x**S(2)) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*x**S(4)) - S(7)*b**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(6)*sqrt(Pi)*x) + b*exp(-S(2)*b**S(2)*x**S(2))/(S(6)*sqrt(Pi)*x**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x**S(4), x), x, -sqrt(Pi)*b**S(3)*Erfc(b*x)**S(2)/S(3) + S(2)*b**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*x) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(3)*x**S(3)) + S(4)*b**S(3)*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/(S(3)*sqrt(Pi)) + b*exp(-S(2)*b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x**S(3), x), x, sqrt(S(2))*b**S(2)*Erf(sqrt(S(2))*b*x) - b**S(2)*Integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x, x) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*x**S(2)) + b*exp(-S(2)*b**S(2)*x**S(2))/(sqrt(Pi)*x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x**S(2), x), x, sqrt(Pi)*b*Erfc(b*x)**S(2)/S(2) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/x - b*ExpIntegralEi(-S(2)*b**S(2)*x**S(2))/sqrt(Pi), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x, x), x, Integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2))/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfc(b*x)*exp(-b**S(2)*x**S(2)), x), x, -sqrt(Pi)*Erfc(b*x)**S(2)/(S(4)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erfc(b*x)*exp(-b**S(2)*x**S(2)), x), x, -sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(4)*b**S(2)) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2)), x), x, -sqrt(Pi)*Erfc(b*x)**S(2)/(S(8)*b**S(3)) - x*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) + exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(3)*Erfc(b*x)*exp(-b**S(2)*x**S(2)), x), x, -x**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) - S(5)*sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(16)*b**S(4)) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(4)) + x*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(4)*Erfc(b*x)*exp(-b**S(2)*x**S(2)), x), x, -S(3)*sqrt(Pi)*Erfc(b*x)**S(2)/(S(16)*b**S(5)) - x**S(3)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) - S(3)*x*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*b**S(4)) + x**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)) + exp(-S(2)*b**S(2)*x**S(2))/(S(2)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(5)*Erfc(b*x)*exp(-b**S(2)*x**S(2)), x), x, -x**S(4)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) - x**S(2)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/b**S(4) - S(43)*sqrt(S(2))*Erf(sqrt(S(2))*b*x)/(S(64)*b**S(6)) - Erfc(b*x)*exp(-b**S(2)*x**S(2))/b**S(6) + x**S(3)*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)) + S(11)*x*exp(-S(2)*b**S(2)*x**S(2))/(S(16)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(6)*Erfc(b*x)*exp(-b**S(2)*x**S(2)), x), x, -S(15)*sqrt(Pi)*Erfc(b*x)**S(2)/(S(32)*b**S(7)) - x**S(5)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(2)*b**S(2)) - S(5)*x**S(3)*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(4)*b**S(4)) - S(15)*x*Erfc(b*x)*exp(-b**S(2)*x**S(2))/(S(8)*b**S(6)) + x**S(4)*exp(-S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)) + S(7)*x**S(2)*exp(-S(2)*b**S(2)*x**S(2))/(S(8)*sqrt(Pi)*b**S(5)) + S(11)*exp(-S(2)*b**S(2)*x**S(2))/(S(8)*sqrt(Pi)*b**S(7)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)**S(2)/x**S(8), x), x, Integrate(Erfi(b*x)**S(2)/x**S(8), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)**S(2)/x**S(7), x), x, S(4)*b**S(6)*Erfi(b*x)**S(2)/S(45) - Erfi(b*x)**S(2)/(S(6)*x**S(6)) + S(28)*b**S(6)*ExpIntegralEi(S(2)*b**S(2)*x**S(2))/(S(45)*Pi) - S(2)*b**S(4)*exp(S(2)*b**S(2)*x**S(2))/(S(9)*Pi*x**S(2)) - b**S(2)*exp(S(2)*b**S(2)*x**S(2))/(S(15)*Pi*x**S(4)) - S(8)*b**S(5)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(45)*sqrt(Pi)*x) - S(4)*b**S(3)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(45)*sqrt(Pi)*x**S(3)) - S(2)*b*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(15)*sqrt(Pi)*x**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)**S(2)/x**S(6), x), x, Integrate(Erfi(b*x)**S(2)/x**S(6), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)**S(2)/x**S(5), x), x, b**S(4)*Erfi(b*x)**S(2)/S(3) - Erfi(b*x)**S(2)/(S(4)*x**S(4)) + S(4)*b**S(4)*ExpIntegralEi(S(2)*b**S(2)*x**S(2))/(S(3)*Pi) - b**S(2)*exp(S(2)*b**S(2)*x**S(2))/(S(3)*Pi*x**S(2)) - S(2)*b**S(3)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x) - b*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)**S(2)/x**S(4), x), x, Integrate(Erfi(b*x)**S(2)/x**S(4), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)**S(2)/x**S(3), x), x, b**S(2)*Erfi(b*x)**S(2) - Erfi(b*x)**S(2)/(S(2)*x**S(2)) + S(2)*b**S(2)*ExpIntegralEi(S(2)*b**S(2)*x**S(2))/Pi - S(2)*b*Erfi(b*x)*exp(b**S(2)*x**S(2))/(sqrt(Pi)*x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)**S(2)/x**S(2), x), x, Integrate(Erfi(b*x)**S(2)/x**S(2), x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)**S(2)/x, x), x, Integrate(Erfi(b*x)**S(2)/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)**S(2), x), x, x*Erfi(b*x)**S(2) + sqrt(S(2))*sqrt(S(1)/Pi)*Erfi(sqrt(S(2))*b*x)/b - S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erfi(b*x)**S(2), x), x, x**S(2)*Erfi(b*x)**S(2)/S(2) + Erfi(b*x)**S(2)/(S(4)*b**S(2)) + exp(S(2)*b**S(2)*x**S(2))/(S(2)*Pi*b**S(2)) - x*Erfi(b*x)*exp(b**S(2)*x**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erfi(b*x)**S(2), x), x, x**S(3)*Erfi(b*x)**S(2)/S(3) + x*exp(S(2)*b**S(2)*x**S(2))/(S(3)*Pi*b**S(2)) - S(2)*x**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*b) + S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*b**S(3)) - S(5)*sqrt(S(2))*Erfi(sqrt(S(2))*b*x)/(S(12)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(3)*Erfi(b*x)**S(2), x), x, x**S(4)*Erfi(b*x)**S(2)/S(4) - S(3)*Erfi(b*x)**S(2)/(S(16)*b**S(4)) + x**S(2)*exp(S(2)*b**S(2)*x**S(2))/(S(4)*Pi*b**S(2)) - exp(S(2)*b**S(2)*x**S(2))/(S(2)*Pi*b**S(4)) - x**S(3)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(2)*sqrt(Pi)*b) + S(3)*x*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(4)*Erfi(b*x)**S(2), x), x, x**S(5)*Erfi(b*x)**S(2)/S(5) + x**S(3)*exp(S(2)*b**S(2)*x**S(2))/(S(5)*Pi*b**S(2)) - S(11)*x*exp(S(2)*b**S(2)*x**S(2))/(S(20)*Pi*b**S(4)) - S(2)*x**S(4)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(5)*sqrt(Pi)*b) + S(4)*x**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(5)*sqrt(Pi)*b**S(3)) - S(4)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(5)*sqrt(Pi)*b**S(5)) + S(43)*sqrt(S(2))*Erfi(sqrt(S(2))*b*x)/(S(80)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(5)*Erfi(b*x)**S(2), x), x, x**S(6)*Erfi(b*x)**S(2)/S(6) + S(5)*Erfi(b*x)**S(2)/(S(16)*b**S(6)) + x**S(4)*exp(S(2)*b**S(2)*x**S(2))/(S(6)*Pi*b**S(2)) - S(7)*x**S(2)*exp(S(2)*b**S(2)*x**S(2))/(S(12)*Pi*b**S(4)) + S(11)*exp(S(2)*b**S(2)*x**S(2))/(S(12)*Pi*b**S(6)) - x**S(5)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*b) + S(5)*x**S(3)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(6)*sqrt(Pi)*b**S(3)) - S(5)*x*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(a + b*x)/x, x), x, Integrate(Erfi(a + b*x)/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(a + b*x), x), x, (a + b*x)*Erfi(a + b*x)/b - exp((a + b*x)**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erfi(a + b*x), x), x, -a**S(2)*Erfi(a + b*x)/(S(2)*b**S(2)) + x**S(2)*Erfi(a + b*x)/S(2) + Erfi(a + b*x)/(S(4)*b**S(2)) + a*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(2)) - (a + b*x)*exp((a + b*x)**S(2))/(S(2)*sqrt(Pi)*b**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erfi(a + b*x), x), x, a**S(3)*Erfi(a + b*x)/(S(3)*b**S(3)) - a*Erfi(a + b*x)/(S(2)*b**S(3)) + x**S(3)*Erfi(a + b*x)/S(3) - a**S(2)*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) + a*(a + b*x)*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) - (a + b*x)**S(2)*exp((a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)) + exp((a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(3)*Erfi(a + b*x), x), x, -a**S(4)*Erfi(a + b*x)/(S(4)*b**S(4)) + S(3)*a**S(2)*Erfi(a + b*x)/(S(4)*b**S(4)) + x**S(4)*Erfi(a + b*x)/S(4) - S(3)*Erfi(a + b*x)/(S(16)*b**S(4)) + a**S(3)*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(4)) - S(3)*a**S(2)*(a + b*x)*exp((a + b*x)**S(2))/(S(2)*sqrt(Pi)*b**S(4)) + a*(a + b*x)**S(2)*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(4)) - a*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(4)) - (a + b*x)**S(3)*exp((a + b*x)**S(2))/(S(4)*sqrt(Pi)*b**S(4)) + S(3)*(a + b*x)*exp((a + b*x)**S(2))/(S(8)*sqrt(Pi)*b**S(4)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(a + b*x)**S(2)/x, x), x, Integrate(Erfi(a + b*x)**S(2)/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(a + b*x)**S(2), x), x, (a + b*x)*Erfi(a + b*x)**S(2)/b + sqrt(S(2))*sqrt(S(1)/Pi)*Erfi(sqrt(S(2))*(a + b*x))/b - S(2)*Erfi(a + b*x)*exp((a + b*x)**S(2))/(sqrt(Pi)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erfi(a + b*x)**S(2), x), x, -a*(a + b*x)*Erfi(a + b*x)**S(2)/b**S(2) - sqrt(S(2))*a*sqrt(S(1)/Pi)*Erfi(sqrt(S(2))*(a + b*x))/b**S(2) + (a + b*x)**S(2)*Erfi(a + b*x)**S(2)/(S(2)*b**S(2)) + Erfi(a + b*x)**S(2)/(S(4)*b**S(2)) + exp(S(2)*(a + b*x)**S(2))/(S(2)*Pi*b**S(2)) + S(2)*a*Erfi(a + b*x)*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(2)) - (a + b*x)*Erfi(a + b*x)*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erfi(a + b*x)**S(2), x), x, a**S(2)*(a + b*x)*Erfi(a + b*x)**S(2)/b**S(3) + sqrt(S(2))*a**S(2)*sqrt(S(1)/Pi)*Erfi(sqrt(S(2))*(a + b*x))/b**S(3) - a*(a + b*x)**S(2)*Erfi(a + b*x)**S(2)/b**S(3) - a*Erfi(a + b*x)**S(2)/(S(2)*b**S(3)) + (a + b*x)**S(3)*Erfi(a + b*x)**S(2)/(S(3)*b**S(3)) - a*exp(S(2)*(a + b*x)**S(2))/(Pi*b**S(3)) + (a + b*x)*exp(S(2)*(a + b*x)**S(2))/(S(3)*Pi*b**S(3)) - S(2)*a**S(2)*Erfi(a + b*x)*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) + S(2)*a*(a + b*x)*Erfi(a + b*x)*exp((a + b*x)**S(2))/(sqrt(Pi)*b**S(3)) - S(2)*(a + b*x)**S(2)*Erfi(a + b*x)*exp((a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)) - S(5)*sqrt(S(2))*Erfi(sqrt(S(2))*(a + b*x))/(S(12)*sqrt(Pi)*b**S(3)) + S(2)*Erfi(a + b*x)*exp((a + b*x)**S(2))/(S(3)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x**S(8), x), x, S(4)*sqrt(Pi)*b**S(7)*Erfi(b*x)**S(2)/S(105) - S(8)*b**S(6)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(105)*x) - S(4)*b**S(4)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(105)*x**S(3)) - S(2)*b**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(35)*x**S(5)) - Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(7)*x**S(7)) + S(16)*b**S(7)*ExpIntegralEi(S(2)*b**S(2)*x**S(2))/(S(35)*sqrt(Pi)) - S(4)*b**S(5)*exp(S(2)*b**S(2)*x**S(2))/(S(21)*sqrt(Pi)*x**S(2)) - S(8)*b**S(3)*exp(S(2)*b**S(2)*x**S(2))/(S(105)*sqrt(Pi)*x**S(4)) - b*exp(S(2)*b**S(2)*x**S(2))/(S(21)*sqrt(Pi)*x**S(6)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x**S(7), x), x, S(67)*sqrt(S(2))*b**S(6)*Erfi(sqrt(S(2))*b*x)/S(90) + b**S(6)*Integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x, x)/S(6) - b**S(4)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(12)*x**S(2)) - b**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(12)*x**S(4)) - Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(6)*x**S(6)) - S(67)*b**S(5)*exp(S(2)*b**S(2)*x**S(2))/(S(90)*sqrt(Pi)*x) - S(13)*b**S(3)*exp(S(2)*b**S(2)*x**S(2))/(S(90)*sqrt(Pi)*x**S(3)) - b*exp(S(2)*b**S(2)*x**S(2))/(S(15)*sqrt(Pi)*x**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x**S(6), x), x, S(2)*sqrt(Pi)*b**S(5)*Erfi(b*x)**S(2)/S(15) - S(4)*b**S(4)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(15)*x) - S(2)*b**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(15)*x**S(3)) - Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(5)*x**S(5)) + S(14)*b**S(5)*ExpIntegralEi(S(2)*b**S(2)*x**S(2))/(S(15)*sqrt(Pi)) - b**S(3)*exp(S(2)*b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x**S(2)) - b*exp(S(2)*b**S(2)*x**S(2))/(S(10)*sqrt(Pi)*x**S(4)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x**S(5), x), x, S(7)*sqrt(S(2))*b**S(4)*Erfi(sqrt(S(2))*b*x)/S(6) + b**S(4)*Integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x, x)/S(2) - b**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(4)*x**S(2)) - Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(4)*x**S(4)) - S(7)*b**S(3)*exp(S(2)*b**S(2)*x**S(2))/(S(6)*sqrt(Pi)*x) - b*exp(S(2)*b**S(2)*x**S(2))/(S(6)*sqrt(Pi)*x**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x**S(4), x), x, sqrt(Pi)*b**S(3)*Erfi(b*x)**S(2)/S(3) - S(2)*b**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(3)*x) - Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(3)*x**S(3)) + S(4)*b**S(3)*ExpIntegralEi(S(2)*b**S(2)*x**S(2))/(S(3)*sqrt(Pi)) - b*exp(S(2)*b**S(2)*x**S(2))/(S(3)*sqrt(Pi)*x**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x**S(3), x), x, sqrt(S(2))*b**S(2)*Erfi(sqrt(S(2))*b*x) + b**S(2)*Integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x, x) - Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(2)*x**S(2)) - b*exp(S(2)*b**S(2)*x**S(2))/(sqrt(Pi)*x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x**S(2), x), x, sqrt(Pi)*b*Erfi(b*x)**S(2)/S(2) - Erfi(b*x)*exp(b**S(2)*x**S(2))/x + b*ExpIntegralEi(S(2)*b**S(2)*x**S(2))/sqrt(Pi), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x, x), x, Integrate(Erfi(b*x)*exp(b**S(2)*x**S(2))/x, x), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(Erfi(b*x)*exp(b**S(2)*x**S(2)), x), x, sqrt(Pi)*Erfi(b*x)**S(2)/(S(4)*b), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x*Erfi(b*x)*exp(b**S(2)*x**S(2)), x), x, Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(2)*b**S(2)) - sqrt(S(2))*Erfi(sqrt(S(2))*b*x)/(S(4)*b**S(2)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2)), x), x, -sqrt(Pi)*Erfi(b*x)**S(2)/(S(8)*b**S(3)) + x*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(2)*b**S(2)) - exp(S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(3)*Erfi(b*x)*exp(b**S(2)*x**S(2)), x), x, x**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(2)*b**S(2)) - Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(2)*b**S(4)) + S(5)*sqrt(S(2))*Erfi(sqrt(S(2))*b*x)/(S(16)*b**S(4)) - x*exp(S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(4)*Erfi(b*x)*exp(b**S(2)*x**S(2)), x), x, S(3)*sqrt(Pi)*Erfi(b*x)**S(2)/(S(16)*b**S(5)) + x**S(3)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(2)*b**S(2)) - S(3)*x*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(4)*b**S(4)) - x**S(2)*exp(S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)) + exp(S(2)*b**S(2)*x**S(2))/(S(2)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(5)*Erfi(b*x)*exp(b**S(2)*x**S(2)), x), x, x**S(4)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(2)*b**S(2)) - x**S(2)*Erfi(b*x)*exp(b**S(2)*x**S(2))/b**S(4) + Erfi(b*x)*exp(b**S(2)*x**S(2))/b**S(6) - S(43)*sqrt(S(2))*Erfi(sqrt(S(2))*b*x)/(S(64)*b**S(6)) - x**S(3)*exp(S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)) + S(11)*x*exp(S(2)*b**S(2)*x**S(2))/(S(16)*sqrt(Pi)*b**S(5)), expand=True, _diff=True, _numerical=True)
    assert rubi_test(rubi_integrate(x**S(6)*Erfi(b*x)*exp(b**S(2)*x**S(2)), x), x, -S(15)*sqrt(Pi)*Erfi(b*x)**S(2)/(S(32)*b**S(7)) + x**S(5)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(2)*b**S(2)) - S(5)*x**S(3)*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(4)*b**S(4)) + S(15)*x*Erfi(b*x)*exp(b**S(2)*x**S(2))/(S(8)*b**S(6)) - x**S(4)*exp(S(2)*b**S(2)*x**S(2))/(S(4)*sqrt(Pi)*b**S(3)) + S(7)*x**S(2)*exp(S(2)*b**S(2)*x**S(2))/(S(8)*sqrt(Pi)*b**S(5)) - S(11)*exp(S(2)*b**S(2)*x**S(2))/(S(8)*sqrt(Pi)*b**S(7)), expand=True, _diff=True, _numerical=True)
