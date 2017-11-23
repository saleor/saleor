from django.utils.translation import gettext
from django.conf import settings

PATTERN = '%s: %s'


def handle_default(field, chips_list):
    chips = chips_list[:]
    chips.append({'content': PATTERN % (field.label, field.value()),
                  'name': field.name, 'value': field.value()})
    return chips


def handle_multiplechoice(field, chips_list, context):
    chips = chips_list[:]
    for partial_value in [f for f in field.value() if f]:
        value = context[partial_value]
        chips.append({'content': PATTERN % (field.label, value),
                      'name': field.name, 'value': partial_value})
    return chips


def handle_nullboolean(field, chips_list):
    chips = chips_list[:]
    values = [
        gettext('No'),
        gettext('Yes')
    ]
    value = values[1] if field.value() else values[0]
    chips.append({'content': PATTERN % (field.label, value),
                  'name': field.name, 'value': 1 if field.value() else 0})
    return chips


def handle_range(field, chips_list):
    chips = chips_list[:]
    values = [f if f else None for f in field.value()]
    text = [gettext('From'), gettext('To')]
    for i, value in enumerate(values):
        if value:
            chips.append(
                {'content': PATTERN % (field.label, text[i] + ' ' + value),
                 'name': '%s_%i' % (field.name, i),
                 'value': field.value()[i]})
    return chips


def handle_choice(field, chips_list):
    chips = chips_list[:]
    value = list(filter(lambda x: x[0] == field.value(),
                        field.field._choices))[0][1]
    chips.append({'content': PATTERN % (field.label, value),
                  'name': field.name, 'value': field.value()})
    return chips
