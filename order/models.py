from django.conf import settings
from django.db import models
from django.utils.translation import pgettext_lazy as _
from django_prices.models import PriceField
from prices import Price
from satchless.item import ItemSet, ItemLine
from saleor import countries
from uuid import uuid4
import datetime
from product.models import Product


class PaymentInfo(ItemLine):

    name = None
    price = None
    description = None

    def __init__(self, name, price, description):
        self.name = name
        self.price = price
        self.description = description

    def get_price_per_item(self, **kwargs):
        return self.price


class Order(models.Model, ItemSet):

    STATUS_CHOICES = (
        ('checkout', _('Order status field value', 'undergoing checkout')),
        ('payment-pending', _('Order status field value',
                              'waiting for payment')),
        ('payment-complete', _('Order status field value', 'paid')),
        ('payment-failed', _('Order status field value', 'payment failed')),
        ('delivery', _('Order status field value', 'shipped')),
        ('cancelled', _('Order status field value', 'cancelled')),
    )

    status = models.CharField(_('Order field', 'order status'), max_length=32,
                              choices=STATUS_CHOICES, default='checkout')
    created = models.DateTimeField(_('Order field', 'created'),
                                   default=datetime.datetime.now,
                                   editable=False, blank=True)
    last_status_change = models.DateTimeField(_('Order field',
                                                'last status change'),
                                              default=datetime.datetime.now,
                                              editable=False, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True,
                             related_name='+', verbose_name=_('Order field',
                                                              'user'))
    billing_first_name = models.CharField(_('Order field billing',
                                            'first name'),
                                          max_length=256, blank=True)
    billing_last_name = models.CharField(_('Order field billing', 'last name'),
                                         max_length=256, blank=True)
    billing_company_name = models.CharField(_('Order field billing',
                                              'company name'),
                                            max_length=256, blank=True)
    billing_street_address_1 = models.CharField(_('Order field billing',
                                                  'street address 1'),
                                                max_length=256, blank=True)
    billing_street_address_2 = models.CharField(_('Order field billing',
                                                  'street address 2'),
                                                max_length=256, blank=True)
    billing_city = models.CharField(_('Order field billing', 'city'),
                                    max_length=256, blank=True)
    billing_postal_code = models.CharField(_('Order field billing',
                                             'postal code'),
                                           max_length=20, blank=True)
    billing_country = models.CharField(_('Order field billing', 'country'),
                                       choices=countries.COUNTRY_CHOICES,
                                       max_length=2, blank=True)
    billing_country_area = models.CharField(_('Order field billing',
                                              'country administrative area'),
                                            max_length=128, blank=True)
    billing_tax_id = models.CharField(_('Order field billing', 'tax ID'),
                                      max_length=40, blank=True)
    billing_phone = models.CharField(_('Order field billing',
                                       'phone number'), max_length=30,
                                     blank=True)
    payment_type = models.CharField(_('Order field', 'payment type'),
                                    max_length=256, blank=True)
    payment_type_name = models.CharField(_('Order field', 'payment name'),
                                         max_length=128, blank=True,
                                         editable=False)
    payment_type_description = models.TextField(_('Order field',
                                                  'payment description'),
                                                blank=True)
    payment_price = PriceField(_('Order field', 'payment unit price'),
                               currency=settings.SATCHLESS_DEFAULT_CURRENCY,
                               max_digits=12, decimal_places=4, default=0,
                               editable=False)
    token = models.CharField(_('Order field', 'token'), max_length=36,
                             blank=True, default='')

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
        for g in self.get_groups():
            yield g
        payment = self.get_payment()
        if payment:
            yield payment

    def __repr__(self):
        return '<Order #%r>' % (self.id,)

    def get_default_currency(self):
        return settings.SATCHLESS_DEFAULT_CURRENCY

    @property
    def billing_full_name(self):
        return u'%s %s' % (self.billing_first_name, self.billing_last_name)

    def get_groups(self):
        return self.groups.all()

    def get_delivery_price(self):
        return sum([g.get_delivery().get_total() for g in self.get_groups()],
                   Price(0, currency=settings.SATCHLESS_DEFAULT_CURRENCY))

    def get_payment(self):
        return PaymentInfo(name=self.payment_type_name,
                           price=self.payment_price,
                           description=self.payment_type_description)

    def create_delivery_group(self, group):
        return self.groups.create(order=self,
                                  require_shipping_address=group.is_shipping)

    def is_empty(self):
        return not self.groups.exists()


class DeliveryInfo(ItemLine):
    name = None
    price = None
    description = None

    def __init__(self, name, price, description):
        self.name = name
        self.price = price
        self.description = description

    def get_price_per_item(self, **kwargs):
        return self.price


class DeliveryGroup(models.Model, ItemSet):

    order = models.ForeignKey('order', related_name='groups', editable=False)
    delivery_price = PriceField(_('DeliveryGroup field', 'unit price'),
                                currency=settings.SATCHLESS_DEFAULT_CURRENCY,
                                max_digits=12, decimal_places=4,
                                default=0, editable=False)
    delivery_type = models.CharField(_('DeliveryGroup field', 'type'),
                                     max_length=256, blank=True)
    delivery_type_name = models.CharField(_('DeliveryGroup field', 'name'),
                                          max_length=128, blank=True,
                                          editable=False)
    delivery_type_description = models.TextField(_('DeliveryGroup field',
                                                   'description'), blank=True,
                                                 editable=False)
    require_shipping_address = models.BooleanField(default=False,
                                                   editable=False)
    shipping_first_name = models.CharField(_('DeliveryGroup field',
                                             'first name'), max_length=256)
    shipping_last_name = models.CharField(_('DeliveryGroup field',
                                            'last name'), max_length=256)
    shipping_company_name = models.CharField(_('DeliveryGroup field',
                                               'company name'),
                                             max_length=256, blank=True)
    shipping_street_address_1 = models.CharField(_('DeliveryGroup field',
                                                   'street address 1'),
                                                 max_length=256)
    shipping_street_address_2 = models.CharField(_('DeliveryGroup field',
                                                   'street address 2'),
                                                 max_length=256, blank=True)
    shipping_city = models.CharField(_('DeliveryGroup field', 'city'),
                                     max_length=256)
    shipping_postal_code = models.CharField(_('DeliveryGroup field',
                                              'postal code'), max_length=20)
    shipping_country = models.CharField(_('DeliveryGroup field', 'country'),
                                        choices=countries.COUNTRY_CHOICES,
                                        max_length=2, blank=True)
    shipping_country_area = models.CharField(_('DeliveryGroup field',
                                               'country administrative area'),
                                             max_length=128, blank=True)
    shipping_phone = models.CharField(_('DeliveryGroup field', 'phone number'),
                                      max_length=30, blank=True)

    def __iter__(self):
        for i in self.get_items():
            yield i
        delivery = self.get_delivery()
        if delivery:
            yield delivery

    def get_default_currency(self):
        return settings.SATCHLESS_DEFAULT_CURRENCY

    def get_delivery(self):
        return DeliveryInfo(name=self.delivery_type_name,
                            price=self.delivery_price,
                            description=self.delivery_type_description)

    def get_items(self):
        return self.items.all()

    def add_item(self, variant, quantity, price, product_name=None):
        product_name = product_name or unicode(variant)
        return self.items.create(product_variant=variant, quantity=quantity,
                                 unit_price_net=price.net,
                                 product_name=product_name,
                                 unit_price_gross=price.gross)


class OrderedItem(models.Model, ItemLine):

    delivery_group = models.ForeignKey(DeliveryGroup, related_name='items',
                                        editable=False,
                                        verbose_name=_('OrderedItem field',
                                                       'delivery group'))
    product = models.ForeignKey(Product, blank=True, null=True,
                                         related_name='+',
                                         on_delete=models.SET_NULL,
                                         verbose_name=_('OrderedItem field',
                                                       'product'))
    product_name = models.CharField(_('OrderedItem field', 'product name'),
                                    max_length=128)
    quantity = models.DecimalField(_('OrderedItem field', 'quantity'),
                                   max_digits=10, decimal_places=4)
    unit_price_net = models.DecimalField(_('OrderedItem field',
                                           'unit price (net)'),
                                         max_digits=12, decimal_places=4)
    unit_price_gross = models.DecimalField(_('OrderedItem field',
                                             'unit price (gross)'),
                                           max_digits=12, decimal_places=4)

    def get_price_per_item(self, **kwargs):
        return Price(net=self.unit_price_net, gross=self.unit_price_gross,
                     currency=settings.SATCHLESS_DEFAULT_CURRENCY)

    def get_quantity(self):
        return self.quantity
