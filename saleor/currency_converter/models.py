from __future__ import unicode_literals
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _
import datetime


class RateManager(models.Manager):
    def today_rates(self):
        today = datetime.datetime.today()
        date_range = (
            datetime.datetime.combine(today.date(), datetime.time.min),
            datetime.datetime.combine(today.date(), datetime.time.max),
        )
        return self.get_queryset().filter(
            source__last_update__range=date_range
        )

@python_2_unicode_compatible
class RateSource(models.Model):
    name = models.CharField(max_length=100, unique=True)
    last_update = models.DateTimeField(auto_now=True)
    base_currency = models.CharField(max_length=3)

    def __str__(self):
        return _("%s rates in %s update %s") % (
            self.name, self.base_currency, self.last_update)


@python_2_unicode_compatible
class Rate(models.Model):
    source = models.ForeignKey(RateSource)
    currency = models.CharField(max_length=3)
    value = models.DecimalField(max_digits=20, decimal_places=6)
    objects = RateManager()

    class Meta:
        unique_together = ('source', 'currency')

    def __str__(self):
        return _("%s at %.6f") % (self.currency, self.value)