from __future__ import unicode_literals
from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.db import models
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from model_utils.managers import InheritanceManager
from mptt.models import MPTTModel
from satchless.item import ItemRange, Item
from unidecode import unidecode

from .discounts import get_product_discounts


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
    sku = models.CharField(
        pgettext_lazy('Product field', 'SKU'), max_length=32, unique=True)
    description = models.TextField(
        verbose_name=pgettext_lazy('Product field', 'description'))
    collection = models.CharField(db_index=True, max_length=100, blank=True)
    categories = models.ManyToManyField(
        Category, verbose_name=pgettext_lazy('Product field', 'categories'),
        related_name='products')
    price = PriceField(pgettext_lazy('Product field', 'price'),
                       currency=settings.DEFAULT_CURRENCY, max_digits=12,
                       decimal_places=4)

    objects = InheritanceManager()

    class Meta:
        app_label = 'product'

    def __iter__(self):
        if self.variants.exists():
            if not hasattr(self, '__variants'):
                setattr(self, '__variants',
                        self.variants.select_subclasses().all())
            return iter(getattr(self, '__variants'))
        else:
            return iter([self])

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

    def get_price_per_item(self, item, discounts=None, **kwargs):
        price = self.price
        if discounts:
            discounts = list(get_product_discounts(self, discounts, **kwargs))
            if discounts:
                modifier = max(discounts)
                price += modifier
        return price

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

    def is_available(self):
        if self.variants.exists():
            return any(variant.is_item_available() for variant in self)
        else:
            return self.is_item_available()

    def is_item_available(self):
        raise NotImplementedError()


@python_2_unicode_compatible
class ProductVariant(models.Model, Item):
    name = models.CharField(pgettext_lazy('Variant field', 'name'),
                            max_length=100)
    sku = models.CharField(pgettext_lazy('Product field', 'SKU'), max_length=32,
                           unique=True)
    price = PriceField(pgettext_lazy('Product field', 'price'),
                       currency=settings.DEFAULT_CURRENCY, max_digits=12,
                       decimal_places=4, blank=True, null=True)
    product = models.ForeignKey(Product, related_name='variants')

    objects = InheritanceManager()

    class Meta:
        app_label = 'product'

    def __str__(self):
        return self.product.name

    def get_price_per_item(self, discounts=None, **kwargs):
        if self.price is not None:
            price = self.price
        else:
            price = self.product.price
        if discounts:
            discounts = list(get_product_discounts(self, discounts, **kwargs))
            if discounts:
                modifier = max(discounts)
                price += modifier
        return price

    def get_absolute_url(self):
        slug = self.product.get_slug()
        product_id = self.product.id
        return reverse('product:details',
                       kwargs={'slug': slug, 'product_id': product_id})

    def as_data(self):
        return {
            'product_name': str(self),
            'product_id': self.product.pk,
            'variant_id': self.pk,
            'unit_price': str(self.get_price_per_item().gross)}

    def is_shipping_required(self):
        return True

    def is_item_available(self):
        return False


@python_2_unicode_compatible
class Stock(models.Model):
    product = models.ForeignKey(Product,
                                verbose_name=pgettext_lazy('Stock item field',
                                                           'product'))
    variant = models.ForeignKey(ProductVariant,
                                verbose_name=pgettext_lazy('Stock item field',
                                                           'variant'),
                                blank=True, null=True)
    stock = models.IntegerField(pgettext_lazy('Stock item field', 'stock'),
                                validators=[MinValueValidator(0)],
                                default=Decimal(1))
    location = models.CharField(pgettext_lazy('Stock item field', 'location'),
                                max_length=100)
    cost_price = PriceField(pgettext_lazy('Stock item field', 'cost price'),
                       currency=settings.DEFAULT_CURRENCY, max_digits=12,
                       decimal_places=4, blank=True, null=True)

    class Meta:
        app_label = 'product'
        unique_together = ('product', 'variant', 'stock')

    def __str__(self):
        return self.product.name
