from django.db import models
from django.utils.translation import pgettext as _
from django_prices.models import PriceField
from satchless.util.models import Subtyped
from satchless.item import ItemRange
from mptt.models import MPTTModel


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


class Product(Subtyped, ItemRange):

    name = models.CharField(_('Product field', 'name'), max_length=128)
    slug = models.SlugField(_('Product field', 'slug'), max_length=50,
                            unique=True)
    price = PriceField(_('Product field', 'price'), currency='USD',
                       max_digits=12, decimal_places=4)
    category = models.ForeignKey(Category,
                                 verbose_name=_('Product field', 'category'))

    def __unicode__(self):
        return self.name
