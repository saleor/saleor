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

def logarithms(rubi):
    from sympy.integrals.rubi.constraints import cons1156, cons7, cons27, cons48, cons125, cons5, cons50, cons87, cons88, cons2, cons3, cons1157, cons415, cons1158, cons1159, cons89, cons543, cons1160, cons208, cons209, cons584, cons4, cons66, cons21, cons1161, cons1162, cons1163, cons1164, cons1165, cons1166, cons1167, cons1168, cons1169, cons148, cons1170, cons1171, cons62, cons93, cons168, cons810, cons811, cons222, cons1172, cons224, cons796, cons79, cons1173, cons17, cons1174, cons1175, cons1176, cons1177, cons1178, cons1179, cons1180, cons1181, cons1182, cons1183, cons1184, cons1185, cons1186, cons1187, cons1188, cons1189, cons1190, cons797, cons1191, cons52, cons925, cons1192, cons1193, cons1194, cons1195, cons1196, cons1197, cons1198, cons1199, cons38, cons552, cons1200, cons1201, cons1202, cons25, cons652, cons1203, cons71, cons128, cons1204, cons1205, cons1206, cons1207, cons1208, cons146, cons1209, cons1210, cons13, cons163, cons1211, cons137, cons1212, cons1213, cons1214, cons1215, cons1216, cons1217, cons1218, cons1219, cons1220, cons1221, cons1222, cons70, cons1223, cons1224, cons806, cons840, cons1225, cons1226, cons68, cons1125, cons1227, cons1228, cons1229, cons1230, cons463, cons1231, cons1232, cons1233, cons1234, cons1235, cons1236, cons31, cons1099, cons1237, cons1055, cons515, cons816, cons817, cons1238, cons1239, cons1240, cons1241, cons1242, cons1243, cons1244, cons1245, cons34, cons35, cons1246, cons1247, cons1248

    pattern2006 = Pattern(Integral(log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))), x_), cons7, cons27, cons48, cons125, cons5, cons50, cons1156)
    def replacement2006(p, f, d, c, x, q, e):
        rubi.append(2006)
        return Simp((e + f*x)*log(c*(d*(e + f*x)**p)**q)/f, x) - Simp(p*q*x, x)
    rule2006 = ReplacementRule(pattern2006, replacement2006)
    pattern2007 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons87, cons88)
    def replacement2007(p, f, b, d, a, c, n, x, q, e):
        rubi.append(2007)
        return -Dist(b*n*p*q, Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(-1)), x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))**n*(e + f*x)/f, x)
    rule2007 = ReplacementRule(pattern2007, replacement2007)
    pattern2008 = Pattern(Integral(S(1)/log((x_*WC('f', S(1)) + WC('e', S(0)))*WC('d', S(1))), x_), cons27, cons48, cons125, cons1157)
    def replacement2008(d, x, f, e):
        rubi.append(2008)
        return Simp(LogIntegral(d*(e + f*x))/(d*f), x)
    rule2008 = ReplacementRule(pattern2008, replacement2008)
    pattern2009 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons415)
    def replacement2009(p, f, b, d, a, c, x, q, e):
        rubi.append(2009)
        return Simp((c*(d*(e + f*x)**p)**q)**(-S(1)/(p*q))*(e + f*x)*ExpIntegralEi((a + b*log(c*(d*(e + f*x)**p)**q))/(b*p*q))*exp(-a/(b*p*q))/(b*f*p*q), x)
    rule2009 = ReplacementRule(pattern2009, replacement2009)
    pattern2010 = Pattern(Integral(S(1)/sqrt(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons1158)
    def replacement2010(p, f, b, d, a, c, x, q, e):
        rubi.append(2010)
        return Simp(sqrt(Pi)*(c*(d*(e + f*x)**p)**q)**(-S(1)/(p*q))*(e + f*x)*Erfi(sqrt(a + b*log(c*(d*(e + f*x)**p)**q))/Rt(b*p*q, S(2)))*Rt(b*p*q, S(2))*exp(-a/(b*p*q))/(b*f*p*q), x)
    rule2010 = ReplacementRule(pattern2010, replacement2010)
    pattern2011 = Pattern(Integral(S(1)/sqrt(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons1159)
    def replacement2011(p, f, b, d, a, c, x, q, e):
        rubi.append(2011)
        return Simp(sqrt(Pi)*(c*(d*(e + f*x)**p)**q)**(-S(1)/(p*q))*(e + f*x)*Erf(sqrt(a + b*log(c*(d*(e + f*x)**p)**q))/Rt(-b*p*q, S(2)))*Rt(-b*p*q, S(2))*exp(-a/(b*p*q))/(b*f*p*q), x)
    rule2011 = ReplacementRule(pattern2011, replacement2011)
    pattern2012 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons87, cons89)
    def replacement2012(p, f, b, d, a, c, n, x, q, e):
        rubi.append(2012)
        return -Dist(S(1)/(b*p*q*(n + S(1))), Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(1)), x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(1))*(e + f*x)/(b*f*p*q*(n + S(1))), x)
    rule2012 = ReplacementRule(pattern2012, replacement2012)
    pattern2013 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons543)
    def replacement2013(p, f, b, d, a, c, n, x, q, e):
        rubi.append(2013)
        return Simp((c*(d*(e + f*x)**p)**q)**(-S(1)/(p*q))*(-(a + b*log(c*(d*(e + f*x)**p)**q))/(b*p*q))**(-n)*(a + b*log(c*(d*(e + f*x)**p)**q))**n*(e + f*x)*Gamma(n + S(1), -(a + b*log(c*(d*(e + f*x)**p)**q))/(b*p*q))*exp(-a/(b*p*q))/f, x)
    rule2013 = ReplacementRule(pattern2013, replacement2013)
    pattern2014 = Pattern(Integral(S(1)/((x_*WC('h', S(1)) + WC('g', S(0)))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons1160)
    def replacement2014(p, f, b, g, d, a, c, x, h, q, e):
        rubi.append(2014)
        return Simp(log(RemoveContent(a + b*log(c*(d*(e + f*x)**p)**q), x))/(b*h*p*q), x)
    rule2014 = ReplacementRule(pattern2014, replacement2014)
    pattern2015 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons4, cons5, cons50, cons1160, cons584)
    def replacement2015(p, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2015)
        return Simp((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(1))/(b*h*p*q*(n + S(1))), x)
    rule2015 = ReplacementRule(pattern2015, replacement2015)
    pattern2016 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons1160, cons66, cons87, cons88)
    def replacement2016(p, m, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2016)
        return -Dist(b*n*p*q/(m + S(1)), Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(-1))*(g + h*x)**m, x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))**n*(g + h*x)**(m + S(1))/(h*(m + S(1))), x)
    rule2016 = ReplacementRule(pattern2016, replacement2016)
    pattern2017 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))/log((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1))), x_), cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons1161, cons1160, cons1162)
    def replacement2017(p, m, f, g, d, x, h, e):
        rubi.append(2017)
        return Simp((h/f)**(p + S(-1))*LogIntegral(d*(e + f*x)**p)/(d*f*p), x)
    rule2017 = ReplacementRule(pattern2017, replacement2017)
    pattern2018 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**m_/log((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1))), x_), cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons1161, cons1160, cons1163)
    def replacement2018(p, m, f, g, d, x, h, e):
        rubi.append(2018)
        return Dist((e + f*x)**(-p + S(1))*(g + h*x)**(p + S(-1)), Int((e + f*x)**(p + S(-1))/log(d*(e + f*x)**p), x), x)
    rule2018 = ReplacementRule(pattern2018, replacement2018)
    pattern2019 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))/(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons1160, cons66)
    def replacement2019(p, m, f, b, g, d, a, c, x, h, q, e):
        rubi.append(2019)
        return Simp((c*(d*(e + f*x)**p)**q)**(-(m + S(1))/(p*q))*(g + h*x)**(m + S(1))*ExpIntegralEi((a + b*log(c*(d*(e + f*x)**p)**q))*(m + S(1))/(b*p*q))*exp(-a*(m + S(1))/(b*p*q))/(b*h*p*q), x)
    rule2019 = ReplacementRule(pattern2019, replacement2019)
    pattern2020 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))/sqrt(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons1160, cons66, cons1164)
    def replacement2020(p, m, f, b, g, d, a, c, x, h, q, e):
        rubi.append(2020)
        return Simp(sqrt(Pi)*(c*(d*(e + f*x)**p)**q)**(-(m + S(1))/(p*q))*(g + h*x)**(m + S(1))*Erfi(sqrt(a + b*log(c*(d*(e + f*x)**p)**q))*Rt((m + S(1))/(b*p*q), S(2)))*exp(-a*(m + S(1))/(b*p*q))/(b*h*p*q*Rt((m + S(1))/(b*p*q), S(2))), x)
    rule2020 = ReplacementRule(pattern2020, replacement2020)
    pattern2021 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))/sqrt(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons1160, cons66, cons1165)
    def replacement2021(p, m, f, b, g, d, a, c, x, h, q, e):
        rubi.append(2021)
        return Simp(sqrt(Pi)*(c*(d*(e + f*x)**p)**q)**(-(m + S(1))/(p*q))*(g + h*x)**(m + S(1))*Erf(sqrt(a + b*log(c*(d*(e + f*x)**p)**q))*Rt(-(m + S(1))/(b*p*q), S(2)))*exp(-a*(m + S(1))/(b*p*q))/(b*h*p*q*Rt(-(m + S(1))/(b*p*q), S(2))), x)
    rule2021 = ReplacementRule(pattern2021, replacement2021)
    pattern2022 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons1160, cons66, cons87, cons89)
    def replacement2022(p, m, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2022)
        return -Dist((m + S(1))/(b*p*q*(n + S(1))), Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(1))*(g + h*x)**m, x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(1))*(g + h*x)**(m + S(1))/(b*h*p*q*(n + S(1))), x)
    rule2022 = ReplacementRule(pattern2022, replacement2022)
    pattern2023 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons5, cons1160, cons66)
    def replacement2023(p, m, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2023)
        return Simp((c*(d*(e + f*x)**p)**q)**(-(m + S(1))/(p*q))*(-(a + b*log(c*(d*(e + f*x)**p)**q))*(m + S(1))/(b*p*q))**(-n)*(a + b*log(c*(d*(e + f*x)**p)**q))**n*(g + h*x)**(m + S(1))*Gamma(n + S(1), -(a + b*log(c*(d*(e + f*x)**p)**q))*(m + S(1))/(b*p*q))*exp(-a*(m + S(1))/(b*p*q))/(h*(m + S(1))), x)
    rule2023 = ReplacementRule(pattern2023, replacement2023)
    pattern2024 = Pattern(Integral(log((x_*WC('f', S(1)) + WC('e', S(0)))*WC('c', S(1)))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons7, cons48, cons125, cons208, cons209, cons1166)
    def replacement2024(f, g, c, x, h, e):
        rubi.append(2024)
        return -Simp(PolyLog(S(2), -(g + h*x)*Together(c*f/h))/h, x)
    rule2024 = ReplacementRule(pattern2024, replacement2024)
    pattern2025 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log((x_*WC('f', S(1)) + WC('e', S(0)))*WC('c', S(1))))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons48, cons125, cons208, cons209, cons1167, cons1168)
    def replacement2025(f, b, g, a, c, x, h, e):
        rubi.append(2025)
        return Dist(b, Int(log(-h*(e + f*x)/(-e*h + f*g))/(g + h*x), x), x) + Simp((a + b*log(c*(e - f*g/h)))*log(g + h*x)/h, x)
    rule2025 = ReplacementRule(pattern2025, replacement2025)
    pattern2026 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons1169, cons148)
    def replacement2026(p, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2026)
        return -Dist(b*f*n*p*q/h, Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(-1))*log(f*(g + h*x)/(-e*h + f*g))/(e + f*x), x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))**n*log(f*(g + h*x)/(-e*h + f*g))/h, x)
    rule2026 = ReplacementRule(pattern2026, replacement2026)
    pattern2027 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons1169, cons66)
    def replacement2027(p, m, f, b, g, d, a, c, x, h, q, e):
        rubi.append(2027)
        return -Dist(b*f*p*q/(h*(m + S(1))), Int((g + h*x)**(m + S(1))/(e + f*x), x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))*(g + h*x)**(m + S(1))/(h*(m + S(1))), x)
    rule2027 = ReplacementRule(pattern2027, replacement2027)
    pattern2028 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**n_/(x_*WC('h', S(1)) + WC('g', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons1169, cons87, cons88)
    def replacement2028(p, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2028)
        return -Dist(b*f*n*p*q/(-e*h + f*g), Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(-1))/(g + h*x), x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))**n*(e + f*x)/((g + h*x)*(-e*h + f*g)), x)
    rule2028 = ReplacementRule(pattern2028, replacement2028)
    pattern2029 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons1169, cons87, cons88, cons66, cons1170, cons1171)
    def replacement2029(p, m, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2029)
        return -Dist(b*f*n*p*q/(h*(m + S(1))), Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(-1))*(g + h*x)**(m + S(1))/(e + f*x), x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))**n*(g + h*x)**(m + S(1))/(h*(m + S(1))), x)
    rule2029 = ReplacementRule(pattern2029, replacement2029)
    pattern2030 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))/(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons1169, cons62)
    def replacement2030(p, m, f, b, g, d, a, c, x, h, q, e):
        rubi.append(2030)
        return Int(ExpandIntegrand((g + h*x)**m/(a + b*log(c*(d*(e + f*x)**p)**q)), x), x)
    rule2030 = ReplacementRule(pattern2030, replacement2030)
    pattern2031 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons1169, cons93, cons89, cons168)
    def replacement2031(p, m, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2031)
        return -Dist((m + S(1))/(b*p*q*(n + S(1))), Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(1))*(g + h*x)**m, x), x) + Dist(m*(-e*h + f*g)/(b*f*p*q*(n + S(1))), Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(1))*(g + h*x)**(m + S(-1)), x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(1))*(e + f*x)*(g + h*x)**m/(b*f*p*q*(n + S(1))), x)
    rule2031 = ReplacementRule(pattern2031, replacement2031)
    pattern2032 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons4, cons5, cons50, cons1169, cons62)
    def replacement2032(p, m, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2032)
        return Int(ExpandIntegrand((a + b*log(c*(d*(e + f*x)**p)**q))**n*(g + h*x)**m, x), x)
    rule2032 = ReplacementRule(pattern2032, replacement2032)
    pattern2033 = Pattern(Integral(u_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log((v_**p_*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons50, cons810, cons811)
    def replacement2033(v, p, u, m, b, d, a, c, n, x, q):
        rubi.append(2033)
        return Int((a + b*log(c*(d*ExpandToSum(v, x)**p)**q))**n*ExpandToSum(u, x)**m, x)
    rule2033 = ReplacementRule(pattern2033, replacement2033)
    pattern2034 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons5, cons50, cons222)
    def replacement2034(p, m, f, b, g, d, a, c, n, x, h, q, e):
        rubi.append(2034)
        return Int((a + b*log(c*(d*(e + f*x)**p)**q))**n*(g + h*x)**m, x)
    rule2034 = ReplacementRule(pattern2034, replacement2034)
    pattern2035 = Pattern(Integral(log(WC('c', S(1))/(x_*WC('f', S(1)) + WC('e', S(0))))/((x_*WC('h', S(1)) + WC('g', S(0)))*(x_*WC('j', S(1)) + WC('i', S(0)))), x_), cons7, cons48, cons125, cons208, cons209, cons224, cons796, cons1160, cons1172)
    def replacement2035(j, f, g, i, c, x, h, e):
        rubi.append(2035)
        return Simp(f*PolyLog(S(2), f*(i + j*x)/(j*(e + f*x)))/(h*(-e*j + f*i)), x)
    rule2035 = ReplacementRule(pattern2035, replacement2035)
    pattern2036 = Pattern(Integral((a_ + WC('b', S(1))*log(WC('c', S(1))/(x_*WC('f', S(1)) + WC('e', S(0)))))/((x_*WC('h', S(1)) + WC('g', S(0)))*(x_*WC('j', S(1)) + WC('i', S(0)))), x_), cons2, cons3, cons7, cons48, cons125, cons208, cons209, cons224, cons796, cons1160, cons1172)
    def replacement2036(j, f, b, g, i, c, a, x, h, e):
        rubi.append(2036)
        return Dist(a, Int(S(1)/((g + h*x)*(i + j*x)), x), x) + Dist(b, Int(log(c/(e + f*x))/((g + h*x)*(i + j*x)), x), x)
    rule2036 = ReplacementRule(pattern2036, replacement2036)
    def With2037(p, j, m, f, b, g, i, d, a, c, x, h, q, e):
        u = IntHide((i + j*x)**m/(g + h*x), x)
        rubi.append(2037)
        return -Dist(b*h*p*q, Int(SimplifyIntegrand(u/(g + h*x), x), x), x) + Dist(a + b*log(c*(d*(e + f*x)**p)**q), u, x)
    pattern2037 = Pattern(Integral((x_*WC('j', S(1)) + WC('i', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons796, cons5, cons50, cons1160, cons79)
    rule2037 = ReplacementRule(pattern2037, With2037)
    pattern2038 = Pattern(Integral((x_*WC('j', S(1)) + WC('i', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log((x_*WC('f', S(1)) + WC('e', S(0)))*WC('c', S(1))))**WC('n', S(1))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons48, cons125, cons208, cons209, cons224, cons796, cons4, cons1160, cons62, cons1173)
    def replacement2038(j, m, f, b, g, i, a, c, n, x, h, e):
        rubi.append(2038)
        return Dist(c**(-m)*f**(-m)/h, Subst(Int((a + b*x)**n*(-c*e*j + c*f*i + j*exp(x))**m, x), x, log(c*(e + f*x))), x)
    rule2038 = ReplacementRule(pattern2038, replacement2038)
    def With2039(p, j, m, f, b, g, i, d, a, c, n, x, h, q, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand((a + b*log(c*(d*(e + f*x)**p)**q))**n, (i + j*x)**m/(g + h*x), x)
        if SumQ(u):
            return True
        return False
    pattern2039 = Pattern(Integral((x_*WC('j', S(1)) + WC('i', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons796, cons5, cons50, cons17, cons148, CustomConstraint(With2039))
    def replacement2039(p, j, m, f, b, g, i, d, a, c, n, x, h, q, e):

        u = ExpandIntegrand((a + b*log(c*(d*(e + f*x)**p)**q))**n, (i + j*x)**m/(g + h*x), x)
        rubi.append(2039)
        return Int(u, x)
    rule2039 = ReplacementRule(pattern2039, replacement2039)
    pattern2040 = Pattern(Integral((x_*WC('j', S(1)) + WC('i', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons796, cons21, cons4, cons5, cons50, cons1174)
    def replacement2040(p, j, m, f, b, g, i, d, a, c, n, x, h, q, e):
        rubi.append(2040)
        return Int((a + b*log(c*(d*(e + f*x)**p)**q))**n*(i + j*x)**m/(g + h*x), x)
    rule2040 = ReplacementRule(pattern2040, replacement2040)
    pattern2041 = Pattern(Integral(log(WC('c', S(1))/(x_*WC('f', S(1)) + WC('e', S(0))))/(g_ + x_**S(2)*WC('h', S(1))), x_), cons7, cons48, cons125, cons208, cons209, cons1175, cons1176)
    def replacement2041(f, g, c, x, h, e):
        rubi.append(2041)
        return -Simp(f*PolyLog(S(2), (-e + f*x)/(e + f*x))/(S(2)*e*h), x)
    rule2041 = ReplacementRule(pattern2041, replacement2041)
    pattern2042 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(WC('c', S(1))/(x_*WC('f', S(1)) + WC('e', S(0)))))/(g_ + x_**S(2)*WC('h', S(1))), x_), cons7, cons48, cons125, cons208, cons209, cons1175, cons1177, cons1178)
    def replacement2042(f, b, g, a, c, x, h, e):
        rubi.append(2042)
        return Dist(b, Int(log(S(2)*e/(e + f*x))/(g + h*x**S(2)), x), x) + Dist(a + b*log(c/(S(2)*e)), Int(S(1)/(g + h*x**S(2)), x), x)
    rule2042 = ReplacementRule(pattern2042, replacement2042)
    pattern2043 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))/(x_**S(2)*WC('i', S(1)) + x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons5, cons50, cons1179)
    def replacement2043(p, f, b, g, i, d, a, c, x, h, q, e):
        rubi.append(2043)
        return Dist(e*f, Int((a + b*log(c*(d*(e + f*x)**p)**q))/((e + f*x)*(e*i*x + f*g)), x), x)
    rule2043 = ReplacementRule(pattern2043, replacement2043)
    pattern2044 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((e_ + x_*WC('f', S(1)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))/(g_ + x_**S(2)*WC('i', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons224, cons5, cons50, cons1180)
    def replacement2044(p, f, b, g, i, d, a, c, x, q, e):
        rubi.append(2044)
        return Dist(e*f, Int((a + b*log(c*(d*(e + f*x)**p)**q))/((e + f*x)*(e*i*x + f*g)), x), x)
    rule2044 = ReplacementRule(pattern2044, replacement2044)
    def With2045(p, f, b, g, d, a, c, x, h, q, e):
        u = IntHide(S(1)/sqrt(g + h*x**S(2)), x)
        rubi.append(2045)
        return -Dist(b*f*p*q, Int(SimplifyIntegrand(u/(e + f*x), x), x), x) + Simp(u*(a + b*log(c*(d*(e + f*x)**p)**q)), x)
    pattern2045 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))/sqrt(g_ + x_**S(2)*WC('h', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons1181)
    rule2045 = ReplacementRule(pattern2045, With2045)
    def With2046(p, f, b, d, h1, a, c, h2, g2, x, g1, q, e):
        u = IntHide(S(1)/sqrt(g1*g2 + h1*h2*x**S(2)), x)
        rubi.append(2046)
        return -Dist(b*f*p*q, Int(SimplifyIntegrand(u/(e + f*x), x), x), x) + Simp(u*(a + b*log(c*(d*(e + f*x)**p)**q)), x)
    pattern2046 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))/(sqrt(g1_ + x_*WC('h1', S(1)))*sqrt(g2_ + x_*WC('h2', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1185, cons1186, cons1187, cons1188, cons5, cons50, cons1182, cons1183, cons1184)
    rule2046 = ReplacementRule(pattern2046, With2046)
    pattern2047 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))/sqrt(g_ + x_**S(2)*WC('h', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons1189)
    def replacement2047(p, f, b, g, d, a, c, x, h, q, e):
        rubi.append(2047)
        return Dist(sqrt(S(1) + h*x**S(2)/g)/sqrt(g + h*x**S(2)), Int((a + b*log(c*(d*(e + f*x)**p)**q))/sqrt(S(1) + h*x**S(2)/g), x), x)
    rule2047 = ReplacementRule(pattern2047, replacement2047)
    pattern2048 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))/(sqrt(g1_ + x_*WC('h1', S(1)))*sqrt(g2_ + x_*WC('h2', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1185, cons1186, cons1187, cons1188, cons5, cons50, cons1182)
    def replacement2048(p, f, b, d, h1, a, c, h2, g2, x, g1, q, e):
        rubi.append(2048)
        return Dist(sqrt(S(1) + h1*h2*x**S(2)/(g1*g2))/(sqrt(g1 + h1*x)*sqrt(g2 + h2*x)), Int((a + b*log(c*(d*(e + f*x)**p)**q))/sqrt(S(1) + h1*h2*x**S(2)/(g1*g2)), x), x)
    rule2048 = ReplacementRule(pattern2048, replacement2048)
    pattern2049 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('k', S(1)) + WC('j', S(0)))*WC('i', S(1)))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons796, cons797, cons5, cons50, cons87, cons88, cons1190)
    def replacement2049(p, j, k, f, b, g, i, d, a, c, n, x, h, q, e):
        rubi.append(2049)
        return Dist(b*f*n*p*q/h, Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(-1))*PolyLog(S(2), Together(-i*(j + k*x) + S(1)))/(e + f*x), x), x) - Simp((a + b*log(c*(d*(e + f*x)**p)**q))**n*PolyLog(S(2), Together(-i*(j + k*x) + S(1)))/h, x)
    rule2049 = ReplacementRule(pattern2049, replacement2049)
    pattern2050 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))*log((x_*WC('k', S(1)) + WC('j', S(0)))**WC('m', S(1))*WC('i', S(1)) + S(1))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons796, cons797, cons21, cons5, cons50, cons87, cons88, cons1191)
    def replacement2050(p, j, k, m, f, b, g, i, d, a, c, n, x, h, q, e):
        rubi.append(2050)
        return Dist(b*f*n*p*q/(h*m), Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(-1))*PolyLog(S(2), -i*(j + k*x)**m)/(e + f*x), x), x) - Simp((a + b*log(c*(d*(e + f*x)**p)**q))**n*PolyLog(S(2), -i*(j + k*x)**m)/(h*m), x)
    rule2050 = ReplacementRule(pattern2050, replacement2050)
    pattern2051 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))*PolyLog(r_, (x_*WC('k', S(1)) + WC('j', S(0)))**WC('m', S(1))*WC('i', S(1)))/(x_*WC('h', S(1)) + WC('g', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons796, cons797, cons21, cons5, cons50, cons52, cons87, cons88, cons1191)
    def replacement2051(p, j, k, m, f, b, g, r, i, d, a, c, n, x, h, q, e):
        rubi.append(2051)
        return -Dist(b*f*n*p*q/(h*m), Int((a + b*log(c*(d*(e + f*x)**p)**q))**(n + S(-1))*PolyLog(r + S(1), i*(j + k*x)**m)/(e + f*x), x), x) + Simp((a + b*log(c*(d*(e + f*x)**p)**q))**n*PolyLog(r + S(1), i*(j + k*x)**m)/(h*m), x)
    rule2051 = ReplacementRule(pattern2051, replacement2051)
    def With2052(p, m, f, b, g, Px, d, a, c, x, h, q, e, F):
        u = IntHide(Px*F(g + h*x)**m, x)
        rubi.append(2052)
        return -Dist(b*f*p*q, Int(SimplifyIntegrand(u/(e + f*x), x), x), x) + Dist(a + b*log(c*(d*(e + f*x)**p)**q), u, x)
    pattern2052 = Pattern(Integral(F_**(x_*WC('h', S(1)) + WC('g', S(0)))*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))*WC('Px', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons925, cons62, cons1192)
    rule2052 = ReplacementRule(pattern2052, With2052)
    pattern2053 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((e_ + x_**m_*WC('f', S(1)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))/x_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons50, cons148)
    def replacement2053(p, m, f, b, d, a, c, n, x, q, e):
        rubi.append(2053)
        return Dist(S(1)/m, Subst(Int((a + b*log(c*(d*(e + f*x)**p)**q))**n/x, x), x, x**m), x)
    rule2053 = ReplacementRule(pattern2053, replacement2053)
    pattern2054 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_**m_*(f_ + x_**WC('r', S(1))*WC('e', S(1))))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))/x_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons50, cons1193, cons148)
    def replacement2054(p, m, f, b, r, d, a, c, n, x, q, e):
        rubi.append(2054)
        return Dist(S(1)/m, Subst(Int((a + b*log(c*(d*(e + f*x)**p)**q))**n/x, x), x, x**m), x)
    rule2054 = ReplacementRule(pattern2054, replacement2054)
    pattern2055 = Pattern(Integral(x_**WC('r1', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_**r_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons50, cons52, cons1194)
    def replacement2055(p, r1, f, b, r, d, a, c, n, x, q, e):
        rubi.append(2055)
        return Dist(S(1)/r, Subst(Int((a + b*log(c*(d*(e + f*x)**p)**q))**n, x), x, x**r), x)
    rule2055 = ReplacementRule(pattern2055, replacement2055)
    pattern2056 = Pattern(Integral(x_**WC('r1', S(1))*(x_**r_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(((x_**r_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons4, cons5, cons50, cons52, cons1194)
    def replacement2056(p, r1, m, f, b, g, r, d, a, c, n, x, h, q, e):
        rubi.append(2056)
        return Dist(S(1)/r, Subst(Int((a + b*log(c*(d*(e + f*x)**p)**q))**n*(g + h*x)**m, x), x, x**r), x)
    rule2056 = ReplacementRule(pattern2056, replacement2056)
    def With2057(b, d, a, n, c, x, e):
        u = IntHide(S(1)/(d + e*x**S(2)), x)
        rubi.append(2057)
        return -Dist(b*n, Int(u/x, x), x) + Dist(a + b*log(c*x**n), u, x)
    pattern2057 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(x_**WC('n', S(1))*WC('c', S(1))))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1195)
    rule2057 = ReplacementRule(pattern2057, With2057)
    pattern2058 = Pattern(Integral(log((x_**mn_*WC('b', S(1)) + WC('a', S(0)))*WC('c', S(1)))/(x_*(d_ + x_**WC('n', S(1))*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1196, cons1197)
    def replacement2058(mn, b, d, c, n, a, x, e):
        rubi.append(2058)
        return Simp(PolyLog(S(2), -Together(b*c*x**(-n)*(d + e*x**n)/d))/(d*n), x)
    rule2058 = ReplacementRule(pattern2058, replacement2058)
    pattern2059 = Pattern(Integral(log(x_**mn_*(x_**WC('n', S(1))*WC('a', S(1)) + WC('b', S(0)))*WC('c', S(1)))/(x_*(d_ + x_**WC('n', S(1))*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1196, cons1197)
    def replacement2059(mn, b, d, c, n, a, x, e):
        rubi.append(2059)
        return Simp(PolyLog(S(2), -Together(b*c*x**(-n)*(d + e*x**n)/d))/(d*n), x)
    rule2059 = ReplacementRule(pattern2059, replacement2059)
    pattern2060 = Pattern(Integral(Px_*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons50, cons925)
    def replacement2060(p, f, b, Px, d, a, c, n, x, q, e):
        rubi.append(2060)
        return Int(ExpandIntegrand(Px*(a + b*log(c*(d*(e + f*x)**p)**q))**n, x), x)
    rule2060 = ReplacementRule(pattern2060, replacement2060)
    def With2061(p, RFx, f, b, d, a, c, n, x, q, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand((a + b*log(c*(d*(e + f*x)**p)**q))**n, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern2061 = Pattern(Integral(RFx_*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons1198, cons148, CustomConstraint(With2061))
    def replacement2061(p, RFx, f, b, d, a, c, n, x, q, e):

        u = ExpandIntegrand((a + b*log(c*(d*(e + f*x)**p)**q))**n, RFx, x)
        rubi.append(2061)
        return Int(u, x)
    rule2061 = ReplacementRule(pattern2061, replacement2061)
    def With2062(p, RFx, f, b, d, a, c, n, x, q, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(RFx*(a + b*log(c*(d*(e + f*x)**p)**q))**n, x)
        if SumQ(u):
            return True
        return False
    pattern2062 = Pattern(Integral(RFx_*(WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons1198, cons148, CustomConstraint(With2062))
    def replacement2062(p, RFx, f, b, d, a, c, n, x, q, e):

        u = ExpandIntegrand(RFx*(a + b*log(c*(d*(e + f*x)**p)**q))**n, x)
        rubi.append(2062)
        return Int(u, x)
    rule2062 = ReplacementRule(pattern2062, replacement2062)
    pattern2063 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_**S(2)*WC('g', S(1)) + x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))*WC('u', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons50, cons4, cons1199, cons38)
    def replacement2063(p, u, f, g, b, d, a, c, n, x, q, e):
        rubi.append(2063)
        return Int(u*(a + b*log(c*(S(4)**(-p)*d*g**(-p)*(f + S(2)*g*x)**(S(2)*p))**q))**n, x)
    rule2063 = ReplacementRule(pattern2063, replacement2063)
    pattern2064 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log((v_**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**WC('n', S(1))*WC('u', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons50, cons552, cons1200)
    def replacement2064(v, p, u, b, d, a, c, n, x, q):
        rubi.append(2064)
        return Int(u*(a + b*log(c*(d*ExpandToSum(v, x)**p)**q))**n, x)
    rule2064 = ReplacementRule(pattern2064, replacement2064)
    pattern2065 = Pattern(Integral(log(((x_**WC('n', S(1))*WC('c', S(1)))**p_*WC('b', S(1)))**q_*WC('a', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons4, cons5, cons50, cons52, cons1201)
    def replacement2065(p, b, r, c, a, n, x, q):
        rubi.append(2065)
        return Subst(Int(log(x**(n*p*q))**r, x), x**(n*p*q), a*(b*(c*x**n)**p)**q)
    rule2065 = ReplacementRule(pattern2065, replacement2065)
    pattern2066 = Pattern(Integral(x_**WC('m', S(1))*log(((x_**WC('n', S(1))*WC('c', S(1)))**p_*WC('b', S(1)))**q_*WC('a', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons21, cons4, cons5, cons50, cons52, cons66, cons1202)
    def replacement2066(p, m, b, r, c, a, n, x, q):
        rubi.append(2066)
        return Subst(Int(x**m*log(x**(n*p*q))**r, x), x**(n*p*q), a*(b*(c*x**n)**p)**q)
    rule2066 = ReplacementRule(pattern2066, replacement2066)
    pattern2067 = Pattern(Integral(WC('u', S(1))*log(((x_*WC('b', S(1)) + WC('a', S(0)))*WC('e1', S(1))/(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons652, cons25)
    def replacement2067(p, u, b, d, c, a, n, e1, x, e):
        rubi.append(2067)
        return Dist(log(e*(b*e1/d)**n)**p, Int(u, x), x)
    rule2067 = ReplacementRule(pattern2067, replacement2067)
    pattern2068 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons652, cons1204, cons1203, cons71, cons128)
    def replacement2068(p, n1, b, n2, d, a, c, n, e1, x, e):
        rubi.append(2068)
        return -Dist(n*n1*p*(-a*d + b*c)/b, Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**(p + S(-1))/(c + d*x), x), x) + Simp((a + b*x)*log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/b, x)
    rule2068 = ReplacementRule(pattern2068, replacement2068)
    pattern2069 = Pattern(Integral(log((x_*WC('b', S(1)) + WC('a', S(0)))*WC('e', S(1))/(x_*WC('d', S(1)) + WC('c', S(0))))/(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1205, cons1206)
    def replacement2069(f, b, g, d, c, a, x, e):
        rubi.append(2069)
        return Simp(PolyLog(S(2), Together(-a*e + c)/(c + d*x))/g, x)
    rule2069 = ReplacementRule(pattern2069, replacement2069)
    pattern2070 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1205, cons128)
    def replacement2070(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2070)
        return Dist(n*n1*p*(-a*d + b*c)/g, Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**(p + S(-1))*log((-a*d + b*c)/(b*(c + d*x)))/((a + b*x)*(c + d*x)), x), x) - Simp(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p*log((-a*d + b*c)/(b*(c + d*x)))/g, x)
    rule2070 = ReplacementRule(pattern2070, replacement2070)
    pattern2071 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1207, cons128)
    def replacement2071(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2071)
        return Dist(n*n1*p*(-a*d + b*c)/g, Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**(p + S(-1))*log(-(-a*d + b*c)/(d*(a + b*x)))/((a + b*x)*(c + d*x)), x), x) - Simp(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p*log(-(-a*d + b*c)/(d*(a + b*x)))/g, x)
    rule2071 = ReplacementRule(pattern2071, replacement2071)
    pattern2072 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))/(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1208)
    def replacement2072(n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2072)
        return -Dist(n*n1*(-a*d + b*c)/g, Int(log(f + g*x)/((a + b*x)*(c + d*x)), x), x) + Simp(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)*log(f + g*x)/g, x)
    rule2072 = ReplacementRule(pattern2072, replacement2072)
    pattern2073 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**p_/(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1208, cons38, cons146)
    def replacement2073(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2073)
        return Dist(d/g, Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/(c + d*x), x), x) - Dist((-c*g + d*f)/g, Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/((c + d*x)*(f + g*x)), x), x)
    rule2073 = ReplacementRule(pattern2073, replacement2073)
    pattern2074 = Pattern(Integral(S(1)/((x_*WC('g', S(1)) + WC('f', S(0)))**S(2)*log((x_*WC('b', S(1)) + WC('a', S(0)))*WC('e', S(1))/(x_*WC('d', S(1)) + WC('c', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1205)
    def replacement2074(f, b, g, d, c, a, x, e):
        rubi.append(2074)
        return Simp(d**S(2)*LogIntegral(e*(a + b*x)/(c + d*x))/(e*g**S(2)*(-a*d + b*c)), x)
    rule2074 = ReplacementRule(pattern2074, replacement2074)
    pattern2075 = Pattern(Integral(S(1)/((x_*WC('g', S(1)) + WC('f', S(0)))**S(2)*log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1205)
    def replacement2075(n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2075)
        return Simp(d**S(2)*(e*(e1*(a + b*x)**n1*(c + d*x)**n2)**n)**(-S(1)/(n*n1))*(a + b*x)*ExpIntegralEi(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)/(n*n1))/(g**S(2)*n*n1*(c + d*x)*(-a*d + b*c)), x)
    rule2075 = ReplacementRule(pattern2075, replacement2075)
    pattern2076 = Pattern(Integral(S(1)/((x_*WC('g', S(1)) + WC('f', S(0)))**S(2)*log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1207)
    def replacement2076(n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2076)
        return Simp(b**S(2)*(e*(e1*(a + b*x)**n1*(c + d*x)**n2)**n)**(S(1)/(n*n1))*(c + d*x)*ExpIntegralEi(-log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)/(n*n1))/(g**S(2)*n*n1*(a + b*x)*(-a*d + b*c)), x)
    rule2076 = ReplacementRule(pattern2076, replacement2076)
    pattern2077 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/(x_*WC('g', S(1)) + WC('f', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1209, cons128)
    def replacement2077(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2077)
        return -Dist(n*n1*p*(-a*d + b*c)/(-a*g + b*f), Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**(p + S(-1))/((c + d*x)*(f + g*x)), x), x) + Simp((a + b*x)*log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/((f + g*x)*(-a*g + b*f)), x)
    rule2077 = ReplacementRule(pattern2077, replacement2077)
    pattern2078 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/(x_*WC('g', S(1)) + WC('f', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1208, cons128)
    def replacement2078(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2078)
        return -Dist(n*n1*p*(-a*d + b*c)/(-c*g + d*f), Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**(p + S(-1))/((a + b*x)*(f + g*x)), x), x) + Simp((c + d*x)*log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/((f + g*x)*(-c*g + d*f)), x)
    rule2078 = ReplacementRule(pattern2078, replacement2078)
    pattern2079 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**p_/(x_*WC('g', S(1)) + WC('f', S(0)))**S(3), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons652, cons1204, cons1203, cons71, cons1209, cons1205)
    def replacement2079(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2079)
        return Dist(b/(-a*g + b*f), Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/(f + g*x)**S(2), x), x) - Dist(g/(-a*g + b*f), Int((a + b*x)*log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/(f + g*x)**S(3), x), x)
    rule2079 = ReplacementRule(pattern2079, replacement2079)
    pattern2080 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**p_/(x_*WC('g', S(1)) + WC('f', S(0)))**S(3), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons652, cons1204, cons1203, cons71, cons1208, cons1207)
    def replacement2080(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2080)
        return Dist(d/(-c*g + d*f), Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/(f + g*x)**S(2), x), x) - Dist(g/(-c*g + d*f), Int((c + d*x)*log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/(f + g*x)**S(3), x), x)
    rule2080 = ReplacementRule(pattern2080, replacement2080)
    pattern2081 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons128, cons17, cons66)
    def replacement2081(p, m, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2081)
        return -Dist(n*n1*p*(-a*d + b*c)/(g*(m + S(1))), Int((f + g*x)**(m + S(1))*log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**(p + S(-1))/((a + b*x)*(c + d*x)), x), x) + Simp((f + g*x)**(m + S(1))*log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/(g*(m + S(1))), x)
    rule2081 = ReplacementRule(pattern2081, replacement2081)
    pattern2082 = Pattern(Integral((x_*WC('b', S(1)) + WC('a', S(0)))**WC('m', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m2', S(1))*log(u_**n_*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1211, cons1210, cons71, cons66, cons13, cons163)
    def replacement2082(p, u, m2, m, b, d, a, c, n, x, e):
        rubi.append(2082)
        return -Dist(n*p/(m + S(1)), Int((a + b*x)**m*(c + d*x)**(-m + S(-2))*log(e*u**n)**(p + S(-1)), x), x) + Simp((a + b*x)**(m + S(1))*(c + d*x)**(-m + S(-1))*log(e*u**n)**p/((m + S(1))*(-a*d + b*c)), x)
    rule2082 = ReplacementRule(pattern2082, replacement2082)
    pattern2083 = Pattern(Integral((x_*WC('b', S(1)) + WC('a', S(0)))**WC('m', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m2', S(1))*log(u_)**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons1211, cons1210, cons71, cons66, cons13, cons163)
    def replacement2083(p, u, m2, m, b, d, a, c, x):
        rubi.append(2083)
        return -Dist(p/(m + S(1)), Int((a + b*x)**m*(c + d*x)**(-m + S(-2))*log(u)**(p + S(-1)), x), x) + Simp((a + b*x)**(m + S(1))*(c + d*x)**(-m + S(-1))*log(u)**p/((m + S(1))*(-a*d + b*c)), x)
    rule2083 = ReplacementRule(pattern2083, replacement2083)
    pattern2084 = Pattern(Integral((x_*WC('b', S(1)) + WC('a', S(0)))**WC('m', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m2', S(1))/log(u_**n_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1211, cons1210, cons71, cons66)
    def replacement2084(u, m2, m, b, d, a, c, n, x, e):
        rubi.append(2084)
        return Simp((e*u**n)**(-(m + S(1))/n)*(a + b*x)**(m + S(1))*(c + d*x)**(-m + S(-1))*ExpIntegralEi((m + S(1))*log(e*u**n)/n)/(n*(-a*d + b*c)), x)
    rule2084 = ReplacementRule(pattern2084, replacement2084)
    pattern2085 = Pattern(Integral((x_*WC('b', S(1)) + WC('a', S(0)))**WC('m', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m2', S(1))/log(u_), x_), cons2, cons3, cons7, cons27, cons1211, cons1210, cons71, cons66)
    def replacement2085(u, m2, m, b, d, a, c, x):
        rubi.append(2085)
        return Simp(u**(-m + S(-1))*(a + b*x)**(m + S(1))*(c + d*x)**(-m + S(-1))*ExpIntegralEi((m + S(1))*log(u))/(-a*d + b*c), x)
    rule2085 = ReplacementRule(pattern2085, replacement2085)
    pattern2086 = Pattern(Integral((x_*WC('b', S(1)) + WC('a', S(0)))**WC('m', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m2', S(1))*log(u_**n_*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1211, cons1210, cons71, cons66, cons13, cons137)
    def replacement2086(p, u, m2, m, b, d, a, c, n, x, e):
        rubi.append(2086)
        return -Dist((m + S(1))/(n*(p + S(1))), Int((a + b*x)**m*(c + d*x)**(-m + S(-2))*log(e*u**n)**(p + S(1)), x), x) + Simp((a + b*x)**(m + S(1))*(c + d*x)**(-m + S(-1))*log(e*u**n)**(p + S(1))/(n*(p + S(1))*(-a*d + b*c)), x)
    rule2086 = ReplacementRule(pattern2086, replacement2086)
    pattern2087 = Pattern(Integral((x_*WC('b', S(1)) + WC('a', S(0)))**WC('m', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m2', S(1))*log(u_)**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons1211, cons1210, cons71, cons66, cons13, cons137)
    def replacement2087(p, u, m2, m, b, d, a, c, x):
        rubi.append(2087)
        return -Dist((m + S(1))/(p + S(1)), Int((a + b*x)**m*(c + d*x)**(-m + S(-2))*log(u)**(p + S(1)), x), x) + Simp((a + b*x)**(m + S(1))*(c + d*x)**(-m + S(-1))*log(u)**(p + S(1))/((p + S(1))*(-a*d + b*c)), x)
    rule2087 = ReplacementRule(pattern2087, replacement2087)
    pattern2088 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/((x_*WC('d', S(1)) + WC('c', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1209, cons1205)
    def replacement2088(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2088)
        return Dist(d/g, Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/(c + d*x)**S(2), x), x)
    rule2088 = ReplacementRule(pattern2088, replacement2088)
    pattern2089 = Pattern(Integral(log((x_*WC('b', S(1)) + WC('a', S(0)))*WC('e', S(1))/(x_*WC('d', S(1)) + WC('c', S(0))))/((x_*WC('d', S(1)) + WC('c', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1209, cons1208, cons1212)
    def replacement2089(f, b, g, d, c, a, x, e):
        rubi.append(2089)
        return Simp(PolyLog(S(2), -(f + g*x)*(a*e - c)/(f*(c + d*x)))/(-c*g + d*f), x)
    rule2089 = ReplacementRule(pattern2089, replacement2089)
    pattern2090 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/((x_*WC('d', S(1)) + WC('c', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons652, cons1204, cons1203, cons71, cons1209, cons1208, cons128)
    def replacement2090(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2090)
        return Dist(n*n1*p*(-a*d + b*c)/(-c*g + d*f), Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**(p + S(-1))*log((f + g*x)*(-a*d + b*c)/((c + d*x)*(-a*g + b*f)))/((a + b*x)*(c + d*x)), x), x) - Simp(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p*log((f + g*x)*(-a*d + b*c)/((c + d*x)*(-a*g + b*f)))/(-c*g + d*f), x)
    rule2090 = ReplacementRule(pattern2090, replacement2090)
    pattern2091 = Pattern(Integral(log((x_*WC('b', S(1)) + WC('a', S(0)))*WC('e', S(1))/(x_*WC('d', S(1)) + WC('c', S(0))))/(f_ + x_**S(2)*WC('g', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1213, cons1214)
    def replacement2091(g, b, f, d, c, a, x, e):
        rubi.append(2091)
        return Simp(c*PolyLog(S(2), -(c - d*x)*(a*e - c)/(c*(c + d*x)))/(S(2)*d*f), x)
    rule2091 = ReplacementRule(pattern2091, replacement2091)
    pattern2092 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/(x_**S(2)*WC('h', S(1)) + x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons4, cons5, cons652, cons1204, cons1203, cons71, cons1215)
    def replacement2092(p, n1, b, f, g, n2, d, a, c, n, e1, x, h, e):
        rubi.append(2092)
        return Dist(d**S(2), Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/((c + d*x)*(-c*h + d*g + d*h*x)), x), x)
    rule2092 = ReplacementRule(pattern2092, replacement2092)
    pattern2093 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/(x_**S(2)*WC('h', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons209, cons4, cons5, cons652, cons1204, cons1203, cons71, cons1216)
    def replacement2093(p, n1, b, f, n2, d, a, c, n, e1, x, h, e):
        rubi.append(2093)
        return -Dist(d**S(2)/h, Int(log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/((c - d*x)*(c + d*x)), x), x)
    rule2093 = ReplacementRule(pattern2093, replacement2093)
    pattern2094 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/((x_*WC('d', S(1)) + WC('c', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons652, cons1204, cons1203, cons71, cons1208, cons1207)
    def replacement2094(p, n1, b, f, g, n2, d, a, c, n, e1, x, e):
        rubi.append(2094)
        return Dist(b/(g*n*n1*(-a*d + b*c)), Subst(Int(x**p, x), x, log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)), x)
    rule2094 = ReplacementRule(pattern2094, replacement2094)
    pattern2095 = Pattern(Integral(log(v_)*log(u_**n_*WC('e', S(1)))**WC('p', S(1))/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1217, cons1211, cons71, cons13, cons163)
    def replacement2095(v, p, u, b, d, c, a, n, x, e):
        rubi.append(2095)
        return Dist(n*p, Int(PolyLog(S(2), Together(-v + S(1)))*log(e*u**n)**(p + S(-1))/((a + b*x)*(c + d*x)), x), x) - Simp(PolyLog(S(2), Together(-v + S(1)))*log(e*u**n)**p/(-a*d + b*c), x)
    rule2095 = ReplacementRule(pattern2095, replacement2095)
    pattern2096 = Pattern(Integral(log(u_)**WC('p', S(1))*log(v_)/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1217, cons1211, cons71, cons13, cons163)
    def replacement2096(v, p, u, b, d, c, a, x):
        rubi.append(2096)
        return Dist(p, Int(PolyLog(S(2), Together(-v + S(1)))*log(u)**(p + S(-1))/((a + b*x)*(c + d*x)), x), x) - Simp(PolyLog(S(2), Together(-v + S(1)))*log(u)**p/(-a*d + b*c), x)
    rule2096 = ReplacementRule(pattern2096, replacement2096)
    def With2097(v, p, u, b, d, c, a, n, x, e):
        f = (-v + S(1))/u
        rubi.append(2097)
        return Dist(f/(n*(p + S(1))), Int(log(e*u**n)**(p + S(1))/((c + d*x)*(-a*f - b*f + c + d)), x), x) + Simp(log(v)*log(e*u**n)**(p + S(1))/(n*(p + S(1))*(-a*d + b*c)), x)
    pattern2097 = Pattern(Integral(log(v_)*log(u_**n_*WC('e', S(1)))**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1217, cons1211, cons71, cons13, cons137)
    rule2097 = ReplacementRule(pattern2097, With2097)
    def With2098(v, p, u, b, d, c, a, x):
        f = (-v + S(1))/u
        rubi.append(2098)
        return Dist(f/(p + S(1)), Int(log(u)**(p + S(1))/((c + d*x)*(-a*f - b*f + c + d)), x), x) + Simp(log(u)**(p + S(1))*log(v)/((p + S(1))*(-a*d + b*c)), x)
    pattern2098 = Pattern(Integral(log(u_)**p_*log(v_)/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1217, cons1211, cons71, cons13, cons137)
    rule2098 = ReplacementRule(pattern2098, With2098)
    pattern2099 = Pattern(Integral(log(v_)*log(u_**n_*WC('e', S(1)))**WC('p', S(1))/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1218, cons1211, cons71, cons13, cons163)
    def replacement2099(v, p, u, b, d, c, a, n, x, e):
        rubi.append(2099)
        return -Dist(n*p, Int(PolyLog(S(2), Together(-v + S(1)))*log(e*u**n)**(p + S(-1))/((a + b*x)*(c + d*x)), x), x) + Simp(PolyLog(S(2), Together(-v + S(1)))*log(e*u**n)**p/(-a*d + b*c), x)
    rule2099 = ReplacementRule(pattern2099, replacement2099)
    pattern2100 = Pattern(Integral(log(u_)**WC('p', S(1))*log(v_)/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1218, cons1211, cons71, cons13, cons163)
    def replacement2100(v, p, u, b, d, c, a, x):
        rubi.append(2100)
        return -Dist(p, Int(PolyLog(S(2), Together(-v + S(1)))*log(u)**(p + S(-1))/((a + b*x)*(c + d*x)), x), x) + Simp(PolyLog(S(2), Together(-v + S(1)))*log(u)**p/(-a*d + b*c), x)
    rule2100 = ReplacementRule(pattern2100, replacement2100)
    def With2101(v, p, u, b, d, c, a, n, x, e):
        f = u*(-v + S(1))
        rubi.append(2101)
        return -Dist(f/(n*(p + S(1))), Int(log(e*u**n)**(p + S(1))/((a + b*x)*(a + b - c*f - d*f)), x), x) + Simp(log(v)*log(e*u**n)**(p + S(1))/(n*(p + S(1))*(-a*d + b*c)), x)
    pattern2101 = Pattern(Integral(log(v_)*log(u_**n_*WC('e', S(1)))**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1218, cons1211, cons71, cons13, cons137)
    rule2101 = ReplacementRule(pattern2101, With2101)
    def With2102(v, p, u, b, d, c, a, x):
        f = u*(-v + S(1))
        rubi.append(2102)
        return -Dist(f/(p + S(1)), Int(log(u)**(p + S(1))/((a + b*x)*(a + b - c*f - d*f)), x), x) + Simp(log(u)**(p + S(1))*log(v)/((p + S(1))*(-a*d + b*c)), x)
    pattern2102 = Pattern(Integral(log(u_)**p_*log(v_)/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1218, cons1211, cons71, cons13, cons137)
    rule2102 = ReplacementRule(pattern2102, With2102)
    pattern2103 = Pattern(Integral(PolyLog(q_, v_)*log(u_**n_*WC('e', S(1)))**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons50, cons1219, cons1211, cons71, cons13, cons146)
    def replacement2103(v, p, u, b, d, c, a, n, x, q, e):
        rubi.append(2103)
        return -Dist(n*p, Int(PolyLog(q + S(1), v)*log(e*u**n)**(p + S(-1))/((a + b*x)*(c + d*x)), x), x) + Simp(PolyLog(q + S(1), v)*log(e*u**n)**p/(-a*d + b*c), x)
    rule2103 = ReplacementRule(pattern2103, replacement2103)
    pattern2104 = Pattern(Integral(PolyLog(q_, v_)*log(u_)**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons50, cons1219, cons1211, cons71, cons13, cons146)
    def replacement2104(v, p, u, b, d, c, a, x, q):
        rubi.append(2104)
        return -Dist(p, Int(PolyLog(q + S(1), v)*log(u)**(p + S(-1))/((a + b*x)*(c + d*x)), x), x) + Simp(PolyLog(q + S(1), v)*log(u)**p/(-a*d + b*c), x)
    rule2104 = ReplacementRule(pattern2104, replacement2104)
    pattern2105 = Pattern(Integral(PolyLog(q_, v_)*log(u_**n_*WC('e', S(1)))**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons50, cons1219, cons1211, cons71, cons13, cons137)
    def replacement2105(v, p, u, b, d, c, a, n, x, q, e):
        rubi.append(2105)
        return -Dist(S(1)/(n*(p + S(1))), Int(PolyLog(q + S(-1), v)*log(e*u**n)**(p + S(1))/((a + b*x)*(c + d*x)), x), x) + Simp(PolyLog(q, v)*log(e*u**n)**(p + S(1))/(n*(p + S(1))*(-a*d + b*c)), x)
    rule2105 = ReplacementRule(pattern2105, replacement2105)
    pattern2106 = Pattern(Integral(PolyLog(q_, v_)*log(u_)**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons50, cons1219, cons1211, cons71, cons13, cons137)
    def replacement2106(v, p, u, b, d, c, a, x, q):
        rubi.append(2106)
        return -Dist(S(1)/(p + S(1)), Int(PolyLog(q + S(-1), v)*log(u)**(p + S(1))/((a + b*x)*(c + d*x)), x), x) + Simp(PolyLog(q, v)*log(u)**(p + S(1))/((p + S(1))*(-a*d + b*c)), x)
    rule2106 = ReplacementRule(pattern2106, replacement2106)
    pattern2107 = Pattern(Integral(PolyLog(q_, v_)*log(u_**n_*WC('e', S(1)))**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons50, cons1220, cons1211, cons71, cons13, cons146)
    def replacement2107(v, p, u, b, d, c, a, n, x, q, e):
        rubi.append(2107)
        return Dist(n*p, Int(PolyLog(q + S(1), v)*log(e*u**n)**(p + S(-1))/((a + b*x)*(c + d*x)), x), x) - Simp(PolyLog(q + S(1), v)*log(e*u**n)**p/(-a*d + b*c), x)
    rule2107 = ReplacementRule(pattern2107, replacement2107)
    pattern2108 = Pattern(Integral(PolyLog(q_, v_)*log(u_)**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons50, cons1220, cons1211, cons71, cons13, cons146)
    def replacement2108(v, p, u, b, d, c, a, x, q):
        rubi.append(2108)
        return Dist(p, Int(PolyLog(q + S(1), v)*log(u)**(p + S(-1))/((a + b*x)*(c + d*x)), x), x) - Simp(PolyLog(q + S(1), v)*log(u)**p/(-a*d + b*c), x)
    rule2108 = ReplacementRule(pattern2108, replacement2108)
    pattern2109 = Pattern(Integral(PolyLog(q_, v_)*log(u_**n_*WC('e', S(1)))**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons50, cons1220, cons1211, cons71, cons13, cons137)
    def replacement2109(v, p, u, b, d, c, a, n, x, q, e):
        rubi.append(2109)
        return Dist(S(1)/(n*(p + S(1))), Int(PolyLog(q + S(-1), v)*log(e*u**n)**(p + S(1))/((a + b*x)*(c + d*x)), x), x) + Simp(PolyLog(q, v)*log(e*u**n)**(p + S(1))/(n*(p + S(1))*(-a*d + b*c)), x)
    rule2109 = ReplacementRule(pattern2109, replacement2109)
    pattern2110 = Pattern(Integral(PolyLog(q_, v_)*log(u_)**p_/((x_*WC('b', S(1)) + WC('a', S(0)))*(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons50, cons1220, cons1211, cons71, cons13, cons137)
    def replacement2110(v, p, u, b, d, c, a, x, q):
        rubi.append(2110)
        return Dist(S(1)/(p + S(1)), Int(PolyLog(q + S(-1), v)*log(u)**(p + S(1))/((a + b*x)*(c + d*x)), x), x) + Simp(PolyLog(q, v)*log(u)**(p + S(1))/((p + S(1))*(-a*d + b*c)), x)
    rule2110 = ReplacementRule(pattern2110, replacement2110)
    pattern2111 = Pattern(Integral(WC('u', S(1))*log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/(x_**S(2)*WC('h', S(1)) + x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons4, cons5, cons652, cons1204, cons1203, cons71, cons1221, cons1222)
    def replacement2111(p, u, n1, b, f, g, n2, d, a, c, n, e1, x, h, e):
        rubi.append(2111)
        return Dist(b*d/h, Int(u*log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/((a + b*x)*(c + d*x)), x), x)
    rule2111 = ReplacementRule(pattern2111, replacement2111)
    pattern2112 = Pattern(Integral(WC('u', S(1))*log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1))/(x_**S(2)*WC('h', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons209, cons4, cons5, cons652, cons1204, cons1203, cons71, cons1221, cons70)
    def replacement2112(p, u, n1, b, f, n2, d, a, c, n, e1, x, h, e):
        rubi.append(2112)
        return Dist(b*d/h, Int(u*log(e*(e1*(a + b*x)**n1*(c + d*x)**(-n1))**n)**p/((a + b*x)*(c + d*x)), x), x)
    rule2112 = ReplacementRule(pattern2112, replacement2112)
    def With2113(n1, b, g, n2, f, d, a, c, n, e1, x, h, e):
        u = IntHide(S(1)/(f + g*x + h*x**S(2)), x)
        rubi.append(2113)
        return -Dist(n*(-a*d + b*c), Int(u/((a + b*x)*(c + d*x)), x), x) + Simp(u*log(e*(e1*(a + b*x)**n1*(c + d*x)**n2)**n), x)
    pattern2113 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))/(f_ + x_**S(2)*WC('h', S(1)) + x_*WC('g', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons652, cons125, cons208, cons209, cons4, cons1204, cons1203)
    rule2113 = ReplacementRule(pattern2113, With2113)
    def With2114(n1, b, n2, f, d, a, c, n, e1, x, h, e):
        u = IntHide(S(1)/(f + h*x**S(2)), x)
        rubi.append(2114)
        return -Dist(n*(-a*d + b*c), Int(u/((a + b*x)*(c + d*x)), x), x) + Simp(u*log(e*(e1*(a + b*x)**n1*(c + d*x)**n2)**n), x)
    pattern2114 = Pattern(Integral(log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))/(f_ + x_**S(2)*WC('h', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons652, cons125, cons209, cons4, cons1204, cons1203)
    rule2114 = ReplacementRule(pattern2114, With2114)
    def With2115(p, RFx, n1, b, n2, d, a, c, n, e1, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(log(e*(e1*(a + b*x)**n1*(c + d*x)**n2)**n)**p, RFx, x)
        if SumQ(u):
            return True
        return False
    pattern2115 = Pattern(Integral(RFx_*log(((x_*WC('b', S(1)) + WC('a', S(0)))**WC('n1', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**n2_*WC('e1', S(1)))**WC('n', S(1))*WC('e', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons652, cons1204, cons1203, cons1198, cons128, CustomConstraint(With2115))
    def replacement2115(p, RFx, n1, b, n2, d, a, c, n, e1, x, e):

        u = ExpandIntegrand(log(e*(e1*(a + b*x)**n1*(c + d*x)**n2)**n)**p, RFx, x)
        rubi.append(2115)
        return Int(u, x)
    rule2115 = ReplacementRule(pattern2115, replacement2115)
    def With2116(v, x, p, u):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        lst = QuotientOfLinearsParts(v, x)
        if Not(And(OneQ(p), ZeroQ(Part(lst, S(3))))):
            return True
        return False
    pattern2116 = Pattern(Integral(WC('u', S(1))*log(v_)**WC('p', S(1)), x_), cons5, cons1223, cons1224, CustomConstraint(With2116))
    def replacement2116(v, x, p, u):

        lst = QuotientOfLinearsParts(v, x)
        rubi.append(2116)
        return Int(u*log((x*Part(lst, S(2)) + Part(lst, S(1)))/(x*Part(lst, S(4)) + Part(lst, S(3))))**p, x)
    rule2116 = ReplacementRule(pattern2116, replacement2116)
    pattern2117 = Pattern(Integral(log((x_**n_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*WC('c', S(1))), x_), cons2, cons3, cons7, cons4, cons5, cons806)
    def replacement2117(p, b, c, a, n, x):
        rubi.append(2117)
        return -Dist(b*n*p, Int(x**n/(a + b*x**n), x), x) + Simp(x*log(c*(a + b*x**n)**p), x)
    rule2117 = ReplacementRule(pattern2117, replacement2117)
    pattern2118 = Pattern(Integral(log(v_**WC('p', S(1))*WC('c', S(1))), x_), cons7, cons5, cons840, cons1225)
    def replacement2118(v, c, p, x):
        rubi.append(2118)
        return Int(log(c*ExpandToSum(v, x)**p), x)
    rule2118 = ReplacementRule(pattern2118, replacement2118)
    pattern2119 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log((x_**n_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*WC('c', S(1))))/(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons1226)
    def replacement2119(p, f, b, g, d, a, c, n, x, e):
        rubi.append(2119)
        return -Dist(b*e*n*p/g, Int(x**(n + S(-1))*log(f + g*x)/(d + e*x**n), x), x) + Simp((a + b*log(c*(d + e*x**n)**p))*log(f + g*x)/g, x)
    rule2119 = ReplacementRule(pattern2119, replacement2119)
    pattern2120 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log((x_**n_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons66)
    def replacement2120(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2120)
        return -Dist(b*e*n*p/(g*(m + S(1))), Int(x**(n + S(-1))*(f + g*x)**(m + S(1))/(d + e*x**n), x), x) + Simp((a + b*log(c*(d + e*x**n)**p))*(f + g*x)**(m + S(1))/(g*(m + S(1))), x)
    rule2120 = ReplacementRule(pattern2120, replacement2120)
    pattern2121 = Pattern(Integral(u_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(v_**WC('p', S(1))*WC('c', S(1)))), x_), cons2, cons3, cons7, cons21, cons5, cons68, cons840, cons1125)
    def replacement2121(v, p, u, m, b, a, c, x):
        rubi.append(2121)
        return Int((a + b*log(c*ExpandToSum(v, x)**p))*ExpandToSum(u, x)**m, x)
    rule2121 = ReplacementRule(pattern2121, replacement2121)
    def With2122(p, m, f, g, b, d, c, a, n, x, e):
        w = IntHide(asin(f + g*x)**m, x)
        rubi.append(2122)
        return -Dist(b*e*n*p, Int(SimplifyIntegrand(w*x**(n + S(-1))/(d + e*x**n), x), x), x) + Dist(a + b*log(c*(d + e*x**n)**p), w, x)
    pattern2122 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log((x_**n_*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*WC('c', S(1))))*asin(x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons62)
    rule2122 = ReplacementRule(pattern2122, With2122)
    def With2123(p, f, b, g, d, a, c, x, e):
        u = IntHide(S(1)/(f + g*x**S(2)), x)
        rubi.append(2123)
        return -Dist(S(2)*b*e*p, Int(u*x/(d + e*x**S(2)), x), x) + Simp(u*(a + b*log(c*(d + e*x**S(2))**p)), x)
    pattern2123 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log((x_**S(2)*WC('e', S(1)) + WC('d', S(0)))**WC('p', S(1))*WC('c', S(1))))/(x_**S(2)*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons1227)
    rule2123 = ReplacementRule(pattern2123, With2123)
    pattern2124 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons148)
    def replacement2124(p, b, d, a, c, n, x, e):
        rubi.append(2124)
        return -Dist(S(2)*b*e*n*p, Int(x**S(2)*(a + b*log(c*(d + e*x**S(2))**p))**(n + S(-1))/(d + e*x**S(2)), x), x) + Simp(x*(a + b*log(c*(d + e*x**S(2))**p))**n, x)
    rule2124 = ReplacementRule(pattern2124, replacement2124)
    pattern2125 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons148, cons1228)
    def replacement2125(p, m, b, d, a, c, n, x, e):
        rubi.append(2125)
        return Dist(S(1)/2, Subst(Int(x**(m/S(2) + S(-1)/2)*(a + b*log(c*(d + e*x)**p))**n, x), x, x**S(2)), x)
    rule2125 = ReplacementRule(pattern2125, replacement2125)
    pattern2126 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log((d_ + x_**S(2)*WC('e', S(1)))**WC('p', S(1))*WC('c', S(1))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons148, cons1229)
    def replacement2126(p, m, b, d, a, c, n, x, e):
        rubi.append(2126)
        return -Dist(S(2)*b*e*n*p/(m + S(1)), Int(x**(m + S(2))*(a + b*log(c*(d + e*x**S(2))**p))**(n + S(-1))/(d + e*x**S(2)), x), x) + Simp(x**(m + S(1))*(a + b*log(c*(d + e*x**S(2))**p))**n/(m + S(1)), x)
    rule2126 = ReplacementRule(pattern2126, replacement2126)
    def With2127(v, x, u):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        try:
            w = DerivativeDivides(v, u*(-v + S(1)), x)
            res = Not(FalseQ(w))
        except (TypeError, AttributeError):
            return False
        if res:
            return True
        return False
    pattern2127 = Pattern(Integral(u_*log(v_), x_), CustomConstraint(With2127))
    def replacement2127(v, x, u):

        w = DerivativeDivides(v, u*(-v + S(1)), x)
        rubi.append(2127)
        return Simp(w*PolyLog(S(2), Together(-v + S(1))), x)
    rule2127 = ReplacementRule(pattern2127, replacement2127)
    def With2128(v, w, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        try:
            z = DerivativeDivides(v, w*(-v + S(1)), x)
            res = Not(FalseQ(z))
        except (TypeError, AttributeError):
            return False
        if res:
            return True
        return False
    pattern2128 = Pattern(Integral(w_*(WC('a', S(0)) + WC('b', S(1))*log(u_))*log(v_), x_), cons2, cons3, cons1230, CustomConstraint(With2128))
    def replacement2128(v, w, u, b, a, x):

        z = DerivativeDivides(v, w*(-v + S(1)), x)
        rubi.append(2128)
        return -Dist(b, Int(SimplifyIntegrand(z*D(u, x)*PolyLog(S(2), Together(-v + S(1)))/u, x), x), x) + Simp(z*(a + b*log(u))*PolyLog(S(2), Together(-v + S(1))), x)
    rule2128 = ReplacementRule(pattern2128, replacement2128)
    pattern2129 = Pattern(Integral(log((a_ + (x_*WC('e', S(1)) + WC('d', S(0)))**n_*WC('b', S(1)))**WC('p', S(1))*WC('c', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons87, cons463)
    def replacement2129(p, b, d, c, a, n, x, e):
        rubi.append(2129)
        return -Dist(b*n*p, Int(S(1)/(a*(d + e*x)**(-n) + b), x), x) + Simp((d + e*x)*log(c*(a + b*(d + e*x)**n)**p)/e, x)
    rule2129 = ReplacementRule(pattern2129, replacement2129)
    pattern2130 = Pattern(Integral(log((a_ + (x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1))*WC('b', S(1)))**WC('p', S(1))*WC('c', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1231)
    def replacement2130(p, b, d, c, n, a, x, e):
        rubi.append(2130)
        return Dist(a*n*p, Int(S(1)/(a + b*(d + e*x)**n), x), x) + Simp((d + e*x)*log(c*(a + b*(d + e*x)**n)**p)/e, x) - Simp(n*p*x, x)
    rule2130 = ReplacementRule(pattern2130, replacement2130)
    pattern2131 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log((d_ + WC('e', S(1))/(x_*WC('g', S(1)) + WC('f', S(0))))**WC('p', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons148)
    def replacement2131(p, f, g, b, d, a, c, n, x, e):
        rubi.append(2131)
        return -Dist(b*e*n*p/(d*g), Subst(Int((a + b*log(c*(d + e*x)**p))**(n + S(-1))/x, x), x, S(1)/(f + g*x)), x) + Simp((a + b*log(c*(d + e/(f + g*x))**p))**n*(d*(f + g*x) + e)/(d*g), x)
    rule2131 = ReplacementRule(pattern2131, replacement2131)
    pattern2132 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(RFx_**WC('p', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons5, cons1198, cons148)
    def replacement2132(p, RFx, b, a, c, n, x):
        rubi.append(2132)
        return -Dist(b*n*p, Int(SimplifyIntegrand(x*(a + b*log(RFx**p*c))**(n + S(-1))*D(RFx, x)/RFx, x), x), x) + Simp(x*(a + b*log(RFx**p*c))**n, x)
    rule2132 = ReplacementRule(pattern2132, replacement2132)
    pattern2133 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(RFx_**WC('p', S(1))*WC('c', S(1))))**WC('n', S(1))/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons1198, cons148)
    def replacement2133(p, RFx, b, d, a, c, n, x, e):
        rubi.append(2133)
        return -Dist(b*n*p/e, Int((a + b*log(RFx**p*c))**(n + S(-1))*D(RFx, x)*log(d + e*x)/RFx, x), x) + Simp((a + b*log(RFx**p*c))**n*log(d + e*x)/e, x)
    rule2133 = ReplacementRule(pattern2133, replacement2133)
    pattern2134 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*log(RFx_**WC('p', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons1198, cons148, cons1232, cons66)
    def replacement2134(p, RFx, m, b, d, a, c, n, x, e):
        rubi.append(2134)
        return -Dist(b*n*p/(e*(m + S(1))), Int(SimplifyIntegrand((a + b*log(RFx**p*c))**(n + S(-1))*(d + e*x)**(m + S(1))*D(RFx, x)/RFx, x), x), x) + Simp((a + b*log(RFx**p*c))**n*(d + e*x)**(m + S(1))/(e*(m + S(1))), x)
    rule2134 = ReplacementRule(pattern2134, replacement2134)
    def With2135(RFx, d, c, n, x, e):
        u = IntHide(S(1)/(d + e*x**S(2)), x)
        rubi.append(2135)
        return -Dist(n, Int(SimplifyIntegrand(u*D(RFx, x)/RFx, x), x), x) + Simp(u*log(RFx**n*c), x)
    pattern2135 = Pattern(Integral(log(RFx_**WC('n', S(1))*WC('c', S(1)))/(d_ + x_**S(2)*WC('e', S(1))), x_), cons7, cons27, cons48, cons4, cons1198, cons1233)
    rule2135 = ReplacementRule(pattern2135, With2135)
    def With2136(Px, c, n, Qx, x):
        u = IntHide(S(1)/Qx, x)
        rubi.append(2136)
        return -Dist(n, Int(SimplifyIntegrand(u*D(Px, x)/Px, x), x), x) + Simp(u*log(Px**n*c), x)
    pattern2136 = Pattern(Integral(log(Px_**WC('n', S(1))*WC('c', S(1)))/Qx_, x_), cons7, cons4, cons1234, cons1235)
    rule2136 = ReplacementRule(pattern2136, With2136)
    def With2137(p, RFx, b, a, c, n, RGx, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand((a + b*log(RFx**p*c))**n, RGx, x)
        if SumQ(u):
            return True
        return False
    pattern2137 = Pattern(Integral(RGx_*(WC('a', S(0)) + WC('b', S(1))*log(RFx_**WC('p', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons5, cons1198, cons1236, cons148, CustomConstraint(With2137))
    def replacement2137(p, RFx, b, a, c, n, RGx, x):

        u = ExpandIntegrand((a + b*log(RFx**p*c))**n, RGx, x)
        rubi.append(2137)
        return Int(u, x)
    rule2137 = ReplacementRule(pattern2137, replacement2137)
    def With2138(p, RFx, b, a, c, n, RGx, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand(RGx*(a + b*log(RFx**p*c))**n, x)
        if SumQ(u):
            return True
        return False
    pattern2138 = Pattern(Integral(RGx_*(WC('a', S(0)) + WC('b', S(1))*log(RFx_**WC('p', S(1))*WC('c', S(1))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons5, cons1198, cons1236, cons148, CustomConstraint(With2138))
    def replacement2138(p, RFx, b, a, c, n, RGx, x):

        u = ExpandIntegrand(RGx*(a + b*log(RFx**p*c))**n, x)
        rubi.append(2138)
        return Int(u, x)
    rule2138 = ReplacementRule(pattern2138, replacement2138)
    def With2139(RFx, u, b, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        try:
            lst = SubstForFractionalPowerOfLinear(RFx*(a + b*log(u)), x)
            res = Not(FalseQ(lst))
        except (TypeError, AttributeError):
            return False
        if res:
            return True
        return False
    pattern2139 = Pattern(Integral(RFx_*(WC('a', S(0)) + WC('b', S(1))*log(u_)), x_), cons2, cons3, cons1198, CustomConstraint(With2139))
    def replacement2139(RFx, u, b, a, x):

        lst = SubstForFractionalPowerOfLinear(RFx*(a + b*log(u)), x)
        rubi.append(2139)
        return Dist(Part(lst, S(2))*Part(lst, S(4)), Subst(Int(Part(lst, S(1)), x), x, Part(lst, S(3))**(S(1)/Part(lst, S(2)))), x)
    rule2139 = ReplacementRule(pattern2139, replacement2139)
    pattern2140 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*log((F_**((x_*WC('b', S(1)) + WC('a', S(0)))*WC('c', S(1))))**WC('n', S(1))*WC('e', S(1)) + S(1)), x_), cons1099, cons2, cons3, cons7, cons48, cons125, cons208, cons4, cons31, cons168)
    def replacement2140(m, f, b, g, c, n, a, x, F, e):
        rubi.append(2140)
        return Dist(g*m/(b*c*n*log(F)), Int((f + g*x)**(m + S(-1))*PolyLog(S(2), -e*(F**(c*(a + b*x)))**n), x), x) - Simp((f + g*x)**m*PolyLog(S(2), -e*(F**(c*(a + b*x)))**n)/(b*c*n*log(F)), x)
    rule2140 = ReplacementRule(pattern2140, replacement2140)
    pattern2141 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**WC('m', S(1))*log(d_ + (F_**((x_*WC('b', S(1)) + WC('a', S(0)))*WC('c', S(1))))**WC('n', S(1))*WC('e', S(1))), x_), cons1099, cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons31, cons168, cons1237)
    def replacement2141(m, f, b, g, d, c, n, a, x, F, e):
        rubi.append(2141)
        return Int((f + g*x)**m*log(S(1) + e*(F**(c*(a + b*x)))**n/d), x) - Simp((f + g*x)**(m + S(1))*log(S(1) + e*(F**(c*(a + b*x)))**n/d)/(g*(m + S(1))), x) + Simp((f + g*x)**(m + S(1))*log(d + e*(F**(c*(a + b*x)))**n)/(g*(m + S(1))), x)
    rule2141 = ReplacementRule(pattern2141, replacement2141)
    pattern2142 = Pattern(Integral(log(x_*WC('e', S(1)) + sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))*WC('f', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1055)
    def replacement2142(f, b, d, a, c, x, e):
        rubi.append(2142)
        return Dist(f**S(2)*(-S(4)*a*c + b**S(2))/S(2), Int(x/(-f*sqrt(a + b*x + c*x**S(2))*(-S(2)*a*e + b*d + x*(-b*e + S(2)*c*d)) + (-b*f**S(2) + S(2)*d*e)*(a + b*x + c*x**S(2))), x), x) + Simp(x*log(d + e*x + f*sqrt(a + b*x + c*x**S(2))), x)
    rule2142 = ReplacementRule(pattern2142, replacement2142)
    pattern2143 = Pattern(Integral(log(x_*WC('e', S(1)) + sqrt(x_**S(2)*WC('c', S(1)) + WC('a', S(0)))*WC('f', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons1055)
    def replacement2143(f, d, a, c, x, e):
        rubi.append(2143)
        return -Dist(a*c*f**S(2), Int(x/(d*e*(a + c*x**S(2)) + f*sqrt(a + c*x**S(2))*(a*e - c*d*x)), x), x) + Simp(x*log(d + e*x + f*sqrt(a + c*x**S(2))), x)
    rule2143 = ReplacementRule(pattern2143, replacement2143)
    pattern2144 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*log(x_*WC('e', S(1)) + sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))*WC('f', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons1055, cons66, cons515)
    def replacement2144(m, f, b, g, d, a, c, x, e):
        rubi.append(2144)
        return Dist(f**S(2)*(-S(4)*a*c + b**S(2))/(S(2)*g*(m + S(1))), Int((g*x)**(m + S(1))/(-f*sqrt(a + b*x + c*x**S(2))*(-S(2)*a*e + b*d + x*(-b*e + S(2)*c*d)) + (-b*f**S(2) + S(2)*d*e)*(a + b*x + c*x**S(2))), x), x) + Simp((g*x)**(m + S(1))*log(d + e*x + f*sqrt(a + b*x + c*x**S(2)))/(g*(m + S(1))), x)
    rule2144 = ReplacementRule(pattern2144, replacement2144)
    pattern2145 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*log(x_*WC('e', S(1)) + sqrt(x_**S(2)*WC('c', S(1)) + WC('a', S(0)))*WC('f', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons1055, cons66, cons515)
    def replacement2145(m, f, g, d, a, c, x, e):
        rubi.append(2145)
        return -Dist(a*c*f**S(2)/(g*(m + S(1))), Int((g*x)**(m + S(1))/(d*e*(a + c*x**S(2)) + f*sqrt(a + c*x**S(2))*(a*e - c*d*x)), x), x) + Simp((g*x)**(m + S(1))*log(d + e*x + f*sqrt(a + c*x**S(2)))/(g*(m + S(1))), x)
    rule2145 = ReplacementRule(pattern2145, replacement2145)
    pattern2146 = Pattern(Integral(WC('v', S(1))*log(sqrt(u_)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons27, cons48, cons125, cons816, cons817, cons1238)
    def replacement2146(v, u, f, d, x, e):
        rubi.append(2146)
        return Int(v*log(d + e*x + f*sqrt(ExpandToSum(u, x))), x)
    rule2146 = ReplacementRule(pattern2146, replacement2146)
    pattern2147 = Pattern(Integral(log(u_), x_), cons1230)
    def replacement2147(x, u):
        rubi.append(2147)
        return -Int(SimplifyIntegrand(x*D(u, x)/u, x), x) + Simp(x*log(u), x)
    rule2147 = ReplacementRule(pattern2147, replacement2147)
    pattern2148 = Pattern(Integral(log(u_)/(x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons1239, cons1240)
    def replacement2148(x, a, b, u):
        rubi.append(2148)
        return -Dist(S(1)/b, Int(SimplifyIntegrand(D(u, x)*log(a + b*x)/u, x), x), x) + Simp(log(u)*log(a + b*x)/b, x)
    rule2148 = ReplacementRule(pattern2148, replacement2148)
    pattern2149 = Pattern(Integral((x_*WC('b', S(1)) + WC('a', S(0)))**WC('m', S(1))*log(u_), x_), cons2, cons3, cons21, cons1230, cons66)
    def replacement2149(u, m, b, a, x):
        rubi.append(2149)
        return -Dist(S(1)/(b*(m + S(1))), Int(SimplifyIntegrand((a + b*x)**(m + S(1))*D(u, x)/u, x), x), x) + Simp((a + b*x)**(m + S(1))*log(u)/(b*(m + S(1))), x)
    rule2149 = ReplacementRule(pattern2149, replacement2149)
    def With2150(x, Qx, u):
        v = IntHide(S(1)/Qx, x)
        rubi.append(2150)
        return -Int(SimplifyIntegrand(v*D(u, x)/u, x), x) + Simp(v*log(u), x)
    pattern2150 = Pattern(Integral(log(u_)/Qx_, x_), cons1241, cons1230)
    rule2150 = ReplacementRule(pattern2150, With2150)
    pattern2151 = Pattern(Integral(u_**(x_*WC('a', S(1)))*log(u_), x_), cons2, cons1230)
    def replacement2151(x, a, u):
        rubi.append(2151)
        return -Int(SimplifyIntegrand(u**(a*x + S(-1))*x*D(u, x), x), x) + Simp(u**(a*x)/a, x)
    rule2151 = ReplacementRule(pattern2151, replacement2151)
    def With2152(v, x, u):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        w = IntHide(v, x)
        if InverseFunctionFreeQ(w, x):
            return True
        return False
    pattern2152 = Pattern(Integral(v_*log(u_), x_), cons1230, CustomConstraint(With2152))
    def replacement2152(v, x, u):

        w = IntHide(v, x)
        rubi.append(2152)
        return Dist(log(u), w, x) - Int(SimplifyIntegrand(w*D(u, x)/u, x), x)
    rule2152 = ReplacementRule(pattern2152, replacement2152)
    pattern2153 = Pattern(Integral(log(v_)*log(w_), x_), cons1242, cons1243)
    def replacement2153(v, w, x):
        rubi.append(2153)
        return -Int(SimplifyIntegrand(x*D(v, x)*log(w)/v, x), x) - Int(SimplifyIntegrand(x*D(w, x)*log(v)/w, x), x) + Simp(x*log(v)*log(w), x)
    rule2153 = ReplacementRule(pattern2153, replacement2153)
    def With2154(v, w, u, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        z = IntHide(u, x)
        if InverseFunctionFreeQ(z, x):
            return True
        return False
    pattern2154 = Pattern(Integral(u_*log(v_)*log(w_), x_), cons1242, cons1243, CustomConstraint(With2154))
    def replacement2154(v, w, u, x):

        z = IntHide(u, x)
        rubi.append(2154)
        return Dist(log(v)*log(w), z, x) - Int(SimplifyIntegrand(z*D(v, x)*log(w)/v, x), x) - Int(SimplifyIntegrand(z*D(w, x)*log(v)/w, x), x)
    rule2154 = ReplacementRule(pattern2154, replacement2154)
    pattern2155 = Pattern(Integral(log(WC('a', S(1))*log(x_**WC('n', S(1))*WC('b', S(1)))**WC('p', S(1))), x_), cons2, cons3, cons4, cons5, cons1244)
    def replacement2155(p, b, a, n, x):
        rubi.append(2155)
        return -Dist(n*p, Int(S(1)/log(b*x**n), x), x) + Simp(x*log(a*log(b*x**n)**p), x)
    rule2155 = ReplacementRule(pattern2155, replacement2155)
    pattern2156 = Pattern(Integral(log(WC('a', S(1))*log(x_**WC('n', S(1))*WC('b', S(1)))**WC('p', S(1)))/x_, x_), cons2, cons3, cons4, cons5, cons1244)
    def replacement2156(p, b, a, n, x):
        rubi.append(2156)
        return Simp((-p + log(a*log(b*x**n)**p))*log(b*x**n)/n, x)
    rule2156 = ReplacementRule(pattern2156, replacement2156)
    pattern2157 = Pattern(Integral(x_**WC('m', S(1))*log(WC('a', S(1))*log(x_**WC('n', S(1))*WC('b', S(1)))**WC('p', S(1))), x_), cons2, cons3, cons21, cons4, cons5, cons66)
    def replacement2157(p, m, b, a, n, x):
        rubi.append(2157)
        return -Dist(n*p/(m + S(1)), Int(x**m/log(b*x**n), x), x) + Simp(x**(m + S(1))*log(a*log(b*x**n)**p)/(m + S(1)), x)
    rule2157 = ReplacementRule(pattern2157, replacement2157)
    pattern2158 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*log(x_*WC('d', S(1)) + WC('c', S(0))))/sqrt(a_ + WC('b', S(1))*log(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons34, cons35, cons1245)
    def replacement2158(B, b, d, c, a, x, A):
        rubi.append(2158)
        return Dist(B/b, Int(sqrt(a + b*log(c + d*x)), x), x) + Dist((A*b - B*a)/b, Int(S(1)/sqrt(a + b*log(c + d*x)), x), x)
    rule2158 = ReplacementRule(pattern2158, replacement2158)
    pattern2159 = Pattern(Integral(f_**(WC('a', S(1))*log(u_)), x_), cons2, cons125, cons1246)
    def replacement2159(x, a, f, u):
        rubi.append(2159)
        return Int(u**(a*log(f)), x)
    rule2159 = ReplacementRule(pattern2159, replacement2159)
    def With2160(x, u):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        try:
            lst = FunctionOfLog(u*x, x)
            res = Not(FalseQ(lst))
        except (TypeError, AttributeError):
            return False
        if res:
            return True
        return False
    pattern2160 = Pattern(Integral(u_, x_), cons1247, CustomConstraint(With2160))
    def replacement2160(x, u):

        lst = FunctionOfLog(u*x, x)
        rubi.append(2160)
        return Dist(S(1)/Part(lst, S(3)), Subst(Int(Part(lst, S(1)), x), x, log(Part(lst, S(2)))), x)
    rule2160 = ReplacementRule(pattern2160, replacement2160)
    pattern2161 = Pattern(Integral(WC('u', S(1))*log(Gamma(v_)), x_))
    def replacement2161(v, x, u):
        rubi.append(2161)
        return Dist(-LogGamma(v) + log(Gamma(v)), Int(u, x), x) + Int(u*LogGamma(v), x)
    rule2161 = ReplacementRule(pattern2161, replacement2161)
    pattern2162 = Pattern(Integral((w_*WC('a', S(1)) + w_*WC('b', S(1))*log(v_)**WC('n', S(1)))**WC('p', S(1))*WC('u', S(1)), x_), cons2, cons3, cons4, cons38)
    def replacement2162(v, w, p, u, b, a, n, x):
        rubi.append(2162)
        return Int(u*w**p*(a + b*log(v)**n)**p, x)
    rule2162 = ReplacementRule(pattern2162, replacement2162)
    pattern2163 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*log(((x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('c', S(1))))**n_*WC('u', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons50, cons1248)
    def replacement2163(p, u, f, b, d, a, c, n, x, q, e):
        rubi.append(2163)
        return Int(u*(a + b*log(c*(d*(e + f*x)**p)**q))**n, x)
    rule2163 = ReplacementRule(pattern2163, replacement2163)
    return [rule2006, rule2007, rule2008, rule2009, rule2010, rule2011, rule2012, rule2013, rule2014, rule2015, rule2016, rule2017, rule2018, rule2019, rule2020, rule2021, rule2022, rule2023, rule2024, rule2025, rule2026, rule2027, rule2028, rule2029, rule2030, rule2031, rule2032, rule2033, rule2034, rule2035, rule2036, rule2037, rule2038, rule2039, rule2040, rule2041, rule2042, rule2043, rule2044, rule2045, rule2046, rule2047, rule2048, rule2049, rule2050, rule2051, rule2052, rule2053, rule2054, rule2055, rule2056, rule2057, rule2058, rule2059, rule2060, rule2061, rule2062, rule2063, rule2064, rule2065, rule2066, rule2067, rule2068, rule2069, rule2070, rule2071, rule2072, rule2073, rule2074, rule2075, rule2076, rule2077, rule2078, rule2079, rule2080, rule2081, rule2082, rule2083, rule2084, rule2085, rule2086, rule2087, rule2088, rule2089, rule2090, rule2091, rule2092, rule2093, rule2094, rule2095, rule2096, rule2097, rule2098, rule2099, rule2100, rule2101, rule2102, rule2103, rule2104, rule2105, rule2106, rule2107, rule2108, rule2109, rule2110, rule2111, rule2112, rule2113, rule2114, rule2115, rule2116, rule2117, rule2118, rule2119, rule2120, rule2121, rule2122, rule2123, rule2124, rule2125, rule2126, rule2127, rule2128, rule2129, rule2130, rule2131, rule2132, rule2133, rule2134, rule2135, rule2136, rule2137, rule2138, rule2139, rule2140, rule2141, rule2142, rule2143, rule2144, rule2145, rule2146, rule2147, rule2148, rule2149, rule2150, rule2151, rule2152, rule2153, rule2154, rule2155, rule2156, rule2157, rule2158, rule2159, rule2160, rule2161, rule2162, rule2163, ]
