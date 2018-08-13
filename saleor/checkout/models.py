"""Cart-related ORM models."""
from decimal import Decimal
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.encoding import smart_str
from django_prices.models import MoneyField
from jsonfield import JSONField
from measurement.measures import Weight
from prices import Money

from ..account.models import Address
from ..core.utils.taxes import ZERO_TAXED_MONEY
from ..order.models import Order
from ..shipping.models import ShippingMethod

CENTS = Decimal('0.01')


class CartQueryset(models.QuerySet):
    """A specialized queryset for dealing with carts."""

    def for_display(self):
        """Annotate the queryset for display purposes.

        Prefetches additional data from the database to avoid the n+1 queries
        problem.
        """
        return self.prefetch_related(
            'lines__variant__translations',
            'lines__variant__product__translations',
            'lines__variant__product__images',
            'lines__variant__product__product_type__product_attributes__values'
        )  # noqa


class Cart(models.Model):
    """A shopping cart."""

    created = models.DateTimeField(auto_now_add=True)
    last_change = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name='carts',
        on_delete=models.CASCADE)
    email = models.EmailField(blank=True, default='')
    token = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    quantity = models.PositiveIntegerField(default=0)
    billing_address = models.ForeignKey(
        Address,
        related_name='+',
        editable=False,
        null=True,
        on_delete=models.SET_NULL)
    shipping_address = models.ForeignKey(
        Address,
        related_name='+',
        editable=False,
        null=True,
        on_delete=models.SET_NULL)
    shipping_method = models.ForeignKey(
        ShippingMethod, blank=True, null=True, related_name='carts',
        on_delete=models.SET_NULL)
    note = models.TextField(blank=True, default='')
    discount_amount = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=12,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0)
    discount_name = models.CharField(max_length=255, blank=True, null=True)
    translated_discount_name = models.CharField(
        max_length=255, blank=True, null=True)
    voucher_code = models.CharField(max_length=12, blank=True, null=True)

    objects = CartQueryset.as_manager()

    class Meta:
        ordering = ('-last_change', )

    def __repr__(self):
        return 'Cart(quantity=%s)' % (self.quantity, )

    def __iter__(self):
        return iter(self.lines.all())

    def __len__(self):
        return self.lines.count()

    def is_shipping_required(self):
        """Return `True` if any of the lines requires shipping."""
        return any(line.is_shipping_required() for line in self)

    def get_shipping_price(self, taxes):
        return (
            self.shipping_method.get_total(taxes)
            if self.shipping_method and self.is_shipping_required()
            else ZERO_TAXED_MONEY)

    def get_subtotal(self, discounts=None, taxes=None):
        """Return the total cost of the cart prior to shipping."""
        subtotals = (line.get_total(discounts, taxes) for line in self)
        return sum(subtotals, ZERO_TAXED_MONEY)

    def get_total(self, discounts=None, taxes=None):
        """Return the total cost of the cart."""
        return (
            self.get_subtotal(discounts, taxes)
            + self.get_shipping_price(taxes) - self.discount_amount)

    def get_total_weight(self):
        # Cannot use `sum` as it parses an empty Weight to an int
        weights = Weight(kg=0)
        for line in self:
            weights += line.variant.get_weight() * line.quantity
        return weights

    def get_line(self, variant):
        """Return a line matching the given variant and data if any."""
        matching_lines = (line for line in self if line.variant == variant)
        return next(matching_lines, None)


class CartLine(models.Model):
    """A single cart line.

    Multiple lines in the same cart can refer to the same product variant if
    their `data` field is different.
    """

    cart = models.ForeignKey(
        Cart, related_name='lines', on_delete=models.CASCADE)
    variant = models.ForeignKey(
        'product.ProductVariant', related_name='+', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    data = JSONField(blank=True, default=dict)

    class Meta:
        unique_together = ('cart', 'variant', 'data')

    def __str__(self):
        return smart_str(self.variant)

    def __eq__(self, other):
        if not isinstance(other, CartLine):
            return NotImplemented

        return (
            self.variant == other.variant and self.quantity == other.quantity)

    def __ne__(self, other):
        return not self == other  # pragma: no cover

    def __repr__(self):
        return 'CartLine(variant=%r, quantity=%r)' % (
            self.variant, self.quantity)

    def __getstate__(self):
        return self.variant, self.quantity

    def __setstate__(self, data):
        self.variant, self.quantity = data

    def get_total(self, discounts=None, taxes=None):
        """Return the total price of this line."""
        amount = self.quantity * self.variant.get_price(discounts, taxes)
        return amount.quantize(CENTS)

    def is_shipping_required(self):
        """Return `True` if the related product variant requires shipping."""
        return self.variant.is_shipping_required()


class TransactionType:
    AUTH = 'auth'
    CHARGE = 'charge'
    VOID = 'void'
    REFUND = 'refund'

    CHOICES = [(AUTH, pgettext_lazy('transaction type', 'Authorization')),
               (CHARGE, pgettext_lazy('transaction type', 'Charge')),
               (REFUND, pgettext_lazy('transaction type', 'Refund')),
               (VOID, pgettext_lazy('transaction type', 'Void'))]


class PaymentMethodChargeStatus:
    CHARGED = 'charged'
    NOT_CHARGED = 'not-charged'
    FULLY_REFUNDED = 'fully-refunded'

    CHOICES = [
        (CHARGED, pgettext_lazy('payment method status', 'Charged')),
        (NOT_CHARGED, pgettext_lazy('payment method status', 'Not charged')), (
            FULLY_REFUNDED,
            pgettext_lazy('payment method status', 'Fully refunded'))]


class PaymentMethod(models.Model):
    variant = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    #: Creation date and time
    created = models.DateTimeField(auto_now_add=True)
    #: Date and time of last modification
    modified = models.DateTimeField(auto_now=True)
    charge_status = models.CharField(
        max_length=15,
        choices=PaymentMethodChargeStatus.CHOICES,
        default=PaymentMethodChargeStatus.NOT_CHARGED)
    billing_first_name = models.CharField(max_length=256, blank=True)
    billing_last_name = models.CharField(max_length=256, blank=True)
    billing_address_1 = models.CharField(max_length=256, blank=True)
    billing_address_2 = models.CharField(max_length=256, blank=True)
    billing_city = models.CharField(max_length=256, blank=True)
    billing_postcode = models.CharField(max_length=256, blank=True)
    billing_country_code = models.CharField(max_length=2, blank=True)
    billing_country_area = models.CharField(max_length=256, blank=True)
    billing_email = models.EmailField(blank=True)
    customer_ip_address = models.GenericIPAddressField(blank=True, null=True)
    extra_data = models.TextField(blank=True, default='')
    token = models.CharField(max_length=36, blank=True, default='')

    total = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')
    currency = models.CharField(max_length=10)
    captured_amount = models.DecimalField(
        max_digits=9, decimal_places=2, default='0.0')
    tax = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')

    checkout = models.ForeignKey(
        Cart,
        null=True,
        related_name='payment_methods',
        on_delete=models.SET_NULL)
    order = models.ForeignKey(
        Order,
        null=True,
        related_name='payment_methods',
        on_delete=models.CASCADE)

    def _get_money(self, amount):
        return Money(amount=amount, currency=self.currency)

    def get_total(self):
        return self._get_money(self.total)

    def get_captured_money(self):
        return self._get_money(self.captured_amount)

    def get_tax_money(self):
        return self._get_money(self.tax)

    def authorize(self):
        # Check if payment method is active and create Transaction with AUTH type
        pass

    def void(self):
        # Check if payment method is active and create Transaction with VOID type
        pass

    def charge(self, amount=None):
        # Check if payment method is active and create Transaction with CHARGE type
        pass

    def refund(self, amount=None):
        # Check if payment method is active and create Transaction with REFUND type
        pass


class Transaction(models.Model):
    payment_method = models.ForeignKey(
        PaymentMethod, related_name='transactions', on_delete=models.CASCADE)
    token = models.CharField(max_length=64, blank=True, default='')
    transaction_type = models.CharField(
        max_length=10, choices=TransactionType.CHOICES)
    is_success = models.BooleanField(default=False)

    total = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')
    currency = models.CharField(max_length=10)
    captured_amount = models.DecimalField(
        max_digits=9, decimal_places=2, default='0.0')
    tax = models.DecimalField(max_digits=9, decimal_places=2, default='0.0')

    gateway_response = JSONField()

    def _get_money(self, amount):
        return Money(amount=amount, currency=self.currency)

    def get_total(self):
        return self._get_money(self.total)

    def get_captured_money(self):
        return self._get_money(self.captured_amount)

    def get_tax_money(self):
        return self._get_money(self.tax)
