from decimal import Decimal
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext as _
from django_prices.models import PriceField
from mptt.models import MPTTModel
from satchless.item import Item
from satchless.util.models import Subtyped
from unidecode import unidecode
import re


class Category(MPTTModel):

    name = models.CharField(_('Category field', 'name'), max_length=128)
    slug = models.SlugField(_('Category field', 'slug'), max_length=50,
                            unique=True)
    description = models.TextField(_('Category field', 'description'),
                                   blank=True)
    parent = models.ForeignKey('self', null=True, related_name='children',
                               blank=True,
                               verbose_name=_('Category field', 'parent'))

    def __unicode__(self):
        return self.name


class Product(Subtyped, Item):

    name = models.CharField(_('Product field', 'name'), max_length=128)
    price = PriceField(_('Product field', 'price'), currency='USD',
                       max_digits=12, decimal_places=4)
    category = models.ForeignKey(Category, related_name='products',
                                 verbose_name=_('Product field', 'category'))
    stock = models.DecimalField(_('Product item field','stock'),
                                max_digits=10, decimal_places=4,
                                default=Decimal(1))

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('product:details', [self.get_slug(), self.id])

    def get_price_per_item(self, **kwargs):
        return self.price

    def get_slug(self):
        value = unidecode(self.name)
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()

        return mark_safe(re.sub(r'[-\s]+', '-', value))
