from django.db import models
from django.db.models import F
from django.utils.translation import pgettext_lazy

from ..core.exceptions import InsufficientStock
from ..product.models import ProductVariant
from ..warehouse.models import Warehouse


class StockQuerySet(models.QuerySet):
    def annotate_available_quantity(self):
        return self.annotate(available_quantity=F("quantity") - F("quantity_allocated"))

    def for_country(self, country_code: str):
        query_warehouse = models.Subquery(
            Warehouse.objects.filter(
                shipping_zones__countries__contains=country_code
            ).values("pk")
        )
        return self.select_related("product_variant", "warehouse").filter(
            warehouse__in=query_warehouse
        )

    def get_variant_stock_for_country(
        self, country_code: str, product_variant: ProductVariant
    ):
        return self.for_country(country_code).get(product_variant=product_variant)


class Stock(models.Model):
    warehouse = models.ForeignKey(Warehouse, null=False, on_delete=models.PROTECT)
    product_variant = models.ForeignKey(
        ProductVariant, null=False, on_delete=models.CASCADE
    )
    quantity = models.PositiveIntegerField(default=0)
    quantity_allocated = models.PositiveIntegerField(default=0)

    objects = StockQuerySet.as_manager()

    class Meta:
        unique_together = [["warehouse", "product_variant"]]
        permissions = (
            (
                "manage_stocks",
                pgettext_lazy("Permission description", "Manage stocks."),
            ),
        )

    def __str__(self):
        return f"{self.product_variant} - {self.warehouse.name}"

    @property
    def quantity_available(self) -> int:
        return max(self.quantity - self.quantity_allocated, 0)

    @property
    def is_available(self):
        return self.quantity_available > 0

    def check_quantity(self, quantity: int):
        if quantity > self.quantity_available:
            raise InsufficientStock(self)

    def allocate_stock(self, quantity: int, commit: bool = True):
        self.quantity_allocated = F("quantity_allocated") + quantity
        if commit:
            self.save(update_fields=["quantity_allocated"])

    def deallocate_stock(self, quantity: int, commit: bool = True):
        self.quantity_allocated = F("quantity_allocated") - quantity
        if commit:
            self.save(update_fields=["quantity_allocated"])

    def increase_stock(
        self, quantity: int, allocate: bool = False, commit: bool = True
    ):
        """Return given quantity of product to a stock."""
        self.quantity = F("quantity") + quantity
        update_fields = ["quantity"]
        if allocate:
            self.quantity_allocated = F("quantity_allocated") + quantity
            update_fields.append("quantity_allocated")
        if commit:
            self.save(update_fields=update_fields)

    def decrease_stock(self, quantity: int, commit: bool = True):
        self.quantity = F("quantity") - quantity
        self.quantity_allocated = F("quantity_allocated") - quantity
        if commit:
            self.save(update_fields=["quantity", "quantity_allocated"])
