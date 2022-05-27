from django.conf import settings
from django.db import IntegrityError, models
from django_countries.fields import CountryField
from graphene import Int

from ..channel.models import Channel
from ..core.models import ModelWithMetadata

DEFAULT_TAX_CLASS_NAME = "Default"


def get_default_tax_class() -> Int:
    """Get the ID of the default tax class.

    The function gets or creates a default tax class and returns it's ID. It is
    intended to be used as a default tax class in foreign key relations.
    """
    tax_class, _ = TaxClass.objects.get_or_create(
        is_default=True, name=DEFAULT_TAX_CLASS_NAME
    )
    return tax_class.pk


class TaxClass(ModelWithMetadata):
    name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ("is_default", "name", "pk")

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.is_default:
            raise IntegrityError("Cannot remove a default tax class.")
        return super().delete(*args, **kwargs)


class TaxClassCountryRate(models.Model):
    tax_class = models.ForeignKey(
        TaxClass, related_name="country_rates", on_delete=models.CASCADE
    )
    country = CountryField()
    rate = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )

    class Meta:
        ordering = ("country", "pk")
        unique_together = (("tax_class", "country"),)

    def __str__(self):
        return f"{self.country}: {self.rate}"


class TaxConfiguration(ModelWithMetadata):
    channel = models.OneToOneField(
        Channel, related_name="tax_configuration", on_delete=models.CASCADE
    )
    charge_taxes = models.BooleanField(default=True)
    display_gross_prices = models.BooleanField(default=True)
    prices_entered_with_tax = models.BooleanField(default=True)

    class Meta:
        ordering = ("pk",)


class TaxConfigurationPerCountry(models.Model):
    tax_configuration = models.ForeignKey(
        TaxConfiguration, related_name="country_exceptions", on_delete=models.CASCADE
    )
    country = CountryField()
    charge_taxes = models.BooleanField(default=True)
    display_gross_prices = models.BooleanField(default=True)

    class Meta:
        ordering = ("country", "pk")
        unique_together = (("tax_configuration", "country"),)

    def __str__(self):
        return str(self.country)
