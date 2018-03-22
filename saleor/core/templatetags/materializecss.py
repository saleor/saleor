from django import forms, template
from django.template.loader import get_template
from django_filters.widgets import RangeWidget

from ...dashboard.widgets import (
    CharsLeftWidget, DateRangeWidget, MoneyRangeWidget)

register = template.Library()


@register.filter
def materializecss(element, label_cols=None):
    if not label_cols:
        label_cols = 's12'

    markup_classes = {'label': label_cols, 'value': '', 'single_value': ''}
    return render(element, markup_classes)


def add_input_classes(field):
    if not any([is_checkbox(field), is_checkbox_select_multiple(field),
                is_radio(field), is_file(field)]):
        field_classes = field.field.widget.attrs.get('class', '')
        if field.errors:
            field_classes = ' '.join([field_classes, 'invalid'])
        field.field.widget.attrs['class'] = field_classes


def render(element, markup_classes):
    element_type = element.__class__.__name__.lower()

    if element_type == 'boundfield':
        add_input_classes(element)
        template = get_template("materializecssform/field.html")
        context = {'field': element, 'classes': markup_classes}
    else:
        has_management = getattr(element, 'management_form', None)
        if has_management:
            for form in element.forms:
                for field in form.visible_fields():
                    add_input_classes(field)

            template = get_template("materializecssform/formset.html")
            context = {'formset': element, 'classes': markup_classes}
        else:
            for field in element.visible_fields():
                add_input_classes(field)

            template = get_template("materializecssform/form.html")
            context = {'form': element, 'classes': markup_classes}

    return template.render(context)


@register.filter
def is_checkbox(field):
    return isinstance(field.field.widget, forms.CheckboxInput)


@register.filter
def is_textarea(field):
    return isinstance(field.field.widget, forms.Textarea)


@register.filter
def is_radio(field):
    return isinstance(field.field.widget, forms.RadioSelect)


@register.filter
def is_date_input(field):
    return isinstance(field.field.widget, forms.DateInput)


@register.filter
def is_file(field):
    return isinstance(field.field.widget, forms.FileInput)


@register.filter
def is_select(field):
    return isinstance(field.field.widget, forms.Select)


@register.filter
def is_checkbox_select_multiple(field):
    return isinstance(field.field.widget, forms.CheckboxSelectMultiple)


@register.filter
def is_range(field):
    return isinstance(field.field.widget, RangeWidget)


@register.filter
def is_date_range(field):
    return isinstance(field.field.widget, DateRangeWidget)


@register.filter
def is_price_range(field):
    return isinstance(field.field.widget, MoneyRangeWidget)


@register.filter
def is_chars_left(field):
    return isinstance(field.field.widget, CharsLeftWidget)
