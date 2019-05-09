# -*- coding: utf-8 -*-
"""Python phone number parsing and formatting library

If you use this library, and want to be notified about important changes,
please sign up to the libphonenumber mailing list at
https://groups.google.com/forum/#!aboutgroup/libphonenumber-discuss.

NOTE: A lot of methods in this module require Region Code strings. These must
be provided using CLDR two-letter region-code format. These should be in
upper-case. The list of the codes can be found here:
http://www.iso.org/iso/country_codes/iso_3166_code_lists/country_names_and_code_elements.htm
"""
# Based on original Java code:
#     java/src/com/google/i18n/phonenumbers/PhoneNumberUtil.java
#   Copyright (C) 2009-2011 The Libphonenumber Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import sys
import re

from .re_util import fullmatch   # Extra regexp function; see README
from .util import UnicodeMixin, u, unicod, prnt, to_long
from .util import U_EMPTY_STRING, U_SPACE, U_DASH, U_TILDE, U_ZERO, U_SEMICOLON
from .unicode_util import digit as unicode_digit

# Data class definitions
from .phonenumber import PhoneNumber, CountryCodeSource
from .phonemetadata import NumberFormat, PhoneMetadata, REGION_CODE_FOR_NON_GEO_ENTITY

# Import auto-generated data structures
try:
    from .data import _COUNTRY_CODE_TO_REGION_CODE
except ImportError:  # pragma no cover
    # Before the generated code exists, the data/ directory is empty.
    # The generation process imports this module, creating a circular
    # dependency.  The hack below works around this.
    import os
    if (os.path.basename(sys.argv[0]) == "buildmetadatafromxml.py" or
        os.path.basename(sys.argv[0]) == "buildprefixdata.py"):
        prnt("Failed to import generated data (but OK as during autogeneration)", file=sys.stderr)
        _COUNTRY_CODE_TO_REGION_CODE = {1: ("US",)}
    else:
        raise

# Set the master map from country code to region code.  The
# extra level of indirection allows the unit test to replace
# the map with test data.
COUNTRY_CODE_TO_REGION_CODE = _COUNTRY_CODE_TO_REGION_CODE

# Naming convention for phone number arguments and variables:
#  - string arguments are named 'number'
#  - PhoneNumber objects are named 'numobj'

# Flags to use when compiling regular expressions for phone numbers.
_REGEX_FLAGS = re.UNICODE | re.IGNORECASE
# The minimum and maximum length of the national significant number.
_MIN_LENGTH_FOR_NSN = 2
# The ITU says the maximum length should be 15, but we have found longer
# numbers in Germany.
_MAX_LENGTH_FOR_NSN = 17
# The maximum length of the country calling code.
_MAX_LENGTH_COUNTRY_CODE = 3
# We don't allow input strings for parsing to be longer than 250 chars. This
# prevents malicious input from overflowing the regular-expression engine.
_MAX_INPUT_STRING_LENGTH = 250
# Region-code for the unknown region.
UNKNOWN_REGION = u("ZZ")
# The set of regions that share country calling code 1.
_NANPA_COUNTRY_CODE = 1
# The prefix that needs to be inserted in front of a Colombian landline number
# when dialed from a mobile phone in Colombia.
_COLOMBIA_MOBILE_TO_FIXED_LINE_PREFIX = unicod("3")
# Map of country calling codes that use a mobile token before the area
# code. One example of when this is relevant is when determining the length of
# the national destination code, which should be the length of the area code
# plus the length of the mobile token.
_MOBILE_TOKEN_MAPPINGS = {52: u('1'), 54: u('9')}
# Set of country codes that have geographically assigned mobile numbers (see
# GEO_MOBILE_COUNTRIES below) which are not based on *area codes*. For example,
# in China mobile numbers start with a carrier indicator, and beyond that are
# geographically assigned: this carrier indicator is not considered to be an
# area code.
_GEO_MOBILE_COUNTRIES_WITHOUT_MOBILE_AREA_CODES = frozenset((
    86,))  # China
# Set of country calling codes that have geographically assigned mobile
# numbers. This may not be complete; we add calling codes case by case, as we
# find geographical mobile numbers or hear from user reports.  Note that
# countries like the US, where we can't distinguish between fixed-line or
# mobile numbers, are not listed here, since we consider FIXED_LINE_OR_MOBILE
# to be a possibly geographically-related type anyway (like FIXED_LINE).
_GEO_MOBILE_COUNTRIES = _GEO_MOBILE_COUNTRIES_WITHOUT_MOBILE_AREA_CODES | set((
    52,  # Mexico
    54,  # Argentina
    55,  # Brazil
    62))  # Indonesia: some prefixes only (fixed CMDA wireless)
# The PLUS_SIGN signifies the international prefix.
_PLUS_SIGN = u("+")
_STAR_SIGN = u('*')
_RFC3966_EXTN_PREFIX = u(";ext=")
_RFC3966_PREFIX = u("tel:")
_RFC3966_PHONE_CONTEXT = u(";phone-context=")
_RFC3966_ISDN_SUBADDRESS = u(";isub=")

# Simple ASCII digits map used to populate _ALPHA_PHONE_MAPPINGS and
# _ALL_PLUS_NUMBER_GROUPING_SYMBOLS.
_ASCII_DIGITS_MAP = {u("0"): u("0"), u("1"): u("1"),
                     u("2"): u("2"), u("3"): u("3"),
                     u("4"): u("4"), u("5"): u("5"),
                     u("6"): u("6"), u("7"): u("7"),
                     u("8"): u("8"), u("9"): u("9")}

# Only upper-case variants of alpha characters are stored.
_ALPHA_MAPPINGS = {u("A"): u("2"),
                   u("B"): u("2"),
                   u("C"): u("2"),
                   u("D"): u("3"),
                   u("E"): u("3"),
                   u("F"): u("3"),
                   u("G"): u("4"),
                   u("H"): u("4"),
                   u("I"): u("4"),
                   u("J"): u("5"),
                   u("K"): u("5"),
                   u("L"): u("5"),
                   u("M"): u("6"),
                   u("N"): u("6"),
                   u("O"): u("6"),
                   u("P"): u("7"),
                   u("Q"): u("7"),
                   u("R"): u("7"),
                   u("S"): u("7"),
                   u("T"): u("8"),
                   u("U"): u("8"),
                   u("V"): u("8"),
                   u("W"): u("9"),
                   u("X"): u("9"),
                   u("Y"): u("9"),
                   u("Z"): u("9"), }
# For performance reasons, amalgamate both into one map.
_ALPHA_PHONE_MAPPINGS = dict(_ALPHA_MAPPINGS, **_ASCII_DIGITS_MAP)

# A map that contains characters that are essential when dialling. That means
# any of the characters in this map must not be removed from a number when
# dialling, otherwise the call will not reach the intended destination.
_DIALLABLE_CHAR_MAPPINGS = dict({_PLUS_SIGN: _PLUS_SIGN,
                                 u('*'): u('*'),
                                 u('#'): u('#')},
                                **_ASCII_DIGITS_MAP)

# Separate map of all symbols that we wish to retain when formatting alpha
# numbers. This includes digits, ASCII letters and number grouping symbols
# such as "-" and " ".
_ALL_PLUS_NUMBER_GROUPING_SYMBOLS = dict({u("-"): u("-"),  # Add grouping symbols.
                                          u("\uFF0D"): u("-"),
                                          u("\u2010"): u("-"),
                                          u("\u2011"): u("-"),
                                          u("\u2012"): u("-"),
                                          u("\u2013"): u("-"),
                                          u("\u2014"): u("-"),
                                          u("\u2015"): u("-"),
                                          u("\u2212"): u("-"),
                                          u("/"): u("/"),
                                          u("\uFF0F"): u("/"),
                                          u(" "): u(" "),
                                          u("\u3000"): u(" "),
                                          u("\u2060"): u(" "),
                                          u("."): u("."),
                                          u("\uFF0E"): u(".")},
                                         # Put (lower letter -> upper letter) and
                                         # (upper letter -> upper letter) mappings.
                                         **dict([(_c.lower(), _c) for _c in _ALPHA_MAPPINGS.keys()] +
                                                [(_c, _c) for _c in _ALPHA_MAPPINGS.keys()],
                                                **_ASCII_DIGITS_MAP))

# Pattern that makes it easy to distinguish whether a region has a single international dialing
# prefix or not. If a region has a single international prefix (e.g. 011 in USA), it will be
# represented as a string that contains a sequence of ASCII digits, and possibly a tilde, which
# signals waiting for the tone. If there are multiple available international prefixes in a
# region, they will be represented as a regex string that always contains one or more characters
# that are not ASCII digits or a tilde.
_SINGLE_INTERNATIONAL_PREFIX = re.compile(u("[\\d]+(?:[~\u2053\u223C\uFF5E][\\d]+)?"))

# Regular expression of acceptable punctuation found in phone numbers. This
# excludes punctuation found as a leading character only.

# Regular expression of acceptable punctuation found in phone numbers, used to find numbers in
# text and to decide what is a viable phone number. This excludes diallable characters.
# This consists of dash characters, white space characters, full stops, slashes, square brackets,
# parentheses and tildes. It also includes the letter 'x' as that is found as a placeholder for
# carrier information in some phone numbers. Full-width variants are also present.
_VALID_PUNCTUATION = (u("-x\u2010-\u2015\u2212\u30FC\uFF0D-\uFF0F ") +
                      u("\u00A0\u00AD\u200B\u2060\u3000()\uFF08\uFF09\uFF3B\uFF3D.\\[\\]/~\u2053\u223C\uFF5E"))

_DIGITS = unicod('\\d')  # Java "\\p{Nd}", so need "(?u)" or re.UNICODE wherever this is used
# We accept alpha characters in phone numbers, ASCII only, upper and lower
# case.
_VALID_ALPHA = (U_EMPTY_STRING.join(_ALPHA_MAPPINGS.keys()) +
                U_EMPTY_STRING.join([_k.lower() for _k in _ALPHA_MAPPINGS.keys()]))
_PLUS_CHARS = u("+\uFF0B")
_PLUS_CHARS_PATTERN = re.compile(u("[") + _PLUS_CHARS + u("]+"))
_SEPARATOR_PATTERN = re.compile(u("[") + _VALID_PUNCTUATION + u("]+"))
_CAPTURING_DIGIT_PATTERN = re.compile(u("(") + _DIGITS + u(")"), re.UNICODE)

# Regular expression of acceptable characters that may start a phone number
# for the purposes of parsing. This allows us to strip away meaningless
# prefixes to phone numbers that may be mistakenly given to us. This consists
# of digits, the plus symbol and arabic-indic digits. This does not contain
# alpha characters, although they may be used later in the number. It also
# does not include other punctuation, as this will be stripped later during
# parsing and is of no information value when parsing a number.
_VALID_START_CHAR = u("[") + _PLUS_CHARS + _DIGITS + u("]")
_VALID_START_CHAR_PATTERN = re.compile(_VALID_START_CHAR, re.UNICODE)

# Regular expression of characters typically used to start a second phone
# number for the purposes of parsing. This allows us to strip off parts of the
# number that are actually the start of another number, such as for: (530)
# 583-6985 x302/x2303 -> the second extension here makes this actually two
# phone numbers, (530) 583-6985 x302 and (530) 583-6985 x2303. We remove the
# second extension so that the first number is parsed correctly.
_SECOND_NUMBER_START = u("[\\\\/] *x")
_SECOND_NUMBER_START_PATTERN = re.compile(_SECOND_NUMBER_START)

# Regular expression of trailing characters that we want to remove. We remove
# all characters that are not alpha or numerical characters. The hash
# character is retained here, as it may signify the previous block was an
# extension.
#
# The original Java regexp is:
#   [[\\P{N}&&\\P{L}]&&[^#]]+$
# which splits out as:
#   [                      ]+$  : >=1 of the following chars at end of string
#    [              ]&&[  ]     : intersection of these two sets of chars
#    [      &&      ]           : intersection of these two sets of chars
#     \\P{N}                    : characters without the "Number" Unicode property
#              \\P{L}           : characters without the "Letter" Unicode property
#                      [^#]     : character other than hash
# which nets down to: >=1 non-Number, non-Letter, non-# characters at string end
# In Python Unicode regexp mode '(?u)', the class '[^#\w]' will match anything
# that is not # and is not alphanumeric and is not underscore.
_UNWANTED_END_CHARS = u(r"(?u)(?:_|[^#\w])+$")
_UNWANTED_END_CHAR_PATTERN = re.compile(_UNWANTED_END_CHARS)

# We use this pattern to check if the phone number has at least three letters
# in it - if so, then we treat it as a number where some phone-number digits
# are represented by letters.
_VALID_ALPHA_PHONE_PATTERN = re.compile(u("(?:.*?[A-Za-z]){3}.*"))

# Regular expression of viable phone numbers. This is location
# independent. Checks we have at least three leading digits, and only valid
# punctuation, alpha characters and digits in the phone number. Does not
# include extension data.  The symbol 'x' is allowed here as valid punctuation
# since it is often used as a placeholder for carrier codes, for example in
# Brazilian phone numbers. We also allow multiple "+" characters at the start.
# Corresponds to the following:
# [digits]{minLengthNsn}|
# plus_sign*(([punctuation]|[star])*[digits]){3,}([punctuation]|[star]|[digits]|[alpha])*
#
# The first reg-ex is to allow short numbers (two digits long) to be parsed if
# they are entered as "15" etc, but only if there is no punctuation in
# them. The second expression restricts the number of digits to three or more,
# but then allows them to be in international form, and to have
# alpha-characters and punctuation.
#
# Note VALID_PUNCTUATION starts with a -, so must be the first in the range.
_VALID_PHONE_NUMBER = (_DIGITS + (u("{%d}") % _MIN_LENGTH_FOR_NSN) + u("|") +
                       u("[") + _PLUS_CHARS + u("]*(?:[") + _VALID_PUNCTUATION + _STAR_SIGN + u("]*") + _DIGITS + u("){3,}[") +
                       _VALID_PUNCTUATION + _STAR_SIGN + _VALID_ALPHA + _DIGITS + u("]*"))

# Default extension prefix to use when formatting. This will be put in front
# of any extension component of the number, after the main national number is
# formatted. For example, if you wish the default extension formatting to be
# " extn: 3456", then you should specify " extn: " here as the default
# extension prefix. This can be overridden by region-specific preferences.
_DEFAULT_EXTN_PREFIX = u(" ext. ")

# Pattern to capture digits used in an extension. Places a maximum length of
# "7" for an extension.
_CAPTURING_EXTN_DIGITS = u("(") + _DIGITS + u("{1,7})")

# Regexp of all possible ways to write extensions, for use when parsing. This
# will be run as a case-insensitive regexp match. Wide character versions are
# also provided after each ASCII version.

# One-character symbols that can be used to indicate an extension.
_SINGLE_EXTN_SYMBOLS_FOR_MATCHING = u("x\uFF58#\uFF03~\uFF5E")
# For parsing, we are slightly more lenient in our interpretation than for
# matching. Here we allow "comma" and "semicolon" as a possible extension
# indicator. When matching, these are hardly ever used to indicate this.
_SINGLE_EXTN_SYMBOLS_FOR_PARSING = u(",;") + _SINGLE_EXTN_SYMBOLS_FOR_MATCHING


def _create_extn_pattern(single_extn_symbols):
    """Helper initialiser method to create the regular-expression pattern to
    match extensions, allowing the one-char extension symbols provided by
    single_extn_symbols."""
    # There are three regular expressions here. The first covers RFC 3966
    # format, where the extension is added using ";ext=". The second more
    # generic one starts with optional white space and ends with an optional
    # full stop (.), followed by zero or more spaces/tabs/commas and then the
    # numbers themselves. The other one covers the special case of American
    # numbers where the extension is written with a hash at the end, such as
    # "- 503#".  Note that the only capturing groups should be around the
    # digits that you want to capture as part of the extension, or else
    # parsing will fail!  Canonical-equivalence doesn't seem to be an option
    # with Android java, so we allow two options for representing the accented
    # o - the character itself, and one in the unicode decomposed form with
    # the combining acute accent.
    return (_RFC3966_EXTN_PREFIX + _CAPTURING_EXTN_DIGITS + u("|") +
            u("[ \u00A0\\t,]*(?:e?xt(?:ensi(?:o\u0301?|\u00F3))?n?|") +
            u("\uFF45?\uFF58\uFF54\uFF4E?|") +
            u("\u0434\u043e\u0431|") + u("[") + single_extn_symbols + u("]|int|anexo|\uFF49\uFF4E\uFF54)") +
            u("[:\\.\uFF0E]?[ \u00A0\\t,-]*") + _CAPTURING_EXTN_DIGITS + u("#?|") +
            u("[- ]+(") + _DIGITS + u("{1,5})#"))


_EXTN_PATTERNS_FOR_PARSING = _create_extn_pattern(_SINGLE_EXTN_SYMBOLS_FOR_PARSING)
_EXTN_PATTERNS_FOR_MATCHING = _create_extn_pattern(_SINGLE_EXTN_SYMBOLS_FOR_MATCHING)

# Regexp of all known extension prefixes used by different regions followed by
# 1 or more valid digits, for use when parsing.
_EXTN_PATTERN = re.compile(u("(?:") + _EXTN_PATTERNS_FOR_PARSING + u(")$"), _REGEX_FLAGS)

# We append optionally the extension pattern to the end here, as a valid phone
# number may have an extension prefix appended, followed by 1 or more digits.
_VALID_PHONE_NUMBER_PATTERN = re.compile(_VALID_PHONE_NUMBER + u("(?:") + _EXTN_PATTERNS_FOR_PARSING + u(")?"), _REGEX_FLAGS)

# We use a non-capturing group because Python's re.split() returns any capturing
# groups interspersed with the other results (unlike Java's Pattern.split()).
NON_DIGITS_PATTERN = re.compile(u("(?:\\D+)"))

# The FIRST_GROUP_PATTERN was originally set to \1 but there are some
# countries for which the first group is not used in the national pattern
# (e.g. Argentina) so the \1 group does not match correctly.  Therefore, we
# use \d, so that the first group actually used in the pattern will be
# matched.
_FIRST_GROUP_PATTERN = re.compile(u(r"(\\\d)"))
# Constants used in the formatting rules to represent the national prefix, first group and
# carrier code respectively.
_NP_STRING = "$NP"
_FG_STRING = "$FG"
_CC_STRING = "$CC"

# A pattern that is used to determine if the national prefix formatting rule
# has the first group only, i.e., does not start with the national
# prefix. Note that the pattern explicitly allows for unbalanced parentheses.
_FIRST_GROUP_ONLY_PREFIX_PATTERN = re.compile("\\(?\\\\1\\)?")


class PhoneNumberFormat(object):
    """
    Phone number format.

    INTERNATIONAL and NATIONAL formats are consistent with the definition in
    ITU-T Recommendation E123. However we follow local conventions such as using
    '-' instead of whitespace as separators. For example, the number of the
    Google Switzerland office will be written as "+41 44 668 1800" in
    INTERNATIONAL format, and as "044 668 1800" in NATIONAL format. E164 format
    is as per INTERNATIONAL format but with no formatting applied,
    e.g. "+41446681800". RFC3966 is as per INTERNATIONAL format, but with all
    spaces and other separating symbols replaced with a hyphen, and with any
    phone number extension appended with ";ext=". It also will have a prefix of
    "tel:" added, e.g. "tel:+41-44-668-1800".

    Note: If you are considering storing the number in a neutral format, you
    are highly advised to use the PhoneNumber class.
    """
    E164 = 0
    INTERNATIONAL = 1
    NATIONAL = 2
    RFC3966 = 3


class PhoneNumberType(object):
    """Type of phone numbers."""
    FIXED_LINE = 0
    MOBILE = 1
    # In some regions (e.g. the USA), it is impossible to distinguish between
    # fixed-line and mobile numbers by looking at the phone number itself.
    FIXED_LINE_OR_MOBILE = 2
    # Freephone lines
    TOLL_FREE = 3
    PREMIUM_RATE = 4
    # The cost of this call is shared between the caller and the recipient,
    # and is hence typically less than PREMIUM_RATE calls. See
    # http://en.wikipedia.org/wiki/Shared_Cost_Service for more information.
    SHARED_COST = 5
    # Voice over IP numbers. This includes TSoIP (Telephony Service over IP).
    VOIP = 6
    # A personal number is associated with a particular person, and may be
    # routed to either a MOBILE or FIXED_LINE number. Some more information
    # can be found here: http://en.wikipedia.org/wiki/Personal_Numbers
    PERSONAL_NUMBER = 7
    PAGER = 8
    # Used for "Universal Access Numbers" or "Company Numbers". They may be
    # further routed to specific offices, but allow one number to be used for
    # a company.
    UAN = 9
    # Used for "Voice Mail Access Numbers".
    VOICEMAIL = 10
    # A phone number is of type UNKNOWN when it does not fit any of the known
    # patterns for a specific region.
    UNKNOWN = 99

    @classmethod
    def values(cls):
        return (PhoneNumberType.FIXED_LINE,
                PhoneNumberType.MOBILE,
                PhoneNumberType.FIXED_LINE_OR_MOBILE,
                PhoneNumberType.TOLL_FREE,
                PhoneNumberType.PREMIUM_RATE,
                PhoneNumberType.SHARED_COST,
                PhoneNumberType.VOIP,
                PhoneNumberType.PERSONAL_NUMBER,
                PhoneNumberType.PAGER,
                PhoneNumberType.UAN,
                PhoneNumberType.VOICEMAIL,
                PhoneNumberType.UNKNOWN)


class MatchType(object):
    """Types of phone number matches."""
    # Not a telephone number
    NOT_A_NUMBER = 0
    # None of the match types below apply
    NO_MATCH = 1
    # Returns SHORT_NSN_MATCH if either or both has no region specified, or
    # the region specified is the same, and one NSN could be a shorter version
    # of the other number. This includes the case where one has an extension
    # specified, and the other does not.
    SHORT_NSN_MATCH = 2
    # Either or both has no region specified, and the NSNs and extensions are
    # the same.
    NSN_MATCH = 3
    # The country_code, NSN, presence of a leading zero for Italian numbers
    # and any extension present are the same.
    EXACT_MATCH = 4


class ValidationResult(object):
    """Possible outcomes when testing if a PhoneNumber is a possible number."""
    # The number length matches that of valid numbers for this region.
    IS_POSSIBLE = 0
    # The number length matches that of local numbers for this region only
    # (i.e. numbers that may be able to be dialled within an area, but do not
    # have all the information to be dialled from anywhere inside or outside
    # the country).
    IS_POSSIBLE_LOCAL_ONLY = 4
    # The number has an invalid country calling code.
    INVALID_COUNTRY_CODE = 1
    # The number is shorter than all valid numbers for this region.
    TOO_SHORT = 2
    # The number is longer than the shortest valid numbers for this region,
    # shorter than the longest valid numbers for this region, and does not
    # itself have a number length that matches valid numbers for this region.
    # This can also be returned in the case where
    # is_possible_number_for_type_with_reason was called, and there are no
    # numbers of this type at all for this region.
    INVALID_LENGTH = 5
    # The number is longer than all valid numbers for this region.
    TOO_LONG = 3


# Derived data structures
SUPPORTED_REGIONS = set()
COUNTRY_CODES_FOR_NON_GEO_REGIONS = set()
_NANPA_REGIONS = set()


def _regenerate_derived_data():
    global SUPPORTED_REGIONS, COUNTRY_CODES_FOR_NON_GEO_REGIONS, _NANPA_REGIONS
    SUPPORTED_REGIONS.clear()
    COUNTRY_CODES_FOR_NON_GEO_REGIONS.clear()
    for cc, region_codes in COUNTRY_CODE_TO_REGION_CODE.items():
        if (len(region_codes) == 1 and region_codes[0] == REGION_CODE_FOR_NON_GEO_ENTITY):
            COUNTRY_CODES_FOR_NON_GEO_REGIONS.add(cc)
        else:
            SUPPORTED_REGIONS.update(region_codes)
    if REGION_CODE_FOR_NON_GEO_ENTITY in SUPPORTED_REGIONS:  # pragma no cover
        SUPPORTED_REGIONS.remove(REGION_CODE_FOR_NON_GEO_ENTITY)
    _NANPA_REGIONS.clear()
    _NANPA_REGIONS.update(COUNTRY_CODE_TO_REGION_CODE[_NANPA_COUNTRY_CODE])


_regenerate_derived_data()


def _copy_number_format(other):
    """Return a mutable copy of the given NumberFormat object"""
    copy = NumberFormat(pattern=other.pattern,
                        format=other.format,
                        leading_digits_pattern=list(other.leading_digits_pattern),
                        national_prefix_formatting_rule=other.national_prefix_formatting_rule,
                        national_prefix_optional_when_formatting=other.national_prefix_optional_when_formatting,
                        domestic_carrier_code_formatting_rule=other.domestic_carrier_code_formatting_rule)
    copy._mutable = True
    return copy


def _extract_possible_number(number):
    """Attempt to extract a possible number from the string passed in.

    This currently strips all leading characters that cannot be used to
    start a phone number. Characters that can be used to start a phone number
    are defined in the VALID_START_CHAR_PATTERN. If none of these characters
    are found in the number passed in, an empty string is returned. This
    function also attempts to strip off any alternative extensions or endings
    if two or more are present, such as in the case of: (530) 583-6985
    x302/x2303. The second extension here makes this actually two phone
    numbers, (530) 583-6985 x302 and (530) 583-6985 x2303. We remove the
    second extension so that the first number is parsed correctly.

    Arguments:
    number -- The string that might contain a phone number.

    Returns the number, stripped of any non-phone-number prefix (such
    as "Tel:") or an empty string if no character used to start phone
    numbers (such as + or any digit) is found in the number
    """
    match = _VALID_START_CHAR_PATTERN.search(number)
    if match:
        number = number[match.start():]
        # Remove trailing non-alpha non-numberical characters.
        trailing_chars_match = _UNWANTED_END_CHAR_PATTERN.search(number)
        if trailing_chars_match:
            number = number[:trailing_chars_match.start()]
        # Check for extra numbers at the end.
        second_number_match = _SECOND_NUMBER_START_PATTERN.search(number)
        if second_number_match:
            number = number[:second_number_match.start()]
        return number
    else:
        return U_EMPTY_STRING


def _is_viable_phone_number(number):
    """Checks to see if a string could possibly be a phone number.

    At the moment, checks to see that the string begins with at least 2
    digits, ignoring any punctuation commonly found in phone numbers.  This
    method does not require the number to be normalized in advance - but does
    assume that leading non-number symbols have been removed, such as by the
    method _extract_possible_number.

    Arguments:
    number -- string to be checked for viability as a phone number

    Returns True if the number could be a phone number of some sort, otherwise
    False
    """
    if len(number) < _MIN_LENGTH_FOR_NSN:
        return False
    match = fullmatch(_VALID_PHONE_NUMBER_PATTERN, number)
    return bool(match)


def _normalize(number):
    """Normalizes a string of characters representing a phone number.

    This performs the following conversions:
     - Punctuation is stripped.
     - For ALPHA/VANITY numbers:
        - Letters are converted to their numeric representation on a telephone
          keypad. The keypad used here is the one defined in ITU
          Recommendation E.161. This is only done if there are 3 or more
          letters in the number, to lessen the risk that such letters are
          typos.
     - For other numbers:
        - Wide-ascii digits are converted to normal ASCII (European) digits.
        - Arabic-Indic numerals are converted to European numerals.
        - Spurious alpha characters are stripped.

    Arguments:
    number -- string representing a phone number

    Returns the normalized string version of the phone number.
    """
    m = fullmatch(_VALID_ALPHA_PHONE_PATTERN, number)
    if m:
        return _normalize_helper(number, _ALPHA_PHONE_MAPPINGS, True)
    else:
        return normalize_digits_only(number)


def normalize_digits_only(number, keep_non_digits=False):
    """Normalizes a string of characters representing a phone number.

    This converts wide-ascii and arabic-indic numerals to European numerals,
    and strips punctuation and alpha characters (optional).

    Arguments:
    number -- a string representing a phone number
    keep_non_digits -- whether to keep non-digits

    Returns the normalized string version of the phone number.
    """
    number = unicod(number)
    number_length = len(number)
    normalized_digits = U_EMPTY_STRING
    for ii in range(number_length):
        d = unicode_digit(number[ii], -1)
        if d != -1:
            normalized_digits += unicod(d)
        elif keep_non_digits:
            normalized_digits += number[ii]
    return normalized_digits


def normalize_diallable_chars_only(number):
    """Normalizes a string of characters representing a phone number.

    This strips all characters which are not diallable on a mobile phone
    keypad (including all non-ASCII digits).

    Arguments:
    number -- a string of characters representing a phone number

    Returns the normalized string version of the phone number.
    """
    return _normalize_helper(number, _DIALLABLE_CHAR_MAPPINGS, True)


def convert_alpha_characters_in_number(number):
    """Convert alpha chars in a number to their respective digits on a keypad,
    but retains existing formatting."""
    return _normalize_helper(number, _ALPHA_PHONE_MAPPINGS, False)


def length_of_geographical_area_code(numobj):
    """Return length of the geographical area code for a number.

    Gets the length of the geographical area code from the PhoneNumber object
    passed in, so that clients could use it to split a national significant
    number into geographical area code and subscriber number. It works in such
    a way that the resultant subscriber number should be diallable, at least
    on some devices. An example of how this could be used:

    >>> import phonenumbers
    >>> numobj = phonenumbers.parse("16502530000", "US")
    >>> nsn = phonenumbers.national_significant_number(numobj)
    >>> ac_len = phonenumbers.length_of_geographical_area_code(numobj)
    >>> if ac_len > 0:
    ...     area_code = nsn[:ac_len]
    ...     subscriber_number = nsn[ac_len:]
    ... else:
    ...     area_code = ""
    ...     subscriber_number = nsn

    N.B.: area code is a very ambiguous concept, so the I18N team generally
    recommends against using it for most purposes, but recommends using the
    more general national_number instead. Read the following carefully before
    deciding to use this method:

     - geographical area codes change over time, and this method honors those
       changes; therefore, it doesn't guarantee the stability of the result it
       produces.
     - subscriber numbers may not be diallable from all devices (notably
       mobile devices, which typically require the full national_number to be
       dialled in most countries).
     - most non-geographical numbers have no area codes, including numbers
       from non-geographical entities.
     - some geographical numbers have no area codes.

    Arguments:
    numobj -- The PhoneNumber object to find the length of the area code form.

    Returns the length of area code of the PhoneNumber object passed in.
    """
    metadata = PhoneMetadata.metadata_for_region(region_code_for_number(numobj), None)
    if metadata is None:
        return 0

    # If a country doesn't use a national prefix, and this number doesn't have
    # an Italian leading zero, we assume it is a closed dialling plan with no
    # area codes.
    if metadata.national_prefix is None and not numobj.italian_leading_zero:
        return 0

    ntype = number_type(numobj)
    country_code = numobj.country_code
    if (ntype == PhoneNumberType.MOBILE and
        (country_code in _GEO_MOBILE_COUNTRIES_WITHOUT_MOBILE_AREA_CODES)):
        # Note this is a rough heuristic; it doesn't cover Indonesia well, for
        # example, where area codes are present for some mobile phones but not
        # for others. We have no better way of representing this in the
        # metadata at this point.
        return 0

    if not is_number_type_geographical(ntype, country_code):
        return 0

    return length_of_national_destination_code(numobj)


def length_of_national_destination_code(numobj):
    """Return length of the national destination code code for a number.

    Gets the length of the national destination code (NDC) from the
    PhoneNumber object passed in, so that clients could use it to split a
    national significant number into NDC and subscriber number. The NDC of a
    phone number is normally the first group of digit(s) right after the
    country calling code when the number is formatted in the international
    format, if there is a subscriber number part that follows.

    N.B.: similar to an area code, not all numbers have an NDC!

    An example of how this could be used:

    >>> import phonenumbers
    >>> numobj = phonenumbers.parse("18002530000", "US")
    >>> nsn = phonenumbers.national_significant_number(numobj)
    >>> ndc_len = phonenumbers.length_of_national_destination_code(numobj)
    >>> if ndc_len > 0:
    ...     national_destination_code = nsn[:ndc_len]
    ...     subscriber_number = nsn[ndc_len:]
    ... else:
    ...     national_destination_code = ""
    ...     subscriber_number = nsn

    Refer to the unittests to see the difference between this function and
    length_of_geographical_area_code.

    Arguments:
    numobj -- The PhoneNumber object to find the length of the NDC from.

    Returns the length of NDC of the PhoneNumber object passed in, which
    could be zero.
    """
    if numobj.extension is not None:
        # We don't want to alter the object given to us, but we don't want to
        # include the extension when we format it, so we copy it and clear the
        # extension here.
        copied_numobj = PhoneNumber()
        copied_numobj.merge_from(numobj)
        copied_numobj.extension = None
    else:
        copied_numobj = numobj

    nsn = format_number(copied_numobj, PhoneNumberFormat.INTERNATIONAL)
    number_groups = re.split(NON_DIGITS_PATTERN, nsn)

    # The pattern will start with "+COUNTRY_CODE " so the first group will
    # always be the empty string (before the + symbol) and the second group
    # will be the country calling code. The third group will be area code if
    # it is not the last group.
    if len(number_groups) <= 3:
        return 0

    if number_type(numobj) == PhoneNumberType.MOBILE:
        # For example Argentinian mobile numbers, when formatted in the
        # international format, are in the form of +54 9 NDC XXXX... As a
        # result, we take the length of the third group (NDC) and add the
        # length of the second group (which is the mobile token), which also
        # forms part of the national significant number.  This assumes that
        # the mobile token is always formatted separately from the rest of the
        # phone number.
        mobile_token = country_mobile_token(numobj.country_code)
        if mobile_token != U_EMPTY_STRING:
            return len(number_groups[2]) + len(number_groups[3])
    return len(number_groups[2])


def country_mobile_token(country_code):
    """Returns the mobile token for the provided country calling code if it has one, otherwise
    returns an empty string. A mobile token is a number inserted before the area code when dialing
    a mobile number from that country from abroad.

    Arguments:
    country_code -- the country calling code for which we want the mobile token
    Returns the mobile token, as a string, for the given country calling code.
    """
    return _MOBILE_TOKEN_MAPPINGS.get(country_code, U_EMPTY_STRING)


def _normalize_helper(number, replacements, remove_non_matches):
    """Normalizes a string of characters representing a phone number by
    replacing all characters found in the accompanying map with the values
    therein, and stripping all other characters if remove_non_matches is true.

    Arguments:
    number -- a string representing a phone number
    replacements -- a mapping of characters to what they should be replaced
              by in the normalized version of the phone number
    remove_non_matches -- indicates whether characters that are not able to be
              replaced should be stripped from the number. If this is False,
              they will be left unchanged in the number.

    Returns the normalized string version of the phone number.
    """
    normalized_number = []
    for char in number:
        new_digit = replacements.get(char.upper(), None)
        if new_digit is not None:
            normalized_number.append(new_digit)
        elif not remove_non_matches:
            normalized_number.append(char)
        # If neither of the above are true, we remove this character
    return U_EMPTY_STRING.join(normalized_number)


def supported_calling_codes():
    """Returns all country calling codes the library has metadata for, covering
    both non-geographical entities (global network calling codes) and those
    used for geographical entities. This could be used to populate a drop-down
    box of country calling codes for a phone-number widget, for instance.

    Returns an unordered set of the country calling codes for every geographica
    and non-geographical entity the library supports.
    """
    return set(COUNTRY_CODE_TO_REGION_CODE.keys())


def _desc_has_possible_number_data(desc):

    """Returns true if there is any possible number data set for a particular PhoneNumberDesc."""
    # If this is empty, it means numbers of this type inherit from the "general desc" -> the value
    # "-1" means that no numbers exist for this type.
    if desc is None:
        return False
    return len(desc.possible_length) != 1 or desc.possible_length[0] != -1


# Note: desc_has_data must account for any of MetadataFilter's excludableChildFields potentially
# being absent from the metadata. It must check them all. For any changes in descHasData, ensure
# that all the excludableChildFields are still being checked. If your change is safe simply
# mention why during a review without needing to change MetadataFilter.
def _desc_has_data(desc):
    """Returns true if there is any data set for a particular PhoneNumberDesc."""
    if desc is None:
        return False
    # Checking most properties since we don't know what's present, since a custom build may have
    # stripped just one of them (e.g. liteBuild strips exampleNumber). We don't bother checking the
    # possibleLengthsLocalOnly, since if this is the only thing that's present we don't really
    # support the type at all: no type-specific methods will work with only this data.
    return ((desc.example_number is not None) or
            _desc_has_possible_number_data(desc) or
            (desc.national_number_pattern is not None))


def _supported_types_for_metadata(metadata):
    """Returns the types we have metadata for based on the PhoneMetadata object passed in, which must be non-None."""
    numtypes = set()
    for numtype in PhoneNumberType.values():
        if numtype in (PhoneNumberType.FIXED_LINE_OR_MOBILE, PhoneNumberType.UNKNOWN):
            # Never return FIXED_LINE_OR_MOBILE (it is a convenience type, and represents that a
            # particular number type can't be determined) or UNKNOWN (the non-type).
            continue
        if _desc_has_data(_number_desc_by_type(metadata, numtype)):
            numtypes.add(numtype)
    return numtypes


def supported_types_for_region(region_code):
    """Returns the types for a given region which the library has metadata for.

    Will not include FIXED_LINE_OR_MOBILE (if numbers in this region could
    be classified as FIXED_LINE_OR_MOBILE, both FIXED_LINE and MOBILE would
    be present) and UNKNOWN.

    No types will be returned for invalid or unknown region codes.
    """
    if not _is_valid_region_code(region_code):
        return set()
    metadata = PhoneMetadata.metadata_for_region(region_code.upper())
    return _supported_types_for_metadata(metadata)


def supported_types_for_non_geo_entity(country_code):
    """Returns the types for a country-code belonging to a non-geographical entity
    which the library has metadata for. Will not include FIXED_LINE_OR_MOBILE
    (if numbers for this non-geographical entity could be classified as
    FIXED_LINE_OR_MOBILE, both FIXED_LINE and MOBILE would be present) and
    UNKNOWN.

    No types will be returned for country calling codes that do not map to a
    known non-geographical entity.
    """
    metadata = PhoneMetadata.metadata_for_nongeo_region(country_code, None)
    if metadata is None:
        return set()
    return _supported_types_for_metadata(metadata)


def _formatting_rule_has_first_group_only(national_prefix_formatting_rule):
    """Helper function to check if the national prefix formatting rule has the
    first group only, i.e., does not start with the national prefix.
    """
    if national_prefix_formatting_rule is None:
        return True
    return bool(fullmatch(_FIRST_GROUP_ONLY_PREFIX_PATTERN,
                          national_prefix_formatting_rule))


def is_number_geographical(numobj):
    """Tests whether a phone number has a geographical association.

    It checks if the number is associated with a certain region in the country
    to which it belongs. Note that this doesn't verify if the number is
    actually in use.
    country_code -- the country calling code for which we want the mobile token
    """
    return is_number_type_geographical(number_type(numobj), numobj.country_code)


def is_number_type_geographical(num_type, country_code):
    """Tests whether a phone number has a geographical association,
    as represented by its type and the country it belongs to.

    This version of isNumberGeographical exists since calculating the phone
    number type is expensive; if we have already done this, we don't want to
    do it again.
    """
    return (num_type == PhoneNumberType.FIXED_LINE or
            num_type == PhoneNumberType.FIXED_LINE_OR_MOBILE or
            ((country_code in _GEO_MOBILE_COUNTRIES) and
             num_type == PhoneNumberType.MOBILE))


def _is_valid_region_code(region_code):
    """Helper function to check region code is not unknown or None"""
    if region_code is None:
        return False
    return (region_code in SUPPORTED_REGIONS)


def _has_valid_country_calling_code(country_calling_code):
    return (country_calling_code in COUNTRY_CODE_TO_REGION_CODE)


def format_number(numobj, num_format):
    """Formats a phone number in the specified format using default rules.

    Note that this does not promise to produce a phone number that the user
    can dial from where they are - although we do format in either 'national'
    or 'international' format depending on what the client asks for, we do not
    currently support a more abbreviated format, such as for users in the same
    "area" who could potentially dial the number without area code. Note that
    if the phone number has a country calling code of 0 or an otherwise
    invalid country calling code, we cannot work out which formatting rules to
    apply so we return the national significant number with no formatting
    applied.

    Arguments:
    numobj -- The phone number to be formatted.
    num_format -- The format the phone number should be formatted into

    Returns the formatted phone number.
    """
    if numobj.national_number == 0 and numobj.raw_input is not None:
        # Unparseable numbers that kept their raw input just use that.  This
        # is the only case where a number can be formatted as E164 without a
        # leading '+' symbol (but the original number wasn't parseable
        # anyway).
        # TODO: Consider removing the 'if' above so that unparseable strings
        # without raw input format to the empty string instead of "+00".
        if len(numobj.raw_input) > 0:
            return numobj.raw_input
    country_calling_code = numobj.country_code
    nsn = national_significant_number(numobj)
    if num_format == PhoneNumberFormat.E164:
        # Early exit for E164 case (even if the country calling code is
        # invalid) since no formatting of the national number needs to be
        # applied.  Extensions are not formatted.
        return _prefix_number_with_country_calling_code(country_calling_code, num_format, nsn)
    if not _has_valid_country_calling_code(country_calling_code):
        return nsn
    # Note region_code_for_country_code() is used because formatting
    # information for regions which share a country calling code is contained
    # by only one region for performance reasons. For example, for NANPA
    # regions it will be contained in the metadata for US.
    region_code = region_code_for_country_code(country_calling_code)
    # Metadata cannot be None because the country calling code is valid (which
    # means that the region code cannot be ZZ and must be one of our supported
    # region codes).
    metadata = PhoneMetadata.metadata_for_region_or_calling_code(country_calling_code, region_code.upper())
    formatted_number = _format_nsn(nsn, metadata, num_format)
    formatted_number = _maybe_append_formatted_extension(numobj,
                                                         metadata,
                                                         num_format,
                                                         formatted_number)
    return _prefix_number_with_country_calling_code(country_calling_code,
                                                    num_format,
                                                    formatted_number)


def format_by_pattern(numobj, number_format, user_defined_formats):
    """Formats a phone number using client-defined formatting rules."

    Note that if the phone number has a country calling code of zero or an
    otherwise invalid country calling code, we cannot work out things like
    whether there should be a national prefix applied, or how to format
    extensions, so we return the national significant number with no
    formatting applied.

    Arguments:
    numobj -- The phone number to be formatted
    num_format -- The format the phone number should be formatted into
    user_defined_formats -- formatting rules specified by clients

    Returns the formatted phone number.
    """
    country_code = numobj.country_code
    nsn = national_significant_number(numobj)
    if not _has_valid_country_calling_code(country_code):
        return nsn
    # Note region_code_for_country_code() is used because formatting
    # information for regions which share a country calling code is contained
    # by only one region for performance reasons. For example, for NANPA
    # regions it will be contained in the metadata for US.
    region_code = region_code_for_country_code(country_code)
    # Metadata cannot be None because the country calling code is valid.
    metadata = PhoneMetadata.metadata_for_region_or_calling_code(country_code, region_code)

    formatted_number = U_EMPTY_STRING
    formatting_pattern = _choose_formatting_pattern_for_number(user_defined_formats, nsn)
    if formatting_pattern is None:
        # If no pattern above is matched, we format the number as a whole.
        formatted_number = nsn
    else:
        num_format_copy = _copy_number_format(formatting_pattern)
        # Before we do a replacement of the national prefix pattern $NP with
        # the national prefix, we need to copy the rule so that subsequent
        # replacements for different numbers have the appropriate national
        # prefix.
        np_formatting_rule = formatting_pattern.national_prefix_formatting_rule
        if np_formatting_rule:
            national_prefix = metadata.national_prefix
            if national_prefix:
                # Replace $NP with national prefix and $FG with the first
                # group (\1) matcher.
                np_formatting_rule = np_formatting_rule.replace(_NP_STRING, national_prefix)
                np_formatting_rule = np_formatting_rule.replace(_FG_STRING, unicod("\\1"))
                num_format_copy.national_prefix_formatting_rule = np_formatting_rule
            else:
                # We don't want to have a rule for how to format the national
                # prefix if there isn't one.
                num_format_copy.national_prefix_formatting_rule = None
        formatted_number = _format_nsn_using_pattern(nsn, num_format_copy, number_format)
    formatted_number = _maybe_append_formatted_extension(numobj,
                                                         metadata,
                                                         number_format,
                                                         formatted_number)
    formatted_number = _prefix_number_with_country_calling_code(country_code,
                                                                number_format,
                                                                formatted_number)
    return formatted_number


def format_national_number_with_carrier_code(numobj, carrier_code):
    """Format a number in national format for dialing using the specified carrier.

    The carrier-code will always be used regardless of whether the phone
    number already has a preferred domestic carrier code stored. If
    carrier_code contains an empty string, returns the number in national
    format without any carrier code.

    Arguments:
    numobj -- The phone number to be formatted
    carrier_code -- The carrier selection code to be used

    Returns the formatted phone number in national format for dialing using
    the carrier as specified in the carrier_code.
    """
    country_code = numobj.country_code
    nsn = national_significant_number(numobj)
    if not _has_valid_country_calling_code(country_code):
        return nsn
    # Note region_code_for_country_code() is used because formatting
    # information for regions which share a country calling code is contained
    # by only one region for performance reasons. For example, for NANPA
    # regions it will be contained in the metadata for US.
    region_code = region_code_for_country_code(country_code)
    # Metadata cannot be None because the country calling code is valid
    metadata = PhoneMetadata.metadata_for_region_or_calling_code(country_code, region_code)
    formatted_number = _format_nsn(nsn,
                                   metadata,
                                   PhoneNumberFormat.NATIONAL,
                                   carrier_code)
    formatted_number = _maybe_append_formatted_extension(numobj,
                                                         metadata,
                                                         PhoneNumberFormat.NATIONAL,
                                                         formatted_number)
    formatted_number = _prefix_number_with_country_calling_code(country_code,
                                                                PhoneNumberFormat.NATIONAL,
                                                                formatted_number)
    return formatted_number


def format_national_number_with_preferred_carrier_code(numobj, fallback_carrier_code):
    """Formats a phone number in national format for dialing using the carrier
    as specified in the preferred_domestic_carrier_code field of the
    PhoneNumber object passed in. If that is missing, use the
    fallback_carrier_code passed in instead. If there is no
    preferred_domestic_carrier_code, and the fallback_carrier_code contains an
    empty string, return the number in national format without any carrier
    code.

    Use format_national_number_with_carrier_code instead if the carrier code
    passed in should take precedence over the number's
    preferred_domestic_carrier_code when formatting.

    Arguments:
    numobj -- The phone number to be formatted
    carrier_code -- The carrier selection code to be used, if none is found in the
              phone number itself.

    Returns the formatted phone number in national format for dialing using
    the number's preferred_domestic_carrier_code, or the fallback_carrier_code
    pass in if none is found.
    """
    # Historically, we set this to an empty string when parsing with raw input
    # if none was found in the input string. However, this doesn't result in a
    # number we can dial. For this reason, we treat the empty string the same
    # as if it isn't set at all.
    if (numobj.preferred_domestic_carrier_code is not None and
        len(numobj.preferred_domestic_carrier_code) > 0):
        carrier_code = numobj.preferred_domestic_carrier_code
    else:
        carrier_code = fallback_carrier_code
    return format_national_number_with_carrier_code(numobj, carrier_code)


def format_number_for_mobile_dialing(numobj, region_calling_from, with_formatting):
    """Returns a number formatted in such a way that it can be dialed from a
     mobile phone in a specific region.

    If the number cannot be reached from the region (e.g. some countries block
    toll-free numbers from being called outside of the country), the method
    returns an empty string.

    Arguments:
    numobj -- The phone number to be formatted
    region_calling_from -- The region where the call is being placed.

    with_formatting -- whether the number should be returned with formatting
              symbols, such as spaces and dashes.

    Returns the formatted phone number.
    """
    country_calling_code = numobj.country_code
    if not _has_valid_country_calling_code(country_calling_code):
        if numobj.raw_input is None:
            return U_EMPTY_STRING
        else:
            return numobj.raw_input
    formatted_number = U_EMPTY_STRING
    # Clear the extension, as that part cannot normally be dialed together with the main number.
    numobj_no_ext = PhoneNumber()
    numobj_no_ext.merge_from(numobj)
    numobj_no_ext.extension = None
    region_code = region_code_for_country_code(country_calling_code)
    numobj_type = number_type(numobj_no_ext)
    is_valid_number = (numobj_type != PhoneNumberType.UNKNOWN)
    if region_calling_from == region_code:
        is_fixed_line_or_mobile = ((numobj_type == PhoneNumberType.FIXED_LINE) or
                                   (numobj_type == PhoneNumberType.MOBILE) or
                                   (numobj_type == PhoneNumberType.FIXED_LINE_OR_MOBILE))
        # Carrier codes may be needed in some countries. We handle this here.
        if region_code == "CO" and numobj_type == PhoneNumberType.FIXED_LINE:
            formatted_number = format_national_number_with_carrier_code(numobj_no_ext,
                                                                        _COLOMBIA_MOBILE_TO_FIXED_LINE_PREFIX)
        elif region_code == "BR" and is_fixed_line_or_mobile:
            # Historically, we set this to an empty string when parsing with
            # raw input if none was found in the input string. However, this
            # doesn't result in a number we can dial. For this reason, we
            # treat the empty string the same as if it isn't set at all.
            if (numobj_no_ext.preferred_domestic_carrier_code is not None and
                len(numobj_no_ext.preferred_domestic_carrier_code) > 0):
                formatted_number = format_national_number_with_preferred_carrier_code(numobj_no_ext, "")
            else:
                # Brazilian fixed line and mobile numbers need to be dialed with a
                # carrier code when called within Brazil. Without that, most of
                # the carriers won't connect the call.  Because of that, we return
                # an empty string here.
                formatted_number = U_EMPTY_STRING
        elif is_valid_number and region_code == "HU":
            # The national format for HU numbers doesn't contain the national
            # prefix, because that is how numbers are normally written
            # down. However, the national prefix is obligatory when dialing
            # from a mobile phone, except for short numbers. As a result, we
            # add it back here if it is a valid regular length phone number.
            formatted_number = (ndd_prefix_for_region(region_code, True) +  # strip non-digits
                                U_SPACE + format_number(numobj_no_ext, PhoneNumberFormat.NATIONAL))
        elif country_calling_code == _NANPA_COUNTRY_CODE:
            # For NANPA countries, we output international format for numbers
            # that can be dialed internationally, since that always works,
            # except for numbers which might potentially be short numbers,
            # which are always dialled in national format.
            metadata = PhoneMetadata.metadata_for_region(region_calling_from)
            if (can_be_internationally_dialled(numobj_no_ext) and
                _test_number_length(national_significant_number(numobj_no_ext),
                                    metadata) != ValidationResult.TOO_SHORT):
                formatted_number = format_number(numobj_no_ext, PhoneNumberFormat.INTERNATIONAL)
            else:
                formatted_number = format_number(numobj_no_ext, PhoneNumberFormat.NATIONAL)
        else:
            # For non-geographical countries, and Mexican, Chilean, and Uzbek
            # fixed line and mobile numbers, we output international format for
            # numbers that can be dialed internationally as that always works.
            if ((region_code == REGION_CODE_FOR_NON_GEO_ENTITY or
                 ((region_code == unicod("MX") or region_code == unicod("CL") or
                   region_code == unicod("UZ")) and
                  is_fixed_line_or_mobile)) and
                can_be_internationally_dialled(numobj_no_ext)):
                # MX fixed line and mobile numbers should always be formatted
                # in international format, even when dialed within MX. For
                # national format to work, a carrier code needs to be used,
                # and the correct carrier code depends on if the caller and
                # callee are from the same local area. It is trickier to get
                # that to work correctly than using international format,
                # which is tested to work fine on all carriers.
                # CL fixed line numbers need the national prefix when dialing
                # in the national format, but don't have it when used for
                # display. The reverse is true for mobile numbers.  As a
                # result, we output them in the international format to make
                # it work.
                # UZ mobile and fixed-line numbers have to be formatted in
                # international format or prefixed with special codes like 03,
                # 04 (for fixed-line) and 05 (for mobile) for dialling
                # successfully from mobile devices. As we do not have complete
                # information on special codes and to be consistent with
                # formatting across all phone types we return the number in
                # international format here.
                formatted_number = format_number(numobj_no_ext, PhoneNumberFormat.INTERNATIONAL)
            else:
                formatted_number = format_number(numobj_no_ext, PhoneNumberFormat.NATIONAL)
    elif is_valid_number and can_be_internationally_dialled(numobj_no_ext):
        # We assume that short numbers are not diallable from outside their
        # region, so if a number is not a valid regular length phone number,
        # we treat it as if it cannot be internationally dialled.
        if with_formatting:
            return format_number(numobj_no_ext, PhoneNumberFormat.INTERNATIONAL)
        else:
            return format_number(numobj_no_ext, PhoneNumberFormat.E164)

    if with_formatting:
        return formatted_number
    else:
        return normalize_diallable_chars_only(formatted_number)


def format_out_of_country_calling_number(numobj, region_calling_from):
    """Formats a phone number for out-of-country dialing purposes.

    If no region_calling_from is supplied, we format the number in its
    INTERNATIONAL format. If the country calling code is the same as that of
    the region where the number is from, then NATIONAL formatting will be
    applied.

    If the number itself has a country calling code of zero or an otherwise
    invalid country calling code, then we return the number with no formatting
    applied.

    Note this function takes care of the case for calling inside of NANPA and
    between Russia and Kazakhstan (who share the same country calling
    code). In those cases, no international prefix is used. For regions which
    have multiple international prefixes, the number in its INTERNATIONAL
    format will be returned instead.

    Arguments:
    numobj -- The phone number to be formatted
    region_calling_from -- The region where the call is being placed

    Returns the formatted phone number
    """
    if not _is_valid_region_code(region_calling_from):
        return format_number(numobj, PhoneNumberFormat.INTERNATIONAL)
    country_code = numobj.country_code
    nsn = national_significant_number(numobj)
    if not _has_valid_country_calling_code(country_code):
        return nsn
    if country_code == _NANPA_COUNTRY_CODE:
        if is_nanpa_country(region_calling_from):
            # For NANPA regions, return the national format for these regions
            # but prefix it with the country calling code.
            return (unicod(country_code) + U_SPACE +
                    format_number(numobj, PhoneNumberFormat.NATIONAL))
    elif country_code == country_code_for_valid_region(region_calling_from):
        # If regions share a country calling code, the country calling code
        # need not be dialled.  This also applies when dialling within a
        # region, so this if clause covers both these cases.  Technically this
        # is the case for dialling from La Reunion to other overseas
        # departments of France (French Guiana, Martinique, Guadeloupe), but
        # not vice versa - so we don't cover this edge case for now and for
        # those cases return the version including country calling code.
        # Details here:
        # http://www.petitfute.com/voyage/225-info-pratiques-reunion
        return format_number(numobj, PhoneNumberFormat.NATIONAL)

    # Metadata cannot be None because we checked '_is_valid_region_code()' above.
    metadata_for_region_calling_from = PhoneMetadata.metadata_for_region_or_calling_code(country_code, region_calling_from.upper())
    international_prefix = metadata_for_region_calling_from.international_prefix

    # For regions that have multiple international prefixes, the international
    # format of the number is returned, unless there is a preferred
    # international prefix.
    i18n_prefix_for_formatting = U_EMPTY_STRING
    i18n_match = fullmatch(_SINGLE_INTERNATIONAL_PREFIX, international_prefix)
    if i18n_match:
        i18n_prefix_for_formatting = international_prefix
    elif metadata_for_region_calling_from.preferred_international_prefix is not None:
        i18n_prefix_for_formatting = metadata_for_region_calling_from.preferred_international_prefix

    region_code = region_code_for_country_code(country_code)
    # Metadata cannot be None because the country calling code is valid.
    metadata_for_region = PhoneMetadata.metadata_for_region_or_calling_code(country_code, region_code.upper())
    formatted_national_number = _format_nsn(nsn,
                                            metadata_for_region,
                                            PhoneNumberFormat.INTERNATIONAL)
    formatted_number = _maybe_append_formatted_extension(numobj,
                                                         metadata_for_region,
                                                         PhoneNumberFormat.INTERNATIONAL,
                                                         formatted_national_number)
    if len(i18n_prefix_for_formatting) > 0:
        formatted_number = (i18n_prefix_for_formatting + U_SPACE +
                            unicod(country_code) + U_SPACE + formatted_number)
    else:
        formatted_number = _prefix_number_with_country_calling_code(country_code,
                                                                    PhoneNumberFormat.INTERNATIONAL,
                                                                    formatted_number)
    return formatted_number


def format_in_original_format(numobj, region_calling_from):
    """Format a number using the original format that the number was parsed from.

    The original format is embedded in the country_code_source field of the
    PhoneNumber object passed in. If such information is missing, the number
    will be formatted into the NATIONAL format by default.

    When  we don't have a formatting pattern for the number, the method
    returns the raw input when it is available.

    Note this method guarantees no digit will be inserted, removed or modified
    as a result of formatting.

    Arguments:
    number -- The phone number that needs to be formatted in its original
              number format
    region_calling_from -- The region whose IDD needs to be prefixed if the
              original number has one.

    Returns the formatted phone number in its original number format.
    """
    if (numobj.raw_input is not None and not _has_formatting_pattern_for_number(numobj)):
        # We check if we have the formatting pattern because without that, we
        # might format the number as a group without national prefix.
        return numobj.raw_input
    if numobj.country_code_source is CountryCodeSource.UNSPECIFIED:
        return format_number(numobj, PhoneNumberFormat.NATIONAL)

    formatted_number = _format_original_allow_mods(numobj, region_calling_from)
    num_raw_input = numobj.raw_input
    # If no digit is inserted/removed/modified as a result of our formatting,
    # we return the formatted phone number; otherwise we return the raw input
    # the user entered.
    if (formatted_number is not None and num_raw_input):
        normalized_formatted_number = normalize_diallable_chars_only(formatted_number)
        normalized_raw_input = normalize_diallable_chars_only(num_raw_input)
        if normalized_formatted_number != normalized_raw_input:
            formatted_number = num_raw_input
    return formatted_number


def _format_original_allow_mods(numobj, region_calling_from):
    if (numobj.country_code_source == CountryCodeSource.FROM_NUMBER_WITH_PLUS_SIGN):
        return format_number(numobj, PhoneNumberFormat.INTERNATIONAL)
    elif numobj.country_code_source == CountryCodeSource.FROM_NUMBER_WITH_IDD:
        return format_out_of_country_calling_number(numobj, region_calling_from)
    elif (numobj.country_code_source == CountryCodeSource.FROM_NUMBER_WITHOUT_PLUS_SIGN):
        return format_number(numobj, PhoneNumberFormat.INTERNATIONAL)[1:]
    else:
        region_code = region_code_for_country_code(numobj.country_code)
        # We strip non-digits from the NDD here, and from the raw input later, so that we can
        # compare them easily.
        national_prefix = ndd_prefix_for_region(region_code, True)  # strip non-digits
        national_format = format_number(numobj, PhoneNumberFormat.NATIONAL)
        if (national_prefix is None or len(national_prefix) == 0):
            # If the region doesn't have a national prefix at all, we can
            # safely return the national format without worrying about a
            # national prefix being added.
            return national_format
        # Otherwise, we check if the original number was entered with a national prefix.
        if (_raw_input_contains_national_prefix(numobj.raw_input, national_prefix, region_code)):
            # If so, we can safely return the national format.
            return national_format
        # Metadata cannot be None here because ndd_prefix_for_region() (above) returns None if
        # there is no metadata for the region.
        metadata = PhoneMetadata.metadata_for_region(region_code)
        national_number = national_significant_number(numobj)
        format_rule = _choose_formatting_pattern_for_number(metadata.number_format, national_number)
        # The format rule could still be null here if the national number was
        # 0 and there was no raw input (this should not be possible for
        # numbers generated by the phonenumber library as they would also not
        # have a country calling code and we would have exited earlier).
        if format_rule is None:
            return national_format
        # When the format we apply to this number doesn't contain national
        # prefix, we can just return the national format.
        # TODO: Refactor the code below with the code in isNationalPrefixPresentIfRequired.
        candidate_national_prefix_rule = format_rule.national_prefix_formatting_rule
        # We assume that the first-group symbol will never be _before_ the national prefix.
        if candidate_national_prefix_rule is None:
            return national_format
        index_of_first_group = candidate_national_prefix_rule.find("\\1")
        if (index_of_first_group <= 0):
            return national_format
        candidate_national_prefix_rule = candidate_national_prefix_rule[:index_of_first_group]
        candidate_national_prefix_rule = normalize_digits_only(candidate_national_prefix_rule)
        if len(candidate_national_prefix_rule) == 0:
            # National prefix not used when formatting this number.
            return national_format
        # Otherwise, we need to remove the national prefix from our output.
        new_format_rule = _copy_number_format(format_rule)
        new_format_rule.national_prefix_formatting_rule = None
        return format_by_pattern(numobj, PhoneNumberFormat.NATIONAL, [new_format_rule])


def _raw_input_contains_national_prefix(raw_input, national_prefix, region_code):
    """Check if raw_input, which is assumed to be in the national format, has a
    national prefix. The national prefix is assumed to be in digits-only
    form."""
    nnn = normalize_digits_only(raw_input)
    if nnn.startswith(national_prefix):
        try:
            # Some Japanese numbers (e.g. 00777123) might be mistaken to
            # contain the national prefix when written without it
            # (e.g. 0777123) if we just do prefix matching. To tackle that, we
            # check the validity of the number if the assumed national prefix
            # is removed (777123 won't be valid in Japan).
            return is_valid_number(parse(nnn[len(national_prefix):], region_code))
        except NumberParseException:
            return False
    return False


def _has_formatting_pattern_for_number(numobj):
    country_code = numobj.country_code
    phone_number_region = region_code_for_country_code(country_code)
    metadata = PhoneMetadata.metadata_for_region_or_calling_code(country_code, phone_number_region)
    if metadata is None:
        return False
    national_number = national_significant_number(numobj)
    format_rule = _choose_formatting_pattern_for_number(metadata.number_format, national_number)
    return format_rule is not None


def format_out_of_country_keeping_alpha_chars(numobj, region_calling_from):
    """Formats a phone number for out-of-country dialing purposes.

    Note that in this version, if the number was entered originally using
    alpha characters and this version of the number is stored in raw_input,
    this representation of the number will be used rather than the digit
    representation. Grouping information, as specified by characters such as
    "-" and " ", will be retained.

    Caveats:

     - This will not produce good results if the country calling code is both
       present in the raw input _and_ is the start of the national
       number. This is not a problem in the regions which typically use alpha
       numbers.

     - This will also not produce good results if the raw input has any
       grouping information within the first three digits of the national
       number, and if the function needs to strip preceding digits/words in
       the raw input before these digits. Normally people group the first
       three digits together so this is not a huge problem - and will be fixed
       if it proves to be so.

    Arguments:
    numobj -- The phone number that needs to be formatted.
    region_calling_from -- The region where the call is being placed.

    Returns the formatted phone number
    """
    num_raw_input = numobj.raw_input
    # If there is no raw input, then we can't keep alpha characters because there aren't any.
    # In this case, we return format_out_of_country_calling_number.
    if num_raw_input is None or len(num_raw_input) == 0:
        return format_out_of_country_calling_number(numobj, region_calling_from)
    country_code = numobj.country_code
    if not _has_valid_country_calling_code(country_code):
        return num_raw_input
    # Strip any prefix such as country calling code, IDD, that was present. We
    # do this by comparing the number in raw_input with the parsed number.  To
    # do this, first we normalize punctuation. We retain number grouping
    # symbols such as " " only.
    num_raw_input = _normalize_helper(num_raw_input,
                                      _ALL_PLUS_NUMBER_GROUPING_SYMBOLS,
                                      True)
    # Now we trim everything before the first three digits in the parsed
    # number. We choose three because all valid alpha numbers have 3 digits at
    # the start - if it does not, then we don't trim anything at
    # all. Similarly, if the national number was less than three digits, we
    # don't trim anything at all.
    national_number = national_significant_number(numobj)
    if len(national_number) > 3:
        first_national_number_digit = num_raw_input.find(national_number[:3])
        if first_national_number_digit != -1:
            num_raw_input = num_raw_input[first_national_number_digit:]

    metadata_for_region_calling_from = PhoneMetadata.metadata_for_region(region_calling_from.upper(), None)
    if country_code == _NANPA_COUNTRY_CODE:
        if is_nanpa_country(region_calling_from):
            return unicod(country_code) + U_SPACE + num_raw_input
    elif (metadata_for_region_calling_from is not None and
          country_code == country_code_for_region(region_calling_from)):
        formatting_pattern = _choose_formatting_pattern_for_number(metadata_for_region_calling_from.number_format,
                                                                   national_number)
        if formatting_pattern is None:
            # If no pattern above is matched, we format the original input
            return num_raw_input
        new_format = _copy_number_format(formatting_pattern)
        # The first group is the first group of digits that the user
        # wrote together.
        new_format.pattern = u("(\\d+)(.*)")
        # Here we just concatenate them back together after the national
        # prefix has been fixed.
        new_format.format = u(r"\1\2")
        # Now we format using this pattern instead of the default pattern,
        # but with the national prefix prefixed if necessary.
        # This will not work in the cases where the pattern (and not the
        # leading digits) decide whether a national prefix needs to be used,
        # since we have overridden the pattern to match anything, but that is
        # not the case in the metadata to date.
        return _format_nsn_using_pattern(num_raw_input,
                                         new_format,
                                         PhoneNumberFormat.NATIONAL)
    i18n_prefix_for_formatting = U_EMPTY_STRING
    # If an unsupported region-calling-from is entered, or a country with
    # multiple international prefixes, the international format of the number
    # is returned, unless there is a preferred international prefix.
    if metadata_for_region_calling_from is not None:
        international_prefix = metadata_for_region_calling_from.international_prefix
        i18n_match = fullmatch(_SINGLE_INTERNATIONAL_PREFIX, international_prefix)
        if i18n_match:
            i18n_prefix_for_formatting = international_prefix
        else:
            i18n_prefix_for_formatting = metadata_for_region_calling_from.preferred_international_prefix

    region_code = region_code_for_country_code(country_code)
    # Metadata cannot be None because the country calling code is valid.
    metadata_for_region = PhoneMetadata.metadata_for_region_or_calling_code(country_code, region_code)
    formatted_number = _maybe_append_formatted_extension(numobj,
                                                         metadata_for_region,
                                                         PhoneNumberFormat.INTERNATIONAL,
                                                         num_raw_input)
    if i18n_prefix_for_formatting:
        formatted_number = (i18n_prefix_for_formatting + U_SPACE +
                            unicod(country_code) + U_SPACE + formatted_number)
    else:
        # Invalid region entered as country-calling-from (so no metadata was
        # found for it) or the region chosen has multiple international
        # dialling prefixes.
        formatted_number = _prefix_number_with_country_calling_code(country_code,
                                                                    PhoneNumberFormat.INTERNATIONAL,
                                                                    formatted_number)
    return formatted_number


def national_significant_number(numobj):
    """Gets the national significant number of a phone number.

    Note that a national significant number doesn't contain a national prefix
    or any formatting.

    Arguments:
    numobj -- The PhoneNumber object for which the national significant number
              is needed.

    Returns the national significant number of the PhoneNumber object passed
    in.
    """
    # If leading zero(s) have been set, we prefix this now. Note this is not a
    # national prefix.
    national_number = U_EMPTY_STRING
    if numobj.italian_leading_zero:
        num_zeros = numobj.number_of_leading_zeros
        if num_zeros is None:
            num_zeros = 1
        if num_zeros > 0:
            national_number = U_ZERO * num_zeros
    national_number += str(numobj.national_number)
    return national_number


def _prefix_number_with_country_calling_code(country_code, num_format, formatted_number):
    """A helper function that is used by format_number and format_by_pattern."""
    if num_format == PhoneNumberFormat.E164:
        return _PLUS_SIGN + unicod(country_code) + formatted_number
    elif num_format == PhoneNumberFormat.INTERNATIONAL:
        return _PLUS_SIGN + unicod(country_code) + U_SPACE + formatted_number
    elif num_format == PhoneNumberFormat.RFC3966:
        return _RFC3966_PREFIX + _PLUS_SIGN + unicod(country_code) + U_DASH + formatted_number
    else:
        return formatted_number


def _format_nsn(number, metadata, num_format, carrier_code=None):
    """Format a national number."""
    # Note in some regions, the national number can be written in two
    # completely different ways depending on whether it forms part of the
    # NATIONAL format or INTERNATIONAL format. The num_format parameter here
    # is used to specify which format to use for those cases. If a carrier_code
    # is specified, this will be inserted into the formatted string to replace
    # $CC.
    intl_number_formats = metadata.intl_number_format

    # When the intl_number_formats exists, we use that to format national
    # number for the INTERNATIONAL format instead of using the
    # number_desc.number_formats.
    if (len(intl_number_formats) == 0 or
        num_format == PhoneNumberFormat.NATIONAL):
        available_formats = metadata.number_format
    else:
        available_formats = metadata.intl_number_format
    formatting_pattern = _choose_formatting_pattern_for_number(available_formats, number)
    if formatting_pattern is None:
        return number
    else:
        return _format_nsn_using_pattern(number, formatting_pattern, num_format, carrier_code)


def _choose_formatting_pattern_for_number(available_formats, national_number):
    for num_format in available_formats:
        size = len(num_format.leading_digits_pattern)
        # We always use the last leading_digits_pattern, as it is the most detailed.
        if size > 0:
            ld_pattern = re.compile(num_format.leading_digits_pattern[-1])
            ld_match = ld_pattern.match(national_number)
        if size == 0 or ld_match:
            format_pattern = re.compile(num_format.pattern)
            if fullmatch(format_pattern, national_number):
                return num_format
    return None


def _format_nsn_using_pattern(national_number, formatting_pattern, number_format,
                              carrier_code=None):
    # Note that carrier_code is optional - if None or an empty string, no
    # carrier code replacement will take place.
    number_format_rule = formatting_pattern.format
    m_re = re.compile(formatting_pattern.pattern)
    formatted_national_number = U_EMPTY_STRING

    if (number_format == PhoneNumberFormat.NATIONAL and carrier_code and
        formatting_pattern.domestic_carrier_code_formatting_rule):
        # Replace the $CC in the formatting rule with the desired
        # carrier code.
        cc_format_rule = formatting_pattern.domestic_carrier_code_formatting_rule
        cc_format_rule = cc_format_rule.replace(_CC_STRING, carrier_code)

        # Now replace the $FG in the formatting rule with the
        # first group and the carrier code combined in the
        # appropriate way.
        number_format_rule = re.sub(_FIRST_GROUP_PATTERN,
                                    cc_format_rule,
                                    number_format_rule,
                                    count=1)
        formatted_national_number = re.sub(m_re, number_format_rule, national_number)
    else:
        # Use the national prefix formatting rule instead.
        national_prefix_formatting_rule = formatting_pattern.national_prefix_formatting_rule
        if (number_format == PhoneNumberFormat.NATIONAL and
            national_prefix_formatting_rule):
            first_group_rule = re.sub(_FIRST_GROUP_PATTERN,
                                      national_prefix_formatting_rule,
                                      number_format_rule,
                                      count=1)
            formatted_national_number = re.sub(m_re, first_group_rule, national_number)
        else:
            formatted_national_number = re.sub(m_re, number_format_rule, national_number)

    if number_format == PhoneNumberFormat.RFC3966:
        # Strip any leading punctuation.
        m = _SEPARATOR_PATTERN.match(formatted_national_number)
        if m:
            formatted_national_number = re.sub(_SEPARATOR_PATTERN, U_EMPTY_STRING, formatted_national_number, count=1)
        # Replace the rest with a dash between each number group
        formatted_national_number = re.sub(_SEPARATOR_PATTERN, U_DASH, formatted_national_number)

    return formatted_national_number


def example_number(region_code):
    """Gets a valid number for the specified region.

    Arguments:
    region_code -- The region for which an example number is needed.

    Returns a valid fixed-line number for the specified region. Returns None
    when the metadata does not contain such information, or the region 001 is
    passed in.  For 001 (representing non-geographical numbers), call
    example_number_for_non_geo_entity instead.
    """
    return example_number_for_type(region_code, PhoneNumberType.FIXED_LINE)


def invalid_example_number(region_code):
    """Gets an invalid number for the specified region.

    This is useful for unit-testing purposes, where you want to test what
    will happen with an invalid number. Note that the number that is
    returned will always be able to be parsed and will have the correct
    country code. It may also be a valid *short* number/code for this
    region. Validity checking such numbers is handled with shortnumberinfo.

    Arguments:
    region_code -- The region for which an example number is needed.


    Returns an invalid number for the specified region. Returns None when an
    unsupported region or the region 001 (Earth) is passed in.
    """
    if not _is_valid_region_code(region_code):
        return None
    # We start off with a valid fixed-line number since every country
    # supports this. Alternatively we could start with a different number
    # type, since fixed-line numbers typically have a wide breadth of valid
    # number lengths and we may have to make it very short before we get an
    # invalid number.
    metadata = PhoneMetadata.metadata_for_region(region_code.upper())
    desc = _number_desc_by_type(metadata, PhoneNumberType.FIXED_LINE)
    if desc is None or desc.example_number is None:
        # This shouldn't happen; we have a test for this.
        return None  # pragma no cover
    example_number = desc.example_number
    # Try and make the number invalid. We do this by changing the length. We
    # try reducing the length of the number, since currently no region has a
    # number that is the same length as MIN_LENGTH_FOR_NSN. This is probably
    # quicker than making the number longer, which is another
    # alternative. We could also use the possible number pattern to extract
    # the possible lengths of the number to make this faster, but this
    # method is only for unit-testing so simplicity is preferred to
    # performance.  We don't want to return a number that can't be parsed,
    # so we check the number is long enough. We try all possible lengths
    # because phone number plans often have overlapping prefixes so the
    # number 123456 might be valid as a fixed-line number, and 12345 as a
    # mobile number. It would be faster to loop in a different order, but we
    # prefer numbers that look closer to real numbers (and it gives us a
    # variety of different lengths for the resulting phone numbers -
    # otherwise they would all be MIN_LENGTH_FOR_NSN digits long.)
    phone_number_length = len(example_number) - 1
    while phone_number_length >= _MIN_LENGTH_FOR_NSN:
        number_to_try = example_number[:phone_number_length]
        try:
            possibly_valid_number = parse(number_to_try, region_code)
            if not is_valid_number(possibly_valid_number):
                return possibly_valid_number
        except NumberParseException:  # pragma no cover
            # Shouldn't happen: we have already checked the length, we know
            # example numbers have only valid digits, and we know the region
            # code is fine.
            pass
        phone_number_length -= 1

    # We have a test to check that this doesn't happen for any of our
    # supported regions.
    return None  # pragma no cover


def example_number_for_type(region_code, num_type):
    """Gets a valid number for the specified region and number type.

    If None is given as the region_code, then the returned number object
    may belong to any country.

    Arguments:
    region_code -- The region for which an example number is needed, or None.
    num_type -- The type of number that is needed.

    Returns a valid number for the specified region and type. Returns None
    when the metadata does not contain such information or if an invalid
    region or region 001 was specified.  For 001 (representing
    non-geographical numbers), call example_number_for_non_geo_entity instead.
    """
    if region_code is None:
        return _example_number_anywhere_for_type(num_type)
    # Check the region code is valid.
    if not _is_valid_region_code(region_code):
        return None
    metadata = PhoneMetadata.metadata_for_region(region_code.upper())
    desc = _number_desc_by_type(metadata, num_type)
    if desc is not None and desc.example_number is not None:
        try:
            return parse(desc.example_number, region_code)
        except NumberParseException:  # pragma no cover
            pass
    return None


def _example_number_anywhere_for_type(num_type):
    """Gets a valid number for the specified number type (it may belong to any country).

    Arguments:
    num_type -- The type of number that is needed.

    Returns a valid number for the specified type. Returns None when the
    metadata does not contain such information. This should only happen when
    no numbers of this type are allocated anywhere in the world anymore.
    """
    for region_code in SUPPORTED_REGIONS:
        example_numobj = example_number_for_type(region_code, num_type)
        if example_numobj is not None:
            return example_numobj
    # If there wasn't an example number for a region, try the non-geographical entities.
    for country_calling_code in COUNTRY_CODES_FOR_NON_GEO_REGIONS:
        metadata = PhoneMetadata.metadata_for_nongeo_region(country_calling_code, None)
        desc = _number_desc_by_type(metadata, num_type)
        if desc is not None and desc.example_number is not None:
            try:
                return parse(_PLUS_SIGN + unicod(country_calling_code) + desc.example_number, UNKNOWN_REGION)
            except NumberParseException:  # pragma no cover
                pass

    # There are no example numbers of this type for any country in the library.
    return None  # pragma no cover


def example_number_for_non_geo_entity(country_calling_code):
    """Gets a valid number for the specified country calling code for a non-geographical entity.

    Arguments:
    country_calling_code -- The country calling code for a non-geographical entity.

    Returns a valid number for the non-geographical entity. Returns None when
    the metadata does not contain such information, or the country calling
    code passed in does not belong to a non-geographical entity.
    """
    metadata = PhoneMetadata.metadata_for_nongeo_region(country_calling_code, None)
    if metadata is not None:
        # For geographical entities, fixed-line data is always present. However, for non-geographical
        # entities, this is not the case, so we have to go through different types to find the
        # example number. We don't check fixed-line or personal number since they aren't used by
        # non-geographical entities (if this changes, a unit-test will catch this.)
        for desc in (metadata.mobile, metadata.toll_free, metadata.shared_cost, metadata.voip,
                     metadata.voicemail, metadata.uan, metadata.premium_rate):
            try:
                if (desc is not None and desc.example_number is not None):
                    return parse(_PLUS_SIGN + unicod(country_calling_code) + desc.example_number, UNKNOWN_REGION)
            except NumberParseException:
                pass
    return None


def _maybe_append_formatted_extension(numobj, metadata, num_format, number):
    """Appends the formatted extension of a phone number to formatted number,
    if the phone number had an extension specified.
    """
    if numobj.extension:
        if num_format == PhoneNumberFormat.RFC3966:
            return number + _RFC3966_EXTN_PREFIX + numobj.extension
        else:
            if metadata.preferred_extn_prefix is not None:
                return number + metadata.preferred_extn_prefix + numobj.extension
            else:
                return number + _DEFAULT_EXTN_PREFIX + numobj.extension
    return number


def _number_desc_by_type(metadata, num_type):
    """Return the PhoneNumberDesc of the metadata for the given number type"""
    if num_type == PhoneNumberType.PREMIUM_RATE:
        return metadata.premium_rate
    elif num_type == PhoneNumberType.TOLL_FREE:
        return metadata.toll_free
    elif num_type == PhoneNumberType.MOBILE:
        return metadata.mobile
    elif (num_type == PhoneNumberType.FIXED_LINE or
          num_type == PhoneNumberType.FIXED_LINE_OR_MOBILE):
        return metadata.fixed_line
    elif num_type == PhoneNumberType.SHARED_COST:
        return metadata.shared_cost
    elif num_type == PhoneNumberType.VOIP:
        return metadata.voip
    elif num_type == PhoneNumberType.PERSONAL_NUMBER:
        return metadata.personal_number
    elif num_type == PhoneNumberType.PAGER:
        return metadata.pager
    elif num_type == PhoneNumberType.UAN:
        return metadata.uan
    elif num_type == PhoneNumberType.VOICEMAIL:
        return metadata.voicemail
    else:
        return metadata.general_desc


def number_type(numobj):
    """Gets the type of a valid phone number.

    Arguments:
    numobj -- The PhoneNumber object that we want to know the type of.

    Returns the type of the phone number, as a PhoneNumberType value;
    returns PhoneNumberType.UNKNOWN if it is invalid.
    """
    region_code = region_code_for_number(numobj)
    metadata = PhoneMetadata.metadata_for_region_or_calling_code(numobj.country_code, region_code)
    if metadata is None:
        return PhoneNumberType.UNKNOWN
    national_number = national_significant_number(numobj)
    return _number_type_helper(national_number, metadata)


def _number_type_helper(national_number, metadata):
    """Return the type of the given number against the metadata"""
    if not _is_number_matching_desc(national_number, metadata.general_desc):
        return PhoneNumberType.UNKNOWN
    if _is_number_matching_desc(national_number, metadata.premium_rate):
        return PhoneNumberType.PREMIUM_RATE
    if _is_number_matching_desc(national_number, metadata.toll_free):
        return PhoneNumberType.TOLL_FREE
    if _is_number_matching_desc(national_number, metadata.shared_cost):
        return PhoneNumberType.SHARED_COST
    if _is_number_matching_desc(national_number, metadata.voip):
        return PhoneNumberType.VOIP
    if _is_number_matching_desc(national_number, metadata.personal_number):
        return PhoneNumberType.PERSONAL_NUMBER
    if _is_number_matching_desc(national_number, metadata.pager):
        return PhoneNumberType.PAGER
    if _is_number_matching_desc(national_number, metadata.uan):
        return PhoneNumberType.UAN
    if _is_number_matching_desc(national_number, metadata.voicemail):
        return PhoneNumberType.VOICEMAIL

    if _is_number_matching_desc(national_number, metadata.fixed_line):
        if metadata.same_mobile_and_fixed_line_pattern:
            return PhoneNumberType.FIXED_LINE_OR_MOBILE
        elif _is_number_matching_desc(national_number, metadata.mobile):
            return PhoneNumberType.FIXED_LINE_OR_MOBILE
        return PhoneNumberType.FIXED_LINE

    # Otherwise, test to see if the number is mobile. Only do this if certain
    # that the patterns for mobile and fixed line aren't the same.
    if (not metadata.same_mobile_and_fixed_line_pattern and
        _is_number_matching_desc(national_number, metadata.mobile)):
        return PhoneNumberType.MOBILE
    return PhoneNumberType.UNKNOWN


def _is_number_matching_desc(national_number, number_desc):
    """Determine if the number matches the given PhoneNumberDesc"""
    # Check if any possible number lengths are present; if so, we use them to avoid checking the
    # validation pattern if they don't match. If they are absent, this means they match the general
    # description, which we have already checked before checking a specific number type.
    if number_desc is None:
        return False
    actual_length = len(national_number)
    possible_lengths = number_desc.possible_length
    if len(possible_lengths) > 0 and actual_length not in possible_lengths:
        return False
    return _match_national_number(national_number, number_desc, False)


def is_valid_number(numobj):
    """Tests whether a phone number matches a valid pattern.

    Note this doesn't verify the number is actually in use, which is
    impossible to tell by just looking at a number itself.  It only verifies
    whether the parsed, canonicalised number is valid: not whether a
    particular series of digits entered by the user is diallable from the
    region provided when parsing. For example, the number +41 (0) 78 927 2696
    can be parsed into a number with country code "41" and national
    significant number "789272696". This is valid, while the original string
    is not diallable.

    Arguments:
    numobj -- The phone number object that we want to validate

    Returns a boolean that indicates whether the number is of a valid pattern.
    """
    region_code = region_code_for_number(numobj)
    return is_valid_number_for_region(numobj, region_code)


def is_valid_number_for_region(numobj, region_code):
    """Tests whether a phone number is valid for a certain region.

    Note this doesn't verify the number is actually in use, which is
    impossible to tell by just looking at a number itself. If the country
    calling code is not the same as the country calling code for the region,
    this immediately exits with false. After this, the specific number pattern
    rules for the region are examined. This is useful for determining for
    example whether a particular number is valid for Canada, rather than just
    a valid NANPA number.

    Warning: In most cases, you want to use is_valid_number instead. For
    example, this method will mark numbers from British Crown dependencies
    such as the Isle of Man as invalid for the region "GB" (United Kingdom),
    since it has its own region code, "IM", which may be undesirable.

    Arguments:
    numobj -- The phone number object that we want to validate.
    region_code -- The region that we want to validate the phone number for.

    Returns a boolean that indicates whether the number is of a valid pattern.
    """
    country_code = numobj.country_code
    if region_code is None:
        return False
    metadata = PhoneMetadata.metadata_for_region_or_calling_code(country_code, region_code.upper())
    if (metadata is None or
        (region_code != REGION_CODE_FOR_NON_GEO_ENTITY and
         country_code != country_code_for_valid_region(region_code))):
        # Either the region code was invalid, or the country calling code for
        # this number does not match that of the region code.
        return False
    nsn = national_significant_number(numobj)
    return (_number_type_helper(nsn, metadata) != PhoneNumberType.UNKNOWN)


def region_code_for_number(numobj):
    """Returns the region where a phone number is from.

    This could be used for geocoding at the region level. Only guarantees
    correct results for valid, full numbers (not short-codes, or invalid
    numbers).

    Arguments:
    numobj -- The phone number object whose origin we want to know

    Returns the region where the phone number is from, or None if no region
    matches this calling code.

    """
    country_code = numobj.country_code
    regions = COUNTRY_CODE_TO_REGION_CODE.get(country_code, None)
    if regions is None:
        return None

    if len(regions) == 1:
        return regions[0]
    else:
        return _region_code_for_number_from_list(numobj, regions)


def _region_code_for_number_from_list(numobj, regions):
    """Find the region in a list that matches a number"""
    national_number = national_significant_number(numobj)
    for region_code in regions:
        # If leading_digits is present, use this. Otherwise, do full
        # validation.
        # Metadata cannot be None because the region codes come from
        # the country calling code map.
        metadata = PhoneMetadata.metadata_for_region(region_code.upper(), None)
        if metadata is None:
            continue
        if metadata.leading_digits is not None:
            leading_digit_re = re.compile(metadata.leading_digits)
            match = leading_digit_re.match(national_number)
            if match:
                return region_code
        elif _number_type_helper(national_number, metadata) != PhoneNumberType.UNKNOWN:
            return region_code
    return None


def region_code_for_country_code(country_code):
    """Returns the region code that matches a specific country calling code.

    In the case of no region code being found, UNKNOWN_REGION ('ZZ') will be
    returned. In the case of multiple regions, the one designated in the
    metadata as the "main" region for this calling code will be returned.  If
    the country_code entered is valid but doesn't match a specific region
    (such as in the case of non-geographical calling codes like 800) the value
    "001" will be returned (corresponding to the value for World in the UN
    M.49 schema).
    """
    regions = COUNTRY_CODE_TO_REGION_CODE.get(country_code, None)
    if regions is None:
        return UNKNOWN_REGION
    else:
        return regions[0]


def region_codes_for_country_code(country_code):
    """Returns a list with the region codes that match the specific country calling code.

    For non-geographical country calling codes, the region code 001 is
    returned. Also, in the case of no region code being found, an empty
    list is returned.
    """
    regions = COUNTRY_CODE_TO_REGION_CODE.get(country_code, None)
    if regions is None:
        return ()
    else:
        return regions


def country_code_for_region(region_code):
    """Returns the country calling code for a specific region.

    For example, this would be 1 for the United States, and 64 for New
    Zealand.

    Arguments:
    region_code -- The region that we want to get the country calling code for.

    Returns the country calling code for the region denoted by region_code.
    """
    if not _is_valid_region_code(region_code):
        return 0
    return country_code_for_valid_region(region_code)


def country_code_for_valid_region(region_code):
    """Returns the country calling code for a specific region.

    For example, this would be 1 for the United States, and 64 for New
    Zealand.  Assumes the region is already valid.

    Arguments:
    region_code -- The region that we want to get the country calling code for.

    Returns the country calling code for the region denoted by region_code.
    """
    metadata = PhoneMetadata.metadata_for_region(region_code.upper(), None)
    if metadata is None:
        raise Exception("Invalid region code %s" % region_code)
    return metadata.country_code


def ndd_prefix_for_region(region_code, strip_non_digits):
    """Returns the national dialling prefix for a specific region.

    For example, this would be 1 for the United States, and 0 for New
    Zealand. Set strip_non_digits to True to strip symbols like "~" (which
    indicates a wait for a dialling tone) from the prefix returned. If no
    national prefix is present, we return None.

    Warning: Do not use this method for do-your-own formatting - for some
    regions, the national dialling prefix is used only for certain types of
    numbers. Use the library's formatting functions to prefix the national
    prefix when required.

    Arguments:
    region_code -- The region that we want to get the dialling prefix for.
    strip_non_digits -- whether to strip non-digits from the national
               dialling prefix.

    Returns the dialling prefix for the region denoted by region_code.
    """
    if region_code is None:
        return None
    metadata = PhoneMetadata.metadata_for_region(region_code.upper(), None)
    if metadata is None:
        return None
    national_prefix = metadata.national_prefix
    if national_prefix is None or len(national_prefix) == 0:
        return None
    if strip_non_digits:
        # Note: if any other non-numeric symbols are ever used in national
        # prefixes, these would have to be removed here as well.
        national_prefix = re.sub(U_TILDE, U_EMPTY_STRING, national_prefix)
    return national_prefix


def is_nanpa_country(region_code):
    """Checks if this region is a NANPA region.

    Returns True if region_code is one of the regions under the North American
    Numbering Plan Administration (NANPA).
    """
    return region_code in _NANPA_REGIONS


def is_alpha_number(number):
    """Checks if the number is a valid vanity (alpha) number such as 800
    MICROSOFT. A valid vanity number will start with at least 3 digits and
    will have three or more alpha characters. This does not do region-specific
    checks - to work out if this number is actually valid for a region, it
    should be parsed and methods such as is_possible_number_with_reason() and
    is_valid_number() should be used.

    Arguments:
    number -- the number that needs to be checked

    Returns True if the number is a valid vanity number
    """
    if not _is_viable_phone_number(number):
        # Number is too short, or doesn't match the basic phone number pattern.
        return False
    extension, stripped_number = _maybe_strip_extension(number)
    return bool(fullmatch(_VALID_ALPHA_PHONE_PATTERN, stripped_number))


def is_possible_number(numobj):
    """Convenience wrapper around is_possible_number_with_reason.

    Instead of returning the reason for failure, this method returns true if
    the number is either a possible fully-qualified number (containing the area
    code and country code), or if the number could be a possible local number
    (with a country code, but missing an area code). Local numbers are
    considered possible if they could be possibly dialled in this format: if
    the area code is needed for a call to connect, the number is not considered
    possible without it.

    Arguments:
    numobj -- the number object that needs to be checked

    Returns True if the number is possible

    """
    result = is_possible_number_with_reason(numobj)
    return (result == ValidationResult.IS_POSSIBLE or
            result == ValidationResult.IS_POSSIBLE_LOCAL_ONLY)


def is_possible_number_for_type(numobj, numtype):
    """Convenience wrapper around is_possible_number_for_type_with_reason.

    Instead of returning the reason for failure, this method returns true if
    the number is either a possible fully-qualified number (containing the area
    code and country code), or if the number could be a possible local number
    (with a country code, but missing an area code). Local numbers are
    considered possible if they could be possibly dialled in this format: if
    the area code is needed for a call to connect, the number is not considered
    possible without it.

    Arguments:
    numobj -- the number object that needs to be checked
    numtype -- the type we are interested in

    Returns True if the number is possible

    """
    result = is_possible_number_for_type_with_reason(numobj, numtype)
    return (result == ValidationResult.IS_POSSIBLE or
            result == ValidationResult.IS_POSSIBLE_LOCAL_ONLY)


def _test_number_length(national_number, metadata, numtype=PhoneNumberType.UNKNOWN):
    """Helper method to check a number against possible lengths for this number,
    and determine whether it matches, or is too short or too long.
    """
    desc_for_type = _number_desc_by_type(metadata, numtype)
    if desc_for_type is None:
        possible_lengths = metadata.general_desc.possible_length
        local_lengths = ()
    else:
        # There should always be "possibleLengths" set for every element. This is declared in the XML
        # schema which is verified by PhoneNumberMetadataSchemaTest.
        # For size efficiency, where a sub-description (e.g. fixed-line) has the same possibleLengths
        # as the parent, this is missing, so we fall back to the general desc (where no numbers of the
        # type exist at all, there is one possible length (-1) which is guaranteed not to match the
        # length of any real phone number).
        possible_lengths = desc_for_type.possible_length
        if len(possible_lengths) == 0:  # pragma no cover: Python sub-descs all have possible_length
            possible_lengths = metadata.general_desc.possible_length
        local_lengths = desc_for_type.possible_length_local_only

    if numtype == PhoneNumberType.FIXED_LINE_OR_MOBILE:
        if not _desc_has_possible_number_data(_number_desc_by_type(metadata, PhoneNumberType.FIXED_LINE)):
            # The rare case has been encountered where no fixedLine data is available (true for some
            # non-geographical entities), so we just check mobile.
            return _test_number_length(national_number, metadata, PhoneNumberType.MOBILE)
        else:
            mobile_desc = _number_desc_by_type(metadata, PhoneNumberType.MOBILE)
            if _desc_has_possible_number_data(mobile_desc):
                # Merge the mobile data in if there was any. We have to make a copy to do this.
                possible_lengths = list(possible_lengths)
                # Note that when adding the possible lengths from mobile, we have to again check they
                # aren't empty since if they are this indicates they are the same as the general desc and
                # should be obtained from there.
                if len(mobile_desc.possible_length) == 0:  # pragma no cover: Python sub-descs all have possible_length
                    possible_lengths += metadata.general_desc.possible_length
                else:
                    possible_lengths += mobile_desc.possible_length
                # The current list is sorted; we need to merge in the new list and re-sort (duplicates
                # are okay). Sorting isn't so expensive because the lists are very small.
                list.sort(possible_lengths)

                if len(local_lengths) == 0:
                    local_lengths = mobile_desc.possible_length_local_only
                else:
                    local_lengths = list(local_lengths)
                    local_lengths += mobile_desc.possible_length_local_only
                    list.sort(local_lengths)

    # If the type is not supported at all (indicated by a missing PhoneNumberDesc) we return invalid length.
    if desc_for_type is None:
        return ValidationResult.INVALID_LENGTH

    actual_length = len(national_number)
    # This is safe because there is never an overlap beween the possible lengths and the local-only
    # lengths; this is checked at build time.
    if actual_length in local_lengths:
        return ValidationResult.IS_POSSIBLE_LOCAL_ONLY

    minimum_length = possible_lengths[0]
    if minimum_length == actual_length:
        return ValidationResult.IS_POSSIBLE
    elif minimum_length > actual_length:
        return ValidationResult.TOO_SHORT
    elif possible_lengths[-1] < actual_length:
        return ValidationResult.TOO_LONG
    # We skip the first element; we've already checked it.
    if actual_length in possible_lengths[1:]:
        return ValidationResult.IS_POSSIBLE
    else:
        return ValidationResult.INVALID_LENGTH


def is_possible_number_with_reason(numobj):
    return is_possible_number_for_type_with_reason(numobj, PhoneNumberType.UNKNOWN)


def is_possible_number_for_type_with_reason(numobj, numtype):
    """Check whether a phone number is a possible number of a particular type.

    For types that don't exist in a particular region, this will return a result
    that isn't so useful; it is recommended that you use
    supported_types_for_region or supported_types_for_non_geo_entity
    respectively before calling this method to determine whether you should call
    it for this number at all.

    This provides a more lenient check than is_valid_number in the following sense:

     - It only checks the length of phone numbers. In particular, it doesn't
       check starting digits of the number.

     - For some numbers (particularly fixed-line), many regions have the
       concept of area code, which together with subscriber number constitute
       the national significant number. It is sometimes okay to dial only the
       subscriber number when dialing in the same area. This function will
       return IS_POSSIBLE_LOCAL_ONLY if the subscriber-number-only version is
       passed in. On the other hand, because is_valid_number validates using
       information on both starting digits (for fixed line numbers, that would
       most likely be area codes) and length (obviously includes the length of
       area codes for fixed line numbers), it will return false for the
       subscriber-number-only version.

    Arguments:
    numobj -- The number object that needs to be checked
    numtype -- The type we are interested in

    Returns a value from ValidationResult which indicates whether the number
    is possible
    """
    national_number = national_significant_number(numobj)
    country_code = numobj.country_code
    # Note: For regions that share a country calling code, like NANPA numbers,
    # we just use the rules from the default region (US in this case) since the
    # region_code_for_number will not work if the number is possible but not
    # valid. There is in fact one country calling code (290) where the possible
    # number pattern differs between various regions (Saint Helena and Tristan
    # da Cuñha), but this is handled by putting all possible lengths for any
    # country with this country calling code in the metadata for the default
    # region in this case.
    if not _has_valid_country_calling_code(country_code):
        return ValidationResult.INVALID_COUNTRY_CODE
    region_code = region_code_for_country_code(country_code)
    # Metadata cannot be None because the country calling code is valid.
    metadata = PhoneMetadata.metadata_for_region_or_calling_code(country_code, region_code)
    return _test_number_length(national_number, metadata, numtype)


def is_possible_number_string(number, region_dialing_from):
    """Check whether a phone number string is a possible number.

    Takes a number in the form of a string, and the region where the number
    could be dialed from. It provides a more lenient check than
    is_valid_number; see is_possible_number_with_reason() for details.

    This method first parses the number, then invokes is_possible_number with
    the resultant PhoneNumber object.

    Arguments:
    number -- The number that needs to be checked, in the form of a string.
    region_dialling_from -- The region that we are expecting the number to be
              dialed from.  Note this is different from the region where the
              number belongs.  For example, the number +1 650 253 0000 is a
              number that belongs to US. When written in this form, it can be
              dialed from any region. When it is written as 00 1 650 253 0000,
              it can be dialed from any region which uses an international
              dialling prefix of 00. When it is written as 650 253 0000, it
              can only be dialed from within the US, and when written as 253
              0000, it can only be dialed from within a smaller area in the US
              (Mountain View, CA, to be more specific).

    Returns True if the number is possible
    """
    try:
        return is_possible_number(parse(number, region_dialing_from))
    except NumberParseException:
        return False


def truncate_too_long_number(numobj):
    """Truncate a number object that is too long.

    Attempts to extract a valid number from a phone number that is too long
    to be valid, and resets the PhoneNumber object passed in to that valid
    version. If no valid number could be extracted, the PhoneNumber object
    passed in will not be modified.

    Arguments:
    numobj -- A PhoneNumber object which contains a number that is too long to
              be valid.

    Returns True if a valid phone number can be successfully extracted.
    """
    if is_valid_number(numobj):
        return True
    numobj_copy = PhoneNumber()
    numobj_copy.merge_from(numobj)
    national_number = numobj.national_number

    while not is_valid_number(numobj_copy):
        # Strip a digit off the RHS
        national_number = national_number // 10
        numobj_copy.national_number = national_number
        validation_result = is_possible_number_with_reason(numobj_copy)
        if (validation_result == ValidationResult.TOO_SHORT or
            national_number == 0):
            return False
    # To reach here, numobj_copy is a valid number.  Modify the original object
    numobj.national_number = national_number
    return True


def _extract_country_code(number):
    """Extracts country calling code from number.

    Returns a 2-tuple of (country_calling_code, rest_of_number).  It assumes
    that the leading plus sign or IDD has already been removed.  Returns (0,
    number) if number doesn't start with a valid country calling code.
    """

    if len(number) == 0 or number[0] == U_ZERO:
        # Country codes do not begin with a '0'.
        return (0, number)
    for ii in range(1, min(len(number), _MAX_LENGTH_COUNTRY_CODE) + 1):
        try:
            country_code = int(number[:ii])
            if country_code in COUNTRY_CODE_TO_REGION_CODE:
                return (country_code, number[ii:])
        except Exception:
            pass
    return (0, number)


def _maybe_extract_country_code(number, metadata, keep_raw_input, numobj):
    """Tries to extract a country calling code from a number.

    This method will return zero if no country calling code is considered to
    be present. Country calling codes are extracted in the following ways:

     - by stripping the international dialing prefix of the region the person
       is dialing from, if this is present in the number, and looking at the
       next digits

     - by stripping the '+' sign if present and then looking at the next
       digits

     - by comparing the start of the number and the country calling code of
       the default region.  If the number is not considered possible for the
       numbering plan of the default region initially, but starts with the
       country calling code of this region, validation will be reattempted
       after stripping this country calling code. If this number is considered
       a possible number, then the first digits will be considered the country
       calling code and removed as such.

    It will raise a NumberParseException if the number starts with a '+' but
    the country calling code supplied after this does not match that of any
    known region.

    Arguments:
    number -- non-normalized telephone number that we wish to extract a
              country calling code from; may begin with '+'
    metadata -- metadata about the region this number may be from, or None
    keep_raw_input -- True if the country_code_source and
              preferred_carrier_code fields of numobj should be populated.
    numobj -- The PhoneNumber object where the country_code and
              country_code_source need to be populated. Note the country_code
              is always populated, whereas country_code_source is only
              populated when keep_raw_input is True.

    Returns a 2-tuple containing:
      - the country calling code extracted or 0 if none could be extracted
      - a string holding the national significant number, in the case
        that a country calling code was extracted. If no country calling code
        was extracted, this will be empty.
    """
    if len(number) == 0:
        return (0, U_EMPTY_STRING)
    full_number = number
    # Set the default prefix to be something that will never match.
    possible_country_idd_prefix = unicod("NonMatch")
    if metadata is not None and metadata.international_prefix is not None:
        possible_country_idd_prefix = metadata.international_prefix

    country_code_source, full_number = _maybe_strip_i18n_prefix_and_normalize(full_number,
                                                                              possible_country_idd_prefix)
    if keep_raw_input:
        numobj.country_code_source = country_code_source

    if country_code_source != CountryCodeSource.FROM_DEFAULT_COUNTRY:
        if len(full_number) <= _MIN_LENGTH_FOR_NSN:
            raise NumberParseException(NumberParseException.TOO_SHORT_AFTER_IDD,
                                       "Phone number had an IDD, but after this was not " +
                                       "long enough to be a viable phone number.")
        potential_country_code, rest_of_number = _extract_country_code(full_number)
        if potential_country_code != 0:
            numobj.country_code = potential_country_code
            return (potential_country_code, rest_of_number)

        # If this fails, they must be using a strange country calling code
        # that we don't recognize, or that doesn't exist.
        raise NumberParseException(NumberParseException.INVALID_COUNTRY_CODE,
                                   "Country calling code supplied was not recognised.")
    elif metadata is not None:
        # Check to see if the number starts with the country calling code for
        # the default region. If so, we remove the country calling code, and
        # do some checks on the validity of the number before and after.
        default_country_code = metadata.country_code
        default_country_code_str = str(metadata.country_code)
        normalized_number = full_number
        if normalized_number.startswith(default_country_code_str):
            potential_national_number = full_number[len(default_country_code_str):]
            general_desc = metadata.general_desc
            _, potential_national_number, _ = _maybe_strip_national_prefix_carrier_code(potential_national_number,
                                                                                        metadata)

            # If the number was not valid before but is valid now, or if it
            # was too long before, we consider the number with the country
            # calling code stripped to be a better result and keep that
            # instead.
            if ((not _match_national_number(full_number, general_desc, False) and
                 _match_national_number(potential_national_number, general_desc, False)) or
                (_test_number_length(full_number, metadata) == ValidationResult.TOO_LONG)):
                if keep_raw_input:
                    numobj.country_code_source = CountryCodeSource.FROM_NUMBER_WITHOUT_PLUS_SIGN
                numobj.country_code = default_country_code
                return (default_country_code, potential_national_number)

    # No country calling code present.
    numobj.country_code = 0
    return (0, U_EMPTY_STRING)


def _parse_prefix_as_idd(idd_pattern, number):
    """Strips the IDD from the start of the number if present.

    Helper function used by _maybe_strip_i18n_prefix_and_normalize().

    Returns a 2-tuple:
      - Boolean indicating if IDD was stripped
      - Number with IDD stripped
    """
    match = idd_pattern.match(number)
    if match:
        match_end = match.end()
        # Only strip this if the first digit after the match is not a 0, since
        # country calling codes cannot begin with 0.
        digit_match = _CAPTURING_DIGIT_PATTERN.search(number[match_end:])
        if digit_match:
            normalized_group = normalize_digits_only(digit_match.group(1))
            if normalized_group == U_ZERO:
                return (False, number)
        return (True, number[match_end:])
    return (False, number)


def _maybe_strip_i18n_prefix_and_normalize(number, possible_idd_prefix):
    """Strips any international prefix (such as +, 00, 011) present in the
    number provided, normalizes the resulting number, and indicates if an
    international prefix was present.

    Arguments:
    number -- The non-normalized telephone number that we wish to strip any international
              dialing prefix from.
    possible_idd_prefix -- The international direct dialing prefix from the region we
              think this number may be dialed in.

    Returns a 2-tuple containing:
      - The corresponding CountryCodeSource if an international dialing prefix
        could be removed from the number, otherwise
        CountryCodeSource.FROM_DEFAULT_COUNTRY if the number did not seem to
        be in international format.
      - The number with the prefix stripped.
    """
    if len(number) == 0:
        return (CountryCodeSource.FROM_DEFAULT_COUNTRY, number)
    # Check to see if the number begins with one or more plus signs.
    m = _PLUS_CHARS_PATTERN.match(number)
    if m:
        number = number[m.end():]
        # Can now normalize the rest of the number since we've consumed the
        # "+" sign at the start.
        return (CountryCodeSource.FROM_NUMBER_WITH_PLUS_SIGN,
                _normalize(number))

    # Attempt to parse the first digits as an international prefix.
    idd_pattern = re.compile(possible_idd_prefix)
    number = _normalize(number)
    stripped, number = _parse_prefix_as_idd(idd_pattern, number)
    if stripped:
        return (CountryCodeSource.FROM_NUMBER_WITH_IDD, number)
    else:
        return (CountryCodeSource.FROM_DEFAULT_COUNTRY, number)


def _maybe_strip_national_prefix_carrier_code(number, metadata):
    """Strips any national prefix (such as 0, 1) present in a number.

    Arguments:
    number -- The normalized telephone number that we wish to strip any
              national dialing prefix from
    metadata -- The metadata for the region that we think this number
              is from.

    Returns a 3-tuple of
     - The carrier code extracted if it is present, otherwise an empty string.
     - The number with the prefix stripped.
     - Boolean indicating if a national prefix or carrier code (or both) could be extracted.
     """
    carrier_code = U_EMPTY_STRING
    possible_national_prefix = metadata.national_prefix_for_parsing
    if (len(number) == 0 or
        possible_national_prefix is None or
        len(possible_national_prefix) == 0):
        # Early return for numbers of zero length.
        return (U_EMPTY_STRING, number, False)

    # Attempt to parse the first digits as a national prefix.
    prefix_pattern = re.compile(possible_national_prefix)
    prefix_match = prefix_pattern.match(number)
    if prefix_match:
        general_desc = metadata.general_desc
        # Check if the original number is viable.
        is_viable_original_number = _match_national_number(number, general_desc, False)
        # prefix_match.groups() == () implies nothing was captured by the
        # capturing groups in possible_national_prefix; therefore, no
        # transformation is necessary, and we just remove the national prefix.
        num_groups = len(prefix_match.groups())
        transform_rule = metadata.national_prefix_transform_rule
        if (transform_rule is None or
            len(transform_rule) == 0 or
            prefix_match.groups()[num_groups - 1] is None):
            # If the original number was viable, and the resultant number is not, we return.
            # Check that the resultant number is viable. If not, return.
            national_number_match = _match_national_number(number[prefix_match.end():], general_desc, False)
            if (is_viable_original_number and not national_number_match):
                return (U_EMPTY_STRING, number, False)

            if (num_groups > 0 and
                prefix_match.groups(num_groups) is not None):
                carrier_code = prefix_match.group(1)
            return (carrier_code, number[prefix_match.end():], True)
        else:
            # Check that the resultant number is still viable. If not,
            # return. Check this by copying the number and making the
            # transformation on the copy first.
            transformed_number = re.sub(prefix_pattern, transform_rule, number, count=1)
            national_number_match = _match_national_number(transformed_number, general_desc, False)
            if (is_viable_original_number and not national_number_match):
                return ("", number, False)
            if num_groups > 1:
                carrier_code = prefix_match.group(1)
            return (carrier_code, transformed_number, True)
    else:
        return (carrier_code, number, False)


def _maybe_strip_extension(number):
    """Strip extension from the end of a number string.

    Strips any extension (as in, the part of the number dialled after the
    call is connected, usually indicated with extn, ext, x or similar) from
    the end of the number, and returns it.

    Arguments:
    number -- the non-normalized telephone number that we wish to strip the extension from.

    Returns a 2-tuple of:
     - the phone extension (or "" or not present)
     - the number before the extension.
    """
    match = _EXTN_PATTERN.search(number)
    # If we find a potential extension, and the number preceding this is a
    # viable number, we assume it is an extension.
    if match and _is_viable_phone_number(number[:match.start()]):
        # The numbers are captured into groups in the regular expression.
        for group in match.groups():
            # We go through the capturing groups until we find one that
            # captured some digits. If none did, then we will return the empty
            # string.
            if group is not None:
                return (group, number[:match.start()])
    return ("", number)


def _check_region_for_parsing(number, default_region):
    """Checks to see that the region code used is valid, or if it is not
    valid, that the number to parse starts with a + symbol so that we can
    attempt to infer the region from the number.  Returns False if it cannot
    use the region provided and the region cannot be inferred.
    """
    if not _is_valid_region_code(default_region):
        # If the number is None or empty, we can't infer the region.
        if number is None or len(number) == 0:
            return False
        match = _PLUS_CHARS_PATTERN.match(number)
        if match is None:
            return False
    return True


def _set_italian_leading_zeros_for_phone_number(national_number, numobj):
    """A helper function to set the values related to leading zeros in a
    PhoneNumber."""
    if len(national_number) > 1 and national_number[0] == U_ZERO:
        numobj.italian_leading_zero = True
        number_of_leading_zeros = 1
        # Note that if the number is all "0"s, the last "0" is not counted as
        # a leading zero.
        while (number_of_leading_zeros < len(national_number) - 1 and
               national_number[number_of_leading_zeros] == U_ZERO):
            number_of_leading_zeros += 1
        if number_of_leading_zeros != 1:
            numobj.number_of_leading_zeros = number_of_leading_zeros


def parse(number, region=None, keep_raw_input=False,
          numobj=None, _check_region=True):
    """Parse a string and return a corresponding PhoneNumber object.

    The method is quite lenient and looks for a number in the input text
    (raw input) and does not check whether the string is definitely only a
    phone number. To do this, it ignores punctuation and white-space, as
    well as any text before the number (e.g. a leading "Tel: ") and trims
    the non-number bits.  It will accept a number in any format (E164,
    national, international etc), assuming it can be interpreted with the
    defaultRegion supplied. It also attempts to convert any alpha characters
    into digits if it thinks this is a vanity number of the type "1800
    MICROSOFT".

    This method will throw a NumberParseException if the number is not
    considered to be a possible number. Note that validation of whether the
    number is actually a valid number for a particular region is not
    performed. This can be done separately with is_valid_number.

    Note this method canonicalizes the phone number such that different
    representations can be easily compared, no matter what form it was
    originally entered in (e.g. national, international). If you want to
    record context about the number being parsed, such as the raw input that
    was entered, how the country code was derived etc. then ensure
    keep_raw_input is set.

    Note if any new field is added to this method that should always be filled
    in, even when keep_raw_input is False, it should also be handled in the
    _copy_core_fields_only() function.

    Arguments:
    number -- The number that we are attempting to parse. This can
              contain formatting such as +, ( and -, as well as a phone
              number extension. It can also be provided in RFC3966 format.
    region -- The region that we are expecting the number to be from. This
              is only used if the number being parsed is not written in
              international format. The country_code for the number in
              this case would be stored as that of the default region
              supplied. If the number is guaranteed to start with a '+'
              followed by the country calling code, then None or
              UNKNOWN_REGION can be supplied.
    keep_raw_input -- Whether to populate the raw_input field of the
              PhoneNumber object with number (as well as the
              country_code_source field).
    numobj -- An optional existing PhoneNumber object to receive the
              parsing results
    _check_region -- Whether to check the supplied region parameter;
              should always be True for external callers.

    Returns a PhoneNumber object filled with the parse number.

    Raises:
    NumberParseException if the string is not considered to be a viable
    phone number (e.g.  too few or too many digits) or if no default
    region was supplied and the number is not in international format
    (does not start with +).

    """
    if numobj is None:
        numobj = PhoneNumber()
    if number is None:
        raise NumberParseException(NumberParseException.NOT_A_NUMBER,
                                   "The phone number supplied was None.")
    elif len(number) > _MAX_INPUT_STRING_LENGTH:
        raise NumberParseException(NumberParseException.TOO_LONG,
                                   "The string supplied was too long to parse.")

    national_number = _build_national_number_for_parsing(number)

    if not _is_viable_phone_number(national_number):
        raise NumberParseException(NumberParseException.NOT_A_NUMBER,
                                   "The string supplied did not seem to be a phone number.")

    # Check the region supplied is valid, or that the extracted number starts
    # with some sort of + sign so the number's region can be determined.
    if _check_region and not _check_region_for_parsing(national_number, region):
        raise NumberParseException(NumberParseException.INVALID_COUNTRY_CODE,
                                   "Missing or invalid default region.")
    if keep_raw_input:
        numobj.raw_input = number

    # Attempt to parse extension first, since it doesn't require
    # region-specific data and we want to have the non-normalised number here.
    extension, national_number = _maybe_strip_extension(national_number)
    if len(extension) > 0:
        numobj.extension = extension
    if region is None:
        metadata = None
    else:
        metadata = PhoneMetadata.metadata_for_region(region.upper(), None)

    country_code = 0
    try:
        country_code, normalized_national_number = _maybe_extract_country_code(national_number,
                                                                               metadata,
                                                                               keep_raw_input,
                                                                               numobj)
    except NumberParseException:
        _, e, _ = sys.exc_info()
        matchobj = _PLUS_CHARS_PATTERN.match(national_number)
        if (e.error_type == NumberParseException.INVALID_COUNTRY_CODE and
            matchobj is not None):
            # Strip the plus-char, and try again.
            country_code, normalized_national_number = _maybe_extract_country_code(national_number[matchobj.end():],
                                                                                   metadata,
                                                                                   keep_raw_input,
                                                                                   numobj)
            if country_code == 0:
                raise NumberParseException(NumberParseException.INVALID_COUNTRY_CODE,
                                           "Could not interpret numbers after plus-sign.")
        else:
            raise

    if country_code != 0:
        number_region = region_code_for_country_code(country_code)
        if number_region != region:
            # Metadata cannot be null because the country calling code is valid.
            metadata = PhoneMetadata.metadata_for_region_or_calling_code(country_code, number_region)
    else:
        # If no extracted country calling code, use the region supplied
        # instead. The national number is just the normalized version of the
        # number we were given to parse.
        normalized_national_number += _normalize(national_number)
        if region is not None:
            country_code = metadata.country_code
            numobj.country_code = country_code
        elif keep_raw_input:
            numobj.country_code_source = CountryCodeSource.UNSPECIFIED

    if len(normalized_national_number) < _MIN_LENGTH_FOR_NSN:
        raise NumberParseException(NumberParseException.TOO_SHORT_NSN,
                                   "The string supplied is too short to be a phone number.")
    if metadata is not None:
        potential_national_number = normalized_national_number
        carrier_code, potential_national_number, _ = _maybe_strip_national_prefix_carrier_code(potential_national_number,
                                                                                               metadata)
        # We require that the NSN remaining after stripping the national
        # prefix and carrier code be long enough to be a possible length for
        # the region. Otherwise, we don't do the stripping, since the original
        # number could be a valid short number.
        validation_result = _test_number_length(potential_national_number, metadata)
        if validation_result not in (ValidationResult.TOO_SHORT,
                                     ValidationResult.IS_POSSIBLE_LOCAL_ONLY,
                                     ValidationResult.INVALID_LENGTH):
            normalized_national_number = potential_national_number
            if keep_raw_input and carrier_code is not None and len(carrier_code) > 0:
                numobj.preferred_domestic_carrier_code = carrier_code
    len_national_number = len(normalized_national_number)
    if len_national_number < _MIN_LENGTH_FOR_NSN:  # pragma no cover
        # Check of _is_viable_phone_number() at the top of this function makes
        # this effectively unhittable.
        raise NumberParseException(NumberParseException.TOO_SHORT_NSN,
                                   "The string supplied is too short to be a phone number.")
    if len_national_number > _MAX_LENGTH_FOR_NSN:
        raise NumberParseException(NumberParseException.TOO_LONG,
                                   "The string supplied is too long to be a phone number.")
    _set_italian_leading_zeros_for_phone_number(normalized_national_number, numobj)
    numobj.national_number = to_long(normalized_national_number)
    return numobj


def _build_national_number_for_parsing(number):
    """Converts number to a form that we can parse and return it if it is
    written in RFC3966; otherwise extract a possible number out of it and return it."""
    index_of_phone_context = number.find(_RFC3966_PHONE_CONTEXT)
    if index_of_phone_context >= 0:
        phone_context_start = index_of_phone_context + len(_RFC3966_PHONE_CONTEXT)
        # If the phone context contains a phone number prefix, we need to
        # capture it, whereas domains will be ignored.
        if (phone_context_start < (len(number) - 1) and
            number[phone_context_start] == _PLUS_SIGN):
            # Additional parameters might follow the phone context. If so, we
            # will remove them here because the parameters after phone context
            # are not important for parsing the phone number.
            phone_context_end = number.find(U_SEMICOLON, phone_context_start)
            if phone_context_end > 0:
                national_number = number[phone_context_start:phone_context_end]
            else:
                national_number = number[phone_context_start:]
        else:
            national_number = U_EMPTY_STRING
        # Now append everything between the "tel:" prefix and the
        # phone-context. This should include the national number, an optional
        # extension or isdn-subaddress component. Note we also handle the case
        # when "tel:" is missing, as we have seen in some of the phone number
        # inputs.  In that case we append everything from the beginning.
        index_of_rfc3996_prefix = number.find(_RFC3966_PREFIX)
        index_of_national_number = ((index_of_rfc3996_prefix + len(_RFC3966_PREFIX))
                                    if (index_of_rfc3996_prefix >= 0) else 0)
        national_number += number[index_of_national_number:index_of_phone_context]
    else:
        # Extract a possible number from the string passed in (this strips leading characters that
        # could not be the start of a phone number.)
        national_number = _extract_possible_number(number)

    # Delete the isdn-subaddress and everything after it if it is
    # present. Note extension won't appear at the same time with
    # isdn-subaddress according to paragraph 5.3 of the RFC3966 spec,
    index_of_isdn = national_number.find(_RFC3966_ISDN_SUBADDRESS)
    if index_of_isdn > 0:
        national_number = national_number[:index_of_isdn]
    # If both phone context and isdn-subaddress are absent but other
    # parameters are present, the parameters are left in national_number. This
    # is because we are concerned about deleting content from a potential
    # number string when there is no strong evidence that the number is
    # actually written in RFC3966.
    return national_number


def _copy_core_fields_only(inobj):
    """Returns a new phone number containing only the fields needed to uniquely
    identify a phone number, rather than any fields that capture the context in
    which the phone number was created.
    """
    numobj = PhoneNumber()
    numobj.country_code = inobj.country_code
    numobj.national_number = inobj.national_number
    if inobj.extension is not None and len(inobj.extension) > 0:
        numobj.extension = inobj.extension
    if inobj.italian_leading_zero:
        numobj.italian_leading_zero = True
        # This field is only relevant if there are leading zeros at all.
        numobj.number_of_leading_zeros = inobj.number_of_leading_zeros
        if numobj.number_of_leading_zeros is None:
            # No number set is implicitly a count of 1; make it explicit.
            numobj.number_of_leading_zeros = 1
    return numobj


def _is_number_match_OO(numobj1_in, numobj2_in):
    """Takes two phone number objects and compares them for equality."""
    # We only care about the fields that uniquely define a number, so we copy these across explicitly.
    numobj1 = _copy_core_fields_only(numobj1_in)
    numobj2 = _copy_core_fields_only(numobj2_in)

    # Early exit if both had extensions and these are different.
    if (numobj1.extension is not None and
        numobj2.extension is not None and
        numobj1.extension != numobj2.extension):
        return MatchType.NO_MATCH

    country_code1 = numobj1.country_code
    country_code2 = numobj2.country_code
    # Both had country_code specified.
    if country_code1 != 0 and country_code2 != 0:
        if numobj1 == numobj2:
            return MatchType.EXACT_MATCH
        elif (country_code1 == country_code2 and
              _is_national_number_suffix_of_other(numobj1, numobj2)):
            # A SHORT_NSN_MATCH occurs if there is a difference because of the
            # presence or absence of an 'Italian leading zero', the presence
            # or absence of an extension, or one NSN being a shorter variant
            # of the other.
            return MatchType.SHORT_NSN_MATCH
        # This is not a match.
        return MatchType.NO_MATCH

    # Checks cases where one or both country_code fields were not
    # specified. To make equality checks easier, we first set the country_code
    # fields to be equal.
    numobj1.country_code = country_code2
    # If all else was the same, then this is an NSN_MATCH.
    if numobj1 == numobj2:
        return MatchType.NSN_MATCH
    if _is_national_number_suffix_of_other(numobj1, numobj2):
        return MatchType.SHORT_NSN_MATCH
    return MatchType.NO_MATCH


def _is_national_number_suffix_of_other(numobj1, numobj2):
    """Returns true when one national number is the suffix of the other or both
    are the same.
    """
    nn1 = str(numobj1.national_number)
    nn2 = str(numobj2.national_number)
    # Note that endswith returns True if the numbers are equal.
    return nn1.endswith(nn2) or nn2.endswith(nn1)


def _is_number_match_SS(number1, number2):
    """Takes two phone numbers as strings and compares them for equality.

    This is a convenience wrapper for _is_number_match_OO/_is_number_match_OS.
    No default region is known.
    """
    try:
        numobj1 = parse(number1, UNKNOWN_REGION)
        return _is_number_match_OS(numobj1, number2)
    except NumberParseException:
        _, exc, _ = sys.exc_info()
        if exc.error_type == NumberParseException.INVALID_COUNTRY_CODE:
            try:
                numobj2 = parse(number2, UNKNOWN_REGION)
                return _is_number_match_OS(numobj2, number1)
            except NumberParseException:
                _, exc2, _ = sys.exc_info()
                if exc2.error_type == NumberParseException.INVALID_COUNTRY_CODE:
                    try:
                        numobj1 = parse(number1, None, keep_raw_input=False,
                                        _check_region=False, numobj=None)
                        numobj2 = parse(number2, None, keep_raw_input=False,
                                        _check_region=False, numobj=None)
                        return _is_number_match_OO(numobj1, numobj2)
                    except NumberParseException:
                        return MatchType.NOT_A_NUMBER

    # One or more of the phone numbers we are trying to match is not a viable
    # phone number.
    return MatchType.NOT_A_NUMBER


def _is_number_match_OS(numobj1, number2):
    """Wrapper variant of _is_number_match_OO that copes with one
    PhoneNumber object and one string."""
    # First see if the second number has an implicit country calling code, by
    # attempting to parse it.
    try:
        numobj2 = parse(number2, UNKNOWN_REGION)
        return _is_number_match_OO(numobj1, numobj2)
    except NumberParseException:
        _, exc, _ = sys.exc_info()
        if exc.error_type == NumberParseException.INVALID_COUNTRY_CODE:
            # The second number has no country calling code. EXACT_MATCH is no
            # longer possible.  We parse it as if the region was the same as
            # that for the first number, and if EXACT_MATCH is returned, we
            # replace this with NSN_MATCH.
            region1 = region_code_for_country_code(numobj1.country_code)
            try:
                if region1 != UNKNOWN_REGION:
                    numobj2 = parse(number2, region1)
                    match = _is_number_match_OO(numobj1, numobj2)
                    if match == MatchType.EXACT_MATCH:
                        return MatchType.NSN_MATCH
                    else:
                        return match
                else:
                    # If the first number didn't have a valid country calling
                    # code, then we parse the second number without one as
                    # well.
                    numobj2 = parse(number2, None, keep_raw_input=False,
                                    _check_region=False, numobj=None)
                    return _is_number_match_OO(numobj1, numobj2)
            except NumberParseException:
                return MatchType.NOT_A_NUMBER
    # One or more of the phone numbers we are trying to match is not a viable
    # phone number.
    return MatchType.NOT_A_NUMBER


def is_number_match(num1, num2):
    """Takes two phone numbers and compares them for equality.

    For example, the numbers +1 345 657 1234 and 657 1234 are a SHORT_NSN_MATCH.
    The numbers +1 345 657 1234 and 345 657 are a NO_MATCH.

    Arguments
    num1 -- First number object or string to compare. Can contain formatting,
              and can have country calling code specified with + at the start.
    num2 -- Second number object or string to compare. Can contain formatting,
              and can have country calling code specified with + at the start.

    Returns:
     - EXACT_MATCH if the country_code, NSN, presence of a leading zero for
       Italian numbers and any extension present are the same.
     - NSN_MATCH if either or both has no region specified, and the NSNs and
       extensions are the same.
     - SHORT_NSN_MATCH if either or both has no region specified, or the
       region specified is the same, and one NSN could be a shorter version of
       the other number. This includes the case where one has an extension
       specified, and the other does not.
     - NO_MATCH otherwise.
     """
    if isinstance(num1, PhoneNumber) and isinstance(num2, PhoneNumber):
        return _is_number_match_OO(num1, num2)
    elif isinstance(num1, PhoneNumber):
        return _is_number_match_OS(num1, num2)
    elif isinstance(num2, PhoneNumber):
        return _is_number_match_OS(num2, num1)
    else:
        return _is_number_match_SS(num1, num2)


def can_be_internationally_dialled(numobj):
    """Returns True if the number can only be dialled from outside the region,
    or unknown.

    If the number can only be dialled from within the region
    as well, returns False. Does not check the number is a valid number.
    Note that, at the moment, this method does not handle short numbers (which
    are currently all presumed to not be diallable from outside their country).

    Arguments:
    numobj -- the phone number objectfor which we want to know whether it is
              diallable from outside the region.
    """
    metadata = PhoneMetadata.metadata_for_region(region_code_for_number(numobj), None)
    if metadata is None:
        # Note numbers belonging to non-geographical entities (e.g. +800
        # numbers) are always internationally diallable, and will be caught
        # here.
        return True
    nsn = national_significant_number(numobj)
    return not _is_number_matching_desc(nsn, metadata.no_international_dialling)


def is_mobile_number_portable_region(region_code):
    """Returns true if the supplied region supports mobile number portability.
    Returns false for invalid, unknown or regions that don't support mobile
    number portability.

    Arguments:
    region_code -- the region for which we want to know whether it supports mobile number
                   portability or not.
    """
    metadata = PhoneMetadata.metadata_for_region(region_code, None)
    if metadata is None:
        return False
    return metadata.mobile_number_portable_region


class NumberParseException(UnicodeMixin, Exception):
    """Exception when attempting to parse a putative phone number"""

    # The reason a string could not be interpreted as a phone number.

    # The country code supplied did not belong to a supported country or
    # non-geographical entity.
    INVALID_COUNTRY_CODE = 0

    # This generally indicates the string passed in had fewer than 3 digits in
    # it.  The number failed to match the regular expression
    # _VALID_PHONE_NUMBER in phonenumberutil.py.
    NOT_A_NUMBER = 1

    # This indicates the string started with an international dialing prefix,
    # but after this was removed, it had fewer digits than any valid phone
    # number (including country code) could have.
    TOO_SHORT_AFTER_IDD = 2

    # This indicates the string, after any country code has been stripped,
    # had fewer digits than any valid phone number could have.
    TOO_SHORT_NSN = 3

    # This indicates the string had more digits than any valid phone number
    # could have
    TOO_LONG = 4

    def __init__(self, error_type, msg):
        Exception.__init__(self, msg)
        self.error_type = error_type
        self._msg = msg

    def __unicode__(self):
        return unicod("(%s) %s") % (self.error_type, self._msg)


def _match_national_number(number, number_desc, allow_prefix_match):
    """Returns whether the given national number (a string containing only decimal digits) matches
    the national number pattern defined in the given PhoneNumberDesc object.
    """
    # We don't want to consider it a prefix match when matching non-empty input against an empty
    # pattern.
    if number_desc is None or number_desc.national_number_pattern is None or len(number_desc.national_number_pattern) == 0:
        return False
    return _match(number, re.compile(number_desc.national_number_pattern), allow_prefix_match)


def _match(number, pattern, allow_prefix_match):
    if not pattern.match(number):
        return False
    else:
        if fullmatch(pattern, number):
            return True
        else:
            return allow_prefix_match
