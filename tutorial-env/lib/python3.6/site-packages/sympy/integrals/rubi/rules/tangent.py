'''
This code is automatically generated. Never edit it manually.
For details of generating the code see `rubi_parsing_guide.md` in `parsetools`.
'''

from sympy.external import import_module
matchpy = import_module("matchpy")
from sympy.utilities.decorator import doctest_depends_on

if matchpy:
    from matchpy import Pattern, ReplacementRule, CustomConstraint, is_match
    from sympy.integrals.rubi.utility_function import (
        Int, Sum, Set, With, Module, Scan, MapAnd, FalseQ,
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
        Zeta, ProductLog, DerivativeDivides, HypergeometricPFQ, IntHide, OneQ, Null, rubi_exp as exp, rubi_log as log, Discriminant,
        Negative, Quotient
    )
    from sympy import (Integral, S, sqrt, And, Or, Integer, Float, Mod, I, Abs, simplify, Mul,
    Add, Pow, sign, EulerGamma)
    from sympy.integrals.rubi.symbol import WC
    from sympy.core.symbol import symbols, Symbol
    from sympy.functions import (sin, cos, tan, cot, csc, sec, sqrt, erf)
    from sympy.functions.elementary.hyperbolic import (acosh, asinh, atanh, acoth, acsch, asech, cosh, sinh, tanh, coth, sech, csch)
    from sympy.functions.elementary.trigonometric import (atan, acsc, asin, acot, acos, asec, atan2)
    from sympy import pi as Pi


    A_, B_, C_, F_, G_, H_, a_, b_, c_, d_, e_, f_, g_, h_, i_, j_, k_, l_, m_, n_, p_, q_, r_, t_, u_, v_, s_, w_, x_, y_, z_ = [WC(i) for i in 'ABCFGHabcdefghijklmnpqrtuvswxyz']
    a1_, a2_, b1_, b2_, c1_, c2_, d1_, d2_, n1_, n2_, e1_, e2_, f1_, f2_, g1_, g2_, n1_, n2_, n3_, Pq_, Pm_, Px_, Qm_, Qr_, Qx_, jn_, mn_, non2_, RFx_, RGx_ = [WC(i) for i in ['a1', 'a2', 'b1', 'b2', 'c1', 'c2', 'd1', 'd2', 'n1', 'n2', 'e1', 'e2', 'f1', 'f2', 'g1', 'g2', 'n1', 'n2', 'n3', 'Pq', 'Pm', 'Px', 'Qm', 'Qr', 'Qx', 'jn', 'mn', 'non2', 'RFx', 'RGx']]
    i, ii , Pqq, Q, R, r, C, k, u = symbols('i ii Pqq Q R r C k u')
    _UseGamma = False
    ShowSteps = False
    StepCounter = None

def tangent(rubi):
    from sympy.integrals.rubi.constraints import cons1508, cons2, cons3, cons48, cons125, cons21, cons4, cons1509, cons17, cons23, cons93, cons165, cons94, cons1510, cons1170, cons87, cons1511, cons89, cons166, cons683, cons31, cons266, cons32, cons1512, cons1513, cons18, cons155, cons1250, cons1514, cons1515, cons1516, cons1517, cons1518, cons1519, cons1520, cons1521, cons1522, cons80, cons79, cons1523, cons1524, cons1525, cons1526, cons27, cons5, cons1527, cons7, cons1261, cons1264, cons1439, cons463, cons1440, cons1528, cons1255, cons1529, cons88, cons1530, cons1531, cons1532, cons515, cons1533, cons1534, cons1535, cons1536, cons1537, cons1538, cons66, cons1539, cons84, cons1228, cons148, cons196, cons1540, cons85, cons70, cons1541, cons71, cons1412, cons267, cons1303, cons168, cons1542, cons1543, cons1322, cons1544, cons1323, cons1545, cons1546, cons1547, cons1548, cons77, cons1549, cons1550, cons1551, cons1423, cons1385, cons111, cons272, cons1325, cons1327, cons1334, cons1552, cons1553, cons1333, cons1554, cons1555, cons1336, cons1556, cons1557, cons808, cons380, cons208, cons147, cons1417, cons50, cons38, cons34, cons35, cons346, cons1418, cons1426, cons1558, cons1559, cons1560, cons1256, cons1561, cons36, cons33, cons1433, cons1562, cons1563, cons1564, cons1565, cons1566, cons1567, cons1568, cons1569, cons1492, cons1456, cons1570, cons1481, cons1479, cons743, cons1497, cons46, cons45, cons226, cons1480, cons62, cons528, cons1571, cons1572, cons810, cons811, cons1360, cons1573, cons1495, cons68, cons69, cons823, cons824, cons1574, cons1575, cons1576, cons1577, cons1578, cons1579, cons47, cons239, cons1580

    pattern3398 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1508)
    def replacement3398(m, f, b, a, n, x, e):
        rubi.append(3398)
        return -Simp(b*(a*sin(e + f*x))**m*(b*tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3398 = ReplacementRule(pattern3398, replacement3398)
    pattern3399 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1508)
    def replacement3399(m, f, b, a, n, x, e):
        rubi.append(3399)
        return Simp(b*(a*cos(e + f*x))**m*(b/tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3399 = ReplacementRule(pattern3399, replacement3399)
    pattern3400 = Pattern(Integral(sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**WC('n', S(1)), x_), cons48, cons125, cons1509)
    def replacement3400(m, f, n, x, e):
        rubi.append(3400)
        return -Dist(S(1)/f, Subst(Int(x**(-n)*(-x**S(2) + S(1))**(m/S(2) + n/S(2) + S(-1)/2), x), x, cos(e + f*x)), x)
    rule3400 = ReplacementRule(pattern3400, replacement3400)
    pattern3401 = Pattern(Integral((S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons48, cons125, cons1509)
    def replacement3401(m, f, n, x, e):
        rubi.append(3401)
        return Dist(S(1)/f, Subst(Int(x**(-n)*(-x**S(2) + S(1))**(m/S(2) + n/S(2) + S(-1)/2), x), x, sin(e + f*x)), x)
    rule3401 = ReplacementRule(pattern3401, replacement3401)
    pattern3402 = Pattern(Integral((WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons3, cons48, cons125, cons4, cons17, cons23)
    def replacement3402(m, f, b, n, x, e):
        rubi.append(3402)
        return Dist(b**(-m), Int((b*tan(e + f*x))**(m + n)*(S(1)/cos(e + f*x))**(-m), x), x)
    rule3402 = ReplacementRule(pattern3402, replacement3402)
    pattern3403 = Pattern(Integral((WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons3, cons48, cons125, cons4, cons17, cons23)
    def replacement3403(m, f, b, n, x, e):
        rubi.append(3403)
        return Dist(b**(-m), Int((b/tan(e + f*x))**(m + n)*(S(1)/sin(e + f*x))**(-m), x), x)
    rule3403 = ReplacementRule(pattern3403, replacement3403)
    pattern3404 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons165, cons94, cons1510, cons1170)
    def replacement3404(m, f, b, a, n, x, e):
        rubi.append(3404)
        return -Dist(b**S(2)*(m + S(2))/(a**S(2)*(n + S(-1))), Int((a*sin(e + f*x))**(m + S(2))*(b*tan(e + f*x))**(n + S(-2)), x), x) + Simp(b*(a*sin(e + f*x))**(m + S(2))*(b*tan(e + f*x))**(n + S(-1))/(a**S(2)*f*(n + S(-1))), x)
    rule3404 = ReplacementRule(pattern3404, replacement3404)
    pattern3405 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons165, cons94, cons1510, cons1170)
    def replacement3405(m, f, b, a, n, x, e):
        rubi.append(3405)
        return -Dist(b**S(2)*(m + S(2))/(a**S(2)*(n + S(-1))), Int((a*cos(e + f*x))**(m + S(2))*(b/tan(e + f*x))**(n + S(-2)), x), x) - Simp(b*(a*cos(e + f*x))**(m + S(2))*(b/tan(e + f*x))**(n + S(-1))/(a**S(2)*f*(n + S(-1))), x)
    rule3405 = ReplacementRule(pattern3405, replacement3405)
    pattern3406 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons165, cons1170, cons1511)
    def replacement3406(m, f, b, a, n, x, e):
        rubi.append(3406)
        return -Dist(b**S(2)*(m + n + S(-1))/(n + S(-1)), Int((a*sin(e + f*x))**m*(b*tan(e + f*x))**(n + S(-2)), x), x) + Simp(b*(a*sin(e + f*x))**m*(b*tan(e + f*x))**(n + S(-1))/(f*(n + S(-1))), x)
    rule3406 = ReplacementRule(pattern3406, replacement3406)
    pattern3407 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons165, cons1170, cons1511)
    def replacement3407(m, f, b, a, n, x, e):
        rubi.append(3407)
        return -Dist(b**S(2)*(m + n + S(-1))/(n + S(-1)), Int((a*cos(e + f*x))**m*(b/tan(e + f*x))**(n + S(-2)), x), x) - Simp(b*(a*cos(e + f*x))**m*(b/tan(e + f*x))**(n + S(-1))/(f*(n + S(-1))), x)
    rule3407 = ReplacementRule(pattern3407, replacement3407)
    pattern3408 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons89, cons166, cons1170)
    def replacement3408(m, f, b, a, n, x, e):
        rubi.append(3408)
        return -Dist(a**S(2)*(n + S(1))/(b**S(2)*m), Int((a*sin(e + f*x))**(m + S(-2))*(b*tan(e + f*x))**(n + S(2)), x), x) + Simp((a*sin(e + f*x))**m*(b*tan(e + f*x))**(n + S(1))/(b*f*m), x)
    rule3408 = ReplacementRule(pattern3408, replacement3408)
    pattern3409 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons89, cons166, cons1170)
    def replacement3409(m, f, b, a, n, x, e):
        rubi.append(3409)
        return -Dist(a**S(2)*(n + S(1))/(b**S(2)*m), Int((a*cos(e + f*x))**(m + S(-2))*(b/tan(e + f*x))**(n + S(2)), x), x) - Simp((a*cos(e + f*x))**m*(b/tan(e + f*x))**(n + S(1))/(b*f*m), x)
    rule3409 = ReplacementRule(pattern3409, replacement3409)
    pattern3410 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons89, cons683, cons1170)
    def replacement3410(m, f, b, a, n, x, e):
        rubi.append(3410)
        return -Dist((n + S(1))/(b**S(2)*(m + n + S(1))), Int((a*sin(e + f*x))**m*(b*tan(e + f*x))**(n + S(2)), x), x) + Simp((a*sin(e + f*x))**m*(b*tan(e + f*x))**(n + S(1))/(b*f*(m + n + S(1))), x)
    rule3410 = ReplacementRule(pattern3410, replacement3410)
    pattern3411 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons89, cons683, cons1170)
    def replacement3411(m, f, b, a, n, x, e):
        rubi.append(3411)
        return -Dist((n + S(1))/(b**S(2)*(m + n + S(1))), Int((a*cos(e + f*x))**m*(b/tan(e + f*x))**(n + S(2)), x), x) - Simp((a*cos(e + f*x))**m*(b/tan(e + f*x))**(n + S(1))/(b*f*(m + n + S(1))), x)
    rule3411 = ReplacementRule(pattern3411, replacement3411)
    pattern3412 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons4, cons31, cons266, cons1170)
    def replacement3412(m, f, b, a, n, x, e):
        rubi.append(3412)
        return Dist(a**S(2)*(m + n + S(-1))/m, Int((a*sin(e + f*x))**(m + S(-2))*(b*tan(e + f*x))**n, x), x) - Simp(b*(a*sin(e + f*x))**m*(b*tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3412 = ReplacementRule(pattern3412, replacement3412)
    pattern3413 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons4, cons31, cons266, cons1170)
    def replacement3413(m, f, b, a, n, x, e):
        rubi.append(3413)
        return Dist(a**S(2)*(m + n + S(-1))/m, Int((a*cos(e + f*x))**(m + S(-2))*(b/tan(e + f*x))**n, x), x) + Simp(b*(a*cos(e + f*x))**m*(b/tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3413 = ReplacementRule(pattern3413, replacement3413)
    pattern3414 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons4, cons31, cons32, cons683, cons1170)
    def replacement3414(m, f, b, a, n, x, e):
        rubi.append(3414)
        return Dist((m + S(2))/(a**S(2)*(m + n + S(1))), Int((a*sin(e + f*x))**(m + S(2))*(b*tan(e + f*x))**n, x), x) + Simp(b*(a*sin(e + f*x))**(m + S(2))*(b*tan(e + f*x))**(n + S(-1))/(a**S(2)*f*(m + n + S(1))), x)
    rule3414 = ReplacementRule(pattern3414, replacement3414)
    pattern3415 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons4, cons31, cons32, cons683, cons1170)
    def replacement3415(m, f, b, a, n, x, e):
        rubi.append(3415)
        return Dist((m + S(2))/(a**S(2)*(m + n + S(1))), Int((a*cos(e + f*x))**(m + S(2))*(b/tan(e + f*x))**n, x), x) - Simp(b*(a*cos(e + f*x))**(m + S(2))*(b/tan(e + f*x))**(n + S(-1))/(a**S(2)*f*(m + n + S(1))), x)
    rule3415 = ReplacementRule(pattern3415, replacement3415)
    pattern3416 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**WC('n', S(1)), x_), cons2, cons48, cons125, cons21, cons1512)
    def replacement3416(m, f, a, n, x, e):
        rubi.append(3416)
        return Dist(S(1)/f, Subst(Int(x**(m + n)*(a**S(2) - x**S(2))**(-n/S(2) + S(-1)/2), x), x, a*sin(e + f*x)), x)
    rule3416 = ReplacementRule(pattern3416, replacement3416)
    pattern3417 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons48, cons125, cons21, cons1512)
    def replacement3417(m, f, a, n, x, e):
        rubi.append(3417)
        return -Dist(S(1)/f, Subst(Int(x**(m + n)*(a**S(2) - x**S(2))**(-n/S(2) + S(-1)/2), x), x, a*cos(e + f*x)), x)
    rule3417 = ReplacementRule(pattern3417, replacement3417)
    pattern3418 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1513)
    def replacement3418(m, f, b, a, n, x, e):
        rubi.append(3418)
        return Dist(a**(-S(2)*IntPart(n/S(2) + S(1)/2) + S(1))*b**(S(2)*IntPart(n/S(2) + S(1)/2) + S(-1))*(a*sin(e + f*x))**(-S(2)*FracPart(n/S(2) + S(1)/2))*(b*tan(e + f*x))**(S(2)*FracPart(n/S(2) + S(1)/2))*(cos(e + f*x)**S(2))**FracPart(n/S(2) + S(1)/2)/f, Subst(Int((a*x)**(m + n)*(-x**S(2) + S(1))**(-n/S(2) + S(-1)/2), x), x, sin(e + f*x)), x)
    rule3418 = ReplacementRule(pattern3418, replacement3418)
    pattern3419 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1513)
    def replacement3419(m, f, b, a, n, x, e):
        rubi.append(3419)
        return -Dist(a**(-S(2)*IntPart(n/S(2) + S(1)/2) + S(1))*b**(S(2)*IntPart(n/S(2) + S(1)/2) + S(-1))*(a*cos(e + f*x))**(-S(2)*FracPart(n/S(2) + S(1)/2))*(b/tan(e + f*x))**(S(2)*FracPart(n/S(2) + S(1)/2))*(sin(e + f*x)**S(2))**FracPart(n/S(2) + S(1)/2)/f, Subst(Int((a*x)**(m + n)*(-x**S(2) + S(1))**(-n/S(2) + S(-1)/2), x), x, cos(e + f*x)), x)
    rule3419 = ReplacementRule(pattern3419, replacement3419)
    pattern3420 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons18, cons23)
    def replacement3420(m, f, b, a, n, x, e):
        rubi.append(3420)
        return Dist((S(1)/(a*cos(e + f*x)))**FracPart(m)*(a*cos(e + f*x))**FracPart(m), Int((S(1)/(a*cos(e + f*x)))**(-m)*(b*tan(e + f*x))**n, x), x)
    rule3420 = ReplacementRule(pattern3420, replacement3420)
    pattern3421 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons18, cons23)
    def replacement3421(m, f, b, a, n, x, e):
        rubi.append(3421)
        return Dist((S(1)/(a*sin(e + f*x)))**FracPart(m)*(a*sin(e + f*x))**FracPart(m), Int((S(1)/(a*sin(e + f*x)))**(-m)*(b/tan(e + f*x))**n, x), x)
    rule3421 = ReplacementRule(pattern3421, replacement3421)
    pattern3422 = Pattern(Integral((WC('a', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons18, cons23)
    def replacement3422(m, f, b, a, n, x, e):
        rubi.append(3422)
        return Dist((a/tan(e + f*x))**m*(b*tan(e + f*x))**m, Int((b*tan(e + f*x))**(-m + n), x), x)
    rule3422 = ReplacementRule(pattern3422, replacement3422)
    pattern3423 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons4, cons155)
    def replacement3423(m, f, b, a, n, x, e):
        rubi.append(3423)
        return -Simp((a/cos(e + f*x))**m*(b*tan(e + f*x))**(n + S(1))/(b*f*m), x)
    rule3423 = ReplacementRule(pattern3423, replacement3423)
    pattern3424 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons4, cons155)
    def replacement3424(m, f, b, a, n, x, e):
        rubi.append(3424)
        return Simp((a/sin(e + f*x))**m*(b/tan(e + f*x))**(n + S(1))/(b*f*m), x)
    rule3424 = ReplacementRule(pattern3424, replacement3424)
    pattern3425 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons48, cons125, cons21, cons1250, cons1514)
    def replacement3425(m, f, b, a, n, x, e):
        rubi.append(3425)
        return Dist(a/f, Subst(Int((a*x)**(m + S(-1))*(x**S(2) + S(-1))**(n/S(2) + S(-1)/2), x), x, S(1)/cos(e + f*x)), x)
    rule3425 = ReplacementRule(pattern3425, replacement3425)
    pattern3426 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons48, cons125, cons21, cons1250, cons1514)
    def replacement3426(m, f, b, a, n, x, e):
        rubi.append(3426)
        return -Dist(a/f, Subst(Int((a*x)**(m + S(-1))*(x**S(2) + S(-1))**(n/S(2) + S(-1)/2), x), x, S(1)/sin(e + f*x)), x)
    rule3426 = ReplacementRule(pattern3426, replacement3426)
    pattern3427 = Pattern(Integral((WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(S(1)/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons3, cons48, cons125, cons4, cons1515, cons1516)
    def replacement3427(m, f, b, n, x, e):
        rubi.append(3427)
        return Dist(S(1)/f, Subst(Int((b*x)**n*(x**S(2) + S(1))**(m/S(2) + S(-1)), x), x, tan(e + f*x)), x)
    rule3427 = ReplacementRule(pattern3427, replacement3427)
    pattern3428 = Pattern(Integral((WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(S(1)/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons3, cons48, cons125, cons4, cons1515, cons1516)
    def replacement3428(m, f, b, n, x, e):
        rubi.append(3428)
        return -Dist(S(1)/f, Subst(Int((b*x)**n*(x**S(2) + S(1))**(m/S(2) + S(-1)), x), x, S(1)/tan(e + f*x)), x)
    rule3428 = ReplacementRule(pattern3428, replacement3428)
    pattern3429 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons89, cons1517, cons1170)
    def replacement3429(m, f, b, a, n, x, e):
        rubi.append(3429)
        return -Dist(a**S(2)*(m + S(-2))/(b**S(2)*(n + S(1))), Int((a/cos(e + f*x))**(m + S(-2))*(b*tan(e + f*x))**(n + S(2)), x), x) + Simp(a**S(2)*(a/cos(e + f*x))**(m + S(-2))*(b*tan(e + f*x))**(n + S(1))/(b*f*(n + S(1))), x)
    rule3429 = ReplacementRule(pattern3429, replacement3429)
    pattern3430 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons89, cons1517, cons1170)
    def replacement3430(m, f, b, a, n, x, e):
        rubi.append(3430)
        return -Dist(a**S(2)*(m + S(-2))/(b**S(2)*(n + S(1))), Int((a/sin(e + f*x))**(m + S(-2))*(b/tan(e + f*x))**(n + S(2)), x), x) - Simp(a**S(2)*(a/sin(e + f*x))**(m + S(-2))*(b/tan(e + f*x))**(n + S(1))/(b*f*(n + S(1))), x)
    rule3430 = ReplacementRule(pattern3430, replacement3430)
    pattern3431 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons89, cons1170)
    def replacement3431(m, f, b, a, n, x, e):
        rubi.append(3431)
        return -Dist((m + n + S(1))/(b**S(2)*(n + S(1))), Int((a/cos(e + f*x))**m*(b*tan(e + f*x))**(n + S(2)), x), x) + Simp((a/cos(e + f*x))**m*(b*tan(e + f*x))**(n + S(1))/(b*f*(n + S(1))), x)
    rule3431 = ReplacementRule(pattern3431, replacement3431)
    pattern3432 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons89, cons1170)
    def replacement3432(m, f, b, a, n, x, e):
        rubi.append(3432)
        return -Dist((m + n + S(1))/(b**S(2)*(n + S(1))), Int((a/sin(e + f*x))**m*(b/tan(e + f*x))**(n + S(2)), x), x) - Simp((a/sin(e + f*x))**m*(b/tan(e + f*x))**(n + S(1))/(b*f*(n + S(1))), x)
    rule3432 = ReplacementRule(pattern3432, replacement3432)
    pattern3433 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons165, cons1518, cons1170)
    def replacement3433(m, f, b, a, n, x, e):
        rubi.append(3433)
        return -Dist(b**S(2)*(n + S(-1))/(a**S(2)*m), Int((a/cos(e + f*x))**(m + S(2))*(b*tan(e + f*x))**(n + S(-2)), x), x) + Simp(b*(a/cos(e + f*x))**m*(b*tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3433 = ReplacementRule(pattern3433, replacement3433)
    pattern3434 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons165, cons1518, cons1170)
    def replacement3434(m, f, b, a, n, x, e):
        rubi.append(3434)
        return -Dist(b**S(2)*(n + S(-1))/(a**S(2)*m), Int((a/sin(e + f*x))**(m + S(2))*(b/tan(e + f*x))**(n + S(-2)), x), x) - Simp(b*(a/sin(e + f*x))**m*(b/tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3434 = ReplacementRule(pattern3434, replacement3434)
    pattern3435 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons165, cons1519, cons1170)
    def replacement3435(m, f, b, a, n, x, e):
        rubi.append(3435)
        return -Dist(b**S(2)*(n + S(-1))/(m + n + S(-1)), Int((a/cos(e + f*x))**m*(b*tan(e + f*x))**(n + S(-2)), x), x) + Simp(b*(a/cos(e + f*x))**m*(b*tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3435 = ReplacementRule(pattern3435, replacement3435)
    pattern3436 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons165, cons1519, cons1170)
    def replacement3436(m, f, b, a, n, x, e):
        rubi.append(3436)
        return -Dist(b**S(2)*(n + S(-1))/(m + n + S(-1)), Int((a/sin(e + f*x))**m*(b/tan(e + f*x))**(n + S(-2)), x), x) - Simp(b*(a/sin(e + f*x))**m*(b/tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3436 = ReplacementRule(pattern3436, replacement3436)
    pattern3437 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons1520, cons1170)
    def replacement3437(m, f, b, a, n, x, e):
        rubi.append(3437)
        return Dist((m + n + S(1))/(a**S(2)*m), Int((a/cos(e + f*x))**(m + S(2))*(b*tan(e + f*x))**n, x), x) - Simp((a/cos(e + f*x))**m*(b*tan(e + f*x))**(n + S(1))/(b*f*m), x)
    rule3437 = ReplacementRule(pattern3437, replacement3437)
    pattern3438 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons1520, cons1170)
    def replacement3438(m, f, b, a, n, x, e):
        rubi.append(3438)
        return Dist((m + n + S(1))/(a**S(2)*m), Int((a/sin(e + f*x))**(m + S(2))*(b/tan(e + f*x))**n, x), x) + Simp((a/sin(e + f*x))**m*(b/tan(e + f*x))**(n + S(1))/(b*f*m), x)
    rule3438 = ReplacementRule(pattern3438, replacement3438)
    pattern3439 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons1521, cons1519, cons1170)
    def replacement3439(m, f, b, a, n, x, e):
        rubi.append(3439)
        return Dist(a**S(2)*(m + S(-2))/(m + n + S(-1)), Int((a/cos(e + f*x))**(m + S(-2))*(b*tan(e + f*x))**n, x), x) + Simp(a**S(2)*(a/cos(e + f*x))**(m + S(-2))*(b*tan(e + f*x))**(n + S(1))/(b*f*(m + n + S(-1))), x)
    rule3439 = ReplacementRule(pattern3439, replacement3439)
    pattern3440 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons1521, cons1519, cons1170)
    def replacement3440(m, f, b, a, n, x, e):
        rubi.append(3440)
        return Dist(a**S(2)*(m + S(-2))/(m + n + S(-1)), Int((a/sin(e + f*x))**(m + S(-2))*(b/tan(e + f*x))**n, x), x) - Simp(a**S(2)*(a/sin(e + f*x))**(m + S(-2))*(b/tan(e + f*x))**(n + S(1))/(b*f*(m + n + S(-1))), x)
    rule3440 = ReplacementRule(pattern3440, replacement3440)
    pattern3441 = Pattern(Integral(S(1)/(sqrt(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons48, cons125, cons1522)
    def replacement3441(x, f, b, e):
        rubi.append(3441)
        return Dist(sqrt(sin(e + f*x))/(sqrt(b*tan(e + f*x))*sqrt(cos(e + f*x))), Int(S(1)/(sqrt(sin(e + f*x))*sqrt(cos(e + f*x))), x), x)
    rule3441 = ReplacementRule(pattern3441, replacement3441)
    pattern3442 = Pattern(Integral(S(1)/(sqrt(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons48, cons125, cons1522)
    def replacement3442(x, f, b, e):
        rubi.append(3442)
        return Dist(sqrt(cos(e + f*x))/(sqrt(b/tan(e + f*x))*sqrt(sin(e + f*x))), Int(S(1)/(sqrt(sin(e + f*x))*sqrt(cos(e + f*x))), x), x)
    rule3442 = ReplacementRule(pattern3442, replacement3442)
    pattern3443 = Pattern(Integral(sqrt(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons3, cons48, cons125, cons1522)
    def replacement3443(x, f, b, e):
        rubi.append(3443)
        return Dist(sqrt(b*tan(e + f*x))*sqrt(cos(e + f*x))/sqrt(sin(e + f*x)), Int(sqrt(sin(e + f*x))*sqrt(cos(e + f*x)), x), x)
    rule3443 = ReplacementRule(pattern3443, replacement3443)
    pattern3444 = Pattern(Integral(sqrt(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons3, cons48, cons125, cons1522)
    def replacement3444(x, f, b, e):
        rubi.append(3444)
        return Dist(sqrt(b/tan(e + f*x))*sqrt(sin(e + f*x))/sqrt(cos(e + f*x)), Int(sqrt(sin(e + f*x))*sqrt(cos(e + f*x)), x), x)
    rule3444 = ReplacementRule(pattern3444, replacement3444)
    pattern3445 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons80, cons79)
    def replacement3445(m, f, b, a, n, x, e):
        rubi.append(3445)
        return Dist(a**(m + n)*(a/cos(e + f*x))**(-n)*(b*sin(e + f*x))**(-n)*(b*tan(e + f*x))**n, Int((b*sin(e + f*x))**n*cos(e + f*x)**(-m - n), x), x)
    rule3445 = ReplacementRule(pattern3445, replacement3445)
    pattern3446 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons80, cons79)
    def replacement3446(m, f, b, a, n, x, e):
        rubi.append(3446)
        return Dist(a**(m + n)*(a/sin(e + f*x))**(-n)*(b*cos(e + f*x))**(-n)*(b/tan(e + f*x))**n, Int((b*cos(e + f*x))**n*sin(e + f*x)**(-m - n), x), x)
    rule3446 = ReplacementRule(pattern3446, replacement3446)
    pattern3447 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1523, cons1524)
    def replacement3447(m, f, b, a, n, x, e):
        rubi.append(3447)
        return Simp((a/cos(e + f*x))**m*(b*tan(e + f*x))**(n + S(1))*(cos(e + f*x)**S(2))**(m/S(2) + n/S(2) + S(1)/2)*Hypergeometric2F1(n/S(2) + S(1)/2, m/S(2) + n/S(2) + S(1)/2, n/S(2) + S(3)/2, sin(e + f*x)**S(2))/(b*f*(n + S(1))), x)
    rule3447 = ReplacementRule(pattern3447, replacement3447)
    pattern3448 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1523, cons1524)
    def replacement3448(m, f, b, a, n, x, e):
        rubi.append(3448)
        return -Simp((a/sin(e + f*x))**m*(b/tan(e + f*x))**(n + S(1))*(sin(e + f*x)**S(2))**(m/S(2) + n/S(2) + S(1)/2)*Hypergeometric2F1(n/S(2) + S(1)/2, m/S(2) + n/S(2) + S(1)/2, n/S(2) + S(3)/2, cos(e + f*x)**S(2))/(b*f*(n + S(1))), x)
    rule3448 = ReplacementRule(pattern3448, replacement3448)
    pattern3449 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons18, cons23)
    def replacement3449(m, f, b, a, n, x, e):
        rubi.append(3449)
        return Dist((sin(e + f*x)/a)**FracPart(m)*(a/sin(e + f*x))**FracPart(m), Int((sin(e + f*x)/a)**(-m)*(b*tan(e + f*x))**n, x), x)
    rule3449 = ReplacementRule(pattern3449, replacement3449)
    pattern3450 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons18, cons23)
    def replacement3450(m, f, b, a, n, x, e):
        rubi.append(3450)
        return Dist((cos(e + f*x)/a)**FracPart(m)*(a/cos(e + f*x))**FracPart(m), Int((cos(e + f*x)/a)**(-m)*(b/tan(e + f*x))**n, x), x)
    rule3450 = ReplacementRule(pattern3450, replacement3450)
    pattern3451 = Pattern(Integral(((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('a', S(1)))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons5, cons87, cons165, cons1525, cons1526)
    def replacement3451(p, m, f, b, d, a, n, x, e):
        rubi.append(3451)
        return -Dist(b**S(2)*(n + S(-1))/(m*p + n + S(-1)), Int((a*(d/cos(e + f*x))**p)**m*(b*tan(e + f*x))**(n + S(-2)), x), x) + Simp(b*(a*(d/cos(e + f*x))**p)**m*(b*tan(e + f*x))**(n + S(-1))/(f*(m*p + n + S(-1))), x)
    rule3451 = ReplacementRule(pattern3451, replacement3451)
    pattern3452 = Pattern(Integral(((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('a', S(1)))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons5, cons87, cons165, cons1525, cons1526)
    def replacement3452(p, m, f, b, d, a, n, x, e):
        rubi.append(3452)
        return -Dist(b**S(2)*(n + S(-1))/(m*p + n + S(-1)), Int((a*(d/sin(e + f*x))**p)**m*(b/tan(e + f*x))**(n + S(-2)), x), x) - Simp(b*(a*(d/sin(e + f*x))**p)**m*(b/tan(e + f*x))**(n + S(-1))/(f*(m*p + n + S(-1))), x)
    rule3452 = ReplacementRule(pattern3452, replacement3452)
    pattern3453 = Pattern(Integral(((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('a', S(1)))**WC('m', S(1))*(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons5, cons87, cons89, cons1527, cons1526)
    def replacement3453(p, m, f, b, d, a, n, x, e):
        rubi.append(3453)
        return -Dist((m*p + n + S(1))/(b**S(2)*(n + S(1))), Int((a*(d/cos(e + f*x))**p)**m*(b*tan(e + f*x))**(n + S(2)), x), x) + Simp((a*(d/cos(e + f*x))**p)**m*(b*tan(e + f*x))**(n + S(1))/(b*f*(n + S(1))), x)
    rule3453 = ReplacementRule(pattern3453, replacement3453)
    pattern3454 = Pattern(Integral(((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('a', S(1)))**WC('m', S(1))*(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons5, cons87, cons89, cons1527, cons1526)
    def replacement3454(p, m, f, b, d, a, n, x, e):
        rubi.append(3454)
        return -Dist((m*p + n + S(1))/(b**S(2)*(n + S(1))), Int((a*(d/sin(e + f*x))**p)**m*(b/tan(e + f*x))**(n + S(2)), x), x) + Simp((a*(d/sin(e + f*x))**p)**m*(b/tan(e + f*x))**(n + S(1))/(b*f*(n + S(1))), x)
    rule3454 = ReplacementRule(pattern3454, replacement3454)
    pattern3455 = Pattern(Integral((WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons87, cons165)
    def replacement3455(b, d, c, n, x):
        rubi.append(3455)
        return -Dist(b**S(2), Int((b*tan(c + d*x))**(n + S(-2)), x), x) + Simp(b*(b*tan(c + d*x))**(n + S(-1))/(d*(n + S(-1))), x)
    rule3455 = ReplacementRule(pattern3455, replacement3455)
    pattern3456 = Pattern(Integral((WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons87, cons165)
    def replacement3456(b, d, c, n, x):
        rubi.append(3456)
        return -Dist(b**S(2), Int((b/tan(c + d*x))**(n + S(-2)), x), x) - Simp(b*(b/tan(c + d*x))**(n + S(-1))/(d*(n + S(-1))), x)
    rule3456 = ReplacementRule(pattern3456, replacement3456)
    pattern3457 = Pattern(Integral((WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons87, cons89)
    def replacement3457(b, d, c, n, x):
        rubi.append(3457)
        return -Dist(b**(S(-2)), Int((b*tan(c + d*x))**(n + S(2)), x), x) + Simp((b*tan(c + d*x))**(n + S(1))/(b*d*(n + S(1))), x)
    rule3457 = ReplacementRule(pattern3457, replacement3457)
    pattern3458 = Pattern(Integral((WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons87, cons89)
    def replacement3458(b, d, c, n, x):
        rubi.append(3458)
        return -Dist(b**(S(-2)), Int((b/tan(c + d*x))**(n + S(2)), x), x) - Simp((b/tan(c + d*x))**(n + S(1))/(b*d*(n + S(1))), x)
    rule3458 = ReplacementRule(pattern3458, replacement3458)
    pattern3459 = Pattern(Integral(tan(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons1261)
    def replacement3459(d, c, x):
        rubi.append(3459)
        return -Simp(log(RemoveContent(cos(c + d*x), x))/d, x)
    rule3459 = ReplacementRule(pattern3459, replacement3459)
    pattern3460 = Pattern(Integral(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons1261)
    def replacement3460(d, c, x):
        rubi.append(3460)
        return Simp(log(RemoveContent(sin(c + d*x), x))/d, x)
    rule3460 = ReplacementRule(pattern3460, replacement3460)
    pattern3461 = Pattern(Integral((WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons4, cons23)
    def replacement3461(b, d, c, n, x):
        rubi.append(3461)
        return Dist(b/d, Subst(Int(x**n/(b**S(2) + x**S(2)), x), x, b*tan(c + d*x)), x)
    rule3461 = ReplacementRule(pattern3461, replacement3461)
    pattern3462 = Pattern(Integral((WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons4, cons23)
    def replacement3462(b, d, c, n, x):
        rubi.append(3462)
        return -Dist(b/d, Subst(Int(x**n/(b**S(2) + x**S(2)), x), x, b/tan(c + d*x)), x)
    rule3462 = ReplacementRule(pattern3462, replacement3462)
    pattern3463 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons1264)
    def replacement3463(b, d, c, a, x):
        rubi.append(3463)
        return Dist(S(2)*a*b, Int(tan(c + d*x), x), x) + Simp(x*(a**S(2) - b**S(2)), x) + Simp(b**S(2)*tan(c + d*x)/d, x)
    rule3463 = ReplacementRule(pattern3463, replacement3463)
    pattern3464 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons1264)
    def replacement3464(b, d, c, a, x):
        rubi.append(3464)
        return Dist(S(2)*a*b, Int(S(1)/tan(c + d*x), x), x) + Simp(x*(a**S(2) - b**S(2)), x) - Simp(b**S(2)/(d*tan(c + d*x)), x)
    rule3464 = ReplacementRule(pattern3464, replacement3464)
    pattern3465 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1439, cons87, cons165)
    def replacement3465(b, d, c, a, n, x):
        rubi.append(3465)
        return Dist(S(2)*a, Int((a + b*tan(c + d*x))**(n + S(-1)), x), x) + Simp(b*(a + b*tan(c + d*x))**(n + S(-1))/(d*(n + S(-1))), x)
    rule3465 = ReplacementRule(pattern3465, replacement3465)
    pattern3466 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1439, cons87, cons165)
    def replacement3466(b, d, c, a, n, x):
        rubi.append(3466)
        return Dist(S(2)*a, Int((a + b/tan(c + d*x))**(n + S(-1)), x), x) - Simp(b*(a + b/tan(c + d*x))**(n + S(-1))/(d*(n + S(-1))), x)
    rule3466 = ReplacementRule(pattern3466, replacement3466)
    pattern3467 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1439, cons87, cons463)
    def replacement3467(b, d, c, a, n, x):
        rubi.append(3467)
        return Dist(S(1)/(S(2)*a), Int((a + b*tan(c + d*x))**(n + S(1)), x), x) + Simp(a*(a + b*tan(c + d*x))**n/(S(2)*b*d*n), x)
    rule3467 = ReplacementRule(pattern3467, replacement3467)
    pattern3468 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1439, cons87, cons463)
    def replacement3468(b, d, c, a, n, x):
        rubi.append(3468)
        return Dist(S(1)/(S(2)*a), Int((a + b/tan(c + d*x))**(n + S(1)), x), x) - Simp(a*(a + b/tan(c + d*x))**n/(S(2)*b*d*n), x)
    rule3468 = ReplacementRule(pattern3468, replacement3468)
    pattern3469 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1439)
    def replacement3469(b, d, c, a, x):
        rubi.append(3469)
        return Dist(-S(2)*b/d, Subst(Int(S(1)/(S(2)*a - x**S(2)), x), x, sqrt(a + b*tan(c + d*x))), x)
    rule3469 = ReplacementRule(pattern3469, replacement3469)
    pattern3470 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1439)
    def replacement3470(b, d, c, a, x):
        rubi.append(3470)
        return Dist(S(2)*b/d, Subst(Int(S(1)/(S(2)*a - x**S(2)), x), x, sqrt(a + b/tan(c + d*x))), x)
    rule3470 = ReplacementRule(pattern3470, replacement3470)
    pattern3471 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1439)
    def replacement3471(b, d, c, a, n, x):
        rubi.append(3471)
        return -Dist(b/d, Subst(Int((a + x)**(n + S(-1))/(a - x), x), x, b*tan(c + d*x)), x)
    rule3471 = ReplacementRule(pattern3471, replacement3471)
    pattern3472 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1439)
    def replacement3472(b, d, c, a, n, x):
        rubi.append(3472)
        return Dist(b/d, Subst(Int((a + x)**(n + S(-1))/(a - x), x), x, b/tan(c + d*x)), x)
    rule3472 = ReplacementRule(pattern3472, replacement3472)
    pattern3473 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1440, cons87, cons165)
    def replacement3473(b, d, c, a, n, x):
        rubi.append(3473)
        return Int((a + b*tan(c + d*x))**(n + S(-2))*(a**S(2) + S(2)*a*b*tan(c + d*x) - b**S(2)), x) + Simp(b*(a + b*tan(c + d*x))**(n + S(-1))/(d*(n + S(-1))), x)
    rule3473 = ReplacementRule(pattern3473, replacement3473)
    pattern3474 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1440, cons87, cons165)
    def replacement3474(b, d, c, a, n, x):
        rubi.append(3474)
        return Int((a + b/tan(c + d*x))**(n + S(-2))*(a**S(2) + S(2)*a*b/tan(c + d*x) - b**S(2)), x) - Simp(b*(a + b/tan(c + d*x))**(n + S(-1))/(d*(n + S(-1))), x)
    rule3474 = ReplacementRule(pattern3474, replacement3474)
    pattern3475 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1440, cons87, cons89)
    def replacement3475(b, d, c, a, n, x):
        rubi.append(3475)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a - b*tan(c + d*x))*(a + b*tan(c + d*x))**(n + S(1)), x), x) + Simp(b*(a + b*tan(c + d*x))**(n + S(1))/(d*(a**S(2) + b**S(2))*(n + S(1))), x)
    rule3475 = ReplacementRule(pattern3475, replacement3475)
    pattern3476 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1440, cons87, cons89)
    def replacement3476(b, d, c, a, n, x):
        rubi.append(3476)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a - b/tan(c + d*x))*(a + b/tan(c + d*x))**(n + S(1)), x), x) - Simp(b*(a + b/tan(c + d*x))**(n + S(1))/(d*(a**S(2) + b**S(2))*(n + S(1))), x)
    rule3476 = ReplacementRule(pattern3476, replacement3476)
    pattern3477 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440)
    def replacement3477(b, d, c, a, x):
        rubi.append(3477)
        return Dist(b/(a**S(2) + b**S(2)), Int((-a*tan(c + d*x) + b)/(a + b*tan(c + d*x)), x), x) + Simp(a*x/(a**S(2) + b**S(2)), x)
    rule3477 = ReplacementRule(pattern3477, replacement3477)
    pattern3478 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440)
    def replacement3478(b, d, c, a, x):
        rubi.append(3478)
        return Dist(b/(a**S(2) + b**S(2)), Int((-a/tan(c + d*x) + b)/(a + b/tan(c + d*x)), x), x) + Simp(a*x/(a**S(2) + b**S(2)), x)
    rule3478 = ReplacementRule(pattern3478, replacement3478)
    pattern3479 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1440)
    def replacement3479(b, d, c, a, n, x):
        rubi.append(3479)
        return Dist(b/d, Subst(Int((a + x)**n/(b**S(2) + x**S(2)), x), x, b*tan(c + d*x)), x)
    rule3479 = ReplacementRule(pattern3479, replacement3479)
    pattern3480 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1440)
    def replacement3480(b, d, c, a, n, x):
        rubi.append(3480)
        return -Dist(b/d, Subst(Int((a + x)**n/(b**S(2) + x**S(2)), x), x, b/tan(c + d*x)), x)
    rule3480 = ReplacementRule(pattern3480, replacement3480)
    pattern3481 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1528)
    def replacement3481(m, f, b, d, a, x, e):
        rubi.append(3481)
        return Dist(a, Int((d/cos(e + f*x))**m, x), x) + Simp(b*(d/cos(e + f*x))**m/(f*m), x)
    rule3481 = ReplacementRule(pattern3481, replacement3481)
    pattern3482 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1528)
    def replacement3482(m, f, b, d, a, x, e):
        rubi.append(3482)
        return Dist(a, Int((d/sin(e + f*x))**m, x), x) - Simp(b*(d/sin(e + f*x))**m/(f*m), x)
    rule3482 = ReplacementRule(pattern3482, replacement3482)
    pattern3483 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(S(1)/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons4, cons1439, cons1515)
    def replacement3483(m, f, b, a, n, x, e):
        rubi.append(3483)
        return Dist(a**(-m + S(2))/(b*f), Subst(Int((a - x)**(m/S(2) + S(-1))*(a + x)**(m/S(2) + n + S(-1)), x), x, b*tan(e + f*x)), x)
    rule3483 = ReplacementRule(pattern3483, replacement3483)
    pattern3484 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(S(1)/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons4, cons1439, cons1515)
    def replacement3484(m, f, b, a, n, x, e):
        rubi.append(3484)
        return -Dist(a**(-m + S(2))/(b*f), Subst(Int((a - x)**(m/S(2) + S(-1))*(a + x)**(m/S(2) + n + S(-1)), x), x, b/tan(e + f*x)), x)
    rule3484 = ReplacementRule(pattern3484, replacement3484)
    pattern3485 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1255)
    def replacement3485(m, f, b, d, a, n, x, e):
        rubi.append(3485)
        return Simp(b*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**n/(a*f*m), x)
    rule3485 = ReplacementRule(pattern3485, replacement3485)
    pattern3486 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1255)
    def replacement3486(m, f, b, d, a, n, x, e):
        rubi.append(3486)
        return -Simp(b*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**n/(a*f*m), x)
    rule3486 = ReplacementRule(pattern3486, replacement3486)
    pattern3487 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1439)
    def replacement3487(f, b, a, x, e):
        rubi.append(3487)
        return Dist(-S(2)*a/(b*f), Subst(Int(S(1)/(-a*x**S(2) + S(2)), x), x, S(1)/(sqrt(a + b*tan(e + f*x))*cos(e + f*x))), x)
    rule3487 = ReplacementRule(pattern3487, replacement3487)
    pattern3488 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1439)
    def replacement3488(f, b, a, x, e):
        rubi.append(3488)
        return Dist(S(2)*a/(b*f), Subst(Int(S(1)/(-a*x**S(2) + S(2)), x), x, S(1)/(sqrt(a + b/tan(e + f*x))*sin(e + f*x))), x)
    rule3488 = ReplacementRule(pattern3488, replacement3488)
    pattern3489 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons1529, cons93, cons88)
    def replacement3489(m, f, b, d, a, n, x, e):
        rubi.append(3489)
        return Dist(a/(S(2)*d**S(2)), Int((d/cos(e + f*x))**(m + S(2))*(a + b*tan(e + f*x))**(n + S(-1)), x), x) + Simp(b*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**n/(a*f*m), x)
    rule3489 = ReplacementRule(pattern3489, replacement3489)
    pattern3490 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons1529, cons93, cons88)
    def replacement3490(m, f, b, d, a, n, x, e):
        rubi.append(3490)
        return Dist(a/(S(2)*d**S(2)), Int((d/sin(e + f*x))**(m + S(2))*(a + b/tan(e + f*x))**(n + S(-1)), x), x) - Simp(b*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**n/(a*f*m), x)
    rule3490 = ReplacementRule(pattern3490, replacement3490)
    pattern3491 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons1529, cons93, cons89)
    def replacement3491(m, f, b, d, a, n, x, e):
        rubi.append(3491)
        return Dist(S(2)*d**S(2)/a, Int((d/cos(e + f*x))**(m + S(-2))*(a + b*tan(e + f*x))**(n + S(1)), x), x) + Simp(S(2)*d**S(2)*(d/cos(e + f*x))**(m + S(-2))*(a + b*tan(e + f*x))**(n + S(1))/(b*f*(m + S(-2))), x)
    rule3491 = ReplacementRule(pattern3491, replacement3491)
    pattern3492 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons1529, cons93, cons89)
    def replacement3492(m, f, b, d, a, n, x, e):
        rubi.append(3492)
        return Dist(S(2)*d**S(2)/a, Int((d/sin(e + f*x))**(m + S(-2))*(a + b/tan(e + f*x))**(n + S(1)), x), x) + Simp(-S(2)*d**S(2)*(d/sin(e + f*x))**(m + S(-2))*(a + b/tan(e + f*x))**(n + S(1))/(b*f*(m + S(-2))), x)
    rule3492 = ReplacementRule(pattern3492, replacement3492)
    pattern3493 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1529)
    def replacement3493(m, f, b, d, a, n, x, e):
        rubi.append(3493)
        return Dist((a/d)**(S(2)*IntPart(n))*(d/cos(e + f*x))**(-S(2)*FracPart(n))*(a - b*tan(e + f*x))**FracPart(n)*(a + b*tan(e + f*x))**FracPart(n), Int((a - b*tan(e + f*x))**(-n), x), x)
    rule3493 = ReplacementRule(pattern3493, replacement3493)
    pattern3494 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1529)
    def replacement3494(m, f, b, d, a, n, x, e):
        rubi.append(3494)
        return Dist((a/d)**(S(2)*IntPart(n))*(d/sin(e + f*x))**(-S(2)*FracPart(n))*(a - b/tan(e + f*x))**FracPart(n)*(a + b/tan(e + f*x))**FracPart(n), Int((a - b/tan(e + f*x))**(-n), x), x)
    rule3494 = ReplacementRule(pattern3494, replacement3494)
    pattern3495 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1530)
    def replacement3495(m, f, b, d, a, n, x, e):
        rubi.append(3495)
        return Simp(S(2)*b*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3495 = ReplacementRule(pattern3495, replacement3495)
    pattern3496 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1530)
    def replacement3496(m, f, b, d, a, n, x, e):
        rubi.append(3496)
        return Simp(-S(2)*b*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3496 = ReplacementRule(pattern3496, replacement3496)
    pattern3497 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1531, cons23)
    def replacement3497(m, f, b, d, a, n, x, e):
        rubi.append(3497)
        return Dist(a*(m + S(2)*n + S(-2))/(m + n + S(-1)), Int((d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(-1)), x), x) + Simp(b*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3497 = ReplacementRule(pattern3497, replacement3497)
    pattern3498 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1531, cons23)
    def replacement3498(m, f, b, d, a, n, x, e):
        rubi.append(3498)
        return Dist(a*(m + S(2)*n + S(-2))/(m + n + S(-1)), Int((d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(-1)), x), x) - Simp(b*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3498 = ReplacementRule(pattern3498, replacement3498)
    pattern3499 = Pattern(Integral(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1439)
    def replacement3499(f, b, d, a, x, e):
        rubi.append(3499)
        return Dist(-S(4)*b*d**S(2)/f, Subst(Int(x**S(2)/(a**S(2) + d**S(2)*x**S(4)), x), x, sqrt(a + b*tan(e + f*x))/sqrt(d/cos(e + f*x))), x)
    rule3499 = ReplacementRule(pattern3499, replacement3499)
    pattern3500 = Pattern(Integral(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1439)
    def replacement3500(f, b, d, a, x, e):
        rubi.append(3500)
        return Dist(S(4)*b*d**S(2)/f, Subst(Int(x**S(2)/(a**S(2) + d**S(2)*x**S(4)), x), x, sqrt(a + b/tan(e + f*x))/sqrt(d/sin(e + f*x))), x)
    rule3500 = ReplacementRule(pattern3500, replacement3500)
    pattern3501 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons93, cons165, cons1532, cons515)
    def replacement3501(m, f, b, d, a, n, x, e):
        rubi.append(3501)
        return -Dist(b**S(2)*(m + S(2)*n + S(-2))/(d**S(2)*m), Int((d/cos(e + f*x))**(m + S(2))*(a + b*tan(e + f*x))**(n + S(-2)), x), x) + Simp(S(2)*b*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3501 = ReplacementRule(pattern3501, replacement3501)
    pattern3502 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons93, cons165, cons1533, cons515)
    def replacement3502(m, f, b, d, a, n, x, e):
        rubi.append(3502)
        return -Dist(b**S(2)*(m + S(2)*n + S(-2))/(d**S(2)*m), Int((d/sin(e + f*x))**(m + S(2))*(a + b/tan(e + f*x))**(n + S(-2)), x), x) + Simp(-S(2)*b*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(-1))/(f*m), x)
    rule3502 = ReplacementRule(pattern3502, replacement3502)
    pattern3503 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons93, cons88, cons94, cons1170)
    def replacement3503(m, f, b, d, a, n, x, e):
        rubi.append(3503)
        return Dist(a*(m + n)/(d**S(2)*m), Int((d/cos(e + f*x))**(m + S(2))*(a + b*tan(e + f*x))**(n + S(-1)), x), x) + Simp(b*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**n/(a*f*m), x)
    rule3503 = ReplacementRule(pattern3503, replacement3503)
    pattern3504 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons93, cons88, cons94, cons1170)
    def replacement3504(m, f, b, d, a, n, x, e):
        rubi.append(3504)
        return Dist(a*(m + n)/(d**S(2)*m), Int((d/sin(e + f*x))**(m + S(2))*(a + b/tan(e + f*x))**(n + S(-1)), x), x) - Simp(b*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**n/(a*f*m), x)
    rule3504 = ReplacementRule(pattern3504, replacement3504)
    pattern3505 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1439, cons87, cons88, cons1519, cons1170)
    def replacement3505(m, f, b, d, a, n, x, e):
        rubi.append(3505)
        return Dist(a*(m + S(2)*n + S(-2))/(m + n + S(-1)), Int((d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(-1)), x), x) + Simp(b*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3505 = ReplacementRule(pattern3505, replacement3505)
    pattern3506 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1439, cons87, cons88, cons1519, cons1170)
    def replacement3506(m, f, b, d, a, n, x, e):
        rubi.append(3506)
        return Dist(a*(m + S(2)*n + S(-2))/(m + n + S(-1)), Int((d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(-1)), x), x) - Simp(b*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3506 = ReplacementRule(pattern3506, replacement3506)
    pattern3507 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1439)
    def replacement3507(f, b, d, a, x, e):
        rubi.append(3507)
        return Dist(d/(sqrt(a - b*tan(e + f*x))*sqrt(a + b*tan(e + f*x))*cos(e + f*x)), Int(sqrt(d/cos(e + f*x))*sqrt(a - b*tan(e + f*x)), x), x)
    rule3507 = ReplacementRule(pattern3507, replacement3507)
    pattern3508 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1439)
    def replacement3508(f, b, d, a, x, e):
        rubi.append(3508)
        return Dist(d/(sqrt(a - b/tan(e + f*x))*sqrt(a + b/tan(e + f*x))*sin(e + f*x)), Int(sqrt(d/sin(e + f*x))*sqrt(a - b/tan(e + f*x)), x), x)
    rule3508 = ReplacementRule(pattern3508, replacement3508)
    pattern3509 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1439, cons87, cons89, cons1534, cons515)
    def replacement3509(m, f, b, d, a, n, x, e):
        rubi.append(3509)
        return -Dist(d**S(2)*(m + S(-2))/(b**S(2)*(m + S(2)*n)), Int((d/cos(e + f*x))**(m + S(-2))*(a + b*tan(e + f*x))**(n + S(2)), x), x) + Simp(S(2)*d**S(2)*(d/cos(e + f*x))**(m + S(-2))*(a + b*tan(e + f*x))**(n + S(1))/(b*f*(m + S(2)*n)), x)
    rule3509 = ReplacementRule(pattern3509, replacement3509)
    pattern3510 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1439, cons87, cons89, cons1534, cons515)
    def replacement3510(m, f, b, d, a, n, x, e):
        rubi.append(3510)
        return -Dist(d**S(2)*(m + S(-2))/(b**S(2)*(m + S(2)*n)), Int((d/sin(e + f*x))**(m + S(-2))*(a + b/tan(e + f*x))**(n + S(2)), x), x) + Simp(-S(2)*d**S(2)*(d/sin(e + f*x))**(m + S(-2))*(a + b/tan(e + f*x))**(n + S(1))/(b*f*(m + S(2)*n)), x)
    rule3510 = ReplacementRule(pattern3510, replacement3510)
    pattern3511 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons93, cons463, cons166, cons1535, cons1519, cons1170)
    def replacement3511(m, f, b, d, a, n, x, e):
        rubi.append(3511)
        return Dist(d**S(2)*(m + S(-2))/(a*(m + n + S(-1))), Int((d/cos(e + f*x))**(m + S(-2))*(a + b*tan(e + f*x))**(n + S(1)), x), x) + Simp(d**S(2)*(d/cos(e + f*x))**(m + S(-2))*(a + b*tan(e + f*x))**(n + S(1))/(b*f*(m + n + S(-1))), x)
    rule3511 = ReplacementRule(pattern3511, replacement3511)
    pattern3512 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons1439, cons93, cons463, cons166, cons1535, cons1519, cons1170)
    def replacement3512(m, f, b, d, a, n, x, e):
        rubi.append(3512)
        return Dist(d**S(2)*(m + S(-2))/(a*(m + n + S(-1))), Int((d/sin(e + f*x))**(m + S(-2))*(a + b/tan(e + f*x))**(n + S(1)), x), x) - Simp(d**S(2)*(d/sin(e + f*x))**(m + S(-2))*(a + b/tan(e + f*x))**(n + S(1))/(b*f*(m + n + S(-1))), x)
    rule3512 = ReplacementRule(pattern3512, replacement3512)
    pattern3513 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1439, cons87, cons463, cons1536, cons1170)
    def replacement3513(m, f, b, d, a, n, x, e):
        rubi.append(3513)
        return Dist((m + n)/(a*(m + S(2)*n)), Int((d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(1)), x), x) + Simp(a*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**n/(b*f*(m + S(2)*n)), x)
    rule3513 = ReplacementRule(pattern3513, replacement3513)
    pattern3514 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1439, cons87, cons463, cons1536, cons1170)
    def replacement3514(m, f, b, d, a, n, x, e):
        rubi.append(3514)
        return Dist((m + n)/(a*(m + S(2)*n)), Int((d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(1)), x), x) - Simp(a*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**n/(b*f*(m + S(2)*n)), x)
    rule3514 = ReplacementRule(pattern3514, replacement3514)
    pattern3515 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1537, cons87)
    def replacement3515(m, f, b, d, a, n, x, e):
        rubi.append(3515)
        return Dist(a*(m + S(2)*n + S(-2))/(m + n + S(-1)), Int((d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(-1)), x), x) + Simp(b*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3515 = ReplacementRule(pattern3515, replacement3515)
    pattern3516 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1537, cons87)
    def replacement3516(m, f, b, d, a, n, x, e):
        rubi.append(3516)
        return Dist(a*(m + S(2)*n + S(-2))/(m + n + S(-1)), Int((d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(-1)), x), x) - Simp(b*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3516 = ReplacementRule(pattern3516, replacement3516)
    pattern3517 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1538, cons1536)
    def replacement3517(m, f, b, d, a, n, x, e):
        rubi.append(3517)
        return Dist((m + n)/(a*(m + S(2)*n)), Int((d/cos(e + f*x))**m*(a + b*tan(e + f*x))**(n + S(1)), x), x) + Simp(a*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))**n/(b*f*(m + S(2)*n)), x)
    rule3517 = ReplacementRule(pattern3517, replacement3517)
    pattern3518 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439, cons1538, cons1536)
    def replacement3518(m, f, b, d, a, n, x, e):
        rubi.append(3518)
        return Dist((m + n)/(a*(m + S(2)*n)), Int((d/sin(e + f*x))**m*(a + b/tan(e + f*x))**(n + S(1)), x), x) - Simp(a*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))**n/(b*f*(m + S(2)*n)), x)
    rule3518 = ReplacementRule(pattern3518, replacement3518)
    pattern3519 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439)
    def replacement3519(m, f, b, d, a, n, x, e):
        rubi.append(3519)
        return Dist((d/cos(e + f*x))**m*(a - b*tan(e + f*x))**(-m/S(2))*(a + b*tan(e + f*x))**(-m/S(2)), Int((a - b*tan(e + f*x))**(m/S(2))*(a + b*tan(e + f*x))**(m/S(2) + n), x), x)
    rule3519 = ReplacementRule(pattern3519, replacement3519)
    pattern3520 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1439)
    def replacement3520(m, f, b, d, a, n, x, e):
        rubi.append(3520)
        return Dist((d/sin(e + f*x))**m*(a - b/tan(e + f*x))**(-m/S(2))*(a + b/tan(e + f*x))**(-m/S(2)), Int((a - b/tan(e + f*x))**(m/S(2))*(a + b/tan(e + f*x))**(m/S(2) + n), x), x)
    rule3520 = ReplacementRule(pattern3520, replacement3520)
    pattern3521 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(S(1)/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons4, cons1440, cons1515)
    def replacement3521(m, f, b, a, n, x, e):
        rubi.append(3521)
        return Dist(S(1)/(b*f), Subst(Int((S(1) + x**S(2)/b**S(2))**(m/S(2) + S(-1))*(a + x)**n, x), x, b*tan(e + f*x)), x)
    rule3521 = ReplacementRule(pattern3521, replacement3521)
    pattern3522 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(S(1)/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons4, cons1440, cons1515)
    def replacement3522(m, f, b, a, n, x, e):
        rubi.append(3522)
        return -Dist(S(1)/(b*f), Subst(Int((S(1) + x**S(2)/b**S(2))**(m/S(2) + S(-1))*(a + x)**n, x), x, b/tan(e + f*x)), x)
    rule3522 = ReplacementRule(pattern3522, replacement3522)
    pattern3523 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2)*cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1440)
    def replacement3523(f, b, a, x, e):
        rubi.append(3523)
        return Simp(b**S(2)*atanh(sin(e + f*x))/f, x) + Simp((a**S(2) - b**S(2))*sin(e + f*x)/f, x) - Simp(S(2)*a*b*cos(e + f*x)/f, x)
    rule3523 = ReplacementRule(pattern3523, replacement3523)
    pattern3524 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**S(2)*tan(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1440)
    def replacement3524(f, b, a, x, e):
        rubi.append(3524)
        return -Simp(b**S(2)*atanh(cos(e + f*x))/f, x) - Simp((a**S(2) - b**S(2))*cos(e + f*x)/f, x) + Simp(S(2)*a*b*sin(e + f*x)/f, x)
    rule3524 = ReplacementRule(pattern3524, replacement3524)
    pattern3525 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1440, cons66)
    def replacement3525(m, f, b, d, a, x, e):
        rubi.append(3525)
        return Dist(S(1)/(m + S(1)), Int((d/cos(e + f*x))**m*(a**S(2)*(m + S(1)) + a*b*(m + S(2))*tan(e + f*x) - b**S(2)), x), x) + Simp(b*(d/cos(e + f*x))**m*(a + b*tan(e + f*x))/(f*(m + S(1))), x)
    rule3525 = ReplacementRule(pattern3525, replacement3525)
    pattern3526 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1440, cons66)
    def replacement3526(m, f, b, d, a, x, e):
        rubi.append(3526)
        return Dist(S(1)/(m + S(1)), Int((d/sin(e + f*x))**m*(a**S(2)*(m + S(1)) + a*b*(m + S(2))/tan(e + f*x) - b**S(2)), x), x) - Simp(b*(d/sin(e + f*x))**m*(a + b/tan(e + f*x))/(f*(m + S(1))), x)
    rule3526 = ReplacementRule(pattern3526, replacement3526)
    pattern3527 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1440)
    def replacement3527(f, b, a, x, e):
        rubi.append(3527)
        return -Dist(S(1)/f, Subst(Int(S(1)/(a**S(2) + b**S(2) - x**S(2)), x), x, (-a*tan(e + f*x) + b)*cos(e + f*x)), x)
    rule3527 = ReplacementRule(pattern3527, replacement3527)
    pattern3528 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1440)
    def replacement3528(f, b, a, x, e):
        rubi.append(3528)
        return Dist(S(1)/f, Subst(Int(S(1)/(a**S(2) + b**S(2) - x**S(2)), x), x, (-a/tan(e + f*x) + b)*sin(e + f*x)), x)
    rule3528 = ReplacementRule(pattern3528, replacement3528)
    pattern3529 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1440, cons1539)
    def replacement3529(m, f, b, d, a, x, e):
        rubi.append(3529)
        return -Dist(d**S(2)/b**S(2), Int((d/cos(e + f*x))**(m + S(-2))*(a - b*tan(e + f*x)), x), x) + Dist(d**S(2)*(a**S(2) + b**S(2))/b**S(2), Int((d/cos(e + f*x))**(m + S(-2))/(a + b*tan(e + f*x)), x), x)
    rule3529 = ReplacementRule(pattern3529, replacement3529)
    pattern3530 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1440, cons1539)
    def replacement3530(m, f, b, d, a, x, e):
        rubi.append(3530)
        return -Dist(d**S(2)/b**S(2), Int((d/sin(e + f*x))**(m + S(-2))*(a - b/tan(e + f*x)), x), x) + Dist(d**S(2)*(a**S(2) + b**S(2))/b**S(2), Int((d/sin(e + f*x))**(m + S(-2))/(a + b/tan(e + f*x)), x), x)
    rule3530 = ReplacementRule(pattern3530, replacement3530)
    pattern3531 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1440, cons84)
    def replacement3531(m, f, b, d, a, x, e):
        rubi.append(3531)
        return Dist(b**S(2)/(d**S(2)*(a**S(2) + b**S(2))), Int((d/cos(e + f*x))**(m + S(2))/(a + b*tan(e + f*x)), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int((d/cos(e + f*x))**m*(a - b*tan(e + f*x)), x), x)
    rule3531 = ReplacementRule(pattern3531, replacement3531)
    pattern3532 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1440, cons84)
    def replacement3532(m, f, b, d, a, x, e):
        rubi.append(3532)
        return Dist(b**S(2)/(d**S(2)*(a**S(2) + b**S(2))), Int((d/sin(e + f*x))**(m + S(2))/(a + b/tan(e + f*x)), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int((d/sin(e + f*x))**m*(a - b/tan(e + f*x)), x), x)
    rule3532 = ReplacementRule(pattern3532, replacement3532)
    pattern3533 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1440, cons1524)
    def replacement3533(m, f, b, d, a, n, x, e):
        rubi.append(3533)
        return Dist(d**(S(2)*IntPart(m/S(2)))*(d/cos(e + f*x))**(S(2)*FracPart(m/S(2)))*(cos(e + f*x)**(S(-2)))**(-FracPart(m/S(2)))/(b*f), Subst(Int((S(1) + x**S(2)/b**S(2))**(m/S(2) + S(-1))*(a + x)**n, x), x, b*tan(e + f*x)), x)
    rule3533 = ReplacementRule(pattern3533, replacement3533)
    pattern3534 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1440, cons1524)
    def replacement3534(m, f, b, d, a, n, x, e):
        rubi.append(3534)
        return -Dist(d**(S(2)*IntPart(m/S(2)))*(d/sin(e + f*x))**(S(2)*FracPart(m/S(2)))*(sin(e + f*x)**(S(-2)))**(-FracPart(m/S(2)))/(b*f), Subst(Int((S(1) + x**S(2)/b**S(2))**(m/S(2) + S(-1))*(a + x)**n, x), x, b/tan(e + f*x)), x)
    rule3534 = ReplacementRule(pattern3534, replacement3534)
    pattern3535 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1439)
    def replacement3535(f, b, d, a, x, e):
        rubi.append(3535)
        return Dist(-S(4)*b/f, Subst(Int(x**S(2)/(a**S(2)*d**S(2) + x**S(4)), x), x, sqrt(d*cos(e + f*x))*sqrt(a + b*tan(e + f*x))), x)
    rule3535 = ReplacementRule(pattern3535, replacement3535)
    pattern3536 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1439)
    def replacement3536(f, b, d, a, x, e):
        rubi.append(3536)
        return Dist(S(4)*b/f, Subst(Int(x**S(2)/(a**S(2)*d**S(2) + x**S(4)), x), x, sqrt(d*sin(e + f*x))*sqrt(a + b/tan(e + f*x))), x)
    rule3536 = ReplacementRule(pattern3536, replacement3536)
    pattern3537 = Pattern(Integral(S(1)/((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1439)
    def replacement3537(f, b, d, a, x, e):
        rubi.append(3537)
        return Dist(S(1)/(d*sqrt(a - b*tan(e + f*x))*sqrt(a + b*tan(e + f*x))*cos(e + f*x)), Int(sqrt(a - b*tan(e + f*x))/sqrt(d*cos(e + f*x)), x), x)
    rule3537 = ReplacementRule(pattern3537, replacement3537)
    pattern3538 = Pattern(Integral(S(1)/((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1439)
    def replacement3538(f, b, d, a, x, e):
        rubi.append(3538)
        return Dist(S(1)/(d*sqrt(a - b/tan(e + f*x))*sqrt(a + b/tan(e + f*x))*sin(e + f*x)), Int(sqrt(a - b/tan(e + f*x))/sqrt(d*sin(e + f*x)), x), x)
    rule3538 = ReplacementRule(pattern3538, replacement3538)
    pattern3539 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons18)
    def replacement3539(m, f, b, d, a, n, x, e):
        rubi.append(3539)
        return Dist((d/cos(e + f*x))**m*(d*cos(e + f*x))**m, Int((d/cos(e + f*x))**(-m)*(a + b*tan(e + f*x))**n, x), x)
    rule3539 = ReplacementRule(pattern3539, replacement3539)
    pattern3540 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons18)
    def replacement3540(m, f, b, d, a, n, x, e):
        rubi.append(3540)
        return Dist((d/sin(e + f*x))**m*(d*sin(e + f*x))**m, Int((d/sin(e + f*x))**(-m)*(a + b/tan(e + f*x))**n, x), x)
    rule3540 = ReplacementRule(pattern3540, replacement3540)
    pattern3541 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**m_, x_), cons2, cons3, cons48, cons125, cons4, cons1515)
    def replacement3541(m, f, b, a, n, x, e):
        rubi.append(3541)
        return Dist(b/f, Subst(Int(x**m*(a + x)**n*(b**S(2) + x**S(2))**(-m/S(2) + S(-1)), x), x, b*tan(e + f*x)), x)
    rule3541 = ReplacementRule(pattern3541, replacement3541)
    pattern3542 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**m_, x_), cons2, cons3, cons48, cons125, cons4, cons1515)
    def replacement3542(m, f, b, a, n, x, e):
        rubi.append(3542)
        return -Dist(b/f, Subst(Int(x**m*(a + x)**n*(b**S(2) + x**S(2))**(-m/S(2) + S(-1)), x), x, b/tan(e + f*x)), x)
    rule3542 = ReplacementRule(pattern3542, replacement3542)
    pattern3543 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons1228, cons148)
    def replacement3543(m, f, b, a, n, x, e):
        rubi.append(3543)
        return Int((a + b*tan(e + f*x))**n*sin(e + f*x)**m, x)
    rule3543 = ReplacementRule(pattern3543, replacement3543)
    pattern3544 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons1228, cons148)
    def replacement3544(m, f, b, a, n, x, e):
        rubi.append(3544)
        return Int((a + b/tan(e + f*x))**n*cos(e + f*x)**m, x)
    rule3544 = ReplacementRule(pattern3544, replacement3544)
    pattern3545 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons1228, cons196, cons1540)
    def replacement3545(m, f, b, a, n, x, e):
        rubi.append(3545)
        return Int((a*cos(e + f*x) + b*sin(e + f*x))**n*sin(e + f*x)**m*cos(e + f*x)**(-n), x)
    rule3545 = ReplacementRule(pattern3545, replacement3545)
    pattern3546 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons1228, cons196, cons1540)
    def replacement3546(m, f, b, a, n, x, e):
        rubi.append(3546)
        return Int((a*sin(e + f*x) + b*cos(e + f*x))**n*sin(e + f*x)**(-n)*cos(e + f*x)**m, x)
    rule3546 = ReplacementRule(pattern3546, replacement3546)
    pattern3547 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons18)
    def replacement3547(m, f, b, d, a, n, x, e):
        rubi.append(3547)
        return Dist((sin(e + f*x)/d)**FracPart(m)*(d/sin(e + f*x))**FracPart(m), Int((sin(e + f*x)/d)**(-m)*(a + b*tan(e + f*x))**n, x), x)
    rule3547 = ReplacementRule(pattern3547, replacement3547)
    pattern3548 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons18)
    def replacement3548(m, f, b, d, a, n, x, e):
        rubi.append(3548)
        return Dist((cos(e + f*x)/d)**FracPart(m)*(d/cos(e + f*x))**FracPart(m), Int((cos(e + f*x)/d)**(-m)*(a + b/tan(e + f*x))**n, x), x)
    rule3548 = ReplacementRule(pattern3548, replacement3548)
    pattern3549 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons5, cons85)
    def replacement3549(p, m, f, b, a, n, x, e):
        rubi.append(3549)
        return Int((a*cos(e + f*x) + b*sin(e + f*x))**n*sin(e + f*x)**p*cos(e + f*x)**(m - n), x)
    rule3549 = ReplacementRule(pattern3549, replacement3549)
    pattern3550 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons5, cons85)
    def replacement3550(p, m, f, b, a, n, x, e):
        rubi.append(3550)
        return Int((a*sin(e + f*x) + b*cos(e + f*x))**n*sin(e + f*x)**(m - n)*cos(e + f*x)**p, x)
    rule3550 = ReplacementRule(pattern3550, replacement3550)
    pattern3551 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1439, cons17, cons1541)
    def replacement3551(m, f, b, d, a, n, c, x, e):
        rubi.append(3551)
        return Dist(a**m*c**m, Int((c + d*tan(e + f*x))**(-m + n)*(S(1)/cos(e + f*x))**(S(2)*m), x), x)
    rule3551 = ReplacementRule(pattern3551, replacement3551)
    pattern3552 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1439, cons17, cons1541)
    def replacement3552(m, f, b, d, a, n, c, x, e):
        rubi.append(3552)
        return Dist(a**m*c**m, Int((c + d/tan(e + f*x))**(-m + n)*(S(1)/sin(e + f*x))**(S(2)*m), x), x)
    rule3552 = ReplacementRule(pattern3552, replacement3552)
    pattern3553 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1439)
    def replacement3553(m, f, b, d, a, c, n, x, e):
        rubi.append(3553)
        return Dist(a*c/f, Subst(Int((a + b*x)**(m + S(-1))*(c + d*x)**(n + S(-1)), x), x, tan(e + f*x)), x)
    rule3553 = ReplacementRule(pattern3553, replacement3553)
    pattern3554 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1439)
    def replacement3554(m, f, b, d, a, c, n, x, e):
        rubi.append(3554)
        return -Dist(a*c/f, Subst(Int((a + b*x)**(m + S(-1))*(c + d*x)**(n + S(-1)), x), x, S(1)/tan(e + f*x)), x)
    rule3554 = ReplacementRule(pattern3554, replacement3554)
    pattern3555 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons70)
    def replacement3555(f, b, d, a, c, x, e):
        rubi.append(3555)
        return Simp(x*(a*c - b*d), x) + Simp(b*d*tan(e + f*x)/f, x)
    rule3555 = ReplacementRule(pattern3555, replacement3555)
    pattern3556 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons70)
    def replacement3556(f, b, d, a, c, x, e):
        rubi.append(3556)
        return Simp(x*(a*c - b*d), x) - Simp(b*d/(f*tan(e + f*x)), x)
    rule3556 = ReplacementRule(pattern3556, replacement3556)
    pattern3557 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1412)
    def replacement3557(f, b, d, c, a, x, e):
        rubi.append(3557)
        return Dist(a*d + b*c, Int(tan(e + f*x), x), x) + Simp(x*(a*c - b*d), x) + Simp(b*d*tan(e + f*x)/f, x)
    rule3557 = ReplacementRule(pattern3557, replacement3557)
    pattern3558 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1412)
    def replacement3558(f, b, d, c, a, x, e):
        rubi.append(3558)
        return Dist(a*d + b*c, Int(S(1)/tan(e + f*x), x), x) + Simp(x*(a*c - b*d), x) - Simp(b*d/(f*tan(e + f*x)), x)
    rule3558 = ReplacementRule(pattern3558, replacement3558)
    pattern3559 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons31, cons267)
    def replacement3559(m, f, b, d, c, a, x, e):
        rubi.append(3559)
        return Dist((a*d + b*c)/(S(2)*a*b), Int((a + b*tan(e + f*x))**(m + S(1)), x), x) - Simp((a + b*tan(e + f*x))**m*(-a*d + b*c)/(S(2)*a*f*m), x)
    rule3559 = ReplacementRule(pattern3559, replacement3559)
    pattern3560 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons31, cons267)
    def replacement3560(m, f, b, d, c, a, x, e):
        rubi.append(3560)
        return Dist((a*d + b*c)/(S(2)*a*b), Int((a + b/tan(e + f*x))**(m + S(1)), x), x) + Simp((a + b/tan(e + f*x))**m*(-a*d + b*c)/(S(2)*a*f*m), x)
    rule3560 = ReplacementRule(pattern3560, replacement3560)
    pattern3561 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1439, cons1303)
    def replacement3561(m, f, b, d, c, a, x, e):
        rubi.append(3561)
        return Dist((a*d + b*c)/b, Int((a + b*tan(e + f*x))**m, x), x) + Simp(d*(a + b*tan(e + f*x))**m/(f*m), x)
    rule3561 = ReplacementRule(pattern3561, replacement3561)
    pattern3562 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1439, cons1303)
    def replacement3562(m, f, b, d, c, a, x, e):
        rubi.append(3562)
        return Dist((a*d + b*c)/b, Int((a + b/tan(e + f*x))**m, x), x) - Simp(d*(a + b/tan(e + f*x))**m/(f*m), x)
    rule3562 = ReplacementRule(pattern3562, replacement3562)
    pattern3563 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons31, cons168)
    def replacement3563(m, f, b, d, c, a, x, e):
        rubi.append(3563)
        return Int((a + b*tan(e + f*x))**(m + S(-1))*Simp(a*c - b*d + (a*d + b*c)*tan(e + f*x), x), x) + Simp(d*(a + b*tan(e + f*x))**m/(f*m), x)
    rule3563 = ReplacementRule(pattern3563, replacement3563)
    pattern3564 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons31, cons168)
    def replacement3564(m, f, b, d, c, a, x, e):
        rubi.append(3564)
        return Int((a + b/tan(e + f*x))**(m + S(-1))*Simp(a*c - b*d + (a*d + b*c)/tan(e + f*x), x), x) - Simp(d*(a + b/tan(e + f*x))**m/(f*m), x)
    rule3564 = ReplacementRule(pattern3564, replacement3564)
    pattern3565 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons31, cons94)
    def replacement3565(m, f, b, d, c, a, x, e):
        rubi.append(3565)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(a*c + b*d - (-a*d + b*c)*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(1))*(-a*d + b*c)/(f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3565 = ReplacementRule(pattern3565, replacement3565)
    pattern3566 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons31, cons94)
    def replacement3566(m, f, b, d, c, a, x, e):
        rubi.append(3566)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(a*c + b*d - (-a*d + b*c)/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(1))*(-a*d + b*c)/(f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3566 = ReplacementRule(pattern3566, replacement3566)
    pattern3567 = Pattern(Integral((c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1542)
    def replacement3567(f, b, d, a, c, x, e):
        rubi.append(3567)
        return Simp(c*log(RemoveContent(a*cos(e + f*x) + b*sin(e + f*x), x))/(b*f), x)
    rule3567 = ReplacementRule(pattern3567, replacement3567)
    pattern3568 = Pattern(Integral((c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1542)
    def replacement3568(f, b, d, a, c, x, e):
        rubi.append(3568)
        return -Simp(c*log(RemoveContent(a*sin(e + f*x) + b*cos(e + f*x), x))/(b*f), x)
    rule3568 = ReplacementRule(pattern3568, replacement3568)
    pattern3569 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1543)
    def replacement3569(f, b, d, c, a, x, e):
        rubi.append(3569)
        return Dist((-a*d + b*c)/(a**S(2) + b**S(2)), Int((-a*tan(e + f*x) + b)/(a + b*tan(e + f*x)), x), x) + Simp(x*(a*c + b*d)/(a**S(2) + b**S(2)), x)
    rule3569 = ReplacementRule(pattern3569, replacement3569)
    pattern3570 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1543)
    def replacement3570(f, b, d, c, a, x, e):
        rubi.append(3570)
        return Dist((-a*d + b*c)/(a**S(2) + b**S(2)), Int((-a/tan(e + f*x) + b)/(a + b/tan(e + f*x)), x), x) + Simp(x*(a*c + b*d)/(a**S(2) + b**S(2)), x)
    rule3570 = ReplacementRule(pattern3570, replacement3570)
    pattern3571 = Pattern(Integral((c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1322)
    def replacement3571(f, b, d, c, x, e):
        rubi.append(3571)
        return Dist(-S(2)*d**S(2)/f, Subst(Int(S(1)/(b*x**S(2) + S(2)*c*d), x), x, (c - d*tan(e + f*x))/sqrt(b*tan(e + f*x))), x)
    rule3571 = ReplacementRule(pattern3571, replacement3571)
    pattern3572 = Pattern(Integral((c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1322)
    def replacement3572(f, b, d, c, x, e):
        rubi.append(3572)
        return Dist(S(2)*d**S(2)/f, Subst(Int(S(1)/(b*x**S(2) + S(2)*c*d), x), x, (c - d/tan(e + f*x))/sqrt(b/tan(e + f*x))), x)
    rule3572 = ReplacementRule(pattern3572, replacement3572)
    pattern3573 = Pattern(Integral((c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1544)
    def replacement3573(f, b, d, c, x, e):
        rubi.append(3573)
        return Dist(S(2)*c**S(2)/f, Subst(Int(S(1)/(b*c - d*x**S(2)), x), x, sqrt(b*tan(e + f*x))), x)
    rule3573 = ReplacementRule(pattern3573, replacement3573)
    pattern3574 = Pattern(Integral((c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1544)
    def replacement3574(f, b, d, c, x, e):
        rubi.append(3574)
        return Dist(-S(2)*c**S(2)/f, Subst(Int(S(1)/(b*c - d*x**S(2)), x), x, sqrt(b/tan(e + f*x))), x)
    rule3574 = ReplacementRule(pattern3574, replacement3574)
    pattern3575 = Pattern(Integral((c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1323, cons1545)
    def replacement3575(f, b, d, c, x, e):
        rubi.append(3575)
        return Dist(S(2)/f, Subst(Int((b*c + d*x**S(2))/(b**S(2) + x**S(4)), x), x, sqrt(b*tan(e + f*x))), x)
    rule3575 = ReplacementRule(pattern3575, replacement3575)
    pattern3576 = Pattern(Integral((c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1323, cons1545)
    def replacement3576(f, b, d, c, x, e):
        rubi.append(3576)
        return Dist(-S(2)/f, Subst(Int((b*c + d*x**S(2))/(b**S(2) + x**S(4)), x), x, sqrt(b/tan(e + f*x))), x)
    rule3576 = ReplacementRule(pattern3576, replacement3576)
    pattern3577 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons1546)
    def replacement3577(f, b, d, c, a, x, e):
        rubi.append(3577)
        return Dist(-S(2)*d**S(2)/f, Subst(Int(S(1)/(-S(4)*a*d**S(2) + S(2)*b*c*d + x**S(2)), x), x, (-S(2)*a*d + b*c - b*d*tan(e + f*x))/sqrt(a + b*tan(e + f*x))), x)
    rule3577 = ReplacementRule(pattern3577, replacement3577)
    pattern3578 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons1546)
    def replacement3578(f, b, d, c, a, x, e):
        rubi.append(3578)
        return Dist(S(2)*d**S(2)/f, Subst(Int(S(1)/(-S(4)*a*d**S(2) + S(2)*b*c*d + x**S(2)), x), x, (-S(2)*a*d + b*c - b*d/tan(e + f*x))/sqrt(a + b/tan(e + f*x))), x)
    rule3578 = ReplacementRule(pattern3578, replacement3578)
    def With3579(f, b, d, c, a, x, e):
        q = Rt(a**S(2) + b**S(2), S(2))
        rubi.append(3579)
        return -Dist(S(1)/(S(2)*q), Int((a*c + b*d - c*q + (-a*d + b*c - d*q)*tan(e + f*x))/sqrt(a + b*tan(e + f*x)), x), x) + Dist(S(1)/(S(2)*q), Int((a*c + b*d + c*q + (-a*d + b*c + d*q)*tan(e + f*x))/sqrt(a + b*tan(e + f*x)), x), x)
    pattern3579 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons1547, cons1548)
    rule3579 = ReplacementRule(pattern3579, With3579)
    def With3580(f, b, d, c, a, x, e):
        q = Rt(a**S(2) + b**S(2), S(2))
        rubi.append(3580)
        return -Dist(S(1)/(S(2)*q), Int((a*c + b*d - c*q + (-a*d + b*c - d*q)/tan(e + f*x))/sqrt(a + b/tan(e + f*x)), x), x) + Dist(S(1)/(S(2)*q), Int((a*c + b*d + c*q + (-a*d + b*c + d*q)/tan(e + f*x))/sqrt(a + b/tan(e + f*x)), x), x)
    pattern3580 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons1547, cons1548)
    rule3580 = ReplacementRule(pattern3580, With3580)
    pattern3581 = Pattern(Integral((c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1440, cons1544)
    def replacement3581(m, f, b, d, a, c, x, e):
        rubi.append(3581)
        return Dist(c*d/f, Subst(Int((a + b*x/d)**m/(c*x + d**S(2)), x), x, d*tan(e + f*x)), x)
    rule3581 = ReplacementRule(pattern3581, replacement3581)
    pattern3582 = Pattern(Integral((c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1440, cons1544)
    def replacement3582(m, f, b, d, a, c, x, e):
        rubi.append(3582)
        return -Dist(c*d/f, Subst(Int((a + b*x/d)**m/(c*x + d**S(2)), x), x, d/tan(e + f*x)), x)
    rule3582 = ReplacementRule(pattern3582, replacement3582)
    pattern3583 = Pattern(Integral((WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons21, cons1545, cons77)
    def replacement3583(m, f, b, d, c, x, e):
        rubi.append(3583)
        return Dist(c, Int((b*tan(e + f*x))**m, x), x) + Dist(d/b, Int((b*tan(e + f*x))**(m + S(1)), x), x)
    rule3583 = ReplacementRule(pattern3583, replacement3583)
    pattern3584 = Pattern(Integral((WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons21, cons1545, cons77)
    def replacement3584(m, f, b, d, c, x, e):
        rubi.append(3584)
        return Dist(c, Int((b/tan(e + f*x))**m, x), x) + Dist(d/b, Int((b/tan(e + f*x))**(m + S(1)), x), x)
    rule3584 = ReplacementRule(pattern3584, replacement3584)
    pattern3585 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1440, cons1545, cons18)
    def replacement3585(m, f, b, d, c, a, x, e):
        rubi.append(3585)
        return Dist(c/S(2) - I*d/S(2), Int((a + b*tan(e + f*x))**m*(I*tan(e + f*x) + S(1)), x), x) + Dist(c/S(2) + I*d/S(2), Int((a + b*tan(e + f*x))**m*(-I*tan(e + f*x) + S(1)), x), x)
    rule3585 = ReplacementRule(pattern3585, replacement3585)
    pattern3586 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1440, cons1545, cons18)
    def replacement3586(m, f, b, d, c, a, x, e):
        rubi.append(3586)
        return Dist(c/S(2) - I*d/S(2), Int((S(1) + I/tan(e + f*x))*(a + b/tan(e + f*x))**m, x), x) + Dist(c/S(2) + I*d/S(2), Int((S(1) - I/tan(e + f*x))*(a + b/tan(e + f*x))**m, x), x)
    rule3586 = ReplacementRule(pattern3586, replacement3586)
    pattern3587 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons32, cons1439)
    def replacement3587(m, f, b, d, c, a, x, e):
        rubi.append(3587)
        return Dist(S(1)/(S(2)*a**S(2)), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(a*c**S(2) + a*d**S(2) - S(2)*b*c*d - S(2)*b*d**S(2)*tan(e + f*x), x), x), x) - Simp(b*(a + b*tan(e + f*x))**m*(a*c + b*d)**S(2)/(S(2)*a**S(3)*f*m), x)
    rule3587 = ReplacementRule(pattern3587, replacement3587)
    pattern3588 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons32, cons1439)
    def replacement3588(m, f, b, d, c, a, x, e):
        rubi.append(3588)
        return Dist(S(1)/(S(2)*a**S(2)), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(a*c**S(2) + a*d**S(2) - S(2)*b*c*d - S(2)*b*d**S(2)/tan(e + f*x), x), x), x) + Simp(b*(a + b/tan(e + f*x))**m*(a*c + b*d)**S(2)/(S(2)*a**S(3)*f*m), x)
    rule3588 = ReplacementRule(pattern3588, replacement3588)
    pattern3589 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2)/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440)
    def replacement3589(f, b, d, c, a, x, e):
        rubi.append(3589)
        return Dist((-a*d + b*c)**S(2)/b**S(2), Int(S(1)/(a + b*tan(e + f*x)), x), x) + Dist(d**S(2)/b, Int(tan(e + f*x), x), x) + Simp(d*x*(-a*d + S(2)*b*c)/b**S(2), x)
    rule3589 = ReplacementRule(pattern3589, replacement3589)
    pattern3590 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2)/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440)
    def replacement3590(f, b, d, c, a, x, e):
        rubi.append(3590)
        return Dist((-a*d + b*c)**S(2)/b**S(2), Int(S(1)/(a + b/tan(e + f*x)), x), x) + Dist(d**S(2)/b, Int(S(1)/tan(e + f*x), x), x) + Simp(d*x*(-a*d + S(2)*b*c)/b**S(2), x)
    rule3590 = ReplacementRule(pattern3590, replacement3590)
    pattern3591 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons94, cons1440)
    def replacement3591(m, f, b, d, c, a, x, e):
        rubi.append(3591)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(a*c**S(2) - a*d**S(2) + S(2)*b*c*d - (-S(2)*a*c*d + b*c**S(2) - b*d**S(2))*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(1))*(-a*d + b*c)**S(2)/(b*f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3591 = ReplacementRule(pattern3591, replacement3591)
    pattern3592 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons94, cons1440)
    def replacement3592(m, f, b, d, c, a, x, e):
        rubi.append(3592)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(a*c**S(2) - a*d**S(2) + S(2)*b*c*d - (-S(2)*a*c*d + b*c**S(2) - b*d**S(2))/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(1))*(-a*d + b*c)**S(2)/(b*f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3592 = ReplacementRule(pattern3592, replacement3592)
    pattern3593 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1549, cons1550)
    def replacement3593(m, f, b, d, c, a, x, e):
        rubi.append(3593)
        return Int((a + b*tan(e + f*x))**m*Simp(c**S(2) + S(2)*c*d*tan(e + f*x) - d**S(2), x), x) + Simp(d**S(2)*(a + b*tan(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule3593 = ReplacementRule(pattern3593, replacement3593)
    pattern3594 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1549, cons1550)
    def replacement3594(m, f, b, d, c, a, x, e):
        rubi.append(3594)
        return Int((a + b/tan(e + f*x))**m*Simp(c**S(2) + S(2)*c*d/tan(e + f*x) - d**S(2), x), x) - Simp(d**S(2)*(a + b/tan(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule3594 = ReplacementRule(pattern3594, replacement3594)
    pattern3595 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3595(f, b, d, c, a, x, e):
        rubi.append(3595)
        return Dist(-S(2)*a*b/f, Subst(Int(S(1)/(-S(2)*a**S(2)*x**S(2) + a*c - b*d), x), x, sqrt(c + d*tan(e + f*x))/sqrt(a + b*tan(e + f*x))), x)
    rule3595 = ReplacementRule(pattern3595, replacement3595)
    pattern3596 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3596(f, b, d, c, a, x, e):
        rubi.append(3596)
        return Dist(S(2)*a*b/f, Subst(Int(S(1)/(-S(2)*a**S(2)*x**S(2) + a*c - b*d), x), x, sqrt(c + d/tan(e + f*x))/sqrt(a + b/tan(e + f*x))), x)
    rule3596 = ReplacementRule(pattern3596, replacement3596)
    pattern3597 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons1551, cons1423)
    def replacement3597(m, f, b, d, c, a, n, x, e):
        rubi.append(3597)
        return Dist(S(2)*a**S(2)/(a*c - b*d), Int((a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(1)), x), x) + Simp(a*b*(a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(1))/(f*(m + S(-1))*(a*c - b*d)), x)
    rule3597 = ReplacementRule(pattern3597, replacement3597)
    pattern3598 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons1551, cons1423)
    def replacement3598(m, f, b, d, c, n, a, x, e):
        rubi.append(3598)
        return Dist(S(2)*a**S(2)/(a*c - b*d), Int((a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(1)), x), x) - Simp(a*b*(a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(1))/(f*(m + S(-1))*(a*c - b*d)), x)
    rule3598 = ReplacementRule(pattern3598, replacement3598)
    pattern3599 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons1551, cons1385)
    def replacement3599(m, f, b, d, c, a, n, x, e):
        rubi.append(3599)
        return -Dist((a*c - b*d)/(S(2)*b**S(2)), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(-1)), x), x) + Simp(a*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n/(S(2)*b*f*m), x)
    rule3599 = ReplacementRule(pattern3599, replacement3599)
    pattern3600 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons1551, cons1385)
    def replacement3600(m, f, b, d, c, n, a, x, e):
        rubi.append(3600)
        return -Dist((a*c - b*d)/(S(2)*b**S(2)), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(-1)), x), x) - Simp(a*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n/(S(2)*b*f*m), x)
    rule3600 = ReplacementRule(pattern3600, replacement3600)
    pattern3601 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons111, cons94)
    def replacement3601(m, f, b, d, c, a, n, x, e):
        rubi.append(3601)
        return Dist(S(1)/(S(2)*a), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n, x), x) + Simp(a*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))/(S(2)*f*m*(-a*d + b*c)), x)
    rule3601 = ReplacementRule(pattern3601, replacement3601)
    pattern3602 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons111, cons94)
    def replacement3602(m, f, b, d, c, n, a, x, e):
        rubi.append(3602)
        return Dist(S(1)/(S(2)*a), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n, x), x) - Simp(a*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))/(S(2)*f*m*(-a*d + b*c)), x)
    rule3602 = ReplacementRule(pattern3602, replacement3602)
    pattern3603 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1439, cons1545, cons155, cons272)
    def replacement3603(m, f, b, d, c, a, n, x, e):
        rubi.append(3603)
        return Dist(a/(a*c - b*d), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1)), x), x) - Simp(d*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))/(f*m*(c**S(2) + d**S(2))), x)
    rule3603 = ReplacementRule(pattern3603, replacement3603)
    pattern3604 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1439, cons1545, cons155, cons272)
    def replacement3604(m, f, b, d, c, n, a, x, e):
        rubi.append(3604)
        return Dist(a/(a*c - b*d), Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1)), x), x) + Simp(d*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))/(f*m*(c**S(2) + d**S(2))), x)
    rule3604 = ReplacementRule(pattern3604, replacement3604)
    pattern3605 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons87, cons1325)
    def replacement3605(f, b, d, c, a, n, x, e):
        rubi.append(3605)
        return Dist(S(1)/(S(2)*a*(-a*d + b*c)), Int((c + d*tan(e + f*x))**(n + S(-1))*Simp(a*c*d*(n + S(-1)) + b*c**S(2) + b*d**S(2)*n - d*(n + S(-1))*(-a*d + b*c)*tan(e + f*x), x), x), x) - Simp((c + d*tan(e + f*x))**n*(a*c + b*d)/(S(2)*f*(a + b*tan(e + f*x))*(-a*d + b*c)), x)
    rule3605 = ReplacementRule(pattern3605, replacement3605)
    pattern3606 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons87, cons1325)
    def replacement3606(f, b, d, c, n, a, x, e):
        rubi.append(3606)
        return Dist(S(1)/(S(2)*a*(-a*d + b*c)), Int((c + d/tan(e + f*x))**(n + S(-1))*Simp(a*c*d*(n + S(-1)) + b*c**S(2) + b*d**S(2)*n - d*(n + S(-1))*(-a*d + b*c)/tan(e + f*x), x), x), x) + Simp((c + d/tan(e + f*x))**n*(a*c + b*d)/(S(2)*f*(a + b/tan(e + f*x))*(-a*d + b*c)), x)
    rule3606 = ReplacementRule(pattern3606, replacement3606)
    pattern3607 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons87, cons165)
    def replacement3607(f, b, d, c, a, n, x, e):
        rubi.append(3607)
        return Dist(S(1)/(S(2)*a**S(2)), Int((c + d*tan(e + f*x))**(n + S(-2))*Simp(a*c**S(2) + a*d**S(2)*(n + S(-1)) - b*c*d*n - d*(a*c*(n + S(-2)) + b*d*n)*tan(e + f*x), x), x), x) + Simp((c + d*tan(e + f*x))**(n + S(-1))*(-a*d + b*c)/(S(2)*a*f*(a + b*tan(e + f*x))), x)
    rule3607 = ReplacementRule(pattern3607, replacement3607)
    pattern3608 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons87, cons165)
    def replacement3608(f, b, d, c, n, a, x, e):
        rubi.append(3608)
        return Dist(S(1)/(S(2)*a**S(2)), Int((c + d/tan(e + f*x))**(n + S(-2))*Simp(a*c**S(2) + a*d**S(2)*(n + S(-1)) - b*c*d*n - d*(a*c*(n + S(-2)) + b*d*n)/tan(e + f*x), x), x), x) - Simp((c + d/tan(e + f*x))**(n + S(-1))*(-a*d + b*c)/(S(2)*a*f*(a + b/tan(e + f*x))), x)
    rule3608 = ReplacementRule(pattern3608, replacement3608)
    pattern3609 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3609(f, b, d, c, a, x, e):
        rubi.append(3609)
        return Dist(b/(-a*d + b*c), Int(S(1)/(a + b*tan(e + f*x)), x), x) - Dist(d/(-a*d + b*c), Int(S(1)/(c + d*tan(e + f*x)), x), x)
    rule3609 = ReplacementRule(pattern3609, replacement3609)
    pattern3610 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3610(f, b, d, c, a, x, e):
        rubi.append(3610)
        return Dist(b/(-a*d + b*c), Int(S(1)/(a + b/tan(e + f*x)), x), x) - Dist(d/(-a*d + b*c), Int(S(1)/(c + d/tan(e + f*x)), x), x)
    rule3610 = ReplacementRule(pattern3610, replacement3610)
    pattern3611 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1439, cons1545, cons1327)
    def replacement3611(f, b, d, c, a, n, x, e):
        rubi.append(3611)
        return Dist(S(1)/(S(2)*a*(-a*d + b*c)), Int((c + d*tan(e + f*x))**n*Simp(a*d*(n + S(-1)) + b*c - b*d*n*tan(e + f*x), x), x), x) - Simp(a*(c + d*tan(e + f*x))**(n + S(1))/(S(2)*f*(a + b*tan(e + f*x))*(-a*d + b*c)), x)
    rule3611 = ReplacementRule(pattern3611, replacement3611)
    pattern3612 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1439, cons1545, cons1327)
    def replacement3612(f, b, d, c, n, a, x, e):
        rubi.append(3612)
        return Dist(S(1)/(S(2)*a*(-a*d + b*c)), Int((c + d/tan(e + f*x))**n*Simp(a*d*(n + S(-1)) + b*c - b*d*n/tan(e + f*x), x), x), x) + Simp(a*(c + d/tan(e + f*x))**(n + S(1))/(S(2)*f*(a + b/tan(e + f*x))*(-a*d + b*c)), x)
    rule3612 = ReplacementRule(pattern3612, replacement3612)
    pattern3613 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons166, cons89, cons1334)
    def replacement3613(m, f, b, d, c, a, n, x, e):
        rubi.append(3613)
        return Dist(a/(d*(n + S(1))*(a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(-2))*(c + d*tan(e + f*x))**(n + S(1))*Simp(b*(-a*d*(m - S(2)*n + S(-4)) + b*c*(m + S(-2))) + (-a**S(2)*d*(m + n + S(-1)) + a*b*c*(m + S(-2)) + b**S(2)*d*(n + S(1)))*tan(e + f*x), x), x), x) - Simp(a**S(2)*(a + b*tan(e + f*x))**(m + S(-2))*(c + d*tan(e + f*x))**(n + S(1))*(-a*d + b*c)/(d*f*(n + S(1))*(a*d + b*c)), x)
    rule3613 = ReplacementRule(pattern3613, replacement3613)
    pattern3614 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons166, cons89, cons1334)
    def replacement3614(m, f, b, d, c, n, a, x, e):
        rubi.append(3614)
        return Dist(a/(d*(n + S(1))*(a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(-2))*(c + d/tan(e + f*x))**(n + S(1))*Simp(b*(-a*d*(m - S(2)*n + S(-4)) + b*c*(m + S(-2))) + (-a**S(2)*d*(m + n + S(-1)) + a*b*c*(m + S(-2)) + b**S(2)*d*(n + S(1)))/tan(e + f*x), x), x), x) + Simp(a**S(2)*(a + b/tan(e + f*x))**(m + S(-2))*(c + d/tan(e + f*x))**(n + S(1))*(-a*d + b*c)/(d*f*(n + S(1))*(a*d + b*c)), x)
    rule3614 = ReplacementRule(pattern3614, replacement3614)
    pattern3615 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3615(f, b, d, c, a, x, e):
        rubi.append(3615)
        return Dist(S(2)*a**S(2)/(a*c - b*d), Int(sqrt(a + b*tan(e + f*x)), x), x) - Dist((a*(c**S(2) - d**S(2)) + S(2)*b*c*d)/(a*(c**S(2) + d**S(2))), Int((a - b*tan(e + f*x))*sqrt(a + b*tan(e + f*x))/(c + d*tan(e + f*x)), x), x)
    rule3615 = ReplacementRule(pattern3615, replacement3615)
    pattern3616 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3616(f, b, d, c, a, x, e):
        rubi.append(3616)
        return Dist(S(2)*a**S(2)/(a*c - b*d), Int(sqrt(a + b/tan(e + f*x)), x), x) - Dist((a*(c**S(2) - d**S(2)) + S(2)*b*c*d)/(a*(c**S(2) + d**S(2))), Int((a - b/tan(e + f*x))*sqrt(a + b/tan(e + f*x))/(c + d/tan(e + f*x)), x), x)
    rule3616 = ReplacementRule(pattern3616, replacement3616)
    pattern3617 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3617(f, b, d, c, a, x, e):
        rubi.append(3617)
        return Dist(S(2)*a, Int(sqrt(a + b*tan(e + f*x))/sqrt(c + d*tan(e + f*x)), x), x) + Dist(b/a, Int(sqrt(a + b*tan(e + f*x))*(a*tan(e + f*x) + b)/sqrt(c + d*tan(e + f*x)), x), x)
    rule3617 = ReplacementRule(pattern3617, replacement3617)
    pattern3618 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3618(f, b, d, c, a, x, e):
        rubi.append(3618)
        return Dist(S(2)*a, Int(sqrt(a + b/tan(e + f*x))/sqrt(c + d/tan(e + f*x)), x), x) + Dist(b/a, Int(sqrt(a + b/tan(e + f*x))*(a/tan(e + f*x) + b)/sqrt(c + d/tan(e + f*x)), x), x)
    rule3618 = ReplacementRule(pattern3618, replacement3618)
    pattern3619 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1439, cons1545, cons515, cons166, cons1519, cons1334)
    def replacement3619(m, f, b, d, c, a, n, x, e):
        rubi.append(3619)
        return Dist(a/(d*(m + n + S(-1))), Int((a + b*tan(e + f*x))**(m + S(-2))*(c + d*tan(e + f*x))**n*Simp(a*d*(m + S(2)*n) + b*c*(m + S(-2)) + (a*c*(m + S(-2)) + b*d*(S(3)*m + S(2)*n + S(-4)))*tan(e + f*x), x), x), x) + Simp(b**S(2)*(a + b*tan(e + f*x))**(m + S(-2))*(c + d*tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(-1))), x)
    rule3619 = ReplacementRule(pattern3619, replacement3619)
    pattern3620 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1439, cons1545, cons515, cons166, cons1519, cons1334)
    def replacement3620(m, f, b, d, c, n, a, x, e):
        rubi.append(3620)
        return Dist(a/(d*(m + n + S(-1))), Int((a + b/tan(e + f*x))**(m + S(-2))*(c + d/tan(e + f*x))**n*Simp(a*d*(m + S(2)*n) + b*c*(m + S(-2)) + (a*c*(m + S(-2)) + b*d*(S(3)*m + S(2)*n + S(-4)))/tan(e + f*x), x), x), x) - Simp(b**S(2)*(a + b/tan(e + f*x))**(m + S(-2))*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(-1))), x)
    rule3620 = ReplacementRule(pattern3620, replacement3620)
    pattern3621 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sqrt(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons31, cons267, cons1552)
    def replacement3621(m, f, b, d, c, a, x, e):
        rubi.append(3621)
        return Dist(S(1)/(S(4)*a**S(2)*m), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(S(2)*a*c*m + a*d*(S(2)*m + S(1))*tan(e + f*x) + b*d, x)/sqrt(c + d*tan(e + f*x)), x), x) - Simp(b*(a + b*tan(e + f*x))**m*sqrt(c + d*tan(e + f*x))/(S(2)*a*f*m), x)
    rule3621 = ReplacementRule(pattern3621, replacement3621)
    pattern3622 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sqrt(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons31, cons267, cons1552)
    def replacement3622(m, f, b, d, c, a, x, e):
        rubi.append(3622)
        return Dist(S(1)/(S(4)*a**S(2)*m), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(S(2)*a*c*m + a*d*(S(2)*m + S(1))/tan(e + f*x) + b*d, x)/sqrt(c + d/tan(e + f*x)), x), x) + Simp(b*(a + b/tan(e + f*x))**m*sqrt(c + d/tan(e + f*x))/(S(2)*a*f*m), x)
    rule3622 = ReplacementRule(pattern3622, replacement3622)
    pattern3623 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons267, cons165, cons1334)
    def replacement3623(m, f, b, d, c, a, n, x, e):
        rubi.append(3623)
        return Dist(S(1)/(S(2)*a**S(2)*m), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(-2))*Simp(c*(a*c*m + b*d*(n + S(-1))) - d*(-a*c*(m + n + S(-1)) + b*d*(m - n + S(1)))*tan(e + f*x) - d*(a*d*(n + S(-1)) + b*c*m), x), x), x) - Simp((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(-1))*(-a*d + b*c)/(S(2)*a*f*m), x)
    rule3623 = ReplacementRule(pattern3623, replacement3623)
    pattern3624 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545, cons93, cons267, cons165, cons1334)
    def replacement3624(m, f, b, d, c, n, a, x, e):
        rubi.append(3624)
        return Dist(S(1)/(S(2)*a**S(2)*m), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(-2))*Simp(c*(a*c*m + b*d*(n + S(-1))) - d*(-a*c*(m + n + S(-1)) + b*d*(m - n + S(1)))/tan(e + f*x) - d*(a*d*(n + S(-1)) + b*c*m), x), x), x) + Simp((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(-1))*(-a*d + b*c)/(S(2)*a*f*m), x)
    rule3624 = ReplacementRule(pattern3624, replacement3624)
    pattern3625 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1439, cons1545, cons31, cons267, cons1334)
    def replacement3625(m, f, b, d, c, a, n, x, e):
        rubi.append(3625)
        return Dist(S(1)/(S(2)*a*m*(-a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n*Simp(-a*d*(S(2)*m + n + S(1)) + b*c*m + b*d*(m + n + S(1))*tan(e + f*x), x), x), x) + Simp(a*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))/(S(2)*f*m*(-a*d + b*c)), x)
    rule3625 = ReplacementRule(pattern3625, replacement3625)
    pattern3626 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1439, cons1545, cons31, cons267, cons1334)
    def replacement3626(m, f, b, d, c, n, a, x, e):
        rubi.append(3626)
        return Dist(S(1)/(S(2)*a*m*(-a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n*Simp(-a*d*(S(2)*m + n + S(1)) + b*c*m + b*d*(m + n + S(1))/tan(e + f*x), x), x), x) - Simp(a*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))/(S(2)*f*m*(-a*d + b*c)), x)
    rule3626 = ReplacementRule(pattern3626, replacement3626)
    pattern3627 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1439, cons1545, cons87, cons165, cons1519, cons1553)
    def replacement3627(m, f, b, d, c, a, n, x, e):
        rubi.append(3627)
        return -Dist(S(1)/(a*(m + n + S(-1))), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(-2))*Simp(-a*c**S(2)*(m + n + S(-1)) + d*(-a*c*(m + S(2)*n + S(-2)) + b*d*m)*tan(e + f*x) + d*(a*d*(n + S(-1)) + b*c*m), x), x), x) + Simp(d*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3627 = ReplacementRule(pattern3627, replacement3627)
    pattern3628 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1439, cons1545, cons87, cons165, cons1519, cons1553)
    def replacement3628(m, f, b, d, c, a, n, x, e):
        rubi.append(3628)
        return -Dist(S(1)/(a*(m + n + S(-1))), Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(-2))*Simp(-a*c**S(2)*(m + n + S(-1)) + d*(-a*c*(m + S(2)*n + S(-2)) + b*d*m)/tan(e + f*x) + d*(a*d*(n + S(-1)) + b*c*m), x), x), x) - Simp(d*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(-1))/(f*(m + n + S(-1))), x)
    rule3628 = ReplacementRule(pattern3628, replacement3628)
    pattern3629 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1439, cons1545, cons87, cons89, cons1553)
    def replacement3629(m, f, b, d, c, a, n, x, e):
        rubi.append(3629)
        return -Dist(S(1)/(a*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*Simp(-a*c*(n + S(1)) + a*d*(m + n + S(1))*tan(e + f*x) + b*d*m, x), x), x) + Simp(d*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))/(f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3629 = ReplacementRule(pattern3629, replacement3629)
    pattern3630 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1439, cons1545, cons87, cons89, cons1553)
    def replacement3630(m, f, b, d, c, n, a, x, e):
        rubi.append(3630)
        return -Dist(S(1)/(a*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*Simp(-a*c*(n + S(1)) + a*d*(m + n + S(1))/tan(e + f*x) + b*d*m, x), x), x) - Simp(d*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))/(f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3630 = ReplacementRule(pattern3630, replacement3630)
    pattern3631 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1439, cons1545)
    def replacement3631(m, f, b, d, c, a, x, e):
        rubi.append(3631)
        return Dist(a/(a*c - b*d), Int((a + b*tan(e + f*x))**m, x), x) - Dist(d/(a*c - b*d), Int((a + b*tan(e + f*x))**m*(a*tan(e + f*x) + b)/(c + d*tan(e + f*x)), x), x)
    rule3631 = ReplacementRule(pattern3631, replacement3631)
    pattern3632 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1439, cons1545)
    def replacement3632(m, f, b, d, c, a, x, e):
        rubi.append(3632)
        return Dist(a/(a*c - b*d), Int((a + b/tan(e + f*x))**m, x), x) - Dist(d/(a*c - b*d), Int((a + b/tan(e + f*x))**m*(a/tan(e + f*x) + b)/(c + d/tan(e + f*x)), x), x)
    rule3632 = ReplacementRule(pattern3632, replacement3632)
    pattern3633 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3633(f, b, d, c, a, x, e):
        rubi.append(3633)
        return Dist(d/a, Int(sqrt(a + b*tan(e + f*x))*(a*tan(e + f*x) + b)/sqrt(c + d*tan(e + f*x)), x), x) + Dist((a*c - b*d)/a, Int(sqrt(a + b*tan(e + f*x))/sqrt(c + d*tan(e + f*x)), x), x)
    rule3633 = ReplacementRule(pattern3633, replacement3633)
    pattern3634 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1439, cons1545)
    def replacement3634(f, b, d, c, a, x, e):
        rubi.append(3634)
        return Dist(d/a, Int(sqrt(a + b/tan(e + f*x))*(a/tan(e + f*x) + b)/sqrt(c + d/tan(e + f*x)), x), x) + Dist((a*c - b*d)/a, Int(sqrt(a + b/tan(e + f*x))/sqrt(c + d/tan(e + f*x)), x), x)
    rule3634 = ReplacementRule(pattern3634, replacement3634)
    pattern3635 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1439, cons1545)
    def replacement3635(m, f, b, d, c, a, n, x, e):
        rubi.append(3635)
        return Dist(a*b/f, Subst(Int((a + x)**(m + S(-1))*(c + d*x/b)**n/(a*x + b**S(2)), x), x, b*tan(e + f*x)), x)
    rule3635 = ReplacementRule(pattern3635, replacement3635)
    pattern3636 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1439, cons1545)
    def replacement3636(m, f, b, d, c, a, n, x, e):
        rubi.append(3636)
        return -Dist(a*b/f, Subst(Int((a + x)**(m + S(-1))*(c + d*x/b)**n/(a*x + b**S(2)), x), x, b/tan(e + f*x)), x)
    rule3636 = ReplacementRule(pattern3636, replacement3636)
    pattern3637 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons93, cons1333, cons89, cons515)
    def replacement3637(m, f, b, d, c, a, n, x, e):
        rubi.append(3637)
        return -Dist(S(1)/(d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b*tan(e + f*x))**(m + S(-3))*(c + d*tan(e + f*x))**(n + S(1))*Simp(a**S(2)*d*(-a*c*(n + S(1)) + b*d*(m + S(-2))) + b*(-S(2)*a*d + b*c)*(a*d*(n + S(1)) + b*c*(m + S(-2))) - b*(a*d*(-a*d + S(2)*b*c)*(m + n + S(-1)) - b**S(2)*(c**S(2)*(m + S(-2)) - d**S(2)*(n + S(1))))*tan(e + f*x)**S(2) - d*(n + S(1))*(-a**S(3)*d + S(3)*a**S(2)*b*c + S(3)*a*b**S(2)*d - b**S(3)*c)*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(-2))*(c + d*tan(e + f*x))**(n + S(1))*(-a*d + b*c)**S(2)/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3637 = ReplacementRule(pattern3637, replacement3637)
    pattern3638 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons93, cons1333, cons89, cons515)
    def replacement3638(m, f, b, d, c, a, n, x, e):
        rubi.append(3638)
        return -Dist(S(1)/(d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b/tan(e + f*x))**(m + S(-3))*(c + d/tan(e + f*x))**(n + S(1))*Simp(a**S(2)*d*(-a*c*(n + S(1)) + b*d*(m + S(-2))) + b*(-S(2)*a*d + b*c)*(a*d*(n + S(1)) + b*c*(m + S(-2))) - b*(a*d*(-a*d + S(2)*b*c)*(m + n + S(-1)) - b**S(2)*(c**S(2)*(m + S(-2)) - d**S(2)*(n + S(1))))/tan(e + f*x)**S(2) - d*(n + S(1))*(-a**S(3)*d + S(3)*a**S(2)*b*c + S(3)*a*b**S(2)*d - b**S(3)*c)/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(-2))*(c + d/tan(e + f*x))**(n + S(1))*(-a*d + b*c)**S(2)/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3638 = ReplacementRule(pattern3638, replacement3638)
    pattern3639 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1440, cons1545, cons515, cons1333, cons1554, cons1555)
    def replacement3639(m, f, b, d, c, a, n, x, e):
        rubi.append(3639)
        return Dist(S(1)/(d*(m + n + S(-1))), Int((a + b*tan(e + f*x))**(m + S(-3))*(c + d*tan(e + f*x))**n*Simp(a**S(3)*d*(m + n + S(-1)) - b**S(2)*(a*d*(n + S(1)) + b*c*(m + S(-2))) - b**S(2)*(-a*d*(S(3)*m + S(2)*n + S(-4)) + b*c*(m + S(-2)))*tan(e + f*x)**S(2) + b*d*(S(3)*a**S(2) - b**S(2))*(m + n + S(-1))*tan(e + f*x), x), x), x) + Simp(b**S(2)*(a + b*tan(e + f*x))**(m + S(-2))*(c + d*tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(-1))), x)
    rule3639 = ReplacementRule(pattern3639, replacement3639)
    pattern3640 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1440, cons1545, cons515, cons1333, cons1554, cons1555)
    def replacement3640(m, f, b, d, c, a, n, x, e):
        rubi.append(3640)
        return Dist(S(1)/(d*(m + n + S(-1))), Int((a + b/tan(e + f*x))**(m + S(-3))*(c + d/tan(e + f*x))**n*Simp(a**S(3)*d*(m + n + S(-1)) - b**S(2)*(a*d*(n + S(1)) + b*c*(m + S(-2))) - b**S(2)*(-a*d*(S(3)*m + S(2)*n + S(-4)) + b*c*(m + S(-2)))/tan(e + f*x)**S(2) + b*d*(S(3)*a**S(2) - b**S(2))*(m + n + S(-1))/tan(e + f*x), x), x), x) - Simp(b**S(2)*(a + b/tan(e + f*x))**(m + S(-2))*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(-1))), x)
    rule3640 = ReplacementRule(pattern3640, replacement3640)
    pattern3641 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons93, cons94, cons1336, cons515)
    def replacement3641(m, f, b, d, c, a, n, x, e):
        rubi.append(3641)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(-2))*Simp(a*c**S(2)*(m + S(1)) + a*d**S(2)*(n + S(-1)) + b*c*d*(m - n + S(2)) - d*(m + n)*(-a*d + b*c)*tan(e + f*x)**S(2) - (m + S(1))*(-S(2)*a*c*d + b*c**S(2) - b*d**S(2))*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(-1))*(-a*d + b*c)/(f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3641 = ReplacementRule(pattern3641, replacement3641)
    pattern3642 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons93, cons94, cons1336, cons515)
    def replacement3642(m, f, b, d, c, a, n, x, e):
        rubi.append(3642)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(-2))*Simp(a*c**S(2)*(m + S(1)) + a*d**S(2)*(n + S(-1)) + b*c*d*(m - n + S(2)) - d*(m + n)*(-a*d + b*c)/tan(e + f*x)**S(2) - (m + S(1))*(-S(2)*a*c*d + b*c**S(2) - b*d**S(2))/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(-1))*(-a*d + b*c)/(f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3642 = ReplacementRule(pattern3642, replacement3642)
    pattern3643 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons93, cons94, cons88, cons515)
    def replacement3643(m, f, b, d, c, a, n, x, e):
        rubi.append(3643)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(-1))*Simp(a*c*(m + S(1)) - b*d*n - b*d*(m + n + S(1))*tan(e + f*x)**S(2) - (m + S(1))*(-a*d + b*c)*tan(e + f*x), x), x), x) + Simp(b*(a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n/(f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3643 = ReplacementRule(pattern3643, replacement3643)
    pattern3644 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons93, cons94, cons88, cons515)
    def replacement3644(m, f, b, d, c, a, n, x, e):
        rubi.append(3644)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(-1))*Simp(a*c*(m + S(1)) - b*d*n - b*d*(m + n + S(1))/tan(e + f*x)**S(2) - (m + S(1))*(-a*d + b*c)/tan(e + f*x), x), x), x) - Simp(b*(a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n/(f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3644 = ReplacementRule(pattern3644, replacement3644)
    pattern3645 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1440, cons1545, cons515, cons94, cons1556, cons1557)
    def replacement3645(m, f, b, d, c, a, n, x, e):
        rubi.append(3645)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n*Simp(a*(m + S(1))*(-a*d + b*c) - b**S(2)*d*(m + n + S(2))*tan(e + f*x)**S(2) - b**S(2)*d*(m + n + S(2)) - b*(m + S(1))*(-a*d + b*c)*tan(e + f*x), x), x), x) + Simp(b**S(2)*(a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(1))/(f*(a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3645 = ReplacementRule(pattern3645, replacement3645)
    pattern3646 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1440, cons1545, cons515, cons94, cons1556, cons1557)
    def replacement3646(m, f, b, d, c, a, n, x, e):
        rubi.append(3646)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n*Simp(a*(m + S(1))*(-a*d + b*c) - b**S(2)*d*(m + n + S(2)) - b**S(2)*d*(m + n + S(2))/tan(e + f*x)**S(2) - b*(m + S(1))*(-a*d + b*c)/tan(e + f*x), x), x), x) - Simp(b**S(2)*(a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(1))/(f*(a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3646 = ReplacementRule(pattern3646, replacement3646)
    pattern3647 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons93, cons166, cons88, cons808)
    def replacement3647(m, f, b, d, c, a, n, x, e):
        rubi.append(3647)
        return Dist(S(1)/(m + n + S(-1)), Int((a + b*tan(e + f*x))**(m + S(-2))*(c + d*tan(e + f*x))**(n + S(-1))*Simp(a**S(2)*c*(m + n + S(-1)) - b*(a*d*n + b*c*(m + S(-1))) + b*(a*d*(S(2)*m + n + S(-2)) + b*c*n)*tan(e + f*x)**S(2) + (m + n + S(-1))*(a**S(2)*d + S(2)*a*b*c - b**S(2)*d)*tan(e + f*x), x), x), x) + Simp(b*(a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**n/(f*(m + n + S(-1))), x)
    rule3647 = ReplacementRule(pattern3647, replacement3647)
    pattern3648 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545, cons93, cons166, cons88, cons808)
    def replacement3648(m, f, b, d, c, a, n, x, e):
        rubi.append(3648)
        return Dist(S(1)/(m + n + S(-1)), Int((a + b/tan(e + f*x))**(m + S(-2))*(c + d/tan(e + f*x))**(n + S(-1))*Simp(a**S(2)*c*(m + n + S(-1)) - b*(a*d*n + b*c*(m + S(-1))) + b*(a*d*(S(2)*m + n + S(-2)) + b*c*n)/tan(e + f*x)**S(2) + (m + n + S(-1))*(a**S(2)*d + S(2)*a*b*c - b**S(2)*d)/tan(e + f*x), x), x), x) - Simp(b*(a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**n/(f*(m + n + S(-1))), x)
    rule3648 = ReplacementRule(pattern3648, replacement3648)
    pattern3649 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545)
    def replacement3649(f, b, d, c, a, x, e):
        rubi.append(3649)
        return Dist(b**S(2)/((a**S(2) + b**S(2))*(-a*d + b*c)), Int((-a*tan(e + f*x) + b)/(a + b*tan(e + f*x)), x), x) - Dist(d**S(2)/((c**S(2) + d**S(2))*(-a*d + b*c)), Int((-c*tan(e + f*x) + d)/(c + d*tan(e + f*x)), x), x) + Simp(x*(a*c - b*d)/((a**S(2) + b**S(2))*(c**S(2) + d**S(2))), x)
    rule3649 = ReplacementRule(pattern3649, replacement3649)
    pattern3650 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545)
    def replacement3650(f, b, d, c, a, x, e):
        rubi.append(3650)
        return Dist(b**S(2)/((a**S(2) + b**S(2))*(-a*d + b*c)), Int((-a/tan(e + f*x) + b)/(a + b/tan(e + f*x)), x), x) - Dist(d**S(2)/((c**S(2) + d**S(2))*(-a*d + b*c)), Int((-c/tan(e + f*x) + d)/(c + d/tan(e + f*x)), x), x) + Simp(x*(a*c - b*d)/((a**S(2) + b**S(2))*(c**S(2) + d**S(2))), x)
    rule3650 = ReplacementRule(pattern3650, replacement3650)
    pattern3651 = Pattern(Integral(sqrt(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons71, cons1440, cons1545)
    def replacement3651(f, b, d, c, a, x, e):
        rubi.append(3651)
        return -Dist(d*(-a*d + b*c)/(c**S(2) + d**S(2)), Int((tan(e + f*x)**S(2) + S(1))/(sqrt(a + b*tan(e + f*x))*(c + d*tan(e + f*x))), x), x) + Dist(S(1)/(c**S(2) + d**S(2)), Int(Simp(a*c + b*d + (-a*d + b*c)*tan(e + f*x), x)/sqrt(a + b*tan(e + f*x)), x), x)
    rule3651 = ReplacementRule(pattern3651, replacement3651)
    pattern3652 = Pattern(Integral(sqrt(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons71, cons1440, cons1545)
    def replacement3652(f, b, d, c, a, x, e):
        rubi.append(3652)
        return -Dist(d*(-a*d + b*c)/(c**S(2) + d**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))/(sqrt(a + b/tan(e + f*x))*(c + d/tan(e + f*x))), x), x) + Dist(S(1)/(c**S(2) + d**S(2)), Int(Simp(a*c + b*d + (-a*d + b*c)/tan(e + f*x), x)/sqrt(a + b/tan(e + f*x)), x), x)
    rule3652 = ReplacementRule(pattern3652, replacement3652)
    pattern3653 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545)
    def replacement3653(f, b, d, c, a, x, e):
        rubi.append(3653)
        return Dist((-a*d + b*c)**S(2)/(c**S(2) + d**S(2)), Int((tan(e + f*x)**S(2) + S(1))/(sqrt(a + b*tan(e + f*x))*(c + d*tan(e + f*x))), x), x) + Dist(S(1)/(c**S(2) + d**S(2)), Int(Simp(a**S(2)*c + S(2)*a*b*d - b**S(2)*c + (-a**S(2)*d + S(2)*a*b*c + b**S(2)*d)*tan(e + f*x), x)/sqrt(a + b*tan(e + f*x)), x), x)
    rule3653 = ReplacementRule(pattern3653, replacement3653)
    pattern3654 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1440, cons1545)
    def replacement3654(f, b, d, c, a, x, e):
        rubi.append(3654)
        return Dist((-a*d + b*c)**S(2)/(c**S(2) + d**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))/(sqrt(a + b/tan(e + f*x))*(c + d/tan(e + f*x))), x), x) + Dist(S(1)/(c**S(2) + d**S(2)), Int(Simp(a**S(2)*c + S(2)*a*b*d - b**S(2)*c + (-a**S(2)*d + S(2)*a*b*c + b**S(2)*d)/tan(e + f*x), x)/sqrt(a + b/tan(e + f*x)), x), x)
    rule3654 = ReplacementRule(pattern3654, replacement3654)
    pattern3655 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1440, cons1545, cons18)
    def replacement3655(m, f, b, d, c, a, x, e):
        rubi.append(3655)
        return Dist(d**S(2)/(c**S(2) + d**S(2)), Int((a + b*tan(e + f*x))**m*(tan(e + f*x)**S(2) + S(1))/(c + d*tan(e + f*x)), x), x) + Dist(S(1)/(c**S(2) + d**S(2)), Int((a + b*tan(e + f*x))**m*(c - d*tan(e + f*x)), x), x)
    rule3655 = ReplacementRule(pattern3655, replacement3655)
    pattern3656 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1440, cons1545, cons18)
    def replacement3656(m, f, b, d, c, a, x, e):
        rubi.append(3656)
        return Dist(d**S(2)/(c**S(2) + d**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))*(a + b/tan(e + f*x))**m/(c + d/tan(e + f*x)), x), x) + Dist(S(1)/(c**S(2) + d**S(2)), Int((a + b/tan(e + f*x))**m*(c - d/tan(e + f*x)), x), x)
    rule3656 = ReplacementRule(pattern3656, replacement3656)
    pattern3657 = Pattern(Integral((c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1440, cons1545)
    def replacement3657(m, f, b, d, a, c, n, x, e):
        rubi.append(3657)
        return Dist(b/f, Subst(Int((a + x)**m*(c + d*x/b)**n/(b**S(2) + x**S(2)), x), x, b*tan(e + f*x)), x)
    rule3657 = ReplacementRule(pattern3657, replacement3657)
    pattern3658 = Pattern(Integral((c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1440, cons1545)
    def replacement3658(m, f, b, d, a, c, n, x, e):
        rubi.append(3658)
        return -Dist(b/f, Subst(Int((a + x)**m*(c + d*x/b)**n/(b**S(2) + x**S(2)), x), x, b/tan(e + f*x)), x)
    rule3658 = ReplacementRule(pattern3658, replacement3658)
    pattern3659 = Pattern(Integral((WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons23, cons17)
    def replacement3659(m, f, b, d, a, n, x, e):
        rubi.append(3659)
        return Dist(d**m, Int((d/tan(e + f*x))**(-m + n)*(a/tan(e + f*x) + b)**m, x), x)
    rule3659 = ReplacementRule(pattern3659, replacement3659)
    pattern3660 = Pattern(Integral((WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons23, cons17)
    def replacement3660(m, f, b, d, a, n, x, e):
        rubi.append(3660)
        return Dist(d**m, Int((d*tan(e + f*x))**(-m + n)*(a*tan(e + f*x) + b)**m, x), x)
    rule3660 = ReplacementRule(pattern3660, replacement3660)
    pattern3661 = Pattern(Integral(((WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons23, cons18)
    def replacement3661(p, m, f, b, d, c, a, n, x, e):
        rubi.append(3661)
        return Dist(c**IntPart(n)*(c*(d*tan(e + f*x))**p)**FracPart(n)*(d*tan(e + f*x))**(-p*FracPart(n)), Int((d*tan(e + f*x))**(n*p)*(a + b*tan(e + f*x))**m, x), x)
    rule3661 = ReplacementRule(pattern3661, replacement3661)
    pattern3662 = Pattern(Integral(((WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons23, cons18)
    def replacement3662(p, m, f, b, d, a, c, n, x, e):
        rubi.append(3662)
        return Dist(c**IntPart(n)*(c*(d/tan(e + f*x))**p)**FracPart(n)*(d/tan(e + f*x))**(-p*FracPart(n)), Int((d/tan(e + f*x))**(n*p)*(a + b/tan(e + f*x))**m, x), x)
    rule3662 = ReplacementRule(pattern3662, replacement3662)
    pattern3663 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons380)
    def replacement3663(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(3663)
        return Int((g*tan(e + f*x))**p*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n, x)
    rule3663 = ReplacementRule(pattern3663, replacement3663)
    pattern3664 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons380)
    def replacement3664(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(3664)
        return Int((g/tan(e + f*x))**p*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n, x)
    rule3664 = ReplacementRule(pattern3664, replacement3664)
    pattern3665 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons147, cons17, cons85)
    def replacement3665(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(3665)
        return Dist(g**(m + n), Int((g/tan(e + f*x))**(-m - n + p)*(a/tan(e + f*x) + b)**m*(c/tan(e + f*x) + d)**n, x), x)
    rule3665 = ReplacementRule(pattern3665, replacement3665)
    pattern3666 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons147, cons17, cons85)
    def replacement3666(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(3666)
        return Dist(g**(m + n), Int((g*tan(e + f*x))**(-m - n + p)*(a*tan(e + f*x) + b)**m*(c*tan(e + f*x) + d)**n, x), x)
    rule3666 = ReplacementRule(pattern3666, replacement3666)
    pattern3667 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**q_)**p_*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons147, cons1417)
    def replacement3667(p, m, f, g, b, d, a, n, c, x, q, e):
        rubi.append(3667)
        return Dist((g*tan(e + f*x))**(-p*q)*(g*tan(e + f*x)**q)**p, Int((g*tan(e + f*x))**(p*q)*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n, x), x)
    rule3667 = ReplacementRule(pattern3667, replacement3667)
    pattern3668 = Pattern(Integral(((S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**q_*WC('g', S(1)))**p_*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons147, cons1417)
    def replacement3668(p, m, f, b, g, d, a, n, c, x, q, e):
        rubi.append(3668)
        return Dist((g*(S(1)/tan(e + f*x))**q)**p*(g/tan(e + f*x))**(-p*q), Int((g/tan(e + f*x))**(p*q)*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n, x), x)
    rule3668 = ReplacementRule(pattern3668, replacement3668)
    pattern3669 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons85)
    def replacement3669(p, m, g, f, b, d, c, n, a, x, e):
        rubi.append(3669)
        return Dist(g**n, Int((g*tan(e + f*x))**(-n + p)*(a + b*tan(e + f*x))**m*(c*tan(e + f*x) + d)**n, x), x)
    rule3669 = ReplacementRule(pattern3669, replacement3669)
    pattern3670 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons85)
    def replacement3670(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(3670)
        return Dist(g**n, Int((g/tan(e + f*x))**(-n + p)*(a + b/tan(e + f*x))**m*(c/tan(e + f*x) + d)**n, x), x)
    rule3670 = ReplacementRule(pattern3670, replacement3670)
    pattern3671 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons23, cons17, cons38)
    def replacement3671(p, m, f, b, d, c, n, a, x, e):
        rubi.append(3671)
        return Int((c + d/tan(e + f*x))**n*(a/tan(e + f*x) + b)**m*(S(1)/tan(e + f*x))**(-m - p), x)
    rule3671 = ReplacementRule(pattern3671, replacement3671)
    pattern3672 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons23, cons17, cons38)
    def replacement3672(p, m, f, b, d, a, c, n, x, e):
        rubi.append(3672)
        return Int((c + d*tan(e + f*x))**n*(a*tan(e + f*x) + b)**m*tan(e + f*x)**(-m - p), x)
    rule3672 = ReplacementRule(pattern3672, replacement3672)
    pattern3673 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons23, cons17, cons147)
    def replacement3673(p, m, f, b, g, d, c, n, a, x, e):
        rubi.append(3673)
        return Dist((g*tan(e + f*x))**p*(S(1)/tan(e + f*x))**p, Int((c + d/tan(e + f*x))**n*(a/tan(e + f*x) + b)**m*(S(1)/tan(e + f*x))**(-m - p), x), x)
    rule3673 = ReplacementRule(pattern3673, replacement3673)
    pattern3674 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons23, cons17, cons147)
    def replacement3674(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(3674)
        return Dist((g/tan(e + f*x))**p*tan(e + f*x)**p, Int((c + d*tan(e + f*x))**n*(a*tan(e + f*x) + b)**m*tan(e + f*x)**(-m - p), x), x)
    rule3674 = ReplacementRule(pattern3674, replacement3674)
    pattern3675 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons23, cons18)
    def replacement3675(p, m, f, g, b, d, c, n, a, x, e):
        rubi.append(3675)
        return Dist((g*tan(e + f*x))**n*(c + d/tan(e + f*x))**n*(c*tan(e + f*x) + d)**(-n), Int((g*tan(e + f*x))**(-n + p)*(a + b*tan(e + f*x))**m*(c*tan(e + f*x) + d)**n, x), x)
    rule3675 = ReplacementRule(pattern3675, replacement3675)
    pattern3676 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons23, cons18)
    def replacement3676(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(3676)
        return Dist((g/tan(e + f*x))**n*(c + d*tan(e + f*x))**n*(c/tan(e + f*x) + d)**(-n), Int((g/tan(e + f*x))**(-n + p)*(a + b/tan(e + f*x))**m*(c/tan(e + f*x) + d)**n, x), x)
    rule3676 = ReplacementRule(pattern3676, replacement3676)
    pattern3677 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons70, cons1439)
    def replacement3677(B, e, m, f, b, d, a, n, c, x, A):
        rubi.append(3677)
        return Dist(a*c/f, Subst(Int((A + B*x)*(a + b*x)**(m + S(-1))*(c + d*x)**(n + S(-1)), x), x, tan(e + f*x)), x)
    rule3677 = ReplacementRule(pattern3677, replacement3677)
    pattern3678 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons70, cons1439)
    def replacement3678(B, m, f, b, d, a, n, c, A, x, e):
        rubi.append(3678)
        return -Dist(a*c/f, Subst(Int((A + B*x)*(a + b*x)**(m + S(-1))*(c + d*x)**(n + S(-1)), x), x, S(1)/tan(e + f*x)), x)
    rule3678 = ReplacementRule(pattern3678, replacement3678)
    pattern3679 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71)
    def replacement3679(B, e, f, b, d, a, c, x, A):
        rubi.append(3679)
        return Dist(S(1)/b, Int(Simp(A*b*c + (A*b*d + B*(-a*d + b*c))*tan(e + f*x), x)/(a + b*tan(e + f*x)), x), x) + Dist(B*d/b, Int(tan(e + f*x), x), x)
    rule3679 = ReplacementRule(pattern3679, replacement3679)
    pattern3680 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71)
    def replacement3680(B, e, f, b, d, a, c, x, A):
        rubi.append(3680)
        return Dist(S(1)/b, Int(Simp(A*b*c + (A*b*d + B*(-a*d + b*c))/tan(e + f*x), x)/(a + b/tan(e + f*x)), x), x) + Dist(B*d/b, Int(S(1)/tan(e + f*x), x), x)
    rule3680 = ReplacementRule(pattern3680, replacement3680)
    pattern3681 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons31, cons94, cons1439)
    def replacement3681(B, e, m, f, b, d, c, a, x, A):
        rubi.append(3681)
        return Dist(S(1)/(S(2)*a*b), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(A*a*d + A*b*c + B*a*c + S(2)*B*a*d*tan(e + f*x) + B*b*d, x), x), x) - Simp((a + b*tan(e + f*x))**m*(A*b - B*a)*(a*c + b*d)/(S(2)*a**S(2)*f*m), x)
    rule3681 = ReplacementRule(pattern3681, replacement3681)
    pattern3682 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons31, cons94, cons1439)
    def replacement3682(B, m, f, b, d, c, a, A, x, e):
        rubi.append(3682)
        return Dist(S(1)/(S(2)*a*b), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(A*a*d + A*b*c + B*a*c + S(2)*B*a*d/tan(e + f*x) + B*b*d, x), x), x) + Simp((a + b/tan(e + f*x))**m*(A*b - B*a)*(a*c + b*d)/(S(2)*a**S(2)*f*m), x)
    rule3682 = ReplacementRule(pattern3682, replacement3682)
    pattern3683 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons31, cons94, cons1440)
    def replacement3683(B, e, m, f, b, d, a, c, x, A):
        rubi.append(3683)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(A*a*c + A*b*d - B*a*d + B*b*c - (-A*a*d + A*b*c - B*a*c - B*b*d)*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(1))*(A*b - B*a)*(-a*d + b*c)/(b*f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3683 = ReplacementRule(pattern3683, replacement3683)
    pattern3684 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons31, cons94, cons1440)
    def replacement3684(B, e, m, f, b, d, a, c, x, A):
        rubi.append(3684)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(A*a*c + A*b*d - B*a*d + B*b*c - (-A*a*d + A*b*c - B*a*c - B*b*d)/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(1))*(A*b - B*a)*(-a*d + b*c)/(b*f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3684 = ReplacementRule(pattern3684, replacement3684)
    pattern3685 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1549)
    def replacement3685(B, m, f, b, d, a, c, A, x, e):
        rubi.append(3685)
        return Int((a + b*tan(e + f*x))**m*Simp(A*c - B*d + (A*d + B*c)*tan(e + f*x), x), x) + Simp(B*d*(a + b*tan(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule3685 = ReplacementRule(pattern3685, replacement3685)
    pattern3686 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1549)
    def replacement3686(B, m, f, b, d, a, c, A, x, e):
        rubi.append(3686)
        return Int((a + b/tan(e + f*x))**m*Simp(A*c - B*d + (A*d + B*c)/tan(e + f*x), x), x) - Simp(B*d*(a + b/tan(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule3686 = ReplacementRule(pattern3686, replacement3686)
    pattern3687 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1439, cons93, cons166, cons89)
    def replacement3687(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(3687)
        return -Dist(a/(d*(n + S(1))*(a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(1))*Simp(A*b*d*(m - n + S(-2)) - B*(a*d*(n + S(1)) + b*c*(m + S(-1))) + (A*a*d*(m + n) - B*(a*c*(m + S(-1)) + b*d*(n + S(1))))*tan(e + f*x), x), x), x) - Simp(a**S(2)*(a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(1))*(-A*d + B*c)/(d*f*(n + S(1))*(a*d + b*c)), x)
    rule3687 = ReplacementRule(pattern3687, replacement3687)
    pattern3688 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1439, cons93, cons166, cons89)
    def replacement3688(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3688)
        return -Dist(a/(d*(n + S(1))*(a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(1))*Simp(A*b*d*(m - n + S(-2)) - B*(a*d*(n + S(1)) + b*c*(m + S(-1))) + (A*a*d*(m + n) - B*(a*c*(m + S(-1)) + b*d*(n + S(1))))/tan(e + f*x), x), x), x) + Simp(a**S(2)*(a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(1))*(-A*d + B*c)/(d*f*(n + S(1))*(a*d + b*c)), x)
    rule3688 = ReplacementRule(pattern3688, replacement3688)
    pattern3689 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1439, cons31, cons166, cons346)
    def replacement3689(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(3689)
        return Dist(S(1)/(d*(m + n)), Int((a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**n*Simp(A*a*d*(m + n) + B*(a*c*(m + S(-1)) - b*d*(n + S(1))) - (B*(m + S(-1))*(-a*d + b*c) - d*(m + n)*(A*b + B*a))*tan(e + f*x), x), x), x) + Simp(B*b*(a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(1))/(d*f*(m + n)), x)
    rule3689 = ReplacementRule(pattern3689, replacement3689)
    pattern3690 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1439, cons31, cons166, cons346)
    def replacement3690(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3690)
        return Dist(S(1)/(d*(m + n)), Int((a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**n*Simp(A*a*d*(m + n) + B*(a*c*(m + S(-1)) - b*d*(n + S(1))) - (B*(m + S(-1))*(-a*d + b*c) - d*(m + n)*(A*b + B*a))/tan(e + f*x), x), x), x) - Simp(B*b*(a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(m + n)), x)
    rule3690 = ReplacementRule(pattern3690, replacement3690)
    pattern3691 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1439, cons93, cons267, cons88)
    def replacement3691(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(3691)
        return Dist(S(1)/(S(2)*a**S(2)*m), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(-1))*Simp(A*(a*c*m + b*d*n) - B*(a*d*n + b*c*m) - d*(-A*a*(m + n) + B*b*(m - n))*tan(e + f*x), x), x), x) - Simp((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n*(A*b - B*a)/(S(2)*a*f*m), x)
    rule3691 = ReplacementRule(pattern3691, replacement3691)
    pattern3692 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1439, cons93, cons267, cons88)
    def replacement3692(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3692)
        return Dist(S(1)/(S(2)*a**S(2)*m), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(-1))*Simp(A*(a*c*m + b*d*n) - B*(a*d*n + b*c*m) - d*(-A*a*(m + n) + B*b*(m - n))/tan(e + f*x), x), x), x) + Simp((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n*(A*b - B*a)/(S(2)*a*f*m), x)
    rule3692 = ReplacementRule(pattern3692, replacement3692)
    pattern3693 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1439, cons31, cons267, cons1327)
    def replacement3693(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(3693)
        return Dist(S(1)/(S(2)*a*m*(-a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n*Simp(A*(-a*d*(S(2)*m + n + S(1)) + b*c*m) + B*(a*c*m - b*d*(n + S(1))) + d*(A*b - B*a)*(m + n + S(1))*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*(A*a + B*b)/(S(2)*f*m*(-a*d + b*c)), x)
    rule3693 = ReplacementRule(pattern3693, replacement3693)
    pattern3694 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1439, cons31, cons267, cons1327)
    def replacement3694(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3694)
        return Dist(S(1)/(S(2)*a*m*(-a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n*Simp(A*(-a*d*(S(2)*m + n + S(1)) + b*c*m) + B*(a*c*m - b*d*(n + S(1))) + d*(A*b - B*a)*(m + n + S(1))/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*(A*a + B*b)/(S(2)*f*m*(-a*d + b*c)), x)
    rule3694 = ReplacementRule(pattern3694, replacement3694)
    pattern3695 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1439, cons87, cons88)
    def replacement3695(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(3695)
        return Dist(S(1)/(a*(m + n)), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(-1))*Simp(A*a*c*(m + n) - B*(a*d*n + b*c*m) + (A*a*d*(m + n) - B*(-a*c*n + b*d*m))*tan(e + f*x), x), x), x) + Simp(B*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n/(f*(m + n)), x)
    rule3695 = ReplacementRule(pattern3695, replacement3695)
    pattern3696 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1439, cons87, cons88)
    def replacement3696(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3696)
        return Dist(S(1)/(a*(m + n)), Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(-1))*Simp(A*a*c*(m + n) - B*(a*d*n + b*c*m) + (A*a*d*(m + n) - B*(-a*c*n + b*d*m))/tan(e + f*x), x), x), x) - Simp(B*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n/(f*(m + n)), x)
    rule3696 = ReplacementRule(pattern3696, replacement3696)
    pattern3697 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1439, cons87, cons89)
    def replacement3697(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(3697)
        return -Dist(S(1)/(a*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*Simp(A*(-a*c*(n + S(1)) + b*d*m) - B*(a*d*(n + S(1)) + b*c*m) - a*(-A*d + B*c)*(m + n + S(1))*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*(A*d - B*c)/(f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3697 = ReplacementRule(pattern3697, replacement3697)
    pattern3698 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1439, cons87, cons89)
    def replacement3698(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3698)
        return -Dist(S(1)/(a*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*Simp(A*(-a*c*(n + S(1)) + b*d*m) - B*(a*d*(n + S(1)) + b*c*m) - a*(-A*d + B*c)*(m + n + S(1))/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*(A*d - B*c)/(f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3698 = ReplacementRule(pattern3698, replacement3698)
    pattern3699 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1439, cons1418)
    def replacement3699(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(3699)
        return Dist(B*b/f, Subst(Int((a + b*x)**(m + S(-1))*(c + d*x)**n, x), x, tan(e + f*x)), x)
    rule3699 = ReplacementRule(pattern3699, replacement3699)
    pattern3700 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1439, cons1418)
    def replacement3700(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3700)
        return -Dist(B*b/f, Subst(Int((a + b*x)**(m + S(-1))*(c + d*x)**n, x), x, S(1)/tan(e + f*x)), x)
    rule3700 = ReplacementRule(pattern3700, replacement3700)
    pattern3701 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1439, cons1426)
    def replacement3701(B, e, m, f, b, d, c, a, x, A):
        rubi.append(3701)
        return Dist((A*b + B*a)/(a*d + b*c), Int((a + b*tan(e + f*x))**m, x), x) - Dist((-A*d + B*c)/(a*d + b*c), Int((a - b*tan(e + f*x))*(a + b*tan(e + f*x))**m/(c + d*tan(e + f*x)), x), x)
    rule3701 = ReplacementRule(pattern3701, replacement3701)
    pattern3702 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1439, cons1426)
    def replacement3702(B, m, f, b, d, c, a, A, x, e):
        rubi.append(3702)
        return Dist((A*b + B*a)/(a*d + b*c), Int((a + b/tan(e + f*x))**m, x), x) - Dist((-A*d + B*c)/(a*d + b*c), Int((a - b/tan(e + f*x))*(a + b/tan(e + f*x))**m/(c + d/tan(e + f*x)), x), x)
    rule3702 = ReplacementRule(pattern3702, replacement3702)
    pattern3703 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1439, cons1426)
    def replacement3703(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(3703)
        return -Dist(B/b, Int((a - b*tan(e + f*x))*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n, x), x) + Dist((A*b + B*a)/b, Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n, x), x)
    rule3703 = ReplacementRule(pattern3703, replacement3703)
    pattern3704 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1439, cons1426)
    def replacement3704(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3704)
        return -Dist(B/b, Int((a - b/tan(e + f*x))*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n, x), x) + Dist((A*b + B*a)/b, Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n, x), x)
    rule3704 = ReplacementRule(pattern3704, replacement3704)
    pattern3705 = Pattern(Integral((A_ + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1440, cons18, cons23, cons1513, cons1558)
    def replacement3705(B, m, f, b, d, a, c, n, A, x, e):
        rubi.append(3705)
        return Dist(A**S(2)/f, Subst(Int((a + b*x)**m*(c + d*x)**n/(A - B*x), x), x, tan(e + f*x)), x)
    rule3705 = ReplacementRule(pattern3705, replacement3705)
    pattern3706 = Pattern(Integral((A_ + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1440, cons18, cons23, cons1513, cons1558)
    def replacement3706(B, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3706)
        return -Dist(A**S(2)/f, Subst(Int((a + b*x)**m*(c + d*x)**n/(A - B*x), x), x, S(1)/tan(e + f*x)), x)
    rule3706 = ReplacementRule(pattern3706, replacement3706)
    pattern3707 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1440, cons18, cons23, cons1513, cons1559)
    def replacement3707(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3707)
        return Dist(A/S(2) - I*B/S(2), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n*(I*tan(e + f*x) + S(1)), x), x) + Dist(A/S(2) + I*B/S(2), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n*(-I*tan(e + f*x) + S(1)), x), x)
    rule3707 = ReplacementRule(pattern3707, replacement3707)
    pattern3708 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1440, cons18, cons23, cons1513, cons1559)
    def replacement3708(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3708)
        return Dist(A/S(2) - I*B/S(2), Int((S(1) + I/tan(e + f*x))*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n, x), x) + Dist(A/S(2) + I*B/S(2), Int((S(1) - I/tan(e + f*x))*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n, x), x)
    rule3708 = ReplacementRule(pattern3708, replacement3708)
    pattern3709 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545, cons93, cons166, cons89, cons1334)
    def replacement3709(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3709)
        return -Dist(S(1)/(d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b*tan(e + f*x))**(m + S(-2))*(c + d*tan(e + f*x))**(n + S(1))*Simp(A*a*d*(-a*c*(n + S(1)) + b*d*(m + S(-1))) - b*(-B*b*(c**S(2)*(m + S(-1)) - d**S(2)*(n + S(1))) + d*(m + n)*(-A*a*d + A*b*c + B*a*c))*tan(e + f*x)**S(2) - d*(n + S(1))*((A*a - B*b)*(-a*d + b*c) + (A*b + B*a)*(a*c + b*d))*tan(e + f*x) + (B*b*c - d*(A*b + B*a))*(a*d*(n + S(1)) + b*c*(m + S(-1))), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(1))*(-A*d + B*c)*(-a*d + b*c)/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3709 = ReplacementRule(pattern3709, replacement3709)
    pattern3710 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545, cons93, cons166, cons89, cons1334)
    def replacement3710(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3710)
        return -Dist(S(1)/(d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b/tan(e + f*x))**(m + S(-2))*(c + d/tan(e + f*x))**(n + S(1))*Simp(A*a*d*(-a*c*(n + S(1)) + b*d*(m + S(-1))) - b*(-B*b*(c**S(2)*(m + S(-1)) - d**S(2)*(n + S(1))) + d*(m + n)*(-A*a*d + A*b*c + B*a*c))/tan(e + f*x)**S(2) - d*(n + S(1))*((A*a - B*b)*(-a*d + b*c) + (A*b + B*a)*(a*c + b*d))/tan(e + f*x) + (B*b*c - d*(A*b + B*a))*(a*d*(n + S(1)) + b*c*(m + S(-1))), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(1))*(-A*d + B*c)*(-a*d + b*c)/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3710 = ReplacementRule(pattern3710, replacement3710)
    pattern3711 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1440, cons1545, cons31, cons166, cons1334, cons1560)
    def replacement3711(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3711)
        return Dist(S(1)/(d*(m + n)), Int((a + b*tan(e + f*x))**(m + S(-2))*(c + d*tan(e + f*x))**n*Simp(A*a**S(2)*d*(m + n) - B*b*(a*d*(n + S(1)) + b*c*(m + S(-1))) + d*(m + n)*(S(2)*A*a*b + B*(a**S(2) - b**S(2)))*tan(e + f*x) - (B*b*(m + S(-1))*(-a*d + b*c) - b*d*(m + n)*(A*b + B*a))*tan(e + f*x)**S(2), x), x), x) + Simp(B*b*(a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(1))/(d*f*(m + n)), x)
    rule3711 = ReplacementRule(pattern3711, replacement3711)
    pattern3712 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1440, cons1545, cons31, cons166, cons1334, cons1560)
    def replacement3712(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3712)
        return Dist(S(1)/(d*(m + n)), Int((a + b/tan(e + f*x))**(m + S(-2))*(c + d/tan(e + f*x))**n*Simp(A*a**S(2)*d*(m + n) - B*b*(a*d*(n + S(1)) + b*c*(m + S(-1))) + d*(m + n)*(S(2)*A*a*b + B*(a**S(2) - b**S(2)))/tan(e + f*x) - (B*b*(m + S(-1))*(-a*d + b*c) - b*d*(m + n)*(A*b + B*a))/tan(e + f*x)**S(2), x), x), x) - Simp(B*b*(a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(m + n)), x)
    rule3712 = ReplacementRule(pattern3712, replacement3712)
    pattern3713 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545, cons93, cons94, cons1325, cons1334)
    def replacement3713(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3713)
        return Dist(S(1)/(b*(a**S(2) + b**S(2))*(m + S(1))), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(-1))*Simp(A*b*(a*c*(m + S(1)) - b*d*n) + B*b*(a*d*n + b*c*(m + S(1))) - b*d*(A*b - B*a)*(m + n + S(1))*tan(e + f*x)**S(2) - b*(m + S(1))*(A*(-a*d + b*c) - B*(a*c + b*d))*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n*(A*b - B*a)/(f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3713 = ReplacementRule(pattern3713, replacement3713)
    pattern3714 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545, cons93, cons94, cons1325, cons1334)
    def replacement3714(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3714)
        return Dist(S(1)/(b*(a**S(2) + b**S(2))*(m + S(1))), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(-1))*Simp(A*b*(a*c*(m + S(1)) - b*d*n) + B*b*(a*d*n + b*c*(m + S(1))) - b*d*(A*b - B*a)*(m + n + S(1))/tan(e + f*x)**S(2) - b*(m + S(1))*(A*(-a*d + b*c) - B*(a*c + b*d))/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n*(A*b - B*a)/(f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3714 = ReplacementRule(pattern3714, replacement3714)
    pattern3715 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1440, cons1545, cons31, cons94, cons1334, cons1557)
    def replacement3715(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3715)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n*Simp(A*(a*(m + S(1))*(-a*d + b*c) - b**S(2)*d*(m + n + S(2))) + B*b*(a*d*(n + S(1)) + b*c*(m + S(1))) - b*d*(A*b - B*a)*(m + n + S(2))*tan(e + f*x)**S(2) - (m + S(1))*(A*b - B*a)*(-a*d + b*c)*tan(e + f*x), x), x), x) + Simp(b*(a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(1))*(A*b - B*a)/(f*(a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3715 = ReplacementRule(pattern3715, replacement3715)
    pattern3716 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1440, cons1545, cons31, cons94, cons1334, cons1557)
    def replacement3716(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3716)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n*Simp(A*(a*(m + S(1))*(-a*d + b*c) - b**S(2)*d*(m + n + S(2))) + B*b*(a*d*(n + S(1)) + b*c*(m + S(1))) - b*d*(A*b - B*a)*(m + n + S(2))/tan(e + f*x)**S(2) - (m + S(1))*(A*b - B*a)*(-a*d + b*c)/tan(e + f*x), x), x), x) - Simp(b*(a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(1))*(A*b - B*a)/(f*(a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3716 = ReplacementRule(pattern3716, replacement3716)
    pattern3717 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545, cons93, cons1256, cons1325)
    def replacement3717(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3717)
        return Dist(S(1)/(m + n), Int((a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(-1))*Simp(A*a*c*(m + n) - B*(a*d*n + b*c*m) + (m + n)*(A*a*d + A*b*c + B*a*c - B*b*d)*tan(e + f*x) + (A*b*d*(m + n) + B*(a*d*m + b*c*n))*tan(e + f*x)**S(2), x), x), x) + Simp(B*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n/(f*(m + n)), x)
    rule3717 = ReplacementRule(pattern3717, replacement3717)
    pattern3718 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545, cons93, cons1256, cons1325)
    def replacement3718(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3718)
        return Dist(S(1)/(m + n), Int((a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(-1))*Simp(A*a*c*(m + n) - B*(a*d*n + b*c*m) + (m + n)*(A*a*d + A*b*c + B*a*c - B*b*d)/tan(e + f*x) + (A*b*d*(m + n) + B*(a*d*m + b*c*n))/tan(e + f*x)**S(2), x), x), x) - Simp(B*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n/(f*(m + n)), x)
    rule3718 = ReplacementRule(pattern3718, replacement3718)
    pattern3719 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545)
    def replacement3719(B, e, f, b, d, c, a, x, A):
        rubi.append(3719)
        return Dist(b*(A*b - B*a)/((a**S(2) + b**S(2))*(-a*d + b*c)), Int((-a*tan(e + f*x) + b)/(a + b*tan(e + f*x)), x), x) + Dist(d*(-A*d + B*c)/((c**S(2) + d**S(2))*(-a*d + b*c)), Int((-c*tan(e + f*x) + d)/(c + d*tan(e + f*x)), x), x) + Simp(x*(A*(a*c - b*d) + B*(a*d + b*c))/((a**S(2) + b**S(2))*(c**S(2) + d**S(2))), x)
    rule3719 = ReplacementRule(pattern3719, replacement3719)
    pattern3720 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545)
    def replacement3720(B, f, b, d, c, a, A, x, e):
        rubi.append(3720)
        return Dist(b*(A*b - B*a)/((a**S(2) + b**S(2))*(-a*d + b*c)), Int((-a/tan(e + f*x) + b)/(a + b/tan(e + f*x)), x), x) + Dist(d*(-A*d + B*c)/((c**S(2) + d**S(2))*(-a*d + b*c)), Int((-c/tan(e + f*x) + d)/(c + d/tan(e + f*x)), x), x) + Simp(x*(A*(a*c - b*d) + B*(a*d + b*c))/((a**S(2) + b**S(2))*(c**S(2) + d**S(2))), x)
    rule3720 = ReplacementRule(pattern3720, replacement3720)
    pattern3721 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545)
    def replacement3721(B, e, f, b, d, a, c, x, A):
        rubi.append(3721)
        return -Dist((-A*b + B*a)*(-a*d + b*c)/(a**S(2) + b**S(2)), Int((tan(e + f*x)**S(2) + S(1))/((a + b*tan(e + f*x))*sqrt(c + d*tan(e + f*x))), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int(Simp(A*(a*c + b*d) + B*(-a*d + b*c) - (A*(-a*d + b*c) - B*(a*c + b*d))*tan(e + f*x), x)/sqrt(c + d*tan(e + f*x)), x), x)
    rule3721 = ReplacementRule(pattern3721, replacement3721)
    pattern3722 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545)
    def replacement3722(B, e, f, b, d, a, c, x, A):
        rubi.append(3722)
        return -Dist((-A*b + B*a)*(-a*d + b*c)/(a**S(2) + b**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))/((a + b/tan(e + f*x))*sqrt(c + d/tan(e + f*x))), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int(Simp(A*(a*c + b*d) + B*(-a*d + b*c) - (A*(-a*d + b*c) - B*(a*c + b*d))/tan(e + f*x), x)/sqrt(c + d/tan(e + f*x)), x), x)
    rule3722 = ReplacementRule(pattern3722, replacement3722)
    pattern3723 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1440, cons1545)
    def replacement3723(B, e, f, b, d, a, c, n, x, A):
        rubi.append(3723)
        return Dist(b*(A*b - B*a)/(a**S(2) + b**S(2)), Int((c + d*tan(e + f*x))**n*(tan(e + f*x)**S(2) + S(1))/(a + b*tan(e + f*x)), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int((c + d*tan(e + f*x))**n*Simp(A*a + B*b - (A*b - B*a)*tan(e + f*x), x), x), x)
    rule3723 = ReplacementRule(pattern3723, replacement3723)
    pattern3724 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1440, cons1545)
    def replacement3724(B, e, f, b, d, a, c, n, x, A):
        rubi.append(3724)
        return Dist(b*(A*b - B*a)/(a**S(2) + b**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))*(c + d/tan(e + f*x))**n/(a + b/tan(e + f*x)), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int((c + d/tan(e + f*x))**n*Simp(A*a + B*b - (A*b - B*a)/tan(e + f*x), x), x), x)
    rule3724 = ReplacementRule(pattern3724, replacement3724)
    pattern3725 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545)
    def replacement3725(B, e, f, b, d, a, c, x, A):
        rubi.append(3725)
        return Dist(B*b, Int((tan(e + f*x)**S(2) + S(1))/(sqrt(a + b*tan(e + f*x))*sqrt(c + d*tan(e + f*x))), x), x) + Int(Simp(A*a - B*b + (A*b + B*a)*tan(e + f*x), x)/(sqrt(a + b*tan(e + f*x))*sqrt(c + d*tan(e + f*x))), x)
    rule3725 = ReplacementRule(pattern3725, replacement3725)
    pattern3726 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1440, cons1545)
    def replacement3726(B, e, f, b, d, a, c, x, A):
        rubi.append(3726)
        return Dist(B*b, Int((S(1) + tan(e + f*x)**(S(-2)))/(sqrt(a + b/tan(e + f*x))*sqrt(c + d/tan(e + f*x))), x), x) + Int(Simp(A*a - B*b + (A*b + B*a)/tan(e + f*x), x)/(sqrt(a + b/tan(e + f*x))*sqrt(c + d/tan(e + f*x))), x)
    rule3726 = ReplacementRule(pattern3726, replacement3726)
    pattern3727 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1440, cons1558)
    def replacement3727(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3727)
        return Dist(A**S(2)/f, Subst(Int((a + b*x)**m*(c + d*x)**n/(A - B*x), x), x, tan(e + f*x)), x)
    rule3727 = ReplacementRule(pattern3727, replacement3727)
    pattern3728 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1440, cons1558)
    def replacement3728(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3728)
        return -Dist(A**S(2)/f, Subst(Int((a + b*x)**m*(c + d*x)**n/(A - B*x), x), x, S(1)/tan(e + f*x)), x)
    rule3728 = ReplacementRule(pattern3728, replacement3728)
    pattern3729 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1440, cons1559)
    def replacement3729(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3729)
        return Dist(A/S(2) - I*B/S(2), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n*(I*tan(e + f*x) + S(1)), x), x) + Dist(A/S(2) + I*B/S(2), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n*(-I*tan(e + f*x) + S(1)), x), x)
    rule3729 = ReplacementRule(pattern3729, replacement3729)
    pattern3730 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1440, cons1559)
    def replacement3730(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3730)
        return Dist(A/S(2) - I*B/S(2), Int((S(1) + I/tan(e + f*x))*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n, x), x) + Dist(A/S(2) + I*B/S(2), Int((S(1) - I/tan(e + f*x))*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n, x), x)
    rule3730 = ReplacementRule(pattern3730, replacement3730)
    pattern3731 = Pattern(Integral((A_ + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1561)
    def replacement3731(C, m, f, b, a, A, x, e):
        rubi.append(3731)
        return Dist(A/(b*f), Subst(Int((a + x)**m, x), x, b*tan(e + f*x)), x)
    rule3731 = ReplacementRule(pattern3731, replacement3731)
    pattern3732 = Pattern(Integral((A_ + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1561)
    def replacement3732(C, m, f, b, a, A, x, e):
        rubi.append(3732)
        return -Dist(A/(b*f), Subst(Int((a + x)**m, x), x, b/tan(e + f*x)), x)
    rule3732 = ReplacementRule(pattern3732, replacement3732)
    pattern3733 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons33)
    def replacement3733(B, C, m, f, b, a, A, x, e):
        rubi.append(3733)
        return Dist(b**(S(-2)), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(B*b - C*a + C*b*tan(e + f*x), x), x), x)
    rule3733 = ReplacementRule(pattern3733, replacement3733)
    pattern3734 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons33)
    def replacement3734(B, C, m, f, b, a, A, x, e):
        rubi.append(3734)
        return Dist(b**(S(-2)), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(B*b - C*a + C*b/tan(e + f*x), x), x), x)
    rule3734 = ReplacementRule(pattern3734, replacement3734)
    pattern3735 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1433)
    def replacement3735(C, m, f, b, a, A, x, e):
        rubi.append(3735)
        return -Dist(C/b**S(2), Int((a - b*tan(e + f*x))*(a + b*tan(e + f*x))**(m + S(1)), x), x)
    rule3735 = ReplacementRule(pattern3735, replacement3735)
    pattern3736 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1433)
    def replacement3736(C, m, f, b, a, A, x, e):
        rubi.append(3736)
        return -Dist(C/b**S(2), Int((a - b/tan(e + f*x))*(a + b/tan(e + f*x))**(m + S(1)), x), x)
    rule3736 = ReplacementRule(pattern3736, replacement3736)
    pattern3737 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1562, cons31, cons32, cons1439)
    def replacement3737(B, C, m, f, b, a, A, x, e):
        rubi.append(3737)
        return Dist(S(1)/(S(2)*a**S(2)*m), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(A*a*(S(2)*m + S(1)) + B*b - C*a - (C*b*(m + S(-1)) + (m + S(1))*(A*b - B*a))*tan(e + f*x), x), x), x) - Simp((a + b*tan(e + f*x))**m*(A*a + B*b - C*a)*tan(e + f*x)/(S(2)*a*f*m), x)
    rule3737 = ReplacementRule(pattern3737, replacement3737)
    pattern3738 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1562, cons31, cons32, cons1439)
    def replacement3738(B, C, m, f, b, a, A, x, e):
        rubi.append(3738)
        return Dist(S(1)/(S(2)*a**S(2)*m), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(A*a*(S(2)*m + S(1)) + B*b - C*a - (C*b*(m + S(-1)) + (m + S(1))*(A*b - B*a))/tan(e + f*x), x), x), x) + Simp((a + b/tan(e + f*x))**m*(A*a + B*b - C*a)/(S(2)*a*f*m*tan(e + f*x)), x)
    rule3738 = ReplacementRule(pattern3738, replacement3738)
    pattern3739 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1563, cons31, cons32, cons1439)
    def replacement3739(C, m, f, b, a, A, x, e):
        rubi.append(3739)
        return Dist(S(1)/(S(2)*a**S(2)*m), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(A*a*(S(2)*m + S(1)) - C*a - (A*b*(m + S(1)) + C*b*(m + S(-1)))*tan(e + f*x), x), x), x) - Simp((a + b*tan(e + f*x))**m*(A*a - C*a)*tan(e + f*x)/(S(2)*a*f*m), x)
    rule3739 = ReplacementRule(pattern3739, replacement3739)
    pattern3740 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1563, cons31, cons32, cons1439)
    def replacement3740(C, m, f, b, a, A, x, e):
        rubi.append(3740)
        return Dist(S(1)/(S(2)*a**S(2)*m), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(A*a*(S(2)*m + S(1)) - C*a - (A*b*(m + S(1)) + C*b*(m + S(-1)))/tan(e + f*x), x), x), x) + Simp((a + b/tan(e + f*x))**m*(A*a - C*a)/(S(2)*a*f*m*tan(e + f*x)), x)
    rule3740 = ReplacementRule(pattern3740, replacement3740)
    pattern3741 = Pattern(Integral((A_ + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1440, cons1564)
    def replacement3741(B, C, f, b, a, A, x, e):
        rubi.append(3741)
        return Dist((A*b**S(2) - B*a*b + C*a**S(2))/(a**S(2) + b**S(2)), Int((tan(e + f*x)**S(2) + S(1))/(a + b*tan(e + f*x)), x), x) + Simp(x*(A*a + B*b - C*a)/(a**S(2) + b**S(2)), x)
    rule3741 = ReplacementRule(pattern3741, replacement3741)
    pattern3742 = Pattern(Integral((A_ + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1440, cons1564)
    def replacement3742(B, C, f, b, a, A, x, e):
        rubi.append(3742)
        return Dist((A*b**S(2) - B*a*b + C*a**S(2))/(a**S(2) + b**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))/(a + b/tan(e + f*x)), x), x) + Simp(x*(A*a + B*b - C*a)/(a**S(2) + b**S(2)), x)
    rule3742 = ReplacementRule(pattern3742, replacement3742)
    pattern3743 = Pattern(Integral((A_ + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/tan(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons48, cons125, cons34, cons35, cons36, cons1565)
    def replacement3743(B, C, f, A, x, e):
        rubi.append(3743)
        return Dist(A, Int(S(1)/tan(e + f*x), x), x) + Dist(C, Int(tan(e + f*x), x), x) + Simp(B*x, x)
    rule3743 = ReplacementRule(pattern3743, replacement3743)
    pattern3744 = Pattern(Integral((A_ + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*tan(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons48, cons125, cons34, cons35, cons36, cons1565)
    def replacement3744(B, C, f, A, x, e):
        rubi.append(3744)
        return Dist(A, Int(tan(e + f*x), x), x) + Dist(C, Int(S(1)/tan(e + f*x), x), x) + Simp(B*x, x)
    rule3744 = ReplacementRule(pattern3744, replacement3744)
    pattern3745 = Pattern(Integral((A_ + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/tan(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons48, cons125, cons34, cons36, cons1565)
    def replacement3745(C, e, f, x, A):
        rubi.append(3745)
        return Dist(A, Int(S(1)/tan(e + f*x), x), x) + Dist(C, Int(tan(e + f*x), x), x)
    rule3745 = ReplacementRule(pattern3745, replacement3745)
    pattern3746 = Pattern(Integral((A_ + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*tan(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons48, cons125, cons34, cons36, cons1565)
    def replacement3746(C, e, f, x, A):
        rubi.append(3746)
        return Dist(A, Int(tan(e + f*x), x), x) + Dist(C, Int(S(1)/tan(e + f*x), x), x)
    rule3746 = ReplacementRule(pattern3746, replacement3746)
    pattern3747 = Pattern(Integral((A_ + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1562, cons1440, cons1566)
    def replacement3747(B, C, f, b, a, A, x, e):
        rubi.append(3747)
        return -Dist((A*b - B*a - C*b)/(a**S(2) + b**S(2)), Int(tan(e + f*x), x), x) + Dist((A*b**S(2) - B*a*b + C*a**S(2))/(a**S(2) + b**S(2)), Int((tan(e + f*x)**S(2) + S(1))/(a + b*tan(e + f*x)), x), x) + Simp(x*(A*a + B*b - C*a)/(a**S(2) + b**S(2)), x)
    rule3747 = ReplacementRule(pattern3747, replacement3747)
    pattern3748 = Pattern(Integral((A_ + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1562, cons1440, cons1566)
    def replacement3748(B, C, f, b, a, A, x, e):
        rubi.append(3748)
        return -Dist((A*b - B*a - C*b)/(a**S(2) + b**S(2)), Int(S(1)/tan(e + f*x), x), x) + Dist((A*b**S(2) - B*a*b + C*a**S(2))/(a**S(2) + b**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))/(a + b/tan(e + f*x)), x), x) + Simp(x*(A*a + B*b - C*a)/(a**S(2) + b**S(2)), x)
    rule3748 = ReplacementRule(pattern3748, replacement3748)
    pattern3749 = Pattern(Integral((A_ + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1563, cons1440, cons1565)
    def replacement3749(C, f, b, a, A, x, e):
        rubi.append(3749)
        return Dist((A*b**S(2) + C*a**S(2))/(a**S(2) + b**S(2)), Int((tan(e + f*x)**S(2) + S(1))/(a + b*tan(e + f*x)), x), x) - Dist(b*(A - C)/(a**S(2) + b**S(2)), Int(tan(e + f*x), x), x) + Simp(a*x*(A - C)/(a**S(2) + b**S(2)), x)
    rule3749 = ReplacementRule(pattern3749, replacement3749)
    pattern3750 = Pattern(Integral((A_ + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1563, cons1440, cons1565)
    def replacement3750(C, f, b, a, A, x, e):
        rubi.append(3750)
        return Dist((A*b**S(2) + C*a**S(2))/(a**S(2) + b**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))/(a + b/tan(e + f*x)), x), x) - Dist(b*(A - C)/(a**S(2) + b**S(2)), Int(S(1)/tan(e + f*x), x), x) + Simp(a*x*(A - C)/(a**S(2) + b**S(2)), x)
    rule3750 = ReplacementRule(pattern3750, replacement3750)
    pattern3751 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1562, cons31, cons94, cons1440)
    def replacement3751(B, C, e, m, f, b, a, x, A):
        rubi.append(3751)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(B*b + a*(A - C) - (A*b - B*a - C*b)*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))/(b*f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3751 = ReplacementRule(pattern3751, replacement3751)
    pattern3752 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1562, cons31, cons94, cons1440)
    def replacement3752(B, C, e, m, f, b, a, x, A):
        rubi.append(3752)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(B*b + a*(A - C) - (A*b - B*a - C*b)/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))/(b*f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3752 = ReplacementRule(pattern3752, replacement3752)
    pattern3753 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1563, cons31, cons94, cons1440)
    def replacement3753(C, e, m, f, b, a, x, A):
        rubi.append(3753)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b*tan(e + f*x))**(m + S(1))*Simp(a*(A - C) - (A*b - C*b)*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))/(b*f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3753 = ReplacementRule(pattern3753, replacement3753)
    pattern3754 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1563, cons31, cons94, cons1440)
    def replacement3754(C, e, m, f, b, a, x, A):
        rubi.append(3754)
        return Dist(S(1)/(a**S(2) + b**S(2)), Int((a + b/tan(e + f*x))**(m + S(1))*Simp(a*(A - C) - (A*b - C*b)/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))/(b*f*(a**S(2) + b**S(2))*(m + S(1))), x)
    rule3754 = ReplacementRule(pattern3754, replacement3754)
    pattern3755 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1562, cons1549)
    def replacement3755(B, C, m, f, b, a, A, x, e):
        rubi.append(3755)
        return Int((a + b*tan(e + f*x))**m*Simp(A + B*tan(e + f*x) - C, x), x) + Simp(C*(a + b*tan(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule3755 = ReplacementRule(pattern3755, replacement3755)
    pattern3756 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1562, cons1549)
    def replacement3756(B, C, m, f, b, a, A, x, e):
        rubi.append(3756)
        return Int((a + b/tan(e + f*x))**m*Simp(A + B/tan(e + f*x) - C, x), x) - Simp(C*(a + b/tan(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule3756 = ReplacementRule(pattern3756, replacement3756)
    pattern3757 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1563, cons1549)
    def replacement3757(C, m, f, b, a, A, x, e):
        rubi.append(3757)
        return Dist(A - C, Int((a + b*tan(e + f*x))**m, x), x) + Simp(C*(a + b*tan(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule3757 = ReplacementRule(pattern3757, replacement3757)
    pattern3758 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1563, cons1549)
    def replacement3758(C, m, f, b, a, A, x, e):
        rubi.append(3758)
        return Dist(A - C, Int((a + b/tan(e + f*x))**m, x), x) - Simp(C*(a + b/tan(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule3758 = ReplacementRule(pattern3758, replacement3758)
    pattern3759 = Pattern(Integral((A_ + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons1561)
    def replacement3759(C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(3759)
        return Dist(A/f, Subst(Int((a + b*x)**m*(c + d*x)**n, x), x, tan(e + f*x)), x)
    rule3759 = ReplacementRule(pattern3759, replacement3759)
    pattern3760 = Pattern(Integral((A_ + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons1561)
    def replacement3760(C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(3760)
        return -Dist(A/f, Subst(Int((a + b*x)**m*(c + d*x)**n, x), x, S(1)/tan(e + f*x)), x)
    rule3760 = ReplacementRule(pattern3760, replacement3760)
    pattern3761 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1545, cons87, cons89)
    def replacement3761(B, C, f, b, d, c, a, n, A, x, e):
        rubi.append(3761)
        return Dist(S(1)/(d*(c**S(2) + d**S(2))), Int((c + d*tan(e + f*x))**(n + S(1))*Simp(C*b*(c**S(2) + d**S(2))*tan(e + f*x)**S(2) + a*d*(A*c + B*d - C*c) + b*(A*d**S(2) - B*c*d + C*c**S(2)) + d*(-A*a*d + A*b*c + B*a*c + B*b*d + C*a*d - C*b*c)*tan(e + f*x), x), x), x) - Simp((c + d*tan(e + f*x))**(n + S(1))*(-a*d + b*c)*(A*d**S(2) - B*c*d + C*c**S(2))/(d**S(2)*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3761 = ReplacementRule(pattern3761, replacement3761)
    pattern3762 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1545, cons87, cons89)
    def replacement3762(B, C, e, f, b, d, a, c, n, x, A):
        rubi.append(3762)
        return Dist(S(1)/(d*(c**S(2) + d**S(2))), Int((c + d/tan(e + f*x))**(n + S(1))*Simp(C*b*(c**S(2) + d**S(2))/tan(e + f*x)**S(2) + a*d*(A*c + B*d - C*c) + b*(A*d**S(2) - B*c*d + C*c**S(2)) + d*(-A*a*d + A*b*c + B*a*c + B*b*d + C*a*d - C*b*c)/tan(e + f*x), x), x), x) + Simp((c + d/tan(e + f*x))**(n + S(1))*(-a*d + b*c)*(A*d**S(2) - B*c*d + C*c**S(2))/(d**S(2)*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3762 = ReplacementRule(pattern3762, replacement3762)
    pattern3763 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1545, cons87, cons89)
    def replacement3763(C, f, b, d, c, a, n, A, x, e):
        rubi.append(3763)
        return Dist(S(1)/(d*(c**S(2) + d**S(2))), Int((c + d*tan(e + f*x))**(n + S(1))*Simp(C*b*(c**S(2) + d**S(2))*tan(e + f*x)**S(2) + a*d*(A*c - C*c) + b*(A*d**S(2) + C*c**S(2)) + d*(-A*a*d + A*b*c + C*a*d - C*b*c)*tan(e + f*x), x), x), x) - Simp((c + d*tan(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))*(-a*d + b*c)/(d**S(2)*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3763 = ReplacementRule(pattern3763, replacement3763)
    pattern3764 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1545, cons87, cons89)
    def replacement3764(C, e, f, b, d, a, c, n, x, A):
        rubi.append(3764)
        return Dist(S(1)/(d*(c**S(2) + d**S(2))), Int((c + d/tan(e + f*x))**(n + S(1))*Simp(C*b*(c**S(2) + d**S(2))/tan(e + f*x)**S(2) + a*d*(A*c - C*c) + b*(A*d**S(2) + C*c**S(2)) + d*(-A*a*d + A*b*c + C*a*d - C*b*c)/tan(e + f*x), x), x), x) + Simp((c + d/tan(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))*(-a*d + b*c)/(d**S(2)*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3764 = ReplacementRule(pattern3764, replacement3764)
    pattern3765 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1545, cons346)
    def replacement3765(B, C, f, b, d, c, n, a, A, x, e):
        rubi.append(3765)
        return -Dist(S(1)/(d*(n + S(2))), Int((c + d*tan(e + f*x))**n*Simp(-A*a*d*(n + S(2)) + C*b*c - d*(n + S(2))*(A*b + B*a - C*b)*tan(e + f*x) - (C*a*d*(n + S(2)) - b*(-B*d*(n + S(2)) + C*c))*tan(e + f*x)**S(2), x), x), x) + Simp(C*b*(c + d*tan(e + f*x))**(n + S(1))*tan(e + f*x)/(d*f*(n + S(2))), x)
    rule3765 = ReplacementRule(pattern3765, replacement3765)
    pattern3766 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1545, cons346)
    def replacement3766(B, C, f, b, d, c, n, a, A, x, e):
        rubi.append(3766)
        return -Dist(S(1)/(d*(n + S(2))), Int((c + d/tan(e + f*x))**n*Simp(-A*a*d*(n + S(2)) + C*b*c - d*(n + S(2))*(A*b + B*a - C*b)/tan(e + f*x) - (C*a*d*(n + S(2)) - b*(-B*d*(n + S(2)) + C*c))/tan(e + f*x)**S(2), x), x), x) - Simp(C*b*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(n + S(2))*tan(e + f*x)), x)
    rule3766 = ReplacementRule(pattern3766, replacement3766)
    pattern3767 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1545, cons346)
    def replacement3767(C, f, b, d, c, n, a, A, x, e):
        rubi.append(3767)
        return -Dist(S(1)/(d*(n + S(2))), Int((c + d*tan(e + f*x))**n*Simp(-A*a*d*(n + S(2)) + C*b*c - d*(n + S(2))*(A*b - C*b)*tan(e + f*x) - (C*a*d*(n + S(2)) - C*b*c)*tan(e + f*x)**S(2), x), x), x) + Simp(C*b*(c + d*tan(e + f*x))**(n + S(1))*tan(e + f*x)/(d*f*(n + S(2))), x)
    rule3767 = ReplacementRule(pattern3767, replacement3767)
    pattern3768 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1545, cons346)
    def replacement3768(C, f, b, d, c, n, a, A, x, e):
        rubi.append(3768)
        return -Dist(S(1)/(d*(n + S(2))), Int((c + d/tan(e + f*x))**n*Simp(-A*a*d*(n + S(2)) + C*b*c - d*(n + S(2))*(A*b - C*b)/tan(e + f*x) - (C*a*d*(n + S(2)) - C*b*c)/tan(e + f*x)**S(2), x), x), x) - Simp(C*b*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(n + S(2))*tan(e + f*x)), x)
    rule3768 = ReplacementRule(pattern3768, replacement3768)
    pattern3769 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1439, cons1567)
    def replacement3769(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3769)
        return Dist(S(1)/(S(2)*a*m*(-a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n*Simp(a*(-A*d*(S(2)*m + n + S(1)) + B*c*m + C*d*(n + S(1))) + b*(-B*d*(n + S(1)) + c*m*(A + C)) + (A*b*d*(m + n + S(1)) + C*b*d*(m - n + S(-1)) + a*(-B*d*(m + n + S(1)) + S(2)*C*c*m))*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*(A*a + B*b - C*a)/(S(2)*f*m*(-a*d + b*c)), x)
    rule3769 = ReplacementRule(pattern3769, replacement3769)
    pattern3770 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1439, cons1567)
    def replacement3770(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3770)
        return Dist(S(1)/(S(2)*a*m*(-a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n*Simp(a*(-A*d*(S(2)*m + n + S(1)) + B*c*m + C*d*(n + S(1))) + b*(-B*d*(n + S(1)) + c*m*(A + C)) + (A*b*d*(m + n + S(1)) + C*b*d*(m - n + S(-1)) + a*(-B*d*(m + n + S(1)) + S(2)*C*c*m))/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*(A*a + B*b - C*a)/(S(2)*f*m*(-a*d + b*c)), x)
    rule3770 = ReplacementRule(pattern3770, replacement3770)
    pattern3771 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1439, cons1567)
    def replacement3771(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3771)
        return Dist(S(1)/(S(2)*a*m*(-a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n*Simp(a*(-A*d*(S(2)*m + n + S(1)) + C*d*(n + S(1))) + b*c*m*(A + C) + (A*b*d*(m + n + S(1)) + S(2)*C*a*c*m + C*b*d*(m - n + S(-1)))*tan(e + f*x), x), x), x) + Simp(a*(A - C)*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))/(S(2)*f*m*(-a*d + b*c)), x)
    rule3771 = ReplacementRule(pattern3771, replacement3771)
    pattern3772 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1439, cons1567)
    def replacement3772(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3772)
        return Dist(S(1)/(S(2)*a*m*(-a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n*Simp(a*(-A*d*(S(2)*m + n + S(1)) + C*d*(n + S(1))) + b*c*m*(A + C) + (A*b*d*(m + n + S(1)) + S(2)*C*a*c*m + C*b*d*(m - n + S(-1)))/tan(e + f*x), x), x), x) - Simp(a*(A - C)*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))/(S(2)*f*m*(-a*d + b*c)), x)
    rule3772 = ReplacementRule(pattern3772, replacement3772)
    pattern3773 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons71, cons1439, cons1303, cons87, cons89, cons1545)
    def replacement3773(B, C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3773)
        return -Dist(S(1)/(a*d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*Simp(-a*d*(n + S(1))*(A*c + B*d - C*c) - a*(-C*(c**S(2)*m - d**S(2)*(n + S(1))) + d*(-A*d + B*c)*(m + n + S(1)))*tan(e + f*x) + b*m*(A*d**S(2) - B*c*d + C*c**S(2)), x), x), x) + Simp((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*(A*d**S(2) - B*c*d + C*c**S(2))/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3773 = ReplacementRule(pattern3773, replacement3773)
    pattern3774 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons71, cons1439, cons1303, cons87, cons89, cons1545)
    def replacement3774(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3774)
        return -Dist(S(1)/(a*d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*Simp(-a*d*(n + S(1))*(A*c + B*d - C*c) - a*(-C*(c**S(2)*m - d**S(2)*(n + S(1))) + d*(-A*d + B*c)*(m + n + S(1)))/tan(e + f*x) + b*m*(A*d**S(2) - B*c*d + C*c**S(2)), x), x), x) - Simp((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*(A*d**S(2) - B*c*d + C*c**S(2))/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3774 = ReplacementRule(pattern3774, replacement3774)
    pattern3775 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons71, cons1439, cons1303, cons87, cons89, cons1545)
    def replacement3775(C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3775)
        return -Dist(S(1)/(a*d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*Simp(-a*d*(n + S(1))*(A*c - C*c) - a*(-A*d**S(2)*(m + n + S(1)) - C*(c**S(2)*m - d**S(2)*(n + S(1))))*tan(e + f*x) + b*m*(A*d**S(2) + C*c**S(2)), x), x), x) + Simp((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3775 = ReplacementRule(pattern3775, replacement3775)
    pattern3776 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons71, cons1439, cons1303, cons87, cons89, cons1545)
    def replacement3776(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3776)
        return -Dist(S(1)/(a*d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*Simp(-a*d*(n + S(1))*(A*c - C*c) - a*(-A*d**S(2)*(m + n + S(1)) - C*(c**S(2)*m - d**S(2)*(n + S(1))))/tan(e + f*x) + b*m*(A*d**S(2) + C*c**S(2)), x), x), x) - Simp((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3776 = ReplacementRule(pattern3776, replacement3776)
    pattern3777 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons71, cons1439, cons1303, cons683)
    def replacement3777(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3777)
        return Dist(S(1)/(b*d*(m + n + S(1))), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n*Simp(A*b*d*(m + n + S(1)) + C*(a*c*m - b*d*(n + S(1))) - (-B*b*d*(m + n + S(1)) + C*m*(-a*d + b*c))*tan(e + f*x), x), x), x) + Simp(C*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(1))), x)
    rule3777 = ReplacementRule(pattern3777, replacement3777)
    pattern3778 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons71, cons1439, cons1303, cons683)
    def replacement3778(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3778)
        return Dist(S(1)/(b*d*(m + n + S(1))), Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n*Simp(A*b*d*(m + n + S(1)) + C*(a*c*m - b*d*(n + S(1))) - (-B*b*d*(m + n + S(1)) + C*m*(-a*d + b*c))/tan(e + f*x), x), x), x) - Simp(C*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(1))), x)
    rule3778 = ReplacementRule(pattern3778, replacement3778)
    pattern3779 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons71, cons1439, cons1303, cons683)
    def replacement3779(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3779)
        return Dist(S(1)/(b*d*(m + n + S(1))), Int((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**n*Simp(A*b*d*(m + n + S(1)) - C*m*(-a*d + b*c)*tan(e + f*x) + C*(a*c*m - b*d*(n + S(1))), x), x), x) + Simp(C*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(1))), x)
    rule3779 = ReplacementRule(pattern3779, replacement3779)
    pattern3780 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons71, cons1439, cons1303, cons683)
    def replacement3780(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(3780)
        return Dist(S(1)/(b*d*(m + n + S(1))), Int((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**n*Simp(A*b*d*(m + n + S(1)) - C*m*(-a*d + b*c)/tan(e + f*x) + C*(a*c*m - b*d*(n + S(1))), x), x), x) - Simp(C*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(1))), x)
    rule3780 = ReplacementRule(pattern3780, replacement3780)
    pattern3781 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1440, cons1545, cons93, cons168, cons89)
    def replacement3781(B, C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3781)
        return -Dist(S(1)/(d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(1))*Simp(A*d*(-a*c*(n + S(1)) + b*d*m) - b*(-C*(c**S(2)*m - d**S(2)*(n + S(1))) + d*(-A*d + B*c)*(m + n + S(1)))*tan(e + f*x)**S(2) - d*(n + S(1))*(B*(a*c + b*d) + (A - C)*(-a*d + b*c))*tan(e + f*x) + (-B*d + C*c)*(a*d*(n + S(1)) + b*c*m), x), x), x) + Simp((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*(A*d**S(2) + c*(-B*d + C*c))/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3781 = ReplacementRule(pattern3781, replacement3781)
    pattern3782 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1440, cons1545, cons93, cons168, cons89)
    def replacement3782(B, C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3782)
        return -Dist(S(1)/(d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(1))*Simp(A*d*(-a*c*(n + S(1)) + b*d*m) - b*(-C*(c**S(2)*m - d**S(2)*(n + S(1))) + d*(-A*d + B*c)*(m + n + S(1)))/tan(e + f*x)**S(2) - d*(n + S(1))*(B*(a*c + b*d) + (A - C)*(-a*d + b*c))/tan(e + f*x) + (-B*d + C*c)*(a*d*(n + S(1)) + b*c*m), x), x), x) - Simp((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*(A*d**S(2) + c*(-B*d + C*c))/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3782 = ReplacementRule(pattern3782, replacement3782)
    pattern3783 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1440, cons1545, cons93, cons168, cons89)
    def replacement3783(C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3783)
        return -Dist(S(1)/(d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**(n + S(1))*Simp(A*d*(-a*c*(n + S(1)) + b*d*m) + C*c*(a*d*(n + S(1)) + b*c*m) + b*(A*d**S(2)*(m + n + S(1)) + C*(c**S(2)*m - d**S(2)*(n + S(1))))*tan(e + f*x)**S(2) - d*(A - C)*(n + S(1))*(-a*d + b*c)*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3783 = ReplacementRule(pattern3783, replacement3783)
    pattern3784 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1440, cons1545, cons93, cons168, cons89)
    def replacement3784(C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3784)
        return -Dist(S(1)/(d*(c**S(2) + d**S(2))*(n + S(1))), Int((a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**(n + S(1))*Simp(A*d*(-a*c*(n + S(1)) + b*d*m) + C*c*(a*d*(n + S(1)) + b*c*m) + b*(A*d**S(2)*(m + n + S(1)) + C*(c**S(2)*m - d**S(2)*(n + S(1))))/tan(e + f*x)**S(2) - d*(A - C)*(n + S(1))*(-a*d + b*c)/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))/(d*f*(c**S(2) + d**S(2))*(n + S(1))), x)
    rule3784 = ReplacementRule(pattern3784, replacement3784)
    pattern3785 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1440, cons1545, cons31, cons168, cons1568)
    def replacement3785(B, C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(3785)
        return Dist(S(1)/(d*(m + n + S(1))), Int((a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**n*Simp(A*a*d*(m + n + S(1)) - C*(a*d*(n + S(1)) + b*c*m) + d*(m + n + S(1))*(A*b + B*a - C*b)*tan(e + f*x) - (-B*b*d*(m + n + S(1)) + C*m*(-a*d + b*c))*tan(e + f*x)**S(2), x), x), x) + Simp(C*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(1))), x)
    rule3785 = ReplacementRule(pattern3785, replacement3785)
    pattern3786 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1440, cons1545, cons31, cons168, cons1568)
    def replacement3786(B, C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(3786)
        return Dist(S(1)/(d*(m + n + S(1))), Int((a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**n*Simp(A*a*d*(m + n + S(1)) - C*(a*d*(n + S(1)) + b*c*m) + d*(m + n + S(1))*(A*b + B*a - C*b)/tan(e + f*x) - (-B*b*d*(m + n + S(1)) + C*m*(-a*d + b*c))/tan(e + f*x)**S(2), x), x), x) - Simp(C*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(1))), x)
    rule3786 = ReplacementRule(pattern3786, replacement3786)
    pattern3787 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1440, cons1545, cons31, cons168, cons1568)
    def replacement3787(C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(3787)
        return Dist(S(1)/(d*(m + n + S(1))), Int((a + b*tan(e + f*x))**(m + S(-1))*(c + d*tan(e + f*x))**n*Simp(A*a*d*(m + n + S(1)) - C*m*(-a*d + b*c)*tan(e + f*x)**S(2) - C*(a*d*(n + S(1)) + b*c*m) + d*(A*b - C*b)*(m + n + S(1))*tan(e + f*x), x), x), x) + Simp(C*(a + b*tan(e + f*x))**m*(c + d*tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(1))), x)
    rule3787 = ReplacementRule(pattern3787, replacement3787)
    pattern3788 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1440, cons1545, cons31, cons168, cons1568)
    def replacement3788(C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(3788)
        return Dist(S(1)/(d*(m + n + S(1))), Int((a + b/tan(e + f*x))**(m + S(-1))*(c + d/tan(e + f*x))**n*Simp(A*a*d*(m + n + S(1)) - C*m*(-a*d + b*c)/tan(e + f*x)**S(2) - C*(a*d*(n + S(1)) + b*c*m) + d*(A*b - C*b)*(m + n + S(1))/tan(e + f*x), x), x), x) - Simp(C*(a + b/tan(e + f*x))**m*(c + d/tan(e + f*x))**(n + S(1))/(d*f*(m + n + S(1))), x)
    rule3788 = ReplacementRule(pattern3788, replacement3788)
    pattern3789 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1440, cons1545, cons31, cons94, cons1557)
    def replacement3789(B, C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3789)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n*Simp(A*(a*(m + S(1))*(-a*d + b*c) - b**S(2)*d*(m + n + S(2))) - d*(A*b**S(2) - a*(B*b - C*a))*(m + n + S(2))*tan(e + f*x)**S(2) - (m + S(1))*(-a*d + b*c)*(A*b - B*a - C*b)*tan(e + f*x) + (B*b - C*a)*(a*d*(n + S(1)) + b*c*(m + S(1))), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(1))*(A*b**S(2) - a*(B*b - C*a))/(f*(a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3789 = ReplacementRule(pattern3789, replacement3789)
    pattern3790 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1440, cons1545, cons31, cons94, cons1557)
    def replacement3790(B, C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3790)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n*Simp(A*(a*(m + S(1))*(-a*d + b*c) - b**S(2)*d*(m + n + S(2))) - d*(A*b**S(2) - a*(B*b - C*a))*(m + n + S(2))/tan(e + f*x)**S(2) - (m + S(1))*(-a*d + b*c)*(A*b - B*a - C*b)/tan(e + f*x) + (B*b - C*a)*(a*d*(n + S(1)) + b*c*(m + S(1))), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(1))*(A*b**S(2) - a*(B*b - C*a))/(f*(a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3790 = ReplacementRule(pattern3790, replacement3790)
    pattern3791 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1440, cons1545, cons31, cons94, cons1557)
    def replacement3791(C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3791)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**n*Simp(A*(a*(m + S(1))*(-a*d + b*c) - b**S(2)*d*(m + n + S(2))) - C*a*(a*d*(n + S(1)) + b*c*(m + S(1))) - d*(A*b**S(2) + C*a**S(2))*(m + n + S(2))*tan(e + f*x)**S(2) - (m + S(1))*(A*b - C*b)*(-a*d + b*c)*tan(e + f*x), x), x), x) + Simp((a + b*tan(e + f*x))**(m + S(1))*(c + d*tan(e + f*x))**(n + S(1))*(A*b**S(2) + C*a**S(2))/(f*(a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3791 = ReplacementRule(pattern3791, replacement3791)
    pattern3792 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1440, cons1545, cons31, cons94, cons1557)
    def replacement3792(C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3792)
        return Dist(S(1)/((a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**n*Simp(A*(a*(m + S(1))*(-a*d + b*c) - b**S(2)*d*(m + n + S(2))) - C*a*(a*d*(n + S(1)) + b*c*(m + S(1))) - d*(A*b**S(2) + C*a**S(2))*(m + n + S(2))/tan(e + f*x)**S(2) - (m + S(1))*(A*b - C*b)*(-a*d + b*c)/tan(e + f*x), x), x), x) - Simp((a + b/tan(e + f*x))**(m + S(1))*(c + d/tan(e + f*x))**(n + S(1))*(A*b**S(2) + C*a**S(2))/(f*(a**S(2) + b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3792 = ReplacementRule(pattern3792, replacement3792)
    pattern3793 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1440, cons1545)
    def replacement3793(B, C, f, b, d, c, a, A, x, e):
        rubi.append(3793)
        return Dist((A*b**S(2) - B*a*b + C*a**S(2))/((a**S(2) + b**S(2))*(-a*d + b*c)), Int((-a*tan(e + f*x) + b)/(a + b*tan(e + f*x)), x), x) - Dist((A*d**S(2) - B*c*d + C*c**S(2))/((c**S(2) + d**S(2))*(-a*d + b*c)), Int((-c*tan(e + f*x) + d)/(c + d*tan(e + f*x)), x), x) + Simp(x*(a*(A*c + B*d - C*c) + b*(-A*d + B*c + C*d))/((a**S(2) + b**S(2))*(c**S(2) + d**S(2))), x)
    rule3793 = ReplacementRule(pattern3793, replacement3793)
    pattern3794 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1440, cons1545)
    def replacement3794(B, C, f, b, d, c, a, A, x, e):
        rubi.append(3794)
        return Dist((A*b**S(2) - B*a*b + C*a**S(2))/((a**S(2) + b**S(2))*(-a*d + b*c)), Int((-a/tan(e + f*x) + b)/(a + b/tan(e + f*x)), x), x) - Dist((A*d**S(2) - B*c*d + C*c**S(2))/((c**S(2) + d**S(2))*(-a*d + b*c)), Int((-c/tan(e + f*x) + d)/(c + d/tan(e + f*x)), x), x) + Simp(x*(a*(A*c + B*d - C*c) + b*(-A*d + B*c + C*d))/((a**S(2) + b**S(2))*(c**S(2) + d**S(2))), x)
    rule3794 = ReplacementRule(pattern3794, replacement3794)
    pattern3795 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1440, cons1545)
    def replacement3795(C, f, b, d, c, a, A, x, e):
        rubi.append(3795)
        return Dist((A*b**S(2) + C*a**S(2))/((a**S(2) + b**S(2))*(-a*d + b*c)), Int((-a*tan(e + f*x) + b)/(a + b*tan(e + f*x)), x), x) - Dist((A*d**S(2) + C*c**S(2))/((c**S(2) + d**S(2))*(-a*d + b*c)), Int((-c*tan(e + f*x) + d)/(c + d*tan(e + f*x)), x), x) + Simp(x*(a*(A*c - C*c) - b*(A*d - C*d))/((a**S(2) + b**S(2))*(c**S(2) + d**S(2))), x)
    rule3795 = ReplacementRule(pattern3795, replacement3795)
    pattern3796 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1440, cons1545)
    def replacement3796(C, f, b, d, c, a, A, x, e):
        rubi.append(3796)
        return Dist((A*b**S(2) + C*a**S(2))/((a**S(2) + b**S(2))*(-a*d + b*c)), Int((-a/tan(e + f*x) + b)/(a + b/tan(e + f*x)), x), x) - Dist((A*d**S(2) + C*c**S(2))/((c**S(2) + d**S(2))*(-a*d + b*c)), Int((-c/tan(e + f*x) + d)/(c + d/tan(e + f*x)), x), x) + Simp(x*(a*(A*c - C*c) - b*(A*d - C*d))/((a**S(2) + b**S(2))*(c**S(2) + d**S(2))), x)
    rule3796 = ReplacementRule(pattern3796, replacement3796)
    pattern3797 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1440, cons1545, cons1327, cons1569)
    def replacement3797(B, C, f, b, d, c, a, n, A, x, e):
        rubi.append(3797)
        return Dist((A*b**S(2) - B*a*b + C*a**S(2))/(a**S(2) + b**S(2)), Int((c + d*tan(e + f*x))**n*(tan(e + f*x)**S(2) + S(1))/(a + b*tan(e + f*x)), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int((c + d*tan(e + f*x))**n*Simp(B*b + a*(A - C) + (B*a - b*(A - C))*tan(e + f*x), x), x), x)
    rule3797 = ReplacementRule(pattern3797, replacement3797)
    pattern3798 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1440, cons1545, cons1327, cons1569)
    def replacement3798(B, C, e, f, b, d, a, c, n, x, A):
        rubi.append(3798)
        return Dist((A*b**S(2) - B*a*b + C*a**S(2))/(a**S(2) + b**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))*(c + d/tan(e + f*x))**n/(a + b/tan(e + f*x)), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int((c + d/tan(e + f*x))**n*Simp(B*b + a*(A - C) + (B*a - b*(A - C))/tan(e + f*x), x), x), x)
    rule3798 = ReplacementRule(pattern3798, replacement3798)
    pattern3799 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1440, cons1545, cons1327, cons1569)
    def replacement3799(C, f, b, d, c, a, n, A, x, e):
        rubi.append(3799)
        return Dist((A*b**S(2) + C*a**S(2))/(a**S(2) + b**S(2)), Int((c + d*tan(e + f*x))**n*(tan(e + f*x)**S(2) + S(1))/(a + b*tan(e + f*x)), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int((c + d*tan(e + f*x))**n*Simp(a*(A - C) - (A*b - C*b)*tan(e + f*x), x), x), x)
    rule3799 = ReplacementRule(pattern3799, replacement3799)
    pattern3800 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1440, cons1545, cons1327, cons1569)
    def replacement3800(C, e, f, b, d, a, c, n, x, A):
        rubi.append(3800)
        return Dist((A*b**S(2) + C*a**S(2))/(a**S(2) + b**S(2)), Int((S(1) + tan(e + f*x)**(S(-2)))*(c + d/tan(e + f*x))**n/(a + b/tan(e + f*x)), x), x) + Dist(S(1)/(a**S(2) + b**S(2)), Int((c + d/tan(e + f*x))**n*Simp(a*(A - C) - (A*b - C*b)/tan(e + f*x), x), x), x)
    rule3800 = ReplacementRule(pattern3800, replacement3800)
    pattern3801 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons71, cons1440, cons1545)
    def replacement3801(B, C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3801)
        return Dist(S(1)/(b*f), Subst(Int((a + x)**m*(c + d*x/b)**n*(A*b**S(2) + B*b*x + C*x**S(2))/(b**S(2) + x**S(2)), x), x, b*tan(e + f*x)), x)
    rule3801 = ReplacementRule(pattern3801, replacement3801)
    pattern3802 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons71, cons1440, cons1545)
    def replacement3802(B, C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3802)
        return -Dist(S(1)/(b*f), Subst(Int((a + x)**m*(c + d*x/b)**n*(A*b**S(2) + B*b*x + C*x**S(2))/(b**S(2) + x**S(2)), x), x, b/tan(e + f*x)), x)
    rule3802 = ReplacementRule(pattern3802, replacement3802)
    pattern3803 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons71, cons1440, cons1545)
    def replacement3803(C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3803)
        return Dist(S(1)/(b*f), Subst(Int((a + x)**m*(c + d*x/b)**n*(A*b**S(2) + C*x**S(2))/(b**S(2) + x**S(2)), x), x, b*tan(e + f*x)), x)
    rule3803 = ReplacementRule(pattern3803, replacement3803)
    pattern3804 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons71, cons1440, cons1545)
    def replacement3804(C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3804)
        return -Dist(S(1)/(b*f), Subst(Int((a + x)**m*(c + d*x/b)**n*(A*b**S(2) + C*x**S(2))/(b**S(2) + x**S(2)), x), x, b/tan(e + f*x)), x)
    rule3804 = ReplacementRule(pattern3804, replacement3804)
    pattern3805 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons1492)
    def replacement3805(b, d, c, a, x):
        rubi.append(3805)
        return Dist(S(1)/a, Int(cos(c + d*x)**S(2), x), x)
    rule3805 = ReplacementRule(pattern3805, replacement3805)
    pattern3806 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons1492)
    def replacement3806(b, d, c, a, x):
        rubi.append(3806)
        return Dist(S(1)/a, Int(sin(c + d*x)**S(2), x), x)
    rule3806 = ReplacementRule(pattern3806, replacement3806)
    pattern3807 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons1456)
    def replacement3807(b, d, c, a, x):
        rubi.append(3807)
        return -Dist(b/(a - b), Int(S(1)/((a + b*tan(c + d*x)**S(2))*cos(c + d*x)**S(2)), x), x) + Simp(x/(a - b), x)
    rule3807 = ReplacementRule(pattern3807, replacement3807)
    pattern3808 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons1456)
    def replacement3808(b, d, c, a, x):
        rubi.append(3808)
        return -Dist(b/(a - b), Int(S(1)/((a + b/tan(c + d*x)**S(2))*sin(c + d*x)**S(2)), x), x) + Simp(x/(a - b), x)
    rule3808 = ReplacementRule(pattern3808, replacement3808)
    pattern3809 = Pattern(Integral((a_ + (WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement3809(p, b, d, c, a, n, x, e):
        rubi.append(3809)
        return Dist(e/d, Subst(Int((a + b*x**n)**p/(e**S(2) + x**S(2)), x), x, e*tan(c + d*x)), x)
    rule3809 = ReplacementRule(pattern3809, replacement3809)
    pattern3810 = Pattern(Integral((a_ + (WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement3810(p, b, d, c, n, a, x, e):
        rubi.append(3810)
        return -Dist(e/d, Subst(Int((a + b*x**n)**p/(e**S(2) + x**S(2)), x), x, e/tan(c + d*x)), x)
    rule3810 = ReplacementRule(pattern3810, replacement3810)
    def With3811(p, m, b, d, c, a, n, x, e):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(3811)
        return Dist(f**(m + S(1))/d, Subst(Int(x**m*(a + b*(e*f*x)**n)**p*(f**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1)), x), x, tan(c + d*x)/f), x)
    pattern3811 = Pattern(Integral((a_ + (WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1515)
    rule3811 = ReplacementRule(pattern3811, With3811)
    def With3812(p, m, b, d, c, n, a, x, e):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(3812)
        return -Dist(f**(m + S(1))/d, Subst(Int(x**m*(a + b*(e*f*x)**n)**p*(f**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1)), x), x, S(1)/(f*tan(c + d*x))), x)
    pattern3812 = Pattern(Integral((a_ + (WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1515)
    rule3812 = ReplacementRule(pattern3812, With3812)
    def With3813(p, m, b, d, c, a, n, x):
        f = FreeFactors(cos(c + d*x), x)
        rubi.append(3813)
        return -Dist(f/d, Subst(Int((f*x)**(-n*p)*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*ExpandToSum(a*(f*x)**n + b*(-f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p, x), x, cos(c + d*x)/f), x)
    pattern3813 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**WC('p', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1481, cons1479, cons38)
    rule3813 = ReplacementRule(pattern3813, With3813)
    def With3814(p, m, b, d, c, n, a, x):
        f = FreeFactors(sin(c + d*x), x)
        rubi.append(3814)
        return Dist(f/d, Subst(Int((f*x)**(-n*p)*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*ExpandToSum(a*(f*x)**n + b*(-f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p, x), x, sin(c + d*x)/f), x)
    pattern3814 = Pattern(Integral((a_ + (S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1481, cons1479, cons38)
    rule3814 = ReplacementRule(pattern3814, With3814)
    def With3815(p, m, b, d, c, a, n, x, e):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(3815)
        return Dist(f/d, Subst(Int((a + b*(e*f*x)**n)**p*(f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)), x), x, tan(c + d*x)/f), x)
    pattern3815 = Pattern(Integral((a_ + (WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*(S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1515)
    rule3815 = ReplacementRule(pattern3815, With3815)
    def With3816(p, m, b, d, c, n, a, x, e):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(3816)
        return -Dist(f/d, Subst(Int((a + b*(e*f*x)**n)**p*(f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)), x), x, S(1)/(f*tan(c + d*x))), x)
    pattern3816 = Pattern(Integral((a_ + (WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*(S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1515)
    rule3816 = ReplacementRule(pattern3816, With3816)
    def With3817(p, m, b, d, c, a, n, x):
        f = FreeFactors(sin(c + d*x), x)
        rubi.append(3817)
        return Dist(f/d, Subst(Int((-f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1)/2)*ExpandToSum(a*(-f**S(2)*x**S(2) + S(1))**(n/S(2)) + b*(f*x)**n, x)**p, x), x, sin(c + d*x)/f), x)
    pattern3817 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**WC('p', S(1))*(S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1228, cons743, cons38)
    rule3817 = ReplacementRule(pattern3817, With3817)
    def With3818(p, m, b, d, c, n, a, x):
        f = FreeFactors(cos(c + d*x), x)
        rubi.append(3818)
        return -Dist(f/d, Subst(Int((-f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1)/2)*ExpandToSum(a*(-f**S(2)*x**S(2) + S(1))**(n/S(2)) + b*(f*x)**n, x)**p, x), x, cos(c + d*x)/f), x)
    pattern3818 = Pattern(Integral((a_ + (S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*(S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1228, cons743, cons38)
    rule3818 = ReplacementRule(pattern3818, With3818)
    pattern3819 = Pattern(Integral((a_ + (WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*tan(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement3819(p, m, b, d, c, a, n, x, e):
        rubi.append(3819)
        return Dist(e/d, Subst(Int((x/e)**m*(a + b*x**n)**p/(e**S(2) + x**S(2)), x), x, e*tan(c + d*x)), x)
    rule3819 = ReplacementRule(pattern3819, replacement3819)
    pattern3820 = Pattern(Integral((a_ + (WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement3820(p, m, b, d, c, n, a, x, e):
        rubi.append(3820)
        return -Dist(e/d, Subst(Int((x/e)**m*(a + b*x**n)**p/(e**S(2) + x**S(2)), x), x, e/tan(c + d*x)), x)
    rule3820 = ReplacementRule(pattern3820, replacement3820)
    pattern3821 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons45, cons38)
    def replacement3821(p, b, n2, d, c, n, a, x, e):
        rubi.append(3821)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*tan(d + e*x)**n)**(S(2)*p), x), x)
    rule3821 = ReplacementRule(pattern3821, replacement3821)
    pattern3822 = Pattern(Integral((a_ + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons45, cons38)
    def replacement3822(p, b, n2, d, c, n, a, x, e):
        rubi.append(3822)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*(S(1)/tan(d + e*x))**n)**(S(2)*p), x), x)
    rule3822 = ReplacementRule(pattern3822, replacement3822)
    pattern3823 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons45, cons147)
    def replacement3823(p, b, n2, d, c, n, a, x, e):
        rubi.append(3823)
        return Dist((b + S(2)*c*tan(d + e*x)**n)**(-S(2)*p)*(a + b*tan(d + e*x)**n + c*tan(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*tan(d + e*x)**n)**(S(2)*p), x), x)
    rule3823 = ReplacementRule(pattern3823, replacement3823)
    pattern3824 = Pattern(Integral((a_ + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons45, cons147)
    def replacement3824(p, b, n2, d, c, n, a, x, e):
        rubi.append(3824)
        return Dist((b + S(2)*c*(S(1)/tan(d + e*x))**n)**(-S(2)*p)*(a + b*(S(1)/tan(d + e*x))**n + c*(S(1)/tan(d + e*x))**(S(2)*n))**p, Int((b + S(2)*c*(S(1)/tan(d + e*x))**n)**(S(2)*p), x), x)
    rule3824 = ReplacementRule(pattern3824, replacement3824)
    def With3825(b, n2, d, a, n, c, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(3825)
        return Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*tan(d + e*x)**n - q), x), x) - Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*tan(d + e*x)**n + q), x), x)
    pattern3825 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons226)
    rule3825 = ReplacementRule(pattern3825, With3825)
    def With3826(b, n2, d, a, n, c, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(3826)
        return Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*(S(1)/tan(d + e*x))**n - q), x), x) - Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*(S(1)/tan(d + e*x))**n + q), x), x)
    pattern3826 = Pattern(Integral(S(1)/((S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons226)
    rule3826 = ReplacementRule(pattern3826, With3826)
    pattern3827 = Pattern(Integral(((WC('f', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (WC('f', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*sin(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons46, cons1515)
    def replacement3827(p, m, f, b, n2, d, a, n, c, x, e):
        rubi.append(3827)
        return Dist(f/e, Subst(Int(x**m*(f**S(2) + x**S(2))**(-m/S(2) + S(-1))*(a + b*x**n + c*x**(S(2)*n))**p, x), x, f*tan(d + e*x)), x)
    rule3827 = ReplacementRule(pattern3827, replacement3827)
    pattern3828 = Pattern(Integral(((WC('f', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (WC('f', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*cos(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons46, cons1515)
    def replacement3828(p, m, f, b, n2, d, a, n, c, x, e):
        rubi.append(3828)
        return -Dist(f/e, Subst(Int(x**m*(f**S(2) + x**S(2))**(-m/S(2) + S(-1))*(a + b*x**n + c*x**(S(2)*n))**p, x), x, f/tan(d + e*x)), x)
    rule3828 = ReplacementRule(pattern3828, replacement3828)
    def With3829(p, m, b, n2, d, a, n, c, x, e):
        g = FreeFactors(cos(d + e*x), x)
        rubi.append(3829)
        return -Dist(g/e, Subst(Int((g*x)**(-S(2)*n*p)*(-g**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*ExpandToSum(a*(g*x)**(S(2)*n) + b*(g*x)**n*(-g**S(2)*x**S(2) + S(1))**(n/S(2)) + c*(-g**S(2)*x**S(2) + S(1))**n, x)**p, x), x, cos(d + e*x)/g), x)
    pattern3829 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1481, cons1479, cons38)
    rule3829 = ReplacementRule(pattern3829, With3829)
    def With3830(p, m, b, n2, d, a, n, c, x, e):
        g = FreeFactors(sin(d + e*x), x)
        rubi.append(3830)
        return Dist(g/e, Subst(Int((g*x)**(-S(2)*n*p)*(-g**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*ExpandToSum(a*(g*x)**(S(2)*n) + b*(g*x)**n*(-g**S(2)*x**S(2) + S(1))**(n/S(2)) + c*(-g**S(2)*x**S(2) + S(1))**n, x)**p, x), x, sin(d + e*x)/g), x)
    pattern3830 = Pattern(Integral(((S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1481, cons1479, cons38)
    rule3830 = ReplacementRule(pattern3830, With3830)
    pattern3831 = Pattern(Integral(((WC('f', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (WC('f', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons46, cons1480)
    def replacement3831(p, m, f, b, n2, d, a, n, c, x, e):
        rubi.append(3831)
        return Dist(f**(m + S(1))/e, Subst(Int((f**S(2) + x**S(2))**(-m/S(2) + S(-1))*(a + b*x**n + c*x**(S(2)*n))**p, x), x, f*tan(d + e*x)), x)
    rule3831 = ReplacementRule(pattern3831, replacement3831)
    pattern3832 = Pattern(Integral(((WC('f', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (WC('f', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons46, cons1480)
    def replacement3832(p, m, f, b, n2, d, a, n, c, x, e):
        rubi.append(3832)
        return -Dist(f**(m + S(1))/e, Subst(Int((f**S(2) + x**S(2))**(-m/S(2) + S(-1))*(a + b*x**n + c*x**(S(2)*n))**p, x), x, f/tan(d + e*x)), x)
    rule3832 = ReplacementRule(pattern3832, replacement3832)
    def With3833(p, m, b, n2, d, a, n, c, x, e):
        g = FreeFactors(sin(d + e*x), x)
        rubi.append(3833)
        return Dist(g/e, Subst(Int((-g**S(2)*x**S(2) + S(1))**(m/S(2) - n*p + S(-1)/2)*ExpandToSum(a*(-x**S(2) + S(1))**n + b*x**n*(-x**S(2) + S(1))**(n/S(2)) + c*x**(S(2)*n), x)**p, x), x, sin(d + e*x)/g), x)
    pattern3833 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1481, cons1479, cons38)
    rule3833 = ReplacementRule(pattern3833, With3833)
    def With3834(p, m, b, n2, d, a, n, c, x, e):
        g = FreeFactors(cos(d + e*x), x)
        rubi.append(3834)
        return -Dist(g/e, Subst(Int((-g**S(2)*x**S(2) + S(1))**(m/S(2) - n*p + S(-1)/2)*ExpandToSum(a*(-x**S(2) + S(1))**n + b*x**n*(-x**S(2) + S(1))**(n/S(2)) + c*x**(S(2)*n), x)**p, x), x, cos(d + e*x)/g), x)
    pattern3834 = Pattern(Integral(((S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1481, cons1479, cons38)
    rule3834 = ReplacementRule(pattern3834, With3834)
    pattern3835 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons45, cons38)
    def replacement3835(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3835)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*tan(d + e*x)**n)**(S(2)*p)*tan(d + e*x)**m, x), x)
    rule3835 = ReplacementRule(pattern3835, replacement3835)
    pattern3836 = Pattern(Integral(((S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons45, cons38)
    def replacement3836(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3836)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*(S(1)/tan(d + e*x))**n)**(S(2)*p)*(S(1)/tan(d + e*x))**m, x), x)
    rule3836 = ReplacementRule(pattern3836, replacement3836)
    pattern3837 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons45, cons147)
    def replacement3837(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3837)
        return Dist((b + S(2)*c*tan(d + e*x)**n)**(-S(2)*p)*(a + b*tan(d + e*x)**n + c*tan(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*tan(d + e*x)**n)**(S(2)*p)*tan(d + e*x)**m, x), x)
    rule3837 = ReplacementRule(pattern3837, replacement3837)
    pattern3838 = Pattern(Integral(((S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons45, cons147)
    def replacement3838(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3838)
        return Dist((b + S(2)*c*(S(1)/tan(d + e*x))**n)**(-S(2)*p)*(a + b*(S(1)/tan(d + e*x))**n + c*(S(1)/tan(d + e*x))**(S(2)*n))**p, Int((b + S(2)*c*(S(1)/tan(d + e*x))**n)**(S(2)*p)*(S(1)/tan(d + e*x))**m, x), x)
    rule3838 = ReplacementRule(pattern3838, replacement3838)
    pattern3839 = Pattern(Integral(((WC('f', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (WC('f', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons46, cons226)
    def replacement3839(p, m, f, b, n2, d, a, n, c, x, e):
        rubi.append(3839)
        return Dist(f/e, Subst(Int((x/f)**m*(a + b*x**n + c*x**(S(2)*n))**p/(f**S(2) + x**S(2)), x), x, f*tan(d + e*x)), x)
    rule3839 = ReplacementRule(pattern3839, replacement3839)
    pattern3840 = Pattern(Integral(((WC('f', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (WC('f', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons46, cons226)
    def replacement3840(p, m, f, b, n2, d, a, n, c, x, e):
        rubi.append(3840)
        return -Dist(f/e, Subst(Int((x/f)**m*(a + b*x**n + c*x**(S(2)*n))**p/(f**S(2) + x**S(2)), x), x, f/tan(d + e*x)), x)
    rule3840 = ReplacementRule(pattern3840, replacement3840)
    pattern3841 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons45, cons38)
    def replacement3841(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3841)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*tan(d + e*x)**n)**(S(2)*p)*(S(1)/tan(d + e*x))**m, x), x)
    rule3841 = ReplacementRule(pattern3841, replacement3841)
    pattern3842 = Pattern(Integral(((S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons45, cons38)
    def replacement3842(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3842)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*(S(1)/tan(d + e*x))**n)**(S(2)*p)*tan(d + e*x)**m, x), x)
    rule3842 = ReplacementRule(pattern3842, replacement3842)
    pattern3843 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons45, cons147)
    def replacement3843(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3843)
        return Dist((b + S(2)*c*tan(d + e*x)**n)**(-S(2)*p)*(a + b*tan(d + e*x)**n + c*tan(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*tan(d + e*x)**n)**(S(2)*p)*(S(1)/tan(d + e*x))**m, x), x)
    rule3843 = ReplacementRule(pattern3843, replacement3843)
    pattern3844 = Pattern(Integral(((S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons45, cons147)
    def replacement3844(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3844)
        return Dist((b + S(2)*c*(S(1)/tan(d + e*x))**n)**(-S(2)*p)*(a + b*(S(1)/tan(d + e*x))**n + c*(S(1)/tan(d + e*x))**(S(2)*n))**p, Int((b + S(2)*c*(S(1)/tan(d + e*x))**n)**(S(2)*p)*tan(d + e*x)**m, x), x)
    rule3844 = ReplacementRule(pattern3844, replacement3844)
    def With3845(p, m, b, n2, d, a, c, n, x, e):
        g = FreeFactors(S(1)/tan(d + e*x), x)
        rubi.append(3845)
        return Dist(g/e, Subst(Int((g*x)**(m - S(2)*n*p)*(a*(g*x)**(S(2)*n) + b*(g*x)**n + c)**p/(g**S(2)*x**S(2) + S(1)), x), x, S(1)/(g*tan(d + e*x))), x)
    pattern3845 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**n_ + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**n2_)**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons46, cons226, cons1479)
    rule3845 = ReplacementRule(pattern3845, With3845)
    def With3846(p, m, b, n2, d, c, a, n, x, e):
        g = FreeFactors(tan(d + e*x), x)
        rubi.append(3846)
        return -Dist(g/e, Subst(Int((g*x)**(m - S(2)*n*p)*(a*(g*x)**(S(2)*n) + b*(g*x)**n + c)**p/(g**S(2)*x**S(2) + S(1)), x), x, tan(d + e*x)/g), x)
    pattern3846 = Pattern(Integral(((S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**n2_*WC('c', S(1)) + (S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**n_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons46, cons226, cons1479)
    rule3846 = ReplacementRule(pattern3846, With3846)
    pattern3847 = Pattern(Integral((A_ + WC('B', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons85)
    def replacement3847(B, b, d, c, a, n, A, x, e):
        rubi.append(3847)
        return Dist(S(4)**(-n)*c**(-n), Int((A + B*tan(d + e*x))*(b + S(2)*c*tan(d + e*x))**(S(2)*n), x), x)
    rule3847 = ReplacementRule(pattern3847, replacement3847)
    pattern3848 = Pattern(Integral((A_ + WC('B', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons85)
    def replacement3848(B, b, d, c, a, n, A, x, e):
        rubi.append(3848)
        return Dist(S(4)**(-n)*c**(-n), Int((A + B/tan(d + e*x))*(b + S(2)*c/tan(d + e*x))**(S(2)*n), x), x)
    rule3848 = ReplacementRule(pattern3848, replacement3848)
    pattern3849 = Pattern(Integral((A_ + WC('B', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons23)
    def replacement3849(B, b, d, c, a, n, A, x, e):
        rubi.append(3849)
        return Dist((b + S(2)*c*tan(d + e*x))**(-S(2)*n)*(a + b*tan(d + e*x) + c*tan(d + e*x)**S(2))**n, Int((A + B*tan(d + e*x))*(b + S(2)*c*tan(d + e*x))**(S(2)*n), x), x)
    rule3849 = ReplacementRule(pattern3849, replacement3849)
    pattern3850 = Pattern(Integral((A_ + WC('B', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons23)
    def replacement3850(B, b, d, c, a, n, A, x, e):
        rubi.append(3850)
        return Dist((b + S(2)*c/tan(d + e*x))**(-S(2)*n)*(a + b/tan(d + e*x) + c/tan(d + e*x)**S(2))**n, Int((A + B/tan(d + e*x))*(b + S(2)*c/tan(d + e*x))**(S(2)*n), x), x)
    rule3850 = ReplacementRule(pattern3850, replacement3850)
    def With3851(B, b, d, a, c, A, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(3851)
        return Dist(B - (-S(2)*A*c + B*b)/q, Int(S(1)/Simp(b + S(2)*c*tan(d + e*x) - q, x), x), x) + Dist(B + (-S(2)*A*c + B*b)/q, Int(S(1)/Simp(b + S(2)*c*tan(d + e*x) + q, x), x), x)
    pattern3851 = Pattern(Integral((A_ + WC('B', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226)
    rule3851 = ReplacementRule(pattern3851, With3851)
    def With3852(B, b, d, c, a, A, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(3852)
        return Dist(B - (-S(2)*A*c + B*b)/q, Int(S(1)/Simp(b + S(2)*c/tan(d + e*x) - q, x), x), x) + Dist(B + (-S(2)*A*c + B*b)/q, Int(S(1)/Simp(b + S(2)*c/tan(d + e*x) + q, x), x), x)
    pattern3852 = Pattern(Integral((A_ + WC('B', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226)
    rule3852 = ReplacementRule(pattern3852, With3852)
    pattern3853 = Pattern(Integral((A_ + WC('B', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226, cons85)
    def replacement3853(B, b, d, a, c, n, A, x, e):
        rubi.append(3853)
        return Int(ExpandTrig((A + B*tan(d + e*x))*(a + b*tan(d + e*x) + c*tan(d + e*x)**S(2))**n, x), x)
    rule3853 = ReplacementRule(pattern3853, replacement3853)
    pattern3854 = Pattern(Integral((A_ + WC('B', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226, cons85)
    def replacement3854(B, b, d, c, a, n, A, x, e):
        rubi.append(3854)
        return Int(ExpandTrig((A + B/tan(d + e*x))*(a + b/tan(d + e*x) + c/tan(d + e*x)**S(2))**n, x), x)
    rule3854 = ReplacementRule(pattern3854, replacement3854)
    pattern3855 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons62)
    def replacement3855(m, f, d, c, x, e):
        rubi.append(3855)
        return -Dist(S(2)*I, Int((c + d*x)**m*exp(S(2)*I*(e + f*x))/(exp(S(2)*I*(e + f*x)) + S(1)), x), x) + Simp(I*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule3855 = ReplacementRule(pattern3855, replacement3855)
    pattern3856 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons62)
    def replacement3856(m, f, d, c, x, e):
        rubi.append(3856)
        return -Dist(S(2)*I, Int((c + d*x)**m*exp(S(2)*I*(e + f*x))/(-exp(S(2)*I*(e + f*x)) + S(1)), x), x) - Simp(I*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule3856 = ReplacementRule(pattern3856, replacement3856)
    pattern3857 = Pattern(Integral((WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons93, cons165, cons168)
    def replacement3857(m, f, b, d, c, n, x, e):
        rubi.append(3857)
        return -Dist(b**S(2), Int((b*tan(e + f*x))**(n + S(-2))*(c + d*x)**m, x), x) - Dist(b*d*m/(f*(n + S(-1))), Int((b*tan(e + f*x))**(n + S(-1))*(c + d*x)**(m + S(-1)), x), x) + Simp(b*(b*tan(e + f*x))**(n + S(-1))*(c + d*x)**m/(f*(n + S(-1))), x)
    rule3857 = ReplacementRule(pattern3857, replacement3857)
    pattern3858 = Pattern(Integral((WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons93, cons165, cons168)
    def replacement3858(m, f, b, d, c, n, x, e):
        rubi.append(3858)
        return -Dist(b**S(2), Int((b/tan(e + f*x))**(n + S(-2))*(c + d*x)**m, x), x) + Dist(b*d*m/(f*(n + S(-1))), Int((b/tan(e + f*x))**(n + S(-1))*(c + d*x)**(m + S(-1)), x), x) - Simp(b*(b/tan(e + f*x))**(n + S(-1))*(c + d*x)**m/(f*(n + S(-1))), x)
    rule3858 = ReplacementRule(pattern3858, replacement3858)
    pattern3859 = Pattern(Integral((WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons93, cons89, cons168)
    def replacement3859(m, f, b, d, c, n, x, e):
        rubi.append(3859)
        return -Dist(b**(S(-2)), Int((b*tan(e + f*x))**(n + S(2))*(c + d*x)**m, x), x) - Dist(d*m/(b*f*(n + S(1))), Int((b*tan(e + f*x))**(n + S(1))*(c + d*x)**(m + S(-1)), x), x) + Simp((b*tan(e + f*x))**(n + S(1))*(c + d*x)**m/(b*f*(n + S(1))), x)
    rule3859 = ReplacementRule(pattern3859, replacement3859)
    pattern3860 = Pattern(Integral((WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons93, cons89, cons168)
    def replacement3860(m, f, b, d, c, n, x, e):
        rubi.append(3860)
        return -Dist(b**(S(-2)), Int((b/tan(e + f*x))**(n + S(2))*(c + d*x)**m, x), x) + Dist(d*m/(b*f*(n + S(1))), Int((b/tan(e + f*x))**(n + S(1))*(c + d*x)**(m + S(-1)), x), x) - Simp((b/tan(e + f*x))**(n + S(1))*(c + d*x)**m/(b*f*(n + S(1))), x)
    rule3860 = ReplacementRule(pattern3860, replacement3860)
    pattern3861 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons528)
    def replacement3861(m, f, b, d, c, n, a, x, e):
        rubi.append(3861)
        return Int(ExpandIntegrand((c + d*x)**m, (a + b*tan(e + f*x))**n, x), x)
    rule3861 = ReplacementRule(pattern3861, replacement3861)
    pattern3862 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons528)
    def replacement3862(m, f, b, d, c, n, a, x, e):
        rubi.append(3862)
        return Int(ExpandIntegrand((c + d*x)**m, (a + b/tan(e + f*x))**n, x), x)
    rule3862 = ReplacementRule(pattern3862, replacement3862)
    pattern3863 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439, cons31, cons168)
    def replacement3863(m, f, b, d, c, a, x, e):
        rubi.append(3863)
        return Dist(a*d*m/(S(2)*b*f), Int((c + d*x)**(m + S(-1))/(a + b*tan(e + f*x)), x), x) + Simp((c + d*x)**(m + S(1))/(S(2)*a*d*(m + S(1))), x) - Simp(a*(c + d*x)**m/(S(2)*b*f*(a + b*tan(e + f*x))), x)
    rule3863 = ReplacementRule(pattern3863, replacement3863)
    pattern3864 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439, cons31, cons168)
    def replacement3864(m, f, b, d, c, a, x, e):
        rubi.append(3864)
        return -Dist(a*d*m/(S(2)*b*f), Int((c + d*x)**(m + S(-1))/(a + b/tan(e + f*x)), x), x) + Simp((c + d*x)**(m + S(1))/(S(2)*a*d*(m + S(1))), x) + Simp(a*(c + d*x)**m/(S(2)*b*f*(a + b/tan(e + f*x))), x)
    rule3864 = ReplacementRule(pattern3864, replacement3864)
    pattern3865 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(x_*WC('d', S(1)) + WC('c', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439)
    def replacement3865(f, b, d, c, a, x, e):
        rubi.append(3865)
        return -Dist(f/(a*d), Int(sin(S(2)*e + S(2)*f*x)/(c + d*x), x), x) + Dist(f/(b*d), Int(cos(S(2)*e + S(2)*f*x)/(c + d*x), x), x) - Simp(S(1)/(d*(a + b*tan(e + f*x))*(c + d*x)), x)
    rule3865 = ReplacementRule(pattern3865, replacement3865)
    pattern3866 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(x_*WC('d', S(1)) + WC('c', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439)
    def replacement3866(f, b, d, c, a, x, e):
        rubi.append(3866)
        return Dist(f/(a*d), Int(sin(S(2)*e + S(2)*f*x)/(c + d*x), x), x) + Dist(f/(b*d), Int(cos(S(2)*e + S(2)*f*x)/(c + d*x), x), x) - Simp(S(1)/(d*(a + b/tan(e + f*x))*(c + d*x)), x)
    rule3866 = ReplacementRule(pattern3866, replacement3866)
    pattern3867 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439, cons31, cons94, cons1510)
    def replacement3867(m, f, b, d, c, a, x, e):
        rubi.append(3867)
        return Dist(S(2)*b*f/(a*d*(m + S(1))), Int((c + d*x)**(m + S(1))/(a + b*tan(e + f*x)), x), x) + Simp((c + d*x)**(m + S(1))/(d*(a + b*tan(e + f*x))*(m + S(1))), x) + Simp(f*(c + d*x)**(m + S(2))/(b*d**S(2)*(m + S(1))*(m + S(2))), x)
    rule3867 = ReplacementRule(pattern3867, replacement3867)
    pattern3868 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439, cons31, cons94, cons1510)
    def replacement3868(m, f, b, d, c, a, x, e):
        rubi.append(3868)
        return -Dist(S(2)*b*f/(a*d*(m + S(1))), Int((c + d*x)**(m + S(1))/(a + b/tan(e + f*x)), x), x) + Simp((c + d*x)**(m + S(1))/(d*(a + b/tan(e + f*x))*(m + S(1))), x) - Simp(f*(c + d*x)**(m + S(2))/(b*d**S(2)*(m + S(1))*(m + S(2))), x)
    rule3868 = ReplacementRule(pattern3868, replacement3868)
    pattern3869 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439)
    def replacement3869(f, b, d, c, a, x, e):
        rubi.append(3869)
        return Dist(S(1)/(S(2)*a), Int(cos(S(2)*e + S(2)*f*x)/(c + d*x), x), x) + Dist(S(1)/(S(2)*b), Int(sin(S(2)*e + S(2)*f*x)/(c + d*x), x), x) + Simp(log(c + d*x)/(S(2)*a*d), x)
    rule3869 = ReplacementRule(pattern3869, replacement3869)
    pattern3870 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439)
    def replacement3870(f, b, d, c, a, x, e):
        rubi.append(3870)
        return -Dist(S(1)/(S(2)*a), Int(cos(S(2)*e + S(2)*f*x)/(c + d*x), x), x) + Dist(S(1)/(S(2)*b), Int(sin(S(2)*e + S(2)*f*x)/(c + d*x), x), x) + Simp(log(c + d*x)/(S(2)*a*d), x)
    rule3870 = ReplacementRule(pattern3870, replacement3870)
    pattern3871 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1439, cons18)
    def replacement3871(m, f, b, d, c, a, x, e):
        rubi.append(3871)
        return Dist(S(1)/(S(2)*a), Int((c + d*x)**m*exp(S(2)*a*(e + f*x)/b), x), x) + Simp((c + d*x)**(m + S(1))/(S(2)*a*d*(m + S(1))), x)
    rule3871 = ReplacementRule(pattern3871, replacement3871)
    pattern3872 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1439, cons18)
    def replacement3872(m, f, b, d, c, a, x, e):
        rubi.append(3872)
        return -Dist(S(1)/(S(2)*a), Int((c + d*x)**m*exp(-S(2)*a*(e + f*x)/b), x), x) + Simp((c + d*x)**(m + S(1))/(S(2)*a*d*(m + S(1))), x)
    rule3872 = ReplacementRule(pattern3872, replacement3872)
    pattern3873 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439, cons1571)
    def replacement3873(m, f, b, d, c, a, n, x, e):
        rubi.append(3873)
        return Int(ExpandIntegrand((c + d*x)**m, (sin(S(2)*e + S(2)*f*x)/(S(2)*b) + cos(S(2)*e + S(2)*f*x)/(S(2)*a) + S(1)/(S(2)*a))**(-n), x), x)
    rule3873 = ReplacementRule(pattern3873, replacement3873)
    pattern3874 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439, cons1571)
    def replacement3874(m, f, b, d, c, a, n, x, e):
        rubi.append(3874)
        return Int(ExpandIntegrand((c + d*x)**m, (sin(S(2)*e + S(2)*f*x)/(S(2)*b) - cos(S(2)*e + S(2)*f*x)/(S(2)*a) + S(1)/(S(2)*a))**(-n), x), x)
    rule3874 = ReplacementRule(pattern3874, replacement3874)
    pattern3875 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1439, cons196)
    def replacement3875(m, f, b, d, c, a, n, x, e):
        rubi.append(3875)
        return Int(ExpandIntegrand((c + d*x)**m, (exp(S(2)*a*(e + f*x)/b)/(S(2)*a) + S(1)/(S(2)*a))**(-n), x), x)
    rule3875 = ReplacementRule(pattern3875, replacement3875)
    pattern3876 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1439, cons196)
    def replacement3876(m, f, b, d, c, a, n, x, e):
        rubi.append(3876)
        return Int(ExpandIntegrand((c + d*x)**m, (S(1)/(S(2)*a) - exp(-S(2)*a*(e + f*x)/b)/(S(2)*a))**(-n), x), x)
    rule3876 = ReplacementRule(pattern3876, replacement3876)
    def With3877(m, f, b, d, c, a, n, x, e):
        u = IntHide((a + b*tan(e + f*x))**n, x)
        rubi.append(3877)
        return -Dist(d*m, Int(Dist((c + d*x)**(m + S(-1)), u, x), x), x) + Dist((c + d*x)**m, u, x)
    pattern3877 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439, cons1572, cons31, cons168)
    rule3877 = ReplacementRule(pattern3877, With3877)
    def With3878(m, f, b, d, c, a, n, x, e):
        u = IntHide((a + b/tan(e + f*x))**n, x)
        rubi.append(3878)
        return -Dist(d*m, Int(Dist((c + d*x)**(m + S(-1)), u, x), x), x) + Dist((c + d*x)**m, u, x)
    pattern3878 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1439, cons1572, cons31, cons168)
    rule3878 = ReplacementRule(pattern3878, With3878)
    pattern3879 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1440, cons62)
    def replacement3879(m, f, b, d, c, a, x, e):
        rubi.append(3879)
        return -Dist(S(2)*I*b, Int((c + d*x)**m/(a**S(2) + b**S(2) + (a - I*b)**S(2)*exp(S(2)*I*(e + f*x))), x), x) + Simp((c + d*x)**(m + S(1))/(d*(a - I*b)*(m + S(1))), x)
    rule3879 = ReplacementRule(pattern3879, replacement3879)
    pattern3880 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1440, cons62)
    def replacement3880(m, f, b, d, c, a, x, e):
        rubi.append(3880)
        return Dist(S(2)*I*b, Int((c + d*x)**m/(a**S(2) + b**S(2) - (a + I*b)**S(2)*exp(S(2)*I*(e + f*x))), x), x) + Simp((c + d*x)**(m + S(1))/(d*(a + I*b)*(m + S(1))), x)
    rule3880 = ReplacementRule(pattern3880, replacement3880)
    pattern3881 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))/(a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1440)
    def replacement3881(f, b, d, c, a, x, e):
        rubi.append(3881)
        return Dist(S(1)/(f*(a**S(2) + b**S(2))), Int((S(2)*a*c*f + S(2)*a*d*f*x + b*d)/(a + b*tan(e + f*x)), x), x) - Simp((c + d*x)**S(2)/(S(2)*d*(a**S(2) + b**S(2))), x) - Simp(b*(c + d*x)/(f*(a + b*tan(e + f*x))*(a**S(2) + b**S(2))), x)
    rule3881 = ReplacementRule(pattern3881, replacement3881)
    pattern3882 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))/(a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1440)
    def replacement3882(f, b, d, c, a, x, e):
        rubi.append(3882)
        return -Dist(S(1)/(f*(a**S(2) + b**S(2))), Int((-S(2)*a*c*f - S(2)*a*d*f*x + b*d)/(a + b/tan(e + f*x)), x), x) - Simp((c + d*x)**S(2)/(S(2)*d*(a**S(2) + b**S(2))), x) + Simp(b*(c + d*x)/(f*(a + b/tan(e + f*x))*(a**S(2) + b**S(2))), x)
    rule3882 = ReplacementRule(pattern3882, replacement3882)
    pattern3883 = Pattern(Integral((a_ + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1440, cons196, cons62)
    def replacement3883(m, f, b, d, c, a, n, x, e):
        rubi.append(3883)
        return Int(ExpandIntegrand((c + d*x)**m, (-S(2)*I*b/(a**S(2) + b**S(2) + (a - I*b)**S(2)*exp(S(2)*I*(e + f*x))) + S(1)/(a - I*b))**(-n), x), x)
    rule3883 = ReplacementRule(pattern3883, replacement3883)
    pattern3884 = Pattern(Integral((a_ + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1440, cons196, cons62)
    def replacement3884(m, f, b, d, c, a, n, x, e):
        rubi.append(3884)
        return Int(ExpandIntegrand((c + d*x)**m, (S(2)*I*b/(a**S(2) + b**S(2) - (a + I*b)**S(2)*exp(S(2)*I*(e + f*x))) + S(1)/(a + I*b))**(-n), x), x)
    rule3884 = ReplacementRule(pattern3884, replacement3884)
    pattern3885 = Pattern(Integral(u_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*tan(v_))**WC('n', S(1)), x_), cons2, cons3, cons21, cons4, cons810, cons811)
    def replacement3885(v, u, m, b, a, n, x):
        rubi.append(3885)
        return Int((a + b*tan(ExpandToSum(v, x)))**n*ExpandToSum(u, x)**m, x)
    rule3885 = ReplacementRule(pattern3885, replacement3885)
    pattern3886 = Pattern(Integral(u_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/tan(v_))**WC('n', S(1)), x_), cons2, cons3, cons21, cons4, cons810, cons811)
    def replacement3886(v, u, m, b, a, n, x):
        rubi.append(3886)
        return Int((a + b/tan(ExpandToSum(v, x)))**n*ExpandToSum(u, x)**m, x)
    rule3886 = ReplacementRule(pattern3886, replacement3886)
    pattern3887 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement3887(m, f, b, d, c, a, n, x, e):
        rubi.append(3887)
        return Int((a + b*tan(e + f*x))**n*(c + d*x)**m, x)
    rule3887 = ReplacementRule(pattern3887, replacement3887)
    pattern3888 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement3888(m, f, b, d, a, n, c, x, e):
        rubi.append(3888)
        return Int((a + b/tan(e + f*x))**n*(c + d*x)**m, x)
    rule3888 = ReplacementRule(pattern3888, replacement3888)
    pattern3889 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons5, cons1573, cons38)
    def replacement3889(p, b, d, c, a, n, x):
        rubi.append(3889)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + S(1)/n)*(a + b*tan(c + d*x))**p, x), x, x**n), x)
    rule3889 = ReplacementRule(pattern3889, replacement3889)
    pattern3890 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons5, cons1573, cons38)
    def replacement3890(p, b, d, a, c, n, x):
        rubi.append(3890)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + S(1)/n)*(a + b/tan(c + d*x))**p, x), x, x**n), x)
    rule3890 = ReplacementRule(pattern3890, replacement3890)
    pattern3891 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons1495)
    def replacement3891(p, b, d, c, a, n, x):
        rubi.append(3891)
        return Int((a + b*tan(c + d*x**n))**p, x)
    rule3891 = ReplacementRule(pattern3891, replacement3891)
    pattern3892 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons1495)
    def replacement3892(p, b, d, a, c, n, x):
        rubi.append(3892)
        return Int((a + b/tan(c + d*x**n))**p, x)
    rule3892 = ReplacementRule(pattern3892, replacement3892)
    pattern3893 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons68, cons69)
    def replacement3893(p, u, b, d, c, a, n, x):
        rubi.append(3893)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b*tan(c + d*x**n))**p, x), x, u), x)
    rule3893 = ReplacementRule(pattern3893, replacement3893)
    pattern3894 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons68, cons69)
    def replacement3894(p, u, b, d, a, c, n, x):
        rubi.append(3894)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b/tan(c + d*x**n))**p, x), x, u), x)
    rule3894 = ReplacementRule(pattern3894, replacement3894)
    pattern3895 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*tan(u_))**WC('p', S(1)), x_), cons2, cons3, cons5, cons823, cons824)
    def replacement3895(p, u, b, a, x):
        rubi.append(3895)
        return Int((a + b*tan(ExpandToSum(u, x)))**p, x)
    rule3895 = ReplacementRule(pattern3895, replacement3895)
    pattern3896 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/tan(u_))**WC('p', S(1)), x_), cons2, cons3, cons5, cons823, cons824)
    def replacement3896(p, u, b, a, x):
        rubi.append(3896)
        return Int((a + b/tan(ExpandToSum(u, x)))**p, x)
    rule3896 = ReplacementRule(pattern3896, replacement3896)
    pattern3897 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons1574, cons38)
    def replacement3897(p, m, b, d, c, a, n, x):
        rubi.append(3897)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + (m + S(1))/n)*(a + b*tan(c + d*x))**p, x), x, x**n), x)
    rule3897 = ReplacementRule(pattern3897, replacement3897)
    pattern3898 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons1574, cons38)
    def replacement3898(p, m, b, d, a, c, n, x):
        rubi.append(3898)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + (m + S(1))/n)*(a + b/tan(c + d*x))**p, x), x, x**n), x)
    rule3898 = ReplacementRule(pattern3898, replacement3898)
    pattern3899 = Pattern(Integral(x_**WC('m', S(1))*tan(x_**n_*WC('d', S(1)) + WC('c', S(0)))**S(2), x_), cons7, cons27, cons21, cons4, cons1575)
    def replacement3899(m, d, c, n, x):
        rubi.append(3899)
        return -Dist((m - n + S(1))/(d*n), Int(x**(m - n)*tan(c + d*x**n), x), x) - Int(x**m, x) + Simp(x**(m - n + S(1))*tan(c + d*x**n)/(d*n), x)
    rule3899 = ReplacementRule(pattern3899, replacement3899)
    pattern3900 = Pattern(Integral(x_**WC('m', S(1))/tan(x_**n_*WC('d', S(1)) + WC('c', S(0)))**S(2), x_), cons7, cons27, cons21, cons4, cons1575)
    def replacement3900(m, d, c, n, x):
        rubi.append(3900)
        return Dist((m - n + S(1))/(d*n), Int(x**(m - n)/tan(c + d*x**n), x), x) - Int(x**m, x) - Simp(x**(m - n + S(1))/(d*n*tan(c + d*x**n)), x)
    rule3900 = ReplacementRule(pattern3900, replacement3900)
    pattern3901 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons1576)
    def replacement3901(p, m, b, d, c, a, n, x):
        rubi.append(3901)
        return Int(x**m*(a + b*tan(c + d*x**n))**p, x)
    rule3901 = ReplacementRule(pattern3901, replacement3901)
    pattern3902 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons1576)
    def replacement3902(p, m, b, d, a, c, n, x):
        rubi.append(3902)
        return Int(x**m*(a + b/tan(c + d*x**n))**p, x)
    rule3902 = ReplacementRule(pattern3902, replacement3902)
    pattern3903 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement3903(p, m, b, d, c, a, n, x, e):
        rubi.append(3903)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*tan(c + d*x**n))**p, x), x)
    rule3903 = ReplacementRule(pattern3903, replacement3903)
    pattern3904 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/tan(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement3904(p, m, b, d, a, c, n, x, e):
        rubi.append(3904)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b/tan(c + d*x**n))**p, x), x)
    rule3904 = ReplacementRule(pattern3904, replacement3904)
    pattern3905 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*tan(u_))**WC('p', S(1)), x_), cons2, cons3, cons48, cons21, cons5, cons823, cons824)
    def replacement3905(p, u, m, b, a, x, e):
        rubi.append(3905)
        return Int((e*x)**m*(a + b*tan(ExpandToSum(u, x)))**p, x)
    rule3905 = ReplacementRule(pattern3905, replacement3905)
    pattern3906 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/tan(u_))**WC('p', S(1)), x_), cons2, cons3, cons48, cons21, cons5, cons823, cons824)
    def replacement3906(p, u, m, b, a, x, e):
        rubi.append(3906)
        return Int((e*x)**m*(a + b/tan(ExpandToSum(u, x)))**p, x)
    rule3906 = ReplacementRule(pattern3906, replacement3906)
    pattern3907 = Pattern(Integral(x_**WC('m', S(1))*(S(1)/cos(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('p', S(1))*tan(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons5, cons31, cons85, cons1577, cons1578)
    def replacement3907(p, m, b, a, n, x, q):
        rubi.append(3907)
        return -Dist((m - n + S(1))/(b*n*p), Int(x**(m - n)*(S(1)/cos(a + b*x**n))**p, x), x) + Simp(x**(m - n + S(1))*(S(1)/cos(a + b*x**n))**p/(b*n*p), x)
    rule3907 = ReplacementRule(pattern3907, replacement3907)
    pattern3908 = Pattern(Integral(x_**WC('m', S(1))*(S(1)/sin(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('p', S(1))*(S(1)/tan(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('q', S(1)), x_), cons2, cons3, cons5, cons31, cons85, cons1577, cons1578)
    def replacement3908(p, m, b, a, n, x, q):
        rubi.append(3908)
        return Dist((m - n + S(1))/(b*n*p), Int(x**(m - n)*(S(1)/sin(a + b*x**n))**p, x), x) - Simp(x**(m - n + S(1))*(S(1)/sin(a + b*x**n))**p/(b*n*p), x)
    rule3908 = ReplacementRule(pattern3908, replacement3908)
    pattern3909 = Pattern(Integral(tan(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement3909(b, c, a, n, x):
        rubi.append(3909)
        return Int(tan(a + b*x + c*x**S(2))**n, x)
    rule3909 = ReplacementRule(pattern3909, replacement3909)
    pattern3910 = Pattern(Integral((S(1)/tan(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement3910(b, c, a, n, x):
        rubi.append(3910)
        return Int((S(1)/tan(a + b*x + c*x**S(2)))**n, x)
    rule3910 = ReplacementRule(pattern3910, replacement3910)
    pattern3911 = Pattern(Integral((d_ + x_*WC('e', S(1)))*tan(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons47)
    def replacement3911(b, d, c, a, x, e):
        rubi.append(3911)
        return -Simp(e*log(cos(a + b*x + c*x**S(2)))/(S(2)*c), x)
    rule3911 = ReplacementRule(pattern3911, replacement3911)
    pattern3912 = Pattern(Integral((d_ + x_*WC('e', S(1)))/tan(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons47)
    def replacement3912(b, d, c, a, x, e):
        rubi.append(3912)
        return Simp(e*log(sin(a + b*x + c*x**S(2)))/(S(2)*c), x)
    rule3912 = ReplacementRule(pattern3912, replacement3912)
    pattern3913 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))*tan(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons239)
    def replacement3913(b, d, c, a, x, e):
        rubi.append(3913)
        return Dist((-b*e + S(2)*c*d)/(S(2)*c), Int(tan(a + b*x + c*x**S(2)), x), x) - Simp(e*log(cos(a + b*x + c*x**S(2)))/(S(2)*c), x)
    rule3913 = ReplacementRule(pattern3913, replacement3913)
    pattern3914 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))/tan(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons239)
    def replacement3914(b, d, c, a, x, e):
        rubi.append(3914)
        return Dist((-b*e + S(2)*c*d)/(S(2)*c), Int(S(1)/tan(a + b*x + c*x**S(2)), x), x) + Simp(e*log(sin(a + b*x + c*x**S(2)))/(S(2)*c), x)
    rule3914 = ReplacementRule(pattern3914, replacement3914)
    pattern3915 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*tan(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1580)
    def replacement3915(m, b, d, a, c, n, x, e):
        rubi.append(3915)
        return Int((d + e*x)**m*tan(a + b*x + c*x**S(2))**n, x)
    rule3915 = ReplacementRule(pattern3915, replacement3915)
    pattern3916 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(S(1)/tan(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1580)
    def replacement3916(m, b, d, c, a, n, x, e):
        rubi.append(3916)
        return Int((d + e*x)**m*(S(1)/tan(a + b*x + c*x**S(2)))**n, x)
    rule3916 = ReplacementRule(pattern3916, replacement3916)
    return [rule3398, rule3399, rule3400, rule3401, rule3402, rule3403, rule3404, rule3405, rule3406, rule3407, rule3408, rule3409, rule3410, rule3411, rule3412, rule3413, rule3414, rule3415, rule3416, rule3417, rule3418, rule3419, rule3420, rule3421, rule3422, rule3423, rule3424, rule3425, rule3426, rule3427, rule3428, rule3429, rule3430, rule3431, rule3432, rule3433, rule3434, rule3435, rule3436, rule3437, rule3438, rule3439, rule3440, rule3441, rule3442, rule3443, rule3444, rule3445, rule3446, rule3447, rule3448, rule3449, rule3450, rule3451, rule3452, rule3453, rule3454, rule3455, rule3456, rule3457, rule3458, rule3459, rule3460, rule3461, rule3462, rule3463, rule3464, rule3465, rule3466, rule3467, rule3468, rule3469, rule3470, rule3471, rule3472, rule3473, rule3474, rule3475, rule3476, rule3477, rule3478, rule3479, rule3480, rule3481, rule3482, rule3483, rule3484, rule3485, rule3486, rule3487, rule3488, rule3489, rule3490, rule3491, rule3492, rule3493, rule3494, rule3495, rule3496, rule3497, rule3498, rule3499, rule3500, rule3501, rule3502, rule3503, rule3504, rule3505, rule3506, rule3507, rule3508, rule3509, rule3510, rule3511, rule3512, rule3513, rule3514, rule3515, rule3516, rule3517, rule3518, rule3519, rule3520, rule3521, rule3522, rule3523, rule3524, rule3525, rule3526, rule3527, rule3528, rule3529, rule3530, rule3531, rule3532, rule3533, rule3534, rule3535, rule3536, rule3537, rule3538, rule3539, rule3540, rule3541, rule3542, rule3543, rule3544, rule3545, rule3546, rule3547, rule3548, rule3549, rule3550, rule3551, rule3552, rule3553, rule3554, rule3555, rule3556, rule3557, rule3558, rule3559, rule3560, rule3561, rule3562, rule3563, rule3564, rule3565, rule3566, rule3567, rule3568, rule3569, rule3570, rule3571, rule3572, rule3573, rule3574, rule3575, rule3576, rule3577, rule3578, rule3579, rule3580, rule3581, rule3582, rule3583, rule3584, rule3585, rule3586, rule3587, rule3588, rule3589, rule3590, rule3591, rule3592, rule3593, rule3594, rule3595, rule3596, rule3597, rule3598, rule3599, rule3600, rule3601, rule3602, rule3603, rule3604, rule3605, rule3606, rule3607, rule3608, rule3609, rule3610, rule3611, rule3612, rule3613, rule3614, rule3615, rule3616, rule3617, rule3618, rule3619, rule3620, rule3621, rule3622, rule3623, rule3624, rule3625, rule3626, rule3627, rule3628, rule3629, rule3630, rule3631, rule3632, rule3633, rule3634, rule3635, rule3636, rule3637, rule3638, rule3639, rule3640, rule3641, rule3642, rule3643, rule3644, rule3645, rule3646, rule3647, rule3648, rule3649, rule3650, rule3651, rule3652, rule3653, rule3654, rule3655, rule3656, rule3657, rule3658, rule3659, rule3660, rule3661, rule3662, rule3663, rule3664, rule3665, rule3666, rule3667, rule3668, rule3669, rule3670, rule3671, rule3672, rule3673, rule3674, rule3675, rule3676, rule3677, rule3678, rule3679, rule3680, rule3681, rule3682, rule3683, rule3684, rule3685, rule3686, rule3687, rule3688, rule3689, rule3690, rule3691, rule3692, rule3693, rule3694, rule3695, rule3696, rule3697, rule3698, rule3699, rule3700, rule3701, rule3702, rule3703, rule3704, rule3705, rule3706, rule3707, rule3708, rule3709, rule3710, rule3711, rule3712, rule3713, rule3714, rule3715, rule3716, rule3717, rule3718, rule3719, rule3720, rule3721, rule3722, rule3723, rule3724, rule3725, rule3726, rule3727, rule3728, rule3729, rule3730, rule3731, rule3732, rule3733, rule3734, rule3735, rule3736, rule3737, rule3738, rule3739, rule3740, rule3741, rule3742, rule3743, rule3744, rule3745, rule3746, rule3747, rule3748, rule3749, rule3750, rule3751, rule3752, rule3753, rule3754, rule3755, rule3756, rule3757, rule3758, rule3759, rule3760, rule3761, rule3762, rule3763, rule3764, rule3765, rule3766, rule3767, rule3768, rule3769, rule3770, rule3771, rule3772, rule3773, rule3774, rule3775, rule3776, rule3777, rule3778, rule3779, rule3780, rule3781, rule3782, rule3783, rule3784, rule3785, rule3786, rule3787, rule3788, rule3789, rule3790, rule3791, rule3792, rule3793, rule3794, rule3795, rule3796, rule3797, rule3798, rule3799, rule3800, rule3801, rule3802, rule3803, rule3804, rule3805, rule3806, rule3807, rule3808, rule3809, rule3810, rule3811, rule3812, rule3813, rule3814, rule3815, rule3816, rule3817, rule3818, rule3819, rule3820, rule3821, rule3822, rule3823, rule3824, rule3825, rule3826, rule3827, rule3828, rule3829, rule3830, rule3831, rule3832, rule3833, rule3834, rule3835, rule3836, rule3837, rule3838, rule3839, rule3840, rule3841, rule3842, rule3843, rule3844, rule3845, rule3846, rule3847, rule3848, rule3849, rule3850, rule3851, rule3852, rule3853, rule3854, rule3855, rule3856, rule3857, rule3858, rule3859, rule3860, rule3861, rule3862, rule3863, rule3864, rule3865, rule3866, rule3867, rule3868, rule3869, rule3870, rule3871, rule3872, rule3873, rule3874, rule3875, rule3876, rule3877, rule3878, rule3879, rule3880, rule3881, rule3882, rule3883, rule3884, rule3885, rule3886, rule3887, rule3888, rule3889, rule3890, rule3891, rule3892, rule3893, rule3894, rule3895, rule3896, rule3897, rule3898, rule3899, rule3900, rule3901, rule3902, rule3903, rule3904, rule3905, rule3906, rule3907, rule3908, rule3909, rule3910, rule3911, rule3912, rule3913, rule3914, rule3915, rule3916, ]
