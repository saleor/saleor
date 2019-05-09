"""Plotting module for Sympy.

A plot is represented by the ``Plot`` class that contains a reference to the
backend and a list of the data series to be plotted. The data series are
instances of classes meant to simplify getting points and meshes from sympy
expressions. ``plot_backends`` is a dictionary with all the backends.

This module gives only the essential. For all the fancy stuff use directly
the backend. You can get the backend wrapper for every plot from the
``_backend`` attribute. Moreover the data series classes have various useful
methods like ``get_points``, ``get_segments``, ``get_meshes``, etc, that may
be useful if you wish to use another plotting library.

Especially if you need publication ready graphs and this module is not enough
for you - just get the ``_backend`` attribute and add whatever you want
directly to it. In the case of matplotlib (the common way to graph data in
python) just copy ``_backend.fig`` which is the figure and ``_backend.ax``
which is the axis and work on them as you would on any other matplotlib object.

Simplicity of code takes much greater importance than performance. Don't use it
if you care at all about performance. A new backend instance is initialized
every time you call ``show()`` and the old one is left to the garbage collector.
"""

from __future__ import print_function, division

import warnings

from sympy import sympify, Expr, Tuple, Dummy, Symbol
from sympy.external import import_module
from sympy.core.function import arity
from sympy.core.compatibility import range, Callable
from sympy.utilities.iterables import is_sequence
from .experimental_lambdify import (vectorized_lambdify, lambdify)

# N.B.
# When changing the minimum module version for matplotlib, please change
# the same in the `SymPyDocTestFinder`` in `sympy/utilities/runtests.py`

# Backend specific imports - textplot
from sympy.plotting.textplot import textplot

# Global variable
# Set to False when running tests / doctests so that the plots don't show.
_show = True


def unset_show():
    """
    Disable show(). For use in the tests.
    """
    global _show
    _show = False

##############################################################################
# The public interface
##############################################################################


class Plot(object):
    """The central class of the plotting module.

    For interactive work the function ``plot`` is better suited.

    This class permits the plotting of sympy expressions using numerous
    backends (matplotlib, textplot, the old pyglet module for sympy, Google
    charts api, etc).

    The figure can contain an arbitrary number of plots of sympy expressions,
    lists of coordinates of points, etc. Plot has a private attribute _series that
    contains all data series to be plotted (expressions for lines or surfaces,
    lists of points, etc (all subclasses of BaseSeries)). Those data series are
    instances of classes not imported by ``from sympy import *``.

    The customization of the figure is on two levels. Global options that
    concern the figure as a whole (eg title, xlabel, scale, etc) and
    per-data series options (eg name) and aesthetics (eg. color, point shape,
    line type, etc.).

    The difference between options and aesthetics is that an aesthetic can be
    a function of the coordinates (or parameters in a parametric plot). The
    supported values for an aesthetic are:
    - None (the backend uses default values)
    - a constant
    - a function of one variable (the first coordinate or parameter)
    - a function of two variables (the first and second coordinate or
    parameters)
    - a function of three variables (only in nonparametric 3D plots)
    Their implementation depends on the backend so they may not work in some
    backends.

    If the plot is parametric and the arity of the aesthetic function permits
    it the aesthetic is calculated over parameters and not over coordinates.
    If the arity does not permit calculation over parameters the calculation is
    done over coordinates.

    Only cartesian coordinates are supported for the moment, but you can use
    the parametric plots to plot in polar, spherical and cylindrical
    coordinates.

    The arguments for the constructor Plot must be subclasses of BaseSeries.

    Any global option can be specified as a keyword argument.

    The global options for a figure are:

    - title : str
    - xlabel : str
    - ylabel : str
    - legend : bool
    - xscale : {'linear', 'log'}
    - yscale : {'linear', 'log'}
    - axis : bool
    - axis_center : tuple of two floats or {'center', 'auto'}
    - xlim : tuple of two floats
    - ylim : tuple of two floats
    - aspect_ratio : tuple of two floats or {'auto'}
    - autoscale : bool
    - margin : float in [0, 1]

    The per data series options and aesthetics are:
    There are none in the base series. See below for options for subclasses.

    Some data series support additional aesthetics or options:

    ListSeries, LineOver1DRangeSeries, Parametric2DLineSeries,
    Parametric3DLineSeries support the following:

    Aesthetics:

    - line_color : function which returns a float.

    options:

    - label : str
    - steps : bool
    - integers_only : bool

    SurfaceOver2DRangeSeries, ParametricSurfaceSeries support the following:

    aesthetics:

    - surface_color : function which returns a float.
    """

    def __init__(self, *args, **kwargs):
        super(Plot, self).__init__()

        #  Options for the graph as a whole.
        #  The possible values for each option are described in the docstring of
        # Plot. They are based purely on convention, no checking is done.
        self.title = None
        self.xlabel = None
        self.ylabel = None
        self.aspect_ratio = 'auto'
        self.xlim = None
        self.ylim = None
        self.axis_center = 'auto'
        self.axis = True
        self.xscale = 'linear'
        self.yscale = 'linear'
        self.legend = False
        self.autoscale = True
        self.margin = 0

        # Contains the data objects to be plotted. The backend should be smart
        # enough to iterate over this list.
        self._series = []
        self._series.extend(args)

        # The backend type. On every show() a new backend instance is created
        # in self._backend which is tightly coupled to the Plot instance
        # (thanks to the parent attribute of the backend).
        self.backend = DefaultBackend


        # The keyword arguments should only contain options for the plot.
        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)

    def show(self):
        # TODO move this to the backend (also for save)
        if hasattr(self, '_backend'):
            self._backend.close()
        self._backend = self.backend(self)
        self._backend.show()

    def save(self, path):
        if hasattr(self, '_backend'):
            self._backend.close()
        self._backend = self.backend(self)
        self._backend.save(path)

    def __str__(self):
        series_strs = [('[%d]: ' % i) + str(s)
                       for i, s in enumerate(self._series)]
        return 'Plot object containing:\n' + '\n'.join(series_strs)

    def __getitem__(self, index):
        return self._series[index]

    def __setitem__(self, index, *args):
        if len(args) == 1 and isinstance(args[0], BaseSeries):
            self._series[index] = args

    def __delitem__(self, index):
        del self._series[index]

    def append(self, arg):
        """Adds an element from a plot's series to an existing plot.

        Examples
        ========

        Consider two ``Plot`` objects, ``p1`` and ``p2``. To add the
        second plot's first series object to the first, use the
        ``append`` method, like so:

        .. plot::
           :format: doctest
           :include-source: True

           >>> from sympy import symbols
           >>> from sympy.plotting import plot
           >>> x = symbols('x')
           >>> p1 = plot(x*x, show=False)
           >>> p2 = plot(x, show=False)
           >>> p1.append(p2[0])
           >>> p1
           Plot object containing:
           [0]: cartesian line: x**2 for x over (-10.0, 10.0)
           [1]: cartesian line: x for x over (-10.0, 10.0)
           >>> p1.show()

        See Also
        ========
        extend

        """
        if isinstance(arg, BaseSeries):
            self._series.append(arg)
        else:
            raise TypeError('Must specify element of plot to append.')

    def extend(self, arg):
        """Adds all series from another plot.

        Examples
        ========

        Consider two ``Plot`` objects, ``p1`` and ``p2``. To add the
        second plot to the first, use the ``extend`` method, like so:

        .. plot::
           :format: doctest
           :include-source: True

           >>> from sympy import symbols
           >>> from sympy.plotting import plot
           >>> x = symbols('x')
           >>> p1 = plot(x**2, show=False)
           >>> p2 = plot(x, -x, show=False)
           >>> p1.extend(p2)
           >>> p1
           Plot object containing:
           [0]: cartesian line: x**2 for x over (-10.0, 10.0)
           [1]: cartesian line: x for x over (-10.0, 10.0)
           [2]: cartesian line: -x for x over (-10.0, 10.0)
           >>> p1.show()

        """
        if isinstance(arg, Plot):
            self._series.extend(arg._series)
        elif is_sequence(arg):
            self._series.extend(arg)
        else:
            raise TypeError('Expecting Plot or sequence of BaseSeries')


##############################################################################
# Data Series
##############################################################################
#TODO more general way to calculate aesthetics (see get_color_array)

### The base class for all series
class BaseSeries(object):
    """Base class for the data objects containing stuff to be plotted.

    The backend should check if it supports the data series that it's given.
    (eg TextBackend supports only LineOver1DRange).
    It's the backend responsibility to know how to use the class of
    data series that it's given.

    Some data series classes are grouped (using a class attribute like is_2Dline)
    according to the api they present (based only on convention). The backend is
    not obliged to use that api (eg. The LineOver1DRange belongs to the
    is_2Dline group and presents the get_points method, but the
    TextBackend does not use the get_points method).
    """

    # Some flags follow. The rationale for using flags instead of checking base
    # classes is that setting multiple flags is simpler than multiple
    # inheritance.

    is_2Dline = False
    # Some of the backends expect:
    #  - get_points returning 1D np.arrays list_x, list_y
    #  - get_segments returning np.array (done in Line2DBaseSeries)
    #  - get_color_array returning 1D np.array (done in Line2DBaseSeries)
    # with the colors calculated at the points from get_points

    is_3Dline = False
    # Some of the backends expect:
    #  - get_points returning 1D np.arrays list_x, list_y, list_y
    #  - get_segments returning np.array (done in Line2DBaseSeries)
    #  - get_color_array returning 1D np.array (done in Line2DBaseSeries)
    # with the colors calculated at the points from get_points

    is_3Dsurface = False
    # Some of the backends expect:
    #   - get_meshes returning mesh_x, mesh_y, mesh_z (2D np.arrays)
    #   - get_points an alias for get_meshes

    is_contour = False
    # Some of the backends expect:
    #   - get_meshes returning mesh_x, mesh_y, mesh_z (2D np.arrays)
    #   - get_points an alias for get_meshes

    is_implicit = False
    # Some of the backends expect:
    #   - get_meshes returning mesh_x (1D array), mesh_y(1D array,
    #     mesh_z (2D np.arrays)
    #   - get_points an alias for get_meshes
    #Different from is_contour as the colormap in backend will be
    #different

    is_parametric = False
    # The calculation of aesthetics expects:
    #   - get_parameter_points returning one or two np.arrays (1D or 2D)
    # used for calculation aesthetics

    def __init__(self):
        super(BaseSeries, self).__init__()

    @property
    def is_3D(self):
        flags3D = [
            self.is_3Dline,
            self.is_3Dsurface
        ]
        return any(flags3D)

    @property
    def is_line(self):
        flagslines = [
            self.is_2Dline,
            self.is_3Dline
        ]
        return any(flagslines)


### 2D lines
class Line2DBaseSeries(BaseSeries):
    """A base class for 2D lines.

    - adding the label, steps and only_integers options
    - making is_2Dline true
    - defining get_segments and get_color_array
    """

    is_2Dline = True

    _dim = 2

    def __init__(self):
        super(Line2DBaseSeries, self).__init__()
        self.label = None
        self.steps = False
        self.only_integers = False
        self.line_color = None

    def get_segments(self):
        np = import_module('numpy')
        points = self.get_points()
        if self.steps is True:
            x = np.array((points[0], points[0])).T.flatten()[1:]
            y = np.array((points[1], points[1])).T.flatten()[:-1]
            points = (x, y)
        points = np.ma.array(points).T.reshape(-1, 1, self._dim)
        return np.ma.concatenate([points[:-1], points[1:]], axis=1)

    def get_color_array(self):
        np = import_module('numpy')
        c = self.line_color
        if hasattr(c, '__call__'):
            f = np.vectorize(c)
            nargs = arity(c)
            if nargs == 1 and self.is_parametric:
                x = self.get_parameter_points()
                return f(centers_of_segments(x))
            else:
                variables = list(map(centers_of_segments, self.get_points()))
                if nargs == 1:
                    return f(variables[0])
                elif nargs == 2:
                    return f(*variables[:2])
                else:  # only if the line is 3D (otherwise raises an error)
                    return f(*variables)
        else:
            return c*np.ones(self.nb_of_points)


class List2DSeries(Line2DBaseSeries):
    """Representation for a line consisting of list of points."""

    def __init__(self, list_x, list_y):
        np = import_module('numpy')
        super(List2DSeries, self).__init__()
        self.list_x = np.array(list_x)
        self.list_y = np.array(list_y)
        self.label = 'list'

    def __str__(self):
        return 'list plot'

    def get_points(self):
        return (self.list_x, self.list_y)


class LineOver1DRangeSeries(Line2DBaseSeries):
    """Representation for a line consisting of a SymPy expression over a range."""

    def __init__(self, expr, var_start_end, **kwargs):
        super(LineOver1DRangeSeries, self).__init__()
        self.expr = sympify(expr)
        self.label = str(self.expr)
        self.var = sympify(var_start_end[0])
        self.start = float(var_start_end[1])
        self.end = float(var_start_end[2])
        self.nb_of_points = kwargs.get('nb_of_points', 300)
        self.adaptive = kwargs.get('adaptive', True)
        self.depth = kwargs.get('depth', 12)
        self.line_color = kwargs.get('line_color', None)
        self.xscale=kwargs.get('xscale','linear')
        self.flag=0





    def __str__(self):
        return 'cartesian line: %s for %s over %s' % (
            str(self.expr), str(self.var), str((self.start, self.end)))

    def get_segments(self):
        """
        Adaptively gets segments for plotting.

        The adaptive sampling is done by recursively checking if three
        points are almost collinear. If they are not collinear, then more
        points are added between those points.

        References
        ==========
        [1] Adaptive polygonal approximation of parametric curves,
            Luiz Henrique de Figueiredo.

        """

        if self.only_integers or not self.adaptive:
            return super(LineOver1DRangeSeries, self).get_segments()
        else:
            f = lambdify([self.var], self.expr)
            list_segments = []
            np=import_module('numpy')
            def sample(p, q, depth):
                """ Samples recursively if three points are almost collinear.
                For depth < 6, points are added irrespective of whether they
                satisfy the collinearity condition or not. The maximum depth
                allowed is 12.
                """
                np = import_module('numpy')
                #Randomly sample to avoid aliasing.
                random = 0.45 + np.random.rand() * 0.1
                xnew = p[0] + random * (q[0] - p[0])
                ynew = f(xnew)
                new_point = np.array([xnew, ynew])

                if self.flag==1:
                    return
                #Maximum depth
                if depth > self.depth:
                    if p[1] is None or q[1] is None:
                        self.flag=1
                        return
                    list_segments.append([p, q])

                #Sample irrespective of whether the line is flat till the
                #depth of 6. We are not using linspace to avoid aliasing.
                elif depth < 6:
                    sample(p, new_point, depth + 1)
                    sample(new_point, q, depth + 1)

                #Sample ten points if complex values are encountered
                #at both ends. If there is a real value in between, then
                #sample those points further.
                elif p[1] is None and q[1] is None:
                    if self.xscale is 'log':
                        xarray = np.logspace(p[0],q[0], 10)
                    else:
                        xarray = np.linspace(p[0], q[0], 10)
                    yarray = list(map(f, xarray))
                    if any(y is not None for y in yarray):
                        for i in range(len(yarray) - 1):
                            if yarray[i] is not None or yarray[i + 1] is not None:
                                sample([xarray[i], yarray[i]],
                                    [xarray[i + 1], yarray[i + 1]], depth + 1)

                #Sample further if one of the end points in None( i.e. a complex
                #value) or the three points are not almost collinear.
                elif (p[1] is None or q[1] is None or new_point[1] is None
                        or not flat(p, new_point, q)):
                    sample(p, new_point, depth + 1)
                    sample(new_point, q, depth + 1)
                else:
                    list_segments.append([p, q])

            if self.xscale is 'log':
                self.start=np.log10(self.start)
                self.end=np.log10(self.end)

            f_start = f(self.start)
            f_end = f(self.end)
            sample([self.start, f_start], [self.end, f_end], 0)

            return list_segments

    def get_points(self):
        np = import_module('numpy')
        if self.only_integers is True:
            if self.xscale is 'log':
                list_x = np.logspace(int(self.start), int(self.end),
                        num=int(self.end) - int(self.start) + 1)
            else:
                list_x = np.linspace(int(self.start), int(self.end),
                    num=int(self.end) - int(self.start) + 1)
        else:
            if self.xscale is 'log':
                list_x = np.logspace(self.start, self.end, num=self.nb_of_points)
            else:
                list_x = np.linspace(self.start, self.end, num=self.nb_of_points)
        f = vectorized_lambdify([self.var], self.expr)
        list_y = f(list_x)
        return (list_x, list_y)


class Parametric2DLineSeries(Line2DBaseSeries):
    """Representation for a line consisting of two parametric sympy expressions
    over a range."""

    is_parametric = True

    def __init__(self, expr_x, expr_y, var_start_end, **kwargs):
        super(Parametric2DLineSeries, self).__init__()
        self.expr_x = sympify(expr_x)
        self.expr_y = sympify(expr_y)
        self.label = "(%s, %s)" % (str(self.expr_x), str(self.expr_y))
        self.var = sympify(var_start_end[0])
        self.start = float(var_start_end[1])
        self.end = float(var_start_end[2])
        self.nb_of_points = kwargs.get('nb_of_points', 300)
        self.adaptive = kwargs.get('adaptive', True)
        self.depth = kwargs.get('depth', 12)
        self.line_color = kwargs.get('line_color', None)

    def __str__(self):
        return 'parametric cartesian line: (%s, %s) for %s over %s' % (
            str(self.expr_x), str(self.expr_y), str(self.var),
            str((self.start, self.end)))

    def get_parameter_points(self):
        np = import_module('numpy')
        return np.linspace(self.start, self.end, num=self.nb_of_points)

    def get_points(self):
        param = self.get_parameter_points()
        fx = vectorized_lambdify([self.var], self.expr_x)
        fy = vectorized_lambdify([self.var], self.expr_y)
        list_x = fx(param)
        list_y = fy(param)
        return (list_x, list_y)

    def get_segments(self):
        """
        Adaptively gets segments for plotting.

        The adaptive sampling is done by recursively checking if three
        points are almost collinear. If they are not collinear, then more
        points are added between those points.

        References
        ==========
        [1] Adaptive polygonal approximation of parametric curves,
            Luiz Henrique de Figueiredo.

        """
        if not self.adaptive:
            return super(Parametric2DLineSeries, self).get_segments()

        f_x = lambdify([self.var], self.expr_x)
        f_y = lambdify([self.var], self.expr_y)
        list_segments = []

        def sample(param_p, param_q, p, q, depth):
            """ Samples recursively if three points are almost collinear.
            For depth < 6, points are added irrespective of whether they
            satisfy the collinearity condition or not. The maximum depth
            allowed is 12.
            """
            #Randomly sample to avoid aliasing.
            np = import_module('numpy')
            random = 0.45 + np.random.rand() * 0.1
            param_new = param_p + random * (param_q - param_p)
            xnew = f_x(param_new)
            ynew = f_y(param_new)
            new_point = np.array([xnew, ynew])

            #Maximum depth
            if depth > self.depth:
                list_segments.append([p, q])

            #Sample irrespective of whether the line is flat till the
            #depth of 6. We are not using linspace to avoid aliasing.
            elif depth < 6:
                sample(param_p, param_new, p, new_point, depth + 1)
                sample(param_new, param_q, new_point, q, depth + 1)

            #Sample ten points if complex values are encountered
            #at both ends. If there is a real value in between, then
            #sample those points further.
            elif ((p[0] is None and q[1] is None) or
                    (p[1] is None and q[1] is None)):
                param_array = np.linspace(param_p, param_q, 10)
                x_array = list(map(f_x, param_array))
                y_array = list(map(f_y, param_array))
                if any(x is not None and y is not None
                        for x, y in zip(x_array, y_array)):
                    for i in range(len(y_array) - 1):
                        if ((x_array[i] is not None and y_array[i] is not None) or
                                (x_array[i + 1] is not None and y_array[i + 1] is not None)):
                            point_a = [x_array[i], y_array[i]]
                            point_b = [x_array[i + 1], y_array[i + 1]]
                            sample(param_array[i], param_array[i], point_a,
                                   point_b, depth + 1)

            #Sample further if one of the end points in None( ie a complex
            #value) or the three points are not almost collinear.
            elif (p[0] is None or p[1] is None
                    or q[1] is None or q[0] is None
                    or not flat(p, new_point, q)):
                sample(param_p, param_new, p, new_point, depth + 1)
                sample(param_new, param_q, new_point, q, depth + 1)
            else:
                list_segments.append([p, q])

        f_start_x = f_x(self.start)
        f_start_y = f_y(self.start)
        start = [f_start_x, f_start_y]
        f_end_x = f_x(self.end)
        f_end_y = f_y(self.end)
        end = [f_end_x, f_end_y]
        sample(self.start, self.end, start, end, 0)
        return list_segments


### 3D lines
class Line3DBaseSeries(Line2DBaseSeries):
    """A base class for 3D lines.

    Most of the stuff is derived from Line2DBaseSeries."""

    is_2Dline = False
    is_3Dline = True
    _dim = 3

    def __init__(self):
        super(Line3DBaseSeries, self).__init__()


class Parametric3DLineSeries(Line3DBaseSeries):
    """Representation for a 3D line consisting of two parametric sympy
    expressions and a range."""

    def __init__(self, expr_x, expr_y, expr_z, var_start_end, **kwargs):
        super(Parametric3DLineSeries, self).__init__()
        self.expr_x = sympify(expr_x)
        self.expr_y = sympify(expr_y)
        self.expr_z = sympify(expr_z)
        self.label = "(%s, %s)" % (str(self.expr_x), str(self.expr_y))
        self.var = sympify(var_start_end[0])
        self.start = float(var_start_end[1])
        self.end = float(var_start_end[2])
        self.nb_of_points = kwargs.get('nb_of_points', 300)
        self.line_color = kwargs.get('line_color', None)

    def __str__(self):
        return '3D parametric cartesian line: (%s, %s, %s) for %s over %s' % (
            str(self.expr_x), str(self.expr_y), str(self.expr_z),
            str(self.var), str((self.start, self.end)))

    def get_parameter_points(self):
        np = import_module('numpy')
        return np.linspace(self.start, self.end, num=self.nb_of_points)

    def get_points(self):
        param = self.get_parameter_points()
        fx = vectorized_lambdify([self.var], self.expr_x)
        fy = vectorized_lambdify([self.var], self.expr_y)
        fz = vectorized_lambdify([self.var], self.expr_z)
        list_x = fx(param)
        list_y = fy(param)
        list_z = fz(param)
        return (list_x, list_y, list_z)


### Surfaces
class SurfaceBaseSeries(BaseSeries):
    """A base class for 3D surfaces."""

    is_3Dsurface = True

    def __init__(self):
        super(SurfaceBaseSeries, self).__init__()
        self.surface_color = None

    def get_color_array(self):
        np = import_module('numpy')
        c = self.surface_color
        if isinstance(c, Callable):
            f = np.vectorize(c)
            nargs = arity(c)
            if self.is_parametric:
                variables = list(map(centers_of_faces, self.get_parameter_meshes()))
                if nargs == 1:
                    return f(variables[0])
                elif nargs == 2:
                    return f(*variables)
            variables = list(map(centers_of_faces, self.get_meshes()))
            if nargs == 1:
                return f(variables[0])
            elif nargs == 2:
                return f(*variables[:2])
            else:
                return f(*variables)
        else:
            return c*np.ones(self.nb_of_points)


class SurfaceOver2DRangeSeries(SurfaceBaseSeries):
    """Representation for a 3D surface consisting of a sympy expression and 2D
    range."""
    def __init__(self, expr, var_start_end_x, var_start_end_y, **kwargs):
        super(SurfaceOver2DRangeSeries, self).__init__()
        self.expr = sympify(expr)
        self.var_x = sympify(var_start_end_x[0])
        self.start_x = float(var_start_end_x[1])
        self.end_x = float(var_start_end_x[2])
        self.var_y = sympify(var_start_end_y[0])
        self.start_y = float(var_start_end_y[1])
        self.end_y = float(var_start_end_y[2])
        self.nb_of_points_x = kwargs.get('nb_of_points_x', 50)
        self.nb_of_points_y = kwargs.get('nb_of_points_y', 50)
        self.surface_color = kwargs.get('surface_color', None)

    def __str__(self):
        return ('cartesian surface: %s for'
                ' %s over %s and %s over %s') % (
                    str(self.expr),
                    str(self.var_x),
                    str((self.start_x, self.end_x)),
                    str(self.var_y),
                    str((self.start_y, self.end_y)))

    def get_meshes(self):
        np = import_module('numpy')
        mesh_x, mesh_y = np.meshgrid(np.linspace(self.start_x, self.end_x,
                                                 num=self.nb_of_points_x),
                                     np.linspace(self.start_y, self.end_y,
                                                 num=self.nb_of_points_y))
        f = vectorized_lambdify((self.var_x, self.var_y), self.expr)
        return (mesh_x, mesh_y, f(mesh_x, mesh_y))


class ParametricSurfaceSeries(SurfaceBaseSeries):
    """Representation for a 3D surface consisting of three parametric sympy
    expressions and a range."""

    is_parametric = True

    def __init__(
        self, expr_x, expr_y, expr_z, var_start_end_u, var_start_end_v,
            **kwargs):
        super(ParametricSurfaceSeries, self).__init__()
        self.expr_x = sympify(expr_x)
        self.expr_y = sympify(expr_y)
        self.expr_z = sympify(expr_z)
        self.var_u = sympify(var_start_end_u[0])
        self.start_u = float(var_start_end_u[1])
        self.end_u = float(var_start_end_u[2])
        self.var_v = sympify(var_start_end_v[0])
        self.start_v = float(var_start_end_v[1])
        self.end_v = float(var_start_end_v[2])
        self.nb_of_points_u = kwargs.get('nb_of_points_u', 50)
        self.nb_of_points_v = kwargs.get('nb_of_points_v', 50)
        self.surface_color = kwargs.get('surface_color', None)

    def __str__(self):
        return ('parametric cartesian surface: (%s, %s, %s) for'
                ' %s over %s and %s over %s') % (
                    str(self.expr_x),
                    str(self.expr_y),
                    str(self.expr_z),
                    str(self.var_u),
                    str((self.start_u, self.end_u)),
                    str(self.var_v),
                    str((self.start_v, self.end_v)))

    def get_parameter_meshes(self):
        np = import_module('numpy')
        return np.meshgrid(np.linspace(self.start_u, self.end_u,
                                       num=self.nb_of_points_u),
                           np.linspace(self.start_v, self.end_v,
                                       num=self.nb_of_points_v))

    def get_meshes(self):
        mesh_u, mesh_v = self.get_parameter_meshes()
        fx = vectorized_lambdify((self.var_u, self.var_v), self.expr_x)
        fy = vectorized_lambdify((self.var_u, self.var_v), self.expr_y)
        fz = vectorized_lambdify((self.var_u, self.var_v), self.expr_z)
        return (fx(mesh_u, mesh_v), fy(mesh_u, mesh_v), fz(mesh_u, mesh_v))


### Contours
class ContourSeries(BaseSeries):
    """Representation for a contour plot."""
    # The code is mostly repetition of SurfaceOver2DRange.
    # Presently used in contour_plot function

    is_contour = True

    def __init__(self, expr, var_start_end_x, var_start_end_y):
        super(ContourSeries, self).__init__()
        self.nb_of_points_x = 50
        self.nb_of_points_y = 50
        self.expr = sympify(expr)
        self.var_x = sympify(var_start_end_x[0])
        self.start_x = float(var_start_end_x[1])
        self.end_x = float(var_start_end_x[2])
        self.var_y = sympify(var_start_end_y[0])
        self.start_y = float(var_start_end_y[1])
        self.end_y = float(var_start_end_y[2])

        self.get_points = self.get_meshes

    def __str__(self):
        return ('contour: %s for '
                '%s over %s and %s over %s') % (
                    str(self.expr),
                    str(self.var_x),
                    str((self.start_x, self.end_x)),
                    str(self.var_y),
                    str((self.start_y, self.end_y)))

    def get_meshes(self):
        np = import_module('numpy')
        mesh_x, mesh_y = np.meshgrid(np.linspace(self.start_x, self.end_x,
                                                 num=self.nb_of_points_x),
                                     np.linspace(self.start_y, self.end_y,
                                                 num=self.nb_of_points_y))
        f = vectorized_lambdify((self.var_x, self.var_y), self.expr)
        return (mesh_x, mesh_y, f(mesh_x, mesh_y))


##############################################################################
# Backends
##############################################################################

class BaseBackend(object):
    def __init__(self, parent):
        super(BaseBackend, self).__init__()
        self.parent = parent


## don't have to check for the success of importing matplotlib in each case;
## we will only be using this backend if we can successfully import matploblib
class MatplotlibBackend(BaseBackend):
    def __init__(self, parent):
        super(MatplotlibBackend, self).__init__(parent)
        are_3D = [s.is_3D for s in self.parent._series]
        self.matplotlib = import_module('matplotlib',
            __import__kwargs={'fromlist': ['pyplot', 'cm', 'collections']},
            min_module_version='1.1.0', catch=(RuntimeError,))
        self.plt = self.matplotlib.pyplot
        self.cm = self.matplotlib.cm
        self.LineCollection = self.matplotlib.collections.LineCollection
        if any(are_3D) and not all(are_3D):
            raise ValueError('The matplotlib backend can not mix 2D and 3D.')
        elif not any(are_3D):
            self.fig = self.plt.figure()
            self.ax = self.fig.add_subplot(111)
            self.ax.spines['left'].set_position('zero')
            self.ax.spines['right'].set_color('none')
            self.ax.spines['bottom'].set_position('zero')
            self.ax.spines['top'].set_color('none')
            self.ax.spines['left'].set_smart_bounds(True)
            self.ax.spines['bottom'].set_smart_bounds(False)
            self.ax.xaxis.set_ticks_position('bottom')
            self.ax.yaxis.set_ticks_position('left')
        elif all(are_3D):
            ## mpl_toolkits.mplot3d is necessary for
            ##      projection='3d'
            mpl_toolkits = import_module('mpl_toolkits',
                                     __import__kwargs={'fromlist': ['mplot3d']})
            self.fig = self.plt.figure()
            self.ax = self.fig.add_subplot(111, projection='3d')

    def process_series(self):
        parent = self.parent

        for s in self.parent._series:
            # Create the collections
            if s.is_2Dline:
                collection = self.LineCollection(s.get_segments())
                self.ax.add_collection(collection)
            elif s.is_contour:
                self.ax.contour(*s.get_meshes())
            elif s.is_3Dline:
                # TODO too complicated, I blame matplotlib
                mpl_toolkits = import_module('mpl_toolkits',
                    __import__kwargs={'fromlist': ['mplot3d']})
                art3d = mpl_toolkits.mplot3d.art3d
                collection = art3d.Line3DCollection(s.get_segments())
                self.ax.add_collection(collection)
                x, y, z = s.get_points()
                self.ax.set_xlim((min(x), max(x)))
                self.ax.set_ylim((min(y), max(y)))
                self.ax.set_zlim((min(z), max(z)))
            elif s.is_3Dsurface:
                x, y, z = s.get_meshes()
                collection = self.ax.plot_surface(x, y, z,
                    cmap=getattr(self.cm, 'viridis', self.cm.jet),
                    rstride=1, cstride=1, linewidth=0.1)
            elif s.is_implicit:
                #Smart bounds have to be set to False for implicit plots.
                self.ax.spines['left'].set_smart_bounds(False)
                self.ax.spines['bottom'].set_smart_bounds(False)
                points = s.get_raster()
                if len(points) == 2:
                    #interval math plotting
                    x, y = _matplotlib_list(points[0])
                    self.ax.fill(x, y, facecolor=s.line_color, edgecolor='None')
                else:
                    # use contourf or contour depending on whether it is
                    # an inequality or equality.
                    #XXX: ``contour`` plots multiple lines. Should be fixed.
                    ListedColormap = self.matplotlib.colors.ListedColormap
                    colormap = ListedColormap(["white", s.line_color])
                    xarray, yarray, zarray, plot_type = points
                    if plot_type == 'contour':
                        self.ax.contour(xarray, yarray, zarray, cmap=colormap)
                    else:
                        self.ax.contourf(xarray, yarray, zarray, cmap=colormap)
            else:
                raise ValueError('The matplotlib backend supports only '
                                 'is_2Dline, is_3Dline, is_3Dsurface and '
                                 'is_contour objects.')

            # Customise the collections with the corresponding per-series
            # options.
            if hasattr(s, 'label'):
                collection.set_label(s.label)
            if s.is_line and s.line_color:
                if isinstance(s.line_color, (float, int)) or isinstance(s.line_color, Callable):
                    color_array = s.get_color_array()
                    collection.set_array(color_array)
                else:
                    collection.set_color(s.line_color)
            if s.is_3Dsurface and s.surface_color:
                if self.matplotlib.__version__ < "1.2.0":  # TODO in the distant future remove this check
                    warnings.warn('The version of matplotlib is too old to use surface coloring.')
                elif isinstance(s.surface_color, (float, int)) or isinstance(s.surface_color, Callable):
                    color_array = s.get_color_array()
                    color_array = color_array.reshape(color_array.size)
                    collection.set_array(color_array)
                else:
                    collection.set_color(s.surface_color)

        # Set global options.
        # TODO The 3D stuff
        # XXX The order of those is important.

        mpl_toolkits = import_module('mpl_toolkits',
            __import__kwargs={'fromlist': ['mplot3d']})
        Axes3D = mpl_toolkits.mplot3d.Axes3D
        if parent.xscale and not isinstance(self.ax, Axes3D):
            self.ax.set_xscale(parent.xscale)
        if parent.yscale and not isinstance(self.ax, Axes3D):
            self.ax.set_yscale(parent.yscale)
        if parent.xlim:
            from sympy.core.basic import Basic
            xlim = parent.xlim
            if any(isinstance(i,Basic) and not i.is_real for i in xlim):
                raise ValueError(
                "All numbers from xlim={} must be real".format(xlim))
            if any(isinstance(i,Basic) and not i.is_finite for i in xlim):
                raise ValueError(
                "All numbers from xlim={} must be finite".format(xlim))
            xlim = (float(i) for i in xlim)
            self.ax.set_xlim(xlim)
        else:
            if all(isinstance(s, LineOver1DRangeSeries) for s in parent._series):
                starts = [s.start for s in parent._series]
                ends = [s.end for s in parent._series]
                self.ax.set_xlim(min(starts), max(ends))
        if parent.ylim:
            from sympy.core.basic import Basic
            ylim = parent.ylim
            if any(isinstance(i,Basic) and not i.is_real for i in ylim):
                raise ValueError(
                "All numbers from ylim={} must be real".format(ylim))
            if any(isinstance(i,Basic) and not i.is_finite for i in ylim):
                raise ValueError(
                "All numbers from ylim={} must be finite".format(ylim))
            ylim = (float(i) for i in ylim)
            self.ax.set_ylim(ylim)
        if not isinstance(self.ax, Axes3D) or self.matplotlib.__version__ >= '1.2.0':  # XXX in the distant future remove this check
            self.ax.set_autoscale_on(parent.autoscale)
        if parent.axis_center:
            val = parent.axis_center
            if isinstance(self.ax, Axes3D):
                pass
            elif val == 'center':
                self.ax.spines['left'].set_position('center')
                self.ax.spines['bottom'].set_position('center')
            elif val == 'auto':
                xl, xh = self.ax.get_xlim()
                yl, yh = self.ax.get_ylim()
                pos_left = ('data', 0) if xl*xh <= 0 else 'center'
                pos_bottom = ('data', 0) if yl*yh <= 0 else 'center'
                self.ax.spines['left'].set_position(pos_left)
                self.ax.spines['bottom'].set_position(pos_bottom)
            else:
                self.ax.spines['left'].set_position(('data', val[0]))
                self.ax.spines['bottom'].set_position(('data', val[1]))
        if not parent.axis:
            self.ax.set_axis_off()
        if parent.legend:
            if self.ax.legend():
                self.ax.legend_.set_visible(parent.legend)
        if parent.margin:
            self.ax.set_xmargin(parent.margin)
            self.ax.set_ymargin(parent.margin)
        if parent.title:
            self.ax.set_title(parent.title)
        if parent.xlabel:
            self.ax.set_xlabel(parent.xlabel, position=(1, 0))
        if parent.ylabel:
            self.ax.set_ylabel(parent.ylabel, position=(0, 1))

    def show(self):
        self.process_series()
        #TODO after fixing https://github.com/ipython/ipython/issues/1255
        # you can uncomment the next line and remove the pyplot.show() call
        #self.fig.show()
        if _show:
            self.plt.show()
        else:
            self.close()

    def save(self, path):
        self.process_series()
        self.fig.savefig(path)

    def close(self):
        self.plt.close(self.fig)


class TextBackend(BaseBackend):
    def __init__(self, parent):
        super(TextBackend, self).__init__(parent)

    def show(self):
        if not _show:
            return
        if len(self.parent._series) != 1:
            raise ValueError(
                'The TextBackend supports only one graph per Plot.')
        elif not isinstance(self.parent._series[0], LineOver1DRangeSeries):
            raise ValueError(
                'The TextBackend supports only expressions over a 1D range')
        else:
            ser = self.parent._series[0]
            textplot(ser.expr, ser.start, ser.end)

    def close(self):
        pass


class DefaultBackend(BaseBackend):
    def __new__(cls, parent):
        matplotlib = import_module('matplotlib', min_module_version='1.1.0', catch=(RuntimeError,))
        if matplotlib:
            return MatplotlibBackend(parent)
        else:
            return TextBackend(parent)


plot_backends = {
    'matplotlib': MatplotlibBackend,
    'text': TextBackend,
    'default': DefaultBackend
}


##############################################################################
# Finding the centers of line segments or mesh faces
##############################################################################

def centers_of_segments(array):
    np = import_module('numpy')
    return np.mean(np.vstack((array[:-1], array[1:])), 0)


def centers_of_faces(array):
    np = import_module('numpy')
    return np.mean(np.dstack((array[:-1, :-1],
                                 array[1:, :-1],
                                 array[:-1, 1: ],
                                 array[:-1, :-1],
                                 )), 2)


def flat(x, y, z, eps=1e-3):
    """Checks whether three points are almost collinear"""
    np = import_module('numpy')
    # Workaround plotting piecewise (#8577):
    #   workaround for `lambdify` in `.experimental_lambdify` fails
    #   to return numerical values in some cases. Lower-level fix
    #   in `lambdify` is possible.
    vector_a = (x - y).astype(np.float)
    vector_b = (z - y).astype(np.float)
    dot_product = np.dot(vector_a, vector_b)
    vector_a_norm = np.linalg.norm(vector_a)
    vector_b_norm = np.linalg.norm(vector_b)
    cos_theta = dot_product / (vector_a_norm * vector_b_norm)
    return abs(cos_theta + 1) < eps


def _matplotlib_list(interval_list):
    """
    Returns lists for matplotlib ``fill`` command from a list of bounding
    rectangular intervals
    """
    xlist = []
    ylist = []
    if len(interval_list):
        for intervals in interval_list:
            intervalx = intervals[0]
            intervaly = intervals[1]
            xlist.extend([intervalx.start, intervalx.start,
                          intervalx.end, intervalx.end, None])
            ylist.extend([intervaly.start, intervaly.end,
                          intervaly.end, intervaly.start, None])
    else:
        #XXX Ugly hack. Matplotlib does not accept empty lists for ``fill``
        xlist.extend([None, None, None, None])
        ylist.extend([None, None, None, None])
    return xlist, ylist


####New API for plotting module ####

# TODO: Add color arrays for plots.
# TODO: Add more plotting options for 3d plots.
# TODO: Adaptive sampling for 3D plots.

def plot(*args, **kwargs):
    """
    Plots a function of a single variable and returns an instance of
    the ``Plot`` class (also, see the description of the
    ``show`` keyword argument below).

    The plotting uses an adaptive algorithm which samples recursively to
    accurately plot the plot. The adaptive algorithm uses a random point near
    the midpoint of two points that has to be further sampled. Hence the same
    plots can appear slightly different.

    Usage
    =====

    Single Plot

    ``plot(expr, range, **kwargs)``

    If the range is not specified, then a default range of (-10, 10) is used.

    Multiple plots with same range.

    ``plot(expr1, expr2, ..., range, **kwargs)``

    If the range is not specified, then a default range of (-10, 10) is used.

    Multiple plots with different ranges.

    ``plot((expr1, range), (expr2, range), ..., **kwargs)``

    Range has to be specified for every expression.

    Default range may change in the future if a more advanced default range
    detection algorithm is implemented.

    Arguments
    =========

    ``expr`` : Expression representing the function of single variable

    ``range``: (x, 0, 5), A 3-tuple denoting the range of the free variable.

    Keyword Arguments
    =================

    Arguments for ``plot`` function:

    ``show``: Boolean. The default value is set to ``True``. Set show to
    ``False`` and the function will not display the plot. The returned
    instance of the ``Plot`` class can then be used to save or display
    the plot by calling the ``save()`` and ``show()`` methods
    respectively.

    Arguments for ``LineOver1DRangeSeries`` class:

    ``adaptive``: Boolean. The default value is set to True. Set adaptive to False and
    specify ``nb_of_points`` if uniform sampling is required.

    ``depth``: int Recursion depth of the adaptive algorithm. A depth of value ``n``
    samples a maximum of `2^{n}` points.

    ``nb_of_points``: int. Used when the ``adaptive`` is set to False. The function
    is uniformly sampled at ``nb_of_points`` number of points.

    Aesthetics options:

    ``line_color``: float. Specifies the color for the plot.
    See ``Plot`` to see how to set color for the plots.

    If there are multiple plots, then the same series series are applied to
    all the plots. If you want to set these options separately, you can index
    the ``Plot`` object returned and set it.

    Arguments for ``Plot`` class:

    ``title`` : str. Title of the plot. It is set to the latex representation of
    the expression, if the plot has only one expression.

    ``xlabel`` : str. Label for the x-axis.

    ``ylabel`` : str. Label for the y-axis.

    ``xscale``: {'linear', 'log'} Sets the scaling of the x-axis.

    ``yscale``: {'linear', 'log'} Sets the scaling if the y-axis.

    ``axis_center``: tuple of two floats denoting the coordinates of the center or
    {'center', 'auto'}

    ``xlim`` : tuple of two floats, denoting the x-axis limits.

    ``ylim`` : tuple of two floats, denoting the y-axis limits.

    Examples
    ========

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> from sympy import symbols
       >>> from sympy.plotting import plot
       >>> x = symbols('x')

    Single Plot

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot(x**2, (x, -5, 5))
       Plot object containing:
       [0]: cartesian line: x**2 for x over (-5.0, 5.0)

    Multiple plots with single range.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot(x, x**2, x**3, (x, -5, 5))
       Plot object containing:
       [0]: cartesian line: x for x over (-5.0, 5.0)
       [1]: cartesian line: x**2 for x over (-5.0, 5.0)
       [2]: cartesian line: x**3 for x over (-5.0, 5.0)

    Multiple plots with different ranges.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot((x**2, (x, -6, 6)), (x, (x, -5, 5)))
       Plot object containing:
       [0]: cartesian line: x**2 for x over (-6.0, 6.0)
       [1]: cartesian line: x for x over (-5.0, 5.0)

    No adaptive sampling.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot(x**2, adaptive=False, nb_of_points=400)
       Plot object containing:
       [0]: cartesian line: x**2 for x over (-10.0, 10.0)

    See Also
    ========

    Plot, LineOver1DRangeSeries.

    """
    args = list(map(sympify, args))
    free = set()
    for a in args:
        if isinstance(a, Expr):
            free |= a.free_symbols
            if len(free) > 1:
                raise ValueError(
                    'The same variable should be used in all '
                    'univariate expressions being plotted.')
    x = free.pop() if free else Symbol('x')
    kwargs.setdefault('xlabel', x.name)
    kwargs.setdefault('ylabel', 'f(%s)' % x.name)
    show = kwargs.pop('show', True)
    series = []
    plot_expr = check_arguments(args, 1, 1)
    series = [LineOver1DRangeSeries(*arg, **kwargs) for arg in plot_expr]

    plots = Plot(*series, **kwargs)
    if show:
        plots.show()
    return plots


def plot_parametric(*args, **kwargs):
    """
    Plots a 2D parametric plot.

    The plotting uses an adaptive algorithm which samples recursively to
    accurately plot the plot. The adaptive algorithm uses a random point near
    the midpoint of two points that has to be further sampled. Hence the same
    plots can appear slightly different.

    Usage
    =====

    Single plot.

    ``plot_parametric(expr_x, expr_y, range, **kwargs)``

    If the range is not specified, then a default range of (-10, 10) is used.

    Multiple plots with same range.

    ``plot_parametric((expr1_x, expr1_y), (expr2_x, expr2_y), range, **kwargs)``

    If the range is not specified, then a default range of (-10, 10) is used.

    Multiple plots with different ranges.

    ``plot_parametric((expr_x, expr_y, range), ..., **kwargs)``

    Range has to be specified for every expression.

    Default range may change in the future if a more advanced default range
    detection algorithm is implemented.

    Arguments
    =========

    ``expr_x`` : Expression representing the function along x.

    ``expr_y`` : Expression representing the function along y.

    ``range``: (u, 0, 5), A 3-tuple denoting the range of the parameter
    variable.

    Keyword Arguments
    =================

    Arguments for ``Parametric2DLineSeries`` class:

    ``adaptive``: Boolean. The default value is set to True. Set adaptive to
    False and specify ``nb_of_points`` if uniform sampling is required.

    ``depth``: int Recursion depth of the adaptive algorithm. A depth of
    value ``n`` samples a maximum of `2^{n}` points.

    ``nb_of_points``: int. Used when the ``adaptive`` is set to False. The
    function is uniformly sampled at ``nb_of_points`` number of points.

    Aesthetics
    ----------

    ``line_color``: function which returns a float. Specifies the color for the
    plot. See ``sympy.plotting.Plot`` for more details.

    If there are multiple plots, then the same Series arguments are applied to
    all the plots. If you want to set these options separately, you can index
    the returned ``Plot`` object and set it.

    Arguments for ``Plot`` class:

    ``xlabel`` : str. Label for the x-axis.

    ``ylabel`` : str. Label for the y-axis.

    ``xscale``: {'linear', 'log'} Sets the scaling of the x-axis.

    ``yscale``: {'linear', 'log'} Sets the scaling if the y-axis.

    ``axis_center``: tuple of two floats denoting the coordinates of the center
    or {'center', 'auto'}

    ``xlim`` : tuple of two floats, denoting the x-axis limits.

    ``ylim`` : tuple of two floats, denoting the y-axis limits.

    Examples
    ========

    .. plot::
       :context: reset
       :format: doctest
       :include-source: True

       >>> from sympy import symbols, cos, sin
       >>> from sympy.plotting import plot_parametric
       >>> u = symbols('u')

    Single Parametric plot

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_parametric(cos(u), sin(u), (u, -5, 5))
       Plot object containing:
       [0]: parametric cartesian line: (cos(u), sin(u)) for u over (-5.0, 5.0)


    Multiple parametric plot with single range.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_parametric((cos(u), sin(u)), (u, cos(u)))
       Plot object containing:
       [0]: parametric cartesian line: (cos(u), sin(u)) for u over (-10.0, 10.0)
       [1]: parametric cartesian line: (u, cos(u)) for u over (-10.0, 10.0)

    Multiple parametric plots.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot_parametric((cos(u), sin(u), (u, -5, 5)),
       ...     (cos(u), u, (u, -5, 5)))
       Plot object containing:
       [0]: parametric cartesian line: (cos(u), sin(u)) for u over (-5.0, 5.0)
       [1]: parametric cartesian line: (cos(u), u) for u over (-5.0, 5.0)


    See Also
    ========
    Plot, Parametric2DLineSeries

    """
    args = list(map(sympify, args))
    show = kwargs.pop('show', True)
    series = []
    plot_expr = check_arguments(args, 2, 1)
    series = [Parametric2DLineSeries(*arg, **kwargs) for arg in plot_expr]
    plots = Plot(*series, **kwargs)
    if show:
        plots.show()
    return plots


def plot3d_parametric_line(*args, **kwargs):
    """
    Plots a 3D parametric line plot.

    Usage
    =====

    Single plot:

    ``plot3d_parametric_line(expr_x, expr_y, expr_z, range, **kwargs)``

    If the range is not specified, then a default range of (-10, 10) is used.

    Multiple plots.

    ``plot3d_parametric_line((expr_x, expr_y, expr_z, range), ..., **kwargs)``

    Ranges have to be specified for every expression.

    Default range may change in the future if a more advanced default range
    detection algorithm is implemented.

    Arguments
    =========

    ``expr_x`` : Expression representing the function along x.

    ``expr_y`` : Expression representing the function along y.

    ``expr_z`` : Expression representing the function along z.

    ``range``: ``(u, 0, 5)``, A 3-tuple denoting the range of the parameter
    variable.

    Keyword Arguments
    =================

    Arguments for ``Parametric3DLineSeries`` class.

    ``nb_of_points``: The range is uniformly sampled at ``nb_of_points``
    number of points.

    Aesthetics:

    ``line_color``: function which returns a float. Specifies the color for the
    plot. See ``sympy.plotting.Plot`` for more details.

    If there are multiple plots, then the same series arguments are applied to
    all the plots. If you want to set these options separately, you can index
    the returned ``Plot`` object and set it.

    Arguments for ``Plot`` class.

    ``title`` : str. Title of the plot.

    Examples
    ========

    .. plot::
       :context: reset
       :format: doctest
       :include-source: True

       >>> from sympy import symbols, cos, sin
       >>> from sympy.plotting import plot3d_parametric_line
       >>> u = symbols('u')

    Single plot.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot3d_parametric_line(cos(u), sin(u), u, (u, -5, 5))
       Plot object containing:
       [0]: 3D parametric cartesian line: (cos(u), sin(u), u) for u over (-5.0, 5.0)


    Multiple plots.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot3d_parametric_line((cos(u), sin(u), u, (u, -5, 5)),
       ...     (sin(u), u**2, u, (u, -5, 5)))
       Plot object containing:
       [0]: 3D parametric cartesian line: (cos(u), sin(u), u) for u over (-5.0, 5.0)
       [1]: 3D parametric cartesian line: (sin(u), u**2, u) for u over (-5.0, 5.0)


    See Also
    ========

    Plot, Parametric3DLineSeries

    """
    args = list(map(sympify, args))
    show = kwargs.pop('show', True)
    series = []
    plot_expr = check_arguments(args, 3, 1)
    series = [Parametric3DLineSeries(*arg, **kwargs) for arg in plot_expr]
    plots = Plot(*series, **kwargs)
    if show:
        plots.show()
    return plots


def plot3d(*args, **kwargs):
    """
    Plots a 3D surface plot.

    Usage
    =====

    Single plot

    ``plot3d(expr, range_x, range_y, **kwargs)``

    If the ranges are not specified, then a default range of (-10, 10) is used.

    Multiple plot with the same range.

    ``plot3d(expr1, expr2, range_x, range_y, **kwargs)``

    If the ranges are not specified, then a default range of (-10, 10) is used.

    Multiple plots with different ranges.

    ``plot3d((expr1, range_x, range_y), (expr2, range_x, range_y), ..., **kwargs)``

    Ranges have to be specified for every expression.

    Default range may change in the future if a more advanced default range
    detection algorithm is implemented.

    Arguments
    =========

    ``expr`` : Expression representing the function along x.

    ``range_x``: (x, 0, 5), A 3-tuple denoting the range of the x
    variable.

    ``range_y``: (y, 0, 5), A 3-tuple denoting the range of the y
     variable.

    Keyword Arguments
    =================

    Arguments for ``SurfaceOver2DRangeSeries`` class:

    ``nb_of_points_x``: int. The x range is sampled uniformly at
    ``nb_of_points_x`` of points.

    ``nb_of_points_y``: int. The y range is sampled uniformly at
    ``nb_of_points_y`` of points.

    Aesthetics:

    ``surface_color``: Function which returns a float. Specifies the color for
    the surface of the plot. See ``sympy.plotting.Plot`` for more details.

    If there are multiple plots, then the same series arguments are applied to
    all the plots. If you want to set these options separately, you can index
    the returned ``Plot`` object and set it.

    Arguments for ``Plot`` class:

    ``title`` : str. Title of the plot.

    Examples
    ========

    .. plot::
       :context: reset
       :format: doctest
       :include-source: True

       >>> from sympy import symbols
       >>> from sympy.plotting import plot3d
       >>> x, y = symbols('x y')

    Single plot

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot3d(x*y, (x, -5, 5), (y, -5, 5))
       Plot object containing:
       [0]: cartesian surface: x*y for x over (-5.0, 5.0) and y over (-5.0, 5.0)


    Multiple plots with same range

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot3d(x*y, -x*y, (x, -5, 5), (y, -5, 5))
       Plot object containing:
       [0]: cartesian surface: x*y for x over (-5.0, 5.0) and y over (-5.0, 5.0)
       [1]: cartesian surface: -x*y for x over (-5.0, 5.0) and y over (-5.0, 5.0)


    Multiple plots with different ranges.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot3d((x**2 + y**2, (x, -5, 5), (y, -5, 5)),
       ...     (x*y, (x, -3, 3), (y, -3, 3)))
       Plot object containing:
       [0]: cartesian surface: x**2 + y**2 for x over (-5.0, 5.0) and y over (-5.0, 5.0)
       [1]: cartesian surface: x*y for x over (-3.0, 3.0) and y over (-3.0, 3.0)


    See Also
    ========
    Plot, SurfaceOver2DRangeSeries

    """

    args = list(map(sympify, args))
    show = kwargs.pop('show', True)
    series = []
    plot_expr = check_arguments(args, 1, 2)
    series = [SurfaceOver2DRangeSeries(*arg, **kwargs) for arg in plot_expr]
    plots = Plot(*series, **kwargs)
    if show:
        plots.show()
    return plots


def plot3d_parametric_surface(*args, **kwargs):
    """
    Plots a 3D parametric surface plot.

    Usage
    =====

    Single plot.

    ``plot3d_parametric_surface(expr_x, expr_y, expr_z, range_u, range_v, **kwargs)``

    If the ranges is not specified, then a default range of (-10, 10) is used.

    Multiple plots.

    ``plot3d_parametric_surface((expr_x, expr_y, expr_z, range_u, range_v), ..., **kwargs)``

    Ranges have to be specified for every expression.

    Default range may change in the future if a more advanced default range
    detection algorithm is implemented.

    Arguments
    =========

    ``expr_x``: Expression representing the function along ``x``.

    ``expr_y``: Expression representing the function along ``y``.

    ``expr_z``: Expression representing the function along ``z``.

    ``range_u``: ``(u, 0, 5)``,  A 3-tuple denoting the range of the ``u``
    variable.

    ``range_v``: ``(v, 0, 5)``,  A 3-tuple denoting the range of the v
    variable.

    Keyword Arguments
    =================

    Arguments for ``ParametricSurfaceSeries`` class:

    ``nb_of_points_u``: int. The ``u`` range is sampled uniformly at
    ``nb_of_points_v`` of points

    ``nb_of_points_y``: int. The ``v`` range is sampled uniformly at
    ``nb_of_points_y`` of points

    Aesthetics:

    ``surface_color``: Function which returns a float. Specifies the color for
    the surface of the plot. See ``sympy.plotting.Plot`` for more details.

    If there are multiple plots, then the same series arguments are applied for
    all the plots. If you want to set these options separately, you can index
    the returned ``Plot`` object and set it.


    Arguments for ``Plot`` class:

    ``title`` : str. Title of the plot.

    Examples
    ========

    .. plot::
       :context: reset
       :format: doctest
       :include-source: True

       >>> from sympy import symbols, cos, sin
       >>> from sympy.plotting import plot3d_parametric_surface
       >>> u, v = symbols('u v')

    Single plot.

    .. plot::
       :context: close-figs
       :format: doctest
       :include-source: True

       >>> plot3d_parametric_surface(cos(u + v), sin(u - v), u - v,
       ...     (u, -5, 5), (v, -5, 5))
       Plot object containing:
       [0]: parametric cartesian surface: (cos(u + v), sin(u - v), u - v) for u over (-5.0, 5.0) and v over (-5.0, 5.0)


    See Also
    ========
    Plot, ParametricSurfaceSeries

    """

    args = list(map(sympify, args))
    show = kwargs.pop('show', True)
    series = []
    plot_expr = check_arguments(args, 3, 2)
    series = [ParametricSurfaceSeries(*arg, **kwargs) for arg in plot_expr]
    plots = Plot(*series, **kwargs)
    if show:
        plots.show()
    return plots

def plot_contour(*args, **kwargs):
    """
    Draws contour plot of a function

    Usage
    =====

    Single plot

    ``plot_contour(expr, range_x, range_y, **kwargs)``

    If the ranges are not specified, then a default range of (-10, 10) is used.

    Multiple plot with the same range.

    ``plot_contour(expr1, expr2, range_x, range_y, **kwargs)``

    If the ranges are not specified, then a default range of (-10, 10) is used.

    Multiple plots with different ranges.

    ``plot_contour((expr1, range_x, range_y), (expr2, range_x, range_y), ..., **kwargs)``

    Ranges have to be specified for every expression.

    Default range may change in the future if a more advanced default range
    detection algorithm is implemented.

    Arguments
    =========

    ``expr`` : Expression representing the function along x.

    ``range_x``: (x, 0, 5), A 3-tuple denoting the range of the x
    variable.

    ``range_y``: (y, 0, 5), A 3-tuple denoting the range of the y
     variable.

    Keyword Arguments
    =================

    Arguments for ``ContourSeries`` class:

    ``nb_of_points_x``: int. The x range is sampled uniformly at
    ``nb_of_points_x`` of points.

    ``nb_of_points_y``: int. The y range is sampled uniformly at
    ``nb_of_points_y`` of points.

    Aesthetics:

    ``surface_color``: Function which returns a float. Specifies the color for
    the surface of the plot. See ``sympy.plotting.Plot`` for more details.

    If there are multiple plots, then the same series arguments are applied to
    all the plots. If you want to set these options separately, you can index
    the returned ``Plot`` object and set it.

    Arguments for ``Plot`` class:

    ``title`` : str. Title of the plot.

    See Also
    ========
    Plot, ContourSeries
    """

    args = list(map(sympify, args))
    show = kwargs.pop('show', True)
    plot_expr = check_arguments(args, 1, 2)
    series = [ContourSeries(*arg) for arg in plot_expr]
    plot_contours = Plot(*series, **kwargs)
    if len(plot_expr[0].free_symbols) > 2:
        raise ValueError('Contour Plot cannot Plot for more than two variables.')
    if show:
        plot_contours.show()
    return plot_contours

def check_arguments(args, expr_len, nb_of_free_symbols):
    """
    Checks the arguments and converts into tuples of the
    form (exprs, ranges)

    Examples
    ========

    .. plot::
       :context: reset
       :format: doctest
       :include-source: True

       >>> from sympy import plot, cos, sin, symbols
       >>> from sympy.plotting.plot import check_arguments
       >>> x = symbols('x')
       >>> check_arguments([cos(x), sin(x)], 2, 1)
           [(cos(x), sin(x), (x, -10, 10))]

       >>> check_arguments([x, x**2], 1, 1)
           [(x, (x, -10, 10)), (x**2, (x, -10, 10))]
    """
    if expr_len > 1 and isinstance(args[0], Expr):
        # Multiple expressions same range.
        # The arguments are tuples when the expression length is
        # greater than 1.
        if len(args) < expr_len:
            raise ValueError("len(args) should not be less than expr_len")
        for i in range(len(args)):
            if isinstance(args[i], Tuple):
                break
        else:
            i = len(args) + 1

        exprs = Tuple(*args[:i])
        free_symbols = list(set().union(*[e.free_symbols for e in exprs]))
        if len(args) == expr_len + nb_of_free_symbols:
            #Ranges given
            plots = [exprs + Tuple(*args[expr_len:])]
        else:
            default_range = Tuple(-10, 10)
            ranges = []
            for symbol in free_symbols:
                ranges.append(Tuple(symbol) + default_range)

            for i in range(len(free_symbols) - nb_of_free_symbols):
                ranges.append(Tuple(Dummy()) + default_range)
            plots = [exprs + Tuple(*ranges)]
        return plots

    if isinstance(args[0], Expr) or (isinstance(args[0], Tuple) and
                                     len(args[0]) == expr_len and
                                     expr_len != 3):
        # Cannot handle expressions with number of expression = 3. It is
        # not possible to differentiate between expressions and ranges.
        #Series of plots with same range
        for i in range(len(args)):
            if isinstance(args[i], Tuple) and len(args[i]) != expr_len:
                break
            if not isinstance(args[i], Tuple):
                args[i] = Tuple(args[i])
        else:
            i = len(args) + 1

        exprs = args[:i]
        assert all(isinstance(e, Expr) for expr in exprs for e in expr)
        free_symbols = list(set().union(*[e.free_symbols for expr in exprs
                                        for e in expr]))

        if len(free_symbols) > nb_of_free_symbols:
            raise ValueError("The number of free_symbols in the expression "
                             "is greater than %d" % nb_of_free_symbols)
        if len(args) == i + nb_of_free_symbols and isinstance(args[i], Tuple):
            ranges = Tuple(*[range_expr for range_expr in args[
                           i:i + nb_of_free_symbols]])
            plots = [expr + ranges for expr in exprs]
            return plots
        else:
            #Use default ranges.
            default_range = Tuple(-10, 10)
            ranges = []
            for symbol in free_symbols:
                ranges.append(Tuple(symbol) + default_range)

            for i in range(nb_of_free_symbols - len(free_symbols)):
                ranges.append(Tuple(Dummy()) + default_range)
            ranges = Tuple(*ranges)
            plots = [expr + ranges for expr in exprs]
            return plots

    elif isinstance(args[0], Tuple) and len(args[0]) == expr_len + nb_of_free_symbols:
        #Multiple plots with different ranges.
        for arg in args:
            for i in range(expr_len):
                if not isinstance(arg[i], Expr):
                    raise ValueError("Expected an expression, given %s" %
                                     str(arg[i]))
            for i in range(nb_of_free_symbols):
                if not len(arg[i + expr_len]) == 3:
                    raise ValueError("The ranges should be a tuple of "
                                     "length 3, got %s" % str(arg[i + expr_len]))
        return args
