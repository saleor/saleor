from sympy import (pi, sin, cos, Symbol, Integral, Sum, sqrt, log,
                   oo, LambertW, I, meijerg, exp_polar, Max, Piecewise, And)
from sympy.plotting import (plot, plot_parametric, plot3d_parametric_line,
                            plot3d, plot3d_parametric_surface)
from sympy.plotting.plot import unset_show, plot_contour
from sympy.utilities import lambdify as lambdify_
from sympy.utilities.pytest import skip, raises, warns
from sympy.plotting.experimental_lambdify import lambdify
from sympy.external import import_module

from tempfile import NamedTemporaryFile
import os

unset_show()


# XXX: We could implement this as a context manager instead
# That would need rewriting the plot_and_save() function
# entirely
class TmpFileManager:

    tmp_files = []

    @classmethod
    def tmp_file(cls, name=''):
        cls.tmp_files.append(NamedTemporaryFile(prefix=name, suffix='.png').name)
        return cls.tmp_files[-1]

    @classmethod
    def cleanup(cls):
        for file in cls.tmp_files:
            try:
                os.remove(file)
            except OSError:
                # If the file doesn't exist, for instance, if the test failed.
                pass

def plot_and_save_1(name):
    tmp_file = TmpFileManager.tmp_file

    x = Symbol('x')
    y = Symbol('y')
    z = Symbol('z')

    ###
    # Examples from the 'introduction' notebook
    ###

    p = plot(x)
    p = plot(x*sin(x), x*cos(x))
    p.extend(p)
    p[0].line_color = lambda a: a
    p[1].line_color = 'b'
    p.title = 'Big title'
    p.xlabel = 'the x axis'
    p[1].label = 'straight line'
    p.legend = True
    p.aspect_ratio = (1, 1)
    p.xlim = (-15, 20)
    p.save(tmp_file('%s_basic_options_and_colors' % name))
    p._backend.close()

    p.extend(plot(x + 1))
    p.append(plot(x + 3, x**2)[1])
    p.save(tmp_file('%s_plot_extend_append' % name))

    p[2] = plot(x**2, (x, -2, 3))
    p.save(tmp_file('%s_plot_setitem' % name))
    p._backend.close()

    p = plot(sin(x), (x, -2*pi, 4*pi))
    p.save(tmp_file('%s_line_explicit' % name))
    p._backend.close()

    p = plot(sin(x))
    p.save(tmp_file('%s_line_default_range' % name))
    p._backend.close()

    p = plot((x**2, (x, -5, 5)), (x**3, (x, -3, 3)))
    p.save(tmp_file('%s_line_multiple_range' % name))
    p._backend.close()

    raises(ValueError, lambda: plot(x, y))

    #Piecewise plots
    p = plot(Piecewise((1, x > 0), (0, True)), (x, -1, 1))
    p.save(tmp_file('%s_plot_piecewise' % name))
    p._backend.close()

    p = plot(Piecewise((x, x < 1), (x**2, True)), (x, -3, 3))
    p.save(tmp_file('%s_plot_piecewise_2' % name))
    p._backend.close()

    # test issue 7471
    p1 = plot(x)
    p2 = plot(3)
    p1.extend(p2)
    p.save(tmp_file('%s_horizontal_line' % name))
    p._backend.close()

    # test issue 10925
    f = Piecewise((-1, x < -1), (x, And(-1 <= x, x < 0)), \
        (x**2, And(0 <= x, x < 1)), (x**3, x >= 1))
    p = plot(f, (x, -3, 3))
    p.save(tmp_file('%s_plot_piecewise_3' % name))
    p._backend.close()

def plot_and_save_2(name):
    tmp_file = TmpFileManager.tmp_file

    x = Symbol('x')
    y = Symbol('y')
    z = Symbol('z')

    #parametric 2d plots.
    #Single plot with default range.
    plot_parametric(sin(x), cos(x)).save(tmp_file())

    #Single plot with range.
    p = plot_parametric(sin(x), cos(x), (x, -5, 5))
    p.save(tmp_file('%s_parametric_range' % name))
    p._backend.close()

    #Multiple plots with same range.
    p = plot_parametric((sin(x), cos(x)), (x, sin(x)))
    p.save(tmp_file('%s_parametric_multiple' % name))
    p._backend.close()

    #Multiple plots with different ranges.
    p = plot_parametric((sin(x), cos(x), (x, -3, 3)), (x, sin(x), (x, -5, 5)))
    p.save(tmp_file('%s_parametric_multiple_ranges' % name))
    p._backend.close()

    #depth of recursion specified.
    p = plot_parametric(x, sin(x), depth=13)
    p.save(tmp_file('%s_recursion_depth' % name))
    p._backend.close()

    #No adaptive sampling.
    p = plot_parametric(cos(x), sin(x), adaptive=False, nb_of_points=500)
    p.save(tmp_file('%s_adaptive' % name))
    p._backend.close()

    #3d parametric plots
    p = plot3d_parametric_line(sin(x), cos(x), x)
    p.save(tmp_file('%s_3d_line' % name))
    p._backend.close()

    p = plot3d_parametric_line(
        (sin(x), cos(x), x, (x, -5, 5)), (cos(x), sin(x), x, (x, -3, 3)))
    p.save(tmp_file('%s_3d_line_multiple' % name))
    p._backend.close()

    p = plot3d_parametric_line(sin(x), cos(x), x, nb_of_points=30)
    p.save(tmp_file('%s_3d_line_points' % name))
    p._backend.close()

    # 3d surface single plot.
    p = plot3d(x * y)
    p.save(tmp_file('%s_surface' % name))
    p._backend.close()

    # Multiple 3D plots with same range.
    p = plot3d(-x * y, x * y, (x, -5, 5))
    p.save(tmp_file('%s_surface_multiple' % name))
    p._backend.close()

    # Multiple 3D plots with different ranges.
    p = plot3d(
        (x * y, (x, -3, 3), (y, -3, 3)), (-x * y, (x, -3, 3), (y, -3, 3)))
    p.save(tmp_file('%s_surface_multiple_ranges' % name))
    p._backend.close()

    # Single Parametric 3D plot
    p = plot3d_parametric_surface(sin(x + y), cos(x - y), x - y)
    p.save(tmp_file('%s_parametric_surface' % name))
    p._backend.close()

    # Multiple Parametric 3D plots.
    p = plot3d_parametric_surface(
        (x*sin(z), x*cos(z), z, (x, -5, 5), (z, -5, 5)),
        (sin(x + y), cos(x - y), x - y, (x, -5, 5), (y, -5, 5)))
    p.save(tmp_file('%s_parametric_surface' % name))
    p._backend.close()

    # Single Contour plot.
    p = plot_contour(sin(x)*sin(y), (x, -5, 5), (y, -5, 5))
    p.save(tmp_file('%s_contour_plot' % name))
    p._backend.close()

    # Multiple Contour plots with same range.
    p = plot_contour(x**2 + y**2, x**3 + y**3, (x, -5, 5), (y, -5, 5))
    p.save(tmp_file('%s_contour_plot' % name))
    p._backend.close()

    # Multiple Contour plots with different range.
    p = plot_contour((x**2 + y**2, (x, -5, 5), (y, -5, 5)), (x**3 + y**3, (x, -3, 3), (y, -3, 3)))
    p.save(tmp_file('%s_contour_plot' % name))
    p._backend.close()

def plot_and_save_3(name):
    tmp_file = TmpFileManager.tmp_file

    x = Symbol('x')
    y = Symbol('y')
    z = Symbol('z')

    ###
    # Examples from the 'colors' notebook
    ###

    p = plot(sin(x))
    p[0].line_color = lambda a: a
    p.save(tmp_file('%s_colors_line_arity1' % name))

    p[0].line_color = lambda a, b: b
    p.save(tmp_file('%s_colors_line_arity2' % name))
    p._backend.close()

    p = plot(x*sin(x), x*cos(x), (x, 0, 10))
    p[0].line_color = lambda a: a
    p.save(tmp_file('%s_colors_param_line_arity1' % name))

    p[0].line_color = lambda a, b: a
    p.save(tmp_file('%s_colors_param_line_arity2a' % name))

    p[0].line_color = lambda a, b: b
    p.save(tmp_file('%s_colors_param_line_arity2b' % name))
    p._backend.close()

    p = plot3d_parametric_line(sin(x) + 0.1*sin(x)*cos(7*x),
             cos(x) + 0.1*cos(x)*cos(7*x),
        0.1*sin(7*x),
        (x, 0, 2*pi))
    p[0].line_color = lambdify_(x, sin(4*x))
    p.save(tmp_file('%s_colors_3d_line_arity1' % name))
    p[0].line_color = lambda a, b: b
    p.save(tmp_file('%s_colors_3d_line_arity2' % name))
    p[0].line_color = lambda a, b, c: c
    p.save(tmp_file('%s_colors_3d_line_arity3' % name))
    p._backend.close()

    p = plot3d(sin(x)*y, (x, 0, 6*pi), (y, -5, 5))
    p[0].surface_color = lambda a: a
    p.save(tmp_file('%s_colors_surface_arity1' % name))
    p[0].surface_color = lambda a, b: b
    p.save(tmp_file('%s_colors_surface_arity2' % name))
    p[0].surface_color = lambda a, b, c: c
    p.save(tmp_file('%s_colors_surface_arity3a' % name))
    p[0].surface_color = lambdify_((x, y, z), sqrt((x - 3*pi)**2 + y**2))
    p.save(tmp_file('%s_colors_surface_arity3b' % name))
    p._backend.close()

    p = plot3d_parametric_surface(x * cos(4 * y), x * sin(4 * y), y,
             (x, -1, 1), (y, -1, 1))
    p[0].surface_color = lambda a: a
    p.save(tmp_file('%s_colors_param_surf_arity1' % name))
    p[0].surface_color = lambda a, b: a*b
    p.save(tmp_file('%s_colors_param_surf_arity2' % name))
    p[0].surface_color = lambdify_((x, y, z), sqrt(x**2 + y**2 + z**2))
    p.save(tmp_file('%s_colors_param_surf_arity3' % name))
    p._backend.close()

def plot_and_save_4(name):
    tmp_file = TmpFileManager.tmp_file

    x = Symbol('x')
    y = Symbol('y')
    z = Symbol('z')

    ###
    # Examples from the 'advanced' notebook
    ###

    # XXX: This raises the warning "The evaluation of the expression is
    # problematic. We are trying a failback method that may still work. Please
    # report this as a bug." It has to use the fallback because using evalf()
    # is the only way to evaluate the integral. We should perhaps just remove
    # that warning.

    with warns(UserWarning, match="The evaluation of the expression is problematic"):
        i = Integral(log((sin(x)**2 + 1)*sqrt(x**2 + 1)), (x, 0, y))
        p = plot(i, (y, 1, 5))
        p.save(tmp_file('%s_advanced_integral' % name))
        p._backend.close()

def plot_and_save_5(name):
    tmp_file = TmpFileManager.tmp_file

    x = Symbol('x')
    y = Symbol('y')
    z = Symbol('z')

    s = Sum(1/x**y, (x, 1, oo))
    p = plot(s, (y, 2, 10))
    p.save(tmp_file('%s_advanced_inf_sum' % name))
    p._backend.close()

    p = plot(Sum(1/x, (x, 1, y)), (y, 2, 10), show=False)
    p[0].only_integers = True
    p[0].steps = True
    p.save(tmp_file('%s_advanced_fin_sum' % name))
    p._backend.close()

def plot_and_save_6(name):
    tmp_file = TmpFileManager.tmp_file

    x = Symbol('x')
    y = Symbol('y')
    z = Symbol('z')

    ###
    # Test expressions that can not be translated to np and generate complex
    # results.
    ###
    plot(sin(x) + I*cos(x)).save(tmp_file())
    plot(sqrt(sqrt(-x))).save(tmp_file())
    plot(LambertW(x)).save(tmp_file())
    plot(sqrt(LambertW(x))).save(tmp_file())

    #Characteristic function of a StudentT distribution with nu=10
    plot((meijerg(((1 / 2,), ()), ((5, 0, 1 / 2), ()), 5 * x**2 * exp_polar(-I*pi)/2)
            + meijerg(((1/2,), ()), ((5, 0, 1/2), ()),
                5*x**2 * exp_polar(I*pi)/2)) / (48 * pi), (x, 1e-6, 1e-2)).save(tmp_file())

def test_matplotlib_1():

    matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
    if matplotlib:
        try:
            plot_and_save_1('test')
        finally:
            # clean up
            TmpFileManager.cleanup()
    else:
        skip("Matplotlib not the default backend")

def test_matplotlib_2():

    matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
    if matplotlib:
        try:
            plot_and_save_2('test')
        finally:
            # clean up
            TmpFileManager.cleanup()
    else:
        skip("Matplotlib not the default backend")

def test_matplotlib_3():

    matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
    if matplotlib:
        try:
            plot_and_save_3('test')
        finally:
            # clean up
            TmpFileManager.cleanup()
    else:
        skip("Matplotlib not the default backend")

def test_matplotlib_4():

    matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
    if matplotlib:
        try:
            plot_and_save_4('test')
        finally:
            # clean up
            TmpFileManager.cleanup()
    else:
        skip("Matplotlib not the default backend")

def test_matplotlib_5():

    matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
    if matplotlib:
        try:
            plot_and_save_5('test')
        finally:
            # clean up
            TmpFileManager.cleanup()
    else:
        skip("Matplotlib not the default backend")

def test_matplotlib_6():

    matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
    if matplotlib:
        try:
            plot_and_save_6('test')
        finally:
            # clean up
            TmpFileManager.cleanup()
    else:
        skip("Matplotlib not the default backend")

# Tests for exception handling in experimental_lambdify
def test_experimental_lambify():
    x = Symbol('x')
    f = lambdify([x], Max(x, 5))
    # XXX should f be tested? If f(2) is attempted, an
    # error is raised because a complex produced during wrapping of the arg
    # is being compared with an int.
    assert Max(2, 5) == 5
    assert Max(5, 7) == 7

    x = Symbol('x-3')
    f = lambdify([x], x + 1)
    assert f(1) == 2


def test_append_issue_7140():
    matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
    if not matplotlib:
        skip("Matplotlib not the default backend")

    x = Symbol('x')
    p1 = plot(x)
    p2 = plot(x**2)
    p3 = plot(x + 2)

    # append a series
    p2.append(p1[0])
    assert len(p2._series) == 2

    with raises(TypeError):
        p1.append(p2)

    with raises(TypeError):
        p1.append(p2._series)

def test_issue_15265():
    from sympy.core.sympify import sympify
    from sympy.core.singleton import S

    matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
    if not matplotlib:
        skip("Matplotlib not the default backend")

    x = Symbol('x')
    eqn = sin(x)

    p = plot(eqn, xlim=(-S.Pi, S.Pi), ylim=(-1, 1))
    p._backend.close()

    p = plot(eqn, xlim=(-1, 1), ylim=(-S.Pi, S.Pi))
    p._backend.close()

    p = plot(eqn, xlim=(-1, 1), ylim=(sympify('-3.14'), sympify('3.14')))
    p._backend.close()

    p = plot(eqn, xlim=(sympify('-3.14'), sympify('3.14')), ylim=(-1, 1))
    p._backend.close()

    raises(ValueError,
        lambda: plot(eqn, xlim=(-S.ImaginaryUnit, 1), ylim=(-1, 1)))

    raises(ValueError,
        lambda: plot(eqn, xlim=(-1, 1), ylim=(-1, S.ImaginaryUnit)))

    raises(ValueError,
        lambda: plot(eqn, xlim=(-S.Infinity, 1), ylim=(-1, 1)))

    raises(ValueError,
        lambda: plot(eqn, xlim=(-1, 1), ylim=(-1, S.Infinity)))
