from decimal import Decimal
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.fields.related import SingleRelatedObjectDescriptor
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy as _
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

    def get_query_set(self):
        return SubtypedQuerySet(self.model)


class Subtyped(models.Model):

    objects = SubtypedManager()

    class Meta:
        abstract = True


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


class Product(models.Model, Item):

    name = models.CharField(_('Product field', 'name'), max_length=128)
    price = PriceField(_('Product field', 'price'), currency='USD',
                       max_digits=12, decimal_places=4)
    category = models.ForeignKey(Category, related_name='products',
                                 verbose_name=_('Product field', 'category'))
    stock = models.DecimalField(_('Product item field', 'stock'),
                                max_digits=10, decimal_places=4,
                                default=Decimal(1))

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
