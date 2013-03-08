from django.conf import settings
from django.db import models
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from prices import Price
from satchless.item import ItemSet, ItemLine
from saleor import countries
from uuid import uuid4
import datetime
from product.models import Product
from userprofile.models import Address
from cart import BaseDeliveryGroup, DeliveryLine


class OrderManager(models.Manager):

    def create_from_partitions(self, partitions):
        order = self.get_query_set().create()
        for partition in partitions:
            order.groups.create_from_partition(order, partition)
        return order


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
        ('cancelled', pgettext_lazy('Order status field value', 'cancelled')))

    status = models.CharField(
        pgettext_lazy('Order field', 'order status'),
        max_length=32, choices=STATUS_CHOICES, default='checkout')
    created = models.DateTimeField(
        pgettext_lazy('Order field', 'created'),
        default=datetime.datetime.now, editable=False, blank=True)
    last_status_change = models.DateTimeField(
        pgettext_lazy('Order field', 'last status change'),
        default=datetime.datetime.now, editable=False, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name='+',
        verbose_name=pgettext_lazy('Order field', 'user'))
    billing_first_name = models.CharField(
        pgettext_lazy('Order field billing', 'first name'),
        max_length=256, blank=True)
    billing_last_name = models.CharField(
        pgettext_lazy('Order field billing', 'last name'),
        max_length=256, blank=True)
    billing_company_name = models.CharField(
        pgettext_lazy('Order field billing', 'company name'),
        max_length=256, blank=True)
    billing_street_address_1 = models.CharField(
        pgettext_lazy('Order field billing', 'street address 1'),
        max_length=256, blank=True)
    billing_street_address_2 = models.CharField(
        pgettext_lazy('Order field billing', 'street address 2'),
        max_length=256, blank=True)
    billing_city = models.CharField(
        pgettext_lazy('Order field billing', 'city'),
        max_length=256, blank=True)
    billing_postal_code = models.CharField(
        pgettext_lazy('Order field billing', 'postal code'),
        max_length=20, blank=True)
    billing_country = models.CharField(
        pgettext_lazy('Order field billing', 'country'),
        choices=countries.COUNTRY_CHOICES, max_length=2, blank=True)
    billing_country_area = models.CharField(
        pgettext_lazy('Order field billing', 'country administrative area'),
        max_length=128, blank=True)
    billing_tax_id = models.CharField(
        pgettext_lazy('Order field billing', 'tax ID'),
        max_length=40, blank=True)
    billing_phone = models.CharField(
        pgettext_lazy('Order field billing', 'phone number'),
        max_length=30, blank=True)
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

    objects = OrderManager()

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

    def set_billing_address(self, address):
        self.billing_first_name = address.first_name
        self.billing_last_name = address.last_name
        self.billing_company_name = address.company_name
        self.billing_street_address_1 = address.street_address_1
        self.billing_street_address_2 = address.street_address_2
        self.billing_city = address.city
        self.billing_postal_code = address.postal_code
        self.billing_country = address.country
        self.billing_country_area = address.country_area
        self.billing_phone = address.phone

    def get_billing_address(self):
        return Address(first_name=self.billing_first_name,
                       last_name=self.billing_last_name,
                       company_name=self.billing_company_name,
                       street_address_1=self.billing_street_address_1,
                       street_address_2=self.billing_street_address_2,
                       city=self.billing_city,
                       postal_code=self.billing_postal_code,
                       country=self.billing_country,
                       country_area=self.billing_country_area,
                       phone=self.billing_phone)


class DeliveryGroupManager(models.Manager):

    def create_from_partition(self, order, partition):
        group = self.get_query_set().create(order=order)
        for item_line in partition:
            product_name = unicode(item_line.product)
            price = item_line.get_price_per_item()
            group.items.create(
                product=item_line.product,
                quantity=item_line.get_quantity(),
                unit_price_net=price.net,
                product_name=product_name,
                unit_price_gross=price.gross)
        return group


class DeliveryGroup(models.Model, BaseDeliveryGroup):

    order = models.ForeignKey('order', related_name='groups', editable=False)
    delivery_price = PriceField(
        pgettext_lazy('DeliveryGroup field', 'unit price'),
        currency=settings.SATCHLESS_DEFAULT_CURRENCY, max_digits=12,
        decimal_places=4, default=0, editable=False)
    delivery_type = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'type'),
        max_length=256, blank=True)
    delivery_type_name = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'name'),
        max_length=128, blank=True, editable=False)
    delivery_type_description = models.TextField(
        pgettext_lazy('DeliveryGroup field', 'description'),
        blank=True, editable=False)
    require_shipping_address = models.BooleanField(
        default=False, editable=False)
    shipping_first_name = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'first name'), max_length=256)
    shipping_last_name = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'last name'), max_length=256)
    shipping_company_name = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'company name'),
        max_length=256, blank=True)
    shipping_street_address_1 = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'street address 1'),
        max_length=256)
    shipping_street_address_2 = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'street address 2'),
        max_length=256, blank=True)
    shipping_city = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'city'), max_length=256)
    shipping_postal_code = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'postal code'), max_length=20)
    shipping_country = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'country'),
        choices=countries.COUNTRY_CHOICES, max_length=2, blank=True)
    shipping_country_area = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'country administrative area'),
        max_length=128, blank=True)
    shipping_phone = models.CharField(
        pgettext_lazy('DeliveryGroup field', 'phone number'),
        max_length=30, blank=True)

    objects = DeliveryGroupManager()

    def get_delivery(self):
        return DeliveryLine(name=self.delivery_type_name,
                            price=self.delivery_price,
                            description=self.delivery_type_description)


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
