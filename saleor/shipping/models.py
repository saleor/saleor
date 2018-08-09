from django.conf import settings
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy
from django_countries.fields import CountryField
from django_prices.models import MoneyField
from prices import MoneyRange

from . import ShippingMethodType
from ..core.utils import format_money
from ..shipping.utils import get_taxed_shipping_price


class ShippingZone(models.Model):
    name = models.CharField(max_length=100)
    countries = CountryField(multiple=True)

    def __str__(self):
        return self.name

    def get_countries_display(self):
        if len(self.countries) <= 3:
            return ','.join((country.name for country in self.countries))
        return pgettext_lazy(
            'Number of countries shipping zone apply to',
            '%(num_of_countries)d countries' % {
                'num_of_countries': len(self.countries)})

    @property
    def price_range(self):
        prices = [
            shipping_method.get_total_price()
            for shipping_method in self.shipping_methods.all()]
        if prices:
            return MoneyRange(min(prices).net, max(prices).net)
        return None

    class Meta:
        permissions = ((
            'manage_shipping', pgettext_lazy(
                'Permission description', 'Manage shipping.')),)


class ShippingMethod(models.Model):
    name = models.CharField(max_length=100)
    type = models.CharField(
        max_length=30, choices=ShippingMethodType.CHOICES,
        default=ShippingMethodType.WEIGHT_BASED)
    price = MoneyField(
        currency=settings.DEFAULT_CURRENCY, max_digits=12,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES, default=0)
    shipping_zone = models.ForeignKey(
        ShippingZone, related_name='shipping_methods',
        on_delete=models.CASCADE)

    def __str__(self):
        return self.name

    def get_total_price(self, taxes=None):
        return get_taxed_shipping_price(self.price, taxes)

    def get_ajax_label(self):
        price_html = format_money(self.price)
        label = mark_safe('%s %s' % (self, price_html))
        return label
