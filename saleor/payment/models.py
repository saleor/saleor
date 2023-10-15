from decimal import Decimal
from operator import attrgetter
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.indexes import GinIndex
from django.core.serializers.json import DjangoJSONEncoder
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from django_prices.models import MoneyField
from prices import Money

from ..checkout.models import Checkout
from ..core.models import ModelWithMetadata
from ..core.taxes import zero_money
from ..permission.enums import PaymentPermissions
from . import (
    ChargeStatus,
    CustomPaymentChoices,
    StorePaymentMethod,
    TransactionAction,
    TransactionEventType,
    TransactionKind,
)


class TransactionItem(ModelWithMetadata):
    token = models.UUIDField(unique=True, default=uuid4)
    use_old_id = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=512, blank=True, null=True, default="")
    message = models.CharField(max_length=512, blank=True, null=True, default="")
    psp_reference = models.CharField(max_length=512, blank=True, null=True)
    available_actions = ArrayField(
        models.CharField(max_length=128, choices=TransactionAction.CHOICES),
        default=list,
    )

    currency = models.CharField(max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH)

    amount_charged = MoneyField(amount_field="charged_value", currency_field="currency")
    charged_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )
    amount_authorized = MoneyField(
        amount_field="authorized_value", currency_field="currency"
    )
    authorized_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )
    amount_refunded = MoneyField(
        amount_field="refunded_value", currency_field="currency"
    )
    refunded_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )
    amount_canceled = MoneyField(
        amount_field="canceled_value", currency_field="currency"
    )
    canceled_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )
    amount_refund_pending = MoneyField(
        amount_field="refund_pending_value", currency_field="currency"
    )
    refund_pending_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )

    amount_charge_pending = MoneyField(
        amount_field="charge_pending_value", currency_field="currency"
    )
    charge_pending_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )

    amount_authorize_pending = MoneyField(
        amount_field="authorize_pending_value", currency_field="currency"
    )
    authorize_pending_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )

    cancel_pending_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )
    amount_cancel_pending = MoneyField(
        amount_field="cancel_pending_value", currency_field="currency"
    )

    external_url = models.URLField(blank=True, null=True)

    checkout = models.ForeignKey(
        Checkout,
        null=True,
        related_name="payment_transactions",
        on_delete=models.SET_NULL,
    )
    order = models.ForeignKey(
        "order.Order",
        related_name="payment_transactions",
        null=True,
        on_delete=models.PROTECT,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # We store app and app_identifier, as the app field stores apps of
    # all types (local, third-party), and the app_identifier field stores
    # only third-party apps.
    # In the case of re-installing the third-party app, we are able to match
    # existing transactions with the re-installed app by using `app_identifier`.
    app = models.ForeignKey(
        "app.App",
        related_name="+",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    app_identifier = models.CharField(blank=True, null=True, max_length=256)

    class Meta:
        ordering = ("pk",)
        indexes = [
            *ModelWithMetadata.Meta.indexes,
        ]


class TransactionEvent(models.Model):
    created_at = models.DateTimeField(default=timezone.now)
    psp_reference = models.CharField(max_length=512, blank=True, null=True)
    message = models.CharField(max_length=512, blank=True, null=True, default="")
    transaction = models.ForeignKey(
        TransactionItem, related_name="events", on_delete=models.CASCADE
    )
    external_url = models.URLField(blank=True, null=True)
    currency = models.CharField(max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH)
    type = models.CharField(
        max_length=128,
        choices=TransactionEventType.CHOICES,
        default=TransactionEventType.INFO,
    )
    amount = MoneyField(amount_field="amount_value", currency_field="currency")
    amount_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0"),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    # We store app and app_identifier, as the app field stores apps of
    # all types (local, third-party), and the app_identifier field stores
    # only third-party apps.
    # In the case of re-installing the third-party app, we are able to match
    # existing transactions with the re-installed app by using `app_identifier`.
    app = models.ForeignKey(
        "app.App", related_name="+", null=True, blank=True, on_delete=models.SET_NULL
    )
    app_identifier = models.CharField(blank=True, null=True, max_length=256)

    include_in_calculations = models.BooleanField(default=False)

    class Meta:
        ordering = ("pk",)


class Payment(ModelWithMetadata):
    """A model that represents a single payment.

    This might be a transactable payment information such as credit card
    details, gift card information or a customer's authorization to charge
    their PayPal account.

    All payment process related pieces of information are stored
    at the gateway level, we are operating on the reusable token
    which is a unique identifier of the customer for given gateway.

    Several payment methods can be used within a single order. Each payment
    method may consist of multiple transactions.
    """

    gateway = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    to_confirm = models.BooleanField(default=False)
    partial = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    charge_status = models.CharField(
        max_length=20, choices=ChargeStatus.CHOICES, default=ChargeStatus.NOT_CHARGED
    )
    token = models.CharField(max_length=512, blank=True, default="")
    total = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    captured_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH
    )  # FIXME: add ISO4217 validator

    checkout = models.ForeignKey(
        Checkout, null=True, related_name="payments", on_delete=models.SET_NULL
    )
    order = models.ForeignKey(
        "order.Order",
        related_name="payments",
        null=True,
        on_delete=models.PROTECT,
    )
    store_payment_method = models.CharField(
        max_length=11,
        choices=StorePaymentMethod.CHOICES,
        default=StorePaymentMethod.NONE,
    )

    billing_email = models.EmailField(blank=True)
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

    cc_first_digits = models.CharField(max_length=6, blank=True, default="")
    cc_last_digits = models.CharField(max_length=4, blank=True, default="")
    cc_brand = models.CharField(max_length=40, blank=True, default="")
    cc_exp_month = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)], null=True, blank=True
    )
    cc_exp_year = models.PositiveIntegerField(
        validators=[MinValueValidator(1000)], null=True, blank=True
    )

    payment_method_type = models.CharField(max_length=256, blank=True)

    customer_ip_address = models.GenericIPAddressField(blank=True, null=True)
    extra_data = models.TextField(blank=True, default="")
    return_url = models.URLField(blank=True, null=True)
    psp_reference = models.CharField(
        max_length=512, null=True, blank=True, db_index=True
    )

    class Meta:
        ordering = ("pk",)
        permissions = (
            (
                PaymentPermissions.HANDLE_PAYMENTS.codename,
                "Handle payments",
            ),
        )
        indexes = [
            *ModelWithMetadata.Meta.indexes,
            # Orders filtering by status index
            GinIndex(fields=["order_id", "is_active", "charge_status"]),
        ]

    def __repr__(self):
        return (
            f"Payment(gateway={self.gateway}, is_active={self.is_active}, "
            f"created={self.created_at}, charge_status={self.charge_status})"
        )

    def get_last_transaction(self):
        return max(self.transactions.all(), default=None, key=attrgetter("pk"))

    def get_total(self):
        return Money(self.total, self.currency)

    def get_authorized_amount(self):
        money = zero_money(self.currency)

        # Query all the transactions which should be prefetched
        # to optimize db queries
        transactions = self.transactions.all()

        # There is no authorized amount anymore when capture is succeeded
        # since capture can only be made once, even it is a partial capture
        if any(
            [
                txn.kind == TransactionKind.CAPTURE and txn.is_success
                for txn in transactions
            ]
        ):
            return money

        # Filter the succeeded auth transactions
        authorized_txns = [
            txn
            for txn in transactions
            if txn.kind == TransactionKind.AUTH
            and txn.is_success
            and not txn.action_required
        ]

        # Calculate authorized amount from all succeeded auth transactions
        for txn in authorized_txns:
            money += Money(txn.amount, self.currency)

        # If multiple partial capture is supported later though it's unlikely,
        # the authorized amount should exclude the already captured amount here
        return money

    def get_captured_amount(self):
        return Money(self.captured_amount, self.currency)

    def get_charge_amount(self):
        """Retrieve the maximum capture possible."""
        return self.total - self.captured_amount

    @property
    def is_authorized(self):
        return any(
            [
                txn.kind == TransactionKind.AUTH
                and txn.is_success
                and not txn.action_required
                for txn in self.transactions.all()
            ]
        )

    @property
    def not_charged(self):
        return self.charge_status == ChargeStatus.NOT_CHARGED

    def can_authorize(self):
        return self.is_active and self.not_charged

    def can_capture(self):
        if not (self.is_active and self.not_charged):
            return False
        return True

    def can_void(self):
        return self.not_charged and self.is_authorized

    def can_refund(self):
        can_refund_charge_status = (
            ChargeStatus.PARTIALLY_CHARGED,
            ChargeStatus.FULLY_CHARGED,
            ChargeStatus.PARTIALLY_REFUNDED,
        )
        return self.charge_status in can_refund_charge_status

    def can_confirm(self):
        return self.is_active and self.not_charged

    def is_manual(self):
        return self.gateway == CustomPaymentChoices.MANUAL


class Transaction(models.Model):
    """Represents a single payment operation.

    Transaction is an attempt to transfer money between your store
    and your customers, with a chosen payment method.
    """

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    payment = models.ForeignKey(
        Payment, related_name="transactions", on_delete=models.PROTECT
    )
    token = models.CharField(max_length=512, blank=True, default="")
    kind = models.CharField(max_length=25, choices=TransactionKind.CHOICES)
    is_success = models.BooleanField(default=False)
    action_required = models.BooleanField(default=False)
    action_required_data = JSONField(
        blank=True, default=dict, encoder=DjangoJSONEncoder
    )
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )
    amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    error = models.TextField(null=True)
    customer_id = models.CharField(max_length=256, null=True)
    gateway_response = JSONField(encoder=DjangoJSONEncoder)
    already_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ("pk",)

    def __repr__(self):
        return (
            f"Transaction(type={self.kind}, is_success={self.is_success}, "
            f"created={self.created_at})"
        )

    def get_amount(self):
        return Money(self.amount, self.currency)
