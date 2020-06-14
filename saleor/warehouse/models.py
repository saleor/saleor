import itertools
import uuid
from typing import Set

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import Coalesce

from ..account.models import Address
from ..checkout.models import CheckoutLine
from ..order.models import OrderLine
from ..product.models import Product, ProductVariant
from ..shipping.models import ShippingZone


class WarehouseQueryset(models.QuerySet):
    def prefetch_data(self):
        return self.select_related("address").prefetch_related("shipping_zones")

    def for_country(self, country: str):
        return (
            self.prefetch_data()
            .filter(shipping_zones__countries__contains=country)
            .order_by("pk")
        )


class Warehouse(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=250)
    slug = models.SlugField(max_length=255, unique=True)
    company_name = models.CharField(blank=True, max_length=255)
    shipping_zones = models.ManyToManyField(
        ShippingZone, blank=True, related_name="warehouses"
    )
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    email = models.EmailField(blank=True, default="")

    objects = WarehouseQueryset.as_manager()

    class Meta:
        ordering = ("-name",)

    def __str__(self):
        return self.name

    @property
    def countries(self) -> Set[str]:
        shipping_zones = self.shipping_zones.all()
        return set(itertools.chain(*[zone.countries for zone in shipping_zones]))

    def delete(self, *args, **kwargs):
        address = self.address
        super().delete(*args, **kwargs)
        address.delete()


class StockQuerySet(models.QuerySet):
    def annotate_available_quantity(self):
        return self.annotate(
            available_quantity=F("quantity")
            - Coalesce(Sum("allocations__quantity_allocated"), 0)
        )

    def for_country(self, country_code: str):
        query_warehouse = models.Subquery(
            Warehouse.objects.filter(
                shipping_zones__countries__contains=country_code
            ).values("pk")
        )
        return self.select_related("product_variant", "warehouse").filter(
            warehouse__in=query_warehouse
        )

    def get_variant_stocks_for_country(
        self, country_code: str, product_variant: ProductVariant
    ):
        """Return the stock information about the a stock for a given country.

        Note it will raise a 'Stock.DoesNotExist' exception if no such stock is found.
        """
        return self.for_country(country_code).filter(product_variant=product_variant)

    def get_product_stocks_for_country(self, country_code: str, product: Product):
        return self.for_country(country_code).filter(
            product_variant__product_id=product.pk
        )


class Stock(models.Model):
    warehouse = models.ForeignKey(Warehouse, null=False, on_delete=models.CASCADE)
    product_variant = models.ForeignKey(
        ProductVariant, null=False, on_delete=models.CASCADE, related_name="stocks"
    )
    quantity = models.PositiveIntegerField(default=0)

    objects = StockQuerySet.as_manager()

    class Meta:
        unique_together = [["warehouse", "product_variant"]]
        ordering = ("pk",)

    def increase_stock(self, quantity: int, commit: bool = True):
        """Return given quantity of product to a stock."""
        self.quantity = F("quantity") + quantity
        if commit:
            self.save(update_fields=["quantity"])

    def decrease_stock(self, quantity: int, commit: bool = True):
        self.quantity = F("quantity") - quantity
        if commit:
            self.save(update_fields=["quantity"])


class Allocation(models.Model):
    order_line = models.ForeignKey(
        OrderLine,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    checkout_line = models.ForeignKey(
        CheckoutLine,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    stock = models.ForeignKey(
        Stock,
        null=False,
        blank=False,
        on_delete=models.CASCADE,
        related_name="allocations",
    )
    quantity_allocated = models.PositiveIntegerField(default=0)

    def clean(self):
        if self.order_line is None and self.checkout_line is None:
            raise ValidationError("Order line or checkout line is required")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['order_line', 'stock'], name='order stock constraint'),
            models.UniqueConstraint(fields=['checkout_line', 'stock'], name='checkout stock constraint'),
        ]
        ordering = ("pk",)
