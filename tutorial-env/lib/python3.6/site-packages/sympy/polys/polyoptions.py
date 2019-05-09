"""Options manager for :class:`Poly` and public API functions. """

from __future__ import print_function, division

__all__ = ["Options"]

from sympy.core import S, Basic, sympify
from sympy.core.compatibility import string_types, with_metaclass
from sympy.polys.polyerrors import GeneratorsError, OptionError, FlagError
from sympy.utilities import numbered_symbols, topological_sort, public
from sympy.utilities.iterables import has_dups

import sympy.polys

import re

class Option(object):
    """Base class for all kinds of options. """

    option = None

    is_Flag = False

    requires = []
    excludes = []

    after = []
    before = []

    @classmethod
    def default(cls):
        return None

    @classmethod
    def preprocess(cls, option):
        return None

    @classmethod
    def postprocess(cls, options):
        pass


class Flag(Option):
    """Base class for all kinds of flags. """

    is_Flag = True


class BooleanOption(Option):
    """An option that must have a boolean value or equivalent assigned. """

    @classmethod
    def preprocess(cls, value):
        if value in [True, False]:
            return bool(value)
        else:
            raise OptionError("'%s' must have a boolean value assigned, got %s" % (cls.option, value))


class OptionType(type):
    """Base type for all options that does registers options. """

    def __init__(cls, *args, **kwargs):
        @property
        def getter(self):
            try:
                return self[cls.option]
            except KeyError:
                return cls.default()

        setattr(Options, cls.option, getter)
        Options.__options__[cls.option] = cls


@public
class Options(dict):
    """
    Options manager for polynomial manipulation module.

    Examples
    ========

    >>> from sympy.polys.polyoptions import Options
    >>> from sympy.polys.polyoptions import build_options

    >>> from sympy.abc import x, y, z

    >>> Options((x, y, z), {'domain': 'ZZ'})
    {'auto': False, 'domain': ZZ, 'gens': (x, y, z)}

    >>> build_options((x, y, z), {'domain': 'ZZ'})
    {'auto': False, 'domain': ZZ, 'gens': (x, y, z)}

    **Options**

    * Expand --- boolean option
    * Gens --- option
    * Wrt --- option
    * Sort --- option
    * Order --- option
    * Field --- boolean option
    * Greedy --- boolean option
    * Domain --- option
    * Split --- boolean option
    * Gaussian --- boolean option
    * Extension --- option
    * Modulus --- option
    * Symmetric --- boolean option
    * Strict --- boolean option

    **Flags**

    * Auto --- boolean flag
    * Frac --- boolean flag
    * Formal --- boolean flag
    * Polys --- boolean flag
    * Include --- boolean flag
    * All --- boolean flag
    * Gen --- flag
    * Series --- boolean flag

    """

    __order__ = None
    __options__ = {}

    def __init__(self, gens, args, flags=None, strict=False):
        dict.__init__(self)

        if gens and args.get('gens', ()):
            raise OptionError(
                "both '*gens' and keyword argument 'gens' supplied")
        elif gens:
            args = dict(args)
            args['gens'] = gens

        defaults = args.pop('defaults', {})

        def preprocess_options(args):
            for option, value in args.items():
                try:
                    cls = self.__options__[option]
                except KeyError:
                    raise OptionError("'%s' is not a valid option" % option)

                if issubclass(cls, Flag):
                    if flags is None or option not in flags:
                        if strict:
                            raise OptionError("'%s' flag is not allowed in this context" % option)

                if value is not None:
                    self[option] = cls.preprocess(value)

        preprocess_options(args)

        for key, value in dict(defaults).items():
            if key in self:
                del defaults[key]
            else:
                for option in self.keys():
                    cls = self.__options__[option]

                    if key in cls.excludes:
                        del defaults[key]
                        break

        preprocess_options(defaults)

        for option in self.keys():
            cls = self.__options__[option]

            for require_option in cls.requires:
                if self.get(require_option) is None:
                    raise OptionError("'%s' option is only allowed together with '%s'" % (option, require_option))

            for exclude_option in cls.excludes:
                if self.get(exclude_option) is not None:
                    raise OptionError("'%s' option is not allowed together with '%s'" % (option, exclude_option))

        for option in self.__order__:
            self.__options__[option].postprocess(self)

    @classmethod
    def _init_dependencies_order(cls):
        """Resolve the order of options' processing. """
        if cls.__order__ is None:
            vertices, edges = [], set([])

            for name, option in cls.__options__.items():
                vertices.append(name)

                for _name in option.after:
                    edges.add((_name, name))

                for _name in option.before:
                    edges.add((name, _name))

            try:
                cls.__order__ = topological_sort((vertices, list(edges)))
            except ValueError:
                raise RuntimeError(
                    "cycle detected in sympy.polys options framework")

    def clone(self, updates={}):
        """Clone ``self`` and update specified options. """
        obj = dict.__new__(self.__class__)

        for option, value in self.items():
            obj[option] = value

        for option, value in updates.items():
            obj[option] = value

        return obj

    def __setattr__(self, attr, value):
        if attr in self.__options__:
            self[attr] = value
        else:
            super(Options, self).__setattr__(attr, value)

    @property
    def args(self):
        args = {}

        for option, value in self.items():
            if value is not None and option != 'gens':
                cls = self.__options__[option]

                if not issubclass(cls, Flag):
                    args[option] = value

        return args

    @property
    def options(self):
        options = {}

        for option, cls in self.__options__.items():
            if not issubclass(cls, Flag):
                options[option] = getattr(self, option)

        return options

    @property
    def flags(self):
        flags = {}

        for option, cls in self.__options__.items():
            if issubclass(cls, Flag):
                flags[option] = getattr(self, option)

        return flags


class Expand(with_metaclass(OptionType, BooleanOption)):
    """``expand`` option to polynomial manipulation functions. """

    option = 'expand'

    requires = []
    excludes = []

    @classmethod
    def default(cls):
        return True


class Gens(with_metaclass(OptionType, Option)):
    """``gens`` option to polynomial manipulation functions. """

    option = 'gens'

    requires = []
    excludes = []

    @classmethod
    def default(cls):
        return ()

    @classmethod
    def preprocess(cls, gens):
        if isinstance(gens, Basic):
            gens = (gens,)
        elif len(gens) == 1 and hasattr(gens[0], '__iter__'):
            gens = gens[0]

        if gens == (None,):
            gens = ()
        elif has_dups(gens):
            raise GeneratorsError("duplicated generators: %s" % str(gens))
        elif any(gen.is_commutative is False for gen in gens):
            raise GeneratorsError("non-commutative generators: %s" % str(gens))

        return tuple(gens)


class Wrt(with_metaclass(OptionType, Option)):
    """``wrt`` option to polynomial manipulation functions. """

    option = 'wrt'

    requires = []
    excludes = []

    _re_split = re.compile(r"\s*,\s*|\s+")

    @classmethod
    def preprocess(cls, wrt):
        if isinstance(wrt, Basic):
            return [str(wrt)]
        elif isinstance(wrt, str):
            wrt = wrt.strip()
            if wrt.endswith(','):
                raise OptionError('Bad input: missing parameter.')
            if not wrt:
                return []
            return [ gen for gen in cls._re_split.split(wrt) ]
        elif hasattr(wrt, '__getitem__'):
            return list(map(str, wrt))
        else:
            raise OptionError("invalid argument for 'wrt' option")


class Sort(with_metaclass(OptionType, Option)):
    """``sort`` option to polynomial manipulation functions. """

    option = 'sort'

    requires = []
    excludes = []

    @classmethod
    def default(cls):
        return []

    @classmethod
    def preprocess(cls, sort):
        if isinstance(sort, str):
            return [ gen.strip() for gen in sort.split('>') ]
        elif hasattr(sort, '__getitem__'):
            return list(map(str, sort))
        else:
            raise OptionError("invalid argument for 'sort' option")


class Order(with_metaclass(OptionType, Option)):
    """``order`` option to polynomial manipulation functions. """

    option = 'order'

    requires = []
    excludes = []

    @classmethod
    def default(cls):
        return sympy.polys.orderings.lex

    @classmethod
    def preprocess(cls, order):
        return sympy.polys.orderings.monomial_key(order)


class Field(with_metaclass(OptionType, BooleanOption)):
    """``field`` option to polynomial manipulation functions. """

    option = 'field'

    requires = []
    excludes = ['domain', 'split', 'gaussian']


class Greedy(with_metaclass(OptionType, BooleanOption)):
    """``greedy`` option to polynomial manipulation functions. """

    option = 'greedy'

    requires = []
    excludes = ['domain', 'split', 'gaussian', 'extension', 'modulus', 'symmetric']


class Composite(with_metaclass(OptionType, BooleanOption)):
    """``composite`` option to polynomial manipulation functions. """

    option = 'composite'

    @classmethod
    def default(cls):
        return None

    requires = []
    excludes = ['domain', 'split', 'gaussian', 'extension', 'modulus', 'symmetric']


class Domain(with_metaclass(OptionType, Option)):
    """``domain`` option to polynomial manipulation functions. """

    option = 'domain'

    requires = []
    excludes = ['field', 'greedy', 'split', 'gaussian', 'extension']

    after = ['gens']

    _re_realfield = re.compile(r"^(R|RR)(_(\d+))?$")
    _re_complexfield = re.compile(r"^(C|CC)(_(\d+))?$")
    _re_finitefield = re.compile(r"^(FF|GF)\((\d+)\)$")
    _re_polynomial = re.compile(r"^(Z|ZZ|Q|QQ)\[(.+)\]$")
    _re_fraction = re.compile(r"^(Z|ZZ|Q|QQ)\((.+)\)$")
    _re_algebraic = re.compile(r"^(Q|QQ)\<(.+)\>$")

    @classmethod
    def preprocess(cls, domain):
        if isinstance(domain, sympy.polys.domains.Domain):
            return domain
        elif hasattr(domain, 'to_domain'):
            return domain.to_domain()
        elif isinstance(domain, string_types):
            if domain in ['Z', 'ZZ']:
                return sympy.polys.domains.ZZ

            if domain in ['Q', 'QQ']:
                return sympy.polys.domains.QQ

            if domain == 'EX':
                return sympy.polys.domains.EX

            r = cls._re_realfield.match(domain)

            if r is not None:
                _, _, prec = r.groups()

                if prec is None:
                    return sympy.polys.domains.RR
                else:
                    return sympy.polys.domains.RealField(int(prec))

            r = cls._re_complexfield.match(domain)

            if r is not None:
                _, _, prec = r.groups()

                if prec is None:
                    return sympy.polys.domains.CC
                else:
                    return sympy.polys.domains.ComplexField(int(prec))

            r = cls._re_finitefield.match(domain)

            if r is not None:
                return sympy.polys.domains.FF(int(r.groups()[1]))

            r = cls._re_polynomial.match(domain)

            if r is not None:
                ground, gens = r.groups()

                gens = list(map(sympify, gens.split(',')))

                if ground in ['Z', 'ZZ']:
                    return sympy.polys.domains.ZZ.poly_ring(*gens)
                else:
                    return sympy.polys.domains.QQ.poly_ring(*gens)

            r = cls._re_fraction.match(domain)

            if r is not None:
                ground, gens = r.groups()

                gens = list(map(sympify, gens.split(',')))

                if ground in ['Z', 'ZZ']:
                    return sympy.polys.domains.ZZ.frac_field(*gens)
                else:
                    return sympy.polys.domains.QQ.frac_field(*gens)

            r = cls._re_algebraic.match(domain)

            if r is not None:
                gens = list(map(sympify, r.groups()[1].split(',')))
                return sympy.polys.domains.QQ.algebraic_field(*gens)

        raise OptionError('expected a valid domain specification, got %s' % domain)

    @classmethod
    def postprocess(cls, options):
        if 'gens' in options and 'domain' in options and options['domain'].is_Composite and \
                (set(options['domain'].symbols) & set(options['gens'])):
            raise GeneratorsError(
                "ground domain and generators interfere together")
        elif ('gens' not in options or not options['gens']) and \
                'domain' in options and options['domain'] == sympy.polys.domains.EX:
            raise GeneratorsError("you have to provide generators because EX domain was requested")


class Split(with_metaclass(OptionType, BooleanOption)):
    """``split`` option to polynomial manipulation functions. """

    option = 'split'

    requires = []
    excludes = ['field', 'greedy', 'domain', 'gaussian', 'extension',
        'modulus', 'symmetric']

    @classmethod
    def postprocess(cls, options):
        if 'split' in options:
            raise NotImplementedError("'split' option is not implemented yet")


class Gaussian(with_metaclass(OptionType, BooleanOption)):
    """``gaussian`` option to polynomial manipulation functions. """

    option = 'gaussian'

    requires = []
    excludes = ['field', 'greedy', 'domain', 'split', 'extension',
        'modulus', 'symmetric']

    @classmethod
    def postprocess(cls, options):
        if 'gaussian' in options and options['gaussian'] is True:
            options['extension'] = set([S.ImaginaryUnit])
            Extension.postprocess(options)


class Extension(with_metaclass(OptionType, Option)):
    """``extension`` option to polynomial manipulation functions. """

    option = 'extension'

    requires = []
    excludes = ['greedy', 'domain', 'split', 'gaussian', 'modulus',
        'symmetric']

    @classmethod
    def preprocess(cls, extension):
        if extension == 1:
            return bool(extension)
        elif extension == 0:
            raise OptionError("'False' is an invalid argument for 'extension'")
        else:
            if not hasattr(extension, '__iter__'):
                extension = set([extension])
            else:
                if not extension:
                    extension = None
                else:
                    extension = set(extension)

            return extension

    @classmethod
    def postprocess(cls, options):
        if 'extension' in options and options['extension'] is not True:
            options['domain'] = sympy.polys.domains.QQ.algebraic_field(
                *options['extension'])


class Modulus(with_metaclass(OptionType, Option)):
    """``modulus`` option to polynomial manipulation functions. """

    option = 'modulus'

    requires = []
    excludes = ['greedy', 'split', 'domain', 'gaussian', 'extension']

    @classmethod
    def preprocess(cls, modulus):
        modulus = sympify(modulus)

        if modulus.is_Integer and modulus > 0:
            return int(modulus)
        else:
            raise OptionError(
                "'modulus' must a positive integer, got %s" % modulus)

    @classmethod
    def postprocess(cls, options):
        if 'modulus' in options:
            modulus = options['modulus']
            symmetric = options.get('symmetric', True)
            options['domain'] = sympy.polys.domains.FF(modulus, symmetric)


class Symmetric(with_metaclass(OptionType, BooleanOption)):
    """``symmetric`` option to polynomial manipulation functions. """

    option = 'symmetric'

    requires = ['modulus']
    excludes = ['greedy', 'domain', 'split', 'gaussian', 'extension']


class Strict(with_metaclass(OptionType, BooleanOption)):
    """``strict`` option to polynomial manipulation functions. """

    option = 'strict'

    @classmethod
    def default(cls):
        return True


class Auto(with_metaclass(OptionType, BooleanOption, Flag)):
    """``auto`` flag to polynomial manipulation functions. """

    option = 'auto'

    after = ['field', 'domain', 'extension', 'gaussian']

    @classmethod
    def default(cls):
        return True

    @classmethod
    def postprocess(cls, options):
        if ('domain' in options or 'field' in options) and 'auto' not in options:
            options['auto'] = False


class Frac(with_metaclass(OptionType, BooleanOption, Flag)):
    """``auto`` option to polynomial manipulation functions. """

    option = 'frac'

    @classmethod
    def default(cls):
        return False


class Formal(with_metaclass(OptionType, BooleanOption, Flag)):
    """``formal`` flag to polynomial manipulation functions. """

    option = 'formal'

    @classmethod
    def default(cls):
        return False


class Polys(with_metaclass(OptionType, BooleanOption, Flag)):
    """``polys`` flag to polynomial manipulation functions. """

    option = 'polys'


class Include(with_metaclass(OptionType, BooleanOption, Flag)):
    """``include`` flag to polynomial manipulation functions. """

    option = 'include'

    @classmethod
    def default(cls):
        return False


class All(with_metaclass(OptionType, BooleanOption, Flag)):
    """``all`` flag to polynomial manipulation functions. """

    option = 'all'

    @classmethod
    def default(cls):
        return False


class Gen(with_metaclass(OptionType, Flag)):
    """``gen`` flag to polynomial manipulation functions. """

    option = 'gen'

    @classmethod
    def default(cls):
        return 0

    @classmethod
    def preprocess(cls, gen):
        if isinstance(gen, (Basic, int)):
            return gen
        else:
            raise OptionError("invalid argument for 'gen' option")


class Series(with_metaclass(OptionType, BooleanOption, Flag)):
    """``series`` flag to polynomial manipulation functions. """

    option = 'series'

    @classmethod
    def default(cls):
        return False


class Symbols(with_metaclass(OptionType, Flag)):
    """``symbols`` flag to polynomial manipulation functions. """

    option = 'symbols'

    @classmethod
    def default(cls):
        return numbered_symbols('s', start=1)

    @classmethod
    def preprocess(cls, symbols):
        if hasattr(symbols, '__iter__'):
            return iter(symbols)
        else:
            raise OptionError("expected an iterator or iterable container, got %s" % symbols)


class Method(with_metaclass(OptionType, Flag)):
    """``method`` flag to polynomial manipulation functions. """

    option = 'method'

    @classmethod
    def preprocess(cls, method):
        if isinstance(method, str):
            return method.lower()
        else:
            raise OptionError("expected a string, got %s" % method)


def build_options(gens, args=None):
    """Construct options from keyword arguments or ... options. """
    if args is None:
        gens, args = (), gens

    if len(args) != 1 or 'opt' not in args or gens:
        return Options(gens, args)
    else:
        return args['opt']


def allowed_flags(args, flags):
    """
    Allow specified flags to be used in the given context.

    Examples
    ========

    >>> from sympy.polys.polyoptions import allowed_flags
    >>> from sympy.polys.domains import ZZ

    >>> allowed_flags({'domain': ZZ}, [])

    >>> allowed_flags({'domain': ZZ, 'frac': True}, [])
    Traceback (most recent call last):
    ...
    FlagError: 'frac' flag is not allowed in this context

    >>> allowed_flags({'domain': ZZ, 'frac': True}, ['frac'])

    """
    flags = set(flags)

    for arg in args.keys():
        try:
            if Options.__options__[arg].is_Flag and not arg in flags:
                raise FlagError(
                    "'%s' flag is not allowed in this context" % arg)
        except KeyError:
            raise OptionError("'%s' is not a valid option" % arg)


def set_defaults(options, **defaults):
    """Update options with default values. """
    if 'defaults' not in options:
        options = dict(options)
        options['defaults'] = defaults

    return options

Options._init_dependencies_order()
