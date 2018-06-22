from django.template import Library

from ...core.utils import get_country_name_by_code

register = Library()


@register.simple_tag
def get_formset_form(formset, index):
    return formset.forms[index]


@register.simple_tag
def get_country_by_code(country_code):
    return get_country_name_by_code(country_code)
