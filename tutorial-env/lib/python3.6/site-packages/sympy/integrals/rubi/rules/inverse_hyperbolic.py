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

def inverse_hyperbolic(rubi):
    from sympy.integrals.rubi.constraints import cons87, cons88, cons2, cons3, cons7, cons89, cons1579, cons4, cons148, cons66, cons27, cons21, cons62, cons1734, cons1735, cons1736, cons1778, cons268, cons48, cons1892, cons1893, cons1894, cons1895, cons731, cons652, cons732, cons654, cons584, cons1738, cons1896, cons128, cons1737, cons338, cons163, cons38, cons347, cons137, cons230, cons667, cons5, cons1739, cons1740, cons961, cons1897, cons1741, cons1898, cons1743, cons1742, cons1744, cons1570, cons1899, cons336, cons1900, cons147, cons125, cons208, cons54, cons242, cons1746, cons1747, cons486, cons162, cons94, cons93, cons272, cons1748, cons17, cons166, cons274, cons1749, cons1750, cons18, cons238, cons237, cons1751, cons246, cons1752, cons1901, cons1753, cons1754, cons1902, cons1755, cons1756, cons1903, cons209, cons925, cons464, cons84, cons1757, cons1758, cons719, cons168, cons1759, cons1760, cons267, cons717, cons1761, cons1608, cons14, cons150, cons1198, cons1273, cons1360, cons1830, cons1763, cons34, cons35, cons36, cons1762, cons1904, cons165, cons1442, cons1765, cons1764, cons1766, cons1767, cons528, cons1230, cons1769, cons1770, cons1905, cons1906, cons85, cons804, cons31, cons340, cons1907, cons1908, cons1909, cons1776, cons1043, cons1777, cons1497, cons13, cons1779, cons1780, cons1781, cons1782, cons240, cons241, cons146, cons1783, cons1510, cons1784, cons1152, cons319, cons1785, cons1786, cons1787, cons1788, cons1910, cons1911, cons1912, cons1913, cons1793, cons1794, cons1914, cons1796, cons601, cons1797, cons261, cons1915, cons1482, cons1441, cons1916, cons1250, cons1917, cons1918, cons1802, cons1803, cons1919, cons743, cons177, cons117, cons1920, cons23, cons1921, cons1922, cons1923, cons1924, cons1925, cons674, cons1926, cons1927, cons1928, cons994, cons1580, cons1818, cons1929, cons1930, cons1931, cons1932, cons1933, cons1934, cons1935, cons1824, cons973, cons1936, cons1827, cons1937, cons1938, cons1094, cons1831, cons1832, cons1833, cons1834, cons1939, cons383, cons808, cons1586, cons818, cons463, cons1940, cons1941, cons1942, cons1943, cons1944, cons67, cons1945, cons1946, cons1947, cons1948, cons1847, cons1949, cons1950, cons1951, cons1952, cons1854, cons178, cons1855, cons1856, cons1299, cons1953, cons1954, cons1955, cons1956

    pattern6084 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons87, cons88)
    def replacement6084(b, a, n, c, x):
        rubi.append(6084)
        return -Dist(b*c*n, Int(x*(a + b*asinh(c*x))**(n + S(-1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*asinh(c*x))**n, x)
    rule6084 = ReplacementRule(pattern6084, replacement6084)
    pattern6085 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons87, cons88)
    def replacement6085(b, a, n, c, x):
        rubi.append(6085)
        return -Dist(b*c*n, Int(x*(a + b*acosh(c*x))**(n + S(-1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) + Simp(x*(a + b*acosh(c*x))**n, x)
    rule6085 = ReplacementRule(pattern6085, replacement6085)
    pattern6086 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons87, cons89)
    def replacement6086(b, a, n, c, x):
        rubi.append(6086)
        return -Dist(c/(b*(n + S(1))), Int(x*(a + b*asinh(c*x))**(n + S(1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*asinh(c*x))**(n + S(1))*sqrt(c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule6086 = ReplacementRule(pattern6086, replacement6086)
    pattern6087 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons87, cons89)
    def replacement6087(b, a, n, c, x):
        rubi.append(6087)
        return -Dist(c/(b*(n + S(1))), Int(x*(a + b*acosh(c*x))**(n + S(1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) + Simp((a + b*acosh(c*x))**(n + S(1))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6087 = ReplacementRule(pattern6087, replacement6087)
    pattern6088 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement6088(b, a, n, c, x):
        rubi.append(6088)
        return Dist(S(1)/(b*c), Subst(Int(x**n*cosh(a/b - x/b), x), x, a + b*asinh(c*x)), x)
    rule6088 = ReplacementRule(pattern6088, replacement6088)
    pattern6089 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement6089(b, a, n, c, x):
        rubi.append(6089)
        return -Dist(S(1)/(b*c), Subst(Int(x**n*sinh(a/b - x/b), x), x, a + b*acosh(c*x)), x)
    rule6089 = ReplacementRule(pattern6089, replacement6089)
    pattern6090 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/x_, x_), cons2, cons3, cons7, cons148)
    def replacement6090(b, a, n, c, x):
        rubi.append(6090)
        return Subst(Int((a + b*x)**n/tanh(x), x), x, asinh(c*x))
    rule6090 = ReplacementRule(pattern6090, replacement6090)
    pattern6091 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/x_, x_), cons2, cons3, cons7, cons148)
    def replacement6091(b, a, n, c, x):
        rubi.append(6091)
        return Subst(Int((a + b*x)**n*tanh(x), x), x, acosh(c*x))
    rule6091 = ReplacementRule(pattern6091, replacement6091)
    pattern6092 = Pattern(Integral((x_*WC('d', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons148, cons66)
    def replacement6092(m, b, d, a, n, c, x):
        rubi.append(6092)
        return -Dist(b*c*n/(d*(m + S(1))), Int((d*x)**(m + S(1))*(a + b*asinh(c*x))**(n + S(-1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x) + Simp((d*x)**(m + S(1))*(a + b*asinh(c*x))**n/(d*(m + S(1))), x)
    rule6092 = ReplacementRule(pattern6092, replacement6092)
    pattern6093 = Pattern(Integral((x_*WC('d', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons148, cons66)
    def replacement6093(m, b, d, a, n, c, x):
        rubi.append(6093)
        return -Dist(b*c*n/(d*(m + S(1))), Int((d*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) + Simp((d*x)**(m + S(1))*(a + b*acosh(c*x))**n/(d*(m + S(1))), x)
    rule6093 = ReplacementRule(pattern6093, replacement6093)
    pattern6094 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons88)
    def replacement6094(m, b, a, c, n, x):
        rubi.append(6094)
        return -Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*asinh(c*x))**(n + S(-1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x) + Simp(x**(m + S(1))*(a + b*asinh(c*x))**n/(m + S(1)), x)
    rule6094 = ReplacementRule(pattern6094, replacement6094)
    pattern6095 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons88)
    def replacement6095(m, b, a, c, n, x):
        rubi.append(6095)
        return -Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) + Simp(x**(m + S(1))*(a + b*acosh(c*x))**n/(m + S(1)), x)
    rule6095 = ReplacementRule(pattern6095, replacement6095)
    pattern6096 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons1734)
    def replacement6096(m, b, a, c, n, x):
        rubi.append(6096)
        return -Dist(c**(-m + S(-1))/(b*(n + S(1))), Subst(Int(ExpandTrigReduce((a + b*x)**(n + S(1)), (m + (m + S(1))*sinh(x)**S(2))*sinh(x)**(m + S(-1)), x), x), x, asinh(c*x)), x) + Simp(x**m*(a + b*asinh(c*x))**(n + S(1))*sqrt(c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule6096 = ReplacementRule(pattern6096, replacement6096)
    pattern6097 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons1734)
    def replacement6097(m, b, a, c, n, x):
        rubi.append(6097)
        return Dist(c**(-m + S(-1))/(b*(n + S(1))), Subst(Int(ExpandTrigReduce((a + b*x)**(n + S(1))*(m - (m + S(1))*cosh(x)**S(2))*cosh(x)**(m + S(-1)), x), x), x, acosh(c*x)), x) + Simp(x**m*(a + b*acosh(c*x))**(n + S(1))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6097 = ReplacementRule(pattern6097, replacement6097)
    pattern6098 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons1735)
    def replacement6098(m, b, a, c, n, x):
        rubi.append(6098)
        return -Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*asinh(c*x))**(n + S(1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x) - Dist(c*(m + S(1))/(b*(n + S(1))), Int(x**(m + S(1))*(a + b*asinh(c*x))**(n + S(1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x) + Simp(x**m*(a + b*asinh(c*x))**(n + S(1))*sqrt(c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule6098 = ReplacementRule(pattern6098, replacement6098)
    pattern6099 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons62, cons87, cons1735)
    def replacement6099(m, b, a, c, n, x):
        rubi.append(6099)
        return Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*acosh(c*x))**(n + S(1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) - Dist(c*(m + S(1))/(b*(n + S(1))), Int(x**(m + S(1))*(a + b*acosh(c*x))**(n + S(1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) + Simp(x**m*(a + b*acosh(c*x))**(n + S(1))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6099 = ReplacementRule(pattern6099, replacement6099)
    pattern6100 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons62)
    def replacement6100(m, b, a, c, n, x):
        rubi.append(6100)
        return Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*sinh(x)**m*cosh(x), x), x, asinh(c*x)), x)
    rule6100 = ReplacementRule(pattern6100, replacement6100)
    pattern6101 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons62)
    def replacement6101(m, b, a, c, n, x):
        rubi.append(6101)
        return Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*sinh(x)*cosh(x)**m, x), x, acosh(c*x)), x)
    rule6101 = ReplacementRule(pattern6101, replacement6101)
    pattern6102 = Pattern(Integral((x_*WC('d', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons1736)
    def replacement6102(m, b, d, a, n, c, x):
        rubi.append(6102)
        return Int((d*x)**m*(a + b*asinh(c*x))**n, x)
    rule6102 = ReplacementRule(pattern6102, replacement6102)
    pattern6103 = Pattern(Integral((x_*WC('d', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons1736)
    def replacement6103(m, b, d, a, n, c, x):
        rubi.append(6103)
        return Int((d*x)**m*(a + b*acosh(c*x))**n, x)
    rule6103 = ReplacementRule(pattern6103, replacement6103)
    pattern6104 = Pattern(Integral(S(1)/(sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons268)
    def replacement6104(b, d, a, c, x, e):
        rubi.append(6104)
        return Simp(log(a + b*asinh(c*x))/(b*c*sqrt(d)), x)
    rule6104 = ReplacementRule(pattern6104, replacement6104)
    pattern6105 = Pattern(Integral(S(1)/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons1894, cons1895)
    def replacement6105(d2, b, e2, a, c, d1, e1, x):
        rubi.append(6105)
        return Simp(log(a + b*acosh(c*x))/(b*c*sqrt(-d1*d2)), x)
    rule6105 = ReplacementRule(pattern6105, replacement6105)
    pattern6106 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons268, cons584)
    def replacement6106(b, d, a, n, c, x, e):
        rubi.append(6106)
        return Simp((a + b*asinh(c*x))**(n + S(1))/(b*c*sqrt(d)*(n + S(1))), x)
    rule6106 = ReplacementRule(pattern6106, replacement6106)
    pattern6107 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons4, cons1892, cons1893, cons1894, cons1895, cons584)
    def replacement6107(d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6107)
        return Simp((a + b*acosh(c*x))**(n + S(1))/(b*c*sqrt(-d1*d2)*(n + S(1))), x)
    rule6107 = ReplacementRule(pattern6107, replacement6107)
    pattern6108 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons1738)
    def replacement6108(b, d, a, n, c, x, e):
        rubi.append(6108)
        return Dist(sqrt(c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*asinh(c*x))**n/sqrt(c**S(2)*x**S(2) + S(1)), x), x)
    rule6108 = ReplacementRule(pattern6108, replacement6108)
    pattern6109 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons4, cons1892, cons1893, cons1896)
    def replacement6109(d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6109)
        return Dist(sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(sqrt(d1 + e1*x)*sqrt(d2 + e2*x)), Int((a + b*acosh(c*x))**n/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x)
    rule6109 = ReplacementRule(pattern6109, replacement6109)
    def With6110(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(6110)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asinh(c*x), u, x)
    pattern6110 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons128)
    rule6110 = ReplacementRule(pattern6110, With6110)
    def With6111(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(6111)
        return -Dist(b*c, Int(SimplifyIntegrand(u/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x), x) + Dist(a + b*acosh(c*x), u, x)
    pattern6111 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons128)
    rule6111 = ReplacementRule(pattern6111, With6111)
    pattern6112 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons88, cons163, cons38)
    def replacement6112(p, b, d, a, n, c, x, e):
        rubi.append(6112)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*n*(-d)**p/(S(2)*p + S(1)), Int(x*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp(x*(a + b*acosh(c*x))**n*(d + e*x**S(2))**p/(S(2)*p + S(1)), x)
    rule6112 = ReplacementRule(pattern6112, replacement6112)
    pattern6113 = Pattern(Integral(sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement6113(b, d, a, n, c, x, e):
        rubi.append(6113)
        return Dist(sqrt(d + e*x**S(2))/(S(2)*sqrt(c**S(2)*x**S(2) + S(1))), Int((a + b*asinh(c*x))**n/sqrt(c**S(2)*x**S(2) + S(1)), x), x) - Dist(b*c*n*sqrt(d + e*x**S(2))/(S(2)*sqrt(c**S(2)*x**S(2) + S(1))), Int(x*(a + b*asinh(c*x))**(n + S(-1)), x), x) + Simp(x*(a + b*asinh(c*x))**n*sqrt(d + e*x**S(2))/S(2), x)
    rule6113 = ReplacementRule(pattern6113, replacement6113)
    pattern6114 = Pattern(Integral(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons87, cons88)
    def replacement6114(d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6114)
        return -Dist(sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(S(2)*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int((a + b*acosh(c*x))**n/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) - Dist(b*c*n*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(S(2)*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int(x*(a + b*acosh(c*x))**(n + S(-1)), x), x) + Simp(x*(a + b*acosh(c*x))**n*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/S(2), x)
    rule6114 = ReplacementRule(pattern6114, replacement6114)
    pattern6115 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons338, cons88, cons163)
    def replacement6115(p, b, d, a, n, c, x, e):
        rubi.append(6115)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*p + S(1)), Int(x*(a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp(x*(a + b*asinh(c*x))**n*(d + e*x**S(2))**p/(S(2)*p + S(1)), x)
    rule6115 = ReplacementRule(pattern6115, replacement6115)
    pattern6116 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons338, cons88, cons163, cons347)
    def replacement6116(p, d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6116)
        return Dist(S(2)*d1*d2*p/(S(2)*p + S(1)), Int((a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(-1))*(d2 + e2*x)**(p + S(-1)), x), x) - Dist(b*c*n*(-d1*d2)**(p + S(-1)/2)*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/((S(2)*p + S(1))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int(x*(a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(-1)/2), x), x) + Simp(x*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p/(S(2)*p + S(1)), x)
    rule6116 = ReplacementRule(pattern6116, replacement6116)
    pattern6117 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons338, cons88, cons163)
    def replacement6117(p, d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6117)
        return Dist(S(2)*d1*d2*p/(S(2)*p + S(1)), Int((a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(-1))*(d2 + e2*x)**(p + S(-1)), x), x) - Dist(b*c*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(S(2)*p + S(1)), Int(x*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp(x*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p/(S(2)*p + S(1)), x)
    rule6117 = ReplacementRule(pattern6117, replacement6117)
    pattern6118 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons87, cons88)
    def replacement6118(b, d, a, n, c, x, e):
        rubi.append(6118)
        return -Dist(b*c*n*sqrt(c**S(2)*x**S(2) + S(1))/(d*sqrt(d + e*x**S(2))), Int(x*(a + b*asinh(c*x))**(n + S(-1))/(c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*asinh(c*x))**n/(d*sqrt(d + e*x**S(2))), x)
    rule6118 = ReplacementRule(pattern6118, replacement6118)
    pattern6119 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/((d1_ + x_*WC('e1', S(1)))**(S(3)/2)*(d2_ + x_*WC('e2', S(1)))**(S(3)/2)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons87, cons88)
    def replacement6119(d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6119)
        return Dist(b*c*n*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(d1*d2*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)), Int(x*(a + b*acosh(c*x))**(n + S(-1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*acosh(c*x))**n/(d1*d2*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)), x)
    rule6119 = ReplacementRule(pattern6119, replacement6119)
    pattern6120 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons88, cons137, cons38)
    def replacement6120(p, b, d, a, n, c, x, e):
        rubi.append(6120)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(b*c*n*(-d)**p/(S(2)*p + S(2)), Int(x*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) - Simp(x*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x)
    rule6120 = ReplacementRule(pattern6120, replacement6120)
    pattern6121 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons338, cons88, cons137, cons230)
    def replacement6121(p, b, d, a, n, c, x, e):
        rubi.append(6121)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) + Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*(p + S(1))), Int(x*(a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) - Simp(x*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x)
    rule6121 = ReplacementRule(pattern6121, replacement6121)
    pattern6122 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons338, cons88, cons137, cons230, cons667)
    def replacement6122(p, d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6122)
        return Dist((S(2)*p + S(3))/(S(2)*d1*d2*(p + S(1))), Int((a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1)), x), x) - Dist(b*c*n*(-d1*d2)**(p + S(1)/2)*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(S(2)*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)*(p + S(1))), Int(x*(a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(1)/2), x), x) - Simp(x*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(S(2)*d1*d2*(p + S(1))), x)
    rule6122 = ReplacementRule(pattern6122, replacement6122)
    pattern6123 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons338, cons88, cons137, cons230)
    def replacement6123(p, d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6123)
        return Dist((S(2)*p + S(3))/(S(2)*d1*d2*(p + S(1))), Int((a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1)), x), x) - Dist(b*c*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(S(2)*(p + S(1))), Int(x*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) - Simp(x*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(S(2)*d1*d2*(p + S(1))), x)
    rule6123 = ReplacementRule(pattern6123, replacement6123)
    pattern6124 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148)
    def replacement6124(b, d, a, n, c, x, e):
        rubi.append(6124)
        return Dist(S(1)/(c*d), Subst(Int((a + b*x)**n/cosh(x), x), x, asinh(c*x)), x)
    rule6124 = ReplacementRule(pattern6124, replacement6124)
    pattern6125 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement6125(b, d, a, n, c, x, e):
        rubi.append(6125)
        return -Dist(S(1)/(c*d), Subst(Int((a + b*x)**n/sinh(x), x), x, acosh(c*x)), x)
    rule6125 = ReplacementRule(pattern6125, replacement6125)
    pattern6126 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons89, cons38)
    def replacement6126(p, b, d, a, c, n, x, e):
        rubi.append(6126)
        return -Dist(c*(-d)**p*(S(2)*p + S(1))/(b*(n + S(1))), Int(x*(a + b*acosh(c*x))**(n + S(1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp((-d)**p*(a + b*acosh(c*x))**(n + S(1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2)/(b*c*(n + S(1))), x)
    rule6126 = ReplacementRule(pattern6126, replacement6126)
    pattern6127 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1778, cons87, cons89)
    def replacement6127(p, b, d, a, c, n, x, e):
        rubi.append(6127)
        return -Dist(c*d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(S(2)*p + S(1))*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(b*(n + S(1))), Int(x*(a + b*asinh(c*x))**(n + S(1))*(c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((a + b*asinh(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule6127 = ReplacementRule(pattern6127, replacement6127)
    pattern6128 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons5, cons1892, cons1893, cons87, cons89, cons347)
    def replacement6128(p, d2, b, e2, a, c, n, d1, e1, x):
        rubi.append(6128)
        return -Dist(c*(-d1*d2)**(p + S(-1)/2)*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)*(S(2)*p + S(1))/(b*(n + S(1))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int(x*(a + b*acosh(c*x))**(n + S(1))*(c**S(2)*x**S(2) + S(-1))**(p + S(-1)/2), x), x) + Simp((a + b*acosh(c*x))**(n + S(1))*(d1 + e1*x)**p*(d2 + e2*x)**p*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6128 = ReplacementRule(pattern6128, replacement6128)
    pattern6129 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons5, cons1892, cons1893, cons87, cons89)
    def replacement6129(p, d2, b, e2, a, c, n, d1, e1, x):
        rubi.append(6129)
        return -Dist(c*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(S(2)*p + S(1))*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(b*(n + S(1))), Int(x*(a + b*acosh(c*x))**(n + S(1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp((a + b*acosh(c*x))**(n + S(1))*(d1 + e1*x)**p*(d2 + e2*x)**p*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6129 = ReplacementRule(pattern6129, replacement6129)
    pattern6130 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons1739, cons1740)
    def replacement6130(p, b, d, a, n, c, x, e):
        rubi.append(6130)
        return Dist(d**p/c, Subst(Int((a + b*x)**n*cosh(x)**(S(2)*p + S(1)), x), x, asinh(c*x)), x)
    rule6130 = ReplacementRule(pattern6130, replacement6130)
    pattern6131 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons128)
    def replacement6131(p, b, d, a, n, c, x, e):
        rubi.append(6131)
        return Dist((-d)**p/c, Subst(Int((a + b*x)**n*sinh(x)**(S(2)*p + S(1)), x), x, acosh(c*x)), x)
    rule6131 = ReplacementRule(pattern6131, replacement6131)
    pattern6132 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons4, cons1892, cons1893, cons961, cons1897)
    def replacement6132(p, d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6132)
        return Dist((-d1*d2)**p/c, Subst(Int((a + b*x)**n*sinh(x)**(S(2)*p + S(1)), x), x, acosh(c*x)), x)
    rule6132 = ReplacementRule(pattern6132, replacement6132)
    pattern6133 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons1739, cons1741)
    def replacement6133(p, b, d, a, n, c, x, e):
        rubi.append(6133)
        return Dist(d**(p + S(-1)/2)*sqrt(d + e*x**S(2))/sqrt(c**S(2)*x**S(2) + S(1)), Int((a + b*asinh(c*x))**n*(c**S(2)*x**S(2) + S(1))**p, x), x)
    rule6133 = ReplacementRule(pattern6133, replacement6133)
    pattern6134 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons4, cons1892, cons1893, cons1739, cons1896)
    def replacement6134(p, d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6134)
        return Dist((-d1*d2)**(p + S(-1)/2)*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int((a + b*acosh(c*x))**n*(c*x + S(-1))**p*(c*x + S(1))**p, x), x)
    rule6134 = ReplacementRule(pattern6134, replacement6134)
    def With6135(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(6135)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asinh(c*x), u, x)
    pattern6135 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1898, cons1743)
    rule6135 = ReplacementRule(pattern6135, With6135)
    def With6136(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(6136)
        return -Dist(b*c, Int(SimplifyIntegrand(u/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x), x) + Dist(a + b*acosh(c*x), u, x)
    pattern6136 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1742, cons1743)
    rule6136 = ReplacementRule(pattern6136, With6136)
    pattern6137 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1898, cons38, cons1744)
    def replacement6137(p, b, d, a, n, c, x, e):
        rubi.append(6137)
        return Int(ExpandIntegrand((a + b*asinh(c*x))**n, (d + e*x**S(2))**p, x), x)
    rule6137 = ReplacementRule(pattern6137, replacement6137)
    pattern6138 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1742, cons38, cons1744)
    def replacement6138(p, b, d, a, n, c, x, e):
        rubi.append(6138)
        return Int(ExpandIntegrand((a + b*acosh(c*x))**n, (d + e*x**S(2))**p, x), x)
    rule6138 = ReplacementRule(pattern6138, replacement6138)
    pattern6139 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement6139(p, b, d, a, n, c, x, e):
        rubi.append(6139)
        return Int((a + b*asinh(c*x))**n*(d + e*x**S(2))**p, x)
    rule6139 = ReplacementRule(pattern6139, replacement6139)
    pattern6140 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons38)
    def replacement6140(p, b, d, a, n, c, x, e):
        rubi.append(6140)
        return Int((a + b*acosh(c*x))**n*(d + e*x**S(2))**p, x)
    rule6140 = ReplacementRule(pattern6140, replacement6140)
    pattern6141 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons4, cons5, cons1899)
    def replacement6141(p, d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6141)
        return Int((a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p, x)
    rule6141 = ReplacementRule(pattern6141, replacement6141)
    pattern6142 = Pattern(Integral((d_ + x_*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons336, cons1900, cons147)
    def replacement6142(p, g, b, f, d, a, n, c, x, e):
        rubi.append(6142)
        return Dist((d + e*x)**FracPart(p)*(f + g*x)**FracPart(p)*(d*f + e*g*x**S(2))**(-FracPart(p)), Int((a + b*asinh(c*x))**n*(d*f + e*g*x**S(2))**p, x), x)
    rule6142 = ReplacementRule(pattern6142, replacement6142)
    pattern6143 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1737, cons147)
    def replacement6143(p, b, d, a, n, c, x, e):
        rubi.append(6143)
        return Dist((-d)**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p)), Int((a + b*acosh(c*x))**n*(c*x + S(-1))**p*(c*x + S(1))**p, x), x)
    rule6143 = ReplacementRule(pattern6143, replacement6143)
    pattern6144 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148)
    def replacement6144(b, d, a, n, c, x, e):
        rubi.append(6144)
        return Dist(S(1)/e, Subst(Int((a + b*x)**n*tanh(x), x), x, asinh(c*x)), x)
    rule6144 = ReplacementRule(pattern6144, replacement6144)
    pattern6145 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement6145(b, d, a, n, c, x, e):
        rubi.append(6145)
        return Dist(S(1)/e, Subst(Int((a + b*x)**n/tanh(x), x), x, acosh(c*x)), x)
    rule6145 = ReplacementRule(pattern6145, replacement6145)
    pattern6146 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons88, cons54, cons38)
    def replacement6146(p, b, d, a, n, c, x, e):
        rubi.append(6146)
        return -Dist(b*n*(-d)**p/(S(2)*c*(p + S(1))), Int((a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp((a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6146 = ReplacementRule(pattern6146, replacement6146)
    pattern6147 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1778, cons87, cons88, cons54)
    def replacement6147(p, b, d, a, n, c, x, e):
        rubi.append(6147)
        return -Dist(b*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp((a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6147 = ReplacementRule(pattern6147, replacement6147)
    pattern6148 = Pattern(Integral(x_*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons5, cons1892, cons1893, cons87, cons88, cons54, cons667)
    def replacement6148(p, d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6148)
        return -Dist(b*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(1)/2), x), x) + Simp((a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(S(2)*e1*e2*(p + S(1))), x)
    rule6148 = ReplacementRule(pattern6148, replacement6148)
    pattern6149 = Pattern(Integral(x_*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons5, cons1892, cons1893, cons87, cons88, cons54)
    def replacement6149(p, d2, b, e2, a, n, c, d1, e1, x):
        rubi.append(6149)
        return -Dist(b*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp((a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(S(2)*e1*e2*(p + S(1))), x)
    rule6149 = ReplacementRule(pattern6149, replacement6149)
    pattern6150 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons148)
    def replacement6150(b, d, a, n, c, x, e):
        rubi.append(6150)
        return Dist(S(1)/d, Subst(Int((a + b*x)**n/(sinh(x)*cosh(x)), x), x, asinh(c*x)), x)
    rule6150 = ReplacementRule(pattern6150, replacement6150)
    pattern6151 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement6151(b, d, a, n, c, x, e):
        rubi.append(6151)
        return -Dist(S(1)/d, Subst(Int((a + b*x)**n/(sinh(x)*cosh(x)), x), x, acosh(c*x)), x)
    rule6151 = ReplacementRule(pattern6151, replacement6151)
    pattern6152 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1737, cons87, cons88, cons242, cons66, cons38)
    def replacement6152(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6152)
        return Dist(b*c*n*(-d)**p/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*f*(m + S(1))), x)
    rule6152 = ReplacementRule(pattern6152, replacement6152)
    pattern6153 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1778, cons87, cons88, cons242, cons66)
    def replacement6153(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6153)
        return -Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*f*(m + S(1))), x)
    rule6153 = ReplacementRule(pattern6153, replacement6153)
    pattern6154 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons5, cons1892, cons1893, cons87, cons88, cons242, cons66, cons667)
    def replacement6154(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6154)
        return Dist(b*c*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(d1*d2*f*(m + S(1))), x)
    rule6154 = ReplacementRule(pattern6154, replacement6154)
    pattern6155 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons5, cons1892, cons1893, cons87, cons88, cons242, cons66)
    def replacement6155(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6155)
        return Dist(b*c*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(d1*d2*f*(m + S(1))), x)
    rule6155 = ReplacementRule(pattern6155, replacement6155)
    pattern6156 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))/x_, x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons128)
    def replacement6156(p, b, d, a, c, x, e):
        rubi.append(6156)
        return Dist(d, Int((a + b*asinh(c*x))*(d + e*x**S(2))**(p + S(-1))/x, x), x) - Dist(b*c*d**p/(S(2)*p), Int((c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((a + b*asinh(c*x))*(d + e*x**S(2))**p/(S(2)*p), x)
    rule6156 = ReplacementRule(pattern6156, replacement6156)
    pattern6157 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))/x_, x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons128)
    def replacement6157(p, b, d, a, c, x, e):
        rubi.append(6157)
        return Dist(d, Int((a + b*acosh(c*x))*(d + e*x**S(2))**(p + S(-1))/x, x), x) - Dist(b*c*(-d)**p/(S(2)*p), Int((c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp((a + b*acosh(c*x))*(d + e*x**S(2))**p/(S(2)*p), x)
    rule6157 = ReplacementRule(pattern6157, replacement6157)
    pattern6158 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1778, cons128, cons1746)
    def replacement6158(p, m, f, b, d, a, c, x, e):
        rubi.append(6158)
        return -Dist(S(2)*e*p/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*asinh(c*x))*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*d**p/(f*(m + S(1))), Int((f*x)**(m + S(1))*(c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asinh(c*x))*(d + e*x**S(2))**p/(f*(m + S(1))), x)
    rule6158 = ReplacementRule(pattern6158, replacement6158)
    pattern6159 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons128, cons1746)
    def replacement6159(p, m, f, b, d, a, c, x, e):
        rubi.append(6159)
        return -Dist(S(2)*e*p/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*acosh(c*x))*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*(-d)**p/(f*(m + S(1))), Int((f*x)**(m + S(1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))*(d + e*x**S(2))**p/(f*(m + S(1))), x)
    rule6159 = ReplacementRule(pattern6159, replacement6159)
    def With6160(p, m, f, b, d, a, c, x, e):
        u = IntHide((f*x)**m*(d + e*x**S(2))**p, x)
        rubi.append(6160)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asinh(c*x), u, x)
    pattern6160 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1778, cons128)
    rule6160 = ReplacementRule(pattern6160, With6160)
    def With6161(p, m, f, b, d, a, c, x, e):
        u = IntHide((f*x)**m*(d + e*x**S(2))**p, x)
        rubi.append(6161)
        return -Dist(b*c, Int(SimplifyIntegrand(u/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x), x) + Dist(a + b*acosh(c*x), u, x)
    pattern6161 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons128)
    rule6161 = ReplacementRule(pattern6161, With6161)
    def With6162(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(c**S(2)*x**S(2) + S(1))**p, x)
        rubi.append(6162)
        return Dist(d**p*(a + b*asinh(c*x)), u, x) - Dist(b*c*d**p, Int(SimplifyIntegrand(u/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x)
    pattern6162 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons347, cons1747, cons486, cons268)
    rule6162 = ReplacementRule(pattern6162, With6162)
    def With6163(p, d2, m, b, e2, a, c, d1, e1, x):
        u = IntHide(x**m*(c*x + S(-1))**p*(c*x + S(1))**p, x)
        rubi.append(6163)
        return Dist((-d1*d2)**p*(a + b*acosh(c*x)), u, x) - Dist(b*c*(-d1*d2)**p, Int(SimplifyIntegrand(u/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x), x)
    pattern6163 = Pattern(Integral(x_**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons347, cons1747, cons486, cons1894, cons1895)
    rule6163 = ReplacementRule(pattern6163, With6163)
    def With6164(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(c**S(2)*x**S(2) + S(1))**p, x)
        rubi.append(6164)
        return -Dist(b*c*d**(p + S(-1)/2)*sqrt(d + e*x**S(2))/sqrt(c**S(2)*x**S(2) + S(1)), Int(SimplifyIntegrand(u/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asinh(c*x), Int(x**m*(d + e*x**S(2))**p, x), x)
    pattern6164 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons961, cons1747)
    rule6164 = ReplacementRule(pattern6164, With6164)
    def With6165(p, d2, m, b, e2, a, c, d1, e1, x):
        u = IntHide(x**m*(c*x + S(-1))**p*(c*x + S(1))**p, x)
        rubi.append(6165)
        return -Dist(b*c*(-d1*d2)**(p + S(-1)/2)*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int(SimplifyIntegrand(u/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x), x) + Dist(a + b*acosh(c*x), Int(x**m*(d1 + e1*x)**p*(d2 + e2*x)**p, x), x)
    pattern6165 = Pattern(Integral(x_**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons961, cons1747)
    rule6165 = ReplacementRule(pattern6165, With6165)
    pattern6166 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons162, cons88, cons163, cons94, cons38)
    def replacement6166(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6166)
        return -Dist(S(2)*e*p/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*n*(-d)**p/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**p/(f*(m + S(1))), x)
    rule6166 = ReplacementRule(pattern6166, replacement6166)
    pattern6167 = Pattern(Integral((x_*WC('f', S(1)))**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1778, cons93, cons88, cons94)
    def replacement6167(m, f, b, d, a, n, c, x, e):
        rubi.append(6167)
        return -Dist(c**S(2)*sqrt(d + e*x**S(2))/(f**S(2)*(m + S(1))*sqrt(c**S(2)*x**S(2) + S(1))), Int((f*x)**(m + S(2))*(a + b*asinh(c*x))**n/sqrt(c**S(2)*x**S(2) + S(1)), x), x) - Dist(b*c*n*sqrt(d + e*x**S(2))/(f*(m + S(1))*sqrt(c**S(2)*x**S(2) + S(1))), Int((f*x)**(m + S(1))*(a + b*asinh(c*x))**(n + S(-1)), x), x) + Simp((f*x)**(m + S(1))*(a + b*asinh(c*x))**n*sqrt(d + e*x**S(2))/(f*(m + S(1))), x)
    rule6167 = ReplacementRule(pattern6167, replacement6167)
    pattern6168 = Pattern(Integral((x_*WC('f', S(1)))**m_*sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons1892, cons1893, cons93, cons88, cons94)
    def replacement6168(d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6168)
        return -Dist(c**S(2)*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(f**S(2)*(m + S(1))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int((f*x)**(m + S(2))*(a + b*acosh(c*x))**n/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) - Dist(b*c*n*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(f*(m + S(1))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1)), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(f*(m + S(1))), x)
    rule6168 = ReplacementRule(pattern6168, replacement6168)
    pattern6169 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1778, cons162, cons88, cons163, cons94)
    def replacement6169(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6169)
        return -Dist(S(2)*e*p/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**p/(f*(m + S(1))), x)
    rule6169 = ReplacementRule(pattern6169, replacement6169)
    pattern6170 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons1892, cons1893, cons162, cons88, cons163, cons94, cons347)
    def replacement6170(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6170)
        return -Dist(S(2)*e1*e2*p/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(-1))*(d2 + e2*x)**(p + S(-1)), x), x) - Dist(b*c*n*(-d1*d2)**(p + S(-1)/2)*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(f*(m + S(1))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p/(f*(m + S(1))), x)
    rule6170 = ReplacementRule(pattern6170, replacement6170)
    pattern6171 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons338, cons88, cons163, cons272, cons38, cons1748)
    def replacement6171(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6171)
        return Dist(S(2)*d*p/(m + S(2)*p + S(1)), Int((f*x)**m*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*n*(-d)**p/(f*(m + S(2)*p + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**p/(f*(m + S(2)*p + S(1))), x)
    rule6171 = ReplacementRule(pattern6171, replacement6171)
    pattern6172 = Pattern(Integral((x_*WC('f', S(1)))**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1778, cons87, cons88, cons272, cons1748)
    def replacement6172(m, f, b, d, a, n, c, x, e):
        rubi.append(6172)
        return Dist(sqrt(d + e*x**S(2))/((m + S(2))*sqrt(c**S(2)*x**S(2) + S(1))), Int((f*x)**m*(a + b*asinh(c*x))**n/sqrt(c**S(2)*x**S(2) + S(1)), x), x) - Dist(b*c*n*sqrt(d + e*x**S(2))/(f*(m + S(2))*sqrt(c**S(2)*x**S(2) + S(1))), Int((f*x)**(m + S(1))*(a + b*asinh(c*x))**(n + S(-1)), x), x) + Simp((f*x)**(m + S(1))*(a + b*asinh(c*x))**n*sqrt(d + e*x**S(2))/(f*(m + S(2))), x)
    rule6172 = ReplacementRule(pattern6172, replacement6172)
    pattern6173 = Pattern(Integral((x_*WC('f', S(1)))**m_*sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons1892, cons1893, cons87, cons88, cons272, cons1748)
    def replacement6173(d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6173)
        return -Dist(sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/((m + S(2))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int((f*x)**m*(a + b*acosh(c*x))**n/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) - Dist(b*c*n*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(f*(m + S(2))*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1)), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(f*(m + S(2))), x)
    rule6173 = ReplacementRule(pattern6173, replacement6173)
    pattern6174 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1778, cons338, cons88, cons163, cons272, cons1748)
    def replacement6174(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6174)
        return Dist(S(2)*d*p/(m + S(2)*p + S(1)), Int((f*x)**m*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(2)*p + S(1))), Int((f*x)**(m + S(1))*(a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**p/(f*(m + S(2)*p + S(1))), x)
    rule6174 = ReplacementRule(pattern6174, replacement6174)
    pattern6175 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons1892, cons1893, cons338, cons88, cons163, cons272, cons347, cons1748)
    def replacement6175(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6175)
        return Dist(S(2)*d1*d2*p/(m + S(2)*p + S(1)), Int((f*x)**m*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(-1))*(d2 + e2*x)**(p + S(-1)), x), x) - Dist(b*c*n*(-d1*d2)**(p + S(-1)/2)*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(f*sqrt(c*x + S(-1))*sqrt(c*x + S(1))*(m + S(2)*p + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(-1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p/(f*(m + S(2)*p + S(1))), x)
    rule6175 = ReplacementRule(pattern6175, replacement6175)
    pattern6176 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons1737, cons93, cons88, cons94, cons17, cons38)
    def replacement6176(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6176)
        return Dist(c**S(2)*(m + S(2)*p + S(3))/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**p, x), x) + Dist(b*c*n*(-d)**p/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*f*(m + S(1))), x)
    rule6176 = ReplacementRule(pattern6176, replacement6176)
    pattern6177 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons1778, cons93, cons88, cons94, cons17)
    def replacement6177(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6177)
        return -Dist(c**S(2)*(m + S(2)*p + S(3))/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**p, x), x) - Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*f*(m + S(1))), x)
    rule6177 = ReplacementRule(pattern6177, replacement6177)
    pattern6178 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons5, cons1892, cons1893, cons93, cons88, cons94, cons17, cons667)
    def replacement6178(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6178)
        return Dist(c**S(2)*(m + S(2)*p + S(3))/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p, x), x) + Dist(b*c*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(d1*d2*f*(m + S(1))), x)
    rule6178 = ReplacementRule(pattern6178, replacement6178)
    pattern6179 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons5, cons1892, cons1893, cons93, cons88, cons94, cons17)
    def replacement6179(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6179)
        return Dist(c**S(2)*(m + S(2)*p + S(3))/(f**S(2)*(m + S(1))), Int((f*x)**(m + S(2))*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p, x), x) + Dist(b*c*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(f*(m + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(d1*d2*f*(m + S(1))), x)
    rule6179 = ReplacementRule(pattern6179, replacement6179)
    pattern6180 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons93, cons88, cons137, cons166, cons38)
    def replacement6180(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6180)
        return -Dist(f**S(2)*(m + S(-1))/(S(2)*e*(p + S(1))), Int((f*x)**(m + S(-2))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(b*f*n*(-d)**p/(S(2)*c*(p + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6180 = ReplacementRule(pattern6180, replacement6180)
    pattern6181 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1778, cons162, cons88, cons137, cons166)
    def replacement6181(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6181)
        return -Dist(f**S(2)*(m + S(-1))/(S(2)*e*(p + S(1))), Int((f*x)**(m + S(-2))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(b*d**IntPart(p)*f*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((f*x)**(m + S(-1))*(a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6181 = ReplacementRule(pattern6181, replacement6181)
    pattern6182 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons1892, cons1893, cons162, cons88, cons137, cons166, cons667)
    def replacement6182(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6182)
        return -Dist(f**S(2)*(m + S(-1))/(S(2)*e1*e2*(p + S(1))), Int((f*x)**(m + S(-2))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1)), x), x) - Dist(b*f*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(S(2)*e1*e2*(p + S(1))), x)
    rule6182 = ReplacementRule(pattern6182, replacement6182)
    pattern6183 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons1892, cons1893, cons162, cons88, cons137, cons147, cons166)
    def replacement6183(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6183)
        return -Dist(f**S(2)*(m + S(-1))/(S(2)*e1*e2*(p + S(1))), Int((f*x)**(m + S(-2))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1)), x), x) - Dist(b*f*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(S(2)*c*(p + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(S(2)*e1*e2*(p + S(1))), x)
    rule6183 = ReplacementRule(pattern6183, replacement6183)
    pattern6184 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1737, cons338, cons88, cons137, cons274, cons38)
    def replacement6184(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6184)
        return Dist((m + S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((f*x)**m*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(b*c*n*(-d)**p/(S(2)*f*(p + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) - Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*f*(p + S(1))), x)
    rule6184 = ReplacementRule(pattern6184, replacement6184)
    pattern6185 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1778, cons338, cons88, cons137, cons274, cons1749)
    def replacement6185(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6185)
        return Dist((m + S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((f*x)**m*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) + Dist(b*c*d**IntPart(p)*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(S(2)*f*(p + S(1))), Int((f*x)**(m + S(1))*(a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) - Simp((f*x)**(m + S(1))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*f*(p + S(1))), x)
    rule6185 = ReplacementRule(pattern6185, replacement6185)
    pattern6186 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons1892, cons1893, cons338, cons88, cons137, cons274, cons1750, cons667)
    def replacement6186(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6186)
        return Dist((m + S(2)*p + S(3))/(S(2)*d1*d2*(p + S(1))), Int((f*x)**m*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1)), x), x) - Dist(b*c*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(S(2)*f*(p + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(1)/2), x), x) - Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(S(2)*d1*d2*f*(p + S(1))), x)
    rule6186 = ReplacementRule(pattern6186, replacement6186)
    pattern6187 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons1892, cons1893, cons338, cons88, cons137, cons274, cons1749)
    def replacement6187(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6187)
        return Dist((m + S(2)*p + S(3))/(S(2)*d1*d2*(p + S(1))), Int((f*x)**m*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1)), x), x) - Dist(b*c*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(S(2)*f*(p + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) - Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(S(2)*d1*d2*f*(p + S(1))), x)
    rule6187 = ReplacementRule(pattern6187, replacement6187)
    pattern6188 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1778, cons93, cons88, cons166, cons17)
    def replacement6188(m, f, b, d, a, n, c, x, e):
        rubi.append(6188)
        return -Dist(f**S(2)*(m + S(-1))/(c**S(2)*m), Int((f*x)**(m + S(-2))*(a + b*asinh(c*x))**n/sqrt(d + e*x**S(2)), x), x) - Dist(b*f*n*sqrt(c**S(2)*x**S(2) + S(1))/(c*m*sqrt(d + e*x**S(2))), Int((f*x)**(m + S(-1))*(a + b*asinh(c*x))**(n + S(-1)), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*asinh(c*x))**n*sqrt(d + e*x**S(2))/(e*m), x)
    rule6188 = ReplacementRule(pattern6188, replacement6188)
    pattern6189 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons1892, cons1893, cons93, cons88, cons166, cons17)
    def replacement6189(d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6189)
        return Dist(f**S(2)*(m + S(-1))/(c**S(2)*m), Int((f*x)**(m + S(-2))*(a + b*acosh(c*x))**n/(sqrt(d1 + e1*x)*sqrt(d2 + e2*x)), x), x) + Dist(b*f*n*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(c*d1*d2*m*sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(-1)), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acosh(c*x))**n*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)/(e1*e2*m), x)
    rule6189 = ReplacementRule(pattern6189, replacement6189)
    pattern6190 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1778, cons268, cons148, cons17)
    def replacement6190(m, b, d, a, n, c, x, e):
        rubi.append(6190)
        return Dist(c**(-m + S(-1))/sqrt(d), Subst(Int((a + b*x)**n*sinh(x)**m, x), x, asinh(c*x)), x)
    rule6190 = ReplacementRule(pattern6190, replacement6190)
    pattern6191 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1892, cons1893, cons148, cons1894, cons1895, cons17)
    def replacement6191(d2, m, b, e2, a, n, c, d1, e1, x):
        rubi.append(6191)
        return Dist(c**(-m + S(-1))/sqrt(-d1*d2), Subst(Int((a + b*x)**n*cosh(x)**m, x), x, acosh(c*x)), x)
    rule6191 = ReplacementRule(pattern6191, replacement6191)
    pattern6192 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1778, cons268, cons18)
    def replacement6192(m, f, b, d, a, c, x, e):
        rubi.append(6192)
        return Simp((f*x)**(m + S(1))*(a + b*asinh(c*x))*Hypergeometric2F1(S(1)/2, m/S(2) + S(1)/2, m/S(2) + S(3)/2, -c**S(2)*x**S(2))/(sqrt(d)*f*(m + S(1))), x) - Simp(b*c*(f*x)**(m + S(2))*HypergeometricPFQ(List(S(1), m/S(2) + S(1), m/S(2) + S(1)), List(m/S(2) + S(3)/2, m/S(2) + S(2)), -c**S(2)*x**S(2))/(sqrt(d)*f**S(2)*(m + S(1))*(m + S(2))), x)
    rule6192 = ReplacementRule(pattern6192, replacement6192)
    pattern6193 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons1892, cons1893, cons1894, cons1895, cons18)
    def replacement6193(d2, m, f, b, e2, a, c, d1, e1, x):
        rubi.append(6193)
        return Simp(b*c*(f*x)**(m + S(2))*HypergeometricPFQ(List(S(1), m/S(2) + S(1), m/S(2) + S(1)), List(m/S(2) + S(3)/2, m/S(2) + S(2)), c**S(2)*x**S(2))/(f**S(2)*sqrt(-d1*d2)*(m + S(1))*(m + S(2))), x) + Simp((f*x)**(m + S(1))*(a + b*acosh(c*x))*sqrt(-c**S(2)*x**S(2) + S(1))*Hypergeometric2F1(S(1)/2, m/S(2) + S(1)/2, m/S(2) + S(3)/2, c**S(2)*x**S(2))/(f*sqrt(d1 + e1*x)*sqrt(d2 + e2*x)*(m + S(1))), x)
    rule6193 = ReplacementRule(pattern6193, replacement6193)
    pattern6194 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1778, cons87, cons88, cons1738, cons1750)
    def replacement6194(m, f, b, d, a, n, c, x, e):
        rubi.append(6194)
        return Dist(sqrt(c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((f*x)**m*(a + b*asinh(c*x))**n/sqrt(c**S(2)*x**S(2) + S(1)), x), x)
    rule6194 = ReplacementRule(pattern6194, replacement6194)
    pattern6195 = Pattern(Integral((x_*WC('f', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons1892, cons1893, cons87, cons88, cons1896, cons1750)
    def replacement6195(d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6195)
        return Dist(sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(sqrt(d1 + e1*x)*sqrt(d2 + e2*x)), Int((f*x)**m*(a + b*acosh(c*x))**n/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x)
    rule6195 = ReplacementRule(pattern6195, replacement6195)
    pattern6196 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons1737, cons93, cons88, cons166, cons238, cons38, cons17)
    def replacement6196(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6196)
        return Dist(f**S(2)*(m + S(-1))/(c**S(2)*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-2))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**p, x), x) - Dist(b*f*n*(-d)**p/(c*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acosh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(e*(m + S(2)*p + S(1))), x)
    rule6196 = ReplacementRule(pattern6196, replacement6196)
    pattern6197 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons1778, cons93, cons88, cons166, cons238, cons17)
    def replacement6197(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6197)
        return -Dist(f**S(2)*(m + S(-1))/(c**S(2)*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-2))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**p, x), x) - Dist(b*d**IntPart(p)*f*n*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(c*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-1))*(a + b*asinh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*asinh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(e*(m + S(2)*p + S(1))), x)
    rule6197 = ReplacementRule(pattern6197, replacement6197)
    pattern6198 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons5, cons1892, cons1893, cons93, cons88, cons166, cons238, cons17, cons667)
    def replacement6198(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6198)
        return Dist(f**S(2)*(m + S(-1))/(c**S(2)*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-2))*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p, x), x) - Dist(b*f*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(c*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(-1))*(c**S(2)*x**S(2) + S(-1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(e1*e2*(m + S(2)*p + S(1))), x)
    rule6198 = ReplacementRule(pattern6198, replacement6198)
    pattern6199 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons5, cons1892, cons1893, cons93, cons88, cons166, cons238, cons17)
    def replacement6199(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6199)
        return Dist(f**S(2)*(m + S(-1))/(c**S(2)*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-2))*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p, x), x) - Dist(b*f*n*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(c*(m + S(2)*p + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(-1))*(c*x + S(-1))**(p + S(1)/2)*(c*x + S(1))**(p + S(1)/2), x), x) + Simp(f*(f*x)**(m + S(-1))*(a + b*acosh(c*x))**n*(d1 + e1*x)**(p + S(1))*(d2 + e2*x)**(p + S(1))/(e1*e2*(m + S(2)*p + S(1))), x)
    rule6199 = ReplacementRule(pattern6199, replacement6199)
    pattern6200 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1737, cons87, cons89, cons237, cons38)
    def replacement6200(p, m, f, b, d, a, c, n, x, e):
        rubi.append(6200)
        return Dist(f*m*(-d)**p/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**m*(a + b*acosh(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6200 = ReplacementRule(pattern6200, replacement6200)
    pattern6201 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1778, cons87, cons89, cons237)
    def replacement6201(p, m, f, b, d, a, c, n, x, e):
        rubi.append(6201)
        return -Dist(d**IntPart(p)*f*m*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*asinh(c*x))**(n + S(1))*(c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**m*(a + b*asinh(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule6201 = ReplacementRule(pattern6201, replacement6201)
    pattern6202 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons5, cons1892, cons1893, cons87, cons89, cons237, cons347)
    def replacement6202(p, d2, m, f, b, e2, a, c, n, d1, e1, x):
        rubi.append(6202)
        return Dist(f*m*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(1))*(c**S(2)*x**S(2) + S(-1))**(p + S(-1)/2), x), x) + Simp((f*x)**m*(a + b*acosh(c*x))**(n + S(1))*(d1 + e1*x)**p*(d2 + e2*x)**p*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6202 = ReplacementRule(pattern6202, replacement6202)
    pattern6203 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons5, cons1892, cons1893, cons87, cons89, cons237)
    def replacement6203(p, d2, m, f, b, e2, a, c, n, d1, e1, x):
        rubi.append(6203)
        return Dist(f*m*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**m*(a + b*acosh(c*x))**(n + S(1))*(d1 + e1*x)**p*(d2 + e2*x)**p*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6203 = ReplacementRule(pattern6203, replacement6203)
    pattern6204 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1778, cons87, cons89, cons268)
    def replacement6204(m, f, b, d, a, c, n, x, e):
        rubi.append(6204)
        return -Dist(f*m/(b*c*sqrt(d)*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*asinh(c*x))**(n + S(1)), x), x) + Simp((f*x)**m*(a + b*asinh(c*x))**(n + S(1))/(b*c*sqrt(d)*(n + S(1))), x)
    rule6204 = ReplacementRule(pattern6204, replacement6204)
    pattern6205 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons1892, cons1893, cons87, cons89, cons1894, cons1895)
    def replacement6205(d2, m, f, b, e2, a, c, n, d1, e1, x):
        rubi.append(6205)
        return -Dist(f*m/(b*c*sqrt(-d1*d2)*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(1)), x), x) + Simp((f*x)**m*(a + b*acosh(c*x))**(n + S(1))/(b*c*sqrt(-d1*d2)*(n + S(1))), x)
    rule6205 = ReplacementRule(pattern6205, replacement6205)
    pattern6206 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1778, cons87, cons89, cons1738)
    def replacement6206(m, f, b, d, a, c, n, x, e):
        rubi.append(6206)
        return Dist(sqrt(c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((f*x)**m*(a + b*asinh(c*x))**n/sqrt(c**S(2)*x**S(2) + S(1)), x), x)
    rule6206 = ReplacementRule(pattern6206, replacement6206)
    pattern6207 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons1892, cons1893, cons87, cons89, cons1896)
    def replacement6207(d2, m, f, b, e2, a, c, n, d1, e1, x):
        rubi.append(6207)
        return Dist(sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(sqrt(d1 + e1*x)*sqrt(d2 + e2*x)), Int((f*x)**m*(a + b*acosh(c*x))**n/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x)
    rule6207 = ReplacementRule(pattern6207, replacement6207)
    pattern6208 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1737, cons87, cons89, cons17, cons1751, cons128)
    def replacement6208(p, m, f, b, d, a, c, n, x, e):
        rubi.append(6208)
        return Dist(f*m*(-d)**p/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) - Dist(c*(-d)**p*(m + S(2)*p + S(1))/(b*f*(n + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(1))*(c*x + S(-1))**(p + S(-1)/2)*(c*x + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**m*(a + b*acosh(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6208 = ReplacementRule(pattern6208, replacement6208)
    pattern6209 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1778, cons87, cons89, cons17, cons1751, cons1739)
    def replacement6209(p, m, f, b, d, a, c, n, x, e):
        rubi.append(6209)
        return -Dist(d**IntPart(p)*f*m*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*asinh(c*x))**(n + S(1))*(c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) - Dist(c*d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p))*(m + S(2)*p + S(1))/(b*f*(n + S(1))), Int((f*x)**(m + S(1))*(a + b*asinh(c*x))**(n + S(1))*(c**S(2)*x**S(2) + S(1))**(p + S(-1)/2), x), x) + Simp((f*x)**m*(a + b*asinh(c*x))**(n + S(1))*(d + e*x**S(2))**p*sqrt(c**S(2)*x**S(2) + S(1))/(b*c*(n + S(1))), x)
    rule6209 = ReplacementRule(pattern6209, replacement6209)
    pattern6210 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons1892, cons1893, cons87, cons89, cons17, cons1751, cons961)
    def replacement6210(p, d2, m, f, b, e2, a, c, n, d1, e1, x):
        rubi.append(6210)
        return Dist(f*m*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))/(b*c*(n + S(1))), Int((f*x)**(m + S(-1))*(a + b*acosh(c*x))**(n + S(1))*(c**S(2)*x**S(2) + S(-1))**(p + S(-1)/2), x), x) - Dist(c*(-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p))*(m + S(2)*p + S(1))/(b*f*(n + S(1))), Int((f*x)**(m + S(1))*(a + b*acosh(c*x))**(n + S(1))*(c**S(2)*x**S(2) + S(-1))**(p + S(-1)/2), x), x) + Simp((f*x)**m*(a + b*acosh(c*x))**(n + S(1))*(d1 + e1*x)**p*(d2 + e2*x)**p*sqrt(c*x + S(-1))*sqrt(c*x + S(1))/(b*c*(n + S(1))), x)
    rule6210 = ReplacementRule(pattern6210, replacement6210)
    pattern6211 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons246, cons1752, cons62, cons1740)
    def replacement6211(p, m, b, d, a, n, c, x, e):
        rubi.append(6211)
        return Dist(c**(-m + S(-1))*d**p, Subst(Int((a + b*x)**n*sinh(x)**m*cosh(x)**(S(2)*p + S(1)), x), x, asinh(c*x)), x)
    rule6211 = ReplacementRule(pattern6211, replacement6211)
    pattern6212 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons128, cons62)
    def replacement6212(p, m, b, d, a, n, c, x, e):
        rubi.append(6212)
        return Dist(c**(-m + S(-1))*(-d)**p, Subst(Int((a + b*x)**n*sinh(x)**(S(2)*p + S(1))*cosh(x)**m, x), x, acosh(c*x)), x)
    rule6212 = ReplacementRule(pattern6212, replacement6212)
    pattern6213 = Pattern(Integral(x_**WC('m', S(1))*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons4, cons1892, cons1893, cons667, cons1752, cons62, cons1897)
    def replacement6213(p, d2, m, b, e2, a, n, c, d1, e1, x):
        rubi.append(6213)
        return Dist(c**(-m + S(-1))*(-d1*d2)**p, Subst(Int((a + b*x)**n*sinh(x)**(S(2)*p + S(1))*cosh(x)**m, x), x, acosh(c*x)), x)
    rule6213 = ReplacementRule(pattern6213, replacement6213)
    pattern6214 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons246, cons1752, cons62, cons1741)
    def replacement6214(p, m, b, d, a, c, n, x, e):
        rubi.append(6214)
        return Dist(d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int(x**m*(a + b*asinh(c*x))**n*(c**S(2)*x**S(2) + S(1))**p, x), x)
    rule6214 = ReplacementRule(pattern6214, replacement6214)
    pattern6215 = Pattern(Integral(x_**WC('m', S(1))*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons4, cons1892, cons1893, cons246, cons1752, cons62, cons1901)
    def replacement6215(p, d2, m, b, e2, a, n, c, d1, e1, x):
        rubi.append(6215)
        return Dist((-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p)), Int(x**m*(a + b*acosh(c*x))**n*(c*x + S(-1))**p*(c*x + S(1))**p, x), x)
    rule6215 = ReplacementRule(pattern6215, replacement6215)
    pattern6216 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1778, cons268, cons961, cons1753, cons17, cons1754)
    def replacement6216(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6216)
        return Int(ExpandIntegrand((a + b*asinh(c*x))**n/sqrt(d + e*x**S(2)), (f*x)**m*(d + e*x**S(2))**(p + S(1)/2), x), x)
    rule6216 = ReplacementRule(pattern6216, replacement6216)
    pattern6217 = Pattern(Integral((x_*WC('f', S(1)))**m_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons4, cons1892, cons1893, cons1894, cons1895, cons961, cons1753, cons17, cons1754)
    def replacement6217(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6217)
        return Int(ExpandIntegrand((a + b*acosh(c*x))**n/(sqrt(d1 + e1*x)*sqrt(d2 + e2*x)), (f*x)**m*(d1 + e1*x)**(p + S(1)/2)*(d2 + e2*x)**(p + S(1)/2), x), x)
    rule6217 = ReplacementRule(pattern6217, replacement6217)
    pattern6218 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1742, cons66, cons1902)
    def replacement6218(m, f, b, d, a, c, x, e):
        rubi.append(6218)
        return -Dist(b*c/(f*(m + S(1))*(m + S(3))), Int((f*x)**(m + S(1))*(d*(m + S(3)) + e*x**S(2)*(m + S(1)))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) + Simp(d*(f*x)**(m + S(1))*(a + b*acosh(c*x))/(f*(m + S(1))), x) + Simp(e*(f*x)**(m + S(3))*(a + b*acosh(c*x))/(f**S(3)*(m + S(3))), x)
    rule6218 = ReplacementRule(pattern6218, replacement6218)
    pattern6219 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1898, cons54)
    def replacement6219(p, b, d, a, c, x, e):
        rubi.append(6219)
        return -Dist(b*c/(S(2)*e*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*asinh(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6219 = ReplacementRule(pattern6219, replacement6219)
    pattern6220 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1742, cons54)
    def replacement6220(p, b, d, a, c, x, e):
        rubi.append(6220)
        return -Dist(b*c/(S(2)*e*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) + Simp((a + b*acosh(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6220 = ReplacementRule(pattern6220, replacement6220)
    def With6221(p, m, f, b, d, a, c, x, e):
        u = IntHide((f*x)**m*(d + e*x**S(2))**p, x)
        rubi.append(6221)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asinh(c*x), u, x)
    pattern6221 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1898, cons38, cons1755)
    rule6221 = ReplacementRule(pattern6221, With6221)
    def With6222(p, m, f, b, d, a, c, x, e):
        u = IntHide((f*x)**m*(d + e*x**S(2))**p, x)
        rubi.append(6222)
        return -Dist(b*c, Int(SimplifyIntegrand(u/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x), x) + Dist(a + b*acosh(c*x), u, x)
    pattern6222 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1742, cons38, cons1755)
    rule6222 = ReplacementRule(pattern6222, With6222)
    pattern6223 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1898, cons148, cons38, cons17)
    def replacement6223(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6223)
        return Int(ExpandIntegrand((a + b*asinh(c*x))**n, (f*x)**m*(d + e*x**S(2))**p, x), x)
    rule6223 = ReplacementRule(pattern6223, replacement6223)
    pattern6224 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1742, cons148, cons38, cons17)
    def replacement6224(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6224)
        return Int(ExpandIntegrand((a + b*acosh(c*x))**n, (f*x)**m*(d + e*x**S(2))**p, x), x)
    rule6224 = ReplacementRule(pattern6224, replacement6224)
    pattern6225 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons1756)
    def replacement6225(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6225)
        return Int((f*x)**m*(a + b*asinh(c*x))**n*(d + e*x**S(2))**p, x)
    rule6225 = ReplacementRule(pattern6225, replacement6225)
    pattern6226 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons38)
    def replacement6226(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6226)
        return Int((f*x)**m*(a + b*acosh(c*x))**n*(d + e*x**S(2))**p, x)
    rule6226 = ReplacementRule(pattern6226, replacement6226)
    pattern6227 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d1_ + x_*WC('e1', S(1)))**WC('p', S(1))*(d2_ + x_*WC('e2', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons21, cons4, cons5, cons1903)
    def replacement6227(p, d2, m, f, b, e2, a, n, c, d1, e1, x):
        rubi.append(6227)
        return Int((f*x)**m*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p, x)
    rule6227 = ReplacementRule(pattern6227, replacement6227)
    pattern6228 = Pattern(Integral((x_*WC('h', S(1)))**WC('m', S(1))*(d_ + x_*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons5, cons336, cons1900, cons147)
    def replacement6228(p, m, g, b, f, d, a, n, c, x, h, e):
        rubi.append(6228)
        return Dist((d + e*x)**FracPart(p)*(f + g*x)**FracPart(p)*(d*f + e*g*x**S(2))**(-FracPart(p)), Int((h*x)**m*(a + b*asinh(c*x))**n*(d*f + e*g*x**S(2))**p, x), x)
    rule6228 = ReplacementRule(pattern6228, replacement6228)
    pattern6229 = Pattern(Integral((x_*WC('f', S(1)))**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons1737, cons147)
    def replacement6229(p, m, f, b, d, a, n, c, x, e):
        rubi.append(6229)
        return Dist((-d)**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p)), Int((f*x)**m*(a + b*acosh(c*x))**n*(c*x + S(-1))**p*(c*x + S(1))**p, x), x)
    rule6229 = ReplacementRule(pattern6229, replacement6229)
    pattern6230 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons148)
    def replacement6230(b, d, a, n, c, x, e):
        rubi.append(6230)
        return Subst(Int((a + b*x)**n*cosh(x)/(c*d + e*sinh(x)), x), x, asinh(c*x))
    rule6230 = ReplacementRule(pattern6230, replacement6230)
    pattern6231 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons148)
    def replacement6231(b, d, a, n, c, x, e):
        rubi.append(6231)
        return Subst(Int((a + b*x)**n*sinh(x)/(c*d + e*cosh(x)), x), x, acosh(c*x))
    rule6231 = ReplacementRule(pattern6231, replacement6231)
    pattern6232 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons148, cons66)
    def replacement6232(m, b, d, a, n, c, x, e):
        rubi.append(6232)
        return -Dist(b*c*n/(e*(m + S(1))), Int((a + b*asinh(c*x))**(n + S(-1))*(d + e*x)**(m + S(1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*asinh(c*x))**n*(d + e*x)**(m + S(1))/(e*(m + S(1))), x)
    rule6232 = ReplacementRule(pattern6232, replacement6232)
    pattern6233 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons148, cons66)
    def replacement6233(m, b, d, a, n, c, x, e):
        rubi.append(6233)
        return -Dist(b*c*n/(e*(m + S(1))), Int((a + b*acosh(c*x))**(n + S(-1))*(d + e*x)**(m + S(1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x) + Simp((a + b*acosh(c*x))**n*(d + e*x)**(m + S(1))/(e*(m + S(1))), x)
    rule6233 = ReplacementRule(pattern6233, replacement6233)
    pattern6234 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons62, cons87, cons89)
    def replacement6234(m, b, d, a, c, n, x, e):
        rubi.append(6234)
        return Int(ExpandIntegrand((a + b*asinh(c*x))**n*(d + e*x)**m, x), x)
    rule6234 = ReplacementRule(pattern6234, replacement6234)
    pattern6235 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons62, cons87, cons89)
    def replacement6235(m, b, d, a, c, n, x, e):
        rubi.append(6235)
        return Int(ExpandIntegrand((a + b*acosh(c*x))**n*(d + e*x)**m, x), x)
    rule6235 = ReplacementRule(pattern6235, replacement6235)
    pattern6236 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons62)
    def replacement6236(m, b, d, a, n, c, x, e):
        rubi.append(6236)
        return Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*(c*d + e*sinh(x))**m*cosh(x), x), x, asinh(c*x)), x)
    rule6236 = ReplacementRule(pattern6236, replacement6236)
    pattern6237 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons62)
    def replacement6237(m, b, d, a, n, c, x, e):
        rubi.append(6237)
        return Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*(c*d + e*cosh(x))**m*sinh(x), x), x, acosh(c*x)), x)
    rule6237 = ReplacementRule(pattern6237, replacement6237)
    def With6238(b, Px, a, c, x):
        u = IntHide(Px, x)
        rubi.append(6238)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asinh(c*x), u, x)
    pattern6238 = Pattern(Integral(Px_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons925)
    rule6238 = ReplacementRule(pattern6238, With6238)
    def With6239(b, Px, a, c, x):
        u = IntHide(Px, x)
        rubi.append(6239)
        return -Dist(b*c*sqrt(-c**S(2)*x**S(2) + S(1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acosh(c*x), u, x)
    pattern6239 = Pattern(Integral(Px_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons925)
    rule6239 = ReplacementRule(pattern6239, With6239)
    pattern6240 = Pattern(Integral(Px_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons925)
    def replacement6240(b, Px, a, n, c, x):
        rubi.append(6240)
        return Int(ExpandIntegrand(Px*(a + b*asinh(c*x))**n, x), x)
    rule6240 = ReplacementRule(pattern6240, replacement6240)
    pattern6241 = Pattern(Integral(Px_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons925)
    def replacement6241(b, Px, a, n, c, x):
        rubi.append(6241)
        return Int(ExpandIntegrand(Px*(a + b*acosh(c*x))**n, x), x)
    rule6241 = ReplacementRule(pattern6241, replacement6241)
    def With6242(m, b, Px, d, a, c, x, e):
        u = IntHide(Px*(d + e*x)**m, x)
        rubi.append(6242)
        return -Dist(b*c, Int(SimplifyIntegrand(u/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asinh(c*x), u, x)
    pattern6242 = Pattern(Integral(Px_*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons925)
    rule6242 = ReplacementRule(pattern6242, With6242)
    def With6243(m, b, Px, d, a, c, x, e):
        u = IntHide(Px*(d + e*x)**m, x)
        rubi.append(6243)
        return -Dist(b*c*sqrt(-c**S(2)*x**S(2) + S(1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int(SimplifyIntegrand(u/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acosh(c*x), u, x)
    pattern6243 = Pattern(Integral(Px_*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons925)
    rule6243 = ReplacementRule(pattern6243, With6243)
    def With6244(p, m, f, b, g, d, a, c, n, x, e):
        u = IntHide((d + e*x)**m*(f + g*x)**p, x)
        rubi.append(6244)
        return -Dist(b*c*n, Int(SimplifyIntegrand(u*(a + b*asinh(c*x))**(n + S(-1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist((a + b*asinh(c*x))**n, u, x)
    pattern6244 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons464, cons84, cons1757)
    rule6244 = ReplacementRule(pattern6244, With6244)
    def With6245(p, m, f, b, g, d, a, c, n, x, e):
        u = IntHide((d + e*x)**m*(f + g*x)**p, x)
        rubi.append(6245)
        return -Dist(b*c*n, Int(SimplifyIntegrand(u*(a + b*acosh(c*x))**(n + S(-1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x), x) + Dist((a + b*acosh(c*x))**n, u, x)
    pattern6245 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons464, cons84, cons1757)
    rule6245 = ReplacementRule(pattern6245, With6245)
    def With6246(p, f, b, g, d, a, c, n, x, h, e):
        u = IntHide((f + g*x + h*x**S(2))**p/(d + e*x)**S(2), x)
        rubi.append(6246)
        return -Dist(b*c*n, Int(SimplifyIntegrand(u*(a + b*asinh(c*x))**(n + S(-1))/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist((a + b*asinh(c*x))**n, u, x)
    pattern6246 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_*(x_**S(2)*WC('h', S(1)) + x_*WC('g', S(1)) + WC('f', S(0)))**WC('p', S(1))/(d_ + x_*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons464, cons1758)
    rule6246 = ReplacementRule(pattern6246, With6246)
    def With6247(p, f, b, g, d, a, c, n, x, h, e):
        u = IntHide((f + g*x + h*x**S(2))**p/(d + e*x)**S(2), x)
        rubi.append(6247)
        return -Dist(b*c*n, Int(SimplifyIntegrand(u*(a + b*acosh(c*x))**(n + S(-1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), x), x), x) + Dist((a + b*acosh(c*x))**n, u, x)
    pattern6247 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_*(x_**S(2)*WC('h', S(1)) + x_*WC('g', S(1)) + WC('f', S(0)))**WC('p', S(1))/(d_ + x_*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons464, cons1758)
    rule6247 = ReplacementRule(pattern6247, With6247)
    pattern6248 = Pattern(Integral(Px_*(d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons925, cons148, cons17)
    def replacement6248(m, b, Px, d, a, n, c, x, e):
        rubi.append(6248)
        return Int(ExpandIntegrand(Px*(a + b*asinh(c*x))**n*(d + e*x)**m, x), x)
    rule6248 = ReplacementRule(pattern6248, replacement6248)
    pattern6249 = Pattern(Integral(Px_*(d_ + x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons925, cons148, cons17)
    def replacement6249(m, b, Px, d, a, n, c, x, e):
        rubi.append(6249)
        return Int(ExpandIntegrand(Px*(a + b*acosh(c*x))**n*(d + e*x)**m, x), x)
    rule6249 = ReplacementRule(pattern6249, replacement6249)
    def With6250(p, m, g, b, f, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p*(f + g*x)**m, x)
        rubi.append(6250)
        return -Dist(b*c, Int(Dist(S(1)/sqrt(c**S(2)*x**S(2) + S(1)), u, x), x), x) + Dist(a + b*asinh(c*x), u, x)
    pattern6250 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1778, cons17, cons719, cons268, cons168, cons1759)
    rule6250 = ReplacementRule(pattern6250, With6250)
    def With6251(p, d2, m, g, b, f, e2, a, c, d1, e1, x):
        u = IntHide((d1 + e1*x)**p*(d2 + e2*x)**p*(f + g*x)**m, x)
        rubi.append(6251)
        return -Dist(b*c, Int(Dist(S(1)/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), u, x), x), x) + Dist(a + b*acosh(c*x), u, x)
    pattern6251 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons1892, cons1893, cons17, cons719, cons1894, cons1895, cons168, cons1759)
    rule6251 = ReplacementRule(pattern6251, With6251)
    pattern6252 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1778, cons17, cons667, cons268, cons148, cons168, cons1760)
    def replacement6252(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(6252)
        return Int(ExpandIntegrand((a + b*asinh(c*x))**n*(d + e*x**S(2))**p, (f + g*x)**m, x), x)
    rule6252 = ReplacementRule(pattern6252, replacement6252)
    pattern6253 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons1892, cons1893, cons17, cons667, cons1894, cons1895, cons148, cons168, cons1760)
    def replacement6253(p, d2, m, g, b, f, e2, a, n, c, d1, e1, x):
        rubi.append(6253)
        return Int(ExpandIntegrand((a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p, (f + g*x)**m, x), x)
    rule6253 = ReplacementRule(pattern6253, replacement6253)
    pattern6254 = Pattern(Integral(sqrt(d_ + x_**S(2)*WC('e', S(1)))*(x_*WC('g', S(1)) + WC('f', S(0)))**m_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1778, cons17, cons268, cons148, cons267)
    def replacement6254(m, f, b, g, d, a, n, c, x, e):
        rubi.append(6254)
        return -Dist(S(1)/(b*c*sqrt(d)*(n + S(1))), Int((a + b*asinh(c*x))**(n + S(1))*(f + g*x)**(m + S(-1))*(d*g*m + S(2)*e*f*x + e*g*x**S(2)*(m + S(2))), x), x) + Simp((a + b*asinh(c*x))**(n + S(1))*(d + e*x**S(2))*(f + g*x)**m/(b*c*sqrt(d)*(n + S(1))), x)
    rule6254 = ReplacementRule(pattern6254, replacement6254)
    pattern6255 = Pattern(Integral(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))*(f_ + x_*WC('g', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons1892, cons1893, cons17, cons1894, cons1895, cons148, cons267)
    def replacement6255(d2, m, g, b, f, e2, a, n, c, d1, e1, x):
        rubi.append(6255)
        return -Dist(S(1)/(b*c*sqrt(-d1*d2)*(n + S(1))), Int((a + b*acosh(c*x))**(n + S(1))*(f + g*x)**(m + S(-1))*(d1*d2*g*m + S(2)*e1*e2*f*x + e1*e2*g*x**S(2)*(m + S(2))), x), x) + Simp((a + b*acosh(c*x))**(n + S(1))*(f + g*x)**m*(d1*d2 + e1*e2*x**S(2))/(b*c*sqrt(-d1*d2)*(n + S(1))), x)
    rule6255 = ReplacementRule(pattern6255, replacement6255)
    pattern6256 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1778, cons17, cons961, cons268, cons148)
    def replacement6256(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(6256)
        return Int(ExpandIntegrand((a + b*asinh(c*x))**n*sqrt(d + e*x**S(2)), (d + e*x**S(2))**(p + S(-1)/2)*(f + g*x)**m, x), x)
    rule6256 = ReplacementRule(pattern6256, replacement6256)
    pattern6257 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons1892, cons1893, cons17, cons961, cons1894, cons1895, cons148)
    def replacement6257(p, d2, m, g, b, f, e2, a, n, c, d1, e1, x):
        rubi.append(6257)
        return Int(ExpandIntegrand((a + b*acosh(c*x))**n*sqrt(d1 + e1*x)*sqrt(d2 + e2*x), (d1 + e1*x)**(p + S(-1)/2)*(d2 + e2*x)**(p + S(-1)/2)*(f + g*x)**m, x), x)
    rule6257 = ReplacementRule(pattern6257, replacement6257)
    pattern6258 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1778, cons17, cons717, cons268, cons148, cons267)
    def replacement6258(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(6258)
        return -Dist(S(1)/(b*c*sqrt(d)*(n + S(1))), Int(ExpandIntegrand((a + b*asinh(c*x))**(n + S(1))*(f + g*x)**(m + S(-1)), (d + e*x**S(2))**(p + S(-1)/2)*(d*g*m + e*f*x*(S(2)*p + S(1)) + e*g*x**S(2)*(m + S(2)*p + S(1))), x), x), x) + Simp((a + b*asinh(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1)/2)*(f + g*x)**m/(b*c*sqrt(d)*(n + S(1))), x)
    rule6258 = ReplacementRule(pattern6258, replacement6258)
    pattern6259 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons1892, cons1893, cons17, cons717, cons1894, cons1895, cons148, cons267)
    def replacement6259(p, d2, m, g, b, f, e2, a, n, c, d1, e1, x):
        rubi.append(6259)
        return -Dist(S(1)/(b*c*sqrt(-d1*d2)*(n + S(1))), Int(ExpandIntegrand((a + b*acosh(c*x))**(n + S(1))*(f + g*x)**(m + S(-1)), (d1 + e1*x)**(p + S(-1)/2)*(d2 + e2*x)**(p + S(-1)/2)*(d1*d2*g*m + e1*e2*f*x*(S(2)*p + S(1)) + e1*e2*g*x**S(2)*(m + S(2)*p + S(1))), x), x), x) + Simp((a + b*acosh(c*x))**(n + S(1))*(d1 + e1*x)**(p + S(1)/2)*(d2 + e2*x)**(p + S(1)/2)*(f + g*x)**m/(b*c*sqrt(-d1*d2)*(n + S(1))), x)
    rule6259 = ReplacementRule(pattern6259, replacement6259)
    pattern6260 = Pattern(Integral((f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1778, cons17, cons268, cons168, cons87, cons89)
    def replacement6260(m, g, b, f, d, a, c, n, x, e):
        rubi.append(6260)
        return -Dist(g*m/(b*c*sqrt(d)*(n + S(1))), Int((a + b*asinh(c*x))**(n + S(1))*(f + g*x)**(m + S(-1)), x), x) + Simp((a + b*asinh(c*x))**(n + S(1))*(f + g*x)**m/(b*c*sqrt(d)*(n + S(1))), x)
    rule6260 = ReplacementRule(pattern6260, replacement6260)
    pattern6261 = Pattern(Integral((f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons1892, cons1893, cons17, cons1894, cons1895, cons168, cons87, cons89)
    def replacement6261(d2, m, g, b, f, e2, a, c, n, d1, e1, x):
        rubi.append(6261)
        return -Dist(g*m/(b*c*sqrt(-d1*d2)*(n + S(1))), Int((a + b*acosh(c*x))**(n + S(1))*(f + g*x)**(m + S(-1)), x), x) + Simp((a + b*acosh(c*x))**(n + S(1))*(f + g*x)**m/(b*c*sqrt(-d1*d2)*(n + S(1))), x)
    rule6261 = ReplacementRule(pattern6261, replacement6261)
    pattern6262 = Pattern(Integral((f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons1778, cons17, cons268, cons1761)
    def replacement6262(m, g, b, f, d, a, n, c, x, e):
        rubi.append(6262)
        return Dist(c**(-m + S(-1))/sqrt(d), Subst(Int((a + b*x)**n*(c*f + g*sinh(x))**m, x), x, asinh(c*x)), x)
    rule6262 = ReplacementRule(pattern6262, replacement6262)
    pattern6263 = Pattern(Integral((f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons4, cons1892, cons1893, cons17, cons1894, cons1895, cons1761)
    def replacement6263(d2, m, g, b, f, e2, a, n, c, d1, e1, x):
        rubi.append(6263)
        return Dist(c**(-m + S(-1))/sqrt(-d1*d2), Subst(Int((a + b*x)**n*(c*f + g*cosh(x))**m, x), x, acosh(c*x)), x)
    rule6263 = ReplacementRule(pattern6263, replacement6263)
    pattern6264 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1778, cons17, cons719, cons268, cons148)
    def replacement6264(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(6264)
        return Int(ExpandIntegrand((a + b*asinh(c*x))**n/sqrt(d + e*x**S(2)), (d + e*x**S(2))**(p + S(1)/2)*(f + g*x)**m, x), x)
    rule6264 = ReplacementRule(pattern6264, replacement6264)
    pattern6265 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons1892, cons1893, cons17, cons719, cons1894, cons1895, cons148)
    def replacement6265(p, d2, m, g, b, f, e2, a, n, c, d1, e1, x):
        rubi.append(6265)
        return Int(ExpandIntegrand((a + b*acosh(c*x))**n/(sqrt(d1 + e1*x)*sqrt(d2 + e2*x)), (d1 + e1*x)**(p + S(1)/2)*(d2 + e2*x)**(p + S(1)/2)*(f + g*x)**m, x), x)
    rule6265 = ReplacementRule(pattern6265, replacement6265)
    pattern6266 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons1778, cons17, cons347, cons1738)
    def replacement6266(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(6266)
        return Dist(d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int((a + b*asinh(c*x))**n*(f + g*x)**m*(c**S(2)*x**S(2) + S(1))**p, x), x)
    rule6266 = ReplacementRule(pattern6266, replacement6266)
    pattern6267 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons1737, cons17, cons347)
    def replacement6267(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(6267)
        return Dist((-d)**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p)), Int((a + b*acosh(c*x))**n*(f + g*x)**m*(c*x + S(-1))**p*(c*x + S(1))**p, x), x)
    rule6267 = ReplacementRule(pattern6267, replacement6267)
    pattern6268 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons4, cons1892, cons1893, cons17, cons347, cons1896)
    def replacement6268(p, d2, m, g, b, f, e2, a, n, c, d1, e1, x):
        rubi.append(6268)
        return Dist((-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(-c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int((a + b*acosh(c*x))**n*(f + g*x)**m*(c*x + S(-1))**p*(c*x + S(1))**p, x), x)
    rule6268 = ReplacementRule(pattern6268, replacement6268)
    pattern6269 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*WC('h', S(1)))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons1778, cons268, cons148)
    def replacement6269(m, f, g, b, d, a, c, n, x, h, e):
        rubi.append(6269)
        return -Dist(g*m/(b*c*sqrt(d)*(n + S(1))), Int((a + b*asinh(c*x))**(n + S(1))/(f + g*x), x), x) + Simp((a + b*asinh(c*x))**(n + S(1))*log(h*(f + g*x)**m)/(b*c*sqrt(d)*(n + S(1))), x)
    rule6269 = ReplacementRule(pattern6269, replacement6269)
    pattern6270 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*WC('h', S(1)))/(sqrt(d1_ + x_*WC('e1', S(1)))*sqrt(d2_ + x_*WC('e2', S(1)))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons209, cons21, cons1892, cons1893, cons1894, cons1895, cons148)
    def replacement6270(d2, m, f, g, b, e2, a, c, n, d1, e1, x, h):
        rubi.append(6270)
        return -Dist(g*m/(b*c*sqrt(-d1*d2)*(n + S(1))), Int((a + b*acosh(c*x))**(n + S(1))/(f + g*x), x), x) + Simp((a + b*acosh(c*x))**(n + S(1))*log(h*(f + g*x)**m)/(b*c*sqrt(-d1*d2)*(n + S(1))), x)
    rule6270 = ReplacementRule(pattern6270, replacement6270)
    pattern6271 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*WC('h', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons1778, cons347, cons1738)
    def replacement6271(p, m, f, g, b, d, a, c, n, x, h, e):
        rubi.append(6271)
        return Dist(d**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(c**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int((a + b*asinh(c*x))**n*(c**S(2)*x**S(2) + S(1))**p*log(h*(f + g*x)**m), x), x)
    rule6271 = ReplacementRule(pattern6271, replacement6271)
    pattern6272 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*WC('h', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons1737, cons347)
    def replacement6272(p, m, f, g, b, d, a, c, n, x, h, e):
        rubi.append(6272)
        return Dist((-d)**IntPart(p)*(d + e*x**S(2))**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p)), Int((a + b*acosh(c*x))**n*(c*x + S(-1))**p*(c*x + S(1))**p*log(h*(f + g*x)**m), x), x)
    rule6272 = ReplacementRule(pattern6272, replacement6272)
    pattern6273 = Pattern(Integral((d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*WC('h', S(1))), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons209, cons21, cons4, cons1892, cons1893, cons347, cons1896)
    def replacement6273(p, d2, m, f, g, b, e2, a, c, n, d1, e1, x, h):
        rubi.append(6273)
        return Dist((-d1*d2)**IntPart(p)*(d1 + e1*x)**FracPart(p)*(d2 + e2*x)**FracPart(p)*(c*x + S(-1))**(-FracPart(p))*(c*x + S(1))**(-FracPart(p)), Int((a + b*acosh(c*x))**n*(c*x + S(-1))**p*(c*x + S(1))**p*log(h*(f + g*x)**m), x), x)
    rule6273 = ReplacementRule(pattern6273, replacement6273)
    def With6274(m, g, b, f, d, a, c, x, e):
        u = IntHide((d + e*x)**m*(f + g*x)**m, x)
        rubi.append(6274)
        return -Dist(b*c, Int(Dist(S(1)/sqrt(c**S(2)*x**S(2) + S(1)), u, x), x), x) + Dist(a + b*asinh(c*x), u, x)
    pattern6274 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(f_ + x_*WC('g', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1608)
    rule6274 = ReplacementRule(pattern6274, With6274)
    def With6275(m, g, b, f, d, a, c, x, e):
        u = IntHide((d + e*x)**m*(f + g*x)**m, x)
        rubi.append(6275)
        return -Dist(b*c, Int(Dist(S(1)/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), u, x), x), x) + Dist(a + b*acosh(c*x), u, x)
    pattern6275 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(f_ + x_*WC('g', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1608)
    rule6275 = ReplacementRule(pattern6275, With6275)
    pattern6276 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons17)
    def replacement6276(m, g, b, f, d, a, n, c, x, e):
        rubi.append(6276)
        return Int(ExpandIntegrand((a + b*asinh(c*x))**n, (d + e*x)**m*(f + g*x)**m, x), x)
    rule6276 = ReplacementRule(pattern6276, replacement6276)
    pattern6277 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(f_ + x_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons17)
    def replacement6277(m, g, b, f, d, a, n, c, x, e):
        rubi.append(6277)
        return Int(ExpandIntegrand((a + b*acosh(c*x))**n, (d + e*x)**m*(f + g*x)**m, x), x)
    rule6277 = ReplacementRule(pattern6277, replacement6277)
    def With6278(u, b, a, c, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        v = IntHide(u, x)
        if InverseFunctionFreeQ(v, x):
            return True
        return False
    pattern6278 = Pattern(Integral(u_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons14, CustomConstraint(With6278))
    def replacement6278(u, b, a, c, x):

        v = IntHide(u, x)
        rubi.append(6278)
        return -Dist(b*c, Int(SimplifyIntegrand(v/sqrt(c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*asinh(c*x), v, x)
    rule6278 = ReplacementRule(pattern6278, replacement6278)
    def With6279(u, b, a, c, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        v = IntHide(u, x)
        if InverseFunctionFreeQ(v, x):
            return True
        return False
    pattern6279 = Pattern(Integral(u_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons14, CustomConstraint(With6279))
    def replacement6279(u, b, a, c, x):

        v = IntHide(u, x)
        rubi.append(6279)
        return -Dist(b*c*sqrt(-c**S(2)*x**S(2) + S(1))/(sqrt(c*x + S(-1))*sqrt(c*x + S(1))), Int(SimplifyIntegrand(v/sqrt(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acosh(c*x), v, x)
    rule6279 = ReplacementRule(pattern6279, replacement6279)
    def With6280(p, b, Px, d, a, c, n, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(Px*(a + b*asinh(c*x))**n*(d + e*x**S(2))**p, x)
        if SumQ(u):
            return True
        return False
    pattern6280 = Pattern(Integral(Px_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons925, cons1778, cons347, CustomConstraint(With6280))
    def replacement6280(p, b, Px, d, a, c, n, x, e):

        u = ExpandIntegrand(Px*(a + b*asinh(c*x))**n*(d + e*x**S(2))**p, x)
        rubi.append(6280)
        return Int(u, x)
    rule6280 = ReplacementRule(pattern6280, replacement6280)
    def With6281(p, d2, b, Px, e2, a, c, n, d1, e1, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(Px*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p, x)
        if SumQ(u):
            return True
        return False
    pattern6281 = Pattern(Integral(Px_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons4, cons925, cons1892, cons1893, cons347, CustomConstraint(With6281))
    def replacement6281(p, d2, b, Px, e2, a, c, n, d1, e1, x):

        u = ExpandIntegrand(Px*(a + b*acosh(c*x))**n*(d1 + e1*x)**p*(d2 + e2*x)**p, x)
        rubi.append(6281)
        return Int(u, x)
    rule6281 = ReplacementRule(pattern6281, replacement6281)
    def With6282(p, m, g, b, f, Px, d, a, n, c, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(Px*(a + b*asinh(c*x))**n*(f + g*(d + e*x**S(2))**p)**m, x)
        if SumQ(u):
            return True
        return False
    pattern6282 = Pattern(Integral((f_ + (d_ + x_**S(2)*WC('e', S(1)))**p_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))*WC('Px', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons925, cons1778, cons961, cons150, CustomConstraint(With6282))
    def replacement6282(p, m, g, b, f, Px, d, a, n, c, x, e):

        u = ExpandIntegrand(Px*(a + b*asinh(c*x))**n*(f + g*(d + e*x**S(2))**p)**m, x)
        rubi.append(6282)
        return Int(u, x)
    rule6282 = ReplacementRule(pattern6282, replacement6282)
    def With6283(p, d2, m, g, b, f, Px, e2, a, n, c, d1, e1, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(Px*(a + b*acosh(c*x))**n*(f + g*(d1 + e1*x)**p*(d2 + e2*x)**p)**m, x)
        if SumQ(u):
            return True
        return False
    pattern6283 = Pattern(Integral((f_ + (d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*WC('g', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))*WC('Px', S(1)), x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons125, cons208, cons925, cons1892, cons1893, cons961, cons150, CustomConstraint(With6283))
    def replacement6283(p, d2, m, g, b, f, Px, e2, a, n, c, d1, e1, x):

        u = ExpandIntegrand(Px*(a + b*acosh(c*x))**n*(f + g*(d1 + e1*x)**p*(d2 + e2*x)**p)**m, x)
        rubi.append(6283)
        return Int(u, x)
    rule6283 = ReplacementRule(pattern6283, replacement6283)
    def With6284(x, c, n, RFx):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(asinh(c*x)**n, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern6284 = Pattern(Integral(RFx_*asinh(x_*WC('c', S(1)))**WC('n', S(1)), x_), cons7, cons1198, cons148, CustomConstraint(With6284))
    def replacement6284(x, c, n, RFx):

        u = ExpandIntegrand(asinh(c*x)**n, RFx, x)
        rubi.append(6284)
        return Int(u, x)
    rule6284 = ReplacementRule(pattern6284, replacement6284)
    def With6285(x, c, n, RFx):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(acosh(c*x)**n, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern6285 = Pattern(Integral(RFx_*acosh(x_*WC('c', S(1)))**WC('n', S(1)), x_), cons7, cons1198, cons148, CustomConstraint(With6285))
    def replacement6285(x, c, n, RFx):

        u = ExpandIntegrand(acosh(c*x)**n, RFx, x)
        rubi.append(6285)
        return Int(u, x)
    rule6285 = ReplacementRule(pattern6285, replacement6285)
    pattern6286 = Pattern(Integral(RFx_*(a_ + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons1198, cons148)
    def replacement6286(RFx, b, c, n, a, x):
        rubi.append(6286)
        return Int(ExpandIntegrand(RFx*(a + b*asinh(c*x))**n, x), x)
    rule6286 = ReplacementRule(pattern6286, replacement6286)
    pattern6287 = Pattern(Integral(RFx_*(a_ + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons1198, cons148)
    def replacement6287(RFx, b, c, n, a, x):
        rubi.append(6287)
        return Int(ExpandIntegrand(RFx*(a + b*acosh(c*x))**n, x), x)
    rule6287 = ReplacementRule(pattern6287, replacement6287)
    def With6288(p, RFx, d, c, n, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand((d + e*x**S(2))**p*asinh(c*x)**n, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern6288 = Pattern(Integral(RFx_*(d_ + x_**S(2)*WC('e', S(1)))**p_*asinh(x_*WC('c', S(1)))**WC('n', S(1)), x_), cons7, cons27, cons48, cons1198, cons148, cons1778, cons347, CustomConstraint(With6288))
    def replacement6288(p, RFx, d, c, n, x, e):

        u = ExpandIntegrand((d + e*x**S(2))**p*asinh(c*x)**n, RFx, x)
        rubi.append(6288)
        return Int(u, x)
    rule6288 = ReplacementRule(pattern6288, replacement6288)
    def With6289(p, RFx, d2, e2, c, n, d1, e1, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand((d1 + e1*x)**p*(d2 + e2*x)**p*acosh(c*x)**n, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern6289 = Pattern(Integral(RFx_*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_*acosh(x_*WC('c', S(1)))**WC('n', S(1)), x_), cons7, cons731, cons652, cons732, cons654, cons1198, cons148, cons1892, cons1893, cons347, CustomConstraint(With6289))
    def replacement6289(p, RFx, d2, e2, c, n, d1, e1, x):

        u = ExpandIntegrand((d1 + e1*x)**p*(d2 + e2*x)**p*acosh(c*x)**n, RFx, x)
        rubi.append(6289)
        return Int(u, x)
    rule6289 = ReplacementRule(pattern6289, replacement6289)
    pattern6290 = Pattern(Integral(RFx_*(a_ + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons1198, cons148, cons1778, cons347)
    def replacement6290(p, RFx, b, d, c, n, a, x, e):
        rubi.append(6290)
        return Int(ExpandIntegrand((d + e*x**S(2))**p, RFx*(a + b*asinh(c*x))**n, x), x)
    rule6290 = ReplacementRule(pattern6290, replacement6290)
    pattern6291 = Pattern(Integral(RFx_*(a_ + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))*(d1_ + x_*WC('e1', S(1)))**p_*(d2_ + x_*WC('e2', S(1)))**p_, x_), cons2, cons3, cons7, cons731, cons652, cons732, cons654, cons1198, cons148, cons1892, cons1893, cons347)
    def replacement6291(p, RFx, d2, b, e2, c, n, a, d1, e1, x):
        rubi.append(6291)
        return Int(ExpandIntegrand((d1 + e1*x)**p*(d2 + e2*x)**p, RFx*(a + b*acosh(c*x))**n, x), x)
    rule6291 = ReplacementRule(pattern6291, replacement6291)
    pattern6292 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(x_*WC('c', S(1))))**WC('n', S(1))*WC('u', S(1)), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement6292(u, b, a, n, c, x):
        rubi.append(6292)
        return Int(u*(a + b*asinh(c*x))**n, x)
    rule6292 = ReplacementRule(pattern6292, replacement6292)
    pattern6293 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_*WC('c', S(1))))**WC('n', S(1))*WC('u', S(1)), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement6293(u, b, a, n, c, x):
        rubi.append(6293)
        return Int(u*(a + b*acosh(c*x))**n, x)
    rule6293 = ReplacementRule(pattern6293, replacement6293)
    pattern6294 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1273)
    def replacement6294(b, d, c, a, n, x):
        rubi.append(6294)
        return Dist(S(1)/d, Subst(Int((a + b*asinh(x))**n, x), x, c + d*x), x)
    rule6294 = ReplacementRule(pattern6294, replacement6294)
    pattern6295 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1273)
    def replacement6295(b, d, c, a, n, x):
        rubi.append(6295)
        return Dist(S(1)/d, Subst(Int((a + b*acosh(x))**n, x), x, c + d*x), x)
    rule6295 = ReplacementRule(pattern6295, replacement6295)
    pattern6296 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement6296(m, f, b, d, a, n, c, x, e):
        rubi.append(6296)
        return Dist(S(1)/d, Subst(Int((a + b*asinh(x))**n*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule6296 = ReplacementRule(pattern6296, replacement6296)
    pattern6297 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement6297(m, f, b, d, a, n, c, x, e):
        rubi.append(6297)
        return Dist(S(1)/d, Subst(Int((a + b*acosh(x))**n*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule6297 = ReplacementRule(pattern6297, replacement6297)
    pattern6298 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons34, cons35, cons36, cons4, cons5, cons1830, cons1763)
    def replacement6298(B, C, p, b, d, a, n, c, x, A):
        rubi.append(6298)
        return Dist(S(1)/d, Subst(Int((a + b*asinh(x))**n*(C*x**S(2)/d**S(2) + C/d**S(2))**p, x), x, c + d*x), x)
    rule6298 = ReplacementRule(pattern6298, replacement6298)
    pattern6299 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons34, cons35, cons36, cons4, cons5, cons1762, cons1763)
    def replacement6299(B, C, p, b, d, a, n, c, x, A):
        rubi.append(6299)
        return Dist(S(1)/d, Subst(Int((a + b*acosh(x))**n*(C*x**S(2)/d**S(2) - C/d**S(2))**p, x), x, c + d*x), x)
    rule6299 = ReplacementRule(pattern6299, replacement6299)
    pattern6300 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons1830, cons1763)
    def replacement6300(B, C, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(6300)
        return Dist(S(1)/d, Subst(Int((a + b*asinh(x))**n*(C*x**S(2)/d**S(2) + C/d**S(2))**p*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule6300 = ReplacementRule(pattern6300, replacement6300)
    pattern6301 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons1762, cons1763)
    def replacement6301(B, C, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(6301)
        return Dist(S(1)/d, Subst(Int((a + b*acosh(x))**n*(C*x**S(2)/d**S(2) - C/d**S(2))**p*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule6301 = ReplacementRule(pattern6301, replacement6301)
    pattern6302 = Pattern(Integral(sqrt(WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons1904)
    def replacement6302(b, d, c, a, x):
        rubi.append(6302)
        return Simp(x*sqrt(a + b*asinh(c + d*x**S(2))), x) - Simp(sqrt(Pi)*x*(-c*sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*FresnelC(sqrt(-c/(Pi*b))*sqrt(a + b*asinh(c + d*x**S(2))))/(sqrt(-c/b)*(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2)))), x) + Simp(sqrt(Pi)*x*(c*sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*FresnelS(sqrt(-c/(Pi*b))*sqrt(a + b*asinh(c + d*x**S(2))))/(sqrt(-c/b)*(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2)))), x)
    rule6302 = ReplacementRule(pattern6302, replacement6302)
    pattern6303 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_**S(2)*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons1904, cons87, cons165)
    def replacement6303(b, d, c, a, n, x):
        rubi.append(6303)
        return Dist(S(4)*b**S(2)*n*(n + S(-1)), Int((a + b*asinh(c + d*x**S(2)))**(n + S(-2)), x), x) + Simp(x*(a + b*asinh(c + d*x**S(2)))**n, x) - Simp(S(2)*b*n*(a + b*asinh(c + d*x**S(2)))**(n + S(-1))*sqrt(S(2)*c*d*x**S(2) + d**S(2)*x**S(4))/(d*x), x)
    rule6303 = ReplacementRule(pattern6303, replacement6303)
    pattern6304 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons1904)
    def replacement6304(b, d, c, a, x):
        rubi.append(6304)
        return Simp(x*(-c*sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*SinhIntegral((a + b*asinh(c + d*x**S(2)))/(S(2)*b))/(S(2)*b*(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2)))), x) + Simp(x*(c*cosh(a/(S(2)*b)) - sinh(a/(S(2)*b)))*CoshIntegral((a + b*asinh(c + d*x**S(2)))/(S(2)*b))/(S(2)*b*(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2)))), x)
    rule6304 = ReplacementRule(pattern6304, replacement6304)
    pattern6305 = Pattern(Integral(S(1)/sqrt(WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons1904)
    def replacement6305(b, d, c, a, x):
        rubi.append(6305)
        return Simp(sqrt(S(2))*sqrt(Pi)*x*(c + S(-1))*(sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erf(sqrt(S(2))*sqrt(a + b*asinh(c + d*x**S(2)))/(S(2)*sqrt(b)))/(S(4)*sqrt(b)*(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2)))), x) + Simp(sqrt(S(2))*sqrt(Pi)*x*(c + S(1))*(-sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erfi(sqrt(S(2))*sqrt(a + b*asinh(c + d*x**S(2)))/(S(2)*sqrt(b)))/(S(4)*sqrt(b)*(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2)))), x)
    rule6305 = ReplacementRule(pattern6305, replacement6305)
    pattern6306 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_**S(2)*WC('d', S(1))))**(S(-3)/2), x_), cons2, cons3, cons7, cons27, cons1904)
    def replacement6306(b, d, c, a, x):
        rubi.append(6306)
        return -Simp(sqrt(S(2)*c*d*x**S(2) + d**S(2)*x**S(4))/(b*d*x*sqrt(a + b*asinh(c + d*x**S(2)))), x) - Simp(sqrt(Pi)*x*(-c/b)**(S(3)/2)*(-c*sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*FresnelC(sqrt(-c/(Pi*b))*sqrt(a + b*asinh(c + d*x**S(2))))/(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2))), x) + Simp(sqrt(Pi)*x*(-c/b)**(S(3)/2)*(c*sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*FresnelS(sqrt(-c/(Pi*b))*sqrt(a + b*asinh(c + d*x**S(2))))/(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2))), x)
    rule6306 = ReplacementRule(pattern6306, replacement6306)
    pattern6307 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_**S(2)*WC('d', S(1))))**(S(-2)), x_), cons2, cons3, cons7, cons27, cons1904)
    def replacement6307(b, d, c, a, x):
        rubi.append(6307)
        return Simp(x*(-c*sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*CoshIntegral((a + b*asinh(c + d*x**S(2)))/(S(2)*b))/(S(4)*b**S(2)*(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2)))), x) + Simp(x*(c*cosh(a/(S(2)*b)) - sinh(a/(S(2)*b)))*SinhIntegral((a + b*asinh(c + d*x**S(2)))/(S(2)*b))/(S(4)*b**S(2)*(c*sinh(asinh(c + d*x**S(2))/S(2)) + cosh(asinh(c + d*x**S(2))/S(2)))), x) - Simp(sqrt(S(2)*c*d*x**S(2) + d**S(2)*x**S(4))/(S(2)*b*d*x*(a + b*asinh(c + d*x**S(2)))), x)
    rule6307 = ReplacementRule(pattern6307, replacement6307)
    pattern6308 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asinh(c_ + x_**S(2)*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons1904, cons87, cons89, cons1442)
    def replacement6308(b, d, c, a, n, x):
        rubi.append(6308)
        return Dist(S(1)/(S(4)*b**S(2)*(n + S(1))*(n + S(2))), Int((a + b*asinh(c + d*x**S(2)))**(n + S(2)), x), x) - Simp(x*(a + b*asinh(c + d*x**S(2)))**(n + S(2))/(S(4)*b**S(2)*(n + S(1))*(n + S(2))), x) + Simp((a + b*asinh(c + d*x**S(2)))**(n + S(1))*sqrt(S(2)*c*d*x**S(2) + d**S(2)*x**S(4))/(S(2)*b*d*x*(n + S(1))), x)
    rule6308 = ReplacementRule(pattern6308, replacement6308)
    pattern6309 = Pattern(Integral(sqrt(WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(1))), x_), cons2, cons3, cons27, cons1765)
    def replacement6309(d, a, b, x):
        rubi.append(6309)
        return Simp(S(2)*sqrt(a + b*acosh(d*x**S(2) + S(1)))*sinh(acosh(d*x**S(2) + S(1))/S(2))**S(2)/(d*x), x) - Simp(sqrt(S(2))*sqrt(Pi)*sqrt(b)*(-sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erfi(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(1)))/(S(2)*sqrt(b)))*sinh(acosh(d*x**S(2) + S(1))/S(2))/(S(2)*d*x), x) + Simp(sqrt(S(2))*sqrt(Pi)*sqrt(b)*(sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erf(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(1)))/(S(2)*sqrt(b)))*sinh(acosh(d*x**S(2) + S(1))/S(2))/(S(2)*d*x), x)
    rule6309 = ReplacementRule(pattern6309, replacement6309)
    pattern6310 = Pattern(Integral(sqrt(WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(-1))), x_), cons2, cons3, cons27, cons1765)
    def replacement6310(d, a, b, x):
        rubi.append(6310)
        return Simp(S(2)*sqrt(a + b*acosh(d*x**S(2) + S(-1)))*cosh(acosh(d*x**S(2) + S(-1))/S(2))**S(2)/(d*x), x) - Simp(sqrt(S(2))*sqrt(Pi)*sqrt(b)*(-sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erfi(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*sqrt(b)))*cosh(acosh(d*x**S(2) + S(-1))/S(2))/(S(2)*d*x), x) - Simp(sqrt(S(2))*sqrt(Pi)*sqrt(b)*(sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erf(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*sqrt(b)))*cosh(acosh(d*x**S(2) + S(-1))/S(2))/(S(2)*d*x), x)
    rule6310 = ReplacementRule(pattern6310, replacement6310)
    pattern6311 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(c_ + x_**S(2)*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons1764, cons87, cons165)
    def replacement6311(b, d, c, a, n, x):
        rubi.append(6311)
        return Dist(S(4)*b**S(2)*n*(n + S(-1)), Int((a + b*acosh(c + d*x**S(2)))**(n + S(-2)), x), x) + Simp(x*(a + b*acosh(c + d*x**S(2)))**n, x) - Simp(S(2)*b*n*(a + b*acosh(c + d*x**S(2)))**(n + S(-1))*(S(2)*c*d*x**S(2) + d**S(2)*x**S(4))/(d*x*sqrt(c + d*x**S(2) + S(-1))*sqrt(c + d*x**S(2) + S(1))), x)
    rule6311 = ReplacementRule(pattern6311, replacement6311)
    pattern6312 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(1))), x_), cons2, cons3, cons27, cons1765)
    def replacement6312(d, a, b, x):
        rubi.append(6312)
        return Simp(sqrt(S(2))*x*CoshIntegral((a + b*acosh(d*x**S(2) + S(1)))/(S(2)*b))*cosh(a/(S(2)*b))/(S(2)*b*sqrt(d*x**S(2))), x) - Simp(sqrt(S(2))*x*SinhIntegral((a + b*acosh(d*x**S(2) + S(1)))/(S(2)*b))*sinh(a/(S(2)*b))/(S(2)*b*sqrt(d*x**S(2))), x)
    rule6312 = ReplacementRule(pattern6312, replacement6312)
    pattern6313 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(-1))), x_), cons2, cons3, cons27, cons1765)
    def replacement6313(d, a, b, x):
        rubi.append(6313)
        return -Simp(sqrt(S(2))*x*CoshIntegral((a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*b))*sinh(a/(S(2)*b))/(S(2)*b*sqrt(d*x**S(2))), x) + Simp(sqrt(S(2))*x*SinhIntegral((a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*b))*cosh(a/(S(2)*b))/(S(2)*b*sqrt(d*x**S(2))), x)
    rule6313 = ReplacementRule(pattern6313, replacement6313)
    pattern6314 = Pattern(Integral(S(1)/sqrt(WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(1))), x_), cons2, cons3, cons27, cons1765)
    def replacement6314(d, a, b, x):
        rubi.append(6314)
        return Simp(sqrt(S(2))*sqrt(Pi)*(-sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erfi(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(1)))/(S(2)*sqrt(b)))*sinh(acosh(d*x**S(2) + S(1))/S(2))/(S(2)*sqrt(b)*d*x), x) + Simp(sqrt(S(2))*sqrt(Pi)*(sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erf(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(1)))/(S(2)*sqrt(b)))*sinh(acosh(d*x**S(2) + S(1))/S(2))/(S(2)*sqrt(b)*d*x), x)
    rule6314 = ReplacementRule(pattern6314, replacement6314)
    pattern6315 = Pattern(Integral(S(1)/sqrt(WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(-1))), x_), cons2, cons3, cons27, cons1765)
    def replacement6315(d, a, b, x):
        rubi.append(6315)
        return Simp(sqrt(S(2))*sqrt(Pi)*(-sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erfi(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*sqrt(b)))*cosh(acosh(d*x**S(2) + S(-1))/S(2))/(S(2)*sqrt(b)*d*x), x) - Simp(sqrt(S(2))*sqrt(Pi)*(sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erf(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*sqrt(b)))*cosh(acosh(d*x**S(2) + S(-1))/S(2))/(S(2)*sqrt(b)*d*x), x)
    rule6315 = ReplacementRule(pattern6315, replacement6315)
    pattern6316 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(1)))**(S(-3)/2), x_), cons2, cons3, cons27, cons1765)
    def replacement6316(d, a, b, x):
        rubi.append(6316)
        return -Simp(sqrt(d*x**S(2))*sqrt(d*x**S(2) + S(2))/(b*d*x*sqrt(a + b*acosh(d*x**S(2) + S(1)))), x) + Simp(sqrt(S(2))*sqrt(Pi)*(-sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erfi(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(1)))/(S(2)*sqrt(b)))*sinh(acosh(d*x**S(2) + S(1))/S(2))/(S(2)*b**(S(3)/2)*d*x), x) - Simp(sqrt(S(2))*sqrt(Pi)*(sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erf(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(1)))/(S(2)*sqrt(b)))*sinh(acosh(d*x**S(2) + S(1))/S(2))/(S(2)*b**(S(3)/2)*d*x), x)
    rule6316 = ReplacementRule(pattern6316, replacement6316)
    pattern6317 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(-1)))**(S(-3)/2), x_), cons2, cons3, cons27, cons1765)
    def replacement6317(d, a, b, x):
        rubi.append(6317)
        return -Simp(sqrt(d*x**S(2))*sqrt(d*x**S(2) + S(-2))/(b*d*x*sqrt(a + b*acosh(d*x**S(2) + S(-1)))), x) + Simp(sqrt(S(2))*sqrt(Pi)*(-sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erfi(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*sqrt(b)))*cosh(acosh(d*x**S(2) + S(-1))/S(2))/(S(2)*b**(S(3)/2)*d*x), x) + Simp(sqrt(S(2))*sqrt(Pi)*(sinh(a/(S(2)*b)) + cosh(a/(S(2)*b)))*Erf(sqrt(S(2))*sqrt(a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*sqrt(b)))*cosh(acosh(d*x**S(2) + S(-1))/S(2))/(S(2)*b**(S(3)/2)*d*x), x)
    rule6317 = ReplacementRule(pattern6317, replacement6317)
    pattern6318 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(1)))**(S(-2)), x_), cons2, cons3, cons27, cons1765)
    def replacement6318(d, a, b, x):
        rubi.append(6318)
        return -Simp(sqrt(S(2))*x*CoshIntegral((a + b*acosh(d*x**S(2) + S(1)))/(S(2)*b))*sinh(a/(S(2)*b))/(S(4)*b**S(2)*sqrt(d*x**S(2))), x) + Simp(sqrt(S(2))*x*SinhIntegral((a + b*acosh(d*x**S(2) + S(1)))/(S(2)*b))*cosh(a/(S(2)*b))/(S(4)*b**S(2)*sqrt(d*x**S(2))), x) - Simp(sqrt(d*x**S(2))*sqrt(d*x**S(2) + S(2))/(S(2)*b*d*x*(a + b*acosh(d*x**S(2) + S(1)))), x)
    rule6318 = ReplacementRule(pattern6318, replacement6318)
    pattern6319 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(x_**S(2)*WC('d', S(1)) + S(-1)))**(S(-2)), x_), cons2, cons3, cons27, cons1765)
    def replacement6319(d, a, b, x):
        rubi.append(6319)
        return Simp(sqrt(S(2))*x*CoshIntegral((a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*b))*cosh(a/(S(2)*b))/(S(4)*b**S(2)*sqrt(d*x**S(2))), x) - Simp(sqrt(S(2))*x*SinhIntegral((a + b*acosh(d*x**S(2) + S(-1)))/(S(2)*b))*sinh(a/(S(2)*b))/(S(4)*b**S(2)*sqrt(d*x**S(2))), x) - Simp(sqrt(d*x**S(2))*sqrt(d*x**S(2) + S(-2))/(S(2)*b*d*x*(a + b*acosh(d*x**S(2) + S(-1)))), x)
    rule6319 = ReplacementRule(pattern6319, replacement6319)
    pattern6320 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acosh(c_ + x_**S(2)*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons1764, cons87, cons89, cons1442)
    def replacement6320(b, d, c, a, n, x):
        rubi.append(6320)
        return Dist(S(1)/(S(4)*b**S(2)*(n + S(1))*(n + S(2))), Int((a + b*acosh(c + d*x**S(2)))**(n + S(2)), x), x) - Simp(x*(a + b*acosh(c + d*x**S(2)))**(n + S(2))/(S(4)*b**S(2)*(n + S(1))*(n + S(2))), x) + Simp((a + b*acosh(c + d*x**S(2)))**(n + S(1))*(S(2)*c*x**S(2) + d*x**S(4))/(S(2)*b*x*(n + S(1))*sqrt(c + d*x**S(2) + S(-1))*sqrt(c + d*x**S(2) + S(1))), x)
    rule6320 = ReplacementRule(pattern6320, replacement6320)
    pattern6321 = Pattern(Integral(asinh(x_**p_*WC('a', S(1)))**WC('n', S(1))/x_, x_), cons2, cons5, cons148)
    def replacement6321(x, a, n, p):
        rubi.append(6321)
        return Dist(S(1)/p, Subst(Int(x**n/tanh(x), x), x, asinh(a*x**p)), x)
    rule6321 = ReplacementRule(pattern6321, replacement6321)
    pattern6322 = Pattern(Integral(acosh(x_**p_*WC('a', S(1)))**WC('n', S(1))/x_, x_), cons2, cons5, cons148)
    def replacement6322(x, a, n, p):
        rubi.append(6322)
        return Dist(S(1)/p, Subst(Int(x**n*tanh(x), x), x, acosh(a*x**p)), x)
    rule6322 = ReplacementRule(pattern6322, replacement6322)
    pattern6323 = Pattern(Integral(WC('u', S(1))*asinh(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement6323(u, m, b, c, n, a, x):
        rubi.append(6323)
        return Int(u*acsch(a/c + b*x**n/c)**m, x)
    rule6323 = ReplacementRule(pattern6323, replacement6323)
    pattern6324 = Pattern(Integral(WC('u', S(1))*acosh(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement6324(u, m, b, c, n, a, x):
        rubi.append(6324)
        return Int(u*asech(a/c + b*x**n/c)**m, x)
    rule6324 = ReplacementRule(pattern6324, replacement6324)
    pattern6325 = Pattern(Integral(asinh(sqrt(x_**S(2)*WC('b', S(1)) + S(-1)))**WC('n', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + S(-1)), x_), cons3, cons4, cons1767)
    def replacement6325(x, n, b):
        rubi.append(6325)
        return Dist(sqrt(b*x**S(2))/(b*x), Subst(Int(asinh(x)**n/sqrt(x**S(2) + S(1)), x), x, sqrt(b*x**S(2) + S(-1))), x)
    rule6325 = ReplacementRule(pattern6325, replacement6325)
    pattern6326 = Pattern(Integral(acosh(sqrt(x_**S(2)*WC('b', S(1)) + S(1)))**WC('n', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + S(1)), x_), cons3, cons4, cons1767)
    def replacement6326(x, n, b):
        rubi.append(6326)
        return Dist(sqrt(sqrt(b*x**S(2) + S(1)) + S(-1))*sqrt(sqrt(b*x**S(2) + S(1)) + S(1))/(b*x), Subst(Int(acosh(x)**n/(sqrt(x + S(-1))*sqrt(x + S(1))), x), x, sqrt(b*x**S(2) + S(1))), x)
    rule6326 = ReplacementRule(pattern6326, replacement6326)
    pattern6327 = Pattern(Integral(f_**(WC('c', S(1))*asinh(x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))), x_), cons2, cons3, cons7, cons125, cons148)
    def replacement6327(f, b, c, a, n, x):
        rubi.append(6327)
        return Dist(S(1)/b, Subst(Int(f**(c*x**n)*cosh(x), x), x, asinh(a + b*x)), x)
    rule6327 = ReplacementRule(pattern6327, replacement6327)
    pattern6328 = Pattern(Integral(f_**(WC('c', S(1))*acosh(x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1))), x_), cons2, cons3, cons7, cons125, cons148)
    def replacement6328(f, b, c, a, n, x):
        rubi.append(6328)
        return Dist(S(1)/b, Subst(Int(f**(c*x**n)*sinh(x), x), x, acosh(a + b*x)), x)
    rule6328 = ReplacementRule(pattern6328, replacement6328)
    pattern6329 = Pattern(Integral(f_**(WC('c', S(1))*asinh(x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)))*x_**WC('m', S(1)), x_), cons2, cons3, cons7, cons125, cons528)
    def replacement6329(m, f, b, c, a, n, x):
        rubi.append(6329)
        return Dist(S(1)/b, Subst(Int(f**(c*x**n)*(-a/b + sinh(x)/b)**m*cosh(x), x), x, asinh(a + b*x)), x)
    rule6329 = ReplacementRule(pattern6329, replacement6329)
    pattern6330 = Pattern(Integral(f_**(WC('c', S(1))*acosh(x_*WC('b', S(1)) + WC('a', S(0)))**WC('n', S(1)))*x_**WC('m', S(1)), x_), cons2, cons3, cons7, cons125, cons528)
    def replacement6330(m, f, b, c, a, n, x):
        rubi.append(6330)
        return Dist(S(1)/b, Subst(Int(f**(c*x**n)*(-a/b + cosh(x)/b)**m*sinh(x), x), x, acosh(a + b*x)), x)
    rule6330 = ReplacementRule(pattern6330, replacement6330)
    pattern6331 = Pattern(Integral(asinh(u_), x_), cons1230, cons1769)
    def replacement6331(x, u):
        rubi.append(6331)
        return -Int(SimplifyIntegrand(x*D(u, x)/sqrt(u**S(2) + S(1)), x), x) + Simp(x*asinh(u), x)
    rule6331 = ReplacementRule(pattern6331, replacement6331)
    pattern6332 = Pattern(Integral(acosh(u_), x_), cons1230, cons1769)
    def replacement6332(x, u):
        rubi.append(6332)
        return -Int(SimplifyIntegrand(x*D(u, x)/(sqrt(u + S(-1))*sqrt(u + S(1))), x), x) + Simp(x*acosh(u), x)
    rule6332 = ReplacementRule(pattern6332, replacement6332)
    pattern6333 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asinh(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1769)
    def replacement6333(u, m, b, d, c, a, x):
        rubi.append(6333)
        return -Dist(b/(d*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/sqrt(u**S(2) + S(1)), x), x), x) + Simp((a + b*asinh(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule6333 = ReplacementRule(pattern6333, replacement6333)
    pattern6334 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acosh(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1769)
    def replacement6334(u, m, b, d, c, a, x):
        rubi.append(6334)
        return -Dist(b/(d*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/(sqrt(u + S(-1))*sqrt(u + S(1))), x), x), x) + Simp((a + b*acosh(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule6334 = ReplacementRule(pattern6334, replacement6334)
    def With6335(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern6335 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*asinh(u_)), x_), cons2, cons3, cons1230, cons1905, CustomConstraint(With6335))
    def replacement6335(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(6335)
        return -Dist(b, Int(SimplifyIntegrand(w*D(u, x)/sqrt(u**S(2) + S(1)), x), x), x) + Dist(a + b*asinh(u), w, x)
    rule6335 = ReplacementRule(pattern6335, replacement6335)
    def With6336(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern6336 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*acosh(u_)), x_), cons2, cons3, cons1230, cons1906, CustomConstraint(With6336))
    def replacement6336(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(6336)
        return -Dist(b, Int(SimplifyIntegrand(w*D(u, x)/(sqrt(u + S(-1))*sqrt(u + S(1))), x), x), x) + Dist(a + b*acosh(u), w, x)
    rule6336 = ReplacementRule(pattern6336, replacement6336)
    pattern6337 = Pattern(Integral(exp(WC('n', S(1))*asinh(u_)), x_), cons85, cons804)
    def replacement6337(x, n, u):
        rubi.append(6337)
        return Int((u + sqrt(u**S(2) + S(1)))**n, x)
    rule6337 = ReplacementRule(pattern6337, replacement6337)
    pattern6338 = Pattern(Integral(x_**WC('m', S(1))*exp(WC('n', S(1))*asinh(u_)), x_), cons31, cons85, cons804)
    def replacement6338(x, m, n, u):
        rubi.append(6338)
        return Int(x**m*(u + sqrt(u**S(2) + S(1)))**n, x)
    rule6338 = ReplacementRule(pattern6338, replacement6338)
    pattern6339 = Pattern(Integral(exp(WC('n', S(1))*acosh(u_)), x_), cons85, cons804)
    def replacement6339(x, n, u):
        rubi.append(6339)
        return Int((u + sqrt(u + S(-1))*sqrt(u + S(1)))**n, x)
    rule6339 = ReplacementRule(pattern6339, replacement6339)
    pattern6340 = Pattern(Integral(x_**WC('m', S(1))*exp(WC('n', S(1))*acosh(u_)), x_), cons31, cons85, cons804)
    def replacement6340(x, m, n, u):
        rubi.append(6340)
        return Int(x**m*(u + sqrt(u + S(-1))*sqrt(u + S(1)))**n, x)
    rule6340 = ReplacementRule(pattern6340, replacement6340)
    pattern6341 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons148)
    def replacement6341(b, a, n, c, x):
        rubi.append(6341)
        return -Dist(b*c*n, Int(x*(a + b*atanh(c*x))**(n + S(-1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*atanh(c*x))**n, x)
    rule6341 = ReplacementRule(pattern6341, replacement6341)
    pattern6342 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons148)
    def replacement6342(b, a, n, c, x):
        rubi.append(6342)
        return -Dist(b*c*n, Int(x*(a + b*acoth(c*x))**(n + S(-1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x*(a + b*acoth(c*x))**n, x)
    rule6342 = ReplacementRule(pattern6342, replacement6342)
    pattern6343 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons340)
    def replacement6343(b, a, n, c, x):
        rubi.append(6343)
        return Int((a + b*atanh(c*x))**n, x)
    rule6343 = ReplacementRule(pattern6343, replacement6343)
    pattern6344 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons340)
    def replacement6344(b, a, n, c, x):
        rubi.append(6344)
        return Int((a + b*acoth(c*x))**n, x)
    rule6344 = ReplacementRule(pattern6344, replacement6344)
    pattern6345 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1907, cons148)
    def replacement6345(b, d, a, n, c, x, e):
        rubi.append(6345)
        return Dist(b*c*n/e, Int((a + b*atanh(c*x))**(n + S(-1))*log(S(2)*d/(d + e*x))/(-c**S(2)*x**S(2) + S(1)), x), x) - Simp((a + b*atanh(c*x))**n*log(S(2)*d/(d + e*x))/e, x)
    rule6345 = ReplacementRule(pattern6345, replacement6345)
    pattern6346 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1907, cons148)
    def replacement6346(b, d, a, n, c, x, e):
        rubi.append(6346)
        return Dist(b*c*n/e, Int((a + b*acoth(c*x))**(n + S(-1))*log(S(2)*d/(d + e*x))/(-c**S(2)*x**S(2) + S(1)), x), x) - Simp((a + b*acoth(c*x))**n*log(S(2)*d/(d + e*x))/e, x)
    rule6346 = ReplacementRule(pattern6346, replacement6346)
    pattern6347 = Pattern(Integral(atanh(x_*WC('c', S(1)))/(d_ + x_*WC('e', S(1))), x_), cons7, cons27, cons48, cons1908, cons1909)
    def replacement6347(x, d, c, e):
        rubi.append(6347)
        return -Simp(PolyLog(S(2), Simp(c*(d + e*x)/(c*d - e), x))/(S(2)*e), x) + Simp(PolyLog(S(2), Simp(c*(d + e*x)/(c*d + e), x))/(S(2)*e), x) - Simp(log(d + e*x)*atanh(c*d/e)/e, x)
    rule6347 = ReplacementRule(pattern6347, replacement6347)
    pattern6348 = Pattern(Integral(atanh(x_*WC('c', S(1)))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons7, cons27, cons48, cons1776)
    def replacement6348(d, c, x, e):
        rubi.append(6348)
        return -Dist(S(1)/2, Int(log(-c*x + S(1))/(d + e*x), x), x) + Dist(S(1)/2, Int(log(c*x + S(1))/(d + e*x), x), x)
    rule6348 = ReplacementRule(pattern6348, replacement6348)
    pattern6349 = Pattern(Integral(acoth(x_*WC('c', S(1)))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons7, cons27, cons48, cons1776)
    def replacement6349(d, c, x, e):
        rubi.append(6349)
        return -Dist(S(1)/2, Int(log(S(1) - S(1)/(c*x))/(d + e*x), x), x) + Dist(S(1)/2, Int(log(S(1) + S(1)/(c*x))/(d + e*x), x), x)
    rule6349 = ReplacementRule(pattern6349, replacement6349)
    pattern6350 = Pattern(Integral((a_ + WC('b', S(1))*atanh(x_*WC('c', S(1))))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement6350(b, d, c, a, x, e):
        rubi.append(6350)
        return Dist(b, Int(atanh(c*x)/(d + e*x), x), x) + Simp(a*log(RemoveContent(d + e*x, x))/e, x)
    rule6350 = ReplacementRule(pattern6350, replacement6350)
    pattern6351 = Pattern(Integral((a_ + WC('b', S(1))*acoth(x_*WC('c', S(1))))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement6351(b, d, c, a, x, e):
        rubi.append(6351)
        return Dist(b, Int(acoth(c*x)/(d + e*x), x), x) + Simp(a*log(RemoveContent(d + e*x, x))/e, x)
    rule6351 = ReplacementRule(pattern6351, replacement6351)
    pattern6352 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement6352(p, b, d, a, c, x, e):
        rubi.append(6352)
        return -Dist(b*c/(e*(p + S(1))), Int((d + e*x)**(p + S(1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*atanh(c*x))*(d + e*x)**(p + S(1))/(e*(p + S(1))), x)
    rule6352 = ReplacementRule(pattern6352, replacement6352)
    pattern6353 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement6353(p, b, d, a, c, x, e):
        rubi.append(6353)
        return -Dist(b*c/(e*(p + S(1))), Int((d + e*x)**(p + S(1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*acoth(c*x))*(d + e*x)**(p + S(1))/(e*(p + S(1))), x)
    rule6353 = ReplacementRule(pattern6353, replacement6353)
    pattern6354 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_/x_, x_), cons2, cons3, cons7, cons85, cons165)
    def replacement6354(b, a, n, c, x):
        rubi.append(6354)
        return -Dist(S(2)*b*c*n, Int((a + b*atanh(c*x))**(n + S(-1))*atanh(S(1) - S(2)/(-c*x + S(1)))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(S(2)*(a + b*atanh(c*x))**n*atanh(S(1) - S(2)/(-c*x + S(1))), x)
    rule6354 = ReplacementRule(pattern6354, replacement6354)
    pattern6355 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_/x_, x_), cons2, cons3, cons7, cons85, cons165)
    def replacement6355(b, a, n, c, x):
        rubi.append(6355)
        return -Dist(S(2)*b*c*n, Int((a + b*acoth(c*x))**(n + S(-1))*acoth(S(1) - S(2)/(-c*x + S(1)))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(S(2)*(a + b*acoth(c*x))**n*acoth(S(1) - S(2)/(-c*x + S(1))), x)
    rule6355 = ReplacementRule(pattern6355, replacement6355)
    pattern6356 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons21, cons85, cons165, cons66)
    def replacement6356(m, b, a, c, n, x):
        rubi.append(6356)
        return -Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*atanh(c*x))**(n + S(-1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x**(m + S(1))*(a + b*atanh(c*x))**n/(m + S(1)), x)
    rule6356 = ReplacementRule(pattern6356, replacement6356)
    pattern6357 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons21, cons85, cons165, cons66)
    def replacement6357(m, b, a, c, n, x):
        rubi.append(6357)
        return -Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*acoth(c*x))**(n + S(-1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp(x**(m + S(1))*(a + b*acoth(c*x))**n/(m + S(1)), x)
    rule6357 = ReplacementRule(pattern6357, replacement6357)
    pattern6358 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons464)
    def replacement6358(p, b, d, a, n, c, x, e):
        rubi.append(6358)
        return Int(ExpandIntegrand((a + b*atanh(c*x))**n*(d + e*x)**p, x), x)
    rule6358 = ReplacementRule(pattern6358, replacement6358)
    pattern6359 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons464)
    def replacement6359(p, b, d, a, n, c, x, e):
        rubi.append(6359)
        return Int(ExpandIntegrand((a + b*acoth(c*x))**n*(d + e*x)**p, x), x)
    rule6359 = ReplacementRule(pattern6359, replacement6359)
    pattern6360 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons340)
    def replacement6360(p, b, d, a, c, n, x, e):
        rubi.append(6360)
        return Int((a + b*atanh(c*x))**n*(d + e*x)**p, x)
    rule6360 = ReplacementRule(pattern6360, replacement6360)
    pattern6361 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons340)
    def replacement6361(p, b, d, a, c, n, x, e):
        rubi.append(6361)
        return Int((a + b*acoth(c*x))**n*(d + e*x)**p, x)
    rule6361 = ReplacementRule(pattern6361, replacement6361)
    pattern6362 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1907, cons148, cons31, cons168)
    def replacement6362(m, b, d, a, n, c, x, e):
        rubi.append(6362)
        return Dist(S(1)/e, Int(x**(m + S(-1))*(a + b*atanh(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-1))*(a + b*atanh(c*x))**n/(d + e*x), x), x)
    rule6362 = ReplacementRule(pattern6362, replacement6362)
    pattern6363 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1907, cons148, cons31, cons168)
    def replacement6363(m, b, d, a, n, c, x, e):
        rubi.append(6363)
        return Dist(S(1)/e, Int(x**(m + S(-1))*(a + b*acoth(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-1))*(a + b*acoth(c*x))**n/(d + e*x), x), x)
    rule6363 = ReplacementRule(pattern6363, replacement6363)
    pattern6364 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1907, cons148)
    def replacement6364(b, d, a, n, c, x, e):
        rubi.append(6364)
        return -Dist(b*c*n/d, Int((a + b*atanh(c*x))**(n + S(-1))*log(S(2)*e*x/(d + e*x))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*atanh(c*x))**n*log(S(2)*e*x/(d + e*x))/d, x)
    rule6364 = ReplacementRule(pattern6364, replacement6364)
    pattern6365 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1907, cons148)
    def replacement6365(b, d, a, n, c, x, e):
        rubi.append(6365)
        return -Dist(b*c*n/d, Int((a + b*acoth(c*x))**(n + S(-1))*log(S(2)*e*x/(d + e*x))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*acoth(c*x))**n*log(S(2)*e*x/(d + e*x))/d, x)
    rule6365 = ReplacementRule(pattern6365, replacement6365)
    pattern6366 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1907, cons148, cons31, cons94)
    def replacement6366(m, b, d, a, n, c, x, e):
        rubi.append(6366)
        return Dist(S(1)/d, Int(x**m*(a + b*atanh(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(1))*(a + b*atanh(c*x))**n/(d + e*x), x), x)
    rule6366 = ReplacementRule(pattern6366, replacement6366)
    pattern6367 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1907, cons148, cons31, cons94)
    def replacement6367(m, b, d, a, n, c, x, e):
        rubi.append(6367)
        return Dist(S(1)/d, Int(x**m*(a + b*acoth(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(1))*(a + b*acoth(c*x))**n/(d + e*x), x), x)
    rule6367 = ReplacementRule(pattern6367, replacement6367)
    pattern6368 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons1777)
    def replacement6368(p, m, b, d, a, n, c, x, e):
        rubi.append(6368)
        return Int(ExpandIntegrand(x**m*(a + b*atanh(c*x))**n*(d + e*x)**p, x), x)
    rule6368 = ReplacementRule(pattern6368, replacement6368)
    pattern6369 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons1777)
    def replacement6369(p, m, b, d, a, n, c, x, e):
        rubi.append(6369)
        return Int(ExpandIntegrand(x**m*(a + b*acoth(c*x))**n*(d + e*x)**p, x), x)
    rule6369 = ReplacementRule(pattern6369, replacement6369)
    pattern6370 = Pattern(Integral(x_**WC('m', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement6370(p, m, b, d, a, n, c, x, e):
        rubi.append(6370)
        return Int(x**m*(a + b*atanh(c*x))**n*(d + e*x)**p, x)
    rule6370 = ReplacementRule(pattern6370, replacement6370)
    pattern6371 = Pattern(Integral(x_**WC('m', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement6371(p, m, b, d, a, n, c, x, e):
        rubi.append(6371)
        return Int(x**m*(a + b*acoth(c*x))**n*(d + e*x)**p, x)
    rule6371 = ReplacementRule(pattern6371, replacement6371)
    pattern6372 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons13, cons163)
    def replacement6372(p, b, d, a, c, x, e):
        rubi.append(6372)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*atanh(c*x))*(d + e*x**S(2))**(p + S(-1)), x), x) + Simp(x*(a + b*atanh(c*x))*(d + e*x**S(2))**p/(S(2)*p + S(1)), x) + Simp(b*(d + e*x**S(2))**p/(S(2)*c*p*(S(2)*p + S(1))), x)
    rule6372 = ReplacementRule(pattern6372, replacement6372)
    pattern6373 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons13, cons163)
    def replacement6373(p, b, d, a, c, x, e):
        rubi.append(6373)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*acoth(c*x))*(d + e*x**S(2))**(p + S(-1)), x), x) + Simp(x*(a + b*acoth(c*x))*(d + e*x**S(2))**p/(S(2)*p + S(1)), x) + Simp(b*(d + e*x**S(2))**p/(S(2)*c*p*(S(2)*p + S(1))), x)
    rule6373 = ReplacementRule(pattern6373, replacement6373)
    pattern6374 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons163, cons165)
    def replacement6374(p, b, d, a, c, n, x, e):
        rubi.append(6374)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b**S(2)*d*n*(n + S(-1))/(S(2)*p*(S(2)*p + S(1))), Int((a + b*atanh(c*x))**(n + S(-2))*(d + e*x**S(2))**(p + S(-1)), x), x) + Simp(x*(a + b*atanh(c*x))**n*(d + e*x**S(2))**p/(S(2)*p + S(1)), x) + Simp(b*n*(a + b*atanh(c*x))**(n + S(-1))*(d + e*x**S(2))**p/(S(2)*c*p*(S(2)*p + S(1))), x)
    rule6374 = ReplacementRule(pattern6374, replacement6374)
    pattern6375 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons163, cons165)
    def replacement6375(p, b, d, a, c, n, x, e):
        rubi.append(6375)
        return Dist(S(2)*d*p/(S(2)*p + S(1)), Int((a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(b**S(2)*d*n*(n + S(-1))/(S(2)*p*(S(2)*p + S(1))), Int((a + b*acoth(c*x))**(n + S(-2))*(d + e*x**S(2))**(p + S(-1)), x), x) + Simp(x*(a + b*acoth(c*x))**n*(d + e*x**S(2))**p/(S(2)*p + S(1)), x) + Simp(b*n*(a + b*acoth(c*x))**(n + S(-1))*(d + e*x**S(2))**p/(S(2)*c*p*(S(2)*p + S(1))), x)
    rule6375 = ReplacementRule(pattern6375, replacement6375)
    pattern6376 = Pattern(Integral(S(1)/((d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))), x_), cons2, cons3, cons7, cons27, cons48, cons1737)
    def replacement6376(b, d, a, c, x, e):
        rubi.append(6376)
        return Simp(log(RemoveContent(a + b*atanh(c*x), x))/(b*c*d), x)
    rule6376 = ReplacementRule(pattern6376, replacement6376)
    pattern6377 = Pattern(Integral(S(1)/((d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))), x_), cons2, cons3, cons7, cons27, cons48, cons1737)
    def replacement6377(b, d, a, c, x, e):
        rubi.append(6377)
        return Simp(log(RemoveContent(a + b*acoth(c*x), x))/(b*c*d), x)
    rule6377 = ReplacementRule(pattern6377, replacement6377)
    pattern6378 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons584)
    def replacement6378(b, d, a, n, c, x, e):
        rubi.append(6378)
        return Simp((a + b*atanh(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule6378 = ReplacementRule(pattern6378, replacement6378)
    pattern6379 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons584)
    def replacement6379(b, d, a, n, c, x, e):
        rubi.append(6379)
        return Simp((a + b*acoth(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule6379 = ReplacementRule(pattern6379, replacement6379)
    pattern6380 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons268)
    def replacement6380(b, d, a, c, x, e):
        rubi.append(6380)
        return Simp(-S(2)*(a + b*atanh(c*x))*ArcTan(sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/(c*sqrt(d)), x) - Simp(I*b*PolyLog(S(2), -I*sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/(c*sqrt(d)), x) + Simp(I*b*PolyLog(S(2), I*sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/(c*sqrt(d)), x)
    rule6380 = ReplacementRule(pattern6380, replacement6380)
    pattern6381 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons268)
    def replacement6381(b, d, a, c, x, e):
        rubi.append(6381)
        return Simp(-S(2)*(a + b*acoth(c*x))*ArcTan(sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/(c*sqrt(d)), x) - Simp(I*b*PolyLog(S(2), -I*sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/(c*sqrt(d)), x) + Simp(I*b*PolyLog(S(2), I*sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/(c*sqrt(d)), x)
    rule6381 = ReplacementRule(pattern6381, replacement6381)
    pattern6382 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148, cons268)
    def replacement6382(b, d, a, n, c, x, e):
        rubi.append(6382)
        return Dist(S(1)/(c*sqrt(d)), Subst(Int((a + b*x)**n/cosh(x), x), x, atanh(c*x)), x)
    rule6382 = ReplacementRule(pattern6382, replacement6382)
    pattern6383 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148, cons268)
    def replacement6383(b, d, a, n, c, x, e):
        rubi.append(6383)
        return -Dist(x*sqrt(S(1) - S(1)/(c**S(2)*x**S(2)))/sqrt(d + e*x**S(2)), Subst(Int((a + b*x)**n/sinh(x), x), x, acoth(c*x)), x)
    rule6383 = ReplacementRule(pattern6383, replacement6383)
    pattern6384 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148, cons1738)
    def replacement6384(b, d, a, n, c, x, e):
        rubi.append(6384)
        return Dist(sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*atanh(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x)
    rule6384 = ReplacementRule(pattern6384, replacement6384)
    pattern6385 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148, cons1738)
    def replacement6385(b, d, a, n, c, x, e):
        rubi.append(6385)
        return Dist(sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*acoth(c*x))**n/sqrt(-c**S(2)*x**S(2) + S(1)), x), x)
    rule6385 = ReplacementRule(pattern6385, replacement6385)
    pattern6386 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement6386(b, d, a, n, c, x, e):
        rubi.append(6386)
        return -Dist(b*c*n/S(2), Int(x*(a + b*atanh(c*x))**(n + S(-1))/(d + e*x**S(2))**S(2), x), x) + Simp(x*(a + b*atanh(c*x))**n/(S(2)*d*(d + e*x**S(2))), x) + Simp((a + b*atanh(c*x))**(n + S(1))/(S(2)*b*c*d**S(2)*(n + S(1))), x)
    rule6386 = ReplacementRule(pattern6386, replacement6386)
    pattern6387 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement6387(b, d, a, n, c, x, e):
        rubi.append(6387)
        return -Dist(b*c*n/S(2), Int(x*(a + b*acoth(c*x))**(n + S(-1))/(d + e*x**S(2))**S(2), x), x) + Simp(x*(a + b*acoth(c*x))**n/(S(2)*d*(d + e*x**S(2))), x) + Simp((a + b*acoth(c*x))**(n + S(1))/(S(2)*b*c*d**S(2)*(n + S(1))), x)
    rule6387 = ReplacementRule(pattern6387, replacement6387)
    pattern6388 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1737)
    def replacement6388(b, d, a, c, x, e):
        rubi.append(6388)
        return -Simp(b/(c*d*sqrt(d + e*x**S(2))), x) + Simp(x*(a + b*atanh(c*x))/(d*sqrt(d + e*x**S(2))), x)
    rule6388 = ReplacementRule(pattern6388, replacement6388)
    pattern6389 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1737)
    def replacement6389(b, d, a, c, x, e):
        rubi.append(6389)
        return -Simp(b/(c*d*sqrt(d + e*x**S(2))), x) + Simp(x*(a + b*acoth(c*x))/(d*sqrt(d + e*x**S(2))), x)
    rule6389 = ReplacementRule(pattern6389, replacement6389)
    pattern6390 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons13, cons137, cons230)
    def replacement6390(p, b, d, a, c, x, e):
        rubi.append(6390)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*atanh(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(b*(d + e*x**S(2))**(p + S(1))/(S(4)*c*d*(p + S(1))**S(2)), x) - Simp(x*(a + b*atanh(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x)
    rule6390 = ReplacementRule(pattern6390, replacement6390)
    pattern6391 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons13, cons137, cons230)
    def replacement6391(p, b, d, a, c, x, e):
        rubi.append(6391)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*acoth(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(b*(d + e*x**S(2))**(p + S(1))/(S(4)*c*d*(p + S(1))**S(2)), x) - Simp(x*(a + b*acoth(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x)
    rule6391 = ReplacementRule(pattern6391, replacement6391)
    pattern6392 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons165)
    def replacement6392(b, d, a, c, n, x, e):
        rubi.append(6392)
        return Dist(b**S(2)*n*(n + S(-1)), Int((a + b*atanh(c*x))**(n + S(-2))/(d + e*x**S(2))**(S(3)/2), x), x) + Simp(x*(a + b*atanh(c*x))**n/(d*sqrt(d + e*x**S(2))), x) - Simp(b*n*(a + b*atanh(c*x))**(n + S(-1))/(c*d*sqrt(d + e*x**S(2))), x)
    rule6392 = ReplacementRule(pattern6392, replacement6392)
    pattern6393 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons165)
    def replacement6393(b, d, a, c, n, x, e):
        rubi.append(6393)
        return Dist(b**S(2)*n*(n + S(-1)), Int((a + b*acoth(c*x))**(n + S(-2))/(d + e*x**S(2))**(S(3)/2), x), x) + Simp(x*(a + b*acoth(c*x))**n/(d*sqrt(d + e*x**S(2))), x) - Simp(b*n*(a + b*acoth(c*x))**(n + S(-1))/(c*d*sqrt(d + e*x**S(2))), x)
    rule6393 = ReplacementRule(pattern6393, replacement6393)
    pattern6394 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons137, cons165, cons230)
    def replacement6394(p, b, d, a, c, n, x, e):
        rubi.append(6394)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) + Dist(b**S(2)*n*(n + S(-1))/(S(4)*(p + S(1))**S(2)), Int((a + b*atanh(c*x))**(n + S(-2))*(d + e*x**S(2))**p, x), x) - Simp(x*(a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x) - Simp(b*n*(a + b*atanh(c*x))**(n + S(-1))*(d + e*x**S(2))**(p + S(1))/(S(4)*c*d*(p + S(1))**S(2)), x)
    rule6394 = ReplacementRule(pattern6394, replacement6394)
    pattern6395 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons137, cons165, cons230)
    def replacement6395(p, b, d, a, c, n, x, e):
        rubi.append(6395)
        return Dist((S(2)*p + S(3))/(S(2)*d*(p + S(1))), Int((a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) + Dist(b**S(2)*n*(n + S(-1))/(S(4)*(p + S(1))**S(2)), Int((a + b*acoth(c*x))**(n + S(-2))*(d + e*x**S(2))**p, x), x) - Simp(x*(a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*d*(p + S(1))), x) - Simp(b*n*(a + b*acoth(c*x))**(n + S(-1))*(d + e*x**S(2))**(p + S(1))/(S(4)*c*d*(p + S(1))**S(2)), x)
    rule6395 = ReplacementRule(pattern6395, replacement6395)
    pattern6396 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons137, cons89)
    def replacement6396(p, b, d, a, c, n, x, e):
        rubi.append(6396)
        return Dist(S(2)*c*(p + S(1))/(b*(n + S(1))), Int(x*(a + b*atanh(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Simp((a + b*atanh(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule6396 = ReplacementRule(pattern6396, replacement6396)
    pattern6397 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons338, cons137, cons89)
    def replacement6397(p, b, d, a, c, n, x, e):
        rubi.append(6397)
        return Dist(S(2)*c*(p + S(1))/(b*(n + S(1))), Int(x*(a + b*acoth(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Simp((a + b*acoth(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule6397 = ReplacementRule(pattern6397, replacement6397)
    pattern6398 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1779, cons1740)
    def replacement6398(p, b, d, a, n, c, x, e):
        rubi.append(6398)
        return Dist(d**p/c, Subst(Int((a + b*x)**n*cosh(x)**(-S(2)*p + S(-2)), x), x, atanh(c*x)), x)
    rule6398 = ReplacementRule(pattern6398, replacement6398)
    pattern6399 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1779, cons1741)
    def replacement6399(p, b, d, a, n, c, x, e):
        rubi.append(6399)
        return Dist(d**(p + S(1)/2)*sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*atanh(c*x))**n*(-c**S(2)*x**S(2) + S(1))**p, x), x)
    rule6399 = ReplacementRule(pattern6399, replacement6399)
    pattern6400 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1779, cons38)
    def replacement6400(p, b, d, a, n, c, x, e):
        rubi.append(6400)
        return -Dist((-d)**p/c, Subst(Int((a + b*x)**n*sinh(x)**(-S(2)*p + S(-2)), x), x, acoth(c*x)), x)
    rule6400 = ReplacementRule(pattern6400, replacement6400)
    pattern6401 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons1779, cons147)
    def replacement6401(p, b, d, a, n, c, x, e):
        rubi.append(6401)
        return -Dist(x*(-d)**(p + S(1)/2)*sqrt((c**S(2)*x**S(2) + S(-1))/(c**S(2)*x**S(2)))/sqrt(d + e*x**S(2)), Subst(Int((a + b*x)**n*sinh(x)**(-S(2)*p + S(-2)), x), x, acoth(c*x)), x)
    rule6401 = ReplacementRule(pattern6401, replacement6401)
    pattern6402 = Pattern(Integral(atanh(x_*WC('c', S(1)))/(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons7, cons27, cons48, cons1776)
    def replacement6402(d, c, x, e):
        rubi.append(6402)
        return -Dist(S(1)/2, Int(log(-c*x + S(1))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int(log(c*x + S(1))/(d + e*x**S(2)), x), x)
    rule6402 = ReplacementRule(pattern6402, replacement6402)
    pattern6403 = Pattern(Integral(acoth(x_*WC('c', S(1)))/(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons7, cons27, cons48, cons1776)
    def replacement6403(d, c, x, e):
        rubi.append(6403)
        return -Dist(S(1)/2, Int(log(S(1) - S(1)/(c*x))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int(log(S(1) + S(1)/(c*x))/(d + e*x**S(2)), x), x)
    rule6403 = ReplacementRule(pattern6403, replacement6403)
    pattern6404 = Pattern(Integral((a_ + WC('b', S(1))*atanh(x_*WC('c', S(1))))/(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement6404(b, d, c, a, x, e):
        rubi.append(6404)
        return Dist(a, Int(S(1)/(d + e*x**S(2)), x), x) + Dist(b, Int(atanh(c*x)/(d + e*x**S(2)), x), x)
    rule6404 = ReplacementRule(pattern6404, replacement6404)
    pattern6405 = Pattern(Integral((a_ + WC('b', S(1))*acoth(x_*WC('c', S(1))))/(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement6405(b, d, c, a, x, e):
        rubi.append(6405)
        return Dist(a, Int(S(1)/(d + e*x**S(2)), x), x) + Dist(b, Int(acoth(c*x)/(d + e*x**S(2)), x), x)
    rule6405 = ReplacementRule(pattern6405, replacement6405)
    def With6406(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(6406)
        return -Dist(b*c, Int(ExpandIntegrand(u/(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*atanh(c*x), u, x)
    pattern6406 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1780)
    rule6406 = ReplacementRule(pattern6406, With6406)
    def With6407(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(6407)
        return -Dist(b*c, Int(ExpandIntegrand(u/(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acoth(c*x), u, x)
    pattern6407 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1780)
    rule6407 = ReplacementRule(pattern6407, With6407)
    pattern6408 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons38, cons148)
    def replacement6408(p, b, d, a, n, c, x, e):
        rubi.append(6408)
        return Int(ExpandIntegrand((a + b*atanh(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule6408 = ReplacementRule(pattern6408, replacement6408)
    pattern6409 = Pattern(Integral((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons38, cons148)
    def replacement6409(p, b, d, a, n, c, x, e):
        rubi.append(6409)
        return Int(ExpandIntegrand((a + b*acoth(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule6409 = ReplacementRule(pattern6409, replacement6409)
    pattern6410 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement6410(p, b, d, a, n, c, x, e):
        rubi.append(6410)
        return Int((a + b*atanh(c*x))**n*(d + e*x**S(2))**p, x)
    rule6410 = ReplacementRule(pattern6410, replacement6410)
    pattern6411 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement6411(p, b, d, a, n, c, x, e):
        rubi.append(6411)
        return Int((a + b*acoth(c*x))**n*(d + e*x**S(2))**p, x)
    rule6411 = ReplacementRule(pattern6411, replacement6411)
    pattern6412 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons93, cons88, cons166)
    def replacement6412(m, b, d, a, n, c, x, e):
        rubi.append(6412)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*atanh(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*atanh(c*x))**n/(d + e*x**S(2)), x), x)
    rule6412 = ReplacementRule(pattern6412, replacement6412)
    pattern6413 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons93, cons88, cons166)
    def replacement6413(m, b, d, a, n, c, x, e):
        rubi.append(6413)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*acoth(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*acoth(c*x))**n/(d + e*x**S(2)), x), x)
    rule6413 = ReplacementRule(pattern6413, replacement6413)
    pattern6414 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons93, cons88, cons94)
    def replacement6414(m, b, d, a, n, c, x, e):
        rubi.append(6414)
        return Dist(S(1)/d, Int(x**m*(a + b*atanh(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*atanh(c*x))**n/(d + e*x**S(2)), x), x)
    rule6414 = ReplacementRule(pattern6414, replacement6414)
    pattern6415 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons93, cons88, cons94)
    def replacement6415(m, b, d, a, n, c, x, e):
        rubi.append(6415)
        return Dist(S(1)/d, Int(x**m*(a + b*acoth(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*acoth(c*x))**n/(d + e*x**S(2)), x), x)
    rule6415 = ReplacementRule(pattern6415, replacement6415)
    pattern6416 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement6416(b, d, a, n, c, x, e):
        rubi.append(6416)
        return Dist(S(1)/(c*d), Int((a + b*atanh(c*x))**n/(-c*x + S(1)), x), x) + Simp((a + b*atanh(c*x))**(n + S(1))/(b*e*(n + S(1))), x)
    rule6416 = ReplacementRule(pattern6416, replacement6416)
    pattern6417 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148)
    def replacement6417(b, d, a, n, c, x, e):
        rubi.append(6417)
        return Dist(S(1)/(c*d), Int((a + b*acoth(c*x))**n/(-c*x + S(1)), x), x) + Simp((a + b*acoth(c*x))**(n + S(1))/(b*e*(n + S(1))), x)
    rule6417 = ReplacementRule(pattern6417, replacement6417)
    pattern6418 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons340, cons584)
    def replacement6418(b, d, a, c, n, x, e):
        rubi.append(6418)
        return -Dist(S(1)/(b*c*d*(n + S(1))), Int((a + b*atanh(c*x))**(n + S(1)), x), x) + Simp(x*(a + b*atanh(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule6418 = ReplacementRule(pattern6418, replacement6418)
    pattern6419 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons340, cons584)
    def replacement6419(b, d, a, c, n, x, e):
        rubi.append(6419)
        return -Dist(S(1)/(b*c*d*(n + S(1))), Int((a + b*acoth(c*x))**(n + S(1)), x), x) - Simp(x*(a + b*acoth(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule6419 = ReplacementRule(pattern6419, replacement6419)
    pattern6420 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons93, cons88, cons166)
    def replacement6420(m, b, d, a, n, c, x, e):
        rubi.append(6420)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*atanh(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*atanh(c*x))**n/(d + e*x**S(2)), x), x)
    rule6420 = ReplacementRule(pattern6420, replacement6420)
    pattern6421 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons93, cons88, cons166)
    def replacement6421(m, b, d, a, n, c, x, e):
        rubi.append(6421)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*acoth(c*x))**n, x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*acoth(c*x))**n/(d + e*x**S(2)), x), x)
    rule6421 = ReplacementRule(pattern6421, replacement6421)
    pattern6422 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement6422(b, d, a, n, c, x, e):
        rubi.append(6422)
        return Dist(S(1)/d, Int((a + b*atanh(c*x))**n/(x*(c*x + S(1))), x), x) + Simp((a + b*atanh(c*x))**(n + S(1))/(b*d*(n + S(1))), x)
    rule6422 = ReplacementRule(pattern6422, replacement6422)
    pattern6423 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(x_*(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement6423(b, d, a, n, c, x, e):
        rubi.append(6423)
        return Dist(S(1)/d, Int((a + b*acoth(c*x))**n/(x*(c*x + S(1))), x), x) + Simp((a + b*acoth(c*x))**(n + S(1))/(b*d*(n + S(1))), x)
    rule6423 = ReplacementRule(pattern6423, replacement6423)
    pattern6424 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons93, cons88, cons94)
    def replacement6424(m, b, d, a, n, c, x, e):
        rubi.append(6424)
        return Dist(S(1)/d, Int(x**m*(a + b*atanh(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*atanh(c*x))**n/(d + e*x**S(2)), x), x)
    rule6424 = ReplacementRule(pattern6424, replacement6424)
    pattern6425 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons93, cons88, cons94)
    def replacement6425(m, b, d, a, n, c, x, e):
        rubi.append(6425)
        return Dist(S(1)/d, Int(x**m*(a + b*acoth(c*x))**n, x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*acoth(c*x))**n/(d + e*x**S(2)), x), x)
    rule6425 = ReplacementRule(pattern6425, replacement6425)
    pattern6426 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons87, cons89)
    def replacement6426(m, b, d, a, c, n, x, e):
        rubi.append(6426)
        return -Dist(m/(b*c*d*(n + S(1))), Int(x**(m + S(-1))*(a + b*atanh(c*x))**(n + S(1)), x), x) + Simp(x**m*(a + b*atanh(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule6426 = ReplacementRule(pattern6426, replacement6426)
    pattern6427 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons87, cons89)
    def replacement6427(m, b, d, a, c, n, x, e):
        rubi.append(6427)
        return -Dist(m/(b*c*d*(n + S(1))), Int(x**(m + S(-1))*(a + b*acoth(c*x))**(n + S(1)), x), x) + Simp(x**m*(a + b*acoth(c*x))**(n + S(1))/(b*c*d*(n + S(1))), x)
    rule6427 = ReplacementRule(pattern6427, replacement6427)
    pattern6428 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons17, cons1781)
    def replacement6428(m, b, d, a, c, x, e):
        rubi.append(6428)
        return Int(ExpandIntegrand(a + b*atanh(c*x), x**m/(d + e*x**S(2)), x), x)
    rule6428 = ReplacementRule(pattern6428, replacement6428)
    pattern6429 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons17, cons1781)
    def replacement6429(m, b, d, a, c, x, e):
        rubi.append(6429)
        return Int(ExpandIntegrand(a + b*acoth(c*x), x**m/(d + e*x**S(2)), x), x)
    rule6429 = ReplacementRule(pattern6429, replacement6429)
    pattern6430 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons88, cons54)
    def replacement6430(p, b, d, a, n, c, x, e):
        rubi.append(6430)
        return Dist(b*n/(S(2)*c*(p + S(1))), Int((a + b*atanh(c*x))**(n + S(-1))*(d + e*x**S(2))**p, x), x) + Simp((a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6430 = ReplacementRule(pattern6430, replacement6430)
    pattern6431 = Pattern(Integral(x_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons88, cons54)
    def replacement6431(p, b, d, a, n, c, x, e):
        rubi.append(6431)
        return Dist(b*n/(S(2)*c*(p + S(1))), Int((a + b*acoth(c*x))**(n + S(-1))*(d + e*x**S(2))**p, x), x) + Simp((a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6431 = ReplacementRule(pattern6431, replacement6431)
    pattern6432 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons89, cons1442)
    def replacement6432(b, d, a, c, n, x, e):
        rubi.append(6432)
        return Dist(S(4)/(b**S(2)*(n + S(1))*(n + S(2))), Int(x*(a + b*atanh(c*x))**(n + S(2))/(d + e*x**S(2))**S(2), x), x) + Simp((a + b*atanh(c*x))**(n + S(2))*(c**S(2)*x**S(2) + S(1))/(b**S(2)*e*(d + e*x**S(2))*(n + S(1))*(n + S(2))), x) + Simp(x*(a + b*atanh(c*x))**(n + S(1))/(b*c*d*(d + e*x**S(2))*(n + S(1))), x)
    rule6432 = ReplacementRule(pattern6432, replacement6432)
    pattern6433 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons89, cons1442)
    def replacement6433(b, d, a, c, n, x, e):
        rubi.append(6433)
        return Dist(S(4)/(b**S(2)*(n + S(1))*(n + S(2))), Int(x*(a + b*acoth(c*x))**(n + S(2))/(d + e*x**S(2))**S(2), x), x) + Simp((a + b*acoth(c*x))**(n + S(2))*(c**S(2)*x**S(2) + S(1))/(b**S(2)*e*(d + e*x**S(2))*(n + S(1))*(n + S(2))), x) + Simp(x*(a + b*acoth(c*x))**(n + S(1))/(b*c*d*(d + e*x**S(2))*(n + S(1))), x)
    rule6433 = ReplacementRule(pattern6433, replacement6433)
    pattern6434 = Pattern(Integral(x_**S(2)*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons13, cons137, cons1782)
    def replacement6434(p, b, d, a, c, x, e):
        rubi.append(6434)
        return Dist(S(1)/(S(2)*c**S(2)*d*(p + S(1))), Int((a + b*atanh(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(b*(d + e*x**S(2))**(p + S(1))/(S(4)*c**S(3)*d*(p + S(1))**S(2)), x) - Simp(x*(a + b*atanh(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*c**S(2)*d*(p + S(1))), x)
    rule6434 = ReplacementRule(pattern6434, replacement6434)
    pattern6435 = Pattern(Integral(x_**S(2)*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons13, cons137, cons1782)
    def replacement6435(p, b, d, a, c, x, e):
        rubi.append(6435)
        return Dist(S(1)/(S(2)*c**S(2)*d*(p + S(1))), Int((a + b*acoth(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(b*(d + e*x**S(2))**(p + S(1))/(S(4)*c**S(3)*d*(p + S(1))**S(2)), x) - Simp(x*(a + b*acoth(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*c**S(2)*d*(p + S(1))), x)
    rule6435 = ReplacementRule(pattern6435, replacement6435)
    pattern6436 = Pattern(Integral(x_**S(2)*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement6436(b, d, a, n, c, x, e):
        rubi.append(6436)
        return -Dist(b*n/(S(2)*c), Int(x*(a + b*atanh(c*x))**(n + S(-1))/(d + e*x**S(2))**S(2), x), x) - Simp((a + b*atanh(c*x))**(n + S(1))/(S(2)*b*c**S(3)*d**S(2)*(n + S(1))), x) + Simp(x*(a + b*atanh(c*x))**n/(S(2)*c**S(2)*d*(d + e*x**S(2))), x)
    rule6436 = ReplacementRule(pattern6436, replacement6436)
    pattern6437 = Pattern(Integral(x_**S(2)*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement6437(b, d, a, n, c, x, e):
        rubi.append(6437)
        return -Dist(b*n/(S(2)*c), Int(x*(a + b*acoth(c*x))**(n + S(-1))/(d + e*x**S(2))**S(2), x), x) - Simp((a + b*acoth(c*x))**(n + S(1))/(S(2)*b*c**S(3)*d**S(2)*(n + S(1))), x) + Simp(x*(a + b*acoth(c*x))**n/(S(2)*c**S(2)*d*(d + e*x**S(2))), x)
    rule6437 = ReplacementRule(pattern6437, replacement6437)
    pattern6438 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons240, cons13, cons137)
    def replacement6438(p, m, b, d, a, c, x, e):
        rubi.append(6438)
        return -Dist((m + S(-1))/(c**S(2)*d*m), Int(x**(m + S(-2))*(a + b*atanh(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(b*x**m*(d + e*x**S(2))**(p + S(1))/(c*d*m**S(2)), x) + Simp(x**(m + S(-1))*(a + b*atanh(c*x))*(d + e*x**S(2))**(p + S(1))/(c**S(2)*d*m), x)
    rule6438 = ReplacementRule(pattern6438, replacement6438)
    pattern6439 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons240, cons13, cons137)
    def replacement6439(p, m, b, d, a, c, x, e):
        rubi.append(6439)
        return -Dist((m + S(-1))/(c**S(2)*d*m), Int(x**(m + S(-2))*(a + b*acoth(c*x))*(d + e*x**S(2))**(p + S(1)), x), x) - Simp(b*x**m*(d + e*x**S(2))**(p + S(1))/(c*d*m**S(2)), x) + Simp(x**(m + S(-1))*(a + b*acoth(c*x))*(d + e*x**S(2))**(p + S(1))/(c**S(2)*d*m), x)
    rule6439 = ReplacementRule(pattern6439, replacement6439)
    pattern6440 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons240, cons338, cons137, cons165)
    def replacement6440(p, m, b, d, a, c, n, x, e):
        rubi.append(6440)
        return Dist(b**S(2)*n*(n + S(-1))/m**S(2), Int(x**m*(a + b*atanh(c*x))**(n + S(-2))*(d + e*x**S(2))**p, x), x) - Dist((m + S(-1))/(c**S(2)*d*m), Int(x**(m + S(-2))*(a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) + Simp(x**(m + S(-1))*(a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(c**S(2)*d*m), x) - Simp(b*n*x**m*(a + b*atanh(c*x))**(n + S(-1))*(d + e*x**S(2))**(p + S(1))/(c*d*m**S(2)), x)
    rule6440 = ReplacementRule(pattern6440, replacement6440)
    pattern6441 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons240, cons338, cons137, cons165)
    def replacement6441(p, m, b, d, a, c, n, x, e):
        rubi.append(6441)
        return Dist(b**S(2)*n*(n + S(-1))/m**S(2), Int(x**m*(a + b*acoth(c*x))**(n + S(-2))*(d + e*x**S(2))**p, x), x) - Dist((m + S(-1))/(c**S(2)*d*m), Int(x**(m + S(-2))*(a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) + Simp(x**(m + S(-1))*(a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(1))/(c**S(2)*d*m), x) - Simp(b*n*x**m*(a + b*acoth(c*x))**(n + S(-1))*(d + e*x**S(2))**(p + S(1))/(c*d*m**S(2)), x)
    rule6441 = ReplacementRule(pattern6441, replacement6441)
    pattern6442 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1737, cons240, cons87, cons89)
    def replacement6442(p, m, b, d, a, c, n, x, e):
        rubi.append(6442)
        return -Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*atanh(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Simp(x**m*(a + b*atanh(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule6442 = ReplacementRule(pattern6442, replacement6442)
    pattern6443 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1737, cons240, cons87, cons89)
    def replacement6443(p, m, b, d, a, c, n, x, e):
        rubi.append(6443)
        return -Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*acoth(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Simp(x**m*(a + b*acoth(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule6443 = ReplacementRule(pattern6443, replacement6443)
    pattern6444 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1737, cons242, cons87, cons88, cons66)
    def replacement6444(p, m, b, d, a, n, c, x, e):
        rubi.append(6444)
        return -Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*atanh(c*x))**(n + S(-1))*(d + e*x**S(2))**p, x), x) + Simp(x**(m + S(1))*(a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*(m + S(1))), x)
    rule6444 = ReplacementRule(pattern6444, replacement6444)
    pattern6445 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1737, cons242, cons87, cons88, cons66)
    def replacement6445(p, m, b, d, a, n, c, x, e):
        rubi.append(6445)
        return -Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*acoth(c*x))**(n + S(-1))*(d + e*x**S(2))**p, x), x) + Simp(x**(m + S(1))*(a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(1))/(d*(m + S(1))), x)
    rule6445 = ReplacementRule(pattern6445, replacement6445)
    pattern6446 = Pattern(Integral(x_**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons241)
    def replacement6446(m, b, d, a, c, x, e):
        rubi.append(6446)
        return Dist(d/(m + S(2)), Int(x**m*(a + b*atanh(c*x))/sqrt(d + e*x**S(2)), x), x) - Dist(b*c*d/(m + S(2)), Int(x**(m + S(1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*atanh(c*x))*sqrt(d + e*x**S(2))/(m + S(2)), x)
    rule6446 = ReplacementRule(pattern6446, replacement6446)
    pattern6447 = Pattern(Integral(x_**m_*sqrt(d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons241)
    def replacement6447(m, b, d, a, c, x, e):
        rubi.append(6447)
        return Dist(d/(m + S(2)), Int(x**m*(a + b*acoth(c*x))/sqrt(d + e*x**S(2)), x), x) - Dist(b*c*d/(m + S(2)), Int(x**(m + S(1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*acoth(c*x))*sqrt(d + e*x**S(2))/(m + S(2)), x)
    rule6447 = ReplacementRule(pattern6447, replacement6447)
    pattern6448 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons148, cons38, cons146)
    def replacement6448(p, m, b, d, a, n, c, x, e):
        rubi.append(6448)
        return Int(ExpandIntegrand(x**m*(a + b*atanh(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule6448 = ReplacementRule(pattern6448, replacement6448)
    pattern6449 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons148, cons38, cons146)
    def replacement6449(p, m, b, d, a, n, c, x, e):
        rubi.append(6449)
        return Int(ExpandIntegrand(x**m*(a + b*acoth(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule6449 = ReplacementRule(pattern6449, replacement6449)
    pattern6450 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons13, cons163, cons148, cons1783)
    def replacement6450(p, m, b, d, a, n, c, x, e):
        rubi.append(6450)
        return Dist(d, Int(x**m*(a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(c**S(2)*d, Int(x**(m + S(2))*(a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x)
    rule6450 = ReplacementRule(pattern6450, replacement6450)
    pattern6451 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1737, cons13, cons163, cons148, cons1783)
    def replacement6451(p, m, b, d, a, n, c, x, e):
        rubi.append(6451)
        return Dist(d, Int(x**m*(a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x) - Dist(c**S(2)*d, Int(x**(m + S(2))*(a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(-1)), x), x)
    rule6451 = ReplacementRule(pattern6451, replacement6451)
    pattern6452 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons93, cons88, cons166)
    def replacement6452(m, b, d, a, n, c, x, e):
        rubi.append(6452)
        return Dist((m + S(-1))/(c**S(2)*m), Int(x**(m + S(-2))*(a + b*atanh(c*x))**n/sqrt(d + e*x**S(2)), x), x) + Dist(b*n/(c*m), Int(x**(m + S(-1))*(a + b*atanh(c*x))**(n + S(-1))/sqrt(d + e*x**S(2)), x), x) - Simp(x**(m + S(-1))*(a + b*atanh(c*x))**n*sqrt(d + e*x**S(2))/(c**S(2)*d*m), x)
    rule6452 = ReplacementRule(pattern6452, replacement6452)
    pattern6453 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons93, cons88, cons166)
    def replacement6453(m, b, d, a, n, c, x, e):
        rubi.append(6453)
        return Dist((m + S(-1))/(c**S(2)*m), Int(x**(m + S(-2))*(a + b*acoth(c*x))**n/sqrt(d + e*x**S(2)), x), x) + Dist(b*n/(c*m), Int(x**(m + S(-1))*(a + b*acoth(c*x))**(n + S(-1))/sqrt(d + e*x**S(2)), x), x) - Simp(x**(m + S(-1))*(a + b*acoth(c*x))**n*sqrt(d + e*x**S(2))/(c**S(2)*d*m), x)
    rule6453 = ReplacementRule(pattern6453, replacement6453)
    pattern6454 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons268)
    def replacement6454(b, d, a, c, x, e):
        rubi.append(6454)
        return Simp(b*PolyLog(S(2), -sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/sqrt(d), x) - Simp(b*PolyLog(S(2), sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/sqrt(d), x) + Simp(-S(2)*(a + b*atanh(c*x))*atanh(sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/sqrt(d), x)
    rule6454 = ReplacementRule(pattern6454, replacement6454)
    pattern6455 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons268)
    def replacement6455(b, d, a, c, x, e):
        rubi.append(6455)
        return Simp(b*PolyLog(S(2), -sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/sqrt(d), x) - Simp(b*PolyLog(S(2), sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/sqrt(d), x) + Simp(-S(2)*(a + b*acoth(c*x))*atanh(sqrt(-c*x + S(1))/sqrt(c*x + S(1)))/sqrt(d), x)
    rule6455 = ReplacementRule(pattern6455, replacement6455)
    pattern6456 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**n_/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148, cons268)
    def replacement6456(b, d, a, c, n, x, e):
        rubi.append(6456)
        return Dist(S(1)/sqrt(d), Subst(Int((a + b*x)**n/sinh(x), x), x, atanh(c*x)), x)
    rule6456 = ReplacementRule(pattern6456, replacement6456)
    pattern6457 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**n_/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148, cons268)
    def replacement6457(b, d, a, c, n, x, e):
        rubi.append(6457)
        return -Dist(c*x*sqrt(S(1) - S(1)/(c**S(2)*x**S(2)))/sqrt(d + e*x**S(2)), Subst(Int((a + b*x)**n/cosh(x), x), x, acoth(c*x)), x)
    rule6457 = ReplacementRule(pattern6457, replacement6457)
    pattern6458 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148, cons1738)
    def replacement6458(b, d, a, n, c, x, e):
        rubi.append(6458)
        return Dist(sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*atanh(c*x))**n/(x*sqrt(-c**S(2)*x**S(2) + S(1))), x), x)
    rule6458 = ReplacementRule(pattern6458, replacement6458)
    pattern6459 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(x_*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons148, cons1738)
    def replacement6459(b, d, a, n, c, x, e):
        rubi.append(6459)
        return Dist(sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int((a + b*acoth(c*x))**n/(x*sqrt(-c**S(2)*x**S(2) + S(1))), x), x)
    rule6459 = ReplacementRule(pattern6459, replacement6459)
    pattern6460 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(x_**S(2)*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement6460(b, d, a, n, c, x, e):
        rubi.append(6460)
        return Dist(b*c*n, Int((a + b*atanh(c*x))**(n + S(-1))/(x*sqrt(d + e*x**S(2))), x), x) - Simp((a + b*atanh(c*x))**n*sqrt(d + e*x**S(2))/(d*x), x)
    rule6460 = ReplacementRule(pattern6460, replacement6460)
    pattern6461 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/(x_**S(2)*sqrt(d_ + x_**S(2)*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88)
    def replacement6461(b, d, a, n, c, x, e):
        rubi.append(6461)
        return Dist(b*c*n, Int((a + b*acoth(c*x))**(n + S(-1))/(x*sqrt(d + e*x**S(2))), x), x) - Simp((a + b*acoth(c*x))**n*sqrt(d + e*x**S(2))/(d*x), x)
    rule6461 = ReplacementRule(pattern6461, replacement6461)
    pattern6462 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons93, cons88, cons94, cons1510)
    def replacement6462(m, b, d, a, n, c, x, e):
        rubi.append(6462)
        return Dist(c**S(2)*(m + S(2))/(m + S(1)), Int(x**(m + S(2))*(a + b*atanh(c*x))**n/sqrt(d + e*x**S(2)), x), x) - Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*atanh(c*x))**(n + S(-1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*atanh(c*x))**n*sqrt(d + e*x**S(2))/(d*(m + S(1))), x)
    rule6462 = ReplacementRule(pattern6462, replacement6462)
    pattern6463 = Pattern(Integral(x_**m_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))/sqrt(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons93, cons88, cons94, cons1510)
    def replacement6463(m, b, d, a, n, c, x, e):
        rubi.append(6463)
        return Dist(c**S(2)*(m + S(2))/(m + S(1)), Int(x**(m + S(2))*(a + b*acoth(c*x))**n/sqrt(d + e*x**S(2)), x), x) - Dist(b*c*n/(m + S(1)), Int(x**(m + S(1))*(a + b*acoth(c*x))**(n + S(-1))/sqrt(d + e*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*acoth(c*x))**n*sqrt(d + e*x**S(2))/(d*(m + S(1))), x)
    rule6463 = ReplacementRule(pattern6463, replacement6463)
    pattern6464 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons1784, cons137, cons166, cons1152)
    def replacement6464(p, m, b, d, a, n, c, x, e):
        rubi.append(6464)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*atanh(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule6464 = ReplacementRule(pattern6464, replacement6464)
    pattern6465 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons1784, cons137, cons166, cons1152)
    def replacement6465(p, m, b, d, a, n, c, x, e):
        rubi.append(6465)
        return Dist(S(1)/e, Int(x**(m + S(-2))*(a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(d/e, Int(x**(m + S(-2))*(a + b*acoth(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule6465 = ReplacementRule(pattern6465, replacement6465)
    pattern6466 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons1784, cons137, cons267, cons1152)
    def replacement6466(p, m, b, d, a, n, c, x, e):
        rubi.append(6466)
        return Dist(S(1)/d, Int(x**m*(a + b*atanh(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*atanh(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule6466 = ReplacementRule(pattern6466, replacement6466)
    pattern6467 = Pattern(Integral(x_**m_*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons1784, cons137, cons267, cons1152)
    def replacement6467(p, m, b, d, a, n, c, x, e):
        rubi.append(6467)
        return Dist(S(1)/d, Int(x**m*(a + b*acoth(c*x))**n*(d + e*x**S(2))**(p + S(1)), x), x) - Dist(e/d, Int(x**(m + S(2))*(a + b*acoth(c*x))**n*(d + e*x**S(2))**p, x), x)
    rule6467 = ReplacementRule(pattern6467, replacement6467)
    pattern6468 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons162, cons137, cons89, cons319)
    def replacement6468(p, m, b, d, a, n, c, x, e):
        rubi.append(6468)
        return -Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*atanh(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Dist(c*(m + S(2)*p + S(2))/(b*(n + S(1))), Int(x**(m + S(1))*(a + b*atanh(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Simp(x**m*(a + b*atanh(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule6468 = ReplacementRule(pattern6468, replacement6468)
    pattern6469 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons162, cons137, cons89, cons319)
    def replacement6469(p, m, b, d, a, n, c, x, e):
        rubi.append(6469)
        return -Dist(m/(b*c*(n + S(1))), Int(x**(m + S(-1))*(a + b*acoth(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Dist(c*(m + S(2)*p + S(2))/(b*(n + S(1))), Int(x**(m + S(1))*(a + b*acoth(c*x))**(n + S(1))*(d + e*x**S(2))**p, x), x) + Simp(x**m*(a + b*acoth(c*x))**(n + S(1))*(d + e*x**S(2))**(p + S(1))/(b*c*d*(n + S(1))), x)
    rule6469 = ReplacementRule(pattern6469, replacement6469)
    pattern6470 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons62, cons1785, cons1740)
    def replacement6470(p, m, b, d, a, n, c, x, e):
        rubi.append(6470)
        return Dist(c**(-m + S(-1))*d**p, Subst(Int((a + b*x)**n*sinh(x)**m*cosh(x)**(-m - S(2)*p + S(-2)), x), x, atanh(c*x)), x)
    rule6470 = ReplacementRule(pattern6470, replacement6470)
    pattern6471 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons62, cons1785, cons1741)
    def replacement6471(p, m, b, d, a, n, c, x, e):
        rubi.append(6471)
        return Dist(d**(p + S(1)/2)*sqrt(-c**S(2)*x**S(2) + S(1))/sqrt(d + e*x**S(2)), Int(x**m*(a + b*atanh(c*x))**n*(-c**S(2)*x**S(2) + S(1))**p, x), x)
    rule6471 = ReplacementRule(pattern6471, replacement6471)
    pattern6472 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons62, cons1785, cons38)
    def replacement6472(p, m, b, d, a, n, c, x, e):
        rubi.append(6472)
        return -Dist(c**(-m + S(-1))*(-d)**p, Subst(Int((a + b*x)**n*sinh(x)**(-m - S(2)*p + S(-2))*cosh(x)**m, x), x, acoth(c*x)), x)
    rule6472 = ReplacementRule(pattern6472, replacement6472)
    pattern6473 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**p_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons62, cons1785, cons147)
    def replacement6473(p, m, b, d, a, n, c, x, e):
        rubi.append(6473)
        return -Dist(c**(-m)*x*(-d)**(p + S(1)/2)*sqrt((c**S(2)*x**S(2) + S(-1))/(c**S(2)*x**S(2)))/sqrt(d + e*x**S(2)), Subst(Int((a + b*x)**n*sinh(x)**(-m - S(2)*p + S(-2))*cosh(x)**m, x), x, acoth(c*x)), x)
    rule6473 = ReplacementRule(pattern6473, replacement6473)
    pattern6474 = Pattern(Integral(x_*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement6474(p, b, d, a, c, x, e):
        rubi.append(6474)
        return -Dist(b*c/(S(2)*e*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*atanh(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6474 = ReplacementRule(pattern6474, replacement6474)
    pattern6475 = Pattern(Integral(x_*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement6475(p, b, d, a, c, x, e):
        rubi.append(6475)
        return -Dist(b*c/(S(2)*e*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/(-c**S(2)*x**S(2) + S(1)), x), x) + Simp((a + b*acoth(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6475 = ReplacementRule(pattern6475, replacement6475)
    def With6476(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(d + e*x**S(2))**p, x)
        rubi.append(6476)
        return -Dist(b*c, Int(SimplifyIntegrand(u/(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*atanh(c*x), u, x)
    pattern6476 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1786)
    rule6476 = ReplacementRule(pattern6476, With6476)
    def With6477(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(d + e*x**S(2))**p, x)
        rubi.append(6477)
        return -Dist(b*c, Int(SimplifyIntegrand(u/(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acoth(c*x), u, x)
    pattern6477 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1786)
    rule6477 = ReplacementRule(pattern6477, With6477)
    pattern6478 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons1787)
    def replacement6478(p, m, b, d, a, n, c, x, e):
        rubi.append(6478)
        return Int(ExpandIntegrand((a + b*atanh(c*x))**n, x**m*(d + e*x**S(2))**p, x), x)
    rule6478 = ReplacementRule(pattern6478, replacement6478)
    pattern6479 = Pattern(Integral(x_**WC('m', S(1))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons1787)
    def replacement6479(p, m, b, d, a, n, c, x, e):
        rubi.append(6479)
        return Int(ExpandIntegrand((a + b*acoth(c*x))**n, x**m*(d + e*x**S(2))**p, x), x)
    rule6479 = ReplacementRule(pattern6479, replacement6479)
    pattern6480 = Pattern(Integral(x_**WC('m', S(1))*(a_ + WC('b', S(1))*atanh(x_*WC('c', S(1))))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1788)
    def replacement6480(p, m, b, d, c, a, x, e):
        rubi.append(6480)
        return Dist(a, Int(x**m*(d + e*x**S(2))**p, x), x) + Dist(b, Int(x**m*(d + e*x**S(2))**p*atanh(c*x), x), x)
    rule6480 = ReplacementRule(pattern6480, replacement6480)
    pattern6481 = Pattern(Integral(x_**WC('m', S(1))*(a_ + WC('b', S(1))*acoth(x_*WC('c', S(1))))*(d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1788)
    def replacement6481(p, m, b, d, c, a, x, e):
        rubi.append(6481)
        return Dist(a, Int(x**m*(d + e*x**S(2))**p, x), x) + Dist(b, Int(x**m*(d + e*x**S(2))**p*acoth(c*x), x), x)
    rule6481 = ReplacementRule(pattern6481, replacement6481)
    pattern6482 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement6482(p, m, b, d, a, n, c, x, e):
        rubi.append(6482)
        return Int(x**m*(a + b*atanh(c*x))**n*(d + e*x**S(2))**p, x)
    rule6482 = ReplacementRule(pattern6482, replacement6482)
    pattern6483 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement6483(p, m, b, d, a, n, c, x, e):
        rubi.append(6483)
        return Int(x**m*(a + b*acoth(c*x))**n*(d + e*x**S(2))**p, x)
    rule6483 = ReplacementRule(pattern6483, replacement6483)
    pattern6484 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))*atanh(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons1910)
    def replacement6484(u, b, d, a, n, c, x, e):
        rubi.append(6484)
        return -Dist(S(1)/2, Int((a + b*atanh(c*x))**n*log(-u + S(1))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int((a + b*atanh(c*x))**n*log(u + S(1))/(d + e*x**S(2)), x), x)
    rule6484 = ReplacementRule(pattern6484, replacement6484)
    pattern6485 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))*acoth(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons1910)
    def replacement6485(u, b, d, a, n, c, x, e):
        rubi.append(6485)
        return -Dist(S(1)/2, Int((a + b*acoth(c*x))**n*log(SimplifyIntegrand(S(1) - S(1)/u, x))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int((a + b*acoth(c*x))**n*log(SimplifyIntegrand(S(1) + S(1)/u, x))/(d + e*x**S(2)), x), x)
    rule6485 = ReplacementRule(pattern6485, replacement6485)
    pattern6486 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))*atanh(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons1911)
    def replacement6486(u, b, d, a, n, c, x, e):
        rubi.append(6486)
        return -Dist(S(1)/2, Int((a + b*atanh(c*x))**n*log(-u + S(1))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int((a + b*atanh(c*x))**n*log(u + S(1))/(d + e*x**S(2)), x), x)
    rule6486 = ReplacementRule(pattern6486, replacement6486)
    pattern6487 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))*acoth(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons1911)
    def replacement6487(u, b, d, a, n, c, x, e):
        rubi.append(6487)
        return -Dist(S(1)/2, Int((a + b*acoth(c*x))**n*log(SimplifyIntegrand(S(1) - S(1)/u, x))/(d + e*x**S(2)), x), x) + Dist(S(1)/2, Int((a + b*acoth(c*x))**n*log(SimplifyIntegrand(S(1) + S(1)/u, x))/(d + e*x**S(2)), x), x)
    rule6487 = ReplacementRule(pattern6487, replacement6487)
    pattern6488 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))*log(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons1912)
    def replacement6488(u, b, d, a, n, c, x, e):
        rubi.append(6488)
        return -Dist(b*n/S(2), Int((a + b*atanh(c*x))**(n + S(-1))*PolyLog(S(2), Together(-u + S(1)))/(d + e*x**S(2)), x), x) + Simp((a + b*atanh(c*x))**n*PolyLog(S(2), Together(-u + S(1)))/(S(2)*c*d), x)
    rule6488 = ReplacementRule(pattern6488, replacement6488)
    pattern6489 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))*log(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons1912)
    def replacement6489(u, b, d, a, n, c, x, e):
        rubi.append(6489)
        return -Dist(b*n/S(2), Int((a + b*acoth(c*x))**(n + S(-1))*PolyLog(S(2), Together(-u + S(1)))/(d + e*x**S(2)), x), x) + Simp((a + b*acoth(c*x))**n*PolyLog(S(2), Together(-u + S(1)))/(S(2)*c*d), x)
    rule6489 = ReplacementRule(pattern6489, replacement6489)
    pattern6490 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))*log(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons1913)
    def replacement6490(u, b, d, a, n, c, x, e):
        rubi.append(6490)
        return Dist(b*n/S(2), Int((a + b*atanh(c*x))**(n + S(-1))*PolyLog(S(2), Together(-u + S(1)))/(d + e*x**S(2)), x), x) - Simp((a + b*atanh(c*x))**n*PolyLog(S(2), Together(-u + S(1)))/(S(2)*c*d), x)
    rule6490 = ReplacementRule(pattern6490, replacement6490)
    pattern6491 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))*log(u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons87, cons88, cons1913)
    def replacement6491(u, b, d, a, n, c, x, e):
        rubi.append(6491)
        return Dist(b*n/S(2), Int((a + b*acoth(c*x))**(n + S(-1))*PolyLog(S(2), Together(-u + S(1)))/(d + e*x**S(2)), x), x) - Simp((a + b*acoth(c*x))**n*PolyLog(S(2), Together(-u + S(1)))/(S(2)*c*d), x)
    rule6491 = ReplacementRule(pattern6491, replacement6491)
    pattern6492 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))*PolyLog(p_, u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons88, cons1910)
    def replacement6492(p, u, b, d, a, n, c, x, e):
        rubi.append(6492)
        return Dist(b*n/S(2), Int((a + b*atanh(c*x))**(n + S(-1))*PolyLog(p + S(1), u)/(d + e*x**S(2)), x), x) - Simp((a + b*atanh(c*x))**n*PolyLog(p + S(1), u)/(S(2)*c*d), x)
    rule6492 = ReplacementRule(pattern6492, replacement6492)
    pattern6493 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))*PolyLog(p_, u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons88, cons1910)
    def replacement6493(p, u, b, d, a, n, c, x, e):
        rubi.append(6493)
        return Dist(b*n/S(2), Int((a + b*acoth(c*x))**(n + S(-1))*PolyLog(p + S(1), u)/(d + e*x**S(2)), x), x) - Simp((a + b*acoth(c*x))**n*PolyLog(p + S(1), u)/(S(2)*c*d), x)
    rule6493 = ReplacementRule(pattern6493, replacement6493)
    pattern6494 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))*PolyLog(p_, u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons88, cons1911)
    def replacement6494(p, u, b, d, a, n, c, x, e):
        rubi.append(6494)
        return -Dist(b*n/S(2), Int((a + b*atanh(c*x))**(n + S(-1))*PolyLog(p + S(1), u)/(d + e*x**S(2)), x), x) + Simp((a + b*atanh(c*x))**n*PolyLog(p + S(1), u)/(S(2)*c*d), x)
    rule6494 = ReplacementRule(pattern6494, replacement6494)
    pattern6495 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))*PolyLog(p_, u_)/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1737, cons87, cons88, cons1911)
    def replacement6495(p, u, b, d, a, n, c, x, e):
        rubi.append(6495)
        return -Dist(b*n/S(2), Int((a + b*acoth(c*x))**(n + S(-1))*PolyLog(p + S(1), u)/(d + e*x**S(2)), x), x) + Simp((a + b*acoth(c*x))**n*PolyLog(p + S(1), u)/(S(2)*c*d), x)
    rule6495 = ReplacementRule(pattern6495, replacement6495)
    pattern6496 = Pattern(Integral(S(1)/((d_ + x_**S(2)*WC('e', S(1)))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))), x_), cons2, cons3, cons7, cons27, cons48, cons1737)
    def replacement6496(b, d, a, c, x, e):
        rubi.append(6496)
        return Simp((-log(a + b*acoth(c*x)) + log(a + b*atanh(c*x)))/(b**S(2)*c*d*(acoth(c*x) - atanh(c*x))), x)
    rule6496 = ReplacementRule(pattern6496, replacement6496)
    pattern6497 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('n', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons150, cons1793)
    def replacement6497(m, b, d, a, n, c, x, e):
        rubi.append(6497)
        return -Dist(n/(m + S(1)), Int((a + b*acoth(c*x))**(m + S(1))*(a + b*atanh(c*x))**(n + S(-1))/(d + e*x**S(2)), x), x) + Simp((a + b*acoth(c*x))**(m + S(1))*(a + b*atanh(c*x))**n/(b*c*d*(m + S(1))), x)
    rule6497 = ReplacementRule(pattern6497, replacement6497)
    pattern6498 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**WC('m', S(1))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons1737, cons150, cons1794)
    def replacement6498(m, b, d, a, n, c, x, e):
        rubi.append(6498)
        return -Dist(n/(m + S(1)), Int((a + b*acoth(c*x))**(n + S(-1))*(a + b*atanh(c*x))**(m + S(1))/(d + e*x**S(2)), x), x) + Simp((a + b*acoth(c*x))**n*(a + b*atanh(c*x))**(m + S(1))/(b*c*d*(m + S(1))), x)
    rule6498 = ReplacementRule(pattern6498, replacement6498)
    pattern6499 = Pattern(Integral(atanh(x_*WC('a', S(1)))/(c_ + x_**WC('n', S(1))*WC('d', S(1))), x_), cons2, cons7, cons27, cons85, cons1914)
    def replacement6499(d, a, n, c, x):
        rubi.append(6499)
        return -Dist(S(1)/2, Int(log(-a*x + S(1))/(c + d*x**n), x), x) + Dist(S(1)/2, Int(log(a*x + S(1))/(c + d*x**n), x), x)
    rule6499 = ReplacementRule(pattern6499, replacement6499)
    pattern6500 = Pattern(Integral(acoth(x_*WC('a', S(1)))/(c_ + x_**WC('n', S(1))*WC('d', S(1))), x_), cons2, cons7, cons27, cons85, cons1914)
    def replacement6500(d, a, n, c, x):
        rubi.append(6500)
        return -Dist(S(1)/2, Int(log(S(1) - S(1)/(a*x))/(c + d*x**n), x), x) + Dist(S(1)/2, Int(log(S(1) + S(1)/(a*x))/(c + d*x**n), x), x)
    rule6500 = ReplacementRule(pattern6500, replacement6500)
    pattern6501 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1796)
    def replacement6501(f, b, g, d, a, c, x, e):
        rubi.append(6501)
        return -Dist(b*c, Int(x*(d + e*log(f + g*x**S(2)))/(-c**S(2)*x**S(2) + S(1)), x), x) - Dist(S(2)*e*g, Int(x**S(2)*(a + b*atanh(c*x))/(f + g*x**S(2)), x), x) + Simp(x*(a + b*atanh(c*x))*(d + e*log(f + g*x**S(2))), x)
    rule6501 = ReplacementRule(pattern6501, replacement6501)
    pattern6502 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1796)
    def replacement6502(f, b, g, d, a, c, x, e):
        rubi.append(6502)
        return -Dist(b*c, Int(x*(d + e*log(f + g*x**S(2)))/(-c**S(2)*x**S(2) + S(1)), x), x) - Dist(S(2)*e*g, Int(x**S(2)*(a + b*acoth(c*x))/(f + g*x**S(2)), x), x) + Simp(x*(a + b*acoth(c*x))*(d + e*log(f + g*x**S(2))), x)
    rule6502 = ReplacementRule(pattern6502, replacement6502)
    pattern6503 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons601)
    def replacement6503(m, f, b, g, d, a, c, x, e):
        rubi.append(6503)
        return -Dist(b*c/(m + S(1)), Int(x**(m + S(1))*(d + e*log(f + g*x**S(2)))/(-c**S(2)*x**S(2) + S(1)), x), x) - Dist(S(2)*e*g/(m + S(1)), Int(x**(m + S(2))*(a + b*atanh(c*x))/(f + g*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*atanh(c*x))*(d + e*log(f + g*x**S(2)))/(m + S(1)), x)
    rule6503 = ReplacementRule(pattern6503, replacement6503)
    pattern6504 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons601)
    def replacement6504(m, f, b, g, d, a, c, x, e):
        rubi.append(6504)
        return -Dist(b*c/(m + S(1)), Int(x**(m + S(1))*(d + e*log(f + g*x**S(2)))/(-c**S(2)*x**S(2) + S(1)), x), x) - Dist(S(2)*e*g/(m + S(1)), Int(x**(m + S(2))*(a + b*acoth(c*x))/(f + g*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*acoth(c*x))*(d + e*log(f + g*x**S(2)))/(m + S(1)), x)
    rule6504 = ReplacementRule(pattern6504, replacement6504)
    def With6505(m, f, b, g, d, a, c, x, e):
        u = IntHide(x**m*(d + e*log(f + g*x**S(2))), x)
        rubi.append(6505)
        return -Dist(b*c, Int(ExpandIntegrand(u/(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*atanh(c*x), u, x)
    pattern6505 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1797)
    rule6505 = ReplacementRule(pattern6505, With6505)
    def With6506(m, f, b, g, d, a, c, x, e):
        u = IntHide(x**m*(d + e*log(f + g*x**S(2))), x)
        rubi.append(6506)
        return -Dist(b*c, Int(ExpandIntegrand(u/(-c**S(2)*x**S(2) + S(1)), x), x), x) + Dist(a + b*acoth(c*x), u, x)
    pattern6506 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1797)
    rule6506 = ReplacementRule(pattern6506, With6506)
    def With6507(m, f, b, g, d, a, c, x, e):
        u = IntHide(x**m*(a + b*atanh(c*x)), x)
        rubi.append(6507)
        return -Dist(S(2)*e*g, Int(ExpandIntegrand(u*x/(f + g*x**S(2)), x), x), x) + Dist(d + e*log(f + g*x**S(2)), u, x)
    pattern6507 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons17, cons261)
    rule6507 = ReplacementRule(pattern6507, With6507)
    def With6508(m, f, b, g, d, a, c, x, e):
        u = IntHide(x**m*(a + b*acoth(c*x)), x)
        rubi.append(6508)
        return -Dist(S(2)*e*g, Int(ExpandIntegrand(u*x/(f + g*x**S(2)), x), x), x) + Dist(d + e*log(f + g*x**S(2)), u, x)
    pattern6508 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))*(WC('d', S(0)) + WC('e', S(1))*log(x_**S(2)*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons17, cons261)
    rule6508 = ReplacementRule(pattern6508, With6508)
    pattern6509 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*atanh(x_*WC('c', S(1))))**S(2)*(WC('d', S(0)) + WC('e', S(1))*log(f_ + x_**S(2)*WC('g', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1915)
    def replacement6509(g, b, f, d, a, c, x, e):
        rubi.append(6509)
        return Dist(b/c, Int((a + b*atanh(c*x))*(d + e*log(f + g*x**S(2))), x), x) + Dist(b*c*e, Int(x**S(2)*(a + b*atanh(c*x))/(-c**S(2)*x**S(2) + S(1)), x), x) - Simp(e*x**S(2)*(a + b*atanh(c*x))**S(2)/S(2), x) + Simp((a + b*atanh(c*x))**S(2)*(d + e*log(f + g*x**S(2)))*(f + g*x**S(2))/(S(2)*g), x)
    rule6509 = ReplacementRule(pattern6509, replacement6509)
    pattern6510 = Pattern(Integral(x_*(WC('a', S(0)) + WC('b', S(1))*acoth(x_*WC('c', S(1))))**S(2)*(WC('d', S(0)) + WC('e', S(1))*log(f_ + x_**S(2)*WC('g', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1915)
    def replacement6510(g, b, f, d, a, c, x, e):
        rubi.append(6510)
        return Dist(b/c, Int((a + b*acoth(c*x))*(d + e*log(f + g*x**S(2))), x), x) + Dist(b*c*e, Int(x**S(2)*(a + b*acoth(c*x))/(-c**S(2)*x**S(2) + S(1)), x), x) - Simp(e*x**S(2)*(a + b*acoth(c*x))**S(2)/S(2), x) + Simp((a + b*acoth(c*x))**S(2)*(d + e*log(f + g*x**S(2)))*(f + g*x**S(2))/(S(2)*g), x)
    rule6510 = ReplacementRule(pattern6510, replacement6510)
    pattern6511 = Pattern(Integral(exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons1482)
    def replacement6511(x, a, n):
        rubi.append(6511)
        return Int((-a*x + S(1))**(-n/S(2) + S(1)/2)*(a*x + S(1))**(n/S(2) + S(1)/2)/sqrt(-a**S(2)*x**S(2) + S(1)), x)
    rule6511 = ReplacementRule(pattern6511, replacement6511)
    pattern6512 = Pattern(Integral(x_**WC('m', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons21, cons1482)
    def replacement6512(x, m, a, n):
        rubi.append(6512)
        return Int(x**m*(-a*x + S(1))**(-n/S(2) + S(1)/2)*(a*x + S(1))**(n/S(2) + S(1)/2)/sqrt(-a**S(2)*x**S(2) + S(1)), x)
    rule6512 = ReplacementRule(pattern6512, replacement6512)
    pattern6513 = Pattern(Integral(exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons4, cons1441)
    def replacement6513(x, a, n):
        rubi.append(6513)
        return Int((-a*x + S(1))**(-n/S(2))*(a*x + S(1))**(n/S(2)), x)
    rule6513 = ReplacementRule(pattern6513, replacement6513)
    pattern6514 = Pattern(Integral(x_**WC('m', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons21, cons4, cons1441)
    def replacement6514(x, m, a, n):
        rubi.append(6514)
        return Int(x**m*(-a*x + S(1))**(-n/S(2))*(a*x + S(1))**(n/S(2)), x)
    rule6514 = ReplacementRule(pattern6514, replacement6514)
    pattern6515 = Pattern(Integral((c_ + x_*WC('d', S(1)))**WC('p', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1916, cons1250, cons246)
    def replacement6515(p, d, a, n, c, x):
        rubi.append(6515)
        return Dist(c**n, Int((c + d*x)**(-n + p)*(-a**S(2)*x**S(2) + S(1))**(n/S(2)), x), x)
    rule6515 = ReplacementRule(pattern6515, replacement6515)
    pattern6516 = Pattern(Integral((c_ + x_*WC('d', S(1)))**WC('p', S(1))*(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons48, cons125, cons21, cons5, cons1916, cons1250, cons1917, cons246)
    def replacement6516(p, m, f, d, a, n, c, x, e):
        rubi.append(6516)
        return Dist(c**n, Int((c + d*x)**(-n + p)*(e + f*x)**m*(-a**S(2)*x**S(2) + S(1))**(n/S(2)), x), x)
    rule6516 = ReplacementRule(pattern6516, replacement6516)
    pattern6517 = Pattern(Integral((c_ + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1918, cons1802)
    def replacement6517(p, u, d, a, n, c, x):
        rubi.append(6517)
        return Dist(c**p, Int(u*(S(1) + d*x/c)**p*(-a*x + S(1))**(-n/S(2))*(a*x + S(1))**(n/S(2)), x), x)
    rule6517 = ReplacementRule(pattern6517, replacement6517)
    pattern6518 = Pattern(Integral((c_ + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1918, cons1803)
    def replacement6518(p, u, d, a, n, c, x):
        rubi.append(6518)
        return Int(u*(c + d*x)**p*(-a*x + S(1))**(-n/S(2))*(a*x + S(1))**(n/S(2)), x)
    rule6518 = ReplacementRule(pattern6518, replacement6518)
    pattern6519 = Pattern(Integral((c_ + WC('d', S(1))/x_)**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1919, cons38)
    def replacement6519(p, u, d, a, n, c, x):
        rubi.append(6519)
        return Dist(d**p, Int(u*x**(-p)*(c*x/d + S(1))**p*exp(n*atanh(a*x)), x), x)
    rule6519 = ReplacementRule(pattern6519, replacement6519)
    pattern6520 = Pattern(Integral((c_ + WC('d', S(1))/x_)**p_*WC('u', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1919, cons147, cons743, cons177)
    def replacement6520(p, u, d, a, n, c, x):
        rubi.append(6520)
        return Dist((S(-1))**(n/S(2))*c**p, Int(u*(S(1) - S(1)/(a*x))**(-n/S(2))*(S(1) + S(1)/(a*x))**(n/S(2))*(S(1) + d/(c*x))**p, x), x)
    rule6520 = ReplacementRule(pattern6520, replacement6520)
    pattern6521 = Pattern(Integral((c_ + WC('d', S(1))/x_)**p_*WC('u', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1919, cons147, cons743, cons117)
    def replacement6521(p, u, d, a, n, c, x):
        rubi.append(6521)
        return Int(u*(c + d/x)**p*(-a*x + S(1))**(-n/S(2))*(a*x + S(1))**(n/S(2)), x)
    rule6521 = ReplacementRule(pattern6521, replacement6521)
    pattern6522 = Pattern(Integral((c_ + WC('d', S(1))/x_)**p_*WC('u', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1919, cons147)
    def replacement6522(p, u, d, a, n, c, x):
        rubi.append(6522)
        return Dist(x**p*(c + d/x)**p*(c*x/d + S(1))**(-p), Int(u*x**(-p)*(c*x/d + S(1))**p*exp(n*atanh(a*x)), x), x)
    rule6522 = ReplacementRule(pattern6522, replacement6522)
    pattern6523 = Pattern(Integral(exp(n_*atanh(x_*WC('a', S(1))))/(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2), x_), cons2, cons7, cons27, cons4, cons1920, cons23)
    def replacement6523(d, a, n, c, x):
        rubi.append(6523)
        return Simp((-a*x + n)*exp(n*atanh(a*x))/(a*c*sqrt(c + d*x**S(2))*(n**S(2) + S(-1))), x)
    rule6523 = ReplacementRule(pattern6523, replacement6523)
    pattern6524 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons13, cons137, cons23, cons1921, cons246)
    def replacement6524(p, d, a, n, c, x):
        rubi.append(6524)
        return -Dist(S(2)*(p + S(1))*(S(2)*p + S(3))/(c*(n**S(2) - S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*atanh(a*x)), x), x) + Simp((c + d*x**S(2))**(p + S(1))*(S(2)*a*x*(p + S(1)) + n)*exp(n*atanh(a*x))/(a*c*(n**S(2) - S(4)*(p + S(1))**S(2))), x)
    rule6524 = ReplacementRule(pattern6524, replacement6524)
    pattern6525 = Pattern(Integral(exp(WC('n', S(1))*atanh(x_*WC('a', S(1))))/(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons7, cons27, cons4, cons1920, cons1922)
    def replacement6525(d, a, n, c, x):
        rubi.append(6525)
        return Simp(exp(n*atanh(a*x))/(a*c*n), x)
    rule6525 = ReplacementRule(pattern6525, replacement6525)
    pattern6526 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1920, cons38, cons1923, cons1924)
    def replacement6526(p, d, a, n, c, x):
        rubi.append(6526)
        return Dist(c**p, Int((a*x + S(1))**n*(-a**S(2)*x**S(2) + S(1))**(-n/S(2) + p), x), x)
    rule6526 = ReplacementRule(pattern6526, replacement6526)
    pattern6527 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1920, cons38, cons1925, cons1924)
    def replacement6527(p, d, a, n, c, x):
        rubi.append(6527)
        return Dist(c**p, Int((-a*x + S(1))**(-n)*(-a**S(2)*x**S(2) + S(1))**(n/S(2) + p), x), x)
    rule6527 = ReplacementRule(pattern6527, replacement6527)
    pattern6528 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1920, cons1802)
    def replacement6528(p, d, a, n, c, x):
        rubi.append(6528)
        return Dist(c**p, Int((-a*x + S(1))**(-n/S(2) + p)*(a*x + S(1))**(n/S(2) + p), x), x)
    rule6528 = ReplacementRule(pattern6528, replacement6528)
    pattern6529 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1920, cons1803, cons674)
    def replacement6529(p, d, a, n, c, x):
        rubi.append(6529)
        return Dist(c**(n/S(2)), Int((c + d*x**S(2))**(-n/S(2) + p)*(a*x + S(1))**n, x), x)
    rule6529 = ReplacementRule(pattern6529, replacement6529)
    pattern6530 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1920, cons1803, cons1926)
    def replacement6530(p, d, a, n, c, x):
        rubi.append(6530)
        return Dist(c**(-n/S(2)), Int((c + d*x**S(2))**(n/S(2) + p)*(-a*x + S(1))**(-n), x), x)
    rule6530 = ReplacementRule(pattern6530, replacement6530)
    pattern6531 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1920, cons1803)
    def replacement6531(p, d, a, n, c, x):
        rubi.append(6531)
        return Dist(c**IntPart(p)*(c + d*x**S(2))**FracPart(p)*(-a**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int((-a**S(2)*x**S(2) + S(1))**p*exp(n*atanh(a*x)), x), x)
    rule6531 = ReplacementRule(pattern6531, replacement6531)
    pattern6532 = Pattern(Integral(x_*exp(n_*atanh(x_*WC('a', S(1))))/(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2), x_), cons2, cons7, cons27, cons4, cons1920, cons23)
    def replacement6532(d, a, n, c, x):
        rubi.append(6532)
        return Simp((-a*n*x + S(1))*exp(n*atanh(a*x))/(d*sqrt(c + d*x**S(2))*(n**S(2) + S(-1))), x)
    rule6532 = ReplacementRule(pattern6532, replacement6532)
    pattern6533 = Pattern(Integral(x_*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons13, cons137, cons23, cons246)
    def replacement6533(p, d, a, n, c, x):
        rubi.append(6533)
        return -Dist(a*c*n/(S(2)*d*(p + S(1))), Int((c + d*x**S(2))**p*exp(n*atanh(a*x)), x), x) + Simp((c + d*x**S(2))**(p + S(1))*exp(n*atanh(a*x))/(S(2)*d*(p + S(1))), x)
    rule6533 = ReplacementRule(pattern6533, replacement6533)
    pattern6534 = Pattern(Integral(x_**S(2)*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons1927, cons23)
    def replacement6534(p, d, a, n, c, x):
        rubi.append(6534)
        return Simp((c + d*x**S(2))**(p + S(1))*(-a*n*x + S(1))*exp(n*atanh(a*x))/(a*d*n*(n**S(2) + S(-1))), x)
    rule6534 = ReplacementRule(pattern6534, replacement6534)
    pattern6535 = Pattern(Integral(x_**S(2)*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons13, cons137, cons23, cons1921, cons246)
    def replacement6535(p, d, a, n, c, x):
        rubi.append(6535)
        return Dist((n**S(2) + S(2)*p + S(2))/(d*(n**S(2) - S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*atanh(a*x)), x), x) - Simp((c + d*x**S(2))**(p + S(1))*(S(2)*a*x*(p + S(1)) + n)*exp(n*atanh(a*x))/(a*d*(n**S(2) - S(4)*(p + S(1))**S(2))), x)
    rule6535 = ReplacementRule(pattern6535, replacement6535)
    pattern6536 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons5, cons1920, cons1802, cons1923, cons1924)
    def replacement6536(p, m, d, a, n, c, x):
        rubi.append(6536)
        return Dist(c**p, Int(x**m*(a*x + S(1))**n*(-a**S(2)*x**S(2) + S(1))**(-n/S(2) + p), x), x)
    rule6536 = ReplacementRule(pattern6536, replacement6536)
    pattern6537 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons5, cons1920, cons1802, cons1925, cons1924)
    def replacement6537(p, m, d, a, n, c, x):
        rubi.append(6537)
        return Dist(c**p, Int(x**m*(-a*x + S(1))**(-n)*(-a**S(2)*x**S(2) + S(1))**(n/S(2) + p), x), x)
    rule6537 = ReplacementRule(pattern6537, replacement6537)
    pattern6538 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons4, cons5, cons1920, cons1802)
    def replacement6538(p, m, d, a, n, c, x):
        rubi.append(6538)
        return Dist(c**p, Int(x**m*(-a*x + S(1))**(-n/S(2) + p)*(a*x + S(1))**(n/S(2) + p), x), x)
    rule6538 = ReplacementRule(pattern6538, replacement6538)
    pattern6539 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons5, cons1920, cons1803, cons674)
    def replacement6539(p, m, d, a, n, c, x):
        rubi.append(6539)
        return Dist(c**(n/S(2)), Int(x**m*(c + d*x**S(2))**(-n/S(2) + p)*(a*x + S(1))**n, x), x)
    rule6539 = ReplacementRule(pattern6539, replacement6539)
    pattern6540 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons5, cons1920, cons1803, cons1926)
    def replacement6540(p, m, d, a, n, c, x):
        rubi.append(6540)
        return Dist(c**(-n/S(2)), Int(x**m*(c + d*x**S(2))**(n/S(2) + p)*(-a*x + S(1))**(-n), x), x)
    rule6540 = ReplacementRule(pattern6540, replacement6540)
    pattern6541 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons4, cons5, cons1920, cons1803, cons1922)
    def replacement6541(p, m, d, a, n, c, x):
        rubi.append(6541)
        return Dist(c**IntPart(p)*(c + d*x**S(2))**FracPart(p)*(-a**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int(x**m*(-a**S(2)*x**S(2) + S(1))**p*exp(n*atanh(a*x)), x), x)
    rule6541 = ReplacementRule(pattern6541, replacement6541)
    pattern6542 = Pattern(Integral(u_*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1920, cons1802)
    def replacement6542(p, u, d, a, n, c, x):
        rubi.append(6542)
        return Dist(c**p, Int(u*(-a*x + S(1))**(-n/S(2) + p)*(a*x + S(1))**(n/S(2) + p), x), x)
    rule6542 = ReplacementRule(pattern6542, replacement6542)
    pattern6543 = Pattern(Integral(u_*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1920, cons1803, cons743)
    def replacement6543(p, u, d, a, n, c, x):
        rubi.append(6543)
        return Dist(c**IntPart(p)*(c + d*x**S(2))**FracPart(p)*(-a*x + S(1))**(-FracPart(p))*(a*x + S(1))**(-FracPart(p)), Int(u*(-a*x + S(1))**(-n/S(2) + p)*(a*x + S(1))**(n/S(2) + p), x), x)
    rule6543 = ReplacementRule(pattern6543, replacement6543)
    pattern6544 = Pattern(Integral(u_*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1920, cons1803, cons1922)
    def replacement6544(p, u, d, a, n, c, x):
        rubi.append(6544)
        return Dist(c**IntPart(p)*(c + d*x**S(2))**FracPart(p)*(-a**S(2)*x**S(2) + S(1))**(-FracPart(p)), Int(u*(-a**S(2)*x**S(2) + S(1))**p*exp(n*atanh(a*x)), x), x)
    rule6544 = ReplacementRule(pattern6544, replacement6544)
    pattern6545 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1928, cons38)
    def replacement6545(p, u, d, a, n, c, x):
        rubi.append(6545)
        return Dist(d**p, Int(u*x**(-S(2)*p)*(-a**S(2)*x**S(2) + S(1))**p*exp(n*atanh(a*x)), x), x)
    rule6545 = ReplacementRule(pattern6545, replacement6545)
    pattern6546 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**p_*WC('u', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1928, cons147, cons743, cons177)
    def replacement6546(p, u, d, a, n, c, x):
        rubi.append(6546)
        return Dist(c**p, Int(u*(S(1) - S(1)/(a*x))**p*(S(1) + S(1)/(a*x))**p*exp(n*atanh(a*x)), x), x)
    rule6546 = ReplacementRule(pattern6546, replacement6546)
    pattern6547 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**p_*WC('u', S(1))*exp(n_*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1928, cons147, cons743, cons117)
    def replacement6547(p, u, d, a, n, c, x):
        rubi.append(6547)
        return Dist(x**(S(2)*p)*(c + d/x**S(2))**p*(-a*x + S(1))**(-p)*(a*x + S(1))**(-p), Int(u*x**(-S(2)*p)*(-a*x + S(1))**p*(a*x + S(1))**p*exp(n*atanh(a*x)), x), x)
    rule6547 = ReplacementRule(pattern6547, replacement6547)
    pattern6548 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**p_*WC('u', S(1))*exp(WC('n', S(1))*atanh(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1928, cons147, cons1922)
    def replacement6548(p, u, d, a, n, c, x):
        rubi.append(6548)
        return Dist(x**(S(2)*p)*(c + d/x**S(2))**p*(c*x**S(2)/d + S(1))**(-p), Int(u*x**(-S(2)*p)*(c*x**S(2)/d + S(1))**p*exp(n*atanh(a*x)), x), x)
    rule6548 = ReplacementRule(pattern6548, replacement6548)
    pattern6549 = Pattern(Integral(exp(WC('n', S(1))*atanh((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement6549(b, c, n, a, x):
        rubi.append(6549)
        return Int((-a*c - b*c*x + S(1))**(-n/S(2))*(a*c + b*c*x + S(1))**(n/S(2)), x)
    rule6549 = ReplacementRule(pattern6549, replacement6549)
    pattern6550 = Pattern(Integral(x_**m_*exp(n_*atanh((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons84, cons87, cons994)
    def replacement6550(m, b, c, n, a, x):
        rubi.append(6550)
        return Dist(S(4)*b**(-m + S(-1))*c**(-m + S(-1))/n, Subst(Int(x**(S(2)/n)*(x**(S(2)/n) + S(1))**(-m + S(-2))*(-a*c + x**(S(2)/n)*(-a*c + S(1)) + S(-1))**m, x), x, (-c*(a + b*x) + S(1))**(-n/S(2))*(c*(a + b*x) + S(1))**(n/S(2))), x)
    rule6550 = ReplacementRule(pattern6550, replacement6550)
    pattern6551 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*exp(WC('n', S(1))*atanh((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1580)
    def replacement6551(m, b, d, c, n, a, x, e):
        rubi.append(6551)
        return Int((d + e*x)**m*(-a*c - b*c*x + S(1))**(-n/S(2))*(a*c + b*c*x + S(1))**(n/S(2)), x)
    rule6551 = ReplacementRule(pattern6551, replacement6551)
    pattern6552 = Pattern(Integral((c_ + x_**S(2)*WC('e', S(1)) + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*atanh(a_ + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1818, cons1929, cons1930)
    def replacement6552(p, u, b, d, a, n, c, x, e):
        rubi.append(6552)
        return Dist((c/(-a**S(2) + S(1)))**p, Int(u*(-a - b*x + S(1))**(-n/S(2) + p)*(a + b*x + S(1))**(n/S(2) + p), x), x)
    rule6552 = ReplacementRule(pattern6552, replacement6552)
    pattern6553 = Pattern(Integral((c_ + x_**S(2)*WC('e', S(1)) + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*atanh(a_ + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1818, cons1929, cons1931)
    def replacement6553(p, u, b, d, a, n, c, x, e):
        rubi.append(6553)
        return Dist((c + d*x + e*x**S(2))**p*(-a**S(2) - S(2)*a*b*x - b**S(2)*x**S(2) + S(1))**(-p), Int(u*(-a**S(2) - S(2)*a*b*x - b**S(2)*x**S(2) + S(1))**p*exp(n*atanh(a*x)), x), x)
    rule6553 = ReplacementRule(pattern6553, replacement6553)
    pattern6554 = Pattern(Integral(WC('u', S(1))*exp(WC('n', S(1))*atanh(WC('c', S(1))/(x_*WC('b', S(1)) + WC('a', S(0))))), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement6554(u, b, c, n, a, x):
        rubi.append(6554)
        return Int(u*exp(n*acoth(a/c + b*x/c)), x)
    rule6554 = ReplacementRule(pattern6554, replacement6554)
    pattern6555 = Pattern(Integral(WC('u', S(1))*exp(n_*acoth(x_*WC('a', S(1)))), x_), cons2, cons743)
    def replacement6555(x, a, n, u):
        rubi.append(6555)
        return Dist((S(-1))**(n/S(2)), Int(u*exp(n*atanh(a*x)), x), x)
    rule6555 = ReplacementRule(pattern6555, replacement6555)
    pattern6556 = Pattern(Integral(exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons1482)
    def replacement6556(x, a, n):
        rubi.append(6556)
        return -Subst(Int((S(1) - x/a)**(-n/S(2) + S(1)/2)*(S(1) + x/a)**(n/S(2) + S(1)/2)/(x**S(2)*sqrt(S(1) - x**S(2)/a**S(2))), x), x, S(1)/x)
    rule6556 = ReplacementRule(pattern6556, replacement6556)
    pattern6557 = Pattern(Integral(x_**WC('m', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons1482, cons17)
    def replacement6557(x, m, a, n):
        rubi.append(6557)
        return -Subst(Int(x**(-m + S(-2))*(S(1) - x/a)**(-n/S(2) + S(1)/2)*(S(1) + x/a)**(n/S(2) + S(1)/2)/sqrt(S(1) - x**S(2)/a**S(2)), x), x, S(1)/x)
    rule6557 = ReplacementRule(pattern6557, replacement6557)
    pattern6558 = Pattern(Integral(exp(n_*acoth(x_*WC('a', S(1)))), x_), cons2, cons4, cons23)
    def replacement6558(x, a, n):
        rubi.append(6558)
        return -Subst(Int((S(1) - x/a)**(-n/S(2))*(S(1) + x/a)**(n/S(2))/x**S(2), x), x, S(1)/x)
    rule6558 = ReplacementRule(pattern6558, replacement6558)
    pattern6559 = Pattern(Integral(x_**WC('m', S(1))*exp(n_*acoth(x_*WC('a', S(1)))), x_), cons2, cons4, cons23, cons17)
    def replacement6559(x, m, a, n):
        rubi.append(6559)
        return -Subst(Int(x**(-m + S(-2))*(S(1) - x/a)**(-n/S(2))*(S(1) + x/a)**(n/S(2)), x), x, S(1)/x)
    rule6559 = ReplacementRule(pattern6559, replacement6559)
    pattern6560 = Pattern(Integral(x_**m_*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons21, cons1482, cons18)
    def replacement6560(x, m, a, n):
        rubi.append(6560)
        return -Dist(x**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(S(1) - x/a)**(-n/S(2) + S(1)/2)*(S(1) + x/a)**(n/S(2) + S(1)/2)/sqrt(S(1) - x**S(2)/a**S(2)), x), x, S(1)/x), x)
    rule6560 = ReplacementRule(pattern6560, replacement6560)
    pattern6561 = Pattern(Integral(x_**m_*exp(n_*acoth(x_*WC('a', S(1)))), x_), cons2, cons21, cons4, cons23, cons18)
    def replacement6561(x, m, a, n):
        rubi.append(6561)
        return -Dist(x**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(S(1) - x/a)**(-n/S(2))*(S(1) + x/a)**(n/S(2)), x), x, S(1)/x), x)
    rule6561 = ReplacementRule(pattern6561, replacement6561)
    pattern6562 = Pattern(Integral((c_ + x_*WC('d', S(1)))**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1916, cons1932, cons1922)
    def replacement6562(p, d, a, n, c, x):
        rubi.append(6562)
        return Simp((c + d*x)**p*(a*x + S(1))*exp(n*acoth(a*x))/(a*(p + S(1))), x)
    rule6562 = ReplacementRule(pattern6562, replacement6562)
    pattern6563 = Pattern(Integral((c_ + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1918, cons1922, cons38)
    def replacement6563(p, u, d, a, n, c, x):
        rubi.append(6563)
        return Dist(d**p, Int(u*x**p*(c/(d*x) + S(1))**p*exp(n*acoth(a*x)), x), x)
    rule6563 = ReplacementRule(pattern6563, replacement6563)
    pattern6564 = Pattern(Integral((c_ + x_*WC('d', S(1)))**p_*WC('u', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1918, cons1922, cons147)
    def replacement6564(p, u, d, a, n, c, x):
        rubi.append(6564)
        return Dist(x**(-p)*(c + d*x)**p*(c/(d*x) + S(1))**(-p), Int(u*x**p*(c/(d*x) + S(1))**p*exp(n*acoth(a*x)), x), x)
    rule6564 = ReplacementRule(pattern6564, replacement6564)
    pattern6565 = Pattern(Integral((c_ + WC('d', S(1))/x_)**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1933, cons1250, cons1917, cons246)
    def replacement6565(p, d, a, n, c, x):
        rubi.append(6565)
        return -Dist(c**n, Subst(Int((S(1) - x**S(2)/a**S(2))**(n/S(2))*(c + d*x)**(-n + p)/x**S(2), x), x, S(1)/x), x)
    rule6565 = ReplacementRule(pattern6565, replacement6565)
    pattern6566 = Pattern(Integral(x_**WC('m', S(1))*(c_ + WC('d', S(1))/x_)**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons5, cons1933, cons1250, cons17, cons1934, cons246)
    def replacement6566(p, m, d, a, n, c, x):
        rubi.append(6566)
        return -Dist(c**n, Subst(Int(x**(-m + S(-2))*(S(1) - x**S(2)/a**S(2))**(n/S(2))*(c + d*x)**(-n + p), x), x, S(1)/x), x)
    rule6566 = ReplacementRule(pattern6566, replacement6566)
    pattern6567 = Pattern(Integral((c_ + WC('d', S(1))/x_)**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1919, cons1922, cons1802)
    def replacement6567(p, d, a, n, c, x):
        rubi.append(6567)
        return -Dist(c**p, Subst(Int((S(1) - x/a)**(-n/S(2))*(S(1) + x/a)**(n/S(2))*(S(1) + d*x/c)**p/x**S(2), x), x, S(1)/x), x)
    rule6567 = ReplacementRule(pattern6567, replacement6567)
    pattern6568 = Pattern(Integral(x_**WC('m', S(1))*(c_ + WC('d', S(1))/x_)**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1919, cons1922, cons1802, cons17)
    def replacement6568(p, m, d, a, n, c, x):
        rubi.append(6568)
        return -Dist(c**p, Subst(Int(x**(-m + S(-2))*(S(1) - x/a)**(-n/S(2))*(S(1) + x/a)**(n/S(2))*(S(1) + d*x/c)**p, x), x, S(1)/x), x)
    rule6568 = ReplacementRule(pattern6568, replacement6568)
    pattern6569 = Pattern(Integral(x_**m_*(c_ + WC('d', S(1))/x_)**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons4, cons5, cons1919, cons1922, cons1802, cons18)
    def replacement6569(p, m, d, a, n, c, x):
        rubi.append(6569)
        return -Dist(c**p*x**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(S(1) - x/a)**(-n/S(2))*(S(1) + x/a)**(n/S(2))*(S(1) + d*x/c)**p, x), x, S(1)/x), x)
    rule6569 = ReplacementRule(pattern6569, replacement6569)
    pattern6570 = Pattern(Integral((c_ + WC('d', S(1))/x_)**p_*WC('u', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1919, cons1922, cons1803)
    def replacement6570(p, u, d, a, n, c, x):
        rubi.append(6570)
        return Dist((S(1) + d/(c*x))**(-p)*(c + d/x)**p, Int(u*(S(1) + d/(c*x))**p*exp(n*acoth(a*x)), x), x)
    rule6570 = ReplacementRule(pattern6570, replacement6570)
    pattern6571 = Pattern(Integral(exp(WC('n', S(1))*acoth(x_*WC('a', S(1))))/(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons7, cons27, cons4, cons1920, cons1922)
    def replacement6571(d, a, n, c, x):
        rubi.append(6571)
        return Simp(exp(n*acoth(a*x))/(a*c*n), x)
    rule6571 = ReplacementRule(pattern6571, replacement6571)
    pattern6572 = Pattern(Integral(exp(n_*acoth(x_*WC('a', S(1))))/(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2), x_), cons2, cons7, cons27, cons4, cons1920, cons23)
    def replacement6572(d, a, n, c, x):
        rubi.append(6572)
        return Simp((-a*x + n)*exp(n*acoth(a*x))/(a*c*sqrt(c + d*x**S(2))*(n**S(2) + S(-1))), x)
    rule6572 = ReplacementRule(pattern6572, replacement6572)
    pattern6573 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons1922, cons13, cons137, cons230, cons1921, cons1935)
    def replacement6573(p, d, a, n, c, x):
        rubi.append(6573)
        return -Dist(S(2)*(p + S(1))*(S(2)*p + S(3))/(c*(n**S(2) - S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*acoth(a*x)), x), x) + Simp((c + d*x**S(2))**(p + S(1))*(S(2)*a*x*(p + S(1)) + n)*exp(n*acoth(a*x))/(a*c*(n**S(2) - S(4)*(p + S(1))**S(2))), x)
    rule6573 = ReplacementRule(pattern6573, replacement6573)
    pattern6574 = Pattern(Integral(x_*exp(n_*acoth(x_*WC('a', S(1))))/(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2), x_), cons2, cons7, cons27, cons4, cons1920, cons23)
    def replacement6574(d, a, n, c, x):
        rubi.append(6574)
        return -Simp((-a*n*x + S(1))*exp(n*acoth(a*x))/(a**S(2)*c*sqrt(c + d*x**S(2))*(n**S(2) + S(-1))), x)
    rule6574 = ReplacementRule(pattern6574, replacement6574)
    pattern6575 = Pattern(Integral(x_*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons1922, cons13, cons1824, cons230, cons1921, cons1935)
    def replacement6575(p, d, a, n, c, x):
        rubi.append(6575)
        return -Dist(n*(S(2)*p + S(3))/(a*c*(n**S(2) - S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*acoth(a*x)), x), x) + Simp((c + d*x**S(2))**(p + S(1))*(a*n*x + S(2)*p + S(2))*exp(n*acoth(a*x))/(a**S(2)*c*(n**S(2) - S(4)*(p + S(1))**S(2))), x)
    rule6575 = ReplacementRule(pattern6575, replacement6575)
    pattern6576 = Pattern(Integral(x_**S(2)*(c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons1922, cons1927, cons973)
    def replacement6576(p, d, a, n, c, x):
        rubi.append(6576)
        return -Simp((c + d*x**S(2))**(p + S(1))*(S(2)*a*x*(p + S(1)) + n)*exp(n*acoth(a*x))/(a**S(3)*c*n**S(2)*(n**S(2) + S(-1))), x)
    rule6576 = ReplacementRule(pattern6576, replacement6576)
    pattern6577 = Pattern(Integral(x_**S(2)*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons1922, cons13, cons1824, cons1936, cons1921, cons1935)
    def replacement6577(p, d, a, n, c, x):
        rubi.append(6577)
        return -Dist((n**S(2) + S(2)*p + S(2))/(a**S(2)*c*(n**S(2) - S(4)*(p + S(1))**S(2))), Int((c + d*x**S(2))**(p + S(1))*exp(n*acoth(a*x)), x), x) + Simp((c + d*x**S(2))**(p + S(1))*(S(2)*a*x*(p + S(1)) + n)*exp(n*acoth(a*x))/(a**S(3)*c*(n**S(2) - S(4)*(p + S(1))**S(2))), x)
    rule6577 = ReplacementRule(pattern6577, replacement6577)
    pattern6578 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**S(2)*WC('d', S(1)))**p_*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons1922, cons17, cons13, cons1827, cons38)
    def replacement6578(p, m, d, a, n, c, x):
        rubi.append(6578)
        return -Dist(a**(-m + S(-1))*(-c)**p, Subst(Int((S(1)/tanh(x))**(m + S(2)*p + S(2))*exp(n*x)*cosh(x)**(-S(2)*p + S(-2)), x), x, acoth(a*x)), x)
    rule6578 = ReplacementRule(pattern6578, replacement6578)
    pattern6579 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons1920, cons1922, cons38)
    def replacement6579(p, u, d, a, n, c, x):
        rubi.append(6579)
        return Dist(d**p, Int(u*x**(S(2)*p)*(S(1) - S(1)/(a**S(2)*x**S(2)))**p*exp(n*acoth(a*x)), x), x)
    rule6579 = ReplacementRule(pattern6579, replacement6579)
    pattern6580 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**p_*WC('u', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1920, cons1922, cons147)
    def replacement6580(p, u, d, a, n, c, x):
        rubi.append(6580)
        return Dist(x**(-S(2)*p)*(S(1) - S(1)/(a**S(2)*x**S(2)))**(-p)*(c + d*x**S(2))**p, Int(u*x**(S(2)*p)*(S(1) - S(1)/(a**S(2)*x**S(2)))**p*exp(n*acoth(a*x)), x), x)
    rule6580 = ReplacementRule(pattern6580, replacement6580)
    pattern6581 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1928, cons1922, cons1802, cons1937)
    def replacement6581(p, u, d, a, n, c, x):
        rubi.append(6581)
        return Dist(a**(-S(2)*p)*c**p, Int(u*x**(-S(2)*p)*(a*x + S(-1))**(-n/S(2) + p)*(a*x + S(1))**(n/S(2) + p), x), x)
    rule6581 = ReplacementRule(pattern6581, replacement6581)
    pattern6582 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1928, cons1922, cons1802, cons1938)
    def replacement6582(p, d, a, n, c, x):
        rubi.append(6582)
        return -Dist(c**p, Subst(Int((S(1) - x/a)**(-n/S(2) + p)*(S(1) + x/a)**(n/S(2) + p)/x**S(2), x), x, S(1)/x), x)
    rule6582 = ReplacementRule(pattern6582, replacement6582)
    pattern6583 = Pattern(Integral(x_**WC('m', S(1))*(c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1928, cons1922, cons1802, cons1938, cons17)
    def replacement6583(p, m, d, a, n, c, x):
        rubi.append(6583)
        return -Dist(c**p, Subst(Int(x**(-m + S(-2))*(S(1) - x/a)**(-n/S(2) + p)*(S(1) + x/a)**(n/S(2) + p), x), x, S(1)/x), x)
    rule6583 = ReplacementRule(pattern6583, replacement6583)
    pattern6584 = Pattern(Integral(x_**m_*(c_ + WC('d', S(1))/x_**S(2))**WC('p', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons21, cons4, cons5, cons1928, cons1922, cons1802, cons1938, cons18)
    def replacement6584(p, m, d, a, n, c, x):
        rubi.append(6584)
        return -Dist(c**p*x**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(S(1) - x/a)**(-n/S(2) + p)*(S(1) + x/a)**(n/S(2) + p), x), x, S(1)/x), x)
    rule6584 = ReplacementRule(pattern6584, replacement6584)
    pattern6585 = Pattern(Integral((c_ + WC('d', S(1))/x_**S(2))**p_*WC('u', S(1))*exp(WC('n', S(1))*acoth(x_*WC('a', S(1)))), x_), cons2, cons7, cons27, cons4, cons5, cons1928, cons1922, cons1803)
    def replacement6585(p, u, d, a, n, c, x):
        rubi.append(6585)
        return Dist(c**IntPart(p)*(S(1) - S(1)/(a**S(2)*x**S(2)))**(-FracPart(p))*(c + d/x**S(2))**FracPart(p), Int(u*(S(1) - S(1)/(a**S(2)*x**S(2)))**p*exp(n*acoth(a*x)), x), x)
    rule6585 = ReplacementRule(pattern6585, replacement6585)
    pattern6586 = Pattern(Integral(WC('u', S(1))*exp(n_*acoth((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons743)
    def replacement6586(u, b, c, a, n, x):
        rubi.append(6586)
        return Dist((S(-1))**(n/S(2)), Int(u*exp(n*atanh(c*(a + b*x))), x), x)
    rule6586 = ReplacementRule(pattern6586, replacement6586)
    pattern6587 = Pattern(Integral(exp(WC('n', S(1))*acoth((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons4, cons1922)
    def replacement6587(b, c, n, a, x):
        rubi.append(6587)
        return Dist((c*(a + b*x))**(n/S(2))*(S(1) + S(1)/(c*(a + b*x)))**(n/S(2))*(a*c + b*c*x + S(1))**(-n/S(2)), Int((a*c + b*c*x + S(-1))**(-n/S(2))*(a*c + b*c*x + S(1))**(n/S(2)), x), x)
    rule6587 = ReplacementRule(pattern6587, replacement6587)
    pattern6588 = Pattern(Integral(x_**m_*exp(n_*acoth((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons84, cons87, cons994)
    def replacement6588(m, b, c, n, a, x):
        rubi.append(6588)
        return Dist(-S(4)*b**(-m + S(-1))*c**(-m + S(-1))/n, Subst(Int(x**(S(2)/n)*(x**(S(2)/n) + S(-1))**(-m + S(-2))*(a*c + x**(S(2)/n)*(-a*c + S(1)) + S(1))**m, x), x, (S(1) - S(1)/(c*(a + b*x)))**(-n/S(2))*(S(1) + S(1)/(c*(a + b*x)))**(n/S(2))), x)
    rule6588 = ReplacementRule(pattern6588, replacement6588)
    pattern6589 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*exp(WC('n', S(1))*acoth((a_ + x_*WC('b', S(1)))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons1922)
    def replacement6589(m, b, d, c, n, a, x, e):
        rubi.append(6589)
        return Dist((c*(a + b*x))**(n/S(2))*(S(1) + S(1)/(c*(a + b*x)))**(n/S(2))*(a*c + b*c*x + S(1))**(-n/S(2)), Int((d + e*x)**m*(a*c + b*c*x + S(-1))**(-n/S(2))*(a*c + b*c*x + S(1))**(n/S(2)), x), x)
    rule6589 = ReplacementRule(pattern6589, replacement6589)
    pattern6590 = Pattern(Integral((c_ + x_**S(2)*WC('e', S(1)) + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acoth(a_ + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1922, cons1818, cons1929, cons1930)
    def replacement6590(p, u, b, d, a, n, c, x, e):
        rubi.append(6590)
        return Dist((c/(-a**S(2) + S(1)))**p*((a + b*x + S(1))/(a + b*x))**(n/S(2))*((a + b*x)/(a + b*x + S(1)))**(n/S(2))*(-a - b*x + S(1))**(n/S(2))*(a + b*x + S(-1))**(-n/S(2)), Int(u*(-a - b*x + S(1))**(-n/S(2) + p)*(a + b*x + S(1))**(n/S(2) + p), x), x)
    rule6590 = ReplacementRule(pattern6590, replacement6590)
    pattern6591 = Pattern(Integral((c_ + x_**S(2)*WC('e', S(1)) + x_*WC('d', S(1)))**WC('p', S(1))*WC('u', S(1))*exp(WC('n', S(1))*acoth(a_ + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1922, cons1818, cons1929, cons1931)
    def replacement6591(p, u, b, d, a, n, c, x, e):
        rubi.append(6591)
        return Dist((c + d*x + e*x**S(2))**p*(-a**S(2) - S(2)*a*b*x - b**S(2)*x**S(2) + S(1))**(-p), Int(u*(-a**S(2) - S(2)*a*b*x - b**S(2)*x**S(2) + S(1))**p*exp(n*acoth(a*x)), x), x)
    rule6591 = ReplacementRule(pattern6591, replacement6591)
    pattern6592 = Pattern(Integral(WC('u', S(1))*exp(WC('n', S(1))*acoth(WC('c', S(1))/(x_*WC('b', S(1)) + WC('a', S(0))))), x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement6592(u, b, c, n, a, x):
        rubi.append(6592)
        return Int(u*exp(n*atanh(a/c + b*x/c)), x)
    rule6592 = ReplacementRule(pattern6592, replacement6592)
    pattern6593 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons148)
    def replacement6593(b, d, c, a, n, x):
        rubi.append(6593)
        return Dist(S(1)/d, Subst(Int((a + b*atanh(x))**n, x), x, c + d*x), x)
    rule6593 = ReplacementRule(pattern6593, replacement6593)
    pattern6594 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons148)
    def replacement6594(b, d, c, a, n, x):
        rubi.append(6594)
        return Dist(S(1)/d, Subst(Int((a + b*acoth(x))**n, x), x, c + d*x), x)
    rule6594 = ReplacementRule(pattern6594, replacement6594)
    pattern6595 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(c_ + x_*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons340)
    def replacement6595(b, d, c, a, n, x):
        rubi.append(6595)
        return Int((a + b*atanh(c + d*x))**n, x)
    rule6595 = ReplacementRule(pattern6595, replacement6595)
    pattern6596 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(c_ + x_*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons340)
    def replacement6596(b, d, c, a, n, x):
        rubi.append(6596)
        return Int((a + b*acoth(c + d*x))**n, x)
    rule6596 = ReplacementRule(pattern6596, replacement6596)
    pattern6597 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons148)
    def replacement6597(m, f, b, d, a, n, c, x, e):
        rubi.append(6597)
        return Dist(S(1)/d, Subst(Int((a + b*atanh(x))**n*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule6597 = ReplacementRule(pattern6597, replacement6597)
    pattern6598 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(c_ + x_*WC('d', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons148)
    def replacement6598(m, f, b, d, a, n, c, x, e):
        rubi.append(6598)
        return Dist(S(1)/d, Subst(Int((a + b*acoth(x))**n*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule6598 = ReplacementRule(pattern6598, replacement6598)
    pattern6599 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**m_*(WC('a', S(0)) + WC('b', S(1))*atanh(c_ + x_*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons340)
    def replacement6599(m, f, b, d, a, c, n, x, e):
        rubi.append(6599)
        return Int((a + b*atanh(c + d*x))**n*(e + f*x)**m, x)
    rule6599 = ReplacementRule(pattern6599, replacement6599)
    pattern6600 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**m_*(WC('a', S(0)) + WC('b', S(1))*acoth(c_ + x_*WC('d', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons340)
    def replacement6600(m, f, b, d, a, c, n, x, e):
        rubi.append(6600)
        return Int((a + b*acoth(c + d*x))**n*(e + f*x)**m, x)
    rule6600 = ReplacementRule(pattern6600, replacement6600)
    pattern6601 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*atanh(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons34, cons35, cons36, cons4, cons5, cons1762, cons1763)
    def replacement6601(B, C, p, b, d, a, n, c, x, A):
        rubi.append(6601)
        return Dist(S(1)/d, Subst(Int((a + b*atanh(x))**n*(C*x**S(2)/d**S(2) - C/d**S(2))**p, x), x, c + d*x), x)
    rule6601 = ReplacementRule(pattern6601, replacement6601)
    pattern6602 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acoth(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons34, cons35, cons36, cons4, cons5, cons1762, cons1763)
    def replacement6602(B, C, p, b, d, a, n, c, x, A):
        rubi.append(6602)
        return Dist(S(1)/d, Subst(Int((a + b*acoth(x))**n*(C*x**S(2)/d**S(2) + C/d**S(2))**p, x), x, c + d*x), x)
    rule6602 = ReplacementRule(pattern6602, replacement6602)
    pattern6603 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons1762, cons1763)
    def replacement6603(B, C, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(6603)
        return Dist(S(1)/d, Subst(Int((a + b*atanh(x))**n*(C*x**S(2)/d**S(2) - C/d**S(2))**p*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule6603 = ReplacementRule(pattern6603, replacement6603)
    pattern6604 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(c_ + x_*WC('d', S(1))))**WC('n', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons1762, cons1763)
    def replacement6604(B, C, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(6604)
        return Dist(S(1)/d, Subst(Int((a + b*acoth(x))**n*(C*x**S(2)/d**S(2) - C/d**S(2))**p*(f*x/d + (-c*f + d*e)/d)**m, x), x, c + d*x), x)
    rule6604 = ReplacementRule(pattern6604, replacement6604)
    pattern6605 = Pattern(Integral(atanh(a_ + x_*WC('b', S(1)))/(c_ + x_**WC('n', S(1))*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons87)
    def replacement6605(b, d, a, n, c, x):
        rubi.append(6605)
        return -Dist(S(1)/2, Int(log(-a - b*x + S(1))/(c + d*x**n), x), x) + Dist(S(1)/2, Int(log(a + b*x + S(1))/(c + d*x**n), x), x)
    rule6605 = ReplacementRule(pattern6605, replacement6605)
    pattern6606 = Pattern(Integral(acoth(a_ + x_*WC('b', S(1)))/(c_ + x_**WC('n', S(1))*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons87)
    def replacement6606(b, d, a, n, c, x):
        rubi.append(6606)
        return -Dist(S(1)/2, Int(log((a + b*x + S(-1))/(a + b*x))/(c + d*x**n), x), x) + Dist(S(1)/2, Int(log((a + b*x + S(1))/(a + b*x))/(c + d*x**n), x), x)
    rule6606 = ReplacementRule(pattern6606, replacement6606)
    pattern6607 = Pattern(Integral(atanh(a_ + x_*WC('b', S(1)))/(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons4, cons1094)
    def replacement6607(b, d, c, a, n, x):
        rubi.append(6607)
        return Int(atanh(a + b*x)/(c + d*x**n), x)
    rule6607 = ReplacementRule(pattern6607, replacement6607)
    pattern6608 = Pattern(Integral(acoth(a_ + x_*WC('b', S(1)))/(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons4, cons1094)
    def replacement6608(b, d, c, a, n, x):
        rubi.append(6608)
        return Int(acoth(a + b*x)/(c + d*x**n), x)
    rule6608 = ReplacementRule(pattern6608, replacement6608)
    pattern6609 = Pattern(Integral(atanh(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons4, cons1831)
    def replacement6609(x, a, n, b):
        rubi.append(6609)
        return -Dist(b*n, Int(x**n/(-a**S(2) - S(2)*a*b*x**n - b**S(2)*x**(S(2)*n) + S(1)), x), x) + Simp(x*atanh(a + b*x**n), x)
    rule6609 = ReplacementRule(pattern6609, replacement6609)
    pattern6610 = Pattern(Integral(acoth(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons4, cons1831)
    def replacement6610(x, a, n, b):
        rubi.append(6610)
        return -Dist(b*n, Int(x**n/(-a**S(2) - S(2)*a*b*x**n - b**S(2)*x**(S(2)*n) + S(1)), x), x) + Simp(x*acoth(a + b*x**n), x)
    rule6610 = ReplacementRule(pattern6610, replacement6610)
    pattern6611 = Pattern(Integral(atanh(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))/x_, x_), cons2, cons3, cons4, cons1831)
    def replacement6611(x, a, n, b):
        rubi.append(6611)
        return -Dist(S(1)/2, Int(log(-a - b*x**n + S(1))/x, x), x) + Dist(S(1)/2, Int(log(a + b*x**n + S(1))/x, x), x)
    rule6611 = ReplacementRule(pattern6611, replacement6611)
    pattern6612 = Pattern(Integral(acoth(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))/x_, x_), cons2, cons3, cons4, cons1831)
    def replacement6612(x, a, n, b):
        rubi.append(6612)
        return -Dist(S(1)/2, Int(log(S(1) - S(1)/(a + b*x**n))/x, x), x) + Dist(S(1)/2, Int(log(S(1) + S(1)/(a + b*x**n))/x, x), x)
    rule6612 = ReplacementRule(pattern6612, replacement6612)
    pattern6613 = Pattern(Integral(x_**WC('m', S(1))*atanh(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons93, cons1832, cons1833)
    def replacement6613(m, b, a, n, x):
        rubi.append(6613)
        return -Dist(b*n/(m + S(1)), Int(x**(m + n)/(-a**S(2) - S(2)*a*b*x**n - b**S(2)*x**(S(2)*n) + S(1)), x), x) + Simp(x**(m + S(1))*atanh(a + b*x**n)/(m + S(1)), x)
    rule6613 = ReplacementRule(pattern6613, replacement6613)
    pattern6614 = Pattern(Integral(x_**WC('m', S(1))*acoth(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons93, cons1832, cons1833)
    def replacement6614(m, b, a, n, x):
        rubi.append(6614)
        return -Dist(b*n/(m + S(1)), Int(x**(m + n)/(-a**S(2) - S(2)*a*b*x**n - b**S(2)*x**(S(2)*n) + S(1)), x), x) + Simp(x**(m + S(1))*acoth(a + b*x**n)/(m + S(1)), x)
    rule6614 = ReplacementRule(pattern6614, replacement6614)
    pattern6615 = Pattern(Integral(atanh(f_**(x_*WC('d', S(1)) + WC('c', S(0)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons1834)
    def replacement6615(f, b, d, c, a, x):
        rubi.append(6615)
        return -Dist(S(1)/2, Int(log(-a - b*f**(c + d*x) + S(1)), x), x) + Dist(S(1)/2, Int(log(a + b*f**(c + d*x) + S(1)), x), x)
    rule6615 = ReplacementRule(pattern6615, replacement6615)
    pattern6616 = Pattern(Integral(acoth(f_**(x_*WC('d', S(1)) + WC('c', S(0)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons1834)
    def replacement6616(f, b, d, c, a, x):
        rubi.append(6616)
        return -Dist(S(1)/2, Int(log(S(1) - S(1)/(a + b*f**(c + d*x))), x), x) + Dist(S(1)/2, Int(log(S(1) + S(1)/(a + b*f**(c + d*x))), x), x)
    rule6616 = ReplacementRule(pattern6616, replacement6616)
    pattern6617 = Pattern(Integral(x_**WC('m', S(1))*atanh(f_**(x_*WC('d', S(1)) + WC('c', S(0)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons17, cons168)
    def replacement6617(m, f, b, d, c, a, x):
        rubi.append(6617)
        return -Dist(S(1)/2, Int(x**m*log(-a - b*f**(c + d*x) + S(1)), x), x) + Dist(S(1)/2, Int(x**m*log(a + b*f**(c + d*x) + S(1)), x), x)
    rule6617 = ReplacementRule(pattern6617, replacement6617)
    pattern6618 = Pattern(Integral(x_**WC('m', S(1))*acoth(f_**(x_*WC('d', S(1)) + WC('c', S(0)))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons17, cons168)
    def replacement6618(m, f, b, d, c, a, x):
        rubi.append(6618)
        return -Dist(S(1)/2, Int(x**m*log(S(1) - S(1)/(a + b*f**(c + d*x))), x), x) + Dist(S(1)/2, Int(x**m*log(S(1) + S(1)/(a + b*f**(c + d*x))), x), x)
    rule6618 = ReplacementRule(pattern6618, replacement6618)
    pattern6619 = Pattern(Integral(WC('u', S(1))*atanh(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement6619(u, m, b, c, n, a, x):
        rubi.append(6619)
        return Int(u*acoth(a/c + b*x**n/c)**m, x)
    rule6619 = ReplacementRule(pattern6619, replacement6619)
    pattern6620 = Pattern(Integral(WC('u', S(1))*acoth(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement6620(u, m, b, c, n, a, x):
        rubi.append(6620)
        return Int(u*atanh(a/c + b*x**n/c)**m, x)
    rule6620 = ReplacementRule(pattern6620, replacement6620)
    pattern6621 = Pattern(Integral(S(1)/(sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0)))*atanh(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))), x_), cons2, cons3, cons7, cons1939)
    def replacement6621(x, c, b, a):
        rubi.append(6621)
        return Simp(log(atanh(c*x/sqrt(a + b*x**S(2))))/c, x)
    rule6621 = ReplacementRule(pattern6621, replacement6621)
    pattern6622 = Pattern(Integral(S(1)/(sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0)))*acoth(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))), x_), cons2, cons3, cons7, cons1939)
    def replacement6622(x, c, b, a):
        rubi.append(6622)
        return -Simp(log(acoth(c*x/sqrt(a + b*x**S(2))))/c, x)
    rule6622 = ReplacementRule(pattern6622, replacement6622)
    pattern6623 = Pattern(Integral(atanh(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons21, cons1939, cons66)
    def replacement6623(m, b, c, a, x):
        rubi.append(6623)
        return Simp(atanh(c*x/sqrt(a + b*x**S(2)))**(m + S(1))/(c*(m + S(1))), x)
    rule6623 = ReplacementRule(pattern6623, replacement6623)
    pattern6624 = Pattern(Integral(acoth(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons21, cons1939, cons66)
    def replacement6624(m, b, c, a, x):
        rubi.append(6624)
        return -Simp(acoth(c*x/sqrt(a + b*x**S(2)))**(m + S(1))/(c*(m + S(1))), x)
    rule6624 = ReplacementRule(pattern6624, replacement6624)
    pattern6625 = Pattern(Integral(atanh(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1))/sqrt(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1939, cons383)
    def replacement6625(m, b, d, c, a, x, e):
        rubi.append(6625)
        return Dist(sqrt(a + b*x**S(2))/sqrt(d + e*x**S(2)), Int(atanh(c*x/sqrt(a + b*x**S(2)))**m/sqrt(a + b*x**S(2)), x), x)
    rule6625 = ReplacementRule(pattern6625, replacement6625)
    pattern6626 = Pattern(Integral(acoth(x_*WC('c', S(1))/sqrt(x_**S(2)*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1))/sqrt(x_**S(2)*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1939, cons383)
    def replacement6626(m, b, d, c, a, x, e):
        rubi.append(6626)
        return Dist(sqrt(a + b*x**S(2))/sqrt(d + e*x**S(2)), Int(acoth(c*x/sqrt(a + b*x**S(2)))**m/sqrt(a + b*x**S(2)), x), x)
    rule6626 = ReplacementRule(pattern6626, replacement6626)
    def With6627(d, a, n, c, x):
        u = IntHide((c + d*x**S(2))**n, x)
        rubi.append(6627)
        return -Dist(a, Int(Dist(S(1)/(-a**S(2)*x**S(2) + S(1)), u, x), x), x) + Dist(atanh(a*x), u, x)
    pattern6627 = Pattern(Integral((x_**S(2)*WC('d', S(1)) + WC('c', S(0)))**n_*atanh(x_*WC('a', S(1))), x_), cons2, cons7, cons27, cons808, cons1586)
    rule6627 = ReplacementRule(pattern6627, With6627)
    def With6628(d, a, n, c, x):
        u = IntHide((c + d*x**S(2))**n, x)
        rubi.append(6628)
        return -Dist(a, Int(Dist(S(1)/(-a**S(2)*x**S(2) + S(1)), u, x), x), x) + Dist(acoth(a*x), u, x)
    pattern6628 = Pattern(Integral((x_**S(2)*WC('d', S(1)) + WC('c', S(0)))**n_*acoth(x_*WC('a', S(1))), x_), cons2, cons7, cons27, cons808, cons1586)
    rule6628 = ReplacementRule(pattern6628, With6628)
    def With6629(v, x, n, u):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        try:
            tmp = InverseFunctionOfLinear(u, x)
            res = And(Not(FalseQ(tmp)), SameQ(Head(tmp), ArcTanh), ZeroQ(-D(v, x)**S(2) + Discriminant(v, x)*Part(tmp, S(1))**S(2)))
        except (TypeError, AttributeError):
            return False
        if res:
            return True
        return False
    pattern6629 = Pattern(Integral(u_*v_**WC('n', S(1)), x_), cons818, cons85, cons463, cons1940, cons1941, CustomConstraint(With6629))
    def replacement6629(v, x, n, u):

        tmp = InverseFunctionOfLinear(u, x)
        rubi.append(6629)
        return Dist((-Discriminant(v, x)/(S(4)*Coefficient(v, x, S(2))))**n/Coefficient(Part(tmp, S(1)), x, S(1)), Subst(Int(SimplifyIntegrand((S(1)/cosh(x))**(S(2)*n + S(2))*SubstForInverseFunction(u, tmp, x), x), x), x, tmp), x)
    rule6629 = ReplacementRule(pattern6629, replacement6629)
    def With6630(v, x, n, u):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        try:
            tmp = InverseFunctionOfLinear(u, x)
            res = And(Not(FalseQ(tmp)), SameQ(Head(tmp), ArcCoth), ZeroQ(-D(v, x)**S(2) + Discriminant(v, x)*Part(tmp, S(1))**S(2)))
        except (TypeError, AttributeError):
            return False
        if res:
            return True
        return False
    pattern6630 = Pattern(Integral(u_*v_**WC('n', S(1)), x_), cons818, cons85, cons463, cons1940, cons1942, CustomConstraint(With6630))
    def replacement6630(v, x, n, u):

        tmp = InverseFunctionOfLinear(u, x)
        rubi.append(6630)
        return Dist((-Discriminant(v, x)/(S(4)*Coefficient(v, x, S(2))))**n/Coefficient(Part(tmp, S(1)), x, S(1)), Subst(Int(SimplifyIntegrand((-S(1)/sinh(x)**S(2))**(n + S(1))*SubstForInverseFunction(u, tmp, x), x), x), x, tmp), x)
    rule6630 = ReplacementRule(pattern6630, replacement6630)
    pattern6631 = Pattern(Integral(atanh(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1943)
    def replacement6631(b, d, c, a, x):
        rubi.append(6631)
        return Dist(b, Int(x/(c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp(x*atanh(c + d*tanh(a + b*x)), x)
    rule6631 = ReplacementRule(pattern6631, replacement6631)
    pattern6632 = Pattern(Integral(acoth(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1943)
    def replacement6632(b, d, c, a, x):
        rubi.append(6632)
        return Dist(b, Int(x/(c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp(x*acoth(c + d*tanh(a + b*x)), x)
    rule6632 = ReplacementRule(pattern6632, replacement6632)
    pattern6633 = Pattern(Integral(atanh(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1943)
    def replacement6633(b, d, c, a, x):
        rubi.append(6633)
        return Dist(b, Int(x/(-c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp(x*atanh(c + d/tanh(a + b*x)), x)
    rule6633 = ReplacementRule(pattern6633, replacement6633)
    pattern6634 = Pattern(Integral(acoth(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1943)
    def replacement6634(b, d, c, a, x):
        rubi.append(6634)
        return Dist(b, Int(x/(-c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp(x*acoth(c + d/tanh(a + b*x)), x)
    rule6634 = ReplacementRule(pattern6634, replacement6634)
    pattern6635 = Pattern(Integral(atanh(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1944)
    def replacement6635(b, d, c, a, x):
        rubi.append(6635)
        return Dist(b*(-c - d + S(1)), Int(x*exp(S(2)*a + S(2)*b*x)/(-c + d + (-c - d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) - Dist(b*(c + d + S(1)), Int(x*exp(S(2)*a + S(2)*b*x)/(c - d + (c + d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Simp(x*atanh(c + d*tanh(a + b*x)), x)
    rule6635 = ReplacementRule(pattern6635, replacement6635)
    pattern6636 = Pattern(Integral(acoth(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1944)
    def replacement6636(b, d, c, a, x):
        rubi.append(6636)
        return Dist(b*(-c - d + S(1)), Int(x*exp(S(2)*a + S(2)*b*x)/(-c + d + (-c - d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) - Dist(b*(c + d + S(1)), Int(x*exp(S(2)*a + S(2)*b*x)/(c - d + (c + d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Simp(x*acoth(c + d*tanh(a + b*x)), x)
    rule6636 = ReplacementRule(pattern6636, replacement6636)
    pattern6637 = Pattern(Integral(atanh(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1944)
    def replacement6637(b, d, c, a, x):
        rubi.append(6637)
        return -Dist(b*(-c - d + S(1)), Int(x*exp(S(2)*a + S(2)*b*x)/(-c + d - (-c - d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Dist(b*(c + d + S(1)), Int(x*exp(S(2)*a + S(2)*b*x)/(c - d - (c + d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Simp(x*atanh(c + d/tanh(a + b*x)), x)
    rule6637 = ReplacementRule(pattern6637, replacement6637)
    pattern6638 = Pattern(Integral(acoth(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1944)
    def replacement6638(b, d, c, a, x):
        rubi.append(6638)
        return -Dist(b*(-c - d + S(1)), Int(x*exp(S(2)*a + S(2)*b*x)/(-c + d - (-c - d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Dist(b*(c + d + S(1)), Int(x*exp(S(2)*a + S(2)*b*x)/(c - d - (c + d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Simp(x*acoth(c + d/tanh(a + b*x)), x)
    rule6638 = ReplacementRule(pattern6638, replacement6638)
    pattern6639 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1943)
    def replacement6639(m, f, b, d, c, a, x, e):
        rubi.append(6639)
        return Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp((e + f*x)**(m + S(1))*atanh(c + d*tanh(a + b*x))/(f*(m + S(1))), x)
    rule6639 = ReplacementRule(pattern6639, replacement6639)
    pattern6640 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1943)
    def replacement6640(m, f, b, d, c, a, x, e):
        rubi.append(6640)
        return Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp((e + f*x)**(m + S(1))*acoth(c + d*tanh(a + b*x))/(f*(m + S(1))), x)
    rule6640 = ReplacementRule(pattern6640, replacement6640)
    pattern6641 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1943)
    def replacement6641(m, f, b, d, c, a, x, e):
        rubi.append(6641)
        return Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(-c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp((e + f*x)**(m + S(1))*atanh(c + d/tanh(a + b*x))/(f*(m + S(1))), x)
    rule6641 = ReplacementRule(pattern6641, replacement6641)
    pattern6642 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1943)
    def replacement6642(m, f, b, d, c, a, x, e):
        rubi.append(6642)
        return Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(-c*exp(S(2)*a + S(2)*b*x) + c - d), x), x) + Simp((e + f*x)**(m + S(1))*acoth(c + d/tanh(a + b*x))/(f*(m + S(1))), x)
    rule6642 = ReplacementRule(pattern6642, replacement6642)
    pattern6643 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1944)
    def replacement6643(m, f, b, d, c, a, x, e):
        rubi.append(6643)
        return Dist(b*(-c - d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(-c + d + (-c - d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) - Dist(b*(c + d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(c - d + (c + d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*atanh(c + d*tanh(a + b*x))/(f*(m + S(1))), x)
    rule6643 = ReplacementRule(pattern6643, replacement6643)
    pattern6644 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(WC('c', S(0)) + WC('d', S(1))*tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1944)
    def replacement6644(m, f, b, d, c, a, x, e):
        rubi.append(6644)
        return Dist(b*(-c - d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(-c + d + (-c - d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) - Dist(b*(c + d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(c - d + (c + d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*acoth(c + d*tanh(a + b*x))/(f*(m + S(1))), x)
    rule6644 = ReplacementRule(pattern6644, replacement6644)
    pattern6645 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1944)
    def replacement6645(m, f, b, d, c, a, x, e):
        rubi.append(6645)
        return -Dist(b*(-c - d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(-c + d - (-c - d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Dist(b*(c + d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(c - d - (c + d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*atanh(c + d/tanh(a + b*x))/(f*(m + S(1))), x)
    rule6645 = ReplacementRule(pattern6645, replacement6645)
    pattern6646 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(WC('c', S(0)) + WC('d', S(1))/tanh(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1944)
    def replacement6646(m, f, b, d, c, a, x, e):
        rubi.append(6646)
        return -Dist(b*(-c - d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(-c + d - (-c - d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Dist(b*(c + d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*a + S(2)*b*x)/(c - d - (c + d + S(1))*exp(S(2)*a + S(2)*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*acoth(c + d/tanh(a + b*x))/(f*(m + S(1))), x)
    rule6646 = ReplacementRule(pattern6646, replacement6646)
    pattern6647 = Pattern(Integral(atanh(tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons67)
    def replacement6647(x, a, b):
        rubi.append(6647)
        return -Dist(b, Int(x/cos(S(2)*a + S(2)*b*x), x), x) + Simp(x*atanh(tan(a + b*x)), x)
    rule6647 = ReplacementRule(pattern6647, replacement6647)
    pattern6648 = Pattern(Integral(acoth(tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons67)
    def replacement6648(x, a, b):
        rubi.append(6648)
        return -Dist(b, Int(x/cos(S(2)*a + S(2)*b*x), x), x) + Simp(x*acoth(tan(a + b*x)), x)
    rule6648 = ReplacementRule(pattern6648, replacement6648)
    pattern6649 = Pattern(Integral(atanh(S(1)/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons67)
    def replacement6649(x, a, b):
        rubi.append(6649)
        return -Dist(b, Int(x/cos(S(2)*a + S(2)*b*x), x), x) + Simp(x*atanh(S(1)/tan(a + b*x)), x)
    rule6649 = ReplacementRule(pattern6649, replacement6649)
    pattern6650 = Pattern(Integral(acoth(S(1)/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons67)
    def replacement6650(x, a, b):
        rubi.append(6650)
        return -Dist(b, Int(x/cos(S(2)*a + S(2)*b*x), x), x) + Simp(x*acoth(S(1)/tan(a + b*x)), x)
    rule6650 = ReplacementRule(pattern6650, replacement6650)
    pattern6651 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons48, cons125, cons62)
    def replacement6651(m, f, b, a, x, e):
        rubi.append(6651)
        return -Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/cos(S(2)*a + S(2)*b*x), x), x) + Simp((e + f*x)**(m + S(1))*atanh(tan(a + b*x))/(f*(m + S(1))), x)
    rule6651 = ReplacementRule(pattern6651, replacement6651)
    pattern6652 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons48, cons125, cons62)
    def replacement6652(m, f, b, a, x, e):
        rubi.append(6652)
        return -Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/cos(S(2)*a + S(2)*b*x), x), x) + Simp((e + f*x)**(m + S(1))*acoth(tan(a + b*x))/(f*(m + S(1))), x)
    rule6652 = ReplacementRule(pattern6652, replacement6652)
    pattern6653 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(S(1)/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons48, cons125, cons62)
    def replacement6653(m, f, b, a, x, e):
        rubi.append(6653)
        return -Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/cos(S(2)*a + S(2)*b*x), x), x) + Simp((e + f*x)**(m + S(1))*atanh(S(1)/tan(a + b*x))/(f*(m + S(1))), x)
    rule6653 = ReplacementRule(pattern6653, replacement6653)
    pattern6654 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(S(1)/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons48, cons125, cons62)
    def replacement6654(m, f, b, a, x, e):
        rubi.append(6654)
        return -Dist(b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/cos(S(2)*a + S(2)*b*x), x), x) + Simp((e + f*x)**(m + S(1))*acoth(S(1)/tan(a + b*x))/(f*(m + S(1))), x)
    rule6654 = ReplacementRule(pattern6654, replacement6654)
    pattern6655 = Pattern(Integral(atanh(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1945)
    def replacement6655(b, d, c, a, x):
        rubi.append(6655)
        return Dist(I*b, Int(x/(c*exp(S(2)*I*a + S(2)*I*b*x) + c + I*d), x), x) + Simp(x*atanh(c + d*tan(a + b*x)), x)
    rule6655 = ReplacementRule(pattern6655, replacement6655)
    pattern6656 = Pattern(Integral(acoth(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1945)
    def replacement6656(b, d, c, a, x):
        rubi.append(6656)
        return Dist(I*b, Int(x/(c*exp(S(2)*I*a + S(2)*I*b*x) + c + I*d), x), x) + Simp(x*acoth(c + d*tan(a + b*x)), x)
    rule6656 = ReplacementRule(pattern6656, replacement6656)
    pattern6657 = Pattern(Integral(atanh(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1946)
    def replacement6657(b, d, c, a, x):
        rubi.append(6657)
        return Dist(I*b, Int(x/(-c*exp(S(2)*I*a + S(2)*I*b*x) + c - I*d), x), x) + Simp(x*atanh(c + d/tan(a + b*x)), x)
    rule6657 = ReplacementRule(pattern6657, replacement6657)
    pattern6658 = Pattern(Integral(acoth(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1946)
    def replacement6658(b, d, c, a, x):
        rubi.append(6658)
        return Dist(I*b, Int(x/(-c*exp(S(2)*I*a + S(2)*I*b*x) + c - I*d), x), x) + Simp(x*acoth(c + d/tan(a + b*x)), x)
    rule6658 = ReplacementRule(pattern6658, replacement6658)
    pattern6659 = Pattern(Integral(atanh(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1947)
    def replacement6659(b, d, c, a, x):
        rubi.append(6659)
        return Dist(I*b*(-c + I*d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(-c - I*d + (-c + I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) - Dist(I*b*(c - I*d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(c + I*d + (c - I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp(x*atanh(c + d*tan(a + b*x)), x)
    rule6659 = ReplacementRule(pattern6659, replacement6659)
    pattern6660 = Pattern(Integral(acoth(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1947)
    def replacement6660(b, d, c, a, x):
        rubi.append(6660)
        return Dist(I*b*(-c + I*d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(-c - I*d + (-c + I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) - Dist(I*b*(c - I*d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(c + I*d + (c - I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp(x*acoth(c + d*tan(a + b*x)), x)
    rule6660 = ReplacementRule(pattern6660, replacement6660)
    pattern6661 = Pattern(Integral(atanh(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1948)
    def replacement6661(b, d, c, a, x):
        rubi.append(6661)
        return -Dist(I*b*(-c - I*d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(-c + I*d - (-c - I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Dist(I*b*(c + I*d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(c - I*d - (c + I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp(x*atanh(c + d/tan(a + b*x)), x)
    rule6661 = ReplacementRule(pattern6661, replacement6661)
    pattern6662 = Pattern(Integral(acoth(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons1948)
    def replacement6662(b, d, c, a, x):
        rubi.append(6662)
        return -Dist(I*b*(-c - I*d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(-c + I*d - (-c - I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Dist(I*b*(c + I*d + S(1)), Int(x*exp(S(2)*I*a + S(2)*I*b*x)/(c - I*d - (c + I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp(x*acoth(c + d/tan(a + b*x)), x)
    rule6662 = ReplacementRule(pattern6662, replacement6662)
    pattern6663 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1945)
    def replacement6663(m, f, b, d, c, a, x, e):
        rubi.append(6663)
        return Dist(I*b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(c*exp(S(2)*I*a + S(2)*I*b*x) + c + I*d), x), x) + Simp((e + f*x)**(m + S(1))*atanh(c + d*tan(a + b*x))/(f*(m + S(1))), x)
    rule6663 = ReplacementRule(pattern6663, replacement6663)
    pattern6664 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1945)
    def replacement6664(m, f, b, d, c, a, x, e):
        rubi.append(6664)
        return Dist(I*b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(c*exp(S(2)*I*a + S(2)*I*b*x) + c + I*d), x), x) + Simp((e + f*x)**(m + S(1))*acoth(c + d*tan(a + b*x))/(f*(m + S(1))), x)
    rule6664 = ReplacementRule(pattern6664, replacement6664)
    pattern6665 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1946)
    def replacement6665(m, f, b, d, c, a, x, e):
        rubi.append(6665)
        return Dist(I*b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(-c*exp(S(2)*I*a + S(2)*I*b*x) + c - I*d), x), x) + Simp((e + f*x)**(m + S(1))*atanh(c + d/tan(a + b*x))/(f*(m + S(1))), x)
    rule6665 = ReplacementRule(pattern6665, replacement6665)
    pattern6666 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1946)
    def replacement6666(m, f, b, d, c, a, x, e):
        rubi.append(6666)
        return Dist(I*b/(f*(m + S(1))), Int((e + f*x)**(m + S(1))/(-c*exp(S(2)*I*a + S(2)*I*b*x) + c - I*d), x), x) + Simp((e + f*x)**(m + S(1))*acoth(c + d/tan(a + b*x))/(f*(m + S(1))), x)
    rule6666 = ReplacementRule(pattern6666, replacement6666)
    pattern6667 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1947)
    def replacement6667(m, f, b, d, c, a, x, e):
        rubi.append(6667)
        return Dist(I*b*(-c + I*d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(-c - I*d + (-c + I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) - Dist(I*b*(c - I*d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(c + I*d + (c - I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*atanh(c + d*tan(a + b*x))/(f*(m + S(1))), x)
    rule6667 = ReplacementRule(pattern6667, replacement6667)
    pattern6668 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(WC('c', S(0)) + WC('d', S(1))*tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1947)
    def replacement6668(m, f, b, d, c, a, x, e):
        rubi.append(6668)
        return Dist(I*b*(-c + I*d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(-c - I*d + (-c + I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) - Dist(I*b*(c - I*d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(c + I*d + (c - I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*acoth(c + d*tan(a + b*x))/(f*(m + S(1))), x)
    rule6668 = ReplacementRule(pattern6668, replacement6668)
    pattern6669 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*atanh(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1948)
    def replacement6669(m, f, b, d, c, a, x, e):
        rubi.append(6669)
        return -Dist(I*b*(-c - I*d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(-c + I*d - (-c - I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Dist(I*b*(c + I*d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(c - I*d - (c + I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*atanh(c + d/tan(a + b*x))/(f*(m + S(1))), x)
    rule6669 = ReplacementRule(pattern6669, replacement6669)
    pattern6670 = Pattern(Integral((x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1))*acoth(WC('c', S(0)) + WC('d', S(1))/tan(x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons62, cons1948)
    def replacement6670(m, f, b, d, c, a, x, e):
        rubi.append(6670)
        return -Dist(I*b*(-c - I*d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(-c + I*d - (-c - I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Dist(I*b*(c + I*d + S(1))/(f*(m + S(1))), Int((e + f*x)**(m + S(1))*exp(S(2)*I*a + S(2)*I*b*x)/(c - I*d - (c + I*d + S(1))*exp(S(2)*I*a + S(2)*I*b*x) + S(1)), x), x) + Simp((e + f*x)**(m + S(1))*acoth(c + d/tan(a + b*x))/(f*(m + S(1))), x)
    rule6670 = ReplacementRule(pattern6670, replacement6670)
    pattern6671 = Pattern(Integral(atanh(u_), x_), cons1230)
    def replacement6671(x, u):
        rubi.append(6671)
        return -Int(SimplifyIntegrand(x*D(u, x)/(-u**S(2) + S(1)), x), x) + Simp(x*atanh(u), x)
    rule6671 = ReplacementRule(pattern6671, replacement6671)
    pattern6672 = Pattern(Integral(acoth(u_), x_), cons1230)
    def replacement6672(x, u):
        rubi.append(6672)
        return -Int(SimplifyIntegrand(x*D(u, x)/(-u**S(2) + S(1)), x), x) + Simp(x*acoth(u), x)
    rule6672 = ReplacementRule(pattern6672, replacement6672)
    pattern6673 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*atanh(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1847)
    def replacement6673(u, m, b, d, c, a, x):
        rubi.append(6673)
        return -Dist(b/(d*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/(-u**S(2) + S(1)), x), x), x) + Simp((a + b*atanh(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule6673 = ReplacementRule(pattern6673, replacement6673)
    pattern6674 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acoth(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1847)
    def replacement6674(u, m, b, d, c, a, x):
        rubi.append(6674)
        return -Dist(b/(d*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/(-u**S(2) + S(1)), x), x), x) + Simp((a + b*acoth(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule6674 = ReplacementRule(pattern6674, replacement6674)
    def With6675(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern6675 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*atanh(u_)), x_), cons2, cons3, cons1230, cons1949, cons1950, CustomConstraint(With6675))
    def replacement6675(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(6675)
        return -Dist(b, Int(SimplifyIntegrand(w*D(u, x)/(-u**S(2) + S(1)), x), x), x) + Dist(a + b*atanh(u), w, x)
    rule6675 = ReplacementRule(pattern6675, replacement6675)
    def With6676(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern6676 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*acoth(u_)), x_), cons2, cons3, cons1230, cons1951, cons1952, CustomConstraint(With6676))
    def replacement6676(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(6676)
        return -Dist(b, Int(SimplifyIntegrand(w*D(u, x)/(-u**S(2) + S(1)), x), x), x) + Dist(a + b*acoth(u), w, x)
    rule6676 = ReplacementRule(pattern6676, replacement6676)
    pattern6677 = Pattern(Integral(asech(x_*WC('c', S(1))), x_), cons7, cons7)
    def replacement6677(x, c):
        rubi.append(6677)
        return Dist(sqrt(c*x + S(1))*sqrt(S(1)/(c*x + S(1))), Int(S(1)/(sqrt(-c*x + S(1))*sqrt(c*x + S(1))), x), x) + Simp(x*asech(c*x), x)
    rule6677 = ReplacementRule(pattern6677, replacement6677)
    pattern6678 = Pattern(Integral(acsch(x_*WC('c', S(1))), x_), cons7, cons7)
    def replacement6678(x, c):
        rubi.append(6678)
        return Dist(S(1)/c, Int(S(1)/(x*sqrt(S(1) + S(1)/(c**S(2)*x**S(2)))), x), x) + Simp(x*acsch(c*x), x)
    rule6678 = ReplacementRule(pattern6678, replacement6678)
    pattern6679 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement6679(b, a, n, c, x):
        rubi.append(6679)
        return -Dist(S(1)/c, Subst(Int((a + b*x)**n*tanh(x)/cosh(x), x), x, asech(c*x)), x)
    rule6679 = ReplacementRule(pattern6679, replacement6679)
    pattern6680 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons1579)
    def replacement6680(b, a, n, c, x):
        rubi.append(6680)
        return -Dist(S(1)/c, Subst(Int((a + b*x)**n/(sinh(x)*tanh(x)), x), x, acsch(c*x)), x)
    rule6680 = ReplacementRule(pattern6680, replacement6680)
    pattern6681 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))/x_, x_), cons2, cons3, cons7, cons14)
    def replacement6681(x, a, c, b):
        rubi.append(6681)
        return -Subst(Int((a + b*acosh(x/c))/x, x), x, S(1)/x)
    rule6681 = ReplacementRule(pattern6681, replacement6681)
    pattern6682 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))/x_, x_), cons2, cons3, cons7, cons14)
    def replacement6682(x, a, c, b):
        rubi.append(6682)
        return -Subst(Int((a + b*asinh(x/c))/x, x), x, S(1)/x)
    rule6682 = ReplacementRule(pattern6682, replacement6682)
    pattern6683 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons21, cons66)
    def replacement6683(m, b, a, c, x):
        rubi.append(6683)
        return Dist(b*sqrt(c*x + S(1))*sqrt(S(1)/(c*x + S(1)))/(m + S(1)), Int(x**m/(sqrt(-c*x + S(1))*sqrt(c*x + S(1))), x), x) + Simp(x**(m + S(1))*(a + b*asech(c*x))/(m + S(1)), x)
    rule6683 = ReplacementRule(pattern6683, replacement6683)
    pattern6684 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons21, cons66)
    def replacement6684(m, b, a, c, x):
        rubi.append(6684)
        return Dist(b/(c*(m + S(1))), Int(x**(m + S(-1))/sqrt(S(1) + S(1)/(c**S(2)*x**S(2))), x), x) + Simp(x**(m + S(1))*(a + b*acsch(c*x))/(m + S(1)), x)
    rule6684 = ReplacementRule(pattern6684, replacement6684)
    pattern6685 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons17)
    def replacement6685(m, b, a, c, n, x):
        rubi.append(6685)
        return -Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*(S(1)/cosh(x))**(m + S(1))*tanh(x), x), x, asech(c*x)), x)
    rule6685 = ReplacementRule(pattern6685, replacement6685)
    pattern6686 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons4, cons17)
    def replacement6686(m, b, a, c, n, x):
        rubi.append(6686)
        return -Dist(c**(-m + S(-1)), Subst(Int((a + b*x)**n*(S(1)/sinh(x))**(m + S(1))/tanh(x), x), x, acsch(c*x)), x)
    rule6686 = ReplacementRule(pattern6686, replacement6686)
    pattern6687 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons21, cons4, cons1854)
    def replacement6687(m, b, a, n, c, x):
        rubi.append(6687)
        return Int(x**m*(a + b*asech(c*x))**n, x)
    rule6687 = ReplacementRule(pattern6687, replacement6687)
    pattern6688 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons21, cons4, cons1854)
    def replacement6688(m, b, a, n, c, x):
        rubi.append(6688)
        return Int(x**m*(a + b*acsch(c*x))**n, x)
    rule6688 = ReplacementRule(pattern6688, replacement6688)
    def With6689(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(6689)
        return Dist(b*sqrt(c*x + S(1))*sqrt(S(1)/(c*x + S(1))), Int(SimplifyIntegrand(u/(x*sqrt(-c*x + S(1))*sqrt(c*x + S(1))), x), x), x) + Dist(a + b*asech(c*x), u, x)
    pattern6689 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1743)
    rule6689 = ReplacementRule(pattern6689, With6689)
    def With6690(p, b, d, a, c, x, e):
        u = IntHide((d + e*x**S(2))**p, x)
        rubi.append(6690)
        return -Dist(b*c*x/sqrt(-c**S(2)*x**S(2)), Int(SimplifyIntegrand(u/(x*sqrt(-c**S(2)*x**S(2) + S(-1))), x), x), x) + Dist(a + b*acsch(c*x), u, x)
    pattern6690 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons1743)
    rule6690 = ReplacementRule(pattern6690, With6690)
    pattern6691 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons38)
    def replacement6691(p, b, d, a, n, c, x, e):
        rubi.append(6691)
        return -Subst(Int(x**(-S(2)*p + S(-2))*(a + b*acosh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x)
    rule6691 = ReplacementRule(pattern6691, replacement6691)
    pattern6692 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons38)
    def replacement6692(p, b, d, a, n, c, x, e):
        rubi.append(6692)
        return -Subst(Int(x**(-S(2)*p + S(-2))*(a + b*asinh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x)
    rule6692 = ReplacementRule(pattern6692, replacement6692)
    pattern6693 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons667, cons178, cons1855)
    def replacement6693(p, b, d, a, n, c, x, e):
        rubi.append(6693)
        return -Dist(sqrt(x**S(2))/x, Subst(Int(x**(-S(2)*p + S(-2))*(a + b*acosh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule6693 = ReplacementRule(pattern6693, replacement6693)
    pattern6694 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons667, cons178, cons1855)
    def replacement6694(p, b, d, a, n, c, x, e):
        rubi.append(6694)
        return -Dist(sqrt(x**S(2))/x, Subst(Int(x**(-S(2)*p + S(-2))*(a + b*asinh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule6694 = ReplacementRule(pattern6694, replacement6694)
    pattern6695 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons667, cons1856)
    def replacement6695(p, b, d, a, n, c, x, e):
        rubi.append(6695)
        return -Dist(sqrt(d + e*x**S(2))/(x*sqrt(d/x**S(2) + e)), Subst(Int(x**(-S(2)*p + S(-2))*(a + b*acosh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule6695 = ReplacementRule(pattern6695, replacement6695)
    pattern6696 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons667, cons1856)
    def replacement6696(p, b, d, a, n, c, x, e):
        rubi.append(6696)
        return -Dist(sqrt(d + e*x**S(2))/(x*sqrt(d/x**S(2) + e)), Subst(Int(x**(-S(2)*p + S(-2))*(a + b*asinh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule6696 = ReplacementRule(pattern6696, replacement6696)
    pattern6697 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement6697(p, b, d, a, n, c, x, e):
        rubi.append(6697)
        return Int((a + b*asech(c*x))**n*(d + e*x**S(2))**p, x)
    rule6697 = ReplacementRule(pattern6697, replacement6697)
    pattern6698 = Pattern(Integral((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1570)
    def replacement6698(p, b, d, a, n, c, x, e):
        rubi.append(6698)
        return Int((a + b*acsch(c*x))**n*(d + e*x**S(2))**p, x)
    rule6698 = ReplacementRule(pattern6698, replacement6698)
    pattern6699 = Pattern(Integral(x_*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement6699(p, b, d, a, c, x, e):
        rubi.append(6699)
        return Dist(b*sqrt(c*x + S(1))*sqrt(S(1)/(c*x + S(1)))/(S(2)*e*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/(x*sqrt(-c*x + S(1))*sqrt(c*x + S(1))), x), x) + Simp((a + b*asech(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6699 = ReplacementRule(pattern6699, replacement6699)
    pattern6700 = Pattern(Integral(x_*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons54)
    def replacement6700(p, b, d, a, c, x, e):
        rubi.append(6700)
        return -Dist(b*c*x/(S(2)*e*sqrt(-c**S(2)*x**S(2))*(p + S(1))), Int((d + e*x**S(2))**(p + S(1))/(x*sqrt(-c**S(2)*x**S(2) + S(-1))), x), x) + Simp((a + b*acsch(c*x))*(d + e*x**S(2))**(p + S(1))/(S(2)*e*(p + S(1))), x)
    rule6700 = ReplacementRule(pattern6700, replacement6700)
    def With6701(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(d + e*x**S(2))**p, x)
        rubi.append(6701)
        return Dist(b*sqrt(c*x + S(1))*sqrt(S(1)/(c*x + S(1))), Int(SimplifyIntegrand(u/(x*sqrt(-c*x + S(1))*sqrt(c*x + S(1))), x), x), x) + Dist(a + b*asech(c*x), u, x)
    pattern6701 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1786)
    rule6701 = ReplacementRule(pattern6701, With6701)
    def With6702(p, m, b, d, a, c, x, e):
        u = IntHide(x**m*(d + e*x**S(2))**p, x)
        rubi.append(6702)
        return -Dist(b*c*x/sqrt(-c**S(2)*x**S(2)), Int(SimplifyIntegrand(u/(x*sqrt(-c**S(2)*x**S(2) + S(-1))), x), x), x) + Dist(a + b*acsch(c*x), u, x)
    pattern6702 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1786)
    rule6702 = ReplacementRule(pattern6702, With6702)
    pattern6703 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1299)
    def replacement6703(p, m, b, d, a, n, c, x, e):
        rubi.append(6703)
        return -Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*acosh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x)
    rule6703 = ReplacementRule(pattern6703, replacement6703)
    pattern6704 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1299)
    def replacement6704(p, m, b, d, a, n, c, x, e):
        rubi.append(6704)
        return -Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*asinh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x)
    rule6704 = ReplacementRule(pattern6704, replacement6704)
    pattern6705 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons17, cons667, cons178, cons1855)
    def replacement6705(p, m, b, d, a, n, c, x, e):
        rubi.append(6705)
        return -Dist(sqrt(x**S(2))/x, Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*acosh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule6705 = ReplacementRule(pattern6705, replacement6705)
    pattern6706 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons17, cons667, cons178, cons1855)
    def replacement6706(p, m, b, d, a, n, c, x, e):
        rubi.append(6706)
        return -Dist(sqrt(x**S(2))/x, Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*asinh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule6706 = ReplacementRule(pattern6706, replacement6706)
    pattern6707 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1737, cons17, cons667, cons1856)
    def replacement6707(p, m, b, d, a, n, c, x, e):
        rubi.append(6707)
        return -Dist(sqrt(d + e*x**S(2))/(x*sqrt(d/x**S(2) + e)), Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*acosh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule6707 = ReplacementRule(pattern6707, replacement6707)
    pattern6708 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**p_*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1778, cons17, cons667, cons1856)
    def replacement6708(p, m, b, d, a, n, c, x, e):
        rubi.append(6708)
        return -Dist(sqrt(d + e*x**S(2))/(x*sqrt(d/x**S(2) + e)), Subst(Int(x**(-m - S(2)*p + S(-2))*(a + b*asinh(x/c))**n*(d*x**S(2) + e)**p, x), x, S(1)/x), x)
    rule6708 = ReplacementRule(pattern6708, replacement6708)
    pattern6709 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement6709(p, m, b, d, a, n, c, x, e):
        rubi.append(6709)
        return Int(x**m*(a + b*asech(c*x))**n*(d + e*x**S(2))**p, x)
    rule6709 = ReplacementRule(pattern6709, replacement6709)
    pattern6710 = Pattern(Integral(x_**WC('m', S(1))*(x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(x_*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement6710(p, m, b, d, a, n, c, x, e):
        rubi.append(6710)
        return Int(x**m*(a + b*acsch(c*x))**n*(d + e*x**S(2))**p, x)
    rule6710 = ReplacementRule(pattern6710, replacement6710)
    pattern6711 = Pattern(Integral(asech(a_ + x_*WC('b', S(1))), x_), cons2, cons3, cons67)
    def replacement6711(x, a, b):
        rubi.append(6711)
        return Int(sqrt((-a - b*x + S(1))/(a + b*x + S(1)))/(-a - b*x + S(1)), x) + Simp((a + b*x)*asech(a + b*x)/b, x)
    rule6711 = ReplacementRule(pattern6711, replacement6711)
    pattern6712 = Pattern(Integral(acsch(a_ + x_*WC('b', S(1))), x_), cons2, cons3, cons67)
    def replacement6712(x, a, b):
        rubi.append(6712)
        return Int(S(1)/(sqrt(S(1) + (a + b*x)**(S(-2)))*(a + b*x)), x) + Simp((a + b*x)*acsch(a + b*x)/b, x)
    rule6712 = ReplacementRule(pattern6712, replacement6712)
    pattern6713 = Pattern(Integral(asech(a_ + x_*WC('b', S(1)))**n_, x_), cons2, cons3, cons4, cons1831)
    def replacement6713(x, a, n, b):
        rubi.append(6713)
        return -Dist(S(1)/b, Subst(Int(x**n*tanh(x)/cosh(x), x), x, asech(a + b*x)), x)
    rule6713 = ReplacementRule(pattern6713, replacement6713)
    pattern6714 = Pattern(Integral(acsch(a_ + x_*WC('b', S(1)))**n_, x_), cons2, cons3, cons4, cons1831)
    def replacement6714(x, a, n, b):
        rubi.append(6714)
        return -Dist(S(1)/b, Subst(Int(x**n/(sinh(x)*tanh(x)), x), x, acsch(a + b*x)), x)
    rule6714 = ReplacementRule(pattern6714, replacement6714)
    pattern6715 = Pattern(Integral(asech(a_ + x_*WC('b', S(1)))/x_, x_), cons2, cons3, cons67)
    def replacement6715(x, a, b):
        rubi.append(6715)
        return Simp(log(S(1) - (-sqrt(-a**S(2) + S(1)) + S(1))*exp(-asech(a + b*x))/a)*asech(a + b*x), x) + Simp(log(S(1) - (sqrt(-a**S(2) + S(1)) + S(1))*exp(-asech(a + b*x))/a)*asech(a + b*x), x) - Simp(log(S(1) + exp(-S(2)*asech(a + b*x)))*asech(a + b*x), x) - Simp(PolyLog(S(2), (-sqrt(-a**S(2) + S(1)) + S(1))*exp(-asech(a + b*x))/a), x) - Simp(PolyLog(S(2), (sqrt(-a**S(2) + S(1)) + S(1))*exp(-asech(a + b*x))/a), x) + Simp(PolyLog(S(2), -exp(-S(2)*asech(a + b*x)))/S(2), x)
    rule6715 = ReplacementRule(pattern6715, replacement6715)
    pattern6716 = Pattern(Integral(acsch(a_ + x_*WC('b', S(1)))/x_, x_), cons2, cons3, cons67)
    def replacement6716(x, a, b):
        rubi.append(6716)
        return Simp(log(S(1) + (-sqrt(a**S(2) + S(1)) + S(1))*exp(acsch(a + b*x))/a)*acsch(a + b*x), x) + Simp(log(S(1) + (sqrt(a**S(2) + S(1)) + S(1))*exp(acsch(a + b*x))/a)*acsch(a + b*x), x) - Simp(log(S(1) - exp(-S(2)*acsch(a + b*x)))*acsch(a + b*x), x) + Simp(PolyLog(S(2), -(-sqrt(a**S(2) + S(1)) + S(1))*exp(acsch(a + b*x))/a), x) + Simp(PolyLog(S(2), -(sqrt(a**S(2) + S(1)) + S(1))*exp(acsch(a + b*x))/a), x) + Simp(PolyLog(S(2), exp(-S(2)*acsch(a + b*x)))/S(2), x) - Simp(acsch(a + b*x)**S(2), x)
    rule6716 = ReplacementRule(pattern6716, replacement6716)
    pattern6717 = Pattern(Integral(x_**WC('m', S(1))*asech(a_ + x_*WC('b', S(1))), x_), cons2, cons3, cons21, cons17, cons66)
    def replacement6717(x, m, b, a):
        rubi.append(6717)
        return Dist(b**(-m + S(-1))/(m + S(1)), Subst(Int(x**(-m + S(-1))*((-a*x)**(m + S(1)) - (-a*x + S(1))**(m + S(1)))/(sqrt(x + S(-1))*sqrt(x + S(1))), x), x, S(1)/(a + b*x)), x) - Simp(b**(-m + S(-1))*(-b**(m + S(1))*x**(m + S(1)) + (-a)**(m + S(1)))*asech(a + b*x)/(m + S(1)), x)
    rule6717 = ReplacementRule(pattern6717, replacement6717)
    pattern6718 = Pattern(Integral(x_**WC('m', S(1))*acsch(a_ + x_*WC('b', S(1))), x_), cons2, cons3, cons21, cons17, cons66)
    def replacement6718(x, m, b, a):
        rubi.append(6718)
        return Dist(b**(-m + S(-1))/(m + S(1)), Subst(Int(x**(-m + S(-1))*((-a*x)**(m + S(1)) - (-a*x + S(1))**(m + S(1)))/sqrt(x**S(2) + S(1)), x), x, S(1)/(a + b*x)), x) - Simp(b**(-m + S(-1))*(-b**(m + S(1))*x**(m + S(1)) + (-a)**(m + S(1)))*acsch(a + b*x)/(m + S(1)), x)
    rule6718 = ReplacementRule(pattern6718, replacement6718)
    pattern6719 = Pattern(Integral(x_**WC('m', S(1))*asech(a_ + x_*WC('b', S(1)))**n_, x_), cons2, cons3, cons4, cons62)
    def replacement6719(m, b, a, n, x):
        rubi.append(6719)
        return -Dist(b**(-m + S(-1)), Subst(Int(x**n*(-a + S(1)/cosh(x))**m*tanh(x)/cosh(x), x), x, asech(a + b*x)), x)
    rule6719 = ReplacementRule(pattern6719, replacement6719)
    pattern6720 = Pattern(Integral(x_**WC('m', S(1))*acsch(a_ + x_*WC('b', S(1)))**n_, x_), cons2, cons3, cons4, cons62)
    def replacement6720(m, b, a, n, x):
        rubi.append(6720)
        return -Dist(b**(-m + S(-1)), Subst(Int(x**n*(-a + S(1)/sinh(x))**m/(sinh(x)*tanh(x)), x), x, acsch(a + b*x)), x)
    rule6720 = ReplacementRule(pattern6720, replacement6720)
    pattern6721 = Pattern(Integral(WC('u', S(1))*asech(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement6721(u, m, b, c, n, a, x):
        rubi.append(6721)
        return Int(u*acosh(a/c + b*x**n/c)**m, x)
    rule6721 = ReplacementRule(pattern6721, replacement6721)
    pattern6722 = Pattern(Integral(WC('u', S(1))*acsch(WC('c', S(1))/(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons4, cons21, cons1766)
    def replacement6722(u, m, b, c, n, a, x):
        rubi.append(6722)
        return Int(u*asinh(a/c + b*x**n/c)**m, x)
    rule6722 = ReplacementRule(pattern6722, replacement6722)
    pattern6723 = Pattern(Integral(exp(asech(x_*WC('a', S(1)))), x_), cons2, cons2)
    def replacement6723(x, a):
        rubi.append(6723)
        return Dist(S(1)/a, Int(sqrt((-a*x + S(1))/(a*x + S(1)))/(x*(-a*x + S(1))), x), x) + Simp(log(x)/a, x) + Simp(x*exp(asech(a*x)), x)
    rule6723 = ReplacementRule(pattern6723, replacement6723)
    pattern6724 = Pattern(Integral(exp(asech(x_**p_*WC('a', S(1)))), x_), cons2, cons5, cons1953)
    def replacement6724(x, a, p):
        rubi.append(6724)
        return Dist(p/a, Int(x**(-p), x), x) + Dist(p*sqrt(a*x**p + S(1))*sqrt(S(1)/(a*x**p + S(1)))/a, Int(x**(-p)/(sqrt(-a*x**p + S(1))*sqrt(a*x**p + S(1))), x), x) + Simp(x*exp(asech(a*x**p)), x)
    rule6724 = ReplacementRule(pattern6724, replacement6724)
    pattern6725 = Pattern(Integral(exp(acsch(x_**WC('p', S(1))*WC('a', S(1)))), x_), cons2, cons5, cons1953)
    def replacement6725(x, a, p):
        rubi.append(6725)
        return Dist(S(1)/a, Int(x**(-p), x), x) + Int(sqrt(S(1) + x**(-S(2)*p)/a**S(2)), x)
    rule6725 = ReplacementRule(pattern6725, replacement6725)
    pattern6726 = Pattern(Integral(exp(WC('n', S(1))*asech(u_)), x_), cons85)
    def replacement6726(x, n, u):
        rubi.append(6726)
        return Int((sqrt((-u + S(1))/(u + S(1))) + sqrt((-u + S(1))/(u + S(1)))/u + S(1)/u)**n, x)
    rule6726 = ReplacementRule(pattern6726, replacement6726)
    pattern6727 = Pattern(Integral(exp(WC('n', S(1))*acsch(u_)), x_), cons85)
    def replacement6727(x, n, u):
        rubi.append(6727)
        return Int((sqrt(S(1) + u**(S(-2))) + S(1)/u)**n, x)
    rule6727 = ReplacementRule(pattern6727, replacement6727)
    pattern6728 = Pattern(Integral(exp(asech(x_**WC('p', S(1))*WC('a', S(1))))/x_, x_), cons2, cons5, cons1953)
    def replacement6728(x, a, p):
        rubi.append(6728)
        return Dist(sqrt(a*x**p + S(1))*sqrt(S(1)/(a*x**p + S(1)))/a, Int(x**(-p + S(-1))*sqrt(-a*x**p + S(1))*sqrt(a*x**p + S(1)), x), x) - Simp(x**(-p)/(a*p), x)
    rule6728 = ReplacementRule(pattern6728, replacement6728)
    pattern6729 = Pattern(Integral(x_**WC('m', S(1))*exp(asech(x_**WC('p', S(1))*WC('a', S(1)))), x_), cons2, cons21, cons5, cons66)
    def replacement6729(x, m, a, p):
        rubi.append(6729)
        return Dist(p/(a*(m + S(1))), Int(x**(m - p), x), x) + Dist(p*sqrt(a*x**p + S(1))*sqrt(S(1)/(a*x**p + S(1)))/(a*(m + S(1))), Int(x**(m - p)/(sqrt(-a*x**p + S(1))*sqrt(a*x**p + S(1))), x), x) + Simp(x**(m + S(1))*exp(asech(a*x**p))/(m + S(1)), x)
    rule6729 = ReplacementRule(pattern6729, replacement6729)
    pattern6730 = Pattern(Integral(x_**WC('m', S(1))*exp(acsch(x_**WC('p', S(1))*WC('a', S(1)))), x_), cons2, cons21, cons5, cons1954)
    def replacement6730(x, m, a, p):
        rubi.append(6730)
        return Dist(S(1)/a, Int(x**(m - p), x), x) + Int(x**m*sqrt(S(1) + x**(-S(2)*p)/a**S(2)), x)
    rule6730 = ReplacementRule(pattern6730, replacement6730)
    pattern6731 = Pattern(Integral(x_**WC('m', S(1))*exp(WC('n', S(1))*asech(u_)), x_), cons21, cons85)
    def replacement6731(x, m, n, u):
        rubi.append(6731)
        return Int(x**m*(sqrt((-u + S(1))/(u + S(1))) + sqrt((-u + S(1))/(u + S(1)))/u + S(1)/u)**n, x)
    rule6731 = ReplacementRule(pattern6731, replacement6731)
    pattern6732 = Pattern(Integral(x_**WC('m', S(1))*exp(WC('n', S(1))*acsch(u_)), x_), cons21, cons85)
    def replacement6732(x, m, n, u):
        rubi.append(6732)
        return Int(x**m*(sqrt(S(1) + u**(S(-2))) + S(1)/u)**n, x)
    rule6732 = ReplacementRule(pattern6732, replacement6732)
    pattern6733 = Pattern(Integral(asech(u_), x_), cons1230, cons1769)
    def replacement6733(x, u):
        rubi.append(6733)
        return Dist(sqrt(-u**S(2) + S(1))/(u*sqrt(S(-1) + S(1)/u)*sqrt(S(1) + S(1)/u)), Int(SimplifyIntegrand(x*D(u, x)/(u*sqrt(-u**S(2) + S(1))), x), x), x) + Simp(x*asech(u), x)
    rule6733 = ReplacementRule(pattern6733, replacement6733)
    pattern6734 = Pattern(Integral(acsch(u_), x_), cons1230, cons1769)
    def replacement6734(x, u):
        rubi.append(6734)
        return -Dist(u/sqrt(-u**S(2)), Int(SimplifyIntegrand(x*D(u, x)/(u*sqrt(-u**S(2) + S(-1))), x), x), x) + Simp(x*acsch(u), x)
    rule6734 = ReplacementRule(pattern6734, replacement6734)
    pattern6735 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*asech(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1769)
    def replacement6735(u, m, b, d, c, a, x):
        rubi.append(6735)
        return Dist(b*sqrt(-u**S(2) + S(1))/(d*u*sqrt(S(-1) + S(1)/u)*sqrt(S(1) + S(1)/u)*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/(u*sqrt(-u**S(2) + S(1))), x), x), x) + Simp((a + b*asech(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule6735 = ReplacementRule(pattern6735, replacement6735)
    pattern6736 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*acsch(u_)), x_), cons2, cons3, cons7, cons27, cons21, cons66, cons1230, cons1770, cons1769)
    def replacement6736(u, m, b, d, c, a, x):
        rubi.append(6736)
        return -Dist(b*u/(d*sqrt(-u**S(2))*(m + S(1))), Int(SimplifyIntegrand((c + d*x)**(m + S(1))*D(u, x)/(u*sqrt(-u**S(2) + S(-1))), x), x), x) + Simp((a + b*acsch(u))*(c + d*x)**(m + S(1))/(d*(m + S(1))), x)
    rule6736 = ReplacementRule(pattern6736, replacement6736)
    def With6737(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern6737 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*asech(u_)), x_), cons2, cons3, cons1230, cons1955, CustomConstraint(With6737))
    def replacement6737(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(6737)
        return Dist(b*sqrt(-u**S(2) + S(1))/(u*sqrt(S(-1) + S(1)/u)*sqrt(S(1) + S(1)/u)), Int(SimplifyIntegrand(w*D(u, x)/(u*sqrt(-u**S(2) + S(1))), x), x), x) + Dist(a + b*asech(u), w, x)
    rule6737 = ReplacementRule(pattern6737, replacement6737)
    def With6738(v, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern6738 = Pattern(Integral(v_*(WC('a', S(0)) + WC('b', S(1))*acsch(u_)), x_), cons2, cons3, cons1230, cons1956, CustomConstraint(With6738))
    def replacement6738(v, u, b, a, x):

        w = IntHide(v, x)
        rubi.append(6738)
        return -Dist(b*u/sqrt(-u**S(2)), Int(SimplifyIntegrand(w*D(u, x)/(u*sqrt(-u**S(2) + S(-1))), x), x), x) + Dist(a + b*acsch(u), w, x)
    rule6738 = ReplacementRule(pattern6738, replacement6738)
    return [rule6084, rule6085, rule6086, rule6087, rule6088, rule6089, rule6090, rule6091, rule6092, rule6093, rule6094, rule6095, rule6096, rule6097, rule6098, rule6099, rule6100, rule6101, rule6102, rule6103, rule6104, rule6105, rule6106, rule6107, rule6108, rule6109, rule6110, rule6111, rule6112, rule6113, rule6114, rule6115, rule6116, rule6117, rule6118, rule6119, rule6120, rule6121, rule6122, rule6123, rule6124, rule6125, rule6126, rule6127, rule6128, rule6129, rule6130, rule6131, rule6132, rule6133, rule6134, rule6135, rule6136, rule6137, rule6138, rule6139, rule6140, rule6141, rule6142, rule6143, rule6144, rule6145, rule6146, rule6147, rule6148, rule6149, rule6150, rule6151, rule6152, rule6153, rule6154, rule6155, rule6156, rule6157, rule6158, rule6159, rule6160, rule6161, rule6162, rule6163, rule6164, rule6165, rule6166, rule6167, rule6168, rule6169, rule6170, rule6171, rule6172, rule6173, rule6174, rule6175, rule6176, rule6177, rule6178, rule6179, rule6180, rule6181, rule6182, rule6183, rule6184, rule6185, rule6186, rule6187, rule6188, rule6189, rule6190, rule6191, rule6192, rule6193, rule6194, rule6195, rule6196, rule6197, rule6198, rule6199, rule6200, rule6201, rule6202, rule6203, rule6204, rule6205, rule6206, rule6207, rule6208, rule6209, rule6210, rule6211, rule6212, rule6213, rule6214, rule6215, rule6216, rule6217, rule6218, rule6219, rule6220, rule6221, rule6222, rule6223, rule6224, rule6225, rule6226, rule6227, rule6228, rule6229, rule6230, rule6231, rule6232, rule6233, rule6234, rule6235, rule6236, rule6237, rule6238, rule6239, rule6240, rule6241, rule6242, rule6243, rule6244, rule6245, rule6246, rule6247, rule6248, rule6249, rule6250, rule6251, rule6252, rule6253, rule6254, rule6255, rule6256, rule6257, rule6258, rule6259, rule6260, rule6261, rule6262, rule6263, rule6264, rule6265, rule6266, rule6267, rule6268, rule6269, rule6270, rule6271, rule6272, rule6273, rule6274, rule6275, rule6276, rule6277, rule6278, rule6279, rule6280, rule6281, rule6282, rule6283, rule6284, rule6285, rule6286, rule6287, rule6288, rule6289, rule6290, rule6291, rule6292, rule6293, rule6294, rule6295, rule6296, rule6297, rule6298, rule6299, rule6300, rule6301, rule6302, rule6303, rule6304, rule6305, rule6306, rule6307, rule6308, rule6309, rule6310, rule6311, rule6312, rule6313, rule6314, rule6315, rule6316, rule6317, rule6318, rule6319, rule6320, rule6321, rule6322, rule6323, rule6324, rule6325, rule6326, rule6327, rule6328, rule6329, rule6330, rule6331, rule6332, rule6333, rule6334, rule6335, rule6336, rule6337, rule6338, rule6339, rule6340, rule6341, rule6342, rule6343, rule6344, rule6345, rule6346, rule6347, rule6348, rule6349, rule6350, rule6351, rule6352, rule6353, rule6354, rule6355, rule6356, rule6357, rule6358, rule6359, rule6360, rule6361, rule6362, rule6363, rule6364, rule6365, rule6366, rule6367, rule6368, rule6369, rule6370, rule6371, rule6372, rule6373, rule6374, rule6375, rule6376, rule6377, rule6378, rule6379, rule6380, rule6381, rule6382, rule6383, rule6384, rule6385, rule6386, rule6387, rule6388, rule6389, rule6390, rule6391, rule6392, rule6393, rule6394, rule6395, rule6396, rule6397, rule6398, rule6399, rule6400, rule6401, rule6402, rule6403, rule6404, rule6405, rule6406, rule6407, rule6408, rule6409, rule6410, rule6411, rule6412, rule6413, rule6414, rule6415, rule6416, rule6417, rule6418, rule6419, rule6420, rule6421, rule6422, rule6423, rule6424, rule6425, rule6426, rule6427, rule6428, rule6429, rule6430, rule6431, rule6432, rule6433, rule6434, rule6435, rule6436, rule6437, rule6438, rule6439, rule6440, rule6441, rule6442, rule6443, rule6444, rule6445, rule6446, rule6447, rule6448, rule6449, rule6450, rule6451, rule6452, rule6453, rule6454, rule6455, rule6456, rule6457, rule6458, rule6459, rule6460, rule6461, rule6462, rule6463, rule6464, rule6465, rule6466, rule6467, rule6468, rule6469, rule6470, rule6471, rule6472, rule6473, rule6474, rule6475, rule6476, rule6477, rule6478, rule6479, rule6480, rule6481, rule6482, rule6483, rule6484, rule6485, rule6486, rule6487, rule6488, rule6489, rule6490, rule6491, rule6492, rule6493, rule6494, rule6495, rule6496, rule6497, rule6498, rule6499, rule6500, rule6501, rule6502, rule6503, rule6504, rule6505, rule6506, rule6507, rule6508, rule6509, rule6510, rule6511, rule6512, rule6513, rule6514, rule6515, rule6516, rule6517, rule6518, rule6519, rule6520, rule6521, rule6522, rule6523, rule6524, rule6525, rule6526, rule6527, rule6528, rule6529, rule6530, rule6531, rule6532, rule6533, rule6534, rule6535, rule6536, rule6537, rule6538, rule6539, rule6540, rule6541, rule6542, rule6543, rule6544, rule6545, rule6546, rule6547, rule6548, rule6549, rule6550, rule6551, rule6552, rule6553, rule6554, rule6555, rule6556, rule6557, rule6558, rule6559, rule6560, rule6561, rule6562, rule6563, rule6564, rule6565, rule6566, rule6567, rule6568, rule6569, rule6570, rule6571, rule6572, rule6573, rule6574, rule6575, rule6576, rule6577, rule6578, rule6579, rule6580, rule6581, rule6582, rule6583, rule6584, rule6585, rule6586, rule6587, rule6588, rule6589, rule6590, rule6591, rule6592, rule6593, rule6594, rule6595, rule6596, rule6597, rule6598, rule6599, rule6600, rule6601, rule6602, rule6603, rule6604, rule6605, rule6606, rule6607, rule6608, rule6609, rule6610, rule6611, rule6612, rule6613, rule6614, rule6615, rule6616, rule6617, rule6618, rule6619, rule6620, rule6621, rule6622, rule6623, rule6624, rule6625, rule6626, rule6627, rule6628, rule6629, rule6630, rule6631, rule6632, rule6633, rule6634, rule6635, rule6636, rule6637, rule6638, rule6639, rule6640, rule6641, rule6642, rule6643, rule6644, rule6645, rule6646, rule6647, rule6648, rule6649, rule6650, rule6651, rule6652, rule6653, rule6654, rule6655, rule6656, rule6657, rule6658, rule6659, rule6660, rule6661, rule6662, rule6663, rule6664, rule6665, rule6666, rule6667, rule6668, rule6669, rule6670, rule6671, rule6672, rule6673, rule6674, rule6675, rule6676, rule6677, rule6678, rule6679, rule6680, rule6681, rule6682, rule6683, rule6684, rule6685, rule6686, rule6687, rule6688, rule6689, rule6690, rule6691, rule6692, rule6693, rule6694, rule6695, rule6696, rule6697, rule6698, rule6699, rule6700, rule6701, rule6702, rule6703, rule6704, rule6705, rule6706, rule6707, rule6708, rule6709, rule6710, rule6711, rule6712, rule6713, rule6714, rule6715, rule6716, rule6717, rule6718, rule6719, rule6720, rule6721, rule6722, rule6723, rule6724, rule6725, rule6726, rule6727, rule6728, rule6729, rule6730, rule6731, rule6732, rule6733, rule6734, rule6735, rule6736, rule6737, rule6738, ]
