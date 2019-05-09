"""
C code printer

The C89CodePrinter & C99CodePrinter converts single sympy expressions into
single C expressions, using the functions defined in math.h where possible.

A complete code generator, which uses ccode extensively, can be found in
sympy.utilities.codegen. The codegen module can be used to generate complete
source code files that are compilable without further modifications.


"""

from __future__ import print_function, division

from functools import wraps
from itertools import chain

from sympy.core import S
from sympy.core.compatibility import string_types, range
from sympy.core.decorators import deprecated
from sympy.codegen.ast import (
    Assignment, Pointer, Variable, Declaration,
    real, complex_, integer, bool_, float32, float64, float80,
    complex64, complex128, intc, value_const, pointer_const,
    int8, int16, int32, int64, uint8, uint16, uint32, uint64, untyped
)
from sympy.printing.codeprinter import CodePrinter, requires
from sympy.printing.precedence import precedence, PRECEDENCE
from sympy.sets.fancysets import Range

# dictionary mapping sympy function to (argument_conditions, C_function).
# Used in C89CodePrinter._print_Function(self)
known_functions_C89 = {
    "Abs": [(lambda x: not x.is_integer, "fabs"), (lambda x: x.is_integer, "abs")],
    "sin": "sin",
    "cos": "cos",
    "tan": "tan",
    "asin": "asin",
    "acos": "acos",
    "atan": "atan",
    "atan2": "atan2",
    "exp": "exp",
    "log": "log",
    "sinh": "sinh",
    "cosh": "cosh",
    "tanh": "tanh",
    "floor": "floor",
    "ceiling": "ceil",
}

# move to C99 once CCodePrinter is removed:
_known_functions_C9X = dict(known_functions_C89, **{
    "asinh": "asinh",
    "acosh": "acosh",
    "atanh": "atanh",
    "erf": "erf",
    "gamma": "tgamma",
})
known_functions = _known_functions_C9X

known_functions_C99 = dict(_known_functions_C9X, **{
    'exp2': 'exp2',
    'expm1': 'expm1',
    'expm1': 'expm1',
    'log10': 'log10',
    'log2': 'log2',
    'log1p': 'log1p',
    'Cbrt': 'cbrt',
    'hypot': 'hypot',
    'fma': 'fma',
    'loggamma': 'lgamma',
    'erfc': 'erfc',
    'Max': 'fmax',
    'Min': 'fmin'
})

# These are the core reserved words in the C language. Taken from:
# http://en.cppreference.com/w/c/keyword

reserved_words = [
    'auto', 'break', 'case', 'char', 'const', 'continue', 'default', 'do',
    'double', 'else', 'enum', 'extern', 'float', 'for', 'goto', 'if', 'int',
    'long', 'register', 'return', 'short', 'signed', 'sizeof', 'static',
    'struct', 'entry',  # never standardized, we'll leave it here anyway
    'switch', 'typedef', 'union', 'unsigned', 'void', 'volatile', 'while'
]

reserved_words_c99 = ['inline', 'restrict']

def get_math_macros():
    """ Returns a dictionary with math-related macros from math.h/cmath

    Note that these macros are not strictly required by the C/C++-standard.
    For MSVC they are enabled by defining "_USE_MATH_DEFINES" (preferably
    via a compilation flag).

    Returns
    =======

    Dictionary mapping sympy expressions to strings (macro names)

    """
    from sympy.codegen.cfunctions import log2, Sqrt
    from sympy.functions.elementary.exponential import log
    from sympy.functions.elementary.miscellaneous import sqrt

    return {
        S.Exp1: 'M_E',
        log2(S.Exp1): 'M_LOG2E',
        1/log(2): 'M_LOG2E',
        log(2): 'M_LN2',
        log(10): 'M_LN10',
        S.Pi: 'M_PI',
        S.Pi/2: 'M_PI_2',
        S.Pi/4: 'M_PI_4',
        1/S.Pi: 'M_1_PI',
        2/S.Pi: 'M_2_PI',
        2/sqrt(S.Pi): 'M_2_SQRTPI',
        2/Sqrt(S.Pi): 'M_2_SQRTPI',
        sqrt(2): 'M_SQRT2',
        Sqrt(2): 'M_SQRT2',
        1/sqrt(2): 'M_SQRT1_2',
        1/Sqrt(2): 'M_SQRT1_2'
    }


def _as_macro_if_defined(meth):
    """ Decorator for printer methods

    When a Printer's method is decorated using this decorator the expressions printed
    will first be looked for in the attribute ``math_macros``, and if present it will
    print the macro name in ``math_macros`` followed by a type suffix for the type
    ``real``. e.g. printing ``sympy.pi`` would print ``M_PIl`` if real is mapped to float80.

    """
    @wraps(meth)
    def _meth_wrapper(self, expr, **kwargs):
        if expr in self.math_macros:
            return '%s%s' % (self.math_macros[expr], self._get_math_macro_suffix(real))
        else:
            return meth(self, expr, **kwargs)

    return _meth_wrapper


class C89CodePrinter(CodePrinter):
    """A printer to convert python expressions to strings of c code"""
    printmethod = "_ccode"
    language = "C"
    standard = "C89"
    reserved_words = set(reserved_words)

    _default_settings = {
        'order': None,
        'full_prec': 'auto',
        'precision': 17,
        'user_functions': {},
        'human': True,
        'allow_unknown_functions': False,
        'contract': True,
        'dereference': set(),
        'error_on_reserved': False,
        'reserved_word_suffix': '_',
    }

    type_aliases = {
        real: float64,
        complex_: complex128,
        integer: intc
    }

    type_mappings = {
        real: 'double',
        intc: 'int',
        float32: 'float',
        float64: 'double',
        integer: 'int',
        bool_: 'bool',
        int8: 'int8_t',
        int16: 'int16_t',
        int32: 'int32_t',
        int64: 'int64_t',
        uint8: 'int8_t',
        uint16: 'int16_t',
        uint32: 'int32_t',
        uint64: 'int64_t',
    }

    type_headers = {
        bool_: {'stdbool.h'},
        int8: {'stdint.h'},
        int16: {'stdint.h'},
        int32: {'stdint.h'},
        int64: {'stdint.h'},
        uint8: {'stdint.h'},
        uint16: {'stdint.h'},
        uint32: {'stdint.h'},
        uint64: {'stdint.h'},
    }
    type_macros = {}  # Macros needed to be defined when using a Type

    type_func_suffixes = {
        float32: 'f',
        float64: '',
        float80: 'l'
    }

    type_literal_suffixes = {
        float32: 'F',
        float64: '',
        float80: 'L'
    }

    type_math_macro_suffixes = {
        float80: 'l'
    }

    math_macros = None

    _ns = ''  # namespace, C++ uses 'std::'
    _kf = known_functions_C89  # known_functions-dict to copy

    def __init__(self, settings={}):
        if self.math_macros is None:
            self.math_macros = settings.pop('math_macros', get_math_macros())
        self.type_aliases = dict(chain(self.type_aliases.items(),
                                       settings.pop('type_aliases', {}).items()))
        self.type_mappings = dict(chain(self.type_mappings.items(),
                                        settings.pop('type_mappings', {}).items()))
        self.type_headers = dict(chain(self.type_headers.items(),
                                       settings.pop('type_headers', {}).items()))
        self.type_macros = dict(chain(self.type_macros.items(),
                                       settings.pop('type_macros', {}).items()))
        self.type_func_suffixes = dict(chain(self.type_func_suffixes.items(),
                                        settings.pop('type_func_suffixes', {}).items()))
        self.type_literal_suffixes = dict(chain(self.type_literal_suffixes.items(),
                                        settings.pop('type_literal_suffixes', {}).items()))
        self.type_math_macro_suffixes = dict(chain(self.type_math_macro_suffixes.items(),
                                        settings.pop('type_math_macro_suffixes', {}).items()))
        super(C89CodePrinter, self).__init__(settings)
        self.known_functions = dict(self._kf, **settings.get('user_functions', {}))
        self._dereference = set(settings.get('dereference', []))
        self.headers = set()
        self.libraries = set()
        self.macros = set()

    def _rate_index_position(self, p):
        return p*5

    def _get_statement(self, codestring):
        """ Get code string as a statement - i.e. ending with a semicolon. """
        return codestring if codestring.endswith(';') else codestring + ';'

    def _get_comment(self, text):
        return "// {0}".format(text)

    def _declare_number_const(self, name, value):
        type_ = self.type_aliases[real]
        var = Variable(name, type=type_, value=value.evalf(type_.decimal_dig), attrs={value_const})
        decl = Declaration(var)
        return self._get_statement(self._print(decl))

    def _format_code(self, lines):
        return self.indent_code(lines)

    def _traverse_matrix_indices(self, mat):
        rows, cols = mat.shape
        return ((i, j) for i in range(rows) for j in range(cols))

    @_as_macro_if_defined
    def _print_Mul(self, expr, **kwargs):
        return super(C89CodePrinter, self)._print_Mul(expr, **kwargs)

    @_as_macro_if_defined
    def _print_Pow(self, expr):
        if "Pow" in self.known_functions:
            return self._print_Function(expr)
        PREC = precedence(expr)
        suffix = self._get_func_suffix(real)
        if expr.exp == -1:
            return '1.0%s/%s' % (suffix.upper(), self.parenthesize(expr.base, PREC))
        elif expr.exp == 0.5:
            return '%ssqrt%s(%s)' % (self._ns, suffix, self._print(expr.base))
        elif expr.exp == S.One/3 and self.standard != 'C89':
            return '%scbrt%s(%s)' % (self._ns, suffix, self._print(expr.base))
        else:
            return '%spow%s(%s, %s)' % (self._ns, suffix, self._print(expr.base),
                                   self._print(expr.exp))

    def _print_Mod(self, expr):
        num, den = expr.args
        if num.is_integer and den.is_integer:
            return "(({}) % ({}))".format(self._print(num), self._print(den))
        else:
            return self._print_math_func(expr, known='fmod')

    def _print_Rational(self, expr):
        p, q = int(expr.p), int(expr.q)
        suffix = self._get_literal_suffix(real)
        return '%d.0%s/%d.0%s' % (p, suffix, q, suffix)

    def _print_Indexed(self, expr):
        # calculate index for 1d array
        offset = getattr(expr.base, 'offset', S.Zero)
        strides = getattr(expr.base, 'strides', None)
        indices = expr.indices

        if strides is None or isinstance(strides, string_types):
            dims = expr.shape
            shift = S.One
            temp = tuple()
            if strides == 'C' or strides is None:
                traversal = reversed(range(expr.rank))
                indices = indices[::-1]
            elif strides == 'F':
                traversal = range(expr.rank)

            for i in traversal:
                temp += (shift,)
                shift *= dims[i]
            strides = temp
        flat_index = sum([x[0]*x[1] for x in zip(indices, strides)]) + offset
        return "%s[%s]" % (self._print(expr.base.label),
                           self._print(flat_index))

    def _print_Idx(self, expr):
        return self._print(expr.label)

    @_as_macro_if_defined
    def _print_NumberSymbol(self, expr):
        return super(C89CodePrinter, self)._print_NumberSymbol(expr)

    def _print_Infinity(self, expr):
        return 'HUGE_VAL'

    def _print_NegativeInfinity(self, expr):
        return '-HUGE_VAL'

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

    def _print_ITE(self, expr):
        from sympy.functions import Piecewise
        _piecewise = Piecewise((expr.args[1], expr.args[0]), (expr.args[2], True))
        return self._print(_piecewise)

    def _print_MatrixElement(self, expr):
        return "{0}[{1}]".format(self.parenthesize(expr.parent, PRECEDENCE["Atom"],
            strict=True), expr.j + expr.i*expr.parent.shape[1])

    def _print_Symbol(self, expr):
        name = super(C89CodePrinter, self)._print_Symbol(expr)
        if expr in self._settings['dereference']:
            return '(*{0})'.format(name)
        else:
            return name

    def _print_Relational(self, expr):
        lhs_code = self._print(expr.lhs)
        rhs_code = self._print(expr.rhs)
        op = expr.rel_op
        return ("{0} {1} {2}").format(lhs_code, op, rhs_code)

    def _print_sinc(self, expr):
        from sympy.functions.elementary.trigonometric import sin
        from sympy.core.relational import Ne
        from sympy.functions import Piecewise
        _piecewise = Piecewise(
            (sin(expr.args[0]) / expr.args[0], Ne(expr.args[0], 0)), (1, True))
        return self._print(_piecewise)

    def _print_For(self, expr):
        target = self._print(expr.target)
        if isinstance(expr.iterable, Range):
            start, stop, step = expr.iterable.args
        else:
            raise NotImplementedError("Only iterable currently supported is Range")
        body = self._print(expr.body)
        return ('for ({target} = {start}; {target} < {stop}; {target} += '
                '{step}) {{\n{body}\n}}').format(target=target, start=start,
                stop=stop, step=step, body=body)

    def _print_sign(self, func):
        return '((({0}) > 0) - (({0}) < 0))'.format(self._print(func.args[0]))

    def _print_Max(self, expr):
        if "Max" in self.known_functions:
            return self._print_Function(expr)
        def inner_print_max(args): # The more natural abstraction of creating
            if len(args) == 1:     # and printing smaller Max objects is slow
                return self._print(args[0]) # when there are many arguments.
            half = len(args) // 2
            return "((%(a)s > %(b)s) ? %(a)s : %(b)s)" % {
                'a': inner_print_max(args[:half]),
                'b': inner_print_max(args[half:])
            }
        return inner_print_max(expr.args)

    def _print_Min(self, expr):
        if "Min" in self.known_functions:
            return self._print_Function(expr)
        def inner_print_min(args): # The more natural abstraction of creating
            if len(args) == 1:     # and printing smaller Min objects is slow
                return self._print(args[0]) # when there are many arguments.
            half = len(args) // 2
            return "((%(a)s < %(b)s) ? %(a)s : %(b)s)" % {
                'a': inner_print_min(args[:half]),
                'b': inner_print_min(args[half:])
            }
        return inner_print_min(expr.args)

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

    def _get_func_suffix(self, type_):
        return self.type_func_suffixes[self.type_aliases.get(type_, type_)]

    def _get_literal_suffix(self, type_):
        return self.type_literal_suffixes[self.type_aliases.get(type_, type_)]

    def _get_math_macro_suffix(self, type_):
        alias = self.type_aliases.get(type_, type_)
        dflt = self.type_math_macro_suffixes.get(alias, '')
        return self.type_math_macro_suffixes.get(type_, dflt)

    def _print_Type(self, type_):
        self.headers.update(self.type_headers.get(type_, set()))
        self.macros.update(self.type_macros.get(type_, set()))
        return self._print(self.type_mappings.get(type_, type_.name))

    def _print_Declaration(self, decl):
        from sympy.codegen.cnodes import restrict
        var = decl.variable
        val = var.value
        if var.type == untyped:
            raise ValueError("C does not support untyped variables")

        if isinstance(var, Pointer):
            result = '{vc}{t} *{pc} {r}{s}'.format(
                vc='const ' if value_const in var.attrs else '',
                t=self._print(var.type),
                pc=' const' if pointer_const in var.attrs else '',
                r='restrict ' if restrict in var.attrs else '',
                s=self._print(var.symbol)
            )
        elif isinstance(var, Variable):
            result = '{vc}{t} {s}'.format(
                vc='const ' if value_const in var.attrs else '',
                t=self._print(var.type),
                s=self._print(var.symbol)
            )
        else:
            raise NotImplementedError("Unknown type of var: %s" % type(var))
        if val != None: # Must be "!= None", cannot be "is not None"
            result += ' = %s' % self._print(val)
        return result

    def _print_Float(self, flt):
        type_ = self.type_aliases.get(real, real)
        self.macros.update(self.type_macros.get(type_, set()))
        suffix = self._get_literal_suffix(type_)
        num = str(flt.evalf(type_.decimal_dig))
        if 'e' not in num and '.' not in num:
            num += '.0'
        num_parts = num.split('e')
        num_parts[0] = num_parts[0].rstrip('0')
        if num_parts[0].endswith('.'):
            num_parts[0] += '0'
        return 'e'.join(num_parts) + suffix

    @requires(headers={'stdbool.h'})
    def _print_BooleanTrue(self, expr):
        return 'true'

    @requires(headers={'stdbool.h'})
    def _print_BooleanFalse(self, expr):
        return 'false'

    def _print_Element(self, elem):
        if elem.strides == None: # Must be "== None", cannot be "is None"
            if elem.offset != None: # Must be "!= None", cannot be "is not None"
                raise ValueError("Expected strides when offset is given")
            idxs = ']['.join(map(lambda arg: self._print(arg),
                                 elem.indices))
        else:
            global_idx = sum([i*s for i, s in zip(elem.indices, elem.strides)])
            if elem.offset != None: # Must be "!= None", cannot be "is not None"
                global_idx += elem.offset
            idxs = self._print(global_idx)

        return "{symb}[{idxs}]".format(
            symb=self._print(elem.symbol),
            idxs=idxs
        )

    def _print_CodeBlock(self, expr):
        """ Elements of code blocks printed as statements. """
        return '\n'.join([self._get_statement(self._print(i)) for i in expr.args])

    def _print_While(self, expr):
        return 'while ({condition}) {{\n{body}\n}}'.format(**expr.kwargs(
            apply=lambda arg: self._print(arg)))

    def _print_Scope(self, expr):
        return '{\n%s\n}' % self._print_CodeBlock(expr.body)

    @requires(headers={'stdio.h'})
    def _print_Print(self, expr):
        return 'printf({fmt}, {pargs})'.format(
            fmt=self._print(expr.format_string),
            pargs=', '.join(map(lambda arg: self._print(arg), expr.print_args))
        )

    def _print_FunctionPrototype(self, expr):
        pars = ', '.join(map(lambda arg: self._print(Declaration(arg)),
                             expr.parameters))
        return "%s %s(%s)" % (
            tuple(map(lambda arg: self._print(arg),
                      (expr.return_type, expr.name))) + (pars,)
        )

    def _print_FunctionDefinition(self, expr):
        return "%s%s" % (self._print_FunctionPrototype(expr),
                         self._print_Scope(expr))

    def _print_Return(self, expr):
        arg, = expr.args
        return 'return %s' % self._print(arg)

    def _print_CommaOperator(self, expr):
        return '(%s)' % ', '.join(map(lambda arg: self._print(arg), expr.args))

    def _print_Label(self, expr):
        return '%s:' % str(expr)

    def _print_goto(self, expr):
        return 'goto %s' % expr.label

    def _print_PreIncrement(self, expr):
        arg, = expr.args
        return '++(%s)' % self._print(arg)

    def _print_PostIncrement(self, expr):
        arg, = expr.args
        return '(%s)++' % self._print(arg)

    def _print_PreDecrement(self, expr):
        arg, = expr.args
        return '--(%s)' % self._print(arg)

    def _print_PostDecrement(self, expr):
        arg, = expr.args
        return '(%s)--' % self._print(arg)

    def _print_struct(self, expr):
        return "%(keyword)s %(name)s {\n%(lines)s}" % dict(
            keyword=expr.__class__.__name__, name=expr.name, lines=';\n'.join(
                [self._print(decl) for decl in expr.declarations] + [''])
        )

    def _print_BreakToken(self, _):
        return 'break'

    def _print_ContinueToken(self, _):
        return 'continue'

    _print_union = _print_struct



class _C9XCodePrinter(object):
    # Move these methods to C99CodePrinter when removing CCodePrinter
    def _get_loop_opening_ending(self, indices):
        open_lines = []
        close_lines = []
        loopstart = "for (int %(var)s=%(start)s; %(var)s<%(end)s; %(var)s++){"  # C99
        for i in indices:
            # C arrays start at 0 and end at dimension-1
            open_lines.append(loopstart % {
                'var': self._print(i.label),
                'start': self._print(i.lower),
                'end': self._print(i.upper + 1)})
            close_lines.append("}")
        return open_lines, close_lines


@deprecated(
    last_supported_version='1.0',
    useinstead="C89CodePrinter or C99CodePrinter, e.g. ccode(..., standard='C99')",
    issue=12220,
    deprecated_since_version='1.1')
class CCodePrinter(_C9XCodePrinter, C89CodePrinter):
    """
    Deprecated.

    Alias for C89CodePrinter, for backwards compatibility.
    """
    _kf = _known_functions_C9X  # known_functions-dict to copy


class C99CodePrinter(_C9XCodePrinter, C89CodePrinter):
    standard = 'C99'
    reserved_words = set(reserved_words + reserved_words_c99)
    type_mappings=dict(chain(C89CodePrinter.type_mappings.items(), {
        complex64: 'float complex',
        complex128: 'double complex',
    }.items()))
    type_headers = dict(chain(C89CodePrinter.type_headers.items(), {
        complex64: {'complex.h'},
        complex128: {'complex.h'}
    }.items()))
    _kf = known_functions_C99  # known_functions-dict to copy

    # functions with versions with 'f' and 'l' suffixes:
    _prec_funcs = ('fabs fmod remainder remquo fma fmax fmin fdim nan exp exp2'
                   ' expm1 log log10 log2 log1p pow sqrt cbrt hypot sin cos tan'
                   ' asin acos atan atan2 sinh cosh tanh asinh acosh atanh erf'
                   ' erfc tgamma lgamma ceil floor trunc round nearbyint rint'
                   ' frexp ldexp modf scalbn ilogb logb nextafter copysign').split()

    def _print_Infinity(self, expr):
        return 'INFINITY'

    def _print_NegativeInfinity(self, expr):
        return '-INFINITY'

    def _print_NaN(self, expr):
        return 'NAN'

    # tgamma was already covered by 'known_functions' dict

    @requires(headers={'math.h'}, libraries={'m'})
    @_as_macro_if_defined
    def _print_math_func(self, expr, nest=False, known=None):
        if known is None:
            known = self.known_functions[expr.__class__.__name__]
        if not isinstance(known, string_types):
            for cb, name in known:
                if cb(*expr.args):
                    known = name
                    break
            else:
                raise ValueError("No matching printer")
        try:
            return known(self, *expr.args)
        except TypeError:
            suffix = self._get_func_suffix(real) if self._ns + known in self._prec_funcs else ''

        if nest:
            args = self._print(expr.args[0])
            if len(expr.args) > 1:
                paren_pile = ''
                for curr_arg in expr.args[1:-1]:
                    paren_pile += ')'
                    args += ', {ns}{name}{suffix}({next}'.format(
                        ns=self._ns,
                        name=known,
                        suffix=suffix,
                        next = self._print(curr_arg)
                    )
                args += ', %s%s' % (
                    self._print(expr.func(expr.args[-1])),
                    paren_pile
                )
        else:
            args = ', '.join(map(lambda arg: self._print(arg), expr.args))
        return '{ns}{name}{suffix}({args})'.format(
            ns=self._ns,
            name=known,
            suffix=suffix,
            args=args
        )

    def _print_Max(self, expr):
        return self._print_math_func(expr, nest=True)

    def _print_Min(self, expr):
        return self._print_math_func(expr, nest=True)


for k in ('Abs Sqrt exp exp2 expm1 log log10 log2 log1p Cbrt hypot fma'
          ' loggamma sin cos tan asin acos atan atan2 sinh cosh tanh asinh acosh '
          'atanh erf erfc loggamma gamma ceiling floor').split():
    setattr(C99CodePrinter, '_print_%s' % k, C99CodePrinter._print_math_func)


class C11CodePrinter(C99CodePrinter):

    @requires(headers={'stdalign.h'})
    def _print_alignof(self, expr):
        arg, = expr.args
        return 'alignof(%s)' % self._print(arg)


c_code_printers = {
    'c89': C89CodePrinter,
    'c99': C99CodePrinter,
    'c11': C11CodePrinter
}


def ccode(expr, assign_to=None, standard='c99', **settings):
    """Converts an expr to a string of c code

    Parameters
    ==========

    expr : Expr
        A sympy expression to be converted.
    assign_to : optional
        When given, the argument is used as the name of the variable to which
        the expression is assigned. Can be a string, ``Symbol``,
        ``MatrixSymbol``, or ``Indexed`` type. This is helpful in case of
        line-wrapping, or for expressions that generate multi-line statements.
    standard : str, optional
        String specifying the standard. If your compiler supports a more modern
        standard you may set this to 'c99' to allow the printer to use more math
        functions. [default='c89'].
    precision : integer, optional
        The precision for numbers such as pi [default=17].
    user_functions : dict, optional
        A dictionary where the keys are string representations of either
        ``FunctionClass`` or ``UndefinedFunction`` instances and the values
        are their desired C string representations. Alternatively, the
        dictionary value can be a list of tuples i.e. [(argument_test,
        cfunction_string)] or [(argument_test, cfunction_formater)]. See below
        for examples.
    dereference : iterable, optional
        An iterable of symbols that should be dereferenced in the printed code
        expression. These would be values passed by address to the function.
        For example, if ``dereference=[a]``, the resulting code would print
        ``(*a)`` instead of ``a``.
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

    >>> from sympy import ccode, symbols, Rational, sin, ceiling, Abs, Function
    >>> x, tau = symbols("x, tau")
    >>> expr = (2*tau)**Rational(7, 2)
    >>> ccode(expr)
    '8*M_SQRT2*pow(tau, 7.0/2.0)'
    >>> ccode(expr, math_macros={})
    '8*sqrt(2)*pow(tau, 7.0/2.0)'
    >>> ccode(sin(x), assign_to="s")
    's = sin(x);'
    >>> from sympy.codegen.ast import real, float80
    >>> ccode(expr, type_aliases={real: float80})
    '8*M_SQRT2l*powl(tau, 7.0L/2.0L)'

    Simple custom printing can be defined for certain types by passing a
    dictionary of {"type" : "function"} to the ``user_functions`` kwarg.
    Alternatively, the dictionary value can be a list of tuples i.e.
    [(argument_test, cfunction_string)].

    >>> custom_functions = {
    ...   "ceiling": "CEIL",
    ...   "Abs": [(lambda x: not x.is_integer, "fabs"),
    ...           (lambda x: x.is_integer, "ABS")],
    ...   "func": "f"
    ... }
    >>> func = Function('func')
    >>> ccode(func(Abs(x) + ceiling(x)), standard='C89', user_functions=custom_functions)
    'f(fabs(x) + CEIL(x))'

    or if the C-function takes a subset of the original arguments:

    >>> ccode(2**x + 3**x, standard='C99', user_functions={'Pow': [
    ...   (lambda b, e: b == 2, lambda b, e: 'exp2(%s)' % e),
    ...   (lambda b, e: b != 2, 'pow')]})
    'exp2(x) + pow(3, x)'

    ``Piecewise`` expressions are converted into conditionals. If an
    ``assign_to`` variable is provided an if statement is created, otherwise
    the ternary operator is used. Note that if the ``Piecewise`` lacks a
    default term, represented by ``(expr, True)`` then an error will be thrown.
    This is to prevent generating an expression that may not evaluate to
    anything.

    >>> from sympy import Piecewise
    >>> expr = Piecewise((x + 1, x > 0), (x, True))
    >>> print(ccode(expr, tau, standard='C89'))
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
    >>> ccode(e.rhs, assign_to=e.lhs, contract=False, standard='C89')
    'Dy[i] = (y[i + 1] - y[i])/(t[i + 1] - t[i]);'

    Matrices are also supported, but a ``MatrixSymbol`` of the same dimensions
    must be provided to ``assign_to``. Note that any expression that can be
    generated normally can also exist inside a Matrix:

    >>> from sympy import Matrix, MatrixSymbol
    >>> mat = Matrix([x**2, Piecewise((x + 1, x > 0), (x, True)), sin(x)])
    >>> A = MatrixSymbol('A', 3, 1)
    >>> print(ccode(mat, A, standard='C89'))
    A[0] = pow(x, 2);
    if (x > 0) {
       A[1] = x + 1;
    }
    else {
       A[1] = x;
    }
    A[2] = sin(x);
    """
    return c_code_printers[standard.lower()](settings).doprint(expr, assign_to)


def print_ccode(expr, **settings):
    """Prints C representation of the given expression."""
    print(ccode(expr, **settings))
