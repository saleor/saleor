from __future__ import unicode_literals

from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.timezone import now
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from payments import PaymentStatus, PurchasedItem
from payments.models import BasePayment
from prices import Price, FixedDiscount
from satchless.item import ItemLine, ItemSet
from templated_email import send_templated_mail

from ..core.utils import build_absolute_uri
from ..discount.models import Voucher
from ..product.models import Product
from ..userprofile.models import Address
from ..search import index
from ..site.utils import get_site_name
from . import OrderStatus


class OrderManager(models.Manager):
    def recalculate_order(self, order):
        prices = [group.get_total() for group in order
                  if group.status != OrderStatus.CANCELLED]
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
        max_length=32, choices=OrderStatus.CHOICES, default=OrderStatus.NEW)
    created = models.DateTimeField(
        pgettext_lazy('Order field', 'created'),
        default=now, editable=False)
    last_status_change = models.DateTimeField(
        pgettext_lazy('Order field', 'last status change'),
        default=now, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name='orders',
        verbose_name=pgettext_lazy('Order field', 'user'))
    language_code = models.CharField(max_length=35, default=settings.LANGUAGE_CODE)
    tracking_client_id = models.CharField(
        pgettext_lazy('Order field', 'tracking client id'),
        max_length=36, blank=True, editable=False)
    billing_address = models.ForeignKey(
        Address, related_name='+', editable=False,
        verbose_name=pgettext_lazy('Order field', 'billing address'))
    shipping_address = models.ForeignKey(
        Address, related_name='+', editable=False, null=True,
        verbose_name=pgettext_lazy('Order field', 'shipping address'))
    user_email = models.EmailField(
        pgettext_lazy('Order field', 'user email'),
        blank=True, default='', editable=False)
    token = models.CharField(
        pgettext_lazy('Order field', 'token'), max_length=36, unique=True)
    total_net = PriceField(
        pgettext_lazy('Order field', 'total net'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)
    total_tax = PriceField(
        pgettext_lazy('Order field', 'total tax'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)
    voucher = models.ForeignKey(
        Voucher, null=True, related_name='+', on_delete=models.SET_NULL,
        verbose_name=pgettext_lazy('Order field', 'voucher'))
    discount_amount = PriceField(
        verbose_name=pgettext_lazy('Order field', 'discount amount'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)
    discount_name = models.CharField(
        verbose_name=pgettext_lazy('Order field', 'discount name'),
        max_length=255, default='', blank=True)

    objects = OrderManager()

    search_fields = [
        index.SearchField('id'),
        index.SearchField('get_user_current_email'),
        index.SearchField('_index_billing_phone'),
        index.SearchField('_index_shipping_phone')]

    class Meta:
        ordering = ('-last_status_change',)
        verbose_name = pgettext_lazy('Order model', 'Order')
        verbose_name_plural = pgettext_lazy('Order model', 'Orders')
        permissions = (
            ('view_order', 'Can view orders'),
            ('edit_order', 'Can edit orders'))

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
        total_paid = sum(
            [payment.total for payment in
             self.payments.filter(status=PaymentStatus.CONFIRMED)], Decimal())
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
        return sum(
            [group.shipping_price for group in self.groups.all()],
            Price(0, currency=settings.DEFAULT_CURRENCY))

    def send_confirmation_email(self):
        email = self.get_user_current_email()
        payment_url = build_absolute_uri(
            reverse('order:details', kwargs={'token': self.token}))
        context = {'payment_url': payment_url, 'site_name': get_site_name()}
        send_templated_mail(
            'order/confirm_order', from_email=settings.ORDER_FROM_EMAIL,
            recipient_list=[email], context=context)

    def get_last_payment_status(self):
        last_payment = self.payments.last()
        if last_payment:
            return last_payment.status

    def get_last_payment_status_display(self):
        last_payment = self.payments.last()
        if last_payment:
            return last_payment.get_status_display()

    def is_pre_authorized(self):
        return self.payments.filter(status=PaymentStatus.PREAUTH).exists()

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
        return self.status not in {OrderStatus.CANCELLED, OrderStatus.SHIPPED}


class DeliveryGroup(models.Model, ItemSet):
    """Represents a single shipment.

    A single order can consist of may delivery groups.
    """
    status = models.CharField(
        pgettext_lazy('Delivery group field', 'delivery status'),
        max_length=32, default=OrderStatus.NEW, choices=OrderStatus.CHOICES)
    order = models.ForeignKey(Order, related_name='groups', editable=False)
    shipping_price = PriceField(
        pgettext_lazy('Delivery group field', 'shipping price'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=4,
        default=0, editable=False)
    shipping_method_name = models.CharField(
        pgettext_lazy('Delivery group field', 'shipping method name'),
        max_length=255, null=True, default=None, blank=True, editable=False)
    tracking_number = models.CharField(
        pgettext_lazy('Delivery group field', 'tracking number'),
        max_length=255, default='', blank=True)
    last_updated = models.DateTimeField(
        pgettext_lazy('Delivery group field', 'last updated'),
        null=True, auto_now=True)

    class Meta:
        verbose_name = pgettext_lazy('Delivery group model', 'Delivery Group')
        verbose_name_plural = pgettext_lazy('Delivery group model', 'Delivery Groups')

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

    def get_total_quantity(self):
        return sum([item.get_quantity() for item in self])

    def is_shipping_required(self):
        return self.shipping_required

    def can_ship(self):
        return self.is_shipping_required() and self.status == OrderStatus.NEW

    def can_cancel(self):
        return self.status != OrderStatus.CANCELLED


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
            order.change_status(OrderStatus.CANCELLED)


@python_2_unicode_compatible
class OrderedItem(models.Model, ItemLine):
    delivery_group = models.ForeignKey(
        DeliveryGroup, related_name='items', editable=False,
        verbose_name=pgettext_lazy('Ordered item field', 'delivery group'))
    product = models.ForeignKey(
        Product, blank=True, null=True, related_name='+',
        on_delete=models.SET_NULL,
        verbose_name=pgettext_lazy('Ordered item field', 'product'))
    product_name = models.CharField(
        pgettext_lazy('Ordered item field', 'product name'), max_length=128)
    product_sku = models.CharField(
        pgettext_lazy('Ordered item field', 'sku'), max_length=32)
    stock_location = models.CharField(
        pgettext_lazy('OrderedItem field', 'stock location'), max_length=100,
        default='')
    stock = models.ForeignKey(
        'product.Stock', on_delete=models.SET_NULL, null=True,
        verbose_name=pgettext_lazy('Ordered item field', 'stock'))
    quantity = models.IntegerField(
        pgettext_lazy('Ordered item field', 'quantity'),
        validators=[MinValueValidator(0), MaxValueValidator(999)])
    unit_price_net = models.DecimalField(
        pgettext_lazy('Ordered item field', 'unit price (net)'),
        max_digits=12, decimal_places=4)
    unit_price_gross = models.DecimalField(
        pgettext_lazy('Ordered item field', 'unit price (gross)'),
        max_digits=12, decimal_places=4)

    objects = OrderedItemManager()

    class Meta:
        verbose_name = pgettext_lazy('Ordered item model', 'Ordered item')
        verbose_name_plural = pgettext_lazy('Ordered item model', 'Ordered items')

    def __str__(self):
        return self.product_name

    def get_price_per_item(self, **kwargs):
        return Price(net=self.unit_price_net, gross=self.unit_price_gross,
                     currency=settings.DEFAULT_CURRENCY)

    def get_quantity(self):
        return self.quantity

    def change_quantity(self, new_quantity):
        order = self.delivery_group.order
        self.quantity = new_quantity
        self.save()
        if not self.delivery_group.get_total_quantity():
            self.delivery_group.delete()
        if not order.get_items():
            order.change_status(OrderStatus.CANCELLED)


class PaymentManager(models.Manager):
    def last(self):
        # using .all() here reuses data fetched by prefetch_related
        objects = list(self.all()[:1])
        if objects:
            return objects[0]


class Payment(BasePayment):
    order = models.ForeignKey(
        Order, related_name='payments',
        verbose_name=pgettext_lazy('Payment field', 'order'))

    objects = PaymentManager()

    class Meta:
        ordering = ('-pk',)
        verbose_name = pgettext_lazy('Payment model', 'Payment')
        verbose_name_plural = pgettext_lazy('Payment model', 'Payments')

    def get_failure_url(self):
        return build_absolute_uri(
            reverse('order:details', kwargs={'token': self.order.token}))

    def get_success_url(self):
        return build_absolute_uri(
            reverse('order:create-password', kwargs={'token': self.order.token}))

    def send_confirmation_email(self):
        email = self.order.get_user_current_email()
        order_url = build_absolute_uri(
            reverse('order:details', kwargs={'token': self.order.token}))
        context = {'order_url': order_url, 'site_name': get_site_name()}
        send_templated_mail(
            'order/payment/confirm_payment', context=context,
            from_email=settings.ORDER_FROM_EMAIL, recipient_list=[email])

    def get_purchased_items(self):
        items = [
            PurchasedItem(
                name=item.product_name, sku=item.product_sku,
                quantity=item.quantity,
                price=item.unit_price_gross.quantize(Decimal('0.01')),
                currency=settings.DEFAULT_CURRENCY)
            for item in self.order.get_items()]

        voucher = self.order.voucher
        if voucher is not None:
            items.append(PurchasedItem(
                name=self.order.discount_name,
                sku='DISCOUNT',
                quantity=1,
                price=-self.order.discount_amount.net,
                currency=self.currency))
        return items

    def get_total_price(self):
        net = self.total - self.tax
        return Price(net, gross=self.total, currency=self.currency)

    def get_captured_price(self):
        return Price(self.captured_amount, currency=self.currency)


@python_2_unicode_compatible
class OrderHistoryEntry(models.Model):
    date = models.DateTimeField(
        pgettext_lazy('Order history entry field', 'last history change'),
        default=now, editable=False)
    order = models.ForeignKey(
        Order, related_name='history',
        verbose_name=pgettext_lazy('Order history entry field', 'order'))
    status = models.CharField(
        pgettext_lazy('Order history entry field', 'order status'),
        max_length=32, choices=OrderStatus.CHOICES)
    comment = models.CharField(
        pgettext_lazy('Order history entry field', 'comment'),
        max_length=100, default='', blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        verbose_name=pgettext_lazy('Order history entry field', 'user'))

    class Meta:
        ordering = ('date', )
        verbose_name = pgettext_lazy(
            'Order history entry model', 'Order history entry')
        verbose_name_plural = pgettext_lazy(
            'Order history entry model', 'Order history entries')

    def __str__(self):
        return pgettext_lazy(
            'Order history entry str',
            'OrderHistoryEntry for Order #%d') % self.order.pk


@python_2_unicode_compatible
class OrderNote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    date = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, related_name='notes')
    content = models.CharField(
        pgettext_lazy('Order note model', 'content'),
        max_length=250)

    class Meta:
        verbose_name = pgettext_lazy('Order note model', 'Order note')
        verbose_name_plural = pgettext_lazy('Order note model', 'Order notes')

    def __str__(self):
        return pgettext_lazy(
            'Order note str',
            'OrderNote for Order #%d' % self.order.pk)
