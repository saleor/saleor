# -*- coding: utf-8 -*-
# Copyright 2009-2013, Peter A. Bigot
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain a
# copy of the License at:
#
#            http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""Classes supporting U{XMLSchema Part 2: Datatypes<http://www.w3.org/TR/xmlschema-2/>}.

Each L{simple type definition<pyxb.xmlschema.structures.SimpleTypeDefinition>} component
instance is paired with at most one L{basis.simpleTypeDefinition}
class, which is a subclass of a Python type augmented with facets and
other constraining information.  This file contains the definitions of
these types.

We want the simple datatypes to be efficient Python values, but to
also hold specific constraints that don't apply to the Python types.
To do this, we subclass each PST.  Primitive PSTs inherit from the
Python type that represents them, and from a
pyxb.binding.basis.simpleTypeDefinition class which adds in the
constraint infrastructure.  Derived PSTs inherit from the parent PST.

There is an exception to this when the Python type best suited for a
derived SimpleTypeDefinition differs from the type associated with its
parent STD: for example, L{xsd:integer<integer>} has a value range
that requires it be represented by a Python C{long}, but
L{xsd:int<int>} allows representation by a Python C{int}.  In this
case, the derived PST class is structured like a primitive type, but
the PST associated with the STD superclass is recorded in a class
variable C{_XsdBaseType}.

Note the strict terminology: "datatype" refers to a class which is a
subclass of a Python type, while "type definition" refers to an
instance of either SimpleTypeDefinition or ComplexTypeDefinition.

"""

import logging
import re
import binascii
import base64
import math
import decimal as python_decimal
from pyxb.exceptions_ import *
import pyxb.namespace
import pyxb.utils.unicode
from pyxb.utils import six
from . import basis

_log = logging.getLogger(__name__)

_PrimitiveDatatypes = []
_DerivedDatatypes = []
_ListDatatypes = []

# We use unicode as the Python type for anything that isn't a normal
# primitive type.  Presumably, only enumeration and pattern facets
# will be applied.
class anySimpleType (basis.simpleTypeDefinition, six.text_type):
    """XMLSchema datatype U{anySimpleType<http://www.w3.org/TR/xmlschema-2/#dt-anySimpleType>}."""
    _XsdBaseType = None
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('anySimpleType')

    @classmethod
    def XsdLiteral (cls, value):
        return value
# anySimpleType is not treated as a primitive, because its variety
# must be absent (not atomic).

class string (basis.simpleTypeDefinition, six.text_type):
    """XMLSchema datatype U{string<http://www.w3.org/TR/xmlschema-2/#string>}."""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('string')

    @classmethod
    def XsdLiteral (cls, value):
        assert isinstance(value, cls)
        return value

    @classmethod
    def XsdValueLength (cls, value):
        return len(value)

_PrimitiveDatatypes.append(string)

# It is illegal to subclass the bool type in Python, so we subclass
# int instead.
@six.python_2_unicode_compatible
class boolean (basis.simpleTypeDefinition, six.int_type):
    """XMLSchema datatype U{boolean<http://www.w3.org/TR/xmlschema-2/#boolean>}."""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('boolean')

    @classmethod
    def XsdLiteral (cls, value):
        if value:
            return 'true'
        return 'false'

    def __str__ (self):
        if self:
            return six.u('true')
        return six.u('false')

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        if 0 < len(args):
            value = args[0]
            args = args[1:]
            if value in (1, 0, '1', '0', 'true', 'false'):
                if value in (1, '1', 'true'):
                    iv = True
                else:
                    iv = False
                return super(boolean, cls).__new__(cls, iv, *args, **kw)
            raise SimpleTypeValueError(cls, value)
        return super(boolean, cls).__new__(cls, *args, **kw)

_PrimitiveDatatypes.append(boolean)

class decimal (basis.simpleTypeDefinition, python_decimal.Decimal, basis._RepresentAsXsdLiteral_mixin):
    """XMLSchema datatype U{decimal<http://www.w3.org/TR/xmlschema-2/#decimal>}.

    This class uses Python's L{decimal.Decimal} class to support (by
    default) 28 significant digits.  Only normal and zero values are
    valid; this means C{NaN} and C{Infinity} may be created during
    calculations, but cannot be expressed in XML documents.
    """
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('decimal')

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        # Pre Python 2.7 can't construct from float values
        if (1 <= len(args)) and isinstance(args[0], six.float_type):
            args = (str(args[0]),) + args[1:]
        try:
            rv = super(decimal, cls).__new__(cls, *args, **kw)
        except python_decimal.DecimalException:
            raise SimpleTypeValueError(cls, *args)
        cls._CheckValidValue(rv)
        return rv

    @classmethod
    def _CheckValidValue (cls, value):
        if not (value.is_normal() or value.is_zero()):
            raise SimpleTypeValueError(cls, value)
        return super(decimal, cls)._CheckValidValue(value)

    @classmethod
    def XsdLiteral (cls, value):
        (sign, digits, exponent) = value.normalize().as_tuple()
        if (0 < len(digits)) and (0 == digits[0]):
            digits = ()
        rchars = []
        if sign:
            rchars.append('-')
        digits_before = len(digits) + exponent
        if 0 < digits_before:
            rchars.extend(map(str, digits[:digits_before]))
            digits = digits[digits_before:]
            if (0 == len(digits)) and (0 < exponent):
                rchars.extend(['0'] * exponent)
                exponent = 0
        else:
            rchars.append('0')
        rchars.append('.')
        digits_after = -exponent
        assert(0 <= digits_after)
        if 0 < digits_after:
            rchars.extend(['0'] * (digits_after - len(digits)))
            rchars.extend(map(str, digits))
        else:
            rchars.append('0')
        return six.u('').join(rchars)

_PrimitiveDatatypes.append(decimal)

class _fp (basis.simpleTypeDefinition, six.float_type):
    _XsdBaseType = anySimpleType

    @classmethod
    def XsdLiteral (cls, value):
        if math.isinf(value):
            if (0 > value):
                return '-INF'
            return 'INF'
        if math.isnan(value):
            return 'NaN'
        return '%s' % (value,)

class float (_fp):
    """XMLSchema datatype U{float<http://www.w3.org/TR/xmlschema-2/#float>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('float')

_PrimitiveDatatypes.append(float)

class double (_fp):
    """XMLSchema datatype U{double<http://www.w3.org/TR/xmlschema-2/#double>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('double')

_PrimitiveDatatypes.append(double)

import datetime

class duration (basis.simpleTypeDefinition, datetime.timedelta, basis._RepresentAsXsdLiteral_mixin):
    """XMLSchema datatype U{duration<http://www.w3.org/TR/xmlschema-2/#duration>}.

    This class uses the Python C{datetime.timedelta} class as its
    underlying representation.  This works fine as long as no months
    or years are involved, and no negative durations are involved.
    Because the XML Schema value space is so much larger, it is kept
    distinct from the Python value space, which reduces to integral
    days, seconds, and microseconds.

    In other words, the implementation of this type is a little
    shakey.

    """

    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('duration')

    __Lexical_re = re.compile('^(?P<neg>-?)P((?P<years>\d+)Y)?((?P<months>\d+)M)?((?P<days>\d+)D)?(?P<Time>T((?P<hours>\d+)H)?((?P<minutes>\d+)M)?(((?P<seconds>\d+)(?P<fracsec>\.\d+)?)S)?)?$')

    # We do not use weeks
    __XSDFields = ( 'years', 'months', 'days', 'hours', 'minutes', 'seconds' )
    __PythonFields = ( 'days', 'seconds', 'microseconds', 'minutes', 'hours' )

    def negativeDuration (self):
        return self.__negativeDuration
    __negativeDuration = None

    def durationData (self):
        return self.__durationData
    __durationData = None

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        have_kw_update = False
        if not kw.get('_nil'):
            if 0 == len(args):
                raise SimpleTypeValueError(cls, args)
            text = args[0]
        if kw.get('_nil'):
            data = dict(zip(cls.__PythonFields, len(cls.__PythonFields) * [0,]))
            negative_duration = False
        elif isinstance(text, six.string_types):
            match = cls.__Lexical_re.match(text)
            if match is None:
                raise SimpleTypeValueError(cls, text)
            match_map = match.groupdict()
            if 'T' == match_map.get('Time'):
                # Can't have T without additional time information
                raise SimpleTypeValueError(cls, text)

            negative_duration = ('-' == match_map.get('neg'))

            fractional_seconds = 0.0
            if match_map.get('fracsec') is not None:
                fractional_seconds = six.float_type('0%s' % (match_map['fracsec'],))
                usec = six.int_type(1000000 * fractional_seconds)
                if negative_duration:
                    kw['microseconds'] = - usec
                else:
                    kw['microseconds'] = usec
            else:
                # Discard any bogosity passed in by the caller
                kw.pop('microsecond', None)

            data = { }
            for fn in cls.__XSDFields:
                v = match_map.get(fn, 0)
                if v is None:
                    v = 0
                data[fn] = six.int_type(v)
                if fn in cls.__PythonFields:
                    if negative_duration:
                        kw[fn] = - data[fn]
                    else:
                        kw[fn] = data[fn]
            data['seconds'] += fractional_seconds
            have_kw_update = True
        elif isinstance(text, cls):
            data = text.durationData().copy()
            negative_duration = text.negativeDuration()
        elif isinstance(text, datetime.timedelta):
            data = { 'days' : text.days,
                     'seconds' : text.seconds + (text.microseconds / 1000000.0) }
            negative_duration = (0 > data['days'])
            if negative_duration:
                if 0.0 == data['seconds']:
                    data['days'] = - data['days']
                else:
                    data['days'] = 1 - data['days']
                    data['seconds'] = 24 * 60 * 60.0 - data['seconds']
            data['minutes'] = 0
            data['hours'] = 0
        elif isinstance(text, six.integer_types) and (1 < len(args)):
            # Apply the arguments as in the underlying Python constructor
            data = dict(zip(cls.__PythonFields[:len(args)], args))
            negative_duration = False
        else:
            raise SimpleTypeValueError(cls, text)
        if not have_kw_update:
            rem_time = data.pop('seconds', 0)
            if (0 != (rem_time % 1)):
                data['microseconds'] = data.pop('microseconds', 0) + six.int_type(1000000 * (rem_time % 1))
                rem_time = rem_time // 1
            data['seconds'] = rem_time % 60
            rem_time = data.pop('minutes', 0) + (rem_time // 60)
            data['minutes'] = rem_time % 60
            rem_time = data.pop('hours', 0) + (rem_time // 60)
            data['hours'] = rem_time % 24
            data['days'] += (rem_time // 24)
            for fn in cls.__PythonFields:
                if fn in data:
                    if negative_duration:
                        kw[fn] = - data[fn]
                    else:
                        kw[fn] = data[fn]
                else:
                    kw.pop(fn, None)
            kw['microseconds'] = data.pop('microseconds', 0)
            data['seconds'] += kw['microseconds'] / 1000000.0

        rv = super(duration, cls).__new__(cls, **kw)
        rv.__durationData = data
        rv.__negativeDuration = negative_duration
        return rv

    @classmethod
    def XsdLiteral (cls, value):
        elts = []
        if value.negativeDuration():
            elts.append('-')
        elts.append('P')
        for k in ( 'years', 'months', 'days' ):
            v = value.__durationData.get(k, 0)
            if 0 != v:
                elts.append('%d%s' % (v, k[0].upper()))
        time_elts = []
        for k in ( 'hours', 'minutes' ):
            v = value.__durationData.get(k, 0)
            if 0 != v:
                time_elts.append('%d%s' % (v, k[0].upper()))
        v = value.__durationData.get('seconds', 0)
        if 0 != v:
            time_elts.append('%gS' % (v,))
        if 0 < len(time_elts):
            elts.append('T')
            elts.extend(time_elts)
        if 1 == len(elts):
            # Value must have zero duration.  Pick something short.
            elts.append('0D')
        return ''.join(elts)

_PrimitiveDatatypes.append(duration)

class _PyXBDateTime_base (basis.simpleTypeDefinition, basis._RepresentAsXsdLiteral_mixin):

    _Lexical_fmt = None
    """Format for the lexical representation of a date-related instance, excluding timezone.

    Subclasses must define this."""

    # Map from strptime/strftime formats to the regular expressions we
    # use to extract them.  We're more strict than strptime, so not
    # trying to use that.
    __PatternMap = { '%Y' : '(?P<negYear>-?)(?P<year>\d{4,})'
                   , '%m' : '(?P<month>\d{2})'
                   , '%d' : '(?P<day>\d{2})'
                   , '%H' : '(?P<hour>\d{2})'
                   , '%M' : '(?P<minute>\d{2})'
                   , '%S' : '(?P<second>\d{2})(?P<fracsec>\.\d+)?'
                   , '%Z' : '(?P<tzinfo>Z|[-+]\d\d:\d\d)' }

    # Cache of compiled regular expressions to parse lexical space of
    # a subclass.
    __LexicalREMap = { }

    # Fields extracted by parsing that have an integer value
    __LexicalIntegerFields = ( 'year', 'month', 'day', 'hour', 'minute', 'second' )

    _UTCTimeZone = pyxb.utils.utility.UTCOffsetTimeZone(0)
    """A L{datetime.tzinfo} instance representing UTC."""

    _LocalTimeZone = pyxb.utils.utility.LocalTimeZone()
    """A L{datetime.tzinfo} instance representing the local time zone."""

    _DefaultYear = 1900
    _DefaultMonth = 1
    _DefaultDay = 1

    @classmethod
    def _LexicalToKeywords (cls, text):
        lexical_re = cls.__LexicalREMap.get(cls)
        if lexical_re is None:
            pattern = '^' + cls._Lexical_fmt + '%Z?$'
            for (k, v) in six.iteritems(cls.__PatternMap):
                pattern = pattern.replace(k, v)
            lexical_re = re.compile(pattern)
            cls.__LexicalREMap[cls] = lexical_re
        match = lexical_re.match(text)
        if match is None:
            raise SimpleTypeValueError(cls, text)
        match_map = match.groupdict()
        kw = { }
        for (k, v) in six.iteritems(match_map):
            if (k in cls.__LexicalIntegerFields) and (v is not None):
                kw[k] = six.int_type(v)
        if '-' == match_map.get('negYear'):
            kw['year'] = - kw['year']
        if match_map.get('fracsec') is not None:
            kw['microsecond'] = six.int_type(round(1000000 * six.float_type('0%s' % (match_map['fracsec'],))))
        else:
            # Discard any bogosity passed in by the caller
            kw.pop('microsecond', None)
        if match_map.get('tzinfo') is not None:
            kw['tzinfo'] = pyxb.utils.utility.UTCOffsetTimeZone(match_map['tzinfo'])
        else:
            kw.pop('tzinfo', None)
        return kw

    @classmethod
    def _SetKeysFromPython_csc (cls, python_value, kw, fields):
        for f in fields:
            kw[f] = getattr(python_value, f)
        return getattr(super(_PyXBDateTime_base, cls), '_SetKeysFromPython_csc', lambda *a,**kw: None)(python_value, kw, fields)

    @classmethod
    def _SetKeysFromPython (cls, python_value, kw, fields):
        return cls._SetKeysFromPython_csc(python_value, kw, fields)

    # Several datetime classes are extension classes, and the PyXB
    # subclasses won't recognize the packed values.  Use the lexical
    # representation instead.
    def __reduce__ (self):
        return (self.__class__, (self.xsdLiteral(),))

    @classmethod
    def _AdjustForTimezone (cls, kw):
        """Update datetime keywords to account for timezone effects.

        All XML schema timezoned times are in UTC, with the time "in
        its timezone".  If the keywords indicate a non-UTC timezone is
        in force, and L{pyxb.PreserveInputTimeZone()} has not been
        set, adjust the values to account for the zone by subtracting
        the corresponding UTC offset and mark explicitly that the time
        is in UTC by leaving a C{tzinfo} attribute identifying the UTC
        time zone.

        @param kw: A dictionary of keywords relevant for a date or
        time instance.  The dictionary is updated by this call.
        """
        if pyxb.PreserveInputTimeZone():
            return
        tzoffs = kw.pop('tzinfo', None)
        if tzoffs is not None:
            use_kw = kw.copy()
            # Ensure ctor requirements of datetime.datetime are met
            use_kw.setdefault('year', cls._DefaultYear)
            use_kw.setdefault('month', cls._DefaultMonth)
            use_kw.setdefault('day', cls._DefaultDay)
            dt = datetime.datetime(tzinfo=tzoffs, **use_kw)
            dt -= tzoffs.utcoffset(dt)
            for k in six.iterkeys(kw):
                kw[k] = getattr(dt, k)
            kw['tzinfo'] = cls._UTCTimeZone

    @classmethod
    def XsdLiteral (cls, value):
        iso = value.replace(tzinfo=None).isoformat()
        if 0 <= iso.find('.'):
            iso = iso.rstrip('0')
        if value.tzinfo is not None:
            iso += value.tzinfo.tzname(value)
        return iso

class dateTime (_PyXBDateTime_base, datetime.datetime):
    """XMLSchema datatype U{dateTime<http://www.w3.org/TR/xmlschema-2/#dateTime>}.

    This class uses the Python C{datetime.datetime} class as its
    underlying representation.  Unless L{pyxb.PreserveInputTimeZone()}
    is used, all timezoned dateTime objects are in UTC.  Presence of
    time zone information in the lexical space is preserved by a
    non-empty tzinfo field, which should always be zero minutes offset
    from UTC unless the input time zone was preserved.

    @warning: The value space of Python's C{datetime.datetime} class
    is more restricted than that of C{xs:datetime}.  As a specific
    example, Python does not support negative years or years with more
    than four digits.  For now, the convenience of having an object
    that is compatible with Python is more important than supporting
    the full value space.  In the future, the choice may be left up to
    the developer.
    """

    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('dateTime')

    _Lexical_fmt = '%Y-%m-%dT%H:%M:%S'
    __CtorFields = ( 'year', 'month', 'day', 'hour', 'minute', 'second', 'microsecond', 'tzinfo' )

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)

        ctor_kw = { }
        if kw.get('_nil'):
            ctor_kw = { 'year': 1900, 'month': 1, 'day': 1 }
        elif 1 == len(args):
            value = args[0]
            if isinstance(value, six.string_types):
                ctor_kw.update(cls._LexicalToKeywords(value))
            elif isinstance(value, datetime.datetime):
                cls._SetKeysFromPython(value, ctor_kw, cls.__CtorFields)
            elif isinstance(value, six.integer_types):
                raise TypeError('function takes at least 3 arguments (%d given)' % (len(args),))
            else:
                raise SimpleTypeValueError(cls, value)
        elif 3 <= len(args):
            for fi in range(len(cls.__CtorFields)):
                fn = cls.__CtorFields[fi]
                if fi < len(args):
                    ctor_kw[fn] = args[fi]
                elif fn in kw:
                    ctor_kw[fn] = kw[fn]
                kw.pop(fn, None)
        else:
            raise TypeError('function takes at least 3 arguments (%d given)' % (len(args),))

        cls._AdjustForTimezone(ctor_kw)
        kw.update(ctor_kw)
        year = kw.pop('year')
        month = kw.pop('month')
        day = kw.pop('day')
        rv = super(dateTime, cls).__new__(cls, year, month, day, **kw)
        return rv

    @classmethod
    def today (cls):
        """Return today.

        Just like datetime.datetime.today(), except this one sets a
        tzinfo field so it's clear the value is UTC."""
        return cls(datetime.datetime.now(cls._UTCTimeZone))

    def aslocal (self):
        """Returns a C{datetime.datetime} instance denoting the same
        time as this instance but adjusted to be in the local time
        zone.

        @rtype: C{datetime.datetime} (B{NOT} C{xsd.dateTime})
        """
        dt = self
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._UTCTimeZone)
        return dt.astimezone(self._LocalTimeZone)

_PrimitiveDatatypes.append(dateTime)

class time (_PyXBDateTime_base, datetime.time):
    """XMLSchema datatype U{time<http://www.w3.org/TR/xmlschema-2/#time>}.

    This class uses the Python C{datetime.time} class as its
    underlying representation.  Note that per the XMLSchema spec, all
    dateTime objects are in UTC, and that timezone information in the
    string representation in XML is an indication of the local time
    zone's offset from UTC.  Presence of time zone information in the
    lexical space is indicated by the tzinfo field.

    @note: C{pyxb.PreserveInputTimeZone()} can be used to bypass the
    normalization to UTC.
    """

    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('time')

    _Lexical_fmt = '%H:%M:%S'
    __CtorFields = ( 'hour', 'minute', 'second', 'microsecond', 'tzinfo' )

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        ctor_kw = { }
        if 1 <= len(args):
            value = args[0]
            if isinstance(value, six.string_types):
                ctor_kw.update(cls._LexicalToKeywords(value))
            elif isinstance(value, (datetime.time, datetime.datetime)):
                cls._SetKeysFromPython(value, ctor_kw, cls.__CtorFields)
            elif isinstance(value, six.integer_types):
                for fi in range(len(cls.__CtorFields)):
                    fn = cls.__CtorFields[fi]
                    if fi < len(args):
                        ctor_kw[fn] = args[fi]
                    elif fn in kw:
                        ctor_kw[fn] = kw[fn]
                    kw.pop(fn, None)
            else:
                raise SimpleTypeValueError(cls, value)

        cls._AdjustForTimezone(ctor_kw)
        kw.update(ctor_kw)
        return super(time, cls).__new__(cls, **kw)

_PrimitiveDatatypes.append(time)

class _PyXBDateOnly_base (_PyXBDateTime_base, datetime.datetime):
    _XsdBaseType = anySimpleType

    _ValidFields = ( 'year', 'month', 'day' )

    def __new__ (cls, *args, **kw):
        args = cls._ConvertArguments(args, kw)
        ctor_kw = { }
        ctor_kw['year'] = cls._DefaultYear
        ctor_kw['month'] = cls._DefaultMonth
        ctor_kw['day'] = cls._DefaultDay
        ctor_kw['hour'] = 0
        ctor_kw['minute'] = 0
        ctor_kw['second'] = 0
        if kw.get('_nil'):
            pass
        elif 1 <= len(args):
            value = args[0]
            if isinstance(value, six.string_types):
                if 1 != len(args):
                    raise TypeError('construction from string requires exactly 1 argument')
                ctor_kw.update(cls._LexicalToKeywords(value))
            elif isinstance(value, (datetime.date, datetime.datetime)):
                if 1 != len(args):
                    raise TypeError('construction from instance requires exactly 1 argument')
                cls._SetKeysFromPython(value, ctor_kw, cls._ValidFields)
                try:
                    tzinfo = value.tzinfo
                    if tzinfo is not None:
                        ctor_kw['tzinfo'] = tzinfo
                except AttributeError:
                    pass
            else:
                fi = 0
                while fi < len(cls._ValidFields):
                    fn = cls._ValidFields[fi]
                    if fi < len(args):
                        ctor_kw[fn] = args[fi]
                    elif fn in kw:
                        ctor_kw[fn] = kw[fn]
                    kw.pop(fn, None)
                    fi += 1
                if fi < len(args):
                    ctor_kw['tzinfo'] = args[fi]
                    fi += 1
                if fi != len(args):
                    raise TypeError('function takes %d arguments plus optional tzinfo (%d given)' % (len(cls._ValidFields), len(args)))
        else:
            raise TypeError('function takes %d arguments plus optional tzinfo' % (len(cls._ValidFields),))

        # Do not adjust for the timezone here.  Only xsd:date provides
        # a recoverable timezone, so just preserve the as-supplied
        # timezone, and we'll canonicalize the date one if/when it's
        # converted back to lexical form.
        kw.update(ctor_kw)
        argv = []
        argv.append(kw.pop('year'))
        argv.append(kw.pop('month'))
        argv.append(kw.pop('day'))
        return super(_PyXBDateOnly_base, cls).__new__(cls, *argv, **kw)

    @classmethod
    def XsdLiteral (cls, value):
        # Work around strftime year restriction
        fmt = cls._Lexical_fmt
        if value.year < 1900:
            fmt = fmt.replace('%Y', '%04d' % (value.year,))
            value = value.replace(year=1900)
        if value.tzinfo is not None:
            fmt += value.tzinfo.tzname(value)
        return value.strftime(fmt)

class date (_PyXBDateOnly_base):
    """XMLSchema datatype U{date<http://www.w3.org/TR/xmlschema-2/#date>}.

    This class uses the Python C{datetime.datetime} class as its
    underlying representation; fields not relevant to this type are
    derived from 1900-01-01T00:00:00.

    @note: Unlike L{dateTime}, timezoned date values are not converted
    to UTC.  The provided timezone information is retained along with
    the instance; however, the lexical representation generated for
    output is canonicalized (timezones no more than 12 hours off UTC).
    """

    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('date')
    _Lexical_fmt = '%Y-%m-%d'
    _Fields = ( 'year', 'month', 'day' )

    __SecondsPerMinute = 60
    __MinutesPerHalfDay = 12 * 60
    __MinutesPerDay = 24 * 60
    def xsdRecoverableTzinfo (self):
        """Return the recoverable tzinfo for the date.

        Return a L{pyxb.utils.utility.UTCOffsetTimeZone} instance
        reflecting the timezone associated with the date, or C{None}
        if the date is not timezoned.

        @note: This is not the recoverable timezone, because timezones are
        represented as timedeltas which get normalized in ways that
        don't match what we expect for a tzinfo.
        """
        if self.tzinfo is None:
            return None
        sdt = self.replace(hour=0, minute=0, second=0, tzinfo=self._UTCTimeZone)
        utc_offset = (sdt - self).seconds // self.__SecondsPerMinute
        if utc_offset > self.__MinutesPerHalfDay:
            utc_offset -= self.__MinutesPerDay
        return pyxb.utils.utility.UTCOffsetTimeZone(utc_offset)

    @classmethod
    def XsdLiteral (cls, value):
        # Work around strftime year restriction
        fmt = cls._Lexical_fmt
        rtz = value.xsdRecoverableTzinfo()
        if rtz is not None:
            # If the date is timezoned, convert it to UTC
            value -= value.tzinfo.utcoffset(value)
            value = value.replace(tzinfo=cls._UTCTimeZone)
        # Use the midpoint of the one-day interval to get the correct
        # month/day.
        value += datetime.timedelta(minutes=cls.__MinutesPerHalfDay)
        if value.year < 1900:
            fmt = fmt.replace('%Y', '%04d' % (value.year,))
            value = value.replace(year=1900)
        if rtz is not None:
            fmt += rtz.tzname(value)
        return value.strftime(fmt)

_PrimitiveDatatypes.append(date)

class gYearMonth (_PyXBDateOnly_base):
    """XMLSchema datatype U{gYearMonth<http://www.w3.org/TR/xmlschema-2/#gYearMonth>}.

    This class uses the Python C{datetime.datetime} class as its
    underlying representation; fields not relevant to this type are
    derived from 1900-01-01T00:00:00.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gYearMonth')
    _Lexical_fmt = '%Y-%m'
    _ValidFields = ( 'year', 'month' )

_PrimitiveDatatypes.append(gYearMonth)

class gYear (_PyXBDateOnly_base):
    """XMLSchema datatype U{gYear<http://www.w3.org/TR/xmlschema-2/#gYear>}.

    This class uses the Python C{datetime.datetime} class as its
    underlying representation; fields not relevant to this type are
    derived from 1900-01-01T00:00:00.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gYear')
    _Lexical_fmt = '%Y'
    _ValidFields = ( 'year', )
_PrimitiveDatatypes.append(gYear)

class gMonthDay (_PyXBDateOnly_base):
    """XMLSchema datatype U{gMonthDay<http://www.w3.org/TR/xmlschema-2/#gMonthDay>}.

    This class uses the Python C{datetime.datetime} class as its
    underlying representation; fields not relevant to this type are
    derived from 1900-01-01T00:00:00.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gMonthDay')
    _Lexical_fmt = '--%m-%d'
    _ValidFields = ( 'month', 'day' )
_PrimitiveDatatypes.append(gMonthDay)

class gDay (_PyXBDateOnly_base):
    """XMLSchema datatype U{gDay<http://www.w3.org/TR/xmlschema-2/#gDay>}.

    This class uses the Python C{datetime.datetime} class as its
    underlying representation; fields not relevant to this type are
    derived from 1900-01-01T00:00:00.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gDay')
    _Lexical_fmt = '---%d'
    _ValidFields = ( 'day', )
_PrimitiveDatatypes.append(gDay)

class gMonth (_PyXBDateOnly_base):
    """XMLSchema datatype U{gMonth<http://www.w3.org/TR/xmlschema-2/#gMonth>}.

    This class uses the Python C{datetime.datetime} class as its
    underlying representation; fields not relevant to this type are
    derived from 1900-01-01T00:00:00.
    """
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('gMonth')
    _Lexical_fmt = '--%m'
    _ValidFields = ( 'month', )
_PrimitiveDatatypes.append(gMonth)

class hexBinary (basis.simpleTypeDefinition, six.binary_type):
    """XMLSchema datatype U{hexBinary<http://www.w3.org/TR/xmlschema-2/#hexBinary>}."""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('hexBinary')

    @classmethod
    def _ConvertArguments_vx (cls, args, kw):
        if (1 <= len(args)) and kw.get('_from_xml', False):
            xmlt = args[0]
            try:
                xmld = xmlt.encode('utf-8')
                arg0 = binascii.unhexlify(xmld)
                args = (arg0,) + args[1:]
            except (TypeError, binascii.Error):
                raise SimpleTypeValueError(cls, args[0])
        return args

    @classmethod
    def XsdLiteral (cls, value):
        if isinstance(value, six.text_type):
            value = value.encode('utf-8')
        rvd = binascii.hexlify(value)
        rvt = rvd.decode('utf-8')
        return rvt.upper()

    @classmethod
    def XsdValueLength (cls, value):
        return len(value)

_PrimitiveDatatypes.append(hexBinary)

class base64Binary (basis.simpleTypeDefinition, six.binary_type):
    """XMLSchema datatype U{base64Binary<http://www.w3.org/TR/xmlschema-2/#base64Binary>}.

    See also U{RFC2045<http://tools.ietf.org/html/rfc2045>} and U{RFC4648<http://tools.ietf.org/html/rfc4648>}.
    """
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('base64Binary')

    # base64 is too lenient: it accepts 'ZZZ=' as an encoding of
    # 'e\x96', while the required XML Schema production requires
    # 'ZZY='.  Define a regular expression per section 3.2.16.

    _B04 = '[AQgw]'
    _B04S = '(%s ?)' % (_B04,)
    _B16 = '[AEIMQUYcgkosw048]'
    _B16S = '(%s ?)' % (_B16,)
    _B64 = '[ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/]'
    _B64S = '(%s ?)' % (_B64,)

    __Pattern = '^((' + _B64S + '{4})*((' + _B64S + '{3}' + _B64 + ')|(' + _B64S + '{2}' + _B16S + '=)|(' + _B64S + _B04S + '= ?=)))?$'
    __Lexical_re = re.compile(__Pattern)

    __ValidateLength = None

    @classmethod
    def XsdValidateLength (cls, length):
        """Control the maximum encoded size that is checked for XML literal validity.

        Python's base64 module allows some literals that are invalid
        according to XML rules.  PyXB verifies the validity using a
        regular expression, which is costly for something that is
        unlikely to occur.  Use this function to inhibit checks for
        validity based on the length of the XML literal.

        @param length: C{None} (default) to check all literals,
        otherwise the maximum length literal that will be checked.
        Pass C{-1} to disable the validity check.

        @return: the previous validation length

        """
        rv = cls.__ValidateLength
        if (length is None) or isinstance(length, six.integer_types):
            cls.__ValidateLength = length
            return rv
        raise TypeError('must provide None or integer length')

    @classmethod
    def _ConvertArguments_vx (cls, args, kw):
        if (1 <= len(args)) and kw.get('_from_xml', False):
            xmlt = args[0]
            try:
                xmld = xmlt.encode('utf-8')
                arg0 = base64.standard_b64decode(xmld)
                args = (arg0,) + args[1:]
            except (TypeError, binascii.Error):
                raise SimpleTypeValueError(cls, xmlt)
            if (cls.__ValidateLength is None) or (cls.__ValidateLength >= len(xmlt)):
                # This is what it costs to try to be a validating processor.
                if cls.__Lexical_re.match(xmlt) is None:
                    raise SimpleTypeValueError(cls, xmlt)
        return args

    @classmethod
    def XsdLiteral (cls, value):
        if isinstance(value, six.text_type):
            value = value.encode('utf-8')
        rvd = base64.standard_b64encode(value)
        rvt = rvd.decode('utf-8')
        return rvt

    @classmethod
    def XsdValueLength (cls, value):
        return len(value)

_PrimitiveDatatypes.append(base64Binary)

class anyURI (basis.simpleTypeDefinition, six.text_type):
    """XMLSchema datatype U{anyURI<http://www.w3.org/TR/xmlschema-2/#anyURI>}."""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('anyURI')

    @classmethod
    def XsdValueLength (cls, value):
        return len(value)

    @classmethod
    def XsdLiteral (cls, value):
        return six.text_type(value)

_PrimitiveDatatypes.append(anyURI)

class QName (basis.simpleTypeDefinition, pyxb.namespace.ExpandedName):
    """XMLSchema datatype U{QName<http://www.w3.org/TR/xmlschema-2/#QName>}."""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('QName')

    @classmethod
    def XsdValueLength (cls, value):
        """Section 4.3.1.3: Legacy length return None to indicate no check"""
        return None

    @classmethod
    def _ConvertIf (cls, value, xmlns_context):
        if isinstance(value, pyxb.namespace.ExpandedName):
            assert 0 > value.localName().find(':')
            return value
        if not isinstance(value, six.string_types):
            raise SimpleTypeValueError(cls, value)
        if 0 <= value.find(':'):
            (prefix, local) = value.split(':', 1)
            if (NCName._ValidRE.match(prefix) is None) or (NCName._ValidRE.match(local) is None):
                raise SimpleTypeValueError(cls, value)
            if xmlns_context is None:
                raise pyxb.QNameResolutionError('QName resolution requires namespace context', value, xmlns_context)
            return xmlns_context.interpretQName(value, default_no_namespace=True)
        if NCName._ValidRE.match(value) is None:
            raise SimpleTypeValueError(cls, value)
        if xmlns_context is not None:
            return xmlns_context.interpretQName(value, default_no_namespace=True)
        return pyxb.namespace.ExpandedName(value)

    @classmethod
    def _ConvertArguments_vx (cls, args, kw):
        if 1 == len(args):
            xmlns_context = kw.pop('_xmlns_context', pyxb.namespace.NamespaceContext.Current())
            args = (cls._ConvertIf(args[0], xmlns_context),)
        super_fn = getattr(super(QName, cls), '_ConvertArguments_vx', lambda *a,**kw: args)
        return super_fn(args, kw)

    @classmethod
    def XsdLiteral (cls, value):
        # A QName has no unicode/XSD representation in the absence of
        # a registered namespace.  Whatever called this should have
        # detected that the value is a QName and used
        # BindingDOMSupport.qnameToText() to convert it to a lexical
        # representation that incorporates a declared namespace.
        raise pyxb.UsageError('Cannot represent QName without namespace declaration')

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        super_fn = getattr(super(QName, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: True)
        return super_fn(cls._ConvertIf(value, pyxb.namespace.NamespaceContext.Current()))


_PrimitiveDatatypes.append(QName)

class NOTATION (basis.simpleTypeDefinition):
    """XMLSchema datatype U{NOTATION<http://www.w3.org/TR/xmlschema-2/#NOTATION>}."""
    _XsdBaseType = anySimpleType
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('NOTATION')

    @classmethod
    def XsdValueLength (cls, value):
        """Section 4.3.1.3: Legacy length return None to indicate no check"""
        return None

_PrimitiveDatatypes.append(NOTATION)

class normalizedString (string):
    """XMLSchema datatype U{normalizedString<http:///www.w3.org/TR/xmlschema-2/#normalizedString>}.

    Normalized strings can't have carriage returns, linefeeds, or
    tabs in them."""

    # All descendents of normalizedString constrain the lexical/value
    # space in some way.  Subclasses should set the _ValidRE class
    # variable to a compiled regular expression that matches valid
    # input, or the _InvalidRE class variable to a compiled regular
    # expression that detects invalid inputs.
    #
    # Alternatively, subclasses can override the _ValidateString_va
    # method.

    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('normalizedString')

    # @todo Implement pattern constraints and just rely on them

    # No CR, LF, or TAB
    __BadChars = re.compile("[\r\n\t]")

    _ValidRE = None
    _InvalidRE = None

    @classmethod
    def __ValidateString (cls, value):
        # This regular expression doesn't work.  Don't know why.
        #if cls.__BadChars.match(value) is not None:
        #    raise SimpleTypeValueError('CR/NL/TAB characters illegal in %s' % (cls.__name__,))
        if (0 <= value.find("\n")) or (0 <= value.find("\r")) or (0 <= value.find("\t")):
            raise SimpleTypeValueError(cls, value)
        if cls._ValidRE is not None:
            match_object = cls._ValidRE.match(value)
            if match_object is None:
                raise SimpleTypeValueError(cls, value)
        if cls._InvalidRE is not None:
            match_object = cls._InvalidRE.match(value)
            if not (match_object is None):
                raise SimpleTypeValueError(cls, value)
        return True

    @classmethod
    def _ValidateString_va (cls, value):
        """Post-extended method to validate that a string matches a given pattern.

        If you can express the valid strings as a compiled regular
        expression in the class variable _ValidRE, or the invalid
        strings as a compiled regular expression in the class variable
        _InvalidRE, you can just use those.  If the acceptable matches
        are any trickier, you should invoke the superclass
        implementation, and if it returns True then perform additional
        tests."""
        super_fn = getattr(super(normalizedString, cls), '_ValidateString_va', lambda *a,**kw: True)
        if not super_fn(value):
            return False
        return cls.__ValidateString(value)

    @classmethod
    def _XsdConstraintsPreCheck_vb (cls, value):
        if not isinstance(value, six.string_types):
            raise SimpleTypeValueError(cls, value)
        if not cls._ValidateString_va(value):
            raise SimpleTypeValueError(cls, value)
        super_fn = getattr(super(normalizedString, cls), '_XsdConstraintsPreCheck_vb', lambda *a,**kw: True)
        return super_fn(value)

_DerivedDatatypes.append(normalizedString)
assert normalizedString.XsdSuperType() == string

class token (normalizedString):
    """XMLSchema datatype U{token<http:///www.w3.org/TR/xmlschema-2/#token>}.

    Tokens cannot leading or trailing space characters; any
    carriage return, line feed, or tab characters; nor any occurrence
    of two or more consecutive space characters."""

    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('token')

    @classmethod
    def _ValidateString_va (cls, value):
        super_fn = getattr(super(token, cls), '_ValidateString_va', lambda *a,**kw: True)
        if not super_fn(value):
            return False
        if value.startswith(" ") \
           or value.endswith(" ") \
           or (0 <= value.find('  ')):
            raise SimpleTypeValueError(cls, value)
        return True
_DerivedDatatypes.append(token)

class language (token):
    """XMLSchema datatype U{language<http:///www.w3.org/TR/xmlschema-2/#language>}"""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('language')
    _ValidRE = re.compile('^[a-zA-Z]{1,8}(-[a-zA-Z0-9]{1,8})*$')
_DerivedDatatypes.append(language)

class NMTOKEN (token):
    """XMLSchema datatype U{NMTOKEN<http:///www.w3.org/TR/xmlschema-2/#NMTOKEN>}.

    See U{http://www.w3.org/TR/2000/WD-xml-2e-20000814.html#NT-Nmtoken}.

    NMTOKEN is an identifier that can start with any character that is
    legal in it."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('NMTOKEN')
    _ValidRE = pyxb.utils.unicode.XML1p0e2.NmToken_re
_DerivedDatatypes.append(NMTOKEN)

class NMTOKENS (basis.STD_list):
    _ItemType = NMTOKEN
_ListDatatypes.append(NMTOKENS)

class Name (token):
    """XMLSchema datatype U{Name<http:///www.w3.org/TR/xmlschema-2/#Name>}.

    See U{http://www.w3.org/TR/2000/WD-xml-2e-20000814.html#NT-Name}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('Name')
    _ValidRE = pyxb.utils.unicode.XML1p0e2.Name_re
_DerivedDatatypes.append(Name)

class NCName (Name):
    """XMLSchema datatype U{NCName<http:///www.w3.org/TR/xmlschema-2/#NCName>}.

    See U{http://www.w3.org/TR/1999/REC-xml-names-19990114/#NT-NCName}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('NCName')
    _ValidRE = pyxb.utils.unicode.XML1p0e2.NCName_re
_DerivedDatatypes.append(NCName)

class ID (NCName):
    """XMLSchema datatype U{ID<http:///www.w3.org/TR/xmlschema-2/#ID>}."""
    # Lexical and value space match that of parent NCName
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('ID')
    pass
_DerivedDatatypes.append(ID)

class IDREF (NCName):
    """XMLSchema datatype U{IDREF<http:///www.w3.org/TR/xmlschema-2/#IDREF>}."""
    # Lexical and value space match that of parent NCName
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('IDREF')
    pass
_DerivedDatatypes.append(IDREF)

class IDREFS (basis.STD_list):
    """XMLSchema datatype U{IDREFS<http:///www.w3.org/TR/xmlschema-2/#IDREFS>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('IDREFS')
    _ItemType = IDREF
_ListDatatypes.append(IDREFS)

class ENTITY (NCName):
    """XMLSchema datatype U{ENTITY<http:///www.w3.org/TR/xmlschema-2/#ENTITY>}."""
    # Lexical and value space match that of parent NCName; we're gonna
    # ignore the additional requirement that it be declared as an
    # unparsed entity
    #
    # @todo Don't ignore the requirement that this be declared as an
    # unparsed entity.
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('ENTITY')
    pass
_DerivedDatatypes.append(ENTITY)

class ENTITIES (basis.STD_list):
    """XMLSchema datatype U{ENTITIES<http:///www.w3.org/TR/xmlschema-2/#ENTITIES>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('ENTITIES')
    _ItemType = ENTITY
_ListDatatypes.append(ENTITIES)

class integer (basis.simpleTypeDefinition, six.long_type):
    """XMLSchema datatype U{integer<http://www.w3.org/TR/xmlschema-2/#integer>}."""
    _XsdBaseType = decimal
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('integer')

    @classmethod
    def XsdLiteral (cls, value):
        return '%d' % (value,)

_DerivedDatatypes.append(integer)

class nonPositiveInteger (integer):
    """XMLSchema datatype U{nonPositiveInteger<http://www.w3.org/TR/xmlschema-2/#nonPositiveInteger>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('nonPositiveInteger')
_DerivedDatatypes.append(nonPositiveInteger)

class negativeInteger (nonPositiveInteger):
    """XMLSchema datatype U{negativeInteger<http://www.w3.org/TR/xmlschema-2/#negativeInteger>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('negativeInteger')
_DerivedDatatypes.append(negativeInteger)

class long (integer):
    """XMLSchema datatype U{long<http://www.w3.org/TR/xmlschema-2/#long>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('long')
_DerivedDatatypes.append(long)

class int (basis.simpleTypeDefinition, six.int_type):
    """XMLSchema datatype U{int<http://www.w3.org/TR/xmlschema-2/#int>}."""
    _XsdBaseType = long
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('int')

    @classmethod
    def XsdLiteral (cls, value):
        return '%s' % (value,)

    pass
_DerivedDatatypes.append(int)

class short (int):
    """XMLSchema datatype U{short<http://www.w3.org/TR/xmlschema-2/#short>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('short')
_DerivedDatatypes.append(short)

class byte (short):
    """XMLSchema datatype U{byte<http://www.w3.org/TR/xmlschema-2/#byte>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('byte')
_DerivedDatatypes.append(byte)

class nonNegativeInteger (integer):
    """XMLSchema datatype U{nonNegativeInteger<http://www.w3.org/TR/xmlschema-2/#nonNegativeInteger>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('nonNegativeInteger')
_DerivedDatatypes.append(nonNegativeInteger)

class unsignedLong (nonNegativeInteger):
    """XMLSchema datatype U{unsignedLong<http://www.w3.org/TR/xmlschema-2/#unsignedLong>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('unsignedLong')
_DerivedDatatypes.append(unsignedLong)

class unsignedInt (unsignedLong):
    """XMLSchema datatype U{unsignedInt<http://www.w3.org/TR/xmlschema-2/#unsignedInt>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('unsignedInt')
_DerivedDatatypes.append(unsignedInt)

class unsignedShort (unsignedInt):
    """XMLSchema datatype U{unsignedShort<http://www.w3.org/TR/xmlschema-2/#unsignedShort>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('unsignedShort')
_DerivedDatatypes.append(unsignedShort)

class unsignedByte (unsignedShort):
    """XMLSchema datatype U{unsignedByte<http://www.w3.org/TR/xmlschema-2/#unsignedByte>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('unsignedByte')
_DerivedDatatypes.append(unsignedByte)

class positiveInteger (nonNegativeInteger):
    """XMLSchema datatype U{positiveInteger<http://www.w3.org/TR/xmlschema-2/#positiveInteger>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('positiveInteger')
_DerivedDatatypes.append(positiveInteger)

from . import content

class anyType (basis.complexTypeDefinition):
    """XMLSchema datatype U{anyType<http://www.w3.org/TR/2001/REC-xmlschema-1-20010502/#key-urType>}."""
    _ExpandedName = pyxb.namespace.XMLSchema.createExpandedName('anyType')
    _DefinitionLocation = pyxb.utils.utility.Location('http://www.w3.org/TR/2001/REC-xmlschema-1-20010502/#key-urType', 1, 1)
    _ContentTypeTag = basis.complexTypeDefinition._CT_MIXED
    _Abstract = False
    _HasWildcardElement = True
    _AttributeWildcard = content.Wildcard(namespace_constraint=content.Wildcard.NC_any, process_contents=content.Wildcard.PC_lax)

def _BuildAutomaton ():
    # Remove this helper function from the namespace after it's invoked
    global _BuildAutomaton
    del _BuildAutomaton
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=None, metadata=pyxb.utils.utility.Location('http://www.w3.org/TR/2001/REC-xmlschema-1-20010502/#key-urType', 1, 1))
    counters.add(cc_0)
    states = set()
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = content.WildcardUse(content.Wildcard(process_contents=content.Wildcard.PC_lax, namespace_constraint=content.Wildcard.NC_any), None)
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.add(st_0)
    transitions = set()
    transitions.add(fac.Transition(st_0, [
        fac.UpdateInstruction(cc_0, True) ]))
    st_0._set_transitionSet(transitions)
    return fac.Automaton(states, counters, True, containing_state=None)
anyType._Automaton = _BuildAutomaton()


# anyType._IsUrType() is True; foo._IsUrType() for descendents of it
# should be false.
anyType._IsUrType = classmethod(lambda _c: _c == anyType)
