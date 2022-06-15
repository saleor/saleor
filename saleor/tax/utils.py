from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .models import TaxConfiguration, TaxConfigurationPerCountry


def get_display_gross_prices(
    channel_tax_configuration: "TaxConfiguration",
    country_tax_configuration: Optional["TaxConfigurationPerCountry"],
):
    return (
        country_tax_configuration.display_gross_prices
        if country_tax_configuration
        else channel_tax_configuration.display_gross_prices
    )
