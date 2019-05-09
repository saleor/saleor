from distutils.version import LooseVersion as V
from itertools import product
import math
import inspect

import mpmath
from sympy.utilities.pytest import XFAIL, raises
from sympy import (
    symbols, lambdify, sqrt, sin, cos, tan, pi, acos, acosh, Rational,
    Float, Matrix, Lambda, Piecewise, exp, Integral, oo, I, Abs, Function,
    true, false, And, Or, Not, ITE, Min, Max, floor, diff, IndexedBase, Sum,
    DotProduct, Eq, Dummy, sinc, erf, erfc, factorial, gamma, loggamma,
    digamma, RisingFactorial, besselj, bessely, besseli, besselk, S,
    MatrixSymbol, chebyshevt, chebyshevu, legendre, hermite, laguerre,
    gegenbauer, assoc_legendre, assoc_laguerre, jacobi)
from sympy.printing.lambdarepr import LambdaPrinter
from sympy.printing.pycode import NumPyPrinter
from sympy.utilities.lambdify import implemented_function, lambdastr
from sympy.utilities.pytest import skip
from sympy.utilities.decorator import conserve_mpmath_dps
from sympy.external import import_module
from sympy.functions.special.gamma_functions import uppergamma,lowergamma

import sympy


MutableDenseMatrix = Matrix

numpy = import_module('numpy')
scipy = import_module('scipy')
scipy_special = import_module('scipy.special')
numexpr = import_module('numexpr')
tensorflow = import_module('tensorflow')

if tensorflow:
    # Hide Tensorflow warnings
    import os
    os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

w, x, y, z = symbols('w,x,y,z')

#================== Test different arguments =======================


def test_no_args():
    f = lambdify([], 1)
    raises(TypeError, lambda: f(-1))
    assert f() == 1


def test_single_arg():
    f = lambdify(x, 2*x)
    assert f(1) == 2


def test_list_args():
    f = lambdify([x, y], x + y)
    assert f(1, 2) == 3


def test_nested_args():
    f1 = lambdify([[w, x]], [w, x])
    assert f1([91, 2]) == [91, 2]
    raises(TypeError, lambda: f1(1, 2))

    f2 = lambdify([(w, x), (y, z)], [w, x, y, z])
    assert f2((18, 12), (73, 4)) == [18, 12, 73, 4]
    raises(TypeError, lambda: f2(3, 4))

    f3 = lambdify([w, [[[x]], y], z], [w, x, y, z])
    assert f3(10, [[[52]], 31], 44) == [10, 52, 31, 44]


def test_str_args():
    f = lambdify('x,y,z', 'z,y,x')
    assert f(3, 2, 1) == (1, 2, 3)
    assert f(1.0, 2.0, 3.0) == (3.0, 2.0, 1.0)
    # make sure correct number of args required
    raises(TypeError, lambda: f(0))


def test_own_namespace_1():
    myfunc = lambda x: 1
    f = lambdify(x, sin(x), {"sin": myfunc})
    assert f(0.1) == 1
    assert f(100) == 1


def test_own_namespace_2():
    def myfunc(x):
        return 1
    f = lambdify(x, sin(x), {'sin': myfunc})
    assert f(0.1) == 1
    assert f(100) == 1


def test_own_module():
    f = lambdify(x, sin(x), math)
    assert f(0) == 0.0


def test_bad_args():
    # no vargs given
    raises(TypeError, lambda: lambdify(1))
    # same with vector exprs
    raises(TypeError, lambda: lambdify([1, 2]))


def test_atoms():
    # Non-Symbol atoms should not be pulled out from the expression namespace
    f = lambdify(x, pi + x, {"pi": 3.14})
    assert f(0) == 3.14
    f = lambdify(x, I + x, {"I": 1j})
    assert f(1) == 1 + 1j

#================== Test different modules =========================

# high precision output of sin(0.2*pi) is used to detect if precision is lost unwanted


@conserve_mpmath_dps
def test_sympy_lambda():
    mpmath.mp.dps = 50
    sin02 = mpmath.mpf("0.19866933079506121545941262711838975037020672954020")
    f = lambdify(x, sin(x), "sympy")
    assert f(x) == sin(x)
    prec = 1e-15
    assert -prec < f(Rational(1, 5)).evalf() - Float(str(sin02)) < prec
    # arctan is in numpy module and should not be available
    raises(NameError, lambda: lambdify(x, arctan(x), "sympy"))


@conserve_mpmath_dps
def test_math_lambda():
    mpmath.mp.dps = 50
    sin02 = mpmath.mpf("0.19866933079506121545941262711838975037020672954020")
    f = lambdify(x, sin(x), "math")
    prec = 1e-15
    assert -prec < f(0.2) - sin02 < prec
    raises(TypeError, lambda: f(x))
           # if this succeeds, it can't be a python math function


@conserve_mpmath_dps
def test_mpmath_lambda():
    mpmath.mp.dps = 50
    sin02 = mpmath.mpf("0.19866933079506121545941262711838975037020672954020")
    f = lambdify(x, sin(x), "mpmath")
    prec = 1e-49  # mpmath precision is around 50 decimal places
    assert -prec < f(mpmath.mpf("0.2")) - sin02 < prec
    raises(TypeError, lambda: f(x))
           # if this succeeds, it can't be a mpmath function


@conserve_mpmath_dps
def test_number_precision():
    mpmath.mp.dps = 50
    sin02 = mpmath.mpf("0.19866933079506121545941262711838975037020672954020")
    f = lambdify(x, sin02, "mpmath")
    prec = 1e-49  # mpmath precision is around 50 decimal places
    assert -prec < f(0) - sin02 < prec

@conserve_mpmath_dps
def test_mpmath_precision():
    mpmath.mp.dps = 100
    assert str(lambdify((), pi.evalf(100), 'mpmath')()) == str(pi.evalf(100))

#================== Test Translations ==============================
# We can only check if all translated functions are valid. It has to be checked
# by hand if they are complete.


def test_math_transl():
    from sympy.utilities.lambdify import MATH_TRANSLATIONS
    for sym, mat in MATH_TRANSLATIONS.items():
        assert sym in sympy.__dict__
        assert mat in math.__dict__


def test_mpmath_transl():
    from sympy.utilities.lambdify import MPMATH_TRANSLATIONS
    for sym, mat in MPMATH_TRANSLATIONS.items():
        assert sym in sympy.__dict__ or sym == 'Matrix'
        assert mat in mpmath.__dict__


def test_numpy_transl():
    if not numpy:
        skip("numpy not installed.")

    from sympy.utilities.lambdify import NUMPY_TRANSLATIONS
    for sym, nump in NUMPY_TRANSLATIONS.items():
        assert sym in sympy.__dict__
        assert nump in numpy.__dict__


def test_scipy_transl():
    if not scipy:
        skip("scipy not installed.")

    from sympy.utilities.lambdify import SCIPY_TRANSLATIONS
    for sym, scip in SCIPY_TRANSLATIONS.items():
        assert sym in sympy.__dict__
        assert scip in scipy.__dict__ or scip in scipy.special.__dict__


def test_tensorflow_transl():
    if not tensorflow:
        skip("tensorflow not installed")

    from sympy.utilities.lambdify import TENSORFLOW_TRANSLATIONS
    for sym, tens in TENSORFLOW_TRANSLATIONS.items():
        assert sym in sympy.__dict__
        assert tens in tensorflow.__dict__


def test_numpy_translation_abs():
    if not numpy:
        skip("numpy not installed.")

    f = lambdify(x, Abs(x), "numpy")
    assert f(-1) == 1
    assert f(1) == 1


def test_numexpr_printer():
    if not numexpr:
        skip("numexpr not installed.")

    # if translation/printing is done incorrectly then evaluating
    # a lambdified numexpr expression will throw an exception
    from sympy.printing.lambdarepr import NumExprPrinter

    blacklist = ('where', 'complex', 'contains')
    arg_tuple = (x, y, z) # some functions take more than one argument
    for sym in NumExprPrinter._numexpr_functions.keys():
        if sym in blacklist:
            continue
        ssym = S(sym)
        if hasattr(ssym, '_nargs'):
            nargs = ssym._nargs[0]
        else:
            nargs = 1
        args = arg_tuple[:nargs]
        f = lambdify(args, ssym(*args), modules='numexpr')
        assert f(*(1, )*nargs) is not None


def test_issue_9334():
    if not numexpr:
        skip("numexpr not installed.")
    if not numpy:
        skip("numpy not installed.")
    expr = S('b*a - sqrt(a**2)')
    a, b = sorted(expr.free_symbols, key=lambda s: s.name)
    func_numexpr = lambdify((a,b), expr, modules=[numexpr], dummify=False)
    foo, bar = numpy.random.random((2, 4))
    func_numexpr(foo, bar)

#================== Test some functions ============================


def test_exponentiation():
    f = lambdify(x, x**2)
    assert f(-1) == 1
    assert f(0) == 0
    assert f(1) == 1
    assert f(-2) == 4
    assert f(2) == 4
    assert f(2.5) == 6.25


def test_sqrt():
    f = lambdify(x, sqrt(x))
    assert f(0) == 0.0
    assert f(1) == 1.0
    assert f(4) == 2.0
    assert abs(f(2) - 1.414) < 0.001
    assert f(6.25) == 2.5


def test_trig():
    f = lambdify([x], [cos(x), sin(x)], 'math')
    d = f(pi)
    prec = 1e-11
    assert -prec < d[0] + 1 < prec
    assert -prec < d[1] < prec
    d = f(3.14159)
    prec = 1e-5
    assert -prec < d[0] + 1 < prec
    assert -prec < d[1] < prec

#================== Test vectors ===================================


def test_vector_simple():
    f = lambdify((x, y, z), (z, y, x))
    assert f(3, 2, 1) == (1, 2, 3)
    assert f(1.0, 2.0, 3.0) == (3.0, 2.0, 1.0)
    # make sure correct number of args required
    raises(TypeError, lambda: f(0))


def test_vector_discontinuous():
    f = lambdify(x, (-1/x, 1/x))
    raises(ZeroDivisionError, lambda: f(0))
    assert f(1) == (-1.0, 1.0)
    assert f(2) == (-0.5, 0.5)
    assert f(-2) == (0.5, -0.5)


def test_trig_symbolic():
    f = lambdify([x], [cos(x), sin(x)], 'math')
    d = f(pi)
    assert abs(d[0] + 1) < 0.0001
    assert abs(d[1] - 0) < 0.0001


def test_trig_float():
    f = lambdify([x], [cos(x), sin(x)])
    d = f(3.14159)
    assert abs(d[0] + 1) < 0.0001
    assert abs(d[1] - 0) < 0.0001


def test_docs():
    f = lambdify(x, x**2)
    assert f(2) == 4
    f = lambdify([x, y, z], [z, y, x])
    assert f(1, 2, 3) == [3, 2, 1]
    f = lambdify(x, sqrt(x))
    assert f(4) == 2.0
    f = lambdify((x, y), sin(x*y)**2)
    assert f(0, 5) == 0


def test_math():
    f = lambdify((x, y), sin(x), modules="math")
    assert f(0, 5) == 0


def test_sin():
    f = lambdify(x, sin(x)**2)
    assert isinstance(f(2), float)
    f = lambdify(x, sin(x)**2, modules="math")
    assert isinstance(f(2), float)


def test_matrix():
    A = Matrix([[x, x*y], [sin(z) + 4, x**z]])
    sol = Matrix([[1, 2], [sin(3) + 4, 1]])
    f = lambdify((x, y, z), A, modules="sympy")
    assert f(1, 2, 3) == sol
    f = lambdify((x, y, z), (A, [A]), modules="sympy")
    assert f(1, 2, 3) == (sol, [sol])
    J = Matrix((x, x + y)).jacobian((x, y))
    v = Matrix((x, y))
    sol = Matrix([[1, 0], [1, 1]])
    assert lambdify(v, J, modules='sympy')(1, 2) == sol
    assert lambdify(v.T, J, modules='sympy')(1, 2) == sol


def test_numpy_matrix():
    if not numpy:
        skip("numpy not installed.")
    A = Matrix([[x, x*y], [sin(z) + 4, x**z]])
    sol_arr = numpy.array([[1, 2], [numpy.sin(3) + 4, 1]])
    #Lambdify array first, to ensure return to array as default
    f = lambdify((x, y, z), A, ['numpy'])
    numpy.testing.assert_allclose(f(1, 2, 3), sol_arr)
    #Check that the types are arrays and matrices
    assert isinstance(f(1, 2, 3), numpy.ndarray)

    # gh-15071
    class dot(Function):
        pass
    x_dot_mtx = dot(x, Matrix([[2], [1], [0]]))
    f_dot1 = lambdify(x, x_dot_mtx)
    inp = numpy.zeros((17, 3))
    assert numpy.all(f_dot1(inp) == 0)

    strict_kw = dict(allow_unknown_functions=False, inline=True, fully_qualified_modules=False)
    p2 = NumPyPrinter(dict(user_functions={'dot': 'dot'}, **strict_kw))
    f_dot2 = lambdify(x, x_dot_mtx, printer=p2)
    assert numpy.all(f_dot2(inp) == 0)

    p3 = NumPyPrinter(strict_kw)
    # The line below should probably fail upon construction (before calling with "(inp)"):
    raises(Exception, lambda: lambdify(x, x_dot_mtx, printer=p3)(inp))


def test_numpy_transpose():
    if not numpy:
        skip("numpy not installed.")
    A = Matrix([[1, x], [0, 1]])
    f = lambdify((x), A.T, modules="numpy")
    numpy.testing.assert_array_equal(f(2), numpy.array([[1, 0], [2, 1]]))


def test_numpy_dotproduct():
    if not numpy:
        skip("numpy not installed")
    A = Matrix([x, y, z])
    f1 = lambdify([x, y, z], DotProduct(A, A), modules='numpy')
    f2 = lambdify([x, y, z], DotProduct(A, A.T), modules='numpy')
    f3 = lambdify([x, y, z], DotProduct(A.T, A), modules='numpy')
    f4 = lambdify([x, y, z], DotProduct(A, A.T), modules='numpy')

    assert f1(1, 2, 3) == \
           f2(1, 2, 3) == \
           f3(1, 2, 3) == \
           f4(1, 2, 3) == \
           numpy.array([14])


def test_numpy_inverse():
    if not numpy:
        skip("numpy not installed.")
    A = Matrix([[1, x], [0, 1]])
    f = lambdify((x), A**-1, modules="numpy")
    numpy.testing.assert_array_equal(f(2), numpy.array([[1, -2], [0,  1]]))


def test_numpy_old_matrix():
    if not numpy:
        skip("numpy not installed.")
    A = Matrix([[x, x*y], [sin(z) + 4, x**z]])
    sol_arr = numpy.array([[1, 2], [numpy.sin(3) + 4, 1]])
    f = lambdify((x, y, z), A, [{'ImmutableDenseMatrix': numpy.matrix}, 'numpy'])
    numpy.testing.assert_allclose(f(1, 2, 3), sol_arr)
    assert isinstance(f(1, 2, 3), numpy.matrix)


def test_python_div_zero_issue_11306():
    if not numpy:
        skip("numpy not installed.")
    p = Piecewise((1 / x, y < -1), (x, y < 1), (1 / x, True))
    f = lambdify([x, y], p, modules='numpy')
    numpy.seterr(divide='ignore')
    assert float(f(numpy.array([0]),numpy.array([0.5]))) == 0
    assert str(float(f(numpy.array([0]),numpy.array([1])))) == 'inf'
    numpy.seterr(divide='warn')


def test_issue9474():
    mods = [None, 'math']
    if numpy:
        mods.append('numpy')
    if mpmath:
        mods.append('mpmath')
    for mod in mods:
        f = lambdify(x, S(1)/x, modules=mod)
        assert f(2) == 0.5
        f = lambdify(x, floor(S(1)/x), modules=mod)
        assert f(2) == 0

    for absfunc, modules in product([Abs, abs], mods):
        f = lambdify(x, absfunc(x), modules=modules)
        assert f(-1) == 1
        assert f(1) == 1
        assert f(3+4j) == 5


def test_issue_9871():
    if not numexpr:
        skip("numexpr not installed.")
    if not numpy:
        skip("numpy not installed.")

    r = sqrt(x**2 + y**2)
    expr = diff(1/r, x)

    xn = yn = numpy.linspace(1, 10, 16)
    # expr(xn, xn) = -xn/(sqrt(2)*xn)^3
    fv_exact = -numpy.sqrt(2.)**-3 * xn**-2

    fv_numpy = lambdify((x, y), expr, modules='numpy')(xn, yn)
    fv_numexpr = lambdify((x, y), expr, modules='numexpr')(xn, yn)
    numpy.testing.assert_allclose(fv_numpy, fv_exact, rtol=1e-10)
    numpy.testing.assert_allclose(fv_numexpr, fv_exact, rtol=1e-10)


def test_numpy_piecewise():
    if not numpy:
        skip("numpy not installed.")
    pieces = Piecewise((x, x < 3), (x**2, x > 5), (0, True))
    f = lambdify(x, pieces, modules="numpy")
    numpy.testing.assert_array_equal(f(numpy.arange(10)),
                                     numpy.array([0, 1, 2, 0, 0, 0, 36, 49, 64, 81]))
    # If we evaluate somewhere all conditions are False, we should get back NaN
    nodef_func = lambdify(x, Piecewise((x, x > 0), (-x, x < 0)))
    numpy.testing.assert_array_equal(nodef_func(numpy.array([-1, 0, 1])),
                                     numpy.array([1, numpy.nan, 1]))


def test_numpy_logical_ops():
    if not numpy:
        skip("numpy not installed.")
    and_func = lambdify((x, y), And(x, y), modules="numpy")
    and_func_3 = lambdify((x, y, z), And(x, y, z), modules="numpy")
    or_func = lambdify((x, y), Or(x, y), modules="numpy")
    or_func_3 = lambdify((x, y, z), Or(x, y, z), modules="numpy")
    not_func = lambdify((x), Not(x), modules="numpy")
    arr1 = numpy.array([True, True])
    arr2 = numpy.array([False, True])
    arr3 = numpy.array([True, False])
    numpy.testing.assert_array_equal(and_func(arr1, arr2), numpy.array([False, True]))
    numpy.testing.assert_array_equal(and_func_3(arr1, arr2, arr3), numpy.array([False, False]))
    numpy.testing.assert_array_equal(or_func(arr1, arr2), numpy.array([True, True]))
    numpy.testing.assert_array_equal(or_func_3(arr1, arr2, arr3), numpy.array([True, True]))
    numpy.testing.assert_array_equal(not_func(arr2), numpy.array([True, False]))


def test_numpy_matmul():
    if not numpy:
        skip("numpy not installed.")
    xmat = Matrix([[x, y], [z, 1+z]])
    ymat = Matrix([[x**2], [Abs(x)]])
    mat_func = lambdify((x, y, z), xmat*ymat, modules="numpy")
    numpy.testing.assert_array_equal(mat_func(0.5, 3, 4), numpy.array([[1.625], [3.5]]))
    numpy.testing.assert_array_equal(mat_func(-0.5, 3, 4), numpy.array([[1.375], [3.5]]))
    # Multiple matrices chained together in multiplication
    f = lambdify((x, y, z), xmat*xmat*xmat, modules="numpy")
    numpy.testing.assert_array_equal(f(0.5, 3, 4), numpy.array([[72.125, 119.25],
                                                                [159, 251]]))


def test_numpy_numexpr():
    if not numpy:
        skip("numpy not installed.")
    if not numexpr:
        skip("numexpr not installed.")
    a, b, c = numpy.random.randn(3, 128, 128)
    # ensure that numpy and numexpr return same value for complicated expression
    expr = sin(x) + cos(y) + tan(z)**2 + Abs(z-y)*acos(sin(y*z)) + \
           Abs(y-z)*acosh(2+exp(y-x))- sqrt(x**2+I*y**2)
    npfunc = lambdify((x, y, z), expr, modules='numpy')
    nefunc = lambdify((x, y, z), expr, modules='numexpr')
    assert numpy.allclose(npfunc(a, b, c), nefunc(a, b, c))


def test_numexpr_userfunctions():
    if not numpy:
        skip("numpy not installed.")
    if not numexpr:
        skip("numexpr not installed.")
    a, b = numpy.random.randn(2, 10)
    uf = type('uf', (Function, ),
              {'eval' : classmethod(lambda x, y : y**2+1)})
    func = lambdify(x, 1-uf(x), modules='numexpr')
    assert numpy.allclose(func(a), -(a**2))

    uf = implemented_function(Function('uf'), lambda x, y : 2*x*y+1)
    func = lambdify((x, y), uf(x, y), modules='numexpr')
    assert numpy.allclose(func(a, b), 2*a*b+1)


def test_tensorflow_basic_math():
    if not tensorflow:
        skip("tensorflow not installed.")
    expr = Max(sin(x), Abs(1/(x+2)))
    func = lambdify(x, expr, modules="tensorflow")
    a = tensorflow.constant(0, dtype=tensorflow.float32)
    s = tensorflow.Session()
    assert func(a).eval(session=s) == 0.5


def test_tensorflow_placeholders():
    if not tensorflow:
        skip("tensorflow not installed.")
    expr = Max(sin(x), Abs(1/(x+2)))
    func = lambdify(x, expr, modules="tensorflow")
    a = tensorflow.placeholder(dtype=tensorflow.float32)
    s = tensorflow.Session()
    assert func(a).eval(session=s, feed_dict={a: 0}) == 0.5


def test_tensorflow_variables():
    if not tensorflow:
        skip("tensorflow not installed.")
    expr = Max(sin(x), Abs(1/(x+2)))
    func = lambdify(x, expr, modules="tensorflow")
    a = tensorflow.Variable(0, dtype=tensorflow.float32)
    s = tensorflow.Session()
    if V(tensorflow.__version__) < '1.0':
        s.run(tensorflow.initialize_all_variables())
    else:
        s.run(tensorflow.global_variables_initializer())
    assert func(a).eval(session=s) == 0.5


def test_tensorflow_logical_operations():
    if not tensorflow:
        skip("tensorflow not installed.")
    expr = Not(And(Or(x, y), y))
    func = lambdify([x, y], expr, modules="tensorflow")
    a = tensorflow.constant(False)
    b = tensorflow.constant(True)
    s = tensorflow.Session()
    assert func(a, b).eval(session=s) == 0


def test_tensorflow_piecewise():
    if not tensorflow:
        skip("tensorflow not installed.")
    expr = Piecewise((0, Eq(x,0)), (-1, x < 0), (1, x > 0))
    func = lambdify(x, expr, modules="tensorflow")
    a = tensorflow.placeholder(dtype=tensorflow.float32)
    s = tensorflow.Session()
    assert func(a).eval(session=s, feed_dict={a: -1}) == -1
    assert func(a).eval(session=s, feed_dict={a: 0}) == 0
    assert func(a).eval(session=s, feed_dict={a: 1}) == 1


def test_tensorflow_multi_max():
    if not tensorflow:
        skip("tensorflow not installed.")
    expr = Max(x, -x, x**2)
    func = lambdify(x, expr, modules="tensorflow")
    a = tensorflow.placeholder(dtype=tensorflow.float32)
    s = tensorflow.Session()
    assert func(a).eval(session=s, feed_dict={a: -2}) == 4


def test_tensorflow_multi_min():
    if not tensorflow:
        skip("tensorflow not installed.")
    expr = Min(x, -x, x**2)
    func = lambdify(x, expr, modules="tensorflow")
    a = tensorflow.placeholder(dtype=tensorflow.float32)
    s = tensorflow.Session()
    assert func(a).eval(session=s, feed_dict={a: -2}) == -2


def test_tensorflow_relational():
    if not tensorflow:
        skip("tensorflow not installed.")
    expr = x >= 0
    func = lambdify(x, expr, modules="tensorflow")
    a = tensorflow.placeholder(dtype=tensorflow.float32)
    s = tensorflow.Session()
    assert func(a).eval(session=s, feed_dict={a: 1})


def test_integral():
    f = Lambda(x, exp(-x**2))
    l = lambdify(x, Integral(f(x), (x, -oo, oo)), modules="sympy")
    assert l(x) == Integral(exp(-x**2), (x, -oo, oo))

#================== Test symbolic ==================================


def test_sym_single_arg():
    f = lambdify(x, x * y)
    assert f(z) == z * y


def test_sym_list_args():
    f = lambdify([x, y], x + y + z)
    assert f(1, 2) == 3 + z


def test_sym_integral():
    f = Lambda(x, exp(-x**2))
    l = lambdify(x, Integral(f(x), (x, -oo, oo)), modules="sympy")
    assert l(y).doit() == sqrt(pi)


def test_namespace_order():
    # lambdify had a bug, such that module dictionaries or cached module
    # dictionaries would pull earlier namespaces into themselves.
    # Because the module dictionaries form the namespace of the
    # generated lambda, this meant that the behavior of a previously
    # generated lambda function could change as a result of later calls
    # to lambdify.
    n1 = {'f': lambda x: 'first f'}
    n2 = {'f': lambda x: 'second f',
          'g': lambda x: 'function g'}
    f = sympy.Function('f')
    g = sympy.Function('g')
    if1 = lambdify(x, f(x), modules=(n1, "sympy"))
    assert if1(1) == 'first f'
    if2 = lambdify(x, g(x), modules=(n2, "sympy"))
    # previously gave 'second f'
    assert if1(1) == 'first f'


def test_namespace_type():
    # lambdify had a bug where it would reject modules of type unicode
    # on Python 2.
    x = sympy.Symbol('x')
    lambdify(x, x, modules=u'math')


def test_imps():
    # Here we check if the default returned functions are anonymous - in
    # the sense that we can have more than one function with the same name
    f = implemented_function('f', lambda x: 2*x)
    g = implemented_function('f', lambda x: math.sqrt(x))
    l1 = lambdify(x, f(x))
    l2 = lambdify(x, g(x))
    assert str(f(x)) == str(g(x))
    assert l1(3) == 6
    assert l2(3) == math.sqrt(3)
    # check that we can pass in a Function as input
    func = sympy.Function('myfunc')
    assert not hasattr(func, '_imp_')
    my_f = implemented_function(func, lambda x: 2*x)
    assert hasattr(my_f, '_imp_')
    # Error for functions with same name and different implementation
    f2 = implemented_function("f", lambda x: x + 101)
    raises(ValueError, lambda: lambdify(x, f(f2(x))))


def test_imps_errors():
    # Test errors that implemented functions can return, and still be able to
    # form expressions.
    # See: https://github.com/sympy/sympy/issues/10810
    #
    # XXX: Removed AttributeError here. This test was added due to issue 10810
    # but that issue was about ValueError. It doesn't seem reasonable to
    # "support" catching AttributeError in the same context...
    for val, error_class in product((0, 0., 2, 2.0), (TypeError, ValueError)):

        def myfunc(a):
            if a == 0:
                raise error_class
            return 1

        f = implemented_function('f', myfunc)
        expr = f(val)
        assert expr == f(val)


def test_imps_wrong_args():
    raises(ValueError, lambda: implemented_function(sin, lambda x: x))


def test_lambdify_imps():
    # Test lambdify with implemented functions
    # first test basic (sympy) lambdify
    f = sympy.cos
    assert lambdify(x, f(x))(0) == 1
    assert lambdify(x, 1 + f(x))(0) == 2
    assert lambdify((x, y), y + f(x))(0, 1) == 2
    # make an implemented function and test
    f = implemented_function("f", lambda x: x + 100)
    assert lambdify(x, f(x))(0) == 100
    assert lambdify(x, 1 + f(x))(0) == 101
    assert lambdify((x, y), y + f(x))(0, 1) == 101
    # Can also handle tuples, lists, dicts as expressions
    lam = lambdify(x, (f(x), x))
    assert lam(3) == (103, 3)
    lam = lambdify(x, [f(x), x])
    assert lam(3) == [103, 3]
    lam = lambdify(x, [f(x), (f(x), x)])
    assert lam(3) == [103, (103, 3)]
    lam = lambdify(x, {f(x): x})
    assert lam(3) == {103: 3}
    lam = lambdify(x, {f(x): x})
    assert lam(3) == {103: 3}
    lam = lambdify(x, {x: f(x)})
    assert lam(3) == {3: 103}
    # Check that imp preferred to other namespaces by default
    d = {'f': lambda x: x + 99}
    lam = lambdify(x, f(x), d)
    assert lam(3) == 103
    # Unless flag passed
    lam = lambdify(x, f(x), d, use_imps=False)
    assert lam(3) == 102


def test_dummification():
    t = symbols('t')
    F = Function('F')
    G = Function('G')
    #"\alpha" is not a valid python variable name
    #lambdify should sub in a dummy for it, and return
    #without a syntax error
    alpha = symbols(r'\alpha')
    some_expr = 2 * F(t)**2 / G(t)
    lam = lambdify((F(t), G(t)), some_expr)
    assert lam(3, 9) == 2
    lam = lambdify(sin(t), 2 * sin(t)**2)
    assert lam(F(t)) == 2 * F(t)**2
    #Test that \alpha was properly dummified
    lam = lambdify((alpha, t), 2*alpha + t)
    assert lam(2, 1) == 5
    raises(SyntaxError, lambda: lambdify(F(t) * G(t), F(t) * G(t) + 5))
    raises(SyntaxError, lambda: lambdify(2 * F(t), 2 * F(t) + 5))
    raises(SyntaxError, lambda: lambdify(2 * F(t), 4 * F(t) + 5))


def test_curly_matrix_symbol():
    # Issue #15009
    curlyv = sympy.MatrixSymbol("{v}", 2, 1)
    lam = lambdify(curlyv, curlyv)
    assert lam(1)==1
    lam = lambdify(curlyv, curlyv, dummify=True)
    assert lam(1)==1


def test_python_keywords():
    # Test for issue 7452. The automatic dummification should ensure use of
    # Python reserved keywords as symbol names will create valid lambda
    # functions. This is an additional regression test.
    python_if = symbols('if')
    expr = python_if / 2
    f = lambdify(python_if, expr)
    assert f(4.0) == 2.0


def test_lambdify_docstring():
    func = lambdify((w, x, y, z), w + x + y + z)
    ref = (
        "Created with lambdify. Signature:\n\n"
        "func(w, x, y, z)\n\n"
        "Expression:\n\n"
        "w + x + y + z"
    ).splitlines()
    assert func.__doc__.splitlines()[:len(ref)] == ref
    syms = symbols('a1:26')
    func = lambdify(syms, sum(syms))
    ref = (
        "Created with lambdify. Signature:\n\n"
        "func(a1, a2, a3, a4, a5, a6, a7, a8, a9, a10, a11, a12, a13, a14, a15,\n"
        "        a16, a17, a18, a19, a20, a21, a22, a23, a24, a25)\n\n"
        "Expression:\n\n"
        "a1 + a10 + a11 + a12 + a13 + a14 + a15 + a16 + a17 + a18 + a19 + a2 + a20 +..."
    ).splitlines()
    assert func.__doc__.splitlines()[:len(ref)] == ref


#================== Test special printers ==========================


def test_special_printers():
    class IntervalPrinter(LambdaPrinter):
        """Use ``lambda`` printer but print numbers as ``mpi`` intervals. """

        def _print_Integer(self, expr):
            return "mpi('%s')" % super(IntervalPrinter, self)._print_Integer(expr)

        def _print_Rational(self, expr):
            return "mpi('%s')" % super(IntervalPrinter, self)._print_Rational(expr)

    def intervalrepr(expr):
        return IntervalPrinter().doprint(expr)

    expr = sqrt(sqrt(2) + sqrt(3)) + S(1)/2

    func0 = lambdify((), expr, modules="mpmath", printer=intervalrepr)
    func1 = lambdify((), expr, modules="mpmath", printer=IntervalPrinter)
    func2 = lambdify((), expr, modules="mpmath", printer=IntervalPrinter())

    mpi = type(mpmath.mpi(1, 2))

    assert isinstance(func0(), mpi)
    assert isinstance(func1(), mpi)
    assert isinstance(func2(), mpi)


def test_true_false():
    # We want exact is comparison here, not just ==
    assert lambdify([], true)() is True
    assert lambdify([], false)() is False


def test_issue_2790():
    assert lambdify((x, (y, z)), x + y)(1, (2, 4)) == 3
    assert lambdify((x, (y, (w, z))), w + x + y + z)(1, (2, (3, 4))) == 10
    assert lambdify(x, x + 1, dummify=False)(1) == 2


def test_issue_12092():
    f = implemented_function('f', lambda x: x**2)
    assert f(f(2)).evalf() == Float(16)


def test_issue_14911():
    class Variable(sympy.Symbol):
        def _sympystr(self, printer):
            return printer.doprint(self.name)

        _lambdacode = _sympystr
        _numpycode = _sympystr

    x = Variable('x')
    y = 2 * x
    code = LambdaPrinter().doprint(y)
    assert code.replace(' ', '') == '2*x'


def test_ITE():
    assert lambdify((x, y, z), ITE(x, y, z))(True, 5, 3) == 5
    assert lambdify((x, y, z), ITE(x, y, z))(False, 5, 3) == 3


def test_Min_Max():
    # see gh-10375
    assert lambdify((x, y, z), Min(x, y, z))(1, 2, 3) == 1
    assert lambdify((x, y, z), Max(x, y, z))(1, 2, 3) == 3


def test_Indexed():
    # Issue #10934
    if not numpy:
        skip("numpy not installed")

    a = IndexedBase('a')
    i, j = symbols('i j')
    b = numpy.array([[1, 2], [3, 4]])
    assert lambdify(a, Sum(a[x, y], (x, 0, 1), (y, 0, 1)))(b) == 10


def test_issue_12173():
    #test for issue 12173
    exp1 = lambdify((x, y), uppergamma(x, y),"mpmath")(1, 2)
    exp2 = lambdify((x, y), lowergamma(x, y),"mpmath")(1, 2)
    assert exp1 == uppergamma(1, 2).evalf()
    assert exp2 == lowergamma(1, 2).evalf()


def test_issue_13642():
    if not numpy:
        skip("numpy not installed")
    f = lambdify(x, sinc(x))
    assert Abs(f(1) - sinc(1)).n() < 1e-15


def test_sinc_mpmath():
    f = lambdify(x, sinc(x), "mpmath")
    assert Abs(f(1) - sinc(1)).n() < 1e-15


def test_lambdify_dummy_arg():
    d1 = Dummy()
    f1 = lambdify(d1, d1 + 1, dummify=False)
    assert f1(2) == 3
    f1b = lambdify(d1, d1 + 1)
    assert f1b(2) == 3
    d2 = Dummy('x')
    f2 = lambdify(d2, d2 + 1)
    assert f2(2) == 3
    f3 = lambdify([[d2]], d2 + 1)
    assert f3([2]) == 3


def test_lambdify_mixed_symbol_dummy_args():
    d = Dummy()
    # Contrived example of name clash
    dsym = symbols(str(d))
    f = lambdify([d, dsym], d - dsym)
    assert f(4, 1) == 3


def test_numpy_array_arg():
    # Test for issue 14655 (numpy part)
    if not numpy:
        skip("numpy not installed")

    f = lambdify([[x, y]], x*x + y, 'numpy')

    assert f(numpy.array([2.0, 1.0])) == 5


def test_tensorflow_array_arg():
    # Test for issue 14655 (tensorflow part)
    if not tensorflow:
        skip("tensorflow not installed.")

    f = lambdify([[x, y]], x*x + y, 'tensorflow')

    fcall = f(tensorflow.constant([2.0, 1.0]))

    s = tensorflow.Session()
    assert s.run(fcall) == 5


def test_scipy_fns():
    if not scipy:
        skip("scipy not installed")

    single_arg_sympy_fns = [erf, erfc, factorial, gamma, loggamma, digamma]
    single_arg_scipy_fns = [scipy.special.erf, scipy.special.erfc,
        scipy.special.factorial, scipy.special.gamma, scipy.special.gammaln,
        scipy.special.psi]
    numpy.random.seed(0)
    for (sympy_fn, scipy_fn) in zip(single_arg_sympy_fns, single_arg_scipy_fns):
        f = lambdify(x, sympy_fn(x), modules="scipy")
        for i in range(20):
            tv = numpy.random.uniform(-10, 10) + 1j*numpy.random.uniform(-5, 5)
            # SciPy thinks that factorial(z) is 0 when re(z) < 0.
            # SymPy does not think so.
            if sympy_fn == factorial and numpy.real(tv) < 0:
                tv = tv + 2*numpy.abs(numpy.real(tv))
            # SciPy supports gammaln for real arguments only,
            # and there is also a branch cut along the negative real axis
            if sympy_fn == loggamma:
                tv = numpy.abs(tv)
            # SymPy's digamma evaluates as polygamma(0, z)
            # which SciPy supports for real arguments only
            if sympy_fn == digamma:
                tv = numpy.real(tv)
            sympy_result = sympy_fn(tv).evalf()
            assert abs(f(tv) - sympy_result) < 1e-13*(1 + abs(sympy_result))
            assert abs(f(tv) - scipy_fn(tv)) < 1e-13*(1 + abs(sympy_result))

    double_arg_sympy_fns = [RisingFactorial, besselj, bessely, besseli,
        besselk]
    double_arg_scipy_fns = [scipy.special.poch, scipy.special.jv,
        scipy.special.yv, scipy.special.iv, scipy.special.kv]
    for (sympy_fn, scipy_fn) in zip(double_arg_sympy_fns, double_arg_scipy_fns):
        f = lambdify((x, y), sympy_fn(x, y), modules="scipy")
        for i in range(20):
            # SciPy supports only real orders of Bessel functions
            tv1 = numpy.random.uniform(-10, 10)
            tv2 = numpy.random.uniform(-10, 10) + 1j*numpy.random.uniform(-5, 5)
            # SciPy supports poch for real arguments only
            if sympy_fn == RisingFactorial:
                tv2 = numpy.real(tv2)
            sympy_result = sympy_fn(tv1, tv2).evalf()
            assert abs(f(tv1, tv2) - sympy_result) < 1e-13*(1 + abs(sympy_result))
            assert abs(f(tv1, tv2) - scipy_fn(tv1, tv2)) < 1e-13*(1 + abs(sympy_result))


def test_scipy_polys():
    if not scipy:
        skip("scipy not installed")
    numpy.random.seed(0)

    params = symbols('n k a b')
    # list polynomials with the number of parameters
    polys = [
        (chebyshevt, 1),
        (chebyshevu, 1),
        (legendre, 1),
        (hermite, 1),
        (laguerre, 1),
        (gegenbauer, 2),
        (assoc_legendre, 2),
        (assoc_laguerre, 2),
        (jacobi, 3)
    ]

    for sympy_fn, num_params in polys:
        args = params[:num_params] + (x,)
        f = lambdify(args, sympy_fn(*args))
        for i in range(10):
            tn = numpy.random.randint(3, 10)
            tparams = tuple(numpy.random.uniform(0, 5, size=num_params-1))
            tv = numpy.random.uniform(-10, 10) + 1j*numpy.random.uniform(-5, 5)
            # SciPy supports hermite for real arguments only
            if sympy_fn == hermite:
                tv = numpy.real(tv)
            # assoc_legendre needs x in (-1, 1) and integer param at most n
            if sympy_fn == assoc_legendre:
                tv = numpy.random.uniform(-1, 1)
                tparams = tuple(numpy.random.randint(1, tn, size=1))
            vals = (tn,) + tparams + (tv,)
            sympy_result = sympy_fn(*vals).evalf()
            assert abs(f(*vals) - sympy_result) < 1e-13*(1 + abs(sympy_result))


def test_lambdify_inspect():
    f = lambdify(x, x**2)
    # Test that inspect.getsource works but don't hard-code implementation
    # details
    assert 'x**2' in inspect.getsource(f)


def test_issue_14941():
    x, y = Dummy(), Dummy()

    # test dict
    f1 = lambdify([x, y], {x: 3, y: 3}, 'sympy')
    assert f1(2, 3) == {2: 3, 3: 3}

    # test tuple
    f2 = lambdify([x, y], (y, x), 'sympy')
    assert f2(2, 3) == (3, 2)

    # test list
    f3 = lambdify([x, y], [y, x], 'sympy')
    assert f3(2, 3) == [3, 2]


def test_lambdify_Derivative_arg_issue_16468():
    f = Function('f')(x)
    fx = f.diff()
    assert lambdify((f, fx), f + fx)(10, 5) == 15
    assert eval(lambdastr((f, fx), f/fx))(10, 5) == 2
    raises(SyntaxError, lambda:
        eval(lambdastr((f, fx), f/fx, dummify=False)))
    assert eval(lambdastr((f, fx), f/fx, dummify=True))(10, 5) == 2
    assert eval(lambdastr((fx, f), f/fx, dummify=True))(S(10), 5) == S.Half
    assert lambdify(fx, 1 + fx)(41) == 42
    assert eval(lambdastr(fx, 1 + fx, dummify=True))(41) == 42


def test_imag_real():
    f_re = lambdify([z], sympy.re(z))
    val = 3+2j
    assert f_re(val) == val.real

    f_im = lambdify([z], sympy.im(z))  # see #15400
    assert f_im(val) == val.imag


def test_MatrixSymbol_issue_15578():
    if not numpy:
        skip("numpy not installed")
    A = MatrixSymbol('A', 2, 2)
    A0 = numpy.array([[1, 2], [3, 4]])
    f = lambdify(A, A**(-1))
    assert numpy.allclose(f(A0), numpy.array([[-2., 1.], [1.5, -0.5]]))
    g = lambdify(A, A**3)
    assert numpy.allclose(g(A0), numpy.array([[37, 54], [81, 118]]))


def test_issue_15654():
    if not scipy:
        skip("scipy not installed")
    from sympy.abc import n, l, r, Z
    from sympy.physics import hydrogen
    nv, lv, rv, Zv = 1, 0, 3, 1
    sympy_value = hydrogen.R_nl(nv, lv, rv, Zv).evalf()
    f = lambdify((n, l, r, Z), hydrogen.R_nl(n, l, r, Z))
    scipy_value = f(nv, lv, rv, Zv)
    assert abs(sympy_value - scipy_value) < 1e-15

def test_issue_15827():
    if not numpy:
        skip("numpy not installed")
    A = MatrixSymbol("A", 3, 3)
    B = MatrixSymbol("B", 2, 3)
    C = MatrixSymbol("C", 3, 4)
    D = MatrixSymbol("D", 4, 5)
    k=symbols("k")
    f = lambdify(A, (2*k)*A)
    g = lambdify(A, (2+k)*A)
    h = lambdify(A, 2*A)
    i = lambdify((B, C, D), 2*B*C*D)
    assert numpy.array_equal(f(numpy.array([[1, 2, 3], [1, 2, 3], [1, 2, 3]])), \
    numpy.array([[2*k, 4*k, 6*k], [2*k, 4*k, 6*k], [2*k, 4*k, 6*k]], dtype=object))

    assert numpy.array_equal(g(numpy.array([[1, 2, 3], [1, 2, 3], [1, 2, 3]])), \
    numpy.array([[k + 2, 2*k + 4, 3*k + 6], [k + 2, 2*k + 4, 3*k + 6], \
    [k + 2, 2*k + 4, 3*k + 6]], dtype=object))

    assert numpy.array_equal(h(numpy.array([[1, 2, 3], [1, 2, 3], [1, 2, 3]])), \
    numpy.array([[2, 4, 6], [2, 4, 6], [2, 4, 6]]))

    assert numpy.array_equal(i(numpy.array([[1, 2, 3], [1, 2, 3]]), numpy.array([[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]), \
    numpy.array([[1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [1, 2, 3, 4, 5], [1, 2, 3, 4, 5]])), numpy.array([[ 120, 240, 360, 480, 600], \
    [ 120, 240, 360, 480, 600]]))
