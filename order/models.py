from communication.mail import send_email
from decimal import Decimal
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from prices import Price
from product.models import Product, Subtyped
from saleor.utils import build_absolute_uri
from satchless.item import ItemSet, ItemLine
from userprofile.models import Address
from uuid import uuid4
import datetime


class Order(models.Model, ItemSet):

    STATUS_CHOICES = (
        ('new', pgettext_lazy(u'Order status field value', u'New')),
        ('cancelled', pgettext_lazy(u'Order status field value',
                                    u'Cancelled')),
        ('payment-pending', pgettext_lazy(u'Order status field value',
                                          u'Waiting for payment')),
        ('fully-paid', pgettext_lazy(u'Order status field value',
                                     u'Fully paid')),
        ('shipped', pgettext_lazy(u'Order status field value',
                                  u'Shipped')))
    status = models.CharField(
        pgettext_lazy(u'Order field', u'order status'),
        max_length=32, choices=STATUS_CHOICES, default='new')
    created = models.DateTimeField(
        pgettext_lazy(u'Order field', u'created'),
        default=datetime.datetime.now, editable=False)
    last_status_change = models.DateTimeField(
        pgettext_lazy(u'Order field', u'last status change'),
        default=datetime.datetime.now, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name='orders',
        verbose_name=pgettext_lazy(u'Order field', u'user'))
    billing_address = models.ForeignKey(Address, related_name='+')
    anonymous_user_email = models.EmailField(blank=True, default='')
    token = models.CharField(
        pgettext_lazy(u'Order field', u'token'),
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

    def change_status(self, status):
        self.status = status
        self.save()

    def get_items(self):
        return OrderedItem.objects.filter(delivery_group__order=self)

    def is_full_paid(self):
        total_paid = sum([payment.total for payment in
                          self.payments.filter(status='confirmed')], Decimal())
        total = self.get_total()
        return total_paid >= total.gross

    def get_user_email(self):
        if self.user:
            return self.user.email
        return self.anonymous_user_email

    def __iter__(self):
        return iter(self.groups.all())

    def __repr__(self):
        return '<Order #%r>' % (self.id,)

    def __unicode__(self):
        return u'#%d' % (self.id, )

    @property
    def billing_full_name(self):
        return u'%s %s' % (self.billing_first_name, self.billing_last_name)

    def get_absolute_url(self):
        return reverse('order:details', kwargs={'token': self.token})

    def get_delivery_total(self):
        return sum([group.price for group in self.groups.all()],
                   Price(0, currency=settings.SATCHLESS_DEFAULT_CURRENCY))

    def send_confirmation_email(self):
        email = self.get_user_email()
        payment_url = build_absolute_uri(
            reverse('order:payment:index', kwargs={'token': self.token}))
        context = {'payment_url': payment_url}
        send_email(email, 'order/emails/confirm_email.txt', context)


class DeliveryGroup(Subtyped, ItemSet):
    STATUS_CHOICES = (
        ('new', pgettext_lazy(u'Delivery group status field value', u'New')),
        ('cancelled', pgettext_lazy(u'Delivery group status field value',
                                    u'Cancelled')),
        ('shipped', pgettext_lazy(u'Delivery group status field value',
                                  u'Shipped')))
    status = models.CharField(
        pgettext_lazy(u'Delivery group field', u'Delivery status'),
        max_length=32, default='new', choices=STATUS_CHOICES)
    order = models.ForeignKey(Order, related_name='groups', editable=False)
    price = PriceField(
        pgettext_lazy(u'Delivery group field', u'unit price'),
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

    def change_status(self, status):
        self.status = status
        self.save()

    def get_total(self, **kwargs):
        return (super(DeliveryGroup, self).get_total(**kwargs) + self.price)

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

    address = models.ForeignKey(Address, related_name='+')

    def __unicode__(self):
        return u'Shipped delivery'


class DigitalDeliveryGroup(DeliveryGroup):

    email = models.EmailField()

    def __unicode__(self):
        return u'Digital delivery'


class OrderedItem(models.Model, ItemLine):

    delivery_group = models.ForeignKey(
        DeliveryGroup, related_name='items', editable=False)
    product = models.ForeignKey(
        Product, blank=True, null=True, related_name='+',
        on_delete=models.SET_NULL,
        verbose_name=pgettext_lazy(u'OrderedItem field', u'product'))
    product_name = models.CharField(
        pgettext_lazy(u'OrderedItem field', u'product name'), max_length=128)
    quantity = models.DecimalField(
        pgettext_lazy(u'OrderedItem field', u'quantity'),
        max_digits=10, decimal_places=4)
    unit_price_net = models.DecimalField(
        pgettext_lazy(u'OrderedItem field', u'unit price (net)'),
        max_digits=12, decimal_places=4)
    unit_price_gross = models.DecimalField(
        pgettext_lazy(u'OrderedItem field', u'unit price (gross)'),
        max_digits=12, decimal_places=4)

    def get_price_per_item(self, **kwargs):
        return Price(net=self.unit_price_net, gross=self.unit_price_gross,
                     currency=settings.SATCHLESS_DEFAULT_CURRENCY)

    def __unicode__(self):
        return self.product_name

    def get_quantity(self):
        return self.quantity
