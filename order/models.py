from django.conf import settings
from django.db import models
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from prices import Price
from product.models import Product, Subtyped
from satchless.item import ItemSet, ItemLine
from userprofile.models import Address
from uuid import uuid4
import datetime


class Order(models.Model, ItemSet):

    STATUS_CHOICES = (
        ('checkout', pgettext_lazy(
            'Order status field value', 'undergoing checkout')),
        ('payment-pending', pgettext_lazy(
            'Order status field value', 'waiting for payment')),
        ('payment-complete', pgettext_lazy(
            'Order status field value', 'paid')),
        ('payment-failed', pgettext_lazy(
            'Order status field value', 'payment failed')),
        ('delivery', pgettext_lazy('Order status field value', 'shipped')),
        ('payment', pgettext_lazy('Order status field value', 'payment')),
        ('cancelled', pgettext_lazy('Order status field value', 'cancelled')),
        ('completed', pgettext_lazy('Order status field value', 'completed')))

    status = models.CharField(
        pgettext_lazy('Order field', 'order status'),
        max_length=32, choices=STATUS_CHOICES, default='checkout')
    created = models.DateTimeField(
        pgettext_lazy('Order field', 'created'),
        default=datetime.datetime.now, editable=False)
    last_status_change = models.DateTimeField(
        pgettext_lazy('Order field', 'last status change'),
        default=datetime.datetime.now, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name='+',
        verbose_name=pgettext_lazy('Order field', 'user'))
    billing_address = models.ForeignKey(Address)
    payment_type = models.CharField(
        pgettext_lazy('Order field', 'payment type'),
        max_length=256, blank=True)
    payment_type_name = models.CharField(
        pgettext_lazy('Order field', 'payment name'),
        max_length=128, blank=True, editable=False)
    payment_type_description = models.TextField(
        pgettext_lazy('Order field', 'payment description'), blank=True)
    payment_price = PriceField(
        pgettext_lazy('Order field', 'payment unit price'),
        currency=settings.SATCHLESS_DEFAULT_CURRENCY,
        max_digits=12, decimal_places=4, default=0, editable=False)
    token = models.CharField(
        pgettext_lazy('Order field', 'token'),
        max_length=36, blank=True, default='')

    class Meta:
        ordering = ('-last_status_change',)

    def save(self, *args, **kwargs):
        if not self.token:
            for _i in xrange(100):
                token = str(uuid4())
                if not type(self).objects.filter(token=token).exists():
                    self.token = token
                    break
        return super(Order, self).save(*args, **kwargs)

    def __iter__(self):
        return iter(self.groups.all())

    def __repr__(self):
        return '<Order #%r>' % (self.id,)

    def __unicode__(self):
        return self.token

    @property
    def billing_full_name(self):
        return u'%s %s' % (self.billing_first_name, self.billing_last_name)

    @models.permalink
    def get_absolute_url(self):
        return ('order:details', (), {'token': self.token})

    def get_delivery_total(self):
        return sum([group.price for group in self.groups.all()],
                   Price(0, currency=settings.SATCHLESS_DEFAULT_CURRENCY))


class DeliveryGroup(Subtyped, ItemSet):

    order = models.ForeignKey('order', related_name='groups', editable=False)
    price = PriceField(
        pgettext_lazy('DeliveryGroup field', 'unit price'),
        currency=settings.SATCHLESS_DEFAULT_CURRENCY, max_digits=12,
        decimal_places=4,
        default=0,
        editable=False)

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __iter__(self):
        if self.id:
            return iter(self.items.select_related('product').all())
        return super(DeliveryGroup, self).__iter__()

    def get_total(self, **kwargs):
        return (super(DeliveryGroup, self).get_total(**kwargs) +
                self.get_delivery_total(**kwargs))

    def get_delivery_total(self, **kwargs):
        methods = self.get_delivery_methods()
        return min(method.get_price_per_item(**kwargs) for method in methods)

    def add_items_from_partition(self, partition):
        for item_line in partition:
            product_name = unicode(item_line.product)
            price = item_line.get_price_per_item()
            self.items.create(
                product=item_line.product,
                quantity=item_line.get_quantity(),
                unit_price_net=price.net,
                product_name=product_name,
                unit_price_gross=price.gross)


class ShippedDeliveryGroup(DeliveryGroup):

    address = models.ForeignKey(Address)


class DigitalDeliveryGroup(DeliveryGroup):

    email = models.EmailField()


class OrderedItem(models.Model, ItemLine):

    delivery_group = models.ForeignKey(
        DeliveryGroup, related_name='items', editable=False)
    product = models.ForeignKey(
        Product, blank=True, null=True, related_name='+',
        on_delete=models.SET_NULL,
        verbose_name=pgettext_lazy('OrderedItem field', 'product'))
    product_name = models.CharField(
        pgettext_lazy('OrderedItem field', 'product name'), max_length=128)
    quantity = models.DecimalField(
        pgettext_lazy('OrderedItem field', 'quantity'),
        max_digits=10, decimal_places=4)
    unit_price_net = models.DecimalField(
        pgettext_lazy('OrderedItem field', 'unit price (net)'),
        max_digits=12, decimal_places=4)
    unit_price_gross = models.DecimalField(
        pgettext_lazy('OrderedItem field', 'unit price (gross)'),
        max_digits=12, decimal_places=4)

    def get_price_per_item(self, **kwargs):
        return Price(net=self.unit_price_net, gross=self.unit_price_gross,
                     currency=settings.SATCHLESS_DEFAULT_CURRENCY)

    def get_quantity(self):
        return self.quantity

    def __unicode__(self):
        return self.product_name

