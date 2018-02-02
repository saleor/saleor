from urllib.parse import urlencode

from django.template.defaultfilters import yesno
from django.utils.translation import pgettext_lazy

CHIPS_PATTERN = '%s: %s'


def handle_default(field, request_get):
    """Build a list of chips using raw field's value."""
    return [{
        'content': CHIPS_PATTERN % (field.label, field.value()),
        'link': get_cancel_url(request_get, field.name)}]


def handle_single_choice(field, request_get):
    """Build a list of chips for ChoiceField field."""
    for choice_value, choice_label in field.field.choices:
        if choice_value == field.value():
            item = {
                'content': CHIPS_PATTERN % (field.label, choice_label),
                'link': get_cancel_url(request_get, field.name)}
            return [item]
    return []


def handle_multiple_choice(field, request_get):
    """Build a list of chips for MultipleChoiceField field."""
    items = []
    for value in field.value():
        for choice_value, choice_label in field.field.choices:
            if choice_value == value:
                items.append({
                    'content': CHIPS_PATTERN % (field.label, choice_label),
                    'link': get_cancel_url(request_get, field.name, value)})
    return items


def handle_single_model_choice(field, request_get):
    """Build a list of chips for ModelChoiceField field."""
    for obj in field.field.queryset:
        if str(obj.pk) == str(field.value()):
            return [{
                'content': CHIPS_PATTERN % (field.label, str(obj)),
                'link': get_cancel_url(request_get, field.name)}]
    return []


def handle_multiple_model_choice(field, request_get):
    """Build a list of chips for ModelMultipleChoiceField field."""
    items = []
    for pk in field.value():
        # iterate over field's queryset to match the selected object
        for obj in field.field.queryset:
            if str(obj.pk) == str(pk):
                items.append({
                    'content': CHIPS_PATTERN % (field.label, str(obj)),
                    'link': get_cancel_url(request_get, field.name, pk)})
    return items


def handle_nullboolean(field, request_get):
    """Build a list of chips for NullBooleanField field."""
    value = yesno(
        field.value(),
        pgettext_lazy('Possible values of boolean filter', 'yes,no,all'))
    return [{
        'content': CHIPS_PATTERN % (field.label, value),
        'link': get_cancel_url(request_get, field.name)}]


def handle_range(field, request_get):
    """Build a list of chips for RangeField field."""
    items = []
    values = [f if f else None for f in field.value()]
    text = [
        pgettext_lazy('Label of first value in range filter', 'From'),
        pgettext_lazy('Label of second value in range filter', 'To')]
    for i, value in enumerate(values):
        if value:
            param_name = '%s_%i' % (field.name, i)
            items.append({
                'content': CHIPS_PATTERN % (
                    field.label, text[i] + ' ' + str(value)),
                'link': get_cancel_url(request_get, param_name)})
    return items


def get_cancel_url(request_get, param_name, param_value=None):
    """Build a new URL from a query dict excluding given parameter.

    `request_get` - dictionary of query parameters
    `param_name` - name of a parameter to exclude
    `param_value` - value of a parameter value to exclude (in case a parameter
    has multiple values)
    """
    new_request_get = {
        k: request_get.getlist(k) for k in request_get if k != param_name}
    param_values_list = request_get.getlist(param_name)
    if len(param_values_list) > 1 and param_value is not None:
        new_param_values = [v for v in param_values_list if v != param_value]
        new_request_get[param_name] = new_param_values
    cancel_url = '?' + urlencode(new_request_get, True)
    return cancel_url
