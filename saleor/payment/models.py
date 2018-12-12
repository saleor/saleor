from decimal import Decimal
from operator import attrgetter

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django_prices.models import MoneyField
from prices import Money

from . import (
    ChargeStatus, CustomPaymentChoices, TransactionError, TransactionKind)
from ..checkout.models import Cart
from ..core.utils.taxes import zero_money
from ..order.models import Order


class Payment(models.Model):
    """Represents transactable payment information
    such as credit card details, gift card information or a customer's
    authorization to charge their PayPal account.

    All payment process related pieces of information are stored
    at the gateway level, we are operating on the reusable token
    which is a unique identifier of the customer for given gateway.

    Several payment methods can be used within a single order.
    """
    # FIXME we should provide an option to store the card for later usage
    # FIXME probably we should have pending status for 3d secure
    gateway = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    #: Creation date and time
    created = models.DateTimeField(auto_now_add=True)
    #: Date and time of last modification
    modified = models.DateTimeField(auto_now=True)
    charge_status = models.CharField(
        max_length=15,
        choices=ChargeStatus.CHOICES,
        default=ChargeStatus.NOT_CHARGED)

    billing_first_name = models.CharField(max_length=256, blank=True)
    billing_last_name = models.CharField(max_length=256, blank=True)
    billing_company_name = models.CharField(max_length=256, blank=True)
    billing_address_1 = models.CharField(max_length=256, blank=True)
    billing_address_2 = models.CharField(max_length=256, blank=True)
    billing_city = models.CharField(max_length=256, blank=True)
    billing_city_area = models.CharField(max_length=128, blank=True)
    billing_postal_code = models.CharField(max_length=256, blank=True)
    billing_country_code = models.CharField(max_length=2, blank=True)
    billing_country_area = models.CharField(max_length=256, blank=True)
    billing_email = models.EmailField(blank=True)
    customer_ip_address = models.GenericIPAddressField(blank=True, null=True)
    extra_data = models.TextField(blank=True, default='')
    token = models.CharField(max_length=128, blank=True, default='')

    #: Currency code (might be gateway-specific)
    # FIXME: add ISO4217 validator?
    currency = models.CharField(max_length=10)
    #: Total amount (gross)
    total = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal('0.0'))
    captured_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal('0.0'))

    checkout = models.ForeignKey(
        Cart, null=True, related_name='payments', on_delete=models.SET_NULL)
    order = models.ForeignKey(
        Order, null=True, related_name='payments', on_delete=models.PROTECT)

    # Credit Card data, if applicable
    cc_first_digits = models.CharField(max_length=6, blank=True, default='')
    cc_last_digits = models.CharField(max_length=4, blank=True, default='')
    cc_brand = models.CharField(max_length=40, blank=True, default='')
    cc_exp_month = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)],
        null=True, blank=True)
    # exp year should be in 4 digits format
    cc_exp_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1000)], null=True, blank=True)

    class Meta:
        ordering = ['pk']

    def __repr__(self):
        return 'Payment(gateway=%s, is_active=%s, created=%s, charge_status=%s)' % (
            self.gateway, self.is_active, self.created, self.charge_status)

    def get_last_transaction(self):
        return max(self.transactions.all(), default=None, key=attrgetter('pk'))

    def get_total(self):
        return Money(self.total, self.currency or settings.DEFAULT_CURRENCY)

    def get_authorized_amount(self):
        money = zero_money()

        # There is no authorized amount anymore when capture is succeeded
        # since capture can only be made once, even it is a partial capture
        if self.transactions.filter(
                kind=TransactionKind.CAPTURE, is_success=True).exists():
            return money

        # Calculate authorized amount from all succeeded auth transactions
        for transaction in self.transactions.filter(
                kind=TransactionKind.AUTH, is_success=True).all():
            money += Money(
                transaction.amount, self.currency or settings.DEFAULT_CURRENCY)

        # The authorized amount should exclude the already captured amount
        for transaction in self.transactions.filter(
                kind=TransactionKind.CAPTURE, is_success=True).all():
            money -= Money(
                transaction.amount, self.currency or settings.DEFAULT_CURRENCY)

        return money

    def get_captured_amount(self):
        return Money(
            self.captured_amount, self.currency or settings.DEFAULT_CURRENCY)

    def get_charge_amount(self):
        """Retrieve the maximum capture possible."""
        return self.total - self.captured_amount

    def authorize(self, payment_token):
        from . import utils
        return utils.gateway_authorize(
            payment=self, payment_token=payment_token)

    def charge(self, payment_token, amount=None):
        from . import utils
        if amount is None:
            amount = self.get_charge_amount()
        return utils.gateway_charge(
            payment=self, payment_token=payment_token, amount=amount)

    def void(self):
        from . import utils
        return utils.gateway_void(payment=self)

    def capture(self, amount=None):
        from . import utils
        if amount is None:
            amount = self.get_charge_amount()
        return utils.gateway_capture(payment=self, amount=amount)

    def refund(self, amount=None):
        from . import utils
        if amount is None:
            # If no amount is specified, refund the maximum possible
            amount = self.captured_amount
        return utils.gateway_refund(payment=self, amount=amount)

    def can_authorize(self):
        return (
            self.is_active and self.charge_status == ChargeStatus.NOT_CHARGED)

    def can_capture(self):
        not_charged = self.charge_status == ChargeStatus.NOT_CHARGED
        is_authorized = self.transactions.filter(
            kind=TransactionKind.AUTH, is_success=True).exists()
        return self.is_active and is_authorized and not_charged

    def can_charge(self):
        not_charged = (self.charge_status == ChargeStatus.NOT_CHARGED)
        not_fully_charged = (
            self.charge_status == ChargeStatus.CHARGED
            and self.get_total() > self.get_captured_amount())
        return self.is_active and (not_charged or not_fully_charged)

    def can_void(self):
        is_authorized = self.transactions.filter(
            kind=TransactionKind.AUTH, is_success=True).exists()
        return (
            self.is_active
            and self.charge_status == ChargeStatus.NOT_CHARGED
            and is_authorized)

    def can_refund(self):
        return (
            self.is_active and self.charge_status == ChargeStatus.CHARGED
            and self.gateway != CustomPaymentChoices.MANUAL)


class Transaction(models.Model):
    """Transaction represent attempts to transfer money between your store
    and your customers, with a chosen payment method.
    """
    created = models.DateTimeField(auto_now_add=True, editable=False)
    payment = models.ForeignKey(
        Payment, related_name='transactions', on_delete=models.PROTECT)
    token = models.CharField(max_length=128, blank=True, default='')
    kind = models.CharField(max_length=10, choices=TransactionKind.CHOICES)
    # FIXME probably we should have error/pending/success status instead of
    # a bool, eg for payments with 3d secure
    is_success = models.BooleanField(default=False)
    #: Currency code (may be gateway-specific)
    # FIXME: ISO4217 validator?
    currency = models.CharField(max_length=10)
    #: Total amount (gross)
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal('0.0'))
    # Unified error code across all payment gateways
    error = models.CharField(
        choices=[(tag, tag.value) for tag in TransactionError],
        max_length=256, null=True)
    gateway_response = JSONField()

    def __repr__(self):
        return 'Transaction(type=%s, is_success=%s, created=%s)' % (
            self.kind, self.is_success, self.created)

    def get_amount(self):
        return Money(self.amount, self.currency or settings.DEFAULT_CURRENCY)
