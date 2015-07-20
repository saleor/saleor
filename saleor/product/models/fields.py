from django.db import models

from .. import forms


class WeightField(models.DecimalField):

    description = 'A field which stores a weight.'

    def __init__(self, verbose_name=None, unit=None, *args, **kwargs):
        self.unit = unit
        super(WeightField, self).__init__(verbose_name, *args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super(WeightField, self).deconstruct()
        kwargs['unit'] = self.unit
        return name, path, args, kwargs

    def formfield(self, **kwargs):
        defaults = {'unit': self.unit,
                    'decimal_places': self.decimal_places,
                    'form_class': forms.WeightField}
        defaults.update(kwargs)
        return super(WeightField, self).formfield(**defaults)
