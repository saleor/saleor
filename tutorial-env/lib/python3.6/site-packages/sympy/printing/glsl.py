from sympy.codegen.ast import Assignment
from sympy.core import S
from sympy.core.compatibility import string_types, range
from sympy.core.function import _coeff_isneg, Lambda
from sympy.printing.codeprinter import CodePrinter
from sympy.printing.precedence import precedence
from functools import reduce

known_functions = {
    'Abs': 'abs',
    'sin': 'sin',
    'cos': 'cos',
    'tan': 'tan',
    'acos': 'acos',
    'asin': 'asin',
    'atan': 'atan',
    'atan2': 'atan',
    'ceiling': 'ceil',
    'floor': 'floor',
    'sign': 'sign',
    'exp': 'exp',
    'log': 'log',
    'add': 'add',
    'sub': 'sub',
    'mul': 'mul',
    'pow': 'pow'
}

class GLSLPrinter(CodePrinter):
    """
    Rudimentary, generic GLSL printing tools.

    Additional settings:
    'use_operators': Boolean (should the printer use operators for +,-,*, or functions?)
    """
    _not_supported = set()
    printmethod = "_glsl"
    language = "GLSL"

    _default_settings = {
        'use_operators': True,
        'mat_nested': False,
        'mat_separator': ',\n',
        'mat_transpose': False,
        'glsl_types': True,

        'order': None,
        'full_prec': 'auto',
        'precision': 9,
        'user_functions': {},
        'human': True,
        'allow_unknown_functions': False,
        'contract': True,
        'error_on_reserved': False,
        'reserved_word_suffix': '_'
    }

    def __init__(self, settings={}):
        CodePrinter.__init__(self, settings)
        self.known_functions = dict(known_functions)
        userfuncs = settings.get('user_functions', {})
        self.known_functions.update(userfuncs)

    def _rate_index_position(self, p):
        return p*5

    def _get_statement(self, codestring):
        return "%s;" % codestring

    def _get_comment(self, text):
        return "// {0}".format(text)

    def _declare_number_const(self, name, value):
        return "float {0} = {1};".format(name, value)

    def _format_code(self, lines):
        return self.indent_code(lines)

    def indent_code(self, code):
        """Accepts a string of code or a list of code lines"""

        if isinstance(code, string_types):
            code_lines = self.indent_code(code.splitlines(True))
            return ''.join(code_lines)

        tab = "   "
        inc_token = ('{', '(', '{\n', '(\n')
        dec_token = ('}', ')')

        code = [line.lstrip(' \t') for line in code]

        increase = [int(any(map(line.endswith, inc_token))) for line in code]
        decrease = [int(any(map(line.startswith, dec_token))) for line in code]

        pretty = []
        level = 0
        for n, line in enumerate(code):
            if line == '' or line == '\n':
                pretty.append(line)
                continue
            level -= decrease[n]
            pretty.append("%s%s" % (tab*level, line))
            level += increase[n]
        return pretty

    def _print_MatrixBase(self, mat):
        mat_separator = self._settings['mat_separator']
        mat_transpose = self._settings['mat_transpose']
        glsl_types = self._settings['glsl_types']
        column_vector = (mat.rows == 1) if mat_transpose else (mat.cols == 1)
        A = mat.transpose() if mat_transpose != column_vector else mat

        if A.cols == 1:
            return self._print(A[0]);
        if A.rows <= 4 and A.cols <= 4 and glsl_types:
            if A.rows == 1:
                return 'vec%s%s' % (A.cols, A.table(self,rowstart='(',rowend=')'))
            elif A.rows == A.cols:
                return 'mat%s(%s)' %   (A.rows, A.table(self,rowsep=', ',
                                        rowstart='',rowend=''))
            else:
                return 'mat%sx%s(%s)' % (A.cols, A.rows,
                                        A.table(self,rowsep=', ',
                                        rowstart='',rowend=''))
        elif A.cols == 1 or A.rows == 1:
            return 'float[%s](%s)' % (A.cols*A.rows, A.table(self,rowsep=mat_separator,rowstart='',rowend=''))
        elif not self._settings['mat_nested']:
            return 'float[%s](\n%s\n) /* a %sx%s matrix */' % (A.cols*A.rows,
                            A.table(self,rowsep=mat_separator,rowstart='',rowend=''),
                            A.rows,A.cols)
        elif self._settings['mat_nested']:
            return 'float[%s][%s](\n%s\n)' % (A.rows,A.cols,A.table(self,rowsep=mat_separator,rowstart='float[](',rowend=')'))

    _print_Matrix = \
        _print_MatrixElement = \
        _print_DenseMatrix = \
        _print_MutableDenseMatrix = \
        _print_ImmutableMatrix = \
        _print_ImmutableDenseMatrix = \
        _print_MatrixBase

    def _traverse_matrix_indices(self, mat):
        mat_transpose = self._settings['mat_transpose']
        if mat_transpose:
            rows,cols = mat.shape
        else:
            cols,rows = mat.shape
        return ((i, j) for i in range(cols) for j in range(rows))

    def _print_MatrixElement(self, expr):
        # print('begin _print_MatrixElement')
        nest = self._settings['mat_nested'];
        glsl_types = self._settings['glsl_types'];
        mat_transpose = self._settings['mat_transpose'];
        if mat_transpose:
            cols,rows = expr.parent.shape
            i,j = expr.j,expr.i
        else:
            rows,cols = expr.parent.shape
            i,j = expr.i,expr.j
        pnt = self._print(expr.parent)
        if glsl_types and ((rows <= 4 and cols <=4) or nest):
            # print('end _print_MatrixElement case A',nest,glsl_types)
            return "%s[%s][%s]" % (pnt, i, j)
        else:
            # print('end _print_MatrixElement case B',nest,glsl_types)
            return "{0}[{1}]".format(pnt, i + j*rows)

    def _print_list(self, expr):
        l = ', '.join(self._print(item) for item in expr)
        glsl_types = self._settings['glsl_types']
        if len(expr) <= 4 and glsl_types:
            return 'vec%s(%s)' % (len(expr),l)
        else:
            return 'float[%s](%s)' % (len(expr),l)

    _print_tuple = _print_list
    _print_Tuple = _print_list

    def _get_loop_opening_ending(self, indices):
        open_lines = []
        close_lines = []
        loopstart = "for (int %(varble)s=%(start)s; %(varble)s<%(end)s; %(varble)s++){"
        for i in indices:
            # GLSL arrays start at 0 and end at dimension-1
            open_lines.append(loopstart % {
                'varble': self._print(i.label),
                'start': self._print(i.lower),
                'end': self._print(i.upper + 1)})
            close_lines.append("}")
        return open_lines, close_lines

    def _print_Function_with_args(self, func, func_args):
        if func in self.known_functions:
            cond_func = self.known_functions[func]
            func = None
            if isinstance(cond_func, string_types):
                func = cond_func
            else:
                for cond, func in cond_func:
                    if cond(func_args):
                        break
            if func is not None:
                try:
                    return func(*[self.parenthesize(item, 0) for item in func_args])
                except TypeError:
                    return "%s(%s)" % (func, self.stringify(func_args, ", "))
        elif isinstance(func, Lambda):
            # inlined function
            return self._print(func(*func_args))
        else:
            return self._print_not_supported(func)

    def _print_Piecewise(self, expr):
        if expr.args[-1].cond != True:
            # We need the last conditional to be a True, otherwise the resulting
            # function may not return a result.
            raise ValueError("All Piecewise expressions must contain an "
                             "(expr, True) statement to be used as a default "
                             "condition. Without one, the generated "
                             "expression may not evaluate to anything under "
                             "some condition.")
        lines = []
        if expr.has(Assignment):
            for i, (e, c) in enumerate(expr.args):
                if i == 0:
                    lines.append("if (%s) {" % self._print(c))
                elif i == len(expr.args) - 1 and c == True:
                    lines.append("else {")
                else:
                    lines.append("else if (%s) {" % self._print(c))
                code0 = self._print(e)
                lines.append(code0)
                lines.append("}")
            return "\n".join(lines)
        else:
            # The piecewise was used in an expression, need to do inline
            # operators. This has the downside that inline operators will
            # not work for statements that span multiple lines (Matrix or
            # Indexed expressions).
            ecpairs = ["((%s) ? (\n%s\n)\n" % (self._print(c),
                                               self._print(e))
                    for e, c in expr.args[:-1]]
            last_line = ": (\n%s\n)" % self._print(expr.args[-1].expr)
            return ": ".join(ecpairs) + last_line + " ".join([")"*len(ecpairs)])

    def _print_Idx(self, expr):
        return self._print(expr.label)

    def _print_Indexed(self, expr):
        # calculate index for 1d array
        dims = expr.shape
        elem = S.Zero
        offset = S.One
        for i in reversed(range(expr.rank)):
            elem += expr.indices[i]*offset
            offset *= dims[i]
        return "%s[%s]" % (self._print(expr.base.label),
                           self._print(elem))

    def _print_Pow(self, expr):
        PREC = precedence(expr)
        if expr.exp == -1:
            return '1.0/%s' % (self.parenthesize(expr.base, PREC))
        elif expr.exp == 0.5:
            return 'sqrt(%s)' % self._print(expr.base)
        else:
            try:
                e = self._print(float(expr.exp))
            except TypeError:
                e = self._print(expr.exp)
            # return self.known_functions['pow']+'(%s, %s)' % (self._print(expr.base),e)
            return self._print_Function_with_args('pow', (
                self._print(expr.base),
                e
            ))

    def _print_int(self, expr):
        return str(float(expr))

    def _print_Rational(self, expr):
        return "%s.0/%s.0" % (expr.p, expr.q)

    def _print_Add(self, expr, order=None):
        if self._settings['use_operators']:
            return CodePrinter._print_Add(self, expr, order=order)

        terms = expr.as_ordered_terms()

        def partition(p,l):
            return reduce(lambda x, y: (x[0]+[y], x[1]) if p(y) else (x[0], x[1]+[y]), l,  ([], []))
        def add(a,b):
            return self._print_Function_with_args('add', (a, b))
            # return self.known_functions['add']+'(%s, %s)' % (a,b)
        neg, pos = partition(lambda arg: _coeff_isneg(arg), terms)
        s = pos = reduce(lambda a,b: add(a,b), map(lambda t: self._print(t),pos))
        if neg:
            # sum the absolute values of the negative terms
            neg = reduce(lambda a,b: add(a,b), map(lambda n: self._print(-n),neg))
            # then subtract them from the positive terms
            s = self._print_Function_with_args('sub', (pos,neg))
            # s = self.known_functions['sub']+'(%s, %s)' % (pos,neg)
        return s

    def _print_Mul(self, expr, **kwargs):
        if self._settings['use_operators']:
            return CodePrinter._print_Mul(self, expr, **kwargs)
        terms = expr.as_ordered_factors()
        def mul(a,b):
            # return self.known_functions['mul']+'(%s, %s)' % (a,b)
            return self._print_Function_with_args('mul', (a,b))

        s = reduce(lambda a,b: mul(a,b), map(lambda t: self._print(t), terms))
        return s

def glsl_code(expr,assign_to=None,**settings):
    """Converts an expr to a string of GLSL code

    Parameters
    ==========

    expr : Expr
        A sympy expression to be converted.
    assign_to : optional
        When given, the argument is used as the name of the variable to which
        the expression is assigned. Can be a string, ``Symbol``,
        ``MatrixSymbol``, or ``Indexed`` type. This is helpful in case of
        line-wrapping, or for expressions that generate multi-line statements.
    use_operators: bool, optional
        If set to False, then *,/,+,- operators will be replaced with functions
        mul, add, and sub, which must be implemented by the user, e.g. for
        implementing non-standard rings or emulated quad/octal precision.
        [default=True]
    glsl_types: bool, optional
        Set this argument to ``False`` in order to avoid using the ``vec`` and ``mat``
        types.  The printer will instead use arrays (or nested arrays).
        [default=True]
    mat_nested: bool, optional
        GLSL version 4.3 and above support nested arrays (arrays of arrays).  Set this to ``True``
        to render matrices as nested arrays.
        [default=False]
    mat_separator: str, optional
        By default, matrices are rendered with newlines using this separator,
        making them easier to read, but less compact.  By removing the newline
        this option can be used to make them more vertically compact.
        [default=',\n']
    mat_transpose: bool, optional
        GLSL's matrix multiplication implementation assumes column-major indexing.
        By default, this printer ignores that convention. Setting this option to
        ``True`` transposes all matrix output.
        [default=False]
    precision : integer, optional
        The precision for numbers such as pi [default=15].
    user_functions : dict, optional
        A dictionary where keys are ``FunctionClass`` instances and values are
        their string representations. Alternatively, the dictionary value can
        be a list of tuples i.e. [(argument_test, js_function_string)]. See
        below for examples.
    human : bool, optional
        If True, the result is a single string that may contain some constant
        declarations for the number symbols. If False, the same information is
        returned in a tuple of (symbols_to_declare, not_supported_functions,
        code_text). [default=True].
    contract: bool, optional
        If True, ``Indexed`` instances are assumed to obey tensor contraction
        rules and the corresponding nested loops over indices are generated.
        Setting contract=False will not generate loops, instead the user is
        responsible to provide values for the indices in the code.
        [default=True].

    Examples
    ========

    >>> from sympy import glsl_code, symbols, Rational, sin, ceiling, Abs
    >>> x, tau = symbols("x, tau")
    >>> glsl_code((2*tau)**Rational(7, 2))
    '8*sqrt(2)*pow(tau, 3.5)'
    >>> glsl_code(sin(x), assign_to="float y")
    'float y = sin(x);'

    Various GLSL types are supported:
    >>> from sympy import Matrix, glsl_code
    >>> glsl_code(Matrix([1,2,3]))
    'vec3(1, 2, 3)'

    >>> glsl_code(Matrix([[1, 2],[3, 4]]))
    'mat2(1, 2, 3, 4)'

    Pass ``mat_transpose = True`` to switch to column-major indexing:
    >>> glsl_code(Matrix([[1, 2],[3, 4]]), mat_transpose = True)
    'mat2(1, 3, 2, 4)'

    By default, larger matrices get collapsed into float arrays:
    >>> print(glsl_code( Matrix([[1,2,3,4,5],[6,7,8,9,10]]) ))
    float[10](
       1, 2, 3, 4,  5,
       6, 7, 8, 9, 10
    ) /* a 2x5 matrix */

    Passing ``mat_nested = True`` instead prints out nested float arrays, which are
    supported in GLSL 4.3 and above.
    >>> mat = Matrix([
    ... [ 0,  1,  2],
    ... [ 3,  4,  5],
    ... [ 6,  7,  8],
    ... [ 9, 10, 11],
    ... [12, 13, 14]])
    >>> print(glsl_code( mat, mat_nested = True ))
    float[5][3](
       float[]( 0,  1,  2),
       float[]( 3,  4,  5),
       float[]( 6,  7,  8),
       float[]( 9, 10, 11),
       float[](12, 13, 14)
    )



    Custom printing can be defined for certain types by passing a dictionary of
    "type" : "function" to the ``user_functions`` kwarg. Alternatively, the
    dictionary value can be a list of tuples i.e. [(argument_test,
    js_function_string)].

    >>> custom_functions = {
    ...   "ceiling": "CEIL",
    ...   "Abs": [(lambda x: not x.is_integer, "fabs"),
    ...           (lambda x: x.is_integer, "ABS")]
    ... }
    >>> glsl_code(Abs(x) + ceiling(x), user_functions=custom_functions)
    'fabs(x) + CEIL(x)'

    If further control is needed, addition, subtraction, multiplication and
    division operators can be replaced with ``add``, ``sub``, and ``mul``
    functions.  This is done by passing ``use_operators = False``:

    >>> x,y,z = symbols('x,y,z')
    >>> glsl_code(x*(y+z), use_operators = False)
    'mul(x, add(y, z))'
    >>> glsl_code(x*(y+z*(x-y)**z), use_operators = False)
    'mul(x, add(y, mul(z, pow(sub(x, y), z))))'

    ``Piecewise`` expressions are converted into conditionals. If an
    ``assign_to`` variable is provided an if statement is created, otherwise
    the ternary operator is used. Note that if the ``Piecewise`` lacks a
    default term, represented by ``(expr, True)`` then an error will be thrown.
    This is to prevent generating an expression that may not evaluate to
    anything.

    >>> from sympy import Piecewise
    >>> expr = Piecewise((x + 1, x > 0), (x, True))
    >>> print(glsl_code(expr, tau))
    if (x > 0) {
       tau = x + 1;
    }
    else {
       tau = x;
    }

    Support for loops is provided through ``Indexed`` types. With
    ``contract=True`` these expressions will be turned into loops, whereas
    ``contract=False`` will just print the assignment expression that should be
    looped over:

    >>> from sympy import Eq, IndexedBase, Idx
    >>> len_y = 5
    >>> y = IndexedBase('y', shape=(len_y,))
    >>> t = IndexedBase('t', shape=(len_y,))
    >>> Dy = IndexedBase('Dy', shape=(len_y-1,))
    >>> i = Idx('i', len_y-1)
    >>> e=Eq(Dy[i], (y[i+1]-y[i])/(t[i+1]-t[i]))
    >>> glsl_code(e.rhs, assign_to=e.lhs, contract=False)
    'Dy[i] = (y[i + 1] - y[i])/(t[i + 1] - t[i]);'

    >>> from sympy import Matrix, MatrixSymbol
    >>> mat = Matrix([x**2, Piecewise((x + 1, x > 0), (x, True)), sin(x)])
    >>> A = MatrixSymbol('A', 3, 1)
    >>> print(glsl_code(mat, A))
    A[0][0] = pow(x, 2.0);
    if (x > 0) {
       A[1][0] = x + 1;
    }
    else {
       A[1][0] = x;
    }
    A[2][0] = sin(x);
    """
    return GLSLPrinter(settings).doprint(expr,assign_to)

def print_glsl(expr, **settings):
    """Prints the GLSL representation of the given expression.

       See GLSLPrinter init function for settings.
    """
    print(glsl_code(expr, **settings))
