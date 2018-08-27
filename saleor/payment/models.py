from decimal import Decimal

from django.contrib.postgres.fields import JSONField
from django.db import models
from prices import Money

from . import PaymentMethodChargeStatus, TransactionType
from ..checkout.models import Cart
from ..order.models import Order


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

    # refactor to MoneyField
    total = models.DecimalField(
        max_digits=9, decimal_places=2, default=Decimal('0.0'))
    currency = models.CharField(max_length=10)
    captured_amount = models.DecimalField(
        max_digits=9, decimal_places=2, default=Decimal('0.0'))
    tax = models.DecimalField(
        max_digits=9, decimal_places=2, default=Decimal('0.0'))

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

    def get_auth_transaction(self):
        txn = self.transactions.get(
            transaction_type=TransactionType.AUTH, is_success=True)
        return txn

    def authorize(self, client_token):
        # FIXME
        from . import utils
        return utils.gateway_authorize(
            payment_method=self, transaction_token=client_token)

    def void(self):
        # FIXME
        from . import utils

        return utils.gateway_void(payment_method=self)

    def charge(self, amount=None):
        # FIXME
        from . import utils

        return utils.gateway_charge(payment_method=self, amount=amount)

    def refund(self, amount=None):
        # FIXME
        from . import utils

        return utils.gateway_refund(payment_method=self, amount=amount)


class Transaction(models.Model):
    payment_method = models.ForeignKey(
        PaymentMethod, related_name='transactions', on_delete=models.CASCADE)
    token = models.CharField(max_length=64, blank=True, default='')
    transaction_type = models.CharField(
        max_length=10, choices=TransactionType.CHOICES)
    is_success = models.BooleanField(default=False)
    amount = models.DecimalField(
        max_digits=9, decimal_places=2, default=Decimal('0.0'))
    gateway_response = JSONField()

    def get_amount(self):
        return Money(amount=self.amount, currency=self.payment_method.currency)
