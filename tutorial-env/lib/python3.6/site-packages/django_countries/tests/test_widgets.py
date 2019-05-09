from __future__ import unicode_literals
from unittest import skipIf

try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse  # Python 2

from distutils.version import StrictVersion
import django
from django.forms.models import modelform_factory
from django.test import TestCase
from django.utils import safestring
from django.utils.html import escape

from django_countries import widgets, countries, fields
from django_countries.conf import settings
from django_countries.tests.models import Person


class TestCountrySelectWidget(TestCase):
    def setUp(self):
        del countries.countries
        self.Form = modelform_factory(
            Person, fields=["country"], widgets={"country": widgets.CountrySelectWidget}
        )

    def tearDown(self):
        del countries.countries

    def test_not_default_widget(self):
        Form = modelform_factory(Person, fields=["country"])
        widget = Form().fields["country"].widget
        self.assertFalse(isinstance(widget, widgets.CountrySelectWidget))

    def test_render_contains_flag_url(self):
        with self.settings(COUNTRIES_ONLY={"AU": "Desert"}):
            html = self.Form().as_p()
            self.assertIn(
                escape(
                    urlparse.urljoin(settings.STATIC_URL, settings.COUNTRIES_FLAG_URL)
                ),
                html,
            )

    def test_render(self):
        with self.settings(COUNTRIES_ONLY={"AU": "Desert"}):
            html = self.Form().as_p()
            self.assertIn(fields.Country("__").flag, html)
            self.assertNotIn(fields.Country("AU").flag, html)

    def test_render_initial(self):
        with self.settings(COUNTRIES_ONLY={"AU": "Desert"}):
            html = self.Form(initial={"country": "AU"}).as_p()
            self.assertIn(fields.Country("AU").flag, html)
            self.assertNotIn(fields.Country("__").flag, html)

    def test_render_escaping(self):
        output = widgets.CountrySelectWidget().render("test", "<script>")
        self.assertIn("&lt;script&gt;", output)
        self.assertNotIn("<script>", output)
        self.assertTrue(isinstance(output, safestring.SafeData))

    def test_render_modelform_instance(self):
        person = Person(country="NZ")
        self.Form(instance=person).as_p()

    @skipIf(
        StrictVersion(django.get_version()) < StrictVersion("1.10"),
        "required attribute only implemented in 1.10+",
    )
    def test_required_attribute(self):
        rendered = self.Form()["country"].as_widget()
        rendered = rendered[: rendered.find(">") + 1]
        self.assertIn("required", rendered)
