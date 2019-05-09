import django
from django import template
from django_countries.fields import Country, countries


register = template.Library()

if django.VERSION < (1, 9):
    # Support older versions without implicit assignment support in simple_tag.
    simple_tag = register.assignment_tag
else:
    simple_tag = register.simple_tag


@simple_tag
def get_country(code):
    return Country(code=code)


@simple_tag
def get_countries():
    return list(countries)
