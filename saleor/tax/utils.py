from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .models import TaxConfiguration, TaxConfigurationPerCountry


def get_display_gross_prices(
    tax_configuration: "TaxConfiguration",
    country_tax_configuration: Optional["TaxConfigurationPerCountry"],
):
    return (
        country_tax_configuration.display_gross_prices
        if country_tax_configuration
        else tax_configuration.display_gross_prices
    )
