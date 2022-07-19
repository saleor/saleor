from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..account.models import Address
    from ..channel.models import Channel
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


def get_tax_country(
    channel: "Channel",
    is_shipping_required: bool,
    shipping_address: Optional["Address"] = None,
    billing_address: Optional["Address"] = None,
):
    """Get country code for tax calculations.

    For checkouts and orders, there are following rules for determining the country
    code that should be used for tax calculations:
    - when shipping is required, use the shipping address's country code,
    - when shipping is not required (e.g. because of having only digital products), use
    the billing address's country code,
    - fallback to channel's default country when addresses are not provided.
    """
    if shipping_address and is_shipping_required:
        return shipping_address.country.code

    if billing_address and not is_shipping_required:
        return billing_address.country.code

    return channel.default_country.code
