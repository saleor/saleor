from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.cache import cache
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import python_2_unicode_compatible

from .currencies import CURRENCIES

BASE_CURRENCY = getattr(settings, 'OPENEXCHANGERATES_BASE_CURRENCY', 'USD')
CACHE_KEY = getattr(
    settings, 'OPENEXCHANGERATES_CACHE_KEY',
    'openexchangerates_conversion_rates')
CACHE_TIME = getattr(settings, 'OPENEXCHANGERATES_CACHE_TTL', 60*60)


def get_rates(qs, force_refresh=False):
    conversion_rates = cache.get(CACHE_KEY)
    if not conversion_rates or force_refresh:
        conversion_rates = {rate.to_currency: rate for rate in qs}
        cache.set(CACHE_KEY, conversion_rates, CACHE_TIME)
    return conversion_rates


class CachingManager(models.Manager):

    def get_rate(self, to_currency):  # noqa
        all_rates = get_rates(self.all())
        try:
            return all_rates[to_currency]
        except KeyError:
            msg = 'ConversionRate for %s does not exist' % to_currency
            raise ConversionRate.DoesNotExist(msg)


@python_2_unicode_compatible
class ConversionRate(models.Model):

    base_currency = BASE_CURRENCY

    to_currency = models.CharField(
        _('To'), max_length=3, db_index=True,
        choices=CURRENCIES, unique=True)

    rate = models.DecimalField(
        _('Conversion rate'), max_digits=20, decimal_places=12)

    modified_at = models.DateTimeField(auto_now=True)

    objects = CachingManager()

    class Meta:
        ordering = ['to_currency']

    def save(self, *args, **kwargs):  # noqa
        """ Save the model instance but only on successful validation. """
        self.full_clean()
        super(ConversionRate, self).save(*args, **kwargs)

    def clean(self):  # noqa
        if self.rate <= Decimal(0):
            raise ValidationError('Conversion rate has to be positive')
        if self.base_currency == self.to_currency:
            raise ValidationError(
                'Can\'t set a conversion rate for the same currency')
        super(ConversionRate, self).clean()

    def __str__(self):  # noqa
        return '1 %s = %.04f %s' % (
            self.base_currency, self.rate, self.to_currency)

    def __repr__(self):  # noqa
        format_template = (
            'ConversionRate(pk=%r, base_currency=%r, to_currency=%r, rate=%r)')
        return format_template % (
            self.pk, self.base_currency, self.to_currency, self.rate)
