from typing import TYPE_CHECKING, List, Union

from django.conf import settings
from django.db import models
from django.db.models import OuterRef, Q, Subquery
from django_countries.fields import CountryField
from django_measurement.models import MeasurementField
from django_prices.models import MoneyField
from measurement.measures import Weight
from prices import Money

from ..channel.models import Channel
from ..core.models import ModelWithMetadata
from ..core.permissions import ShippingPermissions
from ..core.utils.translations import TranslationProxy
from ..core.weight import (
    WeightUnits,
    convert_weight,
    get_default_weight_unit,
    zero_weight,
)
from . import ShippingMethodType
from .zip_codes import check_shipping_method_for_zip_code

if TYPE_CHECKING:
    # flake8: noqa
    from ..checkout.models import Checkout
    from ..order.models import Order


def _applicable_weight_based_methods(weight, qs):
    """Return weight based shipping methods that are applicable for the total weight."""
    qs = qs.weight_based()
    min_weight_matched = Q(minimum_order_weight__lte=weight)
    no_weight_limit = Q(maximum_order_weight__isnull=True)
    max_weight_matched = Q(maximum_order_weight__gte=weight)
    return qs.filter(min_weight_matched & (no_weight_limit | max_weight_matched))


def _applicable_price_based_methods(price: Money, qs, channel_id):
    """Return price based shipping methods that are applicable for the given total."""
    qs_shipping_method = qs.price_based()

    price_based = Q(shipping_method_id__in=qs_shipping_method)
    channel_filter = Q(channel_id=channel_id)
    min_price_matched = Q(minimum_order_price_amount__lte=price.amount)
    no_price_limit = Q(maximum_order_price_amount__isnull=True)
    max_price_matched = Q(maximum_order_price_amount__gte=price.amount)

    applicable_price_based_methods = ShippingMethodChannelListing.objects.filter(
        channel_filter
        & price_based
        & min_price_matched
        & (no_price_limit | max_price_matched)
    ).values_list("shipping_method__id", flat=True)
    return qs_shipping_method.filter(id__in=applicable_price_based_methods)


def _get_weight_type_display(min_weight, max_weight):
    default_unit = get_default_weight_unit()

    if min_weight.unit != default_unit:
        min_weight = convert_weight(min_weight, default_unit)
    if max_weight and max_weight.unit != default_unit:
        max_weight = convert_weight(max_weight, default_unit)

    if max_weight is None:
        return ("%(min_weight)s and up" % {"min_weight": min_weight},)
    return "%(min_weight)s to %(max_weight)s" % {
        "min_weight": min_weight,
        "max_weight": max_weight,
    }


class ShippingZone(ModelWithMetadata):
    name = models.CharField(max_length=100)
    countries = CountryField(multiple=True, default=[], blank=True)
    default = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        permissions = (
            (ShippingPermissions.MANAGE_SHIPPING.codename, "Manage shipping."),
        )


class ShippingMethodQueryset(models.QuerySet):
    def price_based(self):
        return self.filter(type=ShippingMethodType.PRICE_BASED)

    def weight_based(self):
        return self.filter(type=ShippingMethodType.WEIGHT_BASED)

    @staticmethod
    def applicable_shipping_methods_by_channel(shipping_methods, channel_id):
        query = ShippingMethodChannelListing.objects.filter(
            shipping_method=OuterRef("pk"), channel_id=channel_id
        ).values_list("price_amount")
        return shipping_methods.annotate(price_amount=Subquery(query)).order_by(
            "price_amount"
        )

    def exclude_shipping_methods_for_excluded_products(
        self, qs, product_ids: List[int]
    ):
        """Exclude the ShippingMethods which have excluded given products."""
        return qs.exclude(excluded_products__id__in=product_ids)

    def applicable_shipping_methods(
        self, price: Money, channel_id, weight, country_code, product_ids=None
    ):
        """Return the ShippingMethods that can be used on an order with shipment.

        It is based on the given country code, and by shipping methods that are
        applicable to the given price, weight and products.
        """
        qs = self.filter(
            shipping_zone__countries__contains=country_code,
            channel_listings__currency=price.currency,
            channel_listings__channel_id=channel_id,
        )
        qs = self.applicable_shipping_methods_by_channel(qs, channel_id)
        qs = qs.prefetch_related("shipping_zone")

        # Products IDs are used to exclude shipping methods that may be not applicable
        # to some of these products, based on exclusion rules defined in shipping method
        # instances.
        if product_ids:
            qs = self.exclude_shipping_methods_for_excluded_products(qs, product_ids)

        price_based_methods = _applicable_price_based_methods(price, qs, channel_id)
        weight_based_methods = _applicable_weight_based_methods(weight, qs)
        shipping_methods = price_based_methods | weight_based_methods

        return shipping_methods

    def applicable_shipping_methods_for_instance(
        self,
        instance: Union["Checkout", "Order"],
        channel_id,
        price: Money,
        country_code=None,
        lines=None,
    ):
        if not instance.shipping_address:
            return None
        if not country_code:
            # TODO: country_code should come from argument
            country_code = instance.shipping_address.country.code  # type: ignore
        if lines is None:
            # TODO: lines should comes from args in get_valid_shipping_methods_for_order
            lines = instance.lines.prefetch_related("variant__product").all()
            instance_product_ids = set(lines.values_list("variant__product", flat=True))
        else:
            instance_product_ids = {line.product.id for line in lines}
        applicable_methods = self.applicable_shipping_methods(
            price=price,
            channel_id=channel_id,
            weight=instance.get_total_weight(lines),
            country_code=country_code or instance.shipping_address.country.code,
            product_ids=instance_product_ids,
        ).prefetch_related("zip_code_rules")

        excluded_methods_by_zip_code = []
        for method in applicable_methods:
            if check_shipping_method_for_zip_code(instance.shipping_address, method):
                excluded_methods_by_zip_code.append(method.pk)
        if excluded_methods_by_zip_code:
            return applicable_methods.exclude(pk__in=excluded_methods_by_zip_code)
        return applicable_methods


class ShippingMethod(ModelWithMetadata):
    name = models.CharField(max_length=100)
    type = models.CharField(max_length=30, choices=ShippingMethodType.CHOICES)
    shipping_zone = models.ForeignKey(
        ShippingZone, related_name="shipping_methods", on_delete=models.CASCADE
    )
    minimum_order_weight = MeasurementField(
        measurement=Weight,
        unit_choices=WeightUnits.CHOICES,
        default=zero_weight,
        blank=True,
        null=True,
    )
    maximum_order_weight = MeasurementField(
        measurement=Weight, unit_choices=WeightUnits.CHOICES, blank=True, null=True
    )
    excluded_products = models.ManyToManyField(
        "product.Product", blank=True
    )  # type: ignore
    maximum_delivery_days = models.PositiveIntegerField(null=True, blank=True)
    minimum_delivery_days = models.PositiveIntegerField(null=True, blank=True)

    objects = ShippingMethodQueryset.as_manager()
    translated = TranslationProxy()

    class Meta:
        ordering = ("pk",)

    def __str__(self):
        return self.name

    def __repr__(self):
        if self.type == ShippingMethodType.PRICE_BASED:
            return "ShippingMethod(type=%s)" % (self.type,)
        return "ShippingMethod(type=%s weight_range=(%s)" % (
            self.type,
            _get_weight_type_display(
                self.minimum_order_weight, self.maximum_order_weight
            ),
        )


class ShippingMethodZipCodeRule(models.Model):
    shipping_method = models.ForeignKey(
        ShippingMethod, on_delete=models.CASCADE, related_name="zip_code_rules"
    )
    start = models.CharField(max_length=32)
    end = models.CharField(max_length=32, blank=True, null=True)

    class Meta:
        unique_together = ("shipping_method", "start", "end")


class ShippingMethodChannelListing(models.Model):
    shipping_method = models.ForeignKey(
        ShippingMethod,
        null=False,
        blank=False,
        related_name="channel_listings",
        on_delete=models.CASCADE,
    )
    channel = models.ForeignKey(
        Channel,
        null=False,
        blank=False,
        related_name="shipping_method_listings",
        on_delete=models.CASCADE,
    )
    minimum_order_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
        blank=True,
        null=True,
    )
    minimum_order_price = MoneyField(
        amount_field="minimum_order_price_amount", currency_field="currency"
    )
    currency = models.CharField(
        max_length=settings.DEFAULT_CURRENCY_CODE_LENGTH,
    )
    maximum_order_price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        blank=True,
        null=True,
    )
    maximum_order_price = MoneyField(
        amount_field="maximum_order_price_amount", currency_field="currency"
    )
    price = MoneyField(amount_field="price_amount", currency_field="currency")
    price_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )

    def get_total(self):
        return self.price

    class Meta:
        unique_together = [["shipping_method", "channel"]]
        ordering = ("pk",)


class ShippingMethodTranslation(models.Model):
    language_code = models.CharField(max_length=10)
    name = models.CharField(max_length=255, null=True, blank=True)
    shipping_method = models.ForeignKey(
        ShippingMethod, related_name="translations", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = (("language_code", "shipping_method"),)
