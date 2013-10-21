from __future__ import unicode_literals
from decimal import Decimal
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy
from django_images.models import Image
from django_prices.models import PriceField
from mptt.models import MPTTModel
from prices import FixedDiscount
from satchless.item import Item, StockedItem
from unidecode import unidecode

from ..core.utils.models import Subtyped


class NotApplicable(ValueError):
    pass


class Category(MPTTModel):

    name = models.CharField(pgettext_lazy('Category field', 'name'),
                            max_length=128)
    slug = models.SlugField(pgettext_lazy('Category field', 'slug'),
                            max_length=50, unique=True)
    description = models.TextField(pgettext_lazy('Category field',
                                                 'description'), blank=True)
    parent = models.ForeignKey('self', null=True, related_name='children',
                               verbose_name=pgettext_lazy('Category field',
                                                          'parent'),
                               blank=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:category', kwargs={'slug': self.slug})


class Product(Subtyped, Item):

    name = models.CharField(pgettext_lazy('Product field', 'name'),
                            max_length=128)
    price = PriceField(pgettext_lazy('Product field', 'price'),
                       currency=settings.SATCHLESS_DEFAULT_CURRENCY,
                       max_digits=12, decimal_places=4)
    sku = models.CharField(pgettext_lazy('Product field', 'sku'),
                           max_length=32, unique=True)
    category = models.ForeignKey(Category, related_name='products',
                                 verbose_name=pgettext_lazy('Product field',
                                                            'category'))

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:details', kwargs={'slug': self.get_slug(),
                                                  'product_id': self.id})

    def get_price_per_item(self, discounted=True, **kwargs):
        price = self.price
        if discounted:
            discounts = list(get_product_discounts(self, **kwargs))
            if discounts:
                modifier = max(discounts)
                price += modifier
        return price

    def get_slug(self):
        value = unidecode(self.name)
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()

        return mark_safe(re.sub(r'[-\s]+', '-', value))


class ImageManager(models.Manager):

    def first(self):
        return self.get_query_set()[0]


class ProductImage(Image):

    product = models.ForeignKey(Product, related_name='images')

    objects = ImageManager()

    class Meta:
        ordering = ['id']

    def __unicode__(self):
        html = '<img src="%s" alt="">' % (
            self.get_absolute_url('admin'),)
        return mark_safe(html)


class ProductDiscountManager(models.Manager):

    def for_product(self, product):
        # Add a caching layer here to reduce the number of queries
        return self.get_query_set().filter(products=product)


class FixedProductDiscount(models.Model):

    name = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, blank=True)
    discount = PriceField(pgettext_lazy('Discount field', 'discount value'),
                          currency=settings.SATCHLESS_DEFAULT_CURRENCY,
                          max_digits=12, decimal_places=4)

    objects = ProductDiscountManager()

    def modifier_for_product(self, product):
        if not self.products.filter(pk=product.pk).exists():
            raise NotApplicable('Discount not applicable for this product')
        if self.discount > product.get_price(discounted=False):
            raise NotApplicable('Discount too high for this product')
        return FixedDiscount(self.discount, name=self.name)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return 'FixedProductDiscount(name=%r, discount=%r)' % (
            str(self.discount), self.name)


def get_product_discounts(product, **kwargs):
    for discount in FixedProductDiscount.objects.for_product(product):
        try:
            yield discount.modifier_for_product(product, **kwargs)
        except NotApplicable:
            pass


class StockedProduct(models.Model, StockedItem):

    stock = models.DecimalField(pgettext_lazy('Product item field', 'stock'),
                                max_digits=10, decimal_places=4,
                                default=Decimal(1))

    class Meta:
        abstract = True

    def get_stock(self):
        return self.stock


class PhysicalProduct(models.Model):

    weight = models.PositiveIntegerField()
    length = models.PositiveIntegerField(blank=True, default=0)
    width = models.PositiveIntegerField(blank=True, default=0)
    depth = models.PositiveIntegerField(blank=True, default=0)

    class Meta:
        abstract = True


class DigitalShip(Product):

    url = models.URLField()


class Ship(Product, StockedProduct, PhysicalProduct):
    pass
