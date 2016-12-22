from __future__ import unicode_literals

import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.postgres.fields import HStoreField
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.db.models import F, Manager, Q
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from mptt.managers import TreeManager
from mptt.models import MPTTModel
from satchless.item import InsufficientStock, Item, ItemRange
from unidecode import unidecode
from versatileimagefield.fields import VersatileImageField

from ...discount.models import get_variant_discounts
from .fields import WeightField
from .utils import get_attributes_display_map
from ...search import index


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


@python_2_unicode_compatible
class ProductClass(models.Model):
    name = models.CharField(
        pgettext_lazy('Product field', 'name'), max_length=128)
    has_variants = models.BooleanField(default=True)
    product_attributes = models.ManyToManyField(
        'ProductAttribute', related_name='products_class', blank=True)
    variant_attributes = models.ManyToManyField(
        'ProductAttribute', related_name='product_variants_class', blank=True)

    class Meta:
        app_label = 'product'

    def __str__(self):
        return self.name

    def __repr__(self):
        class_ = type(self)
        return '<%s.%s(pk=%r, name=%r)>' % (
            class_.__module__, class_.__name__, self.pk, self.name)


class ProductManager(models.Manager):
    def get_available_products(self):
        today = datetime.date.today()
        return self.get_queryset().filter(
            Q(available_on__lte=today) | Q(available_on__isnull=True))


@python_2_unicode_compatible
class Product(models.Model, ItemRange, index.Indexed):
    product_class = models.ForeignKey(ProductClass, related_name='products')
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
    attributes = HStoreField(pgettext_lazy('Product field', 'attributes'),
                             default={})
    updated_at = models.DateTimeField(
        pgettext_lazy('Product field', 'updated at'), auto_now=True, null=True)

    objects = ProductManager()

    search_fields = [
        index.SearchField('name', partial_match=True),
        index.SearchField('description'),
        index.FilterField('available_on')]

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

    def is_in_stock(self):
        return any(variant.is_in_stock() for variant in self)

    def get_first_category(self):
        for category in self.categories.all():
            if not category.hidden:
                return category
        return None

    def is_available(self):
        today = datetime.date.today()
        return self.available_on is None or self.available_on <= today

    def get_first_image(self):
        first_image = self.images.first()

        if first_image:
            return first_image.image
        return None

    def get_attribute(self, pk):
        return self.attributes.get(smart_text(pk))

    def set_attribute(self, pk, value_pk):
        self.attributes[smart_text(pk)] = smart_text(value_pk)


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
    attributes = HStoreField(pgettext_lazy('Variant field', 'attributes'),
                             default={})
    images = models.ManyToManyField('ProductImage', through='VariantImage')

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
        if not len(self.stock.all()):
            return 0
        return max([stock.quantity_available for stock in self.stock.all()])

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
            [stock.quantity_available > 0 for stock in self.stock.all()])

    def get_attribute(self, pk):
        return self.attributes.get(smart_text(pk))

    def set_attribute(self, pk, value_pk):
        self.attributes[smart_text(pk)] = smart_text(value_pk)

    def display_variant(self, attributes=None):
        if attributes is None:
            attributes = self.product.product_class.variant_attributes.all()
        values = get_attributes_display_map(self, attributes).values()
        if values:
            return ', '.join([smart_text(value) for value in values])
        else:
            return smart_text(self)

    def display_product(self, attributes=None):
        return '%s (%s)' % (smart_text(self.product),
                            self.display_variant(attributes=attributes))

    def get_first_image(self):
        return self.product.get_first_image()

    def select_stockrecord(self, quantity=1):
        # By default selects stock with lowest cost price
        stock = filter(
            lambda stock: stock.quantity_available >= quantity,
            self.stock.all())
        stock = sorted(stock, key=lambda stock: stock.cost_price, reverse=True)
        if stock:
            return stock[0]

    def get_cost_price(self):
        stock = self.select_stockrecord()
        if stock:
            return stock.cost_price


@python_2_unicode_compatible
class StockLocation(models.Model):
    name = models.CharField(
        pgettext_lazy('Stock item field', 'location'), max_length=100)

    def __str__(self):
        return self.name


class StockManager(models.Manager):

    def allocate_stock(self, stock, quantity):
        stock.quantity_allocated = F('quantity_allocated') + quantity
        stock.save(update_fields=['quantity_allocated'])

    def deallocate_stock(self, stock, quantity):
        stock.quantity_allocated = F('quantity_allocated') - quantity
        stock.save(update_fields=['quantity_allocated'])

    def decrease_stock(self, stock, quantity):
        stock.quantity = F('quantity') - quantity
        stock.quantity_allocated = F('quantity_allocated') - quantity
        stock.save(update_fields=['quantity', 'quantity_allocated'])


@python_2_unicode_compatible
class Stock(models.Model):
    variant = models.ForeignKey(
        ProductVariant, related_name='stock',
        verbose_name=pgettext_lazy('Stock item field', 'variant'))
    location = models.ForeignKey(StockLocation, null=True)
    quantity = models.IntegerField(
        pgettext_lazy('Stock item field', 'quantity'),
        validators=[MinValueValidator(0)], default=Decimal(1))
    quantity_allocated = models.IntegerField(
        pgettext_lazy('Stock item field', 'allocated quantity'),
        validators=[MinValueValidator(0)], default=Decimal(0))
    cost_price = PriceField(
        pgettext_lazy('Stock item field', 'cost price'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)

    objects = StockManager()

    class Meta:
        app_label = 'product'
        unique_together = ('variant', 'location')

    def __str__(self):
        return '%s - %s' % (self.variant.name, self.location)

    @property
    def quantity_available(self):
        return max(self.quantity - self.quantity_allocated, 0)


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
    attribute = models.ForeignKey(ProductAttribute, related_name='values')

    def __str__(self):
        return self.display
