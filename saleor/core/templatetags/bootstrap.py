from django import forms
from django.forms.forms import BoundField, BaseForm
from django.forms.util import ErrorList
from django.template import Library, Context, TemplateSyntaxError
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe

register = Library()

TEMPLATE_ERRORS = 'bootstrap/_non_field_errors.html'
TEMPLATE_HORIZONTAL = 'bootstrap/_field_horizontal.html'
TEMPLATE_VERTICAL = 'bootstrap/_field_vertical.html'


def render_non_field_errors(errors):
    if not errors:
        return ''
    context = Context({'errors': errors})
    return render_to_string(TEMPLATE_ERRORS, context_instance=context)


def render_field(bound_field, show_label, template):
    widget = bound_field.field.widget

    if isinstance(widget, forms.RadioSelect):
        input_type = 'radio'
    elif isinstance(widget, forms.Select):
        input_type = 'select'
    elif isinstance(widget, forms.Textarea):
        input_type = 'textarea'
    elif isinstance(widget, forms.CheckboxInput):
        input_type = 'checkbox'
    elif issubclass(type(widget), forms.MultiWidget):
        input_type = 'multi_widget'
    else:
        input_type = 'input'

    context = Context({'bound_field': bound_field,
                       'input_type': input_type,
                       'show_label': show_label})
    return render_to_string(template, context_instance=context)


def as_bootstrap(obj, show_label, template):
    if isinstance(obj, BoundField):
        return render_field(obj, show_label, template)
    elif isinstance(obj, ErrorList):
        return render_non_field_errors(obj)
    elif isinstance(obj, BaseForm):
        non_field_errors = render_non_field_errors(obj.non_field_errors())
        fields = (render_field(field, show_label, template) for field in obj)
        form = ''.join(fields)
        return mark_safe(non_field_errors + form)
    else:
        raise TemplateSyntaxError('Filter accepts form, field and non fields '
                                  'errors.')


@register.filter
def as_horizontal_form(obj, show_label=True):
    return as_bootstrap(obj=obj, show_label=show_label,
                        template=TEMPLATE_HORIZONTAL)


@register.filter
def as_vertical_form(obj, show_label=True):
    return as_bootstrap(obj=obj, show_label=show_label,
                        template=TEMPLATE_VERTICAL)


@register.simple_tag
def render_widget(obj, **attrs):
    return obj.as_widget(attrs=attrs)
