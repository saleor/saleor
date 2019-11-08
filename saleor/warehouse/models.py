import uuid

from django.db import models
from django.forms.models import model_to_dict
from django.utils.translation import pgettext_lazy
from django_countries.fields import Country, CountryField
from phonenumber_field.modelfields import PhoneNumber, PhoneNumberField

from saleor.shipping.models import ShippingZone


class Warehouse(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(
        pgettext_lazy("Warehouse field description", "Warehouse name"), max_length=50
    )
    company_name = models.CharField(
        pgettext_lazy("Warehouse field description", "Legal company name"),
        max_length=100,
    )

    shipping_zones = models.ManyToManyField(ShippingZone)

    street_address = models.CharField(
        pgettext_lazy("Warehouse field description", "Street name"), max_length=256
    )
    city = models.CharField(max_length=256)
    postal_code = models.CharField(
        pgettext_lazy("Warehouse field description", "Zip code"), max_length=20
    )
    country = CountryField()
    country_area = models.CharField(
        pgettext_lazy("Warehouse field description", "State/province"), max_length=128
    )

    email = models.EmailField(
        pgettext_lazy("Warehouse field description", "Email address"),
        blank=True,
        default="",
    )
    phone = PhoneNumberField(
        pgettext_lazy("Warehouse field description", "Phone number"),
        blank=True,
        default="",
    )

    def __str__(self):
        return self.name

    def as_data(self):
        """Return the address as a dict suitable for passing as kwargs.

        Result does not contain the primary key or an associated user.
        """
        data = model_to_dict(self, exclude=["id", "site"])
        if isinstance(data["country"], Country):
            data["country"] = data["country"].code
        if isinstance(data["phone"], PhoneNumber):
            data["phone"] = data["phone"].as_e164
        return data

    class Meta:
        ordering = ("-name",)
        permissions = (
            (
                "manage_warehouses",
                pgettext_lazy("Permission description", "Manage warehouses."),
            ),
        )
