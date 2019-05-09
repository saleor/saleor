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

def secant(rubi):
    from sympy.integrals.rubi.constraints import cons1581, cons1502, cons2, cons3, cons48, cons125, cons21, cons4, cons1582, cons1512, cons1583, cons18, cons93, cons166, cons89, cons1170, cons94, cons165, cons31, cons1584, cons87, cons1359, cons23, cons1255, cons1258, cons674, cons7, cons27, cons808, cons1261, cons1585, cons1264, cons1265, cons1586, cons543, cons43, cons448, cons1267, cons744, cons1587, cons1254, cons62, cons1423, cons515, cons1320, cons1321, cons1588, cons1589, cons1590, cons1330, cons111, cons155, cons1591, cons1519, cons1336, cons1592, cons463, cons85, cons1593, cons77, cons168, cons272, cons1333, cons1594, cons1334, cons1595, cons1325, cons1596, cons1597, cons1598, cons1599, cons1553, cons1600, cons1357, cons1601, cons1602, cons1603, cons1604, cons17, cons208, cons5, cons1274, cons1605, cons1606, cons1308, cons147, cons1228, cons1507, cons148, cons1515, cons1607, cons196, cons1311, cons1608, cons1609, cons1580, cons70, cons1610, cons1611, cons79, cons1612, cons1613, cons1304, cons71, cons1412, cons1409, cons1323, cons1322, cons1614, cons80, cons1360, cons1421, cons1315, cons1231, cons1615, cons1314, cons1266, cons1616, cons150, cons1617, cons1618, cons1619, cons1620, cons1621, cons38, cons1622, cons1415, cons380, cons1428, cons34, cons35, cons1245, cons1569, cons1623, cons1624, cons1625, cons1626, cons1627, cons32, cons1549, cons1628, cons1629, cons346, cons88, cons1327, cons1630, cons1631, cons1256, cons1632, cons375, cons33, cons36, cons1433, cons1633, cons1634, cons1431, cons1635, cons1636, cons1637, cons1638, cons1639, cons1640, cons683, cons1641, cons1642, cons1643, cons1454, cons1478, cons54, cons1480, cons1479, cons1481, cons376, cons46, cons45, cons226, cons1644, cons528, cons810, cons811, cons1573, cons1495, cons68, cons69, cons823, cons824, cons1574, cons1576, cons1497, cons1577, cons1645

    pattern3917 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1581, cons1502)
    def replacement3917(m, f, b, a, n, x, e):
        rubi.append(3917)
        return Simp(a*b*(a/sin(e + f*x))**(m + S(-1))*(b/cos(e + f*x))**(n + S(-1))/(f*(n + S(-1))), x)
    rule3917 = ReplacementRule(pattern3917, replacement3917)
    pattern3918 = Pattern(Integral((S(1)/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(S(1)/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons48, cons125, cons1582)
    def replacement3918(m, f, n, x, e):
        rubi.append(3918)
        return Dist(S(1)/f, Subst(Int(x**(-m)*(x**S(2) + S(1))**(m/S(2) + n/S(2) + S(-1)), x), x, tan(e + f*x)), x)
    rule3918 = ReplacementRule(pattern3918, replacement3918)
    pattern3919 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(S(1)/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons48, cons125, cons21, cons1512, cons1583, cons18)
    def replacement3919(m, f, a, n, x, e):
        rubi.append(3919)
        return -Dist(a**(-n + S(1))/f, Subst(Int((a*x)**(m + n + S(-1))*(x**S(2) + S(-1))**(-n/S(2) + S(-1)/2), x), x, S(1)/sin(e + f*x)), x)
    rule3919 = ReplacementRule(pattern3919, replacement3919)
    pattern3920 = Pattern(Integral((WC('a', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(S(1)/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons48, cons125, cons21, cons1512, cons1583, cons18)
    def replacement3920(m, f, a, n, x, e):
        rubi.append(3920)
        return Dist(a**(-n + S(1))/f, Subst(Int((a*x)**(m + n + S(-1))*(x**S(2) + S(-1))**(-n/S(2) + S(-1)/2), x), x, S(1)/cos(e + f*x)), x)
    rule3920 = ReplacementRule(pattern3920, replacement3920)
    pattern3921 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons166, cons89, cons1170)
    def replacement3921(m, f, b, a, n, x, e):
        rubi.append(3921)
        return Dist(a**S(2)*(n + S(1))/(b**S(2)*(m + S(-1))), Int((a/sin(e + f*x))**(m + S(-2))*(b/cos(e + f*x))**(n + S(2)), x), x) - Simp(a*(a/sin(e + f*x))**(m + S(-1))*(b/cos(e + f*x))**(n + S(1))/(b*f*(m + S(-1))), x)
    rule3921 = ReplacementRule(pattern3921, replacement3921)
    pattern3922 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons94, cons165, cons1170)
    def replacement3922(m, f, b, a, n, x, e):
        rubi.append(3922)
        return Dist(b**S(2)*(m + S(1))/(a**S(2)*(n + S(-1))), Int((a/sin(e + f*x))**(m + S(2))*(b/cos(e + f*x))**(n + S(-2)), x), x) + Simp(b*(a/sin(e + f*x))**(m + S(1))*(b/cos(e + f*x))**(n + S(-1))/(a*f*(n + S(-1))), x)
    rule3922 = ReplacementRule(pattern3922, replacement3922)
    pattern3923 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons4, cons31, cons166, cons1170, cons1584)
    def replacement3923(m, f, b, a, n, x, e):
        rubi.append(3923)
        return Dist(a**S(2)*(m + n + S(-2))/(m + S(-1)), Int((a/sin(e + f*x))**(m + S(-2))*(b/cos(e + f*x))**n, x), x) - Simp(a*b*(a/sin(e + f*x))**(m + S(-1))*(b/cos(e + f*x))**(n + S(-1))/(f*(m + S(-1))), x)
    rule3923 = ReplacementRule(pattern3923, replacement3923)
    pattern3924 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons165, cons1170)
    def replacement3924(m, f, b, a, n, x, e):
        rubi.append(3924)
        return Dist(b**S(2)*(m + n + S(-2))/(n + S(-1)), Int((a/sin(e + f*x))**m*(b/cos(e + f*x))**(n + S(-2)), x), x) + Simp(a*b*(a/sin(e + f*x))**(m + S(-1))*(b/cos(e + f*x))**(n + S(-1))/(f*(n + S(-1))), x)
    rule3924 = ReplacementRule(pattern3924, replacement3924)
    pattern3925 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons4, cons31, cons94, cons1359, cons1170)
    def replacement3925(m, f, b, a, n, x, e):
        rubi.append(3925)
        return Dist((m + S(1))/(a**S(2)*(m + n)), Int((a/sin(e + f*x))**(m + S(2))*(b/cos(e + f*x))**n, x), x) + Simp(b*(a/sin(e + f*x))**(m + S(1))*(b/cos(e + f*x))**(n + S(-1))/(a*f*(m + n)), x)
    rule3925 = ReplacementRule(pattern3925, replacement3925)
    pattern3926 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons87, cons89, cons1359, cons1170)
    def replacement3926(m, f, b, a, n, x, e):
        rubi.append(3926)
        return Dist((n + S(1))/(b**S(2)*(m + n)), Int((a/sin(e + f*x))**m*(b/cos(e + f*x))**(n + S(2)), x), x) - Simp(a*(a/sin(e + f*x))**(m + S(-1))*(b/cos(e + f*x))**(n + S(1))/(b*f*(m + n)), x)
    rule3926 = ReplacementRule(pattern3926, replacement3926)
    pattern3927 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons23, cons1255)
    def replacement3927(m, f, b, a, n, x, e):
        rubi.append(3927)
        return Dist((a/sin(e + f*x))**m*(b/cos(e + f*x))**n*tan(e + f*x)**(-n), Int(tan(e + f*x)**n, x), x)
    rule3927 = ReplacementRule(pattern3927, replacement3927)
    pattern3928 = Pattern(Integral((WC('a', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1258)
    def replacement3928(m, f, b, a, n, x, e):
        rubi.append(3928)
        return Dist((a/sin(e + f*x))**m*(a*sin(e + f*x))**m*(b/cos(e + f*x))**n*(b*cos(e + f*x))**n, Int((a*sin(e + f*x))**(-m)*(b*cos(e + f*x))**(-n), x), x)
    rule3928 = ReplacementRule(pattern3928, replacement3928)
    pattern3929 = Pattern(Integral((S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons7, cons27, cons674)
    def replacement3929(d, c, n, x):
        rubi.append(3929)
        return Dist(S(1)/d, Subst(Int(ExpandIntegrand((x**S(2) + S(1))**(n/S(2) + S(-1)), x), x), x, tan(c + d*x)), x)
    rule3929 = ReplacementRule(pattern3929, replacement3929)
    pattern3930 = Pattern(Integral((S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons7, cons27, cons674)
    def replacement3930(d, c, n, x):
        rubi.append(3930)
        return -Dist(S(1)/d, Subst(Int(ExpandIntegrand((x**S(2) + S(1))**(n/S(2) + S(-1)), x), x), x, S(1)/tan(c + d*x)), x)
    rule3930 = ReplacementRule(pattern3930, replacement3930)
    pattern3931 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons165, cons808)
    def replacement3931(b, d, c, n, x):
        rubi.append(3931)
        return Dist(b**S(2)*(n + S(-2))/(n + S(-1)), Int((b/cos(c + d*x))**(n + S(-2)), x), x) + Simp(b*(b/cos(c + d*x))**(n + S(-1))*sin(c + d*x)/(d*(n + S(-1))), x)
    rule3931 = ReplacementRule(pattern3931, replacement3931)
    pattern3932 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons165, cons808)
    def replacement3932(b, d, c, n, x):
        rubi.append(3932)
        return Dist(b**S(2)*(n + S(-2))/(n + S(-1)), Int((b/sin(c + d*x))**(n + S(-2)), x), x) - Simp(b*(b/sin(c + d*x))**(n + S(-1))*cos(c + d*x)/(d*(n + S(-1))), x)
    rule3932 = ReplacementRule(pattern3932, replacement3932)
    pattern3933 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons89, cons808)
    def replacement3933(b, d, c, n, x):
        rubi.append(3933)
        return Dist((n + S(1))/(b**S(2)*n), Int((b/cos(c + d*x))**(n + S(2)), x), x) - Simp((b/cos(c + d*x))**(n + S(1))*sin(c + d*x)/(b*d*n), x)
    rule3933 = ReplacementRule(pattern3933, replacement3933)
    pattern3934 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons89, cons808)
    def replacement3934(b, d, c, n, x):
        rubi.append(3934)
        return Dist((n + S(1))/(b**S(2)*n), Int((b/sin(c + d*x))**(n + S(2)), x), x) + Simp((b/sin(c + d*x))**(n + S(1))*cos(c + d*x)/(b*d*n), x)
    rule3934 = ReplacementRule(pattern3934, replacement3934)
    pattern3935 = Pattern(Integral(S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons1261)
    def replacement3935(d, c, x):
        rubi.append(3935)
        return Simp(atanh(sin(c + d*x))/d, x)
    rule3935 = ReplacementRule(pattern3935, replacement3935)
    pattern3936 = Pattern(Integral(S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons1261)
    def replacement3936(d, c, x):
        rubi.append(3936)
        return -Simp(atanh(cos(c + d*x))/d, x)
    rule3936 = ReplacementRule(pattern3936, replacement3936)
    pattern3937 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons1585)
    def replacement3937(b, d, c, n, x):
        rubi.append(3937)
        return Dist((b/cos(c + d*x))**n*cos(c + d*x)**n, Int(cos(c + d*x)**(-n), x), x)
    rule3937 = ReplacementRule(pattern3937, replacement3937)
    pattern3938 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons1585)
    def replacement3938(b, d, c, n, x):
        rubi.append(3938)
        return Dist((b/sin(c + d*x))**n*sin(c + d*x)**n, Int(sin(c + d*x)**(-n), x), x)
    rule3938 = ReplacementRule(pattern3938, replacement3938)
    pattern3939 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons4, cons23)
    def replacement3939(b, d, c, n, x):
        rubi.append(3939)
        return Simp((cos(c + d*x)/b)**(n + S(-1))*(b/cos(c + d*x))**(n + S(-1))*Int((cos(c + d*x)/b)**(-n), x), x)
    rule3939 = ReplacementRule(pattern3939, replacement3939)
    pattern3940 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons4, cons23)
    def replacement3940(b, d, c, n, x):
        rubi.append(3940)
        return Simp((sin(c + d*x)/b)**(n + S(-1))*(b/sin(c + d*x))**(n + S(-1))*Int((sin(c + d*x)/b)**(-n), x), x)
    rule3940 = ReplacementRule(pattern3940, replacement3940)
    pattern3941 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons1264)
    def replacement3941(b, d, c, a, x):
        rubi.append(3941)
        return Dist(b**S(2), Int(cos(c + d*x)**(S(-2)), x), x) + Dist(S(2)*a*b, Int(S(1)/cos(c + d*x), x), x) + Simp(a**S(2)*x, x)
    rule3941 = ReplacementRule(pattern3941, replacement3941)
    pattern3942 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons1264)
    def replacement3942(b, d, c, a, x):
        rubi.append(3942)
        return Dist(b**S(2), Int(sin(c + d*x)**(S(-2)), x), x) + Dist(S(2)*a*b, Int(S(1)/sin(c + d*x), x), x) + Simp(a**S(2)*x, x)
    rule3942 = ReplacementRule(pattern3942, replacement3942)
    pattern3943 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement3943(b, d, c, a, x):
        rubi.append(3943)
        return Dist(S(2)*b/d, Subst(Int(S(1)/(a + x**S(2)), x), x, b*tan(c + d*x)/sqrt(a + b/cos(c + d*x))), x)
    rule3943 = ReplacementRule(pattern3943, replacement3943)
    pattern3944 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement3944(b, d, c, a, x):
        rubi.append(3944)
        return Dist(-S(2)*b/d, Subst(Int(S(1)/(a + x**S(2)), x), x, b/(sqrt(a + b/sin(c + d*x))*tan(c + d*x))), x)
    rule3944 = ReplacementRule(pattern3944, replacement3944)
    pattern3945 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1265, cons87, cons165, cons808)
    def replacement3945(b, d, c, a, n, x):
        rubi.append(3945)
        return Dist(a/(n + S(-1)), Int((a + b/cos(c + d*x))**(n + S(-2))*(a*(n + S(-1)) + b*(S(3)*n + S(-4))/cos(c + d*x)), x), x) + Simp(b**S(2)*(a + b/cos(c + d*x))**(n + S(-2))*tan(c + d*x)/(d*(n + S(-1))), x)
    rule3945 = ReplacementRule(pattern3945, replacement3945)
    pattern3946 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1265, cons87, cons165, cons808)
    def replacement3946(b, d, c, a, n, x):
        rubi.append(3946)
        return Dist(a/(n + S(-1)), Int((a + b/sin(c + d*x))**(n + S(-2))*(a*(n + S(-1)) + b*(S(3)*n + S(-4))/sin(c + d*x)), x), x) - Simp(b**S(2)*(a + b/sin(c + d*x))**(n + S(-2))/(d*(n + S(-1))*tan(c + d*x)), x)
    rule3946 = ReplacementRule(pattern3946, replacement3946)
    pattern3947 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement3947(b, d, c, a, x):
        rubi.append(3947)
        return Dist(S(1)/a, Int(sqrt(a + b/cos(c + d*x)), x), x) - Dist(b/a, Int(S(1)/(sqrt(a + b/cos(c + d*x))*cos(c + d*x)), x), x)
    rule3947 = ReplacementRule(pattern3947, replacement3947)
    pattern3948 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement3948(b, d, c, a, x):
        rubi.append(3948)
        return Dist(S(1)/a, Int(sqrt(a + b/sin(c + d*x)), x), x) - Dist(b/a, Int(S(1)/(sqrt(a + b/sin(c + d*x))*sin(c + d*x)), x), x)
    rule3948 = ReplacementRule(pattern3948, replacement3948)
    pattern3949 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1265, cons87, cons1586, cons808)
    def replacement3949(b, d, c, a, n, x):
        rubi.append(3949)
        return Dist(S(1)/(a**S(2)*(S(2)*n + S(1))), Int((a + b/cos(c + d*x))**(n + S(1))*(a*(S(2)*n + S(1)) - b*(n + S(1))/cos(c + d*x)), x), x) + Simp((a + b/cos(c + d*x))**n*tan(c + d*x)/(d*(S(2)*n + S(1))), x)
    rule3949 = ReplacementRule(pattern3949, replacement3949)
    pattern3950 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1265, cons87, cons1586, cons808)
    def replacement3950(b, d, c, a, n, x):
        rubi.append(3950)
        return Dist(S(1)/(a**S(2)*(S(2)*n + S(1))), Int((a + b/sin(c + d*x))**(n + S(1))*(a*(S(2)*n + S(1)) - b*(n + S(1))/sin(c + d*x)), x), x) - Simp((a + b/sin(c + d*x))**n/(d*(S(2)*n + S(1))*tan(c + d*x)), x)
    rule3950 = ReplacementRule(pattern3950, replacement3950)
    pattern3951 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons543, cons43)
    def replacement3951(b, d, c, a, n, x):
        rubi.append(3951)
        return -Dist(a**n*tan(c + d*x)/(d*sqrt(S(1) - S(1)/cos(c + d*x))*sqrt(S(1) + S(1)/cos(c + d*x))), Subst(Int((S(1) + b*x/a)**(n + S(-1)/2)/(x*sqrt(S(1) - b*x/a)), x), x, S(1)/cos(c + d*x)), x)
    rule3951 = ReplacementRule(pattern3951, replacement3951)
    pattern3952 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons543, cons43)
    def replacement3952(b, d, c, a, n, x):
        rubi.append(3952)
        return Dist(a**n/(d*sqrt(S(1) - S(1)/sin(c + d*x))*sqrt(S(1) + S(1)/sin(c + d*x))*tan(c + d*x)), Subst(Int((S(1) + b*x/a)**(n + S(-1)/2)/(x*sqrt(S(1) - b*x/a)), x), x, S(1)/sin(c + d*x)), x)
    rule3952 = ReplacementRule(pattern3952, replacement3952)
    pattern3953 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons543, cons448)
    def replacement3953(b, d, c, a, n, x):
        rubi.append(3953)
        return Dist(a**IntPart(n)*(S(1) + b/(a*cos(c + d*x)))**(-FracPart(n))*(a + b/cos(c + d*x))**FracPart(n), Int((S(1) + b/(a*cos(c + d*x)))**n, x), x)
    rule3953 = ReplacementRule(pattern3953, replacement3953)
    pattern3954 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons543, cons448)
    def replacement3954(b, d, c, a, n, x):
        rubi.append(3954)
        return Dist(a**IntPart(n)*(S(1) + b/(a*sin(c + d*x)))**(-FracPart(n))*(a + b/sin(c + d*x))**FracPart(n), Int((S(1) + b/(a*sin(c + d*x)))**n, x), x)
    rule3954 = ReplacementRule(pattern3954, replacement3954)
    pattern3955 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement3955(b, d, c, a, x):
        rubi.append(3955)
        return Simp(-S(2)*sqrt(b*(S(1) + S(1)/cos(c + d*x))/(a + b/cos(c + d*x)))*sqrt(-b*(S(1) - S(1)/cos(c + d*x))/(a + b/cos(c + d*x)))*(a + b/cos(c + d*x))*EllipticPi(a/(a + b), asin(Rt(a + b, S(2))/sqrt(a + b/cos(c + d*x))), (a - b)/(a + b))/(d*Rt(a + b, S(2))*tan(c + d*x)), x)
    rule3955 = ReplacementRule(pattern3955, replacement3955)
    pattern3956 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement3956(b, d, c, a, x):
        rubi.append(3956)
        return Simp(S(2)*sqrt(b*(S(1) + S(1)/sin(c + d*x))/(a + b/sin(c + d*x)))*sqrt(-b*(S(1) - S(1)/sin(c + d*x))/(a + b/sin(c + d*x)))*(a + b/sin(c + d*x))*EllipticPi(a/(a + b), asin(Rt(a + b, S(2))/sqrt(a + b/sin(c + d*x))), (a - b)/(a + b))*tan(c + d*x)/(d*Rt(a + b, S(2))), x)
    rule3956 = ReplacementRule(pattern3956, replacement3956)
    pattern3957 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement3957(b, d, c, a, x):
        rubi.append(3957)
        return Dist(b**S(2), Int((S(1) + S(1)/cos(c + d*x))/(sqrt(a + b/cos(c + d*x))*cos(c + d*x)), x), x) + Int((a**S(2) + b*(S(2)*a - b)/cos(c + d*x))/sqrt(a + b/cos(c + d*x)), x)
    rule3957 = ReplacementRule(pattern3957, replacement3957)
    pattern3958 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement3958(b, d, c, a, x):
        rubi.append(3958)
        return Dist(b**S(2), Int((S(1) + S(1)/sin(c + d*x))/(sqrt(a + b/sin(c + d*x))*sin(c + d*x)), x), x) + Int((a**S(2) + b*(S(2)*a - b)/sin(c + d*x))/sqrt(a + b/sin(c + d*x)), x)
    rule3958 = ReplacementRule(pattern3958, replacement3958)
    pattern3959 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1267, cons87, cons744, cons808)
    def replacement3959(b, d, c, a, n, x):
        rubi.append(3959)
        return Dist(S(1)/(n + S(-1)), Int((a + b/cos(c + d*x))**(n + S(-3))*Simp(a**S(3)*(n + S(-1)) + a*b**S(2)*(S(3)*n + S(-4))/cos(c + d*x)**S(2) + b*(S(3)*a**S(2)*(n + S(-1)) + b**S(2)*(n + S(-2)))/cos(c + d*x), x), x), x) + Simp(b**S(2)*(a + b/cos(c + d*x))**(n + S(-2))*tan(c + d*x)/(d*(n + S(-1))), x)
    rule3959 = ReplacementRule(pattern3959, replacement3959)
    pattern3960 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1267, cons87, cons744, cons808)
    def replacement3960(b, d, c, a, n, x):
        rubi.append(3960)
        return Dist(S(1)/(n + S(-1)), Int((a + b/sin(c + d*x))**(n + S(-3))*Simp(a**S(3)*(n + S(-1)) + a*b**S(2)*(S(3)*n + S(-4))/sin(c + d*x)**S(2) + b*(S(3)*a**S(2)*(n + S(-1)) + b**S(2)*(n + S(-2)))/sin(c + d*x), x), x), x) - Simp(b**S(2)*(a + b/sin(c + d*x))**(n + S(-2))/(d*(n + S(-1))*tan(c + d*x)), x)
    rule3960 = ReplacementRule(pattern3960, replacement3960)
    pattern3961 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement3961(b, d, c, a, x):
        rubi.append(3961)
        return -Dist(S(1)/a, Int(S(1)/(a*cos(c + d*x)/b + S(1)), x), x) + Simp(x/a, x)
    rule3961 = ReplacementRule(pattern3961, replacement3961)
    pattern3962 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement3962(b, d, c, a, x):
        rubi.append(3962)
        return -Dist(S(1)/a, Int(S(1)/(a*sin(c + d*x)/b + S(1)), x), x) + Simp(x/a, x)
    rule3962 = ReplacementRule(pattern3962, replacement3962)
    pattern3963 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement3963(b, d, c, a, x):
        rubi.append(3963)
        return Simp(-S(2)*sqrt(b*(S(1) - S(1)/cos(c + d*x))/(a + b))*sqrt(-b*(S(1) + S(1)/cos(c + d*x))/(a - b))*EllipticPi((a + b)/a, asin(sqrt(a + b/cos(c + d*x))/Rt(a + b, S(2))), (a + b)/(a - b))*Rt(a + b, S(2))/(a*d*tan(c + d*x)), x)
    rule3963 = ReplacementRule(pattern3963, replacement3963)
    pattern3964 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement3964(b, d, c, a, x):
        rubi.append(3964)
        return Simp(S(2)*sqrt(b*(S(1) - S(1)/sin(c + d*x))/(a + b))*sqrt(-b*(S(1) + S(1)/sin(c + d*x))/(a - b))*EllipticPi((a + b)/a, asin(sqrt(a + b/sin(c + d*x))/Rt(a + b, S(2))), (a + b)/(a - b))*Rt(a + b, S(2))*tan(c + d*x)/(a*d), x)
    rule3964 = ReplacementRule(pattern3964, replacement3964)
    pattern3965 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1267, cons87, cons89, cons808)
    def replacement3965(b, d, c, a, n, x):
        rubi.append(3965)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(n + S(1))), Int((a + b/cos(c + d*x))**(n + S(1))*Simp(-a*b*(n + S(1))/cos(c + d*x) + b**S(2)*(n + S(2))/cos(c + d*x)**S(2) + (a**S(2) - b**S(2))*(n + S(1)), x), x), x) - Simp(b**S(2)*(a + b/cos(c + d*x))**(n + S(1))*tan(c + d*x)/(a*d*(a**S(2) - b**S(2))*(n + S(1))), x)
    rule3965 = ReplacementRule(pattern3965, replacement3965)
    pattern3966 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1267, cons87, cons89, cons808)
    def replacement3966(b, d, c, a, n, x):
        rubi.append(3966)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(n + S(1))), Int((a + b/sin(c + d*x))**(n + S(1))*Simp(-a*b*(n + S(1))/sin(c + d*x) + b**S(2)*(n + S(2))/sin(c + d*x)**S(2) + (a**S(2) - b**S(2))*(n + S(1)), x), x), x) + Simp(b**S(2)*(a + b/sin(c + d*x))**(n + S(1))/(a*d*(a**S(2) - b**S(2))*(n + S(1))*tan(c + d*x)), x)
    rule3966 = ReplacementRule(pattern3966, replacement3966)
    pattern3967 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1267, cons543)
    def replacement3967(b, d, c, a, n, x):
        rubi.append(3967)
        return Int((a + b/cos(c + d*x))**n, x)
    rule3967 = ReplacementRule(pattern3967, replacement3967)
    pattern3968 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1267, cons543)
    def replacement3968(b, d, c, a, n, x):
        rubi.append(3968)
        return Int((a + b/sin(c + d*x))**n, x)
    rule3968 = ReplacementRule(pattern3968, replacement3968)
    pattern3969 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1587)
    def replacement3969(f, b, d, a, n, x, e):
        rubi.append(3969)
        return Dist(a, Int((d/cos(e + f*x))**n, x), x) + Dist(b/d, Int((d/cos(e + f*x))**(n + S(1)), x), x)
    rule3969 = ReplacementRule(pattern3969, replacement3969)
    pattern3970 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1587)
    def replacement3970(f, b, d, a, n, x, e):
        rubi.append(3970)
        return Dist(a, Int((d/sin(e + f*x))**n, x), x) + Dist(b/d, Int((d/sin(e + f*x))**(n + S(1)), x), x)
    rule3970 = ReplacementRule(pattern3970, replacement3970)
    pattern3971 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1587)
    def replacement3971(f, b, d, a, n, x, e):
        rubi.append(3971)
        return Dist(S(2)*a*b/d, Int((d/cos(e + f*x))**(n + S(1)), x), x) + Int((d/cos(e + f*x))**n*(a**S(2) + b**S(2)/cos(e + f*x)**S(2)), x)
    rule3971 = ReplacementRule(pattern3971, replacement3971)
    pattern3972 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1587)
    def replacement3972(f, b, d, a, n, x, e):
        rubi.append(3972)
        return Dist(S(2)*a*b/d, Int((d/sin(e + f*x))**(n + S(1)), x), x) + Int((d/sin(e + f*x))**n*(a**S(2) + b**S(2)/sin(e + f*x)**S(2)), x)
    rule3972 = ReplacementRule(pattern3972, replacement3972)
    pattern3973 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons1254)
    def replacement3973(f, b, a, x, e):
        rubi.append(3973)
        return Dist(S(1)/b, Int(S(1)/cos(e + f*x), x), x) - Dist(a/b, Int(S(1)/((a + b/cos(e + f*x))*cos(e + f*x)), x), x)
    rule3973 = ReplacementRule(pattern3973, replacement3973)
    pattern3974 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons1254)
    def replacement3974(f, b, a, x, e):
        rubi.append(3974)
        return Dist(S(1)/b, Int(S(1)/sin(e + f*x), x), x) - Dist(a/b, Int(S(1)/((a + b/sin(e + f*x))*sin(e + f*x)), x), x)
    rule3974 = ReplacementRule(pattern3974, replacement3974)
    pattern3975 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(3)), x_), cons2, cons3, cons48, cons125, cons1254)
    def replacement3975(f, b, a, x, e):
        rubi.append(3975)
        return -Dist(a/b, Int(S(1)/((a + b/cos(e + f*x))*cos(e + f*x)**S(2)), x), x) + Simp(tan(e + f*x)/(b*f), x)
    rule3975 = ReplacementRule(pattern3975, replacement3975)
    pattern3976 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(3)), x_), cons2, cons3, cons48, cons125, cons1254)
    def replacement3976(f, b, a, x, e):
        rubi.append(3976)
        return -Dist(a/b, Int(S(1)/((a + b/sin(e + f*x))*sin(e + f*x)**S(2)), x), x) - Simp(S(1)/(b*f*tan(e + f*x)), x)
    rule3976 = ReplacementRule(pattern3976, replacement3976)
    pattern3977 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons62, cons87)
    def replacement3977(m, f, b, d, a, n, x, e):
        rubi.append(3977)
        return Int(ExpandTrig((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m, x), x)
    rule3977 = ReplacementRule(pattern3977, replacement3977)
    pattern3978 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons62, cons87)
    def replacement3978(m, f, b, d, a, n, x, e):
        rubi.append(3978)
        return Int(ExpandTrig((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m, x), x)
    rule3978 = ReplacementRule(pattern3978, replacement3978)
    pattern3979 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1265)
    def replacement3979(f, b, a, x, e):
        rubi.append(3979)
        return Simp(S(2)*b*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))), x)
    rule3979 = ReplacementRule(pattern3979, replacement3979)
    pattern3980 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1265)
    def replacement3980(f, b, a, x, e):
        rubi.append(3980)
        return Simp(-S(2)*b/(f*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), x)
    rule3980 = ReplacementRule(pattern3980, replacement3980)
    pattern3981 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1423, cons515)
    def replacement3981(m, f, b, a, x, e):
        rubi.append(3981)
        return Dist(a*(S(2)*m + S(-1))/m, Int((a + b/cos(e + f*x))**(m + S(-1))/cos(e + f*x), x), x) + Simp(b*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*m), x)
    rule3981 = ReplacementRule(pattern3981, replacement3981)
    pattern3982 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1423, cons515)
    def replacement3982(m, f, b, a, x, e):
        rubi.append(3982)
        return Dist(a*(S(2)*m + S(-1))/m, Int((a + b/sin(e + f*x))**(m + S(-1))/sin(e + f*x), x), x) - Simp(b*(a + b/sin(e + f*x))**(m + S(-1))/(f*m*tan(e + f*x)), x)
    rule3982 = ReplacementRule(pattern3982, replacement3982)
    pattern3983 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1265)
    def replacement3983(f, b, a, x, e):
        rubi.append(3983)
        return Simp(tan(e + f*x)/(f*(a/cos(e + f*x) + b)), x)
    rule3983 = ReplacementRule(pattern3983, replacement3983)
    pattern3984 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1265)
    def replacement3984(f, b, a, x, e):
        rubi.append(3984)
        return -Simp(S(1)/(f*(a/sin(e + f*x) + b)*tan(e + f*x)), x)
    rule3984 = ReplacementRule(pattern3984, replacement3984)
    pattern3985 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1265)
    def replacement3985(f, b, a, x, e):
        rubi.append(3985)
        return Dist(S(2)/f, Subst(Int(S(1)/(S(2)*a + x**S(2)), x), x, b*tan(e + f*x)/sqrt(a + b/cos(e + f*x))), x)
    rule3985 = ReplacementRule(pattern3985, replacement3985)
    pattern3986 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1265)
    def replacement3986(f, b, a, x, e):
        rubi.append(3986)
        return Dist(-S(2)/f, Subst(Int(S(1)/(S(2)*a + x**S(2)), x), x, b/(sqrt(a + b/sin(e + f*x))*tan(e + f*x))), x)
    rule3986 = ReplacementRule(pattern3986, replacement3986)
    pattern3987 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1320, cons515)
    def replacement3987(m, f, b, a, x, e):
        rubi.append(3987)
        return Dist((m + S(1))/(a*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))/cos(e + f*x), x), x) - Simp(b*(a + b/cos(e + f*x))**m*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule3987 = ReplacementRule(pattern3987, replacement3987)
    pattern3988 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1320, cons515)
    def replacement3988(m, f, b, a, x, e):
        rubi.append(3988)
        return Dist((m + S(1))/(a*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))/sin(e + f*x), x), x) + Simp(b*(a + b/sin(e + f*x))**m/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule3988 = ReplacementRule(pattern3988, replacement3988)
    pattern3989 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1320)
    def replacement3989(m, f, b, a, x, e):
        rubi.append(3989)
        return Dist(m/(b*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(S(2)*m + S(1))), x)
    rule3989 = ReplacementRule(pattern3989, replacement3989)
    pattern3990 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1320)
    def replacement3990(m, f, b, a, x, e):
        rubi.append(3990)
        return Dist(m/(b*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**m/(f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule3990 = ReplacementRule(pattern3990, replacement3990)
    pattern3991 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1321)
    def replacement3991(m, f, b, a, x, e):
        rubi.append(3991)
        return Dist(a*m/(b*(m + S(1))), Int((a + b/cos(e + f*x))**m/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule3991 = ReplacementRule(pattern3991, replacement3991)
    pattern3992 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1321)
    def replacement3992(m, f, b, a, x, e):
        rubi.append(3992)
        return Dist(a*m/(b*(m + S(1))), Int((a + b/sin(e + f*x))**m/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule3992 = ReplacementRule(pattern3992, replacement3992)
    pattern3993 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(3), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1320)
    def replacement3993(m, f, b, a, x, e):
        rubi.append(3993)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*(a*m - b*(S(2)*m + S(1))/cos(e + f*x))/cos(e + f*x), x), x) - Simp(b*(a + b/cos(e + f*x))**m*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule3993 = ReplacementRule(pattern3993, replacement3993)
    pattern3994 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(3), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1320)
    def replacement3994(m, f, b, a, x, e):
        rubi.append(3994)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*(a*m - b*(S(2)*m + S(1))/sin(e + f*x))/sin(e + f*x), x), x) + Simp(b*(a + b/sin(e + f*x))**m/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule3994 = ReplacementRule(pattern3994, replacement3994)
    pattern3995 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(3), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1321)
    def replacement3995(m, f, b, a, x, e):
        rubi.append(3995)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/cos(e + f*x))**m*(-a/cos(e + f*x) + b*(m + S(1)))/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + S(2))), x)
    rule3995 = ReplacementRule(pattern3995, replacement3995)
    pattern3996 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(3), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1321)
    def replacement3996(m, f, b, a, x, e):
        rubi.append(3996)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/sin(e + f*x))**m*(-a/sin(e + f*x) + b*(m + S(1)))/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + S(2))*tan(e + f*x)), x)
    rule3996 = ReplacementRule(pattern3996, replacement3996)
    pattern3997 = Pattern(Integral(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1588)
    def replacement3997(f, b, d, a, x, e):
        rubi.append(3997)
        return Dist(S(2)*a*sqrt(a*d/b)/(b*f), Subst(Int(S(1)/sqrt(S(1) + x**S(2)/a), x), x, b*tan(e + f*x)/sqrt(a + b/cos(e + f*x))), x)
    rule3997 = ReplacementRule(pattern3997, replacement3997)
    pattern3998 = Pattern(Integral(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1588)
    def replacement3998(f, b, d, a, x, e):
        rubi.append(3998)
        return Dist(-S(2)*a*sqrt(a*d/b)/(b*f), Subst(Int(S(1)/sqrt(S(1) + x**S(2)/a), x), x, b/(sqrt(a + b/sin(e + f*x))*tan(e + f*x))), x)
    rule3998 = ReplacementRule(pattern3998, replacement3998)
    pattern3999 = Pattern(Integral(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1589)
    def replacement3999(f, b, d, a, x, e):
        rubi.append(3999)
        return Dist(S(2)*b*d/f, Subst(Int(S(1)/(b - d*x**S(2)), x), x, b*tan(e + f*x)/(sqrt(d/cos(e + f*x))*sqrt(a + b/cos(e + f*x)))), x)
    rule3999 = ReplacementRule(pattern3999, replacement3999)
    pattern4000 = Pattern(Integral(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1589)
    def replacement4000(f, b, d, a, x, e):
        rubi.append(4000)
        return Dist(-S(2)*b*d/f, Subst(Int(S(1)/(b - d*x**S(2)), x), x, b/(sqrt(d/sin(e + f*x))*sqrt(a + b/sin(e + f*x))*tan(e + f*x))), x)
    rule4000 = ReplacementRule(pattern4000, replacement4000)
    pattern4001 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons165, cons808)
    def replacement4001(f, b, d, a, n, x, e):
        rubi.append(4001)
        return Dist(S(2)*a*d*(n + S(-1))/(b*(S(2)*n + S(-1))), Int((d/cos(e + f*x))**(n + S(-1))*sqrt(a + b/cos(e + f*x)), x), x) + Simp(S(2)*b*d*(d/cos(e + f*x))**(n + S(-1))*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(-1))), x)
    rule4001 = ReplacementRule(pattern4001, replacement4001)
    pattern4002 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons165, cons808)
    def replacement4002(f, b, d, a, n, x, e):
        rubi.append(4002)
        return Dist(S(2)*a*d*(n + S(-1))/(b*(S(2)*n + S(-1))), Int((d/sin(e + f*x))**(n + S(-1))*sqrt(a + b/sin(e + f*x)), x), x) + Simp(-S(2)*b*d*(d/sin(e + f*x))**(n + S(-1))/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(-1))*tan(e + f*x)), x)
    rule4002 = ReplacementRule(pattern4002, replacement4002)
    pattern4003 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265)
    def replacement4003(f, b, d, a, x, e):
        rubi.append(4003)
        return Simp(S(2)*a*tan(e + f*x)/(f*sqrt(d/cos(e + f*x))*sqrt(a + b/cos(e + f*x))), x)
    rule4003 = ReplacementRule(pattern4003, replacement4003)
    pattern4004 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265)
    def replacement4004(f, b, d, a, x, e):
        rubi.append(4004)
        return Simp(-S(2)*a/(f*sqrt(d/sin(e + f*x))*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), x)
    rule4004 = ReplacementRule(pattern4004, replacement4004)
    pattern4005 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons1590, cons808)
    def replacement4005(f, b, d, a, n, x, e):
        rubi.append(4005)
        return Dist(a*(S(2)*n + S(1))/(S(2)*b*d*n), Int((d/cos(e + f*x))**(n + S(1))*sqrt(a + b/cos(e + f*x)), x), x) - Simp(a*(d/cos(e + f*x))**n*tan(e + f*x)/(f*n*sqrt(a + b/cos(e + f*x))), x)
    rule4005 = ReplacementRule(pattern4005, replacement4005)
    pattern4006 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons1590, cons808)
    def replacement4006(f, b, d, a, n, x, e):
        rubi.append(4006)
        return Dist(a*(S(2)*n + S(1))/(S(2)*b*d*n), Int((d/sin(e + f*x))**(n + S(1))*sqrt(a + b/sin(e + f*x)), x), x) + Simp(a*(d/sin(e + f*x))**n/(f*n*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), x)
    rule4006 = ReplacementRule(pattern4006, replacement4006)
    pattern4007 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265)
    def replacement4007(f, b, d, a, n, x, e):
        rubi.append(4007)
        return -Dist(a**S(2)*d*tan(e + f*x)/(f*sqrt(a - b/cos(e + f*x))*sqrt(a + b/cos(e + f*x))), Subst(Int((d*x)**(n + S(-1))/sqrt(a - b*x), x), x, S(1)/cos(e + f*x)), x)
    rule4007 = ReplacementRule(pattern4007, replacement4007)
    pattern4008 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265)
    def replacement4008(f, b, d, a, n, x, e):
        rubi.append(4008)
        return Dist(a**S(2)*d/(f*sqrt(a - b/sin(e + f*x))*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), Subst(Int((d*x)**(n + S(-1))/sqrt(a - b*x), x), x, S(1)/sin(e + f*x)), x)
    rule4008 = ReplacementRule(pattern4008, replacement4008)
    pattern4009 = Pattern(Integral(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1330, cons43)
    def replacement4009(f, b, d, a, x, e):
        rubi.append(4009)
        return Dist(sqrt(S(2))*sqrt(a)/(b*f), Subst(Int(S(1)/sqrt(x**S(2) + S(1)), x), x, b*tan(e + f*x)/(a + b/cos(e + f*x))), x)
    rule4009 = ReplacementRule(pattern4009, replacement4009)
    pattern4010 = Pattern(Integral(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1330, cons43)
    def replacement4010(f, b, d, a, x, e):
        rubi.append(4010)
        return -Dist(sqrt(S(2))*sqrt(a)/(b*f), Subst(Int(S(1)/sqrt(x**S(2) + S(1)), x), x, b/((a + b/sin(e + f*x))*tan(e + f*x))), x)
    rule4010 = ReplacementRule(pattern4010, replacement4010)
    pattern4011 = Pattern(Integral(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265)
    def replacement4011(f, b, d, a, x, e):
        rubi.append(4011)
        return Dist(S(2)*b*d/(a*f), Subst(Int(S(1)/(S(2)*b - d*x**S(2)), x), x, b*tan(e + f*x)/(sqrt(d/cos(e + f*x))*sqrt(a + b/cos(e + f*x)))), x)
    rule4011 = ReplacementRule(pattern4011, replacement4011)
    pattern4012 = Pattern(Integral(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265)
    def replacement4012(f, b, d, a, x, e):
        rubi.append(4012)
        return Dist(-S(2)*b*d/(a*f), Subst(Int(S(1)/(S(2)*b - d*x**S(2)), x), x, b/(sqrt(d/sin(e + f*x))*sqrt(a + b/sin(e + f*x))*tan(e + f*x))), x)
    rule4012 = ReplacementRule(pattern4012, replacement4012)
    pattern4013 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1255, cons31, cons1423, cons515)
    def replacement4013(m, f, b, d, a, n, x, e):
        rubi.append(4013)
        return Dist(b*(S(2)*m + S(-1))/(d*m), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**(m + S(-1)), x), x) + Simp(a*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*m), x)
    rule4013 = ReplacementRule(pattern4013, replacement4013)
    pattern4014 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1255, cons31, cons1423, cons515)
    def replacement4014(m, f, b, d, a, n, x, e):
        rubi.append(4014)
        return Dist(b*(S(2)*m + S(-1))/(d*m), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**(m + S(-1)), x), x) - Simp(a*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-1))/(f*m*tan(e + f*x)), x)
    rule4014 = ReplacementRule(pattern4014, replacement4014)
    pattern4015 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1255, cons31, cons1320, cons515)
    def replacement4015(m, f, b, d, a, n, x, e):
        rubi.append(4015)
        return Dist(d*(m + S(1))/(b*(S(2)*m + S(1))), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1)), x), x) - Simp(b*d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**m*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule4015 = ReplacementRule(pattern4015, replacement4015)
    pattern4016 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1255, cons31, cons1320, cons515)
    def replacement4016(m, f, b, d, a, n, x, e):
        rubi.append(4016)
        return Dist(d*(m + S(1))/(b*(S(2)*m + S(1))), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1)), x), x) + Simp(b*d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**m/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4016 = ReplacementRule(pattern4016, replacement4016)
    pattern4017 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons93, cons111, cons1320)
    def replacement4017(m, f, b, d, a, n, x, e):
        rubi.append(4017)
        return Dist(m/(a*(S(2)*m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1)), x), x) + Simp((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(S(2)*m + S(1))), x)
    rule4017 = ReplacementRule(pattern4017, replacement4017)
    pattern4018 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons93, cons111, cons1320)
    def replacement4018(m, f, b, d, a, n, x, e):
        rubi.append(4018)
        return Dist(m/(a*(S(2)*m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1)), x), x) - Simp((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4018 = ReplacementRule(pattern4018, replacement4018)
    pattern4019 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons155, cons1321)
    def replacement4019(m, f, b, d, a, n, x, e):
        rubi.append(4019)
        return Dist(a*m/(b*d*(m + S(1))), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**m, x), x) + Simp((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4019 = ReplacementRule(pattern4019, replacement4019)
    pattern4020 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons155, cons1321)
    def replacement4020(m, f, b, d, a, n, x, e):
        rubi.append(4020)
        return Dist(a*m/(b*d*(m + S(1))), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**m, x), x) - Simp((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4020 = ReplacementRule(pattern4020, replacement4020)
    pattern4021 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons93, cons166, cons1591, cons515)
    def replacement4021(m, f, b, d, a, n, x, e):
        rubi.append(4021)
        return -Dist(a/(d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**(m + S(-2))*(-a*(m + S(2)*n + S(-1))/cos(e + f*x) + b*(m - S(2)*n + S(-2))), x), x) - Simp(b**S(2)*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-2))*tan(e + f*x)/(f*n), x)
    rule4021 = ReplacementRule(pattern4021, replacement4021)
    pattern4022 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons93, cons166, cons1591, cons515)
    def replacement4022(m, f, b, d, a, n, x, e):
        rubi.append(4022)
        return -Dist(a/(d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**(m + S(-2))*(-a*(m + S(2)*n + S(-1))/sin(e + f*x) + b*(m - S(2)*n + S(-2))), x), x) + Simp(b**S(2)*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-2))/(f*n*tan(e + f*x)), x)
    rule4022 = ReplacementRule(pattern4022, replacement4022)
    pattern4023 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons31, cons166, cons1519, cons515)
    def replacement4023(m, f, b, d, a, n, x, e):
        rubi.append(4023)
        return Dist(b/(m + n + S(-1)), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-2))*(a*(S(3)*m + S(2)*n + S(-4))/cos(e + f*x) + b*(m + S(2)*n + S(-1))), x), x) + Simp(b**S(2)*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-2))*tan(e + f*x)/(f*(m + n + S(-1))), x)
    rule4023 = ReplacementRule(pattern4023, replacement4023)
    pattern4024 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons31, cons166, cons1519, cons515)
    def replacement4024(m, f, b, d, a, n, x, e):
        rubi.append(4024)
        return Dist(b/(m + n + S(-1)), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-2))*(a*(S(3)*m + S(2)*n + S(-4))/sin(e + f*x) + b*(m + S(2)*n + S(-1))), x), x) - Simp(b**S(2)*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-2))/(f*(m + n + S(-1))*tan(e + f*x)), x)
    rule4024 = ReplacementRule(pattern4024, replacement4024)
    pattern4025 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons93, cons94, cons1336, cons1592)
    def replacement4025(m, f, b, d, a, n, x, e):
        rubi.append(4025)
        return -Dist(d/(a*b*(S(2)*m + S(1))), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*(a*(n + S(-1)) - b*(m + n)/cos(e + f*x)), x), x) - Simp(b*d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**m*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule4025 = ReplacementRule(pattern4025, replacement4025)
    pattern4026 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons93, cons94, cons1336, cons1592)
    def replacement4026(m, f, b, d, a, n, x, e):
        rubi.append(4026)
        return -Dist(d/(a*b*(S(2)*m + S(1))), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))*(a*(n + S(-1)) - b*(m + n)/sin(e + f*x)), x), x) + Simp(b*d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**m/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4026 = ReplacementRule(pattern4026, replacement4026)
    pattern4027 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons93, cons94, cons744, cons1592)
    def replacement4027(m, f, b, d, a, n, x, e):
        rubi.append(4027)
        return Dist(d**S(2)/(a*b*(S(2)*m + S(1))), Int((d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**(m + S(1))*(a*(m - n + S(2))/cos(e + f*x) + b*(n + S(-2))), x), x) + Simp(d**S(2)*(d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(S(2)*m + S(1))), x)
    rule4027 = ReplacementRule(pattern4027, replacement4027)
    pattern4028 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons93, cons94, cons744, cons1592)
    def replacement4028(m, f, b, d, a, n, x, e):
        rubi.append(4028)
        return Dist(d**S(2)/(a*b*(S(2)*m + S(1))), Int((d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**(m + S(1))*(a*(m - n + S(2))/sin(e + f*x) + b*(n + S(-2))), x), x) - Simp(d**S(2)*(d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**m/(f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4028 = ReplacementRule(pattern4028, replacement4028)
    pattern4029 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons31, cons94, cons1592)
    def replacement4029(m, f, b, d, a, n, x, e):
        rubi.append(4029)
        return Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*(a*(S(2)*m + n + S(1)) - b*(m + n + S(1))/cos(e + f*x)), x), x) + Simp((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(S(2)*m + S(1))), x)
    rule4029 = ReplacementRule(pattern4029, replacement4029)
    pattern4030 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons31, cons94, cons1592)
    def replacement4030(m, f, b, d, a, n, x, e):
        rubi.append(4030)
        return Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*(a*(S(2)*m + n + S(1)) - b*(m + n + S(1))/sin(e + f*x)), x), x) - Simp((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4030 = ReplacementRule(pattern4030, replacement4030)
    pattern4031 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons165)
    def replacement4031(f, b, d, a, n, x, e):
        rubi.append(4031)
        return -Dist(d**S(2)/(a*b), Int((d/cos(e + f*x))**(n + S(-2))*(-a*(n + S(-1))/cos(e + f*x) + b*(n + S(-2))), x), x) - Simp(d**S(2)*(d/cos(e + f*x))**(n + S(-2))*tan(e + f*x)/(f*(a + b/cos(e + f*x))), x)
    rule4031 = ReplacementRule(pattern4031, replacement4031)
    pattern4032 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons165)
    def replacement4032(f, b, d, a, n, x, e):
        rubi.append(4032)
        return -Dist(d**S(2)/(a*b), Int((d/sin(e + f*x))**(n + S(-2))*(-a*(n + S(-1))/sin(e + f*x) + b*(n + S(-2))), x), x) + Simp(d**S(2)*(d/sin(e + f*x))**(n + S(-2))/(f*(a + b/sin(e + f*x))*tan(e + f*x)), x)
    rule4032 = ReplacementRule(pattern4032, replacement4032)
    pattern4033 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons463)
    def replacement4033(f, b, d, a, n, x, e):
        rubi.append(4033)
        return -Dist(a**(S(-2)), Int((d/cos(e + f*x))**n*(a*(n + S(-1)) - b*n/cos(e + f*x)), x), x) - Simp((d/cos(e + f*x))**n*tan(e + f*x)/(f*(a + b/cos(e + f*x))), x)
    rule4033 = ReplacementRule(pattern4033, replacement4033)
    pattern4034 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons463)
    def replacement4034(f, b, d, a, n, x, e):
        rubi.append(4034)
        return -Dist(a**(S(-2)), Int((d/sin(e + f*x))**n*(a*(n + S(-1)) - b*n/sin(e + f*x)), x), x) + Simp((d/sin(e + f*x))**n/(f*(a + b/sin(e + f*x))*tan(e + f*x)), x)
    rule4034 = ReplacementRule(pattern4034, replacement4034)
    pattern4035 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265)
    def replacement4035(f, b, d, a, n, x, e):
        rubi.append(4035)
        return Dist(d*(n + S(-1))/(a*b), Int((d/cos(e + f*x))**(n + S(-1))*(a - b/cos(e + f*x)), x), x) + Simp(b*d*(d/cos(e + f*x))**(n + S(-1))*tan(e + f*x)/(a*f*(a + b/cos(e + f*x))), x)
    rule4035 = ReplacementRule(pattern4035, replacement4035)
    pattern4036 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265)
    def replacement4036(f, b, d, a, n, x, e):
        rubi.append(4036)
        return Dist(d*(n + S(-1))/(a*b), Int((d/sin(e + f*x))**(n + S(-1))*(a - b/sin(e + f*x)), x), x) - Simp(b*d*(d/sin(e + f*x))**(n + S(-1))/(a*f*(a + b/sin(e + f*x))*tan(e + f*x)), x)
    rule4036 = ReplacementRule(pattern4036, replacement4036)
    pattern4037 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265)
    def replacement4037(f, b, d, a, x, e):
        rubi.append(4037)
        return Dist(d/b, Int(sqrt(d/cos(e + f*x))*sqrt(a + b/cos(e + f*x)), x), x) - Dist(a*d/b, Int(sqrt(d/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x)
    rule4037 = ReplacementRule(pattern4037, replacement4037)
    pattern4038 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265)
    def replacement4038(f, b, d, a, x, e):
        rubi.append(4038)
        return Dist(d/b, Int(sqrt(d/sin(e + f*x))*sqrt(a + b/sin(e + f*x)), x), x) - Dist(a*d/b, Int(sqrt(d/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x)
    rule4038 = ReplacementRule(pattern4038, replacement4038)
    pattern4039 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons744, cons808)
    def replacement4039(f, b, d, a, n, x, e):
        rubi.append(4039)
        return Dist(d**S(2)/(b*(S(2)*n + S(-3))), Int((d/cos(e + f*x))**(n + S(-2))*(-a/cos(e + f*x) + S(2)*b*(n + S(-2)))/sqrt(a + b/cos(e + f*x)), x), x) + Simp(S(2)*d**S(2)*(d/cos(e + f*x))**(n + S(-2))*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(-3))), x)
    rule4039 = ReplacementRule(pattern4039, replacement4039)
    pattern4040 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons744, cons808)
    def replacement4040(f, b, d, a, n, x, e):
        rubi.append(4040)
        return Dist(d**S(2)/(b*(S(2)*n + S(-3))), Int((d/sin(e + f*x))**(n + S(-2))*(-a/sin(e + f*x) + S(2)*b*(n + S(-2)))/sqrt(a + b/sin(e + f*x)), x), x) + Simp(-S(2)*d**S(2)*(d/sin(e + f*x))**(n + S(-2))/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(-3))*tan(e + f*x)), x)
    rule4040 = ReplacementRule(pattern4040, replacement4040)
    pattern4041 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons463, cons808)
    def replacement4041(f, b, d, a, n, x, e):
        rubi.append(4041)
        return Dist(S(1)/(S(2)*b*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b*(S(2)*n + S(1))/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x) - Simp((d/cos(e + f*x))**n*tan(e + f*x)/(f*n*sqrt(a + b/cos(e + f*x))), x)
    rule4041 = ReplacementRule(pattern4041, replacement4041)
    pattern4042 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons87, cons463, cons808)
    def replacement4042(f, b, d, a, n, x, e):
        rubi.append(4042)
        return Dist(S(1)/(S(2)*b*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b*(S(2)*n + S(1))/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x) + Simp((d/sin(e + f*x))**n/(f*n*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), x)
    rule4042 = ReplacementRule(pattern4042, replacement4042)
    pattern4043 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1265, cons87, cons744, cons1519, cons85)
    def replacement4043(m, f, b, d, a, n, x, e):
        rubi.append(4043)
        return Dist(d**S(2)/(b*(m + n + S(-1))), Int((d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**m*(a*m/cos(e + f*x) + b*(n + S(-2))), x), x) + Simp(d**S(2)*(d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + n + S(-1))), x)
    rule4043 = ReplacementRule(pattern4043, replacement4043)
    pattern4044 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1265, cons87, cons744, cons1519, cons85)
    def replacement4044(m, f, b, d, a, n, x, e):
        rubi.append(4044)
        return Dist(d**S(2)/(b*(m + n + S(-1))), Int((d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**m*(a*m/sin(e + f*x) + b*(n + S(-2))), x), x) - Simp(d**S(2)*(d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**m/(f*(m + n + S(-1))*tan(e + f*x)), x)
    rule4044 = ReplacementRule(pattern4044, replacement4044)
    pattern4045 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43, cons23, cons1588)
    def replacement4045(m, f, b, d, a, n, x, e):
        rubi.append(4045)
        return Dist(a**(-n + S(2))*(a*d/b)**n*tan(e + f*x)/(f*sqrt(a - b/cos(e + f*x))*sqrt(a + b/cos(e + f*x))), Subst(Int((a - x)**(n + S(-1))*(S(2)*a - x)**(m + S(-1)/2)/sqrt(x), x), x, a - b/cos(e + f*x)), x)
    rule4045 = ReplacementRule(pattern4045, replacement4045)
    pattern4046 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43, cons23, cons1588)
    def replacement4046(m, f, b, d, a, n, x, e):
        rubi.append(4046)
        return -Dist(a**(-n + S(2))*(a*d/b)**n/(f*sqrt(a - b/sin(e + f*x))*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), Subst(Int((a - x)**(n + S(-1))*(S(2)*a - x)**(m + S(-1)/2)/sqrt(x), x), x, a - b/sin(e + f*x)), x)
    rule4046 = ReplacementRule(pattern4046, replacement4046)
    pattern4047 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43, cons23, cons1593)
    def replacement4047(m, f, b, d, a, n, x, e):
        rubi.append(4047)
        return Dist(a**(-n + S(1))*(-a*d/b)**n*tan(e + f*x)/(f*sqrt(a - b/cos(e + f*x))*sqrt(a + b/cos(e + f*x))), Subst(Int(x**(m + S(-1)/2)*(a - x)**(n + S(-1))/sqrt(S(2)*a - x), x), x, a + b/cos(e + f*x)), x)
    rule4047 = ReplacementRule(pattern4047, replacement4047)
    pattern4048 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43, cons23, cons1593)
    def replacement4048(m, f, b, d, a, n, x, e):
        rubi.append(4048)
        return -Dist(a**(-n + S(1))*(-a*d/b)**n/(f*sqrt(a - b/sin(e + f*x))*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), Subst(Int(x**(m + S(-1)/2)*(a - x)**(n + S(-1))/sqrt(S(2)*a - x), x), x, a + b/sin(e + f*x)), x)
    rule4048 = ReplacementRule(pattern4048, replacement4048)
    pattern4049 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43)
    def replacement4049(m, f, b, d, a, n, x, e):
        rubi.append(4049)
        return -Dist(a**S(2)*d*tan(e + f*x)/(f*sqrt(a - b/cos(e + f*x))*sqrt(a + b/cos(e + f*x))), Subst(Int((d*x)**(n + S(-1))*(a + b*x)**(m + S(-1)/2)/sqrt(a - b*x), x), x, S(1)/cos(e + f*x)), x)
    rule4049 = ReplacementRule(pattern4049, replacement4049)
    pattern4050 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43)
    def replacement4050(m, f, b, d, a, n, x, e):
        rubi.append(4050)
        return Dist(a**S(2)*d/(f*sqrt(a - b/sin(e + f*x))*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), Subst(Int((d*x)**(n + S(-1))*(a + b*x)**(m + S(-1)/2)/sqrt(a - b*x), x), x, S(1)/sin(e + f*x)), x)
    rule4050 = ReplacementRule(pattern4050, replacement4050)
    pattern4051 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons448)
    def replacement4051(m, f, b, d, a, n, x, e):
        rubi.append(4051)
        return Dist(a**IntPart(m)*(S(1) + b/(a*cos(e + f*x)))**(-FracPart(m))*(a + b/cos(e + f*x))**FracPart(m), Int((d/cos(e + f*x))**n*(S(1) + b/(a*cos(e + f*x)))**m, x), x)
    rule4051 = ReplacementRule(pattern4051, replacement4051)
    pattern4052 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons448)
    def replacement4052(m, f, b, d, a, n, x, e):
        rubi.append(4052)
        return Dist(a**IntPart(m)*(S(1) + b/(a*sin(e + f*x)))**(-FracPart(m))*(a + b/sin(e + f*x))**FracPart(m), Int((d/sin(e + f*x))**n*(S(1) + b/(a*sin(e + f*x)))**m, x), x)
    rule4052 = ReplacementRule(pattern4052, replacement4052)
    pattern4053 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4053(f, b, a, x, e):
        rubi.append(4053)
        return Dist(b, Int((S(1) + S(1)/cos(e + f*x))/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) + Dist(a - b, Int(S(1)/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4053 = ReplacementRule(pattern4053, replacement4053)
    pattern4054 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4054(f, b, a, x, e):
        rubi.append(4054)
        return Dist(b, Int((S(1) + S(1)/sin(e + f*x))/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) + Dist(a - b, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4054 = ReplacementRule(pattern4054, replacement4054)
    pattern4055 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons166, cons515)
    def replacement4055(m, f, b, a, x, e):
        rubi.append(4055)
        return Dist(S(1)/m, Int((a + b/cos(e + f*x))**(m + S(-2))*(a**S(2)*m + a*b*(S(2)*m + S(-1))/cos(e + f*x) + b**S(2)*(m + S(-1)))/cos(e + f*x), x), x) + Simp(b*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*m), x)
    rule4055 = ReplacementRule(pattern4055, replacement4055)
    pattern4056 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons166, cons515)
    def replacement4056(m, f, b, a, x, e):
        rubi.append(4056)
        return Dist(S(1)/m, Int((a + b/sin(e + f*x))**(m + S(-2))*(a**S(2)*m + a*b*(S(2)*m + S(-1))/sin(e + f*x) + b**S(2)*(m + S(-1)))/sin(e + f*x), x), x) - Simp(b*(a + b/sin(e + f*x))**(m + S(-1))/(f*m*tan(e + f*x)), x)
    rule4056 = ReplacementRule(pattern4056, replacement4056)
    pattern4057 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4057(f, b, a, x, e):
        rubi.append(4057)
        return Dist(S(1)/b, Int(S(1)/(a*cos(e + f*x)/b + S(1)), x), x)
    rule4057 = ReplacementRule(pattern4057, replacement4057)
    pattern4058 = Pattern(Integral(S(1)/((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4058(f, b, a, x, e):
        rubi.append(4058)
        return Dist(S(1)/b, Int(S(1)/(a*sin(e + f*x)/b + S(1)), x), x)
    rule4058 = ReplacementRule(pattern4058, replacement4058)
    pattern4059 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4059(f, b, a, x, e):
        rubi.append(4059)
        return Simp(S(2)*sqrt(b*(S(1) - S(1)/cos(e + f*x))/(a + b))*sqrt(-b*(S(1) + S(1)/cos(e + f*x))/(a - b))*EllipticF(asin(sqrt(a + b/cos(e + f*x))/Rt(a + b, S(2))), (a + b)/(a - b))*Rt(a + b, S(2))/(b*f*tan(e + f*x)), x)
    rule4059 = ReplacementRule(pattern4059, replacement4059)
    pattern4060 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4060(f, b, a, x, e):
        rubi.append(4060)
        return Simp(-S(2)*sqrt(b*(S(1) - S(1)/sin(e + f*x))/(a + b))*sqrt(-b*(S(1) + S(1)/sin(e + f*x))/(a - b))*EllipticF(asin(sqrt(a + b/sin(e + f*x))/Rt(a + b, S(2))), (a + b)/(a - b))*Rt(a + b, S(2))*tan(e + f*x)/(b*f), x)
    rule4060 = ReplacementRule(pattern4060, replacement4060)
    pattern4061 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons94, cons515)
    def replacement4061(m, f, b, a, x, e):
        rubi.append(4061)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*(a*(m + S(1)) - b*(m + S(2))/cos(e + f*x))/cos(e + f*x), x), x) + Simp(b*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4061 = ReplacementRule(pattern4061, replacement4061)
    pattern4062 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons94, cons515)
    def replacement4062(m, f, b, a, x, e):
        rubi.append(4062)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*(a*(m + S(1)) - b*(m + S(2))/sin(e + f*x))/sin(e + f*x), x), x) - Simp(b*(a + b/sin(e + f*x))**(m + S(1))/(f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4062 = ReplacementRule(pattern4062, replacement4062)
    pattern4063 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons77)
    def replacement4063(m, f, b, a, x, e):
        rubi.append(4063)
        return -Dist(tan(e + f*x)/(f*sqrt(S(1) - S(1)/cos(e + f*x))*sqrt(S(1) + S(1)/cos(e + f*x))), Subst(Int((a + b*x)**m/(sqrt(-x + S(1))*sqrt(x + S(1))), x), x, S(1)/cos(e + f*x)), x)
    rule4063 = ReplacementRule(pattern4063, replacement4063)
    pattern4064 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons77)
    def replacement4064(m, f, b, a, x, e):
        rubi.append(4064)
        return Dist(S(1)/(f*sqrt(S(1) - S(1)/sin(e + f*x))*sqrt(S(1) + S(1)/sin(e + f*x))*tan(e + f*x)), Subst(Int((a + b*x)**m/(sqrt(-x + S(1))*sqrt(x + S(1))), x), x, S(1)/sin(e + f*x)), x)
    rule4064 = ReplacementRule(pattern4064, replacement4064)
    pattern4065 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons168)
    def replacement4065(m, f, b, a, x, e):
        rubi.append(4065)
        return Dist(m/(m + S(1)), Int((a + b/cos(e + f*x))**(m + S(-1))*(a/cos(e + f*x) + b)/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4065 = ReplacementRule(pattern4065, replacement4065)
    pattern4066 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons168)
    def replacement4066(m, f, b, a, x, e):
        rubi.append(4066)
        return Dist(m/(m + S(1)), Int((a + b/sin(e + f*x))**(m + S(-1))*(a/sin(e + f*x) + b)/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4066 = ReplacementRule(pattern4066, replacement4066)
    pattern4067 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons94)
    def replacement4067(m, f, b, a, x, e):
        rubi.append(4067)
        return -Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*(-a*(m + S(2))/cos(e + f*x) + b*(m + S(1)))/cos(e + f*x), x), x) - Simp(a*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4067 = ReplacementRule(pattern4067, replacement4067)
    pattern4068 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons94)
    def replacement4068(m, f, b, a, x, e):
        rubi.append(4068)
        return -Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*(-a*(m + S(2))/sin(e + f*x) + b*(m + S(1)))/sin(e + f*x), x), x) + Simp(a*(a + b/sin(e + f*x))**(m + S(1))/(f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4068 = ReplacementRule(pattern4068, replacement4068)
    pattern4069 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4069(f, b, a, x, e):
        rubi.append(4069)
        return -Int(S(1)/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x) + Int((S(1) + S(1)/cos(e + f*x))/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x)
    rule4069 = ReplacementRule(pattern4069, replacement4069)
    pattern4070 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4070(f, b, a, x, e):
        rubi.append(4070)
        return -Int(S(1)/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x) + Int((S(1) + S(1)/sin(e + f*x))/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x)
    rule4070 = ReplacementRule(pattern4070, replacement4070)
    pattern4071 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1267)
    def replacement4071(m, f, b, a, x, e):
        rubi.append(4071)
        return Dist(S(1)/b, Int((a + b/cos(e + f*x))**(m + S(1))/cos(e + f*x), x), x) - Dist(a/b, Int((a + b/cos(e + f*x))**m/cos(e + f*x), x), x)
    rule4071 = ReplacementRule(pattern4071, replacement4071)
    pattern4072 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1267)
    def replacement4072(m, f, b, a, x, e):
        rubi.append(4072)
        return Dist(S(1)/b, Int((a + b/sin(e + f*x))**(m + S(1))/sin(e + f*x), x), x) - Dist(a/b, Int((a + b/sin(e + f*x))**m/sin(e + f*x), x), x)
    rule4072 = ReplacementRule(pattern4072, replacement4072)
    pattern4073 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(3), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons94)
    def replacement4073(m, f, b, a, x, e):
        rubi.append(4073)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(a*b*(m + S(1)) - (a**S(2) + b**S(2)*(m + S(1)))/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp(a**S(2)*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4073 = ReplacementRule(pattern4073, replacement4073)
    pattern4074 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(3), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons94)
    def replacement4074(m, f, b, a, x, e):
        rubi.append(4074)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(a*b*(m + S(1)) - (a**S(2) + b**S(2)*(m + S(1)))/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp(a**S(2)*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4074 = ReplacementRule(pattern4074, replacement4074)
    pattern4075 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(3), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons272)
    def replacement4075(m, f, b, a, x, e):
        rubi.append(4075)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/cos(e + f*x))**m*(-a/cos(e + f*x) + b*(m + S(1)))/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + S(2))), x)
    rule4075 = ReplacementRule(pattern4075, replacement4075)
    pattern4076 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(3), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons272)
    def replacement4076(m, f, b, a, x, e):
        rubi.append(4076)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/sin(e + f*x))**m*(-a/sin(e + f*x) + b*(m + S(1)))/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + S(2))*tan(e + f*x)), x)
    rule4076 = ReplacementRule(pattern4076, replacement4076)
    pattern4077 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons1333, cons1594)
    def replacement4077(m, f, b, d, a, n, x, e):
        rubi.append(4077)
        return -Dist(S(1)/(d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**(m + S(-3))*Simp(a**S(2)*b*(m - S(2)*n + S(-2)) - a*(a**S(2)*(n + S(1)) + S(3)*b**S(2)*n)/cos(e + f*x) - b*(a**S(2)*(m + n + S(-1)) + b**S(2)*n)/cos(e + f*x)**S(2), x), x), x) - Simp(a**S(2)*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-2))*tan(e + f*x)/(f*n), x)
    rule4077 = ReplacementRule(pattern4077, replacement4077)
    pattern4078 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons1333, cons1594)
    def replacement4078(m, f, b, d, a, n, x, e):
        rubi.append(4078)
        return -Dist(S(1)/(d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**(m + S(-3))*Simp(a**S(2)*b*(m - S(2)*n + S(-2)) - a*(a**S(2)*(n + S(1)) + S(3)*b**S(2)*n)/sin(e + f*x) - b*(a**S(2)*(m + n + S(-1)) + b**S(2)*n)/sin(e + f*x)**S(2), x), x), x) + Simp(a**S(2)*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-2))/(f*n*tan(e + f*x)), x)
    rule4078 = ReplacementRule(pattern4078, replacement4078)
    pattern4079 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1267, cons31, cons1333, cons1334, cons1595)
    def replacement4079(m, f, b, d, a, n, x, e):
        rubi.append(4079)
        return Dist(S(1)/(d*(m + n + S(-1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-3))*Simp(a**S(3)*d*(m + n + S(-1)) + a*b**S(2)*d*n + a*b**S(2)*d*(S(3)*m + S(2)*n + S(-4))/cos(e + f*x)**S(2) + b*(S(3)*a**S(2)*d*(m + n + S(-1)) + b**S(2)*d*(m + n + S(-2)))/cos(e + f*x), x), x), x) + Simp(b**S(2)*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-2))*tan(e + f*x)/(f*(m + n + S(-1))), x)
    rule4079 = ReplacementRule(pattern4079, replacement4079)
    pattern4080 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1267, cons31, cons1333, cons1334, cons1595)
    def replacement4080(m, f, b, d, a, n, x, e):
        rubi.append(4080)
        return Dist(S(1)/(d*(m + n + S(-1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-3))*Simp(a**S(3)*d*(m + n + S(-1)) + a*b**S(2)*d*n + a*b**S(2)*d*(S(3)*m + S(2)*n + S(-4))/sin(e + f*x)**S(2) + b*(S(3)*a**S(2)*d*(m + n + S(-1)) + b**S(2)*d*(m + n + S(-2)))/sin(e + f*x), x), x), x) - Simp(b**S(2)*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-2))/(f*(m + n + S(-1))*tan(e + f*x)), x)
    rule4080 = ReplacementRule(pattern4080, replacement4080)
    pattern4081 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons94, cons1325, cons1170)
    def replacement4081(m, f, b, d, a, n, x, e):
        rubi.append(4081)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*Simp(a*d*(m + S(1))/cos(e + f*x) + b*d*(n + S(-1)) - b*d*(m + n + S(1))/cos(e + f*x)**S(2), x), x), x) + Simp(b*d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4081 = ReplacementRule(pattern4081, replacement4081)
    pattern4082 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons94, cons1325, cons1170)
    def replacement4082(m, f, b, d, a, n, x, e):
        rubi.append(4082)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))*Simp(a*d*(m + S(1))/sin(e + f*x) + b*d*(n + S(-1)) - b*d*(m + n + S(1))/sin(e + f*x)**S(2), x), x), x) - Simp(b*d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))/(f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4082 = ReplacementRule(pattern4082, replacement4082)
    pattern4083 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons94, cons1336, cons1170)
    def replacement4083(m, f, b, d, a, n, x, e):
        rubi.append(4083)
        return -Dist(d**S(2)/((a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**(m + S(1))*(-a*(m + n)/cos(e + f*x)**S(2) + a*(n + S(-2)) + b*(m + S(1))/cos(e + f*x)), x), x) - Simp(a*d**S(2)*(d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4083 = ReplacementRule(pattern4083, replacement4083)
    pattern4084 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons94, cons1336, cons1170)
    def replacement4084(m, f, b, d, a, n, x, e):
        rubi.append(4084)
        return -Dist(d**S(2)/((a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**(m + S(1))*(-a*(m + n)/sin(e + f*x)**S(2) + a*(n + S(-2)) + b*(m + S(1))/sin(e + f*x)), x), x) + Simp(a*d**S(2)*(d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**(m + S(1))/(f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4084 = ReplacementRule(pattern4084, replacement4084)
    pattern4085 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons94, cons1596)
    def replacement4085(m, f, b, d, a, n, x, e):
        rubi.append(4085)
        return Dist(d**S(3)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**(n + S(-3))*(a + b/cos(e + f*x))**(m + S(1))*Simp(a**S(2)*(n + S(-3)) + a*b*(m + S(1))/cos(e + f*x) - (a**S(2)*(n + S(-2)) + b**S(2)*(m + S(1)))/cos(e + f*x)**S(2), x), x), x) + Simp(a**S(2)*d**S(3)*(d/cos(e + f*x))**(n + S(-3))*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4085 = ReplacementRule(pattern4085, replacement4085)
    pattern4086 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons94, cons1596)
    def replacement4086(m, f, b, d, a, n, x, e):
        rubi.append(4086)
        return Dist(d**S(3)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**(n + S(-3))*(a + b/sin(e + f*x))**(m + S(1))*Simp(a**S(2)*(n + S(-3)) + a*b*(m + S(1))/sin(e + f*x) - (a**S(2)*(n + S(-2)) + b**S(2)*(m + S(1)))/sin(e + f*x)**S(2), x), x), x) - Simp(a**S(2)*d**S(3)*(d/sin(e + f*x))**(n + S(-3))*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4086 = ReplacementRule(pattern4086, replacement4086)
    pattern4087 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1597)
    def replacement4087(m, f, b, d, a, n, x, e):
        rubi.append(4087)
        return -Dist(S(1)/(a*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**m*Simp(-a*(n + S(1))/cos(e + f*x) + b*(m + n + S(1)) - b*(m + n + S(2))/cos(e + f*x)**S(2), x), x), x) - Simp((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(a*f*n), x)
    rule4087 = ReplacementRule(pattern4087, replacement4087)
    pattern4088 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1597)
    def replacement4088(m, f, b, d, a, n, x, e):
        rubi.append(4088)
        return -Dist(S(1)/(a*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**m*Simp(-a*(n + S(1))/sin(e + f*x) + b*(m + n + S(1)) - b*(m + n + S(2))/sin(e + f*x)**S(2), x), x), x) + Simp((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))/(a*f*n*tan(e + f*x)), x)
    rule4088 = ReplacementRule(pattern4088, replacement4088)
    pattern4089 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1267, cons31, cons94, cons1170)
    def replacement4089(m, f, b, d, a, n, x, e):
        rubi.append(4089)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*(a**S(2)*(m + S(1)) - a*b*(m + S(1))/cos(e + f*x) - b**S(2)*(m + n + S(1)) + b**S(2)*(m + n + S(2))/cos(e + f*x)**S(2)), x), x) - Simp(b**S(2)*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(a*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4089 = ReplacementRule(pattern4089, replacement4089)
    pattern4090 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1267, cons31, cons94, cons1170)
    def replacement4090(m, f, b, d, a, n, x, e):
        rubi.append(4090)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*(a**S(2)*(m + S(1)) - a*b*(m + S(1))/sin(e + f*x) - b**S(2)*(m + n + S(1)) + b**S(2)*(m + n + S(2))/sin(e + f*x)**S(2)), x), x) + Simp(b**S(2)*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))/(a*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4090 = ReplacementRule(pattern4090, replacement4090)
    pattern4091 = Pattern(Integral(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4091(f, b, d, a, x, e):
        rubi.append(4091)
        return Dist(sqrt(d/cos(e + f*x))*sqrt(d*cos(e + f*x))/d, Int(sqrt(d*cos(e + f*x))/(a*cos(e + f*x) + b), x), x)
    rule4091 = ReplacementRule(pattern4091, replacement4091)
    pattern4092 = Pattern(Integral(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4092(f, b, d, a, x, e):
        rubi.append(4092)
        return Dist(sqrt(d/sin(e + f*x))*sqrt(d*sin(e + f*x))/d, Int(sqrt(d*sin(e + f*x))/(a*sin(e + f*x) + b), x), x)
    rule4092 = ReplacementRule(pattern4092, replacement4092)
    pattern4093 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4093(f, b, d, a, x, e):
        rubi.append(4093)
        return Dist(d*sqrt(d/cos(e + f*x))*sqrt(d*cos(e + f*x)), Int(S(1)/(sqrt(d*cos(e + f*x))*(a*cos(e + f*x) + b)), x), x)
    rule4093 = ReplacementRule(pattern4093, replacement4093)
    pattern4094 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4094(f, b, d, a, x, e):
        rubi.append(4094)
        return Dist(d*sqrt(d/sin(e + f*x))*sqrt(d*sin(e + f*x)), Int(S(1)/(sqrt(d*sin(e + f*x))*(a*sin(e + f*x) + b)), x), x)
    rule4094 = ReplacementRule(pattern4094, replacement4094)
    pattern4095 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(5)/2)/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4095(f, b, d, a, x, e):
        rubi.append(4095)
        return Dist(d/b, Int((d/cos(e + f*x))**(S(3)/2), x), x) - Dist(a*d/b, Int((d/cos(e + f*x))**(S(3)/2)/(a + b/cos(e + f*x)), x), x)
    rule4095 = ReplacementRule(pattern4095, replacement4095)
    pattern4096 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(5)/2)/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4096(f, b, d, a, x, e):
        rubi.append(4096)
        return Dist(d/b, Int((d/sin(e + f*x))**(S(3)/2), x), x) - Dist(a*d/b, Int((d/sin(e + f*x))**(S(3)/2)/(a + b/sin(e + f*x)), x), x)
    rule4096 = ReplacementRule(pattern4096, replacement4096)
    pattern4097 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons1598)
    def replacement4097(f, b, d, a, n, x, e):
        rubi.append(4097)
        return Dist(d**S(3)/(b*(n + S(-2))), Int((d/cos(e + f*x))**(n + S(-3))*Simp(a*(n + S(-3)) - a*(n + S(-2))/cos(e + f*x)**S(2) + b*(n + S(-3))/cos(e + f*x), x)/(a + b/cos(e + f*x)), x), x) + Simp(d**S(3)*(d/cos(e + f*x))**(n + S(-3))*tan(e + f*x)/(b*f*(n + S(-2))), x)
    rule4097 = ReplacementRule(pattern4097, replacement4097)
    pattern4098 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons1598)
    def replacement4098(f, b, d, a, n, x, e):
        rubi.append(4098)
        return Dist(d**S(3)/(b*(n + S(-2))), Int((d/sin(e + f*x))**(n + S(-3))*Simp(a*(n + S(-3)) - a*(n + S(-2))/sin(e + f*x)**S(2) + b*(n + S(-3))/sin(e + f*x), x)/(a + b/sin(e + f*x)), x), x) - Simp(d**S(3)*(d/sin(e + f*x))**(n + S(-3))/(b*f*(n + S(-2))*tan(e + f*x)), x)
    rule4098 = ReplacementRule(pattern4098, replacement4098)
    pattern4099 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4099(f, b, d, a, x, e):
        rubi.append(4099)
        return Dist(a**(S(-2)), Int((a - b/cos(e + f*x))/sqrt(d/cos(e + f*x)), x), x) + Dist(b**S(2)/(a**S(2)*d**S(2)), Int((d/cos(e + f*x))**(S(3)/2)/(a + b/cos(e + f*x)), x), x)
    rule4099 = ReplacementRule(pattern4099, replacement4099)
    pattern4100 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4100(f, b, d, a, x, e):
        rubi.append(4100)
        return Dist(a**(S(-2)), Int((a - b/sin(e + f*x))/sqrt(d/sin(e + f*x)), x), x) + Dist(b**S(2)/(a**S(2)*d**S(2)), Int((d/sin(e + f*x))**(S(3)/2)/(a + b/sin(e + f*x)), x), x)
    rule4100 = ReplacementRule(pattern4100, replacement4100)
    pattern4101 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons1586, cons808)
    def replacement4101(f, b, d, a, n, x, e):
        rubi.append(4101)
        return -Dist(S(1)/(a*d*n), Int((d/cos(e + f*x))**(n + S(1))*Simp(-a*(n + S(1))/cos(e + f*x) + b*n - b*(n + S(1))/cos(e + f*x)**S(2), x)/(a + b/cos(e + f*x)), x), x) - Simp((d/cos(e + f*x))**n*tan(e + f*x)/(a*f*n), x)
    rule4101 = ReplacementRule(pattern4101, replacement4101)
    pattern4102 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons1586, cons808)
    def replacement4102(f, b, d, a, n, x, e):
        rubi.append(4102)
        return -Dist(S(1)/(a*d*n), Int((d/sin(e + f*x))**(n + S(1))*Simp(-a*(n + S(1))/sin(e + f*x) + b*n - b*(n + S(1))/sin(e + f*x)**S(2), x)/(a + b/sin(e + f*x)), x), x) + Simp((d/sin(e + f*x))**n/(a*f*n*tan(e + f*x)), x)
    rule4102 = ReplacementRule(pattern4102, replacement4102)
    pattern4103 = Pattern(Integral(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4103(f, b, d, a, x, e):
        rubi.append(4103)
        return Dist(a, Int(sqrt(d/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x) + Dist(b/d, Int((d/cos(e + f*x))**(S(3)/2)/sqrt(a + b/cos(e + f*x)), x), x)
    rule4103 = ReplacementRule(pattern4103, replacement4103)
    pattern4104 = Pattern(Integral(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4104(f, b, d, a, x, e):
        rubi.append(4104)
        return Dist(a, Int(sqrt(d/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x) + Dist(b/d, Int((d/sin(e + f*x))**(S(3)/2)/sqrt(a + b/sin(e + f*x)), x), x)
    rule4104 = ReplacementRule(pattern4104, replacement4104)
    pattern4105 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons165, cons808)
    def replacement4105(f, b, d, a, n, x, e):
        rubi.append(4105)
        return Dist(d**S(2)/(S(2)*n + S(-1)), Int((d/cos(e + f*x))**(n + S(-2))*Simp(S(2)*a*(n + S(-2)) + a/cos(e + f*x)**S(2) + b*(S(2)*n + S(-3))/cos(e + f*x), x)/sqrt(a + b/cos(e + f*x)), x), x) + Simp(S(2)*d*(d/cos(e + f*x))**(n + S(-1))*sqrt(a + b/cos(e + f*x))*sin(e + f*x)/(f*(S(2)*n + S(-1))), x)
    rule4105 = ReplacementRule(pattern4105, replacement4105)
    pattern4106 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons165, cons808)
    def replacement4106(f, b, d, a, n, x, e):
        rubi.append(4106)
        return Dist(d**S(2)/(S(2)*n + S(-1)), Int((d/sin(e + f*x))**(n + S(-2))*Simp(S(2)*a*(n + S(-2)) + a/sin(e + f*x)**S(2) + b*(S(2)*n + S(-3))/sin(e + f*x), x)/sqrt(a + b/sin(e + f*x)), x), x) + Simp(-S(2)*d*(d/sin(e + f*x))**(n + S(-1))*sqrt(a + b/sin(e + f*x))*cos(e + f*x)/(f*(S(2)*n + S(-1))), x)
    rule4106 = ReplacementRule(pattern4106, replacement4106)
    pattern4107 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4107(f, b, d, a, x, e):
        rubi.append(4107)
        return Dist(sqrt(a + b/cos(e + f*x))/(sqrt(d/cos(e + f*x))*sqrt(a*cos(e + f*x) + b)), Int(sqrt(a*cos(e + f*x) + b), x), x)
    rule4107 = ReplacementRule(pattern4107, replacement4107)
    pattern4108 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4108(f, b, d, a, x, e):
        rubi.append(4108)
        return Dist(sqrt(a + b/sin(e + f*x))/(sqrt(d/sin(e + f*x))*sqrt(a*sin(e + f*x) + b)), Int(sqrt(a*sin(e + f*x) + b), x), x)
    rule4108 = ReplacementRule(pattern4108, replacement4108)
    pattern4109 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons1586, cons808)
    def replacement4109(f, b, d, a, n, x, e):
        rubi.append(4109)
        return -Dist(S(1)/(S(2)*d*n), Int((d/cos(e + f*x))**(n + S(1))*Simp(-S(2)*a*(n + S(1))/cos(e + f*x) - b*(S(2)*n + S(3))/cos(e + f*x)**S(2) + b, x)/sqrt(a + b/cos(e + f*x)), x), x) - Simp((d/cos(e + f*x))**n*sqrt(a + b/cos(e + f*x))*tan(e + f*x)/(f*n), x)
    rule4109 = ReplacementRule(pattern4109, replacement4109)
    pattern4110 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons1586, cons808)
    def replacement4110(f, b, d, a, n, x, e):
        rubi.append(4110)
        return -Dist(S(1)/(S(2)*d*n), Int((d/sin(e + f*x))**(n + S(1))*Simp(-S(2)*a*(n + S(1))/sin(e + f*x) - b*(S(2)*n + S(3))/sin(e + f*x)**S(2) + b, x)/sqrt(a + b/sin(e + f*x)), x), x) + Simp((d/sin(e + f*x))**n*sqrt(a + b/sin(e + f*x))/(f*n*tan(e + f*x)), x)
    rule4110 = ReplacementRule(pattern4110, replacement4110)
    pattern4111 = Pattern(Integral(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4111(f, b, d, a, x, e):
        rubi.append(4111)
        return Dist(sqrt(d/cos(e + f*x))*sqrt(a*cos(e + f*x) + b)/sqrt(a + b/cos(e + f*x)), Int(S(1)/sqrt(a*cos(e + f*x) + b), x), x)
    rule4111 = ReplacementRule(pattern4111, replacement4111)
    pattern4112 = Pattern(Integral(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4112(f, b, d, a, x, e):
        rubi.append(4112)
        return Dist(sqrt(d/sin(e + f*x))*sqrt(a*sin(e + f*x) + b)/sqrt(a + b/sin(e + f*x)), Int(S(1)/sqrt(a*sin(e + f*x) + b), x), x)
    rule4112 = ReplacementRule(pattern4112, replacement4112)
    pattern4113 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4113(f, b, d, a, x, e):
        rubi.append(4113)
        return Dist(d*sqrt(d/cos(e + f*x))*sqrt(a*cos(e + f*x) + b)/sqrt(a + b/cos(e + f*x)), Int(S(1)/(sqrt(a*cos(e + f*x) + b)*cos(e + f*x)), x), x)
    rule4113 = ReplacementRule(pattern4113, replacement4113)
    pattern4114 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4114(f, b, d, a, x, e):
        rubi.append(4114)
        return Dist(d*sqrt(d/sin(e + f*x))*sqrt(a*sin(e + f*x) + b)/sqrt(a + b/sin(e + f*x)), Int(S(1)/(sqrt(a*sin(e + f*x) + b)*sin(e + f*x)), x), x)
    rule4114 = ReplacementRule(pattern4114, replacement4114)
    pattern4115 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons744, cons808)
    def replacement4115(f, b, d, a, n, x, e):
        rubi.append(4115)
        return Dist(d**S(3)/(b*(S(2)*n + S(-3))), Int((d/cos(e + f*x))**(n + S(-3))*Simp(S(2)*a*(n + S(-3)) - S(2)*a*(n + S(-2))/cos(e + f*x)**S(2) + b*(S(2)*n + S(-5))/cos(e + f*x), x)/sqrt(a + b/cos(e + f*x)), x), x) + Simp(S(2)*d**S(2)*(d/cos(e + f*x))**(n + S(-2))*sqrt(a + b/cos(e + f*x))*sin(e + f*x)/(b*f*(S(2)*n + S(-3))), x)
    rule4115 = ReplacementRule(pattern4115, replacement4115)
    pattern4116 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons744, cons808)
    def replacement4116(f, b, d, a, n, x, e):
        rubi.append(4116)
        return Dist(d**S(3)/(b*(S(2)*n + S(-3))), Int((d/sin(e + f*x))**(n + S(-3))*Simp(S(2)*a*(n + S(-3)) - S(2)*a*(n + S(-2))/sin(e + f*x)**S(2) + b*(S(2)*n + S(-5))/sin(e + f*x), x)/sqrt(a + b/sin(e + f*x)), x), x) + Simp(-S(2)*d**S(2)*(d/sin(e + f*x))**(n + S(-2))*sqrt(a + b/sin(e + f*x))*cos(e + f*x)/(b*f*(S(2)*n + S(-3))), x)
    rule4116 = ReplacementRule(pattern4116, replacement4116)
    pattern4117 = Pattern(Integral(cos(x_*WC('f', S(1)) + WC('e', S(0)))/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4117(f, b, a, x, e):
        rubi.append(4117)
        return -Dist(b/(S(2)*a), Int((S(1) + cos(e + f*x)**(S(-2)))/sqrt(a + b/cos(e + f*x)), x), x) + Simp(sqrt(a + b/cos(e + f*x))*sin(e + f*x)/(a*f), x)
    rule4117 = ReplacementRule(pattern4117, replacement4117)
    pattern4118 = Pattern(Integral(sin(x_*WC('f', S(1)) + WC('e', S(0)))/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1267)
    def replacement4118(f, b, a, x, e):
        rubi.append(4118)
        return -Dist(b/(S(2)*a), Int((S(1) + sin(e + f*x)**(S(-2)))/sqrt(a + b/sin(e + f*x)), x), x) - Simp(sqrt(a + b/sin(e + f*x))*cos(e + f*x)/(a*f), x)
    rule4118 = ReplacementRule(pattern4118, replacement4118)
    pattern4119 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4119(f, b, d, a, x, e):
        rubi.append(4119)
        return Dist(S(1)/a, Int(sqrt(a + b/cos(e + f*x))/sqrt(d/cos(e + f*x)), x), x) - Dist(b/(a*d), Int(sqrt(d/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x)
    rule4119 = ReplacementRule(pattern4119, replacement4119)
    pattern4120 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4120(f, b, d, a, x, e):
        rubi.append(4120)
        return Dist(S(1)/a, Int(sqrt(a + b/sin(e + f*x))/sqrt(d/sin(e + f*x)), x), x) - Dist(b/(a*d), Int(sqrt(d/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x)
    rule4120 = ReplacementRule(pattern4120, replacement4120)
    pattern4121 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons89, cons808)
    def replacement4121(f, b, d, a, n, x, e):
        rubi.append(4121)
        return Dist(S(1)/(S(2)*a*d*n), Int((d/cos(e + f*x))**(n + S(1))*Simp(S(2)*a*(n + S(1))/cos(e + f*x) - b*(S(2)*n + S(1)) + b*(S(2)*n + S(3))/cos(e + f*x)**S(2), x)/sqrt(a + b/cos(e + f*x)), x), x) - Simp((d/cos(e + f*x))**(n + S(1))*sqrt(a + b/cos(e + f*x))*sin(e + f*x)/(a*d*f*n), x)
    rule4121 = ReplacementRule(pattern4121, replacement4121)
    pattern4122 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons89, cons808)
    def replacement4122(f, b, d, a, n, x, e):
        rubi.append(4122)
        return Dist(S(1)/(S(2)*a*d*n), Int((d/sin(e + f*x))**(n + S(1))*Simp(S(2)*a*(n + S(1))/sin(e + f*x) - b*(S(2)*n + S(1)) + b*(S(2)*n + S(3))/sin(e + f*x)**S(2), x)/sqrt(a + b/sin(e + f*x)), x), x) + Simp((d/sin(e + f*x))**(n + S(1))*sqrt(a + b/sin(e + f*x))*cos(e + f*x)/(a*d*f*n), x)
    rule4122 = ReplacementRule(pattern4122, replacement4122)
    pattern4123 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons1586, cons1599)
    def replacement4123(f, b, d, a, n, x, e):
        rubi.append(4123)
        return Dist(S(1)/(S(2)*d*n), Int((d/cos(e + f*x))**(n + S(1))*Simp(a*b*(S(2)*n + S(-1)) + a*b*(S(2)*n + S(3))/cos(e + f*x)**S(2) + S(2)*(a**S(2)*(n + S(1)) + b**S(2)*n)/cos(e + f*x), x)/sqrt(a + b/cos(e + f*x)), x), x) - Simp(a*(d/cos(e + f*x))**n*sqrt(a + b/cos(e + f*x))*tan(e + f*x)/(f*n), x)
    rule4123 = ReplacementRule(pattern4123, replacement4123)
    pattern4124 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons87, cons1586, cons1599)
    def replacement4124(f, b, d, a, n, x, e):
        rubi.append(4124)
        return Dist(S(1)/(S(2)*d*n), Int((d/sin(e + f*x))**(n + S(1))*Simp(a*b*(S(2)*n + S(-1)) + a*b*(S(2)*n + S(3))/sin(e + f*x)**S(2) + S(2)*(a**S(2)*(n + S(1)) + b**S(2)*n)/sin(e + f*x), x)/sqrt(a + b/sin(e + f*x)), x), x) + Simp(a*(d/sin(e + f*x))**n*sqrt(a + b/sin(e + f*x))/(f*n*tan(e + f*x)), x)
    rule4124 = ReplacementRule(pattern4124, replacement4124)
    pattern4125 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1267, cons87, cons1598, cons1553, cons1600)
    def replacement4125(m, f, b, d, a, n, x, e):
        rubi.append(4125)
        return Dist(d**S(3)/(b*(m + n + S(-1))), Int((d/cos(e + f*x))**(n + S(-3))*(a + b/cos(e + f*x))**m*Simp(a*(n + S(-3)) - a*(n + S(-2))/cos(e + f*x)**S(2) + b*(m + n + S(-2))/cos(e + f*x), x), x), x) + Simp(d**S(3)*(d/cos(e + f*x))**(n + S(-3))*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + n + S(-1))), x)
    rule4125 = ReplacementRule(pattern4125, replacement4125)
    pattern4126 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1267, cons87, cons1598, cons1553, cons1600)
    def replacement4126(m, f, b, d, a, n, x, e):
        rubi.append(4126)
        return Dist(d**S(3)/(b*(m + n + S(-1))), Int((d/sin(e + f*x))**(n + S(-3))*(a + b/sin(e + f*x))**m*Simp(a*(n + S(-3)) - a*(n + S(-2))/sin(e + f*x)**S(2) + b*(m + n + S(-2))/sin(e + f*x), x), x), x) - Simp(d**S(3)*(d/sin(e + f*x))**(n + S(-3))*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + n + S(-1))*tan(e + f*x)), x)
    rule4126 = ReplacementRule(pattern4126, replacement4126)
    pattern4127 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons1357, cons1601, cons1519, cons1334)
    def replacement4127(m, f, b, d, a, n, x, e):
        rubi.append(4127)
        return Dist(d/(m + n + S(-1)), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(-2))*Simp(a*b*(n + S(-1)) + a*b*(S(2)*m + n + S(-2))/cos(e + f*x)**S(2) + (a**S(2)*(m + n + S(-1)) + b**S(2)*(m + n + S(-2)))/cos(e + f*x), x), x), x) + Simp(b*d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*(m + n + S(-1))), x)
    rule4127 = ReplacementRule(pattern4127, replacement4127)
    pattern4128 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons1357, cons1601, cons1519, cons1334)
    def replacement4128(m, f, b, d, a, n, x, e):
        rubi.append(4128)
        return Dist(d/(m + n + S(-1)), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(-2))*Simp(a*b*(n + S(-1)) + a*b*(S(2)*m + n + S(-2))/sin(e + f*x)**S(2) + (a**S(2)*(m + n + S(-1)) + b**S(2)*(m + n + S(-2)))/sin(e + f*x), x), x), x) - Simp(b*d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(-1))/(f*(m + n + S(-1))*tan(e + f*x)), x)
    rule4128 = ReplacementRule(pattern4128, replacement4128)
    pattern4129 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons1602, cons1603, cons1519, cons1553)
    def replacement4129(m, f, b, d, a, n, x, e):
        rubi.append(4129)
        return Dist(d**S(2)/(b*(m + n + S(-1))), Int((d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**(m + S(-1))*Simp(a*b*m/cos(e + f*x)**S(2) + a*b*(n + S(-2)) + b**S(2)*(m + n + S(-2))/cos(e + f*x), x), x), x) + Simp(d**S(2)*(d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + n + S(-1))), x)
    rule4129 = ReplacementRule(pattern4129, replacement4129)
    pattern4130 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons93, cons1602, cons1603, cons1519, cons1553)
    def replacement4130(m, f, b, d, a, n, x, e):
        rubi.append(4130)
        return Dist(d**S(2)/(b*(m + n + S(-1))), Int((d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**(m + S(-1))*Simp(a*b*m/sin(e + f*x)**S(2) + a*b*(n + S(-2)) + b**S(2)*(m + n + S(-2))/sin(e + f*x), x), x), x) - Simp(d**S(2)*(d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**m/(f*(m + n + S(-1))*tan(e + f*x)), x)
    rule4130 = ReplacementRule(pattern4130, replacement4130)
    pattern4131 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4131(f, b, d, a, x, e):
        rubi.append(4131)
        return Dist(a, Int(sqrt(a + b/cos(e + f*x))/sqrt(d/cos(e + f*x)), x), x) + Dist(b/d, Int(sqrt(d/cos(e + f*x))*sqrt(a + b/cos(e + f*x)), x), x)
    rule4131 = ReplacementRule(pattern4131, replacement4131)
    pattern4132 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement4132(f, b, d, a, x, e):
        rubi.append(4132)
        return Dist(a, Int(sqrt(a + b/sin(e + f*x))/sqrt(d/sin(e + f*x)), x), x) + Dist(b/d, Int(sqrt(d/sin(e + f*x))*sqrt(a + b/sin(e + f*x)), x), x)
    rule4132 = ReplacementRule(pattern4132, replacement4132)
    pattern4133 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons62)
    def replacement4133(m, f, b, d, a, n, x, e):
        rubi.append(4133)
        return Dist(a, Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-1)), x), x) + Dist(b/d, Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**(m + S(-1)), x), x)
    rule4133 = ReplacementRule(pattern4133, replacement4133)
    pattern4134 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons62)
    def replacement4134(m, f, b, d, a, n, x, e):
        rubi.append(4134)
        return Dist(a, Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-1)), x), x) + Dist(b/d, Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**(m + S(-1)), x), x)
    rule4134 = ReplacementRule(pattern4134, replacement4134)
    pattern4135 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1604)
    def replacement4135(m, f, b, d, a, n, x, e):
        rubi.append(4135)
        return Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m, x)
    rule4135 = ReplacementRule(pattern4135, replacement4135)
    pattern4136 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1604)
    def replacement4136(m, f, b, d, a, n, x, e):
        rubi.append(4136)
        return Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m, x)
    rule4136 = ReplacementRule(pattern4136, replacement4136)
    pattern4137 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons17)
    def replacement4137(p, m, f, b, g, a, x, e):
        rubi.append(4137)
        return Int((g*sin(e + f*x))**p*(a*cos(e + f*x) + b)**m*cos(e + f*x)**(-m), x)
    rule4137 = ReplacementRule(pattern4137, replacement4137)
    pattern4138 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons17)
    def replacement4138(p, m, f, b, g, a, x, e):
        rubi.append(4138)
        return Int((g*cos(e + f*x))**p*(a*sin(e + f*x) + b)**m*sin(e + f*x)**(-m), x)
    rule4138 = ReplacementRule(pattern4138, replacement4138)
    pattern4139 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1274, cons1265)
    def replacement4139(p, m, f, b, a, x, e):
        rubi.append(4139)
        return Dist(b**(-p + S(1))/f, Subst(Int(x**(-p + S(-1))*(-a + b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2), x), x, S(1)/cos(e + f*x)), x)
    rule4139 = ReplacementRule(pattern4139, replacement4139)
    pattern4140 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1274, cons1265)
    def replacement4140(p, m, f, b, a, x, e):
        rubi.append(4140)
        return -Dist(b**(-p + S(1))/f, Subst(Int(x**(-p + S(-1))*(-a + b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2), x), x, S(1)/sin(e + f*x)), x)
    rule4140 = ReplacementRule(pattern4140, replacement4140)
    pattern4141 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1274, cons1267)
    def replacement4141(p, m, f, b, a, x, e):
        rubi.append(4141)
        return Dist(S(1)/f, Subst(Int(x**(-p + S(-1))*(a + b*x)**m*(x + S(-1))**(p/S(2) + S(-1)/2)*(x + S(1))**(p/S(2) + S(-1)/2), x), x, S(1)/cos(e + f*x)), x)
    rule4141 = ReplacementRule(pattern4141, replacement4141)
    pattern4142 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1274, cons1267)
    def replacement4142(p, m, f, b, a, x, e):
        rubi.append(4142)
        return -Dist(S(1)/f, Subst(Int(x**(-p + S(-1))*(a + b*x)**m*(x + S(-1))**(p/S(2) + S(-1)/2)*(x + S(1))**(p/S(2) + S(-1)/2), x), x, S(1)/sin(e + f*x)), x)
    rule4142 = ReplacementRule(pattern4142, replacement4142)
    pattern4143 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1605)
    def replacement4143(m, f, b, a, x, e):
        rubi.append(4143)
        return Dist(b*m, Int((a + b/cos(e + f*x))**(m + S(-1))/cos(e + f*x), x), x) - Simp((a + b/cos(e + f*x))**m/(f*tan(e + f*x)), x)
    rule4143 = ReplacementRule(pattern4143, replacement4143)
    pattern4144 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1605)
    def replacement4144(m, f, b, a, x, e):
        rubi.append(4144)
        return Dist(b*m, Int((a + b/sin(e + f*x))**(m + S(-1))/sin(e + f*x), x), x) + Simp((a + b/sin(e + f*x))**m*tan(e + f*x)/f, x)
    rule4144 = ReplacementRule(pattern4144, replacement4144)
    pattern4145 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1606)
    def replacement4145(p, m, f, b, g, a, x, e):
        rubi.append(4145)
        return Dist((a + b/cos(e + f*x))**FracPart(m)*(a*cos(e + f*x) + b)**(-FracPart(m))*cos(e + f*x)**FracPart(m), Int((g*sin(e + f*x))**p*(a*cos(e + f*x) + b)**m*cos(e + f*x)**(-m), x), x)
    rule4145 = ReplacementRule(pattern4145, replacement4145)
    pattern4146 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1606)
    def replacement4146(p, m, f, b, g, a, x, e):
        rubi.append(4146)
        return Dist((a + b/sin(e + f*x))**FracPart(m)*(a*sin(e + f*x) + b)**(-FracPart(m))*sin(e + f*x)**FracPart(m), Int((g*cos(e + f*x))**p*(a*sin(e + f*x) + b)**m*sin(e + f*x)**(-m), x), x)
    rule4146 = ReplacementRule(pattern4146, replacement4146)
    pattern4147 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1308)
    def replacement4147(p, m, f, b, g, a, x, e):
        rubi.append(4147)
        return Int((g*sin(e + f*x))**p*(a + b/cos(e + f*x))**m, x)
    rule4147 = ReplacementRule(pattern4147, replacement4147)
    pattern4148 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1308)
    def replacement4148(p, m, f, b, g, a, x, e):
        rubi.append(4148)
        return Int((g*cos(e + f*x))**p*(a + b/sin(e + f*x))**m, x)
    rule4148 = ReplacementRule(pattern4148, replacement4148)
    pattern4149 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons147)
    def replacement4149(p, m, f, b, g, a, x, e):
        rubi.append(4149)
        return Dist((g/sin(e + f*x))**p*(g*sin(e + f*x))**p, Int((g*sin(e + f*x))**(-p)*(a + b/cos(e + f*x))**m, x), x)
    rule4149 = ReplacementRule(pattern4149, replacement4149)
    pattern4150 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons147)
    def replacement4150(p, m, f, b, g, a, x, e):
        rubi.append(4150)
        return Dist((g/cos(e + f*x))**p*(g*cos(e + f*x))**p, Int((g*cos(e + f*x))**(-p)*(a + b/sin(e + f*x))**m, x), x)
    rule4150 = ReplacementRule(pattern4150, replacement4150)
    pattern4151 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1228, cons1265, cons85)
    def replacement4151(m, b, d, c, n, a, x):
        rubi.append(4151)
        return -Dist(a**(-m + n + S(1))*b**(-n)/d, Subst(Int(x**(-m - n)*(a - b*x)**(m/S(2) + S(-1)/2)*(a + b*x)**(m/S(2) + n + S(-1)/2), x), x, cos(c + d*x)), x)
    rule4151 = ReplacementRule(pattern4151, replacement4151)
    pattern4152 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1))*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1228, cons1265, cons85)
    def replacement4152(m, b, d, c, n, a, x):
        rubi.append(4152)
        return Dist(a**(-m + n + S(1))*b**(-n)/d, Subst(Int(x**(-m - n)*(a - b*x)**(m/S(2) + S(-1)/2)*(a + b*x)**(m/S(2) + n + S(-1)/2), x), x, sin(c + d*x)), x)
    rule4152 = ReplacementRule(pattern4152, replacement4152)
    pattern4153 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*tan(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1228, cons1265, cons23)
    def replacement4153(m, b, d, c, a, n, x):
        rubi.append(4153)
        return Dist(b**(-m + S(1))/d, Subst(Int((-a + b*x)**(m/S(2) + S(-1)/2)*(a + b*x)**(m/S(2) + n + S(-1)/2)/x, x), x, S(1)/cos(c + d*x)), x)
    rule4153 = ReplacementRule(pattern4153, replacement4153)
    pattern4154 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1228, cons1265, cons23)
    def replacement4154(m, b, d, c, a, n, x):
        rubi.append(4154)
        return -Dist(b**(-m + S(1))/d, Subst(Int((-a + b*x)**(m/S(2) + S(-1)/2)*(a + b*x)**(m/S(2) + n + S(-1)/2)/x, x), x, S(1)/sin(c + d*x)), x)
    rule4154 = ReplacementRule(pattern4154, replacement4154)
    pattern4155 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons166)
    def replacement4155(m, b, d, c, a, x, e):
        rubi.append(4155)
        return -Dist(e**S(2)/m, Int((e*tan(c + d*x))**(m + S(-2))*(a*m + b*(m + S(-1))/cos(c + d*x)), x), x) + Simp(e*(e*tan(c + d*x))**(m + S(-1))*(a*m + b*(m + S(-1))/cos(c + d*x))/(d*m*(m + S(-1))), x)
    rule4155 = ReplacementRule(pattern4155, replacement4155)
    pattern4156 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons166)
    def replacement4156(m, b, d, c, a, x, e):
        rubi.append(4156)
        return -Dist(e**S(2)/m, Int((e/tan(c + d*x))**(m + S(-2))*(a*m + b*(m + S(-1))/sin(c + d*x)), x), x) - Simp(e*(e/tan(c + d*x))**(m + S(-1))*(a*m + b*(m + S(-1))/sin(c + d*x))/(d*m*(m + S(-1))), x)
    rule4156 = ReplacementRule(pattern4156, replacement4156)
    pattern4157 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons94)
    def replacement4157(m, b, d, c, a, x, e):
        rubi.append(4157)
        return -Dist(S(1)/(e**S(2)*(m + S(1))), Int((e*tan(c + d*x))**(m + S(2))*(a*(m + S(1)) + b*(m + S(2))/cos(c + d*x)), x), x) + Simp((e*tan(c + d*x))**(m + S(1))*(a + b/cos(c + d*x))/(d*e*(m + S(1))), x)
    rule4157 = ReplacementRule(pattern4157, replacement4157)
    pattern4158 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons94)
    def replacement4158(m, b, d, c, a, x, e):
        rubi.append(4158)
        return -Dist(S(1)/(e**S(2)*(m + S(1))), Int((e/tan(c + d*x))**(m + S(2))*(a*(m + S(1)) + b*(m + S(2))/sin(c + d*x)), x), x) - Simp((e/tan(c + d*x))**(m + S(1))*(a + b/sin(c + d*x))/(d*e*(m + S(1))), x)
    rule4158 = ReplacementRule(pattern4158, replacement4158)
    pattern4159 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))/tan(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons1264)
    def replacement4159(b, d, c, a, x):
        rubi.append(4159)
        return Int((a*cos(c + d*x) + b)/sin(c + d*x), x)
    rule4159 = ReplacementRule(pattern4159, replacement4159)
    pattern4160 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))*tan(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons1264)
    def replacement4160(b, d, c, a, x):
        rubi.append(4160)
        return Int((a*sin(c + d*x) + b)/cos(c + d*x), x)
    rule4160 = ReplacementRule(pattern4160, replacement4160)
    pattern4161 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1507)
    def replacement4161(m, b, d, c, a, x, e):
        rubi.append(4161)
        return Dist(a, Int((e*tan(c + d*x))**m, x), x) + Dist(b, Int((e*tan(c + d*x))**m/cos(c + d*x), x), x)
    rule4161 = ReplacementRule(pattern4161, replacement4161)
    pattern4162 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1507)
    def replacement4162(m, b, d, c, a, x, e):
        rubi.append(4162)
        return Dist(a, Int((e/tan(c + d*x))**m, x), x) + Dist(b, Int((e/tan(c + d*x))**m/sin(c + d*x), x), x)
    rule4162 = ReplacementRule(pattern4162, replacement4162)
    pattern4163 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*tan(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1228, cons1267)
    def replacement4163(m, b, d, c, a, n, x):
        rubi.append(4163)
        return Dist((S(-1))**(m/S(2) + S(-1)/2)*b**(-m + S(1))/d, Subst(Int((a + x)**n*(b**S(2) - x**S(2))**(m/S(2) + S(-1)/2)/x, x), x, b/cos(c + d*x)), x)
    rule4163 = ReplacementRule(pattern4163, replacement4163)
    pattern4164 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1228, cons1267)
    def replacement4164(m, b, d, c, a, n, x):
        rubi.append(4164)
        return -Dist((S(-1))**(m/S(2) + S(-1)/2)*b**(-m + S(1))/d, Subst(Int((a + x)**n*(b**S(2) - x**S(2))**(m/S(2) + S(-1)/2)/x, x), x, b/sin(c + d*x)), x)
    rule4164 = ReplacementRule(pattern4164, replacement4164)
    pattern4165 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons148)
    def replacement4165(m, b, d, c, a, n, x, e):
        rubi.append(4165)
        return Int(ExpandIntegrand((e*tan(c + d*x))**m, (a + b/cos(c + d*x))**n, x), x)
    rule4165 = ReplacementRule(pattern4165, replacement4165)
    pattern4166 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons148)
    def replacement4166(m, b, d, c, a, n, x, e):
        rubi.append(4166)
        return Int(ExpandIntegrand((e/tan(c + d*x))**m, (a + b/sin(c + d*x))**n, x), x)
    rule4166 = ReplacementRule(pattern4166, replacement4166)
    pattern4167 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1265, cons1515, cons1607)
    def replacement4167(m, b, d, c, n, a, x):
        rubi.append(4167)
        return Dist(S(2)*a**(m/S(2) + n + S(1)/2)/d, Subst(Int(x**m*(a*x**S(2) + S(2))**(m/S(2) + n + S(-1)/2)/(a*x**S(2) + S(1)), x), x, tan(c + d*x)/sqrt(a + b/cos(c + d*x))), x)
    rule4167 = ReplacementRule(pattern4167, replacement4167)
    pattern4168 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1))*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1265, cons1515, cons1607)
    def replacement4168(m, b, d, c, n, a, x):
        rubi.append(4168)
        return Dist(-S(2)*a**(m/S(2) + n + S(1)/2)/d, Subst(Int(x**m*(a*x**S(2) + S(2))**(m/S(2) + n + S(-1)/2)/(a*x**S(2) + S(1)), x), x, S(1)/(sqrt(a + b/sin(c + d*x))*tan(c + d*x))), x)
    rule4168 = ReplacementRule(pattern4168, replacement4168)
    pattern4169 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1265, cons196)
    def replacement4169(m, b, d, c, a, n, x, e):
        rubi.append(4169)
        return Dist(a**(S(2)*n)*e**(-S(2)*n), Int((e*tan(c + d*x))**(m + S(2)*n)*(-a + b/cos(c + d*x))**(-n), x), x)
    rule4169 = ReplacementRule(pattern4169, replacement4169)
    pattern4170 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1265, cons196)
    def replacement4170(m, b, d, c, a, n, x, e):
        rubi.append(4170)
        return Dist(a**(S(2)*n)*e**(-S(2)*n), Int((e/tan(c + d*x))**(m + S(2)*n)*(-a + b/sin(c + d*x))**(-n), x), x)
    rule4170 = ReplacementRule(pattern4170, replacement4170)
    pattern4171 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1265, cons23)
    def replacement4171(m, b, d, c, a, n, x, e):
        rubi.append(4171)
        return Simp(S(2)**(m + n + S(1))*(a/(a + b/cos(c + d*x)))**(m + n + S(1))*(e*tan(c + d*x))**(m + S(1))*(a + b/cos(c + d*x))**n*AppellF1(m/S(2) + S(1)/2, m + n, S(1), m/S(2) + S(3)/2, -(a - b/cos(c + d*x))/(a + b/cos(c + d*x)), (a - b/cos(c + d*x))/(a + b/cos(c + d*x)))/(d*e*(m + S(1))), x)
    rule4171 = ReplacementRule(pattern4171, replacement4171)
    pattern4172 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1265, cons23)
    def replacement4172(m, b, d, c, a, n, x, e):
        rubi.append(4172)
        return -Simp(S(2)**(m + n + S(1))*(a/(a + b/sin(c + d*x)))**(m + n + S(1))*(e/tan(c + d*x))**(m + S(1))*(a + b/sin(c + d*x))**n*AppellF1(m/S(2) + S(1)/2, m + n, S(1), m/S(2) + S(3)/2, -(a - b/sin(c + d*x))/(a + b/sin(c + d*x)), (a - b/sin(c + d*x))/(a + b/sin(c + d*x)))/(d*e*(m + S(1))), x)
    rule4172 = ReplacementRule(pattern4172, replacement4172)
    pattern4173 = Pattern(Integral(sqrt(WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))/(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1267)
    def replacement4173(b, d, c, a, x, e):
        rubi.append(4173)
        return Dist(S(1)/a, Int(sqrt(e*tan(c + d*x)), x), x) - Dist(b/a, Int(sqrt(e*tan(c + d*x))/(a*cos(c + d*x) + b), x), x)
    rule4173 = ReplacementRule(pattern4173, replacement4173)
    pattern4174 = Pattern(Integral(sqrt(WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))/(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1267)
    def replacement4174(b, d, c, a, x, e):
        rubi.append(4174)
        return Dist(S(1)/a, Int(sqrt(e/tan(c + d*x)), x), x) - Dist(b/a, Int(sqrt(e/tan(c + d*x))/(a*sin(c + d*x) + b), x), x)
    rule4174 = ReplacementRule(pattern4174, replacement4174)
    pattern4175 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_/(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1267, cons1311)
    def replacement4175(m, b, d, c, a, x, e):
        rubi.append(4175)
        return -Dist(e**S(2)/b**S(2), Int((e*tan(c + d*x))**(m + S(-2))*(a - b/cos(c + d*x)), x), x) + Dist(e**S(2)*(a**S(2) - b**S(2))/b**S(2), Int((e*tan(c + d*x))**(m + S(-2))/(a + b/cos(c + d*x)), x), x)
    rule4175 = ReplacementRule(pattern4175, replacement4175)
    pattern4176 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_/(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1267, cons1311)
    def replacement4176(m, b, d, c, a, x, e):
        rubi.append(4176)
        return -Dist(e**S(2)/b**S(2), Int((e/tan(c + d*x))**(m + S(-2))*(a - b/sin(c + d*x)), x), x) + Dist(e**S(2)*(a**S(2) - b**S(2))/b**S(2), Int((e/tan(c + d*x))**(m + S(-2))/(a + b/sin(c + d*x)), x), x)
    rule4176 = ReplacementRule(pattern4176, replacement4176)
    pattern4177 = Pattern(Integral(S(1)/(sqrt(WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons1267)
    def replacement4177(b, d, c, a, x, e):
        rubi.append(4177)
        return Dist(S(1)/a, Int(S(1)/sqrt(e*tan(c + d*x)), x), x) - Dist(b/a, Int(S(1)/(sqrt(e*tan(c + d*x))*(a*cos(c + d*x) + b)), x), x)
    rule4177 = ReplacementRule(pattern4177, replacement4177)
    pattern4178 = Pattern(Integral(S(1)/(sqrt(WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons1267)
    def replacement4178(b, d, c, a, x, e):
        rubi.append(4178)
        return Dist(S(1)/a, Int(S(1)/sqrt(e/tan(c + d*x)), x), x) - Dist(b/a, Int(S(1)/(sqrt(e/tan(c + d*x))*(a*sin(c + d*x) + b)), x), x)
    rule4178 = ReplacementRule(pattern4178, replacement4178)
    pattern4179 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_/(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1267, cons1608)
    def replacement4179(m, b, d, c, a, x, e):
        rubi.append(4179)
        return Dist(b**S(2)/(e**S(2)*(a**S(2) - b**S(2))), Int((e*tan(c + d*x))**(m + S(2))/(a + b/cos(c + d*x)), x), x) + Dist(S(1)/(a**S(2) - b**S(2)), Int((e*tan(c + d*x))**m*(a - b/cos(c + d*x)), x), x)
    rule4179 = ReplacementRule(pattern4179, replacement4179)
    pattern4180 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_/(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1267, cons1608)
    def replacement4180(m, b, d, c, a, x, e):
        rubi.append(4180)
        return Dist(b**S(2)/(e**S(2)*(a**S(2) - b**S(2))), Int((e/tan(c + d*x))**(m + S(2))/(a + b/sin(c + d*x)), x), x) + Dist(S(1)/(a**S(2) - b**S(2)), Int((e/tan(c + d*x))**m*(a - b/sin(c + d*x)), x), x)
    rule4180 = ReplacementRule(pattern4180, replacement4180)
    pattern4181 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*tan(x_*WC('d', S(1)) + WC('c', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement4181(b, d, c, a, n, x):
        rubi.append(4181)
        return Int((S(-1) + cos(c + d*x)**(S(-2)))*(a + b/cos(c + d*x))**n, x)
    rule4181 = ReplacementRule(pattern4181, replacement4181)
    pattern4182 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_/tan(x_*WC('d', S(1)) + WC('c', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons1267)
    def replacement4182(b, d, c, a, n, x):
        rubi.append(4182)
        return Int((S(-1) + sin(c + d*x)**(S(-2)))*(a + b/sin(c + d*x))**n, x)
    rule4182 = ReplacementRule(pattern4182, replacement4182)
    pattern4183 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1267, cons148)
    def replacement4183(m, b, d, c, a, n, x, e):
        rubi.append(4183)
        return Int(ExpandIntegrand((e*tan(c + d*x))**m, (a + b/cos(c + d*x))**n, x), x)
    rule4183 = ReplacementRule(pattern4183, replacement4183)
    pattern4184 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_*(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1267, cons148)
    def replacement4184(m, b, d, c, a, n, x, e):
        rubi.append(4184)
        return Int(ExpandIntegrand((e/tan(c + d*x))**m, (a + b/sin(c + d*x))**n, x), x)
    rule4184 = ReplacementRule(pattern4184, replacement4184)
    pattern4185 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*tan(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1267, cons85, cons17, cons1609)
    def replacement4185(m, b, d, c, a, n, x):
        rubi.append(4185)
        return Int((a*cos(c + d*x) + b)**n*sin(c + d*x)**m*cos(c + d*x)**(-m - n), x)
    rule4185 = ReplacementRule(pattern4185, replacement4185)
    pattern4186 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1267, cons85, cons17, cons1609)
    def replacement4186(m, b, d, c, a, n, x):
        rubi.append(4186)
        return Int((a*sin(c + d*x) + b)**n*sin(c + d*x)**(-m - n)*cos(c + d*x)**m, x)
    rule4186 = ReplacementRule(pattern4186, replacement4186)
    pattern4187 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1580)
    def replacement4187(m, b, d, c, a, n, x, e):
        rubi.append(4187)
        return Int((e*tan(c + d*x))**m*(a + b/cos(c + d*x))**n, x)
    rule4187 = ReplacementRule(pattern4187, replacement4187)
    pattern4188 = Pattern(Integral((WC('e', S(1))/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1580)
    def replacement4188(m, b, d, a, n, c, x, e):
        rubi.append(4188)
        return Int((e/tan(c + d*x))**m*(a + b/sin(c + d*x))**n, x)
    rule4188 = ReplacementRule(pattern4188, replacement4188)
    pattern4189 = Pattern(Integral((WC('e', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**p_)**m_*(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons18)
    def replacement4189(p, m, b, d, c, n, a, x, e):
        rubi.append(4189)
        return Dist((e*tan(c + d*x))**(-m*p)*(e*tan(c + d*x)**p)**m, Int((e*tan(c + d*x))**(m*p)*(a + b/cos(c + d*x))**n, x), x)
    rule4189 = ReplacementRule(pattern4189, replacement4189)
    pattern4190 = Pattern(Integral(((S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**p_*WC('e', S(1)))**m_*(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons18)
    def replacement4190(p, m, b, d, c, n, a, x, e):
        rubi.append(4190)
        return Dist((e*(S(1)/tan(c + d*x))**p)**m*(e/tan(c + d*x))**(-m*p), Int((e/tan(c + d*x))**(m*p)*(a + b/sin(c + d*x))**n, x), x)
    rule4190 = ReplacementRule(pattern4190, replacement4190)
    pattern4191 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons62, cons196, cons1610)
    def replacement4191(m, f, b, d, a, c, n, x, e):
        rubi.append(4191)
        return Dist(c**n, Int(ExpandTrig((S(1) + d/(c*cos(e + f*x)))**n, (a + b/cos(e + f*x))**m, x), x), x)
    rule4191 = ReplacementRule(pattern4191, replacement4191)
    pattern4192 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons62, cons196, cons1610)
    def replacement4192(m, f, b, d, a, c, n, x, e):
        rubi.append(4192)
        return Dist(c**n, Int(ExpandTrig((S(1) + d/(c*sin(e + f*x)))**n, (a + b/sin(e + f*x))**m, x), x), x)
    rule4192 = ReplacementRule(pattern4192, replacement4192)
    pattern4193 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons17, cons87, cons1611)
    def replacement4193(m, f, b, d, a, n, c, x, e):
        rubi.append(4193)
        return Dist((-a*c)**m, Int((c + d/cos(e + f*x))**(-m + n)*tan(e + f*x)**(S(2)*m), x), x)
    rule4193 = ReplacementRule(pattern4193, replacement4193)
    pattern4194 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons17, cons87, cons1611)
    def replacement4194(m, f, b, d, a, n, c, x, e):
        rubi.append(4194)
        return Dist((-a*c)**m, Int((c + d/sin(e + f*x))**(-m + n)*(S(1)/tan(e + f*x))**(S(2)*m), x), x)
    rule4194 = ReplacementRule(pattern4194, replacement4194)
    pattern4195 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons70, cons1265, cons79)
    def replacement4195(m, f, b, d, a, c, x, e):
        rubi.append(4195)
        return Dist((-a*c)**(m + S(1)/2)*tan(e + f*x)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))), Int(tan(e + f*x)**(S(2)*m), x), x)
    rule4195 = ReplacementRule(pattern4195, replacement4195)
    pattern4196 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons70, cons1265, cons79)
    def replacement4196(m, f, b, d, a, c, x, e):
        rubi.append(4196)
        return Dist((-a*c)**(m + S(1)/2)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x)), Int((S(1)/tan(e + f*x))**(S(2)*m), x), x)
    rule4196 = ReplacementRule(pattern4196, replacement4196)
    pattern4197 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons87, cons1612)
    def replacement4197(f, b, d, a, n, c, x, e):
        rubi.append(4197)
        return Dist(c, Int(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))**(n + S(-1)), x), x) + Simp(-S(2)*a*c*(c + d/cos(e + f*x))**(n + S(-1))*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(-1))), x)
    rule4197 = ReplacementRule(pattern4197, replacement4197)
    pattern4198 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons87, cons1612)
    def replacement4198(f, b, d, a, n, c, x, e):
        rubi.append(4198)
        return Dist(c, Int(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))**(n + S(-1)), x), x) + Simp(S(2)*a*c*(c + d/sin(e + f*x))**(n + S(-1))/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(-1))*tan(e + f*x)), x)
    rule4198 = ReplacementRule(pattern4198, replacement4198)
    pattern4199 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons87, cons1590)
    def replacement4199(f, b, d, a, c, n, x, e):
        rubi.append(4199)
        return Dist(S(1)/c, Int(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))**(n + S(1)), x), x) + Simp(S(2)*a*(c + d/cos(e + f*x))**n*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(1))), x)
    rule4199 = ReplacementRule(pattern4199, replacement4199)
    pattern4200 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons87, cons1590)
    def replacement4200(f, b, d, a, c, n, x, e):
        rubi.append(4200)
        return Dist(S(1)/c, Int(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))**(n + S(1)), x), x) + Simp(-S(2)*a*(c + d/sin(e + f*x))**n/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(1))*tan(e + f*x)), x)
    rule4200 = ReplacementRule(pattern4200, replacement4200)
    pattern4201 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons87, cons1590)
    def replacement4201(f, b, d, a, n, c, x, e):
        rubi.append(4201)
        return Dist(a/c, Int(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))**(n + S(1)), x), x) + Simp(S(4)*a**S(2)*(c + d/cos(e + f*x))**n*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(1))), x)
    rule4201 = ReplacementRule(pattern4201, replacement4201)
    pattern4202 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons87, cons1590)
    def replacement4202(f, b, d, a, n, c, x, e):
        rubi.append(4202)
        return Dist(a/c, Int(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))**(n + S(1)), x), x) + Simp(-S(4)*a**S(2)*(c + d/sin(e + f*x))**n/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(1))*tan(e + f*x)), x)
    rule4202 = ReplacementRule(pattern4202, replacement4202)
    pattern4203 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons1613)
    def replacement4203(f, b, d, a, n, c, x, e):
        rubi.append(4203)
        return Dist(a, Int(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))**n, x), x) + Simp(S(2)*a**S(2)*(c + d/cos(e + f*x))**n*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(1))), x)
    rule4203 = ReplacementRule(pattern4203, replacement4203)
    pattern4204 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons1613)
    def replacement4204(f, b, d, a, n, c, x, e):
        rubi.append(4204)
        return Dist(a, Int(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))**n, x), x) + Simp(-S(2)*a**S(2)*(c + d/sin(e + f*x))**n/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(1))*tan(e + f*x)), x)
    rule4204 = ReplacementRule(pattern4204, replacement4204)
    pattern4205 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(5)/2)*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons87, cons1590)
    def replacement4205(f, b, d, a, n, c, x, e):
        rubi.append(4205)
        return Dist(a**S(2)/c**S(2), Int(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))**(n + S(2)), x), x) + Simp(S(8)*a**S(3)*(c + d/cos(e + f*x))**n*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(1))), x)
    rule4205 = ReplacementRule(pattern4205, replacement4205)
    pattern4206 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(5)/2)*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons87, cons1590)
    def replacement4206(f, b, d, a, n, c, x, e):
        rubi.append(4206)
        return Dist(a**S(2)/c**S(2), Int(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))**(n + S(2)), x), x) + Simp(-S(8)*a**S(3)*(c + d/sin(e + f*x))**n/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(1))*tan(e + f*x)), x)
    rule4206 = ReplacementRule(pattern4206, replacement4206)
    pattern4207 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons1304, cons1255)
    def replacement4207(m, f, b, d, a, c, n, x, e):
        rubi.append(4207)
        return Dist(a*c*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))), Subst(Int(x**(-m - n)*(a*x + b)**(m + S(-1)/2)*(c*x + d)**(n + S(-1)/2), x), x, cos(e + f*x)), x)
    rule4207 = ReplacementRule(pattern4207, replacement4207)
    pattern4208 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons1304, cons1255)
    def replacement4208(m, f, b, d, a, c, n, x, e):
        rubi.append(4208)
        return -Dist(a*c/(f*sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x)), Subst(Int(x**(-m - n)*(a*x + b)**(m + S(-1)/2)*(c*x + d)**(n + S(-1)/2), x), x, sin(e + f*x)), x)
    rule4208 = ReplacementRule(pattern4208, replacement4208)
    pattern4209 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265)
    def replacement4209(m, f, b, d, a, n, c, x, e):
        rubi.append(4209)
        return -Dist(a*c*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))), Subst(Int((a + b*x)**(m + S(-1)/2)*(c + d*x)**(n + S(-1)/2)/x, x), x, S(1)/cos(e + f*x)), x)
    rule4209 = ReplacementRule(pattern4209, replacement4209)
    pattern4210 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265)
    def replacement4210(m, f, b, d, a, n, c, x, e):
        rubi.append(4210)
        return Dist(a*c/(f*sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x)), Subst(Int((a + b*x)**(m + S(-1)/2)*(c + d*x)**(n + S(-1)/2)/x, x), x, S(1)/sin(e + f*x)), x)
    rule4210 = ReplacementRule(pattern4210, replacement4210)
    pattern4211 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70)
    def replacement4211(f, b, d, a, c, x, e):
        rubi.append(4211)
        return Dist(b*d, Int(cos(e + f*x)**(S(-2)), x), x) + Simp(a*c*x, x)
    rule4211 = ReplacementRule(pattern4211, replacement4211)
    pattern4212 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70)
    def replacement4212(f, b, d, a, c, x, e):
        rubi.append(4212)
        return Dist(b*d, Int(sin(e + f*x)**(S(-2)), x), x) + Simp(a*c*x, x)
    rule4212 = ReplacementRule(pattern4212, replacement4212)
    pattern4213 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1412)
    def replacement4213(f, b, d, a, c, x, e):
        rubi.append(4213)
        return Dist(b*d, Int(cos(e + f*x)**(S(-2)), x), x) + Dist(a*d + b*c, Int(S(1)/cos(e + f*x), x), x) + Simp(a*c*x, x)
    rule4213 = ReplacementRule(pattern4213, replacement4213)
    pattern4214 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1412)
    def replacement4214(f, b, d, a, c, x, e):
        rubi.append(4214)
        return Dist(b*d, Int(sin(e + f*x)**(S(-2)), x), x) + Dist(a*d + b*c, Int(S(1)/sin(e + f*x), x), x) + Simp(a*c*x, x)
    rule4214 = ReplacementRule(pattern4214, replacement4214)
    pattern4215 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement4215(f, b, d, a, c, x, e):
        rubi.append(4215)
        return Dist(c, Int(sqrt(a + b/cos(e + f*x)), x), x) + Dist(d, Int(sqrt(a + b/cos(e + f*x))/cos(e + f*x), x), x)
    rule4215 = ReplacementRule(pattern4215, replacement4215)
    pattern4216 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement4216(f, b, d, a, c, x, e):
        rubi.append(4216)
        return Dist(c, Int(sqrt(a + b/sin(e + f*x)), x), x) + Dist(d, Int(sqrt(a + b/sin(e + f*x))/sin(e + f*x), x), x)
    rule4216 = ReplacementRule(pattern4216, replacement4216)
    pattern4217 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement4217(f, b, d, a, c, x, e):
        rubi.append(4217)
        return Dist(a*c, Int(S(1)/sqrt(a + b/cos(e + f*x)), x), x) + Int((a*d + b*c + b*d/cos(e + f*x))/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x)
    rule4217 = ReplacementRule(pattern4217, replacement4217)
    pattern4218 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement4218(f, b, d, a, c, x, e):
        rubi.append(4218)
        return Dist(a*c, Int(S(1)/sqrt(a + b/sin(e + f*x)), x), x) + Int((a*d + b*c + b*d/sin(e + f*x))/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x)
    rule4218 = ReplacementRule(pattern4218, replacement4218)
    pattern4219 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons166, cons1265, cons515)
    def replacement4219(m, f, b, d, a, c, x, e):
        rubi.append(4219)
        return Dist(S(1)/m, Int((a + b/cos(e + f*x))**(m + S(-1))*Simp(a*c*m + (a*d*(S(2)*m + S(-1)) + b*c*m)/cos(e + f*x), x), x), x) + Simp(b*d*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*m), x)
    rule4219 = ReplacementRule(pattern4219, replacement4219)
    pattern4220 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons166, cons1265, cons515)
    def replacement4220(m, f, b, d, a, c, x, e):
        rubi.append(4220)
        return Dist(S(1)/m, Int((a + b/sin(e + f*x))**(m + S(-1))*Simp(a*c*m + (a*d*(S(2)*m + S(-1)) + b*c*m)/sin(e + f*x), x), x), x) - Simp(b*d*(a + b/sin(e + f*x))**(m + S(-1))/(f*m*tan(e + f*x)), x)
    rule4220 = ReplacementRule(pattern4220, replacement4220)
    pattern4221 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons166, cons1267, cons515)
    def replacement4221(m, f, b, d, a, c, x, e):
        rubi.append(4221)
        return Dist(S(1)/m, Int((a + b/cos(e + f*x))**(m + S(-2))*Simp(a**S(2)*c*m + b*(a*d*(S(2)*m + S(-1)) + b*c*m)/cos(e + f*x)**S(2) + (a**S(2)*d*m + S(2)*a*b*c*m + b**S(2)*d*(m + S(-1)))/cos(e + f*x), x), x), x) + Simp(b*d*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*m), x)
    rule4221 = ReplacementRule(pattern4221, replacement4221)
    pattern4222 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons166, cons1267, cons515)
    def replacement4222(m, f, b, d, a, c, x, e):
        rubi.append(4222)
        return Dist(S(1)/m, Int((a + b/sin(e + f*x))**(m + S(-2))*Simp(a**S(2)*c*m + b*(a*d*(S(2)*m + S(-1)) + b*c*m)/sin(e + f*x)**S(2) + (a**S(2)*d*m + S(2)*a*b*c*m + b**S(2)*d*(m + S(-1)))/sin(e + f*x), x), x), x) - Simp(b*d*(a + b/sin(e + f*x))**(m + S(-1))/(f*m*tan(e + f*x)), x)
    rule4222 = ReplacementRule(pattern4222, replacement4222)
    pattern4223 = Pattern(Integral((c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement4223(f, b, d, a, c, x, e):
        rubi.append(4223)
        return -Dist((-a*d + b*c)/a, Int(S(1)/((a + b/cos(e + f*x))*cos(e + f*x)), x), x) + Simp(c*x/a, x)
    rule4223 = ReplacementRule(pattern4223, replacement4223)
    pattern4224 = Pattern(Integral((c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement4224(f, b, d, a, c, x, e):
        rubi.append(4224)
        return -Dist((-a*d + b*c)/a, Int(S(1)/((a + b/sin(e + f*x))*sin(e + f*x)), x), x) + Simp(c*x/a, x)
    rule4224 = ReplacementRule(pattern4224, replacement4224)
    pattern4225 = Pattern(Integral((c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement4225(f, b, d, a, c, x, e):
        rubi.append(4225)
        return Dist(c/a, Int(sqrt(a + b/cos(e + f*x)), x), x) - Dist((-a*d + b*c)/a, Int(S(1)/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4225 = ReplacementRule(pattern4225, replacement4225)
    pattern4226 = Pattern(Integral((c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement4226(f, b, d, a, c, x, e):
        rubi.append(4226)
        return Dist(c/a, Int(sqrt(a + b/sin(e + f*x)), x), x) - Dist((-a*d + b*c)/a, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4226 = ReplacementRule(pattern4226, replacement4226)
    pattern4227 = Pattern(Integral((c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement4227(f, b, d, a, c, x, e):
        rubi.append(4227)
        return Dist(c, Int(S(1)/sqrt(a + b/cos(e + f*x)), x), x) + Dist(d, Int(S(1)/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4227 = ReplacementRule(pattern4227, replacement4227)
    pattern4228 = Pattern(Integral((c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement4228(f, b, d, a, c, x, e):
        rubi.append(4228)
        return Dist(c, Int(S(1)/sqrt(a + b/sin(e + f*x)), x), x) + Dist(d, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4228 = ReplacementRule(pattern4228, replacement4228)
    pattern4229 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons94, cons1265, cons515)
    def replacement4229(m, f, b, d, a, c, x, e):
        rubi.append(4229)
        return Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(a*c*(S(2)*m + S(1)) - (m + S(1))*(-a*d + b*c)/cos(e + f*x), x), x), x) + Simp((a + b/cos(e + f*x))**m*(-a*d + b*c)*tan(e + f*x)/(b*f*(S(2)*m + S(1))), x)
    rule4229 = ReplacementRule(pattern4229, replacement4229)
    pattern4230 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons94, cons1265, cons515)
    def replacement4230(m, f, b, d, a, c, x, e):
        rubi.append(4230)
        return Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(a*c*(S(2)*m + S(1)) - (m + S(1))*(-a*d + b*c)/sin(e + f*x), x), x), x) - Simp((a + b/sin(e + f*x))**m*(-a*d + b*c)/(b*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4230 = ReplacementRule(pattern4230, replacement4230)
    pattern4231 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons94, cons1267, cons515)
    def replacement4231(m, f, b, d, a, c, x, e):
        rubi.append(4231)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(-a*(m + S(1))*(-a*d + b*c)/cos(e + f*x) + b*(m + S(2))*(-a*d + b*c)/cos(e + f*x)**S(2) + c*(a**S(2) - b**S(2))*(m + S(1)), x), x), x) - Simp(b*(a + b/cos(e + f*x))**(m + S(1))*(-a*d + b*c)*tan(e + f*x)/(a*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4231 = ReplacementRule(pattern4231, replacement4231)
    pattern4232 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons31, cons94, cons1267, cons515)
    def replacement4232(m, f, b, d, a, c, x, e):
        rubi.append(4232)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(-a*(m + S(1))*(-a*d + b*c)/sin(e + f*x) + b*(m + S(2))*(-a*d + b*c)/sin(e + f*x)**S(2) + c*(a**S(2) - b**S(2))*(m + S(1)), x), x), x) + Simp(b*(a + b/sin(e + f*x))**(m + S(1))*(-a*d + b*c)/(a*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4232 = ReplacementRule(pattern4232, replacement4232)
    pattern4233 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons77)
    def replacement4233(m, f, b, d, a, c, x, e):
        rubi.append(4233)
        return Dist(c, Int((a + b/cos(e + f*x))**m, x), x) + Dist(d, Int((a + b/cos(e + f*x))**m/cos(e + f*x), x), x)
    rule4233 = ReplacementRule(pattern4233, replacement4233)
    pattern4234 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons77)
    def replacement4234(m, f, b, d, a, c, x, e):
        rubi.append(4234)
        return Dist(c, Int((a + b/sin(e + f*x))**m, x), x) + Dist(d, Int((a + b/sin(e + f*x))**m/sin(e + f*x), x), x)
    rule4234 = ReplacementRule(pattern4234, replacement4234)
    pattern4235 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4235(f, b, d, a, c, x, e):
        rubi.append(4235)
        return Dist(S(1)/c, Int(sqrt(a + b/cos(e + f*x)), x), x) - Dist(d/c, Int(sqrt(a + b/cos(e + f*x))/((c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4235 = ReplacementRule(pattern4235, replacement4235)
    pattern4236 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4236(f, b, d, a, c, x, e):
        rubi.append(4236)
        return Dist(S(1)/c, Int(sqrt(a + b/sin(e + f*x)), x), x) - Dist(d/c, Int(sqrt(a + b/sin(e + f*x))/((c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4236 = ReplacementRule(pattern4236, replacement4236)
    pattern4237 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4237(f, b, d, a, c, x, e):
        rubi.append(4237)
        return Dist(a/c, Int(S(1)/sqrt(a + b/cos(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(S(1)/(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4237 = ReplacementRule(pattern4237, replacement4237)
    pattern4238 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4238(f, b, d, a, c, x, e):
        rubi.append(4238)
        return Dist(a/c, Int(S(1)/sqrt(a + b/sin(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(S(1)/(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4238 = ReplacementRule(pattern4238, replacement4238)
    pattern4239 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4239(f, b, d, a, c, x, e):
        rubi.append(4239)
        return Dist(a/c, Int(sqrt(a + b/cos(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(sqrt(a + b/cos(e + f*x))/((c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4239 = ReplacementRule(pattern4239, replacement4239)
    pattern4240 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4240(f, b, d, a, c, x, e):
        rubi.append(4240)
        return Dist(a/c, Int(sqrt(a + b/sin(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(sqrt(a + b/sin(e + f*x))/((c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4240 = ReplacementRule(pattern4240, replacement4240)
    pattern4241 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4241(f, b, d, a, c, x, e):
        rubi.append(4241)
        return Dist(S(1)/(c*d), Int((a**S(2)*d + b**S(2)*c/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x) - Dist((-a*d + b*c)**S(2)/(c*d), Int(S(1)/(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4241 = ReplacementRule(pattern4241, replacement4241)
    pattern4242 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4242(f, b, d, a, c, x, e):
        rubi.append(4242)
        return Dist(S(1)/(c*d), Int((a**S(2)*d + b**S(2)*c/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x) - Dist((-a*d + b*c)**S(2)/(c*d), Int(S(1)/(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4242 = ReplacementRule(pattern4242, replacement4242)
    pattern4243 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4243(f, b, d, a, c, x, e):
        rubi.append(4243)
        return Dist(S(1)/(c*(-a*d + b*c)), Int((-a*d + b*c - b*d/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x) + Dist(d**S(2)/(c*(-a*d + b*c)), Int(sqrt(a + b/cos(e + f*x))/((c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4243 = ReplacementRule(pattern4243, replacement4243)
    pattern4244 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4244(f, b, d, a, c, x, e):
        rubi.append(4244)
        return Dist(S(1)/(c*(-a*d + b*c)), Int((-a*d + b*c - b*d/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x) + Dist(d**S(2)/(c*(-a*d + b*c)), Int(sqrt(a + b/sin(e + f*x))/((c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4244 = ReplacementRule(pattern4244, replacement4244)
    pattern4245 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement4245(f, b, d, a, c, x, e):
        rubi.append(4245)
        return Dist(S(1)/c, Int(S(1)/sqrt(a + b/cos(e + f*x)), x), x) - Dist(d/c, Int(S(1)/(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4245 = ReplacementRule(pattern4245, replacement4245)
    pattern4246 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement4246(f, b, d, a, c, x, e):
        rubi.append(4246)
        return Dist(S(1)/c, Int(S(1)/sqrt(a + b/sin(e + f*x)), x), x) - Dist(d/c, Int(S(1)/(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4246 = ReplacementRule(pattern4246, replacement4246)
    pattern4247 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement4247(f, b, d, a, c, x, e):
        rubi.append(4247)
        return Dist(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))/tan(e + f*x), Int(tan(e + f*x), x), x)
    rule4247 = ReplacementRule(pattern4247, replacement4247)
    pattern4248 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement4248(f, b, d, a, c, x, e):
        rubi.append(4248)
        return Dist(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x), Int(S(1)/tan(e + f*x), x), x)
    rule4248 = ReplacementRule(pattern4248, replacement4248)
    pattern4249 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement4249(f, b, d, a, c, x, e):
        rubi.append(4249)
        return Dist(c, Int(sqrt(a + b/cos(e + f*x))/sqrt(c + d/cos(e + f*x)), x), x) + Dist(d, Int(sqrt(a + b/cos(e + f*x))/(sqrt(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4249 = ReplacementRule(pattern4249, replacement4249)
    pattern4250 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement4250(f, b, d, a, c, x, e):
        rubi.append(4250)
        return Dist(c, Int(sqrt(a + b/sin(e + f*x))/sqrt(c + d/sin(e + f*x)), x), x) + Dist(d, Int(sqrt(a + b/sin(e + f*x))/(sqrt(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4250 = ReplacementRule(pattern4250, replacement4250)
    pattern4251 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement4251(f, b, d, a, c, x, e):
        rubi.append(4251)
        return Dist(S(1)/c, Int(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x)), x), x) - Dist(d/c, Int(sqrt(a + b/cos(e + f*x))/(sqrt(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4251 = ReplacementRule(pattern4251, replacement4251)
    pattern4252 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement4252(f, b, d, a, c, x, e):
        rubi.append(4252)
        return Dist(S(1)/c, Int(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x)), x), x) - Dist(d/c, Int(sqrt(a + b/sin(e + f*x))/(sqrt(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4252 = ReplacementRule(pattern4252, replacement4252)
    pattern4253 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement4253(f, b, d, a, c, x, e):
        rubi.append(4253)
        return Dist(S(2)*a/f, Subst(Int(S(1)/(a*c*x**S(2) + S(1)), x), x, tan(e + f*x)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x)))), x)
    rule4253 = ReplacementRule(pattern4253, replacement4253)
    pattern4254 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement4254(f, b, d, a, c, x, e):
        rubi.append(4254)
        return Dist(-S(2)*a/f, Subst(Int(S(1)/(a*c*x**S(2) + S(1)), x), x, S(1)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x))), x)
    rule4254 = ReplacementRule(pattern4254, replacement4254)
    pattern4255 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1322)
    def replacement4255(f, b, d, a, c, x, e):
        rubi.append(4255)
        return Dist(a/c, Int(sqrt(c + d/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(S(1)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4255 = ReplacementRule(pattern4255, replacement4255)
    pattern4256 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1322)
    def replacement4256(f, b, d, a, c, x, e):
        rubi.append(4256)
        return Dist(a/c, Int(sqrt(c + d/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4256 = ReplacementRule(pattern4256, replacement4256)
    pattern4257 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4257(f, b, d, a, c, x, e):
        rubi.append(4257)
        return Simp(-S(2)*sqrt((S(1) + S(1)/cos(e + f*x))*(-a*d + b*c)/((a + b/cos(e + f*x))*(c - d)))*sqrt(-(S(1) - S(1)/cos(e + f*x))*(-a*d + b*c)/((a + b/cos(e + f*x))*(c + d)))*(a + b/cos(e + f*x))*EllipticPi(a*(c + d)/(c*(a + b)), asin(sqrt(c + d/cos(e + f*x))*Rt((a + b)/(c + d), S(2))/sqrt(a + b/cos(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))/(c*f*Rt((a + b)/(c + d), S(2))*tan(e + f*x)), x)
    rule4257 = ReplacementRule(pattern4257, replacement4257)
    pattern4258 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4258(f, b, d, a, c, x, e):
        rubi.append(4258)
        return Simp(S(2)*sqrt((S(1) + S(1)/sin(e + f*x))*(-a*d + b*c)/((a + b/sin(e + f*x))*(c - d)))*sqrt(-(S(1) - S(1)/sin(e + f*x))*(-a*d + b*c)/((a + b/sin(e + f*x))*(c + d)))*(a + b/sin(e + f*x))*EllipticPi(a*(c + d)/(c*(a + b)), asin(sqrt(c + d/sin(e + f*x))*Rt((a + b)/(c + d), S(2))/sqrt(a + b/sin(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))*tan(e + f*x)/(c*f*Rt((a + b)/(c + d), S(2))), x)
    rule4258 = ReplacementRule(pattern4258, replacement4258)
    pattern4259 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement4259(f, b, d, a, c, x, e):
        rubi.append(4259)
        return Dist(tan(e + f*x)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))), Int(S(1)/tan(e + f*x), x), x)
    rule4259 = ReplacementRule(pattern4259, replacement4259)
    pattern4260 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement4260(f, b, d, a, c, x, e):
        rubi.append(4260)
        return Dist(S(1)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x)), Int(tan(e + f*x), x), x)
    rule4260 = ReplacementRule(pattern4260, replacement4260)
    pattern4261 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement4261(f, b, d, a, c, x, e):
        rubi.append(4261)
        return Dist(S(1)/a, Int(sqrt(a + b/cos(e + f*x))/sqrt(c + d/cos(e + f*x)), x), x) - Dist(b/a, Int(S(1)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4261 = ReplacementRule(pattern4261, replacement4261)
    pattern4262 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement4262(f, b, d, a, c, x, e):
        rubi.append(4262)
        return Dist(S(1)/a, Int(sqrt(a + b/sin(e + f*x))/sqrt(c + d/sin(e + f*x)), x), x) - Dist(b/a, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4262 = ReplacementRule(pattern4262, replacement4262)
    pattern4263 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1323)
    def replacement4263(f, b, d, a, c, x, e):
        rubi.append(4263)
        return Dist(S(1)/c, Int(sqrt(a + b/cos(e + f*x))/sqrt(c + d/cos(e + f*x)), x), x) - Dist(d/c, Int(sqrt(a + b/cos(e + f*x))/((c + d/cos(e + f*x))**(S(3)/2)*cos(e + f*x)), x), x)
    rule4263 = ReplacementRule(pattern4263, replacement4263)
    pattern4264 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1323)
    def replacement4264(f, b, d, a, c, x, e):
        rubi.append(4264)
        return Dist(S(1)/c, Int(sqrt(a + b/sin(e + f*x))/sqrt(c + d/sin(e + f*x)), x), x) - Dist(d/c, Int(sqrt(a + b/sin(e + f*x))/((c + d/sin(e + f*x))**(S(3)/2)*sin(e + f*x)), x), x)
    rule4264 = ReplacementRule(pattern4264, replacement4264)
    pattern4265 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1265, cons1323, cons1304)
    def replacement4265(m, f, b, d, a, n, c, x, e):
        rubi.append(4265)
        return -Dist(a**S(2)*tan(e + f*x)/(f*sqrt(a - b/cos(e + f*x))*sqrt(a + b/cos(e + f*x))), Subst(Int((a + b*x)**(m + S(-1)/2)*(c + d*x)**n/(x*sqrt(a - b*x)), x), x, S(1)/cos(e + f*x)), x)
    rule4265 = ReplacementRule(pattern4265, replacement4265)
    pattern4266 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1265, cons1323, cons1304)
    def replacement4266(m, f, b, d, a, n, c, x, e):
        rubi.append(4266)
        return Dist(a**S(2)*cos(e + f*x)/(f*sqrt(a - b/sin(e + f*x))*sqrt(a + b/sin(e + f*x))), Subst(Int((a + b*x)**(m + S(-1)/2)*(c + d*x)**n/(x*sqrt(a - b*x)), x), x, S(1)/sin(e + f*x)), x)
    rule4266 = ReplacementRule(pattern4266, replacement4266)
    pattern4267 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons17, cons85, cons1614)
    def replacement4267(m, f, b, d, a, c, n, x, e):
        rubi.append(4267)
        return Int((a*cos(e + f*x) + b)**m*(c*cos(e + f*x) + d)**n*cos(e + f*x)**(-m - n), x)
    rule4267 = ReplacementRule(pattern4267, replacement4267)
    pattern4268 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons17, cons85, cons1614)
    def replacement4268(m, f, b, d, a, c, n, x, e):
        rubi.append(4268)
        return Int((a*sin(e + f*x) + b)**m*(c*sin(e + f*x) + d)**n*sin(e + f*x)**(-m - n), x)
    rule4268 = ReplacementRule(pattern4268, replacement4268)
    pattern4269 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons79, cons80, cons1614)
    def replacement4269(m, f, b, d, a, c, n, x, e):
        rubi.append(4269)
        return Dist(sqrt(a + b/cos(e + f*x))*sqrt(c*cos(e + f*x) + d)/(sqrt(c + d/cos(e + f*x))*sqrt(a*cos(e + f*x) + b)), Int((a*cos(e + f*x) + b)**m*(c*cos(e + f*x) + d)**n*cos(e + f*x)**(-m - n), x), x)
    rule4269 = ReplacementRule(pattern4269, replacement4269)
    pattern4270 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons79, cons80, cons1614)
    def replacement4270(m, f, b, d, a, c, n, x, e):
        rubi.append(4270)
        return Dist(sqrt(a + b/sin(e + f*x))*sqrt(c*sin(e + f*x) + d)/(sqrt(c + d/sin(e + f*x))*sqrt(a*sin(e + f*x) + b)), Int((a*sin(e + f*x) + b)**m*(c*sin(e + f*x) + d)**n*sin(e + f*x)**(-m - n), x), x)
    rule4270 = ReplacementRule(pattern4270, replacement4270)
    pattern4271 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1255, cons77)
    def replacement4271(m, f, b, d, a, c, n, x, e):
        rubi.append(4271)
        return Dist((a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**n*(a*cos(e + f*x) + b)**(-m)*(c*cos(e + f*x) + d)**(-n)*cos(e + f*x)**(m + n), Int((a*cos(e + f*x) + b)**m*(c*cos(e + f*x) + d)**n*cos(e + f*x)**(-m - n), x), x)
    rule4271 = ReplacementRule(pattern4271, replacement4271)
    pattern4272 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1255, cons77)
    def replacement4272(m, f, b, d, a, c, n, x, e):
        rubi.append(4272)
        return Dist((a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**n*(a*sin(e + f*x) + b)**(-m)*(c*sin(e + f*x) + d)**(-n)*sin(e + f*x)**(m + n), Int((a*sin(e + f*x) + b)**m*(c*sin(e + f*x) + d)**n*sin(e + f*x)**(-m - n), x), x)
    rule4272 = ReplacementRule(pattern4272, replacement4272)
    pattern4273 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons148)
    def replacement4273(m, f, b, d, a, c, n, x, e):
        rubi.append(4273)
        return Int(ExpandTrig((a + b/cos(e + f*x))**m, (c + d/cos(e + f*x))**n, x), x)
    rule4273 = ReplacementRule(pattern4273, replacement4273)
    pattern4274 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons148)
    def replacement4274(m, f, b, d, a, c, n, x, e):
        rubi.append(4274)
        return Int(ExpandTrig((a + b/sin(e + f*x))**m, (c + d/sin(e + f*x))**n, x), x)
    rule4274 = ReplacementRule(pattern4274, replacement4274)
    pattern4275 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement4275(m, f, b, d, a, n, c, x, e):
        rubi.append(4275)
        return Int((a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**n, x)
    rule4275 = ReplacementRule(pattern4275, replacement4275)
    pattern4276 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement4276(m, f, b, d, a, n, c, x, e):
        rubi.append(4276)
        return Int((a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**n, x)
    rule4276 = ReplacementRule(pattern4276, replacement4276)
    pattern4277 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons23, cons17)
    def replacement4277(m, f, b, d, a, n, x, e):
        rubi.append(4277)
        return Dist(d**m, Int((d*cos(e + f*x))**(-m + n)*(a*cos(e + f*x) + b)**m, x), x)
    rule4277 = ReplacementRule(pattern4277, replacement4277)
    pattern4278 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons23, cons17)
    def replacement4278(m, f, b, d, a, n, x, e):
        rubi.append(4278)
        return Dist(d**m, Int((d*sin(e + f*x))**(-m + n)*(a*sin(e + f*x) + b)**m, x), x)
    rule4278 = ReplacementRule(pattern4278, replacement4278)
    pattern4279 = Pattern(Integral(((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons23)
    def replacement4279(p, m, f, b, d, c, a, n, x, e):
        rubi.append(4279)
        return Dist(c**IntPart(n)*(c*(d/cos(e + f*x))**p)**FracPart(n)*(d/cos(e + f*x))**(-p*FracPart(n)), Int((d/cos(e + f*x))**(n*p)*(a + b/cos(e + f*x))**m, x), x)
    rule4279 = ReplacementRule(pattern4279, replacement4279)
    pattern4280 = Pattern(Integral(((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons23)
    def replacement4280(p, m, f, b, d, a, c, n, x, e):
        rubi.append(4280)
        return Dist(c**IntPart(n)*(c*(d/sin(e + f*x))**p)**FracPart(n)*(d/sin(e + f*x))**(-p*FracPart(n)), Int((d*cos(e + f*x))**(n*p)*(a + b*cos(e + f*x))**m, x), x)
    rule4280 = ReplacementRule(pattern4280, replacement4280)
    pattern4281 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons155, cons1421)
    def replacement4281(m, f, b, d, a, n, c, x, e):
        rubi.append(4281)
        return -Simp(b*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**n*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule4281 = ReplacementRule(pattern4281, replacement4281)
    pattern4282 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons155, cons1421)
    def replacement4282(m, f, b, d, a, n, c, x, e):
        rubi.append(4282)
        return Simp(b*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**n/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4282 = ReplacementRule(pattern4282, replacement4282)
    pattern4283 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons1315, cons1421, cons1231, cons1615)
    def replacement4283(m, f, b, d, a, n, c, x, e):
        rubi.append(4283)
        return Dist((m + n + S(1))/(a*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*(c + d/cos(e + f*x))**n/cos(e + f*x), x), x) - Simp(b*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**n*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule4283 = ReplacementRule(pattern4283, replacement4283)
    pattern4284 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons1315, cons1421, cons1231, cons1615)
    def replacement4284(m, f, b, d, a, n, c, x, e):
        rubi.append(4284)
        return Dist((m + n + S(1))/(a*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*(c + d/sin(e + f*x))**n/sin(e + f*x), x), x) + Simp(b*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**n/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4284 = ReplacementRule(pattern4284, replacement4284)
    pattern4285 = Pattern(Integral(sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265)
    def replacement4285(f, b, d, a, c, x, e):
        rubi.append(4285)
        return -Simp(a*c*log(S(1) + b/(a*cos(e + f*x)))*tan(e + f*x)/(b*f*sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))), x)
    rule4285 = ReplacementRule(pattern4285, replacement4285)
    pattern4286 = Pattern(Integral(sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265)
    def replacement4286(f, b, d, a, c, x, e):
        rubi.append(4286)
        return Simp(a*c*log(S(1) + b/(a*sin(e + f*x)))/(b*f*sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x)), x)
    rule4286 = ReplacementRule(pattern4286, replacement4286)
    pattern4287 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons70, cons1265, cons1314)
    def replacement4287(m, f, b, d, a, c, x, e):
        rubi.append(4287)
        return Simp(-S(2)*a*c*(a + b/cos(e + f*x))**m*tan(e + f*x)/(b*f*sqrt(c + d/cos(e + f*x))*(S(2)*m + S(1))), x)
    rule4287 = ReplacementRule(pattern4287, replacement4287)
    pattern4288 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons70, cons1265, cons1314)
    def replacement4288(m, f, b, d, a, c, x, e):
        rubi.append(4288)
        return Simp(S(2)*a*c*(a + b/sin(e + f*x))**m/(b*f*sqrt(c + d/sin(e + f*x))*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4288 = ReplacementRule(pattern4288, replacement4288)
    pattern4289 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons1266, cons31, cons1320)
    def replacement4289(m, f, b, d, a, n, c, x, e):
        rubi.append(4289)
        return -Dist(d*(S(2)*n + S(-1))/(b*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*(c + d/cos(e + f*x))**(n + S(-1))/cos(e + f*x), x), x) + Simp(-S(2)*a*c*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**(n + S(-1))*tan(e + f*x)/(b*f*(S(2)*m + S(1))), x)
    rule4289 = ReplacementRule(pattern4289, replacement4289)
    pattern4290 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons1266, cons31, cons1320)
    def replacement4290(m, f, b, d, a, n, c, x, e):
        rubi.append(4290)
        return -Dist(d*(S(2)*n + S(-1))/(b*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*(c + d/sin(e + f*x))**(n + S(-1))/sin(e + f*x), x), x) + Simp(S(2)*a*c*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**(n + S(-1))/(b*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4290 = ReplacementRule(pattern4290, replacement4290)
    pattern4291 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons70, cons1265, cons1266, cons1321, cons1616)
    def replacement4291(m, f, b, d, a, c, n, x, e):
        rubi.append(4291)
        return Dist(c*(S(2)*n + S(-1))/(m + n), Int((a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**(n + S(-1))/cos(e + f*x), x), x) + Simp(d*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**(n + S(-1))*tan(e + f*x)/(f*(m + n)), x)
    rule4291 = ReplacementRule(pattern4291, replacement4291)
    pattern4292 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons70, cons1265, cons1266, cons1321, cons1616)
    def replacement4292(m, f, b, d, a, c, n, x, e):
        rubi.append(4292)
        return Dist(c*(S(2)*n + S(-1))/(m + n), Int((a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**(n + S(-1))/sin(e + f*x), x), x) - Simp(d*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**(n + S(-1))/(f*(m + n)*tan(e + f*x)), x)
    rule4292 = ReplacementRule(pattern4292, replacement4292)
    pattern4293 = Pattern(Integral((c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons148)
    def replacement4293(f, b, d, a, n, c, x, e):
        rubi.append(4293)
        return Dist(S(2)*c, Int((c + d/cos(e + f*x))**(n + S(-1))/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) + Simp(S(2)*d*(c + d/cos(e + f*x))**(n + S(-1))*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(-1))), x)
    rule4293 = ReplacementRule(pattern4293, replacement4293)
    pattern4294 = Pattern(Integral((c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons148)
    def replacement4294(f, b, d, a, n, c, x, e):
        rubi.append(4294)
        return Dist(S(2)*c, Int((c + d/sin(e + f*x))**(n + S(-1))/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) + Simp(-S(2)*d*(c + d/sin(e + f*x))**(n + S(-1))/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(-1))*tan(e + f*x)), x)
    rule4294 = ReplacementRule(pattern4294, replacement4294)
    pattern4295 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons148, cons1320, cons515)
    def replacement4295(m, f, b, d, a, n, c, x, e):
        rubi.append(4295)
        return -Dist(d*(S(2)*n + S(-1))/(b*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*(c + d/cos(e + f*x))**(n + S(-1))/cos(e + f*x), x), x) + Simp(-S(2)*a*c*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**(n + S(-1))*tan(e + f*x)/(b*f*(S(2)*m + S(1))), x)
    rule4295 = ReplacementRule(pattern4295, replacement4295)
    pattern4296 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons148, cons1320, cons515)
    def replacement4296(m, f, b, d, a, n, c, x, e):
        rubi.append(4296)
        return -Dist(d*(S(2)*n + S(-1))/(b*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*(c + d/sin(e + f*x))**(n + S(-1))/sin(e + f*x), x), x) + Simp(S(2)*a*c*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**(n + S(-1))/(b*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4296 = ReplacementRule(pattern4296, replacement4296)
    pattern4297 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons150, cons1617, cons1618)
    def replacement4297(m, f, b, d, a, n, c, x, e):
        rubi.append(4297)
        return Dist((-a*c)**m, Int(ExpandTrig(tan(e + f*x)**(S(2)*m)/cos(e + f*x), (c + d/cos(e + f*x))**(-m + n), x), x), x)
    rule4297 = ReplacementRule(pattern4297, replacement4297)
    pattern4298 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons150, cons1617, cons1618)
    def replacement4298(m, f, b, d, a, n, c, x, e):
        rubi.append(4298)
        return Dist((-a*c)**m, Int(ExpandTrig((S(1)/tan(e + f*x))**(S(2)*m)/sin(e + f*x), (c + d/sin(e + f*x))**(-m + n), x), x), x)
    rule4298 = ReplacementRule(pattern4298, replacement4298)
    pattern4299 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons79)
    def replacement4299(m, f, b, d, a, c, x, e):
        rubi.append(4299)
        return Dist((-a*c)**(m + S(1)/2)*tan(e + f*x)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))), Int(tan(e + f*x)**(S(2)*m)/cos(e + f*x), x), x)
    rule4299 = ReplacementRule(pattern4299, replacement4299)
    pattern4300 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons79)
    def replacement4300(m, f, b, d, a, c, x, e):
        rubi.append(4300)
        return Dist((-a*c)**(m + S(1)/2)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x)), Int((S(1)/tan(e + f*x))**(S(2)*m)/sin(e + f*x), x), x)
    rule4300 = ReplacementRule(pattern4300, replacement4300)
    pattern4301 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons1619)
    def replacement4301(m, f, b, d, a, c, n, x, e):
        rubi.append(4301)
        return Dist((m + n + S(1))/(a*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*(c + d/cos(e + f*x))**n/cos(e + f*x), x), x) - Simp(b*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**n*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule4301 = ReplacementRule(pattern4301, replacement4301)
    pattern4302 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons1619)
    def replacement4302(m, f, b, d, a, c, n, x, e):
        rubi.append(4302)
        return Dist((m + n + S(1))/(a*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*(c + d/sin(e + f*x))**n/sin(e + f*x), x), x) + Simp(b*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**n/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4302 = ReplacementRule(pattern4302, replacement4302)
    pattern4303 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265)
    def replacement4303(m, f, b, d, a, c, n, x, e):
        rubi.append(4303)
        return -Dist(a*c*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))), Subst(Int((a + b*x)**(m + S(-1)/2)*(c + d*x)**(n + S(-1)/2), x), x, S(1)/cos(e + f*x)), x)
    rule4303 = ReplacementRule(pattern4303, replacement4303)
    pattern4304 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265)
    def replacement4304(m, f, b, d, a, c, n, x, e):
        rubi.append(4304)
        return Dist(a*c/(f*sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x)), Subst(Int((a + b*x)**(m + S(-1)/2)*(c + d*x)**(n + S(-1)/2), x), x, S(1)/sin(e + f*x)), x)
    rule4304 = ReplacementRule(pattern4304, replacement4304)
    pattern4305 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons150, cons1617, cons1618)
    def replacement4305(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(4305)
        return Dist((-a*c)**m, Int(ExpandTrig((g/cos(e + f*x))**p*tan(e + f*x)**(S(2)*m), (c + d/cos(e + f*x))**(-m + n), x), x), x)
    rule4305 = ReplacementRule(pattern4305, replacement4305)
    pattern4306 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons150, cons1617, cons1618)
    def replacement4306(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(4306)
        return Dist((-a*c)**m, Int(ExpandTrig((g/sin(e + f*x))**p*(S(1)/tan(e + f*x))**(S(2)*m), (c + d/sin(e + f*x))**(-m + n), x), x), x)
    rule4306 = ReplacementRule(pattern4306, replacement4306)
    pattern4307 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons70, cons1265, cons79)
    def replacement4307(p, m, f, g, b, d, a, c, x, e):
        rubi.append(4307)
        return Dist((-a*c)**(m + S(1)/2)*tan(e + f*x)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))), Int((g/cos(e + f*x))**p*tan(e + f*x)**(S(2)*m), x), x)
    rule4307 = ReplacementRule(pattern4307, replacement4307)
    pattern4308 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons70, cons1265, cons79)
    def replacement4308(p, m, f, b, g, d, a, c, x, e):
        rubi.append(4308)
        return Dist((-a*c)**(m + S(1)/2)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x)), Int((g/sin(e + f*x))**p*(S(1)/tan(e + f*x))**(S(2)*m), x), x)
    rule4308 = ReplacementRule(pattern4308, replacement4308)
    pattern4309 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265)
    def replacement4309(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(4309)
        return -Dist(a*c*g*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))), Subst(Int((g*x)**(p + S(-1))*(a + b*x)**(m + S(-1)/2)*(c + d*x)**(n + S(-1)/2), x), x, S(1)/cos(e + f*x)), x)
    rule4309 = ReplacementRule(pattern4309, replacement4309)
    pattern4310 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265)
    def replacement4310(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(4310)
        return Dist(a*c*g/(f*sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x)), Subst(Int((g*x)**(p + S(-1))*(a + b*x)**(m + S(-1)/2)*(c + d*x)**(n + S(-1)/2), x), x, S(1)/sin(e + f*x)), x)
    rule4310 = ReplacementRule(pattern4310, replacement4310)
    pattern4311 = Pattern(Integral(sqrt(WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement4311(f, g, b, d, a, c, x, e):
        rubi.append(4311)
        return Dist(S(2)*b*g/f, Subst(Int(S(1)/(a*d + b*c - c*g*x**S(2)), x), x, b*tan(e + f*x)/(sqrt(g/cos(e + f*x))*sqrt(a + b/cos(e + f*x)))), x)
    rule4311 = ReplacementRule(pattern4311, replacement4311)
    pattern4312 = Pattern(Integral(sqrt(WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement4312(f, b, g, d, a, c, x, e):
        rubi.append(4312)
        return Dist(-S(2)*b*g/f, Subst(Int(S(1)/(a*d + b*c - c*g*x**S(2)), x), x, b/(sqrt(g/sin(e + f*x))*sqrt(a + b/sin(e + f*x))*tan(e + f*x))), x)
    rule4312 = ReplacementRule(pattern4312, replacement4312)
    pattern4313 = Pattern(Integral(sqrt(WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267)
    def replacement4313(f, g, b, d, a, c, x, e):
        rubi.append(4313)
        return Dist(a/c, Int(sqrt(g/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x) + Dist((-a*d + b*c)/(c*g), Int((g/cos(e + f*x))**(S(3)/2)/(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))), x), x)
    rule4313 = ReplacementRule(pattern4313, replacement4313)
    pattern4314 = Pattern(Integral(sqrt(WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267)
    def replacement4314(f, b, g, d, a, c, x, e):
        rubi.append(4314)
        return Dist(a/c, Int(sqrt(g/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x) + Dist((-a*d + b*c)/(c*g), Int((g/sin(e + f*x))**(S(3)/2)/(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))), x), x)
    rule4314 = ReplacementRule(pattern4314, replacement4314)
    pattern4315 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement4315(f, b, d, a, c, x, e):
        rubi.append(4315)
        return Dist(S(2)*b/f, Subst(Int(S(1)/(a*d + b*c + d*x**S(2)), x), x, b*tan(e + f*x)/sqrt(a + b/cos(e + f*x))), x)
    rule4315 = ReplacementRule(pattern4315, replacement4315)
    pattern4316 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement4316(f, b, d, a, c, x, e):
        rubi.append(4316)
        return Dist(-S(2)*b/f, Subst(Int(S(1)/(a*d + b*c + d*x**S(2)), x), x, b/(sqrt(a + b/sin(e + f*x))*tan(e + f*x))), x)
    rule4316 = ReplacementRule(pattern4316, replacement4316)
    pattern4317 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1322)
    def replacement4317(f, b, d, a, c, x, e):
        rubi.append(4317)
        return Simp(sqrt(c/(c + d/cos(e + f*x)))*sqrt(a + b/cos(e + f*x))*EllipticE(asin(c*tan(e + f*x)/(c + d/cos(e + f*x))), -(-a*d + b*c)/(a*d + b*c))/(d*f*sqrt(c*d*(a + b/cos(e + f*x))/((c + d/cos(e + f*x))*(a*d + b*c)))), x)
    rule4317 = ReplacementRule(pattern4317, replacement4317)
    pattern4318 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1322)
    def replacement4318(f, b, d, a, c, x, e):
        rubi.append(4318)
        return -Simp(sqrt(c/(c + d/sin(e + f*x)))*sqrt(a + b/sin(e + f*x))*EllipticE(asin(c/((c + d/sin(e + f*x))*tan(e + f*x))), -(-a*d + b*c)/(a*d + b*c))/(d*f*sqrt(c*d*(a + b/sin(e + f*x))/((c + d/sin(e + f*x))*(a*d + b*c)))), x)
    rule4318 = ReplacementRule(pattern4318, replacement4318)
    pattern4319 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4319(f, b, d, a, c, x, e):
        rubi.append(4319)
        return Dist(b/d, Int(S(1)/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int(S(1)/(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4319 = ReplacementRule(pattern4319, replacement4319)
    pattern4320 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4320(f, b, d, a, c, x, e):
        rubi.append(4320)
        return Dist(b/d, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int(S(1)/(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4320 = ReplacementRule(pattern4320, replacement4320)
    pattern4321 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement4321(f, g, b, d, a, c, x, e):
        rubi.append(4321)
        return Dist(g/d, Int(sqrt(g/cos(e + f*x))*sqrt(a + b/cos(e + f*x)), x), x) - Dist(c*g/d, Int(sqrt(g/cos(e + f*x))*sqrt(a + b/cos(e + f*x))/(c + d/cos(e + f*x)), x), x)
    rule4321 = ReplacementRule(pattern4321, replacement4321)
    pattern4322 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement4322(f, b, g, d, a, c, x, e):
        rubi.append(4322)
        return Dist(g/d, Int(sqrt(g/sin(e + f*x))*sqrt(a + b/sin(e + f*x)), x), x) - Dist(c*g/d, Int(sqrt(g/sin(e + f*x))*sqrt(a + b/sin(e + f*x))/(c + d/sin(e + f*x)), x), x)
    rule4322 = ReplacementRule(pattern4322, replacement4322)
    pattern4323 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267)
    def replacement4323(f, g, b, d, a, c, x, e):
        rubi.append(4323)
        return Dist(b/d, Int((g/cos(e + f*x))**(S(3)/2)/sqrt(a + b/cos(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int((g/cos(e + f*x))**(S(3)/2)/(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))), x), x)
    rule4323 = ReplacementRule(pattern4323, replacement4323)
    pattern4324 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267)
    def replacement4324(f, b, g, d, a, c, x, e):
        rubi.append(4324)
        return Dist(b/d, Int((g/sin(e + f*x))**(S(3)/2)/sqrt(a + b/sin(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int((g/sin(e + f*x))**(S(3)/2)/(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))), x), x)
    rule4324 = ReplacementRule(pattern4324, replacement4324)
    pattern4325 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4325(f, b, d, a, c, x, e):
        rubi.append(4325)
        return Dist(b/(-a*d + b*c), Int(S(1)/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) - Dist(d/(-a*d + b*c), Int(sqrt(a + b/cos(e + f*x))/((c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4325 = ReplacementRule(pattern4325, replacement4325)
    pattern4326 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4326(f, b, d, a, c, x, e):
        rubi.append(4326)
        return Dist(b/(-a*d + b*c), Int(S(1)/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) - Dist(d/(-a*d + b*c), Int(sqrt(a + b/sin(e + f*x))/((c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4326 = ReplacementRule(pattern4326, replacement4326)
    pattern4327 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4327(f, b, d, a, c, x, e):
        rubi.append(4327)
        return Simp(S(2)*sqrt((a + b/cos(e + f*x))/(a + b))*EllipticPi(S(2)*d/(c + d), asin(sqrt(S(2))*sqrt(S(1) - S(1)/cos(e + f*x))/S(2)), S(2)*b/(a + b))*tan(e + f*x)/(f*sqrt(-tan(e + f*x)**S(2))*sqrt(a + b/cos(e + f*x))*(c + d)), x)
    rule4327 = ReplacementRule(pattern4327, replacement4327)
    pattern4328 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4328(f, b, d, a, c, x, e):
        rubi.append(4328)
        return Simp(-S(2)*sqrt((a + b/sin(e + f*x))/(a + b))*EllipticPi(S(2)*d/(c + d), asin(sqrt(S(2))*sqrt(S(1) - S(1)/sin(e + f*x))/S(2)), S(2)*b/(a + b))/(f*sqrt(-S(1)/tan(e + f*x)**S(2))*sqrt(a + b/sin(e + f*x))*(c + d)*tan(e + f*x)), x)
    rule4328 = ReplacementRule(pattern4328, replacement4328)
    pattern4329 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement4329(f, g, b, d, a, c, x, e):
        rubi.append(4329)
        return -Dist(a*g/(-a*d + b*c), Int(sqrt(g/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x) + Dist(c*g/(-a*d + b*c), Int(sqrt(g/cos(e + f*x))*sqrt(a + b/cos(e + f*x))/(c + d/cos(e + f*x)), x), x)
    rule4329 = ReplacementRule(pattern4329, replacement4329)
    pattern4330 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement4330(f, b, g, d, a, c, x, e):
        rubi.append(4330)
        return -Dist(a*g/(-a*d + b*c), Int(sqrt(g/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x) + Dist(c*g/(-a*d + b*c), Int(sqrt(g/sin(e + f*x))*sqrt(a + b/sin(e + f*x))/(c + d/sin(e + f*x)), x), x)
    rule4330 = ReplacementRule(pattern4330, replacement4330)
    pattern4331 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267)
    def replacement4331(f, g, b, d, a, c, x, e):
        rubi.append(4331)
        return Dist(g*sqrt(g/cos(e + f*x))*sqrt(a*cos(e + f*x) + b)/sqrt(a + b/cos(e + f*x)), Int(S(1)/(sqrt(a*cos(e + f*x) + b)*(c*cos(e + f*x) + d)), x), x)
    rule4331 = ReplacementRule(pattern4331, replacement4331)
    pattern4332 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267)
    def replacement4332(f, b, g, d, a, c, x, e):
        rubi.append(4332)
        return Dist(g*sqrt(g/sin(e + f*x))*sqrt(a*sin(e + f*x) + b)/sqrt(a + b/sin(e + f*x)), Int(S(1)/(sqrt(a*sin(e + f*x) + b)*(c*sin(e + f*x) + d)), x), x)
    rule4332 = ReplacementRule(pattern4332, replacement4332)
    pattern4333 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4333(f, b, d, a, c, x, e):
        rubi.append(4333)
        return -Dist(a/(-a*d + b*c), Int(S(1)/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) + Dist(c/(-a*d + b*c), Int(sqrt(a + b/cos(e + f*x))/((c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4333 = ReplacementRule(pattern4333, replacement4333)
    pattern4334 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1409)
    def replacement4334(f, b, d, a, c, x, e):
        rubi.append(4334)
        return -Dist(a/(-a*d + b*c), Int(S(1)/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) + Dist(c/(-a*d + b*c), Int(sqrt(a + b/sin(e + f*x))/((c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4334 = ReplacementRule(pattern4334, replacement4334)
    pattern4335 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4335(f, b, d, a, c, x, e):
        rubi.append(4335)
        return Dist(S(1)/d, Int(S(1)/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) - Dist(c/d, Int(S(1)/(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4335 = ReplacementRule(pattern4335, replacement4335)
    pattern4336 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4336(f, b, d, a, c, x, e):
        rubi.append(4336)
        return Dist(S(1)/d, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) - Dist(c/d, Int(S(1)/(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4336 = ReplacementRule(pattern4336, replacement4336)
    pattern4337 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(5)/2)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement4337(f, g, b, d, a, c, x, e):
        rubi.append(4337)
        return Dist(g**S(2)/(d*(-a*d + b*c)), Int(sqrt(g/cos(e + f*x))*(a*c + (-a*d + b*c)/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x) - Dist(c**S(2)*g**S(2)/(d*(-a*d + b*c)), Int(sqrt(g/cos(e + f*x))*sqrt(a + b/cos(e + f*x))/(c + d/cos(e + f*x)), x), x)
    rule4337 = ReplacementRule(pattern4337, replacement4337)
    pattern4338 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(5)/2)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement4338(f, b, g, d, a, c, x, e):
        rubi.append(4338)
        return Dist(g**S(2)/(d*(-a*d + b*c)), Int(sqrt(g/sin(e + f*x))*(a*c + (-a*d + b*c)/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x) - Dist(c**S(2)*g**S(2)/(d*(-a*d + b*c)), Int(sqrt(g/sin(e + f*x))*sqrt(a + b/sin(e + f*x))/(c + d/sin(e + f*x)), x), x)
    rule4338 = ReplacementRule(pattern4338, replacement4338)
    pattern4339 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(5)/2)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267)
    def replacement4339(f, g, b, d, a, c, x, e):
        rubi.append(4339)
        return Dist(g/d, Int((g/cos(e + f*x))**(S(3)/2)/sqrt(a + b/cos(e + f*x)), x), x) - Dist(c*g/d, Int((g/cos(e + f*x))**(S(3)/2)/(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))), x), x)
    rule4339 = ReplacementRule(pattern4339, replacement4339)
    pattern4340 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(5)/2)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267)
    def replacement4340(f, b, g, d, a, c, x, e):
        rubi.append(4340)
        return Dist(g/d, Int((g/sin(e + f*x))**(S(3)/2)/sqrt(a + b/sin(e + f*x)), x), x) - Dist(c*g/d, Int((g/sin(e + f*x))**(S(3)/2)/(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))), x), x)
    rule4340 = ReplacementRule(pattern4340, replacement4340)
    pattern4341 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement4341(f, b, d, a, c, x, e):
        rubi.append(4341)
        return Dist(S(2)*b/f, Subst(Int(S(1)/(-b*d*x**S(2) + S(1)), x), x, tan(e + f*x)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x)))), x)
    rule4341 = ReplacementRule(pattern4341, replacement4341)
    pattern4342 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement4342(f, b, d, a, c, x, e):
        rubi.append(4342)
        return Dist(-S(2)*b/f, Subst(Int(S(1)/(-b*d*x**S(2) + S(1)), x), x, S(1)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x))), x)
    rule4342 = ReplacementRule(pattern4342, replacement4342)
    pattern4343 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1322)
    def replacement4343(f, b, d, a, c, x, e):
        rubi.append(4343)
        return Dist(b/d, Int(sqrt(c + d/cos(e + f*x))/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int(S(1)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4343 = ReplacementRule(pattern4343, replacement4343)
    pattern4344 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1322)
    def replacement4344(f, b, d, a, c, x, e):
        rubi.append(4344)
        return Dist(b/d, Int(sqrt(c + d/sin(e + f*x))/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4344 = ReplacementRule(pattern4344, replacement4344)
    pattern4345 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4345(f, b, d, a, c, x, e):
        rubi.append(4345)
        return Simp(S(2)*sqrt((S(1) + S(1)/cos(e + f*x))*(-a*d + b*c)/((a + b/cos(e + f*x))*(c - d)))*sqrt(-(S(1) - S(1)/cos(e + f*x))*(-a*d + b*c)/((a + b/cos(e + f*x))*(c + d)))*(a + b/cos(e + f*x))*EllipticPi(b*(c + d)/(d*(a + b)), asin(sqrt((a + b)/(c + d))*sqrt(c + d/cos(e + f*x))/sqrt(a + b/cos(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))/(d*f*sqrt((a + b)/(c + d))*tan(e + f*x)), x)
    rule4345 = ReplacementRule(pattern4345, replacement4345)
    pattern4346 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4346(f, b, d, a, c, x, e):
        rubi.append(4346)
        return Simp(-S(2)*sqrt((S(1) + S(1)/sin(e + f*x))*(-a*d + b*c)/((a + b/sin(e + f*x))*(c - d)))*sqrt(-(S(1) - S(1)/sin(e + f*x))*(-a*d + b*c)/((a + b/sin(e + f*x))*(c + d)))*(a + b/sin(e + f*x))*EllipticPi(b*(c + d)/(d*(a + b)), asin(sqrt((a + b)/(c + d))*sqrt(c + d/sin(e + f*x))/sqrt(a + b/sin(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))*tan(e + f*x)/(d*f*sqrt((a + b)/(c + d))), x)
    rule4346 = ReplacementRule(pattern4346, replacement4346)
    pattern4347 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement4347(f, b, d, a, c, x, e):
        rubi.append(4347)
        return Dist(S(2)*a/(b*f), Subst(Int(S(1)/(x**S(2)*(a*c - b*d) + S(2)), x), x, tan(e + f*x)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x)))), x)
    rule4347 = ReplacementRule(pattern4347, replacement4347)
    pattern4348 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement4348(f, b, d, a, c, x, e):
        rubi.append(4348)
        return Dist(-S(2)*a/(b*f), Subst(Int(S(1)/(x**S(2)*(a*c - b*d) + S(2)), x), x, S(1)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*tan(e + f*x))), x)
    rule4348 = ReplacementRule(pattern4348, replacement4348)
    pattern4349 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4349(f, b, d, a, c, x, e):
        rubi.append(4349)
        return Simp(S(2)*sqrt((S(1) - S(1)/cos(e + f*x))*(-a*d + b*c)/((a + b)*(c + d/cos(e + f*x))))*sqrt(-(S(1) + S(1)/cos(e + f*x))*(-a*d + b*c)/((a - b)*(c + d/cos(e + f*x))))*(c + d/cos(e + f*x))*EllipticF(asin(sqrt(a + b/cos(e + f*x))*Rt((c + d)/(a + b), S(2))/sqrt(c + d/cos(e + f*x))), (a + b)*(c - d)/((a - b)*(c + d)))/(f*(-a*d + b*c)*Rt((c + d)/(a + b), S(2))*tan(e + f*x)), x)
    rule4349 = ReplacementRule(pattern4349, replacement4349)
    pattern4350 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4350(f, b, d, a, c, x, e):
        rubi.append(4350)
        return Simp(-S(2)*sqrt((S(1) - S(1)/sin(e + f*x))*(-a*d + b*c)/((a + b)*(c + d/sin(e + f*x))))*sqrt(-(S(1) + S(1)/sin(e + f*x))*(-a*d + b*c)/((a - b)*(c + d/sin(e + f*x))))*(c + d/sin(e + f*x))*EllipticF(asin(sqrt(a + b/sin(e + f*x))*Rt((c + d)/(a + b), S(2))/sqrt(c + d/sin(e + f*x))), (a + b)*(c - d)/((a - b)*(c + d)))*tan(e + f*x)/(f*(-a*d + b*c)*Rt((c + d)/(a + b), S(2))), x)
    rule4350 = ReplacementRule(pattern4350, replacement4350)
    pattern4351 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement4351(f, b, d, a, c, x, e):
        rubi.append(4351)
        return Dist(S(1)/b, Int(sqrt(a + b/cos(e + f*x))/(sqrt(c + d/cos(e + f*x))*cos(e + f*x)), x), x) - Dist(a/b, Int(S(1)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4351 = ReplacementRule(pattern4351, replacement4351)
    pattern4352 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement4352(f, b, d, a, c, x, e):
        rubi.append(4352)
        return Dist(S(1)/b, Int(sqrt(a + b/sin(e + f*x))/(sqrt(c + d/sin(e + f*x))*sin(e + f*x)), x), x) - Dist(a/b, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4352 = ReplacementRule(pattern4352, replacement4352)
    pattern4353 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4353(f, b, d, a, c, x, e):
        rubi.append(4353)
        return Dist((a - b)/(c - d), Int(S(1)/(sqrt(a + b/cos(e + f*x))*sqrt(c + d/cos(e + f*x))*cos(e + f*x)), x), x) + Dist((-a*d + b*c)/(c - d), Int((S(1) + S(1)/cos(e + f*x))/(sqrt(a + b/cos(e + f*x))*(c + d/cos(e + f*x))**(S(3)/2)*cos(e + f*x)), x), x)
    rule4353 = ReplacementRule(pattern4353, replacement4353)
    pattern4354 = Pattern(Integral(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement4354(f, b, d, a, c, x, e):
        rubi.append(4354)
        return Dist((a - b)/(c - d), Int(S(1)/(sqrt(a + b/sin(e + f*x))*sqrt(c + d/sin(e + f*x))*sin(e + f*x)), x), x) + Dist((-a*d + b*c)/(c - d), Int((S(1) + S(1)/sin(e + f*x))/(sqrt(a + b/sin(e + f*x))*(c + d/sin(e + f*x))**(S(3)/2)*sin(e + f*x)), x), x)
    rule4354 = ReplacementRule(pattern4354, replacement4354)
    pattern4355 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons1265, cons1323, cons1620)
    def replacement4355(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(4355)
        return -Dist(a**S(2)*g*tan(e + f*x)/(f*sqrt(a - b/cos(e + f*x))*sqrt(a + b/cos(e + f*x))), Subst(Int((g*x)**(p + S(-1))*(a + b*x)**(m + S(-1)/2)*(c + d*x)**n/sqrt(a - b*x), x), x, S(1)/cos(e + f*x)), x)
    rule4355 = ReplacementRule(pattern4355, replacement4355)
    pattern4356 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons1265, cons1323, cons1620)
    def replacement4356(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(4356)
        return Dist(a**S(2)*g/(f*sqrt(a - b/sin(e + f*x))*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), Subst(Int((g*x)**(p + S(-1))*(a + b*x)**(m + S(-1)/2)*(c + d*x)**n/sqrt(a - b*x), x), x, S(1)/sin(e + f*x)), x)
    rule4356 = ReplacementRule(pattern4356, replacement4356)
    pattern4357 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons71, cons17, cons85)
    def replacement4357(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(4357)
        return Dist(g**(-m - n), Int((g/cos(e + f*x))**(m + n + p)*(a*cos(e + f*x) + b)**m*(c*cos(e + f*x) + d)**n, x), x)
    rule4357 = ReplacementRule(pattern4357, replacement4357)
    pattern4358 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons71, cons17, cons85)
    def replacement4358(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(4358)
        return Dist(g**(-m - n), Int((g/sin(e + f*x))**(m + n + p)*(a*sin(e + f*x) + b)**m*(c*sin(e + f*x) + d)**n, x), x)
    rule4358 = ReplacementRule(pattern4358, replacement4358)
    pattern4359 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons71, cons1621, cons17)
    def replacement4359(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(4359)
        return Dist(g**(-m)*(g/cos(e + f*x))**(m + p)*(c + d/cos(e + f*x))**n*(c*cos(e + f*x) + d)**(-n), Int((a*cos(e + f*x) + b)**m*(c*cos(e + f*x) + d)**n, x), x)
    rule4359 = ReplacementRule(pattern4359, replacement4359)
    pattern4360 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons71, cons1621, cons17)
    def replacement4360(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(4360)
        return Dist(g**(-m)*(g/sin(e + f*x))**(m + p)*(c + d/sin(e + f*x))**n*(c*sin(e + f*x) + d)**(-n), Int((a*sin(e + f*x) + b)**m*(c*sin(e + f*x) + d)**n, x), x)
    rule4360 = ReplacementRule(pattern4360, replacement4360)
    pattern4361 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons1621, cons18)
    def replacement4361(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(4361)
        return Dist((g/cos(e + f*x))**p*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**n*(a*cos(e + f*x) + b)**(-m)*(c*cos(e + f*x) + d)**(-n), Int((a*cos(e + f*x) + b)**m*(c*cos(e + f*x) + d)**n, x), x)
    rule4361 = ReplacementRule(pattern4361, replacement4361)
    pattern4362 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons1621, cons18)
    def replacement4362(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(4362)
        return Dist((g/sin(e + f*x))**p*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**n*(a*sin(e + f*x) + b)**(-m)*(c*sin(e + f*x) + d)**(-n), Int((a*sin(e + f*x) + b)**m*(c*sin(e + f*x) + d)**n, x), x)
    rule4362 = ReplacementRule(pattern4362, replacement4362)
    pattern4363 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(S(1)/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1304, cons1607, cons38, cons1622)
    def replacement4363(p, m, f, b, d, a, c, n, x, e):
        rubi.append(4363)
        return Dist(sqrt(a + b/cos(e + f*x))*sqrt(c*cos(e + f*x) + d)/(sqrt(c + d/cos(e + f*x))*sqrt(a*cos(e + f*x) + b)), Int((a*cos(e + f*x) + b)**m*(c*cos(e + f*x) + d)**n*cos(e + f*x)**(-m - n - p), x), x)
    rule4363 = ReplacementRule(pattern4363, replacement4363)
    pattern4364 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(S(1)/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1304, cons1607, cons38, cons1622)
    def replacement4364(p, m, f, b, d, a, c, n, x, e):
        rubi.append(4364)
        return Dist(sqrt(a + b/sin(e + f*x))*sqrt(c*sin(e + f*x) + d)/(sqrt(c + d/sin(e + f*x))*sqrt(a*sin(e + f*x) + b)), Int((a*sin(e + f*x) + b)**m*(c*sin(e + f*x) + d)**n*sin(e + f*x)**(-m - n - p), x), x)
    rule4364 = ReplacementRule(pattern4364, replacement4364)
    pattern4365 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons1415)
    def replacement4365(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(4365)
        return Int(ExpandTrig((g/cos(e + f*x))**p*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**n, x), x)
    rule4365 = ReplacementRule(pattern4365, replacement4365)
    pattern4366 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons1415)
    def replacement4366(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(4366)
        return Int(ExpandTrig((g/sin(e + f*x))**p*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**n, x), x)
    rule4366 = ReplacementRule(pattern4366, replacement4366)
    pattern4367 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons380)
    def replacement4367(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(4367)
        return Int((g/cos(e + f*x))**p*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**n, x)
    rule4367 = ReplacementRule(pattern4367, replacement4367)
    pattern4368 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons380)
    def replacement4368(p, m, f, b, g, d, c, a, n, x, e):
        rubi.append(4368)
        return Int((g/sin(e + f*x))**p*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**n, x)
    rule4368 = ReplacementRule(pattern4368, replacement4368)
    pattern4369 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons1428)
    def replacement4369(B, f, b, d, a, c, A, x, e):
        rubi.append(4369)
        return Simp(S(2)*A*sqrt((S(1) - S(1)/cos(e + f*x))*(-a*d + b*c)/((a + b)*(c + d/cos(e + f*x))))*(S(1) + S(1)/cos(e + f*x))*EllipticE(asin(sqrt(a + b/cos(e + f*x))*Rt((c + d)/(a + b), S(2))/sqrt(c + d/cos(e + f*x))), (a + b)*(c - d)/((a - b)*(c + d)))/(f*sqrt(-(S(1) + S(1)/cos(e + f*x))*(-a*d + b*c)/((a - b)*(c + d/cos(e + f*x))))*(-a*d + b*c)*Rt((c + d)/(a + b), S(2))*tan(e + f*x)), x)
    rule4369 = ReplacementRule(pattern4369, replacement4369)
    pattern4370 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons1428)
    def replacement4370(B, f, b, d, a, c, A, x, e):
        rubi.append(4370)
        return Simp(-S(2)*A*sqrt((S(1) - S(1)/sin(e + f*x))*(-a*d + b*c)/((a + b)*(c + d/sin(e + f*x))))*(S(1) + S(1)/sin(e + f*x))*EllipticE(asin(sqrt(a + b/sin(e + f*x))*Rt((c + d)/(a + b), S(2))/sqrt(c + d/sin(e + f*x))), (a + b)*(c - d)/((a - b)*(c + d)))*tan(e + f*x)/(f*sqrt(-(S(1) + S(1)/sin(e + f*x))*(-a*d + b*c)/((a - b)*(c + d/sin(e + f*x))))*(-a*d + b*c)*Rt((c + d)/(a + b), S(2))), x)
    rule4370 = ReplacementRule(pattern4370, replacement4370)
    pattern4371 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons87, cons1586)
    def replacement4371(B, f, b, d, a, n, A, x, e):
        rubi.append(4371)
        return Dist(S(1)/(d*n), Int((d/cos(e + f*x))**(n + S(1))*Simp(n*(A*b + B*a) + (A*a*(n + S(1)) + B*b*n)/cos(e + f*x), x), x), x) - Simp(A*a*(d/cos(e + f*x))**n*tan(e + f*x)/(f*n), x)
    rule4371 = ReplacementRule(pattern4371, replacement4371)
    pattern4372 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons87, cons1586)
    def replacement4372(B, f, b, d, a, n, A, x, e):
        rubi.append(4372)
        return Dist(S(1)/(d*n), Int((d/sin(e + f*x))**(n + S(1))*Simp(n*(A*b + B*a) + (A*a*(n + S(1)) + B*b*n)/sin(e + f*x), x), x), x) + Simp(A*a*(d/sin(e + f*x))**n/(f*n*tan(e + f*x)), x)
    rule4372 = ReplacementRule(pattern4372, replacement4372)
    pattern4373 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1569)
    def replacement4373(B, f, b, d, a, n, A, x, e):
        rubi.append(4373)
        return Dist(S(1)/(n + S(1)), Int((d/cos(e + f*x))**n*Simp(A*a*(n + S(1)) + B*b*n + (n + S(1))*(A*b + B*a)/cos(e + f*x), x), x), x) + Simp(B*b*(d/cos(e + f*x))**n*tan(e + f*x)/(f*(n + S(1))), x)
    rule4373 = ReplacementRule(pattern4373, replacement4373)
    pattern4374 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1569)
    def replacement4374(B, f, b, d, a, n, A, x, e):
        rubi.append(4374)
        return Dist(S(1)/(n + S(1)), Int((d/sin(e + f*x))**n*Simp(A*a*(n + S(1)) + B*b*n + (n + S(1))*(A*b + B*a)/sin(e + f*x), x), x), x) - Simp(B*b*(d/sin(e + f*x))**n/(f*(n + S(1))*tan(e + f*x)), x)
    rule4374 = ReplacementRule(pattern4374, replacement4374)
    pattern4375 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1245)
    def replacement4375(B, f, b, a, A, x, e):
        rubi.append(4375)
        return Dist(B/b, Int(S(1)/cos(e + f*x), x), x) + Dist((A*b - B*a)/b, Int(S(1)/((a + b/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4375 = ReplacementRule(pattern4375, replacement4375)
    pattern4376 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1245)
    def replacement4376(B, f, b, a, A, x, e):
        rubi.append(4376)
        return Dist(B/b, Int(S(1)/sin(e + f*x), x), x) + Dist((A*b - B*a)/b, Int(S(1)/((a + b/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4376 = ReplacementRule(pattern4376, replacement4376)
    pattern4377 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons21, cons1245, cons1265, cons1623)
    def replacement4377(B, m, f, b, a, A, x, e):
        rubi.append(4377)
        return Simp(B*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4377 = ReplacementRule(pattern4377, replacement4377)
    pattern4378 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons21, cons1245, cons1265, cons1623)
    def replacement4378(B, m, f, b, a, A, x, e):
        rubi.append(4378)
        return -Simp(B*(a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4378 = ReplacementRule(pattern4378, replacement4378)
    pattern4379 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons1245, cons1265, cons1624, cons31, cons1320)
    def replacement4379(B, m, f, b, a, A, x, e):
        rubi.append(4379)
        return Dist((A*b*(m + S(1)) + B*a*m)/(a*b*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))/cos(e + f*x), x), x) - Simp((a + b/cos(e + f*x))**m*(A*b - B*a)*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule4379 = ReplacementRule(pattern4379, replacement4379)
    pattern4380 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons1245, cons1265, cons1624, cons31, cons1320)
    def replacement4380(B, m, f, b, a, A, x, e):
        rubi.append(4380)
        return Dist((A*b*(m + S(1)) + B*a*m)/(a*b*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))/sin(e + f*x), x), x) + Simp((a + b/sin(e + f*x))**m*(A*b - B*a)/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4380 = ReplacementRule(pattern4380, replacement4380)
    pattern4381 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons21, cons1245, cons1265, cons1624, cons1321)
    def replacement4381(B, m, f, b, a, A, x, e):
        rubi.append(4381)
        return Dist((A*b*(m + S(1)) + B*a*m)/(b*(m + S(1))), Int((a + b/cos(e + f*x))**m/cos(e + f*x), x), x) + Simp(B*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4381 = ReplacementRule(pattern4381, replacement4381)
    pattern4382 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons21, cons1245, cons1265, cons1624, cons1321)
    def replacement4382(B, m, f, b, a, A, x, e):
        rubi.append(4382)
        return Dist((A*b*(m + S(1)) + B*a*m)/(b*(m + S(1))), Int((a + b/sin(e + f*x))**m/sin(e + f*x), x), x) - Simp(B*(a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4382 = ReplacementRule(pattern4382, replacement4382)
    pattern4383 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons1245, cons1267, cons31, cons168)
    def replacement4383(B, m, f, b, a, A, x, e):
        rubi.append(4383)
        return Dist(S(1)/(m + S(1)), Int((a + b/cos(e + f*x))**(m + S(-1))*Simp(A*a*(m + S(1)) + B*b*m + (A*b*(m + S(1)) + B*a*m)/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp(B*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4383 = ReplacementRule(pattern4383, replacement4383)
    pattern4384 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons1245, cons1267, cons31, cons168)
    def replacement4384(B, m, f, b, a, A, x, e):
        rubi.append(4384)
        return Dist(S(1)/(m + S(1)), Int((a + b/sin(e + f*x))**(m + S(-1))*Simp(A*a*(m + S(1)) + B*b*m + (A*b*(m + S(1)) + B*a*m)/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp(B*(a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4384 = ReplacementRule(pattern4384, replacement4384)
    pattern4385 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons1245, cons1267, cons31, cons94)
    def replacement4385(B, m, f, b, a, A, x, e):
        rubi.append(4385)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp((m + S(1))*(A*a - B*b) - (m + S(2))*(A*b - B*a)/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**(m + S(1))*(A*b - B*a)*tan(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4385 = ReplacementRule(pattern4385, replacement4385)
    pattern4386 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons1245, cons1267, cons31, cons94)
    def replacement4386(B, m, f, b, a, A, x, e):
        rubi.append(4386)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp((m + S(1))*(A*a - B*b) - (m + S(2))*(A*b - B*a)/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**(m + S(1))*(A*b - B*a)/(f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4386 = ReplacementRule(pattern4386, replacement4386)
    pattern4387 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1267, cons1625)
    def replacement4387(B, f, b, a, A, x, e):
        rubi.append(4387)
        return Simp(S(2)*sqrt(b*(S(1) - S(1)/cos(e + f*x))/(a + b))*sqrt(-b*(S(1) + S(1)/cos(e + f*x))/(a - b))*(A*b - B*a)*EllipticE(asin(sqrt(a + b/cos(e + f*x))/Rt(a + B*b/A, S(2))), (A*a + B*b)/(A*a - B*b))*Rt(a + B*b/A, S(2))/(b**S(2)*f*tan(e + f*x)), x)
    rule4387 = ReplacementRule(pattern4387, replacement4387)
    pattern4388 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1267, cons1625)
    def replacement4388(B, f, b, a, A, x, e):
        rubi.append(4388)
        return Simp(-S(2)*sqrt(b*(S(1) - S(1)/sin(e + f*x))/(a + b))*sqrt(-b*(S(1) + S(1)/sin(e + f*x))/(a - b))*(A*b - B*a)*EllipticE(asin(sqrt(a + b/sin(e + f*x))/Rt(a + B*b/A, S(2))), (A*a + B*b)/(A*a - B*b))*Rt(a + B*b/A, S(2))*tan(e + f*x)/(b**S(2)*f), x)
    rule4388 = ReplacementRule(pattern4388, replacement4388)
    pattern4389 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1267, cons1626)
    def replacement4389(B, f, b, a, A, x, e):
        rubi.append(4389)
        return Dist(B, Int((S(1) + S(1)/cos(e + f*x))/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) + Dist(A - B, Int(S(1)/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x)
    rule4389 = ReplacementRule(pattern4389, replacement4389)
    pattern4390 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1267, cons1626)
    def replacement4390(B, f, b, a, A, x, e):
        rubi.append(4390)
        return Dist(B, Int((S(1) + S(1)/sin(e + f*x))/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) + Dist(A - B, Int(S(1)/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x)
    rule4390 = ReplacementRule(pattern4390, replacement4390)
    pattern4391 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons1245, cons1267, cons1625, cons77)
    def replacement4391(B, m, f, b, a, A, x, e):
        rubi.append(4391)
        return Simp(-S(2)*sqrt(S(2))*A*sqrt((A + B/cos(e + f*x))/A)*(A*(a + b/cos(e + f*x))/(A*a + B*b))**(-m)*(A - B/cos(e + f*x))*(a + b/cos(e + f*x))**m*AppellF1(S(1)/2, S(-1)/2, -m, S(3)/2, (A - B/cos(e + f*x))/(S(2)*A), b*(A - B/cos(e + f*x))/(A*b + B*a))/(B*f*tan(e + f*x)), x)
    rule4391 = ReplacementRule(pattern4391, replacement4391)
    pattern4392 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons1245, cons1267, cons1625, cons77)
    def replacement4392(B, m, f, b, a, A, x, e):
        rubi.append(4392)
        return Simp(S(2)*sqrt(S(2))*A*sqrt((A + B/sin(e + f*x))/A)*(A*(a + b/sin(e + f*x))/(A*a + B*b))**(-m)*(A - B/sin(e + f*x))*(a + b/sin(e + f*x))**m*AppellF1(S(1)/2, S(-1)/2, -m, S(3)/2, (A - B/sin(e + f*x))/(S(2)*A), b*(A - B/sin(e + f*x))/(A*b + B*a))*tan(e + f*x)/(B*f), x)
    rule4392 = ReplacementRule(pattern4392, replacement4392)
    pattern4393 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons21, cons1245, cons1267)
    def replacement4393(B, m, f, b, a, A, x, e):
        rubi.append(4393)
        return Dist(B/b, Int((a + b/cos(e + f*x))**(m + S(1))/cos(e + f*x), x), x) + Dist((A*b - B*a)/b, Int((a + b/cos(e + f*x))**m/cos(e + f*x), x), x)
    rule4393 = ReplacementRule(pattern4393, replacement4393)
    pattern4394 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons34, cons35, cons48, cons125, cons21, cons1245, cons1267)
    def replacement4394(B, m, f, b, a, A, x, e):
        rubi.append(4394)
        return Dist(B/b, Int((a + b/sin(e + f*x))**(m + S(1))/sin(e + f*x), x), x) + Dist((A*b - B*a)/b, Int((a + b/sin(e + f*x))**m/sin(e + f*x), x), x)
    rule4394 = ReplacementRule(pattern4394, replacement4394)
    pattern4395 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1245, cons1265, cons31, cons1320)
    def replacement4395(B, m, f, b, a, A, x, e):
        rubi.append(4395)
        return Dist(S(1)/(b**S(2)*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(A*b*m - B*a*m + B*b*(S(2)*m + S(1))/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**m*(A*b - B*a)*tan(e + f*x)/(b*f*(S(2)*m + S(1))), x)
    rule4395 = ReplacementRule(pattern4395, replacement4395)
    pattern4396 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1245, cons1265, cons31, cons1320)
    def replacement4396(B, m, f, b, a, A, x, e):
        rubi.append(4396)
        return Dist(S(1)/(b**S(2)*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(A*b*m - B*a*m + B*b*(S(2)*m + S(1))/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**m*(A*b - B*a)/(b*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4396 = ReplacementRule(pattern4396, replacement4396)
    pattern4397 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1245, cons1267, cons31, cons94)
    def replacement4397(B, m, f, b, a, A, x, e):
        rubi.append(4397)
        return -Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(b*(m + S(1))*(A*b - B*a) - (A*a*b*(m + S(2)) - B*(a**S(2) + b**S(2)*(m + S(1))))/cos(e + f*x), x)/cos(e + f*x), x), x) - Simp(a*(a + b/cos(e + f*x))**(m + S(1))*(A*b - B*a)*tan(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4397 = ReplacementRule(pattern4397, replacement4397)
    pattern4398 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1245, cons1267, cons31, cons94)
    def replacement4398(B, m, f, b, a, A, x, e):
        rubi.append(4398)
        return -Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(b*(m + S(1))*(A*b - B*a) - (A*a*b*(m + S(2)) - B*(a**S(2) + b**S(2)*(m + S(1))))/sin(e + f*x), x)/sin(e + f*x), x), x) + Simp(a*(a + b/sin(e + f*x))**(m + S(1))*(A*b - B*a)/(b*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4398 = ReplacementRule(pattern4398, replacement4398)
    pattern4399 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons21, cons1245, cons272)
    def replacement4399(B, m, f, b, a, A, x, e):
        rubi.append(4399)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/cos(e + f*x))**m*Simp(B*b*(m + S(1)) + (A*b*(m + S(2)) - B*a)/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp(B*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + S(2))), x)
    rule4399 = ReplacementRule(pattern4399, replacement4399)
    pattern4400 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons21, cons1245, cons272)
    def replacement4400(B, m, f, b, a, A, x, e):
        rubi.append(4400)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/sin(e + f*x))**m*Simp(B*b*(m + S(1)) + (A*b*(m + S(2)) - B*a)/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp(B*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + S(2))*tan(e + f*x)), x)
    rule4400 = ReplacementRule(pattern4400, replacement4400)
    pattern4401 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons1245, cons1265, cons155, cons1627)
    def replacement4401(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4401)
        return -Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*n), x)
    rule4401 = ReplacementRule(pattern4401, replacement4401)
    pattern4402 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons1245, cons1265, cons155, cons1627)
    def replacement4402(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4402)
        return Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*n*tan(e + f*x)), x)
    rule4402 = ReplacementRule(pattern4402, replacement4402)
    pattern4403 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons155, cons31, cons32)
    def replacement4403(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4403)
        return Dist((A*a*m + B*b*(m + S(1)))/(a**S(2)*(S(2)*m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1)), x), x) + Simp((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*(A*b - B*a)*tan(e + f*x)/(b*f*(S(2)*m + S(1))), x)
    rule4403 = ReplacementRule(pattern4403, replacement4403)
    pattern4404 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons155, cons31, cons32)
    def replacement4404(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4404)
        return Dist((A*a*m + B*b*(m + S(1)))/(a**S(2)*(S(2)*m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1)), x), x) - Simp((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m*(A*b - B*a)/(b*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4404 = ReplacementRule(pattern4404, replacement4404)
    pattern4405 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons1245, cons1265, cons155, cons1549)
    def replacement4405(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4405)
        return -Dist((A*a*m - B*b*n)/(b*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**m, x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*n), x)
    rule4405 = ReplacementRule(pattern4405, replacement4405)
    pattern4406 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons1245, cons1265, cons155, cons1549)
    def replacement4406(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4406)
        return -Dist((A*a*m - B*b*n)/(b*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**m, x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*n*tan(e + f*x)), x)
    rule4406 = ReplacementRule(pattern4406, replacement4406)
    pattern4407 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons1628)
    def replacement4407(B, f, b, d, a, n, A, x, e):
        rubi.append(4407)
        return Simp(S(2)*B*b*(d/cos(e + f*x))**n*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(1))), x)
    rule4407 = ReplacementRule(pattern4407, replacement4407)
    pattern4408 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons1628)
    def replacement4408(B, f, b, d, a, n, A, x, e):
        rubi.append(4408)
        return Simp(-S(2)*B*b*(d/sin(e + f*x))**n/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(1))*tan(e + f*x)), x)
    rule4408 = ReplacementRule(pattern4408, replacement4408)
    pattern4409 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1265, cons1629, cons87, cons463)
    def replacement4409(B, f, b, d, a, n, A, x, e):
        rubi.append(4409)
        return Dist((A*b*(S(2)*n + S(1)) + S(2)*B*a*n)/(S(2)*a*d*n), Int((d/cos(e + f*x))**(n + S(1))*sqrt(a + b/cos(e + f*x)), x), x) - Simp(A*b**S(2)*(d/cos(e + f*x))**n*tan(e + f*x)/(a*f*n*sqrt(a + b/cos(e + f*x))), x)
    rule4409 = ReplacementRule(pattern4409, replacement4409)
    pattern4410 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1265, cons1629, cons87, cons463)
    def replacement4410(B, f, b, d, a, n, A, x, e):
        rubi.append(4410)
        return Dist((A*b*(S(2)*n + S(1)) + S(2)*B*a*n)/(S(2)*a*d*n), Int((d/sin(e + f*x))**(n + S(1))*sqrt(a + b/sin(e + f*x)), x), x) + Simp(A*b**S(2)*(d/sin(e + f*x))**n/(a*f*n*sqrt(a + b/sin(e + f*x))*tan(e + f*x)), x)
    rule4410 = ReplacementRule(pattern4410, replacement4410)
    pattern4411 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons1629, cons1231)
    def replacement4411(B, f, b, d, a, n, A, x, e):
        rubi.append(4411)
        return Dist((A*b*(S(2)*n + S(1)) + S(2)*B*a*n)/(b*(S(2)*n + S(1))), Int((d/cos(e + f*x))**n*sqrt(a + b/cos(e + f*x)), x), x) + Simp(S(2)*B*b*(d/cos(e + f*x))**n*tan(e + f*x)/(f*sqrt(a + b/cos(e + f*x))*(S(2)*n + S(1))), x)
    rule4411 = ReplacementRule(pattern4411, replacement4411)
    pattern4412 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons1629, cons1231)
    def replacement4412(B, f, b, d, a, n, A, x, e):
        rubi.append(4412)
        return Dist((A*b*(S(2)*n + S(1)) + S(2)*B*a*n)/(b*(S(2)*n + S(1))), Int((d/sin(e + f*x))**n*sqrt(a + b/sin(e + f*x)), x), x) + Simp(-S(2)*B*b*(d/sin(e + f*x))**n/(f*sqrt(a + b/sin(e + f*x))*(S(2)*n + S(1))*tan(e + f*x)), x)
    rule4412 = ReplacementRule(pattern4412, replacement4412)
    pattern4413 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1265, cons93, cons1423, cons89)
    def replacement4413(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4413)
        return -Dist(b/(a*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**(m + S(-1))*Simp(A*a*(m - n + S(-1)) - B*b*n - (A*b*(m + n) + B*a*n)/cos(e + f*x), x), x), x) - Simp(A*a*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*n), x)
    rule4413 = ReplacementRule(pattern4413, replacement4413)
    pattern4414 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1265, cons93, cons1423, cons89)
    def replacement4414(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4414)
        return -Dist(b/(a*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**(m + S(-1))*Simp(A*a*(m - n + S(-1)) - B*b*n - (A*b*(m + n) + B*a*n)/sin(e + f*x), x), x), x) + Simp(A*a*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-1))/(f*n*tan(e + f*x)), x)
    rule4414 = ReplacementRule(pattern4414, replacement4414)
    pattern4415 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons31, cons1423, cons346)
    def replacement4415(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4415)
        return Dist(S(1)/(d*(m + n)), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-1))*Simp(A*a*d*(m + n) + B*b*d*n + (A*b*d*(m + n) + B*a*d*(S(2)*m + n + S(-1)))/cos(e + f*x), x), x), x) + Simp(B*b*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*(m + n)), x)
    rule4415 = ReplacementRule(pattern4415, replacement4415)
    pattern4416 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons31, cons1423, cons346)
    def replacement4416(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4416)
        return Dist(S(1)/(d*(m + n)), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-1))*Simp(A*a*d*(m + n) + B*b*d*n + (A*b*d*(m + n) + B*a*d*(S(2)*m + n + S(-1)))/sin(e + f*x), x), x), x) - Simp(B*b*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-1))/(f*(m + n)*tan(e + f*x)), x)
    rule4416 = ReplacementRule(pattern4416, replacement4416)
    pattern4417 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1265, cons93, cons1320, cons88)
    def replacement4417(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4417)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*Simp(A*a*d*(n + S(-1)) - B*b*d*(n + S(-1)) - d*(A*b*(m + n) + B*a*(m - n + S(1)))/cos(e + f*x), x), x), x) - Simp(d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**m*(A*b - B*a)*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule4417 = ReplacementRule(pattern4417, replacement4417)
    pattern4418 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1265, cons93, cons1320, cons88)
    def replacement4418(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4418)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))*Simp(A*a*d*(n + S(-1)) - B*b*d*(n + S(-1)) - d*(A*b*(m + n) + B*a*(m - n + S(1)))/sin(e + f*x), x), x), x) + Simp(d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**m*(A*b - B*a)/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4418 = ReplacementRule(pattern4418, replacement4418)
    pattern4419 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons31, cons1320, cons1327)
    def replacement4419(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4419)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*Simp(-A*a*(S(2)*m + n + S(1)) + B*b*n + (A*b - B*a)*(m + n + S(1))/cos(e + f*x), x), x), x) + Simp((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*(A*b - B*a)*tan(e + f*x)/(b*f*(S(2)*m + S(1))), x)
    rule4419 = ReplacementRule(pattern4419, replacement4419)
    pattern4420 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1265, cons31, cons1320, cons1327)
    def replacement4420(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4420)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*Simp(-A*a*(S(2)*m + n + S(1)) + B*b*n + (A*b - B*a)*(m + n + S(1))/sin(e + f*x), x), x), x) - Simp((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m*(A*b - B*a)/(b*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4420 = ReplacementRule(pattern4420, replacement4420)
    pattern4421 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1265, cons87, cons165)
    def replacement4421(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4421)
        return Dist(d/(b*(m + n)), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**m*Simp(B*b*(n + S(-1)) + (A*b*(m + n) + B*a*m)/cos(e + f*x), x), x), x) + Simp(B*d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + n)), x)
    rule4421 = ReplacementRule(pattern4421, replacement4421)
    pattern4422 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1265, cons87, cons165)
    def replacement4422(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4422)
        return Dist(d/(b*(m + n)), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**m*Simp(B*b*(n + S(-1)) + (A*b*(m + n) + B*a*m)/sin(e + f*x), x), x), x) - Simp(B*d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**m/(f*(m + n)*tan(e + f*x)), x)
    rule4422 = ReplacementRule(pattern4422, replacement4422)
    pattern4423 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1265, cons87, cons463)
    def replacement4423(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4423)
        return -Dist(S(1)/(b*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**m*Simp(A*a*m - A*b*(m + n + S(1))/cos(e + f*x) - B*b*n, x), x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*n), x)
    rule4423 = ReplacementRule(pattern4423, replacement4423)
    pattern4424 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1265, cons87, cons463)
    def replacement4424(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4424)
        return -Dist(S(1)/(b*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**m*Simp(A*a*m - A*b*(m + n + S(1))/sin(e + f*x) - B*b*n, x), x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*n*tan(e + f*x)), x)
    rule4424 = ReplacementRule(pattern4424, replacement4424)
    pattern4425 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1265)
    def replacement4425(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4425)
        return Dist(B/b, Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1)), x), x) + Dist((A*b - B*a)/b, Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m, x), x)
    rule4425 = ReplacementRule(pattern4425, replacement4425)
    pattern4426 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1265)
    def replacement4426(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4426)
        return Dist(B/b, Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1)), x), x) + Dist((A*b - B*a)/b, Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m, x), x)
    rule4426 = ReplacementRule(pattern4426, replacement4426)
    pattern4427 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons166, cons1586)
    def replacement4427(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4427)
        return Dist(S(1)/(d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**(m + S(-2))*Simp(a*(-A*b*(m - n + S(-1)) + B*a*n) + b*(A*a*(m + n) + B*b*n)/cos(e + f*x)**S(2) + (A*(a**S(2)*(n + S(1)) + b**S(2)*n) + S(2)*B*a*b*n)/cos(e + f*x), x), x), x) - Simp(A*a*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*n), x)
    rule4427 = ReplacementRule(pattern4427, replacement4427)
    pattern4428 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons166, cons1586)
    def replacement4428(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4428)
        return Dist(S(1)/(d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**(m + S(-2))*Simp(a*(-A*b*(m - n + S(-1)) + B*a*n) + b*(A*a*(m + n) + B*b*n)/sin(e + f*x)**S(2) + (A*(a**S(2)*(n + S(1)) + b**S(2)*n) + S(2)*B*a*b*n)/sin(e + f*x), x), x), x) + Simp(A*a*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-1))/(f*n*tan(e + f*x)), x)
    rule4428 = ReplacementRule(pattern4428, replacement4428)
    pattern4429 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1267, cons31, cons166, cons1630)
    def replacement4429(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4429)
        return Dist(S(1)/(m + n), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-2))*Simp(A*a**S(2)*(m + n) + B*a*b*n + b*(A*b*(m + n) + B*a*(S(2)*m + n + S(-1)))/cos(e + f*x)**S(2) + (B*b**S(2)*(m + n + S(-1)) + a*(m + n)*(S(2)*A*b + B*a))/cos(e + f*x), x), x), x) + Simp(B*b*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-1))*tan(e + f*x)/(f*(m + n)), x)
    rule4429 = ReplacementRule(pattern4429, replacement4429)
    pattern4430 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1267, cons31, cons166, cons1630)
    def replacement4430(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4430)
        return Dist(S(1)/(m + n), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-2))*Simp(A*a**S(2)*(m + n) + B*a*b*n + b*(A*b*(m + n) + B*a*(S(2)*m + n + S(-1)))/sin(e + f*x)**S(2) + (B*b**S(2)*(m + n + S(-1)) + a*(m + n)*(S(2)*A*b + B*a))/sin(e + f*x), x), x), x) - Simp(B*b*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-1))/(f*(m + n)*tan(e + f*x)), x)
    rule4430 = ReplacementRule(pattern4430, replacement4430)
    pattern4431 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons94, cons1325)
    def replacement4431(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4431)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*Simp(d*(m + S(1))*(A*a - B*b)/cos(e + f*x) + d*(n + S(-1))*(A*b - B*a) - d*(A*b - B*a)*(m + n + S(1))/cos(e + f*x)**S(2), x), x), x) + Simp(d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*(A*b - B*a)*tan(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4431 = ReplacementRule(pattern4431, replacement4431)
    pattern4432 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons94, cons1325)
    def replacement4432(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4432)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))*Simp(d*(m + S(1))*(A*a - B*b)/sin(e + f*x) + d*(n + S(-1))*(A*b - B*a) - d*(A*b - B*a)*(m + n + S(1))/sin(e + f*x)**S(2), x), x), x) - Simp(d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))*(A*b - B*a)/(f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4432 = ReplacementRule(pattern4432, replacement4432)
    pattern4433 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons94, cons165)
    def replacement4433(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4433)
        return -Dist(d/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**(m + S(1))*Simp(a*d*(n + S(-2))*(A*b - B*a) + b*d*(m + S(1))*(A*b - B*a)/cos(e + f*x) - (A*a*b*d*(m + n) - B*d*(a**S(2)*(n + S(-1)) + b**S(2)*(m + S(1))))/cos(e + f*x)**S(2), x), x), x) - Simp(a*d**S(2)*(d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**(m + S(1))*(A*b - B*a)*tan(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4433 = ReplacementRule(pattern4433, replacement4433)
    pattern4434 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons94, cons165)
    def replacement4434(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4434)
        return -Dist(d/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**(m + S(1))*Simp(a*d*(n + S(-2))*(A*b - B*a) + b*d*(m + S(1))*(A*b - B*a)/sin(e + f*x) - (A*a*b*d*(m + n) - B*d*(a**S(2)*(n + S(-1)) + b**S(2)*(m + S(1))))/sin(e + f*x)**S(2), x), x), x) + Simp(a*d**S(2)*(d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**(m + S(1))*(A*b - B*a)/(b*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4434 = ReplacementRule(pattern4434, replacement4434)
    pattern4435 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1267, cons31, cons94, cons1631)
    def replacement4435(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4435)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*Simp(A*(a**S(2)*(m + S(1)) - b**S(2)*(m + n + S(1))) + B*a*b*n - a*(m + S(1))*(A*b - B*a)/cos(e + f*x) + b*(A*b - B*a)*(m + n + S(2))/cos(e + f*x)**S(2), x), x), x) - Simp(b*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*(A*b - B*a)*tan(e + f*x)/(a*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4435 = ReplacementRule(pattern4435, replacement4435)
    pattern4436 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1267, cons31, cons94, cons1631)
    def replacement4436(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4436)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*Simp(A*(a**S(2)*(m + S(1)) - b**S(2)*(m + n + S(1))) + B*a*b*n - a*(m + S(1))*(A*b - B*a)/sin(e + f*x) + b*(A*b - B*a)*(m + n + S(2))/sin(e + f*x)**S(2), x), x), x) + Simp(b*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*(A*b - B*a)/(a*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4436 = ReplacementRule(pattern4436, replacement4436)
    pattern4437 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons1256, cons88)
    def replacement4437(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4437)
        return Dist(d/(m + n), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(-1))*Simp(B*a*(n + S(-1)) + (A*a*(m + n) + B*b*(m + n + S(-1)))/cos(e + f*x) + (A*b*(m + n) + B*a*m)/cos(e + f*x)**S(2), x), x), x) + Simp(B*d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + n)), x)
    rule4437 = ReplacementRule(pattern4437, replacement4437)
    pattern4438 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons1256, cons88)
    def replacement4438(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4438)
        return Dist(d/(m + n), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(-1))*Simp(B*a*(n + S(-1)) + (A*a*(m + n) + B*b*(m + n + S(-1)))/sin(e + f*x) + (A*b*(m + n) + B*a*m)/sin(e + f*x)**S(2), x), x), x) - Simp(B*d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**m/(f*(m + n)*tan(e + f*x)), x)
    rule4438 = ReplacementRule(pattern4438, replacement4438)
    pattern4439 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons1256, cons1586)
    def replacement4439(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4439)
        return -Dist(S(1)/(d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**(m + S(-1))*Simp(A*b*m - A*b*(m + n + S(1))/cos(e + f*x)**S(2) - B*a*n - (A*a*(n + S(1)) + B*b*n)/cos(e + f*x), x), x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*n), x)
    rule4439 = ReplacementRule(pattern4439, replacement4439)
    pattern4440 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267, cons93, cons1256, cons1586)
    def replacement4440(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4440)
        return -Dist(S(1)/(d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**(m + S(-1))*Simp(A*b*m - A*b*(m + n + S(1))/sin(e + f*x)**S(2) - B*a*n - (A*a*(n + S(1)) + B*b*n)/sin(e + f*x), x), x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*n*tan(e + f*x)), x)
    rule4440 = ReplacementRule(pattern4440, replacement4440)
    pattern4441 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1267, cons87, cons165, cons1359, cons1632)
    def replacement4441(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4441)
        return Dist(d**S(2)/(b*(m + n)), Int((d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**m*Simp(B*a*(n + S(-2)) + B*b*(m + n + S(-1))/cos(e + f*x) + (A*b*(m + n) - B*a*(n + S(-1)))/cos(e + f*x)**S(2), x), x), x) + Simp(B*d**S(2)*(d/cos(e + f*x))**(n + S(-2))*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + n)), x)
    rule4441 = ReplacementRule(pattern4441, replacement4441)
    pattern4442 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1267, cons87, cons165, cons1359, cons1632)
    def replacement4442(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4442)
        return Dist(d**S(2)/(b*(m + n)), Int((d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**m*Simp(B*a*(n + S(-2)) + B*b*(m + n + S(-1))/sin(e + f*x) + (A*b*(m + n) - B*a*(n + S(-1)))/sin(e + f*x)**S(2), x), x), x) - Simp(B*d**S(2)*(d/sin(e + f*x))**(n + S(-2))*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + n)*tan(e + f*x)), x)
    rule4442 = ReplacementRule(pattern4442, replacement4442)
    pattern4443 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1267, cons87, cons1586)
    def replacement4443(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4443)
        return Dist(S(1)/(a*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**m*Simp(A*a*(n + S(1))/cos(e + f*x) - A*b*(m + n + S(1)) + A*b*(m + n + S(2))/cos(e + f*x)**S(2) + B*a*n, x), x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(a*f*n), x)
    rule4443 = ReplacementRule(pattern4443, replacement4443)
    pattern4444 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons1245, cons1267, cons87, cons1586)
    def replacement4444(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4444)
        return Dist(S(1)/(a*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**m*Simp(A*a*(n + S(1))/sin(e + f*x) - A*b*(m + n + S(1)) + A*b*(m + n + S(2))/sin(e + f*x)**S(2) + B*a*n, x), x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))/(a*f*n*tan(e + f*x)), x)
    rule4444 = ReplacementRule(pattern4444, replacement4444)
    pattern4445 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267)
    def replacement4445(B, f, b, d, a, A, x, e):
        rubi.append(4445)
        return Dist(A/a, Int(sqrt(a + b/cos(e + f*x))/sqrt(d/cos(e + f*x)), x), x) - Dist((A*b - B*a)/(a*d), Int(sqrt(d/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x)
    rule4445 = ReplacementRule(pattern4445, replacement4445)
    pattern4446 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267)
    def replacement4446(B, f, b, d, a, A, x, e):
        rubi.append(4446)
        return Dist(A/a, Int(sqrt(a + b/sin(e + f*x))/sqrt(d/sin(e + f*x)), x), x) - Dist((A*b - B*a)/(a*d), Int(sqrt(d/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x)
    rule4446 = ReplacementRule(pattern4446, replacement4446)
    pattern4447 = Pattern(Integral(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267)
    def replacement4447(B, f, b, d, a, A, x, e):
        rubi.append(4447)
        return Dist(A, Int(sqrt(d/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x), x) + Dist(B/d, Int((d/cos(e + f*x))**(S(3)/2)/sqrt(a + b/cos(e + f*x)), x), x)
    rule4447 = ReplacementRule(pattern4447, replacement4447)
    pattern4448 = Pattern(Integral(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267)
    def replacement4448(B, f, b, d, a, A, x, e):
        rubi.append(4448)
        return Dist(A, Int(sqrt(d/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x), x) + Dist(B/d, Int((d/sin(e + f*x))**(S(3)/2)/sqrt(a + b/sin(e + f*x)), x), x)
    rule4448 = ReplacementRule(pattern4448, replacement4448)
    pattern4449 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267)
    def replacement4449(B, f, b, d, a, A, x, e):
        rubi.append(4449)
        return Dist(A, Int(sqrt(a + b/cos(e + f*x))/sqrt(d/cos(e + f*x)), x), x) + Dist(B/d, Int(sqrt(d/cos(e + f*x))*sqrt(a + b/cos(e + f*x)), x), x)
    rule4449 = ReplacementRule(pattern4449, replacement4449)
    pattern4450 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1245, cons1267)
    def replacement4450(B, f, b, d, a, A, x, e):
        rubi.append(4450)
        return Dist(A, Int(sqrt(a + b/sin(e + f*x))/sqrt(d/sin(e + f*x)), x), x) + Dist(B/d, Int(sqrt(d/sin(e + f*x))*sqrt(a + b/sin(e + f*x)), x), x)
    rule4450 = ReplacementRule(pattern4450, replacement4450)
    pattern4451 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1267)
    def replacement4451(B, f, b, d, a, n, A, x, e):
        rubi.append(4451)
        return Dist(A/a, Int((d/cos(e + f*x))**n, x), x) - Dist((A*b - B*a)/(a*d), Int((d/cos(e + f*x))**(n + S(1))/(a + b/cos(e + f*x)), x), x)
    rule4451 = ReplacementRule(pattern4451, replacement4451)
    pattern4452 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons4, cons1245, cons1267)
    def replacement4452(B, f, b, d, a, n, A, x, e):
        rubi.append(4452)
        return Dist(A/a, Int((d/sin(e + f*x))**n, x), x) - Dist((A*b - B*a)/(a*d), Int((d/sin(e + f*x))**(n + S(1))/(a + b/sin(e + f*x)), x), x)
    rule4452 = ReplacementRule(pattern4452, replacement4452)
    pattern4453 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons1245, cons1267)
    def replacement4453(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4453)
        return Int((d/cos(e + f*x))**n*(A + B/cos(e + f*x))*(a + b/cos(e + f*x))**m, x)
    rule4453 = ReplacementRule(pattern4453, replacement4453)
    pattern4454 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons1245, cons1267)
    def replacement4454(B, m, f, b, d, a, n, A, x, e):
        rubi.append(4454)
        return Int((d/sin(e + f*x))**n*(A + B/sin(e + f*x))*(a + b/sin(e + f*x))**m, x)
    rule4454 = ReplacementRule(pattern4454, replacement4454)
    pattern4455 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons5, cons70, cons1265, cons375)
    def replacement4455(B, p, e, m, f, b, d, a, n, c, x, A):
        rubi.append(4455)
        return Dist((-a*c)**m, Int((A*cos(e + f*x) + B)**p*(c*cos(e + f*x) + d)**(-m + n)*sin(e + f*x)**(S(2)*m)*cos(e + f*x)**(-m - n - p), x), x)
    rule4455 = ReplacementRule(pattern4455, replacement4455)
    pattern4456 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons5, cons70, cons1265, cons375)
    def replacement4456(B, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(4456)
        return Dist((-a*c)**m, Int((A*sin(e + f*x) + B)**p*(c*sin(e + f*x) + d)**(-m + n)*sin(e + f*x)**(-m - n - p)*cos(e + f*x)**(S(2)*m), x), x)
    rule4456 = ReplacementRule(pattern4456, replacement4456)
    pattern4457 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons33)
    def replacement4457(B, C, e, m, f, b, a, x, A):
        rubi.append(4457)
        return Dist(b**(S(-2)), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(B*b - C*a + C*b/cos(e + f*x), x), x), x)
    rule4457 = ReplacementRule(pattern4457, replacement4457)
    pattern4458 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons33)
    def replacement4458(B, C, m, f, b, a, A, x, e):
        rubi.append(4458)
        return Dist(b**(S(-2)), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(B*b - C*a + C*b/sin(e + f*x), x), x), x)
    rule4458 = ReplacementRule(pattern4458, replacement4458)
    pattern4459 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1433)
    def replacement4459(C, e, m, f, b, a, x, A):
        rubi.append(4459)
        return Dist(C/b**S(2), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(-a + b/cos(e + f*x), x), x), x)
    rule4459 = ReplacementRule(pattern4459, replacement4459)
    pattern4460 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1433)
    def replacement4460(C, m, f, b, a, A, x, e):
        rubi.append(4460)
        return Dist(C/b**S(2), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(-a + b/sin(e + f*x), x), x), x)
    rule4460 = ReplacementRule(pattern4460, replacement4460)
    pattern4461 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons1633)
    def replacement4461(C, m, f, b, A, x, e):
        rubi.append(4461)
        return -Simp(A*(b/cos(e + f*x))**m*tan(e + f*x)/(f*m), x)
    rule4461 = ReplacementRule(pattern4461, replacement4461)
    pattern4462 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons1633)
    def replacement4462(C, m, f, b, A, x, e):
        rubi.append(4462)
        return Simp(A*(b/sin(e + f*x))**m/(f*m*tan(e + f*x)), x)
    rule4462 = ReplacementRule(pattern4462, replacement4462)
    pattern4463 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons1634, cons31, cons32)
    def replacement4463(C, m, f, b, A, x, e):
        rubi.append(4463)
        return Dist((A*(m + S(1)) + C*m)/(b**S(2)*m), Int((b/cos(e + f*x))**(m + S(2)), x), x) - Simp(A*(b/cos(e + f*x))**m*tan(e + f*x)/(f*m), x)
    rule4463 = ReplacementRule(pattern4463, replacement4463)
    pattern4464 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons1634, cons31, cons32)
    def replacement4464(C, m, f, b, A, x, e):
        rubi.append(4464)
        return Dist((A*(m + S(1)) + C*m)/(b**S(2)*m), Int((b/sin(e + f*x))**(m + S(2)), x), x) + Simp(A*(b/sin(e + f*x))**m/(f*m*tan(e + f*x)), x)
    rule4464 = ReplacementRule(pattern4464, replacement4464)
    pattern4465 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons1634, cons1549)
    def replacement4465(C, m, f, b, A, x, e):
        rubi.append(4465)
        return Dist((A*(m + S(1)) + C*m)/(m + S(1)), Int((b/cos(e + f*x))**m, x), x) + Simp(C*(b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4465 = ReplacementRule(pattern4465, replacement4465)
    pattern4466 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons1634, cons1549)
    def replacement4466(C, m, f, b, A, x, e):
        rubi.append(4466)
        return Dist((A*(m + S(1)) + C*m)/(m + S(1)), Int((b/sin(e + f*x))**m, x), x) - Simp(C*(b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4466 = ReplacementRule(pattern4466, replacement4466)
    pattern4467 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons35, cons36, cons21, cons1431)
    def replacement4467(B, C, m, f, b, x, e):
        rubi.append(4467)
        return Dist(B/b, Int((b/cos(e + f*x))**(m + S(1)), x), x) + Dist(C/b**S(2), Int((b/cos(e + f*x))**(m + S(2)), x), x)
    rule4467 = ReplacementRule(pattern4467, replacement4467)
    pattern4468 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons35, cons36, cons21, cons1431)
    def replacement4468(B, C, m, f, b, x, e):
        rubi.append(4468)
        return Dist(B/b, Int((b/sin(e + f*x))**(m + S(1)), x), x) + Dist(C/b**S(2), Int((b/sin(e + f*x))**(m + S(2)), x), x)
    rule4468 = ReplacementRule(pattern4468, replacement4468)
    pattern4469 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1635)
    def replacement4469(B, C, m, f, b, A, x, e):
        rubi.append(4469)
        return Dist(B/b, Int((b/cos(e + f*x))**(m + S(1)), x), x) + Int((b/cos(e + f*x))**m*(A + C/cos(e + f*x)**S(2)), x)
    rule4469 = ReplacementRule(pattern4469, replacement4469)
    pattern4470 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1635)
    def replacement4470(B, C, m, f, b, A, x, e):
        rubi.append(4470)
        return Dist(B/b, Int((b/sin(e + f*x))**(m + S(1)), x), x) + Int((b/sin(e + f*x))**m*(A + C/sin(e + f*x)**S(2)), x)
    rule4470 = ReplacementRule(pattern4470, replacement4470)
    pattern4471 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1636)
    def replacement4471(B, C, e, f, b, a, x, A):
        rubi.append(4471)
        return Dist(S(1)/2, Int(Simp(S(2)*A*a + (S(2)*B*a + b*(S(2)*A + C))/cos(e + f*x) + S(2)*(B*b + C*a)/cos(e + f*x)**S(2), x), x), x) + Simp(C*b*tan(e + f*x)/(S(2)*f*cos(e + f*x)), x)
    rule4471 = ReplacementRule(pattern4471, replacement4471)
    pattern4472 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1636)
    def replacement4472(B, C, f, b, a, A, x, e):
        rubi.append(4472)
        return Dist(S(1)/2, Int(Simp(S(2)*A*a + (S(2)*B*a + b*(S(2)*A + C))/sin(e + f*x) + S(2)*(B*b + C*a)/sin(e + f*x)**S(2), x), x), x) - Simp(C*b/(S(2)*f*sin(e + f*x)*tan(e + f*x)), x)
    rule4472 = ReplacementRule(pattern4472, replacement4472)
    pattern4473 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1637)
    def replacement4473(C, e, f, b, a, x, A):
        rubi.append(4473)
        return Dist(S(1)/2, Int(Simp(S(2)*A*a + S(2)*C*a/cos(e + f*x)**S(2) + b*(S(2)*A + C)/cos(e + f*x), x), x), x) + Simp(C*b*tan(e + f*x)/(S(2)*f*cos(e + f*x)), x)
    rule4473 = ReplacementRule(pattern4473, replacement4473)
    pattern4474 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1637)
    def replacement4474(C, f, b, a, A, x, e):
        rubi.append(4474)
        return Dist(S(1)/2, Int(Simp(S(2)*A*a + S(2)*C*a/sin(e + f*x)**S(2) + b*(S(2)*A + C)/sin(e + f*x), x), x), x) - Simp(C*b/(S(2)*f*sin(e + f*x)*tan(e + f*x)), x)
    rule4474 = ReplacementRule(pattern4474, replacement4474)
    pattern4475 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1636)
    def replacement4475(B, C, e, f, b, a, x, A):
        rubi.append(4475)
        return Dist(S(1)/b, Int((A*b + (B*b - C*a)/cos(e + f*x))/(a + b/cos(e + f*x)), x), x) + Dist(C/b, Int(S(1)/cos(e + f*x), x), x)
    rule4475 = ReplacementRule(pattern4475, replacement4475)
    pattern4476 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1636)
    def replacement4476(B, C, f, b, a, A, x, e):
        rubi.append(4476)
        return Dist(S(1)/b, Int((A*b + (B*b - C*a)/sin(e + f*x))/(a + b/sin(e + f*x)), x), x) + Dist(C/b, Int(S(1)/sin(e + f*x), x), x)
    rule4476 = ReplacementRule(pattern4476, replacement4476)
    pattern4477 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1637)
    def replacement4477(C, e, f, b, a, x, A):
        rubi.append(4477)
        return Dist(S(1)/b, Int((A*b - C*a/cos(e + f*x))/(a + b/cos(e + f*x)), x), x) + Dist(C/b, Int(S(1)/cos(e + f*x), x), x)
    rule4477 = ReplacementRule(pattern4477, replacement4477)
    pattern4478 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1637)
    def replacement4478(C, f, b, a, A, x, e):
        rubi.append(4478)
        return Dist(S(1)/b, Int((A*b - C*a/sin(e + f*x))/(a + b/sin(e + f*x)), x), x) + Dist(C/b, Int(S(1)/sin(e + f*x), x), x)
    rule4478 = ReplacementRule(pattern4478, replacement4478)
    pattern4479 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1265, cons31, cons1320)
    def replacement4479(B, C, e, m, f, b, a, x, A):
        rubi.append(4479)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(A*b*(S(2)*m + S(1)) + (B*b*(m + S(1)) - a*(A*(m + S(1)) - C*m))/cos(e + f*x), x), x), x) + Simp((a + b/cos(e + f*x))**m*(A*a - B*b + C*a)*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule4479 = ReplacementRule(pattern4479, replacement4479)
    pattern4480 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1265, cons31, cons1320)
    def replacement4480(B, C, m, f, b, a, A, x, e):
        rubi.append(4480)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(A*b*(S(2)*m + S(1)) + (B*b*(m + S(1)) - a*(A*(m + S(1)) - C*m))/sin(e + f*x), x), x), x) - Simp((a + b/sin(e + f*x))**m*(A*a - B*b + C*a)/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4480 = ReplacementRule(pattern4480, replacement4480)
    pattern4481 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1265, cons31, cons1320)
    def replacement4481(C, e, m, f, b, a, x, A):
        rubi.append(4481)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(A*b*(S(2)*m + S(1)) - a*(A*(m + S(1)) - C*m)/cos(e + f*x), x), x), x) + Simp((A + C)*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(S(2)*m + S(1))), x)
    rule4481 = ReplacementRule(pattern4481, replacement4481)
    pattern4482 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1265, cons31, cons1320)
    def replacement4482(C, m, f, b, a, A, x, e):
        rubi.append(4482)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(A*b*(S(2)*m + S(1)) - a*(A*(m + S(1)) - C*m)/sin(e + f*x), x), x), x) - Simp((A + C)*(a + b/sin(e + f*x))**m/(f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4482 = ReplacementRule(pattern4482, replacement4482)
    pattern4483 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1265, cons1321)
    def replacement4483(B, C, e, m, f, b, a, x, A):
        rubi.append(4483)
        return Dist(S(1)/(b*(m + S(1))), Int((a + b/cos(e + f*x))**m*Simp(A*b*(m + S(1)) + (B*b*(m + S(1)) + C*a*m)/cos(e + f*x), x), x), x) + Simp(C*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4483 = ReplacementRule(pattern4483, replacement4483)
    pattern4484 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1265, cons1321)
    def replacement4484(B, C, m, f, b, a, A, x, e):
        rubi.append(4484)
        return Dist(S(1)/(b*(m + S(1))), Int((a + b/sin(e + f*x))**m*Simp(A*b*(m + S(1)) + (B*b*(m + S(1)) + C*a*m)/sin(e + f*x), x), x), x) - Simp(C*(a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4484 = ReplacementRule(pattern4484, replacement4484)
    pattern4485 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1265, cons1321)
    def replacement4485(C, e, m, f, b, a, x, A):
        rubi.append(4485)
        return Dist(S(1)/(b*(m + S(1))), Int((a + b/cos(e + f*x))**m*Simp(A*b*(m + S(1)) + C*a*m/cos(e + f*x), x), x), x) + Simp(C*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4485 = ReplacementRule(pattern4485, replacement4485)
    pattern4486 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1265, cons1321)
    def replacement4486(C, m, f, b, a, A, x, e):
        rubi.append(4486)
        return Dist(S(1)/(b*(m + S(1))), Int((a + b/sin(e + f*x))**m*Simp(A*b*(m + S(1)) + C*a*m/sin(e + f*x), x), x), x) - Simp(C*(a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4486 = ReplacementRule(pattern4486, replacement4486)
    pattern4487 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1267, cons1638)
    def replacement4487(B, C, e, m, f, b, a, x, A):
        rubi.append(4487)
        return Dist(S(1)/(m + S(1)), Int((a + b/cos(e + f*x))**(m + S(-1))*Simp(A*a*(m + S(1)) + (B*b*(m + S(1)) + C*a*m)/cos(e + f*x)**S(2) + (C*b*m + (m + S(1))*(A*b + B*a))/cos(e + f*x), x), x), x) + Simp(C*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4487 = ReplacementRule(pattern4487, replacement4487)
    pattern4488 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1267, cons1638)
    def replacement4488(B, C, m, f, b, a, A, x, e):
        rubi.append(4488)
        return Dist(S(1)/(m + S(1)), Int((a + b/sin(e + f*x))**(m + S(-1))*Simp(A*a*(m + S(1)) + (B*b*(m + S(1)) + C*a*m)/sin(e + f*x)**S(2) + (C*b*m + (m + S(1))*(A*b + B*a))/sin(e + f*x), x), x), x) - Simp(C*(a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4488 = ReplacementRule(pattern4488, replacement4488)
    pattern4489 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1267, cons1638)
    def replacement4489(C, e, m, f, b, a, x, A):
        rubi.append(4489)
        return Dist(S(1)/(m + S(1)), Int((a + b/cos(e + f*x))**(m + S(-1))*Simp(A*a*(m + S(1)) + C*a*m/cos(e + f*x)**S(2) + (A*b*(m + S(1)) + C*b*m)/cos(e + f*x), x), x), x) + Simp(C*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + S(1))), x)
    rule4489 = ReplacementRule(pattern4489, replacement4489)
    pattern4490 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1267, cons1638)
    def replacement4490(C, m, f, b, a, A, x, e):
        rubi.append(4490)
        return Dist(S(1)/(m + S(1)), Int((a + b/sin(e + f*x))**(m + S(-1))*Simp(A*a*(m + S(1)) + C*a*m/sin(e + f*x)**S(2) + (A*b*(m + S(1)) + C*b*m)/sin(e + f*x), x), x), x) - Simp(C*(a + b/sin(e + f*x))**m/(f*(m + S(1))*tan(e + f*x)), x)
    rule4490 = ReplacementRule(pattern4490, replacement4490)
    pattern4491 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1267)
    def replacement4491(B, C, e, f, b, a, x, A):
        rubi.append(4491)
        return Dist(C, Int((S(1) + S(1)/cos(e + f*x))/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) + Int((A + (B - C)/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x)
    rule4491 = ReplacementRule(pattern4491, replacement4491)
    pattern4492 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1267)
    def replacement4492(B, C, f, b, a, A, x, e):
        rubi.append(4492)
        return Dist(C, Int((S(1) + S(1)/sin(e + f*x))/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) + Int((A + (B - C)/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x)
    rule4492 = ReplacementRule(pattern4492, replacement4492)
    pattern4493 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1267)
    def replacement4493(C, e, f, b, a, x, A):
        rubi.append(4493)
        return Dist(C, Int((S(1) + S(1)/cos(e + f*x))/(sqrt(a + b/cos(e + f*x))*cos(e + f*x)), x), x) + Int((A - C/cos(e + f*x))/sqrt(a + b/cos(e + f*x)), x)
    rule4493 = ReplacementRule(pattern4493, replacement4493)
    pattern4494 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1267)
    def replacement4494(C, f, b, a, A, x, e):
        rubi.append(4494)
        return Dist(C, Int((S(1) + S(1)/sin(e + f*x))/(sqrt(a + b/sin(e + f*x))*sin(e + f*x)), x), x) + Int((A - C/sin(e + f*x))/sqrt(a + b/sin(e + f*x)), x)
    rule4494 = ReplacementRule(pattern4494, replacement4494)
    pattern4495 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1267, cons515, cons94)
    def replacement4495(B, C, e, m, f, b, a, x, A):
        rubi.append(4495)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(A*(a**S(2) - b**S(2))*(m + S(1)) - a*(m + S(1))*(A*b - B*a + C*b)/cos(e + f*x) + (m + S(2))*(A*b**S(2) - B*a*b + C*a**S(2))/cos(e + f*x)**S(2), x), x), x) - Simp((a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))*tan(e + f*x)/(a*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4495 = ReplacementRule(pattern4495, replacement4495)
    pattern4496 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1267, cons31, cons94)
    def replacement4496(B, C, m, f, b, a, A, x, e):
        rubi.append(4496)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(A*(a**S(2) - b**S(2))*(m + S(1)) - a*(m + S(1))*(A*b - B*a + C*b)/sin(e + f*x) + (m + S(2))*(A*b**S(2) - B*a*b + C*a**S(2))/sin(e + f*x)**S(2), x), x), x) + Simp((a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))/(a*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4496 = ReplacementRule(pattern4496, replacement4496)
    pattern4497 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1267, cons515, cons94)
    def replacement4497(C, e, m, f, b, a, x, A):
        rubi.append(4497)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(A*(a**S(2) - b**S(2))*(m + S(1)) - a*b*(A + C)*(m + S(1))/cos(e + f*x) + (m + S(2))*(A*b**S(2) + C*a**S(2))/cos(e + f*x)**S(2), x), x), x) - Simp((a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))*tan(e + f*x)/(a*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4497 = ReplacementRule(pattern4497, replacement4497)
    pattern4498 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1267, cons515, cons94)
    def replacement4498(C, m, f, b, a, A, x, e):
        rubi.append(4498)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(A*(a**S(2) - b**S(2))*(m + S(1)) - a*b*(A + C)*(m + S(1))/sin(e + f*x) + (m + S(2))*(A*b**S(2) + C*a**S(2))/sin(e + f*x)**S(2), x), x), x) + Simp((a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))/(a*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4498 = ReplacementRule(pattern4498, replacement4498)
    pattern4499 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1267, cons77)
    def replacement4499(B, C, e, m, f, b, a, x, A):
        rubi.append(4499)
        return Dist(S(1)/b, Int((a + b/cos(e + f*x))**m*(A*b + (B*b - C*a)/cos(e + f*x)), x), x) + Dist(C/b, Int((a + b/cos(e + f*x))**(m + S(1))/cos(e + f*x), x), x)
    rule4499 = ReplacementRule(pattern4499, replacement4499)
    pattern4500 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1267, cons77)
    def replacement4500(B, C, m, f, b, a, A, x, e):
        rubi.append(4500)
        return Dist(S(1)/b, Int((a + b/sin(e + f*x))**m*(A*b + (B*b - C*a)/sin(e + f*x)), x), x) + Dist(C/b, Int((a + b/sin(e + f*x))**(m + S(1))/sin(e + f*x), x), x)
    rule4500 = ReplacementRule(pattern4500, replacement4500)
    pattern4501 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1267, cons77)
    def replacement4501(C, e, m, f, b, a, x, A):
        rubi.append(4501)
        return Dist(S(1)/b, Int((a + b/cos(e + f*x))**m*(A*b - C*a/cos(e + f*x)), x), x) + Dist(C/b, Int((a + b/cos(e + f*x))**(m + S(1))/cos(e + f*x), x), x)
    rule4501 = ReplacementRule(pattern4501, replacement4501)
    pattern4502 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1267, cons77)
    def replacement4502(C, m, f, b, a, A, x, e):
        rubi.append(4502)
        return Dist(S(1)/b, Int((a + b/sin(e + f*x))**m*(A*b - C*a/sin(e + f*x)), x), x) + Dist(C/b, Int((a + b/sin(e + f*x))**(m + S(1))/sin(e + f*x), x), x)
    rule4502 = ReplacementRule(pattern4502, replacement4502)
    pattern4503 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons18)
    def replacement4503(B, C, e, m, f, b, x, A):
        rubi.append(4503)
        return Dist(b**S(2), Int((b*cos(e + f*x))**(m + S(-2))*(A*cos(e + f*x)**S(2) + B*cos(e + f*x) + C), x), x)
    rule4503 = ReplacementRule(pattern4503, replacement4503)
    pattern4504 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons18)
    def replacement4504(B, C, e, m, f, b, x, A):
        rubi.append(4504)
        return Dist(b**S(2), Int((b*sin(e + f*x))**(m + S(-2))*(A*sin(e + f*x)**S(2) + B*sin(e + f*x) + C), x), x)
    rule4504 = ReplacementRule(pattern4504, replacement4504)
    pattern4505 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons18)
    def replacement4505(C, e, m, f, b, x, A):
        rubi.append(4505)
        return Dist(b**S(2), Int((b*cos(e + f*x))**(m + S(-2))*(A*cos(e + f*x)**S(2) + C), x), x)
    rule4505 = ReplacementRule(pattern4505, replacement4505)
    pattern4506 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons18)
    def replacement4506(C, e, m, f, b, x, A):
        rubi.append(4506)
        return Dist(b**S(2), Int((b*sin(e + f*x))**(m + S(-2))*(A*sin(e + f*x)**S(2) + C), x), x)
    rule4506 = ReplacementRule(pattern4506, replacement4506)
    pattern4507 = Pattern(Integral(((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('a', S(1)))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons5, cons18)
    def replacement4507(B, C, e, p, m, f, b, a, x, A):
        rubi.append(4507)
        return Dist(a**IntPart(m)*(a*(b/cos(e + f*x))**p)**FracPart(m)*(b/cos(e + f*x))**(-p*FracPart(m)), Int((b/cos(e + f*x))**(m*p)*(A + B/cos(e + f*x) + C/cos(e + f*x)**S(2)), x), x)
    rule4507 = ReplacementRule(pattern4507, replacement4507)
    pattern4508 = Pattern(Integral(((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('a', S(1)))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons5, cons18)
    def replacement4508(B, C, e, p, m, f, b, a, x, A):
        rubi.append(4508)
        return Dist(a**IntPart(m)*(a*(b/sin(e + f*x))**p)**FracPart(m)*(b/sin(e + f*x))**(-p*FracPart(m)), Int((b/sin(e + f*x))**(m*p)*(A + B/sin(e + f*x) + C/sin(e + f*x)**S(2)), x), x)
    rule4508 = ReplacementRule(pattern4508, replacement4508)
    pattern4509 = Pattern(Integral(((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('a', S(1)))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons5, cons18)
    def replacement4509(C, e, p, m, f, b, a, x, A):
        rubi.append(4509)
        return Dist(a**IntPart(m)*(a*(b/cos(e + f*x))**p)**FracPart(m)*(b/cos(e + f*x))**(-p*FracPart(m)), Int((b/cos(e + f*x))**(m*p)*(A + C/cos(e + f*x)**S(2)), x), x)
    rule4509 = ReplacementRule(pattern4509, replacement4509)
    pattern4510 = Pattern(Integral(((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('a', S(1)))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons5, cons18)
    def replacement4510(C, e, p, m, f, b, a, x, A):
        rubi.append(4510)
        return Dist(a**IntPart(m)*(a*(b/sin(e + f*x))**p)**FracPart(m)*(b/sin(e + f*x))**(-p*FracPart(m)), Int((b/sin(e + f*x))**(m*p)*(A + C/sin(e + f*x)**S(2)), x), x)
    rule4510 = ReplacementRule(pattern4510, replacement4510)
    pattern4511 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons87, cons89)
    def replacement4511(B, C, e, f, b, d, a, n, x, A):
        rubi.append(4511)
        return Dist(S(1)/(d*n), Int((d/cos(e + f*x))**(n + S(1))*Simp(C*b*n/cos(e + f*x)**S(2) + n*(A*b + B*a) + (A*a*(n + S(1)) + n*(B*b + C*a))/cos(e + f*x), x), x), x) - Simp(A*a*(d/cos(e + f*x))**n*tan(e + f*x)/(f*n), x)
    rule4511 = ReplacementRule(pattern4511, replacement4511)
    pattern4512 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons87, cons89)
    def replacement4512(B, C, f, b, d, a, n, A, x, e):
        rubi.append(4512)
        return Dist(S(1)/(d*n), Int((d/sin(e + f*x))**(n + S(1))*Simp(C*b*n/sin(e + f*x)**S(2) + n*(A*b + B*a) + (A*a*(n + S(1)) + n*(B*b + C*a))/sin(e + f*x), x), x), x) + Simp(A*a*(d/sin(e + f*x))**n/(f*n*tan(e + f*x)), x)
    rule4512 = ReplacementRule(pattern4512, replacement4512)
    pattern4513 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons87, cons89)
    def replacement4513(C, e, f, b, d, a, n, x, A):
        rubi.append(4513)
        return Dist(S(1)/(d*n), Int((d/cos(e + f*x))**(n + S(1))*Simp(A*b*n + C*b*n/cos(e + f*x)**S(2) + a*(A*(n + S(1)) + C*n)/cos(e + f*x), x), x), x) - Simp(A*a*(d/cos(e + f*x))**n*tan(e + f*x)/(f*n), x)
    rule4513 = ReplacementRule(pattern4513, replacement4513)
    pattern4514 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons87, cons89)
    def replacement4514(C, f, b, d, a, n, A, x, e):
        rubi.append(4514)
        return Dist(S(1)/(d*n), Int((d/sin(e + f*x))**(n + S(1))*Simp(A*b*n + C*b*n/sin(e + f*x)**S(2) + a*(A*(n + S(1)) + C*n)/sin(e + f*x), x), x), x) + Simp(A*a*(d/sin(e + f*x))**n/(f*n*tan(e + f*x)), x)
    rule4514 = ReplacementRule(pattern4514, replacement4514)
    pattern4515 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons346)
    def replacement4515(B, C, f, b, d, a, n, A, x, e):
        rubi.append(4515)
        return Dist(S(1)/(n + S(2)), Int((d/cos(e + f*x))**n*Simp(A*a*(n + S(2)) + (n + S(2))*(B*b + C*a)/cos(e + f*x)**S(2) + (B*a*(n + S(2)) + b*(A*(n + S(2)) + C*(n + S(1))))/cos(e + f*x), x), x), x) + Simp(C*b*(d/cos(e + f*x))**n*tan(e + f*x)/(f*(n + S(2))*cos(e + f*x)), x)
    rule4515 = ReplacementRule(pattern4515, replacement4515)
    pattern4516 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons346)
    def replacement4516(B, C, f, b, d, a, n, A, x, e):
        rubi.append(4516)
        return Dist(S(1)/(n + S(2)), Int((d/sin(e + f*x))**n*Simp(A*a*(n + S(2)) + (n + S(2))*(B*b + C*a)/sin(e + f*x)**S(2) + (B*a*(n + S(2)) + b*(A*(n + S(2)) + C*(n + S(1))))/sin(e + f*x), x), x), x) - Simp(C*b*(d/sin(e + f*x))**n/(f*(n + S(2))*sin(e + f*x)*tan(e + f*x)), x)
    rule4516 = ReplacementRule(pattern4516, replacement4516)
    pattern4517 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons346)
    def replacement4517(C, f, b, d, a, n, A, x, e):
        rubi.append(4517)
        return Dist(S(1)/(n + S(2)), Int((d/cos(e + f*x))**n*Simp(A*a*(n + S(2)) + C*a*(n + S(2))/cos(e + f*x)**S(2) + b*(A*(n + S(2)) + C*(n + S(1)))/cos(e + f*x), x), x), x) + Simp(C*b*(d/cos(e + f*x))**n*tan(e + f*x)/(f*(n + S(2))*cos(e + f*x)), x)
    rule4517 = ReplacementRule(pattern4517, replacement4517)
    pattern4518 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons346)
    def replacement4518(C, f, b, d, a, n, A, x, e):
        rubi.append(4518)
        return Dist(S(1)/(n + S(2)), Int((d/sin(e + f*x))**n*Simp(A*a*(n + S(2)) + C*a*(n + S(2))/sin(e + f*x)**S(2) + b*(A*(n + S(2)) + C*(n + S(1)))/sin(e + f*x), x), x), x) - Simp(C*b*(d/sin(e + f*x))**n/(f*(n + S(2))*sin(e + f*x)*tan(e + f*x)), x)
    rule4518 = ReplacementRule(pattern4518, replacement4518)
    pattern4519 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons31, cons94, cons1265)
    def replacement4519(B, C, e, m, f, b, a, x, A):
        rubi.append(4519)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(-S(2)*A*b*(m + S(1)) + B*a - C*b - (B*b*(m + S(2)) - a*(A*(m + S(2)) - C*(m + S(-1))))/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**m*(A*a - B*b + C*a)*tan(e + f*x)/(a*f*(S(2)*m + S(1))*cos(e + f*x)), x)
    rule4519 = ReplacementRule(pattern4519, replacement4519)
    pattern4520 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons31, cons94, cons1265)
    def replacement4520(B, C, e, m, f, b, a, x, A):
        rubi.append(4520)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(-S(2)*A*b*(m + S(1)) + B*a - C*b - (B*b*(m + S(2)) - a*(A*(m + S(2)) - C*(m + S(-1))))/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**m*(A*a - B*b + C*a)/(a*f*(S(2)*m + S(1))*sin(e + f*x)*tan(e + f*x)), x)
    rule4520 = ReplacementRule(pattern4520, replacement4520)
    pattern4521 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons31, cons94, cons1265)
    def replacement4521(C, e, m, f, b, a, x, A):
        rubi.append(4521)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(-S(2)*A*b*(m + S(1)) - C*b + a*(A*(m + S(2)) - C*(m + S(-1)))/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp((A + C)*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(S(2)*m + S(1))*cos(e + f*x)), x)
    rule4521 = ReplacementRule(pattern4521, replacement4521)
    pattern4522 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons31, cons94, cons1265)
    def replacement4522(C, e, m, f, b, a, x, A):
        rubi.append(4522)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(-S(2)*A*b*(m + S(1)) - C*b + a*(A*(m + S(2)) - C*(m + S(-1)))/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp((A + C)*(a + b/sin(e + f*x))**m/(f*(S(2)*m + S(1))*sin(e + f*x)*tan(e + f*x)), x)
    rule4522 = ReplacementRule(pattern4522, replacement4522)
    pattern4523 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons31, cons94, cons1267)
    def replacement4523(B, C, e, m, f, b, a, x, A):
        rubi.append(4523)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(b*(m + S(1))*(A*a - B*b + C*a) - (A*b**S(2) - B*a*b + C*a**S(2) + b*(m + S(1))*(A*b - B*a + C*b))/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))*tan(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4523 = ReplacementRule(pattern4523, replacement4523)
    pattern4524 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons31, cons94, cons1267)
    def replacement4524(B, C, e, m, f, b, a, x, A):
        rubi.append(4524)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(b*(m + S(1))*(A*a - B*b + C*a) - (A*b**S(2) - B*a*b + C*a**S(2) + b*(m + S(1))*(A*b - B*a + C*b))/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))/(b*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4524 = ReplacementRule(pattern4524, replacement4524)
    pattern4525 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons31, cons94, cons1267)
    def replacement4525(C, e, m, f, b, a, x, A):
        rubi.append(4525)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(a*b*(A + C)*(m + S(1)) - (A*b**S(2) + C*a**S(2) + b*(m + S(1))*(A*b + C*b))/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp((a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))*tan(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4525 = ReplacementRule(pattern4525, replacement4525)
    pattern4526 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons31, cons94, cons1267)
    def replacement4526(C, e, m, f, b, a, x, A):
        rubi.append(4526)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(a*b*(A + C)*(m + S(1)) - (A*b**S(2) + C*a**S(2) + b*(m + S(1))*(A*b + C*b))/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp((a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))/(b*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4526 = ReplacementRule(pattern4526, replacement4526)
    pattern4527 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons272)
    def replacement4527(B, C, e, m, f, b, a, x, A):
        rubi.append(4527)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/cos(e + f*x))**m*Simp(A*b*(m + S(2)) + C*b*(m + S(1)) + (B*b*(m + S(2)) - C*a)/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp(C*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + S(2))), x)
    rule4527 = ReplacementRule(pattern4527, replacement4527)
    pattern4528 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons272)
    def replacement4528(B, C, e, m, f, b, a, x, A):
        rubi.append(4528)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/sin(e + f*x))**m*Simp(A*b*(m + S(2)) + C*b*(m + S(1)) + (B*b*(m + S(2)) - C*a)/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp(C*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + S(2))*tan(e + f*x)), x)
    rule4528 = ReplacementRule(pattern4528, replacement4528)
    pattern4529 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons272)
    def replacement4529(C, e, m, f, b, a, x, A):
        rubi.append(4529)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/cos(e + f*x))**m*Simp(A*b*(m + S(2)) - C*a/cos(e + f*x) + C*b*(m + S(1)), x)/cos(e + f*x), x), x) + Simp(C*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + S(2))), x)
    rule4529 = ReplacementRule(pattern4529, replacement4529)
    pattern4530 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons272)
    def replacement4530(C, e, m, f, b, a, x, A):
        rubi.append(4530)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b/sin(e + f*x))**m*Simp(A*b*(m + S(2)) - C*a/sin(e + f*x) + C*b*(m + S(1)), x)/sin(e + f*x), x), x) - Simp(C*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + S(2))*tan(e + f*x)), x)
    rule4530 = ReplacementRule(pattern4530, replacement4530)
    pattern4531 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons1265, cons31, cons1320)
    def replacement4531(B, C, e, m, f, b, d, a, n, x, A):
        rubi.append(4531)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*Simp(-A*b*(S(2)*m + n + S(1)) + B*a*n - C*b*n - (B*b*(m + n + S(1)) - a*(A*(m + n + S(1)) - C*(m - n)))/cos(e + f*x), x), x), x) + Simp((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*(A*a - B*b + C*a)*tan(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule4531 = ReplacementRule(pattern4531, replacement4531)
    pattern4532 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons1265, cons31, cons1320)
    def replacement4532(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4532)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*Simp(-A*b*(S(2)*m + n + S(1)) + B*a*n - C*b*n - (B*b*(m + n + S(1)) - a*(A*(m + n + S(1)) - C*(m - n)))/sin(e + f*x), x), x), x) - Simp((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m*(A*a - B*b + C*a)/(a*f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4532 = ReplacementRule(pattern4532, replacement4532)
    pattern4533 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons1265, cons31, cons1320)
    def replacement4533(C, e, m, f, b, d, a, n, x, A):
        rubi.append(4533)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*Simp(A*b*(S(2)*m + n + S(1)) + C*b*n - a*(A*(m + n + S(1)) - C*(m - n))/cos(e + f*x), x), x), x) + Simp((d/cos(e + f*x))**n*(A + C)*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(S(2)*m + S(1))), x)
    rule4533 = ReplacementRule(pattern4533, replacement4533)
    pattern4534 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons1265, cons31, cons1320)
    def replacement4534(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4534)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*Simp(A*b*(S(2)*m + n + S(1)) + C*b*n - a*(A*(m + n + S(1)) - C*(m - n))/sin(e + f*x), x), x), x) - Simp((d/sin(e + f*x))**n*(A + C)*(a + b/sin(e + f*x))**m/(f*(S(2)*m + S(1))*tan(e + f*x)), x)
    rule4534 = ReplacementRule(pattern4534, replacement4534)
    pattern4535 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons1265, cons1321, cons1639)
    def replacement4535(B, C, e, m, f, b, d, a, n, x, A):
        rubi.append(4535)
        return -Dist(S(1)/(b*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**m*Simp(A*a*m - B*b*n - b*(A*(m + n + S(1)) + C*n)/cos(e + f*x), x), x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*n), x)
    rule4535 = ReplacementRule(pattern4535, replacement4535)
    pattern4536 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons1265, cons1321, cons1639)
    def replacement4536(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4536)
        return -Dist(S(1)/(b*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**m*Simp(A*a*m - B*b*n - b*(A*(m + n + S(1)) + C*n)/sin(e + f*x), x), x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*n*tan(e + f*x)), x)
    rule4536 = ReplacementRule(pattern4536, replacement4536)
    pattern4537 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons1265, cons1321, cons1639)
    def replacement4537(C, e, m, f, b, d, a, n, x, A):
        rubi.append(4537)
        return -Dist(S(1)/(b*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**m*Simp(A*a*m - b*(A*(m + n + S(1)) + C*n)/cos(e + f*x), x), x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*n), x)
    rule4537 = ReplacementRule(pattern4537, replacement4537)
    pattern4538 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons1265, cons1321, cons1639)
    def replacement4538(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4538)
        return -Dist(S(1)/(b*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**m*Simp(A*a*m - b*(A*(m + n + S(1)) + C*n)/sin(e + f*x), x), x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*n*tan(e + f*x)), x)
    rule4538 = ReplacementRule(pattern4538, replacement4538)
    pattern4539 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons1265, cons1321, cons1640, cons683)
    def replacement4539(B, C, e, m, f, b, d, a, n, x, A):
        rubi.append(4539)
        return Dist(S(1)/(b*(m + n + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*Simp(A*b*(m + n + S(1)) + C*b*n + (B*b*(m + n + S(1)) + C*a*m)/cos(e + f*x), x), x), x) + Simp(C*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + n + S(1))), x)
    rule4539 = ReplacementRule(pattern4539, replacement4539)
    pattern4540 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons1265, cons1321, cons1640, cons683)
    def replacement4540(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4540)
        return Dist(S(1)/(b*(m + n + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m*Simp(A*b*(m + n + S(1)) + C*b*n + (B*b*(m + n + S(1)) + C*a*m)/sin(e + f*x), x), x), x) - Simp(C*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*(m + n + S(1))*tan(e + f*x)), x)
    rule4540 = ReplacementRule(pattern4540, replacement4540)
    pattern4541 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons1265, cons1321, cons1640, cons683)
    def replacement4541(C, e, m, f, b, d, a, n, x, A):
        rubi.append(4541)
        return Dist(S(1)/(b*(m + n + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*Simp(A*b*(m + n + S(1)) + C*a*m/cos(e + f*x) + C*b*n, x), x), x) + Simp(C*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + n + S(1))), x)
    rule4541 = ReplacementRule(pattern4541, replacement4541)
    pattern4542 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons1265, cons1321, cons1640, cons683)
    def replacement4542(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4542)
        return Dist(S(1)/(b*(m + n + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m*Simp(A*b*(m + n + S(1)) + C*a*m/sin(e + f*x) + C*b*n, x), x), x) - Simp(C*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*(m + n + S(1))*tan(e + f*x)), x)
    rule4542 = ReplacementRule(pattern4542, replacement4542)
    pattern4543 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1267, cons31, cons94)
    def replacement4543(B, C, e, m, f, b, a, x, A):
        rubi.append(4543)
        return -Dist(S(1)/(b**S(2)*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(-C*b*(a**S(2) - b**S(2))*(m + S(1))/cos(e + f*x)**S(2) + b*(m + S(1))*(A*b**S(2) - a*(B*b - C*a)) + (B*b*(a**S(2) + b**S(2)*(m + S(1))) - a*(A*b**S(2)*(m + S(2)) + C*(a**S(2) + b**S(2)*(m + S(1)))))/cos(e + f*x), x)/cos(e + f*x), x), x) - Simp(a*(a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))*tan(e + f*x)/(b**S(2)*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4543 = ReplacementRule(pattern4543, replacement4543)
    pattern4544 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons1267, cons31, cons94)
    def replacement4544(B, C, e, m, f, b, a, x, A):
        rubi.append(4544)
        return -Dist(S(1)/(b**S(2)*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(-C*b*(a**S(2) - b**S(2))*(m + S(1))/sin(e + f*x)**S(2) + b*(m + S(1))*(A*b**S(2) - a*(B*b - C*a)) + (B*b*(a**S(2) + b**S(2)*(m + S(1))) - a*(A*b**S(2)*(m + S(2)) + C*(a**S(2) + b**S(2)*(m + S(1)))))/sin(e + f*x), x)/sin(e + f*x), x), x) + Simp(a*(a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))/(b**S(2)*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4544 = ReplacementRule(pattern4544, replacement4544)
    pattern4545 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1267, cons31, cons94)
    def replacement4545(C, e, m, f, b, a, x, A):
        rubi.append(4545)
        return -Dist(S(1)/(b**S(2)*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/cos(e + f*x))**(m + S(1))*Simp(-C*b*(a**S(2) - b**S(2))*(m + S(1))/cos(e + f*x)**S(2) - a*(A*b**S(2)*(m + S(2)) + C*(a**S(2) + b**S(2)*(m + S(1))))/cos(e + f*x) + b*(m + S(1))*(A*b**S(2) + C*a**S(2)), x)/cos(e + f*x), x), x) - Simp(a*(a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))*tan(e + f*x)/(b**S(2)*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4545 = ReplacementRule(pattern4545, replacement4545)
    pattern4546 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons1267, cons31, cons94)
    def replacement4546(C, e, m, f, b, a, x, A):
        rubi.append(4546)
        return -Dist(S(1)/(b**S(2)*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b/sin(e + f*x))**(m + S(1))*Simp(-C*b*(a**S(2) - b**S(2))*(m + S(1))/sin(e + f*x)**S(2) - a*(A*b**S(2)*(m + S(2)) + C*(a**S(2) + b**S(2)*(m + S(1))))/sin(e + f*x) + b*(m + S(1))*(A*b**S(2) + C*a**S(2)), x)/sin(e + f*x), x), x) + Simp(a*(a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))/(b**S(2)*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4546 = ReplacementRule(pattern4546, replacement4546)
    pattern4547 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1267, cons272)
    def replacement4547(B, C, e, m, f, b, a, x, A):
        rubi.append(4547)
        return Dist(S(1)/(b*(m + S(3))), Int((a + b/cos(e + f*x))**m*Simp(C*a + b*(A*(m + S(3)) + C*(m + S(2)))/cos(e + f*x) - (-B*b*(m + S(3)) + S(2)*C*a)/cos(e + f*x)**S(2), x)/cos(e + f*x), x), x) + Simp(C*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + S(3))*cos(e + f*x)), x)
    rule4547 = ReplacementRule(pattern4547, replacement4547)
    pattern4548 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1267, cons272)
    def replacement4548(B, C, e, m, f, b, a, x, A):
        rubi.append(4548)
        return Dist(S(1)/(b*(m + S(3))), Int((a + b/sin(e + f*x))**m*Simp(C*a + b*(A*(m + S(3)) + C*(m + S(2)))/sin(e + f*x) - (-B*b*(m + S(3)) + S(2)*C*a)/sin(e + f*x)**S(2), x)/sin(e + f*x), x), x) - Simp(C*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + S(3))*sin(e + f*x)*tan(e + f*x)), x)
    rule4548 = ReplacementRule(pattern4548, replacement4548)
    pattern4549 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1267, cons272)
    def replacement4549(C, e, m, f, b, a, x, A):
        rubi.append(4549)
        return Dist(S(1)/(b*(m + S(3))), Int((a + b/cos(e + f*x))**m*Simp(C*a - S(2)*C*a/cos(e + f*x)**S(2) + b*(A*(m + S(3)) + C*(m + S(2)))/cos(e + f*x), x)/cos(e + f*x), x), x) + Simp(C*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + S(3))*cos(e + f*x)), x)
    rule4549 = ReplacementRule(pattern4549, replacement4549)
    pattern4550 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1267, cons272)
    def replacement4550(C, e, m, f, b, a, x, A):
        rubi.append(4550)
        return Dist(S(1)/(b*(m + S(3))), Int((a + b/sin(e + f*x))**m*Simp(C*a - S(2)*C*a/sin(e + f*x)**S(2) + b*(A*(m + S(3)) + C*(m + S(2)))/sin(e + f*x), x)/sin(e + f*x), x), x) - Simp(C*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + S(3))*sin(e + f*x)*tan(e + f*x)), x)
    rule4550 = ReplacementRule(pattern4550, replacement4550)
    pattern4551 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267, cons93, cons168, cons1586)
    def replacement4551(B, C, e, m, f, b, d, a, n, x, A):
        rubi.append(4551)
        return -Dist(S(1)/(d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**(m + S(-1))*Simp(A*b*m - B*a*n - b*(A*(m + n + S(1)) + C*n)/cos(e + f*x)**S(2) - (B*b*n + a*(A*(n + S(1)) + C*n))/cos(e + f*x), x), x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*n), x)
    rule4551 = ReplacementRule(pattern4551, replacement4551)
    pattern4552 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267, cons93, cons168, cons1586)
    def replacement4552(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4552)
        return -Dist(S(1)/(d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**(m + S(-1))*Simp(A*b*m - B*a*n - b*(A*(m + n + S(1)) + C*n)/sin(e + f*x)**S(2) - (B*b*n + a*(A*(n + S(1)) + C*n))/sin(e + f*x), x), x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*n*tan(e + f*x)), x)
    rule4552 = ReplacementRule(pattern4552, replacement4552)
    pattern4553 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267, cons93, cons168, cons1586)
    def replacement4553(C, e, m, f, b, d, a, n, x, A):
        rubi.append(4553)
        return -Dist(S(1)/(d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**(m + S(-1))*Simp(A*b*m - a*(A*(n + S(1)) + C*n)/cos(e + f*x) - b*(A*(m + n + S(1)) + C*n)/cos(e + f*x)**S(2), x), x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*n), x)
    rule4553 = ReplacementRule(pattern4553, replacement4553)
    pattern4554 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267, cons93, cons168, cons1586)
    def replacement4554(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4554)
        return -Dist(S(1)/(d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**(m + S(-1))*Simp(A*b*m - a*(A*(n + S(1)) + C*n)/sin(e + f*x) - b*(A*(m + n + S(1)) + C*n)/sin(e + f*x)**S(2), x), x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*n*tan(e + f*x)), x)
    rule4554 = ReplacementRule(pattern4554, replacement4554)
    pattern4555 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons1267, cons31, cons168, cons1569)
    def replacement4555(B, C, e, m, f, b, d, a, n, x, A):
        rubi.append(4555)
        return Dist(S(1)/(m + n + S(1)), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-1))*Simp(A*a*(m + n + S(1)) + C*a*n + (B*b*(m + n + S(1)) + C*a*m)/cos(e + f*x)**S(2) + (C*b*(m + n) + (A*b + B*a)*(m + n + S(1)))/cos(e + f*x), x), x), x) + Simp(C*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + n + S(1))), x)
    rule4555 = ReplacementRule(pattern4555, replacement4555)
    pattern4556 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons1267, cons31, cons168, cons1569)
    def replacement4556(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4556)
        return Dist(S(1)/(m + n + S(1)), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-1))*Simp(A*a*(m + n + S(1)) + C*a*n + (B*b*(m + n + S(1)) + C*a*m)/sin(e + f*x)**S(2) + (C*b*(m + n) + (A*b + B*a)*(m + n + S(1)))/sin(e + f*x), x), x), x) - Simp(C*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*(m + n + S(1))*tan(e + f*x)), x)
    rule4556 = ReplacementRule(pattern4556, replacement4556)
    pattern4557 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons1267, cons31, cons168, cons1569)
    def replacement4557(C, e, m, f, b, d, a, n, x, A):
        rubi.append(4557)
        return Dist(S(1)/(m + n + S(1)), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(-1))*Simp(A*a*(m + n + S(1)) + C*a*m/cos(e + f*x)**S(2) + C*a*n + b*(A*(m + n + S(1)) + C*(m + n))/cos(e + f*x), x), x), x) + Simp(C*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*tan(e + f*x)/(f*(m + n + S(1))), x)
    rule4557 = ReplacementRule(pattern4557, replacement4557)
    pattern4558 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons1267, cons31, cons168, cons1569)
    def replacement4558(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4558)
        return Dist(S(1)/(m + n + S(1)), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(-1))*Simp(A*a*(m + n + S(1)) + C*a*m/sin(e + f*x)**S(2) + C*a*n + b*(A*(m + n + S(1)) + C*(m + n))/sin(e + f*x), x), x), x) - Simp(C*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m/(f*(m + n + S(1))*tan(e + f*x)), x)
    rule4558 = ReplacementRule(pattern4558, replacement4558)
    pattern4559 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267, cons93, cons94, cons88)
    def replacement4559(B, C, e, m, f, b, d, a, n, x, A):
        rubi.append(4559)
        return Dist(d/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*Simp(A*b**S(2)*(n + S(-1)) - a*(n + S(-1))*(B*b - C*a) + b*(m + S(1))*(A*a - B*b + C*a)/cos(e + f*x) - (C*(a**S(2)*n + b**S(2)*(m + S(1))) + b*(A*b - B*a)*(m + n + S(1)))/cos(e + f*x)**S(2), x), x), x) + Simp(d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))*tan(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4559 = ReplacementRule(pattern4559, replacement4559)
    pattern4560 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267, cons93, cons94, cons88)
    def replacement4560(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4560)
        return Dist(d/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))*Simp(A*b**S(2)*(n + S(-1)) - a*(n + S(-1))*(B*b - C*a) + b*(m + S(1))*(A*a - B*b + C*a)/sin(e + f*x) - (C*(a**S(2)*n + b**S(2)*(m + S(1))) + b*(A*b - B*a)*(m + n + S(1)))/sin(e + f*x)**S(2), x), x), x) - Simp(d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))/(b*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4560 = ReplacementRule(pattern4560, replacement4560)
    pattern4561 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267, cons93, cons94, cons88)
    def replacement4561(C, e, m, f, b, d, a, n, x, A):
        rubi.append(4561)
        return Dist(d/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*Simp(A*b**S(2)*(n + S(-1)) + C*a**S(2)*(n + S(-1)) + a*b*(A + C)*(m + S(1))/cos(e + f*x) - (A*b**S(2)*(m + n + S(1)) + C*(a**S(2)*n + b**S(2)*(m + S(1))))/cos(e + f*x)**S(2), x), x), x) + Simp(d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))*tan(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4561 = ReplacementRule(pattern4561, replacement4561)
    pattern4562 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267, cons93, cons94, cons88)
    def replacement4562(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4562)
        return Dist(d/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))*Simp(A*b**S(2)*(n + S(-1)) + C*a**S(2)*(n + S(-1)) + a*b*(A + C)*(m + S(1))/sin(e + f*x) - (A*b**S(2)*(m + n + S(1)) + C*(a**S(2)*n + b**S(2)*(m + S(1))))/sin(e + f*x)**S(2), x), x), x) - Simp(d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))/(b*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4562 = ReplacementRule(pattern4562, replacement4562)
    pattern4563 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons1267, cons31, cons94, cons1631)
    def replacement4563(B, C, e, m, f, b, d, a, n, x, A):
        rubi.append(4563)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*Simp(a*(m + S(1))*(A*a - B*b + C*a) - a*(m + S(1))*(A*b - B*a + C*b)/cos(e + f*x) - (m + n + S(1))*(A*b**S(2) - B*a*b + C*a**S(2)) + (m + n + S(2))*(A*b**S(2) - B*a*b + C*a**S(2))/cos(e + f*x)**S(2), x), x), x) - Simp((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))*tan(e + f*x)/(a*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4563 = ReplacementRule(pattern4563, replacement4563)
    pattern4564 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons1267, cons31, cons94, cons1631)
    def replacement4564(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4564)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*Simp(a*(m + S(1))*(A*a - B*b + C*a) - a*(m + S(1))*(A*b - B*a + C*b)/sin(e + f*x) - (m + n + S(1))*(A*b**S(2) - B*a*b + C*a**S(2)) + (m + n + S(2))*(A*b**S(2) - B*a*b + C*a**S(2))/sin(e + f*x)**S(2), x), x), x) + Simp((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))/(a*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4564 = ReplacementRule(pattern4564, replacement4564)
    pattern4565 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons1267, cons31, cons94, cons1631)
    def replacement4565(C, e, m, f, b, d, a, n, x, A):
        rubi.append(4565)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*Simp(a**S(2)*(A + C)*(m + S(1)) - a*b*(A + C)*(m + S(1))/cos(e + f*x) - (A*b**S(2) + C*a**S(2))*(m + n + S(1)) + (A*b**S(2) + C*a**S(2))*(m + n + S(2))/cos(e + f*x)**S(2), x), x), x) - Simp((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))*tan(e + f*x)/(a*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule4565 = ReplacementRule(pattern4565, replacement4565)
    pattern4566 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons1267, cons31, cons94, cons1631)
    def replacement4566(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4566)
        return Dist(S(1)/(a*(a**S(2) - b**S(2))*(m + S(1))), Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*Simp(a**S(2)*(A + C)*(m + S(1)) - a*b*(A + C)*(m + S(1))/sin(e + f*x) - (A*b**S(2) + C*a**S(2))*(m + n + S(1)) + (A*b**S(2) + C*a**S(2))*(m + n + S(2))/sin(e + f*x)**S(2), x), x), x) + Simp((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))/(a*f*(a**S(2) - b**S(2))*(m + S(1))*tan(e + f*x)), x)
    rule4566 = ReplacementRule(pattern4566, replacement4566)
    pattern4567 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons1267, cons87, cons88)
    def replacement4567(B, C, e, m, f, b, d, a, n, x, A):
        rubi.append(4567)
        return Dist(d/(b*(m + n + S(1))), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**m*Simp(C*a*(n + S(-1)) + (A*b*(m + n + S(1)) + C*b*(m + n))/cos(e + f*x) + (B*b*(m + n + S(1)) - C*a*n)/cos(e + f*x)**S(2), x), x), x) + Simp(C*d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + n + S(1))), x)
    rule4567 = ReplacementRule(pattern4567, replacement4567)
    pattern4568 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons1267, cons87, cons88)
    def replacement4568(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4568)
        return Dist(d/(b*(m + n + S(1))), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**m*Simp(C*a*(n + S(-1)) + (A*b*(m + n + S(1)) + C*b*(m + n))/sin(e + f*x) + (B*b*(m + n + S(1)) - C*a*n)/sin(e + f*x)**S(2), x), x), x) - Simp(C*d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + n + S(1))*tan(e + f*x)), x)
    rule4568 = ReplacementRule(pattern4568, replacement4568)
    pattern4569 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons1267, cons87, cons88)
    def replacement4569(C, e, m, f, b, d, a, n, x, A):
        rubi.append(4569)
        return Dist(d/(b*(m + n + S(1))), Int((d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**m*Simp(-C*a*n/cos(e + f*x)**S(2) + C*a*(n + S(-1)) + (A*b*(m + n + S(1)) + C*b*(m + n))/cos(e + f*x), x), x), x) + Simp(C*d*(d/cos(e + f*x))**(n + S(-1))*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(b*f*(m + n + S(1))), x)
    rule4569 = ReplacementRule(pattern4569, replacement4569)
    pattern4570 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons1267, cons87, cons88)
    def replacement4570(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4570)
        return Dist(d/(b*(m + n + S(1))), Int((d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**m*Simp(-C*a*n/sin(e + f*x)**S(2) + C*a*(n + S(-1)) + (A*b*(m + n + S(1)) + C*b*(m + n))/sin(e + f*x), x), x), x) - Simp(C*d*(d/sin(e + f*x))**(n + S(-1))*(a + b/sin(e + f*x))**(m + S(1))/(b*f*(m + n + S(1))*tan(e + f*x)), x)
    rule4570 = ReplacementRule(pattern4570, replacement4570)
    pattern4571 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons1267, cons87, cons1586)
    def replacement4571(B, C, e, m, f, b, d, a, n, x, A):
        rubi.append(4571)
        return Dist(S(1)/(a*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**m*Simp(-A*b*(m + n + S(1)) + A*b*(m + n + S(2))/cos(e + f*x)**S(2) + B*a*n + a*(A*n + A + C*n)/cos(e + f*x), x), x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(a*f*n), x)
    rule4571 = ReplacementRule(pattern4571, replacement4571)
    pattern4572 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons1267, cons87, cons1586)
    def replacement4572(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4572)
        return Dist(S(1)/(a*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**m*Simp(-A*b*(m + n + S(1)) + A*b*(m + n + S(2))/sin(e + f*x)**S(2) + B*a*n + a*(A*n + A + C*n)/sin(e + f*x), x), x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))/(a*f*n*tan(e + f*x)), x)
    rule4572 = ReplacementRule(pattern4572, replacement4572)
    pattern4573 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons1267, cons87, cons1586)
    def replacement4573(C, e, m, f, b, d, a, n, x, A):
        rubi.append(4573)
        return Dist(S(1)/(a*d*n), Int((d/cos(e + f*x))**(n + S(1))*(a + b/cos(e + f*x))**m*Simp(-A*b*(m + n + S(1)) + A*b*(m + n + S(2))/cos(e + f*x)**S(2) + a*(A*n + A + C*n)/cos(e + f*x), x), x), x) - Simp(A*(d/cos(e + f*x))**n*(a + b/cos(e + f*x))**(m + S(1))*tan(e + f*x)/(a*f*n), x)
    rule4573 = ReplacementRule(pattern4573, replacement4573)
    pattern4574 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons1267, cons87, cons1586)
    def replacement4574(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4574)
        return Dist(S(1)/(a*d*n), Int((d/sin(e + f*x))**(n + S(1))*(a + b/sin(e + f*x))**m*Simp(-A*b*(m + n + S(1)) + A*b*(m + n + S(2))/sin(e + f*x)**S(2) + a*(A*n + A + C*n)/sin(e + f*x), x), x), x) + Simp(A*(d/sin(e + f*x))**n*(a + b/sin(e + f*x))**(m + S(1))/(a*f*n*tan(e + f*x)), x)
    rule4574 = ReplacementRule(pattern4574, replacement4574)
    pattern4575 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267)
    def replacement4575(B, C, e, f, b, d, a, x, A):
        rubi.append(4575)
        return Dist(a**(S(-2)), Int((A*a - (A*b - B*a)/cos(e + f*x))/sqrt(d/cos(e + f*x)), x), x) + Dist((A*b**S(2) - B*a*b + C*a**S(2))/(a**S(2)*d**S(2)), Int((d/cos(e + f*x))**(S(3)/2)/(a + b/cos(e + f*x)), x), x)
    rule4575 = ReplacementRule(pattern4575, replacement4575)
    pattern4576 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267)
    def replacement4576(B, C, f, b, d, a, A, x, e):
        rubi.append(4576)
        return Dist(a**(S(-2)), Int((A*a - (A*b - B*a)/sin(e + f*x))/sqrt(d/sin(e + f*x)), x), x) + Dist((A*b**S(2) - B*a*b + C*a**S(2))/(a**S(2)*d**S(2)), Int((d/sin(e + f*x))**(S(3)/2)/(a + b/sin(e + f*x)), x), x)
    rule4576 = ReplacementRule(pattern4576, replacement4576)
    pattern4577 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267)
    def replacement4577(C, e, f, b, d, a, x, A):
        rubi.append(4577)
        return Dist(a**(S(-2)), Int((A*a - A*b/cos(e + f*x))/sqrt(d/cos(e + f*x)), x), x) + Dist((A*b**S(2) + C*a**S(2))/(a**S(2)*d**S(2)), Int((d/cos(e + f*x))**(S(3)/2)/(a + b/cos(e + f*x)), x), x)
    rule4577 = ReplacementRule(pattern4577, replacement4577)
    pattern4578 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267)
    def replacement4578(C, f, b, d, a, A, x, e):
        rubi.append(4578)
        return Dist(a**(S(-2)), Int((A*a - A*b/sin(e + f*x))/sqrt(d/sin(e + f*x)), x), x) + Dist((A*b**S(2) + C*a**S(2))/(a**S(2)*d**S(2)), Int((d/sin(e + f*x))**(S(3)/2)/(a + b/sin(e + f*x)), x), x)
    rule4578 = ReplacementRule(pattern4578, replacement4578)
    pattern4579 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267)
    def replacement4579(B, C, e, f, b, d, a, x, A):
        rubi.append(4579)
        return Dist(C/d**S(2), Int((d/cos(e + f*x))**(S(3)/2)/sqrt(a + b/cos(e + f*x)), x), x) + Int((A + B/cos(e + f*x))/(sqrt(d/cos(e + f*x))*sqrt(a + b/cos(e + f*x))), x)
    rule4579 = ReplacementRule(pattern4579, replacement4579)
    pattern4580 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267)
    def replacement4580(B, C, f, b, d, a, A, x, e):
        rubi.append(4580)
        return Dist(C/d**S(2), Int((d/sin(e + f*x))**(S(3)/2)/sqrt(a + b/sin(e + f*x)), x), x) + Int((A + B/sin(e + f*x))/(sqrt(d/sin(e + f*x))*sqrt(a + b/sin(e + f*x))), x)
    rule4580 = ReplacementRule(pattern4580, replacement4580)
    pattern4581 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267)
    def replacement4581(C, e, f, b, d, a, x, A):
        rubi.append(4581)
        return Dist(A, Int(S(1)/(sqrt(d/cos(e + f*x))*sqrt(a + b/cos(e + f*x))), x), x) + Dist(C/d**S(2), Int((d/cos(e + f*x))**(S(3)/2)/sqrt(a + b/cos(e + f*x)), x), x)
    rule4581 = ReplacementRule(pattern4581, replacement4581)
    pattern4582 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267)
    def replacement4582(C, f, b, d, a, A, x, e):
        rubi.append(4582)
        return Dist(A, Int(S(1)/(sqrt(d/sin(e + f*x))*sqrt(a + b/sin(e + f*x))), x), x) + Dist(C/d**S(2), Int((d/sin(e + f*x))**(S(3)/2)/sqrt(a + b/sin(e + f*x)), x), x)
    rule4582 = ReplacementRule(pattern4582, replacement4582)
    pattern4583 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons1641)
    def replacement4583(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4583)
        return Int((d/cos(e + f*x))**n*(a + b/cos(e + f*x))**m*(A + B/cos(e + f*x) + C/cos(e + f*x)**S(2)), x)
    rule4583 = ReplacementRule(pattern4583, replacement4583)
    pattern4584 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons1641)
    def replacement4584(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4584)
        return Int((d/sin(e + f*x))**n*(a + b/sin(e + f*x))**m*(A + B/sin(e + f*x) + C/sin(e + f*x)**S(2)), x)
    rule4584 = ReplacementRule(pattern4584, replacement4584)
    pattern4585 = Pattern(Integral((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons1642)
    def replacement4585(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4585)
        return Int((d/cos(e + f*x))**n*(A + C/cos(e + f*x)**S(2))*(a + b/cos(e + f*x))**m, x)
    rule4585 = ReplacementRule(pattern4585, replacement4585)
    pattern4586 = Pattern(Integral((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons1642)
    def replacement4586(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4586)
        return Int((d/sin(e + f*x))**n*(A + C/sin(e + f*x)**S(2))*(a + b/sin(e + f*x))**m, x)
    rule4586 = ReplacementRule(pattern4586, replacement4586)
    pattern4587 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons23, cons17)
    def replacement4587(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4587)
        return Dist(d**(m + S(2)), Int((d*cos(e + f*x))**(-m + n + S(-2))*(a*cos(e + f*x) + b)**m*(A*cos(e + f*x)**S(2) + B*cos(e + f*x) + C), x), x)
    rule4587 = ReplacementRule(pattern4587, replacement4587)
    pattern4588 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons23, cons17)
    def replacement4588(B, C, m, f, b, d, a, n, A, x, e):
        rubi.append(4588)
        return Dist(d**(m + S(2)), Int((d*sin(e + f*x))**(-m + n + S(-2))*(a*sin(e + f*x) + b)**m*(A*sin(e + f*x)**S(2) + B*sin(e + f*x) + C), x), x)
    rule4588 = ReplacementRule(pattern4588, replacement4588)
    pattern4589 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons23, cons17)
    def replacement4589(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4589)
        return Dist(d**(m + S(2)), Int((d*cos(e + f*x))**(-m + n + S(-2))*(A*cos(e + f*x)**S(2) + C)*(a*cos(e + f*x) + b)**m, x), x)
    rule4589 = ReplacementRule(pattern4589, replacement4589)
    pattern4590 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons4, cons23, cons17)
    def replacement4590(C, m, f, b, d, a, n, A, x, e):
        rubi.append(4590)
        return Dist(d**(m + S(2)), Int((d*sin(e + f*x))**(-m + n + S(-2))*(A*sin(e + f*x)**S(2) + C)*(a*sin(e + f*x) + b)**m, x), x)
    rule4590 = ReplacementRule(pattern4590, replacement4590)
    pattern4591 = Pattern(Integral(((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons23)
    def replacement4591(B, C, p, m, f, b, d, c, n, a, A, x, e):
        rubi.append(4591)
        return Dist(c**IntPart(n)*(c*(d/cos(e + f*x))**p)**FracPart(n)*(d/cos(e + f*x))**(-p*FracPart(n)), Int((d/cos(e + f*x))**(n*p)*(a + b/cos(e + f*x))**m*(A + B/cos(e + f*x) + C/cos(e + f*x)**S(2)), x), x)
    rule4591 = ReplacementRule(pattern4591, replacement4591)
    pattern4592 = Pattern(Integral(((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons23)
    def replacement4592(B, C, p, m, f, b, d, c, n, a, A, x, e):
        rubi.append(4592)
        return Dist(c**IntPart(n)*(c*(d/sin(e + f*x))**p)**FracPart(n)*(d/sin(e + f*x))**(-p*FracPart(n)), Int((d/sin(e + f*x))**(n*p)*(a + b/sin(e + f*x))**m*(A + B/sin(e + f*x) + C/sin(e + f*x)**S(2)), x), x)
    rule4592 = ReplacementRule(pattern4592, replacement4592)
    pattern4593 = Pattern(Integral(((WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons5, cons23)
    def replacement4593(C, p, m, f, b, d, c, n, a, A, x, e):
        rubi.append(4593)
        return Dist(c**IntPart(n)*(c*(d/cos(e + f*x))**p)**FracPart(n)*(d/cos(e + f*x))**(-p*FracPart(n)), Int((d/cos(e + f*x))**(n*p)*(A + C/cos(e + f*x)**S(2))*(a + b/cos(e + f*x))**m, x), x)
    rule4593 = ReplacementRule(pattern4593, replacement4593)
    pattern4594 = Pattern(Integral(((WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons5, cons23)
    def replacement4594(C, p, m, f, b, d, c, n, a, A, x, e):
        rubi.append(4594)
        return Dist(c**IntPart(n)*(c*(d/sin(e + f*x))**p)**FracPart(n)*(d/sin(e + f*x))**(-p*FracPart(n)), Int((d/sin(e + f*x))**(n*p)*(A + C/sin(e + f*x)**S(2))*(a + b/sin(e + f*x))**m, x), x)
    rule4594 = ReplacementRule(pattern4594, replacement4594)
    pattern4595 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**n_, x_), cons3, cons7, cons27, cons4, cons1643)
    def replacement4595(b, d, c, n, x):
        rubi.append(4595)
        return Dist(b/d, Subst(Int((b*x**S(2) + b)**(n + S(-1)), x), x, tan(c + d*x)), x)
    rule4595 = ReplacementRule(pattern4595, replacement4595)
    pattern4596 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**n_, x_), cons3, cons7, cons27, cons4, cons1643)
    def replacement4596(b, d, c, n, x):
        rubi.append(4596)
        return -Dist(b/d, Subst(Int((b*x**S(2) + b)**(n + S(-1)), x), x, S(1)/tan(c + d*x)), x)
    rule4596 = ReplacementRule(pattern4596, replacement4596)
    pattern4597 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1454)
    def replacement4597(p, b, d, c, a, x):
        rubi.append(4597)
        return Int((-a*tan(c + d*x)**S(2))**p, x)
    rule4597 = ReplacementRule(pattern4597, replacement4597)
    pattern4598 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1454)
    def replacement4598(p, b, d, c, a, x):
        rubi.append(4598)
        return Int((-a/tan(c + d*x)**S(2))**p, x)
    rule4598 = ReplacementRule(pattern4598, replacement4598)
    pattern4599 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons1478)
    def replacement4599(b, d, c, a, x):
        rubi.append(4599)
        return -Dist(b/a, Int(S(1)/(a*cos(c + d*x)**S(2) + b), x), x) + Simp(x/a, x)
    rule4599 = ReplacementRule(pattern4599, replacement4599)
    pattern4600 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons1478)
    def replacement4600(b, d, c, a, x):
        rubi.append(4600)
        return -Dist(b/a, Int(S(1)/(a*sin(c + d*x)**S(2) + b), x), x) + Simp(x/a, x)
    rule4600 = ReplacementRule(pattern4600, replacement4600)
    pattern4601 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1478, cons54)
    def replacement4601(p, b, d, c, a, x):
        rubi.append(4601)
        return Dist(S(1)/d, Subst(Int((a + b*x**S(2) + b)**p/(x**S(2) + S(1)), x), x, tan(c + d*x)), x)
    rule4601 = ReplacementRule(pattern4601, replacement4601)
    pattern4602 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1478, cons54)
    def replacement4602(p, b, d, c, a, x):
        rubi.append(4602)
        return -Dist(S(1)/d, Subst(Int((a + b*x**S(2) + b)**p/(x**S(2) + S(1)), x), x, S(1)/tan(c + d*x)), x)
    rule4602 = ReplacementRule(pattern4602, replacement4602)
    def With4603(p, m, b, d, c, a, n, x):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(4603)
        return Dist(f**(m + S(1))/d, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1))*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p, x), x, tan(c + d*x)/f), x)
    pattern4603 = Pattern(Integral((a_ + (S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons5, cons1480, cons1479)
    rule4603 = ReplacementRule(pattern4603, With4603)
    def With4604(p, m, b, d, c, n, a, x):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(4604)
        return -Dist(f**(m + S(1))/d, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1))*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p, x), x, S(1)/(f*tan(c + d*x))), x)
    pattern4604 = Pattern(Integral((a_ + (S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons5, cons1480, cons1479)
    rule4604 = ReplacementRule(pattern4604, With4604)
    def With4605(p, m, b, d, c, a, n, x):
        f = FreeFactors(cos(c + d*x), x)
        rubi.append(4605)
        return -Dist(f/d, Subst(Int((f*x)**(-n*p)*(a*(f*x)**n + b)**p*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2), x), x, cos(c + d*x)/f), x)
    pattern4605 = Pattern(Integral((a_ + (S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1481, cons376)
    rule4605 = ReplacementRule(pattern4605, With4605)
    def With4606(p, m, b, d, c, n, a, x):
        f = FreeFactors(sin(c + d*x), x)
        rubi.append(4606)
        return Dist(f/d, Subst(Int((f*x)**(-n*p)*(a*(f*x)**n + b)**p*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2), x), x, sin(c + d*x)/f), x)
    pattern4606 = Pattern(Integral((a_ + (S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1481, cons376)
    rule4606 = ReplacementRule(pattern4606, With4606)
    def With4607(p, m, b, d, c, a, n, x):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(4607)
        return Dist(f/d, Subst(Int((f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1))*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p, x), x, tan(c + d*x)/f), x)
    pattern4607 = Pattern(Integral((a_ + (S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*(S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons5, cons1480, cons1479)
    rule4607 = ReplacementRule(pattern4607, With4607)
    def With4608(p, m, b, d, c, n, a, x):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(4608)
        return -Dist(f/d, Subst(Int((f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1))*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p, x), x, S(1)/(f*tan(c + d*x))), x)
    pattern4608 = Pattern(Integral((a_ + (S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*(S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons5, cons1480, cons1479)
    rule4608 = ReplacementRule(pattern4608, With4608)
    def With4609(p, m, b, d, c, a, n, x):
        f = FreeFactors(sin(c + d*x), x)
        rubi.append(4609)
        return Dist(f/d, Subst(Int((-f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1)/2)*ExpandToSum(a*(-f**S(2)*x**S(2) + S(1))**(n/S(2)) + b, x)**p, x), x, sin(c + d*x)/f), x)
    pattern4609 = Pattern(Integral((a_ + (S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*(S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1481, cons1479, cons38)
    rule4609 = ReplacementRule(pattern4609, With4609)
    def With4610(p, m, b, d, c, n, a, x):
        f = FreeFactors(cos(c + d*x), x)
        rubi.append(4610)
        return -Dist(f/d, Subst(Int((-f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1)/2)*ExpandToSum(a*(-f**S(2)*x**S(2) + S(1))**(n/S(2)) + b, x)**p, x), x, cos(c + d*x)/f), x)
    pattern4610 = Pattern(Integral((a_ + (S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*(S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1481, cons1479, cons38)
    rule4610 = ReplacementRule(pattern4610, With4610)
    pattern4611 = Pattern(Integral((a_ + (S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*(S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons375)
    def replacement4611(p, m, b, d, c, a, n, x):
        rubi.append(4611)
        return Int(ExpandTrig((a + b*(S(1)/cos(c + d*x))**n)**p*(S(1)/cos(c + d*x))**m, x), x)
    rule4611 = ReplacementRule(pattern4611, replacement4611)
    pattern4612 = Pattern(Integral((a_ + (S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**p_*(S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons375)
    def replacement4612(p, m, b, d, c, n, a, x):
        rubi.append(4612)
        return Int(ExpandTrig((a + b*(S(1)/sin(c + d*x))**n)**p*(S(1)/sin(c + d*x))**m, x), x)
    rule4612 = ReplacementRule(pattern4612, replacement4612)
    def With4613(p, m, b, d, c, a, n, x):
        f = FreeFactors(cos(c + d*x), x)
        rubi.append(4613)
        return -Dist(f**(-m - n*p + S(1))/d, Subst(Int(x**(-m - n*p)*(a*(f*x)**n + b)**p*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2), x), x, cos(c + d*x)/f), x)
    pattern4613 = Pattern(Integral((a_ + (S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1481, cons85, cons38)
    rule4613 = ReplacementRule(pattern4613, With4613)
    def With4614(p, m, b, d, c, n, a, x):
        f = FreeFactors(sin(c + d*x), x)
        rubi.append(4614)
        return Dist(f**(-m - n*p + S(1))/d, Subst(Int(x**(-m - n*p)*(a*(f*x)**n + b)**p*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2), x), x, sin(c + d*x)/f), x)
    pattern4614 = Pattern(Integral((a_ + (S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1481, cons85, cons38)
    rule4614 = ReplacementRule(pattern4614, With4614)
    def With4615(p, m, b, d, c, a, n, x):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(4615)
        return Dist(f**(m + S(1))/d, Subst(Int(x**m*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p/(f**S(2)*x**S(2) + S(1)), x), x, tan(c + d*x)/f), x)
    pattern4615 = Pattern(Integral((a_ + (S(1)/cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1480, cons1479)
    rule4615 = ReplacementRule(pattern4615, With4615)
    def With4616(p, m, b, d, c, n, a, x):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(4616)
        return -Dist(f**(m + S(1))/d, Subst(Int(x**m*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p/(f**S(2)*x**S(2) + S(1)), x), x, S(1)/(f*tan(c + d*x))), x)
    pattern4616 = Pattern(Integral((a_ + (S(1)/sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1480, cons1479)
    rule4616 = ReplacementRule(pattern4616, With4616)
    pattern4617 = Pattern(Integral(((S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons45, cons38)
    def replacement4617(p, b, n2, d, a, n, c, x, e):
        rubi.append(4617)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*(S(1)/cos(d + e*x))**n)**(S(2)*p), x), x)
    rule4617 = ReplacementRule(pattern4617, replacement4617)
    pattern4618 = Pattern(Integral(((S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons45, cons38)
    def replacement4618(p, b, n2, d, a, n, c, x, e):
        rubi.append(4618)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*(S(1)/sin(d + e*x))**n)**(S(2)*p), x), x)
    rule4618 = ReplacementRule(pattern4618, replacement4618)
    pattern4619 = Pattern(Integral(((S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons46, cons45, cons147)
    def replacement4619(p, b, n2, d, a, n, c, x, e):
        rubi.append(4619)
        return Dist((b + S(2)*c*(S(1)/cos(d + e*x))**n)**(-S(2)*p)*(a + b*(S(1)/cos(d + e*x))**n + c*(S(1)/cos(d + e*x))**(S(2)*n))**p, Int(u*(b + S(2)*c*(S(1)/cos(d + e*x))**n)**(S(2)*p), x), x)
    rule4619 = ReplacementRule(pattern4619, replacement4619)
    pattern4620 = Pattern(Integral(((S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons46, cons45, cons147)
    def replacement4620(p, b, n2, d, a, n, c, x, e):
        rubi.append(4620)
        return Dist((b + S(2)*c*(S(1)/sin(d + e*x))**n)**(-S(2)*p)*(a + b*(S(1)/sin(d + e*x))**n + c*(S(1)/sin(d + e*x))**(S(2)*n))**p, Int(u*(b + S(2)*c*(S(1)/sin(d + e*x))**n)**(S(2)*p), x), x)
    rule4620 = ReplacementRule(pattern4620, replacement4620)
    def With4621(b, n2, d, a, n, c, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(4621)
        return Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*(S(1)/cos(d + e*x))**n - q), x), x) - Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*(S(1)/cos(d + e*x))**n + q), x), x)
    pattern4621 = Pattern(Integral(S(1)/((S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons226)
    rule4621 = ReplacementRule(pattern4621, With4621)
    def With4622(b, n2, d, a, n, c, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(4622)
        return Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*(S(1)/sin(d + e*x))**n - q), x), x) - Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*(S(1)/sin(d + e*x))**n + q), x), x)
    pattern4622 = Pattern(Integral(S(1)/((S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons226)
    rule4622 = ReplacementRule(pattern4622, With4622)
    def With4623(p, m, b, n2, d, a, n, c, x, e):
        f = FreeFactors(cos(d + e*x), x)
        rubi.append(4623)
        return -Dist(f/e, Subst(Int((f*x)**(-n*p)*(a*(f*x)**n + b)**p*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2), x), x, cos(d + e*x)/f), x)
    pattern4623 = Pattern(Integral(((S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**n2_*WC('c', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1481, cons376)
    rule4623 = ReplacementRule(pattern4623, With4623)
    def With4624(p, m, b, n2, d, a, n, c, x, e):
        f = FreeFactors(sin(d + e*x), x)
        rubi.append(4624)
        return Dist(f/e, Subst(Int((f*x)**(-n*p)*(a*(f*x)**n + b)**p*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2), x), x, sin(d + e*x)/f), x)
    pattern4624 = Pattern(Integral(((S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**n2_*WC('c', S(1)) + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1481, cons376)
    rule4624 = ReplacementRule(pattern4624, With4624)
    def With4625(p, m, b, n2, d, c, a, n, x, e):
        f = FreeFactors(tan(d + e*x), x)
        rubi.append(4625)
        return Dist(f**(m + S(1))/e, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1))*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + c*(f**S(2)*x**S(2) + S(1))**n, x)**p, x), x, tan(d + e*x)/f), x)
    pattern4625 = Pattern(Integral(((S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**n2_*WC('c', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**n_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons46, cons1480, cons1479)
    rule4625 = ReplacementRule(pattern4625, With4625)
    def With4626(p, m, b, n2, d, c, a, n, x, e):
        f = FreeFactors(S(1)/tan(d + e*x), x)
        rubi.append(4626)
        return -Dist(f**(m + S(1))/e, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1))*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + c*(f**S(2)*x**S(2) + S(1))**n, x)**p, x), x, S(1)/(f*tan(d + e*x))), x)
    pattern4626 = Pattern(Integral(((S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**n2_*WC('c', S(1)) + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons46, cons1480, cons1479)
    rule4626 = ReplacementRule(pattern4626, With4626)
    pattern4627 = Pattern(Integral(((S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*(S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons45, cons38)
    def replacement4627(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(4627)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*(S(1)/cos(d + e*x))**n)**(S(2)*p)*(S(1)/cos(d + e*x))**m, x), x)
    rule4627 = ReplacementRule(pattern4627, replacement4627)
    pattern4628 = Pattern(Integral(((S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*(S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons45, cons38)
    def replacement4628(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(4628)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*(S(1)/sin(d + e*x))**n)**(S(2)*p)*(S(1)/sin(d + e*x))**m, x), x)
    rule4628 = ReplacementRule(pattern4628, replacement4628)
    pattern4629 = Pattern(Integral(((S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*(S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons45, cons147)
    def replacement4629(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(4629)
        return Dist((b + S(2)*c*(S(1)/cos(d + e*x))**n)**(-S(2)*p)*(a + b*(S(1)/cos(d + e*x))**n + c*(S(1)/cos(d + e*x))**(S(2)*n))**p, Int((b + S(2)*c*(S(1)/cos(d + e*x))**n)**(S(2)*p)*(S(1)/cos(d + e*x))**m, x), x)
    rule4629 = ReplacementRule(pattern4629, replacement4629)
    pattern4630 = Pattern(Integral(((S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*(S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons45, cons147)
    def replacement4630(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(4630)
        return Dist((b + S(2)*c*(S(1)/sin(d + e*x))**n)**(-S(2)*p)*(a + b*(S(1)/sin(d + e*x))**n + c*(S(1)/sin(d + e*x))**(S(2)*n))**p, Int((b + S(2)*c*(S(1)/sin(d + e*x))**n)**(S(2)*p)*(S(1)/sin(d + e*x))**m, x), x)
    rule4630 = ReplacementRule(pattern4630, replacement4630)
    pattern4631 = Pattern(Integral(((S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*(S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons375)
    def replacement4631(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(4631)
        return Int(ExpandTrig((a + b*(S(1)/cos(d + e*x))**n + c*(S(1)/cos(d + e*x))**(S(2)*n))**p*(S(1)/cos(d + e*x))**m, x), x)
    rule4631 = ReplacementRule(pattern4631, replacement4631)
    pattern4632 = Pattern(Integral(((S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**p_*(S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons375)
    def replacement4632(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(4632)
        return Int(ExpandTrig((a + b*(S(1)/sin(d + e*x))**n + c*(S(1)/sin(d + e*x))**(S(2)*n))**p*(S(1)/sin(d + e*x))**m, x), x)
    rule4632 = ReplacementRule(pattern4632, replacement4632)
    def With4633(p, m, b, n2, d, c, n, a, x, e):
        f = FreeFactors(cos(d + e*x), x)
        rubi.append(4633)
        return -Dist(f**(-m - n*p + S(1))/e, Subst(Int(x**(-m - S(2)*n*p)*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*(b*(f*x)**n + c*(f*x)**(S(2)*n) + c)**p, x), x, cos(d + e*x)/f), x)
    pattern4633 = Pattern(Integral((a_ + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons1481, cons85, cons38)
    rule4633 = ReplacementRule(pattern4633, With4633)
    def With4634(p, m, b, n2, d, c, n, a, x, e):
        f = FreeFactors(sin(d + e*x), x)
        rubi.append(4634)
        return Dist(f**(-m - n*p + S(1))/e, Subst(Int(x**(-m - S(2)*n*p)*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*(b*(f*x)**n + c*(f*x)**(S(2)*n) + c)**p, x), x, sin(d + e*x)/f), x)
    pattern4634 = Pattern(Integral((a_ + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons1481, cons85, cons38)
    rule4634 = ReplacementRule(pattern4634, With4634)
    def With4635(p, m, b, n2, d, c, a, n, x, e):
        f = FreeFactors(tan(d + e*x), x)
        rubi.append(4635)
        return Dist(f**(m + S(1))/e, Subst(Int(x**m*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + c*(f**S(2)*x**S(2) + S(1))**n, x)**p/(f**S(2)*x**S(2) + S(1)), x), x, tan(d + e*x)/f), x)
    pattern4635 = Pattern(Integral((a_ + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**n_*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons1479)
    rule4635 = ReplacementRule(pattern4635, With4635)
    def With4636(p, m, b, n2, d, c, n, a, x, e):
        f = FreeFactors(S(1)/tan(d + e*x), x)
        rubi.append(4636)
        return -Dist(f**(m + S(1))/e, Subst(Int(x**m*ExpandToSum(a + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + c*(f**S(2)*x**S(2) + S(1))**n, x)**p/(f**S(2)*x**S(2) + S(1)), x), x, S(1)/(f*tan(d + e*x))), x)
    pattern4636 = Pattern(Integral((a_ + (S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_*WC('b', S(1)) + (S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons1479)
    rule4636 = ReplacementRule(pattern4636, With4636)
    pattern4637 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons85)
    def replacement4637(B, b, d, c, a, n, A, x, e):
        rubi.append(4637)
        return Dist(S(4)**(-n)*c**(-n), Int((A + B/cos(d + e*x))*(b + S(2)*c/cos(d + e*x))**(S(2)*n), x), x)
    rule4637 = ReplacementRule(pattern4637, replacement4637)
    pattern4638 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons85)
    def replacement4638(B, b, d, c, a, n, A, x, e):
        rubi.append(4638)
        return Dist(S(4)**(-n)*c**(-n), Int((A + B/sin(d + e*x))*(b + S(2)*c/sin(d + e*x))**(S(2)*n), x), x)
    rule4638 = ReplacementRule(pattern4638, replacement4638)
    pattern4639 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons23)
    def replacement4639(B, b, d, c, a, n, A, x, e):
        rubi.append(4639)
        return Dist((b + S(2)*c/cos(d + e*x))**(-S(2)*n)*(a + b/cos(d + e*x) + c/cos(d + e*x)**S(2))**n, Int((A + B/cos(d + e*x))*(b + S(2)*c/cos(d + e*x))**(S(2)*n), x), x)
    rule4639 = ReplacementRule(pattern4639, replacement4639)
    pattern4640 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons23)
    def replacement4640(B, b, d, c, a, n, A, x, e):
        rubi.append(4640)
        return Dist((b + S(2)*c/sin(d + e*x))**(-S(2)*n)*(a + b/sin(d + e*x) + c/sin(d + e*x)**S(2))**n, Int((A + B/sin(d + e*x))*(b + S(2)*c/sin(d + e*x))**(S(2)*n), x), x)
    rule4640 = ReplacementRule(pattern4640, replacement4640)
    def With4641(B, b, d, a, c, A, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(4641)
        return Dist(B - (-S(2)*A*c + B*b)/q, Int(S(1)/(b + S(2)*c/cos(d + e*x) - q), x), x) + Dist(B + (-S(2)*A*c + B*b)/q, Int(S(1)/(b + S(2)*c/cos(d + e*x) + q), x), x)
    pattern4641 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226)
    rule4641 = ReplacementRule(pattern4641, With4641)
    def With4642(B, b, d, c, a, A, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(4642)
        return Dist(B - (-S(2)*A*c + B*b)/q, Int(S(1)/(b + S(2)*c/sin(d + e*x) - q), x), x) + Dist(B + (-S(2)*A*c + B*b)/q, Int(S(1)/(b + S(2)*c/sin(d + e*x) + q), x), x)
    pattern4642 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226)
    rule4642 = ReplacementRule(pattern4642, With4642)
    pattern4643 = Pattern(Integral((A_ + WC('B', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226, cons85)
    def replacement4643(B, b, d, a, c, n, A, x, e):
        rubi.append(4643)
        return Int(ExpandTrig((A + B/cos(d + e*x))*(a + b/cos(d + e*x) + c/cos(d + e*x)**S(2))**n, x), x)
    rule4643 = ReplacementRule(pattern4643, replacement4643)
    pattern4644 = Pattern(Integral((A_ + WC('B', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226, cons85)
    def replacement4644(B, b, d, c, a, n, A, x, e):
        rubi.append(4644)
        return Int(ExpandTrig((A + B/sin(d + e*x))*(a + b/sin(d + e*x) + c/sin(d + e*x)**S(2))**n, x), x)
    rule4644 = ReplacementRule(pattern4644, replacement4644)
    pattern4645 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons62)
    def replacement4645(m, f, d, c, x, e):
        rubi.append(4645)
        return -Dist(d*m/f, Int((c + d*x)**(m + S(-1))*log(-I*exp(I*(e + f*x)) + S(1)), x), x) + Dist(d*m/f, Int((c + d*x)**(m + S(-1))*log(I*exp(I*(e + f*x)) + S(1)), x), x) + Simp(-S(2)*I*(c + d*x)**m*ArcTan(exp(I*e + I*f*x))/f, x)
    rule4645 = ReplacementRule(pattern4645, replacement4645)
    pattern4646 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons62)
    def replacement4646(m, f, d, c, x, e):
        rubi.append(4646)
        return -Dist(d*m/f, Int((c + d*x)**(m + S(-1))*log(-exp(I*(e + f*x)) + S(1)), x), x) + Dist(d*m/f, Int((c + d*x)**(m + S(-1))*log(exp(I*(e + f*x)) + S(1)), x), x) + Simp(-S(2)*(c + d*x)**m*atanh(exp(I*e + I*f*x))/f, x)
    rule4646 = ReplacementRule(pattern4646, replacement4646)
    pattern4647 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons7, cons27, cons48, cons125, cons31, cons168)
    def replacement4647(m, f, d, c, x, e):
        rubi.append(4647)
        return -Dist(d*m/f, Int((c + d*x)**(m + S(-1))*tan(e + f*x), x), x) + Simp((c + d*x)**m*tan(e + f*x)/f, x)
    rule4647 = ReplacementRule(pattern4647, replacement4647)
    pattern4648 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons7, cons27, cons48, cons125, cons31, cons168)
    def replacement4648(m, f, d, c, x, e):
        rubi.append(4648)
        return Dist(d*m/f, Int((c + d*x)**(m + S(-1))/tan(e + f*x), x), x) - Simp((c + d*x)**m/(f*tan(e + f*x)), x)
    rule4648 = ReplacementRule(pattern4648, replacement4648)
    pattern4649 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons3, cons7, cons27, cons48, cons125, cons87, cons165, cons1644)
    def replacement4649(f, b, d, c, n, x, e):
        rubi.append(4649)
        return Dist(b**S(2)*(n + S(-2))/(n + S(-1)), Int((b/cos(e + f*x))**(n + S(-2))*(c + d*x), x), x) - Simp(b**S(2)*d*(b/cos(e + f*x))**(n + S(-2))/(f**S(2)*(n + S(-2))*(n + S(-1))), x) + Simp(b**S(2)*(b/cos(e + f*x))**(n + S(-2))*(c + d*x)*tan(e + f*x)/(f*(n + S(-1))), x)
    rule4649 = ReplacementRule(pattern4649, replacement4649)
    pattern4650 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons3, cons7, cons27, cons48, cons125, cons87, cons165, cons1644)
    def replacement4650(f, b, d, c, n, x, e):
        rubi.append(4650)
        return Dist(b**S(2)*(n + S(-2))/(n + S(-1)), Int((b/sin(e + f*x))**(n + S(-2))*(c + d*x), x), x) - Simp(b**S(2)*d*(b/sin(e + f*x))**(n + S(-2))/(f**S(2)*(n + S(-2))*(n + S(-1))), x) - Simp(b**S(2)*(b/sin(e + f*x))**(n + S(-2))*(c + d*x)/(f*(n + S(-1))*tan(e + f*x)), x)
    rule4650 = ReplacementRule(pattern4650, replacement4650)
    pattern4651 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons3, cons7, cons27, cons48, cons125, cons93, cons165, cons1644, cons166)
    def replacement4651(m, f, b, d, c, n, x, e):
        rubi.append(4651)
        return Dist(b**S(2)*(n + S(-2))/(n + S(-1)), Int((b/cos(e + f*x))**(n + S(-2))*(c + d*x)**m, x), x) + Dist(b**S(2)*d**S(2)*m*(m + S(-1))/(f**S(2)*(n + S(-2))*(n + S(-1))), Int((b/cos(e + f*x))**(n + S(-2))*(c + d*x)**(m + S(-2)), x), x) + Simp(b**S(2)*(b/cos(e + f*x))**(n + S(-2))*(c + d*x)**m*tan(e + f*x)/(f*(n + S(-1))), x) - Simp(b**S(2)*d*m*(b/cos(e + f*x))**(n + S(-2))*(c + d*x)**(m + S(-1))/(f**S(2)*(n + S(-2))*(n + S(-1))), x)
    rule4651 = ReplacementRule(pattern4651, replacement4651)
    pattern4652 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons3, cons7, cons27, cons48, cons125, cons93, cons165, cons1644, cons166)
    def replacement4652(m, f, b, d, c, n, x, e):
        rubi.append(4652)
        return Dist(b**S(2)*(n + S(-2))/(n + S(-1)), Int((b/sin(e + f*x))**(n + S(-2))*(c + d*x)**m, x), x) + Dist(b**S(2)*d**S(2)*m*(m + S(-1))/(f**S(2)*(n + S(-2))*(n + S(-1))), Int((b/sin(e + f*x))**(n + S(-2))*(c + d*x)**(m + S(-2)), x), x) - Simp(b**S(2)*(b/sin(e + f*x))**(n + S(-2))*(c + d*x)**m/(f*(n + S(-1))*tan(e + f*x)), x) - Simp(b**S(2)*d*m*(b/sin(e + f*x))**(n + S(-2))*(c + d*x)**(m + S(-1))/(f**S(2)*(n + S(-2))*(n + S(-1))), x)
    rule4652 = ReplacementRule(pattern4652, replacement4652)
    pattern4653 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons3, cons7, cons27, cons48, cons125, cons87, cons89)
    def replacement4653(f, b, d, c, n, x, e):
        rubi.append(4653)
        return Dist((n + S(1))/(b**S(2)*n), Int((b/cos(e + f*x))**(n + S(2))*(c + d*x), x), x) + Simp(d*(b/cos(e + f*x))**n/(f**S(2)*n**S(2)), x) - Simp((b/cos(e + f*x))**(n + S(1))*(c + d*x)*sin(e + f*x)/(b*f*n), x)
    rule4653 = ReplacementRule(pattern4653, replacement4653)
    pattern4654 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons3, cons7, cons27, cons48, cons125, cons87, cons89)
    def replacement4654(f, b, d, c, n, x, e):
        rubi.append(4654)
        return Dist((n + S(1))/(b**S(2)*n), Int((b/sin(e + f*x))**(n + S(2))*(c + d*x), x), x) + Simp(d*(b/sin(e + f*x))**n/(f**S(2)*n**S(2)), x) + Simp((b/sin(e + f*x))**(n + S(1))*(c + d*x)*cos(e + f*x)/(b*f*n), x)
    rule4654 = ReplacementRule(pattern4654, replacement4654)
    pattern4655 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons3, cons7, cons27, cons48, cons125, cons93, cons89, cons166)
    def replacement4655(m, f, b, d, c, n, x, e):
        rubi.append(4655)
        return Dist((n + S(1))/(b**S(2)*n), Int((b/cos(e + f*x))**(n + S(2))*(c + d*x)**m, x), x) - Dist(d**S(2)*m*(m + S(-1))/(f**S(2)*n**S(2)), Int((b/cos(e + f*x))**n*(c + d*x)**(m + S(-2)), x), x) - Simp((b/cos(e + f*x))**(n + S(1))*(c + d*x)**m*sin(e + f*x)/(b*f*n), x) + Simp(d*m*(b/cos(e + f*x))**n*(c + d*x)**(m + S(-1))/(f**S(2)*n**S(2)), x)
    rule4655 = ReplacementRule(pattern4655, replacement4655)
    pattern4656 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons3, cons7, cons27, cons48, cons125, cons93, cons89, cons166)
    def replacement4656(m, f, b, d, c, n, x, e):
        rubi.append(4656)
        return Dist((n + S(1))/(b**S(2)*n), Int((b/sin(e + f*x))**(n + S(2))*(c + d*x)**m, x), x) - Dist(d**S(2)*m*(m + S(-1))/(f**S(2)*n**S(2)), Int((b/sin(e + f*x))**n*(c + d*x)**(m + S(-2)), x), x) + Simp((b/sin(e + f*x))**(n + S(1))*(c + d*x)**m*cos(e + f*x)/(b*f*n), x) + Simp(d*m*(b/sin(e + f*x))**n*(c + d*x)**(m + S(-1))/(f**S(2)*n**S(2)), x)
    rule4656 = ReplacementRule(pattern4656, replacement4656)
    pattern4657 = Pattern(Integral((WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons23)
    def replacement4657(m, f, b, d, c, n, x, e):
        rubi.append(4657)
        return Dist((b/cos(e + f*x))**n*(b*cos(e + f*x))**n, Int((b*cos(e + f*x))**(-n)*(c + d*x)**m, x), x)
    rule4657 = ReplacementRule(pattern4657, replacement4657)
    pattern4658 = Pattern(Integral((WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons23)
    def replacement4658(m, f, b, d, c, n, x, e):
        rubi.append(4658)
        return Dist((b/sin(e + f*x))**n*(b*sin(e + f*x))**n, Int((b*sin(e + f*x))**(-n)*(c + d*x)**m, x), x)
    rule4658 = ReplacementRule(pattern4658, replacement4658)
    pattern4659 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons528)
    def replacement4659(m, f, b, d, c, n, a, x, e):
        rubi.append(4659)
        return Int(ExpandIntegrand((c + d*x)**m, (a + b/cos(e + f*x))**n, x), x)
    rule4659 = ReplacementRule(pattern4659, replacement4659)
    pattern4660 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons528)
    def replacement4660(m, f, b, d, c, n, a, x, e):
        rubi.append(4660)
        return Int(ExpandIntegrand((c + d*x)**m, (a + b/sin(e + f*x))**n, x), x)
    rule4660 = ReplacementRule(pattern4660, replacement4660)
    pattern4661 = Pattern(Integral((a_ + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons196, cons62)
    def replacement4661(m, f, b, d, c, n, a, x, e):
        rubi.append(4661)
        return Int(ExpandIntegrand((c + d*x)**m, (a*cos(e + f*x) + b)**n*cos(e + f*x)**(-n), x), x)
    rule4661 = ReplacementRule(pattern4661, replacement4661)
    pattern4662 = Pattern(Integral((a_ + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons196, cons62)
    def replacement4662(m, f, b, d, c, n, a, x, e):
        rubi.append(4662)
        return Int(ExpandIntegrand((c + d*x)**m, (a*sin(e + f*x) + b)**n*sin(e + f*x)**(-n), x), x)
    rule4662 = ReplacementRule(pattern4662, replacement4662)
    pattern4663 = Pattern(Integral(u_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(v_))**WC('n', S(1)), x_), cons2, cons3, cons21, cons4, cons810, cons811)
    def replacement4663(v, u, m, b, a, n, x):
        rubi.append(4663)
        return Int((a + b/cos(ExpandToSum(v, x)))**n*ExpandToSum(u, x)**m, x)
    rule4663 = ReplacementRule(pattern4663, replacement4663)
    pattern4664 = Pattern(Integral(u_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(v_))**WC('n', S(1)), x_), cons2, cons3, cons21, cons4, cons810, cons811)
    def replacement4664(v, u, m, b, a, n, x):
        rubi.append(4664)
        return Int((a + b/sin(ExpandToSum(v, x)))**n*ExpandToSum(u, x)**m, x)
    rule4664 = ReplacementRule(pattern4664, replacement4664)
    pattern4665 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement4665(m, f, b, d, c, a, n, x, e):
        rubi.append(4665)
        return Int((a + b/cos(e + f*x))**n*(c + d*x)**m, x)
    rule4665 = ReplacementRule(pattern4665, replacement4665)
    pattern4666 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement4666(m, f, b, d, a, n, c, x, e):
        rubi.append(4666)
        return Int((a + b/sin(e + f*x))**n*(c + d*x)**m, x)
    rule4666 = ReplacementRule(pattern4666, replacement4666)
    pattern4667 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons5, cons1573, cons38)
    def replacement4667(p, b, d, c, a, n, x):
        rubi.append(4667)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + S(1)/n)*(a + b/cos(c + d*x))**p, x), x, x**n), x)
    rule4667 = ReplacementRule(pattern4667, replacement4667)
    pattern4668 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons5, cons1573, cons38)
    def replacement4668(p, b, d, a, c, n, x):
        rubi.append(4668)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + S(1)/n)*(a + b/sin(c + d*x))**p, x), x, x**n), x)
    rule4668 = ReplacementRule(pattern4668, replacement4668)
    pattern4669 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons1495)
    def replacement4669(p, b, d, c, a, n, x):
        rubi.append(4669)
        return Int((a + b/cos(c + d*x**n))**p, x)
    rule4669 = ReplacementRule(pattern4669, replacement4669)
    pattern4670 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons1495)
    def replacement4670(p, b, d, a, c, n, x):
        rubi.append(4670)
        return Int((a + b/sin(c + d*x**n))**p, x)
    rule4670 = ReplacementRule(pattern4670, replacement4670)
    pattern4671 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/cos(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons68, cons69)
    def replacement4671(p, u, b, d, c, a, n, x):
        rubi.append(4671)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b/cos(c + d*x**n))**p, x), x, u), x)
    rule4671 = ReplacementRule(pattern4671, replacement4671)
    pattern4672 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/sin(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons68, cons69)
    def replacement4672(p, u, b, d, a, c, n, x):
        rubi.append(4672)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b/sin(c + d*x**n))**p, x), x, u), x)
    rule4672 = ReplacementRule(pattern4672, replacement4672)
    pattern4673 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/cos(u_))**WC('p', S(1)), x_), cons2, cons3, cons5, cons823, cons824)
    def replacement4673(p, u, b, a, x):
        rubi.append(4673)
        return Int((a + b/cos(ExpandToSum(u, x)))**p, x)
    rule4673 = ReplacementRule(pattern4673, replacement4673)
    pattern4674 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/sin(u_))**WC('p', S(1)), x_), cons2, cons3, cons5, cons823, cons824)
    def replacement4674(p, u, b, a, x):
        rubi.append(4674)
        return Int((a + b/sin(ExpandToSum(u, x)))**p, x)
    rule4674 = ReplacementRule(pattern4674, replacement4674)
    pattern4675 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons1574, cons38)
    def replacement4675(p, m, b, d, c, a, n, x):
        rubi.append(4675)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + (m + S(1))/n)*(a + b/cos(c + d*x))**p, x), x, x**n), x)
    rule4675 = ReplacementRule(pattern4675, replacement4675)
    pattern4676 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons1574, cons38)
    def replacement4676(p, m, b, d, a, c, n, x):
        rubi.append(4676)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + (m + S(1))/n)*(a + b/sin(c + d*x))**p, x), x, x**n), x)
    rule4676 = ReplacementRule(pattern4676, replacement4676)
    pattern4677 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons1576)
    def replacement4677(p, m, b, d, c, a, n, x):
        rubi.append(4677)
        return Int(x**m*(a + b/cos(c + d*x**n))**p, x)
    rule4677 = ReplacementRule(pattern4677, replacement4677)
    pattern4678 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons1576)
    def replacement4678(p, m, b, d, a, c, n, x):
        rubi.append(4678)
        return Int(x**m*(a + b/sin(c + d*x**n))**p, x)
    rule4678 = ReplacementRule(pattern4678, replacement4678)
    pattern4679 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement4679(p, m, b, d, c, a, n, x, e):
        rubi.append(4679)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b/cos(c + d*x**n))**p, x), x)
    rule4679 = ReplacementRule(pattern4679, replacement4679)
    pattern4680 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement4680(p, m, b, d, a, c, n, x, e):
        rubi.append(4680)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b/sin(c + d*x**n))**p, x), x)
    rule4680 = ReplacementRule(pattern4680, replacement4680)
    pattern4681 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(u_))**WC('p', S(1)), x_), cons2, cons3, cons48, cons21, cons5, cons823, cons824)
    def replacement4681(p, u, m, b, a, x, e):
        rubi.append(4681)
        return Int((e*x)**m*(a + b/cos(ExpandToSum(u, x)))**p, x)
    rule4681 = ReplacementRule(pattern4681, replacement4681)
    pattern4682 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(u_))**WC('p', S(1)), x_), cons2, cons3, cons48, cons21, cons5, cons823, cons824)
    def replacement4682(p, u, m, b, a, x, e):
        rubi.append(4682)
        return Int((e*x)**m*(a + b/sin(ExpandToSum(u, x)))**p, x)
    rule4682 = ReplacementRule(pattern4682, replacement4682)
    pattern4683 = Pattern(Integral(x_**WC('m', S(1))*(S(1)/cos(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**p_*sin(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons5, cons31, cons85, cons1577, cons1645)
    def replacement4683(p, m, b, a, n, x):
        rubi.append(4683)
        return -Dist((m - n + S(1))/(b*n*(p + S(-1))), Int(x**(m - n)*(S(1)/cos(a + b*x**n))**(p + S(-1)), x), x) + Simp(x**(m - n + S(1))*(S(1)/cos(a + b*x**n))**(p + S(-1))/(b*n*(p + S(-1))), x)
    rule4683 = ReplacementRule(pattern4683, replacement4683)
    pattern4684 = Pattern(Integral(x_**WC('m', S(1))*(S(1)/sin(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**p_*cos(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons5, cons31, cons85, cons1577, cons1645)
    def replacement4684(p, m, b, a, n, x):
        rubi.append(4684)
        return Dist((m - n + S(1))/(b*n*(p + S(-1))), Int(x**(m - n)*(S(1)/sin(a + b*x**n))**(p + S(-1)), x), x) - Simp(x**(m - n + S(1))*(S(1)/sin(a + b*x**n))**(p + S(-1))/(b*n*(p + S(-1))), x)
    rule4684 = ReplacementRule(pattern4684, replacement4684)
    return [rule3917, rule3918, rule3919, rule3920, rule3921, rule3922, rule3923, rule3924, rule3925, rule3926, rule3927, rule3928, rule3929, rule3930, rule3931, rule3932, rule3933, rule3934, rule3935, rule3936, rule3937, rule3938, rule3939, rule3940, rule3941, rule3942, rule3943, rule3944, rule3945, rule3946, rule3947, rule3948, rule3949, rule3950, rule3951, rule3952, rule3953, rule3954, rule3955, rule3956, rule3957, rule3958, rule3959, rule3960, rule3961, rule3962, rule3963, rule3964, rule3965, rule3966, rule3967, rule3968, rule3969, rule3970, rule3971, rule3972, rule3973, rule3974, rule3975, rule3976, rule3977, rule3978, rule3979, rule3980, rule3981, rule3982, rule3983, rule3984, rule3985, rule3986, rule3987, rule3988, rule3989, rule3990, rule3991, rule3992, rule3993, rule3994, rule3995, rule3996, rule3997, rule3998, rule3999, rule4000, rule4001, rule4002, rule4003, rule4004, rule4005, rule4006, rule4007, rule4008, rule4009, rule4010, rule4011, rule4012, rule4013, rule4014, rule4015, rule4016, rule4017, rule4018, rule4019, rule4020, rule4021, rule4022, rule4023, rule4024, rule4025, rule4026, rule4027, rule4028, rule4029, rule4030, rule4031, rule4032, rule4033, rule4034, rule4035, rule4036, rule4037, rule4038, rule4039, rule4040, rule4041, rule4042, rule4043, rule4044, rule4045, rule4046, rule4047, rule4048, rule4049, rule4050, rule4051, rule4052, rule4053, rule4054, rule4055, rule4056, rule4057, rule4058, rule4059, rule4060, rule4061, rule4062, rule4063, rule4064, rule4065, rule4066, rule4067, rule4068, rule4069, rule4070, rule4071, rule4072, rule4073, rule4074, rule4075, rule4076, rule4077, rule4078, rule4079, rule4080, rule4081, rule4082, rule4083, rule4084, rule4085, rule4086, rule4087, rule4088, rule4089, rule4090, rule4091, rule4092, rule4093, rule4094, rule4095, rule4096, rule4097, rule4098, rule4099, rule4100, rule4101, rule4102, rule4103, rule4104, rule4105, rule4106, rule4107, rule4108, rule4109, rule4110, rule4111, rule4112, rule4113, rule4114, rule4115, rule4116, rule4117, rule4118, rule4119, rule4120, rule4121, rule4122, rule4123, rule4124, rule4125, rule4126, rule4127, rule4128, rule4129, rule4130, rule4131, rule4132, rule4133, rule4134, rule4135, rule4136, rule4137, rule4138, rule4139, rule4140, rule4141, rule4142, rule4143, rule4144, rule4145, rule4146, rule4147, rule4148, rule4149, rule4150, rule4151, rule4152, rule4153, rule4154, rule4155, rule4156, rule4157, rule4158, rule4159, rule4160, rule4161, rule4162, rule4163, rule4164, rule4165, rule4166, rule4167, rule4168, rule4169, rule4170, rule4171, rule4172, rule4173, rule4174, rule4175, rule4176, rule4177, rule4178, rule4179, rule4180, rule4181, rule4182, rule4183, rule4184, rule4185, rule4186, rule4187, rule4188, rule4189, rule4190, rule4191, rule4192, rule4193, rule4194, rule4195, rule4196, rule4197, rule4198, rule4199, rule4200, rule4201, rule4202, rule4203, rule4204, rule4205, rule4206, rule4207, rule4208, rule4209, rule4210, rule4211, rule4212, rule4213, rule4214, rule4215, rule4216, rule4217, rule4218, rule4219, rule4220, rule4221, rule4222, rule4223, rule4224, rule4225, rule4226, rule4227, rule4228, rule4229, rule4230, rule4231, rule4232, rule4233, rule4234, rule4235, rule4236, rule4237, rule4238, rule4239, rule4240, rule4241, rule4242, rule4243, rule4244, rule4245, rule4246, rule4247, rule4248, rule4249, rule4250, rule4251, rule4252, rule4253, rule4254, rule4255, rule4256, rule4257, rule4258, rule4259, rule4260, rule4261, rule4262, rule4263, rule4264, rule4265, rule4266, rule4267, rule4268, rule4269, rule4270, rule4271, rule4272, rule4273, rule4274, rule4275, rule4276, rule4277, rule4278, rule4279, rule4280, rule4281, rule4282, rule4283, rule4284, rule4285, rule4286, rule4287, rule4288, rule4289, rule4290, rule4291, rule4292, rule4293, rule4294, rule4295, rule4296, rule4297, rule4298, rule4299, rule4300, rule4301, rule4302, rule4303, rule4304, rule4305, rule4306, rule4307, rule4308, rule4309, rule4310, rule4311, rule4312, rule4313, rule4314, rule4315, rule4316, rule4317, rule4318, rule4319, rule4320, rule4321, rule4322, rule4323, rule4324, rule4325, rule4326, rule4327, rule4328, rule4329, rule4330, rule4331, rule4332, rule4333, rule4334, rule4335, rule4336, rule4337, rule4338, rule4339, rule4340, rule4341, rule4342, rule4343, rule4344, rule4345, rule4346, rule4347, rule4348, rule4349, rule4350, rule4351, rule4352, rule4353, rule4354, rule4355, rule4356, rule4357, rule4358, rule4359, rule4360, rule4361, rule4362, rule4363, rule4364, rule4365, rule4366, rule4367, rule4368, rule4369, rule4370, rule4371, rule4372, rule4373, rule4374, rule4375, rule4376, rule4377, rule4378, rule4379, rule4380, rule4381, rule4382, rule4383, rule4384, rule4385, rule4386, rule4387, rule4388, rule4389, rule4390, rule4391, rule4392, rule4393, rule4394, rule4395, rule4396, rule4397, rule4398, rule4399, rule4400, rule4401, rule4402, rule4403, rule4404, rule4405, rule4406, rule4407, rule4408, rule4409, rule4410, rule4411, rule4412, rule4413, rule4414, rule4415, rule4416, rule4417, rule4418, rule4419, rule4420, rule4421, rule4422, rule4423, rule4424, rule4425, rule4426, rule4427, rule4428, rule4429, rule4430, rule4431, rule4432, rule4433, rule4434, rule4435, rule4436, rule4437, rule4438, rule4439, rule4440, rule4441, rule4442, rule4443, rule4444, rule4445, rule4446, rule4447, rule4448, rule4449, rule4450, rule4451, rule4452, rule4453, rule4454, rule4455, rule4456, rule4457, rule4458, rule4459, rule4460, rule4461, rule4462, rule4463, rule4464, rule4465, rule4466, rule4467, rule4468, rule4469, rule4470, rule4471, rule4472, rule4473, rule4474, rule4475, rule4476, rule4477, rule4478, rule4479, rule4480, rule4481, rule4482, rule4483, rule4484, rule4485, rule4486, rule4487, rule4488, rule4489, rule4490, rule4491, rule4492, rule4493, rule4494, rule4495, rule4496, rule4497, rule4498, rule4499, rule4500, rule4501, rule4502, rule4503, rule4504, rule4505, rule4506, rule4507, rule4508, rule4509, rule4510, rule4511, rule4512, rule4513, rule4514, rule4515, rule4516, rule4517, rule4518, rule4519, rule4520, rule4521, rule4522, rule4523, rule4524, rule4525, rule4526, rule4527, rule4528, rule4529, rule4530, rule4531, rule4532, rule4533, rule4534, rule4535, rule4536, rule4537, rule4538, rule4539, rule4540, rule4541, rule4542, rule4543, rule4544, rule4545, rule4546, rule4547, rule4548, rule4549, rule4550, rule4551, rule4552, rule4553, rule4554, rule4555, rule4556, rule4557, rule4558, rule4559, rule4560, rule4561, rule4562, rule4563, rule4564, rule4565, rule4566, rule4567, rule4568, rule4569, rule4570, rule4571, rule4572, rule4573, rule4574, rule4575, rule4576, rule4577, rule4578, rule4579, rule4580, rule4581, rule4582, rule4583, rule4584, rule4585, rule4586, rule4587, rule4588, rule4589, rule4590, rule4591, rule4592, rule4593, rule4594, rule4595, rule4596, rule4597, rule4598, rule4599, rule4600, rule4601, rule4602, rule4603, rule4604, rule4605, rule4606, rule4607, rule4608, rule4609, rule4610, rule4611, rule4612, rule4613, rule4614, rule4615, rule4616, rule4617, rule4618, rule4619, rule4620, rule4621, rule4622, rule4623, rule4624, rule4625, rule4626, rule4627, rule4628, rule4629, rule4630, rule4631, rule4632, rule4633, rule4634, rule4635, rule4636, rule4637, rule4638, rule4639, rule4640, rule4641, rule4642, rule4643, rule4644, rule4645, rule4646, rule4647, rule4648, rule4649, rule4650, rule4651, rule4652, rule4653, rule4654, rule4655, rule4656, rule4657, rule4658, rule4659, rule4660, rule4661, rule4662, rule4663, rule4664, rule4665, rule4666, rule4667, rule4668, rule4669, rule4670, rule4671, rule4672, rule4673, rule4674, rule4675, rule4676, rule4677, rule4678, rule4679, rule4680, rule4681, rule4682, rule4683, rule4684, ]
