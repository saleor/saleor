from django.db import models

DEFAULT_RAX_RATE = 23


class TaxCountry(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)
    tax_rate_name = models.CharField(max_length=255)
    standard_tax_rate = models.PositiveIntegerField(default=DEFAULT_RAX_RATE)
    b2b_tax_rate = models.PositiveIntegerField(default=DEFAULT_RAX_RATE)

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name!r}, code={self.code!r})"


class TaxGroup(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=255)


class TaxCountryRate(models.Model):
    country = models.ForeignKey(
        to=TaxCountry,
        related_name="country_rates",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    value = models.PositiveIntegerField(default=DEFAULT_RAX_RATE)
    group = models.ForeignKey(
        to=TaxGroup,
        related_name="country_rates",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )


class TaxSetting(models.Model):
    name = models.CharField(max_length=255)
    include_taxes_in_prices = models.BooleanField(default=False)
    display_gross_prices = models.BooleanField(default=False)
    charge_taxes_on_shipping = models.BooleanField(default=False)
    default = models.BooleanField(default=False)
