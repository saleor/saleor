from decimal import Decimal
from django.db import models
from django.db.models.fields.related import SingleRelatedObjectDescriptor
from django.utils.safestring import mark_safe
from django.utils.translation import pgettext_lazy as _
from django_prices.models import PriceField
from mptt.models import MPTTModel
from satchless.item import Item
from unidecode import unidecode
import re


class SubtypedManager(models.Manager):

    def find_subclasses(self, root):
        for a in dir(root):
            attr = getattr(root, a)
            if isinstance(attr, SingleRelatedObjectDescriptor):
                child = attr.related.model
                if (issubclass(child, root) and
                    child is not root):
                    yield a
                    for s in self.find_subclasses(child):
                        yield '%s__%s' % (a, s)

    # https://code.djangoproject.com/ticket/16572
    #def get_query_set(self):
    #    qs = super(SubtypedManager, self).get_query_set()
    #    subclasses = list(self.find_subclasses(self.model))
    #    if subclasses:
    #        return qs.select_related(*subclasses)
    #    return qs


class Subtyped(models.Model):

    subtype_attr = models.CharField(max_length=500, editable=False)
    __in_unicode = False

    objects = SubtypedManager()

    class Meta:
        abstract = True

    def __unicode__(self):
        # XXX: can we do it in more clean way?
        if self.__in_unicode:
            return unicode(super(Subtyped, self))
        subtype_instance = self.get_subtype_instance()
        if type(subtype_instance) is type(self):
            self.__in_unicode = True
            res = self.__unicode__()
            self.__in_unicode = False
            return res
        return subtype_instance.__unicode__()

    def get_subtype_instance(self):
        """
        Caches and returns the final subtype instance. If refresh is set,
        the instance is taken from database, no matter if cached copy
        exists.
        """
        subtype = self
        path = self.subtype_attr.split()
        whoami = self._meta.module_name
        remaining = path[path.index(whoami) + 1:]
        for r in remaining:
            subtype = getattr(subtype, r)
        return subtype

    def store_subtype(self, klass):
        if not self.id:
            path = [self]
            parents = self._meta.parents.keys()
            while parents:
                parent = parents[0]
                path.append(parent)
                parents = parent._meta.parents.keys()
            path = [p._meta.module_name for p in reversed(path)]
            self.subtype_attr = ' '.join(path)


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


class Product(Subtyped, Item):

    name = models.CharField(_('Product field', 'name'), max_length=128)
    price = PriceField(_('Product field', 'price'), currency='USD',
                       max_digits=12, decimal_places=4)
    category = models.ForeignKey(Category, related_name='products',
                                 verbose_name=_('Product field', 'category'))
    stock = models.DecimalField(_('Product item field','stock'),
                                max_digits=10, decimal_places=4,
                                default=Decimal(1))

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return ('product:details', [self.get_slug(), self.id])

    def get_price_per_item(self, **kwargs):
        return self.price

    def get_slug(self):
        value = unidecode(self.name)
        value = re.sub(r'[^\w\s-]', '', value).strip().lower()

        return mark_safe(re.sub(r'[-\s]+', '-', value))
