from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from functools import partial
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

import pytz
from django.conf import settings
from django.contrib.postgres.indexes import BTreeIndex, GinIndex
from django.db import connection, models
from django.db.models import Exists, JSONField, OuterRef, Q, Subquery, Sum
from django.utils import timezone
from django_countries.fields import CountryField
from django_prices.models import MoneyField
from django_prices.templatetags.prices import amount
from prices import Money, fixed_discount, percentage_discount

from ..app.models import App
from ..channel.models import Channel
from ..core.db.fields import SanitizedJSONField
from ..core.models import ModelWithMetadata
from ..core.utils.editorjs import clean_editor_js
from ..core.utils.json_serializer import CustomJsonEncoder
from ..core.utils.translations import Translation
from ..permission.enums import DiscountPermissions
from . import (
    DiscountType,
    DiscountValueType,
    PromotionEvents,
    PromotionType,
    RewardType,
    RewardValueType,
    VoucherType,
)

if TYPE_CHECKING:
    from ..account.models import User


class NotApplicable(ValueError):
    """Exception raised when a discount is not applicable to a checkout.

    The error is raised if the order value is below the minimum required
    price or the order quantity is below the minimum quantity of items.
    Minimum price will be available as the `min_spent` attribute.
    Minimum quantity will be available as the `min_checkout_items_quantity` attribute.
    """

    def __init__(self, msg, min_spent=None, min_checkout_items_quantity=None):
        super().__init__(msg)
        self.min_spent = min_spent
        self.min_checkout_items_quantity = min_checkout_items_quantity


class VoucherQueryset(models.QuerySet["Voucher"]):
    def active(self, date):
        subquery = (
            VoucherCode.objects.filter(voucher_id=OuterRef("pk"))
            .annotate(total_used=Sum("used"))
            .values("total_used")[:1]
        )
        return self.filter(
            Q(usage_limit__isnull=True) | Q(usage_limit__gt=Subquery(subquery)),
            Q(end_date__isnull=True) | Q(end_date__gte=date),
            start_date__lte=date,
        )

    def active_in_channel(self, date, channel_slug: str):
        channels = Channel.objects.filter(
            slug=str(channel_slug), is_active=True
        ).values("id")
        channel_listings = VoucherChannelListing.objects.filter(
            Exists(channels.filter(pk=OuterRef("channel_id"))),
        ).values("id")

        return self.active(date).filter(
            Exists(channel_listings.filter(voucher_id=OuterRef("pk")))
        )

    def expired(self, date):
        subquery = (
            VoucherCode.objects.filter(voucher_id=OuterRef("pk"))
            .annotate(total_used=Sum("used"))
            .values("total_used")[:1]
        )
        return self.filter(
            Q(usage_limit__lte=Subquery(subquery)) | Q(end_date__lt=date),
            start_date__lt=date,
        )


VoucherManager = models.Manager.from_queryset(VoucherQueryset)


class Voucher(ModelWithMetadata):
    type = models.CharField(
        max_length=20, choices=VoucherType.CHOICES, default=VoucherType.ENTIRE_ORDER
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    # this field indicates if discount should be applied per order or
    # individually to every item
    apply_once_per_order = models.BooleanField(default=False)
    apply_once_per_customer = models.BooleanField(default=False)
    single_use = models.BooleanField(default=False)

    only_for_staff = models.BooleanField(default=False)

    discount_value_type = models.CharField(
        max_length=10,
        choices=DiscountValueType.CHOICES,
        default=DiscountValueType.FIXED,
    )

    # not mandatory fields, usage depends on type
    countries = CountryField(multiple=True, blank=True)
    min_checkout_items_quantity = models.PositiveIntegerField(null=True, blank=True)
    products = models.ManyToManyField("product.Product", blank=True)
    variants = models.ManyToManyField("product.ProductVariant", blank=True)
    collections = models.ManyToManyField("product.Collection", blank=True)
    categories = models.ManyToManyField("product.Category", blank=True)

    objects = VoucherManager()

    class Meta:
        ordering = ("name", "pk")

    @property
    def code(self):
        # this function should be removed after field `code` will be deprecated
        code_instance = self.codes.last()
        return code_instance.code if code_instance else None

    @property
    def promo_codes(self):
        return list(self.codes.values_list("code", flat=True))

    def get_discount(self, channel: Channel):
        """Return proper discount amount for given channel.

        It operates over all channel listings as assuming that we have prefetched them.
        """
        voucher_channel_listing = None

        for channel_listing in self.channel_listings.all():
            if channel.id == channel_listing.channel_id:
                voucher_channel_listing = channel_listing
                break

        if not voucher_channel_listing:
            raise NotApplicable("This voucher is not assigned to this channel")
        if self.discount_value_type == DiscountValueType.FIXED:
            discount_amount = Money(
                voucher_channel_listing.discount_value, voucher_channel_listing.currency
            )
            return partial(fixed_discount, discount=discount_amount)
        if self.discount_value_type == DiscountValueType.PERCENTAGE:
            return partial(
                percentage_discount,
                percentage=voucher_channel_listing.discount_value,
                rounding=ROUND_HALF_UP,
            )
        raise NotImplementedError("Unknown discount type")

    def get_discount_amount_for(self, price: Money, channel: Channel) -> Money:
        discount = self.get_discount(channel)
        after_discount = discount(price)
        if after_discount.amount < 0:
            return price
        return price - after_discount

    def validate_min_spent(self, value: Money, channel: Channel):
        voucher_channel_listing = self.channel_listings.filter(channel=channel).first()
        if not voucher_channel_listing:
            raise NotApplicable("This voucher is not assigned to this channel")
        min_spent = voucher_channel_listing.min_spent
        if min_spent and value < min_spent:
            msg = f"This offer is only valid for orders over {amount(min_spent)}."
            raise NotApplicable(msg, min_spent=min_spent)

    def validate_min_checkout_items_quantity(self, quantity):
        min_checkout_items_quantity = self.min_checkout_items_quantity
        if min_checkout_items_quantity and min_checkout_items_quantity > quantity:
            msg = (
                "This offer is only valid for orders with a minimum of "
                f"{min_checkout_items_quantity} quantity."
            )
            raise NotApplicable(
                msg,
                min_checkout_items_quantity=min_checkout_items_quantity,
            )

    def validate_once_per_customer(self, customer_email):
        voucher_codes = self.codes.all()
        voucher_customer = VoucherCustomer.objects.filter(
            Exists(voucher_codes.filter(id=OuterRef("voucher_code_id"))),
            customer_email=customer_email,
        )
        if voucher_customer:
            msg = "This offer is valid only once per customer."
            raise NotApplicable(msg)

    def validate_only_for_staff(self, customer: Optional["User"]):
        if not self.only_for_staff:
            return

        if not customer or not customer.is_staff:
            msg = "This offer is valid only for staff customers."
            raise NotApplicable(msg)


class VoucherCode(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    code = models.CharField(max_length=255, unique=True, db_index=True)
    used = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    voucher = models.ForeignKey(
        Voucher, related_name="codes", on_delete=models.CASCADE, db_index=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [BTreeIndex(fields=["voucher"], name="vouchercode_voucher_idx")]
        ordering = ("-created_at", "code")


class VoucherChannelListing(models.Model):
    voucher = models.ForeignKey(
        Voucher,
        null=False,
        blank=False,
        related_name="channel_listings",
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        Channel,
        null=False,
        blank=False,
        related_name="voucher_listings",
        on_delete=models.CASCADE,
    )
    discount_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )
    discount = MoneyField(amount_field="discount_value", currency_field="currency")
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )
    min_spent_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    min_spent = MoneyField(amount_field="min_spent_amount", currency_field="currency")

    class Meta:
        unique_together = (("voucher", "channel"),)
        ordering = ("pk",)


class VoucherCustomer(models.Model):
    voucher_code = models.ForeignKey(
        VoucherCode,
        related_name="customers",
        on_delete=models.CASCADE,
        db_index=False,
    )
    customer_email = models.EmailField()

    class Meta:
        indexes = [
            BTreeIndex(fields=["voucher_code"], name="vouchercustomer_voucher_code_idx")
        ]
        ordering = ("voucher_code", "customer_email", "pk")
        unique_together = (("voucher_code", "customer_email"),)


class VoucherTranslation(Translation):
    voucher = models.ForeignKey(
        Voucher, related_name="translations", on_delete=models.CASCADE
    )
    name = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        ordering = ("language_code", "voucher", "pk")
        unique_together = (("language_code", "voucher"),)

    def get_translated_object_id(self):
        return "Voucher", self.voucher_id

    def get_translated_keys(self):
        return {"name": self.name}


class PromotionQueryset(models.QuerySet["Promotion"]):
    def active(self, date=None):
        if date is None:
            date = timezone.now()
        return self.filter(
            Q(end_date__isnull=True) | Q(end_date__gte=date), start_date__lte=date
        )

    def expired(self, date=None):
        if date is None:
            date = timezone.now()
        return self.filter(end_date__lt=date, start_date__lt=date)


PromotionManager = models.Manager.from_queryset(PromotionQueryset)


class Promotion(ModelWithMetadata):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=255,
        choices=PromotionType.CHOICES,
        default=PromotionType.CATALOGUE,
    )
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    old_sale_id = models.IntegerField(blank=True, null=True, unique=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    last_notification_scheduled_at = models.DateTimeField(null=True, blank=True)
    objects = PromotionManager()

    class Meta:
        ordering = ("name", "pk")
        permissions = (
            (
                DiscountPermissions.MANAGE_DISCOUNTS.codename,
                "Manage promotions and vouchers.",
            ),
        )
        indexes = [
            BTreeIndex(fields=["start_date"], name="start_date_idx"),
            BTreeIndex(fields=["end_date"], name="end_date_idx"),
        ]

    def is_active(self, date=None):
        if date is None:
            date = datetime.now(pytz.utc)
        return (not self.end_date or self.end_date >= date) and self.start_date <= date

    def assign_old_sale_id(self):
        with connection.cursor() as cursor:
            cursor.execute("SELECT nextval('discount_promotion_old_sale_id_seq')")
            result = cursor.fetchone()
            self.old_sale_id = result[0]
            self.save(update_fields=["old_sale_id"])


class PromotionTranslation(Translation):
    name = models.CharField(max_length=255, null=True, blank=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    promotion = models.ForeignKey(
        Promotion, related_name="translations", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("language_code", "promotion"),)

    def get_translated_object_id(self):
        return "Promotion", self.promotion_id

    def get_translated_keys(self):
        return {"name": self.name, "description": self.description}


class PromotionRule(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    promotion = models.ForeignKey(
        Promotion, on_delete=models.CASCADE, related_name="rules"
    )
    channels = models.ManyToManyField(Channel)
    catalogue_predicate = models.JSONField(
        blank=True, default=dict, encoder=CustomJsonEncoder
    )
    order_predicate = models.JSONField(
        blank=True, default=dict, encoder=CustomJsonEncoder
    )
    variants = models.ManyToManyField(  # type: ignore[var-annotated]
        "product.ProductVariant", blank=True, through="PromotionRule_Variants"
    )
    reward_value_type = models.CharField(
        max_length=255, choices=RewardValueType.CHOICES, blank=True, null=True
    )
    reward_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        null=True,
        blank=True,
    )
    reward_type = models.CharField(
        max_length=255, choices=RewardType.CHOICES, blank=True, null=True
    )
    gifts = models.ManyToManyField(
        "product.ProductVariant", blank=True, related_name="+"
    )
    old_channel_listing_id = models.IntegerField(blank=True, null=True, unique=True)
    variants_dirty = models.BooleanField(default=False)

    class Meta:
        ordering = ("name", "pk")

    def get_discount(self, currency):
        if self.reward_value_type == RewardValueType.FIXED:
            discount_amount = Money(self.reward_value, currency)
            return partial(fixed_discount, discount=discount_amount)
        if self.reward_value_type == RewardValueType.PERCENTAGE:
            return partial(
                percentage_discount,
                percentage=self.reward_value,
                rounding=ROUND_HALF_UP,
            )
        raise NotImplementedError("Unknown discount type")

    @staticmethod
    def get_old_channel_listing_ids(qunatity):
        with connection.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT nextval('discount_promotionrule_old_channel_listing_id_seq')
                FROM generate_series(1, {qunatity})
                """
            )
            return cursor.fetchall()


class PromotionRule_Variants(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False, unique=True)
    promotionrule = models.ForeignKey(
        PromotionRule,
        on_delete=models.CASCADE,
    )
    productvariant = models.ForeignKey(
        "product.ProductVariant",
        on_delete=models.CASCADE,
    )


class PromotionRuleTranslation(Translation):
    name = models.CharField(max_length=255, null=True, blank=True)
    description = SanitizedJSONField(blank=True, null=True, sanitizer=clean_editor_js)
    promotion_rule = models.ForeignKey(
        PromotionRule, related_name="translations", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("language_code", "promotion_rule"),)

    def get_translated_object_id(self):
        return "PromotionRule", self.promotion_rule_id

    def get_translated_keys(self):
        return {"name": self.name, "description": self.description}


class BaseDiscount(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    type = models.CharField(
        max_length=64,
        choices=DiscountType.CHOICES,
        default=DiscountType.MANUAL,
    )
    value_type = models.CharField(
        max_length=10,
        choices=DiscountValueType.CHOICES,
        default=DiscountValueType.FIXED,
    )
    value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    amount_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=Decimal("0.0"),
    )
    amount = MoneyField(amount_field="amount_value", currency_field="currency")
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    translated_name = models.CharField(max_length=255, null=True, blank=True)
    reason = models.TextField(blank=True, null=True)
    promotion_rule = models.ForeignKey(
        PromotionRule,
        related_name="+",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        db_index=False,
    )
    voucher = models.ForeignKey(
        Voucher, related_name="+", blank=True, null=True, on_delete=models.SET_NULL
    )
    voucher_code = models.CharField(
        max_length=255, null=True, blank=True, db_index=False
    )

    class Meta:
        abstract = True


class OrderDiscount(BaseDiscount):
    order = models.ForeignKey(
        "order.Order",
        related_name="discounts",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    old_id = models.PositiveIntegerField(unique=True, null=True, blank=True)

    class Meta:
        indexes = [
            BTreeIndex(
                fields=["promotion_rule"], name="orderdiscount_promotion_rule_idx"
            ),
            # Orders searching index
            GinIndex(fields=["name", "translated_name"]),
            GinIndex(fields=["voucher_code"], name="orderdiscount_voucher_code_idx"),
        ]
        ordering = ("created_at", "id")


class OrderLineDiscount(BaseDiscount):
    line = models.ForeignKey(
        "order.OrderLine",
        related_name="discounts",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    # Saleor in version 3.19 and below, doesn't have any unique constraint applied on
    # discounts for checkout/order. To not have an impact on existing DB objects,
    # the new field `unique_type` will be used for new discount records.
    # This will ensure that we always apply a single specific discount type.
    unique_type = models.CharField(
        max_length=64, null=True, blank=True, choices=DiscountType.CHOICES
    )

    class Meta:
        indexes = [
            BTreeIndex(
                fields=["promotion_rule"], name="orderlinedisc_promotion_rule_idx"
            ),
            GinIndex(fields=["voucher_code"], name="orderlinedisc_voucher_code_idx"),
        ]
        ordering = ("created_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["line_id", "unique_type"],
                name="unique_orderline_discount_type",
            ),
        ]


class CheckoutDiscount(BaseDiscount):
    checkout = models.ForeignKey(
        "checkout.Checkout",
        related_name="discounts",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        indexes = [
            BTreeIndex(fields=["promotion_rule"], name="checkoutdiscount_rule_idx"),
            # Orders searching index
            GinIndex(fields=["name", "translated_name"]),
            GinIndex(fields=["voucher_code"], name="checkoutdiscount_voucher_idx"),
        ]
        ordering = ("created_at", "id")
        unique_together = ("checkout_id", "promotion_rule_id")


class CheckoutLineDiscount(BaseDiscount):
    line = models.ForeignKey(
        "checkout.CheckoutLine",
        related_name="discounts",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    # Saleor in version 3.19 and below, doesn't have any unique constraint applied on
    # discounts for checkout/order. To not have an impact on existing DB objects,
    # the new field `unique_type` will be used for new discount records.
    # This will ensure that we always apply a single specific discount type.
    unique_type = models.CharField(
        max_length=64, null=True, blank=True, choices=DiscountType.CHOICES
    )

    class Meta:
        indexes = [
            BTreeIndex(
                fields=["promotion_rule"], name="checklinedisc_promotion_rule_idx"
            ),
            GinIndex(fields=["voucher_code"], name="checklinedisc_voucher_code_idx"),
        ]
        ordering = ("created_at", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["line_id", "unique_type"],
                name="unique_checkoutline_discount_type",
            ),
        ]


class PromotionEvent(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, unique=True, default=uuid4)
    date = models.DateTimeField(auto_now_add=True, db_index=True, editable=False)
    type = models.CharField(max_length=255, choices=PromotionEvents.CHOICES)
    parameters = JSONField(blank=True, default=dict, encoder=CustomJsonEncoder)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        related_name="promotion_events",
        on_delete=models.SET_NULL,
    )
    app = models.ForeignKey(
        App,
        blank=True,
        null=True,
        related_name="promotion_events",
        on_delete=models.SET_NULL,
    )
    promotion = models.ForeignKey(
        Promotion, related_name="events", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("date",)
