from jsonfield import JSONField

from django.db import models
from django.utils.translation import pgettext_lazy

DEFAULT_TYPES_INSTANCE_ID = 1


class VAT(models.Model):
    country_code = models.CharField(
        pgettext_lazy('Vat field', 'country code'), max_length=2,
        db_index=True)
    data = JSONField(pgettext_lazy('Vat field', 'data'))

    def __str__(self):
        return self.country_code


class RateTypesQuerySet(models.QuerySet):
    def singleton(self):
        return self.filter(id=DEFAULT_TYPES_INSTANCE_ID).first()


class RateTypes(models.Model):
    types = JSONField(pgettext_lazy('Vat field', 'types'))
    objects = RateTypesQuerySet.as_manager()
