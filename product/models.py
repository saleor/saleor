from decimal import Decimal
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from mptt.models import MPTTModel
from prices import FixedDiscount
from satchless.item import Item, StockedItem
from unidecode import unidecode

from utils.models import Subtyped


class BaseProduct(Subtyped, Item):

    class Meta:
        abstract = True


class BaseStockedProduct(BaseProduct, StockedItem):

    class Meta:
        abstract = True


class NotApplicable(ValueError):
    pass


class Category(MPTTModel):

    name = models.CharField(pgettext_lazy(u'Category field', u'name'),
                            max_length=128)
    slug = models.SlugField(pgettext_lazy(u'Category field', u'slug'),
                            max_length=50, unique=True)
    description = models.TextField(pgettext_lazy(u'Category field',
                                                 u'description'), blank=True)
    parent = models.ForeignKey('self', null=True, related_name='children',
                               verbose_name=pgettext_lazy(u'Category field',
                                                          u'parent'),
                               blank=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product:category', kwargs={'slug': self.slug})


class Product(BaseProduct):

    name = models.CharField(pgettext_lazy(u'Product field', u'name'),
                            max_length=128)
    price = PriceField(pgettext_lazy(u'Product field', u'price'),
                       currency=settings.SATCHLESS_DEFAULT_CURRENCY,
                       max_digits=12, decimal_places=4)
    sku = models.CharField(pgettext_lazy(u'Product field', u'sku'),
                           max_length=32, unique=True)
    category = models.ForeignKey(Category, related_name='products',
                                 verbose_name=pgettext_lazy(u'Product field',
                                                            u'category'))

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


class ProductDiscountManager(models.Manager):

    def for_product(self, product):
        # Add a caching layer here to reduce the number of queries
        return self.get_query_set().filter(products=product)


class FixedProductDiscount(models.Model):

    name = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, blank=True)
    discount = PriceField(pgettext_lazy(u'Discount field', u'discount value'),
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


class StockedProduct(BaseStockedProduct):

    stock = models.DecimalField(pgettext_lazy(u'Product item field', u'stock'),
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
