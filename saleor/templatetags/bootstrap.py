from django import forms
from django.forms.forms import BoundField, BaseForm
from django.forms.util import ErrorList
from django.template import Library, Context, TemplateSyntaxError, loader
from django.utils.safestring import mark_safe


register = Library()
field_template = loader.get_template('bootstrap/_field.html')
errors_template = loader.get_template('bootstrap/_non_field_errors.html')


def render_non_field_errors(errors):
    if errors:
        context = Context({'errors': errors})
        return errors_template.render(context)

    return ''


def render_field(bound_field, show_label):
    widget = bound_field.field.widget

    if isinstance(widget, forms.RadioSelect):
        input_type = 'radio'
    elif isinstance(widget, forms.Select):
        input_type = 'select'
    elif isinstance(widget, forms.Textarea):
        input_type = 'textarea'
    elif isinstance(widget, forms.CheckboxInput):
        input_type = 'checkbox'
    else:
        input_type = 'input'

    context = Context({'bound_field': bound_field,
                       'input_type': input_type,
                       'show_label': show_label})

    return field_template.render(context)


@register.filter
def as_bootstrap(obj, show_label=True):
    if isinstance(obj, BoundField):
        return render_field(obj, show_label)
    elif isinstance(obj, ErrorList):
        return render_non_field_errors(obj)
    elif isinstance(obj, BaseForm):
        non_field_errors = render_non_field_errors(obj.non_field_errors())
        form = ''.join([render_field(field, show_label) for field in obj])
        return mark_safe(non_field_errors + form)
    else:
        raise TemplateSyntaxError('Filter accepts form, field and non fields '
                                  'errors.')
