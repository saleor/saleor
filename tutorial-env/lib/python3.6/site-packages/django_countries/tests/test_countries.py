# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.test import TestCase
from django.utils import translation

from django_countries import countries, Countries, CountryTuple
from django_countries.tests import custom_countries


EXPECTED_COUNTRY_COUNT = 249
FIRST_THREE_COUNTRIES = [
    ("AF", "Afghanistan"),
    ("AX", "Åland Islands"),
    ("AL", "Albania"),
]


class BaseTest(TestCase):
    def setUp(self):
        del countries.countries

    def tearDown(self):
        del countries.countries


class TestCountriesObject(BaseTest):
    def test_countries_len(self):
        self.assertEqual(len(countries), EXPECTED_COUNTRY_COUNT)

    def test_countries_sorted(self):
        self.assertEqual(list(countries)[:3], FIRST_THREE_COUNTRIES)

    def test_countries_namedtuple(self):
        country = list(countries)[0]
        first_country = FIRST_THREE_COUNTRIES[0]
        self.assertEqual(country.code, first_country[0])
        self.assertEqual(country.name, first_country[1])
        self.assertIsInstance(country, CountryTuple)

    def test_countries_limit(self):
        with self.settings(COUNTRIES_ONLY={"NZ": "New Zealand", "NV": "Neverland"}):
            self.assertEqual(
                list(countries), [("NV", "Neverland"), ("NZ", "New Zealand")]
            )
            self.assertEqual(len(countries), 2)

    def test_countries_limit_codes(self):
        with self.settings(COUNTRIES_ONLY=["NZ", ("NV", "Neverland")]):
            self.assertEqual(
                list(countries), [("NV", "Neverland"), ("NZ", "New Zealand")]
            )
            self.assertEqual(len(countries), 2)

    def test_countries_custom_removed_len(self):
        with self.settings(COUNTRIES_OVERRIDE={"AU": None}):
            self.assertEqual(len(countries), EXPECTED_COUNTRY_COUNT - 1)

    def test_countries_custom_added_len(self):
        with self.settings(COUNTRIES_OVERRIDE={"XX": "Neverland"}):
            self.assertEqual(len(countries), EXPECTED_COUNTRY_COUNT + 1)

    def test_countries_getitem(self):
        countries[0]

    def test_countries_slice(self):
        sliced = countries[10:20:2]
        self.assertEqual(len(sliced), 5)

    def test_countries_custom_ugettext_evaluation(self):
        class FakeLazyUGetText(object):
            def __bool__(self):  # pragma: no cover
                raise ValueError("Can't evaluate lazy_ugettext yet")

            __nonzero__ = __bool__

        with self.settings(COUNTRIES_OVERRIDE={"AU": FakeLazyUGetText()}):
            countries.countries

    def test_ioc_countries(self):
        from ..ioc_data import check_ioc_countries

        check_ioc_countries(verbosity=0)

    def test_initial_iter(self):
        # Use a new instance so nothing is cached
        dict(Countries())

    def test_flags(self):
        from ..data import check_flags

        check_flags(verbosity=0)

    def test_common_names(self):
        from ..data import check_common_names

        check_common_names()

    def test_alpha2(self):
        self.assertEqual(countries.alpha2("NZ"), "NZ")
        self.assertEqual(countries.alpha2("nZ"), "NZ")
        self.assertEqual(countries.alpha2("Nzl"), "NZ")
        self.assertEqual(countries.alpha2(554), "NZ")
        self.assertEqual(countries.alpha2("554"), "NZ")

    def test_alpha2_invalid(self):
        self.assertEqual(countries.alpha2("XX"), "")

    def test_alpha2_override(self):
        with self.settings(COUNTRIES_OVERRIDE={"AU": None}):
            self.assertEqual(countries.alpha2("AU"), "")

    def test_alpha2_override_new(self):
        with self.settings(COUNTRIES_OVERRIDE={"XX": "Neverland"}):
            self.assertEqual(countries.alpha2("XX"), "XX")

    def test_fetch_by_name(self):
        code = countries.by_name("United States of America")
        self.assertEqual(code, "US")

    def test_fetch_by_name_case_insensitive(self):
        code = countries.by_name("United states of America")
        self.assertEqual(code, "US")

    def test_fetch_by_name_old(self):
        code = countries.by_name("Czech Republic")
        self.assertEqual(code, "CZ")

    def test_fetch_by_name_old_case_insensitive(self):
        code = countries.by_name("Czech republic")
        self.assertEqual(code, "CZ")

    def test_fetch_by_name_i18n(self):
        code = countries.by_name("Estados Unidos", language="es")
        self.assertEqual(code, "US")

    def test_fetch_by_name_no_match(self):
        self.assertEqual(countries.by_name("Neverland"), "")


class CountriesFirstTest(BaseTest):
    def test_countries_first(self):
        with self.settings(COUNTRIES_FIRST=["NZ", "AU"]):
            self.assertEqual(
                list(countries)[:5],
                [("NZ", "New Zealand"), ("AU", "Australia")] + FIRST_THREE_COUNTRIES,
            )

    def test_countries_first_break(self):
        with self.settings(
            COUNTRIES_FIRST=["NZ", "AU"], COUNTRIES_FIRST_BREAK="------"
        ):
            self.assertEqual(
                list(countries)[:6],
                [("NZ", "New Zealand"), ("AU", "Australia"), ("", "------")]
                + FIRST_THREE_COUNTRIES,
            )

    def test_countries_first_some_valid(self):
        with self.settings(
            COUNTRIES_FIRST=["XX", "NZ", "AU"], COUNTRIES_FIRST_BREAK="------"
        ):
            countries_list = list(countries)
        self.assertEqual(
            countries_list[:6],
            [("NZ", "New Zealand"), ("AU", "Australia"), ("", "------")]
            + FIRST_THREE_COUNTRIES,
        )
        self.assertEqual(len(countries_list), EXPECTED_COUNTRY_COUNT + 1)

    def test_countries_first_no_valid(self):
        with self.settings(COUNTRIES_FIRST=["XX"], COUNTRIES_FIRST_BREAK="------"):
            countries_list = list(countries)
        self.assertEqual(countries_list[:3], FIRST_THREE_COUNTRIES)
        self.assertEqual(len(countries_list), EXPECTED_COUNTRY_COUNT)

    def test_countries_first_repeat(self):
        with self.settings(COUNTRIES_FIRST=["NZ", "AU"], COUNTRIES_FIRST_REPEAT=True):
            countries_list = list(countries)
        self.assertEqual(len(countries_list), EXPECTED_COUNTRY_COUNT + 2)
        sorted_codes = [item[0] for item in countries_list[2:]]
        sorted_codes.index("NZ")
        sorted_codes.index("AU")

    def test_countries_first_len(self):
        with self.settings(COUNTRIES_FIRST=["NZ", "AU", "XX"]):
            self.assertEqual(len(countries), EXPECTED_COUNTRY_COUNT + 2)

    def test_countries_first_break_len(self):
        with self.settings(
            COUNTRIES_FIRST=["NZ", "AU", "XX"], COUNTRIES_FIRST_BREAK="------"
        ):
            self.assertEqual(len(countries), EXPECTED_COUNTRY_COUNT + 3)

    def test_countries_first_break_len_no_valid(self):
        with self.settings(COUNTRIES_FIRST=["XX"], COUNTRIES_FIRST_BREAK="------"):
            self.assertEqual(len(countries), EXPECTED_COUNTRY_COUNT)

    def test_sorted_countries_first_english(self):
        with self.settings(
            COUNTRIES_FIRST=["GB", "AF", "DK"], COUNTRIES_FIRST_SORT=True
        ):
            countries_list = list(countries)
            sorted_codes = [item[0] for item in countries_list[:3]]
            self.assertEqual(["AF", "DK", "GB"], sorted_codes)

    def test_unsorted_countries_first_english(self):
        with self.settings(
            COUNTRIES_FIRST=["GB", "AF", "DK"], COUNTRIES_FIRST_SORT=False
        ):
            countries_list = list(countries)
            unsorted_codes = [item[0] for item in countries_list[:3]]
            self.assertEqual(["GB", "AF", "DK"], unsorted_codes)

    def test_sorted_countries_first_arabic(self):
        with self.settings(
            COUNTRIES_FIRST=["GB", "AF", "DK"], COUNTRIES_FIRST_SORT=True
        ):
            lang = translation.get_language()
            translation.activate("eo")
            try:
                countries_list = list(countries)
                sorted_codes = [item[0] for item in countries_list[:3]]
                self.assertEqual(["AF", "GB", "DK"], sorted_codes)
            finally:
                translation.activate(lang)


class TestCountriesCustom(BaseTest):
    def test_countries_limit(self):
        fantasy_countries = custom_countries.FantasyCountries()
        self.assertEqual(
            list(fantasy_countries), [("NV", "Neverland"), ("NZ", "New Zealand")]
        )
        self.assertEqual(len(fantasy_countries), 2)
