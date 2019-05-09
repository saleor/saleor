import warnings
from sympy import (plot_implicit, cos, Symbol, symbols, Eq, sin, re, And, Or, exp, I,
                   tan, pi)
from sympy.plotting.plot import unset_show
from tempfile import NamedTemporaryFile, mkdtemp
from sympy.utilities.pytest import skip, warns
from sympy.external import import_module
from sympy.utilities.tmpfiles import TmpFileManager, cleanup_tmp_files

#Set plots not to show
unset_show()

def tmp_file(dir=None, name=''):
    return NamedTemporaryFile(
    suffix='.png', dir=dir, delete=False).name

def plot_and_save(expr, *args, **kwargs):
    name = kwargs.pop('name', '')
    dir = kwargs.pop('dir', None)
    p = plot_implicit(expr, *args, **kwargs)
    p.save(tmp_file(dir=dir, name=name))
    # Close the plot to avoid a warning from matplotlib
    p._backend.close()

def plot_implicit_tests(name):
    temp_dir = mkdtemp()
    TmpFileManager.tmp_folder(temp_dir)
    x = Symbol('x')
    y = Symbol('y')
    z = Symbol('z')
    #implicit plot tests
    plot_and_save(Eq(y, cos(x)), (x, -5, 5), (y, -2, 2), name=name, dir=temp_dir)
    plot_and_save(Eq(y**2, x**3 - x), (x, -5, 5),
            (y, -4, 4), name=name, dir=temp_dir)
    plot_and_save(y > 1 / x, (x, -5, 5),
            (y, -2, 2), name=name, dir=temp_dir)
    plot_and_save(y < 1 / tan(x), (x, -5, 5),
            (y, -2, 2), name=name, dir=temp_dir)
    plot_and_save(y >= 2 * sin(x) * cos(x), (x, -5, 5),
            (y, -2, 2), name=name, dir=temp_dir)
    plot_and_save(y <= x**2, (x, -3, 3),
            (y, -1, 5), name=name, dir=temp_dir)

    #Test all input args for plot_implicit
    plot_and_save(Eq(y**2, x**3 - x), dir=temp_dir)
    plot_and_save(Eq(y**2, x**3 - x), adaptive=False, dir=temp_dir)
    plot_and_save(Eq(y**2, x**3 - x), adaptive=False, points=500, dir=temp_dir)
    plot_and_save(y > x, (x, -5, 5), dir=temp_dir)
    plot_and_save(And(y > exp(x), y > x + 2), dir=temp_dir)
    plot_and_save(Or(y > x, y > -x), dir=temp_dir)
    plot_and_save(x**2 - 1, (x, -5, 5), dir=temp_dir)
    plot_and_save(x**2 - 1, dir=temp_dir)
    plot_and_save(y > x, depth=-5, dir=temp_dir)
    plot_and_save(y > x, depth=5, dir=temp_dir)
    plot_and_save(y > cos(x), adaptive=False, dir=temp_dir)
    plot_and_save(y < cos(x), adaptive=False, dir=temp_dir)
    plot_and_save(And(y > cos(x), Or(y > x, Eq(y, x))), dir=temp_dir)
    plot_and_save(y - cos(pi / x), dir=temp_dir)

    #Test plots which cannot be rendered using the adaptive algorithm
    with warns(UserWarning, match="Adaptive meshing could not be applied"):
        plot_and_save(Eq(y, re(cos(x) + I*sin(x))), name=name, dir=temp_dir)

    plot_and_save(x**2 - 1, title='An implicit plot', dir=temp_dir)

def test_line_color():
    x, y = symbols('x, y')
    p = plot_implicit(x**2 + y**2 - 1, line_color="green", show=False)
    assert p._series[0].line_color == "green"
    p = plot_implicit(x**2 + y**2 - 1, line_color='r', show=False)
    assert p._series[0].line_color == "r"

def test_matplotlib():
    matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
    if matplotlib:
        try:
            plot_implicit_tests('test')
            test_line_color()
        finally:
            TmpFileManager.cleanup()
    else:
        skip("Matplotlib not the default backend")
