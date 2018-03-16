from django.template import Library

register = Library()


@register.simple_tag
def get_formset_form(formset, index):
    return formset.forms[index]
