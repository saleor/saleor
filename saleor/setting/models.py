from django.db import models
from django.utils.translation import pgettext_lazy
from django.utils.encoding import python_2_unicode_compatible


INTEGER = 'i'
STRING = 's'
BOOLEAN = 'b'


@python_2_unicode_compatible
class Setting(models.Model):
    VALUE_TYPE_CHOICES = (
        (INTEGER, pgettext_lazy('Settings', 'Integer')),
        (STRING, pgettext_lazy('Settings', 'String')),
        (BOOLEAN, pgettext_lazy('Settings', 'Boolean')),
    )
    name = models.CharField(
        pgettext_lazy('Settings field', 'name'), max_length=128)
    value_type = models.CharField(pgettext_lazy('Settings field', 'value type'),
                                  max_length=1, choices=VALUE_TYPE_CHOICES)
    value = models.CharField(
        pgettext_lazy('Settings field', 'value'), max_length=256)

    def convert_value(self):
        if self.value_type == self.INTEGER:
            return int(self.value)
        elif self.value_type == self.BOOLEAN:
            return self._to_bool()
        elif self.value_type == self.STRING:
            return self.value
        else:
            raise ValueError('Incorrect value')

    def _to_bool(self):
        values_dict = {'true': True, 'false': False}
        try:
            return values_dict[self.value.lower()]
        except KeyError:
            raise ValueError('Cannot convert to boolean')

    def __str__(self):
        return '%s: %s' % (self.name, self.value)
