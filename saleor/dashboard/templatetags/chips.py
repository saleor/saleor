from __future__ import unicode_literals

from django.template.defaultfilters import yesno
from django.utils.translation import pgettext_lazy

CHIPS_PATTERN = '%s: %s'


def handle_default(field):
    item = {
        'content': CHIPS_PATTERN % (field.label, field.value()),
        'name': field.name, 'value': field.value()}
    return [item]


def handle_single_choice(field, value):
    for choice_value, choice_label in field.field.choices:
        if choice_value == value:
            item = {
                'content': CHIPS_PATTERN % (field.label, choice_label),
                'name': field.name, 'value': value}
            return [item]
    return []


def handle_multiple_choice(field, values):
    items = []
    for value in values:
        items.extend(handle_single_choice(field, value))
    return items


def handle_single_model_choice(field, obj):
    return [{
        'content': CHIPS_PATTERN % (field.label, str(obj)),
        'name': field.name, 'value': obj.pk}]


def handle_multiple_model_choice(field, queryset):
    chips = []
    for obj in queryset:
        chips.extend(handle_single_model_choice(field, obj))
    return chips


def handle_nullboolean(field):
    value = yesno(
        field.value(),
        pgettext_lazy('Possible values of boolean filter', 'yes,no,all'))
    item = {
        'content': CHIPS_PATTERN % (field.label, value),
        'name': field.name, 'value': field.value()}
    return [item]


def handle_range(field):
    chips = []
    values = [f if f else None for f in field.value()]
    text = [
        pgettext_lazy('Label of first value in range filter', 'From'),
        pgettext_lazy('Label of second value in range filter', 'To')]
    for i, value in enumerate(values):
        if value:
            chips.append(
                {'content': CHIPS_PATTERN % (
                    field.label, text[i] + ' ' + value),
                 'name': '%s_%i' % (field.name, i),
                 'value': field.value()[i]})
    return chips
