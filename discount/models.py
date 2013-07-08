from . import ItemDiscount
from django.conf import settings
from django.db import models
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from prices import Price
from product.models import Product, Category
import operator


class SelectedProduct(models.Model, ItemDiscount):

    name = models.CharField(max_length=255)
    products = models.ManyToManyField(Product, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    discount = PriceField(pgettext_lazy(u'Discount field', u'discount value'),
                          currency=settings.SATCHLESS_DEFAULT_CURRENCY,
                          max_digits=12, decimal_places=4)

    def apply(self, price):
        return Price(price.gross - self.discount.gross,
                     currency=price.currency,
                     previous=price,
                     modifier=self,
                     operation=operator.__sub__)

    def can_apply(self, item, **kwargs):
        if not super(SelectedProduct, self).can_apply(item, **kwargs):
            return False
        if (self.products.filter(pk=item.pk).exists() or
            self.categories.filter(products=self).exists()):
            return True
        return False

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return 'SelectedProducts(name=%r, discount=%r)' % (str(self.discount),
                                                           self.name)
