"""Checkout-related ORM models."""

from datetime import date
from decimal import Decimal
from operator import attrgetter
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.encoding import smart_str
from django_countries.fields import Country, CountryField
from django_prices.models import MoneyField, TaxedMoneyField
from prices import Money

from ..channel.models import Channel
from ..core.models import ModelWithMetadata
from ..core.taxes import zero_money
from ..giftcard.models import GiftCard
from ..permission.enums import CheckoutPermissions
from ..shipping.models import ShippingMethod
from . import CheckoutAuthorizeStatus, CheckoutChargeStatus

if TYPE_CHECKING:
    from ..payment.models import Payment
    from ..product.models import ProductVariant


def get_default_country():
    return settings.DEFAULT_COUNTRY


class Checkout(models.Model):
    """A shopping checkout."""

    created_at = models.DateTimeField(auto_now_add=True)
    last_change = models.DateTimeField(auto_now=True, db_index=True)
    completing_started_at = models.DateTimeField(blank=True, null=True)

    # Denormalized modified_at for the latest modified transactionItem assigned to
    # checkout
    last_transaction_modified_at = models.DateTimeField(null=True, blank=True)
    automatically_refundable = models.BooleanField(default=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="checkouts",
        on_delete=models.CASCADE,
    )
    email = models.EmailField(blank=True, null=True)
    token = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    channel = models.ForeignKey(
        Channel,
        related_name="checkouts",
        on_delete=models.PROTECT,
    )
    billing_address = models.ForeignKey(
        "account.Address",
        related_name="+",
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
    )
    shipping_address = models.ForeignKey(
        "account.Address",
        related_name="+",
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
    )
    shipping_method = models.ForeignKey(
        ShippingMethod,
        blank=True,
        null=True,
        related_name="checkouts",
        on_delete=models.SET_NULL,
    )
    collection_point = models.ForeignKey(
        "warehouse.Warehouse",
        blank=True,
        null=True,
        related_name="checkouts",
        on_delete=models.SET_NULL,
    )
    note = models.TextField(blank=True, default="")

    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )
    country = CountryField(default=get_default_country)

    total_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    total_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    total = TaxedMoneyField(
        net_amount_field="total_net_amount",
        gross_amount_field="total_gross_amount",
    )
    # base price contains only catalogue discounts (does not contains voucher discount)
    base_total_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    base_total = MoneyField(amount_field="base_total_amount", currency_field="currency")

    subtotal_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    subtotal_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    subtotal = TaxedMoneyField(
        net_amount_field="subtotal_net_amount",
        gross_amount_field="subtotal_gross_amount",
    )
    # base price contains only catalogue discounts (does not contains voucher discount)
    base_subtotal_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    base_subtotal = MoneyField(
        amount_field="base_subtotal_amount", currency_field="currency"
    )

    shipping_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    shipping_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    shipping_price = TaxedMoneyField(
        net_amount_field="shipping_price_net_amount",
        gross_amount_field="shipping_price_gross_amount",
    )
    shipping_tax_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal("0.0")
    )

    authorize_status = models.CharField(
        max_length=32,
        default=CheckoutAuthorizeStatus.NONE,
        choices=CheckoutAuthorizeStatus.CHOICES,
        db_index=True,
    )

    charge_status = models.CharField(
        max_length=32,
        default=CheckoutChargeStatus.NONE,
        choices=CheckoutChargeStatus.CHOICES,
        db_index=True,
    )

    price_expiration = models.DateTimeField(default=timezone.now)

    discount_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    discount = MoneyField(amount_field="discount_amount", currency_field="currency")
    discount_name = models.CharField(max_length=255, blank=True, null=True)

    translated_discount_name = models.CharField(max_length=255, blank=True, null=True)
    gift_cards = models.ManyToManyField(GiftCard, blank=True, related_name="checkouts")
    voucher_code = models.CharField(max_length=255, blank=True, null=True)

    # The field prevents race condition when two different threads are processing
    # the same checkout with limited usage voucher assigned. Both threads increasing the
    # voucher usage would cause `NotApplicable` error for voucher.
    is_voucher_usage_increased = models.BooleanField(default=False)

    redirect_url = models.URLField(blank=True, null=True)
    tracking_code = models.CharField(max_length=255, blank=True, null=True)

    language_code = models.CharField(
        max_length=35, choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE
    )

    tax_exemption = models.BooleanField(default=False)
    tax_error = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        ordering = ("-last_change", "pk")
        permissions = (
            (CheckoutPermissions.MANAGE_CHECKOUTS.codename, "Manage checkouts"),
            (CheckoutPermissions.HANDLE_CHECKOUTS.codename, "Handle checkouts"),
            (CheckoutPermissions.HANDLE_TAXES.codename, "Handle taxes"),
            (CheckoutPermissions.MANAGE_TAXES.codename, "Manage taxes"),
        )

    def __iter__(self):
        return iter(self.lines.all())

    def get_customer_email(self) -> Optional[str]:
        return self.user.email if self.user else self.email

    def is_shipping_required(self) -> bool:
        """Return `True` if any of the lines requires shipping."""
        return any(line.is_shipping_required() for line in self)

    def is_checkout_locked(self) -> bool:
        return bool(
            self.completing_started_at
            and (
                (timezone.now() - self.completing_started_at).seconds
                < settings.CHECKOUT_COMPLETION_LOCK_TIME
            )
        )

    def get_total_gift_cards_balance(
        self, database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME
    ) -> Money:
        """Return the total balance of the gift cards assigned to the checkout."""
        balance = (
            self.gift_cards.using(database_connection_name)
            .active(date=date.today())
            .aggregate(models.Sum("current_balance_amount"))[
                "current_balance_amount__sum"
            ]
        )
        if balance is None:
            return zero_money(currency=self.currency)
        return Money(balance, self.currency)

    def get_line(self, variant: "ProductVariant") -> Optional["CheckoutLine"]:
        """Return a line matching the given variant and data if any."""
        matching_lines = (line for line in self if line.variant.pk == variant.pk)
        return next(matching_lines, None)

    def get_last_active_payment(self) -> Optional["Payment"]:
        payments = [payment for payment in self.payments.all() if payment.is_active]
        return max(payments, default=None, key=attrgetter("pk"))

    def set_country(
        self, country_code: str, commit: bool = False, replace: bool = True
    ):
        """Set country for checkout."""
        if not replace and self.country is not None:
            return
        self.country = Country(country_code)
        if commit:
            self.save(update_fields=["country"])

    def get_country(self):
        address = self.shipping_address or self.billing_address
        saved_country = self.country
        if address is None or not address.country:
            return saved_country.code

        country_code = address.country.code
        if not country_code == saved_country.code:
            self.set_country(country_code, commit=True)
        return country_code


class CheckoutLine(ModelWithMetadata):
    """A single checkout line.

    Multiple lines in the same checkout can refer to the same product variant if
    their `data` field is different.
    """

    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    old_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    checkout = models.ForeignKey(
        Checkout, related_name="lines", on_delete=models.CASCADE
    )
    variant = models.ForeignKey(
        "product.ProductVariant", related_name="+", on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    is_gift = models.BooleanField(default=False)
    price_override = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )

    total_price_net_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    total_price_gross_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    total_price = TaxedMoneyField(
        net_amount_field="total_price_net_amount",
        gross_amount_field="total_price_gross_amount",
    )
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=4, default=Decimal("0.0")
    )

    class Meta(ModelWithMetadata.Meta):
        ordering = ("created_at", "id")

    def __str__(self):
        return smart_str(self.variant)

    __hash__ = models.Model.__hash__

    def __eq__(self, other):
        if not isinstance(other, CheckoutLine):
            return NotImplemented

        return self.variant == other.variant and self.quantity == other.quantity

    def __ne__(self, other):
        return not self == other  # pragma: no cover

    def __repr__(self):
        return f"CheckoutLine(variant={self.variant!r}, quantity={self.quantity!r})"

    def __getstate__(self):
        return self.variant, self.quantity

    def __setstate__(self, data):
        self.variant, self.quantity = data

    def is_shipping_required(self) -> bool:
        """Return `True` if the related product variant requires shipping."""
        return self.variant.is_shipping_required()


# Checkout metadata is moved to separate model so it can be used when checkout model is
# locked by select_for_update during complete_checkout.
class CheckoutMetadata(ModelWithMetadata):
    checkout = models.OneToOneField(
        Checkout, related_name="metadata_storage", on_delete=models.CASCADE
    )
