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

def sine(rubi):
    from sympy.integrals.rubi.constraints import cons1249, cons72, cons66, cons2, cons3, cons48, cons125, cons21, cons4, cons1250, cons1251, cons1252, cons93, cons166, cons89, cons1253, cons31, cons1170, cons94, cons1254, cons1255, cons1256, cons1257, cons1258, cons1259, cons165, cons1260, cons18, cons23, cons521, cons7, cons27, cons808, cons1261, cons1262, cons1263, cons543, cons1264, cons1265, cons148, cons1266, cons87, cons43, cons448, cons1267, cons1268, cons1269, cons1270, cons1271, cons481, cons482, cons1272, cons1273, cons1274, cons1275, cons1276, cons208, cons5, cons17, cons13, cons137, cons1277, cons1278, cons1279, cons1280, cons1281, cons143, cons1282, cons1283, cons1284, cons1285, cons244, cons168, cons1286, cons1287, cons1288, cons146, cons1289, cons1290, cons1291, cons246, cons1292, cons1293, cons1294, cons1295, cons1296, cons84, cons1297, cons147, cons54, cons1298, cons1299, cons1300, cons1301, cons1302, cons62, cons267, cons1303, cons1304, cons1305, cons1306, cons515, cons272, cons1307, cons1308, cons71, cons70, cons1309, cons1310, cons1311, cons1312, cons346, cons1313, cons155, cons1314, cons1315, cons114, cons1316, cons1317, cons1318, cons1319, cons1320, cons1321, cons77, cons1322, cons1323, cons1324, cons1325, cons1326, cons1327, cons1328, cons463, cons88, cons1329, cons1330, cons85, cons1331, cons1332, cons1333, cons1334, cons1335, cons1336, cons1337, cons1338, cons1339, cons1340, cons1341, cons1342, cons1343, cons1344, cons1345, cons1346, cons1347, cons1348, cons1349, cons1350, cons1351, cons1352, cons1353, cons1354, cons1355, cons1356, cons1357, cons1358, cons1359, cons1360, cons1361, cons1362, cons1363, cons1364, cons142, cons335, cons1365, cons1366, cons1367, cons1368, cons1369, cons1370, cons170, cons1371, cons1372, cons1373, cons1374, cons1375, cons253, cons1376, cons1377, cons1378, cons1379, cons1380, cons358, cons1381, cons1382, cons1383, cons1384, cons1385, cons1386, cons1387, cons1388, cons1389, cons1390, cons1391, cons1392, cons1393, cons1394, cons213, cons584, cons1395, cons1396, cons1397, cons1398, cons1399, cons1400, cons1401, cons1402, cons1403, cons1404, cons1405, cons1406, cons1407, cons1408, cons1409, cons1410, cons1411, cons105, cons1412, cons1413, cons1414, cons1415, cons1416, cons1417, cons38, cons1418, cons34, cons35, cons1419, cons1420, cons1421, cons683, cons1422, cons1423, cons1424, cons1425, cons1426, cons1427, cons1428, cons1429, cons1430, cons1431, cons36, cons1228, cons1432, cons33, cons1433, cons1434, cons1435, cons1436, cons214, cons1437, cons1438, cons1439, cons1440, cons1441, cons1442, cons1443, cons1444, cons1445, cons1446, cons1152, cons1447, cons196, cons128, cons63, cons150, cons375, cons322, cons1448, cons1449, cons1450, cons1451, cons1452, cons1453, cons1454, cons76, cons1455, cons1456, cons1457, cons1458, cons1459, cons1460, cons1461, cons1462, cons1463, cons1464, cons1465, cons1466, cons1467, cons1468, cons1469, cons1470, cons1471, cons1245, cons1472, cons1473, cons1474, cons1475, cons1476, cons1477, cons1043, cons1478, cons1479, cons1480, cons1481, cons1482, cons1483, cons1484, cons1485, cons1486, cons1487, cons46, cons45, cons226, cons376, cons1116, cons176, cons1488, cons1489, cons245, cons247, cons1490, cons1491, cons1492, cons1493, cons810, cons811, cons744, cons1494, cons1495, cons53, cons596, cons1496, cons1497, cons489, cons1498, cons68, cons69, cons823, cons824, cons1499, cons1500, cons1501, cons1502, cons56, cons1503, cons1504, cons367, cons1505, cons356, cons854, cons1506, cons818, cons1131, cons47, cons239, cons1132, cons1133, cons1507, cons819

    pattern2164 = Pattern(Integral(u_, x_), cons1249)
    def replacement2164(x, u):
        rubi.append(2164)
        return Int(DeactivateTrig(u, x), x)
    rule2164 = ReplacementRule(pattern2164, replacement2164)
    pattern2165 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons4, cons72, cons66)
    def replacement2165(m, f, b, a, n, x, e):
        rubi.append(2165)
        return Simp((a*sin(e + f*x))**(m + S(1))*(b*cos(e + f*x))**(n + S(1))/(a*b*f*(m + S(1))), x)
    rule2165 = ReplacementRule(pattern2165, replacement2165)
    pattern2166 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('n', S(1)), x_), cons2, cons48, cons125, cons21, cons1250, cons1251)
    def replacement2166(m, f, a, n, x, e):
        rubi.append(2166)
        return Dist(S(1)/(a*f), Subst(Int(x**m*(S(1) - x**S(2)/a**S(2))**(n/S(2) + S(-1)/2), x), x, a*sin(e + f*x)), x)
    rule2166 = ReplacementRule(pattern2166, replacement2166)
    pattern2167 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('n', S(1)), x_), cons2, cons48, cons125, cons21, cons1250, cons1252)
    def replacement2167(m, f, a, n, x, e):
        rubi.append(2167)
        return -Dist(S(1)/(a*f), Subst(Int(x**m*(S(1) - x**S(2)/a**S(2))**(n/S(2) + S(-1)/2), x), x, a*cos(e + f*x)), x)
    rule2167 = ReplacementRule(pattern2167, replacement2167)
    pattern2168 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons166, cons89, cons1253)
    def replacement2168(m, f, b, a, n, x, e):
        rubi.append(2168)
        return Dist(a**S(2)*(m + S(-1))/(b**S(2)*(n + S(1))), Int((a*sin(e + f*x))**(m + S(-2))*(b*cos(e + f*x))**(n + S(2)), x), x) - Simp(a*(a*sin(e + f*x))**(m + S(-1))*(b*cos(e + f*x))**(n + S(1))/(b*f*(n + S(1))), x)
    rule2168 = ReplacementRule(pattern2168, replacement2168)
    pattern2169 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons166, cons89, cons1253)
    def replacement2169(m, f, b, a, n, x, e):
        rubi.append(2169)
        return Dist(a**S(2)*(m + S(-1))/(b**S(2)*(n + S(1))), Int((a*cos(e + f*x))**(m + S(-2))*(b*sin(e + f*x))**(n + S(2)), x), x) + Simp(a*(a*cos(e + f*x))**(m + S(-1))*(b*sin(e + f*x))**(n + S(1))/(b*f*(n + S(1))), x)
    rule2169 = ReplacementRule(pattern2169, replacement2169)
    pattern2170 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons166, cons1170)
    def replacement2170(m, f, b, a, n, x, e):
        rubi.append(2170)
        return Dist(a**S(2)*(m + S(-1))/(m + n), Int((a*sin(e + f*x))**(m + S(-2))*(b*cos(e + f*x))**n, x), x) - Simp(a*(a*sin(e + f*x))**(m + S(-1))*(b*cos(e + f*x))**(n + S(1))/(b*f*(m + n)), x)
    rule2170 = ReplacementRule(pattern2170, replacement2170)
    pattern2171 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons166, cons1170)
    def replacement2171(m, f, b, a, n, x, e):
        rubi.append(2171)
        return Dist(a**S(2)*(m + S(-1))/(m + n), Int((a*cos(e + f*x))**(m + S(-2))*(b*sin(e + f*x))**n, x), x) + Simp(a*(a*cos(e + f*x))**(m + S(-1))*(b*sin(e + f*x))**(n + S(1))/(b*f*(m + n)), x)
    rule2171 = ReplacementRule(pattern2171, replacement2171)
    pattern2172 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons94, cons1170)
    def replacement2172(m, f, b, a, n, x, e):
        rubi.append(2172)
        return Dist((m + n + S(2))/(a**S(2)*(m + S(1))), Int((a*sin(e + f*x))**(m + S(2))*(b*cos(e + f*x))**n, x), x) + Simp((a*sin(e + f*x))**(m + S(1))*(b*cos(e + f*x))**(n + S(1))/(a*b*f*(m + S(1))), x)
    rule2172 = ReplacementRule(pattern2172, replacement2172)
    pattern2173 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons94, cons1170)
    def replacement2173(m, f, b, a, n, x, e):
        rubi.append(2173)
        return Dist((m + n + S(2))/(a**S(2)*(m + S(1))), Int((a*cos(e + f*x))**(m + S(2))*(b*sin(e + f*x))**n, x), x) - Simp((a*cos(e + f*x))**(m + S(1))*(b*sin(e + f*x))**(n + S(1))/(a*b*f*(m + S(1))), x)
    rule2173 = ReplacementRule(pattern2173, replacement2173)
    pattern2174 = Pattern(Integral(sqrt(WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons1254)
    def replacement2174(f, b, a, x, e):
        rubi.append(2174)
        return Dist(sqrt(a*sin(e + f*x))*sqrt(b*cos(e + f*x))/sqrt(sin(S(2)*e + S(2)*f*x)), Int(sqrt(sin(S(2)*e + S(2)*f*x)), x), x)
    rule2174 = ReplacementRule(pattern2174, replacement2174)
    pattern2175 = Pattern(Integral(S(1)/(sqrt(WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons1254)
    def replacement2175(f, b, a, x, e):
        rubi.append(2175)
        return Dist(sqrt(sin(S(2)*e + S(2)*f*x))/(sqrt(a*sin(e + f*x))*sqrt(b*cos(e + f*x))), Int(S(1)/sqrt(sin(S(2)*e + S(2)*f*x)), x), x)
    rule2175 = ReplacementRule(pattern2175, replacement2175)
    def With2176(m, f, b, a, n, x, e):
        k = Denominator(m)
        rubi.append(2176)
        return Dist(a*b*k/f, Subst(Int(x**(k*(m + S(1)) + S(-1))/(a**S(2) + b**S(2)*x**(S(2)*k)), x), x, (a*sin(e + f*x))**(S(1)/k)*(b*cos(e + f*x))**(-S(1)/k)), x)
    pattern2176 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons1255, cons31, cons1256)
    rule2176 = ReplacementRule(pattern2176, With2176)
    def With2177(m, f, b, a, n, x, e):
        k = Denominator(m)
        rubi.append(2177)
        return -Dist(a*b*k/f, Subst(Int(x**(k*(m + S(1)) + S(-1))/(a**S(2) + b**S(2)*x**(S(2)*k)), x), x, (a*cos(e + f*x))**(S(1)/k)*(b*sin(e + f*x))**(-S(1)/k)), x)
    pattern2177 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons1255, cons31, cons1256)
    rule2177 = ReplacementRule(pattern2177, With2177)
    pattern2178 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1257)
    def replacement2178(m, f, b, a, n, x, e):
        rubi.append(2178)
        return Simp(b**(S(2)*IntPart(n/S(2) + S(-1)/2) + S(1))*(a*sin(e + f*x))**(m + S(1))*(b*cos(e + f*x))**(S(2)*FracPart(n/S(2) + S(-1)/2))*(cos(e + f*x)**S(2))**(-FracPart(n/S(2) + S(-1)/2))*Hypergeometric2F1(m/S(2) + S(1)/2, -n/S(2) + S(1)/2, m/S(2) + S(3)/2, sin(e + f*x)**S(2))/(a*f*(m + S(1))), x)
    rule2178 = ReplacementRule(pattern2178, replacement2178)
    pattern2179 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1258)
    def replacement2179(m, f, b, a, n, x, e):
        rubi.append(2179)
        return -Simp(b**(S(2)*IntPart(n/S(2) + S(-1)/2) + S(1))*(a*cos(e + f*x))**(m + S(1))*(b*sin(e + f*x))**(S(2)*FracPart(n/S(2) + S(-1)/2))*(sin(e + f*x)**S(2))**(-FracPart(n/S(2) + S(-1)/2))*Hypergeometric2F1(m/S(2) + S(1)/2, -n/S(2) + S(1)/2, m/S(2) + S(3)/2, cos(e + f*x)**S(2))/(a*f*(m + S(1))), x)
    rule2179 = ReplacementRule(pattern2179, replacement2179)
    pattern2180 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1259, cons66)
    def replacement2180(m, f, b, a, n, x, e):
        rubi.append(2180)
        return Simp(b*(a*sin(e + f*x))**(m + S(1))*(b/cos(e + f*x))**(n + S(-1))/(a*f*(m + S(1))), x)
    rule2180 = ReplacementRule(pattern2180, replacement2180)
    pattern2181 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons4, cons1259, cons66)
    def replacement2181(m, f, b, a, n, x, e):
        rubi.append(2181)
        return -Simp(b*(a*cos(e + f*x))**(m + S(1))*(b/sin(e + f*x))**(n + S(-1))/(a*f*(m + S(1))), x)
    rule2181 = ReplacementRule(pattern2181, replacement2181)
    pattern2182 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons166, cons165, cons1170)
    def replacement2182(m, f, b, a, n, x, e):
        rubi.append(2182)
        return -Dist(a**S(2)*b**S(2)*(m + S(-1))/(n + S(-1)), Int((a*sin(e + f*x))**(m + S(-2))*(b/cos(e + f*x))**(n + S(-2)), x), x) + Simp(a*b*(a*sin(e + f*x))**(m + S(-1))*(b/cos(e + f*x))**(n + S(-1))/(f*(n + S(-1))), x)
    rule2182 = ReplacementRule(pattern2182, replacement2182)
    pattern2183 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons93, cons166, cons165, cons1170)
    def replacement2183(m, f, b, a, n, x, e):
        rubi.append(2183)
        return -Dist(a**S(2)*b**S(2)*(m + S(-1))/(n + S(-1)), Int((a*cos(e + f*x))**(m + S(-2))*(b/sin(e + f*x))**(n + S(-2)), x), x) - Simp(a*b*(a*cos(e + f*x))**(m + S(-1))*(b/sin(e + f*x))**(n + S(-1))/(f*(n + S(-1))), x)
    rule2183 = ReplacementRule(pattern2183, replacement2183)
    pattern2184 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons166, cons1260, cons1170)
    def replacement2184(m, f, b, a, n, x, e):
        rubi.append(2184)
        return Dist(a**S(2)*(m + S(-1))/(m - n), Int((a*sin(e + f*x))**(m + S(-2))*(b/cos(e + f*x))**n, x), x) - Simp(a*b*(a*sin(e + f*x))**(m + S(-1))*(b/cos(e + f*x))**(n + S(-1))/(f*(m - n)), x)
    rule2184 = ReplacementRule(pattern2184, replacement2184)
    pattern2185 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons166, cons1260, cons1170)
    def replacement2185(m, f, b, a, n, x, e):
        rubi.append(2185)
        return Dist(a**S(2)*(m + S(-1))/(m - n), Int((a*cos(e + f*x))**(m + S(-2))*(b/sin(e + f*x))**n, x), x) + Simp(a*b*(a*cos(e + f*x))**(m + S(-1))*(b/sin(e + f*x))**(n + S(-1))/(f*(m - n)), x)
    rule2185 = ReplacementRule(pattern2185, replacement2185)
    pattern2186 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons94, cons1170)
    def replacement2186(m, f, b, a, n, x, e):
        rubi.append(2186)
        return Dist((m - n + S(2))/(a**S(2)*(m + S(1))), Int((a*sin(e + f*x))**(m + S(2))*(b/cos(e + f*x))**n, x), x) + Simp(b*(a*sin(e + f*x))**(m + S(1))*(b/cos(e + f*x))**(n + S(-1))/(a*f*(m + S(1))), x)
    rule2186 = ReplacementRule(pattern2186, replacement2186)
    pattern2187 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons4, cons31, cons94, cons1170)
    def replacement2187(m, f, b, a, n, x, e):
        rubi.append(2187)
        return Dist((m - n + S(2))/(a**S(2)*(m + S(1))), Int((a*cos(e + f*x))**(m + S(2))*(b/sin(e + f*x))**n, x), x) - Simp(b*(a*cos(e + f*x))**(m + S(1))*(b/sin(e + f*x))**(n + S(-1))/(a*f*(m + S(1))), x)
    rule2187 = ReplacementRule(pattern2187, replacement2187)
    pattern2188 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons18, cons23)
    def replacement2188(m, f, b, a, n, x, e):
        rubi.append(2188)
        return Dist((cos(e + f*x)/b)**(FracPart(n) + S(1))*(b/cos(e + f*x))**(FracPart(n) + S(1)), Int((a*sin(e + f*x))**m*(cos(e + f*x)/b)**(-n), x), x)
    rule2188 = ReplacementRule(pattern2188, replacement2188)
    pattern2189 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons18, cons23)
    def replacement2189(m, f, b, a, n, x, e):
        rubi.append(2189)
        return Dist((sin(e + f*x)/b)**(FracPart(n) + S(1))*(b/sin(e + f*x))**(FracPart(n) + S(1)), Int((a*cos(e + f*x))**m*(sin(e + f*x)/b)**(-n), x), x)
    rule2189 = ReplacementRule(pattern2189, replacement2189)
    pattern2190 = Pattern(Integral((WC('a', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons18, cons23)
    def replacement2190(m, f, b, a, n, x, e):
        rubi.append(2190)
        return Dist((a*b)**IntPart(n)*(a*sin(e + f*x))**FracPart(n)*(b/sin(e + f*x))**FracPart(n), Int((a*sin(e + f*x))**(m - n), x), x)
    rule2190 = ReplacementRule(pattern2190, replacement2190)
    pattern2191 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons48, cons125, cons21, cons4, cons18, cons23)
    def replacement2191(m, f, b, a, n, x, e):
        rubi.append(2191)
        return Dist((a*b)**IntPart(n)*(a*cos(e + f*x))**FracPart(n)*(b/cos(e + f*x))**FracPart(n), Int((a*cos(e + f*x))**(m - n), x), x)
    rule2191 = ReplacementRule(pattern2191, replacement2191)
    pattern2192 = Pattern(Integral(sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_, x_), cons7, cons27, cons521)
    def replacement2192(d, c, n, x):
        rubi.append(2192)
        return -Dist(S(1)/d, Subst(Int((-x**S(2) + S(1))**(n/S(2))/sqrt(-x**S(2) + S(1)), x), x, cos(c + d*x)), x)
    rule2192 = ReplacementRule(pattern2192, replacement2192)
    pattern2193 = Pattern(Integral(cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_, x_), cons7, cons27, cons521)
    def replacement2193(d, c, n, x):
        rubi.append(2193)
        return Dist(S(1)/d, Subst(Int((-x**S(2) + S(1))**(n/S(2))/sqrt(-x**S(2) + S(1)), x), x, sin(c + d*x)), x)
    rule2193 = ReplacementRule(pattern2193, replacement2193)
    pattern2194 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons808, cons165)
    def replacement2194(b, d, c, n, x):
        rubi.append(2194)
        return Dist(b**S(2)*(n + S(-1))/n, Int((b*sin(c + d*x))**(n + S(-2)), x), x) - Simp(b*(b*sin(c + d*x))**(n + S(-1))*cos(c + d*x)/(d*n), x)
    rule2194 = ReplacementRule(pattern2194, replacement2194)
    pattern2195 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons808, cons165)
    def replacement2195(b, d, c, n, x):
        rubi.append(2195)
        return Dist(b**S(2)*(n + S(-1))/n, Int((b*cos(c + d*x))**(n + S(-2)), x), x) + Simp(b*(b*cos(c + d*x))**(n + S(-1))*sin(c + d*x)/(d*n), x)
    rule2195 = ReplacementRule(pattern2195, replacement2195)
    pattern2196 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons808, cons89)
    def replacement2196(b, d, c, n, x):
        rubi.append(2196)
        return Dist((n + S(2))/(b**S(2)*(n + S(1))), Int((b*sin(c + d*x))**(n + S(2)), x), x) + Simp((b*sin(c + d*x))**(n + S(1))*cos(c + d*x)/(b*d*(n + S(1))), x)
    rule2196 = ReplacementRule(pattern2196, replacement2196)
    pattern2197 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons808, cons89)
    def replacement2197(b, d, c, n, x):
        rubi.append(2197)
        return Dist((n + S(2))/(b**S(2)*(n + S(1))), Int((b*cos(c + d*x))**(n + S(2)), x), x) - Simp((b*cos(c + d*x))**(n + S(1))*sin(c + d*x)/(b*d*(n + S(1))), x)
    rule2197 = ReplacementRule(pattern2197, replacement2197)
    pattern2198 = Pattern(Integral(sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons1261)
    def replacement2198(d, c, x):
        rubi.append(2198)
        return -Simp(cos(c + d*x)/d, x)
    rule2198 = ReplacementRule(pattern2198, replacement2198)
    pattern2199 = Pattern(Integral(cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons7, cons1262)
    def replacement2199(d, c, x):
        rubi.append(2199)
        return Simp(sin(c + d*x)/d, x)
    rule2199 = ReplacementRule(pattern2199, replacement2199)
    pattern2200 = Pattern(Integral(sqrt(sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons7, cons27, cons1261)
    def replacement2200(d, c, x):
        rubi.append(2200)
        return Simp(S(2)*EllipticE(-Pi/S(4) + c/S(2) + d*x/S(2), S(2))/d, x)
    rule2200 = ReplacementRule(pattern2200, replacement2200)
    pattern2201 = Pattern(Integral(sqrt(cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons7, cons27, cons1261)
    def replacement2201(d, c, x):
        rubi.append(2201)
        return Simp(S(2)*EllipticE(c/S(2) + d*x/S(2), S(2))/d, x)
    rule2201 = ReplacementRule(pattern2201, replacement2201)
    pattern2202 = Pattern(Integral(sqrt(b_*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons3, cons7, cons27, cons1263)
    def replacement2202(d, c, b, x):
        rubi.append(2202)
        return Dist(sqrt(b*sin(c + d*x))/sqrt(sin(c + d*x)), Int(sqrt(sin(c + d*x)), x), x)
    rule2202 = ReplacementRule(pattern2202, replacement2202)
    pattern2203 = Pattern(Integral(sqrt(b_*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons3, cons7, cons27, cons1263)
    def replacement2203(d, c, b, x):
        rubi.append(2203)
        return Dist(sqrt(b*cos(c + d*x))/sqrt(cos(c + d*x)), Int(sqrt(cos(c + d*x)), x), x)
    rule2203 = ReplacementRule(pattern2203, replacement2203)
    pattern2204 = Pattern(Integral(S(1)/sqrt(sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons7, cons27, cons1261)
    def replacement2204(d, c, x):
        rubi.append(2204)
        return Simp(S(2)*EllipticF(-Pi/S(4) + c/S(2) + d*x/S(2), S(2))/d, x)
    rule2204 = ReplacementRule(pattern2204, replacement2204)
    pattern2205 = Pattern(Integral(S(1)/sqrt(cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons7, cons27, cons1261)
    def replacement2205(d, c, x):
        rubi.append(2205)
        return Simp(S(2)*EllipticF(c/S(2) + d*x/S(2), S(2))/d, x)
    rule2205 = ReplacementRule(pattern2205, replacement2205)
    pattern2206 = Pattern(Integral(S(1)/sqrt(b_*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons3, cons7, cons27, cons1263)
    def replacement2206(d, c, b, x):
        rubi.append(2206)
        return Dist(sqrt(sin(c + d*x))/sqrt(b*sin(c + d*x)), Int(S(1)/sqrt(sin(c + d*x)), x), x)
    rule2206 = ReplacementRule(pattern2206, replacement2206)
    pattern2207 = Pattern(Integral(S(1)/sqrt(b_*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons3, cons7, cons27, cons1263)
    def replacement2207(d, c, b, x):
        rubi.append(2207)
        return Dist(sqrt(cos(c + d*x))/sqrt(b*cos(c + d*x)), Int(S(1)/sqrt(cos(c + d*x)), x), x)
    rule2207 = ReplacementRule(pattern2207, replacement2207)
    pattern2208 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons4, cons543)
    def replacement2208(b, d, c, n, x):
        rubi.append(2208)
        return Simp((b*sin(c + d*x))**(n + S(1))*Hypergeometric2F1(S(1)/2, n/S(2) + S(1)/2, n/S(2) + S(3)/2, sin(c + d*x)**S(2))*cos(c + d*x)/(b*d*(n + S(1))*sqrt(cos(c + d*x)**S(2))), x)
    rule2208 = ReplacementRule(pattern2208, replacement2208)
    pattern2209 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons3, cons7, cons27, cons4, cons543)
    def replacement2209(b, d, c, n, x):
        rubi.append(2209)
        return -Simp((b*cos(c + d*x))**(n + S(1))*Hypergeometric2F1(S(1)/2, n/S(2) + S(1)/2, n/S(2) + S(3)/2, cos(c + d*x)**S(2))*sin(c + d*x)/(b*d*(n + S(1))*sqrt(sin(c + d*x)**S(2))), x)
    rule2209 = ReplacementRule(pattern2209, replacement2209)
    pattern2210 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons1264)
    def replacement2210(b, d, c, a, x):
        rubi.append(2210)
        return Dist(S(2)*a*b, Int(sin(c + d*x), x), x) + Simp(x*(S(2)*a**S(2) + b**S(2))/S(2), x) - Simp(b**S(2)*sin(c + d*x)*cos(c + d*x)/(S(2)*d), x)
    rule2210 = ReplacementRule(pattern2210, replacement2210)
    pattern2211 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons1264)
    def replacement2211(b, d, c, a, x):
        rubi.append(2211)
        return Dist(S(2)*a*b, Int(cos(c + d*x), x), x) + Simp(x*(S(2)*a**S(2) + b**S(2))/S(2), x) + Simp(b**S(2)*sin(c + d*x)*cos(c + d*x)/(S(2)*d), x)
    rule2211 = ReplacementRule(pattern2211, replacement2211)
    pattern2212 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons148)
    def replacement2212(b, d, c, a, n, x):
        rubi.append(2212)
        return Int(ExpandTrig((a + b*sin(c + d*x))**n, x), x)
    rule2212 = ReplacementRule(pattern2212, replacement2212)
    pattern2213 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons148)
    def replacement2213(b, d, c, a, n, x):
        rubi.append(2213)
        return Int(ExpandTrig((a + b*cos(c + d*x))**n, x), x)
    rule2213 = ReplacementRule(pattern2213, replacement2213)
    pattern2214 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement2214(b, d, c, a, x):
        rubi.append(2214)
        return Simp(-S(2)*b*cos(c + d*x)/(d*sqrt(a + b*sin(c + d*x))), x)
    rule2214 = ReplacementRule(pattern2214, replacement2214)
    pattern2215 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement2215(b, d, c, a, x):
        rubi.append(2215)
        return Simp(S(2)*b*sin(c + d*x)/(d*sqrt(a + b*cos(c + d*x))), x)
    rule2215 = ReplacementRule(pattern2215, replacement2215)
    pattern2216 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1265, cons1266)
    def replacement2216(b, d, c, a, n, x):
        rubi.append(2216)
        return Dist(a*(S(2)*n + S(-1))/n, Int((a + b*sin(c + d*x))**(n + S(-1)), x), x) - Simp(b*(a + b*sin(c + d*x))**(n + S(-1))*cos(c + d*x)/(d*n), x)
    rule2216 = ReplacementRule(pattern2216, replacement2216)
    pattern2217 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1265, cons1266)
    def replacement2217(b, d, c, a, n, x):
        rubi.append(2217)
        return Dist(a*(S(2)*n + S(-1))/n, Int((a + b*cos(c + d*x))**(n + S(-1)), x), x) + Simp(b*(a + b*cos(c + d*x))**(n + S(-1))*sin(c + d*x)/(d*n), x)
    rule2217 = ReplacementRule(pattern2217, replacement2217)
    pattern2218 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement2218(b, d, c, a, x):
        rubi.append(2218)
        return -Simp(cos(c + d*x)/(d*(a*sin(c + d*x) + b)), x)
    rule2218 = ReplacementRule(pattern2218, replacement2218)
    pattern2219 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement2219(b, d, c, a, x):
        rubi.append(2219)
        return Simp(sin(c + d*x)/(d*(a*cos(c + d*x) + b)), x)
    rule2219 = ReplacementRule(pattern2219, replacement2219)
    pattern2220 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement2220(b, d, c, a, x):
        rubi.append(2220)
        return Dist(-S(2)/d, Subst(Int(S(1)/(S(2)*a - x**S(2)), x), x, b*cos(c + d*x)/sqrt(a + b*sin(c + d*x))), x)
    rule2220 = ReplacementRule(pattern2220, replacement2220)
    pattern2221 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1265)
    def replacement2221(b, d, c, a, x):
        rubi.append(2221)
        return Dist(S(2)/d, Subst(Int(S(1)/(S(2)*a - x**S(2)), x), x, b*sin(c + d*x)/sqrt(a + b*cos(c + d*x))), x)
    rule2221 = ReplacementRule(pattern2221, replacement2221)
    pattern2222 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1265, cons87, cons89, cons808)
    def replacement2222(b, d, c, a, n, x):
        rubi.append(2222)
        return Dist((n + S(1))/(a*(S(2)*n + S(1))), Int((a + b*sin(c + d*x))**(n + S(1)), x), x) + Simp(b*(a + b*sin(c + d*x))**n*cos(c + d*x)/(a*d*(S(2)*n + S(1))), x)
    rule2222 = ReplacementRule(pattern2222, replacement2222)
    pattern2223 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1265, cons87, cons89, cons808)
    def replacement2223(b, d, c, a, n, x):
        rubi.append(2223)
        return Dist((n + S(1))/(a*(S(2)*n + S(1))), Int((a + b*cos(c + d*x))**(n + S(1)), x), x) - Simp(b*(a + b*cos(c + d*x))**n*sin(c + d*x)/(a*d*(S(2)*n + S(1))), x)
    rule2223 = ReplacementRule(pattern2223, replacement2223)
    pattern2224 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons543, cons43)
    def replacement2224(b, d, c, a, n, x):
        rubi.append(2224)
        return -Simp(S(2)**(n + S(1)/2)*a**(n + S(-1)/2)*b*Hypergeometric2F1(S(1)/2, -n + S(1)/2, S(3)/2, S(1)/2 - b*sin(c + d*x)/(S(2)*a))*cos(c + d*x)/(d*sqrt(a + b*sin(c + d*x))), x)
    rule2224 = ReplacementRule(pattern2224, replacement2224)
    pattern2225 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons543, cons43)
    def replacement2225(b, d, c, a, n, x):
        rubi.append(2225)
        return Simp(S(2)**(n + S(1)/2)*a**(n + S(-1)/2)*b*Hypergeometric2F1(S(1)/2, -n + S(1)/2, S(3)/2, S(1)/2 - b*cos(c + d*x)/(S(2)*a))*sin(c + d*x)/(d*sqrt(a + b*cos(c + d*x))), x)
    rule2225 = ReplacementRule(pattern2225, replacement2225)
    pattern2226 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons543, cons448)
    def replacement2226(b, d, c, a, n, x):
        rubi.append(2226)
        return Dist(a**IntPart(n)*(S(1) + b*sin(c + d*x)/a)**(-FracPart(n))*(a + b*sin(c + d*x))**FracPart(n), Int((S(1) + b*sin(c + d*x)/a)**n, x), x)
    rule2226 = ReplacementRule(pattern2226, replacement2226)
    pattern2227 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1265, cons543, cons448)
    def replacement2227(b, d, c, a, n, x):
        rubi.append(2227)
        return Dist(a**IntPart(n)*(S(1) + b*cos(c + d*x)/a)**(-FracPart(n))*(a + b*cos(c + d*x))**FracPart(n), Int((S(1) + b*cos(c + d*x)/a)**n, x), x)
    rule2227 = ReplacementRule(pattern2227, replacement2227)
    pattern2228 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1268)
    def replacement2228(b, d, c, a, x):
        rubi.append(2228)
        return Simp(S(2)*sqrt(a + b)*EllipticE(-Pi/S(4) + c/S(2) + d*x/S(2), S(2)*b/(a + b))/d, x)
    rule2228 = ReplacementRule(pattern2228, replacement2228)
    pattern2229 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1268)
    def replacement2229(b, d, c, a, x):
        rubi.append(2229)
        return Simp(S(2)*sqrt(a + b)*EllipticE(c/S(2) + d*x/S(2), S(2)*b/(a + b))/d, x)
    rule2229 = ReplacementRule(pattern2229, replacement2229)
    pattern2230 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1269)
    def replacement2230(b, d, c, a, x):
        rubi.append(2230)
        return Simp(S(2)*sqrt(a - b)*EllipticE(Pi/S(4) + c/S(2) + d*x/S(2), -S(2)*b/(a - b))/d, x)
    rule2230 = ReplacementRule(pattern2230, replacement2230)
    pattern2231 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1269)
    def replacement2231(b, d, c, a, x):
        rubi.append(2231)
        return Simp(S(2)*sqrt(a - b)*EllipticE(Pi/S(2) + c/S(2) + d*x/S(2), -S(2)*b/(a - b))/d, x)
    rule2231 = ReplacementRule(pattern2231, replacement2231)
    pattern2232 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1270)
    def replacement2232(b, d, c, a, x):
        rubi.append(2232)
        return Dist(sqrt(a + b*sin(c + d*x))/sqrt((a + b*sin(c + d*x))/(a + b)), Int(sqrt(a/(a + b) + b*sin(c + d*x)/(a + b)), x), x)
    rule2232 = ReplacementRule(pattern2232, replacement2232)
    pattern2233 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1270)
    def replacement2233(b, d, c, a, x):
        rubi.append(2233)
        return Dist(sqrt(a + b*cos(c + d*x))/sqrt((a + b*cos(c + d*x))/(a + b)), Int(sqrt(a/(a + b) + b*cos(c + d*x)/(a + b)), x), x)
    rule2233 = ReplacementRule(pattern2233, replacement2233)
    pattern2234 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1267, cons87, cons165, cons808)
    def replacement2234(b, d, c, a, n, x):
        rubi.append(2234)
        return Dist(S(1)/n, Int((a + b*sin(c + d*x))**(n + S(-2))*Simp(a**S(2)*n + a*b*(S(2)*n + S(-1))*sin(c + d*x) + b**S(2)*(n + S(-1)), x), x), x) - Simp(b*(a + b*sin(c + d*x))**(n + S(-1))*cos(c + d*x)/(d*n), x)
    rule2234 = ReplacementRule(pattern2234, replacement2234)
    pattern2235 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1267, cons87, cons165, cons808)
    def replacement2235(b, d, c, a, n, x):
        rubi.append(2235)
        return Dist(S(1)/n, Int((a + b*cos(c + d*x))**(n + S(-2))*Simp(a**S(2)*n + a*b*(S(2)*n + S(-1))*cos(c + d*x) + b**S(2)*(n + S(-1)), x), x), x) + Simp(b*(a + b*cos(c + d*x))**(n + S(-1))*sin(c + d*x)/(d*n), x)
    rule2235 = ReplacementRule(pattern2235, replacement2235)
    def With2236(b, d, c, a, x):
        q = Rt(a**S(2) - b**S(2), S(2))
        rubi.append(2236)
        return Simp(x/q, x) + Simp(S(2)*ArcTan(b*cos(c + d*x)/(a + b*sin(c + d*x) + q))/(d*q), x)
    pattern2236 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1271, cons481)
    rule2236 = ReplacementRule(pattern2236, With2236)
    def With2237(b, d, c, a, x):
        q = Rt(a**S(2) - b**S(2), S(2))
        rubi.append(2237)
        return Simp(x/q, x) - Simp(S(2)*ArcTan(b*sin(c + d*x)/(a + b*cos(c + d*x) + q))/(d*q), x)
    pattern2237 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1271, cons481)
    rule2237 = ReplacementRule(pattern2237, With2237)
    def With2238(b, d, c, a, x):
        q = Rt(a**S(2) - b**S(2), S(2))
        rubi.append(2238)
        return -Simp(x/q, x) - Simp(S(2)*ArcTan(b*cos(c + d*x)/(a + b*sin(c + d*x) - q))/(d*q), x)
    pattern2238 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1271, cons482)
    rule2238 = ReplacementRule(pattern2238, With2238)
    def With2239(b, d, c, a, x):
        q = Rt(a**S(2) - b**S(2), S(2))
        rubi.append(2239)
        return -Simp(x/q, x) + Simp(S(2)*ArcTan(b*sin(c + d*x)/(a + b*cos(c + d*x) - q))/(d*q), x)
    pattern2239 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1271, cons482)
    rule2239 = ReplacementRule(pattern2239, With2239)
    def With2240(b, d, c, a, x):
        e = FreeFactors(tan(-Pi/S(4) + c/S(2) + d*x/S(2)), x)
        rubi.append(2240)
        return Dist(S(2)*e/d, Subst(Int(S(1)/(a + b + e**S(2)*x**S(2)*(a - b)), x), x, tan(-Pi/S(4) + c/S(2) + d*x/S(2))/e), x)
    pattern2240 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1272)
    rule2240 = ReplacementRule(pattern2240, With2240)
    def With2241(b, d, c, a, x):
        e = FreeFactors(tan(c/S(2) + d*x/S(2)), x)
        rubi.append(2241)
        return Dist(S(2)*e/d, Subst(Int(S(1)/(a*e**S(2)*x**S(2) + a + S(2)*b*e*x), x), x, tan(c/S(2) + d*x/S(2))/e), x)
    pattern2241 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267)
    rule2241 = ReplacementRule(pattern2241, With2241)
    def With2242(b, d, c, a, x):
        e = FreeFactors(tan(c/S(2) + d*x/S(2)), x)
        rubi.append(2242)
        return Dist(S(2)*e/d, Subst(Int(S(1)/(a + b + e**S(2)*x**S(2)*(a - b)), x), x, tan(c/S(2) + d*x/S(2))/e), x)
    pattern2242 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267)
    rule2242 = ReplacementRule(pattern2242, With2242)
    pattern2243 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1268)
    def replacement2243(b, d, c, a, x):
        rubi.append(2243)
        return Simp(S(2)*EllipticF(-Pi/S(4) + c/S(2) + d*x/S(2), S(2)*b/(a + b))/(d*sqrt(a + b)), x)
    rule2243 = ReplacementRule(pattern2243, replacement2243)
    pattern2244 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1268)
    def replacement2244(b, d, c, a, x):
        rubi.append(2244)
        return Simp(S(2)*EllipticF(c/S(2) + d*x/S(2), S(2)*b/(a + b))/(d*sqrt(a + b)), x)
    rule2244 = ReplacementRule(pattern2244, replacement2244)
    pattern2245 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1269)
    def replacement2245(b, d, c, a, x):
        rubi.append(2245)
        return Simp(S(2)*EllipticF(Pi/S(4) + c/S(2) + d*x/S(2), -S(2)*b/(a - b))/(d*sqrt(a - b)), x)
    rule2245 = ReplacementRule(pattern2245, replacement2245)
    pattern2246 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1269)
    def replacement2246(b, d, c, a, x):
        rubi.append(2246)
        return Simp(S(2)*EllipticF(Pi/S(2) + c/S(2) + d*x/S(2), -S(2)*b/(a - b))/(d*sqrt(a - b)), x)
    rule2246 = ReplacementRule(pattern2246, replacement2246)
    pattern2247 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1270)
    def replacement2247(b, d, c, a, x):
        rubi.append(2247)
        return Dist(sqrt((a + b*sin(c + d*x))/(a + b))/sqrt(a + b*sin(c + d*x)), Int(S(1)/sqrt(a/(a + b) + b*sin(c + d*x)/(a + b)), x), x)
    rule2247 = ReplacementRule(pattern2247, replacement2247)
    pattern2248 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1267, cons1270)
    def replacement2248(b, d, c, a, x):
        rubi.append(2248)
        return Dist(sqrt((a + b*cos(c + d*x))/(a + b))/sqrt(a + b*cos(c + d*x)), Int(S(1)/sqrt(a/(a + b) + b*cos(c + d*x)/(a + b)), x), x)
    rule2248 = ReplacementRule(pattern2248, replacement2248)
    pattern2249 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1267, cons87, cons89, cons808)
    def replacement2249(b, d, c, a, n, x):
        rubi.append(2249)
        return Dist(S(1)/((a**S(2) - b**S(2))*(n + S(1))), Int((a + b*sin(c + d*x))**(n + S(1))*Simp(a*(n + S(1)) - b*(n + S(2))*sin(c + d*x), x), x), x) - Simp(b*(a + b*sin(c + d*x))**(n + S(1))*cos(c + d*x)/(d*(a**S(2) - b**S(2))*(n + S(1))), x)
    rule2249 = ReplacementRule(pattern2249, replacement2249)
    pattern2250 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1267, cons87, cons89, cons808)
    def replacement2250(b, d, c, a, n, x):
        rubi.append(2250)
        return Dist(S(1)/((a**S(2) - b**S(2))*(n + S(1))), Int((a + b*cos(c + d*x))**(n + S(1))*Simp(a*(n + S(1)) - b*(n + S(2))*cos(c + d*x), x), x), x) + Simp(b*(a + b*cos(c + d*x))**(n + S(1))*sin(c + d*x)/(d*(a**S(2) - b**S(2))*(n + S(1))), x)
    rule2250 = ReplacementRule(pattern2250, replacement2250)
    pattern2251 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1267, cons543)
    def replacement2251(b, d, c, a, n, x):
        rubi.append(2251)
        return Dist(cos(c + d*x)/(d*sqrt(-sin(c + d*x) + S(1))*sqrt(sin(c + d*x) + S(1))), Subst(Int((a + b*x)**n/(sqrt(-x + S(1))*sqrt(x + S(1))), x), x, sin(c + d*x)), x)
    rule2251 = ReplacementRule(pattern2251, replacement2251)
    pattern2252 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1267, cons543)
    def replacement2252(b, d, c, a, n, x):
        rubi.append(2252)
        return -Dist(sin(c + d*x)/(d*sqrt(-cos(c + d*x) + S(1))*sqrt(cos(c + d*x) + S(1))), Subst(Int((a + b*x)**n/(sqrt(-x + S(1))*sqrt(x + S(1))), x), x, cos(c + d*x)), x)
    rule2252 = ReplacementRule(pattern2252, replacement2252)
    pattern2253 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1273)
    def replacement2253(b, d, c, a, n, x):
        rubi.append(2253)
        return Int((a + b*sin(S(2)*c + S(2)*d*x)/S(2))**n, x)
    rule2253 = ReplacementRule(pattern2253, replacement2253)
    pattern2254 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1274, cons1265, cons1275)
    def replacement2254(p, m, f, b, a, x, e):
        rubi.append(2254)
        return Dist(b**(-p)/f, Subst(Int((a - x)**(p/S(2) + S(-1)/2)*(a + x)**(m + p/S(2) + S(-1)/2), x), x, b*sin(e + f*x)), x)
    rule2254 = ReplacementRule(pattern2254, replacement2254)
    pattern2255 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1274, cons1265, cons1275)
    def replacement2255(p, m, f, b, a, x, e):
        rubi.append(2255)
        return -Dist(b**(-p)/f, Subst(Int((a - x)**(p/S(2) + S(-1)/2)*(a + x)**(m + p/S(2) + S(-1)/2), x), x, b*cos(e + f*x)), x)
    rule2255 = ReplacementRule(pattern2255, replacement2255)
    pattern2256 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1274, cons1267)
    def replacement2256(p, m, f, b, a, x, e):
        rubi.append(2256)
        return Dist(b**(-p)/f, Subst(Int((a + x)**m*(b**S(2) - x**S(2))**(p/S(2) + S(-1)/2), x), x, b*sin(e + f*x)), x)
    rule2256 = ReplacementRule(pattern2256, replacement2256)
    pattern2257 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1274, cons1267)
    def replacement2257(p, m, f, b, a, x, e):
        rubi.append(2257)
        return -Dist(b**(-p)/f, Subst(Int((a + x)**m*(b**S(2) - x**S(2))**(p/S(2) + S(-1)/2), x), x, b*cos(e + f*x)), x)
    rule2257 = ReplacementRule(pattern2257, replacement2257)
    pattern2258 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1276)
    def replacement2258(p, f, b, g, a, x, e):
        rubi.append(2258)
        return Dist(a, Int((g*cos(e + f*x))**p, x), x) - Simp(b*(g*cos(e + f*x))**(p + S(1))/(f*g*(p + S(1))), x)
    rule2258 = ReplacementRule(pattern2258, replacement2258)
    pattern2259 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1276)
    def replacement2259(p, f, b, g, a, x, e):
        rubi.append(2259)
        return Dist(a, Int((g*sin(e + f*x))**p, x), x) + Simp(b*(g*sin(e + f*x))**(p + S(1))/(f*g*(p + S(1))), x)
    rule2259 = ReplacementRule(pattern2259, replacement2259)
    pattern2260 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons17, cons13, cons137, cons1277)
    def replacement2260(p, m, f, b, g, a, x, e):
        rubi.append(2260)
        return Dist((a/g)**(S(2)*m), Int((g*cos(e + f*x))**(S(2)*m + p)*(a - b*sin(e + f*x))**(-m), x), x)
    rule2260 = ReplacementRule(pattern2260, replacement2260)
    pattern2261 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons17, cons13, cons137, cons1277)
    def replacement2261(p, m, f, b, g, a, x, e):
        rubi.append(2261)
        return Dist((a/g)**(S(2)*m), Int((g*sin(e + f*x))**(S(2)*m + p)*(a - b*cos(e + f*x))**(-m), x), x)
    rule2261 = ReplacementRule(pattern2261, replacement2261)
    pattern2262 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1278, cons1279)
    def replacement2262(p, m, f, b, g, a, x, e):
        rubi.append(2262)
        return Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(a*f*g*m), x)
    rule2262 = ReplacementRule(pattern2262, replacement2262)
    pattern2263 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1278, cons1279)
    def replacement2263(p, m, f, b, g, a, x, e):
        rubi.append(2263)
        return -Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(a*f*g*m), x)
    rule2263 = ReplacementRule(pattern2263, replacement2263)
    pattern2264 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1280, cons1281, cons143)
    def replacement2264(p, m, f, b, g, a, x, e):
        rubi.append(2264)
        return Dist((m + p + S(1))/(a*(S(2)*m + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(1)), x), x) + Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2264 = ReplacementRule(pattern2264, replacement2264)
    pattern2265 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1280, cons1281, cons143)
    def replacement2265(p, m, f, b, g, a, x, e):
        rubi.append(2265)
        return Dist((m + p + S(1))/(a*(S(2)*m + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(1)), x), x) - Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2265 = ReplacementRule(pattern2265, replacement2265)
    pattern2266 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1282, cons1283)
    def replacement2266(p, m, f, b, g, a, x, e):
        rubi.append(2266)
        return Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))/(f*g*(m + S(-1))), x)
    rule2266 = ReplacementRule(pattern2266, replacement2266)
    pattern2267 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1282, cons1283)
    def replacement2267(p, m, f, b, g, a, x, e):
        rubi.append(2267)
        return -Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))/(f*g*(m + S(-1))), x)
    rule2267 = ReplacementRule(pattern2267, replacement2267)
    pattern2268 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1284, cons1285)
    def replacement2268(p, m, f, b, g, a, x, e):
        rubi.append(2268)
        return Dist(a*(S(2)*m + p + S(-1))/(m + p), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(-1)), x), x) - Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))/(f*g*(m + p)), x)
    rule2268 = ReplacementRule(pattern2268, replacement2268)
    pattern2269 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1284, cons1285)
    def replacement2269(p, m, f, b, g, a, x, e):
        rubi.append(2269)
        return Dist(a*(S(2)*m + p + S(-1))/(m + p), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(-1)), x), x) + Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))/(f*g*(m + p)), x)
    rule2269 = ReplacementRule(pattern2269, replacement2269)
    pattern2270 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons244, cons168, cons1286, cons1287)
    def replacement2270(p, m, f, b, g, a, x, e):
        rubi.append(2270)
        return Dist(a*(m + p + S(1))/(g**S(2)*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**(m + S(-1)), x), x) - Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(a*f*g*(p + S(1))), x)
    rule2270 = ReplacementRule(pattern2270, replacement2270)
    pattern2271 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons244, cons168, cons1286, cons1287)
    def replacement2271(p, m, f, b, g, a, x, e):
        rubi.append(2271)
        return Dist(a*(m + p + S(1))/(g**S(2)*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**(m + S(-1)), x), x) + Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(a*f*g*(p + S(1))), x)
    rule2271 = ReplacementRule(pattern2271, replacement2271)
    pattern2272 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons244, cons166, cons137, cons1288)
    def replacement2272(p, m, f, b, g, a, x, e):
        rubi.append(2272)
        return Dist(b**S(2)*(S(2)*m + p + S(-1))/(g**S(2)*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**(m + S(-2)), x), x) + Simp(-S(2)*b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))/(f*g*(p + S(1))), x)
    rule2272 = ReplacementRule(pattern2272, replacement2272)
    pattern2273 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons244, cons166, cons137, cons1288)
    def replacement2273(p, m, f, b, g, a, x, e):
        rubi.append(2273)
        return Dist(b**S(2)*(S(2)*m + p + S(-1))/(g**S(2)*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**(m + S(-2)), x), x) + Simp(S(2)*b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))/(f*g*(p + S(1))), x)
    rule2273 = ReplacementRule(pattern2273, replacement2273)
    pattern2274 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265)
    def replacement2274(f, b, g, a, x, e):
        rubi.append(2274)
        return Dist(a*sqrt(a + b*sin(e + f*x))*sqrt(cos(e + f*x) + S(1))/(a*cos(e + f*x) + a + b*sin(e + f*x)), Int(sqrt(cos(e + f*x) + S(1))/sqrt(g*cos(e + f*x)), x), x) + Dist(b*sqrt(a + b*sin(e + f*x))*sqrt(cos(e + f*x) + S(1))/(a*cos(e + f*x) + a + b*sin(e + f*x)), Int(sin(e + f*x)/(sqrt(g*cos(e + f*x))*sqrt(cos(e + f*x) + S(1))), x), x)
    rule2274 = ReplacementRule(pattern2274, replacement2274)
    pattern2275 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265)
    def replacement2275(f, b, g, a, x, e):
        rubi.append(2275)
        return Dist(a*sqrt(a + b*cos(e + f*x))*sqrt(sin(e + f*x) + S(1))/(a*sin(e + f*x) + a + b*cos(e + f*x)), Int(sqrt(sin(e + f*x) + S(1))/sqrt(g*sin(e + f*x)), x), x) + Dist(b*sqrt(a + b*cos(e + f*x))*sqrt(sin(e + f*x) + S(1))/(a*sin(e + f*x) + a + b*cos(e + f*x)), Int(cos(e + f*x)/(sqrt(g*sin(e + f*x))*sqrt(sin(e + f*x) + S(1))), x), x)
    rule2275 = ReplacementRule(pattern2275, replacement2275)
    pattern2276 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons31, cons168, cons1285, cons1288)
    def replacement2276(p, m, f, b, g, a, x, e):
        rubi.append(2276)
        return Dist(a*(S(2)*m + p + S(-1))/(m + p), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(-1)), x), x) - Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))/(f*g*(m + p)), x)
    rule2276 = ReplacementRule(pattern2276, replacement2276)
    pattern2277 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons31, cons168, cons1285, cons1288)
    def replacement2277(p, m, f, b, g, a, x, e):
        rubi.append(2277)
        return Dist(a*(S(2)*m + p + S(-1))/(m + p), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(-1)), x), x) + Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))/(f*g*(m + p)), x)
    rule2277 = ReplacementRule(pattern2277, replacement2277)
    pattern2278 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons244, cons94, cons146, cons1289, cons1285, cons1288)
    def replacement2278(p, m, f, b, g, a, x, e):
        rubi.append(2278)
        return Dist(g**S(2)*(p + S(-1))/(a*(m + p)), Int((g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**(m + S(1)), x), x) + Simp(g*(g*cos(e + f*x))**(p + S(-1))*(a + b*sin(e + f*x))**(m + S(1))/(b*f*(m + p)), x)
    rule2278 = ReplacementRule(pattern2278, replacement2278)
    pattern2279 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons244, cons94, cons146, cons1289, cons1285, cons1288)
    def replacement2279(p, m, f, b, g, a, x, e):
        rubi.append(2279)
        return Dist(g**S(2)*(p + S(-1))/(a*(m + p)), Int((g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**(m + S(1)), x), x) - Simp(g*(g*sin(e + f*x))**(p + S(-1))*(a + b*cos(e + f*x))**(m + S(1))/(b*f*(m + p)), x)
    rule2279 = ReplacementRule(pattern2279, replacement2279)
    pattern2280 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons244, cons1290, cons146, cons1281, cons1291, cons1288)
    def replacement2280(p, m, f, b, g, a, x, e):
        rubi.append(2280)
        return Dist(g**S(2)*(p + S(-1))/(b**S(2)*(S(2)*m + p + S(1))), Int((g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**(m + S(2)), x), x) + Simp(S(2)*g*(g*cos(e + f*x))**(p + S(-1))*(a + b*sin(e + f*x))**(m + S(1))/(b*f*(S(2)*m + p + S(1))), x)
    rule2280 = ReplacementRule(pattern2280, replacement2280)
    pattern2281 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons244, cons1290, cons146, cons1281, cons1291, cons1288)
    def replacement2281(p, m, f, b, g, a, x, e):
        rubi.append(2281)
        return Dist(g**S(2)*(p + S(-1))/(b**S(2)*(S(2)*m + p + S(1))), Int((g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**(m + S(2)), x), x) + Simp(-S(2)*g*(g*sin(e + f*x))**(p + S(-1))*(a + b*cos(e + f*x))**(m + S(1))/(b*f*(S(2)*m + p + S(1))), x)
    rule2281 = ReplacementRule(pattern2281, replacement2281)
    pattern2282 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons31, cons94, cons1281, cons1288)
    def replacement2282(p, m, f, b, g, a, x, e):
        rubi.append(2282)
        return Dist((m + p + S(1))/(a*(S(2)*m + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(1)), x), x) + Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2282 = ReplacementRule(pattern2282, replacement2282)
    pattern2283 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons31, cons94, cons1281, cons1288)
    def replacement2283(p, m, f, b, g, a, x, e):
        rubi.append(2283)
        return Dist((m + p + S(1))/(a*(S(2)*m + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(1)), x), x) - Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2283 = ReplacementRule(pattern2283, replacement2283)
    pattern2284 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons13, cons146, cons246)
    def replacement2284(p, f, b, g, a, x, e):
        rubi.append(2284)
        return Dist(g**S(2)/a, Int((g*cos(e + f*x))**(p + S(-2)), x), x) + Simp(g*(g*cos(e + f*x))**(p + S(-1))/(b*f*(p + S(-1))), x)
    rule2284 = ReplacementRule(pattern2284, replacement2284)
    pattern2285 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons13, cons146, cons246)
    def replacement2285(p, f, b, g, a, x, e):
        rubi.append(2285)
        return Dist(g**S(2)/a, Int((g*sin(e + f*x))**(p + S(-2)), x), x) - Simp(g*(g*sin(e + f*x))**(p + S(-1))/(b*f*(p + S(-1))), x)
    rule2285 = ReplacementRule(pattern2285, replacement2285)
    pattern2286 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons1292, cons246)
    def replacement2286(p, f, b, g, a, x, e):
        rubi.append(2286)
        return Dist(p/(a*(p + S(-1))), Int((g*cos(e + f*x))**p, x), x) + Simp(b*(g*cos(e + f*x))**(p + S(1))/(a*f*g*(a + b*sin(e + f*x))*(p + S(-1))), x)
    rule2286 = ReplacementRule(pattern2286, replacement2286)
    pattern2287 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons1292, cons246)
    def replacement2287(p, f, b, g, a, x, e):
        rubi.append(2287)
        return Dist(p/(a*(p + S(-1))), Int((g*sin(e + f*x))**p, x), x) - Simp(b*(g*sin(e + f*x))**(p + S(1))/(a*f*g*(a + b*cos(e + f*x))*(p + S(-1))), x)
    rule2287 = ReplacementRule(pattern2287, replacement2287)
    pattern2288 = Pattern(Integral(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265)
    def replacement2288(f, b, g, a, x, e):
        rubi.append(2288)
        return -Dist(g*sqrt(a + b*sin(e + f*x))*sqrt(cos(e + f*x) + S(1))/(a*sin(e + f*x) + b*cos(e + f*x) + b), Int(sin(e + f*x)/(sqrt(g*cos(e + f*x))*sqrt(cos(e + f*x) + S(1))), x), x) + Dist(g*sqrt(a + b*sin(e + f*x))*sqrt(cos(e + f*x) + S(1))/(a*cos(e + f*x) + a + b*sin(e + f*x)), Int(sqrt(cos(e + f*x) + S(1))/sqrt(g*cos(e + f*x)), x), x)
    rule2288 = ReplacementRule(pattern2288, replacement2288)
    pattern2289 = Pattern(Integral(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265)
    def replacement2289(f, b, g, a, x, e):
        rubi.append(2289)
        return Dist(g*sqrt(a + b*cos(e + f*x))*sqrt(sin(e + f*x) + S(1))/(a*sin(e + f*x) + a + b*cos(e + f*x)), Int(sqrt(sin(e + f*x) + S(1))/sqrt(g*sin(e + f*x)), x), x) - Dist(g*sqrt(a + b*cos(e + f*x))*sqrt(sin(e + f*x) + S(1))/(a*cos(e + f*x) + b*sin(e + f*x) + b), Int(cos(e + f*x)/(sqrt(g*sin(e + f*x))*sqrt(sin(e + f*x) + S(1))), x), x)
    rule2289 = ReplacementRule(pattern2289, replacement2289)
    pattern2290 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265)
    def replacement2290(f, b, g, a, x, e):
        rubi.append(2290)
        return Dist(g**S(2)/(S(2)*a), Int(sqrt(a + b*sin(e + f*x))/sqrt(g*cos(e + f*x)), x), x) + Simp(g*sqrt(g*cos(e + f*x))*sqrt(a + b*sin(e + f*x))/(b*f), x)
    rule2290 = ReplacementRule(pattern2290, replacement2290)
    pattern2291 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265)
    def replacement2291(f, b, g, a, x, e):
        rubi.append(2291)
        return Dist(g**S(2)/(S(2)*a), Int(sqrt(a + b*cos(e + f*x))/sqrt(g*sin(e + f*x)), x), x) - Simp(g*sqrt(g*sin(e + f*x))*sqrt(a + b*cos(e + f*x))/(b*f), x)
    rule2291 = ReplacementRule(pattern2291, replacement2291)
    pattern2292 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons13, cons1293, cons246)
    def replacement2292(p, f, b, g, a, x, e):
        rubi.append(2292)
        return Dist(S(2)*a*(p + S(-2))/(S(2)*p + S(-1)), Int((g*cos(e + f*x))**p/(a + b*sin(e + f*x))**(S(3)/2), x), x) + Simp(-S(2)*b*(g*cos(e + f*x))**(p + S(1))/(f*g*(a + b*sin(e + f*x))**(S(3)/2)*(S(2)*p + S(-1))), x)
    rule2292 = ReplacementRule(pattern2292, replacement2292)
    pattern2293 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons13, cons1293, cons246)
    def replacement2293(p, f, b, g, a, x, e):
        rubi.append(2293)
        return Dist(S(2)*a*(p + S(-2))/(S(2)*p + S(-1)), Int((g*sin(e + f*x))**p/(a + b*cos(e + f*x))**(S(3)/2), x), x) + Simp(S(2)*b*(g*sin(e + f*x))**(p + S(1))/(f*g*(a + b*cos(e + f*x))**(S(3)/2)*(S(2)*p + S(-1))), x)
    rule2293 = ReplacementRule(pattern2293, replacement2293)
    pattern2294 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons13, cons137, cons246)
    def replacement2294(p, f, b, g, a, x, e):
        rubi.append(2294)
        return Dist(a*(S(2)*p + S(1))/(S(2)*g**S(2)*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))/(a + b*sin(e + f*x))**(S(3)/2), x), x) - Simp(b*(g*cos(e + f*x))**(p + S(1))/(a*f*g*sqrt(a + b*sin(e + f*x))*(p + S(1))), x)
    rule2294 = ReplacementRule(pattern2294, replacement2294)
    pattern2295 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1265, cons13, cons137, cons246)
    def replacement2295(p, f, b, g, a, x, e):
        rubi.append(2295)
        return Dist(a*(S(2)*p + S(1))/(S(2)*g**S(2)*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))/(a + b*cos(e + f*x))**(S(3)/2), x), x) + Simp(b*(g*sin(e + f*x))**(p + S(1))/(a*f*g*sqrt(a + b*cos(e + f*x))*(p + S(1))), x)
    rule2295 = ReplacementRule(pattern2295, replacement2295)
    pattern2296 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons17)
    def replacement2296(p, m, f, b, g, a, x, e):
        rubi.append(2296)
        return Dist(a**m*(g*cos(e + f*x))**(p + S(1))*(-sin(e + f*x) + S(1))**(-p/S(2) + S(-1)/2)*(sin(e + f*x) + S(1))**(-p/S(2) + S(-1)/2)/(f*g), Subst(Int((S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2), x), x, sin(e + f*x)), x)
    rule2296 = ReplacementRule(pattern2296, replacement2296)
    pattern2297 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons17)
    def replacement2297(p, m, f, b, g, a, x, e):
        rubi.append(2297)
        return -Dist(a**m*(g*sin(e + f*x))**(p + S(1))*(-cos(e + f*x) + S(1))**(-p/S(2) + S(-1)/2)*(cos(e + f*x) + S(1))**(-p/S(2) + S(-1)/2)/(f*g), Subst(Int((S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2), x), x, cos(e + f*x)), x)
    rule2297 = ReplacementRule(pattern2297, replacement2297)
    pattern2298 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons18)
    def replacement2298(p, m, f, b, g, a, x, e):
        rubi.append(2298)
        return Dist(a**S(2)*(g*cos(e + f*x))**(p + S(1))*(a - b*sin(e + f*x))**(-p/S(2) + S(-1)/2)*(a + b*sin(e + f*x))**(-p/S(2) + S(-1)/2)/(f*g), Subst(Int((a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2), x), x, sin(e + f*x)), x)
    rule2298 = ReplacementRule(pattern2298, replacement2298)
    pattern2299 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons18)
    def replacement2299(p, m, f, b, g, a, x, e):
        rubi.append(2299)
        return -Dist(a**S(2)*(g*sin(e + f*x))**(p + S(1))*(a - b*cos(e + f*x))**(-p/S(2) + S(-1)/2)*(a + b*cos(e + f*x))**(-p/S(2) + S(-1)/2)/(f*g), Subst(Int((a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2), x), x, cos(e + f*x)), x)
    rule2299 = ReplacementRule(pattern2299, replacement2299)
    pattern2300 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons244, cons1256, cons137, cons1294)
    def replacement2300(p, m, f, b, g, a, x, e):
        rubi.append(2300)
        return Dist(S(1)/(g**S(2)*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**(m + S(-1))*(a*(p + S(2)) + b*(m + p + S(2))*sin(e + f*x)), x), x) - Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m*sin(e + f*x)/(f*g*(p + S(1))), x)
    rule2300 = ReplacementRule(pattern2300, replacement2300)
    pattern2301 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons244, cons1256, cons137, cons1294)
    def replacement2301(p, m, f, b, g, a, x, e):
        rubi.append(2301)
        return Dist(S(1)/(g**S(2)*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**(m + S(-1))*(a*(p + S(2)) + b*(m + p + S(2))*cos(e + f*x)), x), x) + Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m*cos(e + f*x)/(f*g*(p + S(1))), x)
    rule2301 = ReplacementRule(pattern2301, replacement2301)
    pattern2302 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons244, cons166, cons137, cons1294)
    def replacement2302(p, m, f, b, g, a, x, e):
        rubi.append(2302)
        return Dist(S(1)/(g**S(2)*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**(m + S(-2))*(a**S(2)*(p + S(2)) + a*b*(m + p + S(1))*sin(e + f*x) + b**S(2)*(m + S(-1))), x), x) - Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))*(a*sin(e + f*x) + b)/(f*g*(p + S(1))), x)
    rule2302 = ReplacementRule(pattern2302, replacement2302)
    pattern2303 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons244, cons166, cons137, cons1294)
    def replacement2303(p, m, f, b, g, a, x, e):
        rubi.append(2303)
        return Dist(S(1)/(g**S(2)*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**(m + S(-2))*(a**S(2)*(p + S(2)) + a*b*(m + p + S(1))*cos(e + f*x) + b**S(2)*(m + S(-1))), x), x) + Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))*(a*cos(e + f*x) + b)/(f*g*(p + S(1))), x)
    rule2303 = ReplacementRule(pattern2303, replacement2303)
    pattern2304 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons31, cons166, cons1285, cons1294)
    def replacement2304(p, m, f, b, g, a, x, e):
        rubi.append(2304)
        return Dist(S(1)/(m + p), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(-2))*(a**S(2)*(m + p) + a*b*(S(2)*m + p + S(-1))*sin(e + f*x) + b**S(2)*(m + S(-1))), x), x) - Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))/(f*g*(m + p)), x)
    rule2304 = ReplacementRule(pattern2304, replacement2304)
    pattern2305 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons31, cons166, cons1285, cons1294)
    def replacement2305(p, m, f, b, g, a, x, e):
        rubi.append(2305)
        return Dist(S(1)/(m + p), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(-2))*(a**S(2)*(m + p) + a*b*(S(2)*m + p + S(-1))*cos(e + f*x) + b**S(2)*(m + S(-1))), x), x) + Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))/(f*g*(m + p)), x)
    rule2305 = ReplacementRule(pattern2305, replacement2305)
    pattern2306 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons244, cons94, cons146, cons1288)
    def replacement2306(p, m, f, b, g, a, x, e):
        rubi.append(2306)
        return Dist(g**S(2)*(p + S(-1))/(b*(m + S(1))), Int((g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**(m + S(1))*sin(e + f*x), x), x) + Simp(g*(g*cos(e + f*x))**(p + S(-1))*(a + b*sin(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule2306 = ReplacementRule(pattern2306, replacement2306)
    pattern2307 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons244, cons94, cons146, cons1288)
    def replacement2307(p, m, f, b, g, a, x, e):
        rubi.append(2307)
        return Dist(g**S(2)*(p + S(-1))/(b*(m + S(1))), Int((g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**(m + S(1))*cos(e + f*x), x), x) - Simp(g*(g*sin(e + f*x))**(p + S(-1))*(a + b*cos(e + f*x))**(m + S(1))/(b*f*(m + S(1))), x)
    rule2307 = ReplacementRule(pattern2307, replacement2307)
    pattern2308 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons31, cons94, cons1288)
    def replacement2308(p, m, f, b, g, a, x, e):
        rubi.append(2308)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(1))*(a*(m + S(1)) - b*(m + p + S(2))*sin(e + f*x)), x), x) - Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(1))/(f*g*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2308 = ReplacementRule(pattern2308, replacement2308)
    pattern2309 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons31, cons94, cons1288)
    def replacement2309(p, m, f, b, g, a, x, e):
        rubi.append(2309)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(1))*(a*(m + S(1)) - b*(m + p + S(2))*cos(e + f*x)), x), x) + Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(1))/(f*g*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2309 = ReplacementRule(pattern2309, replacement2309)
    pattern2310 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons1267, cons13, cons146, cons1285, cons1288)
    def replacement2310(p, m, f, b, g, a, x, e):
        rubi.append(2310)
        return Dist(g**S(2)*(p + S(-1))/(b*(m + p)), Int((g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**m*(a*sin(e + f*x) + b), x), x) + Simp(g*(g*cos(e + f*x))**(p + S(-1))*(a + b*sin(e + f*x))**(m + S(1))/(b*f*(m + p)), x)
    rule2310 = ReplacementRule(pattern2310, replacement2310)
    pattern2311 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons1267, cons13, cons146, cons1285, cons1288)
    def replacement2311(p, m, f, b, g, a, x, e):
        rubi.append(2311)
        return Dist(g**S(2)*(p + S(-1))/(b*(m + p)), Int((g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**m*(a*cos(e + f*x) + b), x), x) - Simp(g*(g*sin(e + f*x))**(p + S(-1))*(a + b*cos(e + f*x))**(m + S(1))/(b*f*(m + p)), x)
    rule2311 = ReplacementRule(pattern2311, replacement2311)
    pattern2312 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons1267, cons13, cons137, cons1288)
    def replacement2312(p, m, f, b, g, a, x, e):
        rubi.append(2312)
        return Dist(S(1)/(g**S(2)*(a**S(2) - b**S(2))*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**m*(a**S(2)*(p + S(2)) + a*b*(m + p + S(3))*sin(e + f*x) - b**S(2)*(m + p + S(2))), x), x) + Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(1))*(-a*sin(e + f*x) + b)/(f*g*(a**S(2) - b**S(2))*(p + S(1))), x)
    rule2312 = ReplacementRule(pattern2312, replacement2312)
    pattern2313 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons1267, cons13, cons137, cons1288)
    def replacement2313(p, m, f, b, g, a, x, e):
        rubi.append(2313)
        return Dist(S(1)/(g**S(2)*(a**S(2) - b**S(2))*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**m*(a**S(2)*(p + S(2)) + a*b*(m + p + S(3))*cos(e + f*x) - b**S(2)*(m + p + S(2))), x), x) - Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(1))*(-a*cos(e + f*x) + b)/(f*g*(a**S(2) - b**S(2))*(p + S(1))), x)
    rule2313 = ReplacementRule(pattern2313, replacement2313)
    pattern2314 = Pattern(Integral(S(1)/(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    def replacement2314(f, b, g, a, x, e):
        rubi.append(2314)
        return Dist(S(2)*sqrt(S(2))*sqrt(g*cos(e + f*x))*sqrt((a + b*sin(e + f*x))/((a - b)*(-sin(e + f*x) + S(1))))/(f*g*sqrt((sin(e + f*x) + cos(e + f*x) + S(1))/(-sin(e + f*x) + cos(e + f*x) + S(1)))*sqrt(a + b*sin(e + f*x))), Subst(Int(S(1)/sqrt(x**S(4)*(a + b)/(a - b) + S(1)), x), x, sqrt((sin(e + f*x) + cos(e + f*x) + S(1))/(-sin(e + f*x) + cos(e + f*x) + S(1)))), x)
    rule2314 = ReplacementRule(pattern2314, replacement2314)
    pattern2315 = Pattern(Integral(S(1)/(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    def replacement2315(f, b, g, a, x, e):
        rubi.append(2315)
        return Dist(-S(2)*sqrt(S(2))*sqrt(g*sin(e + f*x))*sqrt((a + b*cos(e + f*x))/((a - b)*(-cos(e + f*x) + S(1))))/(f*g*sqrt((sin(e + f*x) + cos(e + f*x) + S(1))/(sin(e + f*x) - cos(e + f*x) + S(1)))*sqrt(a + b*cos(e + f*x))), Subst(Int(S(1)/sqrt(x**S(4)*(a + b)/(a - b) + S(1)), x), x, sqrt((sin(e + f*x) + cos(e + f*x) + S(1))/(sin(e + f*x) - cos(e + f*x) + S(1)))), x)
    rule2315 = ReplacementRule(pattern2315, replacement2315)
    pattern2316 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1267, cons1278)
    def replacement2316(p, m, f, b, g, a, x, e):
        rubi.append(2316)
        return Simp(g*(g*cos(e + f*x))**(p + S(-1))*(-(a - b)*(-sin(e + f*x) + S(1))/((a + b)*(sin(e + f*x) + S(1))))**(m/S(2))*(a + b*sin(e + f*x))**(m + S(1))*(-sin(e + f*x) + S(1))*Hypergeometric2F1(m + S(1), m/S(2) + S(1), m + S(2), S(2)*(a + b*sin(e + f*x))/((a + b)*(sin(e + f*x) + S(1))))/(f*(a + b)*(m + S(1))), x)
    rule2316 = ReplacementRule(pattern2316, replacement2316)
    pattern2317 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1267, cons1278)
    def replacement2317(p, m, f, b, g, a, x, e):
        rubi.append(2317)
        return -Simp(g*(g*sin(e + f*x))**(p + S(-1))*(-(a - b)*(-cos(e + f*x) + S(1))/((a + b)*(cos(e + f*x) + S(1))))**(m/S(2))*(a + b*cos(e + f*x))**(m + S(1))*(-cos(e + f*x) + S(1))*Hypergeometric2F1(m + S(1), m/S(2) + S(1), m + S(2), S(2)*(a + b*cos(e + f*x))/((a + b)*(cos(e + f*x) + S(1))))/(f*(a + b)*(m + S(1))), x)
    rule2317 = ReplacementRule(pattern2317, replacement2317)
    pattern2318 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1267, cons1295)
    def replacement2318(p, m, f, b, g, a, x, e):
        rubi.append(2318)
        return Dist(a/(g**S(2)*(a - b)), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**m/(-sin(e + f*x) + S(1)), x), x) + Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(1))/(f*g*(a - b)*(p + S(1))), x)
    rule2318 = ReplacementRule(pattern2318, replacement2318)
    pattern2319 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1267, cons1295)
    def replacement2319(p, m, f, b, g, a, x, e):
        rubi.append(2319)
        return Dist(a/(g**S(2)*(a - b)), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**m/(-cos(e + f*x) + S(1)), x), x) - Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(1))/(f*g*(a - b)*(p + S(1))), x)
    rule2319 = ReplacementRule(pattern2319, replacement2319)
    pattern2320 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1267, cons1296)
    def replacement2320(p, m, f, b, g, a, x, e):
        rubi.append(2320)
        return Dist(a/(g**S(2)*(a - b)), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**m/(-sin(e + f*x) + S(1)), x), x) - Dist(b*(m + p + S(2))/(g**S(2)*(a - b)*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**m, x), x) + Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(1))/(f*g*(a - b)*(p + S(1))), x)
    rule2320 = ReplacementRule(pattern2320, replacement2320)
    pattern2321 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1267, cons1296)
    def replacement2321(p, m, f, b, g, a, x, e):
        rubi.append(2321)
        return Dist(a/(g**S(2)*(a - b)), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**m/(-cos(e + f*x) + S(1)), x), x) - Dist(b*(m + p + S(2))/(g**S(2)*(a - b)*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**m, x), x) - Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(1))/(f*g*(a - b)*(p + S(1))), x)
    rule2321 = ReplacementRule(pattern2321, replacement2321)
    def With2322(f, b, g, a, x, e):
        q = Rt(-a**S(2) + b**S(2), S(2))
        rubi.append(2322)
        return -Dist(a*g/(S(2)*b), Int(S(1)/(sqrt(g*cos(e + f*x))*(-b*cos(e + f*x) + q)), x), x) + Dist(a*g/(S(2)*b), Int(S(1)/(sqrt(g*cos(e + f*x))*(b*cos(e + f*x) + q)), x), x) + Dist(b*g/f, Subst(Int(sqrt(x)/(b**S(2)*x**S(2) + g**S(2)*(a**S(2) - b**S(2))), x), x, g*cos(e + f*x)), x)
    pattern2322 = Pattern(Integral(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    rule2322 = ReplacementRule(pattern2322, With2322)
    def With2323(f, b, g, a, x, e):
        q = Rt(-a**S(2) + b**S(2), S(2))
        rubi.append(2323)
        return -Dist(a*g/(S(2)*b), Int(S(1)/(sqrt(g*sin(e + f*x))*(-b*sin(e + f*x) + q)), x), x) + Dist(a*g/(S(2)*b), Int(S(1)/(sqrt(g*sin(e + f*x))*(b*sin(e + f*x) + q)), x), x) - Dist(b*g/f, Subst(Int(sqrt(x)/(b**S(2)*x**S(2) + g**S(2)*(a**S(2) - b**S(2))), x), x, g*sin(e + f*x)), x)
    pattern2323 = Pattern(Integral(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    rule2323 = ReplacementRule(pattern2323, With2323)
    def With2324(f, b, g, a, x, e):
        q = Rt(-a**S(2) + b**S(2), S(2))
        rubi.append(2324)
        return -Dist(a/(S(2)*q), Int(S(1)/(sqrt(g*cos(e + f*x))*(-b*cos(e + f*x) + q)), x), x) - Dist(a/(S(2)*q), Int(S(1)/(sqrt(g*cos(e + f*x))*(b*cos(e + f*x) + q)), x), x) + Dist(b*g/f, Subst(Int(S(1)/(sqrt(x)*(b**S(2)*x**S(2) + g**S(2)*(a**S(2) - b**S(2)))), x), x, g*cos(e + f*x)), x)
    pattern2324 = Pattern(Integral(S(1)/(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    rule2324 = ReplacementRule(pattern2324, With2324)
    def With2325(f, b, g, a, x, e):
        q = Rt(-a**S(2) + b**S(2), S(2))
        rubi.append(2325)
        return -Dist(a/(S(2)*q), Int(S(1)/(sqrt(g*sin(e + f*x))*(-b*sin(e + f*x) + q)), x), x) - Dist(a/(S(2)*q), Int(S(1)/(sqrt(g*sin(e + f*x))*(b*sin(e + f*x) + q)), x), x) - Dist(b*g/f, Subst(Int(S(1)/(sqrt(x)*(b**S(2)*x**S(2) + g**S(2)*(a**S(2) - b**S(2)))), x), x, g*sin(e + f*x)), x)
    pattern2325 = Pattern(Integral(S(1)/(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    rule2325 = ReplacementRule(pattern2325, With2325)
    pattern2326 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons84, cons1297)
    def replacement2326(p, m, f, b, g, a, x, e):
        rubi.append(2326)
        return Simp(g*(g*cos(e + f*x))**(p + S(-1))*(b*(sin(e + f*x) + S(1))/(a + b*sin(e + f*x)))**(-p/S(2) + S(1)/2)*(-b*(-sin(e + f*x) + S(1))/(a + b*sin(e + f*x)))**(-p/S(2) + S(1)/2)*(a + b*sin(e + f*x))**(m + S(1))*AppellF1(-m - p, -p/S(2) + S(1)/2, -p/S(2) + S(1)/2, -m - p + S(1), (a + b)/(a + b*sin(e + f*x)), (a - b)/(a + b*sin(e + f*x)))/(b*f*(m + p)), x)
    rule2326 = ReplacementRule(pattern2326, replacement2326)
    pattern2327 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons84, cons1297)
    def replacement2327(p, m, f, b, g, a, x, e):
        rubi.append(2327)
        return -Simp(g*(g*sin(e + f*x))**(p + S(-1))*(b*(cos(e + f*x) + S(1))/(a + b*cos(e + f*x)))**(-p/S(2) + S(1)/2)*(-b*(-cos(e + f*x) + S(1))/(a + b*cos(e + f*x)))**(-p/S(2) + S(1)/2)*(a + b*cos(e + f*x))**(m + S(1))*AppellF1(-m - p, -p/S(2) + S(1)/2, -p/S(2) + S(1)/2, -m - p + S(1), (a + b)/(a + b*cos(e + f*x)), (a - b)/(a + b*cos(e + f*x)))/(b*f*(m + p)), x)
    rule2327 = ReplacementRule(pattern2327, replacement2327)
    pattern2328 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1267, cons143)
    def replacement2328(p, m, f, b, g, a, x, e):
        rubi.append(2328)
        return Dist(g*(g*cos(e + f*x))**(p + S(-1))*(S(1) - (a + b*sin(e + f*x))/(a - b))**(-p/S(2) + S(1)/2)*(S(1) - (a + b*sin(e + f*x))/(a + b))**(-p/S(2) + S(1)/2)/f, Subst(Int((a + b*x)**m*(-b*x/(a - b) - b/(a - b))**(p/S(2) + S(-1)/2)*(-b*x/(a + b) + b/(a + b))**(p/S(2) + S(-1)/2), x), x, sin(e + f*x)), x)
    rule2328 = ReplacementRule(pattern2328, replacement2328)
    pattern2329 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1267, cons143)
    def replacement2329(p, m, f, b, g, a, x, e):
        rubi.append(2329)
        return -Dist(g*(g*sin(e + f*x))**(p + S(-1))*(S(1) - (a + b*cos(e + f*x))/(a - b))**(-p/S(2) + S(1)/2)*(S(1) - (a + b*cos(e + f*x))/(a + b))**(-p/S(2) + S(1)/2)/f, Subst(Int((a + b*x)**m*(-b*x/(a - b) - b/(a - b))**(p/S(2) + S(-1)/2)*(-b*x/(a + b) + b/(a + b))**(p/S(2) + S(-1)/2), x), x, cos(e + f*x)), x)
    rule2329 = ReplacementRule(pattern2329, replacement2329)
    pattern2330 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons147)
    def replacement2330(p, m, f, g, b, a, x, e):
        rubi.append(2330)
        return Dist(g**(S(2)*IntPart(p))*(g/cos(e + f*x))**FracPart(p)*(g*cos(e + f*x))**FracPart(p), Int((g*cos(e + f*x))**(-p)*(a + b*sin(e + f*x))**m, x), x)
    rule2330 = ReplacementRule(pattern2330, replacement2330)
    pattern2331 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons147)
    def replacement2331(p, m, f, b, g, a, x, e):
        rubi.append(2331)
        return Dist(g**(S(2)*IntPart(p))*(g/sin(e + f*x))**FracPart(p)*(g*sin(e + f*x))**FracPart(p), Int((g*sin(e + f*x))**(-p)*(a + b*cos(e + f*x))**m, x), x)
    rule2331 = ReplacementRule(pattern2331, replacement2331)
    pattern2332 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons54)
    def replacement2332(p, f, b, g, a, x, e):
        rubi.append(2332)
        return Dist(S(1)/a, Int((g*tan(e + f*x))**p/cos(e + f*x)**S(2), x), x) - Dist(S(1)/(b*g), Int((g*tan(e + f*x))**(p + S(1))/cos(e + f*x), x), x)
    rule2332 = ReplacementRule(pattern2332, replacement2332)
    pattern2333 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons54)
    def replacement2333(p, f, b, g, a, x, e):
        rubi.append(2333)
        return Dist(S(1)/a, Int((g/tan(e + f*x))**p/sin(e + f*x)**S(2), x), x) - Dist(S(1)/(b*g), Int((g/tan(e + f*x))**(p + S(1))/sin(e + f*x), x), x)
    rule2333 = ReplacementRule(pattern2333, replacement2333)
    pattern2334 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1298)
    def replacement2334(p, m, f, b, a, x, e):
        rubi.append(2334)
        return Dist(S(1)/f, Subst(Int(x**p*(a - x)**(-p/S(2) + S(-1)/2)*(a + x)**(m - p/S(2) + S(-1)/2), x), x, b*sin(e + f*x)), x)
    rule2334 = ReplacementRule(pattern2334, replacement2334)
    pattern2335 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1298)
    def replacement2335(p, m, f, b, a, x, e):
        rubi.append(2335)
        return -Dist(S(1)/f, Subst(Int(x**p*(a - x)**(-p/S(2) + S(-1)/2)*(a + x)**(m - p/S(2) + S(-1)/2), x), x, b*cos(e + f*x)), x)
    rule2335 = ReplacementRule(pattern2335, replacement2335)
    pattern2336 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons48, cons125, cons1265, cons1299, cons1300)
    def replacement2336(p, m, f, b, a, x, e):
        rubi.append(2336)
        return Dist(a**p, Int((a - b*sin(e + f*x))**(-m)*sin(e + f*x)**p, x), x)
    rule2336 = ReplacementRule(pattern2336, replacement2336)
    pattern2337 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_, x_), cons2, cons3, cons48, cons125, cons1265, cons1299, cons1300)
    def replacement2337(p, m, f, b, a, x, e):
        rubi.append(2337)
        return Dist(a**p, Int((a - b*cos(e + f*x))**(-m)*cos(e + f*x)**p, x), x)
    rule2337 = ReplacementRule(pattern2337, replacement2337)
    pattern2338 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons48, cons125, cons1265, cons1301, cons1302)
    def replacement2338(p, m, f, b, a, x, e):
        rubi.append(2338)
        return Dist(a**p, Int(ExpandIntegrand((a - b*sin(e + f*x))**(-p/S(2))*(a + b*sin(e + f*x))**(m - p/S(2))*sin(e + f*x)**p, x), x), x)
    rule2338 = ReplacementRule(pattern2338, replacement2338)
    pattern2339 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_, x_), cons2, cons3, cons48, cons125, cons1265, cons1301, cons1302)
    def replacement2339(p, m, f, b, a, x, e):
        rubi.append(2339)
        return Dist(a**p, Int(ExpandIntegrand((a - b*cos(e + f*x))**(-p/S(2))*(a + b*cos(e + f*x))**(m - p/S(2))*cos(e + f*x)**p, x), x), x)
    rule2339 = ReplacementRule(pattern2339, replacement2339)
    pattern2340 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons62)
    def replacement2340(p, m, f, b, g, a, x, e):
        rubi.append(2340)
        return Int(ExpandIntegrand((g*tan(e + f*x))**p, (a + b*sin(e + f*x))**m, x), x)
    rule2340 = ReplacementRule(pattern2340, replacement2340)
    pattern2341 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons62)
    def replacement2341(p, m, f, b, g, a, x, e):
        rubi.append(2341)
        return Int(ExpandIntegrand((g/tan(e + f*x))**p, (a + b*cos(e + f*x))**m, x), x)
    rule2341 = ReplacementRule(pattern2341, replacement2341)
    pattern2342 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons84)
    def replacement2342(p, m, f, b, g, a, x, e):
        rubi.append(2342)
        return Dist(a**(S(2)*m), Int(ExpandIntegrand((g*tan(e + f*x))**p*(S(1)/cos(e + f*x))**(-m), (a/cos(e + f*x) - b*tan(e + f*x))**(-m), x), x), x)
    rule2342 = ReplacementRule(pattern2342, replacement2342)
    pattern2343 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons84)
    def replacement2343(p, m, f, b, g, a, x, e):
        rubi.append(2343)
        return Dist(a**(S(2)*m), Int(ExpandIntegrand((g/tan(e + f*x))**p*(S(1)/sin(e + f*x))**(-m), (a/sin(e + f*x) - b/tan(e + f*x))**(-m), x), x), x)
    rule2343 = ReplacementRule(pattern2343, replacement2343)
    pattern2344 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1265, cons18, cons31, cons267)
    def replacement2344(m, f, b, a, x, e):
        rubi.append(2344)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + S(-1))), Int((a + b*sin(e + f*x))**(m + S(1))*(a*m - b*(S(2)*m + S(-1))*sin(e + f*x))/cos(e + f*x)**S(2), x), x) + Simp(b*(a + b*sin(e + f*x))**m/(a*f*(S(2)*m + S(-1))*cos(e + f*x)), x)
    rule2344 = ReplacementRule(pattern2344, replacement2344)
    pattern2345 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1265, cons18, cons31, cons267)
    def replacement2345(m, f, b, a, x, e):
        rubi.append(2345)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + S(-1))), Int((a + b*cos(e + f*x))**(m + S(1))*(a*m - b*(S(2)*m + S(-1))*cos(e + f*x))/sin(e + f*x)**S(2), x), x) - Simp(b*(a + b*cos(e + f*x))**m/(a*f*(S(2)*m + S(-1))*sin(e + f*x)), x)
    rule2345 = ReplacementRule(pattern2345, replacement2345)
    pattern2346 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons18, cons1303)
    def replacement2346(m, f, b, a, x, e):
        rubi.append(2346)
        return Dist(S(1)/(b*m), Int((a + b*sin(e + f*x))**m*(a*sin(e + f*x) + b*(m + S(1)))/cos(e + f*x)**S(2), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))/(b*f*m*cos(e + f*x)), x)
    rule2346 = ReplacementRule(pattern2346, replacement2346)
    pattern2347 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons18, cons1303)
    def replacement2347(m, f, b, a, x, e):
        rubi.append(2347)
        return Dist(S(1)/(b*m), Int((a + b*cos(e + f*x))**m*(a*cos(e + f*x) + b*(m + S(1)))/sin(e + f*x)**S(2), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))/(b*f*m*sin(e + f*x)), x)
    rule2347 = ReplacementRule(pattern2347, replacement2347)
    pattern2348 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1304)
    def replacement2348(m, f, b, a, x, e):
        rubi.append(2348)
        return -Int((a + b*sin(e + f*x))**m*(-S(2)*sin(e + f*x)**S(2) + S(1))/cos(e + f*x)**S(4), x) + Int((a + b*sin(e + f*x))**m, x)
    rule2348 = ReplacementRule(pattern2348, replacement2348)
    pattern2349 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1304)
    def replacement2349(m, f, b, a, x, e):
        rubi.append(2349)
        return -Int((a + b*cos(e + f*x))**m*(-S(2)*cos(e + f*x)**S(2) + S(1))/sin(e + f*x)**S(4), x) + Int((a + b*cos(e + f*x))**m, x)
    rule2349 = ReplacementRule(pattern2349, replacement2349)
    pattern2350 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1265, cons1304, cons94)
    def replacement2350(m, f, b, a, x, e):
        rubi.append(2350)
        return Dist(b**(S(-2)), Int((a + b*sin(e + f*x))**(m + S(1))*(-a*(m + S(1))*sin(e + f*x) + b*m)/sin(e + f*x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))/(a*f*tan(e + f*x)), x)
    rule2350 = ReplacementRule(pattern2350, replacement2350)
    pattern2351 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1265, cons1304, cons94)
    def replacement2351(m, f, b, a, x, e):
        rubi.append(2351)
        return Dist(b**(S(-2)), Int((a + b*cos(e + f*x))**(m + S(1))*(-a*(m + S(1))*cos(e + f*x) + b*m)/cos(e + f*x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*tan(e + f*x)/(a*f), x)
    rule2351 = ReplacementRule(pattern2351, replacement2351)
    pattern2352 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1304, cons1305)
    def replacement2352(m, f, b, a, x, e):
        rubi.append(2352)
        return Dist(S(1)/a, Int((a + b*sin(e + f*x))**m*(-a*(m + S(1))*sin(e + f*x) + b*m)/sin(e + f*x), x), x) - Simp((a + b*sin(e + f*x))**m/(f*tan(e + f*x)), x)
    rule2352 = ReplacementRule(pattern2352, replacement2352)
    pattern2353 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1304, cons1305)
    def replacement2353(m, f, b, a, x, e):
        rubi.append(2353)
        return Dist(S(1)/a, Int((a + b*cos(e + f*x))**m*(-a*(m + S(1))*cos(e + f*x) + b*m)/cos(e + f*x), x), x) + Simp((a + b*cos(e + f*x))**m*tan(e + f*x)/f, x)
    rule2353 = ReplacementRule(pattern2353, replacement2353)
    pattern2354 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons1265, cons1304, cons94)
    def replacement2354(m, f, b, a, x, e):
        rubi.append(2354)
        return Dist(a**(S(-2)), Int((a + b*sin(e + f*x))**(m + S(2))*(sin(e + f*x)**S(2) + S(1))/sin(e + f*x)**S(4), x), x) + Dist(-S(2)/(a*b), Int((a + b*sin(e + f*x))**(m + S(2))/sin(e + f*x)**S(3), x), x)
    rule2354 = ReplacementRule(pattern2354, replacement2354)
    pattern2355 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons1265, cons1304, cons94)
    def replacement2355(m, f, b, a, x, e):
        rubi.append(2355)
        return Dist(a**(S(-2)), Int((a + b*cos(e + f*x))**(m + S(2))*(cos(e + f*x)**S(2) + S(1))/cos(e + f*x)**S(4), x), x) + Dist(-S(2)/(a*b), Int((a + b*cos(e + f*x))**(m + S(2))/cos(e + f*x)**S(3), x), x)
    rule2355 = ReplacementRule(pattern2355, replacement2355)
    pattern2356 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1304, cons1305)
    def replacement2356(m, f, b, a, x, e):
        rubi.append(2356)
        return Int((a + b*sin(e + f*x))**m*(-S(2)*sin(e + f*x)**S(2) + S(1))/sin(e + f*x)**S(4), x) + Int((a + b*sin(e + f*x))**m, x)
    rule2356 = ReplacementRule(pattern2356, replacement2356)
    pattern2357 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1304, cons1305)
    def replacement2357(m, f, b, a, x, e):
        rubi.append(2357)
        return Int((a + b*cos(e + f*x))**m*(-S(2)*cos(e + f*x)**S(2) + S(1))/cos(e + f*x)**S(4), x) + Int((a + b*cos(e + f*x))**m, x)
    rule2357 = ReplacementRule(pattern2357, replacement2357)
    pattern2358 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons18, cons1306)
    def replacement2358(p, m, f, b, a, x, e):
        rubi.append(2358)
        return Dist(sqrt(a - b*sin(e + f*x))*sqrt(a + b*sin(e + f*x))/(b*f*cos(e + f*x)), Subst(Int(x**p*(a - x)**(-p/S(2) + S(-1)/2)*(a + x)**(m - p/S(2) + S(-1)/2), x), x, b*sin(e + f*x)), x)
    rule2358 = ReplacementRule(pattern2358, replacement2358)
    pattern2359 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_, x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons18, cons1306)
    def replacement2359(p, m, f, b, a, x, e):
        rubi.append(2359)
        return -Dist(sqrt(a - b*cos(e + f*x))*sqrt(a + b*cos(e + f*x))/(b*f*sin(e + f*x)), Subst(Int(x**p*(a - x)**(-p/S(2) + S(-1)/2)*(a + x)**(m - p/S(2) + S(-1)/2), x), x, b*cos(e + f*x)), x)
    rule2359 = ReplacementRule(pattern2359, replacement2359)
    pattern2360 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons18, cons147)
    def replacement2360(p, m, f, b, g, a, x, e):
        rubi.append(2360)
        return Dist((b*sin(e + f*x))**(-p + S(-1))*(g*tan(e + f*x))**(p + S(1))*(a - b*sin(e + f*x))**(p/S(2) + S(1)/2)*(a + b*sin(e + f*x))**(p/S(2) + S(1)/2)/(f*g), Subst(Int(x**p*(a - x)**(-p/S(2) + S(-1)/2)*(a + x)**(m - p/S(2) + S(-1)/2), x), x, b*sin(e + f*x)), x)
    rule2360 = ReplacementRule(pattern2360, replacement2360)
    pattern2361 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons18, cons147)
    def replacement2361(p, m, f, b, g, a, x, e):
        rubi.append(2361)
        return -Dist((b*cos(e + f*x))**(-p + S(-1))*(g/tan(e + f*x))**(p + S(1))*(a - b*cos(e + f*x))**(p/S(2) + S(1)/2)*(a + b*cos(e + f*x))**(p/S(2) + S(1)/2)/(f*g), Subst(Int(x**p*(a - x)**(-p/S(2) + S(-1)/2)*(a + x)**(m - p/S(2) + S(-1)/2), x), x, b*cos(e + f*x)), x)
    rule2361 = ReplacementRule(pattern2361, replacement2361)
    pattern2362 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons1298)
    def replacement2362(p, m, f, b, a, x, e):
        rubi.append(2362)
        return Dist(S(1)/f, Subst(Int(x**p*(a + x)**m*(b**S(2) - x**S(2))**(-p/S(2) + S(-1)/2), x), x, b*sin(e + f*x)), x)
    rule2362 = ReplacementRule(pattern2362, replacement2362)
    pattern2363 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons1298)
    def replacement2363(p, m, f, b, a, x, e):
        rubi.append(2363)
        return -Dist(S(1)/f, Subst(Int(x**p*(a + x)**m*(b**S(2) - x**S(2))**(-p/S(2) + S(-1)/2), x), x, b*cos(e + f*x)), x)
    rule2363 = ReplacementRule(pattern2363, replacement2363)
    pattern2364 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons62)
    def replacement2364(p, m, f, b, g, a, x, e):
        rubi.append(2364)
        return Int(ExpandIntegrand((g*tan(e + f*x))**p, (a + b*sin(e + f*x))**m, x), x)
    rule2364 = ReplacementRule(pattern2364, replacement2364)
    pattern2365 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons62)
    def replacement2365(p, m, f, b, g, a, x, e):
        rubi.append(2365)
        return Int(ExpandIntegrand((g/tan(e + f*x))**p, (a + b*cos(e + f*x))**m, x), x)
    rule2365 = ReplacementRule(pattern2365, replacement2365)
    pattern2366 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1267)
    def replacement2366(m, f, b, a, x, e):
        rubi.append(2366)
        return Int((a + b*sin(e + f*x))**m*(-sin(e + f*x)**S(2) + S(1))/sin(e + f*x)**S(2), x)
    rule2366 = ReplacementRule(pattern2366, replacement2366)
    pattern2367 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1267)
    def replacement2367(m, f, b, a, x, e):
        rubi.append(2367)
        return Int((a + b*cos(e + f*x))**m*(-cos(e + f*x)**S(2) + S(1))/cos(e + f*x)**S(2), x)
    rule2367 = ReplacementRule(pattern2367, replacement2367)
    pattern2368 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons94, cons515)
    def replacement2368(m, f, b, a, x, e):
        rubi.append(2368)
        return -Dist(S(1)/(S(3)*a**S(2)*b*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(S(6)*a**S(2) + a*b*(m + S(1))*sin(e + f*x) - b**S(2)*(m + S(-2))*(m + S(-1)) - (S(3)*a**S(2) - b**S(2)*m*(m + S(-2)))*sin(e + f*x)**S(2), x)/sin(e + f*x)**S(3), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(S(3)*a*f*sin(e + f*x)**S(3)), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(S(3)*a**S(2) + b**S(2)*(m + S(-2)))*cos(e + f*x)/(S(3)*a**S(2)*b*f*(m + S(1))*sin(e + f*x)**S(2)), x)
    rule2368 = ReplacementRule(pattern2368, replacement2368)
    pattern2369 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons1267, cons31, cons94, cons515)
    def replacement2369(m, f, b, a, x, e):
        rubi.append(2369)
        return -Dist(S(1)/(S(3)*a**S(2)*b*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(S(6)*a**S(2) + a*b*(m + S(1))*cos(e + f*x) - b**S(2)*(m + S(-2))*(m + S(-1)) - (S(3)*a**S(2) - b**S(2)*m*(m + S(-2)))*cos(e + f*x)**S(2), x)/cos(e + f*x)**S(3), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(S(3)*a*f*cos(e + f*x)**S(3)), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(S(3)*a**S(2) + b**S(2)*(m + S(-2)))*sin(e + f*x)/(S(3)*a**S(2)*b*f*(m + S(1))*cos(e + f*x)**S(2)), x)
    rule2369 = ReplacementRule(pattern2369, replacement2369)
    pattern2370 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons272, cons515)
    def replacement2370(m, f, b, a, x, e):
        rubi.append(2370)
        return -Dist(S(1)/(S(6)*a**S(2)), Int((a + b*sin(e + f*x))**m*Simp(S(8)*a**S(2) + a*b*m*sin(e + f*x) - b**S(2)*(m + S(-2))*(m + S(-1)) - (S(6)*a**S(2) - b**S(2)*m*(m + S(-2)))*sin(e + f*x)**S(2), x)/sin(e + f*x)**S(2), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(S(3)*a*f*sin(e + f*x)**S(3)), x) - Simp(b*(a + b*sin(e + f*x))**(m + S(1))*(m + S(-2))*cos(e + f*x)/(S(6)*a**S(2)*f*sin(e + f*x)**S(2)), x)
    rule2370 = ReplacementRule(pattern2370, replacement2370)
    pattern2371 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons272, cons515)
    def replacement2371(m, f, b, a, x, e):
        rubi.append(2371)
        return -Dist(S(1)/(S(6)*a**S(2)), Int((a + b*cos(e + f*x))**m*Simp(S(8)*a**S(2) + a*b*m*cos(e + f*x) - b**S(2)*(m + S(-2))*(m + S(-1)) - (S(6)*a**S(2) - b**S(2)*m*(m + S(-2)))*cos(e + f*x)**S(2), x)/cos(e + f*x)**S(2), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(S(3)*a*f*cos(e + f*x)**S(3)), x) + Simp(b*(a + b*cos(e + f*x))**(m + S(1))*(m + S(-2))*sin(e + f*x)/(S(6)*a**S(2)*f*cos(e + f*x)**S(2)), x)
    rule2371 = ReplacementRule(pattern2371, replacement2371)
    pattern2372 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(6), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons1283, cons515)
    def replacement2372(m, f, b, a, x, e):
        rubi.append(2372)
        return Dist(S(1)/(S(20)*a**S(2)*b**S(2)*m*(m + S(-1))), Int((a + b*sin(e + f*x))**m*Simp(S(60)*a**S(4) - S(44)*a**S(2)*b**S(2)*m*(m + S(-1)) + a*b*m*(S(20)*a**S(2) - b**S(2)*m*(m + S(-1)))*sin(e + f*x) + b**S(4)*m*(m + S(-4))*(m + S(-3))*(m + S(-1)) - (S(40)*a**S(4) - S(20)*a**S(2)*b**S(2)*(m + S(-1))*(S(2)*m + S(1)) + b**S(4)*m*(m + S(-4))*(m + S(-2))*(m + S(-1)))*sin(e + f*x)**S(2), x)/sin(e + f*x)**S(4), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(S(5)*a*f*sin(e + f*x)**S(5)), x) + Simp((a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*m*sin(e + f*x)**S(2)), x) - Simp(b*(a + b*sin(e + f*x))**(m + S(1))*(m + S(-4))*cos(e + f*x)/(S(20)*a**S(2)*f*sin(e + f*x)**S(4)), x) + Simp(a*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b**S(2)*f*m*(m + S(-1))*sin(e + f*x)**S(3)), x)
    rule2372 = ReplacementRule(pattern2372, replacement2372)
    pattern2373 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**S(6), x_), cons2, cons3, cons48, cons125, cons21, cons1267, cons1283, cons515)
    def replacement2373(m, f, b, a, x, e):
        rubi.append(2373)
        return Dist(S(1)/(S(20)*a**S(2)*b**S(2)*m*(m + S(-1))), Int((a + b*cos(e + f*x))**m*Simp(S(60)*a**S(4) - S(44)*a**S(2)*b**S(2)*m*(m + S(-1)) + a*b*m*(S(20)*a**S(2) - b**S(2)*m*(m + S(-1)))*cos(e + f*x) + b**S(4)*m*(m + S(-4))*(m + S(-3))*(m + S(-1)) - (S(40)*a**S(4) - S(20)*a**S(2)*b**S(2)*(m + S(-1))*(S(2)*m + S(1)) + b**S(4)*m*(m + S(-4))*(m + S(-2))*(m + S(-1)))*cos(e + f*x)**S(2), x)/cos(e + f*x)**S(4), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(S(5)*a*f*cos(e + f*x)**S(5)), x) - Simp((a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*m*cos(e + f*x)**S(2)), x) + Simp(b*(a + b*cos(e + f*x))**(m + S(1))*(m + S(-4))*sin(e + f*x)/(S(20)*a**S(2)*f*cos(e + f*x)**S(4)), x) - Simp(a*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b**S(2)*f*m*(m + S(-1))*cos(e + f*x)**S(3)), x)
    rule2373 = ReplacementRule(pattern2373, replacement2373)
    pattern2374 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons1307, cons146)
    def replacement2374(p, f, b, g, a, x, e):
        rubi.append(2374)
        return Dist(a/(a**S(2) - b**S(2)), Int((g*tan(e + f*x))**p/sin(e + f*x)**S(2), x), x) - Dist(a**S(2)*g**S(2)/(a**S(2) - b**S(2)), Int((g*tan(e + f*x))**(p + S(-2))/(a + b*sin(e + f*x)), x), x) - Dist(b*g/(a**S(2) - b**S(2)), Int((g*tan(e + f*x))**(p + S(-1))/cos(e + f*x), x), x)
    rule2374 = ReplacementRule(pattern2374, replacement2374)
    pattern2375 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons1307, cons146)
    def replacement2375(p, f, b, g, a, x, e):
        rubi.append(2375)
        return Dist(a/(a**S(2) - b**S(2)), Int((g/tan(e + f*x))**p/cos(e + f*x)**S(2), x), x) - Dist(a**S(2)*g**S(2)/(a**S(2) - b**S(2)), Int((g/tan(e + f*x))**(p + S(-2))/(a + b*cos(e + f*x)), x), x) - Dist(b*g/(a**S(2) - b**S(2)), Int((g/tan(e + f*x))**(p + S(-1))/sin(e + f*x), x), x)
    rule2375 = ReplacementRule(pattern2375, replacement2375)
    pattern2376 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons1307, cons137)
    def replacement2376(p, f, b, g, a, x, e):
        rubi.append(2376)
        return Dist(S(1)/a, Int((g*tan(e + f*x))**p/cos(e + f*x)**S(2), x), x) - Dist(b/(a**S(2)*g), Int((g*tan(e + f*x))**(p + S(1))/cos(e + f*x), x), x) - Dist((a**S(2) - b**S(2))/(a**S(2)*g**S(2)), Int((g*tan(e + f*x))**(p + S(2))/(a + b*sin(e + f*x)), x), x)
    rule2376 = ReplacementRule(pattern2376, replacement2376)
    pattern2377 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons1307, cons137)
    def replacement2377(p, f, b, g, a, x, e):
        rubi.append(2377)
        return Dist(S(1)/a, Int((g/tan(e + f*x))**p/sin(e + f*x)**S(2), x), x) - Dist(b/(a**S(2)*g), Int((g/tan(e + f*x))**(p + S(1))/sin(e + f*x), x), x) - Dist((a**S(2) - b**S(2))/(a**S(2)*g**S(2)), Int((g/tan(e + f*x))**(p + S(2))/(a + b*cos(e + f*x)), x), x)
    rule2377 = ReplacementRule(pattern2377, replacement2377)
    pattern2378 = Pattern(Integral(sqrt(WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    def replacement2378(f, b, g, a, x, e):
        rubi.append(2378)
        return Dist(sqrt(g*tan(e + f*x))*sqrt(cos(e + f*x))/sqrt(sin(e + f*x)), Int(sqrt(sin(e + f*x))/((a + b*sin(e + f*x))*sqrt(cos(e + f*x))), x), x)
    rule2378 = ReplacementRule(pattern2378, replacement2378)
    pattern2379 = Pattern(Integral(sqrt(WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    def replacement2379(f, b, g, a, x, e):
        rubi.append(2379)
        return Dist(sqrt(g/tan(e + f*x))*sqrt(sin(e + f*x))/sqrt(cos(e + f*x)), Int(sqrt(cos(e + f*x))/((a + b*cos(e + f*x))*sqrt(sin(e + f*x))), x), x)
    rule2379 = ReplacementRule(pattern2379, replacement2379)
    pattern2380 = Pattern(Integral(S(1)/(sqrt(g_*tan(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    def replacement2380(f, b, g, a, x, e):
        rubi.append(2380)
        return Dist(sqrt(sin(e + f*x))/(sqrt(g*tan(e + f*x))*sqrt(cos(e + f*x))), Int(sqrt(cos(e + f*x))/((a + b*sin(e + f*x))*sqrt(sin(e + f*x))), x), x)
    rule2380 = ReplacementRule(pattern2380, replacement2380)
    pattern2381 = Pattern(Integral(S(1)/(sqrt(g_/tan(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    def replacement2381(f, b, g, a, x, e):
        rubi.append(2381)
        return Dist(sqrt(cos(e + f*x))/(sqrt(g/tan(e + f*x))*sqrt(sin(e + f*x))), Int(sqrt(sin(e + f*x))/((a + b*cos(e + f*x))*sqrt(cos(e + f*x))), x), x)
    rule2381 = ReplacementRule(pattern2381, replacement2381)
    pattern2382 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*tan(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons48, cons125, cons1267, cons1301)
    def replacement2382(p, m, f, b, a, x, e):
        rubi.append(2382)
        return Int(ExpandIntegrand((a + b*sin(e + f*x))**m*(-sin(e + f*x)**S(2) + S(1))**(-p/S(2))*sin(e + f*x)**p, x), x)
    rule2382 = ReplacementRule(pattern2382, replacement2382)
    pattern2383 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(S(1)/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_, x_), cons2, cons3, cons48, cons125, cons1267, cons1301)
    def replacement2383(p, m, f, b, a, x, e):
        rubi.append(2383)
        return Int(ExpandIntegrand((a + b*cos(e + f*x))**m*(-cos(e + f*x)**S(2) + S(1))**(-p/S(2))*cos(e + f*x)**p, x), x)
    rule2383 = ReplacementRule(pattern2383, replacement2383)
    pattern2384 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1308)
    def replacement2384(p, m, f, b, g, a, x, e):
        rubi.append(2384)
        return Int((g*tan(e + f*x))**p*(a + b*sin(e + f*x))**m, x)
    rule2384 = ReplacementRule(pattern2384, replacement2384)
    pattern2385 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1308)
    def replacement2385(p, m, f, b, g, a, x, e):
        rubi.append(2385)
        return Int((g/tan(e + f*x))**p*(a + b*cos(e + f*x))**m, x)
    rule2385 = ReplacementRule(pattern2385, replacement2385)
    pattern2386 = Pattern(Integral((WC('g', S(1))/tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons147)
    def replacement2386(p, m, f, b, g, a, x, e):
        rubi.append(2386)
        return Dist(g**(S(2)*IntPart(p))*(g/tan(e + f*x))**FracPart(p)*(g*tan(e + f*x))**FracPart(p), Int((g*tan(e + f*x))**(-p)*(a + b*sin(e + f*x))**m, x), x)
    rule2386 = ReplacementRule(pattern2386, replacement2386)
    pattern2387 = Pattern(Integral((WC('g', S(1))*tan(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons147)
    def replacement2387(p, m, f, b, g, a, x, e):
        rubi.append(2387)
        return Dist(g**(S(2)*IntPart(p))*(g/tan(e + f*x))**FracPart(p)*(g*tan(e + f*x))**FracPart(p), Int((g/tan(e + f*x))**(-p)*(a + b*cos(e + f*x))**m, x), x)
    rule2387 = ReplacementRule(pattern2387, replacement2387)
    pattern2388 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement2388(f, b, d, c, a, x, e):
        rubi.append(2388)
        return Simp(x*(S(2)*a*c + b*d)/S(2), x) - Simp((a*d + b*c)*cos(e + f*x)/f, x) - Simp(b*d*sin(e + f*x)*cos(e + f*x)/(S(2)*f), x)
    rule2388 = ReplacementRule(pattern2388, replacement2388)
    pattern2389 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement2389(f, b, d, c, a, x, e):
        rubi.append(2389)
        return Simp(x*(S(2)*a*c + b*d)/S(2), x) + Simp((a*d + b*c)*sin(e + f*x)/f, x) + Simp(b*d*sin(e + f*x)*cos(e + f*x)/(S(2)*f), x)
    rule2389 = ReplacementRule(pattern2389, replacement2389)
    pattern2390 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement2390(f, b, d, c, a, x, e):
        rubi.append(2390)
        return -Dist((-a*d + b*c)/d, Int(S(1)/(c + d*sin(e + f*x)), x), x) + Simp(b*x/d, x)
    rule2390 = ReplacementRule(pattern2390, replacement2390)
    pattern2391 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement2391(f, b, d, c, a, x, e):
        rubi.append(2391)
        return -Dist((-a*d + b*c)/d, Int(S(1)/(c + d*cos(e + f*x)), x), x) + Simp(b*x/d, x)
    rule2391 = ReplacementRule(pattern2391, replacement2391)
    pattern2392 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons17, cons1309)
    def replacement2392(m, f, b, d, a, n, c, x, e):
        rubi.append(2392)
        return Dist(a**m*c**m, Int((c + d*sin(e + f*x))**(-m + n)*cos(e + f*x)**(S(2)*m), x), x)
    rule2392 = ReplacementRule(pattern2392, replacement2392)
    pattern2393 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons17, cons1309)
    def replacement2393(m, f, b, d, a, n, c, x, e):
        rubi.append(2393)
        return Dist(a**m*c**m, Int((c + d*cos(e + f*x))**(-m + n)*sin(e + f*x)**(S(2)*m), x), x)
    rule2393 = ReplacementRule(pattern2393, replacement2393)
    pattern2394 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265)
    def replacement2394(f, b, d, a, c, x, e):
        rubi.append(2394)
        return Dist(a*c*cos(e + f*x)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), Int(cos(e + f*x)/(c + d*sin(e + f*x)), x), x)
    rule2394 = ReplacementRule(pattern2394, replacement2394)
    pattern2395 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265)
    def replacement2395(f, b, d, a, c, x, e):
        rubi.append(2395)
        return Dist(a*c*sin(e + f*x)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), Int(sin(e + f*x)/(c + d*cos(e + f*x)), x), x)
    rule2395 = ReplacementRule(pattern2395, replacement2395)
    pattern2396 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons1310)
    def replacement2396(f, b, d, a, c, n, x, e):
        rubi.append(2396)
        return Simp(-S(2)*b*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*sqrt(a + b*sin(e + f*x))*(S(2)*n + S(1))), x)
    rule2396 = ReplacementRule(pattern2396, replacement2396)
    pattern2397 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons1310)
    def replacement2397(f, b, d, a, c, n, x, e):
        rubi.append(2397)
        return Simp(S(2)*b*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*sqrt(a + b*cos(e + f*x))*(S(2)*n + S(1))), x)
    rule2397 = ReplacementRule(pattern2397, replacement2397)
    pattern2398 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons1311, cons87, cons89, cons1312)
    def replacement2398(m, f, b, d, a, c, n, x, e):
        rubi.append(2398)
        return -Dist(b*(S(2)*m + S(-1))/(d*(S(2)*n + S(1))), Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1)), x), x) + Simp(-S(2)*b*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*(S(2)*n + S(1))), x)
    rule2398 = ReplacementRule(pattern2398, replacement2398)
    pattern2399 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265, cons1311, cons87, cons89, cons1312)
    def replacement2399(m, f, b, d, a, c, n, x, e):
        rubi.append(2399)
        return -Dist(b*(S(2)*m + S(-1))/(d*(S(2)*n + S(1))), Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1)), x), x) + Simp(S(2)*b*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*(S(2)*n + S(1))), x)
    rule2399 = ReplacementRule(pattern2399, replacement2399)
    pattern2400 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons1311, cons346, cons1313, cons1312)
    def replacement2400(m, f, b, d, a, c, n, x, e):
        rubi.append(2400)
        return Dist(a*(S(2)*m + S(-1))/(m + n), Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n, x), x) - Simp(b*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*(m + n)), x)
    rule2400 = ReplacementRule(pattern2400, replacement2400)
    pattern2401 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons1311, cons346, cons1313, cons1312)
    def replacement2401(m, f, b, d, a, c, n, x, e):
        rubi.append(2401)
        return Dist(a*(S(2)*m + S(-1))/(m + n), Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n, x), x) + Simp(b*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*(m + n)), x)
    rule2401 = ReplacementRule(pattern2401, replacement2401)
    pattern2402 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265)
    def replacement2402(f, b, d, a, c, x, e):
        rubi.append(2402)
        return Dist(cos(e + f*x)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), Int(S(1)/cos(e + f*x), x), x)
    rule2402 = ReplacementRule(pattern2402, replacement2402)
    pattern2403 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons70, cons1265)
    def replacement2403(f, b, d, a, c, x, e):
        rubi.append(2403)
        return Dist(sin(e + f*x)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), Int(S(1)/sin(e + f*x), x), x)
    rule2403 = ReplacementRule(pattern2403, replacement2403)
    pattern2404 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons155, cons1314)
    def replacement2404(m, f, b, d, a, c, n, x, e):
        rubi.append(2404)
        return Simp(b*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2404 = ReplacementRule(pattern2404, replacement2404)
    pattern2405 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons155, cons1314)
    def replacement2405(m, f, b, d, a, c, n, x, e):
        rubi.append(2405)
        return -Simp(b*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2405 = ReplacementRule(pattern2405, replacement2405)
    pattern2406 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons1315, cons1314, cons114)
    def replacement2406(m, f, b, d, a, c, n, x, e):
        rubi.append(2406)
        return Dist((m + n + S(1))/(a*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n, x), x) + Simp(b*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2406 = ReplacementRule(pattern2406, replacement2406)
    pattern2407 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons1315, cons1314, cons114)
    def replacement2407(m, f, b, d, a, c, n, x, e):
        rubi.append(2407)
        return Dist((m + n + S(1))/(a*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n, x), x) - Simp(b*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2407 = ReplacementRule(pattern2407, replacement2407)
    pattern2408 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons31, cons94, cons1316, cons1170)
    def replacement2408(m, f, b, d, a, c, n, x, e):
        rubi.append(2408)
        return Dist((m + n + S(1))/(a*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n, x), x) + Simp(b*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2408 = ReplacementRule(pattern2408, replacement2408)
    pattern2409 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons70, cons1265, cons31, cons94, cons1316, cons1170)
    def replacement2409(m, f, b, d, a, c, n, x, e):
        rubi.append(2409)
        return Dist((m + n + S(1))/(a*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n, x), x) - Simp(b*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2409 = ReplacementRule(pattern2409, replacement2409)
    pattern2410 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons1317)
    def replacement2410(m, f, b, d, a, c, n, x, e):
        rubi.append(2410)
        return Dist(a**IntPart(m)*c**IntPart(m)*(a + b*sin(e + f*x))**FracPart(m)*(c + d*sin(e + f*x))**FracPart(m)*cos(e + f*x)**(-S(2)*FracPart(m)), Int((c + d*sin(e + f*x))**(-m + n)*cos(e + f*x)**(S(2)*m), x), x)
    rule2410 = ReplacementRule(pattern2410, replacement2410)
    pattern2411 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons70, cons1265, cons1317)
    def replacement2411(m, f, b, d, a, c, n, x, e):
        rubi.append(2411)
        return Dist(a**IntPart(m)*c**IntPart(m)*(a + b*cos(e + f*x))**FracPart(m)*(c + d*cos(e + f*x))**FracPart(m)*sin(e + f*x)**(-S(2)*FracPart(m)), Int((c + d*cos(e + f*x))**(-m + n)*sin(e + f*x)**(S(2)*m), x), x)
    rule2411 = ReplacementRule(pattern2411, replacement2411)
    pattern2412 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**S(2)/(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement2412(f, b, d, c, a, x, e):
        rubi.append(2412)
        return Dist(S(1)/d, Int(Simp(a**S(2)*d - b*(-S(2)*a*d + b*c)*sin(e + f*x), x)/(c + d*sin(e + f*x)), x), x) - Simp(b**S(2)*cos(e + f*x)/(d*f), x)
    rule2412 = ReplacementRule(pattern2412, replacement2412)
    pattern2413 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**S(2)/(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement2413(f, b, d, c, a, x, e):
        rubi.append(2413)
        return Dist(S(1)/d, Int(Simp(a**S(2)*d - b*(-S(2)*a*d + b*c)*cos(e + f*x), x)/(c + d*cos(e + f*x)), x), x) + Simp(b**S(2)*sin(e + f*x)/(d*f), x)
    rule2413 = ReplacementRule(pattern2413, replacement2413)
    pattern2414 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement2414(f, b, d, c, a, x, e):
        rubi.append(2414)
        return Dist(b/(-a*d + b*c), Int(S(1)/(a + b*sin(e + f*x)), x), x) - Dist(d/(-a*d + b*c), Int(S(1)/(c + d*sin(e + f*x)), x), x)
    rule2414 = ReplacementRule(pattern2414, replacement2414)
    pattern2415 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71)
    def replacement2415(f, b, d, c, a, x, e):
        rubi.append(2415)
        return Dist(b/(-a*d + b*c), Int(S(1)/(a + b*cos(e + f*x)), x), x) - Dist(d/(-a*d + b*c), Int(S(1)/(c + d*cos(e + f*x)), x), x)
    rule2415 = ReplacementRule(pattern2415, replacement2415)
    pattern2416 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons21, cons1318)
    def replacement2416(m, f, b, d, c, x, e):
        rubi.append(2416)
        return Dist(c, Int((b*sin(e + f*x))**m, x), x) + Dist(d/b, Int((b*sin(e + f*x))**(m + S(1)), x), x)
    rule2416 = ReplacementRule(pattern2416, replacement2416)
    pattern2417 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons21, cons1318)
    def replacement2417(m, f, b, d, c, x, e):
        rubi.append(2417)
        return Dist(c, Int((b*cos(e + f*x))**m, x), x) + Dist(d/b, Int((b*cos(e + f*x))**(m + S(1)), x), x)
    rule2417 = ReplacementRule(pattern2417, replacement2417)
    pattern2418 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1265, cons1319)
    def replacement2418(m, f, b, d, a, c, x, e):
        rubi.append(2418)
        return -Simp(d*(a + b*sin(e + f*x))**m*cos(e + f*x)/(f*(m + S(1))), x)
    rule2418 = ReplacementRule(pattern2418, replacement2418)
    pattern2419 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1265, cons1319)
    def replacement2419(m, f, b, d, a, c, x, e):
        rubi.append(2419)
        return Simp(d*(a + b*cos(e + f*x))**m*sin(e + f*x)/(f*(m + S(1))), x)
    rule2419 = ReplacementRule(pattern2419, replacement2419)
    pattern2420 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons31, cons1320)
    def replacement2420(m, f, b, d, c, a, x, e):
        rubi.append(2420)
        return Dist((a*d*m + b*c*(m + S(1)))/(a*b*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1)), x), x) + Simp((a + b*sin(e + f*x))**m*(-a*d + b*c)*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2420 = ReplacementRule(pattern2420, replacement2420)
    pattern2421 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons31, cons1320)
    def replacement2421(m, f, b, d, c, a, x, e):
        rubi.append(2421)
        return Dist((a*d*m + b*c*(m + S(1)))/(a*b*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1)), x), x) - Simp((a + b*cos(e + f*x))**m*(-a*d + b*c)*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2421 = ReplacementRule(pattern2421, replacement2421)
    pattern2422 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1265, cons1321)
    def replacement2422(m, f, b, d, c, a, x, e):
        rubi.append(2422)
        return Dist((a*d*m + b*c*(m + S(1)))/(b*(m + S(1))), Int((a + b*sin(e + f*x))**m, x), x) - Simp(d*(a + b*sin(e + f*x))**m*cos(e + f*x)/(f*(m + S(1))), x)
    rule2422 = ReplacementRule(pattern2422, replacement2422)
    pattern2423 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1265, cons1321)
    def replacement2423(m, f, b, d, c, a, x, e):
        rubi.append(2423)
        return Dist((a*d*m + b*c*(m + S(1)))/(b*(m + S(1))), Int((a + b*cos(e + f*x))**m, x), x) + Simp(d*(a + b*cos(e + f*x))**m*sin(e + f*x)/(f*(m + S(1))), x)
    rule2423 = ReplacementRule(pattern2423, replacement2423)
    pattern2424 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement2424(f, b, d, c, a, x, e):
        rubi.append(2424)
        return Dist(d/b, Int(sqrt(a + b*sin(e + f*x)), x), x) + Dist((-a*d + b*c)/b, Int(S(1)/sqrt(a + b*sin(e + f*x)), x), x)
    rule2424 = ReplacementRule(pattern2424, replacement2424)
    pattern2425 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement2425(f, b, d, c, a, x, e):
        rubi.append(2425)
        return Dist(d/b, Int(sqrt(a + b*cos(e + f*x)), x), x) + Dist((-a*d + b*c)/b, Int(S(1)/sqrt(a + b*cos(e + f*x)), x), x)
    rule2425 = ReplacementRule(pattern2425, replacement2425)
    pattern2426 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons31, cons168, cons515)
    def replacement2426(m, f, b, d, c, a, x, e):
        rubi.append(2426)
        return Dist(S(1)/(m + S(1)), Int((a + b*sin(e + f*x))**(m + S(-1))*Simp(a*c*(m + S(1)) + b*d*m + (a*d*m + b*c*(m + S(1)))*sin(e + f*x), x), x), x) - Simp(d*(a + b*sin(e + f*x))**m*cos(e + f*x)/(f*(m + S(1))), x)
    rule2426 = ReplacementRule(pattern2426, replacement2426)
    pattern2427 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons31, cons168, cons515)
    def replacement2427(m, f, b, d, c, a, x, e):
        rubi.append(2427)
        return Dist(S(1)/(m + S(1)), Int((a + b*cos(e + f*x))**(m + S(-1))*Simp(a*c*(m + S(1)) + b*d*m + (a*d*m + b*c*(m + S(1)))*cos(e + f*x), x), x), x) + Simp(d*(a + b*cos(e + f*x))**m*sin(e + f*x)/(f*(m + S(1))), x)
    rule2427 = ReplacementRule(pattern2427, replacement2427)
    pattern2428 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons31, cons94, cons515)
    def replacement2428(m, f, b, d, c, a, x, e):
        rubi.append(2428)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp((m + S(1))*(a*c - b*d) - (m + S(2))*(-a*d + b*c)*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(-a*d + b*c)*cos(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2428 = ReplacementRule(pattern2428, replacement2428)
    pattern2429 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons31, cons94, cons515)
    def replacement2429(m, f, b, d, c, a, x, e):
        rubi.append(2429)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp((m + S(1))*(a*c - b*d) - (m + S(2))*(-a*d + b*c)*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(-a*d + b*c)*sin(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2429 = ReplacementRule(pattern2429, replacement2429)
    pattern2430 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1267, cons77, cons1322)
    def replacement2430(m, f, b, d, a, c, x, e):
        rubi.append(2430)
        return Dist(c*cos(e + f*x)/(f*sqrt(-sin(e + f*x) + S(1))*sqrt(sin(e + f*x) + S(1))), Subst(Int(sqrt(S(1) + d*x/c)*(a + b*x)**m/sqrt(S(1) - d*x/c), x), x, sin(e + f*x)), x)
    rule2430 = ReplacementRule(pattern2430, replacement2430)
    pattern2431 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1267, cons77, cons1322)
    def replacement2431(m, f, b, d, a, c, x, e):
        rubi.append(2431)
        return -Dist(c*sin(e + f*x)/(f*sqrt(-cos(e + f*x) + S(1))*sqrt(cos(e + f*x) + S(1))), Subst(Int(sqrt(S(1) + d*x/c)*(a + b*x)**m/sqrt(S(1) - d*x/c), x), x, cos(e + f*x)), x)
    rule2431 = ReplacementRule(pattern2431, replacement2431)
    pattern2432 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1267)
    def replacement2432(m, f, b, d, c, a, x, e):
        rubi.append(2432)
        return Dist(d/b, Int((a + b*sin(e + f*x))**(m + S(1)), x), x) + Dist((-a*d + b*c)/b, Int((a + b*sin(e + f*x))**m, x), x)
    rule2432 = ReplacementRule(pattern2432, replacement2432)
    pattern2433 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1267)
    def replacement2433(m, f, b, d, c, a, x, e):
        rubi.append(2433)
        return Dist(d/b, Int((a + b*cos(e + f*x))**(m + S(1)), x), x) + Dist((-a*d + b*c)/b, Int((a + b*cos(e + f*x))**m, x), x)
    rule2433 = ReplacementRule(pattern2433, replacement2433)
    pattern2434 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons62, cons87)
    def replacement2434(m, f, b, d, a, n, x, e):
        rubi.append(2434)
        return Int(ExpandTrig((d*sin(e + f*x))**n*(a + b*sin(e + f*x))**m, x), x)
    rule2434 = ReplacementRule(pattern2434, replacement2434)
    pattern2435 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons62, cons87)
    def replacement2435(m, f, b, d, a, n, x, e):
        rubi.append(2435)
        return Int(ExpandTrig((d*cos(e + f*x))**n*(a + b*cos(e + f*x))**m, x), x)
    rule2435 = ReplacementRule(pattern2435, replacement2435)
    pattern2436 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1320)
    def replacement2436(m, f, b, a, x, e):
        rubi.append(2436)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(a*m - b*(S(2)*m + S(1))*sin(e + f*x)), x), x) + Simp(b*(a + b*sin(e + f*x))**m*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2436 = ReplacementRule(pattern2436, replacement2436)
    pattern2437 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons1265, cons31, cons1320)
    def replacement2437(m, f, b, a, x, e):
        rubi.append(2437)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(a*m - b*(S(2)*m + S(1))*cos(e + f*x)), x), x) - Simp(b*(a + b*cos(e + f*x))**m*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2437 = ReplacementRule(pattern2437, replacement2437)
    pattern2438 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1321)
    def replacement2438(m, f, b, a, x, e):
        rubi.append(2438)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*sin(e + f*x))**m*(-a*sin(e + f*x) + b*(m + S(1))), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*(m + S(2))), x)
    rule2438 = ReplacementRule(pattern2438, replacement2438)
    pattern2439 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons21, cons1265, cons1321)
    def replacement2439(m, f, b, a, x, e):
        rubi.append(2439)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*cos(e + f*x))**m*(-a*cos(e + f*x) + b*(m + S(1))), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*(m + S(2))), x)
    rule2439 = ReplacementRule(pattern2439, replacement2439)
    pattern2440 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons31, cons94)
    def replacement2440(m, f, b, d, a, c, x, e):
        rubi.append(2440)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(a*c*d*(m + S(-1)) + b*(c**S(2)*(m + S(1)) + d**S(2)) + d*(a*d*(m + S(-1)) + b*c*(m + S(2)))*sin(e + f*x), x), x), x) + Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))*(-a*d + b*c)*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2440 = ReplacementRule(pattern2440, replacement2440)
    pattern2441 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons31, cons94)
    def replacement2441(m, f, b, d, a, c, x, e):
        rubi.append(2441)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(a*c*d*(m + S(-1)) + b*(c**S(2)*(m + S(1)) + d**S(2)) + d*(a*d*(m + S(-1)) + b*c*(m + S(2)))*cos(e + f*x), x), x), x) - Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))*(-a*d + b*c)*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2441 = ReplacementRule(pattern2441, replacement2441)
    pattern2442 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1265, cons272)
    def replacement2442(m, f, b, d, a, c, x, e):
        rubi.append(2442)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*sin(e + f*x))**m*Simp(b*(c**S(2)*(m + S(2)) + d**S(2)*(m + S(1))) - d*(a*d - S(2)*b*c*(m + S(2)))*sin(e + f*x), x), x), x) - Simp(d**S(2)*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*(m + S(2))), x)
    rule2442 = ReplacementRule(pattern2442, replacement2442)
    pattern2443 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1265, cons272)
    def replacement2443(m, f, b, d, a, c, x, e):
        rubi.append(2443)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*cos(e + f*x))**m*Simp(b*(c**S(2)*(m + S(2)) + d**S(2)*(m + S(1))) - d*(a*d - S(2)*b*c*(m + S(2)))*cos(e + f*x), x), x), x) + Simp(d**S(2)*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*(m + S(2))), x)
    rule2443 = ReplacementRule(pattern2443, replacement2443)
    pattern2444 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons93, cons166, cons89, cons1324)
    def replacement2444(m, f, b, d, c, a, n, x, e):
        rubi.append(2444)
        return Dist(b**S(2)/(d*(n + S(1))*(a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(-2))*(c + d*sin(e + f*x))**(n + S(1))*Simp(a*c*(m + S(-2)) - b*d*(m - S(2)*n + S(-4)) - (-a*d*(m + S(2)*n + S(1)) + b*c*(m + S(-1)))*sin(e + f*x), x), x), x) - Simp(b**S(2)*(a + b*sin(e + f*x))**(m + S(-2))*(c + d*sin(e + f*x))**(n + S(1))*(-a*d + b*c)*cos(e + f*x)/(d*f*(n + S(1))*(a*d + b*c)), x)
    rule2444 = ReplacementRule(pattern2444, replacement2444)
    pattern2445 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons93, cons166, cons89, cons1324)
    def replacement2445(m, f, b, d, c, n, a, x, e):
        rubi.append(2445)
        return Dist(b**S(2)/(d*(n + S(1))*(a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(-2))*(c + d*cos(e + f*x))**(n + S(1))*Simp(a*c*(m + S(-2)) - b*d*(m - S(2)*n + S(-4)) - (-a*d*(m + S(2)*n + S(1)) + b*c*(m + S(-1)))*cos(e + f*x), x), x), x) + Simp(b**S(2)*(a + b*cos(e + f*x))**(m + S(-2))*(c + d*cos(e + f*x))**(n + S(1))*(-a*d + b*c)*sin(e + f*x)/(d*f*(n + S(1))*(a*d + b*c)), x)
    rule2445 = ReplacementRule(pattern2445, replacement2445)
    pattern2446 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons31, cons166, cons346, cons1324)
    def replacement2446(m, f, b, d, c, a, n, x, e):
        rubi.append(2446)
        return Dist(S(1)/(d*(m + n)), Int((a + b*sin(e + f*x))**(m + S(-2))*(c + d*sin(e + f*x))**n*Simp(a**S(2)*d*(m + n) + a*b*c*(m + S(-2)) + b**S(2)*d*(n + S(1)) - b*(-a*d*(S(3)*m + S(2)*n + S(-2)) + b*c*(m + S(-1)))*sin(e + f*x), x), x), x) - Simp(b**S(2)*(a + b*sin(e + f*x))**(m + S(-2))*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n)), x)
    rule2446 = ReplacementRule(pattern2446, replacement2446)
    pattern2447 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons31, cons166, cons346, cons1324)
    def replacement2447(m, f, b, d, c, n, a, x, e):
        rubi.append(2447)
        return Dist(S(1)/(d*(m + n)), Int((a + b*cos(e + f*x))**(m + S(-2))*(c + d*cos(e + f*x))**n*Simp(a**S(2)*d*(m + n) + a*b*c*(m + S(-2)) + b**S(2)*d*(n + S(1)) - b*(-a*d*(S(3)*m + S(2)*n + S(-2)) + b*c*(m + S(-1)))*cos(e + f*x), x), x), x) + Simp(b**S(2)*(a + b*cos(e + f*x))**(m + S(-2))*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n)), x)
    rule2447 = ReplacementRule(pattern2447, replacement2447)
    pattern2448 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons93, cons94, cons1325, cons1326)
    def replacement2448(m, f, b, d, c, a, n, x, e):
        rubi.append(2448)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(-1))*Simp(a*d*n - b*c*(m + S(1)) - b*d*(m + n + S(1))*sin(e + f*x), x), x), x) + Simp(b*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2448 = ReplacementRule(pattern2448, replacement2448)
    pattern2449 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons93, cons94, cons1325, cons1326)
    def replacement2449(m, f, b, d, c, n, a, x, e):
        rubi.append(2449)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(-1))*Simp(a*d*n - b*c*(m + S(1)) - b*d*(m + n + S(1))*cos(e + f*x), x), x), x) - Simp(b*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2449 = ReplacementRule(pattern2449, replacement2449)
    pattern2450 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons93, cons94, cons165, cons1326)
    def replacement2450(m, f, b, d, c, a, n, x, e):
        rubi.append(2450)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(-2))*Simp(a*c*d*(m - n + S(1)) + b*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(-1))) + d*(a*d*(m - n + S(1)) + b*c*(m + n))*sin(e + f*x), x), x), x) + Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(-1))*(-a*d + b*c)*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2450 = ReplacementRule(pattern2450, replacement2450)
    pattern2451 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons93, cons94, cons165, cons1326)
    def replacement2451(m, f, b, d, c, n, a, x, e):
        rubi.append(2451)
        return Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(-2))*Simp(a*c*d*(m - n + S(1)) + b*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(-1))) + d*(a*d*(m - n + S(1)) + b*c*(m + n))*cos(e + f*x), x), x), x) - Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(-1))*(-a*d + b*c)*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2451 = ReplacementRule(pattern2451, replacement2451)
    pattern2452 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons31, cons94, cons1327, cons1326)
    def replacement2452(m, f, b, d, c, a, n, x, e):
        rubi.append(2452)
        return Dist(S(1)/(a*(S(2)*m + S(1))*(-a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(-a*d*(S(2)*m + n + S(2)) + b*c*(m + S(1)) + b*d*(m + n + S(2))*sin(e + f*x), x), x), x) + Simp(b**S(2)*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(a*f*(S(2)*m + S(1))*(-a*d + b*c)), x)
    rule2452 = ReplacementRule(pattern2452, replacement2452)
    pattern2453 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons31, cons94, cons1327, cons1326)
    def replacement2453(m, f, b, d, c, n, a, x, e):
        rubi.append(2453)
        return Dist(S(1)/(a*(S(2)*m + S(1))*(-a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(-a*d*(S(2)*m + n + S(2)) + b*c*(m + S(1)) + b*d*(m + n + S(2))*cos(e + f*x), x), x), x) - Simp(b**S(2)*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(a*f*(S(2)*m + S(1))*(-a*d + b*c)), x)
    rule2453 = ReplacementRule(pattern2453, replacement2453)
    pattern2454 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons165, cons1328)
    def replacement2454(f, b, d, c, a, n, x, e):
        rubi.append(2454)
        return -Dist(d/(a*b), Int((c + d*sin(e + f*x))**(n + S(-2))*Simp(-a*c*n + b*d*(n + S(-1)) + (-a*d*n + b*c*(n + S(-1)))*sin(e + f*x), x), x), x) - Simp((c + d*sin(e + f*x))**(n + S(-1))*(-a*d + b*c)*cos(e + f*x)/(a*f*(a + b*sin(e + f*x))), x)
    rule2454 = ReplacementRule(pattern2454, replacement2454)
    pattern2455 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons165, cons1328)
    def replacement2455(f, b, d, c, n, a, x, e):
        rubi.append(2455)
        return -Dist(d/(a*b), Int((c + d*cos(e + f*x))**(n + S(-2))*Simp(-a*c*n + b*d*(n + S(-1)) + (-a*d*n + b*c*(n + S(-1)))*cos(e + f*x), x), x), x) + Simp((c + d*cos(e + f*x))**(n + S(-1))*(-a*d + b*c)*sin(e + f*x)/(a*f*(a + b*cos(e + f*x))), x)
    rule2455 = ReplacementRule(pattern2455, replacement2455)
    pattern2456 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons463, cons1328)
    def replacement2456(f, b, d, c, a, n, x, e):
        rubi.append(2456)
        return Dist(d/(a*(-a*d + b*c)), Int((c + d*sin(e + f*x))**n*(a*n - b*(n + S(1))*sin(e + f*x)), x), x) - Simp(b**S(2)*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(a*f*(a + b*sin(e + f*x))*(-a*d + b*c)), x)
    rule2456 = ReplacementRule(pattern2456, replacement2456)
    pattern2457 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons463, cons1328)
    def replacement2457(f, b, d, c, n, a, x, e):
        rubi.append(2457)
        return Dist(d/(a*(-a*d + b*c)), Int((c + d*cos(e + f*x))**n*(a*n - b*(n + S(1))*cos(e + f*x)), x), x) + Simp(b**S(2)*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(a*f*(a + b*cos(e + f*x))*(-a*d + b*c)), x)
    rule2457 = ReplacementRule(pattern2457, replacement2457)
    pattern2458 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons1328)
    def replacement2458(f, b, d, c, a, n, x, e):
        rubi.append(2458)
        return Dist(d*n/(a*b), Int((a - b*sin(e + f*x))*(c + d*sin(e + f*x))**(n + S(-1)), x), x) - Simp(b*(c + d*sin(e + f*x))**n*cos(e + f*x)/(a*f*(a + b*sin(e + f*x))), x)
    rule2458 = ReplacementRule(pattern2458, replacement2458)
    pattern2459 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons1328)
    def replacement2459(f, b, d, c, n, a, x, e):
        rubi.append(2459)
        return Dist(d*n/(a*b), Int((a - b*cos(e + f*x))*(c + d*cos(e + f*x))**(n + S(-1)), x), x) + Simp(b*(c + d*cos(e + f*x))**n*sin(e + f*x)/(a*f*(a + b*cos(e + f*x))), x)
    rule2459 = ReplacementRule(pattern2459, replacement2459)
    pattern2460 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons88, cons808)
    def replacement2460(f, b, d, c, a, n, x, e):
        rubi.append(2460)
        return Dist(S(2)*n*(a*d + b*c)/(b*(S(2)*n + S(1))), Int(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))**(n + S(-1)), x), x) + Simp(-S(2)*b*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*sqrt(a + b*sin(e + f*x))*(S(2)*n + S(1))), x)
    rule2460 = ReplacementRule(pattern2460, replacement2460)
    pattern2461 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons88, cons808)
    def replacement2461(f, b, d, c, n, a, x, e):
        rubi.append(2461)
        return Dist(S(2)*n*(a*d + b*c)/(b*(S(2)*n + S(1))), Int(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))**(n + S(-1)), x), x) + Simp(S(2)*b*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*sqrt(a + b*cos(e + f*x))*(S(2)*n + S(1))), x)
    rule2461 = ReplacementRule(pattern2461, replacement2461)
    pattern2462 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2462(f, b, d, c, a, x, e):
        rubi.append(2462)
        return Simp(-S(2)*b**S(2)*cos(e + f*x)/(f*sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))*(a*d + b*c)), x)
    rule2462 = ReplacementRule(pattern2462, replacement2462)
    pattern2463 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2463(f, b, d, c, a, x, e):
        rubi.append(2463)
        return Simp(S(2)*b**S(2)*sin(e + f*x)/(f*sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))*(a*d + b*c)), x)
    rule2463 = ReplacementRule(pattern2463, replacement2463)
    pattern2464 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons89, cons1329, cons808)
    def replacement2464(f, b, d, c, a, n, x, e):
        rubi.append(2464)
        return Dist((S(2)*n + S(3))*(-a*d + b*c)/(S(2)*b*(c**S(2) - d**S(2))*(n + S(1))), Int(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))**(n + S(1)), x), x) + Simp((c + d*sin(e + f*x))**(n + S(1))*(-a*d + b*c)*cos(e + f*x)/(f*sqrt(a + b*sin(e + f*x))*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2464 = ReplacementRule(pattern2464, replacement2464)
    pattern2465 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons89, cons808)
    def replacement2465(f, b, d, c, n, a, x, e):
        rubi.append(2465)
        return Dist((S(2)*n + S(3))*(-a*d + b*c)/(S(2)*b*(c**S(2) - d**S(2))*(n + S(1))), Int(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))**(n + S(1)), x), x) - Simp((c + d*cos(e + f*x))**(n + S(1))*(-a*d + b*c)*sin(e + f*x)/(f*sqrt(a + b*cos(e + f*x))*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2465 = ReplacementRule(pattern2465, replacement2465)
    pattern2466 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2466(f, b, d, c, a, x, e):
        rubi.append(2466)
        return Dist(-S(2)*b/f, Subst(Int(S(1)/(a*d + b*c - d*x**S(2)), x), x, b*cos(e + f*x)/sqrt(a + b*sin(e + f*x))), x)
    rule2466 = ReplacementRule(pattern2466, replacement2466)
    pattern2467 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2467(f, b, d, c, a, x, e):
        rubi.append(2467)
        return Dist(S(2)*b/f, Subst(Int(S(1)/(a*d + b*c - d*x**S(2)), x), x, b*sin(e + f*x)/sqrt(a + b*cos(e + f*x))), x)
    rule2467 = ReplacementRule(pattern2467, replacement2467)
    pattern2468 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1330)
    def replacement2468(f, b, d, a, x, e):
        rubi.append(2468)
        return Dist(-S(2)/f, Subst(Int(S(1)/sqrt(S(1) - x**S(2)/a), x), x, b*cos(e + f*x)/sqrt(a + b*sin(e + f*x))), x)
    rule2468 = ReplacementRule(pattern2468, replacement2468)
    pattern2469 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1330)
    def replacement2469(f, b, d, a, x, e):
        rubi.append(2469)
        return Dist(S(2)/f, Subst(Int(S(1)/sqrt(S(1) - x**S(2)/a), x), x, b*sin(e + f*x)/sqrt(a + b*cos(e + f*x))), x)
    rule2469 = ReplacementRule(pattern2469, replacement2469)
    pattern2470 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2470(f, b, d, c, a, x, e):
        rubi.append(2470)
        return Dist(-S(2)*b/f, Subst(Int(S(1)/(b + d*x**S(2)), x), x, b*cos(e + f*x)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x)))), x)
    rule2470 = ReplacementRule(pattern2470, replacement2470)
    pattern2471 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2471(f, b, d, c, a, x, e):
        rubi.append(2471)
        return Dist(S(2)*b/f, Subst(Int(S(1)/(b + d*x**S(2)), x), x, b*sin(e + f*x)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x)))), x)
    rule2471 = ReplacementRule(pattern2471, replacement2471)
    pattern2472 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons543)
    def replacement2472(f, b, d, c, a, n, x, e):
        rubi.append(2472)
        return Dist(a**S(2)*cos(e + f*x)/(f*sqrt(a - b*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), Subst(Int((c + d*x)**n/sqrt(a - b*x), x), x, sin(e + f*x)), x)
    rule2472 = ReplacementRule(pattern2472, replacement2472)
    pattern2473 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons543)
    def replacement2473(f, b, d, c, n, a, x, e):
        rubi.append(2473)
        return -Dist(a**S(2)*sin(e + f*x)/(f*sqrt(a - b*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), Subst(Int((c + d*x)**n/sqrt(a - b*x), x), x, cos(e + f*x)), x)
    rule2473 = ReplacementRule(pattern2473, replacement2473)
    pattern2474 = Pattern(Integral(sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2474(f, b, d, c, a, x, e):
        rubi.append(2474)
        return Dist(d/b, Int(sqrt(a + b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x) + Dist((-a*d + b*c)/b, Int(S(1)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x)
    rule2474 = ReplacementRule(pattern2474, replacement2474)
    pattern2475 = Pattern(Integral(sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2475(f, b, d, c, a, x, e):
        rubi.append(2475)
        return Dist(d/b, Int(sqrt(a + b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x) + Dist((-a*d + b*c)/b, Int(S(1)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x)
    rule2475 = ReplacementRule(pattern2475, replacement2475)
    pattern2476 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons165, cons808)
    def replacement2476(f, b, d, c, a, n, x, e):
        rubi.append(2476)
        return -Dist(S(1)/(b*(S(2)*n + S(-1))), Int((c + d*sin(e + f*x))**(n + S(-2))*Simp(a*c*d - b*(c**S(2)*(S(2)*n + S(-1)) + S(2)*d**S(2)*(n + S(-1))) + d*(a*d - b*c*(S(4)*n + S(-3)))*sin(e + f*x), x)/sqrt(a + b*sin(e + f*x)), x), x) + Simp(-S(2)*d*(c + d*sin(e + f*x))**(n + S(-1))*cos(e + f*x)/(f*sqrt(a + b*sin(e + f*x))*(S(2)*n + S(-1))), x)
    rule2476 = ReplacementRule(pattern2476, replacement2476)
    pattern2477 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons165, cons808)
    def replacement2477(f, b, d, c, n, a, x, e):
        rubi.append(2477)
        return -Dist(S(1)/(b*(S(2)*n + S(-1))), Int((c + d*cos(e + f*x))**(n + S(-2))*Simp(a*c*d - b*(c**S(2)*(S(2)*n + S(-1)) + S(2)*d**S(2)*(n + S(-1))) + d*(a*d - b*c*(S(4)*n + S(-3)))*cos(e + f*x), x)/sqrt(a + b*cos(e + f*x)), x), x) + Simp(S(2)*d*(c + d*cos(e + f*x))**(n + S(-1))*sin(e + f*x)/(f*sqrt(a + b*cos(e + f*x))*(S(2)*n + S(-1))), x)
    rule2477 = ReplacementRule(pattern2477, replacement2477)
    pattern2478 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons89, cons808)
    def replacement2478(f, b, d, c, a, n, x, e):
        rubi.append(2478)
        return -Dist(S(1)/(S(2)*b*(c**S(2) - d**S(2))*(n + S(1))), Int((c + d*sin(e + f*x))**(n + S(1))*Simp(a*d - S(2)*b*c*(n + S(1)) + b*d*(S(2)*n + S(3))*sin(e + f*x), x)/sqrt(a + b*sin(e + f*x)), x), x) - Simp(d*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(f*sqrt(a + b*sin(e + f*x))*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2478 = ReplacementRule(pattern2478, replacement2478)
    pattern2479 = Pattern(Integral((WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_/sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323, cons87, cons89, cons808)
    def replacement2479(f, b, d, c, n, a, x, e):
        rubi.append(2479)
        return -Dist(S(1)/(S(2)*b*(c**S(2) - d**S(2))*(n + S(1))), Int((c + d*cos(e + f*x))**(n + S(1))*Simp(a*d - S(2)*b*c*(n + S(1)) + b*d*(S(2)*n + S(3))*cos(e + f*x), x)/sqrt(a + b*cos(e + f*x)), x), x) + Simp(d*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(f*sqrt(a + b*cos(e + f*x))*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2479 = ReplacementRule(pattern2479, replacement2479)
    pattern2480 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2480(f, b, d, c, a, x, e):
        rubi.append(2480)
        return Dist(b/(-a*d + b*c), Int(S(1)/sqrt(a + b*sin(e + f*x)), x), x) - Dist(d/(-a*d + b*c), Int(sqrt(a + b*sin(e + f*x))/(c + d*sin(e + f*x)), x), x)
    rule2480 = ReplacementRule(pattern2480, replacement2480)
    pattern2481 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2481(f, b, d, c, a, x, e):
        rubi.append(2481)
        return Dist(b/(-a*d + b*c), Int(S(1)/sqrt(a + b*cos(e + f*x)), x), x) - Dist(d/(-a*d + b*c), Int(sqrt(a + b*cos(e + f*x))/(c + d*cos(e + f*x)), x), x)
    rule2481 = ReplacementRule(pattern2481, replacement2481)
    pattern2482 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1330, cons43)
    def replacement2482(f, b, d, a, x, e):
        rubi.append(2482)
        return -Dist(sqrt(S(2))/(sqrt(a)*f), Subst(Int(S(1)/sqrt(-x**S(2) + S(1)), x), x, b*cos(e + f*x)/(a + b*sin(e + f*x))), x)
    rule2482 = ReplacementRule(pattern2482, replacement2482)
    pattern2483 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1330, cons43)
    def replacement2483(f, b, d, a, x, e):
        rubi.append(2483)
        return Dist(sqrt(S(2))/(sqrt(a)*f), Subst(Int(S(1)/sqrt(-x**S(2) + S(1)), x), x, b*sin(e + f*x)/(a + b*cos(e + f*x))), x)
    rule2483 = ReplacementRule(pattern2483, replacement2483)
    pattern2484 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2484(f, b, d, c, a, x, e):
        rubi.append(2484)
        return Dist(-S(2)*a/f, Subst(Int(S(1)/(S(2)*b**S(2) - x**S(2)*(a*c - b*d)), x), x, b*cos(e + f*x)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x)))), x)
    rule2484 = ReplacementRule(pattern2484, replacement2484)
    pattern2485 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1323)
    def replacement2485(f, b, d, c, a, x, e):
        rubi.append(2485)
        return Dist(S(2)*a/f, Subst(Int(S(1)/(S(2)*b**S(2) - x**S(2)*(a*c - b*d)), x), x, b*sin(e + f*x)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x)))), x)
    rule2485 = ReplacementRule(pattern2485, replacement2485)
    pattern2486 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1265, cons1323, cons87, cons165, cons85)
    def replacement2486(m, f, b, d, c, a, n, x, e):
        rubi.append(2486)
        return Dist(S(1)/(b*(m + n)), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(-2))*Simp(b*c**S(2)*(m + n) + d*(a*c*m + b*d*(n + S(-1))) + d*(a*d*m + b*c*(m + S(2)*n + S(-1)))*sin(e + f*x), x), x), x) - Simp(d*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(-1))*cos(e + f*x)/(f*(m + n)), x)
    rule2486 = ReplacementRule(pattern2486, replacement2486)
    pattern2487 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1265, cons1323, cons87, cons165, cons85)
    def replacement2487(m, f, b, d, c, n, a, x, e):
        rubi.append(2487)
        return Dist(S(1)/(b*(m + n)), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(-2))*Simp(b*c**S(2)*(m + n) + d*(a*c*m + b*d*(n + S(-1))) + d*(a*d*m + b*c*(m + S(2)*n + S(-1)))*cos(e + f*x), x), x), x) + Simp(d*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(-1))*sin(e + f*x)/(f*(m + n)), x)
    rule2487 = ReplacementRule(pattern2487, replacement2487)
    pattern2488 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons17)
    def replacement2488(m, f, b, d, c, n, a, x, e):
        rubi.append(2488)
        return Dist(a**m*cos(e + f*x)/(f*sqrt(-sin(e + f*x) + S(1))*sqrt(sin(e + f*x) + S(1))), Subst(Int((S(1) + b*x/a)**(m + S(-1)/2)*(c + d*x)**n/sqrt(S(1) - b*x/a), x), x, sin(e + f*x)), x)
    rule2488 = ReplacementRule(pattern2488, replacement2488)
    pattern2489 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1265, cons1323, cons17)
    def replacement2489(m, f, b, d, c, n, a, x, e):
        rubi.append(2489)
        return -Dist(a**m*sin(e + f*x)/(f*sqrt(-cos(e + f*x) + S(1))*sqrt(cos(e + f*x) + S(1))), Subst(Int((S(1) + b*x/a)**(m + S(-1)/2)*(c + d*x)**n/sqrt(S(1) - b*x/a), x), x, cos(e + f*x)), x)
    rule2489 = ReplacementRule(pattern2489, replacement2489)
    pattern2490 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43, cons1331)
    def replacement2490(m, f, b, d, a, n, x, e):
        rubi.append(2490)
        return -Dist(b*(d/b)**n*cos(e + f*x)/(f*sqrt(a - b*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), Subst(Int((a - x)**n*(S(2)*a - x)**(m + S(-1)/2)/sqrt(x), x), x, a - b*sin(e + f*x)), x)
    rule2490 = ReplacementRule(pattern2490, replacement2490)
    pattern2491 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43, cons1331)
    def replacement2491(m, f, b, d, a, n, x, e):
        rubi.append(2491)
        return Dist(b*(d/b)**n*sin(e + f*x)/(f*sqrt(a - b*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), Subst(Int((a - x)**n*(S(2)*a - x)**(m + S(-1)/2)/sqrt(x), x), x, a - b*cos(e + f*x)), x)
    rule2491 = ReplacementRule(pattern2491, replacement2491)
    pattern2492 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43, cons1332)
    def replacement2492(m, f, b, d, a, n, x, e):
        rubi.append(2492)
        return Dist((d/b)**IntPart(n)*(b*sin(e + f*x))**(-FracPart(n))*(d*sin(e + f*x))**FracPart(n), Int((b*sin(e + f*x))**n*(a + b*sin(e + f*x))**m, x), x)
    rule2492 = ReplacementRule(pattern2492, replacement2492)
    pattern2493 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons43, cons1332)
    def replacement2493(m, f, b, d, a, n, x, e):
        rubi.append(2493)
        return Dist((d/b)**IntPart(n)*(b*cos(e + f*x))**(-FracPart(n))*(d*cos(e + f*x))**FracPart(n), Int((b*cos(e + f*x))**n*(a + b*cos(e + f*x))**m, x), x)
    rule2493 = ReplacementRule(pattern2493, replacement2493)
    pattern2494 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons448)
    def replacement2494(m, f, b, d, a, n, x, e):
        rubi.append(2494)
        return Dist(a**IntPart(m)*(S(1) + b*sin(e + f*x)/a)**(-FracPart(m))*(a + b*sin(e + f*x))**FracPart(m), Int((d*sin(e + f*x))**n*(S(1) + b*sin(e + f*x)/a)**m, x), x)
    rule2494 = ReplacementRule(pattern2494, replacement2494)
    pattern2495 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons18, cons448)
    def replacement2495(m, f, b, d, a, n, x, e):
        rubi.append(2495)
        return Dist(a**IntPart(m)*(S(1) + b*cos(e + f*x)/a)**(-FracPart(m))*(a + b*cos(e + f*x))**FracPart(m), Int((d*cos(e + f*x))**n*(S(1) + b*cos(e + f*x)/a)**m, x), x)
    rule2495 = ReplacementRule(pattern2495, replacement2495)
    pattern2496 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1265, cons1323, cons18)
    def replacement2496(m, f, b, d, a, n, c, x, e):
        rubi.append(2496)
        return Dist(a**S(2)*cos(e + f*x)/(f*sqrt(a - b*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), Subst(Int((a + b*x)**(m + S(-1)/2)*(c + d*x)**n/sqrt(a - b*x), x), x, sin(e + f*x)), x)
    rule2496 = ReplacementRule(pattern2496, replacement2496)
    pattern2497 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1265, cons1323, cons18)
    def replacement2497(m, f, b, d, a, n, c, x, e):
        rubi.append(2497)
        return -Dist(a**S(2)*sin(e + f*x)/(f*sqrt(a - b*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), Subst(Int((a + b*x)**(m + S(-1)/2)*(c + d*x)**n/sqrt(a - b*x), x), x, cos(e + f*x)), x)
    rule2497 = ReplacementRule(pattern2497, replacement2497)
    pattern2498 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons3, cons7, cons27, cons48, cons125, cons21, cons1318)
    def replacement2498(m, f, b, d, c, x, e):
        rubi.append(2498)
        return Dist(S(2)*c*d/b, Int((b*sin(e + f*x))**(m + S(1)), x), x) + Int((b*sin(e + f*x))**m*(c**S(2) + d**S(2)*sin(e + f*x)**S(2)), x)
    rule2498 = ReplacementRule(pattern2498, replacement2498)
    pattern2499 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons3, cons7, cons27, cons48, cons125, cons21, cons1318)
    def replacement2499(m, f, b, d, c, x, e):
        rubi.append(2499)
        return Dist(S(2)*c*d/b, Int((b*cos(e + f*x))**(m + S(1)), x), x) + Int((b*cos(e + f*x))**m*(c**S(2) + d**S(2)*cos(e + f*x)**S(2)), x)
    rule2499 = ReplacementRule(pattern2499, replacement2499)
    pattern2500 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons31, cons94)
    def replacement2500(m, f, b, d, c, a, x, e):
        rubi.append(2500)
        return -Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(b*(m + S(1))*(-a*(c**S(2) + d**S(2)) + S(2)*b*c*d) + (a**S(2)*d**S(2) - S(2)*a*b*c*d*(m + S(2)) + b**S(2)*(c**S(2)*(m + S(2)) + d**S(2)*(m + S(1))))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(a**S(2)*d**S(2) - S(2)*a*b*c*d + b**S(2)*c**S(2))*cos(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2500 = ReplacementRule(pattern2500, replacement2500)
    pattern2501 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons31, cons94)
    def replacement2501(m, f, b, d, c, a, x, e):
        rubi.append(2501)
        return -Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(b*(m + S(1))*(-a*(c**S(2) + d**S(2)) + S(2)*b*c*d) + (a**S(2)*d**S(2) - S(2)*a*b*c*d*(m + S(2)) + b**S(2)*(c**S(2)*(m + S(2)) + d**S(2)*(m + S(1))))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(a**S(2)*d**S(2) - S(2)*a*b*c*d + b**S(2)*c**S(2))*sin(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2501 = ReplacementRule(pattern2501, replacement2501)
    pattern2502 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1267, cons272)
    def replacement2502(m, f, b, d, c, a, x, e):
        rubi.append(2502)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*sin(e + f*x))**m*Simp(b*(c**S(2)*(m + S(2)) + d**S(2)*(m + S(1))) - d*(a*d - S(2)*b*c*(m + S(2)))*sin(e + f*x), x), x), x) - Simp(d**S(2)*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*(m + S(2))), x)
    rule2502 = ReplacementRule(pattern2502, replacement2502)
    pattern2503 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons71, cons1267, cons272)
    def replacement2503(m, f, b, d, c, a, x, e):
        rubi.append(2503)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*cos(e + f*x))**m*Simp(b*(c**S(2)*(m + S(2)) + d**S(2)*(m + S(1))) - d*(a*d - S(2)*b*c*(m + S(2)))*cos(e + f*x), x), x), x) + Simp(d**S(2)*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*(m + S(2))), x)
    rule2503 = ReplacementRule(pattern2503, replacement2503)
    pattern2504 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons93, cons1333, cons89, cons1334)
    def replacement2504(m, f, b, d, c, a, n, x, e):
        rubi.append(2504)
        return Dist(S(1)/(d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*sin(e + f*x))**(m + S(-3))*(c + d*sin(e + f*x))**(n + S(1))*Simp(a*d*(n + S(1))*(-S(2)*a*b*d + c*(a**S(2) + b**S(2))) + b*(m + S(-2))*(-a*d + b*c)**S(2) + b*(b**S(2)*(c**S(2) - d**S(2)) + d*n*(S(2)*a*b*c - d*(a**S(2) + b**S(2))) - m*(-a*d + b*c)**S(2))*sin(e + f*x)**S(2) + (-a*(n + S(2))*(-a*d + b*c)**S(2) + b*(n + S(1))*(a*b*c**S(2) - S(3)*a*b*d**S(2) + c*d*(a**S(2) + b**S(2))))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(-2))*(c + d*sin(e + f*x))**(n + S(1))*(a**S(2)*d**S(2) - S(2)*a*b*c*d + b**S(2)*c**S(2))*cos(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2504 = ReplacementRule(pattern2504, replacement2504)
    pattern2505 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons93, cons1333, cons89, cons1334)
    def replacement2505(m, f, b, d, c, a, n, x, e):
        rubi.append(2505)
        return Dist(S(1)/(d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*cos(e + f*x))**(m + S(-3))*(c + d*cos(e + f*x))**(n + S(1))*Simp(a*d*(n + S(1))*(-S(2)*a*b*d + c*(a**S(2) + b**S(2))) + b*(m + S(-2))*(-a*d + b*c)**S(2) + b*(b**S(2)*(c**S(2) - d**S(2)) + d*n*(S(2)*a*b*c - d*(a**S(2) + b**S(2))) - m*(-a*d + b*c)**S(2))*cos(e + f*x)**S(2) + (-a*(n + S(2))*(-a*d + b*c)**S(2) + b*(n + S(1))*(a*b*c**S(2) - S(3)*a*b*d**S(2) + c*d*(a**S(2) + b**S(2))))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(-2))*(c + d*cos(e + f*x))**(n + S(1))*(a**S(2)*d**S(2) - S(2)*a*b*c*d + b**S(2)*c**S(2))*sin(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2505 = ReplacementRule(pattern2505, replacement2505)
    pattern2506 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1267, cons1323, cons31, cons1333, cons1334, cons1335)
    def replacement2506(m, f, b, d, c, a, n, x, e):
        rubi.append(2506)
        return Dist(S(1)/(d*(m + n)), Int((a + b*sin(e + f*x))**(m + S(-3))*(c + d*sin(e + f*x))**n*Simp(a**S(3)*d*(m + n) + b**S(2)*(a*d*(n + S(1)) + b*c*(m + S(-2))) - b**S(2)*(-a*d*(S(3)*m + S(2)*n + S(-2)) + b*c*(m + S(-1)))*sin(e + f*x)**S(2) - b*(-S(3)*a**S(2)*d*(m + n) + a*b*c - b**S(2)*d*(m + n + S(-1)))*sin(e + f*x), x), x), x) - Simp(b**S(2)*(a + b*sin(e + f*x))**(m + S(-2))*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n)), x)
    rule2506 = ReplacementRule(pattern2506, replacement2506)
    pattern2507 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1267, cons1323, cons31, cons1333, cons1334, cons1335)
    def replacement2507(m, f, b, d, c, a, n, x, e):
        rubi.append(2507)
        return Dist(S(1)/(d*(m + n)), Int((a + b*cos(e + f*x))**(m + S(-3))*(c + d*cos(e + f*x))**n*Simp(a**S(3)*d*(m + n) + b**S(2)*(a*d*(n + S(1)) + b*c*(m + S(-2))) - b**S(2)*(-a*d*(S(3)*m + S(2)*n + S(-2)) + b*c*(m + S(-1)))*cos(e + f*x)**S(2) - b*(-S(3)*a**S(2)*d*(m + n) + a*b*c - b**S(2)*d*(m + n + S(-1)))*cos(e + f*x), x), x), x) + Simp(b**S(2)*(a + b*cos(e + f*x))**(m + S(-2))*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n)), x)
    rule2507 = ReplacementRule(pattern2507, replacement2507)
    pattern2508 = Pattern(Integral(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement2508(f, b, d, a, x, e):
        rubi.append(2508)
        return -Dist(d**S(2)/(a**S(2) - b**S(2)), Int(sqrt(a + b*sin(e + f*x))/(d*sin(e + f*x))**(S(3)/2), x), x) + Simp(-S(2)*a*d*cos(e + f*x)/(f*sqrt(d*sin(e + f*x))*sqrt(a + b*sin(e + f*x))*(a**S(2) - b**S(2))), x)
    rule2508 = ReplacementRule(pattern2508, replacement2508)
    pattern2509 = Pattern(Integral(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement2509(f, b, d, a, x, e):
        rubi.append(2509)
        return -Dist(d**S(2)/(a**S(2) - b**S(2)), Int(sqrt(a + b*cos(e + f*x))/(d*cos(e + f*x))**(S(3)/2), x), x) + Simp(S(2)*a*d*sin(e + f*x)/(f*sqrt(d*cos(e + f*x))*sqrt(a + b*cos(e + f*x))*(a**S(2) - b**S(2))), x)
    rule2509 = ReplacementRule(pattern2509, replacement2509)
    pattern2510 = Pattern(Integral(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2510(f, b, d, a, c, x, e):
        rubi.append(2510)
        return Dist((c - d)/(a - b), Int(S(1)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x) - Dist((-a*d + b*c)/(a - b), Int((sin(e + f*x) + S(1))/((a + b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x), x)
    rule2510 = ReplacementRule(pattern2510, replacement2510)
    pattern2511 = Pattern(Integral(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2511(f, b, d, a, c, x, e):
        rubi.append(2511)
        return Dist((c - d)/(a - b), Int(S(1)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x) - Dist((-a*d + b*c)/(a - b), Int((cos(e + f*x) + S(1))/((a + b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x), x)
    rule2511 = ReplacementRule(pattern2511, replacement2511)
    pattern2512 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons93, cons94, cons1325, cons1170)
    def replacement2512(m, f, b, d, c, a, n, x, e):
        rubi.append(2512)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(-1))*Simp(a*c*(m + S(1)) + b*d*n - b*d*(m + n + S(2))*sin(e + f*x)**S(2) + (a*d*(m + S(1)) - b*c*(m + S(2)))*sin(e + f*x), x), x), x) - Simp(b*(a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2512 = ReplacementRule(pattern2512, replacement2512)
    pattern2513 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons93, cons94, cons1325, cons1170)
    def replacement2513(m, f, b, d, c, a, n, x, e):
        rubi.append(2513)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(-1))*Simp(a*c*(m + S(1)) + b*d*n - b*d*(m + n + S(2))*cos(e + f*x)**S(2) + (a*d*(m + S(1)) - b*c*(m + S(2)))*cos(e + f*x), x), x), x) + Simp(b*(a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2513 = ReplacementRule(pattern2513, replacement2513)
    pattern2514 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement2514(f, b, d, a, x, e):
        rubi.append(2514)
        return Dist(d/b, Int(sqrt(d*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), x), x) - Dist(a*d/b, Int(sqrt(d*sin(e + f*x))/(a + b*sin(e + f*x))**(S(3)/2), x), x)
    rule2514 = ReplacementRule(pattern2514, replacement2514)
    pattern2515 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement2515(f, b, d, a, x, e):
        rubi.append(2515)
        return Dist(d/b, Int(sqrt(d*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), x), x) - Dist(a*d/b, Int(sqrt(d*cos(e + f*x))/(a + b*cos(e + f*x))**(S(3)/2), x), x)
    rule2515 = ReplacementRule(pattern2515, replacement2515)
    pattern2516 = Pattern(Integral((c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2516(f, b, d, a, c, x, e):
        rubi.append(2516)
        return Dist(d**S(2)/b**S(2), Int(sqrt(a + b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x) + Dist((-a*d + b*c)/b**S(2), Int(Simp(a*d + b*c + S(2)*b*d*sin(e + f*x), x)/((a + b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x), x)
    rule2516 = ReplacementRule(pattern2516, replacement2516)
    pattern2517 = Pattern(Integral((c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2517(f, b, d, a, c, x, e):
        rubi.append(2517)
        return Dist(d**S(2)/b**S(2), Int(sqrt(a + b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x) + Dist((-a*d + b*c)/b**S(2), Int(Simp(a*d + b*c + S(2)*b*d*cos(e + f*x), x)/((a + b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x), x)
    rule2517 = ReplacementRule(pattern2517, replacement2517)
    pattern2518 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons93, cons94, cons1336, cons1170)
    def replacement2518(m, f, b, d, c, a, n, x, e):
        rubi.append(2518)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(-2))*Simp(c*(m + S(1))*(a*c - b*d) + d*(n + S(-1))*(-a*d + b*c) - d*(-a*d + b*c)*(m + n + S(1))*sin(e + f*x)**S(2) + (-c*(m + S(2))*(-a*d + b*c) + d*(m + S(1))*(a*c - b*d))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(-1))*(-a*d + b*c)*cos(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2518 = ReplacementRule(pattern2518, replacement2518)
    pattern2519 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons93, cons94, cons1336, cons1170)
    def replacement2519(m, f, b, d, c, a, n, x, e):
        rubi.append(2519)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(-2))*Simp(c*(m + S(1))*(a*c - b*d) + d*(n + S(-1))*(-a*d + b*c) - d*(-a*d + b*c)*(m + n + S(1))*cos(e + f*x)**S(2) + (-c*(m + S(2))*(-a*d + b*c) + d*(m + S(1))*(a*c - b*d))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(-1))*(-a*d + b*c)*sin(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2519 = ReplacementRule(pattern2519, replacement2519)
    pattern2520 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement2520(f, b, d, a, x, e):
        rubi.append(2520)
        return Dist(d/(a**S(2) - b**S(2)), Int((a*sin(e + f*x) + b)/((d*sin(e + f*x))**(S(3)/2)*sqrt(a + b*sin(e + f*x))), x), x) + Simp(S(2)*b*cos(e + f*x)/(f*sqrt(d*sin(e + f*x))*sqrt(a + b*sin(e + f*x))*(a**S(2) - b**S(2))), x)
    rule2520 = ReplacementRule(pattern2520, replacement2520)
    pattern2521 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement2521(f, b, d, a, x, e):
        rubi.append(2521)
        return Dist(d/(a**S(2) - b**S(2)), Int((a*cos(e + f*x) + b)/((d*cos(e + f*x))**(S(3)/2)*sqrt(a + b*cos(e + f*x))), x), x) + Simp(-S(2)*b*sin(e + f*x)/(f*sqrt(d*cos(e + f*x))*sqrt(a + b*cos(e + f*x))*(a**S(2) - b**S(2))), x)
    rule2521 = ReplacementRule(pattern2521, replacement2521)
    pattern2522 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2522(f, b, d, c, a, x, e):
        rubi.append(2522)
        return -Dist(b/(a - b), Int((sin(e + f*x) + S(1))/((a + b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x), x) + Dist(S(1)/(a - b), Int(S(1)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x)
    rule2522 = ReplacementRule(pattern2522, replacement2522)
    pattern2523 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2523(f, b, d, c, a, x, e):
        rubi.append(2523)
        return -Dist(b/(a - b), Int((cos(e + f*x) + S(1))/((a + b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x), x) + Dist(S(1)/(a - b), Int(S(1)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x)
    rule2523 = ReplacementRule(pattern2523, replacement2523)
    pattern2524 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1267, cons1323, cons31, cons94, cons1170, cons1337)
    def replacement2524(m, f, b, d, c, a, n, x, e):
        rubi.append(2524)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(a*(m + S(1))*(-a*d + b*c) + b**S(2)*d*(m + n + S(2)) - b**S(2)*d*(m + n + S(3))*sin(e + f*x)**S(2) - (b**S(2)*c + b*(m + S(1))*(-a*d + b*c))*sin(e + f*x), x), x), x) - Simp(b**S(2)*(a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule2524 = ReplacementRule(pattern2524, replacement2524)
    pattern2525 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons1267, cons1323, cons31, cons94, cons1170, cons1337)
    def replacement2525(m, f, b, d, c, a, n, x, e):
        rubi.append(2525)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(a*(m + S(1))*(-a*d + b*c) + b**S(2)*d*(m + n + S(2)) - b**S(2)*d*(m + n + S(3))*cos(e + f*x)**S(2) - (b**S(2)*c + b*(m + S(1))*(-a*d + b*c))*cos(e + f*x), x), x), x) + Simp(b**S(2)*(a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule2525 = ReplacementRule(pattern2525, replacement2525)
    pattern2526 = Pattern(Integral(sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2526(f, b, d, c, a, x, e):
        rubi.append(2526)
        return Dist(d/b, Int(S(1)/sqrt(c + d*sin(e + f*x)), x), x) + Dist((-a*d + b*c)/b, Int(S(1)/((a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x)
    rule2526 = ReplacementRule(pattern2526, replacement2526)
    pattern2527 = Pattern(Integral(sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2527(f, b, d, c, a, x, e):
        rubi.append(2527)
        return Dist(d/b, Int(S(1)/sqrt(c + d*cos(e + f*x)), x), x) + Dist((-a*d + b*c)/b, Int(S(1)/((a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x)
    rule2527 = ReplacementRule(pattern2527, replacement2527)
    pattern2528 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2528(f, b, d, c, a, x, e):
        rubi.append(2528)
        return Dist(b/d, Int(sqrt(a + b*sin(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int(sqrt(a + b*sin(e + f*x))/(c + d*sin(e + f*x)), x), x)
    rule2528 = ReplacementRule(pattern2528, replacement2528)
    pattern2529 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2529(f, b, d, c, a, x, e):
        rubi.append(2529)
        return Dist(b/d, Int(sqrt(a + b*cos(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int(sqrt(a + b*cos(e + f*x))/(c + d*cos(e + f*x)), x), x)
    rule2529 = ReplacementRule(pattern2529, replacement2529)
    pattern2530 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1338)
    def replacement2530(f, b, d, c, a, x, e):
        rubi.append(2530)
        return Simp(S(2)*EllipticPi(S(2)*b/(a + b), -Pi/S(4) + e/S(2) + f*x/S(2), S(2)*d/(c + d))/(f*(a + b)*sqrt(c + d)), x)
    rule2530 = ReplacementRule(pattern2530, replacement2530)
    pattern2531 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1338)
    def replacement2531(f, b, d, c, a, x, e):
        rubi.append(2531)
        return Simp(S(2)*EllipticPi(S(2)*b/(a + b), e/S(2) + f*x/S(2), S(2)*d/(c + d))/(f*(a + b)*sqrt(c + d)), x)
    rule2531 = ReplacementRule(pattern2531, replacement2531)
    pattern2532 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1339)
    def replacement2532(f, b, d, c, a, x, e):
        rubi.append(2532)
        return Simp(S(2)*EllipticPi(-S(2)*b/(a - b), Pi/S(4) + e/S(2) + f*x/S(2), -S(2)*d/(c - d))/(f*(a - b)*sqrt(c - d)), x)
    rule2532 = ReplacementRule(pattern2532, replacement2532)
    pattern2533 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1339)
    def replacement2533(f, b, d, c, a, x, e):
        rubi.append(2533)
        return Simp(S(2)*EllipticPi(-S(2)*b/(a - b), Pi/S(2) + e/S(2) + f*x/S(2), -S(2)*d/(c - d))/(f*(a - b)*sqrt(c - d)), x)
    rule2533 = ReplacementRule(pattern2533, replacement2533)
    pattern2534 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1340)
    def replacement2534(f, b, d, c, a, x, e):
        rubi.append(2534)
        return Dist(sqrt((c + d*sin(e + f*x))/(c + d))/sqrt(c + d*sin(e + f*x)), Int(S(1)/((a + b*sin(e + f*x))*sqrt(c/(c + d) + d*sin(e + f*x)/(c + d))), x), x)
    rule2534 = ReplacementRule(pattern2534, replacement2534)
    pattern2535 = Pattern(Integral(S(1)/((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1340)
    def replacement2535(f, b, d, c, a, x, e):
        rubi.append(2535)
        return Dist(sqrt((c + d*cos(e + f*x))/(c + d))/sqrt(c + d*cos(e + f*x)), Int(S(1)/((a + b*cos(e + f*x))*sqrt(c/(c + d) + d*cos(e + f*x)/(c + d))), x), x)
    rule2535 = ReplacementRule(pattern2535, replacement2535)
    pattern2536 = Pattern(Integral(sqrt(WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1341, cons1342, cons1343)
    def replacement2536(f, b, d, c, x, e):
        rubi.append(2536)
        return Simp(S(2)*c*sqrt(S(1) - S(1)/sin(e + f*x))*sqrt(S(1) + S(1)/sin(e + f*x))*EllipticPi((c + d)/d, asin(sqrt(c + d*sin(e + f*x))/(sqrt(b*sin(e + f*x))*Rt((c + d)/b, S(2)))), -(c + d)/(c - d))*Rt(b*(c + d), S(2))*tan(e + f*x)/(d*f*sqrt(c**S(2) - d**S(2))), x)
    rule2536 = ReplacementRule(pattern2536, replacement2536)
    pattern2537 = Pattern(Integral(sqrt(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1341, cons1342, cons1343)
    def replacement2537(f, b, d, c, x, e):
        rubi.append(2537)
        return Simp(-S(2)*c*sqrt(S(1) - S(1)/cos(e + f*x))*sqrt(S(1) + S(1)/cos(e + f*x))*EllipticPi((c + d)/d, asin(sqrt(c + d*cos(e + f*x))/(sqrt(b*cos(e + f*x))*Rt((c + d)/b, S(2)))), -(c + d)/(c - d))*Rt(b*(c + d), S(2))/(d*f*sqrt(c**S(2) - d**S(2))*tan(e + f*x)), x)
    rule2537 = ReplacementRule(pattern2537, replacement2537)
    pattern2538 = Pattern(Integral(sqrt(WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1323, cons1342)
    def replacement2538(f, b, d, c, x, e):
        rubi.append(2538)
        return Simp(S(2)*b*sqrt(c*(S(1) - S(1)/sin(e + f*x))/(c + d))*sqrt(c*(S(1) + S(1)/sin(e + f*x))/(c - d))*EllipticPi((c + d)/d, asin(sqrt(c + d*sin(e + f*x))/(sqrt(b*sin(e + f*x))*Rt((c + d)/b, S(2)))), -(c + d)/(c - d))*Rt((c + d)/b, S(2))*tan(e + f*x)/(d*f), x)
    rule2538 = ReplacementRule(pattern2538, replacement2538)
    pattern2539 = Pattern(Integral(sqrt(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1323, cons1342)
    def replacement2539(f, b, d, c, x, e):
        rubi.append(2539)
        return Simp(-S(2)*b*sqrt(c*(S(1) - S(1)/cos(e + f*x))/(c + d))*sqrt(c*(S(1) + S(1)/cos(e + f*x))/(c - d))*EllipticPi((c + d)/d, asin(sqrt(c + d*cos(e + f*x))/(sqrt(b*cos(e + f*x))*Rt((c + d)/b, S(2)))), -(c + d)/(c - d))*Rt((c + d)/b, S(2))/(d*f*tan(e + f*x)), x)
    rule2539 = ReplacementRule(pattern2539, replacement2539)
    pattern2540 = Pattern(Integral(sqrt(WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1323, cons1344)
    def replacement2540(f, b, d, c, x, e):
        rubi.append(2540)
        return Dist(sqrt(b*sin(e + f*x))/sqrt(-b*sin(e + f*x)), Int(sqrt(-b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x)
    rule2540 = ReplacementRule(pattern2540, replacement2540)
    pattern2541 = Pattern(Integral(sqrt(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons3, cons7, cons27, cons48, cons125, cons1323, cons1344)
    def replacement2541(f, b, d, c, x, e):
        rubi.append(2541)
        return Dist(sqrt(b*cos(e + f*x))/sqrt(-b*cos(e + f*x)), Int(sqrt(-b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x)
    rule2541 = ReplacementRule(pattern2541, replacement2541)
    pattern2542 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1345)
    def replacement2542(f, b, d, c, a, x, e):
        rubi.append(2542)
        return Simp(S(2)*sqrt((-a*d + b*c)*(sin(e + f*x) + S(1))/((a + b*sin(e + f*x))*(c - d)))*sqrt(-(-a*d + b*c)*(-sin(e + f*x) + S(1))/((a + b*sin(e + f*x))*(c + d)))*(a + b*sin(e + f*x))*EllipticPi(b*(c + d)/(d*(a + b)), asin(sqrt(c + d*sin(e + f*x))*Rt((a + b)/(c + d), S(2))/sqrt(a + b*sin(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))/(d*f*Rt((a + b)/(c + d), S(2))*cos(e + f*x)), x)
    rule2542 = ReplacementRule(pattern2542, replacement2542)
    pattern2543 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1345)
    def replacement2543(f, b, d, c, a, x, e):
        rubi.append(2543)
        return Simp(-S(2)*sqrt((-a*d + b*c)*(cos(e + f*x) + S(1))/((a + b*cos(e + f*x))*(c - d)))*sqrt(-(-a*d + b*c)*(-cos(e + f*x) + S(1))/((a + b*cos(e + f*x))*(c + d)))*(a + b*cos(e + f*x))*EllipticPi(b*(c + d)/(d*(a + b)), asin(sqrt(c + d*cos(e + f*x))*Rt((a + b)/(c + d), S(2))/sqrt(a + b*cos(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))/(d*f*Rt((a + b)/(c + d), S(2))*sin(e + f*x)), x)
    rule2543 = ReplacementRule(pattern2543, replacement2543)
    pattern2544 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1346)
    def replacement2544(f, b, d, c, a, x, e):
        rubi.append(2544)
        return Dist(sqrt(-c - d*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), Int(sqrt(a + b*sin(e + f*x))/sqrt(-c - d*sin(e + f*x)), x), x)
    rule2544 = ReplacementRule(pattern2544, replacement2544)
    pattern2545 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1346)
    def replacement2545(f, b, d, c, a, x, e):
        rubi.append(2545)
        return Dist(sqrt(-c - d*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), Int(sqrt(a + b*cos(e + f*x))/sqrt(-c - d*cos(e + f*x)), x), x)
    rule2545 = ReplacementRule(pattern2545, replacement2545)
    pattern2546 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1347, cons1348, cons1349)
    def replacement2546(f, b, d, a, x, e):
        rubi.append(2546)
        return Simp(-S(2)*d*EllipticF(asin(cos(e + f*x)/(d*sin(e + f*x) + S(1))), -(a - b*d)/(a + b*d))/(f*sqrt(a + b*d)), x)
    rule2546 = ReplacementRule(pattern2546, replacement2546)
    pattern2547 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1347, cons1348, cons1349)
    def replacement2547(f, b, d, a, x, e):
        rubi.append(2547)
        return Simp(S(2)*d*EllipticF(asin(sin(e + f*x)/(d*cos(e + f*x) + S(1))), -(a - b*d)/(a + b*d))/(f*sqrt(a + b*d)), x)
    rule2547 = ReplacementRule(pattern2547, replacement2547)
    pattern2548 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1347, cons1350, cons1351)
    def replacement2548(f, b, d, a, x, e):
        rubi.append(2548)
        return Dist(sqrt(sin(e + f*x)*sign(b))/sqrt(d*sin(e + f*x)), Int(S(1)/(sqrt(sin(e + f*x)*sign(b))*sqrt(a + b*sin(e + f*x))), x), x)
    rule2548 = ReplacementRule(pattern2548, replacement2548)
    pattern2549 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1347, cons1350, cons1351)
    def replacement2549(f, b, d, a, x, e):
        rubi.append(2549)
        return Dist(sqrt(cos(e + f*x)*sign(b))/sqrt(d*cos(e + f*x)), Int(S(1)/(sqrt(cos(e + f*x)*sign(b))*sqrt(a + b*cos(e + f*x))), x), x)
    rule2549 = ReplacementRule(pattern2549, replacement2549)
    pattern2550 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1271, cons1352, cons1353)
    def replacement2550(f, b, d, a, x, e):
        rubi.append(2550)
        return Simp(-S(2)*sqrt(-S(1)/tan(e + f*x)**S(2))*sqrt(a**S(2))*EllipticF(asin(sqrt(a + b*sin(e + f*x))/(sqrt(d*sin(e + f*x))*Rt((a + b)/d, S(2)))), -(a + b)/(a - b))*Rt((a + b)/d, S(2))*tan(e + f*x)/(a*f*sqrt(a**S(2) - b**S(2))), x)
    rule2550 = ReplacementRule(pattern2550, replacement2550)
    pattern2551 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1271, cons1352, cons1353)
    def replacement2551(f, b, d, a, x, e):
        rubi.append(2551)
        return Simp(S(2)*sqrt(-tan(e + f*x)**S(2))*sqrt(a**S(2))*EllipticF(asin(sqrt(a + b*cos(e + f*x))/(sqrt(d*cos(e + f*x))*Rt((a + b)/d, S(2)))), -(a + b)/(a - b))*Rt((a + b)/d, S(2))/(a*f*sqrt(a**S(2) - b**S(2))*tan(e + f*x)), x)
    rule2551 = ReplacementRule(pattern2551, replacement2551)
    pattern2552 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1352)
    def replacement2552(f, b, d, a, x, e):
        rubi.append(2552)
        return Simp(-S(2)*sqrt(a*(S(1) - S(1)/sin(e + f*x))/(a + b))*sqrt(a*(S(1) + S(1)/sin(e + f*x))/(a - b))*EllipticF(asin(sqrt(a + b*sin(e + f*x))/(sqrt(d*sin(e + f*x))*Rt((a + b)/d, S(2)))), -(a + b)/(a - b))*Rt((a + b)/d, S(2))*tan(e + f*x)/(a*f), x)
    rule2552 = ReplacementRule(pattern2552, replacement2552)
    pattern2553 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1352)
    def replacement2553(f, b, d, a, x, e):
        rubi.append(2553)
        return Simp(S(2)*sqrt(a*(S(1) - S(1)/cos(e + f*x))/(a + b))*sqrt(a*(S(1) + S(1)/cos(e + f*x))/(a - b))*EllipticF(asin(sqrt(a + b*cos(e + f*x))/(sqrt(d*cos(e + f*x))*Rt((a + b)/d, S(2)))), -(a + b)/(a - b))*Rt((a + b)/d, S(2))/(a*f*tan(e + f*x)), x)
    rule2553 = ReplacementRule(pattern2553, replacement2553)
    pattern2554 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1354)
    def replacement2554(f, b, d, a, x, e):
        rubi.append(2554)
        return Dist(sqrt(-d*sin(e + f*x))/sqrt(d*sin(e + f*x)), Int(S(1)/(sqrt(-d*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), x), x)
    rule2554 = ReplacementRule(pattern2554, replacement2554)
    pattern2555 = Pattern(Integral(S(1)/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1354)
    def replacement2555(f, b, d, a, x, e):
        rubi.append(2555)
        return Dist(sqrt(-d*cos(e + f*x))/sqrt(d*cos(e + f*x)), Int(S(1)/(sqrt(-d*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), x), x)
    rule2555 = ReplacementRule(pattern2555, replacement2555)
    pattern2556 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1355)
    def replacement2556(f, b, d, a, c, x, e):
        rubi.append(2556)
        return Simp(S(2)*sqrt((-a*d + b*c)*(-sin(e + f*x) + S(1))/((a + b)*(c + d*sin(e + f*x))))*sqrt(-(-a*d + b*c)*(sin(e + f*x) + S(1))/((a - b)*(c + d*sin(e + f*x))))*(c + d*sin(e + f*x))*EllipticF(asin(sqrt(a + b*sin(e + f*x))*Rt((c + d)/(a + b), S(2))/sqrt(c + d*sin(e + f*x))), (a + b)*(c - d)/((a - b)*(c + d)))/(f*(-a*d + b*c)*Rt((c + d)/(a + b), S(2))*cos(e + f*x)), x)
    rule2556 = ReplacementRule(pattern2556, replacement2556)
    pattern2557 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1355)
    def replacement2557(f, b, d, a, c, x, e):
        rubi.append(2557)
        return Simp(-S(2)*sqrt((-a*d + b*c)*(-cos(e + f*x) + S(1))/((a + b)*(c + d*cos(e + f*x))))*sqrt(-(-a*d + b*c)*(cos(e + f*x) + S(1))/((a - b)*(c + d*cos(e + f*x))))*(c + d*cos(e + f*x))*EllipticF(asin(sqrt(a + b*cos(e + f*x))*Rt((c + d)/(a + b), S(2))/sqrt(c + d*cos(e + f*x))), (a + b)*(c - d)/((a - b)*(c + d)))/(f*(-a*d + b*c)*Rt((c + d)/(a + b), S(2))*sin(e + f*x)), x)
    rule2557 = ReplacementRule(pattern2557, replacement2557)
    pattern2558 = Pattern(Integral(S(1)/(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1356)
    def replacement2558(f, b, d, a, c, x, e):
        rubi.append(2558)
        return Dist(sqrt(-a - b*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), Int(S(1)/(sqrt(-a - b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x)
    rule2558 = ReplacementRule(pattern2558, replacement2558)
    pattern2559 = Pattern(Integral(S(1)/(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons1356)
    def replacement2559(f, b, d, a, c, x, e):
        rubi.append(2559)
        return Dist(sqrt(-a - b*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), Int(S(1)/(sqrt(-a - b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x)
    rule2559 = ReplacementRule(pattern2559, replacement2559)
    pattern2560 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement2560(f, b, d, a, x, e):
        rubi.append(2560)
        return Dist(d/(S(2)*b), Int(sqrt(d*sin(e + f*x))*(a + S(2)*b*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), x), x) - Dist(a*d/(S(2)*b), Int(sqrt(d*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), x), x)
    rule2560 = ReplacementRule(pattern2560, replacement2560)
    pattern2561 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)/sqrt(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    def replacement2561(f, b, d, a, x, e):
        rubi.append(2561)
        return Dist(d/(S(2)*b), Int(sqrt(d*cos(e + f*x))*(a + S(2)*b*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), x), x) - Dist(a*d/(S(2)*b), Int(sqrt(d*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), x), x)
    rule2561 = ReplacementRule(pattern2561, replacement2561)
    pattern2562 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons93, cons1357, cons1358, cons1359, cons1334)
    def replacement2562(m, f, b, d, c, a, n, x, e):
        rubi.append(2562)
        return Dist(S(1)/(d*(m + n)), Int((a + b*sin(e + f*x))**(m + S(-2))*(c + d*sin(e + f*x))**(n + S(-1))*Simp(a**S(2)*c*d*(m + n) + b*d*(a*d*n + b*c*(m + S(-1))) + b*d*(a*d*(S(2)*m + n + S(-1)) + b*c*n)*sin(e + f*x)**S(2) + (a*d*(m + n)*(a*d + S(2)*b*c) - b*d*(a*c - b*d*(m + n + S(-1))))*sin(e + f*x), x), x), x) - Simp(b*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*(m + n)), x)
    rule2562 = ReplacementRule(pattern2562, replacement2562)
    pattern2563 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323, cons93, cons1357, cons1358, cons1359, cons1334)
    def replacement2563(m, f, b, d, c, a, n, x, e):
        rubi.append(2563)
        return Dist(S(1)/(d*(m + n)), Int((a + b*cos(e + f*x))**(m + S(-2))*(c + d*cos(e + f*x))**(n + S(-1))*Simp(a**S(2)*c*d*(m + n) + b*d*(a*d*n + b*c*(m + S(-1))) + b*d*(a*d*(S(2)*m + n + S(-1)) + b*c*n)*cos(e + f*x)**S(2) + (a*d*(m + n)*(a*d + S(2)*b*c) - b*d*(a*c - b*d*(m + n + S(-1))))*cos(e + f*x), x), x), x) + Simp(b*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*(m + n)), x)
    rule2563 = ReplacementRule(pattern2563, replacement2563)
    pattern2564 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons62)
    def replacement2564(m, f, b, d, c, a, n, x, e):
        rubi.append(2564)
        return Dist(b/d, Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1)), x), x) - Dist((-a*d + b*c)/d, Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n, x), x)
    rule2564 = ReplacementRule(pattern2564, replacement2564)
    pattern2565 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons71, cons62)
    def replacement2565(m, f, b, d, c, a, n, x, e):
        rubi.append(2565)
        return Dist(b/d, Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1)), x), x) - Dist((-a*d + b*c)/d, Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n, x), x)
    rule2565 = ReplacementRule(pattern2565, replacement2565)
    pattern2566 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1267, cons1323)
    def replacement2566(m, f, b, d, c, a, n, x, e):
        rubi.append(2566)
        return Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x)
    rule2566 = ReplacementRule(pattern2566, replacement2566)
    pattern2567 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons71, cons1267, cons1323)
    def replacement2567(m, f, b, d, c, a, n, x, e):
        rubi.append(2567)
        return Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x)
    rule2567 = ReplacementRule(pattern2567, replacement2567)
    pattern2568 = Pattern(Integral(((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons23)
    def replacement2568(p, m, f, b, d, c, a, n, x, e):
        rubi.append(2568)
        return Dist(c**IntPart(n)*(c*(d*sin(e + f*x))**p)**FracPart(n)*(d*sin(e + f*x))**(-p*FracPart(n)), Int((d*sin(e + f*x))**(n*p)*(a + b*sin(e + f*x))**m, x), x)
    rule2568 = ReplacementRule(pattern2568, replacement2568)
    pattern2569 = Pattern(Integral(((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*WC('c', S(1)))**n_*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons23)
    def replacement2569(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2569)
        return Dist(c**IntPart(n)*(c*(d*cos(e + f*x))**p)**FracPart(n)*(d*cos(e + f*x))**(-p*FracPart(n)), Int((d*cos(e + f*x))**(n*p)*(a + b*cos(e + f*x))**m, x), x)
    rule2569 = ReplacementRule(pattern2569, replacement2569)
    pattern2570 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons85)
    def replacement2570(m, f, b, d, c, n, a, x, e):
        rubi.append(2570)
        return Int((a + b*sin(e + f*x))**m*(c*sin(e + f*x) + d)**n*sin(e + f*x)**(-n), x)
    rule2570 = ReplacementRule(pattern2570, replacement2570)
    pattern2571 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons85)
    def replacement2571(m, f, b, d, a, n, c, x, e):
        rubi.append(2571)
        return Int((a + b*cos(e + f*x))**m*(c*cos(e + f*x) + d)**n*cos(e + f*x)**(-n), x)
    rule2571 = ReplacementRule(pattern2571, replacement2571)
    pattern2572 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons23, cons17)
    def replacement2572(m, f, b, d, c, n, a, x, e):
        rubi.append(2572)
        return Int((c + d/sin(e + f*x))**n*(a/sin(e + f*x) + b)**m*(S(1)/sin(e + f*x))**(-m), x)
    rule2572 = ReplacementRule(pattern2572, replacement2572)
    pattern2573 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons23, cons17)
    def replacement2573(m, f, b, d, a, c, n, x, e):
        rubi.append(2573)
        return Int((c + d/cos(e + f*x))**n*(a/cos(e + f*x) + b)**m*(S(1)/cos(e + f*x))**(-m), x)
    rule2573 = ReplacementRule(pattern2573, replacement2573)
    pattern2574 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons23, cons18)
    def replacement2574(m, f, b, d, c, n, a, x, e):
        rubi.append(2574)
        return Dist((c + d/sin(e + f*x))**n*(c*sin(e + f*x) + d)**(-n)*sin(e + f*x)**n, Int((a + b*sin(e + f*x))**m*(c*sin(e + f*x) + d)**n*sin(e + f*x)**(-n), x), x)
    rule2574 = ReplacementRule(pattern2574, replacement2574)
    pattern2575 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons23, cons18)
    def replacement2575(m, f, b, d, a, c, n, x, e):
        rubi.append(2575)
        return Dist((c + d/cos(e + f*x))**n*(c*cos(e + f*x) + d)**(-n)*cos(e + f*x)**n, Int((a + b*cos(e + f*x))**m*(c*cos(e + f*x) + d)**n*cos(e + f*x)**(-n), x), x)
    rule2575 = ReplacementRule(pattern2575, replacement2575)
    pattern2576 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement2576(m, f, b, d, c, n, a, x, e):
        rubi.append(2576)
        return Dist(S(1)/(b*f), Subst(Int((a + x)**m*(c + d*x/b)**n, x), x, b*sin(e + f*x)), x)
    rule2576 = ReplacementRule(pattern2576, replacement2576)
    pattern2577 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement2577(m, f, b, d, c, n, a, x, e):
        rubi.append(2577)
        return -Dist(S(1)/(b*f), Subst(Int((a + x)**m*(c + d*x/b)**n, x), x, b*cos(e + f*x)), x)
    rule2577 = ReplacementRule(pattern2577, replacement2577)
    pattern2578 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons5, cons1274, cons85, cons1361)
    def replacement2578(p, f, b, d, a, n, x, e):
        rubi.append(2578)
        return Dist(a, Int((d*sin(e + f*x))**n*cos(e + f*x)**p, x), x) + Dist(b/d, Int((d*sin(e + f*x))**(n + S(1))*cos(e + f*x)**p, x), x)
    rule2578 = ReplacementRule(pattern2578, replacement2578)
    pattern2579 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons5, cons1274, cons85, cons1361)
    def replacement2579(p, f, b, d, a, n, x, e):
        rubi.append(2579)
        return Dist(a, Int((d*cos(e + f*x))**n*sin(e + f*x)**p, x), x) + Dist(b/d, Int((d*cos(e + f*x))**(n + S(1))*sin(e + f*x)**p, x), x)
    rule2579 = ReplacementRule(pattern2579, replacement2579)
    pattern2580 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons5, cons1274, cons1265, cons85, cons1362)
    def replacement2580(p, f, b, d, a, n, x, e):
        rubi.append(2580)
        return Dist(S(1)/a, Int((d*sin(e + f*x))**n*cos(e + f*x)**(p + S(-2)), x), x) - Dist(S(1)/(b*d), Int((d*sin(e + f*x))**(n + S(1))*cos(e + f*x)**(p + S(-2)), x), x)
    rule2580 = ReplacementRule(pattern2580, replacement2580)
    pattern2581 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons5, cons1274, cons1265, cons85, cons1362)
    def replacement2581(p, f, b, d, a, n, x, e):
        rubi.append(2581)
        return Dist(S(1)/a, Int((d*cos(e + f*x))**n*sin(e + f*x)**(p + S(-2)), x), x) - Dist(S(1)/(b*d), Int((d*cos(e + f*x))**(n + S(1))*sin(e + f*x)**(p + S(-2)), x), x)
    rule2581 = ReplacementRule(pattern2581, replacement2581)
    pattern2582 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons48, cons125, cons7, cons27, cons21, cons4, cons1274, cons1265)
    def replacement2582(p, m, f, b, d, c, n, a, x, e):
        rubi.append(2582)
        return Dist(b**(-p)/f, Subst(Int((a - x)**(p/S(2) + S(-1)/2)*(a + x)**(m + p/S(2) + S(-1)/2)*(c + d*x/b)**n, x), x, b*sin(e + f*x)), x)
    rule2582 = ReplacementRule(pattern2582, replacement2582)
    pattern2583 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons48, cons125, cons7, cons27, cons21, cons4, cons1274, cons1265)
    def replacement2583(p, m, f, b, d, c, n, a, x, e):
        rubi.append(2583)
        return -Dist(b**(-p)/f, Subst(Int((a - x)**(p/S(2) + S(-1)/2)*(a + x)**(m + p/S(2) + S(-1)/2)*(c + d*x/b)**n, x), x, b*cos(e + f*x)), x)
    rule2583 = ReplacementRule(pattern2583, replacement2583)
    pattern2584 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1274, cons1267)
    def replacement2584(p, m, f, b, d, c, n, a, x, e):
        rubi.append(2584)
        return Dist(b**(-p)/f, Subst(Int((a + x)**m*(b**S(2) - x**S(2))**(p/S(2) + S(-1)/2)*(c + d*x/b)**n, x), x, b*sin(e + f*x)), x)
    rule2584 = ReplacementRule(pattern2584, replacement2584)
    pattern2585 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1274, cons1267)
    def replacement2585(p, m, f, b, d, c, n, a, x, e):
        rubi.append(2585)
        return -Dist(b**(-p)/f, Subst(Int((a + x)**m*(b**S(2) - x**S(2))**(p/S(2) + S(-1)/2)*(c + d*x/b)**n, x), x, b*cos(e + f*x)), x)
    rule2585 = ReplacementRule(pattern2585, replacement2585)
    pattern2586 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1363)
    def replacement2586(p, f, g, b, d, a, n, x, e):
        rubi.append(2586)
        return Dist(a, Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**p, x), x) + Dist(b/d, Int((d*sin(e + f*x))**(n + S(1))*(g*cos(e + f*x))**p, x), x)
    rule2586 = ReplacementRule(pattern2586, replacement2586)
    pattern2587 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1363)
    def replacement2587(p, f, b, g, d, a, n, x, e):
        rubi.append(2587)
        return Dist(a, Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**p, x), x) + Dist(b/d, Int((d*cos(e + f*x))**(n + S(1))*(g*sin(e + f*x))**p, x), x)
    rule2587 = ReplacementRule(pattern2587, replacement2587)
    pattern2588 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1265)
    def replacement2588(p, f, g, b, d, a, n, x, e):
        rubi.append(2588)
        return Dist(g**S(2)/a, Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**(p + S(-2)), x), x) - Dist(g**S(2)/(b*d), Int((d*sin(e + f*x))**(n + S(1))*(g*cos(e + f*x))**(p + S(-2)), x), x)
    rule2588 = ReplacementRule(pattern2588, replacement2588)
    pattern2589 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1265)
    def replacement2589(p, f, b, g, d, a, n, x, e):
        rubi.append(2589)
        return Dist(g**S(2)/a, Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**(p + S(-2)), x), x) - Dist(g**S(2)/(b*d), Int((d*cos(e + f*x))**(n + S(1))*(g*sin(e + f*x))**(p + S(-2)), x), x)
    rule2589 = ReplacementRule(pattern2589, replacement2589)
    pattern2590 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons17, cons1364)
    def replacement2590(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(2590)
        return Dist(a**m*c**m*g**(-S(2)*m), Int((g*cos(e + f*x))**(S(2)*m + p)*(c + d*sin(e + f*x))**(-m + n), x), x)
    rule2590 = ReplacementRule(pattern2590, replacement2590)
    pattern2591 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons17, cons1364)
    def replacement2591(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(2591)
        return Dist(a**m*c**m*g**(-S(2)*m), Int((g*sin(e + f*x))**(S(2)*m + p)*(c + d*cos(e + f*x))**(-m + n), x), x)
    rule2591 = ReplacementRule(pattern2591, replacement2591)
    pattern2592 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons70, cons1265, cons1306)
    def replacement2592(p, m, f, b, d, a, n, c, x, e):
        rubi.append(2592)
        return Dist(a**(-p/S(2))*c**(-p/S(2)), Int((a + b*sin(e + f*x))**(m + p/S(2))*(c + d*sin(e + f*x))**(n + p/S(2)), x), x)
    rule2592 = ReplacementRule(pattern2592, replacement2592)
    pattern2593 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons70, cons1265, cons1306)
    def replacement2593(p, m, f, b, d, a, n, c, x, e):
        rubi.append(2593)
        return Dist(a**(-p/S(2))*c**(-p/S(2)), Int((a + b*cos(e + f*x))**(m + p/S(2))*(c + d*cos(e + f*x))**(n + p/S(2)), x), x)
    rule2593 = ReplacementRule(pattern2593, replacement2593)
    pattern2594 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons70, cons1265)
    def replacement2594(p, f, b, g, d, a, c, x, e):
        rubi.append(2594)
        return Dist(g*cos(e + f*x)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), Int((g*cos(e + f*x))**(p + S(-1)), x), x)
    rule2594 = ReplacementRule(pattern2594, replacement2594)
    pattern2595 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons70, cons1265)
    def replacement2595(p, f, b, g, d, a, c, x, e):
        rubi.append(2595)
        return Dist(g*sin(e + f*x)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), Int((g*sin(e + f*x))**(p + S(-1)), x), x)
    rule2595 = ReplacementRule(pattern2595, replacement2595)
    pattern2596 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1282, cons142)
    def replacement2596(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2596)
        return Dist(a**IntPart(m)*c**IntPart(m)*g**(-S(2)*IntPart(m))*(g*cos(e + f*x))**(-S(2)*FracPart(m))*(a + b*sin(e + f*x))**FracPart(m)*(c + d*sin(e + f*x))**FracPart(m), Int((g*cos(e + f*x))**(S(2)*m + p)/(c + d*sin(e + f*x)), x), x)
    rule2596 = ReplacementRule(pattern2596, replacement2596)
    pattern2597 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1282, cons142)
    def replacement2597(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2597)
        return Dist(a**IntPart(m)*c**IntPart(m)*g**(-S(2)*IntPart(m))*(g*sin(e + f*x))**(-S(2)*FracPart(m))*(a + b*cos(e + f*x))**FracPart(m)*(c + d*cos(e + f*x))**FracPart(m), Int((g*sin(e + f*x))**(S(2)*m + p)/(c + d*cos(e + f*x)), x), x)
    rule2597 = ReplacementRule(pattern2597, replacement2597)
    pattern2598 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1282, cons335)
    def replacement2598(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2598)
        return Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n/(f*g*(m - n + S(-1))), x)
    rule2598 = ReplacementRule(pattern2598, replacement2598)
    pattern2599 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1282, cons335)
    def replacement2599(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2599)
        return -Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n/(f*g*(m - n + S(-1))), x)
    rule2599 = ReplacementRule(pattern2599, replacement2599)
    pattern2600 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons70, cons1265, cons1284, cons87, cons89, cons1365, cons1366)
    def replacement2600(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2600)
        return -Dist(b*(S(2)*m + p + S(-1))/(d*(S(2)*n + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1)), x), x) + Simp(-S(2)*b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n/(f*g*(S(2)*n + p + S(1))), x)
    rule2600 = ReplacementRule(pattern2600, replacement2600)
    pattern2601 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons70, cons1265, cons1284, cons87, cons89, cons1365, cons1366)
    def replacement2601(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2601)
        return -Dist(b*(S(2)*m + p + S(-1))/(d*(S(2)*n + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1)), x), x) + Simp(S(2)*b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n/(f*g*(S(2)*n + p + S(1))), x)
    rule2601 = ReplacementRule(pattern2601, replacement2601)
    pattern2602 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons1284, cons346, cons1367, cons1366)
    def replacement2602(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2602)
        return Dist(a*(S(2)*m + p + S(-1))/(m + n + p), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n, x), x) - Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n/(f*g*(m + n + p)), x)
    rule2602 = ReplacementRule(pattern2602, replacement2602)
    pattern2603 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons1284, cons346, cons1367, cons1366)
    def replacement2603(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2603)
        return Dist(a*(S(2)*m + p + S(-1))/(m + n + p), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n, x), x) + Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n/(f*g*(m + n + p)), x)
    rule2603 = ReplacementRule(pattern2603, replacement2603)
    pattern2604 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons70, cons1265, cons1368)
    def replacement2604(p, m, f, b, g, d, a, c, x, e):
        rubi.append(2604)
        return Dist(a**IntPart(m)*c**IntPart(m)*g**(-S(2)*IntPart(m))*(g*cos(e + f*x))**(-S(2)*FracPart(m))*(a + b*sin(e + f*x))**FracPart(m)*(c + d*sin(e + f*x))**FracPart(m), Int((g*cos(e + f*x))**(S(2)*m + p), x), x)
    rule2604 = ReplacementRule(pattern2604, replacement2604)
    pattern2605 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons70, cons1265, cons1368)
    def replacement2605(p, m, f, b, g, d, a, c, x, e):
        rubi.append(2605)
        return Dist(a**IntPart(m)*c**IntPart(m)*g**(-S(2)*IntPart(m))*(g*sin(e + f*x))**(-S(2)*FracPart(m))*(a + b*cos(e + f*x))**FracPart(m)*(c + d*cos(e + f*x))**FracPart(m), Int((g*sin(e + f*x))**(S(2)*m + p), x), x)
    rule2605 = ReplacementRule(pattern2605, replacement2605)
    pattern2606 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1369, cons1260)
    def replacement2606(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2606)
        return Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n/(a*f*g*(m - n)), x)
    rule2606 = ReplacementRule(pattern2606, replacement2606)
    pattern2607 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1369, cons1260)
    def replacement2607(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2607)
        return -Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n/(a*f*g*(m - n)), x)
    rule2607 = ReplacementRule(pattern2607, replacement2607)
    pattern2608 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1370, cons1281, cons114)
    def replacement2608(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2608)
        return Dist((m + n + p + S(1))/(a*(S(2)*m + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n, x), x) + Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2608 = ReplacementRule(pattern2608, replacement2608)
    pattern2609 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1370, cons1281, cons114)
    def replacement2609(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2609)
        return Dist((m + n + p + S(1))/(a*(S(2)*m + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n, x), x) - Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2609 = ReplacementRule(pattern2609, replacement2609)
    pattern2610 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons70, cons1265, cons93, cons168, cons89, cons1365, cons170)
    def replacement2610(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2610)
        return -Dist(b*(S(2)*m + p + S(-1))/(d*(S(2)*n + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1)), x), x) + Simp(-S(2)*b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n/(f*g*(S(2)*n + p + S(1))), x)
    rule2610 = ReplacementRule(pattern2610, replacement2610)
    pattern2611 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons70, cons1265, cons93, cons168, cons89, cons1365, cons170)
    def replacement2611(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2611)
        return -Dist(b*(S(2)*m + p + S(-1))/(d*(S(2)*n + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1)), x), x) + Simp(S(2)*b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n/(f*g*(S(2)*n + p + S(1))), x)
    rule2611 = ReplacementRule(pattern2611, replacement2611)
    pattern2612 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons31, cons168, cons1371, cons1372, cons170)
    def replacement2612(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2612)
        return Dist(a*(S(2)*m + p + S(-1))/(m + n + p), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n, x), x) - Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n/(f*g*(m + n + p)), x)
    rule2612 = ReplacementRule(pattern2612, replacement2612)
    pattern2613 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons31, cons168, cons1371, cons1372, cons170)
    def replacement2613(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2613)
        return Dist(a*(S(2)*m + p + S(-1))/(m + n + p), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n, x), x) + Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n/(f*g*(m + n + p)), x)
    rule2613 = ReplacementRule(pattern2613, replacement2613)
    pattern2614 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons31, cons94, cons1281, cons1316, cons170)
    def replacement2614(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2614)
        return Dist((m + n + p + S(1))/(a*(S(2)*m + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n, x), x) + Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2614 = ReplacementRule(pattern2614, replacement2614)
    pattern2615 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons70, cons1265, cons31, cons94, cons1281, cons1316, cons170)
    def replacement2615(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2615)
        return Dist((m + n + p + S(1))/(a*(S(2)*m + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n, x), x) - Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2615 = ReplacementRule(pattern2615, replacement2615)
    pattern2616 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1317)
    def replacement2616(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2616)
        return Dist(a**IntPart(m)*c**IntPart(m)*g**(-S(2)*IntPart(m))*(g*cos(e + f*x))**(-S(2)*FracPart(m))*(a + b*sin(e + f*x))**FracPart(m)*(c + d*sin(e + f*x))**FracPart(m), Int((g*cos(e + f*x))**(S(2)*m + p)*(c + d*sin(e + f*x))**(-m + n), x), x)
    rule2616 = ReplacementRule(pattern2616, replacement2616)
    pattern2617 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons70, cons1265, cons1317)
    def replacement2617(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2617)
        return Dist(a**IntPart(m)*c**IntPart(m)*g**(-S(2)*IntPart(m))*(g*sin(e + f*x))**(-S(2)*FracPart(m))*(a + b*cos(e + f*x))**FracPart(m)*(c + d*cos(e + f*x))**FracPart(m), Int((g*sin(e + f*x))**(S(2)*m + p)*(c + d*cos(e + f*x))**(-m + n), x), x)
    rule2617 = ReplacementRule(pattern2617, replacement2617)
    pattern2618 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons1265, cons1373)
    def replacement2618(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2618)
        return -Simp(d*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(f*g*(m + p + S(1))), x)
    rule2618 = ReplacementRule(pattern2618, replacement2618)
    pattern2619 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons1265, cons1373)
    def replacement2619(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2619)
        return Simp(d*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(f*g*(m + p + S(1))), x)
    rule2619 = ReplacementRule(pattern2619, replacement2619)
    pattern2620 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1265, cons244, cons1374, cons137)
    def replacement2620(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2620)
        return Dist(b*(a*d*m + b*c*(m + p + S(1)))/(a*g**S(2)*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**(m + S(-1)), x), x) - Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m*(a*d + b*c)/(a*f*g*(p + S(1))), x)
    rule2620 = ReplacementRule(pattern2620, replacement2620)
    pattern2621 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1265, cons244, cons1374, cons137)
    def replacement2621(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2621)
        return Dist(b*(a*d*m + b*c*(m + p + S(1)))/(a*g**S(2)*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**(m + S(-1)), x), x) + Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m*(a*d + b*c)/(a*f*g*(p + S(1))), x)
    rule2621 = ReplacementRule(pattern2621, replacement2621)
    pattern2622 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons1265, cons1375, cons253)
    def replacement2622(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2622)
        return Dist((a*d*m + b*c*(m + p + S(1)))/(b*(m + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**m, x), x) - Simp(d*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(f*g*(m + p + S(1))), x)
    rule2622 = ReplacementRule(pattern2622, replacement2622)
    pattern2623 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons1265, cons1375, cons253)
    def replacement2623(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2623)
        return Dist((a*d*m + b*c*(m + p + S(1)))/(b*(m + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**m, x), x) + Simp(d*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(f*g*(m + p + S(1))), x)
    rule2623 = ReplacementRule(pattern2623, replacement2623)
    pattern2624 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1265, cons31, cons1376)
    def replacement2624(m, f, b, d, c, a, x, e):
        rubi.append(2624)
        return Dist(S(1)/(b**S(3)*(S(2)*m + S(3))), Int((a + b*sin(e + f*x))**(m + S(2))*(S(2)*a*d*(m + S(1)) + b*c - b*d*(S(2)*m + S(3))*sin(e + f*x)), x), x) + Simp(S(2)*(a + b*sin(e + f*x))**(m + S(1))*(-a*d + b*c)*cos(e + f*x)/(b**S(2)*f*(S(2)*m + S(3))), x)
    rule2624 = ReplacementRule(pattern2624, replacement2624)
    pattern2625 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1265, cons31, cons1376)
    def replacement2625(m, f, b, d, c, a, x, e):
        rubi.append(2625)
        return Dist(S(1)/(b**S(3)*(S(2)*m + S(3))), Int((a + b*cos(e + f*x))**(m + S(2))*(S(2)*a*d*(m + S(1)) + b*c - b*d*(S(2)*m + S(3))*cos(e + f*x)), x), x) + Simp(-S(2)*(a + b*cos(e + f*x))**(m + S(1))*(-a*d + b*c)*sin(e + f*x)/(b**S(2)*f*(S(2)*m + S(3))), x)
    rule2625 = ReplacementRule(pattern2625, replacement2625)
    pattern2626 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1265, cons31, cons1377)
    def replacement2626(m, f, b, d, c, a, x, e):
        rubi.append(2626)
        return -Dist(S(1)/(b**S(2)*(m + S(3))), Int((a + b*sin(e + f*x))**(m + S(1))*(-a*c*(m + S(3)) + b*d*(m + S(2)) + (-a*d*(m + S(4)) + b*c*(m + S(3)))*sin(e + f*x)), x), x) + Simp(d*(a + b*sin(e + f*x))**(m + S(2))*cos(e + f*x)/(b**S(2)*f*(m + S(3))), x)
    rule2626 = ReplacementRule(pattern2626, replacement2626)
    pattern2627 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1265, cons31, cons1377)
    def replacement2627(m, f, b, d, c, a, x, e):
        rubi.append(2627)
        return -Dist(S(1)/(b**S(2)*(m + S(3))), Int((a + b*cos(e + f*x))**(m + S(1))*(-a*c*(m + S(3)) + b*d*(m + S(2)) + (-a*d*(m + S(4)) + b*c*(m + S(3)))*cos(e + f*x)), x), x) - Simp(d*(a + b*cos(e + f*x))**(m + S(2))*sin(e + f*x)/(b**S(2)*f*(m + S(3))), x)
    rule2627 = ReplacementRule(pattern2627, replacement2627)
    pattern2628 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons1265, cons1378, cons1281)
    def replacement2628(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2628)
        return Dist((a*d*m + b*c*(m + p + S(1)))/(a*b*(S(2)*m + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(1)), x), x) + Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m*(-a*d + b*c)/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2628 = ReplacementRule(pattern2628, replacement2628)
    pattern2629 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons1265, cons1378, cons1281)
    def replacement2629(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2629)
        return Dist((a*d*m + b*c*(m + p + S(1)))/(a*b*(S(2)*m + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(1)), x), x) - Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m*(-a*d + b*c)/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2629 = ReplacementRule(pattern2629, replacement2629)
    pattern2630 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons1265, cons253)
    def replacement2630(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2630)
        return Dist((a*d*m + b*c*(m + p + S(1)))/(b*(m + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**m, x), x) - Simp(d*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(f*g*(m + p + S(1))), x)
    rule2630 = ReplacementRule(pattern2630, replacement2630)
    pattern2631 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons1265, cons253)
    def replacement2631(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2631)
        return Dist((a*d*m + b*c*(m + p + S(1)))/(b*(m + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**m, x), x) + Simp(d*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(f*g*(m + p + S(1))), x)
    rule2631 = ReplacementRule(pattern2631, replacement2631)
    pattern2632 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1267, cons244, cons168, cons137, cons515)
    def replacement2632(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2632)
        return Dist(S(1)/(g**S(2)*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**(m + S(-1))*Simp(a*c*(p + S(2)) + b*c*(m + p + S(2))*sin(e + f*x) + b*d*m, x), x), x) - Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m*(c*sin(e + f*x) + d)/(f*g*(p + S(1))), x)
    rule2632 = ReplacementRule(pattern2632, replacement2632)
    pattern2633 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1267, cons244, cons168, cons137, cons515)
    def replacement2633(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2633)
        return Dist(S(1)/(g**S(2)*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**(m + S(-1))*Simp(a*c*(p + S(2)) + b*c*(m + p + S(2))*cos(e + f*x) + b*d*m, x), x), x) + Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m*(c*cos(e + f*x) + d)/(f*g*(p + S(1))), x)
    rule2633 = ReplacementRule(pattern2633, replacement2633)
    pattern2634 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons1267, cons31, cons168, cons1379, cons515)
    def replacement2634(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2634)
        return Dist(S(1)/(m + p + S(1)), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(-1))*Simp(a*c*(m + p + S(1)) + b*d*m + (a*d*m + b*c*(m + p + S(1)))*sin(e + f*x), x), x), x) - Simp(d*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(f*g*(m + p + S(1))), x)
    rule2634 = ReplacementRule(pattern2634, replacement2634)
    pattern2635 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons1267, cons31, cons168, cons1379, cons515)
    def replacement2635(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2635)
        return Dist(S(1)/(m + p + S(1)), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(-1))*Simp(a*c*(m + p + S(1)) + b*d*m + (a*d*m + b*c*(m + p + S(1)))*cos(e + f*x), x), x), x) + Simp(d*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(f*g*(m + p + S(1))), x)
    rule2635 = ReplacementRule(pattern2635, replacement2635)
    pattern2636 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1267, cons244, cons94, cons146, cons253, cons515)
    def replacement2636(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2636)
        return Dist(g**S(2)*(p + S(-1))/(b**S(2)*(m + S(1))*(m + p + S(1))), Int((g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**(m + S(1))*Simp(b*d*(m + S(1)) + (-a*d*p + b*c*(m + p + S(1)))*sin(e + f*x), x), x), x) + Simp(g*(g*cos(e + f*x))**(p + S(-1))*(a + b*sin(e + f*x))**(m + S(1))*(-a*d*p + b*c*(m + p + S(1)) + b*d*(m + S(1))*sin(e + f*x))/(b**S(2)*f*(m + S(1))*(m + p + S(1))), x)
    rule2636 = ReplacementRule(pattern2636, replacement2636)
    pattern2637 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1267, cons244, cons94, cons146, cons253, cons515)
    def replacement2637(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2637)
        return Dist(g**S(2)*(p + S(-1))/(b**S(2)*(m + S(1))*(m + p + S(1))), Int((g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**(m + S(1))*Simp(b*d*(m + S(1)) + (-a*d*p + b*c*(m + p + S(1)))*cos(e + f*x), x), x), x) - Simp(g*(g*sin(e + f*x))**(p + S(-1))*(a + b*cos(e + f*x))**(m + S(1))*(-a*d*p + b*c*(m + p + S(1)) + b*d*(m + S(1))*cos(e + f*x))/(b**S(2)*f*(m + S(1))*(m + p + S(1))), x)
    rule2637 = ReplacementRule(pattern2637, replacement2637)
    pattern2638 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons1267, cons31, cons94, cons515)
    def replacement2638(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2638)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(1))*Simp((m + S(1))*(a*c - b*d) - (-a*d + b*c)*(m + p + S(2))*sin(e + f*x), x), x), x) - Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(1))*(-a*d + b*c)/(f*g*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2638 = ReplacementRule(pattern2638, replacement2638)
    pattern2639 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons1267, cons31, cons94, cons515)
    def replacement2639(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2639)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(1))*Simp((m + S(1))*(a*c - b*d) - (-a*d + b*c)*(m + p + S(2))*cos(e + f*x), x), x), x) + Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(1))*(-a*d + b*c)/(f*g*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2639 = ReplacementRule(pattern2639, replacement2639)
    pattern2640 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons1267, cons13, cons146, cons1285, cons253, cons515)
    def replacement2640(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2640)
        return Dist(g**S(2)*(p + S(-1))/(b**S(2)*(m + p)*(m + p + S(1))), Int((g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**m*Simp(b*(a*d*m + b*c*(m + p + S(1))) + (a*b*c*(m + p + S(1)) - d*(a**S(2)*p - b**S(2)*(m + p)))*sin(e + f*x), x), x), x) + Simp(g*(g*cos(e + f*x))**(p + S(-1))*(a + b*sin(e + f*x))**(m + S(1))*(-a*d*p + b*c*(m + p + S(1)) + b*d*(m + p)*sin(e + f*x))/(b**S(2)*f*(m + p)*(m + p + S(1))), x)
    rule2640 = ReplacementRule(pattern2640, replacement2640)
    pattern2641 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons1267, cons13, cons146, cons1285, cons253, cons515)
    def replacement2641(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2641)
        return Dist(g**S(2)*(p + S(-1))/(b**S(2)*(m + p)*(m + p + S(1))), Int((g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**m*Simp(b*(a*d*m + b*c*(m + p + S(1))) + (a*b*c*(m + p + S(1)) - d*(a**S(2)*p - b**S(2)*(m + p)))*cos(e + f*x), x), x), x) - Simp(g*(g*sin(e + f*x))**(p + S(-1))*(a + b*cos(e + f*x))**(m + S(1))*(-a*d*p + b*c*(m + p + S(1)) + b*d*(m + p)*cos(e + f*x))/(b**S(2)*f*(m + p)*(m + p + S(1))), x)
    rule2641 = ReplacementRule(pattern2641, replacement2641)
    pattern2642 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons1267, cons13, cons137, cons515)
    def replacement2642(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2642)
        return Dist(S(1)/(g**S(2)*(a**S(2) - b**S(2))*(p + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**m*Simp(a*b*d*m + b*(a*c - b*d)*(m + p + S(3))*sin(e + f*x) + c*(a**S(2)*(p + S(2)) - b**S(2)*(m + p + S(2))), x), x), x) + Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(1))*(-a*d + b*c - (a*c - b*d)*sin(e + f*x))/(f*g*(a**S(2) - b**S(2))*(p + S(1))), x)
    rule2642 = ReplacementRule(pattern2642, replacement2642)
    pattern2643 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons1267, cons13, cons137, cons515)
    def replacement2643(p, m, f, b, g, d, c, a, x, e):
        rubi.append(2643)
        return Dist(S(1)/(g**S(2)*(a**S(2) - b**S(2))*(p + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**m*Simp(a*b*d*m + b*(a*c - b*d)*(m + p + S(3))*cos(e + f*x) + c*(a**S(2)*(p + S(2)) - b**S(2)*(m + p + S(2))), x), x), x) - Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(1))*(-a*d + b*c - (a*c - b*d)*cos(e + f*x))/(f*g*(a**S(2) - b**S(2))*(p + S(1))), x)
    rule2643 = ReplacementRule(pattern2643, replacement2643)
    pattern2644 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1267)
    def replacement2644(p, f, b, g, d, c, a, x, e):
        rubi.append(2644)
        return Dist(d/b, Int((g*cos(e + f*x))**p, x), x) + Dist((-a*d + b*c)/b, Int((g*cos(e + f*x))**p/(a + b*sin(e + f*x)), x), x)
    rule2644 = ReplacementRule(pattern2644, replacement2644)
    pattern2645 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons1267)
    def replacement2645(p, f, b, g, d, c, a, x, e):
        rubi.append(2645)
        return Dist(d/b, Int((g*sin(e + f*x))**p, x), x) + Dist((-a*d + b*c)/b, Int((g*sin(e + f*x))**p/(a + b*cos(e + f*x)), x), x)
    rule2645 = ReplacementRule(pattern2645, replacement2645)
    pattern2646 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1267, cons1322)
    def replacement2646(p, m, f, b, g, d, a, c, x, e):
        rubi.append(2646)
        return Dist(c*g*(g*cos(e + f*x))**(p + S(-1))*(-sin(e + f*x) + S(1))**(-p/S(2) + S(1)/2)*(sin(e + f*x) + S(1))**(-p/S(2) + S(1)/2)/f, Subst(Int((S(1) - d*x/c)**(p/S(2) + S(-1)/2)*(S(1) + d*x/c)**(p/S(2) + S(1)/2)*(a + b*x)**m, x), x, sin(e + f*x)), x)
    rule2646 = ReplacementRule(pattern2646, replacement2646)
    pattern2647 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons5, cons1267, cons1322)
    def replacement2647(p, m, f, b, g, d, a, c, x, e):
        rubi.append(2647)
        return -Dist(c*g*(g*sin(e + f*x))**(p + S(-1))*(-cos(e + f*x) + S(1))**(-p/S(2) + S(1)/2)*(cos(e + f*x) + S(1))**(-p/S(2) + S(1)/2)/f, Subst(Int((S(1) - d*x/c)**(p/S(2) + S(-1)/2)*(S(1) + d*x/c)**(p/S(2) + S(1)/2)*(a + b*x)**m, x), x, cos(e + f*x)), x)
    rule2647 = ReplacementRule(pattern2647, replacement2647)
    pattern2648 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons1299, cons1380)
    def replacement2648(p, m, f, b, d, a, n, x, e):
        rubi.append(2648)
        return Dist(a**(S(2)*m), Int((d*sin(e + f*x))**n*(a - b*sin(e + f*x))**(-m), x), x)
    rule2648 = ReplacementRule(pattern2648, replacement2648)
    pattern2649 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons1299, cons1380)
    def replacement2649(p, m, f, b, d, a, n, x, e):
        rubi.append(2649)
        return Dist(a**(S(2)*m), Int((d*cos(e + f*x))**n*(a - b*cos(e + f*x))**(-m), x), x)
    rule2649 = ReplacementRule(pattern2649, replacement2649)
    pattern2650 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons358)
    def replacement2650(p, m, f, b, g, a, x, e):
        rubi.append(2650)
        return Dist(a/(S(2)*g**S(2)), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**(m + S(-1)), x), x) - Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(1))/(S(2)*b*f*g*(m + S(1))), x)
    rule2650 = ReplacementRule(pattern2650, replacement2650)
    pattern2651 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons358)
    def replacement2651(p, m, f, b, g, a, x, e):
        rubi.append(2651)
        return Dist(a/(S(2)*g**S(2)), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**(m + S(-1)), x), x) + Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(1))/(S(2)*b*f*g*(m + S(1))), x)
    rule2651 = ReplacementRule(pattern2651, replacement2651)
    pattern2652 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1278)
    def replacement2652(p, m, f, b, g, a, x, e):
        rubi.append(2652)
        return -Dist(g**(S(-2)), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**m, x), x) + Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(a*f*g*m), x)
    rule2652 = ReplacementRule(pattern2652, replacement2652)
    pattern2653 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1278)
    def replacement2653(p, m, f, b, g, a, x, e):
        rubi.append(2653)
        return -Dist(g**(S(-2)), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**m, x), x) - Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(a*f*g*m), x)
    rule2653 = ReplacementRule(pattern2653, replacement2653)
    pattern2654 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1381, cons1382)
    def replacement2654(p, m, f, b, d, a, n, x, e):
        rubi.append(2654)
        return Dist(a**(-p), Int(ExpandTrig((d*sin(e + f*x))**n*(a - b*sin(e + f*x))**(p/S(2))*(a + b*sin(e + f*x))**(m + p/S(2)), x), x), x)
    rule2654 = ReplacementRule(pattern2654, replacement2654)
    pattern2655 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons1265, cons1381, cons1382)
    def replacement2655(p, m, f, b, d, a, n, x, e):
        rubi.append(2655)
        return Dist(a**(-p), Int(ExpandTrig((d*cos(e + f*x))**n*(a - b*cos(e + f*x))**(p/S(2))*(a + b*cos(e + f*x))**(m + p/S(2)), x), x), x)
    rule2655 = ReplacementRule(pattern2655, replacement2655)
    pattern2656 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1265, cons62)
    def replacement2656(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2656)
        return Int(ExpandTrig((g*cos(e + f*x))**p, (d*sin(e + f*x))**n*(a + b*sin(e + f*x))**m, x), x)
    rule2656 = ReplacementRule(pattern2656, replacement2656)
    pattern2657 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1265, cons62)
    def replacement2657(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2657)
        return Int(ExpandTrig((g*sin(e + f*x))**p, (d*cos(e + f*x))**n*(a + b*cos(e + f*x))**m, x), x)
    rule2657 = ReplacementRule(pattern2657, replacement2657)
    pattern2658 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1383)
    def replacement2658(m, f, b, d, a, n, x, e):
        rubi.append(2658)
        return Dist(b**(S(-2)), Int((d*sin(e + f*x))**n*(a - b*sin(e + f*x))*(a + b*sin(e + f*x))**(m + S(1)), x), x)
    rule2658 = ReplacementRule(pattern2658, replacement2658)
    pattern2659 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1383)
    def replacement2659(m, f, b, d, a, n, x, e):
        rubi.append(2659)
        return Dist(b**(S(-2)), Int((d*cos(e + f*x))**n*(a - b*cos(e + f*x))*(a + b*cos(e + f*x))**(m + S(1)), x), x)
    rule2659 = ReplacementRule(pattern2659, replacement2659)
    pattern2660 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1265, cons84)
    def replacement2660(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2660)
        return Dist((a/g)**(S(2)*m), Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**(S(2)*m + p)*(a - b*sin(e + f*x))**(-m), x), x)
    rule2660 = ReplacementRule(pattern2660, replacement2660)
    pattern2661 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1265, cons84)
    def replacement2661(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2661)
        return Dist((a/g)**(S(2)*m), Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**(S(2)*m + p)*(a - b*cos(e + f*x))**(-m), x), x)
    rule2661 = ReplacementRule(pattern2661, replacement2661)
    pattern2662 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons1265, cons17, cons13, cons1384)
    def replacement2662(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2662)
        return Dist((a/g)**(S(2)*m), Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**(S(2)*m + p)*(a - b*sin(e + f*x))**(-m), x), x)
    rule2662 = ReplacementRule(pattern2662, replacement2662)
    pattern2663 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons1265, cons17, cons13, cons1384)
    def replacement2663(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2663)
        return Dist((a/g)**(S(2)*m), Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**(S(2)*m + p)*(a - b*cos(e + f*x))**(-m), x), x)
    rule2663 = ReplacementRule(pattern2663, replacement2663)
    pattern2664 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons31, cons1385, cons1281)
    def replacement2664(p, m, f, b, g, a, x, e):
        rubi.append(2664)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + p + S(1))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**(m + S(1))*(a*m - b*(S(2)*m + p + S(1))*sin(e + f*x)), x), x) + Simp(b*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2664 = ReplacementRule(pattern2664, replacement2664)
    pattern2665 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1265, cons31, cons1385, cons1281)
    def replacement2665(p, m, f, b, g, a, x, e):
        rubi.append(2665)
        return -Dist(S(1)/(a**S(2)*(S(2)*m + p + S(1))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**(m + S(1))*(a*m - b*(S(2)*m + p + S(1))*cos(e + f*x)), x), x) - Simp(b*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(a*f*g*(S(2)*m + p + S(1))), x)
    rule2665 = ReplacementRule(pattern2665, replacement2665)
    pattern2666 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1386)
    def replacement2666(p, m, f, b, g, a, x, e):
        rubi.append(2666)
        return Dist(S(1)/(b*(m + p + S(2))), Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**m*(-a*(p + S(1))*sin(e + f*x) + b*(m + S(1))), x), x) - Simp((g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**(m + S(1))/(b*f*g*(m + p + S(2))), x)
    rule2666 = ReplacementRule(pattern2666, replacement2666)
    pattern2667 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons48, cons125, cons208, cons21, cons5, cons1265, cons1386)
    def replacement2667(p, m, f, b, g, a, x, e):
        rubi.append(2667)
        return Dist(S(1)/(b*(m + p + S(2))), Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**m*(-a*(p + S(1))*cos(e + f*x) + b*(m + S(1))), x), x) + Simp((g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**(m + S(1))/(b*f*g*(m + p + S(2))), x)
    rule2667 = ReplacementRule(pattern2667, replacement2667)
    pattern2668 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1170)
    def replacement2668(m, f, b, d, a, n, x, e):
        rubi.append(2668)
        return Dist(b**(S(-2)), Int((d*sin(e + f*x))**n*(a - b*sin(e + f*x))*(a + b*sin(e + f*x))**(m + S(1)), x), x)
    rule2668 = ReplacementRule(pattern2668, replacement2668)
    pattern2669 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1170)
    def replacement2669(m, f, b, d, a, n, x, e):
        rubi.append(2669)
        return Dist(b**(S(-2)), Int((d*cos(e + f*x))**n*(a - b*cos(e + f*x))*(a + b*cos(e + f*x))**(m + S(1)), x), x)
    rule2669 = ReplacementRule(pattern2669, replacement2669)
    pattern2670 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons31, cons94)
    def replacement2670(m, f, b, d, a, n, x, e):
        rubi.append(2670)
        return Dist(a**(S(-2)), Int((d*sin(e + f*x))**n*(a + b*sin(e + f*x))**(m + S(2))*(sin(e + f*x)**S(2) + S(1)), x), x) + Dist(-S(2)/(a*b*d), Int((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(2)), x), x)
    rule2670 = ReplacementRule(pattern2670, replacement2670)
    pattern2671 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons31, cons94)
    def replacement2671(m, f, b, d, a, n, x, e):
        rubi.append(2671)
        return Dist(a**(S(-2)), Int((d*cos(e + f*x))**n*(a + b*cos(e + f*x))**(m + S(2))*(cos(e + f*x)**S(2) + S(1)), x), x) + Dist(-S(2)/(a*b*d), Int((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(2)), x), x)
    rule2671 = ReplacementRule(pattern2671, replacement2671)
    pattern2672 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons143)
    def replacement2672(m, f, b, d, a, n, x, e):
        rubi.append(2672)
        return Dist(d**(S(-4)), Int((d*sin(e + f*x))**(n + S(4))*(a + b*sin(e + f*x))**m, x), x) + Int((d*sin(e + f*x))**n*(a + b*sin(e + f*x))**m*(-S(2)*sin(e + f*x)**S(2) + S(1)), x)
    rule2672 = ReplacementRule(pattern2672, replacement2672)
    pattern2673 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons143)
    def replacement2673(m, f, b, d, a, n, x, e):
        rubi.append(2673)
        return Dist(d**(S(-4)), Int((d*cos(e + f*x))**(n + S(4))*(a + b*cos(e + f*x))**m, x), x) + Int((d*cos(e + f*x))**n*(a + b*cos(e + f*x))**m*(-S(2)*cos(e + f*x)**S(2) + S(1)), x)
    rule2673 = ReplacementRule(pattern2673, replacement2673)
    pattern2674 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons1306, cons17)
    def replacement2674(p, m, f, b, d, a, n, x, e):
        rubi.append(2674)
        return Dist(a**m*cos(e + f*x)/(f*sqrt(-sin(e + f*x) + S(1))*sqrt(sin(e + f*x) + S(1))), Subst(Int((d*x)**n*(S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2), x), x, sin(e + f*x)), x)
    rule2674 = ReplacementRule(pattern2674, replacement2674)
    pattern2675 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1265, cons1306, cons17)
    def replacement2675(p, m, f, b, d, a, n, x, e):
        rubi.append(2675)
        return -Dist(a**m*sin(e + f*x)/(f*sqrt(-cos(e + f*x) + S(1))*sqrt(cos(e + f*x) + S(1))), Subst(Int((d*x)**n*(S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2), x), x, cos(e + f*x)), x)
    rule2675 = ReplacementRule(pattern2675, replacement2675)
    pattern2676 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1306, cons18)
    def replacement2676(p, m, f, b, d, a, n, x, e):
        rubi.append(2676)
        return Dist(a**(-p + S(2))*cos(e + f*x)/(f*sqrt(a - b*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), Subst(Int((d*x)**n*(a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2), x), x, sin(e + f*x)), x)
    rule2676 = ReplacementRule(pattern2676, replacement2676)
    pattern2677 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1265, cons1306, cons18)
    def replacement2677(p, m, f, b, d, a, n, x, e):
        rubi.append(2677)
        return -Dist(a**(-p + S(2))*sin(e + f*x)/(f*sqrt(a - b*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), Subst(Int((d*x)**n*(a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2), x), x, cos(e + f*x)), x)
    rule2677 = ReplacementRule(pattern2677, replacement2677)
    pattern2678 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1265, cons62, cons1387)
    def replacement2678(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2678)
        return Int(ExpandTrig((g*cos(e + f*x))**p, (d*sin(e + f*x))**n*(a + b*sin(e + f*x))**m, x), x)
    rule2678 = ReplacementRule(pattern2678, replacement2678)
    pattern2679 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1265, cons62, cons1387)
    def replacement2679(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2679)
        return Int(ExpandTrig((g*sin(e + f*x))**p, (d*cos(e + f*x))**n*(a + b*cos(e + f*x))**m, x), x)
    rule2679 = ReplacementRule(pattern2679, replacement2679)
    pattern2680 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons5, cons1265, cons17)
    def replacement2680(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2680)
        return Dist(a**m*g*(g*cos(e + f*x))**(p + S(-1))*(-sin(e + f*x) + S(1))**(-p/S(2) + S(1)/2)*(sin(e + f*x) + S(1))**(-p/S(2) + S(1)/2)/f, Subst(Int((d*x)**n*(S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2), x), x, sin(e + f*x)), x)
    rule2680 = ReplacementRule(pattern2680, replacement2680)
    pattern2681 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons4, cons5, cons1265, cons17)
    def replacement2681(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2681)
        return -Dist(a**m*g*(g*sin(e + f*x))**(p + S(-1))*(-cos(e + f*x) + S(1))**(-p/S(2) + S(1)/2)*(cos(e + f*x) + S(1))**(-p/S(2) + S(1)/2)/f, Subst(Int((d*x)**n*(S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2), x), x, cos(e + f*x)), x)
    rule2681 = ReplacementRule(pattern2681, replacement2681)
    pattern2682 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons5, cons1265, cons18)
    def replacement2682(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2682)
        return Dist(g*(g*cos(e + f*x))**(p + S(-1))*(a - b*sin(e + f*x))**(-p/S(2) + S(1)/2)*(a + b*sin(e + f*x))**(-p/S(2) + S(1)/2)/f, Subst(Int((d*x)**n*(a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2), x), x, sin(e + f*x)), x)
    rule2682 = ReplacementRule(pattern2682, replacement2682)
    pattern2683 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons5, cons1265, cons18)
    def replacement2683(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2683)
        return -Dist(g*(g*sin(e + f*x))**(p + S(-1))*(a - b*cos(e + f*x))**(-p/S(2) + S(1)/2)*(a + b*cos(e + f*x))**(-p/S(2) + S(1)/2)/f, Subst(Int((d*x)**n*(a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2), x), x, cos(e + f*x)), x)
    rule2683 = ReplacementRule(pattern2683, replacement2683)
    pattern2684 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons31, cons94, cons1388)
    def replacement2684(p, m, f, b, g, d, a, x, e):
        rubi.append(2684)
        return Dist(g**S(2)*(S(2)*m + S(3))/(S(2)*a*(m + S(1))), Int((g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**(m + S(1))/sqrt(d*sin(e + f*x)), x), x) - Simp(g*sqrt(d*sin(e + f*x))*(g*cos(e + f*x))**(p + S(-1))*(a + b*sin(e + f*x))**(m + S(1))/(a*d*f*(m + S(1))), x)
    rule2684 = ReplacementRule(pattern2684, replacement2684)
    pattern2685 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons31, cons94, cons1388)
    def replacement2685(p, m, f, b, g, d, a, x, e):
        rubi.append(2685)
        return Dist(g**S(2)*(S(2)*m + S(3))/(S(2)*a*(m + S(1))), Int((g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**(m + S(1))/sqrt(d*cos(e + f*x)), x), x) + Simp(g*sqrt(d*cos(e + f*x))*(g*sin(e + f*x))**(p + S(-1))*(a + b*cos(e + f*x))**(m + S(1))/(a*d*f*(m + S(1))), x)
    rule2685 = ReplacementRule(pattern2685, replacement2685)
    pattern2686 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons31, cons168, cons1389)
    def replacement2686(p, m, f, b, g, d, a, x, e):
        rubi.append(2686)
        return Dist(S(2)*a*m/(g**S(2)*(S(2)*m + S(1))), Int((g*cos(e + f*x))**(p + S(2))*(a + b*sin(e + f*x))**(m + S(-1))/sqrt(d*sin(e + f*x)), x), x) + Simp(S(2)*sqrt(d*sin(e + f*x))*(g*cos(e + f*x))**(p + S(1))*(a + b*sin(e + f*x))**m/(d*f*g*(S(2)*m + S(1))), x)
    rule2686 = ReplacementRule(pattern2686, replacement2686)
    pattern2687 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons1267, cons31, cons168, cons1389)
    def replacement2687(p, m, f, b, g, d, a, x, e):
        rubi.append(2687)
        return Dist(S(2)*a*m/(g**S(2)*(S(2)*m + S(1))), Int((g*sin(e + f*x))**(p + S(2))*(a + b*cos(e + f*x))**(m + S(-1))/sqrt(d*cos(e + f*x)), x), x) + Simp(-S(2)*sqrt(d*cos(e + f*x))*(g*sin(e + f*x))**(p + S(1))*(a + b*cos(e + f*x))**m/(d*f*g*(S(2)*m + S(1))), x)
    rule2687 = ReplacementRule(pattern2687, replacement2687)
    pattern2688 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1267, cons1390)
    def replacement2688(m, f, b, d, a, n, x, e):
        rubi.append(2688)
        return Int((d*sin(e + f*x))**n*(a + b*sin(e + f*x))**m*(-sin(e + f*x)**S(2) + S(1)), x)
    rule2688 = ReplacementRule(pattern2688, replacement2688)
    pattern2689 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1267, cons1390)
    def replacement2689(m, f, b, d, a, n, x, e):
        rubi.append(2689)
        return Int((d*cos(e + f*x))**n*(a + b*cos(e + f*x))**m*(-cos(e + f*x)**S(2) + S(1)), x)
    rule2689 = ReplacementRule(pattern2689, replacement2689)
    pattern2690 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1170, cons94, cons89)
    def replacement2690(m, f, b, d, a, n, x, e):
        rubi.append(2690)
        return Dist(S(1)/(a**S(2)*b*d*(m + S(1))*(n + S(1))), Int((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(1))*Simp(a**S(2)*(n + S(1))*(n + S(2)) + a*b*(m + S(1))*sin(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(3)) - (a**S(2)*(n + S(1))*(n + S(3)) - b**S(2)*(m + n + S(2))*(m + n + S(4)))*sin(e + f*x)**S(2), x), x), x) + Simp((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(a*d*f*(n + S(1))), x) - Simp((d*sin(e + f*x))**(n + S(2))*(a + b*sin(e + f*x))**(m + S(1))*(a**S(2)*(n + S(1)) - b**S(2)*(m + n + S(2)))*cos(e + f*x)/(a**S(2)*b*d**S(2)*f*(m + S(1))*(n + S(1))), x)
    rule2690 = ReplacementRule(pattern2690, replacement2690)
    pattern2691 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1170, cons94, cons89)
    def replacement2691(m, f, b, d, a, n, x, e):
        rubi.append(2691)
        return Dist(S(1)/(a**S(2)*b*d*(m + S(1))*(n + S(1))), Int((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(1))*Simp(a**S(2)*(n + S(1))*(n + S(2)) + a*b*(m + S(1))*cos(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(3)) - (a**S(2)*(n + S(1))*(n + S(3)) - b**S(2)*(m + n + S(2))*(m + n + S(4)))*cos(e + f*x)**S(2), x), x), x) - Simp((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(a*d*f*(n + S(1))), x) + Simp((d*cos(e + f*x))**(n + S(2))*(a + b*cos(e + f*x))**(m + S(1))*(a**S(2)*(n + S(1)) - b**S(2)*(m + n + S(2)))*sin(e + f*x)/(a**S(2)*b*d**S(2)*f*(m + S(1))*(n + S(1))), x)
    rule2691 = ReplacementRule(pattern2691, replacement2691)
    pattern2692 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1267, cons1170, cons94, cons1391, cons1392)
    def replacement2692(m, f, b, d, a, n, x, e):
        rubi.append(2692)
        return -Dist(S(1)/(a**S(2)*b**S(2)*(m + S(1))*(m + S(2))), Int((d*sin(e + f*x))**n*(a + b*sin(e + f*x))**(m + S(2))*Simp(a**S(2)*(n + S(1))*(n + S(3)) + a*b*(m + S(2))*sin(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(3)) - (a**S(2)*(n + S(2))*(n + S(3)) - b**S(2)*(m + n + S(2))*(m + n + S(4)))*sin(e + f*x)**S(2), x), x), x) + Simp((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(1))*(a**S(2) - b**S(2))*cos(e + f*x)/(a*b**S(2)*d*f*(m + S(1))), x) + Simp((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(2))*(a**S(2)*(-m + n + S(1)) - b**S(2)*(m + n + S(2)))*cos(e + f*x)/(a**S(2)*b**S(2)*d*f*(m + S(1))*(m + S(2))), x)
    rule2692 = ReplacementRule(pattern2692, replacement2692)
    pattern2693 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1267, cons1170, cons94, cons1391, cons1392)
    def replacement2693(m, f, b, d, a, n, x, e):
        rubi.append(2693)
        return -Dist(S(1)/(a**S(2)*b**S(2)*(m + S(1))*(m + S(2))), Int((d*cos(e + f*x))**n*(a + b*cos(e + f*x))**(m + S(2))*Simp(a**S(2)*(n + S(1))*(n + S(3)) + a*b*(m + S(2))*cos(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(3)) - (a**S(2)*(n + S(2))*(n + S(3)) - b**S(2)*(m + n + S(2))*(m + n + S(4)))*cos(e + f*x)**S(2), x), x), x) - Simp((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(1))*(a**S(2) - b**S(2))*sin(e + f*x)/(a*b**S(2)*d*f*(m + S(1))), x) - Simp((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(2))*(a**S(2)*(-m + n + S(1)) - b**S(2)*(m + n + S(2)))*sin(e + f*x)/(a**S(2)*b**S(2)*d*f*(m + S(1))*(m + S(2))), x)
    rule2693 = ReplacementRule(pattern2693, replacement2693)
    pattern2694 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1267, cons1170, cons94, cons1391, cons1393)
    def replacement2694(m, f, b, d, a, n, x, e):
        rubi.append(2694)
        return -Dist(S(1)/(a*b**S(2)*(m + S(1))*(m + n + S(4))), Int((d*sin(e + f*x))**n*(a + b*sin(e + f*x))**(m + S(1))*Simp(a**S(2)*(n + S(1))*(n + S(3)) + a*b*(m + S(1))*sin(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(4)) - (a**S(2)*(n + S(2))*(n + S(3)) - b**S(2)*(m + n + S(3))*(m + n + S(4)))*sin(e + f*x)**S(2), x), x), x) - Simp((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(2))*cos(e + f*x)/(b**S(2)*d*f*(m + n + S(4))), x) + Simp((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(1))*(a**S(2) - b**S(2))*cos(e + f*x)/(a*b**S(2)*d*f*(m + S(1))), x)
    rule2694 = ReplacementRule(pattern2694, replacement2694)
    pattern2695 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons4, cons1267, cons1170, cons94, cons1391, cons1393)
    def replacement2695(m, f, b, d, a, n, x, e):
        rubi.append(2695)
        return -Dist(S(1)/(a*b**S(2)*(m + S(1))*(m + n + S(4))), Int((d*cos(e + f*x))**n*(a + b*cos(e + f*x))**(m + S(1))*Simp(a**S(2)*(n + S(1))*(n + S(3)) + a*b*(m + S(1))*cos(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(4)) - (a**S(2)*(n + S(2))*(n + S(3)) - b**S(2)*(m + n + S(3))*(m + n + S(4)))*cos(e + f*x)**S(2), x), x), x) + Simp((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(2))*sin(e + f*x)/(b**S(2)*d*f*(m + n + S(4))), x) - Simp((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(1))*(a**S(2) - b**S(2))*sin(e + f*x)/(a*b**S(2)*d*f*(m + S(1))), x)
    rule2695 = ReplacementRule(pattern2695, replacement2695)
    pattern2696 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1267, cons1390, cons1305, cons87, cons89, cons1394)
    def replacement2696(m, f, b, d, a, n, x, e):
        rubi.append(2696)
        return -Dist(S(1)/(a**S(2)*d**S(2)*(n + S(1))*(n + S(2))), Int((d*sin(e + f*x))**(n + S(2))*(a + b*sin(e + f*x))**m*Simp(a**S(2)*n*(n + S(2)) + a*b*m*sin(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(3)) - (a**S(2)*(n + S(1))*(n + S(2)) - b**S(2)*(m + n + S(2))*(m + n + S(4)))*sin(e + f*x)**S(2), x), x), x) + Simp((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(a*d*f*(n + S(1))), x) - Simp(b*(d*sin(e + f*x))**(n + S(2))*(a + b*sin(e + f*x))**(m + S(1))*(m + n + S(2))*cos(e + f*x)/(a**S(2)*d**S(2)*f*(n + S(1))*(n + S(2))), x)
    rule2696 = ReplacementRule(pattern2696, replacement2696)
    pattern2697 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1267, cons1390, cons1305, cons87, cons89, cons1394)
    def replacement2697(m, f, b, d, a, n, x, e):
        rubi.append(2697)
        return -Dist(S(1)/(a**S(2)*d**S(2)*(n + S(1))*(n + S(2))), Int((d*cos(e + f*x))**(n + S(2))*(a + b*cos(e + f*x))**m*Simp(a**S(2)*n*(n + S(2)) + a*b*m*cos(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(3)) - (a**S(2)*(n + S(1))*(n + S(2)) - b**S(2)*(m + n + S(2))*(m + n + S(4)))*cos(e + f*x)**S(2), x), x), x) - Simp((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(a*d*f*(n + S(1))), x) + Simp(b*(d*cos(e + f*x))**(n + S(2))*(a + b*cos(e + f*x))**(m + S(1))*(m + n + S(2))*sin(e + f*x)/(a**S(2)*d**S(2)*f*(n + S(1))*(n + S(2))), x)
    rule2697 = ReplacementRule(pattern2697, replacement2697)
    pattern2698 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1267, cons1390, cons1305, cons87, cons89, cons1393)
    def replacement2698(m, f, b, d, a, n, x, e):
        rubi.append(2698)
        return Dist(S(1)/(a*b*d*(n + S(1))*(m + n + S(4))), Int((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**m*Simp(a**S(2)*(n + S(1))*(n + S(2)) + a*b*(m + S(3))*sin(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(4)) - (a**S(2)*(n + S(1))*(n + S(3)) - b**S(2)*(m + n + S(3))*(m + n + S(4)))*sin(e + f*x)**S(2), x), x), x) + Simp((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(a*d*f*(n + S(1))), x) - Simp((d*sin(e + f*x))**(n + S(2))*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*d**S(2)*f*(m + n + S(4))), x)
    rule2698 = ReplacementRule(pattern2698, replacement2698)
    pattern2699 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons1267, cons1390, cons1305, cons87, cons89, cons1393)
    def replacement2699(m, f, b, d, a, n, x, e):
        rubi.append(2699)
        return Dist(S(1)/(a*b*d*(n + S(1))*(m + n + S(4))), Int((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**m*Simp(a**S(2)*(n + S(1))*(n + S(2)) + a*b*(m + S(3))*cos(e + f*x) - b**S(2)*(m + n + S(2))*(m + n + S(4)) - (a**S(2)*(n + S(1))*(n + S(3)) - b**S(2)*(m + n + S(3))*(m + n + S(4)))*cos(e + f*x)**S(2), x), x), x) - Simp((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(a*d*f*(n + S(1))), x) + Simp((d*cos(e + f*x))**(n + S(2))*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*d**S(2)*f*(m + n + S(4))), x)
    rule2699 = ReplacementRule(pattern2699, replacement2699)
    pattern2700 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1267, cons1390, cons1305, cons346, cons213, cons1393)
    def replacement2700(m, f, b, d, a, n, x, e):
        rubi.append(2700)
        return -Dist(S(1)/(b**S(2)*(m + n + S(3))*(m + n + S(4))), Int((d*sin(e + f*x))**n*(a + b*sin(e + f*x))**m*Simp(a**S(2)*(n + S(1))*(n + S(3)) + a*b*m*sin(e + f*x) - b**S(2)*(m + n + S(3))*(m + n + S(4)) - (a**S(2)*(n + S(2))*(n + S(3)) - b**S(2)*(m + n + S(3))*(m + n + S(5)))*sin(e + f*x)**S(2), x), x), x) - Simp((d*sin(e + f*x))**(n + S(2))*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*d**S(2)*f*(m + n + S(4))), x) + Simp(a*(d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(1))*(n + S(3))*cos(e + f*x)/(b**S(2)*d*f*(m + n + S(3))*(m + n + S(4))), x)
    rule2700 = ReplacementRule(pattern2700, replacement2700)
    pattern2701 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(4), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1267, cons1390, cons1305, cons346, cons213, cons1393)
    def replacement2701(m, f, b, d, a, n, x, e):
        rubi.append(2701)
        return -Dist(S(1)/(b**S(2)*(m + n + S(3))*(m + n + S(4))), Int((d*cos(e + f*x))**n*(a + b*cos(e + f*x))**m*Simp(a**S(2)*(n + S(1))*(n + S(3)) + a*b*m*cos(e + f*x) - b**S(2)*(m + n + S(3))*(m + n + S(4)) - (a**S(2)*(n + S(2))*(n + S(3)) - b**S(2)*(m + n + S(3))*(m + n + S(5)))*cos(e + f*x)**S(2), x), x), x) + Simp((d*cos(e + f*x))**(n + S(2))*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*d**S(2)*f*(m + n + S(4))), x) - Simp(a*(d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(1))*(n + S(3))*sin(e + f*x)/(b**S(2)*d*f*(m + n + S(3))*(m + n + S(4))), x)
    rule2701 = ReplacementRule(pattern2701, replacement2701)
    pattern2702 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(6), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1267, cons1170, cons584, cons1395, cons1396, cons1397, cons143)
    def replacement2702(m, f, b, d, a, n, x, e):
        rubi.append(2702)
        return Dist(S(1)/(a**S(2)*b**S(2)*d**S(2)*(n + S(1))*(n + S(2))*(m + n + S(5))*(m + n + S(6))), Int((d*sin(e + f*x))**(n + S(2))*(a + b*sin(e + f*x))**m*Simp(a**S(4)*(n + S(1))*(n + S(2))*(n + S(3))*(n + S(5)) - a**S(2)*b**S(2)*(n + S(2))*(S(2)*n + S(1))*(m + n + S(5))*(m + n + S(6)) + a*b*m*(a**S(2)*(n + S(1))*(n + S(2)) - b**S(2)*(m + n + S(5))*(m + n + S(6)))*sin(e + f*x) + b**S(4)*(m + n + S(2))*(m + n + S(3))*(m + n + S(5))*(m + n + S(6)) - (a**S(4)*(n + S(1))*(n + S(2))*(n + S(4))*(n + S(5)) - a**S(2)*b**S(2)*(n + S(1))*(n + S(2))*(m + n + S(5))*(S(2)*m + S(2)*n + S(13)) + b**S(4)*(m + n + S(2))*(m + n + S(4))*(m + n + S(5))*(m + n + S(6)))*sin(e + f*x)**S(2), x), x), x) + Simp((d*sin(e + f*x))**(n + S(1))*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(a*d*f*(n + S(1))), x) + Simp((d*sin(e + f*x))**(n + S(4))*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*d**S(4)*f*(m + n + S(6))), x) - Simp(b*(d*sin(e + f*x))**(n + S(2))*(a + b*sin(e + f*x))**(m + S(1))*(m + n + S(2))*cos(e + f*x)/(a**S(2)*d**S(2)*f*(n + S(1))*(n + S(2))), x) - Simp(a*(d*sin(e + f*x))**(n + S(3))*(a + b*sin(e + f*x))**(m + S(1))*(n + S(5))*cos(e + f*x)/(b**S(2)*d**S(3)*f*(m + n + S(5))*(m + n + S(6))), x)
    rule2702 = ReplacementRule(pattern2702, replacement2702)
    pattern2703 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(6), x_), cons2, cons3, cons27, cons48, cons125, cons21, cons4, cons1267, cons1170, cons584, cons1395, cons1396, cons1397, cons143)
    def replacement2703(m, f, b, d, a, n, x, e):
        rubi.append(2703)
        return Dist(S(1)/(a**S(2)*b**S(2)*d**S(2)*(n + S(1))*(n + S(2))*(m + n + S(5))*(m + n + S(6))), Int((d*cos(e + f*x))**(n + S(2))*(a + b*cos(e + f*x))**m*Simp(a**S(4)*(n + S(1))*(n + S(2))*(n + S(3))*(n + S(5)) - a**S(2)*b**S(2)*(n + S(2))*(S(2)*n + S(1))*(m + n + S(5))*(m + n + S(6)) + a*b*m*(a**S(2)*(n + S(1))*(n + S(2)) - b**S(2)*(m + n + S(5))*(m + n + S(6)))*cos(e + f*x) + b**S(4)*(m + n + S(2))*(m + n + S(3))*(m + n + S(5))*(m + n + S(6)) - (a**S(4)*(n + S(1))*(n + S(2))*(n + S(4))*(n + S(5)) - a**S(2)*b**S(2)*(n + S(1))*(n + S(2))*(m + n + S(5))*(S(2)*m + S(2)*n + S(13)) + b**S(4)*(m + n + S(2))*(m + n + S(4))*(m + n + S(5))*(m + n + S(6)))*cos(e + f*x)**S(2), x), x), x) - Simp((d*cos(e + f*x))**(n + S(1))*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(a*d*f*(n + S(1))), x) - Simp((d*cos(e + f*x))**(n + S(4))*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*d**S(4)*f*(m + n + S(6))), x) + Simp(b*(d*cos(e + f*x))**(n + S(2))*(a + b*cos(e + f*x))**(m + S(1))*(m + n + S(2))*sin(e + f*x)/(a**S(2)*d**S(2)*f*(n + S(1))*(n + S(2))), x) + Simp(a*(d*cos(e + f*x))**(n + S(3))*(a + b*cos(e + f*x))**(m + S(1))*(n + S(5))*sin(e + f*x)/(b**S(2)*d**S(3)*f*(m + n + S(5))*(m + n + S(6))), x)
    rule2703 = ReplacementRule(pattern2703, replacement2703)
    pattern2704 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1398, cons1399)
    def replacement2704(p, m, f, b, d, a, n, x, e):
        rubi.append(2704)
        return Int(ExpandTrig((d*sin(e + f*x))**n*(a + b*sin(e + f*x))**m*(-sin(e + f*x)**S(2) + S(1))**(p/S(2)), x), x)
    rule2704 = ReplacementRule(pattern2704, replacement2704)
    pattern2705 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons27, cons48, cons125, cons1267, cons1398, cons1399)
    def replacement2705(p, m, f, b, d, a, n, x, e):
        rubi.append(2705)
        return Int(ExpandTrig((d*cos(e + f*x))**n*(a + b*cos(e + f*x))**m*(-cos(e + f*x)**S(2) + S(1))**(p/S(2)), x), x)
    rule2705 = ReplacementRule(pattern2705, replacement2705)
    pattern2706 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**n_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons85, cons1400)
    def replacement2706(p, f, b, g, a, n, x, e):
        rubi.append(2706)
        return Int(ExpandTrig((g*cos(e + f*x))**p, sin(e + f*x)**n/(a + b*sin(e + f*x)), x), x)
    rule2706 = ReplacementRule(pattern2706, replacement2706)
    pattern2707 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**n_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons48, cons125, cons208, cons5, cons1267, cons85, cons1400)
    def replacement2707(p, f, b, g, a, n, x, e):
        rubi.append(2707)
        return Int(ExpandTrig((g*sin(e + f*x))**p, cos(e + f*x)**n/(a + b*cos(e + f*x)), x), x)
    rule2707 = ReplacementRule(pattern2707, replacement2707)
    pattern2708 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons146, cons1402)
    def replacement2708(p, f, b, g, d, a, n, x, e):
        rubi.append(2708)
        return Dist(g**S(2)/a, Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**(p + S(-2)), x), x) - Dist(b*g**S(2)/(a**S(2)*d), Int((d*sin(e + f*x))**(n + S(1))*(g*cos(e + f*x))**(p + S(-2)), x), x) - Dist(g**S(2)*(a**S(2) - b**S(2))/(a**S(2)*d**S(2)), Int((d*sin(e + f*x))**(n + S(2))*(g*cos(e + f*x))**(p + S(-2))/(a + b*sin(e + f*x)), x), x)
    rule2708 = ReplacementRule(pattern2708, replacement2708)
    pattern2709 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons146, cons1402)
    def replacement2709(p, f, b, g, d, a, n, x, e):
        rubi.append(2709)
        return Dist(g**S(2)/a, Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**(p + S(-2)), x), x) - Dist(b*g**S(2)/(a**S(2)*d), Int((d*cos(e + f*x))**(n + S(1))*(g*sin(e + f*x))**(p + S(-2)), x), x) - Dist(g**S(2)*(a**S(2) - b**S(2))/(a**S(2)*d**S(2)), Int((d*cos(e + f*x))**(n + S(2))*(g*sin(e + f*x))**(p + S(-2))/(a + b*cos(e + f*x)), x), x)
    rule2709 = ReplacementRule(pattern2709, replacement2709)
    pattern2710 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons146, cons1403)
    def replacement2710(p, f, b, g, d, a, n, x, e):
        rubi.append(2710)
        return Dist(g**S(2)/(a*b), Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**(p + S(-2))*(-a*sin(e + f*x) + b), x), x) + Dist(g**S(2)*(a**S(2) - b**S(2))/(a*b*d), Int((d*sin(e + f*x))**(n + S(1))*(g*cos(e + f*x))**(p + S(-2))/(a + b*sin(e + f*x)), x), x)
    rule2710 = ReplacementRule(pattern2710, replacement2710)
    pattern2711 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons146, cons1403)
    def replacement2711(p, f, b, g, d, a, n, x, e):
        rubi.append(2711)
        return Dist(g**S(2)/(a*b), Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**(p + S(-2))*(-a*cos(e + f*x) + b), x), x) + Dist(g**S(2)*(a**S(2) - b**S(2))/(a*b*d), Int((d*cos(e + f*x))**(n + S(1))*(g*sin(e + f*x))**(p + S(-2))/(a + b*cos(e + f*x)), x), x)
    rule2711 = ReplacementRule(pattern2711, replacement2711)
    pattern2712 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons146)
    def replacement2712(p, f, b, g, d, a, n, x, e):
        rubi.append(2712)
        return Dist(g**S(2)/b**S(2), Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**(p + S(-2))*(a - b*sin(e + f*x)), x), x) - Dist(g**S(2)*(a**S(2) - b**S(2))/b**S(2), Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**(p + S(-2))/(a + b*sin(e + f*x)), x), x)
    rule2712 = ReplacementRule(pattern2712, replacement2712)
    pattern2713 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons146)
    def replacement2713(p, f, b, g, d, a, n, x, e):
        rubi.append(2713)
        return Dist(g**S(2)/b**S(2), Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**(p + S(-2))*(a - b*cos(e + f*x)), x), x) - Dist(g**S(2)*(a**S(2) - b**S(2))/b**S(2), Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**(p + S(-2))/(a + b*cos(e + f*x)), x), x)
    rule2713 = ReplacementRule(pattern2713, replacement2713)
    pattern2714 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons137, cons165)
    def replacement2714(p, f, b, g, d, a, n, x, e):
        rubi.append(2714)
        return Dist(a*d**S(2)/(a**S(2) - b**S(2)), Int((d*sin(e + f*x))**(n + S(-2))*(g*cos(e + f*x))**p, x), x) - Dist(b*d/(a**S(2) - b**S(2)), Int((d*sin(e + f*x))**(n + S(-1))*(g*cos(e + f*x))**p, x), x) - Dist(a**S(2)*d**S(2)/(g**S(2)*(a**S(2) - b**S(2))), Int((d*sin(e + f*x))**(n + S(-2))*(g*cos(e + f*x))**(p + S(2))/(a + b*sin(e + f*x)), x), x)
    rule2714 = ReplacementRule(pattern2714, replacement2714)
    pattern2715 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons137, cons165)
    def replacement2715(p, f, b, g, d, a, n, x, e):
        rubi.append(2715)
        return Dist(a*d**S(2)/(a**S(2) - b**S(2)), Int((d*cos(e + f*x))**(n + S(-2))*(g*sin(e + f*x))**p, x), x) - Dist(b*d/(a**S(2) - b**S(2)), Int((d*cos(e + f*x))**(n + S(-1))*(g*sin(e + f*x))**p, x), x) - Dist(a**S(2)*d**S(2)/(g**S(2)*(a**S(2) - b**S(2))), Int((d*cos(e + f*x))**(n + S(-2))*(g*sin(e + f*x))**(p + S(2))/(a + b*cos(e + f*x)), x), x)
    rule2715 = ReplacementRule(pattern2715, replacement2715)
    pattern2716 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons137, cons88)
    def replacement2716(p, f, b, g, d, a, n, x, e):
        rubi.append(2716)
        return -Dist(d/(a**S(2) - b**S(2)), Int((d*sin(e + f*x))**(n + S(-1))*(g*cos(e + f*x))**p*(-a*sin(e + f*x) + b), x), x) + Dist(a*b*d/(g**S(2)*(a**S(2) - b**S(2))), Int((d*sin(e + f*x))**(n + S(-1))*(g*cos(e + f*x))**(p + S(2))/(a + b*sin(e + f*x)), x), x)
    rule2716 = ReplacementRule(pattern2716, replacement2716)
    pattern2717 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons137, cons88)
    def replacement2717(p, f, b, g, d, a, n, x, e):
        rubi.append(2717)
        return -Dist(d/(a**S(2) - b**S(2)), Int((d*cos(e + f*x))**(n + S(-1))*(g*sin(e + f*x))**p*(-a*cos(e + f*x) + b), x), x) + Dist(a*b*d/(g**S(2)*(a**S(2) - b**S(2))), Int((d*cos(e + f*x))**(n + S(-1))*(g*sin(e + f*x))**(p + S(2))/(a + b*cos(e + f*x)), x), x)
    rule2717 = ReplacementRule(pattern2717, replacement2717)
    pattern2718 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons137)
    def replacement2718(p, f, b, g, d, a, n, x, e):
        rubi.append(2718)
        return -Dist(b**S(2)/(g**S(2)*(a**S(2) - b**S(2))), Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**(p + S(2))/(a + b*sin(e + f*x)), x), x) + Dist(S(1)/(a**S(2) - b**S(2)), Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**p*(a - b*sin(e + f*x)), x), x)
    rule2718 = ReplacementRule(pattern2718, replacement2718)
    pattern2719 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons137)
    def replacement2719(p, f, b, g, d, a, n, x, e):
        rubi.append(2719)
        return -Dist(b**S(2)/(g**S(2)*(a**S(2) - b**S(2))), Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**(p + S(2))/(a + b*cos(e + f*x)), x), x) + Dist(S(1)/(a**S(2) - b**S(2)), Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**p*(a - b*cos(e + f*x)), x), x)
    rule2719 = ReplacementRule(pattern2719, replacement2719)
    pattern2720 = Pattern(Integral(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    def replacement2720(f, b, g, a, x, e):
        rubi.append(2720)
        return Dist(-S(4)*sqrt(S(2))*g/f, Subst(Int(x**S(2)/(sqrt(S(1) - x**S(4)/g**S(2))*(g**S(2)*(a + b) + x**S(4)*(a - b))), x), x, sqrt(g*cos(e + f*x))/sqrt(sin(e + f*x) + S(1))), x)
    rule2720 = ReplacementRule(pattern2720, replacement2720)
    pattern2721 = Pattern(Integral(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons208, cons1267)
    def replacement2721(f, b, g, a, x, e):
        rubi.append(2721)
        return Dist(S(4)*sqrt(S(2))*g/f, Subst(Int(x**S(2)/(sqrt(S(1) - x**S(4)/g**S(2))*(g**S(2)*(a + b) + x**S(4)*(a - b))), x), x, sqrt(g*sin(e + f*x))/sqrt(cos(e + f*x) + S(1))), x)
    rule2721 = ReplacementRule(pattern2721, replacement2721)
    pattern2722 = Pattern(Integral(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(d_*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267)
    def replacement2722(f, b, g, d, a, x, e):
        rubi.append(2722)
        return Dist(sqrt(sin(e + f*x))/sqrt(d*sin(e + f*x)), Int(sqrt(g*cos(e + f*x))/((a + b*sin(e + f*x))*sqrt(sin(e + f*x))), x), x)
    rule2722 = ReplacementRule(pattern2722, replacement2722)
    pattern2723 = Pattern(Integral(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(d_*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267)
    def replacement2723(f, b, g, d, a, x, e):
        rubi.append(2723)
        return Dist(sqrt(cos(e + f*x))/sqrt(d*cos(e + f*x)), Int(sqrt(g*sin(e + f*x))/((a + b*cos(e + f*x))*sqrt(cos(e + f*x))), x), x)
    rule2723 = ReplacementRule(pattern2723, replacement2723)
    def With2724(f, b, d, a, x, e):
        q = Rt(-a**S(2) + b**S(2), S(2))
        rubi.append(2724)
        return -Dist(S(2)*sqrt(S(2))*d*(b - q)/(f*q), Subst(Int(S(1)/(sqrt(S(1) - x**S(4)/d**S(2))*(a*x**S(2) + d*(b - q))), x), x, sqrt(d*sin(e + f*x))/sqrt(cos(e + f*x) + S(1))), x) + Dist(S(2)*sqrt(S(2))*d*(b + q)/(f*q), Subst(Int(S(1)/(sqrt(S(1) - x**S(4)/d**S(2))*(a*x**S(2) + d*(b + q))), x), x, sqrt(d*sin(e + f*x))/sqrt(cos(e + f*x) + S(1))), x)
    pattern2724 = Pattern(Integral(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    rule2724 = ReplacementRule(pattern2724, With2724)
    def With2725(f, b, d, a, x, e):
        q = Rt(-a**S(2) + b**S(2), S(2))
        rubi.append(2725)
        return Dist(S(2)*sqrt(S(2))*d*(b - q)/(f*q), Subst(Int(S(1)/(sqrt(S(1) - x**S(4)/d**S(2))*(a*x**S(2) + d*(b - q))), x), x, sqrt(d*cos(e + f*x))/sqrt(sin(e + f*x) + S(1))), x) + Dist(-S(2)*sqrt(S(2))*d*(b + q)/(f*q), Subst(Int(S(1)/(sqrt(S(1) - x**S(4)/d**S(2))*(a*x**S(2) + d*(b + q))), x), x, sqrt(d*cos(e + f*x))/sqrt(sin(e + f*x) + S(1))), x)
    pattern2725 = Pattern(Integral(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons1267)
    rule2725 = ReplacementRule(pattern2725, With2725)
    pattern2726 = Pattern(Integral(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267)
    def replacement2726(f, b, g, d, a, x, e):
        rubi.append(2726)
        return Dist(sqrt(cos(e + f*x))/sqrt(g*cos(e + f*x)), Int(sqrt(d*sin(e + f*x))/((a + b*sin(e + f*x))*sqrt(cos(e + f*x))), x), x)
    rule2726 = ReplacementRule(pattern2726, replacement2726)
    pattern2727 = Pattern(Integral(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267)
    def replacement2727(f, b, g, d, a, x, e):
        rubi.append(2727)
        return Dist(sqrt(sin(e + f*x))/sqrt(g*sin(e + f*x)), Int(sqrt(d*cos(e + f*x))/((a + b*cos(e + f*x))*sqrt(sin(e + f*x))), x), x)
    rule2727 = ReplacementRule(pattern2727, replacement2727)
    pattern2728 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons1404, cons88)
    def replacement2728(p, f, b, g, d, a, n, x, e):
        rubi.append(2728)
        return Dist(d/b, Int((d*sin(e + f*x))**(n + S(-1))*(g*cos(e + f*x))**p, x), x) - Dist(a*d/b, Int((d*sin(e + f*x))**(n + S(-1))*(g*cos(e + f*x))**p/(a + b*sin(e + f*x)), x), x)
    rule2728 = ReplacementRule(pattern2728, replacement2728)
    pattern2729 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons1404, cons88)
    def replacement2729(p, f, b, g, d, a, n, x, e):
        rubi.append(2729)
        return Dist(d/b, Int((d*cos(e + f*x))**(n + S(-1))*(g*sin(e + f*x))**p, x), x) - Dist(a*d/b, Int((d*cos(e + f*x))**(n + S(-1))*(g*sin(e + f*x))**p/(a + b*cos(e + f*x)), x), x)
    rule2729 = ReplacementRule(pattern2729, replacement2729)
    pattern2730 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons1404, cons463)
    def replacement2730(p, f, b, g, d, a, n, x, e):
        rubi.append(2730)
        return Dist(S(1)/a, Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**p, x), x) - Dist(b/(a*d), Int((d*sin(e + f*x))**(n + S(1))*(g*cos(e + f*x))**p/(a + b*sin(e + f*x)), x), x)
    rule2730 = ReplacementRule(pattern2730, replacement2730)
    pattern2731 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1401, cons1404, cons463)
    def replacement2731(p, f, b, g, d, a, n, x, e):
        rubi.append(2731)
        return Dist(S(1)/a, Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**p, x), x) - Dist(b/(a*d), Int((d*cos(e + f*x))**(n + S(1))*(g*sin(e + f*x))**p/(a + b*cos(e + f*x)), x), x)
    rule2731 = ReplacementRule(pattern2731, replacement2731)
    pattern2732 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1267, cons17, cons1405)
    def replacement2732(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2732)
        return Int(ExpandTrig((g*cos(e + f*x))**p, (d*sin(e + f*x))**n*(a + b*sin(e + f*x))**m, x), x)
    rule2732 = ReplacementRule(pattern2732, replacement2732)
    pattern2733 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons4, cons5, cons1267, cons17, cons1405)
    def replacement2733(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2733)
        return Int(ExpandTrig((g*sin(e + f*x))**p, (d*cos(e + f*x))**n*(a + b*cos(e + f*x))**m, x), x)
    rule2733 = ReplacementRule(pattern2733, replacement2733)
    pattern2734 = Pattern(Integral((WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1406, cons267, cons146, cons1407)
    def replacement2734(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2734)
        return Dist(g**S(2)/a, Int((d*sin(e + f*x))**n*(g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**(m + S(1)), x), x) - Dist(b*g**S(2)/(a**S(2)*d), Int((d*sin(e + f*x))**(n + S(1))*(g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**(m + S(1)), x), x) - Dist(g**S(2)*(a**S(2) - b**S(2))/(a**S(2)*d**S(2)), Int((d*sin(e + f*x))**(n + S(2))*(g*cos(e + f*x))**(p + S(-2))*(a + b*sin(e + f*x))**m, x), x)
    rule2734 = ReplacementRule(pattern2734, replacement2734)
    pattern2735 = Pattern(Integral((WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_, x_), cons2, cons3, cons27, cons48, cons125, cons208, cons1267, cons1406, cons267, cons146, cons1407)
    def replacement2735(p, m, f, b, g, d, a, n, x, e):
        rubi.append(2735)
        return Dist(g**S(2)/a, Int((d*cos(e + f*x))**n*(g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**(m + S(1)), x), x) - Dist(b*g**S(2)/(a**S(2)*d), Int((d*cos(e + f*x))**(n + S(1))*(g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**(m + S(1)), x), x) - Dist(g**S(2)*(a**S(2) - b**S(2))/(a**S(2)*d**S(2)), Int((d*cos(e + f*x))**(n + S(2))*(g*sin(e + f*x))**(p + S(-2))*(a + b*cos(e + f*x))**m, x), x)
    rule2735 = ReplacementRule(pattern2735, replacement2735)
    pattern2736 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons1265, cons1299, cons1380)
    def replacement2736(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2736)
        return Dist(a**(S(2)*m), Int((a - b*sin(e + f*x))**(-m)*(c + d*sin(e + f*x))**n, x), x)
    rule2736 = ReplacementRule(pattern2736, replacement2736)
    pattern2737 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons1265, cons1299, cons1380)
    def replacement2737(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2737)
        return Dist(a**(S(2)*m), Int((a - b*cos(e + f*x))**(-m)*(c + d*cos(e + f*x))**n, x), x)
    rule2737 = ReplacementRule(pattern2737, replacement2737)
    pattern2738 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons1265, cons17, cons13, cons1384)
    def replacement2738(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2738)
        return Dist((a/g)**(S(2)*m), Int((g*cos(e + f*x))**(S(2)*m + p)*(a - b*sin(e + f*x))**(-m)*(c + d*sin(e + f*x))**n, x), x)
    rule2738 = ReplacementRule(pattern2738, replacement2738)
    pattern2739 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons1265, cons17, cons13, cons1384)
    def replacement2739(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2739)
        return Dist((a/g)**(S(2)*m), Int((g*sin(e + f*x))**(S(2)*m + p)*(a - b*cos(e + f*x))**(-m)*(c + d*cos(e + f*x))**n, x), x)
    rule2739 = ReplacementRule(pattern2739, replacement2739)
    pattern2740 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1265, cons1170)
    def replacement2740(m, f, b, d, a, c, n, x, e):
        rubi.append(2740)
        return Dist(b**(S(-2)), Int((a - b*sin(e + f*x))*(a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n, x), x)
    rule2740 = ReplacementRule(pattern2740, replacement2740)
    pattern2741 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1265, cons1170)
    def replacement2741(m, f, b, d, a, c, n, x, e):
        rubi.append(2741)
        return Dist(b**(S(-2)), Int((a - b*cos(e + f*x))*(a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n, x), x)
    rule2741 = ReplacementRule(pattern2741, replacement2741)
    pattern2742 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons1265, cons1306, cons17)
    def replacement2742(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2742)
        return Dist(a**m*cos(e + f*x)/(f*sqrt(-sin(e + f*x) + S(1))*sqrt(sin(e + f*x) + S(1))), Subst(Int((S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2)*(c + d*x)**n, x), x, sin(e + f*x)), x)
    rule2742 = ReplacementRule(pattern2742, replacement2742)
    pattern2743 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons1265, cons1306, cons17)
    def replacement2743(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2743)
        return -Dist(a**m*sin(e + f*x)/(f*sqrt(-cos(e + f*x) + S(1))*sqrt(cos(e + f*x) + S(1))), Subst(Int((S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2)*(c + d*x)**n, x), x, cos(e + f*x)), x)
    rule2743 = ReplacementRule(pattern2743, replacement2743)
    pattern2744 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1265, cons1306, cons18)
    def replacement2744(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2744)
        return Dist(a**(-p + S(2))*cos(e + f*x)/(f*sqrt(a - b*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), Subst(Int((a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2)*(c + d*x)**n, x), x, sin(e + f*x)), x)
    rule2744 = ReplacementRule(pattern2744, replacement2744)
    pattern2745 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1265, cons1306, cons18)
    def replacement2745(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2745)
        return -Dist(a**(-p + S(2))*sin(e + f*x)/(f*sqrt(a - b*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), Subst(Int((a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2)*(c + d*x)**n, x), x, cos(e + f*x)), x)
    rule2745 = ReplacementRule(pattern2745, replacement2745)
    pattern2746 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons1265, cons62, cons1387)
    def replacement2746(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2746)
        return Int(ExpandTrig((g*cos(e + f*x))**p, (a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x), x)
    rule2746 = ReplacementRule(pattern2746, replacement2746)
    pattern2747 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons1265, cons62, cons1387)
    def replacement2747(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2747)
        return Int(ExpandTrig((g*sin(e + f*x))**p, (a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x), x)
    rule2747 = ReplacementRule(pattern2747, replacement2747)
    pattern2748 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons1265, cons17)
    def replacement2748(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2748)
        return Dist(a**m*g*(g*cos(e + f*x))**(p + S(-1))*(-sin(e + f*x) + S(1))**(-p/S(2) + S(1)/2)*(sin(e + f*x) + S(1))**(-p/S(2) + S(1)/2)/f, Subst(Int((S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2)*(c + d*x)**n, x), x, sin(e + f*x)), x)
    rule2748 = ReplacementRule(pattern2748, replacement2748)
    pattern2749 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons1265, cons17)
    def replacement2749(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2749)
        return -Dist(a**m*g*(g*sin(e + f*x))**(p + S(-1))*(-cos(e + f*x) + S(1))**(-p/S(2) + S(1)/2)*(cos(e + f*x) + S(1))**(-p/S(2) + S(1)/2)/f, Subst(Int((S(1) - b*x/a)**(p/S(2) + S(-1)/2)*(S(1) + b*x/a)**(m + p/S(2) + S(-1)/2)*(c + d*x)**n, x), x, cos(e + f*x)), x)
    rule2749 = ReplacementRule(pattern2749, replacement2749)
    pattern2750 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons1265, cons18)
    def replacement2750(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2750)
        return Dist(g*(g*cos(e + f*x))**(p + S(-1))*(a - b*sin(e + f*x))**(-p/S(2) + S(1)/2)*(a + b*sin(e + f*x))**(-p/S(2) + S(1)/2)/f, Subst(Int((a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2)*(c + d*x)**n, x), x, sin(e + f*x)), x)
    rule2750 = ReplacementRule(pattern2750, replacement2750)
    pattern2751 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons5, cons1265, cons18)
    def replacement2751(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2751)
        return -Dist(g*(g*sin(e + f*x))**(p + S(-1))*(a - b*cos(e + f*x))**(-p/S(2) + S(1)/2)*(a + b*cos(e + f*x))**(-p/S(2) + S(1)/2)/f, Subst(Int((a - b*x)**(p/S(2) + S(-1)/2)*(a + b*x)**(m + p/S(2) + S(-1)/2)*(c + d*x)**n, x), x, cos(e + f*x)), x)
    rule2751 = ReplacementRule(pattern2751, replacement2751)
    pattern2752 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1267, cons1390)
    def replacement2752(m, f, b, d, a, c, n, x, e):
        rubi.append(2752)
        return Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*(-sin(e + f*x)**S(2) + S(1)), x)
    rule2752 = ReplacementRule(pattern2752, replacement2752)
    pattern2753 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1267, cons1390)
    def replacement2753(m, f, b, d, a, c, n, x, e):
        rubi.append(2753)
        return Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*(-cos(e + f*x)**S(2) + S(1)), x)
    rule2753 = ReplacementRule(pattern2753, replacement2753)
    pattern2754 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1267, cons1408, cons1390)
    def replacement2754(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2754)
        return Int(ExpandTrig((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*(-sin(e + f*x)**S(2) + S(1))**(p/S(2)), x), x)
    rule2754 = ReplacementRule(pattern2754, replacement2754)
    pattern2755 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1267, cons1408, cons1390)
    def replacement2755(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2755)
        return Int(ExpandTrig((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*(-cos(e + f*x)**S(2) + S(1))**(p/S(2)), x), x)
    rule2755 = ReplacementRule(pattern2755, replacement2755)
    pattern2756 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons1267, cons1170)
    def replacement2756(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2756)
        return Int(ExpandTrig((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x), x)
    rule2756 = ReplacementRule(pattern2756, replacement2756)
    pattern2757 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons1267, cons1170)
    def replacement2757(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2757)
        return Int(ExpandTrig((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x), x)
    rule2757 = ReplacementRule(pattern2757, replacement2757)
    pattern2758 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons1267)
    def replacement2758(p, m, f, b, g, d, c, n, a, x, e):
        rubi.append(2758)
        return Int((g*cos(e + f*x))**p*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x)
    rule2758 = ReplacementRule(pattern2758, replacement2758)
    pattern2759 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons1267)
    def replacement2759(p, m, f, b, g, d, c, n, a, x, e):
        rubi.append(2759)
        return Int((g*sin(e + f*x))**p*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x)
    rule2759 = ReplacementRule(pattern2759, replacement2759)
    pattern2760 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons147)
    def replacement2760(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(2760)
        return Dist(g**(S(2)*IntPart(p))*(g/cos(e + f*x))**FracPart(p)*(g*cos(e + f*x))**FracPart(p), Int((g*cos(e + f*x))**(-p)*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x), x)
    rule2760 = ReplacementRule(pattern2760, replacement2760)
    pattern2761 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons147)
    def replacement2761(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2761)
        return Dist(g**(S(2)*IntPart(p))*(g/sin(e + f*x))**FracPart(p)*(g*sin(e + f*x))**FracPart(p), Int((g*sin(e + f*x))**(-p)*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x), x)
    rule2761 = ReplacementRule(pattern2761, replacement2761)
    pattern2762 = Pattern(Integral(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1409)
    def replacement2762(f, g, b, d, a, c, x, e):
        rubi.append(2762)
        return Dist(g/d, Int(sqrt(a + b*sin(e + f*x))/sqrt(g*sin(e + f*x)), x), x) - Dist(c*g/d, Int(sqrt(a + b*sin(e + f*x))/(sqrt(g*sin(e + f*x))*(c + d*sin(e + f*x))), x), x)
    rule2762 = ReplacementRule(pattern2762, replacement2762)
    pattern2763 = Pattern(Integral(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1409)
    def replacement2763(f, b, g, d, a, c, x, e):
        rubi.append(2763)
        return Dist(g/d, Int(sqrt(a + b*cos(e + f*x))/sqrt(g*cos(e + f*x)), x), x) - Dist(c*g/d, Int(sqrt(a + b*cos(e + f*x))/(sqrt(g*cos(e + f*x))*(c + d*cos(e + f*x))), x), x)
    rule2763 = ReplacementRule(pattern2763, replacement2763)
    pattern2764 = Pattern(Integral(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1323)
    def replacement2764(f, g, b, d, a, c, x, e):
        rubi.append(2764)
        return Dist(b/d, Int(sqrt(g*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int(sqrt(g*sin(e + f*x))/(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))), x), x)
    rule2764 = ReplacementRule(pattern2764, replacement2764)
    pattern2765 = Pattern(Integral(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1323)
    def replacement2765(f, b, g, d, a, c, x, e):
        rubi.append(2765)
        return Dist(b/d, Int(sqrt(g*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), x), x) - Dist((-a*d + b*c)/d, Int(sqrt(g*cos(e + f*x))/(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))), x), x)
    rule2765 = ReplacementRule(pattern2765, replacement2765)
    pattern2766 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement2766(f, g, b, d, a, c, x, e):
        rubi.append(2766)
        return Dist(-S(2)*b/f, Subst(Int(S(1)/(a*d + b*c + c*g*x**S(2)), x), x, b*cos(e + f*x)/(sqrt(g*sin(e + f*x))*sqrt(a + b*sin(e + f*x)))), x)
    rule2766 = ReplacementRule(pattern2766, replacement2766)
    pattern2767 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1265)
    def replacement2767(f, b, g, d, a, c, x, e):
        rubi.append(2767)
        return Dist(S(2)*b/f, Subst(Int(S(1)/(a*d + b*c + c*g*x**S(2)), x), x, b*sin(e + f*x)/(sqrt(g*cos(e + f*x))*sqrt(a + b*cos(e + f*x)))), x)
    rule2767 = ReplacementRule(pattern2767, replacement2767)
    pattern2768 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1410, cons1411, cons105)
    def replacement2768(f, b, d, a, c, x, e):
        rubi.append(2768)
        return -Simp(sqrt(a + b)*EllipticE(asin(cos(e + f*x)/(sin(e + f*x) + S(1))), -(a - b)/(a + b))/(c*f), x)
    rule2768 = ReplacementRule(pattern2768, replacement2768)
    pattern2769 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1410, cons1411, cons105)
    def replacement2769(f, b, d, a, c, x, e):
        rubi.append(2769)
        return Simp(sqrt(a + b)*EllipticE(asin(sin(e + f*x)/(cos(e + f*x) + S(1))), -(a - b)/(a + b))/(c*f), x)
    rule2769 = ReplacementRule(pattern2769, replacement2769)
    pattern2770 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1322)
    def replacement2770(f, g, b, d, a, c, x, e):
        rubi.append(2770)
        return -Simp(sqrt(d*sin(e + f*x)/(c + d*sin(e + f*x)))*sqrt(a + b*sin(e + f*x))*EllipticE(asin(c*cos(e + f*x)/(c + d*sin(e + f*x))), (-a*d + b*c)/(a*d + b*c))/(d*f*sqrt(g*sin(e + f*x))*sqrt(c**S(2)*(a + b*sin(e + f*x))/((c + d*sin(e + f*x))*(a*c + b*d)))), x)
    rule2770 = ReplacementRule(pattern2770, replacement2770)
    pattern2771 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1322)
    def replacement2771(f, b, g, d, a, c, x, e):
        rubi.append(2771)
        return Simp(sqrt(d*cos(e + f*x)/(c + d*cos(e + f*x)))*sqrt(a + b*cos(e + f*x))*EllipticE(asin(c*sin(e + f*x)/(c + d*cos(e + f*x))), (-a*d + b*c)/(a*d + b*c))/(d*f*sqrt(g*cos(e + f*x))*sqrt(c**S(2)*(a + b*cos(e + f*x))/((c + d*cos(e + f*x))*(a*c + b*d)))), x)
    rule2771 = ReplacementRule(pattern2771, replacement2771)
    pattern2772 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1323)
    def replacement2772(f, g, b, d, a, c, x, e):
        rubi.append(2772)
        return Dist(a/c, Int(S(1)/(sqrt(g*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), x), x) + Dist((-a*d + b*c)/(c*g), Int(sqrt(g*sin(e + f*x))/(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))), x), x)
    rule2772 = ReplacementRule(pattern2772, replacement2772)
    pattern2773 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1323)
    def replacement2773(f, b, g, d, a, c, x, e):
        rubi.append(2773)
        return Dist(a/c, Int(S(1)/(sqrt(g*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), x), x) + Dist((-a*d + b*c)/(c*g), Int(sqrt(g*cos(e + f*x))/(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))), x), x)
    rule2773 = ReplacementRule(pattern2773, replacement2773)
    pattern2774 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement2774(f, b, d, a, c, x, e):
        rubi.append(2774)
        return Dist(S(1)/c, Int(sqrt(a + b*sin(e + f*x))/sin(e + f*x), x), x) - Dist(d/c, Int(sqrt(a + b*sin(e + f*x))/(c + d*sin(e + f*x)), x), x)
    rule2774 = ReplacementRule(pattern2774, replacement2774)
    pattern2775 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement2775(f, b, d, a, c, x, e):
        rubi.append(2775)
        return Dist(S(1)/c, Int(sqrt(a + b*cos(e + f*x))/cos(e + f*x), x), x) - Dist(d/c, Int(sqrt(a + b*cos(e + f*x))/(c + d*cos(e + f*x)), x), x)
    rule2775 = ReplacementRule(pattern2775, replacement2775)
    pattern2776 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement2776(f, b, d, a, c, x, e):
        rubi.append(2776)
        return Dist(a/c, Int(S(1)/(sqrt(a + b*sin(e + f*x))*sin(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(S(1)/(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))), x), x)
    rule2776 = ReplacementRule(pattern2776, replacement2776)
    pattern2777 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement2777(f, b, d, a, c, x, e):
        rubi.append(2777)
        return Dist(a/c, Int(S(1)/(sqrt(a + b*cos(e + f*x))*cos(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(S(1)/(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))), x), x)
    rule2777 = ReplacementRule(pattern2777, replacement2777)
    pattern2778 = Pattern(Integral(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1409)
    def replacement2778(f, g, b, d, a, c, x, e):
        rubi.append(2778)
        return -Dist(a*g/(-a*d + b*c), Int(S(1)/(sqrt(g*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), x), x) + Dist(c*g/(-a*d + b*c), Int(sqrt(a + b*sin(e + f*x))/(sqrt(g*sin(e + f*x))*(c + d*sin(e + f*x))), x), x)
    rule2778 = ReplacementRule(pattern2778, replacement2778)
    pattern2779 = Pattern(Integral(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1409)
    def replacement2779(f, b, g, d, a, c, x, e):
        rubi.append(2779)
        return -Dist(a*g/(-a*d + b*c), Int(S(1)/(sqrt(g*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), x), x) + Dist(c*g/(-a*d + b*c), Int(sqrt(a + b*cos(e + f*x))/(sqrt(g*cos(e + f*x))*(c + d*cos(e + f*x))), x), x)
    rule2779 = ReplacementRule(pattern2779, replacement2779)
    pattern2780 = Pattern(Integral(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1323)
    def replacement2780(f, g, b, d, a, c, x, e):
        rubi.append(2780)
        return Simp(S(2)*sqrt(-S(1)/tan(e + f*x)**S(2))*sqrt(g*sin(e + f*x))*sqrt((a/sin(e + f*x) + b)/(a + b))*EllipticPi(S(2)*c/(c + d), asin(sqrt(S(2))*sqrt(S(1) - S(1)/sin(e + f*x))/S(2)), S(2)*a/(a + b))*tan(e + f*x)/(f*sqrt(a + b*sin(e + f*x))*(c + d)), x)
    rule2780 = ReplacementRule(pattern2780, replacement2780)
    pattern2781 = Pattern(Integral(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1323)
    def replacement2781(f, b, g, d, a, c, x, e):
        rubi.append(2781)
        return Simp(-S(2)*sqrt(-tan(e + f*x)**S(2))*sqrt(g*cos(e + f*x))*sqrt((a/cos(e + f*x) + b)/(a + b))*EllipticPi(S(2)*c/(c + d), asin(sqrt(S(2))*sqrt(S(1) - S(1)/cos(e + f*x))/S(2)), S(2)*a/(a + b))/(f*sqrt(a + b*cos(e + f*x))*(c + d)*tan(e + f*x)), x)
    rule2781 = ReplacementRule(pattern2781, replacement2781)
    pattern2782 = Pattern(Integral(S(1)/(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1409)
    def replacement2782(f, g, b, d, a, c, x, e):
        rubi.append(2782)
        return Dist(b/(-a*d + b*c), Int(S(1)/(sqrt(g*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), x), x) - Dist(d/(-a*d + b*c), Int(sqrt(a + b*sin(e + f*x))/(sqrt(g*sin(e + f*x))*(c + d*sin(e + f*x))), x), x)
    rule2782 = ReplacementRule(pattern2782, replacement2782)
    pattern2783 = Pattern(Integral(S(1)/(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1409)
    def replacement2783(f, b, g, d, a, c, x, e):
        rubi.append(2783)
        return Dist(b/(-a*d + b*c), Int(S(1)/(sqrt(g*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), x), x) - Dist(d/(-a*d + b*c), Int(sqrt(a + b*cos(e + f*x))/(sqrt(g*cos(e + f*x))*(c + d*cos(e + f*x))), x), x)
    rule2783 = ReplacementRule(pattern2783, replacement2783)
    pattern2784 = Pattern(Integral(S(1)/(sqrt(WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1323)
    def replacement2784(f, g, b, d, a, c, x, e):
        rubi.append(2784)
        return Dist(S(1)/c, Int(S(1)/(sqrt(g*sin(e + f*x))*sqrt(a + b*sin(e + f*x))), x), x) - Dist(d/(c*g), Int(sqrt(g*sin(e + f*x))/(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))), x), x)
    rule2784 = ReplacementRule(pattern2784, replacement2784)
    pattern2785 = Pattern(Integral(S(1)/(sqrt(WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons71, cons1267, cons1323)
    def replacement2785(f, b, g, d, a, c, x, e):
        rubi.append(2785)
        return Dist(S(1)/c, Int(S(1)/(sqrt(g*cos(e + f*x))*sqrt(a + b*cos(e + f*x))), x), x) - Dist(d/(c*g), Int(sqrt(g*cos(e + f*x))/(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))), x), x)
    rule2785 = ReplacementRule(pattern2785, replacement2785)
    pattern2786 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement2786(f, b, d, a, c, x, e):
        rubi.append(2786)
        return Dist(S(1)/(c*(-a*d + b*c)), Int((-a*d + b*c - b*d*sin(e + f*x))/(sqrt(a + b*sin(e + f*x))*sin(e + f*x)), x), x) + Dist(d**S(2)/(c*(-a*d + b*c)), Int(sqrt(a + b*sin(e + f*x))/(c + d*sin(e + f*x)), x), x)
    rule2786 = ReplacementRule(pattern2786, replacement2786)
    pattern2787 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265)
    def replacement2787(f, b, d, a, c, x, e):
        rubi.append(2787)
        return Dist(S(1)/(c*(-a*d + b*c)), Int((-a*d + b*c - b*d*cos(e + f*x))/(sqrt(a + b*cos(e + f*x))*cos(e + f*x)), x), x) + Dist(d**S(2)/(c*(-a*d + b*c)), Int(sqrt(a + b*cos(e + f*x))/(c + d*cos(e + f*x)), x), x)
    rule2787 = ReplacementRule(pattern2787, replacement2787)
    pattern2788 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement2788(f, b, d, a, c, x, e):
        rubi.append(2788)
        return Dist(S(1)/c, Int(S(1)/(sqrt(a + b*sin(e + f*x))*sin(e + f*x)), x), x) - Dist(d/c, Int(S(1)/(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))), x), x)
    rule2788 = ReplacementRule(pattern2788, replacement2788)
    pattern2789 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267)
    def replacement2789(f, b, d, a, c, x, e):
        rubi.append(2789)
        return Dist(S(1)/c, Int(S(1)/(sqrt(a + b*cos(e + f*x))*cos(e + f*x)), x), x) - Dist(d/c, Int(S(1)/(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))), x), x)
    rule2789 = ReplacementRule(pattern2789, replacement2789)
    pattern2790 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons70)
    def replacement2790(f, b, d, a, c, x, e):
        rubi.append(2790)
        return Dist(S(1)/c, Int(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))/sin(e + f*x), x), x) - Dist(d/c, Int(sqrt(a + b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x)
    rule2790 = ReplacementRule(pattern2790, replacement2790)
    pattern2791 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons70)
    def replacement2791(f, b, d, a, c, x, e):
        rubi.append(2791)
        return Dist(S(1)/c, Int(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))/cos(e + f*x), x), x) - Dist(d/c, Int(sqrt(a + b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x)
    rule2791 = ReplacementRule(pattern2791, replacement2791)
    pattern2792 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1412)
    def replacement2792(f, b, d, a, c, x, e):
        rubi.append(2792)
        return Dist(-S(2)*a/f, Subst(Int(S(1)/(-a*c*x**S(2) + S(1)), x), x, cos(e + f*x)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x)))), x)
    rule2792 = ReplacementRule(pattern2792, replacement2792)
    pattern2793 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1412)
    def replacement2793(f, b, d, a, c, x, e):
        rubi.append(2793)
        return Dist(S(2)*a/f, Subst(Int(S(1)/(-a*c*x**S(2) + S(1)), x), x, sin(e + f*x)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x)))), x)
    rule2793 = ReplacementRule(pattern2793, replacement2793)
    pattern2794 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1322)
    def replacement2794(f, b, d, a, c, x, e):
        rubi.append(2794)
        return Dist(a/c, Int(sqrt(c + d*sin(e + f*x))/(sqrt(a + b*sin(e + f*x))*sin(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(S(1)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x)
    rule2794 = ReplacementRule(pattern2794, replacement2794)
    pattern2795 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1322)
    def replacement2795(f, b, d, a, c, x, e):
        rubi.append(2795)
        return Dist(a/c, Int(sqrt(c + d*cos(e + f*x))/(sqrt(a + b*cos(e + f*x))*cos(e + f*x)), x), x) + Dist((-a*d + b*c)/c, Int(S(1)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x)
    rule2795 = ReplacementRule(pattern2795, replacement2795)
    pattern2796 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2796(f, b, d, a, c, x, e):
        rubi.append(2796)
        return Simp(-S(2)*sqrt((-a*d + b*c)*(sin(e + f*x) + S(1))/((a + b*sin(e + f*x))*(c - d)))*sqrt(-(-a*d + b*c)*(-sin(e + f*x) + S(1))/((a + b*sin(e + f*x))*(c + d)))*(a + b*sin(e + f*x))*EllipticPi(a*(c + d)/(c*(a + b)), asin(sqrt(c + d*sin(e + f*x))*Rt((a + b)/(c + d), S(2))/sqrt(a + b*sin(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))/(c*f*Rt((a + b)/(c + d), S(2))*cos(e + f*x)), x)
    rule2796 = ReplacementRule(pattern2796, replacement2796)
    pattern2797 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1267, cons1323)
    def replacement2797(f, b, d, a, c, x, e):
        rubi.append(2797)
        return Simp(S(2)*sqrt((-a*d + b*c)*(cos(e + f*x) + S(1))/((a + b*cos(e + f*x))*(c - d)))*sqrt(-(-a*d + b*c)*(-cos(e + f*x) + S(1))/((a + b*cos(e + f*x))*(c + d)))*(a + b*cos(e + f*x))*EllipticPi(a*(c + d)/(c*(a + b)), asin(sqrt(c + d*cos(e + f*x))*Rt((a + b)/(c + d), S(2))/sqrt(a + b*cos(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))/(c*f*Rt((a + b)/(c + d), S(2))*sin(e + f*x)), x)
    rule2797 = ReplacementRule(pattern2797, replacement2797)
    pattern2798 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement2798(f, b, d, a, c, x, e):
        rubi.append(2798)
        return Dist(cos(e + f*x)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), Int(S(1)/(sin(e + f*x)*cos(e + f*x)), x), x)
    rule2798 = ReplacementRule(pattern2798, replacement2798)
    pattern2799 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement2799(f, b, d, a, c, x, e):
        rubi.append(2799)
        return Dist(sin(e + f*x)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), Int(S(1)/(sin(e + f*x)*cos(e + f*x)), x), x)
    rule2799 = ReplacementRule(pattern2799, replacement2799)
    pattern2800 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1413)
    def replacement2800(f, b, d, a, c, x, e):
        rubi.append(2800)
        return Dist(S(1)/a, Int(sqrt(a + b*sin(e + f*x))/(sqrt(c + d*sin(e + f*x))*sin(e + f*x)), x), x) - Dist(b/a, Int(S(1)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x)
    rule2800 = ReplacementRule(pattern2800, replacement2800)
    pattern2801 = Pattern(Integral(S(1)/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1413)
    def replacement2801(f, b, d, a, c, x, e):
        rubi.append(2801)
        return Dist(S(1)/a, Int(sqrt(a + b*cos(e + f*x))/(sqrt(c + d*cos(e + f*x))*cos(e + f*x)), x), x) - Dist(b/a, Int(S(1)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x)
    rule2801 = ReplacementRule(pattern2801, replacement2801)
    pattern2802 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement2802(f, b, d, a, c, x, e):
        rubi.append(2802)
        return Dist(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))/cos(e + f*x), Int(S(1)/tan(e + f*x), x), x)
    rule2802 = ReplacementRule(pattern2802, replacement2802)
    pattern2803 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1265, cons1322)
    def replacement2803(f, b, d, a, c, x, e):
        rubi.append(2803)
        return Dist(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))/sin(e + f*x), Int(tan(e + f*x), x), x)
    rule2803 = ReplacementRule(pattern2803, replacement2803)
    pattern2804 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1413)
    def replacement2804(f, b, d, a, c, x, e):
        rubi.append(2804)
        return Dist(c, Int(sqrt(a + b*sin(e + f*x))/(sqrt(c + d*sin(e + f*x))*sin(e + f*x)), x), x) + Dist(d, Int(sqrt(a + b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x)
    rule2804 = ReplacementRule(pattern2804, replacement2804)
    pattern2805 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons71, cons1413)
    def replacement2805(f, b, d, a, c, x, e):
        rubi.append(2805)
        return Dist(c, Int(sqrt(a + b*cos(e + f*x))/(sqrt(c + d*cos(e + f*x))*cos(e + f*x)), x), x) + Dist(d, Int(sqrt(a + b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x)
    rule2805 = ReplacementRule(pattern2805, replacement2805)
    pattern2806 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons70, cons1265, cons1414, cons85)
    def replacement2806(p, m, f, b, d, a, n, c, x, e):
        rubi.append(2806)
        return Dist(a**n*c**n, Int((a + b*sin(e + f*x))**(m - n)*tan(e + f*x)**p, x), x)
    rule2806 = ReplacementRule(pattern2806, replacement2806)
    pattern2807 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons70, cons1265, cons1414, cons85)
    def replacement2807(p, m, f, b, d, a, n, c, x, e):
        rubi.append(2807)
        return Dist(a**n*c**n, Int((a + b*cos(e + f*x))**(m - n)*(S(1)/tan(e + f*x))**p, x), x)
    rule2807 = ReplacementRule(pattern2807, replacement2807)
    pattern2808 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons1265, cons1323, cons1304)
    def replacement2808(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(2808)
        return Dist(sqrt(a - b*sin(e + f*x))*sqrt(a + b*sin(e + f*x))/(f*cos(e + f*x)), Subst(Int((g*x)**p*(a + b*x)**(m + S(-1)/2)*(c + d*x)**n/sqrt(a - b*x), x), x, sin(e + f*x)), x)
    rule2808 = ReplacementRule(pattern2808, replacement2808)
    pattern2809 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons1265, cons1323, cons1304)
    def replacement2809(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2809)
        return -Dist(sqrt(a - b*cos(e + f*x))*sqrt(a + b*cos(e + f*x))/(f*sin(e + f*x)), Subst(Int((g*x)**p*(a + b*x)**(m + S(-1)/2)*(c + d*x)**n/sqrt(a - b*x), x), x, cos(e + f*x)), x)
    rule2809 = ReplacementRule(pattern2809, replacement2809)
    pattern2810 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons71, cons1415, cons1416)
    def replacement2810(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(2810)
        return Int(ExpandTrig((g*sin(e + f*x))**p*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x), x)
    rule2810 = ReplacementRule(pattern2810, replacement2810)
    pattern2811 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons71, cons1415, cons1416)
    def replacement2811(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2811)
        return Int(ExpandTrig((g*cos(e + f*x))**p*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x), x)
    rule2811 = ReplacementRule(pattern2811, replacement2811)
    pattern2812 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons1416)
    def replacement2812(p, m, f, g, b, d, a, c, n, x, e):
        rubi.append(2812)
        return Int((g*sin(e + f*x))**p*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x)
    rule2812 = ReplacementRule(pattern2812, replacement2812)
    pattern2813 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons1416)
    def replacement2813(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2813)
        return Int((g*cos(e + f*x))**p*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x)
    rule2813 = ReplacementRule(pattern2813, replacement2813)
    pattern2814 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons71, cons147, cons17, cons85)
    def replacement2814(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(2814)
        return Dist(g**(m + n), Int((g*sin(e + f*x))**(-m - n + p)*(a*sin(e + f*x) + b)**m*(c*sin(e + f*x) + d)**n, x), x)
    rule2814 = ReplacementRule(pattern2814, replacement2814)
    pattern2815 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons71, cons147, cons17, cons85)
    def replacement2815(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(2815)
        return Dist(g**(m + n), Int((g*cos(e + f*x))**(-m - n + p)*(a*cos(e + f*x) + b)**m*(c*cos(e + f*x) + d)**n, x), x)
    rule2815 = ReplacementRule(pattern2815, replacement2815)
    pattern2816 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons147, cons1417)
    def replacement2816(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(2816)
        return Dist((g/sin(e + f*x))**p*(g*sin(e + f*x))**p, Int((g/sin(e + f*x))**(-p)*(a + b/sin(e + f*x))**m*(c + d/sin(e + f*x))**n, x), x)
    rule2816 = ReplacementRule(pattern2816, replacement2816)
    pattern2817 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons147, cons1417)
    def replacement2817(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(2817)
        return Dist((g/cos(e + f*x))**p*(g*cos(e + f*x))**p, Int((g/cos(e + f*x))**(-p)*(a + b/cos(e + f*x))**m*(c + d/cos(e + f*x))**n, x), x)
    rule2817 = ReplacementRule(pattern2817, replacement2817)
    pattern2818 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons85)
    def replacement2818(p, m, g, f, b, d, c, n, a, x, e):
        rubi.append(2818)
        return Dist(g**n, Int((g*sin(e + f*x))**(-n + p)*(a + b*sin(e + f*x))**m*(c*sin(e + f*x) + d)**n, x), x)
    rule2818 = ReplacementRule(pattern2818, replacement2818)
    pattern2819 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons85)
    def replacement2819(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(2819)
        return Dist(g**n, Int((g*cos(e + f*x))**(-n + p)*(a + b*cos(e + f*x))**m*(c*cos(e + f*x) + d)**n, x), x)
    rule2819 = ReplacementRule(pattern2819, replacement2819)
    pattern2820 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons23, cons17, cons38)
    def replacement2820(p, m, f, b, d, c, n, a, x, e):
        rubi.append(2820)
        return Int((c + d/sin(e + f*x))**n*(a/sin(e + f*x) + b)**m*(S(1)/sin(e + f*x))**(-m - p), x)
    rule2820 = ReplacementRule(pattern2820, replacement2820)
    pattern2821 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons23, cons17, cons38)
    def replacement2821(p, m, f, b, d, a, c, n, x, e):
        rubi.append(2821)
        return Int((c + d/cos(e + f*x))**n*(a/cos(e + f*x) + b)**m*(S(1)/cos(e + f*x))**(-m - p), x)
    rule2821 = ReplacementRule(pattern2821, replacement2821)
    pattern2822 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons23, cons17, cons147)
    def replacement2822(p, m, f, b, g, d, c, n, a, x, e):
        rubi.append(2822)
        return Dist((g*sin(e + f*x))**p*(S(1)/sin(e + f*x))**p, Int((c + d/sin(e + f*x))**n*(a/sin(e + f*x) + b)**m*(S(1)/sin(e + f*x))**(-m - p), x), x)
    rule2822 = ReplacementRule(pattern2822, replacement2822)
    pattern2823 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons23, cons17, cons147)
    def replacement2823(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2823)
        return Dist((g*cos(e + f*x))**p*(S(1)/cos(e + f*x))**p, Int((c + d/cos(e + f*x))**n*(a/cos(e + f*x) + b)**m*(S(1)/cos(e + f*x))**(-m - p), x), x)
    rule2823 = ReplacementRule(pattern2823, replacement2823)
    pattern2824 = Pattern(Integral((WC('g', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons23, cons18)
    def replacement2824(p, m, f, g, b, d, c, n, a, x, e):
        rubi.append(2824)
        return Dist((g*sin(e + f*x))**n*(c + d/sin(e + f*x))**n*(c*sin(e + f*x) + d)**(-n), Int((g*sin(e + f*x))**(-n + p)*(a + b*sin(e + f*x))**m*(c*sin(e + f*x) + d)**n, x), x)
    rule2824 = ReplacementRule(pattern2824, replacement2824)
    pattern2825 = Pattern(Integral((WC('g', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons23, cons18)
    def replacement2825(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2825)
        return Dist((g*cos(e + f*x))**n*(c + d/cos(e + f*x))**n*(c*cos(e + f*x) + d)**(-n), Int((g*cos(e + f*x))**(-n + p)*(a + b*cos(e + f*x))**m*(c*cos(e + f*x) + d)**n, x), x)
    rule2825 = ReplacementRule(pattern2825, replacement2825)
    pattern2826 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons71, cons147, cons17, cons85)
    def replacement2826(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(2826)
        return Dist(g**(m + n), Int((g/sin(e + f*x))**(-m - n + p)*(a/sin(e + f*x) + b)**m*(c/sin(e + f*x) + d)**n, x), x)
    rule2826 = ReplacementRule(pattern2826, replacement2826)
    pattern2827 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons5, cons71, cons147, cons17, cons85)
    def replacement2827(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(2827)
        return Dist(g**(m + n), Int((g/cos(e + f*x))**(-m - n + p)*(a/cos(e + f*x) + b)**m*(c/cos(e + f*x) + d)**n, x), x)
    rule2827 = ReplacementRule(pattern2827, replacement2827)
    pattern2828 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons147, cons1417)
    def replacement2828(p, m, f, g, b, d, a, n, c, x, e):
        rubi.append(2828)
        return Dist((g/sin(e + f*x))**p*(g*sin(e + f*x))**p, Int((g*sin(e + f*x))**(-p)*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x), x)
    rule2828 = ReplacementRule(pattern2828, replacement2828)
    pattern2829 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons71, cons147, cons1417)
    def replacement2829(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(2829)
        return Dist((g/cos(e + f*x))**p*(g*cos(e + f*x))**p, Int((g*cos(e + f*x))**(-p)*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x), x)
    rule2829 = ReplacementRule(pattern2829, replacement2829)
    pattern2830 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons17)
    def replacement2830(p, m, f, g, b, d, c, n, a, x, e):
        rubi.append(2830)
        return Dist(g**m, Int((g/sin(e + f*x))**(-m + p)*(c + d/sin(e + f*x))**n*(a/sin(e + f*x) + b)**m, x), x)
    rule2830 = ReplacementRule(pattern2830, replacement2830)
    pattern2831 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons4, cons5, cons17)
    def replacement2831(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(2831)
        return Dist(g**m, Int((g/cos(e + f*x))**(-m + p)*(c + d/cos(e + f*x))**n*(a/cos(e + f*x) + b)**m, x), x)
    rule2831 = ReplacementRule(pattern2831, replacement2831)
    pattern2832 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(S(1)/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons18, cons85, cons38)
    def replacement2832(p, m, f, b, d, c, n, a, x, e):
        rubi.append(2832)
        return Int((a + b*sin(e + f*x))**m*(c*sin(e + f*x) + d)**n*sin(e + f*x)**(-n - p), x)
    rule2832 = ReplacementRule(pattern2832, replacement2832)
    pattern2833 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(S(1)/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons18, cons85, cons38)
    def replacement2833(p, m, f, b, d, a, n, c, x, e):
        rubi.append(2833)
        return Int((a + b*cos(e + f*x))**m*(c*cos(e + f*x) + d)**n*cos(e + f*x)**(-n - p), x)
    rule2833 = ReplacementRule(pattern2833, replacement2833)
    pattern2834 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons18, cons85, cons147)
    def replacement2834(p, m, f, g, b, d, c, n, a, x, e):
        rubi.append(2834)
        return Dist((g/sin(e + f*x))**p*sin(e + f*x)**p, Int((a + b*sin(e + f*x))**m*(c*sin(e + f*x) + d)**n*sin(e + f*x)**(-n - p), x), x)
    rule2834 = ReplacementRule(pattern2834, replacement2834)
    pattern2835 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons5, cons18, cons85, cons147)
    def replacement2835(p, m, f, b, g, d, a, n, c, x, e):
        rubi.append(2835)
        return Dist((g/cos(e + f*x))**p*cos(e + f*x)**p, Int((a + b*cos(e + f*x))**m*(c*cos(e + f*x) + d)**n*cos(e + f*x)**(-n - p), x), x)
    rule2835 = ReplacementRule(pattern2835, replacement2835)
    pattern2836 = Pattern(Integral((WC('g', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons18, cons23)
    def replacement2836(p, m, f, g, b, d, c, n, a, x, e):
        rubi.append(2836)
        return Dist((g/sin(e + f*x))**m*(a + b*sin(e + f*x))**m*(a/sin(e + f*x) + b)**(-m), Int((g/sin(e + f*x))**(-m + p)*(c + d/sin(e + f*x))**n*(a/sin(e + f*x) + b)**m, x), x)
    rule2836 = ReplacementRule(pattern2836, replacement2836)
    pattern2837 = Pattern(Integral((WC('g', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('p', S(1))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))/cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons208, cons21, cons4, cons5, cons18, cons23)
    def replacement2837(p, m, f, b, g, d, a, c, n, x, e):
        rubi.append(2837)
        return Dist((g/cos(e + f*x))**m*(a + b*cos(e + f*x))**m*(a/cos(e + f*x) + b)**(-m), Int((g/cos(e + f*x))**(-m + p)*(c + d/cos(e + f*x))**n*(a/cos(e + f*x) + b)**m, x), x)
    rule2837 = ReplacementRule(pattern2837, replacement2837)
    pattern2838 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1418, cons1265, cons17, cons85)
    def replacement2838(B, m, f, b, a, n, A, x, e):
        rubi.append(2838)
        return Int(ExpandTrig((A + B*sin(e + f*x))*(a + b*sin(e + f*x))**m*sin(e + f*x)**n, x), x)
    rule2838 = ReplacementRule(pattern2838, replacement2838)
    pattern2839 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons1418, cons1265, cons17, cons85)
    def replacement2839(B, e, m, f, b, a, n, x, A):
        rubi.append(2839)
        return Int(ExpandTrig((A + B*cos(e + f*x))*(a + b*cos(e + f*x))**m*cos(e + f*x)**n, x), x)
    rule2839 = ReplacementRule(pattern2839, replacement2839)
    pattern2840 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons70, cons1265, cons17, cons1309)
    def replacement2840(B, e, m, f, b, d, a, n, c, x, A):
        rubi.append(2840)
        return Dist(a**m*c**m, Int((A + B*sin(e + f*x))*(c + d*sin(e + f*x))**(-m + n)*cos(e + f*x)**(S(2)*m), x), x)
    rule2840 = ReplacementRule(pattern2840, replacement2840)
    pattern2841 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons70, cons1265, cons17, cons1309)
    def replacement2841(B, m, f, b, d, a, n, c, A, x, e):
        rubi.append(2841)
        return Dist(a**m*c**m, Int((A + B*cos(e + f*x))*(c + d*cos(e + f*x))**(-m + n)*sin(e + f*x)**(S(2)*m), x), x)
    rule2841 = ReplacementRule(pattern2841, replacement2841)
    pattern2842 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71)
    def replacement2842(B, m, f, b, d, a, c, A, x, e):
        rubi.append(2842)
        return Int((a + b*sin(e + f*x))**m*(A*c + B*d*sin(e + f*x)**S(2) + (A*d + B*c)*sin(e + f*x)), x)
    rule2842 = ReplacementRule(pattern2842, replacement2842)
    pattern2843 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71)
    def replacement2843(B, m, f, b, d, a, c, A, x, e):
        rubi.append(2843)
        return Int((a + b*cos(e + f*x))**m*(A*c + B*d*cos(e + f*x)**S(2) + (A*d + B*c)*cos(e + f*x)), x)
    rule2843 = ReplacementRule(pattern2843, replacement2843)
    pattern2844 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons70, cons1265)
    def replacement2844(B, e, f, b, d, a, c, x, A):
        rubi.append(2844)
        return Dist((A*b + B*a)/(S(2)*a*b), Int(sqrt(a + b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x) + Dist((A*d + B*c)/(S(2)*c*d), Int(sqrt(c + d*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), x), x)
    rule2844 = ReplacementRule(pattern2844, replacement2844)
    pattern2845 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons70, cons1265)
    def replacement2845(B, f, b, d, a, c, A, x, e):
        rubi.append(2845)
        return Dist((A*b + B*a)/(S(2)*a*b), Int(sqrt(a + b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x) + Dist((A*d + B*c)/(S(2)*c*d), Int(sqrt(c + d*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), x), x)
    rule2845 = ReplacementRule(pattern2845, replacement2845)
    pattern2846 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons70, cons1265, cons1419, cons1314)
    def replacement2846(B, e, m, f, b, d, a, n, c, x, A):
        rubi.append(2846)
        return -Simp(B*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*(m + n + S(1))), x)
    rule2846 = ReplacementRule(pattern2846, replacement2846)
    pattern2847 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons70, cons1265, cons1419, cons1314)
    def replacement2847(B, m, f, b, d, a, n, c, A, x, e):
        rubi.append(2847)
        return Simp(B*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*(m + n + S(1))), x)
    rule2847 = ReplacementRule(pattern2847, replacement2847)
    pattern2848 = Pattern(Integral((c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons70, cons1265)
    def replacement2848(B, e, f, b, d, a, c, n, x, A):
        rubi.append(2848)
        return Dist(B/d, Int(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))**(n + S(1)), x), x) - Dist((-A*d + B*c)/d, Int(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))**n, x), x)
    rule2848 = ReplacementRule(pattern2848, replacement2848)
    pattern2849 = Pattern(Integral((c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons70, cons1265)
    def replacement2849(B, e, f, b, d, a, c, n, x, A):
        rubi.append(2849)
        return Dist(B/d, Int(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))**(n + S(1)), x), x) - Dist((-A*d + B*c)/d, Int(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))**n, x), x)
    rule2849 = ReplacementRule(pattern2849, replacement2849)
    pattern2850 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons70, cons1265, cons1420, cons1421)
    def replacement2850(B, e, m, f, b, d, a, n, c, x, A):
        rubi.append(2850)
        return Dist((A*b*(m + n + S(1)) + B*a*(m - n))/(a*b*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n, x), x) + Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*(A*b - B*a)*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2850 = ReplacementRule(pattern2850, replacement2850)
    pattern2851 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons70, cons1265, cons1420, cons1421)
    def replacement2851(B, m, f, b, d, a, n, c, A, x, e):
        rubi.append(2851)
        return Dist((A*b*(m + n + S(1)) + B*a*(m - n))/(a*b*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n, x), x) - Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*(A*b - B*a)*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2851 = ReplacementRule(pattern2851, replacement2851)
    pattern2852 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons70, cons1265, cons1321, cons683)
    def replacement2852(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2852)
        return -Dist((-A*d*(m + n + S(1)) + B*c*(m - n))/(d*(m + n + S(1))), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x), x) - Simp(B*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*(m + n + S(1))), x)
    rule2852 = ReplacementRule(pattern2852, replacement2852)
    pattern2853 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons70, cons1265, cons1321, cons683)
    def replacement2853(B, m, f, b, d, a, c, n, A, x, e):
        rubi.append(2853)
        return -Dist((-A*d*(m + n + S(1)) + B*c*(m - n))/(d*(m + n + S(1))), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x), x) + Simp(B*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*(m + n + S(1))), x)
    rule2853 = ReplacementRule(pattern2853, replacement2853)
    pattern2854 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1265, cons1323, cons72, cons1422)
    def replacement2854(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(2854)
        return Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(-A*d + B*c)*cos(e + f*x)/(f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2854 = ReplacementRule(pattern2854, replacement2854)
    pattern2855 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1265, cons1323, cons72, cons1422)
    def replacement2855(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2855)
        return -Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(-A*d + B*c)*sin(e + f*x)/(f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2855 = ReplacementRule(pattern2855, replacement2855)
    pattern2856 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323, cons93, cons1423, cons89, cons515, cons1328)
    def replacement2856(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(2856)
        return -Dist(b/(d*(n + S(1))*(a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1))*Simp(A*a*d*(m - n + S(-2)) - B*(a*c*(m + S(-1)) + b*d*(n + S(1))) - (A*b*d*(m + n + S(1)) - B*(-a*d*(n + S(1)) + b*c*m))*sin(e + f*x), x), x), x) - Simp(b**S(2)*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1))*(-A*d + B*c)*cos(e + f*x)/(d*f*(n + S(1))*(a*d + b*c)), x)
    rule2856 = ReplacementRule(pattern2856, replacement2856)
    pattern2857 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323, cons93, cons1423, cons89, cons515, cons1328)
    def replacement2857(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2857)
        return -Dist(b/(d*(n + S(1))*(a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1))*Simp(A*a*d*(m - n + S(-2)) - B*(a*c*(m + S(-1)) + b*d*(n + S(1))) - (A*b*d*(m + n + S(1)) - B*(-a*d*(n + S(1)) + b*c*m))*cos(e + f*x), x), x), x) + Simp(b**S(2)*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1))*(-A*d + B*c)*sin(e + f*x)/(d*f*(n + S(1))*(a*d + b*c)), x)
    rule2857 = ReplacementRule(pattern2857, replacement2857)
    pattern2858 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1265, cons1323, cons31, cons1423, cons346, cons515, cons1328)
    def replacement2858(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(2858)
        return Dist(S(1)/(d*(m + n + S(1))), Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n*Simp(A*a*d*(m + n + S(1)) + B*(a*c*(m + S(-1)) + b*d*(n + S(1))) + (A*b*d*(m + n + S(1)) - B*(-a*d*(S(2)*m + n) + b*c*m))*sin(e + f*x), x), x), x) - Simp(B*b*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n + S(1))), x)
    rule2858 = ReplacementRule(pattern2858, replacement2858)
    pattern2859 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1265, cons1323, cons31, cons1423, cons346, cons515, cons1328)
    def replacement2859(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2859)
        return Dist(S(1)/(d*(m + n + S(1))), Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n*Simp(A*a*d*(m + n + S(1)) + B*(a*c*(m + S(-1)) + b*d*(n + S(1))) + (A*b*d*(m + n + S(1)) - B*(-a*d*(S(2)*m + n) + b*c*m))*cos(e + f*x), x), x), x) + Simp(B*b*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n + S(1))), x)
    rule2859 = ReplacementRule(pattern2859, replacement2859)
    pattern2860 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323, cons93, cons1320, cons88, cons515, cons1328)
    def replacement2860(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(2860)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(-1))*Simp(A*(a*d*n - b*c*(m + S(1))) - B*(a*c*m + b*d*n) - d*(A*b*(m + n + S(1)) + B*a*(m - n))*sin(e + f*x), x), x), x) + Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*(A*b - B*a)*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2860 = ReplacementRule(pattern2860, replacement2860)
    pattern2861 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323, cons93, cons1320, cons88, cons515, cons1328)
    def replacement2861(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2861)
        return -Dist(S(1)/(a*b*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(-1))*Simp(A*(a*d*n - b*c*(m + S(1))) - B*(a*c*m + b*d*n) - d*(A*b*(m + n + S(1)) + B*a*(m - n))*cos(e + f*x), x), x), x) - Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*(A*b - B*a)*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2861 = ReplacementRule(pattern2861, replacement2861)
    pattern2862 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1265, cons1323, cons31, cons1320, cons1327, cons515, cons1328)
    def replacement2862(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(2862)
        return Dist(S(1)/(a*(S(2)*m + S(1))*(-a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(A*(-a*d*(S(2)*m + n + S(2)) + b*c*(m + S(1))) + B*(a*c*m + b*d*(n + S(1))) + d*(A*b - B*a)*(m + n + S(2))*sin(e + f*x), x), x), x) + Simp(b*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(A*b - B*a)*cos(e + f*x)/(a*f*(S(2)*m + S(1))*(-a*d + b*c)), x)
    rule2862 = ReplacementRule(pattern2862, replacement2862)
    pattern2863 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1265, cons1323, cons31, cons1320, cons1327, cons515, cons1328)
    def replacement2863(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2863)
        return Dist(S(1)/(a*(S(2)*m + S(1))*(-a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(A*(-a*d*(S(2)*m + n + S(2)) + b*c*(m + S(1))) + B*(a*c*m + b*d*(n + S(1))) + d*(A*b - B*a)*(m + n + S(2))*cos(e + f*x), x), x), x) - Simp(b*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(A*b - B*a)*sin(e + f*x)/(a*f*(S(2)*m + S(1))*(-a*d + b*c)), x)
    rule2863 = ReplacementRule(pattern2863, replacement2863)
    pattern2864 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1265, cons1323, cons1424)
    def replacement2864(B, e, f, b, d, c, a, n, x, A):
        rubi.append(2864)
        return Simp(-S(2)*B*b*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*sqrt(a + b*sin(e + f*x))*(S(2)*n + S(3))), x)
    rule2864 = ReplacementRule(pattern2864, replacement2864)
    pattern2865 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1265, cons1323, cons1424)
    def replacement2865(B, f, b, d, c, n, a, A, x, e):
        rubi.append(2865)
        return Simp(S(2)*B*b*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*sqrt(a + b*cos(e + f*x))*(S(2)*n + S(3))), x)
    rule2865 = ReplacementRule(pattern2865, replacement2865)
    pattern2866 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323, cons87, cons89)
    def replacement2866(B, e, f, b, d, c, a, n, x, A):
        rubi.append(2866)
        return Dist((A*b*d*(S(2)*n + S(3)) - B*(-S(2)*a*d*(n + S(1)) + b*c))/(S(2)*d*(n + S(1))*(a*d + b*c)), Int(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))**(n + S(1)), x), x) - Simp(b**S(2)*(c + d*sin(e + f*x))**(n + S(1))*(-A*d + B*c)*cos(e + f*x)/(d*f*sqrt(a + b*sin(e + f*x))*(n + S(1))*(a*d + b*c)), x)
    rule2866 = ReplacementRule(pattern2866, replacement2866)
    pattern2867 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323, cons87, cons89)
    def replacement2867(B, f, b, d, c, n, a, A, x, e):
        rubi.append(2867)
        return Dist((A*b*d*(S(2)*n + S(3)) - B*(-S(2)*a*d*(n + S(1)) + b*c))/(S(2)*d*(n + S(1))*(a*d + b*c)), Int(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))**(n + S(1)), x), x) + Simp(b**S(2)*(c + d*cos(e + f*x))**(n + S(1))*(-A*d + B*c)*sin(e + f*x)/(d*f*sqrt(a + b*cos(e + f*x))*(n + S(1))*(a*d + b*c)), x)
    rule2867 = ReplacementRule(pattern2867, replacement2867)
    pattern2868 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1265, cons1323, cons346)
    def replacement2868(B, e, f, b, d, c, a, n, x, A):
        rubi.append(2868)
        return Dist((A*b*d*(S(2)*n + S(3)) - B*(-S(2)*a*d*(n + S(1)) + b*c))/(b*d*(S(2)*n + S(3))), Int(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))**n, x), x) + Simp(-S(2)*B*b*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*sqrt(a + b*sin(e + f*x))*(S(2)*n + S(3))), x)
    rule2868 = ReplacementRule(pattern2868, replacement2868)
    pattern2869 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1265, cons1323, cons346)
    def replacement2869(B, f, b, d, c, n, a, A, x, e):
        rubi.append(2869)
        return Dist((A*b*d*(S(2)*n + S(3)) - B*(-S(2)*a*d*(n + S(1)) + b*c))/(b*d*(S(2)*n + S(3))), Int(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))**n, x), x) + Simp(S(2)*B*b*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*sqrt(a + b*cos(e + f*x))*(S(2)*n + S(3))), x)
    rule2869 = ReplacementRule(pattern2869, replacement2869)
    pattern2870 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323)
    def replacement2870(B, e, f, b, d, c, a, x, A):
        rubi.append(2870)
        return Dist(B/b, Int(sqrt(a + b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x) + Dist((A*b - B*a)/b, Int(S(1)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x)
    rule2870 = ReplacementRule(pattern2870, replacement2870)
    pattern2871 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323)
    def replacement2871(B, f, b, d, c, a, A, x, e):
        rubi.append(2871)
        return Dist(B/b, Int(sqrt(a + b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x) + Dist((A*b - B*a)/b, Int(S(1)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x)
    rule2871 = ReplacementRule(pattern2871, replacement2871)
    pattern2872 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1265, cons1323, cons87, cons88, cons1425)
    def replacement2872(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(2872)
        return Dist(S(1)/(b*(m + n + S(1))), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(-1))*Simp(A*b*c*(m + n + S(1)) + B*(a*c*m + b*d*n) + (A*b*d*(m + n + S(1)) + B*(a*d*m + b*c*n))*sin(e + f*x), x), x), x) - Simp(B*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*(m + n + S(1))), x)
    rule2872 = ReplacementRule(pattern2872, replacement2872)
    pattern2873 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1265, cons1323, cons87, cons88, cons1425)
    def replacement2873(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2873)
        return Dist(S(1)/(b*(m + n + S(1))), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(-1))*Simp(A*b*c*(m + n + S(1)) + B*(a*c*m + b*d*n) + (A*b*d*(m + n + S(1)) + B*(a*d*m + b*c*n))*cos(e + f*x), x), x), x) + Simp(B*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*(m + n + S(1))), x)
    rule2873 = ReplacementRule(pattern2873, replacement2873)
    pattern2874 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1265, cons1323, cons87, cons89, cons1425)
    def replacement2874(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(2874)
        return Dist(S(1)/(b*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*Simp(A*(a*d*m + b*c*(n + S(1))) - B*(a*c*m + b*d*(n + S(1))) + b*(-A*d + B*c)*(m + n + S(2))*sin(e + f*x), x), x), x) + Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(-A*d + B*c)*cos(e + f*x)/(f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2874 = ReplacementRule(pattern2874, replacement2874)
    pattern2875 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1265, cons1323, cons87, cons89, cons1425)
    def replacement2875(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2875)
        return Dist(S(1)/(b*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*Simp(A*(a*d*m + b*c*(n + S(1))) - B*(a*c*m + b*d*(n + S(1))) + b*(-A*d + B*c)*(m + n + S(2))*cos(e + f*x), x), x), x) - Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(-A*d + B*c)*sin(e + f*x)/(f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2875 = ReplacementRule(pattern2875, replacement2875)
    pattern2876 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323)
    def replacement2876(B, e, f, b, d, c, a, x, A):
        rubi.append(2876)
        return Dist((A*b - B*a)/(-a*d + b*c), Int(S(1)/sqrt(a + b*sin(e + f*x)), x), x) + Dist((-A*d + B*c)/(-a*d + b*c), Int(sqrt(a + b*sin(e + f*x))/(c + d*sin(e + f*x)), x), x)
    rule2876 = ReplacementRule(pattern2876, replacement2876)
    pattern2877 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1265, cons1323)
    def replacement2877(B, f, b, d, c, a, A, x, e):
        rubi.append(2877)
        return Dist((A*b - B*a)/(-a*d + b*c), Int(S(1)/sqrt(a + b*cos(e + f*x)), x), x) + Dist((-A*d + B*c)/(-a*d + b*c), Int(sqrt(a + b*cos(e + f*x))/(c + d*cos(e + f*x)), x), x)
    rule2877 = ReplacementRule(pattern2877, replacement2877)
    pattern2878 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1265, cons1323, cons1314)
    def replacement2878(B, e, m, f, b, d, c, a, x, A):
        rubi.append(2878)
        return Dist(B/d, Int((a + b*sin(e + f*x))**m, x), x) - Dist((-A*d + B*c)/d, Int((a + b*sin(e + f*x))**m/(c + d*sin(e + f*x)), x), x)
    rule2878 = ReplacementRule(pattern2878, replacement2878)
    pattern2879 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1265, cons1323, cons1314)
    def replacement2879(B, m, f, b, d, c, a, A, x, e):
        rubi.append(2879)
        return Dist(B/d, Int((a + b*cos(e + f*x))**m, x), x) - Dist((-A*d + B*c)/d, Int((a + b*cos(e + f*x))**m/(c + d*cos(e + f*x)), x), x)
    rule2879 = ReplacementRule(pattern2879, replacement2879)
    pattern2880 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1265, cons1323, cons1426)
    def replacement2880(B, e, m, f, b, d, c, a, n, x, A):
        rubi.append(2880)
        return Dist(B/b, Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n, x), x) + Dist((A*b - B*a)/b, Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x), x)
    rule2880 = ReplacementRule(pattern2880, replacement2880)
    pattern2881 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1265, cons1323, cons1426)
    def replacement2881(B, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2881)
        return Dist(B/b, Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n, x), x) + Dist((A*b - B*a)/b, Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x), x)
    rule2881 = ReplacementRule(pattern2881, replacement2881)
    pattern2882 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons93, cons166, cons89)
    def replacement2882(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2882)
        return Dist(S(1)/(d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*sin(e + f*x))**(m + S(-2))*(c + d*sin(e + f*x))**(n + S(1))*Simp(a*d*(n + S(1))*(A*a*c + B*b*c - d*(A*b + B*a)) + b*(m + S(-1))*(-A*d + B*c)*(-a*d + b*c) + b*(-B*b*(c**S(2)*m + d**S(2)*(n + S(1))) + d*(m + n + S(1))*(-A*a*d + A*b*c + B*a*c))*sin(e + f*x)**S(2) + (-a*(n + S(2))*(-A*d + B*c)*(-a*d + b*c) + b*(n + S(1))*(a*(A*c*d + B*(c**S(2) - S(2)*d**S(2))) + b*d*(-A*d + B*c)))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1))*(-A*d + B*c)*(-a*d + b*c)*cos(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2882 = ReplacementRule(pattern2882, replacement2882)
    pattern2883 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons93, cons166, cons89)
    def replacement2883(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2883)
        return Dist(S(1)/(d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*cos(e + f*x))**(m + S(-2))*(c + d*cos(e + f*x))**(n + S(1))*Simp(a*d*(n + S(1))*(A*a*c + B*b*c - d*(A*b + B*a)) + b*(m + S(-1))*(-A*d + B*c)*(-a*d + b*c) + b*(-B*b*(c**S(2)*m + d**S(2)*(n + S(1))) + d*(m + n + S(1))*(-A*a*d + A*b*c + B*a*c))*cos(e + f*x)**S(2) + (-a*(n + S(2))*(-A*d + B*c)*(-a*d + b*c) + b*(n + S(1))*(a*(A*c*d + B*(c**S(2) - S(2)*d**S(2))) + b*d*(-A*d + B*c)))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1))*(-A*d + B*c)*(-a*d + b*c)*sin(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2883 = ReplacementRule(pattern2883, replacement2883)
    pattern2884 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1267, cons1323, cons31, cons166, cons1427)
    def replacement2884(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2884)
        return Dist(S(1)/(d*(m + n + S(1))), Int((a + b*sin(e + f*x))**(m + S(-2))*(c + d*sin(e + f*x))**n*Simp(A*a**S(2)*d*(m + n + S(1)) + B*b*(a*d*(n + S(1)) + b*c*(m + S(-1))) + b*(A*b*d*(m + n + S(1)) - B*(-a*d*(S(2)*m + n) + b*c*m))*sin(e + f*x)**S(2) + (-B*b*(a*c - b*d*(m + n)) + a*d*(S(2)*A*b + B*a)*(m + n + S(1)))*sin(e + f*x), x), x), x) - Simp(B*b*(a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n + S(1))), x)
    rule2884 = ReplacementRule(pattern2884, replacement2884)
    pattern2885 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1267, cons1323, cons31, cons166, cons1427)
    def replacement2885(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2885)
        return Dist(S(1)/(d*(m + n + S(1))), Int((a + b*cos(e + f*x))**(m + S(-2))*(c + d*cos(e + f*x))**n*Simp(A*a**S(2)*d*(m + n + S(1)) + B*b*(a*d*(n + S(1)) + b*c*(m + S(-1))) + b*(A*b*d*(m + n + S(1)) - B*(-a*d*(S(2)*m + n) + b*c*m))*cos(e + f*x)**S(2) + (-B*b*(a*c - b*d*(m + n)) + a*d*(S(2)*A*b + B*a)*(m + n + S(1)))*cos(e + f*x), x), x), x) + Simp(B*b*(a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n + S(1))), x)
    rule2885 = ReplacementRule(pattern2885, replacement2885)
    pattern2886 = Pattern(Integral(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons1323)
    def replacement2886(B, e, f, b, d, c, x, A):
        rubi.append(2886)
        return Dist(B*d/b**S(2), Int(sqrt(b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x) + Int((A*c + (A*d + B*c)*sin(e + f*x))/((b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x)
    rule2886 = ReplacementRule(pattern2886, replacement2886)
    pattern2887 = Pattern(Integral(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons1323)
    def replacement2887(B, e, f, b, d, c, x, A):
        rubi.append(2887)
        return Dist(B*d/b**S(2), Int(sqrt(b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x) + Int((A*c + (A*d + B*c)*cos(e + f*x))/((b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x)
    rule2887 = ReplacementRule(pattern2887, replacement2887)
    pattern2888 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323)
    def replacement2888(B, e, f, b, d, c, a, x, A):
        rubi.append(2888)
        return Dist(B/b, Int(sqrt(c + d*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), x), x) + Dist((A*b - B*a)/b, Int(sqrt(c + d*sin(e + f*x))/(a + b*sin(e + f*x))**(S(3)/2), x), x)
    rule2888 = ReplacementRule(pattern2888, replacement2888)
    pattern2889 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323)
    def replacement2889(B, f, b, d, c, a, A, x, e):
        rubi.append(2889)
        return Dist(B/b, Int(sqrt(c + d*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), x), x) + Dist((A*b - B*a)/b, Int(sqrt(c + d*cos(e + f*x))/(a + b*cos(e + f*x))**(S(3)/2), x), x)
    rule2889 = ReplacementRule(pattern2889, replacement2889)
    pattern2890 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1267)
    def replacement2890(B, e, f, b, d, a, x, A):
        rubi.append(2890)
        return Dist(d/(a**S(2) - b**S(2)), Int((A*b - B*a + (A*a - B*b)*sin(e + f*x))/((d*sin(e + f*x))**(S(3)/2)*sqrt(a + b*sin(e + f*x))), x), x) + Simp(S(2)*(A*b - B*a)*cos(e + f*x)/(f*sqrt(d*sin(e + f*x))*sqrt(a + b*sin(e + f*x))*(a**S(2) - b**S(2))), x)
    rule2890 = ReplacementRule(pattern2890, replacement2890)
    pattern2891 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons1267)
    def replacement2891(B, f, b, d, a, A, x, e):
        rubi.append(2891)
        return Dist(d/(a**S(2) - b**S(2)), Int((A*b - B*a + (A*a - B*b)*cos(e + f*x))/((d*cos(e + f*x))**(S(3)/2)*sqrt(a + b*cos(e + f*x))), x), x) + Simp(-S(2)*(A*b - B*a)*sin(e + f*x)/(f*sqrt(d*cos(e + f*x))*sqrt(a + b*cos(e + f*x))*(a**S(2) - b**S(2))), x)
    rule2891 = ReplacementRule(pattern2891, replacement2891)
    pattern2892 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons1323, cons1428, cons1342)
    def replacement2892(B, f, b, d, c, A, x, e):
        rubi.append(2892)
        return Simp(-S(2)*A*sqrt(c*(S(1) - S(1)/sin(e + f*x))/(c + d))*sqrt(c*(S(1) + S(1)/sin(e + f*x))/(c - d))*(c - d)*EllipticE(asin(sqrt(c + d*sin(e + f*x))/(sqrt(b*sin(e + f*x))*Rt((c + d)/b, S(2)))), -(c + d)/(c - d))*Rt((c + d)/b, S(2))*tan(e + f*x)/(b*c**S(2)*f), x)
    rule2892 = ReplacementRule(pattern2892, replacement2892)
    pattern2893 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons1323, cons1428, cons1342)
    def replacement2893(B, f, b, d, c, A, x, e):
        rubi.append(2893)
        return Simp(S(2)*A*sqrt(c*(S(1) - S(1)/cos(e + f*x))/(c + d))*sqrt(c*(S(1) + S(1)/cos(e + f*x))/(c - d))*(c - d)*EllipticE(asin(sqrt(c + d*cos(e + f*x))/(sqrt(b*cos(e + f*x))*Rt((c + d)/b, S(2)))), -(c + d)/(c - d))*Rt((c + d)/b, S(2))/(b*c**S(2)*f*tan(e + f*x)), x)
    rule2893 = ReplacementRule(pattern2893, replacement2893)
    pattern2894 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons1323, cons1428, cons1344)
    def replacement2894(B, f, b, d, c, A, x, e):
        rubi.append(2894)
        return -Dist(sqrt(-b*sin(e + f*x))/sqrt(b*sin(e + f*x)), Int((A + B*sin(e + f*x))/((-b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x), x)
    rule2894 = ReplacementRule(pattern2894, replacement2894)
    pattern2895 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons1323, cons1428, cons1344)
    def replacement2895(B, f, b, d, c, A, x, e):
        rubi.append(2895)
        return -Dist(sqrt(-b*cos(e + f*x))/sqrt(b*cos(e + f*x)), Int((A + B*cos(e + f*x))/((-b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x), x)
    rule2895 = ReplacementRule(pattern2895, replacement2895)
    pattern2896 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons1428, cons1345)
    def replacement2896(B, f, b, d, a, c, A, x, e):
        rubi.append(2896)
        return Simp(-S(2)*A*sqrt((-a*d + b*c)*(sin(e + f*x) + S(1))/((a + b*sin(e + f*x))*(c - d)))*sqrt(-(-a*d + b*c)*(-sin(e + f*x) + S(1))/((a + b*sin(e + f*x))*(c + d)))*(a + b*sin(e + f*x))*(c - d)*EllipticE(asin(sqrt(c + d*sin(e + f*x))*Rt((a + b)/(c + d), S(2))/sqrt(a + b*sin(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))/(f*(-a*d + b*c)**S(2)*Rt((a + b)/(c + d), S(2))*cos(e + f*x)), x)
    rule2896 = ReplacementRule(pattern2896, replacement2896)
    pattern2897 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons1428, cons1345)
    def replacement2897(B, f, b, d, a, c, A, x, e):
        rubi.append(2897)
        return Simp(S(2)*A*sqrt((-a*d + b*c)*(cos(e + f*x) + S(1))/((a + b*cos(e + f*x))*(c - d)))*sqrt(-(-a*d + b*c)*(-cos(e + f*x) + S(1))/((a + b*cos(e + f*x))*(c + d)))*(a + b*cos(e + f*x))*(c - d)*EllipticE(asin(sqrt(c + d*cos(e + f*x))*Rt((a + b)/(c + d), S(2))/sqrt(a + b*cos(e + f*x))), (a - b)*(c + d)/((a + b)*(c - d)))/(f*(-a*d + b*c)**S(2)*Rt((a + b)/(c + d), S(2))*sin(e + f*x)), x)
    rule2897 = ReplacementRule(pattern2897, replacement2897)
    pattern2898 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons1428, cons1346)
    def replacement2898(B, f, b, d, a, c, A, x, e):
        rubi.append(2898)
        return Dist(sqrt(-c - d*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), Int((A + B*sin(e + f*x))/((a + b*sin(e + f*x))**(S(3)/2)*sqrt(-c - d*sin(e + f*x))), x), x)
    rule2898 = ReplacementRule(pattern2898, replacement2898)
    pattern2899 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons1428, cons1346)
    def replacement2899(B, f, b, d, a, c, A, x, e):
        rubi.append(2899)
        return Dist(sqrt(-c - d*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), Int((A + B*cos(e + f*x))/((a + b*cos(e + f*x))**(S(3)/2)*sqrt(-c - d*cos(e + f*x))), x), x)
    rule2899 = ReplacementRule(pattern2899, replacement2899)
    pattern2900 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons1429)
    def replacement2900(B, e, f, b, d, a, c, x, A):
        rubi.append(2900)
        return Dist((A - B)/(a - b), Int(S(1)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x) - Dist((A*b - B*a)/(a - b), Int((sin(e + f*x) + S(1))/((a + b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x), x)
    rule2900 = ReplacementRule(pattern2900, replacement2900)
    pattern2901 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons1429)
    def replacement2901(B, e, f, b, d, a, c, x, A):
        rubi.append(2901)
        return Dist((A - B)/(a - b), Int(S(1)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x) - Dist((A*b - B*a)/(a - b), Int((cos(e + f*x) + S(1))/((a + b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x), x)
    rule2901 = ReplacementRule(pattern2901, replacement2901)
    pattern2902 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons93, cons94, cons88)
    def replacement2902(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2902)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(-1))*Simp(c*(m + S(1))*(A*a - B*b) + d*n*(A*b - B*a) - d*(A*b - B*a)*(m + n + S(2))*sin(e + f*x)**S(2) + (-c*(m + S(2))*(A*b - B*a) + d*(m + S(1))*(A*a - B*b))*sin(e + f*x), x), x), x) + Simp((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*(-A*b + B*a)*cos(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2902 = ReplacementRule(pattern2902, replacement2902)
    pattern2903 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons93, cons94, cons88)
    def replacement2903(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2903)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(-1))*Simp(c*(m + S(1))*(A*a - B*b) + d*n*(A*b - B*a) - d*(A*b - B*a)*(m + n + S(2))*cos(e + f*x)**S(2) + (-c*(m + S(2))*(A*b - B*a) + d*(m + S(1))*(A*a - B*b))*cos(e + f*x), x), x), x) - Simp((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*(-A*b + B*a)*sin(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2903 = ReplacementRule(pattern2903, replacement2903)
    pattern2904 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1267, cons1323, cons31, cons94, cons1337)
    def replacement2904(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2904)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(b*d*(A*b - B*a)*(m + n + S(2)) - b*d*(A*b - B*a)*(m + n + S(3))*sin(e + f*x)**S(2) + (m + S(1))*(A*a - B*b)*(-a*d + b*c) + (A*b - B*a)*(a*d*(m + S(1)) - b*c*(m + S(2)))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(1))*(A*b**S(2) - B*a*b)*cos(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule2904 = ReplacementRule(pattern2904, replacement2904)
    pattern2905 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons4, cons71, cons1267, cons1323, cons31, cons94, cons1337)
    def replacement2905(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2905)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(b*d*(A*b - B*a)*(m + n + S(2)) - b*d*(A*b - B*a)*(m + n + S(3))*cos(e + f*x)**S(2) + (m + S(1))*(A*a - B*b)*(-a*d + b*c) + (A*b - B*a)*(a*d*(m + S(1)) - b*c*(m + S(2)))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(1))*(A*b**S(2) - B*a*b)*sin(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule2905 = ReplacementRule(pattern2905, replacement2905)
    pattern2906 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323)
    def replacement2906(B, e, f, b, d, a, c, x, A):
        rubi.append(2906)
        return Dist((A*b - B*a)/(-a*d + b*c), Int(S(1)/(a + b*sin(e + f*x)), x), x) + Dist((-A*d + B*c)/(-a*d + b*c), Int(S(1)/(c + d*sin(e + f*x)), x), x)
    rule2906 = ReplacementRule(pattern2906, replacement2906)
    pattern2907 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323)
    def replacement2907(B, e, f, b, d, a, c, x, A):
        rubi.append(2907)
        return Dist((A*b - B*a)/(-a*d + b*c), Int(S(1)/(a + b*cos(e + f*x)), x), x) + Dist((-A*d + B*c)/(-a*d + b*c), Int(S(1)/(c + d*cos(e + f*x)), x), x)
    rule2907 = ReplacementRule(pattern2907, replacement2907)
    pattern2908 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1267, cons1323)
    def replacement2908(B, e, m, f, b, d, a, c, x, A):
        rubi.append(2908)
        return Dist(B/d, Int((a + b*sin(e + f*x))**m, x), x) - Dist((-A*d + B*c)/d, Int((a + b*sin(e + f*x))**m/(c + d*sin(e + f*x)), x), x)
    rule2908 = ReplacementRule(pattern2908, replacement2908)
    pattern2909 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_/(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons71, cons1267, cons1323)
    def replacement2909(B, e, m, f, b, d, a, c, x, A):
        rubi.append(2909)
        return Dist(B/d, Int((a + b*cos(e + f*x))**m, x), x) - Dist((-A*d + B*c)/d, Int((a + b*cos(e + f*x))**m/(c + d*cos(e + f*x)), x), x)
    rule2909 = ReplacementRule(pattern2909, replacement2909)
    pattern2910 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons87, cons1430)
    def replacement2910(B, e, f, b, d, a, c, n, x, A):
        rubi.append(2910)
        return Dist(S(1)/(S(2)*n + S(3)), Int((c + d*sin(e + f*x))**(n + S(-1))*Simp(A*a*c*(S(2)*n + S(3)) + B*(S(2)*a*d*n + b*c) + (A*(S(2)*n + S(3))*(a*d + b*c) + B*(S(2)*n + S(1))*(a*c + b*d))*sin(e + f*x) + (A*b*d*(S(2)*n + S(3)) + B*(a*d + S(2)*b*c*n))*sin(e + f*x)**S(2), x)/sqrt(a + b*sin(e + f*x)), x), x) + Simp(-S(2)*B*sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))**n*cos(e + f*x)/(f*(S(2)*n + S(3))), x)
    rule2910 = ReplacementRule(pattern2910, replacement2910)
    pattern2911 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323, cons87, cons1430)
    def replacement2911(B, e, f, b, d, a, c, n, x, A):
        rubi.append(2911)
        return Dist(S(1)/(S(2)*n + S(3)), Int((c + d*cos(e + f*x))**(n + S(-1))*Simp(A*a*c*(S(2)*n + S(3)) + B*(S(2)*a*d*n + b*c) + (A*(S(2)*n + S(3))*(a*d + b*c) + B*(S(2)*n + S(1))*(a*c + b*d))*cos(e + f*x) + (A*b*d*(S(2)*n + S(3)) + B*(a*d + S(2)*b*c*n))*cos(e + f*x)**S(2), x)/sqrt(a + b*cos(e + f*x)), x), x) + Simp(S(2)*B*sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))**n*sin(e + f*x)/(f*(S(2)*n + S(3))), x)
    rule2911 = ReplacementRule(pattern2911, replacement2911)
    pattern2912 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons105, cons1411, cons1428)
    def replacement2912(B, f, b, a, A, x, e):
        rubi.append(2912)
        return Simp(S(4)*A*EllipticPi(S(-1), -asin(cos(e + f*x)/(sin(e + f*x) + S(1))), -(a - b)/(a + b))/(f*sqrt(a + b)), x)
    rule2912 = ReplacementRule(pattern2912, replacement2912)
    pattern2913 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons105, cons1411, cons1428)
    def replacement2913(B, f, b, a, A, x, e):
        rubi.append(2913)
        return Simp(S(4)*A*EllipticPi(S(-1), asin(sin(e + f*x)/(cos(e + f*x) + S(1))), -(a - b)/(a + b))/(f*sqrt(a + b)), x)
    rule2913 = ReplacementRule(pattern2913, replacement2913)
    pattern2914 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(d_*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons27, cons34, cons35, cons105, cons1411, cons1428)
    def replacement2914(B, f, b, d, a, A, x, e):
        rubi.append(2914)
        return Dist(sqrt(sin(e + f*x))/sqrt(d*sin(e + f*x)), Int((A + B*sin(e + f*x))/(sqrt(a + b*sin(e + f*x))*sqrt(sin(e + f*x))), x), x)
    rule2914 = ReplacementRule(pattern2914, replacement2914)
    pattern2915 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(d_*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons48, cons125, cons27, cons34, cons35, cons105, cons1411, cons1428)
    def replacement2915(B, f, b, d, a, A, x, e):
        rubi.append(2915)
        return Dist(sqrt(cos(e + f*x))/sqrt(d*cos(e + f*x)), Int((A + B*cos(e + f*x))/(sqrt(a + b*cos(e + f*x))*sqrt(cos(e + f*x))), x), x)
    rule2915 = ReplacementRule(pattern2915, replacement2915)
    pattern2916 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323)
    def replacement2916(B, e, f, b, d, c, a, x, A):
        rubi.append(2916)
        return Dist(B/d, Int(sqrt(c + d*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), x), x) - Dist((-A*d + B*c)/d, Int(S(1)/(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))), x), x)
    rule2916 = ReplacementRule(pattern2916, replacement2916)
    pattern2917 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))/(sqrt(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons71, cons1267, cons1323)
    def replacement2917(B, f, b, d, c, a, A, x, e):
        rubi.append(2917)
        return Dist(B/d, Int(sqrt(c + d*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), x), x) - Dist((-A*d + B*c)/d, Int(S(1)/(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))), x), x)
    rule2917 = ReplacementRule(pattern2917, replacement2917)
    pattern2918 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1267, cons1323)
    def replacement2918(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2918)
        return Int((A + B*sin(e + f*x))*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x)
    rule2918 = ReplacementRule(pattern2918, replacement2918)
    pattern2919 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons71, cons1267, cons1323)
    def replacement2919(B, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2919)
        return Int((A + B*cos(e + f*x))*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x)
    rule2919 = ReplacementRule(pattern2919, replacement2919)
    pattern2920 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons5, cons70, cons1265)
    def replacement2920(B, p, e, m, f, b, d, a, n, c, x, A):
        rubi.append(2920)
        return Dist(sqrt(a + b*sin(e + f*x))*sqrt(c + d*sin(e + f*x))/(f*cos(e + f*x)), Subst(Int((A + B*x)**p*(a + b*x)**(m + S(-1)/2)*(c + d*x)**(n + S(-1)/2), x), x, sin(e + f*x)), x)
    rule2920 = ReplacementRule(pattern2920, replacement2920)
    pattern2921 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons21, cons4, cons5, cons70, cons1265)
    def replacement2921(B, p, m, f, b, d, a, n, c, A, x, e):
        rubi.append(2921)
        return -Dist(sqrt(a + b*cos(e + f*x))*sqrt(c + d*cos(e + f*x))/(f*sin(e + f*x)), Subst(Int((A + B*x)**p*(a + b*x)**(m + S(-1)/2)*(c + d*x)**(n + S(-1)/2), x), x, cos(e + f*x)), x)
    rule2921 = ReplacementRule(pattern2921, replacement2921)
    pattern2922 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons35, cons36, cons21, cons1431)
    def replacement2922(B, C, m, f, b, x, e):
        rubi.append(2922)
        return Dist(S(1)/b, Int((b*sin(e + f*x))**(m + S(1))*(B + C*sin(e + f*x)), x), x)
    rule2922 = ReplacementRule(pattern2922, replacement2922)
    pattern2923 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons35, cons36, cons21, cons1431)
    def replacement2923(B, C, m, f, b, x, e):
        rubi.append(2923)
        return Dist(S(1)/b, Int((b*cos(e + f*x))**(m + S(1))*(B + C*cos(e + f*x)), x), x)
    rule2923 = ReplacementRule(pattern2923, replacement2923)
    pattern2924 = Pattern(Integral((A_ + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons48, cons125, cons34, cons36, cons1228)
    def replacement2924(C, m, f, A, x, e):
        rubi.append(2924)
        return -Dist(S(1)/f, Subst(Int((-x**S(2) + S(1))**(m/S(2) + S(-1)/2)*(A - C*x**S(2) + C), x), x, cos(e + f*x)), x)
    rule2924 = ReplacementRule(pattern2924, replacement2924)
    pattern2925 = Pattern(Integral((A_ + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**WC('m', S(1)), x_), cons48, cons125, cons34, cons36, cons1228)
    def replacement2925(C, m, f, A, x, e):
        rubi.append(2925)
        return Dist(S(1)/f, Subst(Int((-x**S(2) + S(1))**(m/S(2) + S(-1)/2)*(A - C*x**S(2) + C), x), x, sin(e + f*x)), x)
    rule2925 = ReplacementRule(pattern2925, replacement2925)
    pattern2926 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(A_ + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons1432)
    def replacement2926(C, m, f, b, A, x, e):
        rubi.append(2926)
        return Simp(A*(b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*(m + S(1))), x)
    rule2926 = ReplacementRule(pattern2926, replacement2926)
    pattern2927 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(A_ + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons1432)
    def replacement2927(C, m, f, b, A, x, e):
        rubi.append(2927)
        return -Simp(A*(b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*(m + S(1))), x)
    rule2927 = ReplacementRule(pattern2927, replacement2927)
    pattern2928 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(A_ + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons31, cons94)
    def replacement2928(C, m, f, b, A, x, e):
        rubi.append(2928)
        return Dist((A*(m + S(2)) + C*(m + S(1)))/(b**S(2)*(m + S(1))), Int((b*sin(e + f*x))**(m + S(2)), x), x) + Simp(A*(b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*(m + S(1))), x)
    rule2928 = ReplacementRule(pattern2928, replacement2928)
    pattern2929 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(A_ + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons31, cons94)
    def replacement2929(C, m, f, b, A, x, e):
        rubi.append(2929)
        return Dist((A*(m + S(2)) + C*(m + S(1)))/(b**S(2)*(m + S(1))), Int((b*cos(e + f*x))**(m + S(2)), x), x) - Simp(A*(b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*(m + S(1))), x)
    rule2929 = ReplacementRule(pattern2929, replacement2929)
    pattern2930 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons272)
    def replacement2930(C, m, f, b, A, x, e):
        rubi.append(2930)
        return Dist((A*(m + S(2)) + C*(m + S(1)))/(m + S(2)), Int((b*sin(e + f*x))**m, x), x) - Simp(C*(b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*(m + S(2))), x)
    rule2930 = ReplacementRule(pattern2930, replacement2930)
    pattern2931 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(A_ + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons272)
    def replacement2931(C, m, f, b, A, x, e):
        rubi.append(2931)
        return Dist((A*(m + S(2)) + C*(m + S(1)))/(m + S(2)), Int((b*cos(e + f*x))**m, x), x) + Simp(C*(b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*(m + S(2))), x)
    rule2931 = ReplacementRule(pattern2931, replacement2931)
    pattern2932 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons33)
    def replacement2932(B, C, e, m, f, b, a, x, A):
        rubi.append(2932)
        return Dist(b**(S(-2)), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(B*b - C*a + C*b*sin(e + f*x), x), x), x)
    rule2932 = ReplacementRule(pattern2932, replacement2932)
    pattern2933 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons33)
    def replacement2933(B, C, m, f, b, a, A, x, e):
        rubi.append(2933)
        return Dist(b**(S(-2)), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(B*b - C*a + C*b*cos(e + f*x), x), x), x)
    rule2933 = ReplacementRule(pattern2933, replacement2933)
    pattern2934 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1433)
    def replacement2934(C, e, m, f, b, a, x, A):
        rubi.append(2934)
        return Dist(C/b**S(2), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(-a + b*sin(e + f*x), x), x), x)
    rule2934 = ReplacementRule(pattern2934, replacement2934)
    pattern2935 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1433)
    def replacement2935(C, m, f, b, a, A, x, e):
        rubi.append(2935)
        return Dist(C/b**S(2), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(-a + b*cos(e + f*x), x), x), x)
    rule2935 = ReplacementRule(pattern2935, replacement2935)
    pattern2936 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1434, cons77)
    def replacement2936(B, C, e, m, f, b, a, x, A):
        rubi.append(2936)
        return Dist(C, Int((a + b*sin(e + f*x))**m*(sin(e + f*x) + S(1))**S(2), x), x) + Dist(A - C, Int((a + b*sin(e + f*x))**m*(sin(e + f*x) + S(1)), x), x)
    rule2936 = ReplacementRule(pattern2936, replacement2936)
    pattern2937 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons1434, cons77)
    def replacement2937(B, C, m, f, b, a, A, x, e):
        rubi.append(2937)
        return Dist(C, Int((a + b*cos(e + f*x))**m*(cos(e + f*x) + S(1))**S(2), x), x) + Dist(A - C, Int((a + b*cos(e + f*x))**m*(cos(e + f*x) + S(1)), x), x)
    rule2937 = ReplacementRule(pattern2937, replacement2937)
    pattern2938 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1435, cons77)
    def replacement2938(C, e, m, f, b, a, x, A):
        rubi.append(2938)
        return Dist(C, Int((a + b*sin(e + f*x))**m*(sin(e + f*x) + S(1))**S(2), x), x) + Dist(A - C, Int((a + b*sin(e + f*x))**m*(sin(e + f*x) + S(1)), x), x)
    rule2938 = ReplacementRule(pattern2938, replacement2938)
    pattern2939 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons1435, cons77)
    def replacement2939(C, m, f, b, a, A, x, e):
        rubi.append(2939)
        return Dist(C, Int((a + b*cos(e + f*x))**m*(cos(e + f*x) + S(1))**S(2), x), x) + Dist(A - C, Int((a + b*cos(e + f*x))**m*(cos(e + f*x) + S(1)), x), x)
    rule2939 = ReplacementRule(pattern2939, replacement2939)
    pattern2940 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons31, cons94, cons1265)
    def replacement2940(B, C, e, m, f, b, a, x, A):
        rubi.append(2940)
        return Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(A*a*(m + S(1)) + C*b*(S(2)*m + S(1))*sin(e + f*x) + m*(B*b - C*a), x), x), x) + Simp((a + b*sin(e + f*x))**m*(A*b - B*a + C*b)*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2940 = ReplacementRule(pattern2940, replacement2940)
    pattern2941 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons31, cons94, cons1265)
    def replacement2941(B, C, m, f, b, a, A, x, e):
        rubi.append(2941)
        return Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(A*a*(m + S(1)) + C*b*(S(2)*m + S(1))*cos(e + f*x) + m*(B*b - C*a), x), x), x) - Simp((a + b*cos(e + f*x))**m*(A*b - B*a + C*b)*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2941 = ReplacementRule(pattern2941, replacement2941)
    pattern2942 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons31, cons94, cons1265)
    def replacement2942(C, e, m, f, b, a, x, A):
        rubi.append(2942)
        return Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(A*a*(m + S(1)) - C*a*m + C*b*(S(2)*m + S(1))*sin(e + f*x), x), x), x) + Simp(b*(A + C)*(a + b*sin(e + f*x))**m*cos(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2942 = ReplacementRule(pattern2942, replacement2942)
    pattern2943 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons31, cons94, cons1265)
    def replacement2943(C, m, f, b, a, A, x, e):
        rubi.append(2943)
        return Dist(S(1)/(a**S(2)*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(A*a*(m + S(1)) - C*a*m + C*b*(S(2)*m + S(1))*cos(e + f*x), x), x), x) - Simp(b*(A + C)*(a + b*cos(e + f*x))**m*sin(e + f*x)/(a*f*(S(2)*m + S(1))), x)
    rule2943 = ReplacementRule(pattern2943, replacement2943)
    pattern2944 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons31, cons94, cons1267)
    def replacement2944(B, C, e, m, f, b, a, x, A):
        rubi.append(2944)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(b*(m + S(1))*(A*a - B*b + C*a) - (A*b**S(2) - B*a*b + C*a**S(2) + b*(m + S(1))*(A*b - B*a + C*b))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))*cos(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2944 = ReplacementRule(pattern2944, replacement2944)
    pattern2945 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons31, cons94, cons1267)
    def replacement2945(B, C, e, m, f, b, a, x, A):
        rubi.append(2945)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(b*(m + S(1))*(A*a - B*b + C*a) - (A*b**S(2) - B*a*b + C*a**S(2) + b*(m + S(1))*(A*b - B*a + C*b))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))*sin(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2945 = ReplacementRule(pattern2945, replacement2945)
    pattern2946 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons31, cons94, cons1267)
    def replacement2946(C, e, m, f, b, a, x, A):
        rubi.append(2946)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(a*b*(A + C)*(m + S(1)) - (A*b**S(2) + C*a**S(2) + b**S(2)*(A + C)*(m + S(1)))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))*cos(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2946 = ReplacementRule(pattern2946, replacement2946)
    pattern2947 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons31, cons94, cons1267)
    def replacement2947(C, m, f, b, a, A, x, e):
        rubi.append(2947)
        return Dist(S(1)/(b*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(a*b*(A + C)*(m + S(1)) - (A*b**S(2) + C*a**S(2) + b**S(2)*(A + C)*(m + S(1)))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))*sin(e + f*x)/(b*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2947 = ReplacementRule(pattern2947, replacement2947)
    pattern2948 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons272)
    def replacement2948(B, C, m, f, b, a, A, x, e):
        rubi.append(2948)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*sin(e + f*x))**m*Simp(A*b*(m + S(2)) + C*b*(m + S(1)) + (B*b*(m + S(2)) - C*a)*sin(e + f*x), x), x), x) - Simp(C*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*(m + S(2))), x)
    rule2948 = ReplacementRule(pattern2948, replacement2948)
    pattern2949 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons272)
    def replacement2949(B, C, m, f, b, a, A, x, e):
        rubi.append(2949)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*cos(e + f*x))**m*Simp(A*b*(m + S(2)) + C*b*(m + S(1)) + (B*b*(m + S(2)) - C*a)*cos(e + f*x), x), x), x) + Simp(C*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*(m + S(2))), x)
    rule2949 = ReplacementRule(pattern2949, replacement2949)
    pattern2950 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons272)
    def replacement2950(C, e, m, f, b, a, x, A):
        rubi.append(2950)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*sin(e + f*x))**m*Simp(A*b*(m + S(2)) - C*a*sin(e + f*x) + C*b*(m + S(1)), x), x), x) - Simp(C*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*(m + S(2))), x)
    rule2950 = ReplacementRule(pattern2950, replacement2950)
    pattern2951 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons48, cons125, cons34, cons36, cons21, cons272)
    def replacement2951(C, m, f, b, a, A, x, e):
        rubi.append(2951)
        return Dist(S(1)/(b*(m + S(2))), Int((a + b*cos(e + f*x))**m*Simp(A*b*(m + S(2)) - C*a*cos(e + f*x) + C*b*(m + S(1)), x), x), x) + Simp(C*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*(m + S(2))), x)
    rule2951 = ReplacementRule(pattern2951, replacement2951)
    pattern2952 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_)**m_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons5, cons18)
    def replacement2952(B, C, e, p, m, f, b, x, A):
        rubi.append(2952)
        return Dist((b*sin(e + f*x))**(-m*p)*(b*sin(e + f*x)**p)**m, Int((b*sin(e + f*x))**(m*p)*(A + B*sin(e + f*x) + C*sin(e + f*x)**S(2)), x), x)
    rule2952 = ReplacementRule(pattern2952, replacement2952)
    pattern2953 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_)**m_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons35, cons36, cons21, cons5, cons18)
    def replacement2953(B, C, e, p, m, f, b, x, A):
        rubi.append(2953)
        return Dist((b*cos(e + f*x))**(-m*p)*(b*cos(e + f*x)**p)**m, Int((b*cos(e + f*x))**(m*p)*(A + B*cos(e + f*x) + C*cos(e + f*x)**S(2)), x), x)
    rule2953 = ReplacementRule(pattern2953, replacement2953)
    pattern2954 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_)**m_*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons5, cons18)
    def replacement2954(C, e, p, m, f, b, x, A):
        rubi.append(2954)
        return Dist((b*sin(e + f*x))**(-m*p)*(b*sin(e + f*x)**p)**m, Int((b*sin(e + f*x))**(m*p)*(A + C*sin(e + f*x)**S(2)), x), x)
    rule2954 = ReplacementRule(pattern2954, replacement2954)
    pattern2955 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_)**m_*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons48, cons125, cons34, cons36, cons21, cons5, cons18)
    def replacement2955(C, e, p, m, f, b, x, A):
        rubi.append(2955)
        return Dist((b*cos(e + f*x))**(-m*p)*(b*cos(e + f*x)**p)**m, Int((b*cos(e + f*x))**(m*p)*(A + C*cos(e + f*x)**S(2)), x), x)
    rule2955 = ReplacementRule(pattern2955, replacement2955)
    pattern2956 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons31, cons94)
    def replacement2956(B, C, m, f, b, d, c, a, A, x, e):
        rubi.append(2956)
        return -Dist(S(1)/(b**S(2)*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(-C*b*d*(a**S(2) - b**S(2))*(m + S(1))*sin(e + f*x)**S(2) + b*(m + S(1))*(-A*b*(a*c - b*d) + (B*b - C*a)*(-a*d + b*c)) + (B*b*(a**S(2)*d - a*b*c*(m + S(2)) + b**S(2)*d*(m + S(1))) + (-a*d + b*c)*(A*b**S(2)*(m + S(2)) + C*(a**S(2) + b**S(2)*(m + S(1)))))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(-a*d + b*c)*(A*b**S(2) - B*a*b + C*a**S(2))*cos(e + f*x)/(b**S(2)*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2956 = ReplacementRule(pattern2956, replacement2956)
    pattern2957 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons31, cons94)
    def replacement2957(B, C, e, m, f, b, d, a, c, x, A):
        rubi.append(2957)
        return -Dist(S(1)/(b**S(2)*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(-C*b*d*(a**S(2) - b**S(2))*(m + S(1))*cos(e + f*x)**S(2) + b*(m + S(1))*(-A*b*(a*c - b*d) + (B*b - C*a)*(-a*d + b*c)) + (B*b*(a**S(2)*d - a*b*c*(m + S(2)) + b**S(2)*d*(m + S(1))) + (-a*d + b*c)*(A*b**S(2)*(m + S(2)) + C*(a**S(2) + b**S(2)*(m + S(1)))))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(-a*d + b*c)*(A*b**S(2) - B*a*b + C*a**S(2))*sin(e + f*x)/(b**S(2)*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2957 = ReplacementRule(pattern2957, replacement2957)
    pattern2958 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons31, cons94)
    def replacement2958(C, m, f, b, d, c, a, A, x, e):
        rubi.append(2958)
        return Dist(S(1)/(b**S(2)*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*Simp(C*b*d*(a**S(2) - b**S(2))*(m + S(1))*sin(e + f*x)**S(2) + b*(m + S(1))*(A*b*(a*c - b*d) + C*a*(-a*d + b*c)) - (-a*d + b*c)*(A*b**S(2)*(m + S(2)) + C*(a**S(2) + b**S(2)*(m + S(1))))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))*(-a*d + b*c)*cos(e + f*x)/(b**S(2)*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2958 = ReplacementRule(pattern2958, replacement2958)
    pattern2959 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons31, cons94)
    def replacement2959(C, e, m, f, b, d, a, c, x, A):
        rubi.append(2959)
        return Dist(S(1)/(b**S(2)*(a**S(2) - b**S(2))*(m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*Simp(C*b*d*(a**S(2) - b**S(2))*(m + S(1))*cos(e + f*x)**S(2) + b*(m + S(1))*(A*b*(a*c - b*d) + C*a*(-a*d + b*c)) - (-a*d + b*c)*(A*b**S(2)*(m + S(2)) + C*(a**S(2) + b**S(2)*(m + S(1))))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(A*b**S(2) + C*a**S(2))*(-a*d + b*c)*sin(e + f*x)/(b**S(2)*f*(a**S(2) - b**S(2))*(m + S(1))), x)
    rule2959 = ReplacementRule(pattern2959, replacement2959)
    pattern2960 = Pattern(Integral((c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons71, cons1267, cons272)
    def replacement2960(B, C, m, f, b, d, a, c, A, x, e):
        rubi.append(2960)
        return Dist(S(1)/(b*(m + S(3))), Int((a + b*sin(e + f*x))**m*Simp(A*b*c*(m + S(3)) + C*a*d + b*(B*c*(m + S(3)) + d*(A*(m + S(3)) + C*(m + S(2))))*sin(e + f*x) - (S(2)*C*a*d - b*(m + S(3))*(B*d + C*c))*sin(e + f*x)**S(2), x), x), x) - Simp(C*d*(a + b*sin(e + f*x))**(m + S(1))*sin(e + f*x)*cos(e + f*x)/(b*f*(m + S(3))), x)
    rule2960 = ReplacementRule(pattern2960, replacement2960)
    pattern2961 = Pattern(Integral((c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons71, cons1267, cons272)
    def replacement2961(B, C, m, f, b, d, a, c, A, x, e):
        rubi.append(2961)
        return Dist(S(1)/(b*(m + S(3))), Int((a + b*cos(e + f*x))**m*Simp(A*b*c*(m + S(3)) + C*a*d + b*(B*c*(m + S(3)) + d*(A*(m + S(3)) + C*(m + S(2))))*cos(e + f*x) - (S(2)*C*a*d - b*(m + S(3))*(B*d + C*c))*cos(e + f*x)**S(2), x), x), x) + Simp(C*d*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)*cos(e + f*x)/(b*f*(m + S(3))), x)
    rule2961 = ReplacementRule(pattern2961, replacement2961)
    pattern2962 = Pattern(Integral((c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons71, cons1267, cons272)
    def replacement2962(C, m, f, b, d, a, c, A, x, e):
        rubi.append(2962)
        return Dist(S(1)/(b*(m + S(3))), Int((a + b*sin(e + f*x))**m*Simp(A*b*c*(m + S(3)) + C*a*d + b*d*(A*(m + S(3)) + C*(m + S(2)))*sin(e + f*x) - (S(2)*C*a*d - C*b*c*(m + S(3)))*sin(e + f*x)**S(2), x), x), x) - Simp(C*d*(a + b*sin(e + f*x))**(m + S(1))*sin(e + f*x)*cos(e + f*x)/(b*f*(m + S(3))), x)
    rule2962 = ReplacementRule(pattern2962, replacement2962)
    pattern2963 = Pattern(Integral((c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons71, cons1267, cons272)
    def replacement2963(C, m, f, b, d, a, c, A, x, e):
        rubi.append(2963)
        return Dist(S(1)/(b*(m + S(3))), Int((a + b*cos(e + f*x))**m*Simp(A*b*c*(m + S(3)) + C*a*d + b*d*(A*(m + S(3)) + C*(m + S(2)))*cos(e + f*x) - (S(2)*C*a*d - C*b*c*(m + S(3)))*cos(e + f*x)**S(2), x), x), x) + Simp(C*d*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)*cos(e + f*x)/(b*f*(m + S(3))), x)
    rule2963 = ReplacementRule(pattern2963, replacement2963)
    pattern2964 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons70, cons1265, cons1436)
    def replacement2964(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2964)
        return -Dist(S(1)/(S(2)*b*c*d*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(A*(c**S(2)*(m + S(1)) + d**S(2)*(S(2)*m + n + S(2))) - B*c*d*(m - n + S(-1)) - C*(c**S(2)*m - d**S(2)*(n + S(1))) + d*(-C*c*(S(3)*m - n) + (A*c + B*d)*(m + n + S(2)))*sin(e + f*x), x), x), x) + Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(A*a - B*b + C*a)*cos(e + f*x)/(S(2)*b*c*f*(S(2)*m + S(1))), x)
    rule2964 = ReplacementRule(pattern2964, replacement2964)
    pattern2965 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons70, cons1265, cons1436)
    def replacement2965(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2965)
        return -Dist(S(1)/(S(2)*b*c*d*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(A*(c**S(2)*(m + S(1)) + d**S(2)*(S(2)*m + n + S(2))) - B*c*d*(m - n + S(-1)) - C*(c**S(2)*m - d**S(2)*(n + S(1))) + d*(-C*c*(S(3)*m - n) + (A*c + B*d)*(m + n + S(2)))*cos(e + f*x), x), x), x) - Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(A*a - B*b + C*a)*sin(e + f*x)/(S(2)*b*c*f*(S(2)*m + S(1))), x)
    rule2965 = ReplacementRule(pattern2965, replacement2965)
    pattern2966 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons70, cons1265, cons1436)
    def replacement2966(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2966)
        return -Dist(S(1)/(S(2)*b*c*d*(S(2)*m + S(1))), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(A*(c**S(2)*(m + S(1)) + d**S(2)*(S(2)*m + n + S(2))) - C*(c**S(2)*m - d**S(2)*(n + S(1))) + d*(A*c*(m + n + S(2)) - C*c*(S(3)*m - n))*sin(e + f*x), x), x), x) + Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(A*a + C*a)*cos(e + f*x)/(S(2)*b*c*f*(S(2)*m + S(1))), x)
    rule2966 = ReplacementRule(pattern2966, replacement2966)
    pattern2967 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons70, cons1265, cons1436)
    def replacement2967(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2967)
        return -Dist(S(1)/(S(2)*b*c*d*(S(2)*m + S(1))), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(A*(c**S(2)*(m + S(1)) + d**S(2)*(S(2)*m + n + S(2))) - C*(c**S(2)*m - d**S(2)*(n + S(1))) + d*(A*c*(m + n + S(2)) - C*c*(S(3)*m - n))*cos(e + f*x), x), x), x) - Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(A*a + C*a)*sin(e + f*x)/(S(2)*b*c*f*(S(2)*m + S(1))), x)
    rule2967 = ReplacementRule(pattern2967, replacement2967)
    pattern2968 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons70, cons1265, cons1321)
    def replacement2968(B, C, m, f, b, d, a, c, A, x, e):
        rubi.append(2968)
        return Int((a + b*sin(e + f*x))**m*Simp(A + B*sin(e + f*x) + C, x)/sqrt(c + d*sin(e + f*x)), x) + Simp(-S(2)*C*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*sqrt(c + d*sin(e + f*x))*(S(2)*m + S(3))), x)
    rule2968 = ReplacementRule(pattern2968, replacement2968)
    pattern2969 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons70, cons1265, cons1321)
    def replacement2969(B, C, m, f, b, d, a, c, A, x, e):
        rubi.append(2969)
        return Int((a + b*cos(e + f*x))**m*Simp(A + B*cos(e + f*x) + C, x)/sqrt(c + d*cos(e + f*x)), x) + Simp(S(2)*C*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*sqrt(c + d*cos(e + f*x))*(S(2)*m + S(3))), x)
    rule2969 = ReplacementRule(pattern2969, replacement2969)
    pattern2970 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))/sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons70, cons1265, cons1321)
    def replacement2970(C, m, f, b, d, a, c, A, x, e):
        rubi.append(2970)
        return Dist(A + C, Int((a + b*sin(e + f*x))**m/sqrt(c + d*sin(e + f*x)), x), x) + Simp(-S(2)*C*(a + b*sin(e + f*x))**(m + S(1))*cos(e + f*x)/(b*f*sqrt(c + d*sin(e + f*x))*(S(2)*m + S(3))), x)
    rule2970 = ReplacementRule(pattern2970, replacement2970)
    pattern2971 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))/sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons70, cons1265, cons1321)
    def replacement2971(C, m, f, b, d, a, c, A, x, e):
        rubi.append(2971)
        return Dist(A + C, Int((a + b*cos(e + f*x))**m/sqrt(c + d*cos(e + f*x)), x), x) + Simp(S(2)*C*(a + b*cos(e + f*x))**(m + S(1))*sin(e + f*x)/(b*f*sqrt(c + d*cos(e + f*x))*(S(2)*m + S(3))), x)
    rule2971 = ReplacementRule(pattern2971, replacement2971)
    pattern2972 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons70, cons1265, cons1321, cons214)
    def replacement2972(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2972)
        return Dist(S(1)/(b*d*(m + n + S(2))), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*Simp(A*b*d*(m + n + S(2)) + C*(a*c*m + b*d*(n + S(1))) + (B*b*d*(m + n + S(2)) - C*b*c*(S(2)*m + S(1)))*sin(e + f*x), x), x), x) - Simp(C*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2972 = ReplacementRule(pattern2972, replacement2972)
    pattern2973 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons70, cons1265, cons1321, cons214)
    def replacement2973(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2973)
        return Dist(S(1)/(b*d*(m + n + S(2))), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*Simp(A*b*d*(m + n + S(2)) + C*(a*c*m + b*d*(n + S(1))) + (B*b*d*(m + n + S(2)) - C*b*c*(S(2)*m + S(1)))*cos(e + f*x), x), x), x) + Simp(C*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2973 = ReplacementRule(pattern2973, replacement2973)
    pattern2974 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons70, cons1265, cons1321, cons214)
    def replacement2974(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2974)
        return Dist(S(1)/(b*d*(m + n + S(2))), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*Simp(A*b*d*(m + n + S(2)) - C*b*c*(S(2)*m + S(1))*sin(e + f*x) + C*(a*c*m + b*d*(n + S(1))), x), x), x) - Simp(C*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2974 = ReplacementRule(pattern2974, replacement2974)
    pattern2975 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons70, cons1265, cons1321, cons214)
    def replacement2975(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2975)
        return Dist(S(1)/(b*d*(m + n + S(2))), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*Simp(A*b*d*(m + n + S(2)) - C*b*c*(S(2)*m + S(1))*cos(e + f*x) + C*(a*c*m + b*d*(n + S(1))), x), x), x) + Simp(C*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2975 = ReplacementRule(pattern2975, replacement2975)
    pattern2976 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1265, cons1323, cons31, cons1320)
    def replacement2976(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2976)
        return Dist(S(1)/(b*(S(2)*m + S(1))*(-a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(A*(a*c*(m + S(1)) - b*d*(S(2)*m + n + S(2))) + B*(a*d*(n + S(1)) + b*c*m) - C*(a*c*m + b*d*(n + S(1))) + (C*(-a*d*(m - n + S(-1)) + b*c*(S(2)*m + S(1))) + d*(A*a - B*b)*(m + n + S(2)))*sin(e + f*x), x), x), x) + Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(A*a - B*b + C*a)*cos(e + f*x)/(f*(S(2)*m + S(1))*(-a*d + b*c)), x)
    rule2976 = ReplacementRule(pattern2976, replacement2976)
    pattern2977 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1265, cons1323, cons31, cons1320)
    def replacement2977(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2977)
        return Dist(S(1)/(b*(S(2)*m + S(1))*(-a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(A*(a*c*(m + S(1)) - b*d*(S(2)*m + n + S(2))) + B*(a*d*(n + S(1)) + b*c*m) - C*(a*c*m + b*d*(n + S(1))) + (C*(-a*d*(m - n + S(-1)) + b*c*(S(2)*m + S(1))) + d*(A*a - B*b)*(m + n + S(2)))*cos(e + f*x), x), x), x) - Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(A*a - B*b + C*a)*sin(e + f*x)/(f*(S(2)*m + S(1))*(-a*d + b*c)), x)
    rule2977 = ReplacementRule(pattern2977, replacement2977)
    pattern2978 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1265, cons1323, cons31, cons1320)
    def replacement2978(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2978)
        return Dist(S(1)/(b*(S(2)*m + S(1))*(-a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(A*(a*c*(m + S(1)) - b*d*(S(2)*m + n + S(2))) - C*(a*c*m + b*d*(n + S(1))) + (A*a*d*(m + n + S(2)) + C*(-a*d*(m - n + S(-1)) + b*c*(S(2)*m + S(1))))*sin(e + f*x), x), x), x) + Simp(a*(A + C)*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(f*(S(2)*m + S(1))*(-a*d + b*c)), x)
    rule2978 = ReplacementRule(pattern2978, replacement2978)
    pattern2979 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1265, cons1323, cons31, cons1320)
    def replacement2979(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2979)
        return Dist(S(1)/(b*(S(2)*m + S(1))*(-a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(A*(a*c*(m + S(1)) - b*d*(S(2)*m + n + S(2))) - C*(a*c*m + b*d*(n + S(1))) + (A*a*d*(m + n + S(2)) + C*(-a*d*(m - n + S(-1)) + b*c*(S(2)*m + S(1))))*cos(e + f*x), x), x), x) - Simp(a*(A + C)*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(f*(S(2)*m + S(1))*(-a*d + b*c)), x)
    rule2979 = ReplacementRule(pattern2979, replacement2979)
    pattern2980 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons71, cons1265, cons1323, cons1321, cons1437)
    def replacement2980(B, C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(2980)
        return Dist(S(1)/(b*d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*Simp(A*d*(a*d*m + b*c*(n + S(1))) + b*(-C*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(1))) + d*(-A*d + B*c)*(m + n + S(2)))*sin(e + f*x) + (-B*d + C*c)*(a*c*m + b*d*(n + S(1))), x), x), x) - Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(A*d**S(2) - B*c*d + C*c**S(2))*cos(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2980 = ReplacementRule(pattern2980, replacement2980)
    pattern2981 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons71, cons1265, cons1323, cons1321, cons1437)
    def replacement2981(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2981)
        return Dist(S(1)/(b*d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*Simp(A*d*(a*d*m + b*c*(n + S(1))) + b*(-C*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(1))) + d*(-A*d + B*c)*(m + n + S(2)))*cos(e + f*x) + (-B*d + C*c)*(a*c*m + b*d*(n + S(1))), x), x), x) + Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(A*d**S(2) - B*c*d + C*c**S(2))*sin(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2981 = ReplacementRule(pattern2981, replacement2981)
    pattern2982 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons71, cons1265, cons1323, cons1321, cons1437)
    def replacement2982(C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(2982)
        return Dist(S(1)/(b*d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*Simp(A*d*(a*d*m + b*c*(n + S(1))) + C*c*(a*c*m + b*d*(n + S(1))) - b*(A*d**S(2)*(m + n + S(2)) + C*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(1))))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))*cos(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2982 = ReplacementRule(pattern2982, replacement2982)
    pattern2983 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons71, cons1265, cons1323, cons1321, cons1437)
    def replacement2983(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2983)
        return Dist(S(1)/(b*d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*Simp(A*d*(a*d*m + b*c*(n + S(1))) + C*c*(a*c*m + b*d*(n + S(1))) - b*(A*d**S(2)*(m + n + S(2)) + C*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(1))))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))*sin(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2983 = ReplacementRule(pattern2983, replacement2983)
    pattern2984 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons71, cons1265, cons1323, cons1321, cons214)
    def replacement2984(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2984)
        return Dist(S(1)/(b*d*(m + n + S(2))), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*Simp(A*b*d*(m + n + S(2)) + C*(a*c*m + b*d*(n + S(1))) + (B*b*d*(m + n + S(2)) + C*(a*d*m - b*c*(m + S(1))))*sin(e + f*x), x), x), x) - Simp(C*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2984 = ReplacementRule(pattern2984, replacement2984)
    pattern2985 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons71, cons1265, cons1323, cons1321, cons214)
    def replacement2985(B, C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2985)
        return Dist(S(1)/(b*d*(m + n + S(2))), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*Simp(A*b*d*(m + n + S(2)) + C*(a*c*m + b*d*(n + S(1))) + (B*b*d*(m + n + S(2)) + C*(a*d*m - b*c*(m + S(1))))*cos(e + f*x), x), x), x) + Simp(C*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2985 = ReplacementRule(pattern2985, replacement2985)
    pattern2986 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons71, cons1265, cons1323, cons1321, cons214)
    def replacement2986(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2986)
        return Dist(S(1)/(b*d*(m + n + S(2))), Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*Simp(A*b*d*(m + n + S(2)) + C*(a*c*m + b*d*(n + S(1))) + C*(a*d*m - b*c*(m + S(1)))*sin(e + f*x), x), x), x) - Simp(C*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2986 = ReplacementRule(pattern2986, replacement2986)
    pattern2987 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons71, cons1265, cons1323, cons1321, cons214)
    def replacement2987(C, m, f, b, d, c, n, a, A, x, e):
        rubi.append(2987)
        return Dist(S(1)/(b*d*(m + n + S(2))), Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*Simp(A*b*d*(m + n + S(2)) + C*(a*c*m + b*d*(n + S(1))) + C*(a*d*m - b*c*(m + S(1)))*cos(e + f*x), x), x), x) + Simp(C*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2987 = ReplacementRule(pattern2987, replacement2987)
    pattern2988 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323, cons93, cons168, cons89)
    def replacement2988(B, C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(2988)
        return Dist(S(1)/(d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1))*Simp(A*d*(a*c*(n + S(1)) + b*d*m) + b*(-C*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(1))) + d*(-A*d + B*c)*(m + n + S(2)))*sin(e + f*x)**S(2) + (-B*d + C*c)*(a*d*(n + S(1)) + b*c*m) - (-C*(-a*(c**S(2) + d**S(2)*(n + S(1))) + b*c*d*(n + S(1))) + d*(A*(a*d*(n + S(2)) - b*c*(n + S(1))) + B*(-a*c*(n + S(2)) + b*d*(n + S(1)))))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(A*d**S(2) - B*c*d + C*c**S(2))*cos(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2988 = ReplacementRule(pattern2988, replacement2988)
    pattern2989 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323, cons93, cons168, cons89)
    def replacement2989(B, C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2989)
        return Dist(S(1)/(d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1))*Simp(A*d*(a*c*(n + S(1)) + b*d*m) + b*(-C*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(1))) + d*(-A*d + B*c)*(m + n + S(2)))*cos(e + f*x)**S(2) + (-B*d + C*c)*(a*d*(n + S(1)) + b*c*m) - (-C*(-a*(c**S(2) + d**S(2)*(n + S(1))) + b*c*d*(n + S(1))) + d*(A*(a*d*(n + S(2)) - b*c*(n + S(1))) + B*(-a*c*(n + S(2)) + b*d*(n + S(1)))))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(A*d**S(2) - B*c*d + C*c**S(2))*sin(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2989 = ReplacementRule(pattern2989, replacement2989)
    pattern2990 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323, cons93, cons168, cons89)
    def replacement2990(C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(2990)
        return Dist(S(1)/(d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**(n + S(1))*Simp(A*d*(a*c*(n + S(1)) + b*d*m) + C*c*(a*d*(n + S(1)) + b*c*m) - b*(A*d**S(2)*(m + n + S(2)) + C*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(1))))*sin(e + f*x)**S(2) - (A*d*(a*d*(n + S(2)) - b*c*(n + S(1))) - C*(-a*(c**S(2) + d**S(2)*(n + S(1))) + b*c*d*(n + S(1))))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))*cos(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2990 = ReplacementRule(pattern2990, replacement2990)
    pattern2991 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323, cons93, cons168, cons89)
    def replacement2991(C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(2991)
        return Dist(S(1)/(d*(c**S(2) - d**S(2))*(n + S(1))), Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**(n + S(1))*Simp(A*d*(a*c*(n + S(1)) + b*d*m) + C*c*(a*d*(n + S(1)) + b*c*m) - b*(A*d**S(2)*(m + n + S(2)) + C*(c**S(2)*(m + S(1)) + d**S(2)*(n + S(1))))*cos(e + f*x)**S(2) - (A*d*(a*d*(n + S(2)) - b*c*(n + S(1))) - C*(-a*(c**S(2) + d**S(2)*(n + S(1))) + b*c*d*(n + S(1))))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*(A*d**S(2) + C*c**S(2))*sin(e + f*x)/(d*f*(c**S(2) - d**S(2))*(n + S(1))), x)
    rule2991 = ReplacementRule(pattern2991, replacement2991)
    pattern2992 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1267, cons1323, cons31, cons168, cons1438)
    def replacement2992(B, C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(2992)
        return Dist(S(1)/(d*(m + n + S(2))), Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n*Simp(A*a*d*(m + n + S(2)) + C*(a*d*(n + S(1)) + b*c*m) + (-C*(a*c - b*d*(m + n + S(1))) + d*(A*b + B*a)*(m + n + S(2)))*sin(e + f*x) + (B*b*d*(m + n + S(2)) + C*(a*d*m - b*c*(m + S(1))))*sin(e + f*x)**S(2), x), x), x) - Simp(C*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2992 = ReplacementRule(pattern2992, replacement2992)
    pattern2993 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1267, cons1323, cons31, cons168, cons1438)
    def replacement2993(B, C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(2993)
        return Dist(S(1)/(d*(m + n + S(2))), Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n*Simp(A*a*d*(m + n + S(2)) + C*(a*d*(n + S(1)) + b*c*m) + (-C*(a*c - b*d*(m + n + S(1))) + d*(A*b + B*a)*(m + n + S(2)))*cos(e + f*x) + (B*b*d*(m + n + S(2)) + C*(a*d*m - b*c*(m + S(1))))*cos(e + f*x)**S(2), x), x), x) + Simp(C*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2993 = ReplacementRule(pattern2993, replacement2993)
    pattern2994 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1267, cons1323, cons31, cons168, cons1438)
    def replacement2994(C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(2994)
        return Dist(S(1)/(d*(m + n + S(2))), Int((a + b*sin(e + f*x))**(m + S(-1))*(c + d*sin(e + f*x))**n*Simp(A*a*d*(m + n + S(2)) + C*(a*d*m - b*c*(m + S(1)))*sin(e + f*x)**S(2) + C*(a*d*(n + S(1)) + b*c*m) + (A*b*d*(m + n + S(2)) - C*(a*c - b*d*(m + n + S(1))))*sin(e + f*x), x), x), x) - Simp(C*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**(n + S(1))*cos(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2994 = ReplacementRule(pattern2994, replacement2994)
    pattern2995 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('m', S(1))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1267, cons1323, cons31, cons168, cons1438)
    def replacement2995(C, m, f, b, d, a, c, n, A, x, e):
        rubi.append(2995)
        return Dist(S(1)/(d*(m + n + S(2))), Int((a + b*cos(e + f*x))**(m + S(-1))*(c + d*cos(e + f*x))**n*Simp(A*a*d*(m + n + S(2)) + C*(a*d*m - b*c*(m + S(1)))*cos(e + f*x)**S(2) + C*(a*d*(n + S(1)) + b*c*m) + (A*b*d*(m + n + S(2)) - C*(a*c - b*d*(m + n + S(1))))*cos(e + f*x), x), x), x) + Simp(C*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**(n + S(1))*sin(e + f*x)/(d*f*(m + n + S(2))), x)
    rule2995 = ReplacementRule(pattern2995, replacement2995)
    pattern2996 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267)
    def replacement2996(B, C, e, f, b, d, a, x, A):
        rubi.append(2996)
        return Dist(S(1)/b, Int((A*b + (B*b - C*a)*sin(e + f*x))/(sqrt(d*sin(e + f*x))*(a + b*sin(e + f*x))**(S(3)/2)), x), x) + Dist(C/(b*d), Int(sqrt(d*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), x), x)
    rule2996 = ReplacementRule(pattern2996, replacement2996)
    pattern2997 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons35, cons36, cons1267)
    def replacement2997(B, C, f, b, d, a, A, x, e):
        rubi.append(2997)
        return Dist(S(1)/b, Int((A*b + (B*b - C*a)*cos(e + f*x))/(sqrt(d*cos(e + f*x))*(a + b*cos(e + f*x))**(S(3)/2)), x), x) + Dist(C/(b*d), Int(sqrt(d*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), x), x)
    rule2997 = ReplacementRule(pattern2997, replacement2997)
    pattern2998 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267)
    def replacement2998(C, e, f, b, d, a, x, A):
        rubi.append(2998)
        return Dist(S(1)/b, Int((A*b - C*a*sin(e + f*x))/(sqrt(d*sin(e + f*x))*(a + b*sin(e + f*x))**(S(3)/2)), x), x) + Dist(C/(b*d), Int(sqrt(d*sin(e + f*x))/sqrt(a + b*sin(e + f*x)), x), x)
    rule2998 = ReplacementRule(pattern2998, replacement2998)
    pattern2999 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)), x_), cons2, cons3, cons27, cons48, cons125, cons34, cons36, cons1267)
    def replacement2999(C, f, b, d, a, A, x, e):
        rubi.append(2999)
        return Dist(S(1)/b, Int((A*b - C*a*cos(e + f*x))/(sqrt(d*cos(e + f*x))*(a + b*cos(e + f*x))**(S(3)/2)), x), x) + Dist(C/(b*d), Int(sqrt(d*cos(e + f*x))/sqrt(a + b*cos(e + f*x)), x), x)
    rule2999 = ReplacementRule(pattern2999, replacement2999)
    pattern3000 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323)
    def replacement3000(B, C, f, b, d, c, a, A, x, e):
        rubi.append(3000)
        return Dist(b**(S(-2)), Int((A*b**S(2) - C*a**S(2) + b*(B*b - S(2)*C*a)*sin(e + f*x))/((a + b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x), x) + Dist(C/b**S(2), Int(sqrt(a + b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x)
    rule3000 = ReplacementRule(pattern3000, replacement3000)
    pattern3001 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323)
    def replacement3001(B, C, e, f, b, d, a, c, x, A):
        rubi.append(3001)
        return Dist(b**(S(-2)), Int((A*b**S(2) - C*a**S(2) + b*(B*b - S(2)*C*a)*cos(e + f*x))/((a + b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x), x) + Dist(C/b**S(2), Int(sqrt(a + b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x)
    rule3001 = ReplacementRule(pattern3001, replacement3001)
    pattern3002 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323)
    def replacement3002(C, f, b, d, c, a, A, x, e):
        rubi.append(3002)
        return Dist(b**(S(-2)), Int((A*b**S(2) - C*a**S(2) - S(2)*C*a*b*sin(e + f*x))/((a + b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x), x) + Dist(C/b**S(2), Int(sqrt(a + b*sin(e + f*x))/sqrt(c + d*sin(e + f*x)), x), x)
    rule3002 = ReplacementRule(pattern3002, replacement3002)
    pattern3003 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**(S(3)/2)*sqrt(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323)
    def replacement3003(C, e, f, b, d, a, c, x, A):
        rubi.append(3003)
        return Dist(b**(S(-2)), Int((A*b**S(2) - C*a**S(2) - S(2)*C*a*b*cos(e + f*x))/((a + b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x), x) + Dist(C/b**S(2), Int(sqrt(a + b*cos(e + f*x))/sqrt(c + d*cos(e + f*x)), x), x)
    rule3003 = ReplacementRule(pattern3003, replacement3003)
    pattern3004 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1267, cons1323, cons31, cons94, cons1337)
    def replacement3004(B, C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3004)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(d*(m + n + S(2))*(A*b**S(2) - B*a*b + C*a**S(2)) - d*(m + n + S(3))*(A*b**S(2) - B*a*b + C*a**S(2))*sin(e + f*x)**S(2) + (m + S(1))*(-a*d + b*c)*(A*a - B*b + C*a) - (c*(A*b**S(2) - B*a*b + C*a**S(2)) + (m + S(1))*(-a*d + b*c)*(A*b - B*a + C*b))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))*cos(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3004 = ReplacementRule(pattern3004, replacement3004)
    pattern3005 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons4, cons71, cons1267, cons1323, cons31, cons94, cons1337)
    def replacement3005(B, C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3005)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(d*(m + n + S(2))*(A*b**S(2) - B*a*b + C*a**S(2)) - d*(m + n + S(3))*(A*b**S(2) - B*a*b + C*a**S(2))*cos(e + f*x)**S(2) + (m + S(1))*(-a*d + b*c)*(A*a - B*b + C*a) - (c*(A*b**S(2) - B*a*b + C*a**S(2)) + (m + S(1))*(-a*d + b*c)*(A*b - B*a + C*b))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(1))*(A*b**S(2) - B*a*b + C*a**S(2))*sin(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3005 = ReplacementRule(pattern3005, replacement3005)
    pattern3006 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1267, cons1323, cons31, cons94, cons1337)
    def replacement3006(C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3006)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**n*Simp(a*(A + C)*(m + S(1))*(-a*d + b*c) + d*(A*b**S(2) + C*a**S(2))*(m + n + S(2)) - d*(A*b**S(2) + C*a**S(2))*(m + n + S(3))*sin(e + f*x)**S(2) - (b*(A + C)*(m + S(1))*(-a*d + b*c) + c*(A*b**S(2) + C*a**S(2)))*sin(e + f*x), x), x), x) - Simp((a + b*sin(e + f*x))**(m + S(1))*(c + d*sin(e + f*x))**(n + S(1))*(A*b**S(2) + C*a**S(2))*cos(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3006 = ReplacementRule(pattern3006, replacement3006)
    pattern3007 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons4, cons71, cons1267, cons1323, cons31, cons94, cons1337)
    def replacement3007(C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3007)
        return Dist(S(1)/((a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), Int((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**n*Simp(a*(A + C)*(m + S(1))*(-a*d + b*c) + d*(A*b**S(2) + C*a**S(2))*(m + n + S(2)) - d*(A*b**S(2) + C*a**S(2))*(m + n + S(3))*cos(e + f*x)**S(2) - (b*(A + C)*(m + S(1))*(-a*d + b*c) + c*(A*b**S(2) + C*a**S(2)))*cos(e + f*x), x), x), x) + Simp((a + b*cos(e + f*x))**(m + S(1))*(c + d*cos(e + f*x))**(n + S(1))*(A*b**S(2) + C*a**S(2))*sin(e + f*x)/(f*(a**S(2) - b**S(2))*(m + S(1))*(-a*d + b*c)), x)
    rule3007 = ReplacementRule(pattern3007, replacement3007)
    pattern3008 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323)
    def replacement3008(B, C, f, b, d, c, a, A, x, e):
        rubi.append(3008)
        return Dist((A*b**S(2) - B*a*b + C*a**S(2))/(b*(-a*d + b*c)), Int(S(1)/(a + b*sin(e + f*x)), x), x) - Dist((A*d**S(2) - B*c*d + C*c**S(2))/(d*(-a*d + b*c)), Int(S(1)/(c + d*sin(e + f*x)), x), x) + Simp(C*x/(b*d), x)
    rule3008 = ReplacementRule(pattern3008, replacement3008)
    pattern3009 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323)
    def replacement3009(B, C, f, b, d, c, a, A, x, e):
        rubi.append(3009)
        return Dist((A*b**S(2) - B*a*b + C*a**S(2))/(b*(-a*d + b*c)), Int(S(1)/(a + b*cos(e + f*x)), x), x) - Dist((A*d**S(2) - B*c*d + C*c**S(2))/(d*(-a*d + b*c)), Int(S(1)/(c + d*cos(e + f*x)), x), x) + Simp(C*x/(b*d), x)
    rule3009 = ReplacementRule(pattern3009, replacement3009)
    pattern3010 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323)
    def replacement3010(C, f, b, d, c, a, A, x, e):
        rubi.append(3010)
        return Dist((A*b**S(2) + C*a**S(2))/(b*(-a*d + b*c)), Int(S(1)/(a + b*sin(e + f*x)), x), x) - Dist((A*d**S(2) + C*c**S(2))/(d*(-a*d + b*c)), Int(S(1)/(c + d*sin(e + f*x)), x), x) + Simp(C*x/(b*d), x)
    rule3010 = ReplacementRule(pattern3010, replacement3010)
    pattern3011 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323)
    def replacement3011(C, f, b, d, c, a, A, x, e):
        rubi.append(3011)
        return Dist((A*b**S(2) + C*a**S(2))/(b*(-a*d + b*c)), Int(S(1)/(a + b*cos(e + f*x)), x), x) - Dist((A*d**S(2) + C*c**S(2))/(d*(-a*d + b*c)), Int(S(1)/(c + d*cos(e + f*x)), x), x) + Simp(C*x/(b*d), x)
    rule3011 = ReplacementRule(pattern3011, replacement3011)
    pattern3012 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323)
    def replacement3012(B, C, f, b, d, c, a, A, x, e):
        rubi.append(3012)
        return -Dist(S(1)/(b*d), Int(Simp(-A*b*d + C*a*c + (-B*b*d + C*a*d + C*b*c)*sin(e + f*x), x)/(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))), x), x) + Dist(C/(b*d), Int(sqrt(a + b*sin(e + f*x)), x), x)
    rule3012 = ReplacementRule(pattern3012, replacement3012)
    pattern3013 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323)
    def replacement3013(B, C, e, f, b, d, a, c, x, A):
        rubi.append(3013)
        return -Dist(S(1)/(b*d), Int(Simp(-A*b*d + C*a*c + (-B*b*d + C*a*d + C*b*c)*cos(e + f*x), x)/(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))), x), x) + Dist(C/(b*d), Int(sqrt(a + b*cos(e + f*x)), x), x)
    rule3013 = ReplacementRule(pattern3013, replacement3013)
    pattern3014 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323)
    def replacement3014(C, f, b, d, c, a, A, x, e):
        rubi.append(3014)
        return -Dist(S(1)/(b*d), Int(Simp(-A*b*d + C*a*c + (C*a*d + C*b*c)*sin(e + f*x), x)/(sqrt(a + b*sin(e + f*x))*(c + d*sin(e + f*x))), x), x) + Dist(C/(b*d), Int(sqrt(a + b*sin(e + f*x)), x), x)
    rule3014 = ReplacementRule(pattern3014, replacement3014)
    pattern3015 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323)
    def replacement3015(C, e, f, b, d, a, c, x, A):
        rubi.append(3015)
        return -Dist(S(1)/(b*d), Int(Simp(-A*b*d + C*a*c + (C*a*d + C*b*c)*cos(e + f*x), x)/(sqrt(a + b*cos(e + f*x))*(c + d*cos(e + f*x))), x), x) + Dist(C/(b*d), Int(sqrt(a + b*cos(e + f*x)), x), x)
    rule3015 = ReplacementRule(pattern3015, replacement3015)
    pattern3016 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323)
    def replacement3016(B, C, f, b, d, a, c, A, x, e):
        rubi.append(3016)
        return Dist(S(1)/(S(2)*d), Int(Simp(S(2)*A*a*d - C*(-a*d + b*c) + (S(2)*B*b*d - C*(a*d + b*c))*sin(e + f*x)**S(2) - S(2)*(C*a*c - d*(A*b + B*a))*sin(e + f*x), x)/((a + b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x), x) - Simp(C*sqrt(c + d*sin(e + f*x))*cos(e + f*x)/(d*f*sqrt(a + b*sin(e + f*x))), x)
    rule3016 = ReplacementRule(pattern3016, replacement3016)
    pattern3017 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons71, cons1267, cons1323)
    def replacement3017(B, C, e, f, b, d, a, c, x, A):
        rubi.append(3017)
        return Dist(S(1)/(S(2)*d), Int(Simp(S(2)*A*a*d - C*(-a*d + b*c) + (S(2)*B*b*d - C*(a*d + b*c))*cos(e + f*x)**S(2) - S(2)*(C*a*c - d*(A*b + B*a))*cos(e + f*x), x)/((a + b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x), x) + Simp(C*sqrt(c + d*cos(e + f*x))*sin(e + f*x)/(d*f*sqrt(a + b*cos(e + f*x))), x)
    rule3017 = ReplacementRule(pattern3017, replacement3017)
    pattern3018 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(c_ + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323)
    def replacement3018(C, f, b, d, a, c, A, x, e):
        rubi.append(3018)
        return Dist(S(1)/(S(2)*d), Int(Simp(S(2)*A*a*d - C*(-a*d + b*c) - C*(a*d + b*c)*sin(e + f*x)**S(2) - S(2)*(-A*b*d + C*a*c)*sin(e + f*x), x)/((a + b*sin(e + f*x))**(S(3)/2)*sqrt(c + d*sin(e + f*x))), x), x) - Simp(C*sqrt(c + d*sin(e + f*x))*cos(e + f*x)/(d*f*sqrt(a + b*sin(e + f*x))), x)
    rule3018 = ReplacementRule(pattern3018, replacement3018)
    pattern3019 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))/(sqrt(c_ + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))*sqrt(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons71, cons1267, cons1323)
    def replacement3019(C, e, f, b, d, a, c, x, A):
        rubi.append(3019)
        return Dist(S(1)/(S(2)*d), Int(Simp(S(2)*A*a*d - C*(-a*d + b*c) - C*(a*d + b*c)*cos(e + f*x)**S(2) - S(2)*(-A*b*d + C*a*c)*cos(e + f*x), x)/((a + b*cos(e + f*x))**(S(3)/2)*sqrt(c + d*cos(e + f*x))), x), x) + Simp(C*sqrt(c + d*cos(e + f*x))*sin(e + f*x)/(d*f*sqrt(a + b*cos(e + f*x))), x)
    rule3019 = ReplacementRule(pattern3019, replacement3019)
    pattern3020 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons71, cons1267, cons1323)
    def replacement3020(B, C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3020)
        return Int((a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n*(A + B*sin(e + f*x) + C*sin(e + f*x)**S(2)), x)
    rule3020 = ReplacementRule(pattern3020, replacement3020)
    pattern3021 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons71, cons1267, cons1323)
    def replacement3021(B, C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3021)
        return Int((a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n*(A + B*cos(e + f*x) + C*cos(e + f*x)**S(2)), x)
    rule3021 = ReplacementRule(pattern3021, replacement3021)
    pattern3022 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons71, cons1267, cons1323)
    def replacement3022(C, m, f, b, d, c, a, n, A, x, e):
        rubi.append(3022)
        return Int((A + C*sin(e + f*x)**S(2))*(a + b*sin(e + f*x))**m*(c + d*sin(e + f*x))**n, x)
    rule3022 = ReplacementRule(pattern3022, replacement3022)
    pattern3023 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons71, cons1267, cons1323)
    def replacement3023(C, e, m, f, b, d, a, c, n, x, A):
        rubi.append(3023)
        return Int((A + C*cos(e + f*x)**S(2))*(a + b*cos(e + f*x))**m*(c + d*cos(e + f*x))**n, x)
    rule3023 = ReplacementRule(pattern3023, replacement3023)
    pattern3024 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_)**m_*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons18)
    def replacement3024(B, C, p, m, f, b, d, c, n, A, x, e):
        rubi.append(3024)
        return Dist((b*sin(e + f*x))**(-m*p)*(b*sin(e + f*x)**p)**m, Int((b*sin(e + f*x))**(m*p)*(c + d*sin(e + f*x))**n*(A + B*sin(e + f*x) + C*sin(e + f*x)**S(2)), x), x)
    rule3024 = ReplacementRule(pattern3024, replacement3024)
    pattern3025 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_)**m_*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2)), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons35, cons36, cons21, cons4, cons5, cons18)
    def replacement3025(B, C, e, p, m, f, b, d, c, n, x, A):
        rubi.append(3025)
        return Dist((b*cos(e + f*x))**(-m*p)*(b*cos(e + f*x)**p)**m, Int((b*cos(e + f*x))**(m*p)*(c + d*cos(e + f*x))**n*(A + B*cos(e + f*x) + C*cos(e + f*x)**S(2)), x), x)
    rule3025 = ReplacementRule(pattern3025, replacement3025)
    pattern3026 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**p_)**m_*(WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons5, cons18)
    def replacement3026(C, p, m, f, b, d, c, n, A, x, e):
        rubi.append(3026)
        return Dist((b*sin(e + f*x))**(-m*p)*(b*sin(e + f*x)**p)**m, Int((b*sin(e + f*x))**(m*p)*(A + C*sin(e + f*x)**S(2))*(c + d*sin(e + f*x))**n, x), x)
    rule3026 = ReplacementRule(pattern3026, replacement3026)
    pattern3027 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**p_)**m_*(WC('A', S(0)) + WC('C', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))**S(2))*(WC('c', S(0)) + WC('d', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons34, cons36, cons21, cons4, cons5, cons18)
    def replacement3027(C, e, p, m, f, b, d, c, n, x, A):
        rubi.append(3027)
        return Dist((b*cos(e + f*x))**(-m*p)*(b*cos(e + f*x)**p)**m, Int((b*cos(e + f*x))**(m*p)*(A + C*cos(e + f*x)**S(2))*(c + d*cos(e + f*x))**n, x), x)
    rule3027 = ReplacementRule(pattern3027, replacement3027)
    pattern3028 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1439)
    def replacement3028(b, d, c, a, n, x):
        rubi.append(3028)
        return Simp(a*(a*cos(c + d*x) + b*sin(c + d*x))**n/(b*d*n), x)
    rule3028 = ReplacementRule(pattern3028, replacement3028)
    pattern3029 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1440, cons521)
    def replacement3029(b, d, c, a, n, x):
        rubi.append(3029)
        return -Dist(S(1)/d, Subst(Int((a**S(2) + b**S(2) - x**S(2))**(n/S(2) + S(-1)/2), x), x, -a*sin(c + d*x) + b*cos(c + d*x)), x)
    rule3029 = ReplacementRule(pattern3029, replacement3029)
    pattern3030 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1440, cons1441, cons87, cons165)
    def replacement3030(b, d, c, a, n, x):
        rubi.append(3030)
        return Dist((a**S(2) + b**S(2))*(n + S(-1))/n, Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-2)), x), x) - Simp((-a*sin(c + d*x) + b*cos(c + d*x))*(a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-1))/(d*n), x)
    rule3030 = ReplacementRule(pattern3030, replacement3030)
    pattern3031 = Pattern(Integral(S(1)/(WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440)
    def replacement3031(b, d, c, a, x):
        rubi.append(3031)
        return -Dist(S(1)/d, Subst(Int(S(1)/(a**S(2) + b**S(2) - x**S(2)), x), x, -a*sin(c + d*x) + b*cos(c + d*x)), x)
    rule3031 = ReplacementRule(pattern3031, replacement3031)
    pattern3032 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**(S(-2)), x_), cons2, cons3, cons7, cons27, cons1440)
    def replacement3032(b, d, c, a, x):
        rubi.append(3032)
        return Simp(sin(c + d*x)/(a*d*(a*cos(c + d*x) + b*sin(c + d*x))), x)
    rule3032 = ReplacementRule(pattern3032, replacement3032)
    pattern3033 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons1440, cons87, cons89, cons1442)
    def replacement3033(b, d, c, a, n, x):
        rubi.append(3033)
        return Dist((n + S(2))/((a**S(2) + b**S(2))*(n + S(1))), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(2)), x), x) + Simp((-a*sin(c + d*x) + b*cos(c + d*x))*(a*cos(c + d*x) + b*sin(c + d*x))**(n + S(1))/(d*(a**S(2) + b**S(2))*(n + S(1))), x)
    rule3033 = ReplacementRule(pattern3033, replacement3033)
    pattern3034 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1443, cons1444)
    def replacement3034(b, d, c, a, n, x):
        rubi.append(3034)
        return Dist((a**S(2) + b**S(2))**(n/S(2)), Int(cos(c + d*x - ArcTan(a, b))**n, x), x)
    rule3034 = ReplacementRule(pattern3034, replacement3034)
    pattern3035 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons4, cons1443, cons1445)
    def replacement3035(b, d, c, a, n, x):
        rubi.append(3035)
        return Dist(((a*cos(c + d*x) + b*sin(c + d*x))/sqrt(a**S(2) + b**S(2)))**(-n)*(a*cos(c + d*x) + b*sin(c + d*x))**n, Int(cos(c + d*x - ArcTan(a, b))**n, x), x)
    rule3035 = ReplacementRule(pattern3035, replacement3035)
    pattern3036 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1255, cons1439, cons87, cons165)
    def replacement3036(m, b, d, c, a, n, x):
        rubi.append(3036)
        return Dist(S(2)*b, Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-1))*sin(c + d*x)**(-n + S(1)), x), x) - Simp(a*(a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-1))*sin(c + d*x)**(-n + S(1))/(d*(n + S(-1))), x)
    rule3036 = ReplacementRule(pattern3036, replacement3036)
    pattern3037 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1255, cons1439, cons87, cons165)
    def replacement3037(m, b, d, c, a, n, x):
        rubi.append(3037)
        return Dist(S(2)*a, Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-1))*cos(c + d*x)**(-n + S(1)), x), x) + Simp(b*(a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-1))*cos(c + d*x)**(-n + S(1))/(d*(n + S(-1))), x)
    rule3037 = ReplacementRule(pattern3037, replacement3037)
    pattern3038 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1255, cons1439, cons87, cons463)
    def replacement3038(m, b, d, c, a, n, x):
        rubi.append(3038)
        return Dist(S(1)/(S(2)*b), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(1))*sin(c + d*x)**(-n + S(-1)), x), x) + Simp(a*(a*cos(c + d*x) + b*sin(c + d*x))**n*sin(c + d*x)**(-n)/(S(2)*b*d*n), x)
    rule3038 = ReplacementRule(pattern3038, replacement3038)
    pattern3039 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1255, cons1439, cons87, cons463)
    def replacement3039(m, b, d, c, a, n, x):
        rubi.append(3039)
        return Dist(S(1)/(S(2)*a), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(1))*cos(c + d*x)**(-n + S(-1)), x), x) - Simp(b*(a*cos(c + d*x) + b*sin(c + d*x))**n*cos(c + d*x)**(-n)/(S(2)*a*d*n), x)
    rule3039 = ReplacementRule(pattern3039, replacement3039)
    pattern3040 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1255, cons1439, cons23)
    def replacement3040(m, b, d, c, a, n, x):
        rubi.append(3040)
        return Simp(a*(a*cos(c + d*x) + b*sin(c + d*x))**n*Hypergeometric2F1(S(1), n, n + S(1), (a/tan(c + d*x) + b)/(S(2)*b))*sin(c + d*x)**(-n)/(S(2)*b*d*n), x)
    rule3040 = ReplacementRule(pattern3040, replacement3040)
    pattern3041 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons1255, cons1439, cons23)
    def replacement3041(m, b, d, c, a, n, x):
        rubi.append(3041)
        return -Simp(b*(a*cos(c + d*x) + b*sin(c + d*x))**n*Hypergeometric2F1(S(1), n, n + S(1), (a + b*tan(c + d*x))/(S(2)*a))*cos(c + d*x)**(-n)/(S(2)*a*d*n), x)
    rule3041 = ReplacementRule(pattern3041, replacement3041)
    pattern3042 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1255, cons85, cons1440)
    def replacement3042(m, b, d, c, n, a, x):
        rubi.append(3042)
        return Int((a/tan(c + d*x) + b)**n, x)
    rule3042 = ReplacementRule(pattern3042, replacement3042)
    pattern3043 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1255, cons85, cons1440)
    def replacement3043(m, b, d, c, n, a, x):
        rubi.append(3043)
        return Int((a + b*tan(c + d*x))**n, x)
    rule3043 = ReplacementRule(pattern3043, replacement3043)
    pattern3044 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons85, cons1446, cons1152, cons1447)
    def replacement3044(m, b, d, c, a, n, x):
        rubi.append(3044)
        return Dist(S(1)/d, Subst(Int(x**m*(a + b*x)**n*(x**S(2) + S(1))**(-m/S(2) - n/S(2) + S(-1)), x), x, tan(c + d*x)), x)
    rule3044 = ReplacementRule(pattern3044, replacement3044)
    pattern3045 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons85, cons1446, cons1152, cons1447)
    def replacement3045(m, b, d, c, a, n, x):
        rubi.append(3045)
        return -Dist(S(1)/d, Subst(Int(x**m*(x**S(2) + S(1))**(-m/S(2) - n/S(2) + S(-1))*(a*x + b)**n, x), x, S(1)/tan(c + d*x)), x)
    rule3045 = ReplacementRule(pattern3045, replacement3045)
    pattern3046 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons17, cons148)
    def replacement3046(m, b, d, c, a, n, x):
        rubi.append(3046)
        return Int(ExpandTrig((a*cos(c + d*x) + b*sin(c + d*x))**n*sin(c + d*x)**m, x), x)
    rule3046 = ReplacementRule(pattern3046, replacement3046)
    pattern3047 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('n', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons17, cons148)
    def replacement3047(m, b, d, c, a, n, x):
        rubi.append(3047)
        return Int(ExpandTrig((a*cos(c + d*x) + b*sin(c + d*x))**n*cos(c + d*x)**m, x), x)
    rule3047 = ReplacementRule(pattern3047, replacement3047)
    pattern3048 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons1439, cons196)
    def replacement3048(m, b, d, c, a, n, x):
        rubi.append(3048)
        return Dist(a**n*b**n, Int((a*sin(c + d*x) + b*cos(c + d*x))**(-n)*sin(c + d*x)**m, x), x)
    rule3048 = ReplacementRule(pattern3048, replacement3048)
    pattern3049 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons1439, cons196)
    def replacement3049(m, b, d, c, a, n, x):
        rubi.append(3049)
        return Dist(a**n*b**n, Int((a*sin(c + d*x) + b*cos(c + d*x))**(-n)*cos(c + d*x)**m, x), x)
    rule3049 = ReplacementRule(pattern3049, replacement3049)
    pattern3050 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_/sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons1440, cons87, cons89)
    def replacement3050(b, d, c, a, n, x):
        rubi.append(3050)
        return Dist(a**(S(-2)), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(2))/sin(c + d*x), x), x) - Dist(b/a**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(1)), x), x) - Simp((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(1))/(a*d*(n + S(1))), x)
    rule3050 = ReplacementRule(pattern3050, replacement3050)
    pattern3051 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_/cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons1440, cons87, cons89)
    def replacement3051(b, d, c, a, n, x):
        rubi.append(3051)
        return Dist(b**(S(-2)), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(2))/cos(c + d*x), x), x) - Dist(a/b**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(1)), x), x) + Simp((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(1))/(b*d*(n + S(1))), x)
    rule3051 = ReplacementRule(pattern3051, replacement3051)
    pattern3052 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1440, cons93, cons165, cons94)
    def replacement3052(m, b, d, c, a, n, x):
        rubi.append(3052)
        return Dist(a**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-2))*sin(c + d*x)**m, x), x) + Dist(S(2)*b, Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-1))*sin(c + d*x)**(m + S(1)), x), x) - Dist(a**S(2) + b**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-2))*sin(c + d*x)**(m + S(2)), x), x)
    rule3052 = ReplacementRule(pattern3052, replacement3052)
    pattern3053 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1440, cons93, cons165, cons94)
    def replacement3053(m, b, d, c, a, n, x):
        rubi.append(3053)
        return Dist(S(2)*a, Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-1))*cos(c + d*x)**(m + S(1)), x), x) + Dist(b**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-2))*cos(c + d*x)**m, x), x) - Dist(a**S(2) + b**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(-2))*cos(c + d*x)**(m + S(2)), x), x)
    rule3053 = ReplacementRule(pattern3053, replacement3053)
    pattern3054 = Pattern(Integral(sin(x_*WC('d', S(1)) + WC('c', S(0)))/(WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440)
    def replacement3054(b, d, c, a, x):
        rubi.append(3054)
        return -Dist(a/(a**S(2) + b**S(2)), Int((-a*sin(c + d*x) + b*cos(c + d*x))/(a*cos(c + d*x) + b*sin(c + d*x)), x), x) + Simp(b*x/(a**S(2) + b**S(2)), x)
    rule3054 = ReplacementRule(pattern3054, replacement3054)
    pattern3055 = Pattern(Integral(cos(x_*WC('d', S(1)) + WC('c', S(0)))/(WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440)
    def replacement3055(b, d, c, a, x):
        rubi.append(3055)
        return Dist(b/(a**S(2) + b**S(2)), Int((-a*sin(c + d*x) + b*cos(c + d*x))/(a*cos(c + d*x) + b*sin(c + d*x)), x), x) + Simp(a*x/(a**S(2) + b**S(2)), x)
    rule3055 = ReplacementRule(pattern3055, replacement3055)
    pattern3056 = Pattern(Integral(sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_/(WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440, cons31, cons166)
    def replacement3056(m, b, d, c, a, x):
        rubi.append(3056)
        return Dist(a**S(2)/(a**S(2) + b**S(2)), Int(sin(c + d*x)**(m + S(-2))/(a*cos(c + d*x) + b*sin(c + d*x)), x), x) + Dist(b/(a**S(2) + b**S(2)), Int(sin(c + d*x)**(m + S(-1)), x), x) - Simp(a*sin(c + d*x)**(m + S(-1))/(d*(a**S(2) + b**S(2))*(m + S(-1))), x)
    rule3056 = ReplacementRule(pattern3056, replacement3056)
    pattern3057 = Pattern(Integral(cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_/(WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440, cons31, cons166)
    def replacement3057(m, b, d, c, a, x):
        rubi.append(3057)
        return Dist(a/(a**S(2) + b**S(2)), Int(cos(c + d*x)**(m + S(-1)), x), x) + Dist(b**S(2)/(a**S(2) + b**S(2)), Int(cos(c + d*x)**(m + S(-2))/(a*cos(c + d*x) + b*sin(c + d*x)), x), x) + Simp(b*cos(c + d*x)**(m + S(-1))/(d*(a**S(2) + b**S(2))*(m + S(-1))), x)
    rule3057 = ReplacementRule(pattern3057, replacement3057)
    pattern3058 = Pattern(Integral(S(1)/((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440)
    def replacement3058(b, d, c, a, x):
        rubi.append(3058)
        return -Dist(S(1)/a, Int((-a*sin(c + d*x) + b*cos(c + d*x))/(a*cos(c + d*x) + b*sin(c + d*x)), x), x) + Dist(S(1)/a, Int(S(1)/tan(c + d*x), x), x)
    rule3058 = ReplacementRule(pattern3058, replacement3058)
    pattern3059 = Pattern(Integral(S(1)/((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))*cos(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440)
    def replacement3059(b, d, c, a, x):
        rubi.append(3059)
        return Dist(S(1)/b, Int((-a*sin(c + d*x) + b*cos(c + d*x))/(a*cos(c + d*x) + b*sin(c + d*x)), x), x) + Dist(S(1)/b, Int(tan(c + d*x), x), x)
    rule3059 = ReplacementRule(pattern3059, replacement3059)
    pattern3060 = Pattern(Integral(sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_/(WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440, cons31, cons94)
    def replacement3060(m, b, d, c, a, x):
        rubi.append(3060)
        return -Dist(b/a**S(2), Int(sin(c + d*x)**(m + S(1)), x), x) + Dist((a**S(2) + b**S(2))/a**S(2), Int(sin(c + d*x)**(m + S(2))/(a*cos(c + d*x) + b*sin(c + d*x)), x), x) + Simp(sin(c + d*x)**(m + S(1))/(a*d*(m + S(1))), x)
    rule3060 = ReplacementRule(pattern3060, replacement3060)
    pattern3061 = Pattern(Integral(cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_/(WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440, cons31, cons94)
    def replacement3061(m, b, d, c, a, x):
        rubi.append(3061)
        return -Dist(a/b**S(2), Int(cos(c + d*x)**(m + S(1)), x), x) + Dist((a**S(2) + b**S(2))/b**S(2), Int(cos(c + d*x)**(m + S(2))/(a*cos(c + d*x) + b*sin(c + d*x)), x), x) - Simp(cos(c + d*x)**(m + S(1))/(b*d*(m + S(1))), x)
    rule3061 = ReplacementRule(pattern3061, replacement3061)
    pattern3062 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1440, cons93, cons89, cons94)
    def replacement3062(m, b, d, c, a, n, x):
        rubi.append(3062)
        return Dist(a**(S(-2)), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(2))*sin(c + d*x)**m, x), x) - Dist(S(2)*b/a**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(1))*sin(c + d*x)**(m + S(1)), x), x) + Dist((a**S(2) + b**S(2))/a**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**n*sin(c + d*x)**(m + S(2)), x), x)
    rule3062 = ReplacementRule(pattern3062, replacement3062)
    pattern3063 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1440, cons93, cons89, cons94)
    def replacement3063(m, b, d, c, a, n, x):
        rubi.append(3063)
        return Dist(b**(S(-2)), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(2))*cos(c + d*x)**m, x), x) - Dist(S(2)*a/b**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**(n + S(1))*cos(c + d*x)**(m + S(1)), x), x) + Dist((a**S(2) + b**S(2))/b**S(2), Int((a*cos(c + d*x) + b*sin(c + d*x))**n*cos(c + d*x)**(m + S(2)), x), x)
    rule3063 = ReplacementRule(pattern3063, replacement3063)
    pattern3064 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('n', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons128)
    def replacement3064(p, m, b, d, c, n, a, x):
        rubi.append(3064)
        return Int(ExpandTrig((a*cos(c + d*x) + b*sin(c + d*x))**p*sin(c + d*x)**n*cos(c + d*x)**m, x), x)
    rule3064 = ReplacementRule(pattern3064, replacement3064)
    pattern3065 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('n', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons1439, cons63)
    def replacement3065(p, m, b, d, c, n, a, x):
        rubi.append(3065)
        return Dist(a**p*b**p, Int((a*sin(c + d*x) + b*cos(c + d*x))**(-p)*sin(c + d*x)**n*cos(c + d*x)**m, x), x)
    rule3065 = ReplacementRule(pattern3065, replacement3065)
    pattern3066 = Pattern(Integral(sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('n', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons1440, cons150, cons168, cons88)
    def replacement3066(m, b, d, c, n, a, x):
        rubi.append(3066)
        return Dist(a/(a**S(2) + b**S(2)), Int(sin(c + d*x)**n*cos(c + d*x)**(m + S(-1)), x), x) + Dist(b/(a**S(2) + b**S(2)), Int(sin(c + d*x)**(n + S(-1))*cos(c + d*x)**m, x), x) - Dist(a*b/(a**S(2) + b**S(2)), Int(sin(c + d*x)**(n + S(-1))*cos(c + d*x)**(m + S(-1))/(a*cos(c + d*x) + b*sin(c + d*x)), x), x)
    rule3066 = ReplacementRule(pattern3066, replacement3066)
    pattern3067 = Pattern(Integral(sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('n', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons150)
    def replacement3067(m, b, d, c, n, a, x):
        rubi.append(3067)
        return Int(ExpandTrig(sin(c + d*x)**n*cos(c + d*x)**m/(a*cos(c + d*x) + b*sin(c + d*x)), x), x)
    rule3067 = ReplacementRule(pattern3067, replacement3067)
    pattern3068 = Pattern(Integral((WC('a', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))) + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('n', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons1440, cons375, cons168, cons88, cons322)
    def replacement3068(p, m, b, d, c, n, a, x):
        rubi.append(3068)
        return Dist(a/(a**S(2) + b**S(2)), Int((a*cos(c + d*x) + b*sin(c + d*x))**(p + S(1))*sin(c + d*x)**n*cos(c + d*x)**(m + S(-1)), x), x) + Dist(b/(a**S(2) + b**S(2)), Int((a*cos(c + d*x) + b*sin(c + d*x))**(p + S(1))*sin(c + d*x)**(n + S(-1))*cos(c + d*x)**m, x), x) - Dist(a*b/(a**S(2) + b**S(2)), Int((a*cos(c + d*x) + b*sin(c + d*x))**p*sin(c + d*x)**(n + S(-1))*cos(c + d*x)**(m + S(-1)), x), x)
    rule3068 = ReplacementRule(pattern3068, replacement3068)
    pattern3069 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1448)
    def replacement3069(b, d, c, a, x, e):
        rubi.append(3069)
        return Simp(-S(2)*(-b*sin(d + e*x) + c*cos(d + e*x))/(e*sqrt(a + b*cos(d + e*x) + c*sin(d + e*x))), x)
    rule3069 = ReplacementRule(pattern3069, replacement3069)
    pattern3070 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1448, cons87, cons88)
    def replacement3070(b, d, c, a, n, x, e):
        rubi.append(3070)
        return Dist(a*(S(2)*n + S(-1))/n, Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(-1)), x), x) - Simp((-b*sin(d + e*x) + c*cos(d + e*x))*(a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(-1))/(e*n), x)
    rule3070 = ReplacementRule(pattern3070, replacement3070)
    pattern3071 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1448)
    def replacement3071(b, d, c, a, x, e):
        rubi.append(3071)
        return -Simp((-a*sin(d + e*x) + c)/(c*e*(-b*sin(d + e*x) + c*cos(d + e*x))), x)
    rule3071 = ReplacementRule(pattern3071, replacement3071)
    pattern3072 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1448)
    def replacement3072(b, d, c, a, x, e):
        rubi.append(3072)
        return Int(S(1)/sqrt(a + sqrt(b**S(2) + c**S(2))*cos(d + e*x - ArcTan(b, c))), x)
    rule3072 = ReplacementRule(pattern3072, replacement3072)
    pattern3073 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1448, cons87, cons89)
    def replacement3073(b, d, c, a, n, x, e):
        rubi.append(3073)
        return Dist((n + S(1))/(a*(S(2)*n + S(1))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1)), x), x) + Simp((-b*sin(d + e*x) + c*cos(d + e*x))*(a + b*cos(d + e*x) + c*sin(d + e*x))**n/(a*e*(S(2)*n + S(1))), x)
    rule3073 = ReplacementRule(pattern3073, replacement3073)
    pattern3074 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1449)
    def replacement3074(b, d, c, a, x, e):
        rubi.append(3074)
        return Dist(b/(c*e), Subst(Int(sqrt(a + x)/x, x), x, b*cos(d + e*x) + c*sin(d + e*x)), x)
    rule3074 = ReplacementRule(pattern3074, replacement3074)
    pattern3075 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1450, cons1451)
    def replacement3075(b, d, c, a, x, e):
        rubi.append(3075)
        return Int(sqrt(a + sqrt(b**S(2) + c**S(2))*cos(d + e*x - ArcTan(b, c))), x)
    rule3075 = ReplacementRule(pattern3075, replacement3075)
    pattern3076 = Pattern(Integral(sqrt(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1452, cons1450, cons1453)
    def replacement3076(b, d, c, a, x, e):
        rubi.append(3076)
        return Dist(sqrt(a + b*cos(d + e*x) + c*sin(d + e*x))/sqrt((a + b*cos(d + e*x) + c*sin(d + e*x))/(a + sqrt(b**S(2) + c**S(2)))), Int(sqrt(a/(a + sqrt(b**S(2) + c**S(2))) + sqrt(b**S(2) + c**S(2))*cos(d + e*x - ArcTan(b, c))/(a + sqrt(b**S(2) + c**S(2)))), x), x)
    rule3076 = ReplacementRule(pattern3076, replacement3076)
    pattern3077 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1452, cons87, cons165)
    def replacement3077(b, d, c, a, n, x, e):
        rubi.append(3077)
        return Dist(S(1)/n, Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(-2))*Simp(a**S(2)*n + a*b*(S(2)*n + S(-1))*cos(d + e*x) + a*c*(S(2)*n + S(-1))*sin(d + e*x) + (b**S(2) + c**S(2))*(n + S(-1)), x), x), x) - Simp((-b*sin(d + e*x) + c*cos(d + e*x))*(a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(-1))/(e*n), x)
    rule3077 = ReplacementRule(pattern3077, replacement3077)
    def With3078(b, d, c, a, x, e):
        f = FreeFactors(S(1)/tan(d/S(2) + e*x/S(2)), x)
        rubi.append(3078)
        return -Dist(f/e, Subst(Int(S(1)/(a + c*f*x), x), x, S(1)/(f*tan(d/S(2) + e*x/S(2)))), x)
    pattern3078 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1454)
    rule3078 = ReplacementRule(pattern3078, With3078)
    def With3079(b, d, c, a, x, e):
        f = FreeFactors(tan(Pi/S(4) + d/S(2) + e*x/S(2)), x)
        rubi.append(3079)
        return Dist(f/e, Subst(Int(S(1)/(a + b*f*x), x), x, tan(Pi/S(4) + d/S(2) + e*x/S(2))/f), x)
    pattern3079 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons76)
    rule3079 = ReplacementRule(pattern3079, With3079)
    def With3080(b, d, c, a, x, e):
        f = FreeFactors(S(1)/tan(Pi/S(4) + d/S(2) + e*x/S(2)), x)
        rubi.append(3080)
        return -Dist(f/e, Subst(Int(S(1)/(a + b*f*x), x), x, S(1)/(f*tan(Pi/S(4) + d/S(2) + e*x/S(2)))), x)
    pattern3080 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1455, cons1456)
    rule3080 = ReplacementRule(pattern3080, With3080)
    def With3081(b, d, c, a, x, e):
        f = FreeFactors(tan(d/S(2) + e*x/S(2)), x)
        rubi.append(3081)
        return Dist(S(2)*f/e, Subst(Int(S(1)/(a + b + S(2)*c*f*x + f**S(2)*x**S(2)*(a - b)), x), x, tan(d/S(2) + e*x/S(2))/f), x)
    pattern3081 = Pattern(Integral(S(1)/(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1452)
    rule3081 = ReplacementRule(pattern3081, With3081)
    pattern3082 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1449)
    def replacement3082(b, d, c, a, x, e):
        rubi.append(3082)
        return Dist(b/(c*e), Subst(Int(S(1)/(x*sqrt(a + x)), x), x, b*cos(d + e*x) + c*sin(d + e*x)), x)
    rule3082 = ReplacementRule(pattern3082, replacement3082)
    pattern3083 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1450, cons1451)
    def replacement3083(b, d, c, a, x, e):
        rubi.append(3083)
        return Int(S(1)/sqrt(a + sqrt(b**S(2) + c**S(2))*cos(d + e*x - ArcTan(b, c))), x)
    rule3083 = ReplacementRule(pattern3083, replacement3083)
    pattern3084 = Pattern(Integral(S(1)/sqrt(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1452, cons1450, cons1453)
    def replacement3084(b, d, c, a, x, e):
        rubi.append(3084)
        return Dist(sqrt((a + b*cos(d + e*x) + c*sin(d + e*x))/(a + sqrt(b**S(2) + c**S(2))))/sqrt(a + b*cos(d + e*x) + c*sin(d + e*x)), Int(S(1)/sqrt(a/(a + sqrt(b**S(2) + c**S(2))) + sqrt(b**S(2) + c**S(2))*cos(d + e*x - ArcTan(b, c))/(a + sqrt(b**S(2) + c**S(2)))), x), x)
    rule3084 = ReplacementRule(pattern3084, replacement3084)
    pattern3085 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**(S(-3)/2), x_), cons2, cons3, cons7, cons27, cons48, cons1452)
    def replacement3085(b, d, c, a, x, e):
        rubi.append(3085)
        return Dist(S(1)/(a**S(2) - b**S(2) - c**S(2)), Int(sqrt(a + b*cos(d + e*x) + c*sin(d + e*x)), x), x) + Simp(S(2)*(-b*sin(d + e*x) + c*cos(d + e*x))/(e*sqrt(a + b*cos(d + e*x) + c*sin(d + e*x))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3085 = ReplacementRule(pattern3085, replacement3085)
    pattern3086 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons1452, cons87, cons89, cons1457)
    def replacement3086(b, d, c, a, n, x, e):
        rubi.append(3086)
        return Dist(S(1)/((n + S(1))*(a**S(2) - b**S(2) - c**S(2))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1))*(a*(n + S(1)) - b*(n + S(2))*cos(d + e*x) - c*(n + S(2))*sin(d + e*x)), x), x) + Simp((b*sin(d + e*x) - c*cos(d + e*x))*(a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1))/(e*(n + S(1))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3086 = ReplacementRule(pattern3086, replacement3086)
    pattern3087 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons1449)
    def replacement3087(B, C, e, b, d, c, a, x, A):
        rubi.append(3087)
        return Simp(x*(S(2)*A*a - B*b - C*c)/(S(2)*a**S(2)), x) + Simp((-S(2)*A*a*b**S(2) + a**S(2)*(B*b - C*c) + b**S(2)*(B*b + C*c))*log(RemoveContent(a + b*cos(d + e*x) + c*sin(d + e*x), x))/(S(2)*a**S(2)*b*c*e), x) - Simp((B*b + C*c)*(b*cos(d + e*x) - c*sin(d + e*x))/(S(2)*a*b*c*e), x)
    rule3087 = ReplacementRule(pattern3087, replacement3087)
    pattern3088 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons36, cons1449)
    def replacement3088(C, e, b, d, c, a, x, A):
        rubi.append(3088)
        return Simp(x*(S(2)*A*a - C*c)/(S(2)*a**S(2)), x) - Simp(C*cos(d + e*x)/(S(2)*a*e), x) + Simp((S(2)*A*a*c - C*a**S(2) + C*b**S(2))*log(RemoveContent(a + b*cos(d + e*x) + c*sin(d + e*x), x))/(S(2)*a**S(2)*b*e), x) + Simp(C*c*sin(d + e*x)/(S(2)*a*b*e), x)
    rule3088 = ReplacementRule(pattern3088, replacement3088)
    pattern3089 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))/(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons1449)
    def replacement3089(B, b, d, c, a, A, x, e):
        rubi.append(3089)
        return Simp(x*(S(2)*A*a - B*b)/(S(2)*a**S(2)), x) + Simp(B*sin(d + e*x)/(S(2)*a*e), x) + Simp((-S(2)*A*a*b + B*a**S(2) + B*b**S(2))*log(RemoveContent(a + b*cos(d + e*x) + c*sin(d + e*x), x))/(S(2)*a**S(2)*c*e), x) - Simp(B*b*cos(d + e*x)/(S(2)*a*c*e), x)
    rule3089 = ReplacementRule(pattern3089, replacement3089)
    pattern3090 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons1450, cons1458)
    def replacement3090(B, C, b, d, c, a, A, x, e):
        rubi.append(3090)
        return Simp(x*(B*b + C*c)/(b**S(2) + c**S(2)), x) + Simp((B*c - C*b)*log(a + b*cos(d + e*x) + c*sin(d + e*x))/(e*(b**S(2) + c**S(2))), x)
    rule3090 = ReplacementRule(pattern3090, replacement3090)
    pattern3091 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons36, cons1450, cons1459)
    def replacement3091(C, b, d, c, a, A, x, e):
        rubi.append(3091)
        return Simp(C*c*x/(b**S(2) + c**S(2)), x) - Simp(C*b*log(a + b*cos(d + e*x) + c*sin(d + e*x))/(e*(b**S(2) + c**S(2))), x)
    rule3091 = ReplacementRule(pattern3091, replacement3091)
    pattern3092 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons1450, cons1460)
    def replacement3092(B, b, d, a, c, A, x, e):
        rubi.append(3092)
        return Simp(B*b*x/(b**S(2) + c**S(2)), x) + Simp(B*c*log(a + b*cos(d + e*x) + c*sin(d + e*x))/(e*(b**S(2) + c**S(2))), x)
    rule3092 = ReplacementRule(pattern3092, replacement3092)
    pattern3093 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons1450, cons1461)
    def replacement3093(B, C, b, d, c, a, A, x, e):
        rubi.append(3093)
        return Dist((A*(b**S(2) + c**S(2)) - a*(B*b + C*c))/(b**S(2) + c**S(2)), Int(S(1)/(a + b*cos(d + e*x) + c*sin(d + e*x)), x), x) + Simp(x*(B*b + C*c)/(b**S(2) + c**S(2)), x) + Simp((B*c - C*b)*log(a + b*cos(d + e*x) + c*sin(d + e*x))/(e*(b**S(2) + c**S(2))), x)
    rule3093 = ReplacementRule(pattern3093, replacement3093)
    pattern3094 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons36, cons1450, cons1462)
    def replacement3094(C, b, d, c, a, A, x, e):
        rubi.append(3094)
        return Dist((A*(b**S(2) + c**S(2)) - C*a*c)/(b**S(2) + c**S(2)), Int(S(1)/(a + b*cos(d + e*x) + c*sin(d + e*x)), x), x) - Simp(C*b*log(a + b*cos(d + e*x) + c*sin(d + e*x))/(e*(b**S(2) + c**S(2))), x) + Simp(C*c*(d + e*x)/(e*(b**S(2) + c**S(2))), x)
    rule3094 = ReplacementRule(pattern3094, replacement3094)
    pattern3095 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons1450, cons1463)
    def replacement3095(B, b, d, a, c, A, x, e):
        rubi.append(3095)
        return Dist((A*(b**S(2) + c**S(2)) - B*a*b)/(b**S(2) + c**S(2)), Int(S(1)/(a + b*cos(d + e*x) + c*sin(d + e*x)), x), x) + Simp(B*b*(d + e*x)/(e*(b**S(2) + c**S(2))), x) + Simp(B*c*log(a + b*cos(d + e*x) + c*sin(d + e*x))/(e*(b**S(2) + c**S(2))), x)
    rule3095 = ReplacementRule(pattern3095, replacement3095)
    pattern3096 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons4, cons584, cons1448, cons1464)
    def replacement3096(B, C, b, d, c, n, a, A, x, e):
        rubi.append(3096)
        return Simp((a + b*cos(d + e*x) + c*sin(d + e*x))**n*(B*a*sin(d + e*x) + B*c - C*a*cos(d + e*x) - C*b)/(a*e*(n + S(1))), x)
    rule3096 = ReplacementRule(pattern3096, replacement3096)
    pattern3097 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons36, cons4, cons584, cons1448, cons1465)
    def replacement3097(C, b, d, c, n, a, A, x, e):
        rubi.append(3097)
        return -Simp((C*a*cos(d + e*x) + C*b)*(a + b*cos(d + e*x) + c*sin(d + e*x))**n/(a*e*(n + S(1))), x)
    rule3097 = ReplacementRule(pattern3097, replacement3097)
    pattern3098 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons4, cons584, cons1448, cons1466)
    def replacement3098(B, b, d, c, n, a, A, x, e):
        rubi.append(3098)
        return Simp((B*a*sin(d + e*x) + B*c)*(a + b*cos(d + e*x) + c*sin(d + e*x))**n/(a*e*(n + S(1))), x)
    rule3098 = ReplacementRule(pattern3098, replacement3098)
    pattern3099 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons4, cons584, cons1448, cons1467)
    def replacement3099(B, C, b, d, c, n, a, A, x, e):
        rubi.append(3099)
        return Dist((A*a*(n + S(1)) + n*(B*b + C*c))/(a*(n + S(1))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**n, x), x) + Simp((a + b*cos(d + e*x) + c*sin(d + e*x))**n*(B*a*sin(d + e*x) + B*c - C*a*cos(d + e*x) - C*b)/(a*e*(n + S(1))), x)
    rule3099 = ReplacementRule(pattern3099, replacement3099)
    pattern3100 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons36, cons4, cons584, cons1448, cons1468)
    def replacement3100(C, b, d, c, n, a, A, x, e):
        rubi.append(3100)
        return Dist((A*a*(n + S(1)) + C*c*n)/(a*(n + S(1))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**n, x), x) - Simp((C*a*cos(d + e*x) + C*b)*(a + b*cos(d + e*x) + c*sin(d + e*x))**n/(a*e*(n + S(1))), x)
    rule3100 = ReplacementRule(pattern3100, replacement3100)
    pattern3101 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons4, cons584, cons1448, cons1469)
    def replacement3101(B, b, d, c, n, a, A, x, e):
        rubi.append(3101)
        return Dist((A*a*(n + S(1)) + B*b*n)/(a*(n + S(1))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**n, x), x) + Simp((B*a*sin(d + e*x) + B*c)*(a + b*cos(d + e*x) + c*sin(d + e*x))**n/(a*e*(n + S(1))), x)
    rule3101 = ReplacementRule(pattern3101, replacement3101)
    pattern3102 = Pattern(Integral((WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons3, cons7, cons27, cons48, cons35, cons36, cons584, cons1450, cons1470)
    def replacement3102(B, C, b, d, c, n, x, e):
        rubi.append(3102)
        return Simp((B*c - C*b)*(b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1))/(e*(b**S(2) + c**S(2))*(n + S(1))), x)
    rule3102 = ReplacementRule(pattern3102, replacement3102)
    pattern3103 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*(WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons87, cons88, cons1452)
    def replacement3103(B, C, b, d, c, n, a, A, x, e):
        rubi.append(3103)
        return Dist(S(1)/(a*(n + S(1))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(-1))*Simp(A*a**S(2)*(n + S(1)) + a*n*(B*b + C*c) + (A*a*b*(n + S(1)) + n*(B*a**S(2) - B*c**S(2) + C*b*c))*cos(d + e*x) + (A*a*c*(n + S(1)) + n*(B*b*c + C*a**S(2) - C*b**S(2)))*sin(d + e*x), x), x), x) + Simp((a + b*cos(d + e*x) + c*sin(d + e*x))**n*(B*a*sin(d + e*x) + B*c - C*a*cos(d + e*x) - C*b)/(a*e*(n + S(1))), x)
    rule3103 = ReplacementRule(pattern3103, replacement3103)
    pattern3104 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons36, cons87, cons88, cons1452)
    def replacement3104(C, b, d, c, n, a, A, x, e):
        rubi.append(3104)
        return Dist(S(1)/(a*(n + S(1))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(-1))*Simp(A*a**S(2)*(n + S(1)) + C*a*c*n + (A*a*b*(n + S(1)) + C*b*c*n)*cos(d + e*x) + (A*a*c*(n + S(1)) + C*a**S(2)*n - C*b**S(2)*n)*sin(d + e*x), x), x), x) - Simp((C*a*cos(d + e*x) + C*b)*(a + b*cos(d + e*x) + c*sin(d + e*x))**n/(a*e*(n + S(1))), x)
    rule3104 = ReplacementRule(pattern3104, replacement3104)
    pattern3105 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons87, cons88, cons1452)
    def replacement3105(B, b, d, c, n, a, A, x, e):
        rubi.append(3105)
        return Dist(S(1)/(a*(n + S(1))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(-1))*Simp(A*a**S(2)*(n + S(1)) + B*a*b*n + (A*a*c*(n + S(1)) + B*b*c*n)*sin(d + e*x) + (A*a*b*(n + S(1)) + B*a**S(2)*n - B*c**S(2)*n)*cos(d + e*x), x), x), x) + Simp((B*a*sin(d + e*x) + B*c)*(a + b*cos(d + e*x) + c*sin(d + e*x))**n/(a*e*(n + S(1))), x)
    rule3105 = ReplacementRule(pattern3105, replacement3105)
    pattern3106 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/sqrt(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons1471, cons1245)
    def replacement3106(B, C, e, b, d, c, a, x, A):
        rubi.append(3106)
        return Dist(B/b, Int(sqrt(a + b*cos(d + e*x) + c*sin(d + e*x)), x), x) + Dist((A*b - B*a)/b, Int(S(1)/sqrt(a + b*cos(d + e*x) + c*sin(d + e*x)), x), x)
    rule3106 = ReplacementRule(pattern3106, replacement3106)
    pattern3107 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons1452, cons1472)
    def replacement3107(B, C, b, d, c, a, A, x, e):
        rubi.append(3107)
        return Simp((B*c - C*b + (-A*b + B*a)*sin(d + e*x) - (-A*c + C*a)*cos(d + e*x))/(e*(a + b*cos(d + e*x) + c*sin(d + e*x))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3107 = ReplacementRule(pattern3107, replacement3107)
    pattern3108 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons36, cons1452, cons1473)
    def replacement3108(C, b, d, c, a, A, x, e):
        rubi.append(3108)
        return -Simp((A*b*sin(d + e*x) + C*b + (-A*c + C*a)*cos(d + e*x))/(e*(a + b*cos(d + e*x) + c*sin(d + e*x))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3108 = ReplacementRule(pattern3108, replacement3108)
    pattern3109 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons1452, cons1474)
    def replacement3109(B, b, d, a, c, A, x, e):
        rubi.append(3109)
        return Simp((A*c*cos(d + e*x) + B*c + (-A*b + B*a)*sin(d + e*x))/(e*(a + b*cos(d + e*x) + c*sin(d + e*x))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3109 = ReplacementRule(pattern3109, replacement3109)
    pattern3110 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons1452, cons1475)
    def replacement3110(B, C, b, d, c, a, A, x, e):
        rubi.append(3110)
        return Dist((A*a - B*b - C*c)/(a**S(2) - b**S(2) - c**S(2)), Int(S(1)/(a + b*cos(d + e*x) + c*sin(d + e*x)), x), x) + Simp((B*c - C*b + (-A*b + B*a)*sin(d + e*x) - (-A*c + C*a)*cos(d + e*x))/(e*(a + b*cos(d + e*x) + c*sin(d + e*x))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3110 = ReplacementRule(pattern3110, replacement3110)
    pattern3111 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons36, cons1452, cons1476)
    def replacement3111(C, b, d, c, a, A, x, e):
        rubi.append(3111)
        return Dist((A*a - C*c)/(a**S(2) - b**S(2) - c**S(2)), Int(S(1)/(a + b*cos(d + e*x) + c*sin(d + e*x)), x), x) - Simp((A*b*sin(d + e*x) + C*b + (-A*c + C*a)*cos(d + e*x))/(e*(a + b*cos(d + e*x) + c*sin(d + e*x))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3111 = ReplacementRule(pattern3111, replacement3111)
    pattern3112 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons1452, cons1477)
    def replacement3112(B, b, d, a, c, A, x, e):
        rubi.append(3112)
        return Dist((A*a - B*b)/(a**S(2) - b**S(2) - c**S(2)), Int(S(1)/(a + b*cos(d + e*x) + c*sin(d + e*x)), x), x) + Simp((A*c*cos(d + e*x) + B*c + (-A*b + B*a)*sin(d + e*x))/(e*(a + b*cos(d + e*x) + c*sin(d + e*x))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3112 = ReplacementRule(pattern3112, replacement3112)
    pattern3113 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons36, cons87, cons89, cons1452, cons1442)
    def replacement3113(B, C, b, d, c, a, n, A, x, e):
        rubi.append(3113)
        return Dist(S(1)/((n + S(1))*(a**S(2) - b**S(2) - c**S(2))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1))*Simp((n + S(1))*(A*a - B*b - C*c) + (n + S(2))*(-A*b + B*a)*cos(d + e*x) + (n + S(2))*(-A*c + C*a)*sin(d + e*x), x), x), x) - Simp((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1))*(B*c - C*b + (-A*b + B*a)*sin(d + e*x) - (-A*c + C*a)*cos(d + e*x))/(e*(n + S(1))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3113 = ReplacementRule(pattern3113, replacement3113)
    pattern3114 = Pattern(Integral((WC('A', S(0)) + WC('C', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons36, cons87, cons89, cons1452, cons1442)
    def replacement3114(C, b, d, c, a, n, A, x, e):
        rubi.append(3114)
        return Dist(S(1)/((n + S(1))*(a**S(2) - b**S(2) - c**S(2))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1))*Simp(-A*b*(n + S(2))*cos(d + e*x) + (n + S(1))*(A*a - C*c) + (n + S(2))*(-A*c + C*a)*sin(d + e*x), x), x), x) + Simp((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1))*(A*b*sin(d + e*x) + C*b + (-A*c + C*a)*cos(d + e*x))/(e*(n + S(1))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3114 = ReplacementRule(pattern3114, replacement3114)
    pattern3115 = Pattern(Integral((WC('A', S(0)) + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons87, cons89, cons1452, cons1442)
    def replacement3115(B, b, d, a, c, n, A, x, e):
        rubi.append(3115)
        return Dist(S(1)/((n + S(1))*(a**S(2) - b**S(2) - c**S(2))), Int((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1))*Simp(-A*c*(n + S(2))*sin(d + e*x) + (n + S(1))*(A*a - B*b) + (n + S(2))*(-A*b + B*a)*cos(d + e*x), x), x), x) - Simp((a + b*cos(d + e*x) + c*sin(d + e*x))**(n + S(1))*(A*c*cos(d + e*x) + B*c + (-A*b + B*a)*sin(d + e*x))/(e*(n + S(1))*(a**S(2) - b**S(2) - c**S(2))), x)
    rule3115 = ReplacementRule(pattern3115, replacement3115)
    pattern3116 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement3116(b, d, c, a, x, e):
        rubi.append(3116)
        return Int(cos(d + e*x)/(a*cos(d + e*x) + b + c*sin(d + e*x)), x)
    rule3116 = ReplacementRule(pattern3116, replacement3116)
    pattern3117 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons1043)
    def replacement3117(b, d, c, a, x, e):
        rubi.append(3117)
        return Int(sin(d + e*x)/(a*sin(d + e*x) + b + c*cos(d + e*x)), x)
    rule3117 = ReplacementRule(pattern3117, replacement3117)
    pattern3118 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons85)
    def replacement3118(b, d, a, n, c, x, e):
        rubi.append(3118)
        return Int((a*cos(d + e*x) + b + c*sin(d + e*x))**n, x)
    rule3118 = ReplacementRule(pattern3118, replacement3118)
    pattern3119 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons85)
    def replacement3119(b, d, c, a, n, x, e):
        rubi.append(3119)
        return Int((a*sin(d + e*x) + b + c*cos(d + e*x))**n, x)
    rule3119 = ReplacementRule(pattern3119, replacement3119)
    pattern3120 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**n_*cos(x_*WC('e', S(1)) + WC('d', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons23)
    def replacement3120(b, d, c, a, n, x, e):
        rubi.append(3120)
        return Dist((a + b/cos(d + e*x) + c*tan(d + e*x))**n*(a*cos(d + e*x) + b + c*sin(d + e*x))**(-n)*cos(d + e*x)**n, Int((a*cos(d + e*x) + b + c*sin(d + e*x))**n, x), x)
    rule3120 = ReplacementRule(pattern3120, replacement3120)
    pattern3121 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**n_*sin(x_*WC('e', S(1)) + WC('d', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons23)
    def replacement3121(b, d, c, a, n, x, e):
        rubi.append(3121)
        return Dist((a + b/sin(d + e*x) + c/tan(d + e*x))**n*(a*sin(d + e*x) + b + c*cos(d + e*x))**(-n)*sin(d + e*x)**n, Int((a*sin(d + e*x) + b + c*cos(d + e*x))**n, x), x)
    rule3121 = ReplacementRule(pattern3121, replacement3121)
    pattern3122 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**m_*(S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1255, cons85)
    def replacement3122(m, b, d, a, n, c, x, e):
        rubi.append(3122)
        return Int((a*cos(d + e*x) + b + c*sin(d + e*x))**(-n), x)
    rule3122 = ReplacementRule(pattern3122, replacement3122)
    pattern3123 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**m_*(S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1255, cons85)
    def replacement3123(m, b, d, a, n, c, x, e):
        rubi.append(3123)
        return Int((a*sin(d + e*x) + b + c*cos(d + e*x))**(-n), x)
    rule3123 = ReplacementRule(pattern3123, replacement3123)
    pattern3124 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0))))**m_*(S(1)/cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1255, cons23)
    def replacement3124(m, b, d, a, n, c, x, e):
        rubi.append(3124)
        return Dist((a + b/cos(d + e*x) + c*tan(d + e*x))**(-n)*(a*cos(d + e*x) + b + c*sin(d + e*x))**n*(S(1)/cos(d + e*x))**n, Int((a*cos(d + e*x) + b + c*sin(d + e*x))**(-n), x), x)
    rule3124 = ReplacementRule(pattern3124, replacement3124)
    pattern3125 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))/sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))/tan(x_*WC('e', S(1)) + WC('d', S(0))))**m_*(S(1)/sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons1255, cons23)
    def replacement3125(m, b, d, a, n, c, x, e):
        rubi.append(3125)
        return Dist((a + b/sin(d + e*x) + c/tan(d + e*x))**(-n)*(a*sin(d + e*x) + b + c*cos(d + e*x))**n*(S(1)/sin(d + e*x))**n, Int((a*sin(d + e*x) + b + c*cos(d + e*x))**(-n), x), x)
    rule3125 = ReplacementRule(pattern3125, replacement3125)
    pattern3126 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons3, cons7, cons27, cons13, cons146)
    def replacement3126(p, b, d, c, x):
        rubi.append(3126)
        return Dist(b*(S(2)*p + S(-1))/(S(2)*p), Int((b*sin(c + d*x)**S(2))**(p + S(-1)), x), x) - Simp((b*sin(c + d*x)**S(2))**p/(S(2)*d*p*tan(c + d*x)), x)
    rule3126 = ReplacementRule(pattern3126, replacement3126)
    pattern3127 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons3, cons7, cons27, cons13, cons146)
    def replacement3127(p, b, d, c, x):
        rubi.append(3127)
        return Dist(b*(S(2)*p + S(-1))/(S(2)*p), Int((b*cos(c + d*x)**S(2))**(p + S(-1)), x), x) + Simp((b*cos(c + d*x)**S(2))**p*tan(c + d*x)/(S(2)*d*p), x)
    rule3127 = ReplacementRule(pattern3127, replacement3127)
    pattern3128 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons3, cons7, cons27, cons13, cons137)
    def replacement3128(p, b, d, c, x):
        rubi.append(3128)
        return Dist(S(2)*(p + S(1))/(b*(S(2)*p + S(1))), Int((b*sin(c + d*x)**S(2))**(p + S(1)), x), x) + Simp((b*sin(c + d*x)**S(2))**(p + S(1))/(b*d*(S(2)*p + S(1))*tan(c + d*x)), x)
    rule3128 = ReplacementRule(pattern3128, replacement3128)
    pattern3129 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons3, cons7, cons27, cons13, cons137)
    def replacement3129(p, b, d, c, x):
        rubi.append(3129)
        return Dist(S(2)*(p + S(1))/(b*(S(2)*p + S(1))), Int((b*cos(c + d*x)**S(2))**(p + S(1)), x), x) - Simp((b*cos(c + d*x)**S(2))**(p + S(1))*tan(c + d*x)/(b*d*(S(2)*p + S(1))), x)
    rule3129 = ReplacementRule(pattern3129, replacement3129)
    pattern3130 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons1454, cons38)
    def replacement3130(p, b, d, c, a, x):
        rubi.append(3130)
        return Dist(a**p, Int(cos(c + d*x)**(S(2)*p), x), x)
    rule3130 = ReplacementRule(pattern3130, replacement3130)
    pattern3131 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons1454, cons38)
    def replacement3131(p, b, d, c, a, x):
        rubi.append(3131)
        return Dist(a**p, Int(sin(c + d*x)**(S(2)*p), x), x)
    rule3131 = ReplacementRule(pattern3131, replacement3131)
    pattern3132 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1454, cons147)
    def replacement3132(p, b, d, c, a, x):
        rubi.append(3132)
        return Int((a*cos(c + d*x)**S(2))**p, x)
    rule3132 = ReplacementRule(pattern3132, replacement3132)
    pattern3133 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1454, cons147)
    def replacement3133(p, b, d, c, a, x):
        rubi.append(3133)
        return Int((a*sin(c + d*x)**S(2))**p, x)
    rule3133 = ReplacementRule(pattern3133, replacement3133)
    def With3134(p, b, d, c, a, x):
        e = FreeFactors(tan(c + d*x), x)
        rubi.append(3134)
        return Dist(e/d, Subst(Int((a + e**S(2)*x**S(2)*(a + b))**p*(e**S(2)*x**S(2) + S(1))**(-p + S(-1)), x), x, tan(c + d*x)/e), x)
    pattern3134 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons38)
    rule3134 = ReplacementRule(pattern3134, With3134)
    def With3135(p, b, d, c, a, x):
        e = FreeFactors(tan(c + d*x), x)
        rubi.append(3135)
        return Dist(e/d, Subst(Int((e**S(2)*x**S(2) + S(1))**(-p + S(-1))*(a*e**S(2)*x**S(2) + a + b)**p, x), x, tan(c + d*x)/e), x)
    pattern3135 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons38)
    rule3135 = ReplacementRule(pattern3135, With3135)
    pattern3136 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1478, cons147)
    def replacement3136(p, b, d, c, a, x):
        rubi.append(3136)
        return Dist(S(2)**(-p), Int((S(2)*a - b*cos(S(2)*c + S(2)*d*x) + b)**p, x), x)
    rule3136 = ReplacementRule(pattern3136, replacement3136)
    pattern3137 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1478, cons147)
    def replacement3137(p, b, d, c, a, x):
        rubi.append(3137)
        return Dist(S(2)**(-p), Int((S(2)*a + b*cos(S(2)*c + S(2)*d*x) + b)**p, x), x)
    rule3137 = ReplacementRule(pattern3137, replacement3137)
    pattern3138 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_, x_), cons2, cons3, cons7, cons27, cons85, cons128)
    def replacement3138(p, b, d, c, a, n, x):
        rubi.append(3138)
        return Int((a + b*sin(c + d*x)**n)**p, x)
    rule3138 = ReplacementRule(pattern3138, replacement3138)
    pattern3139 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_, x_), cons2, cons3, cons7, cons27, cons85, cons128)
    def replacement3139(p, b, d, c, n, a, x):
        rubi.append(3139)
        return Int((a + b*cos(c + d*x)**n)**p, x)
    rule3139 = ReplacementRule(pattern3139, replacement3139)
    def With3140(p, b, d, c, a, n, x):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(3140)
        return -Dist(f/d, Subst(Int((f**S(2)*x**S(2) + S(1))**(-n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b, x)**p, x), x, S(1)/(f*tan(c + d*x))), x)
    pattern3140 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_, x_), cons2, cons3, cons7, cons27, cons1479, cons38, cons137)
    rule3140 = ReplacementRule(pattern3140, With3140)
    def With3141(p, b, d, c, n, a, x):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(3141)
        return Dist(f/d, Subst(Int((f**S(2)*x**S(2) + S(1))**(-n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b, x)**p, x), x, tan(c + d*x)/f), x)
    pattern3141 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_, x_), cons2, cons3, cons7, cons27, cons1479, cons38, cons137)
    rule3141 = ReplacementRule(pattern3141, With3141)
    pattern3142 = Pattern(Integral(u_*(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons1454, cons38)
    def replacement3142(p, u, b, d, c, a, x):
        rubi.append(3142)
        return Dist(a**p, Int(ActivateTrig(u)*cos(c + d*x)**(S(2)*p), x), x)
    rule3142 = ReplacementRule(pattern3142, replacement3142)
    pattern3143 = Pattern(Integral(u_*(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons1454, cons38)
    def replacement3143(p, u, b, d, c, a, x):
        rubi.append(3143)
        return Dist(a**p, Int(ActivateTrig(u)*sin(c + d*x)**(S(2)*p), x), x)
    rule3143 = ReplacementRule(pattern3143, replacement3143)
    pattern3144 = Pattern(Integral(u_*(a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1454, cons147)
    def replacement3144(p, u, b, d, c, a, x):
        rubi.append(3144)
        return Dist((a*cos(c + d*x)**S(2))**p*cos(c + d*x)**(-S(2)*p), Int(ActivateTrig(u)*cos(c + d*x)**(S(2)*p), x), x)
    rule3144 = ReplacementRule(pattern3144, replacement3144)
    pattern3145 = Pattern(Integral(u_*(a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**S(2))**p_, x_), cons2, cons3, cons7, cons27, cons5, cons1454, cons147)
    def replacement3145(p, u, b, d, c, a, x):
        rubi.append(3145)
        return Dist((a*sin(c + d*x)**S(2))**p*sin(c + d*x)**(-S(2)*p), Int(ActivateTrig(u)*sin(c + d*x)**(S(2)*p), x), x)
    rule3145 = ReplacementRule(pattern3145, replacement3145)
    def With3146(p, m, b, d, c, a, n, x):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(3146)
        return -Dist(f/d, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b, x)**p, x), x, S(1)/(f*tan(c + d*x))), x)
    pattern3146 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1479, cons1480, cons38)
    rule3146 = ReplacementRule(pattern3146, With3146)
    def With3147(p, m, b, d, c, n, a, x):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(3147)
        return Dist(f/d, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b, x)**p, x), x, tan(c + d*x)/f), x)
    pattern3147 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1479, cons1480, cons38)
    rule3147 = ReplacementRule(pattern3147, With3147)
    def With3148(p, m, b, d, c, a, n, x):
        f = FreeFactors(cos(c + d*x), x)
        rubi.append(3148)
        return -Dist(f/d, Subst(Int((-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*ExpandToSum(a + b*(-f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p, x), x, cos(c + d*x)/f), x)
    pattern3148 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons5, cons1479, cons1481)
    rule3148 = ReplacementRule(pattern3148, With3148)
    def With3149(p, m, b, d, c, n, a, x):
        f = FreeFactors(sin(c + d*x), x)
        rubi.append(3149)
        return Dist(f/d, Subst(Int((-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*ExpandToSum(a + b*(-f**S(2)*x**S(2) + S(1))**(n/S(2)), x)**p, x), x, sin(c + d*x)/f), x)
    pattern3149 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons5, cons1479, cons1481)
    rule3149 = ReplacementRule(pattern3149, With3149)
    pattern3150 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons375)
    def replacement3150(p, m, b, d, c, a, n, x):
        rubi.append(3150)
        return Int(ExpandTrig((a + b*sin(c + d*x)**n)**p*sin(c + d*x)**m, x), x)
    rule3150 = ReplacementRule(pattern3150, replacement3150)
    pattern3151 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons375)
    def replacement3151(p, m, b, d, c, n, a, x):
        rubi.append(3151)
        return Int(ExpandTrig((a + b*cos(c + d*x)**n)**p*cos(c + d*x)**m, x), x)
    rule3151 = ReplacementRule(pattern3151, replacement3151)
    def With3152(p, m, b, d, c, a, n, x):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(3152)
        return Dist(f/d, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b*f**n*x**n, x)**p, x), x, tan(c + d*x)/f), x)
    pattern3152 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1480, cons1479, cons38)
    rule3152 = ReplacementRule(pattern3152, With3152)
    def With3153(p, m, b, d, c, n, a, x):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(3153)
        return -Dist(f/d, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b*f**n*x**n, x)**p, x), x, S(1)/(f*tan(c + d*x))), x)
    pattern3153 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1480, cons1479, cons38)
    rule3153 = ReplacementRule(pattern3153, With3153)
    pattern3154 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1480, cons1482, cons38, cons168)
    def replacement3154(p, m, b, d, c, a, n, x):
        rubi.append(3154)
        return Int((a + b*sin(c + d*x)**n)**p*(-sin(c + d*x)**S(2) + S(1))**(m/S(2)), x)
    rule3154 = ReplacementRule(pattern3154, replacement3154)
    pattern3155 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1480, cons1482, cons38, cons168)
    def replacement3155(p, m, b, d, c, n, a, x):
        rubi.append(3155)
        return Int((a + b*cos(c + d*x)**n)**p*(-cos(c + d*x)**S(2) + S(1))**(m/S(2)), x)
    rule3155 = ReplacementRule(pattern3155, replacement3155)
    pattern3156 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*cos(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1480, cons1482, cons38, cons267, cons137)
    def replacement3156(p, m, b, d, c, a, n, x):
        rubi.append(3156)
        return Int(ExpandTrig((a + b*sin(c + d*x)**n)**p*(-sin(c + d*x)**S(2) + S(1))**(m/S(2)), x), x)
    rule3156 = ReplacementRule(pattern3156, replacement3156)
    pattern3157 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**p_*sin(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons1480, cons1482, cons38, cons267, cons137)
    def replacement3157(p, m, b, d, c, n, a, x):
        rubi.append(3157)
        return Int(ExpandTrig((a + b*cos(c + d*x)**n)**p*(-cos(c + d*x)**S(2) + S(1))**(m/S(2)), x), x)
    rule3157 = ReplacementRule(pattern3157, replacement3157)
    def With3158(p, m, b, d, c, a, n, x, e):
        f = FreeFactors(sin(c + d*x), x)
        rubi.append(3158)
        return Dist(f/d, Subst(Int((a + b*(e*f*x)**n)**p*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2), x), x, sin(c + d*x)/f), x)
    pattern3158 = Pattern(Integral((a_ + (WC('e', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1481)
    rule3158 = ReplacementRule(pattern3158, With3158)
    def With3159(p, m, b, d, c, n, a, x, e):
        f = FreeFactors(cos(c + d*x), x)
        rubi.append(3159)
        return -Dist(f/d, Subst(Int((a + b*(e*f*x)**n)**p*(-f**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2), x), x, cos(c + d*x)/f), x)
    pattern3159 = Pattern(Integral((a_ + (WC('e', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons1481)
    rule3159 = ReplacementRule(pattern3159, With3159)
    def With3160(p, m, b, d, c, a, n, x, e):
        f = FreeFactors(sin(c + d*x), x)
        rubi.append(3160)
        return Dist(f**(m + S(1))/d, Subst(Int(x**m*(a + b*(e*f*x)**n)**p*(-f**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1)/2), x), x, sin(c + d*x)/f), x)
    pattern3160 = Pattern(Integral((a_ + (WC('e', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1481, cons246)
    rule3160 = ReplacementRule(pattern3160, With3160)
    def With3161(p, m, b, d, c, n, a, x, e):
        f = FreeFactors(cos(c + d*x), x)
        rubi.append(3161)
        return -Dist(f**(m + S(1))/d, Subst(Int(x**m*(a + b*(e*f*x)**n)**p*(-f**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1)/2), x), x, cos(c + d*x)/f), x)
    pattern3161 = Pattern(Integral((a_ + (WC('e', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))))**n_*WC('b', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons1481, cons246)
    rule3161 = ReplacementRule(pattern3161, With3161)
    def With3162(p, m, b, d, c, a, n, x):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(3162)
        return Dist(f**(m + S(1))/d, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b*f**n*x**n, x)**p, x), x, tan(c + d*x)/f), x)
    pattern3162 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**WC('p', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons21, cons1483, cons1479, cons38)
    rule3162 = ReplacementRule(pattern3162, With3162)
    def With3163(p, m, b, d, c, n, a, x):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(3163)
        return -Dist(f**(m + S(1))/d, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b*f**n*x**n, x)**p, x), x, S(1)/(f*tan(c + d*x))), x)
    pattern3163 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**WC('p', S(1))*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons21, cons1483, cons1479, cons38)
    rule3163 = ReplacementRule(pattern3163, With3163)
    def With3164(p, m, b, d, c, a, n, x):
        f = FreeFactors(tan(c + d*x), x)
        rubi.append(3164)
        return Dist(f**(m + S(1))/d, Subst(Int(x**m*((f**S(2)*x**S(2) + S(1))**(-n/S(2))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b*f**n*x**n, x))**p/(f**S(2)*x**S(2) + S(1)), x), x, tan(c + d*x)/f), x)
    pattern3164 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**WC('p', S(1))*tan(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons21, cons5, cons1483, cons1479, cons147)
    rule3164 = ReplacementRule(pattern3164, With3164)
    def With3165(p, m, b, d, c, n, a, x):
        f = FreeFactors(S(1)/tan(c + d*x), x)
        rubi.append(3165)
        return -Dist(f**(m + S(1))/d, Subst(Int(x**m*((f**S(2)*x**S(2) + S(1))**(-n/S(2))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + b*f**n*x**n, x))**p/(f**S(2)*x**S(2) + S(1)), x), x, S(1)/(f*tan(c + d*x))), x)
    pattern3165 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0)))**n_)**WC('p', S(1))*(S(1)/tan(x_*WC('d', S(1)) + WC('c', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons21, cons5, cons1483, cons1479, cons147)
    rule3165 = ReplacementRule(pattern3165, With3165)
    def With3166(p, m, b, d, c, a, n, x, q, e):
        f = FreeFactors(S(1)/tan(d + e*x), x)
        rubi.append(3166)
        return -Dist(f/e, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*q/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(q/S(2)) + b*(f**S(2)*x**S(2) + S(1))**(-p/S(2) + q/S(2)) + c, x)**n, x), x, S(1)/(f*tan(d + e*x))), x)
    pattern3166 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**p_ + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**q_)**n_*sin(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons1480, cons1484, cons1485, cons85, cons1486)
    rule3166 = ReplacementRule(pattern3166, With3166)
    def With3167(p, m, b, d, c, a, n, x, q, e):
        f = FreeFactors(tan(d + e*x), x)
        rubi.append(3167)
        return Dist(f/e, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*q/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(q/S(2)) + b*(f**S(2)*x**S(2) + S(1))**(-p/S(2) + q/S(2)) + c, x)**n, x), x, tan(d + e*x)/f), x)
    pattern3167 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**p_ + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**q_)**n_*cos(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons1480, cons1484, cons1485, cons85, cons1486)
    rule3167 = ReplacementRule(pattern3167, With3167)
    def With3168(p, m, b, d, c, a, n, x, q, e):
        f = FreeFactors(S(1)/tan(d + e*x), x)
        rubi.append(3168)
        return -Dist(f/e, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(p/S(2)) + b*f**p*x**p + c*(f**S(2)*x**S(2) + S(1))**(p/S(2) - q/S(2)), x)**n, x), x, S(1)/(f*tan(d + e*x))), x)
    pattern3168 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**p_ + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**q_)**n_*sin(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons1480, cons1484, cons1485, cons85, cons1487)
    rule3168 = ReplacementRule(pattern3168, With3168)
    def With3169(p, m, b, d, c, a, n, x, q, e):
        f = FreeFactors(tan(d + e*x), x)
        rubi.append(3169)
        return Dist(f/e, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p/S(2) + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**(p/S(2)) + b*f**p*x**p + c*(f**S(2)*x**S(2) + S(1))**(p/S(2) - q/S(2)), x)**n, x), x, tan(d + e*x)/f), x)
    pattern3169 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**p_ + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**q_)**n_*cos(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons1480, cons1484, cons1485, cons85, cons1487)
    rule3169 = ReplacementRule(pattern3169, With3169)
    pattern3170 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons45, cons38)
    def replacement3170(p, b, n2, d, a, n, c, x, e):
        rubi.append(3170)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*sin(d + e*x)**n)**(S(2)*p), x), x)
    rule3170 = ReplacementRule(pattern3170, replacement3170)
    pattern3171 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons45, cons38)
    def replacement3171(p, b, n2, d, a, n, c, x, e):
        rubi.append(3171)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*cos(d + e*x)**n)**(S(2)*p), x), x)
    rule3171 = ReplacementRule(pattern3171, replacement3171)
    pattern3172 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons46, cons45, cons147)
    def replacement3172(p, b, n2, d, a, n, c, x, e):
        rubi.append(3172)
        return Dist((b + S(2)*c*sin(d + e*x)**n)**(-S(2)*p)*(a + b*sin(d + e*x)**n + c*sin(d + e*x)**(S(2)*n))**p, Int(u*(b + S(2)*c*sin(d + e*x)**n)**(S(2)*p), x), x)
    rule3172 = ReplacementRule(pattern3172, replacement3172)
    pattern3173 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons4, cons5, cons46, cons45, cons147)
    def replacement3173(p, b, n2, d, a, n, c, x, e):
        rubi.append(3173)
        return Dist((b + S(2)*c*cos(d + e*x)**n)**(-S(2)*p)*(a + b*cos(d + e*x)**n + c*cos(d + e*x)**(S(2)*n))**p, Int(u*(b + S(2)*c*cos(d + e*x)**n)**(S(2)*p), x), x)
    rule3173 = ReplacementRule(pattern3173, replacement3173)
    def With3174(b, n2, d, a, n, c, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(3174)
        return Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*sin(d + e*x)**n - q), x), x) - Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*sin(d + e*x)**n + q), x), x)
    pattern3174 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons226)
    rule3174 = ReplacementRule(pattern3174, With3174)
    def With3175(b, n2, d, a, n, c, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(3175)
        return Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*cos(d + e*x)**n - q), x), x) - Dist(S(2)*c/q, Int(S(1)/(b + S(2)*c*cos(d + e*x)**n + q), x), x)
    pattern3175 = Pattern(Integral(S(1)/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1))), x_), cons2, cons3, cons7, cons27, cons48, cons4, cons46, cons226)
    rule3175 = ReplacementRule(pattern3175, With3175)
    pattern3176 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons45, cons38)
    def replacement3176(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3176)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*sin(d + e*x)**n)**(S(2)*p)*sin(d + e*x)**m, x), x)
    rule3176 = ReplacementRule(pattern3176, replacement3176)
    pattern3177 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons45, cons38)
    def replacement3177(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3177)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*cos(d + e*x)**n)**(S(2)*p)*cos(d + e*x)**m, x), x)
    rule3177 = ReplacementRule(pattern3177, replacement3177)
    pattern3178 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons45, cons147)
    def replacement3178(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3178)
        return Dist((b + S(2)*c*sin(d + e*x)**n)**(-S(2)*p)*(a + b*sin(d + e*x)**n + c*sin(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*sin(d + e*x)**n)**(S(2)*p)*sin(d + e*x)**m, x), x)
    rule3178 = ReplacementRule(pattern3178, replacement3178)
    pattern3179 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons45, cons147)
    def replacement3179(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3179)
        return Dist((b + S(2)*c*cos(d + e*x)**n)**(-S(2)*p)*(a + b*cos(d + e*x)**n + c*cos(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*cos(d + e*x)**n)**(S(2)*p)*cos(d + e*x)**m, x), x)
    rule3179 = ReplacementRule(pattern3179, replacement3179)
    def With3180(p, m, b, n2, d, c, a, n, x, e):
        f = FreeFactors(S(1)/tan(d + e*x), x)
        rubi.append(3180)
        return -Dist(f/e, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p + S(-1))*ExpandToSum(a*(x**S(2) + S(1))**n + b*(x**S(2) + S(1))**(n/S(2)) + c, x)**p, x), x, S(1)/(f*tan(d + e*x))), x)
    pattern3180 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**n_ + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**n2_)**p_*sin(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons1479, cons38)
    rule3180 = ReplacementRule(pattern3180, With3180)
    def With3181(p, m, b, n2, d, a, c, n, x, e):
        f = FreeFactors(tan(d + e*x), x)
        rubi.append(3181)
        return Dist(f/e, Subst(Int((f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p + S(-1))*ExpandToSum(a*(x**S(2) + S(1))**n + b*(x**S(2) + S(1))**(n/S(2)) + c, x)**p, x), x, tan(d + e*x)/f), x)
    pattern3181 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**n_ + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**n2_)**p_*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons1479, cons38)
    rule3181 = ReplacementRule(pattern3181, With3181)
    pattern3182 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons226, cons375)
    def replacement3182(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3182)
        return Int(ExpandTrig((a + b*sin(d + e*x)**n + c*sin(d + e*x)**(S(2)*n))**p*sin(d + e*x)**m, x), x)
    rule3182 = ReplacementRule(pattern3182, replacement3182)
    pattern3183 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons226, cons375)
    def replacement3183(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3183)
        return Int(ExpandTrig((a + b*cos(d + e*x)**n + c*cos(d + e*x)**(S(2)*n))**p*cos(d + e*x)**m, x), x)
    rule3183 = ReplacementRule(pattern3183, replacement3183)
    def With3184(p, m, f, b, n2, d, a, n, c, x, e):
        g = FreeFactors(sin(d + e*x), x)
        rubi.append(3184)
        return Dist(g/e, Subst(Int((-g**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*(a + b*(f*g*x)**n + c*(f*g*x)**(S(2)*n))**p, x), x, sin(d + e*x)/g), x)
    pattern3184 = Pattern(Integral(((WC('f', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (WC('f', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons46, cons1481)
    rule3184 = ReplacementRule(pattern3184, With3184)
    def With3185(p, m, f, b, n2, d, a, n, c, x, e):
        g = FreeFactors(cos(d + e*x), x)
        rubi.append(3185)
        return -Dist(g/e, Subst(Int((-g**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*(a + b*(f*g*x)**n + c*(f*g*x)**(S(2)*n))**p, x), x, cos(d + e*x)/g), x)
    pattern3185 = Pattern(Integral(((WC('f', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n', S(1))*WC('b', S(1)) + (WC('f', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)) + WC('a', S(0)))**WC('p', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons5, cons46, cons1481)
    rule3185 = ReplacementRule(pattern3185, With3185)
    pattern3186 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons1483, cons45, cons38)
    def replacement3186(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3186)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*sin(d + e*x)**n)**(S(2)*p)*cos(d + e*x)**m, x), x)
    rule3186 = ReplacementRule(pattern3186, replacement3186)
    pattern3187 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons1483, cons45, cons38)
    def replacement3187(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3187)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*cos(d + e*x)**n)**(S(2)*p)*sin(d + e*x)**m, x), x)
    rule3187 = ReplacementRule(pattern3187, replacement3187)
    pattern3188 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*cos(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons1483, cons45, cons147)
    def replacement3188(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3188)
        return Dist((b + S(2)*c*sin(d + e*x)**n)**(-S(2)*p)*(a + b*sin(d + e*x)**n + c*sin(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*sin(d + e*x)**n)**(S(2)*p)*cos(d + e*x)**m, x), x)
    rule3188 = ReplacementRule(pattern3188, replacement3188)
    pattern3189 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*sin(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons1483, cons45, cons147)
    def replacement3189(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3189)
        return Dist((b + S(2)*c*cos(d + e*x)**n)**(-S(2)*p)*(a + b*cos(d + e*x)**n + c*cos(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*cos(d + e*x)**n)**(S(2)*p)*sin(d + e*x)**m, x), x)
    rule3189 = ReplacementRule(pattern3189, replacement3189)
    def With3190(p, m, b, n2, d, c, a, n, x, e):
        f = FreeFactors(S(1)/tan(d + e*x), x)
        rubi.append(3190)
        return -Dist(f**(m + S(1))/e, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p + S(-1))*ExpandToSum(a*(x**S(2) + S(1))**n + b*(x**S(2) + S(1))**(n/S(2)) + c, x)**p, x), x, S(1)/(f*tan(d + e*x))), x)
    pattern3190 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**n_ + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**n2_)**WC('p', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons1479, cons38)
    rule3190 = ReplacementRule(pattern3190, With3190)
    def With3191(p, m, b, n2, d, c, a, n, x, e):
        f = FreeFactors(tan(d + e*x), x)
        rubi.append(3191)
        return Dist(f**(m + S(1))/e, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-m/S(2) - n*p + S(-1))*ExpandToSum(a*(x**S(2) + S(1))**n + b*(x**S(2) + S(1))**(n/S(2)) + c, x)**p, x), x, tan(d + e*x)/f), x)
    pattern3191 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**n_ + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**n2_)**WC('p', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons1479, cons38)
    rule3191 = ReplacementRule(pattern3191, With3191)
    pattern3192 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons376)
    def replacement3192(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3192)
        return Int(ExpandTrig((-sin(d + e*x)**S(2) + S(1))**(m/S(2))*(a + b*sin(d + e*x)**n + c*sin(d + e*x)**(S(2)*n))**p, x), x)
    rule3192 = ReplacementRule(pattern3192, replacement3192)
    pattern3193 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons376)
    def replacement3193(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3193)
        return Int(ExpandTrig((-cos(d + e*x)**S(2) + S(1))**(m/S(2))*(a + b*cos(d + e*x)**n + c*cos(d + e*x)**(S(2)*n))**p, x), x)
    rule3193 = ReplacementRule(pattern3193, replacement3193)
    def With3194(p, m, f, b, n2, d, c, a, n, x, e):
        g = FreeFactors(sin(d + e*x), x)
        rubi.append(3194)
        return Dist(g**(m + S(1))/e, Subst(Int(x**m*(-g**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1)/2)*(a + b*(f*g*x)**n + c*(f*g*x)**(S(2)*n))**p, x), x, sin(d + e*x)/g), x)
    pattern3194 = Pattern(Integral((a_ + (WC('f', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_*WC('b', S(1)) + (WC('f', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons1481, cons246)
    rule3194 = ReplacementRule(pattern3194, With3194)
    def With3195(p, m, f, b, n2, d, c, n, a, x, e):
        g = FreeFactors(cos(d + e*x), x)
        rubi.append(3195)
        return -Dist(g**(m + S(1))/e, Subst(Int(x**m*(-g**S(2)*x**S(2) + S(1))**(-m/S(2) + S(-1)/2)*(a + b*(f*g*x)**n + c*(f*g*x)**(S(2)*n))**p, x), x, cos(d + e*x)/g), x)
    pattern3195 = Pattern(Integral((a_ + (WC('f', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))**n_*WC('b', S(1)) + (WC('f', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons1481, cons246)
    rule3195 = ReplacementRule(pattern3195, With3195)
    pattern3196 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons1483, cons45, cons38)
    def replacement3196(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3196)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*sin(d + e*x)**n)**(S(2)*p)*tan(d + e*x)**m, x), x)
    rule3196 = ReplacementRule(pattern3196, replacement3196)
    pattern3197 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons1483, cons45, cons38)
    def replacement3197(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3197)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*cos(d + e*x)**n)**(S(2)*p)*(S(1)/tan(d + e*x))**m, x), x)
    rule3197 = ReplacementRule(pattern3197, replacement3197)
    pattern3198 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*tan(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons1483, cons45, cons147)
    def replacement3198(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3198)
        return Dist((b + S(2)*c*sin(d + e*x)**n)**(-S(2)*p)*(a + b*sin(d + e*x)**n + c*sin(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*sin(d + e*x)**n)**(S(2)*p)*tan(d + e*x)**m, x), x)
    rule3198 = ReplacementRule(pattern3198, replacement3198)
    pattern3199 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons1483, cons45, cons147)
    def replacement3199(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3199)
        return Dist((b + S(2)*c*cos(d + e*x)**n)**(-S(2)*p)*(a + b*cos(d + e*x)**n + c*cos(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*cos(d + e*x)**n)**(S(2)*p)*(S(1)/tan(d + e*x))**m, x), x)
    rule3199 = ReplacementRule(pattern3199, replacement3199)
    def With3200(p, m, b, n2, d, c, a, n, x, e):
        f = FreeFactors(tan(d + e*x), x)
        rubi.append(3200)
        return Dist(f**(m + S(1))/e, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-n*p + S(-1))*ExpandToSum(a*(x**S(2) + S(1))**n + b*x**n*(x**S(2) + S(1))**(n/S(2)) + c*x**(S(2)*n), x)**p, x), x, tan(d + e*x)/f), x)
    pattern3200 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**n_ + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**n2_)**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons46, cons1483, cons226, cons1479, cons38)
    rule3200 = ReplacementRule(pattern3200, With3200)
    def With3201(p, m, b, n2, d, a, c, n, x, e):
        f = FreeFactors(S(1)/tan(d + e*x), x)
        rubi.append(3201)
        return -Dist(f**(m + S(1))/e, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-n*p + S(-1))*ExpandToSum(a*(x**S(2) + S(1))**n + b*x**n*(x**S(2) + S(1))**(n/S(2)) + c*x**(S(2)*n), x)**p, x), x, S(1)/(f*tan(d + e*x))), x)
    pattern3201 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**n_ + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**n2_)**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons46, cons1483, cons226, cons1479, cons38)
    rule3201 = ReplacementRule(pattern3201, With3201)
    pattern3202 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons376)
    def replacement3202(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3202)
        return Int(ExpandTrig((-sin(d + e*x)**S(2) + S(1))**(-m/S(2))*(a + b*sin(d + e*x)**n + c*sin(d + e*x)**(S(2)*n))**p*sin(d + e*x)**m, x), x)
    rule3202 = ReplacementRule(pattern3202, replacement3202)
    pattern3203 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons376)
    def replacement3203(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3203)
        return Int(ExpandTrig((-cos(d + e*x)**S(2) + S(1))**(-m/S(2))*(a + b*cos(d + e*x)**n + c*cos(d + e*x)**(S(2)*n))**p*cos(d + e*x)**m, x), x)
    rule3203 = ReplacementRule(pattern3203, replacement3203)
    def With3204(p, m, f, b, n2, d, c, a, n, x, e):
        g = FreeFactors(sin(d + e*x), x)
        rubi.append(3204)
        return Dist(g**(m + S(1))/e, Subst(Int(x**(-m)*(-g**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*(a + b*(f*g*x)**n + c*(f*g*x)**(S(2)*n))**p, x), x, sin(d + e*x)/g), x)
    pattern3204 = Pattern(Integral((a_ + (WC('f', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**n_*WC('b', S(1)) + (WC('f', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons1481, cons246)
    rule3204 = ReplacementRule(pattern3204, With3204)
    def With3205(p, m, f, b, n2, d, c, n, a, x, e):
        g = FreeFactors(cos(d + e*x), x)
        rubi.append(3205)
        return -Dist(g**(m + S(1))/e, Subst(Int(x**(-m)*(-g**S(2)*x**S(2) + S(1))**(m/S(2) + S(-1)/2)*(a + b*(f*g*x)**n + c*(f*g*x)**(S(2)*n))**p, x), x, cos(d + e*x)/g), x)
    pattern3205 = Pattern(Integral((a_ + (WC('f', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))**n_*WC('b', S(1)) + (WC('f', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))**WC('n2', S(1))*WC('c', S(1)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons4, cons1481, cons246)
    rule3205 = ReplacementRule(pattern3205, With3205)
    pattern3206 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons1483, cons45, cons38)
    def replacement3206(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3206)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*sin(d + e*x)**n)**(S(2)*p)*(S(1)/tan(d + e*x))**m, x), x)
    rule3206 = ReplacementRule(pattern3206, replacement3206)
    pattern3207 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons46, cons1483, cons45, cons38)
    def replacement3207(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3207)
        return Dist(S(4)**(-p)*c**(-p), Int((b + S(2)*c*cos(d + e*x)**n)**(S(2)*p)*tan(d + e*x)**m, x), x)
    rule3207 = ReplacementRule(pattern3207, replacement3207)
    pattern3208 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons1483, cons45, cons147)
    def replacement3208(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3208)
        return Dist((b + S(2)*c*sin(d + e*x)**n)**(-S(2)*p)*(a + b*sin(d + e*x)**n + c*sin(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*sin(d + e*x)**n)**(S(2)*p)*(S(1)/tan(d + e*x))**m, x), x)
    rule3208 = ReplacementRule(pattern3208, replacement3208)
    pattern3209 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**p_*tan(x_*WC('e', S(1)) + WC('d', S(0)))**m_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons46, cons1483, cons45, cons147)
    def replacement3209(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3209)
        return Dist((b + S(2)*c*cos(d + e*x)**n)**(-S(2)*p)*(a + b*cos(d + e*x)**n + c*cos(d + e*x)**(S(2)*n))**p, Int((b + S(2)*c*cos(d + e*x)**n)**(S(2)*p)*tan(d + e*x)**m, x), x)
    rule3209 = ReplacementRule(pattern3209, replacement3209)
    def With3210(p, m, b, n2, d, c, a, n, x, e):
        f = FreeFactors(S(1)/tan(d + e*x), x)
        rubi.append(3210)
        return -Dist(f**(m + S(1))/e, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-n*p + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**n + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + c, x)**p, x), x, S(1)/(f*tan(d + e*x))), x)
    pattern3210 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**n_ + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**n2_)**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons46, cons1479, cons38)
    rule3210 = ReplacementRule(pattern3210, With3210)
    def With3211(p, m, b, n2, d, c, n, a, x, e):
        f = FreeFactors(tan(d + e*x), x)
        rubi.append(3211)
        return Dist(f**(m + S(1))/e, Subst(Int(x**m*(f**S(2)*x**S(2) + S(1))**(-n*p + S(-1))*ExpandToSum(a*(f**S(2)*x**S(2) + S(1))**n + b*(f**S(2)*x**S(2) + S(1))**(n/S(2)) + c, x)**p, x), x, tan(d + e*x)/f), x)
    pattern3211 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**n_ + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**n2_)**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons46, cons1479, cons38)
    rule3211 = ReplacementRule(pattern3211, With3211)
    pattern3212 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*(S(1)/tan(x_*WC('e', S(1)) + WC('d', S(0))))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons376)
    def replacement3212(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3212)
        return Int(ExpandTrig((-sin(d + e*x)**S(2) + S(1))**(m/S(2))*(a + b*sin(d + e*x)**n + c*sin(d + e*x)**(S(2)*n))**p*sin(d + e*x)**(-m), x), x)
    rule3212 = ReplacementRule(pattern3212, replacement3212)
    pattern3213 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n', S(1)) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**WC('n2', S(1)))**WC('p', S(1))*tan(x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons46, cons1480, cons226, cons376)
    def replacement3213(p, m, b, n2, d, a, n, c, x, e):
        rubi.append(3213)
        return Int(ExpandTrig((-cos(d + e*x)**S(2) + S(1))**(m/S(2))*(a + b*cos(d + e*x)**n + c*cos(d + e*x)**(S(2)*n))**p*cos(d + e*x)**(-m), x), x)
    rule3213 = ReplacementRule(pattern3213, replacement3213)
    pattern3214 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons85)
    def replacement3214(B, b, d, c, a, n, A, x, e):
        rubi.append(3214)
        return Dist(S(4)**(-n)*c**(-n), Int((A + B*sin(d + e*x))*(b + S(2)*c*sin(d + e*x))**(S(2)*n), x), x)
    rule3214 = ReplacementRule(pattern3214, replacement3214)
    pattern3215 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons85)
    def replacement3215(B, b, d, c, a, n, A, x, e):
        rubi.append(3215)
        return Dist(S(4)**(-n)*c**(-n), Int((A + B*cos(d + e*x))*(b + S(2)*c*cos(d + e*x))**(S(2)*n), x), x)
    rule3215 = ReplacementRule(pattern3215, replacement3215)
    pattern3216 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons23)
    def replacement3216(B, b, d, c, a, n, A, x, e):
        rubi.append(3216)
        return Dist((b + S(2)*c*sin(d + e*x))**(-S(2)*n)*(a + b*sin(d + e*x) + c*sin(d + e*x)**S(2))**n, Int((A + B*sin(d + e*x))*(b + S(2)*c*sin(d + e*x))**(S(2)*n), x), x)
    rule3216 = ReplacementRule(pattern3216, replacement3216)
    pattern3217 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))*(a_ + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons45, cons23)
    def replacement3217(B, b, d, c, a, n, A, x, e):
        rubi.append(3217)
        return Dist((b + S(2)*c*cos(d + e*x))**(-S(2)*n)*(a + b*cos(d + e*x) + c*cos(d + e*x)**S(2))**n, Int((A + B*cos(d + e*x))*(b + S(2)*c*cos(d + e*x))**(S(2)*n), x), x)
    rule3217 = ReplacementRule(pattern3217, replacement3217)
    def With3218(B, b, d, a, c, A, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(3218)
        return Dist(B - (-S(2)*A*c + B*b)/q, Int(S(1)/(b + S(2)*c*sin(d + e*x) - q), x), x) + Dist(B + (-S(2)*A*c + B*b)/q, Int(S(1)/(b + S(2)*c*sin(d + e*x) + q), x), x)
    pattern3218 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226)
    rule3218 = ReplacementRule(pattern3218, With3218)
    def With3219(B, b, d, c, a, A, x, e):
        q = Rt(-S(4)*a*c + b**S(2), S(2))
        rubi.append(3219)
        return Dist(B - (-S(2)*A*c + B*b)/q, Int(S(1)/(b + S(2)*c*cos(d + e*x) - q), x), x) + Dist(B + (-S(2)*A*c + B*b)/q, Int(S(1)/(b + S(2)*c*cos(d + e*x) + q), x), x)
    pattern3219 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))/(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**S(2)), x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226)
    rule3219 = ReplacementRule(pattern3219, With3219)
    pattern3220 = Pattern(Integral((A_ + WC('B', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*sin(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226, cons85)
    def replacement3220(B, b, d, a, c, n, A, x, e):
        rubi.append(3220)
        return Int(ExpandTrig((A + B*sin(d + e*x))*(a + b*sin(d + e*x) + c*sin(d + e*x)**S(2))**n, x), x)
    rule3220 = ReplacementRule(pattern3220, replacement3220)
    pattern3221 = Pattern(Integral((A_ + WC('B', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0))) + WC('c', S(1))*cos(x_*WC('e', S(1)) + WC('d', S(0)))**S(2))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons34, cons35, cons226, cons85)
    def replacement3221(B, b, d, c, a, n, A, x, e):
        rubi.append(3221)
        return Int(ExpandTrig((A + B*cos(d + e*x))*(a + b*cos(d + e*x) + c*cos(d + e*x)**S(2))**n, x), x)
    rule3221 = ReplacementRule(pattern3221, replacement3221)
    pattern3222 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons31, cons168)
    def replacement3222(m, f, d, c, x, e):
        rubi.append(3222)
        return Dist(d*m/f, Int((c + d*x)**(m + S(-1))*cos(e + f*x), x), x) - Simp((c + d*x)**m*cos(e + f*x)/f, x)
    rule3222 = ReplacementRule(pattern3222, replacement3222)
    pattern3223 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons31, cons168)
    def replacement3223(m, f, d, c, x, e):
        rubi.append(3223)
        return -Dist(d*m/f, Int((c + d*x)**(m + S(-1))*sin(e + f*x), x), x) + Simp((c + d*x)**m*sin(e + f*x)/f, x)
    rule3223 = ReplacementRule(pattern3223, replacement3223)
    pattern3224 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons31, cons94)
    def replacement3224(m, f, d, c, x, e):
        rubi.append(3224)
        return -Dist(f/(d*(m + S(1))), Int((c + d*x)**(m + S(1))*cos(e + f*x), x), x) + Simp((c + d*x)**(m + S(1))*sin(e + f*x)/(d*(m + S(1))), x)
    rule3224 = ReplacementRule(pattern3224, replacement3224)
    pattern3225 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons31, cons94)
    def replacement3225(m, f, d, c, x, e):
        rubi.append(3225)
        return Dist(f/(d*(m + S(1))), Int((c + d*x)**(m + S(1))*sin(e + f*x), x), x) + Simp((c + d*x)**(m + S(1))*cos(e + f*x)/(d*(m + S(1))), x)
    rule3225 = ReplacementRule(pattern3225, replacement3225)
    pattern3226 = Pattern(Integral(sin(x_*WC('f', S(1)) + WC('e', S(0)))/(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons125, cons1116)
    def replacement3226(f, d, c, x, e):
        rubi.append(3226)
        return Simp(SinIntegral(e + f*x)/d, x)
    rule3226 = ReplacementRule(pattern3226, replacement3226)
    pattern3227 = Pattern(Integral(cos(x_*WC('f', S(1)) + WC('e', S(0)))/(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons125, cons1116)
    def replacement3227(f, d, c, x, e):
        rubi.append(3227)
        return Simp(CosIntegral(e + f*x)/d, x)
    rule3227 = ReplacementRule(pattern3227, replacement3227)
    pattern3228 = Pattern(Integral(sin(x_*WC('f', S(1)) + WC('e', S(0)))/(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons125, cons176)
    def replacement3228(f, d, c, x, e):
        rubi.append(3228)
        return Dist(sin((-c*f + d*e)/d), Int(cos(c*f/d + f*x)/(c + d*x), x), x) + Dist(cos((-c*f + d*e)/d), Int(sin(c*f/d + f*x)/(c + d*x), x), x)
    rule3228 = ReplacementRule(pattern3228, replacement3228)
    pattern3229 = Pattern(Integral(cos(x_*WC('f', S(1)) + WC('e', S(0)))/(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons125, cons176)
    def replacement3229(f, d, c, x, e):
        rubi.append(3229)
        return -Dist(sin((-c*f + d*e)/d), Int(sin(c*f/d + f*x)/(c + d*x), x), x) + Dist(cos((-c*f + d*e)/d), Int(cos(c*f/d + f*x)/(c + d*x), x), x)
    rule3229 = ReplacementRule(pattern3229, replacement3229)
    pattern3230 = Pattern(Integral(sin(x_*WC('f', S(1)) + WC('e', S(0)))/sqrt(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons125, cons1116)
    def replacement3230(f, d, c, x, e):
        rubi.append(3230)
        return Dist(S(2)/d, Subst(Int(sin(f*x**S(2)/d), x), x, sqrt(c + d*x)), x)
    rule3230 = ReplacementRule(pattern3230, replacement3230)
    pattern3231 = Pattern(Integral(cos(x_*WC('f', S(1)) + WC('e', S(0)))/sqrt(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons125, cons1116)
    def replacement3231(f, d, c, x, e):
        rubi.append(3231)
        return Dist(S(2)/d, Subst(Int(cos(f*x**S(2)/d), x), x, sqrt(c + d*x)), x)
    rule3231 = ReplacementRule(pattern3231, replacement3231)
    pattern3232 = Pattern(Integral(sin(x_*WC('f', S(1)) + WC('e', S(0)))/sqrt(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons125, cons176)
    def replacement3232(f, d, c, x, e):
        rubi.append(3232)
        return Dist(sin((-c*f + d*e)/d), Int(cos(c*f/d + f*x)/sqrt(c + d*x), x), x) + Dist(cos((-c*f + d*e)/d), Int(sin(c*f/d + f*x)/sqrt(c + d*x), x), x)
    rule3232 = ReplacementRule(pattern3232, replacement3232)
    pattern3233 = Pattern(Integral(cos(x_*WC('f', S(1)) + WC('e', S(0)))/sqrt(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons125, cons176)
    def replacement3233(f, d, c, x, e):
        rubi.append(3233)
        return -Dist(sin((-c*f + d*e)/d), Int(sin(c*f/d + f*x)/sqrt(c + d*x), x), x) + Dist(cos((-c*f + d*e)/d), Int(cos(c*f/d + f*x)/sqrt(c + d*x), x), x)
    rule3233 = ReplacementRule(pattern3233, replacement3233)
    pattern3234 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons21, cons1488)
    def replacement3234(m, f, d, c, x, e):
        rubi.append(3234)
        return Dist(I/S(2), Int((c + d*x)**m*exp(-I*(e + f*x)), x), x) - Dist(I/S(2), Int((c + d*x)**m*exp(I*(e + f*x)), x), x)
    rule3234 = ReplacementRule(pattern3234, replacement3234)
    pattern3235 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))), x_), cons7, cons27, cons48, cons125, cons21, cons1488)
    def replacement3235(m, f, d, c, x, e):
        rubi.append(3235)
        return Dist(S(1)/2, Int((c + d*x)**m*exp(-I*(e + f*x)), x), x) + Dist(S(1)/2, Int((c + d*x)**m*exp(I*(e + f*x)), x), x)
    rule3235 = ReplacementRule(pattern3235, replacement3235)
    pattern3236 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons3, cons7, cons27, cons48, cons125, cons87, cons165)
    def replacement3236(f, b, d, c, n, x, e):
        rubi.append(3236)
        return Dist(b**S(2)*(n + S(-1))/n, Int((b*sin(e + f*x))**(n + S(-2))*(c + d*x), x), x) + Simp(d*(b*sin(e + f*x))**n/(f**S(2)*n**S(2)), x) - Simp(b*(b*sin(e + f*x))**(n + S(-1))*(c + d*x)*cos(e + f*x)/(f*n), x)
    rule3236 = ReplacementRule(pattern3236, replacement3236)
    pattern3237 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons3, cons7, cons27, cons48, cons125, cons87, cons165)
    def replacement3237(f, b, d, c, n, x, e):
        rubi.append(3237)
        return Dist(b**S(2)*(n + S(-1))/n, Int((b*cos(e + f*x))**(n + S(-2))*(c + d*x), x), x) + Simp(d*(b*cos(e + f*x))**n/(f**S(2)*n**S(2)), x) + Simp(b*(b*cos(e + f*x))**(n + S(-1))*(c + d*x)*sin(e + f*x)/(f*n), x)
    rule3237 = ReplacementRule(pattern3237, replacement3237)
    pattern3238 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons3, cons7, cons27, cons48, cons125, cons93, cons165, cons166)
    def replacement3238(m, f, b, d, c, n, x, e):
        rubi.append(3238)
        return Dist(b**S(2)*(n + S(-1))/n, Int((b*sin(e + f*x))**(n + S(-2))*(c + d*x)**m, x), x) - Dist(d**S(2)*m*(m + S(-1))/(f**S(2)*n**S(2)), Int((b*sin(e + f*x))**n*(c + d*x)**(m + S(-2)), x), x) - Simp(b*(b*sin(e + f*x))**(n + S(-1))*(c + d*x)**m*cos(e + f*x)/(f*n), x) + Simp(d*m*(b*sin(e + f*x))**n*(c + d*x)**(m + S(-1))/(f**S(2)*n**S(2)), x)
    rule3238 = ReplacementRule(pattern3238, replacement3238)
    pattern3239 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons3, cons7, cons27, cons48, cons125, cons93, cons165, cons166)
    def replacement3239(m, f, b, d, c, n, x, e):
        rubi.append(3239)
        return Dist(b**S(2)*(n + S(-1))/n, Int((b*cos(e + f*x))**(n + S(-2))*(c + d*x)**m, x), x) - Dist(d**S(2)*m*(m + S(-1))/(f**S(2)*n**S(2)), Int((b*cos(e + f*x))**n*(c + d*x)**(m + S(-2)), x), x) + Simp(b*(b*cos(e + f*x))**(n + S(-1))*(c + d*x)**m*sin(e + f*x)/(f*n), x) + Simp(d*m*(b*cos(e + f*x))**n*(c + d*x)**(m + S(-1))/(f**S(2)*n**S(2)), x)
    rule3239 = ReplacementRule(pattern3239, replacement3239)
    pattern3240 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**n_, x_), cons7, cons27, cons48, cons125, cons21, cons85, cons165, cons1489)
    def replacement3240(m, f, d, c, n, x, e):
        rubi.append(3240)
        return Int(ExpandTrigReduce((c + d*x)**m, sin(e + f*x)**n, x), x)
    rule3240 = ReplacementRule(pattern3240, replacement3240)
    pattern3241 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**n_, x_), cons7, cons27, cons48, cons125, cons21, cons85, cons165, cons1489)
    def replacement3241(m, f, d, c, n, x, e):
        rubi.append(3241)
        return Int(ExpandTrigReduce((c + d*x)**m, cos(e + f*x)**n, x), x)
    rule3241 = ReplacementRule(pattern3241, replacement3241)
    pattern3242 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_*sin(x_*WC('f', S(1)) + WC('e', S(0)))**n_, x_), cons7, cons27, cons48, cons125, cons21, cons85, cons165, cons31, cons245)
    def replacement3242(m, f, d, c, n, x, e):
        rubi.append(3242)
        return -Dist(f*n/(d*(m + S(1))), Int(ExpandTrigReduce((c + d*x)**(m + S(1)), sin(e + f*x)**(n + S(-1))*cos(e + f*x), x), x), x) + Simp((c + d*x)**(m + S(1))*sin(e + f*x)**n/(d*(m + S(1))), x)
    rule3242 = ReplacementRule(pattern3242, replacement3242)
    pattern3243 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**m_*cos(x_*WC('f', S(1)) + WC('e', S(0)))**n_, x_), cons7, cons27, cons48, cons125, cons21, cons85, cons165, cons31, cons245)
    def replacement3243(m, f, d, c, n, x, e):
        rubi.append(3243)
        return Dist(f*n/(d*(m + S(1))), Int(ExpandTrigReduce((c + d*x)**(m + S(1)), sin(e + f*x)*cos(e + f*x)**(n + S(-1)), x), x), x) + Simp((c + d*x)**(m + S(1))*cos(e + f*x)**n/(d*(m + S(1))), x)
    rule3243 = ReplacementRule(pattern3243, replacement3243)
    pattern3244 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons3, cons7, cons27, cons48, cons125, cons93, cons165, cons247)
    def replacement3244(m, f, b, d, c, n, x, e):
        rubi.append(3244)
        return -Dist(f**S(2)*n**S(2)/(d**S(2)*(m + S(1))*(m + S(2))), Int((b*sin(e + f*x))**n*(c + d*x)**(m + S(2)), x), x) + Dist(b**S(2)*f**S(2)*n*(n + S(-1))/(d**S(2)*(m + S(1))*(m + S(2))), Int((b*sin(e + f*x))**(n + S(-2))*(c + d*x)**(m + S(2)), x), x) + Simp((b*sin(e + f*x))**n*(c + d*x)**(m + S(1))/(d*(m + S(1))), x) - Simp(b*f*n*(b*sin(e + f*x))**(n + S(-1))*(c + d*x)**(m + S(2))*cos(e + f*x)/(d**S(2)*(m + S(1))*(m + S(2))), x)
    rule3244 = ReplacementRule(pattern3244, replacement3244)
    pattern3245 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**m_, x_), cons3, cons7, cons27, cons48, cons125, cons93, cons165, cons247)
    def replacement3245(m, f, b, d, c, n, x, e):
        rubi.append(3245)
        return -Dist(f**S(2)*n**S(2)/(d**S(2)*(m + S(1))*(m + S(2))), Int((b*cos(e + f*x))**n*(c + d*x)**(m + S(2)), x), x) + Dist(b**S(2)*f**S(2)*n*(n + S(-1))/(d**S(2)*(m + S(1))*(m + S(2))), Int((b*cos(e + f*x))**(n + S(-2))*(c + d*x)**(m + S(2)), x), x) + Simp((b*cos(e + f*x))**n*(c + d*x)**(m + S(1))/(d*(m + S(1))), x) + Simp(b*f*n*(b*cos(e + f*x))**(n + S(-1))*(c + d*x)**(m + S(2))*sin(e + f*x)/(d**S(2)*(m + S(1))*(m + S(2))), x)
    rule3245 = ReplacementRule(pattern3245, replacement3245)
    pattern3246 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons3, cons7, cons27, cons48, cons125, cons87, cons89, cons1442)
    def replacement3246(f, b, d, c, n, x, e):
        rubi.append(3246)
        return Dist((n + S(2))/(b**S(2)*(n + S(1))), Int((b*sin(e + f*x))**(n + S(2))*(c + d*x), x), x) - Simp(d*(b*sin(e + f*x))**(n + S(2))/(b**S(2)*f**S(2)*(n + S(1))*(n + S(2))), x) + Simp((b*sin(e + f*x))**(n + S(1))*(c + d*x)*cos(e + f*x)/(b*f*(n + S(1))), x)
    rule3246 = ReplacementRule(pattern3246, replacement3246)
    pattern3247 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons3, cons7, cons27, cons48, cons125, cons87, cons89, cons1442)
    def replacement3247(f, b, d, c, n, x, e):
        rubi.append(3247)
        return Dist((n + S(2))/(b**S(2)*(n + S(1))), Int((b*cos(e + f*x))**(n + S(2))*(c + d*x), x), x) - Simp(d*(b*cos(e + f*x))**(n + S(2))/(b**S(2)*f**S(2)*(n + S(1))*(n + S(2))), x) - Simp((b*cos(e + f*x))**(n + S(1))*(c + d*x)*sin(e + f*x)/(b*f*(n + S(1))), x)
    rule3247 = ReplacementRule(pattern3247, replacement3247)
    pattern3248 = Pattern(Integral((WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons93, cons89, cons1442, cons166)
    def replacement3248(m, f, b, d, c, n, x, e):
        rubi.append(3248)
        return Dist((n + S(2))/(b**S(2)*(n + S(1))), Int((b*sin(e + f*x))**(n + S(2))*(c + d*x)**m, x), x) + Dist(d**S(2)*m*(m + S(-1))/(b**S(2)*f**S(2)*(n + S(1))*(n + S(2))), Int((b*sin(e + f*x))**(n + S(2))*(c + d*x)**(m + S(-2)), x), x) + Simp((b*sin(e + f*x))**(n + S(1))*(c + d*x)**m*cos(e + f*x)/(b*f*(n + S(1))), x) - Simp(d*m*(b*sin(e + f*x))**(n + S(2))*(c + d*x)**(m + S(-1))/(b**S(2)*f**S(2)*(n + S(1))*(n + S(2))), x)
    rule3248 = ReplacementRule(pattern3248, replacement3248)
    pattern3249 = Pattern(Integral((WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons3, cons7, cons27, cons48, cons125, cons93, cons89, cons1442, cons166)
    def replacement3249(m, f, b, d, c, n, x, e):
        rubi.append(3249)
        return Dist((n + S(2))/(b**S(2)*(n + S(1))), Int((b*cos(e + f*x))**(n + S(2))*(c + d*x)**m, x), x) + Dist(d**S(2)*m*(m + S(-1))/(b**S(2)*f**S(2)*(n + S(1))*(n + S(2))), Int((b*cos(e + f*x))**(n + S(2))*(c + d*x)**(m + S(-2)), x), x) - Simp((b*cos(e + f*x))**(n + S(1))*(c + d*x)**m*sin(e + f*x)/(b*f*(n + S(1))), x) - Simp(d*m*(b*cos(e + f*x))**(n + S(2))*(c + d*x)**(m + S(-1))/(b**S(2)*f**S(2)*(n + S(1))*(n + S(2))), x)
    rule3249 = ReplacementRule(pattern3249, replacement3249)
    pattern3250 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons148, cons1490)
    def replacement3250(m, f, b, d, c, n, a, x, e):
        rubi.append(3250)
        return Int(ExpandIntegrand((c + d*x)**m, (a + b*sin(e + f*x))**n, x), x)
    rule3250 = ReplacementRule(pattern3250, replacement3250)
    pattern3251 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons148, cons1490)
    def replacement3251(m, f, b, d, c, n, a, x, e):
        rubi.append(3251)
        return Int(ExpandIntegrand((c + d*x)**m, (a + b*cos(e + f*x))**n, x), x)
    rule3251 = ReplacementRule(pattern3251, replacement3251)
    pattern3252 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1265, cons85)
    def replacement3252(m, f, b, d, c, n, a, x, e):
        rubi.append(3252)
        return Dist((S(2)*a)**n, Int((c + d*x)**m*cos(-Pi*a/(S(4)*b) + e/S(2) + f*x/S(2))**(S(2)*n), x), x)
    rule3252 = ReplacementRule(pattern3252, replacement3252)
    pattern3253 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1265, cons808, cons1491)
    def replacement3253(m, f, b, d, c, a, n, x, e):
        rubi.append(3253)
        return Dist((S(2)*a)**IntPart(n)*(a + b*sin(e + f*x))**FracPart(n)*cos(-Pi*a/(S(4)*b) + e/S(2) + f*x/S(2))**(-S(2)*FracPart(n)), Int((c + d*x)**m*cos(-Pi*a/(S(4)*b) + e/S(2) + f*x/S(2))**(S(2)*n), x), x)
    rule3253 = ReplacementRule(pattern3253, replacement3253)
    pattern3254 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1492, cons85)
    def replacement3254(m, f, b, d, c, n, a, x, e):
        rubi.append(3254)
        return Dist((S(2)*a)**n, Int((c + d*x)**m*cos(e/S(2) + f*x/S(2))**(S(2)*n), x), x)
    rule3254 = ReplacementRule(pattern3254, replacement3254)
    pattern3255 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1))*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1454, cons85)
    def replacement3255(m, f, b, d, c, n, a, x, e):
        rubi.append(3255)
        return Dist((S(2)*a)**n, Int((c + d*x)**m*sin(e/S(2) + f*x/S(2))**(S(2)*n), x), x)
    rule3255 = ReplacementRule(pattern3255, replacement3255)
    pattern3256 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1492, cons808, cons1491)
    def replacement3256(m, f, b, d, c, a, n, x, e):
        rubi.append(3256)
        return Dist((S(2)*a)**IntPart(n)*(a + b*cos(e + f*x))**FracPart(n)*cos(e/S(2) + f*x/S(2))**(-S(2)*FracPart(n)), Int((c + d*x)**m*cos(e/S(2) + f*x/S(2))**(S(2)*n), x), x)
    rule3256 = ReplacementRule(pattern3256, replacement3256)
    pattern3257 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons1454, cons808, cons1491)
    def replacement3257(m, f, b, d, c, a, n, x, e):
        rubi.append(3257)
        return Dist((S(2)*a)**IntPart(n)*(a + b*cos(e + f*x))**FracPart(n)*sin(e/S(2) + f*x/S(2))**(-S(2)*FracPart(n)), Int((c + d*x)**m*sin(e/S(2) + f*x/S(2))**(S(2)*n), x), x)
    rule3257 = ReplacementRule(pattern3257, replacement3257)
    pattern3258 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1267, cons62)
    def replacement3258(m, f, b, d, c, a, x, e):
        rubi.append(3258)
        return Dist(S(2), Int((c + d*x)**m*exp(I*(e + f*x))/(S(2)*a*exp(I*(e + f*x)) - I*b*exp(S(2)*I*(e + f*x)) + I*b), x), x)
    rule3258 = ReplacementRule(pattern3258, replacement3258)
    pattern3259 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0)))), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1267, cons62)
    def replacement3259(m, f, b, d, c, a, x, e):
        rubi.append(3259)
        return Dist(S(2), Int((c + d*x)**m*exp(I*(e + f*x))/(S(2)*a*exp(I*(e + f*x)) + b*exp(S(2)*I*(e + f*x)) + b), x), x)
    rule3259 = ReplacementRule(pattern3259, replacement3259)
    pattern3260 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1267, cons62)
    def replacement3260(m, f, b, d, c, a, x, e):
        rubi.append(3260)
        return Dist(a/(a**S(2) - b**S(2)), Int((c + d*x)**m/(a + b*sin(e + f*x)), x), x) - Dist(b*d*m/(f*(a**S(2) - b**S(2))), Int((c + d*x)**(m + S(-1))*cos(e + f*x)/(a + b*sin(e + f*x)), x), x) + Simp(b*(c + d*x)**m*cos(e + f*x)/(f*(a + b*sin(e + f*x))*(a**S(2) - b**S(2))), x)
    rule3260 = ReplacementRule(pattern3260, replacement3260)
    pattern3261 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))/(a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**S(2), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1267, cons62)
    def replacement3261(m, f, b, d, c, a, x, e):
        rubi.append(3261)
        return Dist(a/(a**S(2) - b**S(2)), Int((c + d*x)**m/(a + b*cos(e + f*x)), x), x) + Dist(b*d*m/(f*(a**S(2) - b**S(2))), Int((c + d*x)**(m + S(-1))*sin(e + f*x)/(a + b*cos(e + f*x)), x), x) - Simp(b*(c + d*x)**m*sin(e + f*x)/(f*(a + b*cos(e + f*x))*(a**S(2) - b**S(2))), x)
    rule3261 = ReplacementRule(pattern3261, replacement3261)
    pattern3262 = Pattern(Integral((a_ + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1267, cons1493, cons62)
    def replacement3262(m, f, b, d, c, a, n, x, e):
        rubi.append(3262)
        return Dist(a/(a**S(2) - b**S(2)), Int((a + b*sin(e + f*x))**(n + S(1))*(c + d*x)**m, x), x) - Dist(b*(n + S(2))/((a**S(2) - b**S(2))*(n + S(1))), Int((a + b*sin(e + f*x))**(n + S(1))*(c + d*x)**m*sin(e + f*x), x), x) + Dist(b*d*m/(f*(a**S(2) - b**S(2))*(n + S(1))), Int((a + b*sin(e + f*x))**(n + S(1))*(c + d*x)**(m + S(-1))*cos(e + f*x), x), x) - Simp(b*(a + b*sin(e + f*x))**(n + S(1))*(c + d*x)**m*cos(e + f*x)/(f*(a**S(2) - b**S(2))*(n + S(1))), x)
    rule3262 = ReplacementRule(pattern3262, replacement3262)
    pattern3263 = Pattern(Integral((a_ + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**n_*(x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons1267, cons1493, cons62)
    def replacement3263(m, f, b, d, c, a, n, x, e):
        rubi.append(3263)
        return Dist(a/(a**S(2) - b**S(2)), Int((a + b*cos(e + f*x))**(n + S(1))*(c + d*x)**m, x), x) - Dist(b*(n + S(2))/((a**S(2) - b**S(2))*(n + S(1))), Int((a + b*cos(e + f*x))**(n + S(1))*(c + d*x)**m*cos(e + f*x), x), x) - Dist(b*d*m/(f*(a**S(2) - b**S(2))*(n + S(1))), Int((a + b*cos(e + f*x))**(n + S(1))*(c + d*x)**(m + S(-1))*sin(e + f*x), x), x) + Simp(b*(a + b*cos(e + f*x))**(n + S(1))*(c + d*x)**m*sin(e + f*x)/(f*(a**S(2) - b**S(2))*(n + S(1))), x)
    rule3263 = ReplacementRule(pattern3263, replacement3263)
    pattern3264 = Pattern(Integral(u_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(v_))**WC('n', S(1)), x_), cons2, cons3, cons21, cons4, cons810, cons811)
    def replacement3264(v, u, m, b, a, n, x):
        rubi.append(3264)
        return Int((a + b*sin(ExpandToSum(v, x)))**n*ExpandToSum(u, x)**m, x)
    rule3264 = ReplacementRule(pattern3264, replacement3264)
    pattern3265 = Pattern(Integral(u_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(v_))**WC('n', S(1)), x_), cons2, cons3, cons21, cons4, cons810, cons811)
    def replacement3265(v, u, m, b, a, n, x):
        rubi.append(3265)
        return Int((a + b*cos(ExpandToSum(v, x)))**n*ExpandToSum(u, x)**m, x)
    rule3265 = ReplacementRule(pattern3265, replacement3265)
    pattern3266 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement3266(m, f, b, d, c, a, n, x, e):
        rubi.append(3266)
        return Int((a + b*sin(e + f*x))**n*(c + d*x)**m, x)
    rule3266 = ReplacementRule(pattern3266, replacement3266)
    pattern3267 = Pattern(Integral((x_*WC('d', S(1)) + WC('c', S(0)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(x_*WC('f', S(1)) + WC('e', S(0))))**WC('n', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons125, cons21, cons4, cons1360)
    def replacement3267(m, f, b, d, a, n, c, x, e):
        rubi.append(3267)
        return Int((a + b*cos(e + f*x))**n*(c + d*x)**m, x)
    rule3267 = ReplacementRule(pattern3267, replacement3267)
    pattern3268 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons4, cons128)
    def replacement3268(p, b, d, c, a, n, x):
        rubi.append(3268)
        return Int(ExpandIntegrand(sin(c + d*x), (a + b*x**n)**p, x), x)
    rule3268 = ReplacementRule(pattern3268, replacement3268)
    pattern3269 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons4, cons128)
    def replacement3269(p, b, d, c, a, n, x):
        rubi.append(3269)
        return Int(ExpandIntegrand(cos(c + d*x), (a + b*x**n)**p, x), x)
    rule3269 = ReplacementRule(pattern3269, replacement3269)
    pattern3270 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons38, cons148, cons137, cons744)
    def replacement3270(p, b, d, c, a, n, x):
        rubi.append(3270)
        return -Dist(d/(b*n*(p + S(1))), Int(x**(-n + S(1))*(a + b*x**n)**(p + S(1))*cos(c + d*x), x), x) - Dist((-n + S(1))/(b*n*(p + S(1))), Int(x**(-n)*(a + b*x**n)**(p + S(1))*sin(c + d*x), x), x) + Simp(x**(-n + S(1))*(a + b*x**n)**(p + S(1))*sin(c + d*x)/(b*n*(p + S(1))), x)
    rule3270 = ReplacementRule(pattern3270, replacement3270)
    pattern3271 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons38, cons148, cons137, cons744)
    def replacement3271(p, b, d, c, a, n, x):
        rubi.append(3271)
        return Dist(d/(b*n*(p + S(1))), Int(x**(-n + S(1))*(a + b*x**n)**(p + S(1))*sin(c + d*x), x), x) - Dist((-n + S(1))/(b*n*(p + S(1))), Int(x**(-n)*(a + b*x**n)**(p + S(1))*cos(c + d*x), x), x) + Simp(x**(-n + S(1))*(a + b*x**n)**(p + S(1))*cos(c + d*x)/(b*n*(p + S(1))), x)
    rule3271 = ReplacementRule(pattern3271, replacement3271)
    pattern3272 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons63, cons148, cons1494)
    def replacement3272(p, b, d, c, a, n, x):
        rubi.append(3272)
        return Int(ExpandIntegrand(sin(c + d*x), (a + b*x**n)**p, x), x)
    rule3272 = ReplacementRule(pattern3272, replacement3272)
    pattern3273 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons63, cons148, cons1494)
    def replacement3273(p, b, d, c, a, n, x):
        rubi.append(3273)
        return Int(ExpandIntegrand(cos(c + d*x), (a + b*x**n)**p, x), x)
    rule3273 = ReplacementRule(pattern3273, replacement3273)
    pattern3274 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons63, cons196)
    def replacement3274(p, b, d, c, a, n, x):
        rubi.append(3274)
        return Int(x**(n*p)*(a*x**(-n) + b)**p*sin(c + d*x), x)
    rule3274 = ReplacementRule(pattern3274, replacement3274)
    pattern3275 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons63, cons196)
    def replacement3275(p, b, d, c, a, n, x):
        rubi.append(3275)
        return Int(x**(n*p)*(a*x**(-n) + b)**p*cos(c + d*x), x)
    rule3275 = ReplacementRule(pattern3275, replacement3275)
    pattern3276 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons1495)
    def replacement3276(p, b, d, c, a, n, x):
        rubi.append(3276)
        return Int((a + b*x**n)**p*sin(c + d*x), x)
    rule3276 = ReplacementRule(pattern3276, replacement3276)
    pattern3277 = Pattern(Integral((a_ + x_**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons1495)
    def replacement3277(p, b, d, c, a, n, x):
        rubi.append(3277)
        return Int((a + b*x**n)**p*cos(c + d*x), x)
    rule3277 = ReplacementRule(pattern3277, replacement3277)
    pattern3278 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons128)
    def replacement3278(p, m, b, d, c, a, n, x, e):
        rubi.append(3278)
        return Int(ExpandIntegrand(sin(c + d*x), (e*x)**m*(a + b*x**n)**p, x), x)
    rule3278 = ReplacementRule(pattern3278, replacement3278)
    pattern3279 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons128)
    def replacement3279(p, m, b, d, c, a, n, x, e):
        rubi.append(3279)
        return Int(ExpandIntegrand(cos(c + d*x), (e*x)**m*(a + b*x**n)**p, x), x)
    rule3279 = ReplacementRule(pattern3279, replacement3279)
    pattern3280 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons38, cons53, cons13, cons137, cons596)
    def replacement3280(p, m, b, d, c, a, n, x, e):
        rubi.append(3280)
        return -Dist(d*e**m/(b*n*(p + S(1))), Int((a + b*x**n)**(p + S(1))*cos(c + d*x), x), x) + Simp(e**m*(a + b*x**n)**(p + S(1))*sin(c + d*x)/(b*n*(p + S(1))), x)
    rule3280 = ReplacementRule(pattern3280, replacement3280)
    pattern3281 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons38, cons53, cons13, cons137, cons596)
    def replacement3281(p, m, b, d, c, a, n, x, e):
        rubi.append(3281)
        return Dist(d*e**m/(b*n*(p + S(1))), Int((a + b*x**n)**(p + S(1))*sin(c + d*x), x), x) + Simp(e**m*(a + b*x**n)**(p + S(1))*cos(c + d*x)/(b*n*(p + S(1))), x)
    rule3281 = ReplacementRule(pattern3281, replacement3281)
    pattern3282 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons38, cons148, cons31, cons137, cons1496)
    def replacement3282(p, m, b, d, c, a, n, x):
        rubi.append(3282)
        return -Dist(d/(b*n*(p + S(1))), Int(x**(m - n + S(1))*(a + b*x**n)**(p + S(1))*cos(c + d*x), x), x) - Dist((m - n + S(1))/(b*n*(p + S(1))), Int(x**(m - n)*(a + b*x**n)**(p + S(1))*sin(c + d*x), x), x) + Simp(x**(m - n + S(1))*(a + b*x**n)**(p + S(1))*sin(c + d*x)/(b*n*(p + S(1))), x)
    rule3282 = ReplacementRule(pattern3282, replacement3282)
    pattern3283 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons38, cons148, cons31, cons137, cons1496)
    def replacement3283(p, m, b, d, c, a, n, x):
        rubi.append(3283)
        return Dist(d/(b*n*(p + S(1))), Int(x**(m - n + S(1))*(a + b*x**n)**(p + S(1))*sin(c + d*x), x), x) - Dist((m - n + S(1))/(b*n*(p + S(1))), Int(x**(m - n)*(a + b*x**n)**(p + S(1))*cos(c + d*x), x), x) + Simp(x**(m - n + S(1))*(a + b*x**n)**(p + S(1))*cos(c + d*x)/(b*n*(p + S(1))), x)
    rule3283 = ReplacementRule(pattern3283, replacement3283)
    pattern3284 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons63, cons17, cons148, cons1494)
    def replacement3284(p, m, b, d, c, a, n, x):
        rubi.append(3284)
        return Int(ExpandIntegrand(sin(c + d*x), x**m*(a + b*x**n)**p, x), x)
    rule3284 = ReplacementRule(pattern3284, replacement3284)
    pattern3285 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons63, cons17, cons148, cons1494)
    def replacement3285(p, m, b, d, c, a, n, x):
        rubi.append(3285)
        return Int(ExpandIntegrand(cos(c + d*x), x**m*(a + b*x**n)**p, x), x)
    rule3285 = ReplacementRule(pattern3285, replacement3285)
    pattern3286 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons21, cons63, cons196)
    def replacement3286(p, m, b, d, c, a, n, x):
        rubi.append(3286)
        return Int(x**(m + n*p)*(a*x**(-n) + b)**p*sin(c + d*x), x)
    rule3286 = ReplacementRule(pattern3286, replacement3286)
    pattern3287 = Pattern(Integral(x_**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**p_*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons21, cons63, cons196)
    def replacement3287(p, m, b, d, c, a, n, x):
        rubi.append(3287)
        return Int(x**(m + n*p)*(a*x**(-n) + b)**p*cos(c + d*x), x)
    rule3287 = ReplacementRule(pattern3287, replacement3287)
    pattern3288 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*sin(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement3288(p, m, b, d, c, a, n, x, e):
        rubi.append(3288)
        return Int((e*x)**m*(a + b*x**n)**p*sin(c + d*x), x)
    rule3288 = ReplacementRule(pattern3288, replacement3288)
    pattern3289 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(a_ + x_**n_*WC('b', S(1)))**WC('p', S(1))*cos(x_*WC('d', S(1)) + WC('c', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons1497)
    def replacement3289(p, m, b, d, c, a, n, x, e):
        rubi.append(3289)
        return Int((e*x)**m*(a + b*x**n)**p*cos(c + d*x), x)
    rule3289 = ReplacementRule(pattern3289, replacement3289)
    pattern3290 = Pattern(Integral(sin(x_**S(2)*WC('d', S(1))), x_), cons27, cons27)
    def replacement3290(d, x):
        rubi.append(3290)
        return Simp(sqrt(S(2))*sqrt(Pi)*FresnelS(sqrt(S(2))*x*sqrt(S(1)/Pi)*Rt(d, S(2)))/(S(2)*Rt(d, S(2))), x)
    rule3290 = ReplacementRule(pattern3290, replacement3290)
    pattern3291 = Pattern(Integral(cos(x_**S(2)*WC('d', S(1))), x_), cons27, cons27)
    def replacement3291(d, x):
        rubi.append(3291)
        return Simp(sqrt(S(2))*sqrt(Pi)*FresnelC(sqrt(S(2))*x*sqrt(S(1)/Pi)*Rt(d, S(2)))/(S(2)*Rt(d, S(2))), x)
    rule3291 = ReplacementRule(pattern3291, replacement3291)
    pattern3292 = Pattern(Integral(sin(c_ + x_**S(2)*WC('d', S(1))), x_), cons7, cons27, cons1261)
    def replacement3292(d, c, x):
        rubi.append(3292)
        return Dist(sin(c), Int(cos(d*x**S(2)), x), x) + Dist(cos(c), Int(sin(d*x**S(2)), x), x)
    rule3292 = ReplacementRule(pattern3292, replacement3292)
    pattern3293 = Pattern(Integral(cos(c_ + x_**S(2)*WC('d', S(1))), x_), cons7, cons27, cons1261)
    def replacement3293(d, c, x):
        rubi.append(3293)
        return -Dist(sin(c), Int(sin(d*x**S(2)), x), x) + Dist(cos(c), Int(cos(d*x**S(2)), x), x)
    rule3293 = ReplacementRule(pattern3293, replacement3293)
    pattern3294 = Pattern(Integral(sin(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons85, cons744)
    def replacement3294(d, c, n, x):
        rubi.append(3294)
        return Dist(I/S(2), Int(exp(-I*c - I*d*x**n), x), x) - Dist(I/S(2), Int(exp(I*c + I*d*x**n), x), x)
    rule3294 = ReplacementRule(pattern3294, replacement3294)
    pattern3295 = Pattern(Integral(cos(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons85, cons744)
    def replacement3295(d, c, n, x):
        rubi.append(3295)
        return Dist(S(1)/2, Int(exp(-I*c - I*d*x**n), x), x) + Dist(S(1)/2, Int(exp(I*c + I*d*x**n), x), x)
    rule3295 = ReplacementRule(pattern3295, replacement3295)
    pattern3296 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons376, cons165, cons146)
    def replacement3296(p, b, d, c, a, n, x):
        rubi.append(3296)
        return Int(ExpandTrigReduce((a + b*sin(c + d*x**n))**p, x), x)
    rule3296 = ReplacementRule(pattern3296, replacement3296)
    pattern3297 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons376, cons165, cons146)
    def replacement3297(p, b, d, a, c, n, x):
        rubi.append(3297)
        return Int(ExpandTrigReduce((a + b*cos(c + d*x**n))**p, x), x)
    rule3297 = ReplacementRule(pattern3297, replacement3297)
    pattern3298 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons38, cons196)
    def replacement3298(p, b, d, c, a, n, x):
        rubi.append(3298)
        return -Subst(Int((a + b*sin(c + d*x**(-n)))**p/x**S(2), x), x, S(1)/x)
    rule3298 = ReplacementRule(pattern3298, replacement3298)
    pattern3299 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons38, cons196)
    def replacement3299(p, b, d, a, c, n, x):
        rubi.append(3299)
        return -Subst(Int((a + b*cos(c + d*x**(-n)))**p/x**S(2), x), x, S(1)/x)
    rule3299 = ReplacementRule(pattern3299, replacement3299)
    def With3300(p, b, d, c, a, n, x):
        k = Denominator(n)
        rubi.append(3300)
        return Dist(k, Subst(Int(x**(k + S(-1))*(a + b*sin(c + d*x**(k*n)))**p, x), x, x**(S(1)/k)), x)
    pattern3300 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons38, cons489)
    rule3300 = ReplacementRule(pattern3300, With3300)
    def With3301(p, b, d, a, c, n, x):
        k = Denominator(n)
        rubi.append(3301)
        return Dist(k, Subst(Int(x**(k + S(-1))*(a + b*cos(c + d*x**(k*n)))**p, x), x, x**(S(1)/k)), x)
    pattern3301 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons38, cons489)
    rule3301 = ReplacementRule(pattern3301, With3301)
    pattern3302 = Pattern(Integral(sin(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons4, cons1498)
    def replacement3302(d, c, n, x):
        rubi.append(3302)
        return Dist(I/S(2), Int(exp(-I*c - I*d*x**n), x), x) - Dist(I/S(2), Int(exp(I*c + I*d*x**n), x), x)
    rule3302 = ReplacementRule(pattern3302, replacement3302)
    pattern3303 = Pattern(Integral(cos(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons4, cons1498)
    def replacement3303(d, c, n, x):
        rubi.append(3303)
        return Dist(S(1)/2, Int(exp(-I*c - I*d*x**n), x), x) + Dist(S(1)/2, Int(exp(I*c + I*d*x**n), x), x)
    rule3303 = ReplacementRule(pattern3303, replacement3303)
    pattern3304 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons4, cons128)
    def replacement3304(p, b, d, c, a, n, x):
        rubi.append(3304)
        return Int(ExpandTrigReduce((a + b*sin(c + d*x**n))**p, x), x)
    rule3304 = ReplacementRule(pattern3304, replacement3304)
    pattern3305 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons4, cons128)
    def replacement3305(p, b, d, a, c, n, x):
        rubi.append(3305)
        return Int(ExpandTrigReduce((a + b*cos(c + d*x**n))**p, x), x)
    rule3305 = ReplacementRule(pattern3305, replacement3305)
    pattern3306 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons38, cons68, cons69)
    def replacement3306(p, u, b, d, c, a, n, x):
        rubi.append(3306)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b*sin(c + d*x**n))**p, x), x, u), x)
    rule3306 = ReplacementRule(pattern3306, replacement3306)
    pattern3307 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons38, cons68, cons69)
    def replacement3307(p, u, b, d, a, c, n, x):
        rubi.append(3307)
        return Dist(S(1)/Coefficient(u, x, S(1)), Subst(Int((a + b*cos(c + d*x**n))**p, x), x, u), x)
    rule3307 = ReplacementRule(pattern3307, replacement3307)
    pattern3308 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(u_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons4, cons5, cons68)
    def replacement3308(p, u, b, d, c, a, n, x):
        rubi.append(3308)
        return Int((a + b*sin(c + d*u**n))**p, x)
    rule3308 = ReplacementRule(pattern3308, replacement3308)
    pattern3309 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(u_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons4, cons5, cons68)
    def replacement3309(p, u, b, d, a, c, n, x):
        rubi.append(3309)
        return Int((a + b*cos(c + d*u**n))**p, x)
    rule3309 = ReplacementRule(pattern3309, replacement3309)
    pattern3310 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*sin(u_))**WC('p', S(1)), x_), cons2, cons3, cons5, cons823, cons824)
    def replacement3310(p, u, b, a, x):
        rubi.append(3310)
        return Int((a + b*sin(ExpandToSum(u, x)))**p, x)
    rule3310 = ReplacementRule(pattern3310, replacement3310)
    pattern3311 = Pattern(Integral((WC('a', S(0)) + WC('b', S(1))*cos(u_))**WC('p', S(1)), x_), cons2, cons3, cons5, cons823, cons824)
    def replacement3311(p, u, b, a, x):
        rubi.append(3311)
        return Int((a + b*cos(ExpandToSum(u, x)))**p, x)
    rule3311 = ReplacementRule(pattern3311, replacement3311)
    pattern3312 = Pattern(Integral(sin(x_**n_*WC('d', S(1)))/x_, x_), cons27, cons4, cons1499)
    def replacement3312(d, x, n):
        rubi.append(3312)
        return Simp(SinIntegral(d*x**n)/n, x)
    rule3312 = ReplacementRule(pattern3312, replacement3312)
    pattern3313 = Pattern(Integral(cos(x_**n_*WC('d', S(1)))/x_, x_), cons27, cons4, cons1499)
    def replacement3313(d, x, n):
        rubi.append(3313)
        return Simp(CosIntegral(d*x**n)/n, x)
    rule3313 = ReplacementRule(pattern3313, replacement3313)
    pattern3314 = Pattern(Integral(sin(c_ + x_**n_*WC('d', S(1)))/x_, x_), cons7, cons27, cons4, cons1498)
    def replacement3314(d, x, n, c):
        rubi.append(3314)
        return Dist(sin(c), Int(cos(d*x**n)/x, x), x) + Dist(cos(c), Int(sin(d*x**n)/x, x), x)
    rule3314 = ReplacementRule(pattern3314, replacement3314)
    pattern3315 = Pattern(Integral(cos(c_ + x_**n_*WC('d', S(1)))/x_, x_), cons7, cons27, cons4, cons1498)
    def replacement3315(d, c, n, x):
        rubi.append(3315)
        return -Dist(sin(c), Int(sin(d*x**n)/x, x), x) + Dist(cos(c), Int(cos(d*x**n)/x, x), x)
    rule3315 = ReplacementRule(pattern3315, replacement3315)
    def With3316(p, m, b, d, c, a, n, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        mn = (m + S(1))/n
        if And(IntegerQ(mn), Or(Equal(p, S(1)), Greater(mn, S(0)))):
            return True
        return False
    pattern3316 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons38, CustomConstraint(With3316))
    def replacement3316(p, m, b, d, c, a, n, x):

        mn = (m + S(1))/n
        rubi.append(3316)
        return Dist(S(1)/n, Subst(Int(x**(mn + S(-1))*(a + b*sin(c + d*x))**p, x), x, x**n), x)
    rule3316 = ReplacementRule(pattern3316, replacement3316)
    def With3317(p, m, b, d, a, c, n, x):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        mn = (m + S(1))/n
        if And(IntegerQ(mn), Or(Equal(p, S(1)), Greater(mn, S(0)))):
            return True
        return False
    pattern3317 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons38, CustomConstraint(With3317))
    def replacement3317(p, m, b, d, a, c, n, x):

        mn = (m + S(1))/n
        rubi.append(3317)
        return Dist(S(1)/n, Subst(Int(x**(mn + S(-1))*(a + b*cos(c + d*x))**p, x), x, x**n), x)
    rule3317 = ReplacementRule(pattern3317, replacement3317)
    def With3318(p, m, b, d, c, a, n, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        mn = (m + S(1))/n
        if And(IntegerQ(mn), Or(Equal(p, S(1)), Greater(mn, S(0)))):
            return True
        return False
    pattern3318 = Pattern(Integral((e_*x_)**m_*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons38, CustomConstraint(With3318))
    def replacement3318(p, m, b, d, c, a, n, x, e):

        mn = (m + S(1))/n
        rubi.append(3318)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*sin(c + d*x**n))**p, x), x)
    rule3318 = ReplacementRule(pattern3318, replacement3318)
    def With3319(p, m, b, d, a, c, n, x, e):
        if isinstance(x, (int, Integer, float, Float)):
            return False
        mn = (m + S(1))/n
        if And(IntegerQ(mn), Or(Equal(p, S(1)), Greater(mn, S(0)))):
            return True
        return False
    pattern3319 = Pattern(Integral((e_*x_)**m_*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons38, CustomConstraint(With3319))
    def replacement3319(p, m, b, d, a, c, n, x, e):

        mn = (m + S(1))/n
        rubi.append(3319)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*cos(c + d*x**n))**p, x), x)
    rule3319 = ReplacementRule(pattern3319, replacement3319)
    pattern3320 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**n_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons21, cons4, cons1500)
    def replacement3320(m, b, a, n, x):
        rubi.append(3320)
        return Dist(S(2)/n, Subst(Int(sin(a + b*x**S(2)), x), x, x**(n/S(2))), x)
    rule3320 = ReplacementRule(pattern3320, replacement3320)
    pattern3321 = Pattern(Integral(x_**WC('m', S(1))*cos(x_**n_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons21, cons4, cons1500)
    def replacement3321(m, b, a, n, x):
        rubi.append(3321)
        return Dist(S(2)/n, Subst(Int(cos(a + b*x**S(2)), x), x, x**(n/S(2))), x)
    rule3321 = ReplacementRule(pattern3321, replacement3321)
    pattern3322 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons148, cons31, cons1501)
    def replacement3322(m, d, c, n, x, e):
        rubi.append(3322)
        return Dist(e**n*(m - n + S(1))/(d*n), Int((e*x)**(m - n)*cos(c + d*x**n), x), x) - Simp(e**(n + S(-1))*(e*x)**(m - n + S(1))*cos(c + d*x**n)/(d*n), x)
    rule3322 = ReplacementRule(pattern3322, replacement3322)
    pattern3323 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons148, cons31, cons1501)
    def replacement3323(m, d, c, n, x, e):
        rubi.append(3323)
        return -Dist(e**n*(m - n + S(1))/(d*n), Int((e*x)**(m - n)*sin(c + d*x**n), x), x) + Simp(e**(n + S(-1))*(e*x)**(m - n + S(1))*sin(c + d*x**n)/(d*n), x)
    rule3323 = ReplacementRule(pattern3323, replacement3323)
    pattern3324 = Pattern(Integral((x_*WC('e', S(1)))**m_*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons148, cons31, cons94)
    def replacement3324(m, d, c, n, x, e):
        rubi.append(3324)
        return -Dist(d*e**(-n)*n/(m + S(1)), Int((e*x)**(m + n)*cos(c + d*x**n), x), x) + Simp((e*x)**(m + S(1))*sin(c + d*x**n)/(e*(m + S(1))), x)
    rule3324 = ReplacementRule(pattern3324, replacement3324)
    pattern3325 = Pattern(Integral((x_*WC('e', S(1)))**m_*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons148, cons31, cons94)
    def replacement3325(m, d, c, n, x, e):
        rubi.append(3325)
        return Dist(d*e**(-n)*n/(m + S(1)), Int((e*x)**(m + n)*sin(c + d*x**n), x), x) + Simp((e*x)**(m + S(1))*cos(c + d*x**n)/(e*(m + S(1))), x)
    rule3325 = ReplacementRule(pattern3325, replacement3325)
    pattern3326 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons21, cons148)
    def replacement3326(m, d, c, n, x, e):
        rubi.append(3326)
        return Dist(I/S(2), Int((e*x)**m*exp(-I*c - I*d*x**n), x), x) - Dist(I/S(2), Int((e*x)**m*exp(I*c + I*d*x**n), x), x)
    rule3326 = ReplacementRule(pattern3326, replacement3326)
    pattern3327 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons21, cons148)
    def replacement3327(m, d, c, n, x, e):
        rubi.append(3327)
        return Dist(S(1)/2, Int((e*x)**m*exp(-I*c - I*d*x**n), x), x) + Dist(S(1)/2, Int((e*x)**m*exp(I*c + I*d*x**n), x), x)
    rule3327 = ReplacementRule(pattern3327, replacement3327)
    pattern3328 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons376, cons1255, cons146, cons1502)
    def replacement3328(p, m, b, a, n, x):
        rubi.append(3328)
        return Dist(b*n*p/(n + S(-1)), Int(sin(a + b*x**n)**(p + S(-1))*cos(a + b*x**n), x), x) - Simp(x**(-n + S(1))*sin(a + b*x**n)**p/(n + S(-1)), x)
    rule3328 = ReplacementRule(pattern3328, replacement3328)
    pattern3329 = Pattern(Integral(x_**WC('m', S(1))*cos(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons376, cons1255, cons146, cons1502)
    def replacement3329(p, m, b, a, n, x):
        rubi.append(3329)
        return -Dist(b*n*p/(n + S(-1)), Int(sin(a + b*x**n)*cos(a + b*x**n)**(p + S(-1)), x), x) - Simp(x**(-n + S(1))*cos(a + b*x**n)**p/(n + S(-1)), x)
    rule3329 = ReplacementRule(pattern3329, replacement3329)
    pattern3330 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons21, cons4, cons56, cons13, cons146)
    def replacement3330(p, m, b, a, n, x):
        rubi.append(3330)
        return Dist((p + S(-1))/p, Int(x**m*sin(a + b*x**n)**(p + S(-2)), x), x) + Simp(sin(a + b*x**n)**p/(b**S(2)*n*p**S(2)), x) - Simp(x**n*sin(a + b*x**n)**(p + S(-1))*cos(a + b*x**n)/(b*n*p), x)
    rule3330 = ReplacementRule(pattern3330, replacement3330)
    pattern3331 = Pattern(Integral(x_**WC('m', S(1))*cos(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons21, cons4, cons56, cons13, cons146)
    def replacement3331(p, m, b, a, n, x):
        rubi.append(3331)
        return Dist((p + S(-1))/p, Int(x**m*cos(a + b*x**n)**(p + S(-2)), x), x) + Simp(cos(a + b*x**n)**p/(b**S(2)*n*p**S(2)), x) + Simp(x**n*sin(a + b*x**n)*cos(a + b*x**n)**(p + S(-1))/(b*n*p), x)
    rule3331 = ReplacementRule(pattern3331, replacement3331)
    pattern3332 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons150, cons13, cons146, cons1503)
    def replacement3332(p, m, b, a, n, x):
        rubi.append(3332)
        return Dist((p + S(-1))/p, Int(x**m*sin(a + b*x**n)**(p + S(-2)), x), x) - Dist((m - S(2)*n + S(1))*(m - n + S(1))/(b**S(2)*n**S(2)*p**S(2)), Int(x**(m - S(2)*n)*sin(a + b*x**n)**p, x), x) + Simp(x**(m - S(2)*n + S(1))*(m - n + S(1))*sin(a + b*x**n)**p/(b**S(2)*n**S(2)*p**S(2)), x) - Simp(x**(m - n + S(1))*sin(a + b*x**n)**(p + S(-1))*cos(a + b*x**n)/(b*n*p), x)
    rule3332 = ReplacementRule(pattern3332, replacement3332)
    pattern3333 = Pattern(Integral(x_**WC('m', S(1))*cos(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons150, cons13, cons146, cons1503)
    def replacement3333(p, m, b, a, n, x):
        rubi.append(3333)
        return Dist((p + S(-1))/p, Int(x**m*cos(a + b*x**n)**(p + S(-2)), x), x) - Dist((m - S(2)*n + S(1))*(m - n + S(1))/(b**S(2)*n**S(2)*p**S(2)), Int(x**(m - S(2)*n)*cos(a + b*x**n)**p, x), x) + Simp(x**(m - S(2)*n + S(1))*(m - n + S(1))*cos(a + b*x**n)**p/(b**S(2)*n**S(2)*p**S(2)), x) + Simp(x**(m - n + S(1))*sin(a + b*x**n)*cos(a + b*x**n)**(p + S(-1))/(b*n*p), x)
    rule3333 = ReplacementRule(pattern3333, replacement3333)
    pattern3334 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons150, cons13, cons146, cons1504, cons683)
    def replacement3334(p, m, b, a, n, x):
        rubi.append(3334)
        return -Dist(b**S(2)*n**S(2)*p**S(2)/((m + S(1))*(m + n + S(1))), Int(x**(m + S(2)*n)*sin(a + b*x**n)**p, x), x) + Dist(b**S(2)*n**S(2)*p*(p + S(-1))/((m + S(1))*(m + n + S(1))), Int(x**(m + S(2)*n)*sin(a + b*x**n)**(p + S(-2)), x), x) + Simp(x**(m + S(1))*sin(a + b*x**n)**p/(m + S(1)), x) - Simp(b*n*p*x**(m + n + S(1))*sin(a + b*x**n)**(p + S(-1))*cos(a + b*x**n)/((m + S(1))*(m + n + S(1))), x)
    rule3334 = ReplacementRule(pattern3334, replacement3334)
    pattern3335 = Pattern(Integral(x_**WC('m', S(1))*cos(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons150, cons13, cons146, cons1504, cons683)
    def replacement3335(p, m, b, a, n, x):
        rubi.append(3335)
        return -Dist(b**S(2)*n**S(2)*p**S(2)/((m + S(1))*(m + n + S(1))), Int(x**(m + S(2)*n)*cos(a + b*x**n)**p, x), x) + Dist(b**S(2)*n**S(2)*p*(p + S(-1))/((m + S(1))*(m + n + S(1))), Int(x**(m + S(2)*n)*cos(a + b*x**n)**(p + S(-2)), x), x) + Simp(x**(m + S(1))*cos(a + b*x**n)**p/(m + S(1)), x) + Simp(b*n*p*x**(m + n + S(1))*sin(a + b*x**n)*cos(a + b*x**n)**(p + S(-1))/((m + S(1))*(m + n + S(1))), x)
    rule3335 = ReplacementRule(pattern3335, replacement3335)
    def With3336(p, m, b, d, c, a, n, x, e):
        k = Denominator(m)
        rubi.append(3336)
        return Dist(k/e, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a + b*sin(c + d*e**(-n)*x**(k*n)))**p, x), x, (e*x)**(S(1)/k)), x)
    pattern3336 = Pattern(Integral((x_*WC('e', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons38, cons148, cons367)
    rule3336 = ReplacementRule(pattern3336, With3336)
    def With3337(p, m, b, d, a, c, n, x, e):
        k = Denominator(m)
        rubi.append(3337)
        return Dist(k/e, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a + b*cos(c + d*e**(-n)*x**(k*n)))**p, x), x, (e*x)**(S(1)/k)), x)
    pattern3337 = Pattern(Integral((x_*WC('e', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons38, cons148, cons367)
    rule3337 = ReplacementRule(pattern3337, With3337)
    pattern3338 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons146)
    def replacement3338(p, m, b, d, c, a, n, x, e):
        rubi.append(3338)
        return Int(ExpandTrigReduce((e*x)**m, (a + b*sin(c + d*x**n))**p, x), x)
    rule3338 = ReplacementRule(pattern3338, replacement3338)
    pattern3339 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons148, cons146)
    def replacement3339(p, m, b, d, a, c, n, x, e):
        rubi.append(3339)
        return Int(ExpandTrigReduce((e*x)**m, (a + b*cos(c + d*x**n))**p, x), x)
    rule3339 = ReplacementRule(pattern3339, replacement3339)
    pattern3340 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons21, cons4, cons56, cons13, cons137, cons1505)
    def replacement3340(p, m, b, a, n, x):
        rubi.append(3340)
        return Dist((p + S(2))/(p + S(1)), Int(x**m*sin(a + b*x**n)**(p + S(2)), x), x) - Simp(sin(a + b*x**n)**(p + S(2))/(b**S(2)*n*(p + S(1))*(p + S(2))), x) + Simp(x**n*sin(a + b*x**n)**(p + S(1))*cos(a + b*x**n)/(b*n*(p + S(1))), x)
    rule3340 = ReplacementRule(pattern3340, replacement3340)
    pattern3341 = Pattern(Integral(x_**WC('m', S(1))*cos(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons21, cons4, cons56, cons13, cons137, cons1505)
    def replacement3341(p, m, b, a, n, x):
        rubi.append(3341)
        return Dist((p + S(2))/(p + S(1)), Int(x**m*cos(a + b*x**n)**(p + S(2)), x), x) - Simp(cos(a + b*x**n)**(p + S(2))/(b**S(2)*n*(p + S(1))*(p + S(2))), x) - Simp(x**n*sin(a + b*x**n)*cos(a + b*x**n)**(p + S(1))/(b*n*(p + S(1))), x)
    rule3341 = ReplacementRule(pattern3341, replacement3341)
    pattern3342 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons150, cons13, cons137, cons1505, cons1503)
    def replacement3342(p, m, b, a, n, x):
        rubi.append(3342)
        return Dist((p + S(2))/(p + S(1)), Int(x**m*sin(a + b*x**n)**(p + S(2)), x), x) + Dist((m - S(2)*n + S(1))*(m - n + S(1))/(b**S(2)*n**S(2)*(p + S(1))*(p + S(2))), Int(x**(m - S(2)*n)*sin(a + b*x**n)**(p + S(2)), x), x) + Simp(x**(m - n + S(1))*sin(a + b*x**n)**(p + S(1))*cos(a + b*x**n)/(b*n*(p + S(1))), x) - Simp(x**(m - S(2)*n + S(1))*(m - n + S(1))*sin(a + b*x**n)**(p + S(2))/(b**S(2)*n**S(2)*(p + S(1))*(p + S(2))), x)
    rule3342 = ReplacementRule(pattern3342, replacement3342)
    pattern3343 = Pattern(Integral(x_**WC('m', S(1))*cos(x_**n_*WC('b', S(1)) + WC('a', S(0)))**p_, x_), cons2, cons3, cons150, cons13, cons137, cons1505, cons1503)
    def replacement3343(p, m, b, a, n, x):
        rubi.append(3343)
        return Dist((p + S(2))/(p + S(1)), Int(x**m*cos(a + b*x**n)**(p + S(2)), x), x) + Dist((m - S(2)*n + S(1))*(m - n + S(1))/(b**S(2)*n**S(2)*(p + S(1))*(p + S(2))), Int(x**(m - S(2)*n)*cos(a + b*x**n)**(p + S(2)), x), x) - Simp(x**(m - n + S(1))*sin(a + b*x**n)*cos(a + b*x**n)**(p + S(1))/(b*n*(p + S(1))), x) - Simp(x**(m - S(2)*n + S(1))*(m - n + S(1))*cos(a + b*x**n)**(p + S(2))/(b**S(2)*n**S(2)*(p + S(1))*(p + S(2))), x)
    rule3343 = ReplacementRule(pattern3343, replacement3343)
    pattern3344 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons38, cons196, cons17)
    def replacement3344(p, m, b, d, c, a, n, x):
        rubi.append(3344)
        return -Subst(Int(x**(-m + S(-2))*(a + b*sin(c + d*x**(-n)))**p, x), x, S(1)/x)
    rule3344 = ReplacementRule(pattern3344, replacement3344)
    pattern3345 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons38, cons196, cons17)
    def replacement3345(p, m, b, d, a, c, n, x):
        rubi.append(3345)
        return -Subst(Int(x**(-m + S(-2))*(a + b*cos(c + d*x**(-n)))**p, x), x, S(1)/x)
    rule3345 = ReplacementRule(pattern3345, replacement3345)
    def With3346(p, m, b, d, c, a, n, x, e):
        k = Denominator(m)
        rubi.append(3346)
        return -Dist(k/e, Subst(Int(x**(-k*(m + S(1)) + S(-1))*(a + b*sin(c + d*e**(-n)*x**(-k*n)))**p, x), x, (e*x)**(-S(1)/k)), x)
    pattern3346 = Pattern(Integral((x_*WC('e', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons38, cons196, cons367)
    rule3346 = ReplacementRule(pattern3346, With3346)
    def With3347(p, m, b, d, a, c, n, x, e):
        k = Denominator(m)
        rubi.append(3347)
        return -Dist(k/e, Subst(Int(x**(-k*(m + S(1)) + S(-1))*(a + b*cos(c + d*e**(-n)*x**(-k*n)))**p, x), x, (e*x)**(-S(1)/k)), x)
    pattern3347 = Pattern(Integral((x_*WC('e', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons38, cons196, cons367)
    rule3347 = ReplacementRule(pattern3347, With3347)
    pattern3348 = Pattern(Integral((x_*WC('e', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons196, cons356)
    def replacement3348(p, m, b, d, c, a, n, x, e):
        rubi.append(3348)
        return -Dist((e*x)**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(a + b*sin(c + d*x**(-n)))**p, x), x, S(1)/x), x)
    rule3348 = ReplacementRule(pattern3348, replacement3348)
    pattern3349 = Pattern(Integral((x_*WC('e', S(1)))**m_*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons196, cons356)
    def replacement3349(p, m, b, d, a, c, n, x, e):
        rubi.append(3349)
        return -Dist((e*x)**m*(S(1)/x)**m, Subst(Int(x**(-m + S(-2))*(a + b*cos(c + d*x**(-n)))**p, x), x, S(1)/x), x)
    rule3349 = ReplacementRule(pattern3349, replacement3349)
    def With3350(p, m, b, d, c, a, n, x):
        k = Denominator(n)
        rubi.append(3350)
        return Dist(k, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a + b*sin(c + d*x**(k*n)))**p, x), x, x**(S(1)/k)), x)
    pattern3350 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons38, cons489)
    rule3350 = ReplacementRule(pattern3350, With3350)
    def With3351(p, m, b, d, a, c, n, x):
        k = Denominator(n)
        rubi.append(3351)
        return Dist(k, Subst(Int(x**(k*(m + S(1)) + S(-1))*(a + b*cos(c + d*x**(k*n)))**p, x), x, x**(S(1)/k)), x)
    pattern3351 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons38, cons489)
    rule3351 = ReplacementRule(pattern3351, With3351)
    pattern3352 = Pattern(Integral((e_*x_)**m_*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons489)
    def replacement3352(p, m, b, d, c, a, n, x, e):
        rubi.append(3352)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*sin(c + d*x**n))**p, x), x)
    rule3352 = ReplacementRule(pattern3352, replacement3352)
    pattern3353 = Pattern(Integral((e_*x_)**m_*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons38, cons489)
    def replacement3353(p, m, b, d, a, c, n, x, e):
        rubi.append(3353)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*cos(c + d*x**n))**p, x), x)
    rule3353 = ReplacementRule(pattern3353, replacement3353)
    pattern3354 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons38, cons66, cons854, cons23)
    def replacement3354(p, m, b, d, c, a, n, x):
        rubi.append(3354)
        return Dist(S(1)/(m + S(1)), Subst(Int((a + b*sin(c + d*x**(n/(m + S(1)))))**p, x), x, x**(m + S(1))), x)
    rule3354 = ReplacementRule(pattern3354, replacement3354)
    pattern3355 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons21, cons4, cons38, cons66, cons854, cons23)
    def replacement3355(p, m, b, d, a, c, n, x):
        rubi.append(3355)
        return Dist(S(1)/(m + S(1)), Subst(Int((a + b*cos(c + d*x**(n/(m + S(1)))))**p, x), x, x**(m + S(1))), x)
    rule3355 = ReplacementRule(pattern3355, replacement3355)
    pattern3356 = Pattern(Integral((e_*x_)**m_*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons38, cons66, cons854, cons23)
    def replacement3356(p, m, b, d, c, a, n, x, e):
        rubi.append(3356)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*sin(c + d*x**n))**p, x), x)
    rule3356 = ReplacementRule(pattern3356, replacement3356)
    pattern3357 = Pattern(Integral((e_*x_)**m_*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons38, cons66, cons854, cons23)
    def replacement3357(p, m, b, d, a, c, n, x, e):
        rubi.append(3357)
        return Dist(e**IntPart(m)*x**(-FracPart(m))*(e*x)**FracPart(m), Int(x**m*(a + b*cos(c + d*x**n))**p, x), x)
    rule3357 = ReplacementRule(pattern3357, replacement3357)
    pattern3358 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons21, cons4, cons1506)
    def replacement3358(m, d, c, n, x, e):
        rubi.append(3358)
        return Dist(I/S(2), Int((e*x)**m*exp(-I*c - I*d*x**n), x), x) - Dist(I/S(2), Int((e*x)**m*exp(I*c + I*d*x**n), x), x)
    rule3358 = ReplacementRule(pattern3358, replacement3358)
    pattern3359 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))), x_), cons7, cons27, cons48, cons21, cons4, cons1506)
    def replacement3359(m, d, c, n, x, e):
        rubi.append(3359)
        return Dist(S(1)/2, Int((e*x)**m*exp(-I*c - I*d*x**n), x), x) + Dist(S(1)/2, Int((e*x)**m*exp(I*c + I*d*x**n), x), x)
    rule3359 = ReplacementRule(pattern3359, replacement3359)
    pattern3360 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(x_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons128)
    def replacement3360(p, m, b, d, c, a, n, x, e):
        rubi.append(3360)
        return Int(ExpandTrigReduce((e*x)**m, (a + b*sin(c + d*x**n))**p, x), x)
    rule3360 = ReplacementRule(pattern3360, replacement3360)
    pattern3361 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(x_**n_*WC('d', S(1)) + WC('c', S(0))))**p_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons128)
    def replacement3361(p, m, b, d, a, c, n, x, e):
        rubi.append(3361)
        return Int(ExpandTrigReduce((e*x)**m, (a + b*cos(c + d*x**n))**p, x), x)
    rule3361 = ReplacementRule(pattern3361, replacement3361)
    pattern3362 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons68, cons69, cons17)
    def replacement3362(p, u, m, b, d, c, a, n, x):
        rubi.append(3362)
        return Dist(Coefficient(u, x, S(1))**(-m + S(-1)), Subst(Int((a + b*sin(c + d*x**n))**p*(x - Coefficient(u, x, S(0)))**m, x), x, u), x)
    rule3362 = ReplacementRule(pattern3362, replacement3362)
    pattern3363 = Pattern(Integral(x_**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons4, cons5, cons68, cons69, cons17)
    def replacement3363(p, u, m, b, d, a, c, n, x):
        rubi.append(3363)
        return Dist(Coefficient(u, x, S(1))**(-m + S(-1)), Subst(Int((a + b*cos(c + d*x**n))**p*(x - Coefficient(u, x, S(0)))**m, x), x, u), x)
    rule3363 = ReplacementRule(pattern3363, replacement3363)
    pattern3364 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons68)
    def replacement3364(p, u, m, b, d, c, a, n, x, e):
        rubi.append(3364)
        return Int((e*x)**m*(a + b*sin(c + d*u**n))**p, x)
    rule3364 = ReplacementRule(pattern3364, replacement3364)
    pattern3365 = Pattern(Integral((x_*WC('e', S(1)))**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(u_**n_*WC('d', S(1)) + WC('c', S(0))))**WC('p', S(1)), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons4, cons5, cons68)
    def replacement3365(p, u, m, b, d, a, c, n, x, e):
        rubi.append(3365)
        return Int((e*x)**m*(a + b*cos(c + d*u**n))**p, x)
    rule3365 = ReplacementRule(pattern3365, replacement3365)
    pattern3366 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*sin(u_))**WC('p', S(1)), x_), cons2, cons3, cons48, cons21, cons5, cons823, cons824)
    def replacement3366(p, u, m, b, a, x, e):
        rubi.append(3366)
        return Int((e*x)**m*(a + b*sin(ExpandToSum(u, x)))**p, x)
    rule3366 = ReplacementRule(pattern3366, replacement3366)
    pattern3367 = Pattern(Integral((e_*x_)**WC('m', S(1))*(WC('a', S(0)) + WC('b', S(1))*cos(u_))**WC('p', S(1)), x_), cons2, cons3, cons48, cons21, cons5, cons823, cons824)
    def replacement3367(p, u, m, b, a, x, e):
        rubi.append(3367)
        return Int((e*x)**m*(a + b*cos(ExpandToSum(u, x)))**p, x)
    rule3367 = ReplacementRule(pattern3367, replacement3367)
    pattern3368 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*cos(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons21, cons4, cons5, cons53, cons54)
    def replacement3368(p, m, b, a, n, x):
        rubi.append(3368)
        return Simp(sin(a + b*x**n)**(p + S(1))/(b*n*(p + S(1))), x)
    rule3368 = ReplacementRule(pattern3368, replacement3368)
    pattern3369 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))*cos(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons21, cons4, cons5, cons53, cons54)
    def replacement3369(p, m, b, a, n, x):
        rubi.append(3369)
        return -Simp(cos(a + b*x**n)**(p + S(1))/(b*n*(p + S(1))), x)
    rule3369 = ReplacementRule(pattern3369, replacement3369)
    pattern3370 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1))*cos(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons5, cons93, cons1501, cons54)
    def replacement3370(p, m, b, a, n, x):
        rubi.append(3370)
        return -Dist((m - n + S(1))/(b*n*(p + S(1))), Int(x**(m - n)*sin(a + b*x**n)**(p + S(1)), x), x) + Simp(x**(m - n + S(1))*sin(a + b*x**n)**(p + S(1))/(b*n*(p + S(1))), x)
    rule3370 = ReplacementRule(pattern3370, replacement3370)
    pattern3371 = Pattern(Integral(x_**WC('m', S(1))*sin(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))*cos(x_**WC('n', S(1))*WC('b', S(1)) + WC('a', S(0)))**WC('p', S(1)), x_), cons2, cons3, cons5, cons93, cons1501, cons54)
    def replacement3371(p, m, b, a, n, x):
        rubi.append(3371)
        return Dist((m - n + S(1))/(b*n*(p + S(1))), Int(x**(m - n)*cos(a + b*x**n)**(p + S(1)), x), x) - Simp(x**(m - n + S(1))*cos(a + b*x**n)**(p + S(1))/(b*n*(p + S(1))), x)
    rule3371 = ReplacementRule(pattern3371, replacement3371)
    pattern3372 = Pattern(Integral(sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons45)
    def replacement3372(x, c, a, b):
        rubi.append(3372)
        return Int(sin((b + S(2)*c*x)**S(2)/(S(4)*c)), x)
    rule3372 = ReplacementRule(pattern3372, replacement3372)
    pattern3373 = Pattern(Integral(cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons45)
    def replacement3373(x, c, a, b):
        rubi.append(3373)
        return Int(cos((b + S(2)*c*x)**S(2)/(S(4)*c)), x)
    rule3373 = ReplacementRule(pattern3373, replacement3373)
    pattern3374 = Pattern(Integral(sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons226)
    def replacement3374(x, c, a, b):
        rubi.append(3374)
        return -Dist(sin((-S(4)*a*c + b**S(2))/(S(4)*c)), Int(cos((b + S(2)*c*x)**S(2)/(S(4)*c)), x), x) + Dist(cos((-S(4)*a*c + b**S(2))/(S(4)*c)), Int(sin((b + S(2)*c*x)**S(2)/(S(4)*c)), x), x)
    rule3374 = ReplacementRule(pattern3374, replacement3374)
    pattern3375 = Pattern(Integral(cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons226)
    def replacement3375(x, c, a, b):
        rubi.append(3375)
        return Dist(sin((-S(4)*a*c + b**S(2))/(S(4)*c)), Int(sin((b + S(2)*c*x)**S(2)/(S(4)*c)), x), x) + Dist(cos((-S(4)*a*c + b**S(2))/(S(4)*c)), Int(cos((b + S(2)*c*x)**S(2)/(S(4)*c)), x), x)
    rule3375 = ReplacementRule(pattern3375, replacement3375)
    pattern3376 = Pattern(Integral(sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons85, cons165)
    def replacement3376(b, c, a, n, x):
        rubi.append(3376)
        return Int(ExpandTrigReduce(sin(a + b*x + c*x**S(2))**n, x), x)
    rule3376 = ReplacementRule(pattern3376, replacement3376)
    pattern3377 = Pattern(Integral(cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons85, cons165)
    def replacement3377(b, c, a, n, x):
        rubi.append(3377)
        return Int(ExpandTrigReduce(cos(a + b*x + c*x**S(2))**n, x), x)
    rule3377 = ReplacementRule(pattern3377, replacement3377)
    pattern3378 = Pattern(Integral(sin(v_)**WC('n', S(1)), x_), cons148, cons818, cons1131)
    def replacement3378(v, x, n):
        rubi.append(3378)
        return Int(sin(ExpandToSum(v, x))**n, x)
    rule3378 = ReplacementRule(pattern3378, replacement3378)
    pattern3379 = Pattern(Integral(cos(v_)**WC('n', S(1)), x_), cons148, cons818, cons1131)
    def replacement3379(v, x, n):
        rubi.append(3379)
        return Int(cos(ExpandToSum(v, x))**n, x)
    rule3379 = ReplacementRule(pattern3379, replacement3379)
    pattern3380 = Pattern(Integral((d_ + x_*WC('e', S(1)))*sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons47)
    def replacement3380(b, d, c, a, x, e):
        rubi.append(3380)
        return -Simp(e*cos(a + b*x + c*x**S(2))/(S(2)*c), x)
    rule3380 = ReplacementRule(pattern3380, replacement3380)
    pattern3381 = Pattern(Integral((d_ + x_*WC('e', S(1)))*cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons47)
    def replacement3381(b, d, c, a, x, e):
        rubi.append(3381)
        return Simp(e*sin(a + b*x + c*x**S(2))/(S(2)*c), x)
    rule3381 = ReplacementRule(pattern3381, replacement3381)
    pattern3382 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))*sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons239)
    def replacement3382(b, d, c, a, x, e):
        rubi.append(3382)
        return Dist((-b*e + S(2)*c*d)/(S(2)*c), Int(sin(a + b*x + c*x**S(2)), x), x) - Simp(e*cos(a + b*x + c*x**S(2))/(S(2)*c), x)
    rule3382 = ReplacementRule(pattern3382, replacement3382)
    pattern3383 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))*cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons239)
    def replacement3383(b, d, c, a, x, e):
        rubi.append(3383)
        return Dist((-b*e + S(2)*c*d)/(S(2)*c), Int(cos(a + b*x + c*x**S(2)), x), x) + Simp(e*sin(a + b*x + c*x**S(2))/(S(2)*c), x)
    rule3383 = ReplacementRule(pattern3383, replacement3383)
    pattern3384 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons166, cons1132)
    def replacement3384(m, b, d, c, a, x, e):
        rubi.append(3384)
        return Dist(e**S(2)*(m + S(-1))/(S(2)*c), Int((d + e*x)**(m + S(-2))*cos(a + b*x + c*x**S(2)), x), x) - Simp(e*(d + e*x)**(m + S(-1))*cos(a + b*x + c*x**S(2))/(S(2)*c), x)
    rule3384 = ReplacementRule(pattern3384, replacement3384)
    pattern3385 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons166, cons1132)
    def replacement3385(m, b, d, c, a, x, e):
        rubi.append(3385)
        return -Dist(e**S(2)*(m + S(-1))/(S(2)*c), Int((d + e*x)**(m + S(-2))*sin(a + b*x + c*x**S(2)), x), x) + Simp(e*(d + e*x)**(m + S(-1))*sin(a + b*x + c*x**S(2))/(S(2)*c), x)
    rule3385 = ReplacementRule(pattern3385, replacement3385)
    pattern3386 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons166, cons1133)
    def replacement3386(m, b, d, c, a, x, e):
        rubi.append(3386)
        return -Dist((b*e - S(2)*c*d)/(S(2)*c), Int((d + e*x)**(m + S(-1))*sin(a + b*x + c*x**S(2)), x), x) + Dist(e**S(2)*(m + S(-1))/(S(2)*c), Int((d + e*x)**(m + S(-2))*cos(a + b*x + c*x**S(2)), x), x) - Simp(e*(d + e*x)**(m + S(-1))*cos(a + b*x + c*x**S(2))/(S(2)*c), x)
    rule3386 = ReplacementRule(pattern3386, replacement3386)
    pattern3387 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons166, cons1133)
    def replacement3387(m, b, d, c, a, x, e):
        rubi.append(3387)
        return -Dist((b*e - S(2)*c*d)/(S(2)*c), Int((d + e*x)**(m + S(-1))*cos(a + b*x + c*x**S(2)), x), x) - Dist(e**S(2)*(m + S(-1))/(S(2)*c), Int((d + e*x)**(m + S(-2))*sin(a + b*x + c*x**S(2)), x), x) + Simp(e*(d + e*x)**(m + S(-1))*sin(a + b*x + c*x**S(2))/(S(2)*c), x)
    rule3387 = ReplacementRule(pattern3387, replacement3387)
    pattern3388 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons94, cons1132)
    def replacement3388(m, b, d, c, a, x, e):
        rubi.append(3388)
        return -Dist(S(2)*c/(e**S(2)*(m + S(1))), Int((d + e*x)**(m + S(2))*cos(a + b*x + c*x**S(2)), x), x) + Simp((d + e*x)**(m + S(1))*sin(a + b*x + c*x**S(2))/(e*(m + S(1))), x)
    rule3388 = ReplacementRule(pattern3388, replacement3388)
    pattern3389 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons94, cons1132)
    def replacement3389(m, b, d, c, a, x, e):
        rubi.append(3389)
        return Dist(S(2)*c/(e**S(2)*(m + S(1))), Int((d + e*x)**(m + S(2))*sin(a + b*x + c*x**S(2)), x), x) + Simp((d + e*x)**(m + S(1))*cos(a + b*x + c*x**S(2))/(e*(m + S(1))), x)
    rule3389 = ReplacementRule(pattern3389, replacement3389)
    pattern3390 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons94, cons1133)
    def replacement3390(m, b, d, c, a, x, e):
        rubi.append(3390)
        return -Dist(S(2)*c/(e**S(2)*(m + S(1))), Int((d + e*x)**(m + S(2))*cos(a + b*x + c*x**S(2)), x), x) - Dist((b*e - S(2)*c*d)/(e**S(2)*(m + S(1))), Int((d + e*x)**(m + S(1))*cos(a + b*x + c*x**S(2)), x), x) + Simp((d + e*x)**(m + S(1))*sin(a + b*x + c*x**S(2))/(e*(m + S(1))), x)
    rule3390 = ReplacementRule(pattern3390, replacement3390)
    pattern3391 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**m_*cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons31, cons94, cons1133)
    def replacement3391(m, b, d, c, a, x, e):
        rubi.append(3391)
        return Dist(S(2)*c/(e**S(2)*(m + S(1))), Int((d + e*x)**(m + S(2))*sin(a + b*x + c*x**S(2)), x), x) + Dist((b*e - S(2)*c*d)/(e**S(2)*(m + S(1))), Int((d + e*x)**(m + S(1))*sin(a + b*x + c*x**S(2)), x), x) + Simp((d + e*x)**(m + S(1))*cos(a + b*x + c*x**S(2))/(e*(m + S(1))), x)
    rule3391 = ReplacementRule(pattern3391, replacement3391)
    pattern3392 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1507)
    def replacement3392(m, b, d, a, c, x, e):
        rubi.append(3392)
        return Int((d + e*x)**m*sin(a + b*x + c*x**S(2)), x)
    rule3392 = ReplacementRule(pattern3392, replacement3392)
    pattern3393 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0))), x_), cons2, cons3, cons7, cons27, cons48, cons21, cons1507)
    def replacement3393(m, b, d, c, a, x, e):
        rubi.append(3393)
        return Int((d + e*x)**m*cos(a + b*x + c*x**S(2)), x)
    rule3393 = ReplacementRule(pattern3393, replacement3393)
    pattern3394 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*sin(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons85, cons165)
    def replacement3394(m, b, d, a, c, n, x, e):
        rubi.append(3394)
        return Int(ExpandTrigReduce((d + e*x)**m, sin(a + b*x + c*x**S(2))**n, x), x)
    rule3394 = ReplacementRule(pattern3394, replacement3394)
    pattern3395 = Pattern(Integral((x_*WC('e', S(1)) + WC('d', S(0)))**WC('m', S(1))*cos(x_**S(2)*WC('c', S(1)) + x_*WC('b', S(1)) + WC('a', S(0)))**n_, x_), cons2, cons3, cons7, cons27, cons48, cons21, cons85, cons165)
    def replacement3395(m, b, d, c, a, n, x, e):
        rubi.append(3395)
        return Int(ExpandTrigReduce((d + e*x)**m, cos(a + b*x + c*x**S(2))**n, x), x)
    rule3395 = ReplacementRule(pattern3395, replacement3395)
    pattern3396 = Pattern(Integral(u_**WC('m', S(1))*sin(v_)**WC('n', S(1)), x_), cons21, cons148, cons68, cons818, cons819)
    def replacement3396(v, u, m, n, x):
        rubi.append(3396)
        return Int(ExpandToSum(u, x)**m*sin(ExpandToSum(v, x))**n, x)
    rule3396 = ReplacementRule(pattern3396, replacement3396)
    pattern3397 = Pattern(Integral(u_**WC('m', S(1))*cos(v_)**WC('n', S(1)), x_), cons21, cons148, cons68, cons818, cons819)
    def replacement3397(v, u, m, n, x):
        rubi.append(3397)
        return Int(ExpandToSum(u, x)**m*cos(ExpandToSum(v, x))**n, x)
    rule3397 = ReplacementRule(pattern3397, replacement3397)
    return [rule2164, rule2165, rule2166, rule2167, rule2168, rule2169, rule2170, rule2171, rule2172, rule2173, rule2174, rule2175, rule2176, rule2177, rule2178, rule2179, rule2180, rule2181, rule2182, rule2183, rule2184, rule2185, rule2186, rule2187, rule2188, rule2189, rule2190, rule2191, rule2192, rule2193, rule2194, rule2195, rule2196, rule2197, rule2198, rule2199, rule2200, rule2201, rule2202, rule2203, rule2204, rule2205, rule2206, rule2207, rule2208, rule2209, rule2210, rule2211, rule2212, rule2213, rule2214, rule2215, rule2216, rule2217, rule2218, rule2219, rule2220, rule2221, rule2222, rule2223, rule2224, rule2225, rule2226, rule2227, rule2228, rule2229, rule2230, rule2231, rule2232, rule2233, rule2234, rule2235, rule2236, rule2237, rule2238, rule2239, rule2240, rule2241, rule2242, rule2243, rule2244, rule2245, rule2246, rule2247, rule2248, rule2249, rule2250, rule2251, rule2252, rule2253, rule2254, rule2255, rule2256, rule2257, rule2258, rule2259, rule2260, rule2261, rule2262, rule2263, rule2264, rule2265, rule2266, rule2267, rule2268, rule2269, rule2270, rule2271, rule2272, rule2273, rule2274, rule2275, rule2276, rule2277, rule2278, rule2279, rule2280, rule2281, rule2282, rule2283, rule2284, rule2285, rule2286, rule2287, rule2288, rule2289, rule2290, rule2291, rule2292, rule2293, rule2294, rule2295, rule2296, rule2297, rule2298, rule2299, rule2300, rule2301, rule2302, rule2303, rule2304, rule2305, rule2306, rule2307, rule2308, rule2309, rule2310, rule2311, rule2312, rule2313, rule2314, rule2315, rule2316, rule2317, rule2318, rule2319, rule2320, rule2321, rule2322, rule2323, rule2324, rule2325, rule2326, rule2327, rule2328, rule2329, rule2330, rule2331, rule2332, rule2333, rule2334, rule2335, rule2336, rule2337, rule2338, rule2339, rule2340, rule2341, rule2342, rule2343, rule2344, rule2345, rule2346, rule2347, rule2348, rule2349, rule2350, rule2351, rule2352, rule2353, rule2354, rule2355, rule2356, rule2357, rule2358, rule2359, rule2360, rule2361, rule2362, rule2363, rule2364, rule2365, rule2366, rule2367, rule2368, rule2369, rule2370, rule2371, rule2372, rule2373, rule2374, rule2375, rule2376, rule2377, rule2378, rule2379, rule2380, rule2381, rule2382, rule2383, rule2384, rule2385, rule2386, rule2387, rule2388, rule2389, rule2390, rule2391, rule2392, rule2393, rule2394, rule2395, rule2396, rule2397, rule2398, rule2399, rule2400, rule2401, rule2402, rule2403, rule2404, rule2405, rule2406, rule2407, rule2408, rule2409, rule2410, rule2411, rule2412, rule2413, rule2414, rule2415, rule2416, rule2417, rule2418, rule2419, rule2420, rule2421, rule2422, rule2423, rule2424, rule2425, rule2426, rule2427, rule2428, rule2429, rule2430, rule2431, rule2432, rule2433, rule2434, rule2435, rule2436, rule2437, rule2438, rule2439, rule2440, rule2441, rule2442, rule2443, rule2444, rule2445, rule2446, rule2447, rule2448, rule2449, rule2450, rule2451, rule2452, rule2453, rule2454, rule2455, rule2456, rule2457, rule2458, rule2459, rule2460, rule2461, rule2462, rule2463, rule2464, rule2465, rule2466, rule2467, rule2468, rule2469, rule2470, rule2471, rule2472, rule2473, rule2474, rule2475, rule2476, rule2477, rule2478, rule2479, rule2480, rule2481, rule2482, rule2483, rule2484, rule2485, rule2486, rule2487, rule2488, rule2489, rule2490, rule2491, rule2492, rule2493, rule2494, rule2495, rule2496, rule2497, rule2498, rule2499, rule2500, rule2501, rule2502, rule2503, rule2504, rule2505, rule2506, rule2507, rule2508, rule2509, rule2510, rule2511, rule2512, rule2513, rule2514, rule2515, rule2516, rule2517, rule2518, rule2519, rule2520, rule2521, rule2522, rule2523, rule2524, rule2525, rule2526, rule2527, rule2528, rule2529, rule2530, rule2531, rule2532, rule2533, rule2534, rule2535, rule2536, rule2537, rule2538, rule2539, rule2540, rule2541, rule2542, rule2543, rule2544, rule2545, rule2546, rule2547, rule2548, rule2549, rule2550, rule2551, rule2552, rule2553, rule2554, rule2555, rule2556, rule2557, rule2558, rule2559, rule2560, rule2561, rule2562, rule2563, rule2564, rule2565, rule2566, rule2567, rule2568, rule2569, rule2570, rule2571, rule2572, rule2573, rule2574, rule2575, rule2576, rule2577, rule2578, rule2579, rule2580, rule2581, rule2582, rule2583, rule2584, rule2585, rule2586, rule2587, rule2588, rule2589, rule2590, rule2591, rule2592, rule2593, rule2594, rule2595, rule2596, rule2597, rule2598, rule2599, rule2600, rule2601, rule2602, rule2603, rule2604, rule2605, rule2606, rule2607, rule2608, rule2609, rule2610, rule2611, rule2612, rule2613, rule2614, rule2615, rule2616, rule2617, rule2618, rule2619, rule2620, rule2621, rule2622, rule2623, rule2624, rule2625, rule2626, rule2627, rule2628, rule2629, rule2630, rule2631, rule2632, rule2633, rule2634, rule2635, rule2636, rule2637, rule2638, rule2639, rule2640, rule2641, rule2642, rule2643, rule2644, rule2645, rule2646, rule2647, rule2648, rule2649, rule2650, rule2651, rule2652, rule2653, rule2654, rule2655, rule2656, rule2657, rule2658, rule2659, rule2660, rule2661, rule2662, rule2663, rule2664, rule2665, rule2666, rule2667, rule2668, rule2669, rule2670, rule2671, rule2672, rule2673, rule2674, rule2675, rule2676, rule2677, rule2678, rule2679, rule2680, rule2681, rule2682, rule2683, rule2684, rule2685, rule2686, rule2687, rule2688, rule2689, rule2690, rule2691, rule2692, rule2693, rule2694, rule2695, rule2696, rule2697, rule2698, rule2699, rule2700, rule2701, rule2702, rule2703, rule2704, rule2705, rule2706, rule2707, rule2708, rule2709, rule2710, rule2711, rule2712, rule2713, rule2714, rule2715, rule2716, rule2717, rule2718, rule2719, rule2720, rule2721, rule2722, rule2723, rule2724, rule2725, rule2726, rule2727, rule2728, rule2729, rule2730, rule2731, rule2732, rule2733, rule2734, rule2735, rule2736, rule2737, rule2738, rule2739, rule2740, rule2741, rule2742, rule2743, rule2744, rule2745, rule2746, rule2747, rule2748, rule2749, rule2750, rule2751, rule2752, rule2753, rule2754, rule2755, rule2756, rule2757, rule2758, rule2759, rule2760, rule2761, rule2762, rule2763, rule2764, rule2765, rule2766, rule2767, rule2768, rule2769, rule2770, rule2771, rule2772, rule2773, rule2774, rule2775, rule2776, rule2777, rule2778, rule2779, rule2780, rule2781, rule2782, rule2783, rule2784, rule2785, rule2786, rule2787, rule2788, rule2789, rule2790, rule2791, rule2792, rule2793, rule2794, rule2795, rule2796, rule2797, rule2798, rule2799, rule2800, rule2801, rule2802, rule2803, rule2804, rule2805, rule2806, rule2807, rule2808, rule2809, rule2810, rule2811, rule2812, rule2813, rule2814, rule2815, rule2816, rule2817, rule2818, rule2819, rule2820, rule2821, rule2822, rule2823, rule2824, rule2825, rule2826, rule2827, rule2828, rule2829, rule2830, rule2831, rule2832, rule2833, rule2834, rule2835, rule2836, rule2837, rule2838, rule2839, rule2840, rule2841, rule2842, rule2843, rule2844, rule2845, rule2846, rule2847, rule2848, rule2849, rule2850, rule2851, rule2852, rule2853, rule2854, rule2855, rule2856, rule2857, rule2858, rule2859, rule2860, rule2861, rule2862, rule2863, rule2864, rule2865, rule2866, rule2867, rule2868, rule2869, rule2870, rule2871, rule2872, rule2873, rule2874, rule2875, rule2876, rule2877, rule2878, rule2879, rule2880, rule2881, rule2882, rule2883, rule2884, rule2885, rule2886, rule2887, rule2888, rule2889, rule2890, rule2891, rule2892, rule2893, rule2894, rule2895, rule2896, rule2897, rule2898, rule2899, rule2900, rule2901, rule2902, rule2903, rule2904, rule2905, rule2906, rule2907, rule2908, rule2909, rule2910, rule2911, rule2912, rule2913, rule2914, rule2915, rule2916, rule2917, rule2918, rule2919, rule2920, rule2921, rule2922, rule2923, rule2924, rule2925, rule2926, rule2927, rule2928, rule2929, rule2930, rule2931, rule2932, rule2933, rule2934, rule2935, rule2936, rule2937, rule2938, rule2939, rule2940, rule2941, rule2942, rule2943, rule2944, rule2945, rule2946, rule2947, rule2948, rule2949, rule2950, rule2951, rule2952, rule2953, rule2954, rule2955, rule2956, rule2957, rule2958, rule2959, rule2960, rule2961, rule2962, rule2963, rule2964, rule2965, rule2966, rule2967, rule2968, rule2969, rule2970, rule2971, rule2972, rule2973, rule2974, rule2975, rule2976, rule2977, rule2978, rule2979, rule2980, rule2981, rule2982, rule2983, rule2984, rule2985, rule2986, rule2987, rule2988, rule2989, rule2990, rule2991, rule2992, rule2993, rule2994, rule2995, rule2996, rule2997, rule2998, rule2999, rule3000, rule3001, rule3002, rule3003, rule3004, rule3005, rule3006, rule3007, rule3008, rule3009, rule3010, rule3011, rule3012, rule3013, rule3014, rule3015, rule3016, rule3017, rule3018, rule3019, rule3020, rule3021, rule3022, rule3023, rule3024, rule3025, rule3026, rule3027, rule3028, rule3029, rule3030, rule3031, rule3032, rule3033, rule3034, rule3035, rule3036, rule3037, rule3038, rule3039, rule3040, rule3041, rule3042, rule3043, rule3044, rule3045, rule3046, rule3047, rule3048, rule3049, rule3050, rule3051, rule3052, rule3053, rule3054, rule3055, rule3056, rule3057, rule3058, rule3059, rule3060, rule3061, rule3062, rule3063, rule3064, rule3065, rule3066, rule3067, rule3068, rule3069, rule3070, rule3071, rule3072, rule3073, rule3074, rule3075, rule3076, rule3077, rule3078, rule3079, rule3080, rule3081, rule3082, rule3083, rule3084, rule3085, rule3086, rule3087, rule3088, rule3089, rule3090, rule3091, rule3092, rule3093, rule3094, rule3095, rule3096, rule3097, rule3098, rule3099, rule3100, rule3101, rule3102, rule3103, rule3104, rule3105, rule3106, rule3107, rule3108, rule3109, rule3110, rule3111, rule3112, rule3113, rule3114, rule3115, rule3116, rule3117, rule3118, rule3119, rule3120, rule3121, rule3122, rule3123, rule3124, rule3125, rule3126, rule3127, rule3128, rule3129, rule3130, rule3131, rule3132, rule3133, rule3134, rule3135, rule3136, rule3137, rule3138, rule3139, rule3140, rule3141, rule3142, rule3143, rule3144, rule3145, rule3146, rule3147, rule3148, rule3149, rule3150, rule3151, rule3152, rule3153, rule3154, rule3155, rule3156, rule3157, rule3158, rule3159, rule3160, rule3161, rule3162, rule3163, rule3164, rule3165, rule3166, rule3167, rule3168, rule3169, rule3170, rule3171, rule3172, rule3173, rule3174, rule3175, rule3176, rule3177, rule3178, rule3179, rule3180, rule3181, rule3182, rule3183, rule3184, rule3185, rule3186, rule3187, rule3188, rule3189, rule3190, rule3191, rule3192, rule3193, rule3194, rule3195, rule3196, rule3197, rule3198, rule3199, rule3200, rule3201, rule3202, rule3203, rule3204, rule3205, rule3206, rule3207, rule3208, rule3209, rule3210, rule3211, rule3212, rule3213, rule3214, rule3215, rule3216, rule3217, rule3218, rule3219, rule3220, rule3221, rule3222, rule3223, rule3224, rule3225, rule3226, rule3227, rule3228, rule3229, rule3230, rule3231, rule3232, rule3233, rule3234, rule3235, rule3236, rule3237, rule3238, rule3239, rule3240, rule3241, rule3242, rule3243, rule3244, rule3245, rule3246, rule3247, rule3248, rule3249, rule3250, rule3251, rule3252, rule3253, rule3254, rule3255, rule3256, rule3257, rule3258, rule3259, rule3260, rule3261, rule3262, rule3263, rule3264, rule3265, rule3266, rule3267, rule3268, rule3269, rule3270, rule3271, rule3272, rule3273, rule3274, rule3275, rule3276, rule3277, rule3278, rule3279, rule3280, rule3281, rule3282, rule3283, rule3284, rule3285, rule3286, rule3287, rule3288, rule3289, rule3290, rule3291, rule3292, rule3293, rule3294, rule3295, rule3296, rule3297, rule3298, rule3299, rule3300, rule3301, rule3302, rule3303, rule3304, rule3305, rule3306, rule3307, rule3308, rule3309, rule3310, rule3311, rule3312, rule3313, rule3314, rule3315, rule3316, rule3317, rule3318, rule3319, rule3320, rule3321, rule3322, rule3323, rule3324, rule3325, rule3326, rule3327, rule3328, rule3329, rule3330, rule3331, rule3332, rule3333, rule3334, rule3335, rule3336, rule3337, rule3338, rule3339, rule3340, rule3341, rule3342, rule3343, rule3344, rule3345, rule3346, rule3347, rule3348, rule3349, rule3350, rule3351, rule3352, rule3353, rule3354, rule3355, rule3356, rule3357, rule3358, rule3359, rule3360, rule3361, rule3362, rule3363, rule3364, rule3365, rule3366, rule3367, rule3368, rule3369, rule3370, rule3371, rule3372, rule3373, rule3374, rule3375, rule3376, rule3377, rule3378, rule3379, rule3380, rule3381, rule3382, rule3383, rule3384, rule3385, rule3386, rule3387, rule3388, rule3389, rule3390, rule3391, rule3392, rule3393, rule3394, rule3395, rule3396, rule3397, ]
