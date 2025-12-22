"""Checkout-related ORM models."""

import datetime
from decimal import Decimal
from operator import attrgetter
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from django.conf import settings
from django.contrib.postgres.indexes import BTreeIndex
from django.core.validators import MinValueValidator
from django.db import models, transaction
from django.utils import timezone
from django.utils.encoding import smart_str
from django_countries.fields import Country, CountryField
from prices import Money

from ..channel.models import Channel
from ..core.db.fields import MoneyField, TaxedMoneyField
from ..core.models import ModelWithMetadata
from ..core.taxes import TAX_ERROR_FIELD_LENGTH, zero_money
from ..core.utils.json_serializer import CustomJsonEncoder
from ..giftcard.models import GiftCard
from ..permission.enums import CheckoutPermissions
from ..shipping.models import ShippingMethod
from . import CheckoutAuthorizeStatus, CheckoutChargeStatus

if TYPE_CHECKING:
    from ..payment.models import Payment
    from ..product.models import ProductVariant


def get_default_country():
    return settings.DEFAULT_COUNTRY


class CheckoutDelivery(models.Model):
    """Model to cache shipping methods for a checkout."""

    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    checkout = models.ForeignKey(
        "checkout.Checkout",
        related_name="shipping_methods",
        on_delete=models.CASCADE,
    )
    external_shipping_method_id = models.CharField(
        max_length=1024, blank=True, null=True, editable=False, db_index=True
    )
    built_in_shipping_method_id = models.IntegerField(
        blank=True, null=True, editable=False, db_index=True
    )

    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)

    price = MoneyField(amount_field="price_amount", currency_field="currency")
    price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )

    maximum_delivery_days = models.PositiveIntegerField(null=True, blank=True)
    minimum_delivery_days = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict)
    private_metadata = models.JSONField(default=dict)

    active = models.BooleanField(default=True)
    message = models.TextField(blank=True, null=True)

    is_external = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Denormalized tax class data
    tax_class_id = models.IntegerField(null=True, blank=True)
    tax_class_name = models.CharField(max_length=255, null=True, blank=True)
    tax_class_private_metadata = models.JSONField(
        blank=True, db_default={}, default=dict, encoder=CustomJsonEncoder
    )
    tax_class_metadata = models.JSONField(
        blank=True, db_default={}, default=dict, encoder=CustomJsonEncoder
    )

    @property
    def shipping_method_id(self) -> str:
        return self.external_shipping_method_id or str(self.built_in_shipping_method_id)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "checkout",
                    "external_shipping_method_id",
                    "built_in_shipping_method_id",
                    "is_valid",
                ],
                name="unique_for_checkout",
                nulls_distinct=False,
            ),
        ]
        ordering = ("created_at", "pk")


class Checkout(models.Model):
    """A shopping checkout."""

    created_at = models.DateTimeField(auto_now_add=True)
    last_change = models.DateTimeField(auto_now=True, db_index=True)
    completing_started_at = models.DateTimeField(blank=True, null=True)

    # Denormalized modified_at for the latest modified transactionItem assigned to
    # checkout
    last_transaction_modified_at = models.DateTimeField(null=True, blank=True)
    automatically_refundable = models.BooleanField(default=False)

    # Tracks the last time automatic checkout completion was attempted
    last_automatic_completion_attempt = models.DateTimeField(null=True, blank=True)

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
    save_billing_address = models.BooleanField(default=True)
    billing_address = models.ForeignKey(
        "account.Address",
        related_name="+",
        editable=False,
        null=True,
        on_delete=models.SET_NULL,
    )
    # do not apply on checkouts with collection point
    save_shipping_address = models.BooleanField(default=True)
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

    shipping_method_name = models.CharField(
        max_length=255, null=True, default=None, blank=True, editable=False
    )
    external_shipping_method_id = models.CharField(
        max_length=1024, null=True, default=None, blank=True, editable=False
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

    undiscounted_base_shipping_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )
    # Shipping price before applying any discounts
    undiscounted_base_shipping_price = MoneyField(
        amount_field="undiscounted_base_shipping_price_amount",
        currency_field="currency",
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

    delivery_methods_stale_at = models.DateTimeField(null=True, blank=True)
    price_expiration = models.DateTimeField(default=timezone.now)
    # Expiration time of the applied discounts.
    # Decides if the discounts are updated before tax recalculation.
    discount_expiration = models.DateTimeField(default=timezone.now)

    assigned_delivery = models.ForeignKey(
        CheckoutDelivery,
        blank=True,
        null=True,
        related_name="+",
        on_delete=models.SET_NULL,
    )

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
    tax_error = models.CharField(
        max_length=TAX_ERROR_FIELD_LENGTH, blank=True, null=True
    )

    class Meta:
        ordering = ("-last_change", "pk")
        permissions = (
            (CheckoutPermissions.MANAGE_CHECKOUTS.codename, "Manage checkouts"),
            (CheckoutPermissions.HANDLE_CHECKOUTS.codename, "Handle checkouts"),
            (CheckoutPermissions.HANDLE_TAXES.codename, "Handle taxes"),
            (CheckoutPermissions.MANAGE_TAXES.codename, "Manage taxes"),
        )
        indexes = [
            BTreeIndex(
                fields=["last_automatic_completion_attempt"],
                name="automaticcompletionattempt_idx",
            ),
            models.Index(fields=["created_at"], name="idx_checkout_created_at"),
        ]

    def __iter__(self):
        return iter(self.lines.all())

    def safe_update(self, update_fields: list[str]) -> None:
        """Safely update the checkout instance.

        This method locks the checkout row in the database to prevent concurrent updates.
        In case the checkout does not exist, it raises a CheckoutDoesNotExist exception.

        It prevents the DatabaseError that occurs in case save with update_fields is
        called on a deleted checkout instance.
        """
        from ..core.db.connection import allow_writer

        with allow_writer():
            with transaction.atomic():
                checkout = (
                    Checkout.objects.select_for_update()
                    .filter(pk=self.pk)
                    .only("pk")
                    .first()
                )
                if not checkout:
                    raise Checkout.DoesNotExist(
                        "Checkout does not exist. Unable to update."
                    )
                self.save(update_fields=update_fields)

    def get_customer_email(self) -> str | None:
        if self.email:
            return self.email
        if self.user:
            return self.user.email
        return None

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
            .active(date=datetime.datetime.now(tz=datetime.UTC).date())
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

    undiscounted_unit_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal(0),
    )

    undiscounted_unit_price = MoneyField(
        amount_field="undiscounted_unit_price_amount",
        currency_field="currency",
    )

    prior_unit_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )

    prior_unit_price = MoneyField(
        amount_field="prior_unit_price_amount", currency_field="currency"
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
        return f"<CheckoutLine: variant={self.variant!r}, quantity={self.quantity!r}, total={self.total_price_gross_amount} {self.currency}>"

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
