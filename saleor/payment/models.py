from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.db import models
from django_prices.models import MoneyField, TaxedMoneyField

from . import ChargeStatus, TransactionType
from ..checkout.models import Cart
from ..core import zero_money
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

    total = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=12,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=zero_money)
    captured_amount = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=12,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=zero_money)

    checkout = models.ForeignKey(
        Cart, null=True, related_name='payments', on_delete=models.SET_NULL)
    order = models.ForeignKey(
        Order, null=True, related_name='payments', on_delete=models.PROTECT)

    def __repr__(self):
        return """
            Payment(variant=%s, is_active=%s, created=%s, charge_status=%s)
        """ % (self.variant, self.is_active, self.created, self.charge_status)

    def __iter__(self):
        return iter(self.transactions.all())

    def get_auth_transaction(self):
        txn = self.transactions.get(
            transaction_type=TransactionType.AUTH, is_success=True)
        return txn

    def authorize(self, client_token):
        # FIXME Used for backwards compatibility, remove after moving to
        # dashboard 2.0
        from . import utils
        return utils.gateway_authorize(
            payment=self, transaction_token=client_token)

    def void(self):
        # FIXME Used for backwards compatibility, remove after moving to
        # dashboard 2.0
        from . import utils
        return utils.gateway_void(payment=self)

    def capture(self, amount=None):
        # FIXME Used for backwards compatibility, remove after moving to
        # dashboard 2.0
        from . import utils
        return utils.gateway_capture(payment=self, amount=amount)

    def refund(self, amount=None):
        # FIXME Used for backwards compatibility, remove after moving to
        # dashboard 2.0
        from . import utils
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
    amount = MoneyField(
        currency=settings.DEFAULT_CURRENCY,
        max_digits=12,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=zero_money)

    gateway_response = JSONField()

    def __repr__(self):
        return 'Transaction(created=%s, type=%s, is_success=%s)' % (
            self.created, self.transaction_type, self.is_success)
