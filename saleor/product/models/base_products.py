from __future__ import unicode_literals
import re

from django.core.urlresolvers import reverse
from django.utils.encoding import python_2_unicode_compatible
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy
from mptt.models import MPTTModel
from satchless.item import ItemRange
from unidecode import unidecode

from ...core.utils.models import Subtyped


@python_2_unicode_compatible
class Category(MPTTModel):
    name = models.CharField(
        pgettext_lazy('Category field', 'name'), max_length=128)
    slug = models.SlugField(
        pgettext_lazy('Category field', 'slug'), max_length=50, unique=True)
    description = models.TextField(
        pgettext_lazy('Category field', 'description'), blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        verbose_name=pgettext_lazy('Category field', 'parent'))

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:category', kwargs={'slug': self.slug})

    class Meta:
        verbose_name_plural = 'categories'
        app_label = 'product'


@python_2_unicode_compatible
class Product(Subtyped, ItemRange):
    name = models.CharField(
        pgettext_lazy('Product field', 'name'), max_length=128)
    category = models.ForeignKey(
        Category, verbose_name=pgettext_lazy('Product field', 'category'),
        related_name='products')

    collection = models.CharField(db_index=True, max_length=100,
                                  null=True, blank=True)

    class Meta:
        app_label = 'product'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:details', kwargs={'slug': self.get_slug(),
                                                  'product_id': self.id})

    def get_slug(self):
        value = unidecode(self.name)
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()

        return mark_safe(re.sub(r'[-\s]+', '-', value))

    def get_products_from_collection(self):
        return Product.objects.filter(collection=self.collection,
                                      collection__isnull=False)

    def __iter__(self):
        return iter(self.variants.all())

    def get_formatted_price(self, price):
        return "{0} {1}".format(price.gross, price.currency)

    def admin_get_price_min(self):
        price = self.get_price_range().min_price
        return self.get_formatted_price(price)
    admin_get_price_min.short_description = pgettext_lazy(
        'Product admin page', 'Minimal price'
    )

    def admin_get_price_max(self):
        price = self.get_price_range().max_price
        return self.get_formatted_price(price)
    admin_get_price_max.short_description = pgettext_lazy(
        'Product admin page', 'Maximal price'
    )