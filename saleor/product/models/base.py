from __future__ import unicode_literals

from django.core.urlresolvers import reverse
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.db import models
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from model_utils.managers import InheritanceManager
from mptt.models import MPTTModel
from satchless.item import ItemRange
from unidecode import unidecode


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
class Product(models.Model, ItemRange):
    name = models.CharField(
        pgettext_lazy('Product field', 'name'), max_length=128)
    category = models.ForeignKey(
        Category, verbose_name=pgettext_lazy('Product field', 'category'),
        related_name='products')
    description = models.TextField(
        verbose_name=pgettext_lazy('Product field', 'description'))
    collection = models.CharField(db_index=True, max_length=100, blank=True)

    objects = InheritanceManager()

    class Meta:
        app_label = 'product'

    def __iter__(self):
        if not hasattr(self, '__variants'):
            setattr(self, '__variants', self.variants.all())
        return iter(getattr(self, '__variants'))

    def __repr__(self):
        class_ = type(self)
        return '<%s.%s(pk=%r, name=%r)>' % (
            class_.__module__, class_.__name__, self.pk, self.name)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:details', kwargs={'slug': self.get_slug(),
                                                  'product_id': self.id})

    def get_slug(self):
        return slugify(smart_text(unidecode(self.name)))

    def get_formatted_price(self, price):
        return "{0} {1}".format(price.gross, price.currency)

    def admin_get_price_min(self):
        price = self.get_price_range().min_price
        return self.get_formatted_price(price)
    admin_get_price_min.short_description = pgettext_lazy(
        'Product admin page', 'Minimum price')

    def admin_get_price_max(self):
        price = self.get_price_range().max_price
        return self.get_formatted_price(price)
    admin_get_price_max.short_description = pgettext_lazy(
        'Product admin page', 'Maximum price')
