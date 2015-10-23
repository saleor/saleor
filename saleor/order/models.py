from __future__ import unicode_literals
from decimal import Decimal
from uuid import uuid4
import itertools

from django.forms.models import model_to_dict
from django.shortcuts import get_list_or_404
import emailit.api
from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.encoding import smart_text
from django.utils.timezone import now
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import pgettext_lazy
from django_prices.models import PriceField
from payments import PurchasedItem
from payments.models import BasePayment
from prices import Price
from satchless.item import ItemSet, ItemLine

from ..core.utils import build_absolute_uri
from ..product.models import Product, ProductVariant
from saleor.cart import CartLine
from ..userprofile.models import Address, User
from ..delivery import get_delivery


class OrderQuerySet(models.QuerySet):
    def with_items(self):
        return self.prefetch_related('groups', 'groups__items')

    def with_payments(self):
        return self.prefetch_related('payments')

    def with_user(self):
        return self.select_related('billing_address', 'shipping_address',
                                   'user')

    def with_all_related(self):
        return self.with_items().with_payments().with_user()


@python_2_unicode_compatible
class Order(models.Model, ItemSet):
    STATUS_CHOICES = (
        ('new', pgettext_lazy('Order status field value', 'Processing')),
        ('cancelled', pgettext_lazy('Order status field value',
                                    'Cancelled')),
        ('payment-pending', pgettext_lazy('Order status field value',
                                          'Waiting for payment')),
        ('fully-paid', pgettext_lazy('Order status field value',
                                     'Fully paid')),
        ('shipped', pgettext_lazy('Order status field value',
                                  'Shipped')))
    status = models.CharField(
        pgettext_lazy('Order field', 'order status'),
        max_length=32, choices=STATUS_CHOICES, default='new')
    created = models.DateTimeField(
        pgettext_lazy('Order field', 'created'),
        default=now, editable=False)
    last_status_change = models.DateTimeField(
        pgettext_lazy('Order field', 'last status change'),
        default=now, editable=False)
    user = models.ForeignKey(
        User, blank=True, null=True, related_name='orders',
        verbose_name=pgettext_lazy('Order field', 'user'))
    tracking_client_id = models.CharField(max_length=36, blank=True,
                                          editable=False)
    billing_address = models.ForeignKey(Address, related_name='+',
                                        editable=False)
    shipping_address = models.ForeignKey(Address, related_name='+',
                                         editable=False, null=True)
    shipping_method = models.CharField(
        pgettext_lazy('Order field', 'Delivery method'),
        max_length=255, blank=True)
    anonymous_user_email = models.EmailField(blank=True, default='',
                                             editable=False)
    token = models.CharField(
        pgettext_lazy('Order field', 'token'), max_length=36, unique=True)
    total = PriceField(
        pgettext_lazy('Order field', 'total'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12, decimal_places=2,
        blank=True, null=True)

    objects = OrderQuerySet.as_manager()

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
        return list(
            itertools.chain(
                *[delivery_group.items.all() for delivery_group in self]))

    def is_fully_paid(self):
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

    def __str__(self):
        return '#%d' % (self.id, )

    def get_total(self):
        try:
            return super(Order, self).get_total()
        except AttributeError:
            return Price(0, currency=settings.DEFAULT_CURRENCY)

    @property
    def billing_full_name(self):
        return '%s %s' % (self.billing_first_name, self.billing_last_name)

    def get_absolute_url(self):
        return reverse('order:details', kwargs={'token': self.token})

    def get_delivery_total(self):
        return sum([group.shipping_price for group in self.groups.all()],
                   Price(0, currency=settings.DEFAULT_CURRENCY))

    def send_confirmation_email(self):
        email = self.get_user_email()
        payment_url = build_absolute_uri(
            reverse('order:details', kwargs={'token': self.token}))
        context = {'payment_url': payment_url}

        emailit.api.send_mail(email, context, 'order/emails/confirm_email')

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


class DeliveryGroupManager(models.Manager):

    def duplicate_group(self, group):
        data = model_to_dict(group)
        data['id'] = None
        data['status'] = 'new'
        return group.order.groups.create(**data)


class DeliveryGroup(models.Model, ItemSet):
    STATUS_CHOICES = (
        ('new',
         pgettext_lazy('Delivery group status field value', 'Processing')),
        ('cancelled', pgettext_lazy('Delivery group status field value',
                                    'Cancelled')),
        ('shipped', pgettext_lazy('Delivery group status field value',
                                  'Shipped')))
    status = models.CharField(
        pgettext_lazy('Delivery group field', 'delivery status'),
        max_length=32, default='new', choices=STATUS_CHOICES)
    order = models.ForeignKey(Order, related_name='groups', editable=False)
    shipping_required = models.BooleanField(
        pgettext_lazy('Delivery group field', 'shipping required'),
        default=True)
    shipping_price = PriceField(
        pgettext_lazy('Delivery group field', 'shipping price'),
        currency=settings.DEFAULT_CURRENCY, max_digits=12,
        decimal_places=4,
        default=0,
        editable=False)
    last_updated = models.DateTimeField(null=True, auto_now=True)

    objects = DeliveryGroupManager()

    def __str__(self):
        return pgettext_lazy(
            'Delivery group str', 'Shipment #%s') % self.pk

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, list(self))

    def __iter__(self):
        if self.id:
            return iter(self.items.all())
        return super(DeliveryGroup, self).__iter__()

    def change_status(self, status):
        self.status = status
        self.save()

    def get_total(self, **kwargs):
        subtotal = super(DeliveryGroup, self).get_total(**kwargs)
        return subtotal + self.shipping_price

    def add_items_from_partition(self, partition):
        for item_line in partition:
            product_variant = item_line.product
            price = item_line.get_price_per_item()
            self.items.create(
                product=product_variant.product,
                quantity=item_line.get_quantity(),
                unit_price_net=price.net,
                product_name=smart_text(product_variant),
                product_sku=product_variant.sku,
                unit_price_gross=price.gross)

    def update_delivery_cost(self):
        if self.order.is_shipping_required():
            delivery = get_delivery(self.order.shipping_method)
            skus = [line.product_sku for line in self]
            variants = get_list_or_404(
                ProductVariant.objects.select_related('product'), sku__in=skus)
            variants_map = {variant.sku: variant for variant in variants}
            items = []
            for line in self:
                data = {'product': variants_map[line.product_sku],
                        'quantity': line.get_quantity()}
                items.append(CartLine(**data))
            self.shipping_price = delivery.get_delivery_total(items)
            self.save()

    def get_total_quantity(self):
        return sum([item.get_quantity() for item in self])

    def is_shipping_required(self):
        return self.shipping_required

    def can_ship(self):
        return self.is_shipping_required() and self.status == 'new'


class OrderedItemManager(models.Manager):

    def move_to_group(self, item, target_group, quantity):
        source_group = item.delivery_group
        order = target_group.order
        try:
            target_item = target_group.items.get(
                product=item.product, product_name=item.product_name,
                product_sku=item.product_sku)
        except ObjectDoesNotExist:
            target_group.items.create(
                delivery_group=target_group, product=item.product,
                product_name=item.product_name, product_sku=item.product_sku,
                quantity=quantity, unit_price_net=item.unit_price_net,
                unit_price_gross=item.unit_price_gross)
        else:
            target_item.quantity += quantity
            target_item.save()
        item.quantity -= quantity
        if item.quantity:
            item.save()
        else:
            item.delete()
        if source_group.get_total_quantity():
            source_group.update_delivery_cost()
        else:
            source_group.delete()
        target_group.update_delivery_cost()
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
        self.delivery_group.update_delivery_cost()
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
        email = self.order.get_user_email()
        order_url = build_absolute_uri(
            reverse('order:details', kwargs={'token': self.order.token}))
        context = {'order_url': order_url}
        emailit.api.send_mail(
            email, context, 'order/payment/emails/confirm_email')

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
        max_length=32, choices=Order.STATUS_CHOICES)
    comment = models.CharField(max_length=100, default='', blank=True)
    user = models.ForeignKey(User, blank=True, null=True)

    def __str__(self):
        return 'OrderHistoryEntry for Order #%d' % self.order.pk

    class Meta:
        ordering = ['date']


@python_2_unicode_compatible
class OrderNote(models.Model):
    user = models.ForeignKey(User)
    date = models.DateTimeField(auto_now_add=True)
    order = models.ForeignKey(Order, related_name='notes')
    content = models.CharField(max_length=250)

    def __str__(self):
        return 'OrderNote for Order #%d' % self.order.pk
