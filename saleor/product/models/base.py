from __future__ import unicode_literals
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator, RegexValidator
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.db import models
from django.utils.text import slugify
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from jsonfield import JSONField
from model_utils.managers import InheritanceManager
from mptt.models import MPTTModel
from satchless.item import ItemRange, Item
from unidecode import unidecode
from versatileimagefield.fields import VersatileImageField

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
    description = models.TextField(
        verbose_name=pgettext_lazy('Product field', 'description'))
    categories = models.ManyToManyField(
        Category, verbose_name=pgettext_lazy('Product field', 'categories'),
        related_name='products')
    price = PriceField(
        pgettext_lazy('Product field', 'price'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=4)
    weight = models.DecimalField(
        pgettext_lazy('Product field', 'weight'), max_digits=6,
        decimal_places=2)
    attributes = models.ManyToManyField(
        'ProductAttribute', related_name='products', blank=True, null=True)

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

    def get_price_per_item(self, item, discounts=None, **kwargs):
        price = self.price
        if price and discounts:
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
        return any(variant.is_available() for variant in self)


@python_2_unicode_compatible
class ProductVariant(models.Model, Item):
    name = models.CharField(
        pgettext_lazy('Variant field', 'name'), max_length=100)
    sku = models.CharField(
        pgettext_lazy('Variant field', 'SKU'), max_length=32, unique=True)
    price_override = PriceField(
        pgettext_lazy('Variant field', 'price override'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=4,
        blank=True, null=True)
    weight_override = models.DecimalField(
        pgettext_lazy('Variant field', 'weight override'),
        max_digits=6, decimal_places=2, blank=True, null=True)
    product = models.ForeignKey(Product, related_name='variants')
    attributes = JSONField(pgettext_lazy('Variant field', 'attributes'),
                           default={})

    objects = InheritanceManager()

    class Meta:
        app_label = 'product'

    def __str__(self):
        name = self.product.name
        if self.name:
            name += ' (%s)' % self.name
        return name

    def get_weight(self):
        return self.weight_override or self.product.weight

    def get_price_per_item(self, discounts=None, **kwargs):
        price = self.price_override or self.product.price
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

    def is_available(self):
        return any([stock_item.is_available() for stock_item in self.stock.all()])

    def get_attributes_display(self):
        display = {}
        for attr_pk, value in self.attributes.iteritems():
            attribute = ProductAttribute.objects.get(pk=attr_pk)
            if self.product.attributes.filter(pk=attribute.pk):
                if attribute.has_values():
                    try:
                        value = attribute.values.get(pk=value)
                    except ObjectDoesNotExist:
                        pass
                    else:
                        display[attribute.display] = value.display
                else:
                    display[attribute.display] = value
        return display

    def get_attribute(self, pk):
        return self.attributes.get(str(pk))


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
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=4,
        blank=True, null=True)

    class Meta:
        app_label = 'product'
        unique_together = ('variant', 'location')

    def __str__(self):
        return "%s - %s" % (self.variant.name, self.location)

    def is_available(self):
        return self.quantity > 0


@python_2_unicode_compatible
class ProductAttribute(models.Model):
    display = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.display

    def get_formfield_name(self):
        return slugify('attribute-%s' % self.display)

    def has_values(self):
        return self.values.exists()


@python_2_unicode_compatible
class AttributeChoiceValue(models.Model):
    display = models.CharField(max_length=100)
    color = models.CharField(
        max_length=7,
        validators=[RegexValidator('^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$')],
        blank=True)
    image = VersatileImageField(upload_to='attributes', blank=True, null=True)
    attribute = models.ForeignKey(ProductAttribute, related_name='values')

    def __str__(self):
        return self.display

    def get_slug(self):
        return slugify('%s %s' % (self.attribute.display, self.display))
