"""
Handlers for predicates related to set membership: integer, rational, etc.
"""
from __future__ import print_function, division

from sympy.assumptions import Q, ask
from sympy.assumptions.handlers import CommonHandler, test_closed_group
from sympy.core.numbers import pi
from sympy.functions.elementary.exponential import exp, log
from sympy import I


class AskIntegerHandler(CommonHandler):
    """
    Handler for Q.integer
    Test that an expression belongs to the field of integer numbers
    """

    @staticmethod
    def Expr(expr, assumptions):
        return expr.is_integer

    @staticmethod
    def _number(expr, assumptions):
        # helper method
        try:
            i = int(expr.round())
            if not (expr - i).equals(0):
                raise TypeError
            return True
        except TypeError:
            return False

    @staticmethod
    def Add(expr, assumptions):
        """
        Integer + Integer       -> Integer
        Integer + !Integer      -> !Integer
        !Integer + !Integer -> ?
        """
        if expr.is_number:
            return AskIntegerHandler._number(expr, assumptions)
        return test_closed_group(expr, assumptions, Q.integer)

    @staticmethod
    def Mul(expr, assumptions):
        """
        Integer*Integer      -> Integer
        Integer*Irrational   -> !Integer
        Odd/Even             -> !Integer
        Integer*Rational     -> ?
        """
        if expr.is_number:
            return AskIntegerHandler._number(expr, assumptions)
        _output = True
        for arg in expr.args:
            if not ask(Q.integer(arg), assumptions):
                if arg.is_Rational:
                    if arg.q == 2:
                        return ask(Q.even(2*expr), assumptions)
                    if ~(arg.q & 1):
                        return None
                elif ask(Q.irrational(arg), assumptions):
                    if _output:
                        _output = False
                    else:
                        return
                else:
                    return
        else:
            return _output

    Pow = Add

    int, Integer = [staticmethod(CommonHandler.AlwaysTrue)]*2

    Pi, Exp1, GoldenRatio, TribonacciConstant, Infinity, NegativeInfinity, ImaginaryUnit = \
        [staticmethod(CommonHandler.AlwaysFalse)]*7

    @staticmethod
    def Rational(expr, assumptions):
        # rationals with denominator one get
        # evaluated to Integers
        return False

    @staticmethod
    def Abs(expr, assumptions):
        return ask(Q.integer(expr.args[0]), assumptions)

    @staticmethod
    def MatrixElement(expr, assumptions):
        return ask(Q.integer_elements(expr.args[0]), assumptions)

    Determinant = Trace = MatrixElement


class AskRationalHandler(CommonHandler):
    """
    Handler for Q.rational
    Test that an expression belongs to the field of rational numbers
    """


    @staticmethod
    def Expr(expr, assumptions):
        return expr.is_rational

    @staticmethod
    def Add(expr, assumptions):
        """
        Rational + Rational     -> Rational
        Rational + !Rational    -> !Rational
        !Rational + !Rational   -> ?
        """
        if expr.is_number:
            if expr.as_real_imag()[1]:
                return False
        return test_closed_group(expr, assumptions, Q.rational)

    Mul = Add

    @staticmethod
    def Pow(expr, assumptions):
        """
        Rational ** Integer      -> Rational
        Irrational ** Rational   -> Irrational
        Rational ** Irrational   -> ?
        """
        if ask(Q.integer(expr.exp), assumptions):
            return ask(Q.rational(expr.base), assumptions)
        elif ask(Q.rational(expr.exp), assumptions):
            if ask(Q.prime(expr.base), assumptions):
                return False


    Rational = staticmethod(CommonHandler.AlwaysTrue)

    Float = staticmethod(CommonHandler.AlwaysNone)

    ImaginaryUnit, Infinity, NegativeInfinity, Pi, Exp1, GoldenRatio, TribonacciConstant = \
        [staticmethod(CommonHandler.AlwaysFalse)]*7

    @staticmethod
    def exp(expr, assumptions):
        x = expr.args[0]
        if ask(Q.rational(x), assumptions):
            return ask(~Q.nonzero(x), assumptions)

    @staticmethod
    def cot(expr, assumptions):
        x = expr.args[0]
        if ask(Q.rational(x), assumptions):
            return False

    @staticmethod
    def log(expr, assumptions):
        x = expr.args[0]
        if ask(Q.rational(x), assumptions):
            return ask(~Q.nonzero(x - 1), assumptions)

    sin, cos, tan, asin, atan = [exp]*5
    acos, acot = log, cot


class AskIrrationalHandler(CommonHandler):


    @staticmethod
    def Expr(expr, assumptions):
        return expr.is_irrational

    @staticmethod
    def Basic(expr, assumptions):
        _real = ask(Q.real(expr), assumptions)
        if _real:
            _rational = ask(Q.rational(expr), assumptions)
            if _rational is None:
                return None
            return not _rational
        else:
            return _real


class AskRealHandler(CommonHandler):
    """
    Handler for Q.real
    Test that an expression belongs to the field of real numbers
    """

    @staticmethod
    def Expr(expr, assumptions):
        return expr.is_real

    @staticmethod
    def _number(expr, assumptions):
        # let as_real_imag() work first since the expression may
        # be simpler to evaluate
        i = expr.as_real_imag()[1].evalf(2)
        if i._prec != 1:
            return not i
        # allow None to be returned if we couldn't show for sure
        # that i was 0

    @staticmethod
    def Add(expr, assumptions):
        """
        Real + Real              -> Real
        Real + (Complex & !Real) -> !Real
        """
        if expr.is_number:
            return AskRealHandler._number(expr, assumptions)
        return test_closed_group(expr, assumptions, Q.real)

    @staticmethod
    def Mul(expr, assumptions):
        """
        Real*Real               -> Real
        Real*Imaginary          -> !Real
        Imaginary*Imaginary     -> Real
        """
        if expr.is_number:
            return AskRealHandler._number(expr, assumptions)
        result = True
        for arg in expr.args:
            if ask(Q.real(arg), assumptions):
                pass
            elif ask(Q.imaginary(arg), assumptions):
                result = result ^ True
            else:
                break
        else:
            return result

    @staticmethod
    def Pow(expr, assumptions):
        """
        Real**Integer              -> Real
        Positive**Real             -> Real
        Real**(Integer/Even)       -> Real if base is nonnegative
        Real**(Integer/Odd)        -> Real
        Imaginary**(Integer/Even)  -> Real
        Imaginary**(Integer/Odd)   -> not Real
        Imaginary**Real            -> ? since Real could be 0 (giving real) or 1 (giving imaginary)
        b**Imaginary               -> Real if log(b) is imaginary and b != 0 and exponent != integer multiple of I*pi/log(b)
        Real**Real                 -> ? e.g. sqrt(-1) is imaginary and sqrt(2) is not
        """
        if expr.is_number:
            return AskRealHandler._number(expr, assumptions)

        if expr.base.func == exp:
            if ask(Q.imaginary(expr.base.args[0]), assumptions):
                if ask(Q.imaginary(expr.exp), assumptions):
                    return True
            # If the i = (exp's arg)/(I*pi) is an integer or half-integer
            # multiple of I*pi then 2*i will be an integer. In addition,
            # exp(i*I*pi) = (-1)**i so the overall realness of the expr
            # can be determined by replacing exp(i*I*pi) with (-1)**i.
            i = expr.base.args[0]/I/pi
            if ask(Q.integer(2*i), assumptions):
                return ask(Q.real(((-1)**i)**expr.exp), assumptions)
            return

        if ask(Q.imaginary(expr.base), assumptions):
            if ask(Q.integer(expr.exp), assumptions):
                odd = ask(Q.odd(expr.exp), assumptions)
                if odd is not None:
                    return not odd
                return

        if ask(Q.imaginary(expr.exp), assumptions):
            imlog = ask(Q.imaginary(log(expr.base)), assumptions)
            if imlog is not None:
                # I**i -> real, log(I) is imag;
                # (2*I)**i -> complex, log(2*I) is not imag
                return imlog

        if ask(Q.real(expr.base), assumptions):
            if ask(Q.real(expr.exp), assumptions):
                if expr.exp.is_Rational and \
                        ask(Q.even(expr.exp.q), assumptions):
                    return ask(Q.positive(expr.base), assumptions)
                elif ask(Q.integer(expr.exp), assumptions):
                    return True
                elif ask(Q.positive(expr.base), assumptions):
                    return True
                elif ask(Q.negative(expr.base), assumptions):
                    return False

    Rational, Float, Pi, Exp1, GoldenRatio, TribonacciConstant, Abs, re, im = \
        [staticmethod(CommonHandler.AlwaysTrue)]*9

    ImaginaryUnit, Infinity, NegativeInfinity = \
        [staticmethod(CommonHandler.AlwaysFalse)]*3

    @staticmethod
    def sin(expr, assumptions):
        if ask(Q.real(expr.args[0]), assumptions):
            return True

    cos = sin

    @staticmethod
    def exp(expr, assumptions):
        return ask(Q.integer(expr.args[0]/I/pi) | Q.real(expr.args[0]), assumptions)

    @staticmethod
    def log(expr, assumptions):
        return ask(Q.positive(expr.args[0]), assumptions)

    @staticmethod
    def MatrixElement(expr, assumptions):
        return ask(Q.real_elements(expr.args[0]), assumptions)

    Determinant = Trace = MatrixElement


class AskExtendedRealHandler(AskRealHandler):
    """
    Handler for Q.extended_real
    Test that an expression belongs to the field of extended real numbers,
    that is real numbers union {Infinity, -Infinity}
    """

    @staticmethod
    def Add(expr, assumptions):
        return test_closed_group(expr, assumptions, Q.extended_real)

    Mul, Pow = [Add]*2

    Infinity, NegativeInfinity = [staticmethod(CommonHandler.AlwaysTrue)]*2


class AskHermitianHandler(AskRealHandler):
    """
    Handler for Q.hermitian
    Test that an expression belongs to the field of Hermitian operators
    """

    @staticmethod
    def Add(expr, assumptions):
        """
        Hermitian + Hermitian  -> Hermitian
        Hermitian + !Hermitian -> !Hermitian
        """
        if expr.is_number:
            return AskRealHandler._number(expr, assumptions)
        return test_closed_group(expr, assumptions, Q.hermitian)

    @staticmethod
    def Mul(expr, assumptions):
        """
        As long as there is at most only one noncommutative term:
        Hermitian*Hermitian         -> Hermitian
        Hermitian*Antihermitian     -> !Hermitian
        Antihermitian*Antihermitian -> Hermitian
        """
        if expr.is_number:
            return AskRealHandler._number(expr, assumptions)
        nccount = 0
        result = True
        for arg in expr.args:
            if ask(Q.antihermitian(arg), assumptions):
                result = result ^ True
            elif not ask(Q.hermitian(arg), assumptions):
                break
            if ask(~Q.commutative(arg), assumptions):
                nccount += 1
                if nccount > 1:
                    break
        else:
            return result

    @staticmethod
    def Pow(expr, assumptions):
        """
        Hermitian**Integer -> Hermitian
        """
        if expr.is_number:
            return AskRealHandler._number(expr, assumptions)
        if ask(Q.hermitian(expr.base), assumptions):
            if ask(Q.integer(expr.exp), assumptions):
                return True

    @staticmethod
    def sin(expr, assumptions):
        if ask(Q.hermitian(expr.args[0]), assumptions):
            return True

    cos, exp = [sin]*2


class AskComplexHandler(CommonHandler):
    """
    Handler for Q.complex
    Test that an expression belongs to the field of complex numbers
    """

    @staticmethod
    def Expr(expr, assumptions):
        return expr.is_complex

    @staticmethod
    def Add(expr, assumptions):
        return test_closed_group(expr, assumptions, Q.complex)

    Mul, Pow = [Add]*2

    Number, sin, cos, log, exp, re, im, NumberSymbol, Abs, ImaginaryUnit = \
        [staticmethod(CommonHandler.AlwaysTrue)]*10 # they are all complex functions or expressions

    Infinity, NegativeInfinity = [staticmethod(CommonHandler.AlwaysFalse)]*2

    @staticmethod
    def MatrixElement(expr, assumptions):
        return ask(Q.complex_elements(expr.args[0]), assumptions)

    Determinant = Trace = MatrixElement


class AskImaginaryHandler(CommonHandler):
    """
    Handler for Q.imaginary
    Test that an expression belongs to the field of imaginary numbers,
    that is, numbers in the form x*I, where x is real
    """

    @staticmethod
    def Expr(expr, assumptions):
        return expr.is_imaginary

    @staticmethod
    def _number(expr, assumptions):
        # let as_real_imag() work first since the expression may
        # be simpler to evaluate
        r = expr.as_real_imag()[0].evalf(2)
        if r._prec != 1:
            return not r
        # allow None to be returned if we couldn't show for sure
        # that r was 0

    @staticmethod
    def Add(expr, assumptions):
        """
        Imaginary + Imaginary -> Imaginary
        Imaginary + Complex   -> ?
        Imaginary + Real      -> !Imaginary
        """
        if expr.is_number:
            return AskImaginaryHandler._number(expr, assumptions)

        reals = 0
        for arg in expr.args:
            if ask(Q.imaginary(arg), assumptions):
                pass
            elif ask(Q.real(arg), assumptions):
                reals += 1
            else:
                break
        else:
            if reals == 0:
                return True
            if reals == 1 or (len(expr.args) == reals):
                # two reals could sum 0 thus giving an imaginary
                return False

    @staticmethod
    def Mul(expr, assumptions):
        """
        Real*Imaginary      -> Imaginary
        Imaginary*Imaginary -> Real
        """
        if expr.is_number:
            return AskImaginaryHandler._number(expr, assumptions)
        result = False
        reals = 0
        for arg in expr.args:
            if ask(Q.imaginary(arg), assumptions):
                result = result ^ True
            elif not ask(Q.real(arg), assumptions):
                break
        else:
            if reals == len(expr.args):
                return False
            return result

    @staticmethod
    def Pow(expr, assumptions):
        """
        Imaginary**Odd        -> Imaginary
        Imaginary**Even       -> Real
        b**Imaginary          -> !Imaginary if exponent is an integer multiple of I*pi/log(b)
        Imaginary**Real       -> ?
        Positive**Real        -> Real
        Negative**Integer     -> Real
        Negative**(Integer/2) -> Imaginary
        Negative**Real        -> not Imaginary if exponent is not Rational
        """
        if expr.is_number:
            return AskImaginaryHandler._number(expr, assumptions)

        if expr.base.func == exp:
            if ask(Q.imaginary(expr.base.args[0]), assumptions):
                if ask(Q.imaginary(expr.exp), assumptions):
                    return False
                i = expr.base.args[0]/I/pi
                if ask(Q.integer(2*i), assumptions):
                    return ask(Q.imaginary(((-1)**i)**expr.exp), assumptions)

        if ask(Q.imaginary(expr.base), assumptions):
            if ask(Q.integer(expr.exp), assumptions):
                odd = ask(Q.odd(expr.exp), assumptions)
                if odd is not None:
                    return odd
                return

        if ask(Q.imaginary(expr.exp), assumptions):
            imlog = ask(Q.imaginary(log(expr.base)), assumptions)
            if imlog is not None:
                return False  # I**i -> real; (2*I)**i -> complex ==> not imaginary

        if ask(Q.real(expr.base) & Q.real(expr.exp), assumptions):
            if ask(Q.positive(expr.base), assumptions):
                return False
            else:
                rat = ask(Q.rational(expr.exp), assumptions)
                if not rat:
                    return rat
                if ask(Q.integer(expr.exp), assumptions):
                    return False
                else:
                    half = ask(Q.integer(2*expr.exp), assumptions)
                    if half:
                        return ask(Q.negative(expr.base), assumptions)
                    return half


    @staticmethod
    def log(expr, assumptions):
        if ask(Q.real(expr.args[0]), assumptions):
            if ask(Q.positive(expr.args[0]), assumptions):
                return False
            return
        # XXX it should be enough to do
        # return ask(Q.nonpositive(expr.args[0]), assumptions)
        # but ask(Q.nonpositive(exp(x)), Q.imaginary(x)) -> None;
        # it should return True since exp(x) will be either 0 or complex
        if expr.args[0].func == exp:
            if expr.args[0].args[0] in [I, -I]:
                return True
        im = ask(Q.imaginary(expr.args[0]), assumptions)
        if im is False:
            return False

    @staticmethod
    def exp(expr, assumptions):
        a = expr.args[0]/I/pi
        return ask(Q.integer(2*a) & ~Q.integer(a), assumptions)

    @staticmethod
    def Number(expr, assumptions):
        return not (expr.as_real_imag()[1] == 0)

    NumberSymbol = Number

    ImaginaryUnit = staticmethod(CommonHandler.AlwaysTrue)


class AskAntiHermitianHandler(AskImaginaryHandler):
    """
    Handler for Q.antihermitian
    Test that an expression belongs to the field of anti-Hermitian operators,
    that is, operators in the form x*I, where x is Hermitian
    """

    @staticmethod
    def Add(expr, assumptions):
        """
        Antihermitian + Antihermitian  -> Antihermitian
        Antihermitian + !Antihermitian -> !Antihermitian
        """
        if expr.is_number:
            return AskImaginaryHandler._number(expr, assumptions)
        return test_closed_group(expr, assumptions, Q.antihermitian)

    @staticmethod
    def Mul(expr, assumptions):
        """
        As long as there is at most only one noncommutative term:
        Hermitian*Hermitian         -> !Antihermitian
        Hermitian*Antihermitian     -> Antihermitian
        Antihermitian*Antihermitian -> !Antihermitian
        """
        if expr.is_number:
            return AskImaginaryHandler._number(expr, assumptions)
        nccount = 0
        result = False
        for arg in expr.args:
            if ask(Q.antihermitian(arg), assumptions):
                result = result ^ True
            elif not ask(Q.hermitian(arg), assumptions):
                break
            if ask(~Q.commutative(arg), assumptions):
                nccount += 1
                if nccount > 1:
                    break
        else:
            return result

    @staticmethod
    def Pow(expr, assumptions):
        """
        Hermitian**Integer  -> !Antihermitian
        Antihermitian**Even -> !Antihermitian
        Antihermitian**Odd  -> Antihermitian
        """
        if expr.is_number:
            return AskImaginaryHandler._number(expr, assumptions)
        if ask(Q.hermitian(expr.base), assumptions):
            if ask(Q.integer(expr.exp), assumptions):
                return False
        elif ask(Q.antihermitian(expr.base), assumptions):
            if ask(Q.even(expr.exp), assumptions):
                return False
            elif ask(Q.odd(expr.exp), assumptions):
                return True


class AskAlgebraicHandler(CommonHandler):
    """Handler for Q.algebraic key. """

    @staticmethod
    def Add(expr, assumptions):
        return test_closed_group(expr, assumptions, Q.algebraic)

    @staticmethod
    def Mul(expr, assumptions):
        return test_closed_group(expr, assumptions, Q.algebraic)

    @staticmethod
    def Pow(expr, assumptions):
        return expr.exp.is_Rational and ask(
            Q.algebraic(expr.base), assumptions)

    @staticmethod
    def Rational(expr, assumptions):
        return expr.q != 0

    Float, GoldenRatio, TribonacciConstant, ImaginaryUnit, AlgebraicNumber = \
        [staticmethod(CommonHandler.AlwaysTrue)]*5

    Infinity, NegativeInfinity, ComplexInfinity, Pi, Exp1 = \
        [staticmethod(CommonHandler.AlwaysFalse)]*5

    @staticmethod
    def exp(expr, assumptions):
        x = expr.args[0]
        if ask(Q.algebraic(x), assumptions):
            return ask(~Q.nonzero(x), assumptions)

    @staticmethod
    def cot(expr, assumptions):
        x = expr.args[0]
        if ask(Q.algebraic(x), assumptions):
            return False

    @staticmethod
    def log(expr, assumptions):
        x = expr.args[0]
        if ask(Q.algebraic(x), assumptions):
            return ask(~Q.nonzero(x - 1), assumptions)

    sin, cos, tan, asin, atan = [exp]*5
    acos, acot = log, cot
