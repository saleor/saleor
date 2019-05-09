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

def inverse_trig(rubi):
    from sympy.integrals.rubi.constraints import cons87, cons88, cons2, cons3, cons7, cons89, cons1579, cons4, cons148, cons66, cons27, cons21, cons62, cons1734, cons1735, cons1736, cons1737, cons268, cons48, cons584, cons1738, cons128, cons338, cons163, cons137, cons230, cons5, cons1739, cons1740, cons1741, cons1742, cons1743, cons38, cons1744, cons1570, cons336, cons1745, cons147, cons125, cons208, cons54, cons242, cons1746, cons347, cons1747, cons486, cons961, cons93, cons94, cons162, cons272, cons1748, cons17, cons166, cons274, cons1749, cons18, cons1750, cons238, cons237, cons1751, cons246, cons1752, cons1753, cons1754, cons1755, cons1756, cons209, cons925, cons464, cons84, cons1757, cons1758, cons719, cons168, cons1759, cons667, cons1760, cons267, cons717, cons1761, cons1608, cons14, cons150, cons1198, cons1273, cons1360, cons1762, cons1763, cons34, cons35, cons36, cons1764, cons1765, cons165, cons1442, cons1766, cons1767, cons1768, cons1230, cons1769, cons1770, cons1771, cons1772, cons340, cons1773, cons1774, cons1775, cons1776, cons1043, cons85, cons31, cons1777, cons1497, cons1778, cons13, cons1779, cons1780, cons1781, cons1782, cons240, cons241, cons146, cons1783, cons1510, cons1784, cons1152, cons319, cons1785, cons1786, cons1787, cons1788, cons1789, cons1790, cons1791, cons1792, cons1793, cons1794, cons1795, cons1796, cons601, cons1797, cons261, cons1798, cons1799, cons1800, cons1801, cons1802, cons1803, cons1804, cons1805, cons177, cons117, cons1806, cons1807, cons1808, cons1809, cons1810, cons1811, cons1812, cons1813, cons1814, cons1815, cons1816, cons1817, cons1580, cons1818, cons1819, cons1820, cons1821, cons1822, cons1823, cons1824, cons1825, cons1826, cons1827, cons1828, cons1829, cons1830, cons1094, cons1831, cons1832, cons1833, cons1834, cons1835, cons383, cons1836, cons1837, cons818, cons463, cons1838, cons1839, cons1840, cons1841, cons1842, cons1843, cons1844, cons67, cons1845, cons1846, cons1847, cons1848, cons1849, cons1850, cons1851, cons552, cons1146, cons1852, cons1853, cons1242, cons1243, cons1854, cons178, cons1855, cons1856, cons1299, cons1857, cons1858

    pattern5031 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons87, cons88)
    def replacement5031(b, a, n, c, x):
        rubi.append(5031)
        return -Dist(b*c*n, Int(x*(a + b*asin(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*asin(c*x))**n, x)
    rule5031 = ReplacementRule(pattern5031, replacement5031)
    pattern5032 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons87, cons88)
    def replacement5032(b, a, n, c, x):
        rubi.append(5032)
        return Dist(b*c*n, Int(x*(a + b*acos(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*acos(c*x))**n, x)
    rule5032 = ReplacementRule(pattern5032, replacement5032)
    pattern5033 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons87, cons89)
    def replacement5033(b, a, n, c, x):
        rubi.append(5033)
        return Dist(c/(b*(n + S(1))), Int(x*(a + b*asin(c*x))**(n + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*asin(c*x))**(n + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5033 = ReplacementRule(pattern5033, replacement5033)
    pattern5034 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons87, cons89)
    def replacement5034(b, a, n, c, x):
        rubi.append(5034)
        return -Dist(c/(b*(n + S(1))), Int(x*(a + b*acos(c*x))**(n + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) - Simp((a + b*acos(c*x))**(n + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5034 = ReplacementRule(pattern5034, replacement5034)
    pattern5035 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement5035(b, a, n, c, x):
        rubi.append(5035)
        return Dist(S(1)/(b*c), Subst(Int(x**n*cos(a/b - x/b), x), x, a + b*asin(c*x)), x)
    rule5035 = ReplacementRule(pattern5035, replacement5035)
    pattern5036 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement5036(b, a, n, c, x):
        rubi.append(5036)
        return Dist(S(1)/(b*c), Subst(Int(x**n*sin(a/b - x/b), x), x, a + b*acos(c*x)), x)
    rule5036 = ReplacementRule(pattern5036, replacement5036)
    pattern5037 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/x_, x_), cons2, cons3, cons7, cons148)
    def replacement5037(b, a, n, c, x):
        rubi.append(5037)
        return Subst(Int((a + b*x)**n/tan(x), x), x, asin(c*x))
    rule5037 = ReplacementRule(pattern5037, replacement5037)
    pattern5038 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/x_, x_), cons2, cons3, cons7, cons148)
    def replacement5038(b, a, n, c, x):
        rubi.append(5038)
        return -Subst(Int((a + b*x)**n*tan(x), x), x, acos(c*x))
    rule5038 = ReplacementRule(pattern5038, replacement5038)
    pattern5039 = Pattern(Integral((x_*WC('d', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons148, cons66)
    def replacement5039(m, b, d, a, n, c, x):
        rubi.append(5039)
        return -Dist(b*c*n/(d*(m + S(1))), Int((d*x)**(m + S(1))*(a + b*asin(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((d*x)**(m + S(1))*(a + b*asin(c*x))**n/(d*(m + S(1))), x)
    rule5039 = ReplacementRule(pattern5039, replacement5039)
    pattern5040 = Pattern(Integral((x_*WC('d', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons148, cons66)
    def replacement5040(m, b, d, a, n, c, x):
        rubi.append(5040)
        return Dist(b*c*n/(d*(m + S(1))), Int((d*x)**(m + S(1))*(a + b*acos(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((d*x)**(m + S(1))*(a + b*acos(c*x))**n/(d*(m + S(1))), x)
    rule5040 = ReplacementRule(pattern5040, replacement5040)
    pattern5041 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons88)
    def replacement5041(m, b, a, c, n, x):
        rubi.append(5041)
        return -Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*asin(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x**(m + S(1))*(a + b*asin(c*x))**n/(m + S(1)), x)
    rule5041 = ReplacementRule(pattern5041, replacement5041)
    pattern5042 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons88)
    def replacement5042(m, b, a, c, n, x):
        rubi.append(5042)
        return Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*acos(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x**(m + S(1))*(a + b*acos(c*x))**n/(m + S(1)), x)
    rule5042 = ReplacementRule(pattern5042, replacement5042)
    pattern5043 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons1734)
    def replacement5043(m, b, a, c, n, x):
        rubi.append(5043)
        return -Dist(c**(-m + S(-1))/(b*(n + S(1))), Subst(Int(ExpandTrigReduce((a + b*x)**(n + S(1)), (m - (m + S(1))*sin(x)**S(2))*sin(x)**(m + S(-1)), x), x), x, asin(c*x)), x) + Simp(x**m*(a + b*asin(c*x))**(n + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5043 = ReplacementRule(pattern5043, replacement5043)
    pattern5044 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons1734)
    def replacement5044(m, b, a, c, n, x):
        rubi.append(5044)
        return -Dist(c**(-m + S(-1))/(b*(n + S(1))), Subst(Int(ExpandTrigReduce((a + b*x)**(n + S(1)), (m - (m + S(1))*cos(x)**S(2))*cos(x)**(m + S(-1)), x), x), x, acos(c*x)), x) - Simp(x**m*(a + b*acos(c*x))**(n + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5044 = ReplacementRule(pattern5044, replacement5044)
    pattern5045 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons1735)
    def replacement5045(m, b, a, c, n, x):
        rubi.append(5045)
        return -Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*asin(c*x))**(n + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Dist(c*(m + S(1))/(b*(n + S(1))), Int(x**(m + S(1))*(a + b*asin(c*x))**(n + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x**m*(a + b*asin(c*x))**(n + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5045 = ReplacementRule(pattern5045, replacement5045)
    pattern5046 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons1735)
    def replacement5046(m, b, a, c, n, x):
        rubi.append(5046)
        return Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*acos(c*x))**(n + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) - Dist(c*(m + S(1))/(b*(n + S(1))), Int(x**(m + S(1))*(a + b*acos(c*x))**(n + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) - Simp(x**m*(a + b*acos(c*x))**(n + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5046 = ReplacementRule(pattern5046, replacement5046)
    pattern5047 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons62)
    def replacement5047(m, b, a, c, n, x):
        rubi.append(5047)
        return Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*sin(x)**m*cos(x), x), x, asin(c*x)), x)
    rule5047 = ReplacementRule(pattern5047, replacement5047)
    pattern5048 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons62)
    def replacement5048(m, b, a, c, n, x):
        rubi.append(5048)
        return -Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*sin(x)*cos(x)**m, x), x, acos(c*x)), x)
    rule5048 = ReplacementRule(pattern5048, replacement5048)
    pattern5049 = Pattern(Integral((x_*WC('d', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons1736)
    def replacement5049(m, b, d, a, n, c, x):
        rubi.append(5049)
        return Int((d*x)**m*(a + b*asin(c*x))**n, x)
    rule5049 = ReplacementRule(pattern5049, replacement5049)
    pattern5050 = Pattern(Integral((x_*WC('d', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons1736)
    def replacement5050(m, b, d, a, n, c, x):
        rubi.append(5050)
        return Int((d*x)**m*(a + b*acos(c*x))**n, x)
    rule5050 = ReplacementRule(pattern5050, replacement5050)
    pattern5051 = Pattern(Integral(S(1)/(sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons268)
    def replacement5051(b, d, a, c, x, e):
        rubi.append(5051)
        return Simp(log(a + b*asin(c*x))/(b*c*sqrt(d)), x)
    rule5051 = ReplacementRule(pattern5051, replacement5051)
    pattern5052 = Pattern(Integral(S(1)/(sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons268)
    def replacement5052(b, d, a, c, x, e):
        rubi.append(5052)
        return -Simp(log(a + b*acos(c*x))/(b*c*sqrt(d)), x)
    rule5052 = ReplacementRule(pattern5052, replacement5052)
    pattern5053 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons268, cons584)
    def replacement5053(b, d, a, n, c, x, e):
        rubi.append(5053)
        return Simp((a + b*asin(c*x))**(n + S(1))/(b*c*sqrt(d)*(n + S(1))), x)
    rule5053 = ReplacementRule(pattern5053, replacement5053)
    pattern5054 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons268, cons584)
    def replacement5054(b, d, a, n, c, x, e):
        rubi.append(5054)
        return -Simp((a + b*acos(c*x))**(n + S(1))/(b*c*sqrt(d)*(n + S(1))), x)
    rule5054 = ReplacementRule(pattern5054, replacement5054)
    pattern5055 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1738)
    def replacement5055(b, d, a, n, c, x, e):
        rubi.append(5055)
        return Dist(sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*asin(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x)
    rule5055 = ReplacementRule(pattern5055, replacement5055)
    pattern5056 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1738)
    def replacement5056(b, d, a, n, c, x, e):
        rubi.append(5056)
        return Dist(sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*acos(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x)
    rule5056 = ReplacementRule(pattern5056, replacement5056)
    def With5057(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(5057)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asin(c*x), u, x)
    pattern5057 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons128)
    rule5057 = ReplacementRule(pattern5057, With5057)
    def With5058(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(5058)
        return Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acos(c*x), u, x)
    pattern5058 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons128)
    rule5058 = ReplacementRule(pattern5058, With5058)
    pattern5059 = Pattern(Integral(sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement5059(b, d, a, n, c, x, e):
        rubi.append(5059)
        return Dist(sqrt(d + e*x**S(2))/(S(2)*sqrt(-c**S(2)*x**S(2) + S(1))), Int((a + b*asin(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) - Dist(b*c*n*sqrt(d + e*x**S(2))/(S(2)*sqrt(-c**S(2)*x**S(2) + S(1))), Int(x*(a + b*asin(c*x))**(n + S(-1)), x), x) + Simp(x*(a + b*asin(c*x))**n*sqrt(d + e*x**S(2))/S(2), x)
    rule5059 = ReplacementRule(pattern5059, replacement5059)
    pattern5060 = Pattern(Integral(sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement5060(b, d, a, n, c, x, e):
        rubi.append(5060)
        return Dist(sqrt(d + e*x**S(2))/(S(2)*sqrt(-c**S(2)*x**S(2) + S(1))), Int((a + b*acos(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Dist(b*c*n*sqrt(d + e*x**S(2))/(S(2)*sqrt(-c**S(2)*x**S(2) + S(1))), Int(x*(a + b*acos(c*x))**(n + S(-1)), x), x) + Simp(x*(a + b*acos(c*x))**n*sqrt(d + e*x**S(2))/S(2), x)
    rule5060 = ReplacementRule(pattern5060, replacement5060)
    pattern5061 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons88, cons163)
    def replacement5061(p, b, d, a, n, c, x, e):
        rubi.append(5061)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*p + S(1)), Int(x*(a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp(x*(a + b*asin(c*x))**n*(d + e*x**S(2))**p/(S(2)*p + S(1)), x)
    rule5061 = ReplacementRule(pattern5061, replacement5061)
    pattern5062 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons88, cons163)
    def replacement5062(p, b, d, a, n, c, x, e):
        rubi.append(5062)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) + Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*p + S(1)), Int(x*(a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp(x*(a + b*acos(c*x))**n*(d + e*x**S(2))**p/(S(2)*p + S(1)), x)
    rule5062 = ReplacementRule(pattern5062, replacement5062)
    pattern5063 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons268)
    def replacement5063(b, d, a, n, c, x, e):
        rubi.append(5063)
        return -Dist(b*c*n/sqrt(d), Int(x*(a + b*asin(c*x))**(n + S(-1))/(d + e*x**S(2)), x), x) + Simp(x*(a + b*asin(c*x))**n/(d*sqrt(d + e*x**S(2))), x)
    rule5063 = ReplacementRule(pattern5063, replacement5063)
    pattern5064 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons268)
    def replacement5064(b, d, a, n, c, x, e):
        rubi.append(5064)
        return Dist(b*c*n/sqrt(d), Int(x*(a + b*acos(c*x))**(n + S(-1))/(d + e*x**S(2)), x), x) + Simp(x*(a + b*acos(c*x))**n/(d*sqrt(d + e*x**S(2))), x)
    rule5064 = ReplacementRule(pattern5064, replacement5064)
    pattern5065 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement5065(b, d, a, n, c, x, e):
        rubi.append(5065)
        return -Dist(b*c*n*sqrt(-c**S(2)*x**S(2) + S(1))/(d*sqrt(d + e*x**S(2))), Int(x*(a + b*asin(c*x))**(n + S(-1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*asin(c*x))**n/(d*sqrt(d + e*x**S(2))), x)
    rule5065 = ReplacementRule(pattern5065, replacement5065)
    pattern5066 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement5066(b, d, a, n, c, x, e):
        rubi.append(5066)
        return Dist(b*c*n*sqrt(-c**S(2)*x**S(2) + S(1))/(d*sqrt(d + e*x**S(2))), Int(x*(a + b*acos(c*x))**(n + S(-1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*acos(c*x))**n/(d*sqrt(d + e*x**S(2))), x)
    rule5066 = ReplacementRule(pattern5066, replacement5066)
    pattern5067 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons88, cons137, cons230)
    def replacement5067(p, b, d, a, n, c, x, e):
        rubi.append(5067)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) + Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*(p + S(1))), Int(x*(a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) - Simp(x*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x)
    rule5067 = ReplacementRule(pattern5067, replacement5067)
    pattern5068 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons88, cons137, cons230)
    def replacement5068(p, b, d, a, n, c, x, e):
        rubi.append(5068)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*(p + S(1))), Int(x*(a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) - Simp(x*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x)
    rule5068 = ReplacementRule(pattern5068, replacement5068)
    pattern5069 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement5069(b, d, a, n, c, x, e):
        rubi.append(5069)
        return Dist(S(1)/(c*d), Subst(Int((a + b*x)**n/cos(x), x), x, asin(c*x)), x)
    rule5069 = ReplacementRule(pattern5069, replacement5069)
    pattern5070 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement5070(b, d, a, n, c, x, e):
        rubi.append(5070)
        return -Dist(S(1)/(c*d), Subst(Int((a + b*x)**n/sin(x), x), x, acos(c*x)), x)
    rule5070 = ReplacementRule(pattern5070, replacement5070)
    pattern5071 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons89)
    def replacement5071(p, b, d, a, c, n, x, e):
        rubi.append(5071)
        return Dist(c*d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(S(2)*p + S(1))*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(b*(n + S(1))), Int(x*(a + b*asin(c*x))**(n + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((a + b*asin(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5071 = ReplacementRule(pattern5071, replacement5071)
    pattern5072 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons89)
    def replacement5072(p, b, d, a, c, n, x, e):
        rubi.append(5072)
        return -Dist(c*d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(S(2)*p + S(1))*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(b*(n + S(1))), Int(x*(a + b*acos(c*x))**(n + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) - Simp((a + b*acos(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5072 = ReplacementRule(pattern5072, replacement5072)
    pattern5073 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1739, cons1740)
    def replacement5073(p, b, d, a, n, c, x, e):
        rubi.append(5073)
        return Dist(d**p/c, Subst(Int((a + b*x)**n*cos(x)**(S(2)*p + S(1)), x), x, asin(c*x)), x)
    rule5073 = ReplacementRule(pattern5073, replacement5073)
    pattern5074 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1739, cons1740)
    def replacement5074(p, b, d, a, n, c, x, e):
        rubi.append(5074)
        return -Dist(d**p/c, Subst(Int((a + b*x)**n*sin(x)**(S(2)*p + S(1)), x), x, acos(c*x)), x)
    rule5074 = ReplacementRule(pattern5074, replacement5074)
    pattern5075 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1739, cons1741)
    def replacement5075(p, b, d, a, n, c, x, e):
        rubi.append(5075)
        return Dist(d**(p + S(-1)/2)*sqrt(d + e*x**S(2))/sqrt(-c**S(2)*x**S(2) + S(1)), Int((a + b*asin(c*x))**n*(-c**S(2)*x**S(2) + S(1))**p, x), x)
    rule5075 = ReplacementRule(pattern5075, replacement5075)
    pattern5076 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1739, cons1741)
    def replacement5076(p, b, d, a, n, c, x, e):
        rubi.append(5076)
        return Dist(d**(p + S(-1)/2)*sqrt(d + e*x**S(2))/sqrt(-c**S(2)*x**S(2) + S(1)), Int((a + b*acos(c*x))**n*(-c**S(2)*x**S(2) + S(1))**p, x), x)
    rule5076 = ReplacementRule(pattern5076, replacement5076)
    def With5077(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(5077)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asin(c*x), u, x)
    pattern5077 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1742, cons1743)
    rule5077 = ReplacementRule(pattern5077, With5077)
    def With5078(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(5078)
        return Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acos(c*x), u, x)
    pattern5078 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1742, cons1743)
    rule5078 = ReplacementRule(pattern5078, With5078)
    pattern5079 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1742, cons38, cons1744)
    def replacement5079(p, b, d, a, n, c, x, e):
        rubi.append(5079)
        return Int(ExpandIntegrand((a + b*asin(c*x))**n, (d + e*x**S(2))**p, x), x)
    rule5079 = ReplacementRule(pattern5079, replacement5079)
    pattern5080 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1742, cons38, cons1744)
    def replacement5080(p, b, d, a, n, c, x, e):
        rubi.append(5080)
        return Int(ExpandIntegrand((a + b*acos(c*x))**n, (d + e*x**S(2))**p, x), x)
    rule5080 = ReplacementRule(pattern5080, replacement5080)
    pattern5081 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement5081(p, b, d, a, n, c, x, e):
        rubi.append(5081)
        return Int((a + b*asin(c*x))**n*(d + e*x**S(2))**p, x)
    rule5081 = ReplacementRule(pattern5081, replacement5081)
    pattern5082 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement5082(p, b, d, a, n, c, x, e):
        rubi.append(5082)
        return Int((a + b*acos(c*x))**n*(d + e*x**S(2))**p, x)
    rule5082 = ReplacementRule(pattern5082, replacement5082)
    pattern5083 = Pattern(Integral((d_ + x_*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons336, cons1745, cons147)
    def replacement5083(p, g, b, f, d, a, n, c, x, e):
        rubi.append(5083)
        return Dist((d + e*x)**FracPart(p)*(f + g*x)**FracPart(p)*(d*f + e*g*x**S(2))**(-FracPart(p)), Int((a + b*asin(c*x))**n*(d*f + e*g*x**S(2))**p, x), x)
    rule5083 = ReplacementRule(pattern5083, replacement5083)
    pattern5084 = Pattern(Integral((d_ + x_*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons336, cons1745, cons147)
    def replacement5084(p, g, b, f, d, a, n, c, x, e):
        rubi.append(5084)
        return Dist((d + e*x)**FracPart(p)*(f + g*x)**FracPart(p)*(d*f + e*g*x**S(2))**(-FracPart(p)), Int((a + b*acos(c*x))**n*(d*f + e*g*x**S(2))**p, x), x)
    rule5084 = ReplacementRule(pattern5084, replacement5084)
    pattern5085 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement5085(b, d, a, n, c, x, e):
        rubi.append(5085)
        return -Dist(S(1)/e, Subst(Int((a + b*x)**n*tan(x), x), x, asin(c*x)), x)
    rule5085 = ReplacementRule(pattern5085, replacement5085)
    pattern5086 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement5086(b, d, a, n, c, x, e):
        rubi.append(5086)
        return Dist(S(1)/e, Subst(Int((a + b*x)**n/tan(x), x), x, acos(c*x)), x)
    rule5086 = ReplacementRule(pattern5086, replacement5086)
    pattern5087 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons88, cons54)
    def replacement5087(p, b, d, a, n, c, x, e):
        rubi.append(5087)
        return Dist(b*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp((a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5087 = ReplacementRule(pattern5087, replacement5087)
    pattern5088 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons88, cons54)
    def replacement5088(p, b, d, a, n, c, x, e):
        rubi.append(5088)
        return -Dist(b*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp((a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5088 = ReplacementRule(pattern5088, replacement5088)
    pattern5089 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement5089(b, d, a, n, c, x, e):
        rubi.append(5089)
        return Dist(S(1)/d, Subst(Int((a + b*x)**n/(sin(x)*cos(x)), x), x, asin(c*x)), x)
    rule5089 = ReplacementRule(pattern5089, replacement5089)
    pattern5090 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement5090(b, d, a, n, c, x, e):
        rubi.append(5090)
        return -Dist(S(1)/d, Subst(Int((a + b*x)**n/(sin(x)*cos(x)), x), x, acos(c*x)), x)
    rule5090 = ReplacementRule(pattern5090, replacement5090)
    pattern5091 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1737, cons87, cons88, cons242, cons66)
    def replacement5091(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5091)
        return -Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*f*(m + S(1))), x)
    rule5091 = ReplacementRule(pattern5091, replacement5091)
    pattern5092 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1737, cons87, cons88, cons242, cons66)
    def replacement5092(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5092)
        return Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*f*(m + S(1))), x)
    rule5092 = ReplacementRule(pattern5092, replacement5092)
    pattern5093 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))/x_, x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons128)
    def replacement5093(p, b, d, a, c, x, e):
        rubi.append(5093)
        return Dist(d, Int((a + b*asin(c*x))*(d + e*x**S(2))**(p + S(-1))/x, x), x) - Dist(b*c*d**p/(S(2)*p), Int((-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((a + b*asin(c*x))*(d + e*x**S(2))**p/(S(2)*p), x)
    rule5093 = ReplacementRule(pattern5093, replacement5093)
    pattern5094 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))/x_, x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons128)
    def replacement5094(p, b, d, a, c, x, e):
        rubi.append(5094)
        return Dist(d, Int((a + b*acos(c*x))*(d + e*x**S(2))**(p + S(-1))/x, x), x) + Dist(b*c*d**p/(S(2)*p), Int((-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((a + b*acos(c*x))*(d + e*x**S(2))**p/(S(2)*p), x)
    rule5094 = ReplacementRule(pattern5094, replacement5094)
    pattern5095 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons128, cons1746)
    def replacement5095(p, m, f, b, d, a, c, x, e):
        rubi.append(5095)
        return -Dist(S(2)*e*p/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*asin(c*x))*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*d**p/(f*(m + S(1))), Int((f*x)**(m + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asin(c*x))*(d + e*x**S(2))**p/(f*(m + S(1))), x)
    rule5095 = ReplacementRule(pattern5095, replacement5095)
    pattern5096 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons128, cons1746)
    def replacement5096(p, m, f, b, d, a, c, x, e):
        rubi.append(5096)
        return -Dist(S(2)*e*p/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*acos(c*x))*(d + e*x**S(2))**(p + S(-1)), x), x) + Dist(b*c*d**p/(f*(m + S(1))), Int((f*x)**(m + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acos(c*x))*(d + e*x**S(2))**p/(f*(m + S(1))), x)
    rule5096 = ReplacementRule(pattern5096, replacement5096)
    def With5097(p, m, f, b, d, a, c, x, e):
        u = IntHide((f*x)**m*(d + e*x**S(2))**p, x)
        rubi.append(5097)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asin(c*x), u, x)
    pattern5097 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons128)
    rule5097 = ReplacementRule(pattern5097, With5097)
    def With5098(p, m, f, b, d, a, c, x, e):
        u = IntHide((f*x)**m*(d + e*x**S(2))**p, x)
        rubi.append(5098)
        return Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acos(c*x), u, x)
    pattern5098 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons128)
    rule5098 = ReplacementRule(pattern5098, With5098)
    def With5099(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(-c**S(2)*x**S(2) + S(1))**p, x)
        rubi.append(5099)
        return Dist(d**p*(a + b*asin(c*x)), u, x) - Dist(b*c*d**p, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x)
    pattern5099 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons347, cons1747, cons486, cons268)
    rule5099 = ReplacementRule(pattern5099, With5099)
    def With5100(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(-c**S(2)*x**S(2) + S(1))**p, x)
        rubi.append(5100)
        return Dist(d**p*(a + b*acos(c*x)), u, x) + Dist(b*c*d**p, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x)
    pattern5100 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons347, cons1747, cons486, cons268)
    rule5100 = ReplacementRule(pattern5100, With5100)
    def With5101(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(-c**S(2)*x**S(2) + S(1))**p, x)
        rubi.append(5101)
        return -Dist(b*c*d**(p + S(-1)/2)*sqrt(d + e*x**S(2))/sqrt(-c**S(2)*x**S(2) + S(1)), Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asin(c*x), Int(x**m*(d + e*x**S(2))**p, x), x)
    pattern5101 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons961, cons1747)
    rule5101 = ReplacementRule(pattern5101, With5101)
    def With5102(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(-c**S(2)*x**S(2) + S(1))**p, x)
        rubi.append(5102)
        return Dist(b*c*d**(p + S(-1)/2)*sqrt(d + e*x**S(2))/sqrt(-c**S(2)*x**S(2) + S(1)), Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acos(c*x), Int(x**m*(d + e*x**S(2))**p, x), x)
    pattern5102 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons961, cons1747)
    rule5102 = ReplacementRule(pattern5102, With5102)
    pattern5103 = Pattern(Integral((x_*WC('f', S(1)))**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons93, cons88, cons94)
    def replacement5103(m, f, b, d, a, n, c, x, e):
        rubi.append(5103)
        return Dist(c**S(2)*sqrt(d + e*x**S(2))/(f**S(2)*(m + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))), Int((f*x)**(m + S(2))*(a + b*asin(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) - Dist(b*c*n*sqrt(d + e*x**S(2))/(f*(m + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))), Int((f*x)**(m + S(1))*(a + b*asin(c*x))**(n + S(-1)), x), x) + Simp((f*x)**(m + S(1))*(a + b*asin(c*x))**n*sqrt(d + e*x**S(2))/(f*(m + S(1))), x)
    rule5103 = ReplacementRule(pattern5103, replacement5103)
    pattern5104 = Pattern(Integral((x_*WC('f', S(1)))**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons93, cons88, cons94)
    def replacement5104(m, f, b, d, a, n, c, x, e):
        rubi.append(5104)
        return Dist(c**S(2)*sqrt(d + e*x**S(2))/(f**S(2)*(m + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))), Int((f*x)**(m + S(2))*(a + b*acos(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Dist(b*c*n*sqrt(d + e*x**S(2))/(f*(m + S(1))*sqrt(-c**S(2)*x**S(2) + S(1))), Int((f*x)**(m + S(1))*(a + b*acos(c*x))**(n + S(-1)), x), x) + Simp((f*x)**(m + S(1))*(a + b*acos(c*x))**n*sqrt(d + e*x**S(2))/(f*(m + S(1))), x)
    rule5104 = ReplacementRule(pattern5104, replacement5104)
    pattern5105 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons162, cons88, cons163, cons94)
    def replacement5105(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5105)
        return -Dist(S(2)*e*p/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asin(c*x))**n*(d + e*x**S(2))**p/(f*(m + S(1))), x)
    rule5105 = ReplacementRule(pattern5105, replacement5105)
    pattern5106 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons162, cons88, cons163, cons94)
    def replacement5106(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5106)
        return -Dist(S(2)*e*p/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) + Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acos(c*x))**n*(d + e*x**S(2))**p/(f*(m + S(1))), x)
    rule5106 = ReplacementRule(pattern5106, replacement5106)
    pattern5107 = Pattern(Integral((x_*WC('f', S(1)))**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons87, cons88, cons272, cons1748)
    def replacement5107(m, f, b, d, a, n, c, x, e):
        rubi.append(5107)
        return Dist(sqrt(d + e*x**S(2))/((m + S(2))*sqrt(-c**S(2)*x**S(2) + S(1))), Int((f*x)**m*(a + b*asin(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) - Dist(b*c*n*sqrt(d + e*x**S(2))/(f*(m + S(2))*sqrt(-c**S(2)*x**S(2) + S(1))), Int((f*x)**(m + S(1))*(a + b*asin(c*x))**(n + S(-1)), x), x) + Simp((f*x)**(m + S(1))*(a + b*asin(c*x))**n*sqrt(d + e*x**S(2))/(f*(m + S(2))), x)
    rule5107 = ReplacementRule(pattern5107, replacement5107)
    pattern5108 = Pattern(Integral((x_*WC('f', S(1)))**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons87, cons88, cons272, cons1748)
    def replacement5108(m, f, b, d, a, n, c, x, e):
        rubi.append(5108)
        return Dist(sqrt(d + e*x**S(2))/((m + S(2))*sqrt(-c**S(2)*x**S(2) + S(1))), Int((f*x)**m*(a + b*acos(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Dist(b*c*n*sqrt(d + e*x**S(2))/(f*(m + S(2))*sqrt(-c**S(2)*x**S(2) + S(1))), Int((f*x)**(m + S(1))*(a + b*acos(c*x))**(n + S(-1)), x), x) + Simp((f*x)**(m + S(1))*(a + b*acos(c*x))**n*sqrt(d + e*x**S(2))/(f*(m + S(2))), x)
    rule5108 = ReplacementRule(pattern5108, replacement5108)
    pattern5109 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons338, cons88, cons163, cons272, cons1748)
    def replacement5109(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5109)
        return Dist(S(2)*d*p/(m + S(2)*p + S(1)), Int((f*x)**m*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(2)*p + S(1))), Int((f*x)**(m + S(1))*(a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asin(c*x))**n*(d + e*x**S(2))**p/(f*(m + S(2)*p + S(1))), x)
    rule5109 = ReplacementRule(pattern5109, replacement5109)
    pattern5110 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons338, cons88, cons163, cons272, cons1748)
    def replacement5110(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5110)
        return Dist(S(2)*d*p/(m + S(2)*p + S(1)), Int((f*x)**m*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) + Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(2)*p + S(1))), Int((f*x)**(m + S(1))*(a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acos(c*x))**n*(d + e*x**S(2))**p/(f*(m + S(2)*p + S(1))), x)
    rule5110 = ReplacementRule(pattern5110, replacement5110)
    pattern5111 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons1737, cons93, cons88, cons94, cons17)
    def replacement5111(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5111)
        return Dist(c**S(2)*(m + S(2)*p + S(3))/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*asin(c*x))**n*(d + e*x**S(2))**p, x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*f*(m + S(1))), x)
    rule5111 = ReplacementRule(pattern5111, replacement5111)
    pattern5112 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons1737, cons93, cons88, cons94, cons17)
    def replacement5112(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5112)
        return Dist(c**S(2)*(m + S(2)*p + S(3))/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*acos(c*x))**n*(d + e*x**S(2))**p, x), x) + Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*f*(m + S(1))), x)
    rule5112 = ReplacementRule(pattern5112, replacement5112)
    pattern5113 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons162, cons88, cons137, cons166)
    def replacement5113(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5113)
        return -Dist(f**S(2)*(m + S(-1))/(S(2)*e*(p + S(1))), Int((f*x)**(m + S(-2))*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) + Dist(b*d**IntPart(p)*f*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((f*x)**(m + S(-1))*(a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5113 = ReplacementRule(pattern5113, replacement5113)
    pattern5114 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons162, cons88, cons137, cons166)
    def replacement5114(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5114)
        return -Dist(f**S(2)*(m + S(-1))/(S(2)*e*(p + S(1))), Int((f*x)**(m + S(-2))*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(b*d**IntPart(p)*f*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((f*x)**(m + S(-1))*(a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5114 = ReplacementRule(pattern5114, replacement5114)
    pattern5115 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons338, cons88, cons137, cons274, cons1749)
    def replacement5115(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5115)
        return Dist((m + S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((f*x)**m*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) + Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*f*(p + S(1))), Int((f*x)**(m + S(1))*(a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) - Simp((f*x)**(m + S(1))*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*f*(p + S(1))), x)
    rule5115 = ReplacementRule(pattern5115, replacement5115)
    pattern5116 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons338, cons88, cons137, cons274, cons1749)
    def replacement5116(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5116)
        return Dist((m + S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((f*x)**m*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*f*(p + S(1))), Int((f*x)**(m + S(1))*(a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) - Simp((f*x)**(m + S(1))*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*f*(p + S(1))), x)
    rule5116 = ReplacementRule(pattern5116, replacement5116)
    pattern5117 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons93, cons88, cons166, cons17)
    def replacement5117(m, f, b, d, a, n, c, x, e):
        rubi.append(5117)
        return Dist(f**S(2)*(m + S(-1))/(c**S(2)*m), Int((f*x)**(m + S(-2))*(a + b*asin(c*x))**n/sqrt(d + e*x**S(2)), x), x) + Dist(b*f*n*sqrt(-c**S(2)*x**S(2) + S(1))/(c*m*sqrt(d + e*x**S(2))), Int((f*x)**(m + S(-1))*(a + b*asin(c*x))**(n + S(-1)), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*asin(c*x))**n*sqrt(d + e*x**S(2))/(e*m), x)
    rule5117 = ReplacementRule(pattern5117, replacement5117)
    pattern5118 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons93, cons88, cons166, cons17)
    def replacement5118(m, f, b, d, a, n, c, x, e):
        rubi.append(5118)
        return Dist(f**S(2)*(m + S(-1))/(c**S(2)*m), Int((f*x)**(m + S(-2))*(a + b*acos(c*x))**n/sqrt(d + e*x**S(2)), x), x) - Dist(b*f*n*sqrt(-c**S(2)*x**S(2) + S(1))/(c*m*sqrt(d + e*x**S(2))), Int((f*x)**(m + S(-1))*(a + b*acos(c*x))**(n + S(-1)), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acos(c*x))**n*sqrt(d + e*x**S(2))/(e*m), x)
    rule5118 = ReplacementRule(pattern5118, replacement5118)
    pattern5119 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons268, cons148, cons17)
    def replacement5119(m, b, d, a, n, c, x, e):
        rubi.append(5119)
        return Dist(c**(-m + S(-1))/sqrt(d), Subst(Int((a + b*x)**n*sin(x)**m, x), x, asin(c*x)), x)
    rule5119 = ReplacementRule(pattern5119, replacement5119)
    pattern5120 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons268, cons148, cons17)
    def replacement5120(m, b, d, a, n, c, x, e):
        rubi.append(5120)
        return -Dist(c**(-m + S(-1))/sqrt(d), Subst(Int((a + b*x)**n*cos(x)**m, x), x, acos(c*x)), x)
    rule5120 = ReplacementRule(pattern5120, replacement5120)
    pattern5121 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons268, cons18)
    def replacement5121(m, f, b, d, a, c, x, e):
        rubi.append(5121)
        return Simp((f*x)**(m + S(1))*(a + b*asin(c*x))*Hypergeometric2F1(S(1)/2, m/S(2) + S(1)/2, m/S(2) + S(3)/2, c**S(2)*x**S(2))/(sqrt(d)*f*(m + S(1))), x) - Simp(b*c*(f*x)**(m + S(2))*HypergeometricPFQ(List(S(1), m/S(2) + S(1), m/S(2) + S(1)), List(m/S(2) + S(3)/2, m/S(2) + S(2)), c**S(2)*x**S(2))/(sqrt(d)*f**S(2)*(m + S(1))*(m + S(2))), x)
    rule5121 = ReplacementRule(pattern5121, replacement5121)
    pattern5122 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons268, cons18)
    def replacement5122(m, f, b, d, a, c, x, e):
        rubi.append(5122)
        return Simp((f*x)**(m + S(1))*(a + b*acos(c*x))*Hypergeometric2F1(S(1)/2, m/S(2) + S(1)/2, m/S(2) + S(3)/2, c**S(2)*x**S(2))/(sqrt(d)*f*(m + S(1))), x) + Simp(b*c*(f*x)**(m + S(2))*HypergeometricPFQ(List(S(1), m/S(2) + S(1), m/S(2) + S(1)), List(m/S(2) + S(3)/2, m/S(2) + S(2)), c**S(2)*x**S(2))/(sqrt(d)*f**S(2)*(m + S(1))*(m + S(2))), x)
    rule5122 = ReplacementRule(pattern5122, replacement5122)
    pattern5123 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons87, cons88, cons1738, cons1750)
    def replacement5123(m, f, b, d, a, n, c, x, e):
        rubi.append(5123)
        return Dist(sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((f*x)**m*(a + b*asin(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x)
    rule5123 = ReplacementRule(pattern5123, replacement5123)
    pattern5124 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons87, cons88, cons1738, cons1750)
    def replacement5124(m, f, b, d, a, n, c, x, e):
        rubi.append(5124)
        return Dist(sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((f*x)**m*(a + b*acos(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x)
    rule5124 = ReplacementRule(pattern5124, replacement5124)
    pattern5125 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons1737, cons93, cons88, cons166, cons238, cons17)
    def replacement5125(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5125)
        return Dist(f**S(2)*(m + S(-1))/(c**S(2)*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-2))*(a + b*asin(c*x))**n*(d + e*x**S(2))**p, x), x) + Dist(b*d**IntPart(p)*f*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(c*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-1))*(a + b*asin(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*asin(c*x))**n*(d + e*x**S(2))**(p + S(1))/(e*(m + S(2)*p + S(1))), x)
    rule5125 = ReplacementRule(pattern5125, replacement5125)
    pattern5126 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons1737, cons93, cons88, cons166, cons238, cons17)
    def replacement5126(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5126)
        return Dist(f**S(2)*(m + S(-1))/(c**S(2)*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-2))*(a + b*acos(c*x))**n*(d + e*x**S(2))**p, x), x) - Dist(b*d**IntPart(p)*f*n*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(c*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-1))*(a + b*acos(c*x))**(n + S(-1))*(-c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acos(c*x))**n*(d + e*x**S(2))**(p + S(1))/(e*(m + S(2)*p + S(1))), x)
    rule5126 = ReplacementRule(pattern5126, replacement5126)
    pattern5127 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1737, cons87, cons89, cons237)
    def replacement5127(p, m, f, b, d, a, c, n, x, e):
        rubi.append(5127)
        return -Dist(d**IntPart(p)*f*m*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*asin(c*x))**(n + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**m*(a + b*asin(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5127 = ReplacementRule(pattern5127, replacement5127)
    pattern5128 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1737, cons87, cons89, cons237)
    def replacement5128(p, m, f, b, d, a, c, n, x, e):
        rubi.append(5128)
        return Dist(d**IntPart(p)*f*m*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*acos(c*x))**(n + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) - Simp((f*x)**m*(a + b*acos(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5128 = ReplacementRule(pattern5128, replacement5128)
    pattern5129 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons87, cons89, cons268)
    def replacement5129(m, f, b, d, a, c, n, x, e):
        rubi.append(5129)
        return -Dist(f*m/(b*c*sqrt(d)*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*asin(c*x))**(n + S(1)), x), x) + Simp((f*x)**m*(a + b*asin(c*x))**(n + S(1))/(b*c*sqrt(d)*(n + S(1))), x)
    rule5129 = ReplacementRule(pattern5129, replacement5129)
    pattern5130 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons87, cons89, cons268)
    def replacement5130(m, f, b, d, a, c, n, x, e):
        rubi.append(5130)
        return Dist(f*m/(b*c*sqrt(d)*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*acos(c*x))**(n + S(1)), x), x) - Simp((f*x)**m*(a + b*acos(c*x))**(n + S(1))/(b*c*sqrt(d)*(n + S(1))), x)
    rule5130 = ReplacementRule(pattern5130, replacement5130)
    pattern5131 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons87, cons89, cons17, cons1751, cons1739)
    def replacement5131(p, m, f, b, d, a, c, n, x, e):
        rubi.append(5131)
        return -Dist(d**IntPart(p)*f*m*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*asin(c*x))**(n + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Dist(c*d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))*(m + S(2)*p + S(1))/(b*f*(n + S(1))), Int((f*x)**(m + S(1))*(a + b*asin(c*x))**(n + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**m*(a + b*asin(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5131 = ReplacementRule(pattern5131, replacement5131)
    pattern5132 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons87, cons89, cons17, cons1751, cons1739)
    def replacement5132(p, m, f, b, d, a, c, n, x, e):
        rubi.append(5132)
        return Dist(d**IntPart(p)*f*m*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*acos(c*x))**(n + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) - Dist(c*d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p))*(m + S(2)*p + S(1))/(b*f*(n + S(1))), Int((f*x)**(m + S(1))*(a + b*acos(c*x))**(n + S(1))*(-c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) - Simp((f*x)**m*(a + b*acos(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(-c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule5132 = ReplacementRule(pattern5132, replacement5132)
    pattern5133 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons246, cons1752, cons62, cons1740)
    def replacement5133(p, m, b, d, a, n, c, x, e):
        rubi.append(5133)
        return Dist(c**(-m + S(-1))*d**p, Subst(Int((a + b*x)**n*sin(x)**m*cos(x)**(S(2)*p + S(1)), x), x, asin(c*x)), x)
    rule5133 = ReplacementRule(pattern5133, replacement5133)
    pattern5134 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons246, cons1752, cons62, cons1740)
    def replacement5134(p, m, b, d, a, n, c, x, e):
        rubi.append(5134)
        return -Dist(c**(-m + S(-1))*d**p, Subst(Int((a + b*x)**n*sin(x)**(S(2)*p + S(1))*cos(x)**m, x), x, acos(c*x)), x)
    rule5134 = ReplacementRule(pattern5134, replacement5134)
    pattern5135 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons246, cons1752, cons62, cons1741)
    def replacement5135(p, m, b, d, a, c, n, x, e):
        rubi.append(5135)
        return Dist(d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int(x**m*(a + b*asin(c*x))**n*(-c**S(2)*x**S(2) + S(1))**p, x), x)
    rule5135 = ReplacementRule(pattern5135, replacement5135)
    pattern5136 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons246, cons1752, cons62, cons1741)
    def replacement5136(p, m, b, d, a, c, n, x, e):
        rubi.append(5136)
        return Dist(d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int(x**m*(a + b*acos(c*x))**n*(-c**S(2)*x**S(2) + S(1))**p, x), x)
    rule5136 = ReplacementRule(pattern5136, replacement5136)
    pattern5137 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1737, cons268, cons961, cons1753, cons17, cons1754)
    def replacement5137(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5137)
        return Int(ExpandIntegrand((a + b*asin(c*x))**n/sqrt(d + e*x**S(2)), (f*x)**m*(d + e*x**S(2))**(p + S(1)/2), x), x)
    rule5137 = ReplacementRule(pattern5137, replacement5137)
    pattern5138 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1737, cons268, cons961, cons1753, cons17, cons1754)
    def replacement5138(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5138)
        return Int(ExpandIntegrand((a + b*acos(c*x))**n/sqrt(d + e*x**S(2)), (f*x)**m*(d + e*x**S(2))**(p + S(1)/2), x), x)
    rule5138 = ReplacementRule(pattern5138, replacement5138)
    pattern5139 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1742, cons54)
    def replacement5139(p, b, d, a, c, x, e):
        rubi.append(5139)
        return -Dist(b*c/(S(2)*e*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*asin(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5139 = ReplacementRule(pattern5139, replacement5139)
    pattern5140 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1742, cons54)
    def replacement5140(p, b, d, a, c, x, e):
        rubi.append(5140)
        return Dist(b*c/(S(2)*e*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*acos(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5140 = ReplacementRule(pattern5140, replacement5140)
    def With5141(p, m, f, b, d, a, c, x, e):
        u = IntHide((f*x)**m*(d + e*x**S(2))**p, x)
        rubi.append(5141)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asin(c*x), u, x)
    pattern5141 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1742, cons38, cons1755)
    rule5141 = ReplacementRule(pattern5141, With5141)
    def With5142(p, m, f, b, d, a, c, x, e):
        u = IntHide((f*x)**m*(d + e*x**S(2))**p, x)
        rubi.append(5142)
        return Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acos(c*x), u, x)
    pattern5142 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1742, cons38, cons1755)
    rule5142 = ReplacementRule(pattern5142, With5142)
    pattern5143 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1742, cons148, cons38, cons17)
    def replacement5143(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5143)
        return Int(ExpandIntegrand((a + b*asin(c*x))**n, (f*x)**m*(d + e*x**S(2))**p, x), x)
    rule5143 = ReplacementRule(pattern5143, replacement5143)
    pattern5144 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1742, cons148, cons38, cons17)
    def replacement5144(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5144)
        return Int(ExpandIntegrand((a + b*acos(c*x))**n, (f*x)**m*(d + e*x**S(2))**p, x), x)
    rule5144 = ReplacementRule(pattern5144, replacement5144)
    pattern5145 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons1756)
    def replacement5145(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5145)
        return Int((f*x)**m*(a + b*asin(c*x))**n*(d + e*x**S(2))**p, x)
    rule5145 = ReplacementRule(pattern5145, replacement5145)
    pattern5146 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons1756)
    def replacement5146(p, m, f, b, d, a, n, c, x, e):
        rubi.append(5146)
        return Int((f*x)**m*(a + b*acos(c*x))**n*(d + e*x**S(2))**p, x)
    rule5146 = ReplacementRule(pattern5146, replacement5146)
    pattern5147 = Pattern(Integral((x_*WC('h', S(1)))**WC('m', S(1))*(d_ + x_*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons5, cons336, cons1745, cons147)
    def replacement5147(p, m, g, b, f, d, a, n, c, x, h, e):
        rubi.append(5147)
        return Dist((d + e*x)**FracPart(p)*(f + g*x)**FracPart(p)*(d*f + e*g*x**S(2))**(-FracPart(p)), Int((h*x)**m*(a + b*asin(c*x))**n*(d*f + e*g*x**S(2))**p, x), x)
    rule5147 = ReplacementRule(pattern5147, replacement5147)
    pattern5148 = Pattern(Integral((x_*WC('h', S(1)))**WC('m', S(1))*(d_ + x_*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons5, cons336, cons1745, cons147)
    def replacement5148(p, m, g, b, f, d, a, n, c, x, h, e):
        rubi.append(5148)
        return Dist((d + e*x)**FracPart(p)*(f + g*x)**FracPart(p)*(d*f + e*g*x**S(2))**(-FracPart(p)), Int((h*x)**m*(a + b*acos(c*x))**n*(d*f + e*g*x**S(2))**p, x), x)
    rule5148 = ReplacementRule(pattern5148, replacement5148)
    pattern5149 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons148)
    def replacement5149(b, d, a, n, c, x, e):
        rubi.append(5149)
        return Subst(Int((a + b*x)**n*cos(x)/(c*d + e*sin(x)), x), x, asin(c*x))
    rule5149 = ReplacementRule(pattern5149, replacement5149)
    pattern5150 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons148)
    def replacement5150(b, d, a, n, c, x, e):
        rubi.append(5150)
        return -Subst(Int((a + b*x)**n*sin(x)/(c*d + e*cos(x)), x), x, acos(c*x))
    rule5150 = ReplacementRule(pattern5150, replacement5150)
    pattern5151 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons148, cons66)
    def replacement5151(m, b, d, a, n, c, x, e):
        rubi.append(5151)
        return -Dist(b*c*n/(e*(m + S(1))), Int((a + b*asin(c*x))**(n + S(-1))*(d + e*x)**(m + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*asin(c*x))**n*(d + e*x)**(m + S(1))/(e*(m + S(1))), x)
    rule5151 = ReplacementRule(pattern5151, replacement5151)
    pattern5152 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons148, cons66)
    def replacement5152(m, b, d, a, n, c, x, e):
        rubi.append(5152)
        return Dist(b*c*n/(e*(m + S(1))), Int((a + b*acos(c*x))**(n + S(-1))*(d + e*x)**(m + S(1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*acos(c*x))**n*(d + e*x)**(m + S(1))/(e*(m + S(1))), x)
    rule5152 = ReplacementRule(pattern5152, replacement5152)
    pattern5153 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons62, cons87, cons89)
    def replacement5153(m, b, d, a, c, n, x, e):
        rubi.append(5153)
        return Int(ExpandIntegrand((a + b*asin(c*x))**n*(d + e*x)**m, x), x)
    rule5153 = ReplacementRule(pattern5153, replacement5153)
    pattern5154 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons62, cons87, cons89)
    def replacement5154(m, b, d, a, c, n, x, e):
        rubi.append(5154)
        return Int(ExpandIntegrand((a + b*acos(c*x))**n*(d + e*x)**m, x), x)
    rule5154 = ReplacementRule(pattern5154, replacement5154)
    pattern5155 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons62)
    def replacement5155(m, b, d, a, c, n, x, e):
        rubi.append(5155)
        return Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*(c*d + e*sin(x))**m*cos(x), x), x, asin(c*x)), x)
    rule5155 = ReplacementRule(pattern5155, replacement5155)
    pattern5156 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons62)
    def replacement5156(m, b, d, a, c, n, x, e):
        rubi.append(5156)
        return -Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*(c*d + e*cos(x))**m*sin(x), x), x, acos(c*x)), x)
    rule5156 = ReplacementRule(pattern5156, replacement5156)
    def With5157(b, Px, a, c, x):
        u = IntHide(Px, x)
        rubi.append(5157)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asin(c*x), u, x)
    pattern5157 = Pattern(Integral(Px_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons925)
    rule5157 = ReplacementRule(pattern5157, With5157)
    def With5158(b, Px, a, c, x):
        u = IntHide(Px, x)
        rubi.append(5158)
        return Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acos(c*x), u, x)
    pattern5158 = Pattern(Integral(Px_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons925)
    rule5158 = ReplacementRule(pattern5158, With5158)
    pattern5159 = Pattern(Integral(Px_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons925)
    def replacement5159(b, Px, a, n, c, x):
        rubi.append(5159)
        return Int(ExpandIntegrand(Px*(a + b*asin(c*x))**n, x), x)
    rule5159 = ReplacementRule(pattern5159, replacement5159)
    pattern5160 = Pattern(Integral(Px_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons925)
    def replacement5160(b, Px, a, n, c, x):
        rubi.append(5160)
        return Int(ExpandIntegrand(Px*(a + b*acos(c*x))**n, x), x)
    rule5160 = ReplacementRule(pattern5160, replacement5160)
    def With5161(m, b, Px, d, a, c, x, e):
        u = IntHide(Px*(d + e*x)**m, x)
        rubi.append(5161)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asin(c*x), u, x)
    pattern5161 = Pattern(Integral(Px_*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons925)
    rule5161 = ReplacementRule(pattern5161, With5161)
    def With5162(m, b, Px, d, a, c, x, e):
        u = IntHide(Px*(d + e*x)**m, x)
        rubi.append(5162)
        return Dist(b*c, Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acos(c*x), u, x)
    pattern5162 = Pattern(Integral(Px_*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons925)
    rule5162 = ReplacementRule(pattern5162, With5162)
    def With5163(p, m, f, b, g, d, a, c, n, x, e):
        u = IntHide((d + e*x)**m*(f + g*x)**p, x)
        rubi.append(5163)
        return -Dist(b*c*n, Int(SimplifyIntegrand(u*(a + b*asin(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist((a + b*asin(c*x))**n, u, x)
    pattern5163 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons464, cons84, cons1757)
    rule5163 = ReplacementRule(pattern5163, With5163)
    def With5164(p, m, f, b, g, d, a, c, n, x, e):
        u = IntHide((d + e*x)**m*(f + g*x)**p, x)
        rubi.append(5164)
        return Dist(b*c*n, Int(SimplifyIntegrand(u*(a + b*acos(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist((a + b*acos(c*x))**n, u, x)
    pattern5164 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons464, cons84, cons1757)
    rule5164 = ReplacementRule(pattern5164, With5164)
    def With5165(p, f, b, g, d, a, c, n, x, h, e):
        u = IntHide((f + g*x + h*x**S(2))**p/(d + e*x)**S(2), x)
        rubi.append(5165)
        return -Dist(b*c*n, Int(SimplifyIntegrand(u*(a + b*asin(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist((a + b*asin(c*x))**n, u, x)
    pattern5165 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_*(x_**S(2)*WC('h', S(1)) + x_*WC('g', S(1)) + WC('f', S(0)))**WC('p', S(1))/(d_ + x_*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons464, cons1758)
    rule5165 = ReplacementRule(pattern5165, With5165)
    def With5166(p, f, b, g, d, a, c, n, x, h, e):
        u = IntHide((f + g*x + h*x**S(2))**p/(d + e*x)**S(2), x)
        rubi.append(5166)
        return Dist(b*c*n, Int(SimplifyIntegrand(u*(a + b*acos(c*x))**(n + S(-1))/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist((a + b*acos(c*x))**n, u, x)
    pattern5166 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_*(x_**S(2)*WC('h', S(1)) + x_*WC('g', S(1)) + WC('f', S(0)))**WC('p', S(1))/(d_ + x_*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons464, cons1758)
    rule5166 = ReplacementRule(pattern5166, With5166)
    pattern5167 = Pattern(Integral(Px_*(d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons925, cons148, cons17)
    def replacement5167(m, b, Px, d, a, c, n, x, e):
        rubi.append(5167)
        return Int(ExpandIntegrand(Px*(a + b*asin(c*x))**n*(d + e*x)**m, x), x)
    rule5167 = ReplacementRule(pattern5167, replacement5167)
    pattern5168 = Pattern(Integral(Px_*(d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons925, cons148, cons17)
    def replacement5168(m, b, Px, d, a, c, n, x, e):
        rubi.append(5168)
        return Int(ExpandIntegrand(Px*(a + b*acos(c*x))**n*(d + e*x)**m, x), x)
    rule5168 = ReplacementRule(pattern5168, replacement5168)
    def With5169(p, m, g, b, f, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p*(f + g*x)**m, x)
        rubi.append(5169)
        return -Dist(b*c, Int(Dist(S(1)/sqrt(-c**S(2)*x**S(2) + S(1)), u, x), x), x) + Dist(a + b*asin(c*x), u, x)
    pattern5169 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons719, cons268, cons168, cons1759)
    rule5169 = ReplacementRule(pattern5169, With5169)
    def With5170(p, m, g, b, f, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p*(f + g*x)**m, x)
        rubi.append(5170)
        return Dist(b*c, Int(Dist(S(1)/sqrt(-c**S(2)*x**S(2) + S(1)), u, x), x), x) + Dist(a + b*acos(c*x), u, x)
    pattern5170 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons719, cons268, cons168, cons1759)
    rule5170 = ReplacementRule(pattern5170, With5170)
    pattern5171 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons667, cons268, cons148, cons168, cons1760)
    def replacement5171(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5171)
        return Int(ExpandIntegrand((a + b*asin(c*x))**n*(d + e*x**S(2))**p, (f + g*x)**m, x), x)
    rule5171 = ReplacementRule(pattern5171, replacement5171)
    pattern5172 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons667, cons268, cons148, cons168, cons1760)
    def replacement5172(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5172)
        return Int(ExpandIntegrand((a + b*acos(c*x))**n*(d + e*x**S(2))**p, (f + g*x)**m, x), x)
    rule5172 = ReplacementRule(pattern5172, replacement5172)
    pattern5173 = Pattern(Integral(sqrt(d_ + x_**S(2)*WC('e', S(1)))*(f_ + x_*WC('g', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons268, cons148, cons267)
    def replacement5173(m, g, b, f, d, a, n, c, x, e):
        rubi.append(5173)
        return -Dist(S(1)/(b*c*sqrt(d)*(n + S(1))), Int((a + b*asin(c*x))**(n + S(1))*(f + g*x)**(m + S(-1))*(d*g*m + S(2)*e*f*x + e*g*x**S(2)*(m + S(2))), x), x) + Simp((a + b*asin(c*x))**(n + S(1))*(d + e*x**S(2))*(f + g*x)**m/(b*c*sqrt(d)*(n + S(1))), x)
    rule5173 = ReplacementRule(pattern5173, replacement5173)
    pattern5174 = Pattern(Integral(sqrt(d_ + x_**S(2)*WC('e', S(1)))*(f_ + x_*WC('g', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons268, cons148, cons267)
    def replacement5174(m, g, b, f, d, a, n, c, x, e):
        rubi.append(5174)
        return Dist(S(1)/(b*c*sqrt(d)*(n + S(1))), Int((a + b*acos(c*x))**(n + S(1))*(f + g*x)**(m + S(-1))*(d*g*m + S(2)*e*f*x + e*g*x**S(2)*(m + S(2))), x), x) - Simp((a + b*acos(c*x))**(n + S(1))*(d + e*x**S(2))*(f + g*x)**m/(b*c*sqrt(d)*(n + S(1))), x)
    rule5174 = ReplacementRule(pattern5174, replacement5174)
    pattern5175 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons961, cons268, cons148)
    def replacement5175(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5175)
        return Int(ExpandIntegrand((a + b*asin(c*x))**n*sqrt(d + e*x**S(2)), (d + e*x**S(2))**(p + S(-1)/2)*(f + g*x)**m, x), x)
    rule5175 = ReplacementRule(pattern5175, replacement5175)
    pattern5176 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons961, cons268, cons148)
    def replacement5176(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5176)
        return Int(ExpandIntegrand((a + b*acos(c*x))**n*sqrt(d + e*x**S(2)), (d + e*x**S(2))**(p + S(-1)/2)*(f + g*x)**m, x), x)
    rule5176 = ReplacementRule(pattern5176, replacement5176)
    pattern5177 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons717, cons268, cons148, cons267)
    def replacement5177(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5177)
        return -Dist(S(1)/(b*c*sqrt(d)*(n + S(1))), Int(ExpandIntegrand((a + b*asin(c*x))**(n + S(1))*(f + g*x)**(m + S(-1)), (d + e*x**S(2))**(p + S(-1)/2)*(d*g*m + e*f*x*(S(2)*p + S(1)) + e*g*x**S(2)*(m + S(2)*p + S(1))), x), x), x) + Simp((a + b*asin(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1)/2)*(f + g*x)**m/(b*c*sqrt(d)*(n + S(1))), x)
    rule5177 = ReplacementRule(pattern5177, replacement5177)
    pattern5178 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons717, cons268, cons148, cons267)
    def replacement5178(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5178)
        return Dist(S(1)/(b*c*sqrt(d)*(n + S(1))), Int(ExpandIntegrand((a + b*acos(c*x))**(n + S(1))*(f + g*x)**(m + S(-1)), (d + e*x**S(2))**(p + S(-1)/2)*(d*g*m + e*f*x*(S(2)*p + S(1)) + e*g*x**S(2)*(m + S(2)*p + S(1))), x), x), x) - Simp((a + b*acos(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1)/2)*(f + g*x)**m/(b*c*sqrt(d)*(n + S(1))), x)
    rule5178 = ReplacementRule(pattern5178, replacement5178)
    pattern5179 = Pattern(Integral((f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**n_/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons268, cons168, cons87, cons89)
    def replacement5179(m, g, b, f, d, a, c, n, x, e):
        rubi.append(5179)
        return -Dist(g*m/(b*c*sqrt(d)*(n + S(1))), Int((a + b*asin(c*x))**(n + S(1))*(f + g*x)**(m + S(-1)), x), x) + Simp((a + b*asin(c*x))**(n + S(1))*(f + g*x)**m/(b*c*sqrt(d)*(n + S(1))), x)
    rule5179 = ReplacementRule(pattern5179, replacement5179)
    pattern5180 = Pattern(Integral((f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**n_/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons268, cons168, cons87, cons89)
    def replacement5180(m, g, b, f, d, a, c, n, x, e):
        rubi.append(5180)
        return Dist(g*m/(b*c*sqrt(d)*(n + S(1))), Int((a + b*acos(c*x))**(n + S(1))*(f + g*x)**(m + S(-1)), x), x) - Simp((a + b*acos(c*x))**(n + S(1))*(f + g*x)**m/(b*c*sqrt(d)*(n + S(1))), x)
    rule5180 = ReplacementRule(pattern5180, replacement5180)
    pattern5181 = Pattern(Integral((f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons1737, cons17, cons268, cons1761)
    def replacement5181(m, g, b, f, d, a, n, c, x, e):
        rubi.append(5181)
        return Dist(c**(-m + S(-1))/sqrt(d), Subst(Int((a + b*x)**n*(c*f + g*sin(x))**m, x), x, asin(c*x)), x)
    rule5181 = ReplacementRule(pattern5181, replacement5181)
    pattern5182 = Pattern(Integral((f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons1737, cons17, cons268, cons1761)
    def replacement5182(m, g, b, f, d, a, n, c, x, e):
        rubi.append(5182)
        return -Dist(c**(-m + S(-1))/sqrt(d), Subst(Int((a + b*x)**n*(c*f + g*cos(x))**m, x), x, acos(c*x)), x)
    rule5182 = ReplacementRule(pattern5182, replacement5182)
    pattern5183 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons719, cons268, cons148)
    def replacement5183(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5183)
        return Int(ExpandIntegrand((a + b*asin(c*x))**n/sqrt(d + e*x**S(2)), (d + e*x**S(2))**(p + S(1)/2)*(f + g*x)**m, x), x)
    rule5183 = ReplacementRule(pattern5183, replacement5183)
    pattern5184 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1737, cons17, cons719, cons268, cons148)
    def replacement5184(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5184)
        return Int(ExpandIntegrand((a + b*acos(c*x))**n/sqrt(d + e*x**S(2)), (d + e*x**S(2))**(p + S(1)/2)*(f + g*x)**m, x), x)
    rule5184 = ReplacementRule(pattern5184, replacement5184)
    pattern5185 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons1737, cons17, cons347, cons1738)
    def replacement5185(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5185)
        return Dist(d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int((a + b*asin(c*x))**n*(f + g*x)**m*(-c**S(2)*x**S(2) + S(1))**p, x), x)
    rule5185 = ReplacementRule(pattern5185, replacement5185)
    pattern5186 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons1737, cons17, cons347, cons1738)
    def replacement5186(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(5186)
        return Dist(d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int((a + b*acos(c*x))**n*(f + g*x)**m*(-c**S(2)*x**S(2) + S(1))**p, x), x)
    rule5186 = ReplacementRule(pattern5186, replacement5186)
    pattern5187 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*WC('h', S(1)))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons1737, cons268, cons148)
    def replacement5187(m, f, g, b, d, a, c, n, x, h, e):
        rubi.append(5187)
        return -Dist(g*m/(b*c*sqrt(d)*(n + S(1))), Int((a + b*asin(c*x))**(n + S(1))/(f + g*x), x), x) + Simp((a + b*asin(c*x))**(n + S(1))*log(h*(f + g*x)**m)/(b*c*sqrt(d)*(n + S(1))), x)
    rule5187 = ReplacementRule(pattern5187, replacement5187)
    pattern5188 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*WC('h', S(1)))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons1737, cons268, cons148)
    def replacement5188(m, f, g, b, d, a, c, n, x, h, e):
        rubi.append(5188)
        return Dist(g*m/(b*c*sqrt(d)*(n + S(1))), Int((a + b*acos(c*x))**(n + S(1))/(f + g*x), x), x) - Simp((a + b*acos(c*x))**(n + S(1))*log(h*(f + g*x)**m)/(b*c*sqrt(d)*(n + S(1))), x)
    rule5188 = ReplacementRule(pattern5188, replacement5188)
    pattern5189 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*WC('h', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons1737, cons347, cons1738)
    def replacement5189(p, m, f, g, b, d, a, c, n, x, h, e):
        rubi.append(5189)
        return Dist(d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int((a + b*asin(c*x))**n*(-c**S(2)*x**S(2) + S(1))**p*log(h*(f + g*x)**m), x), x)
    rule5189 = ReplacementRule(pattern5189, replacement5189)
    pattern5190 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*WC('h', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons1737, cons347, cons1738)
    def replacement5190(p, m, f, g, b, d, a, c, n, x, h, e):
        rubi.append(5190)
        return Dist(d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int((a + b*acos(c*x))**n*(-c**S(2)*x**S(2) + S(1))**p*log(h*(f + g*x)**m), x), x)
    rule5190 = ReplacementRule(pattern5190, replacement5190)
    def With5191(m, g, b, f, d, a, c, x, e):
        u = IntHide((d + e*x)**m*(f + g*x)**m, x)
        rubi.append(5191)
        return -Dist(b*c, Int(Dist(S(1)/sqrt(-c**S(2)*x**S(2) + S(1)), u, x), x), x) + Dist(a + b*asin(c*x), u, x)
    pattern5191 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(f_ + x_*WC('g', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1608)
    rule5191 = ReplacementRule(pattern5191, With5191)
    def With5192(m, g, b, f, d, a, c, x, e):
        u = IntHide((d + e*x)**m*(f + g*x)**m, x)
        rubi.append(5192)
        return Dist(b*c, Int(Dist(S(1)/sqrt(-c**S(2)*x**S(2) + S(1)), u, x), x), x) + Dist(a + b*acos(c*x), u, x)
    pattern5192 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(f_ + x_*WC('g', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1608)
    rule5192 = ReplacementRule(pattern5192, With5192)
    pattern5193 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons17)
    def replacement5193(m, g, b, f, d, a, n, c, x, e):
        rubi.append(5193)
        return Int(ExpandIntegrand((a + b*asin(c*x))**n*(d + e*x)**m*(f + g*x)**m, x), x)
    rule5193 = ReplacementRule(pattern5193, replacement5193)
    pattern5194 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons17)
    def replacement5194(m, g, b, f, d, a, n, c, x, e):
        rubi.append(5194)
        return Int(ExpandIntegrand((a + b*acos(c*x))**n*(d + e*x)**m*(f + g*x)**m, x), x)
    rule5194 = ReplacementRule(pattern5194, replacement5194)
    def With5195(u, b, a, c, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        v = IntHide(u, x)
        if InverseFunctionFreeQ(v, x):
            return True
        return False
    pattern5195 = Pattern(Integral(u_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons14, CustomConstraint(With5195))
    def replacement5195(u, b, a, c, x):

        v = IntHide(u, x)
        rubi.append(5195)
        return -Dist(b*c, Int(SimplifyIntegrand(v/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asin(c*x), v, x)
    rule5195 = ReplacementRule(pattern5195, replacement5195)
    def With5196(u, b, a, c, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        v = IntHide(u, x)
        if InverseFunctionFreeQ(v, x):
            return True
        return False
    pattern5196 = Pattern(Integral(u_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons14, CustomConstraint(With5196))
    def replacement5196(u, b, a, c, x):

        v = IntHide(u, x)
        rubi.append(5196)
        return Dist(b*c, Int(SimplifyIntegrand(v/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acos(c*x), v, x)
    rule5196 = ReplacementRule(pattern5196, replacement5196)
    def With5197(p, b, Px, d, a, n, c, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(Px*(a + b*asin(c*x))**n*(d + e*x**S(2))**p, x)
        if SumQ(u):
            return True
        return False
    pattern5197 = Pattern(Integral(Px_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons925, cons1737, cons347, CustomConstraint(With5197))
    def replacement5197(p, b, Px, d, a, n, c, x, e):

        u = ExpandIntegrand(Px*(a + b*asin(c*x))**n*(d + e*x**S(2))**p, x)
        rubi.append(5197)
        return Int(u, x)
    rule5197 = ReplacementRule(pattern5197, replacement5197)
    def With5198(p, b, Px, d, a, n, c, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(Px*(a + b*acos(c*x))**n*(d + e*x**S(2))**p, x)
        if SumQ(u):
            return True
        return False
    pattern5198 = Pattern(Integral(Px_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons925, cons1737, cons347, CustomConstraint(With5198))
    def replacement5198(p, b, Px, d, a, n, c, x, e):

        u = ExpandIntegrand(Px*(a + b*acos(c*x))**n*(d + e*x**S(2))**p, x)
        rubi.append(5198)
        return Int(u, x)
    rule5198 = ReplacementRule(pattern5198, replacement5198)
    def With5199(p, m, g, b, f, Px, d, a, n, c, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(Px*(a + b*asin(c*x))**n*(f + g*(d + e*x**S(2))**p)**m, x)
        if SumQ(u):
            return True
        return False
    pattern5199 = Pattern(Integral((f_ + (d_ + x_**S(2)*WC('e', S(1)))**p_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))*WC('Px', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons925, cons1737, cons961, cons150, CustomConstraint(With5199))
    def replacement5199(p, m, g, b, f, Px, d, a, n, c, x, e):

        u = ExpandIntegrand(Px*(a + b*asin(c*x))**n*(f + g*(d + e*x**S(2))**p)**m, x)
        rubi.append(5199)
        return Int(u, x)
    rule5199 = ReplacementRule(pattern5199, replacement5199)
    def With5200(p, m, g, b, f, Px, d, a, n, c, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(Px*(a + b*acos(c*x))**n*(f + g*(d + e*x**S(2))**p)**m, x)
        if SumQ(u):
            return True
        return False
    pattern5200 = Pattern(Integral((f_ + (d_ + x_**S(2)*WC('e', S(1)))**p_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))*WC('Px', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons925, cons1737, cons961, cons150, CustomConstraint(With5200))
    def replacement5200(p, m, g, b, f, Px, d, a, n, c, x, e):

        u = ExpandIntegrand(Px*(a + b*acos(c*x))**n*(f + g*(d + e*x**S(2))**p)**m, x)
        rubi.append(5200)
        return Int(u, x)
    rule5200 = ReplacementRule(pattern5200, replacement5200)
    def With5201(x, c, n, RFx):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(asin(c*x)**n, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern5201 = Pattern(Integral(RFx_*asin(x_*WC('c', S(1)))**WC('n', S(1)), x_), cons7, cons1198, cons148, CustomConstraint(With5201))
    def replacement5201(x, c, n, RFx):

        u = ExpandIntegrand(asin(c*x)**n, RFx, x)
        rubi.append(5201)
        return Int(u, x)
    rule5201 = ReplacementRule(pattern5201, replacement5201)
    def With5202(x, c, n, RFx):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(acos(c*x)**n, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern5202 = Pattern(Integral(RFx_*acos(x_*WC('c', S(1)))**WC('n', S(1)), x_), cons7, cons1198, cons148, CustomConstraint(With5202))
    def replacement5202(x, c, n, RFx):

        u = ExpandIntegrand(acos(c*x)**n, RFx, x)
        rubi.append(5202)
        return Int(u, x)
    rule5202 = ReplacementRule(pattern5202, replacement5202)
    pattern5203 = Pattern(Integral(RFx_*(a_ + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons1198, cons148)
    def replacement5203(RFx, b, c, n, a, x):
        rubi.append(5203)
        return Int(ExpandIntegrand(RFx*(a + b*asin(c*x))**n, x), x)
    rule5203 = ReplacementRule(pattern5203, replacement5203)
    pattern5204 = Pattern(Integral(RFx_*(a_ + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons1198, cons148)
    def replacement5204(RFx, b, c, n, a, x):
        rubi.append(5204)
        return Int(ExpandIntegrand(RFx*(a + b*acos(c*x))**n, x), x)
    rule5204 = ReplacementRule(pattern5204, replacement5204)
    def With5205(p, RFx, d, c, n, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand((d + e*x**S(2))**p*asin(c*x)**n, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern5205 = Pattern(Integral(RFx_*(d_ + x_**S(2)*WC('e', S(1)))**p_*asin(x_*WC('c', S(1)))**WC('n', S(1)), x_), cons7, cons27, cons48, cons1198, cons148, cons1737, cons347, CustomConstraint(With5205))
    def replacement5205(p, RFx, d, c, n, x, e):

        u = ExpandIntegrand((d + e*x**S(2))**p*asin(c*x)**n, RFx, x)
        rubi.append(5205)
        return Int(u, x)
    rule5205 = ReplacementRule(pattern5205, replacement5205)
    def With5206(p, RFx, d, c, n, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand((d + e*x**S(2))**p*acos(c*x)**n, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern5206 = Pattern(Integral(RFx_*(d_ + x_**S(2)*WC('e', S(1)))**p_*acos(x_*WC('c', S(1)))**WC('n', S(1)), x_), cons7, cons27, cons48, cons1198, cons148, cons1737, cons347, CustomConstraint(With5206))
    def replacement5206(p, RFx, d, c, n, x, e):

        u = ExpandIntegrand((d + e*x**S(2))**p*acos(c*x)**n, RFx, x)
        rubi.append(5206)
        return Int(u, x)
    rule5206 = ReplacementRule(pattern5206, replacement5206)
    pattern5207 = Pattern(Integral(RFx_*(a_ + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons1198, cons148, cons1737, cons347)
    def replacement5207(p, RFx, b, d, c, n, a, x, e):
        rubi.append(5207)
        return Int(ExpandIntegrand((d + e*x**S(2))**p, RFx*(a + b*asin(c*x))**n, x), x)
    rule5207 = ReplacementRule(pattern5207, replacement5207)
    pattern5208 = Pattern(Integral(RFx_*(a_ + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons1198, cons148, cons1737, cons347)
    def replacement5208(p, RFx, b, d, c, n, a, x, e):
        rubi.append(5208)
        return Int(ExpandIntegrand((d + e*x**S(2))**p, RFx*(a + b*acos(c*x))**n, x), x)
    rule5208 = ReplacementRule(pattern5208, replacement5208)
    pattern5209 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(x_*WC('c', S(1))))**WC('n', S(1))*WC('u', S(1)), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement5209(u, b, a, n, c, x):
        rubi.append(5209)
        return Int(u*(a + b*asin(c*x))**n, x)
    rule5209 = ReplacementRule(pattern5209, replacement5209)
    pattern5210 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_*WC('c', S(1))))**WC('n', S(1))*WC('u', S(1)), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement5210(u, b, a, n, c, x):
        rubi.append(5210)
        return Int(u*(a + b*acos(c*x))**n, x)
    rule5210 = ReplacementRule(pattern5210, replacement5210)
    pattern5211 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1273)
    def replacement5211(b, d, c, a, n, x):
        rubi.append(5211)
        return Dist(S(1)/d, Subst(Int((a + b*asin(x))**n, x), x, c + d*x), x)
    rule5211 = ReplacementRule(pattern5211, replacement5211)
    pattern5212 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1273)
    def replacement5212(b, d, c, a, n, x):
        rubi.append(5212)
        return Dist(S(1)/d, Subst(Int((a + b*acos(x))**n, x), x, c + d*x), x)
    rule5212 = ReplacementRule(pattern5212, replacement5212)
    pattern5213 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement5213(m, f, b, d, a, n, c, x, e):
        rubi.append(5213)
        return Dist(S(1)/d, Subst(Int((a + b*asin(x))**n*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule5213 = ReplacementRule(pattern5213, replacement5213)
    pattern5214 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement5214(m, f, b, d, a, n, c, x, e):
        rubi.append(5214)
        return Dist(S(1)/d, Subst(Int((a + b*acos(x))**n*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule5214 = ReplacementRule(pattern5214, replacement5214)
    pattern5215 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons34, cons35, cons36, cons4, cons5, cons1762, cons1763)
    def replacement5215(B, C, p, b, d, a, n, c, x, A):
        rubi.append(5215)
        return Dist(S(1)/d, Subst(Int((a + b*asin(x))**n*(C*x**S(2)/d**S(2) - C/d**S(2))**p, x), x, c + d*x), x)
    rule5215 = ReplacementRule(pattern5215, replacement5215)
    pattern5216 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons34, cons35, cons36, cons4, cons5, cons1762, cons1763)
    def replacement5216(B, C, p, b, d, a, n, c, x, A):
        rubi.append(5216)
        return Dist(S(1)/d, Subst(Int((a + b*acos(x))**n*(C*x**S(2)/d**S(2) - C/d**S(2))**p, x), x, c + d*x), x)
    rule5216 = ReplacementRule(pattern5216, replacement5216)
    pattern5217 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons1762, cons1763)
    def replacement5217(B, C, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(5217)
        return Dist(S(1)/d, Subst(Int((a + b*asin(x))**n*(C*x**S(2)/d**S(2) - C/d**S(2))**p*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule5217 = ReplacementRule(pattern5217, replacement5217)
    pattern5218 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons1762, cons1763)
    def replacement5218(B, C, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(5218)
        return Dist(S(1)/d, Subst(Int((a + b*acos(x))**n*(C*x**S(2)/d**S(2) - C/d**S(2))**p*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule5218 = ReplacementRule(pattern5218, replacement5218)
    pattern5219 = Pattern(Integral(sqrt(WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons1764)
    def replacement5219(b, d, c, a, x):
        rubi.append(5219)
        return Simp(x*sqrt(a + b*asin(c + d*x**S(2))), x) + Simp(sqrt(Pi)*x*(-c*sin(a/(S(2)*b)) + cos(a/(S(2)*b)))*FresnelS(sqrt(c/(Pi*b))*sqrt(a + b*asin(c + d*x**S(2))))/(sqrt(c/b)*(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2)))), x) - Simp(sqrt(Pi)*x*(c*sin(a/(S(2)*b)) + cos(a/(S(2)*b)))*FresnelC(sqrt(c/(Pi*b))*sqrt(a + b*asin(c + d*x**S(2))))/(sqrt(c/b)*(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2)))), x)
    rule5219 = ReplacementRule(pattern5219, replacement5219)
    pattern5220 = Pattern(Integral(sqrt(WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(1))), x_), cons2, cons3, cons27, cons1765)
    def replacement5220(d, a, b, x):
        rubi.append(5220)
        return Simp(-S(2)*sqrt(a + b*acos(d*x**S(2) + S(1)))*sin(acos(d*x**S(2) + S(1))/S(2))**S(2)/(d*x), x) - Simp(S(2)*sqrt(Pi)*FresnelC(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(1))))*sin(a/(S(2)*b))*sin(acos(d*x**S(2) + S(1))/S(2))/(d*x*sqrt(S(1)/b)), x) + Simp(S(2)*sqrt(Pi)*FresnelS(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(1))))*sin(acos(d*x**S(2) + S(1))/S(2))*cos(a/(S(2)*b))/(d*x*sqrt(S(1)/b)), x)
    rule5220 = ReplacementRule(pattern5220, replacement5220)
    pattern5221 = Pattern(Integral(sqrt(WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(-1))), x_), cons2, cons3, cons27, cons1765)
    def replacement5221(d, a, b, x):
        rubi.append(5221)
        return Simp(S(2)*sqrt(a + b*acos(d*x**S(2) + S(-1)))*cos(acos(d*x**S(2) + S(-1))/S(2))**S(2)/(d*x), x) - Simp(S(2)*sqrt(Pi)*FresnelC(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(-1))))*cos(a/(S(2)*b))*cos(acos(d*x**S(2) + S(-1))/S(2))/(d*x*sqrt(S(1)/b)), x) - Simp(S(2)*sqrt(Pi)*FresnelS(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(-1))))*sin(a/(S(2)*b))*cos(acos(d*x**S(2) + S(-1))/S(2))/(d*x*sqrt(S(1)/b)), x)
    rule5221 = ReplacementRule(pattern5221, replacement5221)
    pattern5222 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_**S(2)*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons1764, cons87, cons165)
    def replacement5222(b, d, c, a, n, x):
        rubi.append(5222)
        return -Dist(S(4)*b**S(2)*n*(n + S(-1)), Int((a + b*asin(c + d*x**S(2)))**(n + S(-2)), x), x) + Simp(x*(a + b*asin(c + d*x**S(2)))**n, x) + Simp(S(2)*b*n*(a + b*asin(c + d*x**S(2)))**(n + S(-1))*sqrt(-S(2)*c*d*x**S(2) - d**S(2)*x**S(4))/(d*x), x)
    rule5222 = ReplacementRule(pattern5222, replacement5222)
    pattern5223 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(c_ + x_**S(2)*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons1764, cons87, cons165)
    def replacement5223(b, d, c, a, n, x):
        rubi.append(5223)
        return -Dist(S(4)*b**S(2)*n*(n + S(-1)), Int((a + b*acos(c + d*x**S(2)))**(n + S(-2)), x), x) + Simp(x*(a + b*acos(c + d*x**S(2)))**n, x) - Simp(S(2)*b*n*(a + b*acos(c + d*x**S(2)))**(n + S(-1))*sqrt(-S(2)*c*d*x**S(2) - d**S(2)*x**S(4))/(d*x), x)
    rule5223 = ReplacementRule(pattern5223, replacement5223)
    pattern5224 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons1764)
    def replacement5224(b, d, c, a, x):
        rubi.append(5224)
        return -Simp(x*(c*cos(a/(S(2)*b)) - sin(a/(S(2)*b)))*CosIntegral(c*(a + b*asin(c + d*x**S(2)))/(S(2)*b))/(S(2)*b*(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2)))), x) - Simp(x*(c*cos(a/(S(2)*b)) + sin(a/(S(2)*b)))*SinIntegral(c*(a + b*asin(c + d*x**S(2)))/(S(2)*b))/(S(2)*b*(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2)))), x)
    rule5224 = ReplacementRule(pattern5224, replacement5224)
    pattern5225 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(1))), x_), cons2, cons3, cons27, cons1765)
    def replacement5225(d, a, b, x):
        rubi.append(5225)
        return Simp(sqrt(S(2))*x*CosIntegral((a + b*acos(d*x**S(2) + S(1)))/(S(2)*b))*cos(a/(S(2)*b))/(S(2)*b*sqrt(-d*x**S(2))), x) + Simp(sqrt(S(2))*x*SinIntegral((a + b*acos(d*x**S(2) + S(1)))/(S(2)*b))*sin(a/(S(2)*b))/(S(2)*b*sqrt(-d*x**S(2))), x)
    rule5225 = ReplacementRule(pattern5225, replacement5225)
    pattern5226 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(-1))), x_), cons2, cons3, cons27, cons1765)
    def replacement5226(d, a, b, x):
        rubi.append(5226)
        return Simp(sqrt(S(2))*x*CosIntegral((a + b*acos(d*x**S(2) + S(-1)))/(S(2)*b))*sin(a/(S(2)*b))/(S(2)*b*sqrt(d*x**S(2))), x) - Simp(sqrt(S(2))*x*SinIntegral((a + b*acos(d*x**S(2) + S(-1)))/(S(2)*b))*cos(a/(S(2)*b))/(S(2)*b*sqrt(d*x**S(2))), x)
    rule5226 = ReplacementRule(pattern5226, replacement5226)
    pattern5227 = Pattern(Integral(S(1)/sqrt(WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons1764)
    def replacement5227(b, d, c, a, x):
        rubi.append(5227)
        return -Simp(sqrt(Pi)*x*(-c*sin(a/(S(2)*b)) + cos(a/(S(2)*b)))*FresnelC(sqrt(a + b*asin(c + d*x**S(2)))/(sqrt(Pi)*sqrt(b*c)))/(sqrt(b*c)*(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2)))), x) - Simp(sqrt(Pi)*x*(c*sin(a/(S(2)*b)) + cos(a/(S(2)*b)))*FresnelS(sqrt(a + b*asin(c + d*x**S(2)))/(sqrt(Pi)*sqrt(b*c)))/(sqrt(b*c)*(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2)))), x)
    rule5227 = ReplacementRule(pattern5227, replacement5227)
    pattern5228 = Pattern(Integral(S(1)/sqrt(WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(1))), x_), cons2, cons3, cons27, cons1765)
    def replacement5228(d, a, b, x):
        rubi.append(5228)
        return Simp(-S(2)*sqrt(Pi/b)*FresnelC(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(1))))*sin(acos(d*x**S(2) + S(1))/S(2))*cos(a/(S(2)*b))/(d*x), x) - Simp(S(2)*sqrt(Pi/b)*FresnelS(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(1))))*sin(a/(S(2)*b))*sin(acos(d*x**S(2) + S(1))/S(2))/(d*x), x)
    rule5228 = ReplacementRule(pattern5228, replacement5228)
    pattern5229 = Pattern(Integral(S(1)/sqrt(WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(-1))), x_), cons2, cons3, cons27, cons1765)
    def replacement5229(d, a, b, x):
        rubi.append(5229)
        return Simp(S(2)*sqrt(Pi/b)*FresnelC(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(-1))))*sin(a/(S(2)*b))*cos(acos(d*x**S(2) + S(-1))/S(2))/(d*x), x) - Simp(S(2)*sqrt(Pi/b)*FresnelS(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(-1))))*cos(a/(S(2)*b))*cos(acos(d*x**S(2) + S(-1))/S(2))/(d*x), x)
    rule5229 = ReplacementRule(pattern5229, replacement5229)
    pattern5230 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_**S(2)*WC('d', S(1))))**(S(-3)/2), x_), cons2, cons3, cons7, cons27, cons1764)
    def replacement5230(b, d, c, a, x):
        rubi.append(5230)
        return -Simp(sqrt(-S(2)*c*d*x**S(2) - d**S(2)*x**S(4))/(b*d*x*sqrt(a + b*asin(c + d*x**S(2)))), x) + Simp(sqrt(Pi)*x*(c/b)**(S(3)/2)*(-c*sin(a/(S(2)*b)) + cos(a/(S(2)*b)))*FresnelS(sqrt(c/(Pi*b))*sqrt(a + b*asin(c + d*x**S(2))))/(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2))), x) - Simp(sqrt(Pi)*x*(c/b)**(S(3)/2)*(c*sin(a/(S(2)*b)) + cos(a/(S(2)*b)))*FresnelC(sqrt(c/(Pi*b))*sqrt(a + b*asin(c + d*x**S(2))))/(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2))), x)
    rule5230 = ReplacementRule(pattern5230, replacement5230)
    pattern5231 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(1)))**(S(-3)/2), x_), cons2, cons3, cons27, cons1765)
    def replacement5231(d, a, b, x):
        rubi.append(5231)
        return Simp(sqrt(-d**S(2)*x**S(4) - S(2)*d*x**S(2))/(b*d*x*sqrt(a + b*acos(d*x**S(2) + S(1)))), x) - Simp(S(2)*sqrt(Pi)*(S(1)/b)**(S(3)/2)*FresnelC(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(1))))*sin(a/(S(2)*b))*sin(acos(d*x**S(2) + S(1))/S(2))/(d*x), x) + Simp(S(2)*sqrt(Pi)*(S(1)/b)**(S(3)/2)*FresnelS(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(1))))*sin(acos(d*x**S(2) + S(1))/S(2))*cos(a/(S(2)*b))/(d*x), x)
    rule5231 = ReplacementRule(pattern5231, replacement5231)
    pattern5232 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(-1)))**(S(-3)/2), x_), cons2, cons3, cons27, cons1765)
    def replacement5232(d, a, b, x):
        rubi.append(5232)
        return Simp(sqrt(-d**S(2)*x**S(4) + S(2)*d*x**S(2))/(b*d*x*sqrt(a + b*acos(d*x**S(2) + S(-1)))), x) - Simp(S(2)*sqrt(Pi)*(S(1)/b)**(S(3)/2)*FresnelC(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(-1))))*cos(a/(S(2)*b))*cos(acos(d*x**S(2) + S(-1))/S(2))/(d*x), x) - Simp(S(2)*sqrt(Pi)*(S(1)/b)**(S(3)/2)*FresnelS(sqrt(S(1)/(Pi*b))*sqrt(a + b*acos(d*x**S(2) + S(-1))))*sin(a/(S(2)*b))*cos(acos(d*x**S(2) + S(-1))/S(2))/(d*x), x)
    rule5232 = ReplacementRule(pattern5232, replacement5232)
    pattern5233 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_**S(2)*WC('d', S(1))))**(S(-2)), x_), cons2, cons3, cons7, cons27, cons1764)
    def replacement5233(b, d, c, a, x):
        rubi.append(5233)
        return Simp(x*(-c*sin(a/(S(2)*b)) + cos(a/(S(2)*b)))*SinIntegral(c*(a + b*asin(c + d*x**S(2)))/(S(2)*b))/(S(4)*b**S(2)*(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2)))), x) - Simp(x*(c*sin(a/(S(2)*b)) + cos(a/(S(2)*b)))*CosIntegral(c*(a + b*asin(c + d*x**S(2)))/(S(2)*b))/(S(4)*b**S(2)*(-c*sin(asin(c + d*x**S(2))/S(2)) + cos(asin(c + d*x**S(2))/S(2)))), x) - Simp(sqrt(-S(2)*c*d*x**S(2) - d**S(2)*x**S(4))/(S(2)*b*d*x*(a + b*asin(c + d*x**S(2)))), x)
    rule5233 = ReplacementRule(pattern5233, replacement5233)
    pattern5234 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(1)))**(S(-2)), x_), cons2, cons3, cons27, cons1765)
    def replacement5234(d, a, b, x):
        rubi.append(5234)
        return Simp(sqrt(-d**S(2)*x**S(4) - S(2)*d*x**S(2))/(S(2)*b*d*x*(a + b*acos(d*x**S(2) + S(1)))), x) + Simp(sqrt(S(2))*x*CosIntegral((a + b*acos(d*x**S(2) + S(1)))/(S(2)*b))*sin(a/(S(2)*b))/(S(4)*b**S(2)*sqrt(-d*x**S(2))), x) - Simp(sqrt(S(2))*x*SinIntegral((a + b*acos(d*x**S(2) + S(1)))/(S(2)*b))*cos(a/(S(2)*b))/(S(4)*b**S(2)*sqrt(-d*x**S(2))), x)
    rule5234 = ReplacementRule(pattern5234, replacement5234)
    pattern5235 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(x_**S(2)*WC('d', S(1)) + S(-1)))**(S(-2)), x_), cons2, cons3, cons27, cons1765)
    def replacement5235(d, a, b, x):
        rubi.append(5235)
        return Simp(sqrt(-d**S(2)*x**S(4) + S(2)*d*x**S(2))/(S(2)*b*d*x*(a + b*acos(d*x**S(2) + S(-1)))), x) - Simp(sqrt(S(2))*x*CosIntegral((a + b*acos(d*x**S(2) + S(-1)))/(S(2)*b))*cos(a/(S(2)*b))/(S(4)*b**S(2)*sqrt(d*x**S(2))), x) - Simp(sqrt(S(2))*x*SinIntegral((a + b*acos(d*x**S(2) + S(-1)))/(S(2)*b))*sin(a/(S(2)*b))/(S(4)*b**S(2)*sqrt(d*x**S(2))), x)
    rule5235 = ReplacementRule(pattern5235, replacement5235)
    pattern5236 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asin(c_ + x_**S(2)*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons1764, cons87, cons89, cons1442)
    def replacement5236(b, d, c, a, n, x):
        rubi.append(5236)
        return -Dist(S(1)/(S(4)*b**S(2)*(n + S(1))*(n + S(2))), Int((a + b*asin(c + d*x**S(2)))**(n + S(2)), x), x) + Simp(x*(a + b*asin(c + d*x**S(2)))**(n + S(2))/(S(4)*b**S(2)*(n + S(1))*(n + S(2))), x) + Simp((a + b*asin(c + d*x**S(2)))**(n + S(1))*sqrt(-S(2)*c*d*x**S(2) - d**S(2)*x**S(4))/(S(2)*b*d*x*(n + S(1))), x)
    rule5236 = ReplacementRule(pattern5236, replacement5236)
    pattern5237 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acos(c_ + x_**S(2)*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons1764, cons87, cons89, cons1442)
    def replacement5237(b, d, c, a, n, x):
        rubi.append(5237)
        return -Dist(S(1)/(S(4)*b**S(2)*(n + S(1))*(n + S(2))), Int((a + b*acos(c + d*x**S(2)))**(n + S(2)), x), x) + Simp(x*(a + b*acos(c + d*x**S(2)))**(n + S(2))/(S(4)*b**S(2)*(n + S(1))*(n + S(2))), x) - Simp((a + b*acos(c + d*x**S(2)))**(n + S(1))*sqrt(-S(2)*c*d*x**S(2) - d**S(2)*x**S(4))/(S(2)*b*d*x*(n + S(1))), x)
    rule5237 = ReplacementRule(pattern5237, replacement5237)
    pattern5238 = Pattern(Integral(asin(x_**p_*WC('a', S(1)))**WC('n', S(1))/x_, x_), cons2, cons5, cons148)
    def replacement5238(x, a, n, p):
        rubi.append(5238)
        return Dist(S(1)/p, Subst(Int(x**n/tan(x), x), x, asin(a*x**p)), x)
    rule5238 = ReplacementRule(pattern5238, replacement5238)
    pattern5239 = Pattern(Integral(acos(x_**p_*WC('a', S(1)))**WC('n', S(1))/x_, x_), cons2, cons5, cons148)
    def replacement5239(x, a, n, p):
        rubi.append(5239)
        return -Dist(S(1)/p, Subst(Int(x**n*tan(x), x), x, acos(a*x**p)), x)
    rule5239 = ReplacementRule(pattern5239, replacement5239)
    pattern5240 = Pattern(Integral(WC('u', S(1))*asin(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement5240(u, m, b, c, n, a, x):
        rubi.append(5240)
        return Int(u*acsc(a/c + b*x**n/c)**m, x)
    rule5240 = ReplacementRule(pattern5240, replacement5240)
    pattern5241 = Pattern(Integral(WC('u', S(1))*acos(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement5241(u, m, b, c, n, a, x):
        rubi.append(5241)
        return Int(u*asec(a/c + b*x**n/c)**m, x)
    rule5241 = ReplacementRule(pattern5241, replacement5241)
    pattern5242 = Pattern(Integral(asin(sqrt(x_**S(2)*WC('b', S(1)) + S(1)))**WC('n', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + S(1)), x_), cons3, cons4, cons1767)
    def replacement5242(x, n, b):
        rubi.append(5242)
        return Dist(sqrt(-b*x**S(2))/(b*x), Subst(Int(asin(x)**n/sqrt(-x**S(2) + S(1)), x), x, sqrt(b*x**S(2) + S(1))), x)
    rule5242 = ReplacementRule(pattern5242, replacement5242)
    pattern5243 = Pattern(Integral(acos(sqrt(x_**S(2)*WC('b', S(1)) + S(1)))**WC('n', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + S(1)), x_), cons3, cons4, cons1767)
    def replacement5243(x, n, b):
        rubi.append(5243)
        return Dist(sqrt(-b*x**S(2))/(b*x), Subst(Int(acos(x)**n/sqrt(-x**S(2) + S(1)), x), x, sqrt(b*x**S(2) + S(1))), x)
    rule5243 = ReplacementRule(pattern5243, replacement5243)
    pattern5244 = Pattern(Integral(f_**(WC('c', S(1))*asin(x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)))*WC('u', S(1)), x_), cons2, cons3, cons7, cons125, cons148)
    def replacement5244(u, f, b, c, a, n, x):
        rubi.append(5244)
        return Dist(S(1)/b, Subst(Int(f**(c*x**n)*ReplaceAll(u, Rule(x, -a/b + sin(x)/b))*cos(x), x), x, asin(a + b*x)), x)
    rule5244 = ReplacementRule(pattern5244, replacement5244)
    pattern5245 = Pattern(Integral(f_**(WC('c', S(1))*acos(x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)))*WC('u', S(1)), x_), cons2, cons3, cons7, cons125, cons148)
    def replacement5245(u, f, b, c, a, n, x):
        rubi.append(5245)
        return -Dist(S(1)/b, Subst(Int(f**(c*x**n)*ReplaceAll(u, Rule(x, -a/b + cos(x)/b))*sin(x), x), x, acos(a + b*x)), x)
    rule5245 = ReplacementRule(pattern5245, replacement5245)
    pattern5246 = Pattern(Integral(asin(x_**S(2)*WC('a', S(1)) + sqrt(c_ + x_**S(2)*WC('d', S(1)))*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons1768)
    def replacement5246(b, d, c, a, x):
        rubi.append(5246)
        return -Dist(x*sqrt(a**S(2)*x**S(2) + S(2)*a*b*sqrt(c + d*x**S(2)) + b**S(2)*d)/sqrt(-x**S(2)*(a**S(2)*x**S(2) + S(2)*a*b*sqrt(c + d*x**S(2)) + b**S(2)*d)), Int(x*(S(2)*a*sqrt(c + d*x**S(2)) + b*d)/(sqrt(c + d*x**S(2))*sqrt(a**S(2)*x**S(2) + S(2)*a*b*sqrt(c + d*x**S(2)) + b**S(2)*d)), x), x) + Simp(x*asin(a*x**S(2) + b*sqrt(c + d*x**S(2))), x)
    rule5246 = ReplacementRule(pattern5246, replacement5246)
    pattern5247 = Pattern(Integral(acos(x_**S(2)*WC('a', S(1)) + sqrt(c_ + x_**S(2)*WC('d', S(1)))*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons1768)
    def replacement5247(b, d, c, a, x):
        rubi.append(5247)
        return Dist(x*sqrt(a**S(2)*x**S(2) + S(2)*a*b*sqrt(c + d*x**S(2)) + b**S(2)*d)/sqrt(-x**S(2)*(a**S(2)*x**S(2) + S(2)*a*b*sqrt(c + d*x**S(2)) + b**S(2)*d)), Int(x*(S(2)*a*sqrt(c + d*x**S(2)) + b*d)/(sqrt(c + d*x**S(2))*sqrt(a**S(2)*x**S(2) + S(2)*a*b*sqrt(c + d*x**S(2)) + b**S(2)*d)), x), x) + Simp(x*acos(a*x**S(2) + b*sqrt(c + d*x**S(2))), x)
    rule5247 = ReplacementRule(pattern5247, replacement5247)
    pattern5248 = Pattern(Integral(asin(u_), x_), cons1230, cons1769)
    def replacement5248(x, u):
        rubi.append(5248)
        return -Int(SimplifyIntegrand(x*D(u, x)/sqrt(-u**S(2) + S(1)), x), x) + Simp(x*asin(u), x)
    rule5248 = ReplacementRule(pattern5248, replacement5248)
    pattern5249 = Pattern(Integral(acos(u_), x_), cons1230, cons1769)
    def replacement5249(x, u):
        rubi.append(5249)
        return Int(SimplifyIntegrand(x*D(u, x)/sqrt(-u**S(2) + S(1)), x), x) + Simp(x*acos(u), x)
    rule5249 = ReplacementRule(pattern5249, replacement5249)
    pattern5250 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asin(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1769)
    def replacement5250(u, m, b, d, c, a, x):
        rubi.append(5250)
        return -Dist(b/(d*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/sqrt(-u**S(2) + S(1)), x), x), x) + Simp((a + b*asin(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule5250 = ReplacementRule(pattern5250, replacement5250)
    pattern5251 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acos(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1769)
    def replacement5251(u, m, b, d, c, a, x):
        rubi.append(5251)
        return Dist(b/(d*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/sqrt(-u**S(2) + S(1)), x), x), x) + Simp((a + b*acos(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule5251 = ReplacementRule(pattern5251, replacement5251)
    def With5252(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern5252 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*asin(u_)), x_), cons2, cons3, cons1230, cons1771, CustomConstraint(With5252))
    def replacement5252(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(5252)
        return -Dist(b, Int(SimplifyIntegrand(w*D(u, x)/sqrt(-u**S(2) + S(1)), x), x), x) + Dist(a + b*asin(u), w, x)
    rule5252 = ReplacementRule(pattern5252, replacement5252)
    def With5253(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern5253 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*acos(u_)), x_), cons2, cons3, cons1230, cons1772, CustomConstraint(With5253))
    def replacement5253(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(5253)
        return Dist(b, Int(SimplifyIntegrand(w*D(u, x)/sqrt(-u**S(2) + S(1)), x), x), x) + Dist(a + b*acos(u), w, x)
    rule5253 = ReplacementRule(pattern5253, replacement5253)
    pattern5254 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons148)
    def replacement5254(b, a, n, c, x):
        rubi.append(5254)
        return -Dist(b*c*n, Int(x*(a + b*ArcTan(c*x))**(n + S(-1))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*ArcTan(c*x))**n, x)
    rule5254 = ReplacementRule(pattern5254, replacement5254)
    pattern5255 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons148)
    def replacement5255(b, a, n, c, x):
        rubi.append(5255)
        return Dist(b*c*n, Int(x*(a + b*acot(c*x))**(n + S(-1))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*acot(c*x))**n, x)
    rule5255 = ReplacementRule(pattern5255, replacement5255)
    pattern5256 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons4, cons340)
    def replacement5256(b, a, n, c, x):
        rubi.append(5256)
        return Int((a + b*ArcTan(c*x))**n, x)
    rule5256 = ReplacementRule(pattern5256, replacement5256)
    pattern5257 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons340)
    def replacement5257(b, a, n, c, x):
        rubi.append(5257)
        return Int((a + b*acot(c*x))**n, x)
    rule5257 = ReplacementRule(pattern5257, replacement5257)
    pattern5258 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1773, cons148)
    def replacement5258(b, d, a, n, c, x, e):
        rubi.append(5258)
        return Dist(b*c*n/e, Int((a + b*ArcTan(c*x))**(n + S(-1))*log(S(2)*d/(d + e*x))/(c**S(2)*x**S(2) + S(1)), x), x) - Simp((a + b*ArcTan(c*x))**n*log(S(2)*d/(d + e*x))/e, x)
    rule5258 = ReplacementRule(pattern5258, replacement5258)
    pattern5259 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1773, cons148)
    def replacement5259(b, d, a, n, c, x, e):
        rubi.append(5259)
        return -Dist(b*c*n/e, Int((a + b*acot(c*x))**(n + S(-1))*log(S(2)*d/(d + e*x))/(c**S(2)*x**S(2) + S(1)), x), x) - Simp((a + b*acot(c*x))**n*log(S(2)*d/(d + e*x))/e, x)
    rule5259 = ReplacementRule(pattern5259, replacement5259)
    pattern5260 = Pattern(Integral(ArcTan(x_*WC('c', S(1)))/(d_ + x_*WC('e', S(1))), x_), cons7, cons27, cons48, cons1774, cons1775)
    def replacement5260(x, d, c, e):
        rubi.append(5260)
        return Simp(I*PolyLog(S(2), Simp(I*c*(d + e*x)/(I*c*d - e), x))/(S(2)*e), x) - Simp(I*PolyLog(S(2), Simp(I*c*(d + e*x)/(I*c*d + e), x))/(S(2)*e), x) - Simp(ArcTan(c*d/e)*log(d + e*x)/e, x)
    rule5260 = ReplacementRule(pattern5260, replacement5260)
    pattern5261 = Pattern(Integral(ArcTan(x_*WC('c', S(1)))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons7, cons27, cons48, cons1776)
    def replacement5261(d, c, x, e):
        rubi.append(5261)
        return Dist(I/S(2), Int(log(-I*c*x + S(1))/(d + e*x), x), x) - Dist(I/S(2), Int(log(I*c*x + S(1))/(d + e*x), x), x)
    rule5261 = ReplacementRule(pattern5261, replacement5261)
    pattern5262 = Pattern(Integral(acot(x_*WC('c', S(1)))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons7, cons27, cons48, cons1776)
    def replacement5262(d, c, x, e):
        rubi.append(5262)
        return Dist(I/S(2), Int(log(S(1) - I/(c*x))/(d + e*x), x), x) - Dist(I/S(2), Int(log(S(1) + I/(c*x))/(d + e*x), x), x)
    rule5262 = ReplacementRule(pattern5262, replacement5262)
    pattern5263 = Pattern(Integral((a_ + ArcTan(x_*WC('c', S(1)))*WC('b', S(1)))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement5263(b, d, c, a, x, e):
        rubi.append(5263)
        return Dist(b, Int(ArcTan(c*x)/(d + e*x), x), x) + Simp(a*log(RemoveContent(d + e*x, x))/e, x)
    rule5263 = ReplacementRule(pattern5263, replacement5263)
    pattern5264 = Pattern(Integral((a_ + WC('b', S(1))*acot(x_*WC('c', S(1))))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement5264(b, d, c, a, x, e):
        rubi.append(5264)
        return Dist(b, Int(acot(c*x)/(d + e*x), x), x) + Simp(a*log(RemoveContent(d + e*x, x))/e, x)
    rule5264 = ReplacementRule(pattern5264, replacement5264)
    pattern5265 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement5265(p, b, d, a, c, x, e):
        rubi.append(5265)
        return -Dist(b*c/(e*(p + S(1))), Int((d + e*x)**(p + S(1))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*ArcTan(c*x))*(d + e*x)**(p + S(1))/(e*(p + S(1))), x)
    rule5265 = ReplacementRule(pattern5265, replacement5265)
    pattern5266 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement5266(p, b, d, a, c, x, e):
        rubi.append(5266)
        return Dist(b*c/(e*(p + S(1))), Int((d + e*x)**(p + S(1))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*acot(c*x))*(d + e*x)**(p + S(1))/(e*(p + S(1))), x)
    rule5266 = ReplacementRule(pattern5266, replacement5266)
    pattern5267 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_/x_, x_), cons2, cons3, cons7, cons85, cons165)
    def replacement5267(b, a, n, c, x):
        rubi.append(5267)
        return -Dist(S(2)*b*c*n, Int((a + b*ArcTan(c*x))**(n + S(-1))*atanh(S(1) - S(2)*I/(-c*x + I))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp(S(2)*(a + b*ArcTan(c*x))**n*atanh(S(1) - S(2)*I/(-c*x + I)), x)
    rule5267 = ReplacementRule(pattern5267, replacement5267)
    pattern5268 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_/x_, x_), cons2, cons3, cons7, cons85, cons165)
    def replacement5268(b, a, n, c, x):
        rubi.append(5268)
        return Dist(S(2)*b*c*n, Int((a + b*acot(c*x))**(n + S(-1))*acoth(S(1) - S(2)*I/(-c*x + I))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp(S(2)*(a + b*acot(c*x))**n*acoth(S(1) - S(2)*I/(-c*x + I)), x)
    rule5268 = ReplacementRule(pattern5268, replacement5268)
    pattern5269 = Pattern(Integral(x_**WC('m', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons21, cons85, cons165, cons66)
    def replacement5269(m, b, a, c, n, x):
        rubi.append(5269)
        return -Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*ArcTan(c*x))**(n + S(-1))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp(x**(m + S(1))*(a + b*ArcTan(c*x))**n/(m + S(1)), x)
    rule5269 = ReplacementRule(pattern5269, replacement5269)
    pattern5270 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons21, cons85, cons165, cons66)
    def replacement5270(m, b, a, c, n, x):
        rubi.append(5270)
        return Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*acot(c*x))**(n + S(-1))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp(x**(m + S(1))*(a + b*acot(c*x))**n/(m + S(1)), x)
    rule5270 = ReplacementRule(pattern5270, replacement5270)
    pattern5271 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons464)
    def replacement5271(p, b, d, a, n, c, x, e):
        rubi.append(5271)
        return Int(ExpandIntegrand((a + b*ArcTan(c*x))**n*(d + e*x)**p, x), x)
    rule5271 = ReplacementRule(pattern5271, replacement5271)
    pattern5272 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons464)
    def replacement5272(p, b, d, a, n, c, x, e):
        rubi.append(5272)
        return Int(ExpandIntegrand((a + b*acot(c*x))**n*(d + e*x)**p, x), x)
    rule5272 = ReplacementRule(pattern5272, replacement5272)
    pattern5273 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement5273(p, b, d, a, n, c, x, e):
        rubi.append(5273)
        return Int((a + b*ArcTan(c*x))**n*(d + e*x)**p, x)
    rule5273 = ReplacementRule(pattern5273, replacement5273)
    pattern5274 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement5274(p, b, d, a, n, c, x, e):
        rubi.append(5274)
        return Int((a + b*acot(c*x))**n*(d + e*x)**p, x)
    rule5274 = ReplacementRule(pattern5274, replacement5274)
    pattern5275 = Pattern(Integral(x_**WC('m', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1773, cons148, cons31, cons168)
    def replacement5275(m, b, d, a, n, c, x, e):
        rubi.append(5275)
        return Dist(S(1)/e, Int(x**(m + S(-1))*(a + b*ArcTan(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-1))*(a + b*ArcTan(c*x))**n/(d + e*x), x), x)
    rule5275 = ReplacementRule(pattern5275, replacement5275)
    pattern5276 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1773, cons148, cons31, cons168)
    def replacement5276(m, b, d, a, n, c, x, e):
        rubi.append(5276)
        return Dist(S(1)/e, Int(x**(m + S(-1))*(a + b*acot(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-1))*(a + b*acot(c*x))**n/(d + e*x), x), x)
    rule5276 = ReplacementRule(pattern5276, replacement5276)
    pattern5277 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(x_*(d_ + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1773, cons148)
    def replacement5277(b, d, a, n, c, x, e):
        rubi.append(5277)
        return -Dist(b*c*n/d, Int((a + b*ArcTan(c*x))**(n + S(-1))*log(S(2)*e*x/(d + e*x))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*ArcTan(c*x))**n*log(S(2)*e*x/(d + e*x))/d, x)
    rule5277 = ReplacementRule(pattern5277, replacement5277)
    pattern5278 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1773, cons148)
    def replacement5278(b, d, a, n, c, x, e):
        rubi.append(5278)
        return Dist(b*c*n/d, Int((a + b*acot(c*x))**(n + S(-1))*log(S(2)*e*x/(d + e*x))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*acot(c*x))**n*log(S(2)*e*x/(d + e*x))/d, x)
    rule5278 = ReplacementRule(pattern5278, replacement5278)
    pattern5279 = Pattern(Integral(x_**m_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1773, cons148, cons31, cons94)
    def replacement5279(m, b, d, a, n, c, x, e):
        rubi.append(5279)
        return Dist(S(1)/d, Int(x**m*(a + b*ArcTan(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(1))*(a + b*ArcTan(c*x))**n/(d + e*x), x), x)
    rule5279 = ReplacementRule(pattern5279, replacement5279)
    pattern5280 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1773, cons148, cons31, cons94)
    def replacement5280(m, b, d, a, n, c, x, e):
        rubi.append(5280)
        return Dist(S(1)/d, Int(x**m*(a + b*acot(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(1))*(a + b*acot(c*x))**n/(d + e*x), x), x)
    rule5280 = ReplacementRule(pattern5280, replacement5280)
    pattern5281 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons1777)
    def replacement5281(p, m, b, d, a, n, c, x, e):
        rubi.append(5281)
        return Int(ExpandIntegrand(x**m*(a + b*ArcTan(c*x))**n*(d + e*x)**p, x), x)
    rule5281 = ReplacementRule(pattern5281, replacement5281)
    pattern5282 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons1777)
    def replacement5282(p, m, b, d, a, n, c, x, e):
        rubi.append(5282)
        return Int(ExpandIntegrand(x**m*(a + b*acot(c*x))**n*(d + e*x)**p, x), x)
    rule5282 = ReplacementRule(pattern5282, replacement5282)
    pattern5283 = Pattern(Integral(x_**WC('m', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement5283(p, m, b, d, a, n, c, x, e):
        rubi.append(5283)
        return Int(x**m*(a + b*ArcTan(c*x))**n*(d + e*x)**p, x)
    rule5283 = ReplacementRule(pattern5283, replacement5283)
    pattern5284 = Pattern(Integral(x_**WC('m', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement5284(p, m, b, d, a, n, c, x, e):
        rubi.append(5284)
        return Int(x**m*(a + b*acot(c*x))**n*(d + e*x)**p, x)
    rule5284 = ReplacementRule(pattern5284, replacement5284)
    pattern5285 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons13, cons163)
    def replacement5285(p, b, d, a, c, x, e):
        rubi.append(5285)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*ArcTan(c*x))*(d + e*x**S(2))**(p + S(-1)), x), x) + Simp(x*(a + b*ArcTan(c*x))*(d + e*x**S(2))**p/(S(2)*p + S(1)), x) - Simp(b*(d + e*x**S(2))**p/(S(2)*c*p*(S(2)*p + S(1))), x)
    rule5285 = ReplacementRule(pattern5285, replacement5285)
    pattern5286 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons13, cons163)
    def replacement5286(p, b, d, a, c, x, e):
        rubi.append(5286)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*acot(c*x))*(d + e*x**S(2))**(p + S(-1)), x), x) + Simp(x*(a + b*acot(c*x))*(d + e*x**S(2))**p/(S(2)*p + S(1)), x) + Simp(b*(d + e*x**S(2))**p/(S(2)*c*p*(S(2)*p + S(1))), x)
    rule5286 = ReplacementRule(pattern5286, replacement5286)
    pattern5287 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons338, cons163, cons165)
    def replacement5287(p, b, d, a, c, n, x, e):
        rubi.append(5287)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) + Dist(b**S(2)*d*n*(n + S(-1))/(S(2)*p*(S(2)*p + S(1))), Int((a + b*ArcTan(c*x))**(n + S(-2))*(d + e*x**S(2))**(p + S(-1)), x), x) + Simp(x*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**p/(S(2)*p + S(1)), x) - Simp(b*n*(a + b*ArcTan(c*x))**(n + S(-1))*(d + e*x**S(2))**p/(S(2)*c*p*(S(2)*p + S(1))), x)
    rule5287 = ReplacementRule(pattern5287, replacement5287)
    pattern5288 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons338, cons163, cons165)
    def replacement5288(p, b, d, a, c, n, x, e):
        rubi.append(5288)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) + Dist(b**S(2)*d*n*(n + S(-1))/(S(2)*p*(S(2)*p + S(1))), Int((a + b*acot(c*x))**(n + S(-2))*(d + e*x**S(2))**(p + S(-1)), x), x) + Simp(x*(a + b*acot(c*x))**n*(d + e*x**S(2))**p/(S(2)*p + S(1)), x) + Simp(b*n*(a + b*acot(c*x))**(n + S(-1))*(d + e*x**S(2))**p/(S(2)*c*p*(S(2)*p + S(1))), x)
    rule5288 = ReplacementRule(pattern5288, replacement5288)
    pattern5289 = Pattern(Integral(S(1)/((d_ + x_**S(2)*WC('e', S(1)))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778)
    def replacement5289(b, d, a, c, x, e):
        rubi.append(5289)
        return Simp(log(RemoveContent(a + b*ArcTan(c*x), x))/(b*c*d), x)
    rule5289 = ReplacementRule(pattern5289, replacement5289)
    pattern5290 = Pattern(Integral(S(1)/((d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))), x_), cons2, cons3, cons7, cons27, cons48, cons1778)
    def replacement5290(b, d, a, c, x, e):
        rubi.append(5290)
        return -Simp(log(RemoveContent(a + b*acot(c*x), x))/(b*c*d), x)
    rule5290 = ReplacementRule(pattern5290, replacement5290)
    pattern5291 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons584)
    def replacement5291(b, d, a, n, c, x, e):
        rubi.append(5291)
        return Simp((a + b*ArcTan(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule5291 = ReplacementRule(pattern5291, replacement5291)
    pattern5292 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons584)
    def replacement5292(b, d, a, n, c, x, e):
        rubi.append(5292)
        return -Simp((a + b*acot(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule5292 = ReplacementRule(pattern5292, replacement5292)
    pattern5293 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons268)
    def replacement5293(b, d, a, c, x, e):
        rubi.append(5293)
        return Simp(I*b*PolyLog(S(2), -I*sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/(c*sqrt(d)), x) - Simp(I*b*PolyLog(S(2), I*sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/(c*sqrt(d)), x) + Simp(-S(2)*I*(a + b*ArcTan(c*x))*ArcTan(sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/(c*sqrt(d)), x)
    rule5293 = ReplacementRule(pattern5293, replacement5293)
    pattern5294 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons268)
    def replacement5294(b, d, a, c, x, e):
        rubi.append(5294)
        return -Simp(I*b*PolyLog(S(2), -I*sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/(c*sqrt(d)), x) + Simp(I*b*PolyLog(S(2), I*sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/(c*sqrt(d)), x) + Simp(-S(2)*I*(a + b*acot(c*x))*ArcTan(sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/(c*sqrt(d)), x)
    rule5294 = ReplacementRule(pattern5294, replacement5294)
    pattern5295 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148, cons268)
    def replacement5295(b, d, a, n, c, x, e):
        rubi.append(5295)
        return Dist(S(1)/(c*sqrt(d)), Subst(Int((a + b*x)**n/cos(x), x), x, ArcTan(c*x)), x)
    rule5295 = ReplacementRule(pattern5295, replacement5295)
    pattern5296 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148, cons268)
    def replacement5296(b, d, a, n, c, x, e):
        rubi.append(5296)
        return -Dist(x*sqrt(S(1) + S(1)/(c**S(2)*x**S(2)))/sqrt(d + e*x**S(2)), Subst(Int((a + b*x)**n/sin(x), x), x, acot(c*x)), x)
    rule5296 = ReplacementRule(pattern5296, replacement5296)
    pattern5297 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148, cons1738)
    def replacement5297(b, d, a, n, c, x, e):
        rubi.append(5297)
        return Dist(sqrt(c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*ArcTan(c*x))**n/sqrt(c**S(2)*x**S(2) + S(1)), x), x)
    rule5297 = ReplacementRule(pattern5297, replacement5297)
    pattern5298 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148, cons1738)
    def replacement5298(b, d, a, n, c, x, e):
        rubi.append(5298)
        return Dist(sqrt(c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*acot(c*x))**n/sqrt(c**S(2)*x**S(2) + S(1)), x), x)
    rule5298 = ReplacementRule(pattern5298, replacement5298)
    pattern5299 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement5299(b, d, a, n, c, x, e):
        rubi.append(5299)
        return -Dist(b*c*n/S(2), Int(x*(a + b*ArcTan(c*x))**(n + S(-1))/(d + e*x**S(2))**S(2), x), x) + Simp(x*(a + b*ArcTan(c*x))**n/(S(2)*d*(d + e*x**S(2))), x) + Simp((a + b*ArcTan(c*x))**(n + S(1))/(S(2)*b*c*d**S(2)*(n + S(1))), x)
    rule5299 = ReplacementRule(pattern5299, replacement5299)
    pattern5300 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement5300(b, d, a, n, c, x, e):
        rubi.append(5300)
        return Dist(b*c*n/S(2), Int(x*(a + b*acot(c*x))**(n + S(-1))/(d + e*x**S(2))**S(2), x), x) + Simp(x*(a + b*acot(c*x))**n/(S(2)*d*(d + e*x**S(2))), x) - Simp((a + b*acot(c*x))**(n + S(1))/(S(2)*b*c*d**S(2)*(n + S(1))), x)
    rule5300 = ReplacementRule(pattern5300, replacement5300)
    pattern5301 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1778)
    def replacement5301(b, d, a, c, x, e):
        rubi.append(5301)
        return Simp(b/(c*d*sqrt(d + e*x**S(2))), x) + Simp(x*(a + b*ArcTan(c*x))/(d*sqrt(d + e*x**S(2))), x)
    rule5301 = ReplacementRule(pattern5301, replacement5301)
    pattern5302 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1778)
    def replacement5302(b, d, a, c, x, e):
        rubi.append(5302)
        return -Simp(b/(c*d*sqrt(d + e*x**S(2))), x) + Simp(x*(a + b*acot(c*x))/(d*sqrt(d + e*x**S(2))), x)
    rule5302 = ReplacementRule(pattern5302, replacement5302)
    pattern5303 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons13, cons137, cons230)
    def replacement5303(p, b, d, a, c, x, e):
        rubi.append(5303)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*ArcTan(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) + Simp(b*(d + e*x**S(2))**(p + S(1))/(S(4)*c*d*(p + S(1))**S(2)), x) - Simp(x*(a + b*ArcTan(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x)
    rule5303 = ReplacementRule(pattern5303, replacement5303)
    pattern5304 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons13, cons137, cons230)
    def replacement5304(p, b, d, a, c, x, e):
        rubi.append(5304)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*acot(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(b*(d + e*x**S(2))**(p + S(1))/(S(4)*c*d*(p + S(1))**S(2)), x) - Simp(x*(a + b*acot(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x)
    rule5304 = ReplacementRule(pattern5304, replacement5304)
    pattern5305 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons165)
    def replacement5305(b, d, a, c, n, x, e):
        rubi.append(5305)
        return -Dist(b**S(2)*n*(n + S(-1)), Int((a + b*ArcTan(c*x))**(n + S(-2))/(d + e*x**S(2))**(S(3)/2), x), x) + Simp(x*(a + b*ArcTan(c*x))**n/(d*sqrt(d + e*x**S(2))), x) + Simp(b*n*(a + b*ArcTan(c*x))**(n + S(-1))/(c*d*sqrt(d + e*x**S(2))), x)
    rule5305 = ReplacementRule(pattern5305, replacement5305)
    pattern5306 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons165)
    def replacement5306(b, d, a, c, n, x, e):
        rubi.append(5306)
        return -Dist(b**S(2)*n*(n + S(-1)), Int((a + b*acot(c*x))**(n + S(-2))/(d + e*x**S(2))**(S(3)/2), x), x) + Simp(x*(a + b*acot(c*x))**n/(d*sqrt(d + e*x**S(2))), x) - Simp(b*n*(a + b*acot(c*x))**(n + S(-1))/(c*d*sqrt(d + e*x**S(2))), x)
    rule5306 = ReplacementRule(pattern5306, replacement5306)
    pattern5307 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons338, cons137, cons165, cons230)
    def replacement5307(p, b, d, a, c, n, x, e):
        rubi.append(5307)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(b**S(2)*n*(n + S(-1))/(S(4)*(p + S(1))**S(2)), Int((a + b*ArcTan(c*x))**(n + S(-2))*(d + e*x**S(2))**p, x), x) - Simp(x*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x) + Simp(b*n*(a + b*ArcTan(c*x))**(n + S(-1))*(d + e*x**S(2))**(p + S(1))/(S(4)*c*d*(p + S(1))**S(2)), x)
    rule5307 = ReplacementRule(pattern5307, replacement5307)
    pattern5308 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons338, cons137, cons165, cons230)
    def replacement5308(p, b, d, a, c, n, x, e):
        rubi.append(5308)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(b**S(2)*n*(n + S(-1))/(S(4)*(p + S(1))**S(2)), Int((a + b*acot(c*x))**(n + S(-2))*(d + e*x**S(2))**p, x), x) - Simp(x*(a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x) - Simp(b*n*(a + b*acot(c*x))**(n + S(-1))*(d + e*x**S(2))**(p + S(1))/(S(4)*c*d*(p + S(1))**S(2)), x)
    rule5308 = ReplacementRule(pattern5308, replacement5308)
    pattern5309 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons338, cons137, cons89)
    def replacement5309(p, b, d, a, c, n, x, e):
        rubi.append(5309)
        return -Dist(S(2)*c*(p + S(1))/(b*(n + S(1))), Int(x*(a + b*ArcTan(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Simp((a + b*ArcTan(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule5309 = ReplacementRule(pattern5309, replacement5309)
    pattern5310 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons338, cons137, cons89)
    def replacement5310(p, b, d, a, c, n, x, e):
        rubi.append(5310)
        return Dist(S(2)*c*(p + S(1))/(b*(n + S(1))), Int(x*(a + b*acot(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) - Simp((a + b*acot(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule5310 = ReplacementRule(pattern5310, replacement5310)
    pattern5311 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons1779, cons1740)
    def replacement5311(p, b, d, a, n, c, x, e):
        rubi.append(5311)
        return Dist(d**p/c, Subst(Int((a + b*x)**n*cos(x)**(-S(2)*p + S(-2)), x), x, ArcTan(c*x)), x)
    rule5311 = ReplacementRule(pattern5311, replacement5311)
    pattern5312 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons1779, cons1741)
    def replacement5312(p, b, d, a, n, c, x, e):
        rubi.append(5312)
        return Dist(d**(p + S(1)/2)*sqrt(c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*ArcTan(c*x))**n*(c**S(2)*x**S(2) + S(1))**p, x), x)
    rule5312 = ReplacementRule(pattern5312, replacement5312)
    pattern5313 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons1779, cons38)
    def replacement5313(p, b, d, a, n, c, x, e):
        rubi.append(5313)
        return -Dist(d**p/c, Subst(Int((a + b*x)**n*sin(x)**(-S(2)*p + S(-2)), x), x, acot(c*x)), x)
    rule5313 = ReplacementRule(pattern5313, replacement5313)
    pattern5314 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons1779, cons147)
    def replacement5314(p, b, d, a, n, c, x, e):
        rubi.append(5314)
        return -Dist(d**(p + S(1)/2)*x*sqrt((c**S(2)*x**S(2) + S(1))/(c**S(2)*x**S(2)))/sqrt(d + e*x**S(2)), Subst(Int((a + b*x)**n*sin(x)**(-S(2)*p + S(-2)), x), x, acot(c*x)), x)
    rule5314 = ReplacementRule(pattern5314, replacement5314)
    pattern5315 = Pattern(Integral(ArcTan(x_*WC('c', S(1)))/(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons7, cons27, cons48, cons1776)
    def replacement5315(d, c, x, e):
        rubi.append(5315)
        return Dist(I/S(2), Int(log(-I*c*x + S(1))/(d + e*x**S(2)), x), x) - Dist(I/S(2), Int(log(I*c*x + S(1))/(d + e*x**S(2)), x), x)
    rule5315 = ReplacementRule(pattern5315, replacement5315)
    pattern5316 = Pattern(Integral(acot(x_*WC('c', S(1)))/(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons7, cons27, cons48, cons1776)
    def replacement5316(d, c, x, e):
        rubi.append(5316)
        return Dist(I/S(2), Int(log(S(1) - I/(c*x))/(d + e*x**S(2)), x), x) - Dist(I/S(2), Int(log(S(1) + I/(c*x))/(d + e*x**S(2)), x), x)
    rule5316 = ReplacementRule(pattern5316, replacement5316)
    pattern5317 = Pattern(Integral((a_ + ArcTan(x_*WC('c', S(1)))*WC('b', S(1)))/(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement5317(b, d, c, a, x, e):
        rubi.append(5317)
        return Dist(a, Int(S(1)/(d + e*x**S(2)), x), x) + Dist(b, Int(ArcTan(c*x)/(d + e*x**S(2)), x), x)
    rule5317 = ReplacementRule(pattern5317, replacement5317)
    pattern5318 = Pattern(Integral((a_ + WC('b', S(1))*acot(x_*WC('c', S(1))))/(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement5318(b, d, c, a, x, e):
        rubi.append(5318)
        return Dist(a, Int(S(1)/(d + e*x**S(2)), x), x) + Dist(b, Int(acot(c*x)/(d + e*x**S(2)), x), x)
    rule5318 = ReplacementRule(pattern5318, replacement5318)
    def With5319(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(5319)
        return -Dist(b*c, Int(ExpandIntegrand(u/(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*ArcTan(c*x), u, x)
    pattern5319 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1780)
    rule5319 = ReplacementRule(pattern5319, With5319)
    def With5320(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(5320)
        return Dist(b*c, Int(ExpandIntegrand(u/(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acot(c*x), u, x)
    pattern5320 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1780)
    rule5320 = ReplacementRule(pattern5320, With5320)
    pattern5321 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons38, cons148)
    def replacement5321(p, b, d, a, n, c, x, e):
        rubi.append(5321)
        return Int(ExpandIntegrand((a + b*ArcTan(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule5321 = ReplacementRule(pattern5321, replacement5321)
    pattern5322 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons38, cons148)
    def replacement5322(p, b, d, a, n, c, x, e):
        rubi.append(5322)
        return Int(ExpandIntegrand((a + b*acot(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule5322 = ReplacementRule(pattern5322, replacement5322)
    pattern5323 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement5323(p, b, d, a, n, c, x, e):
        rubi.append(5323)
        return Int((a + b*ArcTan(c*x))**n*(d + e*x**S(2))**p, x)
    rule5323 = ReplacementRule(pattern5323, replacement5323)
    pattern5324 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement5324(p, b, d, a, n, c, x, e):
        rubi.append(5324)
        return Int((a + b*acot(c*x))**n*(d + e*x**S(2))**p, x)
    rule5324 = ReplacementRule(pattern5324, replacement5324)
    pattern5325 = Pattern(Integral(x_**m_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons93, cons88, cons166)
    def replacement5325(m, b, d, a, n, c, x, e):
        rubi.append(5325)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*ArcTan(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*ArcTan(c*x))**n/(d + e*x**S(2)), x), x)
    rule5325 = ReplacementRule(pattern5325, replacement5325)
    pattern5326 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons93, cons88, cons166)
    def replacement5326(m, b, d, a, n, c, x, e):
        rubi.append(5326)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*acot(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*acot(c*x))**n/(d + e*x**S(2)), x), x)
    rule5326 = ReplacementRule(pattern5326, replacement5326)
    pattern5327 = Pattern(Integral(x_**m_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons93, cons88, cons94)
    def replacement5327(m, b, d, a, n, c, x, e):
        rubi.append(5327)
        return Dist(S(1)/d, Int(x**m*(a + b*ArcTan(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*ArcTan(c*x))**n/(d + e*x**S(2)), x), x)
    rule5327 = ReplacementRule(pattern5327, replacement5327)
    pattern5328 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons93, cons88, cons94)
    def replacement5328(m, b, d, a, n, c, x, e):
        rubi.append(5328)
        return Dist(S(1)/d, Int(x**m*(a + b*acot(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*acot(c*x))**n/(d + e*x**S(2)), x), x)
    rule5328 = ReplacementRule(pattern5328, replacement5328)
    pattern5329 = Pattern(Integral(x_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148)
    def replacement5329(b, d, a, n, c, x, e):
        rubi.append(5329)
        return -Dist(S(1)/(c*d), Int((a + b*ArcTan(c*x))**n/(-c*x + I), x), x) - Simp(I*(a + b*ArcTan(c*x))**(n + S(1))/(b*e*(n + S(1))), x)
    rule5329 = ReplacementRule(pattern5329, replacement5329)
    pattern5330 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148)
    def replacement5330(b, d, a, n, c, x, e):
        rubi.append(5330)
        return -Dist(S(1)/(c*d), Int((a + b*acot(c*x))**n/(-c*x + I), x), x) + Simp(I*(a + b*acot(c*x))**(n + S(1))/(b*e*(n + S(1))), x)
    rule5330 = ReplacementRule(pattern5330, replacement5330)
    pattern5331 = Pattern(Integral(x_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons340, cons584)
    def replacement5331(b, d, a, c, n, x, e):
        rubi.append(5331)
        return -Dist(S(1)/(b*c*d*(n + S(1))), Int((a + b*ArcTan(c*x))**(n + S(1)), x), x) + Simp(x*(a + b*ArcTan(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule5331 = ReplacementRule(pattern5331, replacement5331)
    pattern5332 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons340, cons584)
    def replacement5332(b, d, a, c, n, x, e):
        rubi.append(5332)
        return Dist(S(1)/(b*c*d*(n + S(1))), Int((a + b*acot(c*x))**(n + S(1)), x), x) - Simp(x*(a + b*acot(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule5332 = ReplacementRule(pattern5332, replacement5332)
    pattern5333 = Pattern(Integral(x_**m_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons93, cons88, cons166)
    def replacement5333(m, b, d, a, n, c, x, e):
        rubi.append(5333)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*ArcTan(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*ArcTan(c*x))**n/(d + e*x**S(2)), x), x)
    rule5333 = ReplacementRule(pattern5333, replacement5333)
    pattern5334 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons93, cons88, cons166)
    def replacement5334(m, b, d, a, n, c, x, e):
        rubi.append(5334)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*acot(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*acot(c*x))**n/(d + e*x**S(2)), x), x)
    rule5334 = ReplacementRule(pattern5334, replacement5334)
    pattern5335 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(x_*(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement5335(b, d, a, n, c, x, e):
        rubi.append(5335)
        return Dist(I/d, Int((a + b*ArcTan(c*x))**n/(x*(c*x + I)), x), x) - Simp(I*(a + b*ArcTan(c*x))**(n + S(1))/(b*d*(n + S(1))), x)
    rule5335 = ReplacementRule(pattern5335, replacement5335)
    pattern5336 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement5336(b, d, a, n, c, x, e):
        rubi.append(5336)
        return Dist(I/d, Int((a + b*acot(c*x))**n/(x*(c*x + I)), x), x) + Simp(I*(a + b*acot(c*x))**(n + S(1))/(b*d*(n + S(1))), x)
    rule5336 = ReplacementRule(pattern5336, replacement5336)
    pattern5337 = Pattern(Integral(x_**m_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons93, cons88, cons94)
    def replacement5337(m, b, d, a, n, c, x, e):
        rubi.append(5337)
        return Dist(S(1)/d, Int(x**m*(a + b*ArcTan(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*ArcTan(c*x))**n/(d + e*x**S(2)), x), x)
    rule5337 = ReplacementRule(pattern5337, replacement5337)
    pattern5338 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons93, cons88, cons94)
    def replacement5338(m, b, d, a, n, c, x, e):
        rubi.append(5338)
        return Dist(S(1)/d, Int(x**m*(a + b*acot(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*acot(c*x))**n/(d + e*x**S(2)), x), x)
    rule5338 = ReplacementRule(pattern5338, replacement5338)
    pattern5339 = Pattern(Integral(x_**m_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons87, cons89)
    def replacement5339(m, b, d, a, c, n, x, e):
        rubi.append(5339)
        return -Dist(m/(b*c*d*(n + S(1))), Int(x**(m + S(-1))*(a + b*ArcTan(c*x))**(n + S(1)), x), x) + Simp(x**m*(a + b*ArcTan(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule5339 = ReplacementRule(pattern5339, replacement5339)
    pattern5340 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons87, cons89)
    def replacement5340(m, b, d, a, c, n, x, e):
        rubi.append(5340)
        return Dist(m/(b*c*d*(n + S(1))), Int(x**(m + S(-1))*(a + b*acot(c*x))**(n + S(1)), x), x) - Simp(x**m*(a + b*acot(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule5340 = ReplacementRule(pattern5340, replacement5340)
    pattern5341 = Pattern(Integral(x_**WC('m', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons17, cons1781)
    def replacement5341(m, b, d, a, c, x, e):
        rubi.append(5341)
        return Int(ExpandIntegrand(a + b*ArcTan(c*x), x**m/(d + e*x**S(2)), x), x)
    rule5341 = ReplacementRule(pattern5341, replacement5341)
    pattern5342 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons17, cons1781)
    def replacement5342(m, b, d, a, c, x, e):
        rubi.append(5342)
        return Int(ExpandIntegrand(a + b*acot(c*x), x**m/(d + e*x**S(2)), x), x)
    rule5342 = ReplacementRule(pattern5342, replacement5342)
    pattern5343 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1778, cons87, cons88, cons54)
    def replacement5343(p, b, d, a, n, c, x, e):
        rubi.append(5343)
        return -Dist(b*n/(S(2)*c*(p + S(1))), Int((a + b*ArcTan(c*x))**(n + S(-1))*(d + e*x**S(2))**p, x), x) + Simp((a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5343 = ReplacementRule(pattern5343, replacement5343)
    pattern5344 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1778, cons87, cons88, cons54)
    def replacement5344(p, b, d, a, n, c, x, e):
        rubi.append(5344)
        return Dist(b*n/(S(2)*c*(p + S(1))), Int((a + b*acot(c*x))**(n + S(-1))*(d + e*x**S(2))**p, x), x) + Simp((a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5344 = ReplacementRule(pattern5344, replacement5344)
    pattern5345 = Pattern(Integral(x_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons89, cons1442)
    def replacement5345(b, d, a, c, n, x, e):
        rubi.append(5345)
        return -Dist(S(4)/(b**S(2)*(n + S(1))*(n + S(2))), Int(x*(a + b*ArcTan(c*x))**(n + S(2))/(d + e*x**S(2))**S(2), x), x) - Simp((a + b*ArcTan(c*x))**(n + S(2))*(-c**S(2)*x**S(2) + S(1))/(b**S(2)*e*(d + e*x**S(2))*(n + S(1))*(n + S(2))), x) + Simp(x*(a + b*ArcTan(c*x))**(n + S(1))/(b*c*d*(d + e*x**S(2))*(n + S(1))), x)
    rule5345 = ReplacementRule(pattern5345, replacement5345)
    pattern5346 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons89, cons1442)
    def replacement5346(b, d, a, c, n, x, e):
        rubi.append(5346)
        return -Dist(S(4)/(b**S(2)*(n + S(1))*(n + S(2))), Int(x*(a + b*acot(c*x))**(n + S(2))/(d + e*x**S(2))**S(2), x), x) - Simp((a + b*acot(c*x))**(n + S(2))*(-c**S(2)*x**S(2) + S(1))/(b**S(2)*e*(d + e*x**S(2))*(n + S(1))*(n + S(2))), x) - Simp(x*(a + b*acot(c*x))**(n + S(1))/(b*c*d*(d + e*x**S(2))*(n + S(1))), x)
    rule5346 = ReplacementRule(pattern5346, replacement5346)
    pattern5347 = Pattern(Integral(x_**S(2)*(d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons13, cons137, cons1782)
    def replacement5347(p, b, d, a, c, x, e):
        rubi.append(5347)
        return -Dist(S(1)/(S(2)*c**S(2)*d*(p + S(1))), Int((a + b*ArcTan(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(b*(d + e*x**S(2))**(p + S(1))/(S(4)*c**S(3)*d*(p + S(1))**S(2)), x) + Simp(x*(a + b*ArcTan(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*c**S(2)*d*(p + S(1))), x)
    rule5347 = ReplacementRule(pattern5347, replacement5347)
    pattern5348 = Pattern(Integral(x_**S(2)*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons13, cons137, cons1782)
    def replacement5348(p, b, d, a, c, x, e):
        rubi.append(5348)
        return -Dist(S(1)/(S(2)*c**S(2)*d*(p + S(1))), Int((a + b*acot(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) + Simp(b*(d + e*x**S(2))**(p + S(1))/(S(4)*c**S(3)*d*(p + S(1))**S(2)), x) + Simp(x*(a + b*acot(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*c**S(2)*d*(p + S(1))), x)
    rule5348 = ReplacementRule(pattern5348, replacement5348)
    pattern5349 = Pattern(Integral(x_**S(2)*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement5349(b, d, a, n, c, x, e):
        rubi.append(5349)
        return Dist(b*n/(S(2)*c), Int(x*(a + b*ArcTan(c*x))**(n + S(-1))/(d + e*x**S(2))**S(2), x), x) + Simp((a + b*ArcTan(c*x))**(n + S(1))/(S(2)*b*c**S(3)*d**S(2)*(n + S(1))), x) - Simp(x*(a + b*ArcTan(c*x))**n/(S(2)*c**S(2)*d*(d + e*x**S(2))), x)
    rule5349 = ReplacementRule(pattern5349, replacement5349)
    pattern5350 = Pattern(Integral(x_**S(2)*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement5350(b, d, a, n, c, x, e):
        rubi.append(5350)
        return -Dist(b*n/(S(2)*c), Int(x*(a + b*acot(c*x))**(n + S(-1))/(d + e*x**S(2))**S(2), x), x) - Simp((a + b*acot(c*x))**(n + S(1))/(S(2)*b*c**S(3)*d**S(2)*(n + S(1))), x) - Simp(x*(a + b*acot(c*x))**n/(S(2)*c**S(2)*d*(d + e*x**S(2))), x)
    rule5350 = ReplacementRule(pattern5350, replacement5350)
    pattern5351 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons240, cons13, cons137)
    def replacement5351(p, m, b, d, a, c, x, e):
        rubi.append(5351)
        return Dist((m + S(-1))/(c**S(2)*d*m), Int(x**(m + S(-2))*(a + b*ArcTan(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) + Simp(b*x**m*(d + e*x**S(2))**(p + S(1))/(c*d*m**S(2)), x) - Simp(x**(m + S(-1))*(a + b*ArcTan(c*x))*(d + e*x**S(2))**(p + S(1))/(c**S(2)*d*m), x)
    rule5351 = ReplacementRule(pattern5351, replacement5351)
    pattern5352 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons240, cons13, cons137)
    def replacement5352(p, m, b, d, a, c, x, e):
        rubi.append(5352)
        return Dist((m + S(-1))/(c**S(2)*d*m), Int(x**(m + S(-2))*(a + b*acot(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(b*x**m*(d + e*x**S(2))**(p + S(1))/(c*d*m**S(2)), x) - Simp(x**(m + S(-1))*(a + b*acot(c*x))*(d + e*x**S(2))**(p + S(1))/(c**S(2)*d*m), x)
    rule5352 = ReplacementRule(pattern5352, replacement5352)
    pattern5353 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons240, cons338, cons137, cons165)
    def replacement5353(p, m, b, d, a, c, n, x, e):
        rubi.append(5353)
        return -Dist(b**S(2)*n*(n + S(-1))/m**S(2), Int(x**m*(a + b*ArcTan(c*x))**(n + S(-2))*(d + e*x**S(2))**p, x), x) + Dist((m + S(-1))/(c**S(2)*d*m), Int(x**(m + S(-2))*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(x**(m + S(-1))*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(1))/(c**S(2)*d*m), x) + Simp(b*n*x**m*(a + b*ArcTan(c*x))**(n + S(-1))*(d + e*x**S(2))**(p + S(1))/(c*d*m**S(2)), x)
    rule5353 = ReplacementRule(pattern5353, replacement5353)
    pattern5354 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons240, cons338, cons137, cons165)
    def replacement5354(p, m, b, d, a, c, n, x, e):
        rubi.append(5354)
        return -Dist(b**S(2)*n*(n + S(-1))/m**S(2), Int(x**m*(a + b*acot(c*x))**(n + S(-2))*(d + e*x**S(2))**p, x), x) + Dist((m + S(-1))/(c**S(2)*d*m), Int(x**(m + S(-2))*(a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(x**(m + S(-1))*(a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(1))/(c**S(2)*d*m), x) - Simp(b*n*x**m*(a + b*acot(c*x))**(n + S(-1))*(d + e*x**S(2))**(p + S(1))/(c*d*m**S(2)), x)
    rule5354 = ReplacementRule(pattern5354, replacement5354)
    pattern5355 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1778, cons240, cons87, cons89)
    def replacement5355(p, m, b, d, a, c, n, x, e):
        rubi.append(5355)
        return -Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*ArcTan(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Simp(x**m*(a + b*ArcTan(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule5355 = ReplacementRule(pattern5355, replacement5355)
    pattern5356 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1778, cons240, cons87, cons89)
    def replacement5356(p, m, b, d, a, c, n, x, e):
        rubi.append(5356)
        return Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*acot(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) - Simp(x**m*(a + b*acot(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule5356 = ReplacementRule(pattern5356, replacement5356)
    pattern5357 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1778, cons242, cons87, cons88, cons66)
    def replacement5357(p, m, b, d, a, n, c, x, e):
        rubi.append(5357)
        return -Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*ArcTan(c*x))**(n + S(-1))*(d + e*x**S(2))**p, x), x) + Simp(x**(m + S(1))*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*(m + S(1))), x)
    rule5357 = ReplacementRule(pattern5357, replacement5357)
    pattern5358 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1778, cons242, cons87, cons88, cons66)
    def replacement5358(p, m, b, d, a, n, c, x, e):
        rubi.append(5358)
        return Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*acot(c*x))**(n + S(-1))*(d + e*x**S(2))**p, x), x) + Simp(x**(m + S(1))*(a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*(m + S(1))), x)
    rule5358 = ReplacementRule(pattern5358, replacement5358)
    pattern5359 = Pattern(Integral(x_**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons241)
    def replacement5359(m, b, d, a, c, x, e):
        rubi.append(5359)
        return Dist(d/(m + S(2)), Int(x**m*(a + b*ArcTan(c*x))/sqrt(d + e*x**S(2)), x), x) - Dist(b*c*d/(m + S(2)), Int(x**(m + S(1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*ArcTan(c*x))*sqrt(d + e*x**S(2))/(m + S(2)), x)
    rule5359 = ReplacementRule(pattern5359, replacement5359)
    pattern5360 = Pattern(Integral(x_**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons241)
    def replacement5360(m, b, d, a, c, x, e):
        rubi.append(5360)
        return Dist(d/(m + S(2)), Int(x**m*(a + b*acot(c*x))/sqrt(d + e*x**S(2)), x), x) + Dist(b*c*d/(m + S(2)), Int(x**(m + S(1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*acot(c*x))*sqrt(d + e*x**S(2))/(m + S(2)), x)
    rule5360 = ReplacementRule(pattern5360, replacement5360)
    pattern5361 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons148, cons38, cons146)
    def replacement5361(p, m, b, d, a, n, c, x, e):
        rubi.append(5361)
        return Int(ExpandIntegrand(x**m*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule5361 = ReplacementRule(pattern5361, replacement5361)
    pattern5362 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons148, cons38, cons146)
    def replacement5362(p, m, b, d, a, n, c, x, e):
        rubi.append(5362)
        return Int(ExpandIntegrand(x**m*(a + b*acot(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule5362 = ReplacementRule(pattern5362, replacement5362)
    pattern5363 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons13, cons163, cons148, cons1783)
    def replacement5363(p, m, b, d, a, n, c, x, e):
        rubi.append(5363)
        return Dist(d, Int(x**m*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) + Dist(c**S(2)*d, Int(x**(m + S(2))*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x)
    rule5363 = ReplacementRule(pattern5363, replacement5363)
    pattern5364 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1778, cons13, cons163, cons148, cons1783)
    def replacement5364(p, m, b, d, a, n, c, x, e):
        rubi.append(5364)
        return Dist(d, Int(x**m*(a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) + Dist(c**S(2)*d, Int(x**(m + S(2))*(a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x)
    rule5364 = ReplacementRule(pattern5364, replacement5364)
    pattern5365 = Pattern(Integral(x_**m_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons93, cons88, cons166)
    def replacement5365(m, b, d, a, n, c, x, e):
        rubi.append(5365)
        return -Dist((m + S(-1))/(c**S(2)*m), Int(x**(m + S(-2))*(a + b*ArcTan(c*x))**n/sqrt(d + e*x**S(2)), x), x) - Dist(b*n/(c*m), Int(x**(m + S(-1))*(a + b*ArcTan(c*x))**(n + S(-1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(-1))*(a + b*ArcTan(c*x))**n*sqrt(d + e*x**S(2))/(c**S(2)*d*m), x)
    rule5365 = ReplacementRule(pattern5365, replacement5365)
    pattern5366 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons93, cons88, cons166)
    def replacement5366(m, b, d, a, n, c, x, e):
        rubi.append(5366)
        return -Dist((m + S(-1))/(c**S(2)*m), Int(x**(m + S(-2))*(a + b*acot(c*x))**n/sqrt(d + e*x**S(2)), x), x) + Dist(b*n/(c*m), Int(x**(m + S(-1))*(a + b*acot(c*x))**(n + S(-1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(-1))*(a + b*acot(c*x))**n*sqrt(d + e*x**S(2))/(c**S(2)*d*m), x)
    rule5366 = ReplacementRule(pattern5366, replacement5366)
    pattern5367 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons268)
    def replacement5367(b, d, a, c, x, e):
        rubi.append(5367)
        return Simp(-S(2)*(a + b*ArcTan(c*x))*atanh(sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/sqrt(d), x) + Simp(I*b*PolyLog(S(2), -sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/sqrt(d), x) - Simp(I*b*PolyLog(S(2), sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/sqrt(d), x)
    rule5367 = ReplacementRule(pattern5367, replacement5367)
    pattern5368 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons268)
    def replacement5368(b, d, a, c, x, e):
        rubi.append(5368)
        return Simp(-S(2)*(a + b*acot(c*x))*atanh(sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/sqrt(d), x) - Simp(I*b*PolyLog(S(2), -sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/sqrt(d), x) + Simp(I*b*PolyLog(S(2), sqrt(I*c*x + S(1))/sqrt(-I*c*x + S(1)))/sqrt(d), x)
    rule5368 = ReplacementRule(pattern5368, replacement5368)
    pattern5369 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148, cons268)
    def replacement5369(b, d, a, c, n, x, e):
        rubi.append(5369)
        return Dist(S(1)/sqrt(d), Subst(Int((a + b*x)**n/sin(x), x), x, ArcTan(c*x)), x)
    rule5369 = ReplacementRule(pattern5369, replacement5369)
    pattern5370 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**n_/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148, cons268)
    def replacement5370(b, d, a, c, n, x, e):
        rubi.append(5370)
        return -Dist(c*x*sqrt(S(1) + S(1)/(c**S(2)*x**S(2)))/sqrt(d + e*x**S(2)), Subst(Int((a + b*x)**n/cos(x), x), x, acot(c*x)), x)
    rule5370 = ReplacementRule(pattern5370, replacement5370)
    pattern5371 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148, cons1738)
    def replacement5371(b, d, a, n, c, x, e):
        rubi.append(5371)
        return Dist(sqrt(c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*ArcTan(c*x))**n/(x*sqrt(c**S(2)*x**S(2) + S(1))), x), x)
    rule5371 = ReplacementRule(pattern5371, replacement5371)
    pattern5372 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148, cons1738)
    def replacement5372(b, d, a, n, c, x, e):
        rubi.append(5372)
        return Dist(sqrt(c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*acot(c*x))**n/(x*sqrt(c**S(2)*x**S(2) + S(1))), x), x)
    rule5372 = ReplacementRule(pattern5372, replacement5372)
    pattern5373 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/(x_**S(2)*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement5373(b, d, a, n, c, x, e):
        rubi.append(5373)
        return Dist(b*c*n, Int((a + b*ArcTan(c*x))**(n + S(-1))/(x*sqrt(d + e*x**S(2))), x), x) - Simp((a + b*ArcTan(c*x))**n*sqrt(d + e*x**S(2))/(d*x), x)
    rule5373 = ReplacementRule(pattern5373, replacement5373)
    pattern5374 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(x_**S(2)*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement5374(b, d, a, n, c, x, e):
        rubi.append(5374)
        return -Dist(b*c*n, Int((a + b*acot(c*x))**(n + S(-1))/(x*sqrt(d + e*x**S(2))), x), x) - Simp((a + b*acot(c*x))**n*sqrt(d + e*x**S(2))/(d*x), x)
    rule5374 = ReplacementRule(pattern5374, replacement5374)
    pattern5375 = Pattern(Integral(x_**m_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons93, cons88, cons94, cons1510)
    def replacement5375(m, b, d, a, n, c, x, e):
        rubi.append(5375)
        return -Dist(c**S(2)*(m + S(2))/(m + S(1)), Int(x**(m + S(2))*(a + b*ArcTan(c*x))**n/sqrt(d + e*x**S(2)), x), x) - Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*ArcTan(c*x))**(n + S(-1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*ArcTan(c*x))**n*sqrt(d + e*x**S(2))/(d*(m + S(1))), x)
    rule5375 = ReplacementRule(pattern5375, replacement5375)
    pattern5376 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons93, cons88, cons94, cons1510)
    def replacement5376(m, b, d, a, n, c, x, e):
        rubi.append(5376)
        return -Dist(c**S(2)*(m + S(2))/(m + S(1)), Int(x**(m + S(2))*(a + b*acot(c*x))**n/sqrt(d + e*x**S(2)), x), x) + Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*acot(c*x))**(n + S(-1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*acot(c*x))**n*sqrt(d + e*x**S(2))/(d*(m + S(1))), x)
    rule5376 = ReplacementRule(pattern5376, replacement5376)
    pattern5377 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons1784, cons137, cons166, cons1152)
    def replacement5377(p, m, b, d, a, n, c, x, e):
        rubi.append(5377)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule5377 = ReplacementRule(pattern5377, replacement5377)
    pattern5378 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons1784, cons137, cons166, cons1152)
    def replacement5378(p, m, b, d, a, n, c, x, e):
        rubi.append(5378)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*acot(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule5378 = ReplacementRule(pattern5378, replacement5378)
    pattern5379 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons1784, cons137, cons267, cons1152)
    def replacement5379(p, m, b, d, a, n, c, x, e):
        rubi.append(5379)
        return Dist(S(1)/d, Int(x**m*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule5379 = ReplacementRule(pattern5379, replacement5379)
    pattern5380 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons1784, cons137, cons267, cons1152)
    def replacement5380(p, m, b, d, a, n, c, x, e):
        rubi.append(5380)
        return Dist(S(1)/d, Int(x**m*(a + b*acot(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*acot(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule5380 = ReplacementRule(pattern5380, replacement5380)
    pattern5381 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons162, cons137, cons89, cons319)
    def replacement5381(p, m, b, d, a, n, c, x, e):
        rubi.append(5381)
        return -Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*ArcTan(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) - Dist(c*(m + S(2)*p + S(2))/(b*(n + S(1))), Int(x**(m + S(1))*(a + b*ArcTan(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Simp(x**m*(a + b*ArcTan(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule5381 = ReplacementRule(pattern5381, replacement5381)
    pattern5382 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons162, cons137, cons89, cons319)
    def replacement5382(p, m, b, d, a, n, c, x, e):
        rubi.append(5382)
        return Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*acot(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Dist(c*(m + S(2)*p + S(2))/(b*(n + S(1))), Int(x**(m + S(1))*(a + b*acot(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) - Simp(x**m*(a + b*acot(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule5382 = ReplacementRule(pattern5382, replacement5382)
    pattern5383 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons62, cons1785, cons1740)
    def replacement5383(p, m, b, d, a, n, c, x, e):
        rubi.append(5383)
        return Dist(c**(-m + S(-1))*d**p, Subst(Int((a + b*x)**n*sin(x)**m*cos(x)**(-m - S(2)*p + S(-2)), x), x, ArcTan(c*x)), x)
    rule5383 = ReplacementRule(pattern5383, replacement5383)
    pattern5384 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons62, cons1785, cons1741)
    def replacement5384(p, m, b, d, a, n, c, x, e):
        rubi.append(5384)
        return Dist(d**(p + S(1)/2)*sqrt(c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int(x**m*(a + b*ArcTan(c*x))**n*(c**S(2)*x**S(2) + S(1))**p, x), x)
    rule5384 = ReplacementRule(pattern5384, replacement5384)
    pattern5385 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons62, cons1785, cons38)
    def replacement5385(p, m, b, d, a, n, c, x, e):
        rubi.append(5385)
        return -Dist(c**(-m + S(-1))*d**p, Subst(Int((a + b*x)**n*sin(x)**(-m - S(2)*p + S(-2))*cos(x)**m, x), x, acot(c*x)), x)
    rule5385 = ReplacementRule(pattern5385, replacement5385)
    pattern5386 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons62, cons1785, cons147)
    def replacement5386(p, m, b, d, a, n, c, x, e):
        rubi.append(5386)
        return -Dist(c**(-m)*d**(p + S(1)/2)*x*sqrt((c**S(2)*x**S(2) + S(1))/(c**S(2)*x**S(2)))/sqrt(d + e*x**S(2)), Subst(Int((a + b*x)**n*sin(x)**(-m - S(2)*p + S(-2))*cos(x)**m, x), x, acot(c*x)), x)
    rule5386 = ReplacementRule(pattern5386, replacement5386)
    pattern5387 = Pattern(Integral(x_*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement5387(p, b, d, a, c, x, e):
        rubi.append(5387)
        return -Dist(b*c/(S(2)*e*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*ArcTan(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5387 = ReplacementRule(pattern5387, replacement5387)
    pattern5388 = Pattern(Integral(x_*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement5388(p, b, d, a, c, x, e):
        rubi.append(5388)
        return Dist(b*c/(S(2)*e*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*acot(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5388 = ReplacementRule(pattern5388, replacement5388)
    def With5389(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(d + e*x**S(2))**p, x)
        rubi.append(5389)
        return -Dist(b*c, Int(SimplifyIntegrand(u/(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*ArcTan(c*x), u, x)
    pattern5389 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1786)
    rule5389 = ReplacementRule(pattern5389, With5389)
    def With5390(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(d + e*x**S(2))**p, x)
        rubi.append(5390)
        return Dist(b*c, Int(SimplifyIntegrand(u/(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acot(c*x), u, x)
    pattern5390 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1786)
    rule5390 = ReplacementRule(pattern5390, With5390)
    pattern5391 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons1787)
    def replacement5391(p, m, b, d, a, n, c, x, e):
        rubi.append(5391)
        return Int(ExpandIntegrand((a + b*ArcTan(c*x))**n, x**m*(d + e*x**S(2))**p, x), x)
    rule5391 = ReplacementRule(pattern5391, replacement5391)
    pattern5392 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons1787)
    def replacement5392(p, m, b, d, a, n, c, x, e):
        rubi.append(5392)
        return Int(ExpandIntegrand((a + b*acot(c*x))**n, x**m*(d + e*x**S(2))**p, x), x)
    rule5392 = ReplacementRule(pattern5392, replacement5392)
    pattern5393 = Pattern(Integral(x_**WC('m', S(1))*(a_ + ArcTan(x_*WC('c', S(1)))*WC('b', S(1)))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1788)
    def replacement5393(p, m, b, d, c, a, x, e):
        rubi.append(5393)
        return Dist(a, Int(x**m*(d + e*x**S(2))**p, x), x) + Dist(b, Int(x**m*(d + e*x**S(2))**p*ArcTan(c*x), x), x)
    rule5393 = ReplacementRule(pattern5393, replacement5393)
    pattern5394 = Pattern(Integral(x_**WC('m', S(1))*(a_ + WC('b', S(1))*acot(x_*WC('c', S(1))))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1788)
    def replacement5394(p, m, b, d, c, a, x, e):
        rubi.append(5394)
        return Dist(a, Int(x**m*(d + e*x**S(2))**p, x), x) + Dist(b, Int(x**m*(d + e*x**S(2))**p*acot(c*x), x), x)
    rule5394 = ReplacementRule(pattern5394, replacement5394)
    pattern5395 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement5395(p, m, b, d, a, n, c, x, e):
        rubi.append(5395)
        return Int(x**m*(a + b*ArcTan(c*x))**n*(d + e*x**S(2))**p, x)
    rule5395 = ReplacementRule(pattern5395, replacement5395)
    pattern5396 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement5396(p, m, b, d, a, n, c, x, e):
        rubi.append(5396)
        return Int(x**m*(a + b*acot(c*x))**n*(d + e*x**S(2))**p, x)
    rule5396 = ReplacementRule(pattern5396, replacement5396)
    pattern5397 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))*atanh(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88, cons1789)
    def replacement5397(u, b, d, a, n, c, x, e):
        rubi.append(5397)
        return -Dist(S(1)/2, Int((a + b*ArcTan(c*x))**n*log(-u + S(1))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int((a + b*ArcTan(c*x))**n*log(u + S(1))/(d + e*x**S(2)), x), x)
    rule5397 = ReplacementRule(pattern5397, replacement5397)
    pattern5398 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))*acoth(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88, cons1789)
    def replacement5398(u, b, d, a, n, c, x, e):
        rubi.append(5398)
        return -Dist(S(1)/2, Int((a + b*acot(c*x))**n*log(SimplifyIntegrand(S(1) - S(1)/u, x))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int((a + b*acot(c*x))**n*log(SimplifyIntegrand(S(1) + S(1)/u, x))/(d + e*x**S(2)), x), x)
    rule5398 = ReplacementRule(pattern5398, replacement5398)
    pattern5399 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))*atanh(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88, cons1790)
    def replacement5399(u, b, d, a, n, c, x, e):
        rubi.append(5399)
        return -Dist(S(1)/2, Int((a + b*ArcTan(c*x))**n*log(-u + S(1))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int((a + b*ArcTan(c*x))**n*log(u + S(1))/(d + e*x**S(2)), x), x)
    rule5399 = ReplacementRule(pattern5399, replacement5399)
    pattern5400 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))*acoth(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88, cons1790)
    def replacement5400(u, b, d, a, n, c, x, e):
        rubi.append(5400)
        return -Dist(S(1)/2, Int((a + b*acot(c*x))**n*log(SimplifyIntegrand(S(1) - S(1)/u, x))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int((a + b*acot(c*x))**n*log(SimplifyIntegrand(S(1) + S(1)/u, x))/(d + e*x**S(2)), x), x)
    rule5400 = ReplacementRule(pattern5400, replacement5400)
    pattern5401 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))*log(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88, cons1791)
    def replacement5401(u, b, d, a, n, c, x, e):
        rubi.append(5401)
        return -Dist(I*b*n/S(2), Int((a + b*ArcTan(c*x))**(n + S(-1))*PolyLog(S(2), Together(-u + S(1)))/(d + e*x**S(2)), x), x) + Simp(I*(a + b*ArcTan(c*x))**n*PolyLog(S(2), Together(-u + S(1)))/(S(2)*c*d), x)
    rule5401 = ReplacementRule(pattern5401, replacement5401)
    pattern5402 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))*log(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88, cons1791)
    def replacement5402(u, b, d, a, n, c, x, e):
        rubi.append(5402)
        return Dist(I*b*n/S(2), Int((a + b*acot(c*x))**(n + S(-1))*PolyLog(S(2), Together(-u + S(1)))/(d + e*x**S(2)), x), x) + Simp(I*(a + b*acot(c*x))**n*PolyLog(S(2), Together(-u + S(1)))/(S(2)*c*d), x)
    rule5402 = ReplacementRule(pattern5402, replacement5402)
    pattern5403 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))*log(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88, cons1792)
    def replacement5403(u, b, d, a, n, c, x, e):
        rubi.append(5403)
        return Dist(I*b*n/S(2), Int((a + b*ArcTan(c*x))**(n + S(-1))*PolyLog(S(2), Together(-u + S(1)))/(d + e*x**S(2)), x), x) - Simp(I*(a + b*ArcTan(c*x))**n*PolyLog(S(2), Together(-u + S(1)))/(S(2)*c*d), x)
    rule5403 = ReplacementRule(pattern5403, replacement5403)
    pattern5404 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))*log(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88, cons1792)
    def replacement5404(u, b, d, a, n, c, x, e):
        rubi.append(5404)
        return -Dist(I*b*n/S(2), Int((a + b*acot(c*x))**(n + S(-1))*PolyLog(S(2), Together(-u + S(1)))/(d + e*x**S(2)), x), x) - Simp(I*(a + b*acot(c*x))**n*PolyLog(S(2), Together(-u + S(1)))/(S(2)*c*d), x)
    rule5404 = ReplacementRule(pattern5404, replacement5404)
    pattern5405 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))*PolyLog(p_, u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1778, cons87, cons88, cons1789)
    def replacement5405(p, u, b, d, a, n, c, x, e):
        rubi.append(5405)
        return Dist(I*b*n/S(2), Int((a + b*ArcTan(c*x))**(n + S(-1))*PolyLog(p + S(1), u)/(d + e*x**S(2)), x), x) - Simp(I*(a + b*ArcTan(c*x))**n*PolyLog(p + S(1), u)/(S(2)*c*d), x)
    rule5405 = ReplacementRule(pattern5405, replacement5405)
    pattern5406 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))*PolyLog(p_, u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1778, cons87, cons88, cons1789)
    def replacement5406(p, u, b, d, a, n, c, x, e):
        rubi.append(5406)
        return -Dist(I*b*n/S(2), Int((a + b*acot(c*x))**(n + S(-1))*PolyLog(p + S(1), u)/(d + e*x**S(2)), x), x) - Simp(I*(a + b*acot(c*x))**n*PolyLog(p + S(1), u)/(S(2)*c*d), x)
    rule5406 = ReplacementRule(pattern5406, replacement5406)
    pattern5407 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))*PolyLog(p_, u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1778, cons87, cons88, cons1790)
    def replacement5407(p, u, b, d, a, n, c, x, e):
        rubi.append(5407)
        return -Dist(I*b*n/S(2), Int((a + b*ArcTan(c*x))**(n + S(-1))*PolyLog(p + S(1), u)/(d + e*x**S(2)), x), x) + Simp(I*(a + b*ArcTan(c*x))**n*PolyLog(p + S(1), u)/(S(2)*c*d), x)
    rule5407 = ReplacementRule(pattern5407, replacement5407)
    pattern5408 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))*PolyLog(p_, u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1778, cons87, cons88, cons1790)
    def replacement5408(p, u, b, d, a, n, c, x, e):
        rubi.append(5408)
        return Dist(I*b*n/S(2), Int((a + b*acot(c*x))**(n + S(-1))*PolyLog(p + S(1), u)/(d + e*x**S(2)), x), x) + Simp(I*(a + b*acot(c*x))**n*PolyLog(p + S(1), u)/(S(2)*c*d), x)
    rule5408 = ReplacementRule(pattern5408, replacement5408)
    pattern5409 = Pattern(Integral(S(1)/((d_ + x_**S(2)*WC('e', S(1)))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))), x_), cons2, cons3, cons7, cons27, cons48, cons1778)
    def replacement5409(b, d, a, c, x, e):
        rubi.append(5409)
        return Simp((log(a + b*ArcTan(c*x)) - log(a + b*acot(c*x)))/(b*c*d*(S(2)*a + b*ArcTan(c*x) + b*acot(c*x))), x)
    rule5409 = ReplacementRule(pattern5409, replacement5409)
    pattern5410 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('m', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons150, cons1793)
    def replacement5410(m, b, d, a, n, c, x, e):
        rubi.append(5410)
        return Dist(n/(m + S(1)), Int((a + b*ArcTan(c*x))**(n + S(-1))*(a + b*acot(c*x))**(m + S(1))/(d + e*x**S(2)), x), x) - Simp((a + b*ArcTan(c*x))**n*(a + b*acot(c*x))**(m + S(1))/(b*c*d*(m + S(1))), x)
    rule5410 = ReplacementRule(pattern5410, replacement5410)
    pattern5411 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons150, cons1794)
    def replacement5411(m, b, d, a, n, c, x, e):
        rubi.append(5411)
        return Dist(n/(m + S(1)), Int((a + b*ArcTan(c*x))**(m + S(1))*(a + b*acot(c*x))**(n + S(-1))/(d + e*x**S(2)), x), x) + Simp((a + b*ArcTan(c*x))**(m + S(1))*(a + b*acot(c*x))**n/(b*c*d*(m + S(1))), x)
    rule5411 = ReplacementRule(pattern5411, replacement5411)
    pattern5412 = Pattern(Integral(ArcTan(x_*WC('a', S(1)))/(c_ + x_**WC('n', S(1))*WC('d', S(1))), x_), cons2, cons7, cons27, cons85, cons1795)
    def replacement5412(d, a, n, c, x):
        rubi.append(5412)
        return Dist(I/S(2), Int(log(-I*a*x + S(1))/(c + d*x**n), x), x) - Dist(I/S(2), Int(log(I*a*x + S(1))/(c + d*x**n), x), x)
    rule5412 = ReplacementRule(pattern5412, replacement5412)
    pattern5413 = Pattern(Integral(acot(x_*WC('a', S(1)))/(c_ + x_**WC('n', S(1))*WC('d', S(1))), x_), cons2, cons7, cons27, cons85, cons1795)
    def replacement5413(d, a, n, c, x):
        rubi.append(5413)
        return Dist(I/S(2), Int(log(S(1) - I/(a*x))/(c + d*x**n), x), x) - Dist(I/S(2), Int(log(S(1) + I/(a*x))/(c + d*x**n), x), x)
    rule5413 = ReplacementRule(pattern5413, replacement5413)
    pattern5414 = Pattern(Integral((ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1796)
    def replacement5414(f, b, g, d, a, c, x, e):
        rubi.append(5414)
        return -Dist(b*c, Int(x*(d + e*log(f + g*x**S(2)))/(c**S(2)*x**S(2) + S(1)), x), x) - Dist(S(2)*e*g, Int(x**S(2)*(a + b*ArcTan(c*x))/(f + g*x**S(2)), x), x) + Simp(x*(a + b*ArcTan(c*x))*(d + e*log(f + g*x**S(2))), x)
    rule5414 = ReplacementRule(pattern5414, replacement5414)
    pattern5415 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1796)
    def replacement5415(f, b, g, d, a, c, x, e):
        rubi.append(5415)
        return Dist(b*c, Int(x*(d + e*log(f + g*x**S(2)))/(c**S(2)*x**S(2) + S(1)), x), x) - Dist(S(2)*e*g, Int(x**S(2)*(a + b*acot(c*x))/(f + g*x**S(2)), x), x) + Simp(x*(a + b*acot(c*x))*(d + e*log(f + g*x**S(2))), x)
    rule5415 = ReplacementRule(pattern5415, replacement5415)
    pattern5416 = Pattern(Integral(x_**WC('m', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons601)
    def replacement5416(m, f, b, g, d, a, c, x, e):
        rubi.append(5416)
        return -Dist(b*c/(m + S(1)), Int(x**(m + S(1))*(d + e*log(f + g*x**S(2)))/(c**S(2)*x**S(2) + S(1)), x), x) - Dist(S(2)*e*g/(m + S(1)), Int(x**(m + S(2))*(a + b*ArcTan(c*x))/(f + g*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*ArcTan(c*x))*(d + e*log(f + g*x**S(2)))/(m + S(1)), x)
    rule5416 = ReplacementRule(pattern5416, replacement5416)
    pattern5417 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons601)
    def replacement5417(m, f, b, g, d, a, c, x, e):
        rubi.append(5417)
        return Dist(b*c/(m + S(1)), Int(x**(m + S(1))*(d + e*log(f + g*x**S(2)))/(c**S(2)*x**S(2) + S(1)), x), x) - Dist(S(2)*e*g/(m + S(1)), Int(x**(m + S(2))*(a + b*acot(c*x))/(f + g*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*acot(c*x))*(d + e*log(f + g*x**S(2)))/(m + S(1)), x)
    rule5417 = ReplacementRule(pattern5417, replacement5417)
    def With5418(m, f, b, g, d, a, c, x, e):
        u = IntHide(x**m*(d + e*log(f + g*x**S(2))), x)
        rubi.append(5418)
        return -Dist(b*c, Int(ExpandIntegrand(u/(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*ArcTan(c*x), u, x)
    pattern5418 = Pattern(Integral(x_**WC('m', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1797)
    rule5418 = ReplacementRule(pattern5418, With5418)
    def With5419(m, f, b, g, d, a, c, x, e):
        u = IntHide(x**m*(d + e*log(f + g*x**S(2))), x)
        rubi.append(5419)
        return Dist(b*c, Int(ExpandIntegrand(u/(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acot(c*x), u, x)
    pattern5419 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1797)
    rule5419 = ReplacementRule(pattern5419, With5419)
    def With5420(m, f, b, g, d, a, c, x, e):
        u = IntHide(x**m*(a + b*ArcTan(c*x)), x)
        rubi.append(5420)
        return -Dist(S(2)*e*g, Int(ExpandIntegrand(u*x/(f + g*x**S(2)), x), x), x) + Dist(d + e*log(f + g*x**S(2)), u, x)
    pattern5420 = Pattern(Integral(x_**WC('m', S(1))*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons17, cons261)
    rule5420 = ReplacementRule(pattern5420, With5420)
    def With5421(m, f, b, g, d, a, c, x, e):
        u = IntHide(x**m*(a + b*acot(c*x)), x)
        rubi.append(5421)
        return -Dist(S(2)*e*g, Int(ExpandIntegrand(u*x/(f + g*x**S(2)), x), x), x) + Dist(d + e*log(f + g*x**S(2)), u, x)
    pattern5421 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons17, cons261)
    rule5421 = ReplacementRule(pattern5421, With5421)
    pattern5422 = Pattern(Integral(x_*(ArcTan(x_*WC('c', S(1)))*WC('b', S(1)) + WC('a', S(0)))**S(2)*(WC('d', S(0)) + WC('e', S(1))*log(f_ + x_**S(2)*WC('g', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1798)
    def replacement5422(g, b, f, d, a, c, x, e):
        rubi.append(5422)
        return -Dist(b/c, Int((a + b*ArcTan(c*x))*(d + e*log(f + g*x**S(2))), x), x) + Dist(b*c*e, Int(x**S(2)*(a + b*ArcTan(c*x))/(c**S(2)*x**S(2) + S(1)), x), x) - Simp(e*x**S(2)*(a + b*ArcTan(c*x))**S(2)/S(2), x) + Simp((a + b*ArcTan(c*x))**S(2)*(d + e*log(f + g*x**S(2)))*(f + g*x**S(2))/(S(2)*g), x)
    rule5422 = ReplacementRule(pattern5422, replacement5422)
    pattern5423 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acot(x_*WC('c', S(1))))**S(2)*(WC('d', S(0)) + WC('e', S(1))*log(f_ + x_**S(2)*WC('g', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1798)
    def replacement5423(g, b, f, d, a, c, x, e):
        rubi.append(5423)
        return Dist(b/c, Int((a + b*acot(c*x))*(d + e*log(f + g*x**S(2))), x), x) - Dist(b*c*e, Int(x**S(2)*(a + b*acot(c*x))/(c**S(2)*x**S(2) + S(1)), x), x) - Simp(e*x**S(2)*(a + b*acot(c*x))**S(2)/S(2), x) + Simp((a + b*acot(c*x))**S(2)*(d + e*log(f + g*x**S(2)))*(f + g*x**S(2))/(S(2)*g), x)
    rule5423 = ReplacementRule(pattern5423, replacement5423)
    pattern5424 = Pattern(Integral(exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons1799)
    def replacement5424(x, a, n):
        rubi.append(5424)
        return Int((-I*a*x + S(1))**(I*n/S(2) + S(1)/2)*(I*a*x + S(1))**(-I*n/S(2) + S(1)/2)/sqrt(a**S(2)*x**S(2) + S(1)), x)
    rule5424 = ReplacementRule(pattern5424, replacement5424)
    pattern5425 = Pattern(Integral(x_**WC('m', S(1))*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons21, cons1799)
    def replacement5425(x, m, a, n):
        rubi.append(5425)
        return Int(x**m*(-I*a*x + S(1))**(I*n/S(2) + S(1)/2)*(I*a*x + S(1))**(-I*n/S(2) + S(1)/2)/sqrt(a**S(2)*x**S(2) + S(1)), x)
    rule5425 = ReplacementRule(pattern5425, replacement5425)
    pattern5426 = Pattern(Integral(exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons4, cons1800)
    def replacement5426(x, a, n):
        rubi.append(5426)
        return Int((-I*a*x + S(1))**(I*n/S(2))*(I*a*x + S(1))**(-I*n/S(2)), x)
    rule5426 = ReplacementRule(pattern5426, replacement5426)
    pattern5427 = Pattern(Integral(x_**WC('m', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons21, cons4, cons1800)
    def replacement5427(x, m, a, n):
        rubi.append(5427)
        return Int(x**m*(-I*a*x + S(1))**(I*n/S(2))*(I*a*x + S(1))**(-I*n/S(2)), x)
    rule5427 = ReplacementRule(pattern5427, replacement5427)
    pattern5428 = Pattern(Integral((c_ + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons5, cons1801, cons1802)
    def replacement5428(p, u, d, a, n, c, x):
        rubi.append(5428)
        return Dist(c**p, Int(u*(S(1) + d*x/c)**p*(-I*a*x + S(1))**(I*n/S(2))*(I*a*x + S(1))**(-I*n/S(2)), x), x)
    rule5428 = ReplacementRule(pattern5428, replacement5428)
    pattern5429 = Pattern(Integral((c_ + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons5, cons1801, cons1803)
    def replacement5429(p, u, d, a, n, c, x):
        rubi.append(5429)
        return Int(u*(c + d*x)**p*(-I*a*x + S(1))**(I*n/S(2))*(I*a*x + S(1))**(-I*n/S(2)), x)
    rule5429 = ReplacementRule(pattern5429, replacement5429)
    pattern5430 = Pattern(Integral((c_ + WC('d', S(1))/x_)**WC('p', S(1))*WC('u', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons1804, cons38)
    def replacement5430(p, u, d, a, n, c, x):
        rubi.append(5430)
        return Dist(d**p, Int(u*x**(-p)*(c*x/d + S(1))**p*exp(n*ArcTan(a*x)), x), x)
    rule5430 = ReplacementRule(pattern5430, replacement5430)
    pattern5431 = Pattern(Integral((c_ + WC('d', S(1))/x_)**p_*WC('u', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1804, cons147, cons1805, cons177)
    def replacement5431(p, u, d, a, n, c, x):
        rubi.append(5431)
        return Dist((S(-1))**(n/S(2))*c**p, Int(u*(S(1) - I/(a*x))**(-I*n/S(2))*(S(1) + I/(a*x))**(I*n/S(2))*(S(1) + d/(c*x))**p, x), x)
    rule5431 = ReplacementRule(pattern5431, replacement5431)
    pattern5432 = Pattern(Integral((c_ + WC('d', S(1))/x_)**p_*WC('u', S(1))*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1804, cons147, cons1805, cons117)
    def replacement5432(p, u, d, a, n, c, x):
        rubi.append(5432)
        return Int(u*(c + d/x)**p*(-I*a*x + S(1))**(I*n/S(2))*(I*a*x + S(1))**(-I*n/S(2)), x)
    rule5432 = ReplacementRule(pattern5432, replacement5432)
    pattern5433 = Pattern(Integral((c_ + WC('d', S(1))/x_)**p_*WC('u', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons5, cons1804, cons147)
    def replacement5433(p, u, d, a, n, c, x):
        rubi.append(5433)
        return Dist(x**p*(c + d/x)**p*(c*x/d + S(1))**(-p), Int(u*x**(-p)*(c*x/d + S(1))**p*exp(n*ArcTan(a*x)), x), x)
    rule5433 = ReplacementRule(pattern5433, replacement5433)
    pattern5434 = Pattern(Integral(exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1)))/(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2), x_), cons2, cons7, cons27, cons4, cons1806, cons1807)
    def replacement5434(d, a, n, c, x):
        rubi.append(5434)
        return Simp((a*x + n)*exp(n*ArcTan(a*x))/(a*c*sqrt(c + d*x**S(2))*(n**S(2) + S(1))), x)
    rule5434 = ReplacementRule(pattern5434, replacement5434)
    pattern5435 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons1806, cons13, cons137, cons1807, cons1808, cons246)
    def replacement5435(p, d, a, n, c, x):
        rubi.append(5435)
        return Dist(S(2)*(p + S(1))*(S(2)*p + S(3))/(c*(n**S(2) + S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*ArcTan(a*x)), x), x) + Simp((c + d*x**S(2))**(p + S(1))*(-S(2)*a*x*(p + S(1)) + n)*exp(n*ArcTan(a*x))/(a*c*(n**S(2) + S(4)*(p + S(1))**S(2))), x)
    rule5435 = ReplacementRule(pattern5435, replacement5435)
    pattern5436 = Pattern(Integral(exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1)))/(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons7, cons27, cons4, cons1806)
    def replacement5436(d, a, n, c, x):
        rubi.append(5436)
        return Simp(exp(n*ArcTan(a*x))/(a*c*n), x)
    rule5436 = ReplacementRule(pattern5436, replacement5436)
    pattern5437 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1806, cons38, cons1809, cons1810)
    def replacement5437(p, d, a, n, c, x):
        rubi.append(5437)
        return Dist(c**p, Int((a**S(2)*x**S(2) + S(1))**(-I*n/S(2) + p)*(-I*a*x + S(1))**(I*n), x), x)
    rule5437 = ReplacementRule(pattern5437, replacement5437)
    pattern5438 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons5, cons1806, cons1802)
    def replacement5438(p, d, a, n, c, x):
        rubi.append(5438)
        return Dist(c**p, Int((-I*a*x + S(1))**(I*n/S(2) + p)*(I*a*x + S(1))**(-I*n/S(2) + p), x), x)
    rule5438 = ReplacementRule(pattern5438, replacement5438)
    pattern5439 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1806, cons1803, cons1811)
    def replacement5439(p, d, a, n, c, x):
        rubi.append(5439)
        return Dist(c**(I*n/S(2)), Int((c + d*x**S(2))**(-I*n/S(2) + p)*(-I*a*x + S(1))**(I*n), x), x)
    rule5439 = ReplacementRule(pattern5439, replacement5439)
    pattern5440 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1806, cons1803, cons1812)
    def replacement5440(p, d, a, n, c, x):
        rubi.append(5440)
        return Dist(c**(-I*n/S(2)), Int((c + d*x**S(2))**(I*n/S(2) + p)*(I*a*x + S(1))**(-I*n), x), x)
    rule5440 = ReplacementRule(pattern5440, replacement5440)
    pattern5441 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons5, cons1806, cons1803)
    def replacement5441(p, d, a, n, c, x):
        rubi.append(5441)
        return Dist(c**IntPart(p)*(c + d*x**S(2))**FracPart(p)*(a**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int((a**S(2)*x**S(2) + S(1))**p*exp(n*ArcTan(a*x)), x), x)
    rule5441 = ReplacementRule(pattern5441, replacement5441)
    pattern5442 = Pattern(Integral(x_*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1)))/(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2), x_), cons2, cons7, cons27, cons4, cons1806, cons1807)
    def replacement5442(d, a, n, c, x):
        rubi.append(5442)
        return -Simp((-a*n*x + S(1))*exp(n*ArcTan(a*x))/(d*sqrt(c + d*x**S(2))*(n**S(2) + S(1))), x)
    rule5442 = ReplacementRule(pattern5442, replacement5442)
    pattern5443 = Pattern(Integral(x_*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons1806, cons13, cons137, cons1807, cons246)
    def replacement5443(p, d, a, n, c, x):
        rubi.append(5443)
        return -Dist(a*c*n/(S(2)*d*(p + S(1))), Int((c + d*x**S(2))**p*exp(n*ArcTan(a*x)), x), x) + Simp((c + d*x**S(2))**(p + S(1))*exp(n*ArcTan(a*x))/(S(2)*d*(p + S(1))), x)
    rule5443 = ReplacementRule(pattern5443, replacement5443)
    pattern5444 = Pattern(Integral(x_**S(2)*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons1806, cons1813, cons1807)
    def replacement5444(p, d, a, n, c, x):
        rubi.append(5444)
        return -Simp((c + d*x**S(2))**(p + S(1))*(-a*n*x + S(1))*exp(n*ArcTan(a*x))/(a*d*n*(n**S(2) + S(1))), x)
    rule5444 = ReplacementRule(pattern5444, replacement5444)
    pattern5445 = Pattern(Integral(x_**S(2)*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons1806, cons13, cons137, cons1807, cons1808, cons246)
    def replacement5445(p, d, a, n, c, x):
        rubi.append(5445)
        return Dist((n**S(2) - S(2)*p + S(-2))/(d*(n**S(2) + S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*ArcTan(a*x)), x), x) - Simp((c + d*x**S(2))**(p + S(1))*(-S(2)*a*x*(p + S(1)) + n)*exp(n*ArcTan(a*x))/(a*d*(n**S(2) + S(4)*(p + S(1))**S(2))), x)
    rule5445 = ReplacementRule(pattern5445, replacement5445)
    pattern5446 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons5, cons1806, cons1802, cons1809, cons1810)
    def replacement5446(p, m, d, a, n, c, x):
        rubi.append(5446)
        return Dist(c**p, Int(x**m*(a**S(2)*x**S(2) + S(1))**(-I*n/S(2) + p)*(-I*a*x + S(1))**(I*n), x), x)
    rule5446 = ReplacementRule(pattern5446, replacement5446)
    pattern5447 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons21, cons4, cons5, cons1806, cons1802)
    def replacement5447(p, m, d, a, n, c, x):
        rubi.append(5447)
        return Dist(c**p, Int(x**m*(-I*a*x + S(1))**(I*n/S(2) + p)*(I*a*x + S(1))**(-I*n/S(2) + p), x), x)
    rule5447 = ReplacementRule(pattern5447, replacement5447)
    pattern5448 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons5, cons1806, cons1803, cons1811)
    def replacement5448(p, m, d, a, n, c, x):
        rubi.append(5448)
        return Dist(c**(I*n/S(2)), Int(x**m*(c + d*x**S(2))**(-I*n/S(2) + p)*(-I*a*x + S(1))**(I*n), x), x)
    rule5448 = ReplacementRule(pattern5448, replacement5448)
    pattern5449 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons5, cons1806, cons1803, cons1812)
    def replacement5449(p, m, d, a, n, c, x):
        rubi.append(5449)
        return Dist(c**(-I*n/S(2)), Int(x**m*(c + d*x**S(2))**(I*n/S(2) + p)*(I*a*x + S(1))**(-I*n), x), x)
    rule5449 = ReplacementRule(pattern5449, replacement5449)
    pattern5450 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons21, cons4, cons5, cons1806, cons1803)
    def replacement5450(p, m, d, a, n, c, x):
        rubi.append(5450)
        return Dist(c**IntPart(p)*(c + d*x**S(2))**FracPart(p)*(a**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int(x**m*(a**S(2)*x**S(2) + S(1))**p*exp(n*ArcTan(a*x)), x), x)
    rule5450 = ReplacementRule(pattern5450, replacement5450)
    pattern5451 = Pattern(Integral(u_*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons5, cons1806, cons1802)
    def replacement5451(p, u, d, a, n, c, x):
        rubi.append(5451)
        return Dist(c**p, Int(u*(-I*a*x + S(1))**(I*n/S(2) + p)*(I*a*x + S(1))**(-I*n/S(2) + p), x), x)
    rule5451 = ReplacementRule(pattern5451, replacement5451)
    pattern5452 = Pattern(Integral(u_*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1806, cons1802, cons1805)
    def replacement5452(p, u, d, a, n, c, x):
        rubi.append(5452)
        return Dist(c**IntPart(p)*(c + d*x**S(2))**FracPart(p)*(-I*a*x + S(1))**(-FracPart(p))*(I*a*x + S(1))**(-FracPart(p)), Int(u*(-I*a*x + S(1))**(I*n/S(2) + p)*(I*a*x + S(1))**(-I*n/S(2) + p), x), x)
    rule5452 = ReplacementRule(pattern5452, replacement5452)
    pattern5453 = Pattern(Integral(u_*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons5, cons1806, cons1803, cons1814)
    def replacement5453(p, u, d, a, n, c, x):
        rubi.append(5453)
        return Dist(c**IntPart(p)*(c + d*x**S(2))**FracPart(p)*(a**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int(u*(a**S(2)*x**S(2) + S(1))**p*exp(n*ArcTan(a*x)), x), x)
    rule5453 = ReplacementRule(pattern5453, replacement5453)
    pattern5454 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*WC('u', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons1815, cons38)
    def replacement5454(p, u, d, a, n, c, x):
        rubi.append(5454)
        return Dist(d**p, Int(u*x**(-S(2)*p)*(a**S(2)*x**S(2) + S(1))**p*exp(n*ArcTan(a*x)), x), x)
    rule5454 = ReplacementRule(pattern5454, replacement5454)
    pattern5455 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**p_*WC('u', S(1))*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1815, cons147, cons1805, cons177)
    def replacement5455(p, u, d, a, n, c, x):
        rubi.append(5455)
        return Dist(c**p, Int(u*(S(1) - I/(a*x))**p*(S(1) + I/(a*x))**p*exp(n*ArcTan(a*x)), x), x)
    rule5455 = ReplacementRule(pattern5455, replacement5455)
    pattern5456 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**p_*WC('u', S(1))*exp(n_*ArcTan(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1815, cons147, cons1805, cons117)
    def replacement5456(p, u, d, a, n, c, x):
        rubi.append(5456)
        return Dist(x**(S(2)*p)*(c + d/x**S(2))**p*(-I*a*x + S(1))**(-p)*(I*a*x + S(1))**(-p), Int(u*x**(-S(2)*p)*(-I*a*x + S(1))**p*(I*a*x + S(1))**p*exp(n*ArcTan(a*x)), x), x)
    rule5456 = ReplacementRule(pattern5456, replacement5456)
    pattern5457 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**p_*WC('u', S(1))*exp(ArcTan(x_*WC('a', S(1)))*WC('n', S(1))), x_), cons2, cons7, cons27, cons4, cons5, cons1815, cons147, cons1814)
    def replacement5457(p, u, d, a, n, c, x):
        rubi.append(5457)
        return Dist(x**(S(2)*p)*(c + d/x**S(2))**p*(a**S(2)*x**S(2) + S(1))**(-p), Int(u*x**(-S(2)*p)*(a**S(2)*x**S(2) + S(1))**p*exp(n*ArcTan(a*x)), x), x)
    rule5457 = ReplacementRule(pattern5457, replacement5457)
    pattern5458 = Pattern(Integral(exp(ArcTan((a_ + x_*WC('b', S(1)))*WC('c', S(1)))*WC('n', S(1))), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement5458(b, c, n, a, x):
        rubi.append(5458)
        return Int((-I*a*c - I*b*c*x + S(1))**(I*n/S(2))*(I*a*c + I*b*c*x + S(1))**(-I*n/S(2)), x)
    rule5458 = ReplacementRule(pattern5458, replacement5458)
    pattern5459 = Pattern(Integral(x_**m_*exp(n_*ArcTan((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons84, cons1816, cons1817)
    def replacement5459(m, b, c, n, a, x):
        rubi.append(5459)
        return Dist(S(4)*I**(-m)*b**(-m + S(-1))*c**(-m + S(-1))/n, Subst(Int(x**(-S(2)*I/n)*(S(1) + x**(-S(2)*I/n))**(-m + S(-2))*(-I*a*c + S(1) - x**(-S(2)*I/n)*(I*a*c + S(1)))**m, x), x, (-I*c*(a + b*x) + S(1))**(I*n/S(2))*(I*c*(a + b*x) + S(1))**(-I*n/S(2))), x)
    rule5459 = ReplacementRule(pattern5459, replacement5459)
    pattern5460 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*exp(ArcTan((a_ + x_*WC('b', S(1)))*WC('c', S(1)))*WC('n', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1580)
    def replacement5460(m, b, d, c, n, a, x, e):
        rubi.append(5460)
        return Int((d + e*x)**m*(-I*a*c - I*b*c*x + S(1))**(I*n/S(2))*(I*a*c + I*b*c*x + S(1))**(-I*n/S(2)), x)
    rule5460 = ReplacementRule(pattern5460, replacement5460)
    pattern5461 = Pattern(Integral((c_ + x_**S(2)*WC('e', S(1)) + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(ArcTan(a_ + x_*WC('b', S(1)))*WC('n', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1818, cons1819, cons1820)
    def replacement5461(p, u, b, d, a, n, c, x, e):
        rubi.append(5461)
        return Dist((c/(a**S(2) + S(1)))**p, Int(u*(-I*a - I*b*x + S(1))**(I*n/S(2) + p)*(I*a + I*b*x + S(1))**(-I*n/S(2) + p), x), x)
    rule5461 = ReplacementRule(pattern5461, replacement5461)
    pattern5462 = Pattern(Integral((c_ + x_**S(2)*WC('e', S(1)) + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(ArcTan(a_ + x_*WC('b', S(1)))*WC('n', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1818, cons1819, cons1821)
    def replacement5462(p, u, b, d, a, n, c, x, e):
        rubi.append(5462)
        return Dist((c + d*x + e*x**S(2))**p*(a**S(2) + S(2)*a*b*x + b**S(2)*x**S(2) + S(1))**(-p), Int(u*(a**S(2) + S(2)*a*b*x + b**S(2)*x**S(2) + S(1))**p*exp(n*ArcTan(a*x)), x), x)
    rule5462 = ReplacementRule(pattern5462, replacement5462)
    pattern5463 = Pattern(Integral(WC('u', S(1))*exp(ArcTan(WC('c', S(1))/(x_*WC('b', S(1)) + WC('a', S(0))))*WC('n', S(1))), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement5463(u, b, c, n, a, x):
        rubi.append(5463)
        return Int(u*exp(n*acot(a/c + b*x/c)), x)
    rule5463 = ReplacementRule(pattern5463, replacement5463)
    pattern5464 = Pattern(Integral(WC('u', S(1))*exp(n_*acot(x_*WC('a', S(1)))), x_), cons2, cons1805)
    def replacement5464(x, a, n, u):
        rubi.append(5464)
        return Dist((S(-1))**(I*n/S(2)), Int(u*exp(-n*ArcTan(a*x)), x), x)
    rule5464 = ReplacementRule(pattern5464, replacement5464)
    pattern5465 = Pattern(Integral(exp(n_*acot(x_*WC('a', S(1)))), x_), cons2, cons1799)
    def replacement5465(x, a, n):
        rubi.append(5465)
        return -Subst(Int((S(1) - I*x/a)**(I*n/S(2) + S(1)/2)*(S(1) + I*x/a)**(-I*n/S(2) + S(1)/2)/(x**S(2)*sqrt(S(1) + x**S(2)/a**S(2))), x), x, S(1)/x)
    rule5465 = ReplacementRule(pattern5465, replacement5465)
    pattern5466 = Pattern(Integral(x_**WC('m', S(1))*exp(n_*acot(x_*WC('a', S(1)))), x_), cons2, cons1799, cons17)
    def replacement5466(x, m, a, n):
        rubi.append(5466)
        return -Subst(Int(x**(-m + S(-2))*(S(1) - I*x/a)**(I*n/S(2) + S(1)/2)*(S(1) + I*x/a)**(-I*n/S(2) + S(1)/2)/sqrt(S(1) + x**S(2)/a**S(2)), x), x, S(1)/x)
    rule5466 = ReplacementRule(pattern5466, replacement5466)
    pattern5467 = Pattern(Integral(exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons4, cons1807)
    def replacement5467(x, a, n):
        rubi.append(5467)
        return -Subst(Int((S(1) - I*x/a)**(I*n/S(2))*(S(1) + I*x/a)**(-I*n/S(2))/x**S(2), x), x, S(1)/x)
    rule5467 = ReplacementRule(pattern5467, replacement5467)
    pattern5468 = Pattern(Integral(x_**WC('m', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons4, cons1807, cons17)
    def replacement5468(x, m, a, n):
        rubi.append(5468)
        return -Subst(Int(x**(-m + S(-2))*(S(1) - I*x/a)**(n/S(2))*(S(1) + I*x/a)**(-n/S(2)), x), x, S(1)/x)
    rule5468 = ReplacementRule(pattern5468, replacement5468)
    pattern5469 = Pattern(Integral(x_**m_*exp(n_*acot(x_*WC('a', S(1)))), x_), cons2, cons21, cons1799, cons18)
    def replacement5469(x, m, a, n):
        rubi.append(5469)
        return -Dist(x**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(S(1) - I*x/a)**(I*n/S(2) + S(1)/2)*(S(1) + I*x/a)**(-I*n/S(2) + S(1)/2)/sqrt(S(1) + x**S(2)/a**S(2)), x), x, S(1)/x), x)
    rule5469 = ReplacementRule(pattern5469, replacement5469)
    pattern5470 = Pattern(Integral(x_**m_*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons21, cons4, cons1814, cons18)
    def replacement5470(x, m, a, n):
        rubi.append(5470)
        return -Subst(Int(x**(-m + S(-2))*(S(1) - I*x/a)**(n/S(2))*(S(1) + I*x/a)**(-n/S(2)), x), x, S(1)/x)
    rule5470 = ReplacementRule(pattern5470, replacement5470)
    pattern5471 = Pattern(Integral((c_ + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1801, cons1814, cons38)
    def replacement5471(p, u, d, a, n, c, x):
        rubi.append(5471)
        return Dist(d**p, Int(u*x**p*(c/(d*x) + S(1))**p*exp(n*acot(a*x)), x), x)
    rule5471 = ReplacementRule(pattern5471, replacement5471)
    pattern5472 = Pattern(Integral((c_ + x_*WC('d', S(1)))**p_*WC('u', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1801, cons1814, cons147)
    def replacement5472(p, u, d, a, n, c, x):
        rubi.append(5472)
        return Dist(x**(-p)*(c + d*x)**p*(c/(d*x) + S(1))**(-p), Int(u*x**p*(c/(d*x) + S(1))**p*exp(n*acot(a*x)), x), x)
    rule5472 = ReplacementRule(pattern5472, replacement5472)
    pattern5473 = Pattern(Integral((c_ + WC('d', S(1))/x_)**WC('p', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1804, cons1814, cons1802)
    def replacement5473(p, d, a, n, c, x):
        rubi.append(5473)
        return -Dist(c**p, Subst(Int((S(1) - I*x/a)**(I*n/S(2))*(S(1) + I*x/a)**(-I*n/S(2))*(S(1) + d*x/c)**p/x**S(2), x), x, S(1)/x), x)
    rule5473 = ReplacementRule(pattern5473, replacement5473)
    pattern5474 = Pattern(Integral(x_**WC('m', S(1))*(c_ + WC('d', S(1))/x_)**WC('p', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons4, cons5, cons1804, cons1814, cons1802, cons17)
    def replacement5474(p, m, d, a, n, c, x):
        rubi.append(5474)
        return -Dist(c**p, Subst(Int(x**(-m + S(-2))*(S(1) - I*x/a)**(I*n/S(2))*(S(1) + I*x/a)**(-I*n/S(2))*(S(1) + d*x/c)**p, x), x, S(1)/x), x)
    rule5474 = ReplacementRule(pattern5474, replacement5474)
    pattern5475 = Pattern(Integral((c_ + WC('d', S(1))/x_)**p_*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1804, cons1814, cons1803)
    def replacement5475(p, d, a, n, c, x):
        rubi.append(5475)
        return Dist((S(1) + d/(c*x))**(-p)*(c + d/x)**p, Int((S(1) + d/(c*x))**p*exp(n*acot(a*x)), x), x)
    rule5475 = ReplacementRule(pattern5475, replacement5475)
    pattern5476 = Pattern(Integral(x_**m_*(c_ + WC('d', S(1))/x_)**WC('p', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons4, cons5, cons1804, cons1814, cons1802, cons18)
    def replacement5476(p, m, d, a, n, c, x):
        rubi.append(5476)
        return -Dist(c**p*x**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(S(1) - I*x/a)**(I*n/S(2))*(S(1) + I*x/a)**(-I*n/S(2))*(S(1) + d*x/c)**p, x), x, S(1)/x), x)
    rule5476 = ReplacementRule(pattern5476, replacement5476)
    pattern5477 = Pattern(Integral((c_ + WC('d', S(1))/x_)**p_*WC('u', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1804, cons1814, cons1803)
    def replacement5477(p, u, d, a, n, c, x):
        rubi.append(5477)
        return Dist((S(1) + d/(c*x))**(-p)*(c + d/x)**p, Int(u*(S(1) + d/(c*x))**p*exp(n*acot(a*x)), x), x)
    rule5477 = ReplacementRule(pattern5477, replacement5477)
    pattern5478 = Pattern(Integral(exp(WC('n', S(1))*acot(x_*WC('a', S(1))))/(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons7, cons27, cons4, cons1806)
    def replacement5478(d, a, n, c, x):
        rubi.append(5478)
        return -Simp(exp(n*acot(a*x))/(a*c*n), x)
    rule5478 = ReplacementRule(pattern5478, replacement5478)
    pattern5479 = Pattern(Integral(exp(WC('n', S(1))*acot(x_*WC('a', S(1))))/(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2), x_), cons2, cons7, cons27, cons4, cons1806, cons1800)
    def replacement5479(d, a, n, c, x):
        rubi.append(5479)
        return -Simp((-a*x + n)*exp(n*acot(a*x))/(a*c*sqrt(c + d*x**S(2))*(n**S(2) + S(1))), x)
    rule5479 = ReplacementRule(pattern5479, replacement5479)
    pattern5480 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1806, cons13, cons137, cons230, cons1808, cons1822, cons1823)
    def replacement5480(p, d, a, n, c, x):
        rubi.append(5480)
        return Dist(S(2)*(p + S(1))*(S(2)*p + S(3))/(c*(n**S(2) + S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*acot(a*x)), x), x) - Simp((c + d*x**S(2))**(p + S(1))*(S(2)*a*x*(p + S(1)) + n)*exp(n*acot(a*x))/(a*c*(n**S(2) + S(4)*(p + S(1))**S(2))), x)
    rule5480 = ReplacementRule(pattern5480, replacement5480)
    pattern5481 = Pattern(Integral(x_*exp(WC('n', S(1))*acot(x_*WC('a', S(1))))/(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2), x_), cons2, cons7, cons27, cons4, cons1806, cons1800)
    def replacement5481(d, a, n, c, x):
        rubi.append(5481)
        return -Simp((a*n*x + S(1))*exp(n*acot(a*x))/(a**S(2)*c*sqrt(c + d*x**S(2))*(n**S(2) + S(1))), x)
    rule5481 = ReplacementRule(pattern5481, replacement5481)
    pattern5482 = Pattern(Integral(x_*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1806, cons13, cons1824, cons230, cons1808, cons1822, cons1823)
    def replacement5482(p, d, a, n, c, x):
        rubi.append(5482)
        return Dist(n*(S(2)*p + S(3))/(a*c*(n**S(2) + S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*acot(a*x)), x), x) + Simp((c + d*x**S(2))**(p + S(1))*(-a*n*x + S(2)*p + S(2))*exp(n*acot(a*x))/(a**S(2)*c*(n**S(2) + S(4)*(p + S(1))**S(2))), x)
    rule5482 = ReplacementRule(pattern5482, replacement5482)
    pattern5483 = Pattern(Integral(x_**S(2)*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1806, cons1813, cons1825)
    def replacement5483(p, d, a, n, c, x):
        rubi.append(5483)
        return Simp((c + d*x**S(2))**(p + S(1))*(S(2)*a*x*(p + S(1)) + n)*exp(n*acot(a*x))/(a**S(3)*c*n**S(2)*(n**S(2) + S(1))), x)
    rule5483 = ReplacementRule(pattern5483, replacement5483)
    pattern5484 = Pattern(Integral(x_**S(2)*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1806, cons13, cons1824, cons1826, cons1808, cons1822, cons1823)
    def replacement5484(p, d, a, n, c, x):
        rubi.append(5484)
        return Dist((n**S(2) - S(2)*p + S(-2))/(a**S(2)*c*(n**S(2) + S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*acot(a*x)), x), x) + Simp((c + d*x**S(2))**(p + S(1))*(S(2)*a*x*(p + S(1)) + n)*exp(n*acot(a*x))/(a**S(3)*c*(n**S(2) + S(4)*(p + S(1))**S(2))), x)
    rule5484 = ReplacementRule(pattern5484, replacement5484)
    pattern5485 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1806, cons17, cons1827, cons38)
    def replacement5485(p, m, d, a, n, c, x):
        rubi.append(5485)
        return -Dist(a**(-m + S(-1))*c**p, Subst(Int((S(1)/tan(x))**(m + S(2)*p + S(2))*exp(n*x)*cos(x)**(-S(2)*p + S(-2)), x), x, acot(a*x)), x)
    rule5485 = ReplacementRule(pattern5485, replacement5485)
    pattern5486 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1806, cons1814, cons38)
    def replacement5486(p, u, d, a, n, c, x):
        rubi.append(5486)
        return Dist(d**p, Int(u*x**(S(2)*p)*(S(1) + S(1)/(a**S(2)*x**S(2)))**p*exp(n*acot(a*x)), x), x)
    rule5486 = ReplacementRule(pattern5486, replacement5486)
    pattern5487 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*WC('u', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1806, cons1814, cons147)
    def replacement5487(p, u, d, a, n, c, x):
        rubi.append(5487)
        return Dist(x**(-S(2)*p)*(S(1) + S(1)/(a**S(2)*x**S(2)))**(-p)*(c + d*x**S(2))**p, Int(u*x**(S(2)*p)*(S(1) + S(1)/(a**S(2)*x**S(2)))**p*exp(n*acot(a*x)), x), x)
    rule5487 = ReplacementRule(pattern5487, replacement5487)
    pattern5488 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1815, cons1814, cons1802, cons1828)
    def replacement5488(p, u, d, a, n, c, x):
        rubi.append(5488)
        return Dist(c**p*(I*a)**(-S(2)*p), Int(u*x**(-S(2)*p)*(I*a*x + S(-1))**(-I*n/S(2) + p)*(I*a*x + S(1))**(I*n/S(2) + p), x), x)
    rule5488 = ReplacementRule(pattern5488, replacement5488)
    pattern5489 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1815, cons1814, cons1802, cons1829)
    def replacement5489(p, d, a, n, c, x):
        rubi.append(5489)
        return -Dist(c**p, Subst(Int((S(1) - I*x/a)**(I*n/S(2) + p)*(S(1) + I*x/a)**(-I*n/S(2) + p)/x**S(2), x), x, S(1)/x), x)
    rule5489 = ReplacementRule(pattern5489, replacement5489)
    pattern5490 = Pattern(Integral(x_**WC('m', S(1))*(c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1815, cons1814, cons1802, cons1829, cons17)
    def replacement5490(p, m, d, a, n, c, x):
        rubi.append(5490)
        return -Dist(c**p, Subst(Int(x**(-m + S(-2))*(S(1) - I*x/a)**(I*n/S(2) + p)*(S(1) + I*x/a)**(-I*n/S(2) + p), x), x, S(1)/x), x)
    rule5490 = ReplacementRule(pattern5490, replacement5490)
    pattern5491 = Pattern(Integral(x_**m_*(c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons4, cons5, cons1815, cons1814, cons1802, cons1829, cons18)
    def replacement5491(p, m, d, a, n, c, x):
        rubi.append(5491)
        return -Dist(c**p*x**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(S(1) - I*x/a)**(I*n/S(2) + p)*(S(1) + I*x/a)**(-I*n/S(2) + p), x), x, S(1)/x), x)
    rule5491 = ReplacementRule(pattern5491, replacement5491)
    pattern5492 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**p_*WC('u', S(1))*exp(WC('n', S(1))*acot(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1815, cons1814, cons1803)
    def replacement5492(p, u, d, a, n, c, x):
        rubi.append(5492)
        return Dist((S(1) + S(1)/(a**S(2)*x**S(2)))**(-p)*(c + d/x**S(2))**p, Int(u*(S(1) + S(1)/(a**S(2)*x**S(2)))**p*exp(n*acot(a*x)), x), x)
    rule5492 = ReplacementRule(pattern5492, replacement5492)
    pattern5493 = Pattern(Integral(WC('u', S(1))*exp(n_*acot((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons1805)
    def replacement5493(u, b, c, a, n, x):
        rubi.append(5493)
        return Dist((S(-1))**(I*n/S(2)), Int(u*exp(-n*ArcTan(c*(a + b*x))), x), x)
    rule5493 = ReplacementRule(pattern5493, replacement5493)
    pattern5494 = Pattern(Integral(exp(WC('n', S(1))*acot((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons4, cons1814)
    def replacement5494(b, c, n, a, x):
        rubi.append(5494)
        return Dist((I*c*(a + b*x))**(I*n/S(2))*(S(1) - I/(c*(a + b*x)))**(I*n/S(2))*(I*a*c + I*b*c*x + S(1))**(-I*n/S(2)), Int((I*a*c + I*b*c*x + S(-1))**(-I*n/S(2))*(I*a*c + I*b*c*x + S(1))**(I*n/S(2)), x), x)
    rule5494 = ReplacementRule(pattern5494, replacement5494)
    pattern5495 = Pattern(Integral(x_**m_*exp(n_*acoth((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons84, cons1816, cons1817)
    def replacement5495(m, b, c, n, a, x):
        rubi.append(5495)
        return Dist(S(4)*I**(-m)*b**(-m + S(-1))*c**(-m + S(-1))/n, Subst(Int(x**(-S(2)*I/n)*(S(-1) + x**(-S(2)*I/n))**(-m + S(-2))*(I*a*c + S(1) + x**(-S(2)*I/n)*(-I*a*c + S(1)))**m, x), x, (S(1) - I/(c*(a + b*x)))**(I*n/S(2))*(S(1) + I/(c*(a + b*x)))**(-I*n/S(2))), x)
    rule5495 = ReplacementRule(pattern5495, replacement5495)
    pattern5496 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*exp(WC('n', S(1))*acoth((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1814)
    def replacement5496(m, b, d, c, n, a, x, e):
        rubi.append(5496)
        return Dist((I*c*(a + b*x))**(I*n/S(2))*(S(1) - I/(c*(a + b*x)))**(I*n/S(2))*(I*a*c + I*b*c*x + S(1))**(-I*n/S(2)), Int((d + e*x)**m*(I*a*c + I*b*c*x + S(-1))**(-I*n/S(2))*(I*a*c + I*b*c*x + S(1))**(I*n/S(2)), x), x)
    rule5496 = ReplacementRule(pattern5496, replacement5496)
    pattern5497 = Pattern(Integral((c_ + x_**S(2)*WC('e', S(1)) + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acot(a_ + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1814, cons1818, cons1819, cons1820)
    def replacement5497(p, u, b, d, a, n, c, x, e):
        rubi.append(5497)
        return Dist((c/(a**S(2) + S(1)))**p*((I*a + I*b*x + S(1))/(I*a + I*b*x))**(I*n/S(2))*((I*a + I*b*x)/(I*a + I*b*x + S(1)))**(I*n/S(2))*(-I*a - I*b*x + S(1))**(I*n/S(2))*(I*a + I*b*x + S(-1))**(-I*n/S(2)), Int(u*(-I*a - I*b*x + S(1))**(-I*n/S(2) + p)*(I*a + I*b*x + S(1))**(I*n/S(2) + p), x), x)
    rule5497 = ReplacementRule(pattern5497, replacement5497)
    pattern5498 = Pattern(Integral((c_ + x_**S(2)*WC('e', S(1)) + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acot(a_ + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1814, cons1818, cons1819, cons1821)
    def replacement5498(p, u, b, d, a, n, c, x, e):
        rubi.append(5498)
        return Dist((c + d*x + e*x**S(2))**p*(a**S(2) + S(2)*a*b*x + b**S(2)*x**S(2) + S(1))**(-p), Int(u*(a**S(2) + S(2)*a*b*x + b**S(2)*x**S(2) + S(1))**p*exp(n*acot(a*x)), x), x)
    rule5498 = ReplacementRule(pattern5498, replacement5498)
    pattern5499 = Pattern(Integral(WC('u', S(1))*exp(WC('n', S(1))*acot(WC('c', S(1))/(x_*WC('b', S(1)) + WC('a', S(0))))), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement5499(u, b, c, n, a, x):
        rubi.append(5499)
        return Int(u*exp(n*ArcTan(a/c + b*x/c)), x)
    rule5499 = ReplacementRule(pattern5499, replacement5499)
    pattern5500 = Pattern(Integral((ArcTan(c_ + x_*WC('d', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons148)
    def replacement5500(b, d, c, a, n, x):
        rubi.append(5500)
        return Dist(S(1)/d, Subst(Int((a + b*ArcTan(x))**n, x), x, c + d*x), x)
    rule5500 = ReplacementRule(pattern5500, replacement5500)
    pattern5501 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons148)
    def replacement5501(b, d, c, a, n, x):
        rubi.append(5501)
        return Dist(S(1)/d, Subst(Int((a + b*acot(x))**n, x), x, c + d*x), x)
    rule5501 = ReplacementRule(pattern5501, replacement5501)
    pattern5502 = Pattern(Integral((ArcTan(c_ + x_*WC('d', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons340)
    def replacement5502(b, d, c, a, n, x):
        rubi.append(5502)
        return Int((a + b*ArcTan(c + d*x))**n, x)
    rule5502 = ReplacementRule(pattern5502, replacement5502)
    pattern5503 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(c_ + x_*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons340)
    def replacement5503(b, d, c, a, n, x):
        rubi.append(5503)
        return Int((a + b*acot(c + d*x))**n, x)
    rule5503 = ReplacementRule(pattern5503, replacement5503)
    pattern5504 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(ArcTan(c_ + x_*WC('d', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons148)
    def replacement5504(m, f, b, d, a, n, c, x, e):
        rubi.append(5504)
        return Dist(S(1)/d, Subst(Int((a + b*ArcTan(x))**n*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule5504 = ReplacementRule(pattern5504, replacement5504)
    pattern5505 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons148)
    def replacement5505(m, f, b, d, a, n, c, x, e):
        rubi.append(5505)
        return Dist(S(1)/d, Subst(Int((a + b*acot(x))**n*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule5505 = ReplacementRule(pattern5505, replacement5505)
    pattern5506 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**m_*(ArcTan(c_ + x_*WC('d', S(1)))*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons340)
    def replacement5506(m, f, b, d, a, c, n, x, e):
        rubi.append(5506)
        return Int((a + b*ArcTan(c + d*x))**n*(e + f*x)**m, x)
    rule5506 = ReplacementRule(pattern5506, replacement5506)
    pattern5507 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**m_*(WC('a', S(0)) + WC('b', S(1))*acot(c_ + x_*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons340)
    def replacement5507(m, f, b, d, a, c, n, x, e):
        rubi.append(5507)
        return Int((a + b*acot(c + d*x))**n*(e + f*x)**m, x)
    rule5507 = ReplacementRule(pattern5507, replacement5507)
    pattern5508 = Pattern(Integral((ArcTan(c_ + x_*WC('d', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons34, cons35, cons36, cons4, cons5, cons1830, cons1763)
    def replacement5508(B, C, p, b, d, a, n, c, x, A):
        rubi.append(5508)
        return Dist(S(1)/d, Subst(Int((a + b*ArcTan(x))**n*(C*x**S(2)/d**S(2) + C/d**S(2))**p, x), x, c + d*x), x)
    rule5508 = ReplacementRule(pattern5508, replacement5508)
    pattern5509 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acot(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons34, cons35, cons36, cons4, cons5, cons1830, cons1763)
    def replacement5509(B, C, p, b, d, a, n, c, x, A):
        rubi.append(5509)
        return Dist(S(1)/d, Subst(Int((a + b*acot(x))**n*(C*x**S(2)/d**S(2) + C/d**S(2))**p, x), x, c + d*x), x)
    rule5509 = ReplacementRule(pattern5509, replacement5509)
    pattern5510 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(ArcTan(c_ + x_*WC('d', S(1)))*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons1830, cons1763)
    def replacement5510(B, C, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(5510)
        return Dist(S(1)/d, Subst(Int((a + b*ArcTan(x))**n*(C*x**S(2)/d**S(2) + C/d**S(2))**p*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule5510 = ReplacementRule(pattern5510, replacement5510)
    pattern5511 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons1830, cons1763)
    def replacement5511(B, C, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(5511)
        return Dist(S(1)/d, Subst(Int((a + b*acot(x))**n*(C*x**S(2)/d**S(2) + C/d**S(2))**p*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule5511 = ReplacementRule(pattern5511, replacement5511)
    pattern5512 = Pattern(Integral(ArcTan(a_ + x_*WC('b', S(1)))/(c_ + x_**WC('n', S(1))*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons87)
    def replacement5512(b, d, a, n, c, x):
        rubi.append(5512)
        return Dist(I/S(2), Int(log(-I*a - I*b*x + S(1))/(c + d*x**n), x), x) - Dist(I/S(2), Int(log(I*a + I*b*x + S(1))/(c + d*x**n), x), x)
    rule5512 = ReplacementRule(pattern5512, replacement5512)
    pattern5513 = Pattern(Integral(acot(a_ + x_*WC('b', S(1)))/(c_ + x_**WC('n', S(1))*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons87)
    def replacement5513(b, d, a, n, c, x):
        rubi.append(5513)
        return Dist(I/S(2), Int(log((a + b*x - I)/(a + b*x))/(c + d*x**n), x), x) - Dist(I/S(2), Int(log((a + b*x + I)/(a + b*x))/(c + d*x**n), x), x)
    rule5513 = ReplacementRule(pattern5513, replacement5513)
    pattern5514 = Pattern(Integral(ArcTan(a_ + x_*WC('b', S(1)))/(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons4, cons1094)
    def replacement5514(b, d, c, a, n, x):
        rubi.append(5514)
        return Int(ArcTan(a + b*x)/(c + d*x**n), x)
    rule5514 = ReplacementRule(pattern5514, replacement5514)
    pattern5515 = Pattern(Integral(acot(a_ + x_*WC('b', S(1)))/(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons4, cons1094)
    def replacement5515(b, d, c, a, n, x):
        rubi.append(5515)
        return Int(acot(a + b*x)/(c + d*x**n), x)
    rule5515 = ReplacementRule(pattern5515, replacement5515)
    pattern5516 = Pattern(Integral(ArcTan(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons4, cons1831)
    def replacement5516(x, a, n, b):
        rubi.append(5516)
        return -Dist(b*n, Int(x**n/(a**S(2) + S(2)*a*b*x**n + b**S(2)*x**(S(2)*n) + S(1)), x), x) + Simp(x*ArcTan(a + b*x**n), x)
    rule5516 = ReplacementRule(pattern5516, replacement5516)
    pattern5517 = Pattern(Integral(acot(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons4, cons1831)
    def replacement5517(x, a, n, b):
        rubi.append(5517)
        return Dist(b*n, Int(x**n/(a**S(2) + S(2)*a*b*x**n + b**S(2)*x**(S(2)*n) + S(1)), x), x) + Simp(x*acot(a + b*x**n), x)
    rule5517 = ReplacementRule(pattern5517, replacement5517)
    pattern5518 = Pattern(Integral(ArcTan(x_**n_*WC('b', S(1)) + WC('a', S(0)))/x_, x_), cons2, cons3, cons4, cons1831)
    def replacement5518(x, a, n, b):
        rubi.append(5518)
        return Dist(I/S(2), Int(log(-I*a - I*b*x**n + S(1))/x, x), x) - Dist(I/S(2), Int(log(I*a + I*b*x**n + S(1))/x, x), x)
    rule5518 = ReplacementRule(pattern5518, replacement5518)
    pattern5519 = Pattern(Integral(acot(x_**n_*WC('b', S(1)) + WC('a', S(0)))/x_, x_), cons2, cons3, cons4, cons1831)
    def replacement5519(x, a, n, b):
        rubi.append(5519)
        return Dist(I/S(2), Int(log(S(1) - I/(a + b*x**n))/x, x), x) - Dist(I/S(2), Int(log(S(1) + I/(a + b*x**n))/x, x), x)
    rule5519 = ReplacementRule(pattern5519, replacement5519)
    pattern5520 = Pattern(Integral(x_**WC('m', S(1))*ArcTan(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons93, cons1832, cons1833)
    def replacement5520(m, b, a, n, x):
        rubi.append(5520)
        return -Dist(b*n/(m + S(1)), Int(x**(m + n)/(a**S(2) + S(2)*a*b*x**n + b**S(2)*x**(S(2)*n) + S(1)), x), x) + Simp(x**(m + S(1))*ArcTan(a + b*x**n)/(m + S(1)), x)
    rule5520 = ReplacementRule(pattern5520, replacement5520)
    pattern5521 = Pattern(Integral(x_**WC('m', S(1))*acot(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons93, cons1832, cons1833)
    def replacement5521(m, b, a, n, x):
        rubi.append(5521)
        return Dist(b*n/(m + S(1)), Int(x**(m + n)/(a**S(2) + S(2)*a*b*x**n + b**S(2)*x**(S(2)*n) + S(1)), x), x) + Simp(x**(m + S(1))*acot(a + b*x**n)/(m + S(1)), x)
    rule5521 = ReplacementRule(pattern5521, replacement5521)
    pattern5522 = Pattern(Integral(ArcTan(f_**(x_*WC('d', S(1)) + WC('c', S(0)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons1834)
    def replacement5522(f, b, d, c, a, x):
        rubi.append(5522)
        return Dist(I/S(2), Int(log(-I*a - I*b*f**(c + d*x) + S(1)), x), x) - Dist(I/S(2), Int(log(I*a + I*b*f**(c + d*x) + S(1)), x), x)
    rule5522 = ReplacementRule(pattern5522, replacement5522)
    pattern5523 = Pattern(Integral(acot(f_**(x_*WC('d', S(1)) + WC('c', S(0)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons1834)
    def replacement5523(f, b, d, c, a, x):
        rubi.append(5523)
        return Dist(I/S(2), Int(log(S(1) - I/(a + b*f**(c + d*x))), x), x) - Dist(I/S(2), Int(log(S(1) + I/(a + b*f**(c + d*x))), x), x)
    rule5523 = ReplacementRule(pattern5523, replacement5523)
    pattern5524 = Pattern(Integral(x_**WC('m', S(1))*ArcTan(f_**(x_*WC('d', S(1)) + WC('c', S(0)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons17, cons168)
    def replacement5524(m, f, b, d, c, a, x):
        rubi.append(5524)
        return Dist(I/S(2), Int(x**m*log(-I*a - I*b*f**(c + d*x) + S(1)), x), x) - Dist(I/S(2), Int(x**m*log(I*a + I*b*f**(c + d*x) + S(1)), x), x)
    rule5524 = ReplacementRule(pattern5524, replacement5524)
    pattern5525 = Pattern(Integral(x_**WC('m', S(1))*acot(f_**(x_*WC('d', S(1)) + WC('c', S(0)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons17, cons168)
    def replacement5525(m, f, b, d, c, a, x):
        rubi.append(5525)
        return Dist(I/S(2), Int(x**m*log(S(1) - I/(a + b*f**(c + d*x))), x), x) - Dist(I/S(2), Int(x**m*log(S(1) + I/(a + b*f**(c + d*x))), x), x)
    rule5525 = ReplacementRule(pattern5525, replacement5525)
    pattern5526 = Pattern(Integral(ArcTan(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1))*WC('u', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement5526(u, m, b, c, n, a, x):
        rubi.append(5526)
        return Int(u*acot(a/c + b*x**n/c)**m, x)
    rule5526 = ReplacementRule(pattern5526, replacement5526)
    pattern5527 = Pattern(Integral(WC('u', S(1))*acot(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement5527(u, m, b, c, n, a, x):
        rubi.append(5527)
        return Int(u*ArcTan(a/c + b*x**n/c)**m, x)
    rule5527 = ReplacementRule(pattern5527, replacement5527)
    pattern5528 = Pattern(Integral(S(1)/(sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0)))*ArcTan(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))), x_), cons2, cons3, cons7, cons1835)
    def replacement5528(x, c, b, a):
        rubi.append(5528)
        return Simp(log(ArcTan(c*x/sqrt(a + b*x**S(2))))/c, x)
    rule5528 = ReplacementRule(pattern5528, replacement5528)
    pattern5529 = Pattern(Integral(S(1)/(sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0)))*acot(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))), x_), cons2, cons3, cons7, cons1835)
    def replacement5529(x, c, b, a):
        rubi.append(5529)
        return -Simp(log(acot(c*x/sqrt(a + b*x**S(2))))/c, x)
    rule5529 = ReplacementRule(pattern5529, replacement5529)
    pattern5530 = Pattern(Integral(ArcTan(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons21, cons1835, cons66)
    def replacement5530(m, b, c, a, x):
        rubi.append(5530)
        return Simp(ArcTan(c*x/sqrt(a + b*x**S(2)))**(m + S(1))/(c*(m + S(1))), x)
    rule5530 = ReplacementRule(pattern5530, replacement5530)
    pattern5531 = Pattern(Integral(acot(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons21, cons1835, cons66)
    def replacement5531(m, b, c, a, x):
        rubi.append(5531)
        return -Simp(acot(c*x/sqrt(a + b*x**S(2)))**(m + S(1))/(c*(m + S(1))), x)
    rule5531 = ReplacementRule(pattern5531, replacement5531)
    pattern5532 = Pattern(Integral(ArcTan(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1))/sqrt(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1835, cons383)
    def replacement5532(m, b, d, c, a, x, e):
        rubi.append(5532)
        return Dist(sqrt(a + b*x**S(2))/sqrt(d + e*x**S(2)), Int(ArcTan(c*x/sqrt(a + b*x**S(2)))**m/sqrt(a + b*x**S(2)), x), x)
    rule5532 = ReplacementRule(pattern5532, replacement5532)
    pattern5533 = Pattern(Integral(acot(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1))/sqrt(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1835, cons383)
    def replacement5533(m, b, d, c, a, x, e):
        rubi.append(5533)
        return Dist(sqrt(a + b*x**S(2))/sqrt(d + e*x**S(2)), Int(acot(c*x/sqrt(a + b*x**S(2)))**m/sqrt(a + b*x**S(2)), x), x)
    rule5533 = ReplacementRule(pattern5533, replacement5533)
    pattern5534 = Pattern(Integral(ArcTan(v_ + sqrt(w_)*WC('s', S(1)))*WC('u', S(1)), x_), cons1836, cons1837)
    def replacement5534(v, w, u, x, s):
        rubi.append(5534)
        return Dist(S(1)/2, Int(u*ArcTan(v), x), x) + Dist(Pi*s/S(4), Int(u, x), x)
    rule5534 = ReplacementRule(pattern5534, replacement5534)
    pattern5535 = Pattern(Integral(WC('u', S(1))*acot(v_ + sqrt(w_)*WC('s', S(1))), x_), cons1836, cons1837)
    def replacement5535(v, w, u, x, s):
        rubi.append(5535)
        return -Dist(S(1)/2, Int(u*ArcTan(v), x), x) + Dist(Pi*s/S(4), Int(u, x), x)
    rule5535 = ReplacementRule(pattern5535, replacement5535)
    def With5536(v, x, n, u):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        try:
            tmp = InverseFunctionOfLinear(u, x)
            res = And(Not(FalseQ(tmp)), SameQ(Head(tmp), ArcTan), ZeroQ(D(v, x)**S(2) + Discriminant(v, x)*Part(tmp, S(1))**S(2)))
        except (TypeError, AttributeError):
            return False
        if res:
            return True
        return False
    pattern5536 = Pattern(Integral(u_*v_**WC('n', S(1)), x_), cons818, cons85, cons463, cons1838, cons1839, CustomConstraint(With5536))
    def replacement5536(v, x, n, u):

        tmp = InverseFunctionOfLinear(u, x)
        rubi.append(5536)
        return Dist((-Discriminant(v, x)/(S(4)*Coefficient(v, x, S(2))))**n/Coefficient(Part(tmp, S(1)), x, S(1)), Subst(Int(SimplifyIntegrand((S(1)/cos(x))**(S(2)*n + S(2))*SubstForInverseFunction(u, tmp, x), x), x), x, tmp), x)
    rule5536 = ReplacementRule(pattern5536, replacement5536)
    def With5537(v, x, n, u):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        try:
            tmp = InverseFunctionOfLinear(u, x)
            res = And(Not(FalseQ(tmp)), SameQ(Head(tmp), ArcCot), ZeroQ(D(v, x)**S(2) + Discriminant(v, x)*Part(tmp, S(1))**S(2)))
        except (TypeError, AttributeError):
            return False
        if res:
            return True
        return False
    pattern5537 = Pattern(Integral(u_*v_**WC('n', S(1)), x_), cons818, cons85, cons463, cons1838, cons1840, CustomConstraint(With5537))
    def replacement5537(v, x, n, u):

        tmp = InverseFunctionOfLinear(u, x)
        rubi.append(5537)
        return -Dist((-Discriminant(v, x)/(S(4)*Coefficient(v, x, S(2))))**n/Coefficient(Part(tmp, S(1)), x, S(1)), Subst(Int(SimplifyIntegrand((S(1)/sin(x))**(S(2)*n + S(2))*SubstForInverseFunction(u, tmp, x), x), x), x, tmp), x)
    rule5537 = ReplacementRule(pattern5537, replacement5537)
    pattern5538 = Pattern(Integral(ArcTan(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1841)
    def replacement5538(b, d, c, a, x):
        rubi.append(5538)
        return -Dist(I*b, Int(x/(c*exp(S(2)*I*a + S(2)*I*b*x) + c + I*d), x), x) + Simp(x*ArcTan(c + d*tan(a + b*x)), x)
    rule5538 = ReplacementRule(pattern5538, replacement5538)
    pattern5539 = Pattern(Integral(acot(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1841)
    def replacement5539(b, d, c, a, x):
        rubi.append(5539)
        return Dist(I*b, Int(x/(c*exp(S(2)*I*a + S(2)*I*b*x) + c + I*d), x), x) + Simp(x*acot(c + d*tan(a + b*x)), x)
    rule5539 = ReplacementRule(pattern5539, replacement5539)
    pattern5540 = Pattern(Integral(ArcTan(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1842)
    def replacement5540(b, d, c, a, x):
        rubi.append(5540)
        return -Dist(I*b, Int(x/(-c*exp(S(2)*I*a + S(2)*I*b*x) + c - I*d), x), x) + Simp(x*ArcTan(c + d/tan(a + b*x)), x)
    rule5540 = ReplacementRule(pattern5540, replacement5540)
    pattern5541 = Pattern(Integral(acot(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1842)
    def replacement5541(b, d, c, a, x):
        rubi.append(5541)
        return Dist(I*b, Int(x/(-c*exp(S(2)*I*a + S(2)*I*b*x) + c - I*d), x), x) + Simp(x*acot(c + d/tan(a + b*x)), x)
    rule5541 = ReplacementRule(pattern5541, replacement5541)
    pattern5542 = Pattern(Integral(ArcTan(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1843)
    def replacement5542(b, d, c, a, x):
        rubi.append(5542)
        return Dist(b*(-I*c - d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(-I*c + d + (-I*c - d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) - Dist(b*(I*c + d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(I*c - d + (I*c + d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp(x*ArcTan(c + d*tan(a + b*x)), x)
    rule5542 = ReplacementRule(pattern5542, replacement5542)
    pattern5543 = Pattern(Integral(acot(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1843)
    def replacement5543(b, d, c, a, x):
        rubi.append(5543)
        return -Dist(b*(-I*c - d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(-I*c + d + (-I*c - d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Dist(b*(I*c + d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(I*c - d + (I*c + d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp(x*acot(c + d*tan(a + b*x)), x)
    rule5543 = ReplacementRule(pattern5543, replacement5543)
    pattern5544 = Pattern(Integral(ArcTan(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1843)
    def replacement5544(b, d, c, a, x):
        rubi.append(5544)
        return -Dist(b*(-I*c + d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(-I*c - d - (-I*c + d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Dist(b*(I*c - d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(I*c + d - (I*c - d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp(x*ArcTan(c + d/tan(a + b*x)), x)
    rule5544 = ReplacementRule(pattern5544, replacement5544)
    pattern5545 = Pattern(Integral(acot(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1844)
    def replacement5545(b, d, c, a, x):
        rubi.append(5545)
        return Dist(b*(-I*c + d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(-I*c - d - (-I*c + d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) - Dist(b*(I*c - d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(I*c + d - (I*c - d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp(x*acot(c + d/tan(a + b*x)), x)
    rule5545 = ReplacementRule(pattern5545, replacement5545)
    pattern5546 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1841)
    def replacement5546(m, f, b, d, c, a, x, e):
        rubi.append(5546)
        return -Dist(I*b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(c*exp(S(2)*I*a + S(2)*I*b*x) + c + I*d), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(c + d*tan(a + b*x))/(f*(m + S(1))), x)
    rule5546 = ReplacementRule(pattern5546, replacement5546)
    pattern5547 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1841)
    def replacement5547(m, f, b, d, c, a, x, e):
        rubi.append(5547)
        return Dist(I*b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(c*exp(S(2)*I*a + S(2)*I*b*x) + c + I*d), x), x) + Simp((e + f*x)**(m + S(1))*acot(c + d*tan(a + b*x))/(f*(m + S(1))), x)
    rule5547 = ReplacementRule(pattern5547, replacement5547)
    pattern5548 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1842)
    def replacement5548(m, f, b, d, c, a, x, e):
        rubi.append(5548)
        return -Dist(I*b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(-c*exp(S(2)*I*a + S(2)*I*b*x) + c - I*d), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(c + d/tan(a + b*x))/(f*(m + S(1))), x)
    rule5548 = ReplacementRule(pattern5548, replacement5548)
    pattern5549 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1842)
    def replacement5549(m, f, b, d, c, a, x, e):
        rubi.append(5549)
        return Dist(I*b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(-c*exp(S(2)*I*a + S(2)*I*b*x) + c - I*d), x), x) + Simp((e + f*x)**(m + S(1))*acot(c + d/tan(a + b*x))/(f*(m + S(1))), x)
    rule5549 = ReplacementRule(pattern5549, replacement5549)
    pattern5550 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1843)
    def replacement5550(m, f, b, d, c, a, x, e):
        rubi.append(5550)
        return Dist(b*(-I*c - d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(-I*c + d + (-I*c - d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) - Dist(b*(I*c + d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(I*c - d + (I*c + d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(c + d*tan(a + b*x))/(f*(m + S(1))), x)
    rule5550 = ReplacementRule(pattern5550, replacement5550)
    pattern5551 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1843)
    def replacement5551(m, f, b, d, c, a, x, e):
        rubi.append(5551)
        return -Dist(b*(-I*c - d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(-I*c + d + (-I*c - d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Dist(b*(I*c + d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(I*c - d + (I*c + d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*acot(c + d*tan(a + b*x))/(f*(m + S(1))), x)
    rule5551 = ReplacementRule(pattern5551, replacement5551)
    pattern5552 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1844)
    def replacement5552(m, f, b, d, c, a, x, e):
        rubi.append(5552)
        return -Dist(b*(-I*c + d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(-I*c - d - (-I*c + d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Dist(b*(I*c - d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(I*c + d - (I*c - d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(c + d/tan(a + b*x))/(f*(m + S(1))), x)
    rule5552 = ReplacementRule(pattern5552, replacement5552)
    pattern5553 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1844)
    def replacement5553(m, f, b, d, c, a, x, e):
        rubi.append(5553)
        return Dist(b*(-I*c + d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(-I*c - d - (-I*c + d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) - Dist(b*(I*c - d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(I*c + d - (I*c - d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*acot(c + d/tan(a + b*x))/(f*(m + S(1))), x)
    rule5553 = ReplacementRule(pattern5553, replacement5553)
    pattern5554 = Pattern(Integral(ArcTan(tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons67)
    def replacement5554(x, a, b):
        rubi.append(5554)
        return -Dist(b, Int(x/cosh(S(2)*a + S(2)*b*x), x), x) + Simp(x*ArcTan(tanh(a + b*x)), x)
    rule5554 = ReplacementRule(pattern5554, replacement5554)
    pattern5555 = Pattern(Integral(acot(tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons67)
    def replacement5555(x, a, b):
        rubi.append(5555)
        return Dist(b, Int(x/cosh(S(2)*a + S(2)*b*x), x), x) + Simp(x*acot(tanh(a + b*x)), x)
    rule5555 = ReplacementRule(pattern5555, replacement5555)
    pattern5556 = Pattern(Integral(ArcTan(S(1)/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons67)
    def replacement5556(x, a, b):
        rubi.append(5556)
        return Dist(b, Int(x/cosh(S(2)*a + S(2)*b*x), x), x) + Simp(x*ArcTan(S(1)/tanh(a + b*x)), x)
    rule5556 = ReplacementRule(pattern5556, replacement5556)
    pattern5557 = Pattern(Integral(acot(S(1)/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons67)
    def replacement5557(x, a, b):
        rubi.append(5557)
        return -Dist(b, Int(x/cosh(S(2)*a + S(2)*b*x), x), x) + Simp(x*acot(S(1)/tanh(a + b*x)), x)
    rule5557 = ReplacementRule(pattern5557, replacement5557)
    pattern5558 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons48, cons125, cons62)
    def replacement5558(m, f, b, a, x, e):
        rubi.append(5558)
        return -Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/cosh(S(2)*a + S(2)*b*x), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(tanh(a + b*x))/(f*(m + S(1))), x)
    rule5558 = ReplacementRule(pattern5558, replacement5558)
    pattern5559 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons48, cons125, cons62)
    def replacement5559(m, f, b, a, x, e):
        rubi.append(5559)
        return Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/cosh(S(2)*a + S(2)*b*x), x), x) + Simp((e + f*x)**(m + S(1))*acot(tanh(a + b*x))/(f*(m + S(1))), x)
    rule5559 = ReplacementRule(pattern5559, replacement5559)
    pattern5560 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(S(1)/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons48, cons125, cons62)
    def replacement5560(m, f, b, a, x, e):
        rubi.append(5560)
        return Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/cosh(S(2)*a + S(2)*b*x), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(S(1)/tanh(a + b*x))/(f*(m + S(1))), x)
    rule5560 = ReplacementRule(pattern5560, replacement5560)
    pattern5561 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(S(1)/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons48, cons125, cons62)
    def replacement5561(m, f, b, a, x, e):
        rubi.append(5561)
        return -Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/cosh(S(2)*a + S(2)*b*x), x), x) + Simp((e + f*x)**(m + S(1))*acot(S(1)/tanh(a + b*x))/(f*(m + S(1))), x)
    rule5561 = ReplacementRule(pattern5561, replacement5561)
    pattern5562 = Pattern(Integral(ArcTan(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1845)
    def replacement5562(b, d, c, a, x):
        rubi.append(5562)
        return -Dist(b, Int(x/(c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp(x*ArcTan(c + d*tanh(a + b*x)), x)
    rule5562 = ReplacementRule(pattern5562, replacement5562)
    pattern5563 = Pattern(Integral(acot(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1845)
    def replacement5563(b, d, c, a, x):
        rubi.append(5563)
        return Dist(b, Int(x/(c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp(x*acot(c + d*tanh(a + b*x)), x)
    rule5563 = ReplacementRule(pattern5563, replacement5563)
    pattern5564 = Pattern(Integral(ArcTan(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1845)
    def replacement5564(b, d, c, a, x):
        rubi.append(5564)
        return -Dist(b, Int(x/(-c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp(x*ArcTan(c + d/tanh(a + b*x)), x)
    rule5564 = ReplacementRule(pattern5564, replacement5564)
    pattern5565 = Pattern(Integral(acot(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1845)
    def replacement5565(b, d, c, a, x):
        rubi.append(5565)
        return Dist(b, Int(x/(-c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp(x*acot(c + d/tanh(a + b*x)), x)
    rule5565 = ReplacementRule(pattern5565, replacement5565)
    pattern5566 = Pattern(Integral(ArcTan(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1846)
    def replacement5566(b, d, c, a, x):
        rubi.append(5566)
        return Dist(I*b*(-c - d + I), Int(x*exp(S(2)*a + S(2)*b*x)/(-c + d + (-c - d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) - Dist(I*b*(c + d + I), Int(x*exp(S(2)*a + S(2)*b*x)/(c - d + (c + d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Simp(x*ArcTan(c + d*tanh(a + b*x)), x)
    rule5566 = ReplacementRule(pattern5566, replacement5566)
    pattern5567 = Pattern(Integral(acot(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1846)
    def replacement5567(b, d, c, a, x):
        rubi.append(5567)
        return -Dist(I*b*(-c - d + I), Int(x*exp(S(2)*a + S(2)*b*x)/(-c + d + (-c - d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Dist(I*b*(c + d + I), Int(x*exp(S(2)*a + S(2)*b*x)/(c - d + (c + d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Simp(x*acot(c + d*tanh(a + b*x)), x)
    rule5567 = ReplacementRule(pattern5567, replacement5567)
    pattern5568 = Pattern(Integral(ArcTan(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1846)
    def replacement5568(b, d, c, a, x):
        rubi.append(5568)
        return -Dist(I*b*(-c - d + I), Int(x*exp(S(2)*a + S(2)*b*x)/(-c + d - (-c - d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Dist(I*b*(c + d + I), Int(x*exp(S(2)*a + S(2)*b*x)/(c - d - (c + d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Simp(x*ArcTan(c + d/tanh(a + b*x)), x)
    rule5568 = ReplacementRule(pattern5568, replacement5568)
    pattern5569 = Pattern(Integral(acot(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1846)
    def replacement5569(b, d, c, a, x):
        rubi.append(5569)
        return Dist(I*b*(-c - d + I), Int(x*exp(S(2)*a + S(2)*b*x)/(-c + d - (-c - d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) - Dist(I*b*(c + d + I), Int(x*exp(S(2)*a + S(2)*b*x)/(c - d - (c + d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Simp(x*acot(c + d/tanh(a + b*x)), x)
    rule5569 = ReplacementRule(pattern5569, replacement5569)
    pattern5570 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1845)
    def replacement5570(m, f, b, d, c, a, x, e):
        rubi.append(5570)
        return -Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(c + d*tanh(a + b*x))/(f*(m + S(1))), x)
    rule5570 = ReplacementRule(pattern5570, replacement5570)
    pattern5571 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1845)
    def replacement5571(m, f, b, d, c, a, x, e):
        rubi.append(5571)
        return Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp((e + f*x)**(m + S(1))*acot(c + d*tanh(a + b*x))/(f*(m + S(1))), x)
    rule5571 = ReplacementRule(pattern5571, replacement5571)
    pattern5572 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1845)
    def replacement5572(m, f, b, d, c, a, x, e):
        rubi.append(5572)
        return -Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(-c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(c + d/tanh(a + b*x))/(f*(m + S(1))), x)
    rule5572 = ReplacementRule(pattern5572, replacement5572)
    pattern5573 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1845)
    def replacement5573(m, f, b, d, c, a, x, e):
        rubi.append(5573)
        return Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(-c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp((e + f*x)**(m + S(1))*acot(c + d/tanh(a + b*x))/(f*(m + S(1))), x)
    rule5573 = ReplacementRule(pattern5573, replacement5573)
    pattern5574 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1846)
    def replacement5574(m, f, b, d, c, a, x, e):
        rubi.append(5574)
        return Dist(I*b*(-c - d + I)/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(-c + d + (-c - d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) - Dist(I*b*(c + d + I)/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(c - d + (c + d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(c + d*tanh(a + b*x))/(f*(m + S(1))), x)
    rule5574 = ReplacementRule(pattern5574, replacement5574)
    pattern5575 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1846)
    def replacement5575(m, f, b, d, c, a, x, e):
        rubi.append(5575)
        return -Dist(I*b*(-c - d + I)/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(-c + d + (-c - d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Dist(I*b*(c + d + I)/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(c - d + (c + d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Simp((e + f*x)**(m + S(1))*acot(c + d*tanh(a + b*x))/(f*(m + S(1))), x)
    rule5575 = ReplacementRule(pattern5575, replacement5575)
    pattern5576 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*ArcTan(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1846)
    def replacement5576(m, f, b, d, c, a, x, e):
        rubi.append(5576)
        return -Dist(I*b*(-c - d + I)/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(-c + d - (-c - d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Dist(I*b*(c + d + I)/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(c - d - (c + d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Simp((e + f*x)**(m + S(1))*ArcTan(c + d/tanh(a + b*x))/(f*(m + S(1))), x)
    rule5576 = ReplacementRule(pattern5576, replacement5576)
    pattern5577 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acot(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1846)
    def replacement5577(m, f, b, d, c, a, x, e):
        rubi.append(5577)
        return Dist(I*b*(-c - d + I)/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(-c + d - (-c - d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) - Dist(I*b*(c + d + I)/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(c - d - (c + d + I)*exp(S(2)*a + S(2)*b*x) + I), x), x) + Simp((e + f*x)**(m + S(1))*acot(c + d/tanh(a + b*x))/(f*(m + S(1))), x)
    rule5577 = ReplacementRule(pattern5577, replacement5577)
    pattern5578 = Pattern(Integral(ArcTan(u_), x_), cons1230)
    def replacement5578(x, u):
        rubi.append(5578)
        return -Int(SimplifyIntegrand(x*D(u, x)/(u**S(2) + S(1)), x), x) + Simp(x*ArcTan(u), x)
    rule5578 = ReplacementRule(pattern5578, replacement5578)
    pattern5579 = Pattern(Integral(acot(u_), x_), cons1230)
    def replacement5579(x, u):
        rubi.append(5579)
        return Int(SimplifyIntegrand(x*D(u, x)/(u**S(2) + S(1)), x), x) + Simp(x*acot(u), x)
    rule5579 = ReplacementRule(pattern5579, replacement5579)
    pattern5580 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(ArcTan(u_)*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1847)
    def replacement5580(u, m, b, d, c, a, x):
        rubi.append(5580)
        return -Dist(b/(d*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/(u**S(2) + S(1)), x), x), x) + Simp((a + b*ArcTan(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule5580 = ReplacementRule(pattern5580, replacement5580)
    pattern5581 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acot(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1847)
    def replacement5581(u, m, b, d, c, a, x):
        rubi.append(5581)
        return Dist(b/(d*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/(u**S(2) + S(1)), x), x), x) + Simp((a + b*acot(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule5581 = ReplacementRule(pattern5581, replacement5581)
    def With5582(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern5582 = Pattern(Integral(v_*(ArcTan(u_)*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons1230, cons1848, cons1849, CustomConstraint(With5582))
    def replacement5582(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(5582)
        return -Dist(b, Int(SimplifyIntegrand(w*D(u, x)/(u**S(2) + S(1)), x), x), x) + Dist(a + b*ArcTan(u), w, x)
    rule5582 = ReplacementRule(pattern5582, replacement5582)
    def With5583(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern5583 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*acot(u_)), x_), cons2, cons3, cons1230, cons1850, cons1851, CustomConstraint(With5583))
    def replacement5583(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(5583)
        return Dist(b, Int(SimplifyIntegrand(w*D(u, x)/(u**S(2) + S(1)), x), x), x) + Dist(a + b*acot(u), w, x)
    rule5583 = ReplacementRule(pattern5583, replacement5583)
    pattern5584 = Pattern(Integral(ArcTan(v_)*log(w_)/(x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons552, cons1146, cons1852, cons1853)
    def replacement5584(v, w, b, a, x):
        rubi.append(5584)
        return Dist(I/S(2), Int(log(w)*log(-I*v + S(1))/(a + b*x), x), x) - Dist(I/S(2), Int(log(w)*log(I*v + S(1))/(a + b*x), x), x)
    rule5584 = ReplacementRule(pattern5584, replacement5584)
    pattern5585 = Pattern(Integral(ArcTan(v_)*log(w_), x_), cons1242, cons1243)
    def replacement5585(v, w, x):
        rubi.append(5585)
        return -Int(SimplifyIntegrand(x*ArcTan(v)*D(w, x)/w, x), x) - Int(SimplifyIntegrand(x*D(v, x)*log(w)/(v**S(2) + S(1)), x), x) + Simp(x*ArcTan(v)*log(w), x)
    rule5585 = ReplacementRule(pattern5585, replacement5585)
    pattern5586 = Pattern(Integral(log(w_)*acot(v_), x_), cons1242, cons1243)
    def replacement5586(v, w, x):
        rubi.append(5586)
        return -Int(SimplifyIntegrand(x*D(w, x)*acot(v)/w, x), x) + Int(SimplifyIntegrand(x*D(v, x)*log(w)/(v**S(2) + S(1)), x), x) + Simp(x*log(w)*acot(v), x)
    rule5586 = ReplacementRule(pattern5586, replacement5586)
    def With5587(v, w, u, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        z = IntHide(u, x)
        if InverseFunctionFreeQ(z, x):
            return True
        return False
    pattern5587 = Pattern(Integral(u_*ArcTan(v_)*log(w_), x_), cons1242, cons1243, CustomConstraint(With5587))
    def replacement5587(v, w, u, x):

        z = IntHide(u, x)
        rubi.append(5587)
        return Dist(ArcTan(v)*log(w), z, x) - Int(SimplifyIntegrand(z*ArcTan(v)*D(w, x)/w, x), x) - Int(SimplifyIntegrand(z*D(v, x)*log(w)/(v**S(2) + S(1)), x), x)
    rule5587 = ReplacementRule(pattern5587, replacement5587)
    def With5588(v, w, u, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        z = IntHide(u, x)
        if InverseFunctionFreeQ(z, x):
            return True
        return False
    pattern5588 = Pattern(Integral(u_*log(w_)*acot(v_), x_), cons1242, cons1243, CustomConstraint(With5588))
    def replacement5588(v, w, u, x):

        z = IntHide(u, x)
        rubi.append(5588)
        return Dist(log(w)*acot(v), z, x) - Int(SimplifyIntegrand(z*D(w, x)*acot(v)/w, x), x) + Int(SimplifyIntegrand(z*D(v, x)*log(w)/(v**S(2) + S(1)), x), x)
    rule5588 = ReplacementRule(pattern5588, replacement5588)
    pattern5589 = Pattern(Integral(asec(x_*WC('c', S(1))), x_), cons7, cons7)
    def replacement5589(x, c):
        rubi.append(5589)
        return -Dist(S(1)/c, Int(S(1)/(x*sqrt(S(1) - S(1)/(c**S(2)*x**S(2)))), x), x) + Simp(x*asec(c*x), x)
    rule5589 = ReplacementRule(pattern5589, replacement5589)
    pattern5590 = Pattern(Integral(acsc(x_*WC('c', S(1))), x_), cons7, cons7)
    def replacement5590(x, c):
        rubi.append(5590)
        return Dist(S(1)/c, Int(S(1)/(x*sqrt(S(1) - S(1)/(c**S(2)*x**S(2)))), x), x) + Simp(x*acsc(c*x), x)
    rule5590 = ReplacementRule(pattern5590, replacement5590)
    pattern5591 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement5591(b, a, n, c, x):
        rubi.append(5591)
        return Dist(S(1)/c, Subst(Int((a + b*x)**n*tan(x)/cos(x), x), x, asec(c*x)), x)
    rule5591 = ReplacementRule(pattern5591, replacement5591)
    pattern5592 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement5592(b, a, n, c, x):
        rubi.append(5592)
        return -Dist(S(1)/c, Subst(Int((a + b*x)**n/(sin(x)*tan(x)), x), x, acsc(c*x)), x)
    rule5592 = ReplacementRule(pattern5592, replacement5592)
    pattern5593 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))/x_, x_), cons2, cons3, cons7, cons14)
    def replacement5593(x, a, c, b):
        rubi.append(5593)
        return -Subst(Int((a + b*acos(x/c))/x, x), x, S(1)/x)
    rule5593 = ReplacementRule(pattern5593, replacement5593)
    pattern5594 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))/x_, x_), cons2, cons3, cons7, cons14)
    def replacement5594(x, a, c, b):
        rubi.append(5594)
        return -Subst(Int((a + b*asin(x/c))/x, x), x, S(1)/x)
    rule5594 = ReplacementRule(pattern5594, replacement5594)
    pattern5595 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons21, cons66)
    def replacement5595(m, b, a, c, x):
        rubi.append(5595)
        return -Dist(b/(c*(m + S(1))), Int(x**(m + S(-1))/sqrt(S(1) - S(1)/(c**S(2)*x**S(2))), x), x) + Simp(x**(m + S(1))*(a + b*asec(c*x))/(m + S(1)), x)
    rule5595 = ReplacementRule(pattern5595, replacement5595)
    pattern5596 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons21, cons66)
    def replacement5596(m, b, a, c, x):
        rubi.append(5596)
        return Dist(b/(c*(m + S(1))), Int(x**(m + S(-1))/sqrt(S(1) - S(1)/(c**S(2)*x**S(2))), x), x) + Simp(x**(m + S(1))*(a + b*acsc(c*x))/(m + S(1)), x)
    rule5596 = ReplacementRule(pattern5596, replacement5596)
    pattern5597 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons17)
    def replacement5597(m, b, a, c, n, x):
        rubi.append(5597)
        return Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*(S(1)/cos(x))**(m + S(1))*tan(x), x), x, asec(c*x)), x)
    rule5597 = ReplacementRule(pattern5597, replacement5597)
    pattern5598 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons17)
    def replacement5598(m, b, a, c, n, x):
        rubi.append(5598)
        return -Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*(S(1)/sin(x))**(m + S(1))/tan(x), x), x, acsc(c*x)), x)
    rule5598 = ReplacementRule(pattern5598, replacement5598)
    pattern5599 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons21, cons4, cons1854)
    def replacement5599(m, b, a, n, c, x):
        rubi.append(5599)
        return Int(x**m*(a + b*asec(c*x))**n, x)
    rule5599 = ReplacementRule(pattern5599, replacement5599)
    pattern5600 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons21, cons4, cons1854)
    def replacement5600(m, b, a, n, c, x):
        rubi.append(5600)
        return Int(x**m*(a + b*acsc(c*x))**n, x)
    rule5600 = ReplacementRule(pattern5600, replacement5600)
    def With5601(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(5601)
        return -Dist(b*c*x/sqrt(c**S(2)*x**S(2)), Int(SimplifyIntegrand(u/(x*sqrt(c**S(2)*x**S(2) + S(-1))), x), x), x) + Dist(a + b*asec(c*x), u, x)
    pattern5601 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1743)
    rule5601 = ReplacementRule(pattern5601, With5601)
    def With5602(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(5602)
        return Dist(b*c*x/sqrt(c**S(2)*x**S(2)), Int(SimplifyIntegrand(u/(x*sqrt(c**S(2)*x**S(2) + S(-1))), x), x), x) + Dist(a + b*acsc(c*x), u, x)
    pattern5602 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1743)
    rule5602 = ReplacementRule(pattern5602, With5602)
    pattern5603 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons38)
    def replacement5603(p, b, d, a, n, c, x, e):
        rubi.append(5603)
        return -Subst(Int(x**(-S(2)*p + S(-2))*(a + b*acos(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x)
    rule5603 = ReplacementRule(pattern5603, replacement5603)
    pattern5604 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons38)
    def replacement5604(p, b, d, a, n, c, x, e):
        rubi.append(5604)
        return -Subst(Int(x**(-S(2)*p + S(-2))*(a + b*asin(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x)
    rule5604 = ReplacementRule(pattern5604, replacement5604)
    pattern5605 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons667, cons178, cons1855)
    def replacement5605(p, b, d, a, n, c, x, e):
        rubi.append(5605)
        return -Dist(sqrt(x**S(2))/x, Subst(Int(x**(-S(2)*p + S(-2))*(a + b*acos(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule5605 = ReplacementRule(pattern5605, replacement5605)
    pattern5606 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons667, cons178, cons1855)
    def replacement5606(p, b, d, a, n, c, x, e):
        rubi.append(5606)
        return -Dist(sqrt(x**S(2))/x, Subst(Int(x**(-S(2)*p + S(-2))*(a + b*asin(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule5606 = ReplacementRule(pattern5606, replacement5606)
    pattern5607 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons667, cons1856)
    def replacement5607(p, b, d, a, n, c, x, e):
        rubi.append(5607)
        return -Dist(sqrt(d + e*x**S(2))/(x*sqrt(d/x**S(2) + e)), Subst(Int(x**(-S(2)*p + S(-2))*(a + b*acos(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule5607 = ReplacementRule(pattern5607, replacement5607)
    pattern5608 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons667, cons1856)
    def replacement5608(p, b, d, a, n, c, x, e):
        rubi.append(5608)
        return -Dist(sqrt(d + e*x**S(2))/(x*sqrt(d/x**S(2) + e)), Subst(Int(x**(-S(2)*p + S(-2))*(a + b*asin(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule5608 = ReplacementRule(pattern5608, replacement5608)
    pattern5609 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement5609(p, b, d, a, n, c, x, e):
        rubi.append(5609)
        return Int((a + b*asec(c*x))**n*(d + e*x**S(2))**p, x)
    rule5609 = ReplacementRule(pattern5609, replacement5609)
    pattern5610 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement5610(p, b, d, a, n, c, x, e):
        rubi.append(5610)
        return Int((a + b*acsc(c*x))**n*(d + e*x**S(2))**p, x)
    rule5610 = ReplacementRule(pattern5610, replacement5610)
    pattern5611 = Pattern(Integral(x_*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement5611(p, b, d, a, c, x, e):
        rubi.append(5611)
        return -Dist(b*c*x/(S(2)*e*sqrt(c**S(2)*x**S(2))*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/(x*sqrt(c**S(2)*x**S(2) + S(-1))), x), x) + Simp((a + b*asec(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5611 = ReplacementRule(pattern5611, replacement5611)
    pattern5612 = Pattern(Integral(x_*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement5612(p, b, d, a, c, x, e):
        rubi.append(5612)
        return Dist(b*c*x/(S(2)*e*sqrt(c**S(2)*x**S(2))*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/(x*sqrt(c**S(2)*x**S(2) + S(-1))), x), x) + Simp((a + b*acsc(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule5612 = ReplacementRule(pattern5612, replacement5612)
    def With5613(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(d + e*x**S(2))**p, x)
        rubi.append(5613)
        return -Dist(b*c*x/sqrt(c**S(2)*x**S(2)), Int(SimplifyIntegrand(u/(x*sqrt(c**S(2)*x**S(2) + S(-1))), x), x), x) + Dist(a + b*asec(c*x), u, x)
    pattern5613 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1786)
    rule5613 = ReplacementRule(pattern5613, With5613)
    def With5614(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(d + e*x**S(2))**p, x)
        rubi.append(5614)
        return Dist(b*c*x/sqrt(c**S(2)*x**S(2)), Int(SimplifyIntegrand(u/(x*sqrt(c**S(2)*x**S(2) + S(-1))), x), x), x) + Dist(a + b*acsc(c*x), u, x)
    pattern5614 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1786)
    rule5614 = ReplacementRule(pattern5614, With5614)
    pattern5615 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1299)
    def replacement5615(p, m, b, d, a, n, c, x, e):
        rubi.append(5615)
        return -Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*acos(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x)
    rule5615 = ReplacementRule(pattern5615, replacement5615)
    pattern5616 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1299)
    def replacement5616(p, m, b, d, a, n, c, x, e):
        rubi.append(5616)
        return -Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*asin(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x)
    rule5616 = ReplacementRule(pattern5616, replacement5616)
    pattern5617 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons17, cons667, cons178, cons1855)
    def replacement5617(p, m, b, d, a, n, c, x, e):
        rubi.append(5617)
        return -Dist(sqrt(x**S(2))/x, Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*acos(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule5617 = ReplacementRule(pattern5617, replacement5617)
    pattern5618 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons17, cons667, cons178, cons1855)
    def replacement5618(p, m, b, d, a, n, c, x, e):
        rubi.append(5618)
        return -Dist(sqrt(x**S(2))/x, Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*asin(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule5618 = ReplacementRule(pattern5618, replacement5618)
    pattern5619 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons17, cons667, cons1856)
    def replacement5619(p, m, b, d, a, n, c, x, e):
        rubi.append(5619)
        return -Dist(sqrt(d + e*x**S(2))/(x*sqrt(d/x**S(2) + e)), Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*acos(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule5619 = ReplacementRule(pattern5619, replacement5619)
    pattern5620 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons17, cons667, cons1856)
    def replacement5620(p, m, b, d, a, n, c, x, e):
        rubi.append(5620)
        return -Dist(sqrt(d + e*x**S(2))/(x*sqrt(d/x**S(2) + e)), Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*asin(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule5620 = ReplacementRule(pattern5620, replacement5620)
    pattern5621 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement5621(p, m, b, d, a, n, c, x, e):
        rubi.append(5621)
        return Int(x**m*(a + b*asec(c*x))**n*(d + e*x**S(2))**p, x)
    rule5621 = ReplacementRule(pattern5621, replacement5621)
    pattern5622 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement5622(p, m, b, d, a, n, c, x, e):
        rubi.append(5622)
        return Int(x**m*(a + b*acsc(c*x))**n*(d + e*x**S(2))**p, x)
    rule5622 = ReplacementRule(pattern5622, replacement5622)
    pattern5623 = Pattern(Integral(asec(a_ + x_*WC('b', S(1))), x_), cons2, cons3, cons67)
    def replacement5623(x, a, b):
        rubi.append(5623)
        return -Int(S(1)/(sqrt(S(1) - S(1)/(a + b*x)**S(2))*(a + b*x)), x) + Simp((a + b*x)*asec(a + b*x)/b, x)
    rule5623 = ReplacementRule(pattern5623, replacement5623)
    pattern5624 = Pattern(Integral(acsc(a_ + x_*WC('b', S(1))), x_), cons2, cons3, cons67)
    def replacement5624(x, a, b):
        rubi.append(5624)
        return Int(S(1)/(sqrt(S(1) - S(1)/(a + b*x)**S(2))*(a + b*x)), x) + Simp((a + b*x)*acsc(a + b*x)/b, x)
    rule5624 = ReplacementRule(pattern5624, replacement5624)
    pattern5625 = Pattern(Integral(asec(a_ + x_*WC('b', S(1)))**n_, x_), cons2, cons3, cons4, cons1831)
    def replacement5625(x, a, n, b):
        rubi.append(5625)
        return Dist(S(1)/b, Subst(Int(x**n*tan(x)/cos(x), x), x, asec(a + b*x)), x)
    rule5625 = ReplacementRule(pattern5625, replacement5625)
    pattern5626 = Pattern(Integral(acsc(a_ + x_*WC('b', S(1)))**n_, x_), cons2, cons3, cons4, cons1831)
    def replacement5626(x, a, n, b):
        rubi.append(5626)
        return -Dist(S(1)/b, Subst(Int(x**n/(sin(x)*tan(x)), x), x, acsc(a + b*x)), x)
    rule5626 = ReplacementRule(pattern5626, replacement5626)
    pattern5627 = Pattern(Integral(asec(a_ + x_*WC('b', S(1)))/x_, x_), cons2, cons3, cons67)
    def replacement5627(x, a, b):
        rubi.append(5627)
        return -Simp(I*PolyLog(S(2), (-sqrt(-a**S(2) + S(1)) + S(1))*exp(I*asec(a + b*x))/a), x) - Simp(I*PolyLog(S(2), (sqrt(-a**S(2) + S(1)) + S(1))*exp(I*asec(a + b*x))/a), x) + Simp(I*PolyLog(S(2), -exp(S(2)*I*asec(a + b*x)))/S(2), x) + Simp(log(S(1) - (-sqrt(-a**S(2) + S(1)) + S(1))*exp(I*asec(a + b*x))/a)*asec(a + b*x), x) + Simp(log(S(1) - (sqrt(-a**S(2) + S(1)) + S(1))*exp(I*asec(a + b*x))/a)*asec(a + b*x), x) - Simp(log(exp(S(2)*I*asec(a + b*x)) + S(1))*asec(a + b*x), x)
    rule5627 = ReplacementRule(pattern5627, replacement5627)
    pattern5628 = Pattern(Integral(acsc(a_ + x_*WC('b', S(1)))/x_, x_), cons2, cons3, cons67)
    def replacement5628(x, a, b):
        rubi.append(5628)
        return Simp(I*PolyLog(S(2), I*(-sqrt(-a**S(2) + S(1)) + S(1))*exp(-I*acsc(a + b*x))/a), x) + Simp(I*PolyLog(S(2), I*(sqrt(-a**S(2) + S(1)) + S(1))*exp(-I*acsc(a + b*x))/a), x) + Simp(I*PolyLog(S(2), exp(S(2)*I*acsc(a + b*x)))/S(2), x) + Simp(I*acsc(a + b*x)**S(2), x) + Simp(log(S(1) - I*(-sqrt(-a**S(2) + S(1)) + S(1))*exp(-I*acsc(a + b*x))/a)*acsc(a + b*x), x) + Simp(log(S(1) - I*(sqrt(-a**S(2) + S(1)) + S(1))*exp(-I*acsc(a + b*x))/a)*acsc(a + b*x), x) - Simp(log(-exp(S(2)*I*acsc(a + b*x)) + S(1))*acsc(a + b*x), x)
    rule5628 = ReplacementRule(pattern5628, replacement5628)
    pattern5629 = Pattern(Integral(x_**WC('m', S(1))*asec(a_ + x_*WC('b', S(1))), x_), cons2, cons3, cons21, cons17, cons66)
    def replacement5629(x, m, b, a):
        rubi.append(5629)
        return -Dist(b**(-m + S(-1))/(m + S(1)), Subst(Int(x**(-m + S(-1))*((-a*x)**(m + S(1)) - (-a*x + S(1))**(m + S(1)))/sqrt(-x**S(2) + S(1)), x), x, S(1)/(a + b*x)), x) - Simp(b**(-m + S(-1))*(-b**(m + S(1))*x**(m + S(1)) + (-a)**(m + S(1)))*asec(a + b*x)/(m + S(1)), x)
    rule5629 = ReplacementRule(pattern5629, replacement5629)
    pattern5630 = Pattern(Integral(x_**WC('m', S(1))*acsc(a_ + x_*WC('b', S(1))), x_), cons2, cons3, cons21, cons17, cons66)
    def replacement5630(x, m, b, a):
        rubi.append(5630)
        return Dist(b**(-m + S(-1))/(m + S(1)), Subst(Int(x**(-m + S(-1))*((-a*x)**(m + S(1)) - (-a*x + S(1))**(m + S(1)))/sqrt(-x**S(2) + S(1)), x), x, S(1)/(a + b*x)), x) - Simp(b**(-m + S(-1))*(-b**(m + S(1))*x**(m + S(1)) + (-a)**(m + S(1)))*acsc(a + b*x)/(m + S(1)), x)
    rule5630 = ReplacementRule(pattern5630, replacement5630)
    pattern5631 = Pattern(Integral(x_**WC('m', S(1))*asec(a_ + x_*WC('b', S(1)))**n_, x_), cons2, cons3, cons4, cons62)
    def replacement5631(m, b, a, n, x):
        rubi.append(5631)
        return Dist(b**(-m + S(-1)), Subst(Int(x**n*(-a + S(1)/cos(x))**m*tan(x)/cos(x), x), x, asec(a + b*x)), x)
    rule5631 = ReplacementRule(pattern5631, replacement5631)
    pattern5632 = Pattern(Integral(x_**WC('m', S(1))*acsc(a_ + x_*WC('b', S(1)))**n_, x_), cons2, cons3, cons4, cons62)
    def replacement5632(m, b, a, n, x):
        rubi.append(5632)
        return -Dist(b**(-m + S(-1)), Subst(Int(x**n*(-a + S(1)/sin(x))**m/(sin(x)*tan(x)), x), x, acsc(a + b*x)), x)
    rule5632 = ReplacementRule(pattern5632, replacement5632)
    pattern5633 = Pattern(Integral(WC('u', S(1))*asec(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement5633(u, m, b, c, n, a, x):
        rubi.append(5633)
        return Int(u*acos(a/c + b*x**n/c)**m, x)
    rule5633 = ReplacementRule(pattern5633, replacement5633)
    pattern5634 = Pattern(Integral(WC('u', S(1))*acsc(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement5634(u, m, b, c, n, a, x):
        rubi.append(5634)
        return Int(u*asin(a/c + b*x**n/c)**m, x)
    rule5634 = ReplacementRule(pattern5634, replacement5634)
    pattern5635 = Pattern(Integral(f_**(WC('c', S(1))*asec(x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)))*WC('u', S(1)), x_), cons2, cons3, cons7, cons125, cons148)
    def replacement5635(u, f, b, c, a, n, x):
        rubi.append(5635)
        return Dist(S(1)/b, Subst(Int(f**(c*x**n)*ReplaceAll(u, Rule(x, -a/b + S(1)/(b*cos(x))))*tan(x)/cos(x), x), x, asec(a + b*x)), x)
    rule5635 = ReplacementRule(pattern5635, replacement5635)
    pattern5636 = Pattern(Integral(f_**(WC('c', S(1))*acsc(x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)))*WC('u', S(1)), x_), cons2, cons3, cons7, cons125, cons148)
    def replacement5636(u, f, b, c, a, n, x):
        rubi.append(5636)
        return -Dist(S(1)/b, Subst(Int(f**(c*x**n)*ReplaceAll(u, Rule(x, -a/b + S(1)/(b*sin(x))))/(sin(x)*tan(x)), x), x, acsc(a + b*x)), x)
    rule5636 = ReplacementRule(pattern5636, replacement5636)
    pattern5637 = Pattern(Integral(asec(u_), x_), cons1230, cons1769)
    def replacement5637(x, u):
        rubi.append(5637)
        return -Dist(u/sqrt(u**S(2)), Int(SimplifyIntegrand(x*D(u, x)/(u*sqrt(u**S(2) + S(-1))), x), x), x) + Simp(x*asec(u), x)
    rule5637 = ReplacementRule(pattern5637, replacement5637)
    pattern5638 = Pattern(Integral(acsc(u_), x_), cons1230, cons1769)
    def replacement5638(x, u):
        rubi.append(5638)
        return Dist(u/sqrt(u**S(2)), Int(SimplifyIntegrand(x*D(u, x)/(u*sqrt(u**S(2) + S(-1))), x), x), x) + Simp(x*acsc(u), x)
    rule5638 = ReplacementRule(pattern5638, replacement5638)
    pattern5639 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asec(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1769)
    def replacement5639(u, m, b, d, c, a, x):
        rubi.append(5639)
        return -Dist(b*u/(d*(m + S(1))*sqrt(u**S(2))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/(u*sqrt(u**S(2) + S(-1))), x), x), x) + Simp((a + b*asec(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule5639 = ReplacementRule(pattern5639, replacement5639)
    pattern5640 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsc(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1769)
    def replacement5640(u, m, b, d, c, a, x):
        rubi.append(5640)
        return Dist(b*u/(d*(m + S(1))*sqrt(u**S(2))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/(u*sqrt(u**S(2) + S(-1))), x), x), x) + Simp((a + b*acsc(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule5640 = ReplacementRule(pattern5640, replacement5640)
    def With5641(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern5641 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*asec(u_)), x_), cons2, cons3, cons1230, cons1857, CustomConstraint(With5641))
    def replacement5641(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(5641)
        return -Dist(b*u/sqrt(u**S(2)), Int(SimplifyIntegrand(w*D(u, x)/(u*sqrt(u**S(2) + S(-1))), x), x), x) + Dist(a + b*asec(u), w, x)
    rule5641 = ReplacementRule(pattern5641, replacement5641)
    def With5642(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern5642 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*acsc(u_)), x_), cons2, cons3, cons1230, cons1858, CustomConstraint(With5642))
    def replacement5642(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(5642)
        return Dist(b*u/sqrt(u**S(2)), Int(SimplifyIntegrand(w*D(u, x)/(u*sqrt(u**S(2) + S(-1))), x), x), x) + Dist(a + b*acsc(u), w, x)
    rule5642 = ReplacementRule(pattern5642, replacement5642)
    return [rule5031, rule5032, rule5033, rule5034, rule5035, rule5036, rule5037, rule5038, rule5039, rule5040, rule5041, rule5042, rule5043, rule5044, rule5045, rule5046, rule5047, rule5048, rule5049, rule5050, rule5051, rule5052, rule5053, rule5054, rule5055, rule5056, rule5057, rule5058, rule5059, rule5060, rule5061, rule5062, rule5063, rule5064, rule5065, rule5066, rule5067, rule5068, rule5069, rule5070, rule5071, rule5072, rule5073, rule5074, rule5075, rule5076, rule5077, rule5078, rule5079, rule5080, rule5081, rule5082, rule5083, rule5084, rule5085, rule5086, rule5087, rule5088, rule5089, rule5090, rule5091, rule5092, rule5093, rule5094, rule5095, rule5096, rule5097, rule5098, rule5099, rule5100, rule5101, rule5102, rule5103, rule5104, rule5105, rule5106, rule5107, rule5108, rule5109, rule5110, rule5111, rule5112, rule5113, rule5114, rule5115, rule5116, rule5117, rule5118, rule5119, rule5120, rule5121, rule5122, rule5123, rule5124, rule5125, rule5126, rule5127, rule5128, rule5129, rule5130, rule5131, rule5132, rule5133, rule5134, rule5135, rule5136, rule5137, rule5138, rule5139, rule5140, rule5141, rule5142, rule5143, rule5144, rule5145, rule5146, rule5147, rule5148, rule5149, rule5150, rule5151, rule5152, rule5153, rule5154, rule5155, rule5156, rule5157, rule5158, rule5159, rule5160, rule5161, rule5162, rule5163, rule5164, rule5165, rule5166, rule5167, rule5168, rule5169, rule5170, rule5171, rule5172, rule5173, rule5174, rule5175, rule5176, rule5177, rule5178, rule5179, rule5180, rule5181, rule5182, rule5183, rule5184, rule5185, rule5186, rule5187, rule5188, rule5189, rule5190, rule5191, rule5192, rule5193, rule5194, rule5195, rule5196, rule5197, rule5198, rule5199, rule5200, rule5201, rule5202, rule5203, rule5204, rule5205, rule5206, rule5207, rule5208, rule5209, rule5210, rule5211, rule5212, rule5213, rule5214, rule5215, rule5216, rule5217, rule5218, rule5219, rule5220, rule5221, rule5222, rule5223, rule5224, rule5225, rule5226, rule5227, rule5228, rule5229, rule5230, rule5231, rule5232, rule5233, rule5234, rule5235, rule5236, rule5237, rule5238, rule5239, rule5240, rule5241, rule5242, rule5243, rule5244, rule5245, rule5246, rule5247, rule5248, rule5249, rule5250, rule5251, rule5252, rule5253, rule5254, rule5255, rule5256, rule5257, rule5258, rule5259, rule5260, rule5261, rule5262, rule5263, rule5264, rule5265, rule5266, rule5267, rule5268, rule5269, rule5270, rule5271, rule5272, rule5273, rule5274, rule5275, rule5276, rule5277, rule5278, rule5279, rule5280, rule5281, rule5282, rule5283, rule5284, rule5285, rule5286, rule5287, rule5288, rule5289, rule5290, rule5291, rule5292, rule5293, rule5294, rule5295, rule5296, rule5297, rule5298, rule5299, rule5300, rule5301, rule5302, rule5303, rule5304, rule5305, rule5306, rule5307, rule5308, rule5309, rule5310, rule5311, rule5312, rule5313, rule5314, rule5315, rule5316, rule5317, rule5318, rule5319, rule5320, rule5321, rule5322, rule5323, rule5324, rule5325, rule5326, rule5327, rule5328, rule5329, rule5330, rule5331, rule5332, rule5333, rule5334, rule5335, rule5336, rule5337, rule5338, rule5339, rule5340, rule5341, rule5342, rule5343, rule5344, rule5345, rule5346, rule5347, rule5348, rule5349, rule5350, rule5351, rule5352, rule5353, rule5354, rule5355, rule5356, rule5357, rule5358, rule5359, rule5360, rule5361, rule5362, rule5363, rule5364, rule5365, rule5366, rule5367, rule5368, rule5369, rule5370, rule5371, rule5372, rule5373, rule5374, rule5375, rule5376, rule5377, rule5378, rule5379, rule5380, rule5381, rule5382, rule5383, rule5384, rule5385, rule5386, rule5387, rule5388, rule5389, rule5390, rule5391, rule5392, rule5393, rule5394, rule5395, rule5396, rule5397, rule5398, rule5399, rule5400, rule5401, rule5402, rule5403, rule5404, rule5405, rule5406, rule5407, rule5408, rule5409, rule5410, rule5411, rule5412, rule5413, rule5414, rule5415, rule5416, rule5417, rule5418, rule5419, rule5420, rule5421, rule5422, rule5423, rule5424, rule5425, rule5426, rule5427, rule5428, rule5429, rule5430, rule5431, rule5432, rule5433, rule5434, rule5435, rule5436, rule5437, rule5438, rule5439, rule5440, rule5441, rule5442, rule5443, rule5444, rule5445, rule5446, rule5447, rule5448, rule5449, rule5450, rule5451, rule5452, rule5453, rule5454, rule5455, rule5456, rule5457, rule5458, rule5459, rule5460, rule5461, rule5462, rule5463, rule5464, rule5465, rule5466, rule5467, rule5468, rule5469, rule5470, rule5471, rule5472, rule5473, rule5474, rule5475, rule5476, rule5477, rule5478, rule5479, rule5480, rule5481, rule5482, rule5483, rule5484, rule5485, rule5486, rule5487, rule5488, rule5489, rule5490, rule5491, rule5492, rule5493, rule5494, rule5495, rule5496, rule5497, rule5498, rule5499, rule5500, rule5501, rule5502, rule5503, rule5504, rule5505, rule5506, rule5507, rule5508, rule5509, rule5510, rule5511, rule5512, rule5513, rule5514, rule5515, rule5516, rule5517, rule5518, rule5519, rule5520, rule5521, rule5522, rule5523, rule5524, rule5525, rule5526, rule5527, rule5528, rule5529, rule5530, rule5531, rule5532, rule5533, rule5534, rule5535, rule5536, rule5537, rule5538, rule5539, rule5540, rule5541, rule5542, rule5543, rule5544, rule5545, rule5546, rule5547, rule5548, rule5549, rule5550, rule5551, rule5552, rule5553, rule5554, rule5555, rule5556, rule5557, rule5558, rule5559, rule5560, rule5561, rule5562, rule5563, rule5564, rule5565, rule5566, rule5567, rule5568, rule5569, rule5570, rule5571, rule5572, rule5573, rule5574, rule5575, rule5576, rule5577, rule5578, rule5579, rule5580, rule5581, rule5582, rule5583, rule5584, rule5585, rule5586, rule5587, rule5588, rule5589, rule5590, rule5591, rule5592, rule5593, rule5594, rule5595, rule5596, rule5597, rule5598, rule5599, rule5600, rule5601, rule5602, rule5603, rule5604, rule5605, rule5606, rule5607, rule5608, rule5609, rule5610, rule5611, rule5612, rule5613, rule5614, rule5615, rule5616, rule5617, rule5618, rule5619, rule5620, rule5621, rule5622, rule5623, rule5624, rule5625, rule5626, rule5627, rule5628, rule5629, rule5630, rule5631, rule5632, rule5633, rule5634, rule5635, rule5636, rule5637, rule5638, rule5639, rule5640, rule5641, rule5642, ]
