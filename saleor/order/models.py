from __future__ import unicode_literals

from decimal import Decimal
from uuid import uuid4

import emailit.api
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible, smart_text
from django.utils.timezone import now
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from payments import PurchasedItem
from payments.models import BasePayment
from prices import Price, FixedDiscount
from satchless.item import ItemLine, ItemSet

from ..core.utils import build_absolute_uri
from ..discount.models import Voucher
from ..product.models import Product, Stock
from ..userprofile.models import Address
from ..search import index
from . import Status


class OrderManager(models.Manager):

    def recalculate_order(self, order):
        prices = [group.get_total() for group in order
                  if group.status != Status.CANCELLED]
        total_net = sum(p.net for p in prices)
        total_gross = sum(p.gross for p in prices)
        shipping = [group.shipping_price for group in order]
        if shipping:
            total_shipping = sum(shipping[1:], shipping[0])
        else:
            total_shipping = Price(0, currency=settings.DEFAULT_CURRENCY)
        total = Price(net=total_net, gross=total_gross,
                      currency=settings.DEFAULT_CURRENCY)
        total += total_shipping
        order.total = total
        order.save()


@python_2_unicode_compatible
class Order(models.Model, ItemSet, index.Indexed):
    status = models.CharField(
        pgettext_lazy('Order field', 'order status'),
        max_length=32, choices=Status.CHOICES, default=Status.NEW)
    created = models.DateTimeField(
        pgettext_lazy('Order field', 'created'),
        default=now, editable=False)
    last_status_change = models.DateTimeField(
        pgettext_lazy('Order field', 'last status change'),
        default=now, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name='orders',
        verbose_name=pgettext_lazy('Order field', 'user'))
    tracking_client_id = models.CharField(
        max_length=36, blank=True, editable=False)
    billing_address = models.ForeignKey(
        Address, related_name='+', editable=False)
    shipping_address = models.ForeignKey(
        Address, related_name='+', editable=False, null=True)
    user_email = models.EmailField(
        blank=True, default='', editable=False)
    token = models.CharField(
        pgettext_lazy('Order field', 'token'), max_length=36, unique=True)
    total_net = PriceField(
        pgettext_lazy('Order field', 'total'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)
    total_tax = PriceField(
        pgettext_lazy('Order field', 'total'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)
    voucher = models.ForeignKey(
        Voucher, null=True, related_name='+', on_delete=models.SET_NULL)
    discount_amount = PriceField(
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)
    discount_name = models.CharField(max_length=255, default='', blank=True)

    objects = OrderManager()

    search_fields = [
        index.SearchField('id'),
        index.SearchField('get_user_current_email'),
        index.SearchField('_index_billing_phone'),
        index.SearchField('_index_shipping_phone')]

    class Meta:
        ordering = ('-last_status_change',)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        return super(Order, self).save(*args, **kwargs)

    def change_status(self, status):
        if status != self.status:
            self.status = status
            self.save()
            self.history.create(status=status)

    def get_items(self):
        return OrderedItem.objects.filter(delivery_group__order=self)

    def is_fully_paid(self):
        total_paid = sum([payment.total for payment in
                          self.payments.filter(status='confirmed')], Decimal())
        total = self.get_total()
        return total_paid >= total.gross

    def get_user_current_email(self):
        if self.user:
            return self.user.email
        else:
            return self.user_email

    def _index_billing_phone(self):
        billing_address = self.billing_address
        return billing_address.phone

    def _index_shipping_phone(self):
        return self.shipping_address.phone

    def __iter__(self):
        return iter(self.groups.all())

    def __repr__(self):
        return '<Order #%r>' % (self.id,)

    def __str__(self):
        return '#%d' % (self.id, )

    @property
    def discount(self):
        return FixedDiscount(
            amount=self.discount_amount, name=self.discount_name)

    def get_total(self):
        return self.total

    @property
    def billing_full_name(self):
        return '%s %s' % (self.billing_first_name, self.billing_last_name)

    def get_absolute_url(self):
        return reverse('order:details', kwargs={'token': self.token})

    def get_delivery_total(self):
        return sum([group.shipping_price for group in self.groups.all()],
                   Price(0, currency=settings.DEFAULT_CURRENCY))

    def send_confirmation_email(self):
        email = self.get_user_current_email()
        payment_url = build_absolute_uri(
            reverse('order:details', kwargs={'token': self.token}))
        context = {'payment_url': payment_url}

        emailit.api.send_mail(
                email, context, 'order/emails/confirm_email',
                from_email=settings.ORDER_FROM_EMAIL)

    def get_last_payment_status(self):
        last_payment = self.payments.last()
        if last_payment:
            return last_payment.status

    def get_last_payment_status_display(self):
        last_payment = self.payments.last()
        if last_payment:
            return last_payment.get_status_display()

    def is_pre_authorized(self):
        return self.payments.filter(status='preauth').exists()

    def create_history_entry(self, comment='', status=None, user=None):
        if not status:
            status = self.status
        self.history.create(status=status, comment=comment, user=user)

    def is_shipping_required(self):
        return any(group.is_shipping_required() for group in self.groups.all())

    @property
    def total(self):
        if self.total_net is not None:
            gross = self.total_net.net + self.total_tax.gross
            return Price(net=self.total_net.net, gross=gross,
                         currency=settings.DEFAULT_CURRENCY)

    @total.setter
    def total(self, price):
        self.total_net = price
        self.total_tax = Price(price.tax, currency=price.currency)

    def get_subtotal_without_voucher(self):
        if self.get_items():
            return super(Order, self).get_total()
        return Price(net=0, currency=settings.DEFAULT_CURRENCY)

    def get_total_shipping(self):
        costs = [group.shipping_price for group in self]
        if costs:
            return sum(costs[1:], costs[0])
        return Price(net=0, currency=settings.DEFAULT_CURRENCY)

    def can_cancel(self):
        return self.status not in {Status.CANCELLED, Status.SHIPPED}


class DeliveryGroup(models.Model, ItemSet):
    status = models.CharField(
        pgettext_lazy('Delivery group field', 'delivery status'),
        max_length=32, default=Status.NEW, choices=Status.CHOICES)
    order = models.ForeignKey(Order, related_name='groups', editable=False)
    shipping_price = PriceField(
        pgettext_lazy('Delivery group field', 'shipping price'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=4,
        default=0, editable=False)
    shipping_method_name = models.CharField(
        max_length=255, null=True, default=None, blank=True, editable=False)
    tracking_number = models.CharField(max_length=255, default='', blank=True)
    last_updated = models.DateTimeField(null=True, auto_now=True)

    def __str__(self):
        return pgettext_lazy(
            'Delivery group str', 'Shipment #%s') % self.pk

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __iter__(self):
        if self.id:
            return iter(self.items.all())
        return super(DeliveryGroup, self).__iter__()

    @property
    def shipping_required(self):
        return self.shipping_method_name is not None

    def change_status(self, status):
        self.status = status
        self.save()

    def get_total(self, **kwargs):
        subtotal = super(DeliveryGroup, self).get_total(**kwargs)
        return subtotal + self.shipping_price

    def add_items_from_partition(self, partition, discounts=None):
        for item_line in partition:
            product_variant = item_line.variant
            price = item_line.get_price_per_item(discounts)
            quantity = item_line.get_quantity()
            stock = product_variant.select_stockrecord(quantity)
            self.items.create(
                product=product_variant.product,
                quantity=quantity,
                unit_price_net=price.net,
                product_name=smart_text(product_variant),
                product_sku=product_variant.sku,
                unit_price_gross=price.gross,
                stock=stock,
                stock_location=stock.location.name if stock else None)
            if stock:
                # allocate quantity to avoid overselling
                Stock.objects.allocate_stock(stock, quantity)

    def get_total_quantity(self):
        return sum([item.get_quantity() for item in self])

    def is_shipping_required(self):
        return self.shipping_required

    def can_ship(self):
        return self.is_shipping_required() and self.status == 'new'

    def can_cancel(self):
        return self.status != Status.CANCELLED


class OrderedItemManager(models.Manager):

    def move_to_group(self, item, target_group, quantity):
        try:
            target_item = target_group.items.get(
                product=item.product, product_name=item.product_name,
                product_sku=item.product_sku)
        except ObjectDoesNotExist:
            target_group.items.create(
                delivery_group=target_group, product=item.product,
                product_name=item.product_name, product_sku=item.product_sku,
                quantity=quantity, unit_price_net=item.unit_price_net,
                stock=item.stock,
                unit_price_gross=item.unit_price_gross)
        else:
            target_item.quantity += quantity
            target_item.save()
        item.quantity -= quantity
        self.remove_empty_groups(item)

    def remove_empty_groups(self, item, force=False):
        source_group = item.delivery_group
        order = source_group.order
        if item.quantity:
            item.save()
        else:
            item.delete()
        if not source_group.get_total_quantity() or force:
            source_group.delete()
        if not order.get_items():
            order.change_status('cancelled')


@python_2_unicode_compatible
class OrderedItem(models.Model, ItemLine):
    delivery_group = models.ForeignKey(
        DeliveryGroup, related_name='items', editable=False)
    product = models.ForeignKey(
        Product, blank=True, null=True, related_name='+',
        on_delete=models.SET_NULL,
        verbose_name=pgettext_lazy('OrderedItem field', 'product'))
    product_name = models.CharField(
        pgettext_lazy('OrderedItem field', 'product name'), max_length=128)
    product_sku = models.CharField(pgettext_lazy('OrderedItem field', 'sku'),
                                   max_length=32)
    stock_location = models.CharField(
        pgettext_lazy('OrderedItem field', 'stock location'), max_length=100,
        default='')
    stock = models.ForeignKey('product.Stock', on_delete=models.SET_NULL,
                              null=True)
    quantity = models.IntegerField(
        pgettext_lazy('OrderedItem field', 'quantity'),
        validators=[MinValueValidator(0), MaxValueValidator(999)])
    unit_price_net = models.DecimalField(
        pgettext_lazy('OrderedItem field', 'unit price (net)'),
        max_digits=12, decimal_places=4)
    unit_price_gross = models.DecimalField(
        pgettext_lazy('OrderedItem field', 'unit price (gross)'),
        max_digits=12, decimal_places=4)

    objects = OrderedItemManager()

    def get_price_per_item(self, **kwargs):
        return Price(net=self.unit_price_net, gross=self.unit_price_gross,
                     currency=settings.DEFAULT_CURRENCY)

    def __str__(self):
        return self.product_name

    def get_quantity(self):
        return self.quantity

    def change_quantity(self, new_quantity):
        order = self.delivery_group.order
        self.quantity = new_quantity
        self.save()
        if not self.delivery_group.get_total_quantity():
            self.delivery_group.delete()
        if not order.get_items():
            order.change_status('cancelled')


class PaymentManager(models.Manager):

    def last(self):
        # using .all() here reuses data fetched by prefetch_related
        objects = list(self.all()[:1])
        if objects:
            return objects[0]


class Payment(BasePayment):
    order = models.ForeignKey(Order, related_name='payments')

    objects = PaymentManager()

    def get_failure_url(self):
        return build_absolute_uri(
            reverse('order:details', kwargs={'token': self.order.token}))

    def get_success_url(self):
        return build_absolute_uri(
            reverse('order:details', kwargs={'token': self.order.token}))

    def send_confirmation_email(self):
        email = self.order.get_user_current_email()
        order_url = build_absolute_uri(
            reverse('order:details', kwargs={'token': self.order.token}))
        context = {'order_url': order_url}
        emailit.api.send_mail(
            email, context, 'order/payment/emails/confirm_email',
            from_email=settings.ORDER_FROM_EMAIL)

    def get_purchased_items(self):
        items = [PurchasedItem(
            name=item.product_name, sku=item.product_sku,
            quantity=item.quantity,
            price=item.unit_price_gross.quantize(Decimal('0.01')),
            currency=settings.DEFAULT_CURRENCY)
            for item in self.order.get_items()]
        return items

    def get_total_price(self):
        net = self.total - self.tax
        return Price(net, gross=self.total, currency=self.currency)

    def get_captured_price(self):
        return Price(self.captured_amount, currency=self.currency)

    class Meta:
        ordering = ('-pk',)


@python_2_unicode_compatible
class OrderHistoryEntry(models.Model):
    date = models.DateTimeField(
        pgettext_lazy('Order field', 'last history change'),
        default=now, editable=False)
    order = models.ForeignKey(Order, related_name='history')
    status = models.CharField(
        pgettext_lazy('Order field', 'order status'),
        max_length=32, choices=Status.CHOICES)
    comment = models.CharField(max_length=100, default='', blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True)

    def __str__(self):
        return 'OrderHistoryEntry for Order #%d' % self.order.pk

    class Meta:
        ordering = ['date']


@python_2_unicode_compatible
class OrderNote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    date = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, related_name='notes')
    content = models.CharField(max_length=250)

    def __str__(self):
        return 'OrderNote for Order #%d' % self.order.pk
