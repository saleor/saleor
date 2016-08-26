from __future__ import unicode_literals
from collections import namedtuple
from uuid import uuid4

from decimal import Decimal
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible, smart_str
from django.utils.timezone import now
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from jsonfield import JSONField
from satchless.item import ItemLine, ItemSet, ItemList, partition

from ..discount.models import Voucher
from ..product.models import ProductVariant

CENTS = Decimal('0.01')


SimpleCart = namedtuple('SimpleCart', ('quantity', 'total', 'token'))


class ProductGroup(ItemList):
    def is_shipping_required(self):
        return any(p.is_shipping_required() for p in self)


class CartQueryset(models.QuerySet):

    def anonymous(self):
        return self.filter(user=None)

    def open(self):
        return self.filter(status=Cart.OPEN)

    def saved(self):
        return self.filter(status=Cart.SAVED)

    def waiting_for_payment(self):
        return self.filter(status=Cart.WAITING_FOR_PAYMENT)

    def checkout(self):
        return self.filter(status=Cart.CHECKOUT)

    def canceled(self):
        return self.filter(status=Cart.CANCELED)

    def save(self):
        self.update(status=Cart.SAVED)


class Cart(models.Model, ItemSet):

    COOKIE_NAME = 'cart'

    OPEN, SAVED, WAITING_FOR_PAYMENT, ORDERED, CHECKOUT, CANCELED = (
        'open', 'saved', 'payment', 'ordered', 'checkout', 'canceled')

    STATUS_CHOICES = (
        (OPEN, pgettext_lazy('Cart', 'Open - currently active')),
        (WAITING_FOR_PAYMENT, pgettext_lazy('Cart', 'Waiting for payment')),
        (SAVED, pgettext_lazy(
            'Cart', 'Saved - for items to be purchased later')),
        (ORDERED, pgettext_lazy(
            'Cart', 'Submitted - has been ordered at the checkout')),
        (CHECKOUT, pgettext_lazy(
            'Cart', 'Checkout - basket is processed in checkout')),
        (CANCELED, pgettext_lazy(
            'Cart', 'Canceled - basket was canceled by user'))
    )

    status = models.CharField(
        pgettext_lazy('Cart', 'order status'),
        max_length=32, choices=STATUS_CHOICES, default=OPEN)
    created = models.DateTimeField(
        pgettext_lazy('Cart', 'created'), auto_now_add=True)
    last_status_change = models.DateTimeField(
        pgettext_lazy('Cart', 'last status change'), auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name='carts',
        verbose_name=pgettext_lazy('Cart', 'user'))
    email = models.EmailField(blank=True, null=True)
    token = models.UUIDField(pgettext_lazy('Cart', 'token'),
                             primary_key=True, default=uuid4, editable=False)
    voucher = models.ForeignKey(
        Voucher, null=True, related_name='+', on_delete=models.SET_NULL)
    checkout_data = JSONField(null=True, editable=False)

    total = PriceField(
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        default=0)
    quantity = models.PositiveIntegerField(default=0)

    objects = CartQueryset.as_manager()

    class Meta:
        ordering = ('-last_status_change',)

    def __init__(self, *args, **kwargs):
        self.discounts = kwargs.pop('discounts', None)
        super(Cart, self).__init__(*args, **kwargs)

    def update_quantity(self):
        total_lines = self.count()['total_quantity']
        if not total_lines:
            total_lines = 0
        self.quantity = total_lines
        self.save(update_fields=['quantity'])

    def change_status(self, status):
        if status not in dict(self.STATUS_CHOICES):
            raise ValueError('Not expected status')
        if status != self.status:
            self.status = status
            self.last_status_change = now()
            self.save()

    def is_shipping_required(self):
        return any(line.is_shipping_required() for line in self.lines.all())

    #Satchless
    def __repr__(self):
        return 'Cart(quantity=%s)' % (self.quantity,)

    def __iter__(self):
        return iter(self.lines.select_related('product').all())

    def __len__(self):
        return self.lines.count()

    def count(self):
        lines = self.lines.all()
        return lines.aggregate(total_quantity=models.Sum('quantity'))

    def clear(self):
        self.delete()

    def create_line(self, product, quantity, data):
        line = self.lines.create(product=product, quantity=quantity, data=data)
        return line

    def get_line(self, product, data=None):
        try:
            return self.lines.get(product=product)
        except CartLine.DoesNotExist:
            return None

    def add(self, product, quantity=1, data=None, replace=False,
            check_quantity=True):
        cart_line, created = self.lines.get_or_create(
            product=product, defaults={'quantity': 0, 'data': data})
        if replace:
            new_quantity = quantity
        else:
            new_quantity = cart_line.quantity + quantity

        if new_quantity < 0:
            raise ValueError('%r is not a valid quantity (results in %r)' % (
                quantity, new_quantity))

        if check_quantity:
            product.check_quantity(new_quantity)

        cart_line.quantity = new_quantity

        if not cart_line.quantity:
            cart_line.delete()
        else:
            cart_line.save(update_fields=['quantity'])
        self.update_quantity()

    def partition(self):
        grouper = (
            lambda p: 'physical' if p.is_shipping_required() else 'digital')
        return partition(self, grouper, ProductGroup)


@python_2_unicode_compatible
class CartLine(models.Model, ItemLine):

    cart = models.ForeignKey(Cart, related_name='lines')
    product = models.ForeignKey(
        ProductVariant, related_name='+',
        verbose_name=pgettext_lazy('Cart line', 'product'))
    quantity = models.PositiveIntegerField(
        pgettext_lazy('Cart line', 'quantity'),
        validators=[MinValueValidator(0), MaxValueValidator(999)])
    data = JSONField(blank=True, default={})


    class Meta:
        unique_together = ('cart', 'product', 'data')

    def __str__(self):
        return smart_str(self.product)

    # Satchless
    def __eq__(self, other):
        if not isinstance(other, CartLine):
            return NotImplemented

        return (self.product == other.product and
                self.quantity == other.quantity and
                self.data == other.data)

    def __ne__(self, other):
        return not self == other  # pragma: no cover

    def __repr__(self):
        return 'CartLine(product=%r, quantity=%r, data=%r)' % (
            self.product, self.quantity, self.data)

    def __getstate__(self):
        return self.product, self.quantity, self.data

    def __setstate__(self, data):
        self.product, self.quantity, self.data = data

    def get_total(self, **kwargs):
        amount = super(CartLine, self).get_total(**kwargs)
        return amount.quantize(CENTS)

    def get_quantity(self, **kwargs):
        return self.quantity

    def get_price_per_item(self, discounts=None, **kwargs):
        return self.product.get_price_per_item(discounts=discounts, **kwargs)

    def is_shipping_required(self):
        return self.product.is_shipping_required()
