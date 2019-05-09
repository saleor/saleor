from __future__ import unicode_literals
from django.test import TestCase
from django.utils import six

from django_countries import countries, data, base


class TestSettings(TestCase):
    def setUp(self):
        del countries.countries

    def tearDown(self):
        del countries.countries

    def test_override_additional(self):
        with self.settings(COUNTRIES_OVERRIDE={"XX": "New"}):
            self.assertEqual(countries.name("XX"), "New")

    def test_override_replace(self):
        with self.settings(COUNTRIES_OVERRIDE={"NZ": "Middle Earth"}):
            self.assertEqual(countries.name("NZ"), "Middle Earth")

    def test_override_remove(self):
        with self.settings(COUNTRIES_OVERRIDE={"AU": None}):
            self.assertNotIn("AU", countries)
            self.assertEqual(countries.name("AU"), "")

    def test_override_only(self):
        with self.settings(COUNTRIES_ONLY={"AU": "Desert"}):
            self.assertTrue(len(countries.countries) == 1)
            self.assertIn("AU", countries)
            self.assertEqual(countries.name("AU"), "Desert")

    def test_common_names(self):
        common_code, common_name = list(base.CountriesBase.COMMON_NAMES.items())[0]
        common_name = six.text_type(common_name)
        name = six.text_type(countries.countries[common_code])
        self.assertEqual(name, common_name)

        del countries.countries
        official_name = six.text_type(data.COUNTRIES[common_code])
        with self.settings(COUNTRIES_COMMON_NAMES=False):
            name = six.text_type(countries.countries[common_code])
            self.assertEqual(name, official_name)
