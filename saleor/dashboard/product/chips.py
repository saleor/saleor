from django.utils.translation import gettext
from django.conf import settings

PATTERN = '%s: %s'


def find_type_in_list(needle, haystack):
    matches = list(filter(lambda x: x in str(needle), haystack))
    return matches[0] if len(matches) else 'default'


def handle_default(field, chips, context):
    in_context = field.name in context.keys()
    value = context[field.name][str(field.value())] if in_context else field.value()
    chips.append({'content': PATTERN % (field.label, value),
                  'name': field.name, 'value': field.value()})


def handle_multiple_select(field, chips, context):
    in_context = field.name in context.keys()
    for partial_value in [f for f in field.value() if f]:
        value = context[field.name][partial_value] if in_context else partial_value
        chips.append({'content': PATTERN % (field.label, value),
                      'name': field.name, 'value': partial_value})


def handle_boolean(field, chips, context):
    values = context[field.name] if field.name in context.keys() else [
        gettext('No'),
        gettext('Yes')
    ]
    value = values[1] if field.value() else values[0]
    chips.append({'content': PATTERN % (field.label, value),
                  'name': field.name, 'value': 1 if field.value() else 0})


def handle_range(field, chips, context):
    values = ['%s <span class="currency">%s</span>' % (f, settings.DEFAULT_CURRENCY)
              if f else None for f in field.value()]
    text = [gettext('From'), gettext('To')]
    for i, value in enumerate(values):
        if value:
            chips.append({'content': PATTERN % (field.label, text[i] + ' ' + value),
                          'name': '%s_%i' % (field.name, i),
                          'value': field.value()[i]})


DEFAULT_HANDLERS = {
    'default': handle_default,
    'NullBooleanField': handle_boolean,
    'ModelMultipleChoiceField': handle_multiple_select,
    'RangeField': handle_range,
}


class ChipFactory:
    def __init__(self, form, context=None, handlers=None):
        self.chips = []
        self.context = context
        self.form = form
        self.handlers = dict(DEFAULT_HANDLERS)
        self.handlers.update(handlers)

    def make(self):
        for field in self.form:
            if field.value() not in ['', None]:
                field_type = str(type(field.field))
                if field.name in self.handlers.keys():
                    self.handlers[field.name](field, self.chips, self.context)
                else:
                    key = find_type_in_list(field_type, self.handlers.keys())
                    self.handlers[key](field, self.chips, self.context)
        return self.chips
