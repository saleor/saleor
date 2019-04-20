from decimal import Decimal
from operator import attrgetter
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import F, Max, Sum
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import pgettext_lazy
from django_measurement.models import MeasurementField
from django_prices.models import MoneyField, TaxedMoneyField
from measurement.measures import Weight
from prices import Money

from ..account.models import Address
from ..core.utils.json_serializer import CustomJsonEncoder
from ..core.utils.taxes import ZERO_TAXED_MONEY, zero_money
from ..core.weight import WeightUnits, zero_weight
from ..discount.models import Voucher
from ..payment import ChargeStatus, TransactionKind
from ..shipping.models import ShippingMethod
from . import FulfillmentStatus, OrderEvents, OrderStatus, display_order_event


class OrderQueryset(models.QuerySet):
    def confirmed(self):
        """Return non-draft orders."""
        return self.exclude(status=OrderStatus.DRAFT)

    def drafts(self):
        """Return draft orders."""
        return self.filter(status=OrderStatus.DRAFT)

    def ready_to_fulfill(self):
        """Return orders that can be fulfilled.

        Orders ready to fulfill are fully paid but unfulfilled (or partially
        fulfilled).
        """
        statuses = {OrderStatus.UNFULFILLED, OrderStatus.PARTIALLY_FULFILLED}
        qs = self.filter(status__in=statuses, payments__is_active=True)
        qs = qs.annotate(amount_paid=Sum('payments__captured_amount'))
        return qs.filter(total_gross__lte=F('amount_paid'))

    def ready_to_capture(self):
        """Return orders with payments to capture.

        Orders ready to capture are those which are not draft or canceled and
        have a preauthorized payment. The preauthorized payment can not
        already be partially or fully captured.
        """
        qs = self.filter(
            payments__is_active=True,
            payments__charge_status=ChargeStatus.NOT_CHARGED)
        qs = qs.exclude(status={OrderStatus.DRAFT, OrderStatus.CANCELED})
        return qs.distinct()


class Order(models.Model):
    created = models.DateTimeField(
        default=now, editable=False)
    status = models.CharField(
        max_length=32, default=OrderStatus.UNFULFILLED,
        choices=OrderStatus.CHOICES)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, related_name='orders',
        on_delete=models.SET_NULL)
    language_code = models.CharField(
        max_length=35, default=settings.LANGUAGE_CODE)
    tracking_client_id = models.CharField(
        max_length=36, blank=True, editable=False)
    billing_address = models.ForeignKey(
        Address, related_name='+', editable=False, null=True,
        on_delete=models.SET_NULL)
    shipping_address = models.ForeignKey(
        Address, related_name='+', editable=False, null=True,
        on_delete=models.SET_NULL)
    user_email = models.EmailField(blank=True, default='')
    shipping_method = models.ForeignKey(
        ShippingMethod, blank=True, null=True, related_name='orders',
        on_delete=models.SET_NULL)
    shipping_price_net = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0, editable=False)
    shipping_price_gross = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0, editable=False)
    shipping_price = TaxedMoneyField(
        net_field='shipping_price_net', gross_field='shipping_price_gross')
    shipping_method_name = models.CharField(
        max_length=255, null=True, default=None, blank=True, editable=False)
    token = models.CharField(max_length=36, unique=True, blank=True)
    # Token of a checkout instance that this order was created from
    checkout_token = models.CharField(max_length=36, blank=True)
    total_net = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=zero_money)
    total_gross = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=zero_money)
    total = TaxedMoneyField(net_field='total_net', gross_field='total_gross')
    voucher = models.ForeignKey(
        Voucher, blank=True, null=True, related_name='+',
        on_delete=models.SET_NULL)
    discount_amount = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=zero_money)
    discount_name = models.CharField(max_length=255, default='', blank=True)
    translated_discount_name = models.CharField(
        max_length=255, default='', blank=True)
    display_gross_prices = models.BooleanField(default=True)
    customer_note = models.TextField(blank=True, default='')
    weight = MeasurementField(
        measurement=Weight, unit_choices=WeightUnits.CHOICES,
        default=zero_weight)
    objects = OrderQueryset.as_manager()

    class Meta:
        ordering = ('-pk', )
        permissions = ((
            'manage_orders',
            pgettext_lazy('Permission description', 'Manage orders.')),)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        return super().save(*args, **kwargs)

    def is_fully_paid(self):
        total_paid = self._total_paid()
        return total_paid.gross >= self.total.gross

    def is_partly_paid(self):
        total_paid = self._total_paid()
        return total_paid.gross.amount > 0

    def get_user_current_email(self):
        return self.user.email if self.user else self.user_email

    def _total_paid(self):
        # Get total paid amount from partially charged,
        # fully charged and partially refunded payments
        payments = self.payments.filter(
            charge_status__in=[
                ChargeStatus.PARTIALLY_CHARGED,
                ChargeStatus.FULLY_CHARGED,
                ChargeStatus.PARTIALLY_REFUNDED])
        total_captured = [
            payment.get_captured_amount() for payment in payments]
        total_paid = sum(total_captured, ZERO_TAXED_MONEY)
        return total_paid

    def _index_billing_phone(self):
        return self.billing_address.phone

    def _index_shipping_phone(self):
        return self.shipping_address.phone

    def __iter__(self):
        return iter(self.lines.all())

    def __repr__(self):
        return '<Order #%r>' % (self.id,)

    def __str__(self):
        return '#%d' % (self.id,)

    def get_absolute_url(self):
        return reverse('order:details', kwargs={'token': self.token})

    def get_last_payment(self):
        return max(self.payments.all(), default=None, key=attrgetter('pk'))

    def get_payment_status(self):
        last_payment = self.get_last_payment()
        if last_payment:
            return last_payment.charge_status
        return ChargeStatus.NOT_CHARGED

    def get_payment_status_display(self):
        last_payment = self.get_last_payment()
        if last_payment:
            return last_payment.get_charge_status_display()
        return dict(ChargeStatus.CHOICES).get(ChargeStatus.NOT_CHARGED)

    def is_pre_authorized(self):
        return self.payments.filter(
            is_active=True,
            transactions__kind=TransactionKind.AUTH).filter(
                transactions__is_success=True).exists()

    @property
    def quantity_fulfilled(self):
        return sum([line.quantity_fulfilled for line in self])

    def is_shipping_required(self):
        return any(line.is_shipping_required for line in self)

    def get_subtotal(self):
        subtotal_iterator = (line.get_total() for line in self)
        return sum(subtotal_iterator, ZERO_TAXED_MONEY)

    def get_total_quantity(self):
        return sum([line.quantity for line in self])

    def is_draft(self):
        return self.status == OrderStatus.DRAFT

    def is_open(self):
        statuses = {OrderStatus.UNFULFILLED, OrderStatus.PARTIALLY_FULFILLED}
        return self.status in statuses

    def can_cancel(self):
        return self.status not in {OrderStatus.CANCELED, OrderStatus.DRAFT}

    def can_capture(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        order_status_ok = self.status not in {
            OrderStatus.DRAFT, OrderStatus.CANCELED}
        return payment.can_capture() and order_status_ok

    def can_charge(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        order_status_ok = self.status not in {
            OrderStatus.DRAFT, OrderStatus.CANCELED}
        return payment.can_charge() and order_status_ok

    def can_void(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        return payment.can_void()

    def can_refund(self, payment=None):
        if not payment:
            payment = self.get_last_payment()
        if not payment:
            return False
        return payment.can_refund()

    def can_mark_as_paid(self):
        return len(self.payments.all()) == 0

    @property
    def total_authorized(self):
        payment = self.get_last_payment()
        if payment:
            return payment.get_authorized_amount()
        return zero_money()

    @property
    def total_captured(self):
        payment = self.get_last_payment()
        if payment and payment.charge_status in (
                ChargeStatus.PARTIALLY_CHARGED,
                ChargeStatus.FULLY_CHARGED,
                ChargeStatus.PARTIALLY_REFUNDED):
            return Money(payment.captured_amount, payment.currency)
        return zero_money()

    @property
    def total_balance(self):
        return self.total_captured - self.total.gross

    def get_total_weight(self):
        return self.weight


class OrderLineQueryset(models.QuerySet):
    def digital(self):
        """Returns lines with digital products"""
        for line in self.all():
            if line.is_digital:
                yield line

    def physical(self):
        """Returns lines with physical products"""
        for line in self.all():
            if not line.is_digital:
                yield line


class OrderLine(models.Model):
    order = models.ForeignKey(
        Order, related_name='lines', editable=False, on_delete=models.CASCADE)
    variant = models.ForeignKey(
        'product.ProductVariant', related_name='order_lines',
        on_delete=models.SET_NULL, blank=True, null=True)
    # max_length is as produced by ProductVariant's display_product method
    product_name = models.CharField(max_length=386)
    translated_product_name = models.CharField(
        max_length=386, default='', blank=True)
    product_sku = models.CharField(max_length=32)
    is_shipping_required = models.BooleanField()
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    quantity_fulfilled = models.IntegerField(
        validators=[MinValueValidator(0)], default=0)
    unit_price_net = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES)
    unit_price_gross = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES)
    unit_price = TaxedMoneyField(
        net_field='unit_price_net', gross_field='unit_price_gross')
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal('0.0'))

    objects = OrderLineQueryset.as_manager()

    class Meta:
        ordering = ('pk', )

    def __str__(self):
        return self.product_name

    def get_total(self):
        return self.unit_price * self.quantity

    @property
    def quantity_unfulfilled(self):
        return self.quantity - self.quantity_fulfilled

    @property
    def is_digital(self) -> bool:
        """Return true if product variant is a digital type and has assigned
        digital content"""
        is_digital = self.variant.is_digital()
        has_digital = hasattr(self.variant, 'digital_content')
        return is_digital and has_digital


class Fulfillment(models.Model):
    fulfillment_order = models.PositiveIntegerField(editable=False)
    order = models.ForeignKey(
        Order, related_name='fulfillments', editable=False,
        on_delete=models.CASCADE)
    status = models.CharField(
        max_length=32, default=FulfillmentStatus.FULFILLED,
        choices=FulfillmentStatus.CHOICES)
    tracking_number = models.CharField(max_length=255, default='', blank=True)
    shipping_date = models.DateTimeField(default=now, editable=False)

    def __str__(self):
        return pgettext_lazy(
            'Fulfillment str', 'Fulfillment #%s') % (self.composed_id,)

    def __iter__(self):
        return iter(self.lines.all())

    def save(self, *args, **kwargs):
        """Assign an auto incremented value as a fulfillment order."""
        if not self.pk:
            groups = self.order.fulfillments.all()
            existing_max = groups.aggregate(Max('fulfillment_order'))
            existing_max = existing_max.get('fulfillment_order__max')
            self.fulfillment_order = (
                existing_max + 1 if existing_max is not None else 1)
        return super().save(*args, **kwargs)

    @property
    def composed_id(self):
        return '%s-%s' % (self.order.id, self.fulfillment_order)

    def can_edit(self):
        return self.status != FulfillmentStatus.CANCELED

    def get_total_quantity(self):
        return sum([line.quantity for line in self])


class FulfillmentLine(models.Model):
    order_line = models.ForeignKey(
        OrderLine, related_name='+', on_delete=models.CASCADE)
    fulfillment = models.ForeignKey(
        Fulfillment, related_name='lines', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class OrderEvent(models.Model):
    """Model used to store events that happened during the order lifecycle.

        Args:
            parameters: Values needed to display the event on the storefront
            type: Type of an order
    """
    date = models.DateTimeField(default=now, editable=False)
    type = models.CharField(
        max_length=255,
        choices=((event.name, event.value) for event in OrderEvents))
    order = models.ForeignKey(
        Order, related_name='events', on_delete=models.CASCADE)
    parameters = JSONField(
        blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.SET_NULL, related_name='+')

    class Meta:
        ordering = ('date', )

    def __repr__(self):
        return 'OrderEvent(type=%r, user=%r)' % (self.type, self.user)

    def get_event_display(self):
        return display_order_event(self)
