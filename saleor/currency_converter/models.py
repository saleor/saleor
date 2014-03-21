from __future__ import unicode_literals
import datetime

from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext_lazy as _


class RateManager(models.Manager):
    def today_rates(self):
        today = datetime.datetime.today()
        date_range = (
            datetime.datetime.combine(today.date(), datetime.time.min),
            datetime.datetime.combine(today.date(), datetime.time.max),
        )
        return self.get_queryset().filter(last_update__range=date_range)


@python_2_unicode_compatible
class OpenExchangeRate(models.Model):
    source_currency = models.CharField(max_length=3)
    target_currency = models.CharField(max_length=3)
    exchange_rate = models.DecimalField(max_digits=20, decimal_places=8)
    last_update = models.DateTimeField(auto_now=True)
    objects = RateManager()

    class Meta:
        unique_together = ('source_currency', 'target_currency', 'last_update')

    def __str__(self):
        return _("%s at %.6f") % (self.target_currency, self.exchange_rate)
