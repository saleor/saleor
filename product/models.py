from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models.fields.related import SingleRelatedObjectDescriptor
from django.db.models.query import QuerySet
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from mptt.models import MPTTModel
from satchless.item import Item
from unidecode import unidecode
import re


class SubtypedQuerySet(QuerySet):

    def find_subclasses(self, root):
        for a in dir(root):
            try:
                attr = getattr(root, a)
            except AttributeError:
                continue
            if isinstance(attr, SingleRelatedObjectDescriptor):
                child = attr.related.model
                if (issubclass(child, root) and
                        child is not root):
                    yield a
                    for s in self.find_subclasses(child):
                        yield '%s__%s' % (a, s)

    def subcast(self, obj):
        subtype = obj
        while True:
            root = type(subtype)
            last_root = root
            for a in dir(root):
                try:
                    attr = getattr(root, a)
                except AttributeError:
                    continue
                if isinstance(attr, SingleRelatedObjectDescriptor):
                    child = attr.related.model
                    if (issubclass(child, root) and
                            child is not root):
                        try:
                            next_type = getattr(subtype, a)
                        except models.ObjectDoesNotExist:
                            pass
                        else:
                            subtype = next_type
                            break
            if root == last_root:
                break
        return subtype

    def iterator(self, subclass=True):
        subclasses = list(self.find_subclasses(self.model))
        if subclasses and subclass:
            # https://code.djangoproject.com/ticket/16572
            related = self.select_related(*subclasses)
            for obj in related.iterator(subclass=False):
                yield obj
        else:
            objs = super(SubtypedQuerySet, self).iterator()
            for obj in objs:
                yield self.subcast(obj)


class SubtypedManager(models.Manager):

    use_for_related_fields = True

    def get_query_set(self):
        return SubtypedQuerySet(self.model)


class Subtyped(models.Model):

    objects = SubtypedManager()

    class Meta:
        abstract = True


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


class Product(Subtyped, Item):

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

    @models.permalink
    def get_absolute_url(self):
        return ('product:details',
                (),
                {'slug': self.get_slug(), 'product_id': self.id})

    def get_price_per_item(self, **kwargs):
        return self.price

    def get_slug(self):
        value = unidecode(self.name)
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()

        return mark_safe(re.sub(r'[-\s]+', '-', value))


class StockedProduct(models.Model):

    stock = models.DecimalField(pgettext_lazy(u'Product item field', u'stock'),
                                max_digits=10, decimal_places=4,
                                default=Decimal(1))

    class Meta:
        abstract = True


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
