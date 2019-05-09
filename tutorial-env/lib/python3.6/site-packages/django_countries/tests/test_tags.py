from django.template import Template, Context
from django.test import TestCase
from django.utils import translation

from django_countries import countries


class TestCountriesTags(TestCase):

    TEMPLATE_COUNTRY = Template(
        "{% load countries %}{% get_country code as country %}{{ country }}"
    )
    TEMPLATE_NAME = Template(
        "{% load countries %}{% get_country code as country %}{{ country.name }}"
    )
    TEMPLATE_COUNTRIES = Template(
        "{% load countries %}{% get_countries as countries_list %}{{ countries_list }}"
    )

    def test_country(self):
        rendered = self.TEMPLATE_COUNTRY.render(Context({"code": "BR"}))
        self.assertEqual(rendered, "BR")

    def test_country_name(self):
        rendered = self.TEMPLATE_NAME.render(Context({"code": "BR"}))
        self.assertEqual(rendered, "Brazil")

    def test_country_name_translated(self):
        with translation.override("pt-BR"):
            rendered = self.TEMPLATE_NAME.render(Context({"code": "BR"}))
        self.assertEqual(rendered, "Brasil")

    def test_wrong_code(self):
        rendered = self.TEMPLATE_COUNTRY.render(Context({"code": "XX"}))
        self.assertEqual(rendered, "XX")

        rendered = self.TEMPLATE_NAME.render(Context({"code": "XX"}))
        self.assertEqual(rendered, "")

    def test_countries_displayed_all(self):
        rendered = self.TEMPLATE_COUNTRIES.render(Context())
        self.assertEqual(
            rendered,
            Template("{{ expected }}").render(
                Context({"expected": [(code, name) for code, name in countries]})
            ),
        )
