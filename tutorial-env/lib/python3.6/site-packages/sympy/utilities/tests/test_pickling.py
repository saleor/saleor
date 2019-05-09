import sys
import inspect
import copy
import pickle

from sympy.physics.units import meter

from sympy.utilities.pytest import XFAIL

from sympy.core.basic import Atom, Basic
from sympy.core.core import BasicMeta
from sympy.core.singleton import SingletonRegistry
from sympy.core.symbol import Dummy, Symbol, Wild
from sympy.core.numbers import (E, I, pi, oo, zoo, nan, Integer,
        Rational, Float)
from sympy.core.relational import (Equality, GreaterThan, LessThan, Relational,
        StrictGreaterThan, StrictLessThan, Unequality)
from sympy.core.add import Add
from sympy.core.mul import Mul
from sympy.core.power import Pow
from sympy.core.function import Derivative, Function, FunctionClass, Lambda, \
    WildFunction
from sympy.sets.sets import Interval
from sympy.core.multidimensional import vectorize

from sympy.core.compatibility import HAS_GMPY
from sympy.utilities.exceptions import SymPyDeprecationWarning
from sympy.utilities.pytest import ignore_warnings

from sympy import symbols, S

from sympy.external import import_module
cloudpickle = import_module('cloudpickle')

excluded_attrs = set(
    ['_assumptions', '_mhash', 'message',
    # XXX Remove these after deprecation is done for issue #15887
    '_cache_eigenvects', '_cache_is_diagonalizable']
    )


def check(a, exclude=[], check_attr=True):
    """ Check that pickling and copying round-trips.
    """
    protocols = [0, 1, 2, copy.copy, copy.deepcopy]
    # Python 2.x doesn't support the third pickling protocol
    if sys.version_info >= (3,):
        protocols.extend([3, 4])
    if cloudpickle:
        protocols.extend([cloudpickle])

    for protocol in protocols:
        if protocol in exclude:
            continue

        if callable(protocol):
            if isinstance(a, BasicMeta):
                # Classes can't be copied, but that's okay.
                continue
            b = protocol(a)
        elif inspect.ismodule(protocol):
            b = protocol.loads(protocol.dumps(a))
        else:
            b = pickle.loads(pickle.dumps(a, protocol))

        d1 = dir(a)
        d2 = dir(b)
        assert set(d1) == set(d2)

        if not check_attr:
            continue

        def c(a, b, d):
            for i in d:
                if i in excluded_attrs:
                    continue
                if not hasattr(a, i):
                    continue
                attr = getattr(a, i)
                if not hasattr(attr, "__call__"):
                    assert hasattr(b, i), i
                    assert getattr(b, i) == attr, "%s != %s, protocol: %s" % (getattr(b, i), attr, protocol)

        c(a, b, d1)
        c(b, a, d2)



#================== core =========================


def test_core_basic():
    for c in (Atom, Atom(),
              Basic, Basic(),
              # XXX: dynamically created types are not picklable
              # BasicMeta, BasicMeta("test", (), {}),
              SingletonRegistry, S):
        check(c)


def test_core_symbol():
    # make the Symbol a unique name that doesn't class with any other
    # testing variable in this file since after this test the symbol
    # having the same name will be cached as noncommutative
    for c in (Dummy, Dummy("x", commutative=False), Symbol,
            Symbol("_issue_3130", commutative=False), Wild, Wild("x")):
        check(c)


def test_core_numbers():
    for c in (Integer(2), Rational(2, 3), Float("1.2")):
        check(c)


def test_core_float_copy():
    # See gh-7457
    y = Symbol("x") + 1.0
    check(y)  # does not raise TypeError ("argument is not an mpz")


def test_core_relational():
    x = Symbol("x")
    y = Symbol("y")
    for c in (Equality, Equality(x, y), GreaterThan, GreaterThan(x, y),
              LessThan, LessThan(x, y), Relational, Relational(x, y),
              StrictGreaterThan, StrictGreaterThan(x, y), StrictLessThan,
              StrictLessThan(x, y), Unequality, Unequality(x, y)):
        check(c)


def test_core_add():
    x = Symbol("x")
    for c in (Add, Add(x, 4)):
        check(c)


def test_core_mul():
    x = Symbol("x")
    for c in (Mul, Mul(x, 4)):
        check(c)


def test_core_power():
    x = Symbol("x")
    for c in (Pow, Pow(x, 4)):
        check(c)


def test_core_function():
    x = Symbol("x")
    for f in (Derivative, Derivative(x), Function, FunctionClass, Lambda,
              WildFunction):
        check(f)


def test_core_undefinedfunctions():
    f = Function("f")
    # Full XFAILed test below
    exclude = list(range(5))
    # https://github.com/cloudpipe/cloudpickle/issues/65
    # https://github.com/cloudpipe/cloudpickle/issues/190
    exclude.append(cloudpickle)
    check(f, exclude=exclude)

@XFAIL
def test_core_undefinedfunctions_fail():
    # This fails because f is assumed to be a class at sympy.basic.function.f
    f = Function("f")
    check(f)


def test_core_interval():
    for c in (Interval, Interval(0, 2)):
        check(c)


def test_core_multidimensional():
    for c in (vectorize, vectorize(0)):
        check(c)


def test_Singletons():
    protocols = [0, 1, 2]
    if sys.version_info >= (3,):
        protocols.extend([3, 4])
    copiers = [copy.copy, copy.deepcopy]
    copiers += [lambda x: pickle.loads(pickle.dumps(x, proto))
            for proto in protocols]
    if cloudpickle:
        copiers += [lambda x: cloudpickle.loads(cloudpickle.dumps(x))]

    for obj in (Integer(-1), Integer(0), Integer(1), Rational(1, 2), pi, E, I,
            oo, -oo, zoo, nan, S.GoldenRatio, S.TribonacciConstant,
            S.EulerGamma, S.Catalan, S.EmptySet, S.IdentityFunction):
        for func in copiers:
            assert func(obj) is obj


#================== functions ===================
from sympy.functions import (Piecewise, lowergamma, acosh,
        chebyshevu, chebyshevt, ln, chebyshevt_root, binomial, legendre,
        Heaviside, factorial, bernoulli, coth, tanh, assoc_legendre, sign,
        arg, asin, DiracDelta, re, rf, Abs, uppergamma, binomial, sinh, Ynm,
        cos, cot, acos, acot, gamma, bell, hermite, harmonic,
        LambertW, zeta, log, factorial, asinh, acoth, Znm,
        cosh, dirichlet_eta, Eijk, loggamma, erf, ceiling, im, fibonacci,
        tribonacci, conjugate, tan, chebyshevu_root, floor, atanh, sqrt,
        RisingFactorial, sin, atan, ff, FallingFactorial, lucas, atan2,
        polygamma, exp)


def test_functions():
    one_var = (acosh, ln, Heaviside, factorial, bernoulli, coth, tanh,
            sign, arg, asin, DiracDelta, re, Abs, sinh, cos, cot, acos, acot,
            gamma, bell, harmonic, LambertW, zeta, log, factorial, asinh,
            acoth, cosh, dirichlet_eta, loggamma, erf, ceiling, im, fibonacci,
            tribonacci, conjugate, tan, floor, atanh, sin, atan, lucas, exp)
    two_var = (rf, ff, lowergamma, chebyshevu, chebyshevt, binomial,
            atan2, polygamma, hermite, legendre, uppergamma)
    x, y, z = symbols("x,y,z")
    others = (chebyshevt_root, chebyshevu_root, Eijk(x, y, z),
            Piecewise( (0, x < -1), (x**2, x <= 1), (x**3, True)),
            assoc_legendre)
    for cls in one_var:
        check(cls)
        c = cls(x)
        check(c)
    for cls in two_var:
        check(cls)
        c = cls(x, y)
        check(c)
    for cls in others:
        check(cls)

#================== geometry ====================
from sympy.geometry.entity import GeometryEntity
from sympy.geometry.point import Point
from sympy.geometry.ellipse import Circle, Ellipse
from sympy.geometry.line import Line, LinearEntity, Ray, Segment
from sympy.geometry.polygon import Polygon, RegularPolygon, Triangle


def test_geometry():
    p1 = Point(1, 2)
    p2 = Point(2, 3)
    p3 = Point(0, 0)
    p4 = Point(0, 1)
    for c in (
        GeometryEntity, GeometryEntity(), Point, p1, Circle, Circle(p1, 2),
        Ellipse, Ellipse(p1, 3, 4), Line, Line(p1, p2), LinearEntity,
        LinearEntity(p1, p2), Ray, Ray(p1, p2), Segment, Segment(p1, p2),
        Polygon, Polygon(p1, p2, p3, p4), RegularPolygon,
            RegularPolygon(p1, 4, 5), Triangle, Triangle(p1, p2, p3)):
        check(c, check_attr=False)

#================== integrals ====================
from sympy.integrals.integrals import Integral


def test_integrals():
    x = Symbol("x")
    for c in (Integral, Integral(x)):
        check(c)

#==================== logic =====================
from sympy.core.logic import Logic


def test_logic():
    for c in (Logic, Logic(1)):
        check(c)

#================== matrices ====================
from sympy.matrices import Matrix, SparseMatrix


def test_matrices():
    for c in (Matrix, Matrix([1, 2, 3]), SparseMatrix, SparseMatrix([[1, 2], [3, 4]])):
        check(c)

#================== ntheory =====================
from sympy.ntheory.generate import Sieve


def test_ntheory():
    for c in (Sieve, Sieve()):
        check(c)

#================== physics =====================
from sympy.physics.paulialgebra import Pauli
from sympy.physics.units import Unit


def test_physics():
    for c in (Unit, meter, Pauli, Pauli(1)):
        check(c)

#================== plotting ====================
# XXX: These tests are not complete, so XFAIL them


@XFAIL
def test_plotting():
    from sympy.plotting.color_scheme import ColorGradient, ColorScheme
    from sympy.plotting.managed_window import ManagedWindow
    from sympy.plotting.plot import Plot, ScreenShot
    from sympy.plotting.plot_axes import PlotAxes, PlotAxesBase, PlotAxesFrame, PlotAxesOrdinate
    from sympy.plotting.plot_camera import PlotCamera
    from sympy.plotting.plot_controller import PlotController
    from sympy.plotting.plot_curve import PlotCurve
    from sympy.plotting.plot_interval import PlotInterval
    from sympy.plotting.plot_mode import PlotMode
    from sympy.plotting.plot_modes import Cartesian2D, Cartesian3D, Cylindrical, \
        ParametricCurve2D, ParametricCurve3D, ParametricSurface, Polar, Spherical
    from sympy.plotting.plot_object import PlotObject
    from sympy.plotting.plot_surface import PlotSurface
    from sympy.plotting.plot_window import PlotWindow
    for c in (
        ColorGradient, ColorGradient(0.2, 0.4), ColorScheme, ManagedWindow,
        ManagedWindow, Plot, ScreenShot, PlotAxes, PlotAxesBase,
        PlotAxesFrame, PlotAxesOrdinate, PlotCamera, PlotController,
        PlotCurve, PlotInterval, PlotMode, Cartesian2D, Cartesian3D,
        Cylindrical, ParametricCurve2D, ParametricCurve3D,
        ParametricSurface, Polar, Spherical, PlotObject, PlotSurface,
            PlotWindow):
        check(c)


@XFAIL
def test_plotting2():
    from sympy.plotting.color_scheme import ColorGradient, ColorScheme
    from sympy.plotting.managed_window import ManagedWindow
    from sympy.plotting.plot import Plot, ScreenShot
    from sympy.plotting.plot_axes import PlotAxes, PlotAxesBase, PlotAxesFrame, PlotAxesOrdinate
    from sympy.plotting.plot_camera import PlotCamera
    from sympy.plotting.plot_controller import PlotController
    from sympy.plotting.plot_curve import PlotCurve
    from sympy.plotting.plot_interval import PlotInterval
    from sympy.plotting.plot_mode import PlotMode
    from sympy.plotting.plot_modes import Cartesian2D, Cartesian3D, Cylindrical, \
        ParametricCurve2D, ParametricCurve3D, ParametricSurface, Polar, Spherical
    from sympy.plotting.plot_object import PlotObject
    from sympy.plotting.plot_surface import PlotSurface
    from sympy.plotting.plot_window import PlotWindow
    check(ColorScheme("rainbow"))
    check(Plot(1, visible=False))
    check(PlotAxes())

#================== polys =======================
from sympy import Poly, ZZ, QQ, lex

def test_pickling_polys_polytools():
    from sympy.polys.polytools import Poly, PurePoly, GroebnerBasis
    x = Symbol('x')

    for c in (Poly, Poly(x, x)):
        check(c)

    for c in (PurePoly, PurePoly(x)):
        check(c)

    # TODO: fix pickling of Options class (see GroebnerBasis._options)
    # for c in (GroebnerBasis, GroebnerBasis([x**2 - 1], x, order=lex)):
    #     check(c)

def test_pickling_polys_polyclasses():
    from sympy.polys.polyclasses import DMP, DMF, ANP

    for c in (DMP, DMP([[ZZ(1)], [ZZ(2)], [ZZ(3)]], ZZ)):
        check(c)
    for c in (DMF, DMF(([ZZ(1), ZZ(2)], [ZZ(1), ZZ(3)]), ZZ)):
        check(c)
    for c in (ANP, ANP([QQ(1), QQ(2)], [QQ(1), QQ(2), QQ(3)], QQ)):
        check(c)

@XFAIL
def test_pickling_polys_rings():
    # NOTE: can't use protocols < 2 because we have to execute __new__ to
    # make sure caching of rings works properly.

    from sympy.polys.rings import PolyRing

    ring = PolyRing("x,y,z", ZZ, lex)

    for c in (PolyRing, ring):
        check(c, exclude=[0, 1])

    for c in (ring.dtype, ring.one):
        check(c, exclude=[0, 1], check_attr=False) # TODO: Py3k

def test_pickling_polys_fields():
    # NOTE: can't use protocols < 2 because we have to execute __new__ to
    # make sure caching of fields works properly.

    from sympy.polys.fields import FracField

    field = FracField("x,y,z", ZZ, lex)

    # TODO: AssertionError: assert id(obj) not in self.memo
    # for c in (FracField, field):
    #     check(c, exclude=[0, 1])

    # TODO: AssertionError: assert id(obj) not in self.memo
    # for c in (field.dtype, field.one):
    #     check(c, exclude=[0, 1])

def test_pickling_polys_elements():
    from sympy.polys.domains.pythonrational import PythonRational
    from sympy.polys.domains.pythonfinitefield import PythonFiniteField
    from sympy.polys.domains.mpelements import MPContext

    for c in (PythonRational, PythonRational(1, 7)):
        check(c)

    gf = PythonFiniteField(17)

    # TODO: fix pickling of ModularInteger
    # for c in (gf.dtype, gf(5)):
    #     check(c)

    mp = MPContext()

    # TODO: fix pickling of RealElement
    # for c in (mp.mpf, mp.mpf(1.0)):
    #     check(c)

    # TODO: fix pickling of ComplexElement
    # for c in (mp.mpc, mp.mpc(1.0, -1.5)):
    #     check(c)

def test_pickling_polys_domains():
    from sympy.polys.domains.pythonfinitefield import PythonFiniteField
    from sympy.polys.domains.pythonintegerring import PythonIntegerRing
    from sympy.polys.domains.pythonrationalfield import PythonRationalField

    # TODO: fix pickling of ModularInteger
    # for c in (PythonFiniteField, PythonFiniteField(17)):
    #     check(c)

    for c in (PythonIntegerRing, PythonIntegerRing()):
        check(c, check_attr=False)

    for c in (PythonRationalField, PythonRationalField()):
        check(c, check_attr=False)

    if HAS_GMPY:
        from sympy.polys.domains.gmpyfinitefield import GMPYFiniteField
        from sympy.polys.domains.gmpyintegerring import GMPYIntegerRing
        from sympy.polys.domains.gmpyrationalfield import GMPYRationalField

        # TODO: fix pickling of ModularInteger
        # for c in (GMPYFiniteField, GMPYFiniteField(17)):
        #     check(c)

        for c in (GMPYIntegerRing, GMPYIntegerRing()):
            check(c, check_attr=False)

        for c in (GMPYRationalField, GMPYRationalField()):
            check(c, check_attr=False)

    from sympy.polys.domains.realfield import RealField
    from sympy.polys.domains.complexfield import ComplexField
    from sympy.polys.domains.algebraicfield import AlgebraicField
    from sympy.polys.domains.polynomialring import PolynomialRing
    from sympy.polys.domains.fractionfield import FractionField
    from sympy.polys.domains.expressiondomain import ExpressionDomain

    # TODO: fix pickling of RealElement
    # for c in (RealField, RealField(100)):
    #     check(c)

    # TODO: fix pickling of ComplexElement
    # for c in (ComplexField, ComplexField(100)):
    #     check(c)

    for c in (AlgebraicField, AlgebraicField(QQ, sqrt(3))):
        check(c, check_attr=False)

    # TODO: AssertionError
    # for c in (PolynomialRing, PolynomialRing(ZZ, "x,y,z")):
    #     check(c)

    # TODO: AttributeError: 'PolyElement' object has no attribute 'ring'
    # for c in (FractionField, FractionField(ZZ, "x,y,z")):
    #     check(c)

    for c in (ExpressionDomain, ExpressionDomain()):
        check(c, check_attr=False)

def test_pickling_polys_numberfields():
    from sympy.polys.numberfields import AlgebraicNumber

    for c in (AlgebraicNumber, AlgebraicNumber(sqrt(3))):
        check(c, check_attr=False)

def test_pickling_polys_orderings():
    from sympy.polys.orderings import (LexOrder, GradedLexOrder,
        ReversedGradedLexOrder, ProductOrder, InverseOrder)

    for c in (LexOrder, LexOrder()):
        check(c)

    for c in (GradedLexOrder, GradedLexOrder()):
        check(c)

    for c in (ReversedGradedLexOrder, ReversedGradedLexOrder()):
        check(c)

    # TODO: Argh, Python is so naive. No lambdas nor inner function support in
    # pickling module. Maybe someone could figure out what to do with this.
    #
    # for c in (ProductOrder, ProductOrder((LexOrder(),       lambda m: m[:2]),
    #                                      (GradedLexOrder(), lambda m: m[2:]))):
    #     check(c)

    for c in (InverseOrder, InverseOrder(LexOrder())):
        check(c)

def test_pickling_polys_monomials():
    from sympy.polys.monomials import MonomialOps, Monomial
    x, y, z = symbols("x,y,z")

    for c in (MonomialOps, MonomialOps(3)):
        check(c)

    for c in (Monomial, Monomial((1, 2, 3), (x, y, z))):
        check(c)

def test_pickling_polys_errors():
    from sympy.polys.polyerrors import (ExactQuotientFailed, OperationNotSupported,
        HeuristicGCDFailed, HomomorphismFailed, IsomorphismFailed, ExtraneousFactors,
        EvaluationFailed, RefinementFailed, CoercionFailed, NotInvertible, NotReversible,
        NotAlgebraic, DomainError, PolynomialError, UnificationFailed, GeneratorsError,
        GeneratorsNeeded, ComputationFailed, UnivariatePolynomialError,
        MultivariatePolynomialError, PolificationFailed, OptionError, FlagError)

    x = Symbol('x')

    # TODO: TypeError: __init__() takes at least 3 arguments (1 given)
    # for c in (ExactQuotientFailed, ExactQuotientFailed(x, 3*x, ZZ)):
    #    check(c)

    # TODO: TypeError: can't pickle instancemethod objects
    # for c in (OperationNotSupported, OperationNotSupported(Poly(x), Poly.gcd)):
    #    check(c)

    for c in (HeuristicGCDFailed, HeuristicGCDFailed()):
        check(c)

    for c in (HomomorphismFailed, HomomorphismFailed()):
        check(c)

    for c in (IsomorphismFailed, IsomorphismFailed()):
        check(c)

    for c in (ExtraneousFactors, ExtraneousFactors()):
        check(c)

    for c in (EvaluationFailed, EvaluationFailed()):
        check(c)

    for c in (RefinementFailed, RefinementFailed()):
        check(c)

    for c in (CoercionFailed, CoercionFailed()):
        check(c)

    for c in (NotInvertible, NotInvertible()):
        check(c)

    for c in (NotReversible, NotReversible()):
        check(c)

    for c in (NotAlgebraic, NotAlgebraic()):
        check(c)

    for c in (DomainError, DomainError()):
        check(c)

    for c in (PolynomialError, PolynomialError()):
        check(c)

    for c in (UnificationFailed, UnificationFailed()):
        check(c)

    for c in (GeneratorsError, GeneratorsError()):
        check(c)

    for c in (GeneratorsNeeded, GeneratorsNeeded()):
        check(c)

    # TODO: PicklingError: Can't pickle <function <lambda> at 0x38578c0>: it's not found as __main__.<lambda>
    # for c in (ComputationFailed, ComputationFailed(lambda t: t, 3, None)):
    #    check(c)

    for c in (UnivariatePolynomialError, UnivariatePolynomialError()):
        check(c)

    for c in (MultivariatePolynomialError, MultivariatePolynomialError()):
        check(c)

    # TODO: TypeError: __init__() takes at least 3 arguments (1 given)
    # for c in (PolificationFailed, PolificationFailed({}, x, x, False)):
    #    check(c)

    for c in (OptionError, OptionError()):
        check(c)

    for c in (FlagError, FlagError()):
        check(c)

def test_pickling_polys_options():
    from sympy.polys.polyoptions import Options

    # TODO: fix pickling of `symbols' flag
    # for c in (Options, Options((), dict(domain='ZZ', polys=False))):
    #    check(c)

# TODO: def test_pickling_polys_rootisolation():
#    RealInterval
#    ComplexInterval

def test_pickling_polys_rootoftools():
    from sympy.polys.rootoftools import CRootOf, RootSum

    x = Symbol('x')
    f = x**3 + x + 3

    for c in (CRootOf, CRootOf(f, 0)):
        check(c)

    for c in (RootSum, RootSum(f, exp)):
        check(c)

#================== printing ====================
from sympy.printing.latex import LatexPrinter
from sympy.printing.mathml import MathMLContentPrinter, MathMLPresentationPrinter
from sympy.printing.pretty.pretty import PrettyPrinter
from sympy.printing.pretty.stringpict import prettyForm, stringPict
from sympy.printing.printer import Printer
from sympy.printing.python import PythonPrinter


def test_printing():
    for c in (LatexPrinter, LatexPrinter(), MathMLContentPrinter,
              MathMLPresentationPrinter, PrettyPrinter, prettyForm, stringPict,
              stringPict("a"), Printer, Printer(), PythonPrinter,
              PythonPrinter()):
        check(c)


@XFAIL
def test_printing1():
    check(MathMLContentPrinter())


@XFAIL
def test_printing2():
    check(MathMLPresentationPrinter())


@XFAIL
def test_printing3():
    check(PrettyPrinter())

#================== series ======================
from sympy.series.limits import Limit
from sympy.series.order import Order


def test_series():
    e = Symbol("e")
    x = Symbol("x")
    for c in (Limit, Limit(e, x, 1), Order, Order(e)):
        check(c)

#================== concrete ==================
from sympy.concrete.products import Product
from sympy.concrete.summations import Sum


def test_concrete():
    x = Symbol("x")
    for c in (Product, Product(x, (x, 2, 4)), Sum, Sum(x, (x, 2, 4))):
        check(c)

def test_deprecation_warning():
    w = SymPyDeprecationWarning('value', 'feature', issue=12345, deprecated_since_version='1.0')
    check(w)
