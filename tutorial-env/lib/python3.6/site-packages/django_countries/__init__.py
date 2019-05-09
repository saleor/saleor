#!/usr/bin/env python
from __future__ import unicode_literals
from itertools import islice
from collections import namedtuple

from django_countries.conf import settings
from django.utils import six
from django.utils.encoding import force_text
from django.utils.translation import override

from .base import CountriesBase

try:
    import pyuca
except ImportError:
    pyuca = None

# Use UCA sorting if it's available.
if pyuca:
    collator = pyuca.Collator()

    def sort_key(item):
        return collator.sort_key(item[1])


else:
    import unicodedata

    # Cheap and dirty method to sort against ASCII characters only.

    def sort_key(item):
        return (
            unicodedata.normalize("NFKD", item[1])
            .encode("ascii", "ignore")
            .decode("ascii")
        )


class CountryTuple(namedtuple("CountryTupleBase", ["code", "name"])):
    def __repr__(self):
        """
        Display the repr as a standard tuple for better backwards
        compatibility with outputting this in a template.
        """
        return "({this.code!r}, {this.name!r})".format(this=self)


class Countries(CountriesBase):
    """
    An object containing a list of ISO3166-1 countries.

    Iterating this object will return the countries as namedtuples (of
    the country ``code`` and ``name``), sorted by name.
    """

    def get_option(self, option):
        """
        Get a configuration option, trying the options attribute first and
        falling back to a Django project setting.
        """
        value = getattr(self, option, None)
        if value is not None:
            return value
        return getattr(settings, "COUNTRIES_{0}".format(option.upper()))

    @property
    def countries(self):
        """
        Return the a dictionary of countries, modified by any overriding
        options.

        The result is cached so future lookups are less work intensive.
        """
        if not hasattr(self, "_countries"):
            only = self.get_option("only")
            if only:
                only_choices = True
                if not isinstance(only, dict):
                    for item in only:
                        if isinstance(item, six.string_types):
                            only_choices = False
                            break
            if only and only_choices:
                self._countries = dict(only)
            else:
                # Local import so that countries aren't loaded into memory
                # until first used.
                from django_countries.data import COUNTRIES

                self._countries = dict(COUNTRIES)
                if self.get_option("common_names"):
                    self._countries.update(self.COMMON_NAMES)
                override = self.get_option("override")
                if override:
                    self._countries.update(override)
                    self._countries = dict(
                        (code, name)
                        for code, name in self._countries.items()
                        if name is not None
                    )
            if only and not only_choices:
                countries = {}
                for item in only:
                    if isinstance(item, six.string_types):
                        countries[item] = self._countries[item]
                    else:
                        key, value = item
                        countries[key] = value
                self._countries = countries
            self.countries_first = []
            first = self.get_option("first") or []
            for code in first:
                code = self.alpha2(code)
                if code in self._countries:
                    self.countries_first.append(code)
        return self._countries

    @property
    def alt_codes(self):
        if not hasattr(self, "_alt_codes"):
            # Again, local import so data is not loaded unless it's needed.
            from django_countries.data import ALT_CODES

            self._alt_codes = ALT_CODES
        return self._alt_codes

    @countries.deleter
    def countries(self):
        """
        Reset the countries cache in case for some crazy reason the settings or
        internal options change. But surely no one is crazy enough to do that,
        right?
        """
        if hasattr(self, "_countries"):
            del self._countries

    def translate_pair(self, code):
        """
        Force a country to the current activated translation.

        :returns: ``CountryTuple(code, translated_country_name)`` namedtuple
        """
        name = self.countries[code]
        if code in self.OLD_NAMES:
            # Check if there's an older translation available if there's no
            # translation for the newest name.
            with override(None):
                source_name = force_text(name)
            name = force_text(name)
            if name == source_name:
                for old_name in self.OLD_NAMES[code]:
                    with override(None):
                        source_old_name = force_text(old_name)
                    old_name = force_text(old_name)
                    if old_name != source_old_name:
                        name = old_name
                        break
        else:
            name = force_text(name)
        return CountryTuple(code, name)

    def __iter__(self):
        """
        Iterate through countries, sorted by name.

        Each country record consists of a namedtuple of the two letter
        ISO3166-1 country ``code`` and short ``name``.

        The sorting happens based on the thread's current translation.

        Countries that are in ``settings.COUNTRIES_FIRST`` will be
        displayed before any sorted countries (in the order provided),
        and are only repeated in the sorted list if
        ``settings.COUNTRIES_FIRST_REPEAT`` is ``True``.

        The first countries can be separated from the sorted list by the
        value provided in ``settings.COUNTRIES_FIRST_BREAK``.
        """
        # Initializes countries_first, so needs to happen first.
        countries = self.countries

        # Yield countries that should be displayed first.
        countries_first = (self.translate_pair(code) for code in self.countries_first)

        if self.get_option("first_sort"):
            countries_first = sorted(countries_first, key=sort_key)

        for item in countries_first:
            yield item

        if self.countries_first:
            first_break = self.get_option("first_break")
            if first_break:
                yield ("", force_text(first_break))

        # Force translation before sorting.
        first_repeat = self.get_option("first_repeat")
        countries = (
            self.translate_pair(code)
            for code in countries
            if first_repeat or code not in self.countries_first
        )

        # Return sorted country list.
        for item in sorted(countries, key=sort_key):
            yield item

    def alpha2(self, code):
        """
        Return the two letter country code when passed any type of ISO 3166-1
        country code.

        If no match is found, returns an empty string.
        """
        code = force_text(code).upper()
        if code.isdigit():
            lookup_code = int(code)

            def find(alt_codes):
                return alt_codes[1] == lookup_code

        elif len(code) == 3:
            lookup_code = code

            def find(alt_codes):
                return alt_codes[0] == lookup_code

        else:
            find = None
        if find:
            code = None
            for alpha2, alt_codes in self.alt_codes.items():
                if find(alt_codes):
                    code = alpha2
                    break
        if code in self.countries:
            return code
        return ""

    def name(self, code):
        """
        Return the name of a country, based on the code.

        If no match is found, returns an empty string.
        """
        code = self.alpha2(code)
        if code not in self.countries:
            return ""
        return self.translate_pair(code)[1]

    def by_name(self, country, language="en"):
        """
        Fetch a country's ISO3166-1 two letter country code from its name.

        An optional language parameter is also available.
        Warning: This depends on the quality of the available translations.

        If no match is found, returns an empty string.

        ..warning:: Be cautious about relying on this returning a country code
            (especially with any hard-coded string) since the ISO names of
            countries may change over time.
        """
        with override(language):
            for code, name in self:
                if name.lower() == country.lower():
                    return code
                if code in self.OLD_NAMES:
                    for old_name in self.OLD_NAMES[code]:
                        if old_name.lower() == country.lower():
                            return code
        return ""

    def alpha3(self, code):
        """
        Return the ISO 3166-1 three letter country code matching the provided
        country code.

        If no match is found, returns an empty string.
        """
        code = self.alpha2(code)
        try:
            return self.alt_codes[code][0]
        except KeyError:
            return ""

    def numeric(self, code, padded=False):
        """
        Return the ISO 3166-1 numeric country code matching the provided
        country code.

        If no match is found, returns ``None``.

        :param padded: Pass ``True`` to return a 0-padded three character
            string, otherwise an integer will be returned.
        """
        code = self.alpha2(code)
        try:
            num = self.alt_codes[code][1]
        except KeyError:
            return None
        if padded:
            return "%03d" % num
        return num

    def __len__(self):
        """
        len() used by several third party applications to calculate the length
        of choices. This will solve a bug related to generating fixtures.
        """
        count = len(self.countries)
        # Add first countries, and the break if necessary.
        count += len(self.countries_first)
        if self.countries_first and self.get_option("first_break"):
            count += 1
        return count

    def __bool__(self):
        return bool(self.countries)

    __nonzero__ = __bool__

    def __contains__(self, code):
        """
        Check to see if the countries contains the given code.
        """
        return code in self.countries

    def __getitem__(self, index):
        """
        Some applications expect to be able to access members of the field
        choices by index.
        """
        try:
            return next(islice(self.__iter__(), index, index + 1))
        except TypeError:
            return list(islice(self.__iter__(), index.start, index.stop, index.step))


countries = Countries()
