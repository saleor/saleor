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

def binomial_products(rubi):
    from sympy.integrals.rubi.constraints import cons459, cons3, cons4, cons5, cons460, cons2, cons461, cons54, cons462, cons87, cons463, cons38, cons464, cons148, cons13, cons163, cons465, cons466, cons43, cons448, cons67, cons137, cons467, cons468, cons469, cons470, cons471, cons472, cons473, cons474, cons475, cons476, cons477, cons478, cons479, cons480, cons481, cons482, cons483, cons484, cons105, cons485, cons486, cons487, cons488, cons196, cons489, cons128, cons357, cons490, cons491, cons492, cons493, cons68, cons69, cons55, cons494, cons57, cons58, cons59, cons60, cons495, cons496, cons497, cons498, cons147, cons7, cons21, cons499, cons500, cons501, cons18, cons502, cons503, cons66, cons504, cons505, cons506, cons507, cons17, cons244, cons94, cons508, cons509, cons510, cons511, cons512, cons513, cons514, cons515, cons516, cons517, cons518, cons519, cons520, cons521, cons62, cons522, cons523, cons524, cons525, cons526, cons527, cons528, cons529, cons31, cons530, cons531, cons532, cons533, cons534, cons535, cons536, cons367, cons537, cons538, cons539, cons540, cons356, cons541, cons23, cons542, cons543, cons544, cons545, cons546, cons547, cons548, cons549, cons550, cons551, cons552, cons553, cons554, cons71, cons555, cons27, cons220, cons50, cons556, cons85, cons557, cons395, cons403, cons63, cons558, cons559, cons560, cons561, cons562, cons563, cons564, cons565, cons566, cons567, cons568, cons569, cons70, cons570, cons571, cons572, cons573, cons402, cons574, cons575, cons576, cons405, cons577, cons578, cons579, cons580, cons581, cons177, cons582, cons583, cons117, cons584, cons585, cons586, cons587, cons386, cons588, cons589, cons590, cons591, cons48, cons53, cons592, cons593, cons594, cons595, cons596, cons93, cons597, cons598, cons599, cons600, cons601, cons602, cons603, cons604, cons88, cons605, cons606, cons607, cons608, cons609, cons610, cons611, cons612, cons613, cons614, cons615, cons616, cons617, cons618, cons619, cons620, cons621, cons622, cons623, cons624, cons625, cons626, cons627, cons46, cons628, cons125, cons629, cons630, cons631, cons153, cons632, cons633, cons176, cons634, cons635, cons636, cons637, cons638, cons178, cons639, cons640, cons396, cons641, cons52, cons642, cons643, cons644, cons645, cons646, cons647, cons648, cons649, cons650, cons651, cons652, cons653, cons654, cons655, cons656, cons208, cons657, cons658, cons659, cons660, cons661, cons380, cons662, cons663

    pattern689 = Pattern(Integral((x_**n_*WC('b', S(1)))**p_, x_), cons3, cons4, cons5, cons459)
    def replacement689(x, p, n, b):
        rubi.append(689)
        return Dist(b**IntPart(p)*x**(-n*FracPart(p))*(b*x**n)**FracPart(p), Int(x**(n*p), x), x)
    rule689 = ReplacementRule(pattern689, replacement689)
    pattern690 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons4, cons5, cons460)
    def replacement690(p, b, a, n, x):
        rubi.append(690)
        return Simp(x*(a + b*x**n)**(p + S(1))/a, x)
    rule690 = ReplacementRule(pattern690, replacement690)
    pattern691 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons4, cons5, cons461, cons54)
    def replacement691(p, b, a, n, x):
        rubi.append(691)
        return Dist((n*(p + S(1)) + S(1))/(a*n*(p + S(1))), Int((a + b*x**n)**(p + S(1)), x), x) - Simp(x*(a + b*x**n)**(p + S(1))/(a*n*(p + S(1))), x)
    rule691 = ReplacementRule(pattern691, replacement691)
    pattern692 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**S(2), x_), cons2, cons3, cons4, cons462)
    def replacement692(x, a, n, b):
        rubi.append(692)
        return Int(a**S(2) + S(2)*a*b*x**n + b**S(2)*x**(S(2)*n), x)
    rule692 = ReplacementRule(pattern692, replacement692)
    pattern693 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons87, cons463, cons38)
    def replacement693(p, b, a, n, x):
        rubi.append(693)
        return Int(x**(n*p)*(a*x**(-n) + b)**p, x)
    rule693 = ReplacementRule(pattern693, replacement693)
    pattern694 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons464)
    def replacement694(p, b, a, n, x):
        rubi.append(694)
        return Int(ExpandIntegrand((a + b*x**n)**p, x), x)
    rule694 = ReplacementRule(pattern694, replacement694)
    pattern695 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons148, cons13, cons163, cons465)
    def replacement695(p, b, a, n, x):
        rubi.append(695)
        return Dist(a*n*p/(n*p + S(1)), Int((a + b*x**n)**(p + S(-1)), x), x) + Simp(x*(a + b*x**n)**p/(n*p + S(1)), x)
    rule695 = ReplacementRule(pattern695, replacement695)
    pattern696 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-5)/4), x_), cons2, cons3, cons466, cons43)
    def replacement696(x, a, b):
        rubi.append(696)
        return Simp(S(2)*EllipticE(ArcTan(x*Rt(b/a, S(2)))/S(2), S(2))/(a**(S(5)/4)*Rt(b/a, S(2))), x)
    rule696 = ReplacementRule(pattern696, replacement696)
    pattern697 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-5)/4), x_), cons2, cons3, cons466, cons448)
    def replacement697(x, a, b):
        rubi.append(697)
        return Dist((S(1) + b*x**S(2)/a)**(S(1)/4)/(a*(a + b*x**S(2))**(S(1)/4)), Int((S(1) + b*x**S(2)/a)**(S(-5)/4), x), x)
    rule697 = ReplacementRule(pattern697, replacement697)
    pattern698 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-7)/6), x_), cons2, cons3, cons67)
    def replacement698(x, a, b):
        rubi.append(698)
        return Dist(S(1)/((a/(a + b*x**S(2)))**(S(2)/3)*(a + b*x**S(2))**(S(2)/3)), Subst(Int((-b*x**S(2) + S(1))**(S(-1)/3), x), x, x/sqrt(a + b*x**S(2))), x)
    rule698 = ReplacementRule(pattern698, replacement698)
    pattern699 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons148, cons13, cons137, cons465)
    def replacement699(p, b, a, n, x):
        rubi.append(699)
        return Dist((n*(p + S(1)) + S(1))/(a*n*(p + S(1))), Int((a + b*x**n)**(p + S(1)), x), x) - Simp(x*(a + b*x**n)**(p + S(1))/(a*n*(p + S(1))), x)
    rule699 = ReplacementRule(pattern699, replacement699)
    pattern700 = Pattern(Integral(S(1)/(a_ + x_**S(3)*WC('b', S(1))), x_), cons2, cons3, cons67)
    def replacement700(x, a, b):
        rubi.append(700)
        return Dist(S(1)/(S(3)*Rt(a, S(3))**S(2)), Int((-x*Rt(b, S(3)) + S(2)*Rt(a, S(3)))/(x**S(2)*Rt(b, S(3))**S(2) - x*Rt(a, S(3))*Rt(b, S(3)) + Rt(a, S(3))**S(2)), x), x) + Dist(S(1)/(S(3)*Rt(a, S(3))**S(2)), Int(S(1)/(x*Rt(b, S(3)) + Rt(a, S(3))), x), x)
    rule700 = ReplacementRule(pattern700, replacement700)
    def With701(x, a, n, b):
        r = Numerator(Rt(a/b, n))
        s = Denominator(Rt(a/b, n))
        k = Symbol('k')
        u = Symbol('u')
        u = Int((r - s*x*cos(Pi*(S(2)*k + S(-1))/n))/(r**S(2) - S(2)*r*s*x*cos(Pi*(S(2)*k + S(-1))/n) + s**S(2)*x**S(2)), x)
        u = Int((r - s*x*cos(Pi*(2*k - 1)/n))/(r**2 - 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x)
        return Simp(Dist(2*r/(a*n), Sum_doit(u, List(k, 1, n/2 - 1/2)), x) + r*Int(1/(r + s*x), x)/(a*n), x)
    pattern701 = Pattern(Integral(S(1)/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons467, cons468)
    rule701 = ReplacementRule(pattern701, With701)
    def With702(x, a, n, b):
        r = Numerator(Rt(-a/b, n))
        s = Denominator(Rt(-a/b, n))
        k = Symbol('k')
        u = Symbol('u')
        u = Int((r + s*x*cos(Pi*(S(2)*k + S(-1))/n))/(r**S(2) + S(2)*r*s*x*cos(Pi*(S(2)*k + S(-1))/n) + s**S(2)*x**S(2)), x)
        u = Int((r + s*x*cos(Pi*(2*k - 1)/n))/(r**2 + 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x)
        return Simp(Dist(2*r/(a*n), Sum_doit(u, List(k, 1, n/2 - 1/2)), x) + r*Int(1/(r - s*x), x)/(a*n), x)
    pattern702 = Pattern(Integral(S(1)/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons467, cons469)
    rule702 = ReplacementRule(pattern702, With702)
    pattern703 = Pattern(Integral(S(1)/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons468, cons470)
    def replacement703(x, a, b):
        rubi.append(703)
        return Simp(ArcTan(x*Rt(b, S(2))/Rt(a, S(2)))/(Rt(a, S(2))*Rt(b, S(2))), x)
    rule703 = ReplacementRule(pattern703, replacement703)
    pattern704 = Pattern(Integral(S(1)/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons468, cons471)
    def replacement704(x, a, b):
        rubi.append(704)
        return -Simp(ArcTan(x*Rt(-b, S(2))/Rt(-a, S(2)))/(Rt(-a, S(2))*Rt(-b, S(2))), x)
    rule704 = ReplacementRule(pattern704, replacement704)
    pattern705 = Pattern(Integral(S(1)/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons468)
    def replacement705(x, a, b):
        rubi.append(705)
        return Simp(ArcTan(x/Rt(a/b, S(2)))*Rt(a/b, S(2))/a, x)
    rule705 = ReplacementRule(pattern705, replacement705)
    pattern706 = Pattern(Integral(S(1)/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons469, cons472)
    def replacement706(x, a, b):
        rubi.append(706)
        return Simp(atanh(x*Rt(-b, S(2))/Rt(a, S(2)))/(Rt(a, S(2))*Rt(-b, S(2))), x)
    rule706 = ReplacementRule(pattern706, replacement706)
    pattern707 = Pattern(Integral(S(1)/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons469, cons473)
    def replacement707(x, a, b):
        rubi.append(707)
        return -Simp(atanh(x*Rt(b, S(2))/Rt(-a, S(2)))/(Rt(-a, S(2))*Rt(b, S(2))), x)
    rule707 = ReplacementRule(pattern707, replacement707)
    pattern708 = Pattern(Integral(S(1)/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons469)
    def replacement708(x, a, b):
        rubi.append(708)
        return Simp(Rt(-a/b, S(2))*atanh(x/Rt(-a/b, S(2)))/a, x)
    rule708 = ReplacementRule(pattern708, replacement708)
    def With709(x, a, n, b):
        r = Numerator(Rt(a/b, n))
        s = Denominator(Rt(a/b, n))
        k = Symbol('k')
        u = Symbol('u')
        v = Symbol('v')
        u = Int((r - s*x*cos(Pi*(S(2)*k + S(-1))/n))/(r**S(2) - S(2)*r*s*x*cos(Pi*(S(2)*k + S(-1))/n) + s**S(2)*x**S(2)), x) + Int((r + s*x*cos(Pi*(S(2)*k + S(-1))/n))/(r**S(2) + S(2)*r*s*x*cos(Pi*(S(2)*k + S(-1))/n) + s**S(2)*x**S(2)), x)
        u = Int((r - s*x*cos(Pi*(2*k - 1)/n))/(r**2 - 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x) + Int((r + s*x*cos(Pi*(2*k - 1)/n))/(r**2 + 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x)
        return Simp(Dist(2*r/(a*n), Sum_doit(u, List(k, 1, n/4 - 1/2)), x) + 2*r**2*Int(1/(r**2 + s**2*x**2), x)/(a*n), x)
    pattern709 = Pattern(Integral(S(1)/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons474, cons468)
    rule709 = ReplacementRule(pattern709, With709)
    def With710(x, a, n, b):
        r = Numerator(Rt(-a/b, n))
        s = Denominator(Rt(-a/b, n))
        k = Symbol('k')
        u = Symbol('u')
        u = Int((r - s*x*cos(S(2)*Pi*k/n))/(r**S(2) - S(2)*r*s*x*cos(S(2)*Pi*k/n) + s**S(2)*x**S(2)), x) + Int((r + s*x*cos(S(2)*Pi*k/n))/(r**S(2) + S(2)*r*s*x*cos(S(2)*Pi*k/n) + s**S(2)*x**S(2)), x)
        u = Int((r - s*x*cos(2*Pi*k/n))/(r**2 - 2*r*s*x*cos(2*Pi*k/n) + s**2*x**2), x) + Int((r + s*x*cos(2*Pi*k/n))/(r**2 + 2*r*s*x*cos(2*Pi*k/n) + s**2*x**2), x)
        return Simp(Dist(2*r/(a*n), Sum_doit(u, List(k, 1, n/4 - 1/2)), x) + 2*r**2*Int(1/(r**2 - s**2*x**2), x)/(a*n), x)
    pattern710 = Pattern(Integral(S(1)/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons474, cons469)
    rule710 = ReplacementRule(pattern710, With710)
    def With711(x, a, b):
        r = Numerator(Rt(a/b, S(2)))
        s = Denominator(Rt(a/b, S(2)))
        rubi.append(711)
        return Dist(S(1)/(S(2)*r), Int((r - s*x**S(2))/(a + b*x**S(4)), x), x) + Dist(S(1)/(S(2)*r), Int((r + s*x**S(2))/(a + b*x**S(4)), x), x)
    pattern711 = Pattern(Integral(S(1)/(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons475)
    rule711 = ReplacementRule(pattern711, With711)
    def With712(x, a, b):
        r = Numerator(Rt(-a/b, S(2)))
        s = Denominator(Rt(-a/b, S(2)))
        rubi.append(712)
        return Dist(r/(S(2)*a), Int(S(1)/(r - s*x**S(2)), x), x) + Dist(r/(S(2)*a), Int(S(1)/(r + s*x**S(2)), x), x)
    pattern712 = Pattern(Integral(S(1)/(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons476)
    rule712 = ReplacementRule(pattern712, With712)
    def With713(x, a, n, b):
        r = Numerator(Rt(a/b, S(4)))
        s = Denominator(Rt(a/b, S(4)))
        rubi.append(713)
        return Dist(sqrt(S(2))*r/(S(4)*a), Int((sqrt(S(2))*r - s*x**(n/S(4)))/(r**S(2) - sqrt(S(2))*r*s*x**(n/S(4)) + s**S(2)*x**(n/S(2))), x), x) + Dist(sqrt(S(2))*r/(S(4)*a), Int((sqrt(S(2))*r + s*x**(n/S(4)))/(r**S(2) + sqrt(S(2))*r*s*x**(n/S(4)) + s**S(2)*x**(n/S(2))), x), x)
    pattern713 = Pattern(Integral(S(1)/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons477, cons478)
    rule713 = ReplacementRule(pattern713, With713)
    def With714(x, a, n, b):
        r = Numerator(Rt(-a/b, S(2)))
        s = Denominator(Rt(-a/b, S(2)))
        rubi.append(714)
        return Dist(r/(S(2)*a), Int(S(1)/(r - s*x**(n/S(2))), x), x) + Dist(r/(S(2)*a), Int(S(1)/(r + s*x**(n/S(2))), x), x)
    pattern714 = Pattern(Integral(S(1)/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons477, cons476)
    rule714 = ReplacementRule(pattern714, With714)
    pattern715 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons43, cons479)
    def replacement715(x, a, b):
        rubi.append(715)
        return Simp(asinh(x*Rt(b, S(2))/sqrt(a))/Rt(b, S(2)), x)
    rule715 = ReplacementRule(pattern715, replacement715)
    pattern716 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons43, cons480)
    def replacement716(x, a, b):
        rubi.append(716)
        return Simp(asin(x*Rt(-b, S(2))/sqrt(a))/Rt(-b, S(2)), x)
    rule716 = ReplacementRule(pattern716, replacement716)
    pattern717 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons448)
    def replacement717(x, a, b):
        rubi.append(717)
        return Subst(Int(S(1)/(-b*x**S(2) + S(1)), x), x, x/sqrt(a + b*x**S(2)))
    rule717 = ReplacementRule(pattern717, replacement717)
    def With718(x, a, b):
        r = Numer(Rt(b/a, S(3)))
        s = Denom(Rt(b/a, S(3)))
        rubi.append(718)
        return Simp(S(2)*S(3)**(S(3)/4)*sqrt((r**S(2)*x**S(2) - r*s*x + s**S(2))/(r*x + s*(S(1) + sqrt(S(3))))**S(2))*sqrt(sqrt(S(3)) + S(2))*(r*x + s)*EllipticF(asin((r*x + s*(-sqrt(S(3)) + S(1)))/(r*x + s*(S(1) + sqrt(S(3))))), S(-7) - S(4)*sqrt(S(3)))/(S(3)*r*sqrt(s*(r*x + s)/(r*x + s*(S(1) + sqrt(S(3))))**S(2))*sqrt(a + b*x**S(3))), x)
    pattern718 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(3)*WC('b', S(1))), x_), cons2, cons3, cons481)
    rule718 = ReplacementRule(pattern718, With718)
    def With719(x, a, b):
        r = Numer(Rt(b/a, S(3)))
        s = Denom(Rt(b/a, S(3)))
        rubi.append(719)
        return Simp(S(2)*S(3)**(S(3)/4)*sqrt((r**S(2)*x**S(2) - r*s*x + s**S(2))/(r*x + s*(-sqrt(S(3)) + S(1)))**S(2))*sqrt(-sqrt(S(3)) + S(2))*(r*x + s)*EllipticF(asin((r*x + s*(S(1) + sqrt(S(3))))/(r*x + s*(-sqrt(S(3)) + S(1)))), S(-7) + S(4)*sqrt(S(3)))/(S(3)*r*sqrt(-s*(r*x + s)/(r*x + s*(-sqrt(S(3)) + S(1)))**S(2))*sqrt(a + b*x**S(3))), x)
    pattern719 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(3)*WC('b', S(1))), x_), cons2, cons3, cons482)
    rule719 = ReplacementRule(pattern719, With719)
    def With720(x, a, b):
        q = Rt(b/a, S(4))
        rubi.append(720)
        return Simp(sqrt((a + b*x**S(4))/(a*(q**S(2)*x**S(2) + S(1))**S(2)))*(q**S(2)*x**S(2) + S(1))*EllipticF(S(2)*ArcTan(q*x), S(1)/2)/(S(2)*q*sqrt(a + b*x**S(4))), x)
    pattern720 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons466)
    rule720 = ReplacementRule(pattern720, With720)
    pattern721 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons483, cons43)
    def replacement721(x, a, b):
        rubi.append(721)
        return Simp(EllipticF(asin(x*Rt(-b, S(4))/Rt(a, S(4))), S(-1))/(Rt(a, S(4))*Rt(-b, S(4))), x)
    rule721 = ReplacementRule(pattern721, replacement721)
    def With722(x, a, b):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = Rt(-a*b, S(2))
        if IntegerQ(q):
            return True
        return False
    pattern722 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons484, cons105, CustomConstraint(With722))
    def replacement722(x, a, b):

        q = Rt(-a*b, S(2))
        rubi.append(722)
        return Simp(sqrt(S(2))*sqrt((a + q*x**S(2))/q)*sqrt(-a + q*x**S(2))*EllipticF(asin(sqrt(S(2))*x/sqrt((a + q*x**S(2))/q)), S(1)/2)/(S(2)*sqrt(-a)*sqrt(a + b*x**S(4))), x)
    rule722 = ReplacementRule(pattern722, replacement722)
    def With723(x, a, b):
        q = Rt(-a*b, S(2))
        rubi.append(723)
        return Simp(sqrt(S(2))*sqrt((a + q*x**S(2))/q)*sqrt((a - q*x**S(2))/(a + q*x**S(2)))*EllipticF(asin(sqrt(S(2))*x/sqrt((a + q*x**S(2))/q)), S(1)/2)/(S(2)*sqrt(a/(a + q*x**S(2)))*sqrt(a + b*x**S(4))), x)
    pattern723 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons484, cons105)
    rule723 = ReplacementRule(pattern723, With723)
    pattern724 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons483, cons448)
    def replacement724(x, a, b):
        rubi.append(724)
        return Dist(sqrt(S(1) + b*x**S(4)/a)/sqrt(a + b*x**S(4)), Int(S(1)/sqrt(S(1) + b*x**S(4)/a), x), x)
    rule724 = ReplacementRule(pattern724, replacement724)
    def With725(x, a, b):
        r = Numer(Rt(b/a, S(3)))
        s = Denom(Rt(b/a, S(3)))
        rubi.append(725)
        return Simp(S(3)**(S(3)/4)*x*sqrt((r**S(2)*x**S(4) - r*s*x**S(2) + s**S(2))/(r*x**S(2)*(S(1) + sqrt(S(3))) + s)**S(2))*(r*x**S(2) + s)*EllipticF(acos((r*x**S(2)*(-sqrt(S(3)) + S(1)) + s)/(r*x**S(2)*(S(1) + sqrt(S(3))) + s)), sqrt(S(3))/S(4) + S(1)/2)/(S(6)*s*sqrt(r*x**S(2)*(r*x**S(2) + s)/(r*x**S(2)*(S(1) + sqrt(S(3))) + s)**S(2))*sqrt(a + b*x**S(6))), x)
    pattern725 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(6)*WC('b', S(1))), x_), cons2, cons3, cons67)
    rule725 = ReplacementRule(pattern725, With725)
    pattern726 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(8)*WC('b', S(1))), x_), cons2, cons3, cons67)
    def replacement726(x, a, b):
        rubi.append(726)
        return Dist(S(1)/2, Int((-x**S(2)*Rt(b/a, S(4)) + S(1))/sqrt(a + b*x**S(8)), x), x) + Dist(S(1)/2, Int((x**S(2)*Rt(b/a, S(4)) + S(1))/sqrt(a + b*x**S(8)), x), x)
    rule726 = ReplacementRule(pattern726, replacement726)
    pattern727 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-1)/4), x_), cons2, cons3, cons466)
    def replacement727(x, a, b):
        rubi.append(727)
        return -Dist(a, Int((a + b*x**S(2))**(S(-5)/4), x), x) + Simp(S(2)*x/(a + b*x**S(2))**(S(1)/4), x)
    rule727 = ReplacementRule(pattern727, replacement727)
    pattern728 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-1)/4), x_), cons2, cons3, cons483, cons43)
    def replacement728(x, a, b):
        rubi.append(728)
        return Simp(S(2)*EllipticE(asin(x*Rt(-b/a, S(2)))/S(2), S(2))/(a**(S(1)/4)*Rt(-b/a, S(2))), x)
    rule728 = ReplacementRule(pattern728, replacement728)
    pattern729 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-1)/4), x_), cons2, cons3, cons483, cons448)
    def replacement729(x, a, b):
        rubi.append(729)
        return Dist((S(1) + b*x**S(2)/a)**(S(1)/4)/(a + b*x**S(2))**(S(1)/4), Int((S(1) + b*x**S(2)/a)**(S(-1)/4), x), x)
    rule729 = ReplacementRule(pattern729, replacement729)
    pattern730 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-3)/4), x_), cons2, cons3, cons43, cons466)
    def replacement730(x, a, b):
        rubi.append(730)
        return Simp(S(2)*EllipticF(ArcTan(x*Rt(b/a, S(2)))/S(2), S(2))/(a**(S(3)/4)*Rt(b/a, S(2))), x)
    rule730 = ReplacementRule(pattern730, replacement730)
    pattern731 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-3)/4), x_), cons2, cons3, cons43, cons483)
    def replacement731(x, a, b):
        rubi.append(731)
        return Simp(S(2)*EllipticF(asin(x*Rt(-b/a, S(2)))/S(2), S(2))/(a**(S(3)/4)*Rt(-b/a, S(2))), x)
    rule731 = ReplacementRule(pattern731, replacement731)
    pattern732 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-3)/4), x_), cons2, cons3, cons448)
    def replacement732(x, a, b):
        rubi.append(732)
        return Dist((S(1) + b*x**S(2)/a)**(S(3)/4)/(a + b*x**S(2))**(S(3)/4), Int((S(1) + b*x**S(2)/a)**(S(-3)/4), x), x)
    rule732 = ReplacementRule(pattern732, replacement732)
    pattern733 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-1)/3), x_), cons2, cons3, cons67)
    def replacement733(x, a, b):
        rubi.append(733)
        return Dist(S(3)*sqrt(b*x**S(2))/(S(2)*b*x), Subst(Int(x/sqrt(-a + x**S(3)), x), x, (a + b*x**S(2))**(S(1)/3)), x)
    rule733 = ReplacementRule(pattern733, replacement733)
    pattern734 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-2)/3), x_), cons2, cons3, cons67)
    def replacement734(x, a, b):
        rubi.append(734)
        return Dist(S(3)*sqrt(b*x**S(2))/(S(2)*b*x), Subst(Int(S(1)/sqrt(-a + x**S(3)), x), x, (a + b*x**S(2))**(S(1)/3)), x)
    rule734 = ReplacementRule(pattern734, replacement734)
    pattern735 = Pattern(Integral((a_ + x_**S(4)*WC('b', S(1)))**(S(-3)/4), x_), cons2, cons3, cons67)
    def replacement735(x, a, b):
        rubi.append(735)
        return Dist(x**S(3)*(a/(b*x**S(4)) + S(1))**(S(3)/4)/(a + b*x**S(4))**(S(3)/4), Int(S(1)/(x**S(3)*(a/(b*x**S(4)) + S(1))**(S(3)/4)), x), x)
    rule735 = ReplacementRule(pattern735, replacement735)
    pattern736 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(-1)/6), x_), cons2, cons3, cons67)
    def replacement736(x, a, b):
        rubi.append(736)
        return -Dist(a/S(2), Int((a + b*x**S(2))**(S(-7)/6), x), x) + Simp(S(3)*x/(S(2)*(a + b*x**S(2))**(S(1)/6)), x)
    rule736 = ReplacementRule(pattern736, replacement736)
    pattern737 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons148, cons13, cons485, cons486, cons487)
    def replacement737(p, b, a, n, x):
        rubi.append(737)
        return Dist(a**(p + S(1)/n), Subst(Int((-b*x**n + S(1))**(-p + S(-1) - S(1)/n), x), x, x*(a + b*x**n)**(-S(1)/n)), x)
    rule737 = ReplacementRule(pattern737, replacement737)
    pattern738 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons148, cons13, cons485, cons486, cons488)
    def replacement738(p, b, a, n, x):
        rubi.append(738)
        return Dist((a/(a + b*x**n))**(p + S(1)/n)*(a + b*x**n)**(p + S(1)/n), Subst(Int((-b*x**n + S(1))**(-p + S(-1) - S(1)/n), x), x, x*(a + b*x**n)**(-S(1)/n)), x)
    rule738 = ReplacementRule(pattern738, replacement738)
    pattern739 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons5, cons196)
    def replacement739(p, b, a, n, x):
        rubi.append(739)
        return -Subst(Int((a + b*x**(-n))**p/x**S(2), x), x, S(1)/x)
    rule739 = ReplacementRule(pattern739, replacement739)
    def With740(p, b, a, n, x):
        k = Denominator(n)
        rubi.append(740)
        return Dist(k, Subst(Int(x**(k + S(-1))*(a + b*x**(k*n))**p, x), x, x**(S(1)/k)), x)
    pattern740 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons5, cons489)
    rule740 = ReplacementRule(pattern740, With740)
    pattern741 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons4, cons128)
    def replacement741(p, b, a, n, x):
        rubi.append(741)
        return Int(ExpandIntegrand((a + b*x**n)**p, x), x)
    rule741 = ReplacementRule(pattern741, replacement741)
    pattern742 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons4, cons5, cons357, cons490, cons491, cons492)
    def replacement742(p, b, a, n, x):
        rubi.append(742)
        return Simp(a**p*x*Hypergeometric2F1(-p, S(1)/n, S(1) + S(1)/n, -b*x**n/a), x)
    rule742 = ReplacementRule(pattern742, replacement742)
    pattern743 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons4, cons5, cons357, cons490, cons491, cons493)
    def replacement743(p, b, a, n, x):
        rubi.append(743)
        return Dist(a**IntPart(p)*(S(1) + b*x**n/a)**(-FracPart(p))*(a + b*x**n)**FracPart(p), Int((S(1) + b*x**n/a)**p, x), x)
    rule743 = ReplacementRule(pattern743, replacement743)
    pattern744 = Pattern(Integral((u_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons4, cons5, cons68, cons69)
    def replacement744(p, u, b, a, n, x):
        rubi.append(744)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b*x**n)**p, x), x, u), x)
    rule744 = ReplacementRule(pattern744, replacement744)
    pattern745 = Pattern(Integral((x_**n_*WC('b1', S(1)) + WC('a1', S(0)))**WC('p', S(1))*(x_**n_*WC('b2', S(1)) + WC('a2', S(0)))**WC('p', S(1)), x_), cons57, cons58, cons59, cons60, cons4, cons5, cons55, cons494)
    def replacement745(a2, p, b2, b1, n, x, a1):
        rubi.append(745)
        return Int((a1*a2 + b1*b2*x**(S(2)*n))**p, x)
    rule745 = ReplacementRule(pattern745, replacement745)
    pattern746 = Pattern(Integral((a1_ + x_**WC('n', S(1))*WC('b1', S(1)))**WC('p', S(1))*(a2_ + x_**WC('n', S(1))*WC('b2', S(1)))**WC('p', S(1)), x_), cons57, cons58, cons59, cons60, cons55, cons495, cons13, cons163, cons496)
    def replacement746(p, a2, b2, b1, n, x, a1):
        rubi.append(746)
        return Dist(S(2)*a1*a2*n*p/(S(2)*n*p + S(1)), Int((a1 + b1*x**n)**(p + S(-1))*(a2 + b2*x**n)**(p + S(-1)), x), x) + Simp(x*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p/(S(2)*n*p + S(1)), x)
    rule746 = ReplacementRule(pattern746, replacement746)
    pattern747 = Pattern(Integral((a1_ + x_**WC('n', S(1))*WC('b1', S(1)))**p_*(a2_ + x_**WC('n', S(1))*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons55, cons495, cons13, cons137, cons496)
    def replacement747(p, a2, b2, b1, n, x, a1):
        rubi.append(747)
        return Dist((S(2)*n*(p + S(1)) + S(1))/(S(2)*a1*a2*n*(p + S(1))), Int((a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1)), x), x) - Simp(x*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(S(2)*a1*a2*n*(p + S(1))), x)
    rule747 = ReplacementRule(pattern747, replacement747)
    pattern748 = Pattern(Integral((a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons5, cons55, cons497)
    def replacement748(p, a2, b2, b1, n, x, a1):
        rubi.append(748)
        return -Subst(Int((a1 + b1*x**(-n))**p*(a2 + b2*x**(-n))**p/x**S(2), x), x, S(1)/x)
    rule748 = ReplacementRule(pattern748, replacement748)
    def With749(p, a2, b2, b1, n, x, a1):
        k = Denominator(S(2)*n)
        rubi.append(749)
        return Dist(k, Subst(Int(x**(k + S(-1))*(a1 + b1*x**(k*n))**p*(a2 + b2*x**(k*n))**p, x), x, x**(S(1)/k)), x)
    pattern749 = Pattern(Integral((a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons5, cons55, cons498)
    rule749 = ReplacementRule(pattern749, With749)
    pattern750 = Pattern(Integral((x_**n_*WC('b1', S(1)) + WC('a1', S(0)))**p_*(x_**n_*WC('b2', S(1)) + WC('a2', S(0)))**p_, x_), cons57, cons58, cons59, cons60, cons4, cons5, cons55, cons147)
    def replacement750(a2, p, b2, b1, n, x, a1):
        rubi.append(750)
        return Dist((a1 + b1*x**n)**FracPart(p)*(a2 + b2*x**n)**FracPart(p)*(a1*a2 + b1*b2*x**(S(2)*n))**(-FracPart(p)), Int((a1*a2 + b1*b2*x**(S(2)*n))**p, x), x)
    rule750 = ReplacementRule(pattern750, replacement750)
    pattern751 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons5, cons55, cons494)
    def replacement751(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(751)
        return Int((c*x)**m*(a1*a2 + b1*b2*x**(S(2)*n))**p, x)
    rule751 = ReplacementRule(pattern751, replacement751)
    pattern752 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(x_**n_*WC('b', S(1)))**p_, x_), cons3, cons7, cons21, cons4, cons5, cons499, cons500)
    def replacement752(p, m, b, c, n, x):
        rubi.append(752)
        return Dist(b**(S(1) - (m + S(1))/n)*c**m/n, Subst(Int((b*x)**(p + S(-1) + (m + S(1))/n), x), x, x**n), x)
    rule752 = ReplacementRule(pattern752, replacement752)
    pattern753 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(x_**WC('n', S(1))*WC('b', S(1)))**p_, x_), cons3, cons7, cons21, cons4, cons5, cons499, cons501)
    def replacement753(p, m, b, c, n, x):
        rubi.append(753)
        return Dist(b**IntPart(p)*c**m*x**(-n*FracPart(p))*(b*x**n)**FracPart(p), Int(x**(m + n*p), x), x)
    rule753 = ReplacementRule(pattern753, replacement753)
    pattern754 = Pattern(Integral((c_*x_)**m_*(x_**WC('n', S(1))*WC('b', S(1)))**p_, x_), cons3, cons7, cons21, cons4, cons5, cons18)
    def replacement754(p, m, b, c, n, x):
        rubi.append(754)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(b*x**n)**p, x), x)
    rule754 = ReplacementRule(pattern754, replacement754)
    pattern755 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons21, cons4, cons38, cons502)
    def replacement755(p, m, b, a, n, x):
        rubi.append(755)
        return Int(x**(m + n*p)*(a*x**(-n) + b)**p, x)
    rule755 = ReplacementRule(pattern755, replacement755)
    pattern756 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons5, cons503, cons66)
    def replacement756(p, m, b, c, a, n, x):
        rubi.append(756)
        return Simp((c*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*c*(m + S(1))), x)
    rule756 = ReplacementRule(pattern756, replacement756)
    pattern757 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons5, cons55, cons504, cons66)
    def replacement757(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(757)
        return Simp((c*x)**(m + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(a1*a2*c*(m + S(1))), x)
    rule757 = ReplacementRule(pattern757, replacement757)
    pattern758 = Pattern(Integral(x_**WC('m', S(1))*(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons21, cons4, cons5, cons500)
    def replacement758(p, m, b, a, n, x):
        rubi.append(758)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + (m + S(1))/n)*(a + b*x)**p, x), x, x**n), x)
    rule758 = ReplacementRule(pattern758, replacement758)
    pattern759 = Pattern(Integral(x_**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons21, cons4, cons5, cons55, cons505)
    def replacement759(p, a2, m, b2, b1, n, x, a1):
        rubi.append(759)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + (m + S(1))/n)*(a1 + b1*x)**p*(a2 + b2*x)**p, x), x, x**n), x)
    rule759 = ReplacementRule(pattern759, replacement759)
    pattern760 = Pattern(Integral((c_*x_)**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons5, cons500)
    def replacement760(p, m, b, c, a, n, x):
        rubi.append(760)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a + b*x**n)**p, x), x)
    rule760 = ReplacementRule(pattern760, replacement760)
    pattern761 = Pattern(Integral((c_*x_)**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons5, cons55, cons505)
    def replacement761(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(761)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x)
    rule761 = ReplacementRule(pattern761, replacement761)
    pattern762 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons21, cons4, cons128)
    def replacement762(p, m, b, c, a, n, x):
        rubi.append(762)
        return Int(ExpandIntegrand((c*x)**m*(a + b*x**n)**p, x), x)
    rule762 = ReplacementRule(pattern762, replacement762)
    pattern763 = Pattern(Integral(x_**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons21, cons4, cons5, cons506, cons66)
    def replacement763(p, m, b, a, n, x):
        rubi.append(763)
        return -Dist(b*(m + n*(p + S(1)) + S(1))/(a*(m + S(1))), Int(x**(m + n)*(a + b*x**n)**p, x), x) + Simp(x**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*(m + S(1))), x)
    rule763 = ReplacementRule(pattern763, replacement763)
    pattern764 = Pattern(Integral(x_**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons21, cons4, cons5, cons55, cons507, cons66)
    def replacement764(p, a2, m, b2, b1, n, x, a1):
        rubi.append(764)
        return -Dist(b1*b2*(m + S(2)*n*(p + S(1)) + S(1))/(a1*a2*(m + S(1))), Int(x**(m + S(2)*n)*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x) + Simp(x**(m + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(a1*a2*(m + S(1))), x)
    rule764 = ReplacementRule(pattern764, replacement764)
    pattern765 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons5, cons506, cons54)
    def replacement765(p, m, b, c, a, n, x):
        rubi.append(765)
        return Dist((m + n*(p + S(1)) + S(1))/(a*n*(p + S(1))), Int((c*x)**m*(a + b*x**n)**(p + S(1)), x), x) - Simp((c*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*c*n*(p + S(1))), x)
    rule765 = ReplacementRule(pattern765, replacement765)
    pattern766 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons5, cons55, cons507, cons54)
    def replacement766(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(766)
        return Dist((m + S(2)*n*(p + S(1)) + S(1))/(S(2)*a1*a2*n*(p + S(1))), Int((c*x)**m*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1)), x), x) - Simp((c*x)**(m + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(S(2)*a1*a2*c*n*(p + S(1))), x)
    rule766 = ReplacementRule(pattern766, replacement766)
    def With767(p, m, b, a, n, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        k = GCD(m + S(1), n)
        if Unequal(k, S(1)):
            return True
        return False
    pattern767 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons5, cons148, cons17, CustomConstraint(With767))
    def replacement767(p, m, b, a, n, x):

        k = GCD(m + S(1), n)
        rubi.append(767)
        return Dist(S(1)/k, Subst(Int(x**(S(-1) + (m + S(1))/k)*(a + b*x**(n/k))**p, x), x, x**k), x)
    rule767 = ReplacementRule(pattern767, replacement767)
    def With768(p, a2, m, b2, b1, n, x, a1):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        k = GCD(m + S(1), S(2)*n)
        if Unequal(k, S(1)):
            return True
        return False
    pattern768 = Pattern(Integral(x_**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons5, cons55, cons495, cons17, CustomConstraint(With768))
    def replacement768(p, a2, m, b2, b1, n, x, a1):

        k = GCD(m + S(1), S(2)*n)
        rubi.append(768)
        return Dist(S(1)/k, Subst(Int(x**(S(-1) + (m + S(1))/k)*(a1 + b1*x**(n/k))**p*(a2 + b2*x**(n/k))**p, x), x, x**k), x)
    rule768 = ReplacementRule(pattern768, replacement768)
    pattern769 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons148, cons244, cons163, cons94, cons508, cons509)
    def replacement769(p, m, b, c, a, n, x):
        rubi.append(769)
        return -Dist(b*c**(-n)*n*p/(m + S(1)), Int((c*x)**(m + n)*(a + b*x**n)**(p + S(-1)), x), x) + Simp((c*x)**(m + S(1))*(a + b*x**n)**p/(c*(m + S(1))), x)
    rule769 = ReplacementRule(pattern769, replacement769)
    pattern770 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons55, cons495, cons244, cons163, cons510, cons511)
    def replacement770(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(770)
        return Dist(S(2)*a1*a2*n*p/(m + S(2)*n*p + S(1)), Int((c*x)**m*(a1 + b1*x**n)**(p + S(-1))*(a2 + b2*x**n)**(p + S(-1)), x), x) + Simp((c*x)**(m + S(1))*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p/(c*(m + S(2)*n*p + S(1))), x)
    rule770 = ReplacementRule(pattern770, replacement770)
    pattern771 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons148, cons244, cons163, cons512, cons509)
    def replacement771(p, m, b, c, a, n, x):
        rubi.append(771)
        return Dist(a*n*p/(m + n*p + S(1)), Int((c*x)**m*(a + b*x**n)**(p + S(-1)), x), x) + Simp((c*x)**(m + S(1))*(a + b*x**n)**p/(c*(m + n*p + S(1))), x)
    rule771 = ReplacementRule(pattern771, replacement771)
    pattern772 = Pattern(Integral(x_**S(2)/(a_ + x_**S(4)*WC('b', S(1)))**(S(5)/4), x_), cons2, cons3, cons466)
    def replacement772(x, a, b):
        rubi.append(772)
        return Dist(x*(a/(b*x**S(4)) + S(1))**(S(1)/4)/(b*(a + b*x**S(4))**(S(1)/4)), Int(S(1)/(x**S(3)*(a/(b*x**S(4)) + S(1))**(S(5)/4)), x), x)
    rule772 = ReplacementRule(pattern772, replacement772)
    pattern773 = Pattern(Integral(x_**m_/(a_ + x_**S(4)*WC('b', S(1)))**(S(5)/4), x_), cons2, cons3, cons466, cons513)
    def replacement773(x, m, b, a):
        rubi.append(773)
        return -Dist(a*(m + S(-3))/(b*(m + S(-4))), Int(x**(m + S(-4))/(a + b*x**S(4))**(S(5)/4), x), x) + Simp(x**(m + S(-3))/(b*(a + b*x**S(4))**(S(1)/4)*(m + S(-4))), x)
    rule773 = ReplacementRule(pattern773, replacement773)
    pattern774 = Pattern(Integral(x_**m_/(a_ + x_**S(4)*WC('b', S(1)))**(S(5)/4), x_), cons2, cons3, cons466, cons514)
    def replacement774(x, m, b, a):
        rubi.append(774)
        return -Dist(b*m/(a*(m + S(1))), Int(x**(m + S(4))/(a + b*x**S(4))**(S(5)/4), x), x) + Simp(x**(m + S(1))/(a*(a + b*x**S(4))**(S(1)/4)*(m + S(1))), x)
    rule774 = ReplacementRule(pattern774, replacement774)
    pattern775 = Pattern(Integral(sqrt(x_*WC('c', S(1)))/(a_ + x_**S(2)*WC('b', S(1)))**(S(5)/4), x_), cons2, cons3, cons7, cons466)
    def replacement775(x, c, b, a):
        rubi.append(775)
        return Dist(sqrt(c*x)*(a/(b*x**S(2)) + S(1))**(S(1)/4)/(b*(a + b*x**S(2))**(S(1)/4)), Int(S(1)/(x**S(2)*(a/(b*x**S(2)) + S(1))**(S(5)/4)), x), x)
    rule775 = ReplacementRule(pattern775, replacement775)
    pattern776 = Pattern(Integral((x_*WC('c', S(1)))**m_/(a_ + x_**S(2)*WC('b', S(1)))**(S(5)/4), x_), cons2, cons3, cons7, cons466, cons515, cons516)
    def replacement776(m, b, c, a, x):
        rubi.append(776)
        return -Dist(S(2)*a*c**S(2)*(m + S(-1))/(b*(S(2)*m + S(-3))), Int((c*x)**(m + S(-2))/(a + b*x**S(2))**(S(5)/4), x), x) + Simp(S(2)*c*(c*x)**(m + S(-1))/(b*(a + b*x**S(2))**(S(1)/4)*(S(2)*m + S(-3))), x)
    rule776 = ReplacementRule(pattern776, replacement776)
    pattern777 = Pattern(Integral((x_*WC('c', S(1)))**m_/(a_ + x_**S(2)*WC('b', S(1)))**(S(5)/4), x_), cons2, cons3, cons7, cons466, cons515, cons94)
    def replacement777(m, b, c, a, x):
        rubi.append(777)
        return -Dist(b*(S(2)*m + S(1))/(S(2)*a*c**S(2)*(m + S(1))), Int((c*x)**(m + S(2))/(a + b*x**S(2))**(S(5)/4), x), x) + Simp((c*x)**(m + S(1))/(a*c*(a + b*x**S(2))**(S(1)/4)*(m + S(1))), x)
    rule777 = ReplacementRule(pattern777, replacement777)
    pattern778 = Pattern(Integral(x_**S(2)/(a_ + x_**S(4)*WC('b', S(1)))**(S(5)/4), x_), cons2, cons3, cons483)
    def replacement778(x, a, b):
        rubi.append(778)
        return -Dist(S(1)/b, Int(S(1)/(x**S(2)*(a + b*x**S(4))**(S(1)/4)), x), x) - Simp(S(1)/(b*x*(a + b*x**S(4))**(S(1)/4)), x)
    rule778 = ReplacementRule(pattern778, replacement778)
    pattern779 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons148, cons244, cons137, cons517, cons518, cons509)
    def replacement779(p, m, b, c, a, n, x):
        rubi.append(779)
        return -Dist(c**n*(m - n + S(1))/(b*n*(p + S(1))), Int((c*x)**(m - n)*(a + b*x**n)**(p + S(1)), x), x) + Simp(c**(n + S(-1))*(c*x)**(m - n + S(1))*(a + b*x**n)**(p + S(1))/(b*n*(p + S(1))), x)
    rule779 = ReplacementRule(pattern779, replacement779)
    pattern780 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons55, cons495, cons244, cons137, cons519, cons520, cons511)
    def replacement780(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(780)
        return -Dist(c**(S(2)*n)*(m - S(2)*n + S(1))/(S(2)*b1*b2*n*(p + S(1))), Int((c*x)**(m - S(2)*n)*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1)), x), x) + Simp(c**(S(2)*n + S(-1))*(c*x)**(m - S(2)*n + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(S(2)*b1*b2*n*(p + S(1))), x)
    rule780 = ReplacementRule(pattern780, replacement780)
    pattern781 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons148, cons244, cons137, cons509)
    def replacement781(p, m, b, c, a, n, x):
        rubi.append(781)
        return Dist((m + n*(p + S(1)) + S(1))/(a*n*(p + S(1))), Int((c*x)**m*(a + b*x**n)**(p + S(1)), x), x) - Simp((c*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*c*n*(p + S(1))), x)
    rule781 = ReplacementRule(pattern781, replacement781)
    pattern782 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons55, cons495, cons244, cons137, cons511)
    def replacement782(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(782)
        return Dist((m + S(2)*n*(p + S(1)) + S(1))/(S(2)*a1*a2*n*(p + S(1))), Int((c*x)**m*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1)), x), x) - Simp((c*x)**(m + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(S(2)*a1*a2*c*n*(p + S(1))), x)
    rule782 = ReplacementRule(pattern782, replacement782)
    pattern783 = Pattern(Integral(x_/(a_ + x_**S(3)*WC('b', S(1))), x_), cons2, cons3, cons67)
    def replacement783(x, a, b):
        rubi.append(783)
        return Dist(S(1)/(S(3)*Rt(a, S(3))*Rt(b, S(3))), Int((x*Rt(b, S(3)) + Rt(a, S(3)))/(x**S(2)*Rt(b, S(3))**S(2) - x*Rt(a, S(3))*Rt(b, S(3)) + Rt(a, S(3))**S(2)), x), x) - Dist(S(1)/(S(3)*Rt(a, S(3))*Rt(b, S(3))), Int(S(1)/(x*Rt(b, S(3)) + Rt(a, S(3))), x), x)
    rule783 = ReplacementRule(pattern783, replacement783)
    def With784(m, b, a, n, x):
        r = Numerator(Rt(a/b, n))
        s = Denominator(Rt(a/b, n))
        k = Symbol('k')
        u = Symbol('u')
        u = Int((r*cos(Pi*m*(S(2)*k + S(-1))/n) - s*x*cos(Pi*(S(2)*k + S(-1))*(m + S(1))/n))/(r**S(2) - S(2)*r*s*x*cos(Pi*(S(2)*k + S(-1))/n) + s**S(2)*x**S(2)), x)
        u = Int((r*cos(Pi*m*(2*k - 1)/n) - s*x*cos(Pi*(2*k - 1)*(m + 1)/n))/(r**2 - 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x)
        return Simp(Dist(2*r**(m + 1)*s**(-m)/(a*n), Sum_doit(u, List(k, 1, n/2 - 1/2)), x) - s**(-m)*(-r)**(m + 1)*Int(1/(r + s*x), x)/(a*n), x)
    pattern784 = Pattern(Integral(x_**WC('m', S(1))/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons521, cons62, cons522, cons468)
    rule784 = ReplacementRule(pattern784, With784)
    def With785(m, b, a, n, x):
        r = Numerator(Rt(-a/b, n))
        s = Denominator(Rt(-a/b, n))
        k = Symbol('k')
        u = Symbol('u')
        u = Int((r*cos(Pi*m*(S(2)*k + S(-1))/n) + s*x*cos(Pi*(S(2)*k + S(-1))*(m + S(1))/n))/(r**S(2) + S(2)*r*s*x*cos(Pi*(S(2)*k + S(-1))/n) + s**S(2)*x**S(2)), x)
        u = Int((r*cos(Pi*m*(2*k - 1)/n) + s*x*cos(Pi*(2*k - 1)*(m + 1)/n))/(r**2 + 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x)
        return Simp(-Dist(2*s**(-m)*(-r)**(m + 1)/(a*n), Sum_doit(u, List(k, 1, n/2 - 1/2)), x) + r**(m + 1)*s**(-m)*Int(1/(r - s*x), x)/(a*n), x)
    pattern785 = Pattern(Integral(x_**WC('m', S(1))/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons523, cons62, cons522, cons469)
    rule785 = ReplacementRule(pattern785, With785)
    def With786(m, b, a, n, x):
        r = Numerator(Rt(a/b, n))
        s = Denominator(Rt(a/b, n))
        k = Symbol('k')
        u = Symbol('u')
        u = Int((r*cos(Pi*m*(S(2)*k + S(-1))/n) - s*x*cos(Pi*(S(2)*k + S(-1))*(m + S(1))/n))/(r**S(2) - S(2)*r*s*x*cos(Pi*(S(2)*k + S(-1))/n) + s**S(2)*x**S(2)), x) + Int((r*cos(Pi*m*(S(2)*k + S(-1))/n) + s*x*cos(Pi*(S(2)*k + S(-1))*(m + S(1))/n))/(r**S(2) + S(2)*r*s*x*cos(Pi*(S(2)*k + S(-1))/n) + s**S(2)*x**S(2)), x)
        u = Int((r*cos(Pi*m*(2*k - 1)/n) - s*x*cos(Pi*(2*k - 1)*(m + 1)/n))/(r**2 - 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x) + Int((r*cos(Pi*m*(2*k - 1)/n) + s*x*cos(Pi*(2*k - 1)*(m + 1)/n))/(r**2 + 2*r*s*x*cos(Pi*(2*k - 1)/n) + s**2*x**2), x)
        return Simp(2*(-1)**(m/2)*r**(m + 2)*s**(-m)*Int(1/(r**2 + s**2*x**2), x)/(a*n) + Dist(2*r**(m + 1)*s**(-m)/(a*n), Sum_doit(u, List(k, 1, n/4 - 1/2)), x), x)
    pattern786 = Pattern(Integral(x_**WC('m', S(1))/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons524, cons62, cons522, cons468)
    rule786 = ReplacementRule(pattern786, With786)
    def With787(m, b, a, n, x):
        r = Numerator(Rt(-a/b, n))
        s = Denominator(Rt(-a/b, n))
        k = Symbol('k')
        u = Symbol('u')
        u = Int((r*cos(S(2)*Pi*k*m/n) - s*x*cos(S(2)*Pi*k*(m + S(1))/n))/(r**S(2) - S(2)*r*s*x*cos(S(2)*Pi*k/n) + s**S(2)*x**S(2)), x) + Int((r*cos(S(2)*Pi*k*m/n) + s*x*cos(S(2)*Pi*k*(m + S(1))/n))/(r**S(2) + S(2)*r*s*x*cos(S(2)*Pi*k/n) + s**S(2)*x**S(2)), x)
        u = Int((r*cos(2*Pi*k*m/n) - s*x*cos(2*Pi*k*(m + 1)/n))/(r**2 - 2*r*s*x*cos(2*Pi*k/n) + s**2*x**2), x) + Int((r*cos(2*Pi*k*m/n) + s*x*cos(2*Pi*k*(m + 1)/n))/(r**2 + 2*r*s*x*cos(2*Pi*k/n) + s**2*x**2), x)
        return Simp(Dist(2*r**(m + 1)*s**(-m)/(a*n), Sum_doit(u, List(k, 1, n/4 - 1/2)), x) + 2*r**(m + 2)*s**(-m)*Int(1/(r**2 - s**2*x**2), x)/(a*n), x)
    pattern787 = Pattern(Integral(x_**WC('m', S(1))/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons524, cons62, cons522, cons469)
    rule787 = ReplacementRule(pattern787, With787)
    def With788(x, a, b):
        r = Numerator(Rt(a/b, S(2)))
        s = Denominator(Rt(a/b, S(2)))
        rubi.append(788)
        return -Dist(S(1)/(S(2)*s), Int((r - s*x**S(2))/(a + b*x**S(4)), x), x) + Dist(S(1)/(S(2)*s), Int((r + s*x**S(2))/(a + b*x**S(4)), x), x)
    pattern788 = Pattern(Integral(x_**S(2)/(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons475)
    rule788 = ReplacementRule(pattern788, With788)
    def With789(x, a, b):
        r = Numerator(Rt(-a/b, S(2)))
        s = Denominator(Rt(-a/b, S(2)))
        rubi.append(789)
        return -Dist(s/(S(2)*b), Int(S(1)/(r - s*x**S(2)), x), x) + Dist(s/(S(2)*b), Int(S(1)/(r + s*x**S(2)), x), x)
    pattern789 = Pattern(Integral(x_**S(2)/(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons476)
    rule789 = ReplacementRule(pattern789, With789)
    def With790(m, b, a, n, x):
        r = Numerator(Rt(a/b, S(4)))
        s = Denominator(Rt(a/b, S(4)))
        rubi.append(790)
        return Dist(sqrt(S(2))*s**S(3)/(S(4)*b*r), Int(x**(m - n/S(4))/(r**S(2) - sqrt(S(2))*r*s*x**(n/S(4)) + s**S(2)*x**(n/S(2))), x), x) - Dist(sqrt(S(2))*s**S(3)/(S(4)*b*r), Int(x**(m - n/S(4))/(r**S(2) + sqrt(S(2))*r*s*x**(n/S(4)) + s**S(2)*x**(n/S(2))), x), x)
    pattern790 = Pattern(Integral(x_**WC('m', S(1))/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons525, cons62, cons522, cons478)
    rule790 = ReplacementRule(pattern790, With790)
    def With791(m, b, a, n, x):
        r = Numerator(Rt(-a/b, S(2)))
        s = Denominator(Rt(-a/b, S(2)))
        rubi.append(791)
        return Dist(r/(S(2)*a), Int(x**m/(r - s*x**(n/S(2))), x), x) + Dist(r/(S(2)*a), Int(x**m/(r + s*x**(n/S(2))), x), x)
    pattern791 = Pattern(Integral(x_**m_/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons525, cons62, cons526, cons476)
    rule791 = ReplacementRule(pattern791, With791)
    def With792(m, b, a, n, x):
        r = Numerator(Rt(-a/b, S(2)))
        s = Denominator(Rt(-a/b, S(2)))
        rubi.append(792)
        return -Dist(s/(S(2)*b), Int(x**(m - n/S(2))/(r - s*x**(n/S(2))), x), x) + Dist(s/(S(2)*b), Int(x**(m - n/S(2))/(r + s*x**(n/S(2))), x), x)
    pattern792 = Pattern(Integral(x_**m_/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons525, cons62, cons527, cons476)
    rule792 = ReplacementRule(pattern792, With792)
    pattern793 = Pattern(Integral(x_**m_/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons528, cons529)
    def replacement793(m, b, a, n, x):
        rubi.append(793)
        return Int(PolynomialDivide(x**m, a + b*x**n, x), x)
    rule793 = ReplacementRule(pattern793, replacement793)
    def With794(x, a, b):
        r = Numer(Rt(b/a, S(3)))
        s = Denom(Rt(b/a, S(3)))
        rubi.append(794)
        return Dist(S(1)/r, Int((r*x + s*(-sqrt(S(3)) + S(1)))/sqrt(a + b*x**S(3)), x), x) + Dist(sqrt(S(2))*s/(r*sqrt(sqrt(S(3)) + S(2))), Int(S(1)/sqrt(a + b*x**S(3)), x), x)
    pattern794 = Pattern(Integral(x_/sqrt(a_ + x_**S(3)*WC('b', S(1))), x_), cons2, cons3, cons481)
    rule794 = ReplacementRule(pattern794, With794)
    def With795(x, a, b):
        r = Numer(Rt(b/a, S(3)))
        s = Denom(Rt(b/a, S(3)))
        rubi.append(795)
        return Dist(S(1)/r, Int((r*x + s*(S(1) + sqrt(S(3))))/sqrt(a + b*x**S(3)), x), x) - Dist(sqrt(S(2))*s/(r*sqrt(-sqrt(S(3)) + S(2))), Int(S(1)/sqrt(a + b*x**S(3)), x), x)
    pattern795 = Pattern(Integral(x_/sqrt(a_ + x_**S(3)*WC('b', S(1))), x_), cons2, cons3, cons482)
    rule795 = ReplacementRule(pattern795, With795)
    def With796(x, a, b):
        q = Rt(b/a, S(2))
        rubi.append(796)
        return -Dist(S(1)/q, Int((-q*x**S(2) + S(1))/sqrt(a + b*x**S(4)), x), x) + Dist(S(1)/q, Int(S(1)/sqrt(a + b*x**S(4)), x), x)
    pattern796 = Pattern(Integral(x_**S(2)/sqrt(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons466)
    rule796 = ReplacementRule(pattern796, With796)
    def With797(x, a, b):
        q = Rt(-b/a, S(2))
        rubi.append(797)
        return -Dist(S(1)/q, Int((-q*x**S(2) + S(1))/sqrt(a + b*x**S(4)), x), x) + Dist(S(1)/q, Int(S(1)/sqrt(a + b*x**S(4)), x), x)
    pattern797 = Pattern(Integral(x_**S(2)/sqrt(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons484, cons105)
    rule797 = ReplacementRule(pattern797, With797)
    def With798(x, a, b):
        q = Rt(-b/a, S(2))
        rubi.append(798)
        return Dist(S(1)/q, Int((q*x**S(2) + S(1))/sqrt(a + b*x**S(4)), x), x) - Dist(S(1)/q, Int(S(1)/sqrt(a + b*x**S(4)), x), x)
    pattern798 = Pattern(Integral(x_**S(2)/sqrt(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons483)
    rule798 = ReplacementRule(pattern798, With798)
    def With799(x, a, b):
        r = Numer(Rt(b/a, S(3)))
        s = Denom(Rt(b/a, S(3)))
        rubi.append(799)
        return -Dist(S(1)/(S(2)*r**S(2)), Int((-S(2)*r**S(2)*x**S(4) + s**S(2)*(S(-1) + sqrt(S(3))))/sqrt(a + b*x**S(6)), x), x) + Dist(s**S(2)*(S(-1) + sqrt(S(3)))/(S(2)*r**S(2)), Int(S(1)/sqrt(a + b*x**S(6)), x), x)
    pattern799 = Pattern(Integral(x_**S(4)/sqrt(a_ + x_**S(6)*WC('b', S(1))), x_), cons2, cons3, cons67)
    rule799 = ReplacementRule(pattern799, With799)
    pattern800 = Pattern(Integral(x_**S(2)/sqrt(a_ + x_**S(8)*WC('b', S(1))), x_), cons2, cons3, cons67)
    def replacement800(x, a, b):
        rubi.append(800)
        return -Dist(S(1)/(S(2)*Rt(b/a, S(4))), Int((-x**S(2)*Rt(b/a, S(4)) + S(1))/sqrt(a + b*x**S(8)), x), x) + Dist(S(1)/(S(2)*Rt(b/a, S(4))), Int((x**S(2)*Rt(b/a, S(4)) + S(1))/sqrt(a + b*x**S(8)), x), x)
    rule800 = ReplacementRule(pattern800, replacement800)
    pattern801 = Pattern(Integral(x_**S(2)/(a_ + x_**S(4)*WC('b', S(1)))**(S(1)/4), x_), cons2, cons3, cons466)
    def replacement801(x, a, b):
        rubi.append(801)
        return -Dist(a/S(2), Int(x**S(2)/(a + b*x**S(4))**(S(5)/4), x), x) + Simp(x**S(3)/(S(2)*(a + b*x**S(4))**(S(1)/4)), x)
    rule801 = ReplacementRule(pattern801, replacement801)
    pattern802 = Pattern(Integral(x_**S(2)/(a_ + x_**S(4)*WC('b', S(1)))**(S(1)/4), x_), cons2, cons3, cons483)
    def replacement802(x, a, b):
        rubi.append(802)
        return Dist(a/(S(2)*b), Int(S(1)/(x**S(2)*(a + b*x**S(4))**(S(1)/4)), x), x) + Simp((a + b*x**S(4))**(S(3)/4)/(S(2)*b*x), x)
    rule802 = ReplacementRule(pattern802, replacement802)
    pattern803 = Pattern(Integral(S(1)/(x_**S(2)*(a_ + x_**S(4)*WC('b', S(1)))**(S(1)/4)), x_), cons2, cons3, cons466)
    def replacement803(x, a, b):
        rubi.append(803)
        return -Dist(b, Int(x**S(2)/(a + b*x**S(4))**(S(5)/4), x), x) - Simp(S(1)/(x*(a + b*x**S(4))**(S(1)/4)), x)
    rule803 = ReplacementRule(pattern803, replacement803)
    pattern804 = Pattern(Integral(S(1)/(x_**S(2)*(a_ + x_**S(4)*WC('b', S(1)))**(S(1)/4)), x_), cons2, cons3, cons483)
    def replacement804(x, a, b):
        rubi.append(804)
        return Dist(x*(a/(b*x**S(4)) + S(1))**(S(1)/4)/(a + b*x**S(4))**(S(1)/4), Int(S(1)/(x**S(3)*(a/(b*x**S(4)) + S(1))**(S(1)/4)), x), x)
    rule804 = ReplacementRule(pattern804, replacement804)
    pattern805 = Pattern(Integral(sqrt(c_*x_)/(a_ + x_**S(2)*WC('b', S(1)))**(S(1)/4), x_), cons2, cons3, cons7, cons466)
    def replacement805(x, c, b, a):
        rubi.append(805)
        return -Dist(a/S(2), Int(sqrt(c*x)/(a + b*x**S(2))**(S(5)/4), x), x) + Simp(x*sqrt(c*x)/(a + b*x**S(2))**(S(1)/4), x)
    rule805 = ReplacementRule(pattern805, replacement805)
    pattern806 = Pattern(Integral(sqrt(c_*x_)/(a_ + x_**S(2)*WC('b', S(1)))**(S(1)/4), x_), cons2, cons3, cons7, cons483)
    def replacement806(x, c, b, a):
        rubi.append(806)
        return Dist(a*c**S(2)/(S(2)*b), Int(S(1)/((c*x)**(S(3)/2)*(a + b*x**S(2))**(S(1)/4)), x), x) + Simp(c*(a + b*x**S(2))**(S(3)/4)/(b*sqrt(c*x)), x)
    rule806 = ReplacementRule(pattern806, replacement806)
    pattern807 = Pattern(Integral(S(1)/((x_*WC('c', S(1)))**(S(3)/2)*(a_ + x_**S(2)*WC('b', S(1)))**(S(1)/4)), x_), cons2, cons3, cons7, cons466)
    def replacement807(x, c, b, a):
        rubi.append(807)
        return -Dist(b/c**S(2), Int(sqrt(c*x)/(a + b*x**S(2))**(S(5)/4), x), x) + Simp(-S(2)/(c*sqrt(c*x)*(a + b*x**S(2))**(S(1)/4)), x)
    rule807 = ReplacementRule(pattern807, replacement807)
    pattern808 = Pattern(Integral(S(1)/((x_*WC('c', S(1)))**(S(3)/2)*(a_ + x_**S(2)*WC('b', S(1)))**(S(1)/4)), x_), cons2, cons3, cons7, cons483)
    def replacement808(x, c, b, a):
        rubi.append(808)
        return Dist(sqrt(c*x)*(a/(b*x**S(2)) + S(1))**(S(1)/4)/(c**S(2)*(a + b*x**S(2))**(S(1)/4)), Int(S(1)/(x**S(2)*(a/(b*x**S(2)) + S(1))**(S(1)/4)), x), x)
    rule808 = ReplacementRule(pattern808, replacement808)
    pattern809 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons5, cons148, cons31, cons530, cons512, cons509)
    def replacement809(p, m, b, c, a, n, x):
        rubi.append(809)
        return -Dist(a*c**n*(m - n + S(1))/(b*(m + n*p + S(1))), Int((c*x)**(m - n)*(a + b*x**n)**p, x), x) + Simp(c**(n + S(-1))*(c*x)**(m - n + S(1))*(a + b*x**n)**(p + S(1))/(b*(m + n*p + S(1))), x)
    rule809 = ReplacementRule(pattern809, replacement809)
    pattern810 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons5, cons148, cons531, cons512, cons532)
    def replacement810(p, m, b, c, a, n, x):
        rubi.append(810)
        return -Dist(a*c**n*(m - n + S(1))/(b*(m + n*p + S(1))), Int((c*x)**(m - n)*(a + b*x**n)**p, x), x) + Simp(c**(n + S(-1))*(c*x)**(m - n + S(1))*(a + b*x**n)**(p + S(1))/(b*(m + n*p + S(1))), x)
    rule810 = ReplacementRule(pattern810, replacement810)
    pattern811 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons5, cons55, cons495, cons31, cons529, cons510, cons511)
    def replacement811(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(811)
        return -Dist(a1*a2*c**(S(2)*n)*(m - S(2)*n + S(1))/(b1*b2*(m + S(2)*n*p + S(1))), Int((c*x)**(m - S(2)*n)*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x) + Simp(c**(S(2)*n + S(-1))*(c*x)**(m - S(2)*n + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(b1*b2*(m + S(2)*n*p + S(1))), x)
    rule811 = ReplacementRule(pattern811, replacement811)
    pattern812 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons5, cons55, cons495, cons533, cons510, cons534)
    def replacement812(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(812)
        return -Dist(a1*a2*c**(S(2)*n)*(m - S(2)*n + S(1))/(b1*b2*(m + S(2)*n*p + S(1))), Int((c*x)**(m - S(2)*n)*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x) + Simp(c**(S(2)*n + S(-1))*(c*x)**(m - S(2)*n + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(b1*b2*(m + S(2)*n*p + S(1))), x)
    rule812 = ReplacementRule(pattern812, replacement812)
    pattern813 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons5, cons148, cons31, cons94, cons509)
    def replacement813(p, m, b, c, a, n, x):
        rubi.append(813)
        return -Dist(b*c**(-n)*(m + n*(p + S(1)) + S(1))/(a*(m + S(1))), Int((c*x)**(m + n)*(a + b*x**n)**p, x), x) + Simp((c*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*c*(m + S(1))), x)
    rule813 = ReplacementRule(pattern813, replacement813)
    pattern814 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons5, cons148, cons535, cons532)
    def replacement814(p, m, b, c, a, n, x):
        rubi.append(814)
        return -Dist(b*c**(-n)*(m + n*(p + S(1)) + S(1))/(a*(m + S(1))), Int((c*x)**(m + n)*(a + b*x**n)**p, x), x) + Simp((c*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*c*(m + S(1))), x)
    rule814 = ReplacementRule(pattern814, replacement814)
    pattern815 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons5, cons55, cons495, cons31, cons94, cons511)
    def replacement815(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(815)
        return -Dist(b1*b2*c**(-S(2)*n)*(m + S(2)*n*(p + S(1)) + S(1))/(a1*a2*(m + S(1))), Int((c*x)**(m + S(2)*n)*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x) + Simp((c*x)**(m + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(a1*a2*c*(m + S(1))), x)
    rule815 = ReplacementRule(pattern815, replacement815)
    pattern816 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons5, cons55, cons495, cons536, cons534)
    def replacement816(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(816)
        return -Dist(b1*b2*c**(-S(2)*n)*(m + S(2)*n*(p + S(1)) + S(1))/(a1*a2*(m + S(1))), Int((c*x)**(m + S(2)*n)*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x) + Simp((c*x)**(m + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(a1*a2*c*(m + S(1))), x)
    rule816 = ReplacementRule(pattern816, replacement816)
    def With817(p, m, b, c, a, n, x):
        k = Denominator(m)
        rubi.append(817)
        return Dist(k/c, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a + b*c**(-n)*x**(k*n))**p, x), x, (c*x)**(S(1)/k)), x)
    pattern817 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons5, cons148, cons367, cons509)
    rule817 = ReplacementRule(pattern817, With817)
    def With818(p, a2, m, b2, b1, c, n, x, a1):
        k = Denominator(m)
        rubi.append(818)
        return Dist(k/c, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a1 + b1*c**(-n)*x**(k*n))**p*(a2 + b2*c**(-n)*x**(k*n))**p, x), x, (c*x)**(S(1)/k)), x)
    pattern818 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons5, cons55, cons495, cons367, cons511)
    rule818 = ReplacementRule(pattern818, With818)
    pattern819 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons148, cons13, cons485, cons486, cons537)
    def replacement819(p, m, b, a, n, x):
        rubi.append(819)
        return Dist(a**(p + (m + S(1))/n), Subst(Int(x**m*(-b*x**n + S(1))**(-p + S(-1) - (m + S(1))/n), x), x, x*(a + b*x**n)**(-S(1)/n)), x)
    rule819 = ReplacementRule(pattern819, replacement819)
    pattern820 = Pattern(Integral(x_**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons55, cons495, cons13, cons485, cons486, cons538)
    def replacement820(p, a2, m, b2, b1, n, x, a1):
        rubi.append(820)
        return Dist((a1*a2)**(p + (m + S(1))/(S(2)*n)), Subst(Int(x**m*(-b1*x**n + S(1))**(-p + S(-1) - (m + S(1))/(S(2)*n))*(-b2*x**n + S(1))**(-p + S(-1) - (m + S(1))/(S(2)*n)), x), x, x*(a1 + b1*x**n)**(-S(1)/(S(2)*n))*(a2 + b2*x**n)**(-S(1)/(S(2)*n))), x)
    rule820 = ReplacementRule(pattern820, replacement820)
    pattern821 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons148, cons13, cons485, cons486, cons17, cons539)
    def replacement821(p, m, b, a, n, x):
        rubi.append(821)
        return Dist((a/(a + b*x**n))**(p + (m + S(1))/n)*(a + b*x**n)**(p + (m + S(1))/n), Subst(Int(x**m*(-b*x**n + S(1))**(-p + S(-1) - (m + S(1))/n), x), x, x*(a + b*x**n)**(-S(1)/n)), x)
    rule821 = ReplacementRule(pattern821, replacement821)
    pattern822 = Pattern(Integral(x_**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons55, cons495, cons13, cons485, cons486, cons17, cons540)
    def replacement822(p, a2, m, b2, b1, n, x, a1):
        rubi.append(822)
        return Dist((a1/(a1 + b1*x**n))**(p + (m + S(1))/(S(2)*n))*(a2/(a2 + b2*x**n))**(p + (m + S(1))/(S(2)*n))*(a1 + b1*x**n)**(p + (m + S(1))/(S(2)*n))*(a2 + b2*x**n)**(p + (m + S(1))/(S(2)*n)), Subst(Int(x**m*(-b1*x**n + S(1))**(-p + S(-1) - (m + S(1))/(S(2)*n))*(-b2*x**n + S(1))**(-p + S(-1) - (m + S(1))/(S(2)*n)), x), x, x*(a1 + b1*x**n)**(-S(1)/(S(2)*n))*(a2 + b2*x**n)**(-S(1)/(S(2)*n))), x)
    rule822 = ReplacementRule(pattern822, replacement822)
    pattern823 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons5, cons196, cons17)
    def replacement823(p, m, b, a, n, x):
        rubi.append(823)
        return -Subst(Int(x**(-m + S(-2))*(a + b*x**(-n))**p, x), x, S(1)/x)
    rule823 = ReplacementRule(pattern823, replacement823)
    pattern824 = Pattern(Integral(x_**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons5, cons55, cons497, cons17)
    def replacement824(p, a2, m, b2, b1, n, x, a1):
        rubi.append(824)
        return -Subst(Int(x**(-m + S(-2))*(a1 + b1*x**(-n))**p*(a2 + b2*x**(-n))**p, x), x, S(1)/x)
    rule824 = ReplacementRule(pattern824, replacement824)
    def With825(p, m, b, c, a, n, x):
        k = Denominator(m)
        rubi.append(825)
        return -Dist(k/c, Subst(Int(x**(-k*(m + S(1)) + S(-1))*(a + b*c**(-n)*x**(-k*n))**p, x), x, (c*x)**(-S(1)/k)), x)
    pattern825 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons5, cons196, cons367)
    rule825 = ReplacementRule(pattern825, With825)
    def With826(p, a2, m, b2, b1, c, n, x, a1):
        k = Denominator(m)
        rubi.append(826)
        return -Dist(k/c, Subst(Int(x**(-k*(m + S(1)) + S(-1))*(a1 + b1*c**(-n)*x**(-k*n))**p*(a2 + b2*c**(-n)*x**(-k*n))**p, x), x, (c*x)**(-S(1)/k)), x)
    pattern826 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons5, cons55, cons497, cons367)
    rule826 = ReplacementRule(pattern826, With826)
    pattern827 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons5, cons196, cons356)
    def replacement827(p, m, b, c, a, n, x):
        rubi.append(827)
        return -Dist((c*x)**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(a + b*x**(-n))**p, x), x, S(1)/x), x)
    rule827 = ReplacementRule(pattern827, replacement827)
    pattern828 = Pattern(Integral((x_*WC('c', S(1)))**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons5, cons55, cons497, cons356)
    def replacement828(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(828)
        return -Dist((c*x)**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(a1 + b1*x**(-n))**p*(a2 + b2*x**(-n))**p, x), x, S(1)/x), x)
    rule828 = ReplacementRule(pattern828, replacement828)
    def With829(p, m, b, a, n, x):
        k = Denominator(n)
        rubi.append(829)
        return Dist(k, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a + b*x**(k*n))**p, x), x, x**(S(1)/k)), x)
    pattern829 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons21, cons5, cons489)
    rule829 = ReplacementRule(pattern829, With829)
    def With830(p, a2, m, b2, b1, n, x, a1):
        k = Denominator(S(2)*n)
        rubi.append(830)
        return Dist(k, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a1 + b1*x**(k*n))**p*(a2 + b2*x**(k*n))**p, x), x, x**(S(1)/k)), x)
    pattern830 = Pattern(Integral(x_**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons21, cons5, cons55, cons498)
    rule830 = ReplacementRule(pattern830, With830)
    pattern831 = Pattern(Integral((c_*x_)**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons5, cons489)
    def replacement831(p, m, b, c, a, n, x):
        rubi.append(831)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a + b*x**n)**p, x), x)
    rule831 = ReplacementRule(pattern831, replacement831)
    pattern832 = Pattern(Integral((c_*x_)**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons5, cons55, cons498)
    def replacement832(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(832)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x)
    rule832 = ReplacementRule(pattern832, replacement832)
    pattern833 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons21, cons4, cons5, cons541, cons23)
    def replacement833(p, m, b, a, n, x):
        rubi.append(833)
        return Dist(S(1)/(m + S(1)), Subst(Int((a + b*x**(n/(m + S(1))))**p, x), x, x**(m + S(1))), x)
    rule833 = ReplacementRule(pattern833, replacement833)
    pattern834 = Pattern(Integral(x_**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons21, cons4, cons5, cons55, cons542, cons543)
    def replacement834(p, a2, m, b2, b1, n, x, a1):
        rubi.append(834)
        return Dist(S(1)/(m + S(1)), Subst(Int((a1 + b1*x**(n/(m + S(1))))**p*(a2 + b2*x**(n/(m + S(1))))**p, x), x, x**(m + S(1))), x)
    rule834 = ReplacementRule(pattern834, replacement834)
    pattern835 = Pattern(Integral((c_*x_)**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons5, cons541, cons23)
    def replacement835(p, m, b, c, a, n, x):
        rubi.append(835)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a + b*x**n)**p, x), x)
    rule835 = ReplacementRule(pattern835, replacement835)
    pattern836 = Pattern(Integral((c_*x_)**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons5, cons55, cons542, cons543)
    def replacement836(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(836)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x)
    rule836 = ReplacementRule(pattern836, replacement836)
    pattern837 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons21, cons4, cons544, cons13, cons163)
    def replacement837(p, m, b, a, n, x):
        rubi.append(837)
        return -Dist(b*n*p/(m + S(1)), Int(x**(m + n)*(a + b*x**n)**(p + S(-1)), x), x) + Simp(x**(m + S(1))*(a + b*x**n)**p/(m + S(1)), x)
    rule837 = ReplacementRule(pattern837, replacement837)
    pattern838 = Pattern(Integral(x_**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons21, cons4, cons55, cons545, cons13, cons163)
    def replacement838(p, a2, m, b2, b1, n, x, a1):
        rubi.append(838)
        return -Dist(S(2)*b1*b2*n*p/(m + S(1)), Int(x**(m + n)*(a1 + b1*x**n)**(p + S(-1))*(a2 + b2*x**n)**(p + S(-1)), x), x) + Simp(x**(m + S(1))*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p/(m + S(1)), x)
    rule838 = ReplacementRule(pattern838, replacement838)
    pattern839 = Pattern(Integral((c_*x_)**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons544, cons13, cons163)
    def replacement839(p, m, b, c, a, n, x):
        rubi.append(839)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a + b*x**n)**p, x), x)
    rule839 = ReplacementRule(pattern839, replacement839)
    pattern840 = Pattern(Integral((c_*x_)**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons55, cons545, cons13, cons163)
    def replacement840(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(840)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x)
    rule840 = ReplacementRule(pattern840, replacement840)
    pattern841 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons546, cons13, cons163, cons512)
    def replacement841(p, m, b, c, a, n, x):
        rubi.append(841)
        return Dist(a*n*p/(m + n*p + S(1)), Int((c*x)**m*(a + b*x**n)**(p + S(-1)), x), x) + Simp((c*x)**(m + S(1))*(a + b*x**n)**p/(c*(m + n*p + S(1))), x)
    rule841 = ReplacementRule(pattern841, replacement841)
    pattern842 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons55, cons547, cons13, cons163, cons510)
    def replacement842(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(842)
        return Dist(S(2)*a1*a2*n*p/(m + S(2)*n*p + S(1)), Int((c*x)**m*(a1 + b1*x**n)**(p + S(-1))*(a2 + b2*x**n)**(p + S(-1)), x), x) + Simp((c*x)**(m + S(1))*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p/(c*(m + S(2)*n*p + S(1))), x)
    rule842 = ReplacementRule(pattern842, replacement842)
    def With843(p, m, b, a, n, x):
        k = Denominator(p)
        rubi.append(843)
        return Dist(a**(p + (m + S(1))/n)*k/n, Subst(Int(x**(k*(m + S(1))/n + S(-1))*(-b*x**k + S(1))**(-p + S(-1) - (m + S(1))/n), x), x, x**(n/k)*(a + b*x**n)**(-S(1)/k)), x)
    pattern843 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons21, cons4, cons546, cons13, cons485)
    rule843 = ReplacementRule(pattern843, With843)
    def With844(p, a2, m, b2, b1, n, x, a1):
        k = Denominator(p)
        rubi.append(844)
        return Dist(k*(a1*a2)**(p + (m + S(1))/(S(2)*n))/(S(2)*n), Subst(Int(x**(k*(m + S(1))/(S(2)*n) + S(-1))*(-b1*x**k + S(1))**(-p + S(-1) - (m + S(1))/(S(2)*n))*(-b2*x**k + S(1))**(-p + S(-1) - (m + S(1))/(S(2)*n)), x), x, x**(S(2)*n/k)*(a1 + b1*x**n)**(-S(1)/k)*(a2 + b2*x**n)**(-S(1)/k)), x)
    pattern844 = Pattern(Integral(x_**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons21, cons4, cons55, cons547, cons13, cons485)
    rule844 = ReplacementRule(pattern844, With844)
    pattern845 = Pattern(Integral((c_*x_)**m_*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons546, cons13, cons485)
    def replacement845(p, m, b, c, a, n, x):
        rubi.append(845)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a + b*x**n)**p, x), x)
    rule845 = ReplacementRule(pattern845, replacement845)
    pattern846 = Pattern(Integral((c_*x_)**m_*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons55, cons547, cons13, cons485)
    def replacement846(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(846)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m*(a1 + b1*x**n)**p*(a2 + b2*x**n)**p, x), x)
    rule846 = ReplacementRule(pattern846, replacement846)
    pattern847 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons546, cons13, cons137)
    def replacement847(p, m, b, c, a, n, x):
        rubi.append(847)
        return Dist((m + n*(p + S(1)) + S(1))/(a*n*(p + S(1))), Int((c*x)**m*(a + b*x**n)**(p + S(1)), x), x) - Simp((c*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*c*n*(p + S(1))), x)
    rule847 = ReplacementRule(pattern847, replacement847)
    pattern848 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons55, cons546, cons13, cons137)
    def replacement848(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(848)
        return Dist((m + S(2)*n*(p + S(1)) + S(1))/(S(2)*a1*a2*n*(p + S(1))), Int((c*x)**m*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1)), x), x) - Simp((c*x)**(m + S(1))*(a1 + b1*x**n)**(p + S(1))*(a2 + b2*x**n)**(p + S(1))/(S(2)*a1*a2*c*n*(p + S(1))), x)
    rule848 = ReplacementRule(pattern848, replacement848)
    def With849(m, b, a, n, x):
        mn = m - n
        rubi.append(849)
        return -Dist(a/b, Int(x**mn/(a + b*x**n), x), x) + Simp(x**(mn + S(1))/(b*(mn + S(1))), x)
    pattern849 = Pattern(Integral(x_**WC('m', S(1))/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons21, cons4, cons548, cons531)
    rule849 = ReplacementRule(pattern849, With849)
    pattern850 = Pattern(Integral(x_**m_/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons21, cons4, cons548, cons535)
    def replacement850(m, b, a, n, x):
        rubi.append(850)
        return -Dist(b/a, Int(x**(m + n)/(a + b*x**n), x), x) + Simp(x**(m + S(1))/(a*(m + S(1))), x)
    rule850 = ReplacementRule(pattern850, replacement850)
    pattern851 = Pattern(Integral((c_*x_)**m_/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons7, cons21, cons4, cons548, cons549)
    def replacement851(m, b, c, a, n, x):
        rubi.append(851)
        return Dist(c**IntPart(m)*x**(-FracPart(m))*(c*x)**FracPart(m), Int(x**m/(a + b*x**n), x), x)
    rule851 = ReplacementRule(pattern851, replacement851)
    pattern852 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons5, cons357, cons550)
    def replacement852(p, m, b, c, a, n, x):
        rubi.append(852)
        return Simp(a**p*(c*x)**(m + S(1))*Hypergeometric2F1(-p, (m + S(1))/n, S(1) + (m + S(1))/n, -b*x**n/a)/(c*(m + S(1))), x)
    rule852 = ReplacementRule(pattern852, replacement852)
    pattern853 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons21, cons4, cons5, cons357, cons551)
    def replacement853(p, m, b, c, a, n, x):
        rubi.append(853)
        return Dist(a**IntPart(p)*(S(1) + b*x**n/a)**(-FracPart(p))*(a + b*x**n)**FracPart(p), Int((c*x)**m*(S(1) + b*x**n/a)**p, x), x)
    rule853 = ReplacementRule(pattern853, replacement853)
    pattern854 = Pattern(Integral(x_**WC('m', S(1))*(a_ + v_**n_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons4, cons5, cons552, cons17, cons553)
    def replacement854(v, p, m, b, a, n, x):
        rubi.append(854)
        return Dist(Coefficient(v, x, S(1))**(-m + S(-1)), Subst(Int(SimplifyIntegrand((a + b*x**n)**p*(x - Coefficient(v, x, S(0)))**m, x), x), x, v), x)
    rule854 = ReplacementRule(pattern854, replacement854)
    pattern855 = Pattern(Integral(u_**WC('m', S(1))*(a_ + v_**n_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons21, cons4, cons5, cons554)
    def replacement855(v, p, u, m, b, a, n, x):
        rubi.append(855)
        return Dist(u**m*v**(-m)/Coefficient(v, x, S(1)), Subst(Int(x**m*(a + b*x**n)**p, x), x, v), x)
    rule855 = ReplacementRule(pattern855, replacement855)
    pattern856 = Pattern(Integral((x_*WC('c', S(1)))**WC('m', S(1))*(a1_ + x_**n_*WC('b1', S(1)))**p_*(a2_ + x_**n_*WC('b2', S(1)))**p_, x_), cons57, cons58, cons59, cons60, cons7, cons21, cons4, cons5, cons55, cons147)
    def replacement856(p, a2, m, b2, b1, c, n, x, a1):
        rubi.append(856)
        return Dist((a1 + b1*x**n)**FracPart(p)*(a2 + b2*x**n)**FracPart(p)*(a1*a2 + b1*b2*x**(S(2)*n))**(-FracPart(p)), Int((c*x)**m*(a1*a2 + b1*b2*x**(S(2)*n))**p, x), x)
    rule856 = ReplacementRule(pattern856, replacement856)
    pattern857 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons71, cons555)
    def replacement857(p, b, d, a, n, c, x, q):
        rubi.append(857)
        return Int(ExpandIntegrand((a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule857 = ReplacementRule(pattern857, replacement857)
    pattern858 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons71, cons220, cons502)
    def replacement858(p, b, d, a, n, c, x, q):
        rubi.append(858)
        return Int(x**(n*(p + q))*(a*x**(-n) + b)**p*(c*x**(-n) + d)**q, x)
    rule858 = ReplacementRule(pattern858, replacement858)
    pattern859 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons5, cons50, cons71, cons196)
    def replacement859(p, b, d, a, n, c, x, q):
        rubi.append(859)
        return -Subst(Int((a + b*x**(-n))**p*(c + d*x**(-n))**q/x**S(2), x), x, S(1)/x)
    rule859 = ReplacementRule(pattern859, replacement859)
    def With860(p, b, d, a, n, c, x, q):
        g = Denominator(n)
        rubi.append(860)
        return Dist(g, Subst(Int(x**(g + S(-1))*(a + b*x**(g*n))**p*(c + d*x**(g*n))**q, x), x, x**(S(1)/g)), x)
    pattern860 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons5, cons50, cons71, cons489)
    rule860 = ReplacementRule(pattern860, With860)
    pattern861 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_/(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons71, cons556, cons85)
    def replacement861(p, b, d, a, n, c, x):
        rubi.append(861)
        return Subst(Int(S(1)/(c - x**n*(-a*d + b*c)), x), x, x*(a + b*x**n)**(-S(1)/n))
    rule861 = ReplacementRule(pattern861, replacement861)
    pattern862 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons71, cons557, cons395, cons403, cons54)
    def replacement862(p, b, d, a, n, c, x, q):
        rubi.append(862)
        return -Dist(c*q/(a*(p + S(1))), Int((a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1)), x), x) - Simp(x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(a*n*(p + S(1))), x)
    rule862 = ReplacementRule(pattern862, replacement862)
    pattern863 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons50, cons71, cons557, cons63)
    def replacement863(p, b, d, a, n, c, x, q):
        rubi.append(863)
        return Simp(a**p*c**(-p + S(-1))*x*(c + d*x**n)**(-S(1)/n)*Hypergeometric2F1(S(1)/n, -p, S(1) + S(1)/n, -x**n*(-a*d + b*c)/(a*(c + d*x**n))), x)
    rule863 = ReplacementRule(pattern863, replacement863)
    pattern864 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons5, cons50, cons71, cons557)
    def replacement864(p, b, d, a, n, c, x, q):
        rubi.append(864)
        return Simp(x*(c*(a + b*x**n)/(a*(c + d*x**n)))**(-p)*(a + b*x**n)**p*(c + d*x**n)**(-p - S(1)/n)*Hypergeometric2F1(S(1)/n, -p, S(1) + S(1)/n, -x**n*(-a*d + b*c)/(a*(c + d*x**n)))/c, x)
    rule864 = ReplacementRule(pattern864, replacement864)
    pattern865 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons5, cons50, cons71, cons558, cons559)
    def replacement865(p, b, d, a, n, c, x, q):
        rubi.append(865)
        return Simp(x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(a*c), x)
    rule865 = ReplacementRule(pattern865, replacement865)
    pattern866 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons50, cons71, cons558, cons560, cons54)
    def replacement866(p, b, d, a, n, c, x, q):
        rubi.append(866)
        return Dist((b*c + n*(p + S(1))*(-a*d + b*c))/(a*n*(p + S(1))*(-a*d + b*c)), Int((a + b*x**n)**(p + S(1))*(c + d*x**n)**q, x), x) - Simp(b*x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(a*n*(p + S(1))*(-a*d + b*c)), x)
    rule866 = ReplacementRule(pattern866, replacement866)
    pattern867 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons71, cons561)
    def replacement867(p, b, d, a, n, c, x):
        rubi.append(867)
        return Simp(c*x*(a + b*x**n)**(p + S(1))/a, x)
    rule867 = ReplacementRule(pattern867, replacement867)
    pattern868 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons71, cons562)
    def replacement868(p, b, d, a, n, c, x):
        rubi.append(868)
        return -Dist((a*d - b*c*(n*(p + S(1)) + S(1)))/(a*b*n*(p + S(1))), Int((a + b*x**n)**(p + S(1)), x), x) - Simp(x*(a + b*x**n)**(p + S(1))*(-a*d + b*c)/(a*b*n*(p + S(1))), x)
    rule868 = ReplacementRule(pattern868, replacement868)
    pattern869 = Pattern(Integral((c_ + x_**n_*WC('d', S(1)))/(a_ + x_**n_*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons4, cons71, cons87, cons463)
    def replacement869(b, d, a, n, c, x):
        rubi.append(869)
        return -Dist((-a*d + b*c)/a, Int(S(1)/(a*x**(-n) + b), x), x) + Simp(c*x/a, x)
    rule869 = ReplacementRule(pattern869, replacement869)
    pattern870 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons4, cons71, cons563)
    def replacement870(p, b, d, a, n, c, x):
        rubi.append(870)
        return -Dist((a*d - b*c*(n*(p + S(1)) + S(1)))/(b*(n*(p + S(1)) + S(1))), Int((a + b*x**n)**p, x), x) + Simp(d*x*(a + b*x**n)**(p + S(1))/(b*(n*(p + S(1)) + S(1))), x)
    rule870 = ReplacementRule(pattern870, replacement870)
    pattern871 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons71, cons464, cons564, cons565)
    def replacement871(p, b, d, a, n, c, x, q):
        rubi.append(871)
        return Int(PolynomialDivide((a + b*x**n)**p, (c + d*x**n)**(-q), x), x)
    rule871 = ReplacementRule(pattern871, replacement871)
    pattern872 = Pattern(Integral(S(1)/((a_ + x_**n_*WC('b', S(1)))*(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons4, cons71)
    def replacement872(b, d, a, n, c, x):
        rubi.append(872)
        return Dist(b/(-a*d + b*c), Int(S(1)/(a + b*x**n), x), x) - Dist(d/(-a*d + b*c), Int(S(1)/(c + d*x**n), x), x)
    rule872 = ReplacementRule(pattern872, replacement872)
    pattern873 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('b', S(1)))**(S(1)/3)*(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71, cons566, cons466)
    def replacement873(b, d, c, a, x):
        rubi.append(873)
        return Dist(sqrt(S(3))/(S(2)*c), Int(S(1)/((a + b*x**S(2))**(S(1)/3)*(-x*Rt(b/a, S(2)) + sqrt(S(3)))), x), x) + Dist(sqrt(S(3))/(S(2)*c), Int(S(1)/((a + b*x**S(2))**(S(1)/3)*(x*Rt(b/a, S(2)) + sqrt(S(3)))), x), x)
    rule873 = ReplacementRule(pattern873, replacement873)
    pattern874 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('b', S(1)))**(S(1)/3)*(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71, cons566, cons483)
    def replacement874(b, d, c, a, x):
        rubi.append(874)
        return Dist(S(1)/6, Int((-x*Rt(-b/a, S(2)) + S(3))/((a + b*x**S(2))**(S(1)/3)*(c + d*x**S(2))), x), x) + Dist(S(1)/6, Int((x*Rt(-b/a, S(2)) + S(3))/((a + b*x**S(2))**(S(1)/3)*(c + d*x**S(2))), x), x)
    rule874 = ReplacementRule(pattern874, replacement874)
    pattern875 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**(S(2)/3)/(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons71, cons566)
    def replacement875(b, d, c, a, x):
        rubi.append(875)
        return Dist(b/d, Int((a + b*x**S(2))**(S(-1)/3), x), x) - Dist((-a*d + b*c)/d, Int(S(1)/((a + b*x**S(2))**(S(1)/3)*(c + d*x**S(2))), x), x)
    rule875 = ReplacementRule(pattern875, replacement875)
    pattern876 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('b', S(1)))**(S(1)/4)*(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71)
    def replacement876(b, d, c, a, x):
        rubi.append(876)
        return Dist(sqrt(-b*x**S(2)/a)/(S(2)*x), Subst(Int(S(1)/(sqrt(-b*x/a)*(a + b*x)**(S(1)/4)*(c + d*x)), x), x, x**S(2)), x)
    rule876 = ReplacementRule(pattern876, replacement876)
    pattern877 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('b', S(1)))**(S(3)/4)*(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71)
    def replacement877(b, d, c, a, x):
        rubi.append(877)
        return Dist(sqrt(-b*x**S(2)/a)/(S(2)*x), Subst(Int(S(1)/(sqrt(-b*x/a)*(a + b*x)**(S(3)/4)*(c + d*x)), x), x, x**S(2)), x)
    rule877 = ReplacementRule(pattern877, replacement877)
    pattern878 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**WC('p', S(1))/(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons71, cons13, cons163, cons567)
    def replacement878(p, b, d, a, c, x):
        rubi.append(878)
        return Dist(b/d, Int((a + b*x**S(2))**(p + S(-1)), x), x) - Dist((-a*d + b*c)/d, Int((a + b*x**S(2))**(p + S(-1))/(c + d*x**S(2)), x), x)
    rule878 = ReplacementRule(pattern878, replacement878)
    pattern879 = Pattern(Integral((a_ + x_**S(2)*WC('b', S(1)))**p_/(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons71, cons13, cons137, cons568, cons569)
    def replacement879(p, b, d, a, c, x):
        rubi.append(879)
        return Dist(b/(-a*d + b*c), Int((a + b*x**S(2))**p, x), x) - Dist(d/(-a*d + b*c), Int((a + b*x**S(2))**(p + S(1))/(c + d*x**S(2)), x), x)
    rule879 = ReplacementRule(pattern879, replacement879)
    pattern880 = Pattern(Integral(sqrt(a_ + x_**S(4)*WC('b', S(1)))/(c_ + x_**S(4)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons70, cons570)
    def replacement880(b, d, c, a, x):
        rubi.append(880)
        return Dist(a/c, Subst(Int(S(1)/(-S(4)*a*b*x**S(4) + S(1)), x), x, x/sqrt(a + b*x**S(4))), x)
    rule880 = ReplacementRule(pattern880, replacement880)
    def With881(b, d, c, a, x):
        q = Rt(-a*b, S(4))
        rubi.append(881)
        return Simp(a*ArcTan(q*x*(a + q**S(2)*x**S(2))/(a*sqrt(a + b*x**S(4))))/(S(2)*c*q), x) + Simp(a*atanh(q*x*(a - q**S(2)*x**S(2))/(a*sqrt(a + b*x**S(4))))/(S(2)*c*q), x)
    pattern881 = Pattern(Integral(sqrt(a_ + x_**S(4)*WC('b', S(1)))/(c_ + x_**S(4)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons70, cons571)
    rule881 = ReplacementRule(pattern881, With881)
    pattern882 = Pattern(Integral(sqrt(a_ + x_**S(4)*WC('b', S(1)))/(c_ + x_**S(4)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons71)
    def replacement882(b, d, c, a, x):
        rubi.append(882)
        return Dist(b/d, Int(S(1)/sqrt(a + b*x**S(4)), x), x) - Dist((-a*d + b*c)/d, Int(S(1)/(sqrt(a + b*x**S(4))*(c + d*x**S(4))), x), x)
    rule882 = ReplacementRule(pattern882, replacement882)
    pattern883 = Pattern(Integral((a_ + x_**S(4)*WC('b', S(1)))**(S(1)/4)/(c_ + x_**S(4)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons71)
    def replacement883(b, d, c, a, x):
        rubi.append(883)
        return Dist(sqrt(a/(a + b*x**S(4)))*sqrt(a + b*x**S(4)), Subst(Int(S(1)/((c - x**S(4)*(-a*d + b*c))*sqrt(-b*x**S(4) + S(1))), x), x, x/(a + b*x**S(4))**(S(1)/4)), x)
    rule883 = ReplacementRule(pattern883, replacement883)
    pattern884 = Pattern(Integral((a_ + x_**S(4)*WC('b', S(1)))**p_/(c_ + x_**S(4)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons71, cons13, cons572)
    def replacement884(p, b, d, a, c, x):
        rubi.append(884)
        return Dist(b/d, Int((a + b*x**S(4))**(p + S(-1)), x), x) - Dist((-a*d + b*c)/d, Int((a + b*x**S(4))**(p + S(-1))/(c + d*x**S(4)), x), x)
    rule884 = ReplacementRule(pattern884, replacement884)
    pattern885 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(4)*WC('b', S(1)))*(c_ + x_**S(4)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71)
    def replacement885(b, d, c, a, x):
        rubi.append(885)
        return Dist(S(1)/(S(2)*c), Int(S(1)/(sqrt(a + b*x**S(4))*(-x**S(2)*Rt(-d/c, S(2)) + S(1))), x), x) + Dist(S(1)/(S(2)*c), Int(S(1)/(sqrt(a + b*x**S(4))*(x**S(2)*Rt(-d/c, S(2)) + S(1))), x), x)
    rule885 = ReplacementRule(pattern885, replacement885)
    pattern886 = Pattern(Integral(S(1)/((a_ + x_**S(4)*WC('b', S(1)))**(S(3)/4)*(c_ + x_**S(4)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71)
    def replacement886(b, d, c, a, x):
        rubi.append(886)
        return Dist(b/(-a*d + b*c), Int((a + b*x**S(4))**(S(-3)/4), x), x) - Dist(d/(-a*d + b*c), Int((a + b*x**S(4))**(S(1)/4)/(c + d*x**S(4)), x), x)
    rule886 = ReplacementRule(pattern886, replacement886)
    pattern887 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))/(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons466, cons573)
    def replacement887(b, d, c, a, x):
        rubi.append(887)
        return Simp(sqrt(a + b*x**S(2))*EllipticE(ArcTan(x*Rt(d/c, S(2))), S(1) - b*c/(a*d))/(c*sqrt(c*(a + b*x**S(2))/(a*(c + d*x**S(2))))*sqrt(c + d*x**S(2))*Rt(d/c, S(2))), x)
    rule887 = ReplacementRule(pattern887, replacement887)
    pattern888 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons71, cons402, cons137, cons574, cons575)
    def replacement888(p, b, d, a, n, c, x, q):
        rubi.append(888)
        return Dist(S(1)/(a*n*(p + S(1))), Int((a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*Simp(c*(n*(p + S(1)) + S(1)) + d*x**n*(n*(p + q + S(1)) + S(1)), x), x), x) - Simp(x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(a*n*(p + S(1))), x)
    rule888 = ReplacementRule(pattern888, replacement888)
    pattern889 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons71, cons402, cons137, cons576, cons575)
    def replacement889(p, b, d, a, n, c, x, q):
        rubi.append(889)
        return -Dist(S(1)/(a*b*n*(p + S(1))), Int((a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-2))*Simp(c*(a*d - b*c*(n*(p + S(1)) + S(1))) + d*x**n*(a*d*(n*(q + S(-1)) + S(1)) - b*c*(n*(p + q) + S(1))), x), x), x) + Simp(x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*(a*d - b*c)/(a*b*n*(p + S(1))), x)
    rule889 = ReplacementRule(pattern889, replacement889)
    pattern890 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons50, cons71, cons13, cons137, cons405, cons575)
    def replacement890(p, b, d, a, n, c, x, q):
        rubi.append(890)
        return Dist(S(1)/(a*n*(p + S(1))*(-a*d + b*c)), Int((a + b*x**n)**(p + S(1))*(c + d*x**n)**q*Simp(b*c + b*d*x**n*(n*(p + q + S(2)) + S(1)) + n*(p + S(1))*(-a*d + b*c), x), x), x) - Simp(b*x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(a*n*(p + S(1))*(-a*d + b*c)), x)
    rule890 = ReplacementRule(pattern890, replacement890)
    pattern891 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons71, cons148, cons220, cons577)
    def replacement891(p, b, d, a, n, c, x, q):
        rubi.append(891)
        return Int(ExpandIntegrand((a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule891 = ReplacementRule(pattern891, replacement891)
    pattern892 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons5, cons71, cons395, cons576, cons578, cons579, cons575)
    def replacement892(p, b, d, a, n, c, x, q):
        rubi.append(892)
        return Dist(S(1)/(b*(n*(p + q) + S(1))), Int((a + b*x**n)**p*(c + d*x**n)**(q + S(-2))*Simp(c*(-a*d + b*c*(n*(p + q) + S(1))) + d*x**n*(-a*d*(n*(q + S(-1)) + S(1)) + b*c*(n*(p + S(2)*q + S(-1)) + S(1))), x), x), x) + Simp(d*x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))/(b*(n*(p + q) + S(1))), x)
    rule892 = ReplacementRule(pattern892, replacement892)
    pattern893 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons71, cons402, cons403, cons163, cons575)
    def replacement893(p, b, d, a, n, c, x, q):
        rubi.append(893)
        return Dist(n/(n*(p + q) + S(1)), Int((a + b*x**n)**(p + S(-1))*(c + d*x**n)**(q + S(-1))*Simp(a*c*(p + q) + x**n*(a*d*(p + q) + q*(-a*d + b*c)), x), x), x) + Simp(x*(a + b*x**n)**p*(c + d*x**n)**q/(n*(p + q) + S(1)), x)
    rule893 = ReplacementRule(pattern893, replacement893)
    pattern894 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons573, cons466, cons580)
    def replacement894(b, d, c, a, x):
        rubi.append(894)
        return Simp(sqrt(a + b*x**S(2))*EllipticF(ArcTan(x*Rt(d/c, S(2))), S(1) - b*c/(a*d))/(a*sqrt(c*(a + b*x**S(2))/(a*(c + d*x**S(2))))*sqrt(c + d*x**S(2))*Rt(d/c, S(2))), x)
    rule894 = ReplacementRule(pattern894, replacement894)
    pattern895 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons581, cons177, cons43, cons582)
    def replacement895(b, d, c, a, x):
        rubi.append(895)
        return Simp(EllipticF(asin(x*Rt(-d/c, S(2))), b*c/(a*d))/(sqrt(a)*sqrt(c)*Rt(-d/c, S(2))), x)
    rule895 = ReplacementRule(pattern895, replacement895)
    pattern896 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons581, cons177, cons583)
    def replacement896(b, d, c, a, x):
        rubi.append(896)
        return -Simp(EllipticF(acos(x*Rt(-d/c, S(2))), b*c/(-a*d + b*c))/(sqrt(c)*sqrt(a - b*c/d)*Rt(-d/c, S(2))), x)
    rule896 = ReplacementRule(pattern896, replacement896)
    pattern897 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons117)
    def replacement897(b, d, c, a, x):
        rubi.append(897)
        return Dist(sqrt(S(1) + d*x**S(2)/c)/sqrt(c + d*x**S(2)), Int(S(1)/(sqrt(S(1) + d*x**S(2)/c)*sqrt(a + b*x**S(2))), x), x)
    rule897 = ReplacementRule(pattern897, replacement897)
    pattern898 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))/sqrt(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons573, cons466)
    def replacement898(b, d, c, a, x):
        rubi.append(898)
        return Dist(a, Int(S(1)/(sqrt(a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x) + Dist(b, Int(x**S(2)/(sqrt(a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x)
    rule898 = ReplacementRule(pattern898, replacement898)
    pattern899 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))/sqrt(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons573, cons483)
    def replacement899(b, d, c, a, x):
        rubi.append(899)
        return Dist(b/d, Int(sqrt(c + d*x**S(2))/sqrt(a + b*x**S(2)), x), x) - Dist((-a*d + b*c)/d, Int(S(1)/(sqrt(a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x)
    rule899 = ReplacementRule(pattern899, replacement899)
    pattern900 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))/sqrt(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons581, cons177, cons43)
    def replacement900(b, d, c, a, x):
        rubi.append(900)
        return Simp(sqrt(a)*EllipticE(asin(x*Rt(-d/c, S(2))), b*c/(a*d))/(sqrt(c)*Rt(-d/c, S(2))), x)
    rule900 = ReplacementRule(pattern900, replacement900)
    pattern901 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))/sqrt(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons581, cons177, cons583)
    def replacement901(b, d, c, a, x):
        rubi.append(901)
        return -Simp(sqrt(a - b*c/d)*EllipticE(acos(x*Rt(-d/c, S(2))), b*c/(-a*d + b*c))/(sqrt(c)*Rt(-d/c, S(2))), x)
    rule901 = ReplacementRule(pattern901, replacement901)
    pattern902 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))/sqrt(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons581, cons177, cons448)
    def replacement902(b, d, c, a, x):
        rubi.append(902)
        return Dist(sqrt(a + b*x**S(2))/sqrt(S(1) + b*x**S(2)/a), Int(sqrt(S(1) + b*x**S(2)/a)/sqrt(c + d*x**S(2)), x), x)
    rule902 = ReplacementRule(pattern902, replacement902)
    pattern903 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))/sqrt(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons581, cons117)
    def replacement903(b, d, c, a, x):
        rubi.append(903)
        return Dist(sqrt(S(1) + d*x**S(2)/c)/sqrt(c + d*x**S(2)), Int(sqrt(a + b*x**S(2))/sqrt(S(1) + d*x**S(2)/c), x), x)
    rule903 = ReplacementRule(pattern903, replacement903)
    pattern904 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons50, cons71, cons128)
    def replacement904(p, b, d, a, n, c, x, q):
        rubi.append(904)
        return Int(ExpandIntegrand((a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule904 = ReplacementRule(pattern904, replacement904)
    pattern905 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons5, cons50, cons71, cons584, cons43, cons177)
    def replacement905(p, b, d, a, n, c, x, q):
        rubi.append(905)
        return Simp(a**p*c**q*x*AppellF1(S(1)/n, -p, -q, S(1) + S(1)/n, -b*x**n/a, -d*x**n/c), x)
    rule905 = ReplacementRule(pattern905, replacement905)
    pattern906 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons5, cons50, cons71, cons584, cons448)
    def replacement906(p, b, d, a, n, c, x, q):
        rubi.append(906)
        return Dist(a**IntPart(p)*(S(1) + b*x**n/a)**(-FracPart(p))*(a + b*x**n)**FracPart(p), Int((S(1) + b*x**n/a)**p*(c + d*x**n)**q, x), x)
    rule906 = ReplacementRule(pattern906, replacement906)
    pattern907 = Pattern(Integral((a_ + x_**WC('n', S(1))*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**WC('mn', S(1))*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons585, cons586, cons587)
    def replacement907(mn, p, b, d, c, n, a, x, q):
        rubi.append(907)
        return Int(x**(-n*q)*(a + b*x**n)**p*(c*x**n + d)**q, x)
    rule907 = ReplacementRule(pattern907, replacement907)
    pattern908 = Pattern(Integral((a_ + x_**WC('n', S(1))*WC('b', S(1)))**p_*(c_ + x_**WC('mn', S(1))*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons4, cons5, cons50, cons585, cons386, cons147)
    def replacement908(mn, p, b, d, c, n, a, x, q):
        rubi.append(908)
        return Dist(x**(n*FracPart(q))*(c + d*x**(-n))**FracPart(q)*(c*x**n + d)**(-FracPart(q)), Int(x**(-n*q)*(a + b*x**n)**p*(c*x**n + d)**q, x), x)
    rule908 = ReplacementRule(pattern908, replacement908)
    pattern909 = Pattern(Integral((u_**n_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**n_*WC('d', S(1)) + WC('c', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons50, cons68, cons69)
    def replacement909(p, u, b, d, c, a, n, x, q):
        rubi.append(909)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b*x**n)**p*(c + d*x**n)**q, x), x, u), x)
    rule909 = ReplacementRule(pattern909, replacement909)
    pattern910 = Pattern(Integral(u_**WC('p', S(1))*v_**WC('q', S(1)), x_), cons5, cons50, cons588)
    def replacement910(v, p, u, x, q):
        rubi.append(910)
        return Int(NormalizePseudoBinomial(u, x)**p*NormalizePseudoBinomial(v, x)**q, x)
    rule910 = ReplacementRule(pattern910, replacement910)
    pattern911 = Pattern(Integral(u_**WC('p', S(1))*v_**WC('q', S(1))*x_**WC('m', S(1)), x_), cons5, cons50, cons589, cons590)
    def replacement911(v, p, u, m, x, q):
        rubi.append(911)
        return Int(NormalizePseudoBinomial(v, x)**q*NormalizePseudoBinomial(u*x**(m/p), x)**p, x)
    rule911 = ReplacementRule(pattern911, replacement911)
    pattern912 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons50, cons591, cons500)
    def replacement912(p, m, b, d, c, n, x, q, e):
        rubi.append(912)
        return Dist(b**(S(1) - (m + S(1))/n)*e**m/n, Subst(Int((b*x)**(p + S(-1) + (m + S(1))/n)*(c + d*x)**q, x), x, x**n), x)
    rule912 = ReplacementRule(pattern912, replacement912)
    pattern913 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(x_**WC('n', S(1))*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons50, cons591, cons501)
    def replacement913(p, m, b, d, c, n, x, q, e):
        rubi.append(913)
        return Dist(b**IntPart(p)*e**m*x**(-n*FracPart(p))*(b*x**n)**FracPart(p), Int(x**(m + n*p)*(c + d*x**n)**q, x), x)
    rule913 = ReplacementRule(pattern913, replacement913)
    pattern914 = Pattern(Integral((e_*x_)**m_*(x_**WC('n', S(1))*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons50, cons18)
    def replacement914(p, m, b, d, c, n, x, q, e):
        rubi.append(914)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(b*x**n)**p*(c + d*x**n)**q, x), x)
    rule914 = ReplacementRule(pattern914, replacement914)
    pattern915 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons50, cons71, cons53)
    def replacement915(p, m, b, d, a, n, c, x, q):
        rubi.append(915)
        return Dist(S(1)/n, Subst(Int((a + b*x)**p*(c + d*x)**q, x), x, x**n), x)
    rule915 = ReplacementRule(pattern915, replacement915)
    pattern916 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons71, cons220, cons502)
    def replacement916(p, m, b, d, a, n, c, x, q):
        rubi.append(916)
        return Int(x**(m + n*(p + q))*(a*x**(-n) + b)**p*(c*x**(-n) + d)**q, x)
    rule916 = ReplacementRule(pattern916, replacement916)
    pattern917 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons50, cons71, cons500)
    def replacement917(p, m, b, d, a, n, c, x, q):
        rubi.append(917)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + (m + S(1))/n)*(a + b*x)**p*(c + d*x)**q, x), x, x**n), x)
    rule917 = ReplacementRule(pattern917, replacement917)
    pattern918 = Pattern(Integral((e_*x_)**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons50, cons71, cons500)
    def replacement918(p, m, b, d, a, n, c, x, q, e):
        rubi.append(918)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule918 = ReplacementRule(pattern918, replacement918)
    pattern919 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons71, cons555)
    def replacement919(p, m, b, d, a, n, c, x, q, e):
        rubi.append(919)
        return Int(ExpandIntegrand((e*x)**m*(a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule919 = ReplacementRule(pattern919, replacement919)
    pattern920 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons71, cons592, cons66)
    def replacement920(p, m, b, d, a, n, c, x, e):
        rubi.append(920)
        return Simp(c*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*e*(m + S(1))), x)
    rule920 = ReplacementRule(pattern920, replacement920)
    pattern921 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a1_ + x_**WC('non2', S(1))*WC('b1', S(1)))**WC('p', S(1))*(a2_ + x_**WC('non2', S(1))*WC('b2', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons57, cons58, cons59, cons60, cons7, cons27, cons48, cons21, cons4, cons5, cons593, cons55, cons594, cons66)
    def replacement921(p, a2, m, b2, b1, d, c, n, non2, x, a1, e):
        rubi.append(921)
        return Simp(c*(e*x)**(m + S(1))*(a1 + b1*x**(n/S(2)))**(p + S(1))*(a2 + b2*x**(n/S(2)))**(p + S(1))/(a1*a2*e*(m + S(1))), x)
    rule921 = ReplacementRule(pattern921, replacement921)
    pattern922 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons71, cons595, cons596, cons93, cons597)
    def replacement922(p, m, b, d, a, n, c, x, e):
        rubi.append(922)
        return Dist(d*e**(-n), Int((e*x)**(m + n)*(a + b*x**n)**p, x), x) + Simp(c*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*e*(m + S(1))), x)
    rule922 = ReplacementRule(pattern922, replacement922)
    pattern923 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons71, cons595, cons66)
    def replacement923(p, m, b, d, a, n, c, x, e):
        rubi.append(923)
        return Dist(d/b, Int((e*x)**m*(a + b*x**n)**(p + S(1)), x), x) + Simp((e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(-a*d + b*c)/(a*b*e*(m + S(1))), x)
    rule923 = ReplacementRule(pattern923, replacement923)
    pattern924 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons71, cons596, cons93, cons597, cons598)
    def replacement924(p, m, b, d, a, n, c, x, e):
        rubi.append(924)
        return Dist(e**(-n)*(a*d*(m + S(1)) - b*c*(m + n*(p + S(1)) + S(1)))/(a*(m + S(1))), Int((e*x)**(m + n)*(a + b*x**n)**p, x), x) + Simp(c*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*e*(m + S(1))), x)
    rule924 = ReplacementRule(pattern924, replacement924)
    pattern925 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a1_ + x_**WC('non2', S(1))*WC('b1', S(1)))**WC('p', S(1))*(a2_ + x_**WC('non2', S(1))*WC('b2', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons57, cons58, cons59, cons60, cons7, cons27, cons48, cons5, cons593, cons55, cons596, cons93, cons597, cons598)
    def replacement925(p, a2, m, b2, b1, d, c, n, non2, x, a1, e):
        rubi.append(925)
        return Dist(e**(-n)*(a1*a2*d*(m + S(1)) - b1*b2*c*(m + n*(p + S(1)) + S(1)))/(a1*a2*(m + S(1))), Int((e*x)**(m + n)*(a1 + b1*x**(n/S(2)))**p*(a2 + b2*x**(n/S(2)))**p, x), x) + Simp(c*(e*x)**(m + S(1))*(a1 + b1*x**(n/S(2)))**(p + S(1))*(a2 + b2*x**(n/S(2)))**(p + S(1))/(a1*a2*e*(m + S(1))), x)
    rule925 = ReplacementRule(pattern925, replacement925)
    pattern926 = Pattern(Integral(x_**m_*(a_ + x_**S(2)*WC('b', S(1)))**p_*(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons71, cons13, cons137, cons599, cons600)
    def replacement926(p, m, b, d, a, c, x):
        rubi.append(926)
        return Dist(b**(-m/S(2) + S(-1))/(S(2)*(p + S(1))), Int((a + b*x**S(2))**(p + S(1))*ExpandToSum(S(2)*b*x**S(2)*(p + S(1))*Together((b**(m/S(2))*x**(m + S(-2))*(c + d*x**S(2)) - (-a)**(m/S(2) + S(-1))*(-a*d + b*c))/(a + b*x**S(2))) - (-a)**(m/S(2) + S(-1))*(-a*d + b*c), x), x), x) + Simp(b**(-m/S(2) + S(-1))*x*(-a)**(m/S(2) + S(-1))*(a + b*x**S(2))**(p + S(1))*(-a*d + b*c)/(S(2)*(p + S(1))), x)
    rule926 = ReplacementRule(pattern926, replacement926)
    pattern927 = Pattern(Integral(x_**m_*(a_ + x_**S(2)*WC('b', S(1)))**p_*(c_ + x_**S(2)*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons71, cons13, cons137, cons601, cons600)
    def replacement927(p, m, b, d, a, c, x):
        rubi.append(927)
        return Dist(b**(-m/S(2) + S(-1))/(S(2)*(p + S(1))), Int(x**m*(a + b*x**S(2))**(p + S(1))*ExpandToSum(S(2)*b*(p + S(1))*Together((b**(m/S(2))*(c + d*x**S(2)) - x**(-m + S(2))*(-a)**(m/S(2) + S(-1))*(-a*d + b*c))/(a + b*x**S(2))) - x**(-m)*(-a)**(m/S(2) + S(-1))*(-a*d + b*c), x), x), x) + Simp(b**(-m/S(2) + S(-1))*x*(-a)**(m/S(2) + S(-1))*(a + b*x**S(2))**(p + S(1))*(-a*d + b*c)/(S(2)*(p + S(1))), x)
    rule927 = ReplacementRule(pattern927, replacement927)
    pattern928 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons71, cons13, cons137, cons602)
    def replacement928(p, m, b, d, a, n, c, x, e):
        rubi.append(928)
        return -Dist((a*d*(m + S(1)) - b*c*(m + n*(p + S(1)) + S(1)))/(a*b*n*(p + S(1))), Int((e*x)**m*(a + b*x**n)**(p + S(1)), x), x) - Simp((e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(-a*d + b*c)/(a*b*e*n*(p + S(1))), x)
    rule928 = ReplacementRule(pattern928, replacement928)
    pattern929 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a1_ + x_**WC('non2', S(1))*WC('b1', S(1)))**WC('p', S(1))*(a2_ + x_**WC('non2', S(1))*WC('b2', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons57, cons58, cons59, cons60, cons7, cons27, cons48, cons21, cons4, cons593, cons55, cons13, cons137, cons602)
    def replacement929(p, a2, m, b2, b1, d, c, n, non2, x, a1, e):
        rubi.append(929)
        return -Dist((a1*a2*d*(m + S(1)) - b1*b2*c*(m + n*(p + S(1)) + S(1)))/(a1*a2*b1*b2*n*(p + S(1))), Int((e*x)**m*(a1 + b1*x**(n/S(2)))**(p + S(1))*(a2 + b2*x**(n/S(2)))**(p + S(1)), x), x) - Simp((e*x)**(m + S(1))*(a1 + b1*x**(n/S(2)))**(p + S(1))*(a2 + b2*x**(n/S(2)))**(p + S(1))*(-a1*a2*d + b1*b2*c)/(a1*a2*b1*b2*e*n*(p + S(1))), x)
    rule929 = ReplacementRule(pattern929, replacement929)
    pattern930 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons71, cons603)
    def replacement930(p, m, b, d, a, n, c, x, e):
        rubi.append(930)
        return -Dist((a*d*(m + S(1)) - b*c*(m + n*(p + S(1)) + S(1)))/(b*(m + n*(p + S(1)) + S(1))), Int((e*x)**m*(a + b*x**n)**p, x), x) + Simp(d*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(b*e*(m + n*(p + S(1)) + S(1))), x)
    rule930 = ReplacementRule(pattern930, replacement930)
    pattern931 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a1_ + x_**WC('non2', S(1))*WC('b1', S(1)))**WC('p', S(1))*(a2_ + x_**WC('non2', S(1))*WC('b2', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1))), x_), cons57, cons58, cons59, cons60, cons7, cons27, cons48, cons21, cons4, cons5, cons593, cons55, cons603)
    def replacement931(p, a2, m, b2, b1, d, c, n, non2, x, a1, e):
        rubi.append(931)
        return -Dist((a1*a2*d*(m + S(1)) - b1*b2*c*(m + n*(p + S(1)) + S(1)))/(b1*b2*(m + n*(p + S(1)) + S(1))), Int((e*x)**m*(a1 + b1*x**(n/S(2)))**p*(a2 + b2*x**(n/S(2)))**p, x), x) + Simp(d*(e*x)**(m + S(1))*(a1 + b1*x**(n/S(2)))**(p + S(1))*(a2 + b2*x**(n/S(2)))**(p + S(1))/(b1*b2*e*(m + n*(p + S(1)) + S(1))), x)
    rule931 = ReplacementRule(pattern931, replacement931)
    pattern932 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_/(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons71, cons148, cons128, cons604)
    def replacement932(p, m, b, d, a, n, c, x, e):
        rubi.append(932)
        return Int(ExpandIntegrand((e*x)**m*(a + b*x**n)**p/(c + d*x**n), x), x)
    rule932 = ReplacementRule(pattern932, replacement932)
    pattern933 = Pattern(Integral((x_*WC('e', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons71, cons148, cons93, cons94, cons88)
    def replacement933(p, m, b, d, a, n, c, x, e):
        rubi.append(933)
        return -Dist(e**(-n)/(a*(m + S(1))), Int((e*x)**(m + n)*(a + b*x**n)**p*Simp(-a*d**S(2)*x**n*(m + S(1)) + b*c**S(2)*n*(p + S(1)) + c*(m + S(1))*(-S(2)*a*d + b*c), x), x), x) + Simp(c**S(2)*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))/(a*e*(m + S(1))), x)
    rule933 = ReplacementRule(pattern933, replacement933)
    pattern934 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons71, cons148, cons13, cons137)
    def replacement934(p, m, b, d, a, n, c, x, e):
        rubi.append(934)
        return Dist(S(1)/(a*b**S(2)*n*(p + S(1))), Int((e*x)**m*(a + b*x**n)**(p + S(1))*Simp(a*b*d**S(2)*n*x**n*(p + S(1)) + b**S(2)*c**S(2)*n*(p + S(1)) + (m + S(1))*(-a*d + b*c)**S(2), x), x), x) - Simp((e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(-a*d + b*c)**S(2)/(a*b**S(2)*e*n*(p + S(1))), x)
    rule934 = ReplacementRule(pattern934, replacement934)
    pattern935 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons71, cons148, cons605)
    def replacement935(p, m, b, d, a, n, c, x, e):
        rubi.append(935)
        return Dist(S(1)/(b*(m + n*(p + S(2)) + S(1))), Int((e*x)**m*(a + b*x**n)**p*Simp(b*c**S(2)*(m + n*(p + S(2)) + S(1)) + d*x**n*(S(2)*b*c*n*(p + S(1)) + (-a*d + S(2)*b*c)*(m + n + S(1))), x), x), x) + Simp(d**S(2)*e**(-n + S(-1))*(e*x)**(m + n + S(1))*(a + b*x**n)**(p + S(1))/(b*(m + n*(p + S(2)) + S(1))), x)
    rule935 = ReplacementRule(pattern935, replacement935)
    def With936(p, m, b, d, a, n, c, x, q):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        k = GCD(m + S(1), n)
        if Unequal(k, S(1)):
            return True
        return False
    pattern936 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons5, cons50, cons71, cons148, cons17, CustomConstraint(With936))
    def replacement936(p, m, b, d, a, n, c, x, q):

        k = GCD(m + S(1), n)
        rubi.append(936)
        return Dist(S(1)/k, Subst(Int(x**(S(-1) + (m + S(1))/k)*(a + b*x**(n/k))**p*(c + d*x**(n/k))**q, x), x, x**k), x)
    rule936 = ReplacementRule(pattern936, replacement936)
    def With937(p, m, b, d, a, n, c, x, q, e):
        k = Denominator(m)
        rubi.append(937)
        return Dist(k/e, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a + b*e**(-n)*x**(k*n))**p*(c + d*e**(-n)*x**(k*n))**q, x), x, (e*x)**(S(1)/k)), x)
    pattern937 = Pattern(Integral((x_*WC('e', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons50, cons71, cons148, cons367, cons38)
    rule937 = ReplacementRule(pattern937, With937)
    pattern938 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons71, cons148, cons606, cons137, cons403, cons607, cons608)
    def replacement938(p, m, b, d, a, n, c, x, q, e):
        rubi.append(938)
        return -Dist(e**n/(b*n*(p + S(1))), Int((e*x)**(m - n)*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*Simp(c*(m - n + S(1)) + d*x**n*(m + n*(q + S(-1)) + S(1)), x), x), x) + Simp(e**(n + S(-1))*(e*x)**(m - n + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(b*n*(p + S(1))), x)
    rule938 = ReplacementRule(pattern938, replacement938)
    pattern939 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons71, cons148, cons402, cons137, cons576, cons608)
    def replacement939(p, m, b, d, a, n, c, x, q, e):
        rubi.append(939)
        return Dist(S(1)/(a*b*n*(p + S(1))), Int((e*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-2))*Simp(c*(b*c*n*(p + S(1)) + (m + S(1))*(-a*d + b*c)) + d*x**n*(b*c*n*(p + S(1)) + (-a*d + b*c)*(m + n*(q + S(-1)) + S(1))), x), x), x) - Simp((e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*(-a*d + b*c)/(a*b*e*n*(p + S(1))), x)
    rule939 = ReplacementRule(pattern939, replacement939)
    pattern940 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons71, cons148, cons402, cons137, cons574, cons608)
    def replacement940(p, m, b, d, a, n, c, x, q, e):
        rubi.append(940)
        return Dist(S(1)/(a*n*(p + S(1))), Int((e*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*Simp(c*(m + n*(p + S(1)) + S(1)) + d*x**n*(m + n*(p + q + S(1)) + S(1)), x), x), x) - Simp((e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(a*e*n*(p + S(1))), x)
    rule940 = ReplacementRule(pattern940, replacement940)
    pattern941 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons50, cons71, cons148, cons244, cons137, cons609, cons608)
    def replacement941(p, m, b, d, a, n, c, x, q, e):
        rubi.append(941)
        return Dist(e**(S(2)*n)/(b*n*(p + S(1))*(-a*d + b*c)), Int((e*x)**(m - S(2)*n)*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*Simp(a*c*(m - S(2)*n + S(1)) + x**n*(a*d*(m + n*q - n + S(1)) + b*c*n*(p + S(1))), x), x), x) - Simp(a*e**(S(2)*n + S(-1))*(e*x)**(m - S(2)*n + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(b*n*(p + S(1))*(-a*d + b*c)), x)
    rule941 = ReplacementRule(pattern941, replacement941)
    pattern942 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons50, cons71, cons148, cons244, cons137, cons610, cons608)
    def replacement942(p, m, b, d, a, n, c, x, q, e):
        rubi.append(942)
        return -Dist(e**n/(n*(p + S(1))*(-a*d + b*c)), Int((e*x)**(m - n)*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*Simp(c*(m - n + S(1)) + d*x**n*(m + n*(p + q + S(1)) + S(1)), x), x), x) + Simp(e**(n + S(-1))*(e*x)**(m - n + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(n*(p + S(1))*(-a*d + b*c)), x)
    rule942 = ReplacementRule(pattern942, replacement942)
    pattern943 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons50, cons71, cons148, cons13, cons137, cons608)
    def replacement943(p, m, b, d, a, n, c, x, q, e):
        rubi.append(943)
        return Dist(S(1)/(a*n*(p + S(1))*(-a*d + b*c)), Int((e*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*Simp(b*c*(m + S(1)) + b*d*x**n*(m + n*(p + q + S(2)) + S(1)) + n*(p + S(1))*(-a*d + b*c), x), x), x) - Simp(b*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(a*e*n*(p + S(1))*(-a*d + b*c)), x)
    rule943 = ReplacementRule(pattern943, replacement943)
    pattern944 = Pattern(Integral((x_*WC('e', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons71, cons148, cons606, cons403, cons94, cons163, cons608)
    def replacement944(p, m, b, d, a, n, c, x, q, e):
        rubi.append(944)
        return -Dist(e**(-n)*n/(m + S(1)), Int((e*x)**(m + n)*(a + b*x**n)**(p + S(-1))*(c + d*x**n)**(q + S(-1))*Simp(a*d*q + b*c*p + b*d*x**n*(p + q), x), x), x) + Simp((e*x)**(m + S(1))*(a + b*x**n)**p*(c + d*x**n)**q/(e*(m + S(1))), x)
    rule944 = ReplacementRule(pattern944, replacement944)
    pattern945 = Pattern(Integral((x_*WC('e', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons71, cons148, cons611, cons576, cons94, cons608)
    def replacement945(p, m, b, d, a, n, c, x, q, e):
        rubi.append(945)
        return -Dist(e**(-n)/(a*(m + S(1))), Int((e*x)**(m + n)*(a + b*x**n)**p*(c + d*x**n)**(q + S(-2))*Simp(c*n*(a*d*(q + S(-1)) + b*c*(p + S(1))) + c*(m + S(1))*(-a*d + b*c) + d*x**n*(b*c*n*(p + q) + (m + S(1))*(-a*d + b*c)), x), x), x) + Simp(c*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))/(a*e*(m + S(1))), x)
    rule945 = ReplacementRule(pattern945, replacement945)
    pattern946 = Pattern(Integral((x_*WC('e', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons71, cons148, cons611, cons574, cons94, cons608)
    def replacement946(p, m, b, d, a, n, c, x, q, e):
        rubi.append(946)
        return -Dist(e**(-n)/(a*(m + S(1))), Int((e*x)**(m + n)*(a + b*x**n)**p*(c + d*x**n)**(q + S(-1))*Simp(b*c*(m + S(1)) + d*x**n*(b*n*(p + q + S(1)) + b*(m + S(1))) + n*(a*d*q + b*c*(p + S(1))), x), x), x) + Simp((e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(a*e*(m + S(1))), x)
    rule946 = ReplacementRule(pattern946, replacement946)
    pattern947 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons71, cons148, cons402, cons403, cons163, cons608)
    def replacement947(p, m, b, d, a, n, c, x, q, e):
        rubi.append(947)
        return Dist(n/(m + n*(p + q) + S(1)), Int((e*x)**m*(a + b*x**n)**(p + S(-1))*(c + d*x**n)**(q + S(-1))*Simp(a*c*(p + q) + x**n*(a*d*(p + q) + q*(-a*d + b*c)), x), x), x) + Simp((e*x)**(m + S(1))*(a + b*x**n)**p*(c + d*x**n)**q/(e*(m + n*(p + q) + S(1))), x)
    rule947 = ReplacementRule(pattern947, replacement947)
    pattern948 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons71, cons148, cons395, cons576, cons608)
    def replacement948(p, m, b, d, a, n, c, x, q, e):
        rubi.append(948)
        return Dist(S(1)/(b*(m + n*(p + q) + S(1))), Int((e*x)**m*(a + b*x**n)**p*(c + d*x**n)**(q + S(-2))*Simp(c*(b*c*n*(p + q) + (m + S(1))*(-a*d + b*c)) + x**n*(b*c*d*n*(p + q) + d*n*(q + S(-1))*(-a*d + b*c) + d*(m + S(1))*(-a*d + b*c)), x), x), x) + Simp(d*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))/(b*e*(m + n*(p + q) + S(1))), x)
    rule948 = ReplacementRule(pattern948, replacement948)
    pattern949 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons71, cons148, cons611, cons403, cons607, cons608)
    def replacement949(p, m, b, d, a, n, c, x, q, e):
        rubi.append(949)
        return -Dist(e**n/(b*(m + n*(p + q) + S(1))), Int((e*x)**(m - n)*(a + b*x**n)**p*(c + d*x**n)**(q + S(-1))*Simp(a*c*(m - n + S(1)) + x**n*(a*d*(m - n + S(1)) - n*q*(-a*d + b*c)), x), x), x) + Simp(e**(n + S(-1))*(e*x)**(m - n + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(b*(m + n*(p + q) + S(1))), x)
    rule949 = ReplacementRule(pattern949, replacement949)
    pattern950 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons50, cons71, cons148, cons31, cons609, cons608)
    def replacement950(p, m, b, d, a, n, c, x, q, e):
        rubi.append(950)
        return -Dist(e**(S(2)*n)/(b*d*(m + n*(p + q) + S(1))), Int((e*x)**(m - S(2)*n)*(a + b*x**n)**p*(c + d*x**n)**q*Simp(a*c*(m - S(2)*n + S(1)) + x**n*(a*d*(m + n*(q + S(-1)) + S(1)) + b*c*(m + n*(p + S(-1)) + S(1))), x), x), x) + Simp(e**(S(2)*n + S(-1))*(e*x)**(m - S(2)*n + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(b*d*(m + n*(p + q) + S(1))), x)
    rule950 = ReplacementRule(pattern950, replacement950)
    pattern951 = Pattern(Integral((x_*WC('e', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons50, cons71, cons148, cons31, cons94, cons608)
    def replacement951(p, m, b, d, a, n, c, x, q, e):
        rubi.append(951)
        return -Dist(e**(-n)/(a*c*(m + S(1))), Int((e*x)**(m + n)*(a + b*x**n)**p*(c + d*x**n)**q*Simp(b*d*x**n*(m + n*(p + q + S(2)) + S(1)) + n*(a*d*q + b*c*p) + (a*d + b*c)*(m + n + S(1)), x), x), x) + Simp((e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(a*c*e*(m + S(1))), x)
    rule951 = ReplacementRule(pattern951, replacement951)
    pattern952 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))/((a_ + x_**n_*WC('b', S(1)))*(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons71, cons148, cons31, cons612)
    def replacement952(m, b, d, a, n, c, x, e):
        rubi.append(952)
        return -Dist(a*e**n/(-a*d + b*c), Int((e*x)**(m - n)/(a + b*x**n), x), x) + Dist(c*e**n/(-a*d + b*c), Int((e*x)**(m - n)/(c + d*x**n), x), x)
    rule952 = ReplacementRule(pattern952, replacement952)
    pattern953 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))/((a_ + x_**n_*WC('b', S(1)))*(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons71, cons148)
    def replacement953(m, b, d, a, n, c, x, e):
        rubi.append(953)
        return Dist(b/(-a*d + b*c), Int((e*x)**m/(a + b*x**n), x), x) - Dist(d/(-a*d + b*c), Int((e*x)**m/(c + d*x**n), x), x)
    rule953 = ReplacementRule(pattern953, replacement953)
    pattern954 = Pattern(Integral(x_**m_/((a_ + x_**n_*WC('b', S(1)))*sqrt(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71, cons613, cons614, cons615)
    def replacement954(m, b, d, a, n, c, x):
        rubi.append(954)
        return Dist(S(1)/b, Int(x**(m - n)/sqrt(c + d*x**n), x), x) - Dist(a/b, Int(x**(m - n)/((a + b*x**n)*sqrt(c + d*x**n)), x), x)
    rule954 = ReplacementRule(pattern954, replacement954)
    def With955(b, d, c, a, x):
        r = Numerator(Rt(-a/b, S(2)))
        s = Denominator(Rt(-a/b, S(2)))
        rubi.append(955)
        return -Dist(s/(S(2)*b), Int(S(1)/(sqrt(c + d*x**S(4))*(r - s*x**S(2))), x), x) + Dist(s/(S(2)*b), Int(S(1)/(sqrt(c + d*x**S(4))*(r + s*x**S(2))), x), x)
    pattern955 = Pattern(Integral(x_**S(2)/((a_ + x_**S(4)*WC('b', S(1)))*sqrt(c_ + x_**S(4)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71)
    rule955 = ReplacementRule(pattern955, With955)
    def With956(b, d, c, a, x):
        q = Rt(d/c, S(3))
        rubi.append(956)
        return Simp(S(2)**(S(1)/3)*q*log(-S(2)**(S(1)/3)*q*x + S(1) - sqrt(c + d*x**S(3))/sqrt(c))/(S(12)*b*sqrt(c)), x) - Simp(S(2)**(S(1)/3)*q*log(-S(2)**(S(1)/3)*q*x + S(1) + sqrt(c + d*x**S(3))/sqrt(c))/(S(12)*b*sqrt(c)), x) + Simp(S(2)**(S(1)/3)*q*atanh(sqrt(c + d*x**S(3))/sqrt(c))/(S(18)*b*sqrt(c)), x) - Simp(S(2)**(S(1)/3)*sqrt(S(3))*q*ArcTan(sqrt(S(3))/S(3) + S(2)**(S(2)/3)*sqrt(S(3))*(sqrt(c) - sqrt(c + d*x**S(3)))/(S(3)*sqrt(c)*q*x))/(S(18)*b*sqrt(c)), x) + Simp(S(2)**(S(1)/3)*sqrt(S(3))*q*ArcTan(sqrt(S(3))/S(3) + S(2)**(S(2)/3)*sqrt(S(3))*(sqrt(c) + sqrt(c + d*x**S(3)))/(S(3)*sqrt(c)*q*x))/(S(18)*b*sqrt(c)), x)
    pattern956 = Pattern(Integral(x_/((a_ + x_**S(3)*WC('b', S(1)))*sqrt(c_ + x_**S(3)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71, cons616)
    rule956 = ReplacementRule(pattern956, With956)
    pattern957 = Pattern(Integral(x_**m_/((a_ + x_**S(3)*WC('b', S(1)))*sqrt(c_ + x_**S(3)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71, cons616, cons617)
    def replacement957(m, b, d, a, c, x):
        rubi.append(957)
        return Dist(S(1)/b, Int(x**(m + S(-3))/sqrt(c + d*x**S(3)), x), x) - Dist(a/b, Int(x**(m + S(-3))/((a + b*x**S(3))*sqrt(c + d*x**S(3))), x), x)
    rule957 = ReplacementRule(pattern957, replacement957)
    pattern958 = Pattern(Integral(x_**m_/((a_ + x_**S(3)*WC('b', S(1)))*sqrt(c_ + x_**S(3)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71, cons616, cons618)
    def replacement958(m, b, d, a, c, x):
        rubi.append(958)
        return Dist(S(1)/a, Int(x**m/sqrt(c + d*x**S(3)), x), x) - Dist(b/a, Int(x**(m + S(3))/((a + b*x**S(3))*sqrt(c + d*x**S(3))), x), x)
    rule958 = ReplacementRule(pattern958, replacement958)
    pattern959 = Pattern(Integral(x_**S(2)*sqrt(c_ + x_**S(4)*WC('d', S(1)))/(a_ + x_**S(4)*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons71)
    def replacement959(b, d, c, a, x):
        rubi.append(959)
        return Dist(d/b, Int(x**S(2)/sqrt(c + d*x**S(4)), x), x) + Dist((-a*d + b*c)/b, Int(x**S(2)/((a + b*x**S(4))*sqrt(c + d*x**S(4))), x), x)
    rule959 = ReplacementRule(pattern959, replacement959)
    pattern960 = Pattern(Integral(x_**WC('m', S(1))*sqrt(c_ + x_**S(3)*WC('d', S(1)))/(a_ + x_**S(3)*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons71, cons616, cons619)
    def replacement960(m, b, d, a, c, x):
        rubi.append(960)
        return Dist(d/b, Int(x**m/sqrt(c + d*x**S(3)), x), x) + Dist((-a*d + b*c)/b, Int(x**m/((a + b*x**S(3))*sqrt(c + d*x**S(3))), x), x)
    rule960 = ReplacementRule(pattern960, replacement960)
    pattern961 = Pattern(Integral(x_**S(2)/(sqrt(a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71, cons466, cons573, cons580)
    def replacement961(b, d, c, a, x):
        rubi.append(961)
        return -Dist(c/b, Int(sqrt(a + b*x**S(2))/(c + d*x**S(2))**(S(3)/2), x), x) + Simp(x*sqrt(a + b*x**S(2))/(b*sqrt(c + d*x**S(2))), x)
    rule961 = ReplacementRule(pattern961, replacement961)
    pattern962 = Pattern(Integral(x_**n_/(sqrt(a_ + x_**n_*WC('b', S(1)))*sqrt(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons71, cons620, cons621)
    def replacement962(b, d, a, n, c, x):
        rubi.append(962)
        return Dist(S(1)/b, Int(sqrt(a + b*x**n)/sqrt(c + d*x**n), x), x) - Dist(a/b, Int(S(1)/(sqrt(a + b*x**n)*sqrt(c + d*x**n)), x), x)
    rule962 = ReplacementRule(pattern962, replacement962)
    def With963(p, m, b, d, a, n, c, x, q):
        k = Denominator(p)
        rubi.append(963)
        return Dist(a**(p + (m + S(1))/n)*k/n, Subst(Int(x**(k*(m + S(1))/n + S(-1))*(c - x**k*(-a*d + b*c))**q*(-b*x**k + S(1))**(-p - q + S(-1) - (m + S(1))/n), x), x, x**(n/k)*(a + b*x**n)**(-S(1)/k)), x)
    pattern963 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons148, cons244, cons622, cons485)
    rule963 = ReplacementRule(pattern963, With963)
    pattern964 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons5, cons50, cons71, cons196, cons17)
    def replacement964(p, m, b, d, a, n, c, x, q):
        rubi.append(964)
        return -Subst(Int(x**(-m + S(-2))*(a + b*x**(-n))**p*(c + d*x**(-n))**q, x), x, S(1)/x)
    rule964 = ReplacementRule(pattern964, replacement964)
    def With965(p, m, b, d, a, n, c, x, q, e):
        g = Denominator(m)
        rubi.append(965)
        return -Dist(g/e, Subst(Int(x**(-g*(m + S(1)) + S(-1))*(a + b*e**(-n)*x**(-g*n))**p*(c + d*e**(-n)*x**(-g*n))**q, x), x, (e*x)**(-S(1)/g)), x)
    pattern965 = Pattern(Integral((x_*WC('e', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons50, cons196, cons367)
    rule965 = ReplacementRule(pattern965, With965)
    pattern966 = Pattern(Integral((x_*WC('e', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons50, cons71, cons196, cons356)
    def replacement966(p, m, b, d, a, n, c, x, q, e):
        rubi.append(966)
        return -Dist((e*x)**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(a + b*x**(-n))**p*(c + d*x**(-n))**q, x), x, S(1)/x), x)
    rule966 = ReplacementRule(pattern966, replacement966)
    def With967(p, m, b, d, a, n, c, x, q):
        g = Denominator(n)
        rubi.append(967)
        return Dist(g, Subst(Int(x**(g*(m + S(1)) + S(-1))*(a + b*x**(g*n))**p*(c + d*x**(g*n))**q, x), x, x**(S(1)/g)), x)
    pattern967 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons21, cons5, cons50, cons71, cons489)
    rule967 = ReplacementRule(pattern967, With967)
    pattern968 = Pattern(Integral((e_*x_)**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons50, cons71, cons489)
    def replacement968(p, m, b, d, a, n, c, x, q, e):
        rubi.append(968)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule968 = ReplacementRule(pattern968, replacement968)
    pattern969 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons50, cons71, cons541, cons23)
    def replacement969(p, m, b, d, a, n, c, x, q):
        rubi.append(969)
        return Dist(S(1)/(m + S(1)), Subst(Int((a + b*x**(n/(m + S(1))))**p*(c + d*x**(n/(m + S(1))))**q, x), x, x**(m + S(1))), x)
    rule969 = ReplacementRule(pattern969, replacement969)
    pattern970 = Pattern(Integral((e_*x_)**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons50, cons71, cons541, cons23)
    def replacement970(p, m, b, d, a, n, c, x, q, e):
        rubi.append(970)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule970 = ReplacementRule(pattern970, replacement970)
    pattern971 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons71, cons402, cons137, cons576, cons608)
    def replacement971(p, m, b, d, a, n, c, x, q, e):
        rubi.append(971)
        return Dist(S(1)/(a*b*n*(p + S(1))), Int((e*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-2))*Simp(c*(b*c*n*(p + S(1)) + (m + S(1))*(-a*d + b*c)) + d*x**n*(b*c*n*(p + S(1)) + (-a*d + b*c)*(m + n*(q + S(-1)) + S(1))), x), x), x) - Simp((e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*(-a*d + b*c)/(a*b*e*n*(p + S(1))), x)
    rule971 = ReplacementRule(pattern971, replacement971)
    pattern972 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons71, cons402, cons137, cons574, cons608)
    def replacement972(p, m, b, d, a, n, c, x, q, e):
        rubi.append(972)
        return Dist(S(1)/(a*n*(p + S(1))), Int((e*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*Simp(c*(m + n*(p + S(1)) + S(1)) + d*x**n*(m + n*(p + q + S(1)) + S(1)), x), x), x) - Simp((e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(a*e*n*(p + S(1))), x)
    rule972 = ReplacementRule(pattern972, replacement972)
    pattern973 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons50, cons71, cons13, cons137, cons608)
    def replacement973(p, m, b, d, a, n, c, x, q, e):
        rubi.append(973)
        return Dist(S(1)/(a*n*(p + S(1))*(-a*d + b*c)), Int((e*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*Simp(b*c*(m + S(1)) + b*d*x**n*(m + n*(p + q + S(2)) + S(1)) + n*(p + S(1))*(-a*d + b*c), x), x), x) - Simp(b*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(a*e*n*(p + S(1))*(-a*d + b*c)), x)
    rule973 = ReplacementRule(pattern973, replacement973)
    pattern974 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons71, cons402, cons403, cons163, cons608)
    def replacement974(p, m, b, d, a, n, c, x, q, e):
        rubi.append(974)
        return Dist(n/(m + n*(p + q) + S(1)), Int((e*x)**m*(a + b*x**n)**(p + S(-1))*(c + d*x**n)**(q + S(-1))*Simp(a*c*(p + q) + x**n*(a*d*(p + q) + q*(-a*d + b*c)), x), x), x) + Simp((e*x)**(m + S(1))*(a + b*x**n)**p*(c + d*x**n)**q/(e*(m + n*(p + q) + S(1))), x)
    rule974 = ReplacementRule(pattern974, replacement974)
    pattern975 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons71, cons395, cons576, cons608)
    def replacement975(p, m, b, d, a, n, c, x, q, e):
        rubi.append(975)
        return Dist(S(1)/(b*(m + n*(p + q) + S(1))), Int((e*x)**m*(a + b*x**n)**p*(c + d*x**n)**(q + S(-2))*Simp(c*(b*c*n*(p + q) + (m + S(1))*(-a*d + b*c)) + x**n*(b*c*d*n*(p + q) + d*n*(q + S(-1))*(-a*d + b*c) + d*(m + S(1))*(-a*d + b*c)), x), x), x) + Simp(d*(e*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))/(b*e*(m + n*(p + q) + S(1))), x)
    rule975 = ReplacementRule(pattern975, replacement975)
    pattern976 = Pattern(Integral(x_**m_/((a_ + x_**n_*WC('b', S(1)))*(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons71, cons623)
    def replacement976(m, b, d, a, n, c, x):
        rubi.append(976)
        return -Dist(a/(-a*d + b*c), Int(x**(m - n)/(a + b*x**n), x), x) + Dist(c/(-a*d + b*c), Int(x**(m - n)/(c + d*x**n), x), x)
    rule976 = ReplacementRule(pattern976, replacement976)
    pattern977 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))/((a_ + x_**n_*WC('b', S(1)))*(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons21, cons71)
    def replacement977(m, b, d, a, n, c, x, e):
        rubi.append(977)
        return Dist(b/(-a*d + b*c), Int((e*x)**m/(a + b*x**n), x), x) - Dist(d/(-a*d + b*c), Int((e*x)**m/(c + d*x**n), x), x)
    rule977 = ReplacementRule(pattern977, replacement977)
    pattern978 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons71, cons624, cons625, cons626)
    def replacement978(p, m, b, d, a, n, c, x, q, e):
        rubi.append(978)
        return Int(ExpandIntegrand((e*x)**m*(a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule978 = ReplacementRule(pattern978, replacement978)
    pattern979 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**WC('n', S(1))*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**WC('mn', S(1))*WC('d', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons585, cons586, cons587)
    def replacement979(mn, p, m, b, d, c, n, a, x, q):
        rubi.append(979)
        return Int(x**(m - n*q)*(a + b*x**n)**p*(c*x**n + d)**q, x)
    rule979 = ReplacementRule(pattern979, replacement979)
    pattern980 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**WC('n', S(1))*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**WC('mn', S(1))*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons50, cons585, cons386, cons147)
    def replacement980(mn, p, m, b, d, c, n, a, x, q):
        rubi.append(980)
        return Dist(x**(n*FracPart(q))*(c + d*x**(-n))**FracPart(q)*(c*x**n + d)**(-FracPart(q)), Int(x**(m - n*q)*(a + b*x**n)**p*(c*x**n + d)**q, x), x)
    rule980 = ReplacementRule(pattern980, replacement980)
    pattern981 = Pattern(Integral((e_*x_)**m_*(c_ + x_**WC('mn', S(1))*WC('d', S(1)))**WC('q', S(1))*(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons50, cons585)
    def replacement981(mn, p, m, b, d, a, n, c, x, q, e):
        rubi.append(981)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*x**n)**p*(c + d*x**(-n))**q, x), x)
    rule981 = ReplacementRule(pattern981, replacement981)
    pattern982 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons50, cons71, cons66, cons627, cons43, cons177)
    def replacement982(p, m, b, d, a, n, c, x, q, e):
        rubi.append(982)
        return Simp(a**p*c**q*(e*x)**(m + S(1))*AppellF1((m + S(1))/n, -p, -q, S(1) + (m + S(1))/n, -b*x**n/a, -d*x**n/c)/(e*(m + S(1))), x)
    rule982 = ReplacementRule(pattern982, replacement982)
    pattern983 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons50, cons71, cons66, cons627, cons448)
    def replacement983(p, m, b, d, a, n, c, x, q, e):
        rubi.append(983)
        return Dist(a**IntPart(p)*(S(1) + b*x**n/a)**(-FracPart(p))*(a + b*x**n)**FracPart(p), Int((e*x)**m*(S(1) + b*x**n/a)**p*(c + d*x**n)**q, x), x)
    rule983 = ReplacementRule(pattern983, replacement983)
    pattern984 = Pattern(Integral(x_**WC('m', S(1))*(v_**n_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(v_**n_*WC('d', S(1)) + WC('c', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons50, cons552, cons17, cons553)
    def replacement984(v, p, m, b, d, c, a, n, x, q):
        rubi.append(984)
        return Dist(Coefficient(v, x, S(1))**(-m + S(-1)), Subst(Int(SimplifyIntegrand((a + b*x**n)**p*(c + d*x**n)**q*(x - Coefficient(v, x, S(0)))**m, x), x), x, v), x)
    rule984 = ReplacementRule(pattern984, replacement984)
    pattern985 = Pattern(Integral(u_**WC('m', S(1))*(v_**n_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(v_**n_*WC('d', S(1)) + WC('c', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons5, cons50, cons554)
    def replacement985(v, p, u, m, b, d, c, a, n, x, q):
        rubi.append(985)
        return Dist(u**m*v**(-m)/Coefficient(v, x, S(1)), Subst(Int(x**m*(a + b*x**n)**p*(c + d*x**n)**q, x), x, v), x)
    rule985 = ReplacementRule(pattern985, replacement985)
    pattern986 = Pattern(Integral((a1_ + x_**WC('non2', S(1))*WC('b1', S(1)))**WC('p', S(1))*(a2_ + x_**WC('non2', S(1))*WC('b2', S(1)))**WC('p', S(1))*(c_ + x_**WC('n', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('u', S(1)), x_), cons57, cons58, cons59, cons60, cons7, cons27, cons4, cons5, cons50, cons593, cons55, cons494)
    def replacement986(p, a2, u, b2, b1, d, c, n, non2, x, a1, q):
        rubi.append(986)
        return Int(u*(c + d*x**n)**q*(a1*a2 + b1*b2*x**n)**p, x)
    rule986 = ReplacementRule(pattern986, replacement986)
    pattern987 = Pattern(Integral((a1_ + x_**WC('non2', S(1))*WC('b1', S(1)))**WC('p', S(1))*(a2_ + x_**WC('non2', S(1))*WC('b2', S(1)))**WC('p', S(1))*(c_ + x_**WC('n', S(1))*WC('d', S(1)) + x_**WC('n2', S(1))*WC('e', S(1)))**WC('q', S(1))*WC('u', S(1)), x_), cons57, cons58, cons59, cons60, cons7, cons27, cons48, cons4, cons5, cons50, cons593, cons46, cons55, cons494)
    def replacement987(p, a2, u, b2, n2, b1, d, c, n, non2, x, a1, q, e):
        rubi.append(987)
        return Int(u*(a1*a2 + b1*b2*x**n)**p*(c + d*x**n + e*x**(S(2)*n))**q, x)
    rule987 = ReplacementRule(pattern987, replacement987)
    pattern988 = Pattern(Integral((a1_ + x_**WC('non2', S(1))*WC('b1', S(1)))**p_*(a2_ + x_**WC('non2', S(1))*WC('b2', S(1)))**p_*(c_ + x_**WC('n', S(1))*WC('d', S(1)))**WC('q', S(1))*WC('u', S(1)), x_), cons57, cons58, cons59, cons60, cons7, cons27, cons4, cons5, cons50, cons593, cons55)
    def replacement988(p, a2, u, b2, b1, d, c, n, non2, x, a1, q):
        rubi.append(988)
        return Dist((a1 + b1*x**(n/S(2)))**FracPart(p)*(a2 + b2*x**(n/S(2)))**FracPart(p)*(a1*a2 + b1*b2*x**n)**(-FracPart(p)), Int(u*(c + d*x**n)**q*(a1*a2 + b1*b2*x**n)**p, x), x)
    rule988 = ReplacementRule(pattern988, replacement988)
    pattern989 = Pattern(Integral((a1_ + x_**WC('non2', S(1))*WC('b1', S(1)))**WC('p', S(1))*(a2_ + x_**WC('non2', S(1))*WC('b2', S(1)))**WC('p', S(1))*(c_ + x_**WC('n', S(1))*WC('d', S(1)) + x_**WC('n2', S(1))*WC('e', S(1)))**WC('q', S(1))*WC('u', S(1)), x_), cons57, cons58, cons59, cons60, cons7, cons27, cons48, cons4, cons5, cons50, cons593, cons46, cons55)
    def replacement989(p, a2, u, b2, n2, b1, d, c, n, non2, x, a1, q, e):
        rubi.append(989)
        return Dist((a1 + b1*x**(n/S(2)))**FracPart(p)*(a2 + b2*x**(n/S(2)))**FracPart(p)*(a1*a2 + b1*b2*x**n)**(-FracPart(p)), Int(u*(a1*a2 + b1*b2*x**n)**p*(c + d*x**n + e*x**(S(2)*n))**q, x), x)
    rule989 = ReplacementRule(pattern989, replacement989)
    pattern990 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons628)
    def replacement990(p, f, b, r, d, a, n, c, x, q, e):
        rubi.append(990)
        return Int(ExpandIntegrand((a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x), x)
    rule990 = ReplacementRule(pattern990, replacement990)
    pattern991 = Pattern(Integral((e_ + x_**n_*WC('f', S(1)))/((a_ + x_**n_*WC('b', S(1)))*(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons629)
    def replacement991(f, b, d, a, n, c, x, e):
        rubi.append(991)
        return Dist((-a*f + b*e)/(-a*d + b*c), Int(S(1)/(a + b*x**n), x), x) - Dist((-c*f + d*e)/(-a*d + b*c), Int(S(1)/(c + d*x**n), x), x)
    rule991 = ReplacementRule(pattern991, replacement991)
    pattern992 = Pattern(Integral((e_ + x_**n_*WC('f', S(1)))/((a_ + x_**n_*WC('b', S(1)))*sqrt(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons629)
    def replacement992(f, b, d, a, n, c, x, e):
        rubi.append(992)
        return Dist(f/b, Int(S(1)/sqrt(c + d*x**n), x), x) + Dist((-a*f + b*e)/b, Int(S(1)/((a + b*x**n)*sqrt(c + d*x**n)), x), x)
    rule992 = ReplacementRule(pattern992, replacement992)
    pattern993 = Pattern(Integral((e_ + x_**n_*WC('f', S(1)))/(sqrt(a_ + x_**n_*WC('b', S(1)))*sqrt(c_ + x_**n_*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons630)
    def replacement993(f, b, d, a, n, c, x, e):
        rubi.append(993)
        return Dist(f/b, Int(sqrt(a + b*x**n)/sqrt(c + d*x**n), x), x) + Dist((-a*f + b*e)/b, Int(S(1)/(sqrt(a + b*x**n)*sqrt(c + d*x**n)), x), x)
    rule993 = ReplacementRule(pattern993, replacement993)
    pattern994 = Pattern(Integral((e_ + x_**S(2)*WC('f', S(1)))/(sqrt(a_ + x_**S(2)*WC('b', S(1)))*(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons466, cons573)
    def replacement994(f, b, d, a, c, x, e):
        rubi.append(994)
        return Dist((-a*f + b*e)/(-a*d + b*c), Int(S(1)/(sqrt(a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x) - Dist((-c*f + d*e)/(-a*d + b*c), Int(sqrt(a + b*x**S(2))/(c + d*x**S(2))**(S(3)/2), x), x)
    rule994 = ReplacementRule(pattern994, replacement994)
    pattern995 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons402, cons137, cons403)
    def replacement995(p, f, b, d, a, n, c, x, q, e):
        rubi.append(995)
        return Dist(S(1)/(a*b*n*(p + S(1))), Int((a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*Simp(c*(-a*f + b*e*n*(p + S(1)) + b*e) + d*x**n*(b*e*n*(p + S(1)) + (-a*f + b*e)*(n*q + S(1))), x), x), x) - Simp(x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*(-a*f + b*e)/(a*b*n*(p + S(1))), x)
    rule995 = ReplacementRule(pattern995, replacement995)
    pattern996 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons50, cons13, cons137)
    def replacement996(p, f, b, d, a, n, c, x, q, e):
        rubi.append(996)
        return Dist(S(1)/(a*n*(p + S(1))*(-a*d + b*c)), Int((a + b*x**n)**(p + S(1))*(c + d*x**n)**q*Simp(c*(-a*f + b*e) + d*x**n*(-a*f + b*e)*(n*(p + q + S(2)) + S(1)) + e*n*(p + S(1))*(-a*d + b*c), x), x), x) - Simp(x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))*(-a*f + b*e)/(a*n*(p + S(1))*(-a*d + b*c)), x)
    rule996 = ReplacementRule(pattern996, replacement996)
    pattern997 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons395, cons403, cons631)
    def replacement997(p, f, b, d, a, n, c, x, q, e):
        rubi.append(997)
        return Dist(S(1)/(b*(n*(p + q + S(1)) + S(1))), Int((a + b*x**n)**p*(c + d*x**n)**(q + S(-1))*Simp(c*(-a*f + b*e*n*(p + q + S(1)) + b*e) + x**n*(b*d*e*n*(p + q + S(1)) + d*(-a*f + b*e) + f*n*q*(-a*d + b*c)), x), x), x) + Simp(f*x*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(b*(n*(p + q + S(1)) + S(1))), x)
    rule997 = ReplacementRule(pattern997, replacement997)
    pattern998 = Pattern(Integral((e_ + x_**S(4)*WC('f', S(1)))/((a_ + x_**S(4)*WC('b', S(1)))**(S(3)/4)*(c_ + x_**S(4)*WC('d', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons153)
    def replacement998(f, b, d, a, c, x, e):
        rubi.append(998)
        return Dist((-a*f + b*e)/(-a*d + b*c), Int((a + b*x**S(4))**(S(-3)/4), x), x) - Dist((-c*f + d*e)/(-a*d + b*c), Int((a + b*x**S(4))**(S(1)/4)/(c + d*x**S(4)), x), x)
    rule998 = ReplacementRule(pattern998, replacement998)
    pattern999 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(e_ + x_**n_*WC('f', S(1)))/(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons4, cons632)
    def replacement999(p, f, b, d, a, n, c, x, e):
        rubi.append(999)
        return Dist(f/d, Int((a + b*x**n)**p, x), x) + Dist((-c*f + d*e)/d, Int((a + b*x**n)**p/(c + d*x**n), x), x)
    rule999 = ReplacementRule(pattern999, replacement999)
    pattern1000 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons50, cons633)
    def replacement1000(p, f, b, d, a, n, c, x, q, e):
        rubi.append(1000)
        return Dist(e, Int((a + b*x**n)**p*(c + d*x**n)**q, x), x) + Dist(f, Int(x**n*(a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule1000 = ReplacementRule(pattern1000, replacement1000)
    pattern1001 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('b', S(1)))*(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons153)
    def replacement1001(f, b, d, a, c, x, e):
        rubi.append(1001)
        return Dist(b/(-a*d + b*c), Int(S(1)/((a + b*x**S(2))*sqrt(e + f*x**S(2))), x), x) - Dist(d/(-a*d + b*c), Int(S(1)/((c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x)
    rule1001 = ReplacementRule(pattern1001, replacement1001)
    pattern1002 = Pattern(Integral(S(1)/(x_**S(2)*(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons7, cons27, cons48, cons125, cons176)
    def replacement1002(f, d, c, x, e):
        rubi.append(1002)
        return Dist(S(1)/c, Int(S(1)/(x**S(2)*sqrt(e + f*x**S(2))), x), x) - Dist(d/c, Int(S(1)/((c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x)
    rule1002 = ReplacementRule(pattern1002, replacement1002)
    pattern1003 = Pattern(Integral(sqrt(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons634, cons635, cons636)
    def replacement1003(f, b, d, a, c, x, e):
        rubi.append(1003)
        return Dist(d/b, Int(sqrt(e + f*x**S(2))/sqrt(c + d*x**S(2)), x), x) + Dist((-a*d + b*c)/b, Int(sqrt(e + f*x**S(2))/((a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x)
    rule1003 = ReplacementRule(pattern1003, replacement1003)
    pattern1004 = Pattern(Integral(sqrt(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons637)
    def replacement1004(f, b, d, a, c, x, e):
        rubi.append(1004)
        return Dist(d/b, Int(sqrt(e + f*x**S(2))/sqrt(c + d*x**S(2)), x), x) + Dist((-a*d + b*c)/b, Int(sqrt(e + f*x**S(2))/((a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x)
    rule1004 = ReplacementRule(pattern1004, replacement1004)
    pattern1005 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons573, cons638, cons636)
    def replacement1005(f, b, d, a, c, x, e):
        rubi.append(1005)
        return Dist(b/(-a*f + b*e), Int(sqrt(e + f*x**S(2))/((a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x) - Dist(f/(-a*f + b*e), Int(S(1)/(sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x)
    rule1005 = ReplacementRule(pattern1005, replacement1005)
    pattern1006 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons581, cons177, cons178, cons639)
    def replacement1006(f, b, d, a, c, x, e):
        rubi.append(1006)
        return Simp(EllipticPi(b*c/(a*d), asin(x*Rt(-d/c, S(2))), c*f/(d*e))/(a*sqrt(c)*sqrt(e)*Rt(-d/c, S(2))), x)
    rule1006 = ReplacementRule(pattern1006, replacement1006)
    pattern1007 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons117)
    def replacement1007(f, b, d, a, c, x, e):
        rubi.append(1007)
        return Dist(sqrt(S(1) + d*x**S(2)/c)/sqrt(c + d*x**S(2)), Int(S(1)/(sqrt(S(1) + d*x**S(2)/c)*(a + b*x**S(2))*sqrt(e + f*x**S(2))), x), x)
    rule1007 = ReplacementRule(pattern1007, replacement1007)
    pattern1008 = Pattern(Integral(sqrt(c_ + x_**S(2)*WC('d', S(1)))/((a_ + x_**S(2)*WC('b', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons573)
    def replacement1008(f, b, d, a, c, x, e):
        rubi.append(1008)
        return Simp(c*sqrt(e + f*x**S(2))*EllipticPi(S(1) - b*c/(a*d), ArcTan(x*Rt(d/c, S(2))), -c*f/(d*e) + S(1))/(a*e*sqrt(c*(e + f*x**S(2))/(e*(c + d*x**S(2))))*sqrt(c + d*x**S(2))*Rt(d/c, S(2))), x)
    rule1008 = ReplacementRule(pattern1008, replacement1008)
    pattern1009 = Pattern(Integral(sqrt(c_ + x_**S(2)*WC('d', S(1)))/((a_ + x_**S(2)*WC('b', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons581)
    def replacement1009(f, b, d, a, c, x, e):
        rubi.append(1009)
        return Dist(d/b, Int(S(1)/(sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x) + Dist((-a*d + b*c)/b, Int(S(1)/((a + b*x**S(2))*sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x)
    rule1009 = ReplacementRule(pattern1009, replacement1009)
    pattern1010 = Pattern(Integral(sqrt(e_ + x_**S(2)*WC('f', S(1)))/((a_ + x_**S(2)*WC('b', S(1)))*(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons573, cons638)
    def replacement1010(f, b, d, a, c, x, e):
        rubi.append(1010)
        return Dist(b/(-a*d + b*c), Int(sqrt(e + f*x**S(2))/((a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x) - Dist(d/(-a*d + b*c), Int(sqrt(e + f*x**S(2))/(c + d*x**S(2))**(S(3)/2), x), x)
    rule1010 = ReplacementRule(pattern1010, replacement1010)
    pattern1011 = Pattern(Integral((e_ + x_**S(2)*WC('f', S(1)))**(S(3)/2)/((a_ + x_**S(2)*WC('b', S(1)))*(c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons573, cons638)
    def replacement1011(f, b, d, a, c, x, e):
        rubi.append(1011)
        return Dist((-a*f + b*e)/(-a*d + b*c), Int(sqrt(e + f*x**S(2))/((a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x) - Dist((-c*f + d*e)/(-a*d + b*c), Int(sqrt(e + f*x**S(2))/(c + d*x**S(2))**(S(3)/2), x), x)
    rule1011 = ReplacementRule(pattern1011, replacement1011)
    pattern1012 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**(S(3)/2)*sqrt(e_ + x_**S(2)*WC('f', S(1)))/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons573, cons638)
    def replacement1012(f, b, d, a, c, x, e):
        rubi.append(1012)
        return Dist(d/b**S(2), Int(sqrt(e + f*x**S(2))*(-a*d + S(2)*b*c + b*d*x**S(2))/sqrt(c + d*x**S(2)), x), x) + Dist((-a*d + b*c)**S(2)/b**S(2), Int(sqrt(e + f*x**S(2))/((a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x)
    rule1012 = ReplacementRule(pattern1012, replacement1012)
    pattern1013 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**q_*(e_ + x_**S(2)*WC('f', S(1)))**r_/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons640, cons396, cons641)
    def replacement1013(f, b, r, d, a, c, x, q, e):
        rubi.append(1013)
        return Dist(b*(-a*f + b*e)/(-a*d + b*c)**S(2), Int((c + d*x**S(2))**(q + S(2))*(e + f*x**S(2))**(r + S(-1))/(a + b*x**S(2)), x), x) - Dist((-a*d + b*c)**(S(-2)), Int((c + d*x**S(2))**q*(e + f*x**S(2))**(r + S(-1))*(-a*d**S(2)*e - b*c**S(2)*f + S(2)*b*c*d*e + d**S(2)*x**S(2)*(-a*f + b*e)), x), x)
    rule1013 = ReplacementRule(pattern1013, replacement1013)
    pattern1014 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**q_*(e_ + x_**S(2)*WC('f', S(1)))**r_/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons52, cons395, cons576)
    def replacement1014(f, b, r, d, a, c, x, q, e):
        rubi.append(1014)
        return Dist(d/b, Int((c + d*x**S(2))**(q + S(-1))*(e + f*x**S(2))**r, x), x) + Dist((-a*d + b*c)/b, Int((c + d*x**S(2))**(q + S(-1))*(e + f*x**S(2))**r/(a + b*x**S(2)), x), x)
    rule1014 = ReplacementRule(pattern1014, replacement1014)
    pattern1015 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**q_*(e_ + x_**S(2)*WC('f', S(1)))**r_/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons52, cons395, cons396)
    def replacement1015(f, b, r, d, a, c, x, q, e):
        rubi.append(1015)
        return Dist(b**S(2)/(-a*d + b*c)**S(2), Int((c + d*x**S(2))**(q + S(2))*(e + f*x**S(2))**r/(a + b*x**S(2)), x), x) - Dist(d/(-a*d + b*c)**S(2), Int((c + d*x**S(2))**q*(e + f*x**S(2))**r*(-a*d + S(2)*b*c + b*d*x**S(2)), x), x)
    rule1015 = ReplacementRule(pattern1015, replacement1015)
    pattern1016 = Pattern(Integral((c_ + x_**S(2)*WC('d', S(1)))**q_*(e_ + x_**S(2)*WC('f', S(1)))**r_/(a_ + x_**S(2)*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons52, cons395, cons642)
    def replacement1016(f, b, r, d, a, c, x, q, e):
        rubi.append(1016)
        return Dist(b/(-a*d + b*c), Int((c + d*x**S(2))**(q + S(1))*(e + f*x**S(2))**r/(a + b*x**S(2)), x), x) - Dist(d/(-a*d + b*c), Int((c + d*x**S(2))**q*(e + f*x**S(2))**r, x), x)
    rule1016 = ReplacementRule(pattern1016, replacement1016)
    pattern1017 = Pattern(Integral(sqrt(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))/(a_ + x_**S(2)*WC('b', S(1)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons153)
    def replacement1017(f, b, d, a, c, x, e):
        rubi.append(1017)
        return Dist((-a**S(2)*d*f + b**S(2)*c*e)/(S(2)*a*b**S(2)), Int(S(1)/((a + b*x**S(2))*sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x) + Dist(d*f/(S(2)*a*b**S(2)), Int((a - b*x**S(2))/(sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x) + Simp(x*sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))/(S(2)*a*(a + b*x**S(2))), x)
    rule1017 = ReplacementRule(pattern1017, replacement1017)
    pattern1018 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('b', S(1)))**S(2)*sqrt(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons153)
    def replacement1018(f, b, d, a, c, x, e):
        rubi.append(1018)
        return Dist((S(3)*a**S(2)*d*f - S(2)*a*b*(c*f + d*e) + b**S(2)*c*e)/(S(2)*a*(-a*d + b*c)*(-a*f + b*e)), Int(S(1)/((a + b*x**S(2))*sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x) - Dist(d*f/(S(2)*a*(-a*d + b*c)*(-a*f + b*e)), Int((a + b*x**S(2))/(sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x) + Simp(b**S(2)*x*sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))/(S(2)*a*(a + b*x**S(2))*(-a*d + b*c)*(-a*f + b*e)), x)
    rule1018 = ReplacementRule(pattern1018, replacement1018)
    pattern1019 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_*(e_ + x_**n_*WC('f', S(1)))**r_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons52, cons63, cons395, cons403)
    def replacement1019(p, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1019)
        return Dist(d/b, Int((a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*(e + f*x**n)**r, x), x) + Dist((-a*d + b*c)/b, Int((a + b*x**n)**p*(c + d*x**n)**(q + S(-1))*(e + f*x**n)**r, x), x)
    rule1019 = ReplacementRule(pattern1019, replacement1019)
    pattern1020 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_*(e_ + x_**n_*WC('f', S(1)))**r_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons50, cons63, cons395, cons642)
    def replacement1020(p, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1020)
        return Dist(b/(-a*d + b*c), Int((a + b*x**n)**p*(c + d*x**n)**(q + S(1))*(e + f*x**n)**r, x), x) - Dist(d/(-a*d + b*c), Int((a + b*x**n)**(p + S(1))*(c + d*x**n)**q*(e + f*x**n)**r, x), x)
    rule1020 = ReplacementRule(pattern1020, replacement1020)
    pattern1021 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons153)
    def replacement1021(f, b, d, a, c, x, e):
        rubi.append(1021)
        return Dist(sqrt(a*(e + f*x**S(2))/(e*(a + b*x**S(2))))*sqrt(c + d*x**S(2))/(c*sqrt(a*(c + d*x**S(2))/(c*(a + b*x**S(2))))*sqrt(e + f*x**S(2))), Subst(Int(S(1)/(sqrt(S(1) - x**S(2)*(-a*d + b*c)/c)*sqrt(S(1) - x**S(2)*(-a*f + b*e)/e)), x), x, x/sqrt(a + b*x**S(2))), x)
    rule1021 = ReplacementRule(pattern1021, replacement1021)
    pattern1022 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))/(sqrt(c_ + x_**S(2)*WC('d', S(1)))*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons153)
    def replacement1022(f, b, d, a, c, x, e):
        rubi.append(1022)
        return Dist(a*sqrt(a*(e + f*x**S(2))/(e*(a + b*x**S(2))))*sqrt(c + d*x**S(2))/(c*sqrt(a*(c + d*x**S(2))/(c*(a + b*x**S(2))))*sqrt(e + f*x**S(2))), Subst(Int(S(1)/(sqrt(S(1) - x**S(2)*(-a*d + b*c)/c)*sqrt(S(1) - x**S(2)*(-a*f + b*e)/e)*(-b*x**S(2) + S(1))), x), x, x/sqrt(a + b*x**S(2))), x)
    rule1022 = ReplacementRule(pattern1022, replacement1022)
    pattern1023 = Pattern(Integral(sqrt(c_ + x_**S(2)*WC('d', S(1)))/((a_ + x_**S(2)*WC('b', S(1)))**(S(3)/2)*sqrt(e_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons153)
    def replacement1023(f, b, d, a, c, x, e):
        rubi.append(1023)
        return Dist(sqrt(a*(e + f*x**S(2))/(e*(a + b*x**S(2))))*sqrt(c + d*x**S(2))/(a*sqrt(a*(c + d*x**S(2))/(c*(a + b*x**S(2))))*sqrt(e + f*x**S(2))), Subst(Int(sqrt(S(1) - x**S(2)*(-a*d + b*c)/c)/sqrt(S(1) - x**S(2)*(-a*f + b*e)/e), x), x, x/sqrt(a + b*x**S(2))), x)
    rule1023 = ReplacementRule(pattern1023, replacement1023)
    pattern1024 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))/sqrt(e_ + x_**S(2)*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons643)
    def replacement1024(f, b, d, a, c, x, e):
        rubi.append(1024)
        return -Dist(c*(-c*f + d*e)/(S(2)*f), Int(sqrt(a + b*x**S(2))/((c + d*x**S(2))**(S(3)/2)*sqrt(e + f*x**S(2))), x), x) - Dist((-a*d*f - b*c*f + b*d*e)/(S(2)*d*f), Int(sqrt(c + d*x**S(2))/(sqrt(a + b*x**S(2))*sqrt(e + f*x**S(2))), x), x) + Dist(b*c*(-c*f + d*e)/(S(2)*d*f), Int(S(1)/(sqrt(a + b*x**S(2))*sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x) + Simp(d*x*sqrt(a + b*x**S(2))*sqrt(e + f*x**S(2))/(S(2)*f*sqrt(c + d*x**S(2))), x)
    rule1024 = ReplacementRule(pattern1024, replacement1024)
    pattern1025 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))/sqrt(e_ + x_**S(2)*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons644)
    def replacement1025(f, b, d, a, c, x, e):
        rubi.append(1025)
        return -Dist((-a*d*f - b*c*f + b*d*e)/(S(2)*f**S(2)), Int(sqrt(e + f*x**S(2))/(sqrt(a + b*x**S(2))*sqrt(c + d*x**S(2))), x), x) + Dist(e*(-a*f + b*e)/(S(2)*f), Int(sqrt(c + d*x**S(2))/(sqrt(a + b*x**S(2))*(e + f*x**S(2))**(S(3)/2)), x), x) + Dist((-a*f + b*e)*(-S(2)*c*f + d*e)/(S(2)*f**S(2)), Int(S(1)/(sqrt(a + b*x**S(2))*sqrt(c + d*x**S(2))*sqrt(e + f*x**S(2))), x), x) + Simp(x*sqrt(a + b*x**S(2))*sqrt(c + d*x**S(2))/(S(2)*sqrt(e + f*x**S(2))), x)
    rule1025 = ReplacementRule(pattern1025, replacement1025)
    pattern1026 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('b', S(1)))*sqrt(c_ + x_**S(2)*WC('d', S(1)))/(e_ + x_**S(2)*WC('f', S(1)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons153)
    def replacement1026(f, b, d, a, c, x, e):
        rubi.append(1026)
        return Dist(b/f, Int(sqrt(c + d*x**S(2))/(sqrt(a + b*x**S(2))*sqrt(e + f*x**S(2))), x), x) - Dist((-a*f + b*e)/f, Int(sqrt(c + d*x**S(2))/(sqrt(a + b*x**S(2))*(e + f*x**S(2))**(S(3)/2)), x), x)
    rule1026 = ReplacementRule(pattern1026, replacement1026)
    def With1027(p, f, b, r, d, a, n, c, x, q, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        u = ExpandIntegrand((a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x)
        if SumQ(u):
            return True
        return False
    pattern1027 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_*(e_ + x_**n_*WC('f', S(1)))**r_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons52, cons148, CustomConstraint(With1027))
    def replacement1027(p, f, b, r, d, a, n, c, x, q, e):

        u = ExpandIntegrand((a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x)
        rubi.append(1027)
        return Int(u, x)
    rule1027 = ReplacementRule(pattern1027, replacement1027)
    pattern1028 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_*(e_ + x_**n_*WC('f', S(1)))**r_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons52, cons196)
    def replacement1028(p, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1028)
        return -Subst(Int((a + b*x**(-n))**p*(c + d*x**(-n))**q*(e + f*x**(-n))**r/x**S(2), x), x, S(1)/x)
    rule1028 = ReplacementRule(pattern1028, replacement1028)
    pattern1029 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons50, cons52, cons645)
    def replacement1029(p, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1029)
        return Int((a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x)
    rule1029 = ReplacementRule(pattern1029, replacement1029)
    pattern1030 = Pattern(Integral((u_**n_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(v_**n_*WC('d', S(1)) + WC('c', S(0)))**WC('q', S(1))*(w_**n_*WC('f', S(1)) + WC('e', S(0)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons4, cons50, cons52, cons646, cons647, cons68, cons69)
    def replacement1030(v, w, p, u, f, b, r, d, c, a, n, x, q, e):
        rubi.append(1030)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x), x, u), x)
    rule1030 = ReplacementRule(pattern1030, replacement1030)
    pattern1031 = Pattern(Integral((c_ + x_**WC('mn', S(1))*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**WC('n', S(1))*WC('f', S(1)))**WC('r', S(1))*(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons52, cons585, cons586)
    def replacement1031(mn, p, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1031)
        return Int(x**(-n*q)*(a + b*x**n)**p*(e + f*x**n)**r*(c*x**n + d)**q, x)
    rule1031 = ReplacementRule(pattern1031, replacement1031)
    pattern1032 = Pattern(Integral((c_ + x_**WC('mn', S(1))*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**WC('n', S(1))*WC('f', S(1)))**WC('r', S(1))*(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons50, cons585, cons38, cons648)
    def replacement1032(mn, p, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1032)
        return Int(x**(n*(p + r))*(c + d*x**(-n))**q*(a*x**(-n) + b)**p*(e*x**(-n) + f)**r, x)
    rule1032 = ReplacementRule(pattern1032, replacement1032)
    pattern1033 = Pattern(Integral((c_ + x_**WC('mn', S(1))*WC('d', S(1)))**q_*(e_ + x_**WC('n', S(1))*WC('f', S(1)))**WC('r', S(1))*(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons50, cons52, cons585, cons386)
    def replacement1033(mn, p, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1033)
        return Dist(x**(n*FracPart(q))*(c + d*x**(-n))**FracPart(q)*(c*x**n + d)**(-FracPart(q)), Int(x**(-n*q)*(a + b*x**n)**p*(e + f*x**n)**r*(c*x**n + d)**q, x), x)
    rule1033 = ReplacementRule(pattern1033, replacement1033)
    pattern1034 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e1_ + x_**WC('n2', S(1))*WC('f1', S(1)))**WC('r', S(1))*(e2_ + x_**WC('n2', S(1))*WC('f2', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons652, cons653, cons654, cons655, cons4, cons5, cons50, cons52, cons649, cons650, cons651)
    def replacement1034(p, f2, b, n2, r, d, e2, f1, a, n, c, e1, x, q):
        rubi.append(1034)
        return Int((a + b*x**n)**p*(c + d*x**n)**q*(e1*e2 + f1*f2*x**n)**r, x)
    rule1034 = ReplacementRule(pattern1034, replacement1034)
    pattern1035 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e1_ + x_**WC('n2', S(1))*WC('f1', S(1)))**WC('r', S(1))*(e2_ + x_**WC('n2', S(1))*WC('f2', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons652, cons653, cons654, cons655, cons4, cons5, cons50, cons52, cons649, cons650)
    def replacement1035(p, f2, b, n2, r, d, e2, f1, a, n, c, e1, x, q):
        rubi.append(1035)
        return Dist((e1 + f1*x**(n/S(2)))**FracPart(r)*(e2 + f2*x**(n/S(2)))**FracPart(r)*(e1*e2 + f1*f2*x**n)**(-FracPart(r)), Int((a + b*x**n)**p*(c + d*x**n)**q*(e1*e2 + f1*f2*x**n)**r, x), x)
    rule1035 = ReplacementRule(pattern1035, replacement1035)
    pattern1036 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons52, cons656, cons500)
    def replacement1036(p, m, g, b, f, r, d, c, n, x, q, e):
        rubi.append(1036)
        return Dist(b**(S(1) - (m + S(1))/n)*g**m/n, Subst(Int((b*x)**(p + S(-1) + (m + S(1))/n)*(c + d*x)**q*(e + f*x)**r, x), x, x**n), x)
    rule1036 = ReplacementRule(pattern1036, replacement1036)
    pattern1037 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(x_**WC('n', S(1))*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons52, cons656, cons501)
    def replacement1037(p, m, g, b, f, r, d, c, n, x, q, e):
        rubi.append(1037)
        return Dist(b**IntPart(p)*g**m*x**(-n*FracPart(p))*(b*x**n)**FracPart(p), Int(x**(m + n*p)*(c + d*x**n)**q*(e + f*x**n)**r, x), x)
    rule1037 = ReplacementRule(pattern1037, replacement1037)
    pattern1038 = Pattern(Integral((g_*x_)**m_*(x_**WC('n', S(1))*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons52, cons18)
    def replacement1038(p, m, f, b, r, g, d, c, n, x, q, e):
        rubi.append(1038)
        return Dist(g**IntPart(m)*x**(-FracPart(m))*(g*x)**FracPart(m), Int(x**m*(b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x), x)
    rule1038 = ReplacementRule(pattern1038, replacement1038)
    pattern1039 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons657)
    def replacement1039(p, m, g, b, f, r, d, a, n, c, x, q, e):
        rubi.append(1039)
        return Int(ExpandIntegrand((g*x)**m*(a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x), x)
    rule1039 = ReplacementRule(pattern1039, replacement1039)
    pattern1040 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons50, cons52, cons53)
    def replacement1040(p, m, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1040)
        return Dist(S(1)/n, Subst(Int((a + b*x)**p*(c + d*x)**q*(e + f*x)**r, x), x, x**n), x)
    rule1040 = ReplacementRule(pattern1040, replacement1040)
    pattern1041 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons658, cons502)
    def replacement1041(p, m, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1041)
        return Int(x**(m + n*(p + q + r))*(a*x**(-n) + b)**p*(c*x**(-n) + d)**q*(e*x**(-n) + f)**r, x)
    rule1041 = ReplacementRule(pattern1041, replacement1041)
    pattern1042 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons50, cons52, cons500)
    def replacement1042(p, m, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1042)
        return Dist(S(1)/n, Subst(Int(x**(S(-1) + (m + S(1))/n)*(a + b*x)**p*(c + d*x)**q*(e + f*x)**r, x), x, x**n), x)
    rule1042 = ReplacementRule(pattern1042, replacement1042)
    pattern1043 = Pattern(Integral((g_*x_)**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons52, cons500)
    def replacement1043(p, m, f, b, r, g, d, a, n, c, x, q, e):
        rubi.append(1043)
        return Dist(g**IntPart(m)*x**(-FracPart(m))*(g*x)**FracPart(m), Int(x**m*(a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x), x)
    rule1043 = ReplacementRule(pattern1043, replacement1043)
    def With1044(p, m, f, b, r, d, a, n, c, x, q, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        k = GCD(m + S(1), n)
        if Unequal(k, S(1)):
            return True
        return False
    pattern1044 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons52, cons148, cons17, CustomConstraint(With1044))
    def replacement1044(p, m, f, b, r, d, a, n, c, x, q, e):

        k = GCD(m + S(1), n)
        rubi.append(1044)
        return Dist(S(1)/k, Subst(Int(x**(S(-1) + (m + S(1))/k)*(a + b*x**(n/k))**p*(c + d*x**(n/k))**q*(e + f*x**(n/k))**r, x), x, x**k), x)
    rule1044 = ReplacementRule(pattern1044, replacement1044)
    def With1045(p, m, f, g, b, r, d, a, n, c, x, q, e):
        k = Denominator(m)
        rubi.append(1045)
        return Dist(k/g, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a + b*g**(-n)*x**(k*n))**p*(c + d*g**(-n)*x**(k*n))**q*(e + f*g**(-n)*x**(k*n))**r, x), x, (g*x)**(S(1)/k)), x)
    pattern1045 = Pattern(Integral((x_*WC('g', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_*(e_ + x_**n_*WC('f', S(1)))**r_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons50, cons52, cons148, cons367)
    rule1045 = ReplacementRule(pattern1045, With1045)
    pattern1046 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons148, cons402, cons137, cons403, cons659)
    def replacement1046(p, m, g, b, f, d, a, n, c, x, q, e):
        rubi.append(1046)
        return Dist(S(1)/(a*b*n*(p + S(1))), Int((g*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*Simp(c*(b*e*n*(p + S(1)) + (m + S(1))*(-a*f + b*e)) + d*x**n*(b*e*n*(p + S(1)) + (-a*f + b*e)*(m + n*q + S(1))), x), x), x) - Simp((g*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*(-a*f + b*e)/(a*b*g*n*(p + S(1))), x)
    rule1046 = ReplacementRule(pattern1046, replacement1046)
    pattern1047 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons50, cons148, cons244, cons137, cons607)
    def replacement1047(p, m, f, g, b, d, a, n, c, x, q, e):
        rubi.append(1047)
        return -Dist(g**n/(b*n*(p + S(1))*(-a*d + b*c)), Int((g*x)**(m - n)*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*Simp(c*(-a*f + b*e)*(m - n + S(1)) + x**n*(-b*n*(p + S(1))*(c*f - d*e) + d*(-a*f + b*e)*(m + n*q + S(1))), x), x), x) + Simp(g**(n + S(-1))*(g*x)**(m - n + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))*(-a*f + b*e)/(b*n*(p + S(1))*(-a*d + b*c)), x)
    rule1047 = ReplacementRule(pattern1047, replacement1047)
    pattern1048 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons50, cons148, cons13, cons137)
    def replacement1048(p, m, f, g, b, d, a, n, c, x, q, e):
        rubi.append(1048)
        return Dist(S(1)/(a*n*(p + S(1))*(-a*d + b*c)), Int((g*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*Simp(c*(m + S(1))*(-a*f + b*e) + d*x**n*(-a*f + b*e)*(m + n*(p + q + S(2)) + S(1)) + e*n*(p + S(1))*(-a*d + b*c), x), x), x) - Simp((g*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))*(-a*f + b*e)/(a*g*n*(p + S(1))*(-a*d + b*c)), x)
    rule1048 = ReplacementRule(pattern1048, replacement1048)
    pattern1049 = Pattern(Integral((x_*WC('g', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons148, cons611, cons403, cons94, cons660)
    def replacement1049(p, m, g, b, f, d, a, n, c, x, q, e):
        rubi.append(1049)
        return -Dist(g**(-n)/(a*(m + S(1))), Int((g*x)**(m + n)*(a + b*x**n)**p*(c + d*x**n)**(q + S(-1))*Simp(c*(m + S(1))*(-a*f + b*e) + d*x**n*(b*e*n*(p + q + S(1)) + (m + S(1))*(-a*f + b*e)) + e*n*(a*d*q + b*c*(p + S(1))), x), x), x) + Simp(e*(g*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(a*g*(m + S(1))), x)
    rule1049 = ReplacementRule(pattern1049, replacement1049)
    pattern1050 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons148, cons395, cons403, cons660)
    def replacement1050(p, m, g, b, f, d, a, n, c, x, q, e):
        rubi.append(1050)
        return Dist(S(1)/(b*(m + n*(p + q + S(1)) + S(1))), Int((g*x)**m*(a + b*x**n)**p*(c + d*x**n)**(q + S(-1))*Simp(c*(b*e*n*(p + q + S(1)) + (m + S(1))*(-a*f + b*e)) + x**n*(b*d*e*n*(p + q + S(1)) + d*(m + S(1))*(-a*f + b*e) + f*n*q*(-a*d + b*c)), x), x), x) + Simp(f*(g*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(b*g*(m + n*(p + q + S(1)) + S(1))), x)
    rule1050 = ReplacementRule(pattern1050, replacement1050)
    pattern1051 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons50, cons148, cons31, cons530)
    def replacement1051(p, m, g, b, f, d, a, n, c, x, q, e):
        rubi.append(1051)
        return -Dist(g**n/(b*d*(m + n*(p + q + S(1)) + S(1))), Int((g*x)**(m - n)*(a + b*x**n)**p*(c + d*x**n)**q*Simp(a*c*f*(m - n + S(1)) + x**n*(a*d*f*(m + n*q + S(1)) + b*(c*f*(m + n*p + S(1)) - d*e*(m + n*(p + q + S(1)) + S(1)))), x), x), x) + Simp(f*g**(n + S(-1))*(g*x)**(m - n + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(b*d*(m + n*(p + q + S(1)) + S(1))), x)
    rule1051 = ReplacementRule(pattern1051, replacement1051)
    pattern1052 = Pattern(Integral((x_*WC('g', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons50, cons148, cons31, cons94)
    def replacement1052(p, m, g, b, f, d, a, n, c, x, q, e):
        rubi.append(1052)
        return Dist(g**(-n)/(a*c*(m + S(1))), Int((g*x)**(m + n)*(a + b*x**n)**p*(c + d*x**n)**q*Simp(a*c*f*(m + S(1)) - b*d*e*x**n*(m + n*(p + q + S(2)) + S(1)) - e*n*(a*d*q + b*c*p) - e*(a*d + b*c)*(m + n + S(1)), x), x), x) + Simp(e*(g*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))/(a*c*g*(m + S(1))), x)
    rule1052 = ReplacementRule(pattern1052, replacement1052)
    pattern1053 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(e_ + x_**n_*WC('f', S(1)))/(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons148)
    def replacement1053(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(1053)
        return Int(ExpandIntegrand((g*x)**m*(a + b*x**n)**p*(e + f*x**n)/(c + d*x**n), x), x)
    rule1053 = ReplacementRule(pattern1053, replacement1053)
    pattern1054 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons50, cons148)
    def replacement1054(p, m, g, b, f, d, a, n, c, x, q, e):
        rubi.append(1054)
        return Dist(e, Int((g*x)**m*(a + b*x**n)**p*(c + d*x**n)**q, x), x) + Dist(e**(-n)*f, Int((g*x)**(m + n)*(a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule1054 = ReplacementRule(pattern1054, replacement1054)
    pattern1055 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons50, cons148, cons661)
    def replacement1055(p, m, g, b, f, r, d, a, n, c, x, q, e):
        rubi.append(1055)
        return Dist(e, Int((g*x)**m*(a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**(r + S(-1)), x), x) + Dist(e**(-n)*f, Int((g*x)**(m + n)*(a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**(r + S(-1)), x), x)
    rule1055 = ReplacementRule(pattern1055, replacement1055)
    pattern1056 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons52, cons196, cons17)
    def replacement1056(p, m, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1056)
        return -Subst(Int(x**(-m + S(-2))*(a + b*x**(-n))**p*(c + d*x**(-n))**q*(e + f*x**(-n))**r, x), x, S(1)/x)
    rule1056 = ReplacementRule(pattern1056, replacement1056)
    def With1057(p, m, g, b, f, r, d, a, n, c, x, q, e):
        k = Denominator(m)
        rubi.append(1057)
        return -Dist(k/g, Subst(Int(x**(-k*(m + S(1)) + S(-1))*(a + b*g**(-n)*x**(-k*n))**p*(c + d*g**(-n)*x**(-k*n))**q*(e + f*g**(-n)*x**(-k*n))**r, x), x, (g*x)**(-S(1)/k)), x)
    pattern1057 = Pattern(Integral((x_*WC('g', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons50, cons52, cons196, cons367)
    rule1057 = ReplacementRule(pattern1057, With1057)
    pattern1058 = Pattern(Integral((x_*WC('g', S(1)))**m_*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons50, cons52, cons196, cons356)
    def replacement1058(p, m, g, b, f, r, d, a, n, c, x, q, e):
        rubi.append(1058)
        return -Dist((g*x)**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(a + b*x**(-n))**p*(c + d*x**(-n))**q*(e + f*x**(-n))**r, x), x, S(1)/x), x)
    rule1058 = ReplacementRule(pattern1058, replacement1058)
    def With1059(p, m, f, b, r, d, a, n, c, x, q, e):
        k = Denominator(n)
        rubi.append(1059)
        return Dist(k, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a + b*x**(k*n))**p*(c + d*x**(k*n))**q*(e + f*x**(k*n))**r, x), x, x**(S(1)/k)), x)
    pattern1059 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons50, cons52, cons489)
    rule1059 = ReplacementRule(pattern1059, With1059)
    pattern1060 = Pattern(Integral((g_*x_)**m_*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons50, cons52, cons489)
    def replacement1060(p, m, f, b, r, g, d, a, n, c, x, q, e):
        rubi.append(1060)
        return Dist(g**IntPart(m)*x**(-FracPart(m))*(g*x)**FracPart(m), Int(x**m*(a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x), x)
    rule1060 = ReplacementRule(pattern1060, replacement1060)
    pattern1061 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons50, cons52, cons541)
    def replacement1061(p, m, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1061)
        return Dist(S(1)/(m + S(1)), Subst(Int((a + b*x**(n/(m + S(1))))**p*(c + d*x**(n/(m + S(1))))**q*(e + f*x**(n/(m + S(1))))**r, x), x, x**(m + S(1))), x)
    rule1061 = ReplacementRule(pattern1061, replacement1061)
    pattern1062 = Pattern(Integral((g_*x_)**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons52, cons541)
    def replacement1062(p, m, f, b, r, g, d, a, n, c, x, q, e):
        rubi.append(1062)
        return Dist(g**IntPart(m)*x**(-FracPart(m))*(g*x)**FracPart(m), Int(x**m*(a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x), x)
    rule1062 = ReplacementRule(pattern1062, replacement1062)
    pattern1063 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons402, cons137, cons403, cons659)
    def replacement1063(p, m, g, b, f, d, a, n, c, x, q, e):
        rubi.append(1063)
        return Dist(S(1)/(a*b*n*(p + S(1))), Int((g*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(-1))*Simp(c*(b*e*n*(p + S(1)) + (m + S(1))*(-a*f + b*e)) + d*x**n*(b*e*n*(p + S(1)) + (-a*f + b*e)*(m + n*q + S(1))), x), x), x) - Simp((g*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*(-a*f + b*e)/(a*b*g*n*(p + S(1))), x)
    rule1063 = ReplacementRule(pattern1063, replacement1063)
    pattern1064 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons50, cons13, cons137)
    def replacement1064(p, m, f, g, b, d, a, n, c, x, q, e):
        rubi.append(1064)
        return Dist(S(1)/(a*n*(p + S(1))*(-a*d + b*c)), Int((g*x)**m*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q*Simp(c*(m + S(1))*(-a*f + b*e) + d*x**n*(-a*f + b*e)*(m + n*(p + q + S(2)) + S(1)) + e*n*(p + S(1))*(-a*d + b*c), x), x), x) - Simp((g*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**(q + S(1))*(-a*f + b*e)/(a*g*n*(p + S(1))*(-a*d + b*c)), x)
    rule1064 = ReplacementRule(pattern1064, replacement1064)
    pattern1065 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons395, cons403, cons660)
    def replacement1065(p, m, g, b, f, d, a, n, c, x, q, e):
        rubi.append(1065)
        return Dist(S(1)/(b*(m + n*(p + q + S(1)) + S(1))), Int((g*x)**m*(a + b*x**n)**p*(c + d*x**n)**(q + S(-1))*Simp(c*(b*e*n*(p + q + S(1)) + (m + S(1))*(-a*f + b*e)) + x**n*(b*d*e*n*(p + q + S(1)) + d*(m + S(1))*(-a*f + b*e) + f*n*q*(-a*d + b*c)), x), x), x) + Simp(f*(g*x)**(m + S(1))*(a + b*x**n)**(p + S(1))*(c + d*x**n)**q/(b*g*(m + n*(p + q + S(1)) + S(1))), x)
    rule1065 = ReplacementRule(pattern1065, replacement1065)
    pattern1066 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(e_ + x_**n_*WC('f', S(1)))/(c_ + x_**n_*WC('d', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons380)
    def replacement1066(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(1066)
        return Int(ExpandIntegrand((g*x)**m*(a + b*x**n)**p*(e + f*x**n)/(c + d*x**n), x), x)
    rule1066 = ReplacementRule(pattern1066, replacement1066)
    pattern1067 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*(c_ + x_**n_*WC('d', S(1)))**q_*(e_ + x_**n_*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons662)
    def replacement1067(p, m, f, g, b, d, a, n, c, x, q, e):
        rubi.append(1067)
        return Dist(e, Int((g*x)**m*(a + b*x**n)**p*(c + d*x**n)**q, x), x) + Dist(f*x**(-m)*(g*x)**m, Int(x**(m + n)*(a + b*x**n)**p*(c + d*x**n)**q, x), x)
    rule1067 = ReplacementRule(pattern1067, replacement1067)
    pattern1068 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**WC('n', S(1))*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**WC('mn', S(1))*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**WC('n', S(1))*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons52, cons585, cons586)
    def replacement1068(mn, p, m, f, b, r, d, c, n, a, x, q, e):
        rubi.append(1068)
        return Int(x**(m - n*q)*(a + b*x**n)**p*(e + f*x**n)**r*(c*x**n + d)**q, x)
    rule1068 = ReplacementRule(pattern1068, replacement1068)
    pattern1069 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**WC('mn', S(1))*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**WC('n', S(1))*WC('f', S(1)))**WC('r', S(1))*(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons50, cons585, cons38, cons648)
    def replacement1069(mn, p, m, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1069)
        return Int(x**(m + n*(p + r))*(c + d*x**(-n))**q*(a*x**(-n) + b)**p*(e*x**(-n) + f)**r, x)
    rule1069 = ReplacementRule(pattern1069, replacement1069)
    pattern1070 = Pattern(Integral(x_**WC('m', S(1))*(c_ + x_**WC('mn', S(1))*WC('d', S(1)))**q_*(e_ + x_**WC('n', S(1))*WC('f', S(1)))**WC('r', S(1))*(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons50, cons52, cons585, cons386)
    def replacement1070(mn, p, m, f, b, r, d, a, n, c, x, q, e):
        rubi.append(1070)
        return Dist(x**(n*FracPart(q))*(c + d*x**(-n))**FracPart(q)*(c*x**n + d)**(-FracPart(q)), Int(x**(m - n*q)*(a + b*x**n)**p*(e + f*x**n)**r*(c*x**n + d)**q, x), x)
    rule1070 = ReplacementRule(pattern1070, replacement1070)
    pattern1071 = Pattern(Integral((g_*x_)**m_*(a_ + x_**WC('n', S(1))*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**WC('mn', S(1))*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**WC('n', S(1))*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons52, cons585)
    def replacement1071(mn, p, m, f, b, r, g, d, c, n, a, x, q, e):
        rubi.append(1071)
        return Dist(g**IntPart(m)*x**(-FracPart(m))*(g*x)**FracPart(m), Int(x**m*(a + b*x**n)**p*(c + d*x**(-n))**q*(e + f*x**n)**r, x), x)
    rule1071 = ReplacementRule(pattern1071, replacement1071)
    pattern1072 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e_ + x_**n_*WC('f', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons50, cons52, cons663)
    def replacement1072(p, m, g, b, f, r, d, a, n, c, x, q, e):
        rubi.append(1072)
        return Int((g*x)**m*(a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x)
    rule1072 = ReplacementRule(pattern1072, replacement1072)
    pattern1073 = Pattern(Integral(u_**WC('m', S(1))*(e_ + v_**n_*WC('f', S(1)))**WC('r', S(1))*(v_**n_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(v_**n_*WC('d', S(1)) + WC('c', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons50, cons52, cons554)
    def replacement1073(v, p, u, m, f, b, r, d, c, a, n, x, q, e):
        rubi.append(1073)
        return Dist(u**m*v**(-m)/Coefficient(v, x, S(1)), Subst(Int(x**m*(a + b*x**n)**p*(c + d*x**n)**q*(e + f*x**n)**r, x), x, v), x)
    rule1073 = ReplacementRule(pattern1073, replacement1073)
    pattern1074 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e1_ + x_**WC('n2', S(1))*WC('f1', S(1)))**WC('r', S(1))*(e2_ + x_**WC('n2', S(1))*WC('f2', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons652, cons653, cons654, cons655, cons208, cons21, cons4, cons5, cons50, cons52, cons649, cons650, cons651)
    def replacement1074(p, m, g, f2, n2, r, b, d, e2, f1, a, n, c, e1, x, q):
        rubi.append(1074)
        return Int((g*x)**m*(a + b*x**n)**p*(c + d*x**n)**q*(e1*e2 + f1*f2*x**n)**r, x)
    rule1074 = ReplacementRule(pattern1074, replacement1074)
    pattern1075 = Pattern(Integral((x_*WC('g', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*(c_ + x_**n_*WC('d', S(1)))**WC('q', S(1))*(e1_ + x_**WC('n2', S(1))*WC('f1', S(1)))**WC('r', S(1))*(e2_ + x_**WC('n2', S(1))*WC('f2', S(1)))**WC('r', S(1)), x_), cons2, cons3, cons7, cons27, cons652, cons653, cons654, cons655, cons208, cons21, cons4, cons5, cons50, cons52, cons649, cons650)
    def replacement1075(p, m, g, f2, n2, r, b, d, e2, f1, a, n, c, e1, x, q):
        rubi.append(1075)
        return Dist((e1 + f1*x**(n/S(2)))**FracPart(r)*(e2 + f2*x**(n/S(2)))**FracPart(r)*(e1*e2 + f1*f2*x**n)**(-FracPart(r)), Int((g*x)**m*(a + b*x**n)**p*(c + d*x**n)**q*(e1*e2 + f1*f2*x**n)**r, x), x)
    rule1075 = ReplacementRule(pattern1075, replacement1075)
    return [rule689, rule690, rule691, rule692, rule693, rule694, rule695, rule696, rule697, rule698, rule699, rule700, rule701, rule702, rule703, rule704, rule705, rule706, rule707, rule708, rule709, rule710, rule711, rule712, rule713, rule714, rule715, rule716, rule717, rule718, rule719, rule720, rule721, rule722, rule723, rule724, rule725, rule726, rule727, rule728, rule729, rule730, rule731, rule732, rule733, rule734, rule735, rule736, rule737, rule738, rule739, rule740, rule741, rule742, rule743, rule744, rule745, rule746, rule747, rule748, rule749, rule750, rule751, rule752, rule753, rule754, rule755, rule756, rule757, rule758, rule759, rule760, rule761, rule762, rule763, rule764, rule765, rule766, rule767, rule768, rule769, rule770, rule771, rule772, rule773, rule774, rule775, rule776, rule777, rule778, rule779, rule780, rule781, rule782, rule783, rule784, rule785, rule786, rule787, rule788, rule789, rule790, rule791, rule792, rule793, rule794, rule795, rule796, rule797, rule798, rule799, rule800, rule801, rule802, rule803, rule804, rule805, rule806, rule807, rule808, rule809, rule810, rule811, rule812, rule813, rule814, rule815, rule816, rule817, rule818, rule819, rule820, rule821, rule822, rule823, rule824, rule825, rule826, rule827, rule828, rule829, rule830, rule831, rule832, rule833, rule834, rule835, rule836, rule837, rule838, rule839, rule840, rule841, rule842, rule843, rule844, rule845, rule846, rule847, rule848, rule849, rule850, rule851, rule852, rule853, rule854, rule855, rule856, rule857, rule858, rule859, rule860, rule861, rule862, rule863, rule864, rule865, rule866, rule867, rule868, rule869, rule870, rule871, rule872, rule873, rule874, rule875, rule876, rule877, rule878, rule879, rule880, rule881, rule882, rule883, rule884, rule885, rule886, rule887, rule888, rule889, rule890, rule891, rule892, rule893, rule894, rule895, rule896, rule897, rule898, rule899, rule900, rule901, rule902, rule903, rule904, rule905, rule906, rule907, rule908, rule909, rule910, rule911, rule912, rule913, rule914, rule915, rule916, rule917, rule918, rule919, rule920, rule921, rule922, rule923, rule924, rule925, rule926, rule927, rule928, rule929, rule930, rule931, rule932, rule933, rule934, rule935, rule936, rule937, rule938, rule939, rule940, rule941, rule942, rule943, rule944, rule945, rule946, rule947, rule948, rule949, rule950, rule951, rule952, rule953, rule954, rule955, rule956, rule957, rule958, rule959, rule960, rule961, rule962, rule963, rule964, rule965, rule966, rule967, rule968, rule969, rule970, rule971, rule972, rule973, rule974, rule975, rule976, rule977, rule978, rule979, rule980, rule981, rule982, rule983, rule984, rule985, rule986, rule987, rule988, rule989, rule990, rule991, rule992, rule993, rule994, rule995, rule996, rule997, rule998, rule999, rule1000, rule1001, rule1002, rule1003, rule1004, rule1005, rule1006, rule1007, rule1008, rule1009, rule1010, rule1011, rule1012, rule1013, rule1014, rule1015, rule1016, rule1017, rule1018, rule1019, rule1020, rule1021, rule1022, rule1023, rule1024, rule1025, rule1026, rule1027, rule1028, rule1029, rule1030, rule1031, rule1032, rule1033, rule1034, rule1035, rule1036, rule1037, rule1038, rule1039, rule1040, rule1041, rule1042, rule1043, rule1044, rule1045, rule1046, rule1047, rule1048, rule1049, rule1050, rule1051, rule1052, rule1053, rule1054, rule1055, rule1056, rule1057, rule1058, rule1059, rule1060, rule1061, rule1062, rule1063, rule1064, rule1065, rule1066, rule1067, rule1068, rule1069, rule1070, rule1071, rule1072, rule1073, rule1074, rule1075, ]
