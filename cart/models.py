# coding: utf-8
from product.models import Product
from decimal import Decimal
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import pgettext as _p, ugettext as _
from satchless.item import ItemSet, ItemLine
from django.conf import settings
from uuid import uuid4
from satchless.cart import InvalidQuantityException


class Cart(models.Model, ItemSet):

    owner = models.ForeignKey(User, null=True, blank=True, related_name='+',
                              verbose_name=_p('Cart field','owner'))
    token = models.CharField(_p('Cart field','token'), max_length=36,
                             blank=True, default='')

    def __iter__(self):
        for i in self.get_all_items():
            yield i

    def save(self, *args, **kwargs):
        if not self.token:
            for i in xrange(100):
                token = str(uuid4())
                if not type(self).objects.filter(token=token).exists():
                    self.token = token
                    break
        return super(Cart, self).save(*args, **kwargs)

    def check_quantity(self, product, quantity, replace=False):
        '''
        Method checks quantity. Return valid quantity or raise
        InvalidQuantityException.
        '''
        if not replace:
            try:
                cart_item = self.get_item(product=product)
            except CartItem.DoesNotExist:
                pass
            else:
                quantity += cart_item.quantity

        if quantity < 0:
            quantity = Decimal(0)

        if quantity > product.stock:
            raise InvalidQuantityException(_(u'To many'),
                                           product.stock - quantity)

        return quantity

    def add_item(self, product, quantity, replace=False):
        try:
            quantity = self.check_quantity(product, quantity, replace=replace)
        except InvalidQuantityException:
            quantity = product.stock

        cart_item = self.get_item(product=product)

        if not quantity and cart_item:
            cart_item.delete()
        elif quantity and cart_item:
            cart_item.quantity = quantity
            cart_item.save(update_fields=['quantity'])
        elif quantity and not cart_item:
            cart_item = self.items.create(product=product, quantity=quantity)

        return cart_item

    def replace_item(self, product, quantity):
        return self.add_item(product, quantity, replace=True)

    def get_default_currency(self, **kwargs):
        return settings.SATCHLESS_DEFAULT_CURRENCY

    def get_item(self, product, create_instance=False):
        return self.items.get(product=product)

    def get_all_items(self):
        return list(self.items.all())

    def get_quantity(self, product):
        try:
            return self.get_item(product=product).quantity
        except CartItem.ObjectDoesNotExist:
            return Decimal('0')

    def is_empty(self):
        return not self.items.exists()


class CartItem(models.Model, ItemLine):

    cart = models.ForeignKey(Cart, related_name='items', editable=False,
                             verbose_name=_p('Cart item field','cart'))
    product = models.ForeignKey(Product, related_name='+', editable=False,
                                verbose_name=_p('Cart item field','product'))
    quantity = models.DecimalField(_p('Cart item field','quantity'),
                                   max_digits=10, decimal_places=4,
                                   default=Decimal(1))

    class Meta:
        unique_together = ('cart', 'product')

    def __unicode__(self):
        return u'%s × %.10g' % (self.product, self.quantity)

    def get_price_per_item(self, **kwargs):
        return self.product.get_price(**kwargs)

    def get_quantity(self, **kwargs):
        return self.quantity

    def save(self, *args, **kwargs):
        assert self.quantity > 0
        return super(CartItem, self).save(*args, **kwargs)
