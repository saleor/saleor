from decimal import Decimal
from functools import partial

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django_countries.fields import CountryField
from django_prices.models import MoneyField
from django_prices.templatetags.prices import amount
from prices import Money, fixed_discount, percentage_discount

from ..channel.models import Channel
from ..core.permissions import DiscountPermissions
from ..core.utils.translations import TranslationProxy
from . import DiscountValueType, VoucherType


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


class VoucherQueryset(models.QuerySet):
    def active(self, date):
        return self.filter(
            Q(usage_limit__isnull=True) | Q(used__lt=F("usage_limit")),
            Q(end_date__isnull=True) | Q(end_date__gte=date),
            start_date__lte=date,
        )

    def active_in_channel(self, date, channel_slug: str):
        return self.active(date).filter(
            channel_listings__channel__slug=channel_slug,
            channel_listings__channel__is_active=True,
        )

    def expired(self, date):
        return self.filter(
            Q(used__gte=F("usage_limit")) | Q(end_date__lt=date), start_date__lt=date
        )


class Voucher(models.Model):
    type = models.CharField(
        max_length=20, choices=VoucherType.CHOICES, default=VoucherType.ENTIRE_ORDER
    )
    name = models.CharField(max_length=255, null=True, blank=True)
    code = models.CharField(max_length=12, unique=True, db_index=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used = models.PositiveIntegerField(default=0, editable=False)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)
    # this field indicates if discount should be applied per order or
    # individually to every item
    apply_once_per_order = models.BooleanField(default=False)
    apply_once_per_customer = models.BooleanField(default=False)

    discount_value_type = models.CharField(
        max_length=10,
        choices=DiscountValueType.CHOICES,
        default=DiscountValueType.FIXED,
    )

    # not mandatory fields, usage depends on type
    countries = CountryField(multiple=True, blank=True)
    min_checkout_items_quantity = models.PositiveIntegerField(null=True, blank=True)
    products = models.ManyToManyField("product.Product", blank=True)
    collections = models.ManyToManyField("product.Collection", blank=True)
    categories = models.ManyToManyField("product.Category", blank=True)

    objects = VoucherQueryset.as_manager()
    translated = TranslationProxy()

    class Meta:
        ordering = ("code",)

    @property
    def is_free(self):
        return (
            self.discount_value == Decimal(100)
            and self.discount_value_type == DiscountValueType.PERCENTAGE
        )

    def get_discount(self, channel: Channel):
        voucher_channel_listing = self.channel_listings.filter(channel=channel).first()
        if not voucher_channel_listing:
            raise NotApplicable("This voucher is not assigned to this channel")
        if self.discount_value_type == DiscountValueType.FIXED:
            discount_amount = Money(
                voucher_channel_listing.discount_value, voucher_channel_listing.currency
            )
            return partial(fixed_discount, discount=discount_amount)
        if self.discount_value_type == DiscountValueType.PERCENTAGE:
            return partial(
                percentage_discount, percentage=voucher_channel_listing.discount_value
            )
        raise NotImplementedError("Unknown discount type")

    def get_discount_amount_for(self, price: Money, channel: Channel):
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
        voucher_customer = VoucherCustomer.objects.filter(
            voucher=self, customer_email=customer_email
        )
        if voucher_customer:
            msg = "This offer is valid only once per customer."
            raise NotApplicable(msg)


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
    voucher = models.ForeignKey(
        Voucher, related_name="customers", on_delete=models.CASCADE
    )
    customer_email = models.EmailField()

    class Meta:
        ordering = ("voucher", "customer_email", "pk")
        unique_together = (("voucher", "customer_email"),)


class SaleQueryset(models.QuerySet):
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


class VoucherTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=255, null=True, blank=True)
    voucher = models.ForeignKey(
        Voucher, related_name="translations", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("language_code", "voucher", "pk")
        unique_together = (("language_code", "voucher"),)


class Sale(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(
        max_length=10,
        choices=DiscountValueType.CHOICES,
        default=DiscountValueType.FIXED,
    )
    products = models.ManyToManyField("product.Product", blank=True)
    categories = models.ManyToManyField("product.Category", blank=True)
    collections = models.ManyToManyField("product.Collection", blank=True)
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    objects = SaleQueryset.as_manager()
    translated = TranslationProxy()

    class Meta:
        ordering = ("name", "pk")
        app_label = "discount"
        permissions = (
            (
                DiscountPermissions.MANAGE_DISCOUNTS.codename,
                "Manage sales and vouchers.",
            ),
        )

    def __repr__(self):
        return "Sale(name=%r, type=%s)" % (
            str(self.name),
            self.get_type_display(),
        )

    def __str__(self):
        return self.name

    def get_discount(self, sale_channel_listing):
        if not sale_channel_listing:
            raise NotApplicable("This sale is not assigned to this channel.")
        if self.type == DiscountValueType.FIXED:
            discount_amount = Money(
                sale_channel_listing.discount_value, sale_channel_listing.currency
            )
            return partial(fixed_discount, discount=discount_amount)
        if self.type == DiscountValueType.PERCENTAGE:
            return partial(
                percentage_discount,
                percentage=sale_channel_listing.discount_value,
            )
        raise NotImplementedError("Unknown discount type")


class SaleChannelListing(models.Model):
    sale = models.ForeignKey(
        Sale,
        null=False,
        blank=False,
        related_name="channel_listings",
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        Channel,
        null=False,
        blank=False,
        related_name="sale_listings",
        on_delete=models.CASCADE,
    )
    discount_value = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )

    class Meta:
        unique_together = [["sale", "channel"]]
        ordering = ("pk",)


class SaleTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=255, null=True, blank=True)
    sale = models.ForeignKey(
        Sale, related_name="translations", on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("language_code", "name", "pk")
        unique_together = (("language_code", "sale"),)
