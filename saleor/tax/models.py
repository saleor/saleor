from django.conf import settings
from django.db import models
from django_countries.fields import CountryField

from ..channel.models import Channel
from ..core.models import ModelWithMetadata
from . import TaxCalculationStrategy


class TaxClass(ModelWithMetadata):
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ("name", "pk")

    def __str__(self):
        return self.name


class TaxClassCountryRate(models.Model):
    tax_class = models.ForeignKey(
        TaxClass, related_name="country_rates", on_delete=models.CASCADE, null=True
    )
    country = CountryField()
    rate = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
    )

    class Meta:
        ordering = ("country", models.F("tax_class_id").asc(nulls_first=True), "pk")
        # Custom constraints to restrict unique pairs of ("country", "tax_class") and
        # allow exactly one object per country when tax_class is null ("country", None).
        # TaxClassCountryRate with tax_class=null is considered a default tax rate
        # value for a country.
        constraints = [
            models.constraints.UniqueConstraint(
                fields=("country", "tax_class"), name="unique_country_tax_class"
            ),
            models.constraints.UniqueConstraint(
                fields=("country",),
                condition=models.Q(tax_class=None),
                name="unique_country_without_tax_class",
            ),
        ]

    def __str__(self):
        return f"{self.country}: {self.rate}"


class TaxConfiguration(ModelWithMetadata):
    channel = models.OneToOneField(
        Channel, related_name="tax_configuration", on_delete=models.CASCADE
    )
    charge_taxes = models.BooleanField(default=True)
    tax_calculation_strategy = models.CharField(
        max_length=20,
        choices=TaxCalculationStrategy.CHOICES,
        blank=True,
        null=True,
        default=TaxCalculationStrategy.FLAT_RATES,
    )
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
    tax_calculation_strategy = models.CharField(
        max_length=20, choices=TaxCalculationStrategy.CHOICES, blank=True, null=True
    )
    display_gross_prices = models.BooleanField(default=True)

    class Meta:
        ordering = ("country", "pk")
        unique_together = (("tax_configuration", "country"),)

    def __str__(self):
        return str(self.country)
