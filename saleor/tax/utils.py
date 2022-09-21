from typing import TYPE_CHECKING, Iterable, Optional, Tuple

if TYPE_CHECKING:
    from ..account.models import Address
    from ..channel.models import Channel
    from ..checkout.fetch import CheckoutInfo, CheckoutLineInfo
    from ..order.models import Order
    from .models import TaxConfiguration, TaxConfigurationPerCountry


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


def get_display_gross_prices(
    channel_tax_configuration: "TaxConfiguration",
    country_tax_configuration: Optional["TaxConfigurationPerCountry"],
):
    """Get display_gross_prices value for tax channel configuration.

    :param channel_tax_configuration: Channel-specific tax configuration.
    :param country_tax_configuration: Country-specific tax configuration for the given
    channel.
    """
    return (
        country_tax_configuration.display_gross_prices
        if country_tax_configuration
        else channel_tax_configuration.display_gross_prices
    )


def get_charge_taxes(
    channel_tax_configuration: "TaxConfiguration",
    country_tax_configuration: Optional["TaxConfigurationPerCountry"],
) -> bool:
    """Get charge_taxes value for tax channel configuration.

    :param channel_tax_configuration: Channel-specific tax configuration.
    :param country_tax_configuration: Country-specific tax configuration for the given
    channel.
    """
    return (
        country_tax_configuration.charge_taxes
        if country_tax_configuration
        else channel_tax_configuration.charge_taxes
    )


def get_tax_calculation_strategy(
    channel_tax_configuration: "TaxConfiguration",
    country_tax_configuration: Optional["TaxConfigurationPerCountry"],
) -> Optional[str]:
    """Get tax_calculation_strategy value for tax channel configuration.

    :param channel_tax_configuration: Channel-specific tax configuration.
    :param country_tax_configuration: Country-specific tax configuration for the given
    channel.
    """
    return (
        country_tax_configuration.tax_calculation_strategy
        if country_tax_configuration
        else channel_tax_configuration.tax_calculation_strategy
    )


def get_charge_taxes_for_order(order: "Order") -> bool:
    """Get charge_taxes value for order."""
    channel = order.channel
    tax_configuration = channel.tax_configuration
    country_code = get_tax_country(
        channel,
        order.is_shipping_required(),
        order.shipping_address,
        order.billing_address,
    )
    country_tax_configuration = next(
        (
            tc
            for tc in tax_configuration.country_exceptions.all()
            if tc.country.code == country_code
        ),
        None,
    )
    return get_charge_taxes(tax_configuration, country_tax_configuration)


def _get_tax_configuration_for_checkout(
    checkout_info: "CheckoutInfo", lines: Iterable["CheckoutLineInfo"]
) -> Tuple["TaxConfiguration", Optional["TaxConfigurationPerCountry"]]:
    from ..checkout.utils import is_shipping_required

    tax_configuration = checkout_info.tax_configuration
    country_code = get_tax_country(
        checkout_info.channel,
        is_shipping_required(lines),
        checkout_info.shipping_address,
        checkout_info.billing_address,
    )
    country_tax_configuration = next(
        (
            tc
            for tc in tax_configuration.country_exceptions.all()
            if tc.country.code == country_code
        ),
        None,
    )
    return tax_configuration, country_tax_configuration


def get_charge_taxes_for_checkout(
    checkout_info: "CheckoutInfo", lines: Iterable["CheckoutLineInfo"]
):
    """Get charge_taxes value for checkout."""
    tax_configuration, country_tax_configuration = _get_tax_configuration_for_checkout(
        checkout_info, lines
    )
    return get_charge_taxes(tax_configuration, country_tax_configuration)


def get_tax_calculation_strategy_for_checkout(
    checkout_info: "CheckoutInfo", lines: Iterable["CheckoutLineInfo"]
):
    tax_configuration, country_tax_configuration = _get_tax_configuration_for_checkout(
        checkout_info, lines
    )
    return get_tax_calculation_strategy(tax_configuration, country_tax_configuration)
