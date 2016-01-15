from __future__ import unicode_literals

import datetime
from decimal import Decimal

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import Q, Manager
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from jsonfield import JSONField
from model_utils.managers import InheritanceManager
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from satchless.item import InsufficientStock, Item, ItemRange
from unidecode import unidecode
from versatileimagefield.fields import VersatileImageField

from prices import PriceRange
from ..utils import get_attributes_display_map
from .discounts import get_variant_discounts
from .fields import WeightField


@python_2_unicode_compatible
class Category(MPTTModel):
    name = models.CharField(
        pgettext_lazy('Category field', 'name'), max_length=128)
    slug = models.SlugField(
        pgettext_lazy('Category field', 'slug'), max_length=50)
    description = models.TextField(
        pgettext_lazy('Category field', 'description'), blank=True)
    parent = models.ForeignKey(
        'self', null=True, blank=True, related_name='children',
        verbose_name=pgettext_lazy('Category field', 'parent'))
    hidden = models.BooleanField(
        pgettext_lazy('Category field', 'hidden'), default=False)

    objects = Manager()
    tree = TreeManager()

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:category',
                       kwargs={'path': self.get_full_path(),
                               'category_id': self.id})

    def get_full_path(self):
        if not self.parent_id:
            return self.slug
        return '/'.join(
            [node.slug for node in self.get_ancestors(include_self=True)])

    class Meta:
        verbose_name_plural = 'categories'
        app_label = 'product'

    def set_hidden_descendants(self, hidden):
        self.get_descendants().update(hidden=hidden)


class ProductManager(InheritanceManager):
    def get_available_products(self):
        today = datetime.datetime.today()
        return self.get_queryset().filter(
            Q(available_on__lte=today) | Q(available_on__isnull=True))


@python_2_unicode_compatible
class Product(models.Model, ItemRange):
    name = models.CharField(
        pgettext_lazy('Product field', 'name'), max_length=128)
    description = models.TextField(
        verbose_name=pgettext_lazy('Product field', 'description'))
    categories = models.ManyToManyField(
        Category, verbose_name=pgettext_lazy('Product field', 'categories'),
        related_name='products')
    price = PriceField(
        pgettext_lazy('Product field', 'price'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2)
    weight = WeightField(
        pgettext_lazy('Product field', 'weight'), unit=settings.DEFAULT_WEIGHT,
        max_digits=6, decimal_places=2)
    available_on = models.DateField(
        pgettext_lazy('Product field', 'available on'), blank=True, null=True)
    attributes = models.ManyToManyField(
        'ProductAttribute', related_name='products', blank=True)
    updated_at = models.DateTimeField(
        pgettext_lazy('Product field', 'updated at'), auto_now=True, null=True)

    objects = ProductManager()

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

    def get_price_range(self, **kwargs):
        prices = [item.get_price_per_item(**kwargs) for item in self]
        if not prices:
            raise AttributeError(
                'Calling get_price_range() on an empty item range')
        return PriceRange(min(prices), max(prices))

    def is_in_stock(self):
        return any(variant.is_in_stock() for variant in self)

    def get_first_category(self):
        for category in self.categories.all():
            if not category.hidden:
                return category
        return None


@python_2_unicode_compatible
class ProductVariant(models.Model, Item):
    sku = models.CharField(
        pgettext_lazy('Variant field', 'SKU'), max_length=32, unique=True)
    name = models.CharField(
        pgettext_lazy('Variant field', 'variant name'), max_length=100,
        blank=True)
    price_override = PriceField(
        pgettext_lazy('Variant field', 'price override'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)
    weight_override = WeightField(
        pgettext_lazy('Variant field', 'weight override'),
        unit=settings.DEFAULT_WEIGHT, max_digits=6, decimal_places=2,
        blank=True, null=True)
    product = models.ForeignKey(Product, related_name='variants')
    attributes = JSONField(pgettext_lazy('Variant field', 'attributes'),
                           default={})

    objects = InheritanceManager()

    class Meta:
        app_label = 'product'

    def __str__(self):
        return self.name or self.sku

    def get_weight(self):
        return self.weight_override or self.product.weight

    def check_quantity(self, quantity):
        available_quantity = self.get_stock_quantity()
        if quantity > available_quantity:
            raise InsufficientStock(self)

    def get_stock_quantity(self):
        return sum([stock.quantity for stock in self.stock.all()])

    def get_price_per_item(self, discounts=None, **kwargs):
        price = self.price_override or self.product.price
        if discounts:
            discounts = list(
                get_variant_discounts(self, discounts, **kwargs))
            if discounts:
                price = min(price | discount for discount in discounts)
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

    def is_in_stock(self):
        return any(
            [stock_item.quantity > 0 for stock_item in self.stock.all()])

    def get_attribute(self, pk):
        return self.attributes.get(str(pk))

    def display_variant(self, attributes=None):
        if attributes is None:
            attributes = self.product.attributes.all()
        values = get_attributes_display_map(self, attributes).values()
        if values:
            return ', '.join([smart_text(value) for value in values])
        else:
            return smart_text(self)

    def display_product(self, attributes=None):
        return '%s (%s)' % (smart_text(self.product),
                            self.display_variant(attributes=attributes))

    def select_stockrecord(self):
        # By default selects stock with lowest cost price
        stock = sorted(self.stock.all(), key=lambda stock: stock.cost_price,
                       reverse=True)
        if stock:
            return stock[0]

    def get_cost_price(self):
        stock = self.select_stockrecord()
        if stock:
            return stock.cost_price


@python_2_unicode_compatible
class Stock(models.Model):
    variant = models.ForeignKey(
        ProductVariant, related_name='stock',
        verbose_name=pgettext_lazy('Stock item field', 'variant'))
    location = models.CharField(
        pgettext_lazy('Stock item field', 'location'), max_length=100)
    quantity = models.IntegerField(
        pgettext_lazy('Stock item field', 'quantity'),
        validators=[MinValueValidator(0)], default=Decimal(1))
    cost_price = PriceField(
        pgettext_lazy('Stock item field', 'cost price'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)

    class Meta:
        app_label = 'product'
        unique_together = ('variant', 'location')

    def __str__(self):
        return '%s - %s' % (self.variant.name, self.location)


@python_2_unicode_compatible
class ProductAttribute(models.Model):
    name = models.SlugField(
        pgettext_lazy('Product attribute field', 'internal name'),
        max_length=50, unique=True)
    display = models.CharField(
        pgettext_lazy('Product attribute field', 'display name'),
        max_length=100)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.display

    def get_formfield_name(self):
        return slugify('attribute-%s' % self.name)

    def has_values(self):
        return self.values.exists()


@python_2_unicode_compatible
class AttributeChoiceValue(models.Model):
    display = models.CharField(
        pgettext_lazy('Attribute choice value field', 'display name'),
        max_length=100)
    color = models.CharField(
        pgettext_lazy('Attribute choice value field', 'color'),
        max_length=7,
        validators=[RegexValidator('^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')],
        blank=True)
    image = VersatileImageField(
        pgettext_lazy('Attribute choice value field', 'image'),
        upload_to='attributes', blank=True, null=True)
    attribute = models.ForeignKey(ProductAttribute, related_name='values')

    def __str__(self):
        return self.display
