from typing import TYPE_CHECKING, Optional

from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.db.models.functions import Coalesce
from django.utils import timezone
from django_countries.fields import CountryField

from ..shipping.models import ShippingZone

if TYPE_CHECKING:
    # flake8: noqa
    from ..account.models import User
    from ..product.models import ProductVariant


class ReservationQuerySet(models.QuerySet):
    def annotate_total_quantity(self):
        return self.annotate(total_quantity=Coalesce(Sum("quantity"), 0))

    def for_country(self, country_code: str):
        query_shipping_zone = models.Subquery(
            ShippingZone.objects.filter(countries__contains=country_code).values("pk")
        )
        return self.filter(shipping_zone__in=query_shipping_zone)

    def exclude_user(self, user: Optional["User"]):
        if user and user.is_authenticated:
            return self.exclude(user=user)
        return self

    def active(self):
        return self.filter(expires__gt=timezone.now())

    def expired(self):
        return self.filter(expires__lte=timezone.now())


class Reservation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="reservations",
        on_delete=models.CASCADE,
    )
    shipping_zone = models.ForeignKey(
        "shipping.ShippingZone",
        null=False,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    expires = models.DateTimeField(null=False, db_index=True)
    product_variant = models.ForeignKey(
        "product.ProductVariant",
        null=False,
        on_delete=models.CASCADE,
        related_name="reservations",
    )
    quantity = models.PositiveIntegerField(default=0)

    objects = ReservationQuerySet.as_manager()

    class Meta:
        unique_together = [["user", "shipping_zone", "product_variant"]]
        ordering = ("pk",)
