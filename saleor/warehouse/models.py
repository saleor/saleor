import itertools
import uuid
from typing import Set

from django.db import models
from django.utils.translation import pgettext_lazy

from ..account.models import Address
from ..shipping.models import ShippingZone


class WarehouseQueryset(models.QuerySet):
    def prefetch_data(self):
        return self.select_related("address").prefetch_related("shipping_zones")


class Warehouse(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(
        pgettext_lazy("Warehouse field description", "Warehouse name"), max_length=255
    )
    company_name = models.CharField(
        pgettext_lazy("Warehouse field description", "Legal company name"),
        blank=True,
        max_length=255,
    )

    shipping_zones = models.ManyToManyField(ShippingZone, blank=True)
    address = models.ForeignKey(Address, on_delete=models.PROTECT)

    email = models.EmailField(
        pgettext_lazy("Warehouse field description", "Email address"),
        blank=True,
        default="",
    )

    objects = WarehouseQueryset.as_manager()

    class Meta:
        ordering = ("-name",)
        permissions = (
            (
                "manage_warehouses",
                pgettext_lazy("Permission description", "Manage warehouses."),
            ),
        )

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
