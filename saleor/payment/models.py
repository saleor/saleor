from decimal import Decimal
from operator import attrgetter

from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django_prices.models import MoneyField
from prices import Money

from . import ChargeStatus, TransactionType
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
    #FIXME we should provide an option to store the card for later usage
    variant = models.CharField(max_length=255)
    # FIXME probably we should have error/pending/active status instead of
    # a bool
    is_active = models.BooleanField(default=True)
    #: Creation date and time
    created = models.DateTimeField(auto_now_add=True)
    #: Date and time of last modification
    modified = models.DateTimeField(auto_now=True)
    charge_status = models.CharField(
        max_length=15,
        choices=ChargeStatus.CHOICES,
        default=ChargeStatus.NOT_CHARGED)

    # FIXME maybe assign it as a separate Address instance?
    billing_first_name = models.CharField(max_length=256, blank=True)
    billing_last_name = models.CharField(max_length=256, blank=True)
    billing_company_name = models.CharField(max_length=256, blank=True)
    billing_address_1 = models.CharField(max_length=256, blank=True)
    billing_address_2 = models.CharField(max_length=256, blank=True)
    billing_city = models.CharField(max_length=256, blank=True)
    billing_postal_code = models.CharField(max_length=256, blank=True)
    billing_country_code = models.CharField(max_length=2, blank=True)
    billing_country_area = models.CharField(max_length=256, blank=True)
    billing_email = models.EmailField(blank=True)
    customer_ip_address = models.GenericIPAddressField(blank=True, null=True)
    extra_data = models.TextField(blank=True, default='')
    token = models.CharField(max_length=36, blank=True, default='')

    #: Currency code (may be provider-specific)
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

    def __repr__(self):
        return 'Payment(variant=%s, is_active=%s, created=%s, charge_status=%s)' % (
            self.variant, self.is_active, self.created, self.charge_status)

    def __iter__(self):
        return iter(self.transactions.all())

    def get_total(self):
        return Money(self.total, self.currency or settings.DEFAULT_CURRENCY)

    def get_captured_amount(self):
        return Money(
            self.captured_amount, self.currency or settings.DEFAULT_CURRENCY)

    def get_last_transaction(self):
        return max(self.transactions.all(), default=None, key=attrgetter('pk'))

    def get_auth_transaction(self):
        txn = self.transactions.get(
            transaction_type=TransactionType.AUTH, is_success=True)
        return txn

    def authorize(self, transaction_token):
        from . import utils
        return utils.gateway_authorize(
            payment=self, transaction_token=transaction_token)

    def void(self):
        from . import utils
        return utils.gateway_void(payment=self)

    def capture(self, amount=None):
        from . import utils
        if amount is None:
            amount = self.total
        return utils.gateway_capture(payment=self, amount=amount)

    def refund(self, amount=None):
        from . import utils
        if amount is None:
            amount = self.total
        return utils.gateway_refund(payment=self, amount=amount)


class Transaction(models.Model):
    """Transactions represent attempts to transfer money between your store
    and your customers, with a chosen payment method.
    """
    created = models.DateTimeField(auto_now_add=True, editable=False)
    payment = models.ForeignKey(
        Payment, related_name='transactions', on_delete=models.PROTECT)
    token = models.CharField(max_length=64, blank=True, default='')
    transaction_type = models.CharField(
        max_length=10, choices=TransactionType.CHOICES)
    # FIXME probably we should have error/pending/success status instead of
    # a bool, eg for payments with 3d secure
    is_success = models.BooleanField(default=False)
    #: Currency code (may be provider-specific)
    currency = models.CharField(max_length=10)
    #: Total amount (gross)
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal('0.0'))

    gateway_response = JSONField()

    def __repr__(self):
        return 'Transaction(created=%s, type=%s, is_success=%s)' % (
            self.created, self.transaction_type, self.is_success)
