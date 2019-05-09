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

def quadratic_products(rubi):
    from sympy.integrals.rubi.constraints import cons45, cons2, cons3, cons7, cons225, cons5, cons226, cons128, cons227, cons228, cons13, cons163, cons229, cons137, cons230, cons231, cons232, cons233, cons234, cons235, cons68, cons69, cons47, cons236, cons27, cons48, cons21, cons237, cons238, cons239, cons240, cons66, cons241, cons242, cons243, cons244, cons146, cons245, cons246, cons247, cons248, cons249, cons250, cons251, cons252, cons166, cons253, cons31, cons168, cons254, cons255, cons94, cons147, cons256, cons38, cons257, cons258, cons41, cons17, cons259, cons260, cons261, cons262, cons263, cons264, cons265, cons266, cons267, cons43, cons268, cons54, cons269, cons270, cons271, cons272, cons273, cons274, cons275, cons276, cons277, cons278, cons279, cons280, cons281, cons282, cons283, cons284, cons285, cons286, cons18, cons287, cons288, cons289, cons290, cons291, cons292, cons293, cons294, cons295, cons296, cons297, cons298, cons299, cons300, cons301, cons302, cons303, cons304, cons305, cons306, cons307, cons308, cons309, cons310, cons311, cons312, cons313, cons84, cons85, cons314, cons315, cons316, cons125, cons208, cons317, cons318, cons319, cons62, cons320, cons321, cons322, cons323, cons324, cons4, cons325, cons326, cons327, cons139, cons328, cons329, cons330, cons331, cons150, cons332, cons148, cons333, cons196, cons334, cons335, cons336, cons337, cons338, cons89, cons339, cons340, cons341, cons88, cons87, cons342, cons343, cons344, cons126, cons345, cons346, cons207, cons347, cons348, cons349, cons350, cons351, cons352, cons353, cons354, cons355, cons356, cons357, cons358, cons359, cons360, cons361, cons362, cons363, cons364, cons365, cons366, cons367, cons368, cons369, cons370, cons371, cons372, cons373, cons374, cons375, cons149, cons376, cons124, cons377, cons93, cons23, cons165, cons73, cons378, cons80, cons379, cons380, cons381, cons382, cons383, cons384, cons385, cons50, cons386, cons387, cons388, cons389, cons390, cons391, cons392, cons393, cons394, cons395, cons396, cons397, cons398, cons399, cons400, cons401, cons402, cons403, cons404, cons405, cons406, cons407, cons408, cons409, cons410, cons411, cons412, cons413, cons414, cons415, cons416, cons209, cons417, cons418, cons419, cons420, cons421, cons422, cons423, cons424, cons425, cons426, cons427, cons428, cons429, cons430, cons431, cons220, cons432, cons433, cons434, cons435, cons436, cons437, cons438, cons439, cons440, cons441, cons442, cons443, cons444, cons445, cons446, cons447, cons448, cons449, cons450, cons451, cons452, cons453, cons224, cons34, cons35, cons36, cons454, cons455, cons456, cons457, cons458

    pattern189 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons45)
    def replacement189(x, c, b, a):
        rubi.append(189)
        return Dist((b/S(2) + c*x)/sqrt(a + b*x + c*x**S(2)), Int(S(1)/(b/S(2) + c*x), x), x)
    rule189 = ReplacementRule(pattern189, replacement189)
    pattern190 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons5, cons45, cons225)
    def replacement190(p, b, c, a, x):
        rubi.append(190)
        return Simp((b + S(2)*c*x)*(a + b*x + c*x**S(2))**p/(S(2)*c*(S(2)*p + S(1))), x)
    rule190 = ReplacementRule(pattern190, replacement190)
    def With191(p, b, c, a, x):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(191)
        return Dist(c**(-p), Int(Simp(b/S(2) + c*x - q/S(2), x)**p*Simp(b/S(2) + c*x + q/S(2), x)**p, x), x)
    pattern191 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons226, cons128, cons227)
    rule191 = ReplacementRule(pattern191, With191)
    pattern192 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons226, cons128, cons228)
    def replacement192(p, b, c, a, x):
        rubi.append(192)
        return Int(ExpandIntegrand((a + b*x + c*x**S(2))**p, x), x)
    rule192 = ReplacementRule(pattern192, replacement192)
    pattern193 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons226, cons13, cons163, cons229)
    def replacement193(p, b, c, a, x):
        rubi.append(193)
        return -Dist(p*(-S(4)*a*c + b**S(2))/(S(2)*c*(S(2)*p + S(1))), Int((a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((b + S(2)*c*x)*(a + b*x + c*x**S(2))**p/(S(2)*c*(S(2)*p + S(1))), x)
    rule193 = ReplacementRule(pattern193, replacement193)
    pattern194 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**(S(-3)/2), x_), cons2, cons3, cons7, cons226)
    def replacement194(x, c, a, b):
        rubi.append(194)
        return Simp(-S(2)*(b + S(2)*c*x)/((-S(4)*a*c + b**S(2))*sqrt(a + b*x + c*x**S(2))), x)
    rule194 = ReplacementRule(pattern194, replacement194)
    pattern195 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons226, cons13, cons137, cons230, cons229)
    def replacement195(p, b, c, a, x):
        rubi.append(195)
        return -Dist(S(2)*c*(S(2)*p + S(3))/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((b + S(2)*c*x)*(a + b*x + c*x**S(2))**(p + S(1))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule195 = ReplacementRule(pattern195, replacement195)
    def With196(x, c, b, a):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(196)
        return Dist(c/q, Int(S(1)/Simp(b/S(2) + c*x - q/S(2), x), x), x) - Dist(c/q, Int(S(1)/Simp(b/S(2) + c*x + q/S(2), x), x), x)
    pattern196 = Pattern(Integral(S(1)/(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons226, cons231, cons227)
    rule196 = ReplacementRule(pattern196, With196)
    def With197(x, c, b, a):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = -S(4)*a*c/b**S(2) + S(1)
        if And(RationalQ(q), Or(EqQ(q**S(2), S(1)), Not(RationalQ(-S(4)*a*c + b**S(2))))):
            return True
        return False
    pattern197 = Pattern(Integral(S(1)/(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons226, CustomConstraint(With197))
    def replacement197(x, c, b, a):

        q = -S(4)*a*c/b**S(2) + S(1)
        rubi.append(197)
        return Dist(-S(2)/b, Subst(Int(S(1)/(q - x**S(2)), x), x, S(1) + S(2)*c*x/b), x)
    rule197 = ReplacementRule(pattern197, replacement197)
    pattern198 = Pattern(Integral(S(1)/(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons226)
    def replacement198(x, c, b, a):
        rubi.append(198)
        return Dist(S(-2), Subst(Int(S(1)/Simp(-S(4)*a*c + b**S(2) - x**S(2), x), x), x, b + S(2)*c*x), x)
    rule198 = ReplacementRule(pattern198, replacement198)
    pattern199 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons5, cons232)
    def replacement199(p, b, c, a, x):
        rubi.append(199)
        return Dist((-S(4)*c/(-S(4)*a*c + b**S(2)))**(-p)/(S(2)*c), Subst(Int(Simp(-x**S(2)/(-S(4)*a*c + b**S(2)) + S(1), x)**p, x), x, b + S(2)*c*x), x)
    rule199 = ReplacementRule(pattern199, replacement199)
    pattern200 = Pattern(Integral(S(1)/sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons3, cons7, cons233)
    def replacement200(x, c, b):
        rubi.append(200)
        return Dist(S(2), Subst(Int(S(1)/(-c*x**S(2) + S(1)), x), x, x/sqrt(b*x + c*x**S(2))), x)
    rule200 = ReplacementRule(pattern200, replacement200)
    pattern201 = Pattern(Integral(S(1)/sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons226)
    def replacement201(x, c, b, a):
        rubi.append(201)
        return Dist(S(2), Subst(Int(S(1)/(S(4)*c - x**S(2)), x), x, (b + S(2)*c*x)/sqrt(a + b*x + c*x**S(2))), x)
    rule201 = ReplacementRule(pattern201, replacement201)
    pattern202 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons3, cons7, cons13, cons234)
    def replacement202(x, c, p, b):
        rubi.append(202)
        return Dist((-c*(b*x + c*x**S(2))/b**S(2))**(-p)*(b*x + c*x**S(2))**p, Int((-c*x/b - c**S(2)*x**S(2)/b**S(2))**p, x), x)
    rule202 = ReplacementRule(pattern202, replacement202)
    def With203(p, b, c, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        d = Denominator(p)
        if LessEqual(S(3), d, S(4)):
            return True
        return False
    pattern203 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons226, cons13, CustomConstraint(With203))
    def replacement203(p, b, c, a, x):

        d = Denominator(p)
        rubi.append(203)
        return Dist(d*sqrt((b + S(2)*c*x)**S(2))/(b + S(2)*c*x), Subst(Int(x**(d*(p + S(1)) + S(-1))/sqrt(-S(4)*a*c + b**S(2) + S(4)*c*x**d), x), x, (a + b*x + c*x**S(2))**(S(1)/d)), x)
    rule203 = ReplacementRule(pattern203, replacement203)
    def With204(p, b, c, a, x):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(204)
        return -Simp(((-b - S(2)*c*x + q)/(S(2)*q))**(-p + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*Hypergeometric2F1(-p, p + S(1), p + S(2), (b + S(2)*c*x + q)/(S(2)*q))/(q*(p + S(1))), x)
    pattern204 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons5, cons226, cons235)
    rule204 = ReplacementRule(pattern204, With204)
    pattern205 = Pattern(Integral((u_**S(2)*WC('c', S(1)) + u_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons5, cons68, cons69)
    def replacement205(p, u, b, c, a, x):
        rubi.append(205)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b*x + c*x**S(2))**p, x), x, u), x)
    rule205 = ReplacementRule(pattern205, replacement205)
    pattern206 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons45, cons47, cons236)
    def replacement206(p, m, b, d, c, a, x, e):
        rubi.append(206)
        return Simp(c**(-m/S(2) + S(-1)/2)*e**m*(a + b*x + c*x**S(2))**(m/S(2) + p + S(1)/2)/(m + S(2)*p + S(1)), x)
    rule206 = ReplacementRule(pattern206, replacement206)
    pattern207 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons45, cons47, cons237)
    def replacement207(p, m, b, d, c, a, x, e):
        rubi.append(207)
        return Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*log(RemoveContent(d + e*x, x))/e, x)
    rule207 = ReplacementRule(pattern207, replacement207)
    pattern208 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons45, cons47, cons238)
    def replacement208(p, m, b, d, c, a, x, e):
        rubi.append(208)
        return Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + S(2)*p + S(1))), x)
    rule208 = ReplacementRule(pattern208, replacement208)
    pattern209 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons45, cons239, cons240, cons66)
    def replacement209(p, m, b, d, c, a, x, e):
        rubi.append(209)
        return -Simp((b + S(2)*c*x)*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/((m + S(1))*(-b*e + S(2)*c*d)), x)
    rule209 = ReplacementRule(pattern209, replacement209)
    pattern210 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))/(x_*WC('e', S(1)) + WC('d', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons45, cons239)
    def replacement210(b, d, c, a, x, e):
        rubi.append(210)
        return Dist(sqrt(a + b*x + c*x**S(2))/(b + S(2)*c*x), Int((b + S(2)*c*x)/(d + e*x)**S(2), x), x)
    rule210 = ReplacementRule(pattern210, replacement210)
    pattern211 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons45, cons239, cons241)
    def replacement211(m, b, d, c, a, x, e):
        rubi.append(211)
        return -Dist((-b*e + S(2)*c*d)*sqrt(a + b*x + c*x**S(2))/(e*(b + S(2)*c*x)*(m + S(2))), Int((d + e*x)**m, x), x) + Simp((d + e*x)**(m + S(1))*sqrt(a + b*x + c*x**S(2))/(e*(m + S(2))), x)
    rule211 = ReplacementRule(pattern211, replacement211)
    pattern212 = Pattern(Integral(S(1)/((x_*WC('e', S(1)) + WC('d', S(0)))**S(2)*sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons45, cons239)
    def replacement212(b, d, c, a, x, e):
        rubi.append(212)
        return Dist(S(2)*c/(-b*e + S(2)*c*d), Int(S(1)/((d + e*x)*sqrt(a + b*x + c*x**S(2))), x), x) + Simp(-S(4)*c*e*sqrt(a + b*x + c*x**S(2))/((d + e*x)*(-b*e + S(2)*c*d)**S(2)), x)
    rule212 = ReplacementRule(pattern212, replacement212)
    pattern213 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons45, cons239, cons242, cons241)
    def replacement213(p, m, b, d, c, a, x, e):
        rubi.append(213)
        return -Simp((b + S(2)*c*x)*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/((m + S(2))*(-b*e + S(2)*c*d)), x) + Simp(-S(2)*c*e*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/((-b*e + S(2)*c*d)**S(2)*(m*p + S(-1))), x)
    rule213 = ReplacementRule(pattern213, replacement213)
    pattern214 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons45, cons239, cons243)
    def replacement214(p, b, d, c, a, x, e):
        rubi.append(214)
        return Dist((-b*e + S(2)*c*d)/(S(2)*c), Int((a + b*x + c*x**S(2))**p, x), x) + Simp(e*(a + b*x + c*x**S(2))**(p + S(1))/(S(2)*c*(p + S(1))), x)
    rule214 = ReplacementRule(pattern214, replacement214)
    pattern215 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons45, cons239, cons244, cons146, cons245, cons246)
    def replacement215(p, m, b, d, c, a, x, e):
        rubi.append(215)
        return Dist(p*(S(2)*p + S(-1))*(-b*e + S(2)*c*d)/(e**S(2)*(m + S(1))*(m + S(2)*p + S(1))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + S(1))), x) - Simp(p*(b + S(2)*c*x)*(d + e*x)**(m + S(2))*(a + b*x + c*x**S(2))**(p + S(-1))/(e**S(2)*(m + S(1))*(m + S(2)*p + S(1))), x)
    rule215 = ReplacementRule(pattern215, replacement215)
    pattern216 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons45, cons239, cons244, cons146, cons247, cons246, cons248)
    def replacement216(p, m, b, d, c, a, x, e):
        rubi.append(216)
        return Dist(S(2)*c*p*(S(2)*p + S(-1))/(e**S(2)*(m + S(1))*(m + S(2))), Int((d + e*x)**(m + S(2))*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + S(1))), x) - Simp(p*(b + S(2)*c*x)*(d + e*x)**(m + S(2))*(a + b*x + c*x**S(2))**(p + S(-1))/(e**S(2)*(m + S(1))*(m + S(2))), x)
    rule216 = ReplacementRule(pattern216, replacement216)
    pattern217 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons45, cons239, cons13, cons163, cons249, cons238, cons248, cons250, cons251, cons246)
    def replacement217(p, m, b, d, c, a, x, e):
        rubi.append(217)
        return Dist(p*(S(2)*p + S(-1))*(-b*e + S(2)*c*d)**S(2)/(S(2)*c*e**S(2)*(m + S(2)*p)*(m + S(2)*p + S(1))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + S(2)*p + S(1))), x) - Simp(p*(b + S(2)*c*x)*(d + e*x)**(m + S(1))*(-b*e + S(2)*c*d)*(a + b*x + c*x**S(2))**(p + S(-1))/(S(2)*c*e**S(2)*(m + S(2)*p)*(m + S(2)*p + S(1))), x)
    rule217 = ReplacementRule(pattern217, replacement217)
    pattern218 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons45, cons239, cons244, cons137, cons252, cons246)
    def replacement218(p, m, b, d, c, a, x, e):
        rubi.append(218)
        return Dist(e**S(2)*m*(m + S(2)*p + S(2))/((p + S(1))*(S(2)*p + S(1))*(-b*e + S(2)*c*d)), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((b + S(2)*c*x)*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/((S(2)*p + S(1))*(-b*e + S(2)*c*d)), x) - Simp(e*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))*(m + S(2)*p + S(2))/((p + S(1))*(S(2)*p + S(1))*(-b*e + S(2)*c*d)), x)
    rule218 = ReplacementRule(pattern218, replacement218)
    pattern219 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons45, cons239, cons244, cons137, cons166, cons246)
    def replacement219(p, m, b, d, c, a, x, e):
        rubi.append(219)
        return Dist(e**S(2)*m*(m + S(-1))/(S(2)*c*(p + S(1))*(S(2)*p + S(1))), Int((d + e*x)**(m + S(-2))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((b + S(2)*c*x)*(d + e*x)**m*(a + b*x + c*x**S(2))**p/(S(2)*c*(S(2)*p + S(1))), x) - Simp(e*m*(d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))/(S(2)*c*(p + S(1))*(S(2)*p + S(1))), x)
    rule219 = ReplacementRule(pattern219, replacement219)
    pattern220 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons45, cons239, cons244, cons137, cons253, cons246)
    def replacement220(p, m, b, d, c, a, x, e):
        rubi.append(220)
        return Dist(S(2)*c*e**S(2)*(m + S(2)*p + S(2))*(m + S(2)*p + S(3))/((p + S(1))*(S(2)*p + S(1))*(-b*e + S(2)*c*d)**S(2)), Int((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((b + S(2)*c*x)*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/((S(2)*p + S(1))*(-b*e + S(2)*c*d)), x) + Simp(-S(2)*c*e*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(m + S(2)*p + S(2))/((p + S(1))*(S(2)*p + S(1))*(-b*e + S(2)*c*d)**S(2)), x)
    rule220 = ReplacementRule(pattern220, replacement220)
    pattern221 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons45, cons239, cons31, cons168, cons238, cons254, cons255)
    def replacement221(p, m, b, d, c, a, x, e):
        rubi.append(221)
        return Dist(m*(-b*e + S(2)*c*d)/(S(2)*c*(m + S(2)*p + S(1))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**p, x), x) + Simp((b + S(2)*c*x)*(d + e*x)**m*(a + b*x + c*x**S(2))**p/(S(2)*c*(m + S(2)*p + S(1))), x)
    rule221 = ReplacementRule(pattern221, replacement221)
    pattern222 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons45, cons239, cons31, cons94, cons246)
    def replacement222(p, m, b, d, c, a, x, e):
        rubi.append(222)
        return Dist(S(2)*c*(m + S(2)*p + S(2))/((m + S(1))*(-b*e + S(2)*c*d)), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) - Simp((b + S(2)*c*x)*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/((m + S(1))*(-b*e + S(2)*c*d)), x)
    rule222 = ReplacementRule(pattern222, replacement222)
    pattern223 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons45, cons147, cons239)
    def replacement223(p, m, b, d, c, a, x, e):
        rubi.append(223)
        return Dist(c**(-IntPart(p))*(b/S(2) + c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((b/S(2) + c*x)**(S(2)*p)*(d + e*x)**m, x), x)
    rule223 = ReplacementRule(pattern223, replacement223)
    pattern224 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons256, cons38)
    def replacement224(p, m, b, d, c, a, x, e):
        rubi.append(224)
        return Int((d + e*x)**(m + p)*(a/d + c*x/e)**p, x)
    rule224 = ReplacementRule(pattern224, replacement224)
    pattern225 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons5, cons257, cons258)
    def replacement225(p, m, d, c, a, x, e):
        rubi.append(225)
        return Int((d + e*x)**(m + p)*(a/d + c*x/e)**p, x)
    rule225 = ReplacementRule(pattern225, replacement225)
    pattern226 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons256, cons147, cons41)
    def replacement226(p, m, b, d, c, a, x, e):
        rubi.append(226)
        return Simp(e*(d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*(p + S(1))), x)
    rule226 = ReplacementRule(pattern226, replacement226)
    pattern227 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons5, cons257, cons147, cons41)
    def replacement227(p, m, d, c, a, x, e):
        rubi.append(227)
        return Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))/(c*(p + S(1))), x)
    rule227 = ReplacementRule(pattern227, replacement227)
    pattern228 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons256, cons147, cons240)
    def replacement228(p, m, b, d, a, c, x, e):
        rubi.append(228)
        return Simp(e*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/((p + S(1))*(-b*e + S(2)*c*d)), x)
    rule228 = ReplacementRule(pattern228, replacement228)
    pattern229 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons5, cons257, cons147, cons240)
    def replacement229(p, m, d, c, a, x, e):
        rubi.append(229)
        return Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m/(S(2)*c*d*(p + S(1))), x)
    rule229 = ReplacementRule(pattern229, replacement229)
    pattern230 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**S(2)*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons226, cons256, cons147, cons13, cons137)
    def replacement230(p, b, d, c, a, x, e):
        rubi.append(230)
        return -Dist(e**S(2)*(p + S(2))/(c*(p + S(1))), Int((a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp(e*(d + e*x)*(a + b*x + c*x**S(2))**(p + S(1))/(c*(p + S(1))), x)
    rule230 = ReplacementRule(pattern230, replacement230)
    pattern231 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**S(2), x_), cons2, cons7, cons27, cons48, cons5, cons257, cons147, cons13, cons137)
    def replacement231(p, d, c, a, x, e):
        rubi.append(231)
        return -Dist(e**S(2)*(p + S(2))/(c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1)), x), x) + Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)/(c*(p + S(1))), x)
    rule231 = ReplacementRule(pattern231, replacement231)
    pattern232 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons256, cons147, cons17, cons13, cons259, cons260, cons261)
    def replacement232(p, m, b, d, c, a, x, e):
        rubi.append(232)
        return Int((a/d + c*x/e)**(-m)*(a + b*x + c*x**S(2))**(m + p), x)
    rule232 = ReplacementRule(pattern232, replacement232)
    pattern233 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons5, cons257, cons147, cons17, cons13, cons259, cons260, cons261)
    def replacement233(p, m, d, c, a, x, e):
        rubi.append(233)
        return Dist(a**(-m)*d**(S(2)*m), Int((a + c*x**S(2))**(m + p)*(d - e*x)**(-m), x), x)
    rule233 = ReplacementRule(pattern233, replacement233)
    pattern234 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons256, cons147, cons262)
    def replacement234(p, m, b, d, a, c, x, e):
        rubi.append(234)
        return Dist((m + p)*(-b*e + S(2)*c*d)/(c*(m + S(2)*p + S(1))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**p, x), x) + Simp(e*(d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m + S(2)*p + S(1))), x)
    rule234 = ReplacementRule(pattern234, replacement234)
    pattern235 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons5, cons257, cons147, cons262)
    def replacement235(p, m, d, c, a, x, e):
        rubi.append(235)
        return Dist(S(2)*d*(m + p)/(m + S(2)*p + S(1)), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(-1)), x), x) + Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))/(c*(m + S(2)*p + S(1))), x)
    rule235 = ReplacementRule(pattern235, replacement235)
    pattern236 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons256, cons147, cons263)
    def replacement236(p, m, b, d, c, a, x, e):
        rubi.append(236)
        return Dist(c*(m + S(2)*p + S(2))/((-b*e + S(2)*c*d)*(m + p + S(1))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) - Simp(e*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/((-b*e + S(2)*c*d)*(m + p + S(1))), x)
    rule236 = ReplacementRule(pattern236, replacement236)
    pattern237 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons5, cons257, cons147, cons263)
    def replacement237(p, m, d, c, a, x, e):
        rubi.append(237)
        return Dist((m + S(2)*p + S(2))/(S(2)*d*(m + p + S(1))), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1)), x), x) - Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m/(S(2)*c*d*(m + p + S(1))), x)
    rule237 = ReplacementRule(pattern237, replacement237)
    pattern238 = Pattern(Integral(S(1)/(sqrt(x_*WC('e', S(1)) + WC('d', S(0)))*sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons256)
    def replacement238(b, d, c, a, x, e):
        rubi.append(238)
        return Dist(S(2)*e, Subst(Int(S(1)/(-b*e + S(2)*c*d + e**S(2)*x**S(2)), x), x, sqrt(a + b*x + c*x**S(2))/sqrt(d + e*x)), x)
    rule238 = ReplacementRule(pattern238, replacement238)
    pattern239 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('c', S(1)))*sqrt(d_ + x_*WC('e', S(1)))), x_), cons2, cons7, cons27, cons48, cons257)
    def replacement239(d, c, a, x, e):
        rubi.append(239)
        return Dist(S(2)*e, Subst(Int(S(1)/(S(2)*c*d + e**S(2)*x**S(2)), x), x, sqrt(a + c*x**S(2))/sqrt(d + e*x)), x)
    rule239 = ReplacementRule(pattern239, replacement239)
    pattern240 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons256, cons244, cons163, cons264, cons253, cons246)
    def replacement240(p, m, b, d, c, a, x, e):
        rubi.append(240)
        return -Dist(c*p/(e**S(2)*(m + p + S(1))), Int((d + e*x)**(m + S(2))*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + p + S(1))), x)
    rule240 = ReplacementRule(pattern240, replacement240)
    pattern241 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons257, cons244, cons163, cons264, cons253, cons246)
    def replacement241(p, m, d, c, a, x, e):
        rubi.append(241)
        return -Dist(c*p/(e**S(2)*(m + p + S(1))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x)**(m + S(2)), x), x) + Simp((a + c*x**S(2))**p*(d + e*x)**(m + S(1))/(e*(m + p + S(1))), x)
    rule241 = ReplacementRule(pattern241, replacement241)
    pattern242 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons256, cons244, cons163, cons265, cons238, cons246)
    def replacement242(p, m, b, d, c, a, x, e):
        rubi.append(242)
        return -Dist(p*(-b*e + S(2)*c*d)/(e**S(2)*(m + S(2)*p + S(1))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + S(2)*p + S(1))), x)
    rule242 = ReplacementRule(pattern242, replacement242)
    pattern243 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons257, cons244, cons163, cons265, cons238, cons246)
    def replacement243(p, m, d, c, a, x, e):
        rubi.append(243)
        return -Dist(S(2)*c*d*p/(e**S(2)*(m + S(2)*p + S(1))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x)**(m + S(1)), x), x) + Simp((a + c*x**S(2))**p*(d + e*x)**(m + S(1))/(e*(m + S(2)*p + S(1))), x)
    rule243 = ReplacementRule(pattern243, replacement243)
    pattern244 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons256, cons244, cons137, cons252, cons246)
    def replacement244(p, m, b, d, a, c, x, e):
        rubi.append(244)
        return -Dist((-b*e + S(2)*c*d)*(m + S(2)*p + S(2))/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((d + e*x)**m*(-b*e + S(2)*c*d)*(a + b*x + c*x**S(2))**(p + S(1))/(e*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule244 = ReplacementRule(pattern244, replacement244)
    pattern245 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons257, cons244, cons137, cons252, cons246)
    def replacement245(p, m, d, c, a, x, e):
        rubi.append(245)
        return Dist(d*(m + S(2)*p + S(2))/(S(2)*a*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1)), x), x) - Simp(d*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m/(S(2)*a*e*(p + S(1))), x)
    rule245 = ReplacementRule(pattern245, replacement245)
    pattern246 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons256, cons244, cons137, cons166, cons246)
    def replacement246(p, m, b, d, c, a, x, e):
        rubi.append(246)
        return -Dist(e**S(2)*(m + p)/(c*(p + S(1))), Int((d + e*x)**(m + S(-2))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp(e*(d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*(p + S(1))), x)
    rule246 = ReplacementRule(pattern246, replacement246)
    pattern247 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons257, cons244, cons137, cons166, cons246)
    def replacement247(p, m, d, c, a, x, e):
        rubi.append(247)
        return -Dist(e**S(2)*(m + p)/(c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-2)), x), x) + Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))/(c*(p + S(1))), x)
    rule247 = ReplacementRule(pattern247, replacement247)
    pattern248 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons226, cons256, cons31, cons266, cons238, cons246)
    def replacement248(p, m, b, d, a, c, x, e):
        rubi.append(248)
        return Dist((m + p)*(-b*e + S(2)*c*d)/(c*(m + S(2)*p + S(1))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**p, x), x) + Simp(e*(d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m + S(2)*p + S(1))), x)
    rule248 = ReplacementRule(pattern248, replacement248)
    pattern249 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons5, cons257, cons31, cons266, cons238, cons246)
    def replacement249(p, m, d, c, a, x, e):
        rubi.append(249)
        return Dist(S(2)*d*(m + p)/(m + S(2)*p + S(1)), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(-1)), x), x) + Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))/(c*(m + S(2)*p + S(1))), x)
    rule249 = ReplacementRule(pattern249, replacement249)
    pattern250 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons226, cons256, cons31, cons267, cons253, cons246)
    def replacement250(p, m, b, d, c, a, x, e):
        rubi.append(250)
        return Dist(c*(m + S(2)*p + S(2))/((-b*e + S(2)*c*d)*(m + p + S(1))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) - Simp(e*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/((-b*e + S(2)*c*d)*(m + p + S(1))), x)
    rule250 = ReplacementRule(pattern250, replacement250)
    pattern251 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons5, cons257, cons31, cons267, cons253, cons246)
    def replacement251(p, m, d, c, a, x, e):
        rubi.append(251)
        return Dist((m + S(2)*p + S(2))/(S(2)*d*(m + p + S(1))), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1)), x), x) - Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m/(S(2)*c*d*(m + p + S(1))), x)
    rule251 = ReplacementRule(pattern251, replacement251)
    pattern252 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons3, cons7, cons48, cons21, cons147)
    def replacement252(p, m, b, c, x, e):
        rubi.append(252)
        return Dist(x**(-m - p)*(e*x)**m*(b + c*x)**(-p)*(b*x + c*x**S(2))**p, Int(x**(m + p)*(b + c*x)**p, x), x)
    rule252 = ReplacementRule(pattern252, replacement252)
    pattern253 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons5, cons257, cons147, cons43, cons268)
    def replacement253(p, m, d, c, a, x, e):
        rubi.append(253)
        return Int((d + e*x)**(m + p)*(a/d + c*x/e)**p, x)
    rule253 = ReplacementRule(pattern253, replacement253)
    pattern254 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons256, cons147)
    def replacement254(p, m, b, d, c, a, x, e):
        rubi.append(254)
        return Dist((d + e*x)**(-FracPart(p))*(a/d + c*x/e)**(-FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((d + e*x)**(m + p)*(a/d + c*x/e)**p, x), x)
    rule254 = ReplacementRule(pattern254, replacement254)
    pattern255 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons257, cons147)
    def replacement255(p, m, d, c, a, x, e):
        rubi.append(255)
        return Dist((a + c*x**S(2))**FracPart(p)*(d + e*x)**(-FracPart(p))*(a/d + c*x/e)**(-FracPart(p)), Int((d + e*x)**(m + p)*(a/d + c*x/e)**p, x), x)
    rule255 = ReplacementRule(pattern255, replacement255)
    pattern256 = Pattern(Integral(S(1)/((d_ + x_*WC('e', S(1)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons47)
    def replacement256(b, d, c, a, x, e):
        rubi.append(256)
        return Dist(b**S(2)/(d**S(2)*(-S(4)*a*c + b**S(2))), Int((d + e*x)/(a + b*x + c*x**S(2)), x), x) + Dist(-S(4)*b*c/(d*(-S(4)*a*c + b**S(2))), Int(S(1)/(b + S(2)*c*x), x), x)
    rule256 = ReplacementRule(pattern256, replacement256)
    pattern257 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons47, cons242, cons54)
    def replacement257(p, m, b, d, c, a, x, e):
        rubi.append(257)
        return Simp(S(2)*c*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(e*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule257 = ReplacementRule(pattern257, replacement257)
    pattern258 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons47, cons128, cons269)
    def replacement258(p, m, b, d, c, a, x, e):
        rubi.append(258)
        return Int(ExpandIntegrand((d + e*x)**m*(a + b*x + c*x**S(2))**p, x), x)
    rule258 = ReplacementRule(pattern258, replacement258)
    pattern259 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons47, cons270, cons244, cons163, cons94, cons271, cons246)
    def replacement259(p, m, b, d, c, a, x, e):
        rubi.append(259)
        return -Dist(b*p/(d*e*(m + S(1))), Int((d + e*x)**(m + S(2))*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + S(1))), x)
    rule259 = ReplacementRule(pattern259, replacement259)
    pattern260 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons47, cons270, cons13, cons163, cons272, cons273, cons31, cons246)
    def replacement260(p, m, b, d, c, a, x, e):
        rubi.append(260)
        return -Dist(d*p*(-S(4)*a*c + b**S(2))/(b*e*(m + S(2)*p + S(1))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + S(2)*p + S(1))), x)
    rule260 = ReplacementRule(pattern260, replacement260)
    pattern261 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons47, cons270, cons244, cons137, cons166, cons246)
    def replacement261(p, m, b, d, c, a, x, e):
        rubi.append(261)
        return -Dist(d*e*(m + S(-1))/(b*(p + S(1))), Int((d + e*x)**(m + S(-2))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp(d*(d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))/(b*(p + S(1))), x)
    rule261 = ReplacementRule(pattern261, replacement261)
    pattern262 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons47, cons270, cons13, cons137, cons274, cons31, cons246)
    def replacement262(p, m, b, d, c, a, x, e):
        rubi.append(262)
        return -Dist(S(2)*c*(m + S(2)*p + S(3))/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp(S(2)*c*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(e*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule262 = ReplacementRule(pattern262, replacement262)
    pattern263 = Pattern(Integral(S(1)/((d_ + x_*WC('e', S(1)))*sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons47)
    def replacement263(b, d, c, a, x, e):
        rubi.append(263)
        return Dist(S(4)*c, Subst(Int(S(1)/(-S(4)*a*c*e + b**S(2)*e + S(4)*c*e*x**S(2)), x), x, sqrt(a + b*x + c*x**S(2))), x)
    rule263 = ReplacementRule(pattern263, replacement263)
    pattern264 = Pattern(Integral(S(1)/(sqrt(d_ + x_*WC('e', S(1)))*sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons47, cons275)
    def replacement264(b, d, c, a, x, e):
        rubi.append(264)
        return Dist(S(4)*sqrt(-c/(-S(4)*a*c + b**S(2)))/e, Subst(Int(S(1)/sqrt(Simp(-b**S(2)*x**S(4)/(d**S(2)*(-S(4)*a*c + b**S(2))) + S(1), x)), x), x, sqrt(d + e*x)), x)
    rule264 = ReplacementRule(pattern264, replacement264)
    pattern265 = Pattern(Integral(sqrt(d_ + x_*WC('e', S(1)))/sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons47, cons275)
    def replacement265(b, d, c, a, x, e):
        rubi.append(265)
        return Dist(S(4)*sqrt(-c/(-S(4)*a*c + b**S(2)))/e, Subst(Int(x**S(2)/sqrt(Simp(-b**S(2)*x**S(4)/(d**S(2)*(-S(4)*a*c + b**S(2))) + S(1), x)), x), x, sqrt(d + e*x)), x)
    rule265 = ReplacementRule(pattern265, replacement265)
    pattern266 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_/sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons47, cons276)
    def replacement266(m, b, d, c, a, x, e):
        rubi.append(266)
        return Dist(sqrt(-c*(a + b*x + c*x**S(2))/(-S(4)*a*c + b**S(2)))/sqrt(a + b*x + c*x**S(2)), Int((d + e*x)**m/sqrt(-a*c/(-S(4)*a*c + b**S(2)) - b*c*x/(-S(4)*a*c + b**S(2)) - c**S(2)*x**S(2)/(-S(4)*a*c + b**S(2))), x), x)
    rule266 = ReplacementRule(pattern266, replacement266)
    pattern267 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons226, cons47, cons270, cons31, cons166, cons238, cons277)
    def replacement267(p, m, b, d, c, a, x, e):
        rubi.append(267)
        return Dist(d**S(2)*(m + S(-1))*(-S(4)*a*c + b**S(2))/(b**S(2)*(m + S(2)*p + S(1))), Int((d + e*x)**(m + S(-2))*(a + b*x + c*x**S(2))**p, x), x) + Simp(S(2)*d*(d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))/(b*(m + S(2)*p + S(1))), x)
    rule267 = ReplacementRule(pattern267, replacement267)
    pattern268 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons226, cons47, cons270, cons31, cons94, cons278)
    def replacement268(p, m, b, d, c, a, x, e):
        rubi.append(268)
        return Dist(b**S(2)*(m + S(2)*p + S(3))/(d**S(2)*(m + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**(m + S(2))*(a + b*x + c*x**S(2))**p, x), x) + Simp(-S(2)*b*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(d*(m + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule268 = ReplacementRule(pattern268, replacement268)
    pattern269 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons47)
    def replacement269(p, m, b, d, c, a, x, e):
        rubi.append(269)
        return Dist(S(1)/e, Subst(Int(x**m*(a - b**S(2)/(S(4)*c) + c*x**S(2)/e**S(2))**p, x), x, d + e*x), x)
    rule269 = ReplacementRule(pattern269, replacement269)
    pattern270 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons279, cons239, cons128)
    def replacement270(p, m, b, d, a, c, x, e):
        rubi.append(270)
        return Int(ExpandIntegrand((d + e*x)**m*(a + b*x + c*x**S(2))**p, x), x)
    rule270 = ReplacementRule(pattern270, replacement270)
    pattern271 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons280, cons128, cons281)
    def replacement271(p, m, d, c, a, x, e):
        rubi.append(271)
        return Int(ExpandIntegrand((a + c*x**S(2))**p*(d + e*x)**m, x), x)
    rule271 = ReplacementRule(pattern271, replacement271)
    def With272(b, d, c, a, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(272)
        return Dist((c*d - e*(b/S(2) - q/S(2)))/q, Int(S(1)/(b/S(2) + c*x - q/S(2)), x), x) - Dist((c*d - e*(b/S(2) + q/S(2)))/q, Int(S(1)/(b/S(2) + c*x + q/S(2)), x), x)
    pattern272 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))/(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons282)
    rule272 = ReplacementRule(pattern272, With272)
    def With273(d, c, a, x, e):
        q = Rt(-a*c, S(2))
        rubi.append(273)
        return Dist(-c*d/(S(2)*q) + e/S(2), Int(S(1)/(c*x + q), x), x) + Dist(c*d/(S(2)*q) + e/S(2), Int(S(1)/(c*x - q), x), x)
    pattern273 = Pattern(Integral((d_ + x_*WC('e', S(1)))/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons280, cons283)
    rule273 = ReplacementRule(pattern273, With273)
    pattern274 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))/(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons284)
    def replacement274(b, d, c, a, x, e):
        rubi.append(274)
        return Dist(e/(S(2)*c), Int((b + S(2)*c*x)/(a + b*x + c*x**S(2)), x), x) + Dist((-b*e + S(2)*c*d)/(S(2)*c), Int(S(1)/(a + b*x + c*x**S(2)), x), x)
    rule274 = ReplacementRule(pattern274, replacement274)
    pattern275 = Pattern(Integral((d_ + x_*WC('e', S(1)))/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons280, cons285)
    def replacement275(d, c, a, x, e):
        rubi.append(275)
        return Dist(d, Int(S(1)/(a + c*x**S(2)), x), x) + Dist(e, Int(x/(a + c*x**S(2)), x), x)
    rule275 = ReplacementRule(pattern275, replacement275)
    pattern276 = Pattern(Integral(sqrt(x_*WC('e', S(1)) + WC('d', S(0)))/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239)
    def replacement276(b, d, c, a, x, e):
        rubi.append(276)
        return Dist(S(2)*e, Subst(Int(x**S(2)/(a*e**S(2) - b*d*e + c*d**S(2) + c*x**S(4) - x**S(2)*(-b*e + S(2)*c*d)), x), x, sqrt(d + e*x)), x)
    rule276 = ReplacementRule(pattern276, replacement276)
    pattern277 = Pattern(Integral(sqrt(d_ + x_*WC('e', S(1)))/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons280)
    def replacement277(d, c, a, x, e):
        rubi.append(277)
        return Dist(S(2)*e, Subst(Int(x**S(2)/(a*e**S(2) + c*d**S(2) - S(2)*c*d*x**S(2) + c*x**S(4)), x), x, sqrt(d + e*x)), x)
    rule277 = ReplacementRule(pattern277, replacement277)
    pattern278 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons17, cons166, cons286)
    def replacement278(m, b, d, c, a, x, e):
        rubi.append(278)
        return Int(PolynomialDivide((d + e*x)**m, a + b*x + c*x**S(2), x), x)
    rule278 = ReplacementRule(pattern278, replacement278)
    pattern279 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons280, cons17, cons166, cons286)
    def replacement279(m, d, c, a, x, e):
        rubi.append(279)
        return Int(PolynomialDivide((d + e*x)**m, a + c*x**S(2), x), x)
    rule279 = ReplacementRule(pattern279, replacement279)
    pattern280 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons31, cons166)
    def replacement280(m, b, d, c, a, x, e):
        rubi.append(280)
        return Dist(S(1)/c, Int((d + e*x)**(m + S(-2))*Simp(-a*e**S(2) + c*d**S(2) + e*x*(-b*e + S(2)*c*d), x)/(a + b*x + c*x**S(2)), x), x) + Simp(e*(d + e*x)**(m + S(-1))/(c*(m + S(-1))), x)
    rule280 = ReplacementRule(pattern280, replacement280)
    pattern281 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons280, cons31, cons166)
    def replacement281(m, d, c, a, x, e):
        rubi.append(281)
        return Dist(S(1)/c, Int((d + e*x)**(m + S(-2))*Simp(-a*e**S(2) + c*d**S(2) + S(2)*c*d*e*x, x)/(a + c*x**S(2)), x), x) + Simp(e*(d + e*x)**(m + S(-1))/(c*(m + S(-1))), x)
    rule281 = ReplacementRule(pattern281, replacement281)
    pattern282 = Pattern(Integral(S(1)/((x_*WC('e', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239)
    def replacement282(b, d, c, a, x, e):
        rubi.append(282)
        return Dist(e**S(2)/(a*e**S(2) - b*d*e + c*d**S(2)), Int(S(1)/(d + e*x), x), x) + Dist(S(1)/(a*e**S(2) - b*d*e + c*d**S(2)), Int((-b*e + c*d - c*e*x)/(a + b*x + c*x**S(2)), x), x)
    rule282 = ReplacementRule(pattern282, replacement282)
    pattern283 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('c', S(1)))*(d_ + x_*WC('e', S(1)))), x_), cons2, cons7, cons27, cons48, cons280)
    def replacement283(d, c, a, x, e):
        rubi.append(283)
        return Dist(e**S(2)/(a*e**S(2) + c*d**S(2)), Int(S(1)/(d + e*x), x), x) + Dist(S(1)/(a*e**S(2) + c*d**S(2)), Int((c*d - c*e*x)/(a + c*x**S(2)), x), x)
    rule283 = ReplacementRule(pattern283, replacement283)
    pattern284 = Pattern(Integral(S(1)/(sqrt(x_*WC('e', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239)
    def replacement284(b, d, c, a, x, e):
        rubi.append(284)
        return Dist(S(2)*e, Subst(Int(S(1)/(a*e**S(2) - b*d*e + c*d**S(2) + c*x**S(4) - x**S(2)*(-b*e + S(2)*c*d)), x), x, sqrt(d + e*x)), x)
    rule284 = ReplacementRule(pattern284, replacement284)
    pattern285 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(d_ + x_*WC('e', S(1)))), x_), cons2, cons7, cons27, cons48, cons280)
    def replacement285(d, c, a, x, e):
        rubi.append(285)
        return Dist(S(2)*e, Subst(Int(S(1)/(a*e**S(2) + c*d**S(2) - S(2)*c*d*x**S(2) + c*x**S(4)), x), x, sqrt(d + e*x)), x)
    rule285 = ReplacementRule(pattern285, replacement285)
    pattern286 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons279, cons239, cons31, cons94)
    def replacement286(m, b, d, c, a, x, e):
        rubi.append(286)
        return Dist(S(1)/(a*e**S(2) - b*d*e + c*d**S(2)), Int((d + e*x)**(m + S(1))*Simp(-b*e + c*d - c*e*x, x)/(a + b*x + c*x**S(2)), x), x) + Simp(e*(d + e*x)**(m + S(1))/((m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule286 = ReplacementRule(pattern286, replacement286)
    pattern287 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons21, cons280, cons31, cons94)
    def replacement287(m, d, c, a, x, e):
        rubi.append(287)
        return Dist(c/(a*e**S(2) + c*d**S(2)), Int((d - e*x)*(d + e*x)**(m + S(1))/(a + c*x**S(2)), x), x) + Simp(e*(d + e*x)**(m + S(1))/((m + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule287 = ReplacementRule(pattern287, replacement287)
    pattern288 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons279, cons239, cons18)
    def replacement288(m, b, d, c, a, x, e):
        rubi.append(288)
        return Int(ExpandIntegrand((d + e*x)**m, S(1)/(a + b*x + c*x**S(2)), x), x)
    rule288 = ReplacementRule(pattern288, replacement288)
    pattern289 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons21, cons280, cons18)
    def replacement289(m, d, c, a, x, e):
        rubi.append(289)
        return Int(ExpandIntegrand((d + e*x)**m, S(1)/(a + c*x**S(2)), x), x)
    rule289 = ReplacementRule(pattern289, replacement289)
    pattern290 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239)
    def replacement290(b, d, c, a, x, e):
        rubi.append(290)
        return Simp(-S(2)*(-S(2)*a*e + b*d + x*(-b*e + S(2)*c*d))/((-S(4)*a*c + b**S(2))*sqrt(a + b*x + c*x**S(2))), x)
    rule290 = ReplacementRule(pattern290, replacement290)
    pattern291 = Pattern(Integral((d_ + x_*WC('e', S(1)))/(a_ + x_**S(2)*WC('c', S(1)))**(S(3)/2), x_), cons2, cons7, cons27, cons48, cons280)
    def replacement291(d, c, a, x, e):
        rubi.append(291)
        return Simp((-a*e + c*d*x)/(a*c*sqrt(a + c*x**S(2))), x)
    rule291 = ReplacementRule(pattern291, replacement291)
    pattern292 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons13, cons137, cons230)
    def replacement292(p, b, d, c, a, x, e):
        rubi.append(292)
        return -Dist((S(2)*p + S(3))*(-b*e + S(2)*c*d)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((a + b*x + c*x**S(2))**(p + S(1))*(-S(2)*a*e + b*d + x*(-b*e + S(2)*c*d))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule292 = ReplacementRule(pattern292, replacement292)
    pattern293 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1))), x_), cons2, cons7, cons27, cons48, cons280, cons13, cons137, cons230)
    def replacement293(p, d, c, a, x, e):
        rubi.append(293)
        return Dist(d*(S(2)*p + S(3))/(S(2)*a*(p + S(1))), Int((a + c*x**S(2))**(p + S(1)), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(a*e - c*d*x)/(S(2)*a*c*(p + S(1))), x)
    rule293 = ReplacementRule(pattern293, replacement293)
    pattern294 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons226, cons279, cons239, cons287)
    def replacement294(p, b, d, c, a, x, e):
        rubi.append(294)
        return Dist((-b*e + S(2)*c*d)/(S(2)*c), Int((a + b*x + c*x**S(2))**p, x), x) + Simp(e*(a + b*x + c*x**S(2))**(p + S(1))/(S(2)*c*(p + S(1))), x)
    rule294 = ReplacementRule(pattern294, replacement294)
    pattern295 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1))), x_), cons2, cons7, cons27, cons48, cons5, cons280, cons287)
    def replacement295(p, d, c, a, x, e):
        rubi.append(295)
        return Dist(d, Int((a + c*x**S(2))**p, x), x) + Simp(e*(a + c*x**S(2))**(p + S(1))/(S(2)*c*(p + S(1))), x)
    rule295 = ReplacementRule(pattern295, replacement295)
    pattern296 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons288, cons289, cons290, cons147)
    def replacement296(p, m, b, d, c, a, x, e):
        rubi.append(296)
        return Dist((d + e*x)**FracPart(p)*(a*d + c*e*x**S(3))**(-FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((d + e*x)**(m - p)*(a*d + c*e*x**S(3))**p, x), x)
    rule296 = ReplacementRule(pattern296, replacement296)
    pattern297 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_/sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons3, cons7, cons27, cons48, cons291, cons239, cons31, cons292, cons293, cons294)
    def replacement297(m, b, d, c, x, e):
        rubi.append(297)
        return Int((d + e*x)**m/(sqrt(b*x)*sqrt(S(1) + c*x/b)), x)
    rule297 = ReplacementRule(pattern297, replacement297)
    pattern298 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_/sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons3, cons7, cons27, cons48, cons291, cons239, cons31, cons292)
    def replacement298(m, b, d, c, x, e):
        rubi.append(298)
        return Dist(sqrt(x)*sqrt(b + c*x)/sqrt(b*x + c*x**S(2)), Int((d + e*x)**m/(sqrt(x)*sqrt(b + c*x)), x), x)
    rule298 = ReplacementRule(pattern298, replacement298)
    pattern299 = Pattern(Integral(x_**m_/sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons226, cons295)
    def replacement299(m, b, c, a, x):
        rubi.append(299)
        return Dist(S(2), Subst(Int(x**(S(2)*m + S(1))/sqrt(a + b*x**S(2) + c*x**S(4)), x), x, sqrt(x)), x)
    rule299 = ReplacementRule(pattern299, replacement299)
    pattern300 = Pattern(Integral((e_*x_)**m_/sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons48, cons226, cons295)
    def replacement300(m, b, c, a, x, e):
        rubi.append(300)
        return Dist(x**(-m)*(e*x)**m, Int(x**m/sqrt(a + b*x + c*x**S(2)), x), x)
    rule300 = ReplacementRule(pattern300, replacement300)
    pattern301 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_/sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons295)
    def replacement301(m, b, d, c, a, x, e):
        rubi.append(301)
        return Dist(S(2)*sqrt(-c*(a + b*x + c*x**S(2))/(-S(4)*a*c + b**S(2)))*(S(2)*c*(d + e*x)/(-b*e + S(2)*c*d - e*Rt(-S(4)*a*c + b**S(2), S(2))))**(-m)*(d + e*x)**m*Rt(-S(4)*a*c + b**S(2), S(2))/(c*sqrt(a + b*x + c*x**S(2))), Subst(Int((S(2)*e*x**S(2)*Rt(-S(4)*a*c + b**S(2), S(2))/(-b*e + S(2)*c*d - e*Rt(-S(4)*a*c + b**S(2), S(2))) + S(1))**m/sqrt(-x**S(2) + S(1)), x), x, sqrt(S(2))*sqrt((b + S(2)*c*x + Rt(-S(4)*a*c + b**S(2), S(2)))/Rt(-S(4)*a*c + b**S(2), S(2)))/S(2)), x)
    rule301 = ReplacementRule(pattern301, replacement301)
    pattern302 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_/sqrt(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons280, cons295)
    def replacement302(m, d, c, a, x, e):
        rubi.append(302)
        return Dist(S(2)*a*(c*(d + e*x)/(-a*e*Rt(-c/a, S(2)) + c*d))**(-m)*sqrt(S(1) + c*x**S(2)/a)*(d + e*x)**m*Rt(-c/a, S(2))/(c*sqrt(a + c*x**S(2))), Subst(Int((S(2)*a*e*x**S(2)*Rt(-c/a, S(2))/(-a*e*Rt(-c/a, S(2)) + c*d) + S(1))**m/sqrt(-x**S(2) + S(1)), x), x, sqrt(-x*Rt(-c/a, S(2))/S(2) + S(1)/2)), x)
    rule302 = ReplacementRule(pattern302, replacement302)
    pattern303 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons244, cons296, cons163)
    def replacement303(p, m, b, d, c, a, x, e):
        rubi.append(303)
        return Dist(p*(-S(4)*a*c + b**S(2))/(S(2)*(m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), Int((d + e*x)**(m + S(2))*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) - Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*(-S(2)*a*e + b*d + x*(-b*e + S(2)*c*d))/(S(2)*(m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule303 = ReplacementRule(pattern303, replacement303)
    pattern304 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons280, cons244, cons296, cons163)
    def replacement304(p, m, d, c, a, x, e):
        rubi.append(304)
        return -Dist(S(2)*a*c*p/((m + S(1))*(a*e**S(2) + c*d**S(2))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x)**(m + S(2)), x), x) - Simp((a + c*x**S(2))**p*(d + e*x)**(m + S(1))*(-S(2)*a*e + S(2)*c*d*x)/(S(2)*(m + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule304 = ReplacementRule(pattern304, replacement304)
    pattern305 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons244, cons296, cons137)
    def replacement305(p, m, b, d, c, a, x, e):
        rubi.append(305)
        return -Dist(S(2)*(S(2)*p + S(3))*(a*e**S(2) - b*d*e + c*d**S(2))/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**(m + S(-2))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*(-S(2)*a*e + b*d + x*(-b*e + S(2)*c*d))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule305 = ReplacementRule(pattern305, replacement305)
    pattern306 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons280, cons244, cons296, cons137)
    def replacement306(p, m, d, c, a, x, e):
        rubi.append(306)
        return Dist((S(2)*p + S(3))*(a*e**S(2) + c*d**S(2))/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-2)), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(a*e - c*d*x)/(S(2)*a*c*(p + S(1))), x)
    rule306 = ReplacementRule(pattern306, replacement306)
    pattern307 = Pattern(Integral(S(1)/((x_*WC('e', S(1)) + WC('d', S(0)))*sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons239)
    def replacement307(b, d, c, a, x, e):
        rubi.append(307)
        return Dist(S(-2), Subst(Int(S(1)/(S(4)*a*e**S(2) - S(4)*b*d*e + S(4)*c*d**S(2) - x**S(2)), x), x, (S(2)*a*e - b*d - x*(-b*e + S(2)*c*d))/sqrt(a + b*x + c*x**S(2))), x)
    rule307 = ReplacementRule(pattern307, replacement307)
    pattern308 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('c', S(1)))*(d_ + x_*WC('e', S(1)))), x_), cons2, cons7, cons27, cons48, cons297)
    def replacement308(d, c, a, x, e):
        rubi.append(308)
        return -Subst(Int(S(1)/(a*e**S(2) + c*d**S(2) - x**S(2)), x), x, (a*e - c*d*x)/sqrt(a + c*x**S(2)))
    rule308 = ReplacementRule(pattern308, replacement308)
    pattern309 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons279, cons239, cons147, cons240)
    def replacement309(p, m, b, d, a, c, x, e):
        rubi.append(309)
        return -Simp(((b + S(2)*c*x + Rt(-S(4)*a*c + b**S(2), S(2)))*(-b*e + S(2)*c*d + e*Rt(-S(4)*a*c + b**S(2), S(2)))/((b + S(2)*c*x - Rt(-S(4)*a*c + b**S(2), S(2)))*(-b*e + S(2)*c*d - e*Rt(-S(4)*a*c + b**S(2), S(2)))))**(-p)*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*(b + S(2)*c*x - Rt(-S(4)*a*c + b**S(2), S(2)))*Hypergeometric2F1(m + S(1), -p, m + S(2), -S(4)*c*(d + e*x)*Rt(-S(4)*a*c + b**S(2), S(2))/((b + S(2)*c*x - Rt(-S(4)*a*c + b**S(2), S(2)))*(-b*e + S(2)*c*d - e*Rt(-S(4)*a*c + b**S(2), S(2)))))/((m + S(1))*(-b*e + S(2)*c*d + e*Rt(-S(4)*a*c + b**S(2), S(2)))), x)
    rule309 = ReplacementRule(pattern309, replacement309)
    pattern310 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons5, cons280, cons147, cons240)
    def replacement310(p, m, d, c, a, x, e):
        rubi.append(310)
        return Simp(((c*d + e*Rt(-a*c, S(2)))*(c*x + Rt(-a*c, S(2)))/((c*d - e*Rt(-a*c, S(2)))*(c*x - Rt(-a*c, S(2)))))**(-p)*(a + c*x**S(2))**p*(d + e*x)**(m + S(1))*(-c*x + Rt(-a*c, S(2)))*Hypergeometric2F1(m + S(1), -p, m + S(2), S(2)*c*(d + e*x)*Rt(-a*c, S(2))/((c*d - e*Rt(-a*c, S(2)))*(-c*x + Rt(-a*c, S(2)))))/((m + S(1))*(c*d + e*Rt(-a*c, S(2)))), x)
    rule310 = ReplacementRule(pattern310, replacement310)
    pattern311 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons279, cons239, cons242, cons13, cons137)
    def replacement311(p, m, b, d, c, a, x, e):
        rubi.append(311)
        return Dist(m*(-b*e + S(2)*c*d)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((b + S(2)*c*x)*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule311 = ReplacementRule(pattern311, replacement311)
    pattern312 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons5, cons280, cons242, cons13, cons137)
    def replacement312(p, m, d, c, a, x, e):
        rubi.append(312)
        return -Dist(d*m/(S(2)*a*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1)), x), x) - Simp(x*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m/(S(2)*a*(p + S(1))), x)
    rule312 = ReplacementRule(pattern312, replacement312)
    pattern313 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons279, cons239, cons242)
    def replacement313(p, m, b, d, c, a, x, e):
        rubi.append(313)
        return Dist((-b*e + S(2)*c*d)/(S(2)*a*e**S(2) - S(2)*b*d*e + S(2)*c*d**S(2)), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) + Simp(e*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/((m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule313 = ReplacementRule(pattern313, replacement313)
    pattern314 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons5, cons280, cons242)
    def replacement314(p, m, d, c, a, x, e):
        rubi.append(314)
        return Dist(c*d/(a*e**S(2) + c*d**S(2)), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1)), x), x) + Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(1))/((m + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule314 = ReplacementRule(pattern314, replacement314)
    pattern315 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons279, cons239, cons13, cons163, cons298, cons66, cons299, cons300)
    def replacement315(p, m, b, d, c, a, x, e):
        rubi.append(315)
        return -Dist(p/(e*(m + S(1))), Int((b + S(2)*c*x)*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + S(1))), x)
    rule315 = ReplacementRule(pattern315, replacement315)
    pattern316 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons280, cons13, cons163, cons298, cons66, cons299, cons301)
    def replacement316(p, m, d, c, a, x, e):
        rubi.append(316)
        return -Dist(S(2)*c*p/(e*(m + S(1))), Int(x*(a + c*x**S(2))**(p + S(-1))*(d + e*x)**(m + S(1)), x), x) + Simp((a + c*x**S(2))**p*(d + e*x)**(m + S(1))/(e*(m + S(1))), x)
    rule316 = ReplacementRule(pattern316, replacement316)
    pattern317 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons279, cons239, cons13, cons163, cons238, cons302, cons303, cons300)
    def replacement317(p, m, b, d, c, a, x, e):
        rubi.append(317)
        return -Dist(p/(e*(m + S(2)*p + S(1))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(-1))*Simp(-S(2)*a*e + b*d + x*(-b*e + S(2)*c*d), x), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(e*(m + S(2)*p + S(1))), x)
    rule317 = ReplacementRule(pattern317, replacement317)
    pattern318 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons280, cons13, cons163, cons238, cons302, cons303, cons301)
    def replacement318(p, m, d, c, a, x, e):
        rubi.append(318)
        return Dist(S(2)*p/(e*(m + S(2)*p + S(1))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x)**m*Simp(a*e - c*d*x, x), x), x) + Simp((a + c*x**S(2))**p*(d + e*x)**(m + S(1))/(e*(m + S(2)*p + S(1))), x)
    rule318 = ReplacementRule(pattern318, replacement318)
    pattern319 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons244, cons137, cons168, cons304, cons300)
    def replacement319(p, m, b, d, c, a, x, e):
        rubi.append(319)
        return -Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*(b*e*m + S(2)*c*d*(S(2)*p + S(3)) + S(2)*c*e*x*(m + S(2)*p + S(3))), x), x) + Simp((b + S(2)*c*x)*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule319 = ReplacementRule(pattern319, replacement319)
    pattern320 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons280, cons244, cons137, cons168, cons304, cons301)
    def replacement320(p, m, d, c, a, x, e):
        rubi.append(320)
        return Dist(S(1)/(S(2)*a*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(d*(S(2)*p + S(3)) + e*x*(m + S(2)*p + S(3))), x), x) - Simp(x*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m/(S(2)*a*(p + S(1))), x)
    rule320 = ReplacementRule(pattern320, replacement320)
    pattern321 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons226, cons279, cons239, cons244, cons137, cons166, cons300)
    def replacement321(p, m, b, d, c, a, x, e):
        rubi.append(321)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**(m + S(-2))*(a + b*x + c*x**S(2))**(p + S(1))*Simp(-S(2)*c*d**S(2)*(S(2)*p + S(3)) + e*x*(b*e - S(2)*c*d)*(m + S(2)*p + S(2)) + e*(S(2)*a*e*(m + S(-1)) + b*d*(-m + S(2)*p + S(4))), x), x), x) + Simp((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*(-S(2)*a*e + b*d + x*(-b*e + S(2)*c*d))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule321 = ReplacementRule(pattern321, replacement321)
    pattern322 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons280, cons244, cons137, cons166, cons301)
    def replacement322(p, m, d, c, a, x, e):
        rubi.append(322)
        return Dist(-S(1)/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-2))*Simp(a*e**S(2)*(m + S(-1)) - c*d**S(2)*(S(2)*p + S(3)) - c*d*e*x*(m + S(2)*p + S(2)), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(a*e - c*d*x)/(S(2)*a*c*(p + S(1))), x)
    rule322 = ReplacementRule(pattern322, replacement322)
    pattern323 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons226, cons279, cons239, cons13, cons137, cons300)
    def replacement323(p, m, b, d, c, a, x, e):
        rubi.append(323)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(a*e**S(2) - b*d*e + c*d**S(2))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))*Simp(-S(2)*a*c*e**S(2)*(m + S(2)*p + S(3)) + b**S(2)*e**S(2)*(m + p + S(2)) + b*c*d*e*(-m + S(2)*p + S(2)) - S(2)*c**S(2)*d**S(2)*(S(2)*p + S(3)) - c*e*x*(-b*e + S(2)*c*d)*(m + S(2)*p + S(4)), x), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(S(2)*a*c*e - b**S(2)*e + b*c*d + c*x*(-b*e + S(2)*c*d))/((p + S(1))*(-S(4)*a*c + b**S(2))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule323 = ReplacementRule(pattern323, replacement323)
    pattern324 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons280, cons13, cons137, cons301)
    def replacement324(p, m, d, c, a, x, e):
        rubi.append(324)
        return Dist(S(1)/(S(2)*a*(p + S(1))*(a*e**S(2) + c*d**S(2))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**m*Simp(a*e**S(2)*(m + S(2)*p + S(3)) + c*d**S(2)*(S(2)*p + S(3)) + c*d*e*x*(m + S(2)*p + S(4)), x), x), x) - Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(1))*(a*e + c*d*x)/(S(2)*a*(p + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule324 = ReplacementRule(pattern324, replacement324)
    pattern325 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons279, cons239, cons305, cons238, cons300)
    def replacement325(p, m, b, d, c, a, x, e):
        rubi.append(325)
        return Dist(S(1)/(c*(m + S(2)*p + S(1))), Int((d + e*x)**(m + S(-2))*(a + b*x + c*x**S(2))**p*Simp(c*d**S(2)*(m + S(2)*p + S(1)) + e*x*(m + p)*(-b*e + S(2)*c*d) - e*(a*e*(m + S(-1)) + b*d*(p + S(1))), x), x), x) + Simp(e*(d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m + S(2)*p + S(1))), x)
    rule325 = ReplacementRule(pattern325, replacement325)
    pattern326 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons5, cons280, cons305, cons238, cons301)
    def replacement326(p, m, d, c, a, x, e):
        rubi.append(326)
        return Dist(S(1)/(c*(m + S(2)*p + S(1))), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(-2))*Simp(-a*e**S(2)*(m + S(-1)) + c*d**S(2)*(m + S(2)*p + S(1)) + S(2)*c*d*e*x*(m + p), x), x), x) + Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))/(c*(m + S(2)*p + S(1))), x)
    rule326 = ReplacementRule(pattern326, replacement326)
    pattern327 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons279, cons239, cons306)
    def replacement327(p, m, b, d, c, a, x, e):
        rubi.append(327)
        return Dist(S(1)/((m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*Simp(-b*e*(m + p + S(2)) + c*d*(m + S(1)) - c*e*x*(m + S(2)*p + S(3)), x), x), x) + Simp(e*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/((m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule327 = ReplacementRule(pattern327, replacement327)
    pattern328 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_, x_), cons2, cons7, cons27, cons48, cons21, cons5, cons280, cons307)
    def replacement328(p, m, d, c, a, x, e):
        rubi.append(328)
        return Dist(c/((m + S(1))*(a*e**S(2) + c*d**S(2))), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1))*Simp(d*(m + S(1)) - e*x*(m + S(2)*p + S(3)), x), x), x) + Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(1))/((m + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule328 = ReplacementRule(pattern328, replacement328)
    def With329(b, d, c, a, x, e):
        q = Rt(S(3)*c*e**S(2)*(-b*e + S(2)*c*d), S(3))
        rubi.append(329)
        return -Simp(S(3)*c*e*log(d + e*x)/(S(2)*q**S(2)), x) + Simp(S(3)*c*e*log(-b*e + c*d - c*e*x - q*(a + b*x + c*x**S(2))**(S(1)/3))/(S(2)*q**S(2)), x) - Simp(sqrt(S(3))*c*e*ArcTan(sqrt(S(3))/S(3) + S(2)*sqrt(S(3))*(-b*e + c*d - c*e*x)/(S(3)*q*(a + b*x + c*x**S(2))**(S(1)/3)))/q**S(2), x)
    pattern329 = Pattern(Integral(S(1)/((x_*WC('e', S(1)) + WC('d', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**(S(1)/3)), x_), cons2, cons3, cons7, cons27, cons48, cons239, cons308, cons309)
    rule329 = ReplacementRule(pattern329, With329)
    def With330(d, c, a, x, e):
        q = Rt(S(6)*c**S(2)*e**S(2)/d**S(2), S(3))
        rubi.append(330)
        return -Simp(S(3)*c*e*log(d + e*x)/(S(2)*d**S(2)*q**S(2)), x) + Simp(S(3)*c*e*log(c*d - c*e*x - d*q*(a + c*x**S(2))**(S(1)/3))/(S(2)*d**S(2)*q**S(2)), x) - Simp(sqrt(S(3))*c*e*ArcTan(S(2)*sqrt(S(3))*c*(d - e*x)/(S(3)*d*q*(a + c*x**S(2))**(S(1)/3)) + sqrt(S(3))/S(3))/(d**S(2)*q**S(2)), x)
    pattern330 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('c', S(1)))**(S(1)/3)*(d_ + x_*WC('e', S(1)))), x_), cons2, cons7, cons27, cons48, cons310)
    rule330 = ReplacementRule(pattern330, With330)
    def With331(b, d, c, a, x, e):
        q = Rt(-S(3)*c*e**S(2)*(-b*e + S(2)*c*d), S(3))
        rubi.append(331)
        return -Simp(S(3)*c*e*log(d + e*x)/(S(2)*q**S(2)), x) + Simp(S(3)*c*e*log(-b*e + c*d - c*e*x + q*(a + b*x + c*x**S(2))**(S(1)/3))/(S(2)*q**S(2)), x) - Simp(sqrt(S(3))*c*e*ArcTan(sqrt(S(3))/S(3) - S(2)*sqrt(S(3))*(-b*e + c*d - c*e*x)/(S(3)*q*(a + b*x + c*x**S(2))**(S(1)/3)))/q**S(2), x)
    pattern331 = Pattern(Integral(S(1)/((x_*WC('e', S(1)) + WC('d', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**(S(1)/3)), x_), cons2, cons3, cons7, cons27, cons48, cons239, cons308, cons311)
    rule331 = ReplacementRule(pattern331, With331)
    def With332(b, d, c, a, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(332)
        return Dist((b + S(2)*c*x - q)**(S(1)/3)*(b + S(2)*c*x + q)**(S(1)/3)/(a + b*x + c*x**S(2))**(S(1)/3), Int(S(1)/((d + e*x)*(b + S(2)*c*x - q)**(S(1)/3)*(b + S(2)*c*x + q)**(S(1)/3)), x), x)
    pattern332 = Pattern(Integral(S(1)/((x_*WC('e', S(1)) + WC('d', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**(S(1)/3)), x_), cons2, cons3, cons7, cons27, cons48, cons226, cons312)
    rule332 = ReplacementRule(pattern332, With332)
    pattern333 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('c', S(1)))**(S(1)/4)*(d_ + x_*WC('e', S(1)))), x_), cons2, cons7, cons27, cons48, cons280)
    def replacement333(d, c, a, x, e):
        rubi.append(333)
        return Dist(d, Int(S(1)/((a + c*x**S(2))**(S(1)/4)*(d**S(2) - e**S(2)*x**S(2))), x), x) - Dist(e, Int(x/((a + c*x**S(2))**(S(1)/4)*(d**S(2) - e**S(2)*x**S(2))), x), x)
    rule333 = ReplacementRule(pattern333, replacement333)
    pattern334 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('c', S(1)))**(S(3)/4)*(d_ + x_*WC('e', S(1)))), x_), cons2, cons7, cons27, cons48, cons280)
    def replacement334(d, c, a, x, e):
        rubi.append(334)
        return Dist(d, Int(S(1)/((a + c*x**S(2))**(S(3)/4)*(d**S(2) - e**S(2)*x**S(2))), x), x) - Dist(e, Int(x/((a + c*x**S(2))**(S(3)/4)*(d**S(2) - e**S(2)*x**S(2))), x), x)
    rule334 = ReplacementRule(pattern334, replacement334)
    pattern335 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons232, cons229)
    def replacement335(p, b, d, c, a, x, e):
        rubi.append(335)
        return Dist((-S(4)*c/(-S(4)*a*c + b**S(2)))**(-p), Subst(Int(Simp(-x**S(2)/(-S(4)*a*c + b**S(2)) + S(1), x)**p/Simp(-b*e + S(2)*c*d + e*x, x), x), x, b + S(2)*c*x), x)
    rule335 = ReplacementRule(pattern335, replacement335)
    pattern336 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons313, cons229)
    def replacement336(p, b, d, c, a, x, e):
        rubi.append(336)
        return Dist((-c*(a + b*x + c*x**S(2))/(-S(4)*a*c + b**S(2)))**(-p)*(a + b*x + c*x**S(2))**p, Int((-a*c/(-S(4)*a*c + b**S(2)) - b*c*x/(-S(4)*a*c + b**S(2)) - c**S(2)*x**S(2)/(-S(4)*a*c + b**S(2)))**p/(d + e*x), x), x)
    rule336 = ReplacementRule(pattern336, replacement336)
    pattern337 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons5, cons280, cons147, cons43, cons293)
    def replacement337(p, m, d, c, a, x, e):
        rubi.append(337)
        return Int((d + e*x)**m*(-x*Rt(-c, S(2)) + Rt(a, S(2)))**p*(x*Rt(-c, S(2)) + Rt(a, S(2)))**p, x)
    rule337 = ReplacementRule(pattern337, replacement337)
    def With338(p, m, b, d, a, c, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(338)
        return -Dist((e*(b + S(2)*c*x - q)/(S(2)*c*(d + e*x)))**(-p)*(e*(b + S(2)*c*x + q)/(S(2)*c*(d + e*x)))**(-p)*(a + b*x + c*x**S(2))**p*(S(1)/(d + e*x))**(S(2)*p)/e, Subst(Int(x**(-m - S(2)*p + S(-2))*Simp(-x*(d - e*(b - q)/(S(2)*c)) + S(1), x)**p*Simp(-x*(d - e*(b + q)/(S(2)*c)) + S(1), x)**p, x), x, S(1)/(d + e*x)), x)
    pattern338 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons5, cons226, cons279, cons239, cons147, cons84)
    rule338 = ReplacementRule(pattern338, With338)
    def With339(p, m, d, c, a, x, e):
        q = Rt(-a*c, S(2))
        rubi.append(339)
        return -Dist((e*(c*x + q)/(c*(d + e*x)))**(-p)*(-e*(-c*x + q)/(c*(d + e*x)))**(-p)*(a + c*x**S(2))**p*(S(1)/(d + e*x))**(S(2)*p)/e, Subst(Int(x**(-m - S(2)*p + S(-2))*Simp(-x*(d - e*q/c) + S(1), x)**p*Simp(-x*(d + e*q/c) + S(1), x)**p, x), x, S(1)/(d + e*x)), x)
    pattern339 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons5, cons280, cons147, cons84)
    rule339 = ReplacementRule(pattern339, With339)
    def With340(p, m, b, d, a, c, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(340)
        return Dist((-(d + e*x)/(d - e*(b - q)/(S(2)*c)) + S(1))**(-p)*(-(d + e*x)/(d - e*(b + q)/(S(2)*c)) + S(1))**(-p)*(a + b*x + c*x**S(2))**p/e, Subst(Int(x**m*Simp(-x/(d - e*(b - q)/(S(2)*c)) + S(1), x)**p*Simp(-x/(d - e*(b + q)/(S(2)*c)) + S(1), x)**p, x), x, d + e*x), x)
    pattern340 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons226, cons279, cons239, cons147)
    rule340 = ReplacementRule(pattern340, With340)
    def With341(p, m, d, c, a, x, e):
        q = Rt(-a*c, S(2))
        rubi.append(341)
        return Dist((a + c*x**S(2))**p*(-(d + e*x)/(d - e*q/c) + S(1))**(-p)*(-(d + e*x)/(d + e*q/c) + S(1))**(-p)/e, Subst(Int(x**m*Simp(-x/(d - e*q/c) + S(1), x)**p*Simp(-x/(d + e*q/c) + S(1), x)**p, x), x, d + e*x), x)
    pattern341 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons5, cons280, cons147)
    rule341 = ReplacementRule(pattern341, With341)
    pattern342 = Pattern(Integral((u_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + u_**S(2)*WC('c', S(1)) + u_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons5, cons68, cons69)
    def replacement342(p, u, m, b, d, c, a, x, e):
        rubi.append(342)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((d + e*x)**m*(a + b*x + c*x**S(2))**p, x), x, u), x)
    rule342 = ReplacementRule(pattern342, replacement342)
    pattern343 = Pattern(Integral((a_ + u_**S(2)*WC('c', S(1)))**WC('p', S(1))*(u_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons21, cons5, cons68, cons69)
    def replacement343(p, u, m, d, c, a, x, e):
        rubi.append(343)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + c*x**S(2))**p*(d + e*x)**m, x), x, u), x)
    rule343 = ReplacementRule(pattern343, replacement343)
    pattern344 = Pattern(Integral(x_**WC('n', S(1))*(a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons5, cons85, cons314)
    def replacement344(p, d, c, n, a, x, e):
        rubi.append(344)
        return Dist(d, Int(x**n*(a + c*x**S(2))**p, x), x) + Dist(e, Int(x**(n + S(1))*(a + c*x**S(2))**p, x), x)
    rule344 = ReplacementRule(pattern344, replacement344)
    pattern345 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))/sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons45, cons316)
    def replacement345(m, g, b, f, d, c, a, x, e):
        rubi.append(345)
        return Dist((f + g*x)/sqrt(a + b*x + c*x**S(2)), Int((d + e*x)**m, x), x)
    rule345 = ReplacementRule(pattern345, replacement345)
    pattern346 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons45, cons316, cons147, cons242)
    def replacement346(p, m, g, b, f, d, c, a, x, e):
        rubi.append(346)
        return -Simp(f*g*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(b*(p + S(1))*(-d*g + e*f)), x)
    rule346 = ReplacementRule(pattern346, replacement346)
    pattern347 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons45, cons316, cons147, cons244, cons137, cons168)
    def replacement347(p, m, g, b, f, d, c, a, x, e):
        rubi.append(347)
        return -Dist(e*g*m/(S(2)*c*(p + S(1))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp(g*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/(S(2)*c*(p + S(1))), x)
    rule347 = ReplacementRule(pattern347, replacement347)
    pattern348 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons45, cons316, cons147, cons13, cons137, cons317)
    def replacement348(p, m, g, b, f, d, c, a, x, e):
        rubi.append(348)
        return Dist(e*f*g*(m + S(2)*p + S(3))/(b*(p + S(1))*(-d*g + e*f)), Int((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1)), x), x) - Simp(f*g*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(b*(p + S(1))*(-d*g + e*f)), x)
    rule348 = ReplacementRule(pattern348, replacement348)
    pattern349 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons45, cons316, cons147, cons31, cons94, cons225, cons318)
    def replacement349(p, m, g, b, f, d, c, a, x, e):
        rubi.append(349)
        return -Dist(g*(S(2)*p + S(1))/(e*(m + S(1))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) + Simp((d + e*x)**(m + S(1))*(f + g*x)*(a + b*x + c*x**S(2))**p/(e*(m + S(1))), x)
    rule349 = ReplacementRule(pattern349, replacement349)
    pattern350 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons45, cons316, cons147, cons31, cons94, cons319)
    def replacement350(p, m, g, b, f, d, c, a, x, e):
        rubi.append(350)
        return -Dist(g*(m + S(2)*p + S(3))/((m + S(1))*(-d*g + e*f)), Int((d + e*x)**(m + S(1))*(f + g*x)*(a + b*x + c*x**S(2))**p, x), x) + Simp(S(2)*f*g*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(b*(m + S(1))*(-d*g + e*f)), x)
    rule350 = ReplacementRule(pattern350, replacement350)
    pattern351 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons45, cons316, cons147, cons62, cons319, cons320)
    def replacement351(p, m, g, b, f, d, c, a, x, e):
        rubi.append(351)
        return -Dist(b*m*(-d*g + e*f)/(S(2)*c*f*(m + S(2)*p + S(2))), Int((d + e*x)**(m + S(-1))*(f + g*x)*(a + b*x + c*x**S(2))**p, x), x) + Simp(g*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m + S(2)*p + S(2))), x)
    rule351 = ReplacementRule(pattern351, replacement351)
    pattern352 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons45, cons316, cons147, cons319)
    def replacement352(p, m, g, b, f, d, c, a, x, e):
        rubi.append(352)
        return Dist((S(2)*p + S(1))*(-d*g + e*f)/(e*(m + S(2)*p + S(2))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**p, x), x) + Simp((d + e*x)**(m + S(1))*(f + g*x)*(a + b*x + c*x**S(2))**p/(e*(m + S(2)*p + S(2))), x)
    rule352 = ReplacementRule(pattern352, replacement352)
    pattern353 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons45, cons321, cons147, cons239, cons13, cons322)
    def replacement353(p, f, b, g, d, c, a, x, e):
        rubi.append(353)
        return Dist((-b*g + S(2)*c*f)/(-b*e + S(2)*c*d), Int((a + b*x + c*x**S(2))**p, x), x) - Dist((-d*g + e*f)/(-b*e + S(2)*c*d), Int((b + S(2)*c*x)*(a + b*x + c*x**S(2))**p/(d + e*x), x), x)
    rule353 = ReplacementRule(pattern353, replacement353)
    pattern354 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons45, cons321, cons147, cons323)
    def replacement354(p, m, g, b, f, d, c, a, x, e):
        rubi.append(354)
        return Dist(g/e, Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) + Dist((-d*g + e*f)/e, Int((d + e*x)**m*(a + b*x + c*x**S(2))**p, x), x)
    rule354 = ReplacementRule(pattern354, replacement354)
    pattern355 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons45, cons321, cons147, cons239, cons242)
    def replacement355(p, m, f, g, b, d, c, a, x, e):
        rubi.append(355)
        return Dist((-b*g + S(2)*c*f)/(-b*e + S(2)*c*d), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) - Dist((-d*g + e*f)/(-b*e + S(2)*c*d), Int((b + S(2)*c*x)*(d + e*x)**m*(a + b*x + c*x**S(2))**p, x), x)
    rule355 = ReplacementRule(pattern355, replacement355)
    pattern356 = Pattern(Integral((f_ + x_*WC('g', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons45, cons321, cons147, cons239, cons319, cons270, cons31, cons94)
    def replacement356(p, m, g, b, f, d, c, a, x, e):
        rubi.append(356)
        return Dist((S(2)*c*e*f*(m + S(2)*p + S(2)) - g*(b*e*(m + S(1)) + S(2)*c*d*(S(2)*p + S(1))))/(e*(m + S(1))*(-b*e + S(2)*c*d)), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) - Simp((b + S(2)*c*x)*(d + e*x)**(m + S(1))*(-d*g + e*f)*(a + b*x + c*x**S(2))**p/(e*(m + S(1))*(-b*e + S(2)*c*d)), x)
    rule356 = ReplacementRule(pattern356, replacement356)
    pattern357 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons45, cons321, cons147, cons239, cons319, cons270, cons272, cons324)
    def replacement357(p, m, f, g, b, d, c, a, x, e):
        rubi.append(357)
        return Dist((S(2)*c*e*f*(m + S(2)*p + S(2)) - g*(b*e*(m + S(1)) + S(2)*c*(S(2)*d*p + d)))/(S(2)*c*e*(m + S(2)*p + S(2))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**p, x), x) + Simp(g*(b + S(2)*c*x)*(d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p/(S(2)*c*e*(m + S(2)*p + S(2))), x)
    rule357 = ReplacementRule(pattern357, replacement357)
    pattern358 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons315, cons45, cons147)
    def replacement358(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(358)
        return Dist(c**(-IntPart(p))*(b/S(2) + c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((b/S(2) + c*x)**(S(2)*p)*(d + e*x)**m*(f + g*x)**n, x), x)
    rule358 = ReplacementRule(pattern358, replacement358)
    pattern359 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons315, cons226, cons256, cons38)
    def replacement359(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(359)
        return Int((d + e*x)**(m + p)*(f + g*x)**n*(a/d + c*x/e)**p, x)
    rule359 = ReplacementRule(pattern359, replacement359)
    pattern360 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(d_ + x_*WC('e', S(1)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons315, cons257, cons325)
    def replacement360(p, m, f, g, d, c, n, a, x, e):
        rubi.append(360)
        return Int((d + e*x)**(m + p)*(f + g*x)**n*(a/d + c*x/e)**p, x)
    rule360 = ReplacementRule(pattern360, replacement360)
    pattern361 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons256, cons84, cons314)
    def replacement361(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(361)
        return Dist(d**m*e**m, Int((f + g*x)**n*(a*e + c*d*x)**(-m)*(a + b*x + c*x**S(2))**(m + p), x), x)
    rule361 = ReplacementRule(pattern361, replacement361)
    pattern362 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons257, cons84, cons314)
    def replacement362(p, m, f, g, d, c, n, a, x, e):
        rubi.append(362)
        return Dist(d**m*e**m, Int((a + c*x**S(2))**(m + p)*(f + g*x)**n*(a*e + c*d*x)**(-m), x), x)
    rule362 = ReplacementRule(pattern362, replacement362)
    pattern363 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons256, cons326)
    def replacement363(p, m, f, g, b, d, a, c, x, e):
        rubi.append(363)
        return Simp(g*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m + S(2)*p + S(2))), x)
    rule363 = ReplacementRule(pattern363, replacement363)
    pattern364 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons257, cons327)
    def replacement364(p, m, f, g, d, c, a, x, e):
        rubi.append(364)
        return Simp(g*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m/(c*(m + S(2)*p + S(2))), x)
    rule364 = ReplacementRule(pattern364, replacement364)
    pattern365 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons256, cons244, cons137, cons168)
    def replacement365(p, m, f, g, b, d, a, c, x, e):
        rubi.append(365)
        return -Dist(e*(e*(p + S(1))*(-b*g + S(2)*c*f) + m*(c*e*f + g*(-b*e + c*d)))/(c*(p + S(1))*(-b*e + S(2)*c*d)), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((d + e*x)**m*(c*e*f + g*(-b*e + c*d))*(a + b*x + c*x**S(2))**(p + S(1))/(c*(p + S(1))*(-b*e + S(2)*c*d)), x)
    rule365 = ReplacementRule(pattern365, replacement365)
    pattern366 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons257, cons244, cons137, cons168)
    def replacement366(p, m, f, g, d, c, a, x, e):
        rubi.append(366)
        return -Dist(e*(S(2)*e*f*(p + S(1)) + m*(d*g + e*f))/(S(2)*c*d*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1)), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**m*(d*g + e*f)/(S(2)*c*d*(p + S(1))), x)
    rule366 = ReplacementRule(pattern366, replacement366)
    pattern367 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons256, cons139, cons328, cons54)
    def replacement367(p, m, f, g, b, d, a, c, x, e):
        rubi.append(367)
        return -Dist(e*(e*(p + S(1))*(-b*g + S(2)*c*f) + m*(c*e*f + g*(-b*e + c*d)))/(c*(p + S(1))*(-b*e + S(2)*c*d)), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((d + e*x)**m*(c*e*f + g*(-b*e + c*d))*(a + b*x + c*x**S(2))**(p + S(1))/(c*(p + S(1))*(-b*e + S(2)*c*d)), x)
    rule367 = ReplacementRule(pattern367, replacement367)
    pattern368 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons257, cons139, cons328, cons54)
    def replacement368(p, m, f, g, d, c, a, x, e):
        rubi.append(368)
        return -Dist(e*(S(2)*e*f*(p + S(1)) + m*(d*g + e*f))/(S(2)*c*d*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1)), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**m*(d*g + e*f)/(S(2)*c*d*(p + S(1))), x)
    rule368 = ReplacementRule(pattern368, replacement368)
    pattern369 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons256, cons329, cons253)
    def replacement369(p, m, f, g, b, d, a, c, x, e):
        rubi.append(369)
        return Dist((e*(p + S(1))*(-b*g + S(2)*c*f) + m*(c*e*f + g*(-b*e + c*d)))/(e*(-b*e + S(2)*c*d)*(m + p + S(1))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) + Simp((d + e*x)**m*(d*g - e*f)*(a + b*x + c*x**S(2))**(p + S(1))/((-b*e + S(2)*c*d)*(m + p + S(1))), x)
    rule369 = ReplacementRule(pattern369, replacement369)
    pattern370 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons257, cons329, cons253)
    def replacement370(p, m, f, g, d, c, a, x, e):
        rubi.append(370)
        return Dist((S(2)*c*e*f*(p + S(1)) + m*(c*d*g + c*e*f))/(S(2)*c*d*e*(m + p + S(1))), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1)), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**m*(d*g - e*f)/(S(2)*c*d*(m + p + S(1))), x)
    rule370 = ReplacementRule(pattern370, replacement370)
    pattern371 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons256, cons319)
    def replacement371(p, m, f, g, b, d, a, c, x, e):
        rubi.append(371)
        return Dist((e*(p + S(1))*(-b*g + S(2)*c*f) + m*(c*e*f + g*(-b*e + c*d)))/(c*e*(m + S(2)*p + S(2))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**p, x), x) + Simp(g*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m + S(2)*p + S(2))), x)
    rule371 = ReplacementRule(pattern371, replacement371)
    pattern372 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons257, cons319)
    def replacement372(p, m, f, g, d, c, a, x, e):
        rubi.append(372)
        return Dist((S(2)*e*f*(p + S(1)) + m*(d*g + e*f))/(e*(m + S(2)*p + S(2))), Int((a + c*x**S(2))**p*(d + e*x)**m, x), x) + Simp(g*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m/(c*(m + S(2)*p + S(2))), x)
    rule372 = ReplacementRule(pattern372, replacement372)
    pattern373 = Pattern(Integral(x_**S(2)*(a_ + x_**S(2)*WC('c', S(1)))**p_*(f_ + x_*WC('g', S(1))), x_), cons2, cons7, cons125, cons208, cons330, cons13, cons331)
    def replacement373(p, f, g, c, a, x):
        rubi.append(373)
        return -Dist(S(1)/(S(2)*a*c*(p + S(1))), Int(x*(a + c*x**S(2))**(p + S(1))*Simp(S(2)*a*g - c*f*x*(S(2)*p + S(5)), x), x), x) + Simp(x**S(2)*(a + c*x**S(2))**(p + S(1))*(a*g - c*f*x)/(S(2)*a*c*(p + S(1))), x)
    rule373 = ReplacementRule(pattern373, replacement373)
    pattern374 = Pattern(Integral(x_**S(2)*(a_ + x_**S(2)*WC('c', S(1)))**p_*(f_ + x_*WC('g', S(1))), x_), cons2, cons7, cons125, cons208, cons5, cons330)
    def replacement374(p, f, g, c, a, x):
        rubi.append(374)
        return Dist(S(1)/c, Int((a + c*x**S(2))**(p + S(1))*(f + g*x), x), x) - Dist(f**S(2)/c, Int((a + c*x**S(2))**(p + S(1))/(f - g*x), x), x)
    rule374 = ReplacementRule(pattern374, replacement374)
    pattern375 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons256, cons147, cons150, cons13, cons332)
    def replacement375(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(375)
        return Int((f + g*x)**n*(a/d + c*x/e)**(-m)*(a + b*x + c*x**S(2))**(m + p), x)
    rule375 = ReplacementRule(pattern375, replacement375)
    pattern376 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons257, cons147, cons150, cons13, cons332)
    def replacement376(p, m, f, g, d, c, n, a, x, e):
        rubi.append(376)
        return Dist(a**(-m)*d**(S(2)*m), Int((a + c*x**S(2))**(m + p)*(d - e*x)**(-m)*(f + g*x)**n, x), x)
    rule376 = ReplacementRule(pattern376, replacement376)
    pattern377 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons256, cons147, cons148, cons333)
    def replacement377(p, f, g, b, d, a, n, c, x, e):
        rubi.append(377)
        return -Dist(S(1)/(d*e*p*(-S(4)*a*c + b**S(2))), Int((f + g*x)**(n + S(-1))*(a + b*x + c*x**S(2))**p*Simp(-S(2)*a*c*(d*g*n - e*f*(S(2)*p + S(1))) + b*(a*e*g*n - c*d*f*(S(2)*p + S(1))) - c*g*x*(-S(2)*a*e + b*d)*(n + S(2)*p + S(1)), x), x), x) - Simp((f + g*x)**n*(a*(-b*e + S(2)*c*d) + c*x*(-S(2)*a*e + b*d))*(a + b*x + c*x**S(2))**p/(d*e*p*(-S(4)*a*c + b**S(2))), x)
    rule377 = ReplacementRule(pattern377, replacement377)
    pattern378 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons257, cons147, cons148, cons333)
    def replacement378(p, f, g, d, c, n, a, x, e):
        rubi.append(378)
        return -Dist(S(1)/(S(2)*d*e*p), Int((a + c*x**S(2))**p*(f + g*x)**(n + S(-1))*Simp(d*g*n - e*f*(S(2)*p + S(1)) - e*g*x*(n + S(2)*p + S(1)), x), x), x) + Simp((a + c*x**S(2))**p*(d - e*x)*(f + g*x)**n/(S(2)*d*e*p), x)
    rule378 = ReplacementRule(pattern378, replacement378)
    pattern379 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons256, cons147, cons196, cons333)
    def replacement379(p, f, g, b, d, a, n, c, x, e):
        rubi.append(379)
        return -Dist(S(1)/(d*e*p*(-S(4)*a*c + b**S(2))*(a*g**S(2) - b*f*g + c*f**S(2))), Int((f + g*x)**n*(a + b*x + c*x**S(2))**p*Simp(S(2)*a*c*(a*e*g**S(2)*(n + S(2)*p + S(1)) + c*f*(-d*g*n + S(2)*e*f*p + e*f)) + b**S(2)*g*(-a*e*g*(n + p + S(1)) + c*d*f*p) + b*c*(a*g*(d*g*(n + S(1)) + e*f*(n - S(2)*p)) - c*d*f**S(2)*(S(2)*p + S(1))) + c*g*x*(S(2)*a*c*(d*g + e*f) - b*(a*e*g + c*d*f))*(n + S(2)*p + S(2)), x), x), x) - Simp((f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**p*(a*c*d*(-b*g + S(2)*c*f) - a*e*(S(2)*a*c*g - b**S(2)*g + b*c*f) + c*x*(-a*e*(-b*g + S(2)*c*f) + c*d*(-S(2)*a*g + b*f)))/(d*e*p*(-S(4)*a*c + b**S(2))*(a*g**S(2) - b*f*g + c*f**S(2))), x)
    rule379 = ReplacementRule(pattern379, replacement379)
    pattern380 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))/(d_ + x_*WC('e', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons257, cons147, cons196, cons333)
    def replacement380(p, f, g, d, c, n, a, x, e):
        rubi.append(380)
        return Dist(S(1)/(S(2)*d*e*p*(a*g**S(2) + c*f**S(2))), Int((a + c*x**S(2))**p*(f + g*x)**n*Simp(a*e*g**S(2)*(n + S(2)*p + S(1)) - c*f*(d*g*n - e*(S(2)*f*p + f)) + c*g*x*(d*g + e*f)*(n + S(2)*p + S(2)), x), x), x) + Simp((a + c*x**S(2))**p*(f + g*x)**(n + S(1))*(-a*e*g + c*d*f - c*x*(d*g + e*f))/(S(2)*d*e*p*(a*g**S(2) + c*f**S(2))), x)
    rule380 = ReplacementRule(pattern380, replacement380)
    pattern381 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons315, cons226, cons256, cons147, cons41, cons334, cons335)
    def replacement381(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(381)
        return -Simp(e*(d + e*x)**(m + S(-1))*(f + g*x)**n*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m - n + S(-1))), x)
    rule381 = ReplacementRule(pattern381, replacement381)
    pattern382 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons315, cons257, cons147, cons41, cons336, cons335)
    def replacement382(p, m, f, g, d, c, n, a, x, e):
        rubi.append(382)
        return -Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(f + g*x)**n/(c*(m - n + S(-1))), x)
    rule382 = ReplacementRule(pattern382, replacement382)
    pattern383 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons315, cons226, cons256, cons147, cons41, cons337)
    def replacement383(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(383)
        return -Simp(e**S(2)*(d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/((n + S(1))*(-b*e*g + c*d*g + c*e*f)), x)
    rule383 = ReplacementRule(pattern383, replacement383)
    pattern384 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons315, cons257, cons147, cons41, cons337)
    def replacement384(p, m, f, g, d, c, n, a, x, e):
        rubi.append(384)
        return -Simp(e**S(2)*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1))/(c*(n + S(1))*(d*g + e*f)), x)
    rule384 = ReplacementRule(pattern384, replacement384)
    pattern385 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons256, cons147, cons41, cons338, cons163, cons89, cons339)
    def replacement385(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(385)
        return Dist(c*m/(e*g*(n + S(1))), Int((d + e*x)**(m + S(1))*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) + Simp((d + e*x)**m*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**p/(g*(n + S(1))), x)
    rule385 = ReplacementRule(pattern385, replacement385)
    pattern386 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons257, cons147, cons41, cons338, cons163, cons89, cons339)
    def replacement386(p, m, f, g, d, c, n, a, x, e):
        rubi.append(386)
        return Dist(c*m/(e*g*(n + S(1))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x)**(m + S(1))*(f + g*x)**(n + S(1)), x), x) + Simp((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**(n + S(1))/(g*(n + S(1))), x)
    rule386 = ReplacementRule(pattern386, replacement386)
    pattern387 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons315, cons226, cons256, cons147, cons41, cons338, cons163, cons335, cons340, cons341)
    def replacement387(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(387)
        return -Dist(m*(-b*e*g + c*d*g + c*e*f)/(e**S(2)*g*(m - n + S(-1))), Int((d + e*x)**(m + S(1))*(f + g*x)**n*(a + b*x + c*x**S(2))**(p + S(-1)), x), x) - Simp((d + e*x)**m*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**p/(g*(m - n + S(-1))), x)
    rule387 = ReplacementRule(pattern387, replacement387)
    pattern388 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons4, cons315, cons257, cons147, cons41, cons338, cons163, cons335, cons340, cons341)
    def replacement388(p, m, f, g, d, c, n, a, x, e):
        rubi.append(388)
        return -Dist(c*m*(d*g + e*f)/(e**S(2)*g*(m - n + S(-1))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x)**(m + S(1))*(f + g*x)**n, x), x) - Simp((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**(n + S(1))/(g*(m - n + S(-1))), x)
    rule388 = ReplacementRule(pattern388, replacement388)
    pattern389 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons256, cons147, cons41, cons338, cons137, cons88)
    def replacement389(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(389)
        return -Dist(e*g*n/(c*(p + S(1))), Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-1))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp(e*(d + e*x)**(m + S(-1))*(f + g*x)**n*(a + b*x + c*x**S(2))**(p + S(1))/(c*(p + S(1))), x)
    rule389 = ReplacementRule(pattern389, replacement389)
    pattern390 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons257, cons147, cons41, cons338, cons137, cons88)
    def replacement390(p, m, f, g, d, c, n, a, x, e):
        rubi.append(390)
        return -Dist(e*g*n/(c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-1)), x), x) + Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(f + g*x)**n/(c*(p + S(1))), x)
    rule390 = ReplacementRule(pattern390, replacement390)
    pattern391 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons315, cons226, cons256, cons147, cons41, cons338, cons137)
    def replacement391(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(391)
        return Dist(e**S(2)*g*(m - n + S(-2))/((p + S(1))*(-b*e*g + c*d*g + c*e*f)), Int((d + e*x)**(m + S(-1))*(f + g*x)**n*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp(e**S(2)*(d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/((p + S(1))*(-b*e*g + c*d*g + c*e*f)), x)
    rule391 = ReplacementRule(pattern391, replacement391)
    pattern392 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons4, cons315, cons257, cons147, cons41, cons338, cons137)
    def replacement392(p, m, f, g, d, c, n, a, x, e):
        rubi.append(392)
        return Dist(e**S(2)*g*(m - n + S(-2))/(c*(p + S(1))*(d*g + e*f)), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(f + g*x)**n, x), x) + Simp(e**S(2)*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1))/(c*(p + S(1))*(d*g + e*f)), x)
    rule392 = ReplacementRule(pattern392, replacement392)
    pattern393 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons256, cons147, cons41, cons87, cons88, cons335, cons342)
    def replacement393(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(393)
        return -Dist(n*(-b*e*g + c*d*g + c*e*f)/(c*e*(m - n + S(-1))), Int((d + e*x)**m*(f + g*x)**(n + S(-1))*(a + b*x + c*x**S(2))**p, x), x) - Simp(e*(d + e*x)**(m + S(-1))*(f + g*x)**n*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m - n + S(-1))), x)
    rule393 = ReplacementRule(pattern393, replacement393)
    pattern394 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons257, cons147, cons41, cons87, cons88, cons335, cons342)
    def replacement394(p, m, f, g, d, c, n, a, x, e):
        rubi.append(394)
        return -Dist(n*(d*g + e*f)/(e*(m - n + S(-1))), Int((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**(n + S(-1)), x), x) - Simp(e*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(f + g*x)**n/(c*(m - n + S(-1))), x)
    rule394 = ReplacementRule(pattern394, replacement394)
    pattern395 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons256, cons147, cons41, cons87, cons89, cons246)
    def replacement395(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(395)
        return -Dist(c*e*(m - n + S(-2))/((n + S(1))*(-b*e*g + c*d*g + c*e*f)), Int((d + e*x)**m*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**p, x), x) - Simp(e**S(2)*(d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/((n + S(1))*(-b*e*g + c*d*g + c*e*f)), x)
    rule395 = ReplacementRule(pattern395, replacement395)
    pattern396 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons257, cons147, cons41, cons87, cons89, cons246)
    def replacement396(p, m, f, g, d, c, n, a, x, e):
        rubi.append(396)
        return -Dist(e*(m - n + S(-2))/((n + S(1))*(d*g + e*f)), Int((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**(n + S(1)), x), x) - Simp(e**S(2)*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1))/((n + S(1))*(c*d*g + c*e*f)), x)
    rule396 = ReplacementRule(pattern396, replacement396)
    pattern397 = Pattern(Integral(sqrt(d_ + x_*WC('e', S(1)))/((x_*WC('g', S(1)) + WC('f', S(0)))*sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons256)
    def replacement397(f, b, g, d, a, c, x, e):
        rubi.append(397)
        return Dist(S(2)*e**S(2), Subst(Int(S(1)/(-b*e*g + c*(d*g + e*f) + e**S(2)*g*x**S(2)), x), x, sqrt(a + b*x + c*x**S(2))/sqrt(d + e*x)), x)
    rule397 = ReplacementRule(pattern397, replacement397)
    pattern398 = Pattern(Integral(sqrt(d_ + x_*WC('e', S(1)))/(sqrt(a_ + x_**S(2)*WC('c', S(1)))*(x_*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons257)
    def replacement398(f, g, d, c, a, x, e):
        rubi.append(398)
        return Dist(S(2)*e**S(2), Subst(Int(S(1)/(c*(d*g + e*f) + e**S(2)*g*x**S(2)), x), x, sqrt(a + c*x**S(2))/sqrt(d + e*x)), x)
    rule398 = ReplacementRule(pattern398, replacement398)
    pattern399 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons315, cons226, cons256, cons147, cons343, cons344, cons126)
    def replacement399(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(399)
        return Simp(e**S(2)*(d + e*x)**(m + S(-2))*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*g*(n + p + S(2))), x)
    rule399 = ReplacementRule(pattern399, replacement399)
    pattern400 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons315, cons257, cons147, cons343, cons345, cons126)
    def replacement400(p, m, f, g, d, c, n, a, x, e):
        rubi.append(400)
        return Simp(e**S(2)*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-2))*(f + g*x)**(n + S(1))/(c*g*(n + p + S(2))), x)
    rule400 = ReplacementRule(pattern400, replacement400)
    pattern401 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons256, cons147, cons343, cons87, cons89, cons246)
    def replacement401(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(401)
        return -Dist(e*(b*e*g*(n + S(1)) - c*d*g*(S(2)*n + p + S(3)) + c*e*f*(p + S(1)))/(g*(n + S(1))*(-b*e*g + c*d*g + c*e*f)), Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**p, x), x) + Simp(e**S(2)*(d + e*x)**(m + S(-2))*(f + g*x)**(n + S(1))*(-d*g + e*f)*(a + b*x + c*x**S(2))**(p + S(1))/(g*(n + S(1))*(-b*e*g + c*d*g + c*e*f)), x)
    rule401 = ReplacementRule(pattern401, replacement401)
    pattern402 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons257, cons147, cons343, cons87, cons89, cons246)
    def replacement402(p, m, f, g, d, c, n, a, x, e):
        rubi.append(402)
        return -Dist(e*(-d*g*(S(2)*n + p + S(3)) + e*f*(p + S(1)))/(g*(n + S(1))*(d*g + e*f)), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1)), x), x) + Simp(e**S(2)*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-2))*(f + g*x)**(n + S(1))*(-d*g + e*f)/(c*g*(n + S(1))*(d*g + e*f)), x)
    rule402 = ReplacementRule(pattern402, replacement402)
    pattern403 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons315, cons226, cons256, cons147, cons343, cons346, cons246)
    def replacement403(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(403)
        return -Dist((b*e*g*(n + S(1)) - c*d*g*(S(2)*n + p + S(3)) + c*e*f*(p + S(1)))/(c*g*(n + p + S(2))), Int((d + e*x)**(m + S(-1))*(f + g*x)**n*(a + b*x + c*x**S(2))**p, x), x) + Simp(e**S(2)*(d + e*x)**(m + S(-2))*(f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*g*(n + p + S(2))), x)
    rule403 = ReplacementRule(pattern403, replacement403)
    pattern404 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons315, cons257, cons147, cons343, cons346, cons246)
    def replacement404(p, m, f, g, d, c, n, a, x, e):
        rubi.append(404)
        return -Dist((-d*g*(S(2)*n + p + S(3)) + e*f*(p + S(1)))/(g*(n + p + S(2))), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(-1))*(f + g*x)**n, x), x) + Simp(e**S(2)*(a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-2))*(f + g*x)**(n + S(1))/(c*g*(n + p + S(2))), x)
    rule404 = ReplacementRule(pattern404, replacement404)
    pattern405 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons315, cons226, cons256, cons147, cons207)
    def replacement405(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(405)
        return Int(ExpandIntegrand((d + e*x)**m*(f + g*x)**n*(a + b*x + c*x**S(2))**p, x), x)
    rule405 = ReplacementRule(pattern405, replacement405)
    pattern406 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons315, cons257, cons347, cons150, cons348, cons349)
    def replacement406(p, m, f, g, d, c, n, a, x, e):
        rubi.append(406)
        return Int(ExpandIntegrand(S(1)/sqrt(a + c*x**S(2)), (a + c*x**S(2))**(p + S(1)/2)*(d + e*x)**m*(f + g*x)**n, x), x)
    rule406 = ReplacementRule(pattern406, replacement406)
    pattern407 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons315, cons257, cons147, cons207)
    def replacement407(p, m, f, g, d, c, n, a, x, e):
        rubi.append(407)
        return Int(ExpandIntegrand((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**n, x), x)
    rule407 = ReplacementRule(pattern407, replacement407)
    pattern408 = Pattern(Integral(x_**S(2)*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_/(d_ + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons5, cons226, cons256)
    def replacement408(p, b, d, c, a, x, e):
        rubi.append(408)
        return -Dist(e**(S(-2)), Int((d - e*x)*(a + b*x + c*x**S(2))**p, x), x) + Dist(d**S(2)/e**S(2), Int((a + b*x + c*x**S(2))**p/(d + e*x), x), x)
    rule408 = ReplacementRule(pattern408, replacement408)
    pattern409 = Pattern(Integral(x_**S(2)*(a_ + x_**S(2)*WC('c', S(1)))**p_/(d_ + x_*WC('e', S(1))), x_), cons2, cons7, cons27, cons48, cons5, cons257)
    def replacement409(p, d, c, a, x, e):
        rubi.append(409)
        return -Dist(e**(S(-2)), Int((a + c*x**S(2))**p*(d - e*x), x), x) + Dist(d**S(2)/e**S(2), Int((a + c*x**S(2))**p/(d + e*x), x), x)
    rule409 = ReplacementRule(pattern409, replacement409)
    pattern410 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**S(2)*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons256, cons147, cons270)
    def replacement410(p, m, f, b, g, d, a, c, x, e):
        rubi.append(410)
        return -Dist(S(1)/(c*e**S(2)*(m + S(2)*p + S(3))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**p*Simp(b*e*g*(d*g + e*f*(m + p + S(1))) - c*(d**S(2)*g**S(2) + d*e*f*g*m + e**S(2)*f**S(2)*(m + S(2)*p + S(3))) + e*g*x*(b*e*g*(m + p + S(2)) - c*(d*g*m + e*f*(m + S(2)*p + S(4)))), x), x), x) + Simp(g*(d + e*x)**m*(f + g*x)*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m + S(2)*p + S(3))), x)
    rule410 = ReplacementRule(pattern410, replacement410)
    pattern411 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**S(2), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons257, cons147, cons270)
    def replacement411(p, m, f, g, d, c, a, x, e):
        rubi.append(411)
        return -Dist(S(1)/(c*e**S(2)*(m + S(2)*p + S(3))), Int((a + c*x**S(2))**p*(d + e*x)**m*Simp(-c*e*g*x*(d*g*m + e*f*(m + S(2)*p + S(4))) - c*(d**S(2)*g**S(2) + d*e*f*g*m + e**S(2)*f**S(2)*(m + S(2)*p + S(3))), x), x), x) + Simp(g*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m*(f + g*x)/(c*(m + S(2)*p + S(3))), x)
    rule411 = ReplacementRule(pattern411, replacement411)
    pattern412 = Pattern(Integral((x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons3, cons7, cons48, cons125, cons208, cons21, cons4, cons147)
    def replacement412(p, m, f, b, g, c, n, x, e):
        rubi.append(412)
        return Dist(x**(-m - p)*(e*x)**m*(b + c*x)**(-p)*(b*x + c*x**S(2))**p, Int(x**(m + p)*(b + c*x)**p*(f + g*x)**n, x), x)
    rule412 = ReplacementRule(pattern412, replacement412)
    pattern413 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons315, cons257, cons147, cons43, cons268)
    def replacement413(p, m, f, g, d, c, n, a, x, e):
        rubi.append(413)
        return Int((d + e*x)**(m + p)*(f + g*x)**n*(a/d + c*x/e)**p, x)
    rule413 = ReplacementRule(pattern413, replacement413)
    pattern414 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons315, cons226, cons256, cons147)
    def replacement414(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(414)
        return Dist((d + e*x)**(-FracPart(p))*(a/d + c*x/e)**(-FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((d + e*x)**(m + p)*(f + g*x)**n*(a/d + c*x/e)**p, x), x)
    rule414 = ReplacementRule(pattern414, replacement414)
    pattern415 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(d_ + x_*WC('e', S(1)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons315, cons257, cons147)
    def replacement415(p, m, f, g, d, c, n, a, x, e):
        rubi.append(415)
        return Dist((a + c*x**S(2))**FracPart(p)*(d + e*x)**(-FracPart(p))*(a/d + c*x/e)**(-FracPart(p)), Int((d + e*x)**(m + p)*(f + g*x)**n*(a/d + c*x/e)**p, x), x)
    rule415 = ReplacementRule(pattern415, replacement415)
    pattern416 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons226, cons279, cons128)
    def replacement416(p, m, f, g, b, d, a, c, x, e):
        rubi.append(416)
        return Int(ExpandIntegrand((d + e*x)**m*(f + g*x)*(a + b*x + c*x**S(2))**p, x), x)
    rule416 = ReplacementRule(pattern416, replacement416)
    pattern417 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons280, cons128)
    def replacement417(p, m, f, g, d, c, a, x, e):
        rubi.append(417)
        return Int(ExpandIntegrand((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x), x), x)
    rule417 = ReplacementRule(pattern417, replacement417)
    pattern418 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))/((x_*WC('e', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279)
    def replacement418(f, g, b, d, a, c, x, e):
        rubi.append(418)
        return Dist(e*(-d*g + e*f)/(a*e**S(2) - b*d*e + c*d**S(2)), Int(S(1)/(d + e*x), x), x) + Dist(S(1)/(a*e**S(2) - b*d*e + c*d**S(2)), Int(Simp(a*e*g - b*e*f + c*d*f - c*x*(-d*g + e*f), x)/(a + b*x + c*x**S(2)), x), x)
    rule418 = ReplacementRule(pattern418, replacement418)
    pattern419 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))/((a_ + x_**S(2)*WC('c', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280)
    def replacement419(f, g, d, c, a, x, e):
        rubi.append(419)
        return Dist(e*(-d*g + e*f)/(a*e**S(2) + c*d**S(2)), Int(S(1)/(d + e*x), x), x) + Dist(S(1)/(a*e**S(2) + c*d**S(2)), Int(Simp(a*e*g + c*d*f - c*x*(-d*g + e*f), x)/(a + c*x**S(2)), x), x)
    rule419 = ReplacementRule(pattern419, replacement419)
    pattern420 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons279, cons242, cons350)
    def replacement420(p, m, f, g, b, d, a, c, x, e):
        rubi.append(420)
        return -Simp((d + e*x)**(m + S(1))*(-d*g + e*f)*(a + b*x + c*x**S(2))**(p + S(1))/(S(2)*(p + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule420 = ReplacementRule(pattern420, replacement420)
    pattern421 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons280, cons242, cons351)
    def replacement421(p, m, f, g, d, c, a, x, e):
        rubi.append(421)
        return -Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(1))*(-d*g + e*f)/(S(2)*(p + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule421 = ReplacementRule(pattern421, replacement421)
    pattern422 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons242, cons13, cons137, cons352)
    def replacement422(p, m, f, g, b, d, a, c, x, e):
        rubi.append(422)
        return -Dist(m*(-S(2)*a*e*g + b*(d*g + e*f) - S(2)*c*d*f)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1)), x), x) + Simp((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))*(-S(2)*a*g + b*f + x*(-b*g + S(2)*c*f))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule422 = ReplacementRule(pattern422, replacement422)
    pattern423 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons242, cons13, cons137, cons353)
    def replacement423(p, m, f, g, d, c, a, x, e):
        rubi.append(423)
        return -Dist(m*(a*e*g + c*d*f)/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1)), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**m*(a*g - c*f*x)/(S(2)*a*c*(p + S(1))), x)
    rule423 = ReplacementRule(pattern423, replacement423)
    pattern424 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons279, cons242)
    def replacement424(p, m, f, g, b, d, a, c, x, e):
        rubi.append(424)
        return -Dist((-S(2)*a*e*g + b*(d*g + e*f) - S(2)*c*d*f)/(S(2)*a*e**S(2) - S(2)*b*d*e + S(2)*c*d**S(2)), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) - Simp((d + e*x)**(m + S(1))*(-d*g + e*f)*(a + b*x + c*x**S(2))**(p + S(1))/(S(2)*(p + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule424 = ReplacementRule(pattern424, replacement424)
    pattern425 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons280, cons242)
    def replacement425(p, m, f, g, d, c, a, x, e):
        rubi.append(425)
        return Dist((a*e*g + c*d*f)/(a*e**S(2) + c*d**S(2)), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1)), x), x) - Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(1))*(-d*g + e*f)/(S(2)*(p + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule425 = ReplacementRule(pattern425, replacement425)
    pattern426 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons226, cons279, cons354)
    def replacement426(p, f, g, b, d, a, c, x, e):
        rubi.append(426)
        return -Simp((a + b*x + c*x**S(2))**(p + S(1))*(b*e*g*(p + S(2)) - S(2)*c*e*g*x*(p + S(1)) - c*(S(2)*p + S(3))*(d*g + e*f))/(S(2)*c**S(2)*(p + S(1))*(S(2)*p + S(3))), x)
    rule426 = ReplacementRule(pattern426, replacement426)
    pattern427 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('e', S(1)) + WC('d', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons280, cons355)
    def replacement427(p, f, g, d, c, a, x, e):
        rubi.append(427)
        return Simp((a + c*x**S(2))**(p + S(1))*(S(2)*e*g*x*(p + S(1)) + (S(2)*p + S(3))*(d*g + e*f))/(S(2)*c*(p + S(1))*(S(2)*p + S(3))), x)
    rule427 = ReplacementRule(pattern427, replacement427)
    pattern428 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons13, cons137)
    def replacement428(p, f, g, b, d, a, c, x, e):
        rubi.append(428)
        return -Dist((-S(2)*a*c*e*g + b**S(2)*e*g*(p + S(2)) + c*(S(2)*p + S(3))*(-b*(d*g + e*f) + S(2)*c*d*f))/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1)), x), x) - Simp((a + b*x + c*x**S(2))**(p + S(1))*(S(2)*a*c*(d*g + e*f) - b*(a*e*g + c*d*f) - x*(b**S(2)*e*g - b*c*(d*g + e*f) + S(2)*c*(-a*e*g + c*d*f)))/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule428 = ReplacementRule(pattern428, replacement428)
    pattern429 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('e', S(1)) + WC('d', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons13, cons137)
    def replacement429(p, f, g, d, c, a, x, e):
        rubi.append(429)
        return -Dist((a*e*g - c*d*f*(S(2)*p + S(3)))/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1)), x), x) - Simp((a + c*x**S(2))**(p + S(1))*(-a*(d*g + e*(f + g*x)) + c*d*f*x)/(S(2)*a*c*(p + S(1))), x)
    rule429 = ReplacementRule(pattern429, replacement429)
    pattern430 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons226, cons279, cons287)
    def replacement430(p, f, g, b, d, a, c, x, e):
        rubi.append(430)
        return Dist((-S(2)*a*c*e*g + b**S(2)*e*g*(p + S(2)) + c*(S(2)*p + S(3))*(-b*(d*g + e*f) + S(2)*c*d*f))/(S(2)*c**S(2)*(S(2)*p + S(3))), Int((a + b*x + c*x**S(2))**p, x), x) - Simp((a + b*x + c*x**S(2))**(p + S(1))*(b*e*g*(p + S(2)) - S(2)*c*e*g*x*(p + S(1)) - c*(S(2)*p + S(3))*(d*g + e*f))/(S(2)*c**S(2)*(p + S(1))*(S(2)*p + S(3))), x)
    rule430 = ReplacementRule(pattern430, replacement430)
    pattern431 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('e', S(1)) + WC('d', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons280, cons287)
    def replacement431(p, f, g, d, c, a, x, e):
        rubi.append(431)
        return -Dist((a*e*g - c*d*f*(S(2)*p + S(3)))/(c*(S(2)*p + S(3))), Int((a + c*x**S(2))**p, x), x) + Simp((a + c*x**S(2))**(p + S(1))*(S(2)*e*g*x*(p + S(1)) + (S(2)*p + S(3))*(d*g + e*f))/(S(2)*c*(p + S(1))*(S(2)*p + S(3))), x)
    rule431 = ReplacementRule(pattern431, replacement431)
    pattern432 = Pattern(Integral((x_*WC('e', S(1)))**m_*(a_ + x_**S(2)*WC('c', S(1)))**p_*(f_ + x_*WC('g', S(1))), x_), cons2, cons7, cons48, cons125, cons208, cons5, cons356, cons357)
    def replacement432(p, m, g, f, c, a, x, e):
        rubi.append(432)
        return Dist(f, Int((e*x)**m*(a + c*x**S(2))**p, x), x) + Dist(g/e, Int((e*x)**(m + S(1))*(a + c*x**S(2))**p, x), x)
    rule432 = ReplacementRule(pattern432, replacement432)
    pattern433 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons358, cons288, cons289)
    def replacement433(p, m, f, b, g, d, c, a, x, e):
        rubi.append(433)
        return Dist((d + e*x)**FracPart(p)*(a*d + c*e*x**S(3))**(-FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((f + g*x)*(a*d + c*e*x**S(3))**p, x), x)
    rule433 = ReplacementRule(pattern433, replacement433)
    pattern434 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons244, cons163, cons247, cons359, cons360)
    def replacement434(p, m, f, g, b, d, a, c, x, e):
        rubi.append(434)
        return -Dist(p/(e**S(2)*(m + S(1))*(m + S(2))*(a*e**S(2) - b*d*e + c*d**S(2))), Int((d + e*x)**(m + S(2))*(a + b*x + c*x**S(2))**(p + S(-1))*Simp(S(2)*a*c*e*(m + S(2))*(-d*g + e*f) + b**S(2)*e*(d*g*(p + S(1)) - e*f*(m + p + S(2))) + b*(a*e**S(2)*g*(m + S(1)) - c*d*(d*g*(S(2)*p + S(1)) - e*f*(m + S(2)*p + S(2)))) - c*x*(S(2)*c*d*(d*g*(S(2)*p + S(1)) - e*f*(m + S(2)*p + S(2))) - e*(S(2)*a*e*g*(m + S(1)) - b*(d*g*(m - S(2)*p) + e*f*(m + S(2)*p + S(2))))), x), x), x) - Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*(-d*p*(-b*e + S(2)*c*d)*(-d*g + e*f) - e*x*(g*(m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2)) + p*(-b*e + S(2)*c*d)*(-d*g + e*f)) + (d*g - e*f*(m + S(2)))*(a*e**S(2) - b*d*e + c*d**S(2)))/(e**S(2)*(m + S(1))*(m + S(2))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule434 = ReplacementRule(pattern434, replacement434)
    pattern435 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons244, cons163, cons247, cons359, cons360)
    def replacement435(p, m, f, g, d, c, a, x, e):
        rubi.append(435)
        return -Dist(p/(e**S(2)*(m + S(1))*(m + S(2))*(a*e**S(2) + c*d**S(2))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x)**(m + S(2))*Simp(S(2)*a*c*e*(m + S(2))*(-d*g + e*f) - c*x*(-S(2)*a*e**S(2)*g*(m + S(1)) + S(2)*c*d*(d*g*(S(2)*p + S(1)) - e*f*(m + S(2)*p + S(2)))), x), x), x) - Simp((a + c*x**S(2))**p*(d + e*x)**(m + S(1))*(-S(2)*c*d**S(2)*p*(-d*g + e*f) - e*x*(S(2)*c*d*p*(-d*g + e*f) + g*(m + S(1))*(a*e**S(2) + c*d**S(2))) + (a*e**S(2) + c*d**S(2))*(d*g - e*f*(m + S(2))))/(e**S(2)*(m + S(1))*(m + S(2))*(a*e**S(2) + c*d**S(2))), x)
    rule435 = ReplacementRule(pattern435, replacement435)
    pattern436 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons226, cons279, cons13, cons163, cons361, cons66, cons299, cons362)
    def replacement436(p, m, f, g, b, d, a, c, x, e):
        rubi.append(436)
        return Dist(p/(e**S(2)*(m + S(1))*(m + S(2)*p + S(2))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(-1))*Simp(-b*e*f*(m + S(2)*p + S(2)) + g*(S(2)*a*e*m + S(2)*a*e + S(2)*b*d*p + b*d) + x*(-S(2)*c*e*f*(m + S(2)*p + S(2)) + g*(b*e*m + b*e + S(4)*c*d*p + S(2)*c*d)), x), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*(-d*g*(S(2)*p + S(1)) + e*f*(m + S(2)*p + S(2)) + e*g*x*(m + S(1)))/(e**S(2)*(m + S(1))*(m + S(2)*p + S(2))), x)
    rule436 = ReplacementRule(pattern436, replacement436)
    pattern437 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons280, cons13, cons163, cons361, cons66, cons299, cons362)
    def replacement437(p, m, f, g, d, c, a, x, e):
        rubi.append(437)
        return Dist(p/(e**S(2)*(m + S(1))*(m + S(2)*p + S(2))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x)**(m + S(1))*Simp(g*(S(2)*a*e*m + S(2)*a*e) + x*(-S(2)*c*e*f*(m + S(2)*p + S(2)) + g*(S(4)*c*d*p + S(2)*c*d)), x), x), x) + Simp((a + c*x**S(2))**p*(d + e*x)**(m + S(1))*(-d*g*(S(2)*p + S(1)) + e*f*(m + S(2)*p + S(2)) + e*g*x*(m + S(1)))/(e**S(2)*(m + S(1))*(m + S(2)*p + S(2))), x)
    rule437 = ReplacementRule(pattern437, replacement437)
    pattern438 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons226, cons279, cons13, cons163, cons363, cons303, cons362)
    def replacement438(p, m, f, g, b, d, a, c, x, e):
        rubi.append(438)
        return -Dist(p/(c*e**S(2)*(m + S(2)*p + S(1))*(m + S(2)*p + S(2))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(-1))*Simp(c*e*f*(-S(2)*a*e + b*d)*(m + S(2)*p + S(2)) + g*(a*e*(b*e*m + b*e - S(2)*c*d*m) + b*d*(b*e*p - S(2)*c*d*p - c*d)) + x*(c*e*f*(-b*e + S(2)*c*d)*(m + S(2)*p + S(2)) + g*(b**S(2)*e**S(2)*(m + p + S(1)) - S(2)*c**S(2)*d**S(2)*(S(2)*p + S(1)) - c*e*(S(2)*a*e*(m + S(2)*p + S(1)) + b*d*(m - S(2)*p)))), x), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*(c*e*f*(m + S(2)*p + S(2)) + c*e*g*x*(m + S(2)*p + S(1)) - g*(-b*e*p + S(2)*c*d*p + c*d))/(c*e**S(2)*(m + S(2)*p + S(1))*(m + S(2)*p + S(2))), x)
    rule438 = ReplacementRule(pattern438, replacement438)
    pattern439 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons280, cons13, cons163, cons363, cons303, cons362)
    def replacement439(p, m, f, g, d, c, a, x, e):
        rubi.append(439)
        return Dist(S(2)*p/(c*e**S(2)*(m + S(2)*p + S(1))*(m + S(2)*p + S(2))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x)**m*Simp(a*c*d*e*g*m + a*c*e**S(2)*f*(m + S(2)*p + S(2)) - x*(c**S(2)*d*e*f*(m + S(2)*p + S(2)) - g*(a*c*e**S(2)*(m + S(2)*p + S(1)) + c**S(2)*d**S(2)*(S(2)*p + S(1)))), x), x), x) + Simp((a + c*x**S(2))**p*(d + e*x)**(m + S(1))*(-c*d*g*(S(2)*p + S(1)) + c*e*f*(m + S(2)*p + S(2)) + c*e*g*x*(m + S(2)*p + S(1)))/(c*e**S(2)*(m + S(2)*p + S(1))*(m + S(2)*p + S(2))), x)
    rule439 = ReplacementRule(pattern439, replacement439)
    pattern440 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons244, cons137, cons166, cons364)
    def replacement440(p, m, f, g, b, d, a, c, x, e):
        rubi.append(440)
        return -Dist(S(1)/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**(m + S(-2))*(a + b*x + c*x**S(2))**(p + S(1))*Simp(b*e*g*(a*e*(m + S(-1)) + b*d*(p + S(2))) + S(2)*c**S(2)*d**S(2)*f*(S(2)*p + S(3)) - c*(S(2)*a*e*(d*g*m + e*f*(m + S(-1))) + b*d*(d*g*(S(2)*p + S(3)) - e*f*(m - S(2)*p + S(-4)))) + e*x*(b**S(2)*e*g*(m + p + S(1)) + S(2)*c**S(2)*d*f*(m + S(2)*p + S(2)) - c*(S(2)*a*e*g*m + b*(d*g + e*f)*(m + S(2)*p + S(2)))), x), x), x) - Simp((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*(S(2)*a*c*(d*g + e*f) - b*(a*e*g + c*d*f) - x*(b**S(2)*e*g + S(2)*c**S(2)*d*f - c*(S(2)*a*e*g + b*d*g + b*e*f)))/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule440 = ReplacementRule(pattern440, replacement440)
    pattern441 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons244, cons137, cons166, cons365)
    def replacement441(p, m, f, g, d, c, a, x, e):
        rubi.append(441)
        return -Dist(S(1)/(S(4)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-2))*Simp(S(2)*a*e*(d*g*m + e*f*(m + S(-1))) - S(2)*c*d**S(2)*f*(S(2)*p + S(3)) + e*x*(S(2)*a*e*g*m - S(2)*c*d*f*(m + S(2)*p + S(2))), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*(S(2)*a*(d*g + e*f) - x*(-S(2)*a*e*g + S(2)*c*d*f))/(S(4)*a*c*(p + S(1))), x)
    rule441 = ReplacementRule(pattern441, replacement441)
    pattern442 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons244, cons137, cons168, cons366, cons362)
    def replacement442(p, m, f, g, b, d, a, c, x, e):
        rubi.append(442)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*Simp(-e*x*(-b*g + S(2)*c*f)*(m + S(2)*p + S(3)) - f*(b*e*m + S(2)*c*d*(S(2)*p + S(3))) + g*(S(2)*a*e*m + b*d*(S(2)*p + S(3))), x), x), x) + Simp((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))*(-S(2)*a*g + b*f + x*(-b*g + S(2)*c*f))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule442 = ReplacementRule(pattern442, replacement442)
    pattern443 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons244, cons137, cons168, cons366, cons362)
    def replacement443(p, m, f, g, d, c, a, x, e):
        rubi.append(443)
        return -Dist(S(1)/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(-1))*Simp(a*e*g*m - c*d*f*(S(2)*p + S(3)) - c*e*f*x*(m + S(2)*p + S(3)), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**m*(a*g - c*f*x)/(S(2)*a*c*(p + S(1))), x)
    rule443 = ReplacementRule(pattern443, replacement443)
    pattern444 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons226, cons279, cons13, cons137, cons362)
    def replacement444(p, m, f, g, b, d, a, c, x, e):
        rubi.append(444)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(a*e**S(2) - b*d*e + c*d**S(2))), Int((d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))*Simp(c*e*x*(-f*(-b*e + S(2)*c*d) + g*(-S(2)*a*e + b*d))*(m + S(2)*p + S(4)) + f*(-S(2)*a*c*e**S(2)*(m + S(2)*p + S(3)) + b**S(2)*e**S(2)*(m + p + S(2)) + b*c*d*e*(-m + S(2)*p + S(2)) - S(2)*c**S(2)*d**S(2)*(S(2)*p + S(3))) - g*(a*e*(b*e*m + b*e - S(2)*c*d*m) - b*d*(-b*e*p - b*e + S(2)*c*d*p + S(3)*c*d)), x), x), x) + Simp((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(-a*g*(-b*e + S(2)*c*d) + c*x*(f*(-b*e + S(2)*c*d) - g*(-S(2)*a*e + b*d)) + f*(S(2)*a*c*e - b**S(2)*e + b*c*d))/((p + S(1))*(-S(4)*a*c + b**S(2))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule444 = ReplacementRule(pattern444, replacement444)
    pattern445 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons13, cons137, cons362)
    def replacement445(p, m, f, g, d, c, a, x, e):
        rubi.append(445)
        return Dist(S(1)/(S(2)*a*c*(p + S(1))*(a*e**S(2) + c*d**S(2))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x)**m*Simp(-a*c*d*e*g*m + c*e*x*(a*e*g + c*d*f)*(m + S(2)*p + S(4)) + f*(a*c*e**S(2)*(m + S(2)*p + S(3)) + c**S(2)*d**S(2)*(S(2)*p + S(3))), x), x), x) - Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(1))*(-a*c*d*g + a*c*e*f + c*x*(a*e*g + c*d*f))/(S(2)*a*c*(p + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule445 = ReplacementRule(pattern445, replacement445)
    pattern446 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons17)
    def replacement446(m, f, g, b, d, a, c, x, e):
        rubi.append(446)
        return Int(ExpandIntegrand((d + e*x)**m*(f + g*x)/(a + b*x + c*x**S(2)), x), x)
    rule446 = ReplacementRule(pattern446, replacement446)
    pattern447 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons17)
    def replacement447(m, f, g, d, c, a, x, e):
        rubi.append(447)
        return Int(ExpandIntegrand((d + e*x)**m*(f + g*x)/(a + c*x**S(2)), x), x)
    rule447 = ReplacementRule(pattern447, replacement447)
    pattern448 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons367, cons168)
    def replacement448(m, f, g, b, d, a, c, x, e):
        rubi.append(448)
        return Dist(S(1)/c, Int((d + e*x)**(m + S(-1))*Simp(-a*e*g + c*d*f + x*(-b*e*g + c*d*g + c*e*f), x)/(a + b*x + c*x**S(2)), x), x) + Simp(g*(d + e*x)**m/(c*m), x)
    rule448 = ReplacementRule(pattern448, replacement448)
    pattern449 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons367, cons168)
    def replacement449(m, f, g, d, c, a, x, e):
        rubi.append(449)
        return Dist(S(1)/c, Int((d + e*x)**(m + S(-1))*Simp(-a*e*g + c*d*f + x*(c*d*g + c*e*f), x)/(a + c*x**S(2)), x), x) + Simp(g*(d + e*x)**m/(c*m), x)
    rule449 = ReplacementRule(pattern449, replacement449)
    pattern450 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))/(sqrt(x_*WC('e', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279)
    def replacement450(f, g, b, d, a, c, x, e):
        rubi.append(450)
        return Dist(S(2), Subst(Int((-d*g + e*f + g*x**S(2))/(a*e**S(2) - b*d*e + c*d**S(2) + c*x**S(4) - x**S(2)*(-b*e + S(2)*c*d)), x), x, sqrt(d + e*x)), x)
    rule450 = ReplacementRule(pattern450, replacement450)
    pattern451 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280)
    def replacement451(f, g, d, c, a, x, e):
        rubi.append(451)
        return Dist(S(2), Subst(Int((-d*g + e*f + g*x**S(2))/(a*e**S(2) + c*d**S(2) - S(2)*c*d*x**S(2) + c*x**S(4)), x), x, sqrt(d + e*x)), x)
    rule451 = ReplacementRule(pattern451, replacement451)
    pattern452 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons226, cons279, cons367, cons94)
    def replacement452(m, f, g, b, d, a, c, x, e):
        rubi.append(452)
        return Dist(S(1)/(a*e**S(2) - b*d*e + c*d**S(2)), Int((d + e*x)**(m + S(1))*Simp(a*e*g - b*e*f + c*d*f - c*x*(-d*g + e*f), x)/(a + b*x + c*x**S(2)), x), x) + Simp((d + e*x)**(m + S(1))*(-d*g + e*f)/((m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule452 = ReplacementRule(pattern452, replacement452)
    pattern453 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons315, cons280, cons367, cons94)
    def replacement453(m, f, g, d, c, a, x, e):
        rubi.append(453)
        return Dist(S(1)/(a*e**S(2) + c*d**S(2)), Int((d + e*x)**(m + S(1))*Simp(a*e*g + c*d*f - c*x*(-d*g + e*f), x)/(a + c*x**S(2)), x), x) + Simp((d + e*x)**(m + S(1))*(-d*g + e*f)/((m + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule453 = ReplacementRule(pattern453, replacement453)
    pattern454 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons356)
    def replacement454(m, f, g, b, d, a, c, x, e):
        rubi.append(454)
        return Int(ExpandIntegrand((d + e*x)**m, (f + g*x)/(a + b*x + c*x**S(2)), x), x)
    rule454 = ReplacementRule(pattern454, replacement454)
    pattern455 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons356)
    def replacement455(m, f, g, d, c, a, x, e):
        rubi.append(455)
        return Int(ExpandIntegrand((d + e*x)**m, (f + g*x)/(a + c*x**S(2)), x), x)
    rule455 = ReplacementRule(pattern455, replacement455)
    pattern456 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons226, cons279, cons31, cons168, cons319, cons368, cons362)
    def replacement456(p, m, f, g, b, d, a, c, x, e):
        rubi.append(456)
        return Dist(S(1)/(c*(m + S(2)*p + S(2))), Int((d + e*x)**(m + S(-1))*(a + b*x + c*x**S(2))**p*Simp(d*(p + S(1))*(-b*g + S(2)*c*f) + m*(-a*e*g + c*d*f) + x*(e*(p + S(1))*(-b*g + S(2)*c*f) + m*(-b*e*g + c*d*g + c*e*f)), x), x), x) + Simp(g*(d + e*x)**m*(a + b*x + c*x**S(2))**(p + S(1))/(c*(m + S(2)*p + S(2))), x)
    rule456 = ReplacementRule(pattern456, replacement456)
    pattern457 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons280, cons31, cons168, cons319, cons368, cons362)
    def replacement457(p, m, f, g, d, c, a, x, e):
        rubi.append(457)
        return Dist(S(1)/(c*(m + S(2)*p + S(2))), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(-1))*Simp(-a*e*g*m + c*d*f*(m + S(2)*p + S(2)) + c*x*(d*g*m + e*f*(m + S(2)*p + S(2))), x), x), x) + Simp(g*(a + c*x**S(2))**(p + S(1))*(d + e*x)**m/(c*(m + S(2)*p + S(2))), x)
    rule457 = ReplacementRule(pattern457, replacement457)
    pattern458 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons226, cons279, cons31, cons94, cons362)
    def replacement458(p, m, f, g, b, d, a, c, x, e):
        rubi.append(458)
        return Dist(S(1)/((m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*Simp(b*(p + S(1))*(d*g - e*f) - c*x*(-d*g + e*f)*(m + S(2)*p + S(3)) + (m + S(1))*(a*e*g - b*e*f + c*d*f), x), x), x) + Simp((d + e*x)**(m + S(1))*(-d*g + e*f)*(a + b*x + c*x**S(2))**(p + S(1))/((m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule458 = ReplacementRule(pattern458, replacement458)
    pattern459 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons5, cons315, cons280, cons31, cons94, cons362)
    def replacement459(p, m, f, g, d, c, a, x, e):
        rubi.append(459)
        return Dist(S(1)/((m + S(1))*(a*e**S(2) + c*d**S(2))), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1))*Simp(-c*x*(-d*g + e*f)*(m + S(2)*p + S(3)) + (m + S(1))*(a*e*g + c*d*f), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(1))*(-d*g + e*f)/((m + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule459 = ReplacementRule(pattern459, replacement459)
    pattern460 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons279, cons369, cons66)
    def replacement460(p, m, f, g, b, d, a, c, x, e):
        rubi.append(460)
        return Dist(S(1)/((m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*Simp(b*(p + S(1))*(d*g - e*f) - c*x*(-d*g + e*f)*(m + S(2)*p + S(3)) + (m + S(1))*(a*e*g - b*e*f + c*d*f), x), x), x) + Simp((d + e*x)**(m + S(1))*(-d*g + e*f)*(a + b*x + c*x**S(2))**(p + S(1))/((m + S(1))*(a*e**S(2) - b*d*e + c*d**S(2))), x)
    rule460 = ReplacementRule(pattern460, replacement460)
    pattern461 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons280, cons369, cons66)
    def replacement461(p, m, f, g, d, c, a, x, e):
        rubi.append(461)
        return Dist(S(1)/((m + S(1))*(a*e**S(2) + c*d**S(2))), Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1))*Simp(-c*x*(-d*g + e*f)*(m + S(2)*p + S(3)) + (m + S(1))*(a*e*g + c*d*f), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(d + e*x)**(m + S(1))*(-d*g + e*f)/((m + S(1))*(a*e**S(2) + c*d**S(2))), x)
    rule461 = ReplacementRule(pattern461, replacement461)
    pattern462 = Pattern(Integral((f_ + x_*WC('g', S(1)))/((x_*WC('e', S(1)) + WC('d', S(0)))*sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons370, cons371, cons372)
    def replacement462(g, b, f, d, a, c, x, e):
        rubi.append(462)
        return Dist(S(4)*f*(a - d)/(-a*e + b*d), Subst(Int(S(1)/(S(4)*a - S(4)*d - x**S(2)), x), x, (S(2)*a - S(2)*d + x*(b - e))/sqrt(a + b*x + c*x**S(2))), x)
    rule462 = ReplacementRule(pattern462, replacement462)
    pattern463 = Pattern(Integral((f_ + x_*WC('g', S(1)))/(sqrt(x_)*sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons125, cons208, cons226)
    def replacement463(f, g, b, c, a, x):
        rubi.append(463)
        return Dist(S(2), Subst(Int((f + g*x**S(2))/sqrt(a + b*x**S(2) + c*x**S(4)), x), x, sqrt(x)), x)
    rule463 = ReplacementRule(pattern463, replacement463)
    pattern464 = Pattern(Integral((f_ + x_*WC('g', S(1)))/(sqrt(x_)*sqrt(a_ + x_**S(2)*WC('c', S(1)))), x_), cons2, cons7, cons125, cons208, cons373)
    def replacement464(f, g, c, a, x):
        rubi.append(464)
        return Dist(S(2), Subst(Int((f + g*x**S(2))/sqrt(a + c*x**S(4)), x), x, sqrt(x)), x)
    rule464 = ReplacementRule(pattern464, replacement464)
    pattern465 = Pattern(Integral((f_ + x_*WC('g', S(1)))/(sqrt(e_*x_)*sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons48, cons125, cons208, cons226)
    def replacement465(g, b, f, c, a, x, e):
        rubi.append(465)
        return Dist(sqrt(x)/sqrt(e*x), Int((f + g*x)/(sqrt(x)*sqrt(a + b*x + c*x**S(2))), x), x)
    rule465 = ReplacementRule(pattern465, replacement465)
    pattern466 = Pattern(Integral((f_ + x_*WC('g', S(1)))/(sqrt(e_*x_)*sqrt(a_ + x_**S(2)*WC('c', S(1)))), x_), cons2, cons7, cons48, cons125, cons208, cons374)
    def replacement466(f, g, c, a, x, e):
        rubi.append(466)
        return Dist(sqrt(x)/sqrt(e*x), Int((f + g*x)/(sqrt(x)*sqrt(a + c*x**S(2))), x), x)
    rule466 = ReplacementRule(pattern466, replacement466)
    pattern467 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons279)
    def replacement467(p, m, f, g, b, d, a, c, x, e):
        rubi.append(467)
        return Dist(g/e, Int((d + e*x)**(m + S(1))*(a + b*x + c*x**S(2))**p, x), x) + Dist((-d*g + e*f)/e, Int((d + e*x)**m*(a + b*x + c*x**S(2))**p, x), x)
    rule467 = ReplacementRule(pattern467, replacement467)
    pattern468 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons280)
    def replacement468(p, m, f, g, d, c, a, x, e):
        rubi.append(468)
        return Dist(g/e, Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1)), x), x) + Dist((-d*g + e*f)/e, Int((a + c*x**S(2))**p*(d + e*x)**m, x), x)
    rule468 = ReplacementRule(pattern468, replacement468)
    pattern469 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons226, cons279, cons375)
    def replacement469(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(469)
        return Int(ExpandIntegrand((d + e*x)**m*(f + g*x)**n*(a + b*x + c*x**S(2))**p, x), x)
    rule469 = ReplacementRule(pattern469, replacement469)
    pattern470 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons280, cons375)
    def replacement470(p, m, f, g, d, c, n, a, x, e):
        rubi.append(470)
        return Int(ExpandIntegrand((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**n, x), x)
    rule470 = ReplacementRule(pattern470, replacement470)
    pattern471 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_/((x_*WC('e', S(1)) + WC('d', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons149, cons163)
    def replacement471(p, f, g, b, d, a, c, x, e):
        rubi.append(471)
        return -Dist(S(1)/(e*(-d*g + e*f)), Int((a + b*x + c*x**S(2))**(p + S(-1))*Simp(a*e*g - b*e*f + c*d*f - c*x*(-d*g + e*f), x)/(f + g*x), x), x) + Dist((a*e**S(2) - b*d*e + c*d**S(2))/(e*(-d*g + e*f)), Int((a + b*x + c*x**S(2))**(p + S(-1))/(d + e*x), x), x)
    rule471 = ReplacementRule(pattern471, replacement471)
    pattern472 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_/((x_*WC('e', S(1)) + WC('d', S(0)))*(x_*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons149, cons163)
    def replacement472(p, f, g, d, c, a, x, e):
        rubi.append(472)
        return -Dist(S(1)/(e*(-d*g + e*f)), Int((a + c*x**S(2))**(p + S(-1))*Simp(a*e*g + c*d*f - c*x*(-d*g + e*f), x)/(f + g*x), x), x) + Dist((a*e**S(2) + c*d**S(2))/(e*(-d*g + e*f)), Int((a + c*x**S(2))**(p + S(-1))/(d + e*x), x), x)
    rule472 = ReplacementRule(pattern472, replacement472)
    def With473(p, m, f, g, b, d, a, c, n, x, e):
        q = Denominator(m)
        rubi.append(473)
        return Dist(q/e, Subst(Int(x**(q*(m + S(1)) + S(-1))*(g*x**q/e + (-d*g + e*f)/e)**n*(c*x**(S(2)*q)/e**S(2) - x**q*(-b*e + S(2)*c*d)/e**S(2) + (a*e**S(2) - b*d*e + c*d**S(2))/e**S(2))**p, x), x, (d + e*x)**(S(1)/q)), x)
    pattern473 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons376, cons367)
    rule473 = ReplacementRule(pattern473, With473)
    def With474(p, m, f, g, d, c, n, a, x, e):
        q = Denominator(m)
        rubi.append(474)
        return Dist(q/e, Subst(Int(x**(q*(m + S(1)) + S(-1))*(g*x**q/e + (-d*g + e*f)/e)**n*(-S(2)*c*d*x**q/e**S(2) + c*x**(S(2)*q)/e**S(2) + (a*e**S(2) + c*d**S(2))/e**S(2))**p, x), x, (d + e*x)**(S(1)/q)), x)
    pattern474 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons376, cons367)
    rule474 = ReplacementRule(pattern474, With474)
    pattern475 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(f_ + x_*WC('g', S(1)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons124, cons336, cons377)
    def replacement475(p, m, g, b, f, d, a, n, c, x, e):
        rubi.append(475)
        return Int((d*f + e*g*x**S(2))**m*(a + b*x + c*x**S(2))**p, x)
    rule475 = ReplacementRule(pattern475, replacement475)
    pattern476 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(f_ + x_*WC('g', S(1)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons124, cons336, cons377)
    def replacement476(p, m, g, f, d, a, n, c, x, e):
        rubi.append(476)
        return Int((a + c*x**S(2))**p*(d*f + e*g*x**S(2))**m, x)
    rule476 = ReplacementRule(pattern476, replacement476)
    pattern477 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(f_ + x_*WC('g', S(1)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons124, cons336)
    def replacement477(p, m, g, b, f, d, c, a, n, x, e):
        rubi.append(477)
        return Dist((d + e*x)**FracPart(m)*(f + g*x)**FracPart(m)*(d*f + e*g*x**S(2))**(-FracPart(m)), Int((d*f + e*g*x**S(2))**m*(a + b*x + c*x**S(2))**p, x), x)
    rule477 = ReplacementRule(pattern477, replacement477)
    pattern478 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(f_ + x_*WC('g', S(1)))**n_*(x_**S(2)*WC('c', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons124, cons336)
    def replacement478(p, m, g, f, d, a, c, n, x, e):
        rubi.append(478)
        return Dist((d + e*x)**FracPart(m)*(f + g*x)**FracPart(m)*(d*f + e*g*x**S(2))**(-FracPart(m)), Int((a + c*x**S(2))**p*(d*f + e*g*x**S(2))**m, x), x)
    rule478 = ReplacementRule(pattern478, replacement478)
    pattern479 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons226, cons279, cons93)
    def replacement479(m, f, g, b, d, a, c, n, x, e):
        rubi.append(479)
        return Dist(c, Int(x**S(2)*(d + e*x)**m*(f + g*x)**n, x), x) + Int((a + b*x)*(d + e*x)**m*(f + g*x)**n, x)
    rule479 = ReplacementRule(pattern479, replacement479)
    pattern480 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons280, cons93)
    def replacement480(m, f, g, d, c, n, a, x, e):
        rubi.append(480)
        return Dist(a, Int((d + e*x)**m*(f + g*x)**n, x), x) + Dist(c, Int(x**S(2)*(d + e*x)**m*(f + g*x)**n, x), x)
    rule480 = ReplacementRule(pattern480, replacement480)
    pattern481 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons226, cons279, cons18, cons23, cons93, cons168, cons165)
    def replacement481(m, f, g, b, d, a, c, n, x, e):
        rubi.append(481)
        return Dist(c**(S(-2)), Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-2))*Simp(a*b*e*g**S(2) - a*c*d*g**S(2) - S(2)*a*c*e*f*g + c**S(2)*d*f**S(2) + x*(-a*c*e*g**S(2) + b**S(2)*e*g**S(2) - b*c*d*g**S(2) - S(2)*b*c*e*f*g + S(2)*c**S(2)*d*f*g + c**S(2)*e*f**S(2)), x)/(a + b*x + c*x**S(2)), x), x) + Dist(g/c**S(2), Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-2))*Simp(-b*e*g + c*d*g + S(2)*c*e*f + c*e*g*x, x), x), x)
    rule481 = ReplacementRule(pattern481, replacement481)
    pattern482 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons280, cons18, cons23, cons93, cons168, cons165)
    def replacement482(m, f, g, d, c, n, a, x, e):
        rubi.append(482)
        return Dist(S(1)/c, Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-2))*Simp(-a*d*g**S(2) - S(2)*a*e*f*g + c*d*f**S(2) + x*(-a*e*g**S(2) + S(2)*c*d*f*g + c*e*f**S(2)), x)/(a + c*x**S(2)), x), x) + Dist(g/c, Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-2))*Simp(d*g + S(2)*e*f + e*g*x, x), x), x)
    rule482 = ReplacementRule(pattern482, replacement482)
    pattern483 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons226, cons279, cons18, cons23, cons93, cons168, cons88)
    def replacement483(m, f, g, b, d, a, c, n, x, e):
        rubi.append(483)
        return Dist(S(1)/c, Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-1))*Simp(-a*e*g + c*d*f + x*(-b*e*g + c*d*g + c*e*f), x)/(a + b*x + c*x**S(2)), x), x) + Dist(e*g/c, Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-1)), x), x)
    rule483 = ReplacementRule(pattern483, replacement483)
    pattern484 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons280, cons18, cons23, cons93, cons168, cons88)
    def replacement484(m, f, g, d, c, n, a, x, e):
        rubi.append(484)
        return Dist(S(1)/c, Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-1))*Simp(-a*e*g + c*d*f + x*(c*d*g + c*e*f), x)/(a + c*x**S(2)), x), x) + Dist(e*g/c, Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(-1)), x), x)
    rule484 = ReplacementRule(pattern484, replacement484)
    pattern485 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons226, cons279, cons18, cons23, cons93, cons168, cons89)
    def replacement485(m, f, g, b, d, a, c, n, x, e):
        rubi.append(485)
        return -Dist(g*(-d*g + e*f)/(a*g**S(2) - b*f*g + c*f**S(2)), Int((d + e*x)**(m + S(-1))*(f + g*x)**n, x), x) + Dist(S(1)/(a*g**S(2) - b*f*g + c*f**S(2)), Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1))*Simp(a*e*g - b*d*g + c*d*f + c*x*(-d*g + e*f), x)/(a + b*x + c*x**S(2)), x), x)
    rule485 = ReplacementRule(pattern485, replacement485)
    pattern486 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons280, cons18, cons23, cons93, cons168, cons89)
    def replacement486(m, f, g, d, c, n, a, x, e):
        rubi.append(486)
        return -Dist(g*(-d*g + e*f)/(a*g**S(2) + c*f**S(2)), Int((d + e*x)**(m + S(-1))*(f + g*x)**n, x), x) + Dist(S(1)/(a*g**S(2) + c*f**S(2)), Int((d + e*x)**(m + S(-1))*(f + g*x)**(n + S(1))*Simp(a*e*g + c*d*f + c*x*(-d*g + e*f), x)/(a + c*x**S(2)), x), x)
    rule486 = ReplacementRule(pattern486, replacement486)
    pattern487 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_/(sqrt(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons226, cons279, cons73)
    def replacement487(m, f, g, b, d, a, c, x, e):
        rubi.append(487)
        return Int(ExpandIntegrand(S(1)/(sqrt(d + e*x)*sqrt(f + g*x)), (d + e*x)**(m + S(1)/2)/(a + b*x + c*x**S(2)), x), x)
    rule487 = ReplacementRule(pattern487, replacement487)
    pattern488 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_/(sqrt(x_*WC('g', S(1)) + WC('f', S(0)))*(x_**S(2)*WC('c', S(1)) + WC('a', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons280, cons73)
    def replacement488(m, f, g, d, a, c, x, e):
        rubi.append(488)
        return Int(ExpandIntegrand(S(1)/(sqrt(d + e*x)*sqrt(f + g*x)), (d + e*x)**(m + S(1)/2)/(a + c*x**S(2)), x), x)
    rule488 = ReplacementRule(pattern488, replacement488)
    pattern489 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons226, cons279, cons18, cons23)
    def replacement489(m, f, g, b, d, a, c, n, x, e):
        rubi.append(489)
        return Int(ExpandIntegrand((d + e*x)**m*(f + g*x)**n, S(1)/(a + b*x + c*x**S(2)), x), x)
    rule489 = ReplacementRule(pattern489, replacement489)
    pattern490 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(a_ + x_**S(2)*WC('c', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons280, cons18, cons23)
    def replacement490(m, f, g, d, c, n, a, x, e):
        rubi.append(490)
        return Int(ExpandIntegrand((d + e*x)**m*(f + g*x)**n, S(1)/(a + c*x**S(2)), x), x)
    rule490 = ReplacementRule(pattern490, replacement490)
    pattern491 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons378)
    def replacement491(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(491)
        return Int(ExpandIntegrand((d + e*x)**m*(f + g*x)**n*(a + b*x + c*x**S(2))**p, x), x)
    rule491 = ReplacementRule(pattern491, replacement491)
    pattern492 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons378)
    def replacement492(p, m, f, g, d, c, n, a, x, e):
        rubi.append(492)
        return Int(ExpandIntegrand((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**n, x), x)
    rule492 = ReplacementRule(pattern492, replacement492)
    pattern493 = Pattern(Integral((x_*WC('g', S(1)))**WC('n', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons208, cons21, cons4, cons5, cons358, cons288, cons289)
    def replacement493(p, m, g, b, d, c, n, a, x, e):
        rubi.append(493)
        return Dist((d + e*x)**FracPart(p)*(a*d + c*e*x**S(3))**(-FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((g*x)**n*(a*d + c*e*x**S(3))**p, x), x)
    rule493 = ReplacementRule(pattern493, replacement493)
    pattern494 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons23, cons147, cons338, cons163, cons89)
    def replacement494(p, f, g, b, d, a, c, n, x, e):
        rubi.append(494)
        return -Dist(S(1)/(e*(-d*g + e*f)), Int((f + g*x)**n*(a + b*x + c*x**S(2))**(p + S(-1))*(a*e*g - b*e*f + c*d*f - c*x*(-d*g + e*f)), x), x) + Dist((a*e**S(2) - b*d*e + c*d**S(2))/(e*(-d*g + e*f)), Int((f + g*x)**(n + S(1))*(a + b*x + c*x**S(2))**(p + S(-1))/(d + e*x), x), x)
    rule494 = ReplacementRule(pattern494, replacement494)
    pattern495 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons23, cons147, cons338, cons163, cons89)
    def replacement495(p, f, g, d, c, n, a, x, e):
        rubi.append(495)
        return -Dist(S(1)/(e*(-d*g + e*f)), Int((a + c*x**S(2))**(p + S(-1))*(f + g*x)**n*(a*e*g + c*d*f - c*x*(-d*g + e*f)), x), x) + Dist((a*e**S(2) + c*d**S(2))/(e*(-d*g + e*f)), Int((a + c*x**S(2))**(p + S(-1))*(f + g*x)**(n + S(1))/(d + e*x), x), x)
    rule495 = ReplacementRule(pattern495, replacement495)
    pattern496 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons23, cons147, cons338, cons137, cons88)
    def replacement496(p, f, g, b, d, a, c, n, x, e):
        rubi.append(496)
        return Dist(e*(-d*g + e*f)/(a*e**S(2) - b*d*e + c*d**S(2)), Int((f + g*x)**(n + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))/(d + e*x), x), x) + Dist(S(1)/(a*e**S(2) - b*d*e + c*d**S(2)), Int((f + g*x)**(n + S(-1))*(a + b*x + c*x**S(2))**p*(a*e*g - b*e*f + c*d*f - c*x*(-d*g + e*f)), x), x)
    rule496 = ReplacementRule(pattern496, replacement496)
    pattern497 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_/(x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons23, cons147, cons338, cons137, cons88)
    def replacement497(p, f, g, d, c, n, a, x, e):
        rubi.append(497)
        return Dist(e*(-d*g + e*f)/(a*e**S(2) + c*d**S(2)), Int((a + c*x**S(2))**(p + S(1))*(f + g*x)**(n + S(-1))/(d + e*x), x), x) + Dist(S(1)/(a*e**S(2) + c*d**S(2)), Int((a + c*x**S(2))**p*(f + g*x)**(n + S(-1))*(a*e*g + c*d*f - c*x*(-d*g + e*f)), x), x)
    rule497 = ReplacementRule(pattern497, replacement497)
    def With498(f, g, b, d, a, c, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(498)
        return Simp(-sqrt(S(2))*sqrt(-g*(b + S(2)*c*x - q)/(-b*g + S(2)*c*f + g*q))*sqrt(-g*(b + S(2)*c*x + q)/(-b*g + S(2)*c*f - g*q))*EllipticPi(e*(-b*g + S(2)*c*f + g*q)/(S(2)*c*(-d*g + e*f)), asin(sqrt(S(2))*sqrt(c/(-b*g + S(2)*c*f + g*q))*sqrt(f + g*x)), (-b*g + S(2)*c*f + g*q)/(-b*g + S(2)*c*f - g*q))/(sqrt(c/(-b*g + S(2)*c*f + g*q))*(-d*g + e*f)*sqrt(a + b*x + c*x**S(2))), x)
    pattern498 = Pattern(Integral(S(1)/((x_*WC('e', S(1)) + WC('d', S(0)))*sqrt(x_*WC('g', S(1)) + WC('f', S(0)))*sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279)
    rule498 = ReplacementRule(pattern498, With498)
    def With499(f, g, d, c, a, x, e):
        q = Rt(-a*c, S(2))
        rubi.append(499)
        return Simp(-S(2)*sqrt(g*(-c*x + q)/(c*f + g*q))*sqrt(-g*(c*x + q)/(c*f - g*q))*EllipticPi(e*(c*f + g*q)/(c*(-d*g + e*f)), asin(sqrt(c/(c*f + g*q))*sqrt(f + g*x)), (c*f + g*q)/(c*f - g*q))/(sqrt(c/(c*f + g*q))*sqrt(a + c*x**S(2))*(-d*g + e*f)), x)
    pattern499 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('c', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))*sqrt(x_*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280)
    rule499 = ReplacementRule(pattern499, With499)
    pattern500 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**n_/((x_*WC('e', S(1)) + WC('d', S(0)))*sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279, cons80)
    def replacement500(f, g, b, d, a, c, n, x, e):
        rubi.append(500)
        return Int(ExpandIntegrand(S(1)/(sqrt(f + g*x)*sqrt(a + b*x + c*x**S(2))), (f + g*x)**(n + S(1)/2)/(d + e*x), x), x)
    rule500 = ReplacementRule(pattern500, replacement500)
    pattern501 = Pattern(Integral((x_*WC('g', S(1)) + WC('f', S(0)))**n_/(sqrt(a_ + x_**S(2)*WC('c', S(1)))*(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280, cons80)
    def replacement501(f, g, d, c, n, a, x, e):
        rubi.append(501)
        return Int(ExpandIntegrand(S(1)/(sqrt(a + c*x**S(2))*sqrt(f + g*x)), (f + g*x)**(n + S(1)/2)/(d + e*x), x), x)
    rule501 = ReplacementRule(pattern501, replacement501)
    pattern502 = Pattern(Integral(S(1)/(sqrt(x_*WC('e', S(1)) + WC('d', S(0)))*sqrt(x_*WC('g', S(1)) + WC('f', S(0)))*sqrt(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons315, cons226, cons279)
    def replacement502(f, g, b, d, a, c, x, e):
        rubi.append(502)
        return Dist(-S(2)*sqrt((-d*g + e*f)**S(2)*(a + b*x + c*x**S(2))/((d + e*x)**S(2)*(a*g**S(2) - b*f*g + c*f**S(2))))*(d + e*x)/((-d*g + e*f)*sqrt(a + b*x + c*x**S(2))), Subst(Int(S(1)/sqrt(x**S(4)*(a*e**S(2) - b*d*e + c*d**S(2))/(a*g**S(2) - b*f*g + c*f**S(2)) - x**S(2)*(S(2)*a*e*g - b*d*g - b*e*f + S(2)*c*d*f)/(a*g**S(2) - b*f*g + c*f**S(2)) + S(1)), x), x, sqrt(f + g*x)/sqrt(d + e*x)), x)
    rule502 = ReplacementRule(pattern502, replacement502)
    pattern503 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('c', S(1)))*sqrt(x_*WC('e', S(1)) + WC('d', S(0)))*sqrt(x_*WC('g', S(1)) + WC('f', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons315, cons280)
    def replacement503(f, g, d, c, a, x, e):
        rubi.append(503)
        return Dist(-S(2)*sqrt((a + c*x**S(2))*(-d*g + e*f)**S(2)/((d + e*x)**S(2)*(a*g**S(2) + c*f**S(2))))*(d + e*x)/(sqrt(a + c*x**S(2))*(-d*g + e*f)), Subst(Int(S(1)/sqrt(x**S(4)*(a*e**S(2) + c*d**S(2))/(a*g**S(2) + c*f**S(2)) - x**S(2)*(S(2)*a*e*g + S(2)*c*d*f)/(a*g**S(2) + c*f**S(2)) + S(1)), x), x, sqrt(f + g*x)/sqrt(d + e*x)), x)
    rule503 = ReplacementRule(pattern503, replacement503)
    pattern504 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(f_ + x_*WC('g', S(1)))**S(2), x_), cons2, cons7, cons48, cons125, cons208, cons21, cons5, cons379)
    def replacement504(p, m, g, f, c, a, x, e):
        rubi.append(504)
        return Dist(S(2)*f*g/e, Int((e*x)**(m + S(1))*(a + c*x**S(2))**p, x), x) + Int((e*x)**m*(a + c*x**S(2))**p*(f**S(2) + g**S(2)*x**S(2)), x)
    rule504 = ReplacementRule(pattern504, replacement504)
    pattern505 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(f_ + x_*WC('g', S(1)))**S(3), x_), cons2, cons7, cons48, cons125, cons208, cons21, cons5, cons379)
    def replacement505(p, m, g, f, c, a, x, e):
        rubi.append(505)
        return Dist(f, Int((e*x)**m*(a + c*x**S(2))**p*(f**S(2) + S(3)*g**S(2)*x**S(2)), x), x) + Dist(g/e, Int((e*x)**(m + S(1))*(a + c*x**S(2))**p*(S(3)*f**S(2) + g**S(2)*x**S(2)), x), x)
    rule505 = ReplacementRule(pattern505, replacement505)
    pattern506 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons226, cons279, cons148)
    def replacement506(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(506)
        return Dist(g/e, Int((d + e*x)**(m + S(1))*(f + g*x)**(n + S(-1))*(a + b*x + c*x**S(2))**p, x), x) + Dist((-d*g + e*f)/e, Int((d + e*x)**m*(f + g*x)**(n + S(-1))*(a + b*x + c*x**S(2))**p, x), x)
    rule506 = ReplacementRule(pattern506, replacement506)
    pattern507 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**m_*(x_*WC('g', S(1)) + WC('f', S(0)))**n_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons315, cons280, cons148)
    def replacement507(p, m, f, g, d, c, n, a, x, e):
        rubi.append(507)
        return Dist(g/e, Int((a + c*x**S(2))**p*(d + e*x)**(m + S(1))*(f + g*x)**(n + S(-1)), x), x) + Dist((-d*g + e*f)/e, Int((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**(n + S(-1)), x), x)
    rule507 = ReplacementRule(pattern507, replacement507)
    pattern508 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons380)
    def replacement508(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(508)
        return Int((d + e*x)**m*(f + g*x)**n*(a + b*x + c*x**S(2))**p, x)
    rule508 = ReplacementRule(pattern508, replacement508)
    pattern509 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons381)
    def replacement509(p, m, f, g, d, c, n, a, x, e):
        rubi.append(509)
        return Int((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**n, x)
    rule509 = ReplacementRule(pattern509, replacement509)
    pattern510 = Pattern(Integral((u_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(u_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(a_ + u_**S(2)*WC('c', S(1)) + u_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons68, cons69)
    def replacement510(p, u, m, f, g, b, d, c, n, a, x, e):
        rubi.append(510)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((d + e*x)**m*(f + g*x)**n*(a + b*x + c*x**S(2))**p, x), x, u), x)
    rule510 = ReplacementRule(pattern510, replacement510)
    pattern511 = Pattern(Integral((a_ + u_**S(2)*WC('c', S(1)))**WC('p', S(1))*(u_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(u_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons68, cons69)
    def replacement511(p, u, m, f, g, d, c, n, a, x, e):
        rubi.append(511)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + c*x**S(2))**p*(d + e*x)**m*(f + g*x)**n, x), x, u), x)
    rule511 = ReplacementRule(pattern511, replacement511)
    pattern512 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons382, cons383, cons384, cons385)
    def replacement512(p, f, b, d, c, a, x, q, e):
        rubi.append(512)
        return Dist((c/f)**p, Int((d + e*x + f*x**S(2))**(p + q), x), x)
    rule512 = ReplacementRule(pattern512, replacement512)
    pattern513 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons382, cons383, cons147, cons386, cons387)
    def replacement513(p, f, b, d, c, a, x, q, e):
        rubi.append(513)
        return Dist(a**IntPart(p)*d**(-IntPart(p))*(a + b*x + c*x**S(2))**FracPart(p)*(d + e*x + f*x**S(2))**(-FracPart(p)), Int((d + e*x + f*x**S(2))**(p + q), x), x)
    rule513 = ReplacementRule(pattern513, replacement513)
    pattern514 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons45, cons147)
    def replacement514(p, f, b, d, c, a, x, q, e):
        rubi.append(514)
        return Dist((S(4)*c)**(-IntPart(p))*(b + S(2)*c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((b + S(2)*c*x)**(S(2)*p)*(d + e*x + f*x**S(2))**q, x), x)
    rule514 = ReplacementRule(pattern514, replacement514)
    pattern515 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons125, cons5, cons50, cons45, cons147)
    def replacement515(p, f, b, d, c, a, x, q):
        rubi.append(515)
        return Dist((S(4)*c)**(-IntPart(p))*(b + S(2)*c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((b + S(2)*c*x)**(S(2)*p)*(d + f*x**S(2))**q, x), x)
    rule515 = ReplacementRule(pattern515, replacement515)
    pattern516 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons50, cons388, cons389, cons390)
    def replacement516(f, b, d, c, a, x, q, e):
        rubi.append(516)
        return Simp((d + e*x + f*x**S(2))**(q + S(1))*(b*f*(S(2)*q + S(3)) - c*e*(q + S(2)) + S(2)*c*f*x*(q + S(1)))/(S(2)*f**S(2)*(q + S(1))*(S(2)*q + S(3))), x)
    rule516 = ReplacementRule(pattern516, replacement516)
    pattern517 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons7, cons27, cons48, cons125, cons50, cons391, cons389, cons390)
    def replacement517(f, d, c, a, x, q, e):
        rubi.append(517)
        return Simp((-c*e*(q + S(2)) + S(2)*c*f*x*(q + S(1)))*(d + e*x + f*x**S(2))**(q + S(1))/(S(2)*f**S(2)*(q + S(1))*(S(2)*q + S(3))), x)
    rule517 = ReplacementRule(pattern517, replacement517)
    pattern518 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**q_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons125, cons50, cons389, cons392)
    def replacement518(f, b, d, c, a, x, q):
        rubi.append(518)
        return Simp((d + f*x**S(2))**(q + S(1))*(S(2)*a*f*x*(q + S(1)) + b*d)/(S(2)*d*f*(q + S(1))), x)
    rule518 = ReplacementRule(pattern518, replacement518)
    pattern519 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**q_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons125, cons50, cons393)
    def replacement519(f, b, d, c, a, x, q):
        rubi.append(519)
        return Dist(b, Int(x*(d + f*x**S(2))**q, x), x) + Int((a + c*x**S(2))*(d + f*x**S(2))**q, x)
    rule519 = ReplacementRule(pattern519, replacement519)
    pattern520 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons394, cons393)
    def replacement520(f, b, d, c, a, x, q, e):
        rubi.append(520)
        return Int(ExpandIntegrand((a + b*x + c*x**S(2))*(d + e*x + f*x**S(2))**q, x), x)
    rule520 = ReplacementRule(pattern520, replacement520)
    pattern521 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons394, cons393)
    def replacement521(f, d, c, a, x, q, e):
        rubi.append(521)
        return Int(ExpandIntegrand((a + c*x**S(2))*(d + e*x + f*x**S(2))**q, x), x)
    rule521 = ReplacementRule(pattern521, replacement521)
    pattern522 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons394, cons395, cons396, cons397)
    def replacement522(f, b, d, c, a, x, q, e):
        rubi.append(522)
        return -Dist((c*(-S(2)*d*f + e**S(2)*(q + S(2))) + f*(S(2)*q + S(3))*(S(2)*a*f - b*e))/(f*(q + S(1))*(-S(4)*d*f + e**S(2))), Int((d + e*x + f*x**S(2))**(q + S(1)), x), x) + Simp((d + e*x + f*x**S(2))**(q + S(1))*(a*e*f - S(2)*b*d*f + c*d*e + x*(c*(-S(2)*d*f + e**S(2)) + f*(S(2)*a*f - b*e)))/(f*(q + S(1))*(-S(4)*d*f + e**S(2))), x)
    rule522 = ReplacementRule(pattern522, replacement522)
    pattern523 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons7, cons27, cons48, cons125, cons394, cons395, cons396, cons398)
    def replacement523(f, d, c, a, x, q, e):
        rubi.append(523)
        return -Dist((S(2)*a*f**S(2)*(S(2)*q + S(3)) + c*(-S(2)*d*f + e**S(2)*(q + S(2))))/(f*(q + S(1))*(-S(4)*d*f + e**S(2))), Int((d + e*x + f*x**S(2))**(q + S(1)), x), x) + Simp((d + e*x + f*x**S(2))**(q + S(1))*(a*e*f + c*d*e + x*(S(2)*a*f**S(2) + c*(-S(2)*d*f + e**S(2))))/(f*(q + S(1))*(-S(4)*d*f + e**S(2))), x)
    rule523 = ReplacementRule(pattern523, replacement523)
    pattern524 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**q_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons2, cons3, cons7, cons27, cons125, cons395, cons396, cons399)
    def replacement524(f, b, d, c, a, x, q):
        rubi.append(524)
        return Dist((S(2)*a*f*q + S(3)*a*f - c*d)/(S(2)*d*f*(q + S(1))), Int((d + f*x**S(2))**(q + S(1)), x), x) + Simp((d + f*x**S(2))**(q + S(1))*(b*d - x*(a*f - c*d))/(S(2)*d*f*(q + S(1))), x)
    rule524 = ReplacementRule(pattern524, replacement524)
    pattern525 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons27, cons48, cons125, cons2, cons3, cons7, cons50, cons394, cons400, cons401, cons397)
    def replacement525(f, b, d, c, a, x, q, e):
        rubi.append(525)
        return Dist((c*(-S(2)*d*f + e**S(2)*(q + S(2))) + f*(S(2)*q + S(3))*(S(2)*a*f - b*e))/(S(2)*f**S(2)*(S(2)*q + S(3))), Int((d + e*x + f*x**S(2))**q, x), x) + Simp((d + e*x + f*x**S(2))**(q + S(1))*(b*f*(S(2)*q + S(3)) - c*e*(q + S(2)) + S(2)*c*f*x*(q + S(1)))/(S(2)*f**S(2)*(q + S(1))*(S(2)*q + S(3))), x)
    rule525 = ReplacementRule(pattern525, replacement525)
    pattern526 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons27, cons48, cons125, cons2, cons7, cons50, cons394, cons400, cons401, cons398)
    def replacement526(f, d, c, a, x, q, e):
        rubi.append(526)
        return Dist((S(2)*a*f**S(2)*(S(2)*q + S(3)) + c*(-S(2)*d*f + e**S(2)*(q + S(2))))/(S(2)*f**S(2)*(S(2)*q + S(3))), Int((d + e*x + f*x**S(2))**q, x), x) + Simp((-c*e*(q + S(2)) + S(2)*c*f*x*(q + S(1)))*(d + e*x + f*x**S(2))**(q + S(1))/(S(2)*f**S(2)*(q + S(1))*(S(2)*q + S(3))), x)
    rule526 = ReplacementRule(pattern526, replacement526)
    pattern527 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**q_*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1))), x_), cons27, cons125, cons2, cons3, cons7, cons50, cons400, cons401, cons399)
    def replacement527(f, b, d, c, a, x, q):
        rubi.append(527)
        return Dist((S(2)*a*f*q + S(3)*a*f - c*d)/(f*(S(2)*q + S(3))), Int((d + f*x**S(2))**q, x), x) + Simp((d + f*x**S(2))**(q + S(1))*(b*f*(S(2)*q + S(3)) + S(2)*c*f*x*(q + S(1)))/(S(2)*f**S(2)*(q + S(1))*(S(2)*q + S(3))), x)
    rule527 = ReplacementRule(pattern527, replacement527)
    pattern528 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons226, cons394, cons402, cons137, cons403)
    def replacement528(p, f, b, d, c, a, x, q, e):
        rubi.append(528)
        return -Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(-1))*Simp(b*e*q + S(2)*c*d*(S(2)*p + S(3)) + S(2)*c*f*x**S(2)*(S(2)*p + S(2)*q + S(3)) + x*(S(2)*b*f*q + S(2)*c*e*(S(2)*p + q + S(3))), x), x), x) + Simp((b + S(2)*c*x)*(a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule528 = ReplacementRule(pattern528, replacement528)
    pattern529 = Pattern(Integral((x_**S(2)*WC('f', S(1)) + WC('d', S(0)))**WC('q', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons125, cons226, cons402, cons137, cons403)
    def replacement529(p, f, b, d, c, a, x, q):
        rubi.append(529)
        return -Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + f*x**S(2))**(q + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*Simp(S(2)*b*f*q*x + S(2)*c*d*(S(2)*p + S(3)) + S(2)*c*f*x**S(2)*(S(2)*p + S(2)*q + S(3)), x), x), x) + Simp((b + S(2)*c*x)*(d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(1))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule529 = ReplacementRule(pattern529, replacement529)
    pattern530 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons394, cons402, cons137, cons403)
    def replacement530(p, f, d, a, c, x, q, e):
        rubi.append(530)
        return -Dist(-S(1)/(S(4)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(-1))*Simp(S(2)*c*d*(S(2)*p + S(3)) + S(2)*c*e*x*(S(2)*p + q + S(3)) + S(2)*c*f*x**S(2)*(S(2)*p + S(2)*q + S(3)), x), x), x) + Simp(-x*(a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q/(S(2)*a*(p + S(1))), x)
    rule530 = ReplacementRule(pattern530, replacement530)
    pattern531 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons50, cons226, cons394, cons13, cons137, cons404, cons405)
    def replacement531(p, f, b, d, c, a, x, q, e):
        rubi.append(531)
        return -Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*Simp(c*f*x**S(2)*(S(2)*p + S(2)*q + S(5))*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) + S(2)*c*(p + S(1))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2)) - e*(p + q + S(2))*(-S(2)*a*c**S(2)*e - b**S(3)*f + b**S(2)*c*e - b*c*(-S(3)*a*f + c*d)) + x*(S(2)*f*(p + q + S(2))*(S(2)*a*c**S(2)*e + b**S(3)*f - b**S(2)*c*e + b*c*(-S(3)*a*f + c*d)) - (b*f*(p + S(1)) - c*e*(S(2)*p + q + S(4)))*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e))) - (a*f*(p + S(1)) - c*d*(p + S(2)))*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)), x), x), x) + Simp((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(1))*(S(2)*a*c**S(2)*e + b**S(3)*f - b**S(2)*c*e + b*c*(-S(3)*a*f + c*d) + c*x*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)))/((p + S(1))*(-S(4)*a*c + b**S(2))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2))), x)
    rule531 = ReplacementRule(pattern531, replacement531)
    pattern532 = Pattern(Integral((x_**S(2)*WC('f', S(1)) + WC('d', S(0)))**WC('q', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons125, cons50, cons226, cons13, cons137, cons406, cons405)
    def replacement532(p, f, b, d, c, a, x, q):
        rubi.append(532)
        return -Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(b**S(2)*d*f + (-a*f + c*d)**S(2))), Int((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(1))*Simp(c*f*x**S(2)*(S(2)*p + S(2)*q + S(5))*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d) + S(2)*c*(p + S(1))*(b**S(2)*d*f + (-a*f + c*d)**S(2)) + x*(-b*f*(p + S(1))*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d) + S(2)*f*(b**S(3)*f + b*c*(-S(3)*a*f + c*d))*(p + q + S(2))) - (a*f*(p + S(1)) - c*d*(p + S(2)))*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d), x), x), x) + Simp((d + f*x**S(2))**(q + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(b**S(3)*f + b*c*(-S(3)*a*f + c*d) + c*x*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d))/((p + S(1))*(-S(4)*a*c + b**S(2))*(b**S(2)*d*f + (-a*f + c*d)**S(2))), x)
    rule532 = ReplacementRule(pattern532, replacement532)
    pattern533 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons50, cons394, cons13, cons137, cons407, cons405)
    def replacement533(p, f, d, a, c, x, q, e):
        rubi.append(533)
        return -Dist(-S(1)/(S(4)*a*c*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*Simp(S(2)*a*c**S(2)*e**S(2)*(p + q + S(2)) + c*f*x**S(2)*(-S(2)*a*c*f + S(2)*c**S(2)*d)*(S(2)*p + S(2)*q + S(5)) + S(2)*c*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2)) + x*(S(4)*a*c**S(2)*e*f*(p + q + S(2)) + c*e*(-S(2)*a*c*f + S(2)*c**S(2)*d)*(S(2)*p + q + S(4))) - (-S(2)*a*c*f + S(2)*c**S(2)*d)*(a*f*(p + S(1)) - c*d*(p + S(2))), x), x), x) + Simp(-(a + c*x**S(2))**(p + S(1))*(S(2)*a*c**S(2)*e + c*x*(-S(2)*a*c*f + S(2)*c**S(2)*d))*(d + e*x + f*x**S(2))**(q + S(1))/(S(4)*a*c*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2))), x)
    rule533 = ReplacementRule(pattern533, replacement533)
    pattern534 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons50, cons226, cons394, cons13, cons146, cons408, cons409)
    def replacement534(p, f, b, d, c, a, x, q, e):
        rubi.append(534)
        return -Dist(S(1)/(S(2)*f**S(2)*(p + q)*(S(2)*p + S(2)*q + S(1))), Int((a + b*x + c*x**S(2))**(p + S(-2))*(d + e*x + f*x**S(2))**q*Simp(x**S(2)*(c*(p + q)*(-c*(S(2)*d*f*(-S(2)*p + S(1)) + e**S(2)*(S(3)*p + q + S(-1))) + f*(-S(2)*a*f + b*e)*(S(4)*p + S(2)*q + S(-1))) + p*(-p + S(1))*(-b*f + c*e)**S(2)) + x*(S(2)*(-p + S(1))*(S(2)*p + q)*(-a*f + c*d)*(-b*f + c*e) - (p + q)*(b*(c*(S(2)*p + q)*(-S(4)*d*f + e**S(2)) + f*(S(2)*p + S(2)*q + S(1))*(S(2)*a*f - b*e + S(2)*c*d)) + e*f*(-p + S(1))*(-S(4)*a*c + b**S(2)))) + (-p + S(1))*(S(2)*p + q)*(-a*e + b*d)*(-b*f + c*e) - (p + q)*(-a*(c*(S(2)*d*f - e**S(2)*(S(2)*p + q)) + f*(-S(2)*a*f + b*e)*(S(2)*p + S(2)*q + S(1))) + b**S(2)*d*f*(-p + S(1))), x), x), x) + Simp((a + b*x + c*x**S(2))**(p + S(-1))*(d + e*x + f*x**S(2))**(q + S(1))*(b*f*(S(3)*p + S(2)*q) - c*e*(S(2)*p + q) + S(2)*c*f*x*(p + q))/(S(2)*f**S(2)*(p + q)*(S(2)*p + S(2)*q + S(1))), x)
    rule534 = ReplacementRule(pattern534, replacement534)
    pattern535 = Pattern(Integral((x_**S(2)*WC('f', S(1)) + WC('d', S(0)))**WC('q', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons125, cons50, cons226, cons13, cons146, cons408, cons409)
    def replacement535(p, f, b, d, c, a, x, q):
        rubi.append(535)
        return -Dist(S(1)/(S(2)*f*(p + q)*(S(2)*p + S(2)*q + S(1))), Int((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(-2))*Simp(b**S(2)*d*(p + S(-1))*(S(2)*p + q) + x**S(2)*(b**S(2)*f*p*(-p + S(1)) + S(2)*c*(p + q)*(-a*f*(S(4)*p + S(2)*q + S(-1)) + c*d*(S(2)*p + S(-1)))) - x*(S(2)*b*(-p + S(1))*(S(2)*p + q)*(-a*f + c*d) - S(2)*b*(p + q)*(S(2)*c*d*(S(2)*p + q) - (a*f + c*d)*(S(2)*p + S(2)*q + S(1)))) - (p + q)*(-S(2)*a*(-a*f*(S(2)*p + S(2)*q + S(1)) + c*d) + b**S(2)*d*(-p + S(1))), x), x), x) + Simp((d + f*x**S(2))**(q + S(1))*(b*(S(3)*p + S(2)*q) + S(2)*c*x*(p + q))*(a + b*x + c*x**S(2))**(p + S(-1))/(S(2)*f*(p + q)*(S(2)*p + S(2)*q + S(1))), x)
    rule535 = ReplacementRule(pattern535, replacement535)
    pattern536 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons50, cons394, cons13, cons146, cons408, cons409)
    def replacement536(p, f, d, a, c, x, q, e):
        rubi.append(536)
        return -Dist(S(1)/(S(2)*f**S(2)*(p + q)*(S(2)*p + S(2)*q + S(1))), Int((a + c*x**S(2))**(p + S(-2))*(d + e*x + f*x**S(2))**q*Simp(-a*c*e**S(2)*(-p + S(1))*(S(2)*p + q) + a*(p + q)*(-S(2)*a*f**S(2)*(S(2)*p + S(2)*q + S(1)) + c*(S(2)*d*f - e**S(2)*(S(2)*p + q))) + x**S(2)*(c**S(2)*e**S(2)*p*(-p + S(1)) - c*(p + q)*(S(2)*a*f**S(2)*(S(4)*p + S(2)*q + S(-1)) + c*(S(2)*d*f*(-S(2)*p + S(1)) + e**S(2)*(S(3)*p + q + S(-1))))) + x*(S(4)*a*c*e*f*(-p + S(1))*(p + q) + S(2)*c*e*(-p + S(1))*(S(2)*p + q)*(-a*f + c*d)), x), x), x) - Simp(c*(a + c*x**S(2))**(p + S(-1))*(e*(S(2)*p + q) - S(2)*f*x*(p + q))*(d + e*x + f*x**S(2))**(q + S(1))/(S(2)*f**S(2)*(p + q)*(S(2)*p + S(2)*q + S(1))), x)
    rule536 = ReplacementRule(pattern536, replacement536)
    def With537(f, b, d, c, a, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = a**S(2)*f**S(2) - a*b*e*f - S(2)*a*c*d*f + a*c*e**S(2) + b**S(2)*d*f - b*c*d*e + c**S(2)*d**S(2)
        if NonzeroQ(q):
            return True
        return False
    pattern537 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons226, cons394, CustomConstraint(With537))
    def replacement537(f, b, d, c, a, x, e):

        q = a**S(2)*f**S(2) - a*b*e*f - S(2)*a*c*d*f + a*c*e**S(2) + b**S(2)*d*f - b*c*d*e + c**S(2)*d**S(2)
        rubi.append(537)
        return Dist(S(1)/q, Int((-a*c*f + b**S(2)*f - b*c*e + c**S(2)*d - x*(-b*c*f + c**S(2)*e))/(a + b*x + c*x**S(2)), x), x) + Dist(S(1)/q, Int((a*f**S(2) - b*e*f - c*d*f + c*e**S(2) + x*(-b*f**S(2) + c*e*f))/(d + e*x + f*x**S(2)), x), x)
    rule537 = ReplacementRule(pattern537, replacement537)
    def With538(f, b, d, c, a, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = a**S(2)*f**S(2) - S(2)*a*c*d*f + b**S(2)*d*f + c**S(2)*d**S(2)
        if NonzeroQ(q):
            return True
        return False
    pattern538 = Pattern(Integral(S(1)/((d_ + x_**S(2)*WC('f', S(1)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons226, CustomConstraint(With538))
    def replacement538(f, b, d, c, a, x):

        q = a**S(2)*f**S(2) - S(2)*a*c*d*f + b**S(2)*d*f + c**S(2)*d**S(2)
        rubi.append(538)
        return -Dist(S(1)/q, Int((-a*f**S(2) + b*f**S(2)*x + c*d*f)/(d + f*x**S(2)), x), x) + Dist(S(1)/q, Int((-a*c*f + b**S(2)*f + b*c*f*x + c**S(2)*d)/(a + b*x + c*x**S(2)), x), x)
    rule538 = ReplacementRule(pattern538, replacement538)
    pattern539 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons226, cons394, cons410)
    def replacement539(f, b, d, c, a, x, e):
        rubi.append(539)
        return Dist(-S(2)*e, Subst(Int(S(1)/(e*(-S(4)*a*f + b*e) - x**S(2)*(-a*e + b*d)), x), x, (e + S(2)*f*x)/sqrt(d + e*x + f*x**S(2))), x)
    rule539 = ReplacementRule(pattern539, replacement539)
    def With540(f, b, d, c, a, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(540)
        return Dist(S(2)*c/q, Int(S(1)/((b + S(2)*c*x - q)*sqrt(d + e*x + f*x**S(2))), x), x) - Dist(S(2)*c/q, Int(S(1)/((b + S(2)*c*x + q)*sqrt(d + e*x + f*x**S(2))), x), x)
    pattern540 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons226, cons394, cons411, cons231)
    rule540 = ReplacementRule(pattern540, With540)
    pattern541 = Pattern(Integral(S(1)/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons394, cons412)
    def replacement541(f, d, c, a, x, e):
        rubi.append(541)
        return Dist(S(1)/2, Int(S(1)/((a - x*Rt(-a*c, S(2)))*sqrt(d + e*x + f*x**S(2))), x), x) + Dist(S(1)/2, Int(S(1)/((a + x*Rt(-a*c, S(2)))*sqrt(d + e*x + f*x**S(2))), x), x)
    rule541 = ReplacementRule(pattern541, replacement541)
    def With542(f, b, d, c, a, x):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(542)
        return Dist(S(2)*c/q, Int(S(1)/(sqrt(d + f*x**S(2))*(b + S(2)*c*x - q)), x), x) - Dist(S(2)*c/q, Int(S(1)/(sqrt(d + f*x**S(2))*(b + S(2)*c*x + q)), x), x)
    pattern542 = Pattern(Integral(S(1)/(sqrt(d_ + x_**S(2)*WC('f', S(1)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons226, cons231)
    rule542 = ReplacementRule(pattern542, With542)
    def With543(f, b, d, c, a, x, e):
        q = Rt(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2), S(2))
        rubi.append(543)
        return -Dist(S(1)/(S(2)*q), Int((-a*f + c*d - q + x*(-b*f + c*e))/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x) + Dist(S(1)/(S(2)*q), Int((-a*f + c*d + q + x*(-b*f + c*e))/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x)
    pattern543 = Pattern(Integral(S(1)/((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons226, cons394, cons411, cons413)
    rule543 = ReplacementRule(pattern543, With543)
    def With544(f, d, a, c, x, e):
        q = Rt(a*c*e**S(2) + (-a*f + c*d)**S(2), S(2))
        rubi.append(544)
        return -Dist(S(1)/(S(2)*q), Int((-a*f + c*d + c*e*x - q)/((a + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x) + Dist(S(1)/(S(2)*q), Int((-a*f + c*d + c*e*x + q)/((a + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x)
    pattern544 = Pattern(Integral(S(1)/((x_**S(2)*WC('c', S(1)) + WC('a', S(0)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons394, cons414)
    rule544 = ReplacementRule(pattern544, With544)
    def With545(f, b, d, c, a, x):
        q = Rt(b**S(2)*d*f + (-a*f + c*d)**S(2), S(2))
        rubi.append(545)
        return -Dist(S(1)/(S(2)*q), Int((-a*f - b*f*x + c*d - q)/(sqrt(d + f*x**S(2))*(a + b*x + c*x**S(2))), x), x) + Dist(S(1)/(S(2)*q), Int((-a*f - b*f*x + c*d + q)/(sqrt(d + f*x**S(2))*(a + b*x + c*x**S(2))), x), x)
    pattern545 = Pattern(Integral(S(1)/(sqrt(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons125, cons226, cons413)
    rule545 = ReplacementRule(pattern545, With545)
    pattern546 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))/(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons226, cons394)
    def replacement546(f, b, d, c, a, x, e):
        rubi.append(546)
        return -Dist(S(1)/f, Int((-a*f + c*d + x*(-b*f + c*e))/(sqrt(a + b*x + c*x**S(2))*(d + e*x + f*x**S(2))), x), x) + Dist(c/f, Int(S(1)/sqrt(a + b*x + c*x**S(2)), x), x)
    rule546 = ReplacementRule(pattern546, replacement546)
    pattern547 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))/(d_ + x_**S(2)*WC('f', S(1))), x_), cons2, cons3, cons7, cons27, cons125, cons226)
    def replacement547(f, b, d, c, a, x):
        rubi.append(547)
        return -Dist(S(1)/f, Int((-a*f - b*f*x + c*d)/((d + f*x**S(2))*sqrt(a + b*x + c*x**S(2))), x), x) + Dist(c/f, Int(S(1)/sqrt(a + b*x + c*x**S(2)), x), x)
    rule547 = ReplacementRule(pattern547, replacement547)
    pattern548 = Pattern(Integral(sqrt(a_ + x_**S(2)*WC('c', S(1)))/(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1))), x_), cons2, cons7, cons27, cons48, cons125, cons394)
    def replacement548(f, d, c, a, x, e):
        rubi.append(548)
        return -Dist(S(1)/f, Int((-a*f + c*d + c*e*x)/(sqrt(a + c*x**S(2))*(d + e*x + f*x**S(2))), x), x) + Dist(c/f, Int(S(1)/sqrt(a + c*x**S(2)), x), x)
    rule548 = ReplacementRule(pattern548, replacement548)
    def With549(f, b, d, c, a, x, e):
        r = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(549)
        return Dist(sqrt(S(2)*a + x*(b + r))*sqrt(b + S(2)*c*x + r)/sqrt(a + b*x + c*x**S(2)), Int(S(1)/(sqrt(S(2)*a + x*(b + r))*sqrt(b + S(2)*c*x + r)*sqrt(d + e*x + f*x**S(2))), x), x)
    pattern549 = Pattern(Integral(S(1)/(sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons226, cons394)
    rule549 = ReplacementRule(pattern549, With549)
    def With550(f, b, d, c, a, x):
        r = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(550)
        return Dist(sqrt(S(2)*a + x*(b + r))*sqrt(b + S(2)*c*x + r)/sqrt(a + b*x + c*x**S(2)), Int(S(1)/(sqrt(S(2)*a + x*(b + r))*sqrt(d + f*x**S(2))*sqrt(b + S(2)*c*x + r)), x), x)
    pattern550 = Pattern(Integral(S(1)/(sqrt(d_ + x_**S(2)*WC('f', S(1)))*sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons226)
    rule550 = ReplacementRule(pattern550, With550)
    pattern551 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons415)
    def replacement551(p, f, b, d, c, a, x, q, e):
        rubi.append(551)
        return Int((a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x)
    rule551 = ReplacementRule(pattern551, replacement551)
    pattern552 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons7, cons27, cons48, cons125, cons5, cons50, cons416)
    def replacement552(p, f, d, c, a, x, q, e):
        rubi.append(552)
        return Int((a + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x)
    rule552 = ReplacementRule(pattern552, replacement552)
    pattern553 = Pattern(Integral((u_**S(2)*WC('c', S(1)) + u_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons5, cons50, cons68, cons69)
    def replacement553(p, u, f, b, d, c, a, x, q, e):
        rubi.append(553)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule553 = ReplacementRule(pattern553, replacement553)
    pattern554 = Pattern(Integral((u_**S(2)*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons5, cons50, cons68, cons69)
    def replacement554(p, u, f, d, a, c, x, q, e):
        rubi.append(554)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule554 = ReplacementRule(pattern554, replacement554)
    pattern555 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons382, cons383, cons384, cons385)
    def replacement555(p, m, g, b, f, d, c, a, x, h, q, e):
        rubi.append(555)
        return Dist((c/f)**p, Int((g + h*x)**m*(d + e*x + f*x**S(2))**(p + q), x), x)
    rule555 = ReplacementRule(pattern555, replacement555)
    pattern556 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons382, cons383, cons147, cons386, cons387)
    def replacement556(p, m, g, b, f, d, c, a, x, h, q, e):
        rubi.append(556)
        return Dist(a**IntPart(p)*d**(-IntPart(p))*(a + b*x + c*x**S(2))**FracPart(p)*(d + e*x + f*x**S(2))**(-FracPart(p)), Int((g + h*x)**m*(d + e*x + f*x**S(2))**(p + q), x), x)
    rule556 = ReplacementRule(pattern556, replacement556)
    pattern557 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons45)
    def replacement557(p, m, g, b, f, d, c, a, x, h, q, e):
        rubi.append(557)
        return Dist((S(4)*c)**(-IntPart(p))*(b + S(2)*c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((b + S(2)*c*x)**(S(2)*p)*(g + h*x)**m*(d + e*x + f*x**S(2))**q, x), x)
    rule557 = ReplacementRule(pattern557, replacement557)
    pattern558 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons21, cons5, cons50, cons45)
    def replacement558(p, m, g, b, f, d, c, a, x, h, q):
        rubi.append(558)
        return Dist((S(4)*c)**(-IntPart(p))*(b + S(2)*c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((b + S(2)*c*x)**(S(2)*p)*(d + f*x**S(2))**q*(g + h*x)**m, x), x)
    rule558 = ReplacementRule(pattern558, replacement558)
    pattern559 = Pattern(Integral((g_ + x_*WC('h', S(1)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons417, cons418, cons17)
    def replacement559(p, m, f, b, g, d, c, a, x, h, e):
        rubi.append(559)
        return Int((f*h*x/c + d*g/a)**m*(a + b*x + c*x**S(2))**(m + p), x)
    rule559 = ReplacementRule(pattern559, replacement559)
    pattern560 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(g_ + x_*WC('h', S(1)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons419, cons418, cons17)
    def replacement560(p, m, f, g, d, c, a, x, h, e):
        rubi.append(560)
        return Int((a + c*x**S(2))**(m + p)*(f*h*x/c + d*g/a)**m, x)
    rule560 = ReplacementRule(pattern560, replacement560)
    pattern561 = Pattern(Integral((g_ + x_*WC('h', S(1)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))**WC('m', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons5, cons417, cons420, cons17)
    def replacement561(p, m, f, b, g, d, c, a, x, h):
        rubi.append(561)
        return Int((f*h*x/c + d*g/a)**m*(a + b*x + c*x**S(2))**(m + p), x)
    rule561 = ReplacementRule(pattern561, replacement561)
    pattern562 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(g_ + x_*WC('h', S(1)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons5, cons419, cons420, cons17)
    def replacement562(p, m, f, g, d, c, a, x, h):
        rubi.append(562)
        return Int((a + c*x**S(2))**(m + p)*(f*h*x/c + d*g/a)**m, x)
    rule562 = ReplacementRule(pattern562, replacement562)
    pattern563 = Pattern(Integral(x_**WC('p', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons48, cons125, cons50, cons226, cons421, cons38)
    def replacement563(p, f, b, c, a, x, q, e):
        rubi.append(563)
        return Int((a/e + c*x/f)**p*(e*x + f*x**S(2))**(p + q), x)
    rule563 = ReplacementRule(pattern563, replacement563)
    pattern564 = Pattern(Integral(x_**WC('p', S(1))*(a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons7, cons48, cons125, cons50, cons422, cons38)
    def replacement564(p, f, c, a, x, q, e):
        rubi.append(564)
        return Int((a/e + c*x/f)**p*(e*x + f*x**S(2))**(p + q), x)
    rule564 = ReplacementRule(pattern564, replacement564)
    pattern565 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons423, cons424, cons270)
    def replacement565(p, m, g, b, f, d, a, c, x, h, e):
        rubi.append(565)
        return Simp(f*(g + h*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*h*(m + S(2)*p + S(3))), x)
    rule565 = ReplacementRule(pattern565, replacement565)
    pattern566 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons425, cons426, cons270)
    def replacement566(p, m, g, f, d, c, a, x, h, e):
        rubi.append(566)
        return Simp(f*(a + c*x**S(2))**(p + S(1))*(g + h*x)**(m + S(1))/(c*h*(m + S(2)*p + S(3))), x)
    rule566 = ReplacementRule(pattern566, replacement566)
    pattern567 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))*(x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons21, cons5, cons427, cons424, cons270)
    def replacement567(p, m, g, b, f, d, a, c, x, h):
        rubi.append(567)
        return Simp(f*(g + h*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*h*(m + S(2)*p + S(3))), x)
    rule567 = ReplacementRule(pattern567, replacement567)
    pattern568 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons226, cons394, cons428)
    def replacement568(p, m, g, b, f, d, a, c, x, h, e):
        rubi.append(568)
        return Int(ExpandIntegrand((g + h*x)**m*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2)), x), x)
    rule568 = ReplacementRule(pattern568, replacement568)
    pattern569 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons394, cons428)
    def replacement569(p, m, g, f, d, c, a, x, h, e):
        rubi.append(569)
        return Int(ExpandIntegrand((a + c*x**S(2))**p*(g + h*x)**m*(d + e*x + f*x**S(2)), x), x)
    rule569 = ReplacementRule(pattern569, replacement569)
    pattern570 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))*(x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons21, cons226, cons428)
    def replacement570(p, m, g, b, f, d, a, c, x, h):
        rubi.append(570)
        return Int(ExpandIntegrand((d + f*x**S(2))*(g + h*x)**m*(a + b*x + c*x**S(2))**p, x), x)
    rule570 = ReplacementRule(pattern570, replacement570)
    pattern571 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(g_ + x_*WC('h', S(1)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons21, cons428)
    def replacement571(p, m, f, g, d, c, a, x, h):
        rubi.append(571)
        return Int(ExpandIntegrand((a + c*x**S(2))**p*(d + f*x**S(2))*(g + h*x)**m, x), x)
    rule571 = ReplacementRule(pattern571, replacement571)
    pattern572 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons226, cons394, cons31, cons94, cons429)
    def replacement572(p, m, g, b, f, d, a, c, x, h, e):
        rubi.append(572)
        return Dist(S(1)/(h*(m + S(1))*(a*h**S(2) - b*g*h + c*g**S(2))), Int((g + h*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*Simp(-b*(f*g**S(2)*(p + S(1)) - h*(-d*h*(m + p + S(2)) + e*g*(p + S(1)))) + h*(m + S(1))*(a*e*h - a*f*g + c*d*g) - x*(c*(S(2)*f*g**S(2)*(p + S(1)) - h*(-d*h + e*g)*(m + S(2)*p + S(3))) + f*h*(m + S(1))*(-a*h + b*g)), x), x), x) + Simp((g + h*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(d*h**S(2) - e*g*h + f*g**S(2))/(h*(m + S(1))*(a*h**S(2) - b*g*h + c*g**S(2))), x)
    rule572 = ReplacementRule(pattern572, replacement572)
    pattern573 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))**m_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons394, cons31, cons94, cons430)
    def replacement573(p, m, g, f, d, c, a, x, h, e):
        rubi.append(573)
        return Dist(S(1)/(h*(m + S(1))*(a*h**S(2) + c*g**S(2))), Int((a + c*x**S(2))**p*(g + h*x)**(m + S(1))*Simp(h*(m + S(1))*(a*e*h - a*f*g + c*d*g) + x*(a*f*h**S(2)*(m + S(1)) - c*(S(2)*f*g**S(2)*(p + S(1)) - h*(-d*h + e*g)*(m + S(2)*p + S(3)))), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(g + h*x)**(m + S(1))*(d*h**S(2) - e*g*h + f*g**S(2))/(h*(m + S(1))*(a*h**S(2) + c*g**S(2))), x)
    rule573 = ReplacementRule(pattern573, replacement573)
    pattern574 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**m_*(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons5, cons226, cons31, cons94, cons429)
    def replacement574(p, m, g, b, f, d, a, c, x, h):
        rubi.append(574)
        return Dist(S(1)/(h*(m + S(1))*(a*h**S(2) - b*g*h + c*g**S(2))), Int((g + h*x)**(m + S(1))*(a + b*x + c*x**S(2))**p*Simp(-b*(d*h**S(2)*(m + p + S(2)) + f*g**S(2)*(p + S(1))) + h*(m + S(1))*(-a*f*g + c*d*g) - x*(c*(d*h**S(2)*(m + S(2)*p + S(3)) + S(2)*f*g**S(2)*(p + S(1))) + f*h*(m + S(1))*(-a*h + b*g)), x), x), x) + Simp((g + h*x)**(m + S(1))*(d*h**S(2) + f*g**S(2))*(a + b*x + c*x**S(2))**(p + S(1))/(h*(m + S(1))*(a*h**S(2) - b*g*h + c*g**S(2))), x)
    rule574 = ReplacementRule(pattern574, replacement574)
    pattern575 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(g_ + x_*WC('h', S(1)))**m_*(x_**S(2)*WC('f', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons5, cons31, cons94, cons430)
    def replacement575(p, m, f, g, d, c, a, x, h):
        rubi.append(575)
        return Dist(S(1)/(h*(m + S(1))*(a*h**S(2) + c*g**S(2))), Int((a + c*x**S(2))**p*(g + h*x)**(m + S(1))*Simp(h*(m + S(1))*(-a*f*g + c*d*g) + x*(a*f*h**S(2)*(m + S(1)) - c*(d*h**S(2)*(m + S(2)*p + S(3)) + S(2)*f*g**S(2)*(p + S(1)))), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(g + h*x)**(m + S(1))*(d*h**S(2) + f*g**S(2))/(h*(m + S(1))*(a*h**S(2) + c*g**S(2))), x)
    rule575 = ReplacementRule(pattern575, replacement575)
    pattern576 = Pattern(Integral((x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))/((x_*WC('h', S(1)) + WC('g', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**(S(3)/2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons429)
    def replacement576(g, b, f, d, a, c, x, h, e):
        rubi.append(576)
        return Dist((d*h**S(2) - e*g*h + f*g**S(2))/(a*h**S(2) - b*g*h + c*g**S(2)), Int(S(1)/((g + h*x)*sqrt(a + b*x + c*x**S(2))), x), x) + Dist(S(1)/(a*h**S(2) - b*g*h + c*g**S(2)), Int((a*e*h - a*f*g - b*d*h + c*d*g + x*(a*f*h - b*f*g - c*d*h + c*e*g))/(a + b*x + c*x**S(2))**(S(3)/2), x), x)
    rule576 = ReplacementRule(pattern576, replacement576)
    pattern577 = Pattern(Integral((x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))/((a_ + x_**S(2)*WC('c', S(1)))**(S(3)/2)*(x_*WC('h', S(1)) + WC('g', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons394, cons430)
    def replacement577(g, f, d, c, a, x, h, e):
        rubi.append(577)
        return Dist((d*h**S(2) - e*g*h + f*g**S(2))/(a*h**S(2) + c*g**S(2)), Int(S(1)/(sqrt(a + c*x**S(2))*(g + h*x)), x), x) + Dist(S(1)/(a*h**S(2) + c*g**S(2)), Int((a*e*h - a*f*g + c*d*g + x*(a*f*h - c*d*h + c*e*g))/(a + c*x**S(2))**(S(3)/2), x), x)
    rule577 = ReplacementRule(pattern577, replacement577)
    pattern578 = Pattern(Integral((x_**S(2)*WC('f', S(1)) + WC('d', S(0)))/((x_*WC('h', S(1)) + WC('g', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**(S(3)/2)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons226, cons429)
    def replacement578(g, b, f, d, a, c, x, h):
        rubi.append(578)
        return Dist((d*h**S(2) + f*g**S(2))/(a*h**S(2) - b*g*h + c*g**S(2)), Int(S(1)/((g + h*x)*sqrt(a + b*x + c*x**S(2))), x), x) + Dist(S(1)/(a*h**S(2) - b*g*h + c*g**S(2)), Int((-a*f*g - b*d*h + c*d*g - x*(-a*f*h + b*f*g + c*d*h))/(a + b*x + c*x**S(2))**(S(3)/2), x), x)
    rule578 = ReplacementRule(pattern578, replacement578)
    pattern579 = Pattern(Integral((x_**S(2)*WC('f', S(1)) + WC('d', S(0)))/((a_ + x_**S(2)*WC('c', S(1)))**(S(3)/2)*(g_ + x_*WC('h', S(1)))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons430)
    def replacement579(f, g, d, c, a, x, h):
        rubi.append(579)
        return Dist((d*h**S(2) + f*g**S(2))/(a*h**S(2) + c*g**S(2)), Int(S(1)/(sqrt(a + c*x**S(2))*(g + h*x)), x), x) + Dist(S(1)/(a*h**S(2) + c*g**S(2)), Int((-a*f*g + c*d*g - x*(-a*f*h + c*d*h))/(a + c*x**S(2))**(S(3)/2), x), x)
    rule579 = ReplacementRule(pattern579, replacement579)
    pattern580 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**m_*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons244, cons137, cons166)
    def replacement580(p, m, g, b, f, d, a, c, x, h, e):
        rubi.append(580)
        return -Dist(S(1)/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), Int((g + h*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*Simp(g*(c*(S(2)*p + S(3))*(-b*e + S(2)*c*d) - f*(S(2)*a*c - b**S(2)*(p + S(2)))) + h*m*(a*b*f - S(2)*a*c*e + b*c*d) + h*x*(c*(-b*e + S(2)*c*d)*(m + S(2)*p + S(3)) - f*(S(2)*a*c*(m + S(1)) - b**S(2)*(m + p + S(2)))), x), x), x) + Simp((g + h*x)**m*(a + b*x + c*x**S(2))**(p + S(1))*(a*b*f - S(2)*a*c*e + b*c*d + x*(c*(-b*e + S(2)*c*d) + f*(-S(2)*a*c + b**S(2))))/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule580 = ReplacementRule(pattern580, replacement580)
    pattern581 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('h', S(1)) + WC('g', S(0)))**m_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons394, cons244, cons137, cons166)
    def replacement581(p, m, g, f, d, c, a, x, h, e):
        rubi.append(581)
        return -Dist(S(1)/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(g + h*x)**(m + S(-1))*Simp(a*(e*h*m + f*g) - c*d*g*(S(2)*p + S(3)) + h*x*(a*f*(m + S(1)) - c*d*(m + S(2)*p + S(3))), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(g + h*x)**m*(a*e - x*(-a*f + c*d))/(S(2)*a*c*(p + S(1))), x)
    rule581 = ReplacementRule(pattern581, replacement581)
    pattern582 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**m_*(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons226, cons244, cons137, cons166)
    def replacement582(p, m, g, b, f, d, a, c, x, h):
        rubi.append(582)
        return -Dist(S(1)/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), Int((g + h*x)**(m + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*Simp(g*(S(2)*c**S(2)*d*(S(2)*p + S(3)) - f*(S(2)*a*c - b**S(2)*(p + S(2)))) + h*m*(a*b*f + b*c*d) + h*x*(S(2)*c**S(2)*d*(m + S(2)*p + S(3)) - f*(S(2)*a*c*(m + S(1)) - b**S(2)*(m + p + S(2)))), x), x), x) + Simp((g + h*x)**m*(a + b*x + c*x**S(2))**(p + S(1))*(a*b*f + b*c*d + x*(S(2)*c**S(2)*d + f*(-S(2)*a*c + b**S(2))))/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule582 = ReplacementRule(pattern582, replacement582)
    pattern583 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(g_ + x_*WC('h', S(1)))**m_*(x_**S(2)*WC('f', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons244, cons137, cons166)
    def replacement583(p, m, f, g, d, c, a, x, h):
        rubi.append(583)
        return -Dist(S(1)/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(g + h*x)**(m + S(-1))*Simp(a*f*g - c*d*g*(S(2)*p + S(3)) + h*x*(a*f*(m + S(1)) - c*d*(m + S(2)*p + S(3))), x), x), x) - Simp(x*(a + c*x**S(2))**(p + S(1))*(g + h*x)**m*(-a*f + c*d)/(S(2)*a*c*(p + S(1))), x)
    rule583 = ReplacementRule(pattern583, replacement583)
    pattern584 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons226, cons394, cons13, cons137, cons431)
    def replacement584(p, m, g, b, f, d, a, c, x, h, e):
        rubi.append(584)
        return -Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(c*g**S(2) - h*(-a*h + b*g))), Int((g + h*x)**m*(a + b*x + c*x**S(2))**(p + S(1))*Simp(g*(p + S(2))*(-S(2)*a*(-c*e*h + c*f*g) + b**S(2)*f*g - b*(a*f*h + c*d*h + c*e*g) + S(2)*c**S(2)*d*g) + h*x*(m + S(2)*p + S(4))*(-S(2)*a*(-c*e*h + c*f*g) + b**S(2)*f*g - b*(a*f*h + c*d*h + c*e*g) + S(2)*c**S(2)*d*g) - h*(-(-a*e + b*d)*(-b*h + S(2)*c*g) + (-a*f + c*d)*(-S(2)*a*h + b*g))*(m + p + S(2)) + (p + S(1))*(c*g**S(2) - h*(-a*h + b*g))*(S(2)*a*f - b*e + S(2)*c*d), x), x), x) - Simp((g + h*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(-x*(b*f*(-a*h + b*g) + S(2)*c**S(2)*d*g - c*(-S(2)*a*e*h + S(2)*a*f*g + b*d*h + b*e*g)) - (-a*e + b*d)*(-b*h + S(2)*c*g) + (-a*f + c*d)*(-S(2)*a*h + b*g))/((p + S(1))*(-S(4)*a*c + b**S(2))*(c*g**S(2) - h*(-a*h + b*g))), x)
    rule584 = ReplacementRule(pattern584, replacement584)
    pattern585 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons394, cons13, cons137, cons430)
    def replacement585(p, m, g, f, d, c, a, x, h, e):
        rubi.append(585)
        return Dist(S(1)/(S(2)*a*c*(p + S(1))*(a*h**S(2) + c*g**S(2))), Int((a + c*x**S(2))**(p + S(1))*(g + h*x)**m*Simp(g*(p + S(2))*(-a*(-c*e*h + c*f*g) + c**S(2)*d*g) + h*x*(-a*(-c*e*h + c*f*g) + c**S(2)*d*g)*(m + S(2)*p + S(4)) - h*(a*c*e*g - a*h*(-a*f + c*d))*(m + p + S(2)) + (p + S(1))*(a*f + c*d)*(a*h**S(2) + c*g**S(2)), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(g + h*x)**(m + S(1))*(a*c*e*g - a*h*(-a*f + c*d) - c*x*(a*e*h - a*f*g + c*d*g))/(S(2)*a*c*(p + S(1))*(a*h**S(2) + c*g**S(2))), x)
    rule585 = ReplacementRule(pattern585, replacement585)
    pattern586 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons21, cons226, cons13, cons137, cons431)
    def replacement586(p, m, g, b, f, d, a, c, x, h):
        rubi.append(586)
        return -Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(c*g**S(2) - h*(-a*h + b*g))), Int((g + h*x)**m*(a + b*x + c*x**S(2))**(p + S(1))*Simp(g*(p + S(2))*(-S(2)*a*c*f*g + b**S(2)*f*g - b*(a*f*h + c*d*h) + S(2)*c**S(2)*d*g) + h*x*(m + S(2)*p + S(4))*(-S(2)*a*c*f*g + b**S(2)*f*g - b*(a*f*h + c*d*h) + S(2)*c**S(2)*d*g) - h*(-b*d*(-b*h + S(2)*c*g) + (-a*f + c*d)*(-S(2)*a*h + b*g))*(m + p + S(2)) + S(2)*(p + S(1))*(a*f + c*d)*(c*g**S(2) - h*(-a*h + b*g)), x), x), x) - Simp((g + h*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(-b*d*(-b*h + S(2)*c*g) - x*(b*f*(-a*h + b*g) + S(2)*c**S(2)*d*g - c*(S(2)*a*f*g + b*d*h)) + (-a*f + c*d)*(-S(2)*a*h + b*g))/((p + S(1))*(-S(4)*a*c + b**S(2))*(c*g**S(2) - h*(-a*h + b*g))), x)
    rule586 = ReplacementRule(pattern586, replacement586)
    pattern587 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**p_*(g_ + x_*WC('h', S(1)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons21, cons13, cons137, cons430)
    def replacement587(p, m, f, g, d, c, a, x, h):
        rubi.append(587)
        return Dist(S(1)/(S(2)*a*c*(p + S(1))*(a*h**S(2) + c*g**S(2))), Int((a + c*x**S(2))**(p + S(1))*(g + h*x)**m*Simp(a*h**S(2)*(-a*f + c*d)*(m + p + S(2)) + g*(p + S(2))*(-a*c*f*g + c**S(2)*d*g) + h*x*(-a*c*f*g + c**S(2)*d*g)*(m + S(2)*p + S(4)) + (p + S(1))*(a*f + c*d)*(a*h**S(2) + c*g**S(2)), x), x), x) - Simp((a + c*x**S(2))**(p + S(1))*(g + h*x)**(m + S(1))*(a*h*(-a*f + c*d) + c*x*(-a*f*g + c*d*g))/(S(2)*a*c*(p + S(1))*(a*h**S(2) + c*g**S(2))), x)
    rule587 = ReplacementRule(pattern587, replacement587)
    pattern588 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons226, cons394, cons242)
    def replacement588(p, m, g, b, f, d, a, c, x, h, e):
        rubi.append(588)
        return -Dist(h**(S(-2)), Int((g + h*x)**m*(a + b*x + c*x**S(2))**p*(-d*h**S(2) + f*g**S(2) + h*x*(-e*h + S(2)*f*g)), x), x) + Dist(f/h**S(2), Int((g + h*x)**(m + S(2))*(a + b*x + c*x**S(2))**p, x), x)
    rule588 = ReplacementRule(pattern588, replacement588)
    pattern589 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons394, cons242)
    def replacement589(p, m, g, f, d, c, a, x, h, e):
        rubi.append(589)
        return -Dist(h**(S(-2)), Int((a + c*x**S(2))**p*(g + h*x)**m*(-d*h**S(2) + f*g**S(2) + h*x*(-e*h + S(2)*f*g)), x), x) + Dist(f/h**S(2), Int((a + c*x**S(2))**p*(g + h*x)**(m + S(2)), x), x)
    rule589 = ReplacementRule(pattern589, replacement589)
    pattern590 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons21, cons5, cons226, cons242)
    def replacement590(p, m, g, b, f, d, a, c, x, h):
        rubi.append(590)
        return -Dist(h**(S(-2)), Int((g + h*x)**m*(a + b*x + c*x**S(2))**p*(-d*h**S(2) + f*g**S(2) + S(2)*f*g*h*x), x), x) + Dist(f/h**S(2), Int((g + h*x)**(m + S(2))*(a + b*x + c*x**S(2))**p, x), x)
    rule590 = ReplacementRule(pattern590, replacement590)
    pattern591 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(g_ + x_*WC('h', S(1)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons21, cons5, cons242)
    def replacement591(p, m, f, g, d, c, a, x, h):
        rubi.append(591)
        return -Dist(h**(S(-2)), Int((a + c*x**S(2))**p*(g + h*x)**m*(-d*h**S(2) + f*g**S(2) + S(2)*f*g*h*x), x), x) + Dist(f/h**S(2), Int((a + c*x**S(2))**p*(g + h*x)**(m + S(2)), x), x)
    rule591 = ReplacementRule(pattern591, replacement591)
    pattern592 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons226, cons394, cons270)
    def replacement592(p, m, g, b, f, d, a, c, x, h, e):
        rubi.append(592)
        return -Dist(S(1)/(c*h*(m + S(2)*p + S(3))), Int((g + h*x)**m*(a + b*x + c*x**S(2))**p*Simp(b*f*g*(p + S(1)) + h*(a*f*(m + S(1)) - c*d*(m + S(2)*p + S(3))) + x*(b*f*h*(m + p + S(2)) + c*(-e*h*(m + S(2)*p + S(3)) + S(2)*f*g*(p + S(1)))), x), x), x) + Simp(f*(g + h*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*h*(m + S(2)*p + S(3))), x)
    rule592 = ReplacementRule(pattern592, replacement592)
    pattern593 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons394, cons270)
    def replacement593(p, m, g, f, d, c, a, x, h, e):
        rubi.append(593)
        return -Dist(S(1)/(c*h*(m + S(2)*p + S(3))), Int((a + c*x**S(2))**p*(g + h*x)**m*Simp(c*x*(-e*h*(m + S(2)*p + S(3)) + S(2)*f*g*(p + S(1))) + h*(a*f*(m + S(1)) - c*d*(m + S(2)*p + S(3))), x), x), x) + Simp(f*(a + c*x**S(2))**(p + S(1))*(g + h*x)**(m + S(1))/(c*h*(m + S(2)*p + S(3))), x)
    rule593 = ReplacementRule(pattern593, replacement593)
    pattern594 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))*(x_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons21, cons5, cons226, cons270)
    def replacement594(p, m, g, b, f, d, a, c, x, h):
        rubi.append(594)
        return -Dist(S(1)/(c*h*(m + S(2)*p + S(3))), Int((g + h*x)**m*(a + b*x + c*x**S(2))**p*Simp(b*f*g*(p + S(1)) + f*x*(b*h*(m + p + S(2)) + S(2)*c*g*(p + S(1))) + h*(a*f*(m + S(1)) - c*d*(m + S(2)*p + S(3))), x), x), x) + Simp(f*(g + h*x)**(m + S(1))*(a + b*x + c*x**S(2))**(p + S(1))/(c*h*(m + S(2)*p + S(3))), x)
    rule594 = ReplacementRule(pattern594, replacement594)
    pattern595 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)))*(g_ + x_*WC('h', S(1)))**WC('m', S(1)), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons21, cons5, cons270)
    def replacement595(p, m, f, g, d, c, a, x, h):
        rubi.append(595)
        return -Dist(S(1)/(c*h*(m + S(2)*p + S(3))), Int((a + c*x**S(2))**p*(g + h*x)**m*Simp(S(2)*c*f*g*x*(p + S(1)) + h*(a*f*(m + S(1)) - c*d*(m + S(2)*p + S(3))), x), x), x) + Simp(f*(a + c*x**S(2))**(p + S(1))*(g + h*x)**(m + S(1))/(c*h*(m + S(2)*p + S(3))), x)
    rule595 = ReplacementRule(pattern595, replacement595)
    pattern596 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons220, cons163)
    def replacement596(p, g, b, f, d, c, a, x, h, q, e):
        rubi.append(596)
        return Int(ExpandIntegrand((g + h*x)*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x)
    rule596 = ReplacementRule(pattern596, replacement596)
    pattern597 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons394, cons220, cons432)
    def replacement597(p, g, f, d, c, a, x, h, q, e):
        rubi.append(597)
        return Int(ExpandIntegrand((a + c*x**S(2))**p*(g + h*x)*(d + e*x + f*x**S(2))**q, x), x)
    rule597 = ReplacementRule(pattern597, replacement597)
    pattern598 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons402, cons137, cons403)
    def replacement598(p, g, b, f, d, c, a, x, h, q, e):
        rubi.append(598)
        return -Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(-1))*Simp(-d*(S(2)*p + S(3))*(b*h - S(2)*c*g) + e*q*(-S(2)*a*h + b*g) - f*x**S(2)*(b*h - S(2)*c*g)*(S(2)*p + S(2)*q + S(3)) + x*(-e*(b*h - S(2)*c*g)*(S(2)*p + q + S(3)) + S(2)*f*q*(-S(2)*a*h + b*g)), x), x), x) + Simp((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*(-S(2)*a*h + b*g - x*(b*h - S(2)*c*g))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule598 = ReplacementRule(pattern598, replacement598)
    pattern599 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons394, cons402, cons137, cons403)
    def replacement599(p, g, f, d, c, a, x, h, q, e):
        rubi.append(599)
        return Dist(S(1)/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(-1))*Simp(-a*e*h*q + c*d*g*(S(2)*p + S(3)) + c*f*g*x**S(2)*(S(2)*p + S(2)*q + S(3)) + x*(-S(2)*a*f*h*q + c*e*g*(S(2)*p + q + S(3))), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(a*h - c*g*x)*(d + e*x + f*x**S(2))**q/(S(2)*a*c*(p + S(1))), x)
    rule599 = ReplacementRule(pattern599, replacement599)
    pattern600 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons226, cons402, cons137, cons403)
    def replacement600(p, g, b, f, d, c, a, x, h, q):
        rubi.append(600)
        return -Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + f*x**S(2))**(q + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*Simp(-d*(S(2)*p + S(3))*(b*h - S(2)*c*g) + S(2)*f*q*x*(-S(2)*a*h + b*g) - f*x**S(2)*(b*h - S(2)*c*g)*(S(2)*p + S(2)*q + S(3)), x), x), x) + Simp((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(1))*(-S(2)*a*h + b*g - x*(b*h - S(2)*c*g))/((p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule600 = ReplacementRule(pattern600, replacement600)
    pattern601 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons50, cons226, cons394, cons13, cons137, cons404, cons405)
    def replacement601(p, g, b, f, d, c, a, x, h, q, e):
        rubi.append(601)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*Simp(-c*f*x**S(2)*(S(2)*p + S(2)*q + S(5))*(S(2)*a*c*e*h + b**S(2)*f*g - b*(a*f*h + c*d*h + c*e*g) + S(2)*c*g*(-a*f + c*d)) - e*(c*g*(S(2)*a*c*e - b*(a*f + c*d)) + (-a*h + b*g)*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)))*(p + q + S(2)) - x*(S(2)*f*(c*g*(S(2)*a*c*e - b*(a*f + c*d)) + (-a*h + b*g)*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)))*(p + q + S(2)) - (b*f*(p + S(1)) - c*e*(S(2)*p + q + S(4)))*(S(2)*a*c*e*h + b**S(2)*f*g - b*(a*f*h + c*d*h + c*e*g) + S(2)*c*g*(-a*f + c*d))) + (p + S(1))*(b*h - S(2)*c*g)*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2)) + (a*f*(p + S(1)) - c*d*(p + S(2)))*(S(2)*a*c*e*h + b**S(2)*f*g - b*(a*f*h + c*d*h + c*e*g) + S(2)*c*g*(-a*f + c*d)), x), x), x) + Simp((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(1))*(c*g*(S(2)*a*c*e - b*(a*f + c*d)) + c*x*(g*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) - h*(a*b*f - S(2)*a*c*e + b*c*d)) + (-a*h + b*g)*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)))/((p + S(1))*(-S(4)*a*c + b**S(2))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2))), x)
    rule601 = ReplacementRule(pattern601, replacement601)
    pattern602 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons50, cons394, cons13, cons137, cons407, cons405)
    def replacement602(p, g, f, d, c, a, x, h, q, e):
        rubi.append(602)
        return Dist(-S(1)/(S(4)*a*c*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*Simp(-c*f*x**S(2)*(S(2)*a*c*e*h + S(2)*c*g*(-a*f + c*d))*(S(2)*p + S(2)*q + S(5)) - S(2)*c*g*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2)) - e*(S(2)*a*c**S(2)*e*g - a*h*(-S(2)*a*c*f + S(2)*c**S(2)*d))*(p + q + S(2)) - x*(c*e*(S(2)*a*c*e*h + S(2)*c*g*(-a*f + c*d))*(S(2)*p + q + S(4)) + S(2)*f*(S(2)*a*c**S(2)*e*g - a*h*(-S(2)*a*c*f + S(2)*c**S(2)*d))*(p + q + S(2))) + (a*f*(p + S(1)) - c*d*(p + S(2)))*(S(2)*a*c*e*h + S(2)*c*g*(-a*f + c*d)), x), x), x) + Simp(-(a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(1))*(S(2)*a*c**S(2)*e*g - a*h*(-S(2)*a*c*f + S(2)*c**S(2)*d) + c*x*(S(2)*a*c*e*h + g*(-S(2)*a*c*f + S(2)*c**S(2)*d)))/(S(4)*a*c*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2))), x)
    rule602 = ReplacementRule(pattern602, replacement602)
    pattern603 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons50, cons226, cons13, cons137, cons406, cons405)
    def replacement603(p, g, b, f, d, c, a, x, h, q):
        rubi.append(603)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(b**S(2)*d*f + (-a*f + c*d)**S(2))), Int((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(1))*Simp(-c*f*x**S(2)*(S(2)*p + S(2)*q + S(5))*(b**S(2)*f*g - b*(a*f*h + c*d*h) + S(2)*c*g*(-a*f + c*d)) - x*(-b*f*(p + S(1))*(b**S(2)*f*g - b*(a*f*h + c*d*h) + S(2)*c*g*(-a*f + c*d)) + S(2)*f*(-b*c*g*(a*f + c*d) + (-a*h + b*g)*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d))*(p + q + S(2))) + (p + S(1))*(b*h - S(2)*c*g)*(b**S(2)*d*f + (-a*f + c*d)**S(2)) + (a*f*(p + S(1)) - c*d*(p + S(2)))*(b**S(2)*f*g - b*(a*f*h + c*d*h) + S(2)*c*g*(-a*f + c*d)), x), x), x) + Simp((d + f*x**S(2))**(q + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(-b*c*g*(a*f + c*d) + c*x*(g*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d) - h*(a*b*f + b*c*d)) + (-a*h + b*g)*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d))/((p + S(1))*(-S(4)*a*c + b**S(2))*(b**S(2)*d*f + (-a*f + c*d)**S(2))), x)
    rule603 = ReplacementRule(pattern603, replacement603)
    pattern604 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons50, cons226, cons394, cons13, cons163, cons433)
    def replacement604(p, g, b, f, d, c, a, x, h, q, e):
        rubi.append(604)
        return -Dist(S(1)/(S(2)*f*(p + q + S(1))), Int((a + b*x + c*x**S(2))**(p + S(-1))*(d + e*x + f*x**S(2))**q*Simp(a*(e*h - S(2)*f*g)*(p + q + S(1)) + h*p*(-a*e + b*d) + x**S(2)*(c*(e*h - S(2)*f*g)*(p + q + S(1)) + h*p*(-b*f + c*e)) + x*(b*(e*h - S(2)*f*g)*(p + q + S(1)) + S(2)*h*p*(-a*f + c*d)), x), x), x) + Simp(h*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**(q + S(1))/(S(2)*f*(p + q + S(1))), x)
    rule604 = ReplacementRule(pattern604, replacement604)
    pattern605 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons50, cons394, cons13, cons163, cons433)
    def replacement605(p, g, f, d, c, a, x, h, q, e):
        rubi.append(605)
        return Dist(S(1)/(S(2)*f*(p + q + S(1))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x + f*x**S(2))**q*Simp(a*e*h*p - a*(e*h - S(2)*f*g)*(p + q + S(1)) - S(2)*h*p*x*(-a*f + c*d) - x**S(2)*(c*e*h*p + c*(e*h - S(2)*f*g)*(p + q + S(1))), x), x), x) + Simp(h*(a + c*x**S(2))**p*(d + e*x + f*x**S(2))**(q + S(1))/(S(2)*f*(p + q + S(1))), x)
    rule605 = ReplacementRule(pattern605, replacement605)
    pattern606 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(x_*WC('h', S(1)) + WC('g', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons50, cons226, cons13, cons163, cons433)
    def replacement606(p, g, b, f, d, c, a, x, h, q):
        rubi.append(606)
        return -Dist(S(1)/(S(2)*f*(p + q + S(1))), Int((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(-1))*Simp(-S(2)*a*f*g*(p + q + S(1)) + b*d*h*p + x**S(2)*(-b*f*h*p - S(2)*c*f*g*(p + q + S(1))) + x*(-S(2)*b*f*g*(p + q + S(1)) + S(2)*h*p*(-a*f + c*d)), x), x), x) + Simp(h*(d + f*x**S(2))**(q + S(1))*(a + b*x + c*x**S(2))**p/(S(2)*f*(p + q + S(1))), x)
    rule606 = ReplacementRule(pattern606, replacement606)
    def With607(g, b, f, d, c, a, x, h, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = a**S(2)*f**S(2) - a*b*e*f - S(2)*a*c*d*f + a*c*e**S(2) + b**S(2)*d*f - b*c*d*e + c**S(2)*d**S(2)
        if NonzeroQ(q):
            return True
        return False
    pattern607 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, CustomConstraint(With607))
    def replacement607(g, b, f, d, c, a, x, h, e):

        q = a**S(2)*f**S(2) - a*b*e*f - S(2)*a*c*d*f + a*c*e**S(2) + b**S(2)*d*f - b*c*d*e + c**S(2)*d**S(2)
        rubi.append(607)
        return Dist(S(1)/q, Int(Simp(-a*b*f*h + a*c*e*h - a*c*f*g + b**S(2)*f*g - b*c*e*g + c**S(2)*d*g + c*x*(-a*f*h + b*f*g + c*d*h - c*e*g), x)/(a + b*x + c*x**S(2)), x), x) + Dist(S(1)/q, Int(Simp(a*f**S(2)*g + b*d*f*h - b*e*f*g - c*d*e*h - c*d*f*g + c*e**S(2)*g - f*x*(-a*f*h + b*f*g + c*d*h - c*e*g), x)/(d + e*x + f*x**S(2)), x), x)
    rule607 = ReplacementRule(pattern607, replacement607)
    def With608(g, b, f, d, c, a, x, h):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = a**S(2)*f**S(2) - S(2)*a*c*d*f + b**S(2)*d*f + c**S(2)*d**S(2)
        if NonzeroQ(q):
            return True
        return False
    pattern608 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((d_ + x_**S(2)*WC('f', S(1)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons226, CustomConstraint(With608))
    def replacement608(g, b, f, d, c, a, x, h):

        q = a**S(2)*f**S(2) - S(2)*a*c*d*f + b**S(2)*d*f + c**S(2)*d**S(2)
        rubi.append(608)
        return Dist(S(1)/q, Int(Simp(a*f**S(2)*g + b*d*f*h - c*d*f*g - f*x*(-a*f*h + b*f*g + c*d*h), x)/(d + f*x**S(2)), x), x) + Dist(S(1)/q, Int(Simp(-a*b*f*h - a*c*f*g + b**S(2)*f*g + c**S(2)*d*g + c*x*(-a*f*h + b*f*g + c*d*h), x)/(a + b*x + c*x**S(2)), x), x)
    rule608 = ReplacementRule(pattern608, replacement608)
    pattern609 = Pattern(Integral((g_ + x_*WC('h', S(1)))/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(d_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons434)
    def replacement609(f, g, d, c, a, x, h):
        rubi.append(609)
        return Dist(g, Int(S(1)/((a + c*x**S(2))*sqrt(d + f*x**S(2))), x), x) + Dist(h, Int(x/((a + c*x**S(2))*sqrt(d + f*x**S(2))), x), x)
    rule609 = ReplacementRule(pattern609, replacement609)
    def With610(f, g, d, c, a, x, h):
        q = Rt(-a*c, S(2))
        rubi.append(610)
        return -Dist((c*g - h*q)/(S(2)*q), Int(S(1)/(sqrt(d + f*x**S(2))*(c*x + q)), x), x) - Dist((c*g + h*q)/(S(2)*q), Int(S(1)/(sqrt(d + f*x**S(2))*(-c*x + q)), x), x)
    pattern610 = Pattern(Integral((g_ + x_*WC('h', S(1)))/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(d_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons435)
    rule610 = ReplacementRule(pattern610, With610)
    pattern611 = Pattern(Integral((g_ + x_*WC('h', S(1)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons410, cons436)
    def replacement611(f, b, g, d, c, a, x, h, e):
        rubi.append(611)
        return Dist(-S(2)*g, Subst(Int(S(1)/(-a*e + b*d - b*x**S(2)), x), x, sqrt(d + e*x + f*x**S(2))), x)
    rule611 = ReplacementRule(pattern611, replacement611)
    pattern612 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons410, cons437)
    def replacement612(g, b, f, d, c, a, x, h, e):
        rubi.append(612)
        return Dist(h/(S(2)*f), Int((e + S(2)*f*x)/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x) - Dist((e*h - S(2)*f*g)/(S(2)*f), Int(S(1)/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x)
    rule612 = ReplacementRule(pattern612, replacement612)
    pattern613 = Pattern(Integral(x_/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons226, cons394, cons383)
    def replacement613(f, b, d, c, a, x, e):
        rubi.append(613)
        return Dist(-S(2)*e, Subst(Int((-d*x**S(2) + S(1))/(-b*f + c*e + d**S(2)*x**S(4)*(-b*f + c*e) - e*x**S(2)*(S(2)*a*f - b*e + S(2)*c*d)), x), x, (S(1) + x*(e + sqrt(-S(4)*d*f + e**S(2)))/(S(2)*d))/sqrt(d + e*x + f*x**S(2))), x)
    rule613 = ReplacementRule(pattern613, replacement613)
    pattern614 = Pattern(Integral((g_ + x_*WC('h', S(1)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons383, cons438)
    def replacement614(f, b, g, d, c, a, x, h, e):
        rubi.append(614)
        return Dist(g, Subst(Int(S(1)/(a + x**S(2)*(-a*f + c*d)), x), x, x/sqrt(d + e*x + f*x**S(2))), x)
    rule614 = ReplacementRule(pattern614, replacement614)
    pattern615 = Pattern(Integral((g_ + x_*WC('h', S(1)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons383, cons439)
    def replacement615(f, b, g, d, c, a, x, h, e):
        rubi.append(615)
        return Dist(h/e, Int((S(2)*d + e*x)/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x) - Dist((S(2)*d*h - e*g)/e, Int(S(1)/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x)
    rule615 = ReplacementRule(pattern615, replacement615)
    pattern616 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons372, cons440)
    def replacement616(g, b, f, d, a, c, x, h, e):
        rubi.append(616)
        return Dist(-S(2)*g*(-S(2)*a*h + b*g), Subst(Int(S(1)/Simp(g*(-S(4)*a*c + b**S(2))*(-S(2)*a*h + b*g) - x**S(2)*(-a*e + b*d), x), x), x, Simp(-S(2)*a*h + b*g - x*(b*h - S(2)*c*g), x)/sqrt(d + e*x + f*x**S(2))), x)
    rule616 = ReplacementRule(pattern616, replacement616)
    pattern617 = Pattern(Integral((g_ + x_*WC('h', S(1)))/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons441)
    def replacement617(f, g, d, c, a, x, h, e):
        rubi.append(617)
        return Dist(-S(2)*a*g*h, Subst(Int(S(1)/Simp(S(2)*a**S(2)*c*g*h + a*e*x**S(2), x), x), x, Simp(a*h - c*g*x, x)/sqrt(d + e*x + f*x**S(2))), x)
    rule617 = ReplacementRule(pattern617, replacement617)
    pattern618 = Pattern(Integral((g_ + x_*WC('h', S(1)))/(sqrt(d_ + x_**S(2)*WC('f', S(1)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons226, cons442)
    def replacement618(f, b, g, d, c, a, x, h):
        rubi.append(618)
        return Dist(-S(2)*g*(-S(2)*a*h + b*g), Subst(Int(S(1)/Simp(-b*d*x**S(2) + g*(-S(4)*a*c + b**S(2))*(-S(2)*a*h + b*g), x), x), x, Simp(-S(2)*a*h + b*g - x*(b*h - S(2)*c*g), x)/sqrt(d + f*x**S(2))), x)
    rule618 = ReplacementRule(pattern618, replacement618)
    def With619(g, b, f, d, c, a, x, h, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(619)
        return Dist((S(2)*c*g - h*(b - q))/q, Int(S(1)/((b + S(2)*c*x - q)*sqrt(d + e*x + f*x**S(2))), x), x) - Dist((S(2)*c*g - h*(b + q))/q, Int(S(1)/((b + S(2)*c*x + q)*sqrt(d + e*x + f*x**S(2))), x), x)
    pattern619 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons231)
    rule619 = ReplacementRule(pattern619, With619)
    def With620(g, f, d, c, a, x, h, e):
        q = Rt(-a*c, S(2))
        rubi.append(620)
        return Dist(-c*g/(S(2)*q) + h/S(2), Int(S(1)/((c*x + q)*sqrt(d + e*x + f*x**S(2))), x), x) + Dist(c*g/(S(2)*q) + h/S(2), Int(S(1)/((c*x - q)*sqrt(d + e*x + f*x**S(2))), x), x)
    pattern620 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons394, cons412)
    rule620 = ReplacementRule(pattern620, With620)
    def With621(g, b, f, d, c, a, x, h):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(621)
        return Dist((S(2)*c*g - h*(b - q))/q, Int(S(1)/(sqrt(d + f*x**S(2))*(b + S(2)*c*x - q)), x), x) - Dist((S(2)*c*g - h*(b + q))/q, Int(S(1)/(sqrt(d + f*x**S(2))*(b + S(2)*c*x + q)), x), x)
    pattern621 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/(sqrt(d_ + x_**S(2)*WC('f', S(1)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons226, cons231)
    rule621 = ReplacementRule(pattern621, With621)
    def With622(g, b, f, d, a, c, x, h, e):
        q = Rt(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2), S(2))
        rubi.append(622)
        return Dist(S(1)/(S(2)*q), Int(Simp(-g*(-a*f + c*d - q) + h*(-a*e + b*d) - x*(g*(-b*f + c*e) - h*(-a*f + c*d + q)), x)/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x) - Dist(S(1)/(S(2)*q), Int(Simp(-g*(-a*f + c*d + q) + h*(-a*e + b*d) - x*(g*(-b*f + c*e) - h*(-a*f + c*d - q)), x)/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x)
    pattern622 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394, cons372, cons413)
    rule622 = ReplacementRule(pattern622, With622)
    def With623(g, f, d, c, a, x, h, e):
        q = Rt(a*c*e**S(2) + (-a*f + c*d)**S(2), S(2))
        rubi.append(623)
        return Dist(S(1)/(S(2)*q), Int(Simp(-a*e*h - g*(-a*f + c*d - q) + x*(-c*e*g + h*(-a*f + c*d + q)), x)/((a + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x) - Dist(S(1)/(S(2)*q), Int(Simp(-a*e*h - g*(-a*f + c*d + q) + x*(-c*e*g + h*(-a*f + c*d - q)), x)/((a + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x)
    pattern623 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons394, cons414)
    rule623 = ReplacementRule(pattern623, With623)
    def With624(g, b, f, d, a, c, x, h):
        q = Rt(b**S(2)*d*f + (-a*f + c*d)**S(2), S(2))
        rubi.append(624)
        return Dist(S(1)/(S(2)*q), Int(Simp(b*d*h - g*(-a*f + c*d - q) + x*(b*f*g + h*(-a*f + c*d + q)), x)/(sqrt(d + f*x**S(2))*(a + b*x + c*x**S(2))), x), x) - Dist(S(1)/(S(2)*q), Int(Simp(b*d*h - g*(-a*f + c*d + q) + x*(b*f*g + h*(-a*f + c*d - q)), x)/(sqrt(d + f*x**S(2))*(a + b*x + c*x**S(2))), x), x)
    pattern624 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/(sqrt(d_ + x_**S(2)*WC('f', S(1)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons226, cons413)
    rule624 = ReplacementRule(pattern624, With624)
    def With625(g, b, f, d, c, a, x, h, e):
        s = Rt(-S(4)*a*c + b**S(2), S(2))
        t = Rt(-S(4)*d*f + e**S(2), S(2))
        rubi.append(625)
        return Dist(sqrt(S(2)*a + x*(b + s))*sqrt(S(2)*d + x*(e + t))*sqrt(b + S(2)*c*x + s)*sqrt(e + S(2)*f*x + t)/(sqrt(a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), Int((g + h*x)/(sqrt(S(2)*a + x*(b + s))*sqrt(S(2)*d + x*(e + t))*sqrt(b + S(2)*c*x + s)*sqrt(e + S(2)*f*x + t)), x), x)
    pattern625 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/(sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons226, cons394)
    rule625 = ReplacementRule(pattern625, With625)
    def With626(g, b, f, d, c, a, x, h):
        s = Rt(-S(4)*a*c + b**S(2), S(2))
        t = Rt(-S(4)*d*f, S(2))
        rubi.append(626)
        return Dist(sqrt(S(2)*a + x*(b + s))*sqrt(S(2)*d + t*x)*sqrt(S(2)*f*x + t)*sqrt(b + S(2)*c*x + s)/(sqrt(d + f*x**S(2))*sqrt(a + b*x + c*x**S(2))), Int((g + h*x)/(sqrt(S(2)*a + x*(b + s))*sqrt(S(2)*d + t*x)*sqrt(S(2)*f*x + t)*sqrt(b + S(2)*c*x + s)), x), x)
    pattern626 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/(sqrt(d_ + x_**S(2)*WC('f', S(1)))*sqrt(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons208, cons209, cons226)
    rule626 = ReplacementRule(pattern626, With626)
    def With627(g, b, f, d, a, c, x, h, e):
        q = S(3)**(S(2)/3)*(-c*h**S(2)/(-b*h + S(2)*c*g)**S(2))**(S(1)/3)
        rubi.append(627)
        return -Simp(S(3)*h*q*log((-S(3)*h*(b + S(2)*c*x)/(-b*h + S(2)*c*g) + S(1))**(S(2)/3) + S(2)**(S(1)/3)*(S(3)*h*(b + S(2)*c*x)/(-b*h + S(2)*c*g) + S(1))**(S(1)/3))/(S(2)*f), x) + Simp(h*q*log(d + e*x + f*x**S(2))/(S(2)*f), x) + Simp(sqrt(S(3))*h*q*ArcTan(-S(2)**(S(2)/3)*sqrt(S(3))*(-S(3)*h*(b + S(2)*c*x)/(-b*h + S(2)*c*g) + S(1))**(S(2)/3)/(S(3)*(S(3)*h*(b + S(2)*c*x)/(-b*h + S(2)*c*g) + S(1))**(S(1)/3)) + sqrt(S(3))/S(3))/f, x)
    pattern627 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**(S(1)/3)*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons410, cons443, cons444, cons445)
    rule627 = ReplacementRule(pattern627, With627)
    pattern628 = Pattern(Integral((g_ + x_*WC('h', S(1)))/((a_ + x_**S(2)*WC('c', S(1)))**(S(1)/3)*(d_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons446, cons447, cons43)
    def replacement628(f, g, d, c, a, x, h):
        rubi.append(628)
        return Simp(S(2)**(S(1)/3)*h*log(d + f*x**S(2))/(S(4)*a**(S(1)/3)*f), x) - Simp(S(3)*S(2)**(S(1)/3)*h*log((S(1) - S(3)*h*x/g)**(S(2)/3) + S(2)**(S(1)/3)*(S(1) + S(3)*h*x/g)**(S(1)/3))/(S(4)*a**(S(1)/3)*f), x) + Simp(S(2)**(S(1)/3)*sqrt(S(3))*h*ArcTan(-S(2)**(S(2)/3)*sqrt(S(3))*(S(1) - S(3)*h*x/g)**(S(2)/3)/(S(3)*(S(1) + S(3)*h*x/g)**(S(1)/3)) + sqrt(S(3))/S(3))/(S(2)*a**(S(1)/3)*f), x)
    rule628 = ReplacementRule(pattern628, replacement628)
    def With629(g, b, f, d, a, c, x, h, e):
        q = -c/(-S(4)*a*c + b**S(2))
        rubi.append(629)
        return Dist((q*(a + b*x + c*x**S(2)))**(S(1)/3)/(a + b*x + c*x**S(2))**(S(1)/3), Int((g + h*x)/((d + e*x + f*x**S(2))*(a*q + b*q*x + c*q*x**S(2))**(S(1)/3)), x), x)
    pattern629 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))/((x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**(S(1)/3)*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons410, cons443, cons444, cons313)
    rule629 = ReplacementRule(pattern629, With629)
    pattern630 = Pattern(Integral((g_ + x_*WC('h', S(1)))/((a_ + x_**S(2)*WC('c', S(1)))**(S(1)/3)*(d_ + x_**S(2)*WC('f', S(1)))), x_), cons2, cons7, cons27, cons125, cons208, cons209, cons446, cons447, cons448)
    def replacement630(f, g, d, c, a, x, h):
        rubi.append(630)
        return Dist((S(1) + c*x**S(2)/a)**(S(1)/3)/(a + c*x**S(2))**(S(1)/3), Int((g + h*x)/((S(1) + c*x**S(2)/a)**(S(1)/3)*(d + f*x**S(2))), x), x)
    rule630 = ReplacementRule(pattern630, replacement630)
    pattern631 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons449)
    def replacement631(p, g, b, f, d, a, c, x, h, q, e):
        rubi.append(631)
        return Int((g + h*x)*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x)
    rule631 = ReplacementRule(pattern631, replacement631)
    pattern632 = Pattern(Integral((x_*WC('h', S(1)) + WC('g', S(0)))*(x_**S(2)*WC('c', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons5, cons50, cons450)
    def replacement632(p, g, f, d, a, c, x, h, q, e):
        rubi.append(632)
        return Int((a + c*x**S(2))**p*(g + h*x)*(d + e*x + f*x**S(2))**q, x)
    rule632 = ReplacementRule(pattern632, replacement632)
    pattern633 = Pattern(Integral((u_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(u_**S(2)*WC('c', S(1)) + u_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons68, cons69)
    def replacement633(p, u, m, g, b, f, d, a, c, x, h, q, e):
        rubi.append(633)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((g + h*x)**m*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule633 = ReplacementRule(pattern633, replacement633)
    pattern634 = Pattern(Integral((u_*WC('h', S(1)) + WC('g', S(0)))**WC('m', S(1))*(u_**S(2)*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons208, cons209, cons21, cons5, cons50, cons68, cons69)
    def replacement634(p, u, m, g, f, d, c, a, x, h, q, e):
        rubi.append(634)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + c*x**S(2))**p*(g + h*x)**m*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule634 = ReplacementRule(pattern634, replacement634)
    pattern635 = Pattern(Integral(u_**WC('p', S(1))*v_**WC('q', S(1))*z_**WC('m', S(1)), x_), cons21, cons5, cons50, cons451, cons452, cons453)
    def replacement635(v, z, p, u, m, x, q):
        rubi.append(635)
        return Int(ExpandToSum(u, x)**p*ExpandToSum(v, x)**q*ExpandToSum(z, x)**m, x)
    rule635 = ReplacementRule(pattern635, replacement635)
    pattern636 = Pattern(Integral((d_ + x_*WC('e', S(1)))**WC('m', S(1))*(f_ + x_*WC('g', S(1)))**WC('n', S(1))*(x_*WC('i', S(1)) + WC('h', S(0)))**WC('q', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons21, cons4, cons5, cons50, cons336, cons124, cons377)
    def replacement636(p, m, g, b, f, i, d, a, n, c, x, h, q, e):
        rubi.append(636)
        return Int((h + i*x)**q*(d*f + e*g*x**S(2))**m*(a + b*x + c*x**S(2))**p, x)
    rule636 = ReplacementRule(pattern636, replacement636)
    pattern637 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*(x_*WC('g', S(1)) + WC('f', S(0)))**WC('n', S(1))*(x_*WC('i', S(1)) + WC('h', S(0)))**WC('q', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons21, cons4, cons5, cons50, cons128, cons84)
    def replacement637(p, m, f, g, b, i, d, a, n, c, x, h, q, e):
        rubi.append(637)
        return Int(ExpandIntegrand((d + e*x)**m*(f + g*x)**n*(h + i*x)**q*(a + b*x + c*x**S(2))**p, x), x)
    rule637 = ReplacementRule(pattern637, replacement637)
    pattern638 = Pattern(Integral((d_ + x_*WC('e', S(1)))**m_*(f_ + x_*WC('g', S(1)))**n_*(x_*WC('i', S(1)) + WC('h', S(0)))**WC('q', S(1))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons209, cons224, cons21, cons4, cons5, cons50, cons336, cons124)
    def replacement638(p, m, g, b, f, i, d, a, c, n, x, h, q, e):
        rubi.append(638)
        return Dist((d + e*x)**FracPart(m)*(f + g*x)**FracPart(m)*(d*f + e*g*x**S(2))**(-FracPart(m)), Int((h + i*x)**q*(d*f + e*g*x**S(2))**m*(a + b*x + c*x**S(2))**p, x), x)
    rule638 = ReplacementRule(pattern638, replacement638)
    pattern639 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons5, cons50, cons382, cons383, cons384, cons385)
    def replacement639(B, p, C, e, f, b, d, c, a, x, q, A):
        rubi.append(639)
        return Dist((c/f)**p, Int((A + B*x + C*x**S(2))*(d + e*x + f*x**S(2))**(p + q), x), x)
    rule639 = ReplacementRule(pattern639, replacement639)
    pattern640 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons5, cons50, cons382, cons383, cons384, cons385)
    def replacement640(C, p, e, f, b, d, c, a, x, q, A):
        rubi.append(640)
        return Dist((c/f)**p, Int((A + C*x**S(2))*(d + e*x + f*x**S(2))**(p + q), x), x)
    rule640 = ReplacementRule(pattern640, replacement640)
    pattern641 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons5, cons50, cons382, cons383, cons147, cons386, cons387)
    def replacement641(B, p, C, e, f, b, d, c, a, x, q, A):
        rubi.append(641)
        return Dist(a**IntPart(p)*d**(-IntPart(p))*(a + b*x + c*x**S(2))**FracPart(p)*(d + e*x + f*x**S(2))**(-FracPart(p)), Int((A + B*x + C*x**S(2))*(d + e*x + f*x**S(2))**(p + q), x), x)
    rule641 = ReplacementRule(pattern641, replacement641)
    pattern642 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons5, cons50, cons382, cons383, cons147, cons386, cons387)
    def replacement642(C, p, e, f, b, d, c, a, x, q, A):
        rubi.append(642)
        return Dist(a**IntPart(p)*d**(-IntPart(p))*(a + b*x + c*x**S(2))**FracPart(p)*(d + e*x + f*x**S(2))**(-FracPart(p)), Int((A + C*x**S(2))*(d + e*x + f*x**S(2))**(p + q), x), x)
    rule642 = ReplacementRule(pattern642, replacement642)
    pattern643 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons5, cons50, cons45)
    def replacement643(B, p, C, e, f, b, d, c, a, x, q, A):
        rubi.append(643)
        return Dist((S(4)*c)**(-IntPart(p))*(b + S(2)*c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((b + S(2)*c*x)**(S(2)*p)*(A + B*x + C*x**S(2))*(d + e*x + f*x**S(2))**q, x), x)
    rule643 = ReplacementRule(pattern643, replacement643)
    pattern644 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons5, cons50, cons45)
    def replacement644(C, p, e, f, b, d, c, a, x, q, A):
        rubi.append(644)
        return Dist((S(4)*c)**(-IntPart(p))*(b + S(2)*c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((A + C*x**S(2))*(b + S(2)*c*x)**(S(2)*p)*(d + e*x + f*x**S(2))**q, x), x)
    rule644 = ReplacementRule(pattern644, replacement644)
    pattern645 = Pattern(Integral((x_**S(2)*WC('f', S(1)) + WC('d', S(0)))**WC('q', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons35, cons36, cons5, cons50, cons45)
    def replacement645(B, p, C, f, b, d, c, a, x, q, A):
        rubi.append(645)
        return Dist((S(4)*c)**(-IntPart(p))*(b + S(2)*c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((b + S(2)*c*x)**(S(2)*p)*(d + f*x**S(2))**q*(A + B*x + C*x**S(2)), x), x)
    rule645 = ReplacementRule(pattern645, replacement645)
    pattern646 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))**WC('q', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons36, cons5, cons50, cons45)
    def replacement646(C, p, f, b, d, c, a, x, q, A):
        rubi.append(646)
        return Dist((S(4)*c)**(-IntPart(p))*(b + S(2)*c*x)**(-S(2)*FracPart(p))*(a + b*x + c*x**S(2))**FracPart(p), Int((A + C*x**S(2))*(b + S(2)*c*x)**(S(2)*p)*(d + f*x**S(2))**q, x), x)
    rule646 = ReplacementRule(pattern646, replacement646)
    pattern647 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons226, cons394, cons220, cons163)
    def replacement647(B, p, C, e, f, b, d, c, a, x, q, A):
        rubi.append(647)
        return Int(ExpandIntegrand((A + B*x + C*x**S(2))*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x)
    rule647 = ReplacementRule(pattern647, replacement647)
    pattern648 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons226, cons394, cons220, cons163)
    def replacement648(C, p, e, f, b, d, c, a, x, q, A):
        rubi.append(648)
        return Int(ExpandIntegrand((A + C*x**S(2))*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x)
    rule648 = ReplacementRule(pattern648, replacement648)
    pattern649 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons394, cons220, cons432)
    def replacement649(B, C, p, e, f, d, c, a, x, q, A):
        rubi.append(649)
        return Int(ExpandIntegrand((a + c*x**S(2))**p*(A + B*x + C*x**S(2))*(d + e*x + f*x**S(2))**q, x), x)
    rule649 = ReplacementRule(pattern649, replacement649)
    pattern650 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons36, cons394, cons220, cons432)
    def replacement650(C, p, f, d, c, a, A, x, q, e):
        rubi.append(650)
        return Int(ExpandIntegrand((A + C*x**S(2))*(a + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x)
    rule650 = ReplacementRule(pattern650, replacement650)
    pattern651 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons226, cons394, cons402, cons137, cons403)
    def replacement651(B, p, C, e, f, b, d, c, a, x, q, A):
        rubi.append(651)
        return -Dist(S(1)/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(-1))*Simp(-d*(C*(S(2)*a*c - b**S(2)*(p + S(2))) + c*(S(2)*p + S(3))*(-S(2)*A*c + B*b)) + e*q*(A*b*c - S(2)*B*a*c + C*a*b) - f*x**S(2)*(C*(S(2)*a*c*(S(2)*q + S(1)) - b**S(2)*(p + S(2)*q + S(2))) + c*(-S(2)*A*c + B*b)*(S(2)*p + S(2)*q + S(3))) + x*(-e*(C*(S(2)*a*c*(q + S(1)) - b**S(2)*(p + q + S(2))) + c*(-S(2)*A*c + B*b)*(S(2)*p + q + S(3))) + S(2)*f*q*(A*b*c - S(2)*B*a*c + C*a*b)), x), x), x) + Simp((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*(A*b*c - S(2)*B*a*c + C*a*b - x*(-C*(-S(2)*a*c + b**S(2)) + c*(-S(2)*A*c + B*b)))/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule651 = ReplacementRule(pattern651, replacement651)
    pattern652 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons226, cons394, cons402, cons137, cons403)
    def replacement652(C, p, e, f, b, d, c, a, x, q, A):
        rubi.append(652)
        return -Dist(S(1)/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(-1))*Simp(A*c*(b*e*q + S(2)*c*d*(S(2)*p + S(3))) - C*(-a*b*e*q + S(2)*a*c*d - b**S(2)*d*(p + S(2))) - f*x**S(2)*(-S(2)*A*c**S(2)*(S(2)*p + S(2)*q + S(3)) + C*(S(2)*a*c*(S(2)*q + S(1)) - b**S(2)*(p + S(2)*q + S(2)))) + x*(S(2)*A*c*(b*f*q + c*e*(S(2)*p + q + S(3))) + C*(S(2)*a*b*f*q - S(2)*a*c*e*(q + S(1)) + b**S(2)*e*(p + q + S(2)))), x), x), x) + Simp((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*(A*b*c + C*a*b + x*(S(2)*A*c**S(2) + C*(-S(2)*a*c + b**S(2))))/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule652 = ReplacementRule(pattern652, replacement652)
    pattern653 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons394, cons402, cons137, cons403)
    def replacement653(B, C, p, e, f, d, c, a, x, q, A):
        rubi.append(653)
        return -Dist(-S(1)/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(-1))*Simp(A*c*d*(S(2)*p + S(3)) - a*(B*e*q + C*d) - f*x**S(2)*(-A*c*(S(2)*p + S(2)*q + S(3)) + C*a*(S(2)*q + S(1))) + x*(A*c*e*(S(2)*p + q + S(3)) - a*(S(2)*B*f*q + C*e*(q + S(1)))), x), x), x) + Simp((a + c*x**S(2))**(p + S(1))*(B*a - x*(A*c - C*a))*(d + e*x + f*x**S(2))**q/(S(2)*a*c*(p + S(1))), x)
    rule653 = ReplacementRule(pattern653, replacement653)
    pattern654 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons36, cons394, cons402, cons137, cons403)
    def replacement654(C, p, f, d, c, a, A, x, q, e):
        rubi.append(654)
        return Dist(S(1)/(S(2)*a*c*(p + S(1))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(-1))*Simp(A*c*d*(S(2)*p + S(3)) - C*a*d - f*x**S(2)*(-A*c*(S(2)*p + S(2)*q + S(3)) + C*a*(S(2)*q + S(1))) + x*(A*c*e*(S(2)*p + q + S(3)) - C*a*e*(q + S(1))), x), x), x) - Simp(x*(a + c*x**S(2))**(p + S(1))*(A*c - C*a)*(d + e*x + f*x**S(2))**q/(S(2)*a*c*(p + S(1))), x)
    rule654 = ReplacementRule(pattern654, replacement654)
    pattern655 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons35, cons36, cons226, cons402, cons137, cons403)
    def replacement655(B, p, C, f, b, d, c, a, x, q, A):
        rubi.append(655)
        return -Dist(S(1)/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + f*x**S(2))**(q + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*Simp(-d*(C*(S(2)*a*c - b**S(2)*(p + S(2))) + c*(S(2)*p + S(3))*(-S(2)*A*c + B*b)) + S(2)*f*q*x*(A*b*c - S(2)*B*a*c + C*a*b) - f*x**S(2)*(C*(S(2)*a*c*(S(2)*q + S(1)) - b**S(2)*(p + S(2)*q + S(2))) + c*(-S(2)*A*c + B*b)*(S(2)*p + S(2)*q + S(3))), x), x), x) + Simp((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(1))*(A*b*c - S(2)*B*a*c + C*a*b - x*(-C*(-S(2)*a*c + b**S(2)) + c*(-S(2)*A*c + B*b)))/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule655 = ReplacementRule(pattern655, replacement655)
    pattern656 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons36, cons226, cons402, cons137, cons403)
    def replacement656(C, p, f, b, d, c, a, x, q, A):
        rubi.append(656)
        return -Dist(S(1)/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), Int((d + f*x**S(2))**(q + S(-1))*(a + b*x + c*x**S(2))**(p + S(1))*Simp(S(2)*A*c**S(2)*d*(S(2)*p + S(3)) - C*(S(2)*a*c*d - b**S(2)*d*(p + S(2))) - f*x**S(2)*(-S(2)*A*c**S(2)*(S(2)*p + S(2)*q + S(3)) + C*(S(2)*a*c*(S(2)*q + S(1)) - b**S(2)*(p + S(2)*q + S(2)))) + x*(S(2)*A*b*c*f*q + S(2)*C*a*b*f*q), x), x), x) + Simp((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(1))*(A*b*c + C*a*b + x*(S(2)*A*c**S(2) + C*(-S(2)*a*c + b**S(2))))/(c*(p + S(1))*(-S(4)*a*c + b**S(2))), x)
    rule656 = ReplacementRule(pattern656, replacement656)
    pattern657 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons50, cons226, cons394, cons13, cons137, cons404, cons405)
    def replacement657(B, p, C, e, f, b, d, c, a, x, q, A):
        rubi.append(657)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*Simp(-c*f*x**S(2)*(S(2)*p + S(2)*q + S(5))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-B*c*e - C*a*f + C*c*d) + b**S(2)*(A*f + C*d) - b*(A*c*e + B*a*f + B*c*d + C*a*e)) - e*((A*b - B*a)*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) + (A*c - C*a)*(S(2)*a*c*e - b*(a*f + c*d)))*(p + q + S(2)) - x*(S(2)*f*((A*b - B*a)*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) + (A*c - C*a)*(S(2)*a*c*e - b*(a*f + c*d)))*(p + q + S(2)) - (b*f*(p + S(1)) - c*e*(S(2)*p + q + S(4)))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-B*c*e - C*a*f + C*c*d) + b**S(2)*(A*f + C*d) - b*(A*c*e + B*a*f + B*c*d + C*a*e))) + (p + S(1))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2))*(-S(2)*A*c + B*b - S(2)*C*a) + (a*f*(p + S(1)) - c*d*(p + S(2)))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-B*c*e - C*a*f + C*c*d) + b**S(2)*(A*f + C*d) - b*(A*c*e + B*a*f + B*c*d + C*a*e)), x), x), x) + Simp((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(1))*(c*x*(A*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) - B*(a*b*f - S(2)*a*c*e + b*c*d) + C*(-a*b*e - S(2)*a*(-a*f + c*d) + b**S(2)*d)) + (A*b - B*a)*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) + (A*c - C*a)*(S(2)*a*c*e - b*(a*f + c*d)))/((p + S(1))*(-S(4)*a*c + b**S(2))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2))), x)
    rule657 = ReplacementRule(pattern657, replacement657)
    pattern658 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons50, cons226, cons394, cons13, cons137, cons404, cons405)
    def replacement658(C, p, e, f, b, d, c, a, x, q, A):
        rubi.append(658)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2))), Int((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*Simp(-c*f*x**S(2)*(S(2)*p + S(2)*q + S(5))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d) + b**S(2)*(A*f + C*d) - b*(A*c*e + C*a*e)) - e*(A*b*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) + (A*c - C*a)*(S(2)*a*c*e - b*(a*f + c*d)))*(p + q + S(2)) - x*(S(2)*f*(A*b*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) + (A*c - C*a)*(S(2)*a*c*e - b*(a*f + c*d)))*(p + q + S(2)) - (b*f*(p + S(1)) - c*e*(S(2)*p + q + S(4)))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d) + b**S(2)*(A*f + C*d) - b*(A*c*e + C*a*e))) + (p + S(1))*(-S(2)*A*c - S(2)*C*a)*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2)) + (a*f*(p + S(1)) - c*d*(p + S(2)))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d) + b**S(2)*(A*f + C*d) - b*(A*c*e + C*a*e)), x), x), x) + Simp((a + b*x + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(1))*(A*b*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) + c*x*(A*(b**S(2)*f + S(2)*c**S(2)*d - c*(S(2)*a*f + b*e)) + C*(-a*b*e - S(2)*a*(-a*f + c*d) + b**S(2)*d)) + (A*c - C*a)*(S(2)*a*c*e - b*(a*f + c*d)))/((p + S(1))*(-S(4)*a*c + b**S(2))*(-(-a*e + b*d)*(-b*f + c*e) + (-a*f + c*d)**S(2))), x)
    rule658 = ReplacementRule(pattern658, replacement658)
    pattern659 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons50, cons394, cons13, cons137, cons407, cons405)
    def replacement659(B, C, p, e, f, d, c, a, x, q, A):
        rubi.append(659)
        return Dist(-S(1)/(S(4)*a*c*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*Simp(-c*f*x**S(2)*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-B*c*e - C*a*f + C*c*d))*(S(2)*p + S(2)*q + S(5)) - e*(-B*a*(-S(2)*a*c*f + S(2)*c**S(2)*d) + S(2)*a*c*e*(A*c - C*a))*(p + q + S(2)) - x*(c*e*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-B*c*e - C*a*f + C*c*d))*(S(2)*p + q + S(4)) + S(2)*f*(-B*a*(-S(2)*a*c*f + S(2)*c**S(2)*d) + S(2)*a*c*e*(A*c - C*a))*(p + q + S(2))) + (p + S(1))*(-S(2)*A*c - S(2)*C*a)*(a*c*e**S(2) + (-a*f + c*d)**S(2)) + (S(2)*A*c*(-a*f + c*d) - S(2)*a*(-B*c*e - C*a*f + C*c*d))*(a*f*(p + S(1)) - c*d*(p + S(2))), x), x), x) + Simp(-(a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**(q + S(1))*(-B*a*(-S(2)*a*c*f + S(2)*c**S(2)*d) + S(2)*a*c*e*(A*c - C*a) + c*x*(A*(-S(2)*a*c*f + S(2)*c**S(2)*d) + S(2)*B*a*c*e - S(2)*C*a*(-a*f + c*d)))/(S(4)*a*c*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2))), x)
    rule659 = ReplacementRule(pattern659, replacement659)
    pattern660 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons36, cons50, cons394, cons13, cons137, cons407, cons405)
    def replacement660(C, p, f, d, c, a, A, x, q, e):
        rubi.append(660)
        return Dist(-S(1)/(S(4)*a*c*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2))), Int((a + c*x**S(2))**(p + S(1))*(d + e*x + f*x**S(2))**q*Simp(-S(2)*a*c*e**S(2)*(A*c - C*a)*(p + q + S(2)) - c*f*x**S(2)*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d))*(S(2)*p + S(2)*q + S(5)) - x*(S(4)*a*c*e*f*(A*c - C*a)*(p + q + S(2)) + c*e*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d))*(S(2)*p + q + S(4))) + (p + S(1))*(-S(2)*A*c - S(2)*C*a)*(a*c*e**S(2) + (-a*f + c*d)**S(2)) + (S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d))*(a*f*(p + S(1)) - c*d*(p + S(2))), x), x), x) + Simp(-(a + c*x**S(2))**(p + S(1))*(S(2)*a*c*e*(A*c - C*a) + c*x*(A*(-S(2)*a*c*f + S(2)*c**S(2)*d) - S(2)*C*a*(-a*f + c*d)))*(d + e*x + f*x**S(2))**(q + S(1))/(S(4)*a*c*(p + S(1))*(a*c*e**S(2) + (-a*f + c*d)**S(2))), x)
    rule660 = ReplacementRule(pattern660, replacement660)
    pattern661 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons35, cons36, cons50, cons226, cons13, cons137, cons406, cons405)
    def replacement661(B, p, C, f, b, d, c, a, x, q, A):
        rubi.append(661)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(b**S(2)*d*f + (-a*f + c*d)**S(2))), Int((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(1))*Simp(-c*f*x**S(2)*(S(2)*p + S(2)*q + S(5))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d) + b**S(2)*(A*f + C*d) - b*(B*a*f + B*c*d)) - x*(-b*f*(p + S(1))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d) + b**S(2)*(A*f + C*d) - b*(B*a*f + B*c*d)) + S(2)*f*(-b*(A*c - C*a)*(a*f + c*d) + (A*b - B*a)*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d))*(p + q + S(2))) + (p + S(1))*(b**S(2)*d*f + (-a*f + c*d)**S(2))*(-S(2)*A*c + B*b - S(2)*C*a) + (a*f*(p + S(1)) - c*d*(p + S(2)))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d) + b**S(2)*(A*f + C*d) - b*(B*a*f + B*c*d)), x), x), x) + Simp((d + f*x**S(2))**(q + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(-b*(A*c - C*a)*(a*f + c*d) + c*x*(A*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d) - B*(a*b*f + b*c*d) + C*(-S(2)*a*(-a*f + c*d) + b**S(2)*d)) + (A*b - B*a)*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d))/((p + S(1))*(-S(4)*a*c + b**S(2))*(b**S(2)*d*f + (-a*f + c*d)**S(2))), x)
    rule661 = ReplacementRule(pattern661, replacement661)
    pattern662 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons36, cons50, cons226, cons13, cons137, cons406, cons405)
    def replacement662(C, p, f, b, d, c, a, x, q, A):
        rubi.append(662)
        return Dist(S(1)/((p + S(1))*(-S(4)*a*c + b**S(2))*(b**S(2)*d*f + (-a*f + c*d)**S(2))), Int((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(1))*Simp(-c*f*x**S(2)*(S(2)*p + S(2)*q + S(5))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d) + b**S(2)*(A*f + C*d)) - x*(-b*f*(p + S(1))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d) + b**S(2)*(A*f + C*d)) + S(2)*f*(A*b*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d) - b*(A*c - C*a)*(a*f + c*d))*(p + q + S(2))) + (p + S(1))*(-S(2)*A*c - S(2)*C*a)*(b**S(2)*d*f + (-a*f + c*d)**S(2)) + (a*f*(p + S(1)) - c*d*(p + S(2)))*(S(2)*A*c*(-a*f + c*d) - S(2)*a*(-C*a*f + C*c*d) + b**S(2)*(A*f + C*d)), x), x), x) + Simp((d + f*x**S(2))**(q + S(1))*(a + b*x + c*x**S(2))**(p + S(1))*(A*b*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d) - b*(A*c - C*a)*(a*f + c*d) + c*x*(A*(-S(2)*a*c*f + b**S(2)*f + S(2)*c**S(2)*d) + C*(-S(2)*a*(-a*f + c*d) + b**S(2)*d)))/((p + S(1))*(-S(4)*a*c + b**S(2))*(b**S(2)*d*f + (-a*f + c*d)**S(2))), x)
    rule662 = ReplacementRule(pattern662, replacement662)
    pattern663 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons50, cons226, cons394, cons13, cons163, cons433, cons454)
    def replacement663(B, p, C, e, f, b, d, c, a, x, q, A):
        rubi.append(663)
        return -Dist(S(1)/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), Int((a + b*x + c*x**S(2))**(p + S(-1))*(d + e*x + f*x**S(2))**q*Simp(p*(-a*e + b*d)*(C*(q + S(1))*(-b*f + c*e) - c*(-B*f + C*e)*(S(2)*p + S(2)*q + S(3))) + x**S(2)*(p*(-b*f + c*e)*(C*(q + S(1))*(-b*f + c*e) - c*(-B*f + C*e)*(S(2)*p + S(2)*q + S(3))) + (C*f**S(2)*p*(-S(4)*a*c + b**S(2)) - c**S(2)*(C*(-S(4)*d*f + e**S(2))*(S(2)*p + q + S(2)) + f*(S(2)*p + S(2)*q + S(3))*(S(2)*A*f - B*e + S(2)*C*d)))*(p + q + S(1))) + x*(S(2)*p*(-a*f + c*d)*(C*(q + S(1))*(-b*f + c*e) - c*(-B*f + C*e)*(S(2)*p + S(2)*q + S(3))) + (C*e*f*p*(-S(4)*a*c + b**S(2)) - b*c*(C*(-S(4)*d*f + e**S(2))*(S(2)*p + q + S(2)) + f*(S(2)*p + S(2)*q + S(3))*(S(2)*A*f - B*e + S(2)*C*d)))*(p + q + S(1))) + (C*b**S(2)*d*f*p + a*c*(C*(S(2)*d*f - e**S(2)*(S(2)*p + q + S(2))) + f*(-S(2)*A*f + B*e)*(S(2)*p + S(2)*q + S(3))))*(p + q + S(1)), x), x), x) + Simp((a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**(q + S(1))*(B*c*f*(S(2)*p + S(2)*q + S(3)) + S(2)*C*c*f*x*(p + q + S(1)) + C*(b*f*p - c*e*(S(2)*p + q + S(2))))/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), x)
    rule663 = ReplacementRule(pattern663, replacement663)
    pattern664 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons50, cons226, cons394, cons13, cons163, cons433, cons454)
    def replacement664(C, p, e, f, b, d, c, a, x, q, A):
        rubi.append(664)
        return -Dist(S(1)/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), Int((a + b*x + c*x**S(2))**(p + S(-1))*(d + e*x + f*x**S(2))**q*Simp(p*(-a*e + b*d)*(-C*c*e*(S(2)*p + S(2)*q + S(3)) + C*(q + S(1))*(-b*f + c*e)) + x**S(2)*(p*(-b*f + c*e)*(-C*c*e*(S(2)*p + S(2)*q + S(3)) + C*(q + S(1))*(-b*f + c*e)) + (C*f**S(2)*p*(-S(4)*a*c + b**S(2)) - c**S(2)*(C*(-S(4)*d*f + e**S(2))*(S(2)*p + q + S(2)) + f*(S(2)*A*f + S(2)*C*d)*(S(2)*p + S(2)*q + S(3))))*(p + q + S(1))) + x*(S(2)*p*(-a*f + c*d)*(-C*c*e*(S(2)*p + S(2)*q + S(3)) + C*(q + S(1))*(-b*f + c*e)) + (C*e*f*p*(-S(4)*a*c + b**S(2)) - b*c*(C*(-S(4)*d*f + e**S(2))*(S(2)*p + q + S(2)) + f*(S(2)*A*f + S(2)*C*d)*(S(2)*p + S(2)*q + S(3))))*(p + q + S(1))) + (C*b**S(2)*d*f*p + a*c*(-S(2)*A*f**S(2)*(S(2)*p + S(2)*q + S(3)) + C*(S(2)*d*f - e**S(2)*(S(2)*p + q + S(2)))))*(p + q + S(1)), x), x), x) + Simp((S(2)*C*c*f*x*(p + q + S(1)) + C*(b*f*p - c*e*(S(2)*p + q + S(2))))*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**(q + S(1))/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), x)
    rule664 = ReplacementRule(pattern664, replacement664)
    pattern665 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons50, cons394, cons13, cons163, cons433, cons454)
    def replacement665(B, C, p, e, f, d, c, a, x, q, A):
        rubi.append(665)
        return -Dist(S(1)/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x + f*x**S(2))**q*Simp(a*c*(C*(S(2)*d*f - e**S(2)*(S(2)*p + q + S(2))) + f*(-S(2)*A*f + B*e)*(S(2)*p + S(2)*q + S(3)))*(p + q + S(1)) - a*e*p*(C*c*e*(q + S(1)) - c*(-B*f + C*e)*(S(2)*p + S(2)*q + S(3))) + x**S(2)*(c*e*p*(C*c*e*(q + S(1)) - c*(-B*f + C*e)*(S(2)*p + S(2)*q + S(3))) + (-S(4)*C*a*c*f**S(2)*p - c**S(2)*(C*(-S(4)*d*f + e**S(2))*(S(2)*p + q + S(2)) + f*(S(2)*p + S(2)*q + S(3))*(S(2)*A*f - B*e + S(2)*C*d)))*(p + q + S(1))) + x*(-S(4)*C*a*c*e*f*p*(p + q + S(1)) + S(2)*p*(-a*f + c*d)*(C*c*e*(q + S(1)) - c*(-B*f + C*e)*(S(2)*p + S(2)*q + S(3)))), x), x), x) + Simp((a + c*x**S(2))**p*(d + e*x + f*x**S(2))**(q + S(1))*(B*c*f*(S(2)*p + S(2)*q + S(3)) - C*c*e*(S(2)*p + q + S(2)) + S(2)*C*c*f*x*(p + q + S(1)))/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), x)
    rule665 = ReplacementRule(pattern665, replacement665)
    pattern666 = Pattern(Integral((a_ + x_**S(2)*WC('c', S(1)))**WC('p', S(1))*(x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons36, cons50, cons394, cons13, cons163, cons433, cons454)
    def replacement666(C, p, f, d, c, a, A, x, q, e):
        rubi.append(666)
        return -Dist(S(1)/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), Int((a + c*x**S(2))**(p + S(-1))*(d + e*x + f*x**S(2))**q*Simp(a*c*(-S(2)*A*f**S(2)*(S(2)*p + S(2)*q + S(3)) + C*(S(2)*d*f - e**S(2)*(S(2)*p + q + S(2))))*(p + q + S(1)) - a*e*p*(C*c*e*(q + S(1)) - C*c*e*(S(2)*p + S(2)*q + S(3))) + x**S(2)*(c*e*p*(C*c*e*(q + S(1)) - C*c*e*(S(2)*p + S(2)*q + S(3))) + (-S(4)*C*a*c*f**S(2)*p - c**S(2)*(C*(-S(4)*d*f + e**S(2))*(S(2)*p + q + S(2)) + f*(S(2)*A*f + S(2)*C*d)*(S(2)*p + S(2)*q + S(3))))*(p + q + S(1))) + x*(-S(4)*C*a*c*e*f*p*(p + q + S(1)) + S(2)*p*(-a*f + c*d)*(C*c*e*(q + S(1)) - C*c*e*(S(2)*p + S(2)*q + S(3)))), x), x), x) + Simp((a + c*x**S(2))**p*(-C*c*e*(S(2)*p + q + S(2)) + S(2)*C*c*f*x*(p + q + S(1)))*(d + e*x + f*x**S(2))**(q + S(1))/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), x)
    rule666 = ReplacementRule(pattern666, replacement666)
    pattern667 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1))*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0))), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons35, cons36, cons50, cons226, cons13, cons163, cons433, cons454)
    def replacement667(B, p, C, f, b, d, c, a, x, q, A):
        rubi.append(667)
        return -Dist(S(1)/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), Int((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(-1))*Simp(b*d*p*(B*c*f*(S(2)*p + S(2)*q + S(3)) - C*b*f*(q + S(1))) + x**S(2)*(-b*f*p*(B*c*f*(S(2)*p + S(2)*q + S(3)) - C*b*f*(q + S(1))) + (C*f**S(2)*p*(-S(4)*a*c + b**S(2)) - c**S(2)*(-S(4)*C*d*f*(S(2)*p + q + S(2)) + f*(S(2)*A*f + S(2)*C*d)*(S(2)*p + S(2)*q + S(3))))*(p + q + S(1))) + x*(-b*c*(-S(4)*C*d*f*(S(2)*p + q + S(2)) + f*(S(2)*A*f + S(2)*C*d)*(S(2)*p + S(2)*q + S(3)))*(p + q + S(1)) + S(2)*p*(-a*f + c*d)*(B*c*f*(S(2)*p + S(2)*q + S(3)) - C*b*f*(q + S(1)))) + (C*b**S(2)*d*f*p + a*c*(-S(2)*A*f**S(2)*(S(2)*p + S(2)*q + S(3)) + S(2)*C*d*f))*(p + q + S(1)), x), x), x) + Simp((d + f*x**S(2))**(q + S(1))*(a + b*x + c*x**S(2))**p*(B*c*f*(S(2)*p + S(2)*q + S(3)) + C*b*f*p + S(2)*C*c*f*x*(p + q + S(1)))/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), x)
    rule667 = ReplacementRule(pattern667, replacement667)
    pattern668 = Pattern(Integral((d_ + x_**S(2)*WC('f', S(1)))**WC('q', S(1))*(x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons36, cons50, cons226, cons13, cons163, cons433, cons454)
    def replacement668(C, p, f, b, d, c, a, x, q, A):
        rubi.append(668)
        return -Dist(S(1)/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), Int((d + f*x**S(2))**q*(a + b*x + c*x**S(2))**(p + S(-1))*Simp(-C*b**S(2)*d*f*p*(q + S(1)) + x**S(2)*(C*b**S(2)*f**S(2)*p*(q + S(1)) + (C*f**S(2)*p*(-S(4)*a*c + b**S(2)) - c**S(2)*(-S(4)*C*d*f*(S(2)*p + q + S(2)) + f*(S(2)*A*f + S(2)*C*d)*(S(2)*p + S(2)*q + S(3))))*(p + q + S(1))) + x*(-S(2)*C*b*f*p*(q + S(1))*(-a*f + c*d) - b*c*(-S(4)*C*d*f*(S(2)*p + q + S(2)) + f*(S(2)*A*f + S(2)*C*d)*(S(2)*p + S(2)*q + S(3)))*(p + q + S(1))) + (C*b**S(2)*d*f*p + a*c*(-S(2)*A*f**S(2)*(S(2)*p + S(2)*q + S(3)) + S(2)*C*d*f))*(p + q + S(1)), x), x), x) + Simp((d + f*x**S(2))**(q + S(1))*(C*b*f*p + S(2)*C*c*f*x*(p + q + S(1)))*(a + b*x + c*x**S(2))**p/(S(2)*c*f**S(2)*(p + q + S(1))*(S(2)*p + S(2)*q + S(3))), x)
    rule668 = ReplacementRule(pattern668, replacement668)
    def With669(B, C, e, f, b, d, c, a, x, A):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = a**S(2)*f**S(2) - a*b*e*f - S(2)*a*c*d*f + a*c*e**S(2) + b**S(2)*d*f - b*c*d*e + c**S(2)*d**S(2)
        if NonzeroQ(q):
            return True
        return False
    pattern669 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons226, cons394, CustomConstraint(With669))
    def replacement669(B, C, e, f, b, d, c, a, x, A):

        q = a**S(2)*f**S(2) - a*b*e*f - S(2)*a*c*d*f + a*c*e**S(2) + b**S(2)*d*f - b*c*d*e + c**S(2)*d**S(2)
        rubi.append(669)
        return Dist(S(1)/q, Int((-A*a*c*f + A*b**S(2)*f - A*b*c*e + A*c**S(2)*d - B*a*b*f + B*a*c*e + C*a**S(2)*f - C*a*c*d + c*x*(A*b*f - A*c*e - B*a*f + B*c*d + C*a*e - C*b*d))/(a + b*x + c*x**S(2)), x), x) + Dist(S(1)/q, Int((A*a*f**S(2) - A*b*e*f - A*c*d*f + A*c*e**S(2) + B*b*d*f - B*c*d*e - C*a*d*f + C*c*d**S(2) - f*x*(A*b*f - A*c*e - B*a*f + B*c*d + C*a*e - C*b*d))/(d + e*x + f*x**S(2)), x), x)
    rule669 = ReplacementRule(pattern669, replacement669)
    def With670(C, f, b, d, c, a, A, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = a**S(2)*f**S(2) - a*b*e*f - S(2)*a*c*d*f + a*c*e**S(2) + b**S(2)*d*f - b*c*d*e + c**S(2)*d**S(2)
        if NonzeroQ(q):
            return True
        return False
    pattern670 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*(d_ + x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons226, cons394, CustomConstraint(With670))
    def replacement670(C, f, b, d, c, a, A, x, e):

        q = a**S(2)*f**S(2) - a*b*e*f - S(2)*a*c*d*f + a*c*e**S(2) + b**S(2)*d*f - b*c*d*e + c**S(2)*d**S(2)
        rubi.append(670)
        return Dist(S(1)/q, Int((-A*a*c*f + A*b**S(2)*f - A*b*c*e + A*c**S(2)*d + C*a**S(2)*f - C*a*c*d + c*x*(A*b*f - A*c*e + C*a*e - C*b*d))/(a + b*x + c*x**S(2)), x), x) + Dist(S(1)/q, Int((A*a*f**S(2) - A*b*e*f - A*c*d*f + A*c*e**S(2) - C*a*d*f + C*c*d**S(2) - f*x*(A*b*f - A*c*e + C*a*e - C*b*d))/(d + e*x + f*x**S(2)), x), x)
    rule670 = ReplacementRule(pattern670, replacement670)
    def With671(B, C, f, b, d, c, a, x, A):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = a**S(2)*f**S(2) - S(2)*a*c*d*f + b**S(2)*d*f + c**S(2)*d**S(2)
        if NonzeroQ(q):
            return True
        return False
    pattern671 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))/((d_ + x_**S(2)*WC('f', S(1)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons35, cons36, cons226, CustomConstraint(With671))
    def replacement671(B, C, f, b, d, c, a, x, A):

        q = a**S(2)*f**S(2) - S(2)*a*c*d*f + b**S(2)*d*f + c**S(2)*d**S(2)
        rubi.append(671)
        return Dist(S(1)/q, Int((A*a*f**S(2) - A*c*d*f + B*b*d*f - C*a*d*f + C*c*d**S(2) - f*x*(A*b*f - B*a*f + B*c*d - C*b*d))/(d + f*x**S(2)), x), x) + Dist(S(1)/q, Int((-A*a*c*f + A*b**S(2)*f + A*c**S(2)*d - B*a*b*f + C*a**S(2)*f - C*a*c*d + c*x*(A*b*f - B*a*f + B*c*d - C*b*d))/(a + b*x + c*x**S(2)), x), x)
    rule671 = ReplacementRule(pattern671, replacement671)
    def With672(C, f, b, d, c, a, x, A):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        q = a**S(2)*f**S(2) - S(2)*a*c*d*f + b**S(2)*d*f + c**S(2)*d**S(2)
        if NonzeroQ(q):
            return True
        return False
    pattern672 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))/((d_ + x_**S(2)*WC('f', S(1)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons36, cons226, CustomConstraint(With672))
    def replacement672(C, f, b, d, c, a, x, A):

        q = a**S(2)*f**S(2) - S(2)*a*c*d*f + b**S(2)*d*f + c**S(2)*d**S(2)
        rubi.append(672)
        return Dist(S(1)/q, Int((A*a*f**S(2) - A*c*d*f - C*a*d*f + C*c*d**S(2) - f*x*(A*b*f - C*b*d))/(d + f*x**S(2)), x), x) + Dist(S(1)/q, Int((-A*a*c*f + A*b**S(2)*f + A*c**S(2)*d + C*a**S(2)*f - C*a*c*d + c*x*(A*b*f - C*b*d))/(a + b*x + c*x**S(2)), x), x)
    rule672 = ReplacementRule(pattern672, replacement672)
    pattern673 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons226, cons394)
    def replacement673(B, C, e, f, b, d, c, a, x, A):
        rubi.append(673)
        return Dist(S(1)/c, Int((A*c - C*a + x*(B*c - C*b))/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x) + Dist(C/c, Int(S(1)/sqrt(d + e*x + f*x**S(2)), x), x)
    rule673 = ReplacementRule(pattern673, replacement673)
    pattern674 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))/((a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons226, cons394)
    def replacement674(C, e, f, b, d, c, a, x, A):
        rubi.append(674)
        return Dist(S(1)/c, Int((A*c - C*a - C*b*x)/((a + b*x + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x) + Dist(C/c, Int(S(1)/sqrt(d + e*x + f*x**S(2)), x), x)
    rule674 = ReplacementRule(pattern674, replacement674)
    pattern675 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons394)
    def replacement675(B, C, e, f, d, c, a, x, A):
        rubi.append(675)
        return Dist(S(1)/c, Int((A*c + B*c*x - C*a)/((a + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x) + Dist(C/c, Int(S(1)/sqrt(d + e*x + f*x**S(2)), x), x)
    rule675 = ReplacementRule(pattern675, replacement675)
    pattern676 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))/((a_ + x_**S(2)*WC('c', S(1)))*sqrt(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons36, cons394)
    def replacement676(C, f, d, c, a, A, x, e):
        rubi.append(676)
        return Dist(C/c, Int(S(1)/sqrt(d + e*x + f*x**S(2)), x), x) + Dist((A*c - C*a)/c, Int(S(1)/((a + c*x**S(2))*sqrt(d + e*x + f*x**S(2))), x), x)
    rule676 = ReplacementRule(pattern676, replacement676)
    pattern677 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))/(sqrt(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons35, cons36, cons226)
    def replacement677(B, C, f, b, d, c, a, x, A):
        rubi.append(677)
        return Dist(S(1)/c, Int((A*c - C*a + x*(B*c - C*b))/(sqrt(d + f*x**S(2))*(a + b*x + c*x**S(2))), x), x) + Dist(C/c, Int(S(1)/sqrt(d + f*x**S(2)), x), x)
    rule677 = ReplacementRule(pattern677, replacement677)
    pattern678 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))/(sqrt(x_**S(2)*WC('f', S(1)) + WC('d', S(0)))*(a_ + x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)))), x_), cons2, cons3, cons7, cons27, cons125, cons34, cons36, cons226)
    def replacement678(C, f, b, d, c, a, x, A):
        rubi.append(678)
        return Dist(S(1)/c, Int((A*c - C*a - C*b*x)/(sqrt(d + f*x**S(2))*(a + b*x + c*x**S(2))), x), x) + Dist(C/c, Int(S(1)/sqrt(d + f*x**S(2)), x), x)
    rule678 = ReplacementRule(pattern678, replacement678)
    pattern679 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons5, cons50, cons455)
    def replacement679(B, C, e, p, f, b, d, c, a, x, q, A):
        rubi.append(679)
        return Int((A + B*x + C*x**S(2))*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x)
    rule679 = ReplacementRule(pattern679, replacement679)
    pattern680 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons5, cons50, cons456)
    def replacement680(C, e, p, f, b, d, c, a, x, q, A):
        rubi.append(680)
        return Int((A + C*x**S(2))*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x)
    rule680 = ReplacementRule(pattern680, replacement680)
    pattern681 = Pattern(Integral((x_**S(2)*WC('c', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('C', S(1)) + x_*WC('B', S(1)) + WC('A', S(0)))*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons5, cons50, cons457)
    def replacement681(B, C, e, p, f, d, a, c, x, q, A):
        rubi.append(681)
        return Int((a + c*x**S(2))**p*(A + B*x + C*x**S(2))*(d + e*x + f*x**S(2))**q, x)
    rule681 = ReplacementRule(pattern681, replacement681)
    pattern682 = Pattern(Integral((x_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(x_**S(2)*WC('c', S(1)) + WC('a', S(0)))**p_*(x_**S(2)*WC('f', S(1)) + x_*WC('e', S(1)) + WC('d', S(0)))**q_, x_), cons2, cons7, cons27, cons48, cons125, cons34, cons36, cons5, cons50, cons458)
    def replacement682(C, e, p, f, d, a, c, x, q, A):
        rubi.append(682)
        return Int((A + C*x**S(2))*(a + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x)
    rule682 = ReplacementRule(pattern682, replacement682)
    pattern683 = Pattern(Integral((u_**S(2)*WC('C', S(1)) + u_*WC('B', S(1)) + WC('A', S(0)))*(u_**S(2)*WC('c', S(1)) + u_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons5, cons50, cons68, cons69)
    def replacement683(B, p, C, e, u, f, b, d, c, a, x, q, A):
        rubi.append(683)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((A + B*x + C*x**S(2))*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule683 = ReplacementRule(pattern683, replacement683)
    pattern684 = Pattern(Integral((u_*WC('B', S(1)) + WC('A', S(0)))*(u_**S(2)*WC('c', S(1)) + u_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons5, cons50, cons68, cons69)
    def replacement684(B, p, e, u, f, b, d, c, a, x, q, A):
        rubi.append(684)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((A + B*x)*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule684 = ReplacementRule(pattern684, replacement684)
    pattern685 = Pattern(Integral((u_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(u_**S(2)*WC('c', S(1)) + u_*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons5, cons50, cons68, cons69)
    def replacement685(p, C, e, u, f, b, d, c, a, x, q, A):
        rubi.append(685)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((A + C*x**S(2))*(a + b*x + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule685 = ReplacementRule(pattern685, replacement685)
    pattern686 = Pattern(Integral((u_**S(2)*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('C', S(1)) + u_*WC('B', S(1)) + WC('A', S(0)))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons5, cons50, cons68, cons69)
    def replacement686(B, p, C, e, u, f, d, a, c, x, q, A):
        rubi.append(686)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + c*x**S(2))**p*(A + B*x + C*x**S(2))*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule686 = ReplacementRule(pattern686, replacement686)
    pattern687 = Pattern(Integral((u_*WC('B', S(1)) + WC('A', S(0)))*(u_**S(2)*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons5, cons50, cons68, cons69)
    def replacement687(B, p, e, u, f, d, a, c, x, q, A):
        rubi.append(687)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((A + B*x)*(a + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule687 = ReplacementRule(pattern687, replacement687)
    pattern688 = Pattern(Integral((u_**S(2)*WC('C', S(1)) + WC('A', S(0)))*(u_**S(2)*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*(u_**S(2)*WC('f', S(1)) + u_*WC('e', S(1)) + WC('d', S(0)))**WC('q', S(1)), x_), cons2, cons7, cons27, cons48, cons125, cons34, cons36, cons5, cons50, cons68, cons69)
    def replacement688(C, p, e, u, f, d, a, c, x, q, A):
        rubi.append(688)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((A + C*x**S(2))*(a + c*x**S(2))**p*(d + e*x + f*x**S(2))**q, x), x, u), x)
    rule688 = ReplacementRule(pattern688, replacement688)
    return [rule189, rule190, rule191, rule192, rule193, rule194, rule195, rule196, rule197, rule198, rule199, rule200, rule201, rule202, rule203, rule204, rule205, rule206, rule207, rule208, rule209, rule210, rule211, rule212, rule213, rule214, rule215, rule216, rule217, rule218, rule219, rule220, rule221, rule222, rule223, rule224, rule225, rule226, rule227, rule228, rule229, rule230, rule231, rule232, rule233, rule234, rule235, rule236, rule237, rule238, rule239, rule240, rule241, rule242, rule243, rule244, rule245, rule246, rule247, rule248, rule249, rule250, rule251, rule252, rule253, rule254, rule255, rule256, rule257, rule258, rule259, rule260, rule261, rule262, rule263, rule264, rule265, rule266, rule267, rule268, rule269, rule270, rule271, rule272, rule273, rule274, rule275, rule276, rule277, rule278, rule279, rule280, rule281, rule282, rule283, rule284, rule285, rule286, rule287, rule288, rule289, rule290, rule291, rule292, rule293, rule294, rule295, rule296, rule297, rule298, rule299, rule300, rule301, rule302, rule303, rule304, rule305, rule306, rule307, rule308, rule309, rule310, rule311, rule312, rule313, rule314, rule315, rule316, rule317, rule318, rule319, rule320, rule321, rule322, rule323, rule324, rule325, rule326, rule327, rule328, rule329, rule330, rule331, rule332, rule333, rule334, rule335, rule336, rule337, rule338, rule339, rule340, rule341, rule342, rule343, rule344, rule345, rule346, rule347, rule348, rule349, rule350, rule351, rule352, rule353, rule354, rule355, rule356, rule357, rule358, rule359, rule360, rule361, rule362, rule363, rule364, rule365, rule366, rule367, rule368, rule369, rule370, rule371, rule372, rule373, rule374, rule375, rule376, rule377, rule378, rule379, rule380, rule381, rule382, rule383, rule384, rule385, rule386, rule387, rule388, rule389, rule390, rule391, rule392, rule393, rule394, rule395, rule396, rule397, rule398, rule399, rule400, rule401, rule402, rule403, rule404, rule405, rule406, rule407, rule408, rule409, rule410, rule411, rule412, rule413, rule414, rule415, rule416, rule417, rule418, rule419, rule420, rule421, rule422, rule423, rule424, rule425, rule426, rule427, rule428, rule429, rule430, rule431, rule432, rule433, rule434, rule435, rule436, rule437, rule438, rule439, rule440, rule441, rule442, rule443, rule444, rule445, rule446, rule447, rule448, rule449, rule450, rule451, rule452, rule453, rule454, rule455, rule456, rule457, rule458, rule459, rule460, rule461, rule462, rule463, rule464, rule465, rule466, rule467, rule468, rule469, rule470, rule471, rule472, rule473, rule474, rule475, rule476, rule477, rule478, rule479, rule480, rule481, rule482, rule483, rule484, rule485, rule486, rule487, rule488, rule489, rule490, rule491, rule492, rule493, rule494, rule495, rule496, rule497, rule498, rule499, rule500, rule501, rule502, rule503, rule504, rule505, rule506, rule507, rule508, rule509, rule510, rule511, rule512, rule513, rule514, rule515, rule516, rule517, rule518, rule519, rule520, rule521, rule522, rule523, rule524, rule525, rule526, rule527, rule528, rule529, rule530, rule531, rule532, rule533, rule534, rule535, rule536, rule537, rule538, rule539, rule540, rule541, rule542, rule543, rule544, rule545, rule546, rule547, rule548, rule549, rule550, rule551, rule552, rule553, rule554, rule555, rule556, rule557, rule558, rule559, rule560, rule561, rule562, rule563, rule564, rule565, rule566, rule567, rule568, rule569, rule570, rule571, rule572, rule573, rule574, rule575, rule576, rule577, rule578, rule579, rule580, rule581, rule582, rule583, rule584, rule585, rule586, rule587, rule588, rule589, rule590, rule591, rule592, rule593, rule594, rule595, rule596, rule597, rule598, rule599, rule600, rule601, rule602, rule603, rule604, rule605, rule606, rule607, rule608, rule609, rule610, rule611, rule612, rule613, rule614, rule615, rule616, rule617, rule618, rule619, rule620, rule621, rule622, rule623, rule624, rule625, rule626, rule627, rule628, rule629, rule630, rule631, rule632, rule633, rule634, rule635, rule636, rule637, rule638, rule639, rule640, rule641, rule642, rule643, rule644, rule645, rule646, rule647, rule648, rule649, rule650, rule651, rule652, rule653, rule654, rule655, rule656, rule657, rule658, rule659, rule660, rule661, rule662, rule663, rule664, rule665, rule666, rule667, rule668, rule669, rule670, rule671, rule672, rule673, rule674, rule675, rule676, rule677, rule678, rule679, rule680, rule681, rule682, rule683, rule684, rule685, rule686, rule687, rule688, ]
